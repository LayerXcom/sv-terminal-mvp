from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sv_terminal_worker.adapters.local.file_run_store import FileRunStore
from sv_terminal_worker.adapters.local.fixture_issue_repository import comment_from_dict, issue_from_dict
from sv_terminal_worker.application.build_context import build_context_packet as _build_context_packet
from sv_terminal_worker.application.detect_actions import detect_approved_proposal as _detect_approved_proposal
from sv_terminal_worker.domain.models import DetectedAction, IssueContext


def load_issue_fixture(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    _validate_fixture(data)
    return data


def detect_approved_proposal(issue_data: dict[str, Any] | IssueContext) -> DetectedAction | None:
    issue_context = issue_data if isinstance(issue_data, IssueContext) else _issue_context_from_dict(issue_data)
    return _detect_approved_proposal(issue_context)


def build_context_packet(issue_data: dict[str, Any] | IssueContext, action: DetectedAction) -> dict[str, Any]:
    issue_context = issue_data if isinstance(issue_data, IssueContext) else _issue_context_from_dict(issue_data)
    return _build_context_packet(issue_context, action)


def write_run_files(base_dir: Path, context_packet: dict[str, Any]) -> dict[str, Path]:
    return FileRunStore(base_dir).write_context_and_state(context_packet, "proposal_approval")


def _validate_fixture(data: dict[str, Any]) -> None:
    if not isinstance(data.get("issue"), dict):
        raise ValueError("fixture requires issue object")
    if not isinstance(data.get("comments"), list):
        raise ValueError("fixture requires comments array")


def _issue_context_from_dict(data: dict[str, Any]) -> IssueContext:
    return IssueContext(
        issue=issue_from_dict(data["issue"]),
        comments=[comment_from_dict(comment) for comment in data.get("comments", [])],
        linked_prs=data.get("linkedPrs", []),
    )
