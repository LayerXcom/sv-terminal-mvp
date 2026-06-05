from __future__ import annotations

from typing import Protocol

from sv_terminal_worker.domain.models import QueuedEvent


class EventQueue(Protocol):
    def poll_queued(self, limit: int = 10) -> list[QueuedEvent]:
        raise NotImplementedError

    def mark_processing(self, event_id: str) -> None:
        raise NotImplementedError

    def mark_processed(self, event_id: str, result: str) -> None:
        raise NotImplementedError

    def mark_failed(self, event_id: str, reason: str) -> None:
        raise NotImplementedError
