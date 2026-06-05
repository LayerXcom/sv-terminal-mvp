# Slack 問い合わせから Linear issue 同期

Linear issue: `BAA-1066`

## 目的

SV またはオペレーターが専用 Slack チャンネルに問い合わせを投稿したら、Linear の delivery issue、MVP1 フェーズ sub issue、Event Log thread を自動作成し、Slack thread を Linear issue に公式 Slack sync で紐づける。

## 決定

MVP では次の経路を採用する。

```text
Slack Events API
  -> n8n webhook
  -> n8n Data Table event
  -> local worker または n8n lightweight action
  -> Linear issue bootstrap
  -> Linear attachmentLinkSlack(syncToCommentThread: true)
```

Linear Asks は MVP の主経路にしない。理由は、次を細かく制御したいため。

- private team / project routing
- tenant project selection
- sub issue creation
- Event Log thread creation
- n8n audit event creation
- bot account attribution

## 専用 Slack チャンネル

問い合わせ開始用の専用チャンネルを作る。

候補:

```text
#sv-approval-inquiries
```

Demo:

```text
#sv-approval-inquiries_test
channel_id: C0B91JF61JL
```

MVP の top-level post は軽量なテキスト形式にする。

```md
tenant: layerx
type: accounting_inquiry
title: 採用会食への移動交通費を通常フォームで承認してよいか

相談内容:
...
```

必須:

- `tenant`
- `type`
- `title`

任意:

- `request_url`
- `rule_id`
- `priority`
- `operator`

必須項目が不足している場合も issue は作る。ただし `Triage` に置き、`needs:intake-fields` 相当の label / marker を付け、Slack thread で不足項目を聞く。

## Slack Event Subscription

public channel:

- `message.channels`

private channel:

- `message.groups`
- Slack app / bot を channel に invite する

問い合わせ開始として扱う条件:

- `event.type = "message"`
- `event.subtype` がない
- `event.bot_id` がない
- `event.thread_ts` がない、または `event.thread_ts == event.ts`
- channel が allowlist に含まれる

無視するもの:

- bot message
- message edit / delete
- thread reply を新規 issue として扱うこと
- hidden subtype
- allowlist 外 channel

thread reply は新規 issue を作らない。issue 紐づけ後は Linear 公式 Slack sync に任せる。

## n8n event

n8n は event row を 1 件作る。

```json
{
  "event_id": "evt_20260604_000001",
  "source": "slack",
  "source_event_id": "Ev...",
  "type": "slack_inquiry_created",
  "status": "queued",
  "priority": 2,
  "tenant_key": "layerx",
  "actor_kind": "sv",
  "actor_id": "U...",
  "dedupe_key": "slack:Cxxxx:1780000000.000001:create_issue",
  "payload_json": "{\"channel\":\"Cxxxx\",\"message_ts\":\"1780000000.000001\",\"thread_ts\":\"1780000000.000001\",\"title\":\"...\"}"
}
```

n8n payload には全文を置かない。channel id、thread ts、短い metadata に留める。

## Tenant Project 解決

解決順:

1. Slack post の `tenant` field
2. Slack channel default mapping
3. fallback project

config 例:

```yaml
tenants:
  layerx:
    project: "SV Ops: LayerX"
    aliases: ["layerx", "lx", "株式会社LayerX"]
  hacobu:
    project: "SV Ops: Hacobu"
    aliases: ["hacobu"]

defaults:
  fallback_project: "SVのエスカレ・ルール変更周知などを複数テナント持てるようにする運用を考える"
```

Demo mapping:

```yaml
tenants:
  test:
    tenant_id: 00000000-0000-488b-81ca-8c90531b1945
    project_url: "https://linear.app/layerx-inc/project/test-tenantid-00000000-0000-488b-81ca-8c90531b1945-9424122f2e0c/overview"
    aliases:
      - test
      - test-tenant
      - 00000000-0000-488b-81ca-8c90531b1945

channels:
  C0B91JF61JL:
    name: sv-approval-inquiries_test
    default_tenant_key: test
    default_tenant_id: 00000000-0000-488b-81ca-8c90531b1945
```

project が存在しない場合:

- fallback project に issue を作る
- `needs:tenant-project` marker を付ける

## Linear bootstrap

親 issue:

- team: MVP は `approval_agent`。将来は `SV Ops`
- project: tenant project
- title: `[<tenant>] <title>`
- status: `Triage` または `In Progress`
- assignee: SV
- labels:
  - `trigger:slack-inquiry`
  - 必要なら `risk:customer-visible`

description template:

```md
## Source

- Slack thread: <slack_thread_url>
- Tenant: <tenant_key>
- Trigger: slack_inquiry

## Current Goal

Resolve this inquiry and decide whether it should become a rule update, one-off decision, or product/ops transfer.

## Completion Condition

- [ ] Decision captured
- [ ] Rule proposal approved or no-rule-change decision recorded
- [ ] PR/backtest completed if needed
- [ ] Production verified if needed
- [ ] Announcement posted if needed

[SV_EVENT id=<event_id> type=linear_issue_bootstrap_requested status=done source=slack]
```

## MVP1 phase sub issues

親 issue の下に作る。

1. `Intake / 問い合わせ受付`
2. `Accounting Discussion / 経理相談`
3. `Decision Capture / 方針確定`
4. `Rule Draft / ルール下書き`
5. `Proposal & Delivery / ルール提案・PR管理`
6. `Announcement / 変更周知`

初期状態:

- `Intake`: bootstrap 成功後 Done
- `Accounting Discussion`: In Progress
- その他: Todo

親 issue の assignee は、経理相談中は SV のままにする。

## Event Log thread

親 issue に comment を作る。

```md
## SV Terminal Event Log

This thread is maintained by sv-terminal-bot.

[SV_EVENT_LOG issue=<LINEAR_IDENTIFIER> version=1]
[SV_EVENT id=<event_id> type=slack_inquiry_created status=done source=slack]
```

以後の machine event はこの comment thread への reply にする。API 上の thread reply が難しい場合は、`SV Terminal Event Log` prefix の top-level comment を許容する。

## Slack thread sync

親 issue 作成後、Linear Slack integration の `attachmentLinkSlack` を使い、`syncToCommentThread: true` で Slack thread を issue に紐づける。

必要値:

- `issueId`
- Slack message URL
- `syncToCommentThread: true`

Slack URL format:

```text
https://<workspace>.slack.com/archives/<channel_id>/p<ts_without_dot>
```

例:

```text
channel_id = C123
ts = 1780000000.000001
url = https://layer-x.slack.com/archives/C123/p1780000000000001
```

Slack sync に失敗した場合:

1. 通常 attachment として Slack URL を付ける
2. Event Log に failure を残す
3. issue は `Triage` のままにする
4. 次の marker を付ける

```md
[SV_ACTION id=act_<date>_sync_slack_thread type=sync_slack_thread target=synced_slack_thread status=requested slack_url=<slack_url>]
```

## Duplicate / replay

dedupe key:

```text
slack:<channel_id>:<thread_ts>:create_issue
```

同じ dedupe key の issue が既にある場合:

- 新規 issue は作らない
- Event Log に duplicate ignored を残す

同じ Slack thread が別 issue に手動リンクされている場合:

- 自動 merge しない
- 可能なら両方の issue に warning を残す
- SV 判断待ちにする

## Thread replies

thread reply は新規 issue を作らない。

期待動作:

- Slack sync 確立後は Linear 公式 sync が両方向に反映する
- sync 確立前の thread reply は audit event として queue してよいが、親 issue が存在しない限り worker は action しない

## Failure modes

### Missing tenant

- fallback project に parent issue を作る
- status は `Triage`
- marker:

```md
[SV_ACTION id=act_<date>_missing_tenant type=request_missing_field target=tenant status=requested]
```

### Linear issue creation failed

- n8n event を `failed`
- 最大3回 retry
- 最終失敗時だけ Slack thread に bot が返信する

```md
Linear issue creation failed. SV Terminal will retry or require manual bootstrap.
```

### Slack sync failed

- 可能なら通常 attachment を作る
- issue はopenのまま
- Event Log に failure を残す

## Minimal test case

1. 専用 Slack channel に投稿:

```md
tenant: layerx
type: accounting_inquiry
title: 採用会食への移動交通費を通常フォームで承認してよいか

相談内容:
採用会食への移動交通費のみであれば通常の経費精算フォームで承認してよいか確認したい。
```

2. n8n row を確認:

- `type = slack_inquiry_created`
- `status = queued`
- correct `dedupe_key`

3. worker を実行。

4. Linear を確認:

- parent issue created
- 8 phase sub issues created
- Event Log comment exists
- Slack thread linked and synced
- parent assigned to SV

5. Slack thread に reply し、Linear synced thread に反映されることを確認。
