from __future__ import annotations

from typing import Protocol

from sv_terminal_worker.domain.models import IssueContext


class IssueRepository(Protocol):
    def get_issue(self, identifier: str) -> IssueContext:
        raise NotImplementedError

    def write_event_log(self, issue_id: str, body: str) -> None:
        raise NotImplementedError

    def write_proposal_delivery(self, issue_id: str, body: str) -> None:
        raise NotImplementedError

    def update_status(self, issue_id: str, status: str) -> None:
        raise NotImplementedError

    def update_assignee(self, issue_id: str, assignee: str) -> None:
        raise NotImplementedError
