from __future__ import annotations


def render_pr_open_preview(context_packet: dict) -> str:
    issue = context_packet["issue"]
    approval = context_packet["approval"]
    return "\n".join(
        [
            "## PR Open Preview",
            "",
            f"- Linear issue: {issue['identifier']}",
            f"- Action ID: {approval['action_id']}",
            "- Result: context built; PR/backtest execution is not enabled in Step 1-3.",
            "",
            (
                f"[SV_ACTION_RESULT id={approval['action_id']} status=preview "
                "result=pr_open_pending target=linked_pr "
                f"linear_issue={issue['identifier']}]"
            ),
            "",
        ]
    )
