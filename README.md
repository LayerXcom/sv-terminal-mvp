# SV Terminal MVP

SV Terminal は、Linear を通じて human-in-the-loop（HITL）の承認ルール配信を運用するための MVP 設計です。

目的は、SV が月次のエスカレーションを多数扱う際に、次の項目を見失わないことです。

- 経理 / オペレーターとの会話
- ルール変更の意思決定
- AI が生成したルール提案
- PR とバックテスト
- 本番検証
- 最終的な Slack 周知

本リポジトリは現時点ではプロダクト / 運用仕様を格納しています。実装は段階的に追加していきます。

## コアアイデア

承認ルールの更新は、ソースコードの配信と同様に扱います。

```text
業務上の議論
  -> 意思決定の記録
  -> エージェントによるルール提案
  -> SV 承認
  -> PR / バックテスト
  -> マージ / 本番検証
  -> 周知
```

Linear がステータス・証跡・承認・引き継ぎの SSoT（単一の正）です。n8n はイベントキューと監査ログを保持します。重い実行エージェントはエンジニアのローカル PC 上で動き、n8n / Linear から作業を取得します。

## MVP ストーリー

### MVP1: Slack 問い合わせからルール配信まで

SV が専用 Slack チャンネルで問い合わせを開始します。会話は Linear issue に同期されます。意思決定が記録されたあと、エージェントがルール案を起草し、SV 承認後に PR を作成、バックテストを実行し、配信を検証し、周知文を起草します。

### MVP2: ルール性能アラートからルール配信まで

エージェントがルール性能の劣化を検知します。MVP ではダミーイベントから開始します。システムが Linear issue を作成し、証跡を集め、修正案を提案したうえで、MVP1 と同じ PR / バックテスト / 配信 / 周知のフローに進みます。

## ドキュメント

- [コンテキスト](docs/01-context.md)
- [Linear モデルとマーカー](docs/02-linear-model-and-markers.md)
- [n8n イベントキュープロトコル](docs/03-n8n-event-queue-protocol.md)
- [MVP イベント設計](docs/04-mvp-event-design.md)
- [実装ロードマップ](docs/05-implementation-roadmap.md)
- [アーカイブ済み作業メモ](docs/archive/20260603-hitl-sv-terminal-requirements/)

## 現在の Linear トラッキング

- 親 issue: `BAA-1030`
- 完了:
  - `BAA-1064`: Linear モデルとマーカー構文
  - `BAA-1065`: n8n イベントキュースキーマ / ポーリングプロトコル
- 次:
  - `BAA-1066`: Slack 問い合わせから Linear issue 同期フロー

## 作業メモの移行

`z/issues/20260603_hitl_sv_terminal_requirements` の初期作業メモは、次の場所にコピー済みです。

```text
docs/archive/20260603-hitl-sv-terminal-requirements/
```

今後、仕様・実装メモ・設計変更の正本は本リポジトリです。
