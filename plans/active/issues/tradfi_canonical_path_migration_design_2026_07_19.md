---
doc_type: issue
title: "TradFi canonical GCS-path + manifest migration — orphan-proof design (2.35M objects, 95 legacy shapes)"
summary:
  Full physical enumeration of the tradfi tick bucket (2.35M+ objects) reveals 95 distinct legacy path shapes, not the
  4-5 first assumed. This doc is the orphan-proof migration design — a TOTAL disposition map (every object gets exactly
  one disposition; the ORPHAN bucket is proven empty), the canonical target per class, the writer/reader/checker
  lockstep changes, the Massive purge sequencing, and the destructive-op gates. Companion to
  tradfi_consolidated_closeout_2026_07_18.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, instruments-service]
scope: [engineer, admin]
tags: [canonical-id, gcs-path, manifest, shard-atom, honest-coverage, massive-purge, orphan-proof, data-correctness]
related: [tradfi_consolidated_closeout_2026_07_18, databento_future_option_blank_instrument_id_shard_atom_2026_07_19]
created: 2026-07-19
author: unknown
priority: P0
parent_epic: tradfi_master
source: "Full physical GCS enumeration (bny7k1yk6) + investigation workflow (wlixucotm), 2026-07-19"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
assigned_vm: planning
resolved_by:
context_scope:
  [
    market-tick-data-service/market_tick_data_service/scripts/migrate_tradfi_canonical_2026_07.py,
    unified-api-contracts/unified_api_contracts/canonical/partition_paths.py,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/tradfi_casing_100pct_redrift_2026_07_27.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/epics/tradfi_master.md,
  ]
---

# TradFi Canonical Path Migration — Orphan-Proof Design

## Why this exists (operator intent, 2026-07-19)

Backfills were STOPPED so the GCS path + manifest layout is settled BEFORE more data lands — "else its gonna be messy to
do completion stats." Operator ruling (from live cefi): match cefi's TWO shapes exactly. Requirement: **no orphans —
every single previous file is deterministically mapped to a new path; missing/unmapped files are a LOUD audit failure,
not a guess.** Massive is purged (Databento = batch SoT, Yahoo = daily candles). Manifest rebuilt + catalogue
MVP-stamped post-migration.

## Canonical target (matches cefi 1:1)

```
raw_tick_data/by_date/day=<D>/pipeline_mode=batch_<source>/asset_group=tradfi/venue=<V>/instrument_type=<IT>/data_type=<DT>/<TAIL>

  · CHAIN  (IT ∈ {futures_chain, options_chain, combo})  TAIL = underlying=<BASE>/quote=<QUOTE>/margin=<MODE>/ticks.parquet
           e.g. CME S&P futures:  underlying=SP500/quote=USD/margin=linear/ticks.parquet   (@LIN ↔ margin=linear; tradfi = USD/linear)
  · SINGLE (IT ∈ {equity, etf, spot_pair})                TAIL = <FULL_CANONICAL_ID>.parquet
           e.g. NYSE:EQUITY:ABBV-USD.parquet ; FX:SPOT:EUR-USD.parquet
```

cefi proof: `.../instrument_type=futures_chain/data_type=trades/underlying=BTC/quote=USD/margin=inverse/ticks.parquet`
(bundle) vs `.../instrument_type=perpetual/data_type=trades/DERIBIT:PERPETUAL:BTC-USD@INV.parquet` (single).

## Ground truth

Physical enumeration `bny7k1yk6` — **FINAL: 2,734,646 objects (walk complete, rc=0)**; NOT the manifest (the manifest
has casing chaos `EQUITY`/`equity` same partition + 69% ghost rows). Analysis scripts (scratchpad, reusable):
`shape_taxonomy.py` (95 distinct templates), `orphan_classifier.py` (disposition classifier, 0-orphan proof).

**Definitive final reconcile (full 2,734,646-object corpus, 0 ORPHAN):** PURGE_MASSIVE 1,696,166 · MIGRATE_CHAIN_ADDQM
528,961 · MIGRATE_SINGLE_RENAME 389,703 · MIGRATE_HYPHEN 100,698 · QUARANTINE_GARBAGE_UL 14,633 · MIGRATE_CONTENT_REPAIR
1,478 · QUARANTINE_CORRUPT 1,180 · MIGRATE_NONHIVE_EQ 920 · MIGRATE_SINGLE_NOOP 907. Totals: MIGRATE 1,022,667 · PURGE
1,696,166 · QUARANTINE 15,813 · **ORPHAN 0** (1,022,667 + 1,696,166 + 15,813 = 2,734,646 ✓). The interim table below
(2.35M) is superseded by these final counts.

## Proven orphan-proof disposition map (2.35M objects, 0 ORPHAN)

| disposition               | objects   | canonical action                                                                                                  |
| ------------------------- | --------- | ----------------------------------------------------------------------------------------------------------------- |
| **PURGE_MASSIVE**         | 1,469,325 | `pipeline_mode=batch_massive/*` → delete AFTER Databento-backfilling the 571 Massive-only shards                  |
| **MIGRATE_CHAIN_ADDQM**   | 473,408   | chain `underlying=X/ticks.parquet` → add `quote=USD/margin=linear` partitions (content re-derives BASE)           |
| **MIGRATE_SINGLE_RENAME** | 286,729   | single, dir canonical, bare/`_migrated_` filename → rename to full canonical id                                   |
| **MIGRATE_HYPHEN**        | 100,698   | legacy `day-` (hyphen) non-Hive → full Hive canonical                                                             |
| **QUARANTINE_GARBAGE_UL** | 12,784    | `underlying=`∈{12,13,23,…} numeric garbage — quarantine, NEVER fake-canonicalize (88% Databento-side; own defect) |
| MIGRATE_CONTENT_REPAIR    | 1,462     | non-canonical itype (`future`/`option`/`index`/plural `equities`) → read content, re-derive canonical             |
| MIGRATE_NONHIVE_EQ        | 896       | `day=/data_type=/(equities\|etf)/` non-Hive pocket → Hive canonical                                               |
| MIGRATE_SINGLE_NOOP       | 889       | already full-id — verify only                                                                                     |
| QUARANTINE_CORRUPT        | 801       | doubled/missing/reordered Hive segments, symbol-less `ticks.parquet` → content-repair or quarantine               |
| **ORPHAN**                | **0**     | ✅ empty — map is total                                                                                           |

Totals: MIGRATE ≈ 864K · PURGE ≈ 1.47M · QUARANTINE ≈ 13.6K · ORPHAN 0.

## Migration must be CONTENT-based, not path-rename

Paths are unreliable (garbage underlying, missing/doubled segments, symbol-less `ticks.parquet`). The executor reads
each parquet → derives canonical `instrument_id`/`underlying`/`quote`/`margin` from the rows via the UAC SSOT
(`derive_tradfi_row_instrument_id`, `tradfi_symbology`, `build_tradfi_partition_path`) → writes canonical → verifies →
deletes old. Any object that reaches ORPHAN at runtime ABORTS loudly.

## The keystone change (shard-atom lockstep — one coherent cross-repo change)

The chain `quote=/margin=` partitions change the shard atom → writer↔manifest↔reader↔checker↔UI must move together:

1. **UAC** `unified_api_contracts/canonical/partition_paths.py::build_tradfi_partition_path` — emit chain
   `underlying=/quote=/margin=/ticks.parquet` + single full-id filename. (Shared SSOT both writer + executor use.)
2. **MTDS W1** `partitioned_writer.py::_resolve_file_symbol` (L273) — add `"tradfi"` (currently prediction/cefi-only);
   precondition: `instrument_id` populated+canonical on every tradfi row-group (Databento ✓; verify UMI Yahoo).
   `_resolve_writer_file_name` (L136-163) — chain branch add quote/margin; harden L163 `ticks.parquet` fallback to RAISE
   for `asset_group=="tradfi"` (mirror W2), scoped to tradfi (prediction book_snapshot_5 keeps the silent fan-in).
3. **MTDS W2** `tradfi_shared.py::_file_stem_for` (L419-469) — single branch use per-row `instrument_id` (already at
   L513) not bare symbol; chain branch feed underlying/quote/margin.
4. **Readers/checker** `reader.py::_build_shard_bases`, `pipeline_e2e_check.py::_write_prefix_candidates`,
   `partition_paths.py::candidate_parquet_paths` — probe the new shape.
5. **Manifest** shard atom carries quote=/margin= for chains; rebuild post-migration (single-walk, consolidator paused).

## Massive removal (non-destructive prep is autonomous; the DELETE is gated)

- Non-destructive NOW: drop `massive` from `_source_priority_data.py` (lines 333/334/354/357/368/369) +
  `SOURCE_MODE_CAPABILITY` (483) + `EMISSION_LATENCY_MS_BY_SOURCE` (639) — no-op for live traffic (Databento already
  index[0]); remove runtime routing (`--source massive`, `massive-futures-backfill`, `_umi_massive.py`).
- KEEP `possible_manifest.py:217` `massive` + `PipelineMode.BATCH_MASSIVE` until the GCS purge completes (else the
  phantom-audit flags 1.47M real objects as orphans).
- Before delete: Databento-backfill the **571 Massive-only `(venue,data_type,date)` shards** (NASDAQ/trades 300,
  CME/trades 214, CME/tbbo 49, …; all 2023-05→2026-05, inside Databento's window → recoverable), re-verify zero
  Massive-only remains. THEN the 1.47M-object delete → **operator go** (prod-data delete = hard-stop).

## Decisions defaulted (documented; flag on operator return)

- ~~**Combo** → chain-bundle (matches W1 `_UNDERLYING_PARTITIONED_TYPES` + cefi). Operator ruling named futures/options;
  combo is the same bundling class.~~ **SUPERSEDED 2026-08-11 — see "2026-08-11 update" section below.** This default
  was never fully implemented: the shipped writer + UAC oracle deliberately excluded combo from the quote=/margin= chain
  treatment (unsettled leg-id at the time, per `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`), but
  `migrate_tradfi_canonical_2026_07.py` was never updated to match — causing a real orphaned-duplicate-object bug (see
  below). The operator's 2026-08-11 ruling is the current design; do not re-apply this original default.
- **`underlying=12/13/23` garbage** → quarantine loudly; separate pre-existing defect (88% Databento). Own issue doc.
- **Catalogue MVP-stamping already exists** (`catalog.parquet` `mvp: bool` from UAC `is_mvp()`, config v18; out-of-MVP =
  legitimate absence, never a gap). Action = re-run `build_instrument_catalogue.py --asset-group tradfi` post-migration.
  Flag: tradfi MVP scope is deliberately narrow (CME ES/NQ/commodity + `TRADFI_EQUITY_PERP_BASIS_UNIVERSE` only); most
  of the ~622 SP500/NASDAQ/ETF tickers tag `mvp=False` by design — broadening needs a `MVP_SCOPE` rule edit + version
  bump.

## 2026-08-11 update — combo/chain semantics resolved; duplicate-write root cause found (operator + interactive session)

**Combo's canonical form is bare `underlying=<U>/ticks.parquet`, confirmed live** —
`partitioned_writer.py::_write_group`, `tradfi_shared.py::build_tradfi_partition_path`, and the UAC oracle
(`_partition_path_canonicality.py`) all deliberately exclude `combo` from `CHAIN_INSTRUMENT_TYPES`/`is_chain`. The 07-19
"Decisions defaulted" combo=chain-bundle line above was never actually shipped.

**Operator-resolved design (2026-08-11, supersedes the 07-19 default):**

- `combo` (CEFI's Deribit multi-expiry wrapper string, `manifest_finalize.py::_UNDERLYING_PARTITIONED_TYPES`) renames to
  `combo_chain` — it collides today with the real `InstrumentType.COMBO` enum member (genuine multi-leg tradeable
  instruments, e.g. calendar spreads); `combo_chain` disambiguates the grouping-wrapper sense from the real type.
- For all three bundle types (`futures_chain`, `options_chain`, `combo_chain`): `underlying` = the grouping key (already
  populated correctly); `instrument_id` = blank for grouping rows, not a synthetic fake id; `instrument_type` accepted
  as dual-meaning — in these three specific values it means "grouping," not a real tradeable instrument type. Deliberate
  convention choice, not a new field.
- A genuine 2-4-leg spread combo (real `InstrumentType.COMBO`, e.g. `CL-BZ`, `WHEAT-CORN` — see
  `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`) is a DIFFERENT concept from `combo_chain` (a
  same-instrument-type bundle across related instruments) — both legitimately coexist. `combo/underlying=GC` (a
  single-underlying bundle) vs `futures_chain/underlying=GOLD` (the dated-contract chain) is NOT duplicate content —
  combos can bundle instruments across instrument-type combinations by definition; futures_chain is specifically the
  same-underlying dated-contract chain. Confirmed not a bug.
- Reconciles the pre-existing operator ruling `BLK-ca110c07` (2026-06-28,
  `unified_api_contracts/canonical/crosscutting/_honest_coverage_empty_reasons.py::EmptyConfirmedReason.EXPECTED_CHAIN_AGGREGATE`)
  — chain-aggregate rows were expected to be blank-instrument_id, `row_count=0`, `capture_status=empty_confirmed`
  structural placeholders excluded from the coverage denominator. The live writer instead produces REAL `captured` rows
  with a synthetic non-blank instrument_id for futures_chain/options_chain (e.g. `CME:FUTURE:GOLD`) sitting in the SAME
  bucket as blank-id placeholders and separate per-contract `instrument_type=FUTURE` rows — real double-counting risk
  for any downstream query summing `captured` rows without filtering to one canonical `instrument_type`. The
  instrument_id-blank ruling above closes this gap.

**Duplicate-write bug found and root-caused (historical debris, NOT a live/ongoing bug):** `combo/underlying=GOLD` (and
SP500/WTI/BTC) had TWO physical GCS objects for day=2020-01-06 — a bare-form and a quote=/margin=-suffixed form. Root
cause: `migrate_tradfi_canonical_2026_07.py`'s `MIGRATE_CHAIN_ADDQM` disposition (`_CHAIN_ITYPES` including `combo`) was
built against the now-superseded 07-19 "combo=chain-bundle" default and moved bare combo objects to the quote/margin
form; `recover_tradfi_garbage_underlying_2026_07.py` later wrote FRESH bare-form objects (matching the ACTUAL shipped
writer, which excludes combo) for previously-quarantined garbage-underlying rows recovered into GOLD/SP500/WTI/BTC —
landing both forms for the same cell. The live writer is already correct and non-duplicating going forward; this is
orphaned historical debris from two scripts that disagreed, not an active bug.

**Also found, unresolved:**

- `lifecycle_phase` column dtype drift — `string`-typed (populated) in `futures_chain/underlying=GOLD` vs `null`-typed
  (all-null) in `combo/underlying=GC`, same VM run, same date — breaks clean multi-file schema unification for
  downstream readers. Scope (isolated vs. systemic across write eras) not yet assessed.
- `underlying` naming-convention inconsistency: `combo/` mixes exchange-root short codes (`GC`, `SI`, `HG`, `CL`, `ES`,
  `6A`-`6M`) with display names (`GOLD`, `SILVER`, `COPPER`, `SP500`, `WTI`) and `AUDUSD`-style FX pairs, all for the
  same date; `futures_chain/` uses a third convention (bare currency codes `AUD`/`EUR`/`GBP`, plus unidentified codes
  `XAB`/`XAF`/`XAI`/`XAK`/`XAP`/`XAU`/`XAV`/`XAY`). Not yet scoped as a migration.

## Sequencing

1. Keystone canonical-shape change (UAC + MTDS writer + reader/checker), QG-green, ship. → new data canonical.
2. Massive SOURCE_PRIORITY/routing removal (non-destructive), ship.
3. Build content-based executor (dry-run default, --apply gated, orphan-abort, per-VM-shard manifest); dry-run produces
   full old→canonical manifest + re-proves 0 orphans on the LIVE walk.
4. Databento-backfill the 571 Massive-only shards; verify.
5. **[GATE]** Operator go → run migration on a VM (copy→verify→delete), quarantine garbage/corrupt loudly.
6. **[GATE]** Operator go → purge Massive (1.47M objects).
7. Rebuild manifest/availability_index (single-walk, consolidator paused) + regen catalogue (MVP re-stamp).
8. Post-migration audit: re-walk → 0 legacy shapes + 0 orphans + count reconciles. Then re-run backfills → Phase D gate.

## Hard-stops (operator-only)

Massive 1.47M-object delete · legacy-object delete after copy · any prod-bucket delete. Non-destructive prep + dry-run +
canonical-shape code changes proceed autonomously.

## Progress log

- **2026-07-19 — Keystone step 2/3 (SINGLES filename) SHIPPED `mtds@d257b7be`** (QG-green: 6433 passed, 0 failed). W1
  `partitioned_writer.py::_resolve_file_symbol` gate extended to `tradfi` (singles now named by full canonical
  `instrument_id`, e.g. `NYSE:EQUITY:ABBV-USD.parquet`, `FX:SPOT_PAIR:EUR-USD.parquet`); W2
  `tradfi_shared.py::_file_stem_for` single branch stems by `instrument_id` (combo excluded — unsettled leg-id; chain
  branch untouched); `_umi_yahoo.py` FX + KRX-equity rows now stamp the canonical id via
  `derive_tradfi_row_instrument_id`; W1 symbol-less non-derivative tradfi fallback now RAISES (prediction
  book_snapshot_5 keeps the silent ticks.parquet fan-in). Filename-only — manifest shard atom unchanged (stays on bare
  symbol). Two tests that asserted the OLD tradfi-excluded behavior were fixed (FX test → canonical `FX:SPOT_PAIR:` id)
  / the now-obsolete "excluded-supported-group" test deleted (writer supports only cefi/tradfi/prediction — all three
  now in the override). **STILL PENDING in the keystone:** the CHAIN `quote=/margin=` shard-atom change (writer chain
  branch + UAC `build_tradfi_partition_path` + reader/checker + manifest) — the higher-risk lockstep piece, next.
- **Orphan-proof map**: PROVEN on the full 2,734,646-object corpus, 0 orphans (see final reconcile above).
- **2026-07-19 — Dry-run migration EXECUTOR SHIPPED `mtds@e16705db`**
  (`market-tick-data-service/scripts/migrate_tradfi_canonical_2026_07.py`
  - 18 unit tests; QG-green). Dry-run over the full enumeration re-proves 0 ORPHAN + disposition counts EXACTLY match
    the final reconcile. 1:1 object migration (copy→verify→delete), `--apply` gated; massive-purge double-gated
    (`--purge-massive` + `--massive-backfill-verified` sentinel); quarantine → `_quarantine/` (never deletes/fake-
    canonicalizes). Local `_canonical_target` = the reference spec the writer lockstep change must match.

## REBUNDLE — the per-contract options_chain SECOND pass ✅ BUILT `mtds@e243460c`

**RESOLVED (tooling)**: `market-tick-data-service/scripts/rebundle_tradfi_chains_2026_07.py` (dry-run default, `--apply`
gated, +20 tests, QG-green). Dry-run over the full enumeration: **140,138 non-massive per-contract sources → 2,841
per-root bundles + 4 quarantine** (`_unknown_` empty-symbol; never fake-bundled), 0 unclassified. Byte-identical to the
1:1 executor (`imports` `_canonical_chain_path`) + the manifest rebuild parser; content-authoritative root
(`classify_databento_symbol`→`EXCHANGE_CODE_TO_NAME`), quarantine on root-disagreement, bundle-level VM sharding (each
bundle whole on one VM). `--apply` is part of the GATED migration execution. Note: I defaulted
`options_chain`-_data-type_ to per-root bundling (matches cefi + the futures/options ruling) — flag if a different
granularity is wanted.

Original finding (for provenance):

The dry-run surfaced **149,521 per-contract chain objects** (chain itype, NO `underlying=`, per-contract stem like
`ESZ4_P4200`): **148,524 are CME `instrument_type=options_chain/data_type=options_chain`** (140,135 `batch_databento` +
9,386 `batch_massive`→purge), venue=CME only, 2022-10-13→2025-01-06. Per-root `options_chain` bundles barely exist today
(~127 objects), so these per-contract files are the PRIMARY options-chain data in the WRONG (per-contract) shape. The
operator's per-root ruling (futures+options bundle by underlying, like cefi) requires a **content-aware REDUCE**: read
all option contracts of a root → concat → write ONE `underlying=<ROOT>/quote=/margin=/ticks.parquet` → delete the
per-contract sources. The 1:1 executor records these as content-needed (never lost) but does NOT merge — **a second
`--rebundle` pass is required** (VM-scale content read; ~148K objects). Smaller content-needed tails: 1,808 FX
`ticks_migrated_*` stems (no symbol in path), 1,478 CONTENT_REPAIR, 1,180 CORRUPT.

## Will new backfills STAY canonical post-migration? (operator Q, 2026-07-19)

Not automatically — **only if the WRITER emits byte-identical canonical paths to the migration target** (batch=live).
Status by shape (updated 2026-07-19):

- **SINGLE** ✅ writer full-id shipped `mtds@d257b7be`.
- **CHAIN WRITE** ✅ shipped `uac@ad28e55a` + `mtds@145e4aae` — writer emits `underlying=/quote=/margin=/ticks.parquet`,
  manifest shard-atom carries quote/margin (5-tuple count-key), **byte-identical to the migration executor**
  (test-verified atom==path). **CHAIN READ** ✅ shipped `mtds@935e1f8d` — `reader.py::_blob_paths_derivative` probes the
  v6 tail first (byte-identical, bare fallback for combo/cefi/pre-migration) + `rebuild_tradfi_manifest.py` parses AND
  CARRIES quote/margin into `row_key` so the rebuilt shard atom matches the live writer (a review caught + fixed a
  dedup-key divergence: rebuild had been dropping quote/margin → would double-count chain shards post-rebuild).
  `candidate_parquet_paths`/`pipeline_e2e_check` needed no change (prefix/glob transparent, verified).
- **WRITE-TIME GUARD** ✅ shipped in the same change — `canonical_path_violations` rejects non-canonical tradfi writes
  (chain missing quote/margin, single bare-symbol filename, `batch_massive`, non-Hive) and is CALLED (raises) in the W1
  writer path. So a regressing tradfi write now fails loud at the source.
- **MASSIVE** ❌ still could reappear (routing/`SOURCE_PRIORITY` not yet stripped).
- legacy hyphen/non-Hive/corrupt ✅ won't reappear (superseded writers).

Remaining before backfills resume: ~~(1) reader/checker companion~~ ✅ shipped `mtds@935e1f8d`; (2) **Massive routing
removal**, (3) **manifest-rebuild casing normalization** (`EQUITY`/`equity` is a rebuild-pass inconsistency; physical
paths are lowercase). The **Phase-D gate** force-writes fresh data + asserts canonical shape, so a regressing backfill
fails there. Net: writer-in-lockstep ✅ + write-time guard ✅ + reader companion ✅ + Phase-D assertion — only Massive
removal + casing normalization remain before backfill-resume.

## Todos

- [x] ✅ [DATA] P1. **Strip Massive routing + fix manifest-rebuild casing normalization** — the two remaining items
      before tradfi backfills can resume: (2) remove `massive` from `SOURCE_PRIORITY`/routing (non-destructive prep; the
      1.47M-object purge itself stays operator-gated), and (3) fix the `EQUITY`/`equity` casing inconsistency in the
      manifest-rebuild pass (physical paths are already lowercase). — **Verified 2026-07-28 (slot 9, data_engineering),
      both already shipped by prior sessions, no code change needed this turn:** (2) confirmed via live grep of
      `unified_api_contracts/canonical/crosscutting/_source_priority_data.py` —
      `SOURCE_PRIORITY["tradfi", "trades"/"tbbo"]` is `["databento"]` only,
      `SOURCE_MODE_CAPABILITY`/`EMISSION_LATENCY_MS_BY_SOURCE` carry zero active `"massive"` entries (comment-only
      historical notes), `_umi_massive.py` deleted, `main.py`'s `massive-futures-backfill` operation removed —
      `unified-api-contracts` routing strip is complete (the 1.47M-object GCS purge itself correctly stays
      `[OPERATOR]`-gated per this doc's own hard-stops, untouched). (3) resolved more broadly than this todo's original
      scope via the separate `tradfi_casing_100pct_redrift_2026_07_27.md` campaign — `rebuild_tradfi_manifest.py`'s two
      manifest-emission call sites (`_emit_bundled_shard_row`'s `row_key["instrument_type"]` and `scan_and_rebuild`'s
      `target.add(instrument_type=...)`) now both route through the shared
      `unified_trading_library.canonical.canonicalize_manifest_instrument_type` seam
      (`market-tick-data-service@4122df13`, re-exporting `unified-trading-library@688e49bc`), replacing the old
      raw-hive-token stamp this todo flagged. Confirmed live via source read (no new code needed): both call sites
      present and wired. Residual 82,311 pre-fix lowercase manifest rows are a separate, already-tracked repair todo
      (that doc's todo `-007`, re-tagged off `[OPERATOR]` 2026-07-28, gated on a fresh soft-delete-retention check) —
      out of this todo's own done-when, not re-duplicated here.
- [ ] [OPERATOR] P1. **(NEW 2026-08-11) Correct or retire `migrate_tradfi_canonical_2026_07.py`'s stale
      `MIGRATE_CHAIN_ADDQM`/`_CHAIN_ITYPES` combo membership** — the script still treats combo as chain-eligible for the
      quote/margin tail, contradicting the shipped writer (see "2026-08-11 update" above) and the now-superseded 07-19
      default. Prevents any future `--apply` rerun from recreating the bare/quote-margin split for combo. Repo:
      market-tick-data-service.
- [ ] [DATA] P1. **(NEW 2026-08-11) Verify content-identity then delete the orphaned quote=/margin=-form combo
      duplicates** (confirmed for GOLD/SP500/WTI/BTC, day=2020-01-06; scope the full affected date range across the CME
      combo corpus before any delete) — prod-bucket delete, needs delete-safety-cite per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`. Repo: market-tick-data-service.
- [ ] [DATA] P1. **(NEW 2026-08-11) Implement the instrument_id-blank / combo→combo_chain design** (see "2026-08-11
      update" above) across the writer (`manifest_finalize.py`, `partitioned_writer.py`, `tardis_cefi_shards.py`), the
      manifest schema, and any downstream reader/pre-flight-skip-check keyed on the old fake instrument_id or the
      `combo` string — both TradFi and CEFI (CEFI's Deribit multi-expiry wrapper is the direct `combo` string
      collision). Migrate existing historical manifest rows written under the old convention. Repos:
      market-tick-data-service, unified-api-contracts.
- [ ] [DATA] P2. **(NEW 2026-08-11) Scope the `lifecycle_phase` null-vs-string dtype drift** — confirm whether it's
      isolated to the combo/futures_chain path split or systemic across historical write eras; fix at the writer if
      systemic. Repo: market-tick-data-service.
- [ ] [DATA] P2. **(NEW 2026-08-11) Scope the `underlying` naming-convention inconsistency** (exchange-root short codes
      vs display names vs currency-pair style, differing between combo/ and futures_chain/) — decide one canonical
      naming convention per axis and migrate. Repos: market-tick-data-service, unified-api-contracts.
- [ ] [DATA] P2. **(NEW 2026-08-11) Re-verify whether ES_OPT/options_chain rows hit the same real-captured-row-vs-
      EXPECTED_CHAIN_AGGREGATE-denominator conflict** found for futures_chain/GOLD — not yet directly checked against
      the blank-instrument_id expectation. Repo: market-tick-data-service.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (1 entries).
- **context-scout 2026-08-03**: re-verified context_scope, unchanged (6 entries) — all todos closed, remaining work
  already cross-linked via the casing-redrift and delete-safety entries already listed.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **2026-08-11 (interactive session)**: Investigating the 2026-08-10 TradFi manifest `source=` write-failure blast
  radius (`tradfi_vix_backfill_launch_failed_2026_08_10.md`) surfaced a live GCS path collision between
  `instrument_type=combo/underlying=GC` and `instrument_type=futures_chain/underlying=GOLD` for day=2020-01-06. Traced
  root cause to this doc's own now-superseded "Combo → chain-bundle" default (2026-07-19) never having been shipped in
  the writer, and `migrate_tradfi_canonical_2026_07.py` still encoding it — producing genuine orphaned duplicate GCS
  objects (bare-form + quote/margin-form for the same combo cell). Operator resolved the semantics in-session: combo→
  `combo_chain` rename, blank `instrument_id` for all three chain-bundle grouping types, `instrument_type` accepted as
  dual-meaning for grouping rows. Also found: `lifecycle_phase` column dtype drift (string vs null) between the two
  paths, and an `underlying` naming-convention inconsistency (short exchange codes vs display names vs FX-pair style)
  co-existing in `combo/` for the same date. See "2026-08-11 update" section above for full detail; 6 new todos filed.
  Per operator instruction, no backfill relaunches or migrations execute until these todos are actioned.
