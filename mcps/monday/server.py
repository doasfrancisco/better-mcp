"""Monday.com MCP Server — manage boards, items, and workspaces."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastmcp import FastMCP

from monday_client import MondayClient

load_dotenv(Path(__file__).parent / ".env")

MONDAY_TOKEN = os.getenv("MONDAY_API_TOKEN", "")

mcp = FastMCP("Monday")

_client: MondayClient | None = None


def _get_client() -> MondayClient:
    global _client
    if _client is None:
        if not MONDAY_TOKEN:
            raise RuntimeError(
                "MONDAY_API_TOKEN environment variable is not set. "
                "Get your token from https://developer.monday.com/api-reference/docs/authentication"
            )
        _client = MondayClient(MONDAY_TOKEN)
    return _client


def _json(data) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False)


@mcp.tool()
def monday_list_workspaces(limit: int = 100, page: int = 1) -> str:
    """List all workspaces in the Monday.com account.

    Args:
        limit: Number of workspaces to return (max 100).
        page: Page number for pagination.
    """
    workspaces = _get_client().list_workspaces(limit=limit, page=page)
    if not workspaces:
        return "No workspaces found."
    return _json(workspaces)


@mcp.tool()
def monday_list_boards(limit: int = 100, page: int = 1) -> str:
    """List all boards. Each board includes which workspace it belongs to.

    Args:
        limit: Number of boards to return (max 100).
        page: Page number for pagination.
    """
    boards = _get_client().list_boards(limit=limit, page=page)
    if not boards:
        return "No boards found."
    return _json(boards)


if __name__ == "__main__":
    mcp.run()
