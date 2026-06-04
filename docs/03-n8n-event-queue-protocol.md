# n8n Event Queue Protocol

## Decision

Use n8n Data Table `sv_terminal_events` as:

- event inbox
- audit log
- retry queue

The engineer local worker polls n8n and Linear. It does not expose inbound ports.

## n8n API

Assumptions:

- Data Tables are managed by Data Table node, DataTable API endpoint, or UI.
- API endpoint family: `/datatables`.
- API auth header: `X-N8N-API-KEY`.

Minimum scopes:

- `dataTable:read`
- `dataTable:list`
- `dataTableRow:create`
- `dataTableRow:read`
- `dataTableRow:update`
- `dataTableRow:upsert`

## Table

```text
sv_terminal_events
```

## Columns

Required:

- `event_id`
- `created_at`
- `updated_at`
- `source`
- `source_event_id`
- `linear_issue_id`
- `linear_issue_identifier`
- `linear_comment_id`
- `tenant_key`
- `tenant_project_id`
- `type`
- `status`
- `priority`
- `actor_kind`
- `actor_id`
- `dedupe_key`
- `payload_json`
- `claimed_by`
- `claimed_at`
- `lease_until`
- `attempts`
- `last_error`
- `result_linear_comment_id`
- `processed_at`

Optional:

- `run_id`
- `parent_event_id`
- `correlation_id`
- `requires_approval`
- `approval_action_id`

## Status Lifecycle

```text
queued -> claimed -> processing -> done
                         |
                         -> failed -> queued
                         |
                         -> ignored
```

## Dedupe Keys

Examples:

- Slack top-level inquiry: `slack:<channel_id>:<thread_ts>:create_issue`
- Slack thread reply: `slack:<channel_id>:<thread_ts>:<message_ts>`
- Linear marker: `linear:<issue_identifier>:<marker_id>`
- Dummy alert: `dummy:<tenant_key>:<rule_id>:<window_start>:<window_end>`

The local worker must check for existing `done`, `processing`, or valid `claimed` rows with the same `dedupe_key` before processing.

## Lease and Retry

When claiming:

- `status = claimed`
- `claimed_by = <worker_id>`
- `claimed_at = now`
- `lease_until = now + 120 sec`
- `attempts = attempts + 1`

Retry condition:

- `status = failed`
- `attempts < 3`

Backoff:

- attempt 1: immediate
- attempt 2: 60 sec
- attempt 3: 300 sec

After 3 failures, keep `failed` and write a manual-attention comment to Linear Event Log.

## Payload Boundary

Allowed:

- Slack channel / thread / message ids
- Linear issue id / identifier
- action type
- marker id
- target proposal id
- rule id
- tenant key
- PR URL
- run id
- short metadata

Forbidden:

- full request details
- full accounting conversation text
- customer secrets
- tokens / API keys / credentials
- attachment contents

The source of truth for content stays in Linear / Slack / GitHub. The worker fetches current state before acting.

## Worker Polling Protocol

Poll interval:

- default 5 sec
- back off to max 30 sec when empty
- reset to 5 sec after finding queued work

Query:

- `status in (queued, failed)`
- `attempts < 3`
- priority ascending
- created_at ascending
- limit 10

Processing:

1. Fetch candidate events from n8n.
2. Check `dedupe_key` and current `status`.
3. Claim the event.
4. Fetch latest Linear issue, comments, links, and sub-issues.
5. If marker-driven, verify that the marker still exists in Linear.
6. If dangerous, verify that `SV_APPROVAL` exists.
7. Set `status = processing`.
8. Run action.
9. Post result to Linear Event Log thread.
10. Mark n8n row `done`.

Failure:

1. Write short `last_error`.
2. Set `status = failed`.
3. Post failure event to Linear Event Log thread.
4. Let retry pick it up when retryable.

## Event Log Records

```md
[SV_EVENT id=evt_20260604_000001 type=<event_type> status=done source=n8n worker=<worker_id>]
[SV_EVENT id=evt_20260604_000001 type=<event_type> status=failed source=local_worker attempts=2 error="<short_error>"]
[SV_ACTION_RESULT id=act_20260604_000001 status=done run_id=<run_id> pr=<url>]
```

## MVP Event Types

MVP1:

- `slack_inquiry_created`
- `linear_issue_bootstrap_requested`
- `decision_capture_requested`
- `rule_draft_requested`
- `rule_proposal_approved`
- `rule_proposal_changes_requested`
- `pr_create_requested`
- `backtest_requested`
- `pr_merged`
- `production_verify_requested`
- `announcement_draft_requested`
- `announcement_approved`

MVP2:

- `dummy_rule_performance_alert`
- `evidence_collection_requested`
- `rule_diagnosis_requested`
- `rule_proposal_requested`

