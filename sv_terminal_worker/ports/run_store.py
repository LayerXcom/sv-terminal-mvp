from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol


class RunStore(Protocol):
    def already_processed(self, issue_identifier: str, action_id: str, action_type: str) -> bool:
        raise NotImplementedError

    def write_context_and_state(self, context_packet: dict[str, Any], action_type: str) -> dict[str, Path]:
        raise NotImplementedError
