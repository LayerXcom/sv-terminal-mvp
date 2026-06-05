# Ports and Adapters Worker Architecture

## 目的

local worker は Ports and Adapters / Hexagonal Architecture に従う。
domain / application は Linear、n8n、GitHub、filesystem の具象 API を知らない。

## Dependency Rule

```text
domain <- application <- ports <- adapters <- cli
```

- `domain`: marker、issue model、queued event、worker result
- `application`: action detection、context packet build、worker loop、write-back body生成
- `ports`: `IssueRepository`, `EventQueue`, `RunStore`, `Clock`
- `adapters`: Linear GraphQL、n8n HTTP、local fixture、file run store
- `cli`: composition root。どの adapter を使うかを決める

内側の層は外側の層を import しない。

## Current Package Layout

```text
sv_terminal_worker/
  domain/
    markers.py
    models.py
    events.py
  application/
    detect_actions.py
    build_context.py
    run_worker.py
    writeback.py
  ports/
    issue_repository.py
    event_queue.py
    run_store.py
    clock.py
  adapters/
    local/
      fixture_issue_repository.py
      fixture_event_queue.py
      file_run_store.py
    linear/
      graphql_client.py
      issue_repository.py
    n8n/
      event_queue.py
  cli.py
```

## Usecase Flow

```text
EventQueue.poll_queued
  -> IssueRepository.get_issue
  -> detect_approved_proposal
  -> build_context_packet
  -> RunStore.write_context_and_state
  -> IssueRepository.write_event_log
  -> EventQueue.mark_processed / mark_failed
```

重要:

- n8n event は trigger metadata
- Linear issue が business source
- synced Slack thread / linked PR は Linear 側の公式連携を SSoT にする
- PR / backtest 実行は Step 4 以降

## Composition Root

`sv_terminal_worker/cli.py` が composition root。

fixture mode:

```bash
python3 -m sv_terminal_worker.cli poll --once --event-source fixture --issue-source fixture
```

real adapter mode:

```bash
LINEAR_API_KEY=... N8N_BASE_URL=... N8N_API_KEY=... \
python3 -m sv_terminal_worker.cli poll --event-source n8n --issue-source linear
```

## Idempotency

`RunStore` が `.sv-terminal/runs/<issue>/<action_id>/state.json` を見る。
同じ issue / action_id / action_type がすでに処理済みなら skip する。

## Testing Strategy

- domain tests: marker parsing / approval detection
- application tests: ports mock or local adapters で event -> context build
- adapter tests: fixture adapter / file store / HTTP request body
- CLI tests: fixture mode の `poll --once` と `run-action`
