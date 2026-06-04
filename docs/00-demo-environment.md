# MVP Demo Environment

This document records the concrete MVP demo environment.

## Linear

Tenant project:

- Name: `test-tenantid-00000000-0000-488b-81ca-8c90531b1945`
- URL: https://linear.app/layerx-inc/project/test-tenantid-00000000-0000-488b-81ca-8c90531b1945-9424122f2e0c/overview

Tenant key:

```text
test
```

Tenant id:

```text
00000000-0000-488b-81ca-8c90531b1945
```

MVP routing rule:

- Slack inquiry channel `C0B91JF61JL` maps to this Linear project.
- If Slack post has `tenant: test` or `tenant_id: 00000000-0000-488b-81ca-8c90531b1945`, route to this project.

## Slack

Operations channel:

```text
#sv-approval-operation-demo
```

Inquiry-only channel:

```text
#sv-approval-inquiries_test
channel_id: C0B91JF61JL
```

## MVP Input Format

For the demo channel, the minimum top-level Slack post is:

```md
tenant: test
type: accounting_inquiry
title: <問い合わせタイトル>

相談内容:
<本文>
```

`tenant_id` may be omitted when the post is in `C0B91JF61JL`; the channel default is:

```text
00000000-0000-488b-81ca-8c90531b1945
```

## Demo Config Sketch

```yaml
slack:
  operation_channel:
    name: sv-approval-operation-demo
  inquiry_channels:
    - name: sv-approval-inquiries_test
      id: C0B91JF61JL
      default_tenant_key: test
      default_tenant_id: 00000000-0000-488b-81ca-8c90531b1945

linear:
  tenants:
    test:
      tenant_id: 00000000-0000-488b-81ca-8c90531b1945
      project_url: https://linear.app/layerx-inc/project/test-tenantid-00000000-0000-488b-81ca-8c90531b1945-9424122f2e0c/overview
      aliases:
        - test
        - test-tenant
        - 00000000-0000-488b-81ca-8c90531b1945
```

## Implementation Status

This is still in design/specification. Implementation starts after the remaining HITL flow specs are finalized, beginning with `BAA-1067`.

