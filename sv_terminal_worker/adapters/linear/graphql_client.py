from __future__ import annotations

import json
import urllib.request
from typing import Any


class LinearGraphQLClient:
    def __init__(self, api_key: str, endpoint: str = "https://api.linear.app/graphql"):
        self.api_key = api_key
        self.endpoint = endpoint

    def execute(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        body = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
        request = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={
                "Authorization": self.api_key,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
        if payload.get("errors"):
            raise RuntimeError(f"Linear GraphQL errors: {payload['errors']}")
        return payload["data"]
