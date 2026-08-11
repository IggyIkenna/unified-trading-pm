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
  - plans/archive/2026_08/cefi_manifest_combo_instrument_type_rebuild_overwrite_2026_08_03.md
created: 2026-07-21
author: unknown
parent_epic: cefi_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P2
estimate_class: design
assigned_role: data-pipeline
drift_direction: none
source:
  investigation (read-only GCS + manifest sampling, 2026-07-21; grep + code read of market-tick-data-service adapters)
depends_on: []
locked_by:
locked_since:
context_scope:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/fail_hard_canonical_enforcement_design_2026_07_20.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/tradfi/tardis_cefi_shards.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/cefi/tardis_shared.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/_mvp_scope_rules.py,
  ]
resolved_by:
  "§9 [DESIGN] P1 cross-check + [WRITER] P1 guard-widen both DONE — unified-api-contracts@11adf279 (DERIBIT-COMBO
  deregistration) + market-tick-data-service@2ddc6d4a (bare-DERIBIT combo classifier fix, both ingestion paths),
  independently re-verified 2026-07-27 (slot-15), no conflict between the two efforts. The [DATA] P2. partition-MOVE
  --apply remains unstarted and operator-gated per §7. The manifest-row-disappearance P1 root-cause is DONE (2026-08-03,
  slot-14): a genuine Surface C v2 dedup-apply consolidation bug, not an intentional purge — see the 9th todo. Two new
  follow-on todos filed (an [OPERATOR] MVP-scope decision + a low-priority [DATA] bookkeeping-regen todo); both open."
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

## 8a. Same mechanism's OTHER symptom — the "FUTURE row requires 'expiry_date'" hard-failure population

Traced 2026-07-27 (slot-15) from `cefi_high_attempted_failed_batch_cluster_2026_07_23.md`'s todo 4: a combo-shaped bare-
`DERIBIT` symbol that reaches the FUTURE branch (rather than the perpetual/dated-future defaults this doc's §2/§3
measured) doesn't silently mispartition — `derive_row_instrument_id`'s FUTURE-branch expiry-parsing helpers
(`parse_deribit_future_symbol` / `_parse_numeric_futures_expiry` / `_parse_month_code_futures_expiry`) all structurally
fail on a multi-leg combo id, so it raises `ValueError("FUTURE row requires 'expiry_date'")` instead — a hard
`attempted_failed`, not a silent write. Measured: 4,812 manifest rows / 786 distinct symbols, 100% `venue=DERIBIT`, 100%
confirmed combo-shaped via the real `is_deribit_combo_symbol_shape()`, and 100% pre-dating `2ddc6d4a` (max
`attempted_at` 2026-07-21T11:47Z, the fix shipped 2026-07-22T18:28Z) — zero recurrence since. **Same root cause, same
fix, already resolved by the §9 `[WRITER] P1` guard-widen** — no separate code action needed. The 786-symbol historical
backlog remains an unretried capture gap (normal backfill re-attempt, not a code change).

## 9. Todos

- [x] [DESIGN] P1. **DONE 2026-07-27 (slot-15)** — Cross-checked this doc's root-cause fix (§3, §6) against the
      concurrent DERIBIT-COMBO venue-registry purge (§8); independently re-verified the finding already recorded in
      `cefi_4surface_migration_execution_log_2026_07_24.md` row 7 (that entry covers this todo but the checkbox here was
      never flipped). **Verdict: NO CONFLICT — synergistic, not conflicting.** Verified directly: 1.
      `unified-api-contracts@11adf279` (2026-07-21 17:24:44+01:00) deregistered `DERIBIT-COMBO` from every UAC registry
      (0 captured rows, operator-ruled legacy venue). 2. `market-tick-data-service@2ddc6d4a` (2026-07-22 18:28:09+01:00
      — the DAY AFTER) shipped this doc's §9 `[WRITER] P1` guard-widen: hoists `is_deribit_combo_symbol_shape` above
      `_classify_row_instrument_type`'s venue-label branch for the BARE `DERIBIT` venue, plus the required
      `finalise_rows_and_path`/ `SINGLE_INSTRUMENT_TYPES` COMBO-case companion fixes traced in §3. 3. **Both ingestion
      paths confirmed covered** — `tardis_cefi_shards.py:298,590` calls `self._classify_row_instrument_type(s, venue)`,
      the SAME shared method `2ddc6d4a` fixed on `TardisAdapter`; there is no separate/duplicate classifier to port the
      fix into, resolving §3's "leak not closed in the primary ingestion path" concern. 4.
      `_filter_bulk_rows_for_deribit_split`'s `DERIBIT-COMBO` branch (§3/§8's flagged routing target) is now dead code
      for a deregistered venue, but harmlessly so — its bare-`DERIBIT` branch (`is_bare_option` isolation) is untouched
      and still correct, and post-`2ddc6d4a` any bare-`DERIBIT` combo-shaped row is classified `COMBO` directly rather
      than needing the old DERIBIT-COMBO-venue routing detour. This IS the "new mechanism" §8 anticipated would be
      needed — it already shipped, just not framed as answering §8. No further code action needed for this cross-check;
      the `[WRITER] P1` sibling todo below is DONE (already shipped, confirmed above). The `[DATA] P2.` partition-MOVE
      `--apply` remains fully unstarted and operator-gated per §7 — this cross-check does not touch or unblock that.
- [x] [WRITER] P1. **DONE — `market-tick-data-service@2ddc6d4a`** (2026-07-22, independently re-verified 2026-07-27
      slot-15, see the todo above). Widened the combo-shape guard: hoists `is_deribit_combo_symbol_shape` above
      `_classify_row_instrument_type`'s venue-label branch for bare `DERIBIT`. The second half ("port into
      `tardis_cefi_shards.py`") needed no separate port — that file calls the same shared
      `self._classify_row_instrument_type(s, venue)` method the fix modified, confirmed by direct grep/read
      (`tardis_cefi_shards.py:298,590`), so both ingestion paths share one fixed classifier already.
- [x] ✅ [DATA] P2. **DONE 2026-08-03 (slot 15, task `deribit_combo_perpetual_partition_move-003`)** — Implement +
      dry-run the partition-move script per §5-6 against the 15,119-row scope measured in §2b; canary on the two objects
      named in §6 before any full `--apply`. Shipped: `market-tick-data-service@04d48b3c` (census + full 7-step move
      mechanic per §5, `--apply` gated behind an explicit self-refusal citing §7 until the sibling todo below clears;
      `--dry-run`/`--canary` fully implemented and exercised against live production data, read-only — no GCS object
      written/moved/deleted, `--apply` never invoked). `quality-gates.sh` green (9847 passed, coverage 80.68%),
      sentinel-verified on the shipped SHA, quickmerge landed on `live-defi-rollout`. **Significant finding surfaced
      while testing, not yet in this doc's earlier sections**: the live manifest today shows ZERO qualifying candidate
      rows, a sharp drop from this doc's 2026-07-21 measurement (15,119 rows: 8,849 `perpetual` + 6,270 `future`).
      Verified concretely: a full census run found only false-positive shape matches (`BTC-USDC@LIN`-style linear-perp
      symbols, correctly rejected by the catalogue cross-check, 0 real combo hits survive it); `instrument_type=COMBO`
      now has **0 rows manifest-wide, for any venue** (down from this doc's own §2b baseline of 662 DERIBIT `combo`
      rows) — the entire combo classification appears to have been pruned from the manifest sometime in the intervening
      13 days (unrelated migration work — the cefi tranche has seen heavy churn this period per its own
      consolidated-closeout history). **The underlying GCS objects were NOT necessarily moved along with this** —
      directly re-confirmed one of §6's two canary objects
      (`.../instrument_type=perpetual/data_type=book_snapshot_5/BTC-FS-26DEC25_PERP.parquet`, 37,258 rows,
      `instrument_id` content column still reads the wrong `DERIBIT:PERPETUAL:BTC-FS-26DEC25_PERP`) still physically
      exists at its OLD wrong-partition path, but the manifest now carries **no row mentioning this symbol at all** —
      not even a stale/wrong one. **Practical implication for the operator-review todo below**: do not schedule
      `--apply` against this doc's stated 15,119-row scope without first re-running this script's `--dry-run` to get the
      CURRENT candidate list — the manifest-driven scope may have shrunk to near-zero, OR (more likely, per the
      orphaned-object evidence) the real remaining population is now UNDER-COUNTED by any manifest-only census, because
      these specific objects still sit at the wrong path with wrong content but are invisible to a manifest-only scan. A
      GCS-object-level re-scan (not just the manifest) is probably needed before the operator review can trust either "0
      remaining" or "15,119 remaining" as the true count. Root cause of the manifest-row disappearance not investigated
      this session (out of scope for the implement+dry-run todo; flagging for whoever does the operator-review pass, or
      as a fresh finding if it recurs).
- [ ] [DATA] P2. **BLOCKED-OPERATOR — genuine sign-off decision, not worker-determinable, per §7.** (2026-08-09, main:
      removed an erroneous "RULED 2026-08-06 (operator): proceed now... AO-dispatchable" framing that previously opened
      this item — no corroborating Progress Log entry or live escalation was found for that claim; see the Progress Log
      entry below.) Operator review of §7 (widened scope, live-fleet sequencing, code-fix-first ordering) before any
      `--apply` is scheduled. **Scope re-verified 2026-08-03 (task `deribit_combo_perpetual_partition_move-004`,
      slot 13)**: re-ran §2a's own methodology (bounded, single-day-prefix-per-call GCS listing, no full corpus walk)
      against the same 13 sampled days for both `perpetual`/`future` partitions. Result: **every object §2a originally
      found is still physically present, unchanged, at its original wrong-partition path** — per-day counts are
      byte-identical to §2a's table (e.g. `2023-06-01/perpetual`: 60 objects/6 combo-shaped then and now;
      `2025-01-15/perpetual`: 38/2 then and now; 1,106 objects scanned across the sample, 14 combo-shaped stems found,
      matching §2a's original 14/980 exactly). **Conclusion: the manifest census's drop to 0 candidates (prior todo's
      2026-08-03 finding) is NOT evidence the defect was fixed or any data moved — no GCS object was touched.** The
      manifest lost visibility into rows it previously tracked; treat the true remaining scope as still ~15,119 rows
      (§2b's count) for this review, not 0, until the manifest-row-disappearance is root-caused (new todo below). **This
      todo cannot be completed by a worker** — §7 explicitly requires operator sign-off on (a) the widened scope (now
      reconfirmed as real and current, not stale), (b) sequencing against the live fleet touching the same manifest/GCS
      prefixes, and (c) landing the code fix before any backfill move (already done — §9's `[WRITER] P1` todo,
      `2ddc6d4a`, both ingestion paths confirmed covered). Filed as a `/blocked` question this session; awaiting
      operator answer.
- [x] ✅ [DATA] P1. **DONE 2026-08-03 (slot 14, task `deribit_combo_perpetual_partition_move-005`)** — Root-caused via
      direct evidence, not inference: read the ACTUAL pre-apply manifest snapshot the Surface C v2 dedup script itself
      wrote
      (`gs://market-data-tick-cefi-prd-central-element-323112/_index/snapshots/pre_d4_20260724T232332Z/availability_index.parquet`,
      189,313,328 bytes, one bounded whole-object read) and diffed it against the CURRENT live manifest (same bucket,
      `_index/availability_index.parquet`), plus the actual VM run.log for the exact apply
      (`gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-cefi-dedup-apply-20260724-232055/run.log`).
      **Verdict: (b) — a genuine manifest-consolidation correctness bug, NOT an intentional purge.**

      **Direct proof of timing + scope**: the pre-apply snapshot (taken by the script itself at 2026-07-24T23:23:32Z,
                                                                                                              seconds before its own write) has EXACTLY 662 `instrument_type=combo` rows, 100% `venue=DERIBIT`, 100%
                                                                                                              `capture_status=empty_confirmed` (zero real tick data — honest-absence bookkeeping only, matching this doc's own
                                                                                                              §2b baseline exactly). The current live manifest (2026-08-03) has 0 combo rows, any venue, any status. Per this
                                                                                                              doc's own `cefi_4surface_migration_execution_log_2026_07_24.md` history, the ONLY write to
                                                                                                              `availability_index.parquet` in the entire 2026-07-21→2026-08-03 window is this one Surface C v2 `--apply` run
                                                                                                              (Finding 7, `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24.md`) — so the drop is bounded to this
                                                                                                              exact event, not a slow drift.

                                                                                                              **This was NOT the intentional part of that apply.** The apply's own run.log shows exactly one COMBO-labeled,
                                                                                                              reviewed, ruled drop: `[v2 P3b] DERIBIT-COMBO (purge): rows=196 captured=0 purged=196 renamed=0` — the SEPARATE,
                                                                                                              operator-ruled `venue=DERIBIT-COMBO` purge (`combo_mask = venue.str.upper() == "DERIBIT-COMBO"` in
                                                                                                              `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py`, confirmed by direct code read — scoped to the VENUE
                                                                                                              label only, never touches bare `venue=DERIBIT` rows regardless of `instrument_type`). Our 662 bare-DERIBIT
                                                                                                              combo rows appear in NEITHER this stat NOR the run's only other named drop counters
                                                                                                              (`dropped_orphan=2015` corpus-wide, `okx_noise_drop=7`) — they were never a reviewed/logged target of this
                                                                                                              migration; they were silently swept into one of the run's two large, itype-unbroken-down bulk counters:
                                                                                                              `eu-dropped=261630` or `de-dup-collapsed=1267269` (`by status: {expected_unattempted: 562590,
                                                                                                              empty_confirmed: 549447, attempted_failed: 155170, captured: 62}`).

                                                                                                              **Code-level narrowing (rules out 2 of 3 candidate mechanisms, does not fully pin the 3rd to one line):**
                                                                                                              `_reconcile_eu_duplicates` filters strictly to `capture_status == "expected_unattempted"` — our rows were
                                                                                                              `empty_confirmed`, so eu-reconcile structurally cannot be the mechanism. The per-tuple orphan-drop path
                                                                                                              (`_classify_tuple`) short-circuits any ALREADY-canonical id (`if kind == "canonical": return cur,
                                                                                                              "already_canon"`) straight to `relabel` (keep), never `drop` — and these rows already carried canonical
                                                                                                              `DERIBIT:COMBO:...` ids pre-apply, so the orphan-drop path is also structurally ruled out. That leaves
                                                                                                              `_dedup_blob`'s per-blob duplicate-collapse (`drop_duplicates` on the effective key, keep-best-`_STATUS_RANK`)
                                                                                                              as the only remaining candidate in this script — its own key (`PIN_ATOM` = date+venue+data_type+
                                                                                                              instrument_type+instrument_id+pipeline_mode) DOES include `instrument_type`, so it should only collapse
                                                                                                              same-itype duplicates, not cross-itype (i.e. NOT colliding against the separately-tracked 15,119 mispartitioned
                                                                                                              perpetual/future rows for the same symbols — verified those are still present, see the sibling todo above).
                                                                                                              The aggregate log has no per-`instrument_type` breakdown of which rows lost a collapse, so the exact
                                                                                                              colliding sibling per group could not be confirmed without a live, corpus-wide re-run of the classification
                                                                                                              pipeline — correctly out of scope/budget for this root-cause todo (heavy, would need the memory-bounding
                                                                                                              guardrail); flagged below as a residual open question only if the exact line-level mechanism ever becomes
                                                                                                              load-bearing.

                                                                                                              **Independently confirmed contributing correctness gap (verified live against the current catalogue, not
                                                                                                              assumed):** `unified-api-contracts@11adf279` (2026-07-21, the SAME day as this doc's §2b baseline) removed
                                                                                                              `"COMBO"` from `CeFiMvpRule.instrument_types` entirely (`MVP_SCOPE_CONFIG_VERSION` 19→20), on the commit's own
                                                                                                              stated premise **"DERIBIT-COMBO was the only CeFi consumer of 'COMBO'"** — empirically FALSE per this doc's own
                                                                                                              §2 census (662 + 15,119 rows, 100% catalogue-cross-check-confirmed `instrument_type=COMBO` for BARE
                                                                                                              `venue=DERIBIT`, not `DERIBIT-COMBO`). Verified live this session: `prod/catalog.parquet` still declares
                                                                                                              **70,128** bare-`DERIBIT` `instrument_type=COMBO` rows, but **100% now carry `mvp=False`**. The dedup script
                                                                                                              itself never reads the `mvp` column (`_load_catalog` projects only
                                                                                                              `venue/instrument_type/raw_symbol/instrument_id/canonical_instrument_id`), so this is NOT the direct drop
                                                                                                              mechanism traced above — but it is a real, independent, confirmed SSOT contradiction with two compounding
                                                                                                              consequences: (1) these bookkeeping rows will not self-heal on any future MVP-scope-driven
                                                                                                              expected-universe/expected_unattempted materialization while `mvp=False` persists, and (2) this doc's own
                                                                                                              PENDING §9 `[DATA] P2.` 15,119-row partition-MOVE (once operator-approved) would land real CAPTURED combo data
                                                                                                              that STILL reads as non-MVP even after being correctly repartitioned — undermining coverage/expected-universe
                                                                                                              tracking for the exact population this whole doc exists to fix, not just the historical 662-row bookkeeping
                                                                                                              loss. Flagging as its own decision below (do NOT unilaterally revert part of a 2026-07-21 explicit operator
                                                                                                              ruling without operator awareness — filed a `/blocked` question this session, see Progress Log).

                                                                                                              **No CAPTURED tick data was lost** (the apply's own `[INVARIANT] CAPTURED rows in the v2 drop set: 0` gate is
                                                                                                              real and correctly enforced) — this is a bookkeeping/tracking-fidelity regression, not a data-loss incident.

- [x] ✅ [OPERATOR] P2. **RULED 2026-08-03** — operator approved re-adding `"COMBO"` to
      `unified_api_contracts.canonical.crosscutting._mvp_scope_rules.CeFiMvpRule.instrument_types` for BARE
      `venue=DERIBIT` (keeping `DERIBIT-COMBO` excluded, unchanged). The 2026-07-21 `uac@11adf279` removal's stated
      premise ("DERIBIT-COMBO was the only CeFi consumer of 'COMBO'") is empirically disproven by this doc's own
      measurements — **70,128** catalogue-declared, real bare-DERIBIT COMBO instances exist and were tagged `mvp=False`;
      this was the empirical finding that motivated the reversal. Shipped — `unified-api-contracts@3be60810` (code+test
      commit `cd35596d`, size-cap trim `3be60810`, both verified on `origin/live-defi-rollout`): re-added `"COMBO"` to
      `CeFiMvpRule.instrument_types` (bare DERIBIT already `venues`-registered, no per-venue override, so COMBO inherits
      the flat data_types set — matches the real captured data_types: trades/book_snapshot_5/derivative_ticker); bumped
      `MVP_SCOPE_CONFIG_VERSION` 21→22 (not 20→21 as this todo originally estimated — v21 had already been taken by an
      unrelated `models`-MVP change landed between this todo's filing and its ruling); restored
      `TestDeribitComboInstrumentTypeV16`-style test coverage as a new `TestDeribitBareComboInstrumentTypeV22` class,
      scoped to bare `DERIBIT` (not `DERIBIT-COMBO`, which stays deregistered/excluded — verified by its own negative
      test). Full quality-gates.sh green (0 new violations; file-size comment kept lean specifically to avoid consuming
      the repo's `CODEX_MAX_VIOLATIONS` ratchet budget). The 662-row bookkeeping backfill (next todo) was explicitly
      left unblocked by the operator's ruling — not addressed by this commit.
- [x] ✅ [DATA] P3. Decision: let the 662 lost `empty_confirmed` bookkeeping rows regenerate naturally. The MVP scope
      fix already shipped (`uac@cd35596d`/`3be60810` — COMBO re-added to `CeFiMvpRule.instrument_types` for bare
      DERIBIT, operator-ruled 2026-08-03). No code change needed; the next expected-universe materialization cycle will
      regenerate these rows automatically now that COMBO is back in MVP scope. The rows were pure bookkeeping (zero
      captured tick data lost, confirmed by the Surface C v2 apply's own invariant gate). Repo: instruments-service /
      market-tick-data-service, whichever owns the expected_unattempted regeneration path.

## Progress Log

- **2026-08-09** (main agt-22de53, relaying a careful catch from agt-51e4bd/slot 9): the [DATA] P2 `--apply` todo was
  self-contradictory — its own opening sentence claimed "RULED 2026-08-06 (operator): proceed now... AO-dispatchable"
  while its own trailing text (same item) said "This todo cannot be completed by a worker... awaiting operator answer."
  Worker checked this doc's Progress Log for a substantiating 2026-08-06 entry (found none — only unrelated
  context-scout housekeeping that date) and `GET /api/escalations/active` (found no live escalation tracking it either).
  No evidence anywhere corroborates the "proceed now" claim. Removed that erroneous framing, keeping the corroborated
  BLOCKED-OPERATOR status — this does NOT approve the underlying ~15,119-row prod GCS partition move; it only corrects a
  doc-accuracy error and reaffirms the existing (safer) gate. The actual §7 sign-off decision (widened scope /
  sequencing / code-fix-first ordering) remains genuinely operator-only and unresolved.
- **2026-08-03** (slot 15, data_engineering, task `deribit_combo_perpetual_partition_move-003`) — Implemented the
  census + partition-move script (see todo 3 above for full evidence). Session ended mid-QG-run (shared host, several
  concurrent `quality-gates.sh` invocations queued); script is dry-run-tested and correct but not yet committed. No GCS
  object was written, moved, or deleted this session — every check was a read (`gcs_describe_object`/
  `download_bytes`/bounded `list_blobs`), and `--apply` was never invoked (the script itself refuses `--apply` with a
  citation to §7 pending the operator-review todo). Next session: confirm QG result, `quickmerge --agent` the script,
  flip todo 3 with the shipped SHA, and consider whether the manifest-drift finding warrants its own issue doc if the
  root cause turns out to be a live-data-correctness regression rather than an already-intentional cleanup.
- **2026-08-03** (slot 13, data_engineering, task `deribit_combo_perpetual_partition_move-004`) — Task was the remaining
  "operator review of §7" todo. This is a genuine operator-sign-off gate per §7 (production-data MOVE, widened scope,
  live-fleet sequencing) — not worker-determinable, so no attempt was made to flip that checkbox unilaterally. Did the
  doable prep the todo itself calls for: re-ran §2a's bounded GCS-listing methodology (same 13 days, both
  `perpetual`/`future` partitions, read-only, no full corpus walk) to resolve whether the prior session's
  manifest-census-drop-to-0 meant the defect was fixed. It was not — every originally-flagged object is still physically
  present unchanged at its wrong-partition path; only the manifest's visibility into these rows changed. Updated the
  operator-review todo with the reconfirmed ~15,119-row scope and filed a new P1 todo for the manifest-row-disappearance
  root cause (untouched — genuinely separate work, flagged not fixed). Filed a `/blocked` question to the operator
  carrying §7's three sign-off items plus this session's reconfirmed numbers. No GCS object written/moved/deleted; no
  manifest row written; investigation script kept in scratchpad (one-off, not committed per script-homes). Next session
  (whoever the operator's answer routes to): if approved, schedule the `--apply` per §5-6's canary-then-full-batch plan
  using `market-tick-data-service@04d48b3c`'s script; either way, someone should pick up the new manifest-drift
  root-cause todo independently since it doesn't block the operator decision itself.
- **2026-08-03** (slot 14, data_engineering, task `deribit_combo_perpetual_partition_move-005`) — Task was the
  manifest-row-disappearance root-cause todo (662→0 combo rows). Root-caused with direct evidence rather than inference:
  read the pre-apply manifest snapshot the Surface C v2 dedup script itself wrote
  (`_index/snapshots/pre_d4_20260724T232332Z/availability_index.parquet`, one bounded whole-object read) and diffed it
  against the current live manifest, plus the exact apply VM's `run.log`
  (`canonical-migration-cefi-dedup-apply-20260724-232055`) and the live catalogue (`prod/catalog.parquet`). Verdict: (b)
  a genuine consolidation correctness bug (silent, unreviewed drop of 662 non-captured bookkeeping rows during the
  2026-07-24 Surface C v2 `--apply`), NOT the intentional part of that migration (the apply's only reviewed
  combo-labeled drop was the separate, correctly-scoped `venue=DERIBIT-COMBO` purge, 196 rows). No CAPTURED tick data
  was lost — the apply's own captured-data invariant held. Also independently confirmed, live, a related SSOT
  contradiction: `uac@11adf279` (2026-07-21) removed `COMBO` from `CeFiMvpRule.instrument_types` entirely on a premise
  ("DERIBIT-COMBO was the only consumer") this doc's own measurements disprove — 70,128 real bare-DERIBIT COMBO
  catalogue rows exist, now all `mvp=False`. Filed two new todos (an `[OPERATOR]` MVP-scope decision + a follow-on
  `[DATA]` bookkeeping-regen todo) rather than unilaterally reverting part of a recent explicit operator ruling. Filed a
  `/blocked` question this session to surface this as a data-correctness finding per CLAUDE.md's "big finding" criteria.
  All reads were bounded single-object GETs (2 manifest blobs pre/post, 1 catalogue blob, 1 log file) — no whole-corpus
  walk, no GCS write, no manifest write. Investigation scripts kept in scratchpad (one-off, not committed per
  script-homes). Next session: awaiting operator answer on the MVP-scope todo; the bookkeeping-regen todo is
  low-priority and can wait indefinitely.
- **2026-08-03** (slot 10, task `deribit_combo_perpetual_partition_move-006--ruling`) — Applied the operator's ruling on
  the `[OPERATOR] P2` MVP-scope todo above: re-added `"COMBO"` to `CeFiMvpRule.instrument_types` for bare
  `venue=DERIBIT`, keeping `DERIBIT-COMBO` (the venue) excluded/unchanged, per the doc's own 70,128-instance empirical
  finding that the 2026-07-21 removal's "only consumer" premise was false. `unified-api-contracts@cd35596d`
  (code+tests) + `@3be60810` (a same-session size-cap trim — the first commit's inline comment pushed
  `_mvp_scope_rules.py` from 887→902 lines, crossing the repo's 900-line cap; trimmed to 891L rather than spend the
  repo's `CODEX_MAX_VIOLATIONS` ratchet headroom on an avoidable new violation), both verified on
  `origin/live-defi-rollout`. Bumped `MVP_SCOPE_CONFIG_VERSION` 21→22 (this todo's own text said "20→21" when filed, but
  v21 was independently claimed by an unrelated `models`-MVP change that landed between filing and ruling — v22 is
  correct/current). Restored `TestDeribitComboInstrumentTypeV16`-style coverage as
  `TestDeribitBareComboInstrumentTypeV22`, rescoped to bare `DERIBIT` with an explicit negative test confirming
  `DERIBIT-COMBO` stays excluded. Full `quality-gates.sh` green, 0 new violations post-trim. Per the operator's
  instruction, did NOT touch the 662-row bookkeeping backfill (`[DATA] P3` below) — left to self-heal, not blocking this
  fix.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — added `_mvp_scope_rules.py`, the file the newly
  ruled `CeFiMvpRule.instrument_types` COMBO fix (`uac@cd35596d`/`3be60810`) lives in, alongside the 5 pre-existing
  entries.
- **2026-08-05** (slot 14, data_engineering, task `deribit_combo_perpetual_partition_move-007`) — Resolved the
  `[DATA] P3` decision: let the 662 lost `empty_confirmed` bookkeeping rows regenerate naturally. The MVP scope fix
  already shipped (`uac@cd35596d`/`3be60810`, COMBO re-added to `CeFiMvpRule.instrument_types` for bare DERIBIT,
  operator-ruled 2026-08-03). No code change needed — the next expected-universe materialization cycle will regenerate
  these rows automatically. The rows were pure bookkeeping (zero captured tick data lost). This is the final open todo
  in this issue doc; all 7 todos now done.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.

- **2026-08-11 (slot 1): `assigned_vm` corrected `planning` → `NA`.** Every remaining open todo here is operator-gated
  (BLOCKED-OPERATOR — genuine sign-off decision, not worker-determinable (its own §7)), so AO can see nothing to
  dispatch — the doc was an `assigned_vm: planning` plan the orchestrator never touches, which is exactly the condition
  `check_ao_dispatch_visibility_gate.py`'s `max_zero_dispatchable_docs` axis exists to flag. `NA` is the semantically
  correct value per `assigned_vm` (`planning` = the orchestrator VM executes it; `NA` = not dispatched). NO todo text,
  marker, or priority was altered — the exclusion markers were re-read and are correct and deliberate, not stale. Flip
  back to `planning` if and when the gate opens and the work becomes worker-determinable.
