# 実装ロードマップ

Linear の親 issue `BAA-1030` 配下で追跡する。

## リポジトリ方針

本リポジトリは SV Terminal MVP の仕様・実装メモ・設計変更の正本（canonical）とする。

`z/issues/20260603_hitl_sv_terminal_requirements` の初期作業メモは次にアーカイブ済み:

```text
docs/archive/20260603-hitl-sv-terminal-requirements/
```

## Demo 環境

- Linear project: `test-tenantid-00000000-0000-488b-81ca-8c90531b1945`
- Linear project URL: https://linear.app/layerx-inc/project/test-tenantid-00000000-0000-488b-81ca-8c90531b1945-9424122f2e0c/overview
- Slack operation channel: `#sv-approval-operation-demo`
- Slack inquiry channel: `#sv-approval-inquiries_test` (`C0B91JF61JL`)

## 完了

- `BAA-1064`: Linear 運用モデルとマーカー構文
- `BAA-1065`: n8n イベントキュースキーマとポーリングプロトコル
- `BAA-1066`: Slack 問い合わせから Linear issue 同期

## 次の作業

### BAA-1066: Slack 問い合わせから Linear issue 同期

- 専用 Slack チャンネルの入力フォーマットを決める
- Slack Events API のイベント種別を決める
- テナント project の解決方法を定義する
- Linear issue ブートストラップの mutation / API を定義する
- MVP1 フェーズ用サブ issue 作成を定義する
- Event Log コメント作成を定義する
- 公式 Slack 同期の紐づけを定義する
- 重複 / リプレイ / スレッド返信の扱いを定義する

仕様: [Slack 問い合わせから Linear issue 同期](06-slack-inquiry-linear-sync.md)

### BAA-1067: 意思決定からルール提案までの HITL

- `capture_decision` マーカーを定義する
- 意思決定メモのフォーマットを定義する
- ルール提案コメントのフォーマットを定義する
- 影響ルール / リスク / 想定 diff のフォーマットを定義する
- 承認 / CR / 却下マーカーを定義する
- CR 時のエージェント再開フローを定義する

論点整理: [方針確定から Rule Proposal 承認までの HITL 論点](07-decision-to-rule-proposal-hitl-questions.md)

体験整理: [Thread Experience Map](08-thread-experience-map.md)

実装契約: [Proposal & Delivery Contract](09-proposal-delivery-contract.md)

### BAA-1068: ローカル PC エージェントの PR / バックテストフロー

- Linear issue コンテキスト取得を定義する
- approval_rules の worktree / ブランチ / PR 作成を定義する
- Codex セッションの役割分担を定義する
- バックテスト結果フォーマットを定義する
- GitHub PR と Linear のリンク方法を定義する
- PR フィードバック検知と再開ルールを定義する

### BAA-1069: 配信検証と変更周知

- PR マージ検知を定義する
- 本番ルールバージョン / デプロイ SHA / スモークチェックを定義する
- 検証コメントのフォーマットを定義する
- 周知文ドラフトのフォーマットを定義する
- Slack 投稿先と実行者を定義する
- issue クローズ条件を定義する

### BAA-1070: ダミー・ルール性能アラート

- ダミーペイロードを定義する
- ダミートリガー方法を定義する
- 証跡と診断のフォーマットを定義する
- 提案承認時点で MVP1 フローに合流する

### BAA-1071: SV 向け薄い UI

- マーカー挿入ボタンを定義する
- n8n イベントボタンを定義する
- ローカルヘルパーのエントリポイントを定義する
- MVP の非目標（non-goals）を定義する
