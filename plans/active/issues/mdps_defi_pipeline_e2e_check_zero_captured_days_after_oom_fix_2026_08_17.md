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
parent_epic: security_and_cross_cutting_master
priority: P1
resolved_by:
locked_by:
source:
  - data_pipeline_check_mdps_features_2026_07_20.md's "mdps-e2e-defi-oom-fix-and-full-matrix-completion" todo —
    the DEFI re-run this todo's own fix enabled surfaced this NEW, separate finding
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/archive/issues/mdps_pipeline_e2e_check_defi_driver_oom_2026_08_16.md,
    market-data-processing-service/scripts/pipeline_e2e_check.py,
    /codex/02-data/defi-canonical-naming-ssot.md,
    /plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md,
  ]
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

1. `[DATA] P1.` ✅ **DONE 2026-08-17 (slot-3, data_engineering).** Confirmed or refuted the service_name
   hypothesis via a bounded DuckDB read (local downloaded copy, `SET memory_limit`, never a full pandas
   materialization) against the real DEFI manifest: **REFUTED.** The non-MTDS `service_name` rows
   (`market-data-processing-service`, 3.58M rows / 38 cells) are legitimate MDPS candle-OUTPUT rows —
   `DefiSwapAdapter` (`market_data_processing_service/app/adapters/defi/swap_adapter.py`) is registered under the
   SAME canonical `data_type="dex_pool_swaps"` name as its raw MTDS input, by design (its own docstring cites the
   2026-06-01 `defi-canonical-naming-ssot.md` ruling) — `_captured_days_by_cell`'s exclusion of them is CORRECT,
   not a bug.
   **Real root cause found instead**: real MTDS-service_name captured rows for DEFI carry a **chain-LESS**
   `venue` column ("UNISWAP_V3", "AAVE", "CURVE", …) plus a separate `chain` column ("ETHEREUM"/"ARBITRUM"/…),
   while `mdps_mvp_universe("defi")` returns a single **chain-SUFFIXED** venue string
   ("UNISWAP_V3-ETHEREUM"). `_INPUT_INDEX_COLUMNS` never even read the `chain` column, so
   `_captured_days_by_cell` could never compose the matching key — every DEFI MVP shard reported zero captured
   input regardless of real coverage. Confirmed abundant, RECENT real coverage exists once chain is accounted
   for: e.g. `UNISWAP_V3`/`ETHEREUM`/`dex_pool_swaps` = 1,768,976 rows through 2026-08-13;
   `UNISWAP_V3`/`ARBITRUM`/`dex_pool_swaps` = 574,557 rows through 2026-08-13; similar depth across
   BALANCER/CURVE/SUSHISWAP_V3/PANCAKESWAP_V3/AERODROME_V3/CAMELOT_V3 and their respective chains.
2. `[DATA] P1.` ✅ **DONE 2026-08-17 (slot-3, data_engineering)** — fixed at the source per the corrected root
   cause above: added `"chain"` to `_INPUT_INDEX_COLUMNS`, and `_captured_days_by_cell` now groups DEFI rows by
   `(venue, chain, data_type)` and composes the cell key as `f"{venue}-{chain}"` when `chain` is non-blank
   (falls back to the bare venue for every other asset_group, where `chain` is always blank per
   `SHARD_AXIS_MATRIX` — regression-tested). 3 new tests
   (`tests/unit/test_pipeline_e2e_check_defi_chain_axis.py`): composed-key match, no-chain-column fallback,
   blank-chain fallback. QG green (64s). **Evidence: market-data-processing-service@fae666bef2.**
- [x] ✅ [SCRIPT] P2. **DONE 2026-08-20 (slot-7)** — the `_read_input_index_frame` full-manifest read is replaced,
   not just resized. `_captured_days_by_cell` now reads through the row-group-STREAMED UTL
   `read_captured_days_by_cell` (unified-trading-library@11f1ebd1: `iter_batches(batch_size=131072)` + per-batch
   `min_day` filter + bounded legacy fallback) with a 400-day `_CAPTURED_DAYS_LOOKBACK_DAYS` date-range bound —
   peak memory ≈ compressed bytes + one batch, never the ~160M-row decode, on any machine size
   (market-data-processing-service@6ee153a0 removed `_read_input_index_frame` entirely; regression tests
   `test_resolve_shard_day_bounds_scan_to_lookback` + streamed-read coverage shipped in the same commit).
   **Evidence: market-data-processing-service@6ee153a0, unified-trading-library@11f1ebd1 — both verified on
   origin/live-defi-rollout by direct code read.**
- [ ] [DATA] P1. **➡️ EXTRACTED → plans/active/defi_satellite_ao_dispatch_batch19_2026_08_21.md (2026-08-21,
   ag-closeout-audit Phase 3 sweep).** Still open. Now that (1)/(2) have landed, re-run DEFI's `--legs force,skip --require-captured
   --auto-day` matrix again to get a REAL (non-"PROVED NOTHING") verdict, then consolidate all 5 AGs' reports per
   `data_pipeline_check_mdps_features_2026_07_20.md`'s open todo. **2026-08-17 note**: the plan's own CEFI driver
   (`pipeline-e2e-check-mdps-20260816-224232-71d52d`) was STILL RUNNING (not terminal) as of this check — do not
   relaunch it; the DEFI re-run this todo needs is independent and can proceed without waiting on CEFI.
   **2026-08-17 update — first re-run attempt (`pipeline-e2e-check-mdps-20260817-005300-c59390`, launched 00:53
   UTC) CRASHED silently, relaunching (see item 5 for root cause + why this is a relaunch-safe mitigation, not a
   blind retry).**
5. `[DATA] P1.` NEW finding 2026-08-17 (slot-3, data_engineering). The 00:53 UTC DEFI re-run (`c59390`) died
   silently mid-run: `run.log` goes dead at `2026-08-17 01:18:49Z` (last line, no error/traceback), `EXIT_STATUS`
   never advanced past `RUNNING`, and the VM is **absent entirely** from `gcloud compute instances list` (not
   `TERMINATED` — gone), confirmed via a direct `gcloud compute instances list --filter="name~c59390"` returning
   zero rows while sibling VMs (CEFI's driver, CEFI's own backfill sub-VM) still list normally. **Root cause,
   inferred from the driver's own RSS-checkpoint log**: after leg 1 (`pipelinecheck`)'s manifest read+groupby,
   `peak_rss=38052.1MB`; by leg 2 (`pcskip`)'s sub-VM-poll ticks, `driver RSS peak` had grown to **62413.7MB** —
   this run WAS on `e2-highmem-8` (64GB; the 38GB leg-1 read alone already exceeds e2-highmem-4's 32GB default,
   so the override must have carried), meaning leg 2 pushed RSS to ~97% of the machine's ceiling. This is
   consistent with a kernel OOM-kill (SIGKILL bypasses any `finally`-block EXIT_STATUS write, but the VM's
   unconditional shutdown-trap self-delete still fires) — **the driver is not releasing leg 1's in-memory
   DataFrame/index structures before starting leg 2**, so RSS accumulates ACROSS legs instead of peaking once
   per leg. This is separate from item 3 (bounding the single manifest read) — even a perfectly row-group-bounded
   read will keep accumulating leg-over-leg if the driver never frees prior legs' objects, and the next AG with
   >2 legs will hit this ceiling on ANY machine size. **Mitigation applied for THIS re-run** (relaunch-safe,
   not a design change): relaunched with `PIPELINE_E2E_CHECK_DRIVER_MACHINE_TYPE=e2-highmem-16` (128GB) — with
   only 2 legs and an observed ~24GB leg-2 increment, 128GB leaves ample headroom to reach a real terminal
   verdict without masking the underlying leak. **Relaunched 2026-08-17 02:42 UTC**: VM
   `pipeline-e2e-check-mdps-20260817-024215-f56c11` (identical `--day 2026-07-05 --asset-group DEFI --legs
   force,skip --require-captured --auto-day` invocation), confirmed `e2-highmem-16` / `PREEMPTIBLE=` (blank —
   NOT spot, ruling out preemption and supporting the OOM-kill inference) / `STATUS=RUNNING` via the launcher's
   own `gcloud compute instances create` output. The cross-leg retention fix is now shipped: `gc.collect()` runs
   after the force and skip legs so their poll-loop/log-buffer objects are reclaimed before the next leg —
   `market-data-processing-service@4990d2361`. The large peak-RSS value remains a historical `ru_maxrss` maximum,
   not a claim that live RSS is still growing.
- [x] ✅ [SCRIPT] P2. Explicit per-leg garbage collection landed in
      `market-data-processing-service@4990d2361`; `_run_shard_batch_legs` calls `gc.collect()` after force and skip
      execution, preventing leg-over-leg retention without changing the canonical matcher or launching a second
      subprocess.

## Progress Log
- **2026-08-21 — stale P2 corrected:** direct code read and git blame verified 4990d2361 already shipped per-leg gc.collect() on 2026-08-20; the prior open checkbox and Real fix still needed prose were stale and are closed with commit evidence.

- **2026-08-19** (`/plan-reconcile security_and_cross_cutting_master` Phase 2.4, zero-checkbox sweep): this entire
  "Recommended decision" list used numbered-prose format (`1. `[TAG] P1.` ...`) instead of canonical `- [ ] [TAG]
  P<n>.` checkboxes — invisible to every mechanical checkbox scanner (`check_todo_format.sh`,
  `count_open_tasks.py`, AO backlog regen) despite carrying 2 genuinely open items (3, 4) plus one more extracted
  from item 5's own prose tail (now the new item above). Converted items 3, 4 to `- [ ]`; items 1, 2 already
  carried explicit ✅ DONE markers and item 5's completed relaunch action was left as historical numbered narrative
  (its own still-open remainder extracted to the new item above). No content changed beyond the format/visibility
  fix — the doc's own claims were not re-verified this pass; whoever picks up item 4 should first check whether
  the 2026-08-17 02:42 UTC relaunch (`pipeline-e2e-check-mdps-20260817-024215-f56c11`) reached a terminal verdict
  before assuming it's still pending.
- **context-scout 2026-08-17**: populated context_scope (5 entries).
- **context-scout 2026-08-20**: refreshed context_scope (5 entries).
- **2026-08-20 (slot-7, quant_dev)**: item 3 DONE — closed as already-shipped-and-verified, not re-implemented. Direct
  code reads of both repos on origin/live-defi-rollout confirmed: the MDPS driver
  (`market-data-processing-service@6ee153a0`) removed `_read_input_index_frame` and re-pointed `_captured_days_by_cell`
  at UTL's streamed `read_captured_days_by_cell` with a 400-day `min_day` lookback bound; the UTL engine
  (`unified-trading-library@11f1ebd1`) streams the consolidated index one row-group batch at a time (131072 rows/batch,
  per-batch `min_day` filter, bounded legacy fallback) so peak memory no longer scales with the manifest's total row
  count — the next AG whose manifest outgrows DeFi's current 160M rows will not re-hit the driver OOM ceiling. The
  old full-read path is fully gone from the driver (only a docstring reference remains). Checkbox flipped with evidence
  in the same commit.
