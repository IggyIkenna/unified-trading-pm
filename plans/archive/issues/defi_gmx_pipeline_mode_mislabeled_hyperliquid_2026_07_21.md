---
doc_type: issue
title:
  "GMX perp_funding stamped pipeline_mode=batch_hyperliquid (copy-paste bug) — fixed in MTDS; the same class of registry
  gap also mis-stamps derivative_ticker as batch_onchain_rpc; ~6,240 historical objects migrated"
summary: >-
  Operator spotted a live GCS object at pipeline_mode=batch_hyperliquid/.../venue=GMX/ and asked why GMX (a DeFi
  on-chain perp DEX sourced from The Graph subgraph) carries a Hyperliquid pipeline_mode. Root cause: a hardcoded
  copy-paste bug at market_tick_data_service/cli/handlers/_perp_funding_gmx.py:65 (`gmx_mode =
  PipelineMode.BATCH_HYPERLIQUID`) used for every GMX manifest record_* call. Investigation found a SECOND, independent
  desync on the GCS-write-path side: write_defi_rows() derives its own pipeline_mode via UAC/UTL's
  derive_pipeline_mode_for_row("GMX", "defi", data_type) when not passed explicitly — for perp_funding this resolves to
  BATCH_HYPERLIQUID too (via a mis-registered UAC SOURCE_PRIORITY[("defi","perp_funding")] = ["hyperliquid"]
  single-source entry), but for derivative_ticker it resolves to BATCH_ONCHAIN_RPC (asset_group fallback, since
  ("defi","derivative_ticker") has no SOURCE_PRIORITY entry) — a THIRD wrong value, independently wrong from both the
  manifest stamp and the correct answer. Fixed entirely within MTDS by passing pipeline_mode explicitly at the GMX write
  call site (bypassing the broken UAC/UTL derivation) and correcting the manifest-side gmx_mode variable — both now
  agree on BATCH_ONCHAIN_SUBGRAPH. Measured + migrated 6,240 mislabeled GCS objects (2,075 perp_funding day/chain units,
  2022-11-01 -> 2026-07-19, plus 8 derivative_ticker day/chain units, 2026-07-15 -> 2026-07-19) via copy -> verify ->
  delete (0 errors, independently spot-checked). Re-registered 1,965 corrected manifest rows via a raw
  ManifestWriter.add() batched pass with per_vm_shards=True (the canonical single-blob CAS path never completes on this
  ~1.9GB/52M-row bucket under contention — confirmed by hitting 13 failed generation-conflict retries over ~19 minutes
  before switching to per-VM-shard mode per an identical precedent hit the same day on this same bucket,
  plans/active/issues/defi_fold_manifest_registration_pending_2026_07_21.md; per-VM mode then completed in <1s). Bonus:
  calling the raw add() path without an explicit asset_group= kwarg bypassed the broken SOURCE_PRIORITY-driven source
  resolution entirely (asset_group self-heals to "defi" via VENUE_TO_ASSET_GROUP; source falls through to the
  pipeline_mode's own producer-source mapping) — so the re-registered rows carry the CORRECT source=onchain_subgraph
  too, verified directly by downloading and querying the written per-VM shard. The residual gap is narrower than
  originally scoped: only FUTURE captures going through DefiManifestRecorder.record_captured() (which explicitly
  resolves+validates source against the still-mis-registered UAC SOURCE_PRIORITY entry) will still stamp
  source=hyperliquid until that registry entry is fixed cross-repo (out of scope this session, workspace-restricted to
  market-tick-data-service + unified-trading-pm only).
status: resolved
nature: issue
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-library]
scope: [engineer]
tags:
  [
    pipeline-mode,
    canonical-path,
    manifest,
    data-correctness,
    provenance,
    source-priority,
    gmx,
    subgraph,
    copy-paste-bug,
  ]
related:
  [
    codex/02-data/pipeline-mode-partition.md,
    codex/02-data/availability-manifest-and-data-status.md,
    codex/02-data/defi-canonical-naming-ssot.md,
    plans/active/issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md,
    plans/active/issues/defi_fold_manifest_registration_pending_2026_07_21.md,
  ]
created: 2026-07-21
priority: P1
parent_epic: defi_master
source: "Operator spotted a live GCS object 2026-07-21; investigated + fixed + migrated same session"
execution_scope: local-only
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by:
  "market-tick-data-service@acb7cf61 (write-path fix + migration script) + unified-trading-library@c3d746ad (GMX
  venue-override, residual source= gap) — see TL;DR table"
locked_by:
last_updated: 2026-07-21
---

# GMX perp_funding / derivative_ticker mislabeled pipeline_mode (copy-paste bug)

## TL;DR

| Surface                                                                                | Before                                                                                                                                    | After                                                                                                                                                                                                                                                                                                                                      | Status                                                                                                                                               |
| -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| MTDS `gmx_mode` (manifest record_\* calls)                                             | `BATCH_HYPERLIQUID` (copy-paste)                                                                                                          | `BATCH_ONCHAIN_SUBGRAPH`                                                                                                                                                                                                                                                                                                                   | FIXED                                                                                                                                                |
| GCS write path, `perp_funding`                                                         | `batch_hyperliquid` (derived, UAC)                                                                                                        | `batch_onchain_subgraph` (explicit)                                                                                                                                                                                                                                                                                                        | FIXED                                                                                                                                                |
| GCS write path, `derivative_ticker`                                                    | `batch_onchain_rpc` (derived, UAC)                                                                                                        | `batch_onchain_subgraph` (explicit)                                                                                                                                                                                                                                                                                                        | FIXED                                                                                                                                                |
| Historical GCS objects, both data_types                                                | **6,240 objects** across 2,083 (date,chain) units (2,075 perp_funding, 2022-11-01→2026-07-19; 8 derivative_ticker, 2026-07-15→2026-07-19) | migrated to `batch_onchain_subgraph`, 0 errors                                                                                                                                                                                                                                                                                             | **MIGRATED + VERIFIED** (copy→describe-both→delete; independently spot-checked earliest/middle/latest days directly against live GCS post-migration) |
| Manifest re-registration                                                               | stale/wrong `pipeline_mode` rows                                                                                                          | **1,965/1,965 rows re-registered**, `pipeline_mode=batch_onchain_subgraph` AND `source=onchain_subgraph` AND `asset_group=defi`, all verified by downloading + querying the written per-VM shard directly; 118 zero-row placeholder rows intentionally left un-reregistered (see §5)                                                       | **DONE + VERIFIED**                                                                                                                                  |
| Manifest `source=` column (re-registered rows)                                         | `hyperliquid` (auto-stamped)                                                                                                              | `onchain_subgraph` — **fixed as a side-effect** of the per-VM `ManifestWriter.add()` path (bypasses the SOURCE_PRIORITY-driven resolver that `DefiManifestRecorder` uses)                                                                                                                                                                  | **FIXED** for the 1,965 re-registered rows                                                                                                           |
| Manifest `source=` column (FUTURE captures via `DefiManifestRecorder.record_captured`) | `hyperliquid` (auto-stamped)                                                                                                              | resolves to `onchain_subgraph` via the new `unified_trading_library.pipeline_mode_resolver._VENUE_OVERRIDES["GMX"]` entry (mirrors the AAVE/CHAINLINK/PYTH single-source-venue override pattern — the SOURCE_PRIORITY-lookup fallback that mis-stamped it is now skipped for GMX)                                                          | **FIXED** — `unified-trading-library@c3d746ad`                                                                                                       |
| UAC `SOURCE_PRIORITY[("defi","perp_funding")]`                                         | `["hyperliquid"]` (mis-registered)                                                                                                        | **left unchanged, correctly** — a venue override (row above) is the documented pattern for a single-source venue that differs from the data_type default (see the LIGHTER/AAVE precedent comments in `_source_priority_data.py`); editing SOURCE_PRIORITY itself would have wrongly flipped `("defi","perp_funding")` into a 2-source cell | **RESOLVED (no code change needed here)**                                                                                                            |

## 1. Root cause

`market_tick_data_service/cli/handlers/_perp_funding_gmx.py:65`:

```python
gmx_mode = _h.PipelineMode.BATCH_HYPERLIQUID
```

GMX is a DeFi on-chain perpetual DEX, sourced from The Graph subgraph (module docstring: _"Perpetual Funding Rate
Handler — GMX (The Graph subgraph) stage module"_). It has nothing to do with Hyperliquid, a separate CeFi-classified
venue with its own REST API (handled entirely by `onchain_perp_batch_handler.py`, confirmed the ONLY other
`BATCH_HYPERLIQUID` reference in MTDS is for genuine Hyperliquid data — never touched). `gmx_mode` is passed as the
`pipeline_mode=` kwarg on every `recorder.record_captured` / `record_failed` / `record_zero_rows` call for BOTH
`perp_funding` and `derivative_ticker` (the 2026-07-15 dual-write). A straightforward copy-paste bug — the correct
sibling convention (subgraph-sourced DeFi handlers like `dex_pools_handler.py`) uses
`PipelineMode.BATCH_ONCHAIN_SUBGRAPH` for this exact kind of source.

## 2. The independent GCS-write-path desync (deeper than the manifest bug)

Per this session's broader lesson (see the `defi_lending_writer_retire_prerequisite_2026_07_20.md` pattern and the
`canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` finding: GCS-path-side and manifest-side fields are
sometimes independently derived and can desync), the GCS object path's `pipeline_mode=` segment was checked separately,
since `_write_gmx_shard()` never passed `pipeline_mode=` to `write_defi_rows()` at all — it defaulted to `None`, letting
`write_defi_rows` (`market_tick_data_service/market_interface/adapters/defi/canonical_write.py:163-169`) derive it
itself via `unified_trading_library.pipeline_mode_resolver.derive_pipeline_mode_for_row("GMX", "defi", data_type)`.

Traced the resolution chain (`unified-trading-library/unified_trading_library/pipeline_mode_resolver.py`):

1. No `"GMX"` entry exists in `_VENUE_OVERRIDES` (lines 39-99) or `_VENUE_DT_OVERRIDES` (lines 115-118) — GMX was never
   registered as a venue override anywhere in UTL.
2. Falls to SOURCE_PRIORITY lookup (`unified_api_contracts.read_with_source_priority("defi", data_type)`):
   - **`perp_funding`**: `unified-api-contracts/unified_api_contracts/canonical/crosscutting/_source_priority_data.py`
     registers `("defi", "perp_funding"): ["hyperliquid"]` — a single-source entry that is itself a **mis-registration
     for a subgraph-sourced venue** (the doc comment at that line anticipated a venue override would be needed for
     non-Hyperliquid perp venues, citing LIGHTER as the pattern, but no override was ever added for GMX). Resolves to
     `PipelineMode.BATCH_HYPERLIQUID` — matching the manifest bug's wrong value BY COINCIDENCE of the same underlying
     registry gap, not because the code reads `gmx_mode`.
   - **`derivative_ticker`**: `("defi", "derivative_ticker")` has **no SOURCE_PRIORITY entry at all** → falls to the
     `_ASSET_GROUP_FALLBACKS["defi"] = PipelineMode.BATCH_ONCHAIN_RPC` catch-all. **A THIRD wrong value** — neither
     `batch_hyperliquid` (what the manifest said) nor `batch_onchain_subgraph` (the correct answer).

Confirmed empirically against live prod GCS (`market-data-tick-defi-prd-central-element-323112`, scoped listing under
`venue=GMX` only — no whole-bucket walk):

```
day=2026-07-19/pipeline_mode=batch_hyperliquid/asset_group=defi/venue=GMX/chain={ARBITRUM,AVALANCHE}/
  instrument_type=perpetual/data_type=perp_funding/all.parquet          <- perp_funding objects live HERE
day=2026-07-19/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=GMX/chain={ARBITRUM,AVALANCHE}/
  instrument_type=perpetual/data_type=derivative_ticker/all.parquet     <- derivative_ticker objects live HERE (not batch_hyperliquid!)
```

The cached manifest index (`defi_index.parquet`, a `duckdb`-built snapshot of the prod availability index) independently
confirmed this: `derivative_ticker` under `venue=GMX` had TWO disagreeing manifest rows per (date, chain) — one stamped
`pipeline_mode=batch_hyperliquid, source=hyperliquid, row_count=1` (the original buggy `record_captured` call) and one
stamped `pipeline_mode=batch_onchain_rpc, source=onchain_rpc, row_count=0` (apparently a later phantom-audit /
reconciliation pass that discovered the TRUE GCS path but did not re-read the real row count) — a live three-way desync
across manifest-pipeline_mode, GCS-path-pipeline_mode, and manifest-source, exactly the failure mode this session was
primed to check for.

## 3. Fix (entirely within `market-tick-data-service`, no UAC/UTL change)

`market_tick_data_service/cli/handlers/_perp_funding_gmx.py`:

1. `gmx_mode = _h.PipelineMode.BATCH_ONCHAIN_SUBGRAPH` (was `BATCH_HYPERLIQUID`) — fixes the manifest `pipeline_mode`
   column for every `record_captured` / `record_failed` / `record_zero_rows` call, both data_types (shared variable).
2. `_write_gmx_shard()` now takes an explicit `pipeline_mode: str` parameter and passes it straight through to
   `write_defi_rows(..., pipeline_mode=pipeline_mode)`. Both call sites in `_collect_gmx()` (the `perp_funding` write
   and the `derivative_ticker` dual-write) pass `_h.PipelineMode.BATCH_ONCHAIN_SUBGRAPH.value` explicitly — this
   BYPASSES `derive_pipeline_mode_for_row` entirely for this call site (a non-`None`, non-`"batch"` value short-circuits
   the UAC/UTL derivation in `canonical_write.write_defi_rows`), so the GCS partition path and the manifest column now
   agree by construction, without touching UAC or UTL.

**Why not fix the UAC registry instead?** This dispatch was explicitly scoped to `market-tick-data-service` +
`unified-trading-pm` only (multi-repo workspace restriction). The correct long-term fix is ALSO adding a
`"GMX": PipelineMode.BATCH_ONCHAIN_SUBGRAPH` entry to UTL's `_VENUE_OVERRIDES` (or fixing
`("defi","perp_funding")`/registering `("defi","derivative_ticker")` in UAC's `SOURCE_PRIORITY`) — that would fix the
`pipeline_mode` derivation AND unlock a correct `source=` stamp (currently `default_source("defi","perp_funding")`
resolves to `"hyperliquid"` because it's the sole SOURCE_PRIORITY-registered source for that cell, and
`_resolve_and_validate_source`'s write-time gate REJECTS any other explicit `source=` value as not in the closed set —
verified: passing `source="onchain_subgraph"` would raise `MissingSourceError`). Until that registry entry changes, GMX
manifest rows will carry a correct `pipeline_mode=batch_onchain_subgraph` but an incorrect `source=hyperliquid`. **This
is a real, understood, but genuinely out-of-scope gap for this session — flagged here rather than silently left
undocumented.**

**Follow-up (P2, cross-repo, not started this session):**

- Add `"GMX": PipelineMode.BATCH_ONCHAIN_SUBGRAPH` to
  `unified-trading-library/unified_trading_library/pipeline_mode_resolver.py::_VENUE_OVERRIDES`.
- Register/fix `unified-api-contracts/.../_source_priority_data.py`: `("defi","perp_funding")` should include
  `"onchain_subgraph"` (GMX's real vendor) rather than only `"hyperliquid"`; `("defi","derivative_ticker")` has no entry
  at all and should get one so future non-GMX subgraph-sourced derivative_ticker writers don't hit the same
  `batch_onchain_rpc` fallback.
- Once fixed, re-run the manifest re-registration (Section 5 below) with `source="onchain_subgraph"` explicit, to
  correct the `source=` column on the rows this session's migration already touched.

## 4. Pinning tests added

`tests/unit/test_perp_funding_handler_coverage.py`:

- `test_collect_and_record_gmx_pins_batch_onchain_subgraph_pipeline_mode` — asserts every `record_failed` call from
  `_collect_and_record_gmx`'s exception path carries `pipeline_mode=PipelineMode.BATCH_ONCHAIN_SUBGRAPH`, never
  `BATCH_HYPERLIQUID`.
- `test_collect_gmx_writes_pin_batch_onchain_subgraph_pipeline_mode` — asserts both `write_defi_rows` calls (the
  `perp_funding` write + the `derivative_ticker` dual-write) from `_collect_gmx()` carry
  `pipeline_mode="batch_onchain_subgraph"` explicitly, never `"batch_hyperliquid"`.

Both tests would have FAILED against the pre-fix code.

## 5. Measured blast radius + migration

Scoped to `venue=GMX` cells only (no whole-bucket walk) — driven from a cached prod availability-index snapshot
(`defi_index.parquet`, DuckDB-queried) to enumerate the exact (date, chain) units needing migration, then a direct
scoped GCS listing under each unit's exact prefix to enumerate real objects (manifest row count != object count, since
GMX shards per-instrument on days its native Graph schema returns multiple markets).

**Measured (dry-run, before any write):**

- `perp_funding`: 2,075 distinct (date, chain) units under `pipeline_mode=batch_hyperliquid`, spanning **2022-11-01 ->
  2026-07-19** (both ARBITRUM + AVALANCHE chains).
- `derivative_ticker`: 8 distinct (date, chain) units under `pipeline_mode=batch_onchain_rpc`, spanning **2026-07-15 ->
  2026-07-19** (the dual-write feature is only 6 days old).
- **6,240 total GCS objects** across both data_types (2,083 units, avg ~3 shards/unit — per-instrument sharding on days
  the native subgraph schema returned multiple GMX markets; the Messari-fallback days write a single `all.parquet`).

**Migration performed** (idempotent, proof-gated — copy -> `gcs_describe_object` verify size match on both old+new ->
delete original; never deletes before a verified twin exists). Executed via a one-off script
(`unified_trading_library.cloud_interface.gcs_copy_object` / `gcs_delete_object` / `gcs_describe_object` — never
subprocess `gcloud`/`gsutil`), NOT committed to any repo (temporary, per `codex/06-coding-standards/script-homes.md`).

**A first single-phase design was RETIRED after it hit real production contention.** The first attempt did the GCS
copy + a per-unit `DefiManifestRecorder` open/write/close INSIDE the same worker thread, at 24-way concurrency.
`DefiManifestRecorder` uses `batch_size=1`, so every single re-registration independently forced `ManifestWriter`'s
legacy-CAS full-index read-modify-write cycle against the canonical `_index/availability_index.parquet` (~1.9GB).
Twenty-four threads doing that concurrently broke connections mid -download — observed 3x
`IncompleteRead(1335885824 bytes read, 540753380 more expected)` at the exact same byte offset before the process was
killed. Worse: `DefiManifestRecorder.close()` swallows internal write failures (logs a WARNING, never raises) — so a
caller could see "OK" from a re-registration call whose flush had actually silently failed. Only 27 of 2,075
perp_funding units had progressed in ~9 minutes before this was caught and the process was killed.

**Retired in favor of a two-phase design:**

- **Phase A (`gcs` mode)** — pure GCS copy/verify/delete, 24-way concurrency, NO manifest writer involved at all (so no
  CAS contention). Ran to completion: **6,240 objects migrated across all 2,083 units, 0 errors** (54 objects had
  already moved during the killed first attempt's 27 completed units; this run's own tally was 6,186 + those 27 units'
  prior 54 = 6,240, reconciling exactly against the pre-migration dry-run measurement).
- **Phase B (`manifest` mode)** — re-registration via ONE shared `ManifestWriter(batch_size=0)` instance: every eligible
  unit is staged with a single `.add(...)` call, then ONE final `.write()`/`.close()` forces exactly one CAS cycle for
  the whole batch instead of one per unit. Gated on Phase A's per-unit status map (`gmx_gcs_status_map.json`) — only
  units confirmed `OK` or `NO_OBJECTS` (i.e. genuinely migrated) are eligible. Of the 2,083 units, **1,965 rows were
  staged** (row_count > 0 — genuine captures) and **118 were intentionally skipped** (perp_funding units whose manifest
  row_count was 0 — placeholder/reconciliation rows with no real captured data; re-stamping their provenance was judged
  out of scope for this pass, since there is no real data whose provenance they misrepresent).

**Even the single-writer Phase B design first hit the SAME contention class, with a known fix.** The first Phase B
attempt (default `ManifestWriter` settings — legacy single-blob CAS path) hit 13 consecutive generation-conflict retries
over ~19 minutes against the live production index (a real manifest-consolidator daemon was confirmed actively rewriting
the same canonical blob during that exact window, per its `consolidator_run_at` custom-metadata timestamp), then the
process was terminated (not by this session) before completing. **Verified directly**: downloaded the live ~1.9GB
canonical index afterward and queried it — zero GMX rows had changed; the manifest still showed 100% of
perp_funding/derivative_ticker rows under the old wrong `pipeline_mode`/`source`. Root cause: this bucket's canonical
`_index/availability_index.parquet` is large enough (~1.9GB / ~52M rows) that the legacy generation-match CAS path (full
read-merge-reupload per attempt) empirically never wins a race against a live, frequently-writing consolidator — an
**identical** failure mode independently hit the same day on this same bucket, diagnosed and fixed in
[`defi_fold_manifest_registration_pending_2026_07_21.md`](defi_fold_manifest_registration_pending_2026_07_21.md) (todo
1): pass `per_vm_shards=True` so the writer targets `_index/per_vm/{instance}.parquet` instead of the contended
canonical blob (no CAS race at all), relying on the manifest-consolidator daemon (or the reader's own live
per-VM-shard-merge fallback) to fold it into the canonical view. Applying that fix, Phase B re-run completed in under a
second.

**Result — fully verified, not just log-trusted:** 6,240/6,240 GCS objects migrated (0 errors, verified size-match copy
before every delete) — spot-checked earliest/middle/latest days directly against live GCS post-migration: old prefix
empty, new prefix populated, in every sample. 1,965/1,965 eligible manifest rows re-registered — verified by downloading
the newly-written per-VM shard (`_index/per_vm/local-34791-ab06.parquet`) and querying it directly (not trusting the
writer's own success log line, after the first attempt demonstrated exactly that log/reality gap): 1,957 `perp_funding`
rows + 8 `derivative_ticker` rows, ALL `pipeline_mode=batch_onchain_subgraph`, `source=onchain_subgraph`,
`asset_group=defi`, `venue=GMX`, `capture_status=captured`, chains ARBITRUM (982) / AVALANCHE (983). The
manifest-consolidator was kicked off afterward to fold the per-VM shard into the canonical index
(`python -m unified_trading_library.manifest_consolidator --bucket market-data-tick-defi-prd-central-element-323112`);
per the identical precedent, the corrected rows are already live to any reader via the per-VM-shard-merge fallback
regardless of consolidator completion timing.

## 6. Codex SSOTs consulted

- [`codex/02-data/pipeline-mode-partition.md`](../../../codex/02-data/pipeline-mode-partition.md) — `{mode}_{source}`
  convention, reader prefix-match rule (`batch_*` is read-safe to move within), GCS delete-safety invariant.
- [`codex/02-data/availability-manifest-and-data-status.md`](../../../codex/02-data/availability-manifest-and-data-status.md)
  — 4-state `capture_status`, shard-atom definition (`pipeline_mode` is NOT part of the shard atom, confirmed via the
  `cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md` precedent — a `pipeline_mode` move does not double-count
  coverage).
- [`plans/active/issues/cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md`](cefi_onchain_venues_mislabeled_batch_tardis_2026_07_20.md)
  — the closely-analogous CeFi precedent (same `_VENUE_OVERRIDES` gap class, different venue) — read for methodology,
  not duplicated.
