from __future__ import annotations

from dataclasses import dataclass
import time

from sv_terminal_worker.application.build_context import build_context_packet
from sv_terminal_worker.application.detect_actions import detect_approved_proposal
from sv_terminal_worker.application.writeback import render_pr_open_preview
from sv_terminal_worker.domain.events import WorkerResult
from sv_terminal_worker.domain.models import QueuedEvent
from sv_terminal_worker.ports.event_queue import EventQueue
from sv_terminal_worker.ports.issue_repository import IssueRepository
from sv_terminal_worker.ports.run_store import RunStore


@dataclass(frozen=True)
class WorkerConfig:
    once: bool = False
    interval_seconds: int = 30
    limit: int = 10
    action_type: str = "proposal_approval"


def run_action(issue_identifier: str, action_id: str, issues: IssueRepository, runs: RunStore) -> WorkerResult:
    issue_context = issues.get_issue(issue_identifier)
    action = detect_approved_proposal(issue_context)
    if action is None:
        return WorkerResult(issue_identifier, action_id, "skipped", "No approved proposal marker found.")
    if action.approval.get("action_id") != action_id:
        return WorkerResult(issue_identifier, action_id, "skipped", "Approved proposal action_id did not match.")
    if runs.already_processed(issue_identifier, action_id, "proposal_approval"):
        return WorkerResult(issue_identifier, action_id, "skipped", "Action already processed.")

    context_packet = build_context_packet(issue_context, action)
    paths = runs.write_context_and_state(context_packet, "proposal_approval")
    issues.write_event_log(issue_context.issue.id or issue_identifier, render_pr_open_preview(context_packet))

    return WorkerResult(
        issue_identifier=issue_identifier,
        action_id=action_id,
        status="context_built",
        message="Context packet and state file written.",
        context_path=str(paths.get("context")),
        state_path=str(paths.get("state")),
    )


def process_event(event: QueuedEvent, issues: IssueRepository, runs: RunStore) -> WorkerResult:
    issue_context = issues.get_issue(event.linear_issue_identifier)
    action = detect_approved_proposal(issue_context)
    if action is None:
        return WorkerResult(event.linear_issue_identifier, event.event_id, "skipped", "No approved proposal marker found.")

    action_id = action.approval.get("action_id")
    if not action_id:
        return WorkerResult(event.linear_issue_identifier, event.event_id, "failed", "Approved marker has no action_id.")
    if runs.already_processed(event.linear_issue_identifier, action_id, "proposal_approval"):
        return WorkerResult(event.linear_issue_identifier, action_id, "skipped", "Action already processed.")

    context_packet = build_context_packet(issue_context, action)
    paths = runs.write_context_and_state(context_packet, "proposal_approval")
    issues.write_event_log(issue_context.issue.id or event.linear_issue_identifier, render_pr_open_preview(context_packet))

    return WorkerResult(
        issue_identifier=event.linear_issue_identifier,
        action_id=action_id,
        status="context_built",
        message="Context packet and state file written.",
        context_path=str(paths.get("context")),
        state_path=str(paths.get("state")),
    )


def poll_loop(queue: EventQueue, issues: IssueRepository, runs: RunStore, config: WorkerConfig) -> list[WorkerResult]:
    all_results: list[WorkerResult] = []
    while True:
        events = queue.poll_queued(limit=config.limit)
        for event in events:
            queue.mark_processing(event.event_id)
            try:
                result = process_event(event, issues, runs)
                if result.status == "failed":
                    queue.mark_failed(event.event_id, result.message)
                else:
                    queue.mark_processed(event.event_id, result.message)
                all_results.append(result)
            except Exception as exc:
                queue.mark_failed(event.event_id, str(exc))
                all_results.append(
                    WorkerResult(event.linear_issue_identifier, event.event_id, "failed", str(exc))
                )
        if config.once:
            return all_results
        time.sleep(config.interval_seconds)
