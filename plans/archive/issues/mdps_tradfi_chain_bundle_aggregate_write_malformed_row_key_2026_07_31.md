---
doc_type: issue
title: >-
  market-data-processing-service tradfi backfill: the underlying-level aggregate candle write (e.g.
  underlying=SP500/ticks.parquet, not tied to a single instrument_id) fails with MalformedRowKeyError on an empty
  instrument_id, and ohlcv_1s has no registered SchemaContract for tradfi COMBO/FUTURE -- both surfaced only now that
  the chain-bundle matcher fix (market-data-processing-service@43b043b) lets execution reach this far; the CORE
  per-instrument candle writes (CME:FUTURE:ES-<exp>.parquet, CME:FUTURE:MES-<exp>.parquet) are confirmed writing
  correctly across multiple timeframes, so this does NOT block the fleet relaunch
summary: >-
  Relaunched the full 14-shard `es`/`es3` tradfi backfill fleet
  (`tradfi_mdps_es_mes_backfill_fleet_consolidator_staleness_failures_2026_07_31.md`'s P0 todo) on the now-fixed tarball
  (market-data-processing-service@4b84d5c11ede, an ancestor-including-43b043b commit). Spot-checked the first shard's
  early log + real GCS output. GOOD: the chain-bundle matcher fix works as designed -- confirmed via direct GCS
  inspection, `CME:FUTURE:ES-20200320.parquet` and `CME:FUTURE:MES-20200320.parquet` are writing successfully across
  multiple timeframes (15s/15m/1h/1d) for `day=2020-01-01`, which never happened before the fix. BUT two narrower gaps
  surfaced in the same run, both pre-existing and simply never previously exercised (this chain-bundle code path never
  successfully ran in production before 43b043b unblocked it): (1) a SEPARATE write attempt for the underlying-level
  AGGREGATE candle (`underlying=SP500/ticks.parquet`, representing the whole contract-family, not one specific
  expiry/instrument_id) passes an empty `instrument_id` into the manifest `record_captured`/`record_failed` row_key,
  which the hard_schema_enforcement Phase-4 gate rejects with `MalformedRowKeyError` -- confirmed via direct log
  inspection, happens for `trades`/`ohlcv_1m` data_types on multiple dates. (2) `ohlcv_1s` has no `SchemaContract`
  registered for `asset_group=tradfi instrument_type=COMBO/ FUTURE` in
  `unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY`, so every `ohlcv_1s` write for this fleet fails
  outright (`ALL FAILED (5/5)` or `(6/6)` on every date checked). Neither blocks the per-instrument candle output that
  downstream consumers (features-service, strategy) actually need -- shard-level failure isolation means the process
  continues past both and keeps writing the real per-instrument files.
status: resolved
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-data-processing-service, unified-api-contracts]
scope: [engineer]
tags: [tradfi, mdps, manifest, schema-contract, row-key, chain-bundle, backfill]
related:
  - /plans/active/issues/tradfi_mdps_es_mes_backfill_fleet_consolidator_staleness_failures_2026_07_31.md
created: "2026-07-31"
source: [mdps-backfill-tradfi-y2020es-20260731-023743 run.log, first-day spot-check after relaunching the fixed fleet]
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: "market-data-processing-service@c78285b, unified-api-contracts@4eeb495f — regression tests + QG green"
---

> **🟢 RESOLVED 2026-08-02** — both todos shipped with regression tests and full QG green.
> `market-data-processing-service@c78285b`, `unified-api-contracts@4eeb495f`.

# What I found

After relaunching the full 14-shard `es`/`es3` tradfi fleet on the chain-bundle-matcher-fixed tarball (see the sibling
issue doc's P0 todo), spot-checked `mdps-backfill-tradfi-y2020es-20260731-023743`'s early log + real GCS output to
confirm the fix actually produces real data (not just "VM is alive", per that doc's own P2 lesson).

## Confirmed working: real per-instrument candles now write correctly

```
gs://market-data-tick-tradfi-prd-central-element-323112/processed_candles/by_date/day=2020-01-01/pipeline_mode=batch_databento/timeframe=15m/data_type=trades/instrument_type=FUTURE/venue=CME/underlying=ES/CME:FUTURE:ES-20200320.parquet
gs://.../timeframe=15m/.../underlying=MES/CME:FUTURE:MES-20200320.parquet
gs://.../timeframe=15s/.../underlying=ES/CME:FUTURE:ES-20200320.parquet
gs://.../timeframe=1h/.../underlying=ES/CME:FUTURE:ES-20200320.parquet
gs://.../timeframe=1d/.../underlying=ES/CME:FUTURE:ES-20200320.parquet
```

These files did NOT exist before `43b043b` (the matcher never found the source data). This is the deliverable the whole
fleet relaunch was for, and it's working.

## Gap 1: the underlying-level AGGREGATE write fails on an empty instrument_id

```
WARNING MDPS canonical_writer: streaming manifest write failed for day=2020-01-01 tf=1m: MalformedRowKeyError:
shard-atom field 'instrument_id' was explicitly passed as empty. Per hard_schema_enforcement Phase 4, callers that
include 'instrument_id' in row_key MUST supply a non-empty value. row_key={'date': '2020-01-01', 'venue': 'CME',
'instrument_type': 'FUTURE', 'data_type': 'trades', 'timeframe': '1m', 'league_id': '', 'underlying': 'SP500',
'instrument_id': ''}
```

This is a DIFFERENT write than the per-instrument one above — it's for the bundle-level aggregate output
(`underlying=SP500/ticks.parquet`, no per-expiry instrument_id, representing the whole contract-family), confirmed via
the corresponding real GCS object also existing at `.../underlying=SP500/ticks.parquet` (present, but its manifest ROW
never got recorded, so the manifest under-reports what's actually on disk for this specific shard-atom). Seen on
`trades`/`ohlcv_1m` data_types across multiple dates in the log (both `record_captured` AND the `record_failed` fallback
fail identically, since both pass the same empty `instrument_id`).

## Gap 2: `ohlcv_1s` has no registered SchemaContract for tradfi COMBO/FUTURE

```
ERROR [ohlcv_1s] .../instrument_type=combo/data_type=ohlcv_1s/underlying=MICRO-SP500/...: No SchemaContract
registered for asset_group='tradfi' instrument_type='COMBO' data_type='ohlcv_1s' venue='CME'. Add a contract to
unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY (and VENUE_CONTRACT_OVERRIDES if venue-specific)
before rerunning the read/migration pipeline.
```

`ALL FAILED (5/5)`/`(6/6)` for `ohlcv_1s` on every date checked — a missing registry entry, not a bug in the matcher or
writer logic. Straightforward to fix (register the contract) once someone confirms `ohlcv_1s` is actually a wanted
output granularity for tradfi (it may simply have never been in scope before this chain-bundle path was unblocked).

# Why this matters

Neither gap blocks the fleet relaunch's actual goal — real `CME:FUTURE:ES`/`CME:FUTURE:MES` candles are confirmed
writing correctly across the timeframes that matter (15s/15m/1h/1d). But: (1) the underlying-level aggregate manifest
under-reports real on-disk data for `trades`/`ohlcv_1m` shard-atoms specifically (a real file exists, manifest has no
row for it — an honest-coverage gap a future audit could misread as "missing"), and (2) `ohlcv_1s` tradfi output is
silently entirely absent for this whole fleet, every date, until the schema contract is added.

# What I did NOT do

Did not patch either gap myself — (1) needs a design call on whether the aggregate write should omit `instrument_id`
from its row_key entirely (a different shard-atom shape) or synthesize one, which I don't have enough context on the
aggregate-write's actual consumer/intent to decide safely; (2) needs confirmation `ohlcv_1s` is actually wanted for
tradfi before adding a contract that expands the CONTRACT_REGISTRY. Filed as a P2 (real, but non-blocking) follow-up
rather than absorbing unplanned scope mid-relaunch-verification.

# Recommended decision

- [x] ✅ [BACKEND] P2. Decide + fix the aggregate-write row_key shape (`underlying=<root>` bundle writes for
      `trades`/`ohlcv_1m`, tradfi COMBO/FUTURE): either drop `instrument_id` from the row_key for this write path (if
      it's genuinely not a per-instrument shard-atom) or populate it with a sentinel/aggregate id. Repo:
      market-data-processing-service. Done when: the `MalformedRowKeyError` warnings stop appearing for this write path
      and the manifest correctly reflects the real on-disk `underlying=*/ticks.parquet` files. —
      market-data-processing-service@c78285b: dropped `instrument_id` from the row_key (mirrors the existing
      `write_candle_parquet` fix) in both `open_candle_streaming_writer`/`close_candle_streaming_writer`
      (`canonical_writer_streaming.py`, the chain-bundle write path) and the shared `_emit_status_for_shard` helper
      (`canonical_writer_manifest.py`, used by `record_empty_for_shard`/`record_failed_for_shard`) — passing
      `instrument_id=""` explicitly was tripping UTL's `MalformedRowKeyError` shard-atom guard; omitting the key is the
      contract for a non-per-instrument shard. 4 regression tests added (2 in `test_streaming_write_per_tf.py`, 2 in
      `test_canonical_writer_record_helpers.py`) asserting `instrument_id` is absent from the row_key for an empty
      instrument_id + `underlying=SP500`. Full quality-gates.sh green (2293 passed, 2 skipped).
- [x] ✅ [BACKEND] P3. Register a `SchemaContract` for
      `asset_group=tradfi instrument_type=COMBO|FUTURE     data_type=ohlcv_1s` in
      `unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY` (confirm `ohlcv_1s` is actually wanted for
      tradfi first — it may be intentionally out of scope). Repo: unified-api-contracts. —
      `unified-api-contracts@4eeb495f` ("fix(schemas): register missing tradfi ohlcv_1s SchemaContract entries")
      registers exactly the four entries this gap needed:
      `("tradfi","future"|"futures_chain"|"combo"|"UNKNOWN", "ohlcv_1s") -> TRADFI_FUTURE_OHLCV_1M`. Confirmed on
      `live-defi-rollout` (clean tree) while investigating DP-VM-001 escalation agt-d05d42 (slot 12) — the dead
      `mdps-backfill-tradfi-y2026es-20260731-023743` VM hit this exact `No SchemaContract registered` error 1,366 times
      across its run because it launched (02:37:43Z) before this fix landed (03:30:26Z). See that doc's Progress Log for
      the fleet-wide detail.

# Progress Log

- 2026-07-31 (slot-2, backend_engineer craft, tradfi_mdps_es_mes_backfill_fleet_consolidator_staleness_failures-004
  dispatch): filed while verifying the P0 fleet-relaunch todo — confirmed the core per-instrument candle output works
  correctly, these two gaps are narrower and non-blocking.
