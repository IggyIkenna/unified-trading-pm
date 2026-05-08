---
plan_type: code+infra
asset_group: cross-cutting
owner: ikenna
created: 2026-05-08
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
name: deployment-ui-lifecycle-tabs-2026-05-08
overview: >-
  Re-shape the deployment-UI + deployment-api into a single SSOT surface for everything deployable, monitorable, and
  observable in the workspace, structured around four mutually-orthogonal axes: (1) Lifecycle class — EPHEMERAL_BATCH
  (data + pricing pipeline jobs: instruments → MTDS → MDPS → features), EPHEMERAL_EXPERIMENT (ML / strategy / execution
  research jobs each with a run_id), SCHEDULED_RECURRING (Cloud Scheduler / EventBridge / VM cron), LONG_LIVED_LIVE
  (strategy / execution / live-MTDS / position-balance / risk / alerting clusters); (2) Cloud target GCP / AWS; (3)
  Environment dev / staging / prod (resolved by domain — `localhost` = dev, `staging.<research-domain>` = staging,
  `<research-domain>` = prod — same model the trading-system-UI followed; never an in-UI toggle); (4) Service /
  asset_group axis (existing sidebar). Tab structure folds onto this: Deploy (fresh deployments only), Monitor (renamed
  from History; sub-tabs Backfill / Experiments / Live / Scheduled — every action visible here: re-deploy, stop, start,
  pause, drain, stream-logs, attach-events), Data Status (data + pricing only — instruments, MTDS, MDPS, features-*;
  Batch / Scheduled-Today / Live mode toggle), Builds (single tab, cloud-toggle), Readiness (existing), Config
  (existing). Header carries the cloud-target toggle (GCP / AWS — the only toggle that pays a network round-trip;
  cross-mode prefetch keeps everything else instant) plus an env badge derived from the domain. Auth + credentials
  always-available — `UnifiedCloudConfig` loads both clouds at api-boot; toggling never re-authenticates. NEW UAC SSOTs:
  `LifecycleClass` enum (4 members), scheduler registry, live-cluster registry, experiment registry. "Deploy-missing
  schedulers" mirrors batch deploy-missing against the registry. VM naming- convention extends to encode
  `lifecycle_class`. Most infrastructure already exists (SSE event-stream, CloudProviderContext, deploy-missing,
  data-status drilldown, vm-launcher registry, vitest+forks); this plan is mostly re-shape + wire-in, with one
  greenfield slice (Experiments tracker) and one infra slice (env-tiered hosting of deployment-UI/API itself).

type: mixed
epic: epic-deployment
status: active

completion_gates:
  code: C5
  deployment: D3
  business: B6

repo_gates:
  - repo: deployment-ui
    code: C0
    deployment: none
    business: none
  - repo: deployment-api
    code: C0
    deployment: none
    business: none
  - repo: deployment-service
    code: C0
    deployment: none
    business: none
  - repo: unified-api-contracts
    code: C0
    deployment: none
    business: none
  - repo: unified-cloud-interface
    code: C0
    deployment: none
    business: none
  - repo: unified-trading-pm
    code: C0
    deployment: none
    business: none

depends_on:
  - deployment-api-work-stream-a-2026-05-07
  - launcher-scripts-consolidation-into-deployment-service-2026-05-07
  - infrastructure-master-2026-05-07

todos:
  # ──────────────────────────────────────────────────────────────────────
  # Phase A — Foundation: lifecycle-class taxonomy + naming convention SSOT
  # All Phase A items are PARALLEL within the phase.
  # ──────────────────────────────────────────────────────────────────────

  - id: a1-lifecycle-class-taxonomy-uac-ssot
    content: |
      - [ ] [SCRIPT] P0. Add `LifecycleClass` StrEnum to UAC
        `unified_api_contracts/canonical/crosscutting/lifecycle_class.py` with FOUR closed members:
        (1) `EPHEMERAL_BATCH` — data + pricing pipeline jobs (instruments, MTDS, MDPS, features-*); has start + end;
        progress measured in dates × shards captured/empty/failed. (2) `EPHEMERAL_EXPERIMENT` — ML training,
        strategy backtest, execution backtest research jobs; has start + end; progress measured in epochs / folds /
        run-id metrics; produces model artifacts + result blobs. (3) `SCHEDULED_RECURRING` — Cloud Scheduler /
        EventBridge / VM cron; expected to fire forever; "missing" + "paused" + "stale" states matter. (4)
        `LONG_LIVED_LIVE` — continuous deployment cluster (strategy / execution / live-MTDS / position-balance /
        risk / alerting); lifecycle actions are start/stop/pause/restart/drain. UAC helpers
        `classify_vm_name(vm_name) -> LifecycleClass`, `classify_cloud_run_service(name) -> LifecycleClass`,
        `classify_scheduled_job(name) -> LifecycleClass`, `classify_experiment_run(run_id) -> LifecycleClass`.
        Single source of truth — deployment-api + UI + watchdog + experiment-tracker all read from here.

  - id: a2-vm-naming-convention-extension
    content: |
      - [ ] [SCRIPT] P0. Extend `deployment-service/scripts/vm/vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` dict
        shape from `{prefix: bucket}` to `{prefix: VmPrefixSpec(bucket=..., lifecycle_class=...)}` where
        `VmPrefixSpec` is a typed UAC dataclass (Phase A.1). Migration: existing prefixes get explicit tags —
        backfill / migration / smoke / forward-poll / consolidator → `EPHEMERAL_BATCH`; manifest-consolidator-60s
        → `SCHEDULED_RECURRING`; reserve `live-strategy-`, `live-execution-`, `live-mtds-`, `live-pbm-`,
        `live-risk-`, `live-alerting-` for `LONG_LIVED_LIVE`; reserve `exp-ml-`, `exp-strategy-`, `exp-execution-`
        for `EPHEMERAL_EXPERIMENT`. New rule in CLAUDE.md "VM Naming Convention" section: every new VM prefix MUST
        tag a `lifecycle_class`; an experiment VM additionally tags its `run_id` in the VM name suffix
        (`exp-ml-{run_id}-{ts}`).

  - id: a3-codex-deployment-ui-architecture-ssot
    content: |
      - [ ] [AGENT] P0. New codex doc `codex/05-infrastructure/deployment-ui-architecture.md` capturing the full
        UX architecture: 6 top-level tabs (Deploy / Monitor / Data-Status / Builds / Readiness / Config); Monitor
        sub-tab structure (Backfill / Experiments / Live / Scheduled); the four orthogonal axes (lifecycle class /
        cloud target / environment / service); the env-resolution-by-domain rule (no in-UI env toggle); the
        cross-mode prefetch policy (instant) vs the cloud-toggle loading-state policy (slow + acceptable); the
        auth-always-available contract; the scope split between Data-Status (data + pricing correctness only) and
        Monitor (runtime state of all jobs/clusters/schedules); the streaming-logs surface contract (one component
        powers logs across all four lifecycle classes). NEW doc REFERENCES existing
        `04-architecture/deployment-topology-diagrams.md`, `05-infrastructure/launcher-script-ssot.md`,
        `05-infrastructure/runtime-tiers-and-deployment.md`, `05-infrastructure/deployment-clusters-live-vs-batch.md`,
        `05-infrastructure/cloud-agnostic-script-pattern.md`, `05-infrastructure/firebase-split-topology.md`.
        Single source of truth for the UX shape.

  - id: a4-codex-update-batch-live-symmetry-ux-section
    content: |
      - [ ] [AGENT] P1. Extend `04-architecture/batch-live-symmetry.md` with a "UX surface" section explicit on how
        the symmetry shows up to the operator: same Data-Status tab, same drilldown depth, same parquet schema-view,
        same event-tail; the only operator-visible difference between live and batch is the Data-Status mode-toggle
        position. Reinforces the engineering invariant via the operator-facing UX.

  - id: a5-uac-cloud-target-and-environment-discriminators
    content: |
      - [ ] [SCRIPT] P0. Confirm + extend the existing `CloudTarget` enum in deployment-ui `CloudProviderContext.tsx`
        and add a typed UAC mirror `unified_api_contracts/canonical/crosscutting/cloud_target.py` (already in scope).
        ALSO add `unified_api_contracts/canonical/crosscutting/environment_tier.py` as a 3-member StrEnum
        (`DEV` / `STAGING` / `PROD`) with helper `resolve_environment_from_hostname(hostname) -> EnvironmentTier`
        encoding the rule: `localhost` / `127.0.0.1` / `*.local` → DEV; `staging.<research-domain>` → STAGING;
        `<research-domain>` (no subdomain) → PROD. Server-side mirror in deployment-api boot-time config — knows its
        own env from `CLOUD_DEPLOYMENT_ENV` env var (already used elsewhere in workspace per
        `runtime-tiers-and-deployment.md`). The UI's env badge in Header reads the resolved tier; never offers an
        in-UI toggle. Auth contract: deployment-api boots with both GCP + AWS auth/credentials loaded into its
        session (existing `UnifiedCloudConfig` pattern); a UI cloud-toggle never re-authenticates — it just changes
        which client is dispatched per request.

  # ──────────────────────────────────────────────────────────────────────
  # Phase B — UI restructure: 6-tab shell + Monitor sub-tabs + prefetch
  # Depends on Phase A taxonomy.
  # ──────────────────────────────────────────────────────────────────────

  - id: b1-six-tab-shell-deploy-monitor-data-builds-readiness-config
    content: |
      - [ ] [SCRIPT] P0. Re-shape `deployment-ui/src/App.tsx` tab bar from current 7 tabs (Deploy / Status /
        History / Builds / Data Status / Readiness / Config) to 6 tabs (Deploy / Monitor / Data Status / Builds /
        Readiness / Config). Renames: History → Monitor (semantic re-purposing — the tab is for runtime state,
        not just past deploys). Removed: standalone Status tab (Status content folds into Monitor sub-tabs per
        lifecycle class). Header carries: cloud-target toggle (GCP / AWS), env badge (read-only, derived from
        domain per Phase A.5). Service-axis sidebar persists unchanged — every tab still scopes to a selected
        service when relevant; service-axis is orthogonal to the lifecycle-class tab axis.

  - id: b2-monitor-tab-four-subtabs
    content: |
      - [ ] [SCRIPT] P0. Monitor tab gets four sub-tabs, one per lifecycle class:
        (a) **Backfill** — list of currently-running + recent ephemeral data-pipeline jobs (instruments / MTDS /
        MDPS / features-* backfills, smokes, migrations); per-job: progress %, dates-completed / total, shards
        captured/empty/failed counts (live event count from the events bucket), live event-tail, stop / restart /
        re-deploy actions.
        (b) **Experiments** — list of currently-running + recent ML / strategy / execution research jobs; per-job:
        run_id, owner, current step (epoch / fold / backtest-day), progress %, ETA, hyperparams summary, key
        metrics live-tail (loss / sharpe / drawdown), result-blob link if completed, stop / restart / re-deploy.
        (c) **Live** — list of long-lived deployment clusters (strategy / execution / live-MTDS / position-balance
        / risk / alerting); per-cluster: replicas, health, last-heartbeat, freshness (last-write per data_type),
        start / stop / pause / restart / drain.
        (d) **Scheduled** — list of every scheduler in the Phase D registry, joined with runtime state;
        alive/dead/stale/paused/missing; per-row: run-now / pause / resume / logs / recent-events; "Deploy-Missing
        Schedulers" button.
        EVERY sub-tab uses the SAME row-component template (lifecycle-class-aware) so the operator sees one
        consistent layout across all four. The deploy-via-monitor pattern (re-deploy from Monitor's row context) is
        first-class; Deploy tab is exclusively for FRESH deployments.

  - id: b3-deploy-tab-fresh-deployments-only
    content: |
      - [ ] [SCRIPT] P0. Restructure Deploy tab to be the home for FRESH deployments only — operator picks a service
        + parameters + clicks Deploy; this fires a single Cloud Build / VM launch / Cloud Run revision rollout. Move
        the existing `<DeployForm>` here. Re-deploys (run-it-again-with-same-params) live in Monitor, NOT Deploy —
        the row's re-deploy action carries forward run-time state (correlation_id, chunk-shape, run_id for
        experiments) that a fresh-deploy doesn't have. This separation prevents the foot-gun where an operator
        re-deploys from Deploy with default params and accidentally clobbers an in-flight run.

  - id: b4-data-status-scope-reduction-pricing-data-only
    content: |
      - [ ] [SCRIPT] P0. Restructure Data Status tab to scope to data + pricing correctness only — instruments,
        MTDS, MDPS, features-*. Strategy / execution / ML signals + metrics are NOT in Data-Status; they live in
        Monitor → Experiments (for ephemeral) or Monitor → Live (for live-cluster freshness). Why: Data-Status is
        about "did the catalog / tick / feature data land on disk correctly?" — a manifest-driven correctness
        question. Strategy / execution / ML are about "is the research run completing + producing valid output?" —
        a runtime-state question. Conflating the two confused operators. The existing widget tree
        (`HierarchicalShardDrilldown`, `LiveFreshnessPanel`, parquet schema-view) stays in Data-Status; service
        filter dropdown defaults to data-pipeline services only.

  - id: b5-data-status-mode-toggle-batch-scheduled-live
    content: |
      - [ ] [SCRIPT] P0. Add a 3-way mode toggle (Batch / Scheduled-Today / Live) at the top of `DataStatusTab.tsx`.
        Each mode reads from a different bucket-set / time-slice: Batch = the historical buckets the tab already
        reads; Scheduled-Today = today's-date slice (what should have run today + has it run); Live = live-write
        buckets per asset_group (per `instruments_live_master_2026_05_08.plan.md` Phase 1 — same path as batch in
        most cases, but the UI surfaces "freshness" as the metric instead of "coverage"). Toggle invalidates the
        `/api/data-status` query key and refetches. NO new bucket convention — reuses the same paths the rest of
        the workspace already writes to (per `batch-live-symmetry.md` SSOT).

  - id: b6-live-freshness-widget
    content: |
      - [ ] [SCRIPT] P1. NEW `LiveFreshnessPanel` component rendered when DataStatus mode-toggle = Live. Per
        (asset_group, data_type, shard) shows: last-write-timestamp, expected-cadence (from Phase D scheduler
        registry), staleness-indicator (green = fresh, amber = within tolerance, red = beyond tolerance + auto-
        emits `INSTRUMENTS_LIVE_UPSTREAM_STALE` per `instruments_live_master_2026_05_08.plan.md` Phase A.5 if not
        already emitted). Reads from the SAME `/api/data-status` endpoint; the freshness math is a UI computation
        over the existing `available_at` per-row column.

  - id: b7-mode-prefetch-context
    content: |
      - [ ] [SCRIPT] P0. New React context `LifecyclePrefetchContext` (TanStack Query is already used per existing
        deployment-ui patterns; just add prefetch keys for each Monitor sub-tab on cold-start + on cloud-target
        change). On UI mount + on cloud-toggle, fire four parallel queries: `/api/monitor/backfill`,
        `/api/monitor/experiments`, `/api/monitor/live`, `/api/monitor/scheduled`. Cache TTL 60s default. Operator
        clicks between Monitor sub-tabs without paying network latency. Cloud-toggle (GCP→AWS) invalidates ALL
        caches and refetches with a loading spinner — explicit "loading" UX is acceptable + expected
        (per user direction 2026-05-08).

  - id: b8-streaming-logs-component
    content: |
      - [ ] [SCRIPT] P0. NEW `StreamingLogsPanel` component — single component powers logs across all four
        lifecycle classes. Inputs: `{lifecycle_class, target_ref, correlation_id|run_id|cluster_name}`. Streams
        from deployment-api `/api/logs/stream/{target_ref}` (NEW; thin wrapper over existing GCS event-stream + Cloud
        Logging tail). Server-side fans out to the right log source per lifecycle class (Cloud Run logs for
        long-lived; VM serial console + GCS event-stream for backfills + experiments + scheduled VMs; Cloud
        Function logs for scheduler-as-cloud-function). Filter / search / pause / download. Operator hits the same
        component shape from Monitor → Backfill / Experiments / Live / Scheduled rows. Per CLAUDE.md UI testing
        rule must use `pool: forks`.

  # ──────────────────────────────────────────────────────────────────────
  # Phase C — deployment-api endpoints for Monitor sub-tabs + streaming
  # ──────────────────────────────────────────────────────────────────────

  - id: c1-monitor-backfill-endpoint
    content: |
      - [ ] [SCRIPT] P0. Add `GET /api/monitor/backfill?cloud=<gcp|aws>` route — lists every running + recent
        EPHEMERAL_BATCH job per cloud-target. Joins VM-name lookup (Phase A.2 lifecycle_class filter) with the
        events bucket (last STARTED / progress / STOPPED / FAILED per correlation_id). Per-entry response:
        `{name, lifecycle_class, asset_group, owning_plan, started_at, progress: {dates_done, dates_total,
        shards_captured, shards_empty, shards_failed}, last_event_at, status, recent_events: [...]}`. Reuses
        existing `vm_deployments.py` join patterns. NEW route module
        `deployment-api/deployment_api/routes/monitor_backfill.py`.

  - id: c2-monitor-experiments-endpoint
    content: |
      - [ ] [SCRIPT] P0. Add `GET /api/monitor/experiments?cloud=<gcp|aws>` route — lists every running + recent
        EPHEMERAL_EXPERIMENT job. Joins experiment-registry (Phase BB.1) with run-state from the experiment-
        tracking bucket (per-run_id metrics + artifacts). Per-entry response: `{run_id, name, owner,
        experiment_kind: ml_training|strategy_backtest|execution_backtest, started_at, current_step,
        progress: {fraction, eta}, hyperparams: {...}, metrics_tail: [{step, key, value}, ...],
        result_blob_uri, status}`. NEW route module
        `deployment-api/deployment_api/routes/monitor_experiments.py`.

  - id: c3-monitor-live-endpoint
    content: |
      - [ ] [SCRIPT] P0. Add `GET /api/monitor/live?cloud=<gcp|aws>` route — lists every LONG_LIVED_LIVE deployment
        cluster from the Phase E.1 registry, joined with runtime state (Cloud Run service status, GKE deployment
        health). Per-entry response: `{name, lifecycle_class, cloud_target, deployment_kind, asset_group,
        archetype_owners, replicas, health, last_heartbeat_at, freshness_per_data_type: {...},
        recent_events: [...]}`. Lifecycle action endpoints:
        `POST /api/monitor/live/{name}/{start|stop|pause|restart|drain}`. SSE event-tail
        `/api/monitor/live/{name}/events` reuses existing `deploy_events_sse.py:76` machinery. NEW route module.

  - id: c4-monitor-scheduled-endpoint
    content: |
      - [ ] [SCRIPT] P0. Add `GET /api/monitor/scheduled?cloud=<gcp|aws>` route — lists every scheduler from the
        Phase D registry joined with current Cloud Scheduler / EventBridge / VM-cron live state. Per-entry response
        as before (alive/dead/stale/paused/missing). Lifecycle action endpoints:
        `POST /api/monitor/scheduled/{name}/{run-now|pause|resume}`,
        `POST /api/monitor/scheduled/deploy-missing` (the registry-driven deploy-missing button).

  - id: c5-streaming-logs-endpoint
    content: |
      - [ ] [SCRIPT] P0. Add `GET /api/logs/stream/{target_ref}` route — SSE / WebSocket stream that fans out per
        lifecycle class. Backfill + experiment + scheduled VM logs come from the events bucket + GCS Cloud Logging
        tail; long-lived live logs come from Cloud Run / GKE per-pod logs. Client filter / search / pause are
        client-side over the stream (server sends raw lines).

  - id: c6-aggregated-status-endpoints-removed-folded-into-monitor
    content: |
      - [ ] [SCRIPT] P1. Per the restructure, the originally-planned aggregated `/api/{batch,scheduled,live}/status`
        endpoints (previous draft Phase C.3) are FOLDED into the four Monitor sub-tab endpoints (C.1-C.4). Phase
        B.7 prefetch fires the four queries directly. NO duplicate aggregation route; the Monitor sub-tab queries
        ARE the prefetch surface.

  # ──────────────────────────────────────────────────────────────────────
  # Phase D — Scheduler registry SSOT (env-scoped)
  # ──────────────────────────────────────────────────────────────────────

  - id: d1-scheduler-registry-uac-ssot-env-scoped
    content: |
      - [ ] [SCRIPT] P0. NEW UAC SSOT
        `unified_api_contracts/canonical/crosscutting/scheduler_registry.py`. Declares every scheduler that should
        exist per `(cloud_target, environment_tier)` cell as a typed list of `SchedulerSpec(name,
        lifecycle_class=SCHEDULED_RECURRING, schedule_cron, target_kind, target_ref, asset_group, owning_plan,
        expected_max_runtime, max_consecutive_failures_before_page, env_tiers: list[EnvironmentTier])`. The
        `env_tiers` field declares which environments the scheduler is expected to exist in; staging and prod
        usually share, but dev typically only runs a subset (no live-instruments triggers in dev, e.g.). Phase 1
        entries: every instruments-live trigger from `instruments_live_master_2026_05_08` Phase A.3 +
        manifest-consolidator-60s + data-status rollup + manifest-aggregation cron + T+1 audit. Adding a new
        scheduler in any plan = adding a row here; "deploy-missing schedulers" reads from this registry filtered
        by `(cloud_target, environment_tier)`. NO ad-hoc `gcloud scheduler jobs create` outside this registry.

  - id: d2-scheduler-deploy-missing-implementation
    content: |
      - [ ] [SCRIPT] P0. Implement `POST /api/monitor/scheduled/deploy-missing` — for each registry entry whose
        runtime-state ≠ deployed AND env_tiers includes the current tier, emit the cloud-target-specific create
        command (gcloud scheduler jobs create OR AWS EventBridge `put-rule` + `put-targets`) and run it.
        Idempotent. Returns per-entry success/fail. Same pattern as existing batch deploy-missing in
        `deploy_missing.py:62`.

  - id: d3-scheduler-pause-resume-implementation
    content: |
      - [ ] [SCRIPT] P0. Implement pause + resume per cloud-target — gcloud scheduler jobs pause/resume / EventBridge
        `disable-rule`/`enable-rule`. State persists across the toggle. UI shows the paused-state from the
        scheduled list. Auto-pause on Phase H circuit-breaker trip per
        `instruments_live_master_2026_05_08.plan.md` Phase H.2 — operator manual-resume only.

  # ──────────────────────────────────────────────────────────────────────
  # Phase E — Live-cluster registry SSOT (env-scoped)
  # ──────────────────────────────────────────────────────────────────────

  - id: e1-live-cluster-registry-uac-ssot-env-scoped
    content: |
      - [ ] [SCRIPT] P0. NEW UAC SSOT
        `unified_api_contracts/canonical/crosscutting/live_cluster_registry.py`. Declares every long-lived
        deployment per `(cloud_target, environment_tier)` cell: typed list of `LiveClusterSpec(name,
        lifecycle_class=LONG_LIVED_LIVE, cloud_target, environment_tier, deployment_kind:
        cloud_run|gke|eks|ecs_service, target_ref, asset_group, archetype_owners, health_endpoint,
        expected_replicas, drain_timeout)`. Phase 1 entries: 6 perp venues × 1 live-MTDS each (live + staging
        for May-23), 1 live-strategy per archetype (carry_staked_basis + leveraged_funding_arb), 1 live-execution
        per cloud, 1 position-balance, 1 risk, 1 alerting. Same SSOT discipline as scheduler registry.

  - id: e2-live-cluster-deploy-and-lifecycle-actions
    content: |
      - [ ] [SCRIPT] P0. Implement start / stop / pause / restart / drain per cloud-target. Cloud Run: revision
        scale-to-0 for stop, set min-instances=N for start, traffic-split for drain. GKE/EKS: deployment scale +
        rolling-restart. Idempotent. State persists. Reuses existing `vm_deployments.py` patterns where
        applicable.

  # ──────────────────────────────────────────────────────────────────────
  # Phase BB — Experiment tracker (greenfield slice)
  # ──────────────────────────────────────────────────────────────────────

  - id: bb1-experiment-registry-uac-ssot
    content: |
      - [ ] [SCRIPT] P0. NEW UAC SSOT
        `unified_api_contracts/canonical/crosscutting/experiment_registry.py`. Declares the experiment kind
        taxonomy (closed set: `ML_TRAINING`, `STRATEGY_BACKTEST`, `EXECUTION_BACKTEST`) + the typed
        `ExperimentRunSpec(run_id, kind, owner, asset_group, started_at, hyperparams: dict, expected_steps,
        result_blob_uri, status: running|completed|failed|cancelled)`. Run_ids are UUIDv7 (sortable by time).
        Persistence: per-run blob at `gs://<pid>-experiments/by_kind={kind}/run_id={run_id}/manifest.json` plus
        per-step append-only metric stream at the same prefix `metrics.jsonl`. NO new database — file-system / GCS
        only, mirroring the rest of the workspace.

  - id: bb2-experiment-emission-utl-helper
    content: |
      - [ ] [SCRIPT] P0. NEW UTL helper
        `unified_trading_library/experiment_tracker.py` — `start_experiment(kind, owner, hyperparams) -> run_id`,
        `emit_metric(run_id, step, key, value)`, `emit_step(run_id, step_name, progress)`,
        `complete_experiment(run_id, result_blob_uri)`, `fail_experiment(run_id, error)`. Integrates with the
        existing `setup_events()` / `log_event()` machinery so every experiment lifecycle event also flows to the
        events bucket. Strategy backtest harness, ML training entry-points, execution-service backtest harness all
        adopt this helper — single emission surface.

  - id: bb3-experiment-monitor-subtab-wiring
    content: |
      - [ ] [SCRIPT] P0. Wire Monitor → Experiments sub-tab (Phase B.2) to `/api/monitor/experiments` endpoint
        (Phase C.2) reading from the experiment registry + per-run blobs. Per-row: run_id, owner, kind, started_at,
        progress, current_step, key metrics tail (sparkline of last N), status. Click-through to per-run detail
        view with full hyperparams / metric chart / artifact download / log-stream. Stop / restart actions:
        `POST /api/monitor/experiments/{run_id}/{stop|restart}`.

  # ──────────────────────────────────────────────────────────────────────
  # Phase H — Environment-tiered hosting for deployment-UI/API itself
  # Mirrors the trading-system-UI pattern (per CLAUDE.md "Local Development" + firebase-split-topology.md)
  # ──────────────────────────────────────────────────────────────────────

  - id: h1-env-tier-codex-doc
    content: |
      - [ ] [AGENT] P0. NEW codex doc `codex/05-infrastructure/deployment-ui-environment-tiers.md` capturing the
        env-tier topology for deployment-UI/API itself: dev (localhost), staging (Cloud Run on staging GCP project +
        AWS staging mirror, hosted at `staging.<research-domain>/deployment`), prod (Cloud Run on prod GCP project +
        AWS prod mirror, hosted at `<research-domain>/deployment`). Each env has its own deployment-api Cloud Run
        instance, its own GCS event/log bucket scope, its own Cloud Scheduler entries, its own live clusters.
        Operator iteration loop: dev tweaks → ship to staging → soak with staging schedules / staging live clusters
        / staging data-status views → promote to prod. NEVER an in-UI env toggle. Same pattern the trading-system-UI
        already follows.

  - id: h2-deployment-api-env-aware-config
    content: |
      - [ ] [SCRIPT] P0. Update deployment-api to read `CLOUD_DEPLOYMENT_ENV` env var at boot and scope every
        registry read (scheduler / live-cluster / experiment) by the resolved tier. Bucket suffixes per env per the
        existing `bucket-isolation-model.md` SSOT (e.g. `<pid>-events-staging` vs `<pid>-events-prod`). Cloud
        Scheduler list / EventBridge list filtered to the project per env. Auth: deployment-api per env uses its
        own service account scoped to that env's projects. NO cross-env data leakage.

  - id: h3-deployment-ui-env-badge-and-domain-resolution
    content: |
      - [ ] [SCRIPT] P0. Add env badge to deployment-UI Header — read-only, computed from `window.location.hostname`
        per Phase A.5 helper. Visual: green DEV / amber STAGING / red PROD. Clicking the badge shows a tooltip with
        the resolved env + the API base URL + the current cloud-target. NEVER a toggle.

  - id: h4-staging-and-prod-domain-deployment
    content: |
      - [ ] [HUMAN+AGENT] P1. Provision staging + prod Cloud Run instances of deployment-api + Firebase Hosting (or
        equivalent) for deployment-UI under `staging.<research-domain>/deployment` and `<research-domain>/deployment`.
        DNS records, TLS certs, IAM bindings. CI builds promote `live-defi-rollout` → staging → prod via the
        existing semver-agent + workflow promotion machinery. Reference existing trading-system-UI deployment for
        the pattern.

  # ──────────────────────────────────────────────────────────────────────
  # Phase F — UI polish + cloud-toggle UX
  # ──────────────────────────────────────────────────────────────────────

  - id: f1-cloud-toggle-loading-state
    content: |
      - [ ] [SCRIPT] P1. Cloud-toggle (GCP / AWS) in Header MUST show explicit loading UX during the cache
        invalidate + parallel refetch (per Phase B.7). Skeleton-loaders or progress indicator on every tab during
        the load; tab-state preserved across the toggle. Per user direction 2026-05-08.

  - id: f2-mode-toggle-instant-ux
    content: |
      - [ ] [SCRIPT] P1. Cross-Monitor-sub-tab navigation (Backfill ↔ Experiments ↔ Live ↔ Scheduled) MUST feel
        instant — Phase B.7 prefetch keeps all four sub-tabs in cache. Add unit test that asserts no network call
        fires on tab switch when cache is warm. Performance budget: <50ms perceptible delay on sub-tab toggle.

  - id: f3-naming-convention-rule-into-claudemd
    content: |
      - [ ] [HUMAN+AGENT] P1. Update CLAUDE.md "VM Naming Convention" section with the new `lifecycle_class`
        requirement (Phase A.2) + the experiment-VM run_id-suffix rule. Operator review then ship via the standard
        PM commit. Symlinks propagate to all repo-mirrors automatically.

  # ──────────────────────────────────────────────────────────────────────
  # Phase G — Final validation gate
  # ──────────────────────────────────────────────────────────────────────

  - id: g1-workspace-qg-sweep
    content: |
      - [ ] [SCRIPT] P0. `bash scripts/quality-gates.sh` on every repo in `repo_gates`; UI vitest with `pool: forks`
        per workspace rule.

  - id: g2-staging-d3
    content: |
      - [ ] [HUMAN+AGENT] P0. Deploy 6-tab UI + Monitor sub-tabs + new deployment-api endpoints to staging GCP
        project (and AWS staging mirror). Verify: cloud-toggle latency, sub-tab instant-feel,
        deploy-missing-schedulers idempotence, live-cluster lifecycle actions on smoke-cluster, experiment
        tracker round-trips a real ML training run, streaming logs render across all four lifecycle classes,
        env badge renders correctly per domain.

  - id: g3-operator-signoff
    content: |
      - [ ] [HUMAN] P1. Operator sign-off on the 6-tab UX + Monitor sub-tab flow + Data-Status scope reduction +
        env-tier hosting. B6 gate.

isProject: false
---

# Deployment-UI Lifecycle Tabs — Cross-Cutting Activation Plan

## Why this plan exists

The deployment-UI today is service-axis-organised (Deploy / Status / History / Builds / Data-Status / Readiness / Config
— seven peer tabs scoped to a single selected service). That made sense when "deployment" meant "Cloud Run service
deploy" only. It now needs to express FOUR structurally different lifecycle classes and THREE other orthogonal axes.

## Four orthogonal axes

| Axis                  | Members                                                   | UI surface                                   |
| --------------------- | --------------------------------------------------------- | -------------------------------------------- |
| Lifecycle class       | EPHEMERAL_BATCH / EPHEMERAL_EXPERIMENT / SCHEDULED / LIVE | Monitor sub-tabs (4 of them)                 |
| Cloud target          | GCP / AWS                                                 | Header toggle (slow refresh on switch)       |
| Environment tier      | DEV / STAGING / PROD                                      | Header badge (read-only; resolved by domain) |
| Service / asset_group | full workspace registry                                   | Sidebar (existing)                           |

These axes are mutually orthogonal. The same logical thing (e.g. an instruments-service backfill) shows up at the
intersection of `(EPHEMERAL_BATCH, GCP, STAGING, instruments-service)` — four coordinates. The UI's job is to make all
four coordinates visible + togglable without conflating them.

## Final 6-tab structure

```
┌─ Header ───────────────────────────────────────────────────────────────────────────┐
│  [Cloud: GCP|AWS]   [Env: DEV|STAGING|PROD badge]   [Service sidebar selector ▾]   │
└────────────────────────────────────────────────────────────────────────────────────┘

┌─ Tabs ─────────────────────────────────────────────────────────────────────────────┐
│  Deploy  │  Monitor  │  Data Status  │  Builds  │  Readiness  │  Config            │
└────┬─────┴─────┬─────┴───────┬───────┴────┬─────┴─────┬───────┴──────┬─────────────┘
     │           │             │            │           │              │
     │           │             │            │           │              └─ existing
     │           │             │            │           └─ existing
     │           │             │            └─ existing (cloud-toggle aware)
     │           │             └─ scoped to data + pricing only (instruments / MTDS / MDPS / features-*)
     │           │                3-mode toggle: Batch / Scheduled-Today / Live
     │           └─ NEW (renamed from History) — runtime state of all jobs/clusters/schedulers
     │              ┌─ Backfill   (EPHEMERAL_BATCH)
     │              ├─ Experiments (EPHEMERAL_EXPERIMENT — ML / strategy / execution)
     │              ├─ Live        (LONG_LIVED_LIVE — clusters)
     │              └─ Scheduled   (SCHEDULED_RECURRING — Cloud Scheduler / EventBridge / VM cron)
     │              every sub-tab: list + per-row actions (re-deploy, stop, start, pause, drain,
     │                              stream-logs, attach-events) using the SAME row-template component
     └─ Fresh deployments only (re-deploys live in Monitor)
```

## Architectural principles

1. **Auth + credentials always-available, never env-var-mode-flag-driven.** deployment-api boots with both GCP + AWS
   credentials loaded into its session via `UnifiedCloudConfig`. UI cloud-toggle just chooses which client to dispatch
   per request — no re-auth, no restart, no env-var dance.

2. **Cross-mode toggles are INSTANT; cloud toggle CAN be slow.** Switching Monitor sub-tabs (Backfill ↔ Experiments ↔
   Live ↔ Scheduled) must feel like clicking a tab in a desktop app — data is pre-fetched on cold-start + on
   cloud-switch. Switching GCP ↔ AWS pays the network round-trip; explicit loading UX.

3. **Same vocabulary across Monitor sub-tabs.** Each sub-tab uses the SAME row-template (lifecycle-class-aware) so the
   operator sees one consistent layout. Verbs differ — deploy + complete (Backfill / Experiments) vs schedule + pause
   (Scheduled) vs start + drain (Live) — but the row-card shape doesn't.

4. **Data-Status is for data + pricing correctness only.** Strategy / execution / ML signals + metrics are NOT in
   Data-Status — they live in Monitor → Experiments / Live. This separation of concerns is the cleanest cut between "did
   the data land on disk?" (manifest-driven) and "is the runtime job healthy?" (process-state-driven).

5. **Deploy tab is for FRESH deployments only. Re-deploys live in Monitor.** A re-deploy from Monitor carries forward
   run-time state (correlation_id, chunk-shape, run_id) that a fresh-deploy doesn't have; conflating them is the
   foot-gun where an operator clobbers an in-flight run with default params.

6. **Environment tier is resolved by domain, never an in-UI toggle.** `localhost` = DEV, `staging.<domain>` = STAGING,
   `<domain>` = PROD. Each tier has its own deployment-api Cloud Run instance, its own buckets, its own Cloud Scheduler
   entries, its own live clusters. Mirrors the trading-system-UI pattern + workspace `firebase-split-topology.md` SSOT.

7. **Most of the infrastructure already exists** (per agent scout 2026-05-08): SSE event-stream
   (`/stream/deploy-events`), batch deploy-missing (`deploy_missing.py:62`), cloud-target context
   (`CloudProviderContext.tsx`), VM-launcher registry, data-status drilldown, shard-detail download, vitest with
   `pool: forks`. This plan is **mostly re-shape + wire-in**, with one greenfield slice (Phase BB Experiments tracker)
   and one infra slice (Phase H env-tier hosting).

## What's NEW vs reused

| Capability                                           | New?              | Where it lives                                                                     |
| ---------------------------------------------------- | ----------------- | ---------------------------------------------------------------------------------- |
| `LifecycleClass` enum (4 members)                    | NEW               | UAC `crosscutting/lifecycle_class.py` (Phase A.1)                                  |
| `EnvironmentTier` enum + domain-resolver             | NEW               | UAC `crosscutting/environment_tier.py` (Phase A.5)                                 |
| VM-prefix `lifecycle_class` annotation               | NEW (extension)   | `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` (Phase A.2)                          |
| 6-tab shell + Monitor sub-tabs                       | NEW (UI re-shape) | `deployment-ui/src/App.tsx` (Phase B.1-B.2)                                        |
| Mode-prefetch context (4 sub-tabs)                   | NEW               | `deployment-ui/src/contexts/LifecyclePrefetchContext.tsx` (B.7)                    |
| Streaming logs panel                                 | NEW               | `deployment-ui/src/components/StreamingLogsPanel.tsx` (B.8)                        |
| Data-Status mode toggle + scope reduction            | NEW               | `DataStatusTab.tsx` (Phase B.4-B.5)                                                |
| Live freshness widget                                | NEW               | `LiveFreshnessPanel.tsx` (Phase B.6)                                               |
| `/api/monitor/{backfill,experiments,live,scheduled}` | NEW               | `deployment-api/.../routes/monitor_*.py` (Phase C.1-C.4)                           |
| `/api/logs/stream/{target_ref}`                      | NEW               | `deployment-api/.../routes/logs_stream.py` (Phase C.5)                             |
| Scheduler registry SSOT (env-scoped)                 | NEW               | UAC `crosscutting/scheduler_registry.py` (Phase D.1)                               |
| Live-cluster registry SSOT (env-scoped)              | NEW               | UAC `crosscutting/live_cluster_registry.py` (Phase E.1)                            |
| Experiment registry + tracker UTL helper             | NEW               | UAC `crosscutting/experiment_registry.py` + UTL `experiment_tracker.py` (Phase BB) |
| Env-tier hosting for deployment-UI/API               | NEW (infra)       | Phase H                                                                            |
| Cloud-target context + always-available auth         | REUSED            | `CloudProviderContext.tsx` + `UnifiedCloudConfig` (existing)                       |
| SSE event-stream                                     | REUSED            | `deploy_events_sse.py:76` (existing)                                               |
| Batch deploy-missing                                 | REUSED            | `deploy_missing.py:62` `_SERVICE_LAUNCHER_SCRIPTS` (existing)                      |
| Data-status drilldown / shard schema-view            | REUSED            | `DataStatusTab.tsx` + `HierarchicalShardDrilldown` (existing)                      |
| VM-launcher registry                                 | REUSED            | `deployment-service/scripts/vm/` (existing)                                        |
| Build history + log retrieval                        | REUSED            | `builds.py` / `cloud_builds.py` (existing)                                         |

## Sibling plan relationships

- `instruments_live_master_2026_05_08.plan.md` — sibling. Phase G of that plan delegates UI scope here. Cross-link both
  ways.
- `master_to_live_defi_2026_05_23.plan.md` — sibling. The 6 long-lived deployment clusters that DeFi-live needs by
  May-23 are entered into Phase E.1 registry on first commit; staging deploy + drain test are part of master's D3 gate.
- `deployment_api_work_stream_a_2026_05_07.plan.md` — depends_on. Owns programmatic VM launch + event-tail; reused for
  live-clusters' SSE stream.
- `launcher_scripts_consolidation_into_deployment_service_2026_05_07.plan.md` — depends_on. Owns the launcher SSOT
  migration; Phase D.2 deploy-missing-schedulers writes scheduler-deploy commands into the same
  `deployment-service/scripts/scheduler/` root.
- `infrastructure_master_2026_05_07.plan.md` — depends_on. Existing UI iteration cadence.
- `firebase-split-topology.md` (codex SSOT, not a plan) — Phase H env-tier hosting follows the same pattern this doc
  establishes for the trading-system-UI.

## Parallelisation strategy

```
Phase A (foundation, all PARALLEL)
  ├─ A.1 LifecycleClass UAC SSOT (4 members)
  ├─ A.2 VM naming-convention extension
  ├─ A.3 codex deployment-ui-architecture.md (NEW)
  ├─ A.4 codex batch-live-symmetry UX section
  └─ A.5 cloud-target + environment-tier discriminators
            │
            ▼ QG gate
Phase B (UI shell + sub-tabs, all PARALLEL after A; B.6 / B.8 can ship after B.1)
  ├─ B.1 6-tab shell
  ├─ B.2 Monitor 4-sub-tab structure
  ├─ B.3 Deploy = fresh-only
  ├─ B.4 Data-Status scope reduction
  ├─ B.5 Data-Status mode toggle
  ├─ B.6 Live freshness widget
  ├─ B.7 mode-prefetch context (4 sub-tabs)
  └─ B.8 streaming logs panel
            │
            ▼ QG gate
Phase C (API endpoints, PARALLEL)         ║   Phase D (scheduler registry, sequential D.1→D.2→D.3)
  ├─ C.1 monitor backfill                 ║     ├─ D.1 registry SSOT (env-scoped)
  ├─ C.2 monitor experiments              ║     ├─ D.2 deploy-missing impl
  ├─ C.3 monitor live                     ║     └─ D.3 pause/resume impl
  ├─ C.4 monitor scheduled                ║
  └─ C.5 streaming logs                   ║   Phase E (live-cluster registry, sequential E.1→E.2)
                                          ║     ├─ E.1 registry SSOT (env-scoped)
                                          ║     └─ E.2 lifecycle actions impl
                                          ║
                                          ║   Phase BB (experiments — greenfield)
                                          ║     ├─ BB.1 experiment registry SSOT
                                          ║     ├─ BB.2 UTL helper
                                          ║     └─ BB.3 Monitor sub-tab wiring
            │
            ▼ QG gate
Phase H (env-tier hosting infra)          ║   Phase F (UX polish)
  ├─ H.1 codex env-tier doc               ║     ├─ F.1 cloud-toggle loading
  ├─ H.2 api env-aware config             ║     ├─ F.2 mode-toggle instant
  ├─ H.3 ui env badge                     ║     └─ F.3 CLAUDE.md naming-rule update
  └─ H.4 staging + prod domain deploy
            │
            ▼ QG gate
Phase G (workspace QG + D3 staging + B6 operator sign-off)
```

## Out of scope

- Replacing the existing service-axis sidebar — operator still navigates by service within each tab.
- Building NEW long-lived clusters — registry entries Phase E.1 are operator-curated; service code is owned by
  per-service plans.
- Cloud Scheduler config files themselves — those are `instruments_live_master_2026_05_08.plan.md` Phase F.1 scope. THIS
  plan owns the UI surface that lists / deploys / pauses them, NOT the YAML content.
- Building a model registry or full MLflow-equivalent — Phase BB experiment tracker is intentionally file-system + GCS
  only, not a relational store. If MLflow becomes warranted, it's a separate plan.

## Plan-format compliance

Follows `unified-trading-pm/plans/PLAN_FORMAT.md`: 3-tier readiness model declared (C5 / D3 / B6); per-repo gates;
Cursor checkboxes on every todo; phased execution DAG with QG gates; parallelisation explicit; SSOT-first (codex docs in
Phase A.3 + A.4 + H.1 own intent, plan owns activation); pre-audit complete (agent scout 2026-05-08 of deployment-ui +
deployment-api).
