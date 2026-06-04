# 方針確定から Rule Proposal 承認までの HITL 論点

Linear issue: `BAA-1067`

## このフェーズの目的

Slack / Linear 同期された経理相談が「何らかの結論」に到達したあと、その結論を rule proposal に変換し、SV が PR 作成に進めてよいかを判断できる状態にする。

このフェーズで決めるべきことは、実装方法そのものではなく、次の境界である。

```text
経理相談の結論
  -> decision memo
  -> rule proposal
  -> SV approval / CR / reject
  -> PR作成へ進む条件
```

## 一番大事な問い

SV は何を見て「このルール案なら PR 作成してよい」と判断するのか。

ここが曖昧なままだと、agent が「それっぽいルール文」を作ってしまい、SV は結局 Slack / PR / rules.json / backtest を横断して確認することになる。

## 決めるべき論点

### 1. `capture_decision` とは何か

`capture_decision` は、経理相談の全会話を要約する命令ではない。

SV が「この相談は一旦結論が出た。次にルール化可否を検討してよい」と明示するイベント。

決めること:

- SV が marker を置く場所
  - 親 issue description
  - Slack sync comment thread
  - Event Log thread
  - Chrome extension button
- marker の最小形式
- marker に含めるべき target
- marker を取り消す方法

候補:

```md
[SV_ACTION id=act_20260604_001 type=capture_decision target=slack_thread status=requested]
```

追加情報を持つ版:

```md
[SV_ACTION id=act_20260604_001 type=capture_decision target=slack_thread status=requested resolution_hint=rule_change]
```

### 2. decision memo に何を含めるか

decision memo は、経理相談から rule proposal へ進むための中間成果物。

これは「会話要約」ではなく、「実装/非実装判断に必要な業務決定メモ」。

必須項目候補:

- Source
  - Slack thread URL
  - Linear issue
  - tenant
- Decision
  - 今回の結論
  - 誰が合意したか
  - 合意日時
- Scope
  - 今回だけの個別判断か
  - 今後の一般基準か
  - 暫定運用か
  - product / form / ops へ移管すべきか
- Rule Impact
  - ルール変更が必要か
  - 既存ルール修正か
  - 新規ルール追加か
  - LLM補足だけで足りるか
  - knowledge / runbook だけで足りるか
- Non-goals
  - 今回一般化しないこと
  - 触らないルール
  - 未決の論点
- SV Next Action
  - proposal 作成に進めてよい
  - 経理に追加確認
  - one-off decision として close
  - product / ops issue に移管

### 3. rule proposal はどの粒度で出すか

rule proposal は PR そのものではない。SV が PR 作成前に判断するための提案。

決めること:

- proposal 1件 = rule 1件か、delivery issue 1件か
- 複数ルールにまたがる場合の表現
- ルール化しない提案を許容するか
- proposal versioning

推奨:

- proposal は delivery issue 単位で出す
- `Affected rules` に複数 rule を列挙する
- proposal version は `proposal:v1`, `proposal:v2` とする

### 4. proposal comment の必須項目

SV が見るべきものを1コメントにまとめる。

必須項目候補:

- Summary
- Source decision memo
- Recommended resolution
  - `rule_change`
  - `one_off_decision`
  - `policy_pending`
  - `transferred_product`
  - `no_change`
- Affected rules
  - rule id
  - current behavior
  - proposed behavior
- Proposed change
  - approval condition
  - reject / needs review behavior
  - LLM supplement
  - knowledge update
- Why this is safe
  - scope
  - non-goals
  - backtest expectation
- Risks
  - over-generalization
  - stale business vocabulary
  - targetItems / applyCondition mismatch
  - product/form dependency
- Expected diff
  - rules.json path
  - rough fields to change
- SV actions
  - approve
  - request changes
  - reject
  - ask accounting

### 5. approval / CR / reject marker

危険操作である PR 作成には、明示的な approval marker が必要。

決めること:

- approval marker を誰が書くか
  - SVが手で書く
  - Chrome extensionが挿入
  - botがbutton相当のcomment commandを補助
- approval marker の対象
  - proposal version
  - action id
  - issue id
- CR の書き方
- reject と one-off close の違い

候補:

```md
[SV_APPROVAL action_id=act_20260604_002 decision=approved target=proposal:v1 by=hirotea]
```

CR:

```md
[SV_APPROVAL action_id=act_20260604_002 decision=changes_requested target=proposal:v1 by=hirotea]
```

Reject:

```md
[SV_APPROVAL action_id=act_20260604_002 decision=rejected target=proposal:v1 reason=one_off_decision by=hirotea]
```

### 6. CR 時の agent resume flow

CR は PR review ではなく、proposal review の CR。

決めること:

- CR comment のsource of truth
- agent が読む範囲
- proposal:v2 の作り方
- 古い proposal thread をどう扱うか
- assignee をいつ SV / agent に戻すか

推奨:

1. SV が Approval thread に CR を返信
2. marker `decision=changes_requested`
3. local worker が `rule_proposal_changes_requested` event を作る
4. agent が issue / decision memo / proposal:v1 / CR comment を読む
5. `proposal:v2` を同じ Approval thread または新規 comment に出す
6. assignee を SV に戻す

### 7. Approval thread を resolve するタイミング

Linear comment thread の resolve は「このapproval論点は閉じた」という印。

決めること:

- approve した瞬間に resolve するか
- PR 作成完了後に resolve するか
- PR merge後に resolve するか

推奨:

- proposal approval thread は「PR作成eventが成功したら resolve」
- つまり approve marker だけでは resolve しない
- PR作成失敗時に未resolveのままにして、SVが状態を追えるようにする

### 8. rule proposal なしで close する経路

すべてがルール変更になるわけではない。

決めること:

- one-off decision として close する marker
- policy pending に戻す marker
- product / form / ops 移管 marker

候補:

```md
[SV_ACTION id=act_20260604_003 type=close_as_one_off_decision target=issue status=requested]
[SV_ACTION id=act_20260604_004 type=transfer_to_product_issue target=issue status=requested]
```

## 推奨する BAA-1067 の決定範囲

BAA-1067 では、実装コードに入らず次を決める。

1. `capture_decision` marker
2. decision memo format
3. rule proposal comment format
4. approval / CR / reject marker
5. CR resume flow
6. Approval thread resolve condition
7. rule proposal に進まない close / transfer 経路

## BAA-1067 でまだ決めないこと

- 実際の approval_rules 編集手順
- PR 作成コマンド
- backtest 実行方法
- production verification 方法
- Slack announcement の文面

これらは `BAA-1068` / `BAA-1069` で扱う。

## 次に壁打ちしたい質問

1. decision memo は agent が自動生成したものを SV が承認するのか、SV が marker だけ置けば agent がそのまま proposal に進んでよいのか。
2. proposal approval は PR 作成の承認なのか、ルール方針の承認なのか。両方を分ける必要があるか。
3. one-off decision / no-change / product transfer は MVP1 で明示的に扱うか、まずは rule_change だけに絞るか。
4. Approval thread の resolve は PR 作成成功時でよいか。

