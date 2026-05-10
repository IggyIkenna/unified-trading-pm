---
scope: [engineer, admin]
---

# Seamless cloud switch

## Why

Live trading is dual-cloud (GCP + AWS) by 2026-05-23. Operators may need to migrate a running workload from one cloud to
the other — for outage failover, cost rebalancing, or region-availability changes — without losing in-flight state,
dropping orders, or producing cross-cloud reconciliation drift. This doc names the preserved-state semantics that make a
cloud switch boring.

## What must be preserved across the switch

| State                        | Where it lives                               | Migration mechanism                                                     |
| ---------------------------- | -------------------------------------------- | ----------------------------------------------------------------------- |
| Open positions               | position-balance-monitor (per-cloud DB)      | Bidirectional CDC: position table replicates GCP↔AWS continuously      |
| In-flight orders             | execution-service (per-cloud DB)             | Pre-switch drain: stop accepting new orders, finish or cancel in-flight |
| Strategy config + last-state | Firestore + per-strategy snapshot            | Read on warm-up; identical schema both clouds                           |
| Manifest writes              | GCS (per-cloud bucket)                       | Manifest consolidator reads both buckets (writegate Phase 3.D)          |
| Open positions audit log     | unified-events-interface event stream        | Cross-cloud event-stream parity (work-stream B)                         |
| Credentials                  | Secret Manager (GCP) + Secrets Manager (AWS) | Secrets-migration tracker keeps both in sync; never single-cloud-only   |
| ML manifest + artifacts      | GCS                                          | Replicated to both clouds; `job_id` lookups work from either cloud      |

## Switch protocol

1. **Pre-switch** — operator declares the intent in DART; alerting-service raises `CLOUD_SWITCH_PENDING`.
2. **Drain** — execution-service stops accepting new orders, drains in-flight to a safe state (filled or cancelled).
3. **Snapshot** — position-balance-monitor takes a coordinated snapshot keyed by `cloud_switch_id`. Strategy-service
   freezes config changes until post-switch.
4. **Switch** — DNS / load-balancer rotates traffic from old-cloud to new-cloud Cloud Run / VM endpoints. Old-cloud
   services enter `drain` mode and stop emitting new state changes.
5. **Warm-up** — new-cloud services boot, load the snapshot, validate via `validate_cloud_switch_state(snapshot_id)`
   helper, resume operations.
6. **Verify** — on-call inspects DART dashboard: open positions match, no in-flight orders are orphaned, alerting-rule
   coverage is identical.
7. **Decommission** — old-cloud services scale to zero. Snapshot retained for the cross-cloud reconciliation report.

## Anti-patterns

- **No "live in two clouds at once"** — split-brain on order placement is unrecoverable. Drain → snapshot → switch is
  the only safe pattern.
- **No "I'll re-derive state from the manifest"** — the manifest captures data, not in-flight order state.
- **No "skip validation if it's an emergency"** — `validate_cloud_switch_state` raises on schema mismatch. If it raises,
  the switch is blocked; if you want to override, the override path is logged + paged.

## Cross-references

- Cloud-agnostic migration overview: [`cloud-agnostic-migration.md`](cloud-agnostic-migration.md)
- Build lineage (cross-cloud build provenance):
  [`../05-infrastructure/cloud-agnostic-build-lineage.md`](../05-infrastructure/cloud-agnostic-build-lineage.md)
- Cloud-agnostic script pattern:
  [`../05-infrastructure/cloud-agnostic-script-pattern.md`](../05-infrastructure/cloud-agnostic-script-pattern.md)
- Secrets migration tracker:
  [`../11-project-management/secrets-migration-tracking.md`](../11-project-management/secrets-migration-tracking.md)
- Live deployment monitoring (event-stream parity):
  [`../05-infrastructure/live-deployment-monitoring.md`](../05-infrastructure/live-deployment-monitoring.md)
