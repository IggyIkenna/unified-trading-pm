---
name: global_ledger_pnl_attribution_master
title: "Global Ledger + PnL Attribution Master"
type: epic
tier: L2
status: active
priority: P0
assigned_vm: vm-trading-core
parent: master_to_live_defi_2026_05_23
created: 2026-05-21
last_updated: 2026-05-21
locked_by: live-defi-rollout
locked_since: 2026-05-21
related_plans:
  - plans/active/global_ledger_pnl_attribution_discovery_2026_05_21.md
---

# Global Ledger + PnL Attribution Master

**Owns**: the canonical ledger architecture from which position, exposure, PnL, and PnL-attribution are all derived.
Four SSOT ledgers (Instruction, Passive, Treasury, Pricing) + four derived materialised views (Position, Exposure, PnL,
PnLAttribution) + one filtered view (Risk).

**Why a new epic** (vs absorbing into `execution_master` or `strategy_master`):

- The architecture spans **5 services as writers** (execution-service, treasury writers in execution-service, MTDS +
  instruments-service for PricingLedger, strategy-service as derived-ledger writer) and **many more as readers** (DART,
  alerting-service, client-reporting-api, strategy-service backtest + live engines).
- The SSOT lives in UAC (`unified_api_contracts.canonical.crosscutting.ledger/`) which is cross-cutting.
- The Group F/G MVP from `client_reporting_pnl_attribution_mvp_2026_05_10.md` (archived 2026-05-16) shipped a per-client
  NAV/PnL surface for the May-23 cutover. This epic generalises that MVP into the SSOT ledger model so every downstream
  consumer joins one of four canonical surfaces.

**Cross-references**:

- `execution_master.md` — InstructionLedger + PassiveLedger writers (active path).
- `strategy_master.md` — `strategy_service/position/`, `strategy_service/pnl/`, `strategy_service/risk/`,
  `strategy_service/portfolio_allocator/` are the derived-ledger compute home (these modules already exist and shipped
  via the archived attribution MVP).
- `mtds_mdps_master.md` — PricingLedger (price + mid + IV + greeks) authoring.
- `instruments_master.md` — instrument metadata that drives passive-event synthesis (expiry timestamps, funding
  intervals, rebase schedules, dividend/coupon dates, settlement style).
- `observability_master.md` — RiskView consumes PassiveLedger liquidation/slashing rows for alerting.
- `dart_and_promote_master.md` — DART consumes PnL + PnLAttribution.

## Architecture summary

**Event taxonomy** (every row in InstructionLedger or PassiveLedger):

| Origin                 | Event types                                                                                                                                                                                                               |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `instruction` (active) | trade, swap, transfer, stake, unstake, supply, withdraw, borrow, repay, bridge, wrap, unwrap, early_exercise, cash_out, deposit, withdrawal_to_bank, custody_move, fx_conversion                                          |
| `passive` (automatic)  | funding, rebase, interest_accrual, staking_reward, validator_reward, mev_reward, airdrop, dividend, coupon, expiry_settlement, sports_resolution, prediction_resolution, liquidation, slashing, gas_refund, auto_compound |

**Four SSOT ledgers** (append-only, event-sourced):

| Ledger            | Writer                                                         | Cardinality             | Storage notes                                                                             |
| ----------------- | -------------------------------------------------------------- | ----------------------- | ----------------------------------------------------------------------------------------- |
| InstructionLedger | execution-service                                              | ~thousands/day          | Append-only; enrichments arrive as separate rows with `parent_event_id`                   |
| PassiveLedger     | execution-service synthesiser + on-chain/venue listeners       | ~thousands–millions/day | Synthesisable from instrument metadata + clock for backtest parity                        |
| TreasuryLedger    | execution-service (operator-tools subset)                      | ~tens/day               | Cohort of InstructionLedger; may be its own table for accounting SLA — discovery decision |
| PricingLedger     | MTDS (price/mid/IV/greeks) + instruments-service (carry rates) | ~millions/day           | Instrument-agnostic from a write-perspective; client/strategy-agnostic                    |

**Four derived ledgers** (materialised views over the SSOT):

| Ledger               | Definition                                                                                                                                | Owner module                                                         |
| -------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| PositionLedger       | `Σ delta` per `(client_id, account, asset_canonical_id)` over time                                                                        | `strategy_service/position/`                                         |
| ExposureLedger       | PositionLedger ⨝ PricingLedger → notional + delta-adj + vega + theta exposure by underlying/venue/client                                  | `strategy_service/risk/core/exposure_aggregator.py`                  |
| PnLLedger            | Δ(cash + MTM value of positions) per period                                                                                               | `strategy_service/pnl/engine/`                                       |
| PnLAttributionLedger | Decomposition: delta-PnL + gamma-PnL + theta-PnL + vega-PnL + carry-PnL + funding-PnL + settlement-PnL + fees + slippage + gas + residual | `strategy_service/pnl/engine/breakdown.py` + `reward_attribution.py` |

**One view**: RiskView — filtered slice of PassiveLedger (liquidation, slashing, margin-call, kill-switch-trip)
augmented with Position + Exposure snapshot at event time.

## Assigned active plans

### P0 — Discovery + target-state spec

- [`global_ledger_pnl_attribution_discovery_2026_05_21.md`](../active/global_ledger_pnl_attribution_discovery_2026_05_21.md)
  — current-state audit across 5+ services, UAC schema spec, late-arriving-data discipline, writer/reader gap analysis,
  VM-prefix additions for net-new runtime artifacts.

### P1 — Implementation (sub-plans spawned from discovery)

_(none yet — sub-plans land here as the discovery plan produces them)_

### P2 — Continuous-verification + reconciliation

_(none yet — to be defined post-discovery)_

### P3 — Post-cutover enrichments

_(none yet — to be defined post-discovery)_

## VM assignment notes

This epic runs on **`vm-trading-core`** alongside `execution_master` and `trading_agent_master`. Net-new runtime
artifacts emerging from the discovery plan declare their own VM prefixes via `VM_PREFIX_TO_BUCKET` in
`deployment-service/scripts/vm/vm_zombie_watchdog.py`. Anticipated additions (subject to discovery confirmation):

- `ledger-reconcile-` → `SCHEDULED_RECURRING`, nightly venue-vs-ledger reconciliation. May absorb into existing
  `batch-live-recon-cron-` cohort if the workload fits the same daily window.
- `passive-listener-` → `LONG_LIVED_LIVE` if on-chain emission listening is dedicated. Discovery decides whether MTDS /
  execution-service workers absorb this.
- No new prefixes for derived ledgers — `strategy-paper-*` / `strategy-live-*` / `client-reporting-cutover-*` already
  exist and are the compute home.

## Continuous-verification path

| Surface                                              | Verification                      | Cadence      |
| ---------------------------------------------------- | --------------------------------- | ------------ |
| InstructionLedger ⟷ venue execution reports          | Daily reconciliation cron         | T+1 daily    |
| PassiveLedger synthesiser ⟷ on-chain/venue emissions | Per-event divergence check        | Per emission |
| PricingLedger ⟷ MTDS canonical prices                | Snapshot cross-check              | Hourly       |
| Derived ledgers ⟷ SSOT replay                        | Backfill replay = production view | Pre-deploy   |
| RiskView liquidation rows ⟷ alerting-service pages   | End-to-end smoke                  | Per event    |
