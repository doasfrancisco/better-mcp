"""Check Claude Code session logs for task progress.

Algorithm:
    1. Map project name to session dirs via projects.json. Each path is
       converted to Claude Code's dir naming (replace :\\/_ with -).
       e.g. mcp_servers -> C--Francisco-github-repositories-mcp-servers
    2. grep -rl keywords across all .jsonl files in those dirs to find
       sessions that mention the task.
    3. Sort matches by creation date descending (newest first), then by
       file size descending (big files = real work sessions).
    4. Read the tail of the top matches — last ~50 text entries — to
       check for completion signals, errors, or progress.

Usage:
    python check-session.py --project mcp_servers --keywords "glpi,get_items,400"
    python check-session.py --keywords "email,federico"  # uses _default
"""

import argparse
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

SIGNAL_DIR = Path.home() / ".claude" / "signal"
PROJECTS_JSON = SIGNAL_DIR / "projects.json"
SESSIONS_BASE = Path.home() / ".claude" / "projects"


def path_to_dirname(path: str) -> str:
    """Convert a filesystem path to Claude Code's session directory name."""
    return re.sub(r"[:\\/_ ]", "-", path)


def load_projects() -> dict:
    with open(PROJECTS_JSON) as f:
        return json.load(f)


def find_session_dirs(project: str | None) -> list[Path]:
    """Get all session directories for a project."""
    projects = load_projects()
    key = project if project and project in projects else "_default"
    paths = projects.get(key, projects["_default"])

    dirs = []
    for p in paths:
        dirname = path_to_dirname(p)
        session_dir = SESSIONS_BASE / dirname
        if session_dir.is_dir():
            dirs.append(session_dir)
    return dirs


def grep_sessions(session_dirs: list[Path], keywords: list[str]) -> list[dict]:
    """Find .jsonl files matching any keyword. Returns list of {path, size, mtime}."""
    pattern = "|".join(re.escape(k) for k in keywords)
    matches = {}

    for d in session_dirs:
        jsonl_files = list(d.glob("*.jsonl"))
        if not jsonl_files:
            continue

        try:
            result = subprocess.run(
                ["grep", "-Erl", "-i", pattern] + [str(f) for f in jsonl_files],
                capture_output=True, text=True, timeout=30
            )
            for line in result.stdout.strip().splitlines():
                if line:
                    p = Path(line)
                    stat = p.stat()
                    matches[str(p)] = {
                        "path": str(p),
                        "session_id": p.stem,
                        "size": stat.st_size,
                        "ctime": stat.st_ctime,
                        "date": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d"),
                    }
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    return sorted(matches.values(), key=lambda x: (x["date"], x["size"]), reverse=True)


def extract_tail(path: str, lines: int = 50) -> list[str]:
    """Extract the last N text content entries from a session .jsonl file."""
    texts = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for raw_line in f:
                try:
                    entry = json.loads(raw_line)
                    # Extract text from assistant messages
                    if entry.get("type") == "assistant":
                        msg = entry.get("message", {})
                        for block in msg.get("content", []):
                            if isinstance(block, dict) and block.get("type") == "text":
                                texts.append(block["text"])
                            elif isinstance(block, str):
                                texts.append(block)
                    # Extract text from user messages
                    elif entry.get("type") == "user":
                        msg = entry.get("message", {})
                        content = msg.get("content", "")
                        if isinstance(content, str):
                            texts.append(f"[USER] {content}")
                        elif isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    texts.append(f"[USER] {block['text']}")
                except json.JSONDecodeError:
                    continue
    except Exception:
        return []

    return texts[-lines:]


def main():
    parser = argparse.ArgumentParser(description="Check session logs for task progress")
    parser.add_argument("--project", type=str, default=None, help="Project name from projects.json")
    parser.add_argument("--keywords", type=str, required=True, help="Comma-separated keywords to search")
    parser.add_argument("--tail", type=int, default=50, help="Number of text entries to show from tail")
    parser.add_argument("--top", type=int, default=3, help="Number of top sessions to return")
    args = parser.parse_args()

    keywords = [k.strip() for k in args.keywords.split(",") if k.strip()]
    session_dirs = find_session_dirs(args.project)

    if not session_dirs:
        print(json.dumps({"error": f"No session dirs found for project: {args.project}"}))
        return

    matches = grep_sessions(session_dirs, keywords)

    if not matches:
        print(json.dumps({"error": "No sessions matched keywords", "keywords": keywords}))
        return

    results = []
    for m in matches[:args.top]:
        tail = extract_tail(m["path"], args.tail)
        results.append({
            "session_id": m["session_id"],
            "date": m["date"],
            "size_kb": round(m["size"] / 1024),
            "tail": tail,
        })

    print(json.dumps({"matches": len(matches), "sessions": results}, indent=2))


if __name__ == "__main__":
    main()
