"""Obsidian Local REST API client + graph builder for the books KB.

The client wraps the HTTPS+bearer-token API exposed by the
coddingtonbear/obsidian-local-rest-api plugin. PUT auto-creates parent
folders, DELETE is idempotent (404 on missing).

`build_graph` walks `raw/` and returns a node+edge structure modeling
Obsidian's actual graph: .md files, .pdf attachments, wikilinks
(in-body and frontmatter), with ghost-link detection.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
import urllib3
import yaml
from dotenv import load_dotenv

_DIR = Path(__file__).parent
load_dotenv(_DIR.parent.parent / ".env")

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# ── HTTP client ───────────────────────────────────────────────────────


@dataclass
class ObsidianClient:
    base: str
    api_key: str
    _session: requests.Session

    @classmethod
    def from_env(cls) -> "ObsidianClient":
        api_key = os.getenv("OBSIDIAN_API_KEY")
        if not api_key:
            raise RuntimeError("OBSIDIAN_API_KEY not set in environment")
        host = os.getenv("OBSIDIAN_HOST", "127.0.0.1")
        port = int(os.getenv("OBSIDIAN_PORT", "27124"))
        s = requests.Session()
        s.headers["Authorization"] = f"Bearer {api_key}"
        s.verify = False
        return cls(base=f"https://{host}:{port}", api_key=api_key, _session=s)

    def _url(self, path: str) -> str:
        # quote() with safe='/' so folder separators stay literal
        return f"{self.base}/vault/{quote(path, safe='/')}"

    def list_dir(self, path: str) -> list[str]:
        """List immediate children of a vault folder. Subfolders end in '/'.

        Returns [] if the folder doesn't exist (404).
        """
        url = self._url(path.rstrip("/")) + "/"
        r = self._session.get(url, timeout=10)
        if r.status_code == 404:
            return []
        r.raise_for_status()
        data = r.json()
        return data.get("files", [])

    def read_text(self, path: str) -> str:
        r = self._session.get(
            self._url(path),
            headers={"Accept": "text/markdown"},
            timeout=15,
        )
        r.raise_for_status()
        return r.text

    def write_text(self, path: str, body: str) -> int:
        r = self._session.put(
            self._url(path),
            data=body.encode("utf-8"),
            headers={"Content-Type": "text/markdown"},
            timeout=30,
        )
        r.raise_for_status()
        return r.status_code

    def walk_files(self, root: str) -> list[str]:
        """Recursively collect file paths under `root`. Folders excluded."""
        files: list[str] = []
        stack = [root.rstrip("/")]
        while stack:
            folder = stack.pop()
            for entry in self.list_dir(folder):
                full = f"{folder}/{entry.rstrip('/')}"
                if entry.endswith("/"):
                    stack.append(full)
                else:
                    files.append(full)
        return files


# ── Frontmatter + wikilinks ───────────────────────────────────────────

_FENCED_RE = re.compile(r"```[\s\S]*?```")
_INLINE_CODE_RE = re.compile(r"`[^`\n]+`")
_WIKILINK_RE = re.compile(
    r"(!?)\[\["                   # 1: '!' if embed
    r"([^\[\]|#]+?)"              # 2: target (no brackets/pipes/hashes)
    r"(?:#([^\[\]|]+?))?"         # 3: anchor (optional)
    r"(?:\|([^\[\]]*?))?"         # 4: alias (optional)
    r"\]\]"
)


def parse_frontmatter(md: str) -> tuple[dict, str]:
    """Split YAML frontmatter from body. Returns ({}, original) if none/invalid."""
    if not md.startswith("---\n"):
        return {}, md
    end = md.find("\n---", 4)
    if end == -1:
        return {}, md
    fm_text = md[4:end]
    body_start = end + len("\n---")
    if md[body_start:body_start + 1] == "\n":
        body_start += 1
    body = md[body_start:]
    try:
        fm = yaml.safe_load(fm_text)
    except yaml.YAMLError:
        return {}, md
    if not isinstance(fm, dict):
        return {}, md
    return fm, body


def extract_body_links(body: str) -> list[tuple[str, str]]:
    """Return [(target, kind)] from .md body. kind = 'wikilink' or 'embed'.

    Strips fenced + inline code blocks first so brackets in code don't
    create phantom edges.
    """
    stripped = _INLINE_CODE_RE.sub("", _FENCED_RE.sub("", body))
    out: list[tuple[str, str]] = []
    for m in _WIKILINK_RE.finditer(stripped):
        target = m.group(2).strip()
        kind = "embed" if m.group(1) == "!" else "wikilink"
        out.append((target, kind))
    return out


def extract_frontmatter_links(fm: dict) -> list[str]:
    """Walk frontmatter values for [[X]] strings — Obsidian renders these as edges."""
    targets: list[str] = []

    def walk(v: Any) -> None:
        if isinstance(v, str):
            for m in _WIKILINK_RE.finditer(v):
                targets.append(m.group(2).strip())
        elif isinstance(v, list):
            for item in v:
                walk(item)
        elif isinstance(v, dict):
            for vv in v.values():
                walk(vv)

    walk(fm)
    return targets


# ── Resolution ────────────────────────────────────────────────────────

_KNOWN_EXTS = (".md", ".pdf", ".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif")


def resolve_link(target: str, all_files: list[str]) -> str | None:
    """Resolve a wikilink target to a vault-relative path, or None if ghost.

    Path-style targets (`folder/file`) are matched as exact paths, with .md
    appended when no recognized extension is present. Bare targets are
    resolved by basename across all .md files.
    """
    target = target.strip()
    if not target:
        return None

    if "/" in target:
        if target in all_files:
            return target
        if not target.lower().endswith(_KNOWN_EXTS):
            md_path = f"{target}.md"
            if md_path in all_files:
                return md_path
        return None

    # Bare basename — match any .md whose stem == target
    for f in all_files:
        if f.endswith(f"/{target}.md") or f == f"{target}.md":
            return f
    # Or any file that matches verbatim (rare)
    for f in all_files:
        if f.endswith(f"/{target}") or f == target:
            return f
    return None


# ── Graph builder ─────────────────────────────────────────────────────


def _classify(path: str) -> str:
    if path.lower().endswith(".pdf"):
        return "pdf"
    if not path.lower().endswith(".md"):
        return "other"
    parts = path.split("/")
    # raw/<book>/<book>.md → hub (basename matches folder name)
    if len(parts) == 3 and parts[0] == "raw" and parts[2] == f"{parts[1]}.md":
        return "hub"
    if parts[-1] == "notes.md":
        return "notes"
    return "other_md"


def _pdf_meta_for(path: str, hub_index: dict[str, dict]) -> dict:
    """Look up pages/extractable for a PDF in its sibling hub's sources[]."""
    folder = "/".join(path.split("/")[:-1])
    filename = path.split("/")[-1]
    hub_fm = hub_index.get(folder)
    if not hub_fm:
        return {}
    sources = hub_fm.get("sources") or []
    if not isinstance(sources, list):
        return {}
    for src in sources:
        if isinstance(src, dict) and src.get("filename") == filename:
            meta = {}
            if "pages" in src:
                meta["pages"] = src["pages"]
            if "extractable" in src:
                meta["extractable"] = src["extractable"]
            if "role" in src:
                meta["role"] = src["role"]
            return meta
    return {}


def build_graph(client: ObsidianClient, root: str = "raw") -> dict:
    """Walk `root/` and return {nodes, edges}.

    Nodes: every .md and .pdf under root, with type + frontmatter (md) or
    pages/extractable (pdf when hub records it).
    Edges: wikilinks (body + frontmatter) + embeds, resolved by basename
    or path. `target_exists: false` flags ghost links.
    """
    files = client.walk_files(root)
    md_files = [f for f in files if f.lower().endswith(".md")]

    # Pass 1: read all .md, parse frontmatter + body links.
    md_data: dict[str, dict] = {}
    hub_index: dict[str, dict] = {}  # folder -> hub frontmatter
    for path in md_files:
        try:
            text = client.read_text(path)
        except requests.HTTPError:
            continue
        fm, body = parse_frontmatter(text)
        body_links = extract_body_links(body)
        fm_links = extract_frontmatter_links(fm)
        md_data[path] = {"fm": fm, "body_links": body_links, "fm_links": fm_links}
        if _classify(path) == "hub":
            folder = "/".join(path.split("/")[:-1])
            hub_index[folder] = fm

    # Pass 2: build nodes.
    nodes = []
    for path in sorted(files):
        kind = _classify(path)
        node: dict[str, Any] = {"path": path, "type": kind}
        if kind == "pdf":
            node.update(_pdf_meta_for(path, hub_index))
        elif kind in ("hub", "notes", "other_md"):
            fm = md_data.get(path, {}).get("fm") or {}
            if fm:
                node["frontmatter"] = fm
        nodes.append(node)

    # Pass 3: resolve edges.
    edges = []
    for path, data in md_data.items():
        for target, kind in data["body_links"]:
            resolved = resolve_link(target, files)
            edges.append({
                "from": path,
                "to": resolved or target,
                "kind": kind,
                "target_exists": resolved is not None,
            })
        for target in data["fm_links"]:
            resolved = resolve_link(target, files)
            edges.append({
                "from": path,
                "to": resolved or target,
                "kind": "frontmatter",
                "target_exists": resolved is not None,
            })

    return {"nodes": nodes, "edges": edges}
