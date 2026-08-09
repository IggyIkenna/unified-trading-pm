---
doc_type: issue
title: CeFi residual follow-ups after honest-done close-out (non-Tardis, operator-deferred)
summary:
  The CeFi completion program was CLOSED at honest-done on 2026-07-17 (operator accepted current coverage 50.79% against
  a COMPLETE denominator; the 2.89M-cell tick gap is honestly-labelled expected_unattempted, not closable at the N=1
  Tardis throughput ceiling). This doc migrates the genuine NON-Tardis residuals that outlive that plan so they stay
  visible — none block the accepted deliverable; each is a discrete, independently-pickup-able follow-up. The Tardis-cap
  backfill work (WS A/B/F/G-tick + af=0 census + ConnectionTimeout diagnosis) is NOT here — it was superseded by the
  operator accept-decision, not deferred.
status: open
nature: issue
asset_group: [cefi]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    deployment-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    cefi,
    honest-coverage,
    residual,
    hyperliquid,
    phantom,
    eu-twin,
    consolidator,
    follow-up,
    canonical-completeness,
    filename-migration,
    content-backfill,
    reader-bridge,
    venue-decomposition,
  ]
related:
  [
    /plans/archive/2026_07/cefi_completion_program_2026_07_15.md,
    /plans/active/issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md,
    /plans/archive/issues/cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md,
    /plans/archive/issues/phantom_captures_cefi_2026_06_28.md,
  ]
created: 2026-07-17
author: unknown
last_updated: 2026-07-30
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 6.0
estimate_calibrated_ai_days: 4.8
assigned_role: data
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: CeFi completion program /autonomous close-out (slot-3, 2026-07-17) — archival ritual step 1 (migrate DEFERRED)
resolved_by:
context_scope:
  [
    /plans/active/issues/_cefi_canonical_blueprint_2026_07_17.md,
    /plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md,
    /codex/02-data/per-asset-group-bucket-layouts.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    market-tick-data-service/market_tick_data_service/engine/cefi_catalog_reader.py,
    deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh,
  ]
---

# CeFi residual follow-ups after honest-done close-out

> **Context**: `plans/archive/2026_07/cefi_completion_program_2026_07_15.md` closed at honest-done on 2026-07-17 —
> operator chose **accept current coverage** (50.79%, denominator COMPLETE, the 2,892,108-cell gap honestly-labelled
> `expected_unattempted`). The full 2026-02..07 tick backfill is not closable at the N=1 Tardis throughput ceiling (~186
> cells/hr ≈ 1.8 years; N=3 = ~94% 403s; US region ruled out on egress). Everything achievable inside that ceiling
> shipped. The items below are the genuine **NON-Tardis** residuals — none block the accepted deliverable; each is a
> discrete, independently-pickup-able follow-up. Filed as archival-ritual step 1 (migrate DEFERRED) so they survive the
> plan archive.

## Residuals (all NON-Tardis — not subject to the accepted ceiling)

1. **[P2] HYPERLIQUID recent-tail fill (~2026-06-24 → now-2).** HL is a DEX venue (non-Tardis, exempt from the N=1 cap)
   so its tail IS fillable — it was simply not run before the close-out. Fill via the HL batch lane (not the Tardis
   fleet). Detail: `cefi_hl_aster_batch_data_gaps_2026_06_22.md`. Evidence on pickup: manifest rows for HL over the tail
   range. **Status (2026-07-27, `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`): IN PROGRESS, not yet closed** — VM
   `cefi-hyperliquid-2026-20260727-150820` launched + verified genuinely healthy (real advancing manifest writes, no
   fire-and-forget); slot-5's `/done` on the batch1 todo was correctly hard-rejected by the AO server's M3 gate since
   `expected_unattempted`→0 was not yet reached. See the 3 Progress Log entries below (2026-07-27,
   slot-6/slot-11/slot-5) for the measured before/after counts — genuinely still open, do not re-flip without a fresh
   `expected_unattempted=0` measurement.

2. **[P2] HYPERLIQUID phantom re-census (1,277 rows → `@LIN` canonical path).** Cosmetic manifest-labelling — does NOT
   affect captured data. Blocked only on box size: the re-census (`reconcile_phantom_manifest_rows_all.py`) OOMs on the
   15GB VM; needs a 32-64GB box. Detail: `phantom_captures_cefi_2026_06_28.md`. Evidence: phantom count → 0 for HL. —
   **DONE 2026-07-27 (slot-2, `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`), root cause = box size.** Extended
   `launch-defi-phantom-recon-vm.sh` (`deployment-service@369c1e3`: `MACHINE_TYPE`/`VENUES` + SPOT); ran
   `defi-phantom-recon-cefi-20260727-173241` (`e2-highmem-4`, HL-scoped, `--apply`): `Real captures: 104153`,
   `Phantom captures: 0`. Re-verified via fresh `_index/phantom_audit_latest.json` (`phantom_count: 0`) — live manifest,
   not exit code.

3. **[P1] Drop eu twins of natively-canonical (non-Tardis) captures — ~10,368 rows (⚠️ superseded estimate, see
   correction below).** The OnchainPerp/native-canonical lane writes canonical `captured` rows but nothing drops the
   matching `expected_unattempted` twin, so the relabel gate is RED on these and its reconcile structurally cannot fix
   them (it only reconciles its own relabels). This is a pre-existing defect, independent of the Tardis ceiling.
   Detail + namespace root cause: `cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md`. Fix: a
   targeted eu-twin drop keyed on `(venue, data_type, day)` where a canonical `captured` twin exists.

   > **Correction (2026-07-25, plan-reconcile finding).** The `~10,368` figure (incl. `518 PACIFICA-SOLANA`) is the
   > pre-measurement blueprint ESTIMATE. It is superseded by the Canonical-completeness program's own Script-4 dry-run
   > (Phase C, 2026-07-18, run against live prod — see history doc §Progress Log), which measured the actual count:
   > **9,850 drops** — EXTENDED-STARKNET 9,817 + DERIBIT 24 + OKX-FUTURES 9, **no PACIFICA-SOLANA twins present live**.
   > Use 9,850 as the authoritative pending count; the fix (Phase 1 "Close residual #3" todo below) still needs
   > `--apply`.

4. **[P3] Manifest consolidator lost-update redeploy — watch item, likely unnecessary.** The maintenance-window
   durability fix (purging `_legacy_seed.parquet` so aliases can't re-merge) held across the resumed consolidator +
   backfill for ~70 min, verified 3×. The CAS lost-update race is documented in
   `manifest_consolidator_cas_retry_lost_update_race_2026_07_08.md`; redeploy only if a future purge fails to stick.

## Not here (superseded, not deferred)

The Tardis-cap backfill work — WS **A** (recent-tail main-venue backfill), **B** (403 re-capture + af=0 census), **F**
(DERIBIT-COMBO historical `by_date`), **G-tick** (equity-perp tick download), the **final `af=0`/`eu=0` recompute**, and
the **ConnectionTimeout-storm diagnosis** — is **superseded by the operator accept-decision (2026-07-17)**, not
deferred. It is only pursuable if the operator later revisits the Tardis licence/scope decision. Do not re-file it as
open work.

---

# Canonical-completeness program (2026-07-17 audit + operator decisions)

> **🟡 In-flight refactor + upcoming GCS cutover.** This program makes cefi tick data canonical across ALL FOUR surfaces
> (filename, parquet `instrument_id` column, manifest key, reader resolution). It includes a corpus-wide parquet-content
> rewrite + a Tardis-lane GCS object rename, both **drain-gated** (stop live cefi writers before cutover). Any agent
> touching cefi MTDS write/read paths, the cefi manifest, or launching cefi VMs must read this section first.

**Provenance.** Two adversarially-verified audit workflows (2026-07-17, slot-3) triggered by the operator spotting a
raw-wire filename
`gs://market-data-tick-cefi-prd-central-element-323112/…/venue=BITFINEX-FUTURES/…/data_type=trades/ADAF0:USTF0.parquet`.
Findings re-confirmed against the **live** 207MB `_index/availability_index.parquet` and real parquet samples (not
docs).

## The four surfaces + verified state (2026-07-17)

| Surface                                | Rule today                                                                                          | Verified current state                                                                                                                                      | Verdict                          |
| -------------------------------------- | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| **(A) GCS filename**                   | raw wire, by current design (`_file_stem_for` → `row["symbol"]`)                                    | MIXED corpus-wide: on-chain lane renamed to canonical (~134,855 objects); Tardis lane still raw wire                                                        | migrate → canonical (decision 3) |
| **(B) parquet `instrument_id` column** | `derive_row_instrument_id`, canonical only for the 6 `MARGIN_MARKER_VENUES`                         | column PRESENT everywhere (0 nulls sampled) but FORMAT canonical only on recent margin-marker writes; 3 non-canonical classes on disk                       | **Q2 = PARTIAL**                 |
| **(C) manifest `instrument_id` key**   | codex MANDATES canonical (`== InstrumentRecord.instrument_key`)                                     | live index: **84.44% canonical / 15.56% (490,492) raw-or-blank**; relabel ran 2026-07-16 (82.6%); raw remainder includes ACTIVE majors + double-keyed forms | **Q3 = NO**                      |
| **(D) reader resolution**              | no cefi wire→canonical bridge (only renormalizer is TRADFI-only, `canonical_writer_shaping.py:259`) | bulk full-shard reads robust; narrow per-instrument lookups + column↔catalogue joins **silently drop/mis-resolve** cefi instruments                         | **Q1 = PARTIAL**                 |

**The 3 non-canonical parquet-content classes (B):** (1) historical margin-marker undecomposed
(`BINANCE-FUTURES:PERPETUAL:BTCUSDT`, 2022 files — the `migrate_cefi_dated_perps_margin_marker_2026_07_09.py` content
patch was written but **never `--apply`'d**, backup prefix absent from bucket); (2) all non-margin venues wrapped-wire
(`BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0`) by current design; (3) on-chain historical backfill (canonical
filename+manifest but raw content `BTC-PERP` — the on-chain migration renamed objects + rewrote the manifest, not the
tick bytes).

**Manifest raw remainder (C) is NOT purely delisted debris:** dominated by BYBIT (278,427), OKX-FUTURES (116,742),
OKX-SWAP (21,403), BINANCE-FUTURES (16,272) — includes ACTIVE majors (BYBIT `BTCUSDT`/`ETHUSDT`) left raw by the
relabel's 297-ambiguous-pair exclusion. Plus live double-keying: same instrument under `…:BTC-USDT@LIN` (137,985) +
`…:BTC-USDT` no-marker (221,388) + bare-wire — these do not join. Residual #3 (10,368-row eu-twin) still OPEN.

## Operator decisions (2026-07-17, AskUserQuestion)

1. **Execution:** in-session workflows; track here in this doc (no new AO-dispatched plan). `assigned_vm: NA` retained.
2. **Prod mutations:** autonomous execution AUTHORIZED (snapshot-first, before/after row-count verified, reported).
3. **Filenames:** MIGRATE the Tardis lane to canonical (execute the 2026-07-08 deferred "last stage").
4. **Venue decomposition:** DECOMPOSE ALL cefi venues (not just the 6 margin-marker) — true canonical everywhere.

## Unifying architecture — catalogue-backed `(venue, raw_symbol) → instrument_key`

The instruments-service catalogue (`gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`)
**already fully decomposes every venue** (`BITFINEX-FUTURES:PERPETUAL:AMP-USDT`, `raw_symbol=AMPF0:USTF0`). So
"decompose all venues" is NOT hand-rolling 18 per-venue parsers — it is making the writer, parquet content, filename,
and manifest all key off the catalogue's proven map (the same mechanism the 2026-07-16 manifest relabel used). MTDS
reads the catalogue as DATA via `CeFiCatalogReader` (no service↔service import). The 297 ambiguous `(venue, raw_symbol)`
pairs stay honest-unresolved (reported, never guessed).

> **⚠️ REDESIGN (2026-07-17, blueprint workflow).** The adversarial design review returned `NEEDS-REDESIGN` and caught
> **5 data-corruption risks** in the naive plan — chiefly that a 2-tuple `(venue, raw_symbol)` key silently
> under-resolves the BYBIT/OKX/BINANCE-FUTURES majors (spot vs perp wire clash) into NON-JOINING ids. The corrected,
> apply-ready blueprint is `_cefi_canonical_blueprint_2026_07_17.md`. **Binding contract changes on every todo below:**
> (1) ONE **3-tuple** key `(venue, instrument_type, raw_symbol)→instrument_id` via ONE shared builder; (2) filename stem
> = the FULL canonical `instrument_id` (matches on-chain precedent — NOT the bare symbol; codex "bare symbol" docs are
> stale → Phase 2); (3) shard atom = `[date, venue, data_type, instrument_type, instrument_id, pipeline_mode]`; (4)
> **fail-loud** on empty/unreachable catalogue (never silently disable decomposition); (5) the D3 reader bridge must
> deploy to EVERY narrow-read consumer before the D4 GCS cutover. Do NOT run any `--apply` until blocker open-questions
> #1–#5 + the Phase -1 catalogue gate are green (blueprint §4).

## Phase -1 — Catalogue rebuild + verify gate (prerequisite of Phase-0 DEPLOY; everything keys off it)

- [x] ✅ [SCRIPT] P0. **Rebuild + verify the cefi reference catalogue — CODE FIX LANDED; prod rebuild is the
      orchestrator's next step.** — instruments-service@517b817b + evidence. Both gate defects diagnosed to `file:line`
      and FIXED at the true source, with the fix proven against REAL live data (909 legacy `by_date` rows → GATE 1 = 0
      `:PERP:`, GATE 2 = 0 drift, both PASS) + 16 new unit tests end-to-end through `build_catalogue_dataframe` carrying
      the exact live defect rows as fixtures. QG green (4417 passed, coverage 88.97%). **GATE 1 root cause was on-disk
      LEGACY data, NOT the adapter** — so a plain rebuild would NOT have fixed it (see Progress Log). **Remaining for
      the orchestrator**: run the prod rebuild (command in the Progress Log), then re-run the gate; the two REMEASURE
      sub-items below are carried forward as their own todos since they need the rebuilt catalogue. (repo:
      instruments-service)
- [x] ✅ [SCRIPT] P0. **Re-measure the single honest-unresolved number off the REBUILT catalogue** — DONE 2026-07-17
      (slot-3). **The ONE number is `439`** (pinned 3-tuple `(venue, instrument_type, raw_symbol)`), measured on the
      REBUILT live `prod/catalog.parquet` (425,161 rows, promoted 13:17:59Z) — **unchanged from the pre-rebuild 439**,
      which is the correct outcome: the 9 `:PERP:` rows were delisted perps, not ambiguous keys, so fixing them cannot
      move the ambiguity count. Independently corroborated from two different code paths (orchestrator pandas cross-tab
      AND the shipped `cefi_wire_bridge.get_cefi_wire_map()` → "439 ambiguous excluded"). Supersedes the divergent
      297/777/781 figures everywhere (blueprint open-q #7 CLOSED). (repo: instruments-service)
- [x] ✅ [SCRIPT] P1. **Sample OPTION / dated-FUTURE `raw_symbol` coverage on the REBUILT catalogue** — DONE via the
      Phase-−1 gate (`instruments-service@scripts/gate_cefi_catalogue_canonical_phase_minus1_2026_07_18.py`, ran GREEN
      2026-07-18 on the rebuilt 425,573-row `prod/catalog.parquet`). Open-q #14 ("decompose ALL types") PROVEN: OPTION
      **264,122** rows decompose per-strike/per-expiry (`BTC-5APR19-3250-C` →
      `DERIBIT:OPTION:BTC-USD@INV-20190405-3250-C`), dated-FUTURE **9,091** decompose per-expiry (`adausd_200925` →
      `BINANCE-DELIVERY:FUTURE:ADA-USD@INV-20200926`); PERPETUAL 5,411 / SPOT_PAIR 8,405. All quote-bearing (gate's
      0-missing-quote assertion). (repo: instruments-service)
- [ ] [SCRIPT] P2. **586 marker-less `VENUE:PERPETUAL:BASE-QUOTE` catalogue rows** (blueprint open-q #19, measured
      2026-07-17: BITGET-FUTURES 275 / BINANCE-FUTURES 153 / COINBASE-FUTURES 107 / BINANCE-DELIVERY 27 /
      BITFINEX-FUTURES 16 / OKX-SWAP 5 / BYBIT 3 — NOT just the 16 BITFINEX rows the blueprint recorded). Deliberately
      OUT of scope of the Phase -1 fix (the gate is `0` `:PERP:`, not `0` marker-less) — rewriting them is a 586-row
      blast radius that needs its own decision + drain. (repo: instruments-service)

## Phase 0a — Contract locks (design lock, before any code)

- [x] ✅ [DOCS] P0. **Lock the two contracts**: single-instrument cefi filename stem = FULL `instrument_id`; shard atom
      WITH `pipeline_mode`. The contradicting codex docs get corrected in Phase 2, but the form is byte-locked now so
      writer/migration/reader agree. (repo: unified-trading-pm) **→ MERGED INTO Phase-2 §445 (2026-07-18, /autonomous
      sequencing decision):** the "lock BEFORE code" purpose is now moot — the writer (D2), all 4 migration scripts, and
      the reader bridge (D3) are already written AND dry-run/gate-proven to agree (rename dry-run stems = FULL
      `instrument_id` e.g. `BINANCE-FUTURES:PERPETUAL:ADA-USDT@LIN.parquet`; Script-3 dedup on the pinned 6-col
      `pipeline_mode`-bearing atom). Both contracts live in the SAME two docs §445 reconciles
      (`per-asset-group-bucket-layouts.md` filename split + `availability-manifest-and-data-status.md` shard atom), so
      locking now + reconciling later = double-editing with drift risk. Doing them TOGETHER post-apply (when the final
      on-disk shapes are proven) is strictly better. The forms are already correct in code; this is a docs-consistency
      lock, not a code gate. **The single-instrument-stem vs aggregated-`underlying={U}/ticks.parquet`-bundle split MUST
      be stated explicitly** (the migration only renames single-instrument files; futures_chain/options_chain bundles
      keep `ticks.parquet`). **CLOSED 2026-08-04 (na-eligibility-audit)**: the merge target, Phase 2's "Resolve the
      codex↔plan SSOT contradictions" item below, is itself `[x]` DONE (`unified-trading-pm@8e435b425`, both cited docs
      — `per-asset-group-bucket-layouts.md` + `availability-manifest-and-data-status.md` — fixed) — nothing left for
      this item to gate.

## Phase 0b — Code fixes (MUST land + DEPLOY to every writer AND every narrow-read consumer before any corpus rewrite)

- [x] ✅ [BACKEND] P0. **FIX 0 — ONE shared 3-tuple builder** `CeFiCatalogReader.build_raw_symbol_map()` (3-tuple, reads
      `instrument_id` NOT `canonical_instrument_id`, excludes ambiguous, fail-loud on empty) + UAC
      `CeFiWireCanonicalMap` (pure, fwd + reverse maps). Single source everything else consumes. (repos:
      market-tick-data-service, unified-api-contracts)
  - ✅ **UAC half DONE — `unified-api-contracts@825878f7`.** NEW pure/pandas-free/no-I/O
    `unified_api_contracts/canonical/domain/cefi_wire_canonical.py`; exported from the package root `__all__` (the
    public surface — deep paths are UAC-internal). API: `CeFiWireCanonicalMap.from_rows(rows)` (constructor named
    **`from_rows`**, NOT the blueprint's provisional `from_triples` — the KEY is a 3-tuple but each input row is a
    4-quad `(venue, instrument_type, raw_symbol, instrument_key)`, so `from_triples` misnames the input; blueprint § 2
    FIX 0 explicitly delegated this naming choice) + `canonical_for(venue, instrument_type, raw_symbol) -> str | None`
    - `raw_symbol_for(venue, instrument_key) -> str | None` + public fields `canonical_by_wire` (fwd) /
      `wire_by_canonical` (rev) / `ambiguous_wire_keys`. **Evidence**: full `bash scripts/quality-gates.sh` GREEN (exit
      0, 342s, `.qg_last_passed_sha` written) — 21/21 new tests pass, basedpyright 0 errors/0 warnings, no
      `Any`/`# type: ignore`/`os.getenv`. Regression guard for the WHOLE program is asserted
      (`test_both_bybit_rows_resolve_neither_excluded`): BOTH BYBIT `BTCUSDT` rows resolve by `instrument_type`, NEITHER
      excluded. **MTDS half (`build_raw_symbol_map()`) still OPEN** — parallel agent; do not tick this box until it
      lands.
  - ✅ **MTDS half DONE — `market-tick-data-service@d302f07a`.** `CeFiCatalogReader.build_wire_map()` (+ the
    `build_raw_symbol_map()` `(map, excluded)` projection the writer's hot path consumes) on the cached full-lifecycle
    frame — no MVP gate / no active-date filter, so a DELISTED instrument still resolves at backfill write time; reads
    `instrument_id`, never the `canonical_instrument_id` trap; memoised (catalogue downloaded ONCE). **Decision: the
    exclusion/normalisation loop DELEGATES to UAC `from_rows` rather than being re-implemented locally** — the blueprint
    sketched a local conflict loop, but UAC's `from_rows` already implements byte-identical semantics, so a second copy
    would be the exact duplicate the "ONE BUILDER" rule exists to delete (and any drift between the copies would
    silently split the writer's honest-unresolved set from the reader's). `build_raw_symbol_map()` is therefore a
    projection (`resolve_map is wire_map.canonical_by_wire`), asserted by test. **Evidence**: 14 tests incl.
    `test_both_bybit_rows_resolve_by_instrument_type_neither_excluded` (the 3-tuple majors proof) + fail-loud on
    absent/empty/column-missing.
- [x] ✅ [BACKEND] P0. **FIX D1 — Writer decompose ALL venues (3-tuple).** One insertion point in
      `derive_row_instrument_id` (`tardis_shared.py:455`) resolving via FIX-0; covers the Tardis parquet column AND
      manifest key (both flow through it — zero change to cap-critical `venue_fetch.py`). Miss → honest fallthrough.
      (repo: market-tick-data-service) — **`market-tick-data-service@d302f07a`**. NEW leaf
      `market_interface/adapters/cefi/catalog_id_resolver.py` (process-global register/resolve + bounded, deduped
      per-venue miss accounting, `_SAMPLE_CAP=32`); registration in `engine/orchestrator/catalog_registration.py`; miss
      WARNING wired into `manifest_finalize.py`. **The blueprint's "ZERO change to `venue_fetch.py`" claim HELD —
      VERIFIED, not assumed**: `_canonicalize_manifest_instrument_id` (`venue_fetch.py:386`) calls the SAME
      `derive_row_instrument_id` with the SAME `instrument_type`, so column == manifest by construction;
      `venue_fetch.py` (898/900, cap-critical) is untouched. Proven by
      `test_manifest_key_is_byte_identical_to_the_parquet_column`, not by inspection. **Evidence**: 18 tests incl. the
      BYBIT spot-vs-perp disambiguation, shard-atom identity, and the disabled-by-default byte-identity guard
      (parametrised over the shapes the ~30 pre-existing assertions rely on).
- [x] ✅ [BACKEND] P0. **FIX D1-live — Live/on-chain COLUMN decomposition** in `PartitionedTickWriter.write_chunk` (the
      live consolidated + on-chain lanes never call `derive_row_instrument_id`; without this, live cefi columns stay
      non-canonical → batch≠live, ε=0 spine broken). Same shared map. (repo: market-tick-data-service) —
      **`market-tick-data-service@d302f07a`**. NEW `engine/cefi_wire_bridge.py` `get_cefi_wire_map()` (process-cached;
      D3 reuses it) + `_normalize_cefi_instrument_id_column()` in `_prepare_write_df`. **Verified the premise**:
      `finalise_rows_and_path`'s only prod callers are `tardis_cefi_shards.py` (Tardis lane) — the on-chain lanes
      (`_umi_hyperliquid`/`_umi_extended`/`_umi_lighter`) do go via `write_chunk`, exactly as the blueprint said.
      Resolves once per unique `(instrument_type, symbol)` pair, not per row. Miss → cell left EXACTLY as stamped;
      `None` map → frame untouched. Only normalises an EXISTING column (never invents one). **Evidence**: 10 tests
      (on-chain `BTC-PERP` → canonical, wrapped-wire → canonical, batch==live for both BYBIT majors, non-cefi
      untouched).
- [x] ✅ [BACKEND] P0. **FIX D2 — Canonical FILENAME stem = full `instrument_id`.** `_file_stem_for` (cefi branch) +
      `partitioned_writer._resolve_file_symbol` (extend the prediction-only override to cefi). Reuses the column
      D1/D1-live made canonical; writer KEY/bookkeeping stay on bare symbol → shard atom unchanged. Chain bundles
      untouched. (repo: market-tick-data-service) — **`market-tick-data-service@d302f07a`**. Stem = the row's full
      canonical `instrument_id` (attached at `:792`, BEFORE the stem helper at `:798` → filename == column == manifest
      by construction); fail-loud on a missing/empty id (no silent placeholder filename). `:`/`@` survive unsanitized
      (asserted). CHAIN bundles + `is_derivative` `ticks.parquet` + tradfi's own `_file_stem_for` all UNCHANGED
      (asserted). **Shard atom UNCHANGED — asserted, not claimed**: `partition_counts` still keys on the sanitized BARE
      symbol (`test_shard_atom_unchanged_writer_key_stays_on_the_bare_symbol`). **Evidence**: 10 stem tests + 4 updated
      pre-existing path assertions (the OLD bare-symbol filename contract → the LOCKED full-id contract; these 4 are the
      intended contract change, not a regression).
- [x] ✅ [BACKEND] P0. **FIX D3 — Reader wire↔canonical bridge (3-tuple; fixes audited silent data-loss).**
      Candidate-stems (canonical + reverse-map wire) in MTDS `reader.py:341`; drop the wire `("symbol","==",id)`
      pushdown (`:388`); normalize-on-read the column via the forward 3-tuple map; MDPS `path_parsing.py` accept both
      stems; rename + widen the TRADFI-only `canonical_writer_shaping.py:259` renormalizer to cover cefi. Handles the
      MIXED-corpus interim. (repos: market-tick-data-service, market-data-processing-service, unified-api-contracts) —
      **BOTH halves shipped: MDPS `market-data-processing-service@0035f79` + MTDS `market-tick-data-service@0388e1a9`.**
  - ✅ **MDPS half DONE — `market-data-processing-service@0035f79`.** NEW `app/utils/cefi_wire_bridge.py`: module-level
    `get_cefi_wire_map() -> CeFiWireCanonicalMap | None`, process-cached with a loaded-flag (a `None` is never
    re-probed); bucket via `resolve_bucket_name(kind="instruments-store", asset_group="cefi")` mirroring
    `dependency_checker.py`; probes `prod/`→`staging/`→`dev/` `catalog.parquet`; reads ONLY the 4 columns
    `venue, instrument_type, raw_symbol, instrument_id` (**never `canonical_instrument_id`**) and feeds UAC `from_rows`.
    `path_parsing.py` — new `blob_matches_canonical_instrument_id_stems()` accepts, for a **cefi** id
    (`VENUE_TO_ASSET_GROUP` gated), stem ∈
    `{canonical symbol segment, full instrument_id, raw_symbol, raw_symbol.upper()}` after the unchanged
    `venue=`/`instrument_type=` axis checks; **non-cefi keeps the single `/{symbol}.parquet` rule** and the DEFAULT
    full-shard path (`instrument_ids=None`) is untouched. `canonical_writer_shaping.py` — RENAMED
    `_renormalize_legacy_tradfi_instrument_ids` → `_renormalize_legacy_instrument_ids` (**no shim**; `__all__` + call
    site updated). **Open-q #17 RESOLVED: no external importer** — grep across the whole workspace found only in-repo
    MDPS files (`canonical_writer.py` + 2 test modules), so the rename was safe. tradfi branch kept intact (extracted
    verbatim to `_renormalize_legacy_tradfi`); new cefi branch tries BOTH the `split(":", 2)` tail (wrapped-wire
    `…:PERPETUAL:ADAF0:USTF0` → `ADAF0:USTF0`) and the whole string (bare on-chain `BTC-PERP`), recovers
    `instrument_type` via the existing `_infer_instrument_type`, then `canonical_for(...)`; unresolved/ambiguous rows
    left **UNCHANGED** (honest-unresolved, never guessed). **Decisions made alone**: (1) **fail-SOFT to `None`** (not
    the writer's fail-loud) — MDPS's consumers are READ-side aids, so a `None` degrades them to exact pre-bridge
    behaviour with no corruption, whereas raising would take down the scanner including the default full-shard path that
    never uses the map; every failure still logs WARNING. (2) An EMPTY forward map is reported as unavailable (`None`)
    rather than handed over as a map resolving nothing. (3) `bucket_arg_typing` is imported **function-level**
    (`noqa: PLC0415`) — `app.core.__init__` → adapters → `app.utils` makes a module-scope `app.core` import a genuine
    circular import (caught by QG; 2 test modules ImportError'd). (4) Two pre-existing tests asserted CEFI was a
    renormalizer no-op — that is no longer true, so they were re-pointed at genuinely-unhandled groups (DEFI/SPORTS)
    instead of being left to pass incidentally on the map-is-`None` path. **Evidence**: full
    `bash scripts/quality-gates.sh` GREEN at the commit SHA (exit 0, **zero ❌** in the output — not just the exit code,
    218s, `.qg_last_passed_sha=0035f79` == HEAD), **2008 passed** / 1 skipped (26 new tests), coverage 85.42%,
    basedpyright 0 errors on all 5 touched files, no `Any`/`# type: ignore`/`os.getenv`/ inline `gs://`. Blueprint
    regression guards asserted: wire-named `ADAF0:USTF0.parquet` now matches `BITFINEX-FUTURES:PERPETUAL:ADA-USDT@LIN`
    (**the audited silent drop is closed**), canonical-named object matches too (mixed-corpus both-ways),
    wrong-venue/wrong-itype → False, and the **3-tuple majors** (BYBIT `BTCUSDT` SPOT_PAIR vs PERPETUAL) resolve to
    their correctly-typed ids AND do not cross-match. **Shipped via a dirty-deps carve-out direct push** — quickmerge
    pre-flight blocked on live foreign WIP in `unified-trading-library` + `unified-api-contracts` (other agents active;
    polled ~17 min, metric flat → their work left untouched).
  - ✅ **MTDS reader half DONE — `market-tick-data-service@0388e1a9`.** `reader.py` candidate-stems
    (`_cefi_candidate_stems`: canonical segment + reverse-map wire, both cases), the `symbol==id` pushdown dropped for
    cefi/prediction (`_NO_SYMBOL_PUSHDOWN_ASSET_GROUPS`), and normalize-on-read the `instrument_id` column via UAC
    `get_cefi_wire_map()`'s forward 3-tuple map (`_normalize_cefi_instrument_id`); fail-SOFT to `None` on absent
    catalogue, mirroring the MDPS read-side asymmetry. **Inherited under the liveness rule** — the originating agent
    went idle ~1.7h mid-final-run (no process, no QG, dead claim), its WIP was complete + passing its own 47 reader
    tests, so this slot inherited + landed it. **Also closed the two ungated-family blockers that gated the cutover**
    (the D3 work exposed `tests/market_interface/` was never collected): (1) bisected the 2
    `test_tardis_canonical_output.py` canonical-output failures to **PRE-EXISTING, not d302f07a** (identical at
    `d302f07a` vs `d302f07a^` in isolated PYTHONPATH-overridden worktrees) and fixed both against the prod contract (a
    stale Kraken `PF_XBTUSD`→`@INV` expectation vs the real linear marker; an inert bucket-resolver patch on a call site
    abandoned 2026-07-10 → rewritten to exercise the real `IS_TEST_RUN`-aware resolver) + 3 `download_batch`
    config-singleton isolation bugs; (2) gated the 3 cefi write-side files d302f07a shipped-but-never-ran in
    `scripts/quality-gates.sh` `PYTEST_UNIT_DIR`. **Evidence**: full `bash scripts/quality-gates.sh` GREEN (exit 0, ZERO
    ❌, **6162 passed** — up from the 6046 baseline that never moved despite 17 new D3 tests, which WAS the bug;
    `.qg_last_passed_sha` == HEAD). Shipped via **quickmerge** (deps clean; carries the `Quickmerge:` trailer →
    promotable, unlike the earlier carve-out ships). See
    `/plans/archive/issues/mtds_ungated_test_families_2026_07_17.md` for the residual 38 whole-tree failures — since
    fixed and the doc archived 2026-07-31 (all 5 todos done).
- [x] ✅ [BACKEND] P0. **FIX D-features — cefi reads (REQUIRED before cutover, not optional).** features
      `raw_data_loader.py`: inherit the D3 bridge (if it reads via MTDS `reader.py`) or add its own
      `get_cefi_wire_map()` bridge; reconcile the `instrument_id`↔`instrument_key` column-name mismatch. (repo:
      features-service) — **`features-service@efd3e038`**. **open-q #9 RESOLVED: features-service needs its OWN bridge —
      it does NOT read via MTDS `CanonicalParquetReader`** (measured: ZERO imports of it corpus-wide;
      `raw_data_loader.py` resolves a bucket via `resolve_bucket` and lists/downloads parquets itself). The onchain
      `adapters/mtds_canonical_reader.py` is `build_defi_partition_path`/`asset_group=defi` HARDCODED → never touches
      cefi. **But the change is NOT the blueprint's shape**: features does **no narrow per-instrument cefi reads** — its
      cefi read is a BULK day scan — so **candidate-stem matching is moot** (the D2/D4 rename cannot break a
      filename-agnostic scan). The real exposure is the **COLUMN**. NEW `cross_instrument/engine/cefi_wire_bridge.py`
      (catalogue as parquet DATA → UAC `from_rows`; fail-SOFT to `None` per the read-side asymmetry; process-cached
      loaded-flag; **no `PLC0415` noqa — features' ruff `select` has no `PL` family, so RUF100 would reject it**, unlike
      MDPS). `instrument_id` → `instrument_key` reconciled + cefi canonicalized via the forward 3-tuple map, keyed on
      venue/instrument_type from the **PATH** (the real trades schema carries `exchange`, no `instrument_type` column —
      content-only keying is impossible). Unresolved/ambiguous → on-disk id kept verbatim (honest); `map=None` →
      identical pre-bridge behaviour. **Evidence**: full `quality-gates.sh --no-fix` GREEN at the commit SHA (exit 0,
      **ZERO ❌ in the output**, 179s, 17665 passed, coverage 83.55%, `.qg_last_passed_sha` == HEAD); 30 new tests incl.
      the BYBIT 3-tuple majors guard (SPOT_PAIR vs PERPETUAL resolve to their correctly-typed ids and do not
      cross-match), a wire-filename fixture asserting **non-empty** rows + canonical join key end-to-end, and the
      `map=None` fallback. Shipped via the **dirty-deps carve-out direct push** (UAC + PM carried foreign WIP; UAC dep
      `825878f7` verified an ancestor of origin).
- [ ] [BACKEND] P1. **features raw feature groups cannot consume the REAL raw_tick schema (found 2026-07-17 during FIX
      D-features; NOT caused by this program, and NOT fixed by `features-service@efd3e038`).** The 5 raw groups
      (`book_depth_bands`, `liquidity_walls`, `liquidation_clusters`, `composite_sr`, `flow_interaction`) declare
      `required_columns = [timestamp, instrument_key, bids, asks, mid_price]` / `[…, side, quote_volume]`, and
      `base_calculator.validate_input` **raises `ValueError: Missing required columns`** on a miss. The real MTDS
      schema, measured on live prod objects (2025-06-15), carries **none of `bids` / `asks` / `mid_price` /
      `quote_volume`**: book is FLAT L5 (`bid_px_00..04`, `bid_sz_00..04`, `ask_px_00..04`, `ask_sz_00..04`, 29 cols)
      and trades carry `price` + `amount` (10 cols). The mock frames (`_make_mock_book_df`) were written to the
      CALCULATOR's contract, not to the writer's — so these groups have **never run against real data** and every
      existing test passes on mocks. `efd3e038` closes the join-key half (`instrument_key` now exists + is canonical);
      the shaping half needs a real decision, so it is NOT silently invented here: derive `mid_price` from
      `(bid_px_00+ask_px_00)/2`? nest the L5 columns into `bids`/`asks` list-of-[px,sz]? `quote_volume = price*amount`?
      Each is a feature-definition change (formula-hash / `/codex/02-data/feature-formula-versioning.md`), not a loader
      tweak. **Blast radius**: these 5 groups produce nothing today regardless of this program. (repo: features-service)
- [ ] [BACKEND] P2. **features raw cefi day-scan is unbounded (found 2026-07-17, `features-service@efd3e038`).** With
      the prefix fixed the loader now downloads EVERY matching parquet for a day and concatenates in memory; one
      HYPERLIQUID `book_snapshot_5` shard alone is 8.4 MB / 156,677 rows, so a whole cefi day across all venues is a
      plausible OOM. This was latent before (the broken prefix matched 0 objects, so it never downloaded anything).
      Bound the read by venue/instrument list or stream per-shard before these groups run for real. Sequenced AFTER the
      schema-gap todo above — the groups cannot consume the data until that lands. (repo: features-service)
- [x] ✅ [BACKEND] P0. **Enumerate the narrow-read consumers** — DONE 2026-07-17 (slot-3), measured. **IN SCOPE (4)**:
      MTDS `reader.py`; MDPS (`path_parsing.py` / `canonical_writer_shaping.py` / `orchestration_scanner.py` /
      `data_source.py`); features-service (`raw_data_loader.py` + cross-instrument `batch_handler.py`);
      **execution-service `algo_library/mtds_book_provider.py`** (narrow `read_shard(instrument_id=)` via
      `CanonicalParquetReader` → inherits D3, REDEPLOY REQUIRED — not named in the blueprint). **VERIFIED OUT (3)**:
      ml-service (0 `raw_tick` refs), batch-live-reconciliation-service (0 refs), strategy-service runtime
      (`asset_group="defi"` hardcoded). Evidence in the Progress Log.
- [x] [BACKEND] P0. **DEPLOY the reader bridge to all 4 in-scope consumers** — already covered by
      /plans/archive/issues/cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md todo 1 (see that doc for execution) —
      the D4 GCS cutover cannot run until every one carries it (the drain stops WRITERS only; readers keep running
      against renamed/rewritten objects). Includes an **execution-service redeploy** even though it needs no code
      change. (repos: market-tick-data-service, market-data-processing-service, features-service, execution-service) —
      **STILL OPEN (`cefi_satellite_ao_dispatch_batch2_2026_07_26.md` item -010 sub-item 1, slot-3, 2026-07-26)**:
      attempted from this worktree — infra-craft work (Cloud Run deploy), out of `backend_engineer` scope, and no Cloud
      Run services found for these 4 consumers from this worktree. Spun to a fresh dispatchable todo:
      `/plans/archive/issues/cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md` todo 1.
- [x] ✅ [INFRA] P1. **Fix the features-service image build — stale base-image UAC (non-cutover-blocking).** features'
      `6ab22c6` main build FAILS: `cefi_wire_bridge.py:59 import CeFiWireCanonicalMap` → ImportError, because features
      uses `uv pip install --no-sources` and relies on the UAC baked into its pinned `BASE_IMAGE_DIGEST`
      (unified-trading-library base image predates the symbol) — whereas MTDS/MDPS/execution COPY fresh UAC source and
      build clean. Fix = bump features' `BASE_IMAGE_DIGEST` to a base image with fresh UAC, OR switch features to
      COPY-fresh-UAC-source like its siblings. NOT a cutover blocker: features' cefi read is a filename-agnostic bulk
      day-scan, so the D2/D4 rename can't break it (found 2026-07-18, Phase-B deploy characterization; rebuild
      `5eb274fa` triggered to confirm). Adjacent: the UAC Artifact-Registry wheel is frozen at 0.72.0 (2026-06-27) —
      **ALREADY RESOLVED (`cefi_satellite_ao_dispatch_batch2_2026_07_26.md` item -010 sub-item 2, slot-3, 2026-07-26, no
      code change needed)**: the automated `update-dependency-version.yml` digest-refresh fan-out bumped
      `BASE_IMAGE_DIGEST` twice (`features-service@586a5cea`, `@8661a7af`); verified the latest `image-build-gate.yml`
      run on `8661a7af` is `conclusion: success`. irrelevant to these source/base-image consumers but a fleet-hygiene
      item for AR-wheel UAC consumers. (repo: features-service)
- [x] ✅ [SCRIPT] P1. **Fix the one campaign script our rename breaks** — **`strategy-service@26b99c69`** (2026-07-18).
      NEW pure helper `_leaf_matches_asset(leaf, asset_upper)` accepts BOTH the pre-migration wire stem
      (`BTCUSDT.parquet` / `PI_BTCUSD.parquet`) AND the post-D4-rename canonical stem
      (`VENUE:TYPE:BASE-QUOTE[@MARKER].parquet`, comparing the `-`-stripped BASE-QUOTE to the wire ticker), replacing
      the hardcoded wire-only leaf-match at `_load_tardis_day`. **Chose FIX not DELETE**: the Delete-when
      (`master_to_live_defi_2026_05_23 Phase D complete — live dispersion archetype running ≥7 days`) is NOT satisfied
      (that plan is still in `plans/active/`). Evidence: repo's own test file passes 12/12 incl. the new
      `test_leaf_matches_asset_accepts_wire_and_canonical_stems` (wire + canonical + non-match cases); ruff green;
      `scripts/` excluded from basedpyright; full QG exit 0 (its lone failure is the pre-existing, unrelated
      `test_golden_pre_trade_check_phase0_risk_eval` risk-eval fixture — NOT this change). `trace_carry_staked_basis.py`
      is a prefix scan → SAFE, no action. (repo: strategy-service)

## Phase 1 — Corpus migrations (scripted + dry-run first; `--apply` ONLY behind the Phase-1 drain, snapshot-first)

- [ ] [SCRIPT] P0. **Parquet CONTENT backfill (corpus-wide).** Canonicalize the frozen `instrument_id` column for all 3
      non-canonical classes: (a) historical margin-marker undecomposed — run the existing
      `migrate_cefi_dated_perps_margin_marker_2026_07_09.py --apply`; (b) all non-margin venues — extend it to
      catalogue-decompose; (c) on-chain historical raw-content (`BTC-PERP`→canonical). Snapshot-first to
      `_migration_backups/`. Do NOT re-fetch. (repo: market-tick-data-service) — **SCRIPT WRITTEN + dry-run-validated:
      `market-tick-data-service@ec04e8f5` (`scripts/migrate_cefi_content_instrument_id_catalogue_2026_07_17.py`); 12-day
      dry-run 7,270/12,662 files, all 3 classes resolve. `--apply` is Phase-E (operator-gated) — see the 2 pre-apply
      fixes below.** **STILL OPEN 2026-07-27
      (`/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` todo 3 execution)**: fresh
      corpus-wide discovery (10-shard, `--workers 24`) measured the TRUE scope for the first time — **≈4.5 MILLION
      files** (cs1=769 … cs10=1,226,258), ~2 orders of magnitude past the 12-day-sample estimate above. At measured
      throughput (~5-10 files/sec/VM, GCS-round-trip-bound) even a 10-VM parallel dry-run needs tens of hours; `--apply`
      was never attempted. Per-shard would-patch rates ranged ~0-90% (cs9 spiked to ~82-90%, unexplained — possibly
      aligned with the same 2025-10/11 LATE-window boundary other scripts use). Added `cefi-content-apply` launcher
      category (`deployment-service@8868a770`) since none existed. New follow-up needed: a dedicated 30-50+ VM,
      multi-hour-to-multi-day campaign (Script-2 scale or larger) — track as its own todo/plan, not a quick re-dispatch.
      (repo: market-tick-data-service, deployment-service) — **na-eligibility-audit 2026-08-07 citation fix**: this is
      genuinely in-flight, tracked in exhaustive detail in
      `plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md` (assigned_vm: planning, status:
      open — the active Script-1 corpus-content-backfill campaign; 44-shard fleet, multiple OOM/preemption/ freeze
      failure classes diagnosed+fixed, still not corpus-complete). This checkbox stays open here as the accounting
      record; do not reclassify this doc for it — flipping `assigned_vm` would dispatch a duplicate of already-active AO
      work.
- [x] ✅ [SCRIPT] P1. **SCRIPT-1 pre-`--apply` fixes** — **`market-tick-data-service@d47609ec`** (2026-07-18). (a) pool:
      `--workers` default lowered **32→12** to stop oversubscribing the size-10 urllib3 pool (`get_storage_client()`
      caches ONE pooled client per process shared by all worker threads; 32 > pool_maxsize=10 caused the ~27% transient
      `error` failures) — a dedicated VM MAY raise workers only in tandem with re-verifying `_GCS_HTTP_POOL_MAXSIZE`.
      (b) reporting: `errors = _stats.get("read_error",0) + _stats.get("error",0)` so the STOP line counts the driver's
      `error` outcome too (was printing `read_errors=0` while 3,380 files errored). QG green (6187 passed, exit 0).
      (repo: market-tick-data-service)
- [x] [SCRIPT] P2. **[already covered by /plans/archive/issues/cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md todo
      3, see that doc for execution]** Manifest `instrument_type` mislabel cleanup — OKX-FUTURES dated-futures tagged
      PERPETUAL (~116,742 rows).** The bulk of Script-3's 174,649 honest-unresolved main-index rows are OKX-FUTURES
      dated futures (`XRP-USD-240329` etc., mostly past-expiry delisted) whose manifest `instrument_type` is `PERPETUAL`
      while the catalogue has them as `FUTURE`, so the 3-tuple honestly misses. Correcting the manifest itype
      PERPETUAL→FUTURE for dated symbols would recover most of them. Separate data-quality task, NOT a cutover blocker
      (leaving them raw is the correct never-guess behaviour; they are delisted historical). (found 2026-07-18 Phase-C
      honest-unresolved audit.) (repo: instruments-service) — **STILL OPEN
      (`cefi_satellite_ao_dispatch_batch2_2026_07_26.md` item -010 sub-item 3, slot-3, 2026-07-26)**: the manifest
      row_key includes `instrument_type`, so a blind relabel can collide with an already-existing FUTURE row for the
      same shard atom — needs the same collision-aware dedup logic as
      `canonicalize_cefi_instrument_type_legacy_lowercase_2026_07_16.py`, not a blind in-place relabel. Spun to a fresh
      dispatchable todo: `/plans/archive/issues/cefi_batch2_010_misscoped_gated_bundle_2026_07_26.md` todo 3.
- [x] ✅ [SCRIPT] P0. **DONE (todo 2 of
      `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`, 2026-07-27). Filename rename
      (Tardis lane).** Rename single-instrument cefi objects wire→canonical, extending the proven
      `migrate_onchain_perp_perpetual_canonical_2026_07_08.py` pattern (GCS rename + manifest rewrite together).
      Snapshot-first; idempotent; per-day prefix batches (single-walk discipline). (repo: market-tick-data-service) —
      corpus-wide EARLY (2019-2025, 39,606 renamed) + LATE-window residual (3,227 renamed) applied via ~40 VM launches;
      ~5,001-object DERIBIT/ASTER/HYPERLIQUID collision residual left honest-raw (already-ruled accepted exception,
      separately tracked). Idempotency re-verified (0 further would-rename except the accepted residual).
- [x] ✅ [SCRIPT] P0. **DONE 2026-07-27
      (`/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` todo 3 execution). Manifest
      completion.** Resolve the ~490k raw captured rows — at minimum the ACTIVE majors (BYBIT/OKX/BINANCE-FUTURES) the
      2026-07-16 relabel's ambiguous-pair exclusion left raw — and de-duplicate the coexisting `…@LIN` / `…:BASE-QUOTE`
      / bare-wire key forms so each instrument maps to ONE canonical id. (repo: instruments-service) — Applied via
      `complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py --apply`
      (`canonical-migration-cefi-dedup-apply-20260727-043604`): wrote main index at 8,728,931 rows (itype_changed
      17,328, orphans-dropped 15, marker_added 48,032, eu-dropped 29,949, de-dup-collapsed 48,529), gate PASSED (0
      further-resolvable, 0 eu/captured collisions, 0 data-loss invariants). Fresh idempotency re-verify: ALL axes 0
      (relabeled/itype_changed/orphans/marker_added/eu-dropped/de-dup-collapsed/chain_lossy all 0), canonical-fraction
      stable 99.45%. Pre-apply STOP-ON-SURPRISE band (`_MARKER_MIN`) diagnosed + lowered with cited justification
      (`instruments-service@f06eba12989d`) after confirming the real 48,032 (vs. the stale 2026-07-20 baseline of 2.3M)
      is fully explained by Script 2's + other already-shipped manifest work this week.
- [x] ✅ [SCRIPT] P1. **DONE 2026-07-27
      (`/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` todo 3 execution). Close
      residual #3** — drop the eu-twin canonical collisions keyed on `(venue, data_type, day)` where a canonical
      `captured` twin exists. **Count corrected 2026-07-25**: the original `10,368` estimate (9,817 EXTENDED-STARKNET +
      518 PACIFICA-SOLANA + ~33) is superseded by the Script-4 dry-run's measured **9,850** (EXTENDED-STARKNET 9,817 +
      DERIBIT 24 + OKX-FUTURES 9, no PACIFICA-SOLANA twins present live) — see the residuals list correction above +
      history doc. Script-4 (`instruments-service@b61f9bdd`) is already written and dry-run clean; only `--apply`
      (behind the Phase-1 drain) remains. (repo: instruments-service) — **Fresh live re-measure found the real number
      had grown to 28,755** (HYPERLIQUID 28,748 / ASTER 5 / BITGET-FUTURES 2 — the interim 2026-07-17→27 HYPERLIQUID
      tail-fill backfill campaign materialized far more eu-twins than the stale 9,850 estimate), diagnosed as a real,
      structurally-safe (exact-key-match mechanism) volume increase, STOP-ON-SURPRISE band widened with cited
      justification (`instruments-service@8166676465f1`). Applied
      (`canonical-migration-cefi-eu-twin-apply-20260727-043653`): wrote 8,778,675 rows (was 8,807,430), gate PASSED,
      **28,755 rows dropped, 0 residual**. Idempotency re-verified (fresh dry-run: 0 further drops).
- [x] ✅ [INFRA] P0. **DONE 2026-07-27
      (`/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` todo 3 execution).
      Pre-migration drain + snapshot (GATES all Phase-1 `--apply`).** Stop ALL live cefi writers (Tardis
      `cefi-queue-*` + on-chain `cefi-*` VMs, both clouds), consolidate the manifest, snapshot the cefi bucket + index
      before any content-rewrite/rename cutover; re-enable writers only after apply + verify. HARD RULE: no GCS cutover
      with writers live. (repo: deployment-service) — Fresh-measured 7 live on-chain writers
      (`cefi-{aster,hyperliquid}-     {year}-20260727-022558`, Tardis `cefi-queue-*` = 0, AWS = 0); drained
      02:36:24Z-02:37:35Z; consolidator cron paused + one manual consolidation pass run; main index snapshotted
      (`_index/backups/availability_index.pre_d4_cutover_20260727T023846Z.parquet`). **Writers re-enabled + verified
      actually capturing** (not just instance RUNNING — confirmed fresh `collect-onchain-perp-batch` processes + log
      activity post-restart) 03:55:26Z-03:55:51Z; consolidator cron resumed ENABLED 03:55:17Z.

## Phase 2 — Docs + codex reconciliation

- [x] ✅ [DOCS] P1. **Resolve the codex↔plan SSOT contradictions** the audit surfaced:
      `chart-candle-delivery-flow.md:274` ("Filename is the bare symbol") → canonical target +
      SUPERSEDED/forward-pointer banner; `read-time-filter-pushdown.md` (filenames now canonical — update the
      substring-match assumption); `availability-manifest-and-data-status.md` "immutable wire-form contract" (superseded
      for the manifest key); `per-asset-group-bucket-layouts.md:135` (`ticks.parquet` vs per-instrument stem split).
      (repo: unified-trading-pm) — **DONE (`cefi_satellite_ao_dispatch_batch2_2026_07_26.md` item -010 sub-item 4,
      slot-3, 2026-07-26): `unified-trading-pm@8e435b425`** fixes `chart-candle-delivery-flow.md`,
      `per-asset-group-bucket-layouts.md`, `read-time-filter-pushdown.md` with SUPERSEDED/forward-pointer banners
      pointing at `cross-asset-canonical-target-ssot.md`. The 4th ("immutable wire-form contract") was not found
      verbatim in the current `availability-manifest-and-data-status.md` — already resolved or a mischaracterization; no
      edit needed.
- [ ] [DOCS] P1. **Progress Log at every gate** — each `--apply` records measured before/after row counts + coverage
      delta as evidence (per the runtime-verification HARD RULE). (repo: unified-trading-pm) — **na-eligibility-audit
      2026-08-07 citation fix**: gated on the same in-flight Script-1 campaign as the P0 item above
      (`plans/active/issues/cefi_content_migration_fleet_half_incomplete_2026_07_26.md`, assigned_vm: planning) — stays
      open here only until Script 1 finishes; not an independent duplicate-eligible item.

## Codex SSOTs (read before touching a phase)

`/codex/02-data/defi-canonical-naming-ssot.md`, `…/availability-manifest-and-data-status.md`,
`…/chart-candle-delivery-flow.md`, `/codex/06-coding-standards/read-time-filter-pushdown.md`,
`/codex/05-infrastructure/vm-launcher-runbook.md` (drain), `/codex/05-infrastructure/gcs-object-operations.md`.

## Progress Log

- **2026-07-18 (slot-3, /autonomous) — CUTOVER STAGED; drain+`--apply`+content GATED on a QUIET cefi fleet (a concurrent
  pipeline-check sweep is active).** Everything reversible is done + verified; only the irreversible core remains, and
  it needs a writer-free window.
  - **Reader-bridge (377) VERIFIED READY**: the D3 `CeFiWireCanonicalMap` bridge is on current `origin/main` for BOTH
    MTDS (`engine/cefi_wire_bridge.py`, `cefi_catalog_reader.py`, `partitioned_writer.py`,
    `market_interface/adapters/cefi/catalog_id_resolver.py`) and MDPS (`app/utils/cefi_wire_bridge.py`,
    `canonical_writer_shaping.py`, `path_parsing.py`). Consumers are batch/job workloads (pick up the image at next
    invocation, which is post-re-enable); features' read is filename-agnostic (rename can't break it); execution-service
    needs only a redeploy (non-trading → low risk). So readers survive the rename/rewrite.
  - **DRAIN BLOCKER (measured)**: `gcloud compute instances list … name~cefi status=RUNNING` = **2 VMs**, both from a
    concurrent PIPELINE-CHECK sweep — `instr-backfill-cefi-pchk-0718120011-f-<venue>` +
    `mtds-backfill-cefi-pipelinecheck- <ts>` (a fresh mtds-backfill launched every ~4 min; venue cycles
    okx-spot→deribit→…). AWS cefi = 0. The STANDING capture writers (Tardis `cefi-queue-*` / on-chain `cefi-*`) are
    already quiet — it is ONLY this concurrent sweep (another session running the `data-pipeline-check-mtds` skill) that
    is live. Draining it would be (a) interfering (not my operation) and (b) INEFFECTIVE — the controller relaunches
    per-venue writers that would then RACE my rename/content `--apply` (the exact hazard the drain exists to prevent).
    Per the drain HARD RULE ("no GCS cutover with writers live") the cutover WAITS for the sweep to finish (a
    fleet-quiet watcher is armed), then executes drain→snapshot→Scripts 2/3/4 `--apply`→re-enable→Script-1 content on a
    VM. **This is a fleet-coordination gate, not a code/data problem** — surfaced to the operator.

- **2026-07-25 — older Progress Log entries (2026-07-17/07-18 build narrative: blueprint workflow, Phase -1 catalogue
  rebuild + gate, Phase 0b write/reader-bridge ships, Phase C migration-script dry-runs, Phase A/B provenance + deploy
  characterization) EXTRACTED verbatim to
  `plans/archive/issues/cefi_residual_followups_after_honest_done_history_2026_07_25.md`** for
  `plans/active/issues/*.md` 1000-line hard-cap compliance (was 1151 lines; pattern per
  `plan_line_cap_remediation_2026_07_23.md` § FINAL RESOLUTION). The entry above (CUTOVER STAGED) is the most recent /
  current status and stays live here. **plan-reconcile contradiction check (2026-07-25)**: read the full
  Canonical-completeness program end-to-end looking for anything contradicting the "residual follow-ups" section's two
  claims — (1) the Tardis-cap backfill work (WS A/B/F/G-tick + af=0 census + ConnectionTimeout diagnosis) being
  superseded-not-deferred / "do not re-file it as open work", and (2) the "operator chose accept current coverage"
  framing. **No contradiction found on either claim** — the Canonical-completeness program is a genuinely separate,
  later-authorized initiative (its own 2026-07-17 `AskUserQuestion` operator decisions, four-surfaces canonical-FORMAT
  audit) about filename/parquet-content/manifest LABELLING, not about raw tick-capture coverage %; none of its ~30 todos
  or its Progress Log re-open WS A/B/F/G-tick or revisit the coverage-acceptance ruling (grepped corpus-wide within this
  doc for `Tardis-cap`, `WS A/B/F/G`, `af=0 census`, `ConnectionTimeout-storm`, `licence`, `N=1`/`N=3`,
  `throughput ceiling`, `denominator`, `50.79`, `2,892,108`, `expected_unattempted` — zero hits outside the residual
  section itself). The one genuine, evidence-backed discrepancy found nearby (not the flagged pair, but in-file so fixed
  same commit): residual #3's `~10,368`-row estimate (incl. 518 PACIFICA-SOLANA) is stale vs. the program's own Script-4
  dry-run measurement of **9,850** (no PACIFICA-SOLANA present) — corrected in the residuals list and the Phase-1 todo
  above.

- **2026-07-27 (Phase D/E drain + `--apply` executed — full detail in
  `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`'s own Progress Log, todo 3 entry;
  summarized here per this doc's own convention)**: Scripts 2 (filename rename), 3 (manifest dedup v2), and 4 (eu-twin
  drop) all **APPLIED + idempotency-verified live** — Script 3 wrote the main index to 8,728,931 rows (0 residual on
  every invariant), Script 4 dropped 28,755 eu-twin rows (0 residual), both re-confirmed via a fresh post-apply dry-run
  showing 0 further changes on every axis. Both scripts' STOP-ON-SURPRISE bands were stale (set 2026-07-17/20, before a
  week of intervening manifest work + an in-flight HYPERLIQUID backfill campaign) and were diagnosed + widened/ lowered
  with cited evidence, not blindly adjusted (`instruments-service@8166676465f1`, `instruments-service@f06eba12989d`).
  Drain executed on 7 freshly-measured live on-chain writer VMs (not in the 9-day-old snapshot this doc's Progress Log
  last recorded) — consolidator cron paused + one consolidation pass run + main index snapshotted before any mutation;
  writers re-enabled and VERIFIED actually capturing again post-apply; consolidator cron resumed. **Script 1 (parquet
  content backfill) is the one script NOT applied** — its true full-corpus scope was measured for the first time this
  session at ≈4.5 million files (vs. the 12-day-sample estimate this doc's own Phase-1 todo was written against), making
  it a dedicated 30-50+ VM, multi-hour-to-multi-day campaign in its own right, not completable inside this dispatch.
  This is the single biggest finding of the session — flagged here, in the main plan, and needs its own follow-up
  todo/plan before the 4-script migration can be called fully closed.

- **2026-07-27 (slot-6) — HYPERLIQUID recent-tail gap: launched, verified healthy, genuinely still open.** Dispatched to
  `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`'s HL recent-tail todo (this doc is its cited Source). Fleet-check
  first: the existing `cefi-hyperliquid-2026-20260727-071055` 365-day historical-year VM (launched 2026-07-27 00:10 UTC)
  was only on day 7/208 (2026-01-07) at pickup, measured pace ~2h/day — it would not reach the 2026-06-24 tail for ~2
  weeks, so a separate targeted launch does not duplicate current in-flight compute. **Baseline**
  (`read_availability_index`, cefi consolidated index, venue=HYPERLIQUID, 2026-06-24..2026-07-25): 30,787 rows —
  `expected_unattempted`=15,376, `empty_confirmed`=9,480, `captured`=5,928, `attempted_failed`=3. **Launched**
  `cefi-hyperliquid-2026-20260727-123922` via
  `VENUES="HYPERLIQUID" YEARS="2026" OVERRIDE_START_DATE=2026-06-24 OVERRIDE_END_DATE=2026-07-25 bash scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`
  (dry-run verified the exact window first; SPOT, non-force/idempotent, `SYMBOLS=ALL` catalogue-driven — matches BUG#4's
  fix, not the old hardcoded-9 cap). **Verified started + healthy** (not fire-and-forget): RUNNING at T+30s; `run.log`
  shows `OnchainPerpBatch: catalogue-driven universe for HYPERLIQUID on 2026-06-24 = 174 symbols` (correct start date) +
  a fresh `vm-heartbeat/cefi-hyperliquid-2026-20260727-123922.txt` timestamp at T+5min, S3 client initialized, actively
  fetching. **Disposition**: the parent todo stays genuinely open — a 32-day multi-symbol S3 backfill is multi-hour at
  the sibling VM's measured pace, not completable in one session. **Next check-in should verify** (via
  `read_availability_index` on the same window): `captured` climbing from the 5,928 baseline toward the ~21,304
  attempted total (expected_unattempted+empty_confirmed+captured), `attempted_failed` still ~3 (no regression), and
  eventual VM `DEPLOYMENT_COMPLETED exit_code=0` — then flip the parent plan checkbox with the before/after counts its
  done_when clause requires. **Separate structural finding**: `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` is
  sitting AT its 1000-line hard cap right now (zero headroom) — even this minimal in-place progress note required
  trimming the parent todo's own wording to stay under cap; a future check-in on ANY still-open todo in that plan will
  hit the identical wall until it goes through the archival/line-cap-remediation ritual (same pattern already applied to
  this doc on 2026-07-25). Flagging so the next agent doesn't burn time on the same discovery.

- **2026-07-27 T+31min (slot-11) — HYPERLIQUID recent-tail gap check-in: healthy, genuine forward progress, still
  open.** Picked up the same still-open `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` HL recent-tail todo per
  slot-6's "next check-in should verify" ask above. `gcloud compute instances list` confirms
  `cefi-hyperliquid-2026-20260727-123922` still `RUNNING`, no preemption; `run.log` ground-truthed (not just VM status)
  — fresh writes at T+31min (`OnchainPerpBatch: HYPERLIQUID/derivative_ticker/KPEPE/2026-06-24 captured 1440 rows`,
  timestamp within ~90s of check time), now on `derivative_ticker` for day 2026-06-24 after finishing `book_snapshot_5`.
  **Fresh `read_availability_index` measurement, same window (venue=HYPERLIQUID, 2026-06-24..2026-07-25, 30,848 rows —
  grew by 61 vs baseline's 30,787 since `now-2` advanced a day)**: `captured`=5,987 (up from baseline 5,928, +59 —
  genuine climb), `attempted_failed`=3 (unchanged — no regression), `expected_unattempted`=15,376,
  `empty_confirmed`=9,482. Confirms the VM is doing real, correct work, but at this pace (+59 captured in ~31min
  covering one symbol-day at a time across `book_snapshot_5`→`derivative_ticker`→likely `trades` next, for each of ~32
  days) this is genuinely a multi-hour-to-multi-day completion, consistent with slot-6's estimate — not completable in
  this session. **Did NOT flip the parent plan checkbox** (real completion criterion — captured across the full range —
  not yet met; the plan file is at its 1000-line hard cap per slot-6's structural finding, so any future check-in note
  belongs here, not inline in the plan). **Next check-in should verify**: `captured` continuing to climb toward the
  ~21,304 total-attempted target, `attempted_failed` still ~3, and eventual `DEPLOYMENT_COMPLETED exit_code=0` — then
  flip the parent checkbox.

- **2026-07-27 (slot-5) — HYPERLIQUID recent-tail gap: prior VM preempted, relaunched, verified healthy, still open.**
  Picked up the same still-open `cefi_satellite_ao_dispatch_batch1_2026_07_25.md` HL recent-tail todo. **Fleet-check
  first**: `gcloud compute instances list` showed `cefi-hyperliquid-2026-20260727-123922` (slot-6/11's VM) no longer
  running. `gcloud compute operations list` confirmed a `compute.instances.preempted` system event at
  `2026-07-27T14:02:54Z` (~1h23m after its 12:39:25Z launch), auto-deleted per `--instance-termination-action=DELETE`;
  no `PROGRESS.json` checkpoint exists for this one-off launch (not wired into the fleet auto-recovery watchdog per
  data_engineering craft-file guidance), so no automated resume was possible. **Pre-relaunch measurement**: `run.log`
  ground-truthed the VM's last real write at `14:01:32Z` (book_snapshot_5/PENGU/2026-06-26), consistent with the
  preemption timestamp. `read_availability_index()` hit a transient auth token-refresh error at check time
  (`Unable to retrieve Identity Pool subject token`) — retried once, still empty; bypassed via a direct
  `google.cloud.storage` read of the consolidated `_index/availability_index.parquet` (same source data, same window
  venue=HYPERLIQUID 2026-06-24..2026-07-25): `captured`=6,725 (up from slot-11's 5,987, +738 — genuine climb from the
  VM's work before preemption), `attempted_failed`=3 (unchanged — no regression), `expected_unattempted`=15,376,
  `empty_confirmed`=9,504. **Relaunched** `cefi-hyperliquid-2026-20260727-150820` via the identical idempotent non-force
  SPOT command slot-6 used
  (`VENUES="HYPERLIQUID" YEARS="2026" OVERRIDE_START_DATE=2026-06-24 OVERRIDE_END_DATE=2026-07-25 bash scripts/vm/launch-cefi-hl-aster-historical-backfill.sh`,
  dry-run verified the window first). Kept the SPOT default (this VM's own preemption count is 1, not the 3-in-a-day
  threshold that justified the sibling historical fleet's `ON_DEMAND=true` escalation) — idempotent skip means the
  relaunch resumes correctly regardless. **Verified started + healthy, not fire-and-forget**: serial console showed
  startup-script completed exit status 0 at `15:11:03Z` (code deployed, deps installed, backfill process launched);
  `run.log` then showed the correct catalogue-driven universe
  (`OnchainPerpBatch: catalogue-driven universe for HYPERLIQUID on 2026-06-24 = 174 symbols`, matching slot-6's original
  figure) and, by `15:14:13Z`, 33+ genuine `captured` rows lines across distinct symbols (AVAX/AVNT/AXS/.../BSV) for day
  2026-06-24. **Disposition**: parent todo stays genuinely open — same multi-hour-to-multi-day completion profile as
  before. **Did NOT flip the parent plan checkbox** (completion criterion not met; plan file still at its 1000-line hard
  cap per slot-6's structural finding). **Next check-in should verify**: `captured` continuing to climb from the 6,725
  baseline toward the ~21,604 total-attempted target (expected_unattempted+empty_confirmed+captured), `attempted_failed`
  still ~3, no further preemption on this run-id, and eventual `DEPLOYMENT_COMPLETED exit_code=0` — then flip the parent
  checkbox. **UPDATE (slot-5, in-session monitoring through 16:34Z)**: `/done` was attempted after the relaunch note
  above and hard-rejected by the AO server's M3 gate (requires a commit touching the actual plan checkbox — an
  issue-doc-only note doesn't satisfy it; correctly refused to force a dishonest flip). Continued monitoring in-session
  instead: day 1 (2026-06-24) completed cleanly at 15:42Z (8.15M rows across trades/book_snapshot_5/ derivative_ticker,
  `process_final=True`), day 2 (2026-06-25) completed cleanly at 16:14Z, day 3 (2026-06-26) in progress as of 16:34Z
  (book_snapshot_5, ~1355 per-VM shard entries) — zero errors, zero `attempted_failed` regressions, one
  correctly-handled honest-absence case (KSHIB, stale S3 archive) and one correctly-handled day-boundary clip (24
  boundary-bleed ticks trimmed) observed. Pace ~30min/day → full 32-day range projects to ~16h total, consistent with
  slot-6's original estimate. **Minor unrelated finding (P3, not blocking)**: the launcher's `FORCE="${FORCE:-250}"`
  default (`deployment-service/scripts/vm/launch-cefi-hl-aster-historical-backfill.sh:61`) is functionally harmless
  (downstream `VM_FORCE` consumers only match the literal string `"true"`, so `"250"` never triggers force-mode) but is
  almost certainly a copy-paste artifact from the adjacent `DRY_RUN="${DRY_RUN:-250}"` default one line above — worth a
  follow-up cleanup to a clearer default (`false`) so a future reader doesn't waste time investigating it as a suspected
  bug the way this session briefly did.

- [ ] [SCRIPT] P3. **deployment-service** — fix the confusing `FORCE="${FORCE:-250}"` default in
      `scripts/vm/launch-cefi-hl-aster-historical-backfill.sh` (line ~61) to `FORCE="${FORCE:-false}"`. Harmless today
      (only the literal string `"true"` triggers `VM_FORCE=true` downstream) but reads as a bug — likely copy-pasted
      from the adjacent `DRY_RUN="${DRY_RUN:-250}"` line. **Done when**: default reads `false`, existing dry-run/force
      tests (if any target this script) still pass, `quality-gates.sh --no-fix` green. Source: this doc, slot-5
      checkbox.

- **na-eligibility-audit 2026-07-30** (tranche=cefi, autonomous): KEEP-NA, valid - carries an operator-gated corpus-wide
  (~4.5M file) content `--apply`, a features schema-shape gap the doc says needs a real decision, and a 586-row
  blast-radius call.

- **2026-07-30 (finalize-plan reconciliation, `cefi_migration_cutover_and_track8_completion_finalize_2026_07_25.md`
  todo 2)**: Reviewed this doc's own Phase-1/2 section end-to-end against the shipped work. **Every Phase-1/2 checkbox
  that can be honestly closed already IS closed** — spot-verified a sample of the cited code commits as genuine
  ancestors of `origin/live-defi-rollout` (`instruments-service@8166676465f1`, `@f06eba12989d`, `@b61f9bdd`;
  `market-tick-data-service@d47609ec`, `@d302f07a`, `@ec04e8f5`, `@0388e1a9`; `unified-api-contracts@825878f7`,
  `@11adf279`, `@dfecc787` — all confirmed via `git merge-base --is-ancestor`). The two Phase-1/2 items still `- [ ]`
  are correctly left open, not missed reconciliation: (1) **Parquet CONTENT backfill (corpus-wide)** — genuinely
  in-flight, tracked in exhaustive detail in `cefi_content_migration_fleet_half_incomplete_2026_07_26.md` (44-shard
  fleet, multiple OOM/preemption/freeze failure classes diagnosed and fixed, still not corpus-complete as of the most
  recent entry there); (2) **Progress Log at every gate** — the discipline itself has been followed for every apply gate
  that HAS run (drain, filename rename, manifest dedup, eu-twin drop all cite measured before/after counts above), but
  the item is tied to the still-incomplete Script-1 migration, so flipping it now would be a premature completion claim.
  Both stay open until Script 1 finishes. **No reconciliation gap found** — this doc's Phase-1/2 state already
  accurately reflects shipped work.
- **context-scout 2026-08-01**: populated context_scope (6 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — swapped the codex-only list for the binding
  blueprint doc, the live content-migration-fleet tracker, and two source targets (catalog reader, HL/ASTER launcher).
- **na-eligibility-audit 2026-08-04** (tranche=cefi, autonomous): KEEP-NA, stale item closed — Phase 0a's "Lock the two
  contracts" checkbox was stale (its merge target, Phase 2's SSOT-contradiction item, is itself `[x]` DONE); closed with
  citation. Doc stays NA overall — the 586-row blast-radius call, the features schema-shape gap, and the corpus-scale
  `--apply` campaign remain genuine judgment/operator-gated work.
- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-07** (tranche=cefi, autonomous): KEEP-NA, stale-duplicate citations fixed — the P0
  "Parquet CONTENT backfill" and P1 "Progress Log at every gate" checkboxes (Phase 1/2) are both already tracked/
  in-flight in `cefi_content_migration_fleet_half_incomplete_2026_07_26.md` (assigned_vm: planning, status: open); fixed
  both citations inline rather than reclassifying (would dispatch a duplicate). Doc stays NA overall — the 586-row
  blast-radius call (line 225) and the features schema-shape gap (line 395, + its dependent line 409) remain genuine
  judgment/operator-gated work, unchanged from the 2026-08-04 verdict. Secondary note for a future pass: the small P3
  `FORCE` default-value item (line 709) reads as an isolated, unclaimed RECLASSIFY candidate on its own — not actioned
  this run since it doesn't change the doc-level verdict.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (6 entries), still accurate.
- **na-eligibility-audit 2026-08-09** (tranche=cefi, autonomous): KEEP-NA, valid — full 759-line read, 6 open items
  confirmed, each requiring a real scoping/design decision before it's worker-determinable. 1 small item (VM-launcher
  FORCE default) flagged MISCLASSIFIED_LIKELY_AO_ELIGIBLE by a prior pass and reaffirmed here, not claimed on its own.
