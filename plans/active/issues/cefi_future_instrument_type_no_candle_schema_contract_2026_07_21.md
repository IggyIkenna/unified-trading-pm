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

- [x] ✅ 1. [DATA] P1. **DONE 2026-07-27 (slot-5) — unified-api-contracts@4ad3f14f.** Ruled + shipped: registered a
      standalone `_register(_build("cefi", "future", ...))` contract (mirroring TradFi's standalone `future`
      registration) — confirmed via `CEFI_CHAIN_INSTRUMENT_TYPES = frozenset({"options_chain", "futures_chain"})` that
      dated futures are deliberately NOT chain-bundled, so this was a missing-contract oversight, not a routing bug. New
      regression test `test_cefi_future_trades_candles` (parametrized over all CEFI timeframes); 218 targeted tests +
      full `quality-gates.sh` green (sentinel-verified). Ruling + patch originally authored by slot-8 (2026-07-27),
      blocked on the shared-host disk-full incident (BLK-ff0ebe7f); applied verbatim now that disk has recovered.
- [x] ✅ 2. [DATA] P2. **DONE 2026-07-27 (slot-11).** Corpus-wide scan: which CEFI venues/instrument_types besides
      DERIBIT hit this (or the DEFI/PREDICTION equivalent) — is this DERIBIT-specific or systemic. See "2026-07-27
      corpus-wide scan (slot-11)" below for the full written findings + evidence (live GCS sampling across 4 days,
      cross-referenced against `CONTRACT_REGISTRY` and MDPS source). Summary: **NOT DERIBIT-specific** — OKX-FUTURES
      also emits standalone (non-chain-bundled) `instrument_type=future` CEFI raw ticks, but todo 1's fix is
      venue-agnostic so it already covers OKX-FUTURES too; no further CEFI action needed. DeFi has 2 unregistered
      candle-contract instrument_types (`spot_asset`, `lending`) but MDPS's own source never references either string
      anywhere, so neither is an ACTIVE "attempts write, crashes on missing contract" bug like the CEFI FUTURE case —
      it's an untouched candle-pipeline coverage gap, a different (lower-priority, separately-scoped) class of finding,
      not this todo's failure class. Prediction could not be fully checked — no dedicated
      `market-data-tick-prediction-*` bucket exists; prediction-market raw ticks appear to live inside the DeFi bucket
      (an unexpected `pipeline_mode=batch_kalshi_perp` shard was found there) — flagged, not resolved, in this pass.
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

# 2026-07-27 corpus-wide scan (slot-11) -- todo 2, written findings

Worked with todo 1 already shipped (`unified-api-contracts@4ad3f14f`, confirmed at HEAD in this worktree). Scanned which
CEFI (and DeFi/Prediction) venue x instrument_type combinations exist in production raw capture and cross-referenced
against `CONTRACT_REGISTRY` (`unified_api_contracts/internal/schemas/_candle_contracts.py`), rather than re-deriving
from code alone -- live `gcloud storage ls` sampling (same method the original finder used) across 4 real days
(`2026-06-27`, `2026-07-19`, `2026-07-20`, `2026-07-21`).

## CEFI -- confirmed NOT DERIBIT-specific, but already fully covered

Real `instrument_type=` partitions observed under `raw_tick_data/` (`market-data-tick-cefi-prd-central-element-323112`):

| pipeline_mode     | venue            | instrument_types observed    |
| ----------------- | ---------------- | ---------------------------- |
| batch_tardis      | BITFINEX-FUTURES | perpetual                    |
| batch_tardis      | COINBASE-FUTURES | perpetual, spot_pair         |
| batch_tardis      | COINBASE-SPOT    | spot_pair                    |
| batch_tardis      | DERIBIT          | future, perpetual, spot_pair |
| batch_tardis      | OKX-FUTURES      | **future**                   |
| batch_tardis      | LIGHTER-ZKSYNC   | perpetual                    |
| batch_hyperliquid | HYPERLIQUID      | perpetual                    |
| batch_aster       | ASTER            | perpetual                    |

**OKX-FUTURES also emits standalone `instrument_type=future` raw ticks** -- so the bug was never DERIBIT-exclusive. It
does not need a SEPARATE fix: todo 1's `_register(_build("cefi", "future", ...))` is venue-agnostic (keyed on
`(asset_group, instrument_type, data_type)`, no venue dimension), so it already covers OKX-FUTURES (and any other CEFI
venue that ever emits standalone dated futures) identically to DERIBIT. Cross-checked `market_data_categories.py`'s
`FUTURE_BUNDLE_VENUES` (`cefi: {"DERIBIT", "OKX"}`) -- OKX's futures actually get chain-bundled to `futures_chain` at
candle-write time in the normal case (already-registered contract), so the standalone-`future` contract is the
fallback/edge-case path for OKX too, not its primary path; either way both venues are now covered.

No `instrument_type=option` raw shard was found in any of the 4 sampled days for DERIBIT (despite DERIBIT having a
registered `options_chain` candle contract and being listed with `options_chain`/`futures_chain` data types in
`market_data_categories.py`'s per-venue registry) -- this reads as a separate, pre-existing "is options capture actually
populated" question, out of scope for this todo (which is about registry gaps, not capture-population gaps), not
investigated further here.

**No other CEFI instrument_type gap exists**: `SPOT_ASSET` (DeFi-only in practice -- every usage across the workspace is
inside `*/defi/*` adapter code, zero CEFI usage), `EQUITY_PERP`/`TOKENIZED_EQUITY` (both explicitly "no longer minted"
per `unified_api_contracts/_instrument_enums.py`'s own docstring) are not live CEFI candle-write risks. **Conclusion:
CEFI is fully covered by todo 1's already-shipped fix; no further action.**

## DeFi -- 2 unregistered instrument_types found, but NEITHER is this failure class

Real `instrument_type=` partitions observed under `raw_tick_data/` (`market-data-tick-defi-prd-central-element-323112`,
day=2026-07-19):

| pipeline_mode          | instrument_types observed  |
| ---------------------- | -------------------------- |
| batch_aave             | spot_asset                 |
| batch_chainlink        | spot_asset                 |
| batch_onchain_rpc      | spot_asset                 |
| batch_onchain_subgraph | lending, lst, pool         |
| batch_kalshi_perp      | perpetual (see note below) |

`CONTRACT_REGISTRY` only registers `"pool"` and `"a_token"` and `"lst"` for `defi` (see `_candle_contracts.py` lines
~422-514) -- **`spot_asset` and `lending` (the real raw values) have no registered contract.** However, this is NOT the
same live-crash failure class as the CEFI FUTURE bug: `grep -rn '"a_token"\|"lending"\|"spot_asset"'` across all of
`market-data-processing-service/market_data_processing_service/` (excluding tests) returns **zero hits** -- MDPS's
candle-derivation pipeline never references any of these three strings anywhere, meaning it does not currently attempt
to candle-process this DeFi data at all (no adapter wired up for it), so there is no live `SchemaContractNotFoundError`
being hit today. This reads as an untouched MDPS candle-pipeline coverage gap (DeFi lending/spot_asset data is
presumably consumed directly as raw ticks by features-service's onchain family instead, per
`defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s D1 todo, rather than via MDPS-derived candles) -- a DIFFERENT,
lower-priority class of finding than "registered adapter, unregistered contract, live crash." Filing it here for
visibility but NOT folding it into todo 3's scope, since todo 3 is specifically about the registered-but-uncontracted
crash class.

**Separate oddity, not investigated further**: `pipeline_mode=batch_kalshi_perp` under the **DeFi** bucket with
`instrument_type=perpetual` is unexpected -- Kalshi is a prediction-market venue, not DeFi. Possibly a legacy
bucket-routing artifact or a deliberate onchain-Kalshi-perp product this scan didn't have context for. Flagging for
whoever owns prediction/DeFi bucket routing; out of scope for this candle-contract todo.

## Prediction -- could not fully verify (bucket-naming gap, not a confirmed-empty finding)

No `market-data-tick-prediction-*` GCS bucket exists (`gcloud storage buckets list --filter="name~prediction"` returned
zero results) -- prediction-market raw ticks apparently do not live in a dedicated prediction bucket (the
`batch_kalshi_perp` shard noted above, found under the DeFi bucket, may be part of this). Did not locate the actual
storage location for Polymarket/Kalshi prediction-market raw ticks within this session's time budget, so I cannot
confirm or rule out a parallel SchemaContract gap for Prediction the way I did for CEFI/DeFi. **Recording as NOT
VERIFIED, not confirmed-empty** -- whoever picks up a Prediction-side check next should start by finding the actual
bucket/path Prediction raw ticks are written to.
