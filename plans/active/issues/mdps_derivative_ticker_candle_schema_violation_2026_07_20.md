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
related: [../data_pipeline_check_mdps_features_2026_07_20.md, candle_feature_canonical_path_divergence_2026_07_20.md]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
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

- [ ] 1. [DATA] P0. Root-cause the missing `funding_rate_mean` / `mark_price_mean` / `index_price_mean` in the
      `derivative_ticker` candle aggregation (CeFi `DerivativeTickerAdapter` → `write_candle_parquet` →
      `StreamingParquetWriter` strict validation vs the `CEFI_PERPETUAL_DERIVATIVE_TICKER` contract). Either restore the
      columns in the aggregator or reconcile the contract. **Blocks the derivative_ticker candle backfill.**
- [ ] 2. [DATA] P0. Make a run whose every write failed EXIT NON-ZERO (and fix the `N success / 0 failed` summary to
      count _written_, not _processed_). Today a 100%-failed shard reports `rc=0` + "20 success".
- [ ] 3. [DATA] P1. Sweep the OTHER candle data_types for the same class of contract drift before the backfill
      (`trades`, `book_snapshot_5`, `liquidations`, `options_chain`, `futures_chain`, the DeFi set). A scoped
      `/data-pipeline-check-mdps --legs force --require-captured --auto-day` per data_type is exactly the tool.
- [ ] 4. [SCRIPT] P2. `/data-pipeline-check-mdps` driver improvement: the force-leg manifest verify currently reads the
      CONSOLIDATED index and reported the uninformative `no_matching_row`, when the leg VM's own per-VM shard held
      `attempted_failed/SCHEMA_VALIDATION_FAILED` (Phase-0 consolidated at 13:05; the VM wrote its shard at 13:12). Read
      the leg VM's OWN per-VM shard first (concurrency-immune), exactly as the MTDS twin's `_read_per_vm_batch_row`
      does, so the report surfaces the actionable error_reason.
