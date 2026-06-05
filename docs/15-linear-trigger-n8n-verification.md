# Linear Trigger / n8n Verification

## 目的

Linear の comment marker event が n8n Linear Trigger node に入り、n8n Data Table queue を経由して local worker が処理できることを確認する。

## n8n docs からの反映

- Linear Trigger node は Linear の `Issue Comment` event をサポートする。今回の入口は Linear Trigger を本線にする。
- Webhook node + `Linear-Signature` 検証は fallback として扱う。
- Data Tables は軽量から中程度の永続化に向く。queue / audit には最小 metadata だけ入れる。
- n8n API は `X-N8N-API-KEY` を使う。
- workflow export JSON は credential names / IDs を含むことがあるため、repo に置く前に sanitize する。

## Workflow artifact

```text
workflows/n8n/linear-comment-marker-to-event-queue.json
```

Sanitize rules:

- credential IDs / credential names を含めない
- API keys を含めない
- Linear Trigger credential は import 後に n8n UI で設定する
- Data Table ID は import 後に n8n UI で設定する

## Required environment / credentials

n8n workflow:

```text
Linear credential with access to the demo workspace
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
2. Set Linear credential on `Linear Trigger - Issue Comment`.
3. Confirm trigger event is `Issue Comment`. If the imported event parameter is not recognized by the n8n UI, reselect `Issue Comment` manually.
4. Replace Data Table ID on `Upsert sv_terminal_events row`.
5. Execute the workflow in test mode or activate it.
6. Create or update a Linear comment containing:

```md
[SV_APPROVAL action_id=act_demo_001 decision=approved target=proposal:v1 by=hirotea]
```

7. Confirm n8n execution succeeded.
8. Confirm one row appears in `sv_terminal_events`.
9. Run local worker:

```bash
LINEAR_API_KEY=... \
N8N_API_BASE_URL=https://<instance>.app.n8n.cloud/api/v1 \
N8N_API_KEY=... \
N8N_DATATABLE_ID=... \
python3 -m sv_terminal_worker.cli poll --once --event-source n8n --issue-source linear
```

10. Confirm:

- Data Table row status changes to `processed`
- `.sv-terminal/runs/<issue>/<action_id>/context.json` exists
- Linear Event Log gets PR open preview

## Acceptance criteria

- Non-marker Linear comments are ignored.
- Approved proposal marker creates exactly one queued row.
- Duplicate marker / same `action_id` upserts instead of duplicating.
- local worker processes the row once.

## Fallback

Linear Trigger node が workspace / credential / event type の都合で使えない場合は、Webhook node で Linear webhook を受け、`Linear-Signature` を Code node で検証する構成に戻す。
