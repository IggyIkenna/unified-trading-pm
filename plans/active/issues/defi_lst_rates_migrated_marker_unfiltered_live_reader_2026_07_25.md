---
doc_type: issue
title:
  "features-service's OnChainDataLoader reads _migrated_* retirement markers as real lst_rates rows (no
  underscore-prefix filter) — silently double-counts rates today, and would silently drop data if the markers are purged
  as currently proposed"
summary: >-
  Found during the five-part delete-safety proof for
  plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md's lst_rates `_migrated_*` purge candidate (todo
  defi_dex_pool_symbol_fix_backfill_purge-001). `features-service/features_service/onchain/app/core/data_loader.py::
  OnChainDataLoader._probe_mtds_blobs` (line ~133) matches ANY blob under a day partition with `n.endswith(".parquet")
  and data_type_segment in n` — no filter excluding `_`-prefixed system markers. This is the matching logic behind
  `load_oracle_prices()` (line 475-511, explicitly probes `data_type="lst_rates"` at line 488-489), which is wired LIVE
  into `OnChainFeatureOrchestrator.compute_lst_features_for_day`
  (`features_service/onchain/engine/orchestrator.py:462,877`) via
  `LstYieldsComputeRunner`/`LstNativeRatesComputeRunner`. Empirical sampling (25 markers/venue,
  COINBASE/MAKER/ETHENA/SWELL, spread 2020-2026) found 76-100% of `_migrated_*` lst_rates markers for these venues
  ALREADY have a content-identical per-instrument twin sitting beside them in the same directory (R3 migration wrote the
  twin 2026-07-22/23, then renamed the source to `_migrated_*` — copy, not move, 100% content match on
  `exchange_rate`+`block_number` across 91/91 sampled pairs). Because the reader has no dedup and no underscore filter,
  `pl.concat(frames, how="diagonal_relaxed")` currently ingests BOTH the marker and its twin for any historical day it
  processes — a live, silent row-level double-count in LST rate/yield feature computation, independent of any delete
  decision. For the minority of markers WITHOUT a twin (24% COINBASE / 8% MAKER / 4% ETHENA / 0% SWELL in the sample),
  the marker is currently the ONLY row this same reader would find for that day — deleting it would silently drop that
  day from every future feature recompute.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [features-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [defi, lst-rates, migrated-markers, data-correctness, double-count, delete-safety, features-service]
related:
  [
    defi_dex_pool_symbol_fix_backfill_purge_2026_07_25,
    defi_migrated_marker_flagged_root_cause_clusters_2026_07_25,
    defi_write_defi_rows_leaf_symbol_not_canonical_id_capture_not_stopped_2026_07_24,
  ]
created: 2026-07-25
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
drift_direction: unknown
depends_on: []
source:
  [
    "found 2026-07-25 by an investigation-only sub-agent running the codex
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md five-part proof against
    defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md todo defi_dex_pool_symbol_fix_backfill_purge-001 (Part 4:
    grep+READ proof no live code reads the candidate)",
  ]
resolved_by: features-service@69753a7c88ba2d33b2def282632ce853d3739dee
locked_by:
locked_since:
---

# `_migrated_*` lst_rates markers are read live, unfiltered, by features-service — double-count risk + delete-blocker

## Why this exists

This is a Part-4 (readers) finding from the five-part delete-safety proof requested against the lst_rates `_migrated_*`
purge candidate. It blocks that purge on its own (a live reader still consumes the exact objects the plan proposes
deleting), and it is ALSO an independent, currently-live data-correctness bug that exists regardless of whether the
purge ever happens — hence its own issue doc per CLAUDE.md's "big finding (data-correctness / cross-repo) → NOTIFY
OPERATOR + issue doc" rule.

## The code path (grep+READ, not grep-then-conclude)

1. `features_service/onchain/app/core/data_loader.py:121-138`, `_probe_mtds_blobs`:
   ```python
   blob_names = [blob.name for blob in self.storage_client.list_blobs(bucket, prefix=prefix)]
   matched = [n for n in blob_names if n.endswith(".parquet") and data_type_segment in n]
   ```
   No exclusion for a `_`-prefixed leaf. Any object under the day partition whose path contains `data_type=lst_rates/`
   and ends in `.parquet` matches — including `_migrated_coinbase_ETHEREUM_....parquet`.
2. `data_loader.py:475-511`, `load_oracle_prices`: explicitly probes `("oracle_prices", "lst_rates")` (line 488-489),
   reads every matched URI with `pl.read_parquet`, and concatenates with `pl.concat(frames, how="diagonal_relaxed")`
   (line 506) — diagonal_relaxed tolerates the marker's slightly different/superset schema (old markers carry
   `schema_version`/`source`/`transport`/`total_staked`/`ts_event` columns the newer per-instrument leaf doesn't), so
   this does not raise; it silently unions both rows in.
3. `features_service/onchain/engine/orchestrator.py:462` and `:877` call
   `compute_lst_features_for_day(day, self.data_loader.load_oracle_prices, ...)` — this is the production LST
   yield/native-rate feature-compute entry point (`features_service/onchain/engine/lst_features.py`,
   `LstYieldsComputeRunner` / `LstNativeRatesComputeRunner` in `features_service/onchain/live/`). It is wired into the
   live orchestrator, not dead code, not behind a disabled flag.

## What this means today, independent of any delete

For any historical day where a `_migrated_*` lst_rates marker still sits beside its per-instrument twin (measured
76-100% of the sampled population for COINBASE/MAKER/ETHENA/SWELL — see the companion delete-safety report for this
purge candidate), a feature recompute for that day currently ingests the SAME on-chain rate twice: once via the marker,
once via the twin. `pl.concat` performs no row-level dedup at this layer. This is a live double-count in LST rate/yield
feature computation for any day that still carries both objects — not something the purge would introduce; it exists
right now, on every day the `_migrated_*` markers have not yet been cleaned up.

## What this means for the purge candidate

`plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` todo `defi_dex_pool_symbol_fix_backfill_purge-001`
proposes purging every lst_rates `_migrated_*` marker for COINBASE/SWELL/MAKER/ETHENA. Per the delete-safety protocol's
Part 4 ("a reader that currently raises still counts as a reader" — a fortiori one that succeeds and silently mixes bad
rows in counts too), this reader being live and unfiltered means the disposition cannot exceed `no-migrate-first`
regardless of Part 1/2/5 outcomes, until one of:

- `_probe_mtds_blobs` (and any sibling MTDS-output prober with the same pattern — check for copies) is fixed to exclude
  `_`-prefixed leaves, matching `rebuild_defi_manifest.py`'s existing convention for the same markers; or
- the markers are actually deleted (removing the double-count source), which is exactly the human-gated action this
  finding is currently blocking.

Fixing the reader is the lower-risk, non-prod-bucket-touching first step and does not require the human-only delete
approval.

## Full report

See the companion delete-safety five-part-proof report (this session's response to the dispatching agent) for the
per-venue twin-coverage sampling, content-match results, and the writer-side (Part 3) confirmation that
`migrate_defi_batch_to_per_instrument.py` is a completed one-off, not a live writer.

## Todos

- [x] [BACKEND] P1. **Fix `_probe_mtds_blobs`**
      (`features-service/features_service/onchain/app/core/data_loader.py:121-138`) to skip any leaf whose basename
      starts with `_` — matching `rebuild_defi_manifest.py`'s existing convention for the same markers. Audit for the
      same unfiltered-glob pattern elsewhere in MTDS-output consumers (any other
      `n.endswith(".parquet") and data_type_segment in n`-shaped match with no underscore exclusion). This is a
      non-destructive code fix (no GCS/prod-data touched) — does NOT require the human-only delete approval. **Done
      when**: a unit test asserts `_probe_mtds_blobs` excludes a `_migrated_*`-prefixed object from its match set while
      still matching the real per-instrument twin; `quality-gates.sh` green. —
      `features-service@69753a7c88ba2d33b2def282632ce853d3739dee`. Fixed `_probe_mtds_blobs` (`data_loader.py`) via a
      new `_is_retirement_marker()` helper (basename after the last `/` startswith `_`) added to the match predicate.
      Audit found the SAME unfiltered shape in two sibling MTDS-output DeFi raw_tick_data probers and fixed both:
      `onchain/calculators/perp_funding_rates_defi.py::     _load_raw_frame` (perp_funding needle-match) and
      `onchain/adapters/mtds_canonical_reader.py::     read_canonical_defi_parquets` (day_blobs listing feeding the
      `shard_suffix` match) — both would otherwise match a `_migrated_*` marker sitting at the identical hive path as
      its twin. `_resolve_parquet_files` (same file, MDPS-candle reader per its docstring) and
      `delta_one/app/core/data_loader.py` (`processed_candles/` MDPS output, not raw_tick_data DeFi) were checked and
      are out of scope — neither path can carry a `_migrated_*` marker. Evidence: 3 new unit tests
      (`test_onchain_data_loader.py::     TestProbeMtdsBlobs::test_excludes_migrated_retirement_marker_but_matches_real_twin`,
      `test_perp_funding_rates_defi.py::test_load_raw_frame_excludes_migrated_retirement_marker`,
      `test_mtds_canonical_reader.py::test_reader_skips_migrated_retirement_marker`), each constructing a real
      per-instrument leaf + a `_migrated_*` marker at the same shard path and asserting only the real leaf is
      matched/read (the marker's mock raises `AssertionError` if ever downloaded — never fires). `quality-gates.sh`
      green: 17826 passed, 209 skipped, 0 failed, sentinel `.qg_last_passed_sha` == HEAD before quickmerge.
- [ ] [OPERATOR] P2. **Re-verify + purge, only after the reader fix lands.** Re-run this delete-safety proof (or the
      sanctioned `delete_migrated_defi_markers_2026_07_23.py --dry-run`, which already implements the correct per-marker
      SAFE/FLAGGED disposition logic) with the reader fixed, then execute `defi_dex_pool_symbol_fix_backfill_purge-001`
      only for the SAFE population — never a blind glob-delete of "every `_migrated_*` lst_rates object for these 4
      venues," since the FLAGGED (no-twin) minority (up to ~24% for COINBASE in-sample) would lose its only surviving
      copy. Human-gated per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — no agent runs the actual
      delete. **UPDATE 2026-07-26**: the FLAGGED (no-twin) minority this todo was waiting on no longer exists — a
      copy-only (never-delete) fold one-off ran on an in-region SPOT VM
      (`canonical-migration-defi-lst-rates-fold-20260726-003855`,
      `market-tick-data-service@9150bc9fae4fe71b1961f4c46ed1c01933b6df5c`) and wrote the missing per-instrument twin for
      all 346 previously-FLAGGED markers (`=== SUMMARY === folded: 346`, `rc=0`). Independently re-verified (exhaustive,
      all 346, not sampled) via the same `verify_marker()` oracle this doc cites: 0 still-FLAGGED, 0 exceptions —
      COINBASE/MAKER/SWELL/ETHENA are each now at 100% twin coverage (was 87.55%/89.66%/99.58%/99.28% respectively; full
      before/after table in `plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`'s Progress Log). 12 of
      the newly-written leaves (3/venue) were read back directly and confirmed non-empty with the full wide schema
      intact. **The re-verify half of this todo is therefore done** (see that Progress Log for the full evidence) — only
      the **purge itself** remains, still correctly `[OPERATOR]`/un-executed/un-checked (prod-bucket delete, human-only
      per this doc's own citation).
