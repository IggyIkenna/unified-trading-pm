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

| Page / surface                                                | Backing APIs                                                                                 | Today (MEASURED 2026-07-13, § 2.7)                                                                                                                                    | Decision — caching                                                                                                  | Decision — UX/polling                               |
| ------------------------------------------------------------- | -------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| Cockpit — deployments tab                                     | `/api/deployments/inventory`, `/api/deployments/umbrella/{U}/summary`, `/api/vm-deployments` | FCP 2.2s but ALL 5 data calls 503/500 (29–38s); warm hit 0.7–1.0s vs cold 46s; vm-deployments UNCACHED, never succeeded; +1.7GB / +2.5GB RSS per surface              | _TBD_                                                                                                               | _TBD_                                               |
| Cockpit — consolidators tab                                   | `/api/health/consolidator`                                                                   | OK — 1.8–7.8s; 30s poll                                                                                                                                               | _TBD_                                                                                                               | _TBD_                                               |
| VM deployments page                                           | `/api/vm-deployments?days=7`, venue-\*                                                       | main call 503 @43s; venue-\* endpoints all &lt;1s                                                                                                                     | _TBD_                                                                                                               | _TBD_                                               |
| Deployments page                                              | inventory + umbrellas + regions                                                              | succeeds but 44–57s per call — ~1 min blank page                                                                                                                      | _TBD_                                                                                                               | _TBD_                                               |
| Live deployments page                                         | `/api/vm-deployments?days=1`, logs endpoints                                                 | vm-deployments 500 @42s; logs caches (B9) fine                                                                                                                        | _TBD_                                                                                                               | _TBD_                                               |
| **Data-status tab (REAL path = `/api/data-status/manifest`)** | `/api/data-status/manifest` (IS/MTDS/MDPS), drilldown, downloads                             | **⚑ THE OOM: IS full-hist 90s/18GB · MTDS full 81GB · MDPS 3mo 56GB — all uncached hot (index cached, cell-grid NOT); default range = full history → 1 click = kill** | _TBD_ — bound/stream window + cap grid + cache result (serve `uts-prod-data-status-rollup` `full.json.gz` from GCS) | _TBD_ — default to a narrow range, not full history |
| Ops / costs (billing)                                         | `/api/costs/{summary,breakdown,timeseries}`                                                  | breakdown **55s** cold + **+1.9GB RSS** (loads full cost-record set); distant #2 memory consumer; uncached-cold                                                       | _TBD_ (pre-warm? bounded/streamed cost cache? longer TTL?)                                                          | _TBD_                                               |
| Repo CI / coverage / escalations                              | `/api/repo-ci/*`, `/api/repos/gh-rate-limit`                                                 | overview warms 13.3→2.3s across repeats (per-worker copies); escalations 0.5s                                                                                         | _TBD_                                                                                                               | _TBD_                                               |
| Kill-switch tab                                               | kill-switch status APIs                                                                      | 5s poll                                                                                                                                                               | _TBD_                                                                                                               | _TBD_                                               |
| Launch consoles / readiness                                   | `/api/services/*`, `/api/deployments/validate*`                                              | B9/B10 — not yet measured (add during walkthrough)                                                                                                                    | _TBD_                                                                                                               | _TBD_                                               |

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

**Codex SSOT to update on landing:** `codex/05-infrastructure/billing-cost-observability.md`.

## 5. Todos

Phase A — walkthrough + decisions (operator-joint; blocks Phase B):

- [ ] [OPERATOR] P3. § 4 walkthrough session — open each deployment-ui page against live backend, fill every Decision
      cell + settle D1–D6 in place. `BLOCKED-OPERATOR-DECISION` until scheduled. **(was: P0 blocking-all-of-Phase-B —
      REPRIORITIZED 2026-07-14 per the operator's own 2026-07-13 Slack ruling in this doc's Progress Log L445-447:
      "general responsiveness → walkthrough" = lowest priority; verify-rerun finding 53. Phase B no longer gates on
      this.)**
- [x] ✅ [INFRA] P1. Rollup-svc cost-stop — elevated to near-term per the operator's 2026-07-13 Slack ruling (Progress
      Log L445-447); was narrative-only, promoted to a tracked todo by verify-rerun finding 53. **Resolved via
      per-service child-process isolation instead of pausing the cron** (pausing would have kept producing ZERO value;
      isolation makes 11 of 12 services succeed instead) — `deployment-api@8d260ad` + `deployment-service@08d29b0`
      (container 16Gi/4CPU→32Gi/8CPU, cron 10min→20min, attempt_deadline 600s→900s). Evidence:
      `gs://central-element-323112-data-status-rollups/` now contains a fresh
      `market-data-processing-service/full.json.gz` (written 2026-07-14T00:15:39Z) for the first time ever; full
      root-cause + fix detail in the Progress Log entry above.
- [ ] [BACKEND] P1. Add the deployment-api fail-fast/refuse-large OOM-guard — elevated to near-term per the same
      operator ruling; promoted from narrative to tracked todo (finding 53).
- [x] ✅ [BACKEND] P0. Benchmark session (2026-07-13, agent-run per operator direction) — deployed-API curl suite (39
      reqs, cold/warm/503 sequences), Playwright page-level timings (6 pages), local 4-worker replica with
      phase-attributed RSS monitoring incl. the turbo data-status path. Results = § 2.7; § 4 "Today" column filled with
      measured numbers; § 3 verdict revised (MTDS turbo = +11GB transient/+3.5GB permanent from ONE query). Evidence —
      raw CSV/JSON in session scratchpad; summaries in § 2.7 are the findings of record.

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
- [ ] [BACKEND] P1. **Costs — DuckDB-over-GCS snapshot (§4b Option B, chosen direction).** New ~12h worker (mirror
      `data_status_rollup_worker.py`) scans BQ/Athena once → writes full-grain parquet to
      `gs://…-cost-snapshots/{cloud}.parquet`; cost service downloads on startup + 12h refresh and queries via DuckDB
      (arbitrary group-by). One snapshot serves all views. Replaces the in-Python `CostWindowCache` aggregation. Target:
      /ops/costs 55s/1.9GB → ms/tens-MB. Codex: `codex/05-infrastructure/billing-cost-observability.md`.
- [ ] [BACKEND] P2. **Costs safety valve (only if /ops/costs hurts before DuckDB ships)** — bound `CostWindowCache`
      (entry cap + evict) + cap default `days`; do NOT build the full coarse-window refactor (thrown away under Option
      B).
- [ ] [BACKEND] P3. **File AWS cost bug** — health tiles report "1 cloud"; AWS Athena CUR path returns no data. Separate
      from perf; `plans/active/issues/<slug>.md` + verify against prod.
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
  (`deployment-service@08d29b0`): cron `_/10`→`\*/20`, `attempt_deadline`600s→900s (applied live via`gcloud scheduler
  jobs
  update`, matching this component's existing "imperatively managed" pattern; `.tf` kept in sync as desired-state SSOT). **Scope boundary respected**: MTDS/MDPS's OWN full-2018-today build still exceeds any sane per-child memory ceiling ("no RAM tier through 64GB survives it", § 3) — this fix does not and cannot make their own rollup blobs succeed; that remains exactly the § 4 walkthrough's job. **Operator asked** (separately, same session) whether DuckDB could help the § 3 compute — researched (not implemented): DuckDB is already a trusted, precedented pattern in this codebase (`unified-trading-library/manifest_consolidator.py`'s pandas→DuckDB migration, plus two one-off dedup/restore scripts in instruments-service and MTDS), but had never been applied to this data-status compute path. A 7-agent design workflow produced a concrete technical memo: DuckDB fixes the read/filter stage cleanly, but the DOMINANT cost (measured 81GB vs. a raw index that's plausibly low-single-digit-GB) is CPython dict-of-dicts overhead + per-category copies + `ProcessPoolExecutor`fan-out duplication in`venue_resolution.py`/`mtds.py`/`breakdowns_core.py`— DuckDB only fixes this if the nested Python loops are themselves replaced by SQL`GROUP
  BY` aggregation, which is a real rewrite (SQL sketches, file:line-cited risks, and an ordered implementation sequence
  are written up and available on request) — squarely § 3/Phase-B work, explicitly not implemented, offered as input to
  the walkthrough whenever it's scheduled.
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
