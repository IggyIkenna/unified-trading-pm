---
doc_type: plan
title: uei-pending-event-additions
summary: Consolidated batch PR for all pending unified-events-interface/schemas.py additions from 3 source plans to avoid
  merge conflicts.
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-11'
type: code
epic: epic-code-completion
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-events-interface, code: C4, deployment: none, business: none, readiness_note: 'DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off required for a code plan.'}
depends_on: [data_availability_live_expectations_2026_03_10, recon_rebalancing_order_recovery_2026_03_10, position_precision_pnl_hardening_2026_03_11]
todos:
- {id: uei-data-freshness-events, content: 'Add 5 data freshness events from data_availability_live_expectations_2026_03_10.md Phase 2: DATA_STALE, DATA_AVAILABILITY_RESTORED, DATA_GAP_DETECTED, FEED_UNHEALTHY, DATA_COMPLETENESS_CHECK. Payload schema for DATA_STALE/FEED_UNHEALTHY: source, age_seconds, max_age_seconds, asset_group, criticality, timestamp.', status: done, note: DONE 2026-03-11 — all 5 events in schemas.py}
- {id: uei-recon-rebalancing-events, content: 'Add 8 reconciliation/rebalancing events from recon_rebalancing_order_recovery_2026_03_10.md Stream A+B+C+D: POSITION_CORRECTION_DISPATCHED, POSITION_CORRECTION_FAILED, ORDER_RECOVERY_INITIATED, ORDER_RECOVERY_COMPLETED, ORDER_RECOVERY_FAILED, PORTFOLIO_REBALANCE_TRIGGERED, PORTFOLIO_REBALANCE_COMPLETED, DEFI_VAULT_REBALANCED.', status: done, note: DONE 2026-03-11 — all 8 events in schemas.py}
- {id: uei-pnl-residual-event, content: 'Add 1 P&L attribution event from position_precision_pnl_hardening_2026_03_11.md Phase E: UNEXPLAINED_PNL_RESIDUAL — emitted hourly + AlertEvent when > 2% of total PnL.', status: done, note: DONE 2026-03-11 — UNEXPLAINED_PNL_RESIDUAL in schemas.py}
- {id: uei-batch-pr, content: 'Batch all 14 events above into a single PR on unified-events-interface. Run quality-gates.sh. Update all source plans to reference this plan''s todo IDs instead of tracking individually. After merge, cascade version bump to all dependent repos (UMI, UTEI, UPI, URDI, strategy-service, execution-service, alerting-service, position-balance-monitor-service).', status: done, note: 'DONE 2026-03-11 — all 14 events committed, ORDER_RECOVERY_INITIATED was the last missing one'}
isProject: false
---

# UEI Pending Event Additions (Consolidated)

**Created:** 2026-03-11 **Status:** PENDING **Priority:** P0 (blocks multiple active plans)

## Purpose

`unified-events-interface/schemas.py` is a single file modified by multiple concurrent plans. Adding events in separate
PRs causes merge conflicts. This plan consolidates all pending additions into one coordinated batch.

---

## Event Inventory

### From `data_availability_live_expectations_2026_03_10`

| Event                        | Trigger                                    |
| ---------------------------- | ------------------------------------------ |
| `DATA_STALE`                 | Warn threshold breached (warn_age_seconds) |
| `DATA_AVAILABILITY_RESTORED` | Feed recovers after stale/unhealthy        |
| `DATA_GAP_DETECTED`          | Gap in time series detected                |
| `FEED_UNHEALTHY`             | Max threshold breached (max_age_seconds)   |
| `DATA_COMPLETENESS_CHECK`    | Scheduled daily completeness report        |

### From `recon_rebalancing_order_recovery_2026_03_10`

| Event                            | Trigger                                       |
| -------------------------------- | --------------------------------------------- |
| `POSITION_CORRECTION_DISPATCHED` | CorrectionDispatcher submits correction order |
| `POSITION_CORRECTION_FAILED`     | Correction order execution fails              |
| `ORDER_RECOVERY_INITIATED`       | Startup recon begins open order recovery      |
| `ORDER_RECOVERY_COMPLETED`       | Open order recovery completes                 |
| `ORDER_RECOVERY_FAILED`          | Open order recovery fails                     |
| `PORTFOLIO_REBALANCE_TRIGGERED`  | Drift threshold exceeded                      |
| `PORTFOLIO_REBALANCE_COMPLETED`  | Rebalancing completes                         |
| `DEFI_VAULT_REBALANCED`          | DeFi vault yield rebalance completes          |

### From `position_precision_pnl_hardening_2026_03_11`

| Event                      | Trigger                                                           |
| -------------------------- | ----------------------------------------------------------------- |
| `UNEXPLAINED_PNL_RESIDUAL` | Hourly when unexplained PnL residual exists; AlertEvent when > 2% |

---

## Implementation

All 14 events added to `unified_events_interface/schemas.py` `EventType` enum in one commit.

```python
# data freshness
DATA_STALE = "DATA_STALE"
DATA_AVAILABILITY_RESTORED = "DATA_AVAILABILITY_RESTORED"
DATA_GAP_DETECTED = "DATA_GAP_DETECTED"
FEED_UNHEALTHY = "FEED_UNHEALTHY"
DATA_COMPLETENESS_CHECK = "DATA_COMPLETENESS_CHECK"

# reconciliation / rebalancing
POSITION_CORRECTION_DISPATCHED = "POSITION_CORRECTION_DISPATCHED"
POSITION_CORRECTION_FAILED = "POSITION_CORRECTION_FAILED"
ORDER_RECOVERY_INITIATED = "ORDER_RECOVERY_INITIATED"
ORDER_RECOVERY_COMPLETED = "ORDER_RECOVERY_COMPLETED"
ORDER_RECOVERY_FAILED = "ORDER_RECOVERY_FAILED"
PORTFOLIO_REBALANCE_TRIGGERED = "PORTFOLIO_REBALANCE_TRIGGERED"
PORTFOLIO_REBALANCE_COMPLETED = "PORTFOLIO_REBALANCE_COMPLETED"
DEFI_VAULT_REBALANCED = "DEFI_VAULT_REBALANCED"

# P&L attribution
UNEXPLAINED_PNL_RESIDUAL = "UNEXPLAINED_PNL_RESIDUAL"
```

---

## Dependencies

- `data_availability_live_expectations_2026_03_10.md` Phase 2 — waits on this plan
- `recon_rebalancing_order_recovery_2026_03_10.md` Stream A/B/C/D — waits on this plan
- `position_precision_pnl_hardening_2026_03_11.md` Phase E — waits on this plan
- `strategy_visibility_grafana_2026_03_10.md` — needs DEFI_VAULT_REBALANCED from this plan
