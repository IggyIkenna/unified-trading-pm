---
doc_type: plan
title: promote-workflow-backtest-to-paper-to-live
summary:
status: plan-spawned
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    batch-live-reconciliation-service,
    deployment-api,
    deployment-service,
    e2e-testing,
    execution-service,
    strategy-service,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md,
    plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md,
    plans/archive/client_reporting_pnl_attribution_mvp_2026_05_10.md,
    plans/archive/risk_simulations_limits_alerting_2026_05_10.md,
    plans/questions/defi_readiness_catalogue_2026_05_08.md,
    plans/epics/strategy_and_dart_master_2026_05_07.md,
    plans/epics/defi_master_2026_05_07.md,
  ]
created: 2026-05-08
overview:
  End-to-end re-audit of the promote workflow — backtest is scored + ranked, operator picks a candidate via UI button
  click → API → "candidate" status → next paper-trading deployment → live production. Re-walk every code path, DART UI
  surface, configuration shape, event stream, service interaction, approval gate, rollback affordance.
type: question
audit_completed: 2026-05-10
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-08
spawned_plan: plans/active/promote_workflow_may23_cli_path_2026_05_10.md
spawned_plan_post_cutover: plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md
related_codex:
  [
    /codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md,
    /codex/04-architecture/operational-modes.md,
    /codex/03-observability/lifecycle-events.md,
    /codex/05-infrastructure/launcher-script-ssot.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Promote workflow — backtest → ranked candidate → paper → live (end-to-end re-audit)

## Intent

The system is supposed to support a clean promotion lifecycle: a strategy / archetype / configuration runs as a
backtest, gets scored against a metric set + ranked alongside its peers, the operator picks one off the ranked board
with a UI button click, the click hits a backend API, that promotes the selected configuration to **candidate** status,
the next paper-trading deployment picks up the candidate, paper-trading runs against real-data live-replay (or live tick
stream) with simulated fills, and once paper performance clears the gates the same configuration promotes to **live
production** under real custody, real venue keys, real capital.

This question doc is a **re-audit** — the workflow has been discussed in pieces across plans (master live-DeFi cutover,
DART UI gate, deployment-api `Deploy-Missing` button, strategy-service archetype canonicalisation, batch-vs-live recon),
but the **end-to-end story** is implicit. The operator wanted to see: (a) where the backtest scoring+ranking lives
today, (b) how the UI button click currently flows through the API to flip a configuration to `candidate`, (c) what
"candidate" means as a status, (d) how the next paper-trading deployment consumes the candidate, (e) how paper → live
promotion works (DART manual gate per master plan G23), and (f) whether the workflow is **production-runnable today**
against a real backtest result, real candidate, real paper deploy, real live cutover — or whether it's a sequence of
code-shipped-but-never-run pieces glued by operator memory.

The 2026-05-23 live-DeFi cutover lands two archetypes (`carry_staked_basis` lead +
`ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion` hedge, the resolved successor of `leveraged_funding_arb`) on a real
wallet for ≥7 continuous days. Whatever the promote workflow looks like, it has to support this cutover concretely.

## Question

(Sub-questions A1-A6, B1-B6, C1-C6, D1-D7, E1-E7, F1-F4, G1-G4, H1-H7, I1-I3 — see prior draft for full text. The audit
findings below answer them per block.)

### Block A — Backtest scoring + ranking

A1 backtest output persistence; A2 score schema; A3 ranking surface; A4 slicing axes; A5 reproducibility
(`backtest_series_ref`); A6 continuous backtest cadence.

### Block B — Promote UI surface + button flow

B1 button location; B2 auth/authz; B3 API endpoint shape; B4 sync vs async + event emission; B5 candidate-state
rendering; B6 mock-mode fixtures.

### Block C — "Candidate" as a status

C1 where state lives; C2 lifecycle states + transition policy; C3 multi-candidate semantics; C4 cross-archetype +
cross-client scoping; C5 configuration capture (candidate manifest); C6 provenance chain.

### Block D — Paper-trading deployment from candidate

D1 trigger; D2 where paper runs; D3 configuration handoff; D4 testnet credentials; D5 paper-mode scoring; D6 paper →
live gates; D7 paper failures + rollback.

### Block E — Live production promotion

E1 DART definitive; E2 live promotion API + button + pre-flight; E3 live deployment shape + events; E4 custody +
treasury wire-up; E5 risk + circuit breakers; E6 live → paused / retired; E7 concurrent live deployments per archetype
(CRITICAL for May-23).

### Block F — State machine + events

F1 canonical state machine; F2 canonical event taxonomy; F3 audit log / event archive; F4 cross-asset-group consistency.

### Block G — Configuration + reproducibility

G1 config-as-code vs database; G2 per-archetype configuration schema; G3 drift detection; G4 hot-reload integration.

### Block H — Cross-cutting integration

H1 risk-and-exposure registration; H2 alerting rules; H3 position-balance-monitor; H4 client reporting; H5 PnL
attribution; H6 custody + API keys (sibling-doc composition); H7 CI / version graduation gate.

### Block I — End-to-end reality check

I1 could Ikenna run carry_staked_basis through the full workflow today? I2 service-readiness checklist walk; I3 May-23
cutover-blocking subset.

## What "answered" looks like

- A canonical plan exists in `plans/active/promote_workflow_may23_cli_path_2026_05_10.md` (May-23 cutover) +
  `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md` (post-cutover UI + state-machine
  consolidation). ✅ SHIPPED 2026-05-10.
- Codex SSOT(s) describe: full lifecycle state machine + transitions; promote API contract; candidate manifest schema;
  paper-trading deployment shape; live deployment shape; rollback / pause / retire flows. (Owned by spawned plans;
  status: scoped + enumerated, not yet shipped.)
- UI surfaces are spec'd. (Owned by post-cutover plan.)
- A real-data run has shipped: ONE archetype has gone backtest → score → rank → promote-to-candidate → paper-deploy →
  paper-green → promote-to-live → live-running, end-to-end, with full event audit trail. (Master plan F18 + `pvl-p18a`
  are the operational surfaces; this question doc closes when the May-23 cutover plan ships its first end-to-end run.)
- The two May-23 archetypes (`carry_staked_basis` + `ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion`) sit in
  `LIVE_RUNNING` for ≥7 continuous days by 2026-05-23.
- Service-readiness checklist Group F items 17-22 and G item 23 are green for both archetypes.

---

## Audit findings (synthesized from 4 parallel audit agents — 2026-05-10)

### Top-line verdicts (TL;DR)

1. **Promote UI is fully scaffolded but 100% mock.** 9 lifecycle sub-pages exist under
   [`unified-trading-system-ui/app/(platform)/services/promote/(lifecycle)/`](<../../../unified-trading-system-ui/app/(platform)/services/promote/(lifecycle)/>)
   (data-validation / model-assessment / risk-stress / paper-trading / champion / capital-allocation / governance /
   execution-readiness / pipeline). The `onPromote: (targetStage) => Promise<void>` callback is unimplemented;
   `PromoteWorkflowProvider` writes to React in-memory context, never calls a backend. Every widget reads from
   `@/lib/mocks/fixtures/promote-fixtures`.

2. **Backtest results don't persist anywhere.**
   [`strategy-service/strategy_service/engine/backtest/runner.py:262-313`](../../../strategy-service/strategy_service/engine/backtest/runner.py#L262-L313)
   `GroupBRunner.run(...)` returns `GroupBBacktestResult` in-process; nothing is written to GCS/BQ/parquet.
   [`engine/strategies/v2/registry.py:73-117`](../../../strategy-service/strategy_service/engine/strategies/v2/registry.py#L73-L117)
   `ConfigRegistry` is `dict` instance attribute, comment line 5 says "in-memory for Phase 3; UAC-persisted store lands
   in Phase 5/11" — Phase 5/11 has not landed. **Three competing path conventions** (PATH_REGISTRY
   `backtest_results/strategy_id={strategy_id}/run_id={run_id}/` vs reader `backtest_results/{run_id}/` vs grid script
   `backtests/config_grid_2yr/{archetype}/{run_id}/`) — the reader literally cannot find files written under
   PATH_REGISTRY.

3. **No ranking surface anywhere.** Workspace-wide search for `BacktestScore` / `RankedRun` / `leaderboard` /
   `best_candidate` / `champion_candidate` / `top_n_candidates` → **zero hits in active code**. The lifecycle gate
   `shadow_within_10pct_of_champion`
   ([`strategy-service/strategy_service/engine/lifecycle/lifecycle_state_machine.py:45`](../../../strategy-service/strategy_service/engine/lifecycle/lifecycle_state_machine.py#L45))
   implies a "champion" exists but no champion-store is populated; the gate is operator-supplied via
   `met_gates: list[str]` arg.

4. **FOUR competing lifecycle SSOTs in UAC.**
   [`StrategyLifecycleStage`](../../../unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/lifecycle.py)
   (legacy 7-state) + `StrategyMaturityPhase` (current canonical 10-state with `is_valid_maturity_transition()`
   validator) +
   [`StrategyMaturity`](../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/strategy_availability.py)
   (architecture-v2 8-state) +
   [`VersionStatus`](../../../unified-api-contracts/unified_api_contracts/internal/domain/strategy_service/versions.py)
   (governance 6-state). Strategy-service uses TWO simultaneously (`availability/store.py` v2 8-state;
   `version_governance/` 10-state). This violates the workspace "no double SSOT" rule four ways.

5. **NO `Candidate` enum value anywhere.** Closest semantic is `StrategyMaturityPhase.PAPER_STABLE` ("Promotion-ready").
   The 30+ "candidate" hits in the codebase are all in-domain (sports value-bet candidates, strike-selection candidates,
   archetype slot resolver candidate protocols).

6. **NO promote/candidate/lifecycle-pause events in canonical UAC `LifecycleEventType` enum.** Only strategy-related
   event in UAC is `STRATEGY_SIGNALS_READY` (coordination, not lifecycle). UTL has bare-string strategy event constants
   ([`unified-trading-library/unified_trading_library/events/event_types.py:387-412`](../../../unified-trading-library/unified_trading_library/events/event_types.py#L387-L412):
   `STRATEGY_AVAILABILITY_CHANGED` / `STRATEGY_LOCKED` / `STRATEGY_UNLOCKED` / `STRATEGY_MATURITY_ADVANCED` /
   `STRATEGY_MATURITY_REGRESSED` / `STRATEGY_LIFECYCLE_CHANGED` / `STRATEGY_LIFECYCLE_SEEDED`) — NOT registered in UAC.
   Workspace SSOT split.

7. **NO paper-trading or live-trading VM launchers in `deployment-service/scripts/vm/`.** 60+ launchers exist for
   backfill/forward-poll/sweep/dashboard but ZERO for strategy execution. `vm_zombie_watchdog.py`'s
   `VM_PREFIX_TO_BUCKET` registry has no `paper-` / `live-` / `strategy-` prefix. `live_execution_handler.py` exists as
   the API server entrypoint with `--mode live`, but its deployment shape is undefined.

8. **`StrategyVersion` doesn't capture pinned shas / model refs / features manifest version / venue keys ref / chain RPC
   URLs ref.** Closest to a candidate manifest, but only stores
   `version_id, parent_instance_id, maturity_phase, status, config_diff (changed-fields tuple), backtest_series_ref (free-form string), approval`.
   **Promotion to live without a frozen all-shas manifest = no rollback target, no incident forensics, no
   reproducibility.**

9. **DART = UI cockpit** in `unified-trading-system-ui` (mock-only).
   [`components/shell/dart-scope-bar.tsx`](../../../unified-trading-system-ui/components/shell/dart-scope-bar.tsx)
   (multi-axis filter cockpit),
   [`components/trading/execution-mode-toggle.tsx`](../../../unified-trading-system-ui/components/trading/execution-mode-toggle.tsx)
   (Live ↔ Batch toggle, no paper). Per-trade manual-trade gate is master plan G23 + `pvl-p23a/b/c` todo, NOT
   implemented. Only DART page today is `app/(platform)/services/dart/locked/` (the locked placeholder).

10. **Custody Copper has real implementation, never operationally verified.**
    [`execution-service/execution_service/custody/copper.py`](../../../execution-service/execution_service/custody/copper.py)
    HMAC-SHA256, sandbox + prod endpoints, sign-poll loop. CEFFU is STUB (`/codex/04-architecture/custody-providers.md`
    PENDING per master plan line 145+ / 515+). Master plan F19 `Last verified: NEVER`.

11. **Risk + circuit breakers + kill-switch bus shipped + wired across 4 services** (strategy / risk-and-exposure /
    alerting / position-balance) — most mature live-only infra. `KillSwitchScope` 6-level enum
    (GLOBAL/CLIENT/VENUE/STRATEGY/ARCHETYPE/INSTRUMENT). Operator-armed via YAML at boot. **NEVER operationally verified
    at archetype-cutover time** for the May-23 lead pair.

12. **NO drift detection between candidate creation and live deployment.** Workspace-wide grep for `drift` returns only
    manifest-path drift (data layer, unrelated). Hot-reload (`DomainConfigReloader` + `VersionGovernanceReloader`)
    exists but only fires on NEW `StrategyVersion` rolling out — does not detect "underlying UAC sha drifted from
    candidate's pin."

13. **Risk-and-exposure has no `register_strategy` handler.** `RiskLimits` keyed by `client_id` only, not
    strategy/deployment. `POST /risk/strategy-status` accepts `StrategyRiskProfile` per-call but doesn't persist. **All
    cross-cutting integration (H1) is operator-driven via separate API calls** at promote time.

14. **Position-balance-monitor uses process-isolation per `CLIENT_ID` env var** (1 process = 1 client), not registration
    model. Multi-tenant carry_staked_basis would require N PBMS instances. Not a May-23 blocker (single client) but a
    Tier 3 blocker.

15. **Alerting rules are STATIC in UAC `LIVE_ALERT_RULES`** (~28 hand-authored rules). NO per-deployment
    auto-generation. `pvl-p22a` adds per-mode (paper/live) thresholds; per-deployment / per-strategy fine-tuning is
    post-cutover scope.

16. **PnL-attribution has `strategy_id` everywhere, NO `deployment_id` concept.**
    [`pnl-attribution-service/pnl_attribution_service/engine/archetype_aggregator.py:12-166`](../../../pnl-attribution-service/pnl_attribution_service/engine/archetype_aggregator.py#L12)
    schema is `(timestamp, archetype, config_variant, strategy_id, slot_label, ...)`. To distinguish v2.0 from v2.1 of
    carry_staked_basis on iggy_main mainnet, attribution schema needs `version_id` extension.

17. **CRITICAL: operator-CLI path EXISTS and is genuinely capable.**
    [`e2e-testing/scripts/defi/run-paper.sh`](../../../e2e-testing/scripts/defi/run-paper.sh) +
    [`run-live.sh`](../../../e2e-testing/scripts/defi/run-live.sh) +
    [`colocated_engine.py`](../../../e2e-testing/scripts/defi/colocated_engine.py) (1343 lines) integrate strategy +
    execution + position + P&L + risk in shared memory; auto-detects DeFi/CeFi/TradFi/Sports from strategy_id; supports
    Tenderly fork (paper) + Copper MPC (live); runs `--continuous --tick-interval 3600`. **Operator-CLI live cutover for
    May-23 is achievable; UI-driven promote workflow is NOT.**

### Block A — Backtest scoring + ranking

#### A1 — Backtest output persistence

- **Code**: `GroupBRunner.run()` returns in-process; `ConfigRegistry` is in-memory dict (Phase 5/11 stub);
  `PaperComparisonTracker` is in-memory dict — lost on restart.
- **Path drift**: PATH_REGISTRY `backtest_results/strategy_id=.../run_id=.../` ≠ reader `backtest_results/{run_id}/` ≠
  grid script `backtests/config_grid_2yr/{archetype}/{run_id}/`. Workspace-internal contract drift uncaught by QG.
- **Archived prior**: `archive/execution-results-api/` (deleted, no active replacement).
- **Codex**: NO SSOT doc for canonical backtest-result path / manifest column / discovery surface.
- **Gap**: P0 — pick winning path, write `BacktestResultWriter` UTL helper that calls `record_captured` with proper
  manifest row, kill duplicate readers.

#### A2 — Score schema

- `GroupBMetrics`
  ([`engine/backtest/config_candidate.py:23-49`](../../../strategy-service/strategy_service/engine/backtest/config_candidate.py#L23-L49)):
  total_pnl / sharpe / sortino / max_drawdown / calmar / num_trades / win_rate / benchmark_fill_count (Decimal).
- **NOT in UAC** — violates "Schema provenance" QG rule. No cross-service consumer can import it cleanly.
- **2yr-grid script declares an alternate flat schema** with bps-typed fields
  ([`run_2yr_config_grid_backtest.py:43-50`](../../../strategy-service/scripts/run_2yr_config_grid_backtest.py#L43-L50))
  — two competing scoring schemas in same service.
- **No per-asset-group score schema** — sports / DeFi / CeFi all flow through `GroupBMetrics`. No CLV / IL /
  LST-yield-attribution components.
- **Gap**: P0 lift `GroupBMetrics` (or its 2yr-grid superset) to UAC `internal/domain/strategy_service/metrics.py`.
  Reconcile 2 schemas. Add per-asset-group sub-schemas.

#### A3 — Ranking surface

- **Zero hits** for `BacktestScore` / `RankedRun` / `leaderboard` / `champion_candidate` / `top_n_candidates`.
- "Rank" code is portfolio-allocators ranking signals at trade-time (`CarryFundingRankAllocator`), not ranking backtest
  candidates.
- `shadow_within_10pct_of_champion` lifecycle gate references a champion that doesn't exist anywhere in code.
- No UI route / page / component for backtest leaderboards in either UI repo.
- **Gap**: P0 ranking is greenfield. Need `RankedCandidate` UAC type + `rank_candidates(archetype, top_k, metric)`
  helper + `GET /strategy/{archetype}/candidates?rank_by=sharpe&top=10` endpoint + UI page.

#### A4 — Slicing axes

- Implicit per-`strategy_instance_id` (5-dim tuple `(archetype, slot_label, share_class, initial_equity, ...)`).
- Per-archetype only emerges in 2yr-grid script (`--archetype carry_staked_basis` flag).
- No `strategy_family` / `archetype_family` taxonomy for cross-archetype rollups.
- **Gap**: P1 make slicing axes first-class in `RankedCandidate`. Aligns with v2 5-dim instance-id.

#### A5 — Reproducibility (`backtest_series_ref`)

- Free-form string (`min_length=1`), zero validation, zero schema. Test fixtures use `"gs://x/y/backtest.parquet"` /
  `"seed://genesis"`.
- **MISSING from candidate manifest**: code-pins (UAC/UTL/strategy-service/features/instruments shas), model-pins,
  features-manifest-version, venue-keys-ref, chain-RPC-URL-pin, dependency snapshot.
- Reproducibility today = "trust the string."
- **Gap**: P0 — `BacktestRunManifest` UAC type with all pins. Composes with C5 candidate-manifest gap.

#### A6 — Continuous backtest cadence

- NO cron VM, NO ScheduleWakeup, NO GHA workflow re-runs backtests nightly/on-commit.
- `run_2yr_config_grid_backtest.py` is operator-runnable only — no `execution.owner` block per CLAUDE.md "Runbook
  Execution-Owner SSOT".
- Master plan continuous-verification matrix has Group F items 17/18 with `Last verified: NEVER`.
- **Gap**: P1 — add cron VM `strategy-backtest-cron-{ts}` per VM Naming Convention + register prefix in
  `VM_PREFIX_TO_BUCKET`.

### Block B — Promote UI surface + button flow

#### B1 — Where the promote button lives

- `unified-trading-system-ui/app/(platform)/services/promote/(lifecycle)/` — 9 lifecycle sub-pages exist
  (data-validation / model-assessment / risk-stress / paper-trading / champion / capital-allocation / governance /
  execution-readiness / pipeline).
- DART surfaces (mock-only): `components/shell/dart-scope-bar.tsx` cockpit,
  `components/trading/execution-mode-toggle.tsx` Live↔Batch toggle, `components/trading/kill-switch-panel.tsx`,
  `app/(platform)/services/dart/locked/` (only DART route).
- **Gap**: P0 — UI exists; backend wiring absent.

#### B2 — Auth/authz

- `LiveConfirmDialog`
  ([`dart-scope-bar.tsx:338-369`](../../../unified-trading-system-ui/components/shell/dart-scope-bar.tsx#L338-L369))
  gates Live mode behind `execution-full` entitlement claim.
- Per-archetype / per-client authz absent.
- **Gap**: P1 — extend Firebase custom-claim model for per-archetype permissions (post-cutover for institutional client
  product).

#### B3 — API endpoint shape

- **NO `/promote/{strategy_id}/{run_id}` endpoint anywhere.** `strategy-service/strategy_service/api/registry_router.py`
  is admin GETs only. `deployment-api/deployment_api/services/` has no `promote.py` or `live_deploy.py`.
- **Gap**: P0 greenfield. New endpoint in `deployment-api` (recommended) or new `promotion-service` repo (NOT
  recommended — adds repo).

#### B4 — Sync vs async + event emission

- Mock callback returns Promise<void> immediately. No event emission.
- **Gap**: P0 — endpoint emits `STRATEGY_PROMOTED_TO_CANDIDATE` etc.; UI shows optimistic state then converges via
  event-stream subscription.

#### B5 — Candidate state rendering

- `paper-trading-tab.tsx` displays `CandidateStrategy` type (mock). No `/candidates` page; no historical-candidates
  view.
- **Gap**: P1 — `/candidates` page + ranked-board annotation + history.

#### B6 — Mock-mode fixtures

- All Promote tabs read from `@/lib/mocks/fixtures/promote-fixtures` — **mock-mode IS the only mode today**.
- **Gap**: P0 — wire `VITE_MOCK_API=false` path to backend endpoints once they exist.

### Block C — "Candidate" as a status

#### C1 — Where state lives

- **NOT FOUND.** Closest is `StrategyMaturityPhase=PAPER_STABLE` ("Promotion-ready" per codex).
- Firestore `strategy_instance_lifecycle` collection holds
  `(maturity_phase, product_routing, available_since, phased_at, backtest_series_ref, paper_series_ref, live_series_ref, phase_history, version_lineage)`.
  **No `candidate_status` / "promotion-ready" flag.**
- **Gap**: P0 — operator decision: collapse "candidate" into `PAPER_STABLE` OR add orthogonal
  `DeploymentCandidacy { NONE, NOMINATED, APPROVED_FOR_PAPER, APPROVED_FOR_LIVE, RETIRED_CANDIDATE }` axis.

#### C2 — Lifecycle states + transition policy (THE BIG FINDING)

| SSOT                                   | File                                                      | Values                                                                                                                               | Validator                           |
| -------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------- |
| 1. `StrategyLifecycleStage` (LEGACY)   | `internal/domain/strategy_service/lifecycle.py:10-19`     | DRAFT, BACKTEST, VALIDATED, PAPER, SHADOW, LIVE, DEPRECATED (7)                                                                      | None                                |
| 2. `StrategyMaturityPhase` (canonical) | same file:45-73                                           | SMOKE, BACKTEST_MINIMAL, BACKTEST_1YR, BACKTEST_MULTI_YEAR, PAPER_1D, PAPER_14D, PAPER_STABLE, LIVE_EARLY, LIVE_STABLE, RETIRED (10) | `is_valid_maturity_transition()` ✅ |
| 3. `StrategyMaturity` (arch-v2)        | `internal/architecture_v2/strategy_availability.py:46-60` | CODE_NOT_WRITTEN, CODE_WRITTEN, CODE_AUDITED, BACKTESTED, PAPER_TRADING, PAPER_TRADING_VALIDATED, LIVE_TINY, LIVE_ALLOCATED (8)      | Implicit (`maturity_rank`)          |
| 4. `VersionStatus` (gov)               | `internal/domain/strategy_service/versions.py:51-59`      | DRAFT, PENDING_APPROVAL, APPROVED, ROLLED_OUT, RETIRED, REJECTED (6)                                                                 | `__post_init__` invariants          |

- **Strategy-service uses TWO simultaneously**: `availability/store.py:24-26` imports `StrategyMaturity` (v2 8-state);
  `version_governance/pending_approvals_runner.py:31` imports `StrategyMaturityPhase` (Plan A 10-state) +
  `VersionStatus`.
- **Gap**: P0 — pick canonical (`StrategyMaturityPhase` recommended — most production code paths, codex-blessed).
  Deprecate `StrategyLifecycleStage` + `StrategyMaturity`. Migrate consumers per Citadel-Grade § 6.

#### C3 — Multiple candidates simultaneously (A/B)

- No code-level rule prevents multiple instances in same `paper_*` phase. Each `instance_id` independent in Firestore.
  A/B is implicit.
- Codex `strategy-lifecycle-maturity.md:100-113` upsell ladder: 4 venue-set variants of one archetype each ship as
  separate `StrategyInstance` — multi-instance per archetype is explicitly the design.
- No "one-candidate-per-archetype" enforcement.
- **Gap**: P2 — if A/B governance is wanted (one candidate per `(archetype, venue_set, share_class)`), add UAC rule.

#### C4 — Cross-archetype + cross-client scoping

- Each instance keyed by 5-dim `instance_id`. No shared cross-archetype state.
- `StrategyAvailabilityEntry.exclusive_client_id` supports per-client locking via `LockState.CLIENT_EXCLUSIVE`.
- `strategy_family` axis missing. Cross-asset-group candidacy implicit (asset_group is property of venues in
  `VenueSetVariant`).
- **Gap**: P2 — add `strategy_family` axis post-cutover.

#### C5 — Configuration capture (candidate manifest) — MAJOR P0 GAP

- `StrategyVersion` captures: `version_id, parent_instance_id, maturity_phase, status, config_diff` (only deltas vs
  parent), `backtest_series_ref` (free-form string), `approval, rolled_out_at, supersedes_version_id, review_history`.
- **MISSING**: pinned commit shas (workspace, UAC, UTL, strategy-service, execution-service), ML model ref (model_id,
  model_version, training_run_id), features manifest version, venue keys ref (Secret Manager paths resolved at boot, NOT
  pinned), chain RPC URLs ref (resolved at runtime from UAC templates), wallet ref / address, execution lane / mode.
- **No `CandidateManifest` Pydantic type, no `promote_strategy_to_candidate()` API, no candidate-blob in GCS, no
  Firestore `strategy_candidate_manifests` collection.**
- **Gap**: P0 — biggest single gap. New UAC `CandidateManifest` (or `LiveDeploymentManifest`) type + Firestore
  collection + admin endpoint. **Rollback / forensics blocker.**

#### C6 — Provenance chain

- `StrategyVersion.parent_version_id` + `phase_history` cover "prior version + when phases moved."
- `StrategyVersion.backtest_series_ref` is a string ref; no `BacktestRunManifest` it points to.
- `version_lineage: tuple[str, ...]` on `StrategyInstanceLifecycle` carries ancestor version IDs.
- **Gap**: P1 — full lineage `backtest_run_id → score → rank → candidate → paper_id → live_id` not captured. Add
  provenance fields to manifest types.

### Block D — Paper-trading deployment from candidate

#### D1 — Trigger

- Today: operator action via CLI flag (`group_b_handler --promote`) OR `e2e-testing/scripts/defi/run-paper.sh`
  invocation.
- NO cron, NO config-as-code merge hook, NO "config_candidate.evaluated_at + days_elapsed > 7 → auto-promote" logic.
- `engine/strategies/v2/shadow_deployment.py:ShadowDecision { PROMOTE, EXTEND, REJECT, ROLLBACK }` +
  `ShadowDeploymentPolicy` (min_shadow_duration=14d, min_shadow_trade_count=100, max_pnl_dispersion_bps=50,
  max_fill_dispersion_bps=15, min_signal_correlation=0.90) — closest existing promotion-gate model but for
  build-vs-build shadow not paper-vs-live.
- **Gap**: P0 — operator-CLI is May-23 path; auto-promote on candidate cron is post-cutover.

#### D2 — Where paper runs

- **NO paper-trading VM launcher in `deployment-service/scripts/vm/`.** 60+ launchers exist; ZERO for strategy
  execution.
- `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` has no `strategy-paper-` / `paper-` prefix.
- `live_execution_handler.py` is API-server entrypoint with `--mode live`; says "Batch mode not yet implemented" —
  contradicts workspace "Batch = Live" SSOT.
- Operator path: `e2e-testing/scripts/defi/colocated_engine.py --mode paper --execution-provider tenderly` works for
  SSH/CLI operator.
- **Gap**: P0 — `launch-strategy-paper-vm.sh` in `deployment-service/scripts/vm/` (per Launcher Script SSOT rule),
  register `strategy-paper-` prefix in `VM_PREFIX_TO_BUCKET`. **Cutover blocker.**

#### D3 — Configuration handoff

- `DeployableConfigCandidate` content_hash + config_version + config_json + GroupBMetrics exists. Round-tripped by
  `ConfigRegistry.ConfigSlot` as versioned JSON blob.
- NO consumer that takes a `DeployableConfigCandidate` → spawns paper VM → boots execution-service with config_json
  injected as env.
- **Gap**: P0 — launcher → boot-env handoff via `--candidate-version=N` flag through `ConfigRegistry`.

#### D4 — Real-venue testnet credentials

- DeFi: Tenderly Virtual TestNet fork covers EVM. **Solana paper analogue absent** for jitoSOL/mSOL/bSOL — open as
  `pvl-p20c-solana-paper-wiring`.
- CeFi: Deribit testnet only. **5 of 6 perp venues (Bybit, Binance, OKX, Hyperliquid, Aster) have NO callable
  testnet-mode constructor** — open as `pvl-p20b-cefi-perp-testnet-audit`. **CRITICAL May-23 GAP for hedge legs.**
- Sports: `paper_betting.py` is most mature paper adapter. `_PAPER_VENUE_KEYS` string-set anti-pattern (`pvl-p17c`
  deletion).
- No `credentials/paper/` namespace in Secret Manager. Per-(venue, mode) credential registry absent.
- **Gap**: P0 — perp testnet audit blocks paper-mode hedge leg run for May-23.

#### D5 — Paper-mode scoring

- Same `GroupBMetrics` schema by SSOT design (workspace "Batch = Live"). No schema gap.
- Two-lane separation: strategy-alpha (always-fill) vs full-execution (matching engine).
- **Gap**: operational — no paper-mode evidence run has produced a scored result. `pvl-p18a` is the missing operational
  step.

#### D6 — Paper → live gates

- `ShadowDeploymentPolicy` shape (14d / 100 trades / dispersion bps) is closest precedent — but gates build-vs-build
  shadow, not paper-vs-live.
- `engine/core/testing_stage_gate.py:validate_stage_transition` enforces ONE-STEP TestingStage progression
  `MOCK → HISTORICAL → LIVE_MOCK → LIVE_TESTNET → STAGING → LIVE_REAL`.
- Master plan target: ≥7 continuous days; DART manual-trade window 3 days operator-monitored on `carry_staked_basis`
  then auto-fire.
- NO codified per-archetype paper → live gate schema (PnL threshold, drawdown ceiling, recon parity threshold).
- **Gap**: P0 — codify gate schema as UAC type, default per archetype.

#### D7 — Paper failures + rollback

- `ShadowDecision.ROLLBACK` exists conceptually. `KillSwitchScope` supports per-archetype halts.
- NO `STRATEGY_PAPER_FAILED` event type. NO "status flips back to RANKED" code path (no candidate state machine in
  production).
- **Gap**: P1 — wire rollback to a paper-deployment registry that doesn't exist yet (D2).

### Block E — Live production promotion

#### E1 — DART (definitive)

- DART = **operator-facing trading cockpit in unified-trading-system-ui** intended to provide (1) mode-toggle
  (batch/paper/live), (2) per-trade manual-execution gate during first days of live trading, (3) per-strategy
  pause/kill-switch.
- Today: cockpit shell + filters exist (mock-only); manual-trade gate is **aspirational, not implemented** (master plan
  G23 + line 1292 is `[ ]` checkbox).
- `LiveConfirmDialog` is mode-toggle confirmation, NOT per-trade approval.
- Codex `/codex/14-customer-journeys/dart/mode-toggle.md` NEW (does not exist on disk yet).
- **Gap**: P0 — `pvl-p23a/b/c` (3-way visualization + deployment-api `/strategy/{id}/runs` endpoint + per-trade
  manual-trade gate UI). Cutover blocker.

#### E2 — Live promotion API + button + pre-flight

- **NO `/promote-to-live/{strategy_id}/{candidate_id}` endpoint** exists.
- Promote UI's `useRecordPromoteWorkflow()` returns `RecordFn` writing to React in-memory context. **No fetch / axios /
  API call.**
- Pre-flight check codification per-stage-tab in UI; **no backend gate enforces them.**
- **Gap**: P0 — endpoint + pre-flight pipeline (custody connected / venue keys present / alerting wired / kill-switch
  armed / risk limits set / recon green).

#### E3 — Live deployment shape + events

- **NO live-deployment VM launcher** in `deployment-service/scripts/vm/`.
- `live_execution_handler.py` is API-server entrypoint when run with `--mode live` — deployment shape (Cloud Run vs GCE
  VM vs both vs per-archetype) undefined.
- `LIVE_DEPLOYMENT_STARTED` event type appears only in OpenAPI YAML — NOT in
  `unified_api_contracts.internal.events.LifecycleEventType`. Boot/shutdown via `ServiceBootstrap` standard
  STARTED/STOPPED/FAILED.
- Codex `/codex/05-infrastructure/live-deployment-monitoring.md` referenced as NEW work-stream B doc; not verified on
  disk.
- **Gap**: P0 — `launch-strategy-live-vm.sh` + register `strategy-live-` prefix; live-deployment event types in UAC;
  per-launch event-verification protocol per "no fire-and-forget VM launches" rule.

#### E4 — Custody + treasury wire-up

- `execution-service/execution_service/custody/copper.py` — full HMAC-SHA256, sandbox + prod, sign-poll loop. Real
  implementation, never operationally verified end-to-end on a live signing.
- CEFFU: ZERO references in code. Codex `custody-providers.md` STUB. Manual handoff acceptable for Binance flows per
  master plan Q&A 3.
- Activation: Copper credentials loaded at execution-service boot via `venues/initializer.py` from Secret Manager. NOT
  triggered by promote — always-on per environment.
- **Gap**: F19 `Last verified: NEVER`. P0 — Copper sub-account provisioned + funded + first live-signing dry-run before
  May-23. CEFFU stays STUB (deferred per Q&A 3).

#### E5 — Risk + circuit breakers

- `unified_api_contracts/internal/reference/circuit_breaker_config.py` ships `VenueCircuitBreakerConfig` +
  `CircuitBreakerConfigRegistry` (per venue: failure_threshold + cooldown_seconds + triggering_error_classes). YAML at
  `unified-trading-pm/configs/circuit_breaker_config.yaml`.
- `KillSwitchBus` shipped + wired across 4 services (strategy / risk-and-exposure / alerting / position-balance). UAC
  `KillSwitchScope` 6-level (GLOBAL/CLIENT/VENUE/STRATEGY/ARCHETYPE/INSTRUMENT).
- Master plan `kill_switch_drawdown_pct=5` + `kill_switch_position_breach_pct=20` per-archetype;
  `kill_switch_scope=ARCHETYPE`.
- **Gap**: code shipped + wired; OPERATIONAL gate (operator arms kill-switch rules in production with actual May-23
  archetype configs) is per-cutover. **Most mature live-only infra surface.**

#### E6 — Live → paused / retired

- `KillSwitchBus` GLOBAL/STRATEGY/ARCHETYPE scopes effectively pause via not-emitting-new-directives. PAUSE primitive
  today.
- NO `STRATEGY_RETIRED` event. NO `/api/strategies/{id}/pause` or `/retire` endpoint.
- Mock-only `demote` action in promote-workflow-context.tsx.
- **Gap**: P1 — `/pause` + `/retire` endpoints + UI buttons + events. Kill-switch covers PAUSE for May-23.

#### E7 — Concurrent live deployments per archetype (CRITICAL for May-23)

- Master plan: `carry_staked_basis` + `ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion` simultaneously ≥7 days.
- `kill_switch_scope=ARCHETYPE` design implies separate per-archetype lanes — but no per-archetype VM launcher exists.
- `V2EngineOrchestrator` runs strategies; whether N archetypes in 1 process vs N processes is undefined.
- **Gap**: P0 most critical for May-23. No deployment shape declared for "two archetypes live, isolated, observable,
  kill-switchable independently." Single-deployment vs two-coordinated undecided. **Resolve in May-23 cutover plan.**

### Block F — State machine + events

#### F1 — Canonical state machine

- Partially codified — 4 competing SSOTs (per C2). Only `StrategyMaturityPhase` has explicit transition validator +
  codex SSOT.
- Cross-asset-group consistent (good).
- **Gap**: P0 — pick `StrategyMaturityPhase` as canonical. Reconcile + deprecate.

#### F2 — Canonical event taxonomy

- UAC `LifecycleEventType` StrEnum (~60 values) is canonical SSOT for service-runtime events. **Only
  `STRATEGY_SIGNALS_READY` is strategy-related.**
- UTL has 7 bare-string strategy event constants NOT in UAC enum.
- Events question doc proposes that **DON'T exist anywhere**: `STRATEGY_PROMOTED_TO_CANDIDATE`,
  `STRATEGY_PROMOTED_TO_PAPER`, `STRATEGY_PROMOTED_TO_LIVE`, `STRATEGY_PAPER_FAILED`, `STRATEGY_LIVE_PAUSED`,
  `STRATEGY_LIVE_RETIRED`, `STRATEGY_LIFECYCLE_DEMOTED` (referenced in codex but not defined).
- **Gap**: P0 — fold UTL constants into UAC `LifecycleEventType`. Add missing event types. Cross-service event-consumer
  matrix.

#### F3 — Audit log / event archive

- **NO `events/strategy-lifecycle/` partition.** Strategy events would land under `events/strategy-service/...` per
  standard service-name partition.
- NO retention policy for strategy-lifecycle events.
- `phase_history` audit trail: kept inline on `StrategyInstanceLifecycle.phase_history: tuple[PhaseTransition, ...]`
  (`(from_phase, to_phase, transitioned_at_utc, transitioned_by, rationale)`).
- Compliance mirror: codex `strategy-lifecycle-maturity.md:255-256` claims `audit_log` collection mirror — **NOT
  verified in code**. PATCH endpoint at `unified-trading-api/.../routes/registry.py` does NOT call `log_event`.
  Codex/code drift.
- **Gap**: P1 — per-strategy events bucket + retention policy + actual `audit_log` mirror.

#### F4 — Cross-asset-group consistency

- All 4 lifecycle enums are asset-group-agnostic. Same machine for cefi/defi/sports/prediction. ✅
- Per-asset-group promotion gates / candidate criteria NOT present.
- **Gap**: P2 — per-asset-group gate fine-tuning post-cutover.

### Block G — Configuration + reproducibility

#### G1 — Config-as-code vs database

- 28 yaml files in `strategy-service/strategy_service/configs/` — flat dicts, no schema, read-once at startup, NOT
  hot-reloaded.
- `ConfigRegistry` in-memory dict (Phase 5/11 stub).
- `VersionGovernanceReloader` polls `VersionStoreReadable` Protocol — Firestore-backed implementation not located in
  this audit.
- `ConfigStore` + `ConfigAuditTrail` exist in UTL for `StrategyDomainConfig` persistence (enable/disable lists,
  instrument universes), NOT per-strategy parameters.
- **Gap**: P0 — Firestore-backed candidate store (the Phase 5/11 promised work).

#### G2 — Per-archetype configuration schema

- `ArchetypeConfig` dataclass exists
  ([`internal/architecture_v2/archetype_config.py:50`](../../../unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_config.py#L50)):
  5 risk fields. `ARCHETYPE_CONFIG_SEED` covers 5 of 53 archetypes.
- `get_archetype_config(archetype)` raises `KeyError` for un-seeded — fail-loud.
- **Validation does NOT cover strategy parameter space** — grid-swept dimensions (slippage_cap_bps /
  funding_spread_threshold_bps / target_leverage / etc.) live in loose `dict[str, str]` (`tested_params`,
  `register_instance(params=...)`).
- Sports has its own `ArbitrageStrategyConfig` BaseModel — sports-specific, not generalised.
- **Gap**: P1 — per-archetype Pydantic config schemas for FULL parameter space + `ARCHETYPE_PARAMS_SEED` covering
  all 53.

#### G3 — Drift detection

- **NONE.** Workspace-wide grep returns only manifest-path drift (data layer, unrelated).
- No "pinned UAC sha vs current main" check. No "features schema for X has changed → invalidate candidate" check. No
  `audit_drift.py` / `config_drift.py`.
- `ConfigDiff` is fork-time parent → child diff, NOT deployed-candidate vs current-state drift.
- **Gap**: P1 — periodic drift checker cron VM `strategy-drift-watchdog-{ts}` + `STRATEGY_CANDIDATE_DRIFT` event +
  alerting wire.

#### G4 — Hot-reload integration

- `DomainConfigReloader[StrategyDomainConfig]` + `[InstrumentDomainConfig]` exist
  (`strategy-service/strategy_service/config_reloaders.py:154-179`). Triggers on Pub/Sub, atomic swap, fires
  `INSTRUMENT_UNIVERSE_CHANGED` event.
- Gated on `CONFIG_STORE_BUCKET` env var — silently disabled if missing (workspace fail-loud anti-pattern).
- `VersionGovernanceReloader` (line 194+) — Plan-D Phase 3 polls VersionStore for ROLLED_OUT versions, applies to
  in-memory strategy registry. 5-min cadence matching `ApiKeyReloader`.
- Per-strategy parameter hot-reload exists via the version-governance path; operationally heavy for parameter tweaks.
- `PaperComparisonTracker` is in-memory — restart loses all in-flight paper comparison evidence.
- **Gap**: P1 — (a) un-silent the `CONFIG_STORE_BUCKET` gate; (b) verify Firestore `VersionStoreReadable` impl; (c)
  persist `PaperComparisonTracker` to Firestore.

### Block H — Cross-cutting integration

#### H1 — Risk-and-exposure-service registration

- NO "register strategy" / "register deployment" handler. Per-client + per-call evaluator only.
- `GET / POST /risk-limits/{client_id}` — per-client RiskLimits keyed by client_id, NOT strategy/deployment.
- `POST /risk/strategy-status` accepts `StrategyRiskProfile` per-call but doesn't persist.
- **Gap**: P1 — when promoting to LIVE_EARLY, no service auto-creates per-strategy RiskLimits / registers risk-monitor
  watchdog. **Operator-driven via separate API calls** for May-23 cutover.

#### H2 — Alerting-service rules

- Alert rules STATIC in UAC `LIVE_ALERT_RULES` (~28 hand-authored). Not auto-generated per deployment.
- `pvl-p22a` adds per-mode (paper/live) thresholds — only per-deployment customisation in scope.
- **Gap**: P1 — per-deployment / per-strategy auto-rule-generation post-cutover. May-23 covered by static rules.

#### H3 — Position-balance-monitor registration

- Process-isolation per `CLIENT_ID` env var bound at boot. 1 PBMS instance = 1 client.
- All position models tagged with `client_id` PII; NO `register_account` / `onboard_strategy` handler.
- Multi-tenant carry_staked_basis requires N PBMS instances.
- **Gap**: P2 (Tier 3 SaaS) — registration model. May-23 single-client = single instance OK.

#### H4 — Client reporting integration

- NO `client_id` / `tenant_id` field on strategy lifecycle / deployment registration shape.
- Client-attribution is END-stage (P&L parquets keyed by client).
- Sibling doc `client_reporting_pnl_attribution_mvp_2026_05_10.md` confirms: client-reporting is Tier 3 post-launch; NOT
  cutover scope.
- **Gap**: P2 — multi-tenancy scope post-cutover.

#### H5 — PnL attribution mapping

- `(timestamp, archetype, config_variant, strategy_id, slot_label)` schema. NO `deployment_id` / `version_id` column.
- `KillSwitchScope.STRATEGY` granularity — finest grain in attribution.
- **Gap**: P1 — extend pnl-attribution schema with `version_id` to distinguish v2.0 from v2.1 of same strategy.

#### H6 — Custody + API keys (sibling doc composition)

- Composes with `api_keys_wallets_accounts_readiness_2026_05_08.md` — sibling doc explicitly frames credential
  pre-flight as operator-discipline.
- Custody factory: copper (real), ceffu (STUB).
- NO pre-flight check that "before promoting to live, custody endpoint must respond to ping."
- F19 + F20 `Last verified: NEVER`.
- **Gap**: P0 — operator pre-flight checklist for May-23; auto pre-flight is post-cutover.

#### H7 — CI / version graduation gate

- NO version-graduation gate ties strategy-promote-to-live to repo 1.0.0 status. They're orthogonal.
- `is_approval_eligible(version)` checks STRATEGY VERSION maturity_phase ≥ BACKTEST_1YR — NOT underlying repo version.
- **Gap**: NONE — the master plan doesn't require this link.

### Block I — End-to-end reality check

#### I1 — Could Ikenna run carry_staked_basis through the full workflow today?

| #   | Step                                                        | Status      | Blocker                                                                                                                                                                                                                                                              |
| --- | ----------------------------------------------------------- | ----------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | Run a backtest against last 60d of real DeFi data           | **PARTIAL** | `trace_carry_staked_basis.py` traces single-archetype; `run_2yr_config_grid_backtest.py` shipped @3dea3c7 but operator-pending full-run. NO "kick off backtest from UI" path.                                                                                        |
| 2   | See run on a ranked board with score vector                 | **NO**      | `model-assessment-tab.tsx` + ranked-board component exist but read mock fixtures only. No real backend endpoint for backtest scores.                                                                                                                                 |
| 3   | Click "Promote to candidate"                                | **NO**      | `promote-flow-modal.tsx onPromote` is a callback prop with no implementation. NO backend handler.                                                                                                                                                                    |
| 4   | See candidate persisted with full provenance                | **NO**      | `StrategyVersion` lacks pinned-shas / model-ref / features-manifest-version. NO `/api/candidates` endpoint.                                                                                                                                                          |
| 5   | Launch (or auto-launch) paper-trading deploy on testnet     | **PARTIAL** | `e2e-testing/scripts/defi/run-paper.sh` works for OPERATOR via SSH/CLI. NO VM launcher in `deployment-service/scripts/vm/`. NO "auto-launch on promote-to-paper" backend wiring.                                                                                     |
| 6   | Watch paper-trading metrics for ≥7 days                     | **PARTIAL** | `colocated_engine.py --continuous --tick-interval 3600` runs continuously. Events stream to GCS. DART Active Alerts panel shipped. NO "promote-workflow-aware" metrics.                                                                                              |
| 7   | Click "Promote to live" once gates clear                    | **NO**      | Same as step 3 — `onPromote` unimplemented. `is_approval_eligible()` exists but no UI/API surface invokes it. Gate would need to extend with paper-runtime ≥7d, drawdown ≤X bps, recon variance ≤Y bps — none codified.                                              |
| 8   | See live deployment running with real keys, custody, wallet | **PARTIAL** | `e2e-testing/scripts/defi/run-live.sh` works for OPERATOR via SSH/CLI: real Copper MPC (HMAC-SHA256), real chain RPCs, Solana via Pyth Hermes (unbanned 2026-05-06). CEFFU STUB. F19 `Last verified: NEVER`. NOT promote-workflow-launched.                          |
| 9   | Have alerting + risk + reconciliation wired in real-mode    | **PARTIAL** | KillSwitchBus + AlertCode + 5-service consumer migration shipped. Alerting consumes UAC `LIVE_ALERT_RULES`. F21 (recon suite) `Last verified: NEVER` — UTL `batch_live_reconciler` shipped @908b1647, cron-pending. F22 paging-target Secret Manager wiring pending. |

**Net answer**: **PARTIALLY** — Ikenna can run carry_staked_basis end-to-end LIVE today via
`e2e-testing/scripts/defi/run-live.sh` (real Copper, real chains, real venues), with the engine doing real work and
emitting events the alerting service can route. What he CANNOT do is execute the **promote workflow** — every step that
involves a UI button, backend transition, or automated gate (steps 2/3/4/5 auto-launch, 7) is either mock-only or
absent. **The execution layer is Citadel-grade; the orchestration layer above it is a skeleton.** **For May-23, an
operator-CLI-driven live cutover is achievable; a UI-driven promote-workflow cutover is not.**

#### I2 — Service-readiness checklist walk

| Group                           | Items | State today                                                         | Gap                                                                               |
| ------------------------------- | ----- | ------------------------------------------------------------------- | --------------------------------------------------------------------------------- |
| A (code health)                 | 1-3   | green for promote-relevant                                          | n/a                                                                               |
| B (data correctness)            | 4-8   | green                                                               | n/a (writegate Phase 3.D.4 complete + UTL cluster validation 61a142b0)            |
| C (runtime parity)              | 9-11  | partial — C10 batch=live cron pending; C11 AWS+GCP parity in flight | continuous-verification matrix                                                    |
| D (coverage & shard)            | 12-14 | green                                                               | n/a                                                                               |
| E (operability)                 | 15-16 | green                                                               | n/a                                                                               |
| F (trading prereqs — live-only) | 17-22 | **all PARTIAL**                                                     | every F item has `Last verified: NEVER` OR code-shipped-not-operationally-shipped |
| G (operator UX — live-only)     | 23    | partial — DART components mock-only                                 | `pvl-p23a/b/c` Phase 4 gates real-backend wiring                                  |

**Pivotal observation**: Groups A-E essentially green for promote-relevant services. Groups F-G (live-only) uniformly
PARTIAL — every F item has either `Last verified: NEVER` OR code-shipped-not-operationally-shipped. **The May-23
critical-path risk is concentrated in Groups F-G, exactly where the promote workflow lives.**

#### I3 — May-23 cutover-blocking subset

**MUST ship for May-23 (P0)** — Ikenna cannot execute live carry_staked_basis without these:

- F19 — Copper sub-account provisioned + funded + first live-signing dry-run (operator-only).
- F18 — 2-year config-grid backtest actually run (`run_2yr_config_grid_backtest.py` operator-pending ~8-12h sweep).
  Informs live-config selection.
- F22 — Phase 4 alerting paging-target Secret Manager wiring + Phase 7 quietness 48h staging dry-run + Phase 8 live
  rehearsal.
- F21 — `batch-live-reconciliation-service` minimum-viable shipment (per-archetype P&L diff + per-trade fill
  comparison).
- F20 — Tenderly fork validated end-to-end for lead archetype + Solana paper wiring (`pvl-p20c`).
- `pvl-p18a` paper-mode evidence run ≥3 continuous days for `carry_staked_basis` +
  `ARBITRAGE_PRICE_DISPERSION:funding-rate-dispersion` lead pair.
- 6 perp-venue API keys present in Secret Manager + read-write scope verified (composes with
  `api_keys_wallets_accounts_readiness_2026_05_08.md`).
- CarryStakedBasis live-CLI execution dry-run end-to-end on testnet via `run-live.sh --dry-run`.
- **NEW** `launch-strategy-paper-vm.sh` + `launch-strategy-live-vm.sh` in `deployment-service/scripts/vm/` (Audit gap,
  register prefixes in VM_PREFIX_TO_BUCKET).
- **NEW** `pvl-p17e-launcher-scripts` per Audit-Tab-4 recommendation.
- **NEW** Resolve E7 concurrent-live-deployment shape (single process vs per-archetype VM).

**Can wait post-cutover (P1+)** — promote-workflow infrastructure not on live-trading critical path:

- H1-H7 cross-cutting auto-registration (operator-driven equivalents work via separate API calls + env vars).
- Promote UI wired to real backend (`pvl-p23a/b/c`) — operator can promote via CLI for May-23.
- `StrategyVersion` provenance enrichment (pinned-shas + model-ref + features-manifest-version).
- Promote/candidate/lifecycle-pause events in canonical UAC `LifecycleEventType`.
- CEFFU non-stub implementation — Binance institutional flow not lead-archetype-blocking.
- DART 3-way visualization (`pvl-p23a`).
- Alerting per-deployment auto-rule-generation.
- `pvl-p17a-d` UAC enum consolidation (4-cell ExecutionTarget × ExecutionTrigger refactor).
- 4 lifecycle SSOT consolidation (operationally functional today; refactor post-cutover).

## Operator notes / answers

**Operator direction 2026-05-09**: "do the audit you have codex, docs and code write plans afetr answerign quesitons
gettig us to full completion befroe 23rd may no shortcuts" → **plan-extraction split**:

1. **May-23 cutover plan** = operator-CLI promote path hardened to ship the live cutover by 2026-05-23 with no shortcuts
   on data correctness / observability / kill-switch / reconciliation.
2. **Post-cutover plan** = UI-driven promote pipeline + state-machine consolidation + cross-service auto-registration +
   candidate manifest enrichment, scoped 4-6 weeks post-cutover.

## Iteration log

| Date            | Author         | Change                                                                                                                                                                                                                                                                                                                              |
| --------------- | -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-08      | agent (claude) | Initial draft per operator request — re-audit promote workflow end-to-end.                                                                                                                                                                                                                                                          |
| 2026-05-09      | agent (claude) | Operator direction "no shortcuts, full completion before May-23". Fanned out 5 parallel audit agents (4 returned: A+G / C+F / D+E / H+I; B covered by D+E coverage of UI surface).                                                                                                                                                  |
| 2026-05-10      | agent (claude) | Audit findings synthesized; status `drafting → iterating`; 2 spawned plans drafted (May-23 cutover CLI path + post-cutover UI pipeline).                                                                                                                                                                                            |
| 2026-05-10 (PM) | agent (claude) | Operator pivot: ship UI promote pipeline alongside CLI for May-23. May-23 plan extended with 6 UI track phases (U1-U6); post-cutover plan reframed to EXTEND minimal-UI shipments rather than build from scratch; master plan banners refreshed. Status `iterating → plan-spawned` (both plans committed; execution multi-session). |

## Plan-shape decisions (filled before plan extraction)

- **Plan name + path**: TWO plans:
  - `plans/active/promote_workflow_may23_cli_path_2026_05_10.md` — operator-CLI cutover hardening.
  - `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md` — full UI-driven workflow + state-machine
    consolidation.
- **Plan type**: mixed (code + infra + UI + ops + governance).
- **Owner side**: Ikenna (cross-cutting design ≥3 repos + trading-judgment + governance per CLAUDE.md split principle).
- **Codex SSOTs touched** (NEW + UPDATE):
  - **NEW** `/codex/04-architecture/promote-workflow-architecture.md` — pin operator-CLI-vs-UI distinction; H1-H7
    cross-service registration model; 9-step flow; reference maturity ladder.
  - **NEW** `/codex/09-strategy/operational/cli-promote-paths.md` — `run-paper.sh` + `run-live.sh` as May-23 SSOT;
    per-mode operator pre-flight checklist (custody / API keys / wallets / RPC / Tenderly / matching engine).
  - **NEW** `/codex/04-architecture/strategy-lifecycle-state-machine.md` — reconciled canonical state machine (replaces
    de-facto split).
  - **NEW** `/codex/04-architecture/live-deployment-manifest.md` — `LiveDeploymentManifest` shape + capture point +
    rollback recipe.
  - **NEW** `/codex/05-infrastructure/live-deployment-monitoring.md` (master plan line 146 work-stream B).
  - **NEW** `/codex/14-customer-journeys/dart/mode-toggle.md` (`pvl-p23a/b/c`).
  - **NEW** `/codex/04-architecture/operational-modes.md` (`pvl-p17a-d`).
  - **NEW** `/codex/04-architecture/paper-vs-live-execution-seam.md`.
  - **NEW** `/codex/05-infrastructure/per-venue-paper-policy.md` (`paper_target_registry`).
  - **NEW** `/codex/05-infrastructure/strategy-vm-launcher-shape.md`.
  - **NEW** `/codex/14-customer-journeys/promote-pipeline-backend.md`.
  - **NEW** `/codex/09-strategy/architecture-v2/cross-cutting/backtest-persistence-and-ranking.md`.
  - **NEW** `/codex/09-strategy/architecture-v2/cross-cutting/backtest-run-manifest.md`.
  - **NEW** `/codex/09-strategy/architecture-v2/cross-cutting/strategy-config-drift-detection.md`.
  - **UPDATE** `/codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md` — fix `STRATEGY_LIFECYCLE_CHANGED`
    PATCH-emit claim (line 245) + `STRATEGY_LIFECYCLE_DEMOTED` (line 46) + `STRATEGY_CIRCUIT_BREAKER` (line 46) +
    `audit_log` mirror claim (line 256). Codex/code drift cleanup.
  - **UPDATE** `/codex/03-observability/lifecycle-events.md` — extend canonical event taxonomy with strategy-lifecycle
    event types + cross-service event-consumer matrix.
  - **UPDATE** `/codex/04-architecture/custody-providers.md` — populate CEFFU subsections per master plan line 515-516.
  - **UPDATE** `/codex/04-architecture/batch-live-architecture.md` — extend with paper-mode positioning.
  - **UPDATE** `/codex/05-infrastructure/path-registry.md` — pin canonical `backtest_results/` template, kill legacy
    reader path.
  - **UPDATE** CLAUDE.md — add "Strategy Lifecycle State Machine SSOT" key rule pointing at the new codex doc + the
    canonical enum; add "Promote Workflow Path" key rule (CLI for May-23 / UI post-cutover).
- **Cross-plan dependencies**:
  - `master_to_live_defi_2026_05_23.md` Group F/G — consumes May-23 cutover plan items.
  - `paper_vs_live_workflow_maturity_2026_05_08.md` — already folded
    `pvl-p17a..d / p18a..b / p20a..c / p21a / p22a / p23a..c`. May-23 plan extends with `pvl-p17e-launcher-scripts` +
    `pvl-p23d-promote-api-and-preflight` + `pvl-p23e-live-deployment-events`.
  - `client_reporting_pnl_attribution_mvp_2026_05_10.md` — H4 + H5 deferred to Tier 3 post-launch.
  - `risk_simulations_limits_alerting_2026_05_10.md` — H1 + H2 composition.
  - `api_keys_wallets_accounts_readiness_2026_05_08.md` — H6 composition.
  - `defi_readiness_catalogue_2026_05_08.md` — venue + chain coverage (jitoSOL/mSOL/bSOL Solana).
- **Estimated scope**:
  - May-23 cutover plan: ~8-12 AI-days over the 13 days remaining (2026-05-10 → 2026-05-23). 4 parallel sub-agent
    fan-outs feasible per CLAUDE.md daily work-split.
  - Post-cutover plan: ~25-40 AI-days over 4-6 weeks (June-July 2026).

## Plan extraction record

Filled when the plans ship:

- May-23 plan path: `plans/active/promote_workflow_may23_cli_path_2026_05_10.md`
- Post-cutover plan path: `plans/active/promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`
- Spawned commit: <PM@sha — pending>
- Codex updates committed: enumerated as plan todos in spawned plans (per Post-Plan-Phase Codex Audit HARD RULE);
  shipped during plan execution, not at audit time.
- Question doc closes (status: closed) when: BOTH spawned plans have shipped their first phase (May-23 plan: paper-mode
  evidence run + first live-signing dry-run completed; post-cutover plan: state-machine consolidation Phase 1 shipped +
  UAC contract land).
