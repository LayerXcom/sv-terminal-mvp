from __future__ import annotations

import json
from pathlib import Path
from typing import Any


class FileRunStore:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def already_processed(self, issue_identifier: str, action_id: str, action_type: str) -> bool:
        state_path = self._run_dir(issue_identifier, action_id) / "state.json"
        if not state_path.exists():
            return False
        with state_path.open("r", encoding="utf-8") as f:
            state = json.load(f)
        return state.get("status") not in {None, "failed"}

    def write_context_and_state(self, context_packet: dict[str, Any], action_type: str) -> dict[str, Path]:
        issue_id = context_packet["issue"]["identifier"]
        action_id = context_packet["approval"]["action_id"]
        if not issue_id or not action_id:
            raise ValueError("context packet requires issue.identifier and approval.action_id")

        run_dir = self._run_dir(issue_id, action_id)
        run_dir.mkdir(parents=True, exist_ok=True)

        context_path = run_dir / "context.json"
        state_path = run_dir / "state.json"

        _write_json(context_path, context_packet)
        _write_json(
            state_path,
            {
                "action_id": action_id,
                "linear_identifier": issue_id,
                "action_type": action_type,
                "status": "context_built",
                "branch": None,
                "pr_url": None,
                "backtest_run_id": None,
            },
        )

        return {"run_dir": run_dir, "context": context_path, "state": state_path}

    def _run_dir(self, issue_identifier: str, action_id: str) -> Path:
        return self.base_dir / "runs" / issue_identifier / action_id


def _write_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
