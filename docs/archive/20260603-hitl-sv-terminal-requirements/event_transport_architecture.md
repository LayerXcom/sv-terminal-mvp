# イベント配送アーキテクチャ案

## ユーザー方針

SV が使う UI / 操作面は可能な限り薄くする。

- 承認などのイベント管理は Linear のテキスト内部の特殊文字列をフラグとして使う。
- SV は Chrome 拡張と薄い local server で作業する。
- Linear API で直接取れる情報は Linear から取る。
- Linear 自体で持てないイベントは n8n を中継し、n8n に一度スタックしてログを残す。
- エンジニア PC にはできるだけ変な公開 port を開けない。
- n8n に Slack Socket Mode のような「ローカル PC が outbound 接続だけでイベントを受ける」方法があれば使いたい。
- 代替として、Google Sheets などに一度イベントを書き、ローカル PC が取りに行く方式も検討する。

## 調査結果

### n8n の Webhook

n8n の Webhook node は外部から n8n 側へ HTTP リクエストを受けて workflow を起動するもの。これは「SV Chrome 拡張 -> n8n」や「Linear webhook -> n8n」には向いている。

一方で、n8n からエンジニア PC の local server に webhook するには、エンジニア PC 側に公開 endpoint / tunnel が必要。

### n8n Queue mode

Queue mode は n8n main が trigger / webhook を受け、Redis に execution を積み、worker が処理する構成。worker は Redis と n8n DB にアクセスする必要がある。Slack Socket Mode 的に任意のローカル PCへ安全にイベントを届ける仕組みというより、n8n 自体の分散実行構成。

### n8n external task runner

task runners は Code node の JavaScript / Python を n8n 本体から分離して実行する仕組み。task runner は task broker に websocket 接続するため「outbound 接続でコード実行を受ける」という意味では Socket Mode に近い。

ただし、これは汎用イベント購読というより Code node の実行基盤。エンジニア PC に置くと、n8n workflow の Code node がエンジニア PC 上で実行される構造になり、セキュリティと運用の注意点が大きい。MVP で使うにはやや危ない。

## 推奨案

### A. Pull queue 方式

n8n は「イベント箱 / 監査ログ / 配線」として使い、エンジニア PC の local worker は n8n / Linear を定期 poll する。

流れ:

1. SV が Linear issue 上で特殊文字列を入れる、または Chrome 拡張から action を送る。
2. Chrome 拡張は n8n webhook に event を POST する。
3. n8n は event を data table / Google Sheets / DB に append し、ack を返す。
4. エンジニア PC の local worker は n8n API / Google Sheets / Linear API を poll する。
5. 未処理 event を拾ったら、Linear API で issue 最新状態を取得する。
6. event + Linear state を使って Codex / approval_rules / Slack / bpo-desktop-app 操作を実行する。
7. 実行結果を Linear comment に戻す。
8. n8n 側の event を processed / failed に更新する。

利点:

- エンジニア PC に inbound port を開けない。
- SV 側は Linear と Chrome 拡張だけで薄い。
- n8n は監査ログと retry queue になる。
- Linear を SSoT として維持しやすい。

弱点:

- 即時性は poll 間隔に依存する。
- idempotency / lock / retry を local worker 側で設計する必要がある。

### B. Linear polling only

n8n を使わず、local worker が Linear issue/comment/reaction を poll する。

流れ:

1. SV が Linear issue に特殊文字列を書く。
2. local worker が Linear API で該当 team / view / label を定期 poll。
3. 未処理 command を検出して実行。
4. 結果を Linear に comment。

利点:

- 一番薄い。
- Linear だけが SSoT。
- n8n なしで始められる。

弱点:

- Chrome 拡張由来のイベントや Linear に載せづらい UI event を扱いにくい。
- 監査ログ / replay queue は Linear comment に寄せる必要がある。

### C. Tunnel webhook 方式

Cloudflare Tunnel / ngrok / Tailscale Funnel などでエンジニア PC の local server を外から叩けるようにする。

利点:

- push 型で即時。
- local server の設計が単純。

弱点:

- 公開 endpoint を持つ。
- 認証 / 署名 / allowlist / secret rotation が必要。
- ユーザー方針「変な port を開けたくない」とはやや相性が悪い。

### D. n8n external task runner 方式

エンジニア PC に n8n task runner を置き、n8n の Code node を local で実行する。

利点:

- inbound port なしで local 実行に近いことができる。
- n8n workflow 上で orchestration を書ける。

弱点:

- Code node 実行基盤なので、業務イベント worker としてはやや無理がある。
- エンジニア PC で remote code を実行する設計になり、危険。
- self-hosted n8n 前提になりやすい。

## 推奨する MVP 構成

まずは A を推奨。

```text
Linear issue/comment
  |
  | (SV Chrome extension reads issue / sends action)
  v
n8n webhook
  |
  | append event + audit log
  v
n8n Data Table or Google Sheets
  ^
  | poll
Engineer local worker
  |
  | fetch Linear issue details
  | run Codex / backtest / Slack draft / bpo-desktop helper
  v
Linear comment / issue status update
```

Linear に載せられる command は Linear text marker だけで運用する。Chrome 拡張は「Linear のテキスト編集を助ける」「n8n event を明示送信する」「local helper を起動する」程度に薄く保つ。

## marker 例

```md
<!-- sv-action
id: 20260604-001
type: approve_rule_proposal
status: requested
target: proposal:v2
requested_by: hirotea
-->
```

または人間が読みやすい形式:

```md
[SV_ACTION id=20260604-001 type=approve_rule_proposal target=proposal:v2 status=requested]
```

local worker は処理後に次を追記する。

```md
[SV_ACTION_RESULT id=20260604-001 status=done run_id=... pr=https://...]
```

## 設計上の注意

- event id を必須にする。
- 同じ event id を二重処理しない。
- Linear issue state を毎回再取得し、古い payload だけを信じない。
- AI が読む入力は Linear issue body / comment / Slack sync thread に限定し、n8n payload は trigger metadata として扱う。
- Slack 投稿や本番反映など危険操作は、Linear 上の explicit approval marker がある場合だけ実行する。
- n8n / Google Sheets には secret や申請詳細の全文を置かず、issue id / action type / metadata 程度にする。

