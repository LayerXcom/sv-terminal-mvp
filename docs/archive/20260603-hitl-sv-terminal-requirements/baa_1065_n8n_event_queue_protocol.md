# BAA-1065 n8n event queue schema / polling protocol

## 決定

n8n Data Table を `sv_terminal_events` として使う。n8n は外部からイベントを受ける箱、監査ログ、retry queue に限定する。実行本体はエンジニア local PC の worker が n8n API と Linear API を poll して行う。

エンジニア PC には inbound port を開けない。

## n8n API 前提

- n8n Data Tables は n8n内の軽量な構造化ストレージとして使える。
- Data Tables は Data Table node、DataTable API endpoint、UIから操作できる。
- API endpoint は `/datatables`。
- API認証は `X-N8N-API-KEY` header。
- 必要scopeは最低限:
  - `dataTable:read`
  - `dataTable:list`
  - `dataTableRow:create`
  - `dataTableRow:read`
  - `dataTableRow:update`
  - `dataTableRow:upsert`

## Data Table

table name:

```text
sv_terminal_events
```

## Columns

必須:

- `event_id`: string。例 `evt_20260604_000001`
- `created_at`: datetime ISO string
- `updated_at`: datetime ISO string
- `source`: string。`slack`, `linear`, `chrome_extension`, `local_worker`, `manual`, `dummy`
- `source_event_id`: string。Slack event id / Linear webhook id / Chrome extension event id
- `linear_issue_id`: string。Linear UUID。未作成なら空
- `linear_issue_identifier`: string。例 `BAA-1030`
- `linear_comment_id`: string。関連comment id
- `tenant_key`: string。例 `layerx`
- `tenant_project_id`: string。Linear Project id
- `type`: string。例 `slack_inquiry_created`, `capture_decision_requested`
- `status`: string。後述
- `priority`: integer。1 urgent, 2 high, 3 normal, 4 low
- `actor_kind`: string。`sv`, `agent`, `bot`, `system`
- `actor_id`: string。Linear user id / Slack user id / bot id
- `dedupe_key`: string
- `payload_json`: string。JSON文字列
- `claimed_by`: string。worker id
- `claimed_at`: datetime ISO string
- `lease_until`: datetime ISO string
- `attempts`: integer
- `last_error`: string
- `result_linear_comment_id`: string
- `processed_at`: datetime ISO string

任意:

- `run_id`: string。local worker / Codex run id
- `parent_event_id`: string
- `correlation_id`: string。1つのdelivery unitを束ねる
- `requires_approval`: boolean
- `approval_action_id`: string

## Status lifecycle

```text
queued -> claimed -> processing -> done
                         |
                         -> failed -> queued
                         |
                         -> ignored
```

意味:

- `queued`: 未処理。local worker がpoll対象にする
- `claimed`: worker がlease取得済み
- `processing`: worker が実行中
- `done`: 成功
- `failed`: 失敗。retry可能
- `ignored`: 処理不要、またはdedupe済み

## dedupe

`dedupe_key` は必須。

生成ルール:

- Slack top-level inquiry: `slack:<channel_id>:<thread_ts>:create_issue`
- Slack thread reply: `slack:<channel_id>:<thread_ts>:<message_ts>`
- Linear marker: `linear:<issue_identifier>:<marker_id>`
- Dummy alert: `dummy:<tenant_key>:<rule_id>:<window_start>:<window_end>`

local worker は処理前に同じ `dedupe_key` の `done` / `processing` / valid `claimed` がないか確認する。

## lease

local worker は `queued` または `failed` のうち retry可能なeventを拾う。

claim時:

- `status = claimed`
- `claimed_by = <worker_id>`
- `claimed_at = now`
- `lease_until = now + 120 sec`
- `attempts = attempts + 1`

lease切れ:

- `claimed` または `processing` で `lease_until < now` のeventは、別workerが再claimしてよい。
- MVPではworkerは1台想定だが、仕様としてleaseを入れておく。

## retry

retry条件:

- `status = failed`
- `attempts < 3`

retry backoff:

- attempt 1: 即時
- attempt 2: 60 sec
- attempt 3: 300 sec

3回失敗したら `failed` のままにして、Linear Event Log threadに手動対応コメントを残す。

## payload_json に置いてよいもの

置いてよい:

- Slack channel id / thread ts / message ts
- Linear issue id / identifier
- action type
- marker id
- target proposal id
- rule id
- tenant key
- PR URL
- run id
- summary程度の短いmetadata

置かない:

- 申請詳細全文
- 経理相談の全文
- 顧客秘密情報
- token / API key / secret
- 添付ファイル中身

本文や会話のsource of truthは Linear / Slack / GitHub に置き、workerは処理時に必要な最新情報をAPIで取り直す。

## local worker polling protocol

poll interval:

- default 5 sec
- 連続空振り時は最大30 secまでbackoff
- queuedを見つけたら即5 secに戻す

poll query:

- `status in (queued, failed)`
- `attempts < 3`
- priority asc
- created_at asc
- limit 10

処理手順:

1. n8n APIで候補eventを取得
2. `dedupe_key` と `status` を確認
3. eventをclaimする
4. Linear issue id / identifier があれば、Linear APIで最新issue、comments、links、sub issuesを取得
5. markerが関わるeventなら、Linear上に該当markerがまだ存在することを確認
6. 危険操作なら、該当 `SV_APPROVAL` markerが存在することを確認
7. `status = processing` に更新
8. action実行
9. Linear Event Log threadに結果を投稿
10. n8n rowを `done` に更新

失敗時:

1. `last_error` に短いエラーを書く
2. `status = failed`
3. Linear Event Log threadに失敗eventを書く
4. retry可能なら次回pollで拾う

## Linear最新状態の再取得タイミング

必ず再取得する:

- claim直後
- Slack投稿 / PR作成 / merge / production verification / announcement投稿など危険操作の直前
- CR retry / Codex resume の直前
- done書き込みの直前

理由:

- n8n payloadは古い可能性がある
- SVがLinear上でmarkerを取り消している可能性がある
- issueがCanceled / Doneに変わっている可能性がある

## Event Log thread record

成功:

```md
[SV_EVENT id=evt_20260604_000001 type=<event_type> status=done source=n8n worker=<worker_id>]
```

失敗:

```md
[SV_EVENT id=evt_20260604_000001 type=<event_type> status=failed source=local_worker attempts=2 error=\"<short_error>\"]
```

危険操作の実行:

```md
[SV_ACTION_RESULT id=act_20260604_000001 status=done run_id=<run_id> pr=<url>]
```

## Worker id

形式:

```text
sv-worker-<hostname>-<short_random>
```

例:

```text
sv-worker-hirotea-mbp-a1b2
```

## MVP対象event types

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

## Security

- n8n API keyはlocal workerのenvに置く。Linear/Slack/GitHub tokenも同様。
- n8n Data Tableにsecretを置かない。
- n8n webhookは署名 / shared secret / allowlisted sourceを使う。
- Chrome extensionからn8nへ送るeventにもshared secretまたは短命tokenを付ける。
- local workerはLinear上の明示approval markerなしに危険操作を行わない。

