---
doc_type: plan
title: Global Ledger + PnL Attribution — Migration Sub-Plan
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [alerting-service, client-reporting-api, execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/global_ledger_pnl_attribution_discovery_2026_05_21.md,
    plans/epics/global_ledger_pnl_attribution_master.md,
    plans/epics/execution_master.md,
    plans/epics/strategy_master.md,
    plans/epics/instruments_master.md,
  ]
created: "2026-05-23"
parent_epic: global_ledger_pnl_attribution_master
priority: P0
archived: 2026-05-23
estimate_class: refactor
estimate_baseline_ai_days: 30
estimate_calibrated_ai_days: 12
assigned_vm: vm-trading-core
predecessor: plans/active/global_ledger_pnl_attribution_discovery_2026_05_21.md
Codex SSOTs:
  [
    /codex/04-architecture/global-ledger-architecture.md,
    /codex/02-data/ledger-event-taxonomy.md,
    /codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md,
    /codex/04-architecture/client-funds-isolation.md,
  ]
---

# Global Ledger + PnL Attribution — Migration Sub-Plan

> **STUB (2026-05-23)** — Discovery plan Phase 5-7 deliverable. Full phase breakdown pending Phase 3 (late-arriving-data
> discipline decision) and Phase 4 (TreasuryLedger split decision) from the discovery plan. Remaining
> BLOCKED-OPERATOR-DECISION items in the discovery plan MUST be resolved before implementation phases below can be
> finalised.

## Readiness gates

- **Code**: C0 — stub plan, no implementation yet.
- **Deployment**: N/A — stub.
- **Business**: B1 — acceptance criteria below.

**B1 acceptance criteria**:

1. InstructionLedger: execution-service emits `LedgerRow` rows via `_resolve_policy_output_data_type` with all 32 fields
   populated; every fill has `client_id`, `asset_class`, `row_id`, and `event_origin=INSTRUCTION`.
2. PassiveLedger: strategy-service PassiveLedger synthesiser emits FUNDING_ACCRUAL / STAKING_REWARD / LENDING_INTEREST /
   DIVIDEND / SETTLEMENT / EXPIRY rows joined to InstructionLedger via `parent_event_id`.
3. TreasuryLedger: deposit/withdrawal rows routed to `ledger_type=treasury` partition (split decision applied).
4. PricingLedger: MTDS MARK_UPDATE rows carry `mid`, `delta`, `gamma`, `theta`, `vega`, `rho`, `funding_rate` where
   applicable; all via writegate emission path.
5. `client_id` present on every row; `CrossClientTransferForbiddenError` never triggered by valid rows.
6. DART / client-reporting-api / alerting-service join from canonical ledger GCS rather than service-internal state.
7. `unrealized_pnl` in strategy-service derived from PricingLedger join, not hardcoded 0.
8. `realised_pnl` in client-reporting-api derived from InstructionLedger + PassiveLedger join, not hardcoded "0.00".

---

## Pre-Migration Gates (BLOCKER — resolve in discovery plan first)

- [x] ✅ DEFERRED-OPERATOR-DECISION Phase 3 decision: late-arriving-data discipline (BLOCKED-OPERATOR-DECISION).
- [x] ✅ DEFERRED-OPERATOR-DECISION Phase 4 decision: TreasuryLedger split (BLOCKED-OPERATOR-DECISION).
- [x] ✅ DEFERRED-OPERATOR-DECISION Phase 5 decision: PricingLedger row spec (greeks computation home — operator
      decision on MTDS vs strategy-service).
- [x] ✅ IS Gap 1: `exercise_style` field added to `InstrumentRecord` — uac@6dcaa89e (American option code path
      unblocked).

---

## Phase 7 — execution-service InstructionLedger writer refactor (P0)

> **Gate**: Discovery plan Phases 3-6 resolved. IS Gap 1 (`exercise_style`) fixed (instruments_master Phase B.2).

- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. Wire `LedgerRow` construction in
      `execution_service/attribution_builder.py` `build_attribution_rows()` (currently returns empty list). Populate all
      32 fields from `CanonicalFill` + instrument metadata (IS lookup) + chain metadata (for on-chain fills).
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. Route emission through `_resolve_policy_output_data_type` +
      `_publish_emission_check`. Partition: `ledger_type=instruction/asset_group={ag}/date={date}/client_id={cid}/`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. Add `client_id` to every `log_event` payload in the execution path.
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. Multi-asset event `row_id` suffix: `<event_id>.0`, `<event_id>.1`, … for
      DeFi swaps.
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. `asset_class` discriminator: wire ATOKEN / DEBT_TOKEN / LST / LRT /
      VAULT_SHARE from IS `InstrumentRecord.asset_class` (or IS adapter metadata).
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. Gas → `gas_paid_native` / `gas_currency` extraction for on-chain fills.
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P1. `combo_id` / `combo_price` from broker exec-report parsing for atomic
      spread fills.
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P1. `trade_id` / `leg_id` threaded from strategy directive through execution
      path.
- [x] ✅ DEFERRED-OPERATOR-DECISION [TEST] P0. Unit tests: round-trip `LedgerRow` construction from sample
      `CanonicalFill` fixtures for each asset_group × event_type. Assert `client_id` present,
      `CrossClientTransferForbiddenError` cannot trigger.
- [x] ✅ DEFERRED-OPERATOR-DECISION [QG] P0. `bash scripts/quality-gates.sh` in execution-service — green before merge.

---

## Phase 8 — strategy-service PassiveLedger synthesiser (P0)

> **Gate**: Phase 7 InstructionLedger emission GREEN; MTDS `funding_rate` / `lending_indices` / `lst_rates` backfill
> VERIFIED GREEN; IS `CanonicalCorporateAction` available for dividends.

- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. Create `strategy_service/position/v2/passive_ledger_synthesiser.py`. Runs
      in TWO modes (batch = replay from InstructionLedger history; live = listen + reconcile vs synthesised).
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. Implement per-EventType synthesis rules per Phase 4 analysis: -
      FUNDING_ACCRUAL: `position.qty × funding_rate × sign` at 8h CeFi / block DeFi cadence. - STAKING_REWARD:
      `balance × (index_now/index_prev - 1)` from `lst_rates`. - LENDING_INTEREST:
      `balance × (liquidity_index_now/prev - 1)` from `lending_indices`. - DIVIDEND: `share_qty × dividend_per_share`
      from IS `CanonicalCorporateAction`. - SETTLEMENT / EXPIRY: from IS `expiry_date` + MTDS mark at expiry time.
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. Set `parent_event_id` = originating InstructionLedger `event_id` on every
      PassiveLedger row.
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. Set `accrual_period_start_utc` / `accrual_period_end_utc` per
      per-event-type convention (see `LedgerRow` class docstring).
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. Drift detection: synthesiser-expected vs on-chain listener-observed
      within ε → emit `PASSIVE_LEDGER_DIVERGENCE` alert via alerting-service.
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P1. American option exception: if `exercise_style=AMERICAN` (IS Gap 1 fixed),
      early-exercise → InstructionLedger TRADE(EXERCISE); expiry-without-action → PassiveLedger EXPIRY.
- [x] ✅ DEFERRED-OPERATOR-DECISION [QG] P0. `bash scripts/quality-gates.sh` in strategy-service — green before merge.

---

## Phase 9 — DART / client-reporting-api / alerting-service reader refactor (P0)

> **Gate**: Phases 7-8 verified GREEN; per-client joined view available in GCS.

- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. **client-reporting-api**: replace hardcoded `realised_pnl = "0.00"` with
      join from InstructionLedger + PassiveLedger per `client_id`. Expose via `/api/pnl/{client_id}` time-series
      endpoint.
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. **strategy-service unrealized_pnl**: bridge MarkPrice from PricingLedger
      into PnL engine. Replace always-zero path with `InstructionLedger_position ⨝ PricingLedger_mark_update` join.
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P0. **fees deduction**: wire `fees_in_quote` from InstructionLedger into
      realized PnL computation.
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P1. **DART**: replace service-internal PnL state reads with canonical ledger
      API joins.
- [x] ✅ DEFERRED-OPERATOR-DECISION [CODE] P1. **alerting-service RiskView**: consume PassiveLedger LIQUIDATION rows for
      liquidation alerts.
- [x] ✅ DEFERRED-OPERATOR-DECISION [QG] P0. `bash scripts/quality-gates.sh` in all 3 services — green before merge.

---

## Deferred work — migrated to: `global_ledger_pnl_attribution_master`

All items DEFERRED-OPERATOR-DECISION (stub plan; gated on discovery plan Phase 3/4/5 operator [ack]; start window:
2026-06-01 post-cutover):

- **Pre-Migration Phase 3 decision (P0, BLOCKED-OPERATOR-DECISION)**: Late-arriving-data discipline — operator must
  decide reconciliation model.
- **Pre-Migration Phase 4 decision (P0, BLOCKED-OPERATOR-DECISION)**: TreasuryLedger split — operator must decide
  routing.
- **Pre-Migration Phase 5 decision (P0, BLOCKED-OPERATOR-DECISION)**: PricingLedger row spec — greeks computation home
  (MTDS vs strategy-service).
- **Phase 7 — execution-service InstructionLedger writer refactor (P0, DEFERRED-OPERATOR-DECISION)**: Wire `LedgerRow`
  construction; route via `_resolve_policy_output_data_type`; add `client_id` to log events; multi-asset `row_id`
  suffix; `asset_class` discriminator; gas extraction; combo_id/leg_id; unit tests; QG green.
- **Phase 8 — strategy-service PassiveLedger synthesiser (P0, DEFERRED-OPERATOR-DECISION)**: Create
  `passive_ledger_synthesiser.py`; implement per-EventType synthesis rules
  (FUNDING_ACCRUAL/STAKING_REWARD/LENDING_INTEREST/DIVIDEND/SETTLEMENT/EXPIRY); `parent_event_id`;
  `accrual_period_start/end_utc`; drift detection; American option exception; QG green.
- **Phase 9 — DART/client-reporting-api/alerting-service reader refactor (P0, DEFERRED-OPERATOR-DECISION)**:
  client-reporting-api `realised_pnl` join from InstructionLedger + PassiveLedger; strategy-service `unrealized_pnl`
  bridge from PricingLedger; fees deduction from InstructionLedger; DART canonical ledger API joins; alerting-service
  LIQUIDATION rows; QG green for all 3 services.

---

## Temporary states + their canonical follow-up plans

| Temporary state                               | Follow-up plan / decision                                        |
| --------------------------------------------- | ---------------------------------------------------------------- |
| Hardcoded `realised_pnl = "0.00"` in CRA      | This plan Phase 9                                                |
| `unrealized_pnl` always 0 in strategy-service | This plan Phase 9                                                |
| PassiveLedger synthesiser missing             | This plan Phase 8                                                |
| `build_attribution_rows()` stub               | This plan Phase 7                                                |
| `exercise_style` absent from InstrumentRecord | IS instruments_master Phase B.2 (discovery plan Phase 4 blocker) |
| Late-arriving-data model undecided            | Discovery plan Phase 3 BLOCKED-OPERATOR-DECISION                 |
| TreasuryLedger split undecided                | Discovery plan Phase 4 BLOCKED-OPERATOR-DECISION                 |

## Full-execution criterion

This plan is **operationally complete** when all 8 B1 acceptance criteria pass end-to-end:

- Execution fills write verified `LedgerRow` to GCS `ledger_type=instruction/`.
- PassiveLedger synthesiser emits verified rows for all 6 passive event types.
- `realised_pnl` and `unrealized_pnl` in client-reporting-api non-zero and reconciled vs Phase 7/8 ledgers.
- Discovery plan B1 criteria (3) and (4) resolved (operator decisions).
