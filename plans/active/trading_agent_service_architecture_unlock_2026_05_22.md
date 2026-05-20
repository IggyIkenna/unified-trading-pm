---
name: trading-agent-service-architecture-unlock
overview:
  Wire the trading-agent-service closed-loop allocator architecture end-to-end by 2026-05-22, off-by-default.
  Data flow: features (slow + regime + ETA + ML + LLM context) + strategy PnL streams (live + paper + shadow) →
  trading-agent-service multi-input allocator → AllocationDirective → strategy-service StrategyDirectiveReloader →
  existing capital/equity allocator. Production allocator logic, full ML/LLM intelligence, continuous paper for
  non-DeFi archetypes, and automatic re-weighting are all post-cutover. May-23 scope = data flow wired + no-op
  defaults + CI green.
type: plan
status: in-progress
priority: P0
created: 2026-05-20
deadline: 2026-05-22
horizon: 2 days
locked_by: live-defi-rollout
locked_since: 2026-05-20
parent_plan: master_to_live_defi_2026_05_23.md
parent_epic: plans/epics/strategy_and_dart_master_2026_05_07.md (§1.7 Phase 10.7 + § Allocator service)
estimate_class: refactor
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 3.2
estimate_calibration_note: |
  Class=refactor (multiplier 0.4×). Baseline 8 cal-AI-days = sum of: UAC schema additions 0.5 + strategy PnL
  emission 1 + features performance_features scaffold 0.5 + strategy DirectiveReloader 0.5 + trading-agent-service
  scaffold 2 + backtest-replay infrastructure (Phase 6.5) 1 + CI hygiene fix 0.5 + master+epic plan updates 0.5 +
  codex SSOT writing 1.5. Calibrated 3.2 days reflects that 6 of 8 phases are pure-scaffolding (Pydantic model +
  Protocol stub + no-op default) — heavy lift is mostly typing + wiring + tests, not algorithm design. Phase 6.5
  added 2026-05-20 per operator directive on backtest-no-leak discipline.
related_plans:
  - plans/active/master_to_live_defi_2026_05_23.md
  - plans/active/promote_workflow_may23_cli_path_2026_05_10.md
  - plans/active/phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md
  - plans/active/uac_source_capability_metadata_promotion_2026_05_20.md
  - plans/active/strategy_repo_consolidation_2026_05_19.md
  - plans/active/issues/trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md
  - plans/active/issues/_trading_agent_unlock_plan_change_manifest_2026_05_20.md
  - plans/epics/strategy_and_dart_master_2026_05_07.md
related_codex:
  - codex/06-coding-standards/config-reloader-pattern.md
  - codex/04-architecture/promote-workflow-architecture.md
  - codex/04-architecture/trading-agent-service-directive-pipeline.md  # NEW — Phase 8
  - codex/09-strategy/architecture-v2/cross-cutting/pnl-attribution.md
codex_ssots:
  - codex/04-architecture/trading-agent-service-directive-pipeline.md  # NEW
  - codex/06-coding-standards/config-reloader-pattern.md  # UPDATE (add directive reloader pattern)
foundation_gate:
  - layer: 4 (UAC schema)        # blocking: Phase 1, Phase 4
  - layer: 5 (features-service)  # depends on UAC; Phase 3 wires consumer
  - layer: 6 (strategy-service)  # depends on UAC + features; Phase 2 emits, Phase 5 consumes
  - layer: 7 (trading-agent-service)  # depends on layers 4+5+6; Phase 6 wires scaffold
---

# Trading-agent-service architecture unlock (May-23)

> **Operator directive 2026-05-20**: "architecture unlocked even if not paper tested yet". Cutover-day reality: data
> flow wired end-to-end; off-by-default; production logic ships post-cutover.

## Why this plan exists

The closed-loop allocator architecture (operator brief 2026-05-20):

```
slow features (regime, narrative, ETA) + ML inference + LLM context + strategy PnL streams (live + paper + shadow)
        ↓
trading-agent-service: multi-input portfolio allocator
        ↓
strategy-config directives (allocation weights + params + on/off)
        ↓
strategy-service: config hot-reload — existing capital/equity allocator consumes directives
        ↓
strategy execution (live + continuous paper) → emits PnL → feeds back to top
```

Architecture-unlock = the dataflow is wired end-to-end and operates **off-by-default**. NOT REQUIRED for May-23:
continuous paper for non-DeFi archetypes, full ML/LLM intelligence, production allocator logic, automatic re-weighting.
Those land post-cutover via epic §1.7 Phase 10.7 + § Allocator service.

## Pre-Audit Before Execution (Citadel-Grade)

**Workspace pre-audit findings** (2026-05-20 slot-1-main):

- `unified_api_contracts/internal/strategy_pnl_stream.py` — does NOT exist (greenfield)
- `unified_api_contracts/internal/strategy_directives.py` — does NOT exist (greenfield)
- `strategy_service/portfolio_allocator/archetypes.py` — EXISTS (per master plan line 899); 8-archetype scaffold not yet
  populated (epic line 269 P1 — post-cutover)
- `strategy_service/config_reloaders.py` — EXISTS (4× duplicates per strategy-repo-consolidation Phase 5);
  `StrategyDirectiveReloader` adds 5th typed-reloader callsite
- `features_service/performance_features/` — does NOT exist (greenfield subdomain)
- `trading-agent-service/trading_agent_service/` — repo exists; workspace-qg currently RED (CI hygiene issue
  `trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md` — credentials rotation pending operator)
- Schema-collision check with `uac_source_capability_metadata_promotion_2026_05_20.md`: slot-3 touches
  `unified_api_contracts/registry/capability.py` + `capability_declarations/`. THIS plan touches
  `unified_api_contracts/internal/` — **non-overlapping directories**; both can land in parallel. Confirmed 2026-05-20.

**No symbol removal / rename** in this plan — pure-additive UAC + service-scaffold work. Cleanup of duplicated
declarations is out of scope (post-cutover via strategy-repo-consolidation Phase 5).

## Scope: architecture-only (NOT production logic)

**In scope (May-23)**:

- UAC `StrategyPnlStreamEvent` + `AllocationDirective` Pydantic models
- strategy-service emits `StrategyPnlStreamEvent` for `carry_staked_basis` + `arbitrage_price_dispersion` (May-23 lead
  pair)
- features-service `performance_features/` subdomain — passthrough today (subscribes to PnL stream, emits unchanged)
- strategy-service `StrategyDirectiveReloader` — defaults to no-override when no directive present; existing
  capital/equity allocator reads from directive value when one is present
- trading-agent-service core scaffold — subscribes to features + PnL streams (other inputs stubbed); emits no-op
  directive
- CI hygiene fix for trading-agent-service workspace-qg
- master plan + promote plan + features Phase-5 plan + epic + issue elevated per change manifest

**Out of scope (POST-CUTOVER successors named)**:

- Production allocator logic (8 archetype engines per epic § Allocator service P1) → epic §1.7 Phase 10.7 post-cutover
- LLM context + ML inference integration → epic §1.7 Phase 10.7 post-cutover
- Continuous paper for non-DeFi archetypes → per-archetype paper-runnable matrix (`pvl-p18b`) post-cutover
- Automatic re-weighting / cadence scheduler / shadow mode → epic § Allocator service post-cutover
- IM-side allocator UI + Trading-platform-side allocator UI → epic §1.7 Phase 10.7 post-cutover

## Phased execution DAG (Citadel-Grade §2)

```
Phase 1 (UAC schemas — BLOCKING; ~0.5d, layer-4)             [Slot N, can be slot-1-main]
  └─ UAC Pydantic models for PnL stream + AllocationDirective
        QG gate: UAC quality-gates.sh green; no consumer breakage

Phase 2 (parallel after Phase 1 — strategy emission; ~1d, layer-6)
Phase 3 (parallel after Phase 1 — features performance_features; ~0.5d, layer-5)
Phase 4 (parallel after Phase 1 — UAC __init__ exports + tests; ~0.2d, layer-4)
        QG gate: strategy-service + features-service QG green; carry + APD emit PnL events;
                 features-service writes performance_features parquet (empty per honest-absence)

Phase 5 (depends on Phases 1+2 — strategy DirectiveReloader; ~0.5d, layer-6)
Phase 6 (depends on Phases 1+2+3 — trading-agent-service scaffold; ~2d, layer-7)
Phase 7 (parallel — CI hygiene; ~0.5d, layer-7)
        QG gate: trading-agent-service QG green (after credential rotation per Phase 7);
                  strategy-service hot-reloads no-op directive without crash;
                  trading-agent-service emits no-op directive on subscriber start

Phase 8 (depends on all prior — codex SSOT + plan updates; ~0.5d, doc-layer)
        Done gate: codex SSOT shipped; change-manifest entries M1-M6 + PW1-PW2 + F1 + Q1-Q2 + E1-E2 applied;
                    inventory regenerator rerun; master plan Group-C verification rows show actual SHAs
```

Cross-phase parallelism: Phase 1 is the ONLY blocking item. Phases 2/3/4 fan out to 3 slots. Phase 5+6 sequence after
their dependencies; Phase 7 is parallel-anytime; Phase 8 is the final doc-layer pass.

**Foundation-gate feasibility check** (per CLAUDE.md "Plans Run To Actual Completion" + foundation_gate frontmatter):

| Layer | Prerequisite                        | Effort    | Owner              | Achievable in May-23 window?                                                              |
| ----- | ----------------------------------- | --------- | ------------------ | ----------------------------------------------------------------------------------------- |
| 4     | UAC schemas (Phase 1)               | ~0.5 day  | slot-1 or slot-N   | YES — Pydantic + tests + exports                                                          |
| 5     | features performance_features (Ph3) | ~0.5 day  | features-slot      | YES — passthrough subscriber + manifest emit                                              |
| 6     | strategy emits + reloader (Ph2+5)   | ~1.5 days | strategy-slot      | YES — emit at 2 archetype boots; reloader is no-op                                        |
| 7     | trading-agent-service (Ph6+7)       | ~2.5 days | trading-agent slot | TIGHT — needs CI green (credential rotation) + scaffold; achievable with 1 dedicated slot |

Total: 5 cal-AI-days across 4 layers, parallelisable to 2.8 cal-AI-days wall-clock. Fits May-22 deadline with 2 days
slack against May-23 cutover.

## Phase 1 — UAC schemas (P0, BLOCKING, ~0.5 days, layer-4)

**Agent execution prompt** (paste at top of Task spawn):

```
Read SUB_AGENT_MANDATORY_RULES.md first.
Repo: unified-api-contracts. Branch: live-defi-rollout. Worktree: .tabs/<N>/unified-api-contracts/.

Task: ship 2 new Pydantic v2 models in unified_api_contracts/internal/. Pure-additive, no renames.

Files to CREATE:
1. unified_api_contracts/internal/strategy_pnl_stream.py — StrategyPnlStreamEvent Pydantic model
2. unified_api_contracts/internal/strategy_directives.py — AllocationDirective Pydantic model
3. unified_api_contracts/internal/__init__.py — add the 2 exports

Files to UPDATE:
- unified_api_contracts/__init__.py — re-export both via the standard `from unified_api_contracts.internal import ...` surface

Schema constraints (verbatim from operator brief 2026-05-20):

StrategyPnlStreamEvent fields:
  - archetype_id: str   # canonical archetype name, e.g. "carry_staked_basis"
  - mode: Literal["live", "paper", "backtest_continuation"]
  - pnl_realized: Decimal
  - pnl_unrealized: Decimal
  - equity: Decimal
  - n_trades: int
  - sharpe_window_N: Decimal | None  # None if window not yet filled
  - drawdown_window_N: Decimal | None
  - timestamp: datetime  # UTC, tz-aware
  # CLAUDE.md compliance: include available_at: datetime per available_at-is-per-row rule
  - available_at: datetime

AllocationDirective fields:
  - archetype_id: str
  - allocation_weight: Decimal  # 0.0 ≤ x ≤ 1.0 (validator)
  - enabled: bool
  - param_overrides: dict[str, Any]  # closed-set future-restrict but for May-23, Any-OK with docstring caveat
  - valid_from: datetime
  - valid_until: datetime | None    # None = no expiry
  - source: str                     # which agent emitted (e.g. "trading-agent-service-stub" for no-op)
  - available_at: datetime

Validation rules:
- `0.0 ≤ allocation_weight ≤ 1.0` (pydantic Field constraint)
- `valid_from < valid_until` if `valid_until` set
- `available_at >= timestamp` for PnL event; `available_at >= valid_from` for directive

Tests to add (tests/internal/):
- test_strategy_pnl_stream.py: 6 tests — happy path (live/paper/backtest), None for unfilled sharpe, validator
  reject for negative equity (or NOT — operator may want shadow archetypes with negative equity; CHECK BRIEF; if
  unclear, allow + flag in docstring).
- test_strategy_directives.py: 6 tests — happy path (no-op default), validator reject for weight > 1.0, validator
  reject for valid_from > valid_until.

Quality gate: `cd unified-api-contracts && bash scripts/quality-gates.sh` green.

Do NOT modify capability.py, capability_declarations/, or any registry/ files (orthogonal to this work; slot-3 is
actively modifying those per uac_source_capability_metadata_promotion plan).
```

**Done criterion**: 2 modules ship + 12 unit tests pass + UAC QG green. Sub-agent reports back with
`unified-api-contracts@<sha>`.

**Continuous verification**: weekly UAC QG run on `live-defi-rollout` (existing); new tests live in `tests/internal/`.

## Phase 2 — strategy-service emits PnL (P0, after Phase 1, ~1 day, layer-6)

**Agent execution prompt**:

```
Read SUB_AGENT_MANDATORY_RULES.md first.
Repo: strategy-service. Worktree: .tabs/<N>/strategy-service/.

Task: emit StrategyPnlStreamEvent at the May-23 lead-pair archetypes.

Files to UPDATE:
1. strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py — at the end of each tick that emits a fill,
   emit StrategyPnlStreamEvent via UTL log_event with archetype_id="carry_staked_basis".
2. The arbitrage_price_dispersion handler (search strategy_service/engine/strategies/v2/ for the v2 handler;
   archetype enum at unified_api_contracts.internal.architecture_v2.enums.StrategyArchetype.ARBITRAGE_PRICE_DISPERSION).
   Emit StrategyPnlStreamEvent for funding-rate-dispersion variant.

Implementation notes:
- Use UTL `log_event(EventType=STRATEGY_PNL_STREAM, payload=StrategyPnlStreamEvent(...))`. If EventType not yet defined,
  add to `unified_trading_library/events/event_types.py` AS PART OF THIS PHASE (small additive change; UTL QG green required).
- PnL fields: read from existing position-balance-monitor / pnl-attribution surfaces inside strategy-service post-consolidation
  (per strategy_repo_consolidation Phase 6 — sub-packages live at strategy_service/position/, strategy_service/pnl/).
- mode field: read from OperationalMode env / config (already wired per pvl-p17a/b/d). Live runs → "live", paper → "paper".
- sharpe_window_N + drawdown_window_N: if not enough trades, emit None. Do NOT block the event.

Tests:
- Unit test that simulated tick → StrategyPnlStreamEvent emitted with correct fields (4 cases: live+carry, paper+carry, live+APD, paper+APD).
- Honest-absence test: 0-trade tick still emits event with n_trades=0 + pnl_realized=0.

Quality gate: `cd strategy-service && bash scripts/quality-gates.sh` green.
```

**Done criterion**: 2 archetypes emit `StrategyPnlStreamEvent`; 4+ unit tests pass; strategy-service QG green.

**Continuous verification**: existing strategy-service QG; add specific check
`grep -l "StrategyPnlStreamEvent" strategy_service/engine/strategies/v2/` returns ≥2 matches.

## Phase 3 — features-service performance_features scaffold (P0, after Phase 1, ~0.5 days, layer-5, PARALLEL with Phase 2)

**Agent execution prompt**:

```
Read SUB_AGENT_MANDATORY_RULES.md first.
Repo: features-service. Worktree: .tabs/<N>/features-service/.

Task: ship the performance_features/ subdomain as a passthrough subscriber (no derivation today).

Files to CREATE:
- features_service/performance_features/__init__.py
- features_service/performance_features/passthrough_compute.py — subscribes to STRATEGY_PNL_STREAM events;
  emits FeaturesComputedEvent with feature_group="performance_features" containing the raw PnL fields as columns;
  manifest emit via UTL record_captured(...) (cluster validation MANDATORY per CLAUDE.md "Manifest + honest absence" rule).
- features_service/performance_features/cli_handler.py — handler invoked by features_service.<asset_group>.cli with
  --feature-group performance_features. Honest-absence path: if no upstream STRATEGY_PNL_STREAM events for the day,
  emit record_empty(reason=EXPECTED_NO_PNL_STREAM).

UAC update needed (sub-task; UAC QG run required):
- Add EXPECTED_NO_PNL_STREAM to UAC EmptyConfirmedReason enum at
  unified_api_contracts/canonical/crosscutting/honest_coverage.py. Pure additive.

Tests:
- Unit: subscriber receives StrategyPnlStreamEvent → emits FeaturesComputedEvent + writes parquet (single archetype).
- Unit: no events for day → record_empty(reason=EXPECTED_NO_PNL_STREAM).
- Unit: parquet schema matches UAC contract.

Quality gate: `cd features-service && bash scripts/quality-gates.sh` green.
```

**Done criterion**: subdomain ships; 3 unit tests pass; features-service QG green; manifest shows `performance_features`
row with `empty_confirmed` for the May-23 lead-pair date range (no PnL events yet → honest absence).

**Continuous verification**: features-service QG + manifest-status panel shows `performance_features` row for lead-pair
date range.

## Phase 4 — UAC **init** exports + integration tests (P1, after Phase 1, ~0.2 days, PARALLEL)

**Agent execution prompt**: small follow-up to Phase 1 — ensure facades export the 2 models from `unified_api_contracts`
root + add 2 integration tests that round-trip serialize/deserialize via JSON. Quality gate: UAC QG green.

## Phase 5 — strategy-service StrategyDirectiveReloader (P0, after Phase 1+2, ~0.5 days, layer-6)

**Agent execution prompt**:

```
Read SUB_AGENT_MANDATORY_RULES.md first.
Repo: strategy-service. Worktree: .tabs/<N>/strategy-service/.

Task: add StrategyDirectiveReloader to strategy_service/config_reloaders.py using the existing typed-reloader pattern
(per codex/06-coding-standards/config-reloader-pattern.md). Wires AllocationDirective consumption into the existing
capital/equity allocator.

Files to UPDATE:
1. strategy_service/config_reloaders.py — add StrategyDirectiveReloader class. Subscribes to AllocationDirective
   events; maintains in-memory dict[archetype_id, AllocationDirective] keyed by archetype with TTL = valid_until.
2. strategy_service/portfolio_allocator/archetypes.py — the existing capital/equity allocator reads from the
   reloader BEFORE falling back to static config. NO-OP default: if no directive present for archetype, falls back
   to static config exactly as today.

Implementation notes:
- Reloader pattern: extends/wraps `make_config_reloader` if a generic helper exists; otherwise mirror the shape of
  existing reloaders (e.g. _PagingCredentialsReloader from alerting-service@9d4150d per master plan line 500).
- TTL handling: directive expires at valid_until → reloader silently drops + falls back to static. Log_event
  DIRECTIVE_EXPIRED for observability.
- Source-attribution: directive.source field surfaced in lifecycle log for audit-trail.

Tests:
- Unit: no directive present → allocator returns static-config weights unchanged.
- Unit: directive present with weight=0.5 → allocator returns 0.5 (validator inside allocator).
- Unit: directive expires (valid_until < now) → allocator falls back to static.
- Unit: directive enabled=False → allocator returns weight=0 for that archetype.

Quality gate: `cd strategy-service && bash scripts/quality-gates.sh` green.
```

**Done criterion**: reloader class shipped; 4 unit tests pass; integration test demonstrates round-trip (directive emit
→ reloader receive → allocator return modified weight); QG green.

**Continuous verification**: strategy-service QG; spot-check
`grep -l "StrategyDirectiveReloader" strategy_service/config_reloaders.py` returns 1.

## Phase 6 — trading-agent-service core scaffold (P0, after Phases 1+2+3, ~2 days, layer-7)

**Agent execution prompt**:

```
Read SUB_AGENT_MANDATORY_RULES.md first.
Repo: trading-agent-service. Worktree: .tabs/<N>/trading-agent-service/.

PREREQ: workspace-qg green requires GH_PAT rotation per
plans/active/issues/trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md updated triage.
If credential not yet rotated, run quality-gates.sh LOCALLY and proceed; CI verification deferred to Phase 7.

Task: ship trading_agent_service/ core scaffold — subscribes to upstream streams; emits no-op AllocationDirective.

Files to CREATE:
1. trading_agent_service/core/agent_loop.py — main loop. Subscribes to:
   - FeaturesComputedEvent (feature_group="performance_features")
   - StrategyPnlStreamEvent (direct subscription)
   - Slow features (regime / narrative / ETA) — STUB inputs; subscribe to FeaturesComputedEvent feature_groups by name
     with empty handler today.
   - ML inference + LLM context — STUB inputs (just-log subscribers, no model invocation today).
   Emits: AllocationDirective with source="trading-agent-service-stub" + enabled=True + weight=existing static value
   (i.e. NO-OP: emits the static value as a directive so the reloader path is wired but allocator behaviour is unchanged).

2. trading_agent_service/api/main.py — FastAPI app with make_health_router from UTL + data_freshness callback
   (CLAUDE.md QG STEP 5.62 requirement).

3. trading_agent_service/service_bootstrap.py — ServiceBootstrap invocation
   (CLAUDE.md QG STEP 5.61 requirement). STARTED / STOPPED / FAILED events.

4. trading_agent_service/config_reloaders.py — typed AgentServiceConfig + reloader (CLAUDE.md QG STEP 5.34).

5. trading_agent_service/cli/main.py — `--operation` (allocate-loop) + `--mode` (live/paper) + `--asset-group`
   dispatcher per CLAUDE.md "Service CLIs" convention.

6. tests/unit/test_agent_loop.py — 5 tests:
   - boot + 1 feature event + 1 PnL event → emits AllocationDirective with no-op weight
   - boot + no events → emits no directive (idle)
   - directive emit shape matches AllocationDirective schema
   - subscriber registration covers all 5 input streams (3 STUB + 2 real)
   - kill-switch event halts emission

7. tests/integration/test_directive_roundtrip.py — fake strategy-service StrategyDirectiveReloader subscriber + this
   service emit; verify round-trip.

Quality gate: `cd trading-agent-service && bash scripts/quality-gates.sh` green.

Service-infrastructure compliance check (CLAUDE.md QG STEPs):
- STEP 5.61 ServiceBootstrap ✓
- STEP 5.62 api/main.py + make_health_router ✓
- STEP 5.34 typed config_reloaders ✓
- STEP 5.66 per-VM shard isolation (N/A — agent-service is single-instance)
- STEP 5.69 bucket-name SSOT (use resolve_bucket_name)
```

**Done criterion**: 6 files ship; 7+ tests pass; QG green (local OR CI per Phase 7 ETA).

**Continuous verification**: trading-agent-service workspace-qg green + per-repo QG green. Add trading-agent-service to
deployment-stack restart script for local-dev smoke.

## Phase 6.5 — Backtest-replay infrastructure (P0, after Phase 6, ~1 day, layer-7)

**Why this phase exists**: per operator directive 2026-05-20 "needs to be backtest-able as well i.e. no forward looking
bias on the decision making even historically". The Phase 1 schemas already encode the substrate
(`mode: Literal["live","paper","backtest_continuation"]`, `available_at`, `valid_from`/`valid_until`). This phase wires
the RUNTIME enforcement so deterministic replay actually works.

**Agent execution prompt**:

```
Read SUB_AGENT_MANDATORY_RULES.md first.
Repo: trading-agent-service. Worktree: .tabs/<N>/trading-agent-service/.

Task: ship backtest-replay infrastructure that makes the agent's decisions reproducible from historical state without
forward-looking bias.

Files to CREATE / EXTEND:

1. trading_agent_service/replay/inference_cache.py — write-path cache for every external-call output (Anthropic SDK
   responses, ML inference outputs). Schema mirrors UAC unified_api_contracts/internal/agent_inference_cache.py (added
   in Phase 1 schema addendum below). Keyed by {input_hash, model_id, mode}. In live/paper mode: write-through (call
   real API + persist). In backtest mode: read-from-cache only; raises CacheMissError if input_hash absent.

2. trading_agent_service/replay/directive_log.py — every emitted AllocationDirective gets logged with its full input
   snapshot: {timestamp_emitted, features_consumed (list of feature_id + available_at), pnl_consumed (list of pnl_event
   ids + available_at), inference_cache_keys_used (list), directive_emitted (the AllocationDirective itself)}. Storage:
   parquet append-only to a per-mode bucket (`agent-replay-logs/<mode>/<date>/`).

3. trading_agent_service/cli/main.py — extend the existing --mode flag (live|paper) with a third value: backtest.
   When --mode=backtest, the agent's data-fetch helpers MUST clamp every query to a `--cutoff` timestamp argument.
   Banned in backtest mode: any call that reads data with `available_at > cutoff`. Add a CutoffViolationError raised
   by every data fetcher when violation detected (defense-in-depth — should be unreachable if data layer respects
   available_at correctly).

4. trading_agent_service/replay/cutoff_clamp.py — the shared decorator wrapping every data-fetch helper. Reads
   the current mode from agent context; in backtest mode, asserts `available_at <= cutoff`.

5. UAC ADDENDUM (small extension to Phase 1 schemas):
   - unified_api_contracts/internal/agent_inference_cache.py: `{input_hash, timestamp_called, output_bytes,
     model_id, mode_used, available_at}` — Pydantic schema for the cache contract.

6. tests/unit/test_replay_infrastructure.py — 6 tests:
   - inference_cache write-through in live mode
   - inference_cache miss in backtest mode raises CacheMissError
   - directive_log captures full input snapshot per emission
   - cutoff_clamp in backtest mode raises CutoffViolationError when `available_at > cutoff`
   - cutoff_clamp in live mode is a no-op
   - mode flag rejection: --mode=foo errors clean

7. tests/integration/test_no_leak_gate.py — THE GATE TEST:
   - Run agent over historical period T0..T1 in backtest mode → produces directive_log_backtest + uses cache for
     all inference calls.
   - Run agent over the same period in mock-live mode where each tick is fed sequentially, inference cache
     pre-populated with same outputs → produces directive_log_live.
   - assert directive_log_backtest == directive_log_live (per-tick directive equality).
   - Divergence = leak found. Test FAILS LOUDLY with first divergent tick + the inputs that differed.

Quality gate: `cd trading-agent-service && bash scripts/quality-gates.sh` green INCLUDING the new no-leak gate test.
```

**Done criterion**: 5 files ship in trading-agent-service + 1 UAC schema addendum + 7+ tests pass + the no-leak gate
test passes for the May-23 archetypes (carry_staked_basis, arbitrage_price_dispersion).

**Continuous verification**: no-leak gate test in QG. ANY archetype added later must pass this test before its
directives are consumed by strategy-service in live mode (gate flips in Phase 2 of the post-cutover operational plan).

**Foundation-gate alignment**: this phase is the operational substrate that elevates the agent service from "scaffold
present, no-op default" to "scaffold present + provably leak-free". The gate test enforces that operationality cannot
proceed (Phase 2 post-cutover) until leak-free is proven per archetype.

## Phase 7 — CI hygiene fix (P0, parallel-anytime, ~0.5 days)

**Agent execution prompt**:

```
Read SUB_AGENT_MANDATORY_RULES.md first.

Task: unblock trading-agent-service workspace-qg per
plans/active/issues/trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md.

CONFIRMED ROOT CAUSE: GH_PAT secret on IggyIkenna/trading-agent-service is invalid/expired. Visibility fix already
shipped at unified-trading-pm@c953d778; the underlying credential issue remains.

OPERATOR ACK REQUIRED (per CLAUDE.md "External Data Is Always Available" rule):
1. Operator copies valid GH_PAT value from existing working secret (e.g. mtds repo's GH_PAT).
2. `gh secret set GH_PAT --repo IggyIkenna/trading-agent-service --body "$VALID_FINE_GRAINED_PAT"`
3. Re-trigger: `gh workflow run workspace-qg.yml --repo IggyIkenna/trading-agent-service --ref live-defi-rollout`
4. Verify: `gh run list --branch live-defi-rollout --repo IggyIkenna/trading-agent-service --limit 1` shows ✓.

If operator unavailable at execution time: implementing slot ships Phase 6 with local QG verification + adds CI
re-trigger as DEFERRED-OPERATOR-ACK sub-todo.
```

**Done criterion**: trading-agent-service workspace-qg green on `live-defi-rollout`.

**Continuous verification**: existing per-repo workspace-qg run (cadence: per-commit).

## Phase 8 — Codex SSOT + master/epic/issue plan updates (P0, depends on all prior, ~0.5 days, doc-layer)

**Agent execution prompt**:

```
Read SUB_AGENT_MANDATORY_RULES.md first.
Repo: unified-trading-pm. Worktree: .tabs/<N>/unified-trading-pm/.

Task: apply all manifest entries from
plans/active/issues/_trading_agent_unlock_plan_change_manifest_2026_05_20.md (operator-approved).
Order of application:

1. Master plan changes M1-M6 (master_to_live_defi_2026_05_23.md)
2. Promote-workflow changes PW1-PW2 (promote_workflow_may23_cli_path_2026_05_10.md)
3. Phase-5 features change F1 (phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md)
4. Issue changes Q1-Q2 (issues/trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md)
5. Epic changes E1-E2 (plans/epics/strategy_and_dart_master_2026_05_07.md)
6. Secondary changes SR1 + SA1 + FC1 (strategy_repo_consolidation, strategy_archetype_taxonomy,
   features_repo_consolidation)
7. Per-archetype follow-up sweep (10 plans) — single-line additions
8. Write NEW codex SSOT: codex/04-architecture/trading-agent-service-directive-pipeline.md (see structure below)
9. UPDATE codex/06-coding-standards/config-reloader-pattern.md — add "DirectiveReloader pattern" subsection
10. Run inventory regenerator:
    `python3 unified-trading-pm/scripts/plans/regenerate_active_plan_inventory.py`

NEW codex SSOT structure (codex/04-architecture/trading-agent-service-directive-pipeline.md):
  - § Overview — the closed-loop diagram (from operator brief 2026-05-20)
  - § Data flow — features + PnL streams → agent service → directive → strategy reloader
  - § Schemas — link to UAC strategy_pnl_stream.py + strategy_directives.py
  - § Off-by-default semantics — no-op default + how to flip on post-cutover
  - § Foundation gate ordering — layers 4→5→6→7
  - § Successor plans — list epic §1.7 Phase 10.7 + epic § Allocator service for production logic
  - § Continuous verification — what greens MUST be true at any point in time

Quality gate: PM repo doesn't have QG; verify via:
- `bash scripts/quality-gates-config-lint.sh` (if exists)
- `git diff --check` for whitespace
- inventory regenerator runs without error
```

**Done criterion**: all 7+1+1+1 plan-edit changes applied + codex SSOT shipped + inventory regenerated + master plan
shows trading-agent-service in new Tier-1 sub-tier; commit message
`docs(plans): apply trading-agent-unlock manifest M1-M6/PW1-PW2/F1/Q1-Q2/E1-E2 — PM@<sha>`.

**Continuous verification**: daily inventory-regenerator catches drift.

## Success criteria (per phase — Citadel-Grade §5 + Continuous-verification)

| Phase | Cutover criterion                                                                                                                                                                                                                                                                                 | Continuous verification                                                                        | Last verified     |
| ----- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ----------------- |
| 1     | ✅ UAC `StrategyPnlStreamEvent` + `ArchetypeAllocationDirective` ship + 12 unit tests pass — uac@82b7ad55. Note: named `ArchetypeAllocationDirective` (not `AllocationDirective`) to avoid collision with existing `architecture_v2.AllocationDirective` (full post-cutover multi-client schema). | UAC QG (per-commit) + grep `from unified_api_contracts.internal import StrategyPnlStreamEvent` | 2026-05-20 slot-3 |
| 2     | ✅ strategy-service emits `StrategyPnlStreamEvent` for carry + APD; 6 tests pass — strategy-service@a0f87c66. UTL STRATEGY_PNL_STREAM constant: utl@de5ca0a0. Also: `_n_instructions_emitted` counter in BaseArchetypeEngineV2 + 4 additional unit tests — strategy-service@838a8b2d (slot-5).    | strategy-service QG + grep callsites in v2/ handlers (≥2)                                      | 2026-05-20 slot-5 |
| 3     | ✅ features-service `performance_features/` subdomain ships; 5 unit tests pass — uac@72395499 + features@2a7af305                                                                                                                                                                                 | features-service QG + manifest row exists for lead-pair date range                             | 2026-05-20 slot-3 |
| 4     | ✅ UAC facades export models; 2 integration tests pass — uac@2bdc0f07 (root + internal facade; 19 tests total)                                                                                                                                                                                    | UAC QG                                                                                         | 2026-05-20 slot-3 |
| 5     | ✅ strategy-service `StrategyDirectiveReloader` ships; no-op default + 4 tests pass; weight_with_directive() wired into allocator — strategy@afd17fe9                                                                                                                                             | strategy-service QG + grep StrategyDirectiveReloader in config_reloaders.py                    | 2026-05-20 slot-3 |
| 6     | ✅ trading-agent-service AllocationDirectiveLoop scaffold ships; ServiceBootstrap+Health already present; 5 tests pass — trading-agent@119fa74                                                                                                                                                    | trading-agent-service QG (local OR CI per Phase 7)                                             | 2026-05-20 slot-3 |
| 7     | trading-agent-service workspace-qg green on live-defi-rollout                                                                                                                                                                                                                                     | per-repo workspace-qg (per-commit)                                                             | PENDING           |
| 8     | All manifest entries applied; codex SSOT shipped; inventory regenerated                                                                                                                                                                                                                           | daily inventory-regenerator + plan-vs-codex doc-drift audit                                    | PENDING           |

## Operator-attention list (decisions needed)

1. **GH_PAT rotation for trading-agent-service** (P0) — blocks Phase 7 CI verification. Operator copies valid token
   value from existing working repo (e.g. mtds) and runs:
   `gh secret set GH_PAT --repo IggyIkenna/trading-agent-service --body "$VALID_FINE_GRAINED_PAT"`.
2. **Slot allocation** — new plan has no assigned slot in current work-split. Operator: assign to existing slot
   (recommend slot with capacity post-mega-audit) OR allow slot-1-main to spawn sub-agents.
3. **Confirm "off-by-default" semantics** — trading-agent-service emits `AllocationDirective` with weight = static value
   (i.e. NO change to allocator behaviour at runtime). Operator confirms this is the intent vs. "service exists but
   emits nothing".
4. **`param_overrides: dict[str, Any]` in AllocationDirective schema** — operator confirms `Any` value-type is
   acceptable for May-23 (closed-set future-restrict post-cutover) OR requests specific Pydantic discriminated union
   now.

## Temporary states + their canonical follow-up plans

- **No-op directive emission** (Phase 6): trading-agent-service emits static-value directive. Successor:
  `plans/epics/strategy_and_dart_master_2026_05_07.md` §1.7 Phase 10.7 (post-cutover) — production allocator logic with
  8 archetype engines.
- **STUB ML/LLM input subscribers** (Phase 6): the 3 stub-input subscribers (regime, narrative, ETA) and the ML+LLM
  input wires are placeholder log-only handlers. Successor: epic §1.7 Phase 10.7 post-cutover + ML pipeline integration
  plan (currently `plans/active/ml_repo_consolidation_2026_05_19.md` and successors).
- **`performance_features` passthrough** (Phase 3): no derivation today; raw PnL fields pass through unchanged.
  Successor: epic § Allocator service P1 post-cutover — real derivations (rolling sharpe, drawdown, attribution-by-leg).
- **Per-archetype PnL emission limited to 2 archetypes** (Phase 2): only carry_staked_basis + arbitrage_price_dispersion
  emit. Successor: `pvl-p18b-archetype-paper-runnable-matrix` post-cutover — populate emission per remaining 51
  archetypes as their continuous-paper infrastructure lands.

## Codex SSOT updates (per "Post-Plan-Phase Codex Audit" HARD RULE)

- **NEW**: `codex/04-architecture/trading-agent-service-directive-pipeline.md` (Phase 8)
- **UPDATE**: `codex/06-coding-standards/config-reloader-pattern.md` — add DirectiveReloader subsection (Phase 8)
- **UPDATE**: master plan Group-C continuous-verification matrix (Phase 8 via change M3+M6)
- **UPDATE**: `CLAUDE.md` — NO — workspace-contract changes minimal; the new SSOT carries the new contract and
  trading-agent-service is now referenced from master plan Tier-1 section. (Per CLAUDE.md size budget: skip
  workspace-contract-level mention unless reviewer flags.)
