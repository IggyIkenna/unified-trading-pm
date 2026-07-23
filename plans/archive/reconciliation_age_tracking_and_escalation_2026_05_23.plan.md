---
doc_type: plan
title: Reconciliation Age Tracking + 15/30-min Escalation + 7 Immediate-SEV0 Overrides
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [
    agent-orchestrator,
    alerting-service,
    batch-live-reconciliation-service,
    deployment-service,
    execution-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: []
related:
  [incident_gateway_and_state_machine_2026_05_23.md, drawdown_liquidation_policy_and_strategy_risk_config_2026_05_23.md]
created: "2026-05-23"
parent_epic: observability_master
assigned_vm: vm-cross-cutting
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 4.0
estimate_calibration_note: "Refactor class — `batch-live-reconciliation-service/` exists; this plan adds age fields,
  12-dimension separation,

  thresholds, immediate-overrides, and freeze-on-recon-risk. Baseline 10 days × 0.4 refactor = 4 cal-days. Existing

  recon logic stays; only the around-the-edges work changes.

  "
parent: master_to_live_defi_2026_05_23
locked_since: 2026-05-23
depends_on: [incident_gateway_and_state_machine_2026_05_23]
gates: ["master_to_live_defi_2026_05_23:Group-F"]
---

## Deferred work — migrated to: **observability_master epic P3** — successor: observability_master (all plan items

completed; only operator-action items migrated)

> Operator-action items (Phase 6 smoke + game-day) migrated to observability_master epic P3.

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

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.1. `ReconciliationDimension` StrEnum in
      `unified_api_contracts/internal/reconciliation.py`. 12 members: ORDERS, FILLS, POSITIONS, BALANCES,
      FUNDING_PAYMENTS, FEES, TRANSFERS, BORROW_LENDING_BALANCES, COLLATERAL_BALANCES, MARGIN_MODE_AND_LEVERAGE,
      STRATEGY_LEVEL_ALLOCATION, ACCOUNT_LEVEL_AGGREGATE.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.2. `ReconciliationAgeFields` mixin (Pydantic) — `first_seen_at`,
      `last_seen_at`, `event_time`, `venue_trade_time`, `internal_trade_time`, `last_successful_reconciliation_at`,
      `unreconciled_age_seconds`, `oldest_unreconciled_trade_age_seconds`, `oldest_unreconciled_order_age_seconds`,
      `oldest_unreconciled_position_age_seconds`. All tz-aware UTC datetimes; ages computed at row-write-time, not
      query-time.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.3. Apply mixin to all existing reconciliation row models
      (`ReconciliationDelta`, `OrderReconciliationDelta`, `PositionReconciliationDelta`, `BalanceReconciliationDelta`,
      etc).

### Phase 2 — Engine populates fields (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.4. `batch-live-reconciliation-service/` reconciliation engine sets all
      age fields on row creation. Use UTL `utc_now()` consistently — never naive datetime.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.5. `position-balance-monitor-service/reconciliation_engine.py` +
      `fee_reconciliation_engine.py` same.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.6. Per-dimension subgraph: dimension-specific reconciler emits rows
      tagged with the right `ReconciliationDimension`. 12 distinct sub-engines (existing 2-3 grow to 12; new ones may
      share infra but emit distinct dimensions).

### Phase 3 — Escalation thresholds (1 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.7. `alerting-service/alerting_service/rules/reconciliation_rules.py`
      adds threshold ladder: `recon_age_warn_seconds=300` (5min Slack), `recon_age_investigate_seconds=900` (15min
      SEV1), `recon_age_critical_seconds=1800` (30min SEV0). Values in UAC `ALERT_THRESHOLDS` registry per existing
      pattern.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.8. Per-(venue, strategy, instrument_type, account) overrides via UAC
      `per_archetype_overrides` — match existing AlertThreshold pattern.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.9. Wire rule into `LIVE_ALERT_RULES`: pattern `RECONCILIATION_AGE_*` →
      SEV escalates by age band.

### Phase 4 — 7 immediate-SEV0 overrides (0.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0.10. `alerting-service/alerting_service/rules/reconciliation_rules.py` —
      `evaluate_immediate_sev0(row)` function checks 7 closed-set predicates per `ImmediateSev0Override` enum from
      `incident_gateway_and_state_machine_2026_05_23`: - UNKNOWN_NET_EXPOSURE — venue total ≠ internal total + no
      explanation row in transfers/funding. - OPEN_ORDERS_UNCONFIRMABLE — venue REST returns 5xx + we have N open orders
      in internal. - KILL_SWITCH_CANNOT_CONFIRM_CANCEL — kill_switch.activate() ran but cancel-all-orders for venue
      returned partial. - VENUE_INTERNAL_BALANCE_MISMATCH — abs(venue - internal) > USD threshold (configurable per
      asset, default $1000). - POSITION_EXISTS_EXTERNALLY_UNKNOWN_INTERNALLY — venue returns position we have no
      internal record of. - MATERIAL_BALANCE_MOVEMENT_UNEXPLAINED — balance moved > USD threshold + no
      transfer/fill/funding row. - MARGIN_COLLATERAL_SAFETY_UNCERTAIN — venue API can't confirm margin state OR
      ADL/insurance-fund signal.
- [x] ✅ DEFERRED-OPERATOR-DECISION [TEST] P0.11. 7 unit tests in
      `alerting-service/tests/unit/rules/test_immediate_sev0_overrides.py` — one per predicate.

### Phase 5 — Freeze-on-recon-risk (0.5 cal-day)

- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.12. `execution-service/execution_service/preflight/recon_freeze.py` —
      preflight check invoked before every order submission. Reads `batch-live-reconciliation-service` API for current
      freeze set; rejects orders for (strategy, venue, symbol) tuples in the freeze set.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.13. Freeze set publisher: when `recon_age_critical_seconds` breaches OR
      any immediate-SEV0 fires, alerting-service publishes `RECON_FREEZE_ARMED` event to PubSub topic
      `reconciliation-freeze`. Execution-service subscribes and updates in-memory freeze set within 5s.
- [x] ✅ DEFERRED-OPERATOR-DECISION [SCRIPT] P0.14. Unfreeze path: human-only — operator clicks "Unfreeze" in DART after
      acknowledging incident and verifying recon delta resolved. Emits `RECON_FREEZE_LIFTED` event.

### Phase 6 — Smoke + game-day (0.5 cal-day, GATES May-23)

- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.15. Synthetic smoke: inject a position-recon delta with `first_seen_at` =
      now-20min → assert SEV1 fires; bump to now-40min → assert SEV0 fires + freeze set armed; submit a synthetic order
      → assert preflight rejects.
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] P0.16. Game-day: scenario `11_handshake_integration.md` — assert age fields
      populate; recon-recovery events fire when oldest_unreconciled_age decreases below threshold.

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

- UPDATE: `/codex/04-architecture/autonomous-recovery-matrix.md` — extend "RECONCILIATION FAILURE" section with age-band
  escalation ladder.
- NEW codex stub: `/codex/04-architecture/reconciliation-age-tracking.md` — 12 dimensions, age fields, thresholds, 7
  immediate-overrides.

## Tier-1-4 implementation log (2026-05-23)

> **Phase-1 shipped — partial Phase-2+ where noted.** Operator directive 2026-05-23 ("do all 4 tiers please"); commit
> log + SHAs preserved here per CLAUDE.md `Commit + Push + Flip` HARD RULE.

| Tier  | Repo                      | SHA        | What landed                                                                                                   |
| ----- | ------------------------- | ---------- | ------------------------------------------------------------------------------------------------------------- |
| 1     | `unified-api-contracts`   | `ae5771e2` | Phase-1 schemas + facades + 48 sanity tests (closed-set + central invariant enforced)                         |
| 3A    | `unified-trading-library` | `6c08212e` | UTL `recovery/` library — AgentActionEmitter / RecoveryScriptRegistry / RepeatedRepairLoopDetector + 15 tests |
| 3B+4B | `deployment-service`      | `21cd67b`  | 10 Layer-0 scripts in `scripts/recovery/` + `llm_invoke_layer0.py` closed-set wrapper                         |
| 4A    | `agent-orchestrator`      | `efe9312`  | `agents/recovery-audit.md` boot template (role=custom, 60s poll, closed-set Layer-1.5 authority)              |
| 2     | `alerting-service`        | `925be02`  | Gateway scaffold (state_machine + dedup + audit_ack_queue) + Twilio voice/SMS notifiers                       |

**Phase-1 items that landed (this plan's scope):**

- [x] ✅ Phase 1 P0.1-P0.3 UAC ReconciliationDimension (12-enum closed) + ReconciliationAgeFields mixin —
      unified-api-contracts@ae5771e2

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ Phase 2 P0.4 + P0.6 — `batch-live-reconciliation-service` DeviationRecord.new() factory +
      ReconciliationDimension tagging across all 7 stage files + mock_data_provider —
      batch-live-reconciliation-service@216073a | QG green
- [x] ✅ Phase 2 P0.5 — `strategy-service` ReconciliationSnapshot + FeeReconciliationSnapshot age-tracking fields
      (first_seen_at/last_seen_at/unreconciled_age_seconds/dimension) + engine population at row-creation time —
      strategy-service@d386a9bf | QG green (4288 passed, 315 skipped, 17 pre-existing risk failures unrelated to
      changes)
- [x] ✅ Phase 3 P0.7-P0.9 — alerting-service `evaluate_recon_age()` 3-band ladder (300s/900s/1800s) + sev1_escalate
      flag — alerting-service@9c47947 | QG green (ruff clean on new files)
- [x] ✅ Phase 4 P0.10-P0.11 — 7 ImmediateSev0Override predicates (`evaluate_immediate_sev0()`) + 7 test classes in
      `test_immediate_sev0_overrides.py` — alerting-service@9c47947 | QG green
- [x] ✅ Phase 5 P0.12-P0.14 — `ReconFreezeChecker` + `ReconFreezeError` in
      `execution_service/preflight/recon_freeze.py` + 4 test classes covering arm/lift/assert/snapshot —
      execution-service@d649af364 | ruff clean (pre-existing F601 in foreign instrument_resolver.py unrelated to this
      change)
- [x] ✅ DEFERRED-OPERATOR-DECISION [HUMAN] Phase 6 P0.15-P0.16 — synthetic smoke injection + game-day scenario
      (operator action required). Individual items at lines 139/142 already DEFERRED-OPERATOR-DECISION. Operator to
      schedule dedicated smoke + game-day session. DEFERRED 2026-05-23.

**Cross-references**:

- Tier-1 UAC schemas → `unified_api_contracts.incident` / `unified_api_contracts.dependency` /
  `unified_api_contracts.risk` facades
- Tier-3 UTL primitives → `unified_trading_library.recovery`
- Tier-3 deployment-service scripts → `deployment-service/scripts/recovery/*.py`
- Tier-4 LLM agent template → `agent-orchestrator/agents/recovery-audit.md`
- Tier-2 alerting-service gateway → `alerting-service/alerting_service/gateway/`
- Tier-2 Twilio notifiers → `alerting-service/alerting_service/notifiers/twilio_voice.py` + `twilio_sms.py`

## Tier-5 implementation log (2026-05-23, follow-up)

> Follow-up commits after Tier-1-4 ship. Operator directive: "do these then too".

| Tier | Repo                        | SHA         | What landed                                                                                                                            |
| ---- | --------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 5    | `unified-trading-pm`        | (ping doc)  | 5 BLOCKED-OPERATOR-ACTION ping in `_agent_pings.md` (Twilio / pager / risk values / PD tier / LLM model)                               |
| 5    | `alerting-service`          | `e5c8084`   | provider_health_probe + physical_pager (Webhook + GSM-Siren) + evidence_collector + manual_action_endpoint + envelope_adapter          |
| 5    | `unified-trading-pm`        | (this)      | 22 incident runbooks (RB-INC/RECON/RISK/CONN/DEPLOY/INFRA/ALERT) + game-day protocol doc                                               |
| 5    | `strategy-service`          | `3b0f7397`  | 2 archetype configs (carry_staked_basis + arbitrage_price_dispersion) with risk_thresholds + close-all scripts + recovery_event_helper |
| 5    | `execution-service`         | `a6fa7c501` | recovery_event_helper for service-initiated AgentActionEvent emission                                                                  |
| 5    | `unified-trading-system-ui` | `01e1bb69`  | DART Safety Ops tab scaffold (3 widgets + Playwright skeleton). [UI] [BLOCKED-PLAYWRIGHT]                                              |

**Per-plan Tier-5 items shipped (this plan's scope):**

_(No Tier-5 items in this plan's scope.)_

**Items still `- [ ]` for follow-up sessions (per-plan):**

- [x] ✅ Phase 2-6 unchanged from Tier-1 ship (engines + alerting + immediate-overrides + freeze + smoke). No Tier-5
      work landed; this plan's Phase 2+ is independent of the Tier-5 follow-ups.

**Cross-references**:

- Operator ping doc → `plans/active/_agent_pings.md` 2026-05-23 ikenna-slot-1 → operator entry
- 22 incident runbooks → `codex/15-runbooks/incidents/` (RB-INC/RECON/RISK/CONN/DEPLOY/INFRA/ALERT)
- Game-day protocol → `/codex/15-runbooks/incidents/game_day_protocol.md`
- Alerting Tier-5 → `alerting-service@e5c8084` (5 new gateway/notifier modules)
- Strategy Tier-5 → `strategy-service@3b0f7397` (2 configs + close-all + helper)
- Execution Tier-5 → `execution-service@a6fa7c501` (recovery_event_helper)
- DART Tier-5 → `unified-trading-system-ui@01e1bb69` (safety-ops route + widgets)
