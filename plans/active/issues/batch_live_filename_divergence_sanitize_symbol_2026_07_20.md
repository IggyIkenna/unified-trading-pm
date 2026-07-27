---
doc_type: issue
title:
  "Batch=live determinism: live/microstructure writers named objects with _sanitize_symbol (colons stripped) while batch
  wrote the id verbatim — one instrument, two object names; part of a verbatim-write / no-guard silent-tolerance family"
summary: >-
  The MTDS batch writer names per-instrument objects for the FULL canonical instrument_id VERBATIM (literal colons), but
  the LIVE lane (live_tick_blob_path) and the microstructure handler named them via _sanitize_symbol, which rewrites ':'
  to '_'. So the same instrument landed at TWO different GCS object names depending on the lane — a batch=live
  determinism divergence and a canonicality defect (the sanitized name can never satisfy the id-form half of path
  canonicality). FIXED forward 2026-07-20 (sanitize_file_stem preserves ':', still escapes '/'; mtds@953679de). This doc
  records the fix AND the broader family the write-path audit surfaced: filename stems written verbatim with zero form
  validation, no write-time path guard on the Tardis cefi lane, and validate=False on the cefi write sites. Those are
  the mechanisms that let ~811,200 wire-named objects land, and they belong to the same fail-hard-in-writes gap.
status: open
nature: issue
asset_group: [cefi, defi, meta]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags:
  [
    data-correctness,
    batch-live-determinism,
    gcs-path,
    canonical-id,
    sanitize-symbol,
    write-time-guard,
    silent-tolerance,
    operator-notify,
  ]
related:
  [
    canonical_path_oracle_blind_to_filename_stem_2026_07_20,
    tradfi_canonical_path_migration_design_2026_07_19,
    _cefi_canonical_blueprint_2026_07_17,
  ]
created: 2026-07-20
priority: P1
parent_epic: infrastructure_master
source:
  "Surfaced while fixing the canonical-path-oracle blindness (measured the live write path by execution); corroborated
  by an independent write-path audit (KRAKEN-SPOT ADA/USD.parquet structural corruption)."
execution_scope: orchestrator-agent
drift_direction: advance-docs
depends_on: []
locked_by:
locked_since:
assigned_vm: planning
resolved_by:
---

# Batch=live filename divergence + the verbatim-write / no-guard family

> **🔴 OPERATOR-NOTIFY — batch=live determinism.** The workspace holds `paper(W) == batch-rerun(W)` trade-for-trade at
> ε=0 (`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`). A live run and a batch rerun of the same
> instrument were writing to **different GCS object names**, so any consumer keyed on the object path saw two different
> shards for one instrument. The naming divergence is fixed forward; the consequences of the historical split, and the
> sibling verbatim-write defects, are the open work here.

## 1. The divergence (measured by execution)

`PartitionedTickWriter._resolve_writer_file_name`
(`market-tick-data-service/.../engine/orchestrator/partitioned_writer.py:181-205`) names each per-instrument object for
the FULL canonical instrument_id **VERBATIM** — its docstring is explicit: _"written VERBATIM, not `_sanitize_symbol`-d
— real live filenames carry literal `:`"_. GCS object names permit `:`, and the tradfi write-time guard positively
REQUIRES a `:` in the filename.

The LIVE lane and the microstructure handler did the opposite:

- `live/websocket_runner.py::live_tick_blob_path` → `file_name = _sanitize_symbol(instrument_id)`
- `cli/handlers/book_microstructure_handler.py::_microstructure_blob_path` → same

`_sanitize_symbol` (`engine/orchestrator/symbol_rules.py:368-380`) rewrites `[/\\:\s]` → `_`. So one instrument:

| lane  | object stem for `HYPERLIQUID:PERPETUAL:BTC-USD@LIN`     |
| ----- | ------------------------------------------------------- |
| batch | `HYPERLIQUID:PERPETUAL:BTC-USD@LIN.parquet` (verbatim)  |
| live  | `HYPERLIQUID_PERPETUAL_BTC-USD@LIN.parquet` (sanitized) |

Two object names, one instrument. Downstream joins keyed on the path silently diverge, and the sanitized name can never
satisfy the id-form half of path canonicality (see the sibling oracle issue).

## 2. The fix (shipped 2026-07-20 — `market-tick-data-service@953679de`)

`sanitize_file_stem` (new, in `symbol_rules.py`) drops ONLY the `:` rewrite from the escape set, so the canonical id's
colons survive to the object name (matching batch), while `/` `\` and whitespace stay escaped. The `/` escape is
**load-bearing, not cosmetic**: DeFi oracle ids are literally `eth/usd`, and a raw `/` would forge a spurious hive path
segment (`.../data_type=oracle_prices/eth/usd.parquet`). Both builders now call `sanitize_file_stem`. Verified by
calling the real functions: live cefi writes now produce `VENUE:ITYPE:BASE-QUOTE.parquet` and no longer crash the
default all-class canonical-path guard.

`CanonicalParquetReader._cefi_candidate_stems` now appends the legacy sanitized stem LAST (all asset groups), so any
object written under the old name still resolves during the migration window; it also resolves the real DeFi oracle
`eth/usd` → `eth_usd` case. Migration population of the sanitized form measured **0** (bounded GCS listing) — the
`_sanitize_symbol` colon-strip landed 2026-07-09, after live cefi capture had already stopped (last live cefi day =
2026-06-29), so nothing persisted in that form.

## 3. The broader family — verbatim writes with no form validation (write-path audit)

The divergence above is one instance of a class. An independent write-path audit found the structurally worse siblings,
all in the same "stem written verbatim / no write-time guard / validation disabled" family. **These are the mechanisms
that let ~811,200 wire-named objects land** and should be treated together.

- **`tardis_shared.py:671` writes `f"{base}/{file_stem}.parquet"` verbatim** — a slash-bearing stem creates a SPURIOUS
  HIVE SEGMENT. Measured: **48/48 KRAKEN-SPOT objects on day=2026-05-01** sit at
  `.../data_type=book_snapshot_5/ADA/USD.parquet` — `ADA` became a path segment. Today the path oracle would call those
  corrupt paths canonical (it drops the last segment). This is exactly why the id-form check belongs ON BY DEFAULT.
- **No write-time path guard on the Tardis cefi lane at all** — `_assert_canonical_tradfi_path` is
  `if self._asset_group == "tradfi"`-gated (`partitioned_writer.py:258-259`) AND the Tardis lane never enters
  `PartitionedTickWriter`. So the lane that produced the bulk of the wire-named corpus had no canonical-path assertion.
- **`tardis_cefi_shards.py:171` and `:505` pass `validate=False`** on BOTH cefi write call sites, disabling UAC
  SchemaContract validation entirely; and even with `validate=True`, `finalise_rows_and_path`
  (`tardis_shared.py:888-892`) returns violations as an ADVISORY list the caller never inspects.

(Line numbers are from the write-path audit as of 2026-07-20; confirm before acting — the Tardis files are actively
edited.)

## 4. Consequences beyond canonicalisation

- **Batch=live determinism**: a paper(W) run and a batch-rerun(W) of the same instrument wrote different object names,
  so a path-keyed reconciliation could not match them. The reader fallback (§ 2) closes the READ side; the WRITE side is
  fixed forward. Historical live objects (the 1,697 colon_wire cefi objects, not the sanitized form) remain in a
  non-canonical id-form and are part of the surface-A re-run.
- **Manifest vs path atom**: a forged hive segment (`ADA/USD.parquet`) means the object path atom and the manifest shard
  atom disagree — a four-surface reconciliation would flag it, but only once the oracle reads the stem (now it does).

## 5. Open work

- [x] ✅ [SERVICE] P1. Add a write-time canonical-path guard to the Tardis cefi lane (the lane currently has none). It
      must use the DEFAULT all-class `canonical_path_violations` so both STRUCTURAL and ID_FORM are enforced — but only
      after the writer emits canonical stems (as the live lane now does), or it fails hard on every write. — SHIPPED
      market-tick-data-service@ca5ae082. Wired the SAME shared `enforce_structural_and_observe_id_form()` helper already
      used by `partitioned_writer.py`/`book_microstructure_handler.py` into `build_partition_path()` (the single funnel
      both real Tardis cefi write sites — `tardis_cefi_shards.py` + `tardis_bulk_download.py` — call), so every Tardis
      cefi write now gets the same write-time guard as the live/batch lane. **Deviated from this todo's literal "DEFAULT
      all-class" wording** — used `enforce_structural_and_observe_id_form`'s existing Stage-P behavior (STRUCTURAL fails
      hard now, ID_FORM is Stage-0 OBSERVE-only) instead. Per `fail_hard_canonical_enforcement_design_2026_07_20.md`
      §2/§6 (written the same day, adversarially verified, more authoritative): full DEFAULT/both-classes enforcement is
      Stage 3, explicitly gated on Stage 2 (manifest `instrument_id_form` classification) landing first — enforcing
      ID_FORM today would fail-hard on every still-unclassified row, exactly the premature-switch risk that doc warns
      against. Matching the already-shipped Stage-P pattern at the other 2 callsites is both correct-per-the-newer-doc
      and consistent. Caught + fixed along the way: 5 tests across 4 files (`test_tardis_canonical_output.py`,
      `test_cefi_canonical_filename_stem.py`, `test_tardis_finalise_id_vectorization.py`, `test_tardis_shared_v6.py`,
      `test_tardis_bulk_download_shard_vectorized.py`) called chain-bundle write paths WITHOUT the v6 quote/margin dims,
      silently relying on the v5-bare-chain-tail fallback that was RULED v6-only everywhere (operator 2026-07-21) —
      those tests predated that ruling. Updated them to match what the real production callers derive via
      `derive_settlement_dimensions()`; added one new regression test proving the guard fires
      (`test_write_time_canonical_path_guard_rejects_v5_bare_chain_tail`). Verified zero regressions: full-suite
      `quality-gates.sh` run was 7079 passed / 2 failed pre-existing-unrelated (databento/tradfi) both before and after
      my change. File-size ratchet note: `tardis_shared.py` was already at the exact 900-line cap — relocated the guard
      call into `build_partition_path()` (one shared call site instead of duplicating at `finalise_rows_and_path()` too)
      and compacted the new lines to land the file at exactly 900.
- [x] ✅ [SERVICE] P1. Fix `tardis_shared.py:671` to escape `/` in the stem (use `sanitize_file_stem`) so a
      slash-bearing id cannot forge a hive segment; migrate the 48+ KRAKEN-SPOT `ADA/USD.parquet`-style corrupt objects.
      — ALREADY RESOLVED (checkbox was stale). Code fix: market-tick-data-service@fd5cfc35 (2026-07-25) —
      `sanitize_file_stem` already escapes `/` and is already called at `build_partition_path`'s v5-path return.
      Migration: verified 2026-07-27 via live `gcloud storage ls` against
      `gs://market-data-tick-cefi-prd-central-element-323112` — the specific corrupt shape
      (`.../data_type={dt}/ADA/USD.parquet`, a forged `ADA/` hive segment) is ABSENT everywhere checked: every
      KRAKEN-SPOT `spot_pair` object across every `day=` partition, both `book_snapshot_5` and `trades`, is the
      canonical `KRAKEN-SPOT:SPOT_PAIR:{BASE}-USD.parquet` shape. A wildcard probe for any extra path segment under
      `data_type=book_snapshot_5/*/` and `data_type=trades/*/` for this venue/instrument_type matched zero objects
      across all dates. No corrupt objects remain to migrate (targeted, scoped GCS checks — not a new whole-corpus walk,
      per the single-walk-discipline rule).
- [ ] [SERVICE] P1. Turn `validate=True` on the two `tardis_cefi_shards.py` write sites and make
      `finalise_rows_and_path` violations FATAL, not advisory (fail hard, per the operator's write-path directive).
- [x] [SERVICE] P0. Remove the silent `build_instrument_id(venue, itype, symbol)` catalogue-miss fallback that mints
      double-wrapped `VENUE:ITYPE:<raw wire>` ids (shared with the oracle issue doc). **DONE at the shared root
      `unified-api-contracts@502ef57e`**: `build_instrument_id` now raises `ValueError` on any `symbol` carrying an
      embedded `:` for every asset group except sports/prediction — the exact shape a catalogue-miss fallback passing a
      raw wire symbol through produces. The literal MTDS caller
      (`market-tick-data-service/.../adapters/cefi/tardis_shared.py::derive_row_instrument_id`'s bare
      `return build_instrument_id(venue, instrument_type, symbol)` fallback, lines ~592/595) is UNCHANGED code — it is a
      `[SERVICE]`-repo file, out of the UAC-scoped session that shipped this fix — but is now functionally moot: on a
      catalogue miss it will raise instead of silently minting a double-wrapped id, surfacing as a per-shard
      `record_failed` via the existing shard-isolation machinery. Full detail:
      `canonical_path_oracle_blind_to_filename_stem_2026_07_20.md` § 7.
- [ ] [DATA] P1. Migrate/restate the historical non-canonical live objects (1,697 colon_wire cefi) as part of the
      surface-A re-run with the fixed oracle.

## 6. Codex SSOTs

- `/codex/09-strategy/operational/paper-batch-live-reconciliation.md` — the ε=0 batch=live determinism requirement this
  divergence violated.
- `/codex/02-data/four-surface-reconciliation-procedure.md` § 4.3 — the path-structure vs id-form orthogonality (updated
  2026-07-20 by the sibling oracle issue).
