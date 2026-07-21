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
execution_scope: local-only
drift_direction: advance-docs
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
---

# Batch=live filename divergence + the verbatim-write / no-guard family

> **🔴 OPERATOR-NOTIFY — batch=live determinism.** The workspace holds `paper(W) == batch-rerun(W)` trade-for-trade at
> ε=0 (`codex/09-strategy/operational/paper-batch-live-reconciliation.md`). A live run and a batch rerun of the same
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

- [ ] [SERVICE] P1. Add a write-time canonical-path guard to the Tardis cefi lane (the lane currently has none). It must
      use the DEFAULT all-class `canonical_path_violations` so both STRUCTURAL and ID_FORM are enforced — but only after
      the writer emits canonical stems (as the live lane now does), or it fails hard on every write.
- [ ] [SERVICE] P1. Fix `tardis_shared.py:671` to escape `/` in the stem (use `sanitize_file_stem`) so a slash-bearing
      id cannot forge a hive segment; migrate the 48+ KRAKEN-SPOT `ADA/USD.parquet`-style corrupt objects.
- [ ] [SERVICE] P1. Turn `validate=True` on the two `tardis_cefi_shards.py` write sites and make
      `finalise_rows_and_path` violations FATAL, not advisory (fail hard, per the operator's write-path directive).
- [ ] [SERVICE] P0. Remove the silent `build_instrument_id(venue, itype, symbol)` catalogue-miss fallback that mints
      double-wrapped `VENUE:ITYPE:<raw wire>` ids (shared with the oracle issue doc).
- [ ] [DATA] P1. Migrate/restate the historical non-canonical live objects (1,697 colon_wire cefi) as part of the
      surface-A re-run with the fixed oracle.

## 6. Codex SSOTs

- `codex/09-strategy/operational/paper-batch-live-reconciliation.md` — the ε=0 batch=live determinism requirement this
  divergence violated.
- `codex/02-data/four-surface-reconciliation-procedure.md` § 4.3 — the path-structure vs id-form orthogonality (updated
  2026-07-20 by the sibling oracle issue).
