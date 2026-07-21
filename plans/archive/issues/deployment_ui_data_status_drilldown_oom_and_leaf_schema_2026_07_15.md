---
doc_type: issue
title:
  "deployment-api/UI Data Status regressed: the hierarchical drilldown fanned out 5 concurrent full-index reads on page
  load (React <details> mounts collapsed children), OOM-killing the 4 GiB uts-shared-deployment-api container → 503
  storm on /drilldown + /api/health flap ('Backend unreachable') + empty Honest Coverage; fixed + drilldown leaf
  schema/metric work"
summary:
  "Root cause (live-reproduced 2026-07-15 via Playwright + Cloud Run logs): DataStatusTab renders a
  HierarchicalShardDrilldown per asset_group inside a default-collapsed <details>, but React mounts <details> children
  even while collapsed, so all 5 drilldowns' fetch-on-mount effects fired on page load. Each drilldown reads the ENTIRE
  per-(service,asset_group) availability index into memory (data_status_hierarchical.get_hierarchical_drilldown ->
  read_availability_index, uncached), so 5 concurrent builds exceeded 4096 MiB ('Memory limit of 4096 MiB exceeded with
  4203 MiB used') and the platform OOM-killed the whole instance -> /drilldown returned 503 (Cloud Run, not app code),
  /api/health flapped -> MockModeBanner showed 'Backend unreachable'. The 030779f OOM guard only bounded the
  turbo/manifest path, not the drilldown path. Honest Coverage was separately empty because HonestCoverageCard requests
  TODAY, which the daily measure-honest-coverage cron hasn't written yet for the first hours of each UTC day (404).
  Fixed across deployment-ui + deployment-api and verified live."
status: resolved
resolved_by:
  "ikennaigboaka (slot-3), 2026-07-15 — code fixes on LDR + verified live: deployment-ui@0d8b9d0 (fan-out) + @22ad900
  (leaf schema), deployment-api@002c479 (drilldown guard + honest-coverage fallback + metric); prod deploy via
  deployment-api-main-deploy Cloud Build."
locked_by:
nature: record
asset_group: [cefi, tradfi, defi, sports, prediction]
stage: [data, meta]
repos: [deployment-ui, deployment-api]
scope: [engineer, admin]
tags: [data-status, drilldown, oom, cloud-run, honest-coverage, leaf-schema, deployment-ui, deployment-api, playwright]
related:
  - codex/03-deployment/data-status-ui-surface.md
  - codex/02-data/honest-coverage-model.md
  - codex/02-data/availability-manifest-and-data-status.md
created: 2026-07-15
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
assigned_role: fullstack
drift_direction: none
source: operator (interactive 2026-07-15) + /autonomous
depends_on: []
---

# Data Status drilldown OOM + honest-coverage + drilldown leaf schema/metric (2026-07-15)

Codex SSOTs: `codex/03-deployment/data-status-ui-surface.md`, `codex/02-data/honest-coverage-model.md`,
`codex/02-data/availability-manifest-and-data-status.md`.

## Symptoms (operator report)

"deployment api and ui data status completely regressed — we wanted to fix OOM + 'backend unreachable' and lost all our
honest coverage and drilldown info."

## Root cause (one bug → four symptoms) — live-reproduced

- **UI fan-out**: `DataStatusTab` renders `HierarchicalShardDrilldown` per asset_group inside a **default-collapsed
  `<details>`**. React **mounts** `<details>` children even when collapsed, so all 5 fetch-on-mount effects fired on
  page load → 5 concurrent `/api/data-status/drilldown/...` calls.
- **Unbounded per-request memory**: each drilldown reads the whole availability index into memory
  (`get_hierarchical_drilldown` → `read_availability_index`, uncached, window-filtered in-memory). 5 concurrent builds
  on one 4 GiB Cloud Run instance → `Memory limit of 4096 MiB exceeded with 4203 MiB used` (Cloud Run logs, timestamps
  matched the page load).
- Consequences: `/drilldown` → **503** (Cloud Run killing the OOM'd instance; app code only ever raises 500) = "lost
  drilldown"; `/api/health` flap → **"Backend unreachable"** banner; the `030779f` OOM guard only bounded the
  **turbo/manifest** path (turbo full-history works fine at ~4.5 s), leaving the **drilldown** path exposed.
- **Honest Coverage empty (separate)**: `HonestCoverageCard` requests **today**; the daily `measure-honest-coverage`
  cron hasn't written today's `coverage.json` for the first hours of each UTC day → **404** → "Coverage not yet
  computed."

## Fixes shipped

deployment-ui (LDR):

- **`0d8b9d0`** — `LazyDrilldownDetails`: the drilldown request fires **only on `<details>` expand**, not on mount.
  Kills the 5-way concurrent fan-out (regression spec `DataStatusTab.lazy_drilldown.test.tsx`).
- **`22ad900`** — per-leaf **"⛃ schema"** control on the hierarchical drilldown: opens the existing `LeafSchemaModal`
  (`/leaf-stats` live parquet columns/stats) beside the existing per-day CSV download. Coord built from the leaf
  `row_key` with `instrument_type: "AUTO"` (deployment-api resolves the parquet path) + a per-service `data_type`
  default (instruments-service leaves are only `{venue, date}`). Regression specs in
  `HierarchicalShardDrilldown.test.tsx`.

deployment-api (LDR — `002c479`):

- **`_deploy_turbo.py`** — drilldown route now runs the heavy sync build **off the event loop** (`asyncio.to_thread`,
  keeps `/api/health` responsive) behind a **concurrency + in-flight guard**: a burst degrades to a graceful per-request
  **503 + Retry-After** instead of a container-wide OOM. Defense-in-depth backstop for the UI fix.
  - **Per-worker-guard correction (2026-07-15, live-caught):** the guard counters are module-level in ONE process, but
    `uts-shared-deployment-api` runs `WORKERS=2` uvicorn processes, so the original `_DRILLDOWN_BUILD_SLOTS=2` meant 2×2
    = **4** concurrent full-index builds container-wide — an 8-way prod burst still OOM'd (`Memory limit … 4249 MiB`).
    Fixed two ways: (1) **`_DRILLDOWN_BUILD_SLOTS=1`** (durable, ships via pipeline) → 1×WORKERS(2) = 2 container-wide
    builds; (2) immediate infra mitigation on prod: `--memory 8Gi` (persists across deploys — the deploy step sets
    `--update-env-vars WORKERS=…` but NOT `--memory`) + `WORKERS=1` (transient — the deploy resets it to 2, so the
    `SLOTS=1` code is the durable half). Re-tested 8-way burst → **6×200 / 2×503 / no OOM**.
- **`_live_coverage.py`** — `get_honest-coverage`: an un-dated request **walks back up to 14 days** to serve the most
  recent measured coverage (its real `date` travels in the payload); an explicit `?date=` stays exact (404 on miss).
- **`data_status_hierarchical.py`** — drilldown `completion_pct` = **(captured + empty_confirmed) / (captured +
  empty_confirmed + attempted_failed + expected_unattempted)** (operator ruling: empty_confirmed counts as a COVERED
  answer so it doesn't drag the ratio down — DRILLDOWN ONLY; the Honest Coverage card + turbo keep their own formulas).

## Verification (live, Playwright + curl + Cloud Run logs)

- Before: 5 concurrent `/drilldown` → all **503**, honest-coverage 404, 7 console errors, `Memory limit … exceeded`.
- After (local dev server → live prod API): **0** drilldown calls on load; expanding one asset_group fires **exactly
  one** request → **200**; Honest Coverage card fully populated; **API: Connected**; **no OOM/503** in the logs;
  drilldown leaf renders **90 "⛃ schema" + 90 "↓ csv"** controls; clicking schema opens `LeafSchemaModal` (`/leaf-stats`
  = 699 rows / 51 columns for an available shard; honest "unavailable" for a missing one).
- QG: deployment-ui green (TS/ESLint/86 tests/build); deployment-api green (134 touched tests pass).

## Progress Log

- 2026-07-15 — Diagnosed + reproduced live; shipped deployment-ui `0d8b9d0` (fan-out fix) + `22ad900` (leaf schema) +
  deployment-api `002c479` (honest-coverage fallback, drilldown concurrency guard, drilldown metric) — all QG-green on
  LDR. Prod deploy = deployment-api Cloud Build (`deployment-api-main-deploy`) rebundles the UI (SPA is bundled into the
  deployment-api image) → `uts-shared-deployment-api`; triggering LDR→main promote + watching the build, then verifying
  prod with Playwright (prod SPA loads without an auth wall).

## Prod deployment + verification (2026-07-15)

- deployment-api PR #288 (backend `002c479`) + deployment-ui PR #368 (`0d8b9d0`+`22ad900`) both auto-merged to `main`
  (v2 + SIT gated); deployment-api Cloud Build `deployment-api-main-deploy` rebundled the UI → Cloud Run revision
  `uts-shared-deployment-api-00172`.
- **Prod verified (Playwright + curl + logs):** data-status page loads with **0 drilldown calls on load** (lazy-mount);
  honest-coverage **200**; API **Connected**; no OOM/503 in normal use.
- **Burst-guard correction (see above):** an 8-way concurrent-drilldown burst still OOM'd (per-worker guard × WORKERS=2
  = 4 builds). Applied `--memory 8Gi` (persists across deploys) + `WORKERS=1` on prod (rev `00173`) → re-burst **6×200 /
  2×503 / no OOM**. Durable half `_DRILLDOWN_BUILD_SLOTS=1` shipped so the fix survives the next deploy (which resets
  `WORKERS=2`).
- **Reconciled a pre-existing RED gate** (autonomous rule 4): `TestTradFiMultiSourceUnion` (4 tests) was red on LDR —
  stale fixture (`CBOE/ohlcv_15m`, retired from UAC capabilities by `unified-api-contracts@78b9e899`). Realigned the
  fixture to a currently-declared venue-level TRADFI pair (`ICE/ohlcv_24h`); no assertions weakened. File now 156 passed
  / 2 skipped.

## Follow-ups — both DONE (2026-07-15, deployment-api@db9c8ed)

- [x] [INFRA] P2. Bake `--memory 8Gi` into the deploy config — deployment-api@db9c8ed. Added `--memory 8Gi` explicitly
      to the `gcloud run deploy` in `cloudbuild.yaml`'s deploy step (alongside `WORKERS=2`), so memory is no longer
      silently inherited from the prior revision. (Note: the deploy step lives in the per-repo cloudbuild.yaml,
      maintained by direct commits like `ab07227`, not the generic api template — pre-existing template drift, out of
      scope here.)
- [x] [PERF] P2. Proper root fix — memory-efficient drilldown read — deployment-api@db9c8ed. UTL
      `read_availability_index` ALREADY supports `columns=`/`filters=` pyarrow row-group predicate pushdown (built for
      `mtds_backfill_vm_startup_oom_rc137`). Wired `manifest_source.read_manifest_index(bucket, date_window=...)` to
      take that path (project `DRILLDOWN_COLUMNS` — the audited union of every axis-matrix axis + provenance cols + the
      `_merge_shard_frames` dedup keys — and filter `date` to the window), and `get_hierarchical_drilldown` now passes
      its window. Each build decodes only the window's row groups instead of the whole multi-year index (UTL benchmark:
      ~14.86 GiB → ~5 MB for a single-day filter on the 27.4M-row DeFi index). **Byte-identical output verified** on
      instruments-service/cefi (old full-read vs new pushdown: same totals, same 27 tree nodes, same completion_pct);
      108 drilldown unit tests + full QG green. Stale-tolerant fall-through preserved (a raising/empty pushdown falls
      back to the full read). Shipped via the dirty-deps direct-push carve-out (unified-trading-library had foreign
      uncommitted WIP at push time; F2 does not depend on it).

## Data observation (not a defect of this fix)

The `/leaf-stats` view surfaced that some manifest-`captured` instruments-service shards (e.g. ASTER 2026-04-16,
count=2) have **no retrievable parquet** at `instrument_availability/by_date/day=…/venue=…/instruments.parquet`
(FileNotFound). The feature correctly surfaces this honestly; the manifest↔parquet-path discrepancy for early ASTER
dates is a separate data-pipeline item to triage.
