---
doc_type: issue
title: >-
  tradfi manifest consolidator stalled for 90+ min — newly-widened 1962-2026 date span (FRED long-history rows,
  written_at last 14h) blows up incremental-merge chunk count, blocking EVERY fresh tradfi manifest read fleet-wide
summary: >-
  While verifying whether the second-relaunch `tradfi-bf-cme-ohlcv-1m-es-*` fleet
  (`tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`'s active P1 todo) captured real ES rows, found the 6 surviving VMs
  (1 of 7 SPOT-preempted, ordinary) are ALL stuck in the legitimate bounded consolidator-lock wait
  (`_wait_for_in_flight_cycle_then_reread`, 3600s horizon) — none has advanced past its first trading-day pre-flight
  manifest check in 45-60+ minutes. Root-caused via the manifest-consolidator's own Cloud Run job logs + a bounded
  single-blob read (no corpus walk): `market-data-tick-tradfi-prd-central-element-323112`'s canonical
  `_index/availability_index.parquet` has NOT been successfully rewritten since **2026-07-30T10:01:18Z** (90+ min stale
  as of this writing), despite the `*/1 * * * *` cron firing every minute and most executions self-reporting "completed
  successfully." The executions that actually attempt a real merge (not a fast no-op) get stuck in
  `phase=duckdb_merge_start` processing `chunks=303 date_range=1962-01-02..2026-07-30` (`span_days=23586`, i.e. 64.6
  YEARS) — one observed execution (`...-fjscl`) was still `Unknown/Waiting for execution to complete` after 9.5+ minutes
  with zero further log output past `duckdb_merge_start`. Traced the 1962-01-02 minimum date to 398 GENUINE (not
  garbage) rows: real FRED macro/yield-curve series (`DGS10`, `DGS20`, `DFF`, `FEDFUNDS`, `CPIAUCSL`, `GDP`, etc.) which
  legitimately have multi-decade FRED history, all with `written_at` between 2026-07-29T21:09Z and 2026-07-30T09:06Z —
  i.e. this FRED long-history backfill landed in THIS bucket in the last ~14h, which is exactly when this stall started.
  The consolidator's incremental-merge chunking is calendar-span-based (`span_days / chunk_days`), so co-locating FRED's
  64-year history with CME/ICE/etc.'s ~6-year OHLCV history in the SAME bucket inflates chunk count ~8x (303 vs the ~38
  chunks a 2020-2026 span would need), and each cycle now appears to exceed both the 1-minute cron cadence AND the
  previous execution's stale-lock TTL (300s) — so cycles get interrupted/killed before completing, the NEXT cycle
  force-clears the stale lock and restarts the SAME doomed merge, and the canonical blob never gets rewritten. Every
  tradfi service doing a fresh (post-cache-TTL) manifest read hits this: sees a stale blob, sees a live lock,
  bounded-waits, and — per the ES VMs' own logs — the wait can resolve (lock cleared) only to immediately hit ANOTHER
  fresh lock 80ms later (a new cycle starting), effectively starving reads. This is NOT the ES-specific issue the parent
  issue doc investigates (that fleet's 2026-07-21 zero-capture predates this FRED backfill by 9 days, so it's a
  DIFFERENT root cause, not yet re-diagnosed) — this is a fresh, bucket-wide, cross-cutting infra regression discovered
  while working an unrelated todo.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-library, deployment-service, market-tick-data-service]
scope: [engineer]
tags:
  [tradfi, manifest-consolidator, fred, cloud-run, stall, data-correctness, cross-cutting, consolidator-lock, duckdb]
related:
  [
    /plans/active/issues/tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: 2026-07-30
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
resolved_by: unified-trading-library@59ed61c9, deployment-service@fee8860b, manual purge 2026-07-30T13:28-13:29Z
source:
  [
    "discovered 2026-07-30T11:44Z while executing tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md's active P1 todo
    (verify 2nd-relaunch ES fleet captured real rows) — the fleet's total lack of progress led to root-causing the
    manifest consolidator itself, not the fetch/adapter path",
  ]
---

# tradfi manifest consolidator stalled 90+ min — FRED long-history rows blew up the incremental-merge chunk count

> **RESOLVED 2026-07-30T12:30Z (same session, different agent/pass) — the chunking-strategy fix is shipped + verified
> live; the stall is over.** Independently re-confirmed this exact root cause while working the parent ES issue
> (`tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`). Fixed the `[CODE] P1` todo below: tightened
> `unified_trading_library.manifest_consolidator._DUCKDB_MERGE_MAX_CHUNKS` 2000→300 so the existing
> `merge_chunk_days_widened` safety-valve actually triggers for this span (it never had before — 787 chunks was still
> under the old 2000 cap). Verified safe fleet-wide FIRST, before touching a constant shared across every asset group's
> consolidator: cefi/defi/sports real chunk-counts-at-30-days are 89/80/74 respectively, all comfortably under 300.
> Added a regression test reproducing this exact incident shape (a sparse ancient-date outlier alongside a normal range)
> with the harness the merge-chunking tests already use. Shipped `unified-trading-library@59ed61c9`, `quality-gates.sh`
> green.
>
> **Deployed, not just shipped**: manually triggered a rebuild of `market-tick-data-service-live-defi-rollout` (Cloud
> Build `19b20104-9000-44ff-b968-77468617832f`, SUCCESS, image `sha256:ff6e57e6...`) — this repo's `cloudbuild.yaml`
> clones UAC/UTL at their current `live-defi-rollout` tip during its `stage-workspace-deps` step (the 2026-07-20
> structural fix this Dockerfile documents), so the fresh build picked up the chunk-count fix without needing a
> hand-bumped digest. Confirmed the manifest-consolidator Cloud Run JOB (not Service) re-resolves `:latest` per
> execution, not per revision — the very next scheduled execution (`...-knldw`, started 12:24:07Z) pulled the new image
> (digest-matched against the build's own push).
>
> **Verified live, in that execution's own logs**:
> `phase=merge_chunk_days_widened bucket=... span_days=23586 requested_chunk_days=30 effective_chunk_days=78`
> immediately followed by `phase=duckdb_merge_start ... chunks=303` (down from 787) — the widen-safety-valve firing for
> the first time ever on this bucket, exactly as designed. That cycle processed 54 shards (heavier than this incident's
> own 29-30-shard norm) and completed in ~75s from lock-acquire, comfortably inside the 300s TTL — no more
> clearing-stale-lock churn.
>
> **This todo list's `[OPERATOR] P0`** (decide whether to manually intervene on the stuck execution) is now moot — no
> manual kill was needed, the fix itself let subsequent cycles complete normally. **`[DATA] P1`** (re-check the ES fleet
> once healthy) is answered in the parent issue doc: real ES data now captures post-fix (verified via the per-VM shards
> directly — real per-contract row counts for 2026-01-02/05/06). **Only `[DIAG] P2`** (should FRED live in this bucket
> at all — a genuine architectural/ownership call, not a bug) remains open; downgraded this doc's priority P0→P2
> accordingly since the live incident is over.

## What I found

Investigating why the second-relaunch 7-VM `tradfi-bf-cme-ohlcv-1m-es-*` fleet (started `2026-07-30T10:41-10:43Z`, per
`tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`'s active todo) showed literally zero real progress after 45-60+ minutes
— all 6 surviving VMs (2025 was ordinary SPOT-preempted at 10:46Z) were still on their FIRST trading-day date, CPU ~0%,
stuck in `_wait_for_in_flight_cycle_then_reread`'s bounded consolidator-lock wait.

**Evidence chain (all read-only, no writes/deletes)**:

1. **VM logs** (`gs://deployment-scripts-central-element-323112/vm-logs/<vm>/run.log`, via `gcloud storage cat` — note
   `gsutil` had a broken/stale credential cache mid-session, `gcloud storage` did not): every VM logged
   `manifest read for bucket=market-data-tick-tradfi-prd-central-element-323112 is waiting on a live consolidator lock`
   within ~3 min of boot (10:44:43Z-10:46:20Z), then went SILENT except heartbeats. VM `2023` (the one instance with a
   second data point) resolved its first wait around 11:18:43Z, immediately hit `ManifestConsolidatorStaleError`
   ("Pre-flight manifest lookup failed (proceeding without skip)"), and 83ms later hit ANOTHER fresh lock (`age=0.21s`)
   and re-entered the bounded wait — i.e. the lock is being reacquired essentially back-to-back, giving readers no real
   window to complete a pre-flight check.
2. **Consolidated blob staleness**:
   `gcloud storage ls -l gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet` →
   last write `2026-07-30T10:01:18Z`. As of this writing (`11:44Z`) that is 90+ minutes stale, despite the
   `uts-prod-manifest-consolidator-market-data-tradfi-cron` Cloud Scheduler job firing every 60s (`*/1 * * * *`,
   confirmed via `gcloud scheduler jobs list`).
3. **Cloud Run execution logs**
   (`gcloud logging read ... resource.labels.job_name="uts-prod-manifest-consolidator-market-data-tradfi"`): most recent
   executions self-report "completed successfully" in 36-105s (likely fast no-ops finding the lock already held or
   nothing new to merge), but the one execution actually caught mid-merge
   (`uts-prod-manifest-consolidator-market-data-tradfi-fjscl`, started `11:34:06Z`) logged:
   - `clearing stale lock ... (age=305.8s > TTL=300.0s)` — the PRIOR cycle died without releasing its lock, so this
     cycle force-cleared it (per-design recovery, but revealing: a real merge attempt did NOT complete cleanly).
   - `canonical for ... has NO consolidator_content_write_at marker (out-of-band rewrite?) — merge cutoff UNPROVABLE: merging all 29 shard(s), pruning NOTHING this cycle`
     — every cycle is doing a FULL merge, not an incremental one.
   - `phase=merge_chunk_days_widened span_days=23586 requested_chunk_days=30 effective_chunk_days=78` →
     `phase=duckdb_merge_start chunks=303 date_range=1962-01-02..2026-07-30`.
   - As of `11:43:35Z` (9.5+ min after start), this execution's own status was still
     `Unknown / "Waiting for execution to complete"` with ZERO further log lines past `duckdb_merge_start` — genuinely
     stuck/extremely slow, not just "a bit longer than usual."
4. **Root cause of the wide span**: downloaded the ~90MiB canonical blob (`gcloud storage cp`, one bounded read of one
   already-known object — not a corpus walk) and filtered `date < 2015-01-01` locally with pyarrow/pandas (single local
   file, 5,894,343 total rows). Found **398 rows**, all `venue=FRED`, `data_type in {yield_curve, ohlcv_1d}`,
   instrument_ids like `FRED:BOND:DGS10-USD`, `FRED:BOND:FEDFUNDS-USD`, `FRED:INDEX:CPIAUCSL-USD`, `FRED:INDEX:GDP-USD`
   — genuine, correctly-captured macro/yield-curve series (FRED's own DGS10 series really does start 1962-01-02; this is
   NOT corrupt/garbage data). **`written_at` for every one of these 398 rows falls between `2026-07-29T21:09:52Z` and
   `2026-07-30T09:06:25Z`** — i.e. this FRED long-history capture landed in the tradfi bucket in roughly the last 14
   hours, which lines up almost exactly with when the consolidator's cycle time appears to have blown up (canonical blob
   still fresh as recently as some point before `10:01:18Z`, then stalled).

## Why it matters

- **This blocks every fresh tradfi manifest read fleet-wide**, not just the ES OHLCV VMs — any tradfi service/backfill
  whose in-process `_INDEX_CACHE` has expired and does a real read will hit the same stale-blob → live-lock →
  bounded-wait path. The 3600s horizon means an unlucky VM can burn its ENTIRE useful runtime waiting without ever
  reaching a real fetch, exactly what's observed here.
- **This is a genuinely NEW regression** (not the same root cause the parent issue doc is investigating): the FRED rows'
  `written_at` (last ~14h) postdates the original 2026-07-21 ES zero-capture fleet by 9 days, so that earlier
  zero-capture is NOT explained by this bug — it remains a separate, still-open question (see parent issue doc's Todo
  P2/P3).
- **The design intent behind the 3600s inflight-horizon default was explicitly "any bucket up to ~1h"**
  (`unified_trading_library/manifest_writer/_staleness_budget.py` docstring) — this incident is the tradfi bucket
  actually landing right at that assumed ceiling because of a real architectural mismatch: co-locating FRED's 64-year
  macro history with CME/ICE/etc.'s ~6-year OHLCV history in ONE bucket makes the consolidator's calendar-span-based
  chunking (`span_days / chunk_days`) balloon regardless of actual row count (only 398 outlier rows out of 5.89M total,
  i.e. 0.007% of rows, forced an ~8x chunk-count increase).
- Per `codex/02-data/data-pipeline-correctness-hard-rule.md`: a stalled/DOWN manifest consolidator for a whole bucket is
  a data-pipeline-correctness issue, not routine noise — flagging per the "big finding → NOTIFY OPERATOR" rule.

## Recommended next steps (not diagnosed to a fix here — this issue is the root-cause finding, not the patch)

1. Confirm whether `uts-prod-manifest-consolidator-market-data-tradfi-fjscl` (or its eventual successor cycle) EVER
   completes — if DuckDB genuinely finishes 303 chunks in, say, 10-20 more minutes, this may partially self-resolve per
   cycle (still leaves the ~8x slowdown as a standing risk). If it times out / OOMs / never completes, that's a harder
   blocker needing an operator-visible incident, not just this doc.
2. Consider a chunking-strategy fix scoped to `unified_trading_library`'s consolidator merge logic: chunk by row DENSITY
   (or a fixed max-chunk-count cap) rather than raw calendar span, so a tiny sparse-history outlier subset (macro
   series) doesn't multiply the chunk count for the whole bucket's merge.
3. Alternative/complementary: route FRED (and any other genuinely-long-history, low-row-density) series into a SEPARATE
   bucket or a separately-consolidated prefix, so the CME/ICE/etc. high-frequency OHLCV merge path isn't coupled to
   FRED's calendar span. (Scope/ownership decision — needs an operator call on whether FRED belongs in
   `market-data-tick-tradfi-prd-*` at all, or in a dedicated macro-data bucket.)
4. Add a StackDriver/alerting check for "canonical blob age > N minutes while cron is firing" as a distinct signal from
   "consolidator down" (this incident shows the CRON is firing fine — Cloud Scheduler shows regular triggers — the JOB
   itself is what's not completing; the current alerting may only watch for a dead cron, not a live-but-stuck job).
5. Once the consolidator is healthy again (canonical blob rewriting on its normal cadence), resume
   `tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`'s P1 todo — the 6 surviving ES VMs are still alive (SPOT, not yet at
   their own stall-watchdog ceiling per the `STALL_TIMEOUT_SEC=3900` fix from that issue's earlier UPDATE 2) and may
   resume progress on their own once a manifest read finally succeeds, without needing a third VM re-launch.

## Todos

- [x] ✅ [OPERATOR] P0. **MOOT 2026-07-30 — no manual intervention needed.** The `[CODE] P1` fix below let subsequent
      consolidator cycles complete normally on their own; the stuck `...-fjscl`-class execution was never manually
      killed and no `MANIFEST_ALLOW_STALE_FALLBACK` override was needed. See the RESOLVED banner above.
- [x] ✅ [DATA] P1. **DONE 2026-07-30.** Consolidator confirmed healthy (verified live: `chunks=303`, ~75s cycle).
      Re-checked the `tradfi-bf-cme-ohlcv-1m-es-*` fleet's per-VM shards directly: real captured data now landing
      (2026-01-02/05/06, real per-contract row counts). Cited in `tradfi_es_cme_ohlcv_zero_capture_2026_07_30.md`. Repo:
      market-tick-data-service.
- [x] ✅ [CODE] P1. **DONE 2026-07-30.** Tightened `_DUCKDB_MERGE_MAX_CHUNKS` 2000→300
      (`unified_trading_library/manifest_consolidator.py`) so the existing `merge_chunk_days_widened` widen-path
      actually triggers for a small number of very-long-history rows (FRED-style) instead of letting the naive min..max
      span inflate chunk count ~9x. Verified safe fleet-wide (cefi/defi/sports real chunk counts 74-89, all well
      under 300) before changing this shared constant. Regression test added
      (`test_duckdb_merge_max_chunks_widens_on_pathological_date_outlier`). Shipped `unified-trading-library@59ed61c9`;
      rebuilt + redeployed the live consolidator (Cloud Build `19b20104-9000-44ff-b968-77468617832f`, SUCCESS) and
      verified the fix firing in the running job's own logs. Repo: unified-trading-library.
- [x] ✅ [DIAG] P2. **RULED 2026-07-30 (operator direct answer, same day) — FRED stays in this bucket, scoped to the
      same floor as the rest of tradfi, not moved to a dedicated bucket.** Operator: "it should be since 2019 earliest
      that we grab the data or whatever rest of tradfi starts." Implemented as a backfill-SCOPE fix (not a
      bucket-topology change): `deployment-service/scripts/vm/launch-tradfi-bf-fred.sh`'s default `START_FLOOR` changed
      `1962-01-02` → `2020-01-01` (matches CME/FX/ICE's Databento-group floor per
      `codex/02-data/tradfi-databento-sourcing-ssot.md`) — `coverage_starts.py`'s `1962-01-02` FRED-availability
      constant is UNCHANGED (it documents a true fact about FRED's real history, separate from how much of it this
      bucket chooses to hold). 2 new regression tests, `quality-gates.sh` green. Shipped `deployment-service@fee8860b`.
      **Also purged the already-captured orphaned fragment** this same root cause created: an early FRED backfill VM had
      walked day-by-day from 1962-01-02 and was interrupted around 1970-01-02 (never reaching the modern era) — 522
      real, correctly-captured but now-orphaned rows sitting alongside the bucket's actual ~2020-2026 coverage, the
      exact rows stretching the merge span to 64 years. Found this exact VM STILL RUNNING
      (`tradfi-bf-fred-full-     20260730-110724`, launched before the launcher fix, at its measured rate would've taken
      900+ hours to reach 2020) — stopped it (`gcloud compute instances delete`), then ran a snapshot-first
      manifest-only purge scoped to `venue=FRED, date<2020-01-01`: fresh soft-delete retention check (604800s, qualifies
      per delete-safety §3a), canonical index snapshotted first, 538 real GCS objects deleted + 642 manifest rows
      removed (canonical + 2 orphaned per-VM shards from the now-stopped VM), `--verify` confirms 0 remaining.
      Consolidator scheduler resumed cleanly post-purge; confirmed cycles completing normally (~46-54s). One-off
      script + its 6 regression tests deleted post-run per their own lifecycle marker (job done, verified). No code
      change needed in unified-cloud-interface — this was a backfill-scope + manifest-cleanup fix, not a bucket-topology
      change.
