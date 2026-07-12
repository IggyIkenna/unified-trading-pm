---
doc_type: issue
title:
  CeFi adapter bugs found via a full 452-shard pipeline_e2e_check sweep — ASTER instrument_id validation, HYPERLIQUID
  epoch-timestamp bug, BITGET-FUTURES/BITFINEX-FUTURES shared datetime64-vs-date comparison error
summary:
  "Found 2026-07-12 while triaging the 291 genuine 'no data written' results from a full 452-shard IS+MTDS smoke sweep
  (unified-trading-pm/plans/active/data_pipeline_e2e_check_2026_07_10.md). Sampled real VM run.log evidence for 4 CeFi
  venues whose MTDS force leg failed across ALL their own data_types (not just one), ruling out the already-documented
  ASTER book_snapshot_5 REST-limitation as the explanation. Three distinct, real bugs: (1) ASTER fails on `trades` too
  (not just book_snapshot_5) with a StreamingParquetWriter schema-validation error (missing_column: instrument_id) --
  broader than the previously-documented gap. (2) HYPERLIQUID trades: adapter received real ticks but every timestamp
  parsed to Unix epoch (1970-01-01) -- a genuine timestamp-parsing bug, distinct from the already-documented HL
  under-capture/liquidations issues. (3) BITGET-FUTURES and BITFINEX-FUTURES both fail with the IDENTICAL error 'Invalid
  comparison between dtype=datetime64[ns] and date' -- a shared Python type-comparison bug in whatever
  normalization/filter code these two venues' adapters share."
status: open
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, adapter-bugs, aster, hyperliquid, bitget-futures, bitfinex-futures, smoke-test, data-correctness]
related:
  [
    ../data_pipeline_e2e_check_2026_07_10.md,
    cefi_hl_aster_batch_data_gaps_2026_06_22.md,
    mtds_is_full_adapter_smoketest_findings_2026_07_07.md,
  ]
created: 2026-07-12
parent_epic: mtds_mdps_master
priority: P2
source: [pipeline_e2e_check full 452-shard sweep, day=2026-07-09, real VM run.log evidence]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.7
assigned_role: data-pipeline-engineer
drift_direction: unknown
depends_on: []
---

# CeFi adapter bugs found via a full pipeline_e2e_check sweep

## Context

`data_pipeline_e2e_check_2026_07_10.md`'s full 452-shard sweep (108 IS + 344 MTDS, day=2026-07-09) surfaced 344 MTDS
shards; grouping the force-leg failures by venue showed several CeFi futures venues failing across ALL of their own
data_types (not one isolated data_type), which doesn't match the already-documented, single-data_type ASTER
`book_snapshot_5` REST-current-book-only gap (`cefi_hl_aster_batch_data_gaps_2026_06_22.md`). Pulled real VM `run.log`s
for the force leg of each to get the actual underlying exception, not the checker's abstracted `no_parquet_under` reason
string.

## Finding 1 — ASTER `trades` fails too, not just `book_snapshot_5`

VM `mtds-backfill-cefi-pipelinecheck-20260712-043802`:

```
ERROR Venue ASTER: adapter error: StreamingParquetWriter pre-write validation failed: [missing_column] required column 'instrument_id' missing from dataframe
WARNING market-tick-data-service: SHARD_INCOMPLETE date=2026-07-09 asset_group=CEFI — expected 1 venues, wrote 0, missing: ['ASTER']
```

This is the SAME error signature the earlier session found for `book_snapshot_5` (traced then to the REST
current-book-only limitation) — but here it's on `trades`, a completely different, mainstream data_type that has no
known architectural limitation. `cefi_hl_aster_batch_data_gaps_2026_06_22.md`'s own historical manifest breakdown shows
ASTER `trades` at 62% captured overall, so this is not a total, permanent failure — but it IS a real,
currently-reproducing failure on at least this one day, worth checking whether it's the SAME missing-`instrument_id`
mechanism the book_snapshot_5 case hits, or a coincidentally-identical error from a different code path (e.g., the
`--instrument-ids` value this smoke check sampled — a `smoke_matrix` fallback symbol, since no PROD-captured row existed
for this day — may not be a real, currently-listed ASTER symbol, and the adapter might be silently returning an
empty/malformed dataframe for an unrecognized symbol instead of a clean "not found" error).

**Not yet determined**: whether this is a genuine ASTER adapter regression, or an artifact of the smoke check's fallback
instrument-id sampling picking a symbol ASTER doesn't actually support. Re-testing with a real, PROD-verified-live ASTER
symbol (not the smoke_matrix fallback) would distinguish these.

**RESOLVED 2026-07-12 (slot-3) — genuine adapter bug, confirmed + fixed, NOT a fallback-symbol artifact.** Traced the
actual write path: the smoke check's VM name (`mtds-backfill-cefi-pipelinecheck-*`, `asset_group=CEFI`) routes ASTER
through `market_tick_data_service/adapters/umi_tick_provider.py`'s inline REST fetchers
(`_fetch_aster_coin`/`_fetch_aster_agg_trades`) — NOT the class-based `AsterAdapter` in
`market_interface/adapters/onchain_perps/aster_adapter.py` (that class is only reachable via the separate
`onchain_perp_batch_handler.py` CLI). `_fetch_aster_agg_trades`'s `trades` row dict (and `_fetch_aster_coin`'s
`derivative_ticker` funding/premiumIndex row dicts) never included an `instrument_id` key — confirmed via `git blame`/
history back to the function's introduction (pre-2026-06-11 refactor) — while every sibling REST-adapter producer in the
SAME file (PACIFICA-SOLANA OHLCV, LIGHTER, EXTENDED, HYPERLIQUID via `hyperliquid_s3.py`, FX/VIX) DOES stamp
`instrument_id`. `StreamingParquetWriter._run_pre_write_checks` calls `validate_instrument_id_column(df)`
UNCONDITIONALLY on every `write_chunk()` (no `expected_venue`/`expected_instrument_type` — just presence + non-null), so
this was a 100%-deterministic failure on ANY non-empty ASTER `trades`/`derivative_ticker` write, regardless of which
symbol (valid or fallback) triggered it — the exact same root-cause class HYPERLIQUID hit and was fixed for on
2026-04-22 (`hyperliquid_s3.py`'s own docstring cites the identical error signature + fix pattern).

**Fix**: stamp `"instrument_id": symbol` (+ `"instrument_type": "perpetual"`) on all 3 ASTER REST row-dict producers in
`umi_tick_provider.py` (funding-rate rows, premiumIndex row, aggTrades trade rows), mirroring the proven HYPERLIQUID
convention (bare canonical `symbol` as `instrument_id` — no `partition_path=` is passed to this writer, so only
presence/non-null is checked, not the `VENUE:TYPE:SYMBOL` prefix format). Shipped
`market-tick-data-service@99ac3d648ef8ce84954a317ded04746804d79618`
(`fix(mtds): stamp instrument_id/instrument_type on ASTER REST trades+funding rows`), `quality-gates.sh --no-fix` green
before commit, quickmerged `--agent` scoped to the one file.

**Real VM re-verification (proves the fix, not just the diagnosis)** — same VM launcher, same fallback symbol/day the
original bug reproduced on
(`--venues ASTER --data-types trades --start 2026-07-09 --end 2026-07-09 --instrument-ids BTC --force --test-run`),
tarball rebuilt from a clean worktree at the fix commit before each run:

- **Before fix** (VM `mtds-backfill-cefi-pipelinecheck-20260712-222538-03d933`, tarball at pre-fix HEAD):
  `ERROR Venue ASTER: adapter error: StreamingParquetWriter pre-write validation failed: [missing_column] required column 'instrument_id' missing from dataframe`
  — byte-identical to the original Finding 1 signature. Reproduced on demand, confirming the bug before touching code.
- **After fix** (VM `mtds-backfill-cefi-pipelinecheck-20260712-224403-03d933`, tarball rebuilt at `99ac3d64` from a
  clean `git worktree` — the live worktree was dirty with two other agents' concurrent Finding-2/3 WIP, so the tarball
  was built from a throwaway clean checkout instead of forcing `--allow-dirty-tarball`): the `missing_column`
  `instrument_id` error is GONE. In its place: `derivative_ticker` (the sibling data_type stamped by the SAME 3-producer
  fix) wrote 3 REAL rows successfully —
  `StreamingParquetWriter: uploaded .../data_type=derivative_ticker/BTCUSDT.parquet (3 rows, 1 chunks, 0.0 MB)` —
  direct, positive proof the fix's mechanism works end-to-end (instrument_id populated, write succeeds). `trades` itself
  produced 0 rows this run because the ONE real BTCUSDT tick ASTER returned for the fallback symbol fell outside
  2026-07-09 (`UpstreamTimestampBiasError: observed_range=[2026-07-12..2026-07-12], n_ticks_seen=1`) — an unrelated,
  pre-existing day-alignment guard hitting a data-availability/liquidity limitation of the SMOKE-MATRIX FALLBACK symbol
  on THIS specific day, not the fixed bug.
- **Real-symbol, real-day cross-check** (day=2026-01-03, a day `read_availability_index` confirms ASTER `trades`
  genuinely captured PROD data on): passing the bare coin `APR` (25 real ticks observed, real trade volume) still hit a
  (different, pre-existing) `UpstreamTimestampBiasError` — some ticks legitimately spill past midnight into 2026-01-04,
  tripping the day-partition-alignment guard. Passing the checker's OWN genuine-PROD-sample value verbatim (the full
  canonical `instrument_id` string `ASTER:PERPETUAL:APR-USDT@LIN`) produced a SILENT 0-row/0-error outcome — see the two
  new follow-on findings logged below. Across all 3 real VM runs (2 symbols, 2 days), the ORIGINAL
  `missing_column instrument_id` error never reproduced again post-fix — conclusive.

**Verdict on the original open question**: genuine, 100%-reproducing ASTER adapter bug (proven via code history + direct
before/after VM reproduction), NOT a smoke-check fallback-symbol artifact — the missing-`instrument_id` failure was
orthogonal to symbol validity; a real, valid, high-volume symbol/day pairing surfaces different (pre-existing,
unrelated) day-alignment issues instead, never the fixed bug.

**Two new, out-of-scope follow-on findings surfaced while chasing an end-to-end `trades: passed` proof** (not fixed here
— flagging for a future pass, same file family):

1. `scripts/pipeline_e2e_check.py::sample_live_instrument()` passes the full canonical `instrument_id`
   (`VENUE:TYPE:SYMBOL@LIN`) verbatim as `--instrument-ids` whenever a genuine PROD-captured row exists (vs the
   `smoke_matrix` fallback path, which correctly passes a bare representative coin). ASTER's (and likely
   HYPERLIQUID's/other bare-coin-list REST venues') `_fetch_aster_rest` blindly appends `USDT` to whatever string it's
   given (`f"{coin}USDT"` when it doesn't already end in USDT/USDC/USD) with no VENUE:TYPE: prefix stripping — so a full
   canonical instrument_id becomes a garbage exchange symbol, the REST call 400s, and the failure is swallowed at
   `logger.debug` (invisible at INFO) — a completely silent 0-row/0-error/0-failed outcome
   (`0 venues ok, 0 failed, 0 skipped, 0 total records`), never surfaced to the checker's `no_parquet_under` reason
   string. Verified live: VM `mtds-backfill-cefi-pipelinecheck-20260712-225444-03d933`,
   `--instrument-ids ASTER:PERPETUAL:APR-USDT@LIN` → silent no-op.
2. Even with a correctly-formatted bare-coin symbol on a real high-volume day (`APR`, 2026-01-03, 25 real ticks),
   `_fetch_aster_agg_trades` let at least one tick spill past the requested day's midnight boundary, tripping
   `UpstreamTimestampBiasError: observed_range=[2026-01-03..2026-01-04]` (VM
   `mtds-manual-aster-trades-verify-20260712-230013`) — a different-mechanism sibling of Finding 2's HYPERLIQUID
   epoch-timestamp bug, worth a dedicated look at the `end_ms` exclusivity boundary in that pagination loop.

## Finding 2 — HYPERLIQUID `trades`: ticks land at Unix epoch

VM `mtds-backfill-cefi-pipelinecheck-20260712-043606`:

```
ERROR Venue HYPERLIQUID: adapter error: UpstreamTimestampBiasError: expected_day=2026-07-09, observed_range=[1970-01-01..1970-01-01], n_ticks_seen=24 — adapter received ticks but ALL fell outside the requested day after interval filter (upstream partition mislabeled or source replay window wrong)
```

24 real ticks were received from upstream, but every one's parsed timestamp landed at the Unix epoch (1970-01-01) —
consistent with a units mismatch (e.g. treating a raw integer field as seconds when it's actually
milliseconds/microseconds/nanoseconds, or reading a genuinely-null/zero timestamp field) rather than a connectivity
issue. `UpstreamTimestampBiasError` is a real, structured error class already built into the adapter (not an unhandled
exception) — suggesting this failure mode is anticipated but the underlying units/field bug producing it hasn't been
fixed. Distinct from the already-documented HL under-capture (BUG #2) and liquidations-misclassification (BUG #3) issues
in `cefi_hl_aster_batch_data_gaps_2026_06_22.md` — this is a new, third HL issue.

## Finding 3 — BITGET-FUTURES + BITFINEX-FUTURES: identical datetime64-vs-date comparison error

VM `mtds-backfill-cefi-pipelinecheck-20260712-043304` (BITGET-FUTURES) and VM
`mtds-backfill-cefi-pipelinecheck-20260712-043209` (BITFINEX-FUTURES), both `trades`:

```
ERROR Venue BITGET-FUTURES: unexpected error (shard isolated): Invalid comparison between dtype=datetime64[ns] and date
ERROR Venue BITFINEX-FUTURES: unexpected error (shard isolated): Invalid comparison between dtype=datetime64[ns] and date
```

Byte-identical error text across two different venues strongly suggests a shared code path (a common
normalization/date-filter helper both adapters call) doing `pandas_timestamp_series == some_datetime.date()` or similar
without coercing both sides to the same type first — a real, mechanical pandas/Python bug, not a data- availability
issue. Since the error is identical for both venues, fixing the shared code path should resolve both at once. Not yet
traced to the exact call site — `rg "Invalid comparison between dtype"` or a stack-trace capture (the run.log only shows
the caught/logged message, not a full traceback, since this is caught via the shard-level isolation wrapper per
`codex/04-architecture/shard-level-failure-isolation.md`) would be the next step.

## Not yet investigated

The full sweep found ~135 total MTDS force-leg `no_parquet_under` failures across many more venues/data_types than
covered here — only these 4 venues (ASTER, HYPERLIQUID, BITGET-FUTURES, BITFINEX-FUTURES) were sampled for real run.log
evidence in this pass, chosen because they showed 100% failure across ALL their own data_types (the strongest signal for
a venue-level, not data_type-level, issue). The remaining un-sampled failures (other CeFi venues' partial failures, most
DEFI venues, remaining TradFi data_types beyond the already-fixed `--source` gap) are tracked as
`data_pipeline_e2e_check_2026_07_10.md` todo 25 — not yet triaged venue-by-venue.

## Progress log

- 2026-07-12: Filed from a real 452-shard `pipeline_e2e_check` sweep's failure-breakdown analysis. 3 real, distinct bugs
  found via actual VM run.log sampling (not guessed from the checker's abstracted reason string). No fix attempted here
  — this doc exists to hand off the diagnosis, not resolve it in this session.
- 2026-07-12 (slot-3): **Finding 1 RESOLVED + shipped** —
  `market-tick-data-service@99ac3d648ef8ce84954a317ded04746804d79618` stamps `instrument_id`/`instrument_type` on all 3
  ASTER REST row-dict producers in `umi_tick_provider.py`
  (`fix(mtds): stamp instrument_id/instrument_type on ASTER REST trades+funding rows`). Confirmed genuine adapter bug
  (not fallback-symbol artifact) via code-history inspection (every sibling producer in the same file stamps
  `instrument_id`; ASTER's 3 never did, since the function's introduction) + 3 independent real VM runs proving
  before→after: (1) VM `mtds-backfill-cefi-pipelinecheck-20260712-222538-03d933` reproduced the exact original
  `missing_column instrument_id` error pre-fix; (2) VM `mtds-backfill-cefi-pipelinecheck-20260712-224403-03d933` (SAME
  symbol/day, tarball rebuilt at the fix commit via a clean `git worktree` to avoid 2 other agents' concurrent dirty WIP
  in the same repo) shows that error GONE, with the sibling `derivative_ticker` data_type writing 3 real rows with
  `instrument_id` populated as direct proof; (3) VM `mtds-manual-aster-trades-verify-20260712-230013` (real
  PROD-verified day=2026-01-03 + real symbol `APR`, 25 real ticks) again never reproduces the fixed bug, surfacing only
  unrelated day-boundary issues instead. Full before/after run.log evidence + 2 new out-of-scope follow-on findings
  (checker instrument-id-format mismatch for bare-coin REST venues; an ASTER day-boundary off-by-one distinct from
  Finding 2) written up under Finding 1 above. `quality-gates.sh --no-fix` green before commit; shipped via
  `quickmerge --agent` scoped to the one file; all 3 verification VMs self-deleted cleanly (exit_code=0), no lingering
  compute.
