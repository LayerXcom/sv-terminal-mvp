from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from sv_terminal_worker.domain.models import QueuedEvent


class N8nEventQueue:
    def __init__(self, base_url: str, api_key: str, event_path: str = "/sv-terminal/events"):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.event_path = event_path

    def poll_queued(self, limit: int = 10) -> list[QueuedEvent]:
        query = urllib.parse.urlencode({"status": "queued", "limit": str(limit)})
        payload = self._request("GET", f"{self.event_path}?{query}")
        events = payload.get("events", payload if isinstance(payload, list) else [])
        return [_event_from_dict(event) for event in events]

    def mark_processing(self, event_id: str) -> None:
        self._update_status(event_id, "processing", None)

    def mark_processed(self, event_id: str, result: str) -> None:
        self._update_status(event_id, "processed", result)

    def mark_failed(self, event_id: str, reason: str) -> None:
        self._update_status(event_id, "failed", reason)

    def _update_status(self, event_id: str, status: str, message: str | None) -> None:
        self._request("POST", f"{self.event_path}/{event_id}/status", {"status": status, "message": message})

    def _request(self, method: str, path: str, data: dict[str, Any] | None = None) -> Any:
        body = json.dumps(data).encode("utf-8") if data is not None else None
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={
                "X-N8N-API-KEY": self.api_key,
                "Content-Type": "application/json",
            },
            method=method,
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            text = response.read().decode("utf-8")
        return json.loads(text) if text else {}


def _event_from_dict(data: dict[str, Any]) -> QueuedEvent:
    payload = data.get("payload_json") or data.get("payload") or {}
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError:
            payload = {"raw": payload}
    return QueuedEvent(
        event_id=data["event_id"],
        type=data["type"],
        linear_issue_identifier=data["linear_issue_identifier"],
        source=data.get("source"),
        dedupe_key=data.get("dedupe_key"),
        payload=payload,
    )
