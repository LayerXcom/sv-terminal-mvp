# Context

## Problem

SVs operate approval-agent based expense approval workflows. They handle:

- escalations from human operators
- accounting / customer consultation
- degraded approval-rule performance
- rule updates and announcements

The current work is spread across Slack, Linear, GitHub PRs, local agent sessions, and production verification. This is manageable for one highly skilled SV with a large monitor, but it does not scale to multiple tenants or high-volume monthly operations.

## Desired Outcome

SVs should be able to look at Linear and immediately know:

- what task is active
- which phase it is in
- who has the ball, SV or agent
- what evidence / Slack thread / PR / backtest is attached
- what human decision is needed next

The SV-facing surface should stay thin. Linear remains the main UI; Chrome extension / local UI should only assist with marker insertion and explicit actions.

## Design Principle

Approval-rule maintenance is treated as a delivery pipeline:

```text
requirements discussion
  -> rule implementation
  -> code review
  -> delivery
  -> announcement
```

The source of truth for approval rules remains the rule repository. The source of truth for task state and human decisions is Linear.

