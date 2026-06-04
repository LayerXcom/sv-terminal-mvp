# MVP Event Design

## Components

### Linear

- private team in the future
- tenant project per tenant
- parent issue as delivery unit
- sub-issues as phases
- status for execution state
- label for trigger / resolution / risk / action
- assignee for current owner
- comment threads for Event Log, Approval, PR & Backtest

### Slack

- dedicated inquiry channel
- Slack bot event on new top-level posts
- n8n flow creates Linear issue
- Linear official Slack sync keeps thread contents attached

### n8n

- receives Slack / Chrome extension / Linear webhook events
- writes event rows to Data Table
- does not execute heavy work

### Local Worker

- polls n8n and Linear
- fetches latest issue context
- runs Codex / approval_rules / backtest / GitHub PR / production verification
- writes results back to Linear

## MVP1: Slack Inquiry to Rule Delivery

1. Slack inquiry created
   - Trigger: new top-level post in dedicated Slack channel
   - n8n creates event
   - Linear issue and sub-issues are created by bot account
   - Slack thread is synced to Linear

2. Accounting discussion updated
   - Slack / Linear sync carries discussion
   - Optional worker can detect decision-like language later

3. Decision captured
   - SV adds `SV_ACTION` marker
   - worker summarizes decision
   - issue moves to rule draft phase

4. Rule draft requested
   - worker runs agent to draft proposal
   - proposal is posted to Approval thread
   - assignee moves to SV

5. Rule proposal approval
   - SV approves, requests changes, or rejects
   - dangerous actions require `SV_APPROVAL`

6. PR and backtest
   - local PC agent edits approval_rules
   - creates PR
   - runs backtest
   - links PR and reports result to Linear

7. PR review / merge
   - reviewer uses GitHub / Linear integration
   - CR resumes the agent
   - merge triggers delivery verification

8. Production verified
   - worker checks production rule version / smoke
   - posts verification comment

9. Announcement posted
   - worker drafts announcement
   - SV approves
   - Slack post is made
   - parent issue closes after announcement, not immediately after PR merge

## MVP2: Dummy Rule Performance Alert to Rule Delivery

1. Dummy bad feedback alert
   - Trigger: manual n8n / local worker dummy event
   - Event includes tenant, rule id, bad feedback count, and window

2. Linear issue created
   - label: `trigger:rule-performance-alert`, `trigger:dummy-alert`
   - phase sub-issues created
   - Event Log thread created

3. Evidence collected
   - worker gathers dummy or real evidence
   - affected rule and diagnosis are posted

4. Diagnosis and proposal
   - worker proposes fix
   - SV approves or requests changes

5. PR / backtest / merge / announcement
   - same as MVP1 after proposal approval

