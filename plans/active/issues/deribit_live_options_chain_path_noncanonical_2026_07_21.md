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
status: open
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

- [ ] 1. [DATA] P1. Confirm via `gcloud storage ls`/manifest query whether `deribit-options-chain` has actually been RUN
      in prod (any objects exist under the `pipeline_mode=live_deribit/...` prefix) — sizes the blast radius before
      choosing copy-forward vs rewrite-in-place.
- [ ] 2. [DATA] P1. Rewrite `_write_shard` to build its path via UAC `build_cefi_partition_path` (or the shared
      `_build_partition_path_for_asset_group`), with `instrument_type="options_chain"`, deriving `quote_asset`/
      `margin_type` via `derive_settlement_dimensions` (same helper `_cefi_chain_tail_v6` uses) so this handler lands on
      the SAME v6 canonical path W1/W2 do — chain fan-in (`ticks.parquet`) instead of one-file-per-write.
- [ ] 3. [REVIEW] P1. Audit `manifest_recorder`/honest-absence bookkeeping for this handler — confirm (or fix) that its
      manifest shard-atom matches the corrected object path post-fix.
- [ ] 4. [DATA] P2. If prod objects exist under the legacy `pipeline_mode=live_deribit/...` shape (todo 1 confirms
      non-zero), migrate them (copy → verify → human-only purge of the legacy shape) — same collision caveat as
      `cefi_chain_tail_v6_canonicalisation_2026_07_21.md` (one-file-per-write means NO collision risk here, unlike the
      v5 bare-underlying fan-in case, but confirm before assuming).
