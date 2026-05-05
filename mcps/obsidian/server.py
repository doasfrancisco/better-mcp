"""Obsidian MCP — books knowledge base.

Three tools:
    raw_graph()           graph of raw/ — nodes (md+pdf) + edges (wikilinks, embeds, fm)
    read(path)            read a .md file
    write(path, content)  write a .md file (full overwrite)

PDFs are visible in the graph but not readable through this server. The
markdown layer is the human↔AI channel.
"""

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import requests

from obsidian_client import ObsidianClient, build_graph

_log_dir = Path(__file__).parent / "logs"
_log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[RotatingFileHandler(_log_dir / "obsidian.log", maxBytes=5_000_000, backupCount=1)],
)

from fastmcp import FastMCP

mcp = FastMCP(
    "Obsidian",
    instructions="""Personal Obsidian KB of math + CS books. Layout:
  raw/<book>/<book>.md   (hub: YAML frontmatter + nav callout + summary)
  raw/<book>/*.pdf       (sources: textbook, solutions, errata, ...)
  raw/<book>/notes.md    (single dated journal across all sources)
  wiki/                  (LLM-compiled output — write here only on
                          explicit "compile" / "rebuild concepts" requests)

THREE TOOLS:
  raw_graph()           full graph of raw/ — nodes + edges
  read(path)            read a .md file
  write(path, content)  write a .md file (full overwrite)

IMPORTANT: discover schemas with ToolSearch before first call.

ALWAYS START WITH raw_graph. Don't read blindly. The graph tells you
what exists, the node types (hub|notes|pdf|other_md), the wikilinks,
and which links are ghosts (target_exists: false). All read/write
decisions follow from it.

PDFS ARE NOT READABLE. They appear in the graph as nodes (with page
count + extractable flag from the sibling hub's sources[]) so you know
they exist, but `read` is .md-only. If the user asks "what does ch.3 of
Lages say?", you cannot answer from the PDF directly. Offer to: (a) read
their notes.md for what they wrote about ch.3, (b) summarize what the
hub already records, or (c) ask them to paste the passage into notes.md.
Do not pretend to have read the PDF.

APPEND = READ-MODIFY-WRITE. `write` is a full overwrite. To add a
journal entry to notes.md, you MUST read it first, append the new entry
to the existing body, then write the whole thing back. Never write
partial content — you'll silently destroy prior entries.

PRESERVE FRONTMATTER. When editing any .md, never drop, reorder, or
silently mutate the YAML frontmatter unless the user explicitly asked
for it. Frontmatter holds the queryable schema (status, sources,
ingested_at, tags) — it's not decoration. Same for the nav callout in
hub pages — it's the connectivity backbone for the graph.

WIKILINK HYGIENE. When you write content that references a book or
concept, use [[Exact Basename]] from raw_graph. Don't invent ghost
links unless intentional. If you're forced to reference something that
doesn't exist yet, mention it explicitly: "this links to a concept page
that doesn't exist — want me to create it?"

NO NEW TOP-LEVEL FOLDERS. Only raw/, wiki/, attachments/ exist by
design. New books go in raw/<book>/. New concepts go in wiki/concepts/.
Don't invent siblings of these.

JOURNAL APPEND FORMAT. notes.md uses dated headings:
    ## YYYY-MM-DD — ch.N §M
    {user's prose, verbatim — don't paraphrase}
Always include chapter/section if the user names them.

CONFIRM BEFORE WRITE. Writes are persistent and overwriting. Tell the
user the path and a short summary of what's changing, then stop your
turn and wait for confirmation. Exception: if the user pre-authorized
("just log this", "append this thought"), proceed without re-asking.

PRESENTATION when showing the graph to the user:
- Group by folder (one section per book in raw/)
- For each book: **Title** — Author · status · sources (mark "needs OCR"
  if all sources are unextractable)
- Surface ghost links explicitly — they're gaps in the KB
- Don't dump the raw JSON; render it as prose + nested lists.
""",
)


_client: ObsidianClient | None = None


def _get_client() -> ObsidianClient:
    global _client
    if _client is None:
        _client = ObsidianClient.from_env()
    return _client


def _normalize(path: str) -> str:
    p = path.replace("\\", "/").lstrip("/")
    if not p:
        raise ValueError("path is empty")
    parts = p.split("/")
    if any(part in ("..", "") for part in parts):
        raise ValueError(f"invalid path: {path!r}")
    if not p.lower().endswith(".md"):
        raise ValueError(f"only .md paths are allowed; got {path!r}")
    return p


@mcp.tool()
def raw_graph() -> str:
    """Return the graph of `raw/` — every .md and .pdf node, plus the
    wikilink/embed/frontmatter edges between them.

    Shape:
        {
          "nodes": [
            {"path": str, "type": "hub|notes|pdf|other_md",
             "frontmatter"?: dict,           # for .md
             "pages"?: int, "extractable"?: bool, "role"?: str  # for .pdf
            }, ...
          ],
          "edges": [
            {"from": path, "to": path-or-basename,
             "kind": "wikilink|embed|frontmatter",
             "target_exists": bool}, ...
          ]
        }

    Call this at the start of every session to orient. Cheap and
    idempotent — no caching needed by the caller.
    """
    g = build_graph(_get_client(), root="raw")
    return json.dumps(g, indent=2, ensure_ascii=False)


@mcp.tool()
def read(path: str) -> str:
    """Read a markdown file from the vault. Path must end in .md.

    Args:
        path: Vault-relative path, e.g.
              "raw/Analisis Real - Lages/Analisis Real - Lages.md"
    """
    p = _normalize(path)
    try:
        return _get_client().read_text(p)
    except requests.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            raise ValueError(f"file not found: {p}") from None
        raise


@mcp.tool()
def write(path: str, content: str) -> str:
    """Write a markdown file to the vault. Full overwrite — creates or
    replaces. Path must end in .md.

    To append, read first, modify in memory, then write the whole file
    back. Writing partial content will destroy what's already there.

    Args:
        path: Vault-relative path, must end in .md
        content: Full markdown body (frontmatter included if applicable)
    """
    p = _normalize(path)
    body_bytes = len(content.encode("utf-8"))
    _get_client().write_text(p, content)
    return json.dumps({"path": p, "bytes": body_bytes}, ensure_ascii=False)


if __name__ == "__main__":
    mcp.run()
