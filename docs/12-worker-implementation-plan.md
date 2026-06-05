# Worker Implementation Plan

## 目的

`BAA-1068` を実装に移すため、local worker の最小 CLI、実装前チェックリスト、外部 API requirements、初期実装範囲を定義する。

MVP の最初の実装は、Linear / n8n / GitHub を直接叩く前に、ローカル JSON fixture を入力にして次を検証できる状態にする。

- marker を parse できる
- approved proposal を検知できる
- Linear context packet を組み立てられる
- PR agent input を生成できる
- idempotency state を保存できる
- dry-run で write-back preview を出せる

## 実装ステップ

### Step 1: Local-only worker skeleton

実装する。

- `sv-terminal-worker parse-marker`
- `sv-terminal-worker dry-run --issue-file <path>`
- `sv-terminal-worker build-agent-input --context-file <path>`
- marker parser
- context packet schema
- agent input markdown generator
- idempotency state file

外部 API はまだ呼ばない。

### Step 2: Linear read adapter

次に実装する。

- issue read
- comments read
- labels / assignee / status read
- synced Slack thread comment detection
- Proposal & Delivery Thread detection
- linked PR detection

### Step 3: Write-back adapter

次に実装する。

- Event Log comment write
- Proposal & Delivery Thread write
- assignee / status update
- n8n event status update

### Step 4: PR / backtest execution

最後に実装する。

- approval_rules repo path validation
- branch creation
- PR body generation
- GitHub PR creation
- linked PR confirmation
- backtest command execution

## 最小 CLI

```text
python3 -m sv_terminal_worker.cli parse-marker "<marker>"
python3 -m sv_terminal_worker.cli dry-run --issue-file fixtures/issues/approved_rule_change.json
python3 -m sv_terminal_worker.cli build-agent-input --context-file .sv-terminal/runs/BAA-1234/act_001/context.json
```

## Local Fixture Format

```json
{
  "issue": {
    "id": "issue_uuid",
    "identifier": "BAA-1234",
    "title": "[test] 交通費ルール相談",
    "url": "https://linear.app/...",
    "project": "test-tenantid-...",
    "team": "approval_agent",
    "status": "In Review",
    "assignee": "sv",
    "labels": ["trigger:slack-inquiry", "resolution:rule-change"]
  },
  "comments": [
    {
      "id": "comment_1",
      "threadName": "Proposal & Delivery",
      "url": "https://linear.app/...",
      "body": "..."
    }
  ]
}
```

## Linear API Requirements

後続実装で必要な read:

- issue by identifier
- issue comments
- comment thread / parent comment
- labels
- assignee
- status
- attachments / linked Slack sync
- GitHub linked PR attachments

後続実装で必要な write:

- create comment
- reply to comment thread
- update issue status
- update assignee
- add labels

## GitHub Requirements

後続実装で必要:

- approval_rules repo path
- current branch / clean worktree check
- branch creation
- commit
- PR create
- PR URL
- PR review state
- PR merge state

## Backtest Requirements

MVP 初期は dummy backtest を許容する。
ただし result format は本物と同じにする。

```md
## Backtest Result

- Run: backtest:<run_id>
- Command: `<command>`
- Result: pass
- Summary: dummy backtest
- Risk: none

[SV_EVENT id=<event_id> type=backtest_completed status=done target=backtest:<run_id> result=pass]
```

## Done Criteria

- [ ] marker parser の unit test が通る
- [ ] dry-run fixture から context packet を生成できる
- [ ] agent input markdown を生成できる
- [ ] state file を `.sv-terminal/runs/.../state.json` に保存できる
- [ ] README に worker CLI を追記する
- [ ] 外部 API なしで `python3 -m unittest discover -s tests` が通る
