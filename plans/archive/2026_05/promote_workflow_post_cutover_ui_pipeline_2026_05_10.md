---
doc_type: plan
title: Promote Workflow — Post-cutover UI pipeline + state-machine consolidation
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [alerting-service, batch-live-reconciliation-service, deployment-api, deployment-ui, e2e-testing, execution-service]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/active/promote_workflow_may23_cli_path_2026_05_10.md,
    plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md,
    plans/archive/client_reporting_pnl_attribution_mvp_2026_05_10.md,
    plans/archive/risk_simulations_limits_alerting_2026_05_10.md,
    plans/epics/strategy_and_dart_master_SUPERSEDED_2026_05_21.md,
  ]
created: 2026-05-10
archived: 2026-05-23
last_updated: 2026-05-23
estimate_class: infra
estimate_baseline_ai_days: 25
estimate_calibrated_ai_days: 20.0
estimate_calibration_note: "No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from
  filename (infra, multiplier 0.8×).

  Owner agent: fill baseline + multiply × 0.8 per /codex/08-workflows/estimation-calibration.md. Refine class if
  dominant work-class differs.

  "
parent_epic: dart_and_promote_master
assigned_vm: vm-operator-ops
priority: P2
---

## Deferred work — migrated to:

All 64 DEFERRED-OPERATOR-DECISION items represent post-cutover implementation scope. Migrated in 7 delivery groups to
`plans/epics/dart_and_promote_master.md` § P3 (Groups A-G):

- A: StrategyMaturityPhase enum + lifecycle events
- B: CandidateManifest enrichment + Firestore + BacktestRunManifest + ranking
- C: Promote UI endpoints + event-stream convergence
- D: DART all-archetype visualization
- E: OperationalMode refactor (pvl-p17a-d)
- F: Strategy drift watchdog + backtest cron VMs
- G: Codex + CLAUDE.md post-cutover update Full 64-item spec preserved in this archived plan for reference. Archiving
  2026-05-23.

# Promote Workflow — Post-cutover UI pipeline + state-machine consolidation

> **🔵 SLOT-7 AUDIT 2026-05-18**: All items in this plan require backend integration (Firestore
> `MinimalCandidateManifest`, promote-api endpoint, DART `ManualTradeGateDialog` wiring) that is explicitly blocked
> until after May-23 cutover per CLAUDE.md promote-workflow-architecture SSOT. Zero pre-stageable UI items exist without
> the backend contract. Status = DEFERRED-POST-CUTOVER (named successor = this plan itself). No code changes until
> May-23 cutover lands. — deployment-ui@e9e90d9 / PM@26336f55.

> **🟢 OPERATOR-PICKS-TRACK AT CUTOVER — RATIFIED 2026-05-10 cross-plan audit Q12.** Both CLI track + UI track ship by
> May-23 per [`promote_workflow_may23_cli_path_2026_05_10.md`](promote_workflow_may23_cli_path_2026_05_10.md). At
> cutover boundary, operator picks ONE track per run. This plan extends the UI track post-cutover (target 2026-07-04)
> into the canonical path; CLI track persists as operational floor for ops/runbooks (NOT deprecated by this plan). Phase
> 9 here (full pre-flight pipeline) extends May-23 Phase U3 into the full state-machine-driven pre-flight; semantically
> a superset, not a replacement of the minimal version.

## Why this plan exists

The May-23 cutover plan
([`promote_workflow_may23_cli_path_2026_05_10.md`](promote_workflow_may23_cli_path_2026_05_10.md)) ships dual-track for
May-23: CLI primary safety-net + **minimal-but-real UI promote pipeline** (Promote button → backend →
MinimalCandidateManifest → DART manual-trade gate → paper/live VM auto-launch). The minimal UI ships as Phases U1-U6 of
the May-23 plan. **This plan EXTENDS the minimal UI into the full UI workflow** + ships everything else DEFERRED from
May-23: heavy state-machine consolidation, full pinned-shas CandidateManifest, cross-service auto-registration, ranking
surface, drift detection, full per-archetype config schemas, operational modes consolidation. Target completion
2026-07-04 (~6 weeks post-cutover).

**Scope** (the May-23 plan's "Temporary states + canonical follow-up plans" section enumerates these):

1. State machine consolidation (4 competing UAC SSOTs → 1 canonical).
2. **EXTENDS May-23 Phase U1**: full `CandidateManifest` UAC type with pinned shas + model refs + features manifest
   version + venue keys ref + chain RPC URLs ref (May-23 plan ships `MinimalCandidateManifest` with placeholder
   `Optional` fields; this plan populates them).
3. Event taxonomy consolidation (UTL bare-string strategy events → UAC `LifecycleEventType`; add missing
   promote/candidate/lifecycle-pause events).
4. Per-archetype Pydantic config schemas (5 of 53 → all 53).
5. Drift detection cron + alerting.
6. Cross-service auto-registration on promote (risk / alerting / position-balance / pnl-attribution).
7. Continuous backtest cron.
8. Backtest persistence + ranking surface (`BacktestResultWriter` + lift `GroupBMetrics` to UAC + `RankedCandidate` UAC
   type + `rank_candidates()` helper + ranking API endpoint).
9. **EXTENDS May-23 Phases U3+U4**: full pre-flight pipeline (May-23 ships minimal pre-flight gates; this plan adds
   per-deployment alerting auto-rule generation + auto-register risk profile + cross-service handlers).
10. **EXTENDS May-23 Phases U5+U6**: full DART experience (May-23 ships pvl-p23a 3-way + pvl-p23c manual-trade gate for
    the lead pair; this plan extends to all archetypes + advanced features like multi-archetype comparison + signal
    explainability + per-trade audit drill-down).
11. Operational modes consolidation (`pvl-p17a-d`).
12. CEFFU custody non-stub (if Binance institutional flow opens; otherwise stays DEFERRED).

Per CLAUDE.md HARD RULE _"Plans Run To Actual Completion"_: every phase has Full-execution criterion. Per
_"Citadel-Grade Planning Standards"_: pre-audit + phased DAG + parallelization + success criteria + downstream consumer
updates + SSOT discipline.

## Pre-audit

The audit (Question doc `## Audit findings`) IS the pre-audit. Files this plan touches enumerated in each phase below.
Workspace-grep audits per Citadel-Grade § 6 extension required for: lifecycle enum migrations (Phase 1), event taxonomy
(Phase 3), candidate-config schema (Phase 4).

## Execution DAG

```
Phase 1 (state machine consolidation) ──┐
                                         │
Phase 2 (CandidateManifest UAC)       ──┤── Phases 1+2+3 are SEQUENTIAL DEPENDENCIES for everything else
Phase 3 (event taxonomy)              ──┤
                                         │
Phase 4 (per-archetype config schemas)──┤
Phase 8 (backtest persistence+ranking)──┤
                                         │
Phase 5 (drift detection cron)         ──┤── PARALLEL once Phases 1-3 land
Phase 7 (continuous backtest cron)     ──┤
Phase 11 (operational modes)            ──┤
                                         │
Phase 6 (cross-service auto-register)  ──┤── needs Phases 1+3 (events) for trigger
Phase 9 (promote API backend)           ──┤── needs Phases 1+2+3+8 for full pipeline
Phase 10 (DART UI 3-way + gate)         ──┘── needs Phase 9 backend
                                         │
Phase 12 (codex SSOT batch)             ── runs alongside, codex per phase per Post-Plan-Phase Codex Audit HARD RULE
```

## Phase 1 — State machine consolidation (P0, ~3-5d, SEQUENTIAL — gates 6+9)

**Why first**: 4 competing UAC SSOTs (`StrategyLifecycleStage` legacy 7-state + `StrategyMaturityPhase` canonical
10-state + `StrategyMaturity` v2 8-state + `VersionStatus` gov 6-state) violate the workspace "no double SSOT" rule four
ways. Consumers (strategy-service uses TWO simultaneously) drift; reasoning across the workspace gets impossible.

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Pick canonical `StrategyMaturityPhase`** (10-state, has
      `is_valid_maturity_transition()` validator, codex-blessed, used by most production code paths).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Workspace-grep audit** per Citadel-Grade § 6 extension — every
      consumer of `StrategyLifecycleStage` / `StrategyMaturity` listed with file:line in plan body.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Migrate
      `strategy-service/strategy_service/availability/store.py:24-26`** from `StrategyMaturity` (v2 8-state) to
      `StrategyMaturityPhase` (canonical 10-state) — atomic transition, all consumers in one commit.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Migrate any other consumer** found in the workspace-grep audit.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Deprecate `StrategyLifecycleStage`** — mark `@deprecated` in source +
      write migration script per CLAUDE.md _"Manifest migration, NOT fallback"_; remove the legacy enum after consumer
      sweep + 1 release cycle.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Deprecate `StrategyMaturity`** (v2 8-state) — same shape.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Add `STRATEGY_LIVE_PAUSED` + `STRATEGY_LIFECYCLE_DEMOTED` event
      types** to UAC `LifecycleEventType` (currently referenced in codex but undefined).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Synchronous PATCH-emit `STRATEGY_LIFECYCLE_CHANGED`** on
      [`unified-trading-api/.../routes/registry.py:170-180`](../../../unified-trading-api/unified_trading_api/routes/registry.py#L170-L180)
      — currently fires only via 5-min reloader poll; kill-switch-grade governance changes can't wait 5 minutes.
      Endpoint should `log_event` directly AND let reloader pick up later for stragglers.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Mirror `phase_history` to `audit_log` collection** — codex
      `strategy-lifecycle-maturity.md:255-256` claims this happens; code doesn't. Either fix the code or strike the
      codex line.

**Phase 1 codex deliverables** (ride with this phase per Post-Plan-Phase Codex Audit):

- NEW `/codex/04-architecture/strategy-lifecycle-state-machine.md` — reconciled canonical state machine.
- UPDATE `/codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md` — fix 4 codex/code drift lines (245, 46,
  46, 256).
- UPDATE CLAUDE.md — add **"Strategy Lifecycle State Machine SSOT"** key rule pointing at the new codex doc + the
  canonical enum.

**Phase 1 done definition**:

- ✅ `StrategyMaturityPhase` is single SSOT in code.
- ✅ Legacy + v2 enums marked deprecated.
- ✅ All consumers migrated.
- ✅ 2 new event types in UAC.
- ✅ PATCH endpoint emits synchronously.
- ✅ `audit_log` mirror works.
- ✅ Codex docs shipped.

**Full-execution criterion**:

- **What ran**: workspace QG green on UAC + strategy-service + unified-trading-api after migrations; PATCH endpoint
  smoke-test verifies synchronous event emission via gcloud event-stream tail.
- **Verification**: `rg "StrategyMaturity\b" --type py --glob '!.venv*' --glob '!build'` returns 0 active hits (only
  deprecated-shim + tests); `rg "StrategyLifecycleStage" --type py --glob '!.venv*' --glob '!build'` returns 0 active
  hits; `gcloud storage cat gs://${PID}-events/events/unified-trading-api/<today>/.../event.jsonl` shows
  `STRATEGY_LIFECYCLE_CHANGED` within 1s of PATCH.

## Phase 2 — Full `CandidateManifest` enrichment (P0, ~3-5d, SEQUENTIAL after Phase 1)

**Why**: Audit Block C5 — biggest single gap. Promotion to live without a frozen all-shas manifest = no rollback target,
no incident forensics, no reproducibility. `StrategyVersion` only stores `config_diff` deltas, not full pinned state.
May-23 plan Phase U1 ships `MinimalCandidateManifest` with placeholder `Optional` fields for pinned shas / model refs /
features manifest version / chain RPC pins. **This phase populates those fields** and adds the rollback runbook.

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **EXTEND `MinimalCandidateManifest` to full `CandidateManifest`**
      (rename in place; backward-compatible because all new fields are `Optional` with `default=None` already from
      May-23). At `unified_api_contracts/internal/domain/strategy_service/candidate_manifest.py`. Captures (full set):
  - `manifest_id: str` (UUID).
  - `strategy_instance_id: str`.
  - `version_id: str` (links to `StrategyVersion`).
  - `archetype: StrategyArchetype`.
  - `pinned_shas: dict[str, str]` (workspace-manifest snapshot — UAC, UTL, strategy-service, execution-service,
    features-service (onchain family), instruments-service, etc.).
  - `model_refs: list[ModelRef]` (model_id, model_version, training_run_id per ML prediction consumed).
  - `features_manifest_version: str` (per features-service (onchain family) feature_group versions).
  - `venue_keys_ref: list[SecretManagerPath]` (Secret Manager paths for venue keys; resolved at boot but PINNED at
    promote-time so future changes don't silently affect the live deployment).
  - `chain_rpc_pins: dict[str, str]` (chain_name → RPC URL snapshot from `CHAIN_RPC_TEMPLATES`).
  - `wallet_ref: WalletRef` (custody endpoint + wallet address).
  - `execution_mode: OperationalMode` (paper/live/etc).
  - `kill_switch_config_snapshot: dict[str, Any]` (kill-switch YAML snapshot).
  - `created_at: datetime`.
  - `created_by: str`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Firestore `strategy_candidate_manifests` collection** for persistence.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Admin endpoint** `POST /strategy/{instance_id}/candidate-manifest`
      writes the manifest + emits `STRATEGY_PROMOTED_TO_CANDIDATE` event (event type added in Phase 3).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **PATCH endpoint extension**: when maturity transition crosses into
      `LIVE_EARLY`, the endpoint reads the most recent `CandidateManifest` for the version_id + emits
      `STRATEGY_PROMOTED_TO_LIVE` with `manifest_id`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Rollback runbook**: given `manifest_id`, restore the captured shas +
      restart the strategy. `e2e-testing/scripts/defi/rollback-from-manifest.sh`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **`BacktestRunManifest`** sibling type — captures pinned state at
      backtest-time so the `backtest_series_ref` is no longer a free-form string; it's a `manifest_id` pointer.

**Phase 2 codex deliverables**:

- NEW `/codex/04-architecture/live-deployment-manifest.md` — `CandidateManifest` shape + capture point + rollback
  recipe.
- NEW `/codex/09-strategy/architecture-v2/cross-cutting/backtest-run-manifest.md` — `BacktestRunManifest` shape +
  reproducibility recipe.

**Phase 2 done definition**:

- ✅ Both UAC types exist with all fields.
- ✅ Firestore collection live.
- ✅ Admin + PATCH endpoints write/read manifests.
- ✅ Rollback runbook tested on a paper-mode candidate.
- ✅ Codex docs shipped.

**Full-execution criterion**:

- **What ran**: end-to-end test — promote a paper candidate, verify Firestore record, fire rollback runbook, verify
  strategy restarts at pinned shas.
- **Verification**: Firestore record present; rollback restores expected state; integration test passes.

## Phase 3 — Event taxonomy consolidation (P0, ~2-3d, SEQUENTIAL after Phase 1)

**Why**: Audit Block F2 — UTL has 7 bare-string strategy event constants NOT in UAC `LifecycleEventType` enum.
Promote/candidate/lifecycle-pause events the question doc names DON'T exist anywhere.

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Fold UTL strategy event constants** at
      [`unified-trading-library/.../events/event_types.py:387-412`](../../../unified-trading-library/unified_trading_library/events/event_types.py#L387-L412)
      into UAC `LifecycleEventType` StrEnum:
  - `STRATEGY_AVAILABILITY_CHANGED`
  - `STRATEGY_LOCKED`
  - `STRATEGY_UNLOCKED`
  - `STRATEGY_MATURITY_ADVANCED`
  - `STRATEGY_MATURITY_REGRESSED`
  - `STRATEGY_LIFECYCLE_CHANGED`
  - `STRATEGY_LIFECYCLE_SEEDED`
  - UTL keeps re-exports for backward compatibility OR deletes constants + imports UAC enum members directly (cleaner —
    pick this).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Add missing event types** to UAC `LifecycleEventType`:
  - `STRATEGY_PROMOTED_TO_CANDIDATE` (with `manifest_id` payload field)
  - `STRATEGY_PROMOTED_TO_PAPER` (with `manifest_id` + `paper_deployment_vm_name`)
  - `STRATEGY_PROMOTED_TO_LIVE` (with `manifest_id` + `live_deployment_vm_name`)
  - `STRATEGY_PAPER_FAILED` (with `failure_reason` + `paper_metrics_snapshot`)
  - `STRATEGY_LIVE_PAUSED` (with `pause_reason` + `paused_by`)
  - `STRATEGY_LIVE_RETIRED` (with `retire_reason`)
  - `STRATEGY_CANDIDATE_DRIFT` (Phase 5 — drift detection)
  - `LIVE_DEPLOYMENT_STARTED` / `LIVE_DEPLOYMENT_STOPPED` (live-deployment scoped events distinct from generic
    ServiceBootstrap STARTED/STOPPED).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Update consumers** — alerting-service, position-balance-monitor,
      risk-and-exposure subscribe to relevant new events.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **GCS partition `events/strategy-lifecycle/`** — separate from
      `events/strategy-service/` so lifecycle audit is queryable independently. Retention policy aligned with regulatory
      (≥7y for promote/live events).

**Phase 3 codex deliverables**:

- UPDATE `/codex/03-observability/lifecycle-events.md` — extend canonical event taxonomy with strategy-lifecycle event
  types + cross-service event-consumer matrix.

**Phase 3 done definition**:

- ✅ UTL strategy events folded into UAC.
- ✅ 8 new event types in UAC `LifecycleEventType`.
- ✅ All listed consumers subscribed.
- ✅ `events/strategy-lifecycle/` partition live with retention.
- ✅ Codex updated.

**Full-execution criterion**: workspace QG green; integration test fires each new event type and verifies subscriber
consumption.

## Phase 4 — Per-archetype Pydantic config schemas (P1, ~5-8d, PARALLEL with 5+7+8+11)

**Why**: Audit Block G2 — `ARCHETYPE_CONFIG_SEED` covers only 5 of 53 archetypes; grid-swept dimensions live in loose
`dict[str, str]` (`tested_params`).

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **Lift the 2yr-grid script's flat schema to UAC** —
      `ArchetypeStrategyParams` per archetype with full parameter space (slippage_cap_bps, funding_spread_threshold_bps,
      target_leverage, etc.).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **`ARCHETYPE_PARAMS_SEED`** covering all 53 archetypes (or AS NEEDED if
      archetypes are added incrementally).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **`validate_config_for_archetype(archetype, config)` helper** in UAC —
      used by `BacktestResultWriter` (Phase 8) + Promote API backend (Phase 9) as the canonical validation.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **Migrate sports-specific** `ArbitrageStrategyConfig` BaseModel to fit
      the generalised pattern.

**Phase 4 codex deliverables**:

- NEW `/codex/09-strategy/architecture-v2/cross-cutting/archetype-strategy-params.md` — per-archetype parameter schema
  SSOT.

**Phase 4 done definition**: 53 archetypes have validated Pydantic schemas; loose dicts gone.

## Phase 5 — Drift detection cron (P1, ~2-3d, PARALLEL after Phases 1-3)

**Why**: Audit Block G3 — no drift detection between candidate creation and live deployment.

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **NEW cron VM `strategy-drift-watchdog-{ts}`** per VM Naming Convention.
  - Walks ROLLED_OUT `StrategyVersion` rows; reads each version's `CandidateManifest` (Phase 2); checks pinned shas vs
    current main per repo.
  - Checks features schema for X has changed (per features-\* services manifest version drift).
  - Checks ML model registry for pinned model_refs (model still served? deprecated?).
  - Emits `STRATEGY_CANDIDATE_DRIFT` event (Phase 3) with drift diff payload.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **Register `strategy-drift-` prefix** in `VM_PREFIX_TO_BUCKET`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **Bounce vm-zombie-watchdog VM** per Phase 1 of May-23 cutover plan
      recipe.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **Alerting rule** wires `STRATEGY_CANDIDATE_DRIFT` to operator paging
      (Telegram / PagerDuty); demote / re-validate stale candidates.

**Phase 5 codex deliverables**:

- NEW `/codex/09-strategy/architecture-v2/cross-cutting/strategy-config-drift-detection.md` — drift checker semantics +
  cron wiring + alerting.

**Phase 5 done definition**: cron VM running daily; drift event fires on injected drift; alert reaches operator within
SLA.

## Phase 6 — Cross-service auto-registration on promote (P1, ~5-8d, SEQUENTIAL after Phases 1+3)

**Why**: Audit Block H1-H3 — risk / alerting / position-balance currently require operator-driven registration via
separate API calls. Manual + error-prone.

### 6.A — Risk-and-exposure auto-register

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **risk-and-exposure subscriber** — when `STRATEGY_PROMOTED_TO_LIVE`
      fires, auto-create per-strategy `RiskLimits` from `CandidateManifest` (capital allocation, max drawdown, position
      limits, exposure caps derived from kill_switch_config_snapshot + archetype params).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **`POST /risk/strategy-status` extension** to accept `strategy_id` +
      persist `StrategyRiskProfile` to Firestore (currently per-call only).

### 6.B — Alerting per-deployment auto-rule generation

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **alerting-service subscriber** — on `STRATEGY_PROMOTED_TO_LIVE`,
      generate per-deployment alert rules from `CandidateManifest` (drawdown breach, position deviation, fill latency,
      venue API errors). Rules stored in `LIVE_ALERT_RULES_DYNAMIC` registry separate from static `LIVE_ALERT_RULES`.

### 6.C — Position-balance-monitor registration

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **PBMS register endpoint** — `POST /accounts/register` accepts
      `(account_id, client_id, strategy_id, venue, instrument)` so accounts are pre-registered, not discovered from
      event stream. Single-tenant per CLIENT_ID env var preserved as boot constraint.

### 6.D — PnL-attribution `version_id` extension

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **Extend pnl-attribution schema** with `version_id` column to
      distinguish v2.0 from v2.1 of carry_staked_basis (sister to deployment_id concept; uses `version_id` from
      `StrategyVersion` per Audit-Tab-5 H5).

**Phase 6 codex deliverables**:

- NEW `/codex/04-architecture/cross-service-promote-handlers.md` — every service that subscribes to lifecycle events +
  what registration handler fires.
- UPDATE `/codex/04-architecture/interface-credential-convention.md` — extend with auto-register patterns.

**Phase 6 done definition**: end-to-end promote-to-live test fires events, all 4 services auto-register, no operator
manual API calls needed.

## Phase 7 — Continuous backtest cron (P1, ~2d, PARALLEL after Phase 8)

**Why**: Audit Block A6 — no cron VM, no GHA workflow re-runs backtests nightly. Master plan continuous-verification
matrix has F17/F18 with `Last verified: NEVER`.

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **NEW cron VM `strategy-backtest-cron-{ts}`** per VM Naming Convention.
      Runs `run_2yr_config_grid_backtest.py` nightly per archetype + records into manifest.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **Register `strategy-backtest-` prefix** in `VM_PREFIX_TO_BUCKET`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **Master plan continuous-verification matrix** — fill F17/F18
      `Continuous Verification` column with the new cron.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **Alerting** — drift event from Phase 5 + new backtest score >X variance
      from prior baseline → alert.

**Phase 7 done definition**: cron running daily; manifest rows present; matrix updated.

## Phase 8 — Backtest persistence + ranking surface (P0, ~5-8d, SEQUENTIAL after Phase 2)

**Why**: Audit Block A1+A3 — backtest results don't persist; no ranking surface. Combined with Phase 2
`BacktestRunManifest`, this closes Block A.

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **NEW UTL `BacktestResultWriter`** helper that:
  - Writes `DeployableConfigCandidate` outputs to canonical PATH_REGISTRY path.
  - Calls `record_captured` with proper manifest row (capture_status taxonomy applies — backtest is just another shard).
  - Validates `GroupBMetrics` schema on output rows (4-pillar gate per CLAUDE.md "Cluster validation MANDATORY at
    `record_captured`").
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Lift `GroupBMetrics` to UAC** at
      `unified_api_contracts/internal/domain/strategy_service/metrics.py` (currently lives only in strategy-service
      source — violates Schema provenance QG rule).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Reconcile 2yr-grid script's flat schema** with `GroupBMetrics` — pick
      one canonical, migrate the other (per CLAUDE.md "No double SSOT in data-saving methodology").
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Per-asset-group score-schema extensions** — sports CLV, DeFi gas-cost
      / IL attribution, LST-yield-vs-perp-funding component breakdown.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **NEW UAC `RankedCandidate`** type — wraps `BacktestRunManifest` + score
      vector + rank + slicing axes (archetype, asset_group, strategy_family, venue_set_variant).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **`rank_candidates(archetype, top_k, metric)` helper** in UTL.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **API endpoint**
      `GET /strategy/{archetype}/candidates?rank_by=sharpe&top=10` in unified-trading-api.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **UI page** in unified-trading-system-ui — ranked board view, real-data
      wiring (replaces mock fixtures).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **`shadow_within_10pct_of_champion` lifecycle gate** — populate the
      champion store; the gate currently references a champion that doesn't exist anywhere in code.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Strategy-service `engine/strategies/v2/registry.py:73-117`** — Phase
      5/11 promised work: persist `ConfigRegistry` to Firestore (kill the in-memory dict).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **`PaperComparisonTracker` Firestore persistence** — currently lost on
      restart.

**Phase 8 codex deliverables**:

- NEW `/codex/09-strategy/architecture-v2/cross-cutting/backtest-persistence-and-ranking.md` — single SSOT for path /
  manifest schema / score schema / ranking semantics / promotion gates.
- UPDATE `/codex/05-infrastructure/path-registry.md` — pin canonical `backtest_results/` template, kill legacy reader
  path.

**Phase 8 done definition**:

- ✅ `BacktestResultWriter` shipped; all backtest runs land in canonical PATH_REGISTRY path with manifest rows.
- ✅ `GroupBMetrics` in UAC; 2 schemas reconciled.
- ✅ Per-asset-group sub-schemas live.
- ✅ `RankedCandidate` UAC type + helper + endpoint + UI page.
- ✅ Champion store populated; lifecycle gate works.
- ✅ Firestore persistence for `ConfigRegistry` + `PaperComparisonTracker`.

**Full-execution criterion**:

- **What ran**: workspace QG green; integration test runs backtest → manifest row present → ranking endpoint returns
  top-10 → UI page renders.
- **Verification**: GCS path + manifest row + endpoint response + UI screenshot.

## Phase 9 — Full pre-flight pipeline + cross-service handlers (P0, ~5-8d, SEQUENTIAL after Phases 1+2+3+6+8)

**Why**: Audit Block B3 + E2 — May-23 Phase U3 ships `POST /promote/{strategy_id}/{manifest_id}` endpoint with **minimal
pre-flight** (Copper sandbox / venue keys / alerting / kill-switch / recon — gates against existing services). **This
phase ships the full pre-flight pipeline** + cross-service handlers (Phase 6 sibling): per-deployment alerting auto-rule
generation + auto-register risk profile + position-balance-monitor account registration + pnl-attribution version_id
wiring all triggered from the promote endpoint.

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Backend `POST /promote/{strategy_id}/{run_id}` endpoint** in
      `deployment-api/deployment_api/services/promote.py` (NEW file).
  - Body: `{target_status: StrategyMaturityPhase, promoter: str, reason: str, candidate_manifest_id?: str}`.
  - Returns 202 Accepted + `workflow_id` for async (recommended) OR 200 OK with new state for sync (if pre-flight passes
    synchronously).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Backend `POST /promote-to-live/{strategy_id}/{candidate_manifest_id}`
      endpoint** — pre-flight checks:
  - Custody connected (Copper sandbox sign-test passes).
  - All venue keys present in Secret Manager.
  - Alerting paging targets configured.
  - Kill-switch armed (kill_switch_config_snapshot from `CandidateManifest` matches deployed config).
  - Risk limits set (per-strategy `RiskLimits` exists from Phase 6.A auto-register).
  - Recon green for last 24h (from `batch-live-reconciliation-service` Phase 5.A of May-23 plan).
  - Fail-loud if any gate fails; emit `STRATEGY_PROMOTE_TO_LIVE_REJECTED` event with failed gates.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Wire Promote UI's `useRecordPromoteWorkflow()` callback** to the new
      backend (replaces React in-memory context).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **UI shows optimistic state then converges via event-stream
      subscription** to lifecycle events (Phase 3).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Auth/authz** — Firebase custom claim `execution-full` gates
      `/promote-to-live`; per-archetype claims for finer-grained authz post-Tier-3.

**Phase 9 codex deliverables**:

- NEW `/codex/14-customer-journeys/promote-pipeline-backend.md` — `/promote-to-live` API + pre-flight checks codified.
- NEW `/codex/04-architecture/promote-workflow-architecture.md` (UI section — May-23 plan ships the operator-CLI
  section).

**Phase 9 done definition**: Promote UI button click hits real backend; pre-flight enforced; events fire; UI converges;
integration test green.

## Phase 10 — Full DART experience extension (P0, ~5-8d, SEQUENTIAL after Phase 9)

**Why**: Audit Block E1 — DART manual-trade gate is master plan G23 + line 1292 todo. May-23 plan Phases U2 (`pvl-p23b`
mode-data API) + U5 (`pvl-p23a` 3-way visualization for lead pair) + U6 (`pvl-p23c` per-trade manual-trade gate UI) ship
the cutover-blocker subset. **This phase extends to all archetypes + advanced operator features.**

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **DART 3-way visualization extends to all archetypes** (May-23 ships
      lead pair only).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **DART signal explainability** — drill-down into per-feature
      contribution to a signal (multi-archetype comparison view).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **DART per-trade audit drill-down** — operator can click any executed
      trade + see full lineage (signal → instruction → execution → fill).
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Per-strategy pause / kill-switch UI buttons** wired to backend
      `/pause` + kill-switch bus.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **`/retire` endpoint + UI button** — retires strategy gracefully; emits
      `STRATEGY_LIVE_RETIRED`.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Multi-archetype DART comparison** — side-by-side per archetype P&L +
      fills + risk metrics in one canvas (extends pvl-p23a single-archetype shape).

**Phase 10 codex deliverables**:

- NEW `/codex/14-customer-journeys/dart/mode-toggle.md` — DART 3-way + manual-trade gate flow.
- NEW `/codex/05-infrastructure/live-deployment-monitoring.md` (master plan line 146 work-stream B doc).

**Phase 10 done definition**: DART supports 3-way visualization; per-trade gate works for first 3d of any new
deployment; pause/retire buttons live.

## Phase 11 — Operational modes consolidation (`pvl-p17a-d`) (P1, ~3-5d, PARALLEL with 4+5+7+8)

**Why**: Audit Block A2 + paper_vs_live sibling doc — `paper_trade: bool` in execution-service + `_PAPER_VENUE_KEYS`
string-set in sports_execution + 3 competing surfaces violate "no double SSOT".

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **`pvl-p17a` UAC `OperationalMode` 4-cell
      `ExecutionTarget × ExecutionTrigger` enum** — canonical mode SSOT.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **`pvl-p17b`** delete `paper_trade: bool` from
      [`execution-service/execution_service/service_config.py:563-567`](../../../execution-service/execution_service/service_config.py#L563-L567);
      replace with `OperationalMode` checks.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **`pvl-p17c`** delete `_PAPER_VENUE_KEYS` from
      [`execution-service/execution_service/sports_execution/routing.py:16-25`](../../../execution-service/execution_service/sports_execution/routing.py#L16-L25);
      replace with `OperationalMode` checks.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P1. **`pvl-p17d`** propagate `OperationalMode` through every adapter / venue
      / connector — workspace-grep audit per Citadel-Grade § 6.

**Phase 11 codex deliverables**:

- NEW `/codex/04-architecture/operational-modes.md` — 4-cell UAC SSOT.
- NEW `/codex/04-architecture/paper-vs-live-execution-seam.md` — execution-service mode dispatch.
- NEW `/codex/05-infrastructure/per-venue-paper-policy.md` (`paper_target_registry` SSOT).

**Phase 11 done definition**: 3 anti-pattern surfaces gone; UAC `OperationalMode` is single SSOT.

## Phase 12 — Codex SSOT batch (P0, runs alongside per Post-Plan-Phase Codex Audit HARD RULE)

All NEW + UPDATE codex docs ship with their phases (per Phases 1-11 docs sections). This phase ensures the
WORKSPACE-WIDE codex audit catches any drift after the post-cutover plan completes.

- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **Codex audit** — re-walk every codex doc the plan touched; verify each
      reflects shipped state. Per CLAUDE.md "Post-Plan-Phase Codex Audit" HARD RULE — codex must be at parity with code
      at every phase boundary.
- [x] ✅ DEFERRED-OPERATOR-DECISION [AGENT] P0. **CLAUDE.md update** — add the post-cutover-shipped key rules:
  - "Strategy Lifecycle State Machine SSOT" (from Phase 1).
  - "Promote Workflow Path" (from May-23 plan; extend with UI-shipped status post-Phase 9).
  - "Candidate Manifest" (from Phase 2).
  - "Operational Modes" (from Phase 11).

## Done definition (overall plan)

- ✅ All 12 phases completed.
- ✅ State machine consolidated (1 canonical UAC SSOT).
- ✅ `CandidateManifest` + `BacktestRunManifest` UAC types live + populated.
- ✅ 8 new event types in UAC + UTL strategy events folded in.
- ✅ Per-archetype Pydantic config schemas for all 53 archetypes.
- ✅ Drift detection cron live.
- ✅ Cross-service auto-registration works end-to-end.
- ✅ Continuous backtest cron live.
- ✅ Backtest persistence + ranking surface end-to-end.
- ✅ Promote API backend endpoint + pre-flight pipeline; Promote UI wired.
- ✅ DART 3-way + manual-trade gate UI.
- ✅ Operational modes consolidation (`pvl-p17a-d`).
- ✅ All NEW + UPDATE codex docs shipped + reflect actual state.
- ✅ Question doc `plans/questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md` flips status
  `iterating → closed` (BOTH plans shipped + codex aligned + first end-to-end UI-driven promote run completed for a new
  archetype).

**Full-execution criterion (overall)**:

- **What ran**: end-to-end UI-driven promote run for a NEW archetype (not the May-23 lead pair — a fresh one) — backtest
  → ranking UI → click promote-to-candidate → CandidateManifest persists → click promote-to-paper → paper VM
  auto-launches → 7d paper monitor → click promote-to-live → live VM auto-launches → cross-service auto-registration
  completes → live trading.
- **Verification**: each lifecycle event present in `events/strategy-lifecycle/` partition; manifest IDs correlate; UI
  screenshots per step; alerting + risk + recon all green.

## Temporary states + canonical follow-up plans

- **Multi-tenant client-id flow (H4)**: deferred to Tier 3 post-launch
  (`plans/archive/client_reporting_pnl_attribution_mvp_2026_05_10.md` companion).
- **CEFFU custody non-stub**: stays DEFERRED unless Binance institutional flow opens.
- **A/B paper-trade governance rules**: deferred to a future plan if operator wants hard A/B enforcement.
- **`strategy_family` taxonomy**: deferred to a future plan once cross-archetype rollups become an operational need.

## Composes with

- CLAUDE.md "Plans Run To Actual Completion" — every phase has Full-execution criterion.
- CLAUDE.md "Citadel-Grade Planning Standards" — pre-audit + DAG + parallelization + SSOT discipline.
- CLAUDE.md "Post-Plan-Phase Codex Audit" — codex per phase.
- CLAUDE.md "Capture Discoveries As Plan Todos Immediately" — discoveries during plan execution land here OR in active
  plans per Findings Triage.
- `plans/active/promote_workflow_may23_cli_path_2026_05_10.md` — companion plan; this plan picks up everything DEFERRED
  there.
- `plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md` — folded
  `pvl-p17a..d / p18a..b / p20a..c / p21a / p22a / p23a..c` items distributed across Phases 1-11.
- `plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md` — Phase 9 pre-flight composes with credential
  matrix.
- `plans/active/master_to_live_defi_2026_05_23.md` Group F/G — post-cutover items track here; master plan refresh per
  CLAUDE.md "Master Plan Continuous-Verification Column" HARD RULE.

## Deferred work — migrated to: dart_and_promote_master

_Archived 2026-05-23 slot 2. This plan is the post-cutover companion to `promote_workflow_may23_cli_path_2026_05_10.md`.
All 12 phases require post-cutover execution._

- **This entire plan is DEFERRED-POST-CUTOVER**: All 12 phases (lifecycle state-machine consolidation,
  `CandidateManifest` UAC type, `LifecycleEventType` enum, per-archetype Pydantic config schemas for 48/53 archetypes,
  drift detection, cross-service auto-registration, continuous backtest cron, backtest persistence + ranking, paper
  auto-launch, champion store, operational modes consolidation, multi-tenant client-id flow) are gated on DeFi 7-day
  live soak completing. Pick up after `promote_workflow_may23_cli_path_2026_05_10.md` Phase 13.A completes.
