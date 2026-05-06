---
title: "Offline data-status rollup — turn 5-minute query into 200ms slice"
status: active
priority: P1
locked_by: live-defi-rollout
locked_since: 2026-05-06
owners: ["@ikenna"]
sources:
  - "this session: tier-3 Cloud Run deploy + ProcessPool benchmark (411s → 327s for full Jan 2018 → May 2026 range)"
  - "deployment-api/services/data_status_service.py (current on-demand compute)"
  - "deployment-service/terraform/manifest_consolidator_scheduler.tf (precedent — 10 jobs × */1 cron)"
links:
  shared_cloud_run: "https://uts-shared-deployment-api-1060025368044.asia-northeast1.run.app/"
  manifest_consolidator_precedent: "unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md"
---

## Problem

The `/api/data-status/manifest` endpoint takes **~310-410s wallclock** for the full Jan 2018 → May 2026 date range
because it computes per-(venue, data_type, date) honest-coverage on every request. Profiled in tier-3 deploy session
2026-05-06: 5 categories × ~30 venues × ~8 data_types × ~3000 dates = ~1200 honest-coverage entries built per request.
DEFI category alone is ~300s and caps any parallelism (verified — ProcessPool fork-based parallelism only shaved ~20%).

Default 30-day UI range works (~5s). The "All" preset is unusable interactively.

## Solution

Mirror the **manifest-consolidator daemon pattern** (`uts-prod-manifest-consolidator-*` — 10 Cloud Run Jobs running
`*/1 * * * *` per `deployment-service/terraform/manifest_consolidator_scheduler.tf`):

- Cloud Scheduler cron fires every 5 min
- Cloud Run Job computes full-range coverage for every service
- Writes a single rollup blob per service to `gs://central-element-323112-data-status-rollups/{service}/full.json.gz`
- `deployment-api` endpoint reads the rollup, slices by user's date range in-memory (microseconds), returns

**Insight**: full-range output is a superset of any sub-range. Compute once globally; the API becomes a thin slicer.

Latency: 310-410s → ~200ms (rollup read + slice). Staleness: at most 5 min — same order as the existing 5-min
`_INDEX_CACHE`. Manifest consolidator is `*/1 * * * *` upstream so the underlying data is at most 1 min stale before the
rollup picks it up.

## Pre-audit

### Consumers of `/api/data-status/manifest` and `/api/data-status/turbo`

- [x] `deployment-ui` (legacy Vite SPA, port 5183 + tier-3 Cloud Run): `src/api/client.ts` calls `/data-status/manifest`
      and `/data-status/turbo` directly.
- [x] `unified-trading-system-ui` (Next.js, port 3000): `components/ops/deployment/data-status/` — same endpoints via
      `/api/service-status/execution-services/data-status?...`.
- [x] No other internal consumers (Playwright tests are smoke only, manifest-consolidator daemon doesn't read these).

### Endpoint behavioural contract

`get_manifest_status(service, start_date, end_date, asset_groups=None)` returns:

```
{
  service, date_range, mode="turbo", sub_dimension, overall_completion_pct,
  overall_dates_found, overall_dates_expected, overall_shards_found, overall_shards_expected,
  migration_in_progress,
  asset_groups: { CEFI: {...}, DEFI: {...}, TRADFI: {...}, ... }
}
```

Each `asset_groups[cat]` has per-venue + per-data_type breakdowns with `dates_found`, `dates_expected`,
`completion_pct`, `missing_dates: list[str]`, `dates_found_list: list[str]`. **The per-date lists are what the slicer
needs to filter to honour the user's window.**

### Slicing semantics

Slicing the precomputed full-range payload to a smaller `(start, end)` window is straightforward:

1. Filter `missing_dates`, `dates_found_list`, and per-instrument `per_instrument` date lists to the requested window.
2. Recompute `dates_found = len(filtered_dates_found_list)`,
   `dates_expected = len([d for d in expected_dates if start ≤ d ≤ end])`.
3. Recompute `completion_pct` from the filtered counts.
4. Roll up overall totals.

The shard-weighted denominators (`expected_shards`) need a per-(venue, data_type) re-clip too — store the per-day
expected mask alongside the response so we can recount.

## Phased execution DAG

```
Phase 1 (worker script — local + smoke)
   │
   ▼
Phase 2 (Cloud Run Job + scheduler infra)
   │
   ▼
Phase 3 (deployment-api read-from-rollup + fallback)
   │
   ▼
Phase 4 (validation + retire on-demand >1y)
```

Phase boundaries are QG gates — next phase doesn't start until previous quality-gates passes for every affected repo.

> **2026-05-06 cross-link.** Two adjacent plans need coordination here:
>
> 1. **`data_status_multi_axis_shard_propagation_2026_05_06.plan.md` Phase 5** introduces a `breakdowns` dict in the
>    rollup blob (per-axis breakdown of coverage). To avoid a v1→v2 schema bump, **Phase 1 worker MUST emit `breakdowns`
>    from the first build** rather than ship the manifest payload alone. Cross-link Phase 1 SCRIPT below to multi-axis's
>    `_build_breakdowns` helper.
> 2. **`data_status_ui_fixes_2026_05_06.plan.md` Finding #3** removes MDPS from `TURBO_MODE_SERVICES` (turbo path hangs
>    > 90s on 1-day window). MDPS rollup adoption depends on that turbo removal landing first; otherwise the manifest
>    > path is fast but turbo path stays slow → confusing UX. **Prereq: ui_fixes Finding #3 lands before MDPS adopts the
>    > rollup.**

## Phase 1 — Worker script (PARALLEL)

- [ ] [SCRIPT] P1. Create `deployment-service/scripts/data_status_rollup_worker.py`
  - Inputs: project_id, output bucket, list of services (default = `_BUCKET_TEMPLATES.keys()` from
    `data_status_service.py`)
  - For each service: call `DataStatusService.get_manifest_status(service, start_date="2018-01-01", end_date=today)`
    synchronously
  - **Include `breakdowns` field per `data_status_multi_axis_shard_propagation_2026_05_06.plan.md` Phase 5 contract**
    (per-asset_group axis breakdown). Avoids v1→v2 schema bump downstream.
  - Compress with gzip, write to `gs://{bucket}/{service}/full.json.gz` with content-encoding=gzip metadata
  - Emit lifecycle events (`STARTED`, per-service `SERVICE_PROCESSED` with row counts, `STOPPED`/`FAILED`) per CLAUDE.md
    "no fire-and-forget VM launches" + adapter-progress-event rules
  - ServiceBootstrap from UTL (STEP 5.61 — required for QG)
- [ ] [SCRIPT] P1. Validation gates per `record_captured` (4 pillars from CLAUDE.md "Shard-granularity SSOT"):
  - row count > 0 (writes must produce a non-empty rollup)
  - no NaN ratio threshold needed (this is rollup output, not feature data)
  - schema matches the response contract above
  - all configured services produced output (cluster coverage)
- [ ] [SCRIPT] P1. Manual one-off run end-to-end:
      `python -m deployment_service.scripts.data_status_rollup_worker --project=central-element-323112 --bucket=central-element-323112-data-status-rollups`.
      Inspect output shape with `gsutil cat | zcat | jq` to confirm parity with the existing `/api/data-status/manifest`
      response.
- [ ] [QG] Phase 1 gate: `cd deployment-service && bash scripts/quality-gates.sh` green.

**Time estimate:** 0.5 day. The compute logic already exists in `data_status_service.py`; this script just batches it.

## Phase 2 — Cloud Run Job + Scheduler (PARALLEL)

- [ ] [INFRA] P1. Create `deployment-service/terraform/data_status_rollup_scheduler.tf` (mirror
      `manifest_consolidator_scheduler.tf`):
  - 1 GCS bucket: `central-element-323112-data-status-rollups` (lifecycle: delete after 7 days)
  - 1 Cloud Run Job: `uts-prod-data-status-rollup` (image = `deployment-service:latest`, mem=8Gi, cpu=4, timeout=600s)
  - 1 Cloud Scheduler cron: `*/5 * * * *` invokes the job
  - IAM: SA `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` gets `storage.objectAdmin` on the
    rollups bucket + `roles/run.invoker` on the job (already has).
- [ ] [INFRA] P1. `terraform apply` from `deployment-service/terraform/` after dry-run plan. Confirm
      `gcloud run jobs describe uts-prod-data-status-rollup --region=asia-northeast1` shows pinned image at fresh
      `:latest` digest (per CLAUDE.md "Cloud Run Jobs pin :latest at create time" — must
      `gcloud run jobs update --image=...:latest` after first AR push to force re-resolution).
- [ ] [INFRA] P1. Add `uts-prod-data-status-rollup` prefix to `VM_PREFIX_TO_BUCKET` in
      `deployment-service/scripts/vm/vm_zombie_watchdog.py` (per CLAUDE.md VM Naming Convention rule — silent zombie
      prevention).
- [ ] [VERIFY] After first cron fire (wait 5 min): confirm
      `gs://central-element-323112-data-status-rollups/{service}/full.json.gz` exists for every service. Check size +
      content via `gcloud storage cat | zcat | jq '.service' | head`.
- [ ] [QG] Phase 2 gate: terraform plan clean + scheduler firing successfully (≥3 consecutive successful cron runs).

**Time estimate:** 0.5 day.

## Phase 3 — deployment-api read-from-rollup + fallback (SEQUENTIAL — depends on Phase 2)

- [ ] [API] P1. Add `_read_rollup_if_fresh(service)` helper in
      `deployment-api/deployment_api/services/data_status_service.py`:
  - Reads `gs://central-element-323112-data-status-rollups/{service}/full.json.gz` if blob age < 600s (matches the
    consolidator-staleness-threshold pattern).
  - Returns the deserialised dict OR `None` if missing/stale.
  - Caches at module level with same 5-min TTL as `_INDEX_CACHE` (re-use that pattern).
- [ ] [API] P1. Add `_slice_rollup_to_window(rollup_dict, start_date, end_date, asset_groups_filter)`:
  - For each asset_group in rollup, for each venue, for each data_type: filter `missing_dates`, `dates_found_list`,
    `per_instrument[*].dates` to within `[start_date, end_date]`.
  - Recompute counts + percentages + overall totals.
  - Honour `asset_groups` filter (CEFI/DEFI/etc. subset).
- [ ] [API] P1. In `get_manifest_status`: try the rollup first; fall through to existing on-demand path if rollup is
      missing/stale. Log which path served the response (`x-data-status-source: rollup|on-demand` response header) for
      observability.
- [ ] [API] P1. Fail-loud guard: if rollup is present but slicing produces empty / malformed output (slice contract
      drift), raise `RuntimeError` rather than silently falling back. Per CLAUDE.md "honest absence vs fake
      placeholders" — empty-looking-populated is worse than missing.
- [ ] [QG] Phase 3 gate: `cd deployment-api && bash scripts/quality-gates.sh` green. Lint + tests + coverage.

**Time estimate:** 0.5 day.

## Phase 4 — Validation + retire on-demand for >1y queries (SEQUENTIAL — depends on Phase 3)

- [ ] [BENCH] P1. Re-bench from tier-3 shared Cloud Run:
  - `curl /api/data-status/manifest?service=market-tick-data-service&start_date=2018-01-01&end_date=2026-05-05`
  - Expect 200 OK in ~200-500ms (rollup read + in-memory slice).
  - Compare to current 327s (ProcessPool) / 411s (serial pre-this-plan).
- [ ] [BENCH] P1. Confirm sub-range queries (`30d`, `90d`, `1y`) ALSO drop to ~200ms. They're now slices of the same
      cached rollup; user's date-picker becomes free.
- [ ] [API] P1. Once rollup latency is confirmed: optionally retire the on-demand `_apply_mtds_honest_coverage` /
      ProcessPool fallback for queries `(end - start) > 1y` — emit a `503 RolloutNotReady` if the rollup is missing for
      large ranges instead of triggering a 5-minute on-demand compute. Keep on-demand for `<1y` queries (rare cache miss
      during deploy windows).
- [ ] [DOC] P1. Update CLAUDE.md "Manifest concurrency principle" section in
      `unified-trading-pm/codex/02-data/availability-manifest-and-data-status.md` to document the rollup pattern + when
      to use it vs on-demand.
- [ ] [QG] Phase 4 gate: end-to-end Playwright smoke from the tier-3 Cloud Run URL hits the "All" preset and gets
      results in <2s.

**Time estimate:** 0.25 day.

## Anti-patterns to avoid

- **Caching stale rollups**: rollup older than 30 min should NOT be served — fall through to on-demand instead. The
  staleness window must be configurable (env var) and enforced in `_read_rollup_if_fresh`.
- **Silently serving partial output**: if any service's rollup is missing, return on-demand for THAT service, not a
  half-populated response. Per CLAUDE.md "honest absence vs fake placeholders".
- **Slicing bug = silent data corruption**: write a test fixture comparing `slice(rollup, 30d_window)` against on-demand
  `get_manifest_status(30d_window)` and assert structural + count equality. Slice contract drift would cause UI to show
  wrong coverage percentages.
- **Pickling a DataStatusService instance into the Cloud Run Job**: Phase 1 worker should use module-level functions or
  `__main__` entrypoint, not pickled bound methods.

## Success criteria

- **Code**: all 3 affected repos pass quality-gates.sh.
- **Latency**: full Jan 2018 → May 2026 query returns < 1s consistently from tier-3 Cloud Run (vs current 310-410s).
- **Freshness**: rollups never older than 10 min in steady state. Cron fires every 5 min, completes in <5 min.
- **Cost**: <$15/month additional Cloud Run Job compute (5min/run × 144 runs/day × ~$0.0007/cpu-hour ≈ $7-12/mo).
- **Fallback**: missing/stale rollup gracefully degrades to existing on-demand compute (5min response).

## Out of scope (separate plans)

- Server-side date downsampling for >5y ranges (return month-bucketed instead of per-day). Lower priority once rollup
  ships; the slice is already <1s so the UX win is marginal.
- Streaming partial results via SSE during on-demand fallback. Only matters if rollup ever fails for hours.
- Per-asset-group lazy loading in the UI (fetch DEFI panel only when expanded). Nice-to-have but rollup makes full query
  fast enough that lazy loading isn't necessary.

## Companion notes

This plan dovetails with `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md` (commit `d591416d` in PM):

- The 4-pillar `record_captured` validation gates apply to the rollup writer (Phase 1 last todo).
- `available_at` is preserved in the rollup output (date lists already store ISO strings — no temporal drift).
- The slicer logic in Phase 3 is the read-side equivalent of the SSOT shard-key matrix: it must respect the same
  per-asset-group axis schema (chain for DeFi, league_id for Sports, instrument_id for CeFi spot/perp, root for bundled
  options/futures).
