from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import json
from typing import Any

from sv_terminal_worker.domain.markers import find_markers, is_proposal_approval


@dataclass(frozen=True)
class QueueRow:
    event_id: str
    source: str
    source_event_id: str | None
    linear_issue_id: str | None
    linear_issue_identifier: str
    linear_comment_id: str | None
    type: str
    status: str
    priority: int
    actor_kind: str | None
    actor_id: str | None
    dedupe_key: str
    payload_json: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "source": self.source,
            "source_event_id": self.source_event_id,
            "linear_issue_id": self.linear_issue_id,
            "linear_issue_identifier": self.linear_issue_identifier,
            "linear_comment_id": self.linear_comment_id,
            "type": self.type,
            "status": self.status,
            "priority": self.priority,
            "actor_kind": self.actor_kind,
            "actor_id": self.actor_id,
            "dedupe_key": self.dedupe_key,
            "payload_json": json.dumps(self.payload_json, ensure_ascii=False),
        }


def verify_linear_signature(raw_body: bytes, signature: str | None, secret: str) -> bool:
    if not signature:
        return False
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    actual = signature.removeprefix("sha256=").strip()
    return hmac.compare_digest(expected, actual)


def normalize_linear_comment_marker(payload: dict[str, Any]) -> QueueRow | None:
    data = payload.get("data") or {}
    if _event_entity(payload) != "Comment":
        return None

    body = data.get("body") or ""
    approval = next((marker for marker in find_markers(body) if is_proposal_approval(marker)), None)
    if approval is None:
        return None

    issue = data.get("issue") or {}
    issue_identifier = issue.get("identifier") or data.get("issueIdentifier")
    if not issue_identifier:
        return None

    action_id = approval.get("action_id")
    if not action_id:
        return None

    comment_id = data.get("id")
    source_event_id = payload.get("webhookTimestamp") or payload.get("createdAt") or payload.get("id")
    event_id = f"evt_linear_{issue_identifier}_{action_id}"

    return QueueRow(
        event_id=_sanitize_event_id(event_id),
        source="linear",
        source_event_id=str(source_event_id) if source_event_id else None,
        linear_issue_id=issue.get("id") or data.get("issueId"),
        linear_issue_identifier=issue_identifier,
        linear_comment_id=comment_id,
        type="linear_marker_detected",
        status="queued",
        priority=2,
        actor_kind="linear_user",
        actor_id=(data.get("user") or {}).get("id") or data.get("userId"),
        dedupe_key=f"linear:{issue_identifier}:{action_id}",
        payload_json={
            "action_id": action_id,
            "marker_type": approval.kind,
            "target": approval.get("target"),
            "decision": approval.get("decision"),
        },
    )


def _event_entity(payload: dict[str, Any]) -> str | None:
    return payload.get("type") or payload.get("model") or payload.get("entity") or payload.get("resourceType")


def _sanitize_event_id(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value)
