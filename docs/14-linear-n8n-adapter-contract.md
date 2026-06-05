# Linear / n8n Adapter Contract

## 目的

Step 1〜3 で実装した Linear / n8n adapter の契約を記録する。
実API接続時も application usecase は変更しない。

## Linear Adapter

Port: `IssueRepository`

Read:

- `get_issue(identifier) -> IssueContext`
- issue metadata
- labels
- assignee
- status
- comments
- attachments
- GitHub linked PR attachments

Write:

- `write_event_log(issue_id, body)`
- `write_proposal_delivery(issue_id, body)`
- `update_status(issue_id, status)`
- `update_assignee(issue_id, assignee)`

Environment:

```text
LINEAR_API_KEY
LINEAR_TEAM_KEY=BAA
SV_TERMINAL_LINEAR_WORKSPACE=layerx-inc
```

MVP 注意:

- `update_status` / `update_assignee` は Linear の id を必要とする。名前から id への解決は後続で追加する。
- linked PR は attachment URL に `github.com/.../pull/...` が含まれるものとして検出する。
- synced Slack thread は comment body / attachment から推測する。公式 sync の正確な schema が見えたら adapter だけ更新する。

## Linear GraphQL Operations

Current read query:

- `IssueForWorker($identifier: String!)`

Current mutations:

- `commentCreate`
- `issueUpdate`

実接続前に確認すること:

- `issue(id: $identifier)` が issue identifier を受けられるか
- comment thread reply が必要な場合の mutation
- attachment / Slack sync / GitHub linked PR の実レスポンス形
- status / assignee 更新に必要な id 解決

## n8n Adapter

Port: `EventQueue`

Read:

- `poll_queued(limit) -> list[QueuedEvent]`

Write:

- `mark_processing(event_id)`
- `mark_processed(event_id, result)`
- `mark_failed(event_id, reason)`

Environment:

```text
N8N_BASE_URL
N8N_API_KEY
N8N_EVENT_PATH=/sv-terminal/events
```

Expected event shape:

```json
{
  "event_id": "evt_...",
  "type": "linear_marker_detected",
  "status": "queued",
  "linear_issue_identifier": "BAA-1234",
  "source": "linear",
  "dedupe_key": "linear:BAA-1234:act_...",
  "payload_json": {
    "action_id": "act_..."
  }
}
```

n8n payload は business source ではない。
worker は必ず Linear の最新 state を取り直す。

## Local Fixture Mode

Fixture mode は default。

```bash
python3 -m sv_terminal_worker.cli poll --once --event-source fixture --issue-source fixture
python3 -m sv_terminal_worker.cli run-action --issue BAA-1234 --action-id act_20260605_001 --issue-source fixture
```

Fixture files:

- `fixtures/issues/approved_rule_change.json`
- `fixtures/events/approved_proposal_event.json`

## Current Limitation

Step 1〜3 は PR / backtest を実行しない。
代わりに context packet、state file、PR open preview write-back を生成する。
