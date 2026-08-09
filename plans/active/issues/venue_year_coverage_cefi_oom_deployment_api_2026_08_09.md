---
doc_type: issue
title: >-
  `GET /api/data-status/venue-year-coverage?asset_groups=cefi` reliably OOM-kills the shared `uts-shared-deployment-api`
  Cloud Run container (16GiB limit) — the unfiltered full-manifest read path, discovered during the MVP data-status
  toggle real-data verify
summary: >-
  While running the real-data verify of the MVP data-status scope toggle (`cross_cutting_satellite_ao_dispatch_batch8_
  2026_08_09.md`), hitting `GET /api/data-status/venue-year-coverage?asset_groups=cefi&scope=could_exist` (the
  endpoint's own DEFAULT `asset_groups` includes cefi) against the live `uts-shared-deployment-api` Cloud Run service
  reliably OOM-killed the container 4/4 times (Cloud Logging, 2026-08-09 14:53-14:55 UTC): each request logged `Memory
  limit of 16384 MiB exceeded with ~16.4-16.7GB used` followed by `Container terminated on signal 9`, and the client
  received `503` after 7-42s. `/health` and other lightweight routes stayed reachable throughout (a fresh instance
  served them), so this is scoped to this one route, not a full outage. Root cause (read from the live code, not
  guessed): `deployment_api/routes/data_status/_live_coverage_venue_year.py:132` calls
  `_ds._read_manifest_index(bucket)` with NO `date_window` argument. `deployment_api/services/manifest_source.py`'s
  `read_manifest_index()` docstring documents that `date_window=None` (the only mode this call site ever uses) skips the
  pyarrow row-group predicate-pushdown path entirely and falls through to the "unfiltered, stale-tolerant full read" of
  the WHOLE multi-year `market-data-tick-cefi-*` availability index — the exact shape the docstring itself cites as the
  known OOM risk (`mtds_backfill_vm_startup_oom_rc137_2026_07_14`: "~14.86 GiB -> ~5 MB for a single-day filter on the
  real 27.4M-row DeFi index"; `read_availability_index_bare_defi_callers_2026_07_27.md`: "one cache-miss from an OOM on
  the 1.58 GB defi-prd index" even with the narrower `DRILLDOWN_COLUMNS` projection this fallback already applies).
  cefi's tick-level manifest is evidently large enough that even the column-pushdown-only fallback (no date filter)
  exceeds the 16GiB container limit outright, not just risks it under cache-miss pressure. Verified NOT a fluke: same
  URL, 4 separate requests, 4 identical failure signatures. `sports` (a much smaller per-venue manifest) succeeded
  cleanly on the same endpoint/service in 15-26s for all three `scope=` values, confirming the bug is
  manifest-size-dependent, not endpoint-universal.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [deployment-api]
scope: [engineer]
tags: [oom, deployment-api, data-status, venue-year-coverage, cloud-run, memory]
related:
  [
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch8_2026_08_09.md,
    /plans/active/mvp_scope_catalogue_tagging_2026_06_08.md,
  ]
created: "2026-08-09"
author: data_engineering-worker-slot3
parent_epic: infrastructure_master
resolved_by:
locked_by:
locked_since:
source: >-
  Discovered live during cross_cutting_satellite_ao_dispatch_batch8_2026_08_09.md's real-data verify of the MVP
  data-status toggle (`venue-year-coverage?scope=mvp|could_exist|all`) — findings-triage HARD RULE (a data-correctness
  /reliability gap found mid-verify, not fixed inline per that todo's own explicit instruction).
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
---

# `venue-year-coverage` cefi OOM (16GiB Cloud Run limit)

## What I found

`GET /api/data-status/venue-year-coverage?asset_groups=cefi&scope=could_exist` against
`https://uts-shared-deployment-api-1060025368044.asia-northeast1.run.app` OOM-killed the shared deployment-api Cloud Run
container 4 times in a row (2026-08-09, 14:53:30-14:55:11 UTC):

| timestamp (UTC) | client result   | Cloud Logging evidence                                                                                           |
| --------------- | --------------- | ---------------------------------------------------------------------------------------------------------------- |
| 14:53:30        | 503 after 33.6s | `Memory limit of 16384 MiB exceeded with 16469 MiB used` @14:53:58, `Container terminated on signal 9` @14:54:03 |
| 14:53:56        | 503 after 6.9s  | (same container cycle)                                                                                           |
| 14:54:07        | 503 after 41.5s | (same container cycle)                                                                                           |
| 14:54:50        | 503 after 20.9s | `Memory limit of 16384 MiB exceeded with 16668 MiB used` @14:55:07, `Container terminated on signal 9` @14:55:11 |

`/health` returned `200 {"status":"ok",...}` throughout (a different, unaffected instance served it) — this is scoped to
the `venue-year-coverage` route for large asset_groups, not a full-service outage.

**Root cause** (`deployment-api` repo, read live from the shipped code — not the QG-passed HEAD assumed, the actual
deployed revision, since the failure is live):

- `deployment_api/routes/data_status/_live_coverage_venue_year.py:132`:
  `df: pd.DataFrame = _ds._read_manifest_index(bucket)` — called with **no `date_window` arg** for every asset_group the
  endpoint loads (its own default `asset_groups="cefi,tradfi,defi"` includes the two heaviest AGs by default).
- `deployment_api/services/manifest_source.py::read_manifest_index()`'s own docstring: `date_window=None` never even
  attempts the pyarrow predicate-pushdown path (`columns=DRILLDOWN_COLUMNS, filters=[("date", ">=", ...), ...]`) and
  falls straight to the "unfiltered, stale-tolerant full read" — which the docstring itself flags as the historically
  OOM-prone shape (`mtds_backfill_vm_startup_oom_rc137_2026_07_14`,
  `read_availability_index_bare_defi_callers_2026_07_27.md`). That fallback DOES already project `DRILLDOWN_COLUMNS`
  (not a truly all-columns read), but for cefi's tick-level manifest even that narrower projection is evidently >16GiB.

**Confirms manifest-size-dependence, not an endpoint-universal bug**: the SAME endpoint/service, requested for `sports`
instead of `cefi`, succeeded cleanly for all three `scope=` values (`could_exist` 17.8s, `mvp` 25.6s, `all` 14.8s, all
`HTTP 200`) — sports' manifest is evidently small enough to fit.

## Why it matters

`venue-year-coverage` backs the deployment-ui data-status dashboard's venue×year drilldown — the DEFAULT `asset_groups`
query param includes `cefi`, so any UI consumer hitting the default view (or `cefi` explicitly) reliably crashes a
container on the SHARED `uts-shared-deployment-api` service, which also serves unrelated routes (epics API, health,
other data-status views) from the same Cloud Run service — a crash-looping instance under this route degrades
availability for everything else routed to that instance while it restarts. This already blocked the batch8 real-data
verify todo's ability to check cefi/tradfi/defi (the endpoint's own listed default asset_groups) and forced falling back
to `sports` as the sample AG instead.

## Recommended decision

Wire a bounded `date_window` (or an equivalent row-cap / pagination) into `_live_coverage_venue_year.py`'s call to
`_read_manifest_index`, mirroring the pushdown path `manifest_source.read_manifest_index()` already supports and the
`data_status_hierarchical` drilldown presumably already uses correctly (worth confirming as part of the fix) — e.g.
default to the current+prior year, or accept an optional `year=` query param, rather than reading the full multi-year
history unconditionally. Re-verify against live cefi/tradfi/defi afterward (this issue's own fix should re-run this same
`venue-year-coverage?asset_groups=cefi&scope=could_exist|mvp|all` probe as its acceptance check).

## Todos

- [ ] [BACKEND] P1. Bound `_live_coverage_venue_year.py`'s `_read_manifest_index(bucket)` call with a `date_window` (or
      row-cap) so it takes the pyarrow pushdown path instead of the unfiltered full read, for every asset_group the
      endpoint serves (starting with cefi, tradfi, defi — the ones NOT yet proven safe). Repo: deployment-api. Done
      when: `GET /api/data-status/venue-year-coverage?asset_groups=cefi&scope=could_exist` (and `=mvp`, `=all`) each
      return `200` against live prod within a reasonable timeout (<30s), with a cited Cloud Logging check showing no
      `Memory limit exceeded` / `terminated on signal 9` entries for the request window, and a passing regression test
      pinning the bounded-read call shape.
- [ ] [BACKEND] P2. Audit the container's memory headroom (16GiB) vs. cefi/tradfi/defi's REAL manifest sizes — measure
      peak RSS for an unfiltered full read of each, similar to the RSS-measurement approach the archived
      `honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08` issue doc used for `measure_honest_coverage.py` — to
      confirm the `date_window` fix alone closes the gap rather than just narrowing the failure window. If peak RSS for
      a bounded read is still uncomfortably close to 16GiB, consider a memory bump alongside the read-shape fix.

## Progress Log

- **2026-08-09**: Filed during `cross_cutting_satellite_ao_dispatch_batch8_2026_08_09.md`'s real-data verify (findings
  discovered mid-verify, not fixed inline per that todo's own explicit instruction). The batch8 todo itself completed
  successfully using `sports` as the sample asset_group instead (unaffected by this bug).
