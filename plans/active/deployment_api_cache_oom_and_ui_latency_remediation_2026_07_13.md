---
doc_type: plan
title: deployment-api cache OOM + UI latency remediation — bounded caching architecture that fits 4GB
summary:
  uts-shared-deployment-api (the deployment-api backend serving deployment-ui) OOM-crash-looped on Cloud Run 2026-07-13
  04:00Z→ (4GiB limit, 20 kills in 75 min). Root cause — 4 gunicorn workers × ~18 process-local caches, four of them
  unbounded-key with lazy-only expiry, holding full untruncated data-status payloads. Same root cause makes the UI slow
  (per-worker cache fragmentation quarters hit rate; /api/vm-deployments avg 94s, uncached). This plan records ALL
  findings of record (incident evidence, full cache inventory B1–B18, latency table), then drives an operator-joint
  page-by-page / API-by-API walkthrough to decide per-surface caching, worker count, UI-UX, scalability and GCS/BigQuery
  read-write cost budget — then implements bounded caching that fits 4GB (8GB bump only if proven impossible).
status: active
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-ui]
scope: [engineer, admin]
tags:
  [deployment-api, deployment-ui, caching, oom, cloud-run, memory, latency, cockpit, data-status, gunicorn, scalability]
related:
  [
    data_status_tab_and_downloads_remediation_2026_06_16.md,
    ../../codex/04-architecture/runtime-deployment-topology.md,
    ../../codex/05-infrastructure/deployment-observability.md,
  ]
created: 2026-07-13
last_updated: 2026-07-13
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 3.6
locked_by: live-defi-rollout
locked_since: 2026-07-13
supersedes:
superseded_by:
depends_on:
source:
  [
    "operator 2026-07-13 (deployment-ui cache-side OOM report; two goals — fast/responsive UI via proper caching +
    caching stable inside 4GB; 8GB only if impossible; joint page-by-page walkthrough before deciding changes, worker
    count, UI-UX, scalability, GCS read/write costs)",
    "live Cloud Run + Cloud Logging + Cloud Monitoring evidence 2026-07-13 (slot-1 session)",
    "sub-agent cache-island inventory 2026-07-13 (B1–B18, file:line verified)",
  ]
assigned_role: backend-engineer
drift_direction: advance-code
---

# deployment-api cache OOM + UI latency remediation

> **Two goals (operator, 2026-07-13):** (1) make deployment-ui fast and responsive via proper caching; (2) make the
> caching stable so it fits inside the 4GB Cloud Run instance. **8GB is the fallback only if a fit is proven
> impossible.** Decisions on per-page caching, worker count, UI-UX, scalability, and GCS/BigQuery read-write cost are
> made JOINTLY in the § 4 walkthrough before implementation.

**Codex SSOTs**: `codex/04-architecture/runtime-deployment-topology.md` (deployment-api = single deploy/launch +
subscriptions backend for both UIs), `codex/05-infrastructure/deployment-observability.md`,
`codex/06-coding-standards/quality-gates.md` (shipping discipline). This plan references them; it does not duplicate.

---

## 1. Incident of record (2026-07-13)

All measured live from GCP project `central-element-323112`, region `asia-northeast1`:

- **Service**: `uts-shared-deployment-api`, revision `00152-s87` (deployed 2026-07-12T15:14Z). 4GiB / 2 CPU,
  `minScale=1`, `maxScale=20`, `containerConcurrency=80`. The `deployment-dashboard` frontend service (4GiB,
  maxScale 10) is healthy — zero OOM events.
- **OOM kills**: 20 between 04:00Z and 05:15Z (7 in hour 04, 13 in hour 05, accelerating). Zero in the prior 7 days.
  Each — `Memory limit of 4096 MiB exceeded with 4099–4247 MiB used`.
- **User-visible failures**: 503s on in-flight requests at kill time — observed on `/api/vm-deployments?days=1` and
  `/api/deployments/umbrella/{LIVE,BATCH}/summary` (i.e. the cockpit visibly breaking).
- **Memory trend (p99 container utilization)**: flat 64–65% (~2.6GiB) for 12+ hours → 72.7% at 04:16Z → 74.0% → **98.7%
  at 05:16Z**. A step change, not a slow drift.
- **Trigger**: a cockpit UI session + `/ops/costs` page opening ~04:00Z — polls to `/api/vm-deployments?days=1` (40×),
  umbrella summaries (33× each), inventory (31×), `/api/costs/*` (60–80s BigQuery/Athena loads) warmed 4 worker-local
  copies of everything on top of an already-2.6GiB baseline. Request volume was otherwise normal.
- **Instances**: 2 active steady-state; churned 2–4 as instances were killed and autoscaling replaced them (the
  `AUTOSCALING` instance-starts in logs are OOM replacements, not load).
- **Amplifier**: gunicorn `max_requests=1000` (+jitter 100) worker recycling — old+new worker coexist briefly during
  recycle; on a container at ~90% that transient alone can tip the 4GiB limit.

## 2. Findings of record — architecture

### 2.1 Process topology multiplies everything ×4

`gunicorn.conf.py` runs `WORKERS` uvicorn workers; default **4** (`deployment_api_config.py:187-191`), **no override on
the deployed Cloud Run service** (env carries only GCP_PROJECT_ID / CLOUD_PROVIDER / CLOUD_MOCK_MODE / DEPLOYMENT_ENV /
DISABLE_AUTH). Consequences, all verified in code:

- **Every cache below exists 4× per container** (all are process-local). The ~2.6GiB idle baseline ≈ 4 × ~650MiB.
- **Cache hit rate is ¼**: cockpit polls round-robin across workers; 3 of 4 polls hit a cold worker and recompute. This
  is why `/api/deployments/inventory` averages 32s despite a working 45s stale-while-revalidate cache.
- **`POST /api/cache/clear` clears only the one worker that receives it** (`health_routes.py:231-295`).
- **4 duplicate background sync loops** per instance (`lifespan.py:163` starts one per worker;
  `background_sync.py::auto_sync_running_deployments` → `sync_service.sync_deployments` scans `deployments.prod/` in GCS
  every 30–60s per worker, contending on per-deployment locks). GCS list+read ops are therefore 4× what one instance
  needs; `_cleanup_recent_orphans` additionally re-loads every non-active state file every cycle
  (`sync_service.py:461-510`).
- **Data-status process pool** (`services/data_status/manifest.py:388-416`, up to 3 forked children per build, per
  worker) COW-inherits the parent's `_INDEX_CACHE` DataFrames — worst case 4 workers × 3 children of forked pandas.

### 2.2 The distributed cache tiers are dead — everything is per-process RAM

- **Redis tier is inert in prod** (verified exhaustively): `REDIS_URL` defaults to `redis://localhost:6379/0`
  (`deployment_api_config.py:411-414`); no `REDIS_URL` env, no `--vpc-connector`, no Memorystore reference anywhere in
  `cloudbuild*.yaml` / `Dockerfile*` / deploy scripts. `RedisCache.connect()` fails, sets `_provider=None`, and every
  get/set silently no-ops (`utils/cache.py:154-212`).
- **GCS tier effectively unused**: `gs://unified-deployment-state-.../cache/` holds only a 146-byte
  `service_status_cache.json`; `cache/unified_cache.json` does not exist. Design flaws if it ever gets used:
  `GCSCache._local_cache` mirrors the WHOLE blob in memory per worker, `set()` fire-and-forgets a full-blob `json.dumps`
  rewrite to GCS per write with unbounded executor concurrency (`utils/cache.py:250-395`) — a GCS write-cost +
  memory-spike trap.
- Net: `UnifiedCache` (`utils/cache.py:398-590`) is in practice **only** its unbounded in-memory dict.

### 2.3 Cache-island inventory (18 sites, file:line verified — sub-agent report 2026-07-13)

Legend — **Bound**: entry cap / eviction discipline. **Expiry**: lazy = only reclaimed if the SAME key is re-read
(never-repeated keys leak forever); none of the caches below has a periodic sweeper unless noted.

| #   | Site (file:line)                                                                  | Stores                                                                                      | Bound / expiry                                               | Key cardinality                                                                                              | Risk                                                    |
| --- | --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------- |
| B1  | `utils/data_status_cache.py:36` `_cache`                                          | **FULL untruncated** data-status trees (all `dates_found/missing_list` per venue×data_type) | **NONE** / lazy 1800s                                        | **EXTREME** — key includes `freshness_date` (tracks "today") + arbitrary UI date ranges → keys ~never repeat | **HIGH — #1 RSS driver**                                |
| B2  | `services/data_analytics_service.py:39` `_turbo_cache`                            | full turbo data-status results + `size_estimate`                                            | 100 entries, evict-oldest-20% / lazy 300s                    | same family as B1, self-limiting                                                                             | MEDIUM (count-capped, **no byte ceiling**)              |
| B3  | `services/data_status_drilldown/_core.py:112` `_cache`                            | per-shard instrument listings (thousands of dicts), shard_info, bucket_counts               | **NONE** / lazy 300s                                         | **HIGH — `day` in every key → new cohort every calendar day forever**                                        | **HIGH**                                                |
| B4  | `routes/deployments_inventory.py:279` `_inventory_cache`                          | full multi-cloud fleet census snapshot (`DeploymentItem` ×30 fields)                        | bounded key set (~6–10) / 45s SWR replace                    | LOW                                                                                                          | LOW (not a leak; large **always-warm** baseline)        |
| B4b | `routes/deployments_inventory.py:348` `_last_alerted_health`                      | status string per VM name                                                                   | **never pruned** on VM disappearance                         | grows with spot/backfill VM churn                                                                            | MEDIUM (tiny entries, real growth)                      |
| B5  | `routes/log_analysis.py:17` `_log_analysis_cache`                                 | ~110 raw log lines per deployment                                                           | **NONE** / lazy 60s                                          | **HIGH — one key per deployment_id forever**                                                                 | **HIGH**                                                |
| B6  | `routes/_repo_ci_github.py:48` `_response_cache`                                  | GitHub REST JSON per full URL                                                               | **NONE** / lazy 90s                                          | MEDIUM-HIGH — per-commit-SHA / per-file URLs never repeat                                                    | MEDIUM                                                  |
| B7  | `services/data_status/mtds.py:364` `mtds_expected_dates_cached`                   | `frozenset[str]` expected trading dates per (venue,dt,cat,window)                           | **lru_cache(8192)** — real eviction                          | near-full daily (window_end tracks today)                                                                    | LOW-MEDIUM (**bounded ceiling ≈ up to ~700MiB/worker**) |
| B8  | `breakdowns_domain.py:526` `_vexp_cache`                                          | per-call local memo                                                                         | freed per call                                               | —                                                                                                            | LOW (not persistent)                                    |
| B9  | `routes/deployment_caching.py:18,23,28` `_logs/_vm_logs/_verification`            | logs/verification payloads                                                                  | **MAX_ENTRIES 100/50/100 + evict-oldest on every set** + TTL | bounded                                                                                                      | LOW — **the correct in-repo reference pattern**         |
| B10 | `routes/service_status_cache.py:17` `_local_cache`                                | per-service status dicts (mirror of one GCS blob)                                           | bounded by fleet service count                               | LOW                                                                                                          | LOW                                                     |
| B11 | `services/cost_observability/cache.py:21` `CostWindowCache`                       | few-thousand `CostRecord` lists per query window                                            | no cap / lazy 3600s                                          | LOW (few reused windows)                                                                                     | LOW                                                     |
| B12 | `routes/_cloud_builds_trigger.py:49` `_trigger_id_cache`                          | trigger_name→id                                                                             | replace-on-refresh                                           | LOW                                                                                                          | LOW                                                     |
| B13 | `routes/repo_ci.py:324` `_builds_cache`                                           | per-cloud build signals                                                                     | 2 keys                                                       | LOW                                                                                                          | LOW                                                     |
| B14 | `utils/artifact_registry.py:21` `_image_cache`                                    | per-image metadata                                                                          | lazy 300s                                                    | LOW (fixed image set)                                                                                        | LOW                                                     |
| B15 | `utils/deployment_events.py:12` `_sse_queues`                                     | SSE queues per deployment                                                                   | self-cleans in `finally`                                     | —                                                                                                            | LOW                                                     |
| B16 | `routes/deployments_helpers.py:22` `_verification_cache`                          | **DEAD CODE** — uncapped twin of B9, never called                                           | —                                                            | —                                                                                                            | latent foot-gun → **delete**                            |
| B17 | single-scalar caches (health_consolidator, fleet_reconciliation, WIF/token, etc.) | one entry each                                                                              | by construction                                              | —                                                                                                            | LOW                                                     |
| B18 | `config_loader.py:68` `_cache`                                                    | YAML config per filename                                                                    | fixed file set                                               | LOW                                                                                                          | LOW                                                     |

Supporting size evidence:

- Offline rollup blobs (`gs://central-element-323112-data-status-rollups/`) — instruments `full.json.gz` **825KB**, MTDS
  `full.json.gz` **3.2MB** gzipped → ~10–30× as JSON text, ~3–5× more as live Python dicts → **one B1 entry can be
  ~100–400MB**. A handful × 4 workers = the whole OOM.
- `_INDEX_CACHE` availability-index DataFrames ≈ **30MB per bucket**, 5-min TTL, replace-on-expiry
  (`data_status_service.py:438-457`) — bounded but always-warm, ×4 workers (+COW forks).
- B7 worst case: multi-year window ≈ 2,200 date strings ≈ ~90KB/entry × 8192 cap.

### 2.4 The single `deepcopy` amplifier

`utils/data_status_cache.py:278` `truncate_dates_list()` does `copy.deepcopy(result)` on **every truncated-view cache
hit** of the B1 mega-cache (called from `routes/batch_cache_manager.py:72`) — a transient second full copy of a
potentially-multi-hundred-MB dict per request, concurrent under load. Only deepcopy site in the package.

### 2.5 Measured endpoint latency (the UI-slowness side, since 2026-07-12 15:00Z deploy)

| Endpoint                                  | n   | avg        | max    | Current caching                                                                                      |
| ----------------------------------------- | --- | ---------- | ------ | ---------------------------------------------------------------------------------------------------- |
| `/api/vm-deployments?days=1`              | 45  | **93.75s** | 99.27s | **NONE** — full GCS registry walk + per-VM Compute API per poll (`routes/vm_deployments.py:177-246`) |
| `/api/deployments/umbrella/BATCH/summary` | 37  | 41.35s     | 70.78s | shares B4 inventory (per-worker)                                                                     |
| `/api/deployments/umbrella/PAPER/summary` | 37  | 38.70s     | 73.33s | shares B4 inventory (per-worker)                                                                     |
| `/api/deployments/umbrella/LIVE/summary`  | 38  | 36.41s     | 73.33s | shares B4 inventory (per-worker)                                                                     |
| `/api/deployments/inventory`              | 37  | 31.89s     | 70.72s | B4, 45s SWR — defeated ×4 workers                                                                    |
| `/api/costs/breakdown`                    | 3   | 65.54s     | 80.86s | B11, 1h TTL per worker; BigQuery/Athena underneath                                                   |
| `/api/costs/timeseries` / `summary`       | 2   | ~62s       | 63s    | B11                                                                                                  |

UI polling cadence (deployment-ui, verified): LiveDeployments 30s + logs 10s; Cockpit consolidators 30s; readiness /
repo-coverage / gh-rate 60s; kill-switch tab 5s.

### 2.6 GCS / query cost surfaces (for the § 4 cost decision)

1. Background sync: 4 workers × (list + N state reads) every 30–60s per instance, ×2 instances steady — most of it
   redundant (same data, 8 readers). `deployments.prod/` is currently **empty** (0 objects) yet the loops still run.
2. `/api/vm-deployments`: full active+archive registry walk per poll (no cache) — GCS class-A/B ops every 30s per open
   cockpit tab.
3. `GCSCache.set()` rewrites the entire cache blob per write (currently unused — keep it that way or fix before use).
4. `/api/costs/*`: BigQuery (GCP free-ish) + **Athena (per-query cost)** scans; cached 1h but per-worker → up to 4× the
   intended query volume per instance.
5. Data-status: the heavy GCS manifest scans behind B1/B2 exist precisely to be amortized by caching — the offline
   rollup fast-path (`uts-prod-data-status-rollup` Cloud Run job writing `full.json.gz` every 5 min) is the
   already-built cheap read path to prefer where fresh-enough.

## 3. Fit-in-4GB verdict (working hypothesis for § 4)

**Yes — fits, with headroom.** Steady-state projection at `WORKERS=2` + bounded caches ≈ 2 × (350–450MB base + 250–350MB
bounded caches) ≈ **1.2–1.6GiB**, leaving ~2.4GiB for spikes (which also shrink once the deepcopy and whole-blob dumps
go). 8GB would only mask the leak class (B1/B3/B5 grow without bound — they'd OOM an 8GB box too, just later) and is NOT
recommended; revisit only if § 4 decisions demand keeping 4 workers AND per-worker mega-caches.

## 4. Joint walkthrough — decide per UI page / per API (operator + agent, fill in place)

> Method: open each page in deployment-ui against the live backend, observe network panel + perceived latency, then fill
> Decision columns. Decisions feed the § 5 todos. Rows are the full page inventory from `deployment-ui/src/pages`
>
> - cockpit tabs; add rows as discovered.

| Page / surface                       | Backing APIs                                                                                 | Today (cache / latency)                                  | Decision — caching                                  | Decision — UX/polling |
| ------------------------------------ | -------------------------------------------------------------------------------------------- | -------------------------------------------------------- | --------------------------------------------------- | --------------------- |
| Cockpit — deployments tab            | `/api/deployments/inventory`, `/api/deployments/umbrella/{U}/summary`, `/api/vm-deployments` | B4 45s SWR (per-worker); vm-deployments UNCACHED avg 94s | _TBD_                                               | _TBD_                 |
| Cockpit — consolidators tab          | `/api/health/consolidator`                                                                   | 30s poll                                                 | _TBD_                                               | _TBD_                 |
| Live deployments page                | `/api/deployments*`, logs endpoints                                                          | B9 bounded logs caches (correct pattern)                 | _TBD_                                               | _TBD_                 |
| Data-status tab (turbo + drill-down) | `/api/.../data-status*`, drilldown, downloads                                                | B1 unbounded mega-cache + B2 turbo + B3 drilldown        | _TBD_ (gzip? entry caps? rollup fast-path default?) | _TBD_                 |
| Ops / costs                          | `/api/costs/{summary,breakdown,timeseries}`                                                  | B11 1h/worker; 60–80s cold                               | _TBD_ (pre-warm? longer TTL? persist?)              | _TBD_                 |
| Repo CI / coverage / escalations     | `/api/repo-ci/*`, `/api/repos/gh-rate-limit`                                                 | B6 unbounded URL cache, B13                              | _TBD_                                               | _TBD_                 |
| Kill-switch tab                      | kill-switch status APIs                                                                      | 5s poll                                                  | _TBD_                                               | _TBD_                 |
| Launch consoles / readiness          | `/api/services/*`, `/api/deployments/validate*`                                              | B9/B10                                                   | _TBD_                                               | _TBD_                 |

Cross-cutting decisions to settle in the same session:

- **D1 — worker count**: `WORKERS=2` (recommended) vs 1 vs keep 4. Interacts with CPU=2, concurrency=80, and sync-loop
  duplication.
- **D2 — memory limit**: keep 4GiB (recommended per § 3) vs 8GiB.
- **D3 — shared cache tier**: none (per-instance only, recommended first step) vs GCS-rollup-style precomputed blobs for
  the heavy surfaces vs real Redis/Memorystore (+VPC connector cost/complexity).
- **D4 — background sync topology**: 1 loop per instance (leader by worker id) vs per-worker; and whether the loop
  should idle-skip when `deployments.prod/` is empty (it is today).
- **D5 — GCS/Athena cost budget**: acceptable op-rate for polls (drives SWR TTLs) + whether `/api/vm-deployments` gets
  its own SWR snapshot (recommended) — turns 94s → instant-after-first.
- **D6 — observability**: RSS/cache-size gauge endpoint + Cloud Monitoring alert at 85% memory so the next regression
  pages before it OOMs.

## 5. Todos

Phase A — walkthrough + decisions (operator-joint; blocks Phase B):

- [ ] [OPERATOR] P0. § 4 walkthrough session — open each deployment-ui page against live backend, fill every Decision
      cell + settle D1–D6 in place. `BLOCKED-OPERATOR-DECISION` until scheduled.
- [ ] [BACKEND] P0. During walkthrough — capture per-page network timings (browser devtools HAR or timed curls) into § 4
      "Today" column where still approximate; verify the B1 entry-size estimate live via `/api/.../cache-stats`
      (`size_estimate` fields, B2) + a one-off RSS probe per worker.

Phase B — implementation (gated on Phase A decisions; each lands via quickmerge with QG-green tree):

- [ ] [INFRA] P0. Apply D1/D2 — set `WORKERS=<decided>` env on `uts-shared-deployment-api` (gcloud run services update;
      also encode in cloudbuild deploy step so it survives redeploys). Evidence — revision env + memory trend 24h after.
- [ ] [BACKEND] P0. One bounded cache primitive (generalize the B9 pattern already in `routes/deployment_caching.py`, or
      `cachetools.TTLCache` — already a transitive dep): max-entries + TTL + evict-on-set + a single periodic sweeper
      task; expose per-cache stats (entries, est. bytes) on one debug endpoint (feeds D6).
- [ ] [BACKEND] P0. B1 `data_status_cache` — cap entries (LRU ~8), store **gzipped JSON bytes** not live dicts, drop
      `freshness_date` from the key (or normalize it) so keys actually repeat, kill the per-hit `deepcopy` (serve
      pre-truncated variant computed once at store time).
- [ ] [BACKEND] P1. B3 drilldown `_core.py` — bound with the primitive (day-keyed growth ends); B5 `log_analysis` —
      bound per-deployment entries; B6 `_repo_ci_github` `_response_cache` — bound + skip caching one-time per-SHA URLs;
      B4b `_last_alerted_health` — prune names absent from the current census; delete dead B16.
- [ ] [BACKEND] P1. `UnifiedCache.in_memory` — bound it; decide GCSCache fate per D3 (delete or fix whole-blob rewrite
      before first real use); B7 `lru_cache` 8192 → ~512; B2 turbo cache — add byte ceiling next to the 100-entry cap.
- [ ] [BACKEND] P1. `/api/vm-deployments` — add the 45s SWR snapshot pattern per D5 (single-flight, background refresh),
      reusing `_load_inventory`'s proven shape. Target — instant-after-first-load instead of 94s.
- [ ] [BACKEND] P2. Costs endpoints per walkthrough decision — pre-warm on background refresher or lengthen TTL (Athena
      per-query cost is the constraint), so /ops/costs never blocks 60–80s interactively.
- [ ] [INFRA] P2. Background sync per D4 — single loop per instance + idle-skip on empty `deployments.prod/`; quantifies
      straight into GCS op-cost reduction.
- [ ] [UI] P2. deployment-ui polling adjustments decided in § 4 (per-tab intervals, visibility-paused polling if
      decided) — with `pw:L2 ✓` + cited regression spec per UI gate.

Phase C — verification + guardrails:

- [ ] [BACKEND] P1. Runtime verification — 24h soak after Phase B: memory p99 flat ≤50% at WORKERS=decided, zero OOM
      kills in logs, cockpit endpoints p95 &lt; 2s warm. Evidence — monitoring queries + log counts cited here.
- [ ] [INFRA] P2. D6 alerting — Cloud Monitoring alert on memory utilization &gt;85% (5 min) for
      uts-shared-deployment-api; wire to existing alerting channel.
- [ ] [BACKEND] P2. Post-phase codex audit — update `codex/05-infrastructure/deployment-observability.md` (cache
      architecture + stats endpoint + alert) and `codex/04-architecture/runtime-deployment-topology.md` if worker
      topology changed; SUPERSEDED-banner any invalidated statements.

## 6. Progress log

- 2026-07-13 (slot-1, interactive): Incident measured live (§ 1); topology + cache inventory verified (§ 2, incl.
  sub-agent B1–B18 report); latency table measured from request logs (§ 2.5); fit-in-4GB analysis written (§ 3); plan
  authored. Immediate-relief option (`WORKERS=2` env-only change) surfaced to operator — **not applied**; operator
  directed plan-first + joint walkthrough before any change.
