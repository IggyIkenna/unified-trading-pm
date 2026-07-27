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
    /plans/active/data_pipeline_check_mdps_features_2026_07_20.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
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

# 2026-07-27 update (slot-8) -- todo 1 RULED + fix ready, blocked on host disk-full (BLK-ff0ebe7f), NOT re-dispatchable to this slot

**Ruling on todo 1**: register a standalone contract (not "confirm chain-bundled-only"). Confirmed via
`unified_api_contracts.gcs_paths.CEFI_CHAIN_INSTRUMENT_TYPES = frozenset({"options_chain", "futures_chain"})` --
`"future"` is deliberately NOT a member, so DERIBIT's raw per-contract dated-futures ticks correctly route to the
standalone (non-bundled) path today; the gap is purely a missing `CONTRACT_REGISTRY` entry, exactly like the doc's
original "oversight, not policy" read (TradFi already registers standalone `future` the same way,
`_TIMEFRAMES_TRADFI_RE_AGGREGATED` loop, trades-only, no book5/derivative_ticker/liquidations since dated futures don't
emit funding/liquidation events).

**Fix written + verified, but NOT shipped**: implemented in `unified-api-contracts`, full `quality-gates.sh` run got to
12101 tests PASSED before the pytest-cov coverage-DB write itself failed with `disk or database is full` -- the code is
correct, only the QG bookkeeping step is blocked by the same host disk-full incident escalated in
`features_service_defi_backfill_vm_oom_unexplained_2026_07_26.md`-adjacent session context (BLK-ff0ebe7f; main PARKED
this task's backlog entry behind `shared-host-disk-headroom-restored=false`, `priority: 999`). Per RULES.md skip
semantics, I could not stay assigned to this exact task without permanently blocking my own slot from ever picking it up
again once the prereq flips -- so I released it via `/skip-current-task`, but that also means whichever slot resumes it
next does NOT have my local `git stash` (`unified-api-contracts`, message
`orchestrator-slot-8-cefi_future_instrument_type_no_candle_schema_contract-001-diskfull-blocked`). Pasting the full
patch here so it survives independent of any one slot's local stash:

```diff
diff --git a/tests/internal/unit/test_mdps_candle_contracts.py b/tests/internal/unit/test_mdps_candle_contracts.py
index 5d844baf..dc6c95cd 100644
--- a/tests/internal/unit/test_mdps_candle_contracts.py
+++ b/tests/internal/unit/test_mdps_candle_contracts.py
@@ -132,6 +132,19 @@ def test_cefi_spot_pair_candles(tf: str) -> None:
     assert book5.symbol_column == "symbol"


+@pytest.mark.parametrize("tf", MDPS_TIMEFRAMES_CEFI)
+def test_cefi_future_trades_candles(tf: str) -> None:
+    """Standalone dated future (e.g. DERIBIT BTC-USD@INV-20260627), not chain-bundled.
+
+    Regression for cefi_future_instrument_type_no_candle_schema_contract_2026_07_21:
+    every CEFI FUTURE candle write failed "No SchemaContract registered" because this
+    instrument_type had no contract at all (CEFI's perpetual/spot_pair loop never
+    covered it, unlike TradFi's `future`, which already registers the same shape).
+    """
+    contract = lookup_contract(asset_group="cefi", instrument_type="future", data_type=MDPS_KEY_TRADES(tf))
+    assert contract.symbol_column == "symbol"
+
+
 @pytest.mark.parametrize("tf", MDPS_TIMEFRAMES_OPTIONS)
 def test_cefi_options_chain_candles_key_on_underlying(tf: str) -> None:
     contract = lookup_contract(asset_group="cefi", instrument_type="options_chain", data_type=MDPS_KEY_TRADES(tf))
diff --git a/unified_api_contracts/internal/schemas/_candle_contracts.py b/unified_api_contracts/internal/schemas/_candle_contracts.py
index bc6c3a30..937661e1 100644
--- a/unified_api_contracts/internal/schemas/_candle_contracts.py
+++ b/unified_api_contracts/internal/schemas/_candle_contracts.py
@@ -332,6 +332,17 @@ for _tf in _TIMEFRAMES_CEFI:
     # spot_pair — no derivative_ticker / liquidations
     _register(_build("cefi", "spot_pair", _trades_key(_tf), symbol_column="symbol", extra_cols=[], nullable_ohlcv=True))
     _register(_build("cefi", "spot_pair", _book5_key(_tf), symbol_column="symbol", extra_cols=_BOOK5_EXT))
+    # standalone dated future (non-chain-bundled per-contract futures, e.g. DERIBIT
+    # BTC-USD@INV-20260627) — mirrors TradFi's `future` registration below (trades
+    # only, no derivative_ticker/liquidations: those are perp-specific funding/
+    # liquidation events that dated futures don't emit).
+    # cefi_future_instrument_type_no_candle_schema_contract_2026_07_21: this
+    # instrument_type is deliberately excluded from CEFI_CHAIN_INSTRUMENT_TYPES
+    # (unified_api_contracts.gcs_paths, frozenset({"options_chain", "futures_chain"}))
+    # so raw per-contract future ticks correctly route here rather than through the
+    # chain-bundle path — the gap was a missing contract registration, not a routing
+    # bug (confirmed: TradFi already registers standalone `future` the same way).
+    _register(_build("cefi", "future", _trades_key(_tf), symbol_column="symbol", extra_cols=[], nullable_ohlcv=True))

 for _tf in _TIMEFRAMES_OPTIONS:
     _register(
```

Whoever resumes this once `shared-host-disk-headroom-restored` flips true: apply the patch above (or pull from
`unified-api-contracts` slot-8 stash if it's still there), re-run `quality-gates.sh` for real (do not skip it — only the
coverage-DB write failed last time, not the actual test assertions), ship via quickmerge, and flip todo 1's checkbox
with the ruling above as evidence. Todos 2 and 3 remain open follow-ups.
