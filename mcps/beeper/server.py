import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_log_dir = Path(__file__).parent / "logs"
_log_dir.mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    handlers=[RotatingFileHandler(_log_dir / "beeper.log", maxBytes=5_000_000, backupCount=1)],
)

from fastmcp import FastMCP
from beeper_client import build_client

mcp = FastMCP(
    "Beeper",
    instructions="""IMPORTANT: Always discover a tool's schema with ToolSearch BEFORE calling it for the first time.""",
)

_client = None
def _get_client():
    global _client
    if _client is None:
        _client = build_client()
    return _client

def _json(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)

def _to_dict(obj):
    if isinstance(obj, list):
        return [_to_dict(x) for x in obj]
    if hasattr(obj, "to_dict"):
        return obj.to_dict()
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj


# ── Tag store (tags.json) ────────────────────────────────────────────

_TAGS_PATH = Path(__file__).parent / "tags.json"

def _read_tags() -> dict:
    with _TAGS_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)
        
def _write_tags(data: dict) -> None:
    with _TAGS_PATH.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── WhatsApp-flavored tools ──────────────────────────────────────────

def _other_participant(chat: dict) -> dict:
    """Return the non-self participant of a DM (or empty dict)."""
    items = (chat.get("participants") or {}).get("items") or []
    for p in items:
        if not p.get("isSelf"):
            return p
    return {}

def _chat_matches(chat: dict, query: str) -> bool:
    """AND-of-words match on title, ids, and phone."""
    q_words = [w for w in query.lower().split() if w]
    if not q_words:
        return True
    other = _other_participant(chat)
    haystacks = [
        str(chat.get("title") or "").lower(),
        str(chat.get("id") or "").lower(),
        str(other.get("id") or "").lower(),
        str(other.get("fullName") or "").lower(),
        str(other.get("phoneNumber") or "").lower(),
    ]
    return all(any(qw in h for h in haystacks) for qw in q_words)

def _shape_chat(chat: dict, tags: list[str]) -> dict:
    """Project a Beeper Chat into the WhatsApp MCP contact shape."""
    is_group = chat.get("type") == "group"
    other = {} if is_group else _other_participant(chat)
    phone = (other.get("phoneNumber") or "").lstrip("+")
    return {
        "id": chat.get("id"),
        "name": chat.get("title"),
        "number": phone,
        "isGroup": is_group,
        "unreadCount": chat.get("unreadCount"),
        "pinned": chat.get("isPinned"),
        "archived": chat.get("isArchived"),
        "muted": chat.get("isMuted"),
        "lastActivity": chat.get("lastActivity"),
        "preview": chat.get("preview"),
        "tags": tags,
    }


@mcp.tool()
def whatsapp_list_contacts(
    query: str | None = None,
    tag: str | None = None,
) -> str:
    """List WhatsApp chats (DMs + groups). At least one of `query` or `tag` is required.
      • query  — substring match on chat title, id, contact name, or phone
      • tag    — filter by tag (e.g. family, work, partner, followup)

    Each result includes its tags. Pass a result's id into whatsapp_get_messages
    to read the conversation.

    Default tags: family, work, partner, followup. Custom tags are auto-created
    on first use via whatsapp_tag_contacts.
    """
    if not query and not tag:
        return "Pass at least one of `query` or `tag`."

    client = _get_client()
    contact_tags = _read_tags().get("contacts", {})

    chats = [_to_dict(c) for c in client.chats.list(account_ids=["whatsapp"])]

    if query:
        chats = [c for c in chats if _chat_matches(c, query)]
    if tag:
        chats = [c for c in chats if tag in contact_tags.get(c.get("id") or "", [])]

    shaped = [_shape_chat(c, contact_tags.get(c.get("id") or "", [])) for c in chats]
    return _json(shaped)


if __name__ == "__main__":
    mcp.run()
