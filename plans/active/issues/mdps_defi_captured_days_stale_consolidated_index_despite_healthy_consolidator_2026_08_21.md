---
doc_type: issue
title: >-
  DEFI `read_captured_days_by_cell` finds 0 MTDS-filtered captured cells for `--day 2026-07-05` even
  post-chain-axis-fix + post-streamed-read-fix — consolidated index blob is >4h stale despite the
  manifest consolidator running successfully every ~1-2 min
summary: >-
  4th re-run attempt of `mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md`'s
  batch19-extracted todo. Both blocking fixes that todo depended on (chain-axis key composition
  `market-data-processing-service@fae666bef2`, streamed-read replacement `market-data-processing-service@6ee153a0`
  / `unified-trading-library@11f1ebd1`) are shipped and independently re-verified — yet the DEFI leg still reports
  `PROVED NOTHING: 206 cell(s) enumerated, 0 verified`. 4 shipped diagnostic rounds this session (each landed via
  QG-green quickmerge, each re-verified live on a fresh driver VM) isolated the mechanism precisely: it is NOT the
  OOM, NOT the chain-axis composition, and NOT a `service_name`-filter bug in the streamed engine — those all work
  correctly. The real blocker is that `read_captured_days_by_cell`'s primary streamed path is never even reached:
  `ManifestReader` logs `consolidated blob age 14912.7s > 7200s threshold — falling back to per-VM shards` on every
  attempt, and the resulting per-VM-shards-only view only contains a handful of cells (14-41 depending on filter),
  none with an MTDS-service captured day >= `--day`'s 400-day lookback floor (2025-05-31). Directly verified via
  `gcs_describe_object`: the consolidated index blob's own `updated` timestamp is `2026-08-21T06:38:39Z` — genuinely
  hours old. Directly verified via `gcloud run jobs executions list`: the DEFI manifest-consolidator Cloud Run job
  (`uts-prod-manifest-consolidator-market-data-defi`) is NOT stalled — it completed successfully every ~1-2 minutes
  throughout this investigation window (10:44-10:50 UTC), each run taking ~35-44s. So the consolidator is healthy
  by its own execution-success signal, yet its OWN output blob is not being refreshed on anywhere near that cadence.
  This may be related to the already-open, independently-tracked
  `defi_collect_schedulers_paused_since_2026_07_18_2026_08_16.md` (DEFI's 3 raw-tick collect cron jobs paused in
  Cloud Scheduler since 2026-07-18) — if there is genuinely nothing new to merge, frequent quick "successful"
  consolidator runs finding no new per-VM shards would explain the blob's staleness — but this does NOT fully
  reconcile with `--day 2026-07-05` (well BEFORE the 07-18 pause) still finding 0 direct-day matches, nor with
  `mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md` item 1's 2026-08-17 finding of
  "abundant coverage through 2026-08-13" for the same canonical cells (AFTER the claimed pause date) via a separate
  DuckDB-based investigation. That reconciliation is NOT done in this session — flagged as the next concrete step,
  not guessed at.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-data-processing-service, unified-trading-library]
scope: [engineer, admin]
tags:
  [
    pipeline-e2e-check,
    mdps,
    defi,
    manifest-consolidator,
    staleness-budget,
    capture-schedulers-paused,
    single-walk,
  ]
related:
  [
    /plans/active/defi_satellite_ao_dispatch_batch19_2026_08_21.md,
    /plans/active/issues/defi_collect_schedulers_paused_since_2026_07_18_2026_08_16.md,
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: "2026-08-21"
author: slot-24 (data_engineering)
assigned_vm: planning
parent_epic: defi_master
priority: P1
resolved_by:
locked_by:
source:
  - defi_satellite_ao_dispatch_batch19_2026_08_21.md's item 3 (the DEFI pipeline_e2e_check re-run) — this session's
    4 re-run attempts against that todo surfaced a NEW, deeper blocker distinct from the OOM/chain-axis/streamed-read
    bugs the todo assumed were the last remaining blockers.
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: [defi_collect_schedulers_paused_since_2026_07_18_2026_08_16]
context_scope:
  [
    /plans/active/issues/defi_collect_schedulers_paused_since_2026_07_18_2026_08_16.md,
    unified-trading-library/unified_trading_library/manifest_writer/_read_index.py,
    unified-trading-library/unified_trading_library/manifest_writer/_staleness_budget.py,
    market-data-processing-service/scripts/pipeline_e2e_check.py,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
---

# DEFI `read_captured_days_by_cell`: consolidated index blob is hours-stale despite a healthy, fast consolidator

## What I found

**Session timeline (2026-08-21, all times UTC), 4 diagnostic rounds, each shipped + re-run on a fresh driver VM:**

1. **Round 1** (`pipeline-e2e-check-mdps-20260821-095728-f56c11`, 09:57): baseline re-run with both prior fixes
   live. Result: `PROVED NOTHING`, `rss_checkpoint(after_read_input_index:DEFI cells=0): peak_rss=1017.1MB`. Peak RSS
   ruled out a repeat OOM (the prior 3 attempts' failure mode) immediately — this is a NEW symptom.
2. **Round 2** (`pipeline-e2e-check-mdps-20260821-101133-f56c11`, 10:11), after shipping a diagnostic unfiltered
   re-read (`market-data-processing-service@47a51b1287`): filtered (service_name=MTDS, min_day=2025-05-31) = 0
   cells; **unfiltered (no service_name filter, same min_day) = 14 cells** — proves the read itself isn't fully
   broken, narrowing to "service_name filter" vs "lookback window" as the two live hypotheses.
3. **Round 3** (`pipeline-e2e-check-mdps-20260821-102123-f56c11`, 10:21), after shipping a 2-way split diagnostic
   (`market-data-processing-service@907ff58912`): **filtered, no min_day = 15 cells** (nonzero!) — proves the
   `service_name` filter itself is NOT broken (it correctly finds 15 real MTDS-service cells when the lookback
   window is removed). Unfiltered/no-min_day = 41 cells. This pins the blocker squarely on the interaction between
   `min_day=2025-05-31` and the underlying data — i.e., no MTDS-service captured DEFI row the read path can see has
   a `date` newer than `2025-05-31`, despite `mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md`
   item 1 (2026-08-17, a separate DuckDB-based investigation) reporting real recent coverage "through 2026-08-13"
   for these same canonical cells.
4. **Blocked mid-investigation on a pre-existing, unrelated QG-red**: `unified-trading-library`'s pip-audit gate
   failed on `PYSEC-2026-3721` (pip 26.1.2, locked in `uv.lock`) — confirmed pre-existing (no source diff touched
   dependencies) and fixed at the source (`uv lock --upgrade-package pip` + `uv sync` -> pip 26.2.1,
   `unified-trading-library@3095f35151`) rather than blindly adding to the fleet's `--ignore-vuln` allowlist, since
   this is the venv's own bootstrap tool, not a runtime dependency needing design discussion.
5. **Round 4** (`pipeline-e2e-check-mdps-20260821-104141-f56c11`, 10:41), after shipping row/batch counters directly
   into `read_captured_days_by_cell` (`unified-trading-library@3095f35151`, same commit as the pip fix): **the new
   counters never appeared in the log at all** — meaning the primary streamed-read branch (`pf.iter_batches(...)`)
   was never entered. Instead, `run.log` shows (module `unified_trading_library.manifest_writer._read_index`, a
   DIFFERENT internal reader class than the one I was instrumenting, `ManifestReader`):
   ```
   ManifestReader: consolidated blob age 14912.7s > 7200s threshold — falling back to per-VM shards
   ```
   repeated 4x through the run. **Directly verified independently**: `gcs_describe_object()` on
   `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` returns
   `last_modified='2026-08-21T06:38:39.982000+00:00'` — genuinely ~4h9m stale at the time of round-4's run
   (10:47 UTC), well past the DEFI-specific `7200s` (2h) staleness budget
   (`unified_trading_library/manifest_writer/_staleness_budget.py` — DEFI was already bumped 3600s->7200s on
   2026-08-14 for the exact same class of false-trip, per that file's own docstring history).

**The consolidator itself is NOT stalled** — `gcloud run jobs executions list --job=uts-prod-manifest-consolidator-market-data-defi`
shows it completing successfully every ~1-2 minutes throughout this session's investigation window (10:44:40,
10:45:44, 10:47:04, 10:47:58, 10:48:48, 10:49:40, 10:50:44 UTC — 7 consecutive successes, ~36-44s each). So by the
consolidator's own execution-success signal it is healthy, yet the blob it is responsible for producing has not
actually been refreshed on anywhere near that cadence.

## Why it matters

Every future `--day 2026-07-05`-style re-run of this DEFI matrix will keep reporting `PROVED NOTHING` regardless of
how many pipeline_e2e_check.py / UTL code fixes land — because the actual blocker is one layer up, in whether the
consolidated index reflects reality, not in the reader code. This also affects `mtds_pipeline_e2e_check_driver_vm_
oom_full_mvp_sweep_2026_08_14.md`'s MTDS driver, which shares `read_captured_days_by_cell` — any asset_group whose
consolidator exhibits this same "frequent successful runs, stale output blob" pattern would silently under-report
coverage there too.

## Two unreconciled hypotheses — next step is to pick between them with direct evidence, not guess

1. **Nothing new to merge** (consistent with `defi_collect_schedulers_paused_since_2026_07_18_2026_08_16.md`, still
   `status: open`): if DEFI's raw-tick collect cron jobs have been paused since 2026-07-18 with zero new per-VM
   shards produced since, frequent quick "successful" consolidator runs finding nothing new to merge would look
   exactly like what was observed. **Problem this doesn't explain**: `--day 2026-07-05` itself predates 2026-07-18
   by 13 days — if capture was flowing normally through 07-18 (as the pause doc's own framing implies), day
   2026-07-05 should be directly present in the manifest with no need for `--auto-day` fallback at all, yet it
   isn't found even via the no-min_day-bound, filtered read (round 3's 15 cells) at ANY date — meaning either those
   15 cells' captured days are ALL older than 2025-05-31 (contradicting a 07-18 pause with normal flow before it),
   or the 15-cell result itself is ALSO scoped to the stale/per-VM-shard-only fallback view, not the true history.
2. **Consolidator incremental-merge correctness gap**: the consolidator's frequent runs may be legitimately
   cheap/no-op passes that skip a full rewrite when nothing NEW has landed, but the LAST real rewrite (06:38 UTC)
   may itself not correctly preserve/re-scan older historical rows on each incremental cycle — a genuine
   consolidator-side data-loss risk distinct from a simple cadence/threshold mismatch. Not directly evidenced this
   session; flagged as a hypothesis only.

## Recommended decision

- [ ] [DATA] P1. Reconcile hypothesis 1 vs 2 above with direct evidence: query the RAW per-VM-shard objects (not the
      consolidated blob) for DEFI's canonical MTDS-service dex_pool_swaps cells directly (bounded, via
      `unified_trading_library.manifest_writer`'s own per-VM-shard listing helpers, on a dedicated VM per the
      heavy-I/O rule) to determine (a) whether ANY raw-tick shard object newer than 2025-05-31 genuinely exists for
      DEFI, and (b) whether the 2026-08-17 "coverage through 2026-08-13" finding
      (`mdps_defi_pipeline_e2e_check_zero_captured_days_after_oom_fix_2026_08_17.md` item 1) was measuring the same
      manifest surface this investigation is, or a different one (e.g. a stale local DuckDB snapshot). Repo:
      unified-trading-library / market-data-processing-service. Done when: a definitive, evidenced answer to "does
      DEFI raw-tick capture data newer than 2025-05-31 actually exist anywhere in GCS" is recorded here.
- [ ] [DATA] P2. If hypothesis 1 is confirmed (genuinely nothing new since before the lookback floor), re-run this
      driver against an OLDER `--day` that predates both the 07-18 pause AND falls within whatever the consolidator
      last had fully merged — to get the FIRST clean terminal, non-"PROVED NOTHING" verdict this todo has been
      chasing across 4 prior OOM/correctness fixes, unblocking `defi_satellite_ao_dispatch_batch19_2026_08_21.md`
      item 3 and `data_pipeline_check_mdps_features_2026_07_20.md`'s 5-AG consolidated report. Repo:
      market-data-processing-service. Done when: the DEFI leg reports a nonzero verified-cell count.
- [ ] [DATA] P2. If hypothesis 2 is confirmed instead (a real incremental-merge correctness gap), file a scoped fix
      plan against the manifest consolidator itself (Cloud Run job `uts-prod-manifest-consolidator-market-data-defi`)
      — do NOT attempt this inline; it is a shared-infra fix, not a driver-script fix, and needs its own careful
      review given `read_captured_days_by_cell` is shared by both the MTDS and MDPS drivers. Repo: TBD (whichever
      repo owns the consolidator job's merge logic — not yet identified this session).

## Progress Log

- **2026-08-21 (slot-24, data_engineering)**: filed after 4 shipped diagnostic rounds (each QG-green, each
  independently re-verified on a fresh driver VM) isolated the mechanism precisely — OOM/chain-axis/streamed-read
  service_name-filter are all confirmed working; the real blocker is the consolidated index blob's staleness vs a
  healthy, fast-running consolidator. Evidence commits: `market-data-processing-service@47a51b1287` (round-1 diag),
  `market-data-processing-service@907ff58912` (round-2 diag), `unified-trading-library@3095f35151` (round-3 diag +
  pip CVE fix, PYSEC-2026-3721). `defi_satellite_ao_dispatch_batch19_2026_08_21.md` item 3 and the source issue doc's
  extracted todo both stay open, cross-referencing this doc for the real next step.
- **2026-08-21 (data_pipeline_failure escalation worker, slot 22, agt-6ea9c3)**: this doc's own "hypothesis 2"
  ("Consolidator incremental-merge correctness gap … not directly evidenced this session; flagged as a hypothesis
  only") is now CONFIRMED with a precise mechanism, via a DP-WATCHER-002 (`DP_CRON_DID_NOT_FIRE`) escalation for
  the same bucket that landed independently. `gcloud logging read` against
  `uts-prod-manifest-consolidator-market-data-defi`'s own execution logs (15:53Z-16:25Z) shows every cycle logging
  `"skipping cycle … fresh lock present (sibling cron still running)"` + a self-diagnosing `CRITICAL "SILENT STALL
  … streak=N … needs consolidate(bucket, force=True)"`, `N` climbing 206→239 across that window — i.e. the
  consolidator is NOT doing frequent legitimate no-op passes, it is WEDGED on an orphaned lock, and this doc's own
  `06:38:39Z` canonical-freeze timestamp is exactly `566.2 min` before the DP-WATCHER-002 alert's `16:04:51Z` fire
  time, confirming both detection paths are reading the SAME frozen blob. Root cause + the already-shipped fix are
  documented in full on the new
  `/plans/active/issues/dp_watcher_002_defi_market_data_consolidator_lock_wedge_2026_08_21.md` (bit-for-bit the
  same wedge `manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md` already root-caused and fixed for
  cefi — `unified-trading-library@af783d92e4`/`53abdf72f3` — blocked purely on that doc's still-open MTDS-image-
  rebuild deploy step). This does NOT yet answer this doc's own open P1 todo ("does DEFI raw-tick capture data
  newer than 2025-05-31 actually exist") — that remains a separate, real question about the UNDERLYING data once
  the consolidator is unwedged and can actually merge it; this entry only explains WHY the consolidated view has
  been frozen, not what it will show once fresh. No code shipped this session (repo: market-tick-data-service — the
  fix belongs to the sibling doc, not duplicated here); doc-only cross-link, shipped via `safe-doc-push.sh`.
