# Local Worker PR / Backtest Flow

## 目的

`BAA-1068` の仕様として、local worker / PR agent が `Proposal & Delivery Contract` を読み、approval_rules の PR 作成と backtest を実行し、結果を Linear に戻す流れを定義する。

ここではまだ実装コードには入らない。
worker が読む Linear context、agent に渡す input、GitHub PR linking、backtest result、失敗時の戻し方を決める。

## Scope

対象:

- `SV_APPROVAL decision=approved target=proposal:*` の検知
- Linear issue context packet の作成
- approval_rules repo の branch / PR 作成
- Linear official linked PR の確認
- backtest 実行
- Proposal & Delivery Thread への write-back
- PR review / merge / production verify への橋渡し

対象外:

- production verification の詳細
- announcement draft / post
- dummy performance alert
- Chrome extension / UI

## Worker Loop

local worker は inbound port を開けず、n8n API と Linear API を polling する。

```text
poll n8n queued events
  -> event metadata から Linear issue id を得る
  -> Linear issue の最新状態を取得
  -> marker を parse
  -> idempotency check
  -> action 実行
  -> Event Log / Proposal & Delivery Thread に write-back
  -> n8n event status update
```

ただし本文の正本は n8n ではなく Linear。
n8n payload は trigger metadata として扱う。

## Trigger

PR 作成の primary trigger:

```md
[SV_APPROVAL action_id=<action_id> decision=approved target=proposal:<version> by=<sv>]
```

検知条件:

- target が `proposal:*`
- decision が `approved`
- 同じ `action_id` の `pr_opened` / `pr_open_failed` result が未処理
- parent issue resolution が `rule_change`
- parent issue / Proposal & Delivery Thread に proposal が存在する

検知後、Event Log に残す:

```md
[SV_EVENT id=<event_id> type=proposal_approval_detected status=done source=linear action_id=<action_id> target=proposal:<version>]
[SV_EVENT id=<event_id> type=pr_create_requested status=done source=worker target=proposal:<version>]
```

## Linear Context Packet

worker は PR agent に渡す前に、Linear から最新 context packet を組み立てる。

```json
{
  "issue": {
    "id": "<linear_issue_uuid>",
    "identifier": "BAA-1234",
    "title": "...",
    "url": "https://linear.app/...",
    "project": "...",
    "team": "approval_agent",
    "status": "In Review",
    "assignee": "sv-or-bot",
    "labels": ["trigger:slack-inquiry", "resolution:rule-change"]
  },
  "sources": {
    "synced_slack_thread": {
      "linear_comment_thread_id": "<comment_thread_id>",
      "slack_url": "<fallback_url>",
      "available": true
    },
    "proposal_delivery_thread": {
      "comment_thread_id": "<comment_thread_id>",
      "proposal_target": "proposal:v1",
      "approval_action_id": "<action_id>"
    }
  },
  "decision_memo": {
    "target": "decision_memo:v1",
    "body": "..."
  },
  "proposal": {
    "target": "proposal:v1",
    "recommended_resolution": "rule_change",
    "affected_rules": [],
    "expected_diff": [],
    "risks": []
  },
  "approval": {
    "action_id": "<action_id>",
    "decision": "approved",
    "by": "<sv>",
    "comment_url": "https://linear.app/..."
  }
}
```

MVP では packet を local file として保存してよい。
例:

```text
.sv-terminal/runs/<linear_identifier>/<action_id>/context.json
```

## PR Agent Input

PR agent には、必要な context だけを渡す。

必須:

- Linear issue identifier / URL
- synced Slack thread summary or excerpt
- decision memo
- rule proposal
- approval marker
- target tenant / approval_rules path
- expected diff
- backtest expectation

禁止:

- n8n payload を business source として扱う
- Slack raw thread だけを読んで Linear context を無視する
- proposal にない追加 scope を勝手に広げる

## Worktree / Branch Policy

MVP では approval_rules repo に専用 branch を作る。

branch name:

```text
codex/<linear_identifier>-<short-slug>
```

例:

```text
codex/BAA-1234-update-transportation-rule
```

PR title:

```text
<linear_identifier> <summary>
```

PR description:

```md
References BAA-1234

## Source

- Linear issue: <linear_issue_url>
- Source proposal: proposal:v1
- Source decision memo: decision_memo:v1

## Summary

<what changed>

## Backtest

<command and result, or pending>
```

`References` を使う。
closing magic word は使わない。
PR merge 直後に parent issue を close しないため。

## PR Open Write-back

PR 作成成功後、worker は Linear official linked PR が issue に表示されることを確認する。

Proposal & Delivery Thread:

```md
## PR Opened

- PR: <github_pr_url>
- Branch: <branch_name>
- Linear linked PR: confirmed / pending

[SV_ACTION_RESULT id=<action_id> status=done result=pr_opened target=linked_pr pr=<github_pr_url> branch=<branch_name> linear_issue=<issue_identifier>]
```

Event Log:

```md
[SV_EVENT id=<event_id> type=linear_linked_pr_confirmed status=done target=linked_pr pr=<github_pr_url>]
```

linked PR がすぐ確認できない場合:

- Proposal & Delivery Thread には `linked PR: pending` と書く
- Event Log に retry予定を書く
- 一定回数後も確認できなければ assignee を SV に戻す

```md
[SV_EVENT id=<event_id> type=linear_linked_pr_confirm_failed status=failed target=linked_pr pr=<github_pr_url> reason=<reason>]
```

## Backtest Execution

PR open 後、worker は backtest を実行する。

backtest command は proposal の `Backtest expectation` と approval_rules repo の標準手順から決める。

MVP の result format:

```md
## Backtest Result

- Run: backtest:<run_id>
- Command: `<command>`
- Result: pass / fail
- Summary: <summary>
- Risk: <risk_or_none>
- Artifacts: <path_or_url>

[SV_EVENT id=<event_id> type=backtest_completed status=done target=backtest:<run_id> result=pass]
```

fail:

```md
[SV_EVENT id=<event_id> type=backtest_completed status=failed target=backtest:<run_id> result=fail reason=<reason>]
```

fail 時:

- 自動 merge しない
- parent issue / Proposal & Delivery sub issue を `In Review` にする
- assignee を SV に戻す
- Proposal & Delivery Thread に「選択肢」を出す

選択肢:

```md
[SV_APPROVAL action_id=<action_id> decision=changes_requested target=proposal:v1 by=<sv>]
[SV_ACTION id=<action_id> type=rerun_backtest target=backtest:<run_id> status=requested]
[SV_ACTION id=<action_id> type=abort_pr target=linked_pr status=requested]
```

## PR Review Updates

PR review の状態は Linear official linked PR を優先して読む。
足りない場合は GitHub polling で補完する。

worker が Proposal & Delivery Thread に戻す event:

```md
[SV_EVENT id=<event_id> type=pr_review_update status=done target=linked_pr state=changes_requested pr=<github_pr_url>]
[SV_EVENT id=<event_id> type=pr_review_update status=done target=linked_pr state=approved pr=<github_pr_url>]
```

GitHub CR 対応は PR agent が実施するが、SV が迷わないよう結果は Proposal & Delivery Thread に戻す。

## Merge Boundary

MVP では merge 自体を自動化しない。
reviewer / SV / engineer が GitHub または Linear Reviews で merge する。

worker は merge を検知して次へ進む。

```md
[SV_EVENT id=<event_id> type=pr_merged status=done target=linked_pr pr=<github_pr_url> merge_sha=<sha>]
```

merge 後:

- parent issue は close しない
- Production verification へ進める
- assignee は worker / bot

## Failure Handling

共通原則:

- failed event は Event Log に必ず残す
- SV が判断すべき失敗では assignee を SV に戻す
- worker retry で解決できる失敗では assignee は worker / bot のまま
- 同じ `action_id` を二重実行しない

| Failure | assignee | status | write-back |
| --- | --- | --- | --- |
| Linear context missing | SV | Triage / In Review | missing context |
| synced Slack thread missing | SV | Triage | slack sync missing |
| proposal parse failed | SV | In Review | proposal parse failed |
| PR open failed | SV | In Review | pr_open_failed |
| linked PR confirm failed | SV | In Review | linked_pr confirm failed |
| backtest failed | SV | In Review | backtest result + choices |
| GitHub transient error | worker / bot | In Progress | retrying |

## Idempotency

idempotency key:

```text
<linear_issue_identifier>:<action_id>:<action_type>
```

worker は次を記録する:

```text
.sv-terminal/runs/<linear_identifier>/<action_id>/state.json
```

state:

```json
{
  "action_id": "act_...",
  "linear_identifier": "BAA-1234",
  "status": "pr_opened",
  "branch": "codex/BAA-1234-update-rule",
  "pr_url": "https://github.com/...",
  "backtest_run_id": "bt_...",
  "updated_at": "2026-06-05T00:00:00Z"
}
```

## BAA-1068 Deliverables

- [ ] Linear context packet schema
- [ ] PR agent prompt/input template
- [ ] branch / PR title / PR description convention
- [ ] PR open write-back format
- [ ] linked PR confirm behavior
- [ ] backtest result format
- [ ] failure handling matrix
- [ ] idempotency state file format
- [ ] BAA-1069 への handoff event

## Handoff To BAA-1069

BAA-1068 の完了点:

```md
[SV_EVENT id=<event_id> type=pr_merged status=done target=linked_pr pr=<github_pr_url> merge_sha=<sha>]
```

この event を起点に、BAA-1069 で production verification / announcement / close を扱う。
