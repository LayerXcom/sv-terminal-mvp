# n8n イベントキュープロトコル

## 方針

n8n Data Table `sv_terminal_events` を次の用途で使う:

- イベント受信箱（inbox）
- 監査ログ
- リトライキュー

エンジニアのローカル worker は n8n と Linear をポーリングする。インバウンド用のポートは公開しない。

## n8n API

前提:

- Data Table は Data Table ノード、DataTable API エンドポイント、または UI で管理する。
- local worker の API base: `https://<instance>.app.n8n.cloud/api/v1`
- local worker の row API: `/data-tables/{dataTableId}/rows`
- API 認証ヘッダ: `X-N8N-API-KEY`。
- custom `/sv-terminal/events` endpoint は使わない。

最低限のスコープ:

- `dataTable:read`
- `dataTableRow:read`
- `dataTableRow:update`
- `dataTableRow:upsert`

## テーブル

```text
sv_terminal_events
```

## カラム

必須:

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

任意:

- `run_id`
- `parent_event_id`
- `correlation_id`
- `requires_approval`
- `approval_action_id`

## ステータスライフサイクル

```text
queued -> claimed -> processing -> processed
                         |
                         -> failed -> queued
                         |
                         -> ignored
```

## 重複排除キー（dedupe_key）

例:

- Slack トップレベル問い合わせ: `slack:<channel_id>:<thread_ts>:create_issue`
- Slack スレッド返信: `slack:<channel_id>:<thread_ts>:<message_ts>`
- Linear マーカー: `linear:<issue_identifier>:<action_id>`
- ダミーアラート: `dummy:<tenant_key>:<rule_id>:<window_start>:<window_end>`

ローカル worker は処理前に、同一 `dedupe_key` で `processed` / `processing` / 有効な `claimed` の行がないか確認する。

## リースとリトライ

クレーム時:

- `status = claimed`
- `claimed_by = <worker_id>`
- `claimed_at = now`
- `lease_until = now + 120 sec`
- `attempts = attempts + 1`

リトライ条件:

- `status = failed`
- `attempts < 3`

バックオフ:

- 1 回目: 即時
- 2 回目: 60 秒
- 3 回目: 300 秒

3 回失敗後は `failed` のままとし、Linear Event Log に手動対応が必要なコメントを書く。

## ペイロードの境界

許可:

- Slack の channel / thread / message id
- Linear の issue id / identifier
- action type
- marker id
- target proposal id
- rule id
- tenant key
- PR URL
- run id
- 短いメタデータ

禁止:

- 申請明細の全文
- 経理会話の全文
- 顧客の機密情報
- トークン / API キー / 認証情報
- 添付ファイルの中身

コンテンツの正本は Linear / Slack / GitHub。worker は実行前に最新状態を取得する。

## Worker のポーリングプロトコル

ポーリング間隔:

- デフォルト 5 秒
- キューが空のときは最大 30 秒までバックオフ
- 処理対象を見つけたら 5 秒にリセット

クエリ:

- `status in (queued, failed)`
- `attempts < 3`
- priority 昇順
- created_at 昇順
- limit 10

処理手順:

1. n8n から候補イベントを取得する。
2. `dedupe_key` と現在の `status` を確認する。
3. イベントをクレームする。
4. 最新の Linear issue、コメント、リンク、サブ issue を取得する。
5. マーカー駆動の場合、マーカーが Linear にまだ存在するか検証する。
6. 危険操作の場合、`SV_APPROVAL` の存在を検証する。
7. `status = processing` にする。
8. アクションを実行する。
9. 結果を Linear Event Log スレッドに投稿する。
10. n8n 行を `processed` にする。

失敗時:

1. 短い `last_error` を書く。
2. `status = failed` にする。
3. 失敗イベントを Linear Event Log スレッドに投稿する。
4. リトライ可能ならリトライ処理に任せる。

## Event Log の記録例

```md
[SV_EVENT id=evt_20260604_000001 type=<event_type> status=done source=n8n worker=<worker_id>]
[SV_EVENT id=evt_20260604_000001 type=<event_type> status=failed source=local_worker attempts=2 error="<short_error>"]
[SV_ACTION_RESULT id=act_20260604_000001 status=done run_id=<run_id> pr=<url>]
```

## MVP のイベント種別

MVP1:

- `linear_marker_detected`
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
