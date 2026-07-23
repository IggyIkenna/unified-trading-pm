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
status: resolved
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, adapter-bugs, aster, hyperliquid, bitget-futures, bitfinex-futures, smoke-test, data-correctness]
related:
  [
    ../data_pipeline_e2e_check_2026_07_10.md,
    /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
    /plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md,
  ]
created: 2026-07-12
parent_epic: mtds_mdps_master
priority: P2
source: [pipeline_e2e_check full 452-shard sweep, day=2026-07-09, real VM run.log evidence]
assigned_vm: NA
resolved_by: slot-3, close_remaining_e2e_bugs workflow 2026-07-13
locked_by:
execution_scope: local-only
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.7
assigned_role: data_engineering
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

**RESOLVED 2026-07-12/13 — genuine units-mismatch bug, confirmed + fixed + real-VM verified.** Root cause:
`market_tick_data_service/adapters/hyperliquid_s3.py`'s `_parse_node_fills` (trades), `_parse_asset_ctxs_csv` (funding),
and `_build_funding_ticker` (REST funding) all emit the raw Hyperliquid `time` field as a bare epoch- MILLISECOND `int`
in the row dict's `"timestamp"` key (only `_parse_l2_book_line` already converted it to a proper tz-aware `datetime`,
which is why `book_snapshot_5` never hit this bug). The classic MTDS download-orchestrator path
(`umi_tick_provider.py::_fetch_hyperliquid_s3` → `PartitionedTickWriter.write_chunk` → `_prepare_write_df`) builds a
`pd.DataFrame` straight from that raw dict list, then calls `raw_tick_hive.validate_day_partition_alignment` →
`pd.to_datetime(timestamps, utc=True)` with NO `unit=` argument — pandas' default unit for a bare-int Series is
NANOSECONDS, so a genuine 2026 ms-epoch value (~1.75e12) is read as ~1.75 SECONDS past epoch, collapsing every row onto
1970-01-01 and tripping the day-partition guard. (A newer, separate path —
`cli/handlers/onchain_perp_batch_handler.py::_rows_to_canonical_df`, added 2026-06-21 for the
`collect-onchain-perp-batch` operation — already has an explicit `unit="ms"` fix, which is why this bug wasn't caught
everywhere; the classic `download` operation the real force-refetch VM actually exercises did not.)

**Fix**: `_clip_rows_to_day` already computes the correct tz-aware UTC `datetime` per row (via `_row_ts_utc`) purely to
decide keep/drop, then discarded that parsed value and returned the raw int. Changed it to write the already-parsed
`datetime` back onto each surviving row's `timestamp` field, so every HL S3 producer
(trades/asset_ctxs/l2Book/funding-via-REST) now hands the writer an unambiguous datetime regardless of the raw upstream
unit — matching what `_parse_l2_book_line` already did. Shipped
`market-tick-data-service@db6356327a9bdc47c4caeb78a035ca61ae9bfe16`
(`fix(mtds): convert HYPERLIQUID S3 trades timestamp from raw ms-int to tz-aware datetime`), 1 new regression test
(`TestFetchTradesTimestampUnitsBugRegression`, reproduces the exact pre-fix collapse-to-1970 failure against a realistic
node_fills-shaped payload) + 3 pre-existing tests updated to assert a real `datetime` instead of a raw ms-int.
`quality-gates.sh --no-fix` green before commit.

**Real VM re-verification (proves the fix, not just the diagnosis)** — the first re-verification attempt
(`mtds-backfill-cefi-pipelinecheck-20260712-222842-04cd57`) STILL reproduced the original epoch error, which turned out
to be a tarball-staleness false negative, not a fix failure: MTDS VMs deploy from a prebuilt code tarball
(`gs://deployment-scripts-central-element-323112/code/mtds-code.tar.gz`), NOT live git state (the same discovery Finding
1's verification made independently) — the VM had launched before the tarball was rebuilt post-commit. Rebuilt the
tarball from a clean 4-repo worktree (`unified-api-contracts`/`unified-trading-library`/
`market-tick-data-service`/`deployment-service`, matching `create-code-tarballs.sh`'s `CORE_REPOS`) to avoid embedding
any other agent's concurrent uncommitted WIP, re-uploaded, then re-ran the SAME force-refetch
(`--asset-group CEFI --venue HYPERLIQUID --data-types trades --day 2026-07-09 --instrument-ids BTC --force`) against the
fresh deploy (VM `mtds-backfill-cefi-pipelinecheck-20260713-002055-04cd57`): the `UpstreamTimestampBiasError`/
1970-01-01 collapse is GONE — `derivative_ticker` (the sibling data_type the same fix touches) wrote 24 REAL rows with
correct 2026-07-09 timestamps
(`StreamingParquetWriter: uploaded .../data_type=derivative_ticker/ BTC-USD@LIN.parquet (24 rows, ...)`,
`Manifest updated: ... total_records=24 complete=True`) — direct, positive proof the units fix works end-to-end. The
original bug is conclusively resolved.

**One new, separate, NOT-yet-fixed finding surfaced by this same verification run**: the `trades` data_type specifically
shows `captured=0` in this run's Tier-3 sentinel fan-out even though `derivative_ticker` (funding) succeeded in the SAME
run — the full run.log shows no S3/REST fetch attempt for trades at all, only
`"No S3 asset_ctxs for BTC on 2026-07-09 — trying REST API"` → `"REST API returned 24 funding records"`. This means the
classic download path for HYPERLIQUID either (a) always fetches funding data via this route regardless of the requested
`data_types`, mirroring the FX/KRX `data_types`-ignored bug fixed earlier this session
(`market-tick-data-service@e128c5bc`), or (b) genuinely has no real trades data for the fallback `BTC` symbol on this
specific day via this fetch route (an honest absence, not a bug). Not distinguished — needs a dedicated trace of
`_fetch_hyperliquid_s3`'s data_type dispatch logic. Flagging here rather than guessing; NOT the same bug as the one just
fixed (that bug produced a hard error on every data_type; this one is a clean, silent 0-rows-for-trades-only result).

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
`/codex/04-architecture/shard-level-failure-isolation.md`) would be the next step.

**RESOLVED 2026-07-12 (slot-3)**: root cause found via local reproduction (a synthetic-parquet harness mirroring
`tests/unit/test_tardis_resolve_symbols_date_boundary.py`'s mock strategy, then a real `pandas==2.3.3` interactive
check) — NOT a fresh instance of the raw-Series-vs-`date` bug R5-fix-1 already fixed (2026-06-16). The shared call site
(`tardis_symbol_resolution.py::_resolve_symbols`'s GCS path, both `_catalogue_symbols_for_venue_date` and its
`_resolve_symbols_from_by_date_snapshot` fallback) DOES apply `.dt.date` before comparing to the Python `date` target —
but pandas' `.dt.date` accessor has a genuine gotcha: when EVERY value in the source Series is `NaT` (an all-null
`available_to_datetime` column — the common shape for a perp-only venue's snapshot, since perpetuals never carry an
expiry), `.dt.date` does NOT drop the `datetime64[ns]` dtype the way it does for a mixed valid/NaT column — it silently
returns another `datetime64[ns]`-dtype Series, so the subsequent `<=`/`>=` against the bare `date` scalar raises the
exact byte-identical `TypeError`. BITGET-FUTURES and BITFINEX-FUTURES both hit it because they're perp-heavy venues
whose by_date snapshot's `available_to_datetime` column is realistically all-NaT. Fix:
`market-tick-data-service@2cd02409155adb54d9aeea85dbc462c2855aad87` replaces the `.dt.date <=/>= target` pattern at both
call sites with two new NaT-safe helpers (`_series_date_le`/`_series_date_ge`) that compare the raw `datetime64[ns]`
Series directly against a `pd.Timestamp` bound (tz-matched, exclusive-next-midnight for the upper bound) — a comparison
that is well-typed for any dtype, all-NaT included, while preserving identical day-only-granularity boundary semantics.
5 new regression tests cover the exact type-mismatch case directly (an all-NaT `available_to_datetime` column, both via
`_resolve_symbols` end-to-end and via the two helpers in isolation) plus the tz-aware fixture the pre-existing R5-fix-1
tests already covered (kept green). Real VM re-verification for BOTH venues below.

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
- 2026-07-13 (slot-3): **Finding 3 RESOLVED + shipped** —
  `market-tick-data-service@2cd02409155adb54d9aeea85dbc462c2855aad87`
  (`fix(mtds): NaT-safe date comparison in Tardis CeFi symbol resolution — fixes BITGET-FUTURES + BITFINEX-FUTURES datetime64-vs-date TypeError`).
  Root cause: pandas `.dt.date` does not drop `datetime64[ns]` dtype when a Series is ALL-`NaT` (see the RESOLVED note
  under Finding 3 above for the full mechanism) — a genuinely different bug than R5-fix-1 (2026-06-16) despite the
  byte-identical error text, since both call sites already used the `.dt.date` pattern R5-fix-1 introduced. Fixed both
  GCS-path call sites in `tardis_symbol_resolution.py` (`_catalogue_symbols_for_venue_date` +
  `_resolve_symbols_from_by_date_snapshot`) with two new NaT-safe helpers comparing directly against a tz-matched
  `pd.Timestamp` bound instead of `.dt.date`. 5 new regression tests added directly covering the all-NaT type-mismatch
  case (`tests/unit/test_tardis_resolve_symbols_date_boundary.py` `TestResolveDateBoundaryAllNatColumn` +
  `TestSeriesDateHelpersAllNat`, `tests/unit/test_tardis_catalogue_lifecycle_universe.py`
  `test_all_nat_available_to_no_type_error`); all 21 tests in the file family green, plus the full 213-test
  tardis-marked suite green. `quality-gates.sh --no-fix` green before commit (re-run once after an unrelated agent's
  fast-forward pull moved HEAD mid-gate, to refresh the `.qg_last_passed_sha` sentinel); shipped via
  `quickmerge --agent` scoped to the 3 touched files (foreign concurrent WIP in
  `databento_base_client.py`/`databento_fetch.py`/`umi_tick_provider.py` in the same repo left untouched throughout, per
  multi-agent safety rules). **Real VM re-verification, BOTH venues, SAME shared-code-path change, day=2026-07-09**
  (matching the original failure day) — tarball built from an isolated `git worktree` at the fix commit (avoiding the
  same repo's foreign concurrent WIP) and pinned via `MTDS_TARBALL_SHA` metadata (a mutable "latest" tarball race with a
  DIFFERENT concurrent agent's rebuild was directly observed and sidestepped this way — confirmed via each VM's own
  `manifest: sha=2cd02409155a` boot-log line): VM `mtds-backfill-cefi-verifybitget-20260712-230433` (BITGET-FUTURES) and
  VM `mtds-backfill-cefi-verifybitfinex-20260712-230433` (BITFINEX-FUTURES), both `--test-run --force`, no
  `--instrument-ids` (mirrors the real failure — neither venue has a `smoke_matrix._REPRESENTATIVE_SYMBOL` entry, so the
  GCS by_date-snapshot path that hits this exact bug is the one genuinely exercised). Both full run.logs (2916 + 345
  lines) grepped for zero hits on `Invalid comparison between dtype` and zero hits on
  `unexpected error (shard isolated)` — CONFIRMED ABSENT on both. Both `_resolve_symbols` calls now resolve the FULL
  per-venue universe (hundreds of BITGET-FUTURES symbols, dozens of BITFINEX-FUTURES symbols) instead of crashing before
  a single Tardis request; `TardisAdapter.download_batch` completes normally for both (`0 records ... SHARD_INCOMPLETE`,
  NOT a venue-level crash); both VMs exit `DEPLOYMENT_COMPLETED ... exit_code=0` and self-delete cleanly, no lingering
  compute. The `0 records` outcome itself is a SEPARATE, pre-existing, already-instrumented issue — every per-symbol
  fetch failed with `Tardis HTTP 403 code=274 concurrent-IP-lock` (the single-concurrent-IP Tardis key lease contended
  by other VMs on this shared host at test time; `tardis_concurrency_lease.py` exists specifically to manage this) — out
  of scope for this fix and not chased further here.
- 2026-07-13 (fresh CeFi futures/derivatives triage pass, unrelated session) — **A 5th venue hitting the identical
  `2cd02409` bug, found and confirmed FIXED via a fresh real-VM run — `BINANCE-DELIVERY`.** While triaging
  `data_pipeline_e2e_check_2026_07_10.md` todo 25's CeFi futures/derivatives cluster,
  `CEFI:BINANCE-DELIVERY:perp_funding`'s original 2026-07-09 sweep failure (`no_parquet_under`) traced to a
  reverify-directory run.log from BEFORE this fix (`mtds-backfill-cefi-pipelinecheck-20260712-101535`, 2026-07-12 10:18
  UTC — the fix landed 22:43 UTC the same day): byte-identical
  `ERROR Venue BINANCE-DELIVERY: unexpected error (shard isolated): Invalid comparison between dtype=datetime64[ns] and date`.
  BINANCE-DELIVERY is a perp-only venue (no dated-futures product), so its `available_to_datetime` catalogue column is
  realistically all-`NaT` — the exact shape this fix's `_series_date_le`/`_series_date_ge` helpers target. **Re-ran
  fresh post-fix** (`mtds-backfill-cefi-pipelinecheck-20260712-234345-091bad`, tarball pinned to a commit already
  including `2cd02409`): the crash is GONE — the run now reaches
  `TardisAdapter.download_batch: binance-delivery 2026-07-09 — 0 records (0 bulk, 1 per-symbol data types)` and proceeds
  into real per-symbol Tardis requests (`binance-delivery/xrpusd_261225/…`, `solusd_260925/…`, etc.), which then hit the
  SAME, separate, already-tracked `Tardis HTTP 403 code=274 concurrent-IP-lock` contention this doc's Finding 3
  verification hit (see `tardis_concurrent_ip_lockout_2026_07_12.md`) — not the fixed bug recurring. **BINANCE-DELIVERY
  confirmed resolved by the existing general fix, no new code needed** — the 0-records outcome is contention noise,
  cross-referenced onto the P0 lockout doc rather than re-diagnosed here.
- 2026-07-13: **Finding 2 RESOLVED + shipped** — `market-tick-data-service@db6356327a9bdc47c4caeb78a035ca61ae9bfe16`
  (units-mismatch fix: the already-parsed tz-aware datetime `_clip_rows_to_day` computes internally is now written back
  onto the row instead of the raw epoch-ms int, which pandas' default `pd.to_datetime` unit (nanoseconds) had been
  silently misreading as ~1.75 seconds past epoch). First real-VM verification attempt was a false negative — the VM ran
  a stale, pre-fix code tarball (MTDS deploys from a prebuilt tarball, not live git state, the same discovery Finding
  1's verification made independently). Rebuilt the tarball from a clean 4-repo worktree (avoiding any other agent's
  concurrent dirty WIP in the shared market-tick-data-service tree) and re-ran the same force-refetch: confirmed fixed —
  `derivative_ticker` wrote 24 real rows with correct 2026-07-09 timestamps, no epoch collapse,
  `Manifest updated: ... total_records=24 complete=True`. One new, separate, unfixed finding surfaced by the same run
  (documented above under Finding 2): `trades` specifically still shows 0 captured even though `derivative_ticker`
  succeeded in the same run — either a `data_types`-ignored dispatch bug (same class as the already-fixed FX/KRX one) or
  an honest absence for this fallback symbol/day, not distinguished — needs its own dedicated trace, not chased further
  this pass.
