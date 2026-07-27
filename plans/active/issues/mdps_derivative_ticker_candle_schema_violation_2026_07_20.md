---
doc_type: issue
title:
  P0 — MDPS derivative_ticker candle derivation is 100% BROKEN (StreamingParquetWriter schema violation, every
  timeframe, every instrument) and the VM still exits rc=0 reporting "20 success, 0 failed"
summary: >-
  Caught on the FIRST real run of the new /data-pipeline-check-mdps skill. A forced CeFi DERIBIT derivative_ticker
  candle derivation for 2024-02-08 read its 20 raw input files, computed 152,300 candles, then failed EVERY parquet
  write with StreamingParquetWriter pre-write validation failed - [schema_violation] column 'funding_rate_mean' /
  'mark_price_mean' / 'index_price_mean' missing from dataframe. Result - ZERO candle objects written, 140 manifest rows
  (7 timeframes x 20 instruments) all attempted_failed/SCHEMA_VALIDATION_FAILED with row_count=0. The honest-absence
  contract HELD (no phantom captured rows), but two things are badly wrong - (1) the derivative_ticker candle
  aggregation does not emit the three perp columns its own schema contract requires, so no derivative_ticker candle can
  be produced at all, and (2) the run reported SUCCESS - VM exit rc=0, run.log summary "cefi 45.1s 20 success 0 failed 0
  skipped 152,300 candles", DEPLOYMENT_COMPLETED exit_code=0 - so a backfill of this data_type would burn full compute,
  write nothing, and look green to every exit-code-based monitor. This directly blocks the candle backfill for
  derivative_ticker (a CeFi/DeFi MVP data_type carrying funding_rate) and invalidates any ETA that assumes the path
  works.
status: open
nature: issue
asset_group: [cefi, defi]
stage: [data]
repos: [market-data-processing-service, unified-trading-library, unified-api-contracts]
scope: [engineer, admin]
tags: [data-correctness, p0, mdps, candles, schema, derivative_ticker, silent-failure, backfill-blocker]
related:
  [
    ../data_pipeline_check_mdps_features_2026_07_20.md,
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.4
assigned_role: data
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  first real-VM run of /data-pipeline-check-mdps, 2026-07-20. VM mdps-backfill-cefi-pipelinecheck-20260720-130757-a63425
  (and its skip twin -pcskip-20260720-131345-a63425). Writes were test-bucket-routed; PROD was verified untouched.
---

# P0 — MDPS `derivative_ticker` candle derivation is 100% broken, and reports success

> Found by the new `/data-pipeline-check-mdps` skill on its first real run. The skill's `failed` verdict was CORRECT
> where the VM's own exit code said success — which is precisely the class of bug an exit-code-trusting monitor misses.

## Evidence (real VM, test-bucket-routed, PROD verified untouched)

VM `mdps-backfill-cefi-pipelinecheck-20260720-130757-a63425`, `cefi 2024-02-08 → 2024-02-08 --force`,
`--data-types derivative_ticker --venues DERIBIT`, output routed to `market-data-tick-cefi-test-central-element-323112`.

**Input was fine:**

```
Listed 20 files from market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2024-02-08/ for data_type=derivative_ticker
📝 Processing 20 files (0 skipped)
```

**Every write failed:**

```
ERROR Error writing candles to GCS: StreamingParquetWriter pre-write validation failed:
  [schema_violation] column 'funding_rate_mean' missing from dataframe;
  [schema_violation] column 'mark_price_mean'  missing from dataframe;
  [schema_violation] column 'index_price_mean' missing from dataframe
```

**Yet the run reported success:**

```
cefi   45.1s   20 success   0 failed   0 skipped   152,300 candles
TIMING BENCHMARKS:  cefi: 2105ms per instrument (42.1s total)
[vm-exec] command exited rc=0
DEPLOYMENT_COMPLETED … (exit_code=0)
```

**Ground truth — objects vs manifest:**

| surface                                                    | result                                                            |
| ---------------------------------------------------------- | ----------------------------------------------------------------- |
| candle objects in the `-test-` bucket for `day=2024-02-08` | **0** (`CommandException: One or more URLs matched no objects`)   |
| manifest rows written (per-VM shard)                       | **140** = 7 timeframes × 20 instruments                           |
| `capture_status` distribution                              | **`attempted_failed` × 140** (`row_count=0`)                      |
| `error_reason`                                             | **`SCHEMA_VALIDATION_FAILED` × 140**                              |
| timeframes                                                 | `15s,1m,5m,15m,1h,4h,1d` — 20 each (confirms the `24h`→`1d` norm) |
| PROD objects modified today                                | **none** — no test-isolation leak                                 |

Reproduced identically on the skip-leg VM (`…-pcskip-…`): `45.4s, 20 success, 0 failed, 152,300 candles`, same failure.

## The two defects

### 1. Schema violation — the aggregation doesn't emit the columns its contract requires (P0, backfill blocker)

The `derivative_ticker` candle dataframe is missing `funding_rate_mean`, `mark_price_mean`, `index_price_mean`. These
are the perp-specific fields (`funding_rate` is carried on `derivative_ticker` per the
`CEFI_PERPETUAL_DERIVATIVE_TICKER` schema contract). The `StreamingParquetWriter` runs `strict=True` pre-write
validation against the UAC `SchemaContract` and correctly refuses the write — so **no `derivative_ticker` candle can be
produced at all, at any timeframe, for any instrument.** Either the aggregator lost these columns, or the contract
gained them without the aggregator following.

**Impact on the backfill:** `derivative_ticker` is an MVP data_type for CeFi (`PERPETUAL`) and appears in the DeFi
enumeration too. Any full-history candle backfill run today would consume the full compute budget for this data_type and
write **nothing**, while every exit-code-based monitor reports success. **Any ETA that assumes this path works is
invalid until this is fixed.**

### 2. The run reports success when every write failed (P0, observability)

`20 success / 0 failed`, `rc=0`, `DEPLOYMENT_COMPLETED exit_code=0` — with 140 `attempted_failed` rows and zero objects.
The per-instrument "success" counter evidently counts _processed_ instruments, not _written_ ones, and the write error
is caught + recorded without failing the shard or the run. This is the workspace's "looks green where I looked" failure
class: a fleet-wide backfill would burn its whole budget and self-report healthy.

**Fix direction:** a shard whose every write failed must exit non-zero (or at minimum the summary must report
`0 written / 20 failed`), so the launcher/watchdog and any cron see the failure. The manifest already tells the truth —
the exit code and the summary line do not.

## What WORKED (do not regress these)

- **Honest-absence contract held**: failures recorded as `attempted_failed` + `SCHEMA_VALIDATION_FAILED`, `row_count=0`
  — NOT a phantom `captured`. The manifest is trustworthy here.
- **Test isolation held**: `--output-bucket` routed both the parquet attempt and the manifest to the `-test-` bucket;
  PROD was verified unmodified.
- **`--auto-day` worked**: no captured input on the requested 2026-07-15, so it substituted 2024-02-08 (a real captured
  day) instead of proving nothing.
- **The new skill caught it**: force verdict `failed` with
  `no_candle_under:gs://…-test-…/processed_candles/by_date/day=2024-02-08/`, against a VM that claimed success.

## Todos

> ## ✅ WRITE-PATH P0 RESOLVED 2026-07-20 ~23:50Z — proven end-to-end on a real VM
>
> The derivative_ticker candle WRITE path is FIXED: three chained fixes (adapter `mdps@beea161` → UAC propagation
> `deployment@e978f32d` → the pre-upload nullability fix `mdps@d4052e20b`) took a cell from **0 objects / 140
> `attempted_failed`** to **140 objects written / 140 `captured` manifest rows / 152,300 candles / 0 errors / no schema
> failures** (VM `…-224318-a63425`, day 2024-02-08, verified: 140 `.parquet` in the -test- bucket + the per-VM shard
> read via pyarrow = all `captured`, `data_type=deriv_ohlcv_15m`, `row_count=96`). Root cause was NOT a UAC key mismatch
> (my first hypothesis) but the MDPS pre-upload validator gating OHLC-nullability on category — corrected + verified by
> adversarial workflow w6kkdobay. **Todos 1 + 5 DONE.** Remaining (lower priority, separate concerns): todo 2
> (exit-code-lies observability), todo 3 (sweep other candle types — the fix already covers them via the shared seam,
> but a proof-sweep is prudent), todo 4 (driver reads consolidated not per-VM shard — the ONLY reason the skill still
> shows "failed" on a fully-successful write).

- [x] 1. ✅ [DATA] P0. DONE (mdps@beea161 adapter + mdps@d4052e20b nullability). The adapter emits
      `funding_rate_mean`/`mark_price_mean`/`index_price_mean` + leaves empty-window OHLC NaN (LOCF removed) per the
      operator's honest-absence ruling; the pre-upload validator now inherits per-type OHLC nullability from the UAC
      SSOT so the honest-absence NaN OHLC is accepted. Proven end-to-end: 140 objects + 140 `captured` rows (was 0). See
      the RESOLVED banner + addendum below.

## ADDENDUM 2026-07-20 ~22:45Z — the write STILL fails after the adapter + UAC fix: an ENFORCER KEY MISMATCH

A loop-closing real-VM re-run (VM `…-213641-a63425`, UAC pinned to `ad317c32`, a git-proven descendant of the
`nullable_ohlcv=True` fix `uac@8e58b009`; boot assertion did NOT fire → correct editable UAC installed) STILL failed:
`SCHEMA_VALIDATION_FAILED: Column 'open' has N NaN/null values but is NOT NULLABLE for data_type=derivative_ticker`
(open/high/low/close, "Skipping upload"), 0 objects written, EXIT_STATUS=0, "20/20 succeeded". **Not a propagation
failure** — the correct UAC is on the VM.

**The nullable_ohlcv fix was applied to a contract key the writer never queries.** The enforcer
(`unified_trading_library/core/parquet_schema_enforcer.py`) resolves OHLC nullability via
`SchemaDefinition.get_nullable_columns(dimensions)` keyed on `dimensions["data_type"]`; the failing dimension is
`data_type=derivative_ticker` (the SOURCE type). But `uac@8e58b009` set `nullable_ohlcv=True` on the registration keyed
`_deriv_key(_tf)` = `deriv_ohlcv_{tf}` (the AGGREGATED type — `_candle_contracts.py:186,318`). So the MDPS candle write
path hands the enforcer the SOURCE `data_type`, the aggregated-key nullable contract is never matched, OHLC is enforced
non-nullable, and the honest-absence NaN rows are rejected. This is the SAME path≠manifest divergence
(`candle_feature_canonical_path_divergence_2026_07_20.md` finding #2) manifesting on the VALIDATION path.

The precise fix + blast radius (does `trades`/`book_snapshot_5`/`liquidations`/chain ALSO mis-key, or only
derivative_ticker? why do trades candles currently succeed?) is under adversarial workflow investigation (w6kkdobay).
Two candidate fixes: (A) MDPS passes the AGGREGATED key `mdps_data_type_key(src,tf)` as the enforcer `data_type`
dimension (aligns validation with the manifest key + registered contract); (B) UAC also registers the nullable candle
contract under the SOURCE key as an alias. The workflow chooses + verifies before any code change.

- [ ] 2. [DATA] P0. Make a run whose every write failed EXIT NON-ZERO (and fix the `N success / 0 failed` summary to
      count _written_, not _processed_). Today a 100%-failed shard reports `rc=0` + "20 success".
- [ ] 3. [DATA] P1. Sweep the OTHER candle data_types for the same class of contract drift before the backfill
      (`trades`, `book_snapshot_5`, `liquidations`, `options_chain`, `futures_chain`, the DeFi set). A scoped
      `/data-pipeline-check-mdps --legs force --require-captured --auto-day` per data_type is exactly the tool.
- [x] 4. ✅ [SCRIPT] P2. DONE (utl@69ff7fee + mdps@8890508) — **EXACT root cause + fix pinned 2026-07-21** (now the ONLY
      reason the skill reports "failed" on a fully-successful write). The force-leg manifest verify
      (`_verify_tf_output`, scripts/pipeline_e2e_check.py:1057) calls the engine
      `verify_manifest_row(bucket, match, day)` which reads the **MERGED** index (`read_availability_index` merges
      consolidated + ALL per-VM shards) and takes `.iloc[-1]` — so when a cell has BOTH a stale `attempted_failed` row
      (pre-fix runs 205051/213641) AND the fresh `captured` row (this run), the dedup/ordering can return the STALE one
      → `manifest_status_invalid:attempted_failed` even though 140 objects wrote and this VM's OWN per-VM shard is
      140/140 `captured` (proven 2026-07-21). The canonical leg already avoids this by reading the leg VM's own shard
      via `_canonical_leg_frame(bucket, force_vm_name)` → `_read_per_vm_shard_frame`. **FIX**: (a) add a public engine
      helper `verify_manifest_row_in_frame(frame, match,     date)` in
      `unified_trading_library/pipeline_e2e_check/shard_verify.py` (refactor the existing match+status body of
      `verify_manifest_row` into it, so the SSOT match logic + `_ACCEPTABLE_CAPTURE_STATUSES` stay in one place); (b) in
      `_verify_tf_output`, thread `force_vm_name` (available as `force.vm_name`, exactly as `_run_canonical_leg` does at
      :1486) and read `_read_per_vm_shard_frame(bucket, force_vm_name)` FIRST — if non-empty, use
      `verify_manifest_row_in_frame`; else fall back to `verify_manifest_row`. Verifiable with a UNIT test (mock a
      per-VM frame `captured` + the consolidated `attempted_failed`, assert the force leg returns ok=True) — NO VM
      re-run needed. Same fix retroactively fixes the trades-smoke `no_matching_row` (consolidated hadn't consolidated
      the fresh shard yet). MTDS twin's `_read_per_vm_batch_row` is the reference pattern.
- [x] 5. ✅ [DATA] P0. DONE — mdps@d4052e20b. The workflow (w6kkdobay) CORRECTED the hypothesis: it was NOT a
      source-vs-aggregated key mismatch but the MDPS pre-upload validator (`candle_write_mixin.py:604` +
      `data_sink.py:118` via `get_schema_for_data_type`) gating OHLC-nullability on CATEGORY (prediction/sports only),
      so cefi honest-absence NaN OHLC was rejected BEFORE the correctly-nullable UAC write seam. Fix: the validator now
      inherits per-type nullability from the UAC SSOT (`mdps_ohlc_is_nullable[_for_frame]` → `lookup_mdps_contract` →
      `open.nullable`), NOT category — book5/state STAY non-nullable automatically (zero regression), lookup-miss →
      category fallback (never raises). Since both validators share `get_schema_for_data_type`, the single seam fixes
      the whole class (subsumes todo 3 for the write path; a proof-sweep of trades/swaps/tradfi-ohlcv is still prudent).
      12 new tests (book5-stays-non-nullable + empty-window-passes + positive-aggregation). Proven end-to-end: 140
      objects + 140 `captured` rows on the re-run VM.
