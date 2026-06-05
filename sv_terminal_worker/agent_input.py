from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_context(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def render_agent_input(context: dict[str, Any]) -> str:
    issue = context["issue"]
    approval = context["approval"]
    proposal = context["proposal"]
    decision_memo = context.get("decision_memo", {})

    return "\n".join(
        [
            f"# PR Agent Input: {issue['identifier']}",
            "",
            "## Linear Issue",
            "",
            f"- Identifier: {issue['identifier']}",
            f"- Title: {issue['title']}",
            f"- URL: {issue['url']}",
            "",
            "## Approval",
            "",
            f"- Action ID: {approval['action_id']}",
            f"- Decision: {approval['decision']}",
            f"- By: {approval['by']}",
            f"- Proposal target: {proposal['target']}",
            "",
            "## Decision Memo",
            "",
            decision_memo.get("body") or "No decision memo found.",
            "",
            "## Rule Proposal",
            "",
            proposal.get("body") or "No proposal body found.",
            "",
            "## PR Requirements",
            "",
            f"- Branch: codex/{issue['identifier']}-<short-slug>",
            f"- PR title prefix: {issue['identifier']}",
            f"- PR description must include: References {issue['identifier']}",
            "- Do not use closing magic words.",
            "- Do not expand scope beyond the approved proposal.",
            "",
        ]
    )


def write_agent_input(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
