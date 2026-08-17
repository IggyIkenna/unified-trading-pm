---
doc_type: issue
title: >-
  DEFI `/data-pipeline-check-mdps` driver survives the OOM fix but proves NOTHING — 0/206 cells verified
  despite the manifest read finding 115 real canonical captured cells (likely the known service_name=MDPS-vs-MTDS
  DeFi-capture discrepancy, not a new bug)
summary: >-
  Follow-up to `mdps_pipeline_e2e_check_defi_driver_oom_2026_08_16.md` (items 1-3 now shipped:
  market-data-processing-service@5773a617ad, deployment-service@5d7230ec04). Re-ran DEFI on the fixed driver
  (`PIPELINE_E2E_CHECK_DRIVER_MACHINE_TYPE=e2-highmem-8`, VM `pipeline-e2e-check-mdps-20260816-235931-f56c11`,
  --day 2026-07-05 --legs force,skip --require-captured --auto-day). The OOM is CONFIRMED FIXED and ROOT-CAUSED:
  the new RSS-checkpoint instrumentation shows `_read_input_index_frame` materializes **160,415,229 rows** (peak
  RSS 33.6GB) reading DEFI's raw-tick INPUT manifest — that single read alone already exceeded the old
  e2-highmem-4 (32GB) ceiling, confirming the OOM's exact mechanism. On e2-highmem-8 (64GB) the run completed
  cleanly in ~2 minutes with exit_code=1 (a soft failure, not a crash) — BUT the result is
  `PROVED NOTHING: 206 cell(s) enumerated, 0 verified (every cell skipped)`, even though the manifest read DID find
  115 real canonical `(venue, data_type)` cells with captured days. None of the 103 DEFI shards from
  `mdps_mvp_universe(DEFI)` matched any of those 115 keys, at ANY historical day (`--auto-day` found nothing to
  fall back to for any of them) — a 0% intersection between the shard universe and what's actually captured under
  `service_name=market-tick-data-service` in the raw manifest.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-data-processing-service, unified-trading-library]
scope: [engineer, admin]
tags: [pipeline-e2e-check, mdps, defi, service_name, capture-mismatch, single-walk]
related:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/archive/issues/mdps_pipeline_e2e_check_defi_driver_oom_2026_08_16.md,
    /plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md,
  ]
created: 2026-08-17
author: slot-20 (data_engineering)
assigned_vm: planning
parent_epic: infrastructure_master
priority: P1
resolved_by:
locked_by:
source:
  - data_pipeline_check_mdps_features_2026_07_20.md's "mdps-e2e-defi-oom-fix-and-full-matrix-completion" todo —
    the DEFI re-run this todo's own fix enabled surfaced this NEW, separate finding
---

# DEFI pipeline_e2e_check: OOM fixed + root-caused, but the driver now proves the shard universe doesn't match captured data

## What I found

**The OOM fix works and is root-caused.** RSS-checkpoint log lines from the live re-run
(`gs://deployment-scripts-central-element-323112/vm-logs/pipeline-e2e-check-mdps-20260816-235931-f56c11/run.log`):

```
00:02:47 rss_checkpoint(before_read_input_index:DEFI): peak_rss=396.7MB
00:04:05 rss_checkpoint(after_read_input_index:DEFI rows=160415229): peak_rss=33614.7MB
00:04:23 rss_checkpoint(before_groupby:DEFI rows=29591797): peak_rss=33767.7MB
00:04:36 rss_checkpoint(after_groupby:DEFI cells=115): peak_rss=33767.7MB
```

`_read_input_index_frame` (`market-data-processing-service/scripts/pipeline_e2e_check.py::_captured_days_by_cell`)
reads **160.4 MILLION rows** for DEFI even with the `_INPUT_INDEX_COLUMNS` 5-column pushdown — this is the ENTIRE
DEFI raw-tick manifest across every venue/data_type/date, not the ~2.37M dex_pool_swaps instrument-days measured
in `data_pipeline_check_mdps_features_2026_07_20.md` todo 13 (that number was PER-data_type; the full manifest is
~68x larger). That single read alone (33.6GB) already exceeded the old `e2-highmem-4` 32GB ceiling — this is the
DEFI driver OOM's confirmed, exact root cause, not a vague "somewhere in enumeration" guess. Column pushdown
narrows COLUMNS, not ROWS — there is no date/venue row-group filter applied to this read, unlike
`precompute_confirmed_empty_dates`'s date-range-pushdown pattern elsewhere in this same plan (todo
10-followup-b). On `e2-highmem-8` (64GB, this session's `PIPELINE_E2E_CHECK_DRIVER_MACHINE_TYPE` override) the
same read completes with ~30GB of headroom to spare — survives, but is NOT a genuine fix, just enough slack.

**New, separate finding: the driver proves nothing for DEFI even once it survives.** After the groupby, 115 real
canonical `(venue, data_type)` cells WERE found with captured days (`_input_row_is_canonical` passed,
`service_name == market-tick-data-service` passed). But `enumerate_mdps_shards(DEFI)`'s own 103 shards (built from
`mdps_mvp_universe(DEFI)`) matched ZERO of those 115 keys — `_resolve_shard_day` returned `None` for every single
shard × leg (206 total), so every cell was recorded `skipped`/no-captured-input via `_record_no_data_skip`. The
report's own migration-worklist section came back empty (`_(none — every checked cell was canonically shaped)_`),
so this is NOT the already-known non-canonical-shape case — it's a genuine 0% overlap between "what MVP says DEFI
should have" and "what's captured under `service_name=market-tick-data-service`" for EVERY shard, at every
historical day `--auto-day` could have picked.

**Likely cause, not yet confirmed**: `defi_pool_uppercase_recurrence_after_fold_2026_08_11.md` (lines 154-192)
already flags an "unexplored lead" that some DeFi raw capture rows carry
`service_name=market-data-processing-service` instead of the expected
`service_name=market-tick-data-service` — if DEFI's actual dex_pool_swaps captures were written under the WRONG
service_name, `_captured_days_by_cell`'s `frame["service_name"] == _MTDS_SERVICE_NAME` filter would silently
exclude every one of them, exactly matching this session's 0%-overlap symptom. This session did NOT confirm that
hypothesis directly (would need to re-run `_read_input_index_frame` without the service_name filter and diff the
resulting cell set against the 103 MVP shards) — flagging as the most promising next step, not a settled root
cause.

## Why it matters

Without this, the plan's DeFi-MVP-ETA headline goal has ZERO automated proof for DEFI even after the driver
mechanism itself is fixed — every future re-run of this exact matrix will keep reporting "PROVED NOTHING" for
DEFI specifically, masking whether MDPS candle derivation genuinely works for DeFi or not.

## Recommended decision

1. `[DATA] P1.` Confirm or refute the service_name hypothesis: re-run `_read_input_index_frame` (or a scoped
   ad-hoc read) against the DEFI prod raw-tick bucket WITHOUT the `service_name` filter, and check how many of the
   103 MVP shards' `(venue, data_type)` keys appear under a service_name OTHER than
   `market-tick-data-service` (most likely `market-data-processing-service`, per the existing lead). Repo:
   market-data-processing-service / unified-trading-library.
2. `[DATA] P1.` If confirmed, fix at the source: either MTDS's DeFi writer path is stamping the wrong
   `service_name` on `record_captured()` calls (fix the writer, most correct) or if some legitimate reason DeFi
   dex_pool_swaps really is written by MDPS itself, extend `_MTDS_SERVICE_NAME` matching in
   `_captured_days_by_cell` to accept both (document why). Do NOT silently broaden the matcher without confirming
   which case this is — the canonical-paths principle this plan already established (never legacy-pass a
   non-canonical shape) applies here too.
3. `[SCRIPT] P2.` Separately, `_read_input_index_frame` should genuinely bound its read (date-range or
   asset_group-scoped row-group pushdown, not just column pushdown) rather than relying on a bigger VM — the
   160.4M-row full-manifest read is real waste even once (1) is fixed, and the next AG whose manifest grows past
   DEFI's current size will re-hit the same OOM ceiling on `e2-highmem-8` too.
4. `[DATA] P1.` Once (1)/(2) land, re-run DEFI's `--legs force,skip --require-captured --auto-day` matrix again to
   get a REAL (non-"PROVED NOTHING") verdict, then consolidate all 5 AGs' reports per
   `data_pipeline_check_mdps_features_2026_07_20.md`'s open todo.
