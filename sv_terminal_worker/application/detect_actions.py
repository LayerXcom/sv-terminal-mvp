from __future__ import annotations

from sv_terminal_worker.domain.markers import find_markers, is_proposal_approval
from sv_terminal_worker.domain.models import DetectedAction, IssueContext


def detect_approved_proposal(issue_context: IssueContext) -> DetectedAction | None:
    for comment in issue_context.comments:
        for marker in find_markers(comment.body):
            if is_proposal_approval(marker):
                return DetectedAction(approval=marker, comment=comment)
    return None
