# SV Terminal MVP

SV Terminal is an MVP design for operating human-in-the-loop approval-rule delivery through Linear.

The goal is to let an SV handle many monthly escalations without losing track of:

- accounting / operator conversations
- rule-change decisions
- AI-generated rule proposals
- PRs and backtests
- production verification
- final Slack announcements

This repository currently stores the product / operations specification. Implementation will be added incrementally.

## Core Idea

Approval-rule updates are treated like source-code delivery.

```text
business discussion
  -> decision capture
  -> rule proposal by agent
  -> SV approval
  -> PR / backtest
  -> merge / production verification
  -> announcement
```

Linear is the SSoT for status, evidence, approvals, and handoffs. n8n stores event queue / audit log records. The heavy execution agent runs on an engineer's local PC and pulls work from n8n / Linear.

## MVP Stories

### MVP1: Slack Inquiry to Rule Delivery

SV starts an inquiry in a dedicated Slack channel. The conversation syncs into a Linear issue. After the decision is captured, an agent drafts a rule proposal, creates a PR after SV approval, runs backtests, verifies delivery, and drafts the announcement.

### MVP2: Rule Performance Alert to Rule Delivery

An agent detects a rule-performance degradation. For MVP, this starts from a dummy event. The system creates a Linear issue, gathers evidence, proposes a fix, and then follows the same PR / backtest / delivery / announcement flow as MVP1.

## Documents

- [Context](docs/01-context.md)
- [Linear Model and Markers](docs/02-linear-model-and-markers.md)
- [n8n Event Queue Protocol](docs/03-n8n-event-queue-protocol.md)
- [MVP Event Design](docs/04-mvp-event-design.md)
- [Implementation Roadmap](docs/05-implementation-roadmap.md)
- [Archived Working Notes](docs/archive/20260603-hitl-sv-terminal-requirements/)

## Current Linear Tracking

- Parent issue: `BAA-1030`
- Completed:
  - `BAA-1064`: Linear model and marker syntax
  - `BAA-1065`: n8n event queue schema / polling protocol
- Next:
  - `BAA-1066`: Slack inquiry to Linear issue sync flow

## Working Note Migration

The initial working notes from `z/issues/20260603_hitl_sv_terminal_requirements` were copied into:

```text
docs/archive/20260603-hitl-sv-terminal-requirements/
```

Going forward, this repository is the canonical place for specifications, implementation notes, and design changes.
