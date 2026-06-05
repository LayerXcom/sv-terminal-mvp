from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

from .agent_input import load_context, render_agent_input, write_agent_input
from .adapters.linear.graphql_client import LinearGraphQLClient
from .adapters.linear.issue_repository import LinearIssueRepository
from .adapters.local.file_run_store import FileRunStore
from .adapters.local.fixture_event_queue import FixtureEventQueue
from .adapters.local.fixture_issue_repository import FixtureIssueRepository
from .adapters.n8n.event_queue import N8nEventQueue
from .application.run_worker import WorkerConfig, poll_loop, run_action
from .context import build_context_packet, detect_approved_proposal, load_issue_fixture, write_run_files
from .markers import parse_marker


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sv-terminal-worker")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_marker_parser = subparsers.add_parser("parse-marker")
    parse_marker_parser.add_argument("marker")

    dry_run_parser = subparsers.add_parser("dry-run")
    dry_run_parser.add_argument("--issue-file", required=True, type=Path)
    dry_run_parser.add_argument("--run-dir", type=Path, default=Path(".sv-terminal"))

    poll_parser = subparsers.add_parser("poll")
    poll_parser.add_argument("--once", action="store_true")
    poll_parser.add_argument("--interval-seconds", type=int, default=30)
    poll_parser.add_argument("--limit", type=int, default=10)
    poll_parser.add_argument("--event-source", choices=["fixture", "n8n"], default="fixture")
    poll_parser.add_argument("--issue-source", choices=["fixture", "linear"], default="fixture")
    poll_parser.add_argument("--event-file", type=Path, default=Path("fixtures/events/approved_proposal_event.json"))
    poll_parser.add_argument("--issue-file", type=Path, default=Path("fixtures/issues/approved_rule_change.json"))
    poll_parser.add_argument("--run-dir", type=Path, default=Path(".sv-terminal"))

    run_action_parser = subparsers.add_parser("run-action")
    run_action_parser.add_argument("--issue", required=True)
    run_action_parser.add_argument("--action-id", required=True)
    run_action_parser.add_argument("--issue-source", choices=["fixture", "linear"], default="fixture")
    run_action_parser.add_argument("--issue-file", type=Path, default=Path("fixtures/issues/approved_rule_change.json"))
    run_action_parser.add_argument("--run-dir", type=Path, default=Path(".sv-terminal"))

    agent_input_parser = subparsers.add_parser("build-agent-input")
    agent_input_parser.add_argument("--context-file", required=True, type=Path)
    agent_input_parser.add_argument("--output", type=Path)

    args = parser.parse_args(argv)

    if args.command == "parse-marker":
        marker = parse_marker(args.marker)
        print(json.dumps({"kind": marker.kind, "attrs": dict(marker.attrs)}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "dry-run":
        issue_data = load_issue_fixture(args.issue_file)
        action = detect_approved_proposal(issue_data)
        if action is None:
            print("No approved proposal marker found.", file=sys.stderr)
            return 2
        context_packet = build_context_packet(issue_data, action)
        paths = write_run_files(args.run_dir, context_packet)
        print(json.dumps({key: str(value) for key, value in paths.items()}, ensure_ascii=False, indent=2))
        return 0

    if args.command == "poll":
        queue = _build_event_queue(args)
        issues = _build_issue_repository(args)
        runs = FileRunStore(args.run_dir)
        results = poll_loop(
            queue,
            issues,
            runs,
            WorkerConfig(once=args.once, interval_seconds=args.interval_seconds, limit=args.limit),
        )
        print(json.dumps([result.__dict__ for result in results], ensure_ascii=False, indent=2))
        return 0

    if args.command == "run-action":
        issues = _build_issue_repository(args)
        runs = FileRunStore(args.run_dir)
        result = run_action(args.issue, args.action_id, issues, runs)
        print(json.dumps(result.__dict__, ensure_ascii=False, indent=2))
        return 0

    if args.command == "build-agent-input":
        context = load_context(args.context_file)
        content = render_agent_input(context)
        if args.output:
            write_agent_input(args.output, content)
            print(str(args.output))
        else:
            print(content)
        return 0

    parser.error(f"unknown command: {args.command}")
    return 2


def _build_issue_repository(args: argparse.Namespace):
    if getattr(args, "issue_source", "fixture") == "linear":
        api_key = os.environ.get("LINEAR_API_KEY")
        if not api_key:
            raise SystemExit("LINEAR_API_KEY is required for --issue-source linear")
        return LinearIssueRepository(LinearGraphQLClient(api_key))
    return FixtureIssueRepository(args.issue_file)


def _build_event_queue(args: argparse.Namespace):
    if getattr(args, "event_source", "fixture") == "n8n":
        base_url = os.environ.get("N8N_API_BASE_URL") or os.environ.get("N8N_BASE_URL")
        api_key = os.environ.get("N8N_API_KEY")
        data_table_id = os.environ.get("N8N_DATATABLE_ID")
        if not base_url or not api_key or not data_table_id:
            raise SystemExit("N8N_API_BASE_URL, N8N_API_KEY, and N8N_DATATABLE_ID are required for --event-source n8n")
        return N8nEventQueue(base_url, api_key, data_table_id)
    return FixtureEventQueue(args.event_file)


if __name__ == "__main__":
    raise SystemExit(main())
