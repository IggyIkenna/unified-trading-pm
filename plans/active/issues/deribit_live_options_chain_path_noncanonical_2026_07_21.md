---
doc_type: issue
title:
  DERIBIT live options-chain handler writes a THIRD, non-canonical GCS path shape (neither v5 nor v6) — unreachable by
  the reader
summary: >-
  Discovered 2026-07-21 while answering todo 1 of cefi_chain_tail_v6_canonicalisation_2026_07_21.md (which W1 vs W2
  writer reaches cefi options_chain/futures_chain in prod). `market_tick_data_service/cli/handlers/
  deribit_options_chain_handler.py` (`DeribitOptionsChainHandler`, wired live in `cli/main.py` as the
  `deribit-options-chain` operation) is a THIRD write path — neither W1 (`PartitionedTickWriter`) nor W2 (the Tardis
  lane) — that hand-builds its own GCS path inline (`_write_shard`, line ~513-518) instead of going through UAC
  `build_cefi_partition_path` or ANY canonical builder. The resulting path is structurally invalid against BOTH the v5
  and v6 cefi chain shapes and is never found by `reader.py`'s v6-then-v5 probe.
status: resolved
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [canonicalisation, cefi, chain-tail, gcs-path, reader, live-write-path, deribit, data-correctness]
related:
  [
    /plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md,
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /codex/02-data/canonical-cutover-register.md,
  ]
created: 2026-07-21
last_updated: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.24
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
  cefi_satellite_ao_dispatch_batch2_2026_07_26.md (all 4 todos closed 2026-07-26; archival ritual not yet run)
source: discovered while resolving cefi_chain_tail_v6_canonicalisation_2026_07_21.md todo 1 (2026-07-21)
depends_on: []
---

# DERIBIT live options-chain handler — non-canonical path, unreachable by the reader

## What was found

While enumerating which writer actually reaches cefi `options_chain`/`futures_chain` in prod (todo 1 of
`cefi_chain_tail_v6_canonicalisation_2026_07_21.md`), grepping for cefi chain production write paths surfaced a THIRD
lane that neither that issue's grounding section nor (apparently) the reader accounts for:

- **W1** (`market_tick_data_service/engine/orchestrator/partitioned_writer.py::PartitionedTickWriter`, dispatched via
  `engine/orchestrator/venue_fetch.py::_process_venue`) — the generic native-REST per-venue writer.
- **W2** (`market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py`) — the Tardis bulk lane, already
  emits v6.
- **W3 (this finding)** — `market_tick_data_service/cli/handlers/deribit_options_chain_handler.py`
  (`DeribitOptionsChainHandler`), registered live in `cli/main.py:599` as the `deribit-options-chain` CLI operation. Per
  its own docstring it is "NOT wired to a backfill runner; it is built for live / replay dispatch only" — i.e. this is
  the actual LIVE Deribit options-chain source, not W1 or W2.

`_write_shard` (`deribit_options_chain_handler.py:500-523`) hand-builds the GCS path inline:

```python
path = (
    f"pipeline_mode=live_deribit/asset_group=cefi/"
    f"venue={_DERIBIT_VENUE}/instrument_type=option/data_type={_DATA_TYPE}/"
    f"day={day_str}/underlying={currency}/expiry={exp_safe}/"
    f"{currency}_{exp_safe}_{ts_str}.parquet"
)
```

Problems, each independently disqualifying vs the canonical shape
(`raw_tick_data/by_date/day={D}/ pipeline_mode={mode}/asset_group=cefi/venue={V}/instrument_type={IT}/data_type={DT}/{TAIL}`,
SSOT `cross-asset-canonical-target-ssot.md`):

1. **Missing the `raw_tick_data/by_date/` prefix entirely** — every canonical builder (`build_cefi_partition_path` et
   al.) emits this prefix; this handler starts directly at `pipeline_mode=`.
2. **`day=` is NOT the first partition segment** — canonical order is `day=` then `pipeline_mode=`; this handler emits
   `pipeline_mode=` then `asset_group=`/`venue=`/`instrument_type=`/`data_type=` and only THEN `day=` — day is
   effectively nested five segments too deep.
3. **`instrument_type=option`** (singular) — the canonical chain partition key is `options_chain` (plural/chain-form);
   `option` does not match `CEFI_CHAIN_INSTRUMENT_TYPES` (`{"options_chain", "futures_chain"}`) nor any reader probe.
4. **Extra `expiry=` hive segment** not in the canonical schema (canonical chain tail is exactly
   `underlying=/quote=/ margin=/ticks.parquet` — three segments, not four, and no `quote=`/`margin=` at all here).
5. **Filename is `{currency}_{expiry}_{timestamp}.parquet`**, not `ticks.parquet` (chain fan-in) nor a canonical
   `instrument_id` stem — every write creates a NEW, never-superseded file (no fan-in, so historical objects accumulate
   one-per-write rather than fanning into the day's chain bundle).

**Net effect**: `reader.py:402-403`'s v6-then-v5 probe (`.../underlying={ROOT}/quote={Q}/margin={M}/ticks.parquet` then
`.../underlying={id}/ticks.parquet`, both rooted at the canonical
`raw_tick_data/by_date/day=.../asset_group=cefi/ venue=DERIBIT/instrument_type=options_chain/data_type=.../` prefix) can
**never** find objects this handler writes — they live under a structurally different path with the WRONG
`instrument_type` value. Live Deribit options-chain data captured via this handler is silently unreadable by the
standard MTDS reader; only a bespoke reader that knows this exact ad-hoc shape could recover it.
`manifest_recorder`/honest-absence bookkeeping for this handler was not audited as part of this discovery — unknown
whether it also diverges (separate check needed, see todos).

## Why this is a SEPARATE finding from `cefi_chain_tail_v6_canonicalisation_2026_07_21.md`

That issue is about the v5-vs-v6 **quote/margin tail** axis on paths that are otherwise correctly rooted
(`raw_tick_data/by_date/day=.../asset_group=cefi/venue=.../instrument_type=options_chain/data_type=.../underlying=.../ [quote=.../margin=.../]ticks.parquet`).
This finding is about a write path that fails the canonical STRUCTURE at a much more basic level (missing prefix, wrong
segment order, wrong `instrument_type` value, extra segment, non-fan-in filename) — it would fail
`unified_api_contracts.canonical.canonical_path_violations()` on multiple STRUCTURAL grounds simultaneously, independent
of the quote/margin question. Fixing the W1 quote/margin derivation (that issue's todo 2) does nothing for this handler,
since it does not use `PartitionedTickWriter` at all.

## Todos

- [x] ✅ 1. [DATA] P1. **DONE 2026-07-26 (slot-8, `review`/`data_engineering`).** Targeted (non-recursive) delimiter
      listing of `gs://market-data-tick-cefi-prd-central-element-323112/pipeline_mode=live_deribit/` returned "matched
      no objects"; the bucket's top-level listing confirms it (only `_index/`, `_migration_backup/`,
      `_migration_backups/`, `_quarantine/`, `_remediation_backups/`, `backfill-logs/`, `processed_candles/`,
      `raw_tick_data/`, `_vm_staging/` exist at root — no `pipeline_mode=live_deribit/` prefix at all). **Count: 0.**
      `deribit-options-chain` was never actually run in prod against this legacy shape (or ran and wrote nothing) — zero
      blast radius, no copy-forward needed.
- [x] ✅ 2. [DATA] P1. **DONE — shipped `market-tick-data-service@ec0df878`**
      (`cefi_satellite_ao_dispatch_batch1_2026_07_25.md`'s "Rewrite `deribit_options_chain_handler.py::_write_shard`"
      todo). `_write_shard` now builds its path via UAC `build_cefi_partition_path` (`instrument_type="options_chain"`),
      deriving `quote_asset`/`margin_type` via `derive_settlement_dimensions`; `record_captured`'s `instrument_type`
      argument matches (`"options_chain"`, not the legacy singular `"option"`); chain fan-in (`ticks.parquet`) verified
      by `test_write_shard_fans_in_across_calls_same_day_underlying`.
- [x] ✅ 3. [REVIEW] P1. **DONE 2026-07-26 (slot-8, `review`) — found + fixed a real remaining mismatch.** The v6 object
      path encodes `instrument_type` as a path dimension (`build_cefi_partition_path`'s `instrument_type={IT}/`
      segment), and UTL's dedup key (`unified_trading_library/manifest_writer/_writer_io.py::_merge_dataframes`)
      includes `instrument_type` in `dedup_cols` whenever ANY row in the merged frame populates it. `record_captured`
      already passed `instrument_type="options_chain"` (todo 2's fix), but `DefiManifestRecorder.record_failed()` /
      `record_zero_rows()` never accepted or forwarded `instrument_type` at all — so a failed/zero-rows attempt for a
      shard wrote a manifest row keyed WITHOUT `instrument_type` while a captured retry for the SAME shard wrote WITH
      it, meaning the two rows have DIFFERENT dedup keys and `drop_duplicates(keep="last")` never collapses them — the
      exact "populated-vs-blank delta" footgun the UTL code's own comment warns about (a stale failed row would persist
      alongside a later captured row for the same logical shard instead of being replaced). Fixed by adding an optional
      `instrument_type: str = ""` kwarg (backward-compatible, defaults preserve every other DeFi handler's existing
      behaviour) to `DefiManifestRecorder.record_failed()`/`_emit_failed_row()`/`record_zero_rows()`, threaded to
      `_build_row_key()`/`record_empty()`, and updated `deribit_options_chain_handler.py`'s three failed/zero-rows call
      sites to pass `instrument_type="options_chain"` so all three record states (captured/failed/zero-rows) now key the
      identical shard atom. Covered by new tests in `test_defi_manifest_recorder.py` (recorder-level forwarding +
      non-breaking default) and `test_deribit_options_chain_handler.py` (handler-level, both `_collect_currency` and
      `_collect_expiry_shard` failure/zero-rows branches). `quality-gates.sh` green. Evidence:
      `market-tick-data-service@ed102ef8`.
- [x] ✅ 4. [DATA] P2. **DONE 2026-07-26 — CLOSED, no migration needed.** Todo 1 found zero prod objects under the
      legacy `pipeline_mode=live_deribit/...` shape, so there is nothing to copy-forward or purge.
