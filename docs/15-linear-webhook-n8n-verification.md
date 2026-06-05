# Linear Webhook / n8n Verification

## 目的

Linear の comment marker event が n8n に入り、n8n Data Table queue を経由して local worker が処理できることを確認する。

## n8n docs からの反映

- Webhook node は Test URL と Production URL が分かれる。検証時は Test URL、本番相当では workflow を publish して Production URL を使う。
- Data Tables は軽量から中程度の永続化に向く。queue / audit には最小 metadata だけ入れる。
- n8n API は `X-N8N-API-KEY` を使う。
- workflow export JSON は credential names / IDs を含むことがあるため、repo に置く前に sanitize する。

## Workflow artifact

```text
workflows/n8n/linear-comment-marker-to-event-queue.json
```

Sanitize rules:

- credential IDs / credential names を含めない
- API keys / webhook secret を含めない
- webhook path の suffix は import 後に高エントロピー値へ置き換える
- Data Table ID は import 後に n8n UI で設定する

## Required environment / credentials

n8n workflow:

```text
LINEAR_WEBHOOK_SECRET
```

local worker:

```text
LINEAR_API_KEY
N8N_API_BASE_URL=https://<instance>.app.n8n.cloud/api/v1
N8N_API_KEY=<api key>
N8N_DATATABLE_ID=<sv_terminal_events data table id>
```

API key scopes:

- `dataTable:read`
- `dataTableRow:read`
- `dataTableRow:update`
- `dataTableRow:upsert`

## Data Table

Name:

```text
sv_terminal_events
```

Minimum columns:

- `event_id`
- `created_at`
- `updated_at`
- `source`
- `source_event_id`
- `linear_issue_id`
- `linear_issue_identifier`
- `linear_comment_id`
- `type`
- `status`
- `priority`
- `actor_kind`
- `actor_id`
- `dedupe_key`
- `payload_json`
- `attempts`
- `claimed_by`
- `claimed_at`
- `lease_until`
- `last_error`
- `result_linear_comment_id`
- `processed_at`

## Manual verification

1. Import workflow JSON into n8n.
2. Replace webhook path suffix and Data Table ID.
3. Set `LINEAR_WEBHOOK_SECRET` in n8n environment.
4. Use Webhook Test URL and send a signed Linear comment payload.
5. Confirm one row appears in `sv_terminal_events`.
6. Publish workflow.
7. Register Production URL in Linear webhook settings.
8. Create or update a Linear comment containing:

```md
[SV_APPROVAL action_id=act_demo_001 decision=approved target=proposal:v1 by=hirotea]
```

9. Confirm n8n execution succeeded.
10. Run local worker:

```bash
LINEAR_API_KEY=... \
N8N_API_BASE_URL=https://<instance>.app.n8n.cloud/api/v1 \
N8N_API_KEY=... \
N8N_DATATABLE_ID=... \
python3 -m sv_terminal_worker.cli poll --once --event-source n8n --issue-source linear
```

11. Confirm:

- Data Table row status changes to `processed`
- `.sv-terminal/runs/<issue>/<action_id>/context.json` exists
- Linear Event Log gets PR open preview

## Acceptance criteria

- Non-marker Linear comments are ignored.
- Invalid Linear signature fails workflow execution.
- Approved proposal marker creates exactly one queued row.
- Duplicate marker / same `action_id` upserts instead of duplicating.
- local worker processes the row once.
