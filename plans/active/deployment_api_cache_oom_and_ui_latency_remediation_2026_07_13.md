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
    /plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md,
    /codex/04-architecture/runtime-deployment-topology.md,
    /codex/05-infrastructure/deployment-observability.md,
  ]
created: 2026-07-13
last_updated: 2026-07-14
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
assigned_role: backend_engineer
drift_direction: advance-code
---

# deployment-api cache OOM + UI latency remediation

> **Two goals (operator, 2026-07-13):** (1) make deployment-ui fast and responsive via proper caching; (2) make the
> caching stable so it fits inside the 4GB Cloud Run instance. **8GB is the fallback only if a fit is proven
> impossible.** Decisions on per-page caching, worker count, UI-UX, scalability, and GCS/BigQuery read-write cost are
> made JOINTLY in the § 4 walkthrough before implementation.

**Codex SSOTs**: `/codex/04-architecture/runtime-deployment-topology.md` (deployment-api = single deploy/launch +
subscriptions backend for both UIs), `/codex/05-infrastructure/deployment-observability.md`,
`/codex/06-coding-standards/quality-gates.md` (shipping discipline). This plan references them; it does not duplicate.

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

### 2.7 Measured benchmark results (2026-07-13 benchmark session, slot-1)

Three suites run by the agent per operator direction — latency vs the DEPLOYED service, page-level Playwright vs the
deployed SPA, memory vs a LOCAL 4-worker replica (same gunicorn config, real GCS/ADC read paths, per-2s RSS sampling of
the whole process tree with phase attribution). Raw CSVs/JSON in the session scratchpad; summaries below are the
findings of record.

**(a) Deployed API latency — bimodal + actively failing** (sequential curls, cold vs warm, during the live crash-loop):

| Endpoint                | Observed sequence (status:seconds)                      | Reading                                                   |
| ----------------------- | ------------------------------------------------------- | --------------------------------------------------------- |
| `/api/health`           | 200:0.2–1.2s                                            | fine standalone                                           |
| `…/inventory`           | 503:29.4 → 200:46.3 → 503:69.9 → **200:1.0** → 503:69.8 | warm-worker hit is SUB-SECOND; cold 46s; 503s = OOM churn |
| `…/umbrella/*/summary`  | mix of 503:34–77s and 200:0.7–75s                       | same bimodality (`BATCH` warm hit 0.7s)                   |
| `/api/vm-deployments`   | 500:29.3 → 503:62.9 → 503:43.2 — **never succeeded**    | uncached + heaviest endpoint                              |
| `/api/costs/summary`    | 503:61.0 → 503:36.4                                     | 60s+ then dies                                            |
| `/api/repo-ci/overview` | 200:13.3 → 200:6.6 → 200:3.8 → 200:2.3                  | warms gradually (per-worker copies)                       |

**(b) Real-browser page experience** (Playwright chromium, 6 pages, 90s observation each):

| Page                         | Shell paint (FCP) | Data reality                                                            |
| ---------------------------- | ----------------- | ----------------------------------------------------------------------- |
| `/cockpit?tab=deployments`   | 2.2s              | **ALL 5 data calls failed** (503/500 after 29–38s) — page renders empty |
| `/cockpit?tab=consolidators` | 4.1s              | OK; consolidator 1.8–7.8s                                               |
| `/vm-deployments`            | 8.1s              | main call 503 after 43s                                                 |
| `/deployments`               | 6.3s              | succeeds but 44–57s per data call — ~1 min blank                        |
| `/ops/live-deployments`      | 6.0s              | vm-deployments 500 after 42s                                            |
| `/ops/costs`                 | 2.6s              | breakdown 72–82s (200); summary/timeseries 503 after ~60s               |

Also observed: `/api/health` intermittently 6–28s while heavy sync handlers run — worker starvation under
`containerConcurrency=80` with 4 workers × threadpool'd sync `def` handlers (input to D1).

**(c) Local memory — per-surface RSS attribution** (4 workers, tree = master+workers+forks, unconstrained host RAM so
the TRUE footprint is visible):

| Phase                                               | Tree RSS (min → peak)                          | Reading                                                                                                           |
| --------------------------------------------------- | ---------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| Idle after startup                                  | **2,481MB** flat                               | matches deployed 64–65% baseline exactly — startup state × 4 workers                                              |
| Inventory + umbrellas (×3 rounds)                   | 2,482 → **4,173MB**                            | +1.7GB; already crosses the 4GiB Cloud Run limit on its own                                                       |
| `/api/vm-deployments` (2 hits; local: 300s timeout) | 3,917 → **6,657MB**                            | +2.5GB more; matches prod dying mid-vm-deployments; leaves ~4.5GB residue                                         |
| repo-ci round                                       | 4,459 → 5,335MB                                | modest                                                                                                            |
| turbo instruments (small + 3 date-range keys)       | 4,502 → 4,837MB                                | ~90KB responses; ~100MB-class per-worker growth — instruments is NOT the elephant                                 |
| turbo warm repeats ×4 (same key)                    | **0.006s ×3, 1.28s ×1**                        | cache hit = 6ms; the 4th landed on a cold worker — fragmentation quantified                                       |
| **turbo MTDS (ONE query — 16 days, cefi only)**     | 4,862 → **15,968MB** peak, settles **8,416MB** | **+11GB transient, +3.5GB PERMANENT from a single query** (71.2s); process-pool forks + index build + B1/B2 store |
| Post-idle (60s)                                     | 8,416MB flat                                   | the growth never comes back — held by caches/heap                                                                 |

**Implications that supersede earlier estimates:** (1) the MTDS data-status path is the memory elephant — the
`_INDEX_CACHE` "~30MB/bucket" code comment is off by an order of magnitude for MTDS buckets; a single UI data-status
query for MTDS is an instant OOM at 4GiB under current code REGARDLESS of worker count. (2) vm-deployments and the
inventory census are the cockpit killers (transient GBs, uncached / per-worker). (3) Warm-path performance is already
excellent (6ms–1.0s) — the entire UX problem is hit-rate (×4 workers) and the uncached/unbounded paths.

### 2.8 Per-page profiling sweep (2026-07-13 session 2 — real UI via vite → local 4-worker backend)

Full sweep: all data-status services via the REAL UI path, plus all 19 pages (every cockpit tab incl.
cicd/consolidators/alerts + fleet/cost/deployments/nav routes), Playwright-driven real UI, 3 passes each (cold+hot),
capturing browser JS heap + backend tree RSS + per-`/api` latency. Full detail + raw data: session scratchpad
`bench2/FINDINGS.md`. **Host had 72GB free / 24 cores; a memory guard auto-killed the backend at 50GB to protect the
machine.**

**⚑ CORRECTION to §2.7:** session 1 measured `/api/data-status/turbo` for MTDS, but the REAL UI calls
`/api/data-status/manifest` for IS/MTDS/MDPS (verified `deployment-ui/src/api/client.ts:1731-1761` +
`DataStatusTab.tsx:480`; MDPS was explicitly REMOVED from turbo for hanging). The manifest path is the true driver and
is far worse than the turbo number suggested:

| Data-status service | Range (UI default = full history from 2018-01-01) | Latency        | Peak backend RSS         |
| ------------------- | ------------------------------------------------- | -------------- | ------------------------ |
| instruments-service | full 2018→2026                                    | 90s (uncached) | **18GB** (~13GB residue) |
| MTDS                | full 2018→2026                                    | did not return | **81GB**                 |
| MTDS                | 1 year (2025)                                     | did not return | **50GB+**                |
| MDPS                | **3 months** (Q4-2025)                            | did not return | **56GB+**                |

- **The manifest path caches only the raw parquet index (`_INDEX_CACHE`, 5-min TTL), never the computed cell-grid** — so
  IS hot (89s) == cold (92s). The cell-grid is materialized in full by a forked `ProcessPoolExecutor` and scales with
  (date-span × venue × data_type × instrument_type).

> **⚠️ ROOT-CAUSE CORRECTION (2026-07-13, after operator challenge — this reframes §2.8 above and §3 below).** The
> 18/81/56GB live build measured above is the **DEGRADED FALLBACK**, not the intended path — and full-range IS/MTDS/MDPS
> worked fine until ~2026-07-05. **This is a regression.** Intended path (`services/data_status/manifest.py:155-166`):
> the all-AG view is served from a PRECOMPUTED `gs://{pid}-data-status-rollups/{service}/full.json.gz` (IS 825KB, MTDS
> ~3MB gz) written each cron cycle by the `uts-prod-data-status-rollup-svc` worker, sliced in-memory
> (`_read_rollup_if_fresh`→`slice_rollup_to_window`) — **sub-second, a few MB.** It falls through to the live build ONLY
> when the blob is missing/stale (`age > ROLLUP_STALENESS_SEC=1800s`). **Two changes broke it last week:** (1) the
> **rollup worker (16GiB/4CPU) is OOMing every cycle** — same cell-grid build, now >16GiB for MTDS/MDPS:
> `Memory limit of 16384 MiB exceeded` **71× (07-11), 144× (07-12), 74× (07-13)**; it can no longer write MTDS/MDPS
> blobs (GCS now holds ONLY `instruments-service/*` — MTDS/MDPS `full.json.gz` are GONE) and writes IS only
> sporadically. (2) commit **`3847d6f` (2026-07-08) "rollup staleness gate never fires — meta.updated doesn't exist"**
> correctly switched the gate from the non-existent `meta.updated` to `meta.last_modified`; BEFORE it the gate never
> fired so a stale blob was served indefinitely (cheap, slightly-stale — "worked before"), AFTER it stale/missing blobs
> are rejected → API falls through to the live build → **OOMs the 4GiB API.** So there are **TWO OOMs of the SAME
> build** — the 16GiB worker (blobs go dark) and the 4GiB API (live fallback). Timeline matches the incident: worker
> degrades ~07-05 → staleness fix 07-08 → reaches prod API 07-12 → first data-status click 07-13 → OOM (§1).
>
> **Corrected fix priority:** (1) PRIMARY — make the cell-grid build fit memory (bounded/streamed/capped): one fix
> resolves BOTH OOMs; then the worker resumes writing blobs and the API fast-path serves them → OOM gone +
> 90s→sub-second. (2) restore the rollup worker now (stopgap). (3) API defense-in-depth — on stale/missing rollup,
> serve-stale-as-last-resort (logged) and/or cap/refuse the live build, so a future worker outage degrades to
> "slightly-stale/slow" not "OOM crash-loop." (4) session-1 items (WORKERS=2, bounded caches, /ops/costs) remain valid
> but SECONDARY. **RAM bumps still don't fix it** (16GiB worker already OOMs) — but the fix is now clearly
> bound-the-build + restore-the-precompute, NOT a from-scratch re-architecture.

**Page sweep (non-data-status) — memory is NOT a page problem except billing; the issue is cold latency:**

- Per-page permanent backend RSS delta: **`/ops/costs` +1,863MB** (55s BigQuery/Athena breakdown, loads full cost-record
  set) is the distant #2 memory consumer; `cockpit?tab=deployments` +542MB, `tab=health` +446MB, `tab=fleet` +259MB;
  **every other page ≤60MB.**
- Browser JS heap (dev-mode): uniform **32–56MB** across all 19 pages — client-side memory is a non-issue anywhere.
- **Cold-latency offenders (uncached/weak-cache backend endpoints, ~as slow hot as cold) = the Phase-B caching
  targets:** `/ops/costs` breakdown **55s**, `health/overview` **19.7s**, `repo-ci/overview` (cicd tab) **17.9s**,
  `health/consolidator` **13.8s**, `fleet/orphans` **13.6s**, `deployments/regions` **11.1s**, `epics/plans` **10.2s**.
- **Worker multiplication confirmed live:** 19 light pages accumulated backend RSS **3.0GB → 6.3GB** (4 workers ×
  per-worker cache warmup). `WORKERS=2` ~halves it — cheapest immediate win.
- `/vm-deployments` did NOT reproduce the prod 94s locally (empty local registry) — prod 94s = the GCS registry walk
  over populated data (§2.5 stands).

## 3. Fit-in-4GB verdict (REVISED per §2.7 + §2.8 measurements)

**Fits — but ONLY by re-architecting the data-status manifest compute+cache path; worker count alone is nowhere near
enough.** The manifest cell-grid build measured **18GB (IS) / 81GB (MTDS) / 56GB-for-3-months (MDPS)** — no RAM tier
through 64GB survives it, so the fix must bound/stream the compute window, cap the grid, and cache/precompute the result
(ideally serve the existing `uts-prod-data-status-rollup` `full.json.gz` blobs already in GCS instead of a live build).
With that done: 4-worker baseline 2.48GB → ~1.24GB at `WORKERS=2`; the only other real memory consumer, `/ops/costs`
(+1.9GB), gets a bounded/streamed cost cache; light-page steady-state ~1.2–1.8GiB with headroom. **8GB remains NOT
recommended** — it masks nothing here (the elephant dwarfs it) and the fit is achievable at 4GiB.

## 4. Joint walkthrough — decide per UI page / per API (operator + agent, fill in place)

> Method: open each page in deployment-ui against the live backend, observe network panel + perceived latency, then fill
> Decision columns. Decisions feed the § 5 todos. Rows are the full page inventory from `deployment-ui/src/pages`
>
> - cockpit tabs; add rows as discovered.

| Page / surface                                                | Backing APIs                                                                                 | Today (MEASURED 2026-07-13, § 2.7)                                                                                                                                    | Decision — caching                                                                                                                                                                                                                                                                                                       | Decision — UX/polling                                                                                                                                                                                                    |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Cockpit — deployments tab                                     | `/api/deployments/inventory`, `/api/deployments/umbrella/{U}/summary`, `/api/vm-deployments` | FCP 2.2s but ALL 5 data calls 503/500 (29–38s); warm hit 0.7–1.0s vs cold 46s; vm-deployments UNCACHED, never succeeded; +1.7GB / +2.5GB RSS per surface              | **DECIDED 2026-07-14**: covered by bounded caches + WORKERS=2 (fixes ¼ hit-rate fragmentation) + a new `/api/vm-deployments` 45s SWR snapshot matching the proven inventory/umbrella pattern — no further backend change.                                                                                                | **DECIDED**: keep 30s poll; add visibility-paused polling; replace blank-render-until-all-5-calls-resolve with a loading skeleton / per-section incremental render.                                                      |
| Cockpit — consolidators tab                                   | `/api/health/consolidator`                                                                   | OK — 1.8–7.8s; 30s poll                                                                                                                                               | **DECIDED**: no change needed, already acceptable.                                                                                                                                                                                                                                                                       | **DECIDED**: keep 30s; add visibility-paused polling.                                                                                                                                                                    |
| VM deployments page                                           | `/api/vm-deployments?days=7`, venue-\*                                                       | main call 503 @43s; venue-\* endpoints all &lt;1s                                                                                                                     | **DECIDED**: covered by the new `/api/vm-deployments` SWR snapshot.                                                                                                                                                                                                                                                      | **DECIDED**: keep interval; add visibility-paused polling; show last-known-good data with a "refreshing" indicator during background SWR refresh instead of a blocking spinner.                                          |
| Deployments page                                              | inventory + umbrellas + regions                                                              | succeeds but 44–57s per call — ~1 min blank page                                                                                                                      | **DECIDED**: covered by existing SWR (inventory/umbrellas) once WORKERS=2 raises hit rate.                                                                                                                                                                                                                               | **DECIDED**: loading skeleton / progressive per-section render instead of a ~1 min blank page.                                                                                                                           |
| Live deployments page                                         | `/api/vm-deployments?days=1`, logs endpoints                                                 | vm-deployments 500 @42s; logs caches (B9) fine                                                                                                                        | **DECIDED**: covered by the new `/api/vm-deployments` SWR snapshot; B9 logs cache already correct, untouched.                                                                                                                                                                                                            | **DECIDED**: keep LiveDeployments 30s / logs 10s cadence (matches real data change-rate); add visibility-paused polling.                                                                                                 |
| **Data-status tab (REAL path = `/api/data-status/manifest`)** | `/api/data-status/manifest` (IS/MTDS/MDPS), drilldown, downloads                             | **⚑ THE OOM: IS full-hist 90s/18GB · MTDS full 81GB · MDPS 3mo 56GB — all uncached hot (index cached, cell-grid NOT); default range = full history → 1 click = kill** | **RE-DECIDED 2026-07-18 (operator): SCHEDULE** the full cell-grid bound/stream/precompute re-architecture → now tracked in `data_status_cell_grid_rearchitecture_2026_07_18.md` (was DEFERRED per the 2026-07-13 Slack ruling). The near-term OOM guard + 90-day default stay the live mitigation until that plan lands. | **DECIDED**: change the UI's default initial range from full-history (2018-01-01) to a bounded recent window (90 days); full history stays reachable via an explicit "Load full history" action, not the silent default. |
| Ops / costs (billing)                                         | `/api/costs/{summary,breakdown,timeseries}`                                                  | breakdown **55s** cold + **+1.9GB RSS** (loads full cost-record set); distant #2 memory consumer; uncached-cold                                                       | **DECIDED (§4b, operator-confirmed 2026-07-14)**: DuckDB-over-GCS-parquet-snapshot (Option B) — see § 4b in full.                                                                                                                                                                                                        | **DECIDED**: no polling-cadence change needed (billing data is daily-lagged by design).                                                                                                                                  |
| Repo CI / coverage / escalations                              | `/api/repo-ci/*`, `/api/repos/gh-rate-limit`                                                 | overview warms 13.3→2.3s across repeats (per-worker copies); escalations 0.5s                                                                                         | **DECIDED**: WORKERS=2 halves the per-worker-copy fragmentation driving this; no separate fix needed.                                                                                                                                                                                                                    | **DECIDED**: keep the existing 60s cadence, already conservative and appropriate.                                                                                                                                        |
| Kill-switch tab                                               | kill-switch status APIs                                                                      | 5s poll                                                                                                                                                               | **DECIDED**: no change — already hits fast single-scalar (B17-style) caches.                                                                                                                                                                                                                                             | **DECIDED**: keep 5s poll, and explicitly EXEMPT from visibility-pausing — kill-switch state is safety-critical and must keep reflecting current status even in a backgrounded tab.                                      |
| Launch consoles / readiness                                   | `/api/services/*`, `/api/deployments/validate*`                                              | B9/B10 — not yet measured (add during walkthrough)                                                                                                                    | **DECIDED**: no change — B9/B10 are already the correct bounded pattern; not identified as a problem surface.                                                                                                                                                                                                            | **DECIDED**: no change.                                                                                                                                                                                                  |

Cross-cutting decisions — **SETTLED 2026-07-14** (operator directed proceeding without a live click-through session;
decisions below are grounded in the already-measured evidence in § 2.5/2.7/2.8 plus the Phase B implementation landing
in the same pass — see § 6 Progress log for shipped-evidence SHAs):

- **D1 — worker count**: **DECIDED = `WORKERS=2`** (operator-confirmed 2026-07-14, applied via the cloudbuild deploy
  step so it survives redeploys — not a manual live `gcloud` mutation).
- **D2 — memory limit**: **DECIDED = keep 4GiB** (per § 3 analysis — achievable once cache bounding + the OOM guard
  land; no evidence 8GiB is needed).
- **D3 — shared cache tier**: **DECIDED = none/per-instance-only as the general default** (Redis stays parked). The ONE
  exception is the now-established "expensive-source → periodic GCS parquet/JSON snapshot → cheap local read" pattern
  (data-status rollup blobs; the costs DuckDB/parquet snapshot) — that's the template for any FUTURE
  cross-instance-sharing need, not a live shared cache tier.
- **D4 — background sync topology**: **DECIDED = single loop per instance** (leader-elected worker, not one loop per
  worker) **+ idle-skip when `deployments.prod/` is empty** (it is today).
- **D5 — GCS/Athena cost budget**: **DECIDED** — `/api/vm-deployments` gets its own 45s SWR snapshot (matching the
  proven inventory/umbrella pattern) — turns 94s → instant-after-first; Athena/BQ cost for `/ops/costs` is now bounded
  to ~2 scans/day via the cost-snapshot worker regardless of UI traffic, independent of how many tabs are open.
- **D6 — observability**: **DECIDED** = Cloud Monitoring alert on memory utilization &gt;85% sustained 5 min for
  `uts-shared-deployment-api`, wired to the existing alert notification channel (see Phase C todo for the debug
  cache-stats endpoint feeding it).

## 4b. Costs tab (`/ops/costs`) — deep-dive + architecture decision (2026-07-14)

Operator focus item (deployments = operator is migrating the resource column to Firestore/DynamoDB; health = do LAST
since it fans in the others). Costs picked as the first backend perf fix.

**Measured root cause (live, GCP billing export
`central-element-323112.billing_export.gcp_billing_export_resource_v1_…`, 30-day window):**

- The BQ/Athena queries return **maximally-granular facts** —
  `GROUP BY day, service, resource_id, region, sku, usage_unit, zone` (`queries.py:91`) — then ALL of
  summary/breakdown/timeseries/per-resource re-aggregate them **in Python** (`service.py`), holding the whole set as
  `CostRecord` objects in `CostWindowCache` (1h TTL, **uncapped**).
- **Row counts (measured via `bq`):** full-grain = **98,542 rows**; drop `resource_id` → **3,236 rows** (**30×**
  smaller). Cardinality driver = **16,900 distinct resources** (NOT sku — only 120). So grouping by `service` fetches
  all 98,542 per-resource rows and throws the resource detail away.
- **Only 2 of 8 views need resource granularity** — by-resource breakdown + `per_resource_daily` (the inventory cost
  column, which the operator is already moving to Firestore). The other 6 (summary, timeseries, by-service, by-region,
  by-day, by-sku, by-zone, by-label) aggregate to low-cardinality keys the 3,236-row coarse window fully serves.
- **AWS/GitHub currently return nothing** — health tiles report "1 cloud"; today's +1.9 GB is GCP-only. (AWS Athena path
  not showing data = a SEPARATE bug to file, not part of this perf fix.)

**Two options considered (operator raised the DuckDB dimension):**

- **Option A — coarse-window BQ (Python aggregation kept):** add a coarse query (no `resource_id`) for the 6
  non-resource views; fetch the fine per-resource window only on demand; bound the cache. Small, same-day, low-risk.
  But: still scans BQ/Athena per cache-miss (Athena $ scales with traffic), still materializes rows as Python objects,
  still 10–55s cold on miss, each dimension hand-coded (no ad-hoc queries).
- **Option B — DuckDB over a periodic GCS parquet snapshot (RECOMMENDED):** a background worker (every ~12h, mirroring
  the existing `deployment_api/scripts/data_status_rollup_worker.py` pattern) scans BQ/Athena ONCE and writes a
  full-resource-grain **parquet to GCS**; each API instance downloads that small parquet on startup + every 12h and
  queries it with **DuckDB** (already a blessed workspace dep — used in
  `unified-trading-library/manifest_consolidator.py`) via arbitrary SQL. **One snapshot serves every view** (summary =
  group by cloud, breakdown = group by any dim, timeseries = group by day, by-resource = group by resource, prior-period
  = date filter).

**Why B is better (and chosen direction — pending operator confirm):**

| Axis           | A (coarse BQ)                                | B (DuckDB / GCS snapshot)                                                          |
| -------------- | -------------------------------------------- | ---------------------------------------------------------------------------------- |
| BQ/Athena cost | per cache-miss (scales with traffic)         | **exactly 2 scans/day** regardless of traffic — bounded                            |
| Memory         | 3.2K rows Py objects (98K for resource view) | DuckDB columnar → returns only small result; **never materializes rows in Python** |
| Latency        | 10–55s cold on miss                          | **ms** for any group-by (few-MB local parquet)                                     |
| Flexibility    | each dimension hand-coded                    | **arbitrary SQL** — any group-by / window / join                                   |
| Resilience     | breaks if BQ/Athena down                     | serves last snapshot                                                               |
| Freshness      | fresh per request                            | ≤12h stale — fine (billing is daily-lagged)                                        |

- **Caveat (shapes the design):** Cloud Run is stateless + autoscaled → the snapshot MUST live in **GCS** (not
  per-instance local disk). Instances download the small parquet on startup; first load on a fresh/scaled instance is a
  few-MB GCS read, **not** a BQ scan → no cold-start penalty. Exactly the data-status rollup shape, but parquet+DuckDB
  for query flexibility instead of a fixed precomputed JSON.
- **Reuse de-risks it:** both building blocks already exist in-repo — DuckDB (UTL `manifest_consolidator`) + the
  worker→GCS-snapshot pattern (`data_status_rollup_worker.py`). This also establishes the reusable "expensive-source →
  periodic GCS parquet → DuckDB serve" shape that the **data-status compute fix can reuse** later.
- **Phasing:** go straight to B. Only add a MINIMAL safety valve now if `/ops/costs` hurts before B ships — bound
  `CostWindowCache` + cap default `days` (do NOT build A's full coarse-window refactor; it's thrown away under B).

**⚑ SETTLED billing decisions (operator-confirmed 2026-07-14) — billing design FINALISED:**

Measured sizing (live `bq`, so the design is grounded, not estimated):

- Raw BQ billing export table ≈ **2 GB** (all un-aggregated line items, all history + nested fields) — **we never
  download this.** The snapshot is the AGGREGATED query result (`GROUP BY day, service, resource, region, sku, zone`).
- A 180-day aggregated query **scans only ~271 MB** server-side (date filter + column pruning) and **returns ~167.6 K
  rows**. Per refresh ≈ **$0.002** BQ on-demand; 2×/day = rounding-error cost.
- **90-day and 180-day both return ~167,641 rows** → the export effectively holds only ~90 days, so "snapshot
  everything" IS the full history and is still just ~168 K rows ≈ **~20–40 MB parquet** (GCP).
- Reconciles the 1.9 GB: today's cache materialises EACH day-window (7/30/90 × current+prior = up to 6 overlapping
  windows) as fat `CostRecord` Python objects (~1–3 KB/row). 6 × 168 K × ~2 KB ≈ ~2 GB. DuckDB replaces all of them with
  ONE ~30 MB snapshot that every window queries by date-filter on the fly → tens-of-MB, no Python materialisation.

Decisions locked:

1. **Snapshot scope** — snapshot the **entire available table** (only ~90 days exist; ~168 K aggregated rows / ~30 MB).
   No retention-window tuning needed.
2. **Refresh cadence** — **every 12 h** (billing lags 2 days per `_PROVISIONAL_TRAILING_DAYS`; only the "today so far"
   figure is ≤12 h stale — acceptable).
3. **Layout** — **per-cloud parquet** (`gcp.parquet` / `aws.parquet` / `github.parquet`) in `gs://…-cost-snapshots/` —
   mirrors the current `_safe` per-cloud isolation; AWS failing never blanks GCP; each refreshes independently.
4. **Read path** — each API instance **downloads the per-cloud parquet to local `/tmp` on startup + each 12 h refresh
   and queries via DuckDB locally** (fastest for repeat queries; ~30 MB in Cloud Run's in-memory `/tmp` is trivial).
   Cold/scaled instance's first load = a ~30 MB GCS read, not a BQ scan → no cold-start penalty.

Build notes (not decisions — the implementation shape + risks):

- **GCP slice ships independently; AWS slice is gated** on the deployed-AWS gap (AWS shows LOCALLY but not on the
  deployed service — **NOT a code bug** per operator: either the Cloud Run service account lacks AWS/Athena perms, or
  the live revision `00152` (2026-07-12) is stale and newer code hasn't shipped). The snapshot worker needs the same AWS
  access, so resolve that before `aws.parquet` populates.
- **The bulk of the work + main risk = porting the in-Python aggregation to DuckDB SQL** view-by-view (cent-exact
  reconciliation, native-GBP tally, top-N "Other" residual rollup, "Unattributed (no resource id)" row, spot/on-demand
  `purchase_option` rollup, machine_type/memory detail) — each verified to match the current endpoint output.
- **Topology is NOT fixed** (operator 2026-07-14): the 20-instance / 4-worker / 4 GB choices predate this and can all be
  changed — so billing is designed to fit comfortably regardless, and D1/D2 (workers/RAM) stay open for the fleet-wide
  right-sizing. **Redis parked** (§ D3) — GCS-snapshot already gives cross-instance sharing for the big datasets.

**Codex SSOT to update on landing:** `/codex/05-infrastructure/billing-cost-observability.md`.

## 5. Todos

Phase A — walkthrough + decisions (operator-joint; blocks Phase B):

- [x] ✅ [OPERATOR] P3. § 4 walkthrough session — every Decision cell filled + D1–D6 settled (§ 4, 2026-07-14). **Method
      note**: operator explicitly directed proceeding WITHOUT a live page-by-page click-through session — decisions were
      made from the already-measured § 2.5/2.7/2.8 evidence plus the Phase B implementation landing in the same pass,
      not fresh live observation. All caching decisions resolve to "covered by the Phase B implementation, no further
      backend change"; UX/polling decisions (visibility-paused polling everywhere except the safety-critical kill-switch
      tab; 90-day default data-status range instead of full-history; loading skeletons on the two
      previously-blank-while-loading pages) implemented in deployment-ui — see § 6 Progress log for shipped-evidence
      SHAs. **(was: P0 blocking-all-of-Phase-B — REPRIORITIZED 2026-07-14 per the operator's own 2026-07-13 Slack ruling
      in this doc's Progress Log L445-447: "general responsiveness → walkthrough" = lowest priority; verify-rerun
      finding 53. Phase B no longer gated on this.)**
- [x] ✅ [INFRA] P1. Rollup-svc cost-stop — elevated to near-term per the operator's 2026-07-13 Slack ruling (Progress
      Log L445-447); was narrative-only, promoted to a tracked todo by verify-rerun finding 53. **Resolved via
      per-service child-process isolation instead of pausing the cron** (pausing would have kept producing ZERO value;
      isolation makes 11 of 12 services succeed instead) — `deployment-api@8d260ad` + `deployment-service@08d29b0`
      (container 16Gi/4CPU→32Gi/8CPU, cron 10min→20min, attempt_deadline 600s→900s). Evidence:
      `gs://central-element-323112-data-status-rollups/` now contains a fresh
      `market-data-processing-service/full.json.gz` (written 2026-07-14T00:15:39Z) for the first time ever; full
      root-cause + fix detail in the Progress Log entry above.
- [x] ✅ [BACKEND] P1. Add the deployment-api fail-fast/refuse-large OOM-guard — elevated to near-term per the same
      operator ruling; promoted from narrative to tracked todo (finding 53). **Resolved** — two-layer guard on the
      manifest live-build fallback: (1) pre-flight byte-budget estimator (768MiB default ceiling, calibrated off the
      measured 18/81/56GB anchors) refuses or serves-stale before attempting a build that would blow the container; (2)
      defense-in-depth — any build that passes the estimate still runs inside a `resource.setrlimit(RLIMIT_AS,...)`
      spawned child (mirrors the proven `8d260ad` pattern), so an underestimate raises a catchable error instead of
      OOM-killing the parent worker. `deployment-api@030779f`. Does NOT touch the already-fine rollup-blob fast path;
      does NOT attempt the full cell-grid re-architecture (stays deliberately deferred per the operator's 2026-07-13
      ruling).
- [x] ✅ [BACKEND] P0. Benchmark session (2026-07-13, agent-run per operator direction) — deployed-API curl suite (39
      reqs, cold/warm/503 sequences), Playwright page-level timings (6 pages), local 4-worker replica with
      phase-attributed RSS monitoring incl. the turbo data-status path. Results = § 2.7; § 4 "Today" column filled with
      measured numbers; § 3 verdict revised (MTDS turbo = +11GB transient/+3.5GB permanent from ONE query). Evidence —
      raw CSV/JSON in session scratchpad; summaries in § 2.7 are the findings of record.

Phase B — implementation (gated on Phase A decisions; each lands via quickmerge with QG-green tree):

- [x] ✅ [INFRA] P0. Apply D1/D2 — set `WORKERS=<decided>` env on `uts-shared-deployment-api` (gcloud run services
      update; also encode in cloudbuild deploy step so it survives redeploys). **Resolved** — `WORKERS=2` encoded in the
      cloudbuild deploy step's `--update-env-vars` (not a manual live mutation — lands on next deploy, survives
      redeploys) `deployment-api@ab07227`. D2 = keep 4GiB (no change made, per § 3). Memory-trend-after-24h evidence NOT
      captured (24h soak explicitly dropped from this session's scope per operator instruction).
- [x] ✅ [BACKEND] P0. One bounded cache primitive (generalize the B9 pattern already in `routes/deployment_caching.py`,
      or `cachetools.TTLCache` — already a transitive dep): max-entries + TTL + evict-on-set + a single periodic sweeper
      task; expose per-cache stats (entries, est. bytes) on one debug endpoint (feeds D6). **Resolved** —
      `deployment_api/utils/bounded_cache.py` (`cachetools.TTLCache`-backed, named registry, single periodic sweeper
      wired into `lifespan.py`, `GET /api/debug/cache-stats`) `deployment-api@0702aa3`.
- [x] ✅ [BACKEND] P0. B1 `data_status_cache` — cap entries (LRU ~8), store **gzipped JSON bytes** not live dicts, drop
      `freshness_date` from the key (or normalize it) so keys actually repeat, kill the per-hit `deepcopy` (serve
      pre-truncated variant computed once at store time). **Resolved** `deployment-api@0702aa3` — same commit as the
      primitive above.
- [x] ✅ [BACKEND] P1. B3 drilldown `_core.py` — bound with the primitive (day-keyed growth ends); B5 `log_analysis` —
      bound per-deployment entries; B6 `_repo_ci_github` `_response_cache` — bound + skip caching one-time per-SHA URLs;
      B4b `_last_alerted_health` — prune names absent from the current census; delete dead B16. **Resolved**
      `deployment-api@0702aa3` — all five in the same cache-hygiene commit.
- [x] ✅ [BACKEND] P1. `UnifiedCache.in_memory` — bound it; decide GCSCache fate per D3 (delete or fix whole-blob
      rewrite before first real use); B7 `lru_cache` 8192 → ~512; B2 turbo cache — add byte ceiling next to the
      100-entry cap. **Resolved** `deployment-api@0702aa3` — D3 resolved as DELETE (confirmed unused in prod,
      grep-verified no other callers) rather than fix the flawed whole-blob-rewrite path.
- [x] ✅ [BACKEND] P1. `/api/vm-deployments` — add the 45s SWR snapshot pattern per D5 (single-flight, background
      refresh), reusing `_load_inventory`'s proven shape. Target — instant-after-first-load instead of 94s. **Resolved**
      `deployment-api@3f1fc66`, 9 unit tests incl. single-flight-refresh and cold-path-collapses-concurrent-first-polls.
- [x] ✅ [BACKEND] P1. **Costs — DuckDB-over-GCS snapshot (§4b Option B, DESIGN FINALISED, operator-confirmed
      2026-07-14).** **Resolved across two increments, by two operators concurrently working this same plan** (flagged
      to the operator mid-session — see Progress log): Increment 1 (`deployment-api@d7c0356`, this session) — the
      `CostSnapshotStore`/`cost_snapshot_worker.py` GCS-parquet-snapshot infra + `_load_window` snapshot-first fallback.
      Increment 2, the DuckDB SQL aggregation port (cent-exact reconciliation / native-GBP tally / top-N "Other" /
      "Unattributed" row / purchase_option rollup), was shipped **independently by a concurrent operator session** —
      `deployment-api@d82405c` + `6ca64d8` + `7b60273` — landed on the shared branch mid-session; this session's own
      costs agent detected the overlap and did not duplicate it. **GCP slice ships; AWS slice** — see the AWS-gap todo
      directly below (this session's addition, not pre-existing). Codex:
      `/codex/05-infrastructure/billing-cost-observability.md` (audit still pending — see Phase C).
- [x] ✅ [BACKEND] P2. **Costs safety valve (only if /ops/costs hurts before DuckDB ships)** — superseded: DuckDB
      shipped directly (see above), so the safety-valve refactor was never needed and was NOT built, matching the plan's
      own phasing note that it would be "thrown away under Option B."
- [x] ✅ [INFRA] P2. **Deployed AWS cost data missing — perms or stale deploy (NOT a code bug; AWS works locally).**
      **Root-caused precisely** (not perms-on-an-existing-role, not a stale deploy): `AWSAnalyticsClient._boto3_client`
      (unified-trading-library) used a bare `boto3.Session()` — no credential source exists for that in a GCP Cloud Run
      container at all (verified live: zero AWS env vars on the deployed revision). **Fixed** by mirroring the
      already-proven CodeBuild-reader keyless GCP→AWS WIF pattern (`_code_builds_aws.py:_assume_codebuild_reader_role`)
      for Athena — `deployment_api/services/cost_observability/aws_wif.py`, config field `aws_athena_reader_role_arn` /
      env `AWS_ATHENA_READER_ROLE_ARN` (`deployment-api@d8add54`). **New AWS IAM role provisioned**
      `arn:aws:iam::427895769566:role/gcp-cloudrun-athena-cost-reader` (read-only, scoped to exactly the CUR data +
      Athena workgroup + results bucket, trusting the same `unified-trading-sa` GCP SA the CodeBuild reader already
      trusts) — this IS a real AWS-side IAM change, done directly (not deferred) per explicit operator instruction this
      session. ARN wired into the Cloud Run deploy env (`deployment-api@fc53899`). Will take effect on the next deploy;
      not yet verified against the live deployed revision (that deploy hasn't happened as of this writing).
- [x] ✅ [INFRA] P2. Background sync per D4 — single loop per instance + idle-skip on empty `deployments.prod/`;
      quantifies straight into GCS op-cost reduction. **Resolved** — leader-election via `worker_identity.py`
      (`deployment-api@6d5a225`) + idle-skip on `sync_service.py` (`deployment-api@650e418`). Distinct from, and layered
      on top of, a separate `reap_stale` tick fix a concurrent operator session shipped this same day
      (`f83ac67`/`3fc1a06`) — the two do not overlap.
- [x] ✅ [UI] P2. deployment-ui polling adjustments decided in § 4 (per-tab intervals, visibility-paused polling if
      decided) — with `pw:L2 ✓` + cited regression spec per UI gate. **Resolved** — visibility-paused polling on every
      interval poll except the safety-critical kill-switch tab (`deployment-ui@3c08c5f`), 90-day default data-status
      range instead of full-history (`deployment-ui@18ba017`), loading skeletons on the two
      previously-blank-while-loading pages (`deployment-ui@0ff25b5`). Each shipped with a green quality-gates.sh run + a
      real Playwright spec (`pw:L2 ✓`); independently re-verified (SAFE_TO_TRUST) by a second agent that re-ran the
      specs itself rather than trusting the implementer's report.

Phase C — verification + guardrails:

- [x] [BACKEND] P1. ✅ **CLOSED (operator 2026-07-18: no 24h wait needed).** Soak signal GREEN — 0 OOM in 24h at rev
      `00205-n42` (16Gi/4CPU), stable across ~7 revisions since the 16Gi deploy. Runtime verification — 24h soak after
      Phase B: memory p99 flat ≤50% at WORKERS=decided, zero OOM kills in logs, cockpit endpoints p95 &lt; 2s warm.
      Evidence — monitoring queries + log counts cited here. **PARTIAL SOAK SIGNAL 2026-07-18 (autonomous):**
      deployment-api is live at **rev `00205-n42` @ 16Gi/4CPU**, and a
      `gcloud logging read … "Memory limit"/"exceeded" --freshness=24h` returns **only the original 2026-07-17T17:21:30
      OOM (the 8Gi pre-fix F2 incident) — ZERO OOM across the ~7 revisions since the 16Gi deploy**. So the container is
      stable in prod (no OOM kills), which is the soak's primary red-flag check. The FULL 24h-continuous memory-p99 +
      warm-p95 soak still wants a dedicated monitoring window and is wall-clock-bound (a 24h wait) — left open for an
      attended pickup. Operator dropped it from the original scope (2026-07-14); recorded here as GREEN-so-far, not
      falsely closed.
- [x] ✅ [INFRA] P2. D6 alerting — Cloud Monitoring alert on memory utilization &gt;85% (5 min) for
      uts-shared-deployment-api; wire to existing alerting channel. **Resolved** —
      `google_monitoring_alert_policy.deployment_api_memory_high` (`>85%` sustained 300s,
      `run.googleapis.com/container/memory/utilizations`), reusing the existing `monitoring_deadman_email` channel
      already wired to this service's uptime alert (not a new channel) `deployment-service@c6c6c8f`.
- [ ] [BACKEND] P2. Post-phase codex audit — update `/codex/05-infrastructure/deployment-observability.md` (cache
      architecture + stats endpoint + alert) and `/codex/04-architecture/runtime-deployment-topology.md` if worker
      topology changed; SUPERSEDED-banner any invalidated statements.

## 6. Progress log

- 2026-07-13 (slot-1, interactive): Incident measured live (§ 1); topology + cache inventory verified (§ 2, incl.
  sub-agent B1–B18 report); latency table measured from request logs (§ 2.5); fit-in-4GB analysis written (§ 3); plan
  authored. Immediate-relief option (`WORKERS=2` env-only change) surfaced to operator — **not applied**; operator
  directed plan-first + joint walkthrough before any change.
- 2026-07-13 (slot-1, later same session): Benchmark session executed (operator delegated measurement to agent):
  deployed curl suite + Playwright 6-page run + local 4-worker memory replica. § 2.7 added; § 3 REVISED — headline
  discovery: **one MTDS `/api/data-status/turbo` query = +11GB transient / +3.5GB permanent RSS** (instant OOM at 4GiB
  under current code, any worker count) — the data-status load path re-engineering is now the load-bearing fix, worker
  count alone is insufficient. Cockpit deployments tab currently renders with ZERO data (all 5 calls 503/500). Local
  benchmark backend + monitors stopped and verified stopped (port 8081 closed). Discovery also logged:
  `deployment-dashboard` Cloud Run service does NOT serve the SPA routes (/cockpit 404) — the API service serves the UI
  itself; dashboard service is possibly dead weight (check during walkthrough; potential cost saving).
- 2026-07-13 (slot-1, session 2 — operator-directed full profiling sweep while away): Profiled ALL data-status services
  via the REAL UI path + all 19 pages via real UI (vite→local 4-worker backend), 3 passes each, browser JS heap +
  backend RSS + per-API latency; §2.8 added; §3 verdict re-revised. **Two corrections/upgrades to session 1:** (a) the
  real UI uses `/api/data-status/manifest` (NOT turbo) for IS/MTDS/MDPS, and that path is far worse — **IS 18GB / MTDS
  81GB / MDPS 56GB-for-3-months**, all uncached hot (index cached, cell-grid recomputed every call); this is the true
  OOM root cause (one default-full-range data-status click = kill on any instance size, 64GB included). (b) Page sweep:
  no page except `/ops/costs` (+1.9GB, 55s) is a memory concern; browser heap uniform 32–56MB; the real page problem is
  cold latency on ~7 uncached endpoints (costs 55s, health/overview 19.7s, repo-ci/overview[cicd] 17.9s,
  health/consolidator 13.8s, fleet/orphans 13.6s, deployments/regions 11.1s, epics/plans 10.2s). Full data +
  methodology: session scratchpad `bench2/FINDINGS.md` (harness scripts + raw CSV/JSON retained). Host-safety: a 50GB
  memory guard auto-killed the backend on the MTDS/MDPS spikes; local stack (backend + vite + monitors) torn down and
  verified stopped. **No prod/deploy changes made — all local, per operator.**
- 2026-07-13 (slot-1, session 2 — ROOT-CAUSE CORRECTION after operator challenge "it worked before at full range, so
  something changed last week"): Operator was RIGHT — the 18/81/56GB is a REGRESSED FALLBACK, not the design. Traced the
  real path: the data-status manifest all-AG view is served from a precomputed
  `gs://…-data-status-rollups/{service}/full.json.gz` (cheap, sub-second) written by the
  `uts-prod-data-status-rollup-svc` worker; it only falls through to the live cell-grid build when that blob is
  stale/missing. **Two last-week changes broke it:** (1) the rollup worker (16GiB) is OOMing every cron cycle —
  `Memory limit of 16384 MiB exceeded` 71×/144×/74× on 07-11/12/13 — so MTDS/MDPS blobs stopped being written (GCS now
  has ONLY instruments-service blobs); (2) commit `3847d6f` (2026-07-08) fixed the staleness gate
  (`meta.updated`→`meta.last_modified`) so the API stopped serving the stale blobs and now falls through to the OOM-ing
  live build. Two OOMs of the SAME build (16GiB worker + 4GiB API). §2.8 + §3 corrected with a ⚠️ block; corrected fix
  priority = **bound/stream the cell-grid build (one fix resolves both OOMs) + restore the rollup worker + API
  serve-stale/refuse-large defense-in-depth**, NOT a from-scratch re-architecture and NOT a RAM bump. Full chain + log
  evidence in `bench2/FINDINGS.md` top block. Verified read-only against live GCS + Cloud Logging + Cloud Run configs;
  no changes made.
- 2026-07-13 (operator context — Ikenna via Slack, recalibrates PRIORITY not diagnosis): Ikenna (primary data-pipeline
  owner + the effective sole consumer of the data-status tab) is **NOT using the data-status tab right now and won't for
  a while** — he's reconciling shard issues / smoke-test outputs so they produce data as expected, and blindly reading
  coverage over broken adapters/consolidators isn't useful yet. **Implication:** the big-ticket cell-grid bound/stream
  re-architecture (make the tab fast at full range) drops OFF the critical path — schedule it deliberately, not under
  incident pressure. **What stays urgent (independent of tab usage):** (1) the rollup worker
  `uts-prod-data-status-rollup-svc` is OOM-looping ~144×/day (16GiB×4CPU every 10 min, producing nothing for MTDS/MDPS)
  — ongoing cost + noise regardless of tab use → pause its `*/10` cron or bound its build; (2) a cheap API
  fail-fast/refuse-large (or serve-stale-as-last-resort) guard so a single `/api/data-status/manifest` request can't
  OOM-crash-loop the WHOLE deployment-api (blast radius = cockpit/deployments/costs all go down) — highest
  value-per-effort near-term item. **Unaffected + still worth doing for the surfaces people DO use:** WORKERS=2,
  bounded-cache hygiene, and the 7 slow non-data-status endpoints (§2.8). Priority: data-status COMPUTE fix →
  deferred/scheduled; rollup-worker cost-stop + API OOM-guard → near-term; general responsiveness → walkthrough.
- 2026-07-13/14 (slot-3): Delivered the near-term "rollup-worker cost-stop" item from the entry above — narrowly scoped,
  no changes to deployment-api's live-serving/caching code, so this does NOT touch the § 4 joint-walkthrough gate.
  **Root cause found**: `data_status_rollup_worker.py::run_rollup` processed all 12 `_DEFAULT_SERVICES` (IS, MTDS, MDPS,
  7× features-_, ml-service, strategy-service, execution-service) SEQUENTIALLY IN ONE PROCESS. MTDS (2nd in the list)
  OOM-killed the WHOLE container on every cron tick — so nothing queued after it (10 of the 12 services, including cheap
  ones) had EVER produced a rollup blob; only instruments-service (1st) had ever succeeded. **Fix**
  (`deployment-api@8d260ad`): each service's compute+write now runs in its own `multiprocessing.get_context("spawn")`
  child, capped by `resource.setrlimit(RLIMIT_AS, 24GiB)` (container bumped 16Gi/4CPU → 32Gi/8CPU, verified against a
  throwaway Cloud Run service first) — a too-large service raises a catchable `MemoryError` in its own throwaway child
  instead of OOM-killing the parent/container. Verified the mechanism end-to-end against real Linux containers (not just
  mocks) before shipping: `RLIMIT_AS` cleanly raises `MemoryError` for numpy/pandas allocations, and a real cgroup
  OOM-kill terminates only the offending child while the parent survives. **Verified in production**:
  `market-data-processing-service/full.json.gz` now exists in `gs://…-data-status-rollups/` for the **first time ever**
  — direct proof MTDS's failure no longer blocks MDPS. **Second finding + fix, cadence mismatch**: the dedicated rollup
  service's own request timeout (900s) was longer than both the old 10-min cron cadence and the old 600s scheduler
  `attempt_deadline`; with `maxScale=1` (no concurrent instances), a new tick routinely fired while the previous sweep
  was still running in the background, got rejected 429/`RESOURCE_EXHAUSTED`, and the previous sweep's real progress
  (e.g. MDPS's blob write completing at t+15min) was invisible to the scheduler's own bookkeeping. Fixed
  (`deployment-service@08d29b0`): cron `_/10`→`\*/20`, `attempt_deadline`600s→900s (applied live
  via`gcloud scheduler jobs update`, matching this component's existing "imperatively managed" pattern; `.tf` kept in
  sync as desired-state SSOT). **Scope boundary respected**: MTDS/MDPS's OWN full-2018-today build still exceeds any
  sane per-child memory ceiling ("no RAM tier through 64GB survives it", § 3) — this fix does not and cannot make their
  own rollup blobs succeed; that remains exactly the § 4 walkthrough's job. **Operator asked** (separately, same
  session) whether DuckDB could help the § 3 compute — researched (not implemented): DuckDB is already a trusted,
  precedented pattern in this codebase (`unified-trading-library/manifest_consolidator.py`'s pandas→DuckDB migration,
  plus two one-off dedup/restore scripts in instruments-service and MTDS), but had never been applied to this
  data-status compute path. A 7-agent design workflow produced a concrete technical memo: DuckDB fixes the read/filter
  stage cleanly, but the DOMINANT cost (measured 81GB vs. a raw index that's plausibly low-single-digit-GB) is CPython
  dict-of-dicts overhead + per-category copies + `ProcessPoolExecutor`fan-out duplication
  in`venue_resolution.py`/`mtds.py`/`breakdowns_core.py`— DuckDB only fixes this if the nested Python loops are
  themselves replaced by SQL`GROUP BY` aggregation, which is a real rewrite (SQL sketches, file:line-cited risks, and an
  ordered implementation sequence are written up and available on request) — squarely § 3/Phase-B work, explicitly not
  implemented, offered as input to the walkthrough whenever it's scheduled.
- 2026-07-14 (operator-directed order: costs first, deployments = operator handling via Firestore, health LAST since it
  fans in the others): Root-caused `/ops/costs` (§4b). Measured the GCP billing explosion with live `bq`: 98,542
  full-grain rows vs 3,236 without `resource_id` (30×; 16,900 distinct resources drive it, not the 120 skus); AWS/GitHub
  return nothing ("1 cloud"). Only 2/8 views need resource grain. Operator raised the DuckDB idea → compared Option A
  (coarse-window BQ, Python aggregation) vs **Option B (DuckDB over a 12h GCS parquet snapshot)** and chose B: bounded
  2-scans/day cost, ms latency, no Python row materialization, arbitrary SQL, resilient — reusing two in-repo patterns
  (DuckDB in UTL `manifest_consolidator`; the `data_status_rollup_worker` → GCS-snapshot shape), which also becomes the
  reusable template for the data-status compute fix. §4b + Phase-B todos written; safety-valve + AWS-bug follow-ups
  filed. Not yet implemented — pending operator confirm to build Option B. Health root-caused too
  (`/api/health/overview` = serial fan-in of 6–8 tiles incl. fleet census + cost load, no rollup cache → 9–17s live;
  deferred to LAST per operator); fleet/orphans = uncached full-project Compute API enumeration shared by 4+ endpoints
  (shared SWR cache fix identified). No code changes yet — all diagnosis; `bq` diagnostic queries were read-only.
- 2026-07-14 (billing design FINALISED — operator-confirmed): Grounded the DuckDB snapshot sizing with live `bq` (raw
  table ~2 GB but a 180-day aggregated query scans only ~271 MB and returns ~167.6 K rows; 90d≈180d rows → export holds
  only ~90 days → full history ≈ ~30 MB parquet; the 1.9 GB is 6 overlapping day-windows materialised as Python objects,
  which DuckDB collapses to one date-filtered snapshot). Locked the 4 decisions (§4b): snapshot full history / refresh
  12h / per-cloud parquet / download-to-`/tmp`+DuckDB. Reworded the AWS item from "bug" → deployed AWS gap is
  perms-or-stale-deploy (works locally, per operator). Topology (20×4×4GB) declared NOT fixed → billing designed to fit
  regardless; Redis parked. **Billing page is DONE at the plan level; implementation starts once the whole plan is
  finalised** (operator: finalise plan first). Still no code changes.
- 2026-07-14 (bug-investigation agent, live-triage of operator report "unknown error opening the data-status
  drill-down"): **Fresh recurrence of THIS incident, not a new bug** — confirms Phase B (§5) is still unshipped and the
  root cause is still live. Live evidence: `uts-shared-deployment-api` (now revision `00163-44l`, still 4Gi/2CPU per
  `gcloud run services describe`) logged `Memory limit of 4096 MiB exceeded with 4098–4372 MiB used` repeatedly
  04:01Z-11:05Z on 2026-07-14, with a dense burst 11:04:06Z-11:05:52Z. Cloud Logging request records show
  `referer = …/service/market-tick-data-service/data-status` firing a parallel burst of
  `GET /api/data-status/drilldown/market-tick-data-service/{cefi,defi,sports,tradfi,prediction}` +
  `/api/data-status/coverage-summary` + `/api/data-status/bucket-counts` + `/api/capabilities/service-asset-groups/*`,
  ALL with the default full-history window `start_date=2018-01-01&end_date=2026-07-13` — exactly the §2.8 "default range
  = full history from 2018-01-01 → 1 click = kill" pattern. Every one of those calls came back `503` after 15-18s
  (container OOM-killed mid-request; matches the documented malformed-response-or-connection-error signature). This is
  what the operator experienced as "unknown error" in the drill-down modal — the browser's fetch simply failed once the
  4GiB container was reaped. **The drill-down endpoint itself
  (`deployment_api/routes/data_status/_deploy_turbo.py::get_data_status_drilldown`,
  `GET /drilldown/{service}/{asset_group}`) is not independently broken** — it is collateral damage of the same
  MTDS/manifest cell-grid OOM root-caused in §2.8/§3 (the drilldown burst and the manifest/coverage/bucket-counts calls
  share the same worker pool and die together). No new code investigated or written per the findings-triage rule (fits
  this existing locked P0 plan; the fix is architectural and gated on Phase A/§4b decisions already in flight here — not
  a ≤30-min patch). Reinforces the urgency of the still-open
  `[BACKEND] P1. Add the deployment-api fail-fast/ refuse-large OOM-guard` todo in §5 Phase A: today's burst shows the
  blast radius is NOT limited to data-status — the same OOM window took down unrelated cockpit/repo-ci calls in-flight,
  so an operator opening ONLY the data-status drill-down can currently crash-loop the whole shared backend for every
  other open tab. By 11:08Z the crash-loop had subsided on its own (autoscaler cycled a fresh instance; `/api/health`
  and `/api/repo-ci/*` were 200 again) — no operator/agent action taken, no deploy performed. Read-only
  `gcloud logging read` / `gcloud run services describe` evidence only; no prod changes made.
- 2026-07-14 (slot-3, operator directive: "action this plan in full"): Drove Phase A/B/C to near-completion in one
  session. **§4 walkthrough** settled without a live click-through (operator-directed) — every Decision cell + D1–D6
  filled from existing measured evidence + the Phase B landing in the same pass (§4 in place, commit
  `unified-trading-pm@dfbeb788d`). **AWS billing gap** root-caused precisely (not perms-on-an-existing-role, not a stale
  deploy — `AWSAnalyticsClient` had zero AWS credential source in the GCP Cloud Run container at all) and fixed with a
  WIF credential path mirroring the proven CodeBuild-reader pattern; **a new AWS IAM role was provisioned live**
  (`arn:aws:iam::427895769566:role/gcp-cloudrun-athena-cost-reader`, read-only, scoped to exactly the CUR data + Athena
  workgroup + results bucket) per explicit operator instruction to do this directly rather than defer it.
  **Cross-operator collision discovered mid-session**: a different operator (Harsh, slot-1/slot-5) was concurrently
  shipping overlapping work on this same plan into the same shared `live-defi-rollout` branch — he landed the costs
  DuckDB Increment 2 migration and a `reap_stale` background-sync fix independently. Flagged to the operator in-chat;
  quickmerge's own rebase-autostash reconciliation handled the concurrent pushes with zero conflicts, and this session's
  own costs agent detected the overlap and built only the non-duplicate AWS WIF piece instead of redoing Increment 2.
  **Serious incident + recovery, mid-session**: three implementation agents (OOM guard, cache hygiene, vm-deployments
  SWR) plus part of the costs agent's work (AWS WIF) each finished substantial, tested code but got cut off before their
  `quality-gates.sh` run completed, so per the commit-only-from-green-tree rule none of them committed anything —
  leaving ~34 files of real work sitting uncommitted in the shared `.tabs/3/deployment-api` clone for the better part of
  two hours. This workspace runs an automated 5-minute cron sweep (`slot-cron-ff-pull.sh`) that force-cleans
  long-uncommitted WIP in slot clones; it silently destroyed all of it (confirmed via `git fsck` — no dangling commits,
  no unreachable blobs; the content was never `git add`-ed, so git had nothing to recover). **Recovered in full**: each
  losing agent's own transcript records every Write/Edit tool call it made, so all 34 files were mechanically
  reconstructed by replaying those tool calls, in the correct cross-agent chronological order, against the current base
  — zero mismatches on replay (every `old_string` matched exactly where expected), which is itself strong evidence the
  reconstruction is byte-correct. Two real, previously-masked test failures surfaced on the first full QG run against
  the recovered tree (both genuine — `test_lifespan.py`'s mocks didn't yet account for the new `start_sweeper()` call,
  and `test_venue_engages_any_row_filter_gate_and_bypasses_rollup` was mocking a call path the OOM guard's subprocess
  wiring had moved) — both fixed properly, not papered over; a third, `test_route_deployments_ inventory*.py`'s
  AWS-census flake, was confirmed pre-existing/parallel-execution-flaky (passes reliably in isolation, a DIFFERENT test
  in the same family fails on each repeated full run) via 3 independent full-QG runs, matching what 3 other agents this
  session independently flagged as unrelated. **Shipped** (all `deployment-api`, chronological): `030779f` (OOM guard:
  pre-flight byte-budget refusal + `RLIMIT_AS`-bounded child, mirrors `8d260ad`'s proven pattern), `0702aa3` (cache
  hygiene: `bounded_cache.py` primitive + sweeper + debug endpoint, all of B1/B3/B4b/B5/B6/B16/
  UnifiedCache/GCSCache/B7/B2), `3f1fc66` (vm-deployments 45s SWR, 9 tests), `d8add54` (AWS WIF credential code path),
  `fc53899` (wires the new role ARN into the cloudbuild deploy env, inert until this — plus the earlier `ab07227`
  WORKERS=2, `6d5a225`+`650e418` background-sync D4). Also shipped: `deployment-service@c6c6c8f` (D6 memory alert
  Terraform) and `deployment-ui@3c08c5f`/`18ba017`/`0ff25b5` (the 3 §4 UX/polling decisions, independently re-verified
  SAFE_TO_TRUST by a second agent that re-ran the Playwright specs itself). **The D6 alert Terraform was additionally
  `tofu apply`-ed live** (targeted apply, plan showed exactly 1-to-add/0-to-change/0-to-destroy) — this repo's
  `terraform/gcp/` has no auto-apply pipeline, so shipping the `.tf` alone would NOT have made the alert live; confirmed
  via `tofu state show` post-apply (`projects/central-element-323112/alertPolicies/10817162460883602732`, enabled).
  Codex updated: `/codex/05-infrastructure/deployment-observability.md` (new alert + pointer to this plan);
  `/codex/04-architecture/runtime-deployment-topology.md` checked — no stale worker-count statement found, no edit
  needed. **Explicitly NOT done, by operator instruction**: the Phase C 24h soak — Phase B has landed on
  `live-defi-rollout` but has not yet promoted to `main`/redeployed, so there is no live window to soak yet regardless;
  left open for whoever next has 24h of live Phase-B runtime to point monitoring queries at. **Not independently
  re-verified** (unlike the OOM guard/costs/UI pieces, which got a dedicated adversarial-verify pass): the cache-hygiene
  and vm-deployments-SWR pieces, and the recovery-reconstruction itself beyond the QG-green confirmation — a follow-up
  review pass would be reasonable before treating this as fully closed.
- 2026-07-14 (slot-3, `/autonomous` continuation — driving the CI/promotion pipeline to a genuinely green end-state per
  AUTONOMOUS_AGENT_RULES.md rule 4 "reconcile everything down here, now"): found and fixed a real blocker unrelated to
  this plan's own code but sitting in its path: `deployment-api` PR #284 (`main-backmerge-to-ldr`, auto-opened, "main
  has commit(s) that conflict with LDR") was CONFLICTING, blocking the LDR→main promote PR from ever landing. Root
  cause: `main` had received a manual operator-approved merge (PR #283, a provenance-gate hotfix for the reap_stale fix)
  that diverged from LDR's independent evolution of the same subsystems (costs DuckDB Increment 2, the cost-snapshot
  bucket-prefix refactor, the lending-indices bucket-retirement follow-up). Resolved the merge locally
  (`git merge origin/main`) — 8 real conflicts (`cloudbuild.yaml`, `cost_snapshot_worker.py`,
  `cost_observability/ {cache,service,snapshot}.py`, `data_status/defi.py`, 2 test files) — investigated each
  individually (diffed main's content against the Increment-1 baseline / checked live call-sites in the already-resolved
  files) before resolving; every single one confirmed LDR's side was a strict superset or a later, documented
  correction, never a case of discarding genuine main-only work. Quality-gates.sh green on the merged tree before push.
  **Recovery incident #2, same root cause as the one earlier in this session**: the first attempt at this merge commit
  silently failed twice (conventional-commit hook rejected the non-prefixed message; my own `tail -10` truncation hid
  the rejection both times) and the resolved-but-uncommitted merge state sat exposed just long enough that it also
  risked the same automated-cron-sweep fate as before — caught it via `git status` showing a stale `MERGE_HEAD` still
  present, re-committed immediately with a conventional-commit-formatted message, verified via `git log -1` before doing
  anything else, and pushed within the same few seconds. Landed as `deployment-api@bd83d87`. PR #284 auto-merged/closed
  on push; the stale promote PR #285 (pinned to an older LDR tip) was superseded by a fresh `#286` once
  `ldr-to-main-promote-fleet` was manually re-triggered (`gh workflow run`, rather than waiting up to 15min for its own
  cron) — `#286` went from CONFLICTING to MERGEABLE immediately. `deployment-service` promote PR #393 and
  `deployment-ui` (no open PRs) were both already clean. Two historical `quality-gates-v2` FAILUREs on deployment-api
  (11:30Z, 13:33Z) and one on deployment-service (14:35Z) were confirmed superseded by later green runs on the same
  branch — not open problems.
