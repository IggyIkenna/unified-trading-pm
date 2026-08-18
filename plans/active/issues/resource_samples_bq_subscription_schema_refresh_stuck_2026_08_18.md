---
doc_type: issue
title: resource-samples-bq native BigQuery subscription not picking up net_sent_rate_bytes_sec column after 55+ min
status: open
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [observability, bigquery, pubsub, gcp, blocked]
related: [/plans/active/deployment_network_egress_ingress_observability_2026_08_18.md]
created: 2026-08-18
last_updated: 2026-08-18
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
source: [interactive session investigation 2026-08-18]
locked_by:
locked_since:
resolved_by:
summary: >-
  The resource-samples-bq native BigQuery subscription (useTableSchema: true) hasn't picked up the
  net_sent_rate_bytes_sec column added to resource_samples 55+ minutes ago, despite 4 real end-to-end publish
  probes and 2 subscription-config nudges — schema + code path both confirmed correct, only the destination
  table's schema-cache refresh remains unconfirmed.
drift_direction: advance-code
depends_on: []
---

# resource-samples-bq subscription not picking up net_sent_rate_bytes_sec after 55+ min

## What's confirmed working

- `deployment_operational_data.resource_samples` (project `central-element-323112`) has the
  `net_sent_rate_bytes_sec FLOAT` column, added via an additive `ALTER TABLE ... ADD COLUMN` at 2026-08-18
  ~19:07 UTC — confirmed via `bq show`.
- The code path is correct end-to-end: `HostMetricsSample.to_dict()` (unified-trading-library@77ee7cec57) →
  `_vm_resource_sample_payload()` → `PubSubFlatEventPublisher.publish()` → topic `resource-samples` → subscription
  `resource-samples-bq` (`useTableSchema: true`, `dropUnknownFields: true`) → the table. 4 real (non-mocked)
  publishes were sent directly through this exact production pipe with distinct synthetic `deployment_id`s
  (`net-egress-observability-verify-probe-2026-08-18{,b,c,d}`), each carrying a correct
  `net_sent_rate_bytes_sec` value. Every publish's `net_recv_rate_bytes_sec` (a pre-existing column) landed
  correctly and immediately in every case — proving the pipe itself, the subscription's field-name mapping, and
  the publish call are all functioning.
- `net_sent_rate_bytes_sec` specifically stays `null` on all 4 landed rows, ~55 min after the ALTER TABLE and
  after 2 explicit subscription-config nudges (a no-op `--clear-dead-letter-policy` update, then an explicit
  `--bigquery-table=... --use-table-schema --drop-unknown-fields` re-assert) intended to force a schema
  re-fetch — GCP's own documentation describes `useTableSchema` subscriptions detecting a destination-table
  schema change automatically, typically within a few minutes and "up to 15 minutes" in the worst case cited.
  We are well past that window.

## What's NOT yet confirmed

The literal gate on
`/plans/active/deployment_network_egress_ingress_observability_2026_08_18.md` Track 1 Todo 2 — "a live query...
shows non-null `net_sent_rate_bytes_sec` for a currently-heartbeating deployment" — remains unmet. The todo is
left `- [ ]` (not falsely checked off) pending this.

## The one remaining untried lever — deliberately not taken without a check-in

Deleting and recreating the `resource-samples-bq` subscription would force a fresh schema fetch at creation
time (this is the same mechanism that worked correctly when the subscription was originally created against
the table's then-current schema). This is very likely to fix it immediately. It was **not** done in this
session because:

- It's a live production subscription that every currently-heartbeating deployment-service VM publishes
  `resource_samples` telemetry through continuously (~every 60s per VM, `HEARTBEAT_INTERVAL_SEC`).
- The topic itself retains messages independently of subscriptions (`topicMessageRetentionDuration: 259200s`),
  but a subscription only receives messages published *after* its own creation by default — so a brief
  delete→recreate window (expected: seconds) would drop any `resource_samples` events published in that
  window. Practically low-stakes (self-healing on the next ~60s tick, and this is a monitoring signal, not a
  transactional record) but it's a materially bigger action than anything else this session took (ALTER TABLE
  ADD COLUMN, synthetic test publishes, and additive VPC Flow Log enablement are all either fully additive or
  fully isolated from the live data path — this one briefly touches it).

## Recommended resolution

1. **First**, just check again — if enough real elapsed time (a few hours) has passed and it's still null,
   the auto-refresh genuinely isn't going to happen on its own.
2. If still stuck: delete + recreate `resource-samples-bq` with the same config
   (`--topic=resource-samples --table=central-element-323112:deployment_operational_data.resource_samples
   --use-table-schema --drop-unknown-fields`). Verify immediately after with one more synthetic probe publish +
   query.
3. Once confirmed, flip Track 1 Todo 2's checkbox with the query result as evidence, delete the 4 probe rows
   (`DELETE FROM deployment_operational_data.resource_samples WHERE deployment_id LIKE
   'net-egress-observability-verify-probe-2026-08-18%'`), and archive/resolve this issue doc.
