from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from .markers import Marker, find_markers, is_proposal_approval


@dataclass(frozen=True)
class DetectedAction:
    approval: Marker
    comment: dict[str, Any]


def load_issue_fixture(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    _validate_fixture(data)
    return data


def detect_approved_proposal(issue_data: dict[str, Any]) -> DetectedAction | None:
    for comment in issue_data.get("comments", []):
        for marker in find_markers(comment.get("body", "")):
            if is_proposal_approval(marker):
                return DetectedAction(approval=marker, comment=comment)
    return None


def build_context_packet(issue_data: dict[str, Any], action: DetectedAction) -> dict[str, Any]:
    issue = issue_data["issue"]
    proposal_target = action.approval.get("target", "proposal:v1")
    action_id = action.approval.get("action_id")

    return {
        "issue": {
            "id": issue.get("id"),
            "identifier": issue.get("identifier"),
            "title": issue.get("title"),
            "url": issue.get("url"),
            "project": issue.get("project"),
            "team": issue.get("team"),
            "status": issue.get("status"),
            "assignee": issue.get("assignee"),
            "labels": issue.get("labels", []),
        },
        "sources": {
            "synced_slack_thread": _thread_source(issue_data, "Slack Sync"),
            "proposal_delivery_thread": {
                "comment_thread_id": action.comment.get("id"),
                "proposal_target": proposal_target,
                "approval_action_id": action_id,
            },
        },
        "decision_memo": _extract_section(issue_data, "Decision Memo"),
        "proposal": {
            "target": proposal_target,
            "recommended_resolution": _detect_resolution(issue_data),
            "body": action.comment.get("body", ""),
        },
        "approval": {
            "action_id": action_id,
            "decision": action.approval.get("decision"),
            "by": action.approval.get("by"),
            "comment_url": action.comment.get("url"),
        },
    }


def write_run_files(base_dir: Path, context_packet: dict[str, Any]) -> dict[str, Path]:
    issue_id = context_packet["issue"]["identifier"]
    action_id = context_packet["approval"]["action_id"]
    if not issue_id or not action_id:
        raise ValueError("context packet requires issue.identifier and approval.action_id")

    run_dir = base_dir / "runs" / issue_id / action_id
    run_dir.mkdir(parents=True, exist_ok=True)

    context_path = run_dir / "context.json"
    state_path = run_dir / "state.json"

    _write_json(context_path, context_packet)
    _write_json(
        state_path,
        {
            "action_id": action_id,
            "linear_identifier": issue_id,
            "status": "context_built",
            "branch": None,
            "pr_url": None,
            "backtest_run_id": None,
        },
    )

    return {"run_dir": run_dir, "context": context_path, "state": state_path}


def _validate_fixture(data: dict[str, Any]) -> None:
    if not isinstance(data.get("issue"), dict):
        raise ValueError("fixture requires issue object")
    if not isinstance(data.get("comments"), list):
        raise ValueError("fixture requires comments array")


def _thread_source(issue_data: dict[str, Any], thread_name: str) -> dict[str, Any]:
    for comment in issue_data.get("comments", []):
        if comment.get("threadName") == thread_name:
            return {
                "linear_comment_thread_id": comment.get("id"),
                "slack_url": comment.get("slackUrl"),
                "available": True,
            }
    return {"linear_comment_thread_id": None, "slack_url": None, "available": False}


def _extract_section(issue_data: dict[str, Any], heading: str) -> dict[str, Any]:
    for comment in issue_data.get("comments", []):
        body = comment.get("body", "")
        if heading in body:
            return {"target": "decision_memo:v1", "body": body}
    return {"target": None, "body": None}


def _detect_resolution(issue_data: dict[str, Any]) -> str:
    labels = issue_data.get("issue", {}).get("labels", [])
    if "resolution:rule-change" in labels or "resolution:rule_change" in labels:
        return "rule_change"
    return "rule_change"


def _write_json(path: Path, data: dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
