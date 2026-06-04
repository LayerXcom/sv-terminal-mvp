# Linear Model and Markers

## Team and Project

Future state:

- Create a private Linear team such as `SV Ops`.
- Create one Linear Project per tenant.
- Suggested project naming: `SV Ops: <tenant_name>`.

MVP starting point:

- Use the existing `approval_agent` team.
- Use the existing project `SVのエスカレ・ルール変更周知などを複数テナント持てるようにする運用を考える` for cross-cutting design and implementation tasks.

## Issue Grain

A parent issue is one delivery unit.

Entry points:

- accounting inquiry
- operator escalation
- rule performance alert from an agent

Completion conditions:

- rule update is delivered and announced
- or the event is explicitly marked as a one-off decision
- or ownership is transferred to another product / operations issue

## Phases as Sub-Issues

MVP1 phases:

1. Intake / 問い合わせ受付
2. Accounting Discussion / 経理相談
3. Decision Capture / 方針確定
4. Rule Draft / ルール下書き
5. SV Review / SVレビュー
6. PR & Backtest / PR・バックテスト
7. Merge & Delivery / merge・本番反映
8. Announcement / 変更周知

MVP2 phases:

1. Alert Intake / 性能低下検知
2. Evidence Collection / 証跡収集
3. Rule Diagnosis / 原因診断
4. Rule Draft / 修正案
5. SV Review / SVレビュー
6. PR & Backtest / PR・バックテスト
7. Merge & Delivery / merge・本番反映
8. Announcement / 変更周知

## Status, Label, and Assignee

Status expresses execution state. Labels express classification and auxiliary routing.

Use existing statuses first:

- `Triage`: entry point
- `Todo`: not started
- `In Progress`: SV or agent is working
- `In Review`: SV review / PR review
- `Done`: completed
- `Canceled`: no rule change, canceled, or transferred

Assignee expresses who has the ball:

- SV decision needed: assign to SV
- agent / local worker work needed: assign to bot / agent account
- before a bot account exists: keep the SV as assignee and use markers/comments to express agent ownership

## Comment Threads

Each parent delivery issue should have:

- Event Log thread: bot / n8n / local worker event records
- Approval thread: rule proposal, approval, changes requested, rejection
- PR & Backtest thread: PR URL, backtest result, CR handling

Slack conversation uses Linear's official Slack sync thread.

## Marker Syntax

Use one-line markers readable by humans and parsable by local worker.

```md
[SV_ACTION id=act_YYYYMMDD_NNN type=<action_type> target=<target> status=requested]
[SV_APPROVAL action_id=act_YYYYMMDD_NNN decision=approved target=<target> by=<linear_user_or_sv>]
[SV_APPROVAL action_id=act_YYYYMMDD_NNN decision=changes_requested target=<target> by=<linear_user_or_sv>]
[SV_ACTION_RESULT id=act_YYYYMMDD_NNN status=done run_id=<run_id> pr=<url>]
[SV_EVENT id=evt_YYYYMMDD_NNN type=<event_type> status=done source=<source>]
```

Dangerous operations, such as Slack posting, PR creation, production delivery, and announcements, require an explicit `SV_APPROVAL` marker in Linear.

