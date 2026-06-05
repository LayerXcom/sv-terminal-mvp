from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class WorkerResult:
    issue_identifier: str
    action_id: str
    status: str
    message: str
    context_path: str | None = None
    state_path: str | None = None

