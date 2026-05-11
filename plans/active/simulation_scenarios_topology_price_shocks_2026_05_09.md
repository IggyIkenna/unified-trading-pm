---
title: Simulation scenarios — synthetic topology gaps + price shocks for backtest robustness
type: plan
status: active
created: 2026-05-09
deadline: 2026-05-23
horizon: 14-day pre-cutover sprint
companion_to:
  master_to_live_defi_2026_05_23.md (Group F items 17 paper-trade smoke, 18 2-yr batch backtest, 20 circuit-breakers +
  kill-switches + alerting + auto-recovery, 21 batch-vs-live reconciliation, 22 P&L attribution)
locked_by: live-defi-rollout
locked_since: 2026-05-09
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/epics/live_defi_rollout_2026_05_23.epic.md
  - plans/epics/cross_cutting_2026_05_23.epic.md
  - plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md
  - plans/active/alerting_service_live_rules_2026_05_07.md
  - plans/active/writegate_honest_coverage_endtoend_2026_05_06.md
  - plans/questions/risk_simulations_limits_alerting_2026_05_08.md
  - plans/questions/disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md
  - plans/questions/mock_data_pipeline_benchmarking_2026_05_08.md
  - plans/questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md
related_codex:
  - codex/04-architecture/kill-switch-circuit-breaker.md
  - codex/04-architecture/autonomous-recovery-matrix.md
  - codex/04-architecture/backtest-groups.md
  - codex/04-architecture/tenderly-execution-provider.md
  - codex/02-data/honest-absence-downstream-handling.md
  - codex/02-data/availability-manifest-and-data-status.md
  - codex/05-infrastructure/live-pipeline-architecture.md
  - codex/05-infrastructure/replay-subsystem.md
  - codex/06-coding-standards/integration-testing-layers.md
  - codex/09-strategy/strategy-summary.md
---

# Simulation scenarios — synthetic topology gaps + price shocks for backtest robustness

> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing 2026-05-10** (BE-AWARE)
>
> [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md) anti-sequencing audit flags this plan as a Phase 2.2 single-walk discipline risk: if the simulation harness writes synthetic-data parquets into the same buckets as real captures, it could conflict with the GCS bundled migration's "one walk only" rule. **Required mitigation (per code_freeze anti-sequencing audit row)**: confirm simulation outputs go to dedicated `*-sim-*` buckets per `bucket_name_ssot_canonicalisation_2026_05_10.md`'s yaml SSOT (operator decision (b+) 2026-05-11 — env-tier convention extends to ALL bucket kinds, so `*-sim-*` buckets also need env-tier in their names). If sim buckets are not yet isolated, **defer simulation runs to Phase 3** (post-Phase-2-freeze 2026-05-19). Banner-removal owned by this plan when sim-bucket isolation is verified.

> **🟡 SCOPE-COMPRESSED 2026-05-10 (T-13 to cutover)** — operator review of Audit C Finding C-5 (56 todos / 0 done at
> T-13, well-designed but unstarted) ratified Citadel-grade compression: ship the **MINIMUM VIABLE adversarial gate**
> that covers the 2 LIVE archetypes (`carry_staked_basis` + `leveraged_funding_arb`) under their 6 highest-likelihood
> failure modes, run end-to-end through real execution-service matching-engine adversarial mode, with per-scenario
> expected-outcome assertion. **Defer the broader regression matrix + per-asset-group scenario library + UI integration
> + 7-layer wire-in to the post-cutover successor plan
> [`simulation_scenarios_post_cutover_2026_06_01.md`](simulation_scenarios_post_cutover_2026_06_01.md)** (NEW, sibling
> plan, ~6-9 weeks scope including the deferred Phases 4-9 of this plan body).
>
> **Pre-cutover compressed scope (~3-5 AI-days, ~15 todos)**:
>
> 1. UAC `ScenarioOverlay` Pydantic dataclass + `ScenarioOutcomeAssertion` closed-enum — minimal subset (5 mutation
>    types + 3 outcome categories). Phase 1 todos 1.A-1.C scoped down; 1.D-1.F deferred.
> 2. UTL `ScenarioOverlayApplier` + `ScenarioOutcomeChecker` — single-layer (execution-service matching-engine adversarial
>    mode) NOT 7-layer. Phase 2 todos 2.A-2.B + 2.D scoped down; 2.C / 2.E / 2.F deferred.
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
> - Full per-asset_group scenario library (Phase 4 ≥34 scenarios — only 6 ship pre-cutover).
> - 7-layer wire-in (Phases 3.A / 3.B / 3.C / 3.D / 3.G — MTDS / MDPS / features / strategy / manifest taps).
> - Backtest harness CLI integration (Phase 6).
> - Codex sweep + DART manual-trade rehearsal (Phases 7-8).
> - Full per-asset_group regression matrix on real VMs across every archetype (Phase 9).
>
> **Phase status under compression** (for reviewers walking this plan):
>
> | Phase | Pre-cutover scope | Status |
> | ----- | ------------------ | ------ |
> | 0 — Pre-audit | Sub-agent fan-out per todos 0.A-0.C | `todo` (3 AI-hours) |
> | 1 — UAC contracts | 1.A + 1.B + 1.C only (scoped to 5 mutations + 3 outcomes) | `todo` (1 AI-day) |
> | 2 — UTL primitives | 2.A + 2.B + 2.D only (single-layer applier) | `todo` (1 AI-day) |
> | 3 — Wire-ins | 3.E + 3.F only (execution-engine adversarial + risk/alerting consumers) | `todo` (1 AI-day) |
> | 4 — Scenario library | 6 scenarios from above bullet (~1 each) | `todo` (1 AI-day) |
> | 5 — Matrix | 12-cell scope (not full per-archetype matrix) | `todo` (0.5 AI-day) |
> | 6 / 7 / 8 / 9 | DEFERRED post-cutover | `deferred-after-simulation_scenarios_post_cutover_2026_06_01` |
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
- A risk-limit / risk-simulation system (that's `risk_simulations_limits_alerting_2026_05_08.md`; this plan **consumes**
  that system's circuit-breaker rules as expected-outcome assertions).
- A DR / chaos drill harness (that's `disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md`; this plan
  **provides** the synthetic injection primitives that DR drills will reuse).
- A separate "backtest engine" — every scenario runs through the unified pipeline (MTDS → MDPS → features-\* →
  strategy-service ↔ position-balance + risk + execution-service-in-matching-engine-mode), with one well-bounded
  overlay layer.

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

- Real-state risk-limit + circuit-breaker rule definition — owned by `risk_simulations_limits_alerting_2026_05_08`. This
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

- `codex/04-architecture/scenario-injection-architecture.md` — overlay layer model, injection points, prod-codepath
  reuse pattern, `synthetic=true` provenance.
- `codex/04-architecture/scenario-outcome-assertions.md` — closed-enum outcome taxonomy, per-archetype expected-outcome
  matrix shape, fail semantics.
- `codex/02-data/scenario-overlay-semantics.md` — overlay parquet schema, per-row provenance, `available_at` discipline
  under overlay, manifest-side scenario_id column.

UPDATE:

- `codex/04-architecture/kill-switch-circuit-breaker.md` — scenario-driven trips section.
- `codex/04-architecture/autonomous-recovery-matrix.md` — scenario-driven recovery validation section.
- `codex/04-architecture/backtest-groups.md` — scenario-overlay mode added to backtest taxonomy.
- `codex/05-infrastructure/live-pipeline-architecture.md` — scenario tap points within the live + batch unified
  pipeline.
- `codex/05-infrastructure/replay-subsystem.md` — scenario-overlay-on-replay extension.
- `codex/02-data/honest-absence-downstream-handling.md` — scenario-driven gap injection per consumer-class table.

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
- **`risk_simulations_limits_alerting_2026_05_08.md`** (question doc) — circuit-breaker rule taxonomy is the upstream
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

- [ ] [AGENT] P0. **0.A Inventory existing scenario / mock infra.** Sub-agent walks:
      `execution-service/matching_engine/{engine,trade_matcher,amm,sports_matching,hooks}.py` (existing slippage +
      latency hooks), `execution-service/tests/integration/conftest.py` (Tenderly fixtures),
      `market-tick-data-service/tests/market_interface/fixtures/mock_ws_server.py` (MockWebSocketFeed),
      `unified-api-contracts/canonical/crosscutting/service_emission_policy.py` (PUBLISHED_DEGRADED + STALE_DATA), UTL
      `streaming` + `batch_live_reconciler` + `honest_coverage_ratchet` (Tab 2 2026-05-08), MDPS feature-layer
      NaN-handling primitives. Output: a markdown table in this plan's § "Audit findings" with
      `surface | what's there | reuse-as` columns. **Don't write code yet — only surface what to reuse.**
- [ ] [AGENT] P0. **0.B Cross-plan coordination banners.** Add
      `> **🟡 IN-FLIGHT REFACTOR — synthetic scenario injection landing across MTDS / MDPS / features / strategy / execution / alerting / position-balance / risk via UAC `ScenarioOverlay`+ UTL`scenario/`; downstream consumers will gain a `scenario_id`provenance column on parquet writes + a`synthetic=true`event metadata field. RE-VERIFY any reader / dashboard code that filters or groups parquet output. See`simulation_scenarios_topology_price_shocks_2026_05_09.md`.**`
      to: `master_to_live_defi_2026_05_23.md`, `live_pipeline_mtds_mdps_features_2026_05_08.md`,
      `alerting_service_live_rules_2026_05_07.md`, `writegate_honest_coverage_endtoend_2026_05_06.md`. Banner removed by
      this plan's owner when Phase 9 ships.
- [ ] [SCRIPT] P0. **0.C Workspace-grep callsite enumeration.** For every overlay tap point — `_fetch_*` per MTDS
      adapter, `_compute_*` per features-\* calculator, `emit_signal` in strategy-service, `submit_order` +
      `simulate_fill` in execution-service, `record_captured` + `record_empty` + `record_failed` +
      `record_expected_unattempted` in UTL ManifestWriter — produce a CSV
      `repo,file,line,callsite_kind,target_overlay_layer` so Phase 3 sub-agents have a complete edit list. Tool:
      `rg -n "<pattern>" --type py --glob '!.venv*' --glob '!tests'` per kind. Output: append to § "Audit findings" as a
      fenced table.

**Full-execution criterion** (per HARD RULE):

- ✅ § "Audit findings" populated with infra inventory + workspace-grep CSV (≥40 callsites enumerated across the 7 tap
  kinds).
  - **What ran**: 3 sub-agent fan-outs + serial commit by parent.
  - **Verification**: `wc -l` on the CSV ≥ 40; `grep -c "tap_kind=" plan` matches expected per-kind counts.
- ✅ Banners on 4 cross-plan files; `grep -l "🟡 IN-FLIGHT REFACTOR — synthetic scenario injection"` returns 4 paths.

## Phase 1 — UAC scenario contracts (Days 2-3, ~2 AI-days)

- [ ] [AGENT] P0. **1.A Closed-enum scenario taxonomy.**
      `unified_api_contracts/canonical/crosscutting/scenario_overlay.py` ships: `ScenarioCategory` (TOPOLOGY*GAP /
      STALENESS / PRICE_SHOCK / VENUE_OUTAGE / DATA_CORRUPTION / CROSS_ASSET / OPERATIONAL), `ScenarioId` (NewType[str]
      with regex `^[a-z]a-z0-9*]+$`), `ScenarioOverlayLayer` (RAW_TICK / FEATURE / SIGNAL / ORDER / EVENT / MANIFEST).
      Frozen Pydantic.
- [ ] [AGENT] P0. **1.B `ScenarioOverlay` Pydantic dataclass.** Fields: `scenario_id`, `category`, `layer`,
      `asset_groups: frozenset[MarketAssetGroup]`, `applies_to: ScenarioApplicabilityFilter` (per-venue / per-data_type
      / per-instrument / per-day / per-archetype), `mutation_spec: ScenarioMutationSpec` (closed union: `DropRows` |
      `StaleHold` | `PriceShift` | `BookSpoof` | `LatencyInject` | `RejectFills` | `OracleDeviate` | `GasSurge` |
      `ManifestPhantom` | `EventDrop` | `EventDuplicate`), `expected_outcomes: list[ScenarioOutcomeAssertion]`. Every
      field typed; no `Any`.
- [ ] [AGENT] P0. **1.C `ScenarioOutcomeAssertion` closed-enum.** Categories: `STRATEGY_HALTED` (signal generator stops
      emitting), `STRATEGY_SCALED_DOWN` (size cut by ≥X%), `RISK_BREAKER_TRIPPED` (named breaker fires),
      `ORDER_REJECTED` (execution refuses), `ORDER_CANCELLED_ON_STALE` (auto-cancel fires), `KILL_SWITCH_ARMED` (named
      kill switch arms), `ALERT_FIRED` (named alert rule fires with `synthetic=true`), `PNL_BOUNDED_BY` (per-archetype
      P&L bound), `RECONCILIATION_FLAGGED` (batch-vs-live recon raises). Each carries a typed
      `expected_within: timedelta` SLA.
- [ ] [AGENT] P0. **1.D Per-asset_group scenario seed library.**
      `unified_api_contracts/registry/scenarios/{cefi,defi,tradfi,sports,prediction,cross_asset}.py` — each module
      exposes a `frozenset[ScenarioOverlay]` constant with seed scenarios from § Phase 4 (full library lands in Phase 4;
      seed shape lands here). Registry: `SCENARIO_REGISTRY: dict[ScenarioId, ScenarioOverlay]` indexed at module load.
- [ ] [AGENT] P0. **1.E `ScenarioReport` Pydantic dataclass.** Fields: `scenario_id`, `archetype: ArchetypeId`,
      `run_id`, `started_at`, `finished_at`, `outcome_results: list[ScenarioOutcomeResult]` (assertion + observed +
      pass/fail), `synthetic: bool = True`, `parquet_artifacts: list[GcsPath]` (per-stage parquet snapshots),
      `event_correlation_id`. Used by Phase 7 UI + Phase 9 evidence.
- [ ] [AGENT] P0. **1.F UAC tests.** ≥30 unit tests in
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

- [ ] [AGENT] P0. **2.A `unified_trading_library/scenario/applier.py`.** `ScenarioOverlayApplier` class — one applier
      per `ScenarioOverlayLayer`. Pure-functional
      `apply(input_frame: pl.DataFrame, overlay: ScenarioOverlay, context: ScenarioContext) -> pl.DataFrame`. Each
      mutation_spec has its own applier method. NEVER mutates input; returns a new frame with
      `_synthetic_provenance: list[ScenarioId]` column appended. Tested against polars + pandas frames.
- [ ] [AGENT] P0. **2.B `unified_trading_library/scenario/checker.py`.** `ScenarioOutcomeChecker` — registers callbacks
      against the event stream + service state surfaces (strategy-service emit, risk-and-exposure breaker fire,
      execution-service order state, alerting-service rule fire, position-balance scaling). Each
      `ScenarioOutcomeAssertion` checks `expected_within` SLA against observed.
      `check(scenario_run_id, assertion) -> ScenarioOutcomeResult`. Uses the existing event stream contract, no new
      infra.
- [ ] [AGENT] P0. **2.C `unified_trading_library/scenario/report.py`.** `ScenarioReportEmitter` — writes
      `ScenarioReport` to `gs://{pid}-events/scenarios/{archetype}/{YYYY-MM-DD}/{scenario_id}/{run_id}.json` (event
      payload) + `gs://{pid}-scenario-reports/{archetype}/{YYYY-MM-DD}/{scenario_id}/{run_id}/report.parquet`
      (queryable). Reuses UTL emission helpers — no new bucket-naming logic; uses Tab 4's `bucket_naming.py` SSOT
      (UTL@780a9575).
- [ ] [AGENT] P0. **2.D `unified_trading_library/scenario/runner.py`.** `ScenarioRunner` — orchestrates a single
      `(scenario_id, archetype, time_window)` run end-to-end: invokes the unified backtest pipeline (the same one Group
      F item 18 uses) with `--scenario-overlay` flag, observes outputs via `ScenarioOutcomeChecker`, emits
      `ScenarioReport` via `ScenarioReportEmitter`. **No parallel backtest engine — this only configures and observes
      the existing one.**
- [ ] [AGENT] P0. **2.E LookaheadBiasError compatibility.** `ScenarioOverlay` mutations that shift `available_at`
      (StaleHold, EventDrop) must NOT trigger LookaheadBiasError downstream. Mechanism: applier stamps
      `_synthetic_available_at_shift: bool` column; UTL `lookahead_bias_check` accepts a `scenario_overlay_active: bool`
      kwarg that downgrades the error to a structured warning emitted to the report. **Strict mode stays on for
      non-overlay paths** — only the overlay-active path skips.
- [ ] [AGENT] P0. **2.F UTL tests.** ≥40 unit tests covering: per-mutation applier correctness,
      per-outcome-assertion-kind checker behavior on a mocked event stream, report-emitter parquet round-trip, runner
      end-to-end with a stub pipeline, lookahead-bias-check behaviour under overlay vs not.

**Full-execution criterion**:

- ✅ UTL PR pushed to `live-defi-rollout` with QG green.
  - **What ran**: UTL@<sha> + QG locally + remote CI watcher confirms green.
  - **Verification**: `cd unified-trading-library && bash scripts/quality-gates.sh` exits 0;
    `python -c "from unified_trading_library.scenario import ScenarioRunner; ScenarioRunner.__init_subclass__"`
    resolves; ≥40 tests in `tests/scenario/` collected.

## Phase 3 — Per-layer wire-ins (Days 5-7, ~3 AI-days, 7 parallel sub-agents)

Each sub-task is a separate sub-agent assignment. Same Bash-bundling discipline per `Commit + Push + Flip` HARD RULE.

- [ ] [AGENT] P0. **3.A MTDS raw-tick overlay.** `market-tick-data-service` adapters' fetch-result post-processing:
      after `record_captured` decision, if `ScenarioContext.has_overlay(layer=RAW_TICK)`, route through
      `ScenarioOverlayApplier`. Wire at `market_tick_data_service/adapters/base_adapter.py` `_post_fetch` hook — single
      edit point per the audit grep. Per-VM scenario_id passed via `VM_NAME` decoration + `ScenarioContext.from_env()`.
- [ ] [AGENT] P0. **3.B MDPS feature-layer overlay.** `mdps/engine/orchestrator.py` after honest-absence guard, before
      parquet write — invoke FEATURE-layer applier. Re-uses existing 4-category guard rails (no new banned-pattern
      surface). LookaheadBiasError downgrade per 2.E.
- [ ] [AGENT] P0. **3.C features-\* overlay tap.** `features-service/feature_calculator/<calculator>.py`
      per-feature-group tap at `_compute_<group>` exit, before `record_captured`. Per the consolidated repo (post Harsh
      Tab 2 features-consolidation 2026-05-08).
- [ ] [AGENT] P0. **3.D strategy-service signal tap + outcome hook.**
      `strategy-service/strategy_service/signal_generator.py` — SIGNAL-layer applier between feature read + signal
      emission; outcome-checker-callback registered at signal-emit boundary. Per-archetype hook list comes from UAC
      scenario registry.
- [ ] [AGENT] P0. **3.E execution-service matching-engine adversarial mode.**
      `execution-service/execution_service/matching_engine/{engine,trade_matcher}.py` — extend the existing slippage /
      latency / partial-fill hooks (per audit 0.A inventory) with `ScenarioOverlay`-driven mutations: `LatencyInject`,
      `RejectFills`, `BookSpoof`. **Do not replace the existing model** — extend via the existing hook interface. Sports
      adapter (`sports_matching.py`) gets fixture-cancellation / kickoff-delay mutations.
- [ ] [AGENT] P0. **3.F position-balance + risk + alerting consumers.** `position-balance-monitor-service`: subscribe to
      `synthetic=true` scenario events; emit per-scenario state snapshots. `risk-and-exposure-service`: outcome-checker
      hook fires on every breaker trip and emits `ScenarioOutcomeResult`. `alerting-service`: rule-eval respects
      `synthetic=true` filter — alert fires + report records, but on-call paging suppressed (synthetic events go to
      dashboard only).
- [ ] [AGENT] P0. **3.G Manifest-layer scenario_id column.** `unified_trading_library/manifest/writer.py`
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

- [ ] [AGENT] P0. **4.A CeFi (≥8 scenarios).** `cefi_tick_gap_15min`, `cefi_funding_spike_10x`,
      `cefi_liquidation_cascade`, `cefi_book_top_stale_120s`, `cefi_venue_outage_single` (Bybit-only),
      `cefi_wide_spread_50bps`, `cefi_halt_then_reopen_gap_5pct`, `cefi_funding_rate_negative_extreme`. Each declares
      per-archetype expected outcomes (e.g. `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`) halts on
      `cefi_funding_spike_10x`).
- [ ] [AGENT] P0. **4.B DeFi (≥8 scenarios).** `defi_oracle_deviation_30sigma`, `defi_gas_surge_50x`,
      `defi_rpc_outage_arbitrum`, `defi_reorg_solana_3block`, `defi_mev_sandwich_2pct`, `defi_slippage_blowout_uniswap`,
      `defi_pyth_feed_lag_solana_5min`, `defi_aave_utilization_99pct`. Per-archetype outcomes (e.g. `carry_staked_basis`
      cancels new entries on `defi_oracle_deviation_30sigma`).
- [ ] [AGENT] P0. **4.C TradFi (≥6 scenarios).** `tradfi_options_chain_partial_4_of_11_clusters_missing`,
      `tradfi_es_halt_circuit_breaker_l2`, `tradfi_overnight_gap_3pct`, `tradfi_databento_429_storm`,
      `tradfi_vix_15m_yahoo_window_edge`, `tradfi_etf_late_close_fill`. Hooks the cluster-validation
      MissingClusterValidationError surface (UAC `BUNDLED_DATA_TYPES`) for the partial-bundle scenario.
- [ ] [AGENT] P0. **4.D Sports seed (4 scenarios).** `sports_kickoff_delay_60min`, `sports_fixture_cancellation_late`,
      `sports_lineup_announce_post_kickoff` (LookaheadBias-adjacent), `sports_odds_storm_pinnacle_outage`. Full coverage
      post-cutover.
- [ ] [AGENT] P0. **4.E Prediction seed (4 scenarios).** `prediction_market_resolve_premature_polymarket`,
      `prediction_canonical_question_lifecycle_violation`, `prediction_clob_book_invert`,
      `prediction_kalshi_resolution_disputed`. Full coverage post-cutover.
- [ ] [AGENT] P0. **4.F Cross-asset (4 scenarios).** `cross_asset_correlation_break_btc_eth`,
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

- [ ] [AGENT] P0. **5.A Matrix definition.** `unified-api-contracts/registry/scenario_archetype_matrix.py` declares
      `MATRIX: dict[ArchetypeId, frozenset[ScenarioId]]`. `carry_staked_basis` × every DeFi + applicable cross_asset
      scenario; `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`) × every CeFi + DeFi + applicable cross_asset
      scenario. Out-of-asset_group scenarios excluded by construction.
- [ ] [AGENT] P0. **5.B `ScenarioMatrixRunner`.** `unified_trading_library/scenario/matrix_runner.py` — given an
      `ArchetypeId`, drives `ScenarioRunner` over every scenario in the matrix, aggregates `ScenarioReport` rows into a
      `ScenarioMatrixReport` parquet at
      `gs://{pid}-scenario-reports/matrix/{archetype}/{YYYY-MM-DD}/{run_id}/matrix.parquet`. Pass/fail per cell +
      aggregate.
- [ ] [AGENT] P0. **5.C Matrix done-definition.** A matrix run is GREEN iff every cell PASSES every declared
      `expected_outcome` within its `expected_within` SLA. Any FAIL = matrix red. RED matrix is a cutover blocker (Phase
      10).

**Full-execution criterion**:

- ✅ Matrix definition shipped + `ScenarioMatrixRunner` ships + a synthetic dry-run on stub data emits a non-empty
  `matrix.parquet` to the actual GCS bucket.
  - **What ran**: UAC + UTL commits + 1 stub run on agent's local-stack with `--scenario-overlay` flag.
  - **Verification**: `gcloud storage ls gs://${PID}-scenario-reports/matrix/arbitrage_price_dispersion/` (renamed from
    legacy `leveraged_funding_arb` per Stream B canonicalisation 2026-05-07) returns ≥1 dated folder; `parquet` row
    count = matrix cardinality (#scenarios × 1 archetype).

## Phase 6 — Backtest harness wire-in (Days 10-11, ~1.5 AI-days, parallel with Phase 7)

- [ ] [AGENT] P0. **6.A Unified backtest CLI flags.** Per `codex/06-coding-standards/cli-convention.md` axes: extend the
      unified backtest entry (the one Group F item 18 uses) with `--scenario-id <id>` (single-scenario run) +
      `--scenario-matrix <archetype>` (matrix run) + `--scenario-overlay-yaml <path>` (ad-hoc declarative). Mutually
      exclusive with each other.
- [ ] [AGENT] P0. **6.B Pipeline wiring.** Backtest entry instantiates `ScenarioContext` from CLI flag + injects into
      the unified pipeline (MTDS feed → MDPS → features → strategy → execution-matching-engine). `ScenarioContext`
      propagates via the existing config-reloader pattern (no new IPC).
- [ ] [AGENT] P0. **6.C YAML overlay schema.** `ScenarioOverlay` Pydantic round-trips via
      `unified_api_contracts.scenario_overlay.ScenarioOverlay.model_validate_yaml`. Schema published to
      `unified-api-contracts/schemas/scenario_overlay.schema.json` for IDE / UI authoring.

**Full-execution criterion**:

- ✅ Single-scenario CLI run on a real VM (not local) executes end-to-end and emits a `ScenarioReport` parquet.
  - **What ran**: 1 GCE VM launch (`scripts/vm/launch-scenario-runner-vm.sh` — new, in deployment-service per VM
    launcher SSOT); ran `defi_oracle_deviation_30sigma` × `carry_staked_basis` against a representative day.
  - **Verification**: VM events show `STARTED` + `STOPPED`;
    `gcloud storage ls gs://${PID}-scenario-reports/.../report.parquet` returns 1 file; opening the parquet shows ≥1
    outcome assertion result row with `pass=true`/`false`.

## Phase 7 — deployment-api + ui surface (Days 10-12, ~1.5 AI-days, parallel with Phase 6)

- [ ] [AGENT] P1. **7.A `/api/scenarios/list` endpoint.** Returns the full UAC scenario registry as JSON, paginated by
      asset_group. deployment-api Pydantic models mirror UAC types via re-export.
- [ ] [AGENT] P1. **7.B `/api/scenarios/run` endpoint (POST).** Accepts `ScenarioRunRequest` (scenario_id, archetype,
      time_window). Launches a backtest VM via the deployment-service launcher (per VM launcher script SSOT). Returns
      `run_id`. Async; result polled via 7.C.
- [ ] [AGENT] P1. **7.C `/api/scenarios/report/{run_id}` + `/api/scenarios/matrix/{archetype}` endpoints.** Read parquet
      from GCS; cache results.
- [ ] [AGENT] P1. **7.D deployment-ui `Scenarios` tab.** New tab next to Data-Status. Three views: scenario library
      browser (per asset_group), per-archetype regression matrix grid (cells colored pass/fail/not-run), per-scenario
      drilldown (assertions + observed + report links). Re-uses existing `TypedReasonBadges` + `FailurePillarStack`
      design pattern.
- [ ] [AGENT] P1. **7.E Operator-author flow.** "+New Scenario" button → YAML editor → POSTs to a new
      `/api/scenarios/draft` endpoint → previews via `model_validate_yaml` → submits a PR-style commit to
      `unified-api-contracts/registry/scenarios/<asset_group>.py` (NOT auto-merge — operator-review gated). Per
      Citadel-Grade § 7 SSOT, every scenario lives in UAC, not the UI.

**Full-execution criterion**:

- ✅ deployment-ui local dev shows the Scenarios tab; clicking a scenario in the matrix drilldown loads a real
  `ScenarioReport` parquet from GCS and renders pass/fail per assertion.
  - **What ran**: `bash unified-trading-pm/scripts/dev/restart-deployment-stack.sh` (real GCP mode); operator clicked
    through the matrix view.
  - **Verification**: Playwright matrix-view smoke test asserts ≥1 cell rendered with pass/fail badge; drilldown asserts
    ≥1 assertion row visible.

## Phase 8 — Codex SSOTs (Days 11-12, ~1.5 AI-days, parallel with Phase 9 first-archetype run)

- [ ] [AGENT] P0. **8.A NEW `codex/04-architecture/scenario-injection-architecture.md`.** Sections: overlay layer
      model + 6 ScenarioOverlayLayer values + reuse-prod-codepath principle + injection-point map + per-layer applier
      semantics + `synthetic=true` event-stream provenance + LookaheadBias compatibility note + cross-references to
      `live-pipeline-architecture.md` + `replay-subsystem.md`. Stub at Phase 1 commit; full content lands here.
- [ ] [AGENT] P0. **8.B NEW `codex/04-architecture/scenario-outcome-assertions.md`.** Sections: outcome taxonomy closed
      enum + per-archetype matrix shape + fail semantics (matrix-red = cutover-block) + scenario-fail vs real-fire event
      distinction (`synthetic=true`) + alerting wire pattern + cross-reference to `kill-switch-circuit-breaker.md` +
      `autonomous-recovery-matrix.md`.
- [ ] [AGENT] P0. **8.C NEW `codex/02-data/scenario-overlay-semantics.md`.** Sections: overlay parquet schema + per-row
      provenance column + `available_at` discipline under overlay (downgrade to warning, never silently shifted) +
      manifest `scenario_id` column + cross-reference to `honest-absence-downstream-handling.md` +
      `availability-manifest-and-data-status.md`.
- [ ] [AGENT] P0. **8.D UPDATE `kill-switch-circuit-breaker.md`.** Add § "Scenario-driven trips" — how synthetic
      scenarios validate breaker rules; per-rule expected-trip mapping.
- [ ] [AGENT] P0. **8.E UPDATE `autonomous-recovery-matrix.md`.** Add § "Scenario-driven recovery validation" — every
      recovery row gets a paired scenario_id that exercises it.
- [ ] [AGENT] P0. **8.F UPDATE `backtest-groups.md`.** Add scenario-overlay mode as a backtest-group axis.
- [ ] [AGENT] P0. **8.G UPDATE `live-pipeline-architecture.md`.** Add § "Scenario tap points" — 7 layer tap point list +
      reuse-prod-codepath note.
- [ ] [AGENT] P0. **8.H UPDATE `replay-subsystem.md`.** Add § "Scenario overlay on replay" — how the replay subsystem
      composes with overlays for batch backtest.
- [ ] [AGENT] P0. **8.I UPDATE `honest-absence-downstream-handling.md`.** Add § "Scenario-driven gap injection" — how
      each consumer-class behaves under synthetic gaps; per-row `scenario_id` provenance respected.

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

- [ ] [SCRIPT] P0. **9.A Per-archetype matrix runs.** Launch 1 VM per archetype (`carry_staked_basis`,
      `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`)); each VM runs `ScenarioMatrixRunner` over the full
      per-archetype matrix. VMs registered in `VM_PREFIX_TO_BUCKET` per VM Naming Convention.
- [ ] [SCRIPT] P0. **9.B Event-stream verification.** Per "No fire-and-forget VM launches" HARD RULE — every VM emits
      STARTED + per-scenario INSTRUMENT_PROCESSED-equivalent (`SCENARIO_RUN_STARTED` / `SCENARIO_RUN_FINISHED` per
      overlay)
  - STOPPED. Watcher (sub-agent or `ScheduleWakeup`) confirms within 90s of launch.
- [ ] [AGENT] P0. **9.C Failure triage.** Any matrix cell that FAILS its assertion is a finding per Findings Triage
      Discipline. Three dispositions: (a) scenario assertion was wrong (fix the assertion in UAC + re-run); (b) prod
      code has a real defect under that condition (file an issue doc + fix in the appropriate plan); (c) outcome is
      acceptable + the assertion was over-strict (fix + document why). No green-washing.
- [ ] [SCRIPT] P0. **9.D Evidence capture.** For every matrix cell, capture: VM name + run_id + report parquet GCS URI +
      outcome assertion pass/fail. Compiled into a `Phase 9 evidence` table appended to this plan body.

**Full-execution criterion**:

- ✅ Both archetype matrices run end-to-end on real VMs; ≥34 scenario × ≥1 archetype = ≥34 cells per matrix; aggregate
  pass rate ≥95% before Phase 10. Failures all triaged + dispositioned.
  - **What ran**: 2 GCE VMs launched via `deployment-service/scripts/vm/launch-scenario-runner-vm.sh`.
  - **Verification**: `gcloud compute instances list --filter="name~scenario-matrix-"` shows VMs ran to STOPPED;
    `gcloud storage ls gs://${PID}-scenario-reports/matrix/{carry_staked_basis,arbitrage_price_dispersion}/` (renamed
    from legacy `leveraged_funding_arb` per Stream B canonicalisation 2026-05-07) each shows ≥1 matrix.parquet; opening
    the matrix parquet, `pass_rate >= 0.95`; § "Phase 9 evidence" table populated with ≥34 rows per archetype.

## Phase 10 — Cutover gate integration (Day 14, ~0.5 AI-day)

- [ ] [AGENT] P0. **10.A Master plan extension.** `master_to_live_defi_2026_05_23.md` Group F gets new item 17.5 (or
      extension of item 20): "Scenario regression matrix green per archetype within ≤24h of cutover; matrix run as part
      of pre-cutover dress rehearsal." Continuous-verification column populated.
- [ ] [AGENT] P0. **10.B Epic banner.** `plans/epics/live_defi_rollout_2026_05_23.epic.md` epic-table gains a row for
      this plan's matrix gate.
- [ ] [AGENT] P0. **10.C Cross-plan banners removed.** The 4 IN-FLIGHT REFACTOR banners from Phase 0.B come down once
      Phase 9 is green. Per the banner-remove-owner-by-launcher rule.
- [ ] [AGENT] P0. **10.D Cron + continuous verification.** `mtds-scenario-matrix-` cron VM runs both matrices nightly;
      alerting-service rule fires if matrix red >24h. Per `Master Plan Continuous-Verification Column` HARD RULE.

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
- **`risk_simulations_limits_alerting_2026_05_08.md`** (question doc) — circuit-breaker rule taxonomy upstream
  vocabulary. If that question spawns a plan first, this plan's outcome-assertion enum consumes its rule names. If this
  plan ships first, the rule taxonomy seeds from this plan's working set + that plan extends.

## Open questions

(Filled as the plan executes — operator + agent iterate here.)

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

## Audit findings

(Phase 0 sub-agents fill this section — left empty at plan creation.)

## DONE block

(Filled at plan completion; per Plan Format end-of-cycle template.)
