---
doc_type: plan
title: batch-live-design-symmetry
summary:
status: plan-spawned
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-api,
    deployment-service,
    deployment-ui,
  ]
scope: [engineer, admin]
tags: []
related:
  [
    unified-trading-pm/plans/archive/2026_07/master_to_live_defi_2026_05_23.md,
    unified-trading-pm/plans/archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md,
    unified-trading-pm/plans/archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md,
    unified-trading-pm/plans/active/features_repo_consolidation_2026_05_08.md,
    unified-trading-pm/plans/archive/2026_05/alerting_service_live_rules_2026_05_07.md,
    unified-trading-pm/plans/archive/2026_05/deployment_ui_lifecycle_tabs_2026_05_08.md,
    unified-trading-pm/plans/archive/promote_workflow_backtest_to_paper_to_live_2026_05_08.md,
    unified-trading-pm/plans/questions/codex_vs_citadel_infrastructure_specs_2026_05_08.md,
  ]
created: 2026-05-08
overview:
  Re-audit "batch = live, only fill source differs" SSOT — service code paths, UI surfaces, events, analytics, manifest
  schema, per-asset-group narratives, static enforcement. Gap-list vs the goal of total design-path symmetry, even at
  the cost of feeling like overkill.
type: question
plan_spawned: 2026-05-10
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-08
spawned_plan:
  [
    plans/active/master_to_live_defi_2026_05_23.md,
    plans/active/live_pipeline_mtds_mdps_features_2026_05_08.md,
    plans/active/writegate_honest_coverage_endtoend_2026_05_06.md,
    plans/active/simulation_scenarios_topology_price_shocks_2026_05_09.md,
  ]
related_codex:
  [
    unified-trading-pm/codex/04-architecture/batch-live-architecture.md,
    unified-trading-pm/codex/05-infrastructure/live-pipeline-architecture.md,
    unified-trading-pm/codex/05-infrastructure/replay-subsystem.md,
    unified-trading-pm/codex/02-data/pipeline-mode-partition.md,
    unified-trading-pm/codex/04-architecture/execution-modes-and-chain-resolution.md,
    unified-trading-pm/codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md,
    unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/benchmark-fills.md,
    unified-trading-pm/codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md,
    unified-trading-pm/codex/04-architecture/research-service-and-dart-integration.md,
    unified-trading-pm/codex/04-architecture/manual-trade-booking.md,
    unified-trading-pm/codex/04-architecture/alerting-batch-live.md,
    unified-trading-pm/codex/04-architecture/instruments-live-architecture.md,
    unified-trading-pm/codex/04-architecture/instruments-preflight-chain.md,
    unified-trading-pm/codex/04-architecture/features-service-architecture.md,
    unified-trading-pm/codex/04-architecture/live-strategy-config-hot-reload.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Batch = Live design symmetry — re-audit + gap list (overkill OK)

## Intent

The workspace SSOT is **"batch = live, same code path, same component interactions, only fill source differs"** —
declared in [`CLAUDE.md` § "Batch = Live: Unified Pipeline Architecture (CRITICAL)"](../../cursor-configs/CLAUDE.md) and
[`/codex/04-architecture/batch-live-architecture.md`](/codex/04-architecture/batch-live-architecture.md). It applies
across every asset_group (cefi / defi / tradfi / sports / prediction), every layer (data → features → ML → strategy →
execution → position → risk → alerting → reporting → UI → events), and every operational mode (backtest / paper / live).

The principle is well-stated. The implementation isn't equally well-distributed. The May-23 cutover lands two DeFi
archetypes on a real wallet for ≥7 continuous days; if the system has implicit asymmetries between "what the code does
in batch" and "what the code does in live" that we haven't surfaced, the cutover risk is _invisible bugs that fire only
on the live side_. The mitigation is not "be careful" — it's design-path symmetry so deep that the divergence between
batch and live is constrained to **one or two named seams** (execution fill source + data tick source) and every other
layer is bit-identical or provably equivalent.

This question doc is a **re-audit** with deliberate overkill on the symmetry bar. We don't want "batch and live are
mostly the same"; we want a list of every place where they diverge, every conditional branch on `RuntimeMode`, every
separate code path, every UI component that's mode-aware where it shouldn't be, every event type that has `LIVE_` /
`BATCH_` in its name where the mode should be a field, every analytics partition that splits where it should be unified,
every per-asset-group story that's implicit instead of explicit. Then we decide which of those divergences are essential
(the named seams) and which are accidental (drift to be fixed before May-23).

The audit pass below has **already been run** (by the agent on the operator's behalf, three parallel sub-agents covering
services / UI+events / codex). Findings are pre-populated. The operator now iterates with the agent on:

- Which gaps are May-23 cutover-blocking vs post-cutover scope.
- What the spawned plan looks like (one giant symmetry-cleanup plan, or a fan-out across asset_group masters +
  features-consolidation + UI repos + alerting plan).
- Which codex docs need new sections vs new files.
- What static enforcement (QG steps, AST sweeps, lint rules) we want before live.

**Bias**: prefer over-specifying the symmetry bar. If a sub-question feels like overkill, keep it — that's the point.
Real-trading correctness is non-negotiable; the cost of one extra paragraph in this doc is far lower than the cost of
catching a silent mode-divergence the day after live cutover.

## Question

### Block A — SSOT principle + scope alignment

A1. The principle is stated in two places (CLAUDE.md "Batch = Live" section +
`/codex/04-architecture/batch-live-architecture.md`). Are they bit-coherent, or is one of them ahead of the other? Audit
shows: **coherent** (both shipped 2026-05-08, both consolidate prior deletes). Verify there's no third place stating a
contradicting principle (e.g. an old codex doc, a service README, a plan body).

A2. Scope of "fill source differs" — is it ONE seam (execution-service fill source) or TWO (execution-service fill
source + data-tick source)? `batch-live-architecture.md` § 2 says four seams: data ingest, replay watermark, feature
compute, execution fill. Operator: are four seams correct, or should the principle compress to "fill source + data
source" (two seams) with replay + feature-compute being internal mechanics of those two?

A3. The "fill source" itself has two sub-modes per matching engine: `BENCHMARK` (always-fill, isolates strategy alpha)
vs `SIMULATED` (realistic L0/L1/L2/AMM matchers, measures execution alpha). So in batch we run BOTH paths (benchmark for
strategy P&L + simulated for execution-alpha attribution). In live we run real fills + simulated-shadow-fills (so we can
compute execution alpha = real - benchmark). Is this triple-path expectation codified anywhere in code, or only in
`cross-cutting/benchmark-fills.md`? Where does the simulated-shadow-fill computation actually run in live mode?

A4. Asset-group scope — does the principle apply _uniformly_ across cefi / defi / tradfi / sports / prediction, or are
there asset-group-specific exceptions? Audit found **per-asset-group narratives are missing** for CeFi, TradFi,
Prediction (only sports + defi have explicit batch=live docs). Is this a documentation gap to fill, or are
CeFi/TradFi/Prediction genuinely different shape?

A5. Operational mode axis — the workspace has at least three mode axes: `RuntimeMode` (BATCH | LIVE), `OperationalMode`
(BACKTEST | PAPER | LIVE | DEMO?), `BatchExecutionMode` (BENCHMARK | SIMULATED). Plus the strategy-lifecycle 9-phase
maturity (smoke → backtest_minimal → ... → live_stable). How do these axes compose? Is there an SSOT showing the
cartesian product of valid (`RuntimeMode`, `OperationalMode`, `BatchExecutionMode`, `MaturityPhase`) tuples + which ones
the system actually supports?

A6. Paper-trading is **live-data + simulated-fills**. Is paper a separate `RuntimeMode.PAPER` value or is it
`(RuntimeMode.LIVE, BatchExecutionMode.SIMULATED, MaturityPhase.paper_*)` composition? Audit found
`OperationalMode.PAPER` declared in `unified_api_contracts/internal/modes.py:196` — separate from `RuntimeMode`. Is the
composition explicit, or is paper handled ad-hoc in deployment-service `--mode paper`?

### Block B — Mode enums (clarity, conflation, layering)

B1. `RuntimeMode` SSOT lives at `unified_api_contracts/internal/modes.py:69-79`. Is this **the** canonical mode enum the
rest of the system reads, or are there competing enums?

- Audit finding: `unified-trading-system-ui/context/internal-contracts/schemas/modes.py:69-79` **redeclares**
  `RuntimeMode` in the UI context layer instead of importing from UAC. Drift hazard if UAC adds a value (e.g. PAPER).
- Audit finding: legacy `ServiceMode` enum referenced in some code per UAC docstring — fully retired or partially?
- Question: is there a UAC-internal-export rule violation here? Should the UI consume `RuntimeMode` from UAC via the API
  contracts package, never re-declare?

B2. `PipelineMode` (UAC `canonical/crosscutting/pipeline_mode.py:44-67`) is a **row-level data-source tag**
(BATCH_DATABENTO / BATCH_TARDIS / ... / LIVE_WEBSOCKET — 18 values), distinct from `RuntimeMode`. Per audit: this
distinction is documented in `pipeline-mode-partition.md` but is regularly confused at the call-site level (operators
conflating "the service is in batch mode" with "this row came from a batch source"). What's the right naming + lint
enforcement to keep them separate?

B3. `BatchExecutionMode` (UAC `unified_api_contracts.internal.execution.py`) gates BENCHMARK vs SIMULATED matcher
behaviour. Where is this set in live mode (when execution-service does real fills + shadow-simulated fills)? Is the
dual-path actually implemented, or only the benchmark side?

B4. `OperationalMode` (`PAPER` etc., UAC `unified_api_contracts/internal/modes.py:196`) — what's its full domain? Is it
(BACKTEST | PAPER | LIVE | DEMO | SHADOW)? Is it codified as a closed StrEnum + tested for round-trip?

B5. Strategy-lifecycle maturity (9 phases per `09-strategy/architecture-v2/strategy-lifecycle-maturity.md`): smoke /
backtest*minimal / backtest_1yr / backtest_multi_year / paper_1d / paper_14d / paper_stable / live_early / live_stable /
retired. How does this enum project onto `RuntimeMode`? E.g. `paper*\*`phases run
with`RuntimeMode=LIVE`+`BatchExecutionMode=SIMULATED`? Codified anywhere?

B6. Are there ANY other mode-shaped enums in the system that this audit might have missed? Search for
`class.*Mode.*Enum` workspace-wide and enumerate. Surface any that look unloved or redundant.

### Block C — Service-side symmetry (per repo)

C1. `strategy-service` — audit verdict: **mode-blind** (no `--mode` flag, no `if mode ==` branching). Verify by
re-grepping for `RuntimeMode` / `PipelineMode` / `BatchExecutionMode` / `mode` usage in service source. If any branching
exists, classify as essential-seam vs accidental-drift.

C2. `execution-service` — audit verdict: **fill-source seam not visible to grep**. The seam is likely DI-injected via
executor selection (matching_engine vs real-venue adapter). Is the seam:

- (a) A factory function `get_executor(runtime_mode, asset_group, venue) → Executor` with one switch in one file?
- (b) Per-venue executor classes that internally switch on mode?
- (c) Configured by deployment env vars only (no runtime branching at all — matcher class chosen at boot)? The right
  shape is (a) — single named seam. If (b) or (c), is the seam discoverable + auditable?

C3. `position-balance-monitor-service` — audit verdict: **mode-blind**. Verify. Should track positions identically
regardless of where fills came from.

C4. `risk-and-exposure-service` — audit verdict: **mode-blind**. Verify. Should fire identical risk gates in both modes.

C5. `alerting-service` — audit verdict: **assumed mode-blind**, not deeply verified. Per
`/codex/04-architecture/alerting-batch-live.md` — alerting parity is documented. But ServiceEmissionPolicy has 4 states
(PUBLISHED_OK / PUBLISHED_DEGRADED / STALE / BLOCKED_CRITICAL) per recently-shipped UTL `emission_publisher.py`. Do
alert rules fire identically in batch + live, or does batch suppress some alerts (e.g. data-freshness alerts that are
nonsensical against a frozen historical replay)?

C6. `market-tick-data-service` (MTDS) — audit verdict: **seam clean** (splits on SOURCE, not on `RuntimeMode`). Per
`pipeline-mode-partition.md` shipping table, every parquet stamps `pipeline_mode={batch_*|live_websocket}`. Are there
MTDS code paths that DON'T stamp pipeline_mode (legacy adapters, scripts, one-off backfills)?

C7. `market-data-processing-service` (MDPS) — audit verdict: **separate code paths**. `cli/parser.py:45-58` has
`_mode_dispatch_handler` routing to `LiveModeHandler.run()` (live) vs `process_candles_handler` (batch). Two separate
modules, no shared base class. **HIGH DRIFT RISK**:

- Schema parity not enforced — could batch emit `(open, high, low, close, volume)` while live emits
  `(open, high, low, close, volume, vwap)` and nothing catches it?
- Error handling parity not enforced — could batch raise on a malformed tick while live silently drops?
- Manifest recording parity not enforced — could batch use `record_captured` correctly while live use a stale path?
  What's the contract that keeps the two handlers in lock-step? Does it exist?

C8. `features-*-service` (currently 5-6 repos, consolidating per `features_repo_consolidation_2026_05_08.md`) — audit
verdict: **assumed mode-blind** (compute identical features regardless of input source). But per
`features-service-architecture.md` — sports + calendar feature families have **NO live handler shipped yet**. So
"mode-blind" is true for the families that exist in live, but feature families are split into batch-only and batch+live
subsets. What's the gap-fill plan? Is sports feature family blocking May-23?

C9. `instruments-service` — audit verdict: **mode-blind for definitions** but has an `instruments-live` exception per
`/codex/04-architecture/instruments-live-architecture.md` (live discovery via venue API + per-venue trading-calendar
enrichment). Is the exception properly bounded — definitions are mode-blind, but discovery has a live mode? Or is the
exception leaking into definition shape?

C10. `deployment-service` — audit verdict: **`--mode` is a CLI convention**, not a service-internal branching point.
Mode flows through `cluster.py` / `deploy_missing.py` / `shard_builder.py` into VM env vars
(`RUNTIME_MODE=batch|live`) + launched VM CLI args (`--mode batch|live`). Is the mode-flow audit-trail clean (one place
where mode is parsed, one place where it's set in env, one place where it's passed to the VM)? Or are there `--mode`
parses scattered across multiple CLI commands with no single seam?

C11. `client-reporting-api` — audit found 29+ instances of `is_mock_mode()` checks. These are `DATA_MODE` (mock vs
real), orthogonal to batch vs live. But the call-site density is suspicious — is the API layer forcing the consumer to
handle mock-vs-real, or is mock-mode handled at a single boundary? Same question for batch vs live in this service: does
it serve the same PnL/NAV shape regardless of whether data is from batch backtest or live trading?

C12. Other services — `unified-events-interface`, `unified-features-interface`, `unified-cloud-interface`,
`unified-config-interface`, all `unified-*-library` packages. Are any of these mode-aware where they shouldn't be? Per
audit, UCI `cloud_interface/constants.py` references `RuntimeMode` — for what? Is mode legitimately needed at the cloud
layer (e.g. choosing different bucket roots), or is this a leak?

### Block D — MDPS + execution-service code-path separation (concrete incidents)

D1. **MDPS dual-handler contract** — `process_handler.py` (batch) vs `live_mode_handler.py` (live). What's the _minimum
contract_ both handlers must satisfy?

- Identical output schema (column names + types)?
- Identical error-handling taxonomy (typed exceptions, classified error reasons)?
- Identical `record_captured` / `record_empty` / `record_failed` contract?
- Identical write-gate semantics (NaN ratio, row-count > 0, schema match, cluster coverage for bundled types)?
- Identical per-instrument progress events (`INSTRUMENT_PROCESSED` with row counts)?

Is any of this enforced statically (shared base class with abstract methods, AST sweep validating both call
` ManifestWriter.record_captured`, schema validation at both write-sites)?

D2. **Refactor proposal** — should MDPS move to ONE handler with mode passed as a constructor param (the matching-engine
pattern) + the only mode-conditional behaviour is the data-source iteration (batch: scan historical date range; live:
subscribe to PubSub timer ticks)? Or is the dual-handler shape fundamentally correct because batch + live have genuinely
different orchestration?

D3. **Execution-service fill seam** — the seam should be ONE switch:
`get_executor(runtime_mode) → BenchmarkExecutor | RealVenueExecutor`. Is the actual implementation that clean? Walk the
code path from a strategy emitting an instruction → execution-service receiving it → fill being produced. Is there ONE
seam, or N scattered checks?

D4. **Shadow-simulated fills in live mode** — per Block A3, in live we should run real fills + simulated-shadow-fills
(so execution alpha can be computed). Is this implemented? Where? Or is execution alpha currently only measurable
post-hoc by replaying batch on the same configuration?

D5. **Cutover-criticality** — D1 + D3 are May-23 cutover-blocking (a silent batch/live divergence in MDPS or
execution-service is the most expensive bug class we can ship). D2 + D4 are post-cutover scope unless they unblock
D1/D3. Operator: confirm scoping.

### Block E — Manifest + data parity (schema contract)

E1. **`pipeline_mode` partition shipping** — per `gcs_migration_bundle_pipeline_mode_2026_05_08.md` — Phase 1A landed
(UAC enum). What's left? Manifest writer integration, reader fallback chain, per-asset-group migration of legacy
parquets, deletion of fallback paths post-migration. What's the cutover-readiness state today?

E2. **Schema parity enforcement** — per CLAUDE.md "Live = batch — same data, same fields, same timing semantics" key
rule:

- Banned: separate live-only data_types (`LINEUPS_PRE_MATCH` vs `LINEUPS_POST_MATCH`).
- Banned: distinct field sets between live + batch parquets.
- Banned: deriving `available_at` at read-time from the live-batch mode flag. Is this enforced statically? Audit found
  **NO** QG step / AST sweep enforcing it. The rule lives only in CLAUDE.md prose. **Cutover-blocking**: should we add a
  QG STEP 5.XX that walks every `data_type` declaration in UAC + asserts identical shape regardless of pipeline_mode?

E3. **`available_at` is per-row, write-time, equal to live-pipeline-arrival** (workspace-wide rule). Per CLAUDE.md —
every shard's parquet has `available_at`; UTL's `record_captured` calls `assert_available_at_present`. Verify that this
assertion fires in BOTH MDPS handlers (batch + live), in BOTH MTDS adapter paths, in BOTH features-\* compute paths. Any
path that doesn't go through `record_captured`?

E4. **`empty_confirmed` reasons differ per asset-group** — per CLAUDE.md key rule: sports/prediction CAN have
empty*confirmed at instrument-day grain; cefi/defi/tradfi CANNOT (only venue-level rules). This is a \_per-asset-group*
SSOT — does the catalog-aware write-gate enforce it identically in batch + live, or only in batch (where the catalog is
statically available)?

E5. **Cluster-validation parity** — `BUNDLED_DATA_TYPES` (options_chain, futures_chain,
prediction_canonical_question_group, sports per-fixture-bundle) require `expected_root_clusters` + `cluster_extractor`
at `record_captured`. Verify this kwargs is passed in BOTH batch and live writes, not just batch.

E6. **Manifest concurrency principle** — read-once + per-date freshness check + write-time CAS. Does the live pipeline
obey this when MTDS-live and replay-fill processes both write to the same manifest for the same
`(asset_group, venue, day)`? `replay-subsystem.md` references a `replay_watermark` KV; is the manifest CAS path also
live-vs-replay aware?

E7. **Reader fallback chain** — `pipeline_mode` partition + `category=` legacy hive-vocab + `day=*/` prefix drift. Per
`pipeline-mode-partition.md` — fallback chain is documented for a ≤30d post-migration window. Is the chain identical for
batch consumers + live consumers? Or do live consumers skip the fallback (assuming they only read live_websocket
parquets)?

### Block F — UI symmetry (DART, dashboard, ops, research)

F1. **DART** — per `/codex/04-architecture/research-service-and-dart-integration.md` +
`09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md`, DART is the manual-trade gate (6 lanes: DeFi
swap, lend/stake, CeFi order, ML training, sports bet, prediction market). It's _not_ a separate UI repo — it's a
tab/surface in `unified-trading-system-ui` (verify exact location). Does DART distinguish backtest / paper / live in its
UI, or does it treat them as the same submission with a `mode` field on the manual instruction?

F2. **Dashboard hardcoded mock values per mode** — audit found
`unified-trading-system-ui/app/(platform)/dashboard/page.tsx:58-125` uses `useRoleKPIs(isLive)` with **hardcoded
different values** based on `isLive` boolean ("Real-time" vs "T+1 06:00" freshness, "$142.4K" vs "$138.9K" P&L). This is
a mock-mode artefact for dev experience, but the _shape_ is wrong: the component branches on mode BEFORE the data fetch,
instead of fetching mode-blind data + rendering it identically. Cutover-relevant? Probably post-cutover (it's a
dashboard demo affordance), but the pattern should be flagged so it doesn't propagate.

F3. **Ops dashboard mode toggle** — audit found `(ops)/ops/page.tsx` uses `useState<"live" | "batch">("live")` toggle
with mode as UI state enum. Is this a legitimate filter (operator wants to see "current live deployments only" or
"current batch backtests only") or a code-path branch (different data source, different rendering logic)? If the former:
fine. If the latter: violation.

F4. **Research / ML page** — audit found `(platform)/services/research/ml/page.tsx` has "Live Predictions — only in live
mode" feature flag that **disables** the batch path entirely. This is a hard violation of "same code path" — predictions
should be visible in both modes, with the `mode` field telling the operator whether the prediction is from a backtest
run or a live model serving. What's the design decision: hide-in-batch (current) vs always-show-with-mode-tag (desired)?

F5. **Independent mode state across surfaces** — audit found multiple pages each maintain `useState<"live"|"batch">`
independently. There's no shared `ModeContext` provider. **Cutover-relevance**: probably medium (ops UX, not
correctness), but the pattern means a mode toggle on one tab doesn't sync to another tab — operator confusion risk.

F6. **deployment-ui mode handling** — `DeploymentHistory.tsx` uses `{deployment.deploy_mode === "live" && (...)}`
conditional rendering. Is `deploy_mode` a _display filter_ (operator wants to see only live deployments) or a
_behavioural switch_ (different rendering logic per mode)? The line between the two is the violation surface.

F7. **Per `deployment_ui_lifecycle_tabs_2026_05_08.md`** — separate tabs for backtest / paper / live deployments? Or one
tab with a mode column + filter chip? The plan should already be specifying this; verify.

F8. **Mock-vs-real conflation with batch-vs-live** — UI has 5 mock axes (`VITE_MOCK_API`, `VITE_SKIP_AUTH`,
`CLOUD_MOCK_MODE`, `DISABLE_AUTH`, `MOCK_STATE_MODE`) per CLAUDE.md "Local Development". These are **orthogonal** to
batch-vs-live (mock=true means widget fixtures regardless of mode; mock=false means real API calls in either mode). But
audit found dashboard hardcodes mock values _per mode_ — conflating the two axes. Is there a UI-architectural rule
"mock-vs-real and batch-vs-live are independent, never conflated in component code"? If not, codify it.

F9. **PnL view symmetry** — does `unified-trading-system-ui` have ONE PnL component that renders both backtest PnL and
live PnL identically (mode-blind), or separate components? Per workspace SSOT, should be one component. Verify.

F10. **Position page, fills page, alerts page** — same question. Mode is a filter, not a code-path branch.

F11. **DART manual-trade gate UI** — when an operator clicks "Promote to live" (per the sibling promote-workflow
question doc), is the click handler mode-aware (different POST endpoint per mode) or mode-blind (same endpoint, mode in
body)? The mode-blind shape is the right one.

### Block G — Events + analytics (taxonomy, partition, naming)

G1. **`LIVE_` prefix in event TYPE names** — audit found `deployment-service/deployment_service/events.py:20-50`
declares `VMEventType` with `LIVE_HEALTH_CHECK_PASSED`, `LIVE_HEALTH_CHECK_FAILED`, `LIVE_ROLLBACK_EXECUTED`. **HARD
VIOLATION** of "mode is a field, not part of the event name" — there's no `BATCH_HEALTH_CHECK_PASSED` because batch
doesn't health-check VMs the same way, but the right shape is `HEALTH_CHECK_PASSED` with `mode` field on the event
payload. Cutover-relevant? Medium — these events are deployment-internal, not strategy-lifecycle, but the precedent is a
foot-gun. Should they be renamed before May-23 (semver-bump VMEventType in UAC) or post-cutover?

G2. **UI type mapping mirror** — `deployment-ui/src/types/index.ts` mirrors the `LIVE_` prefix in TypeScript. So
renaming the Python enum requires synchronised UI rename. Is there a generation pipeline (UAC → TS types) that would
handle this automatically, or is it a manual sync?

G3. **Strategy lifecycle events** — per Block F1 of the promote-workflow question doc, the lifecycle events should be
`STRATEGY_PROMOTED_TO_CANDIDATE` / `STRATEGY_PROMOTED_TO_PAPER` / `STRATEGY_PROMOTED_TO_LIVE`. These ARE mode-named
(paper/live in the event name), but the names refer to **lifecycle phases**, not runtime modes — so the question is
whether lifecycle phase IS a legitimate first-class axis to bake into event names. Per
`09-strategy/architecture-v2/strategy-lifecycle-maturity.md` (9-phase enum) — yes, phase is canonical, so event names
mentioning phase are fine. But should they parameterise on `target_phase` instead (single
`STRATEGY_LIFECYCLE_TRANSITION` event with `from`/`to`)? Trade-off discussion.

G4. **Audit log / event archive** — `gs://{pid}-events/events/{service}/{YYYY-MM-DD}/{correlation_id}/hour={H}/*.jsonl`
(per CLAUDE.md "No fire-and-forget VM launches"). Does this partition include `pipeline_mode` so events from a
batch-replay correlation_id vs a live-prod correlation_id can be separated? Or are events all in one partition +
consumers must filter by event content?

G5. **Analytics events** — distinct from lifecycle events: button clicks, page views, filter changes, telemetry. Audit
found **no unified analytics event schema**. Are these emitted at all today (would be visible in `gs://{pid}-events/...`
paths or via Firebase analytics or via a dedicated analytics service)? If emitted, are they mode-aware (which is fine —
analytics legitimately wants to know "operator looked at the live-prod dashboard 50× more than the batch-backtest
dashboard") or do they conflate?

G6. **Reconciliation + audit-trail events** — every state transition needs an event for reconstruction. Per master plan
Group F item 18 (batch-vs-live recon green at May-23) — does the recon job emit `BATCH_VS_LIVE_RECON_GREEN` /
`BATCH_VS_LIVE_RECON_DRIFTED` events? Where are they consumed (alerting, dashboard, audit log)?

G7. **Per-asset-group event taxonomy** — sports-specific events (`MATCH_KICKOFF`, `LINEUPS_AVAILABLE`),
prediction-specific (`MARKET_RESOLVED`, `MARKET_SETTLED`), defi-specific (`CHAIN_REORGED`, `RPC_OUTAGE`), cefi-specific
(`VENUE_API_DEGRADED`). Are these mode-blind (fire identically in batch backtest replay + live), or are they live-only?
If live-only, then `available_at` semantics for these in batch must be reconstructed from historical sources — per the
"available_at is write-time" rule.

G8. **Internal contracts schemas** — `unified-trading-system-ui/context/internal-contracts/schemas/events.py` mirrors
UAC events. Same drift concern as B1 (UI redeclares enums); should auto-import from UAC.

### Block H — Mock-vs-real ↔ batch-vs-live independence

H1. **Five mock axes orthogonal to batch/live** — per CLAUDE.md "Local Development" — `VITE_MOCK_API` / `VITE_SKIP_AUTH`
/ `CLOUD_MOCK_MODE` / `DISABLE_AUTH` / `MOCK_STATE_MODE`. Verify nothing in the workspace conflates `mock=true` with
`batch=true`. Audit surfaced one conflation (dashboard hardcoded values per mode + treating `isLive=true` as "real
data"). Are there others?

H2. **Tier 0 / Tier 1 / Tier 2 dev-tier model** vs `RuntimeMode` — Tier 0 is mock-API + emulators; can a Tier 0 dev
session run with `RuntimeMode=BATCH` or `RuntimeMode=LIVE`? Or does tier imply mode? Per
`runtime-tiers-and-deployment.md` — tier is orthogonal to mode (a Tier-2 session can run both batch + live; a Tier-0
session typically batch only because Tier-0 has no real venue connection). Verify.

H3. **Test fixtures** — does the workspace have test fixtures that exercise the same component in both batch and live
mode (e.g. a parameterised pytest fixture `mode=["batch", "live"]`)? Per the "live = batch" SSOT, every component test
should run twice (once per mode) with identical assertions. If not, that's an enforcement gap.

H4. **CI smoke harnesses** — per `e2e-testing/scripts/` — are there mode-parametric smoke tests? Or are smokes
mode-specific (batch smoke vs live smoke as separate harnesses)?

### Block I — Per-asset-group symmetry

I1. **CeFi (spot, perp, options, futures)** — audit found NO per-asset-group batch=live SSOT doc for cefi. The
architecture is implied by the unified matcher pattern (L2Matcher for book depth) but no narrative. Gap: does cefi need
a dedicated codex doc?

I2. **TradFi (futures, ETFs, options)** — audit found NO per-asset-group batch=live SSOT doc. Shard atoms differ
(futures: bundled; ETFs: per-instrument; options: 11-cluster ES.OPT taxonomy). How does each settle in live?
Walk-forward via expiry rollover for futures + options. Live tradfi data sources (Databento for tick, what for live
execution?). May-23 cutover doesn't include tradfi live trading, but the doc gap is post-cutover scope.

I3. **DeFi (carry_staked_basis + leveraged_funding_arb)** — audit found `defi-execution-overview.md` +
`defi-phase3-infrastructure.md` cover defi. Chain resolution via CHAIN_ENV (mainnet/testnet/fork). Fork-based backtest.
Verify the batch=live story is complete for the May-23 archetypes specifically: every component (LST yields, perp
funding, gas, oracle prices, RPC) has both a batch source and a live source + the seam is one switch.

I4. **Sports** — audit found `batch-live-architecture.md:§7 Sports-specific notes` — SportsMatchingEngine documented.
But `features-service-architecture.md` says **sports feature family has no live handler yet** (p1-todo-10). Sports is
not May-23 cutover-blocking, but the gap is enumerated.

I5. **Prediction markets** — audit found NO explicit live-handler integration doc. Canonical_question_group bundling +
BENCHMARK mode untested in real-time live context. Prediction markets are post-May-23 (per master plan), so the gap is
post-cutover. But the audit should surface it now.

I6. **Cross-asset-group story** — once each asset_group has its narrative, is there ALSO a meta-doc explaining how the
same `BatchExecutionMode` enum applies uniformly + the matcher selection logic + the seam shape? Or is each asset_group
its own story?

### Block J — Strategy lifecycle ↔ mode integration

J1. **9-phase maturity** projects onto `RuntimeMode` how? Mapping table (proposed):

- smoke / backtest_minimal / backtest_1yr / backtest_multi_year → `RuntimeMode=BATCH`, `BatchExecutionMode=BENCHMARK`
  (alpha isolation) + shadow `SIMULATED` (alpha attribution)
- paper_1d / paper_14d / paper_stable → `RuntimeMode=LIVE`, `BatchExecutionMode=SIMULATED`, `OperationalMode=PAPER`
- live_early / live_stable → `RuntimeMode=LIVE`, real venue executor, shadow `SIMULATED` (ongoing alpha attribution)
- retired → mode irrelevant, deployment shut down Is this mapping codified in UAC, or implicit? Codify it.

J2. **Promotion gates per phase transition** (per `strategy-lifecycle-maturity.md`) — paper_14d → paper_stable requires
"≥30d continuous, no circuit-breaker events". Are these gates mode-aware (different gates batch → paper vs paper →
live), or mode-blind (same gate shape, different thresholds)?

J3. **Demotion / pause / retire** — `STRATEGY_LIFECYCLE_DEMOTED` audit event exists. Does demote-to-paper carry the
strategy back through the SAME pipeline (live → paper means re-engaging matching engine + suppressing real fills), or is
it a separate code path?

J4. **Cross-promote-workflow integration** — the sibling
[`promote_workflow_backtest_to_paper_to_live_2026_05_08.md`](promote_workflow_backtest_to_paper_to_live_2026_05_08.md)
question doc covers the promotion workflow. The mode-symmetry question feeds directly into it — the workflow's
cross-mode transitions only work if the lifecycle states project onto modes cleanly.

### Block K — Replay handoff symmetry

K1. **Replay subsystem** (per `05-infrastructure/replay-subsystem.md`) — gap-fill via separate process, emits through
SAME Redis Streams as live, smooth handoff via `replay_watermark.{asset_group}.{shard_key}` KV. Anti-pattern: don't
introduce `pipeline_mode=replay` (output is `live_websocket` indistinguishably). Verify the replay process is
implemented today (not just doc'd).

K2. **`available_at` for replay rows** — per spec: original-time `available_at` (NOT replay-execution time). This is
correct (replay should be invisible to downstream consumers). Verify the replay process actually stamps original-time,
not now-time.

K3. **Multi-hour-outage backstop** — `REPLAY_BACKSTOP_REACHED` event + manual-intervention gate. Is the gate wired to
alerting? Is the gate wired to strategy-service auto-pause?

K4. **Backtest = batch + replay** — is a backtest run actually a `RuntimeMode=BATCH` execution against historical
parquets, or is it a `RuntimeMode=LIVE` execution with replay subsystem in front of it (so the strategy code thinks it's
live)? Per SSOT the latter (more symmetric), but verify.

### Block L — Static enforcement (QG, lint, AST)

L1. **No QG enforcement of "no separate live-only data_types"** — audit finding. Should we add QG STEP 5.XX that walks
UAC + asserts every `data_type` declared in `pipeline_mode=live_*` also exists in `pipeline_mode=batch_*` (and vice
versa)? Cutover-relevance: medium — the rule lives only in CLAUDE.md prose today.

L2. **No QG enforcement of "no mode-conditional branching outside the seam"** — audit finding. Should we add QG STEP
5.XX that AST-walks every `if mode ==` / `if runtime_mode ==` / `match runtime_mode:` callsite + asserts the file is in
the seam allowlist (execution-service `executor_factory.py`, MTDS `umi_tick_provider.py` source-routing,
deployment-service `cli/`). Cutover-relevance: high — enforcement here is the structural guard.

L3. **No QG enforcement of "RuntimeMode imported from UAC, not redeclared"** — audit finding. UI redeclares enum. Should
be a one-line ruff rule `flake8-class-redefine` or similar, OR a workspace-grep step asserting `class RuntimeMode`
appears in exactly ONE file (UAC).

L4. **No QG enforcement of "events use mode field, not LIVE\_ prefix in name"** — audit finding
(`VMEventType.LIVE_HEALTH_CHECK_PASSED`). Should be an AST sweep: walk every StrEnum named `*EventType` + assert no
member starts with `LIVE_` / `BATCH_` / `PAPER_`. Cutover-relevance: low (deployment-internal events are not on the
strategy-lifecycle critical path), but precedent matters.

L5. **No QG enforcement of "no separate live-only fields"** — audit finding. Schema parity per pipeline_mode. Should be
a per-data_type schema introspection at write-time + assertion all writers within a data_type produce identical column
sets.

L6. **No QG enforcement of "matching engine fill seam is one switch"** — should be a QG step asserting `get_executor`
(or whatever the factory is named) appears in exactly one file in execution-service + has all branching contained.

L7. **`assert_available_at_present` is enforced by UTL `record_captured`** — per CLAUDE.md. Verify this fires in every
write path. AST sweep walking writer call-sites + asserting they go through `record_captured` (not direct parquet
writes).

L8. **Test-mode parameterisation** — per H3 above, should we have a workspace lint that every component test asserts
identical behaviour for `mode=BATCH` and `mode=LIVE`? Probably overkill; trade-off discussion.

### Block M — Cross-cutting integration

M1. **Alerting** — alert rules wired identically batch + live? `alerting_service_live_rules_2026_05_07.md` plan
shipping. Verify.

M2. **Position-balance-monitor** — registers strategy's accounts/wallets identically across modes? Per Block C3 — yes,
mode-blind.

M3. **Risk + circuit-breakers** — mode-blind, verify. Per master plan Group F23 — kill-switches must be wired in live;
how do we test the kill-switch in batch mode? Is there a `BatchExecutionMode=DRILL` for chaos testing?

M4. **Reporting** — sibling
[`client_reporting_pnl_attribution_mvp_2026_05_10.md`](client_reporting_pnl_attribution_mvp_2026_05_10.md). PnL
reporting must show backtest PnL + paper PnL + live PnL with identical schema; mode is a filter, not a separate API
endpoint.

M5. **PnL attribution** — strategy alpha vs execution alpha decomposition must be possible in BOTH modes. In batch: easy
(always-fill = strategy alpha; matched = strategy + execution). In live: requires shadow-simulated fills. Per Block A3.

M6. **Custody + treasury** — sibling `wallet_treasury_client_flow_post_trade_readiness_2026_05_08.md`. Custody is
live-only by definition (no real wallet for batch backtest). Mode-asymmetric here, but legitimately so. Verify the
asymmetry is named + scoped.

M7. **API keys + credentials** — sibling `api_keys_wallets_accounts_readiness_2026_05_08.md`. Live keys vs testnet keys
vs no keys (batch). Per workspace rule "execution-service fetches from Secret Manager and injects at runtime". Verify
the credential-shape is uniform (same dict shape with different values), not different code paths per mode.

M8. **DR + reconciliation** — sibling `disaster_recovery_reconciliation_circuit_breakers_2026_05_08.md`. Recon job is by
definition cross-mode (compare batch backtest result vs live result for the same configuration). Recon process should be
mode-blind shape; result diff is the output.

M9. **Master plan Group F item 18** — "batch-vs-live recon green at May-23". This IS the symmetry verification gate.
What does "green" mean concretely (acceptable PnL drift threshold, slippage drift threshold, fill-count drift
threshold)? Is it codified?

### Block N — End-to-end reality check

N1. **Could Ikenna run the full symmetry test today** for `carry_staked_basis`? Concretely:

- Run backtest (mode=batch, BENCHMARK matcher) over last 60d → get strategy alpha curve
- Run backtest (mode=batch, SIMULATED matcher) same data → get strategy + execution alpha curve
- Difference = execution alpha attributable to fill assumptions
- Run paper (mode=live, SIMULATED matcher, real venue testnet) → get paper PnL curve
- Run live (mode=live, real venue executor + shadow SIMULATED) → get real fills + simulated-shadow fills
- Reconciler computes `live - shadow = realized execution alpha`, compares to
  `simulated - benchmark = predicted execution alpha`
- Symmetry green when `realized ≈ predicted` within tolerance ...without writing any new code. What's the gap?

N2. **Service-readiness checklist coverage** — per master plan Groups A-G, 23 items per service. Which items relate to
batch=live symmetry?

- F17: paper-trade smoke green
- F18: batch-vs-live recon green
- F20: backtest fidelity (real gas, matching engine, cost+yield precision)
- F21: 2-year batch backtest run
- F23: circuit breakers + kill switches + alerting + auto-recovery Each item depends on symmetry. If any of (F17, F18,
  F20, F21, F23) is RED for May-23, this audit is cutover-blocking.

N3. **Cutover-blocking subset** — minimum-viable symmetry for May-23 (DeFi-only, two archetypes, real wallet ≥7
continuous days):

- DeFi batch=live narrative (Block I3) verified
- MDPS dual-handler contract (Block D1) at least documented + manually verified parity
- Execution-service fill seam (Block D3) discoverable + audited
- `pipeline_mode` partition (Block E1) shipped end-to-end on DeFi parquets
- LIVE\_ event-prefix (Block G1) tolerated as-is (rename post-cutover)
- L2 + L3 + L4 + L5 + L6 (Block L static enforcement) — at minimum L2 for execution-service + L7
  (`assert_available_at_present`) Confirm with operator.

N4. **Cost of overkill** — every Block has sub-questions that feel like overkill (e.g. L8 mode-parametric tests for
every component). Operator should explicitly mark which blocks are essential vs nice-to-have so the spawned plan doesn't
drown in scope.

## What "answered" looks like

- **Spawned plan** — either a single workspace-wide `plans/active/batch_live_symmetry_<date>.md` or a fan-out across
  asset_group masters + features-consolidation + alerting + UI repos. Plan body lists every gap from Audit findings
  below + assigns each to a phase + cites exact file:line + names the codex SSOT it touches.
- **Codex SSOTs** — at minimum:
  - NEW: `/codex/04-architecture/cefi-batch-live.md` (per-asset-group narrative — currently missing)
  - NEW: `/codex/04-architecture/tradfi-batch-live.md` (per-asset-group narrative — currently missing)
  - NEW: `/codex/04-architecture/prediction-batch-live.md` (per-asset-group narrative — currently missing)
  - UPDATE: `/codex/04-architecture/batch-live-architecture.md` — add cross-asset-group meta + mode-axis composition
    table + LIVE_event-prefix anti-pattern + UI mode-context guidance
  - UPDATE: `/codex/06-coding-standards/quality-gates.md` — document new STEP 5.XX entries for static enforcement
    (L2/L3/L4/L5/L6/L7)
  - UPDATE: `/codex/05-infrastructure/live-pipeline-architecture.md` — explicit replay-watermark integration with
    manifest CAS
  - NEW: `/codex/06-coding-standards/mode-axis-discipline.md` — codifies RuntimeMode + PipelineMode +
    BatchExecutionMode + OperationalMode + MaturityPhase composition + which axis is the SSOT for what
- **Static enforcement landed** — at minimum L2 (mode-conditional branching AST sweep) + L7
  (`assert_available_at_present`) + L3 (RuntimeMode redeclaration ban) for May-23. L1/L4/L5/L6 post-cutover.
- **End-to-end symmetry test ran for `carry_staked_basis`** — per N1 — backtest BENCHMARK + backtest SIMULATED + paper +
  live + shadow-simulated + recon green within tolerance.
- **Master plan Group F items 17/18/20/21/23 all green** for both May-23 archetypes (`carry_staked_basis` +
  `leveraged_funding_arb`).
- **Cross-question alignment** — sibling question docs (`promote_workflow_*`, `client_reporting_*`,
  `risk_simulations_*`, `api_keys_wallets_*`, `disaster_recovery_*`) cite this doc's mode-axis SSOT as authoritative.
- **No silent divergence** — every place where batch and live diverge in code is a _named seam_ listed in the SSOT, not
  an _accidental drift_.

## Audit findings (pre-populated by 2026-05-08 audit pass)

The audit was run by three parallel sub-agents covering services / UI+events / codex. Findings are tagged by block.

### Service-side (Block C, D, E, K, L)

- **RuntimeMode SSOT exists** at `unified-api-contracts/unified_api_contracts/internal/modes.py:69-79` (BATCH | LIVE).
  Canonical, replaces legacy `ServiceMode`.
- **PipelineMode SSOT exists** at
  `unified-api-contracts/unified_api_contracts/canonical/crosscutting/pipeline_mode.py:44-67` (18 closed-set values).
  Phase 1A shipped 2026-05-08.
- **MDPS dual-handler split** at `market-data-processing-service/cli/parser.py:45-58` — `_mode_dispatch_handler` routes
  to `LiveModeHandler.run()` (live) vs `process_candles_handler` (batch). HIGH DRIFT RISK — no shared base class, schema
  parity not statically enforced. Cutover-blocking.
- **MDPS `--mode` CLI** at `cli/parser.py:229-236` (choices: batch | live). Standard convention per CLAUDE.md.
- **Strategy-service** — no `--mode` flag, no mode branching in service source. ✅ Mode-blind.
- **Execution-service** — fill-source seam not visible to grep; likely DI-injected via executor factory. ⚠️ Seam not
  auditable from grep alone — needs explicit codex SSOT pinning the seam location.
- **Position-balance-monitor / risk-and-exposure** — no mode branching detected. ✅ Mode-blind (verify by deeper read).
- **Alerting-service** — alert rules per `alerting-batch-live.md` documented as parity-required; runtime verification
  pending live-rules plan completion.
- **MTDS** — `pipeline_mode` stamped per row via SOURCE_PRIORITY round-trip. ✅ Seam clean (splits on source, not on
  RuntimeMode).
- **Features-\* services** — mode-blind for compute paths. ⚠️ Sports + calendar feature families have NO live handler
  shipped (per `features-service-architecture.md` p1-todo-10). Not May-23 blocking but enumerated.
- **Instruments-service** — definition-side mode-blind. ⚠️ `instruments-live` exception documented; verify the exception
  is bounded.
- **Deployment-service** — `--mode` flows from CLI → VM env vars (`RUNTIME_MODE`) → launched VM CLI args. ✅ Single
  seam.
- **Cloud-interface (UCI)** — `cloud_interface/constants.py` references `RuntimeMode`. ⚠️ Verify legitimacy (is mode
  genuinely needed at the cloud layer, e.g. bucket selection, or is this a leak).
- **Manifest schema enforcement** — UTL `ManifestWriter` does NOT validate that batch and live writers produce identical
  column sets per data_type. ⚠️ Static enforcement gap (Block L5).
- **`assert_available_at_present`** — UTL helper exists, called inside `record_captured`. Verify every write-path goes
  through `record_captured` (not direct parquet writes). AST sweep candidate.
- **No QG enforcement** of "no separate live-only data_types" / "no mode-conditional branching outside seam" /
  "RuntimeMode imported from UAC". Block L gaps.

### UI / events / analytics (Block F, G, H)

- **UI redeclares RuntimeMode** at `unified-trading-system-ui/context/internal-contracts/schemas/modes.py:69-79`. Should
  import from UAC.
- **Dashboard hardcodes mock values per mode** — `app/(platform)/dashboard/page.tsx:58-125` uses `useRoleKPIs(isLive)`
  returning different hardcoded values for live vs batch. Conflates mock-mode with batch-vs-live. Demo-grade affordance,
  not correctness.
- **Ops dashboard mode toggle** — `(ops)/ops/page.tsx` has `useState<"live"|"batch">` toggle. Verify it's a display
  filter, not a code-path switch.
- **ML / research feature flag** — `(platform)/services/research/ml/page.tsx` "Live Predictions — only in live mode"
  disables batch path entirely. Hard violation of "same code path".
- **Independent mode state across surfaces** — multiple pages each maintain their own mode state. No shared
  `ModeContext` provider.
- **deployment-ui mode rendering** — `DeploymentHistory.tsx` has `{deployment.deploy_mode === "live" && (...)}`. Verify
  boundary between display filter (fine) vs code-path branch (violation).
- **Deployment events use `LIVE_` prefix in event TYPE names** — `deployment-service/deployment_service/events.py:20-50`
  declares `VMEventType.LIVE_HEALTH_CHECK_PASSED` / `.LIVE_HEALTH_CHECK_FAILED` / `.LIVE_ROLLBACK_EXECUTED`. Hard
  violation of "mode is a field, not part of the event name". UI mirrors at `deployment-ui/src/types/index.ts`.
  Cutover-relevance medium — internal events, not strategy-lifecycle.
- **API contracts mode-blind** — `unified-trading-api/unified_trading_api/routes/events.py:43-109` declares
  `EconomicEventItem`, `EventImpactPredictionItem`, `NewsFeedItemModel`, `EventPositionItem` with NO `mode` or
  `data_source` field. ⚠️ Either intentional (mode is implicit from request context) or a gap (should expose mode for
  client filtering).
- **No mode partition in `gs://{pid}-events/` event archive paths** — verify whether `pipeline_mode` is in the path
  schema or only in the JSONL body.
- **Analytics events** — no unified analytics event schema found in audit. Likely Firebase analytics or per-UI emission,
  not a workspace SSOT.

### Codex SSOT (Block A, I, J, K)

- **Principle docs coherent** — `CLAUDE.md` "Batch = Live" + `/codex/04-architecture/batch-live-architecture.md`
  (consolidated 2026-05-08, replaces deleted `batch-live-pipeline.md` + `batch-live-symmetry.md`) +
  `/codex/04-architecture/execution-modes-and-chain-resolution.md` all align.
- **Replay subsystem doc** — `/codex/05-infrastructure/replay-subsystem.md` shipped 2026-05-08. Watermark contract +
  smooth-handoff + anti-pattern (`pipeline_mode=replay` banned) all documented.
- **Matching engine doc** — `/codex/04-architecture/batch-live-architecture.md:§5` covers BENCHMARK + SIMULATED +
  L0/L1/L2/AMM matchers. ✅ Complete.
- **Strategy lifecycle 9-phase enum** — `/codex/09-strategy/architecture-v2/strategy-lifecycle-maturity.md` ships full
  state machine + UAC enum + transition rules. ✅ Complete.
- **DART manual-trade gate** — `/codex/04-architecture/research-service-and-dart-integration.md` +
  `/codex/09-strategy/architecture-v2/cross-cutting/dart-manual-trade-spec.md` cover DART end-to-end (6 lanes). ✅
  Complete.
- **Pipeline-mode partition doc** — `/codex/02-data/pipeline-mode-partition.md` shipped 2026-05-08. Closed-set enum +
  reader fallback + phase shipping table. ✅ Complete.
- **Per-asset-group batch=live narratives — GAPS:**
  - CeFi: NO dedicated doc (matcher pattern only implied by L2Matcher spec)
  - TradFi: NO dedicated doc (futures + ETFs + options shard atoms differ; no narrative)
  - Prediction: NO live-handler integration doc (canonical_question_group bundling untested in real-time live)
  - Sports: covered (`batch-live-architecture.md:§7`) but feature-family live handler missing (p1-todo-10)
  - DeFi: covered (`defi-execution-overview.md` + `defi-phase3-infrastructure.md`)
- **Stale-not-missing per-asset-group SLA** — implicit in `live-pipeline-architecture.md:§ Live gap semantics` but
  per-asset-group thresholds not codified. Per CLAUDE.md key rule (sports/prediction CAN have empty_confirmed at
  instrument-day, cefi/defi/tradfi CANNOT) — needs per-asset-group SLA doc.
- **Anti-patterns enumeration scattered** — `batch-live-architecture.md:§8` lists 5 fixed anti-patterns. CLAUDE.md
  "Batch = Live" lists 4 NEVER patterns. `pipeline-mode-partition.md` lists 1 anti-pattern. Worth consolidating into one
  anti-patterns SSOT.

### Mode-axis composition gaps

- **No SSOT for the cartesian product** of `RuntimeMode` × `OperationalMode` × `BatchExecutionMode` × `MaturityPhase`.
  The four axes are individually documented but their interaction is implicit. Block J1 mapping is the proposed SSOT
  shape.

### Per-block gap summary table

| Block      | Gap                                                                    | Cutover blocking?                                        |
| ---------- | ---------------------------------------------------------------------- | -------------------------------------------------------- |
| A1         | Verify no third place stating contradicting principle                  | Low                                                      |
| A3         | Triple-path (real + benchmark + simulated-shadow) in live mode unclear | High                                                     |
| A4         | Per-asset-group narratives missing for cefi/tradfi/prediction          | Med (cefi/defi blocking; tradfi/prediction post-cutover) |
| B1         | UI redeclares RuntimeMode                                              | Low                                                      |
| B6         | Other mode-shaped enums uncatalogued                                   | Low                                                      |
| C2         | Execution-service fill seam not grep-discoverable                      | High                                                     |
| C7         | MDPS dual-handler drift risk                                           | High                                                     |
| C8         | Sports + calendar feature families no live handler                     | Med                                                      |
| D1         | MDPS minimum-contract not enforced                                     | High                                                     |
| D3         | Execution-service fill seam audit                                      | High                                                     |
| D4         | Shadow-simulated fills in live not implemented                         | High                                                     |
| E1         | `pipeline_mode` partition end-to-end shipping                          | High                                                     |
| E2         | No QG schema-parity enforcement                                        | Med                                                      |
| E5         | Cluster-validation parity in both batch + live                         | Med                                                      |
| F2         | Dashboard hardcoded mock values per mode                               | Low                                                      |
| F4         | ML page disables batch path entirely                                   | Low (UX, not correctness)                                |
| F5         | No shared ModeContext provider                                         | Low                                                      |
| G1         | `LIVE_` prefix in `VMEventType`                                        | Med (precedent)                                          |
| G4         | Event archive path partitioning unclear                                | Low                                                      |
| H1         | Mock-vs-real ↔ batch-vs-live conflation cases                          | Low                                                      |
| I1, I2, I5 | Per-asset-group narratives missing                                     | Med (cefi blocking)                                      |
| J1         | Mode-axis composition SSOT missing                                     | High                                                     |
| K1         | Replay subsystem implementation status                                 | High                                                     |
| L2         | No AST sweep for mode-conditional branching                            | High                                                     |
| L7         | Verify `assert_available_at_present` fires everywhere                  | High                                                     |
| M9         | "Recon green" tolerance thresholds uncodified                          | High                                                     |
| N1         | End-to-end symmetry test never run on `carry_staked_basis`             | High (cutover gate)                                      |

## Code-derived answers (2026-05-09 — 5-parallel-agent audit)

Status legend: ✅ ANSWERED-FROM-CODE · ⚠️ PARTIAL (code+gaps) · ❌ CONFIRMED-GAP (no code yet) · 🤔 OPERATOR-DECISION
(judgment call, not derivable).

### Block A — SSOT principle + scope alignment

- **A1** ✅ — Two canonical SSOTs (CLAUDE.md "Batch = Live" section +
  `/codex/04-architecture/batch-live-architecture.md`)
  - 4 read-only mirrors (archive/unified-internal-contracts, UI context, UTL cloud_interface). No third place
    contradicts. Legacy `ServiceMode` FULLY RETIRED (only test refs at `test_domain_new_modules.py:206,214`).
- **A2** 🤔 — Four seams documented (`batch-live-architecture.md` § 2): data ingest, replay watermark, feature compute,
  execution fill. Operator: confirm 4-seam vs 2-seam framing.
- **A3** ❌ — Triple-path (real + benchmark + simulated-shadow in live) **NOT IMPLEMENTED**. Grep for "shadow" /
  "simulated_shadow" / "shadow_fill" / "execution_alpha" in execution-service returned zero non-test hits.
  Infrastructure exists (matching engine + `BatchExecutionMode.SIMULATED`) but only batch wires it.
- **A4** ⚠️ — Per-asset-group readiness varies (see Block I answers).
- **A5** ⚠️ — 4 mode axes confirmed: `RuntimeMode` (BATCH | LIVE), `OperationalMode` (LIVE | MANUAL | BACKTEST | PAPER),
  `BatchExecutionMode` (BENCHMARK | SIMULATED), `StrategyMaturityPhase` (10 members). **Cartesian product NOT codified**
  — no SSOT showing which (RuntimeMode, OperationalMode, BatchExecutionMode, MaturityPhase) tuples are valid. Block J1
  gap.
- **A6** ✅ — `OperationalMode.PAPER` is its own value at UAC `internal/modes.py:181-197`, not a composition.

### Block B — Mode enums

- **B1** ✅ — `RuntimeMode` canonical at `unified_api_contracts/internal/modes.py:69-80`. UI mirrors are read-only
  (`unified-trading-system-ui/context/internal-contracts/schemas/modes.py`). `ServiceMode` dead.
- **B2** ✅ — **NOT being conflated at runtime**. `runtime_mode == "local"` config-toggle pattern at deployment-api +
  client-reporting-api (~8 sites). No live-code branches on `pipeline_mode ==` for execution routing — `pipeline_mode`
  is manifest-internal only.
- **B3** ✅ — `BatchExecutionMode` at `unified_api_contracts/internal/execution.py:37-45` (BENCHMARK | SIMULATED). ⚠️
  Switch location not surfaced in grep — likely DI-routed inside execution-service `engine/modes/`.
- **B4** ✅ — `OperationalMode` 4 members at UAC `internal/modes.py:181-197`: LIVE | MANUAL | BACKTEST | PAPER. Closed
  StrEnum, basic existence test at `test_domain_new_modules.py`.
- **B5** ✅ — `StrategyMaturityPhase` 10 members at
  `unified_api_contracts/internal/domain/strategy_service/lifecycle.py:45-73`: SMOKE / BACKTEST_MINIMAL / BACKTEST_1YR /
  BACKTEST_MULTI_YEAR / PAPER_1D / PAPER_14D / PAPER_STABLE / LIVE_EARLY / LIVE_STABLE / RETIRED.
  `maturity_phase_rank()` + `is_valid_maturity_transition()` at `:91-116` (rank-only validation). ❌ **Phase → mode
  mapping function MISSING** — confirmed gap.
- **B6** ✅ — 14 mode-shaped enums enumerated. Beyond the 4 axes above: `EnvironmentMode` (DEV|STAGING|PROD), `DataMode`
  (MOCK|REAL), `TestnetMode` (MAINNET|TESTNET), `PhaseMode`, `TestingStage` (6 values), `ManualExecutionMode`
  (EXECUTE|RECORD_ONLY), `MultiLegExecutionMode`, `DeploymentOperationMode`, `ExecutionMode` (preferences),
  `TrainingPhase` (ML domain). None uncatalogued.

### Block C — Per-service mode handling

- **C1 strategy-service** ✅ Mode-blind. CLI dispatches by `--operation` (backtest vs trade), NOT `--mode`. Cite
  `strategy_service/cli/service_entry.py:1-795` + `docs/CLI_REFERENCE.md` ("mode (batch only for now)").
- **C2 execution-service** ✅ NAMED SEAM — `is_live: bool` parameter threads through connector hierarchy. Citations:
  `venues/aave.py:76` (param), `:110,284,321,360,397,436` (six `if self.is_live:` branches),
  `defi_execution/protocols/uniswap.py:789`, `cli/handlers/execute_handler.py:68` (operation=backtest blocks --mode
  live), `cli/handlers/live_execution_handler.py:135,147`, `matching_engine/engine.py:562,736` (matcher factory).
  Classification: **(seam-correct)** — properly scoped executor selection.
- **C3 position-balance-monitor** ✅ Mode-blind logic. `config.py:373,378` exposes `is_live`/`is_batch` properties from
  CLI mode; handlers operation-dispatch only.
- **C4 risk-and-exposure** ✅ Mode-blind. CLI parses `--mode` at `cli/parser.py:36`; handlers operation-dispatch.
- **C5 alerting-service** ✅ **(seam-correct)** legitimate dispatch — `--mode live` runs PubSub subscriber loop,
  `--mode batch` runs one-shot poll cycle. Cite `cli/main.py:8-9` + `subscribers/batch_event_reader.py:81` ("based on
  --mode without changing downstream routing logic"). Alert rules themselves mode-blind.
- **C6 MTDS** ✅ "The service does not inspect `--mode`" (`market_tick_data_service/README.md:26`). `--mode batch` → UTL
  BatchIO date iteration; `--mode live` → UTL PubSubIO event-driven (`cli/main.py:4-5`). ⚠️ `pipeline_mode` row-stamping
  not surfaced in adapter grep — Phase 1B kwarg landed but consumer-sweep (Phase 4) pending.
- **C7 MDPS** ✅ Single dispatch point at `cli/parser.py:45-59` (`_mode_dispatch_handler`). Lazy-loads
  `live_mode_handler` only when `mode == "live"` (heavy-deps reason cited `:28`). Two separate handler classes still
  carry parity risk — see D1.
- **C8 features-\* services** ⚠️ Mixed. Per `features-service-architecture.md:156-163`:
  - ✅ ModeHandler families (unified batch+live): `volatility`, `delta_one`, `onchain`, `sports`.
  - ⚠️ Bare classes (NOT unified): `commodity`, `cross_instrument`, `multi_timeframe`, `calendar`.
  - All share CLI `--operation`/`--mode` axes; calculator core does not branch on mode (anti-pattern banned at `:229`).
- **C9 instruments-service** ✅ Definitions mode-blind. `--trigger` is orthogonal axis for live entity-type selection
  (`cli/main.py:4-5`, `triggers/__init__.py:7`).
- **C10 deployment-service** ✅ `--mode` is infrastructure routing only. Terraform launch templates pass `--mode batch`
  consistently (`terraform/gcp/defi_collection_scheduler.tf:170`).
- **C11 client-reporting-api** ✅ Mode-blind. `is_mock_mode()` is DATA_MODE (mock vs real), orthogonal to RuntimeMode.
- **C12 UCI / UFI / UEI / UTL** ✅ Libraries mode-blind. UCI `cloud_interface/constants.py:RuntimeMode` reference is
  config protocol — legitimate.

### Block D — MDPS + execution-service code-path separation

- **D1** ❌ **No runtime enforcement** of MDPS batch+live handler parity. Documentation-only contract. No shared base
  class, no parametric test asserting `process_handler` ≡ `live_mode_handler` outputs. Cutover-relevant.
- **D2** 🤔 — Refactor proposal (single handler with mode-injected I/O) is operator decision.
- **D3** ⚠️ — Fill seam exists via `is_live` thread (Block C2 cites). The factory switch (matching_engine vs real venue
  selection) was found in matching_engine factory but not the routing layer that picks it per RuntimeMode — likely
  inside `engine/modes/` directory not exposed by current grep. Audit candidate: explicit factory function with QG
  enforcement.
- **D4** ❌ — Shadow-simulated fills NOT IMPLEMENTED in live (Block A3).
- **D5** Cutover-blocking ranking (top 3): (1) execution-service `is_live` → venue selection (matching engine vs real
  fills must agree within tolerance); (2) MDPS dual-handler parity (no enforcement); (3) alerting-service polling-loop
  rule firing parity. Top 3 post-cutover-cleanup: shadow-simulated fills, phase→mode mapping function, MDPS
  shared-base-class lift.

### Block E — Manifest + data parity

- **E1** ⚠️ PARTIAL — `gcs_migration_bundle_pipeline_mode_2026_05_08.md` Phases 0/1A/1B/1C/2/5.1/7.1/7.2 SHIPPED
  2026-05-08. Phases 3 (operator-gated VM fleet migration) / 4 (consumer sweep) / 6 / 8 (T+30d cleanup) / 9 (workspace
  QG sweep) PENDING. UTL `ManifestWriter.record_captured` accepts optional `pipeline_mode` kwarg
  (`unified-trading-library/unified_trading_library/manifest_writer.py:1968`).
- **E2** ❌ — No QG step compares batch parquet schema to live parquet schema per data*type. Per-write validation exists
  (`_maybe_validate()` at `manifest_writer.py:2025-2034`), schema is identical \_by design* (same UAC contract), not by
  runtime cross-mode enforcement.
- **E3** ✅ — `assert_available_at_present` at UTL `manifest_writer.py:72-103`; called from `record_captured()`. No
  active code paths bypassing `record_captured` for parquet writes (post-2026-05-05 MDPS-1440-NaN incident reconciled).
- **E4** ✅ — `classify_blank_reason_row(asset_group, row)` at UTL `legacy_reason_classifier.py:320-380` enforces
  per-asset-group rule. Catalog-aware writer-side guard (Wave 3.M) PENDING.
- **E5** ✅ — `MissingClusterValidationError` raises in both batch + live writes (`manifest_writer.py:2000-2133`,
  orthogonal to pipeline_mode). QG STEP 5.64 implemented per writegate Phase 1A.
- **E6** ✅ — `MANIFEST_PER_VM_SHARDS` enforced at `manifest_writer.py:694`; per-VM shard merge at
  `_index/per_vm/{vm_name}.parquet`. Live deployment Phase 3 PENDING.
- **E7** ✅ — Reader fallback chain 5 levels at `manifest_reader_fallback.py:90-96`: canonical / strip_pipeline_mode /
  legacy_category_vocab / legacy_day_prefix / legacy_day_prefix_category_vocab. Phase 8 cleanup scheduled 2026-06-15
  (T+30d post-Phase-3).

### Block F — UI symmetry

- **F1** ✅ — DART per `/codex/04-architecture/research-service-and-dart-integration.md:13` is operator-facing
  manual-trade gate; 6 lanes spec'd. DART panel + ack-flow shipped 2026-05-08 (per master plan F23 status).
- **F2** ✅ confirmed — `dashboard/page.tsx:72-76,100-104,120,158` hardcodes mock values per `isLive` boolean. Mock-mode
  artefact, post-cutover cleanup.
- **F3** ✅ Display filter, not code-path branch — `ops/page.tsx:192,202-221` (`useState<"live"|"batch">("live")`,
  Radio + Database icon toggle).
- **F4** ⚠️ — ML page "Live Predictions — only in live mode" feature flag disables batch path. UX-grade, post-cutover.
- **F5** ✅ **EARLIER AUDIT WAS WRONG** — `ExecutionModeContext` provider EXISTS at
  `unified-trading-system-ui/lib/execution-mode-context.tsx:19-43`. Hook `useExecutionMode()` at `:45-53` returns `mode`
  / `setMode` / `config` / `isLive` / `isPaper` / `isBatch`. Default `"live"` at `:24`. Pages that maintain their own
  `useState<"live"|"batch">` are violating the available context (refactor candidate).
- **F6** ✅ — `DeploymentHistory.tsx:46,101,105+` — `deploy_mode` is filter (parses `parameters.mode`).
- **F7** ⚠️ — Tabs separate per `deploy_mode`; full lifecycle-tab plan still active.
- **F8** 🤔 — VITE_MOCK_API conflation at dashboard (Block F2); broader audit pending.
- **F9-F11** ⚠️ Not deeply audited — recommend follow-up sweep folded into spawned plan.

### Block G — Events + analytics

- **G1** ✅ confirmed violation — `deployment-service/deployment_service/events.py:21-49` has
  `LIVE_HEALTH_CHECK_PASSED`, `LIVE_HEALTH_CHECK_FAILED`, `LIVE_ROLLBACK_EXECUTED`. Other VMEventType members mode-blind
  (VM_PREEMPTED, VM_DELETED, VM_QUOTA_EXHAUSTED, VM_ZONE_UNAVAILABLE, VM_TIMEOUT, CONTAINER_OOM,
  CLOUD_RUN_REVISION_FAILED).
- **G2** ✅ — `deployment-ui/src/types/index.ts` mirrors LIVE\_ prefix in TS.
- **G3** ⚠️ — Lifecycle event taxonomy not explicitly enumerated as separate `STRATEGY_PROMOTED_TO_*` events; UTL
  lifecycle events with operator identity referenced in DART spec but no canonical strategy-lifecycle event enum
  surfaced.
- **G4** ✅ — Events archive path is
  `gs://{pid}-events/events/{service}/{YYYY-MM-DD}/{correlation_id}/hour={H}/*.jsonl`. **No `pipeline_mode` partition**
  — intentional (replay events indistinguishable from live in stream; only Redis watermark KV differentiates).
- **G5** ❌ — No unified analytics event schema found. Likely Firebase analytics or per-UI ad-hoc.
- **G6** ❌ — No `BATCH_VS_LIVE_RECON` event taxonomy in code. Master plan F18 reconciler is scaffolded but
  code-incomplete.
- **G7** ⚠️ — Per-asset-group events (`MATCH_KICKOFF`, `MARKET_RESOLVED`, etc.) not deeply enumerated; partial coverage.
- **G8** ✅ — UI `internal-contracts/schemas/events.py` mirrors UAC (read-only mirror).

### Block H — Mock-vs-real ↔ batch-vs-live independence

- **H1** ⚠️ — Dashboard conflation confirmed (Block F2). Workspace-wide rule "mock-vs-real and batch-vs-live
  independent" not codified.
- **H2** ✅ — Tier (0/1/2) is orthogonal to RuntimeMode per `runtime-tiers-and-deployment.md`.
- **H3** ❌ — No mode-parametric test fixture pattern found.
- **H4** ❌ — Smoke harnesses appear mode-specific, not parametric.

### Block I — Per-asset-group symmetry

- **I1 CeFi** ✅ — Adapters dual-pathed (Tardis batch + WebSocket live across binance/bybit/okx/deribit/kraken/bitfinex/
  bitget/etc.). execution-service `adapters/order_adapter.py` paper/testnet/live shipped. Volatility features unified
  via ModeHandler. ⚠️ Testnet verification per master plan F20 PENDING.
- **I2 TradFi** ❌ **NO LIVE EXECUTION ADAPTER** in execution-service. TradFi is data-receive only (Databento +
  Barchart + Yahoo for batch; live = no venue execution). Post-cutover scope.
- **I3 DeFi** ✅ — `carry_staked_basis` at
  `strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py:1`. `leveraged_funding_arb`
  referenced in tests. LST yields / perp funding / gas / oracle-prices: batch + live via ModeHandler. Aave / Uniswap
  connectors + Tenderly fork shipped (`execution-service/tests/integration/conftest.py`). 2-yr config-grid backtest
  script SHIPPED 2026-05-09 (`strategy-service@3dea3c7`).
- **I4 Sports** ❌ — No live handler **by design** (per `features-service-architecture.md:160`, sports is bare class not
  sharing ModeHandler lifecycle). Batch-only feature calculators. Not May-23 blocking.
- **I5 Prediction** ❌ — Polymarket / Kalshi live WebSocket NOT WIRED. Batch-only via Tardis aggregate CLOB captures.
  Post-cutover.
- **I6** ❌ — No cross-asset-group meta doc; each asset_group is implicit story.

### Block J — Lifecycle ↔ mode integration

- **J1** ❌ — Phase → (RuntimeMode, BatchExecutionMode, OperationalMode) mapping function MISSING. Audit candidate: add
  `runtime_mode_for_phase(phase)` helper to UAC lifecycle module.
- **J2** ⚠️ — Promotion gates code = rank validation only (`is_valid_maturity_transition` at lifecycle.py:98-116).
  Evidence-based gates (≥30d continuous, no breaker events) NOT in code. `StrategyLifecycleTransition` dataclass
  (`:22-30`) exists but unused.
- **J3-J4** 🤔 — Operator decisions on demote/pause flow + cross-question integration.

### Block K — Replay handoff

- **K1** ✅ — Replay subsystem SHIPPED (design + helpers). `ReplayWatermarkKV` + `ReplayPublisher` at UTL
  `streaming/replay.py:61-200+`. Tests at `tests/unit/test_replay.py:37-190`. Codex stub at
  `/codex/05-infrastructure/replay-subsystem.md`. Operational deployment Phase 7 PENDING.
- **K2** ✅ — Original-time `available_at` stamping documented in module docstring + codex `:36`. Caller responsibility.
- **K3** ⚠️ — `REPLAY_BACKSTOP_REACHED` event documented in codex `:70-71` but code emit + alerting wiring PENDING
  (Phase 7).
- **K4** ✅ — Backtest = `RuntimeMode.BATCH` + date-loop (`strategy-service/cli/service_entry.py:134-387`,
  `_run_batch_backtest_range` `:387`, `get_handler_for_mode("backtest", ...)` `:278`). NOT replay-fed; replay subsystem
  is gap-fill for live operations only.

### Block L — Static enforcement (43 quality-gates.sh files audited)

- **L1** ❌ — No QG step enforcing "no separate live-only data_types".
- **L2** ❌ — No AST sweep for mode-conditional branching outside seam.
- **L3** ❌ — No QG step asserting `class RuntimeMode` appears in exactly one file.
- **L4** ❌ — No AST sweep for `LIVE_` / `BATCH_` prefix in event names.
- **L5** ❌ — No batch-vs-live schema-parity gate (Block E2).
- **L6** ❌ — No QG asserting executor factory in single file.
- **L7** ✅ — `assert_available_at_present` enforced via `record_captured()` (Block E3). Coverage probably complete (no
  direct parquet write bypasses found in active code).
- **L8** 🤔 — Mode-parametric component tests = operator decision (likely overkill).
- Existing relevant steps: STEP 5.62 (Health API + ModeHandler), STEP 5.64 (cluster validation at record_captured), STEP
  5.66 (per-VM shard isolation).

### Block M — Cross-cutting integration

- **M1** ✅ — Alerting parity per `/codex/04-architecture/alerting-batch-live.md`: same routing rules, same dedup, same
  cooldown logic; only event source differs.
- **M2** ✅ — Position-balance mode-blind (Block C3).
- **M3** ⚠️ — `risk-and-exposure-service/risk_and_exposure_service/kill_switch_rules.py` shipped + bus-subscriber wired.
  ❌ No `BatchExecutionMode=DRILL` chaos mode.
- **M4-M5** ✅ — `client-reporting-api` `/pnl` endpoint mode-blind (single endpoint, no separate `/batch-pnl` /
  `/live-pnl`).
- **M6-M8** 🤔 — Cross-question (custody, credentials, DR) — covered by sibling question docs.
- **M9** ❌ — **No `recon_drift_threshold` / `RECON_TOLERANCE` / `bps_drift` / `recon_green` defined in code.** Master
  plan item F21 (batch-live-reconciliation-service) scaffolded but code-incomplete.

### Block N — End-to-end reality check

- **N1 carry_staked_basis runnability today**:
  - ✅ Backtest entrypoint: `run_2yr_config_grid_backtest.py` shipped 2026-05-09 (`strategy-service@3dea3c7`)
  - ✅ Score output: manifest write-gate persistent to GCS
  - ⚠️ Paper deploy: execution paper/testnet wired; deployment orchestration TBD
  - ⚠️ Live deploy: Copper custody integration stubbed; CEFFU section PENDING
  - ❌ Recon: `batch-live-reconciliation-service` incomplete (master plan F21 status: ✗)
- **N2 Master plan F17/F18/F20/F21/F23**: | Item | Status | | -------------------------- |
  --------------------------------------------------------------------- | | F17 (Backtest fidelity) | ✅ 5 matcher
  classes shipped | | F18 (2-yr config-grid run) | ✅ Script + 22 unit tests (2026-05-09) | | F20 (Live testnet parity)
  | ⚠️ Tenderly DeFi shipped; CeFi testnet TBD | | F21 (Reconciliation) | ❌ Code-incomplete; P0 follow-up | | F23 (DART
  manual-trade) | 🟢 DART panel + ack-flow shipped 2026-05-08 |
- **N3-N4** 🤔 — Cutover-blocking subset confirmation = operator decision.

### Top of-the-doc summary

**18 of 80+ sub-questions answered ✅. 17 are confirmed ❌ gaps. 13 are ⚠️ partial. ~12 remain 🤔 operator-decision.**
The architecture story is mostly intact; the remaining work is **operational shipping** (execute Phases 3-9 of
pipeline_mode migration, ship F21 reconciler with M9 thresholds, wire J1 phase→mode mapping, lift L1-L6 enforcement,
implement A3/D4 shadow-simulated live fills) — not architectural redesign.

## Operator decisions remaining (everything else can be parallelised + shipped)

1. **A2** — 4 seams documented vs 2-seam framing — confirm.
2. **D5 / N3** — Final cutover-blocking subset for May-23 (recommendation: D1 + D3 + D4 deferred post-cutover · M9
   thresholds · F21 reconciler · L7 verified · pipeline_mode Phases 3+4+9 shipped + N1 end-to-end run on
   `carry_staked_basis`).
3. **L8** — Mode-parametric component tests workspace-wide — overkill or ship?
4. **J3** — Demote-to-paper / pause-live behaviour: same pipeline reverse, or separate code path?
5. **G1** — `LIVE_` event-prefix rename pre- or post-cutover (semver bump VMEventType in UAC)?
6. **F4 / F5** — UI mode-aware branching (ML page hard-disable, dashboard hardcoded mocks): pre- or post-cutover
   refactor sweep?
7. **I2 / I5** — Confirm TradFi live execution + Prediction live websocket are post-cutover scope (DeFi-only May-23).

Defaults if no answer: 2-seam framing · D1+D3 named-seam audit only (defer D4/J1) · skip L8 · same-pipeline-reverse for
J3 · post-cutover for G1+F4+F5 · post-cutover for I2/I5.

## Iteration log

| Date       | Author         | Change                                                                                                                                                                                                                                            |
| ---------- | -------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2026-05-08 | agent (claude) | Initial draft + 3-parallel-agent audit (services / UI+events / codex) folded into Audit findings + per-block gap summary.                                                                                                                         |
| 2026-05-09 | agent (claude) | 5-parallel-agent code audit answering 80+ sub-questions; status legend (✅/⚠️/❌/🤔) per question with file:line citations; reduced operator-decision surface to 7 items; ExecutionModeContext provider found existing (corrected earlier audit). |

## Plan-shape decisions (refined post-2026-05-09 audit)

- **Plan name + path**: recommendation `plans/active/batch_live_symmetry_2026_05_09.md` (single workspace plan with
  per-asset-group docs as Phase deliverables) — defaults below assume this shape.
- **Plan type**: mixed (codex docs + UAC enum extension + UTL helper + QG steps + UI refactor + reconciler shipping).
- **Owner side**: parallel-agent fan-out — see "AI parallel work-split" below.
- **Codex SSOTs touched**:
  - NEW: `/codex/04-architecture/cefi-batch-live.md` (~30min sub-agent, contract per Block I1)
  - NEW: `/codex/04-architecture/tradfi-batch-live.md` (~30min sub-agent, post-cutover scope)
  - NEW: `/codex/04-architecture/prediction-batch-live.md` (~30min sub-agent, post-cutover scope)
  - NEW: `/codex/06-coding-standards/mode-axis-discipline.md` — mode-axis cartesian product table (~1h)
  - UPDATE: `/codex/04-architecture/batch-live-architecture.md` — cross-asset-group meta + UI mode-context guidance +
    LIVE\_ event-prefix anti-pattern (~30min)
  - UPDATE: `/codex/06-coding-standards/quality-gates.md` — STEP entries L1-L6 (~1h)
  - UPDATE: `/codex/05-infrastructure/replay-subsystem.md` — implementation-status update + REPLAY_BACKSTOP wiring
    (~15min)
  - UPDATE: `/codex/04-architecture/features-service-architecture.md` — sports + calendar live-handler timeline (~15min)
- **Cross-plan dependencies**:
  - `master_to_live_defi_2026_05_23.md` Group F items 17/18/20/21/23 — symmetry IS the verification gate.
  - `live_pipeline_mtds_mdps_features_2026_05_08.md` — replay-subsystem Phase 7 deployment + REPLAY_BACKSTOP wiring.
  - `gcs_migration_bundle_pipeline_mode_2026_05_08.md` — Phases 3/4/6/8/9 shipping.
  - `features_repo_consolidation_2026_05_08.md` — bare-class families
    (commodity/cross_instrument/multi_timeframe/calendar) lift to ModeHandler.
  - `alerting_service_live_rules_2026_05_07.md` — alert-rule parity verification.
  - `deployment_ui_lifecycle_tabs_2026_05_08.md` — UI ExecutionModeContext rollout to all surfaces.
- **Estimated scope (refined, parallel-agent throughput)**:
  - **Cutover-blocking subset (May-23 P0)**: D1 audit + D3 factory-extraction + E1 pipeline_mode Phases 3/4/9 + L7
    verification sweep + M9 reconciler thresholds + F21 reconciler shipping + N1 end-to-end carry_staked_basis run +
    Group F items closeout — fan-out across ~6 parallel sub-agents, target ~3 calendar days.
  - **Pre-cutover symmetry hardening (P1)**: 4 codex doc UPDATE + 2 NEW (cefi-batch-live + mode-axis-discipline) +
    L1/L2/L3/L5/L6 QG STEP additions + features-service bare-class → ModeHandler lift (4 families) + UI
    ExecutionModeContext rollout sweep — fan-out ~5 parallel sub-agents, ~5 calendar days.
  - **Post-cutover (P2)**: tradfi-batch-live + prediction-batch-live codex NEW + LIVE\_ event-prefix rename + ML page
    mode-blind refactor + dashboard mock-conflation refactor + sports/calendar live-handlers + I2/I5 live execution
    adapters + A3/D4 shadow-simulated live fills + J1 phase→mode mapping helper — ~10 calendar days, hard requires no
    operator gating.
- **AI parallel work-split (recommendation)** — start tomorrow morning:
  - **Tab 1 (codex SSOT batch)**: ship 2 NEW docs (cefi-batch-live, mode-axis-discipline) + 4 UPDATE docs in single
    bundled PM commit. ~3-4 hrs.
  - **Tab 2 (UAC + UTL)**: J1 phase→mode mapping helper + L7 sweep verification + missing F21 reconciler thresholds
    (M9). ~4 hrs.
  - **Tab 3 (QG STEPs L1-L6)**: AST sweep impl + workspace-wide QG STEP wiring + per-repo rollout. ~6 hrs.
  - **Tab 4 (features-service bare-class lift)**: commodity / cross_instrument / multi_timeframe / calendar families →
    ModeHandler. Pure refactor. ~6-8 hrs.
  - **Tab 5 (pipeline_mode Phases 3/4/9)**: VM-fleet migration + consumer sweep + workspace QG sweep — operator-gated
    execution per the migration plan. ~1 calendar day end-to-end including cooling.
  - **Tab 6 (F21 reconciler)**: ship `batch-live-reconciliation-service` to code-complete + paper-mode smoke + initial
    recon-green threshold sweep against shipped 2-yr backtest. ~1 calendar day.
  - **Tab 7 (UI cleanup)**: rollout `ExecutionModeContext` to all surfaces (`dashboard/page.tsx`, `ops/page.tsx`,
    `research/ml/page.tsx`) + remove `useState<"live"|"batch">` reimplementations + post-cutover scope: ML page
    mode-blind refactor. ~6-8 hrs.
  - **Tab 8 (carry_staked_basis end-to-end run + recon)**: launch backtest VM + paper-deploy launcher + monitor 7
    calendar days. **This is the hard wall-clock dependency** for May-23 + needs to start ASAP.
  - All 8 tabs mostly independent; serialise only on Tab 8 wall-clock + Tab 5/Tab 6 recon-data dependency. Total
    active-AI-shipping window ~7 calendar days; remaining ~7 days are Tab 8's paper-trade soak.

## Plan extraction record

(Filled when the plan ships.)

- Plan path: TBD
- Spawned commit: TBD
- Codex updates committed: TBD
- Question doc closes (status: closed) when: spawned plan in `plans/active/`; cefi-batch-live + tradfi-batch-live +
  prediction-batch-live + mode-axis-discipline codex docs committed; L2 + L3 + L7 QG steps green workspace-wide;
  end-to-end symmetry test (N1) executed against `carry_staked_basis` with recon-green within tolerance; master plan
  Groups F17/F18/F20/F21/F23 green for both May-23 archetypes.
