# Current Spec Overview

## 目的

ここまで決めた SV Terminal MVP の仕様全体を、次の実装設計に入れるために再整理する。

SV Terminal MVP の勝ち筋は、月初の大量エスカレーションでも SV が破綻せず、経理相談から rule proposal、PR、backtest、本番反映、周知までを Linear だけで追える状態を作ること。

## Core Concept

承認ルール更新は、ソースコードの delivery と同じものとして扱う。

```text
業務相談
  -> decision memo
  -> rule proposal
  -> SV approval
  -> PR / backtest
  -> merge / production verification
  -> announcement
  -> close
```

Linear は HITL delivery の SSoT。
n8n は event queue / audit buffer。
local worker / agent は重い実行を担う。

## SSoT 方針

独自 storage を増やさず、Linear が公式に持てる情報は Linear 側を正にする。

| 対象 | SSoT | 補足 |
| --- | --- | --- |
| delivery unit | Linear parent issue | 1 issue = 1 相談 / alert から生まれた解決単位 |
| phase | Linear sub issue / status | phase は進捗表示であり、delivery context を分断しない |
| 会話根拠 | Linear official Slack synced comment thread | Slack URL / channel id / thread ts は fallback metadata |
| PR | Linear official GitHub linked PR | PR URL / number は人間向け表示と fallback |
| HITL marker | Linear comment marker | `SV_ACTION`, `SV_APPROVAL`, `SV_ACTION_RESULT`, `SV_EVENT` |
| machine audit | Linear Event Log Thread + n8n Data Table | n8n payload は最小 metadata のみ |
| rule source | approval_rules repo | PR / merge / production verification で delivery |

## Thread Model

Parent issue には 4 種類の thread / linked context を持つ。

```text
Parent Issue
  ├─ Slack Sync Thread
  ├─ Event Log Thread
  ├─ Proposal & Delivery Thread
  └─ Announcement Thread
```

### Slack Sync Thread

経理 / オペレーターとの会話の正本。
Linear official Slack sync を使う。

使う場面:

- 問い合わせ本文
- 追加確認
- 合意内容の根拠
- `capture_decision` の対象

### Event Log Thread

機械イベントの監査ログ。
SV は通常読まない。

使う場面:

- n8n event receipt
- local worker processing result
- retry / failed / skipped / duplicate
- agent session id

### Proposal & Delivery Thread

ルール変更の中心。
proposal approval で閉じず、PR / backtest / CR / merge / 本番反映確認まで同じ thread で管理する。

使う場面:

- decision memo
- rule proposal
- SV approval / CR / reject
- Linear linked PR
- backtest result
- PR review update
- merge / production verification

### Announcement Thread

最後の周知判断。

使う場面:

- 周知文 draft
- 投稿先 Slack channel
- SV approval / CR / skip
- Slack posted URL

## Phase Model

MVP1:

1. Intake / 問い合わせ受付
2. Accounting Discussion / 経理相談
3. Decision Capture / 方針確定
4. Rule Draft / ルール下書き
5. Proposal & Delivery / ルール提案・PR管理
6. Announcement / 変更周知

MVP2:

1. Alert Intake / 性能低下検知
2. Evidence Collection / 証跡収集
3. Rule Diagnosis / 原因診断
4. Rule Draft / 修正案
5. Proposal & Delivery / ルール提案・PR管理
6. Announcement / 変更周知

Phase は SV の進捗理解のために使う。
PR / backtest / merge を別 thread / 別 ticket に分けて、proposal の根拠と切り離してはいけない。

## MVP1 Flow

```text
Slack top-level inquiry
  -> n8n event
  -> Linear parent issue bootstrap
  -> Slack synced comment thread
  -> accounting discussion
  -> capture_decision
  -> decision memo
  -> rule proposal
  -> SV approval / CR / reject
  -> local worker creates PR
  -> Linear linked PR
  -> backtest
  -> PR review / merge
  -> production verification
  -> announcement draft
  -> SV announcement approval / skip
  -> Slack posted
  -> issue close
```

入口:

- Slack channel: `#sv-approval-inquiries_test`
- channel id: `C0B91JF61JL`
- tenant project: `test-tenantid-00000000-0000-488b-81ca-8c90531b1945`

## MVP2 Flow

```text
dummy rule performance alert
  -> n8n event
  -> Linear parent issue bootstrap
  -> evidence collection
  -> diagnosis
  -> rule proposal
  -> MVP1 Proposal & Delivery flow に合流
```

MVP2 は入口だけが違う。
Proposal & Delivery 以降は MVP1 と同じ contract を使う。

## Marker Contract

MVP worker が最小で読む marker:

| Marker | Trigger |
| --- | --- |
| `SV_ACTION type=capture_decision target=synced_slack_thread` | decision memo / proposal 生成開始 |
| `SV_APPROVAL decision=approved target=proposal:*` | PR 作成開始 |
| `SV_APPROVAL decision=changes_requested target=proposal:*` | proposal 再生成 |
| `SV_APPROVAL decision=rejected target=proposal:*` | rule proposal なしで close / wait |
| `SV_ACTION type=close_as_one_off_decision` | one-off close |
| `SV_ACTION type=close_as_no_change` | no-change close |
| `SV_ACTION type=mark_policy_pending` | waiting 状態へ戻す |
| `SV_ACTION type=transfer_to_product_issue` | 移管 close |

結果は `SV_ACTION_RESULT` / `SV_EVENT` で返す。

## Resolution Types

| Resolution | 意味 | PR |
| --- | --- | --- |
| `rule_change` | approval_rules の SSoT を更新する | 作る |
| `one_off_decision` | 今回だけの個別判断として閉じる | 作らない |
| `no_change` | 既存ルール / 運用で足りる | 作らない |
| `policy_pending` | 経理 / 顧客 / 社内方針待ち | 作らない |
| `transferred_product` | product / form / ops 側へ移管 | 作らない |

`rule_change` が主経路。
ただし他 4 つの marker は最初から持つ。

## PR Linking Policy

GitHub PR は Linear official GitHub integration の linked PR を SSoT にする。

PR 作成 agent は PR title または description に parent Linear issue identifier を入れる。
MVP では `References BAA-XXXX` のような non-closing magic word を使う。

理由:

- PR merge 直後に parent issue を close したくない
- close は Announcement posted / skipped 後に worker が行う
- SV は Linear 上の linked PR / Diffs / Reviews で PR 状態を見られる

## Slack Sync Policy

Slack 相談は Linear official Slack synced comment thread を SSoT にする。

親 issue 作成後、`attachmentLinkSlack(syncToCommentThread: true)` で既存 Slack thread を issue に同期する。

Slack URL / channel id / thread ts は fallback と監査用 metadata。
worker は decision memo 生成時、Linear issue に紐づく synced Slack thread を読む。

## Close Conditions

`rule_change` の parent issue close 条件:

- Proposal & Delivery Thread の delivery checklist が完了
- Linear linked PR が merge 済み
- backtest result が記録済み
- production verification が成功
- Announcement Thread が posted または skipped
- Event Log に未解決の failed event がない
- resolution label / marker が付いている

PR merge 直後には close しない。

## Role Split

| Actor | 役割 |
| --- | --- |
| SV | 経理相談、`capture_decision`、proposal approval / CR / reject、announcement approval |
| n8n | Slack / Linear / UI event を受け、Data Table に積む |
| local worker | n8n / Linear を polling し、最新 Linear state を読んで処理を実行する |
| rule proposal agent | decision memo / proposal を作る |
| PR agent | approval_rules を編集し、PR / backtest を実行する |
| Linear bot | issue / comment / marker / status / assignee を更新する |

## 決定済み

- Linear parent issue が delivery unit
- tenant ごとに Linear Project
- phase は sub issue / status / label で表現
- 現在ボールは assignee
- Slack conversation は official synced comment thread
- GitHub PR は official linked PR
- n8n は queue / audit buffer であり、本文の正本を持たない
- local worker は処理時に Linear / Slack sync / GitHub linked PR の最新状態を取り直す
- proposal approval はルール方針の承認
- proposal approval 後は PR open まで進んでよい
- Proposal & Delivery Thread は PR open 成功時に resolve しない

## 次に進むこと

次は `BAA-1068`。

作るべき仕様:

```text
docs/11-local-worker-pr-backtest-flow.md
```

決めること:

- local worker がどの marker を polling / detect するか
- Linear issue context packet の構造
- synced Slack thread / Proposal & Delivery Thread / linked PR の読み方
- PR 作成 agent に渡す prompt / input packet
- branch / PR title / PR description の規約
- backtest 実行結果の write-back format
- PR review / merge / production verify の polling 境界
- 失敗時に assignee / status / Event Log をどう戻すか
