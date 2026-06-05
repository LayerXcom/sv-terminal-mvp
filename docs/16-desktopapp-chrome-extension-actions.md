# Desktop App / Chrome Extension SV Actions

## 目的

SV が Linear issue 上で proposal approval / changes requested / reject / close などの明示 action を実行できるようにする。
Chrome extension は SV の操作面、`bpo-operator-desktopapp` は local control plane、Linear は監査可能な SSoT とする。

## 背景

初期案では Chrome extension は Linear comment box に marker text を挿入するだけだった。
しかし MVP 運用では、SV がボタン操作で comment 投稿や status / assignee 更新まで完了できる方が自然である。

一方で、Chrome extension に Linear API key を保存させるのは避ける。
Linear credential と privileged mutation は desktop app main process 側に寄せる。

## Runtime Boundary

```text
SV Chrome extension
  -> 127.0.0.1 desktop app SV action endpoint
  -> bpo-operator-desktopapp main process
  -> Linear API commentCreate / issueUpdate
  -> Linear Trigger
  -> n8n sv_terminal_events
  -> local worker
```

`bpo-operator-desktopapp` の既存 MCP server は browser-like request を拒否する security model を持つ。
Chrome extension は既存 `/mcp` endpoint を直接叩かない。
SV action 用に別の loopback endpoint を用意する。

## Responsibilities

### Chrome Extension

- Linear issue page から issue identifier / issue URL を読む
- proposal target / action type / optional reason を UI で選ばせる
- desktop app の SV action endpoint に POST する
- 結果を小さく表示する
- Linear API key を保持しない

### bpo-operator-desktopapp

- Linear API key を安全に保存する
- Chrome extension と pairing する
- SV action endpoint を `127.0.0.1` のみに bind する
- Action Log thread を探す / 作る
- Linear comment を Action Log thread に投稿する
- 必要に応じて issue status / assignee を更新する
- 実行結果を desktop app の audit log に残す

### Linear

- SV action の SSoT
- Action Log thread
- marker comment
- issue status / assignee / label
- n8n Linear Trigger の event source

### n8n / local worker

- Linear comment event を queue 化する
- local worker は Data Table row を poll する
- worker は実行前に Linear issue の最新 state を取り直す

## Action Log Thread

親 issue ごとに専用 comment thread を 1 つ作る。

```md
## SV Terminal Action Log

[SV_THREAD type=action_log version=1 issue=<issue_identifier>]
```

以降の desktop app / Chrome extension / worker の machine-readable event はこの thread に reply する。
Linear API 上の thread reply が MVP で難しい場合は top-level comment への fallback を許容するが、body には同じ `SV_THREAD` / `SV_EVENT` marker を入れる。

## MVP Actions

### Approve Proposal

Chrome action:

```json
{
  "issueIdentifier": "APCC-1",
  "action": "approve_proposal",
  "target": "proposal:v1",
  "actionId": "act_20260605_001"
}
```

Linear comment:

```md
[SV_APPROVAL action_id=act_20260605_001 decision=approved target=proposal:v1 by=<linear_user>]
```

Side effects:

- assignee を agent / bot に変更する
- status を実行中相当へ進める

### Request Changes

Chrome action:

```json
{
  "issueIdentifier": "APCC-1",
  "action": "request_changes",
  "target": "proposal:v1",
  "actionId": "act_20260605_001",
  "reason": "経理確認の条件が不足"
}
```

Linear comment:

```md
[SV_APPROVAL action_id=act_20260605_001 decision=changes_requested target=proposal:v1 by=<linear_user>]
```

Side effects:

- assignee を agent / bot に変更する
- status は review / in progress のまま維持する

### Reject / No Change / One-off Close

Chrome action:

```json
{
  "issueIdentifier": "APCC-1",
  "action": "close_no_rule_change",
  "actionId": "act_20260605_002",
  "resolution": "no_change",
  "reason": "既存ルールで吸収済み"
}
```

Linear comment:

```md
[SV_ACTION action_id=act_20260605_002 type=close_no_rule_change resolution=no_change by=<linear_user>]
```

Side effects:

- status を Done / Canceled に変更する
- assignee を SV または空にする

## Desktop Endpoint Draft

```http
POST http://127.0.0.1:<port>/sv-terminal/actions
```

Request:

```json
{
  "issueIdentifier": "APCC-1",
  "action": "approve_proposal",
  "target": "proposal:v1",
  "actionId": "act_20260605_001",
  "reason": null
}
```

Response:

```json
{
  "ok": true,
  "issueIdentifier": "APCC-1",
  "actionId": "act_20260605_001",
  "commentId": "<linear_comment_id>",
  "commentUrl": "https://linear.app/...",
  "actionLogThreadId": "<linear_comment_id>"
}
```

## Security

- endpoint は `127.0.0.1` のみに bind する
- Chrome extension と desktop app は pairing token を使う
- Linear API key は Chrome extension に渡さない
- Linear API key は desktop app main process 管理の secure storage に置く
- endpoint は allowed extension id / pairing token / request nonce を検証する
- destructive action は MVP では Linear comment + status update に限定し、production rule mutation は行わない

## Open Questions

- Linear API key の保存は OS keychain、Electron safeStorage、または encrypted userData のどれにするか
- Action Log thread reply の mutation を MVP で実装するか、top-level comment fallback にするか
- status / assignee の名前から id への解決を desktop app が持つか、設定で固定するか
- Chrome extension の actionId 採番を extension 側にするか、desktop app 側にするか
- n8n Linear Trigger が thread reply と top-level comment の両方を同じ shape で扱えるか
