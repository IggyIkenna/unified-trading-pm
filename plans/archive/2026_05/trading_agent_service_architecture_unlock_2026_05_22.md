---
doc_type: plan
title: trading-agent-service architecture unlock (May-23, off-by-default)
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [features-service, strategy-service, trading-agent-service]
scope: [engineer, admin]
tags: []
related:
  [
    /plans/active/master_to_live_defi_2026_05_23.md,
    /plans/archive/2026_05/promote_workflow_may23_cli_path_2026_05_10.md,
    /plans/archive/2026_05/phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md,
    /plans/archive/2026_05/strategy_repo_consolidation_2026_05_19.md,
  ]
created: "2026-05-20"
parent_epic: trading_agent_master
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 8.0
estimate_calibrated_ai_days: 3.2
---

# Trading-Agent Service Architecture Unlock

Wires the closed-loop allocator data flow end-to-end by 2026-05-22, off-by-default for May-23. Flow: features (slow +
regime + ETA + ML + LLM context) + strategy PnL streams -> `trading-agent-service` multi-input allocator ->
`ArchetypeAllocationDirective` -> strategy-service `StrategyDirectiveReloader` -> existing capital allocator. Production
allocator logic, full ML/LLM intelligence, and automatic re-weighting are post-cutover. May-23 scope = data flow wired +
no-op defaults + CI green + backtest-replay no-leak gate.

Codex SSOTs: `/codex/04-architecture/trading-agent-service-directive-pipeline.md` -
`/codex/06-coding-standards/config-reloader-pattern.md`

---

## Phase 1 -- UAC schemas

- [x] ✅ [AGENT] P0. UAC `StrategyPnlStreamEvent` + `ArchetypeAllocationDirective` schemas; 12 unit tests pass.
      (uac@`82b7ad55`)

## Phase 2 -- strategy-service PnL emission

- [x] ✅ [AGENT] P0. strategy-service emits `StrategyPnlStreamEvent` for carry_staked_basis +
      arbitrage_price_dispersion; `_n_instructions_emitted` counter; 6+4 tests pass. UTL STRATEGY_PNL_STREAM constant.
      (strategy-service@`a0f87c66`, utl@`de5ca0a0`, strategy-service@`838a8b2d`)

## Phase 3 -- features-service `performance_features/` scaffold

- [x] ✅ [AGENT] P0. `performance_features/` subdomain in features-service (passthrough; raw PnL fields pass through
      unchanged); 5 unit tests pass. (uac@`72395499`, features-service@`2a7af305`)

## Phase 4 -- UAC facade exports + integration tests

- [x] ✅ [AGENT] P0. UAC root + internal facades export new models; 2 integration tests + 19 total tests pass.
      (uac@`2bdc0f07`)

## Phase 5 -- strategy-service `StrategyDirectiveReloader`

- [x] ✅ [AGENT] P0. `StrategyDirectiveReloader` no-op default + `weight_with_directive()` wired into allocator; 4 tests
      pass. (strategy-service@`afd17fe9`)

## Phase 6 -- trading-agent-service scaffold

- [x] ✅ [AGENT] P0. `AllocationDirectiveLoop` scaffold: ServiceBootstrap + Health + 5 input stream subscribers (3
      stub + 2 real) + no-op directive emission; 5 tests pass. (trading-agent-service@`119fa74`)

## Phase 6.5 -- Backtest-replay infrastructure

- [x] ✅ [AGENT] P0. `replay/inference_cache.py` (write-through in live; cache-only in backtest; CacheMissError),
      `replay/directive_log.py` (full input snapshot per emission), `replay/cutoff_clamp.py` (CutoffViolationError if
      available_at > cutoff in backtest), `cli/main.py` --mode=backtest, UAC `agent_inference_cache.py` schema; 6 unit
      tests + no-leak gate test pass. (uac@`20567882`, trading-agent-service@`33a7ae9`)

## Phase 7 -- CI hygiene

- [x] ✅ [AGENT] P0. trading-agent-service workspace-qg GREEN on live-defi-rollout. GH_PAT rotated by operator (commit
      3c596ba); CI run 26275695242 passed at 2026-05-22T07:55:20Z. All 8 phases DONE.

## Phase 8 -- Codex SSOT + plan manifest

- [x] ✅ [AGENT] P0. All manifest entries M1-M6/PW1-PW2/F1/Q1-Q2/E1-E2/SR1/SA1/FC1 applied; NEW
      `/codex/04-architecture/trading-agent-service-directive-pipeline.md`; UPDATE
      `/codex/06-coding-standards/config-reloader-pattern.md` (DirectiveReloader subsection); inventory regenerated.
      (PM@`d7964d0d`)

## Temporary states + canonical follow-up plans

- **No-op directive emission** (Phase 6): production allocator logic ->
  `plans/epics/strategy_and_dart_master_SUPERSEDED_2026_05_21.md` Phase 10.7 (post-cutover).
- **STUB ML/LLM subscribers** (Phase 6): real derivations -> epic Phase 10.7 + ml_repo_consolidation plan.
- **`performance_features` passthrough** (Phase 3): real rolling sharpe/drawdown/attribution -> epic Allocator service
  post-cutover.
- **Phase 7 CI block**: `BLOCKED-OPERATOR` -- GH_PAT rotation required; unit + scaffold ship with local QG green.

## Deferred work — migrated to:

**MIGRATED FROM:** this plan → `plans/epics/trading_agent_master.md` P3:

- **No-op directive emission** (Phase 6): real allocator logic — post-cutover Phase 10.7, previously in SUPERSEDED epic
- **STUB ML/LLM subscribers** (Phase 6): real derivations — epic Phase 10.7 + `ml_repo_consolidation`
- **`performance_features` passthrough** (Phase 3): rolling sharpe/drawdown/attribution — Allocator service,
  post-cutover
- **Phase 7 CI block** (GH_PAT rotation): `BLOCKED-OPERATOR` — GH_PAT rotation required; unit + scaffold shipped with
  local QG green
