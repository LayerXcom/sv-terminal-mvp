# Linear 機能境界と追加開発の整理

## 前提

MVP は「なんでもあり」。将来的にはプロダクト機能に寄せるが、現時点では Linear、Slack、GitHub、Codex、local app、local server、bpo-desktop-app、browser automation を併用してよい。

## 結論

Linear は、SV Terminal の「状態・証跡・人間判断・通知」の中心として十分使える。

ただし Linear は、LayerX 固有の実行系、つまり approval_rules の worktree 操作、backtest、production 反映、bpo-desktop-app / 承認画面への返信、Slack 上の特殊な thread 運用までは直接持たない。ここは localops-codex-bridge を拡張した local orchestrator が必要。

したがって MVP の構造は次がよい。

- Linear: SSoT / issue / phase / comment thread / approval point / PR review入口
- Slack Asks or Slack sync: 起票と経理/オペレーター会話の同期
- GitHub integration / Linear Diffs: PR と CR の可視化、必要なら Linear 上で review
- Local orchestrator: Linear webhook を受け、Codex / approval_rules / backtest / Slack / bpo-desktop-app を実行
- Local mini app: Linear だけでは重い操作、承認前 preview、draft reply 確認、実行ログ確認

## Linear でできること

### 1. Issue を delivery unit として持つ

Linear issue は、経理相談、オペレーターエスカレ、Agent 精度低下アラートを 1 delivery unit として持つのに向いている。

使う機能:

- Team workflow status
- Triage
- issue template / form template
- labels
- assignee / agent delegate
- parent/sub issue and issue relations
- comments and resolved threads
- issue documents
- custom views / filters

phase 候補:

- Triage
- 経理/顧客相談
- 方針確定
- ルール下書き中
- SV review
- PR / backtest
- 本番反映待ち
- 周知待ち
- Done
- Canceled / One-off decision / Transferred

### 2. Slack 起点の issue 化と thread sync

Linear の Slack integration / Asks は、Slack message から issue を作り、Slack thread と Linear comment thread を同期できる。MVP では、専用 channel に起票されたエスカレや相談を Asks 化するのが自然。

既存 Slack thread を後から Linear issue に同期する場合も、API の `attachmentLinkSlack(syncToCommentThread: true)` で可能。

### 3. ルール提案の HITL approval

Linear issue comment / comment thread を「承認待ちポイント」として使える。

例:

- AI が `Rule proposal v1` コメントを投稿
- SV が thread で質問 / CR
- AI が `Rule proposal v2` を投稿
- SV が「この案で PR 化してよい」と返信
- thread resolve を approval marker として扱う
- local orchestrator が resolved / status / reaction / comment command を見て PR 作成へ進める

Linear comment thread は resolve でき、決定済み論点を閉じる表現として使いやすい。

### 4. PR review / CR / merge

Linear の GitHub integration と Diffs はかなり相性がよい。

できること:

- issue と PR をリンク
- PR activity を Linear で見る
- code review を Linear 上で行う
- approve / request changes / comment
- 権限があれば merge
- GitHub PR の状態で issue status automation

つまり「ルール下書き作成 AI -> PR -> CR -> approval」は Linear 側にかなり寄せられる。

### 5. AI への指示

Linear は agent delegation と @mention を提供している。Codex integration もあり、issue context をもとに Codex Cloud Task を開始できる。

ただし今回の approval_rules / localops のようなローカル worktree、社内 DB、backtest、Slack bot token、bpo-desktop-app を使う workflow は、Linear の標準 agent だけでは足りない可能性が高い。

その場合、Linear agent というより「Linear webhook を受ける local orchestrator」が実行 agent になる。

## 追加開発が必要なこと

### 1. Linear status / comment / reaction をトリガーにする local orchestrator

Linear webhook は issue / comment / attachment / document / reaction などを受けられる。これを local server で受け、次のような action を走らせる。

- `SV approved proposal` -> Codex に PR 作成を指示
- `Needs accounting reply draft` -> Slack 返信 draft を生成
- `Post approved Slack reply` -> Slack thread に投稿
- `Run backtest` -> approval_rules worktree で backtest
- `PR changes requested` -> Codex resume
- `PR merged` -> production 反映確認 job
- `Prod verified` -> 周知 draft 作成

MVP では ngrok / Cloudflare Tunnel / Tailscale Funnel などでローカルに webhook を通してもよい。

### 2. bpo-desktop-app / 承認画面への返信

Linear は LayerOne のエスカレコメントや bpo-desktop-app に直接返信できない。

MVP では次のどちらか。

- local app / browser automation が Linear issue の承認済み reply draft を拾って bpo-desktop-app に投入する
- bpo-desktop-app 側に小さな plugin / URL scheme / local API を足し、Linear issue から `Open in BPO desktop` で該当エスカレを開く

最初は「draft 生成 + 人間が bpo-desktop-app で送信」が安全。

### 3. Slack 返信のガード付き実行

Slack sync thread だけで足りる場合は Linear comment から返信できる。

ただし「経理相談 channel には投稿したいが、同期 thread ではなく別 thread / 別書式 / メンション付きで返したい」などがあるなら、local orchestrator が必要。

重要なのは、AI が勝手に送るのではなく、Linear 上で明示的に approval marker を置くこと。

候補:

- comment thread resolve
- reaction
- status transition
- `@sv-terminal approve slack reply`
- label `approved:slack-reply`

### 4. 本番反映と verification

Linear / GitHub integration は PR merge までは強いが、実際に production へ反映されたか、approval-agent が新 rule set を読んでいるか、backtest / smoke が通ったかは社内固有。

ここは localops-codex-bridge の拡張領域。

必要な item:

- PR merge 検知
- deploy / rule set publish 検知
- production rule version 確認
- 対象 rule の smoke / replay
- Linear issue への verification comment

### 5. フェーズ別 required items の materialization

Linear の status だけでは「この phase で必要な item が揃っているか」は弱い。

MVP では issue description に checklist を生成し、local orchestrator が checklist / attachment / comments を更新する。

例:

```md
## Phase checklist
- [x] Source Slack thread attached
- [x] Tenant identified
- [x] Current rule candidates identified
- [ ] Accounting decision captured
- [ ] Rule proposal approved by SV
- [ ] PR attached
- [ ] Backtest result attached
- [ ] PR merged
- [ ] Production verified
- [ ] Announcement posted
```

## 役割分担案

### Linear native

- issue / phase / assignee / delegate
- comment thread and resolve
- issue template / form template
- Slack Asks / synced thread
- GitHub PR linking and review
- documents for decision memo
- views / filters / notifications

### Linear + local orchestrator

- comment / status / reaction -> action trigger
- Codex local session start / resume
- approval_rules worktree and PR creation
- backtest execution
- AI proposal generation and update
- PR feedback ingestion beyond standard Linear display
- production verification
- Slack special reply

### local app / bpo-desktop-app

- エスカレ画面を開く
- 申請詳細を見る
- reply draft を preview する
- 承認済み reply を投入する
- local logs / agent sessions を見る

### 将来プロダクト化

- approval-agent / workflow product 内で issue phase を持つ
- エスカレ、顧客相談、rule delivery を first-class object 化
- rule proposal approval UI
- production rule version verification
- operator / accounting reply composer

## MVP 推奨

### MVP 0: Linear 設定だけ

- SV Operations team を作る
- phase 用 workflow status を作る
- delivery issue template を作る
- Slack Asks / Slack message action から起票
- GitHub integration / Diffs を有効化
- views を作る

views:

- `SV Inbox`: Triage / 経理相談 / SV review
- `AI Working`: ルール下書き中 / PR backtest
- `Needs SV`: SV review / approval marker 待ち
- `Blocked by Accounting`: 経理/顧客回答待ち
- `Ready to Ship`: PR approved / 本番反映待ち
- `Prod Verify`: PR merged / production 未確認

### MVP 1: localops-linear-bridge

localops-codex-bridge を拡張し、GitHub Issue ではなく Linear issue を中心にする。

最低限:

- Linear issue 作成 / 更新
- Slack thread attachment / sync
- Linear webhook consumer
- status / comment command の処理
- Codex local run / resume
- PR attachment
- backtest result comment
- production verification comment

### MVP 2: local SV console

Linear issue から開ける local app。

- issue summary
- current phase
- required items
- AI session status
- draft replies
- dangerous actions preview
- `post to Slack`
- `open bpo-desktop-app`
- `run backtest`
- `resume Codex`

