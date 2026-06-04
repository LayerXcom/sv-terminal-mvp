# HITL SV Terminal 要件整理

## 原依頼

ユーザーは、自動承認オペレーションにおける HITL の中心ターミナルを作りたいが、いきなりフルで作ると大変なので、まず「本当に何が欲しいか」を壁打ちしながら整理したい。

対象業務は、approval-agent を使った経費申請承認業務の司令官である SV 業務。SV は、人間オペレーターからの申請内容エスカレーション対応、性能が下がったルールの改善、お客様との承認ルール相談などを扱う。

作りたいものの初期イメージ:

- 承認業務を除いた HITL タッチポイントの集約点
- タスク状態が一目でわかる
- ステータスは AI も人も更新する
- Slack link / thread が同期される
- フェーズ管理ができる
- 親チケットで経理相談、ルール下書き、ルール反映、全体周知などを束ねる
- フェーズは Slack thread、agent session、必要なら PR を束ねる
- 起点は専用 Slack channel での起票、または巡回 AI / event hook が候補
- Linear をタスク管理の主体にできそう。必要なら Chrome 拡張などで補う
- Linear comment thread で AI が「どうしますか？」と提案し、人間が判断して resolve する運用も候補

参照資料:

- Slack 経理相談タスク: https://layer-x.slack.com/archives/C0B63DRBQDQ/p1780034068851999
- Slack ルール周知例: https://layer-x.slack.com/archives/C0B63DRBQDQ/p1780295277393949
- localops-codex-bridge/README.md
- Notion: https://app.notion.com/p/layerx/LayerX-2026-06-373cdd370bae80a6a287dc27e1db2f6c
- Miro: https://miro.com/app/board/uXjVGtzST3s=/
- 添付テキスト 2 件
- スクリーンショット 2026-06-03 23.15.12.png

## 今回のタスク

1. 与えられた資料を読み込み、今回のトライとユーザーがやろうとしていることを深く理解する。
2. Codex の言葉でまとめる。
3. 要件を引き出すため、インタビュー形式で質問する。

