# MVP イベント設計

## コンポーネント

### Linear

- 将来はプライベートチーム
- テナントごとの tenant project
- 親 issue = 配信単位
- サブ issue = フェーズ
- ステータス = 実行状態
- ラベル = トリガー / 解決 / リスク / アクション
- 担当者 = 現在のオーナー
- コメントスレッド: Event Log、Approval、PR & Backtest

### Slack

- 専用の問い合わせチャンネル
- トップレベル投稿時の Slack bot イベント
- n8n フローが Linear issue を作成
- Linear 公式 Slack 同期でスレッド内容を紐づけ

### n8n

- Slack / Chrome 拡張 / Linear webhook イベントを受信
- Data Table にイベント行を書き込む
- 重い処理は実行しない

### ローカル Worker

- n8n と Linear をポーリング
- 最新の issue コンテキストを取得
- Codex / approval_rules / バックテスト / GitHub PR / 本番検証を実行
- 結果を Linear に書き戻す

## MVP1: Slack 問い合わせからルール配信まで

1. Slack 問い合わせ作成
   - トリガー: 専用 Slack チャンネルの新規トップレベル投稿
   - n8n がイベントを作成
   - bot アカウントが Linear issue とサブ issue を作成
   - Slack スレッドを Linear に同期

2. 経理相談の更新
   - Slack / Linear 同期で議論を運ぶ
   - 任意で worker が後から意思決定っぽい文言を検知可能

3. 方針確定
   - SV が `SV_ACTION` マーカーを追加
   - worker が意思決定を要約
   - issue をルール下書きフェーズへ進める

4. ルール下書き依頼
   - worker がエージェントで提案を起草
   - Approval スレッドに提案を投稿
   - 担当を SV に移す

5. ルール提案の承認
   - SV が承認、変更依頼、または却下
   - 危険操作には `SV_APPROVAL` が必須

6. PR とバックテスト
   - ローカル PC のエージェントが approval_rules を編集
   - PR を作成
   - バックテストを実行
   - PR と結果を Linear にリンク

7. PR レビュー / マージ
   - レビュアーは GitHub / Linear 連携を利用
   - CR でエージェントを再開
   - マージで配信検証をトリガー

8. 本番検証完了
   - worker が本番ルールバージョン / スモークを確認
   - 検証コメントを投稿

9. 変更周知投稿
   - worker が周知文を起草
   - SV が承認
   - Slack に投稿
   - 親 issue は PR マージ直後ではなく、周知完了後にクローズ

## MVP2: ダミー・ルール性能アラートからルール配信まで

1. ダミー・悪いフィードバックアラート
   - トリガー: 手動 n8n / ローカル worker のダミーイベント
   - イベントに tenant、rule id、悪いフィードバック件数、ウィンドウを含める

2. Linear issue 作成
   - ラベル: `trigger:rule-performance-alert`, `trigger:dummy-alert`
   - フェーズ用サブ issue を作成
   - Event Log スレッドを作成

3. 証跡収集
   - worker がダミーまたは実証跡を収集
   - 影響ルールと診断結果を投稿

4. 診断と提案
   - worker が修正案を提案
   - SV が承認または変更依頼

5. PR / バックテスト / マージ / 周知
   - 提案承認後は MVP1 と同じフロー
