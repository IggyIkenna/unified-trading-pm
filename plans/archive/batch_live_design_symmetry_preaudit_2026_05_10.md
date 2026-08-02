---
doc_type: plan
title: batch-live-design-symmetry-preaudit
summary:
status: ready-for-plan-extraction
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    alerting-service,
    batch-live-reconciliation-service,
    client-reporting-api,
    deployment-service,
    execution-service,
    features-service,
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
    unified-trading-pm/plans/archive/2026_05/manifest_schema_final_gate_2026_05_09.md,
    unified-trading-pm/plans/archive/2026_05/available_at_lookahead_bias_completion_2026_05_08.md,
    unified-trading-pm/plans/archive/2026_05/writegate_honest_coverage_endtoend_2026_05_06.md,
    unified-trading-pm/plans/active/defi_master_2026_05_07.md,
  ]
created: 2026-05-10
overview:
  Citadel-grade pre-execution audit manifest for the spawned plan derived from
  `batch_live_design_symmetry_2026_05_08.md`. Per-Tab pre-audit + service-readiness Groups A-G + QG STEP violation
  pre-flight + cross-plan banners + risk register + collision matrix + ServiceEmissionPolicy gaps + spawned-plan
  readiness checklist + Tab-8 paste-ready operator recipe.
type: pre-audit-manifest
operator: ikenna
locked_by: live-defi-rollout
locked_since: 2026-05-10
companion_to: unified-trading-pm/plans/archive/batch_live_design_symmetry_2026_05_08.md
related_codex:
  [
    unified-trading-pm/codex/04-architecture/batch-live-architecture.md,
    unified-trading-pm/codex/05-infrastructure/live-pipeline-architecture.md,
    unified-trading-pm/codex/05-infrastructure/replay-subsystem.md,
    unified-trading-pm/codex/02-data/pipeline-mode-partition.md,
    unified-trading-pm/codex/06-coding-standards/quality-gates.md,
  ]
---

## Deferred work — migrated to:

**None** — successor: not applicable. Plan archived as 100% completed (no open `- [ ]` items at archive time). Any
incidental DEFERRED / post-cutover / out-of-scope tokens in the body are historical context, not unfinished work.

# Batch=Live design symmetry — Citadel-grade pre-execution audit (2026-05-10)

This is the **durable artefact** every executing sub-agent reads BEFORE doing any work on the spawned plan
(`plans/active/batch_live_symmetry_2026_05_10.md`). No re-scanning, no inferring, no guessing. Every file:line +
violation count + collision risk + removal trigger is captured here so the spawned plan body can cite it directly.

Per CLAUDE.md § "Citadel-Grade Planning Standards § 1 Pre-Audit Before Execution" — pre-audit MUST happen before plan
body ships, embedding the manifest so executing agents don't re-scan. This file is the manifest.

Companion to [`batch_live_design_symmetry_2026_05_08.md`](batch_live_design_symmetry_2026_05_08.md) — the question doc
captures the question + audit findings + Code-derived answers + plan-shape decisions; this file captures the
execution-readiness manifest.

Sourced from 5-parallel-agent audit on 2026-05-10 covering: workspace-grep manifests for symbol moves · QG STEP
inventory + L1-L6 violation pre-flight · service-readiness Groups A-G per affected service · reconciler +
carry_staked_basis end-to-end scaffold deep-dive · cross-plan banners + risk register + collision matrix.

## 1 — Per-Tab pre-audit manifests

### Tab 1 — codex SSOT (NEW + UPDATE codex docs)

- **Cross-link targets** (existing batch=live SSOT mentions to reference, NOT duplicate): `cursor-configs/CLAUDE.md` §
  "Batch = Live"; `/codex/04-architecture/batch-live-architecture.md`;
  `/codex/04-architecture/execution-modes-and-chain-resolution.md`;
  `/codex/05-infrastructure/live-pipeline-architecture.md`; `/codex/05-infrastructure/replay-subsystem.md`;
  `/codex/02-data/pipeline-mode-partition.md`.
- **NEW docs to ship**: `cefi-batch-live.md` · `tradfi-batch-live.md` (post-cutover) · `prediction-batch-live.md`
  (post-cutover) · `mode-axis-discipline.md` (cartesian product table for `RuntimeMode` × `OperationalMode` ×
  `BatchExecutionMode` × `MaturityPhase`).
- **UPDATE docs**: `batch-live-architecture.md` (cross-asset-group meta + UI mode-context guidance + LIVE\_ event
  anti-pattern + consolidated anti-patterns) · `quality-gates.md` (STEP entries L1-L6) · `replay-subsystem.md`
  (implementation status + REPLAY_BACKSTOP wiring) · `features-service-architecture.md` (sports + calendar live-handler
  timeline).

### Tab 2 — UAC + UTL (J1 phase→mode helper · L7 sweep · M9 thresholds)

**Manifest 1 — `MaturityPhase` consumers** (10 callsites; mostly type-annotation-only):

| repo                      | file                                                       | line  | usage                                  | action                                |
| ------------------------- | ---------------------------------------------------------- | ----- | -------------------------------------- | ------------------------------------- |
| unified-trading-system-ui | lib/architecture-v2/lifecycle.ts                           | 39,54 | type export + STRATEGY_MATURITY_PHASES | no change (SSOT)                      |
| unified-trading-system-ui | lib/architecture-v2/lifecycle.ts                           | 307   | `allowsAllocationCta(phase)` helper    | keep (helper returns bool only)       |
| unified-trading-system-ui | lib/architecture-v2/lifecycle.ts                           | 321   | MATURITY_PHASE_LADDER const            | no change                             |
| unified-trading-system-ui | lib/architecture-v2/lifecycle.ts                           | 337   | `maturityPhaseRank(phase)` helper      | keep (helper returns int)             |
| unified-trading-system-ui | components/strategy-catalogue/StrategyCatalogueSurface.tsx | 85    | `synthesiseMaturity()`                 | **call J1 helper** for triplet derive |
| unified-trading-system-ui | components/strategy-catalogue/FomoTearsheetCard.tsx        | 44    | prop type annotation                   | no change                             |
| unified-trading-system-ui | components/strategy-catalogue/RealityPositionCard.tsx      | 57    | prop type annotation                   | no change                             |
| unified-trading-system-ui | app/(ops)/approvals/strategy-versions/page.tsx             | 78,84 | type cast                              | no change (read-only cast)            |
| unified-trading-system-ui | lib/admin/api/strategy-lifecycle.ts                        | 17-18 | from_phase / to_phase fields           | no change (schema)                    |

**Manifest 2 — L7 violations** (direct parquet writes bypassing `record_captured`) — 3 confirmed + 2 audit-needed:

| severity      | file                                                               | line  | call                        | action                                 |
| ------------- | ------------------------------------------------------------------ | ----- | --------------------------- | -------------------------------------- |
| **CONFIRMED** | market-data-processing-service/app/core/storage_dispatch_worker.py | 49    | `df.to_parquet()`           | wrap in `record_captured()` or rewrite |
| **CONFIRMED** | market-data-processing-service/app/core/output_writer_service.py   | 318   | `candles_df.to_parquet()`   | audit upstream; wrap                   |
| **CONFIRMED** | market-data-processing-service/app/core/orchestration_writer.py    | 388   | `validated_df.to_parquet()` | audit upstream; wrap                   |
| audit-needed  | unified-trading-library/.../domain/standardized_service.py         | 100   | `data.to_parquet()`         | check calling context                  |
| audit-needed  | unified-trading-library/.../domain/standardized_service.py         | 299   | `data.to_parquet()`         | check calling context                  |
| OK            | unified-trading-library/.../manifest_writer.py                     | 2886+ | `merged.to_parquet()`       | no change (compliant)                  |
| OK (mock)     | features-commodity-service/scripts/seed_mock_data.py               | 360   | `pq.write_table()`          | skip (mock)                            |

**Manifest 7 — `BatchExecutionMode` switch location**: NO `BatchExecutionMode.SIMULATED` / `.BENCHMARK` enum-value
references found in execution-service runtime code. Hardcoded strings instead at
`execution-service/execution_service/engine/backtest/node_builder.py:496-504`
(`exec_algo_type: "NORMAL"|"BENCHMARK_FILL"`) + `:631-632` (algo_type market-order selection). **Refactor target**:
introduce unified `BatchExecutionMode` enum lookup in `service_config.py`; refactor `node_builder.py` + create explicit
`BatchExecutorFactory`.

**M9 reconciler thresholds**: NO `RECON_GREEN_THRESHOLDS` dict in UAC. Recommended location:
`unified_api_contracts/canonical/crosscutting/alerting/thresholds.py`. Shape:
`{archetype_id: {bps_delta_max, drawdown_pct, fill_rate_min}}`. Decision gate at reconciler:
`if |batch_pnl - live_pnl| / live_pnl > threshold_bps` → emit `BATCH_VS_LIVE_RECON_DRIFTED`.

### Tab 3 — QG STEPs L1-L6 (workspace AST sweeps)

**Reference impl**: `unified-trading-pm/scripts/quality-gates-base/base-service.sh` STEP 5.64 (cluster validation at
`record_captured()`) — the AST-walk template. Pattern: ripgrep file-level detection + emission-site assertion +
violation counter + log_fail when threshold hit. **46 quality-gates.sh files** workspace-wide (27 active repos + 19
archive); per-repo files inherit base-service.sh.

**Pre-flight violation counts** (run before STEP enable to avoid red-on-day-1 in workspace):

| Step | Violations | Status                                                           | Remediation                                                       |
| ---- | ---------- | ---------------------------------------------------------------- | ----------------------------------------------------------------- |
| L1   | **0**      | ACCEPT-FIRST-RUN-GREEN — UAC DataType enum already mode-agnostic | none — DAY-1 ENABLE                                               |
| L2   | **~21**    | FIX-REQUIRED-BEFORE-ENABLE — outside-seam mode branches          | audit each: move-to-seam OR unify-path; ~5 service PRs            |
| L3   | **2**      | FIX-REQUIRED — UAC + UI redeclares (UTL canonical)               | UAC re-exports from UTL; UI imports from UAC; 1 PR per repo       |
| L4   | **~12**    | FIX-REQUIRED — `LIVE_*` event-prefix members                     | rename 6 events; update 4 consumers; 2-3 codex updates            |
| L5   | **0**      | ACCEPT-FIRST-RUN-GREEN — unified DataType enum                   | none — DAY-1 ENABLE (real validation at manifest-shard-auditor)   |
| L6   | **N/A**    | DEFER — executor factory doesn't exist yet                       | Tab 2 introduces `BatchExecutorFactory` first; STEP enables after |

**Recommended sequence**: DAY-1 enable L1 + L5 (zero work) → Phase 2.A (L2 fix) → Phase 2.B (L3 unify) → Phase 3.A (L4
rename) → DEFER L6 until execution-service factory phase ships.

### Tab 4 — features-service bare-class lift (4 families)

**Reference ModeHandler impl**:
`features-volatility-service/features_volatility_service/cli/handlers/base_handler.py:24` — `class ModeHandler(ABC)`
with abstract methods + `LiveHandler` / `BatchHandler` subclasses.

| family           | module path                                                      | public exports                  | consumers              | interface delta              |
| ---------------- | ---------------------------------------------------------------- | ------------------------------- | ---------------------- | ---------------------------- |
| commodity        | features-commodity-service/features_commodity_service/service.py | `CommodityFeatureService`       | 1 (deployment-service) | full lift to ModeHandler ABC |
| cross-instrument | features-cross-instrument-service/.../<root>                     | `CrossInstrumentFeatureService` | 1 (deployment-service) | full lift                    |
| multi-timeframe  | features-multi-timeframe-service/.../<root>                      | `MultiTimeframeFeatureService`  | 1 (deployment-service) | full lift                    |
| calendar         | features-calendar-service/features_calendar_service/             | `CalendarFeatureService`        | 1 (deployment-service) | full lift                    |

### Tab 5 — pipeline_mode Phases 3/4/9 (operator-gated VM fleet migration)

- **Parquet count**: ~10-50M objects (workspace bucket size 50-500 TB).
- **Cost**: ~$550-700 (5M reads + 5M writes class-A ops × $0.05/M = $500; within-region egress = 0; 24h compute = $50).
- **VM fleet**: 1 consolidator VM (n1-standard-8) + per-VM shard isolation (`MANIFEST_PER_VM_SHARDS=true`,
  `VM_NAME=<unique-tag>`); 0 parallel workers (I/O-bound, not CPU-bound).
- **Wall-clock**: ~48 hours total (4-6h pre-audit · 18-24h Phase 2 migration · buffer for CRC32c verification +
  rollback).
- **Failure modes**: CRC32c mismatch (auto-delete dest, retry source — idempotent); manifest row collision (per-VM shard
  prevents race); stale GCS path template (dry-run catches; fix regex + re-run); out-of-quota (script checkpoints
  per-bucket).
- **Rollback affordance**: HIGH — dry-run mode (default) zero GCS calls; operator validates before `--apply`.

### Tab 6 — F21 reconciler shipping (`batch-live-reconciliation-service`)

**Service status**: SCAFFOLDED + PARTIAL. Repo `batch-live-reconciliation-service/` exists with 18 Python files.

**Shipped**: ServiceBootstrap (STARTED/STOPPED events correct) · CLI routing framework (`cli/main.py` dispatches
`ReconcileHandler`) · `config.py` + `config_reloaders.py` + `auth_s2s.py` · `models/recon_report.py` +
`models/deviation_thresholds.py` · `api/main.py` + `api/resolution_api.py`.

**MISSING (Tab 6 ship target)**:

- `engine/orchestrator.py` — **GREENFIELD** (must create).
- `cli/handlers/reconcile_handler.py::ReconcileHandler.run(...)` — likely returns `NotImplementedError` / `pass`.
- 6 stage files `stages/stage{0-5}_*.py` — names exist but content unverified (audit + complete).
- Manifest reader integration (UTL `record_captured` consumption).
- P&L delta calculation pipeline.
- `RECON_GREEN_THRESHOLDS` SSOT in UAC + threshold-decision wiring.
- Alerting hook for `BATCH_VS_LIVE_RECON_DRIFTED` event emit.

**Operator-runnable spot-check command** (greenfield — needs Tab 6 ship to enable):

```bash
python -m batch_live_reconciliation_service \
  --operation reconcile --mode batch \
  --start-date <YYYY-MM-DD> --end-date <YYYY-MM-DD> [--dry-run]
```

### Tab 7 — UI ExecutionModeContext rollout

**Manifest 4 — UI mode-state independent reimplementations** (6 violations to refactor + 2 already-good):

| file                                                           | line  | pattern                                       | action                       |
| -------------------------------------------------------------- | ----- | --------------------------------------------- | ---------------------------- |
| app/(ops)/ops/page.tsx                                         | 192   | `useState<"live"\|"batch">`                   | import `useExecutionMode()`  |
| app/(platform)/services/research/quant/page.tsx                | 216   | `useState<"batch"\|"live">`                   | same                         |
| components/ops/deployment/data-status/data-status-provider.tsx | 33    | `useState<"batch"\|"live">`                   | lift to ExecutionModeContext |
| components/ops/deployment/form/deploy-form-context.tsx         | 31    | `useState<"batch"\|"live">`                   | use ExecutionModeContext     |
| components/widgets/markets/markets-data-context.tsx            | 57,62 | `useState<"live"\|"batch">` + 3-way `compare` | use `{mode, setMode}`        |
| components/widgets/pnl/pnl-data-context.tsx                    | 159   | `useState<"live"\|"batch">`                   | same refactor                |
| components/trading/execution-mode-toggle.tsx                   | 27    | `useExecutionMode()` ✓ already integrated     | no change                    |
| components/shell/lifecycle-nav.tsx                             | 97    | `useExecutionMode()` ✓ already integrated     | no change                    |

**Provider canonical**: `unified-trading-system-ui/lib/execution-mode-context.tsx:19-43`. Default mode `"live"` at
`:24`. Hook returns `{mode, setMode, config, isLive, isPaper, isBatch}`.

### Tab 8 — carry_staked_basis end-to-end run + 7-day soak

| Step                             | Status                                                                                                                                                                                                 |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1. Backtest run                  | ⚠️ PARTIAL — script shipped (`run_2yr_config_grid_backtest.py` `strategy-service@3dea3c7`); deployment-service launcher `launch-defi-backtest-vm.sh` **MISSING**                                       |
| 2. Score persistence             | ⚠️ PARTIAL — paths templated `gs://{pid}-strategy-outputs/backtest/{strategy_id}/{YYYY-MM-DD}/{scores,fills,positions}.parquet`; not verified end-to-end                                               |
| 3. Paper-deploy launcher         | ❌ GREENFIELD — `find deployment-service/scripts/vm/ -name "*defi*" -o -name "*paper*"` returns ZERO matches                                                                                           |
| 4. Tenderly fork wiring          | ⚠️ INTEGRATION-TEST-ONLY — `execution-service/tests/integration/conftest.py` fixture; NOT wired for paper-deploy                                                                                       |
| 5. Aave + Uniswap mainnet        | ⚠️ PARTIAL — venues wired (`venues/aave.py:76`, `defi_execution/protocols/uniswap.py:789`); mainnet keys + RPC URLs unclear (audit Secret Manager + UAC `CHAIN_RPC_TEMPLATES`)                         |
| 6. LST yield + perp funding live | ⚠️ PARTIAL — `features-onchain-service/handlers/lst_yields.py` + `perp_funding.py` shipped; **NO live VM running today** (no recent events at `gs://{pid}-events/events/features-onchain-service/...`) |
| 7. Custody + treasury            | ⚠️ Copper started (`execution-service/custody/copper_provider.py`); ❌ CEFFU stub (no `ceffu_provider.py`); per master plan Q&A 3 — CEFFU manual handoff acceptable for May 23                         |
| 8. Kill-switch + alerting        | ⚠️ Framework shipped (`risk_and_exposure_service/kill_switch_rules.py`); carry_staked_basis-specific rules NOT enumerated; alerting-service rules pending                                              |
| 9. Event-stream verification     | ⚠️ Framework exists; carry_staked_basis-specific event signature not codified                                                                                                                          |

## 2 — Service-readiness Groups A-G (RED-item summary)

| Service                           | Group · Item                | Status | Cutover-blocking? | Owner Tab       |
| --------------------------------- | --------------------------- | ------ | ----------------- | --------------- |
| execution-service                 | F · 17 (Backtest fidelity)  | ❌     | YES               | Tab 8           |
| strategy-service                  | F · 17 (Backtest fidelity)  | ❌     | YES               | Tab 8           |
| strategy-service                  | F · 18 (2-yr grid backtest) | 🟡     | YES               | Tab 8           |
| strategy-service                  | F · 20 (Live testnet)       | 🟡     | YES               | Tab 8           |
| execution-service                 | F · 20 (Live testnet)       | 🟡     | YES               | Tab 8           |
| batch-live-reconciliation-service | A · 1-3 (Code health)       | ❌     | YES               | Tab 6           |
| batch-live-reconciliation-service | F · 21 (Reconciliation)     | 🟡     | YES               | Tab 6           |
| alerting-service                  | F · 22 (Trading guardrails) | 🟡     | YES               | (alerting plan) |
| risk-and-exposure-service         | F · 22 (Trading guardrails) | 🟡     | YES               | (alerting plan) |
| client-reporting-api              | M · 4-5 (PnL view symmetry) | ❌     | PARTIAL           | Tab 7           |

**Top 2 P0 hard-blocks**: execution-service F17 (matching engine fidelity unproven — depends on
`simulation_scenarios_topology_price_shocks` Phase 9 which never ran) · batch-live-reconciliation-service Group A
(service scaffolded but not code-complete).

## 3 — ServiceEmissionPolicy seed-dict gaps (cutover-blocking)

Per CLAUDE.md "Reason taxonomy" + UTL `emission_publisher.py` — every service declares a `ServiceEmissionPolicy` enum
entry. **9 services MISSING** UAC seed-dict entries:

| service                           | missing entry             |
| --------------------------------- | ------------------------- |
| execution-service                 | `(execution, fills)`      |
| market-data-processing-service    | `(mdps, candles)`         |
| market-tick-data-service          | `(mtds, ticks)`           |
| features-service (consolidated)   | per-feature-group entries |
| strategy-service                  | `(strategy, signals)`     |
| position-balance-monitor-service  | `(pbm, positions)`        |
| risk-and-exposure-service         | `(rae, risk_scores)`      |
| batch-live-reconciliation-service | `(recon, green_status)`   |
| alerting-service                  | `(alerts, rules)`         |

**Seed-dict location**: `unified_api_contracts/internal/service_emission_policy.py`. Tab 2 ships these as part of M9 +
Tab 6's reconciler entry as part of F21.

## 4 — Cross-plan coordination banners (per Tab)

Per CLAUDE.md "Cross-Plan Coordination Banners" HARD RULE — every Tab adds banners to every other active plan whose work
is influenced. Banner format: 🟢 VM RUNNING / 🟡 IN-FLIGHT REFACTOR / 🔴 BLOCK / BE-AWARE / RE-VERIFY.

- **Tab 1 (codex)** → `master_to_live_defi_2026_05_23.md` · `live_pipeline_mtds_mdps_features_2026_05_08.md` ·
  `features_repo_consolidation_2026_05_08.md` · `alerting_service_live_rules_2026_05_07.md` (all 🟡 IN-FLIGHT REFACTOR).
- **Tab 2 (UAC + UTL)** → `gcs_migration_bundle_pipeline_mode_2026_05_08.md` (BE-AWARE) ·
  `manifest_schema_final_gate_2026_05_09.md` (RE-VERIFY) · `live_pipeline_mtds_mdps_features_2026_05_08.md` (BE-AWARE) ·
  `defi_master_2026_05_07.md` (BE-AWARE).
- **Tab 3 (QG STEPs)** → `available_at_lookahead_bias_completion_2026_05_08.md` (🔴 BLOCK) ·
  `writegate_honest_coverage_endtoend_2026_05_06.md` (🔴 BLOCK) · `live_pipeline_mtds_mdps_features_2026_05_08.md` (🔴
  BLOCK) · `features_repo_consolidation_2026_05_08.md` (🔴 BLOCK) — until workspace QG green.
- **Tab 4 (features lift)** → `gcs_migration_bundle_pipeline_mode_2026_05_08.md` (🟡) ·
  `live_pipeline_mtds_mdps_features_2026_05_08.md` (🟡) · `features_repo_consolidation_2026_05_08.md` (RE-VERIFY).
- **Tab 5 (pipeline_mode VM fleet)** → `master_to_live_defi_2026_05_23.md` (🔴 BLOCK Phase 3) ·
  `gcs_migration_bundle_pipeline_mode_2026_05_08.md` (🟢 VM RUNNING — mirror) ·
  `live_pipeline_mtds_mdps_features_2026_05_08.md` (🔴 BLOCK Phase 5).
- **Tab 6 (reconciler)** → `master_to_live_defi_2026_05_23.md` (🔴 BLOCK F18 gate) ·
  `manifest_schema_final_gate_2026_05_09.md` (RE-VERIFY) · `live_pipeline_mtds_mdps_features_2026_05_08.md` (BE-AWARE).
- **Tab 7 (UI rollout)** → `deployment_ui_lifecycle_tabs_2026_05_08.md` (🟡 IN-FLIGHT REFACTOR) ·
  `master_to_live_defi_2026_05_23.md` (BE-AWARE G23) · `live_pipeline_mtds_mdps_features_2026_05_08.md` (BE-AWARE).
- **Tab 8 (carry_staked_basis E2E)** → `master_to_live_defi_2026_05_23.md` (🟢 VM RUNNING — 7-day wall-clock) ·
  `defi_master_2026_05_07.md` (🟢 VM RUNNING) · `alerting_service_live_rules_2026_05_07.md` (BE-AWARE drills).

## 5 — Compat paths + removal schedule (no-tech-debt § 3)

| compat path                                       | introduced in         | removal trigger                                                                                                | owner        | effort   |
| ------------------------------------------------- | --------------------- | -------------------------------------------------------------------------------------------------------------- | ------------ | -------- |
| pipeline_mode reader fallback levels 1/3/4        | Phase 1B (2026-05-08) | Phase 8 (T+30d post-Phase-3, ~2026-06-15) when `READER_FELL_BACK_TO_LEGACY_PATH` event count = 0               | Tab 5        | ~30 min  |
| pipeline_mode level 2 (legacy `category=`) reader | Phase 1B (2026-05-08) | NEVER — CLAUDE.md hive-vocab exception (read-only fallback, no writes)                                         | Tab 5        | n/a      |
| UI `RuntimeMode` redeclaration                    | pre-plan (mirror)     | Tab 7 close-out — UAC re-export from UTL + UCI codegen pipeline                                                | Tab 7        | ~2 hours |
| `LIVE_*` event-prefix anti-pattern (VMEventType)  | pre-plan              | Post-cutover (Block G1) — `VMEventType` rename + `mode` field on payload + 3-repo consumer sweep + semver-bump | post-cutover | ~1 day   |
| Feature bare-class fallback (pre-ModeHandler)     | pre-plan              | Tab 4 close-out — hard-delete 4 family classes once ModeHandler lift in prod                                   | Tab 4        | ~3 hours |
| MDPS dual-handler split (process vs live_mode)    | pre-plan              | Post-cutover (Block D2) — design proposal; refactor only if live shows divergence                              | post-cutover | 1-2 days |
| Shadow-simulated fills in live (Block A3 scope)   | (not yet introduced)  | Post-cutover only if operator pivots — Block D5 gates as post-scope                                            | post-cutover | 2-3 days |

## 6 — Risk register (top 12)

| #   | Risk                                                                          | L   | I   | Mitigation                                                                                                                                              | Owner            | Detection                                                  |
| --- | ----------------------------------------------------------------------------- | --- | --- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- | ---------------------------------------------------------- |
| 1   | MDPS dual-handler silently diverges batch ↔ live during cutover               | M   | H   | Tab 2 D1 audit + shared base abstract methods + L7 sweep + schema/error-reason parity unit test; 24h cutover-smoke                                      | Tab 2 + Tab 6    | Recon-green threshold spike on cutover day                 |
| 2   | pipeline_mode migration runs out of GCS quota mid-flight                      | L   | H   | Pre-Phase-3 cost audit; Terraform budget +50%; CloudOps quota alert; nights-only fallback                                                               | Tab 5 + operator | GCS quota alert; Phase-4 VM throttled                      |
| 3   | F21 reconciler ships but recon-green threshold uncalibrated → false alarms    | M   | M   | Tab 6 sweep against shipped 2-yr backtest; 7-day paper-trade calibration; 95p+2× margin starting point                                                  | Tab 6            | Recon alerts >5×/hr post-cutover                           |
| 4   | carry_staked_basis paper-trade soak hits venue testnet rate limits            | M   | H   | Pre-soak rate-limit confirmation across all 6 perp venues; staged Secret Manager keys; watchdog VM                                                      | Tab 8            | 429 errors in events; >10s order-place latency             |
| 5   | Tenderly fork breaks during paper-deploy (currently test-fixture only)        | M   | H   | execution-service integration test pre-flight; pre-deploy fork-swap smoke                                                                               | Tab 8            | swap returns "contract not found" / insufficient liquidity |
| 6   | Aave/Uniswap mainnet RPC + Secret Manager bindings missing on launch          | L   | H   | UAC `CHAIN_RPC_TEMPLATES` codex audit (Tab 1) + Secret path check (Tab 2) + startup `eth_getCode` validation; operator manual sign-off 1 day pre-launch | Tab 2            | RpcConnectionError / MissingSecretError on startup         |
| 7   | UI ExecutionModeContext rollout breaks build (parallel-agent collision)       | M   | M   | Tab 7 codex spec + Playwright matrix + Tab 7/Tab 3 commit serialisation                                                                                 | Tab 7 + Tab 3    | npm build fails / Playwright suite red                     |
| 8   | QG STEP L2/L3/L4 lands red on first run + blocks every PR                     | M   | M   | Tab 3 pre-flight on local repo; identify false-positives; pre-announce rollout window                                                                   | Tab 3            | Workspace CI red >2h; operator override needed             |
| 9   | J1 phase→mode helper signature wrong (operator pivots seam-count)             | L   | M   | Operator confirm Block A2 seam decision before Tab 2 ships helper; signature locked via unit tests                                                      | Tab 2            | helper unit tests fail; consumer startup fails             |
| 10  | Operator pivots — shadow-simulated live fills become cutover-blocking         | L   | M   | Block A3/D4 explicit deferral codified; reversal requires codex update + new Tab spawn (~5-10d slip)                                                    | master_to_live   | operator request after Tab 2/4/5/6 shipped                 |
| 11  | REPLAY_BACKSTOP_REACHED gate fires during cutover week                        | L   | M   | Tab 5 Phase 8 wiring + Tab 8 paper-trade gate-firing rehearsal + alert escalation runbook                                                               | Tab 5 + Tab 8    | event fires + strategy holds positions                     |
| 12  | F21 reconciler consumes wrong inputs (Tab 6 ships before Tab 5 schema stable) | M   | H   | Cross-Tab handshake: Tab 5 publishes manifest shape BEFORE Tab 6 implements; reconciler unit-tests mock real Tab 5 output                               | Tab 5 + Tab 6    | recon misreads pipeline_mode column; recon NaN             |

## 7 — Concurrent-agent collision matrix

| collision point                            | concurrent agents                            | risk     | mitigation                                                                                     |
| ------------------------------------------ | -------------------------------------------- | -------- | ---------------------------------------------------------------------------------------------- |
| UAC `internal/modes.py`                    | 2 (Tab 1 codex cross-link + Tab 2 J1 helper) | MEDIUM   | Tab 2 ships first; Tab 1 references shipped commit sha; conditional-push                       |
| UAC `BUNDLED_DATA_TYPES`                   | 3 (Tab 2 M9 + Tab 5 Phase 3 + Tab 6 F21)     | HIGH     | Tab 2 first (read-only); Tab 5 second (writer refactor); Tab 6 mocks Tab 2 snapshot in tests   |
| UTL `manifest_writer.py`                   | 2 (Tab 2 L7 sweep + Tab 5 Phase 3 refactor)  | MEDIUM   | Serialise: Tab 2 survey → Tab 5 refactor; Tab 5 includes L7 consumer fixes in same batch       |
| features-service base classes (4 families) | 4 sub-agents (Tab 4 fan-out)                 | LOW      | Per-family `git add -p`; sub-agent fan-out pattern from CLAUDE.md "Tab 4 close-out 2026-05-08" |
| UI ExecutionModeContext + 3 page files     | 4 (Tab 7 main + 3 sub-agents)                | HIGH     | SERIALISE NOT PARALLEL — main does context first + dashboard; subs wait + go sequential        |
| `master_to_live_defi_2026_05_23.md`        | 8 (every Tab flips own checkboxes)           | CRITICAL | Pre-agreed row ranges per Tab; per-shippable-unit commits; first-merge-wins                    |
| per-repo `quality-gates.sh`                | 8 (Tab 3 ships STEPs + others trigger)       | LOW      | Tab 3 ships STEP defs first (workspace-wide); other Tabs fix locally + re-push                 |
| Codex `batch-live-architecture.md`         | 8 (Tab 1 writer + Tabs 2-8 readers)          | MEDIUM   | Tab 1 ships codex first (commit + push); Tabs 2-8 pull + verify anchors before pushing         |

## 8 — Spawned-plan readiness checklist

The spawned plan `plans/active/batch_live_symmetry_2026_05_10.md` is execution-ready when:

- ✅ This manifest + the question doc's Code-derived answers + Plan-shape decisions are all populated (DONE).
- 🤔 Operator decisions (1-7 in question doc § "Operator decisions remaining") confirmed OR defaults accepted.
- ⏳ Tab 1-8 sub-agents have self-contained spawn prompts citing this manifest.
- ⏳ Cross-plan banners landed on the 14+ target plans before Tab work begins.
- ⏳ Risk register reviewed by operator; mitigations assigned to owner Tabs.
- ✅ Service-readiness Groups A-G RED items cited in master plan rollup (already there).
- ⏳ ServiceEmissionPolicy seed-dict gaps tracked as Tab 2 sub-todos.
- ⏳ Compat-paths schedule recorded in `## Temporary states + their canonical follow-up plans` section of spawned plan.
- ⏳ Full-execution criterion per Tab (per "Plans Run To Actual Completion" HARD RULE) listed in Tab done-definition.
- ⏳ Codex doc updates listed in spawned-plan body (per "Post-Plan-Phase Codex Audit" HARD RULE).

## 9 — Tab 8 paste-ready operator recipe

```bash
#!/bin/bash
set -e
STRATEGY="carry_staked_basis"
START_DATE="2026-05-10"; END_DATE="2026-05-10"
RUN_TS="$(date +%Y%m%d-%H%M%S)"
PID="$(gcloud config get-value project)"
ZONE="asia-northeast1-c"

# COMMAND #1: launch backtest VM
gcloud compute instances create "defi-carry-backtest-${RUN_TS}" \
  --image-family=unified-trading-base --image-project="${PID}" \
  --machine-type=n1-standard-8 --zone="${ZONE}" \
  --metadata-from-file startup-script=gs://deployment-scripts-${PID}/vm/setup-data-pipeline-vm.sh \
  --metadata="RUNTIME_MODE=batch,STRATEGY_ID=${STRATEGY},START_DATE=${START_DATE},END_DATE=${END_DATE}" \
  --scopes=cloud-platform --quiet
# VERIFY #1: gcloud compute instances describe "defi-carry-backtest-${RUN_TS}" --zone="${ZONE}" --format="value(status)"
#           expected: RUNNING

# COMMAND #2: monitor (poll until STOPPED, max 30min)
# VERIFY #2: gcloud storage ls "gs://${PID}-events/events/strategy-service/${START_DATE}/defi-carry-backtest-${RUN_TS}/"
#           expected: STARTED + per-instrument INSTRUMENT_PROCESSED + STOPPED

# COMMAND #3: fetch backtest scores
gcloud storage ls "gs://${PID}-strategy-outputs/backtest/${STRATEGY}/${END_DATE}/"
# VERIFY #3: parquet has populated columns (not 1440-NaN placeholders) — sample read + assert OHLC populated

# COMMAND #4: launch paper-deploy VM
# GREENFIELD: deployment-service/scripts/vm/launch-defi-paper-trading-vm.sh — Tab 8 P0
# Expected shape:
#   gcloud compute instances create "defi-carry-paper-${RUN_TS}" \
#     --metadata="RUNTIME_MODE=live,EXECUTION_MODE=simulated,STRATEGY_ID=${STRATEGY}" ...

# COMMAND #5: verify paper VM event stream
# VERIFY #5: STARTED within 60s + INSTRUMENT_PROCESSED + PAPER_FILL events + heartbeat

# COMMAND #6: 7-day soak monitoring
# Schedule via Claude ScheduleWakeup: delaySeconds=86400, prompt = daily soak check
#   - VM alive (gcloud compute instances list)
#   - events flowing (gcloud storage ls last hour)
#   - P&L accumulating (parquet read + sample row)
#   - Recon green (Tab 6 reconciler runs daily; check threshold)
```
