from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .agent_input import load_context, render_agent_input, write_agent_input
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


if __name__ == "__main__":
    raise SystemExit(main())
