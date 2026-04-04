"""Monday.com API client — thin wrapper over the GraphQL API."""

import httpx

API_URL = "https://api.monday.com/v2"
API_VERSION = "2025-01"


class MondayClient:
    def __init__(self, token: str):
        self._token = token
        self._headers = {
            "Authorization": token,
            "Content-Type": "application/json",
            "API-Version": API_VERSION,
        }

    def _query(self, query: str, variables: dict | None = None) -> dict:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = httpx.post(API_URL, json=payload, headers=self._headers, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if "errors" in data:
            raise RuntimeError(f"Monday API error: {data['errors']}")
        return data["data"]

    def list_workspaces(self, limit: int = 100, page: int = 1) -> list[dict]:
        query = """
        query listWorkspaces($limit: Int!, $page: Int!) {
            workspaces(limit: $limit, page: $page) {
                id
                name
                description
            }
        }
        """
        data = self._query(query, {"limit": limit, "page": page})
        return data.get("workspaces") or []

    def list_boards(self, limit: int = 100, page: int = 1) -> list[dict]:
        query = """
        query listBoards($limit: Int!, $page: Int!) {
            boards(limit: $limit, page: $page) {
                id
                name
                type
                url
                workspace { id name }
            }
        }
        """
        variables: dict = {"limit": limit, "page": page}
        data = self._query(query, variables)
        boards = data.get("boards") or []
        return [b for b in boards if b.get("type") == "board"]
