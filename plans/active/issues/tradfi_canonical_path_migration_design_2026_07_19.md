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
priority: P0
parent_epic: tradfi_master
source: "Full physical GCS enumeration (bny7k1yk6) + investigation workflow (wlixucotm), 2026-07-19"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
locked_by: live-defi-rollout
locked_since: 2026-05-21
assigned_vm:
resolved_by:
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

- **Combo** → chain-bundle (matches W1 `_UNDERLYING_PARTITIONED_TYPES` + cefi). Operator ruling named futures/options;
  combo is the same bundling class.
- **`underlying=12/13/23` garbage** → quarantine loudly; separate pre-existing defect (88% Databento). Own issue doc.
- **Catalogue MVP-stamping already exists** (`catalog.parquet` `mvp: bool` from UAC `is_mvp()`, config v18; out-of-MVP =
  legitimate absence, never a gap). Action = re-run `build_instrument_catalogue.py --asset-group tradfi` post-migration.
  Flag: tradfi MVP scope is deliberately narrow (CME ES/NQ/commodity + `TRADFI_EQUITY_PERP_BASIS_UNIVERSE` only); most
  of the ~622 SP500/NASDAQ/ETF tickers tag `mvp=False` by design — broadening needs a `MVP_SCOPE` rule edit + version
  bump.

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
