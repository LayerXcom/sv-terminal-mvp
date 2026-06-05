from __future__ import annotations

from sv_terminal_worker.domain.models import DetectedAction, IssueComment, IssueContext


def build_context_packet(issue_context: IssueContext, action: DetectedAction) -> dict:
    issue = issue_context.issue
    proposal_target = action.approval.get("target", "proposal:v1")
    action_id = action.approval.get("action_id")

    return {
        "issue": {
            "id": issue.id,
            "identifier": issue.identifier,
            "title": issue.title,
            "url": issue.url,
            "project": issue.project,
            "team": issue.team,
            "status": issue.status,
            "assignee": issue.assignee,
            "labels": issue.labels,
        },
        "sources": {
            "synced_slack_thread": _thread_source(issue_context.comments, "Slack Sync"),
            "proposal_delivery_thread": {
                "comment_thread_id": action.comment.id,
                "proposal_target": proposal_target,
                "approval_action_id": action_id,
            },
        },
        "decision_memo": _extract_section(issue_context.comments, "Decision Memo"),
        "proposal": {
            "target": proposal_target,
            "recommended_resolution": _detect_resolution(issue.labels),
            "body": action.comment.body,
        },
        "approval": {
            "action_id": action_id,
            "decision": action.approval.get("decision"),
            "by": action.approval.get("by"),
            "comment_url": action.comment.url,
        },
        "linked_prs": issue_context.linked_prs,
    }


def _thread_source(comments: list[IssueComment], thread_name: str) -> dict:
    for comment in comments:
        if comment.thread_name == thread_name:
            return {
                "linear_comment_thread_id": comment.id,
                "slack_url": comment.slack_url,
                "available": True,
            }
    return {"linear_comment_thread_id": None, "slack_url": None, "available": False}


def _extract_section(comments: list[IssueComment], heading: str) -> dict:
    for comment in comments:
        if heading in comment.body:
            return {"target": "decision_memo:v1", "body": comment.body}
    return {"target": None, "body": None}


def _detect_resolution(labels: list[str]) -> str:
    if "resolution:rule-change" in labels or "resolution:rule_change" in labels:
        return "rule_change"
    return "rule_change"
