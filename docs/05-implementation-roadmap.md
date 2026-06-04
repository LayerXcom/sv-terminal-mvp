# Implementation Roadmap

Tracked in Linear under parent issue `BAA-1030`.

## Repository Policy

This repository is the canonical place for SV Terminal MVP specifications, implementation notes, and design changes.

The original working notes from `z/issues/20260603_hitl_sv_terminal_requirements` are archived under:

```text
docs/archive/20260603-hitl-sv-terminal-requirements/
```

## Done

- `BAA-1064`: Linear operation model and marker syntax
- `BAA-1065`: n8n event queue schema and polling protocol

## Next

### BAA-1066: Slack Inquiry to Linear Issue Sync

- Decide dedicated Slack channel input format
- Decide Slack Events API event type
- Define tenant project resolution
- Define Linear issue bootstrap mutation/API
- Define MVP1 phase sub-issue creation
- Define Event Log comment creation
- Define official Slack sync attachment
- Define duplicate / replay / thread reply handling

### BAA-1067: Decision to Rule Proposal HITL

- Define `capture_decision` marker
- Define decision memo format
- Define rule proposal comment format
- Define affected rules / risk / expected diff format
- Define approval / CR / reject markers
- Define CR agent resume flow

### BAA-1068: Local PC Agent PR / Backtest Flow

- Define Linear issue context fetch
- Define approval_rules worktree / branch / PR creation
- Define Codex session roles
- Define backtest result format
- Define GitHub PR to Linear link
- Define PR feedback detection and resume rules

### BAA-1069: Delivery Verification and Announcement

- Define PR merge detection
- Define production rule version / deployed SHA / smoke check
- Define verification comment format
- Define announcement draft format
- Define Slack posting destination and actor
- Define issue close condition

### BAA-1070: Dummy Rule Performance Alert

- Define dummy payload
- Define dummy trigger method
- Define evidence and diagnosis format
- Join MVP1 flow at proposal approval

### BAA-1071: SV Thin UI

- Define marker insertion buttons
- Define n8n event buttons
- Define local helper entrypoints
- Define MVP non-goals
