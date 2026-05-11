---
title: "MTDS per-instrument download API — bundle + per-symbol search via predicate pushdown"
status: active
created: 2026-04-24
locked_by: live-defi-rollout
locked_since: 2026-04-24
estimate_class: design
estimate_baseline_ai_days: TBD
estimate_calibrated_ai_days: TBD
estimate_calibration_note: |
  No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from filename (design, multiplier 0.6×).
  Owner agent: fill baseline + multiply × 0.6 per codex/08-workflows/estimation-calibration.md. Refine class if dominant work-class differs.
---

# MTDS per-instrument download API — bundle + per-symbol search via predicate pushdown

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 11 of 11 unchecked todos
- **Mis-marked DONE -> flipped**: 1 (Phase 4 codex doc — confirmed shipped at
  `unified-trading-pm/codex/02-data/mtds-download-api.md` with `scope: [engineer]`, 145 lines)
- **In-flight (running VMs)**: none gated by this plan
- **Blocked by**: none on Phase 1.5 chain axis (UAC `CHAIN_RPC_TEMPLATES` is shipped); Phase 1.5 prediction
  `canonical_question_group` axis depends on UAC `PREDICTION_GROUPS` registry (UAC `bb24aba` ships skeleton + `af2bc9b`
  SSOT lifecycle, so SSOT is partially landed)
- **Blocks**: `infrastructure_master_2026_05_07` Phase B.2/C.13 drilldown shard-atom alignment — per-instrument access
  from the data-status drilldown's per-day icons would consume this API
- **Last meaningful commit**: MTDS `2095d1b` (2026-04-24) — `CanonicalParquetReader` shipped at
  `market_tick_data_service/reader.py` (428 lines + `tests/market_interface/unit/test_canonical_parquet_reader.py` 472
  lines)
- **Recommendation**: NOT YET ARCHIVE-READY. Phase 1 (CeFi/TradFi/Sports) shipped; Phase 4 codex doc shipped; Phase 1.5
  (DeFi `chain` + Prediction `canonical_question_group` axes), Phase 2 (consumer wiring — 11 `pd.read_parquet` direct
  call sites still in MTDS source), and Phase 3 (integration test) all remain. Phase 1.5 DeFi `chain` axis is
  critical-path for the 24 cefi VMs + DeFi backfills since `read_shard()` callers without the `chain=` axis can silently
  return wrong-chain rows on protocols spanning multiple chains. Suggest promoting Phase 1.5 chain axis to "ship by
  2026-05-12" and deferring Phase 1.5 prediction axis + Phase 2 consumer migration + Phase 3 integration test to
  post-deadline.
- **Anomalies**: `pd.read_parquet` direct calls remain in MTDS source at 11 sites (kalshi_adapter.py:297,
  tardis_adapter.py:1648/1966/2124, polymarket_adapter.py:626, \_instruments_metadata.py:170, \_defi_instruments.py:60,
  plus 4 migrate scripts) — Phase 2 search-and-replace still actionable. Phase 4 codex doc was already shipped but
  listed as `[ ]` in the plan — flipping below.

## Context

The MTDS manifest shards at bundle level where it makes sense (options_chain, futures_chain, combo_chain — if one
strike/expiry fails they all fail together). But consumers (strategy-service, features, UI) need to be able to:

1. Download the full bundle (existing: load the whole parquet)
2. Filter to a specific instrument within a bundle (e.g., "give me BTC-25MAR26-50000-C from the DERIBIT options_chain
   for 2026-04-17") without loading 162M rows into memory

The pyarrow predicate pushdown pattern already exists in `tardis_adapter.py:ae34a70` for the smoke VM case (filtering
instrument_ids from a bulk parquet). That logic needs to be extracted into a clean public API in MTDS so any consumer
can call it — both for bundle-level and per-instrument access.

The manifest stays at bundle granularity (correct: if options_chain fails, the whole strike surface is unavailable — you
can't partially backfill individual strikes). The download function is the layer that supports per-symbol access by
pushing the filter down to pyarrow row group statistics.

## Scope

**In-scope:**

- New `MtdsReader` or `CanonicalParquetReader` class in MTDS (or UTL if shared)
- `read_shard(venue, date, data_type, instrument_type, instrument_id=None, underlying=None, **filters)` method:
  - `instrument_id=None` → returns full bundle (all rows)
  - `instrument_id="BTC-25MAR26-50000-C"` → pyarrow predicate pushdown, returns only matching rows
- Works for all shard types: per-symbol (perpetuals, spot) and bulk (options_chain, futures_chain, combo_chain)
- Manifest lookup: resolves GCS path from manifest columns; raises `ShardNotFoundError` if no manifest row exists
- Unit tests: verify predicate pushdown skips row groups (check `pq.read_table` called with `filters=`)
- Integration test: load real options_chain parquet, filter to 1 symbol, verify memory usage stays low

**Out-of-scope:**

- Changing manifest shard granularity (stays at bundle level)
- Streaming/paginated access for very large bundles (future optimization)
- REST API endpoint (this is a library function for internal consumers)

## Pre-audit manifest

| Repo | File                                                                                                  | Action                                |
| ---- | ----------------------------------------------------------------------------------------------------- | ------------------------------------- |
| MTDS | `market_tick_data_service/reader.py` (new)                                                            | `CanonicalParquetReader` class        |
| MTDS | `market_tick_data_service/__init__.py` or `market_interface/__init__.py`                              | Export `CanonicalParquetReader`       |
| MTDS | `tests/unit/test_canonical_parquet_reader.py` (new)                                                   | Unit tests with mocked GCS + parquet  |
| UAC  | `unified_api_contracts/mtds.py` or `market_data.py`                                                   | Export `ShardNotFoundError` exception |
| UTL  | Consider: if `CanonicalParquetReader` is broadly useful, move to `unified_trading_library/readers.py` |

## Design

```python
class CanonicalParquetReader:
    def read_shard(
        self,
        venue: str,
        date: date,
        data_type: str,
        instrument_type: str,
        instrument_id: str | None = None,       # None = full bundle
        underlying: str | None = None,
        quote_asset: str | None = None,
        margin_type: str | None = None,
        columns: list[str] | None = None,       # column projection
    ) -> pd.DataFrame:
        """
        Resolves GCS path via manifest lookup, then reads parquet.
        If instrument_id is set, applies pyarrow filters=[("symbol","==",instrument_id)]
        so pyarrow skips non-matching row groups — O(1) for exact match on bulk parquets.
        Raises ShardNotFoundError if no manifest row matches.
        """

    def list_instruments(
        self,
        venue: str,
        date: date,
        data_type: str,
        instrument_type: str,
        underlying: str | None = None,
    ) -> list[str]:
        """
        Returns distinct instrument_ids within a bundle without loading all data.
        Uses parquet metadata (row group statistics) where available, else reads
        `symbol` column only (column projection).
        """
```

## Phases

### Phase 1 — `CanonicalParquetReader` implementation (SEQUENTIAL)

> **Phase 1 status 2026-05-06**: PARTIAL — class shipped MTDS `2095d1b` (2026-04-24) at
> `market_tick_data_service/reader.py` (386 lines + 472-line test suite). Supports CeFi / TradFi / Sports shard keys.
> **Two axes from the new shard-granularity HANDOVER are missing** and block DeFi + Prediction reads:
>
> - **DeFi**: per HANDOVER lines 130–145, `chain` is a first-class shard-key axis (e.g. `AAVEV3-ETHEREUM` vs
>   `AAVEV3-ARBITRUM` are distinct shards). Current
>   `read_shard(venue, data_type, instrument_type, target_date, instrument_id)` derives asset_group from venue but
>   doesn't accept `chain` — DeFi reads on chain-agnostic venue tokens may collide / silently return wrong-chain rows.
> - **Prediction**: per HANDOVER line 143, `canonical_question_group` is the bundling axis (analog of options_chain).
>   Currently flagged as "most likely greenfield bit" — UAC SSOT for `market_id → canonical_question_group` mapping may
>   not exist yet. Prediction reads need this once the UAC SSOT lands.
>
> **Coordination**: see `infrastructure_master_2026_05_07.md` (folds in
> `plans/archive/shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md`). Phase 1 follow-up is to extend
> `read_shard()` signature with optional `chain: str | None = None` (validated against UAC `CHAIN_RPC_TEMPLATES`) and
> `canonical_question_group: str | None = None` (validated against the prediction SSOT once it lands). The original
> Phase 1 scope (CeFi/TradFi/Sports) is shipped — these are additive extensions, not a re-design.

- [x] [AGENT] P0. Create `market_tick_data_service/reader.py` with `CanonicalParquetReader` class. Constructor takes
      `ManifestReader` (for GCS path resolution) and `gcs_client`. `read_shard()`: look up manifest row → build GCS path
      → `pq.read_table(path, filters=filters if instrument_id else None)` → return as pd.DataFrame.
      `list_instruments()`: read `symbol` column only via `columns=["symbol"]` projection.
      `ShardNotFoundError(venue, date, data_type)`: raised when manifest has no matching row. **Done 2026-04-24 MTDS
      `2095d1b`** — class at `market_tick_data_service/reader.py` (386 lines).
- [x] [AGENT] P0. Unit tests in `tests/unit/test_canonical_parquet_reader.py`: (a) Full bundle read: mock GCS returns
      3-row parquet → all 3 rows returned, no filters applied. (b) Per-instrument read: mock GCS returns 1000-row
      parquet → `pq.read_table` called with `filters=[("symbol","==","BTC-25MAR26-50000-C")]` → only matching rows
      returned. (c) `list_instruments`: verify `columns=["symbol"]` passed to pyarrow (no full load). (d)
      `ShardNotFoundError` raised when manifest has no matching row. **Done 2026-04-24 MTDS `2095d1b`** —
      `tests/market_interface/unit/test_canonical_parquet_reader.py` (472 lines).
- [x] [AGENT] P0. Export `CanonicalParquetReader` and `ShardNotFoundError` from MTDS public API. **Done 2026-04-24 MTDS
      `2095d1b`**.
- [x] [QG] P0. `cd market-tick-data-service && bash scripts/quality-gates.sh` — **Done 2026-05-06** (this session, 86s
      green, all gates pass including the new STEP 5.63 run_lifecycle pairing gate;
      `mtds_canonical_sharding_alignment_2026_03_31` Phase 2 closeout).
- [x] [SCRIPT] P0. Quickmerge MTDS. **Done 2026-04-24** as part of `2095d1b`.

### Phase 1.5 — DeFi `chain` + Prediction `canonical_question_group` axis extension (NEW — added 2026-05-06)

- [ ] [AGENT] P0. Extend `CanonicalParquetReader.read_shard()` signature with `chain: str | None = None` for DeFi reads
      (when present, validates via UAC `CHAIN_RPC_TEMPLATES` keys and routes to the chain-specific shard path:
      `asset_group=defi/chain={CHAIN}/venue={PROTOCOL}/...`). Default `None` preserves CeFi/TradFi/Sports behaviour.
      [AUDIT 2026-05-07: FRESH — actionable; `grep "chain:|canonical_question_group:" reader.py` shows 0 hits, axes not
      yet plumbed; UAC `CHAIN_RPC_TEMPLATES` exists; CRITICAL-PATH for 2026-05-23 deadline given DeFi
      protocol-multi-chain collision risk]
- [ ] [AGENT] P0. Extend `read_shard()` signature with `canonical_question_group: str | None = None` for Prediction
      reads — gated on the UAC SSOT for `market_id → canonical_question_group` mapping (per HANDOVER line 143). Skip
      until that SSOT lands; coordinate with the shard-granularity stream. [AUDIT 2026-05-07: FRESH — actionable; UAC
      `bb24aba` (PREDICTION_GROUPS skeleton) + UAC `af2bc9b` (canonical-question-group SSOT + lifecycle + classifier)
      shipped — gating SSOT now PARTIALLY landed; can ship the read-side axis now]
- [ ] [AGENT] P0. Unit tests for the two new axes — DeFi chain-collision case (same protocol, two chains, different
      shard rows) and Prediction canonical_question_group filter. [AUDIT 2026-05-07: BLOCKED-ON
      Phase-1.5-axis-extension]
- [ ] [QG] P0. `cd market-tick-data-service && bash scripts/quality-gates.sh` [AUDIT 2026-05-07: BLOCKED-ON
      Phase-1.5-axis-extension]
- [ ] [SCRIPT] P0. Quickmerge MTDS. [AUDIT 2026-05-07: BLOCKED-ON Phase-1.5-axis-extension]

### Phase 2 — Consumer wiring (PARALLEL, after Phase 1 merged)

- [ ] [AGENT] P1. Update any existing MTDS download helpers that currently do `pd.read_parquet(path)` directly to use
      `CanonicalParquetReader.read_shard()` instead. Search:
      `rg "pd\.read_parquet" market-tick-data-service/market_tick_data_service --type py`. This ensures all internal
      consumers benefit from path resolution and pushdown automatically. [AUDIT 2026-05-07: FRESH — actionable; 11
      direct-call sites confirmed: `kalshi_adapter.py:297`, `tardis_adapter.py:1648/1966/2124`,
      `polymarket_adapter.py:626`, `_instruments_metadata.py:170`, `_defi_instruments.py:60`, plus 4 migrate scripts]
- [ ] [AGENT] P1. If `CanonicalParquetReader` is generically useful (features-service, strategy-service), move to
      `unified_trading_library/readers.py` and re-export from MTDS for backwards compatibility. Decide after Phase 1 —
      if >1 non-MTDS repo would import it, move it; otherwise keep in MTDS. [AUDIT 2026-05-07: FRESH — actionable but P1
      deferral acceptable]
- [ ] [QG] P1. QG on all affected repos. [AUDIT 2026-05-07: BLOCKED-ON Phase-2-consumer-wiring]
- [ ] [SCRIPT] P1. Quickmerge. [AUDIT 2026-05-07: BLOCKED-ON Phase-2-consumer-wiring]

### Phase 3 — Integration test (SEQUENTIAL after Phase 1)

- [ ] [AGENT] P1. Integration test: `tests/integration/test_canonical_parquet_reader_integration.py`. Uses a real
      (small) options_chain parquet fixture (or downloads a test date from GCS in CI with `@pytest.mark.allow_network`).
      Verifies: (a) Full bundle returns expected row count. (b) Per-instrument filter returns only the matching symbol's
      rows. (c) Memory RSS during per-instrument read stays below 500 MB even when full bundle is >1 GB parquet. [AUDIT
      2026-05-07: FRESH — actionable; verified `tests/integration/` has no `*canonical_parquet_reader*` file (only
      `test_library_contracts.py`); P1 deferral acceptable for May-23 deadline]
- [ ] [QG] P1. `cd market-tick-data-service && bash scripts/quality-gates.sh` [AUDIT 2026-05-07: BLOCKED-ON
      Phase-3-integration-test]
- [ ] [SCRIPT] P1. Quickmerge MTDS. [AUDIT 2026-05-07: BLOCKED-ON Phase-3-integration-test]

### Phase 4 — Codex doc

- [x] [AGENT] P1. Write `codex/02-data/mtds-download-api.md` (scope: [engineer]): Documents `CanonicalParquetReader` —
      when to use full bundle vs per-instrument filter, memory characteristics, manifest dependency,
      `ShardNotFoundError` handling pattern. [AUDIT 2026-05-07: DONE —
      `unified-trading-pm/codex/02-data/mtds-download-api.md` exists, 145 lines, `scope: [engineer]` frontmatter
      present]
- [ ] [SCRIPT] P1. Quickmerge PM. [AUDIT 2026-05-07: STALE — codex doc is already in PM (verified via `ls`); a
      stand-alone quickmerge for it is no longer needed; the doc was committed as part of an earlier PM session]

## Success criteria

- **API gate:**
  `CanonicalParquetReader.read_shard(venue="DERIBIT", date=..., data_type="options_chain", instrument_type="option", instrument_id="BTC-25MAR26-50000-C")`
  returns a DataFrame with only that symbol's rows.
- **Memory gate:** Per-instrument read on a >1 GB parquet stays below 500 MB RSS (verified by integration test).
- **Predicate gate:** Unit test confirms `pq.read_table` receives `filters=[("symbol","==","...")]` when `instrument_id`
  is set; no filters when `instrument_id=None`.
- **Code gates:** MTDS QG green; no `pd.read_parquet(path)` direct calls remaining in MTDS source.
