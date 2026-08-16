---
doc_type: issue
title: RECON_FREEZE_ARMED is never published — reconciliation→order-block safety chain is dormant
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-27
source: [execution-service/execution_service/preflight/recon_freeze.py, alerting-service/alerting_service/rules/reconciliation_rules.py, unified-trading-pm/codex/04-architecture/reconciliation-age-tracking.md, unified-trading-pm/plans/archive/2026_08/issues/batch_live_reconciliation_service_audit_2026_05_27.md]
locked_by: live-defi-rollout
severity: P0-safety (live-trading critical path)
routed_to: ikenna-main (cross-repo trading-safety decision)
priority: P2
---

# RECON_FREEZE_ARMED never published — recon→order-block chain is dormant

> **ARCHIVED 2026-06-01 (slot 7).** The G12 decision is dispatched (issue-doc-lifecycle: acked → archive): the
> alerting-service recon-freeze publisher is a **P0 todo in `observability_master`** (per-incident-type granularity:
> symbol-scoped for symbol breaks, account-wide for account-level SEV0s) + the **execution-side per-incident emit is a
> P1 todo in `execution_master`**. In-scope for May-23. Operator decision ledger preserved below for provenance.

> **🟦 OPERATOR DECISION LEDGER — 2026-06-01 (Ikenna, recorded slot-1).** FINAL ruling on the routed G12 decision:
>
> - **In-scope for May-23** — the recon-freeze publisher lands pre-cutover. The 7 immediate-SEV0 conditions are NOT
>   covered by the `position_drift_monitor` kill-switch, so deferring would ship cutover with a live-safety gap.
> - **Per-incident-type granularity** — symbol-scoped freeze for symbol-level breaks; **account-wide** for the
>   account-level SEV0s (e.g. `UNKNOWN_NET_EXPOSURE`, `ACCOUNT_LEVEL_AGGREGATE`).
> - **Execution**: record as a P0 todo in `observability_master` + `execution_master`. Slot 7 wires the alerting-service
>   publisher (`evaluate_recon_age()==CRITICAL` || `evaluate_immediate_sev0()==True` → publish `RECON_FREEZE_ARMED` /
>   `RECON_FREEZE_LIFTED` + synthetic test) only if it can land it cleanly + QG-green; otherwise the todo carries to the
>   owning epic VM. Not manifest/CI-CD work — safe for slot 7.

> Surfaced during the BLRS audit (G12). Not BLRS-owned — this is an alerting-service ↔ execution-service gap.

## What I found

The reconciliation-freeze safety chain is fully built on both ends but **has no trigger**:

- **Subscriber side (built):** `execution-service/execution_service/preflight/recon_freeze.py` — `ReconFreezeChecker`
  with `arm()` / `assert_not_frozen()` / `lift()`. Every order submission calls `assert_not_frozen()` and is rejected
  with `ReconFreezeError` for any `(strategy, venue, symbol)` in the in-memory freeze set. Lift is HUMAN-ONLY. Shipped
  execution-service@d649af364.
- **Detection side (built):** `alerting-service/alerting_service/rules/reconciliation_rules.py` — `evaluate_recon_age()`
  (3-band ladder: 5/15/30 min) + `evaluate_immediate_sev0()` (7 overrides). Shipped alerting-service@9c47947.
- **The missing link:** codex `reconciliation-age-tracking.md` § "Reconciliation Freeze" states that on
  `recon_age_critical_seconds` breach OR any immediate-SEV0, **alerting-service publishes `RECON_FREEZE_ARMED` to PubSub
  topic `reconciliation-freeze`**. **No code anywhere publishes that event.** Verified via `rg "RECON_FREEZE_ARMED"`
  across alerting-service (and the workspace) — only the subscriber + the codex/docs reference it; there is no
  publisher.

Result: critical recon-age and the 7 immediate-SEV0 overrides currently route to **PagerDuty/Telegram alerts only**. The
freeze set is never populated, so `assert_not_frozen()` never blocks an order on reconciliation grounds.

## Why it matters

This is the documented mechanism that **halts new trading when reconciliation risk is live** (e.g.
`UNKNOWN_NET_EXPOSURE`, `OPEN_ORDERS_UNCONFIRMABLE`, `VENUE_INTERNAL_BALANCE_MISMATCH`). With no publisher, an operator
seeing a SEV0 recon incident has alerts but the system keeps accepting orders for the affected (strategy, venue, symbol)
until a human manually intervenes. On the May-23 live path this is a real safety hole.

Partial mitigation that DOES exist: `strategy-service/position/core/position_drift_monitor.py` independently fires
`KILL_SWITCH_ACTIVATED` (STOP*NEW_ONLY) on CRITICAL equity/delta drift — so there is \_a* live reflex, but it is
drift-based, not the recon-age / 7-SEV0-override freeze the codex specifies, and it does not cover the immediate-SEV0
conditions (e.g. open-orders-unconfirmable, balance-movement-unexplained).

## Recommended decision

Wire the publisher in **alerting-service**: when `evaluate_recon_age()` returns CRITICAL OR `evaluate_immediate_sev0()`
returns any True override, publish `RECON_FREEZE_ARMED` to the `reconciliation-freeze` PubSub topic with the affected
`(strategy_id, venue, instrument)` scope, so the existing execution-service subscriber arms within 5s. Add the symmetric
`RECON_FREEZE_LIFTED` publish on operator unfreeze. Then add the per-incident synthetic test the codex already names
("assert recon-freeze armed within 5s of SEV0 fire").

Open sub-questions for Ikenna:

1. Scope granularity of the freeze (per `(strategy, venue, symbol)` vs per-venue vs per-account) for each of the 7
   immediate-SEV0 overrides — some (e.g. `UNKNOWN_NET_EXPOSURE`, `ACCOUNT_LEVEL_AGGREGATE`) are account-wide, not
   symbol-scoped.
2. Is this in May-23 scope, or does `position_drift_monitor`'s kill-switch cover enough for cutover with the full
   recon-freeze publisher landing post-cutover? (Recommend: in-scope — the 7 SEV0 overrides are not covered by the drift
   kill-switch.)

## Owner / next step

Routed to **ikenna-main** via `plans/active/_agent_pings.md` (cross-repo alerting-service + execution-service +
trading-safety governance). Tracked as G12 in the BLRS audit.
