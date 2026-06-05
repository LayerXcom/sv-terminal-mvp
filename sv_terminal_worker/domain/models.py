from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .markers import Marker


@dataclass(frozen=True)
class Issue:
    id: str | None
    identifier: str
    title: str
    url: str | None = None
    project: str | None = None
    team: str | None = None
    status: str | None = None
    assignee: str | None = None
    labels: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class IssueComment:
    id: str
    body: str
    thread_name: str | None = None
    url: str | None = None
    slack_url: str | None = None


@dataclass(frozen=True)
class IssueContext:
    issue: Issue
    comments: list[IssueComment]
    linked_prs: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class DetectedAction:
    approval: Marker
    comment: IssueComment


@dataclass(frozen=True)
class QueuedEvent:
    event_id: str
    type: str
    linear_issue_identifier: str
    source: str | None = None
    dedupe_key: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
