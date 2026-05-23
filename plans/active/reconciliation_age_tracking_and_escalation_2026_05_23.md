---
title: "Reconciliation Age Tracking + 15/30-min Escalation + 7 Immediate-SEV0 Overrides"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
status: active
estimate_class: refactor
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 4.0
estimate_calibration_note: |
  Refactor class — `batch-live-reconciliation-service/` exists; this plan adds age fields, 12-dimension separation,
  thresholds, immediate-overrides, and freeze-on-recon-risk. Baseline 10 days × 0.4 refactor = 4 cal-days. Existing
  recon logic stays; only the around-the-edges work changes.
parent: master_to_live_defi_2026_05_23
locked_by: live-defi-rollout
locked_since: 2026-05-23
depends_on:
  - incident_gateway_and_state_machine_2026_05_23 # emits IncidentEnvelope when recon age breaches thresholds
gates:
  - master_to_live_defi_2026_05_23:Group-F
related_plans:
  - incident_gateway_and_state_machine_2026_05_23.md
  - drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md
---

# Reconciliation Age Tracking + 15/30-min Escalation + 7 Immediate-SEV0 Overrides

> **🟢 SPAWNED 2026-05-23 from `observability_disaster_recovery_audit_2026_05_23.md` gap #4.** Closes §7 of the target
> model. **`batch-live-reconciliation-service` is co-owned**; coordinate edits per CLAUDE.md "Two teammates" rule.

## Goal

Make every reconciliation breach **age-tracked**, **dimensioned**, and **escalated by elapsed time**. The system must:

1. Track 12 reconciliation dimensions separately (orders, fills, positions, balances, funding, fees, transfers,
   borrow/lending, collateral, margin-mode+leverage, strategy-allocation, account-aggregate).
2. Stamp `first_seen_at` / `last_seen_at` / `event_time` / `venue_trade_time` / `internal_trade_time` /
   `last_successful_reconciliation_at` / `unreconciled_age_seconds` /
   `oldest_unreconciled_{trade,order,position}_age_seconds` on every reconciliation row.
3. Escalate by age: 0-5min internal warning; 5-15min Slack warning + agent investigation; >15min SEV1 (human
   investigation); >30min OR any of 7 immediate-overrides → SEV0.
4. Codify the 7 closed-set immediate-SEV0 overrides per `disaster_recovery.md` §7.5.
5. Freeze new trading for affected scope when recon risk is live.

## Context

**Existing capability** (verified 2026-05-23):

- `batch-live-reconciliation-service/` exists with reconciliation logic.
- `alerting-service/alerting_service/rules/reconciliation_rules.py` exists.
- UAC `internal/reconciliation.py` has reconciliation types.
- `position-balance-monitor-service/` has reconciliation engine + fee reconciliation engine.

**Missing for May-23**:

- No age fields on reconciliation rows.
- No 12-dimension separation (current is 2-3 dimensions).
- No escalation thresholds wired to alerting.
- No immediate-SEV0 overrides codified.
- No freeze-on-recon-risk for (strategy, venue, symbol) scope.

## Pre-audit (blast radius)

- TOUCH: `unified_api_contracts/internal/reconciliation.py` — add `ReconciliationDimension` StrEnum + age fields on
  reconciliation row schemas.
- TOUCH: `batch-live-reconciliation-service/` reconciliation engine — populate age fields + dimension tag.
- TOUCH: `position-balance-monitor-service/reconciliation_engine.py` + `fee_reconciliation_engine.py` — same.
- TOUCH: `alerting-service/alerting_service/rules/reconciliation_rules.py` — wire 15/30-min thresholds + 7 immediate
  overrides.
- NEW: `execution-service/execution_service/preflight/recon_freeze.py` — preflight check that blocks new order
  submission for (strategy, venue, symbol) scope when reconciliation risk is live.

## Phased execution DAG

### Phase 1 — UAC schema additions (0.5 cal-day)

- [ ] [SCRIPT] P0.1. `ReconciliationDimension` StrEnum in `unified_api_contracts/internal/reconciliation.py`. 12
      members: ORDERS, FILLS, POSITIONS, BALANCES, FUNDING_PAYMENTS, FEES, TRANSFERS, BORROW_LENDING_BALANCES,
      COLLATERAL_BALANCES, MARGIN_MODE_AND_LEVERAGE, STRATEGY_LEVEL_ALLOCATION, ACCOUNT_LEVEL_AGGREGATE.
- [ ] [SCRIPT] P0.2. `ReconciliationAgeFields` mixin (Pydantic) — `first_seen_at`, `last_seen_at`, `event_time`,
      `venue_trade_time`, `internal_trade_time`, `last_successful_reconciliation_at`, `unreconciled_age_seconds`,
      `oldest_unreconciled_trade_age_seconds`, `oldest_unreconciled_order_age_seconds`,
      `oldest_unreconciled_position_age_seconds`. All tz-aware UTC datetimes; ages computed at row-write-time, not
      query-time.
- [ ] [SCRIPT] P0.3. Apply mixin to all existing reconciliation row models (`ReconciliationDelta`,
      `OrderReconciliationDelta`, `PositionReconciliationDelta`, `BalanceReconciliationDelta`, etc).

### Phase 2 — Engine populates fields (1 cal-day)

- [ ] [AGENT] P0.4. `batch-live-reconciliation-service/` reconciliation engine sets all age fields on row creation. Use
      UTL `utc_now()` consistently — never naive datetime.
- [ ] [AGENT] P0.5. `position-balance-monitor-service/reconciliation_engine.py` + `fee_reconciliation_engine.py` same.
- [ ] [AGENT] P0.6. Per-dimension subgraph: dimension-specific reconciler emits rows tagged with the right
      `ReconciliationDimension`. 12 distinct sub-engines (existing 2-3 grow to 12; new ones may share infra but emit
      distinct dimensions).

### Phase 3 — Escalation thresholds (1 cal-day)

- [ ] [SCRIPT] P0.7. `alerting-service/alerting_service/rules/reconciliation_rules.py` adds threshold ladder:
      `recon_age_warn_seconds=300` (5min Slack), `recon_age_investigate_seconds=900` (15min SEV1),
      `recon_age_critical_seconds=1800` (30min SEV0). Values in UAC `ALERT_THRESHOLDS` registry per existing pattern.
- [ ] [SCRIPT] P0.8. Per-(venue, strategy, instrument_type, account) overrides via UAC `per_archetype_overrides` — match
      existing AlertThreshold pattern.
- [ ] [SCRIPT] P0.9. Wire rule into `LIVE_ALERT_RULES`: pattern `RECONCILIATION_AGE_*` → SEV escalates by age band.

### Phase 4 — 7 immediate-SEV0 overrides (0.5 cal-day)

- [ ] [AGENT] P0.10. `alerting-service/alerting_service/rules/reconciliation_rules.py` — `evaluate_immediate_sev0(row)`
      function checks 7 closed-set predicates per `ImmediateSev0Override` enum from
      `incident_gateway_and_state_machine_2026_05_23`: - UNKNOWN_NET_EXPOSURE — venue total ≠ internal total + no
      explanation row in transfers/funding. - OPEN_ORDERS_UNCONFIRMABLE — venue REST returns 5xx + we have N open orders
      in internal. - KILL_SWITCH_CANNOT_CONFIRM_CANCEL — kill_switch.activate() ran but cancel-all-orders for venue
      returned partial. - VENUE_INTERNAL_BALANCE_MISMATCH — abs(venue - internal) > USD threshold (configurable per
      asset, default $1000). - POSITION_EXISTS_EXTERNALLY_UNKNOWN_INTERNALLY — venue returns position we have no
      internal record of. - MATERIAL_BALANCE_MOVEMENT_UNEXPLAINED — balance moved > USD threshold + no
      transfer/fill/funding row. - MARGIN_COLLATERAL_SAFETY_UNCERTAIN — venue API can't confirm margin state OR
      ADL/insurance-fund signal.
- [ ] [TEST] P0.11. 7 unit tests in `alerting-service/tests/unit/rules/test_immediate_sev0_overrides.py` — one per
      predicate.

### Phase 5 — Freeze-on-recon-risk (0.5 cal-day)

- [ ] [SCRIPT] P0.12. `execution-service/execution_service/preflight/recon_freeze.py` — preflight check invoked before
      every order submission. Reads `batch-live-reconciliation-service` API for current freeze set; rejects orders for
      (strategy, venue, symbol) tuples in the freeze set.
- [ ] [SCRIPT] P0.13. Freeze set publisher: when `recon_age_critical_seconds` breaches OR any immediate-SEV0 fires,
      alerting-service publishes `RECON_FREEZE_ARMED` event to PubSub topic `reconciliation-freeze`. Execution-service
      subscribes and updates in-memory freeze set within 5s.
- [ ] [SCRIPT] P0.14. Unfreeze path: human-only — operator clicks "Unfreeze" in DART after acknowledging incident and
      verifying recon delta resolved. Emits `RECON_FREEZE_LIFTED` event.

### Phase 6 — Smoke + game-day (0.5 cal-day, GATES May-23)

- [ ] [HUMAN] P0.15. Synthetic smoke: inject a position-recon delta with `first_seen_at` = now-20min → assert SEV1
      fires; bump to now-40min → assert SEV0 fires + freeze set armed; submit a synthetic order → assert preflight
      rejects.
- [ ] [HUMAN] P0.16. Game-day: scenario `11_handshake_integration.md` — assert age fields populate; recon-recovery
      events fire when oldest_unreconciled_age decreases below threshold.

## Success criteria

- 12 ReconciliationDimension enum members + all reconciliation rows tagged.
- All age fields populated by reconciliation engine.
- 15/30-min escalation thresholds wired in alerting.
- 7 immediate-SEV0 overrides codified + unit-tested.
- Freeze-on-recon-risk blocks new orders within 5s.
- Smoke + game-day green.

## Anti-patterns + banned approaches

- ❌ Computing `unreconciled_age_seconds` at query time — must be persisted at write time per CLAUDE.md
  `available_at`-style rule.
- ❌ Single global `recon_age` threshold — must be per-venue / per-strategy configurable.
- ❌ Auto-unfreeze on age decrease — unfreeze is HUMAN-ONLY (recon-recovery doesn't mean trading is safe to resume).

## Continuous verification

- Daily: `python3 batch-live-reconciliation-service/scripts/check_oldest_age.py` returns max(age) < 30min in healthy
  state.
- Per-incident: assert recon-freeze armed within 5s of SEV0 fire (synthetic test runs nightly).

## Cross-plan blockers

**Blocked by**: `incident_gateway_and_state_machine_2026_05_23` Phase 1 (ImmediateSev0Override enum).

**Blocks** (downstream): `audit_acknowledgement_sla_and_state_2026_05_23` (freeze-lifted requires audit ack).

## Codex SSOT updates

- UPDATE: `codex/04-architecture/autonomous-recovery-matrix.md` — extend "RECONCILIATION FAILURE" section with age-band
  escalation ladder.
- NEW codex stub: `codex/04-architecture/reconciliation-age-tracking.md` — 12 dimensions, age fields, thresholds, 7
  immediate-overrides.
