# Linear モデルとマーカー

## チームとプロジェクト

将来像:

- `SV Ops` のようなプライベート Linear チームを作成する。
- テナントごとに 1 つの Linear Project を作成する。
- プロジェクト名の例: `SV Ops: <tenant_name>`。

MVP の起点:

- 既存の `approval_agent` チームを使う。
- 横断的な設計・実装タスクには、既存プロジェクト `SVのエスカレ・ルール変更周知などを複数テナント持てるようにする運用を考える` を使う。

## Issue の粒度

親 issue は 1 つの配信単位。

入口:

- 経理からの問い合わせ
- オペレーターからのエスカレーション
- エージェントからのルール性能アラート

完了条件:

- ルール更新が配信され、周知まで完了した
- またはイベントがワンオフ判断として明示的にマークされた
- または別のプロダクト / 運用 issue へオーナーシップが移管された

## フェーズ（サブ issue）

MVP1 のフェーズ:

1. Intake / 問い合わせ受付
2. Accounting Discussion / 経理相談
3. Decision Capture / 方針確定
4. Rule Draft / ルール下書き
5. SV Review / SVレビュー
6. PR & Backtest / PR・バックテスト
7. Merge & Delivery / merge・本番反映
8. Announcement / 変更周知

MVP2 のフェーズ:

1. Alert Intake / 性能低下検知
2. Evidence Collection / 証跡収集
3. Rule Diagnosis / 原因診断
4. Rule Draft / 修正案
5. SV Review / SVレビュー
6. PR & Backtest / PR・バックテスト
7. Merge & Delivery / merge・本番反映
8. Announcement / 変更周知

## ステータス・ラベル・担当者

ステータスは実行状態を表す。ラベルは分類と補助的なルーティングを表す。

まず既存ステータスを使う:

- `Triage`: 入口
- `Todo`: 未着手
- `In Progress`: SV またはエージェントが作業中
- `In Review`: SV レビュー / PR レビュー
- `Done`: 完了
- `Canceled`: ルール変更なし、キャンセル、または移管

担当者（assignee）はボールの所在を表す:

- SV の判断が必要: SV に assign
- エージェント / ローカル worker の作業が必要: bot / エージェントアカウントに assign
- bot アカウントがまだない場合: SV を assign のままにし、マーカー / コメントでエージェント側のオーナーシップを表現する

## コメントスレッド

各親配信 issue には次を持つ:

- Event Log スレッド: bot / n8n / ローカル worker のイベント記録
- Approval スレッド: ルール提案、承認、変更依頼、却下
- PR & Backtest スレッド: PR URL、バックテスト結果、CR 対応

Slack の会話は Linear 公式の Slack 同期スレッドを使う。

## マーカー構文

人間が読め、ローカル worker がパースできる 1 行マーカーを使う。

```md
[SV_ACTION id=act_YYYYMMDD_NNN type=<action_type> target=<target> status=requested]
[SV_APPROVAL action_id=act_YYYYMMDD_NNN decision=approved target=<target> by=<linear_user_or_sv>]
[SV_APPROVAL action_id=act_YYYYMMDD_NNN decision=changes_requested target=<target> by=<linear_user_or_sv>]
[SV_ACTION_RESULT id=act_YYYYMMDD_NNN status=done run_id=<run_id> pr=<url>]
[SV_EVENT id=evt_YYYYMMDD_NNN type=<event_type> status=done source=<source>]
```

Slack 投稿、PR 作成、本番配信、変更周知など危険な操作には、Linear 上の明示的な `SV_APPROVAL` マーカーが必須。
