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
priority: P0
drift_direction: advance-code
depends_on: []
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

- [x] ✅ [BACKEND] P1. Bound `_live_coverage_venue_year.py`'s `_read_manifest_index(bucket)` call with a `date_window`
      (or row-cap) so it takes the pyarrow pushdown path instead of the unfiltered full read, for every asset_group the
      endpoint serves (starting with cefi, tradfi, defi — the ones NOT yet proven safe). Repo: deployment-api. —
      **deployment-api@049d8d58a** (Quickmerge, verified ancestor of `origin/live-defi-rollout`): added
      `manifest_source.read_manifest_window()` (pure pyarrow `date_window` pushdown, NEVER falls back to the unfiltered
      full read — a real landmine `read_manifest_index()`'s own empty-window fallback would have hit on every iteration
      otherwise); refactored `_live_coverage_venue_year.py` to read each asset_group in yearly `date_window` chunks
      (2014→today), concatenating venue-year rows (disjoint by year, no merge needed) and summing `source_breakdown`
      counts across chunks by `(asset_group, pipeline_mode, source, transport, cadence)` (a real correctness landmine
      the naive per-chunk `provenance_breakdown()` call would otherwise have year-fragmented). An asset_group is
      `asset_groups_failed` only when EVERY window's read raised (shard-level failure isolation — a transient
      single-window failure no longer blanks the whole asset_group the way the old single-read design did). Full test
      suite: **5265 passed** (`--test --quick`); full `quality-gates.sh` (no skip flags) green, sentinel=049d8d58a.
      New/updated regression coverage: bounded-read call-shape pin (never calls `_read_manifest_index`), a year-boundary
      aggregation-correctness test (2 years' data via chunked reads matches what a single unwindowed read would have
      produced), a cross-chunk `source_breakdown` merge test, plus 3 new `read_manifest_window()` unit tests (pushdown
      columns+filter shape, propagates errors rather than swallowing them, never falls back to the unfiltered read on a
      genuinely-empty window).
- [x] ✅ [INFRA] P1. **Live-prod re-verification — deploy confirmed, but the fix does NOT resolve the OOM live.** Deploy
      trigger identified: Cloud Build trigger `deployment-api-main-deploy` (`_BRANCH=main`, `_DEPLOY=true`,
      `deployment-api/cloudbuild.yaml`'s `deploy` step) fires on every push to `main`; `deployment-api` promotes
      LDR→main per-commit via the `ldr_main` direct model (`promote/deployment-api/<sha>` PRs, auto-merged, one every
      ~10-40min). Confirmed deployment-api@049d8d58a reached `main` — **squashed** (not fast-forwarded) as commit
      `06a2a29` (PR #548, merged 2026-08-09T15:49:40Z, `Promoted-From-LDR: 049d8d58a2ba…`, diff matches the fix exactly:
      `_live_coverage_venue_year.py` + `manifest_source.py` + the 3 new/updated test files) — a **bare
      `git merge-base --is-ancestor 049d8d58a origin/main` reads NO for this repo's promotion model**, since it
      squashes; check by commit-message grep on `origin/main` or the `Promoted-From-LDR` trailer instead. Cloud Build
      `ee9512bb` (SHORT_SHA=06a2a29) deployed revision `uts-shared-deployment-api-00491-qsm` (2026-08-09T15:57:55Z,
      image digest `sha256:2e88a4c…` — verified byte-identical to the `:06a2a29` AR tag digest). A later same-day commit
      `a0b5abb` (build `ab019014`, ancestor-confirmed to include `06a2a29`) then deployed
      `uts-shared-deployment-api-00492-vh6` (2026-08-09T16:08:51Z), which is the STABLE 100%-traffic revision this
      re-verification ran against. **Re-verification result: FAIL.** Ran the 3-scope probe against `00492-vh6`
      (post-settle, requests spaced ≥15s apart, `--max-time 60`, one at a time): `scope=could_exist` → `503` in 47s
      (Cloud Logging: `Memory limit of 16384 MiB exceeded with 16535 MiB used` @16:12:33, SIGTERM/instance-recycle);
      `scope=mvp` → client timeout (`000`) at 60s, Cloud Logging:
      `Memory limit of 16384 MiB exceeded with 16629 MiB used` @16:14:19; `scope=all` → `503` in 58s, Cloud Logging:
      `Memory limit of 16384 MiB exceeded with 16768 MiB used` @16:16:34,
      `"container instance was found to be using too much memory and was terminated"`. All 3 reproduced cleanly on the
      settled, fix-containing revision (not a rollout-transition artifact — confirmed by re-running after traffic was
      100% pinned to `00492-vh6` for >3 min). **The `date_window` yearly-chunk fix from todo 1 does NOT close the cefi
      OOM** — see the new BACKEND todo below. This todo's own infra-scoped done-when (confirm live deploy + run the
      probe + cite responses/logs) is met; the underlying bug is not — deployment-api@a0b5abb (2026-08-09).
- [ ] [BACKEND] P0. **The `date_window` yearly-chunk fix (deployment-api@049d8d58a, squashed to `main`@06a2a29, live
      since 2026-08-09T15:57:55Z) does NOT resolve the cefi OOM in production** — reproduced 3× (all 3 `scope=` values)
      against the stable, fix-containing, 100%-traffic revision `uts-shared-deployment-api-00492-vh6`, each hitting
      `Memory limit of 16384 MiB exceeded` (16535-16768 MiB) per the INFRA todo's evidence above. Root cause unknown —
      the fix's own Progress Log entry (todo 1) passed the full local test suite + `quality-gates.sh`, so this is a
      live-only gap the test suite doesn't cover (no real-size cefi manifest in test fixtures). Candidate causes to
      investigate: (a) a single CALENDAR YEAR of cefi tick-level data is itself still too large post-pushdown (the
      issue's own root-cause section already established that an UNFILTERED read of cefi exceeds 16GiB outright — a
      yearly window may not be a fine-enough grain if recent years carry disproportionately more instruments/ticks than
      older ones; try monthly or weekly windows, or measure real per-year row/byte counts first); (b) the pyarrow
      `date_window` filter in `read_manifest_window()` isn't actually reducing the row-group set for cefi's specific
      partitioning/date-column type (verify EXPLAIN/row-group-skip stats on a real read, not just the filter shape unit
      test); (c) the per-chunk `pd.DataFrame`s or intermediate pyarrow tables aren't being released between years (check
      for an accumulating list before the final `concat` rather than an incremental accumulate+drop). Re-run this same
      3-scope curl probe (`could_exist`/`mvp`/`all`, `asset_groups=cefi`) against live prod as the acceptance check once
      a further fix ships; cite fresh Cloud Logging evidence of a CLEAN window (no `Memory limit exceeded` /
      `terminated on signal 9`) same as this issue's original acceptance bar. Repo: deployment-api.
- [ ] [BACKEND] P2. Audit the container's memory headroom (16GiB) vs. cefi/tradfi/defi's REAL manifest sizes — measure
      peak RSS for an unfiltered full read of each, similar to the RSS-measurement approach the archived
      `honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08` issue doc used for `measure_honest_coverage.py` — to
      confirm the `date_window` fix alone closes the gap rather than just narrowing the failure window. If peak RSS for
      a bounded read is still uncomfortably close to 16GiB, consider a memory bump alongside the read-shape fix. **NOTE
      (2026-08-09): the P0 todo above already confirms the answer is NO for cefi as currently implemented — this audit
      is still useful for tradfi/defi (not yet proven safe either) and for sizing the eventual real fix.**

## Progress Log

- **2026-08-09**: Filed during `cross_cutting_satellite_ao_dispatch_batch8_2026_08_09.md`'s real-data verify (findings
  discovered mid-verify, not fixed inline per that todo's own explicit instruction). The batch8 todo itself completed
  successfully using `sports` as the sample asset_group instead (unaffected by this bug).
- **2026-08-09**: Todo 1 (code fix) done — shipped `deployment-api@049d8d58a`, full test suite + full quality-gates.sh
  green. Split the original done-when's live-prod leg into its own todo (below) since the fix isn't deployed yet as of
  this session — the deploy pipeline/cadence for `uts-shared-deployment-api` wasn't identified and is outside this
  craft's scope to chase down synchronously.
- **2026-08-09 ~16:00-16:17 UTC**: Todo 2 (INFRA live-prod re-verification) done. Identified the deploy mechanism
  (`deployment-api-main-deploy` Cloud Build trigger, fires on push to `main`; deployment-api promotes LDR→main
  per-commit, SQUASHED, via the `ldr_main` model). Confirmed deployment-api@049d8d58a reached `main` (squashed as
  `06a2a29`) and is live (superset commit `a0b5abb`, revision `uts-shared-deployment-api-00492-vh6`, 100% traffic).
  **Re-ran the acceptance probe and it FAILED**: all 3 `scope=` values for `asset_groups=cefi` still OOM the container
  (`Memory limit of 16384 MiB exceeded`, 16535-16768 MiB used, 3 clean reproductions on the settled fix-containing
  revision). Bumped this issue back to **P0** and opened a new BACKEND todo — the yearly-`date_window` chunking fix
  reduces the OOM's trigger surface (single unfiltered read → per-year reads) but does not close it for cefi's real-size
  manifest; root cause of why a single year is still too large (or why pushdown isn't reducing enough) is
  uninvestigated. This is a live, still-open production reliability gap on a SHARED Cloud Run service — flagging
  prominently per the workspace's "big finding" governance rule (data-correctness/reliability, contradicts a prior
  "done" claim).
