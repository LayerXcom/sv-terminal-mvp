from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sv_terminal_worker.domain.models import Issue, IssueComment, IssueContext


class FixtureIssueRepository:
    def __init__(self, issue_file: Path):
        self.issue_file = issue_file
        self.writes: list[dict[str, str]] = []

    def get_issue(self, identifier: str) -> IssueContext:
        data = _load_fixture(self.issue_file)
        issue = issue_from_dict(data["issue"])
        if issue.identifier != identifier:
            raise ValueError(f"fixture issue is {issue.identifier}, not {identifier}")
        comments = [comment_from_dict(comment) for comment in data.get("comments", [])]
        return IssueContext(issue=issue, comments=comments, linked_prs=data.get("linkedPrs", []))

    def write_event_log(self, issue_id: str, body: str) -> None:
        self.writes.append({"kind": "event_log", "issue_id": issue_id, "body": body})

    def write_proposal_delivery(self, issue_id: str, body: str) -> None:
        self.writes.append({"kind": "proposal_delivery", "issue_id": issue_id, "body": body})

    def update_status(self, issue_id: str, status: str) -> None:
        self.writes.append({"kind": "status", "issue_id": issue_id, "body": status})

    def update_assignee(self, issue_id: str, assignee: str) -> None:
        self.writes.append({"kind": "assignee", "issue_id": issue_id, "body": assignee})


def issue_context_from_fixture(path: Path) -> IssueContext:
    data = _load_fixture(path)
    return IssueContext(
        issue=issue_from_dict(data["issue"]),
        comments=[comment_from_dict(comment) for comment in data.get("comments", [])],
        linked_prs=data.get("linkedPrs", []),
    )


def _load_fixture(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data.get("issue"), dict):
        raise ValueError("fixture requires issue object")
    if not isinstance(data.get("comments"), list):
        raise ValueError("fixture requires comments array")
    return data


def issue_from_dict(data: dict[str, Any]) -> Issue:
    return Issue(
        id=data.get("id"),
        identifier=data["identifier"],
        title=data.get("title", ""),
        url=data.get("url"),
        project=data.get("project"),
        team=data.get("team"),
        status=data.get("status"),
        assignee=data.get("assignee"),
        labels=data.get("labels", []),
    )


def comment_from_dict(data: dict[str, Any]) -> IssueComment:
    return IssueComment(
        id=data["id"],
        body=data.get("body", ""),
        thread_name=data.get("threadName"),
        url=data.get("url"),
        slack_url=data.get("slackUrl"),
    )
