---
doc_type: issue
title: DERIBIT combo instruments mispartitioned as perpetual/future — scope, root cause, and MOVE design
summary: >
  Design (no code, no data changes) for the plan's "COMBO instruments stored in a `perpetual` partition" finding. Widens
  the measured scope from the plan's original 23/787 sample to an exhaustive manifest census (15,119 rows across TWO
  partitions — perpetual AND future, not just perpetual), traces the exact root-cause code path (a Deribit combo-shape
  guard scoped to one venue label and one of two ingestion paths), concludes this is a SIBLING but DISTINCT mechanism
  from the fail-hard design doc's §5.1 chain-bundle finding, and proposes a partition-MOVE mechanic mirroring this
  migration's proven merge-preservation pattern.
status: open
nature: design
asset_group: cefi
stage: data
repos: [market-tick-data-service, unified-api-contracts]
scope: engineer
tags: [canonical, deribit, combo-instrument, partition-move, quarantine, data-safety, chain-bundle]
related:
  - plans/active/cefi_consolidated_closeout_2026_07_18.md
  - plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md
  - plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md
created: 2026-07-21
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
assigned_role: data-pipeline
drift_direction: none
source:
  investigation (read-only GCS + manifest sampling, 2026-07-21; grep + code read of market-tick-data-service adapters)
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# DERIBIT combo instruments mispartitioned as perpetual/future — design of record

> Investigation + design only. No code was changed, no GCS object was written/moved/deleted, no manifest row was
> written, and no `--apply` flag was run on any existing script. All GCS/manifest access below was read-only.

## OPERATOR RULING — 2026-07-23 ~08:15Z

**Ruled: proceed with §9's P1 prep work now — the actual data move stays gated.** Operator decision: "Proceed with P1
prep now" in response to an explicit split between (a) the two `[P1]` code-only todos in §9 — cross-check against the
concurrent DERIBIT-COMBO venue-deregistration effort, and widen/port the combo-shape guard into `tardis_cefi_shards.py`
— versus (b) the actual `[DATA] P2.` partition-MOVE `--apply` on the 15,119 live production rows, which §7 already
recommends stays operator-gated and this ruling does NOT touch. **No production data is moved by this ruling** — code
fix + cross-check only. The `--apply` step (§9's second `[DATA] P2.` todo) still requires a SEPARATE, later operator
review of this full doc before it is scheduled — do not infer blanket approval for the move from this ruling.

## 1. What the plan originally found

`plans/active/cefi_consolidated_closeout_2026_07_18.md` (closure-plan table, line ~1098/1118):

> "COMBO instruments stored in a `perpetual` partition (`BTC-FS-29SEP23_PERP`, 23/787 DERIBIT sample). The catalogue HAS
> them under itype `COMBO`; the path says `perpetual`. This needs a partition MOVE, not a rename — renaming alone would
> leave path-itype and id-itype disagreeing."

The plan's closure table listed this at "~2.9% DERIBIT / 🟡 design needed" — this doc is that design, plus a much larger
measured scope (§2) than the original one-off sample.

## 2. Measured scope (read-only, this investigation)

**Two independent measurements were taken.** The provenance script/sample behind the plan's original "23/787" figure is
not reproducible from the current repo state — re-running the shipped
`market-tick-data-service/scripts/audit_cefi_catalogue_coverage_gap_2026_07_20.py --venue DERIBIT` at its default window
(`--start 2025-11-05`, wire-era only) over 10 and 20 evenly-sampled days found only 1/344 and 2/1819 combo-shape
mismatches respectively — because that script's default window is WIRE-ERA ONLY, and (per below) this defect is
concentrated in the PRE-wire-era backfill corpus. The 23/787 number is stated here as inherited context, not reproduced;
the two measurements below are new, explicitly bounded, and their sample composition is stated in full — no silent
extrapolation.

### 2a. GCS object sampling (bounded, single-prefix-per-call — no fresh whole-corpus walk)

Full `instrument_type=perpetual` partition listing for DERIBIT, one full day-prefix per call
(`raw_tick_data/by_date/day=<D>/pipeline_mode=batch_tardis/asset_group=cefi/venue=DERIBIT/instrument_type=perpetual/`),
13 distinct days spanning 2023-06 through 2026-07-18:

| day        | perpetual objects | combo-shaped stems | era               |
| ---------- | ----------------: | -----------------: | ----------------- |
| 2023-06-01 |                60 |                  6 | pre-wire backfill |
| 2023-08-01 |                40 |                  2 | pre-wire backfill |
| 2023-09-15 |                25 |                  2 | pre-wire backfill |
| 2024-01-15 |                25 |                  0 | pre-wire backfill |
| 2024-06-01 |                52 |                  2 | pre-wire backfill |
| 2025-01-15 |                38 |                  2 | pre-wire backfill |
| 2025-11-20 |                 3 |                  0 | wire era          |
| 2025-12-15 |               647 |                  0 | wire era          |
| 2026-02-01 |                23 |                  0 | wire era          |
| 2026-05-01 |                25 |                  0 | wire era          |
| 2026-06-15 |                 0 |                  0 | wire era          |
| 2026-07-15 |                21 |                  0 | wire era          |
| 2026-07-18 |                21 |                  0 | wire era          |
| **TOTAL**  |           **980** |     **14 (1.43%)** |                   |

Every one of the 14 flagged stems (`BTC-FS-*`, `BTC-CS-*`, `BTC-PS-*` shapes) was cross-checked against the real cefi
catalogue by exact `raw_symbol` match: **100% confirmed catalogue `instrument_type=COMBO`.** The defect is concentrated
in the 2023-2025 backfill-era days (6/60 to 2/52 per day, i.e. up to ~10% of that day's perpetual partition) and was
**not observed in any of the 7 wire-era days sampled** — this is a pre-existing backfill-corpus defect, not (primarily)
a current wire-write regression. This 13-day sample is illustrative of density/distribution, not the authoritative count
— §2b below is the authoritative, exhaustive count.

### 2b. Manifest census — exhaustive for DERIBIT, NOT a GCS walk (one bounded read of the availability index)

The availability manifest (`_index/availability_index.parquet`) was read ONCE (one GET, ~188MB) and filtered in Arrow to
`asset_group=cefi, venue=DERIBIT` — this is a single bounded object read, not a GCS prefix walk, and respects
single-walk discipline.

**DERIBIT manifest rows total: 680,380** (itype breakdown: perpetual=52,012, future=181,525, option=435,591,
spot_pair=3,006, options_chain=4,020, futures_chain=3,564, combo=662).

**Combo-shaped `instrument_id` rows sitting under the WRONG `instrument_type` partition key:**

| itype (wrong) | combo-shaped rows | already canonical `DERIBIT:COMBO:` id | still raw wire id |
| ------------- | ----------------: | ------------------------------------: | ----------------: |
| `perpetual`   |         **8,849** |                                 4,965 |             3,884 |
| `future`      |         **6,270** |                                     0 |             6,270 |
| **TOTAL**     |        **15,119** |                                 4,965 |            10,154 |

Every one of the 6,270 `future`-itype rows and a representative sample of the `perpetual`-itype rows were cross-checked
against the catalogue by exact `raw_symbol`/id-stem match: **100% confirmed catalogue `instrument_type=COMBO`** (zero
false positives from the shape regex `-(FS|CS|PS|STRD|STD|IRON|BOX)-`).

This is **an order of magnitude larger than the plan's original 23/787 (~2.9%) estimate**, and it spans a **second
partition** (`future`, not just `perpetual`) the original finding did not name. `itype=perpetual` alone: 8,849/52,012 =
17.0% of ALL DERIBIT perpetual-partition rows are actually mispartitioned combo instruments.

**Not double-counted with the separate DERIBIT-COMBO venue purge.** The manifest cleanly separates `venue=DERIBIT`
(680,380 rows, this doc's entire scope) from `venue=DERIBIT-COMBO` (196 rows — a different, much smaller population than
the "0 captured rows" purge premise states; that discrepancy belongs to the concurrent purge work, not this doc, and is
called out only so the two efforts don't talk past each other). Every row measured in §2a/§2b was confirmed
`venue=DERIBIT`.

**Confirmed real, non-placeholder captured data** (two objects read directly, full parquet metadata plus row-group-0
content):

- `raw_tick_data/by_date/day=2025-01-15/.../venue=DERIBIT/instrument_type=perpetual/data_type=book_snapshot_5/BTC-FS-26DEC25_PERP.parquet`
  — 630,882 bytes, **37,258 rows**, `instrument_id` column reads `DERIBIT:PERPETUAL:BTC-FS-26DEC25_PERP` for all sampled
  rows (the CONTENT column is also wrong, not just the path/manifest — see §3).
- `raw_tick_data/by_date/day=2023-06-01/.../venue=DERIBIT/instrument_type=perpetual/data_type=book_snapshot_5/BTC-FS-29SEP23_PERP.parquet`
  — 88,425 bytes, **6,318 rows**, same pattern.

Both are genuine 5-level order-book captures with real timestamps — not empty or placeholder objects. `data_type`
breakdown for the 8,849 `perpetual`-itype combo rows: book_snapshot_5=4,580, trades=2,614, derivative_ticker=1,655 — all
three real market-data types are affected.

## 3. Root cause (traced through the actual write path — not guessed)

**Origin — the upstream itype classifier, `TardisAdapter._classify_row_instrument_type`**
(`market_tick_data_service/market_interface/adapters/tradfi/tardis_adapter.py:354-402`). This function already has an
explicit combo-aware branch:

```python
if venue_u == "DERIBIT-COMBO":
    return InstrumentType.OPTION
```

Its own comment (lines 362-371) documents WHY: Deribit combo/multi-leg symbols (`BTC-CS-28AUG26-72000_76000`,
`BTC-FS-11JUL26_PERP`) "don't match the OPTION/dated-FUTURE regexes below" and would otherwise "fall through to the
PERPETUAL default below." **But this guard fires only for the separate venue label `"DERIBIT-COMBO"`** — it does nothing
for the identical combo symbol shape arriving tagged under the bare venue `"DERIBIT"`, which is exactly what §2
measured. For a bare-DERIBIT combo symbol: `_OPTION_SYMBOL_RE` doesn't match (multi-leg underscore-separated tail, not a
trailing `-C`/`-P`); `_DATED_FUTURE_SYMBOL_RE` sometimes partially matches a trailing date-like token inside a
calendar-spread id (e.g. the `25SEP26` in `BTC-FS-25SEP26_27FEB26`) → classified `FUTURE`; otherwise the function falls
all the way to its final unconditional line 402, `return InstrumentType.PERPETUAL`.

**The one place this IS already fixed:** `_filter_bulk_rows_for_deribit_split`
(`market_tick_data_service/market_interface/adapters/tradfi/tardis_bulk_download.py:283-306`), scoped to the Tardis
grouped-`OPTIONS.csv.gz` BULK-download path (`_stream_finalise_chain_bulk`, same file). Its docstring (dated 2026-07-12,
citing `cefi_deribit_combo_and_okx_bare_venue_gaps_2026_07_12.md`) explains Tardis mixes bare options and combo symbols
in ONE options-only file; this filter isolates bare-DERIBIT rows down to option-shaped symbols only (`is_bare_option`)
BEFORE `_classify_row_instrument_type` ever runs, routing combo-shaped rows to the separate `DERIBIT-COMBO` venue's own
fetch instead.

**The leak is NOT closed in the other, primary ingestion path.**
`market_tick_data_service/market_interface/adapters/tradfi/tardis_cefi_shards.py` calls
`self._classify_row_instrument_type(s, venue)` DIRECTLY at lines 151 and 538, with **no equivalent pre-filter**. This is
a live, actively-used per-shard ingestion path (the same file the fail-hard design doc's §4 A-iso finding covers) — very
likely the path that wrote most of the 2023-2025 historical corpus §2 measured, and (unlike the bulk path) **it has
never received the `DERIBIT-COMBO` split fix.** This means the defect is not purely historical: any new bare-DERIBIT
combo row captured via this path today would still land mispartitioned.

**A second, independent, compounding gap** inside `derive_row_instrument_id`
(`market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py:439-595`), which runs downstream of whichever
path assigned the (already wrong) `instrument_type`. The catalogue-first lookup at line 472 —
`resolve_cefi_instrument_id(venue, instrument_type.value, symbol)` — is a **3-tuple key** `(venue, itype, symbol)`. The
catalogue's real row for a combo symbol is keyed `(DERIBIT, COMBO, symbol)`; a lookup keyed on the wrong
`(DERIBIT, PERPETUAL, symbol)` or `(DERIBIT, FUTURE, symbol)` misses even though the catalogue holds the correct answer
under a different key. The function's own combo-shape safety net (`is_deribit_combo_symbol_shape`, lines 295-314, called
at line 483) is gated to **both** `instrument_type is InstrumentType.OPTION` **and** `venue.upper() == "DERIBIT-COMBO"`
— neither condition holds here, so it never fires. Traced exactly for the PERPETUAL lane:
`_derive_perpetual_margin_symbol(venue, symbol)` (line 588) raises `ValueError` on the combo shape (it doesn't decompose
into a clean BASE-QUOTE), and the except-clause (lines 591-592) falls back to a blind passthrough —
`build_instrument_id(venue, instrument_type, symbol)` → `"DERIBIT:PERPETUAL:BTC-FS-26DEC25_PERP"` — reproducing exactly
the content-column value measured in §2b. (The FUTURE lane's precise final fallback line was not traced with the same
certainty — several expiry-parsing helpers are candidates — but the structural gap is identical: no combo-shape check
anywhere in that branch either.)

`finalise_rows_and_path` (same file, lines 761-889) then trusts this already-wrong `instrument_type` unquestioned: it
picks `shard_it` (`"perpetual"`/`"future"`, lines 819-832) and builds BOTH the GCS partition path and the file stem from
it. **The defect therefore hits all three of path, content column, and manifest key identically** — there is no surface
where this data reads correctly.

## 4. Is this the same mechanism as the fail-hard doc's §5.1 chain-bundle finding?

**No — a sibling defect, not the same mechanism.** `fail_hard_canonical_enforcement_design_2026_07_20.md` §5.1
("Derivative / chain-bundle lane defeats all three write gates") is about the **options_chain/futures_chain whole-BUNDLE
lane**: many instruments packed into ONE object keyed by `underlying=`, where a per-strike non-canonical id leaks ONLY
into the parquet CONTENT column while the manifest key/path stay bundle-shaped (`instrument_id=""` at the manifest/path
level) — quarantine and id-level gates are blind to it because a bundle object never carries a per-instrument stem/key
at all.

This doc's defect is the **per-symbol, single-instrument shard lane** (`perpetual`/`future` — one object = one
instrument, never a bundle). Here the id/itype is wrong on **all four surfaces at once** (path partition segment,
content column, file stem, manifest key) — the object IS fully addressable by instrument, it is simply addressed under
the wrong `instrument_type`. There is no bundle-shaped blind spot in this defect; a plain per-instrument id/path-form
check would have caught it.

Both defects trace back to the same underlying gap-CLASS — Deribit combo-shape recognition
(`is_deribit_combo_symbol_shape`, and the `DERIBIT-COMBO`-only special case in `_classify_row_instrument_type`) is
scoped far too narrowly: one venue label, one itype branch (`OPTION` only), and one of two ingestion paths
(`tardis_bulk_download.py`, not `tardis_cefi_shards.py`). But they require **two separate code fixes** — a
bundle-content-column gate for §5.1; a pre-classification, catalogue-driven itype correction (hoisting the combo-shape
check above every itype branch, covering both ingestion paths, for this doc — see §6) — not one shared fix. Whoever
implements either should read the other first; the fixes are adjacent, not identical.

## 5. Proposed partition-MOVE mechanic (mirrors this migration's proven merge-preservation pattern)

The plan's already-executed "COLLISION SET FULLY RESOLVED" work (same plan file, PRE-COMPACT checkpoint section) proved
the pattern this move should reuse: **prove the row-count BEFORE, back up the pre-state, write the new correct form,
RE-PROVE the count, delete the OLD form only LAST** (there: `C_now == PRE_C + W_unique`, verified per-object EXACT, zero
rows lost). Concretely, for this move:

1. **PRE-STATE PROOF.** For every one of the ~15,119 flagged manifest rows, record: GCS object path, size, generation
   (`get_blob_metadata(...).generation` — the same mid-flight-rewrite guard the verify script's
   `GcsRangeFile.generation_changed()` already uses), row count (parquet metadata `num_rows`, no full read needed), and
   the exact manifest key tuple + `capture_status`.
2. **BACKUP.** Copy (never move) every flagged object to a new
   `_migration_backups/deribit_combo_perpetual_partition_move_2026_07_21/` prefix, mirroring the naming convention
   already used elsewhere in this same migration (`_migration_backups/cefi_wire_collision_drop_2026_07_19/`).
3. **REWRITE.** For each flagged object: (a) rewrite the parquet `instrument_id` COLUMN to the canonical
   `DERIBIT:COMBO:<raw_symbol>` form — including the 4,965 rows whose id is already correct-looking but whose itype/path
   is not, to force a single consistent pass rather than two different code paths; (b) write the corrected parquet to
   the NEW path `instrument_type=combo/data_type=<dt>/DERIBIT:COMBO:<raw_symbol>.parquet` (a copy-to-new-path, never an
   in-place rename — this is the plan's own stated reason a rename alone is insufficient); (c) every other partition
   segment (`day=`, `data_type=`) is unchanged.
4. **RE-PROOF.** Re-read the new object's row count and a content sample; assert exact equality with the step-1 proof
   (`rows_new == rows_old`, and the `instrument_id` column now reads the canonical form uniformly). Any mismatch aborts
   before the old object is touched.
5. **MANIFEST UPDATE (additive).** Write the NEW manifest row (`instrument_type=combo`, canonical `instrument_id`) as a
   new key — never mutate the old key in place.
6. **DELETE OLD — LAST, per-object, only after independent re-proof.** Delete the old `instrument_type=perpetual|future`
   object and its old manifest row only once steps 4-5 are verified for that EXACT object. Never batch-delete ahead of
   per-object verification.
7. **FINAL CORPUS RE-VERIFICATION.** Re-run the manifest census from §2b post-migration; assert combo-shaped rows under
   `itype ∈ {perpetual, future}` == 0, and `itype=combo` total rows equals the pre-migration combo count plus 15,119
   (adjusted for the 4,965 rows that only change itype label, not id).

## 6. Data-safety proof plan (must pass before any `--apply`)

- Every flagged manifest row's source GCS object exists, is non-empty, and has its row count captured BEFORE any write
  (§5 step 1).
- Generation recorded before backup; re-checked before rewrite (catches a concurrent rewrite — this same manifest object
  and these same GCS prefixes are ALSO being touched right now by the plan's own live "would_patch fleet" and
  "manifest-v2 agent" background operations; this move must NOT run concurrently with those without explicit
  coordination).
- Backup copy verified present (size + generation match) before rewrite is allowed to proceed.
- Row-for-row content-equality proof after rewrite, BEFORE delete (§5 step 4).
- A DRY-RUN mode (no writes) that prints the full per-object plan (source, dest, expected row count, backup path) for
  operator review before the first real `--apply`.
- A small-batch canary first: the two objects already read directly in this doc (`BTC-FS-29SEP23_PERP` / 2023-06-01,
  `BTC-FS-26DEC25_PERP` / 2025-01-15) — independently re-verified via
  `CanonicalParquetReader.read_shard(instrument_type="combo", ...)` (Surface D) — before scaling to the full 15,119.

## 7. Automation vs operator sign-off

**Recommendation: operator sign-off required before any `--apply`.** Reasoning:

1. This is a genuine MOVE of live, currently-served production data, not an additive or reversible write — the
   workspace's own precedent for this class of operation (the plan's "COLLISION SET" merge/drop, same file) was treated
   as a major, closely-tracked operation with per-object EXACT proof gates, not a routine background task.
2. Scope is **15,119 rows across TWO partitions**, an order of magnitude beyond the plan's original 23-row estimate, and
   includes a partition (`future`) the original finding never named — the operator has not yet seen or ruled on this
   widened scope.
3. The defect is **not fully historical** — one of two ingestion paths (`tardis_cefi_shards.py`) still lacks the
   combo-split fix that the other path (`tardis_bulk_download.py`) already received on 2026-07-12. Moving the historical
   corpus before the write-path is fixed would let the same defect re-accumulate immediately behind the migration.
4. A live background fleet is operating on the SAME manifest object and the SAME DERIBIT GCS prefixes right now (per the
   plan's own live-operations section) — sequencing against it is an operator-level scheduling decision.

Once the operator approves (a) the widened scope, (b) sequencing against the live fleet, and (c) landing the code fix
(widening the combo-shape guard to cover bare `DERIBIT`, the `PERPETUAL`/ `FUTURE` branches, and the
`tardis_cefi_shards.py` ingestion path) BEFORE any backfill move — the mechanical MOVE steps themselves, given the
proven merge-preservation pattern already in repeated use in this same plan, are well suited to a supervised
background-agent task with the per-object proof gates in §5-6. Sign-off should gate the START of the backfill, not
necessarily every individual step of its execution once approved.

## 8. Companion note — cross-reference only, not implemented here

The concurrent DERIBIT-COMBO venue-label purge (0-captured-rows ruling, being handled elsewhere in this session;
referenced in this plan's PRE-COMPACT checkpoint section as the "DERIBIT-COMBO GCS sweep") removes the `DERIBIT-COMBO`
venue label entirely. If instruments-service's adapter registration and any UAC capability declarations for
`DERIBIT-COMBO` are deregistered as part of that purge, the ONE place in this codebase that already correctly isolates
combo-vs-bare-option rows (`_filter_bulk_rows_for_deribit_split`, §3) loses its routing target — its `~is_bare_option` /
combo-routing half becomes dead code for a now-deregistered venue. Any future bulk-path combo fetch would then need a
NEW mechanism (e.g. routing combo-shaped symbols straight to `instrument_type=combo` under the bare `DERIBIT` venue,
rather than via a second venue label) — which would need to land together with (or before) this doc's root-cause fix,
not after. Flagging for whoever picks up either piece of work to cross-check with the other before landing; not decided
or implemented here.

## 9. Todos

- [ ] [DESIGN] P1. Cross-check this doc's root-cause fix (§3, §6) against the concurrent DERIBIT-COMBO venue-registry
      purge (§8) before either lands.
- [ ] [WRITER] P1. Widen the combo-shape guard: hoist an `is_deribit_combo_symbol_shape`-style check above
      `_classify_row_instrument_type`'s venue-label branch (bare `DERIBIT`, not just `DERIBIT-COMBO`) AND port the
      existing `_filter_bulk_rows_for_deribit_split` fix (or an equivalent) into `tardis_cefi_shards.py`, which
      currently has none.
- [ ] [DATA] P2. Implement + dry-run the partition-move script per §5-6 against the 15,119-row scope measured in §2b;
      canary on the two objects named in §6 before any full `--apply`.
- [ ] [DATA] P2. Operator review of §7 (widened scope, live-fleet sequencing, code-fix-first ordering) before any
      `--apply` is scheduled.
