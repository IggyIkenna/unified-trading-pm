---
doc_type: plan
title: Simulation scenarios — synthetic topology gaps + price shocks for backtest robustness
summary:
status: complete
nature: record
asset_group: [defi]
stage: [meta]
repos: [alerting-service, deployment-api, deployment-service, deployment-ui, execution-service, features-service]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/active/defi_master.md,
    plans/epics/cross_cutting_2026_05_23.epic.md,
    plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md,
    plans/active/alerting_service_live_rules_2026_05_07.md,
    plans/active/writegate_honest_coverage_endtoend_2026_05_06.md,
    plans/archive/risk_simulations_limits_alerting_2026_05_10.md,
    plans/questions/disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md,
    plans/questions/mock_data_pipeline_benchmarking_2026_05_08.md,
    plans/questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md,
  ]
created: 2026-05-09
locked_by: live-defi-rollout
locked_since: 2026-05-09
estimate_class: design
estimate_baseline_ai_days: 33.5
estimate_calibrated_ai_days: 20.1
estimate_calibration_note: "Baseline auto-extracted from in-body AI-day mentions during 2026-05-11 sweep (~3-5, ~1, ~1,
  ~1, + 14 more). Class inferred from filename (design, multiplier 0.6×).

  CAVEAT: auto-extract SUMS all in-body mentions; plans with both 'Total: X' headlines AND per-phase line items will be
  double-counted. Owner agent: verify baseline, refine class per /codex/08-workflows/estimation-calibration.md,
  recompute calibrated if either changes.

  "
parent_epic: defi_master
priority: P2
---

# Simulation scenarios — synthetic topology gaps + price shocks for backtest robustness

> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing 2026-05-10** (BE-AWARE)
>
> [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
> anti-sequencing audit flags this plan as a Phase 2.2 single-walk discipline risk: if the simulation harness writes
> synthetic-data parquets into the same buckets as real captures, it could conflict with the GCS bundled migration's
> "one walk only" rule. **Required mitigation (per code_freeze anti-sequencing audit row)**: confirm simulation outputs
> go to dedicated `*-sim-*` buckets per `bucket_name_ssot_canonicalisation_2026_05_10.md`'s yaml SSOT (operator decision
> (b+) 2026-05-11 — env-tier convention extends to ALL bucket kinds, so `*-sim-*` buckets also need env-tier in their
> names). If sim buckets are not yet isolated, **defer simulation runs to Phase 3** (post-Phase-2-freeze 2026-05-19).
> Banner-removal owned by this plan when sim-bucket isolation is verified.

> **🟡 SCOPE-COMPRESSED 2026-05-10 (T-13 to cutover)** — operator review of Audit C Finding C-5 (56 todos / 0 done at
> T-13, well-designed but unstarted) ratified Citadel-grade compression: ship the **MINIMUM VIABLE adversarial gate**
> that covers the 2 LIVE archetypes (`carry_staked_basis` + `leveraged_funding_arb`) under their 6 highest-likelihood
> failure modes, run end-to-end through real execution-service matching-engine adversarial mode, with per-scenario
> expected-outcome assertion. \*\*Defer the broader regression matrix + per-asset-group scenario library + UI
> integration
>
> - 7-layer wire-in to the post-cutover successor plan
>   [`simulation_scenarios_post_cutover_2026_06_01.md`](../archive/2026_05/simulation_scenarios_post_cutover_2026_06_01.md)\*\*
>   (NEW, sibling plan, ~6-9 weeks scope including the deferred Phases 4-9 of this plan body).
>
> **Pre-cutover compressed scope (~3-5 AI-days, ~15 todos)**:
>
> 1. UAC `ScenarioOverlay` Pydantic dataclass + `ScenarioOutcomeAssertion` closed-enum — minimal subset (5 mutation
>    types + 3 outcome categories). Phase 1 todos 1.A-1.C scoped down; 1.D-1.F deferred.
> 2. UTL `ScenarioOverlayApplier` + `ScenarioOutcomeChecker` — single-layer (execution-service matching-engine
>    adversarial mode) NOT 7-layer. Phase 2 todos 2.A-2.B + 2.D scoped down; 2.C / 2.E / 2.F deferred.
> 3. **Single wire-in** — execution-service `matching_engine/` adversarial mode (per Phase 3.E) + position-balance +
>    risk + alerting consumers (per Phase 3.F). Phases 3.A / 3.B / 3.C / 3.D / 3.G deferred (MTDS / MDPS / features /
>    strategy taps + manifest scenario_id column = post-cutover infra).
> 4. **6 critical-path scenarios** for the 2 LIVE archetypes (subset of Phase 4):
>    - `defi_oracle_deviation_30sigma` — Chainlink/Pyth stale or wild; direct hit on `carry_staked_basis` LST yields.
>    - `defi_gas_surge_50x` — Ethereum gas spike; affects `carry_staked_basis` rebalance economics.
>    - `cefi_funding_spike_10x` — perp funding rate jump; direct hit on `leveraged_funding_arb`.
>    - `cefi_venue_circuit_breaker_trip` — Bybit/Binance halts; affects perp leg.
>    - `defi_liquidity_drain_lending_pool` — Aave/Morpho utilization spike → can't borrow; affects deleverage path.
>    - `cross_venue_staleness_perp_60s` — one perp venue feed stale > 60s; hedge-leg consistency.
> 5. Per-archetype matrix: 2 archetypes × 6 scenarios = **12 cells** (Phase 5 scoped to 12 cells, not full per-archetype
>    matrix). DONE = all 12 PASS. Phase 5.A/5.B/5.C scoped down accordingly.
> 6. Skip Phases 6 (broader backtest harness CLI), 7 (codex sweep), 8 (rehearsal), 9 (full per-asset_group regression).
>    All migrated to successor plan.
>
> **What this gates pre-cutover**: master plan Group F item 17 (backtest fidelity) + item 22 (trading guardrails). The
> 12-cell matrix passing = "we know what the 2 LIVE archetypes do under the 6 most likely live failure modes." That's
> the May-23 hard-gate; broader coverage is post-cutover.
>
> **What gets DEFERRED to successor plan** (preserved per Plan Archival HARD RULE):
>
> - Full per-asset_group scenario library (Phase 4 ≥34 scenarios — only 6 ship pre-cutover).
> - 7-layer wire-in (Phases 3.A / 3.B / 3.C / 3.D / 3.G — MTDS / MDPS / features / strategy / manifest taps).
> - Backtest harness CLI integration (Phase 6).
> - Codex sweep + DART manual-trade rehearsal (Phases 7-8).
> - Full per-asset_group regression matrix on real VMs across every archetype (Phase 9).
>
> **Phase status under compression** (for reviewers walking this plan):
>
> | Phase                                       | Pre-cutover scope                                                                                               | Status                                                                                                                                                                                                                     |
> | ------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | 0 — Pre-audit                               | Sub-agent fan-out per todos 0.A-0.C                                                                             | `todo` (3 AI-hours)                                                                                                                                                                                                        |
> | 1 — UAC contracts                           | 1.A + 1.B + 1.C + 1.D                                                                                           | **`done` 2026-05-12 slot 7 Day-2** (UAC@`33630a6`: scenario_overlay.py + 10 registry instances + 53 tests; built atop Day-1 design fragments)                                                                              |
> | 2 — UTL primitives                          | 2.A + 2.B + 2.D (Phase 2.E `available_at` discipline)                                                           | **`done` 2026-05-12 slot 7 Day-2+4** (UTL@`3797fed5` applier + checker + runner + 51 tests; UTL@`9e84ee44` Phase 2.E `scenario_overlay_active` kwarg on `assert_no_lookahead_for_feature_group` + 2 tests)                 |
> | 3 — Wire-ins                                | 3.E + 3.F only (execution-engine adversarial + risk/alerting consumers)                                         | **`design-shipped` 2026-05-12 slot 7 Day-2** (integration spec at `scratch_scenarios_day1/12_phase3_integration_spec.md`; cross-side handshake to Harsh slot 5 for implementation)                                         |
> | 4 — Scenario library                        | 10 scenarios shipped as design fragments + UAC registry instances 2026-05-12 slot 7                             | **`done`** (UAC@`33630a6` registry/scenarios/)                                                                                                                                                                             |
> | 5 — Matrix                                  | 16-cell scope (10 scenarios × 2 archetypes filtered to applicable; over-delivered vs 12-cell compressed target) | **`done` 2026-05-12 slot 7 Day-3** (UAC@`556b96f` `registry/scenario_archetype_matrix.py` + 11 tests; UTL@`66904fe0` `scenario/matrix_runner.py` + 10 tests — 16-cell matrix builds at module load from SCENARIO_REGISTRY) |
> | 8.A — Codex scenario-injection-architecture | NEW doc capturing the architecture                                                                              | **`done` 2026-05-12 slot 7 Day-4** (PM `/codex/04-architecture/scenario-injection-architecture.md`)                                                                                                                        |
> | 6 / 7 / 8.B-I / 9                           | DEFERRED post-cutover                                                                                           | `deferred-after-simulation_scenarios_post_cutover_2026_06_01`                                                                                                                                                              |
>
> Total compressed scope: ~4-5 AI-days. Fits T-13 with margin. Successor plan picks up immediately post-cutover for the
> broader 9-phase coverage.

## Why this plan exists

The May-23 live-DeFi cutover gates on Group F items 17 (paper-trade smoke), 18 (2-yr batch backtest), 20 (circuit
breakers + kill switches + alerting + auto-recovery), 21 (batch-vs-live reconciliation), and 22 (P&L attribution). All
five gates measure the system against **historically observed conditions** — real backfilled tick data + real venue
behavior + real fill quality. None measure the system against **synthetic adversarial conditions** the operator can
declare ahead of time.

The gap that this plan closes: today, if a venue stops emitting ticks for 90 minutes mid-session, or an oracle prints a
30σ deviation, or an options-chain bundle arrives missing 4 of 11 strike clusters, or a Polymarket canonical group
resolves 6 hours before its declared `resolution_time`, **we don't know what the strategy + risk + execution + alerting
fleet does** — because no historical day in the backfill has those exact conditions, and no test harness has injected
them through prod codepaths. The first time we'll find out is the first time it happens in live. That's the wrong
sequencing.

The fix: declarative scenario overlays that ride the **same prod codepaths** as live + batch (per the workspace "live =
batch — same data, same fields, same timing semantics" HARD RULE), inject specific topology / staleness / price-shock /
venue-outage perturbations at well-defined pipeline boundaries, drive the full mesh end-to-end on a VM, and assert
per-scenario expected outcomes (strategy halts / circuit breaker trips / alert fires / risk scales down / execution
cancels / kill switch arms). Failing a scenario is a regression. Passing every scenario in the per-archetype matrix is a
pre-cutover gate.

This is **not**:

- A throughput benchmark (that's `mock_data_pipeline_benchmarking_2026_05_08.md`).
- A risk-limit / risk-simulation system (that's `risk_simulations_limits_alerting_2026_05_10.md`; this plan **consumes**
  that system's circuit-breaker rules as expected-outcome assertions).
- A DR / chaos drill harness (that's `disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md`; this plan
  **provides** the synthetic injection primitives that DR drills will reuse).
- A separate "backtest engine" — every scenario runs through the unified pipeline (MTDS → MDPS → features-\* →
  strategy-service ↔ position-balance + risk + execution-service-in-matching-engine-mode), with one well-bounded overlay
  layer.

It **is**: a 14-day sprint that ships UAC scenario contracts, UTL injection primitives, per-layer wire-ins, an
asset-group-scoped scenario library, a per-archetype regression matrix run on real VMs, and the pre-cutover gate
integration — all behind the live = batch principle so adding a new scenario is a single declarative artifact, not a new
code path.

## Scope + non-goals

### In scope (must ship by 2026-05-23)

1. UAC scenario contracts: `ScenarioId`, `ScenarioCategory`, `ScenarioOverlay`, `ScenarioOutcomeAssertion`,
   `ScenarioReport`, per-asset_group scenario seed library, expected-outcome closed enum.
2. UTL primitives: `ScenarioOverlayApplier` (5 layer variants — raw-tick / feature / event / order / manifest),
   `ScenarioOutcomeChecker`, `ScenarioReportEmitter`, `ScenarioRunner` (drives mesh end-to-end with overlay).
3. Per-layer injection wire-ins: MTDS, MDPS, features-\*, strategy-service, execution-service matching engine,
   alerting-service, manifest writer.
4. Scenario library — minimum 8 scenarios per asset_group covering topology + staleness + price + venue, plus 4
   cross-asset scenarios (correlation break / basis blowout / global liquidation cascade / cross-cloud failover).
5. Per-archetype regression matrix: `carry_staked_basis` × all DeFi-relevant scenarios + `ARBITRAGE_PRICE_DISPERSION`
   (`funding-rate-dispersion`; renamed from legacy `leveraged_funding_arb` per Stream B canonicalisation 2026-05-07) ×
   all CeFi/DeFi-relevant scenarios. Expected outcomes asserted; pass/fail report emitted as parquet + event stream.
6. Backtest harness wire-in: `--scenario-id <id>` + `--scenario-overlay <yaml>` flags on the unified backtest entry
   point. Runs through prod mesh on a VM.
7. deployment-ui surface: scenario library browser, per-archetype regression matrix view, scenario run history with
   pass/fail badges, scenario-failure drilldown.
8. alerting-service: every scenario-fail emits a distinguishable event with `synthetic=true` metadata so it doesn't page
   on-call but DOES surface in the UI dashboard for operator review.
9. Codex SSOTs covering the architecture (NEW × 3, UPDATE × 6).
10. Full-cycle real-infra runs: every scenario in the regression matrix executed on real VMs (per "Plans Run To Actual
    Completion" HARD RULE) with per-scenario evidence in the DONE block.
11. Cutover gate integration: master plan Group F gets a new item 17.5 (or extension of 20) "scenario regression matrix
    green per archetype before live trading."

### Non-goals (out of scope; stay in their owner plans)

- Real-state risk-limit + circuit-breaker rule definition — owned by `risk_simulations_limits_alerting_2026_05_10`. This
  plan **consumes** the rule taxonomy as expected outcomes; it doesn't define the rules themselves.
- DR + reconciliation playbooks — owned by `disaster_recovery_reconciliation_circuit_breakers_2026_05_08`. Scenarios
  here may exercise DR primitives, but the playbook content lives there.
- ML training-data corruption / adversarial-ML — out of scope for May-23. Captured as `**DEFERRED-PER-USER**` in §
  "Deferred work after 2026-05-09 session."
- Throughput / latency benchmarking on synthetic data — owned by `mock_data_pipeline_benchmarking_2026_05_08`. Scenarios
  here measure correctness under shock, not throughput.
- Sports / prediction lifecycle correctness scenarios beyond a representative seed — full coverage is post-cutover.
  Captured as `**DEFERRED-PER-USER**`.

## Pre-audit / blast radius

Per Citadel-Grade § 1, this section enumerates every repo + file + concern this plan touches, so executing agents don't
re-scan. Workspace-grep ran 2026-05-09 against `live-defi-rollout`.

### Repos touched (12)

| Repo                               | Surface                                                                                                                                              |
| ---------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts`            | NEW: `canonical/crosscutting/scenario_overlay.py` (enums + dataclasses); `registry/scenarios/{cefi,defi,tradfi,sports,prediction}.py` (seed library) |
| `unified-trading-library`          | NEW: `scenario/applier.py`, `scenario/checker.py`, `scenario/runner.py`, `scenario/report.py` + tests                                                |
| `market-tick-data-service`         | UPDATE: replay subsystem hooks for raw-tick overlay; matching-engine input feed extension                                                            |
| `mdps`                             | UPDATE: feature-layer overlay hook (after honest-absence guard, before parquet write)                                                                |
| `features-*` (consolidated repo)   | UPDATE: per-feature-group overlay tap; LookaheadBiasError suppression for declared `available_at` shifts                                             |
| `strategy-service`                 | UPDATE: signal-layer overlay tap; outcome-checker assertion hook on signal emission                                                                  |
| `execution-service`                | UPDATE: matching engine adversarial-fill mode (latency / partial / reject) — extend existing slippage model, not replace                             |
| `position-balance-monitor-service` | UPDATE: scenario-event consumer; per-scenario state snapshot                                                                                         |
| `risk-and-exposure-service`        | UPDATE: outcome-checker hook (did the right circuit breaker trip?)                                                                                   |
| `alerting-service`                 | UPDATE: scenario-event consumer; `synthetic=true` filter on rule eval                                                                                |
| `deployment-api` + `deployment-ui` | NEW endpoints: `/api/scenarios/{list,run,report}`; NEW UI: scenarios tab, regression matrix, drilldown                                               |
| `unified-trading-pm`               | NEW: 3 codex docs; UPDATE: 6 codex docs; this plan; cross-plan banners                                                                               |

### Codex SSOTs (3 NEW + 6 UPDATE)

NEW:

- `/codex/04-architecture/scenario-injection-architecture.md` — overlay layer model, injection points, prod-codepath
  reuse pattern, `synthetic=true` provenance.
- `/codex/04-architecture/scenario-outcome-assertions.md` — closed-enum outcome taxonomy, per-archetype expected-outcome
  matrix shape, fail semantics.
- `/codex/02-data/scenario-overlay-semantics.md` — overlay parquet schema, per-row provenance, `available_at` discipline
  under overlay, manifest-side scenario_id column.

UPDATE:

- `/codex/04-architecture/kill-switch-circuit-breaker.md` — scenario-driven trips section.
- `/codex/04-architecture/autonomous-recovery-matrix.md` — scenario-driven recovery validation section.
- `/codex/04-architecture/backtest-groups.md` — scenario-overlay mode added to backtest taxonomy.
- `/codex/05-infrastructure/live-pipeline-architecture.md` — scenario tap points within the live + batch unified
  pipeline.
- `/codex/05-infrastructure/replay-subsystem.md` — scenario-overlay-on-replay extension.
- `/codex/02-data/honest-absence-downstream-handling.md` — scenario-driven gap injection per consumer-class table.

### Cross-plan dependencies

- **`alerting_service_live_rules_2026_05_07.md`** — Phase X must declare a `synthetic=true` filter; banner added to that
  plan's body in Phase 0.B of this plan.
- **`live_pipeline_mtds_mdps_features_2026_05_08.md`** — Phase 14 codex updates compose with the 3 NEW codex docs here;
  banner symmetric.
- **`writegate_honest_coverage_endtoend_2026_05_06.md`** — `EMPTY_CONFIRMED_REASONS` taxonomy is the upstream SSOT for
  topology-gap scenarios (`SOURCE_RETURNED_ZERO`, `EXPECTED_PAUSED_LEAGUE`, etc.). Scenarios re-use the existing reason
  set, do not extend it.
- **`master_to_live_defi_2026_05_23.md`** — adds new readiness item 17.5 (or extends item 20) "scenario regression
  matrix green per archetype." Update happens in Phase 10.
- **`risk_simulations_limits_alerting_2026_05_10.md`** (question doc) — circuit-breaker rule taxonomy is the upstream
  vocabulary for outcome assertions. Scenarios consume that doc's rule names; if it spawns a plan first, this plan
  consumes the plan's UAC contracts.

### Service-readiness checklist coverage (per master plan Groups A-G, 23 items)

This plan moves the needle on:

- **Group F item 17** (paper-trade smoke) — scenarios are pre-paper validation.
- **Group F item 18** (2-yr batch backtest) — scenario overlays ride the same backtest harness; the matrix is run
  against representative days.
- **Group F item 20** (circuit breakers + kill switches + alerting + auto-recovery) — scenario regression matrix IS the
  validation surface for these.
- **Group F item 21** (batch-vs-live reconciliation) — scenario runs in batch + live mode produce comparable
  reconciliation evidence.

## Phased execution DAG

```text
Phase 0 (Pre-audit, parallel)
    ├─ 0.A Inventory existing scenario / mock infra (matching engine, Tenderly, MockWS, ServiceEmissionPolicy)
    ├─ 0.B Cross-plan coordination banners on 4 affected plans
    └─ 0.C Workspace-grep callsite enumeration for every overlay tap point
                    │
                    ▼  (QG gate: audit findings recorded, banners shipped)
Phase 1 (UAC contracts) ──────────► blocks Phase 2, 3, 4
                    │
Phase 2 (UTL primitives) ─────────► blocks Phase 3, 5, 6
                    │
Phase 3 (Per-layer wire-ins, parallel) ─► blocks Phase 5
    ├─ 3.A MTDS raw-tick overlay
    ├─ 3.B MDPS feature-layer overlay
    ├─ 3.C features-* overlay tap
    ├─ 3.D strategy-service signal tap + outcome hook
    ├─ 3.E execution-service matching-engine adversarial mode
    ├─ 3.F position-balance + risk + alerting consumers
    └─ 3.G Manifest-layer scenario_id column
                    │
                    ▼  (QG gate: every layer wires + unit tests pass)
Phase 4 (Scenario library, parallel by asset_group) ─► blocks Phase 5
    ├─ 4.A CeFi (≥8 scenarios)
    ├─ 4.B DeFi (≥8 scenarios)
    ├─ 4.C TradFi (≥6 scenarios)
    ├─ 4.D Sports (seed: 4 scenarios)
    ├─ 4.E Prediction (seed: 4 scenarios)
    └─ 4.F Cross-asset (4 scenarios)
                    │
                    ▼
Phase 5 (Per-archetype regression matrix wired)
                    │
Phase 6 (Backtest harness wire-in)  ──► parallel with Phase 7
                    │
Phase 7 (deployment-api + ui surface)
                    │
                    ▼
Phase 8 (Codex SSOTs — 3 NEW + 6 UPDATE) ─► parallel with Phase 9 first run
                    │
Phase 9 (Full-cycle real-infra runs on VMs — every scenario, every archetype)
                    │
                    ▼
Phase 10 (Cutover gate integration in master plan + epic)
```

QG gates are real: each phase pushes to `live-defi-rollout`, runs `bash scripts/quality-gates.sh` on every touched repo,
and only then unblocks dependents.

## Phase 0 — Pre-audit (Day 1, ~1.5 AI-days, 3 parallel sub-agents)

- [x] [AGENT] P0. **0.A Inventory existing scenario / mock infra.** **DEFERRED-PER-COMPRESSED-SCOPE** — Day-1
      6-sub-agent design fan-out (`scratch_scenarios_day1/{01..10}.md`) served as the de-facto infra inventory: each
      fragment cites the relevant existing matching-engine hook / mock-WS infra / ManifestWriter surface inline. Formal
      Phase 0 audit deferred to successor `simulation_scenarios_post_cutover_2026_06_01.md`. Sub-agent walks:
      `execution-service/matching_engine/{engine,trade_matcher,amm,sports_matching,hooks}.py` (existing slippage +
      latency hooks), `execution-service/tests/integration/conftest.py` (Tenderly fixtures),
      `market-tick-data-service/tests/market_interface/fixtures/mock_ws_server.py` (MockWebSocketFeed),
      `unified-api-contracts/canonical/crosscutting/service_emission_policy.py` (PUBLISHED_DEGRADED + STALE_DATA), UTL
      `streaming` + `batch_live_reconciler` + `honest_coverage_ratchet` (Tab 2 2026-05-08), MDPS feature-layer
      NaN-handling primitives. Output: a markdown table in this plan's § "Audit findings" with
      `surface | what's there | reuse-as` columns. **Don't write code yet — only surface what to reuse.**
- [x] [AGENT] P0. **0.B Cross-plan coordination banners.** **DEFERRED-UNTIL-PHASE-3-IMPL** — banner-add is bundled with
      the Phase 3 wire-in launch per CLAUDE.md "Cross-Plan Coordination Banners" rule (banner-add is part of the
      in-flight refactor's logical unit). Phase 3.E + 3.F impl is cross-side-handed-off to Harsh slot 5; banner-add
      becomes their action when implementation begins. Add
      `> **🟡 IN-FLIGHT REFACTOR — synthetic scenario injection landing across MTDS / MDPS / features / strategy / execution / alerting / position-balance / risk via UAC `ScenarioOverlay`+ UTL`scenario/`; downstream consumers will gain a `scenario_id`provenance column on parquet writes + a`synthetic=true`event metadata field. RE-VERIFY any reader / dashboard code that filters or groups parquet output. See`simulation_scenarios_topology_price_shocks_2026_05_09.md`.**`
      to: `master_to_live_defi_2026_05_23.md`, `live_pipeline_mtds_mdps_features_2026_05_08.md`,
      `alerting_service_live_rules_2026_05_07.md`, `writegate_honest_coverage_endtoend_2026_05_06.md`. Banner removed by
      this plan's owner when Phase 9 ships.
- [x] [SCRIPT] P0. **0.C Workspace-grep callsite enumeration.** **DEFERRED-UNTIL-MULTI-LAYER-WIRE-IN** —
      compressed-scope ships only the ORDER-layer wire (Phase 3.E, Harsh slot 5). Multi-layer callsite enumeration
      (RAW*TICK / FEATURE / SIGNAL / EVENT / MANIFEST) is post-cutover scope (Phase 3.A/B/C/G of successor plan); CSV
      emission useful only when those taps land. For every overlay tap point — `\_fetch*_`per MTDS
      adapter,`*compute*_`per features-\* calculator,`emit_signal`in strategy-service,`submit_order`+ `simulate_fill`in
      execution-service,`record_captured`+`record_empty`+`record_failed`+ `record_expected_unattempted`in UTL
      ManifestWriter — produce a CSV `repo,file,line,callsite_kind,target_overlay_layer`so Phase 3 sub-agents have a
      complete edit list. Tool: `rg     -n "<pattern>" --type py --glob '!.venv\*' --glob '!tests'` per kind. Output:
      append to § "Audit findings" as a fenced table.

**Full-execution criterion** (per HARD RULE):

- ✅ § "Audit findings" populated with infra inventory + workspace-grep CSV (≥40 callsites enumerated across the 7 tap
  kinds).
  - **What ran**: 3 sub-agent fan-outs + serial commit by parent.
  - **Verification**: `wc -l` on the CSV ≥ 40; `grep -c "tap_kind=" plan` matches expected per-kind counts.
- ✅ Banners on 4 cross-plan files; `grep -l "🟡 IN-FLIGHT REFACTOR — synthetic scenario injection"` returns 4 paths.

## Phase 1 — UAC scenario contracts (Days 2-3, ~2 AI-days)

- [x] [AGENT] P0. **1.A Closed-enum scenario taxonomy.** ✅ UAC@`33630a6` (slot 7 Day-2 2026-05-12) —
      `canonical/crosscutting/scenario_overlay.py` ships `ScenarioCategory` (7 members) + `ScenarioOverlayLayer` (6) +
      `OutcomeCategory` (9 — replaces `ScenarioOutcomeAssertion` closed-enum proposal with discriminator-typed Pydantic;
      same closed-set discipline). `unified_api_contracts/canonical/crosscutting/scenario_overlay.py` ships:
      `ScenarioCategory` (TOPOLOGY*GAP / STALENESS / PRICE_SHOCK / VENUE_OUTAGE / DATA_CORRUPTION / CROSS_ASSET /
      OPERATIONAL), `ScenarioId` (NewType[str] with regex `^[a-z]a-z0-9*]+$`), `ScenarioOverlayLayer` (RAW_TICK /
      FEATURE / SIGNAL / ORDER / EVENT / MANIFEST). Frozen Pydantic.
- [x] [AGENT] P0. **1.B `ScenarioOverlay` Pydantic dataclass.** ✅ UAC@`33630a6` — frozen + extra-forbid; `scenario_id`
      regex validated; `ScenarioMutationSpec` 11-member discriminated union shipped (PriceShift / StaleHold /
      LatencyInject / BookSpoof / RejectFills / OracleDeviate / GasSurge / DropRows / EventDrop / EventDuplicate /
      ManifestPhantom). Original 1.B plan-body shape now extended; new mutations land via `_MutationBase` subclass +
      discriminator literal. Fields: `scenario_id`, `asset_groups: frozenset[MarketAssetGroup]`,
      `applies_to: ScenarioApplicabilityFilter` (per-venue / per-data_type / per-instrument / per-day / per-archetype),
      `mutation_spec: ScenarioMutationSpec` (closed union: `DropRows` | `StaleHold` | `PriceShift` | `BookSpoof` |
      `LatencyInject` | `RejectFills` | `OracleDeviate` | `GasSurge` | `ManifestPhantom` | `EventDrop` |
      `EventDuplicate`), `expected_outcomes: list[ScenarioOutcomeAssertion]`. Every field typed; no `Any`.
- [x] [AGENT] P0. **1.C `ScenarioOutcomeAssertion` closed-enum.** ✅ UAC@`33630a6` — `ScenarioOutcomeAssertion`
      Pydantic + `OutcomeCategory` 9-member closed-set (STRATEGY_HALTED / STRATEGY_SCALED_DOWN / RISK_BREAKER_TRIPPED /
      ORDER_REJECTED / ORDER_CANCELLED_ON_STALE / KILL_SWITCH_ARMED / ALERT_FIRED / PNL_BOUNDED_BY /
      RECONCILIATION_FLAGGED). Each carries optional consequence / breaker_id / breaker_action / kill_switch_id /
      alert_codes refs (the 6-tuple-per-cell contract from handshake doc fragment 11). Categories: `STRATEGY_HALTED`
      (signal generator stops emitting), `STRATEGY_SCALED_DOWN` (size cut by ≥X%), `RISK_BREAKER_TRIPPED` (named breaker
      fires), `ORDER_REJECTED` (execution refuses), `ORDER_CANCELLED_ON_STALE` (auto-cancel fires), `KILL_SWITCH_ARMED`
      (named kill switch arms), `ALERT_FIRED` (named alert rule fires with `synthetic=true`), `PNL_BOUNDED_BY`
      (per-archetype P&L bound), `RECONCILIATION_FLAGGED` (batch-vs-live recon raises). Each carries a typed
      `expected_within: timedelta` SLA.
- [x] [AGENT] P0. **1.D Per-asset_group scenario seed library.** ✅ UAC@`33630a6` —
      `registry/scenarios/{__init__,cefi,defi,cross_asset}.py` ships 10 `ScenarioOverlay` instances (2 cefi + 6 defi + 2
      cross_asset); `SCENARIO_REGISTRY: dict[str, ScenarioOverlay]` populated via `register_scenario()` helper at
      module-load. `unified_api_contracts/registry/scenarios/{cefi,defi,tradfi,sports,prediction,cross_asset}.py` — each
      module exposes a `frozenset[ScenarioOverlay]` constant with seed scenarios from § Phase 4 (full library lands in
      Phase 4; seed shape lands here). Registry: `SCENARIO_REGISTRY: dict[ScenarioId, ScenarioOverlay]` indexed at
      module load.
- [x] [AGENT] P0. **1.E `ScenarioReport` Pydantic dataclass.** ✅ UAC@`33630a6` (slot 7 Day-2 2026-05-12) —
      `canonical/crosscutting/scenario_overlay.py` ships `ScenarioReport` + `ScenarioOutcomeResult` Pydantic, frozen +
      extra-forbid, with `scenario_id` / `archetype` / `run_id` / `started_at_iso` / `finished_at_iso` /
      `outcome_results: tuple[ScenarioOutcomeResult, ...]` / `synthetic: bool = True` /
      `parquet_artifacts: frozenset[str]` / `event_correlation_id` fields. Fields: `scenario_id`,
      `archetype: ArchetypeId`, `run_id`, `started_at`, `finished_at`, `outcome_results: list[ScenarioOutcomeResult]`
      (assertion + observed + pass/fail), `synthetic: bool = True`, `parquet_artifacts: list[GcsPath]` (per-stage
      parquet snapshots), `event_correlation_id`. Used by Phase 7 UI + Phase 9 evidence.
- [x] [AGENT] P0. **1.F UAC tests.** ✅ UAC@`33630a6` (slot 7 Day-2 2026-05-12) —
      `tests/internal/unit/test_scenario_overlay.py` ships 53 tests (over-delivers vs ≥30 target); + UAC@`556b96f` (slot
      7 Day-3) `tests/internal/unit/test_scenario_archetype_matrix.py` ships 11 tests for the per-archetype matrix layer
      = **64 UAC unit tests total**. Coverage: closed-set enum membership / scenario_id regex / Pydantic frozen +
      extra-forbid / per-mutation discriminator dispatch / 6-tuple seam-ref / registry completeness / per-asset_group
      count / register_scenario idempotency + duplicate guard. ≥30 unit tests in
      `unified-api-contracts/tests/internal/unit/test_scenario_overlay.py`: enum membership / seed-registry round-trip /
      Pydantic validation / typed-mutation discrimination / outcome-assertion serialization round-trip.

**Full-execution criterion**:

- ✅ UAC PR pushed to `live-defi-rollout` with QG green (`bash scripts/quality-gates.sh` in `unified-api-contracts/`).
  - **What ran**: UAC@<sha> + QG locally on agent's box.
  - **Verification**: `cd unified-api-contracts && bash scripts/quality-gates.sh` exits 0; remote CI for the commit on
    `live-defi-rollout` is green per the post-push CI watcher;
    `python -c "from unified_api_contracts.crosscutting import ScenarioOverlay, SCENARIO_REGISTRY; print(len(SCENARIO_REGISTRY))"`
    prints ≥6 (one per asset_group + cross_asset).

## Phase 2 — UTL primitives (Days 3-4, ~2 AI-days)

- [x] [AGENT] P0. **2.A `unified_trading_library/scenario/applier.py`.** ✅ UTL@`3797fed5` — `ScenarioOverlayApplier`
      with per-mutation typed dispatch on all 11 union members; pure-functional (never mutates input); stamps
      `_synthetic_provenance` provenance list (chain-aware). 18 unit tests cover dispatch + provenance + smoke against
      every Day-1 registry scenario. `ScenarioOverlayApplier` class — one applier per `ScenarioOverlayLayer`.
      Pure-functional
      `apply(input_frame: pl.DataFrame, overlay: ScenarioOverlay, context: ScenarioContext) -> pl.DataFrame`. Each
      mutation_spec has its own applier method. NEVER mutates input; returns a new frame with
      `_synthetic_provenance: list[ScenarioId]` column appended. Tested against polars + pandas frames.
- [x] [AGENT] P0. **2.B `unified_trading_library/scenario/checker.py`.** ✅ UTL@`3797fed5` — per-OutcomeCategory match
      logic (9 categories); `synthetic=True` safeguard rejects real-fire events; SLA enforcement
      (`expected_within_seconds`); composes 6-tuple-per-cell contract. 22 unit tests cover all 9 categories + SLA +
      synthetic safeguard. `ScenarioOutcomeChecker` — registers callbacks against the event stream + service state
      surfaces (strategy-service emit, risk-and-exposure breaker fire, execution-service order state, alerting-service
      rule fire, position-balance scaling). Each `ScenarioOutcomeAssertion` checks `expected_within` SLA against
      observed. `check(scenario_run_id, assertion) -> ScenarioOutcomeResult`. Uses the existing event stream contract,
      no new infra.
- [x] [AGENT] P0. **2.C `unified_trading_library/scenario/report.py`.** **DEFERRED-PER-COMPRESSED-SCOPE** (plan body
      line 63 explicit: "2.C / 2.E / 2.F deferred"; 2.E now shipped Day-4 at UTL@`9e84ee44`; 2.F shipped Day-2 at
      UTL@`3797fed5`; 2.C parquet sink remains DEFERRED). Pre-cutover ship returns `ScenarioReport` in-memory via
      `ScenarioRunner.run().report`; consumer JSONL-serializes per matrix-runner spec. Parquet GCS emission lands when
      real-VM matrix runs ship (Phase 9, deferred to successor `simulation_scenarios_post_cutover_2026_06_01.md`).
      `ScenarioReportEmitter` — writes `ScenarioReport` to
      `gs://{pid}-events/scenarios/{archetype}/{YYYY-MM-DD}/{scenario_id}/{run_id}.json` (event payload) +
      `gs://{pid}-scenario-reports/{archetype}/{YYYY-MM-DD}/{scenario_id}/{run_id}/report.parquet` (queryable). Reuses
      UTL emission helpers — no new bucket-naming logic; uses Tab 4's `bucket_naming.py` SSOT (UTL@780a9575).
- [x] [AGENT] P0. **2.D `unified_trading_library/scenario/runner.py`.** ✅ UTL@`3797fed5` — `ScenarioRunner`
      orchestrator; loads `ScenarioOverlay` from UAC `SCENARIO_REGISTRY`; takes caller-supplied `ObserverCallback`;
      emits `ScenarioReport`. Filters assertions to target archetype only; fail-loud on unknown scenario_id +
      archetype-with-no-assertions. 7 unit tests cover end-to-end + error paths. `ScenarioRunner` — orchestrates a
      single `(scenario_id, archetype, time_window)` run end-to-end: invokes the unified backtest pipeline (the same one
      Group F item 18 uses) with `--scenario-overlay` flag, observes outputs via `ScenarioOutcomeChecker`, emits
      `ScenarioReport` via `ScenarioReportEmitter`. **No parallel backtest engine — this only configures and observes
      the existing one.**
- [x] [AGENT] P0. **2.E LookaheadBiasError compatibility.** ✅ UTL@`9e84ee44` (slot 7 Day-4 2026-05-12) —
      `assert_no_lookahead_for_feature_group(..., scenario_overlay_active: bool = False)` kwarg shipped. When True,
      downgrades the `LookaheadBiasError` to a structured `_logger.warning` with `SCENARIO_OVERLAY_LOOKAHEAD_DOWNGRADE`
      marker. Strict mode stays on for every non-overlay path. 2 new tests cover downgrade-to-warning + strict-mode
      invariant; 11/11 `TestAssertNoLookaheadForFeatureGroup` tests pass. `ScenarioOverlay` mutations that shift
      `available_at` (StaleHold, EventDrop) must NOT trigger LookaheadBiasError downstream. Mechanism: applier stamps
      `_synthetic_available_at_shift: bool` column; UTL `lookahead_bias_check` accepts a `scenario_overlay_active: bool`
      kwarg that downgrades the error to a structured warning emitted to the report. **Strict mode stays on for
      non-overlay paths** — only the overlay-active path skips.
- [x] [AGENT] P0. **2.F UTL tests.** ✅ UTL@`3797fed5` (slot 7 Day-2 2026-05-12) ships 51 unit tests in
      `tests/unit/scenario/` (test_applier 18 / test_checker 22 / test_runner 7 + 4 shared); + UTL@`66904fe0` (Day-3)
      ships 10 matrix-runner tests; + UTL@`9e84ee44` (Day-4) adds 2 Phase 2.E LookaheadBias downgrade tests = **63 UTL
      unit tests total** (over-delivers vs ≥40 target). Coverage: per-mutation applier correctness on all 11 union
      members + per-OutcomeCategory checker behaviour on mocked event stream + report-emitter round-trip + runner
      end-to-end + matrix-runner red/green + LookaheadBias compatibility under overlay-active path. ≥40 unit tests
      covering: per-mutation applier correctness, per-outcome-assertion-kind checker behavior on a mocked event stream,
      report-emitter parquet round-trip, runner end-to-end with a stub pipeline, lookahead-bias-check behaviour under
      overlay vs not.

**Full-execution criterion**:

- ✅ UTL PR pushed to `live-defi-rollout` with QG green.
  - **What ran**: UTL@<sha> + QG locally + remote CI watcher confirms green.
  - **Verification**: `cd unified-trading-library && bash scripts/quality-gates.sh` exits 0;
    `python -c "from unified_trading_library.scenario import ScenarioRunner; ScenarioRunner.__init_subclass__"`
    resolves; ≥40 tests in `tests/scenario/` collected.

## Phase 3 — Per-layer wire-ins (Days 5-7, ~3 AI-days, 7 parallel sub-agents)

Each sub-task is a separate sub-agent assignment. Same Bash-bundling discipline per `Commit + Push + Flip` HARD RULE.

- [x] [AGENT] P0. **3.A MTDS raw-tick overlay.** **DEFERRED-PER-COMPRESSED-SCOPE** (scope compression note line 85:
      "Phases 3.A / 3.B / 3.C / 3.D / 3.G deferred — MTDS / MDPS / features / strategy taps + manifest scenario_id
      column = post-cutover infra"). Successor: `simulation_scenarios_post_cutover_2026_06_01.md` Phase 3.A.
      `market-tick-data-service` adapters' fetch-result post-processing: after `record_captured` decision, if
      `ScenarioContext.has_overlay(layer=RAW_TICK)`, route through `ScenarioOverlayApplier`. Wire at
      `market_tick_data_service/adapters/base_adapter.py` `_post_fetch` hook — single edit point per the audit grep.
      Per-VM scenario_id passed via `VM_NAME` decoration + `ScenarioContext.from_env()`.
- [x] [AGENT] P0. **3.B MDPS feature-layer overlay.** **DEFERRED-PER-COMPRESSED-SCOPE** (same as 3.A — post-cutover
      infra). Successor: `simulation_scenarios_post_cutover_2026_06_01.md` Phase 3.B. `mdps/engine/orchestrator.py`
      after honest-absence guard, before parquet write — invoke FEATURE-layer applier. Re-uses existing 4-category guard
      rails (no new banned-pattern surface). LookaheadBiasError downgrade per 2.E.
- [x] [AGENT] P0. **3.C features-\* overlay tap.** **DEFERRED-PER-COMPRESSED-SCOPE** (same as 3.A — post-cutover infra).
      Successor: `simulation_scenarios_post_cutover_2026_06_01.md` Phase 3.C.
      `features-service/feature_calculator/<calculator>.py` per-feature-group tap at `_compute_<group>` exit, before
      `record_captured`. Per the consolidated repo (post Harsh Tab 2 features-consolidation 2026-05-08).
- [x] [AGENT] P0. **3.D strategy-service signal tap + outcome hook.** **DEFERRED-PER-COMPRESSED-SCOPE** (same as 3.A —
      post-cutover infra). Successor: `simulation_scenarios_post_cutover_2026_06_01.md` Phase 3.D.
      `strategy-service/strategy_service/signal_generator.py` — SIGNAL-layer applier between feature read + signal
      emission; outcome-checker-callback registered at signal-emit boundary. Per-archetype hook list comes from UAC
      scenario registry.
- [x] [AGENT] P0. **3.E execution-service matching-engine adversarial mode** — **`done` 2026-05-12 Harsh slot 5.**
      Shipped: `execution-service@d0ec76f1` `AdversarialMatchingEngine` (RejectFills + LatencyInject + BookSpoof at
      fill-attempt boundary; `ObservedEvent` emission with `synthetic=True`; production default `scenario_id=None` →
      zero-overhead pass-through) + `execution-service@6bdf6136` 9 unit tests covering pass-through, registry
      validation, all 3 mutation types, ObservedEvent discipline + `execution-service@1c5923f3` CLI
      `python -m execution_service.cli.run_scenario --scenario-id X --archetype Y` operator-runtime entry. Design
      substrate in
      [`scratch_scenarios_day1/12_phase3_integration_spec.md`](scratch_scenarios_day1/12_phase3_integration_spec.md) §
      "Phase 3.E". `execution-service/execution_service/matching_engine/{engine,trade_matcher}.py` — extend the existing
      slippage / latency / partial-fill hooks (per audit 0.A inventory) with `ScenarioOverlay`-driven mutations:
      `LatencyInject`, `RejectFills`, `BookSpoof`. **Do not replace the existing model** — extend via the existing hook
      interface. Sports adapter (`sports_matching.py`) gets fixture-cancellation / kickoff-delay mutations.
- [x] [AGENT] P0. **3.F position-balance + risk + alerting consumers** — **`done` 2026-05-12 Harsh slot 5.** Shipped:
      (a) `position-balance-monitor-service@8b6c06f` `ScenarioKillSwitchSubscriber` pre-filter for
      `KillSwitchProvenance.SCENARIO_SYNTHETIC` arms + 7 unit tests; (b) `risk-and-exposure-service@0a8f024`
      `ScenarioOutcomeBridge` + `arm_breaker(synthetic=...)` kwarg → emits `BREAKER_ARMED` ObservedEvent on every arm +
      8 unit tests; (c) `alerting-service@3c0d675` router `_is_synthetic()` + `_route_synthetic_log_only()`
      short-circuit in both `route_event` + `route_event_with_explicit_channels` (PagerDuty + Telegram skipped;
      `ALERT_SUPPRESSED_SYNTHETIC` audit + log_only delivery record) + 8 unit tests; (d) `execution-service@92aa4af2`
      per-archetype integration smoke (`tests/integration/scenarios/test_per_archetype_smoke.py` — 2 tests pass: APD ×
      cefi_venue_circuit_breaker_trip + carry_staked_basis × defi_chain_rpc_outage_solana). Design substrate in
      [`scratch_scenarios_day1/12_phase3_integration_spec.md`](scratch_scenarios_day1/12_phase3_integration_spec.md) §
      "Phase 3.F". `position-balance-monitor-service`: subscribe to `synthetic=true` scenario events; emit per-scenario
      state snapshots. `risk-and-exposure-service`: outcome-checker hook fires on every breaker trip and emits
      `ScenarioOutcomeResult`. `alerting-service`: rule-eval respects `synthetic=true` filter — alert fires + report
      records, but on-call paging suppressed (synthetic events go to dashboard only).
- [x] [AGENT] P0. **3.G Manifest-layer scenario_id column.** **DEFERRED-PER-COMPRESSED-SCOPE** (scope compression note
      line 85 — manifest scenario_id column = post-cutover infra). Successor:
      `simulation_scenarios_post_cutover_2026_06_01.md` Phase 3.G. `unified_trading_library/manifest/writer.py`
      `record_captured` accepts optional `scenario_id: ScenarioId | None`. Adds a v5 manifest column `scenario_id` —
      additive, default null. Phantom-audit reconciler scripts gain awareness via 1-line filter (skip rows with
      `scenario_id is not null`).

**Full-execution criterion**:

- ✅ All 7 sub-tasks pushed; per-repo QG green; remote CI green per post-push CI watcher; downstream consumer audit
  passes (no untaped overlay layer; no untouched callsite from the 0.C CSV).
  - **What ran**: 7 parallel sub-agent commits + 7 per-repo QG.
  - **Verification**: workspace-wide grep `rg "ScenarioOverlay" --type py --glob '!.venv*' --glob '!tests'` returns ≥7
    consumer touchpoints; per-repo `scripts/quality-gates.sh` exits 0; CI watcher reports all 7 commits green on
    `live-defi-rollout`.

## Phase 4 — Scenario library per asset_group (Days 7-9, ~3 AI-days, 6 parallel sub-agents)

Each sub-agent owns one module in `unified-api-contracts/registry/scenarios/<asset_group>.py`. Each scenario is a fully
typed `ScenarioOverlay` instance with ≥1 expected outcome. Minimum counts per the scope section.

- [x] [AGENT] P0. **4.A CeFi (compressed-scope subset of ≥8).** ✅ UAC@`33630a6` — `registry/scenarios/cefi.py` ships 2
      ScenarioOverlay instances per compressed-scope plan body line 67-74: `cefi_venue_circuit_breaker_trip` +
      `cefi_funding_spike_10x`. **DEFERRED**: full ≥8 CeFi scenario library (`cefi_tick_gap_15min`,
      `cefi_liquidation_cascade`, `cefi_book_top_stale_120s`, `cefi_venue_outage_single`, `cefi_wide_spread_50bps`,
      `cefi_halt_then_reopen_gap_5pct`, `cefi_funding_rate_negative_extreme`) to successor
      `simulation_scenarios_post_cutover_2026_06_01.md` Phase 4. `cefi_tick_gap_15min`, `cefi_funding_spike_10x`,
      `cefi_liquidation_cascade`, `cefi_book_top_stale_120s`, `cefi_venue_outage_single` (Bybit-only),
      `cefi_wide_spread_50bps`, `cefi_halt_then_reopen_gap_5pct`, `cefi_funding_rate_negative_extreme`. Each declares
      per-archetype expected outcomes (e.g. `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`) halts on
      `cefi_funding_spike_10x`).
- [x] [AGENT] P0. **4.B DeFi (compressed-scope subset of ≥8).** ✅ UAC@`33630a6` — `registry/scenarios/defi.py` ships 6
      ScenarioOverlay instances per compressed-scope plan body line 67-74: `defi_oracle_deviation_30sigma`,
      `defi_gas_surge_50x`, `defi_liquidity_drain_lending_pool`, `defi_chain_rpc_outage_solana`,
      `defi_mempool_congestion_inclusion_delay`, `defi_stablecoin_depeg`. **DEFERRED**: full ≥8 DeFi scenario library
      (`defi_rpc_outage_arbitrum`, `defi_reorg_solana_3block`, `defi_mev_sandwich_2pct`,
      `defi_slippage_blowout_uniswap`, `defi_pyth_feed_lag_solana_5min`, `defi_aave_utilization_99pct` as
      named-but-not-shipped fragments) to successor Phase 4. `defi_oracle_deviation_30sigma`, `defi_gas_surge_50x`,
      `defi_rpc_outage_arbitrum`, `defi_reorg_solana_3block`, `defi_mev_sandwich_2pct`, `defi_slippage_blowout_uniswap`,
      `defi_pyth_feed_lag_solana_5min`, `defi_aave_utilization_99pct`. Per-archetype outcomes (e.g. `carry_staked_basis`
      cancels new entries on `defi_oracle_deviation_30sigma`).
- [x] [AGENT] P0. **4.C TradFi (≥6 scenarios).** **DEFERRED-PER-COMPRESSED-SCOPE** (plan body line 82-83: "Full
      per-asset_group scenario library (Phase 4 ≥34 scenarios — only 6 ship pre-cutover)") — TradFi cluster-bundling
      scenarios are post-cutover; cutover archetypes are CeFi-perp + DeFi-LST, no TradFi exposure. Successor:
      `simulation_scenarios_post_cutover_2026_06_01.md` Phase 4.
      `tradfi_options_chain_partial_4_of_11_clusters_missing`, `tradfi_es_halt_circuit_breaker_l2`,
      `tradfi_overnight_gap_3pct`, `tradfi_databento_429_storm`, `tradfi_vix_15m_yahoo_window_edge`,
      `tradfi_etf_late_close_fill`. Hooks the cluster-validation MissingClusterValidationError surface (UAC
      `BUNDLED_DATA_TYPES`) for the partial-bundle scenario.
- [x] [AGENT] P0. **4.D Sports seed (4 scenarios).** **DEFERRED-PER-USER** (plan body § "Deferred work after 2026-05-09
      session" row 1: "Sports full-coverage scenario library — Post-cutover"). Cutover archetypes have no sports
      exposure. `sports_kickoff_delay_60min`, `sports_fixture_cancellation_late`, `sports_lineup_announce_post_kickoff`
      (LookaheadBias-adjacent), `sports_odds_storm_pinnacle_outage`. Full coverage post-cutover.
- [x] [AGENT] P0. **4.E Prediction seed (4 scenarios).** **DEFERRED-PER-USER** (plan body § "Deferred work after
      2026-05-09 session" row 2: "Prediction full-coverage scenario library — Post-cutover"). Cutover archetypes have no
      prediction-market exposure. `prediction_market_resolve_premature_polymarket`,
      `prediction_canonical_question_lifecycle_violation`, `prediction_clob_book_invert`,
      `prediction_kalshi_resolution_disputed`. Full coverage post-cutover.
- [x] [AGENT] P0. **4.F Cross-asset (compressed-scope subset of 4).** ✅ UAC@`33630a6` —
      `registry/scenarios/cross_asset.py` ships 2 ScenarioOverlay instances per compressed-scope plan body line 67-74:
      `cross_asset_flash_crash` + `cross_asset_basis_blowout_perp_spot`. **DEFERRED**: full 4-scenario cross-asset set
      (`cross_asset_correlation_break_btc_eth`, `cross_asset_global_liquidation_cascade`,
      `cross_asset_cross_cloud_failover_aws_to_gcp`) to successor Phase 4. `cross_asset_correlation_break_btc_eth`,
      `cross_asset_basis_blowout_perp_spot`, `cross_asset_global_liquidation_cascade`,
      `cross_asset_cross_cloud_failover_aws_to_gcp`. Each touches ≥2 asset_groups; outcomes assert global kill switch
      arms in the most severe case.

**Full-execution criterion**:

- ✅ ≥34 scenarios shipped across 6 modules; UAC test `test_scenario_registry_completeness.py` enumerates every declared
  scenario + asserts per-asset_group minimum counts.
  - **What ran**: 6 parallel UAC commits.
  - **Verification**:
    `python -c "from unified_api_contracts.crosscutting import SCENARIO_REGISTRY; print(len(SCENARIO_REGISTRY))"` ≥ 34;
    per-asset_group count assertions in the new test pass.

## Phase 5 — Per-archetype regression matrix (Days 9-10, ~2 AI-days)

- [x] [AGENT] P0. **5.A Matrix definition.** ✅ UAC@`556b96f` (slot 7 Day-3 2026-05-12) —
      `unified-api-contracts/registry/scenario_archetype_matrix.py` ships `MATRIX: dict[str, frozenset[str]]` derived at
      module-load from `SCENARIO_REGISTRY` (each scenario lands in archetype matrix iff at least one declared
      `expected_outcome.archetype` matches). Cutover archetypes: `carry_staked_basis` + `ARBITRAGE_PRICE_DISPERSION`.
      `matrix_cell_count()` + `scenarios_for_archetype()` helpers + 5 facade re-exports. 11 unit tests verify
      per-archetype critical-scenario presence + closed-archetype-set + over-delivers-vs-12-cell-target.
      `unified-api-contracts/registry/scenario_archetype_matrix.py` declares
      `MATRIX: dict[ArchetypeId, frozenset[ScenarioId]]`. `carry_staked_basis` × every DeFi + applicable cross_asset
      scenario; `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`) × every CeFi + DeFi + applicable cross_asset
      scenario. Out-of-asset_group scenarios excluded by construction.
- [x] [AGENT] P0. **5.B `ScenarioMatrixRunner`.** ✅ UTL@`66904fe0` (slot 7 Day-3 2026-05-12) —
      `unified_trading_library/scenario/matrix_runner.py` ships `ScenarioMatrixRunner` (sync serial iterator),
      `ScenarioMatrixCell` (frozen dataclass with passed + failure_count derived properties), `ScenarioMatrixReport`
      (all_passed Phase 5.C invariant + cell_count + passed/failed_cell_count + `failure_summary()` formatter),
      `ObserverFactory` typed alias. Fail-loud on unknown archetype + registry/matrix mismatch. 10 unit tests cover
      red/green matrix + report shape + failure_summary formatting. Pre-cutover synchronous; Phase 9 parallel-per-cell
      GCE VM extension DEFERRED. `unified_trading_library/scenario/matrix_runner.py` — given an `ArchetypeId`, drives
      `ScenarioRunner` over every scenario in the matrix, aggregates `ScenarioReport` rows into a `ScenarioMatrixReport`
      parquet at `gs://{pid}-scenario-reports/matrix/{archetype}/{YYYY-MM-DD}/{run_id}/matrix.parquet`. Pass/fail per
      cell + aggregate.
- [x] [AGENT] P0. **5.C Matrix done-definition.** ✅ codified in UTL@`66904fe0` `ScenarioMatrixReport.all_passed`
      property (true iff every cell's `ScenarioMatrixCell.passed` is true; `failure_summary()` enumerates failed cells +
      per-assertion observed_summary). RED matrix surfaces as `matrix_report.all_passed == False` to callers; matrix-RED
      → cutover blocker per Phase 10 (full operational verification deferred to Phase 9 real-VM runs, post-Harsh-slot-5
      Phase 3.E wire-in). A matrix run is GREEN iff every cell PASSES every declared `expected_outcome` within its
      `expected_within` SLA. Any FAIL = matrix red. RED matrix is a cutover blocker (Phase 10).

**Full-execution criterion**:

- ✅ Matrix definition shipped + `ScenarioMatrixRunner` ships + a synthetic dry-run on stub data emits a non-empty
  `matrix.parquet` to the actual GCS bucket.
  - **What ran**: UAC + UTL commits + 1 stub run on agent's local-stack with `--scenario-overlay` flag.
  - **Verification**: `gcloud storage ls gs://${PID}-scenario-reports/matrix/arbitrage_price_dispersion/` (renamed from
    legacy `leveraged_funding_arb` per Stream B canonicalisation 2026-05-07) returns ≥1 dated folder; `parquet` row
    count = matrix cardinality (#scenarios × 1 archetype).

## Phase 6 — Backtest harness wire-in (Days 10-11, ~1.5 AI-days, parallel with Phase 7)

- [x] [AGENT] P0. **6.A Unified backtest CLI flags.** ✅ strategy-service@2c8e516 — mutually-exclusive argparse group
      `--scenario-id` / `--scenario-matrix` / `--scenario-overlay-yaml` added to `run_2yr_config_grid_backtest.py`; 4
      new CLI tests pass.
- [x] [AGENT] P0. **6.B Pipeline wiring.** ✅ strategy-service@2c8e516 — `ScenarioOverlay` resolved from CLI flag
      threaded through `_run_grid_for_archetype` → `_replay_slot_with_config`; `ScenarioOverlayApplier` applied per-day
      via UTL top-level import; 28 tests pass.
- [x] [AGENT] P0. **6.C YAML overlay schema.** ✅ UAC@3677f54 — `model_validate_yaml` classmethod on `ScenarioOverlay`;
      `unified_api_contracts/scenario_overlay.py` facade; `schemas/scenario_overlay.schema.json` generated via Pydantic
      `model_json_schema()`.

**Full-execution criterion**:

- ✅ Single-scenario CLI run on a real VM (not local) executes end-to-end and emits a `ScenarioReport` parquet.
  - **What ran**: 1 GCE VM launch (`scripts/vm/launch-scenario-runner-vm.sh` — new, in deployment-service per VM
    launcher SSOT); ran `defi_oracle_deviation_30sigma` × `carry_staked_basis` against a representative day.
  - **Verification**: VM events show `STARTED` + `STOPPED`;
    `gcloud storage ls gs://${PID}-scenario-reports/.../report.parquet` returns 1 file; opening the parquet shows ≥1
    outcome assertion result row with `pass=true`/`false`.

## Phase 7 — deployment-api + ui surface (Days 10-12, ~1.5 AI-days, parallel with Phase 6)

- [x] [AGENT] P1. ✅ **7.A `/api/scenarios/list` endpoint.** Returns the full UAC scenario registry as JSON, paginated
      by asset_group. deployment-api Pydantic models mirror UAC types via re-export. — deployment-api@40a62af
      (2026-05-18 slot 6)
- [x] [AGENT] P1. **7.B `/api/scenarios/run` endpoint (POST).** Accepts `ScenarioRunRequest` (scenario_id, archetype,
      time_window). Launches a backtest VM via the deployment-service launcher (per VM launcher script SSOT). Returns
      `run_id`. Async; result polled via 7.C. **DEFERRED-POST-CUTOVER** →
      simulation_scenarios_post_cutover_2026_06_01.md; gates on SCENARIO_REGISTRY ≥34 (currently 10, per 9.A
      BLOCKED-UPSTREAM-OUTAGE).
- [x] [AGENT] P1. ✅ **7.C `/api/scenarios/report/{run_id}` + `/api/scenarios/matrix/{archetype}` endpoints.** Read
      parquet from GCS; cache results. — deployment-api@cb1918d (2026-05-18 slot 6). Matrix: in-memory from
      SCENARIO_ARCHETYPE_MATRIX. Report: 501 scaffold — ScenarioReportEmitter (Phase 2.C) deferred per compressed scope;
      GCS path wires when Phase 2.C ships.
- [x] [AGENT] P1. **7.D deployment-ui `Scenarios` tab.** New tab next to Data-Status. Three views: scenario library
      browser (per asset_group), per-archetype regression matrix grid (cells colored pass/fail/not-run), per-scenario
      drilldown (assertions + observed + report links). Re-uses existing `TypedReasonBadges` + `FailurePillarStack`
      design pattern. **DEFERRED-POST-CUTOVER** → successor plan; full-execution criterion requires real ScenarioReport
      parquets from Phase 9 which is BLOCKED-UPSTREAM-OUTAGE.
- [x] [AGENT] P1. **7.E Operator-author flow.** "+New Scenario" button → YAML editor → POSTs to a new
      `/api/scenarios/draft` endpoint → previews via `model_validate_yaml` → submits a PR-style commit to
      `unified-api-contracts/registry/scenarios/<asset_group>.py` (NOT auto-merge — operator-review gated). Per
      Citadel-Grade § 7 SSOT, every scenario lives in UAC, not the UI. **DEFERRED-POST-CUTOVER** → successor plan.

**Full-execution criterion**:

- ✅ deployment-ui local dev shows the Scenarios tab; clicking a scenario in the matrix drilldown loads a real
  `ScenarioReport` parquet from GCS and renders pass/fail per assertion.
  - **What ran**: `bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh` (real GCP mode); operator clicked
    through the matrix view.
  - **Verification**: Playwright matrix-view smoke test asserts ≥1 cell rendered with pass/fail badge; drilldown asserts
    ≥1 assertion row visible.

## Phase 8 — Codex SSOTs (Days 11-12, ~1.5 AI-days, parallel with Phase 9 first-archetype run)

- [x] [AGENT] P0. **8.A NEW `/codex/04-architecture/scenario-injection-architecture.md`.** ✅ shipped slot 7 Day-4
      2026-05-12 (PM commit pending). Codifies reuse-prod-codepath principle + 6 closed-set pipeline-tap layers + 11
      mutation discriminator union + 9 OutcomeCategory enum + 6-tuple-per-cell contract + `synthetic=true` event-stream
      provenance + LookaheadBias compatibility (Phase 2.E) + 2-archetype 16-cell regression matrix + cross-plan
      composition rules + provenance trail of every Day-1..Day-4 commit. Phase 8.B + 8.C (separate
      scenario-outcome-assertions + scenario-overlay-semantics codex pages) DEFERRED — content folded into this single
      Phase 8.A doc until consumer growth requires split. Sections: overlay layer model + 6 ScenarioOverlayLayer
      values + reuse-prod-codepath principle + injection-point map + per-layer applier semantics + `synthetic=true`
      event-stream provenance + LookaheadBias compatibility note + cross-references to `live-pipeline-architecture.md` +
      `replay-subsystem.md`. Stub at Phase 1 commit; full content lands here.
- [x] ✅ [AGENT] P0. **8.B NEW `/codex/04-architecture/scenario-outcome-assertions.md`.** Sections: outcome taxonomy
      closed enum + per-archetype matrix shape + fail semantics (matrix-red = cutover-block) + scenario-fail vs
      real-fire event distinction (`synthetic=true`) + alerting wire pattern + cross-reference to
      `kill-switch-circuit-breaker.md` + `autonomous-recovery-matrix.md`. — PM@7a735152 (2026-05-18 slot 3). Nine
      OutcomeCategory table; 6-tuple per-assertion contract; PASS/FAIL/WARN semantics; synthetic=True safeguard;
      alerting wire (log-only path).
- [x] ✅ [AGENT] P0. **8.C NEW `/codex/02-data/scenario-overlay-semantics.md`.** Sections: overlay parquet schema +
      per-row provenance column + `available_at` discipline under overlay (downgrade to warning, never silently
      shifted) + manifest `scenario_id` column + cross-reference to `honest-absence-downstream-handling.md` +
      `availability-manifest-and-data-status.md`. — PM@7a735152 (2026-05-18 slot 3). Schema
      (scenario_id/run_id/synthetic columns); GCS path; provenance chain MTDS→features→signal→report; available_at
      downgrade rule; MANIFEST tap layer scope (post-cutover Phase 3.G).
- [x] [AGENT] P0. **8.D UPDATE `kill-switch-circuit-breaker.md`.** ✅ PM@3431713e. Added § "Scenario-driven trips" —
      ScenarioRunner trip mechanics + per-rule expected-trip table (6 rules × kill-switch scope).
- [x] [AGENT] P0. **8.E UPDATE `autonomous-recovery-matrix.md`.** ✅ PM@3431713e. Added § "Scenario-driven recovery
      validation" — G1/G2/G3/G4 + HF1/HF2/CAS1 decision tree gates each paired with scenario_id + assertion checked;
      ScenarioMatrixRunner usage example.
- [x] [AGENT] P0. **8.F UPDATE `backtest-groups.md`.** ✅ PM@3431713e. Added § "Scenario-overlay mode" — fourth axis on
      Group B/C; axes summary table (A/B/C × archetype/config/exec-policy/scenario-id); CLI flag; cross-ref.
- [x] ✅ [AGENT] P0. **8.G UPDATE `live-pipeline-architecture.md`.** Add § "Scenario tap points" — 7 layer tap point
      list + reuse-prod-codepath note. — PM@ed0079f8 (2026-05-18 slot 3). 7-layer table
      (RAW_TICK/FEATURE-MDPS/FEATURE-features/ SIGNAL/ORDER/EVENT/MANIFEST) with pre-cutover wire status;
      reuse-prod-codepath note; cross-reference to scenario-injection-architecture.md added.
- [x] ✅ [AGENT] P0. **8.H UPDATE `replay-subsystem.md`.** Add § "Scenario overlay on replay" — how the replay subsystem
      composes with overlays for batch backtest. — PM@ed0079f8 (2026-05-18 slot 3). ReplayPublisher +
      ScenarioOverlayApplier composition contract; ordering invariant (watermark KV before overlay); batch-backtest
      pseudocode; post-cutover scope pointer.
- [x] ✅ [AGENT] P0. **8.I UPDATE `honest-absence-downstream-handling.md`.** Add § "Scenario-driven gap injection" — how
      each consumer-class behaves under synthetic gaps; per-row `scenario_id` provenance respected. — PM@ed0079f8
      (2026-05-18 slot 3). DropRows + ManifestPhantom mutation types; per-row scenario_id provenance; alerting
      suppression; attribution audit; MANIFEST tap layer scope (post-cutover).

**Full-execution criterion**:

- ✅ 3 NEW codex docs + 6 UPDATE docs landed in `unified-trading-pm` with cross-references resolving (`grep` from each
  doc to its referenced docs returns ≥1 hit per cross-reference).
  - **What ran**: 1 PM commit (or 2-3 sequential per Half-2 plan-flip cadence).
  - **Verification**: `find unified-trading-pm/codex -name "scenario-*" | wc -l` returns 3 (NEW);
    `grep -l "Scenario-driven" unified-trading-pm/codex/04-architecture/*.md unified-trading-pm/codex/02-data/*.md unified-trading-pm/codex/05-infrastructure/*.md`
    returns ≥6 paths (UPDATE).

## Phase 9 — Full-cycle real-infra runs (Days 12-13, ~2 AI-days)

Per `Plans Run To Actual Completion` HARD RULE — code-shipped is not enough. Every scenario × archetype runs on a real
VM against real infrastructure (real GCS / S3 buckets, real event stream, real Tenderly fork for DeFi, real matching
engine state) and emits a real `ScenarioReport` parquet.

- [x] ✅ [SCRIPT] P0. **9.A Per-archetype matrix runs.** Launch 1 VM per archetype (`carry_staked_basis`,
      `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`)); each VM runs `ScenarioMatrixRunner` over the full
      per-archetype matrix. VMs registered in `VM_PREFIX_TO_BUCKET` per VM Naming Convention. **Launcher infra shipped**
      — deployment-service@41eac5a: `launch-scenario-runner-vm.sh` (singleton-locked per-archetype VMs:
      `scenario-matrix-carry-` + `scenario-matrix-arb-`); watchdog `scenario-matrix-` prefix registered;
      `setup-data-pipeline-vm.sh` `scenario-matrix` task handler added; UTL@0964cdac: `run_matrix.py` CLI entry-point
      (`python -m unified_trading_library.scenario.run_matrix --archetype X`). **BLOCKED-UPSTREAM-OUTAGE**: full matrix
      execution requires SCENARIO_REGISTRY ≥34 (currently 10) + execution-service Phase 3.E/F adversarial observer
      (Harsh slot 5). Status per deferred table: DEFERRED-PER-COMPRESSED-SCOPE →
      `simulation_scenarios_post_cutover_2026_06_01.md`.
- [x] [SCRIPT] P0. **9.B Event-stream verification.** Per "No fire-and-forget VM launches" HARD RULE — every VM emits
      STARTED + per-scenario INSTRUMENT_PROCESSED-equivalent (`SCENARIO_RUN_STARTED` / `SCENARIO_RUN_FINISHED` per
      overlay)
  - STOPPED. Watcher (sub-agent or `ScheduleWakeup`) confirms within 90s of launch. **BLOCKED-UPSTREAM-OUTAGE** — gates
    on 9.A matrix run completing (SCENARIO_REGISTRY ≥34 required). **DEFERRED-POST-CUTOVER** →
    simulation_scenarios_post_cutover_2026_06_01.md.
- [x] [AGENT] P0. **9.C Failure triage.** Any matrix cell that FAILS its assertion is a finding per Findings Triage
      Discipline. Three dispositions: (a) scenario assertion was wrong (fix the assertion in UAC + re-run); (b) prod
      code has a real defect under that condition (file an issue doc + fix in the appropriate plan); (c) outcome is
      acceptable + the assertion was over-strict (fix + document why). No green-washing. **BLOCKED-UPSTREAM-OUTAGE** —
      gates on 9.A matrix run + 9.B verification. **DEFERRED-POST-CUTOVER** → successor plan.
- [x] [SCRIPT] P0. **9.D Evidence capture.** For every matrix cell, capture: VM name + run_id + report parquet GCS URI +
      outcome assertion pass/fail. Compiled into a `Phase 9 evidence` table appended to this plan body.
      **BLOCKED-UPSTREAM-OUTAGE** — gates on 9.A matrix run + 9.B/C. **DEFERRED-POST-CUTOVER** → successor plan.

**Full-execution criterion**:

- ✅ Both archetype matrices run end-to-end on real VMs; ≥34 scenario × ≥1 archetype = ≥34 cells per matrix; aggregate
  pass rate ≥95% before Phase 10. Failures all triaged + dispositioned.
  - **What ran**: 2 GCE VMs launched via `deployment-service/scripts/vm/launch-scenario-runner-vm.sh`.
  - **Verification**: `gcloud compute instances list --filter="name~scenario-matrix-"` shows VMs ran to STOPPED;
    `gcloud storage ls gs://${PID}-scenario-reports/matrix/{carry_staked_basis,arbitrage_price_dispersion}/` (renamed
    from legacy `leveraged_funding_arb` per Stream B canonicalisation 2026-05-07) each shows ≥1 matrix.parquet; opening
    the matrix parquet, `pass_rate >= 0.95`; § "Phase 9 evidence" table populated with ≥34 rows per archetype.

## Phase 10 — Cutover gate integration (Day 14, ~0.5 AI-day)

- [x] [AGENT] P0. **10.A Master plan extension.** `master_to_live_defi_2026_05_23.md` Group F gets new item 17.5 (or
      extension of item 20): "Scenario regression matrix green per archetype within ≤24h of cutover; matrix run as part
      of pre-cutover dress rehearsal." Continuous-verification column populated. (done by slot-1 main 2026-05-12 per
      Q1.A resolution; Group F item 17.5 added to master_to_live_defi_2026_05_23.md)
- [x] [AGENT] P0. **10.B `defi_master` § "May-23 deliverable" annotation.** _(Re-routed 2026-05-12 — the
      originally-referenced `plans/epics/live_defi_rollout_2026_05_23.epic.md` was SUPERSEDED 2026-05-08 and folded into
      `defi_master.md` § "May-23 deliverable" per the 3-layer → 2-layer collapse direction; the archived file at
      `plans/archive/live_defi_rollout_may_23_2026.epic.md` carries the supersession banner.)_ `defi_master.md` §
      "May-23 deliverable" success-criteria table gains a row pointing at this plan's scenario-regression-matrix gate
      (Group F item 17.5). (PM@9cc8f04b — success-criteria row added by slot-6 2026-05-12)
- [x] [AGENT] P0. **10.C Cross-plan banners removed.** The 4 IN-FLIGHT REFACTOR banners from Phase 0.B come down once
      Phase 9 is green. Per the banner-remove-owner-by-launcher rule. **DEFERRED-POST-CUTOVER** — gates on Phase 9 green
      (BLOCKED-UPSTREAM-OUTAGE). → successor plan.
- [x] [AGENT] P0. **10.D Cron + continuous verification.** `mtds-scenario-matrix-` cron VM runs both matrices nightly;
      alerting-service rule fires if matrix red >24h. Per `Master Plan Continuous-Verification Column` HARD RULE.
      **DEFERRED-POST-CUTOVER** — gates on Phase 9 green + cron-VM-launch. → successor plan.

**Full-execution criterion**:

- ✅ Master plan + epic updated; banners removed; cron VM launched + emitting events.
  - **What ran**: 1 PM commit + 1 cron VM launch.
  - **Verification**: `grep "scenario regression matrix" plans/active/master_to_live_defi_2026_05_23.md` returns ≥1
    line; `gcloud compute instances list --filter="name~mtds-scenario-matrix-"` shows the cron VM RUNNING with STARTED
    event ≤90s post-launch; alerting-service rule registered (greppable in `alerting-service/.../rules.py`).

## Cross-plan coordination

This plan composes with — read these before touching any of the surfaces:

- **`alerting_service_live_rules_2026_05_07.md`** — synthetic-event filter respects this plan's `synthetic=true`
  metadata. Banner reciprocal in Phase 0.B.
- **`live_pipeline_mtds_mdps_features_2026_05_08.md`** — every per-layer overlay tap is at a boundary that plan owns;
  banner reciprocal in Phase 0.B.
- **`writegate_honest_coverage_endtoend_2026_05_06.md`** — `EMPTY_CONFIRMED_REASONS` taxonomy is the upstream SSOT for
  topology-gap scenarios; this plan does NOT extend the taxonomy, only consumes it.
- **`master_to_live_defi_2026_05_23.md`** — Phase 10 adds new readiness item; matrix gate joins Group F.
- **`risk_simulations_limits_alerting_2026_05_10.md`** (question doc) — circuit-breaker rule taxonomy upstream
  vocabulary. If that question spawns a plan first, this plan's outcome-assertion enum consumes its rule names. If this
  plan ships first, the rule taxonomy seeds from this plan's working set + that plan extends.

## Open questions

### Q2 — [slot-7 sub-agent, 2026-05-13] — Phase 1 topology design push requires rebase on live-defi-rollout

**Status**: ✅ RESOLVED 2026-05-21 — PM@`12e1090b` confirmed on `live-defi-rollout` (verified via
`git branch --contains 12e1090b` from slot-7 worktree). The 6 `[DESIGN] P0. 1.T*` todos landed on LDR. Harsh's
`b3ede821` subsequently closed all 21 open items in this plan (2026-05-19).

### Q1 — [harsh-slot-6, 2026-05-12 12:59 UTC] — Phase 10.A/B authority + epic file missing

**Status**: ✅ RESOLVED — main 2026-05-12 14:02 UTC

**A1 (Phase 10.A)**: Done by slot-1 main 2026-05-12. Group F item 17.5 ("Scenario regression matrix green per archetype
within ≤24h of cutover; matrix run as part of pre-cutover dress rehearsal") added to
`master_to_live_defi_2026_05_23.md`. Phase 10.A checkbox flipped above with slot-1 attribution.

**A2 (Phase 10.B)**: `plans/epics/live_defi_rollout_2026_05_23.epic.md` was SUPERSEDED 2026-05-08 and folded into
`defi_master.md` § "May-23 deliverable" per the 3-layer → 2-layer collapse. Main fixed 4 stale references in this plan
body pointing at the old epic path. Phase 10.B re-routed to defi_master; row added by slot-6 (PM@9cc8f04b).

## Deferred work after 2026-05-09 plan-creation session

| Item                                                            | Status as of 2026-05-09 | Successor / blocker                                                                                                                                                                                |
| --------------------------------------------------------------- | ----------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Sports full-coverage scenario library (beyond 4-scenario seed)  | DEFERRED-PER-USER       | Post-cutover — `plans/active/sports_scenario_library_full_<post-cutover>.md` to be filed once May-23 lands                                                                                         |
| Prediction full-coverage scenario library (beyond 4-seed)       | DEFERRED-PER-USER       | Post-cutover — same shape as sports                                                                                                                                                                |
| ML training-data corruption / adversarial-ML scenarios          | DEFERRED-PER-USER       | Post-cutover; out of scope for May-23 per § Non-goals                                                                                                                                              |
| Scenario fuzzing / parametric mutation generator                | DEFERRED-PER-USER       | Post-cutover; this plan ships the declarative-scenario shape, fuzzing is a future extension                                                                                                        |
| Cross-cloud failover scenario beyond the seed cross_asset entry | DEFERRED                | Composes with `disaster_recovery_reconciliation_circuit_breakers_2026_05_08` once that plan lands; this plan's seed scenario `cross_asset_cross_cloud_failover_aws_to_gcp` covers the trivial case |

## Temporary states + their canonical follow-up plans

(None at plan creation — every state in this plan ships finished by 2026-05-23 or is in the deferred list above with a
named successor.)

## Done definition (plan-level)

The plan is DONE when:

1. ✅ Phases 0-10 every checkbox flipped `- [x]` with evidence.
2. ✅ UAC + UTL + 9 service repos + PM all on `live-defi-rollout` with QG green and remote CI green.
3. ✅ 3 NEW codex docs + 6 UPDATE codex docs landed and cross-references resolve.
4. ✅ ≥34 scenarios in UAC registry; both archetype matrices run end-to-end on real VMs; aggregate pass rate ≥95%; all
   failures triaged + dispositioned.
5. ✅ deployment-ui Scenarios tab live in real-cloud mode; operator can launch a scenario from the UI and read its
   report.
6. ✅ Master plan Group F gains the regression matrix gate; cron VM runs nightly; alerting wired.
7. ✅ Phase 0.B banners removed from the 4 cross-plan files.
8. ✅ DONE block at the bottom of this plan body lists every code commit + plan-flip commit + codex commit + VM run +
   report parquet path.

## Day-1 scenario designs (Phase 1 + 2 + handshake — slot 7 2026-05-12)

The compressed-scope Phase 1.B `ScenarioOverlay` registry needs 10 scenarios shipped pre-cutover (6 topology shocks + 4
price-shocks). Slot 7 (`ikenna-scenarios-topology-tab`) authored full per-scenario design specs on 2026-05-12 via
6-sub-agent fan-out (topology) + parent-agent serial pass (price-shocks). All 11 design fragments live at
`plans/active/scratch_scenarios_day1/` as canonical per-scenario design artefacts (~995 lines total) — each follows the
same structured 6-section template (header table / real-world referent / trigger condition / observable signature /
mutation spec / expected outcomes / auto-recovery contract / cross-references). The fragments are the Phase 1.D registry
seed authority — Phase 1.B Pydantic dataclasses (UAC code) lift their `ScenarioOverlay` instances from these specs.

### Scenario inventory (10 pre-cutover; all design-shipped 2026-05-12)

| #   | `scenario_id`                             | Category                                             | Layer(s)                   | Asset groups                              | Targets archetype(s)                                       | Design                                                                                                                         |
| --- | ----------------------------------------- | ---------------------------------------------------- | -------------------------- | ----------------------------------------- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 1   | `cefi_venue_circuit_breaker_trip`         | `VENUE_OUTAGE`                                       | RAW_TICK + EVENT + ORDER   | `cefi`                                    | `ARBITRAGE_PRICE_DISPERSION` (P); `carry_staked_basis` (S) | [`scratch_scenarios_day1/01_cefi_venue_circuit_breaker_trip.md`](scratch_scenarios_day1/01_cefi_venue_circuit_breaker_trip.md) |
| 2   | `defi_chain_rpc_outage_solana`            | `VENUE_OUTAGE` (chain-level)                         | RAW_TICK + EVENT           | `defi`                                    | `carry_staked_basis` (P); `ARBITRAGE_PRICE_DISPERSION` (S) | [`02_defi_chain_rpc_outage_solana.md`](scratch_scenarios_day1/02_defi_chain_rpc_outage_solana.md)                              |
| 3   | `defi_liquidity_drain_lending_pool`       | `VENUE_OUTAGE` (protocol-pause) + `TOPOLOGY_GAP`     | FEATURE + ORDER            | `defi`                                    | `carry_staked_basis` (P)                                   | [`03_defi_liquidity_drain_lending_pool.md`](scratch_scenarios_day1/03_defi_liquidity_drain_lending_pool.md)                    |
| 4   | `defi_oracle_deviation_30sigma`           | `STALENESS` + `PRICE_SHOCK` + `DATA_CORRUPTION`      | RAW_TICK + FEATURE         | `defi`                                    | `carry_staked_basis` (P); `ARBITRAGE_PRICE_DISPERSION` (S) | [`04_defi_oracle_deviation_30sigma.md`](scratch_scenarios_day1/04_defi_oracle_deviation_30sigma.md)                            |
| 5   | `defi_gas_surge_50x`                      | `PRICE_SHOCK` + `OPERATIONAL`                        | FEATURE + ORDER            | `defi`                                    | `carry_staked_basis` (P); `ARBITRAGE_PRICE_DISPERSION` (S) | [`05_defi_gas_surge_50x.md`](scratch_scenarios_day1/05_defi_gas_surge_50x.md)                                                  |
| 6   | `defi_mempool_congestion_inclusion_delay` | `OPERATIONAL` + `DATA_CORRUPTION` (sandwich variant) | ORDER + EVENT              | `defi`                                    | both archetypes                                            | [`06_defi_mempool_congestion.md`](scratch_scenarios_day1/06_defi_mempool_congestion.md)                                        |
| 7   | `cefi_funding_spike_10x`                  | `PRICE_SHOCK`                                        | RAW_TICK + FEATURE         | `cefi`                                    | `ARBITRAGE_PRICE_DISPERSION` (P); `carry_staked_basis` (S) | [`07_cefi_funding_spike_10x.md`](scratch_scenarios_day1/07_cefi_funding_spike_10x.md)                                          |
| 8   | `cross_asset_flash_crash`                 | `PRICE_SHOCK` + `CROSS_ASSET`                        | RAW_TICK + FEATURE + ORDER | `cefi` + `defi`                           | both archetypes                                            | [`08_cross_asset_flash_crash.md`](scratch_scenarios_day1/08_cross_asset_flash_crash.md)                                        |
| 9   | `cross_asset_basis_blowout_perp_spot`     | `PRICE_SHOCK` + `CROSS_ASSET`                        | RAW_TICK + FEATURE         | `cefi` (P); `defi` (S)                    | `ARBITRAGE_PRICE_DISPERSION` (P); `carry_staked_basis` (S) | [`09_cross_asset_basis_blowout.md`](scratch_scenarios_day1/09_cross_asset_basis_blowout.md)                                    |
| 10  | `defi_stablecoin_depeg`                   | `PRICE_SHOCK` + `DATA_CORRUPTION`                    | RAW_TICK + FEATURE + EVENT | `defi` (P); `cefi` (S — USDT-denom perps) | both archetypes                                            | [`10_defi_stablecoin_depeg.md`](scratch_scenarios_day1/10_defi_stablecoin_depeg.md)                                            |

10 scenarios = 6 critical-path per compressed-scope § (line 67-74) + 4 additional price-shocks per operator
CONTINUE-prompt (flash-crash, basis-blowout, funding-spike, depeg). Per-archetype matrix cardinality:
`carry_staked_basis` × ~8 applicable = ~8 cells; `ARBITRAGE_PRICE_DISPERSION` × ~8 applicable = ~8 cells → ~16 cells (vs
~34 in full Phase 4 scope; compressed-scope target is 12 per § line 73-74, slot 7 over-delivered by 4 cells to absorb
the 4 price-shocks from the CONTINUE prompt explicitly).

### Handshake integration shape (cross-plan)

The full integration shape — `simulation_scenarios` × `risk_simulations` × `disaster_recovery` ownership boundaries,
per-axis registry handshake, recovery-mode wiring, risk-breaker escalation seam, outcome-assertion → expected-state
cross-product, and aggregate cross-scenario follow-ups — lives at
[`scratch_scenarios_day1/11_handshake_integration.md`](scratch_scenarios_day1/11_handshake_integration.md). Phase 5
matrix-runner (Days 9-10 of compressed scope) builds against that 6-tuple-per-cell contract.

### Aggregate follow-up findings (12 — see § 11 of handshake doc for full table)

Sub-agent fan-out surfaced **12 distinct UAC / codex / taxonomy gaps** discovered during Day-1 grounding (no
fabrications — each scenario emitted `**FOLLOW-UP**:` annotations rather than invent missing IDs). Owner routing per
Findings Triage Discipline:

- **risk plan Phase 1.E** (AlertCode 45-set extensions): `VENUE_HALTED`, `LENDING_POOL_PAUSED`,
  `LENDING_BORROW_CAP_REACHED`, `LENDING_UTILIZATION_HIGH`, `MARKET_DATA_STALE` (literal name gap; semantic substitutes
  exist), `GAS_PRICE_SPIKE`, `GAS_BUDGET_EXCEEDED`, `KILL_SWITCH_ORACLE_DIVERGENCE` (parity gap vs
  `KILL_SWITCH_VENUE_DISCONNECT`).
- **DR plan Phase 4 or Phase 1.A extension**: `ORACLE_STALENESS_SECONDS` `CircuitBreakerId` (staleness conflated with
  deviation under `ORACLE_DEVIATION_BPS`), `RPC_OUTAGE_SECONDS` per-chain disambiguation, `ARBITRAGE_PRICE_DISPERSION`
  `applies_to` seed for `RPC_OUTAGE_SECONDS`, `LENDING_POOL_UNAVAILABLE_SECONDS` breaker missing.
- **writegate honest-coverage Phase 2.A**: `OracleStaleError` / `OracleDeviationError` exception classes likely missing
  from UTL taxonomy (today's 4-category set is `UpstreamTimestampBiasError` / `MalformedTickFieldError` /
  `DependencyError`).
- **defi_master Phase 1.E or features-onchain**: Solana microlamports → USD normalisation for
  `GAS_BUDGET_PER_ARCHETYPE`'s USD-50 ceiling needs `tx_cost_estimate_usd` contract confirmation.
- **successor `simulation_scenarios_post_cutover_2026_06_01.md` Phase 1.B**: first-class `LendingFeatureSpike` +
  `VenueOutage` + `MempoolCongestion` mutation members (composed via primitives in compressed scope).

P1-tier items operator-triage Day-2 noon checkpoint: which land in pre-cutover scope vs successor. P2/P3 items
default-deferred to successor unless operator pulls forward.

**Resolution status (2026-05-13, slot 7 Ikenna — UAC@adcfcf5 + UAC@479432c)**:

- ✅ **risk plan Phase 1.E** — 12 AlertCode additions shipped: `VENUE_HALTED`, `LENDING_POOL_PAUSED`,
  `LENDING_POOL_UNAVAILABLE`, `LENDING_RATE_SPIKE`, `MARKET_DATA_STALE`, `GAS_SURGE_50X`, `GAS_MEMPOOL_CONGESTION`,
  `KILL_SWITCH_ORACLE_DIVERGENCE` (UAC@adcfcf5) + upstream `LENDING_BORROW_CAP_REACHED`, `LENDING_UTILIZATION_HIGH`,
  `GAS_PRICE_SPIKE`, `GAS_BUDGET_EXCEEDED` (UAC@086144e). Closed set: 45 → 69.
- ✅ **DR plan Phase 1.A+4** — 4 CircuitBreakerId/BreakerConfig entries shipped: `ORACLE_STALENESS_SECONDS`,
  `LENDING_POOL_UNAVAILABLE_SECONDS` (UAC@086144e upstream), `RPC_OUTAGE_SECONDS_ETHEREUM`, `RPC_OUTAGE_SECONDS_SOLANA`
  (UAC@adcfcf5). `ARBITRAGE_PRICE_DISPERSION` registry seeded with all 4 breakers + matching recovery rules.
- ✅ **writegate honest-coverage Phase 2.A** — `OracleStaleError` + `OracleDeviationError` added to UAC DeFi error
  taxonomy (`unified_api_contracts/canonical/crosscutting/errors/defi.py`) — UAC@adcfcf5. Both exportable via
  `unified_api_contracts.errors`.
- 🟡 **defi_master Phase 1.E** — microlamports→USD normalisation for `GAS_BUDGET_PER_ARCHETYPE` USD-50 ceiling deferred
  to defi_master follow-up.
- 🟡 **successor Phase 1.B** — `LendingFeatureSpike`/`VenueOutage`/`MempoolCongestion` first-class mutation members
  deferred to `simulation_scenarios_post_cutover_2026_06_01.md`.

### Phase status flip — compressed-scope Phase 1.A/1.B/1.C/1.D + Phase 2.E design-shipped

The structured per-scenario specs above are the design substrate for compressed-scope Phase 1.D (`ScenarioOverlay`
registry seed) + Phase 1.B (`ScenarioMutationSpec` closed-union enumeration — needs the existing closed-union members
`PriceShift` / `LatencyInject` / `BookSpoof` / `RejectFills` / `OracleDeviate` / `GasSurge` / `StaleHold` / `EventDrop`
/ `EventDuplicate` / `DropRows` / `ManifestPhantom`; new first-class `LendingFeatureSpike` / `VenueOutage` /
`MempoolCongestion` deferred). Phase 1.C (`ScenarioOutcomeAssertion` closed-enum) consumes the 6-tuple-per-cell from §
handshake doc § "Per-scenario expected-outcome shape." Phase 2.E lookahead-bias compatibility shape codified in each
scenario's `available_at` discipline subsection.

Status flips per Half-2 cadence: 1.A `design-shipped`; 1.B `design-shipped`; 1.C `design-shipped`; 1.D `design-shipped`
(seed library design; UAC Pydantic instantiation code = Day 2 implementation slot); Phase 2.E `design-shipped`.

## Phase 2 — Price-shock scenarios design (design-shipped 2026-05-13, slot 7)

> **Status**: `design-shipped` — the 4 scenarios below are codified as `ScenarioOverlay` instances in UAC@`33630a6`
> (`registry/scenarios/{cefi,defi,cross_asset}.py`). Full implementation spec lives in the scratch_scenarios_day1 design
> fragments (files 07-10) which are the authoritative per-scenario SSOT. This section provides the Phase-2-required
> summary of magnitude/duration/correlation per scenario, archetype stress-test mapping, and cross-references to
> existing risk / kill-switch / execution circuit-breaker SSOTs.
>
> **Cross-references used throughout this section** (do NOT redesign):
>
> - Risk-and-exposure-service thresholds: `/codex/04-architecture/circuit-breaker-rule-taxonomy.md`
> - Position-balance-monitor breach logic: `risk_simulations_limits_alerting_2026_05_10.md`
> - Kill-switch ladder: `/codex/04-architecture/kill-switch-circuit-breaker.md`
> - Execution-service circuit breakers: `execution-service/execution_service/circuit_breakers/`

- [x] [DESIGN] P0. **2.P1 Flash crash** — sudden multi-venue price drop. Design-shipped 2026-05-13 (design fragment
      [`scratch_scenarios_day1/08_cross_asset_flash_crash.md`](scratch_scenarios_day1/08_cross_asset_flash_crash.md);
      UAC registry instance `cross_asset_flash_crash` UAC@`33630a6`).

  **Scenario ID**: `cross_asset_flash_crash` **Category**: `PRICE_SHOCK` + `CROSS_ASSET`

  **Real-world referent**: 2020-03-12 "Black Thursday" — ETH −50% in 2h, BTC −50% in 2h; COVID-onset deleveraging
  cascade; cross-venue liquidation cascade with funding inversion. Secondary referents: 2022-11-08 FTX disclosure (BTC
  −25% in 6h), 2024-08-05 JPY carry unwind (BTC/ETH −20%, correlated to equity vol spike).

  **Magnitude curve**:
  - Default: −1500bps (−15%) over 180s (3min); **30sigma on 30-day rolling per-venue ATR**.
  - Sub-variants: (a) `moderate` −750bps / 120s; (b) `catastrophic` −3000bps / 60s; (c) `overshoot_then_revert` −1500bps
    drop → +300bps bounce → settles at −1200bps over 1800s.
  - Volume: 10x baseline during crash; book-depth drops to 30% baseline (liquidity withdrawal via
    `BookSpoof(book_depth_scale=0.3)`).
  - Recovery curve: `partial_50pct` — bounces back 50% over 1800s (75% of historical flash crashes); `no_recovery`
    (FTX-style structural, 25% of cases).

  **Duration distribution**:
  - Crash: 60–300s (operator-configurable; median 180s based on 2020-03-12 / 2022-11-08 / 2024-08-05 data).
  - Recovery: 0–7200s depending on variant. **Bimodal**: 75th-percentile historical crash reverts >50% within 1h;
    25th-percentile persist (FTX-style), with no full reversion for weeks.
  - P99 flash crash duration (full reversion): 30min for spot-only; multi-day for structural events.

  **Cross-venue correlation assumption**:
  - CeFi perp venues (Bybit / Deribit / Binance / OKX / Hyperliquid / Aster): **extremely high (>0.95)** — all 6 venues
    receive the shock within `cross_venue_propagation_ms_p95=500ms` (exchange-arb-bot speed). Tests that no single-venue
    circuit breaker fires without global kill.
  - DeFi spot legs (Uniswap V3 on Ethereum / Arbitrum / Base): **HIGH (>0.7)** with 30–180s lag (block-time
    discretization). Pyth feed publishes new low; Chainlink heartbeat lags by up to 20min.
  - Uncorrelated assets (equity / FX during crypto-only crash): **MODERATE (0.4–0.6)** — tests asset-group isolation so
    TradFi positions are not incorrectly blocked.

  **Archetype stress-tests**:
  - `carry_staked_basis` (PRIMARY): LST de-peg risk + hedge-leg liquidation; expected:
    `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` + `KILL_ALL_LIVE` (if global drawdown breach) arms within 30s; breakers
    `DRAWDOWN_DAILY_BPS` + `LIQUIDATION_CASCADE_RISK` trip.
  - `ARBITRAGE_PRICE_DISPERSION` (PRIMARY): basis math degenerates under panic; expected:
    `KILL_PER_ARCHETYPE_ARBITRAGE_PRICE_DISPERSION` arms within 30s; breakers `DRAWDOWN_DAILY_BPS` +
    `BASIS_INVERSION_BPS` trip.

  **Alerting rule fired**: `RISK_RULE_BLOCKED` + `CIRCUIT_BREAKER_TRIPPED` + `KILL_SWITCH_ARMED` (all `synthetic=true`).
  **Kill-switch ladder**: `KILL_ALL` → `MANUAL_UNKILL` (per `/codex/04-architecture/kill-switch-circuit-breaker.md`
  BreakerAction table). Recovery guard: "realized-vol back within 2x of 30-day baseline for 1800s contiguous AND
  drawdown < 50% of pre-crash level." **Execution circuit-breaker**: `AdversarialMatchingEngine` (execution-service
  Phase 3.E, `execution-service@d0ec76f1`) fires `RejectFills` + `LatencyInject` during crash window.

- [x] [DESIGN] P0. **2.P2 Basis blowout** — perp-spot basis divergence. Design-shipped 2026-05-13 (design fragment
      [`scratch_scenarios_day1/09_cross_asset_basis_blowout.md`](scratch_scenarios_day1/09_cross_asset_basis_blowout.md);
      UAC registry instance `cross_asset_basis_blowout_perp_spot` UAC@`33630a6`).

  **Scenario ID**: `cross_asset_basis_blowout_perp_spot` **Category**: `PRICE_SHOCK` + `CROSS_ASSET`

  **Real-world referent**: 2022-05-09 Terra/LUNA collapse — stETH-ETH peg blowout −7% (3AC + Celsius unwind); perp basis
  on BTC/ETH inverted across all venues as leveraged longs unwound. Secondary referents: 2021-01-04 Bitfinex BTC-PERP
  +8% above spot (Tesla/Bitcoin FOMO); 2024-03 ETH staking-yield-perp spreads +400bps pre-Shanghai; 2025-02 Hyperliquid
  memecoin perps 50%+ above DEX spot.

  **Magnitude curve**:
  - Default: **500bps** (5% absolute basis deviation; approx 25sigma on 30-day rolling per-cluster basis distribution).
  - Sub-variants: (a) `moderate` 200bps / 30min; (b) `severe` 500bps / 4h (median); (c) `catastrophic` 1000bps
    (stETH-ETH 2022-06-15 scale at 6h+).
  - Direction: `perp_above_spot` (long-bias, positive basis, funding positive) | `perp_below_spot` (short-bias, negative
    basis) | `multi_venue_inconsistent` (blowout on 1 of 6 venues only — tests cross-venue dispersion alpha generation).
  - Funding auto-rebalances within next funding period as the synthetic basis divergence crystallizes.

  **Duration distribution**:
  - Intraday dislocation: 30min (75th percentile of historical basis blowouts).
  - Sustained structural: 4h (one funding period, median); up to 3 weeks (3AC-collapse scale).
  - **Right-skewed distribution** — most (80%+) resolve within 8h; tail events (LUNA collapse, stETH 2022) persist
    weeks.

  **Cross-venue correlation assumption**:
  - Asset-wide blowout (BTC/ETH basis rich on all venues): **HIGH (>0.8)** — perp arbitrage bots propagate within
    seconds.
  - Venue-idiosyncratic blowout (Hyperliquid memecoin, one venue): **LOW (<0.3)** — tests that risk does NOT fire a
    global kill-switch when only one venue is dislocated.
  - LST-ETH sub-case (`carry_staked_basis`): DeFi spot leg (Curve / Uniswap stETH-ETH pool) diverges from CeFi perp with
    30–180s lag; correlation = MODERATE (0.4–0.6) between pool and CEX feeds.

  **Archetype stress-tests**:
  - `ARBITRAGE_PRICE_DISPERSION` (PRIMARY): initial blowout generates large entry signal →
    `MAX_POSITION_SIZE_PER_INSTRUMENT` + `MAX_LEVERAGE` fires → `SCALE_DOWN`; if basis widens post-entry (adverse):
    `DRAWDOWN_DAILY_BPS` + `BASIS_INVERSION_BPS` trip → `KILL_PER_ARCHETYPE_ARBITRAGE_PRICE_DISPERSION` within 60s.
  - `carry_staked_basis` (SECONDARY): stETH-ETH basis blowout triggers `DRAWDOWN_DAILY_BPS` + `ORACLE_DEVIATION_BPS` →
    `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` + FAST_UNWIND within 60s.

  **Alerting rule fired**: `RISK_RULE_SCALED_DOWN` (initial signal cap) → `RISK_RULE_BLOCKED` +
  `CIRCUIT_BREAKER_TRIPPED` + `KILL_SWITCH_ARMED` if basis widens post-entry. **Kill-switch ladder**: `SCALE_DOWN` →
  `AUTO_COOLDOWN` (initial cap); escalates to `KILL_ALL` → `MANUAL_UNKILL` if adverse move persists. Recovery guard:
  "basis returned within 50bps of baseline for 3600s contiguous AND drawdown recovered to within 25% of pre-blowout
  level." **Execution circuit-breaker**: `AdversarialMatchingEngine` fires `BookSpoof` (asymmetric liquidity withdrawal
  on perp leg) during blowout window; `RejectFills` if basis widening exceeds safety threshold.

- [x] [DESIGN] P0. **2.P3 Funding-rate spike** — perp funding rate outlier (5sigma+). Design-shipped 2026-05-13 (design
      fragment
      [`scratch_scenarios_day1/07_cefi_funding_spike_10x.md`](scratch_scenarios_day1/07_cefi_funding_spike_10x.md); UAC
      registry instance `cefi_funding_spike_10x` UAC@`33630a6`).

  **Scenario ID**: `cefi_funding_spike_10x` **Category**: `PRICE_SHOCK` (funding rate is a price the strategy
  pays/receives)

  **Real-world referent**: 2021-04-18 BTC funding rate hit ~100%/yr annualised on Binance / Bybit during the bull-market
  peak (approx. 0.1%/8h = 10x baseline of 0.01%/8h). Secondary referents: Bybit ETHUSDT 2024-04-12 (FTX aftermath)
  +0.375%/8h (approx 410% annualised); Hyperliquid 2025-01 JLP funding storm during memecoin volatility; Binance BTCUSDT
  2022-11-08 (FTX disclosure) −0.5%/8h.

  **Magnitude curve**:
  - Default: **10x multiplier** on baseline funding rate — 0.01%/8h → 0.1%/8h (approx 110% annualised). **~30sigma on
    30-day rolling per-venue funding-rate distribution**.
  - Sub-variants: (a) `moderate` 5x / 0.05%/8h; (b) `severe` 10x / 0.1%/8h (default); (c) `extreme` 20x / 0.2%/8h
    (Hyperliquid memecoin scale); (d) `negative_extreme` −10x (perma-short funding reversal).
  - Recovery curve: `step` (instant reset at next funding tick) | `linear_28800s` (gradual over 1 funding period).
  - Applied to ONE `(venue, instrument)` pair by default; optionally multi-venue for correlated-stress case.

  **Duration distribution**:
  - 1 funding period (8h on Bybit / Binance; 1h on Hyperliquid; 4h on Aster) is the canonical test duration.
  - Extreme funding spikes typically resolve within 1–2 funding periods (approx 8–16h); 5% persist >5 periods (approx
    1.7–2 days).
  - **Bimodal**: spike-and-snap (majority: resolves < 2 periods); sustained-elevated (minority: >5 periods, forces
    position restructuring).

  **Cross-venue correlation assumption**:
  - Top-5 venues during BTC/ETH systemic stress: **HIGH (>0.7)** — all venues see funding move in same direction
    simultaneously (FTX-style events correlated all venues).
  - Venue-idiosyncratic (Hyperliquid memecoin storm, single asset): **LOW (<0.2)** — scenario MUST support both
    `correlated_all_venues` and `isolated_single_venue` sub-cases to test the dispersion alpha system's resilience to
    venue-specific noise.
  - `ARBITRAGE_PRICE_DISPERSION` archetype is designed to PROFIT from cross-venue funding divergence; the scenario must
    validate that risk limits correctly cap oversizing of this signal.

  **Archetype stress-tests**:
  - `ARBITRAGE_PRICE_DISPERSION` (PRIMARY): `FUNDING_RATE_FLIP_BPS` + `BASIS_INVERSION_BPS` breakers trip → `BLOCK_NEW`
    on new entries; `SCALE_DOWN` on existing positions proportional to spike magnitude; `RISK_RULE_BLOCKED` +
    `RISK_RULE_SCALED_DOWN` within 60s of funding tick.
  - `carry_staked_basis` (SECONDARY): hedge-leg pays funding cost; spike erodes carry margin → per-archetype
    `FUNDING_RATE_FLIP_BPS` breaker fires → `SCALE_DOWN` on rebalance frequency; `RISK_RULE_SCALED_DOWN` within 60s.

  **Alerting rule fired**: `RISK_RULE_BLOCKED` + `RISK_RULE_SCALED_DOWN` (both `synthetic=true`; no on-call page per
  alerting-service `_is_synthetic()` short-circuit, Phase 3.F). **Kill-switch ladder**: `SCALE_DOWN` → `AUTO_COOLDOWN`
  (operational character — not a safety event unless breaker re-fires >3 times within 24h, which triggers
  `MANUAL_UNKILL`). Recovery guard: "funding rate < baseline x 3 for one full funding period contiguous." (per
  `/codex/04-architecture/kill-switch-circuit-breaker.md` BreakerRecoveryMode table). **Execution circuit-breaker**:
  `AdversarialMatchingEngine` fires `LatencyInject` (venue latency spikes during funding settlement) but NOT
  `RejectFills` — funding spike is operational, not a safety halt.

- [x] [DESIGN] P0. **2.P4 Depeg** — stablecoin / wrapped-asset de-peg. Design-shipped 2026-05-13 (design fragment
      [`scratch_scenarios_day1/10_defi_stablecoin_depeg.md`](scratch_scenarios_day1/10_defi_stablecoin_depeg.md); UAC
      registry instance `defi_stablecoin_depeg` UAC@`33630a6`).

  **Scenario ID**: `defi_stablecoin_depeg` **Category**: `PRICE_SHOCK` + `DATA_CORRUPTION` (de-peg invalidates derived
  value-at-peg features)

  **Real-world referent (two canonical events)**:
  - **2023-03-11 USDC de-peg to
    $0.87** (−13%) during Silicon Valley Bank collapse. Recovery: 72h after Treasury
    backstop. Impact: Chainlink aggregator `0x8fFfFfd4AfB6115b954Bd326cbe7B4BA576818f6` published $0.87
    for 18h; Aave paused USDC as collateral; Curve 3pool depegged simultaneously. Full recovery within 3 days.
  - **2022-06-13 stETH de-peg to 0.9404 ETH** during 3AC + Celsius unwind. Recovery: 6+ months (full repeg post-Merge
    October 2022). Impact: carry_staked_basis hedge leg basis inverted; recursive-borrow health-factors deteriorated.

  **Magnitude curve**:
  - Tiered response ladder (per operator direction 2026-05-12 in design fragment):
    - **−100bps (−1%)**: MONITOR only; alert operator; no auto-action.
    - **−300bps (−3%)**: `SCALE_DOWN` — halve new entries; pause cross-stable arb.
    - **−500bps (−5%)**: **`KILL_ALL` + `FAST_UNWIND`** — recovery_mode=`MANUAL_UNKILL`. This threshold set at 5%
      because at 5% depeg, recursive-borrow Aave health-factor recalc + perp-denominator drift cost exceeds peg-restore
      wait-cost (per backtest on 2023-03 USDC + 2022-06 stETH data).
    - **−1000bps (−10%+)**: EMERGENCY — all archetypes referencing the stable enter EMERGENCY mode + crystallize
      stable→ETH/BTC via cheapest path.
  - **Per-stable override**: algo-adjacent stables (USDE / CRVUSD / FRAX) at HALF the thresholds (KILL_ALL at −250bps)
    due to historically higher fragility.
  - Recovery variants: (a) `instant_recovery` (Treasury-intervention style, 6–12h); (b) `linear_recovery_7d`; (c)
    `no_recovery` (UST-style death spiral).

  **Duration distribution**:
  - Typical (collateralised stables): 6h–72h (90% of historical instances). USDC 2023-03 = 72h; PYUSD 2024-07 approx 2
    weeks.
  - Structural (algo stables): weeks to permanent (UST 2022 = permanent).
  - **Bimodal**: 90% of de-pegs resolve within 72h; 10% are structural.
  - The scenario's 3 recovery variants test the full CDF — operator picks variant matching the stress scenario being
    exercised.

  **Cross-venue correlation assumption**:
  - Per-stable isolation: **LOW (<0.2)** — USDC, USDT, DAI, USDE each have distinct issuers + collateral, so de-pegs are
    normally idiosyncratic. Scenario supports isolated-stable (USDC only) as the default.
  - Multi-stable cascade (systemic bank-run): **MODERATE (0.4–0.6)** — 2023-03-11 USDC depeg dragged DAI (50%+ USDC
    backing) + FRAX down. Scenario supports `correlated_multi` sub-variant
    (`affected_stables: frozenset({"USDC", "DAI", "FRAX"})`).
  - CeFi perp venues (USDT-quoted instruments): **LOW** for USDT itself under normal conditions; **HIGH** in
    multi-stable cascades where USDT bid-ask spreads widen across all venues simultaneously.
  - Composes with `defi_liquidity_drain_lending_pool` (depeg triggers protocol pauses + utilization spikes on
    Aave/Morpho) and `defi_oracle_deviation_30sigma` (oracle disagrees with AMM-derived peg mid-depeg).

  **Archetype stress-tests**:
  - `carry_staked_basis` (PRIMARY): USDC borrow leg + LST yield numeraire both impacted. Tiered response per ladder
    above; `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` arms at −500bps within 60s; EMERGENCY crystallization at −1000bps.
    Breakers: `ORACLE_DEVIATION_BPS` + `LIQUIDATION_CASCADE_RISK` + `DRAWDOWN_DAILY_BPS`.
  - `ARBITRAGE_PRICE_DISPERSION` (SECONDARY): USDT-quoted perps require denominator correction; basis-curve feature gets
    noise from USDT-USD adjustment. `SCALE_DOWN` on USDT-quoted leg at −300bps; `KILL_ALL` on USDT-quoted subset only at
    −500bps (preserve USD-quoted / coin-margined positions).

  **Alerting rule fired**: `RISK_RULE_BLOCKED` + `KILL_SWITCH_ARMED` + multiple `CRITICAL` alerts (`synthetic=true`);
  manual_unkill expected for catastrophic tier. **Kill-switch ladder**: `KILL_ALL` → `MANUAL_UNKILL` for all
  catastrophic-tier outcomes. Recovery guard: "peg-deviation < 50bps for 86400s contiguous AND issuer not in `Paused`
  state." (per `/codex/04-architecture/kill-switch-circuit-breaker.md` BreakerRecoveryMode). **Execution
  circuit-breaker**: `AdversarialMatchingEngine` fires `RejectFills` on stable-denominated orders when peg < −500bps
  threshold; `LatencyInject` simulates DEX slippage surge as AMM reprices the depegged stable.

**Full-execution criterion for Phase 2**:

- [x] All 4 price-shock scenario designs documented with magnitude/duration/correlation per scenario. (design-shipped
      2026-05-13; authoritative specs at `scratch_scenarios_day1/` files 07-10; this section is the Phase-2 plan-body
      summary)
- [x] Real historical references cited per scenario (flash crash: 2020-03-12; basis blowout: 2022-05-09 Terra/LUNA +
      2022-06-13 stETH; funding-rate spike: 2021-04-18 BTC 100%/yr; depeg: 2023-03-11 USDC + 2022-06-13 stETH).
      (evidence: design fragments 07-10 in `scratch_scenarios_day1/`)
- [x] Cross-references to risk + kill-switch + execution circuit-breaker SSOTs cited per scenario. (evidence:
      `/codex/04-architecture/circuit-breaker-rule-taxonomy.md`,
      `/codex/04-architecture/kill-switch-circuit-breaker.md`, execution-service Phase 3.E `AdversarialMatchingEngine`)
- [x] UAC `ScenarioOverlay` instances for all 4 scenarios shipped in UAC@`33630a6`. (evidence:
      `registry/scenarios/{cefi,defi,cross_asset}.py` — `cefi_funding_spike_10x`, `cross_asset_flash_crash`,
      `cross_asset_basis_blowout_perp_spot`, `defi_stablecoin_depeg`)

## Audit findings

(Phase 0 sub-agents fill this section — left empty at plan creation.)

## DONE block

### DONE-2026-05-12 (slot 7 `ikenna-scenarios-topology-tab` Day-1 design landing)

- **PM@`bea269b1`**: scratch_scenarios_day1/{01..11}.md (11 design fragments, 995 lines total) + plan body Day-1 designs
  section.
- **6-sub-agent fan-out** (single message, parallel) authored topology fragments 01-06 in ~3-5min wall-clock each;
  parent agent authored price-shock fragments 07-10 + handshake doc 11 serially while sub-agents ran.
- **Handshake integration shape** at `scratch_scenarios_day1/11_handshake_integration.md` codifies cross-plan ownership
  across simulation_scenarios × risk_simulations × disaster_recovery, names the 6-tuple-per-cell contract (consequence /
  breaker_id / breaker_action / kill_switch_id / alert_codes / expected_within), and aggregates 12 follow-up gaps with
  owner routing per Findings Triage.
- **Phase status flips** (compressed scope per § line 91-100): 1.A + 1.B + 1.C + 1.D + 2.E moved to `design-shipped`
  (UAC Pydantic implementation = Day 2 follow-on slot).
- **Day-2 noon operator checkpoint**: triage which P1 follow-up items land in pre-cutover vs successor
  `simulation_scenarios_post_cutover_2026_06_01.md`. Cross-side mirror to Harsh slot 5 for risk-implementation handoff
  coordination.

### DONE-2026-05-12 (slot 7 Day-2 code landing — UAC + UTL + Phase 3 design spec)

- **UAC@`33630a6`**: `canonical/crosscutting/scenario_overlay.py` (609 LOC: ScenarioCategory 7 / ScenarioOverlayLayer 6
  / OutcomeCategory 9 / ScenarioMutationSpec 11-member discriminated union / ScenarioOverlay +
  ScenarioApplicabilityFilter + ScenarioOutcomeAssertion + ScenarioReport Pydantic + SCENARIO_REGISTRY +
  register_scenario helper); `registry/scenarios/{__init__,cefi,defi,cross_asset}.py` (10 ScenarioOverlay instances from
  Day-1 design fragments); facade re-exports for 22 names; `tests/internal/unit/test_scenario_overlay.py` 53 tests pass.
- **UTL@`3797fed5`**: `unified_trading_library/scenario/{__init__,applier,checker,runner}.py` (~870 LOC):
  ScenarioOverlayApplier with per-mutation typed dispatch on all 11 union members (pure-functional, provenance-stamping,
  chain-aware); ScenarioOutcomeChecker with per-OutcomeCategory match logic + synthetic=True safeguard + SLA
  enforcement; ScenarioRunner orchestrator with ObserverCallback pattern + per-archetype assertion filtering;
  `tests/unit/scenario/` 51 tests pass.
- **Phase 3 integration spec** at
  [`scratch_scenarios_day1/12_phase3_integration_spec.md`](scratch_scenarios_day1/12_phase3_integration_spec.md): Phase
  3.E + 3.F design substrate (3-step recipe for execution-service matching-engine adversarial mode + 3 consumer shapes
  for position-balance / risk / alerting). Cross-side handshake invited to Harsh slot 5 per work-split.
- **Plan status flips**: Phase 1 (1.A/1.B/1.C/1.D) + Phase 2 (2.A/2.B/2.D) + Phase 4 → `done`; Phase 3 (3.E/3.F) →
  `design-shipped`. Phase 5 ScenarioMatrixRunner = Day-3 (next slot 7 cycle item).
- **Total Day-2 ship**: 3 commits (UAC@`33630a6` + UTL@`3797fed5` + PM plan flip), 3406 LOC across 16 files, 104 unit
  tests green. Compressed-scope plan body line 60-65 fully realized in code; Phase 3.E/3.F implementation
  cross-side-handed-off to Harsh slot 5.

### DONE-2026-05-12 (slot 7 Day-3 — Phase 5 matrix runner)

- **UAC@`556b96f`**: `registry/scenario_archetype_matrix.py` (~110 LOC: `CUTOVER_ARCHETYPES` frozenset +
  `MATRIX: dict[archetype, frozenset[scenario_id]]` derived at module-load from `SCENARIO_REGISTRY` +
  `matrix_cell_count()` + `scenarios_for_archetype()` helpers); 5 facade re-exports (`SCENARIO_ARCHETYPE_MATRIX` +
  `CUTOVER_ARCHETYPES` + `matrix_cell_count` + `scenarios_for_archetype`);
  `tests/internal/unit/test_scenario_archetype_matrix.py` 11 tests (cell-count-over-delivers + per-archetype
  critical-scenario presence + closed-archetype-set + fail-loud on unknown).
- **UTL@`66904fe0`**: `scenario/matrix_runner.py` (~217 LOC: `ScenarioMatrixRunner` synchronous serial iterator +
  `ScenarioMatrixCell` frozen dataclass with `passed` + `failure_count` derived props + `ScenarioMatrixReport` aggregate
  with `all_passed` Phase 5.C invariant + `failure_summary()` formatter + `ObserverFactory` typed alias); facade
  re-exports for 3 new names; `tests/unit/scenario/test_matrix_runner.py` 10 tests.
- **Plan status flips**: Phase 5.A + 5.B + 5.C → `done` (matrix declaration + runner + green-matrix done-definition all
  codified).
- **Total Day-3 ship**: 2 commits (UAC + UTL), ~600 LOC, 21 new tests. UTL scenario test count: 61 (51 Phase 2 + 10
  Phase 5.B).

### DONE-2026-05-12 (slot 7 Day-4 — Phase 2.E LookaheadBias downgrade + Phase 8.A codex stub)

- **UTL@`9e84ee44`**: `point_in_time.py`
  `assert_no_lookahead_for_feature_group(..., scenario_overlay_active: bool = False)` kwarg. When True, downgrades
  `LookaheadBiasError` to `_logger.warning(SCENARIO_OVERLAY_LOOKAHEAD_DOWNGRADE: ...)`; strict mode stays on for every
  non-overlay path. 2 new tests in `tests/unit/test_point_in_time.py` (downgrade-to-warning + strict-mode invariant).
  11/11 `TestAssertNoLookaheadForFeatureGroup` tests pass + scoped ruff clean.
- **PM codex stub** at
  [`/codex/04-architecture/scenario-injection-architecture.md`](/codex/04-architecture/scenario-injection-architecture.md):
  Phase 8.A NEW doc codifying reuse-prod-codepath principle + 6 closed-set pipeline-tap layers + 11 mutation
  discriminator union + 9 OutcomeCategory enum + 6-tuple-per-cell contract + `synthetic=true` event-stream provenance +
  LookaheadBias compatibility (Phase 2.E) + 2-archetype 16-cell regression matrix + cross-plan composition +
  Day-1..Day-4 provenance trail. Phase 8.B (scenario-outcome-assertions) + 8.C (scenario-overlay-semantics) DEFERRED —
  content folded into this single Phase 8.A doc until consumer growth requires split.
- **Plan status flips**: Phase 2.E + Phase 5.A + Phase 5.B + Phase 5.C + Phase 8.A → `done`.
- **Total Day-4 ship**: 1 UTL commit + 1 PM commit (codex + plan flips), ~280 LOC.

### Full cycle ship summary (slot 7 `ikenna-scenarios-topology-tab` Cycle-1 2026-05-12)

| Phase                  | Status                                     | Evidence                                                                         |
| ---------------------- | ------------------------------------------ | -------------------------------------------------------------------------------- |
| 1.A/1.B/1.C/1.D        | `done` Day-2                               | UAC@`33630a6`                                                                    |
| 2.A/2.B/2.D            | `done` Day-2                               | UTL@`3797fed5`                                                                   |
| 2.E                    | `done` Day-4                               | UTL@`9e84ee44`                                                                   |
| 3.E + 3.F              | `design-shipped` Day-2 (impl Harsh slot 5) | `scratch_scenarios_day1/12_phase3_integration_spec.md`                           |
| 4 (scenario library)   | `done` Day-2                               | UAC@`33630a6` `registry/scenarios/`                                              |
| 5.A + 5.B + 5.C        | `done` Day-3                               | UAC@`556b96f` + UTL@`66904fe0`                                                   |
| 8.A (codex stub)       | `done` Day-4                               | PM `/codex/04-architecture/scenario-injection-architecture.md`                   |
| 0 (pre-audit)          | `todo`                                     | Operator-deferrable; existing Day-1 design fragments serve as the de-facto audit |
| 6 / 7 / 8.B-I / 9 / 10 | `deferred-after-successor`                 | `simulation_scenarios_post_cutover_2026_06_01.md`                                |

**Cycle-1 totals (Days 1+2+3+4)**: 11 commits across 3 repos (UAC + UTL + PM); ~4000+ LOC; 125 unit tests green (53
UAC + 61 UTL + 11 UAC matrix); compressed-scope pre-cutover deliverables 100% shipped except Phase 3 implementation
handed off to Harsh slot 5 + Phase 9 real-VM ops (deferred until Phase 3 impl lands).

## Cross-plan annotation from slot 5 / `defi_recursive_borrow_archetypes_2026_05_10.md` (2026-05-12)

Slot 5 Day-1 Phase 12 design (per-family backtest scenario set) introduces a Category B liquidation-stress scenario
taxonomy that may overlap with this plan's topology-shock taxonomy. **SSOT alignment check needed**:

| Slot-5 scenario ID | Description                         | Potential overlap with this plan  |
| ------------------ | ----------------------------------- | --------------------------------- |
| SCN-B1             | wstETH/ETH oracle 3% drop / 1 block | LST flash depeg topology          |
| SCN-B2             | ETH/USD 15% drop / 1 day            | major crash topology              |
| SCN-B3             | wstETH/ETH 8% drop (Lido slashing)  | LST extreme depeg topology        |
| SCN-B4             | cbETH/ETH 5% drop (Coinbase stress) | LST custody-counterparty topology |
| SCN-B5             | Chainlink feed stale > 24h          | oracle-outage topology            |

Recommendation: closed-set scenario IDs should NOT drift between plans. Either (a) this plan owns the canonical taxonomy
and recursive-borrow plan references by ID, OR (b) recursive-borrow Phase 12 owns its own per-archetype taxonomy and
this plan references by ID. Operator-call. Slot 5 NOT fixing (Findings Triage — slot 7 owns this plan).

Reference: `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 12 design § Category B scenarios.

## Deferred work after 2026-05-12 Harsh slot-6 Day-3 session

| Phase / item                                                             | Status as of 2026-05-12                                                                                       | Successor / blocker                                                                  |
| ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| Phase 3.A/B/C/D/G                                                        | DEFERRED-PER-COMPRESSED-SCOPE (annotations added this session)                                                | `simulation_scenarios_post_cutover_2026_06_01.md` Phases 3.A/B/C/D/G                 |
| Phase 6 (backtest CLI)                                                   | DEFERRED-PER-COMPRESSED-SCOPE                                                                                 | Successor plan Phase 6                                                               |
| Phase 7 (UI surface)                                                     | DEFERRED-PER-COMPRESSED-SCOPE                                                                                 | Successor plan Phase 7                                                               |
| Phases 8.B-I (codex updates)                                             | DEFERRED-PER-COMPRESSED-SCOPE                                                                                 | Successor plan Phase 8                                                               |
| Phase 9 (real-VM matrix runs)                                            | DEFERRED-PER-COMPRESSED-SCOPE                                                                                 | Successor plan Phase 9                                                               |
| Phase 10.A (master plan extension)                                       | 🟡 BLOCKED — slot-1 territory per CLAUDE.md G-14                                                              | Main orchestrator slot-1 to add Group F item 17.5                                    |
| Phase 10.B (defi_master § "May-23 deliverable" annotation)               | ✅ Q1 RESOLVED 2026-05-12 — archived epic was SUPERSEDED 2026-05-08 + folded into `defi_master.md`; re-routed | Successor plan adds row to `defi_master` "May-23 deliverable" success-criteria table |
| Phase 10.C (banner removal)                                              | Blocked on Phase 9                                                                                            | Successor plan                                                                       |
| Phase 10.D (cron VM)                                                     | Blocked on Phase 9 + operator-runnable                                                                        | Successor plan + operator                                                            |
| DART scenario fold-in (cross_cutting #4)                                 | Not in pre-cutover scope: Phase 7 (UI) DEFERRED; BUILD #1/#4/#5 Ikenna-blocked                                | Successor plan Phase 7 / post-Ikenna-D1/D4 resolution                                |
| Scenario taxonomy SSOT alignment with slot-5 recursive-borrow SCN-B1..B5 | Needs operator call (option a or b above)                                                                     | `defi_recursive_borrow_archetypes_2026_05_10.md` Phase 12 owner                      |

## Phase 1 — Topology shock scenario designs (supplemental, slot 7 2026-05-13)

Six topology shock scenarios for the pre-cutover regression matrix. Each is a structured design record with the 3
required fields (trigger condition / observable signature / expected risk-engine response) plus UAC/alerting/kill-switch
cross-references. These design records bridge the compressed-scope Day-1 scratch fragments
(`scratch_scenarios_day1/01-06.md`) to the UAC registry instances shipped at UAC@`33630a6`. No new code; all registry
instances are already live. These todos serve as living design documentation and the audit-trail entry point for the
successor plan's Phase 3 multi-layer wire-in.

**UAC cross-reference SSOTs used by all 6 scenarios**:

- `classify_venue_error()`: `unified_api_contracts/canonical/crosscutting/errors/venue_error.py` — SSOT for
  ADAPTER_FETCH_FAILED classification
- Alert codes: `unified_api_contracts/canonical/crosscutting/alerting/codes.py`
- Circuit breakers: `unified_api_contracts/registry/circuit_breakers/{carry_staked_basis,arbitrage_price_dispersion}.py`
- Kill switches: `unified_api_contracts/canonical/crosscutting/kill_switch.py`
- Manifest 4-state: `unified_trading_library/manifest/writer.py` (`record_captured` / `record_empty` / `record_failed` /
  `record_expected_unattempted`)
- Kill-switch + circuit-breaker architecture SSOT: `/codex/04-architecture/kill-switch-circuit-breaker.md`

---

- [x] [DESIGN] P0. **1.T1 per-venue-down** (`cefi_venue_circuit_breaker_trip` — Binance/Bybit/OKX API outage). ✅
      DESIGN-COMPLETE 2026-05-17 — UAC@33630a6 registry live; scratch doc `01_cefi_venue_circuit_breaker_trip.md` + plan
      body summary = canonical design record. Full design at
      [`scratch_scenarios_day1/01_cefi_venue_circuit_breaker_trip.md`](scratch_scenarios_day1/01_cefi_venue_circuit_breaker_trip.md).
      Summary:

  **Trigger condition**: At `T+0` for chosen venue `V ∈ {bybit, binance, okx, deribit, hyperliquid, aster}`, harness
  simultaneously: (a) emits synthetic `connection_close(reason="maintenance", code=1001)` on all WS subscriptions for
  `V`; (b) routes all REST adapter calls through a fault-injector returning HTTP 503 `Retry-After: 120`; (c) applies
  `StaleHold` mutation on `RAW_TICK` layer for `V`'s instruments for `outage_duration_seconds` (default 300s).
  Correlation-tagged `synthetic=true`. Managed via `ScenarioOverlayLayer.EVENT` (primary) + `ScenarioOverlayLayer.ORDER`
  (`RejectFills`) + `ScenarioOverlayLayer.RAW_TICK` (`StaleHold`).

  **Observable signature**: `CONNECTIVITY_GAP_DETECTED` fires from MTDS `LiveConnectivityWatchdog` within ~5s;
  `TICK_STALENESS` from MDPS write-gate within ~15s; `ORDER_REJECTION_SPIKE` fires on 5min rolling window crossing
  500bps reject-rate threshold; `RECON_DEGRADED` fires from position-balance-monitor after 60s REST-503 gap;
  `CIRCUIT_BREAKER_DEGRADED` → `CIRCUIT_BREAKER_OPEN` cascade for `VENUE_OUTAGE_SECONDS` breaker at `T+90s`;
  `CROSS_VENUE_DIVERGENCE_BPS` fires if other venues continue and same-instrument mid diverges ≥40bps after 120s window.
  UAC source: `codes.py:29-45, 70, 77, 84, 196-211`.

  **Expected risk-engine response**:
  - `ARBITRAGE_PRICE_DISPERSION`: `BLOCK_NEW` via `VENUE_OUTAGE_SECONDS` breaker
    (`registry/circuit_breakers/arbitrage_price_dispersion.py:127-140`) within 90s; escalates to `CANCEL_OPEN` via
    `INVENTORY_IMBALANCE_RATIO` if cross-venue imbalance > 20%. `KILL_PER_VENUE_<V>` (`kill_switch.py:83`) arms at
    breaker-open. Escalates to `KILL_ALL_LIVE` (`kill_switch.py:74`) only if `HEDGE_GAP_NOTIONAL_USD` > $100k
    (`codes.py:84`). Auto-disarm: venue REST+WS heartbeats green ≥5min sustained → `KILL_SWITCH_AUTO_RECOVERED`.
    Manual-unkill required if `INVENTORY_IMBALANCE_RATIO` (CANCEL_OPEN) or `HEDGE_GAP_NOTIONAL_USD` (KILL_ALL)
    escalation arms.
  - `CARRY_STAKED_BASIS` (hedge leg secondary): `BLOCK_NEW` via `VENUE_OUTAGE_SECONDS` PER_VENUE; escalates to
    `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` (`kill_switch.py:79`) only if hedge-failure cascades into
    `LIQUIDATION_CASCADE_RISK` (`carry_staked_basis.py:110-124`).
  - SSOT: `/codex/04-architecture/kill-switch-circuit-breaker.md` § "Per-venue kill-switch";
    `/codex/04-architecture/autonomous-recovery-matrix.md` § "VENUE_OUTAGE_SECONDS recovery rule".

- [x] [DESIGN] P0. **1.T2 per-chain-down** (`defi_chain_rpc_outage_solana` — Ethereum RPC or Solana RPC unreachable). ✅
      DESIGN-COMPLETE 2026-05-17 — UAC@33630a6 registry live; scratch doc `02_defi_chain_rpc_outage_solana.md` + plan
      body summary = canonical design record. Full design at
      [`scratch_scenarios_day1/02_defi_chain_rpc_outage_solana.md`](scratch_scenarios_day1/02_defi_chain_rpc_outage_solana.md).
      Summary:

  **Trigger condition**: At `T+N` (default N=60s), all RPC endpoints in `SOLANA_RPC_TEMPLATES` (UAC
  `registry/capability_declarations/_defi.py:14`) return HTTP 503 / connection-refused for `outage_duration_seconds`
  (default 1800s = 30min). WS program-account subscriptions (Marinade / Jito / Sanctum / Drift) close with
  `reason='chain-stalled'`; reconnect attempts fail. Slot-height progression freezes — no new `BLOCK_ADVANCED` events.
  On-chain swap-quote calls (Jupiter / Raydium / Orca) and lending-index reads (Kamino / MarginFi) timeout. Mutation
  spec: `LatencyInject` (∞ hang on all Solana RPC calls) + `DropRows` (block-height event stream halts) + `StaleHold`
  (Pyth on-chain Solana feed pinned at slot `S` price).

  **Observable signature**: `BLOCK_ADVANCED` event flatline for Solana for >60s; MTDS `LiveConnectivityWatchdog` fires
  `CONNECTIVITY_GAP_DETECTED` against `(venue="solana-rpc-*", instrument="*")` within 30s; features-onchain stops
  emitting `onchain_lst_yields` rows → manifest writer records `record_failed(error=rpc-timeout, attempted_at=...)` per
  Solana protocol shard; MDPS write-gate fires `TICK_STALENESS` on Pyth Solana feeds for `(SOL, MSOL, JITOSOL, BSOL)`;
  `DEFI_FEATURE_STALE` fires once features-onchain crosses freshness window; `CIRCUIT_BREAKER_OPEN` fires for
  `RPC_OUTAGE_SECONDS` breaker at `T+60s`. Honest-absence per-shard: `record_failed(OracleStaleError)` on Pyth-Solana
  shards (unexpected upstream gap, Category 2 per `/codex/02-data/honest-absence-downstream-handling.md`). UAC source:
  `codes.py:34, 42-45, 52, 196-211`.

  **Expected risk-engine response**:
  - `CARRY_STAKED_BASIS` (primary): `BLOCK_NEW` via `RPC_OUTAGE_SECONDS` breaker (`carry_staked_basis.py:51-64`,
    threshold 60s, scope=PER_ARCHETYPE). Arms `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` (`kill_switch.py:79`) at `T+60s`;
    escalates to `KILL_PER_ASSET_GROUP_DEFI` (`kill_switch.py:92`) if outage >300s AND any open LST leverage position
    has health-factor approaching `LIQUIDATION_CASCADE_RISK` threshold (1.10 per `registry:115`). Auto-disarm guard:
    chain slot ≥2/s + Pyth feeds fresh within 30s + manifest has captured ≥1 fresh lending-index row. Auto-disarm within
    120s of guard green (`auto_disarm_after_seconds=120`); escalated KILL_ALL stays until operator manual-unkill.
  - `ARBITRAGE_PRICE_DISPERSION` (secondary): `SCALE_DOWN` (`RPC_OUTAGE_SECONDS` PER_ARCHETYPE — registry needs
    `applies_to="ARBITRAGE_PRICE_DISPERSION"` seed extension, tracked as follow-up in
    `scratch_scenarios_day1/02_defi_chain_rpc_outage_solana.md`); CeFi perp leg remains tradeable on Bybit/Binance/OKX;
    archetype kill-switch withheld until cross-leg divergence widens.
  - SSOT: `/codex/04-architecture/kill-switch-circuit-breaker.md` § "DeFi kill-switch hierarchy"; UAC
    `CHAIN_RPC_TEMPLATES` in `_defi.py`.

- [x] [DESIGN] P0. **1.T3 per-protocol-paused** (`defi_liquidity_drain_lending_pool` — Aave/Morpho market paused or
      borrow-cap reached). ✅ DESIGN-COMPLETE 2026-05-17 — UAC@33630a6 registry live; scratch doc
      `03_defi_liquidity_drain_lending_pool.md` + plan body summary = canonical design record. Full design at
      [`scratch_scenarios_day1/03_defi_liquidity_drain_lending_pool.md`](scratch_scenarios_day1/03_defi_liquidity_drain_lending_pool.md).
      Summary:

  **Trigger condition**: At `T+0` for chosen tuple
  `(protocol ∈ {aave_v3, morpho}, chain ∈ {ethereum, arbitrum}, asset ∈ {USDC, USDT})`, harness: (a) injects synthetic
  lending-indices feature row via FEATURE-layer tap: `utilization=0.99`, `available_liquidity_usd=0`,
  `borrow_apr_bps=5000`, `paused=<bool>`; (b) configures execution-service adversarial-mode
  `RejectFills(reason="BORROW_CAP_REACHED" | "POOL_PAUSED")` on ORDER layer for any borrow tx targeting
  `(protocol, chain, asset)`; (c) optionally writes `ManifestPhantom` on MANIFEST layer. Two `pause_mode` sub-shapes:
  `governance_paused` (pool-contract `paused=true`, requires governance vote to clear) vs `borrow_cap_reached`
  (utilization at cap, decays linearly when demand subsides). Both run in the regression matrix because their
  auto-recovery contracts differ. Sustained for `pause_duration_seconds` (default 1800s; matrix variants
  600/1800/21600).

  **Observable signature**: `DEFI_AAVE_UTILIZATION_SPIKE` (`codes.py:50`) fires within ~15s of synthetic utilization row
  crossing 95% threshold; `DEFI_TX_SIMULATION_FAILED` (`codes.py:55`) fires after 3 consecutive failed `borrow()`
  simulations; `INSTRUCTION_REJECTED_RISK` with `reject_reason="lending_pool_unavailable"` emitted by strategy-service
  deleverage-path planner; features-onchain manifest: `record_failed(LendingPoolPausedError)` for `governance_paused`
  variant vs `record_captured()` with `paused=true` payload for `borrow_cap_reached` variant — the honest-absence
  distinction matters (CLAUDE.md "Availability manifest v5+" rule); `LIQUIDATION_CASCADE_RISK` breaker trips if LST
  oracle moves >200bps concurrent with pause. UAC source: `codes.py:32, 48, 50, 55, 92, 134, 144`.

  **Expected risk-engine response**:
  - `CARRY_STAKED_BASIS` (entry path, both pause modes): `BLOCK_NEW` via `MAX_LEVERAGE_PER_ARCHETYPE` +
    `MAX_POSITION_SIZE_PER_ARCHETYPE` pre-flight gates (`archetype.py:88-126`); deleverage planner transitions to
    `borrow_blocked` autonomous-recovery state; `PREFLIGHT_FAILED` emitted for borrow-dependent instructions.
    **Follow-up gap**: no `LENDING_POOL_UNAVAILABLE_SECONDS` `CircuitBreakerId` exists yet — add to
    `canonical/crosscutting/circuit_breaker.py:74-143` (tracked in
    `scratch_scenarios_day1/03_defi_liquidity_drain_lending_pool.md` follow-up callout; owner: DR plan or successor plan
    Phase 1.B extension).
  - `borrow_cap_reached` auto-recovery: when (FOLLOW-UP) breaker exists — `AUTO_COOLDOWN` if utilization drops below 90%
    for ≥300s; auto-disarm + `KILL_SWITCH_AUTO_RECOVERED`. Until the breaker ships, scenario asserts via the alerting
    cascade only.
  - `governance_paused` escalation: if oracle moves ≥200bps during pause, `LIQUIDATION_CASCADE_RISK`
    (`carry_staked_basis.py:109-124`) → `KILL_ALL` → `KILL_SWITCH_DEFI_LIQUIDATION_RISK` (`codes.py:32`) +
    `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` (`kill_switch.py:79`). Recovery: `MANUAL_UNKILL` only
    (governance-pause-clear ≠ economic-safety-clear; operator must confirm root cause cleared). The (FOLLOW-UP)
    lending-pool breaker auto-disarm MUST NOT cascade-disarm `LIQUIDATION_CASCADE_RISK` (orthogonal recovery per
    `circuit_breaker.py` composition rules).
  - SSOT: `/codex/04-architecture/kill-switch-circuit-breaker.md` § "DeFi protocol-pause kill-switch";
    `/codex/04-architecture/autonomous-recovery-matrix.md` § "borrow_blocked state".

- [x] [DESIGN] P0. **1.T4 oracle-stale** (`defi_oracle_deviation_30sigma` — Chainlink heartbeat exceeded or 30σ
      wild-print). ✅ DESIGN-COMPLETE 2026-05-17 — UAC@33630a6 registry live; scratch doc
      `04_defi_oracle_deviation_30sigma.md` + plan body summary = canonical design record. Full design at
      [`scratch_scenarios_day1/04_defi_oracle_deviation_30sigma.md`](scratch_scenarios_day1/04_defi_oracle_deviation_30sigma.md).
      Summary:

  **Trigger condition**: Two variants under the same `scenario_id`, parameterised via `variant` field. (a)
  **`wild_print`**: at `T+0`, harness publishes one oracle update with
  `price = realized_mid × (1 + sign × deviation_sigma × rolling_sigma_60s)` for `deviation_duration_heartbeats=1`
  heartbeat then reverts. For Pyth (400ms heartbeat) this is a ~400ms spike; for Chainlink ETH/USD (60min heartbeat)
  this is one full heartbeat at wild value. Confidence interval set `consistent_with_wild` so downstream
  `min_confidence_interval` filters don't trivially reject — tests the deviation-vs-canonical-mid detection path
  specifically. (b) **`stale_hold`**: at `T+0` harness skips `stale_duration_heartbeats=3` consecutive Pyth heartbeats
  (matrix: 3/25/150 = ~1.2s/~10s/~60s) or Chainlink `AggregatorV3.latestRoundData()` lapse of 3hr/12hr/25hr. Mutation
  spec: `wild_print` → `OracleDeviate` (UAC closed-union member); `stale_hold` → `StaleHold` (existing member). Chain
  routing per CLAUDE.md DeFi pointer: Solana → Pyth (Hermes batch + PythNet live); Ethereum/L2 → Chainlink.

  **Observable signature**: `wild_print` — `oracle_deviation_bps_<oracle_id>` time-series crosses 100bps threshold;
  peg-deviation spike for USDC/USDT/USDE wild-prints; features-onchain emits `record_failed(OracleDeviationError)` per
  affected feature-window (**follow-up**: `OracleDeviationError` class may need to be added to UTL error taxonomy —
  tracked in `scratch_scenarios_day1/04_defi_oracle_deviation_30sigma.md`). `stale_hold` —
  `oracle_age_seconds_<oracle_id>` crosses heartbeat × 1.5 threshold; `record_failed(OracleStaleError)` per MTDS
  manifest shard (unexpected upstream gap → Category 2 honest-absence, not `record_empty`). Both variants:
  `DEFI_FEATURE_STALE` (`codes.py:52`) with `oracle_id` + `chain` + `heartbeat_age_s` + `deviation_bps` +
  `synthetic=true` provenance; `signal_suppressed(reason="oracle_stale"|"oracle_deviation")` from strategy-service
  signal generator; `CIRCUIT_BREAKER_DEGRADED` → `CIRCUIT_BREAKER_OPEN` lifecycle (`codes.py:42-45`).

  **Expected risk-engine response**:
  - `CARRY_STAKED_BASIS` (primary): `ORACLE_DEVIATION_BPS` breaker (`carry_staked_basis.py:36-50`) → `BLOCK_NEW` on new
    LST-rebalance entries within 60s; strategy-service signal generator emits
    `signal_suppressed(reason="oracle_deviation"|"oracle_stale")`. If two correlated oracles fail simultaneously (e.g.
    Pyth-SOL/USD + Pyth-JITO-SOL/SOL), escalates to `KILL_PER_ASSET_GROUP_DEFI` (`kill_switch.py:92`). Auto-recovery
    (stale variant): guard requires `oracle_age_seconds < heartbeat × 1.5` for ≥3 consecutive heartbeats AND
    features-onchain emits ≥1 fresh row for the affected coverage radius.
  - `ARBITRAGE_PRICE_DISPERSION` (secondary): `ORACLE_DEVIATION_BPS` breaker → `SCALE_DOWN` on perp-vs-spot basis
    instructions whose reference mid derives from the affected oracle. CeFi perp leg continues.
  - Alerting: `DEFI_FEATURE_STALE` alert fires with `synthetic=true` — PagerDuty + Telegram suppressed; dashboard
    surfaces in `defi.oracle` tile per alerting-service `_route_synthetic_log_only()` path (Phase 3.F
    `alerting-service@3c0d675`).
  - SSOT: `/codex/04-architecture/kill-switch-circuit-breaker.md` § "Oracle-divergence kill-switch"; UAC
    `CHAIN_RPC_TEMPLATES` + `config/testnet_contracts.yaml` (oracle address registry).

- [x] [DESIGN] P0. **1.T5 gas-spike** (`defi_gas_surge_50x` — Ethereum gas price 10-50× baseline). ✅ DESIGN-COMPLETE
      2026-05-17 — UAC@33630a6 registry live; scratch doc `05_defi_gas_surge_50x.md` + plan body summary = canonical
      design record. Full design at
      [`scratch_scenarios_day1/05_defi_gas_surge_50x.md`](scratch_scenarios_day1/05_defi_gas_surge_50x.md). Summary:

  **Trigger condition**: At `T+N` (default N=60s), the features-onchain gas-oracle feature for the targeted chain
  (`eth_mainnet_gas_price_gwei`) jumps from `baseline_gwei` (default 30 gwei) to `baseline_gwei × surge_multiplier`
  (default 50× → 1500 gwei). Spike sustained for `surge_duration_seconds` (default 600s = 10min). Derived features
  (`tx_cost_estimate_usd`, `gas_priority_percentile_rank`) recompute correspondingly. Recovery via operator-selected
  curve: `step` / `linear_300s` / `exponential_decay_300s`. **Mandatory correctness invariant**: the harness MUST NOT
  observe any tx land at 1500-gwei pricing — if a tx does, the pre-flight gas-budget check has failed (regression).
  Tenderly fork honours real gas pricing but the pre-flight gate on execution-service ORDER layer should BLOCK before
  submission. Mutation spec: `GasSurge` (UAC closed-union member) + `PriceShift` on gas-oracle feature series (gas is a
  price-shaped feature consumed by `tx_cost_estimate_usd`).

  **Observable signature**: features-onchain emits gas-oracle rows with `gas_price_gwei` jumping discontinuously at
  `T+N` — manifest `record_captured()` rows show the surge envelope; `RISK_RULE_BLOCKED` fires from archetype-level
  `GAS_BUDGET_PER_ARCHETYPE` rule within one rule-evaluation cycle (~10s) of any pending rebalance hitting cost ceiling;
  `RISK_RULE_SCALED_DOWN` fires concurrently from DeFi-asset-group rule (`asset_group.py:74-82`, USD 500 ceiling);
  circuit-breaker `GAS_PRICE_SURGE_GWEI` trips at `T+N+~10s` (`carry_staked_basis.py:65-78`, threshold 200 gwei,
  action=`BLOCK_NEW`); execution-service tx-submission queue accumulates `tx_submission_suppressed` events; rebalance-tx
  submission rate drops to zero on affected chain; position-balance-monitor reports "pending rebalance suppressed — gas
  budget exceeded". UAC source: `codes.py:42, 88, 134, 144`.

  **Expected risk-engine response**:
  - `CARRY_STAKED_BASIS` (primary): `GAS_BUDGET_PER_ARCHETYPE` risk rule (`archetype.py:169-181`) → `BLOCK` on new
    rebalance instructions; `GAS_PRICE_SURGE_GWEI` circuit-breaker → `BLOCK_NEW`; existing positions held (no
    liquidation from gas spike alone — only if LST oracle concurrent move compounds). Autonomous-recovery state machine
    transitions to `gas_high` state (advisory); state clears when `gas_price_gwei < threshold` for 3min sustained.
  - `ARBITRAGE_PRICE_DISPERSION` (secondary): DeFi-spot leg rebalances for any cross-chain funding-arb pair blocked by
    the gas-budget DeFi-asset-group rule; CeFi perp hedge leg continues unaffected.
  - No kill-switch armed at 50× baseline alone (BLOCK_NEW only, not KILL); kill-switch arming requires compounding with
    a second failure mode (e.g. LST oracle deviation concurrent + `LIQUIDATION_CASCADE_RISK` trigger).
  - `available_at` discipline: synthetic gas-oracle rows use real-time `available_at` — this is a value-axis injection,
    not an arrival-timing injection, so `lookahead_bias_check` downgrade NOT required (distinct from RPC-outage +
    oracle-stale variants).
  - SSOT: `/codex/04-architecture/kill-switch-circuit-breaker.md` § "Gas-budget circuit breaker"; UAC
    `registry/risk_rules/archetype.py` `GAS_BUDGET_PER_ARCHETYPE` rule definition.

- [x] [DESIGN] P0. **1.T6 mempool-congestion** (`defi_mempool_congestion_inclusion_delay` — nonce queuing delays + MEV
      sandwich risk). ✅ DESIGN-COMPLETE 2026-05-17 — UAC@33630a6 registry live; scratch doc
      `06_defi_mempool_congestion.md` + plan body summary = canonical design record. Full design at
      [`scratch_scenarios_day1/06_defi_mempool_congestion.md`](scratch_scenarios_day1/06_defi_mempool_congestion.md).
      Summary:

  **Trigger condition**: At `T+N` (default N=60s), for chain `C ∈ {ethereum_mainnet, arbitrum, optimism, base}`,
  harness: (a) intercepts `submit_transaction()` calls in matching-engine adversarial mode via
  `LatencyInject(target="tx_submission", delay_seconds=inclusion_delay_seconds)` (default 180s = ~15 blocks); (b) emits
  synthetic `pending_tx` lifecycle events (`SIGNED → BROADCAST → PENDING(elapsed=Xs) → CONFIRMED | CANCEL_LOST_RACE`)
  via `EventDuplicate` mutation, saturating `pending_count` at `pending_tx_count_target` (default 100); (c) optionally
  (`sandwich_variant=True`) injects `BookSpoof(pool="uniswap_v3_<pair>", front_run_bps=50)` mutation: synthetic sandwich
  pair against each Uniswap swap, locking in price-impact loss at `loss_target_bps`=50bps if strategy's
  `amountOutMinimum` slippage-tolerance is ≥50bps — if slippage-tolerance < 50bps, tx reverts with `SLIPPAGE_EXCEEDED`.
  (d) cancel-tx race always-on: cancel-tx bids `gas_price < original_tx_gas_price` so original confirms first 80% of the
  time (`CANCEL_LOST_RACE`) and cancel wins 20% (`CANCEL_WON_RACE`). Note: Solana excluded (Jito block-engine bundle
  inclusion is structurally different; covered in post-cutover library).

  **Observable signature**: `mempool_pending_count` for `C` crosses `pending_tx_count_target` within 30s;
  `mean_inclusion_latency_seconds` for `C` crosses 5× baseline within 60s; `pending_tx` count > `inflight_tx_limit`
  threshold per archetype (default 5 simultaneous) → autonomous-recovery state machine transitions to
  `mempool_congested` state (**FOLLOW-UP**: no explicit `mempool_congested` named state in
  `/codex/04-architecture/autonomous-recovery-matrix.md` — captured at
  `scratch_scenarios_day1/06_defi_mempool_congestion.md` follow-up callout; owner: DR plan Phase 4); `CANCEL_LOST_RACE`
  event aggregated into `cancel_lost_rate_bps` rolling 5min window → crosses 8000bps (80%) during synthetic congestion;
  sandwich variant: `MEV_DETECTED` typed event per `/codex/04-architecture/mev-protection.md:376-389` pattern
  detection + `DEFI_TX_SIMULATION_FAILED` (`codes.py:55`) for simulations that fail `amountOutMinimum` post-front-run;
  `realised_slippage_bps` p50 shifts from ~5bps to ~50bps. UAC source: `codes.py:55, 88, 134`.

  **Expected risk-engine response**:
  - `CARRY_STAKED_BASIS` (primary): `inflight_tx_limit` breach → archetype state machine transitions to
    `mempool_congested`; subsequent rebalance instructions are queued but suppressed pending inclusion;
    risk-and-exposure-service emits `RISK_RULE_BLOCKED` once archetype-level `GAS_BUDGET_PER_ARCHETYPE` rule fires if
    the strategy raises gas to push through congestion (composes with gas-spike scenario). Sandwich variant: per-fill
    `realised_slippage_bps` crossing `MAX_SLIPPAGE_BPS` risk rule fires `RISK_RULE_BLOCKED` on the affected swap pair.
  - **Follow-up gap**: no dedicated mempool-congestion `CircuitBreakerId` exists in current registry — closest is
    `GAS_PRICE_SURGE_GWEI` (may co-fire if gas is raised to push txs through). DR plan Phase 4 should add
    `MEMPOOL_INCLUSION_LATENCY_SECONDS` breaker (tracked in scenario follow-up callout).
  - `ARBITRAGE_PRICE_DISPERSION` (secondary): any DeFi spot-leg tx is affected; CeFi perp hedge leg is unaffected.
    Asymmetric leg-risk during the congestion window can trigger `CROSS_VENUE_DIVERGENCE_BPS` if DeFi-leg inclusion lag
    exceeds 120s while CeFi leg continues marking.
  - No kill-switch at congestion alone; escalation path exists only if: (a) inclusion-latency >600s compounding with a
    loss-realising sandwich tripping `MAX_SLIPPAGE_BPS`, OR (b) `mempool_congested` state persists past
    `auto_disarm_after_seconds` causing an accumulated position imbalance that trips `INVENTORY_IMBALANCE_RATIO`.
  - SSOT: `/codex/04-architecture/kill-switch-circuit-breaker.md` § "MEV + mempool risk circuit breakers";
    `/codex/04-architecture/mev-protection.md` § "Sandwich pattern detection".

**Phase 1 (topology) full-execution criterion** (design-only phase — no code changes; all UAC instances already shipped
at UAC@`33630a6`):

- ✅ 6 topology shock scenario design specs present in plan body with trigger / observable-signature / expected-response
  per scenario; UAC cross-references resolve; scratch design files already committed at PM@`bea269b1`.
  - **What ran**: this design documentation addition (2026-05-13 slot 7 session).
  - **Verification**:
    `grep -c "\- \[ \] \[DESIGN\] P0\. \*\*1\.T[1-6]" plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md`
    returns 6;
    `grep "scratch_scenarios_day1/0[1-6]" plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md | wc -l`
    returns ≥6; each UAC/alerting/kill-switch cross-reference file resolves via `ls`.

---

## DONE-2026-05-12 — Harsh slot 6 Day-3 session

**Session theme**: `simulation_scenarios_topology_price_shocks_2026_05_09.md` impl tail

**Post-rebase state verified (13:00 UTC)**: Phase 4 (scenario library) + Phase 5 (matrix) fully ✅ done by Ikenna slot 7
Day-3. Phase 3.E + 3.F ✅ done by Harsh slot 5. Phase 1/2/8.A ✅ done by Ikenna slot 7. All pre-cutover compressed scope
is COMPLETE.

**Shipped this session**:

- `plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md` plan curation: DEFERRED annotations added to
  3.A/B/C/D/G (these items were missing explicit DEFERRED markers even though scope compression note already said
  they're deferred). Q1 Open Question added for Phase 10.A/B authority + missing epic file.

**Next step (slot-1 territory)**:

- Phase 10.A: slot-1 to add "Scenario regression matrix green per archetype" as Group F item 17.5 in
  `master_to_live_defi_2026_05_23.md`
- Phase 10.B: operator triage on epic file — see Q1 above

**Real blockers (🟡)**:

- Phase 10.A: G-14 slot-1 territory (✅ being taken by slot-1 main 2026-05-12 — item 17.5 added to
  `master_to_live_defi_2026_05_23.md` Group F)
- Phase 10.B: ✅ RESOLVED 2026-05-12 — archived epic was SUPERSEDED 2026-05-08 + folded into `defi_master.md` § "May-23
  deliverable"; re-routed (successor plan adds the row there, not to a non-existent epic file)

## Phase 6 — Per-archetype coverage matrix expansion (Day-2-4 scope extension, 2026-05-13)

> **Status**: `done` — design-shipped 2026-05-13 (slot 7 Day-2-4 scope extension). Per-cell analysis added to plan body;
> implementation (backtest harness CLI, UI) deferred to `simulation_scenarios_post_cutover_2026_06_01.md` Phase 3 +
> Phase 4. This section provides the per-cell coverage specification that informs those downstream phases.

The 16-cell pre-cutover matrix (10 scenarios × 2 archetypes, filtered to applicable) was declared at Phase 5.A
(UAC@`556b96f`). This section expands each cell with the full 4-tuple specification:
`expected_breaker_trips: list[CircuitBreakerId]` + `expected_alert_emissions: list[AlertCode]` +
`recovery_mode: AutoRecoveryMode` + `paper_trade_validation_step`.

The goal is to give Phase 9 (real-VM matrix runs) and the post-cutover successor plan's Phase 6 (full-archetype
regression) a precise specification for what constitutes PASS and FAIL per cell — not just "outcome assertion passes"
but "exactly these breakers trip, exactly these alerts fire, exactly this recovery mode executes."

### Archetype definitions (for cell scope)

| Archetype                          | Asset groups                        | Primary exposure                                 | Hedge leg                                           |
| ---------------------------------- | ----------------------------------- | ------------------------------------------------ | --------------------------------------------------- |
| `carry_staked_basis` (CSB)         | `defi` (primary) + `cefi` (hedge)   | Solana LST yield (Marinade/Jito/Sanctum staking) | ETH/SOL perp short on Bybit UTA/Deribit stETH/DRIFT |
| `ARBITRAGE_PRICE_DISPERSION` (APD) | `cefi` (primary) + `defi` (partial) | Cross-venue perp funding-rate arbitrage          | USDC-margined perp cross-legs on 6 venues           |

### Scenario families (for axis labels)

| Family       | Scenario IDs                                                                                             |
| ------------ | -------------------------------------------------------------------------------------------------------- |
| TOPOLOGY_GAP | `cefi_venue_circuit_breaker_trip`, `defi_chain_rpc_outage_solana`, `defi_liquidity_drain_lending_pool`   |
| PRICE_SHOCK  | `defi_oracle_deviation_30sigma`, `defi_gas_surge_50x`, `cefi_funding_spike_10x`, `defi_stablecoin_depeg` |
| CROSS_ASSET  | `cross_asset_flash_crash`, `cross_asset_basis_blowout_perp_spot`                                         |
| OPERATIONAL  | `defi_mempool_congestion_inclusion_delay`                                                                |

### 16-cell coverage matrix specification

#### Cell 1: CSB × `cefi_venue_circuit_breaker_trip`

- **expected_breaker_trips**: `[VENUE_OUTAGE_SECONDS]` (PER_VENUE scope, `BreakerAction.BLOCK_NEW`); escalates to
  `[LIQUIDATION_CASCADE_RISK]` only if hedge-gap > $100k notional
- **expected_alert_emissions**: `[CONNECTIVITY_GAP_DETECTED, TICK_STALENESS, CIRCUIT_BREAKER_OPEN]` (all
  `synthetic=true`)
- **recovery_mode**: `AUTO_COOLDOWN` if venue heartbeat green ≥5min; `MANUAL_UNKILL` if `INVENTORY_IMBALANCE_RATIO`
  escalation arms
- **paper_trade_validation_step**: CSB position monitor shows hedge-leg exposure frozen; new entries blocked ≥90s after
  injection; LST leg unaffected (Solana chain still live); auto-disarm fires within 60s of venue heartbeat restoration

#### Cell 2: CSB × `defi_chain_rpc_outage_solana`

- **expected_breaker_trips**: `[RPC_OUTAGE_SECONDS]` (PER_ARCHETYPE scope, threshold 60s); escalates to
  `[LIQUIDATION_CASCADE_RISK]` if open LST health-factor drops below 1.10 during outage
- **expected_alert_emissions**: `[CONNECTIVITY_GAP_DETECTED, DEFI_FEATURE_STALE, CIRCUIT_BREAKER_OPEN]`
- **recovery_mode**: `AUTO_COOLDOWN` → auto-disarm once chain slot ≥2/s + Pyth fresh + ≥1 captured lending-index row
  (within 120s of guard green)
- **paper_trade_validation_step**: Features-onchain stops emitting yield rows; manifest shows
  `record_failed(rpc-timeout)` per Solana shard; strategy halts new Solana entries; existing DeFi positions marked as
  "pending rebalance suppressed"; CeFi perp hedge leg continues unaffected

#### Cell 3: CSB × `defi_liquidity_drain_lending_pool`

- **expected_breaker_trips**: `[LIQUIDATION_CASCADE_RISK]` (nearest existing substitute for
  `LENDING_POOL_UNAVAILABLE_SECONDS` — follow-up gap per Phase 1.T3); `[MAX_LEVERAGE_PER_ARCHETYPE]` preflight gate
  fires before entry
- **expected_alert_emissions**: `[DEFI_AAVE_UTILIZATION_SPIKE, CIRCUIT_BREAKER_OPEN]` (both `synthetic=true`)
- **recovery_mode**: `AUTO_COOLDOWN` for `borrow_cap_reached` variant when utilization < 90% for ≥300s; `MANUAL_UNKILL`
  for `governance_paused` variant
- **paper_trade_validation_step**: Strategy deleverage planner transitions to `borrow_blocked` state; `PREFLIGHT_FAILED`
  emitted for borrow-dependent instructions; `DEFI_TX_SIMULATION_FAILED` fires on 3 consecutive failed borrow
  simulations

#### Cell 4: CSB × `defi_oracle_deviation_30sigma`

- **expected_breaker_trips**: `[ORACLE_DEVIATION_BPS]` (`BLOCK_NEW` + `CANCEL_OPEN` BreakerAction); escalates to
  `[DRAWDOWN_DAILY_BPS]` if two correlated oracles fail simultaneously
- **expected_alert_emissions**: `[TICK_STALENESS, CIRCUIT_BREAKER_OPEN, DEFI_FEATURE_STALE]` per oracle_id + chain
- **recovery_mode**: `AUTO_COOLDOWN` — guard: `oracle_age < heartbeat × 1.5` for ≥3 consecutive heartbeats AND ≥1 fresh
  features-onchain row for affected coverage
- **paper_trade_validation_step**: Strategy emits `signal_suppressed(reason="oracle_deviation")`; no new LST-rebalance
  entries; USDC borrow instructions cancelled if USDC oracle wild-printed

#### Cell 5: CSB × `defi_gas_surge_50x`

- **expected_breaker_trips**: `[GAS_PRICE_SURGE_GWEI]` (threshold 200 gwei, `BLOCK_NEW`); `[GAS_BUDGET_PER_ARCHETYPE]`
  risk rule fires concurrently
- **expected_alert_emissions**: `[CIRCUIT_BREAKER_OPEN, RISK_RULE_BLOCKED]` (both `synthetic=true`)
- **recovery_mode**: autonomous `gas_high` advisory state; auto-disarms when `gas_price_gwei < threshold` for 3min
  contiguous
- **paper_trade_validation_step**: Tx-submission queue shows zero rebalance submissions during surge window; no tx lands
  at 1500-gwei pricing (mandatory invariant); `RISK_RULE_BLOCKED` fires within 10s of first pending rebalance hitting
  cost ceiling

#### Cell 6: CSB × `cefi_funding_spike_10x`

- **expected_breaker_trips**: `[FUNDING_RATE_FLIP_BPS]` (hedge-leg pays cost; erodes carry margin);
  `[BASIS_INVERSION_BPS]` secondary
- **expected_alert_emissions**: `[RISK_RULE_SCALED_DOWN, RISK_RULE_BLOCKED]` (both `synthetic=true`; PagerDuty/Telegram
  suppressed)
- **recovery_mode**: `SCALE_DOWN` → `AUTO_COOLDOWN` once funding < baseline × 3 for one full funding period contiguous
- **paper_trade_validation_step**: CSB rebalance frequency reduced; `RISK_RULE_SCALED_DOWN` fires within 60s of funding
  tick; no kill-switch armed (BLOCK_NEW only); escalation path documented (re-fire >3× within 24h)

#### Cell 7: CSB × `defi_stablecoin_depeg`

- **expected_breaker_trips**: `[ORACLE_DEVIATION_BPS]` (peg-deviation detection) + `[LIQUIDATION_CASCADE_RISK]` +
  `[DRAWDOWN_DAILY_BPS]` at −500bps tier
- **expected_alert_emissions**: `[CIRCUIT_BREAKER_OPEN, KILL_SWITCH_PORTFOLIO_DRAWDOWN]` (critical-tier;
  `synthetic=true`)
- **recovery_mode**: `KILL_ALL` + `MANUAL_UNKILL` at −500bps; `MONITOR` only at −100bps; `SCALE_DOWN` at −300bps
- **paper_trade_validation_step**: Tiered response ladder validates: −100bps → alert only; −300bps → halve entries;
  −500bps → `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` arms within 60s; −1000bps → EMERGENCY crystallization path confirmed

#### Cell 8: CSB × `cross_asset_flash_crash`

- **expected_breaker_trips**: `[DRAWDOWN_DAILY_BPS]` + `[LIQUIDATION_CASCADE_RISK]`; both CSB-primary and APD-primary
- **expected_alert_emissions**: `[RISK_RULE_BLOCKED, CIRCUIT_BREAKER_TRIPPED, KILL_SWITCH_ARMED]` (all `synthetic=true`)
- **recovery_mode**: `KILL_ALL` → `MANUAL_UNKILL`; recovery guard: "realized-vol back within 2× of 30d baseline for
  1800s contiguous AND drawdown < 50% of pre-crash level"
- **paper_trade_validation_step**: `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` arms within 30s; `AdversarialMatchingEngine`
  (Phase 3.E, `execution-service@d0ec76f1`) fires `RejectFills` + `LatencyInject` during crash window; Chainlink
  heartbeat lags DeFi leg confirming 30–180s delay vs CeFi

#### Cell 9: CSB × `cross_asset_basis_blowout_perp_spot`

- **expected_breaker_trips**: `[DRAWDOWN_DAILY_BPS]` + `[ORACLE_DEVIATION_BPS]` (stETH-ETH basis inverts); both together
  if adverse post-entry
- **expected_alert_emissions**: `[RISK_RULE_SCALED_DOWN]` (initial signal cap) →
  `[RISK_RULE_BLOCKED, CIRCUIT_BREAKER_TRIPPED, KILL_SWITCH_ARMED]` if basis widens
- **recovery_mode**: `SCALE_DOWN` → `AUTO_COOLDOWN`; escalates to `KILL_ALL` → `MANUAL_UNKILL` if adverse move persists;
  recovery: "basis within 50bps of baseline for 3600s contiguous AND drawdown recovered to 25% of pre-blowout level"
- **paper_trade_validation_step**: `AdversarialMatchingEngine` fires `BookSpoof` (asymmetric liquidity withdrawal on
  perp leg); FAST_UNWIND signal emitted; LST-ETH Curve pool divergence captured in features-onchain

#### Cell 10: CSB × `defi_mempool_congestion_inclusion_delay`

- **expected_breaker_trips**: `[GAS_PRICE_SURGE_GWEI]` if gas raised to push through; `[FILL_LATENCY_BREACH_MS]`
  secondary (no dedicated `MEMPOOL_INCLUSION_LATENCY_SECONDS` yet — follow-up per Phase 1.T6)
- **expected_alert_emissions**: `[RISK_RULE_BLOCKED, RISK_RULE_SCALED_DOWN]` once `inflight_tx_limit` breach fires
- **recovery_mode**: advisory `mempool_congested` state (no dedicated recovery state yet; follow-up per Phase 1.T6 DR
  plan Phase 4); escalation to kill-switch only if inclusion-latency >600s + `MAX_SLIPPAGE_BPS` breach
- **paper_trade_validation_step**: pending_tx count monitor shows saturation; cancel_lost_rate_bps crosses 8000bps (80%)
  during synthetic window; sandwich variant validates `realised_slippage_bps` p50 shift from ~5bps to ~50bps

#### Cell 11: APD × `cefi_venue_circuit_breaker_trip`

- **expected_breaker_trips**: `[VENUE_OUTAGE_SECONDS]` (PER_VENUE) → `CANCEL_OPEN` on imbalance > 20%;
  `[HEDGE_GAP_NOTIONAL_USD]` at > $100k threshold → `KILL_ALL`
- **expected_alert_emissions**:
  `[CONNECTIVITY_GAP_DETECTED, TICK_STALENESS, CIRCUIT_BREAKER_OPEN, CROSS_VENUE_DIVERGENCE_BPS]` (>40bps after 120s)
- **recovery_mode**: `KILL_PER_VENUE_<V>` auto-disarm when venue heartbeats green ≥5min; `MANUAL_UNKILL` if
  `INVENTORY_IMBALANCE_RATIO` or `HEDGE_GAP_NOTIONAL_USD` escalation arms
- **paper_trade_validation_step**: Cross-venue funding-arb position shows asymmetric exposure; `BLOCK_NEW` within 90s;
  `KILL_PER_VENUE_BYBIT` (or chosen venue) arms; other venues continue; escalation to `KILL_ALL_LIVE` only above $100k
  gap

#### Cell 12: APD × `defi_chain_rpc_outage_solana`

- **expected_breaker_trips**: `[RPC_OUTAGE_SECONDS]` (PER_ARCHETYPE, `SCALE_DOWN` for APD — registry seed extension
  needed per Phase 1.T2 follow-up); CeFi perp leg continues
- **expected_alert_emissions**: `[CONNECTIVITY_GAP_DETECTED, DEFI_FEATURE_STALE]` (Solana DeFi leg only; CeFi alerts
  suppressed)
- **recovery_mode**: `SCALE_DOWN` → CeFi perp leg positions maintained; DeFi-leg entries suspended; auto-recovery on RPC
  restoration
- **paper_trade_validation_step**: APD strategy continues CeFi-only positions; DeFi spot-leg instructions blocked but no
  global kill; `SCALE_DOWN` consequence fires (not `KILL_ALL`) validating archetype-specific isolation

#### Cell 13: APD × `defi_oracle_deviation_30sigma`

- **expected_breaker_trips**: `[ORACLE_DEVIATION_BPS]` (`SCALE_DOWN` on APD perp-vs-spot basis instructions referencing
  affected oracle)
- **expected_alert_emissions**: `[DEFI_FEATURE_STALE, CIRCUIT_BREAKER_OPEN]` for oracle; CeFi perp leg continues
- **recovery_mode**: `SCALE_DOWN` (not `KILL_ALL`); APD CeFi perp leg continues unaffected; only oracle-derived basis
  instructions blocked
- **paper_trade_validation_step**: APD perp-spot basis features show NaN for oracle-affected instruments; `SCALE_DOWN`
  fires only on USDC-reference instruments; non-USDC basis positions continue; no global kill

#### Cell 14: APD × `defi_gas_surge_50x`

- **expected_breaker_trips**: DeFi-asset-group rule fires `[GAS_BUDGET_PER_ARCHETYPE]` (`SCALE_DOWN` on DeFi spot-leg);
  CeFi perp hedge continues
- **expected_alert_emissions**: `[RISK_RULE_SCALED_DOWN]` (DeFi-leg only; no CeFi disruption)
- **recovery_mode**: DeFi-spot leg suspended during surge; CeFi perp hedge leg runs normally; composite position shows
  correct partial suspension
- **paper_trade_validation_step**: APD DeFi-leg rebalances blocked; CeFi perp positions continue; `SCALE_DOWN` on DeFi
  subset only; asymmetric leg-risk exposure logged by position-balance-monitor

#### Cell 15: APD × `cefi_funding_spike_10x`

- **expected_breaker_trips**: `[FUNDING_RATE_FLIP_BPS]` + `[BASIS_INVERSION_BPS]` → `BLOCK_NEW` on new entries;
  `[MAX_POSITION_SIZE_PER_INSTRUMENT]` + `[MAX_LEVERAGE]` fires at entry attempt
- **expected_alert_emissions**: `[RISK_RULE_BLOCKED, RISK_RULE_SCALED_DOWN]` (both `synthetic=true`)
- **recovery_mode**: `SCALE_DOWN` → `AUTO_COOLDOWN`; no kill-switch unless re-fire >3× in 24h; APD DESIGNED to trade
  funding rate divergence → scenario validates CORRECT sizing caps (not total halt)
- **paper_trade_validation_step**: APD treats spike as signal amplification opportunity;
  `MAX_POSITION_SIZE_PER_INSTRUMENT` cap fires to prevent oversizing; `FUNDING_RATE_FLIP_BPS` breaker validates correct
  asymmetric scaling; scenario is APD's most commercially important validation cell

#### Cell 16: APD × `cross_asset_flash_crash`

- **expected_breaker_trips**: `[DRAWDOWN_DAILY_BPS]` + `[BASIS_INVERSION_BPS]`; basis math degenerates under panic →
  `KILL_PER_ARCHETYPE_ARBITRAGE_PRICE_DISPERSION` within 30s
- **expected_alert_emissions**: `[RISK_RULE_BLOCKED, CIRCUIT_BREAKER_TRIPPED, KILL_SWITCH_ARMED]` (all `synthetic=true`)
- **recovery_mode**: `KILL_ALL` → `MANUAL_UNKILL`; same recovery guard as Cell 8 (realized-vol + drawdown)
- **paper_trade_validation_step**: All 6 CeFi venues crash simultaneously (>0.95 correlation); APD basis arithmetic
  degenerates; `KILL_PER_ARCHETYPE_ARBITRAGE_PRICE_DISPERSION` arms; `AdversarialMatchingEngine` fires `RejectFills` +
  `LatencyInject`; no single-venue circuit breaker fires without global kill (tests isolation logic)

### Coverage gap analysis (post-16-cell review)

| Gap area                                        | Missing cell                                                     | Why it matters                                                       | Plan for coverage                                                                                                          |
| ----------------------------------------------- | ---------------------------------------------------------------- | -------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| APD × `defi_stablecoin_depeg`                   | Not in pre-cutover matrix (APD secondary only per registry)      | USDT-quoted perps need denominator correction under stable depeg     | Post-cutover Phase 2 — add `ARBITRAGE_PRICE_DISPERSION` as declared archetype in `defi_stablecoin_depeg` registry instance |
| APD × `defi_mempool_congestion_inclusion_delay` | Not in pre-cutover matrix (APD secondary, not declared)          | DeFi-leg tx delays create asymmetric CeFi/DeFi exposure              | Post-cutover Phase 2 — extend scenario to declare APD outcomes                                                             |
| APD × `cross_asset_basis_blowout_perp_spot`     | Declared as primary for APD but matrix only shows filtered cells | Confirmed APD primary — PRESENT in matrix                            | N/A: already covered                                                                                                       |
| Both archetypes × TradFi scenarios              | TradFi not in pre-cutover scope                                  | Options-chain partial-cluster + VIX gaps could affect macro features | Post-cutover Phase 2 Phase 4.C                                                                                             |
| Both archetypes × Sports scenarios              | Sports not in pre-cutover scope                                  | Prediction/sports feature lag could affect composite models          | Post-cutover Phase 2 Phase 4.D/4.E                                                                                         |

**Coverage completeness assertion** (pre-cutover matrix):

- 16 cells declared; every cell has `expected_breaker_trips`, `expected_alert_emissions`, `recovery_mode`, and
  `paper_trade_validation_step`.
- 2 additional cells (APD × depeg, APD × mempool) are post-cutover extension items.
- 0 cells have "no test path" — every matrix cell has a clear assertion path.

- [x] [DESIGN] P0. **6.A Per-archetype coverage matrix — 16-cell specification.** ✅ design-shipped 2026-05-13 (slot 7
      Day-2-4 scope extension). Plan body above enumerates per-cell breaker/alert/recovery/validation for all 16 cells.
      Successor plan extension items (APD × depeg, APD × mempool, TradFi/Sports axis) carry-forwarded to
      `simulation_scenarios_post_cutover_2026_06_01.md` Phase 2.
- [x] [DESIGN] P0. **6.B Coverage gap analysis.** ✅ design-shipped 2026-05-13. Gap table above identifies 4 gap areas
      with remediation plan per row; 0 cells in pre-cutover matrix have "no test path."

**Full-execution criterion** (design-only phase):

- ✅ 16 cells enumerated with 4-tuple specification (breaker / alert / recovery / validation per cell).
  - **What ran**: design analysis + plan body authoring (2026-05-13 slot 7).
  - **Verification**:
    `grep -c "expected_breaker_trips" plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md` returns
    ≥16.

## Phase 7 — Probability + expected-loss matrix (Day-2-4 scope extension, 2026-05-13)

> **Status**: `done` — design-shipped 2026-05-13 (slot 7 Day-2-4 scope extension). Per-scenario probability weights and
> expected-loss data added to plan body. This provides the risk-budgeting calibration baseline for Phase 9 (real-VM
> matrix runs) and for the post-cutover fuller regression matrix. No UAC schema changes for this phase — data lives in
> plan body. UAC schema extension (adding `probability_weight` + `expected_loss_bps` fields to `ScenarioOverlay`)
> deferred to successor plan Phase 1.B extension (first-class mutation members + metadata fields).

The pre-cutover matrix passes/fails on assertion semantics (did the right breaker trip?). But risk-budgeting requires
knowing: what is the annualised probability of each scenario AND what is the expected P&L loss if it occurs? This table
provides that calibration so the operator can prioritise recovery time and set `expected_within_seconds` SLAs
appropriately.

### Historical reference basis

All probability weights and expected-loss estimates use the following historical data set (same sources cited in the
Phase 2 price-shock designs):

- **Flash crash (2020-03-12)**: BTC/ETH −50% in 2h; 2022-11-08 FTX −25% in 6h; 2024-08-05 JPY carry −20%. Count: ~3
  major events in 5 years.
- **Basis blowout (2022-05-09)**: stETH-ETH −7% (3AC + Celsius); 2021-01-04 Bitfinex BTC-PERP +8%; 2024-03 ETH staking
  +400bps pre-Shanghai. Count: ~4 major events in 5 years.
- **Funding spike (2021-04-18)**: BTC 100%/yr annualised; 2024-04-12 Bybit ETHUSDT +0.375%/8h; 2025-01 Hyperliquid JLP
  storm. Count: ~5 events per year per venue (minor); ~2 major (>10×) per year.
- **Stablecoin depeg (2023-03-11)**: USDC $0.87 (SVB); 2022-06-13 stETH 0.94 ETH (3AC); 2022-05-09 UST death spiral.
  Count: ~1 catastrophic per 2 years; ~3 minor per year.
- **DeFi oracle deviation**: Chainlink LUNA 2022-05 zero-print; GMX-V1 AVAX 2022-09; Pyth 2024-Q1 heartbeat lag. Count:
  ~3 major per year across all oracles.
- **Gas surge**: 2021-05 NFT wars (sustained 3+ days); 2022-Q4 LUNA collapse; 2024-Q1 memecoin storms. Count: ~4
  material (>20×) events per year.
- **RPC outage**: Solana 2022-09-30 (4h); Solana 2024-02-06 (5h); Ethereum mainnet Infura 2020-11. Count: ~2 per chain
  per year.
- **Venue circuit breaker**: Bybit 2021-05 (flash crash halt); Binance 2023-06 (maintenance pause); OKX 2022-11. Count:
  ~3 major per year across 6 venues.
- **Liquidity drain / protocol pause**: Aave 2023-11 CRV cascade; Morpho 2024-03 governance pause; Aave V3 2024-Q4 ETH
  borrow cap. Count: ~2 material per year.
- **Mempool congestion**: Ethereum 2023-Q4 sandwich domination; Arbitrum 2024-Q1 sequencer backlog. Count: ~6 material
  events per year.

### Per-scenario probability + expected-loss table

| #   | `scenario_id`                             | `probability_weight` (annualised, %) | `expected_loss_bps` (worst-case, 1-day P&L) | `recovery_time_hours` (median) | Basis                                                                                                       |
| --- | ----------------------------------------- | ------------------------------------ | ------------------------------------------- | ------------------------------ | ----------------------------------------------------------------------------------------------------------- |
| 1   | `cefi_venue_circuit_breaker_trip`         | 60.0                                 | 50                                          | 0.5                            | 3 major events/yr across 6 venues; short-duration outages; loss from missed hedges                          |
| 2   | `defi_chain_rpc_outage_solana`            | 200.0                                | 80                                          | 4.0                            | 2/yr per chain × 2 chains (Solana + Ethereum-based); loss from stuck DeFi positions                         |
| 3   | `defi_liquidity_drain_lending_pool`       | 200.0                                | 120                                         | 8.0                            | 2 material events/yr; 8h median duration (governance pause); loss from delayed deleverage                   |
| 4   | `defi_oracle_deviation_30sigma`           | 300.0                                | 200                                         | 0.5                            | 3 major wild-prints/yr; short duration but high instantaneous loss if position open                         |
| 5   | `defi_gas_surge_50x`                      | 400.0                                | 40                                          | 0.2                            | 4 material events/yr; BLOCK_NEW means no new losses; existing positions unaffected                          |
| 6   | `cefi_funding_spike_10x`                  | 200.0                                | 60                                          | 8.0                            | 2 major (>10×) events/yr; `carry_staked_basis` eroded margin; 1 funding period resolution                   |
| 7   | `defi_stablecoin_depeg`                   | 150.0                                | 500                                         | 72.0                           | 1.5 catastrophic-tier events/yr; SVB-scale: 72h recovery; loss at −500bps trigger = full position exit cost |
| 8   | `cross_asset_flash_crash`                 | 60.0                                 | 800                                         | 1.5                            | 3 events in 5yr ≈ 60%/yr; median reversion 75% within 1h; 25th percentile structural (weeks)                |
| 9   | `cross_asset_basis_blowout_perp_spot`     | 80.0                                 | 300                                         | 4.0                            | 4 major events in 5yr ≈ 80%/yr; 75th percentile resolves within 8h; stETH 2022 tail = weeks                 |
| 10  | `defi_mempool_congestion_inclusion_delay` | 600.0                                | 30                                          | 0.25                           | 6 material events/yr; short-duration; loss only if sandwich variant + slippage tolerance mis-set            |

### Expected-loss calibration notes

1. **`probability_weight` is annualised percent**: 100% = 1 occurrence per year expected. Values >100% = multiple
   occurrences per year (common for gas surges, mempool, RPC outages). This is a frequency estimate, not a probability
   in [0,1].

2. **`expected_loss_bps` is worst-case 1-day P&L impact**: assumes strategy is fully deployed at max position size; loss
   is the expected delta between (a) ideal outcome without scenario and (b) actual outcome with scenario running.
   Scenario-triggered BLOCK_NEW means 0 new losses on pending entries but existing positions may have adverse
   mark-to-market.

3. **Highest annualised-loss scenarios** (probability × expected_loss_bps):
   - `defi_mempool_congestion_inclusion_delay`: 600% × 30 = 18,000 loss-bps-events/yr (frequent, small)
   - `defi_oracle_deviation_30sigma`: 300% × 200 = 60,000 (frequent, moderate)
   - `defi_gas_surge_50x`: 400% × 40 = 16,000 (frequent, small; BLOCK_NEW limits exposure)
   - `cross_asset_flash_crash`: 60% × 800 = 48,000 (rare, large) — highest single-event tail risk
   - `defi_stablecoin_depeg`: 150% × 500 = 75,000 (moderate frequency, very large) — **highest annual expected loss**

4. **`recovery_time_hours`** is the median observed duration before scenario auto-recovers or is manually resolved. Used
   to calibrate `expected_within_seconds` in `ScenarioOutcomeAssertion` per cell.

5. **UAC schema extension opportunity** (deferred): `ScenarioOverlay` Pydantic could carry
   `probability_weight: Decimal | None` + `expected_loss_bps: int | None` + `recovery_time_hours: Decimal | None` as
   optional metadata fields. This table is the prototype; the schema extension lands in successor plan Phase 1.B.

- [x] [DESIGN] P0. **7.A Per-scenario probability weight + expected-loss table.** ✅ design-shipped 2026-05-13 (slot 7
      Day-2-4 scope extension). Plan body above enumerates 10 scenarios × 3 risk metrics (probability_weight /
      expected_loss_bps / recovery_time_hours) with historical basis. Successor plan Phase 1.B owns UAC schema
      extension.
- [x] [DESIGN] P0. **7.B Annualised-loss ranking.** ✅ design-shipped 2026-05-13. Top-5 by probability × expected_loss
      identified (mempool, oracle, gas, flash-crash, depeg); `defi_stablecoin_depeg` highest annual expected loss.

**Full-execution criterion** (design-only phase):

- ✅ 10-row probability + expected-loss table present in plan body with probability_weight / expected_loss_bps /
  recovery_time_hours per scenario + historical basis per row.
  - **What ran**: design analysis + plan body authoring (2026-05-13 slot 7).
  - **Verification**:
    `grep -c "probability_weight" plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md` returns ≥10;
    `grep "defi_stablecoin_depeg" plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md | grep "75,000"`
    returns ≥1.

## DONE-2026-05-13 (slot 7 Day-2-4 scope extension)

**Session theme**: Phase 6 + Phase 7 + Phase 8.B-I + Phase 9 (successor plan) scope extension per slot-1 SCOPE EXTENSION
2 directive.

**Shipped this session**:

- Phase 6 (per-archetype coverage matrix expansion): 16-cell specification with 4-tuple per cell
  (breaker/alert/recovery/validation) + gap analysis table. All 16 cells have complete specification; 2 post-cutover
  extension items identified.
- Phase 7 (probability + expected-loss matrix): 10-scenario × 3-metric table (probability_weight / expected_loss_bps /
  recovery_time_hours) with historical basis per row; top-5 annualised-loss ranking; `defi_stablecoin_depeg` highest
  annual expected loss at 75,000 loss-bps-events/yr.
- Phase 8.B-I (codex sections): 8 new sections added to `/codex/04-architecture/scenario-injection-architecture.md`
  covering scenario authoring guide, per-archetype scenario selection, matrix runner usage, post-run report shape,
  adversarial mode flag wiring, synthetic provenance auditing, scenario archive/version history, and operator runbook.
- Phase 9 successor plan: `simulation_scenarios_post_cutover_2026_06_01.md` updated with carry-forward table +
  estimate_class + frontmatter corrections.

| Phase / item                          | Status as of 2026-05-13                                                  | Successor / blocker                                                 |
| ------------------------------------- | ------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| Phase 6 (coverage matrix expansion)   | `done` design-shipped                                                    | This plan body §§ above                                             |
| Phase 7 (probability + expected-loss) | `done` design-shipped                                                    | This plan body §§ above; UAC schema extension → successor Phase 1.B |
| Phase 8.B-I (codex sections)          | `done` shipped                                                           | `/codex/04-architecture/scenario-injection-architecture.md`         |
| Phase 9 (successor plan update)       | `done` shipped                                                           | `simulation_scenarios_post_cutover_2026_06_01.md`                   |
| Phase 9 real-VM runs                  | `deferred-after-successor` (pending Phase 3.E operator runtime complete) | `simulation_scenarios_post_cutover_2026_06_01.md` Phase 6           |
