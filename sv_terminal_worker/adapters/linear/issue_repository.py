from __future__ import annotations

from typing import Any

from sv_terminal_worker.domain.models import Issue, IssueComment, IssueContext

from .graphql_client import LinearGraphQLClient


ISSUE_QUERY = """
query IssueForWorker($identifier: String!) {
  issue(id: $identifier) {
    id
    identifier
    title
    url
    team { key name }
    project { name }
    state { name }
    assignee { name email }
    labels { nodes { name } }
    comments(first: 100) {
      nodes {
        id
        body
        url
        parent { id }
      }
    }
    attachments(first: 50) {
      nodes {
        id
        title
        url
        subtitle
      }
    }
  }
}
"""

CREATE_COMMENT_MUTATION = """
mutation CreateComment($issueId: String!, $body: String!) {
  commentCreate(input: { issueId: $issueId, body: $body }) {
    success
    comment { id url }
  }
}
"""

UPDATE_ISSUE_MUTATION = """
mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
  issueUpdate(id: $id, input: $input) {
    success
    issue { id identifier }
  }
}
"""


class LinearIssueRepository:
    def __init__(self, client: LinearGraphQLClient):
        self.client = client

    def get_issue(self, identifier: str) -> IssueContext:
        data = self.client.execute(ISSUE_QUERY, {"identifier": identifier})
        raw = data["issue"]
        if raw is None:
            raise ValueError(f"Linear issue not found: {identifier}")

        labels = [node["name"] for node in raw.get("labels", {}).get("nodes", [])]
        issue = Issue(
            id=raw.get("id"),
            identifier=raw.get("identifier"),
            title=raw.get("title"),
            url=raw.get("url"),
            project=(raw.get("project") or {}).get("name"),
            team=(raw.get("team") or {}).get("key"),
            status=(raw.get("state") or {}).get("name"),
            assignee=(raw.get("assignee") or {}).get("name"),
            labels=labels,
        )
        comments = [_comment_from_node(node) for node in raw.get("comments", {}).get("nodes", [])]
        linked_prs = [_attachment_to_pr(node) for node in raw.get("attachments", {}).get("nodes", []) if _looks_like_pr(node)]
        return IssueContext(issue=issue, comments=comments, linked_prs=linked_prs)

    def write_event_log(self, issue_id: str, body: str) -> None:
        self.client.execute(CREATE_COMMENT_MUTATION, {"issueId": issue_id, "body": body})

    def write_proposal_delivery(self, issue_id: str, body: str) -> None:
        self.client.execute(CREATE_COMMENT_MUTATION, {"issueId": issue_id, "body": body})

    def update_status(self, issue_id: str, status: str) -> None:
        self.client.execute(UPDATE_ISSUE_MUTATION, {"id": issue_id, "input": {"stateId": status}})

    def update_assignee(self, issue_id: str, assignee: str) -> None:
        self.client.execute(UPDATE_ISSUE_MUTATION, {"id": issue_id, "input": {"assigneeId": assignee}})


def _comment_from_node(node: dict[str, Any]) -> IssueComment:
    body = node.get("body") or ""
    return IssueComment(
        id=node["id"],
        body=body,
        thread_name=_guess_thread_name(body),
        url=node.get("url"),
        slack_url=_extract_slack_url(body),
    )


def _guess_thread_name(body: str) -> str | None:
    if "SV Terminal Event Log" in body:
        return "Event Log"
    if "Rule Proposal" in body or "Decision Memo" in body:
        return "Proposal & Delivery"
    if "Slack" in body or "slack.com/archives" in body:
        return "Slack Sync"
    return None


def _extract_slack_url(body: str) -> str | None:
    for token in body.split():
        if "slack.com/archives/" in token:
            return token.strip("<>()[]")
    return None


def _looks_like_pr(node: dict[str, Any]) -> bool:
    text = " ".join(str(node.get(key) or "") for key in ("title", "subtitle", "url"))
    return "github.com" in text and "/pull/" in text


def _attachment_to_pr(node: dict[str, Any]) -> dict[str, Any]:
    return {"id": node.get("id"), "title": node.get("title"), "url": node.get("url"), "subtitle": node.get("subtitle")}
