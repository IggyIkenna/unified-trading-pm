---
doc_type: issue
title:
  CEFI standalone FUTURE instrument_type has no registered candle SchemaContract — every MDPS candle write for a
  per-contract dated future fails
summary: |
  Found running the /data-pipeline-check-mdps -test- verification for the candle-canonical migration
  (candle_feature_canonical_path_divergence_2026_07_20.md). unified-api-contracts'
  _candle_contracts.py registers CEFI candle contracts only for instrument_type in
  {perpetual, spot_pair} (+ the bundled options_chain/futures_chain paths) — never for a
  standalone per-contract "future" instrument_type. DERIBIT emits per-contract dated-futures
  raw ticks (e.g. DERIBIT:FUTURE:BTC-USD@INV-20260627, INV/LIN margin, weekly/quarterly expiries)
  that are NOT chain-bundled at the raw-tick level, so MDPS's per-instrument candle path processes
  them as instrument_type=FUTURE and every write fails "No SchemaContract registered for
  asset_group='cefi' instrument_type='FUTURE' data_type=... venue='DERIBIT'" (shard-isolated —
  logged + skipped, not a raise, so it never surfaces as a VM crash, only as
  "cefi/trades/FUTURE: ALL FAILED (N/N)" in the VM's own processing summary).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [unified-api-contracts, market-data-processing-service]
scope: [engineer, admin]
tags: [data-correctness, schema-contract, candles, cefi, deribit, futures]
related:
  [
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    ../data_pipeline_check_mdps_features_2026_07_20.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.0
assigned_role: data
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  measured 2026-07-21 on a real -test- VM (mdps-backfill-cefi-pipelinecheck-20260721-172552-c829e9) while verifying the
  candle-canonical migration foundation on real infra.
---

# CEFI standalone FUTURE instrument_type has no registered candle SchemaContract

## Evidence

Real VM run (`mdps-backfill-cefi-pipelinecheck-20260721-172552-c829e9`, CEFI DERIBIT trades, day=2026-06-27, all 7
timeframes): 60 instrument×timeframe cells, 29 succeeded (PERPETUAL/SPOT_PAIR), **31/31 FUTURE-instrument-type cells
failed identically**:

```
No SchemaContract registered for asset_group='cefi' instrument_type='FUTURE' data_type='ohlcv_15s'
venue='DERIBIT'. Add a contract to unified_api_contracts.internal.schemas.contracts.CONTRACT_REGISTRY
(and VENUE_CONTRACT_OVERRIDES if the schema is venue-specific) before rerunning the read/migration
pipeline. (instrument=raw_tick_data/.../instrument_type=future/data_type=trades/
DERIBIT:FUTURE:BTC-USD@INV-20260627.parquet)
```

Same shape for every dated-futures expiry (`@INV`/`@LIN`, weekly/quarterly) across BTC/ETH and all 7 candle timeframes —
this is not one bad instrument, it is the whole `cefi + FUTURE` combination.

## Root cause (read from `unified_api_contracts/internal/schemas/_candle_contracts.py`)

The CEFI candle-contract registration loop (`for _tf in _TIMEFRAMES_CEFI:`, ~line 291) registers:

- `perpetual` × (trades / book_snapshot_5 / derivative_ticker / liquidations)
- `spot_pair` × (trades / book_snapshot_5)
- `options_chain` / `futures_chain` × trades (bundled per-underlying — a SEPARATE loop over `_TIMEFRAMES_OPTIONS`)

There is no `_register(_build("cefi", "future", ...))` anywhere — a standalone (non-bundled) per-contract
`instrument_type="future"` candle contract for CEFI does not exist. TradFi DOES register `future` (see
`_TIMEFRAMES_TRADFI_RE_AGGREGATED` loop, ~line 375), so this looks like an oversight specific to CEFI, not a deliberate
policy.

## Blast radius

- Shard-isolated (per-instrument `try/except`, logged as `[CRITICAL] unknown error` + counted in the VM's failure
  summary) — never crashes the VM outright, so it is silent unless someone reads the per-shard error breakdown or (as
  here) a driver scopes a cell narrowly enough to notice `ALL FAILED (N/N)`.
- Affects every CEFI venue that has per-contract (non-chain-bundled) dated futures in its raw-tick universe, not just
  DERIBIT — needs a corpus-wide check of which venues emit `instrument_type=future` raw ticks for CEFI (vs. only
  chain-bundled `futures_chain`).
- Every MDPS candle backfill run over CEFI futures has been silently producing ZERO candles for this instrument_type
  since MDPS candle-writing began — this is a coverage gap, not a regression from today's work.

## Not caused by, but found during, the candle-canonical migration

This is orthogonal to `candle_feature_canonical_path_divergence_2026_07_20.md` (the path/manifest `data_type` axis +
`instrument_type=` shape work) — the SchemaContract registry gap exists independent of which path shape the object lands
on. Filed separately per the workspace's findings-triage rule (outside the migration's own scope).

## Todos

- [ ] 1. [DATA] P1. Decide the CEFI `future` candle policy: register a standalone
      `_register(_build("cefi", "future", ...))` contract (mirroring TradFi's `_TIMEFRAMES_TRADFI_RE_AGGREGATED` loop)
      OR confirm CEFI dated futures should ONLY ever be chain-bundled (in which case the raw-tick capture / MDPS
      instrument-type inference is producing a per-contract `instrument_type=future` shard that should never have
      reached the candle writer at all — a routing bug, not a missing-contract bug). Read `output_path_helpers.py`'s
      chain-bundle detection (`CEFI_CHAIN_INSTRUMENT_TYPES`) to see whether DERIBIT dated futures are supposed to route
      through the bundle path.
- [ ] 2. [DATA] P2. Corpus-wide scan: which CEFI venues/instrument_types besides DERIBIT hit this (or the
      DEFI/PREDICTION equivalent) — is this DERIBIT-specific or systemic.
- [ ] 3. [SCRIPT] P2. Once ruled, register the contract (or fix the routing) + add a regression test asserting every
      raw-tick-capturable CEFI instrument_type has a registered candle contract for its capturable data_types (closes
      the class of bug, not just this instance).
