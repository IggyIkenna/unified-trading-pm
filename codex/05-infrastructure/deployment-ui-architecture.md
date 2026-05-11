---
title: Deployment-UI architecture — 6 tabs, 4 lifecycle classes, 4 orthogonal axes
scope: infrastructure
owner: ikenna
status: stub
codified: 2026-05-08
sources:
  - plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md (Phase A.3 — this doc)
  - plans/epics/instruments_live_master_2026_05_08.md (Phase G delegates UI scope here)
  - plans/active/master_to_live_defi_2026_05_23.md
  - codex/04-architecture/runtime-deployment-topology.md
  - codex/05-infrastructure/launcher-script-ssot.md
  - codex/05-infrastructure/runtime-tiers-and-deployment.md
  - codex/05-infrastructure/deployment-clusters-live-vs-batch.md
  - codex/05-infrastructure/cloud-agnostic-script-pattern.md
  - codex/05-infrastructure/firebase-split-topology.md
---

# Deployment-UI architecture — 6 tabs, 4 lifecycle classes, 4 orthogonal axes

> **🟢 ALIGNED with operator decision (b+) 2026-05-11.** The per-env tier resolution pattern documented in this doc
> (each tier has its own domain → own deployment-api Cloud Run → own GCS bucket scope → own service account scoped to
> that env's projects only) **is already the architectural target** for the bucket-naming SSOT operator decision (b+)
> per [`plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`](../../plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md)
> Phase 0g. No additional UI work needed — env-aware bucket targeting works by the operator navigating to the matching
> domain. **Post-Phase-0c (env-tiered bucket provisioning lands)**: the per-env deployment-api must resolve env-tiered
> bucket names via `resolve_bucket_name(cloud=..., kind=..., asset_group=..., env=...)`; if any API code hardcodes
> flat bucket names (audit at implementation time), fix in same logical unit as Phase 0c. The header env badge
> tooltip should show the resolved env-tiered bucket name(s) for the operator's current page so cross-env
> verification is one-glance.

## TL;DR

- The deployment-UI + deployment-api pair is the workspace SSOT surface for **everything deployable, monitorable, and
  observable** — data-pipeline backfills, ML / strategy / execution research jobs, scheduled recurring triggers, and
  long-lived live clusters — across both clouds (GCP, AWS) and three environment tiers (DEV, STAGING, PROD).
- The UX is shaped by **four mutually-orthogonal axes**: (1) lifecycle class (4 members), (2) cloud target (GCP / AWS),
  (3) environment tier (DEV / STAGING / PROD), (4) service / asset_group. The same logical thing — say, an
  instruments-service backfill — sits at the intersection of all four coordinates simultaneously; the UI's job is to
  make every coordinate visible + togglable without conflating axes.
- **Six top-level tabs**: Deploy / Monitor / Data Status / Builds / Readiness / Config. **Monitor** is the new home for
  runtime state (renamed from History) and carries four sub-tabs — one per lifecycle class — Backfill / Experiments /
  Live / Scheduled.
- **Environment tier is resolved from `window.location.hostname`, never via an in-UI toggle.** Each tier has its own
  deployment-api Cloud Run instance, its own bucket scope, its own Cloud Scheduler entries, its own live clusters — same
  pattern as [`firebase-split-topology.md`](firebase-split-topology.md) + the trading-system-UI.
- **What changed from the old mental model**: the deployment-UI was service-axis-organised (seven peer tabs scoped to a
  single selected service) on the assumption that "deployment" meant "Cloud Run service deploy". It now expresses four
  structurally different lifecycle classes plus three other orthogonal axes; the service-axis sidebar persists as one
  axis among four, not the organising principle.

## The four orthogonal axes

| Axis                  | Members                                                                                | UI surface                                   | Refresh cost on change                                       |
| --------------------- | -------------------------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------ |
| Lifecycle class       | `EPHEMERAL_BATCH` / `EPHEMERAL_EXPERIMENT` / `LONG_LIVED_LIVE` / `SCHEDULED_RECURRING` | Monitor sub-tabs (4 of them)                 | Instant (TanStack Query prefetch, see § Cross-mode prefetch) |
| Cloud target          | `GCP` / `AWS`                                                                          | Header toggle                                | Slow — full network round-trip + cache invalidate            |
| Environment tier      | `DEV` / `STAGING` / `PROD`                                                             | Header badge (read-only; resolved by domain) | N/A — domain-resolved per page load, no in-UI toggle         |
| Service / asset_group | full workspace registry                                                                | Sidebar (existing)                           | Cheap — cached client-side                                   |

Every visible row in the UI sits at exactly one coordinate per axis. Two rows that share lifecycle class + service +
asset_group but differ on cloud target are **two distinct rows**, not a merged row with a "cloud" attribute — the cloud
toggle in the header switches the entire frame, not individual rows.

The UAC SSOTs:

- [`unified_api_contracts/canonical/crosscutting/lifecycle_class.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/lifecycle_class.py)
  — the 4-member `LifecycleClass` enum + classifier helpers (`classify_vm_name`, `classify_cloud_run_service`,
  `classify_scheduled_job`, `classify_experiment_run`).
- [`unified_api_contracts/canonical/crosscutting/cloud_target.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/cloud_target.py)
  — the `CloudTarget` enum (mirrors the deployment-ui `CloudProviderContext`).
- [`unified_api_contracts/canonical/crosscutting/environment_tier.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/environment_tier.py)
  — the `EnvironmentTier` enum + `resolve_environment_from_hostname` helper.

## The six top-level tabs

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
     │           └─ NEW (renamed from History) — runtime state of all jobs / clusters / schedulers
     │              ┌─ Backfill   (EPHEMERAL_BATCH)
     │              ├─ Experiments (EPHEMERAL_EXPERIMENT — ML / strategy / execution)
     │              ├─ Live        (LONG_LIVED_LIVE — clusters)
     │              └─ Scheduled   (SCHEDULED_RECURRING — Cloud Scheduler / EventBridge / VM cron)
     │              every sub-tab: list + per-row actions (re-deploy, stop, start, pause, drain,
     │                              stream-logs, attach-events) using the SAME row-template component
     └─ Fresh deployments only (re-deploys live in Monitor)
```

| Tab             | Purpose                                                                                                                                                                                | Explicitly NOT in scope                                                                                        |
| --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| **Deploy**      | Fresh deployments only — operator picks a service + parameters and clicks Deploy. Single Cloud Build / VM launch / Cloud Run revision rollout.                                         | Re-deploys (run-it-again-with-same-params) — those live in **Monitor** with the original row's run-time state. |
| **Monitor**     | Runtime state of every job / cluster / scheduler in the workspace. 4 sub-tabs (one per lifecycle class). Per-row lifecycle actions.                                                    | One-shot fresh-deploy (that's Deploy). Static configuration views (that's Config / Readiness).                 |
| **Data Status** | Did the catalog / tick / feature data land on disk correctly? Manifest-driven correctness for instruments / MTDS / MDPS / features-\*. 3-mode toggle (Batch / Scheduled-Today / Live). | Strategy / execution / ML signals + metrics — those are **Monitor → Experiments / Live**. Pricing / data only. |
| **Builds**      | Cloud Build / Code Build history + log retrieval. Cloud-toggle aware.                                                                                                                  | Runtime job state (Monitor). Source-code diffs (GitHub).                                                       |
| **Readiness**   | Existing — per-repo C / D / B readiness checklist rollups.                                                                                                                             | Per-shard data correctness (Data Status).                                                                      |
| **Config**      | Existing — workspace config inspection + edit surfaces.                                                                                                                                | Runtime job control (Monitor). VM-launcher mechanics ([`launcher-script-ssot.md`](launcher-script-ssot.md)).   |

## Monitor sub-tab structure

Each Monitor sub-tab uses the SAME row-template component (lifecycle-class-aware) so the operator sees one consistent
layout across all four. Verbs differ — deploy + complete (Backfill / Experiments) vs schedule + pause (Scheduled) vs
start + drain (Live) — but the row-card shape doesn't.

| Sub-tab         | Lifecycle class        | Per-row actions                                       | Reads from                                                                                                                                         |
| --------------- | ---------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Backfill**    | `EPHEMERAL_BATCH`      | re-deploy, stop, restart, stream-logs, attach-events  | VM-name lookup (Phase A.2 lifecycle_class filter) joined with the events bucket (last STARTED / progress / STOPPED / FAILED per `correlation_id`). |
| **Experiments** | `EPHEMERAL_EXPERIMENT` | stop, restart, re-deploy, view-artifacts, stream-logs | Phase BB experiment registry (UAC `experiment_registry.py`) + per-`run_id` blobs at `gs://<pid>-experiments/by_kind={kind}/run_id={run_id}/`.      |
| **Live**        | `LONG_LIVED_LIVE`      | start, stop, pause, restart, drain, stream-logs       | Phase E live-cluster registry (UAC `live_cluster_registry.py`) joined with Cloud Run / GKE service status + per-data_type freshness.               |
| **Scheduled**   | `SCHEDULED_RECURRING`  | run-now, pause, resume, deploy-missing, stream-logs   | Phase D scheduler registry (UAC `scheduler_registry.py`) joined with Cloud Scheduler / EventBridge / VM-cron live state.                           |

The deploy-via-monitor pattern (re-deploy from a Monitor row's context) is first-class. The Deploy tab is exclusively
for FRESH deployments — re-deploys carry forward run-time state (`correlation_id`, chunk-shape, `run_id` for
experiments) that a fresh-deploy doesn't have. Conflating them is the foot-gun where an operator re-deploys from Deploy
with default params and accidentally clobbers an in-flight run.

## Environment-resolution-by-domain

The deployment-UI **never** offers an in-UI environment toggle. Tier is resolved from `window.location.hostname` per
[`unified_api_contracts/canonical/crosscutting/environment_tier.py`](../../../unified-api-contracts/unified_api_contracts/canonical/crosscutting/environment_tier.py)
`resolve_environment_from_hostname(hostname) -> EnvironmentTier`:

| Hostname pattern                      | Tier      | Visual              |
| ------------------------------------- | --------- | ------------------- |
| `localhost` / `127.0.0.1` / `*.local` | `DEV`     | green DEV badge     |
| `staging.<research-domain>`           | `STAGING` | amber STAGING badge |
| `<research-domain>` (no subdomain)    | `PROD`    | red PROD badge      |

Each tier has its OWN deployment-api Cloud Run instance, its own GCS event/log bucket scope, its own Cloud Scheduler
entries, and its own live clusters — same pattern as [`firebase-split-topology.md`](firebase-split-topology.md) for the
trading-system-UI. Operator iteration loop: dev tweaks → ship to staging → soak with staging schedules / staging live
clusters / staging data-status views → promote to prod. Cross-env data leakage is impossible because the deployment-api
per env uses its own service account scoped to that env's projects only.

The Header env badge is read-only — clicking shows a tooltip with the resolved env + the API base URL + the current
cloud-target. **There is no toggle.** If the operator needs a different env, they navigate to the matching domain.

Server-side, deployment-api reads `CLOUD_DEPLOYMENT_ENV` at boot (per
[`runtime-tiers-and-deployment.md`](runtime-tiers-and-deployment.md)) and scopes every registry read (scheduler /
live-cluster / experiment) by the resolved tier. Bucket suffixes per env follow
[`bucket-isolation-model.md`](bucket-isolation-model.md) (e.g. `<pid>-events-staging` vs `<pid>-events-prod`).

## Cross-mode prefetch policy

The UI is asymmetric on purpose:

- **Sub-tab toggle (instant).** Switching between Monitor sub-tabs (Backfill ↔ Experiments ↔ Live ↔ Scheduled) MUST
  feel like clicking a tab in a desktop app. The `LifecyclePrefetchContext` (TanStack Query, already used elsewhere in
  the deployment-ui) fires four parallel queries on UI mount + on cloud-target change:

  ```
  /api/monitor/backfill?cloud=<gcp|aws>
  /api/monitor/experiments?cloud=<gcp|aws>
  /api/monitor/live?cloud=<gcp|aws>
  /api/monitor/scheduled?cloud=<gcp|aws>
  ```

  Cache TTL 60s default. The operator clicks between sub-tabs without paying network latency. A unit test asserts no
  network call fires on sub-tab switch when the cache is warm; performance budget <50ms perceptible delay.

- **Cloud-target toggle (slow + acceptable).** Switching `GCP ↔ AWS` invalidates ALL caches and refetches with a
  loading spinner. Skeleton-loaders or progress indicator on every tab during the load; tab-state preserved across the
  toggle. Explicit "loading" UX is acceptable + expected — a cloud-toggle is a structural switch (different region,
  different SDK, different auth context), not a quick navigation.

The asymmetry is correct because the cost shapes are different: sub-tabs share a backend session (one round-trip fetches
the full lifecycle-class cube for one cloud); cloud-toggle re-targets the SDK clients deployment-api dispatches on,
which means a fresh round of cloud-API calls regardless of caching strategy. Caching wouldn't help; explicit UX keeps
the operator informed.

## Auth-always-available contract

deployment-api boots with **both** GCP and AWS credentials loaded into its session via
[`UnifiedCloudConfig`](../../../unified-config-interface/unified_config_interface/cloud_config.py). The UI cloud-toggle
NEVER re-authenticates — it changes which client is dispatched per request:

```
deployment-api session at boot
  ├─ gcp_storage_client = get_storage_client(provider="gcp")
  ├─ aws_storage_client = get_storage_client(provider="aws")
  ├─ gcp_run_client     = ...
  ├─ aws_ecs_client     = ...
  └─ ...

per-request handler reads CloudTarget from query string → dispatches the right client.
```

No env-var-mode-flag-driven switching, no "set CLOUD_PROVIDER and restart" dance. The deployment-api process always
talks to both clouds; the UI just toggles which it asks about. Same auth-always-available pattern as
[`cloud-agnostic-script-pattern.md`](cloud-agnostic-script-pattern.md).

## Scope split: Data Status vs Monitor

Data Status owns **data + pricing correctness** (manifest-driven). Monitor owns **runtime state of jobs / clusters /
schedulers** (process-state-driven). The split:

| Question                                                          | Tab                   | Why                                                                                                                                                          |
| ----------------------------------------------------------------- | --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Did the catalog land on disk? Is yesterday's MTDS shard captured? | Data Status           | Manifest-driven; the answer is "the parquet is on disk + the manifest row says `captured`/`empty_confirmed`/`attempted_failed`". Static at any given moment. |
| Is the live-MTDS Cloud Run service healthy? How many replicas?    | Monitor → Live        | Process-state-driven; the answer is "Cloud Run reports N healthy replicas, last heartbeat 12s ago". Mutable second-by-second.                                |
| Is today's strategy backtest run completing? What's its loss?     | Monitor → Experiments | Process-state-driven + per-`run_id` metric stream.                                                                                                           |
| Did this scheduler fire today?                                    | Monitor → Scheduled   | Process-state-driven (Cloud Scheduler reports "next run / last run / paused").                                                                               |

Conflating the two confused operators (the 2026-05-08 reasoning behind the Phase B.4 scope reduction):

- "The strategy job is failing" used to surface in Data Status as a freshness gap, even though the underlying issue was
  a process-state problem (`OOMKilled`) not a data-correctness problem. The process-state explanation lives in Monitor;
  Data Status now strictly answers "did the catalog / tick / feature data land?".
- Strategy / execution / ML signals + metrics are NOT in Data Status — they live in Monitor → Experiments (for
  ephemeral) or Monitor → Live (for live-cluster freshness).
- The existing widget tree (`HierarchicalShardDrilldown`, `LiveFreshnessPanel`, parquet schema-view) stays in Data
  Status; the service filter dropdown defaults to data-pipeline services only (instruments / MTDS / MDPS / features-\*).

## Streaming-logs surface contract

A single `StreamingLogsPanel` component powers logs across all four lifecycle classes. Inputs:

```ts
{ lifecycle_class: LifecycleClass,
  target_ref: string,
  correlation_id?: string,
  run_id?: string,
  cluster_name?: string }
```

Streams from deployment-api `GET /api/logs/stream/{target_ref}` (SSE / WebSocket; thin wrapper over the existing GCS
event-stream + Cloud Logging tail). Server-side fans out to the right log source per lifecycle class:

| Lifecycle class        | Log source(s)                                                                                           |
| ---------------------- | ------------------------------------------------------------------------------------------------------- |
| `EPHEMERAL_BATCH`      | VM serial console + GCS event-stream (`gs://<pid>-events/events/{service}/{date}/{correlation_id}/...`) |
| `EPHEMERAL_EXPERIMENT` | VM serial console + GCS event-stream + per-run `metrics.jsonl`                                          |
| `SCHEDULED_RECURRING`  | Cloud Function logs (Cloud Functions scheduler) OR VM serial console + events bucket (VM-cron variant)  |
| `LONG_LIVED_LIVE`      | Cloud Run / GKE per-pod logs                                                                            |

Filter / search / pause / download are client-side over the stream (server sends raw lines). Operator hits the same
component shape from Monitor → Backfill / Experiments / Live / Scheduled rows. Per
[`local-dev.md`](../08-workflows/local-dev.md) testing rule, vitest config must use `pool: "forks"` to avoid zombie node
processes.

## Deploy = fresh deployments only; re-deploys live in Monitor

The Deploy tab fires a single Cloud Build / VM launch / Cloud Run revision rollout. The operator picks a service +
parameters and clicks Deploy.

Re-deploys (run-it-again-with-same-params) live in **Monitor**, not Deploy. The Monitor row's re-deploy action carries
forward run-time state (`correlation_id`, chunk-shape, `run_id` for experiments) that a fresh-deploy doesn't have.

This separation prevents the foot-gun where an operator re-deploys from Deploy with default params and accidentally
clobbers an in-flight run — a class of incident the workspace has hit repeatedly when re-deploys were available from the
Deploy form. The new shape makes "fresh" and "re-run" structurally distinct:

- Fresh deploy = "I want a NEW backfill of the BTC perp from 2024-01-01 to 2024-06-01" → Deploy tab.
- Re-run = "the in-flight backfill VM `cefi-bitfinex-spot-2024-...` died at 64% — pick up from where it left off" →
  Monitor → Backfill row → re-deploy action.

## What's NEW vs reused

| Capability                                           | New?              | Where it lives                                                                      |
| ---------------------------------------------------- | ----------------- | ----------------------------------------------------------------------------------- |
| `LifecycleClass` enum (4 members)                    | NEW               | UAC `crosscutting/lifecycle_class.py`                                               |
| `EnvironmentTier` enum + domain-resolver             | NEW               | UAC `crosscutting/environment_tier.py`                                              |
| VM-prefix `lifecycle_class` annotation               | NEW (extension)   | `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET`                                       |
| 6-tab shell + Monitor sub-tabs                       | NEW (UI re-shape) | `deployment-ui/src/App.tsx`                                                         |
| Mode-prefetch context (4 sub-tabs)                   | NEW               | `deployment-ui/src/contexts/LifecyclePrefetchContext.tsx`                           |
| Streaming logs panel                                 | NEW               | `deployment-ui/src/components/StreamingLogsPanel.tsx`                               |
| Data-Status mode toggle + scope reduction            | NEW               | `DataStatusTab.tsx`                                                                 |
| Live freshness widget                                | NEW               | `LiveFreshnessPanel.tsx`                                                            |
| `/api/monitor/{backfill,experiments,live,scheduled}` | NEW               | `deployment-api/.../routes/monitor_*.py`                                            |
| `/api/logs/stream/{target_ref}`                      | NEW               | `deployment-api/.../routes/logs_stream.py`                                          |
| Scheduler registry SSOT (env-scoped)                 | NEW               | UAC `crosscutting/scheduler_registry.py`                                            |
| Live-cluster registry SSOT (env-scoped)              | NEW               | UAC `crosscutting/live_cluster_registry.py`                                         |
| Experiment registry + tracker UTL helper             | NEW               | UAC `crosscutting/experiment_registry.py` + UTL `experiment_tracker.py`             |
| Env-tier hosting for deployment-UI/API               | NEW (infra)       | Cloud Run staging + prod instances; UI hosted under `staging.<domain>` + `<domain>` |
| Cloud-target context + always-available auth         | REUSED            | `CloudProviderContext.tsx` + `UnifiedCloudConfig` (existing)                        |
| SSE event-stream                                     | REUSED            | `deploy_events_sse.py` (existing)                                                   |
| Batch deploy-missing                                 | REUSED            | `deploy_missing.py` `_SERVICE_LAUNCHER_SCRIPTS` (existing)                          |
| Data-status drilldown / shard schema-view            | REUSED            | `DataStatusTab.tsx` + `HierarchicalShardDrilldown` (existing)                       |
| VM-launcher registry                                 | REUSED            | `deployment-service/scripts/vm/` (existing)                                         |
| Build history + log retrieval                        | REUSED            | `builds.py` / `cloud_builds.py` (existing)                                          |

## Cross-references

- [`codex/04-architecture/runtime-deployment-topology.md`](../04-architecture/runtime-deployment-topology.md) —
  service-axis topology diagrams; this doc adds the lifecycle-class axis on top.
- [`codex/04-architecture/batch-live-architecture.md`](../04-architecture/batch-live-architecture.md) (single SSOT) —
  engineering invariant that batch + live share 99% of the code path. Includes the "UX surface" section explicit on how
  the symmetry shows up to the operator (lifted from former batch-live-symmetry.md, folded 2026-05-08).
- [`codex/05-infrastructure/launcher-script-ssot.md`](launcher-script-ssot.md) — VM-launcher SSOT under
  `deployment-service/scripts/vm/`. The Deploy tab + Monitor → Backfill rows + Monitor → Scheduled deploy-missing button
  all dispatch via this registry.
- [`codex/05-infrastructure/runtime-tiers-and-deployment.md`](runtime-tiers-and-deployment.md) — `CLOUD_DEPLOYMENT_ENV`
  boot-time config + tier semantics. deployment-api per env reads this var; the UI's env badge reads
  `window.location.hostname` and crosschecks against the resolved tier.
- [`codex/05-infrastructure/deployment-clusters-live-vs-batch.md`](deployment-clusters-live-vs-batch.md) — deployment
  cluster taxonomy + per-tier shard semantics. Monitor → Live rows reference this doc for cluster sizing + drain
  semantics.
- [`codex/05-infrastructure/cloud-agnostic-script-pattern.md`](cloud-agnostic-script-pattern.md) — auth-always-available
  pattern that backs the cloud-toggle. deployment-api boots with both clouds; UI dispatches per-request.
- [`codex/05-infrastructure/firebase-split-topology.md`](firebase-split-topology.md) — env-tier hosting for
  trading-system-UI. The deployment-UI follows the same pattern (Phase H of the activation plan).
- [`plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md`](../../plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md)
  — the active plan that owns the activation work this doc captures.
- [`plans/active/deploy_missing_auto_launch_2026_05_07.md`](../../plans/active/deploy_missing_auto_launch_2026_05_07.md)
  — Phase 2 of that plan wires into the Monitor → Backfill row's Deploy-Missing button.
- [`plans/epics/instruments_live_master_2026_05_08.md`](../../plans/epics/instruments_live_master_2026_05_08.md) — Phase
  G of that plan delegates UI scope here.
- [`plans/active/master_to_live_defi_2026_05_23.md`](../../plans/active/master_to_live_defi_2026_05_23.md) — the 6
  long-lived deployment clusters DeFi-live needs by 2026-05-23 are entered into the Phase E live-cluster registry on
  first commit; staging deploy + drain test are part of master's D3 gate.

## Plan provenance

Codified by Phase A.3 of
[`deployment_ui_lifecycle_tabs_2026_05_08.md`](../../plans/active/deployment_ui_lifecycle_tabs_2026_05_08.md). That plan
owns the activation work; this doc is the SSOT for the UX shape the activation produces. As later plan phases ship, this
doc gains concrete file paths + screenshots; today's stub captures the design upfront so mid-plan agents read the SSOT,
not the old service-axis-organised topology.
