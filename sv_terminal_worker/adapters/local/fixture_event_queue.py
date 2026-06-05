from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sv_terminal_worker.domain.models import QueuedEvent


class FixtureEventQueue:
    def __init__(self, event_file: Path):
        self.event_file = event_file
        self.statuses: dict[str, str] = {}

    def poll_queued(self, limit: int = 10) -> list[QueuedEvent]:
        data = _load_events(self.event_file)
        queued = [event for event in data if event.get("status", "queued") == "queued"]
        return [_event_from_dict(event) for event in queued[:limit]]

    def mark_processing(self, event_id: str) -> None:
        self.statuses[event_id] = "processing"

    def mark_processed(self, event_id: str, result: str) -> None:
        self.statuses[event_id] = f"processed:{result}"

    def mark_failed(self, event_id: str, reason: str) -> None:
        self.statuses[event_id] = f"failed:{reason}"


def _load_events(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = data.get("events", [])
    if not isinstance(data, list):
        raise ValueError("event fixture must be a list or {events: []}")
    return data


def _event_from_dict(data: dict[str, Any]) -> QueuedEvent:
    return QueuedEvent(
        event_id=data["event_id"],
        type=data["type"],
        linear_issue_identifier=data["linear_issue_identifier"],
        source=data.get("source"),
        dedupe_key=data.get("dedupe_key"),
        payload=data.get("payload_json") or data.get("payload") or {},
    )
