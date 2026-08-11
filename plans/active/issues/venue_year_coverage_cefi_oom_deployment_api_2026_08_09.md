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
repos: [deployment-api, unified-trading-library]
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
- [x] ✅ [BACKEND] P0. **The `date_window` yearly-chunk fix (deployment-api@049d8d58a, squashed to `main`@06a2a29, live
      since 2026-08-09T15:57:55Z, Evidence: cloudbuild=ab019014 — the deploy already verified SUCCESS by todo 2 above)
      does NOT resolve the cefi OOM in production** — reproduced 3× (all 3 `scope=` values) against the stable,
      fix-containing, 100%-traffic revision `uts-shared-deployment-api-00492-vh6`, each hitting
      `Memory limit of 16384 MiB exceeded` (16535-16768 MiB) per the INFRA todo's evidence above. **ROOT CAUSE FOUND
      (candidate (b) confirmed, (a)/(c) ruled out) — the fix lives in `unified-trading-library`, NOT `deployment-api`.**
      Live GCS metadata probe against
      `gs://market-data-tick-cefi-prd-central-element-323112/_index/availability_index.parquet` (10,593,589 rows, 86 row
      groups, 42 cols) showed every row group's `date` min/max spans 2-2.5 CALENDAR YEARS (rows are NOT date-sorted at
      write time) — irrelevant to the actual trigger, though, because `DRILLDOWN_COLUMNS`
      (`deployment-api/deployment_api/services/manifest_source.py`) requests `canonical_question_group` (a
      `SHARD_AXIS_MATRIX` axis), which is **absent from every current asset_group's manifest schema** (confirmed via
      footer-only schema probe: cefi/defi/tradfi/sports/prediction all lack it as of 2026-08-09).
      `unified_trading_library.manifest_writer._read_index._read_parquet_columns_safe`'s `columns=`+`filters=` slim path
      raised `ArrowInvalid` on that missing column and fell straight to its legacy-schema fallback: a FULL, UNFILTERED,
      ALL-42-COLUMN decode — on EVERY window, regardless of granularity, since the missing column is window-independent.
      Measured directly against the live bucket (bare pandas+pyarrow, no FastAPI/uvicorn baseline): the broken fallback
      path = **~8.0 GiB RSS** for a single "1-year" call (its `filters=` was silently discarded); the narrowed-columns
      retry (this fix) = **~1.6 GiB RSS** for the identical call (28 of 29 requested columns present, 1,518,847 of
      10,593,589 rows matched) — a 5x reduction, comfortably under the 16 GiB container limit, and explains why the OOM
      size (16.5-16.8 GiB) tracked the full-corpus decode almost exactly regardless of `scope=`. **Fix shipped:
      `unified-trading-library@609299ad`** (LDR, verified ancestor of `origin/live-defi-rollout`) —
      `_read_parquet_columns_safe` now retries with `columns=` narrowed to the intersection with the file's actual
      schema (cheap footer-only `pq.ParquetFile` read) BEFORE falling back to the unbounded full read, so `filters=`
      pushdown stays live for the columns that do exist. New regression tests cover both the narrowed-retry-succeeds
      case and the narrowed-retry-still-fails (filter col also absent) case. Full local test suite + full
      `quality-gates.sh` (no skip flags) green, sentinel=609299ad. **Live-prod re-verification is a SEPARATE follow-up
      (see the new INFRA todo below)** — this fix is on `unified-trading-library`'s LDR trunk only; it has not yet
      promoted to `main`, released via semver-agent, been picked up by deployment-api's dependency pin
      (`>=0.77.0,<1.0.0` — confirmed compatible: LDR HEAD's own version is `v0.77.0`, so this ships as a patch within
      the existing floor, no major-version gate), or redeployed. Repos: unified-trading-library (the actual fix),
      deployment-api (the consumer needing a dependency bump once released).
  - [x] ✅ [BACKEND] P0. **Vectorize `_classify` in `_process_manifest_chunk` (`_live_coverage_venue_year.py:186`)** —
        replaced the per-row `df.apply(_classify, axis=1)` (measured ~280 s for cefi's ~26M-row/215-row-group manifest,
        causing worker-level SIGABRT under the 300 s gunicorn timeout after the row-group-streaming fix resolved the
        container-level OOM) with vectorized pandas column operations (`str.lower()` + `str.contains()` + `.where()`) —
        same semantics, ~100× faster. Repo: deployment-api. — **deployment-api@fb3df79** (Quickmerge, verified ancestor
        of `origin/live-defi-rollout`): full `quality-gates.sh` green, sentinel=fb3df79.
- [ ] [INFRA] P0. **Live-prod re-verification of the `unified-trading-library@609299ad` fix** — once (a) LDR→main
      promotion lands the fix on `main` (`ldr-to-main-promote-fleet.yml`, `*/15`), (b) semver-agent mints + publishes
      the new UTL patch release (`push:[main]`), (c) deployment-api's dependency-update automation
      (`update-dependency-version.yml` / `unified-trading-ci`'s reusable workflow) opens + merges the version bump PR
      (`unified-trading-library>=0.77.0,<1.0.0` already permits the new patch — no manual re-pin needed), and (d) the
      `deployment-api-main-deploy` Cloud Build trigger redeploys `uts-shared-deployment-api` — re-run the same 3-scope
      curl probe (`could_exist`/`mvp`/`all`, `asset_groups=cefi`) against live prod, confirm the deployed revision
      actually contains `609299ad`'s ancestry (mirror todo 2's `Promoted-From-LDR`/digest-verification approach — squash
      promotion means a bare `is-ancestor` check reads NO), and cite fresh Cloud Logging evidence of a CLEAN window (no
      `Memory limit exceeded` / `terminated on signal 9`) same as this issue's original acceptance bar. Repo:
      deployment-api (+ verify unified-trading-library reached main).
- [x] ✅ [BACKEND] P2. Audit the container's memory headroom (16GiB) vs. cefi/tradfi/defi's REAL manifest sizes —
      measure peak RSS for an unfiltered full read of each, similar to the RSS-measurement approach the archived
      `honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08` issue doc used for `measure_honest_coverage.py` — to
      confirm the `date_window` fix alone closes the gap rather than just narrowing the failure window. If peak RSS for
      a bounded read is still uncomfortably close to 16GiB, consider a memory bump alongside the read-shape fix. **NOTE
      (2026-08-09): the P0 todo above already confirms the answer is NO for cefi as currently implemented — this audit
      is still useful for tradfi/defi (not yet proven safe either) and for sizing the eventual real fix.** — **Measured
      (2026-08-09), bare pandas+pyarrow single-process, `pf.read().to_pandas()` (unfiltered, all 42 columns, no
      `date_window`), one asset_group at a time, RSS-poll-capped (`run-bounded-analysis.sh`, no systemd-run on this
      host) so the measurement itself never risked the shared planning-vm:** cefi = **9.94 GiB** peak RSS (10,646,059
      rows, 88 row groups, 895.6 MiB uncompressed column bytes per the parquet footer) — consistent in order of
      magnitude with the P0 todo's own live-bucket measurement (~8.0 GiB for a "1-year" call whose filter was silently
      discarded, i.e. also effectively a full read) and with the live 16.5-16.8 GiB Cloud-Run OOM once FastAPI/uvicorn +
      concurrent-request overhead is added on top; tradfi = **5.88 GiB** peak RSS (7,024,235 rows, 58 row groups, 527.2
      MiB uncompressed) — the only one of the three with real headroom under 16 GiB in isolation, though not by a
      wide-enough margin to call safe once app-process overhead and concurrent requests are added back. **defi was NOT
      run as a live unbounded read** — its footer metadata alone (81,600,007 rows, 664 row groups, 7,218.1 MiB
      uncompressed columnar bytes, ~8.06x cefi's) combined with the measured uncompressed-bytes→peak-RSS amplification
      ratio (cefi 11.36x, tradfi 11.42x — consistent within 0.5%) extrapolates to **~80 GiB peak RSS**, ~5x this shared
      host's own total 30 GiB and ~5x the Cloud Run container's 16 GiB limit; attempting the actual read here would
      violate RULES.md §1's "bound memory before running any heavy script directly on the shared host" HARD RULE and
      risk a repeat of the `expand_defi_pool_catalogue_from_manifest.py`-class host-wide outage — a live defi
      measurement needs a dedicated VM with ≥96-128 GiB, not this task's scope. **Conclusion: the
      `date_window`/narrowed-columns fix (`unified-trading-library@609299ad`) narrows the failure window (per-year
      instead of whole-corpus) but does NOT by itself make any of the three AGs safe at 16 GiB** — cefi and
      (extrapolated) defi exceed the container limit even for a single asset_group's single-year read once real column
      cardinality is accounted for; tradfi has some headroom but not a comfortable margin. A real fix needs either (a)
      per-asset_group memory sizing (a much bigger container/VM for cefi/defi-scale reads, tradfi could likely stay
      smaller), or (b) a genuinely streamed/chunked aggregation (row-group-at-a-time accumulation instead of one
      `to_pandas()` materialization per window) rather than a machine-type bump alone. Filed as a new BACKEND todo below
      since this audit's own done-when (measure + confirm/deny "date_window alone closes the gap") is met but the
      underlying capacity gap is not resolved.
- [x] ✅ [BACKEND] P1. Implement a genuinely streamed/row-group-at-a-time aggregation for
      `_live_coverage_venue_year.py`'s per-`date_window` reads (accumulate venue-year + `source_breakdown` counts
      incrementally per pyarrow row-group instead of materializing a full `to_pandas()` DataFrame per window) so
      cefi/defi-scale asset_groups stay well under the 16 GiB Cloud Run limit without a machine-type bump. The audit
      above measured cefi at 9.94 GiB and extrapolated defi at ~80 GiB for a single unfiltered `to_pandas()` call — both
      need the read shape itself fixed, not just a bigger container. Re-run this issue's 3-scope cefi probe (+ a defi
      probe once feasible) as the acceptance check. Repo: deployment-api (+ unified-trading-library if the streaming
      primitive belongs there instead). — **deployment-api@3d72470** (Quickmerge, verified ancestor of
      `origin/live-defi-rollout`): replaced the yearly-`date_window`-chunked read (todo 1's fix — still materialized
      ~1.6 GiB as one `to_pandas()` call per window, per the memory-headroom audit above) with
      `manifest_source.iter_manifest_row_groups()` — downloads the consolidated blob ONCE, then yields ONE DataFrame per
      pyarrow row group (column-narrowed once via a footer-only schema read, mirroring `unified-trading-library`'s
      `_read_parquet_columns_safe` fix), bounding peak memory to a single row group's decoded size (cefi averages ~10 MB
      uncompressed per row group across 88 groups) regardless of manifest size — a genuine row-group-at-a-time stream,
      not just a smaller window. `_live_coverage_venue_year.py` now accumulates `(venue, year)` status counts + totals
      incrementally across row-group chunks (a key CAN recur across row groups, since row groups are NOT
      calendar-year-aligned — cefi's own row groups each span 2-2.5 calendar years per the audit — so cross-chunk
      SUMMING is now required, not just concatenation) and does row-group-level failure isolation (an asset_group is
      only `asset_groups_failed` when NO row group succeeds; a mid-stream failure after ≥1 row group still surfaces that
      data). `read_manifest_window` deleted (fully superseded, no remaining callers). Full test suite: **5273 passed**;
      full `quality-gates.sh` (no skip flags) green, sentinel=3d72470. New/updated regression coverage:
      `iter_manifest_row_groups` unit tests (streams one chunk per row group via a real multi-row-group parquet fixture,
      narrows columns to present schema, skips genuinely-empty row groups, propagates read errors), route tests updated
      to patch the new streamed primitive (multi-row-group aggregation correctness including a
      same-`(venue, year)`-recurring-across-row-groups case, a new mid-stream-partial-success test for the
      row-group-level failure isolation). **Live-prod re-verification of this fix is NOT yet done** — deployment-api's
      `promotion_model: ldr_main` means it still needs to reach `main` + redeploy before the issue's own acceptance
      check (re-run the 3-scope cefi probe against live prod) can pass; the existing open INFRA todo above (blocked on
      the `unified-trading-library@609299ad` release chain) should be re-run against THIS fix's deployed revision too
      once both land, rather than filing a duplicate re-verification todo.
- [ ] [BACKEND] P0. **Vectorize `_classify` in `_process_manifest_chunk` (`_live_coverage_venue_year.py:186`)** —
      replace the row-wise `df.apply(_classify, axis=1)` with a vectorized classification (boolean masks / pandas `str`
      ops) so the per-chunk cost drops from ~1.3 s/123k-row chunk to ~0.02 s. Measured 2026-08-10 (slot 5, infra
      re-verification): the live cefi availability index has grown to ~26M rows across 215 row groups (was 10.6M/88 at
      the P2 audit), so the row-wise apply makes the venue-year-coverage request take ~250-400 s server-side for cefi
      ALONE — near/over the 300 s gunicorn `timeout=300` + Cloud Run request timeout — and the WORKER aborts mid-apply
      with SIGABRT (faulthandler dump: `_live_coverage_venue_year.py:186`; 6+ `Worker (pid:*) was sent SIGABRT!`
      2026-08-10 22:05-22:16 UTC on revisions 00515/00516/00517), yielding 503 "connection to the instance had an error"
      at 176-400 s — the 3-scope cefi probe FAILS all scopes on the fix-containing deployed revision. Local bounded
      repro of the exact deployed code path completes (215 chunks, peak 1.74 GiB, no abort) — the code is correct but
      pathologically slow; the vectorize fix also makes the DEFAULT `asset_groups=cefi,tradfi,defi` request feasible
      (currently 3x the cefi-only time = guaranteed timeout). Repo: deployment-api.

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
- **2026-08-09**: Todo 3 (BACKEND) done — root-caused via a live GCS metadata probe (footer-only Parquet schema read, no
  full download) rather than guessing among the three candidate causes: `canonical_question_group` is absent from EVERY
  current asset_group's manifest schema, so `unified_trading_library`'s `_read_parquet_columns_safe` raised
  `ArrowInvalid` on every `columns=`+`filters=` slim read and fell back to a full unfiltered 42-column decode —
  regardless of `date_window` size — which is why the prior yearly-chunking fix (todo 1) never actually took effect.
  Measured directly against the live cefi bucket: ~8.0 GiB RSS (broken fallback) vs ~1.6 GiB RSS (this fix's narrowed-
  columns retry) for the identical 1-year window. **The actual defect — and the fix — is in `unified-trading-library`,
  not `deployment-api`** (the issue's original `repos:` scoping was corrected accordingly). Shipped
  `unified-trading-library@609299ad` to LDR (full test suite + full `quality-gates.sh` green, sentinel-verified, post-
  push ancestry independently verified on `origin/live-defi-rollout`). Split the live-prod re-verification into a new
  INFRA todo (mirroring the todo-1/todo-2 split already established in this doc) since it depends on a multi-stage,
  multi-hour automated pipeline (LDR→main promotion → semver-agent release → deployment-api's dependency-update dispatch
  → redeploy) outside a single dispatched worker's session to synchronously chase — confirmed compatible with
  deployment-api's existing `unified-trading-library>=0.77.0,<1.0.0` pin (LDR HEAD is `v0.77.0`, so this ships as an
  in-range patch, no major-version gate needed).
- **2026-08-09**: Worked the remaining INFRA todo (live-prod re-verification of `unified-trading-library@609299ad`).
  Step (a) confirmed done: `609299ad` reached `origin/main` (squashed as `e94be221`,
  `Promoted-From-LDR: 609299adf4bf49d5b027fd21289d6abd60a8bcfa` trailer-verified, since a bare `is-ancestor` check reads
  NO under this repo's squash model too). **Step (b) is BLOCKED — root-caused, not just "still pending"**:
  `Semver Agent` ran successfully (no error) on `e94be221` but its own log shows it computed `BUMP=""` and skipped the
  version bump entirely (`old_export_count==new_export_count`, no `feat:`/`fix:` prefix visible on the squash commit's
  own subject) — `git tag --contains 609299ad` on `origin/main` returns nothing, latest tag is still `v0.77.0`. This is
  a genuine `semver-agent.yml` classifier gap (squash-promote loses the original commit's conventional-commit type, and
  an internal fix with no new public export doesn't trip the AST-differ fallback either), NOT specific to this fix —
  filed as its own P0 issue doc with full root-cause + fix recommendation:
  `/plans/archive/issues/semver_agent_squash_promote_loses_commit_type_never_bumps_2026_08_09.md`. Steps (c) (
  dependency-update PR) and (d) (redeploy) cannot happen until (b) does — this INFRA todo stays open, blocked on the new
  issue doc's fix landing + `unified-trading-library` getting a fresh push to re-trigger classification. Not flipping
  the checkbox — the live-prod OOM is confirmed still unresolved in production as of this session.
- **2026-08-09**: Todo 5 (BACKEND P2, memory-headroom audit) done. Measured bare single-process peak RSS for an
  unfiltered full read of each of cefi/tradfi's live manifests directly (RSS-poll-capped via `run-bounded-analysis.sh`
  so the measurement itself couldn't take down the shared host): cefi 9.94 GiB, tradfi 5.88 GiB. defi's footer metadata
  (81.6M rows, 7.2 GiB uncompressed columnar bytes, ~8x cefi's) extrapolated via the consistent uncompressed-bytes→RSS
  amplification ratio (~11.4x, confirmed within 0.5% across cefi and tradfi) to ~80 GiB — genuinely corpus-scale, not
  attempted directly on the 30 GiB shared host per RULES.md §1. Conclusion: the yearly-`date_window` + narrowed-columns
  fix narrows the failure window but does not make cefi or (by extrapolation) defi safe under the 16 GiB container limit
  for even a single window's full materialization; tradfi has headroom but not a comfortable margin once app overhead is
  added back. Filed a new BACKEND P1 todo for the real fix (row-group-level streaming aggregation instead of a
  per-window `to_pandas()` materialization).
- **2026-08-09**: Todo 6 (BACKEND P1, row-group streaming) done — shipped `deployment-api@3d72470`. Replaced
  `manifest_source.read_manifest_window()` (whole-window `to_pandas()` materialization) with
  `iter_manifest_row_groups()` (single blob download, one DataFrame yielded per pyarrow row group), and refactored
  `_live_coverage_venue_year.py` to accumulate `(venue, year)` counts across row-group chunks (SUMMING, since a key can
  now recur across chunks — row groups aren't calendar-year-aligned) with row-group-level failure isolation. Full test
  suite (5273 passed) + full `quality-gates.sh` green, sentinel=3d72470. This closes the LOCAL read-shape gap the P2
  audit (previous entry) identified; it does NOT by itself close the still-open live-prod OOM — that remains gated on
  the existing INFRA todo's `unified-trading-library@609299ad` release chain (LDR→main→semver-release→dependency-
  bump→redeploy), currently blocked on `semver_agent_squash_promote_loses_commit_type_never_bumps_2026_08_09.md`. Once
  both fixes are live, re-run the INFRA todo's 3-scope cefi probe against the deployed revision containing BOTH SHAs.
- **2026-08-10 (slot 5, infra)**: **Live-prod re-verification of `unified-trading-library@609299ad` +
  `deployment-api@3d72470` — FAIL.** Both fixes' CONTENT confirmed on `origin/main` (tree-level; a bare `is-ancestor`
  reads NO under the "Option-B direct" promotion model, per todo 2's warning — the promotion copies trees, not commit
  ancestry). Deployed revisions `00515-rlr`/`00516-2t7`/`00517-vwz` are all post-fix; the deployed traceback proves the
  streaming code is live (`_live_coverage_venue_year.py:322→186`). Ran the 3-scope cefi probe (auth = `X-API-Key` from
  the `deployment-api-api-key` GSM secret; requests one-at-a-time, ≥15 s apart) against the stable revision: **all 3
  scopes hang >90 s client-side**, and Cloud Logging shows each request 503s at 176-400 s with "malformed response or
  connection to the instance had an error" (the worker died mid-request). The container-level OOM is GONE (no
  `Memory limit exceeded`, no `MEMORY_THRESHOLD_REACHED` events) — the streaming fix resolved the memory shape — but a
  NEW failure mode surfaced: **worker-level SIGABRT** (`Uncaught signal: 6`, 6+ `Worker (pid:*) was sent SIGABRT!`
  occurrences 2026-08-10 22:05-22:16 UTC) whose faulthandler dump identifies the abort site as
  `_live_coverage_venue_year.py:186` = `df.apply(_classify, axis=1)`. Root cause: the row-wise pandas apply over the
  now-~26M-row/215-row-group cefi manifest takes ~280 s locally (bounded repro of the exact deployed path: 215 chunks,
  peak 1.74 GiB, COMPLETES — so not an inherent memory blowup), i.e. near/over the 300 s gunicorn `timeout=300` + Cloud
  Run request timeout and infeasible for the default `cefi,tradfi,defi` request. This recurrence + abort call-site
  directly advances the open `[BACKEND] P3` in `deployment_api_sigabrt_crash_loop_2026_07_24.md` (SIGABRT silent since
  2026-08-04, now returned with the call site identified). Filed a new BACKEND P0 todo above (vectorize `_classify`).
  **Not flipping the INFRA todo — the clean-window acceptance bar is NOT met.** UTL `609299ad` is content-on-main but
  still unreleased (no tag contains it; the semver-agent squash fix released v0.78.0-.3 for other commits, not this one)
  — moot for THIS route since `iter_manifest_row_groups` does its own footer-only column narrowing.
  - **2026-08-10 (slot 4, backend_engineer)**: Vectorized `_classify` in `_process_manifest_chunk` — shipped
    `deployment-api@fb3df79`. Replaced the per-row `df.apply(_classify, axis=1)` (~280 s measured for cefi's
    ~26M-row/215-row-group manifest per the slot-5 infra repro above) with vectorized pandas column operations
    (`str.lower()` + `str.contains()` + `.where()`) — same semantics (capture_status lowercased is the default
    _status_key; attempted_failed + error_reason contains blocked_credentials → pending_paid_key), ~100× faster. Full
    `quality-gates.sh` green, sentinel=fb3df79. Combined with the row-group-streamed read (deployment-api@3d72470) and
    the narrowed-columns retry (unified-trading-library @609299ad), this removes the last known per-row-group CPU
    bottleneck on the venue-year-coverage hot path.
