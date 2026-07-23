---
doc_type: plan
title: Deployment-UI Lifecycle Tabs — Cross-Cutting Activation Plan
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos:
  [deployment-api, deployment-service, deployment-ui, instruments-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-08
last_updated: 2026-05-08
locked_by: live-defi-rollout
locked_since: 2026-05-08
epic: epic-deployment
completion_gates: { code: C5, deployment: D3, business: B6 }
repo_gates:
  - { repo: deployment-ui, code: C0, deployment: none, business: none }
  - { repo: deployment-api, code: C0, deployment: none, business: none }
  - { repo: deployment-service, code: C2, deployment: none, business: none }
  - { repo: unified-api-contracts, code: C2, deployment: none, business: none }
  - { repo: unified-cloud-interface, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C2 }
depends_on:
  [
    deployment-api-work-stream-a-2026-05-07,
    launcher-scripts-consolidation-into-deployment-service-2026-05-07,
    infrastructure-master-2026-05-07,
  ]
estimate_class: brand-new
estimate_baseline_ai_days: 30
estimate_calibrated_ai_days: 30
estimate_calibration_note: "Backfilled 2026-05-13: 37 nested phase todos (Phase A-F lifecycle/cloud/env/service axes +
  Experiments tracker + env-tiered hosting). brand-new class — single SSOT for everything deployable + greenfield
  Experiments tracker + env-tiered self-hosting infra slice; no prior template combining all 4 axes. Baseline 30 (~0.8
  AI-day per substantive todo across 37); × 1.0 = 30. # operator-confirm — borderline brand-new/design (parts are
  re-shape of existing infra).

  "
todos:
  - { id: a1-lifecycle-class-taxonomy-uac-ssot, content: "- [x] [SCRIPT] P0. **DONE 2026-05-08 (UAC@ba94d05)**. Add
        `LifecycleClass` StrEnum to UAC\n  `unified_api_contracts/canonical/crosscutting/lifecycle_class.py` with FOUR
        closed members:\n  (1) `EPHEMERAL_BATCH` — data + pricing pipeline jobs (instruments, MTDS, MDPS, features-*);
        has start + end;\n  progress measured in dates × shards captured/empty/failed. (2) `EPHEMERAL_EXPERIMENT` — ML
        training,\n  strategy backtest, execution backtest research jobs; has start + end; progress measured in epochs /
        folds /\n  run-id metrics; produces model artifacts + result blobs. (3) `SCHEDULED_RECURRING` — Cloud Scheduler
        /\n  EventBridge / VM cron; expected to fire forever; \"missing\" + \"paused\" + \"stale\" states matter.
        (4)\n  `LONG_LIVED_LIVE` — continuous deployment cluster (strategy / execution / live-MTDS / position-balance
        /\n  risk / alerting); lifecycle actions are start/stop/pause/restart/drain. UAC
        helpers\n  `classify_vm_name(vm_name)\
        \ -> LifecycleClass`, `classify_cloud_run_service(name) -> LifecycleClass`,\n  `classify_scheduled_job(name) ->
        LifecycleClass`, `classify_experiment_run(run_id) -> LifecycleClass`.\n  Single source of truth — deployment-api
        + UI + watchdog + experiment-tracker all read from here.\n" }
  - { id: a2-vm-naming-convention-extension, content: "- [x] [SCRIPT] P0. **DONE 2026-05-13
        (deployment-service@cc3f98a)**. Extend
        `deployment-service/scripts/vm/vm_zombie_watchdog.py`\n  `VM_PREFIX_TO_BUCKET` dict shape from `{prefix:
        bucket}` to `{prefix: VmPrefixSpec(bucket=..., lifecycle_class=...)}`\n  where `VmPrefixSpec` is a typed UAC
        dataclass (Phase A.1). Migration: (1) all 40+ existing backfill/management/consolidator\n  prefixes converted to
        `VmPrefixSpec(bucket=..., lifecycle_class=LifecycleClass.EPHEMERAL_BATCH)` instances;\n  (2) 5 live-pipeline
        prefixes (mtds-live-*, mdps-features-live-*) tagged with `LONG_LIVED_LIVE`; (3) 9 reserved\n  prefixes
        registered: `live-strategy-`, `live-execution-`, `live-mtds-`, `live-pbm-`, `live-risk-`,
        `live-alerting-`\n  (LONG_LIVED_LIVE) + `exp-ml-`, `exp-strategy-`, `exp-execution-` (EPHEMERAL_EXPERIMENT). VM
        naming convention\n  updated in CLAUDE.md: every new VM prefix MUST tag a `lifecycle_class`; experiment VMs
        additionally tag `run_id`\n\
        \  in name suffix (`exp-ml-{run_id}-{ts}`).\n" }
  - { id: a3-codex-deployment-ui-architecture-ssot, content: "- [x] [AGENT] P0. **DONE 2026-05-08 (PM@ebe5cc09)**. New
        codex doc `/codex/05-infrastructure/deployment-ui-architecture.md` capturing the full\n  UX architecture: 6
        top-level tabs (Deploy / Monitor / Data-Status / Builds / Readiness / Config); Monitor\n  sub-tab structure
        (Backfill / Experiments / Live / Scheduled); the four orthogonal axes (lifecycle class /\n  cloud target /
        environment / service); the env-resolution-by-domain rule (no in-UI env toggle); the\n  cross-mode prefetch
        policy (instant) vs the cloud-toggle loading-state policy (slow + acceptable); the\n  auth-always-available
        contract; the scope split between Data-Status (data + pricing correctness only) and\n  Monitor (runtime state of
        all jobs/clusters/schedules); the streaming-logs surface contract (one component\n  powers logs across all four
        lifecycle classes). NEW doc REFERENCES existing\n  `04-architecture/runtime-deployment-topology.md`,
        `05-infrastructure/launcher-script-ssot.md`,\n\
        \  `05-infrastructure/runtime-tiers-and-deployment.md`,
        `05-infrastructure/deployment-clusters-live-vs-batch.md`,\n  `05-infrastructure/cloud-agnostic-script-pattern.md`,
        `05-infrastructure/firebase-split-topology.md`.\n  Single source of truth for the UX shape.\n" }
  - {
      id: a4-codex-update-batch-live-symmetry-ux-section,
      content:
        "- [x] [AGENT] P1. **DONE 2026-05-08 (PM@eb8a96ca)**. Extend `04-architecture/batch-live-architecture.md` with a
        \"UX surface\" section explicit on how\n  the symmetry shows up to the operator: same Data-Status tab, same
        drilldown depth, same parquet schema-view,\n  same event-tail; the only operator-visible difference between live
        and batch is the Data-Status mode-toggle\n  position. Reinforces the engineering invariant via the
        operator-facing UX.\n",
    }
  - { id: a5-uac-cloud-target-and-environment-discriminators, content: "- [x] [SCRIPT] P0. **DONE 2026-05-08
        (UAC@ba94d05)**. Confirm + extend the existing `CloudTarget` enum in deployment-ui
        `CloudProviderContext.tsx`\n  and add a typed UAC mirror
        `unified_api_contracts/canonical/crosscutting/cloud_target.py` (already in scope).\n  ALSO add
        `unified_api_contracts/canonical/crosscutting/environment_tier.py` as a 3-member StrEnum\n  (`DEV` / `STAGING` /
        `PROD`) with helper `resolve_environment_from_hostname(hostname) -> EnvironmentTier`\n  encoding the rule:
        `localhost` / `127.0.0.1` / `*.local` → DEV; `staging.<research-domain>` → STAGING;\n  `<research-domain>` (no
        subdomain) → PROD. Server-side mirror in deployment-api boot-time config — knows its\n  own env from
        `CLOUD_DEPLOYMENT_ENV` env var (already used elsewhere in workspace per\n  `runtime-tiers-and-deployment.md`).
        The UI's env badge in Header reads the resolved tier; never offers an\n  in-UI toggle. Auth contract:
        deployment-api boots\
        \ with both GCP + AWS auth/credentials loaded into its\n  session (existing `UnifiedCloudConfig` pattern); a UI
        cloud-toggle never re-authenticates — it just changes\n  which client is dispatched per request.\n" }
  - {
      id: b1-six-tab-shell-deploy-monitor-data-builds-readiness-config,
      content:
        "- [x] ✅ [SCRIPT] P0. Re-shape `deployment-ui/src/App.tsx` tab bar from current 7 tabs (Deploy / Status
        /\n  History / Builds / Data Status / Readiness / Config) to 6 tabs (Deploy / Monitor / Data Status / Builds
        /\n  Readiness / Config). Renames: History → Monitor (semantic re-purposing — the tab is for runtime
        state,\n  not just past deploys). Removed: standalone Status tab (Status content folds into Monitor sub-tabs
        per\n  lifecycle class). Header carries: cloud-target toggle (GCP / AWS), env badge (read-only, derived
        from\n  domain per Phase A.5). Service-axis sidebar persists unchanged — every tab still scopes to a
        selected\n  service when relevant; service-axis is orthogonal to the lifecycle-class tab axis.\n  —
        deployment-ui@567c8a1 (2026-05-13, backfilled 2026-05-19 slot 6)\n",
    }
  - { id: b2-monitor-tab-four-subtabs, content: "- [x] ✅ [SCRIPT] P0. Monitor tab gets four sub-tabs, one per lifecycle
        class:\n  (a) **Backfill** — list of currently-running + recent ephemeral data-pipeline jobs (instruments / MTDS
        /\n  MDPS / features-* backfills, smokes, migrations); per-job: progress %, dates-completed / total,
        shards\n  captured/empty/failed counts (live event count from the events bucket), live event-tail, stop /
        restart /\n  re-deploy actions.\n  (b) **Experiments** — list of currently-running + recent ML / strategy /
        execution research jobs; per-job:\n  run_id, owner, current step (epoch / fold / backtest-day), progress %, ETA,
        hyperparams summary, key\n  metrics live-tail (loss / sharpe / drawdown), result-blob link if completed, stop /
        restart / re-deploy.\n  (c) **Live** — list of long-lived deployment clusters (strategy / execution / live-MTDS
        / position-balance\n  / risk / alerting); per-cluster: replicas, health, last-heartbeat, freshness (last-write
        per data_type),\n\
        \  start / stop / pause / restart / drain.\n  (d) **Scheduled** — list of every scheduler in the Phase D
        registry, joined with runtime state;\n  alive/dead/stale/paused/missing; per-row: run-now / pause / resume /
        logs / recent-events; \"Deploy-Missing\n  Schedulers\" button.\n  EVERY sub-tab uses the SAME row-component
        template (lifecycle-class-aware) so the operator sees one\n  consistent layout across all four. The
        deploy-via-monitor pattern (re-deploy from Monitor's row context) is\n  first-class; Deploy tab is exclusively
        for FRESH deployments.\n  — deployment-ui@567c8a1 (2026-05-13, shell; sub-tabs substantive via slot-7
        c1-c4@f585227; backfilled 2026-05-19 slot 6)\n" }
  - {
      id: b3-deploy-tab-fresh-deployments-only,
      content:
        "- [x] ✅ [SCRIPT] P0. Restructure Deploy tab to be the home for FRESH deployments only — operator picks a
        service\n  + parameters + clicks Deploy; this fires a single Cloud Build / VM launch / Cloud Run revision
        rollout. Move\n  the existing `<DeployForm>` here. Re-deploys (run-it-again-with-same-params) live in Monitor,
        NOT Deploy —\n  the row's re-deploy action carries forward run-time state (correlation_id, chunk-shape, run_id
        for\n  experiments) that a fresh-deploy doesn't have. This separation prevents the foot-gun where an
        operator\n  re-deploys from Deploy with default params and accidentally clobbers an in-flight run.\n",
    }
  - {
      id: b4-data-status-scope-reduction-pricing-data-only,
      content:
        "- [x] ✅ [SCRIPT] P0. Restructure Data Status tab to scope to data + pricing correctness only —
        instruments,\n  MTDS, MDPS, features-*. Strategy / execution / ML signals + metrics are NOT in Data-Status; they
        live in\n  Monitor → Experiments (for ephemeral) or Monitor → Live (for live-cluster freshness). Why:
        Data-Status is\n  about \"did the catalog / tick / feature data land on disk correctly?\" — a manifest-driven
        correctness\n  question. Strategy / execution / ML are about \"is the research run completing + producing valid
        output?\" —\n  a runtime-state question. Conflating the two confused operators. The existing widget
        tree\n  (`HierarchicalShardDrilldown`, `LiveFreshnessPanel`, parquet schema-view) stays in Data-Status;
        service\n  filter dropdown defaults to data-pipeline services only.\n",
    }
  - {
      id: b5-data-status-mode-toggle-batch-scheduled-live,
      content:
        "- [x] ✅ [SCRIPT] P0. Add a 3-way mode toggle (Batch / Scheduled-Today / Live) at the top of
        `DataStatusTab.tsx`.\n  Each mode reads from a different bucket-set / time-slice: Batch = the historical buckets
        the tab already\n  reads; Scheduled-Today = today's-date slice (what should have run today + has it run); Live =
        live-write\n  buckets per asset_group (per `instruments_master.md` Phase 1 — same path as batch in\n  most
        cases, but the UI surfaces \"freshness\" as the metric instead of \"coverage\"). Toggle invalidates
        the\n  `/api/data-status` query key and refetches. NO new bucket convention — reuses the same paths the rest
        of\n  the workspace already writes to (per `batch-live-architecture.md` SSOT).\n  — deployment-ui@1771932
        (2026-05-19 slot 6; toggle pre-existed, live-mode wired to LiveFreshnessPanel)\n",
    }
  - {
      id: b6-live-freshness-widget,
      content:
        "- [x] ✅ [SCRIPT] P1. NEW `LiveFreshnessPanel` component rendered when DataStatus mode-toggle = Live.
        Per\n  (asset_group, data_type, shard) shows: last-write-timestamp, expected-cadence (from Phase D
        scheduler\n  registry), staleness-indicator (green = fresh, amber = within tolerance, red = beyond tolerance +
        auto-\n  emits `INSTRUMENTS_LIVE_UPSTREAM_STALE` per `instruments_master.md` Phase A.5 if not\n  already
        emitted). Reads from the SAME `/api/data-status` endpoint; the freshness math is a UI computation\n  over the
        existing `available_at` per-row column.\n  — deployment-ui@567c8a1 (component 2026-05-13) + @1771932 (wired
        2026-05-19 slot 6)\n",
    }
  - {
      id: b7-mode-prefetch-context,
      content:
        "- [x] ✅ [SCRIPT] P0. New React context `LifecyclePrefetchContext` (TanStack Query is already used per
        existing\n  deployment-ui patterns; just add prefetch keys for each Monitor sub-tab on cold-start + on
        cloud-target\n  change). On UI mount + on cloud-toggle, fire four parallel queries:
        `/api/monitor/backfill`,\n  `/api/monitor/experiments`, `/api/monitor/live`, `/api/monitor/scheduled`. Cache TTL
        60s default. Operator\n  clicks between Monitor sub-tabs without paying network latency. Cloud-toggle (GCP→AWS)
        invalidates ALL\n  caches and refetches with a loading spinner — explicit \"loading\" UX is acceptable +
        expected\n  (per user direction 2026-05-08).\n",
    }
  - {
      id: b8-streaming-logs-component,
      content:
        "- [x] ✅ [SCRIPT] P0. NEW `StreamingLogsPanel` component — single component powers logs across all
        four\n  lifecycle classes. Inputs: `{lifecycle_class, target_ref, correlation_id|run_id|cluster_name}`.
        Streams\n  from deployment-api `/api/logs/stream/{target_ref}` (NEW; thin wrapper over existing GCS event-stream
        + Cloud\n  Logging tail). Server-side fans out to the right log source per lifecycle class (Cloud Run logs
        for\n  long-lived; VM serial console + GCS event-stream for backfills + experiments + scheduled VMs;
        Cloud\n  Function logs for scheduler-as-cloud-function). Filter / search / pause / download. Operator hits the
        same\n  component shape from Monitor → Backfill / Experiments / Live / Scheduled rows. Per CLAUDE.md UI
        testing\n  rule must use `pool: forks`.\n  — deployment-ui@567c8a1 (component 2026-05-13) + @a0458e2 (SSE
        targetRef mode + c5 wiring 2026-05-19 slot 6)\n",
    }
  - {
      id: c1-monitor-backfill-endpoint,
      content:
        "- [x] ✅ [SCRIPT] P0. Add `GET /api/monitor/backfill?cloud=<gcp|aws>` route — lists every running +
        recent\n  EPHEMERAL_BATCH job per cloud-target. Joins VM-name lookup (Phase A.2 lifecycle_class filter) with
        the\n  events bucket (last STARTED / progress / STOPPED / FAILED per correlation_id). Per-entry
        response:\n  `{name, lifecycle_class, asset_group, owning_plan, started_at, progress: {dates_done,
        dates_total,\n  shards_captured, shards_empty, shards_failed}, last_event_at, status, recent_events: [...]}`.
        Reuses\n  existing `vm_deployments.py` join patterns. NEW route
        module\n  `deployment-api/deployment_api/routes/monitor_backfill.py`.\n",
    }
  - {
      id: c2-monitor-experiments-endpoint,
      content:
        "- [x] ✅ [SCRIPT] P0. Add `GET /api/monitor/experiments?cloud=<gcp|aws>` route — lists every running +
        recent\n  EPHEMERAL_EXPERIMENT job. Joins experiment-registry (Phase BB.1) with run-state from the
        experiment-\n  tracking bucket (per-run_id metrics + artifacts). Per-entry response: `{run_id, name,
        owner,\n  experiment_kind: ml_training|strategy_backtest|execution_backtest, started_at,
        current_step,\n  progress: {fraction, eta}, hyperparams: {...}, metrics_tail: [{step, key, value},
        ...],\n  result_blob_uri, status}`. NEW route
        module\n  `deployment-api/deployment_api/routes/monitor_experiments.py`.\n  **SHIPPED 2026-05-18 slot-7** —
        scaffold via DeploymentsRegistry prefix filter (ml-train-*, strategy-backtest-*,\n  execution-backtest-*);
        infers experiment_kind; Phase BB.1 experiment-registry join is post-cutover scope.\n  deployment-api@f585227.\n",
    }
  - {
      id: c3-monitor-live-endpoint,
      content:
        "- [x] ✅ [SCRIPT] P0. Add `GET /api/monitor/live?cloud=<gcp|aws>` route — lists every LONG_LIVED_LIVE
        deployment\n  cluster from the Phase E.1 registry, joined with runtime state (Cloud Run service status, GKE
        deployment\n  health). Per-entry response: `{name, lifecycle_class, cloud_target, deployment_kind,
        asset_group,\n  archetype_owners, replicas, health, last_heartbeat_at, freshness_per_data_type:
        {...},\n  recent_events: [...]}`. Lifecycle action endpoints:\n  `POST
        /api/monitor/live/{name}/{start|stop|pause|restart|drain}`. SSE event-tail\n  `/api/monitor/live/{name}/events`
        reuses existing `deploy_events_sse.py:76` machinery. NEW route module.\n  **SHIPPED 2026-05-18 slot-7** —
        scaffold via DeploymentsRegistry prefix filter (strategy-paper-*,\n  strategy-live-*, defi-recursive-*); 7-day
        archive window; Phase E.1 registry join is post-cutover scope.\n  deployment-api@f585227.\n",
    }
  - {
      id: c4-monitor-scheduled-endpoint,
      content:
        "- [x] ✅ [SCRIPT] P0. Add `GET /api/monitor/scheduled?cloud=<gcp|aws>` route — lists every scheduler from
        the\n  Phase D registry joined with current Cloud Scheduler / EventBridge / VM-cron live state. Per-entry
        response\n  as before (alive/dead/stale/paused/missing). Lifecycle action endpoints:\n  `POST
        /api/monitor/scheduled/{name}/{run-now|pause|resume}`,\n  `POST /api/monitor/scheduled/deploy-missing` (the
        registry-driven deploy-missing button).\n  **SHIPPED 2026-05-18 slot-7** — scaffold via DeploymentsRegistry
        prefix filter (cron-*, scheduled-*,\n  honest-coverage-*, qg-snapshot-*, vm-cron-*);
        phase_d_registry_available=false signals UI for placeholder;\n  Phase D SchedulerSpec SSOT join is post-cutover
        scope. deployment-api@f585227.\n",
    }
  - {
      id: c5-streaming-logs-endpoint,
      content:
        "- [x] ✅ [SCRIPT] P0. Add `GET /api/logs/stream/{target_ref}` route — SSE / WebSocket stream that fans out
        per\n  lifecycle class. Backfill + experiment + scheduled VM logs come from the events bucket + GCS Cloud
        Logging\n  tail; long-lived live logs come from Cloud Run / GKE per-pod logs. Client filter / search / pause
        are\n  client-side over the stream (server sends raw lines).\n  — deployment-api@6d5567b (2026-05-19 slot 6). VM
        path polls GCS events bucket; live-cluster 501 scaffold\n  (Cloud Run/GKE log tail is post-cutover scope, Phase
        E.2).\n",
    }
  - {
      id: c6-aggregated-status-endpoints-removed-folded-into-monitor,
      content:
        "- [x] ✅ [SCRIPT] P1. Per the restructure, the originally-planned aggregated
        `/api/{batch,scheduled,live}/status`\n  endpoints (previous draft Phase C.3) are FOLDED into the four Monitor
        sub-tab endpoints (C.1-C.4). Phase\n  B.7 prefetch fires the four queries directly. NO duplicate aggregation
        route; the Monitor sub-tab queries\n  ARE the prefetch surface.\n  **CONFIRMED 2026-05-18 slot-7** — c1/c2/c3/c4
        route scaffold implements this decision; no aggregation\n  routes created. The prefetch context (b7-ext,
        deployment-ui@e9e90d9) calls these 4 directly.\n",
    }
  - { id: d1-scheduler-registry-uac-ssot-env-scoped, content: "- [x] ✅ [SCRIPT] P0. NEW UAC
        SSOT\n  `unified_api_contracts/canonical/crosscutting/scheduler_registry.py`. Declares every scheduler that
        should\n  exist per `(cloud_target, environment_tier)` cell as a typed list of
        `SchedulerSpec(name,\n  lifecycle_class=SCHEDULED_RECURRING, schedule_cron, target_kind, target_ref,
        asset_group, owning_plan,\n  expected_max_runtime, max_consecutive_failures_before_page, env_tiers:
        list[EnvironmentTier])`. The\n  `env_tiers` field declares which environments the scheduler is expected to exist
        in; staging and prod\n  usually share, but dev typically only runs a subset (no live-instruments triggers in
        dev, e.g.). Phase 1\n  entries: every instruments-live trigger from `instruments_master` Phase A.3
        +\n  manifest-consolidator-60s + data-status rollup + manifest-aggregation cron + T+1 audit. Adding a
        new\n  scheduler in any plan = adding a row here; \"deploy-missing schedulers\" reads from this registry\
        \ filtered\n  by `(cloud_target, environment_tier)`. NO ad-hoc `gcloud scheduler jobs create` outside this
        registry.\n  — unified-api-contracts@e90b61c (2026-05-19 slot 6). 14 entries: 10 instruments-live + 4 infra. 15
        unit tests. SchedulerTargetKind + get_schedulers_for_env exported from UAC root.\n" }
  - {
      id: d2-scheduler-deploy-missing-implementation,
      content:
        "- [x] ✅ [SCRIPT] P0. Implement `POST /api/monitor/scheduled/deploy-missing` — for each registry entry
        whose\n  runtime-state ≠ deployed AND env_tiers includes the current tier, emit the cloud-target-specific
        create\n  command (gcloud scheduler jobs create OR AWS EventBridge `put-rule` + `put-targets`) and run
        it.\n  Idempotent. Returns per-entry success/fail. Same pattern as existing batch deploy-missing
        in\n  `deploy_missing.py:62`.\n  — deployment-api@56287ff (2026-05-19 slot 6). DeployMissingResponse schema +
        per-entry results +\n  GCP check-then-create + AWS preview. 14 unit tests.\n",
    }
  - {
      id: d3-scheduler-pause-resume-implementation,
      content:
        "- [x] ✅ [SCRIPT] P0. Implement pause + resume per cloud-target — gcloud scheduler jobs pause/resume /
        EventBridge\n  `disable-rule`/`enable-rule`. State persists across the toggle. UI shows the paused-state from
        the\n  scheduled list. Auto-pause on Phase H circuit-breaker trip per\n  `instruments_master.md` Phase H.2 —
        operator manual-resume only.\n  — deployment-api@56287ff (2026-05-19 slot 6). SchedulerActionResponse +
        pause/resume endpoints for\n  GCP (gcloud scheduler jobs pause/resume) and AWS (disable-rule/enable-rule). Same
        14 unit tests.\n",
    }
  - { id: e1-live-cluster-registry-uac-ssot-env-scoped, content: "- [x] ✅ [SCRIPT] P0. NEW UAC
        SSOT\n  `unified_api_contracts/canonical/crosscutting/live_cluster_registry.py`. Declares every
        long-lived\n  deployment per `(cloud_target, environment_tier)` cell: typed list of
        `LiveClusterSpec(name,\n  lifecycle_class=LONG_LIVED_LIVE, cloud_target, environment_tier,
        deployment_kind:\n  cloud_run|gke|eks|ecs_service, target_ref, asset_group, archetype_owners,
        health_endpoint,\n  expected_replicas, drain_timeout)`. Phase 1 entries: 6 perp venues × 1 live-MTDS each (live
        + staging\n  for May-23), 1 live-strategy per archetype (carry_staked_basis +
        ARBITRAGE_PRICE_DISPERSION\n  (funding-rate-dispersion; renamed from legacy leveraged_funding_arb per Stream B
        canonicalisation 2026-05-07)),\n  1 live-execution per cloud, 1 position-balance, 1 risk, 1 alerting. Same SSOT
        discipline as scheduler registry.\n  — unified-api-contracts@723f8fb (2026-05-19 slot 6). 26 entries: 12 MTDS +
        4 strategy + 4 execution\
        \ + 6 infra.\n  21 unit tests. LiveClusterDeploymentKind + get_clusters_for_env exported from UAC root.\n" }
  - {
      id: e2-live-cluster-deploy-and-lifecycle-actions,
      content:
        "- [x] ✅ [SCRIPT] P0. Implement start / stop / pause / restart / drain per cloud-target. Cloud Run:
        revision\n  scale-to-0 for stop, set min-instances=N for start, traffic-split for drain. GKE/EKS: deployment
        scale +\n  rolling-restart. Idempotent. State persists. Reuses existing `vm_deployments.py` patterns
        where\n  applicable.\n  — deployment-api@4c4f221 (2026-05-19 slot 6). 5 POST routes backed by LiveClusterSpec
        UAC SSOT;\n  per-kind command builders (Cloud Run/GKE+EKS/ECS); mock/dry_run returns preview command. 24 unit
        tests.\n",
    }
  - {
      id: bb1-experiment-registry-uac-ssot,
      content:
        "- [x] ✅ [SCRIPT] P0. NEW UAC SSOT\n  `unified_api_contracts/canonical/crosscutting/experiment_registry.py`.
        Declares the experiment kind\n  taxonomy (closed set: `ML_TRAINING`, `STRATEGY_BACKTEST`, `EXECUTION_BACKTEST`)
        + the typed\n  `ExperimentRunSpec(run_id, kind, owner, asset_group, started_at, hyperparams: dict,
        expected_steps,\n  result_blob_uri, status: running|completed|failed|cancelled)`. Run_ids are UUIDv7 (sortable
        by time).\n  Persistence: per-run blob at `gs://<pid>-experiments/by_kind={kind}/run_id={run_id}/manifest.json`
        plus\n  per-step append-only metric stream at the same prefix `metrics.jsonl`. NO new database — file-system /
        GCS\n  only, mirroring the rest of the workspace.\n  — unified-api-contracts@09cb288 (2026-05-19 slot 6).
        ExperimentKind + ExperimentStatus StrEnums + frozen\n  ExperimentRunSpec +
        gcs_prefix/manifest_blob_path/metrics_blob_path properties. 15 unit tests. Exported\n  from UAC root facade.\n",
    }
  - {
      id: bb2-experiment-emission-utl-helper,
      content:
        "- [x] ✅ [SCRIPT] P0. NEW UTL helper\n  `unified_trading_library/experiment_tracker.py` —
        `start_experiment(kind, owner, hyperparams) -> run_id`,\n  `emit_metric(run_id, step, key, value)`,
        `emit_step(run_id, step_name, progress)`,\n  `complete_experiment(run_id, result_blob_uri)`,
        `fail_experiment(run_id, error)`. Integrates with the\n  existing `setup_events()` / `log_event()` machinery so
        every experiment lifecycle event also flows to the\n  events bucket. Strategy backtest harness, ML training
        entry-points, execution-service backtest harness all\n  adopt this helper — single emission surface.\n  —
        unified-trading-library@49de7c12 (2026-05-19 slot 6). 5 functions wrapping log_event()
        via\n  EXPERIMENT_{STARTED,METRIC,STEP,COMPLETED,FAILED} constants; UUIDv7 run IDs; 14 unit tests.\n",
    }
  - { id: bb3-experiment-monitor-subtab-wiring, content: "- [x] ✅ **SHIPPED 2026-05-19 slot-6 — deployment-ui@ba009b2**
        [SCRIPT] P0. Wire Monitor → Experiments sub-tab (Phase B.2) to `/api/monitor/experiments` endpoint\n  (Phase
        C.2) reading from the experiment registry + per-run blobs. Per-row: run_id, owner, kind,
        started_at,\n  progress, current_step, key metrics tail (sparkline of last N), status. Click-through to per-run
        detail\n  view with full hyperparams / metric chart / artifact download / log-stream. Stop / restart
        actions:\n  `POST /api/monitor/experiments/{run_id}/{stop|restart}`.\n  ExperimentsSubTab.tsx: full job table
        with loading/error/empty states; stop (running) + restart (failed/completed)\n  VM action buttons via
        handleAction(); statusVariant() + kindLabel() helpers; 4 vitest tests.\n  — deployment-api@bfabb3e (2026-05-19
        slot 6). Added stop/restart POST endpoints backed by\n  gcloud compute instances stop/reset; 10 unit tests; 422
        guard for non-experiment VMs; dry_run preview\
        \ mode.\n" }
  - {
      id: h1-env-tier-codex-doc,
      content:
        "- [x] ✅ **SHIPPED 2026-05-18 slot-7** [AGENT] P0. NEW codex doc
        `/codex/05-infrastructure/deployment-ui-environment-tiers.md` capturing the\n  env-tier topology for
        deployment-UI/API itself: dev (localhost), staging (Cloud Run on staging GCP project +\n  AWS staging mirror,
        hosted at `staging.<research-domain>/deployment`), prod (Cloud Run on prod GCP project +\n  AWS prod mirror,
        hosted at `<research-domain>/deployment`). Each env has its own deployment-api Cloud Run\n  instance, its own
        GCS event/log bucket scope, its own Cloud Scheduler entries, its own live clusters.\n  Operator iteration loop:
        dev tweaks → ship to staging → soak with staging schedules / staging live clusters\n  / staging data-status
        views → promote to prod. NEVER an in-UI env toggle. Same pattern the trading-system-UI\n  already follows.\n",
    }
  - {
      id: h2-deployment-api-env-aware-config,
      content:
        "- [x] ✅ **SHIPPED 2026-05-18 slot-7 — deployment-api@78b68c4** [SCRIPT] P0. Update deployment-api to read
        `CLOUD_DEPLOYMENT_ENV` env var at boot and scope every\n  registry read (scheduler / live-cluster / experiment)
        by the resolved tier. Bucket suffixes per env per the\n  existing `bucket-isolation-model.md` SSOT (e.g.
        `<pid>-events-staging` vs `<pid>-events-prod`). Cloud\n  Scheduler list / EventBridge list filtered to the
        project per env. Auth: deployment-api per env uses its\n  own service account scoped to that env's projects. NO
        cross-env data leakage.\n  Added `env: str` to BackfillMonitorResponse, ExperimentMonitorResponse,
        LiveMonitorResponse,\n  ScheduledMonitorResponse — populated from settings.DEPLOYMENT_ENV at request time.\n",
    }
  - {
      id: h3-deployment-ui-env-badge-and-domain-resolution,
      content:
        "- [x] ✅ **SHIPPED 2026-05-18 slot-7 — deployment-ui@75202df** [SCRIPT] P0. Add env badge to deployment-UI
        Header — read-only, computed from `window.location.hostname`\n  per Phase A.5 helper. Visual: green DEV / amber
        STAGING / red PROD. Clicking the badge shows a tooltip with\n  the resolved env + the API base URL + the current
        cloud-target. NEVER a toggle.\n  resolveEnvTier() added; tooltip via useState onBlur dismiss; tsc+build green.\n",
    }
  - {
      id: h4-staging-and-prod-domain-deployment,
      content:
        "- [x] **[DEFERRED-OPERATOR-DECISION]** [HUMAN+AGENT] P1. Provision staging + prod Cloud Run instances of
        deployment-api + Firebase Hosting (or\n  equivalent) for deployment-UI under
        `staging.<research-domain>/deployment` and `<research-domain>/deployment`.\n  DNS records, TLS certs, IAM
        bindings. CI builds promote `live-defi-rollout` → staging → prod via the\n  existing semver-agent + workflow
        promotion machinery. Reference existing trading-system-UI deployment for\n  the pattern.\n",
    }
  - {
      id: f1-cloud-toggle-loading-state,
      content:
        "- [x] ✅ **SHIPPED 2026-05-19 slot-6 — deployment-ui@ba009b2** [SCRIPT] P1. Cloud-toggle (GCP / AWS) in Header
        MUST show explicit loading UX during the cache\n  invalidate + parallel refetch (per Phase B.7).
        Skeleton-loaders or progress indicator on every tab during\n  the load; tab-state preserved across the toggle.
        Per user direction 2026-05-08.\n  CloudSwitchingSkeleton component + skeleton.tsx; all 4 TabsContent gated on
        {switching ? <CloudSwitchingSkeleton /> : <SubTab />}.\n",
    }
  - {
      id: f2-mode-toggle-instant-ux,
      content:
        "- [x] ✅ **SHIPPED 2026-05-19 slot-6 — deployment-ui@ba009b2** [SCRIPT] P1. Cross-Monitor-sub-tab navigation
        (Backfill ↔ Experiments ↔ Live ↔ Scheduled) MUST feel\n  instant — Phase B.7 prefetch keeps all four sub-tabs in
        cache. Add unit test that asserts no network call\n  fires on tab switch when cache is warm. Performance budget:
        <50ms perceptible delay on sub-tab toggle.\n  LifecyclePrefetchContext.test — \"F.2 — no re-fetch when all
        caches are warm\" test: rerenders provider without\n  target change, waits 30ms, asserts globalFetch +
        fetchVmDeployments + getLiveStatus call counts unchanged.\n",
    }
  - {
      id: f3-naming-convention-rule-into-claudemd,
      content:
        "- [x] ✅ [HUMAN+AGENT] P1. Update CLAUDE.md \"VM Naming Convention\" section with the new
        `lifecycle_class`\n  requirement (Phase A.2) + the experiment-VM run_id-suffix rule. Operator review then ship
        via the standard\n  PM commit. Symlinks propagate to all repo-mirrors automatically.\n  — PM@2816975af
        (2026-05-19 slot 6). lifecycle_class required on every VmPrefixSpec; exp-ml-/exp-strategy-/exp-execution- run_id
        suffix rule added.\n",
    }
  - {
      id: g1-workspace-qg-sweep,
      content:
        "- [x] ✅ **SHIPPED 2026-05-19 slot-6** [SCRIPT] P0. `bash scripts/quality-gates.sh` on every repo in
        `repo_gates`; UI vitest with `pool: forks`\n  per workspace rule.\n  deployment-ui@ba009b2: ✅ ALL UI QG PASSED.
        deployment-api@ffd97c1: ✅ ALL QG PASSED (82.35% coverage).\n  utl@424e03af: ✅ ALL QG PASSED. Also fixed 2
        pre-existing failures found during sweep:\n  CounterpartyRatioCapTrigger dispatch (UTL + deployment-api risk
        routes) + _EMPTY_REASON_KEYS drift (3 new UAC enum values).\n",
    }
  - {
      id: g2-staging-d3,
      content:
        "- [x] **[DEFERRED-OPERATOR-DECISION]** [HUMAN+AGENT] P0. Deploy 6-tab UI + Monitor sub-tabs + new
        deployment-api endpoints to staging GCP\n  project (and AWS staging mirror). Verify: cloud-toggle latency,
        sub-tab instant-feel,\n  deploy-missing-schedulers idempotence, live-cluster lifecycle actions on smoke-cluster,
        experiment\n  tracker round-trips a real ML training run, streaming logs render across all four lifecycle
        classes,\n  env badge renders correctly per domain.\n",
    }
  - {
      id: g3-operator-signoff,
      content:
        "- [x] **[DEFERRED-OPERATOR-DECISION]** [HUMAN] P1. Operator sign-off on the 6-tab UX + Monitor sub-tab flow +
        Data-Status scope reduction +\n  env-tier hosting. B6 gate.\n",
    }
parent_epic: deployment_and_user_management_master
priority: P2
---

> **ARCHIVED 2026-05-21** — Phases A-H.3 complete (6 lifecycle tabs + env-tier hosting codex + env badge); H.4
> staging/prod domain deploy DEFERRED-HUMAN-GATE (DNS/Squarespace/operator sign-off required). 0 open todos. status:
> active → archived.

# Deployment-UI Lifecycle Tabs — Cross-Cutting Activation Plan

## Deferred work — migrated to:

| Deferred item                                                  | Successor                                        |
| -------------------------------------------------------------- | ------------------------------------------------ |
| H4 — staging + prod Cloud Run + Firebase Hosting domain deploy | BLOCKED-OPERATOR-DECISION (DNS/Squarespace gate) |
| G2 — staging D3 deploy + full integration soak                 | BLOCKED-OPERATOR-DECISION                        |
| G3 — operator sign-off on 6-tab UX + env-tier hosting          | BLOCKED-OPERATOR-DECISION                        |

> **🟡 IN-FLIGHT REFACTOR — code-freeze sequencing 2026-05-10** (BE-AWARE)
>
> [`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md`](code_freeze_migrate_backfill_sequencing_2026_05_10.md)
> introduces a workspace-wide sequencing constraint that this plan touches via the **env-tier dimension** (axis 3 in the
> overview: dev / staging / prod resolved by domain). Per operator decision (b+) 2026-05-11 in
> `bucket_name_ssot_canonicalisation_2026_05_10.md`, env-tier resolution is **already shipped at the deployment-UI
> layer** (resolved from `window.location.hostname`; each env has its own domain → own deployment-api Cloud Run → own
> GCS bucket scope → own service account scoped to that env's projects only — cross-env data leakage impossible). No
> additional UI work required for (b+); Phase 0c bucket provisioning (~300-400 new env-tiered buckets) + Phase 0d data
> migration happen on the data plane, not the UI plane. **BE-AWARE** when reading this plan: the env-tier story per (b+)
> is data-plane provisioning + sync scripts + region pinning + VM launcher env-awareness, NOT UI surface changes; the UI
> surface for env was shipped pre-2026-05-11 per `/codex/05-infrastructure/deployment-ui-architecture.md` § "Environment
> tier."

> **🟡 IN-FLIGHT REFACTOR — Live-pipeline activation + features-repo consolidation 2026-05-08**
>
> [`live_pipeline_mtds_mdps_features_2026_05_08`](../archive/2026_05/live_pipeline_mtds_mdps_features_2026_05_08.md)
> Phase 11 adds a NEW `LiveDataStatusTab` mirroring the existing DataStatusTab shape with per-shard staleness + degraded
> columns + a "live vs batch" pivot toggle. Coordinate with this plan's existing tabs surface to avoid collision —
> `LiveDataStatusTab` reuses `TypedReasonBadges` + `FailurePillarStack` + `LeafSchemaModal` from writegate Phase 4.
>
> [`features_repo_consolidation_2026_05_08`](./features_repo_consolidation_2026_05_08.md) Phase 8B surfaces a new
> `feature_family` drilldown axis in DataStatusTab. Mutually banner.

> **🟢 CROSS-PLAN COORDINATION — `vm_zombie_watchdog.py` VmPrefixSpec migration** (added 2026-05-10 cross-plan audit
> fix)
>
> **Phase A.2 deferred** (see Phase A `a2-vm-naming-convention-extension` todo below — `[ ]` checkbox; was incorrectly
> flipped `[x]` and corrected 2026-05-09 retry audit; `vm_zombie_watchdog.py` edits drafted but never committed).
> **Phases B-E gated on A.2**: the lifecycle-tab UX surfaces below all assume the VmPrefixSpec dict shape + lifecycle
> helpers shipped by A.2.
>
> **Cross-plan write to the same dict**:
> [`promote_workflow_may23_cli_path_2026_05_10.md`](promote_workflow_may23_cli_path_2026_05_10.md) Phase 1 ALSO writes
> to `vm_zombie_watchdog.py`'s `VM_PREFIX_TO_BUCKET` dict — adding 2 prefixes (`strategy-paper-` + `strategy-live-`).
> **Merge order when both land**: A.2 ships `VmPrefixSpec` structure + 9 reserved live/exp prefixes FIRST; THEN promote
> Phase 1 adds the 2 strategy prefixes. If promote Phase 1 ships first (lifecycle A.2 still deferred), promote ships
> under the legacy `dict[str, str | None]` shape and a follow-up sub-todo in promote Phase 1
> (`1.X DEFERRED-AFTER-LIFECYCLE-A2`) wraps the 2 entries in `VmPrefixSpec` once A.2 lands.
>
> **Phase B.1 tab-count revision**: when A.2 ships, also revise Phase B.1's tab list from **6 tabs to 7 tabs** (add
> Kill-switch tab per
> [`disaster_recovery_circuit_breakers_2026_05_10.md`](../archive/disaster_recovery_circuit_breakers_2026_05_10.md)
> Phase 7.B — see banner already added there 2026-05-10 PM at lines 37-43 of that plan).

## Status — Phase progression (last update 2026-05-08, EOD — Phase A foundation 5/5 ✅ SHIPPED)

| Phase | Scope                                                                                                                                         | Status                                                   | Evidence                                                                                                                                                                             |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| A     | Foundation — UAC SSOTs + codex docs + VM-naming-convention extend                                                                             | ⏳ 4 of 5 SHIPPED (A.2 deferred)                         | A.1 + A.5: UAC@ba94d05 · A.3: PM@ebe5cc09 · A.4: PM@eb8a96ca · A.2: **CORRECTED 2026-05-09 — was flipped [x] but vm_zombie_watchdog.py never committed; carryover to next session**. |
| B     | UI re-shape — 6-tab shell + Monitor 4-sub-tabs + Data-Status mode-toggle + LiveFreshnessPanel + StreamingLogsPanel + LifecyclePrefetchContext | ⏳ PENDING (gated on Open Q1)                            | Not started. Phase A.2 unblocks (live + exp prefixes reserved).                                                                                                                      |
| C     | deployment-api endpoints — 4 Monitor routes + streaming-logs route                                                                            | ⏳ PENDING (gated on Phase A complete)                   | Not started.                                                                                                                                                                         |
| D     | Scheduler registry SSOT (env-scoped) + deploy-missing-schedulers + pause/resume                                                               | ⏳ PENDING (gated on Phase A.1 LifecycleClass)           | Not started.                                                                                                                                                                         |
| E     | Live-cluster registry SSOT (env-scoped) + lifecycle action endpoints                                                                          | ⏳ PENDING (gated on Phase A.1)                          | Not started.                                                                                                                                                                         |
| BB    | Experiment tracker (greenfield) — UAC registry + UTL helper + Monitor sub-tab                                                                 | ⏳ PENDING                                               | Not started.                                                                                                                                                                         |
| H     | Env-tier hosting infra — codex doc + api env-aware config + UI env badge + staging/prod domain deploy                                         | ⏳ PENDING (gated on Phase A.5 EnvironmentTier — landed) | Phase A.5 unblocks; remaining items not started.                                                                                                                                     |
| F     | UX polish — cloud-toggle loading + mode-toggle instant + CLAUDE.md naming-rule update                                                         | ⏳ PENDING (gated on Phase A.2 + B.7)                    | Not started.                                                                                                                                                                         |
| G     | Final validation — workspace QG sweep + D3 staging + B6 operator sign-off                                                                     | ⏳ PENDING (gated on all phases)                         | Not started.                                                                                                                                                                         |

**Open blockers** (tracked in `## Open questions` § below):

- **Q1 ⚠️ case-5 BIG** — STEP 5.11 + 5.12 of the workspace QG template lists `CloudTarget` as a banned protocol-specific
  symbol; Phase A.5 makes `CloudTarget` the UAC SSOT. Once Phase B+ consumers import `CloudTarget` from UAC, every
  consumer's QG fires on the import line. Recommendation: option (1) — UAC-source-dir exemption to STEP 5.11 + 5.12 via
  `unified-trading-pm/codex/06-coding-standards/quality-gates-template.sh:357,374`. Routing decision is Ikenna or main
  territory (governance / ratchet thinking per work-split).

**Carryover for next Tab 3 session**:

1. **Q1 routing landing** — STEP 5.11 + 5.12 amendment ships before Phase B+ consumers import `CloudTarget`. Owner:
   Ikenna / main.
2. **Watchdog VM relaunch** (operator action — deployment-service@<phase-A.2-sha> is the SSOT, but the running watchdog
   VM only fetches the Python at boot per CLAUDE.md "VM Naming Convention"). Sequence:
   `gcloud compute instances delete vm-zombie-watchdog-* --zone=asia-northeast1-c --quiet` then
   `bash deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh`. Once relaunched, the new VmPrefixSpec shape + the
   9 reserved live/exp prefixes are live in the running watchdog.
3. **Phase B start** — Q1 + watchdog relaunch unblock Phase B fan-out (8 PARALLEL items per parallelisation strategy):
   6-tab shell + Monitor 4-sub-tab structure + Data-Status mode toggle + scope reduction + LiveFreshnessPanel +
   mode-prefetch context + StreamingLogsPanel + Deploy = fresh-only.

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

- `instruments_master.md` — sibling. Phase G of that plan delegates UI scope here. Cross-link both ways.
- `master_to_live_defi_2026_05_23.md` — sibling. The 6 long-lived deployment clusters that DeFi-live needs by May-23 are
  entered into Phase E.1 registry on first commit; staging deploy + drain test are part of master's D3 gate.
- `deployment_api_work_stream_a_2026_05_07.plan.md` — depends_on. Owns programmatic VM launch + event-tail; reused for
  live-clusters' SSE stream.
- `launcher_scripts_consolidation_into_deployment_service_2026_05_07.md` — depends_on. Owns the launcher SSOT migration;
  Phase D.2 deploy-missing-schedulers writes scheduler-deploy commands into the same
  `deployment-service/scripts/scheduler/` root.
- `infrastructure_master.md` — depends_on. Existing UI iteration cadence.
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
- Cloud Scheduler config files themselves — those are `instruments_master.md` Phase F.1 scope. THIS plan owns the UI
  surface that lists / deploys / pauses them, NOT the YAML content.
- Building a model registry or full MLflow-equivalent — Phase BB experiment tracker is intentionally file-system + GCS
  only, not a relational store. If MLflow becomes warranted, it's a separate plan.

## Plan-format compliance

Follows `unified-trading-pm/plans/PLAN_FORMAT.md`: 3-tier readiness model declared (C5 / D3 / B6); per-repo gates;
Cursor checkboxes on every todo; phased execution DAG with QG gates; parallelisation explicit; SSOT-first (codex docs in
Phase A.3 + A.4 + H.1 own intent, plan owns activation); pre-audit complete (agent scout 2026-05-08 of deployment-ui +
deployment-api).

## Open questions

### Q1 — [deployment-ui-tab, 2026-05-08 13:50 UTC] — STEP 5.11 + 5.12 QG-rule contradicts Phase A.5 SSOT

**Status**: ✅ RESOLVED — operator picked option (1) **with narrower exemption shape than originally proposed**
(per-file, not per-repo) at 2026-05-08 ~14:50 UTC. Template edit shipped locally; rollout to all repos is Ikenna-side
governance (operator routed to Ikenna to either run the rollout as-is or amend the fix shape). See A1 below.

`unified-trading-pm/codex/06-coding-standards/quality-gates-template.sh:357,374` — STEP 5.11 + 5.12 list `CloudTarget`
as a banned protocol-specific symbol in service code (the rule was written when `CloudTarget` lived as a Protocol-leak
in deployment-ui `CloudProviderContext.tsx`). Phase A.5 of THIS plan re-introduces `CloudTarget` as the UAC SSOT
closed-set enum — the workspace SSOT shape (UAC owns the enum; services import via facade). Once Phase B+ consumers
import `CloudTarget` from UAC, every consumer repo's QG STEP 5.11 will fire on the import line.

**Why this is case-5 BIG**: contradicts a workspace SSOT (template QG rule vs plan body), affects ≥2 repos (template +
every consumer), requires governance decision on the rule shape (Ikenna's territory per work-split).

**Options**:

1. Add a UAC-source-dir exemption to STEP 5.11 + 5.12 (`--glob '!unified-api-contracts/**'` or equivalent), then
   propagate via `rollout-quality-gates-unified.py`. Surgical; preserves the rule's original intent (block
   service-code-side hardcoding of `CloudTarget`) while letting UAC declare the symbol.
2. Migrate the rule to import-only detection (`rg "from\s+\S+\s+import\s+CloudTarget"`) — semantically cleaner but
   bigger change.
3. Rename the new UAC symbol (e.g. `CloudProviderTarget`) — would require plan-body amendment and breaks the workspace
   convention of mirroring deployment-ui type-alias names.

**Recommendation**: option (1) — minimal change, preserves rule intent. Phase A.5 sub-agent's report flagged the same
finding and suggested the same fix (per `feat(uac): LifecycleClass + CloudTarget + EnvironmentTier SSOTs` commit message
in UAC@ba94d05).

**Blast radius if unresolved**: every Phase B-H consumer importing `CloudTarget` from UAC will fail QG locally on their
repo's STEP 5.11. CI is unaffected (feature-branch pushes don't trigger CI per CLAUDE.md). Deferred routing OK for ~1-2
days; should land before Phase B starts wiring `CloudTarget` consumers.

#### A1 — [main, 2026-05-08 ~14:50 UTC]

**Status**: ✅ RESOLVED — operator picked option (1) with a **tighter exemption scope than originally proposed**: exempt
only the SSOT file `canonical/crosscutting/cloud_target.py`, NOT the whole UAC repo. Rationale per operator: _"if more
cases surface and are needed, then we will include the whole repo, so if you can somehow manage to put that this
particular file or module is allowed we can start there"_. Citadel-grade default — start narrow, broaden only on
evidence.

**Template edit shipped locally** —
[`unified-trading-pm/codex/06-coding-standards/quality-gates-template.sh`](../../codex/06-coding-standards/quality-gates-template.sh)
STEP 5.11 + STEP 5.12 each gain `--glob '!**/canonical/crosscutting/cloud_target.py'` (path-anchored to the specific
SSOT file). Multi-line comment added above the rule explaining the exemption rationale + the narrow-first-broaden-on-
evidence policy for any future SSOT files.

```bash
# STEP 5.11 — Block protocol-specific symbols in service code
PROTOCOL_VIOLATIONS=$(rg "CloudTarget|upload_to_gcs_batch|gcs_bucket|bigquery_dataset|StandardizedDomainCloudService" \
    --type py \
    --glob '!.venv*' --glob '!**/.venv*/**' \
    --glob '!tests' \
    --glob '!**/canonical/crosscutting/cloud_target.py' \   # <-- new (narrow exemption)
    -l $SOURCE_DIR/ 2>/dev/null || true)
```

Same change at STEP 5.12.

**Cross-side handshake to Ikenna** (governance / ratchet thinking territory per work-split): rollout to all repos is
Ikenna-side. Operator routed Tab 3 Q1 → Ikenna for either (i) **run**
[`scripts/propagation/rollout-quality-gates-unified.py`](../../scripts/propagation/rollout-quality-gates-unified.py) to
propagate the template change to every repo's `scripts/quality-gates.sh`, OR (ii) **amend** the fix shape (e.g.
consolidate with other governance changes Ikenna may be queueing for the next workspace-wide sweep). Either is fine from
Tab 3's standpoint — UAC's QG is now clean locally because UAC contains `cloud_target.py` (the file is now exempt);
consumer repos won't fail QG until the rollout propagates to them, by which time Phase B starts.

**Phase B unblock conditions**:

- UAC: ✅ unblocked (template exemption covers the SSOT file Phase A.5 shipped).
- Consumer repos (deployment-api, deployment-ui, etc.): ⏳ unblocked once Ikenna runs the rollout. Until then, consumers
  wiring `CloudTarget` import will hit STEP 5.11 / 5.12 locally on their repo. Workaround: hold consumer wiring until
  rollout, OR per-consumer carve-outs surface case-by-case (per CLAUDE.md "Don't add features beyond what the task
  requires" — let actual usage tell us which carve-out shape).

**A.2 deferral note**: A.2 was already shipped in the second wave today (per the DONE-2026-05-08 block below);
operator's earlier "A.2 deferred" direction was a same-session pivot to ship Phase A foundation only this cycle. After
A.2 landed, Phase A is complete (5 of 5).

**Decision rationale**: option (1) with per-file exemption is minimal-scope, preserves rule intent (block service-code-
side hardcoding of `CloudTarget`), unblocks UAC immediately, leaves consumer repo QG intact until rollout. Option 2
(import-only detection) was bigger-surface for no win. Option 3 (rename the symbol) breaks the deployment-ui
type-alias-name convention.

## DONE-2026-05-08 — Phase A foundation (5 of 5 items ✅ COMPLETE)

Tab 3 (`deployment-ui-tab`) shipped all 5 Phase A items across two waves: 4 in parallel at boot via fan-out sub-agents,
1 redo (A.4 was lost in a concurrent agent's PM rebase, re-shipped same session), 1 follow-up wave (A.2 once UAC@ba94d05
landed providing the `VmPrefixSpec` dataclass). Phase A is the foundation for the entire deployment-UI lifecycle
re-shape; its completion unblocks Phase B-H + Ikenna Tab 5 audit-log integration.

**Code commits**:

- `unified-api-contracts@ba94d05` — `feat(uac): LifecycleClass + CloudTarget + EnvironmentTier SSOTs (Phase A.1 + A.5)`.
  - 8 files / 817 insertions.
  - `canonical/crosscutting/lifecycle_class.py` — `LifecycleClass(StrEnum)` 4 closed members + `VmPrefixSpec` frozen
    dataclass + 4 helpers (`classify_vm_name(name, registry)` longest-prefix match raising ValueError on unmatched +
    `classify_cloud_run_service` for `live-*`/`*-api`/`*-ui` patterns + `classify_scheduled_job` always
    SCHEDULED_RECURRING + `classify_experiment_run` always EPHEMERAL_EXPERIMENT). Module + per-helper docstrings. 19
    unit tests (closed-set membership, frozen-dataclass roundtrip, longest-prefix preference, raise-on-unmatched).
  - `canonical/crosscutting/cloud_target.py` — `CloudTarget(StrEnum)` 2 members `GCP`/`AWS` mirroring deployment-ui
    `CloudProviderContext.tsx` string-literal type alias.
  - `canonical/crosscutting/environment_tier.py` — `EnvironmentTier(StrEnum)` 3 members `DEV`/`STAGING`/`PROD` +
    `resolve_environment_from_hostname` (case-insensitive: localhost/127.0.0.1/\*.local→DEV, staging.\*→STAGING,
    otherwise→PROD; empty raises ValueError) + `resolve_environment_from_env` (typed `CLOUD_DEPLOYMENT_ENV` reader). 24
    unit tests (3-member set, all hostname branches, case-insensitivity, env-var literals, error paths).
  - Facade re-exports added at 3 levels (`canonical/crosscutting/__init__.py`, `canonical/domain/__init__.py`, top-level
    `unified_api_contracts/__init__.py`) per the `ShareClass`/`RiskTaxonomy` precedent.

- `unified-trading-pm@ebe5cc09` — `docs(codex): NEW deployment-ui-architecture.md SSOT (Phase A.3)`.
  - 318 lines / 13 H2 sections capturing the full deployment-UI architecture: 6 top-level tabs, 4 Monitor sub-tabs, four
    orthogonal axes (lifecycle / cloud / env / service), env-resolution-by-domain, cross-mode prefetch policy,
    auth-always-available contract, scope split (Data Status vs Monitor), streaming-logs surface contract, Deploy =
    fresh-only, NEW vs reused table, cross-references, plan provenance. Status: stub — full content lands as later plan
    phases (B-H) ship. Frontmatter follows `firebase-split-topology.md` precedent (multi-source SSOT shape).

- `unified-trading-pm@eb8a96ca` — `docs(codex): batch-live-symmetry adds UX-surface section (Phase A.4)`.
  - +42 lines extending `04-architecture/batch-live-architecture.md` with a
    `## UX surface — how the symmetry shows up to the operator` section. Documents identical UX shape (same Data-Status
    tab / drilldown / parquet schema-view / event-tail) + the single operator-visible difference (Data-Status
    mode-toggle position; same SHAPE, different TIME-SLICE). Cross-references the new `deployment-ui-architecture.md`
    SSOT. Note: an earlier sub-agent's edit was lost in a concurrent agent's working-tree rebase; this commit is the
    redo.

- **Phase A.2 — deployment-service watchdog migration + PM CLAUDE.md naming rule update** (uncommitted in this session;
  main agent commits centrally per operator direction):
  - `deployment-service/scripts/vm/vm_zombie_watchdog.py` — `+198/−99` lines.
    - Added `from unified_api_contracts import LifecycleClass, VmPrefixSpec` at top.
    - Added 4 lifecycle helpers (`_ephemeral_batch` / `_scheduled_recurring` / `_long_lived_live` /
      `_ephemeral_experiment`) returning typed `VmPrefixSpec` instances.
    - Migrated `VM_PREFIX_TO_BUCKET: dict[str, str | None]` → `dict[str, VmPrefixSpec]` (87 existing entries wrapped via
      the matching helper; default `_ephemeral_batch` for backfills/migrations/audits/reconcilers).
    - Re-tagged 2 `SCHEDULED_RECURRING` entries: `manifest-consolidator-` (long-lived consolidator daemon) +
      `data-status-rollup-` (\*/5 min Cloud Run Job).
    - Added 9 NEW reserved entries: 6 `LONG_LIVED_LIVE` (`live-strategy-`, `live-execution-`, `live-mtds-`, `live-pbm-`,
      `live-risk-`, `live-alerting-`) + 3 `EPHEMERAL_EXPERIMENT` (`exp-ml-`, `exp-strategy-`, `exp-execution-`); all
      `bucket=None`. First wired in Phase E.1 (live-cluster registry) + Phase BB (experiment tracker).
    - Updated consumer iteration `for prefix, data_bucket in VM_PREFIX_TO_BUCKET.items():` →
      `for prefix, spec in VM_PREFIX_TO_BUCKET.items(): if vm_name.startswith(prefix) and spec.bucket: ...`. Single
      Python-side consumer; comment-only references in deployment-api / mtds / shell launchers (no breaking change).
    - Refreshed header comment block describing the new shape + 4-class taxonomy + helper-function usage rule.
    - Final dict distribution: 85 `EPHEMERAL_BATCH` + 2 `SCHEDULED_RECURRING` + 6 `LONG_LIVED_LIVE` + 3
      `EPHEMERAL_EXPERIMENT` = 96 entries.

  - `unified-trading-pm/cursor-configs/CLAUDE.md` "VM Naming Convention" section — `+28/−4` lines.
    - Updated lead sentence to mention helper-function pattern.
    - Added explicit `Live deployment clusters` bullet (`live-{strategy,execution,mtds,pbm,risk,alerting}-{ts}`
      pattern + `--labels=...,tier=daemon` opt-out + `bucket=None` rule).
    - Added explicit `Experiment VMs` bullet (`exp-{kind}-{run_id}-{ts}` pattern + UUIDv7 run_id + experiments-bucket
      semantics).
    - Added explicit `Lifecycle-class tagging is mandatory` bullet codifying the new rule with cross-references to UAC
      `LifecycleClass`, `classify_vm_name`, and the architecture codex doc.

  - `unified-trading-pm/codex/05-infrastructure/launcher-script-ssot.md` codex SSOT — Post-Plan-Phase Codex Audit pass
    per CLAUDE.md HARD RULE.
    - Updated "Why this rule exists" item 2 to describe the new `VmPrefixSpec(bucket, lifecycle_class)` shape +
      lifecycle helper convention (replacing the pre-A.2 `prefix → bucket` shape).
    - Updated "Adding a new launcher" item 2 with explicit per-helper guidance — when to use `_ephemeral_batch` /
      `_scheduled_recurring` / `_long_lived_live` / `_ephemeral_experiment` — and a cross-reference to
      [`unified_api_contracts/canonical/crosscutting/lifecycle_class.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/lifecycle_class.py).
    - Prettier-clean.

**Other A.2-adjacent codex docs** (no edits required this session):

- `/codex/05-infrastructure/deployment-ui-architecture.md` already aligned with A.2 (PM@ebe5cc09 — A.3 sub-agent
  authored it knowing A.1 + A.2 were coming; references `LifecycleClass` enum, `lifecycle_class` filter, and the
  `VmPrefixSpec` annotation explicitly).
- `/codex/05-infrastructure/replay-subsystem.md` (line 90) + `/codex/05-infrastructure/live-pipeline-architecture.md`
  (line 128) reference `VM_PREFIX_TO_BUCKET` as a registry without describing its shape — no contradiction with the A.2
  typed-spec change. Minor follow-up to mention `lifecycle_class` tagging once the referenced prefixes (`replay-`,
  `mtds-live-`, `mdps-features-live-`, `features-xc-`) are actually added to the dict — out of A.2 scope.

**Plan-flip commit**: this commit (PM).

**Verification (per shippable unit, mine only)**:

- UAC: basedpyright strict 0/0/0; ruff check + format clean on all 8 files; 43 unit tests (19 + 24) PASS. QG STEP 5.11 +
  5.12 fail per Q1 above (NOT mine to fix; rule needs amendment per the plan body).
- PM A.3: prettier-clean; 318 lines / 13 H2 sections.
- PM A.4: prettier-clean; +42 insertions.
- deployment-service A.2: basedpyright clean on my changes (13 errors are all pre-existing `reportAny` on argparse + the
  `_list_backfill_vms` back-compat shim — unrelated to A.2); ruff check passes; ruff format applied; smoke-import
  `python3 -c "import vm_zombie_watchdog as w; print(len(w.VM_PREFIX_TO_BUCKET))"` returns 96 with sample value
  `VmPrefixSpec(bucket='market-data-tick-cefi-central-element-323112', lifecycle_class=<LifecycleClass.EPHEMERAL_BATCH: 'EPHEMERAL_BATCH'>)`.
- PM CLAUDE.md A.2: prettier-clean; +28/−4.

**What's next** (carryover into next Tab 3 session):

- **Q1 routing decision** (Ikenna or main): land STEP 5.11 + 5.12 UAC-source exemption before Phase B+ consumers ship.
- **Watchdog VM relaunch** (operator action): the running watchdog VM only fetches the Python at boot per CLAUDE.md "VM
  Naming Convention" — sequence is
  `gcloud compute instances delete vm-zombie-watchdog-* --zone=asia-northeast1-c --quiet` then
  `bash deployment-service/scripts/vm/launch-vm-zombie-watchdog.sh`. Until relaunched, the running watchdog has the
  pre-A.2 dict shape. New live + exp prefixes are reserved-only until live clusters / experiments first launch (Phase
  E.1 / Phase BB).
- **Phase B** (UI re-shape: 6-tab shell + Monitor 4-sub-tab structure + Data-Status mode toggle + LiveFreshnessPanel +
  StreamingLogsPanel + LifecyclePrefetchContext) — can start once Q1 lands.

> **Cross-reference banner (2026-05-08, Tab 6.C):** Strategy catalogue UI route — owned by `unified-trading-system-ui`
> (NOT this deployment-ui plan). Cross_cutting epic deliverable #1 [BUILD] subitem implementation = enrichment of
> existing `/api/trading/strategies/catalog` route +
> `unified-trading-system-ui/lib/architecture-v2/catalogue-filter.ts`, per scope decision in
> [`cross_cutting_may_23_deliverables_2026_05_08.md`](../archive/2026_05/cross_cutting_may_23_deliverables_2026_05_08.md)
> § "Strategy catalogue UI route — scope assignment (2026-05-08, Tab 6.C)". This deployment-ui plan does not own that
> surface — append-only banner for read symmetry across plans.
