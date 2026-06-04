# Linear 転記ログ

## 2026-06-04

親 issue:

- BAA-1030: あるべきもの必要なものを整理する
- Project: SVのエスカレ・ルール変更周知などを複数テナント持てるようにする運用を考える
- Team: approval_agent

追加した親 issue コメント:

- `SV Terminal MVP 実装チェックリスト`
- Event marker: `[SV_EVENT id=evt_20260604_linear_transfer type=planning_checklist_created status=done source=codex]`

作成した sub issues:

- BAA-1064: SV Terminal MVP: Linear運用モデルとmarker文法を確定する
- BAA-1065: SV Terminal MVP: n8n event queue schemaとpolling protocolを定義する
- BAA-1066: SV Terminal MVP1: Slack問い合わせ投稿をLinear issueへ同期するflowを設計する
- BAA-1067: SV Terminal MVP1: 方針確定からrule proposal承認までのHITL flowを設計する
- BAA-1068: SV Terminal MVP1: local PC agentでPR作成/backtest/feedback resumeするflowを設計する
- BAA-1069: SV Terminal MVP1: merge後の本番反映確認とルール変更周知flowを設計する
- BAA-1070: SV Terminal MVP2: dummy rule performance alertからLinear issue起票するflowを設計する
- BAA-1071: SV Terminal MVP: SV向けChrome拡張/薄いlocal UIの責務を最小化して定義する

完了:

- BAA-1064 を Done にした。
- Linear運用モデル、issue粒度、phase表現、status/label/assignee、comment thread、marker文法を決定仕様としてコメントに残した。

次:

- BAA-1065: n8n event queue schemaとpolling protocolを定義する。

## BAA-1065 作業

- BAA-1065 を In Progress にした。
- n8n Data Table `sv_terminal_events` のschema / status lifecycle / dedupe / lease / retry / local worker polling protocol を `baa_1065_n8n_event_queue_protocol.md` に作成した。
