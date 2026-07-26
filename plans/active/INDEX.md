# Active Plans Index

**Last Updated:** 2026-07-12 (was: "2026-05-08 (live-pipeline activation triple — features-repo consolidation +
live-pipeline + GCS migration bundle)" — corrected 2026-07-12, doc-reconciliation finding 4, §A2 B-queue ruling: the
header timestamp was never refreshed as later entries were added, e.g. `prediction_capture_incident_remediation`
2026-07-06 and the is-daily-enum entry 2026-07-07, below)

This is the canonical index of all active plans. Plans are organized by domain.

---

## Cross-cutting SSOT (priority — data plane + agents)

**Read first** when touching venue routing, buckets, or market-data category maps (note — corrected 2026-07-12,
doc-reconciliation finding 3, §A2 B-queue ruling: several bullets below are inline-tagged **(ARCHIVED)** and link into
`archive/2026_05/` — those are historical context only, NOT current priority guidance; treat only the non-ARCHIVED
bullets as live "read first" material):

- [live_pipeline_mtds_mdps_features_2026_05_08.md](../archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md) —
  **(ARCHIVED)** (was: untagged despite linking into `archive/2026_05/` like its tagged siblings — corrected 2026-07-14,
  doc-reconciliation finding 3) **Live (websocket-streaming) pipeline activation** for MTDS / MDPS / consolidated
  features-service across all 5 asset_groups ahead of the 2026-05-23 DeFi cutover. Topology: MTDS standalone cluster
  (websocket-pool concerns isolated), MDPS+features-asset-scoped colocated per asset_group, features-cross-cutting
  standalone flavor of same image. Cascade: MTDS → MDPS → features-service via Redis Streams (CANDLE_BOUNDARY_CROSSED →
  CANDLE_COMPUTED → FEATURES_COMPUTED) with UTC midnight alignment end-to-end so batch ↔ live reconciliation is a
  `GROUP BY pipeline_mode` over the same manifest. Live gap semantics extend the 4-category empty-output tree with
  stale-not-missing wiring via ServiceEmissionPolicy.PUBLISHED_DEGRADED. Replay subsystem covers intraday- restart gap
  windows with smooth handoff to live at the next aligned boundary. Health-API extension + alerting-service tier-up +
  circuit breakers wired to strategy-service. Instrument-cache-delta hot-reload pattern (mirrors ApiKeyReloader; NOT a
  new dedicated stream). 15 phases, ~10d wall-clock. Pre-reqs: features_repo_consolidation Phase 7 +
  gcs_migration_bundle Phase 9.

- [features_repo_consolidation_2026_05_08.md](../archive/features_repo_consolidation_2026_05_08.plan.md) —
  **(ARCHIVED)** (was: plain link + "Pre-requisite for live-pipeline" framed as an open dependency gate — corrected
  2026-07-14, doc-reconciliation finding 5: file was archived to
  `plans/archive/features_repo_consolidation_2026_05_08.plan.md`, `status: archived`, large majority of phases/todos
  done/completed). **Pre-requisite for live-pipeline.** Merge 8 separate `features-*-service` repos (calendar /
  commodity / cross-instrument / delta-one / multi-timeframe / onchain / sports / volatility) into a single
  `features-service` repo with sub-packages per family, ONE Docker image parameterised by `--feature-family` CLI flag,
  ONE flat `pyproject.toml`, ONE Health-API. NEW UAC `feature_family` schema column (additive sibling-or-prefix of
  `feature_group` in v5 manifest). Lift 4 cross-family helpers (watermark+grace fan-in, available_at stamping,
  LookaheadBiasError gate, NaN write-gate) to UTL — currently duplicated across 5-6 repos. Pattern matches UMI→MTDS and
  UCI→UTL precedents. Naming explicitly disambiguated from ml_and_features_master Phase 2's feature-DATA consolidation
  (this is REPO consolidation). 10 phases, ~5d wall-clock with parallelism.

- [gcs_migration_bundle_pipeline_mode_2026_05_08.md](../archive/2026_05/gcs_migration_bundle_pipeline_mode_2026_05_08.md)
  — **Bundled (ARCHIVED)** overnight GCS migration\*\* that walks every parquet ONCE (millions across asset_groups) and
  applies the full set of pending hive-vocab + partition-column changes in a single pass so the canonical manifest is
  rewritten once instead of N times. Three migrations bundled: (1) NEW
  `pipeline_mode={batch_databento, batch_tardis, ..., live_websocket}` hive partition column; (2) finish the dual-vocab
  `category=` → `asset_group=` rekey CLAUDE.md previously preserved as legacy-with-fallback; (3) sweep the 5 drift axes
  from the 2026-05-04 phantom-audit incident (path-prefix, instrument_type casing, schema-4 empty instrument_type,
  chain-bundle equivalence) so the 354 residual phantoms clear. Reader fallback ≤30 days post-migration then deleted.
  Coordinates with manifest_migration_SUPERSEDED_2026_05_21 Stage 1+2+3 (must complete first) + Stage 4 (folds in here).
  9 phases including operator-gated VM fleet execution.

- [instrument_catalogue_availability_matrix_2026_04_29.md](../archive/instrument_catalogue_availability_matrix_2026_04_29.plan.md)
  — **(ARCHIVED, status: complete)** (was: plain link to a nonexistent `active/` path — corrected 2026-07-14,
  doc-reconciliation finding 4: file was archived to
  `plans/archive/instrument_catalogue_availability_matrix_2026_04_29.plan.md`, work complete). Joins **static
  shard-dynamics SSOT** (bucket → partition layout → schema → coverage-start → retention/cutoff → live/batch capability
  per `(asset_group × data_type × venue × instrument_type)`) with **live availability-manifest aggregation**
  (capture_status → coverage %). Publishes `instrument-catalogue.{json,md}` + `shard-dynamics.json` nightly to
  `gs://strategy-store-cefi-{pid}/catalogue/instrument/`. New UI matrix widget cross-links existing data-status
  drilldown. Pulls bucket-naming + partition-layout + coverage-start + capability registries into UAC (sports already
  SSOT, others scattered). Depends on shard-dimension naming + venue-axis vocabulary plans.

- [deployment_ui_lifecycle_tabs_2026_05_08.md](../archive/2026_05/deployment_ui_lifecycle_tabs_2026_05_08.md) —
  **Cross-cutting 6-tab (ARCHIVED)** restructure\*\* of deployment-UI organised around four orthogonal axes: lifecycle
  class (EPHEMERAL_BATCH / EPHEMERAL_EXPERIMENT / SCHEDULED_RECURRING / LONG_LIVED_LIVE), cloud target (GCP / AWS),
  environment tier (DEV / STAGING / PROD — resolved by domain, never an in-UI toggle), service / asset_group. Tabs:
  Deploy (fresh deployments only) / Monitor (renamed from History; sub-tabs Backfill / Experiments / Live / Scheduled —
  runtime state of every job, cluster, scheduler with re-deploy / stop / start / pause / drain / stream-logs /
  attach-events actions on each row using the SAME row-template) / Data Status (scoped to data + pricing only —
  instruments / MTDS / MDPS / features-\*; with Batch / Scheduled-Today / Live mode toggle) / Builds / Readiness /
  Config. Header carries cloud-toggle (slow refresh) + env badge (read-only). Cross-Monitor-sub-tab navigation is
  INSTANT (prefetch context); cloud-toggle pays network round-trip; env switch happens by changing domain. Auth
  always-available (UnifiedCloudConfig loads both clouds at api-boot). NEW UAC SSOTs: `LifecycleClass` enum (4 members),
  `EnvironmentTier` enum + domain-resolver, scheduler registry (env-scoped), live-cluster registry (env-scoped),
  experiment registry. NEW UTL helper `experiment_tracker.py` (run_id / metric / step / artifact emission for ML /
  strategy / execution research jobs). NEW codex docs: `deployment-ui-architecture.md` (UX SSOT) +
  `deployment-ui-environment-tiers.md` (dev/staging/prod hosting, mirrors trading-system-UI pattern +
  firebase-split-topology). NEW deployment-api routes: `/api/monitor/{backfill,experiments,live,scheduled}`,
  `/api/logs/stream/{target_ref}`. Most infrastructure already exists (SSE event-stream, CloudProviderContext,
  deploy-missing, data-status drilldown, vm-launcher registry); plan is mostly re-shape + wire-in with one greenfield
  slice (Experiments tracker) and one infra slice (env-tier hosting of deployment-UI/API itself). Sibling-of
  `instruments_master`; Phase G of that plan delegates UI scope here.

- [hard_schema_enforcement_2026_05_08.md](../archive/2026_05/hard_schema_enforcement_2026_05_08.md) — **Workspace-wide
  hard schema (ARCHIVED)** enforcement at the write boundary\*\* (sub-plan of `infrastructure_master`). Today only
  predictions has hard-required lifecycle enforcement; every other asset_group leaves required fields nullable
  (base_currency / quote_currency / chain_id / contract_address / decimals / fixture_id / futures expiry) and the write
  path fails venue-shard-wide rather than per-row, masking partial-data bugs. Sports adapters minimal-flatten (18-30
  columns dropped). 5 phases: UAC schema audit + nullable→required flips per asset_group; orchestrator per-row
  try/except refactor (record_failed SCHEMA_VALIDATION_FAILED); 6 sports adapter full-column capture audit; UTL row_key
  shape validation; PM QG STEP 5.66 static assertion. Operator decision 2026-05-08: SEQUENCE after `tradfi_master` Q1+Q2
  futures-expiry ships (avoids mass-fail-during-transit). Migrated from archived issue
  `hard_schema_enforcement_at_write_boundary_2026_05_08.md`.

- [cme_polymarket_arb_2026_05_08.md](../archive/2026_05/cme_polymarket_arb_2026_05_08.md) — **(ARCHIVED, status:
  complete)** (was: plain link + "Phases 1-5 here" framed as open work, no ARCHIVED tag despite sitting in this
  ARCHIVED-tagged-bullets section — corrected 2026-07-14, doc-reconciliation finding 2: file archived to
  `plans/archive/2026_05/cme_polymarket_arb_2026_05_08.md`, all 5 phases checked done). **CME × Polymarket cross-venue
  event-arb** (post-May-23 critical path). 9 CME event-contract roots (ECES / ECBTC / ECRTY / ECYM / ECGC / ECCL / ECNG
  / EC6E / ECNQ) are semantically identical to Polymarket binary outcomes; cross-venue basis is exploitable but
  invisible today. Operator decision 2026-05-08 Option (a) split: Phase 0 catalog backfill in `tradfi_master`; Phases
  1-5 here (InstrumentType.EVENT_CONTRACT enum; linked_canonical_question_group cross-link blocked on predictions_master
  Phase 5 canonical-groups backfill; MTDS binary-outcome shard atom; per-cluster expiry; cme_polymarket_event_arb
  strategy archetype + cross-venue execution routing). Migrated from archived 26KB RFC
  `cme_event_contracts_cross_venue_arb_shard_design_2026_05_08.md`.

- [instruments_master.md](../epics/instruments_master.md) — **Activation surface for instruments-live across all 5
  asset_groups** (cefi 15-min CCXT replacing Tardis-T+1; tradfi 15-min Polygon/Yahoo replacing Databento for live;
  sports trigger-driven — daily fixture re-poll + per-league season-roll → teams / mappings + annual transfer-window →
  players + weather cascade pre-kickoff; predictions 15-min market-discovery). Live writes to SAME GCS path as batch (no
  separate live path); T+1 is retrospective audit / comparison job, NOT a backfill. Cloud Scheduler activation
  per-trigger + new deployment-UI "Scheduled Jobs" tab listing every cron invocation with last-run / next-fire / recent
  events / Telegram-alert-on-fail. Critical Phase A.9–A.11 codifies the preflight DAG (downstream-needs-upstream-first)
  as a UAC SSOT + UTL helper invoked identically by live and batch — typed `INSTRUMENTS_LIVE_PREFLIGHT_FAILED` +
  `INSTRUMENTS_LIVE_UPSTREAM_STALE` events route to Telegram with the specific missing-upstream named in the message.
  References (does NOT duplicate) the existing codex SSOTs (`batch-live-architecture`, `backfill-and-live-startup`,
  `live-deployment-monitoring`, `alerting-batch-live`, `sports-live-odds-connectivity`, `runtime-tiers-and-deployment`)
  and 8 active issues for data-correctness deltas. Sibling-of (NOT child-of) `master_to_live_defi_2026_05_23` — only
  Phase D (cefi 15-min CCXT) + Phase F.3 (AWS EventBridge mirror) are on the May-23 critical path; the rest is
  post-cutover.

---

## DeFi Strategy Testing & Automation (NEW)

**⭐ START HERE:** [defi-strategy-testing-quickstart.md](../archive/defi-strategy-testing-quickstart.md) — Quick
reference + examples for testing any DeFi strategy

**Detailed Plans:**

- [defi-strategy-ui-verification.md](../ai/defi-strategy-ui-verification.plan.md) — Phase 1: Verify UI widgets with
  mocked data
- [defi-strategy-e2e-automation.md](defi-strategy-e2e-automation.md) — Full pipeline: UI verification → test generation
  → execution → regression protection

---

## Currently Active Plans

**⚠️ STALE ENTRIES (flagged 2026-07-14, verify-rerun-2 finding 221 — violates this doc's own
`INDEX.md must be updated whenever a plan is added or archived` rule, `PLAN_FORMAT.md:619`):** the 8 plans below are
tagged **(ARCHIVED — was: listed as active, no tag)** — verified present only in `plans/archive/` as `<slug>.plan.md`,
absent from `plans/active/`: `agent1_shell_navigation_2026_03_22.md`, `agent2_trading_service_2026_03_22.md`,
`agent5_api_service_layer_2026_03_22.md`, `agent6_mock_data_quality_2026_03_22.md`,
`agent8_e2e_tests_quality_2026_03_22.md`, `defi_phase3_infrastructure_2026_03_30.md`,
`defi_strategies_phase2_2026_03_29.md`, `instruments_service_reorganisation_2026_03_27.md`. Do not dispatch or treat as
current work.

### Infrastructure & Setup

- agent1_shell_navigation_2026_03_22.md — **(ARCHIVED)** Shell navigation framework
- agent2_trading_service_2026_03_22.md — **(ARCHIVED)** Trading service setup
- agent5_api_service_layer_2026_03_22.md — **(ARCHIVED)** API service layer

### DeFi Strategy Rollout

- [defi_ui_component_audit_2026_03_31.md](../ai/defi_ui_component_audit_2026_03_31.plan.md) — **(DRAFT — plans/ai/,
  never promoted to active/ — corrected 2026-07-25, plan-reconcile finding)** UI component audit
- defi_phase3_infrastructure_2026_03_30.md — **(ARCHIVED)** Infrastructure completion
- defi_strategies_phase2_2026_03_29.md — **(ARCHIVED)** Phase 2 strategies

### Sports

- [sports_predictions_e2e_2026_05_05.md](../archive/sports_predictions_e2e_2026_05_05.plan.md) — **(ARCHIVED — corrected
  2026-07-25, plan-reconcile finding)** Drives sports predictions running end-to-end: feature-service-sports →
  ml-training (Model 2A walk-forward) → strategy-service paper trade (ArbitrageStrategy + MLSportsStrategy) →
  execution-service paper fills + matching-engine for execution alpha → upcoming-fixtures-ui shows predictions. Path:
  re-key existing 288M Odds-API rows (`migrate_sports_canonical.py`, idempotent, no API) + MDPS 8-bucket horizon adapter
  (`SportsBucketAssignmentAdapter`, no API) → FSS feature compute → ML → strategy → UI. Folds
  `sports_e2e_validation_2026_03_27` Phases 2/3/5; Phase 4 re-collection budget dropped (predictions don't need it).
  Depends on master roadmap Phase 6, UTL base-image rebuild, and features_sports_honest_coverage_2026_05_05.
- [run_lifecycle_events_ssot_2026_05_05.md](../archive/run_lifecycle_events_ssot_2026_05_05.plan.md) — **(ARCHIVED —
  corrected 2026-07-25, plan-reconcile finding)** Cross-cutting observability fix per the 2026-05-05 CLAUDE.md "No
  fire-and-forget VM launches" rule. 4 phases: (1) UTL helper `run_lifecycle(service_name, details=...)` context
  manager + unit tests in `unified_trading_library.events`; (2) audit every long-running entry-point in the workspace;
  (3) rollout to MTDS migrates / MDPS / instruments-service / deployment-service / FSS / strategy / execution; (4)
  base-service.sh STEP 5.63 QG enforcement. Closes the gap where 11 audited scripts emit `setup_events` but no
  RUN_STARTED + terminal RUN_COMPLETED|FAILED. Reference incident: migrate_sports_canonical patched ad-hoc in MTDS
  ce9b069; this plan rolls the helper into UTL so every script gets the same shape.
- [instruments_service_write_gate_validation_2026_04_22.md](../ai/instruments_service_write_gate_validation_2026_04_22.plan.md)
  — **(DRAFT — plans/ai/, never promoted to active/ — corrected 2026-07-25, plan-reconcile finding)** Close the
  architectural gap where raw-data sinks in instruments-service bypass UTL's point-in-time validators entirely. Every
  `sink.write(...)` gates through
  `InstrumentsWriteGate.validate_and_write(df, partition, batch_date, mode='strict'|'warn')` asserting
  `value.date() <= batch_date` for every as-of column candidate. Warn-mode rollout measures violation volume; flip to
  strict once adapters clean. Motivated by the 2026-04-22 TM-VM incident (bugs fixed in instruments-service `cdded95`)
  which existed undetected on HEAD because zero UTL validators fire at raw-data write time. 3 repos (UTL +
  instruments-service + PM).

### Prediction

- [prediction_consolidated_closeout_2026_07_18.md](prediction_consolidated_closeout_2026_07_18.md) — One-pass prediction
  close-out aggregating every open prediction + prediction-touching IS/MTDS plan/issue: Phase A code → B migrations
  (manifest/catalogue/CQG canonicalisation + enumeration-driven dedupe) → C data-status/honest-coverage (RE-ADD the
  removed dimensions-enumeration view) → D re-smoke-test with `data-pipeline-check-{is,mtds}` adapted to prediction
  against `-test-` buckets → MVP-backfill-ready; **+ Phase E** football (soccer) cross-venue arb enablement (thread
  `af_fixture_id` onto Polymarket + Kalshi soccer, ~0% team-alias gap, unify the two disconnected arb paths).
  `parent_epic: predictions_master`.

### Data & Testing

- [instruments_to_100pct_eod_2026_05_04.md](../archive/instruments_to_100pct_eod_2026_05_04.plan.md) — **(ARCHIVED —
  link corrected 2026-07-25, plan-reconcile finding: was a 404, real file is
  plans/archive/instruments_to_100pct_eod_2026_05_04.plan.md)** instruments-service to ≥99% honest coverage across all 5
  asset groups (sibling to MTDS plan; epic: data-pipeline-completion).
- [market_tick_data_to_100pct_2026_05_05.md](../archive/market_tick_data_to_100pct_2026_05_05.plan.md) — **(ARCHIVED —
  link corrected 2026-07-25, plan-reconcile finding: was a 404, real file is
  plans/archive/market_tick_data_to_100pct_2026_05_05.plan.md)** market-tick-data-service raw download to ≥99% honest
  coverage across all 5 asset groups. **GCS-truth-first**: Phase 0.1 inverse-phantom audit
  (parquet-on-disk-no-manifest-row) is a mandatory gate before any backfill VM launches — prevents wasted
  Tardis/Databento/DeFi-RPC/odds-API spend on data we already have. Per-AG decision: manifest rebuild (cheap) vs
  backfill (paid). Phase 2 launchers: `launch-cefi-sharded-backfill.sh`, `launch-tradfi-backfill-vm.sh`,
  `launch-mtds-prediction-backfill-vm.sh`, MTDS DeFi data-type launchers. Depends on instruments plan above.
- agent6_mock_data_quality_2026_03_22.md — **(ARCHIVED)** Mock data quality
- agent8_e2e_tests_quality_2026_03_22.md — **(ARCHIVED)** E2E testing
- ui_full_site_link_crawler_e2e_2026_04_22.md — Full-site Playwright link crawler in `unified-trading-system-ui`
  (bounded BFS, shadow-DOM link harvest, nav flyouts, tier0 registry fill, optional external HEAD/GET probes); harden
  `webServer` for Tier 0 (`PLAYWRIGHT_SKIP_API_WEBSERVER`, `/login` readiness); document wall-clock presets + optional
  CI/nightly.

### Service Remediation

- [citadel_per_service_remediation_2026_03_24.md](../ai/citadel_per_service_remediation_2026_03_24.plan.md) — **(DRAFT —
  plans/ai/, never promoted to active/ — corrected 2026-07-25, plan-reconcile finding)** Per-service fixes
- instruments_service_reorganisation_2026_03_27.md — **(ARCHIVED)** Instruments service
- prediction_capture_incident_remediation_2026_07_06.md — Remediation for the 07-01→07-06 prediction-capture outage: (A)
  capture-path dtype hardening (UTL Int64/bool/float coercion shipped; residuals split out, see below) + (B)
  KALSHI/POLYMARKET-PERP adapter correction (wrong Kalshi host → fake PERPETUAL contamination of cefi — guard + purge
  DONE (guard+purge); demo-first repoint (Phase 1-3, no access needed) is PARALLEL/unblocked; prod cutover (Phase 4)
  gated on operator access — corrected 2026-07-12, finding id 2, §A2 "50 reclassified" blanket ruling (was: "demo-first
  repoint gated on the pre-existing `prediction_venue_perps_and_live_clob_depth` plan's ownership" — unsupported;
  Workstream B's own header + Phase 0-3 in `prediction_capture_incident_remediation_2026_07_06.md`, and the sibling plan
  itself, contain no ownership-gating statement anywhere in their bodies)). References issue
  `issues/prediction_universe_capture_dead_since_07_01_2026_07_06.md`.
- **is-daily-enum capture heal + consolidator fix — split 2026-07-07:** is_daily_enum_capture_heal_2026_07_07.md
  (exc_info fix → real diagnosis → fix → backfill; one sequential thread; still `status: draft`, AO-ready, flip to
  `active` once AO updates land) +
  [manifest_consolidator_dtype_at_source_fix_2026_07_07.md](/plans/archive/2026_07/manifest_consolidator_dtype_at_source_fix_2026_07_07.md)
  — **(ARCHIVED 2026-07-25 — RESOLVED, both todos done, fix already shipped `unified-trading-library@02fc4661`, no
  longer AO-ready/pending)**. Both split from prediction_capture_incident_remediation's Workstream A. References issue
  `issues/is_daily_enum_prediction_sports_fail_despite_coercion_2026_07_06.md`.

### Library Consolidation

- [fold_uei_into_utl_2026_04_17.md](../archive/fold_uei_into_utl_2026_04_17.plan.md) — **(ARCHIVED — corrected
  2026-07-25, plan-reconcile finding)** Fold unified-trading-library into `unified_trading_library.events` (aggregate of
  both), migrate 30+ consumers, archive UEI repo

### Strategy Lifecycle & Catalogue (NEW 2026-04-21)

- performance_overlay_pbms_pnl_series_2026_04_22.md — Ship PBMS `GET /api/v1/accounts/{account_id}/pnl-series` + UTA
  `HttpPbmPerformanceClient` so `<PerformanceOverlay>` uses real odum-paper / odum-live P&L streams (synth fallback
  unchanged). Depends on archived performance overlay primitive plan.
- [dart_exclusive_subscription_research_fork_2026_04_21.md](../archive/dart_exclusive_subscription_research_fork_2026_04_21.plan.md)
  — **(ARCHIVED — corrected 2026-07-25, plan-reconcile finding)** Plan D: DART exclusive-subscription model
  (`StrategyInstanceSubscription` with `dart_exclusive`/`im_allocation`/`signals_in` types + exclusive-lock invariant),
  client-authored research fork lifecycle (`StrategyVersion` draft → pending_approval → approved → rolled_out), joint
  Odum-client version governance gated on `backtest_1yr` + admin approval, UTA subscribe/fork/approve/rollout endpoints,
  strategy-service `version_governance` module with canonical backtest-pipeline re-use, DART UI Subscribe/Fork/Admin
  Approvals surfaces. 6 phases across UAC + UTL + UTA + strategy-service + UI + PM. Depends on Plans A + B + C.

### UI & Admin Unification

- [dashboard_services_grid_collapse_2026_04_21.md](../archive/dashboard_services_grid_collapse_2026_04_21.plan.md) —
  **(ARCHIVED — corrected 2026-07-25, plan-reconcile finding)** Collapse `/dashboard` tile grid 11 → 5 (DART · Odum
  Signals · Reports · Investor Relations · Admin & Ops), per-persona sub-route chips under each tile, and
  family/archetype filter strip above grid. Sibling to Phase-11 nav 8→4 collapse. Depends on archived
  [`ui_unification_v2_sanitisation_2026_04_20.md`](../archive/ui_unification_v2_sanitisation_2026_04_20.md).

### Deployment Topology & Client Isolation

- [deployment_topology_and_client_isolation_2026_04_17.md](../archive/deployment_topology_and_client_isolation_2026_04_17.plan.md)
  — **(ARCHIVED, status: complete)** (was: bare unlinked filename presented as an in-flight active-directory entry with
  a detailed "Phase 8 pending" progress claim — corrected 2026-07-14, doc-reconciliation finding 6: file was archived
  months ago to `plans/archive/deployment_topology_and_client_isolation_2026_04_17.plan.md`; frontmatter
  `status: complete`, though that archived file's own Phase 8a/8b todos remain `status: todo` internally). Per-service
  isolation policy (shared vs isolated), SLA tiers (basic/standard/premium) with cost passthrough, runtime profiles
  (backtest/paper/mock-live/staging/prod) collapsing 5 mode env vars, chaos + kill-switch primitives.
  runtime-topology.yaml v6→v7, UAC schemas, UTL readers, deployment-service/api/ui materialisation, downstream service
  wiring. 13 repos. **Progress as of 2026-04-17 live-defi-rollout:** Phases 1 (SSOT), 2a/2b (deployment-service/api),
  3a/3b/3c (UTL ChaosController + KillSwitchBus + ServiceBootstrap wiring + strategy/exec/risk subscribers), 4a
  (deployment-api runtime_profile env var fanout), 5 (18 archetype topology_requirements frontmatter + strategy-service
  enforcement module), 6 (PBM/R&E/PnL/execution isolation policy modules), 7 (8 e2e chaos scenarios), 4b (deployment-ui
  /client-subscriptions, /chaos pages, runtime_profile dropdown on DeployForm + 6 vitest cases) all committed locally.
  Phase 8 workspace QG sweep pending.

---

## How to Use This Index

1. **To find a plan:** Search this file for keywords or domain
2. **To run a plan:** Click the link and follow the plan's execution steps
3. **To create a new plan:** Add it to this INDEX with a one-line description, then update
   `[plan-placement.mdc](../../.cursor/rules/core/plan-placement.mdc)`

---

## Archive

For completed or superseded plans, see `archive/` directory.

### Bulk archive (2026-04-22)

The following 52 plans were moved from `active/` to [`archive/`](../archive/) with all Markdown checkboxes closed
(including residual items recorded as archive notes). Use the archive copy as the historical SSOT.

- [`autonomous_recovery_and_transfer_architecture_2026_04_16.md`](../archive/autonomous_recovery_and_transfer_architecture_2026_04_16.md)
- [`client_lifecycle_platform_2026_04_05.md`](../archive/client_lifecycle_platform_2026_04_05.md)
- [`defi_data_pipeline_e2e_2026_04_08.md`](../archive/defi_data_pipeline_e2e_2026_04_08.md)
- [`defi_demo_e2e_workflow_2026_03_30.md`](../archive/defi_demo_e2e_workflow_2026_03_30.md)
- [`defi_full_data_coverage_2026_04_09.md`](../archive/defi_full_data_coverage_2026_04_09.md)
- [`defi_pipeline_dedup_2026_04_11.md`](../archive/defi_pipeline_dedup_2026_04_11.md)
- [`features_sports_denormalisation_pipeline_2026_04_21.md`](../archive/features_sports_denormalisation_pipeline_2026_04_21.md)
- [`features_sports_derived_data_crime_fixes_2026_04_21.md`](../archive/features_sports_derived_data_crime_fixes_2026_04_21.md)
- [`granularity_per_category_config_2026_04_06.md`](../archive/granularity_per_category_config_2026_04_06.md)
- [`identity_registry_and_shard_enrichment_2026_04_16.md`](../archive/identity_registry_and_shard_enrichment_2026_04_16.md)
- [`institutional_feature_engineering_2026_04_11.md`](../archive/institutional_feature_engineering_2026_04_11.md)
- [`instruments_service_rolling_window_cli_flags_2026_04_21.md`](../archive/instruments_service_rolling_window_cli_flags_2026_04_21.md)
- [`marketing_site_restructure_2026_04_20.md`](../archive/marketing_site_restructure_2026_04_20.md)
- [`ml_pipeline_complete_2026_04_11.md`](../archive/ml_pipeline_complete_2026_04_11.md)
- [`mtds_per_instrument_sentinels_2026_04_21.md`](../archive/mtds_per_instrument_sentinels_2026_04_21.md)
- [`multichain_defi_expansion_2026_03_28.md`](../archive/multichain_defi_expansion_2026_03_28.md)
- [`orphan_audit_policy_2026_04_21.md`](../archive/orphan_audit_policy_2026_04_21.md)
- [`performance_overlay_continuous_timeline_2026_04_21.md`](../archive/performance_overlay_continuous_timeline_2026_04_21.md)
- [`permission_catalogue_2026_03_23.md`](../archive/permission_catalogue_2026_03_23.md)
- [`position_reconciliation_and_cost_preview_2026_04_16.md`](../archive/position_reconciliation_and_cost_preview_2026_04_16.md)
- [`recovery_and_transfer_completion_2026_04_16.md`](../archive/recovery_and_transfer_completion_2026_04_16.md)
- [`refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.md`](../archive/refactor_g1_10_questionnaire_to_configuration_flow_2026_04_20.md)
- [`refactor_g1_11_service_family_scope_rules_2026_04_20.md`](../archive/refactor_g1_11_service_family_scope_rules_2026_04_20.md)
- [`refactor_g1_12_public_site_ia_and_briefings_polish_2026_04_20.md`](../archive/refactor_g1_12_public_site_ia_and_briefings_polish_2026_04_20.md)
- [`refactor_g1_13_demo_upsell_overlay_tempt_logic_2026_04_20.md`](../archive/refactor_g1_13_demo_upsell_overlay_tempt_logic_2026_04_20.md)
- [`refactor_g1_14_presentation_deck_refresh_2026_04_20.md`](../archive/refactor_g1_14_presentation_deck_refresh_2026_04_20.md)
- [`refactor_g1_1_phase_unification_2026_04_20.md`](../archive/refactor_g1_1_phase_unification_2026_04_20.md)
- [`refactor_g1_2_instruction_schema_validation_service_2026_04_20.md`](../archive/refactor_g1_2_instruction_schema_validation_service_2026_04_20.md)
- [`refactor_g1_3_locked_visible_ui_service_tile_mode_2026_04_20.md`](../archive/refactor_g1_3_locked_visible_ui_service_tile_mode_2026_04_20.md)
- [`refactor_g1_4_persona_combinatorial_expansion_2026_04_20.md`](../archive/refactor_g1_4_persona_combinatorial_expansion_2026_04_20.md)
- [`refactor_g1_5_ml_catalogue_broken_hrefs_cleanup_2026_04_20.md`](../archive/refactor_g1_5_ml_catalogue_broken_hrefs_cleanup_2026_04_20.md)
- [`refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.md`](../archive/refactor_g1_6_derivation_engine_ship_to_strategy_service_availability_2026_04_20.md)
- [`refactor_g1_7_restriction_profile_engine_2026_04_20.md`](../archive/refactor_g1_7_restriction_profile_engine_2026_04_20.md)
- [`refactor_g1_8_uac_archetype_capability_v2_2026_04_20.md`](../archive/refactor_g1_8_uac_archetype_capability_v2_2026_04_20.md)
- [`refactor_g1_9_codex_scope_registry_2026_04_20.md`](../archive/refactor_g1_9_codex_scope_registry_2026_04_20.md)
- [`refactor_g3_6_visibility_slicing_e2e_expansion_2026_04_20.md`](../archive/refactor_g3_6_visibility_slicing_e2e_expansion_2026_04_20.md)
- [`reg_umbrella_questionnaire_and_onboarding_docs_2026_04_21.md`](../archive/reg_umbrella_questionnaire_and_onboarding_docs_2026_04_21.md)
- [`share_class_architecture_2026_04_01.md`](../archive/share_class_architecture_2026_04_01.md)
- [`sports_data_status_fixture_level_drilldown_2026_04_21.md`](../archive/sports_data_status_fixture_level_drilldown_2026_04_21.md)
- [`sports_scheduler_periodic_tier_dispatch_2026_04_21.md`](../archive/sports_scheduler_periodic_tier_dispatch_2026_04_21.md)
- [`strategy_architecture_v2_2026_04_17.md`](../archive/strategy_architecture_v2_2026_04_17.md)
- [`strategy_catalogue_3tier_surface_2026_04_21.md`](../archive/strategy_catalogue_3tier_surface_2026_04_21.md)
- [`strategy_docs_vs_system_audit_2026_04_15.md`](../archive/strategy_docs_vs_system_audit_2026_04_15.md)
- [`strategy_lifecycle_maturity_model_2026_04_21.md`](../archive/strategy_lifecycle_maturity_model_2026_04_21.md)
- [`strategy_registry_v1_delete_and_consumer_migration_2026_04_21.md`](../archive/strategy_registry_v1_delete_and_consumer_migration_2026_04_21.md)
- [`structured_error_handling_2026_03_22.md`](../archive/structured_error_handling_2026_03_22.md)
- [`ui_sync_hardening_2026_03_23.md`](../archive/ui_sync_hardening_2026_03_23.md)
- [`ui_unification_v2_sanitisation_2026_04_20.md`](../archive/ui_unification_v2_sanitisation_2026_04_20.md)
- [`umi_mtds_merger_2026_04_11.md`](../archive/umi_mtds_merger_2026_04_11.md)
- [`upcoming_fixtures_ui_view_2026_04_21.md`](../archive/upcoming_fixtures_ui_view_2026_04_21.md)
- [`utl_manifest_migration_primitives_2026_04_21.md`](../archive/utl_manifest_migration_primitives_2026_04_21.md)
- [`vm_observability_codex_update_2026_04_21.md`](../archive/vm_observability_codex_update_2026_04_21.md)
