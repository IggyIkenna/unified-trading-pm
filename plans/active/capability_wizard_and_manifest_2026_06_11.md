---
title:
  "Capability wizard + manifest — strategy/venue/instrument/execution/risk capability SSOT, strategy prospectus
  generator, walkthrough wizard UI"
parent_epic: strategy_master
assigned_vm: vm-trading-core
priority: P1
status: active
execution_scope: local-only # design sign-off pending — flip to orchestrator-agent per-phase once operator approves scope
estimate_class: brand-new
estimate_baseline_ai_days: 24.0
estimate_calibrated_ai_days: 24.0
created: 2026-06-11
source:
  - operator direction 2026-06-11 (capability-wizard discussion — ikenna + harsh; session covered availability Q&A,
    walkthrough chaining, collateral/fees/sim-assumption gaps, prospectus generation, two-sided codex audit)
related_plans:
  - plans/epics/strategy_master.md
  - plans/epics/deployment_and_user_management_master.md
  - plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md
  - plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md
locked_by: live-defi-rollout
locked_since: 2026-06-11
---

# Capability wizard + manifest

## Scope

A **capability manifest** (machine-generated SSOT of everything the system can do, edge-by-edge) + a **strategy
prospectus generator** (script that renders a per-configured-strategy document: mechanics, decision logic, exposures,
fund-flow mermaid, risk scenarios, circuit breakers, backtest Sharpe/drawdown) + a **walkthrough wizard UI**
(progressive configuration where every dropdown IS the availability answer). Codex SSOT for the concept:
[`codex/09-strategy/architecture-v2/capability-wizard.md`](../../codex/09-strategy/architecture-v2/capability-wizard.md).

**Four use cases (operator-stated 2026-06-11):**

1. **Visibility** — internal lens into strategy capabilities from instruments/venues/actual data availability through
   risk/margining/execution to fund flows and configurable decision-making per archetype.
2. **End-to-end parameterization** — drive the whole system from a stated execution preference; expose whether we are
   flexible enough, and surface questions the wizard cannot answer (each one = system expansion candidate).
3. **Two-sided audit** — verify what the wizard _thinks_ is possible is _actually_ possible in code; classify dead ends
   as **logical** (options-on-sports — fine) vs **unbuilt** (missing adapter/registry — gap). Orphan + dead-end-path
   detection across all registries.
4. **Client-lite wizard** — eventual client-facing configurator (successor of the public strategy questionnaire in
   `unified-trading-system-ui/app/(public)/questionnaire/`), ending in a config + credentials checklist + on-demand
   backtest ("here is what I need from you: these API keys; want a 5-year backtest of your configured preference?").

**Architecture decisions (operator-confirmed this session):**

- The manifest exporter is a **new generator in the existing PM openapi family**
  (`unified-trading-pm/scripts/openapi/`), reusing its deterministic-output/CI-drift/UI-delivery pipeline. The suite
  must be **repaired first** (Phase 0) — it has CRITICAL drift (phantom pre-consolidation services, architecture_v2
  never extracted; see pre-audit below).
- **Static capability vs runtime data availability stay separate**: the manifest answers "does the code support it";
  runtime "is the data actually there" questions delegate to deployment-api `/api/data-status/*` (drilldown, schema,
  shard-info). The wizard composes both (e.g. min-history-to-run check). Do NOT rebuild the data-status drilldown.
- **Escalation order: script → test → agent.** Every unanswerable question is logged as a typed gap (`missing_registry`
  | `missing_extraction` | `needs_code_scan`); only `needs_code_scan` goes to agent-orchestrator, and agent answers are
  written back into the manifest as annotations (credits spent once). Gaps tracked in
  [`issues/capability_wizard_gap_discovery_2026_06_11.md`](issues/capability_wizard_gap_discovery_2026_06_11.md).
- **UI placement**: wizard = new route group in `unified-trading-system-ui` (DNS/auth/deploy/Firestore already solved;
  self-contained route group keeps iteration context small). Capability matrix = tab in `deployment-ui` next to the
  existing Data Status tab (same ops audience).
- **Prospectus gives away full alpha for now** (debugging mode); curtailment is a later config flag.

## Pre-audit manifest (audited 2026-06-11, this session)

Generator-suite drift (blast radius for Phase 0 — all in `unified-trading-pm/scripts/openapi/`):

| Component                                                                     | Finding                                                                                                                                                                                                                                                                                                   | Severity |
| ----------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| `generate_unified_spec.py:48-78` SERVICE_REGISTRY                             | 10+ phantom services (8× `features-*-service`, `ml-inference/-training`, `pnl-attribution`, `position-balance-monitor`, `risk-and-exposure`) consolidated away; missing `features-service`, `ml-service`, `fund-administration-service`, `greeks-service`                                                 | CRITICAL |
| `generate_ui_reference_data.py`                                               | architecture_v2 NEVER extracted: `StrategyArchetype` (53), `StrategyFamily` (9), `ARCHETYPE_CAPABILITY_REGISTRY`, `AtomicExecutionMode`, `VenueCategoryV2`, `MarginMode`, `KillSwitchReason`, `VenueFeature`, `RiskGateLayer/Decision`, etc. — extraction only walks package-root exports, not submodules | HIGH     |
| `generate_config_registry.py:38-123`                                          | same phantom/missing service configs                                                                                                                                                                                                                                                                      | HIGH     |
| Outputs (`unified-api-contracts/openapi/*.json`)                              | stale May 22–Jun 1; `_validate_service_coverage()` warns but does not FAIL                                                                                                                                                                                                                                | MEDIUM   |
| Source-mode capability matrix (`source-mode-capability-matrix_2026-06-07.md`) | documented manually, not generator-extracted                                                                                                                                                                                                                                                              | HIGH     |

Key code anchors: `unified_api_contracts/internal/architecture_v2/{enums,archetype_capability}.py` ·
`unified_api_contracts/internal/domain/strategy_service/registry.py` (STRATEGY_REGISTRY) ·
`execution_service/algorithms/registry.py` + `utils/instruction_type.py` + `trade_execution/order_types.py` ·
`features_service/delta_one/app/features/registry.py` (~1,382 specs / 34 groups, `features-status` CLI) ·
`ml_service/training/ml/model_registry.py` · `fund_administration_service/allocation/capital_router.py` ·
`unified_trading_library/performance_metrics.py` · `strategy_service/engine/backtest/runner.py` ·
`codex/09-strategy/architecture-v2/archetypes/` (59 files) ·
`codex/04-architecture/wallet-hierarchy-and-capital-flow.md`.

## Dependency DAG

```mermaid
graph LR
  P0[Phase 0 repair generators] --> P1[Phase 1 capability manifest v1]
  P1 --> P2[Phase 2 gap registries in UAC]
  P1 --> P3[Phase 3 prospectus generator]
  P2 --> P3
  P1 --> P4[Phase 4 wizard UI + matrix tab]
  P2 --> P4
  P3 --> P4
  P4 --> P5[Phase 5 agent escalation + backtest-on-demand]
  P2 -. parallel with .-> P3
```

Phase 2 and Phase 3 run PARALLEL after Phase 1 (prospectus consumes gap-registry stubs as `not_registered` until
backfilled). Phase 4 UI work is PARALLEL across the two repos.

## Phase 0 — repair the generator truth layer (`unified-trading-pm/scripts/openapi/`)

- [ ] [IMPLEMENT] P0. SERVICE_REGISTRY: remove phantom pre-consolidation services; add `features-service`, `ml-service`,
      `fund-administration-service`, `greeks-service`; same sweep for CONFIG_REGISTRY in `generate_config_registry.py`.
- [ ] [IMPLEMENT] P0. Auto-discover services from `workspace-manifest.json` instead of hardcoded lists;
      `_validate_service_coverage()` FAILS the run on disk-vs-registry mismatch (today it only warns).
- [ ] [IMPLEMENT] P0. Extend `extract_uic_enums()` to recursively walk `unified_api_contracts.internal` submodules
      (`architecture_v2.*`) so all 53-archetype/9-family enums + ARCHETYPE_CAPABILITY_REGISTRY land in
      `ui-reference-data.json`.
- [ ] [SCRIPT] P1. Fresh full run of `generate-unified-openapi.sh`; commit regenerated outputs; verify
      `check_openapi_drift.py` quality gate is green and actually fires on synthetic drift.
- [ ] [VERIFY] P1. Drift CI gate: scheduled check that SERVICE_REGISTRY/CONFIG_REGISTRY match on-disk workspace state
      (fail, not warn) so the suite cannot silently rot again.

## Phase 1 — capability manifest exporter v1 (`generate_capability_manifest.py`)

- [ ] [SPEC] P0. `CapabilityManifest` pydantic schema in unified-api-contracts: nodes (archetype, family, venue, chain,
      instrument_type, algo, feature_group, model, data_source, fund_structure, wallet, broker) + typed edges with
      status `available | partial | not_available | not_registered` + gap type
      `missing_registry | missing_extraction | needs_code_scan | logical_dead_end` + `agent_annotation` field for
      written-back agent answers.
- [ ] [IMPLEMENT] P0. Extract: STRATEGY_REGISTRY + ARCHETYPE_CAPABILITY_REGISTRY (archetype × venue_category ×
      instrument_type), venue/instrument universe (instruments-service `InstrumentRecord` + ENDPOINT_REGISTRY incl.
      per-venue access_mode/auth requirements), execution algos + instruction types + order-type/TIF enums
      (FOK/IOC/post-only, make/take), feature registry (34 groups incl. per-group lookback), ML model registry (training
      windows), KillSwitchReason + RiskGateLayer/Decision, MarginMode, deployments/cloud topology (lifecycle_class,
      AWS/GCP), sports leagues + prediction question groups from the instruments snapshot.
- [ ] [IMPLEMENT] P1. Source-mode matrix extraction: batch/live/replay × source × transport (WS vs REST) — codify the
      manual `source-mode-capability-matrix_2026-06-07.md` audit into registry + extraction so batch/live symmetry is
      queryable per data source.
- [ ] [IMPLEMENT] P1. Derived edges: **min-data-to-run** per (archetype, venue, timeframe) = max feature-group lookback
      × ML training window; emitted as a manifest edge the wizard checks against live shard counts via deployment-api.
- [ ] [IMPLEMENT] P1. Orphan + dead-end report: registry entries nothing references; wizard paths that dead-end;
      classify `logical_dead_end` vs unbuilt (use case 3). Extend the existing orphan-report pattern.
- [ ] [VERIFY] P1. Determinism + drift gate for the manifest (same CI pattern as ui-reference-data.json); manifest ships
      to `unified-trading-system-ui/lib/registry/` via the existing uic-openapi-sync workflow.

## Phase 2 — gap registries in unified-api-contracts (schema first = forcing function; PARALLEL items)

- [ ] [SPEC] P0. **Collateral registry**: accepted collateral per venue, haircut per collateral, max/liquidation LTV,
      maintenance vs liquidation margin, liquidation protocol description per platform, broker list. Today derived from
      wallet structure (DeFi 20/80 treasury/hot, CeFi 0/100) — must become declarative.
- [ ] [SPEC] P1. **Fees registry**: exchange/gas/broker/clearing fees, queryable at venue, instrument-type, and tier
      granularity.
- [ ] [SPEC] P1. **Simulation-assumptions registry**: simulatable candle granularities, matching/fill assumptions per
      archetype area, backtest-live symmetry nuances per venue/instrument.
- [ ] [SPEC] P1. **Fund-structure manifest**: pooled/SMA/prop structures, subscription/redemption cadence (daily
      withdraw/deposit support), rebalance cadence — fund-administration-service state machines stay the runtime truth;
      this declares what is _offerable_.
- [ ] [SPEC] P1. **Order-semantics-per-venue-adapter declarations**: which TIF/post-only/make-take each adapter honors;
      ref-pricing modes (fixed entry vs delta-adjusted to underlying); **multi-leg/spread handling** — which algo owns
      delta risk between legs of basis/spread/option-combo instructions; auth-wired status per venue.
- [ ] [SPEC] P2. **Trading-agent/LLM capability declarations**: which archetypes permit agent-driven instruction
      generation over features, permitted models, parameter-guidance scope (trading-agent-service ↔ strategy registry
      link, today absent).
- [ ] [IMPLEMENT] P1. Manifest exporter consumes each new registry as it lands; until then emits honest `not_registered`
      edges (never silently omits the dimension).

## Phase 3 — strategy prospectus generator (script first, UI later; PARALLEL with Phase 2)

- [ ] [IMPLEMENT] P0. `generate_strategy_prospectus.py`: input = strategy config + capability manifest → markdown: what
      the strategy does, decision logic (FULL alpha disclosure — debugging mode; curtailment flag later),
      position-by-scenario table ("in this scenario the strategy will be positioned…"), expected
      returns/Sharpe/max-drawdown (from `performance_metrics.py` over backtest output), written as if presenting to the
      internal allocation team / a potential investor.
- [ ] [IMPLEMENT] P1. Exposure section: per-leg exposures and normalization — staked-ETH vs ETH equivalence,
      base-currency-neutral views; pull from greeks-service / ledger exposure models where available, else emit
      `not_registered` gap.
- [ ] [IMPLEMENT] P1. **Fund-flow mermaid**: venues/wallets as boxes (treasury vs trading/hot per
      `wallet-hierarchy-and-capital-flow.md` + `capital_router.py` AllocationTargets), deposit→conversion→venue paths
      (e.g. deposit ETH → receive stETH → post to CeFi venue → short perp), cross-balance movement arrows.
- [ ] [IMPLEMENT] P1. Risk section: applicable KillSwitchReason set + RiskGateLayer placement for the configured
      archetype/venues, configurable circuit-breaker parameters, liquidation monitoring surface.
- [ ] [AUDIT] P1. **Two-sided audit**: diff generated prospectus vs the hand-written codex archetype doc
      (`codex/09-strategy/architecture-v2/archetypes/<archetype>.md`) for all 53 archetypes; discrepancy report feeds
      the gap tracker (wizard-thinks vs codex-says vs code-does).
- [ ] [VERIFY] P2. Pin a regression test per fixed discrepancy (operator rule: as issues are found, build tests around
      them).

## Phase 4 — wizard UI + capability matrix tab (PARALLEL across repos)

- [ ] [AGENT][UI] P1. `unified-trading-system-ui`: new self-contained route group `app/(wizard)/` + `lib/wizard/`.
      Manifest-driven progressive configuration: each step's options filtered to what remains possible given prior
      answers; unavailable options visible-but-greyed with reason + gap type; every config field shows side-by-side help
      text sourced from pydantic `Field(description=…)` (extend config-registry extraction to carry descriptions). Seeds
      vocabulary from `lib/questionnaire/` axes. pw:L2 gate.
- [ ] [AGENT][UI] P1. Wizard output: strategy configuration artifact + onboarding checklist — required API
      keys/credentials per selected venue (from ENDPOINT_REGISTRY auth requirements), deposit currency/cadence,
      collateral placement — the "what I need from you to get started" surface.
- [ ] [AGENT][UI] P1. `deployment-ui`: **Capability tab** next to Data Status — full matrix view (archetype × venue ×
      instrument × mode × algo), orphan/dead-end report, batch-live symmetry view; leaf data-availability questions call
      existing `/api/data-status/*` (drilldown/schema/shard-info) — no rebuild. pw:L2 gate.
- [ ] [IMPLEMENT] P2. Wizard "isolation mode": flat queries (what strategies/venues/algos/instructions exist) alongside
      the chained walkthrough — same manifest, two query styles.

## Phase 5 — agent escalation + backtest-on-demand

- [ ] [IMPLEMENT] P1. `needs_code_scan` gap → agent-orchestrator task (existing planning-VM workflow); agent answer
      written back as manifest `agent_annotation` so the question is never paid for twice. Strict gating: agents only
      when script/registry cannot answer (operator rule).
- [ ] [IMPLEMENT] P2. Backtest-on-demand: wizard config → `strategy_service/engine/backtest/runner.py` over last N years
      → metrics into the prospectus ("want to see a 5-year backtest of your configured preference?"). Depends on
      data-availability precheck via deployment-api.
- [ ] [DEFERRED] P3. Client-lite wizard mode (use case 4) — named successor plan once internal wizard is hardened.

## Wave 2 — proposed enhancements (Claude 2026-06-11; PENDING OPERATOR SIGN-OFF, do not dispatch)

Question bank SSOT (every wizard question pinned to its code anchor):
[`codex/09-strategy/architecture-v2/capability-wizard-question-bank.md`](../../codex/09-strategy/architecture-v2/capability-wizard-question-bank.md).

- [ ] [DESIGN] P2. **Counterfactual "minimal unlock set" engine** — every unavailable edge computes the smallest set of
      missing pieces that would make it available ("Hyperliquid perps: adapter ✓, auth ✗ — 1 edge away"); wizard counts
      demand per blocked edge; weekly demand-weighted gap report auto-emits canonical todos into the gap tracker (same
      ingestion path as `regen_backlog_from_plan.py`). The wizard becomes a roadmap generator.
- [ ] [DESIGN] P2. **Readiness badges per edge** — stamp every capability edge with operational maturity derived from
      the deployments registry + shadow ledger + archived plans:
      `backtest-only | shadow-observed | staging-proven |     live-proven`, mapped to the C/D/B gate model in
      PLAN_FORMAT.md. "Available" without "ever ran" is a different answer.
- [ ] [DESIGN] P2. **Config-space fuzzer → generated smoke tests** — mechanically enumerate reachable wizard configs,
      sample, compile each to a system-integration-tests batch mock-fill scenario. Use-case-3 audit by _execution_, not
      inspection: every reachable config must at least smoke-run; failures are mechanical dead-end findings.
- [ ] [DESIGN] P2. **Manifest as MCP server + conversational wizard agent** — tools: `query_manifest`, `data_status`
      (deployment-api), `run_backtest`, `render_prospectus`; agent-orchestrator hosts it. Powers the "what I need from
      you is these API keys — want a 5-year backtest?" dialogue with answers grounded in registry paths, not model
      memory.
- [ ] [DESIGN] P2. **Versioned manifest + capability changelog + regression CI** — manifest generated per commit; diffs
      = "what the system learned to do this month" (investor-update material); CI FAILS when an edge regresses
      `available → not_available` without a plan reference.
- [ ] [DESIGN] P2. **Inverse wizard / screener** — start from holdings ("I have BTC today, USDT tomorrow") or targets
      (Sharpe ≥ 1.5, max DD ≤ 10%, carry ≥ 8%) and search the manifest + backtest metrics for qualifying archetypes,
      ranked.
- [ ] [DESIGN] P2. **Portfolio mode** — compose multiple configured strategies: aggregate/netted exposures
      (internalization detection when one leg longs what another shorts), correlation from backtests, capital routing
      across pools/SMA via portfolio_allocator + capital_router. Directly models the two-pooled-investors-now /
      SMA-next-year scenario.
- [ ] [DESIGN] P2. **Cost & capacity model** — full fee stack (exchange/gas/broker/clearing + funding + slippage via
      execution cost prediction) + infra cost per lifecycle_class → **breakeven AUM** per configured strategy; capacity
      ceiling vs venue liquidity/min-ticket constraints.
- [ ] [DESIGN] P3. **Wizard sessions as reproducible artifacts** — session JSON (answers + manifest version + config +
      prospectus hash); nightly replay of saved sessions against the fresh manifest (batch-live-reconciliation pattern)
      alerts when an old answer silently changes; doubles as the client-onboarding compliance record.
- [ ] [DESIGN] P3. **Dual-register copy** — every question/config field carries engineer copy (config path, code anchor)
      AND allocator/investor copy (plain English), reusing the existing glossary Term components; prospectus renders in
      either register.
- [ ] [DESIGN] P3. **Named stress-scenario library** — curated historical windows (May-2021 crash, FTX week, Shapella, a
      funding-flip regime) replayed through the backtest runner per configured strategy; positions/PnL/triggered
      kill-switches become the prospectus risk slides.
- [ ] [DESIGN] P3. **Jurisdiction overlay** — investor entity/jurisdiction filters venues/instruments at Stage A
      (client_isolation_and_governance restrictions), so a config can never include a venue the investor cannot legally
      touch.

## Success criteria

- Phase 0: fresh generator run green; zero phantom/missing services; architecture_v2 enums + capability registry present
  in `ui-reference-data.json`; drift gate FAILS on synthetic mismatch.
- Phase 1: manifest covers all 53 archetypes × all registered venues/instruments/algos/sources; every dimension either
  populated or carries a typed gap — **no silent omissions**; orphan/dead-end report distinguishes logical vs unbuilt.
- Phase 2: each gap registry has UAC schema + at least MVP-universe backfill; manifest consumes them.
- Phase 3: prospectus renders for all 53 archetypes; two-sided audit report produced; discrepancies filed as gaps.
- Phase 4: wizard walkthrough reaches a complete strategy config for ≥3 real archetypes (e.g. carry spot-vs-perp BTC,
  LST-stake-and-short-perp, an options vol archetype) with only-valid-options filtering; capability tab live in
  deployment-ui; pw:L2 green both repos.
- Phase 5: one real `needs_code_scan` gap round-tripped through the orchestrator into a manifest annotation; one
  backtest-on-demand round trip from wizard config to prospectus metrics.

## Full-execution criterion

`bash scripts/openapi/generate-unified-openapi.sh && python scripts/openapi/generate_capability_manifest.py && python scripts/openapi/generate_strategy_prospectus.py --archetype carry_basis_perp`
on the laptop (full workspace) completes end-to-end: regenerated registries, manifest with 0 untyped unknowns, rendered
prospectus whose two-sided audit section diffs against
`codex/09-strategy/architecture-v2/archetypes/carry-basis-perp.md`. Wizard verified via Playwright L2 on both UI repos
against the committed manifest.

## Codex SSOT updates

- NEW
  [`codex/09-strategy/architecture-v2/capability-wizard.md`](../../codex/09-strategy/architecture-v2/capability-wizard.md)
  — concept SSOT (shipped with this plan).
- `codex/14-customer-journeys/` — strategy-onboarding journey update when Phase 4 lands.
- `plans/audit/instructions/strategy_master_audit_instructions.md` — add recurring two-sided-audit criterion (wizard vs
  codex vs code) once Phase 3 ships.

## Findings discipline (operator direction 2026-06-11)

Autonomous build dispatched 2026-06-11 under `cursor-configs/AUTONOMOUS_AGENT_RULES.md`. Two side-docs, both mandatory
for every agent on this plan:

- **Capability gaps** (missing registries/extractions) →
  [`issues/capability_wizard_gap_discovery_2026_06_11.md`](issues/capability_wizard_gap_discovery_2026_06_11.md)
- **Bugs / conflicting truths / dual implementations / understanding gaps** →
  [`issues/capability_wizard_analysis_findings_2026_06_11.md`](issues/capability_wizard_analysis_findings_2026_06_11.md)

## Progress Log (append-only — survives context compression)

- 2026-06-11 — Plan + codex SSOT (`capability-wizard.md`) + question bank + gap tracker + findings doc authored;
  strategy_master related_plans updated (+ duplicate section fix = F6). Autonomous execution started: Wave 1 = Phase 0
  generator repair (PM, sub-agent) ∥ UAC capability/gap schemas (sub-agent). Wave 2 = exporter → prospectus → UI.

## Out of scope / named successors

- Client-facing lite wizard + alpha-curtailment tiers (use case 4) — successor plan.
- Replacing the public strategy questionnaire — it stays as demand capture; wizard supersedes it only for onboarding.
- Rebuilding any part of the data-status drilldown — delegation only.
- Live integration beyond deployment-api data-status + backtest runner calls (wizard is registry/code-driven by design).
