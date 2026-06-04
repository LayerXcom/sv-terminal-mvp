# 理解メモ

## 資料から見えた事実

- 経費承認運用では、AI 中心の運用に移行でき、2 日目以降はほぼ AI タブ中心で対応できた。
- 一方で、SV 業務の認知負荷が大きく、特定メンバーの処理能力と画面環境に依存している。
- エスカレされた申請は 33 件、経理への相談は 19 回、ルール変更周知は 28 回、実際のルールセット変更は 14 回、ルール変更 PR は 38 件マージされた。
- 相談の多くは、個別案件判断、既存ルール解釈、恒久修正候補、一時運用が混ざっている。
- 「今回だけ OK」と「今後の一般基準」が混ざると、個別救済が勝手に一般ルール化されるリスクがある。
- Slack で決まったことが production までつながる見通しが弱く、方針確定後の見失いが再発ポイント。
- localops-codex-bridge は Slack / Langfuse 起点から `approval_rules/<tenant>/rules.json` 編集、GitHub PR、review feedback で Codex session resume までを束ねる既存のプロトタイプ。
- 既存 LocalOps の主な durable pointer は Slack channel / thread ts、GitHub Issue / PR、worktree、Codex session、PR event。

## Codex の理解

作りたいものは、単なるタスクボードでも、Slack bot でも、ルール作成 AI の UI でもない。

中心にあるべき概念は「SV がいま責任を持っている業務イシュー」で、そのイシューに対して、Slack の相談、AI agent session、PR、backtest、周知、暫定運用、production 反映確認がぶら下がる。

このターミナルの価値は、承認判断そのものを置き換えることではなく、承認業務の周辺に発生する HITL の判断点を見失わないこと。特に、AI が進めてよい作業、人間が意思決定すべき作業、顧客/経理に確認すべき作業を同じ面に載せ、状態遷移と証跡を残すことにある。

## 仮説

- MVP は Linear を SSoT にし、Slack / GitHub PR / Codex session をリンクとして束ねるのが最短。
- 最初から双方向同期や完全な UI を作るより、専用 Slack channel 起票 -> Linear 親 issue 作成 -> フェーズ issue / comment thread を更新、という薄い統合で十分価値が出る可能性が高い。
- 重要な状態は「作業中/完了」だけでは足りず、「個別判断済みだが一般基準未決」「方針確定だが PR 未反映」「PR merged だが production 未確認」「暫定運用中」「顧客確認待ち」を明示する必要がある。
- AI の主要役割は、ルールを勝手に直すことより、散らばった会話と証跡から次の human decision を小さく切り出すこと。

## 2026-06-03 追加理解

ユーザーが「勝ち」と見ている場所は 2 つ。

1. 月初の大量エスカレを、SV が破綻せず捌けること。
2. 経理相談 -> ルール下書き作成 AI への HITL -> 本番反映までの流れを、SV が Linear 上でトラックできること。

そのため、issue はフェーズを持つ必要がある。SV は Linear issue を見れば、今どのフェーズか、そのフェーズに必要なアイテムは何か、AI が何をしているか、SV 自身の next action は何かを一目で把握できるべき。

承認ルール更新は、ソースコードのデリバリーと同じ課題として捉える。つまり、ビジネス要件をすり合わせ、要件をもとにルールコードを生成し、PR で CR / 承認を受け、本番にデリバリーする流れである。Coding Agent がその大半をアシストし、Linear は起票からデリバリーまでのコンテキスト中心として機能し続ける。

SV は Linear から下界に介入できる必要がある。介入対象は、AI への指示、Slack への返信、エスカレーションコメントへの返信、ルールのデリバリー判断など。

## 2026-06-03 粒度の修正

当初は「親 issue = テナント運用 / 子 issue = 個別論点 / phase は property」が一覧性の面でよさそうと考えたが、ユーザーの指摘により修正。

1 つのイベントのゴールは、1 つないし複数の承認ルールを本番反映し、AI 精度を向上させること。その完了条件から逆算すると、Linear issue の自然な粒度は「経理への相談内容」「オペレーターからのエスカレーション」「Agent からの特定ルールの精度低下アラート」である。

つまり、issue は delivery unit であり、単なるトピックやテナント運用の箱ではない。解決とは、必要な方針確認、ルール下書き、PR / review / backtest、本番反映、周知が完了し、ルールに反映された状態を指す。

issue 数が増えること自体は許容する。むしろ delivery unit としての traceability を守るためには、issue 粒度を粗くしすぎない方がよい。

## 2026-06-04 イベント配送方針

SV が使う面は可能な限り薄くする。承認や action trigger は Linear の text marker、Chrome 拡張、薄い local server で表現する。

Linear API で取得できるものは Linear を source とする。Linear 自体に載せづらい UI event は n8n に送り、n8n で一旦 stack / audit log 化する。その後、エンジニア PC の local worker が n8n / Linear を pull して処理する。

エンジニア PC には inbound port を開けない方向を優先する。そのため、n8n から local server へ push するより、local worker が n8n Data Table / Google Sheets / Linear API を poll する pull queue 方式が MVP に向いている。

n8n external task runner は websocket 接続で outbound 実行に近いが、Code node 実行基盤であり、エンジニア PC 上で remote code を実行する構造になるため MVP では避けるのが無難。

## 2026-06-04 MVP workflow

MVP は 2 本。

1. MVP1: SV が Slack で問い合わせを開始し、経理とのやり取りが Linear issue に蓄積され、方針確定後にルール下書き作成、PR / review / merge / 本番反映 / 周知まで進む。
2. MVP2: agent が特定ルールの性能低下を検知し、Linear issue を起票し、修正案 / PR / review / merge / 本番反映 / 周知まで進む。MVP では性能低下検知は dummy event でよい。

Linear の private team を作る。tenant ごとに Project を切る。チケットの status と label で状態を表現し、現在のボール保持者は assignee で表現する。各フェーズは親 issue の sub issue として表現する。Slack link や document link は公式機能を使う。

Linear の comment は comment ごとに thread を持てるため、親 issue には bot が `SV Terminal Event Log` comment を作り、その thread を event log の格納場所にする。人間の承認や proposal review は別 comment thread にする。

問い合わせ開始は、最初は特定 Slack channel への投稿を Slack bot event + n8n flow で拾い、Linear issue 作成と Slack thread sync を自動で行う。Linear Asks も候補だが、private team / tenant Project / bot account / sub issue / Event Log の初期化を細かく制御したいため、MVP では Slack bot event + n8n + Linear API を本命にする。
