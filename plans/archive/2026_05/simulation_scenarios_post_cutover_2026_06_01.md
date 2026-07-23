---
doc_type: plan
title: Simulation scenarios — post-cutover broader regression matrix (deferred from May-23 sprint)
summary:
status: scheduled
nature: record
asset_group: [defi]
stage: [meta]
repos: [execution-service, features-service, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-10
target_start: 2026-06-01
migrated_from:
  simulation_scenarios_topology_price_shocks_2026_05_09.md (Phase 4-9 broader scope deferred 2026-05-10 per Audit C
  Finding C-5; Phase 6/7 coverage matrix + probability table added 2026-05-13 slot 7)
locked_by: live-defi-rollout
locked_since: 2026-05-10
estimate_class: infra
estimate_baseline_ai_days: 19.0
estimate_calibrated_ai_days: 15.2
estimate_calibration_note: "Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~5, ~6, ~2,
  ~1, + 2 more). Class inferred from filename (infra, multiplier 0.8×).

  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be
  double-counted. Owner agent: verify baseline, refine class per /codex/08-workflows/estimation-calibration.md,
  recompute calibrated if either changes.

  "
parent_epic: defi_master
priority: P2
---

## Deferred work — migrated to:

See inline `DEFERRED-OPERATOR` / `DEFERRED-OTHER-SLOT` / `DEFERRED-INDEFINITELY` / `DEFERRED-POST-CUTOVER` / etc.
annotations next to each `- [ ]` item in body for the specific successor / blocker per-item. No single migration target
— this plan tracks multiple per-item dispositions.

# Simulation scenarios — post-cutover broader regression matrix

## What this is

Successor plan for the scope-compression decision shipped 2026-05-10 in
[`simulation_scenarios_topology_price_shocks_2026_05_09.md`](simulation_scenarios_topology_price_shocks_2026_05_09.md).

The pre-cutover sprint ships the **minimum viable adversarial gate**: 6 critical-path scenarios for the 2 LIVE
archetypes (`carry_staked_basis` + `leveraged_funding_arb`) running through execution-service matching-engine
adversarial mode + per-cell expected-outcome assertion. 12-cell matrix passes = May-23 hard-gate cleared.

This post-cutover plan picks up the **broader regression matrix** for full coverage:

- Full 7-layer wire-in (MTDS / MDPS / features-\* / strategy-service / execution-service / position-balance / risk +
  alerting consumers + manifest scenario_id column).
- Per-asset_group scenario library expansion (≥34 scenarios across CeFi / DeFi / TradFi / Sports / Prediction /
  cross-asset).
- Backtest harness CLI integration so any scenario can be invoked end-to-end via `--scenario` flag.
- Codex SSOT sweep documenting the scenario taxonomy + applier patterns.
- DART manual-trade rehearsal exercising scenario injection from operator UI.
- Full per-archetype regression matrix on real VMs across every archetype (not just the 2 LIVE ones — also the BATCH
  archetypes for completeness).

## Carry-forward table — every `deferred-after-successor` item from parent plan

Every phase explicitly marked `deferred-after-successor` in `simulation_scenarios_topology_price_shocks_2026_05_09.md`
is enumerated here per Plan Archival HARD RULE (§ "Migrate every deferred item").

| Parent plan phase                           | Status in parent                                 | What it contains                                                                                                                                                       | Successor phase here    | Deferred-since  |
| ------------------------------------------- | ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------- | --------------- |
| Phase 3.A — MTDS raw-tick overlay           | `deferred-after-successor`                       | `market-tick-data-service` adapters' fetch-result post-processing wire-in                                                                                              | Phase 1 (3.A)           | 2026-05-10      |
| Phase 3.B — MDPS feature-layer overlay      | `deferred-after-successor`                       | `mdps/engine/orchestrator.py` injection point after honest-absence guard                                                                                               | Phase 1 (3.B)           | 2026-05-10      |
| Phase 3.C — features-\* overlay tap         | `deferred-after-successor`                       | `features-service/feature_calculator` calculator wire-in                                                                                                               | Phase 1 (3.C)           | 2026-05-10      |
| Phase 3.D — strategy-service signal tap     | `deferred-after-successor`                       | strategy-service signal tap + outcome hook                                                                                                                             | Phase 1 (3.D)           | 2026-05-10      |
| Phase 3.G — manifest scenario_id column     | `deferred-after-successor`                       | `unified_trading_library/manifest/writer.py` scenario_id propagation                                                                                                   | Phase 1 (3.G)           | 2026-05-10      |
| Phase 4.A — CeFi scenario library           | `deferred-after-successor` (net new 6 scenarios) | `cefi_tick_gap_15min`, `cefi_book_thin`, `cefi_perp_basis_inversion`, `cefi_options_chain_partial_strikes`, `cefi_liquidation_cascade`, `cefi_funding_settlement_skew` | Phase 2 (4.A)           | 2026-05-10      |
| Phase 4.B — DeFi scenario library           | `deferred-after-successor` (net new 5 scenarios) | `defi_lst_depeg_5pct`, `defi_subgraph_lag_60min`, `defi_chain_reorg_5block`, `defi_flash_loan_revert`, `defi_aave_utilization_99pct`                                   | Phase 2 (4.B)           | 2026-05-10      |
| Phase 4.C — TradFi scenario library         | `deferred-after-successor` (6 scenarios)         | Full TradFi set                                                                                                                                                        | Phase 2 (4.C)           | 2026-05-10      |
| Phase 4.D — Sports scenario library         | `deferred-after-successor` (4 scenarios)         | Full Sports set                                                                                                                                                        | Phase 2 (4.D)           | 2026-05-10      |
| Phase 4.E — Prediction scenario library     | `deferred-after-successor` (4 scenarios)         | Full Prediction set                                                                                                                                                    | Phase 2 (4.E)           | 2026-05-10      |
| Phase 4.F — Cross-asset scenario library    | `deferred-after-successor` (3 net new)           | `cross_asset_correlation_break_btc_eth`, `cross_chain_bridge_outage`, `cross_archetype_capital_contention`                                                             | Phase 2 (4.F)           | 2026-05-10      |
| Phase 6.A — Backtest CLI `--scenario` flag  | `deferred-after-successor`                       | Unified backtest CLI extension                                                                                                                                         | Phase 3 (6.A)           | 2026-05-10      |
| Phase 6.B — Backtest pipeline wiring        | `deferred-after-successor`                       | `ScenarioContext` instantiation from CLI flag                                                                                                                          | Phase 3 (6.B)           | 2026-05-10      |
| Phase 7 — Codex SSOT sweep                  | `deferred-after-successor`                       | `scenario-injection-architecture.md` + 2 new codex docs (Phase 8.B-I partially completed 2026-05-13)                                                                   | Phase 4                 | 2026-05-10      |
| Phase 8 — DART rehearsal                    | `deferred-after-successor`                       | Scenario injection from operator UI; manual-approval gate                                                                                                              | Phase 5                 | 2026-05-10      |
| Phase 9 — Full per-archetype VM matrix      | `deferred-after-successor`                       | All scenarios × all archetypes on real VMs; 150-200 cells                                                                                                              | Phase 6                 | 2026-05-10      |
| **Phase 6 coverage matrix spec**            | `design-shipped 2026-05-13`                      | 16-cell pre-cutover matrix with 4-tuple per cell (breaker/alert/recovery/validation); informs Phase 6 run                                                              | Phase 6 (spec consumed) | — (design done) |
| **Phase 7 probability/expected-loss table** | `design-shipped 2026-05-13`                      | Per-scenario probability_weight + expected_loss_bps + recovery_time_hours; historical calibration                                                                      | Phase 6 (spec consumed) | — (design done) |

**Note**: Phase 8.B-I codex additions (scenario authoring guide, archetype selection, runner usage, report shape,
adversarial wiring, provenance, archive, operator runbook) were shipped 2026-05-13 at PM@`91577006` as design artefacts
that support Phase 4 of this plan. Phase 4 todo (codex SSOT sweep) still applies for the remaining 2 new codex docs
(`/codex/03-services/simulation-scenarios.md` + `/codex/02-data/scenario-overlay-write-time-semantics.md`).

## Why deferred

Per CLAUDE.md "Plans Run To Actual Completion, Not Smoke-Test Green" + Audit C Finding C-5 (2026-05-10): the original
9-phase plan with 56 todos starting at T-13 was operationally unrealistic. Compressing to the 6 critical-path scenarios
ships the gate that matters (we know how the 2 LIVE archetypes behave under their most-likely failure modes) without
forcing a hard miss on the cutover deadline.

The post-cutover continuation is NOT optional — broader coverage is required for Citadel-grade discipline. This plan
formalises the work as a named-successor per CLAUDE.md "Temporary state must have a named successor plan" rule.

## Composes with

- [`simulation_scenarios_topology_price_shocks_2026_05_09.md`](simulation_scenarios_topology_price_shocks_2026_05_09.md)
  — pre-cutover compressed-scope plan; Phases 0-5 ship the minimum-viable; this plan picks up Phases 4-9 broader work
  post-cutover.
- [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) — Group F item 17 (backtest fidelity) + item
  22 (trading guardrails) gate satisfied by pre-cutover compressed scope; broader coverage continues post-cutover.
- CLAUDE.md "Live = batch — same data, same fields, same timing semantics, different sources OK" — every scenario rides
  prod codepaths.
- [`disaster_recovery_circuit_breakers_2026_05_10.md`](../archive/disaster_recovery_circuit_breakers_2026_05_10.md) —
  consumes scenario primitives from the pre-cutover sprint; this plan extends them.

## Phases

### Phase 1 — Broader 7-layer wire-in (P0, ~5 AI-days)

Pick up the deferred wire-ins from pre-cutover plan Phase 3:

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **3.A MTDS raw-tick overlay.** `market-tick-data-service` adapters'
      fetch-result post-processing. **MIGRATED FROM:** simulation_scenarios_topology_price_shocks_2026_05_09 Phase 3.A.
      status: todo

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **3.B MDPS feature-layer overlay.** `mdps/engine/orchestrator.py` after
      honest-absence guard. **MIGRATED FROM:** simulation_scenarios_topology_price_shocks_2026_05_09 Phase 3.B. status:
      todo

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **3.C features-\* overlay tap.**
      `features-service/feature_calculator/<calculator>.py`. **MIGRATED FROM:**
      simulation_scenarios_topology_price_shocks_2026_05_09 Phase 3.C. status: todo

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **3.D strategy-service signal tap + outcome hook.** **MIGRATED FROM:**
      simulation_scenarios_topology_price_shocks_2026_05_09 Phase 3.D. status: todo

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **3.G Manifest-layer scenario_id column.**
      `unified_trading_library/manifest/writer.py`. **MIGRATED FROM:**
      simulation_scenarios_topology_price_shocks_2026_05_09 Phase 3.G. status: todo

### Phase 2 — Full per-asset_group scenario library (P0, ~6 AI-days, parallel sub-agents per asset_group)

> **🟢 SCENARIO DEDUPE RULE — RATIFIED 2026-05-10 cross-plan audit L2.** Scenarios marked "(already in pre-cutover)"
> below are NOT re-implemented here — they live in
> [`simulation_scenarios_topology_price_shocks_2026_05_09.md`](simulation_scenarios_topology_price_shocks_2026_05_09.md)
> Phase 4 and ship by May-23. This plan ONLY adds the post-cutover-only scenarios (those without the "already in
> pre-cutover" annotation). Re-implementing would create duplicate scenario_id collisions in the scenario registry.
> Pre-cutover plan owns the 6 May-23 critical-path scenarios for `carry_staked_basis` + `leveraged_funding_arb`
> archetypes; this plan extends the matrix to the broader regression set post-cutover.

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **4.A CeFi (≥8 scenarios)** — `cefi_tick_gap_15min`,
      `cefi_funding_spike_10x` (already in pre-cutover), `cefi_venue_circuit_breaker_trip` (already in pre-cutover),
      `cefi_book_thin`, `cefi_perp_basis_inversion`, `cefi_options_chain_partial_strikes`, `cefi_liquidation_cascade`,
      `cefi_funding_settlement_skew`. **MIGRATED FROM:** simulation_scenarios_topology_price_shocks_2026_05_09 Phase
      4.A. **SCOPE HERE (post-cutover only)**: `cefi_tick_gap_15min`, `cefi_book_thin`, `cefi_perp_basis_inversion`,
      `cefi_options_chain_partial_strikes`, `cefi_liquidation_cascade`, `cefi_funding_settlement_skew`. The other 2
      scenarios ship via the pre-cutover plan; this plan only references them for the regression matrix. status: todo

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **4.B DeFi (≥8 scenarios)** — `defi_oracle_deviation_30sigma` (already in
      pre-cutover), `defi_gas_surge_50x` (already in pre-cutover), `defi_liquidity_drain_lending_pool` (already in
      pre-cutover), `defi_lst_depeg_5pct`, `defi_subgraph_lag_60min`, `defi_chain_reorg_5block`,
      `defi_flash_loan_revert`, `defi_aave_utilization_99pct`. **MIGRATED FROM:**
      simulation_scenarios_topology_price_shocks_2026_05_09 Phase 4.B. status: todo

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **4.C TradFi (≥6 scenarios)** —
      `tradfi_options_chain_partial_4_of_11_clusters_missing`, `tradfi_es_circuit_breaker_l1`,
      `tradfi_globex_disconnect`, `tradfi_econ_release_volatility_burst`, `tradfi_databento_429_burst`,
      `tradfi_vix_15m_yahoo_gap_extension`. **MIGRATED FROM:** simulation_scenarios_topology_price_shocks_2026_05_09
      Phase 4.C. status: todo

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **4.D Sports (4 scenarios)** — `sports_kickoff_delay_60min`,
      `sports_fixture_cancellation_late`, `sports_lineup_late_publish`, `sports_odds_provider_outage`. **MIGRATED
      FROM:** simulation_scenarios_topology_price_shocks_2026_05_09 Phase 4.D. status: todo

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **4.E Prediction (4 scenarios)** —
      `prediction_market_resolve_premature_polymarket`, `prediction_canonical_question_group_partial_market_set`,
      `prediction_clob_book_thin`, `prediction_settlement_disputed`. **MIGRATED FROM:**
      simulation_scenarios_topology_price_shocks_2026_05_09 Phase 4.E. status: todo

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **4.F Cross-asset (4 scenarios)** —
      `cross_asset_correlation_break_btc_eth`, `cross_venue_staleness_perp_60s` (already in pre-cutover),
      `cross_chain_bridge_outage`, `cross_archetype_capital_contention`. **MIGRATED FROM:**
      simulation_scenarios_topology_price_shocks_2026_05_09 Phase 4.F. status: todo

### Phase 3 — Backtest harness CLI + scenario integration (P0, ~2 AI-days)

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **6.A Unified backtest CLI flags.** Per
      `/codex/06-coding-standards/cli-convention.md` axes: extend the backtest CLI with `--scenario <id>`. **MIGRATED
      FROM:** simulation_scenarios_topology_price_shocks_2026_05_09 Phase 6.A. status: todo

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **6.B Pipeline wiring.** Backtest entry instantiates `ScenarioContext`
      from CLI flag + injects into pipeline. **MIGRATED FROM:** simulation_scenarios_topology_price_shocks_2026_05_09
      Phase 6.B. status: todo

### Phase 4 — Codex SSOT sweep (P0, ~1 AI-day)

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **Phase 7 codex updates** — document scenario taxonomy + applier
      patterns + per-asset_group conventions in `/codex/04-architecture/scenario-injection-architecture.md` (NEW) +
      `/codex/03-services/simulation-scenarios.md` (NEW) + `/codex/02-data/scenario-overlay-write-time-semantics.md`
      (NEW). **MIGRATED FROM:** simulation_scenarios_topology_price_shocks_2026_05_09 Phase 7. status: todo

### Phase 5 — DART manual-trade rehearsal with scenario injection (P0, ~2 AI-days)

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **Phase 8 DART rehearsal** — exercise scenario injection from operator UI;
      close-loop on manual-approval gate during scenario run. **MIGRATED FROM:**
      simulation_scenarios_topology_price_shocks_2026_05_09 Phase 8. status: todo

### Phase 6 — Full per-archetype regression matrix on real VMs (P0, ~3 AI-days)

- [x] **[DEFERRED-POST-CUTOVER]** [AGENT] P0. **Phase 9 full matrix** — every scenario × every archetype (LIVE + BATCH
      archetypes), real VM runs, per-cell pass/fail report. Cell count grows from pre-cutover 12 to ~150-200 (depending
      on archetype count). **MIGRATED FROM:** simulation_scenarios_topology_price_shocks_2026_05_09 Phase 9. status:
      todo

## Done definition

- ✅ Every deferred phase from the pre-cutover plan ships.
- ✅ Per-asset_group scenario library has ≥34 scenarios (~6 already shipped pre-cutover; ~28 net new).
- ✅ Backtest harness CLI accepts `--scenario` flag end-to-end.
- ✅ DART surfaces scenario injection for operator-driven rehearsal.
- ✅ Full per-archetype regression matrix passes on real VMs.
- ✅ Codex SSOT docs landed.

## Full-execution criterion

Per CLAUDE.md "Plans Run To Actual Completion, Not Smoke-Test Green":

- ✅ Real VM runs of the full per-archetype matrix complete with pass/fail report. Smoke-only insufficient.
- ✅ DART rehearsal records operator interaction with scenario injection (events stream verified).
- ✅ Backtest CLI invocation against real backfilled data with scenario overlay produces correct end-to-end output.

## Composes with

- Pre-cutover plan: `simulation_scenarios_topology_price_shocks_2026_05_09.md` (consumed primitives)
- Master plan Group F items 17 + 22 (gate satisfied by pre-cutover; broader coverage by this plan)
- DR plan: `disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md` (sister consumer)
- CLAUDE.md "Live = batch" + "Plans Run To Actual Completion" + "Plan Archival" HARD RULES
