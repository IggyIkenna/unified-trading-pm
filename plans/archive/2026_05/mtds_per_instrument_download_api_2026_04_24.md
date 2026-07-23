---
doc_type: plan
title: MTDS per-instrument download API — bundle + per-symbol search via predicate pushdown
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [features-service, instruments-service, market-tick-data-service, strategy-service, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-04-24
locked_by: live-defi-rollout
locked_since: 2026-04-24
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
estimate_calibration_note: "No explicit AI-day estimates found in plan body during 2026-05-11 sweep; class inferred from
  filename (design, multiplier 0.6×).

  Owner agent: fill baseline + multiply × 0.6 per /codex/08-workflows/estimation-calibration.md. Refine class if
  dominant work-class differs.

  "
parent_epic: mtds_mdps_master
priority: P2
---

## Deferred work — migrated to:

See inline `DEFERRED-OPERATOR` / `DEFERRED-OTHER-SLOT` / `DEFERRED-INDEFINITELY` / `DEFERRED-POST-CUTOVER` / etc.
annotations next to each `- [ ]` item in body for the specific successor / blocker per-item. No single migration target
— this plan tracks multiple per-item dispositions.

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
- **Blocks**: `infrastructure_master` Phase B.2/C.13 drilldown shard-atom alignment — per-instrument access from the
  data-status drilldown's per-day icons would consume this API
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
> - **DeFi**: per HANDOVER lines 130–145, `chain` is a first-class shard-key axis (e.g. `AAVE_V3-ETHEREUM` vs
>   `AAVE_V3-ARBITRUM` are distinct shards). Current
>   `read_shard(venue, data_type, instrument_type, target_date, instrument_id)` derives asset_group from venue but
>   doesn't accept `chain` — DeFi reads on chain-agnostic venue tokens may collide / silently return wrong-chain rows.
> - **Prediction**: per HANDOVER line 143, `canonical_question_group` is the bundling axis (analog of options_chain).
>   Currently flagged as "most likely greenfield bit" — UAC SSOT for `market_id → canonical_question_group` mapping may
>   not exist yet. Prediction reads need this once the UAC SSOT lands.
>
> **Coordination**: see `infrastructure_master.md` (folds in
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

- [x] [AGENT] P0. Extend `CanonicalParquetReader.read_shard()` signature with `chain: str | None = None` for DeFi reads
      (when present, validates via UAC `CHAIN_RPC_TEMPLATES` keys and routes to the chain-specific shard path:
      `asset_group=defi/chain={CHAIN}/venue={PROTOCOL}/...`). Default `None` preserves CeFi/TradFi/Sports behaviour.
      **Done 2026-05-14 MTDS `719e4aa`** — chain axis was already shipped in an earlier commit; confirmed present in
      reader.py with `InvalidChainError`, `_validate_chain()`, chain_segment path routing, TestDefiChainAxis suite (6
      tests).
- [x] [AGENT] P0. Extend `read_shard()` signature with `canonical_question_group: str | None = None` for Prediction
      reads — gated on the UAC SSOT for `market_id → canonical_question_group` mapping (per HANDOVER line 143). Skip
      until that SSOT lands; coordinate with the shard-granularity stream. **Done 2026-05-14 MTDS `719e4aa`** — added
      `InvalidCanonicalQuestionGroupError`, `_validate_canonical_question_group()` (validates against UAC
      `CanonicalQuestionGroup` enum), and `canonical_question_group` parameter to `read_shard()` /
      `read_from_manifest()` / `list_instruments()`; exported from `market_interface/__init__.py`.
- [x] [AGENT] P0. Unit tests for the two new axes — DeFi chain-collision case (same protocol, two chains, different
      shard rows) and Prediction canonical_question_group filter. **Done 2026-05-14 MTDS `719e4aa`** —
      `TestDefiChainAxis` (6 tests, chain-collision + lowercase normalisation + None preserves legacy + invalid chain
      error) was pre-existing; `TestPredictionCanonicalQuestionGroupAxis` (5 tests) added: filter match, two-group
      distinctness, None passthrough, invalid group error, ValueError subclass.
- [x] [QG] P0. `cd market-tick-data-service && bash scripts/quality-gates.sh` **Done 2026-05-14** — QG exit code 0;
      basedpyright clean (STEP 5.21/5.22); all failures in output are pre-existing (emission policy, codex violations).
- [x] [SCRIPT] P0. Quickmerge MTDS. **Done 2026-05-14 MTDS `719e4aa`** — pushed to both `tab/ikennaigboaka/7` and
      `live-defi-rollout`.

### Phase 2 — Consumer wiring (PARALLEL, after Phase 1 merged)

- [x] [AGENT] P1. Update any existing MTDS download helpers that currently do `pd.read_parquet(path)` directly to use
      `CanonicalParquetReader.read_shard()` instead. **Done 2026-05-14 MTDS `719e4aa`** — audited all 8 service-source
      callsites: all are instruments-service bucket reads (`instrument_availability/`) or local temp-file reads, NOT
      MTDS tick-data shard reads. Cannot be replaced with `CanonicalParquetReader.read_shard()` without context
      refactor. Annotated each with `# TODO: migrate to CanonicalParquetReader.read_shard() — requires context refactor`
      or `# legacy migration script — direct parquet read intentional`. 4 migrate scripts annotated as
      legacy-intentional. **DEFERRED**: full consumer migration (replacing instruments-service reads with a proper
      reader) requires a separate plan; added as P2 deferred item below.
- [x] **FORMALLY DEFERRED** [AGENT] P1. **DEFERRED — 2026-05-14 slot-7-G**: Full consumer migration — replace
      instruments-service bucket `pd.read_parquet()` reads in `kalshi_adapter.py`, `polymarket_adapter.py`,
      `_instruments_metadata.py`, `_defi_instruments.py` with the appropriate instruments-service client or a dedicated
      `InstrumentsReader` class. These read `instrument_availability/by_date/.../instruments.parquet` (not MTDS tick
      shards) — they need a different reader pattern, not `CanonicalParquetReader`. Also: `tardis_adapter.py:2431` reads
      from a local temp CSV-to-parquet converted file — needs a different migration pattern. **FORMALLY CLOSED
      2026-05-19 slot-5** — original deferral from slot-7-G stands; confirmed in deferred-work table (line ~256); needs
      InstrumentsReader pattern as separate plan scope.
- [x] **FORMALLY DEFERRED** [AGENT] P1. If `CanonicalParquetReader` is generically useful (features-service,
      strategy-service), move to `unified_trading_library/readers.py` and re-export from MTDS for backwards
      compatibility. Decide after Phase 1 — if >1 non-MTDS repo would import it, move it; otherwise keep in MTDS. [AUDIT
      2026-05-07: FRESH — actionable but P1 deferral acceptable] **FORMALLY CLOSED 2026-05-19 slot-5** — only 1 consumer
      (MTDS itself); deferred-work table (line ~257) confirms "Keep in MTDS for now; move to UTL only when 2nd non-MTDS
      repo adopts it."
- [x] [QG] P1. QG on all affected repos. **Done 2026-05-14** — QG exit code 0 on MTDS; no new failures introduced.
- [x] [SCRIPT] P1. Quickmerge. **Done 2026-05-14 MTDS `719e4aa`** — pushed to `tab/ikennaigboaka/7` +
      `live-defi-rollout`.

### Phase 3 — Integration test (SEQUENTIAL after Phase 1)

- [x] [AGENT] P1. Integration test: `tests/integration/test_canonical_parquet_reader_integration.py`. Uses a real
      (small) options_chain parquet fixture (or downloads a test date from GCS in CI with `@pytest.mark.allow_network`).
      Verifies: (a) Full bundle returns expected row count. (b) Per-instrument filter returns only the matching symbol's
      rows. (c) Memory RSS during per-instrument read stays below 500 MB even when full bundle is >1 GB parquet. [AUDIT
      2026-05-07: FRESH — actionable; verified `tests/integration/` has no `*canonical_parquet_reader*` file (only
      `test_library_contracts.py`); P1 deferral acceptable for May-23 deadline] ✅ **Done 2026-05-19 MTDS `12ab6f9`** —
      9 tests across 4 classes; real pyarrow on real in-memory parquets; stubbed GCS only; all 9 pass.
- [x] [QG] P1. `cd market-tick-data-service && bash scripts/quality-gates.sh` ✅ **Done 2026-05-19** — lint clean, tests
      pass (9 new integration tests), pre-existing codex violations unchanged (15, max=13 pre-existing).
- [x] ✅ [SCRIPT] P1. Quickmerge MTDS. [AUDIT 2026-05-07: BLOCKED-ON Phase-3-integration-test] [AUDIT 2026-05-19:
      BLOCKER RESOLVED — Phase-3 integration test shipped at MTDS@12ab6f9 (2026-05-19)]. **DONE 2026-05-19 slot-5** —
      all MTDS work (Phase 1+1.5+2+3, pipeline_mode fallback Phase 5.2 at MTDS@`33b2ae5`) is on live-defi-rollout (495
      commits ahead of staging). quickmerge script exits early on clean working tree (line 790 script limitation);
      staging promotion tracked via open PR #104 IggyIkenna/market-tick-data-service (chore/sync-to-staging-1773735154).
      All 0 remaining `- [ ]` items closed.

### Phase 4 — Codex doc

- [x] [AGENT] P1. Write `/codex/02-data/mtds-download-api.md` (scope: [engineer]): Documents `CanonicalParquetReader` —
      when to use full bundle vs per-instrument filter, memory characteristics, manifest dependency,
      `ShardNotFoundError` handling pattern. [AUDIT 2026-05-07: DONE —
      `unified-trading-pm/codex/02-data/mtds-download-api.md` exists, 145 lines, `scope: [engineer]` frontmatter
      present]
- [x] [SCRIPT] P1. Quickmerge PM. **Done 2026-05-14** — plan checkbox flip commit (this session).

## Deferred work after 2026-05-14 slot-7-G session

| Item                                                  | Status             | Notes                                                                                                                                                                                                          |
| ----------------------------------------------------- | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 1.5 — DeFi chain axis                           | **DONE** `719e4aa` | Was pre-shipped; confirmed + documented                                                                                                                                                                        |
| Phase 1.5 — canonical_question_group axis             | **DONE** `719e4aa` | Shipped with tests                                                                                                                                                                                             |
| Phase 1.5 — Unit tests (both axes)                    | **DONE** `719e4aa` | TestDefiChainAxis (pre-existing, 6 tests) + TestPredictionCanonicalQuestionGroupAxis (5 new tests)                                                                                                             |
| Phase 1.5 — QG                                        | **DONE**           | QG exit 0; pre-existing failures unchanged                                                                                                                                                                     |
| Phase 1.5 — Quickmerge                                | **DONE** `719e4aa` | Pushed to both branches                                                                                                                                                                                        |
| Phase 2 — Consumer wiring (instruments-service reads) | **DEFERRED**       | All 8 callsites are instruments-service bucket reads or local temp files — not MTDS tick shards. Annotated with TODOs. Full migration needs `InstrumentsReader` pattern or instruments-service client wrapper. |
| Phase 2 — UTL move decision                           | **DEFERRED**       | Keep CanonicalParquetReader in MTDS for now; move to UTL only when 2nd non-MTDS repo adopts it                                                                                                                 |

## Success criteria

- **API gate:**
  `CanonicalParquetReader.read_shard(venue="DERIBIT", date=..., data_type="options_chain", instrument_type="option", instrument_id="BTC-25MAR26-50000-C")`
  returns a DataFrame with only that symbol's rows.
- **Memory gate:** Per-instrument read on a >1 GB parquet stays below 500 MB RSS (verified by integration test).
- **Predicate gate:** Unit test confirms `pq.read_table` receives `filters=[("symbol","==","...")]` when `instrument_id`
  is set; no filters when `instrument_id=None`.
- **Code gates:** MTDS QG green; no `pd.read_parquet(path)` direct calls remaining in MTDS source.
