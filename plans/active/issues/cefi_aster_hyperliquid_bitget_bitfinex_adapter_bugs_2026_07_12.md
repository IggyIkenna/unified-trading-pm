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
