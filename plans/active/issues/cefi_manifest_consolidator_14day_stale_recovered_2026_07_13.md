---
doc_type: issue
title:
  CEFI market-data manifest consolidator was ~14 days stale (frozen `availability_index.parquet`), slowing the
  2026-07-13 clean re-sweep — a manual trigger recovered it, but the precise root-cause mechanism is unconfirmed
summary:
  "Found 2026-07-13 while running a full clean re-sweep of `data_pipeline_e2e_check_2026_07_10.md` (todo 25): many CEFI
  MTDS shards blew through the checker's 1200s driver-level timeout because every manifest read fell back to a slow
  per-VM-shard scan — `ManifestReader: consolidated blob age 1220694.2s > 120s threshold` (~14.1 days), confirmed
  genuinely frozen (not a one-off) via 3 separate readings whose age growth matched wall-clock elapsed time exactly
  (443.3s / 591s / same). Initially hypothesized a stale pre-fix deploy (mirroring the already-tracked
  `defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md`) but DISPROVED that: CEFI's job is running the
  identical current image digest as DEFI's already-fixed job
  (`sha256:b6878c6eb608c303e6628aeaaa4abd35bca22e3f29618a7b05d9a6e747934085`). Cloud Logging showed the cron executing
  every ~1 minute and exiting cleanly in seconds with zero real work. Manually triggered `gcloud run jobs execute ...
  --args=...,--force` — the blob refreshed (fresh 164.75MB write), and the automatic cron has continued refreshing
  normally every ~1-2 min since (confirmed via 2 follow-up `Update time` checks). The immediate practical problem (stale
  index slowing the re-sweep + likely production reads) is resolved, but the root cause is NOT conclusively diagnosed —
  the forced run's OWN summary (`_index/latest.json`) reported `shards_scanned: 1, incremental: true, no_op: true,
  rows_added: 0`, suggesting `--force` may not have actually been honored by the `gcloud run jobs execute --args=`
  override, yet something about the manual trigger still kicked the cron out of its 14-day-stuck state. This closely
  matches the symptom of an already-ARCHIVED, supposedly-fixed bug
  (`consolidator_idle_bucket_incremental_trap_2026_06_19.md`, resolved 2026-06-19 via a `consolidator_content_write_at`
  marker) — that fix's code is still present in the current `manifest_consolidator.py`, so this is either a regression
  via a different trigger path, or a different bug with the same symptom."
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [unified-trading-library]
scope: [engineer, admin]
tags: [cefi, manifest-consolidator, staleness, incremental-trap, production-incident, data-correctness]
related:
  [
    ../data_pipeline_e2e_check_2026_07_10.md,
    defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md,
    ../../archive/issues/consolidator_idle_bucket_incremental_trap_2026_06_19.md,
  ]
created: 2026-07-13
parent_epic: mtds_mdps_master
priority: P1
source:
  [
    data_pipeline_e2e_check_2026_07_10.md clean re-sweep (2026-07-13),
    real gsutil/gcloud evidence,
    Cloud Logging query for uts-prod-manifest-consolidator-market-data-cefi,
  ]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data-pipeline-engineer
drift_direction: unknown
depends_on: []
---

# CEFI manifest consolidator ~14-day staleness — manually recovered, root cause unconfirmed

## Context

Running a full clean 452-shard re-sweep of `data_pipeline_e2e_check_2026_07_10.md` (todo 25, using all of this session's
fixed tooling), many CEFI MTDS shards (BINANCE-FUTURES, BYBIT, BINANCE-SPOT, BINANCE-DELIVERY, DERIBIT, OKX-SPOT, ...)
blew through the checker's 1200s driver-level timeout during the `sample_live_instrument` pre-check step alone, before
even launching a VM.

## What was found (real evidence, not inference)

1. **The staleness was real and severe, not a one-off reading.**
   `ManifestReader: consolidated blob age %.1fs > %ds threshold — falling back to per-VM shards` appeared across
   multiple different shards' logs, all in the ~1,220,600-1,221,700s range (~14.1 days). Three readings 7-10 minutes
   apart grew by EXACTLY the elapsed wall-clock time (11:47:49→1220693.5s, 11:55:12→1221136.8s [+443.3s / +443s
   elapsed], 12:05:03→1221727.8s [+591s / +591s elapsed]) — mathematically confirming the blob's `updated` timestamp was
   genuinely frozen for real, not intermittently refreshing.

2. **Ruled out: stale pre-fix deploy.** Initially assumed this mirrored
   `defi_consolidator_scheduler_sigkill_ unresolved_2026_07_10.md` (deployed-fix-only-to-defi). Disproven:
   `gcloud run jobs executions describe` on both CEFI's and DEFI's most recent executions showed the IDENTICAL running
   image digest (`sha256:b6878c6eb608c303e6628aeaaa4abd35bca22e3f29618a7b05d9a6e747934085`) — CEFI's job is NOT running
   stale code.

3. **The cron IS executing, just doing no real work.** Cloud Logging showed CEFI's consolidator job executing roughly
   every 1 minute (`uts-prod-manifest-consolidator-market-data-cefi-ngkdm` at 11:19:04, `-q2d86` one minute earlier),
   each completing in seconds with `Container called exit(0)` and zero application-level log output — consistent with a
   fast no-op path, not a crash/kill.

4. **`_index/consolidator_stall_state.json` showed suspiciously small counts**: `{"streak": 0, "baseline_shards": 2}`
   for CEFI, `{"streak": 0, "baseline_shards": 6}` for TRADFI, `{"streak": 0, "baseline_shards": 1}` for SPORTS. Per the
   stall-detector's own docstring (`manifest_consolidator.py:_check_consolidation_stall`), the alert only fires when
   `shards_scanned` grows PAST this baseline without merging — a quiet/idle bucket "never advances past its baseline, so
   it never alerts." Not yet determined whether this baseline reflects a genuinely idle bucket (correct, no-alert
   behavior) or a scanning bug that always reports a near-zero count regardless of real per-VM shard volume.

5. **A manual forced trigger recovered the symptom, but its own report contradicts what should happen under `--force`.**
   Ran
   `gcloud run jobs execute uts-prod-manifest-consolidator-market-data-cefi --args="-m, unified_trading_library.manifest_consolidator,--bucket,market-data-tick-cefi-prd-central-element-323112, --force"`
   (async, completed in 1m40.66s per the execution's own `status.conditions`). The blob was genuinely refreshed (fresh
   164.75MB write, `Update time` advanced to real-time). BUT `_index/latest.json` (the consolidator's own per-cycle
   summary, written at 12:15:43) reported:
   `{"shards_scanned": 1, "shards_changed": 0, "rows_in": 0, "rows_out": 0, "rows_added": 0, "duration_ms": 9444.7, "incremental": true, "no_op": true}`
   — `incremental: true` and `no_op: true` directly contradict what a genuine `force=True` full-rebuild should report
   (`incremental: false`, real `rows_out`). Either the `--args` override to `gcloud run jobs execute` didn't actually
   pass `--force` through to the script's argparse, or `--force`'s effect and this summary's fields don't line up the
   way the docstring describes — not fully reconciled.

6. **The automatic cron has continued refreshing normally since.** Checked `Update time` twice more after the manual
   trigger (12:14:39 → 12:16:49, ~2min apart, matching the job's normal `*/1` schedule) — the consolidator appears to be
   back to healthy, regular ticking. **The immediate practical problem is resolved** (both for this re-sweep's remaining
   CEFI shards and for real production reads), even though the precise mechanism that caused the 14-day freeze — and
   precisely what fixed it — is not conclusively understood.

## Relationship to the archived `consolidator_idle_bucket_incremental_trap_2026_06_19.md`

That doc diagnosed and fixed the IDENTICAL class of symptom in June: an idle bucket's cron taking a no-op path that
advances the canonical blob's mtime (`_touch_canonical_mtime`) without merging real content — proven then by the same
remedy (`consolidate(bucket, force=True)` immediately fixing it). The fix shipped a dedicated
`consolidator_content_write_at` GCS metadata marker (distinct from the raw blob `updated` timestamp) so the incremental
cutoff can no longer advance past a genuinely-unmerged shard. **That fix's code is still present** in the current
`manifest_consolidator.py` (`_CONSOLIDATOR_CONTENT_WRITE_AT_KEY`, `_get_content_write_mtime`, still wired into
`consolidate()`). This means either:

- (a) this is a genuine regression — some new code path bypasses the `consolidator_content_write_at` marker and falls
  back to touching the raw blob `updated` timestamp in a way the June fix didn't anticipate, or
- (b) `ManifestReader`'s OWN staleness check (`_read_consolidated_index_if_fresh` in
  `unified-trading-library/unified_trading_library/manifest_writer/_read_index.py:594-609`) reads the raw `blob.updated`
  timestamp DIRECTLY — NOT the `consolidator_content_write_at` marker the June fix introduced — so a legitimately-idle
  bucket with NO new shards for 14 real days (nothing wrong with the consolidator at all) could still report "stale"
  here even though the June fix's own correctness guarantee (never silently dropping a genuinely-new shard) held
  throughout. Under this reading, the 14-day gap might reflect 14 real days with zero new CEFI captures reaching GCS — a
  genuinely different (and separately concerning) upstream problem, not a consolidator bug at all.

**Not distinguished between (a) and (b) in this pass** — that requires comparing the raw per-VM shard file count/
timestamps in `_index/per_vm/` against the 14-day window to see whether real shards were actually landing and sitting
unmerged (confirming (a), the trap), or whether there simply were none (confirming (b), an upstream capture gap).
Flagging both possibilities rather than picking one without evidence.

## Not yet investigated

- Whether TRADFI's (`baseline_shards: 6`) and SPORTS's (`baseline_shards: 1`) consolidators show the same freeze
  pattern, or whether their small baseline counts are normal/benign (not checked beyond reading the stall-state file
  once).
- The PREDICTION consolidator's bucket name/existence — `market-data-tick-prediction-prd-central-element-323112`
  returned `BucketNotFoundException`; PREDICTION uses a different flat-kind bucket naming per an earlier session finding
  (todo 13 in `data_pipeline_e2e_check_2026_07_10.md`) — not reconciled here.
- Whether this recovery is durable, or whether the freeze will recur (no monitoring/alert was set up to catch a
  recurrence — the existing `_check_consolidation_stall` alerting path is the natural home for this, but its own
  `baseline_shards` semantics are part of what's unconfirmed above).

## Progress log

- 2026-07-13: Found during a full clean re-sweep re-verification. Ruled out stale-deploy (confirmed same image digest as
  DEFI's fixed job). Manually triggered a forced consolidation run — recovered the symptom (blob now refreshing normally
  on its regular cron cadence) but the forced run's own summary contradicts what `--force` should report, and the
  precise root-cause mechanism (regression of the June fix vs. a genuinely-idle bucket vs. an upstream capture gap) is
  not conclusively determined. Filed as an open finding rather than guessing at a definitive root cause without stronger
  evidence — the immediate operational impact (slow re-sweep reads, and likely slow/stale real production reads) is
  resolved by the manual trigger, which is itself a real, actionable remedy worth keeping in mind if this recurs
  (`gcloud run jobs execute uts-prod-manifest-consolidator-market-data-<ag> --args="-m,unified_trading_library.manifest_consolidator, --bucket,<bucket>,--force"`).
