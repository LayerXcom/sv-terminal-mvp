# MVP イベント設計

## 目的

MVP では、Linear を SV の主画面にする。SV は Linear を見れば、問い合わせ / 性能低下アラートがどのフェーズにあり、誰がボールを持ち、次に何をすべきか分かる。

実行系は、n8n とエンジニア PC の local worker に逃がす。SV 向け UI は薄くし、Linear のコメント、コメント thread、status、label、assignee、公式 Slack sync、公式 GitHub / PR 連携を最大限使う。

## 構成要素

### Linear

- private team: `SV Ops` など
- tenant ごとに Project を作成
- 親 issue: 1 つの delivery unit
- sub issue: フェーズ
- status: 親 issue / sub issue の進行状態
- label: trigger 種別、resolution 種別、risk、action type
- assignee: 現在のボール保持者
  - SV が判断する状態なら SV
  - agent / local worker が作業する状態なら bot account / agent account
- comment thread:
  - Slack sync thread
  - Event Log thread
  - Proposal / Approval thread
  - PR / Backtest thread

### Slack

- 問い合わせ開始用の専用 channel を作る
- Slack bot event が新規投稿を拾う
- n8n flow が Linear issue を作成し、Slack thread を Linear issue に sync する
- Slack への返信は原則 Linear 公式 sync thread 経由
- bot account による投稿は専用 bot account に寄せる

### n8n

- Slack event / Chrome extension event / Linear webhook を受ける
- Data Table に event を append する
- local worker が n8n API の `/datatables` から queue を poll する
- event payload は最小化する。本文や申請詳細は Linear / Slack 側に置く

### local worker

- n8n event queue を poll する
- Linear API で issue 最新状態を取得する
- Codex / approval_rules / backtest / GitHub PR / production verification を実行する
- 結果を Linear comment に返す
- n8n event を processed / failed に更新する

### Chrome extension / local thin server

- Linear 上で SV が action marker を挿入する補助
- 必要なら n8n webhook に explicit action event を送る
- MVP ではできるだけ薄く保つ

## Linear issue モデル

### 親 issue

粒度:

- 経理相談 1 件
- オペレーターからのエスカレーション 1 件
- Agent からのルール性能低下アラート 1 件

完了条件:

- ルール反映済み
- または、ルール化しない判断が明示済み
- または、別責務に移管済み

必須フィールド:

- title
- tenant Project
- source Slack thread / source alert
- trigger label
- resolution label
- current assignee
- sub issues
- Event Log comment thread

### sub issues as phases

MVP1:

1. `Intake / 問い合わせ受付`
2. `Accounting Discussion / 経理相談`
3. `Decision Capture / 方針確定`
4. `Rule Draft / ルール下書き`
5. `SV Review / SVレビュー`
6. `PR & Backtest / PR・バックテスト`
7. `Merge & Delivery / merge・本番反映`
8. `Announcement / 変更周知`

MVP2:

1. `Alert Intake / 性能低下検知`
2. `Evidence Collection / 証跡収集`
3. `Rule Diagnosis / 原因診断`
4. `Rule Draft / 修正案`
5. `SV Review / SVレビュー`
6. `PR & Backtest / PR・バックテスト`
7. `Merge & Delivery / merge・本番反映`
8. `Announcement / 変更周知`

### status 案

status は実行状態を表す。

- `Triage`
- `Waiting SV`
- `Waiting Accounting`
- `Agent Working`
- `Reviewing`
- `Ready to Merge`
- `Delivery Verify`
- `Announcement`
- `Done`
- `Canceled`

### label 案

trigger:

- `trigger:slack-inquiry`
- `trigger:operator-escalation`
- `trigger:rule-performance-alert`
- `trigger:dummy-alert`

resolution:

- `resolution:rule-change`
- `resolution:one-off-decision`
- `resolution:policy-pending`
- `resolution:transferred-product`
- `resolution:no-change`

action:

- `action:needs-rule-draft`
- `action:needs-slack-reply`
- `action:needs-pr`
- `action:needs-backtest`
- `action:needs-announcement`

risk:

- `risk:customer-visible`
- `risk:prod-delivery`
- `risk:rule-generalization`

## Event Log thread

親 issue 作成時に bot が最初の comment を作る。

```md
## SV Terminal Event Log

This thread is maintained by sv-terminal-bot.

[SV_EVENT_LOG issue=<ISSUE_ID> version=1]
```

この comment の thread に、bot / local worker / n8n が event log を追記する。

例:

```md
[SV_EVENT id=evt_20260604_0001 type=slack_inquiry_received status=done source=slack ts=...]
```

人間判断が必要なものは別 comment thread を作る。

```md
## Approval Needed: Rule proposal v1

...

[SV_ACTION id=act_20260604_0007 type=approve_rule_proposal target=proposal:v1 status=requested]
```

SV が承認したら、Chrome extension が marker を更新するか、SV が返信する。

```md
[SV_APPROVAL action_id=act_20260604_0007 decision=approved by=<SV_USER>]
```

## n8n event queue

Data Table: `sv_terminal_events`

columns:

- `event_id`
- `created_at`
- `source`
- `source_event_id`
- `linear_issue_id`
- `linear_issue_identifier`
- `linear_comment_id`
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

status:

- `queued`
- `claimed`
- `processing`
- `done`
- `failed`
- `ignored`

原則:

- n8n には最小メタデータだけ置く。
- 本文、申請内容、顧客情報は Linear / Slack / GitHub 側に置く。
- local worker は必ず Linear issue 最新状態を再取得してから動く。

## MVP1 workflow

### Story

SV が問い合わせを Slack で開始 -> 経理とやり取り -> 内容が Linear ticket に蓄積 -> 解決 -> ルール下書き作成指示 -> agent が下書き作成 -> PR 作成 -> review / merge -> issue 自動 close -> merge 後にルール変更を宣言。

### Events

#### 1. Slack inquiry created

trigger:

- 専用 Slack channel への新規投稿

actor:

- SV or operator

n8n:

- Slack event を受信
- tenant を channel / message metadata / command text から推定
- Linear issue を bot account で作成
- Project = tenant
- trigger label = `trigger:slack-inquiry`
- sub issues を作成
- Event Log comment を作成
- Slack thread を Linear issue に sync

Linear:

- 親 issue status = `Waiting Accounting` or `Triage`
- assignee = SV
- sub issue `Intake` done
- sub issue `Accounting Discussion` active

human touchpoint:

- SV は Slack thread / Linear synced thread で経理相談を進める

#### 2. Accounting discussion updated

trigger:

- Slack thread reply
- Linear synced thread comment

n8n / Linear:

- 原則 Linear 公式 sync に任せる
- 追加で Linear webhook -> n8n に comment event を積む

local worker:

- 必須ではない
- 必要なら「方針確定っぽい文言」を検出して `Decision Capture` に促す

human touchpoint:

- SV がやり取り

#### 3. Decision captured

trigger:

- SV が Linear に marker を入れる

example:

```md
[SV_ACTION id=act_x type=capture_decision status=requested]
```

n8n:

- Chrome extension event or Linear webhook comment event を queue

local worker:

- Linear issue / synced thread を取得
- 方針メモを bot comment として作る
- `Decision Capture` sub issue を done
- `Rule Draft` sub issue を active
- parent assignee = bot / agent

human touchpoint:

- SV は方針メモを確認。必要ならコメントで修正

#### 4. Rule draft requested

trigger:

- status / marker / label `action:needs-rule-draft`

local worker:

- Codex にルール下書き作成を依頼
- 現行 rules.json / knowledge / Slack sync context / decision memo を読み込ませる
- proposal comment を作成

Linear:

- parent status = `Agent Working`
- assignee = bot / agent
- Proposal thread 作成

human touchpoint:

- なし。agent 作業待ち

#### 5. Rule proposal approval

trigger:

- proposal comment が作成される

Linear:

- parent status = `Waiting SV`
- assignee = SV
- Approval Needed thread に proposal, affected rules, risk, expected PR diff を記載

human touchpoint:

- SV が承認 / CR / 却下

approval event:

```md
[SV_APPROVAL action_id=act_x decision=approved target=proposal:v1]
```

#### 6. PR created and backtest started

trigger:

- proposal approved

local worker:

- approval_rules worktree / branch 作成
- rules.json 編集
- tests / backtest 実行
- GitHub PR 作成
- PR を Linear issue にリンク
- PR & Backtest thread に結果を投稿

Linear:

- parent status = `Reviewing`
- assignee = SV
- `PR & Backtest` sub issue active

human touchpoint:

- SV / reviewer が PR review

#### 7. PR review / merge

trigger:

- GitHub PR activity
- Linear GitHub integration

Linear:

- PR と issue が連動
- CR があれば assignee = bot / agent
- approve / merge なら delivery verify へ

local worker:

- PR feedback を検出して Codex resume
- merge を検出して production verification を queue

human touchpoint:

- SV が PR review / approve / merge

#### 8. Production verified

trigger:

- PR merged

local worker:

- production rule version / deployed SHA / smoke check を確認
- verification comment を投稿
- `Merge & Delivery` sub issue done
- `Announcement` sub issue active
- parent status = `Announcement`
- assignee = SV or bot

human touchpoint:

- SV が本番反映確認を読む

#### 9. Announcement posted

trigger:

- production verified

local worker:

- 変更周知 draft を作成
- Slack sync / 専用 bot account から投稿準備

human touchpoint:

- SV が文面承認

after approval:

- Slack へ投稿
- Linear に投稿 URL を記録
- `Announcement` sub issue done
- parent issue done

## MVP2 workflow

### Story

agent が特定ルールの性能低下を検知 -> Linear ticket 起票 -> 修正案を SV に提案 / PR 作成 -> review / merge -> issue 自動 close -> merge 後にルール変更を宣言。

MVP では性能低下検知は dummy event でよい。

### Events

#### 1. Dummy bad feedback alert

trigger:

- Chrome extension / local worker / n8n manual trigger

n8n event:

```json
{
  "type": "dummy_rule_performance_alert",
  "tenant": "layerx",
  "rule_id": "TRP-xxx",
  "bad_feedback_count": 5,
  "window": "24h"
}
```

local worker:

- Linear issue を作成
- Project = tenant
- label = `trigger:dummy-alert`, `trigger:rule-performance-alert`
- sub issues を作成
- Event Log thread を作成
- Evidence Collection を開始

Linear:

- parent status = `Agent Working`
- assignee = bot / agent

human touchpoint:

- なし

#### 2. Evidence collected

local worker:

- dummy evidence または Langfuse / Slack / backtest evidence を集める
- Evidence thread にまとめる
- 修正候補 rule / affected rule を特定

Linear:

- `Evidence Collection` done
- `Rule Diagnosis` active

human touchpoint:

- 必要に応じて SV が証跡を確認

#### 3. Diagnosis and proposal

local worker:

- 原因仮説を作る
- proposal comment を作る
- 必要なら PR を draft で作成する

Linear:

- parent status = `Waiting SV`
- assignee = SV

human touchpoint:

- SV が「この方向で進める / 修正 / 却下」

#### 4. PR / backtest / merge / announcement

MVP1 と同じ。

## 初回問い合わせ開始の同期

候補は 3 つある。

### A. Linear Slack integration / Asks

利点:

- Linear native
- Slack thread sync が自然
- Slack から issue 作成できる

懸念:

- private team template の制約がある
- bot account / n8n event queue / tenant Project 自動割当の制御が弱い

### B. Slack bot event + n8n + Linear API

推奨。

利点:

- 専用 channel の新規投稿を自動起票できる
- bot account で Linear issue を作成できる
- tenant Project / label / sub issue / Event Log thread を最初から揃えられる
- Linear API の Slack attachment sync を使えば公式 sync thread 化もできる

必要なこと:

- Slack Events API app
- n8n Webhook workflow
- Linear bot token / OAuth app
- `issueCreate`
- `commentCreate`
- sub issue create
- `attachmentLinkSlack(syncToCommentThread: true)`

### C. SV Chrome extension manual create

backup。

利点:

- Slack event 設定が未完成でも動く
- SV が Linear issue 作成を明示できる

懸念:

- 月初大量エスカレでは手動起票が辛い

## 人間のタッチポイント

### SV

- Slack で問い合わせ開始 / 経理相談
- Linear issue を見て現在フェーズとボールを確認
- 方針確定 marker を入れる
- ルール proposal を承認 / CR / 却下
- PR を review / approve / merge
- 本番反映確認を読む
- ルール変更周知 draft を承認

### 経理

- Slack thread で相談に回答
- Linear は直接見なくてもよい

### Agent / local worker

- issue / thread context を読み込む
- decision memo を作る
- rule proposal を作る
- PR / backtest / production verification / announcement draft を作る
- Linear に進捗と結果を戻す

### Engineer

- local worker を起動 / 監視
- n8n queue / Linear bot / Slack bot / GitHub token を管理
- dummy alert を発火できるようにする

## 最小セットアップ

1. Linear private team 作成
2. tenant Project 作成
3. status / label 定義
4. bot account 作成
5. Slack 専用 channel 作成
6. Slack bot event -> n8n flow
7. n8n Data Table `sv_terminal_events`
8. local worker poller
9. Linear issue / sub issue / comment / Slack attachment sync の GraphQL mutation
10. dummy alert trigger

## 未決事項

- parent issue の自動 close 条件を、PR merge だけにするか、Announcement 完了まで待つか。
  - 推奨: Announcement 完了まで待つ。
- Slack への変更周知はどの channel に投稿するか。
- SV approval marker を comment text だけにするか、Chrome extension button で挿入するか。
- PR 作成前に必ず backtest draft を出すか、PR 作成後に backtest を走らせるか。
- n8n Data Table と Google Sheets のどちらを queue とするか。
  - 推奨: n8n Data Table。Google Sheets は backup。

