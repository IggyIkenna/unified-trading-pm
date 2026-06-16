---
scope: [engineer, admin]
---

# Cutover-window critical-path checkpoint timeline (2026-05-13 → 2026-05-23)

**Created**: 2026-05-13 per operator scope clarification **Status**: SSOT for cutover-window orchestration. Binds slot
scheduling + identifies parallel-track work that does NOT gate on data-pipeline serialization. Read at start of every
slot 1 morning ledger sweep through 2026-05-23.

## Why this exists

Operator direction 2026-05-13: _"even if we find mtds gonna take 5 days for backfill doesn't stop us getting to the end
with code and tests for that asset group whilst waiting. not like everything should pause. we want to keep the 100-200
ai days per day worth of work going"_.

The cutover window has **two interleaved tracks**:

1. **Serial data-pipeline track** (manifest → instruments → MTDS → MDPS → features → ML/strategy backtest) —
   sequencing-bound.
2. **Parallel code-and-tests track** (archetype code, UI, CI/CD, treasury, optimization, codex) — does NOT pause for the
   serial track. Runs concurrently.

This doc identifies what's on which track + the checkpoint dates that bind cutover readiness.

## Hard sequencing constraint (the serial track)

```
2026-05-13 (today)
  ├─ Manifest schema v8 freeze-prep in flight
  │  └─ plans: manifest_schema_final_gate_2026_05_09, expected_unattempted_propagation_chain_2026_05_12
  │
2026-05-15 (Fri) — FREEZE GATE
  ├─ Manifest schema v8 LOCKED — UAC canonical/domain/ no-edit window begins
  ├─ Manifest corrections done (phantom audit residuals, classifier fixes, reconcile-apply done)
  ├─ Bucket provisioning complete on GCP (env-tiered, ~180-300 buckets)
  └─ Instruments-service backfill complete (1-2 day window — runs 2026-05-14 + 2026-05-15)
  │
2026-05-15 → 2026-05-17 (Fri→Sun) — MTDS BACKFILL DRAIN (~2-3 days)
  ├─ MTDS backfill captures real ticks for entire MVP universe
  ├─ All 5 asset_groups in parallel (cefi/defi/tradfi/sports/prediction)
  └─ Honest-absence semantics for known gaps (per UAC SOURCE_PRIORITY + EMPTY_CONFIRMED_REASONS)
  │
2026-05-17 → 2026-05-18 (Sun→Mon) — MDPS + FEATURES BACKFILL (~1-2 days)
  ├─ MDPS aggregates ticks → ohlcv/book_snapshot/funding etc.
  ├─ features-service computes feature_groups per archetype × per-day × per-instrument
  ├─ Pricing data + features READY for MVP universe (per codex/09-strategy/mvp-universe-per-asset-group.md)
  └─ Walk-forward training inputs available for CeFi/TradFi/Sports 5-yr; DeFi/Prediction 2-yr
  │
2026-05-18 → 2026-05-19 (Mon→Tue) — ML TRAINING + STRATEGY BACKTESTS START
  ├─ ML experiments START in PARALLEL:
  │  ├─ Sports ml-settled (Top-5 EU football × 4 markets × 5-yr)
  │  ├─ CeFi ml-continuous (30 MVP coins, focus BTC + ETH × 5-yr walk-forward)
  │  └─ TradFi ml-continuous (ES + commodity futures × 5-yr walk-forward)
  ├─ DeFi strategy backtests START (minimal ML needed — rule-based + paired_price_dispersion):
  │  ├─ CARRY_STAKED_BASIS, CARRY_BASIS_DATED, CARRY_BASIS_PERP
  │  ├─ CARRY_RECURSIVE_STAKED, CARRY_RECURSIVE_BORROW_LENDING_ONLY, CARRY_BASIS_PERP_INV
  │  └─ ARBITRAGE_PRICE_DISPERSION (funding-rate-dispersion + dated-cross-venue variants)
  │
2026-05-19 → 2026-05-21 (Tue→Thu) — STRATEGY + EXECUTION BACKTESTS + PAPER TRADING
  ├─ Execution-alpha measurement (paired live-fills vs always-fill — per archetype)
  ├─ DeFi paper trading on testnet (Aave Sepolia + Uniswap Sepolia + Solana devnet)
  ├─ Live wallets + CeFi accounts funded (operator's wallet, Trust Wallet across 5 EVM chains + Solana)
  └─ CeFi credentials wired (need DeFi venues for arb + carry too — same archetype family)
  │
2026-05-21 → 2026-05-22 (Thu→Fri) — END-TO-END DRESS REHEARSAL + PRE-CUTOVER GATE
  ├─ First real-data end-to-end run through full pipeline
  ├─ credential-probe.sh --mode live --archetype carry_staked_basis = 100% pass
  ├─ DART UI + deployment UI smoke-verified
  ├─ CI/CD on main branch passing all QG
  └─ Treasury rollup + wallet status all green
  │
2026-05-23 (Sat) — CUTOVER
  └─ Live trading begins on real wallet
     ├─ carry_staked_basis live (DART manual-trade gate, operator-monitored)
     └─ ARBITRAGE_PRICE_DISPERSION live (~2 days lag behind carry_staked_basis)
```

## Parallel-track work (does NOT gate on the serial track)

Run RIGHT NOW (2026-05-13) through 2026-05-23 in parallel with the data-pipeline serial track. Mock data + UAC
schema-locked surfaces are sufficient for these.

| Workstream                                                     | Driver plan                                                                      | Target completion            | Owner type                       |
| -------------------------------------------------------------- | -------------------------------------------------------------------------------- | ---------------------------- | -------------------------------- |
| Tier A archetype code finalization (all 6 families)            | defi_master + strategy_and_dart_master                                           | **2026-05-17**               | strategy-service slot            |
| Tier B options-strategy code (architecture-driver)             | strategy_archetype_taxonomy                                                      | **2026-05-21**               | strategy-service slot            |
| `compute_optimization_mock_data_2026_05_13` Phases 0-5         | self                                                                             | **2026-05-18**               | features + execution + ml slots  |
| DART manual-trade UX refactor                                  | `dart_manual_trade_ux_refactor_2026_05_13`                                       | **2026-05-20**               | UTS-UI slot                      |
| Deployment UI lifecycle tabs                                   | `deployment_ui_lifecycle_tabs_2026_05_08`                                        | **2026-05-20**               | UTS-UI slot                      |
| CI/CD images vs tarball decision + main-branch QG green        | `promote_workflow_may23_cli_path` + `governance_qg_automation_gaps_post_cutover` | **2026-05-18 (freeze gate)** | deployment-service slot          |
| Treasury / wallet provisioning verification (CMK already done) | `wallet_treasury_client_flow` + `api_keys_wallets`                               | **2026-05-21**               | wallet-service slot              |
| `governance_qg_automation_gaps` pulled-forward                 | self                                                                             | **2026-05-20**               | platform slot                    |
| `basefc_validation_flip` (75 calcs ClassVar)                   | self                                                                             | **2026-05-19**               | features slot                    |
| `codex_doc_currency_and_consolidation`                         | self                                                                             | **2026-05-22**               | research slot                    |
| 4 DeFi alert codes (`DEFI_AAVE_UTILIZATION_SPIKE` etc.)        | `alerting_service_live_rules`                                                    | **2026-05-18**               | features-onchain + alerting slot |
| Treasury rollup endpoint `/api/treasury/rollup`                | `api_keys_wallets` Phase 3.D                                                     | **2026-05-19**               | deployment-api slot              |
| Risk simulations + disaster recovery scripts                   | `risk_simulations_limits_alerting`, `disaster_recovery_circuit_breakers`         | **2026-05-20**               | risk + DR slots                  |

**Insight for orchestrator**: 13 parallel workstreams above can ship without waiting for backfill. They're all
schema-stable (use UAC canonical models + mock data) or UI-layer (don't touch backfill data).

## Per-archetype ML/backtest sizing (operator clarification: "human takes ~0.5 day per backtest/strategy/ML optimization")

Once data-pipeline serial track completes (2026-05-18 EOD), the parallel ML training + strategy backtest workstream:

| Tier A archetype family                                                               | Instances (multiple strategies + concurrent loops) | Per-instance cal-AI-days (0.5 day per operator estimate) |     Total cal-AI-days |
| ------------------------------------------------------------------------------------- | -------------------------------------------------: | -------------------------------------------------------: | --------------------: |
| ml-continuous (CeFi 30 coins + ES)                                                    |                     ~30 coins × walk-forward loops |                                     0.5 × ~10 concurrent |                  ~5.0 |
| ml-settled (Sports Top-5 EU × 4 markets)                                              |              ~20 instances (5 leagues × 4 markets) |                                     0.5 × ~10 concurrent |                  ~5.0 |
| arbitrage-funding-rate (CeFi 30 × 6 venues)                                           |                    ~6 venue groups, per-pair loops |                                      0.5 × ~6 concurrent |                  ~3.0 |
| arbitrage-sports-book (Polymarket vs Betfair Top-5 EU)                                |                             ~5 leagues × 4 markets |                                      0.5 × ~4 concurrent |                  ~2.0 |
| arbitrage-event-markets (Polymarket vs CME)                                           |                              1-3 venue-pair groups |                                      0.5 × ~2 concurrent |                  ~1.0 |
| defi-carry-family (7 archetypes incl. CARRY_BASIS_DATED + ARBITRAGE_PRICE_DISPERSION) |                                      ~7 archetypes |                                      0.5 × ~7 concurrent |                  ~3.5 |
| **TOTAL Tier A backtest/ML completion**                                               |                                                    |                                                          | **~19.5 cal-AI-days** |

At measured workspace throughput ~150-250 cal-AI-days/day, ~19.5 cal-AI-days = **<1 day wall-clock with concurrent slot
fan-out**.

**Critical implication**: from 2026-05-18 EOD (data ready) to 2026-05-20 (paper-trade dress rehearsal start), full Tier
A backtest/ML completion fits in 1-2 calendar days. Even with the 5-yr CeFi/TradFi/Sports extension.

## Slot scheduling guidance (for slot 1 orchestrator)

### Days 1-2 (2026-05-13 → 2026-05-14) — PARALLEL TRACK ONLY (real backfill not started yet)

Allocate slots heavily to parallel-track work — there's no data-pipeline dependency to wait on yet:

- 2 slots → `compute_optimization_mock_data` Phases 0-2 (verify run_2yr_config_grid_backtest + features parallel
  batching)
- 1 slot → `dart_manual_trade_ux_refactor` (UTS-UI extraction)
- 1 slot → `deployment_ui_lifecycle_tabs`
- 1 slot → Tier B options-strategy code (architecture-driver, post-cutover backtest but code ships now)
- 1 slot → 4 DeFi alert codes producer wiring (features-onchain)
- 1 slot → `basefc_validation_flip` Phase 0 (paradigm decision)
- 1 slot → `treasury rollup endpoint` (deployment-api)

### Days 3-5 (2026-05-15 → 2026-05-17) — FREEZE GATE + BACKFILL DRAIN

- 1 slot → master plan freeze-gate orchestration (slot 1 main)
- 2 slots → MTDS backfill monitoring + retry-on-failure (`live_pipeline_mtds_mdps_features` Phase 5)
- 2 slots → manifest reconciler apply-flips (`expected_unattempted_propagation_chain` Phase 5B)
- 1 slot → batch_live_symmetry codex docs (Tabs 1-3, requested in earlier ping)
- 1 slot → defi_recursive_borrow Solidity contracts (requested in earlier ping)
- 1 slot → CI/CD main-branch QG sweep + `governance_qg_automation` ratchets

### Days 6-7 (2026-05-18 → 2026-05-19) — FEATURES READY + ML/BACKTEST KICKOFF

- 1 slot per Tier A archetype family → backtest harness drives (6 slots, ~0.5 day each)
- 1 slot → ml-training hyperparam grid sweep (`ml_and_features_master` walk-forward)
- 1 slot → execution-alpha measurement (`compute_optimization` Phase 3)
- 1 slot → dress-rehearsal prep (`promote_workflow_may23_cli_path` Phase 9)

### Days 8-9 (2026-05-20 → 2026-05-21) — DRESS REHEARSAL + PAPER TRADE

- 2 slots → end-to-end paper-trade smoke on testnet (DeFi side)
- 1 slot → CeFi account funding + credential verification
- 1 slot → DART UI smoke on dress-rehearsal pipeline
- 1 slot → Treasury rollup + risk + disaster-recovery dry-runs
- 1 slot → `audit_records_pb_1_2_3_pre_cutover` final P0 items

### Day 10 (2026-05-22) — PRE-CUTOVER SIGN-OFF

- All slots → green-light verification via `credential-probe.sh --mode live --archetype carry_staked_basis`
- Slot 1 main → final master plan refresh + cutover-go decision

### Day 11 (2026-05-23) — CUTOVER

- Operator-driven; agent slots in standby for incident response

## What this means for the "do plans encode these checkpoints?" question

**Currently encoded** (good):

- Manifest freeze gate 2026-05-15 in `manifest_schema_final_gate_2026_05_09` + `code_freeze_migrate_backfill_sequencing`
  Phase 1
- Backfill window 2026-05-15→2026-05-19 in `code_freeze_migrate_backfill_sequencing` Phase 2-3
- Tier A archetype scope in `codex/09-strategy/mvp-universe-per-asset-group.md` (just shipped 2026-05-13)
- Compute optimization parallel track in `compute_optimization_mock_data_2026_05_13`
- 7 pulled-forward May-23 items in respective plan frontmatters (2026-05-13 batch)

**Not yet encoded** (action items spawned by this doc):

- Per-asset_group ML kickoff dates (2026-05-19) — need to be added to `features_and_ml_master.md`
- DeFi strategy + execution backtest start dates (2026-05-19) — need to be added to `defi_master.md`
- Live wallet funding + CeFi credentials gate (2026-05-20) — need explicit dates in
  `wallet_treasury_client_flow_2026_05_10.md`
- DART UI + deployment UI ready (2026-05-20) — need explicit dates in `dart_manual_trade_ux_refactor_2026_05_13` +
  `deployment_ui_lifecycle_tabs`
- CI/CD vs tarball decision (2026-05-18) — need explicit milestone in `promote_workflow_may23_cli_path`

These are PENDING — the per-plan frontmatter currently says `deadline: 2026-05-23` for all, which is correct but doesn't
surface the intermediate milestones. Suggested action: orchestrator ping epic owners to add per-checkpoint dates in
their plan bodies.

## Cross-references

- **MVP universe** (Tier A vs Tier B scope):
  [`codex/09-strategy/mvp-universe-per-asset-group.md`](../09-strategy/mvp-universe-per-asset-group.md)
- **Compute optimization parallel track**:
  [`plans/active/compute_optimization_mock_data_2026_05_13.md`](../../plans/active/compute_optimization_mock_data_2026_05_13.md)
- **Manifest freeze gate**:
  [`plans/active/manifest_schema_final_gate_2026_05_09.md`](../../plans/active/manifest_schema_final_gate_2026_05_09.md)
- **Code-freeze cutover sequencing**:
  [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](../../plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md)
- **DeFi archetype owner**: [`plans/active/defi_master.md`](../../plans/active/defi_master.md) Fork 1
- **ML training**: [`plans/epics/features_and_ml_master.md`](../../plans/epics/features_and_ml_master.md)
- **Master umbrella**:
  [`plans/active/master_to_live_defi_2026_05_23.md`](../../plans/active/master_to_live_defi_2026_05_23.md)

### Master plan Group F items — sequencing ownership

This document is the SSOT for cutover-window stage ordering. The following master plan Group F items depend on the
checkpoints and parallelization insights defined above:

| Master plan item                                         | What gates it here                                                                                                                                                                                        | Checkpoint                                            |
| -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| **F.17** — `carry_staked_basis` end-to-end batch run     | Pipeline serial track 2026-05-18→2026-05-19 (ML/backtest kickoff slot); compute-optimization Phase 1 fan-out wrapper needed for config-grid                                                               | `code_freeze` Phase 3.3–3.5 complete                  |
| **F.18** — 2-year P&L variance config-grid batch run     | Requires pipeline serial track through features-service + `compute_optimization` Phase 1 (per-day fan-out wrapper); VM sizing per `codex/06-coding-standards/performance-targets.md` § Acceptable targets | `code_freeze` Phase 3 complete + optimization Phase 1 |
| **F.20** — Execution-service testnet validation          | Parallel-track (does NOT gate on data-pipeline serial track) — runs 2026-05-19→2026-05-20 via execution-alpha measurement harness (`compute_optimization` Phase 3)                                        | Days 6-7 window                                       |
| **F.21** — Batch-vs-live reconciliation within tolerance | Last step: requires live-mode pipeline running (2026-05-22+); execution-alpha delta is the input for tolerance comparison                                                                                 | Week 3 cutover (post 2026-05-22)                      |

## Continuous verification

Read at slot 1 main morning ledger sweep daily through 2026-05-23. Update on any sequencing change (e.g., if MTDS
backfill drags +1 day, push ML kickoff +1 day and update both this doc + master plan).

Last reviewed: 2026-05-13. Next review: every morning slot 1 boot through 2026-05-23.
