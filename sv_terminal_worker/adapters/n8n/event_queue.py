from __future__ import annotations

import json
import urllib.parse
import urllib.request
from typing import Any

from sv_terminal_worker.domain.models import QueuedEvent


class N8nEventQueue:
    def __init__(self, base_url: str, api_key: str, data_table_id: str):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.data_table_id = data_table_id

    def poll_queued(self, limit: int = 10) -> list[QueuedEvent]:
        query = urllib.parse.urlencode({"limit": str(limit)})
        payload = self._request("GET", f"{self._rows_path()}?{query}")
        rows = _rows_from_payload(payload)
        queued = [row for row in rows if row.get("status") == "queued"]
        return [_event_from_dict(row) for row in queued[:limit]]

    def mark_processing(self, event_id: str) -> None:
        self._update_row(event_id, {"status": "processing"})

    def mark_processed(self, event_id: str, result: str) -> None:
        self._update_row(event_id, {"status": "processed", "last_result": result})

    def mark_failed(self, event_id: str, reason: str) -> None:
        self._update_row(event_id, {"status": "failed", "last_error": reason})

    def _update_row(self, event_id: str, data: dict[str, Any]) -> None:
        self._request(
            "PATCH",
            f"{self._rows_path()}/update",
            {
                "filter": {
                    "type": "and",
                    "filters": [
                        {"columnName": "event_id", "condition": "eq", "value": event_id},
                    ],
                },
                "data": data,
                "returnData": False,
            },
        )

    def _rows_path(self) -> str:
        return f"/data-tables/{urllib.parse.quote(self.data_table_id)}/rows"

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


def _rows_from_payload(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict):
        return []
    rows = payload.get("data") or payload.get("rows") or payload.get("items") or payload.get("events") or []
    if not isinstance(rows, list):
        return []
    return rows


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
