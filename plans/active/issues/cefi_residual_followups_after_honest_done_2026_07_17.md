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
    cefi_completion_program_2026_07_15.md,
    cefi_hl_aster_batch_data_gaps_2026_06_22.md,
    cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md,
    phantom_captures_cefi_2026_06_28.md,
  ]
created: 2026-07-17
last_updated: 2026-07-17
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
   range.

2. **[P2] HYPERLIQUID phantom re-census (1,277 rows → `@LIN` canonical path).** Cosmetic manifest-labelling — does NOT
   affect captured data. Blocked only on box size: the re-census (`reconcile_phantom_manifest_rows_all.py`) OOMs on the
   15GB VM; needs a 32-64GB box. Detail: `phantom_captures_cefi_2026_06_28.md`. Evidence: phantom count → 0 for HL.

3. **[P1] Drop eu twins of natively-canonical (non-Tardis) captures — ~10,368 rows.** The OnchainPerp/native-canonical
   lane writes canonical `captured` rows but nothing drops the matching `expected_unattempted` twin, so the relabel gate
   is RED on these and its reconcile structurally cannot fix them (it only reconciles its own relabels). This is a
   pre-existing defect, independent of the Tardis ceiling. Detail + namespace root cause:
   `cefi_mtds_writer_raw_symbol_vs_canonical_eu_namespace_mismatch_2026_07_15.md`. Fix: a targeted eu-twin drop keyed on
   `(venue, data_type, day)` where a canonical `captured` twin exists.

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
- [ ] [SCRIPT] P0. **Re-measure the single honest-unresolved number off the REBUILT catalogue** (pinned 3-tuple
      `(venue, instrument_type, raw_symbol)`; pre-rebuild measurement = **439**) + record it as the ONE number used
      everywhere (blueprint open-q #7). Blocked only on the prod rebuild landing. (repo: instruments-service)
- [ ] [SCRIPT] P1. **Sample OPTION / dated-FUTURE `raw_symbol` coverage on the REBUILT catalogue** (blueprint open-q #14
      — the "decompose ALL types" claim is still unproven for per-option / per-expiry chains). (repo:
      instruments-service)
- [ ] [SCRIPT] P2. **586 marker-less `VENUE:PERPETUAL:BASE-QUOTE` catalogue rows** (blueprint open-q #19, measured
      2026-07-17: BITGET-FUTURES 275 / BINANCE-FUTURES 153 / COINBASE-FUTURES 107 / BINANCE-DELIVERY 27 /
      BITFINEX-FUTURES 16 / OKX-SWAP 5 / BYBIT 3 — NOT just the 16 BITFINEX rows the blueprint recorded). Deliberately
      OUT of scope of the Phase -1 fix (the gate is `0` `:PERP:`, not `0` marker-less) — rewriting them is a 586-row
      blast radius that needs its own decision + drain. (repo: instruments-service)

## Phase 0a — Contract locks (design lock, before any code)

- [ ] [DOCS] P0. **Lock the two contracts**: single-instrument cefi filename stem = FULL `instrument_id`; shard atom
      WITH `pipeline_mode`. The contradicting codex docs get corrected in Phase 2, but the form is byte-locked now so
      writer/migration/reader agree. (repo: unified-trading-pm)

## Phase 0b — Code fixes (MUST land + DEPLOY to every writer AND every narrow-read consumer before any corpus rewrite)

- [ ] [BACKEND] P0. **FIX 0 — ONE shared 3-tuple builder** `CeFiCatalogReader.build_raw_symbol_map()` (3-tuple, reads
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
  - ⬜ **MTDS half OPEN** — `CeFiCatalogReader.build_raw_symbol_map()` (repo: market-tick-data-service).
- [ ] [BACKEND] P0. **FIX D1 — Writer decompose ALL venues (3-tuple).** One insertion point in
      `derive_row_instrument_id` (`tardis_shared.py:455`) resolving via FIX-0; covers the Tardis parquet column AND
      manifest key (both flow through it — zero change to cap-critical `venue_fetch.py`). Miss → honest fallthrough.
      (repo: market-tick-data-service)
- [ ] [BACKEND] P0. **FIX D1-live — Live/on-chain COLUMN decomposition** in `PartitionedTickWriter.write_chunk` (the
      live consolidated + on-chain lanes never call `derive_row_instrument_id`; without this, live cefi columns stay
      non-canonical → batch≠live, ε=0 spine broken). Same shared map. (repo: market-tick-data-service)
- [ ] [BACKEND] P0. **FIX D2 — Canonical FILENAME stem = full `instrument_id`.** `_file_stem_for` (cefi branch) +
      `partitioned_writer._resolve_file_symbol` (extend the prediction-only override to cefi). Reuses the column
      D1/D1-live made canonical; writer KEY/bookkeeping stay on bare symbol → shard atom unchanged. Chain bundles
      untouched. (repo: market-tick-data-service)
- [ ] [BACKEND] P0. **FIX D3 — Reader wire↔canonical bridge (3-tuple; fixes audited silent data-loss).** Candidate-stems
      (canonical + reverse-map wire) in MTDS `reader.py:341`; drop the wire `("symbol","==",id)` pushdown (`:388`);
      normalize-on-read the column via the forward 3-tuple map; MDPS `path_parsing.py` accept both stems; rename + widen
      the TRADFI-only `canonical_writer_shaping.py:259` renormalizer to cover cefi. Handles the MIXED-corpus interim.
      (repos: market-tick-data-service, market-data-processing-service, unified-api-contracts)
- [ ] [BACKEND] P0. **FIX D-features — narrow cefi reads (REQUIRED before cutover, not optional).** features
      `raw_data_loader.py:126-179`: inherit the D3 bridge (if it reads via MTDS `reader.py`) or add its own
      `get_cefi_wire_map()` bridge; reconcile the `instrument_id`↔`instrument_key` column-name mismatch. (repo:
      features-service)
- [x] ✅ [BACKEND] P0. **Enumerate the narrow-read consumers** — DONE 2026-07-17 (slot-3), measured. **IN SCOPE (4)**:
      MTDS `reader.py`; MDPS (`path_parsing.py` / `canonical_writer_shaping.py` / `orchestration_scanner.py` /
      `data_source.py`); features-service (`raw_data_loader.py` + cross-instrument `batch_handler.py`);
      **execution-service `algo_library/mtds_book_provider.py`** (narrow `read_shard(instrument_id=)` via
      `CanonicalParquetReader` → inherits D3, REDEPLOY REQUIRED — not named in the blueprint). **VERIFIED OUT (3)**:
      ml-service (0 `raw_tick` refs), batch-live-reconciliation-service (0 refs), strategy-service runtime
      (`asset_group="defi"` hardcoded). Evidence in the Progress Log.
- [ ] [BACKEND] P0. **DEPLOY the reader bridge to all 4 in-scope consumers** — the D4 GCS cutover cannot run until every
      one carries it (the drain stops WRITERS only; readers keep running against renamed/rewritten objects). Includes an
      **execution-service redeploy** even though it needs no code change. (repos: market-tick-data-service,
      market-data-processing-service, features-service, execution-service)
- [ ] [SCRIPT] P1. **Fix the one campaign script our rename breaks** —
      `strategy-service/scripts/trace_arbitrage_price_dispersion.py` matches the filename LEAF (:294) against hardcoded
      WIRE forms (:273-274) over `asset_group=cefi` → silently mis-matches post-D4-rename. Either make the leaf-match
      accept both wire + canonical stems, or confirm its
      `# Delete-when: master_to_live_defi_2026_05_23 Phase D complete` is satisfied and delete it
      (delete-deprecated-code). `trace_carry_staked_basis.py` is a prefix scan → SAFE, no action. (repo:
      strategy-service)

## Phase 1 — Corpus migrations (scripted + dry-run first; `--apply` ONLY behind the Phase-1 drain, snapshot-first)

- [ ] [SCRIPT] P0. **Parquet CONTENT backfill (corpus-wide).** Canonicalize the frozen `instrument_id` column for all 3
      non-canonical classes: (a) historical margin-marker undecomposed — run the existing
      `migrate_cefi_dated_perps_margin_marker_2026_07_09.py --apply`; (b) all non-margin venues — extend it to
      catalogue-decompose; (c) on-chain historical raw-content (`BTC-PERP`→canonical). Snapshot-first to
      `_migration_backups/`. Do NOT re-fetch. (repo: market-tick-data-service)
- [ ] [SCRIPT] P0. **Filename rename (Tardis lane).** Rename single-instrument cefi objects wire→canonical, extending
      the proven `migrate_onchain_perp_perpetual_canonical_2026_07_08.py` pattern (GCS rename + manifest rewrite
      together). Snapshot-first; idempotent; per-day prefix batches (single-walk discipline). (repo:
      market-tick-data-service)
- [ ] [SCRIPT] P0. **Manifest completion.** Resolve the ~490k raw captured rows — at minimum the ACTIVE majors
      (BYBIT/OKX/BINANCE-FUTURES) the 2026-07-16 relabel's ambiguous-pair exclusion left raw — and de-duplicate the
      coexisting `…@LIN` / `…:BASE-QUOTE` / bare-wire key forms so each instrument maps to ONE canonical id. (repo:
      instruments-service)
- [ ] [SCRIPT] P1. **Close residual #3** — drop the 10,368 non-Tardis eu-twin canonical collisions (9,817
      EXTENDED-STARKNET + 518 PACIFICA-SOLANA + ~33) keyed on `(venue, data_type, day)` where a canonical `captured`
      twin exists. (repo: instruments-service)
- [ ] [INFRA] P0. **Pre-migration drain + snapshot (GATES all Phase-1 `--apply`).** Stop ALL live cefi writers (Tardis
      `cefi-queue-*` + on-chain `cefi-*` VMs, both clouds), consolidate the manifest, snapshot the cefi bucket + index
      before any content-rewrite/rename cutover; re-enable writers only after apply + verify. HARD RULE: no GCS cutover
      with writers live. (repo: deployment-service)

## Phase 2 — Docs + codex reconciliation

- [ ] [DOCS] P1. **Resolve the codex↔plan SSOT contradictions** the audit surfaced: `chart-candle-delivery-flow.md:274`
      ("Filename is the bare symbol") → canonical target + SUPERSEDED/forward-pointer banner;
      `read-time-filter-pushdown.md` (filenames now canonical — update the substring-match assumption);
      `availability-manifest-and-data-status.md` "immutable wire-form contract" (superseded for the manifest key);
      `per-asset-group-bucket-layouts.md:135` (`ticks.parquet` vs per-instrument stem split). (repo: unified-trading-pm)
- [ ] [DOCS] P1. **Progress Log at every gate** — each `--apply` records measured before/after row counts + coverage
      delta as evidence (per the runtime-verification HARD RULE). (repo: unified-trading-pm)

## Codex SSOTs (read before touching a phase)

`codex/02-data/defi-canonical-naming-ssot.md`, `…/availability-manifest-and-data-status.md`,
`…/chart-candle-delivery-flow.md`, `codex/06-coding-standards/read-time-filter-pushdown.md`,
`codex/05-infrastructure/vm-launcher-runbook.md` (drain), `codex/05-infrastructure/gcs-object-operations.md`.

## Progress Log

- **2026-07-17 (slot-3) — PHASE -1 GATE: BOTH DEFECTS FIXED AT SOURCE + PROVEN ON LIVE DATA →
  `instruments-service@517b817b`.** Both halves closed in `scripts/build_instrument_catalogue.py`. QG green (4417
  passed, coverage 88.97%).

  - **GATE 1 root cause — `build_instrument_catalogue.py:1113` (the emit) — LEGACY ON-DISK DATA, _not_ the adapter. A
    plain rebuild alone would NOT have fixed it.** The 9 `:PERP:` rows are all `instrument_type=PERPETUAL`,
    `margin_type=linear`, and all **DELISTED** (`available_to` 2026-02-28…2026-06-28). Measured why: on 2026-06-28 the
    on-chain adapter still emitted `:PERP:` for EVERY row (EXTENDED-STARKNET 101/101, LIGHTER-ZKSYNC 213/213,
    HYPERLIQUID 176/176, ASTER 484/484); the id-format fix landed later. A perp still LIVE after the fix collapses onto
    its canonical form via `_cefi_perp_lineage_key` (the lineage key is stable across the churn) — but one delisted
    BEFORE the fix has no post-fix snapshot at all, so its most-recent `by_date` row carries the legacy id and the
    roll-up passed it straight through. **Exactly the class `79d4dbcb` hit for dated FUTUREs**, so fixed the same way,
    in the same place: new `_canonicalize_cefi_perp_id()` rebuilding at roll-up time via the SAME shared UAC
    `build_instrument_id`. Pre-verified against the live `by_date` corpus that the rebuild HAS its inputs — the legacy
    rows DO carry `base_asset` + `quote_asset` (HL/EXTENDED `USD`, ASTER `USDT`, LIGHTER `USDC`) + `margin_type=linear`
    — and the rebuilds byte-match their live canonical siblings (`HYPERLIQUID:PERPETUAL:ARK-USD@LIN`,
    `ASTER:PERPETUAL:IP-USDT@LIN`, `EXTENDED-STARKNET:PERPETUAL:IP-USD@LIN`, `LIGHTER-ZKSYNC:PERPETUAL:IP-USDC@LIN`).
    Missing-field rows degrade unchanged (never guess).
  - **GATE 2 root cause — `build_instrument_catalogue.py:1140-1142` (the mirror).** All 511 drift rows are
    `instrument_type=FUTURE` — exactly the rows `_canonicalize_cefi_future_id` rewrites. `79d4dbcb` rebuilt the emitted
    `instrument_id` but the mirror kept sourcing `agg.meta["canonical_instrument_id"] or meta["instrument_key"]` (the
    STALE raw-glued value), so the two drifted. **This confirms the earlier "`canonical_instrument_id` is
    stale/vestigial → delete it" read was WRONG** — the column is live-consumed (`enumerate_expected_universe.py`,
    `backfill_defi_canonical_id_and_glued_prefix_2026_07_14.py`, `backfill_spot_asset_population_2026_07_16.py:324`
    which itself writes `canonical_instrument_id := instrument_id`, + MTDS `migrate_onchain_perp_*`). Fix = repair the
    mirror: BOTH surfaces now run through ONE shared `_canonicalize_cefi_rollup_id()` chain so they cannot drift again.
    The mirror **SOURCE** is canonicalized rather than blanket-copied from the emitted id — deliberate, so the DeFi POOL
    contract survives (there `instrument_id` is re-keyed to `pool_address` while `canonical_instrument_id` mirrors the
    glued `instrument_key`, pinned by
    `test_rollup_defi_pool_row_backfills_canonical_instrument_id_from_instrument_key`).
  - **Evidence (runtime-verified, "run it don't read it")**: the FIXED `build_catalogue_dataframe` run against 909 REAL
    live legacy `by_date` rows (HL + ASTER 2026-05-22, EXTENDED-STARKNET + LIGHTER-ZKSYNC 2026-06-28) → **GATE 1 = 0
    `:PERP:` ids, GATE 2 = 0 drift, both PASS**. Plus 16 new unit tests end-to-end through `build_catalogue_dataframe`
    (not the helper in isolation) carrying the exact live defect rows as fixtures; test execution proven by
    falsification (deliberately broken assert → RED, then reverted), so they are not silently uncollected.
  - **⚠️ REBUILD COMMAND — `--mode full` IS MANDATORY (a default `incremental` run leaves the gate RED)**:
    ```bash
    cd instruments-service && GCP_PROJECT_ID=central-element-323112 DEPLOYMENT_ENV=prd \
      .venv/bin/python scripts/build_instrument_catalogue.py --asset-group cefi --mode full
    ```
    Three verified gotchas: (1) **there is NO `--apply`** — the script WRITES by default, `--dry-run` is the opt-in
    flag; (2) `--mode` defaults to **`incremental`**, which only re-reads a self-widening trailing window and leaves the
    frozen tail untouched — every one of the 9 `:PERP:` rows (and most of the 511) is DELISTED and sits in that frozen
    tail, so an incremental run would NOT re-roll them; (3) `GCP_PROJECT_ID` + `DEPLOYMENT_ENV` must be in the env or
    `resolve_bucket_name` fail-loud raises `BucketNamingError`. Add `--allow-catalogue-shrink` ONLY if the monotonic
    guard trips (it should not — this renames ids, it does not drop rows).
  - **Scope decision (decide-and-document)**: fixed the legacy `PERP`-token defect ONLY. Measured a wider population
    while diagnosing — **595** PERPETUAL rows carry NO `@marker`, of which only 9 are the `:PERP:` defect and **586**
    already carry the correct `PERPETUAL` token and merely lack the marker (BITGET-FUTURES 275 / BINANCE-FUTURES 153 /
    COINBASE-FUTURES 107 / BINANCE-DELIVERY 27 / BITFINEX-FUTURES 16 / OKX-SWAP 5 / BYBIT 3 — **materially bigger than
    blueprint open-q #19's "16 BITFINEX rows"**, corrected + filed as its own P2 todo above). Rewriting those 586 is a
    silent blast-radius expansion beyond the documented gate (`0` `:PERP:`, not `0` marker-less), so it is pinned OUT of
    scope by a regression test rather than done quietly.
  - **⚠️ SSOT CONTRADICTION FOR THE OPERATOR (not blocking, not fixed here)**:
    `backfill_defi_canonical_id_and_glued_prefix_2026_07_14.py`'s docstring asserts
    "`catalog.instrument_id == canonical_instrument_id` holds for every row, **pool or not**", but
    `test_rollup_defi_pool_row_backfills_canonical_instrument_id_from_instrument_key` pins the OPPOSITE for POOL rows
    ("per the operator-approved policy"). Both cannot be true. The cefi gate is unaffected (cefi has no POOL rows); the
    DeFi catalogue needs an operator ruling on which is canonical.
  - **Multi-agent note**: shipped under the closed **dirty-deps** carve-out (quickmerge pre-flight blocked on live
    uncommitted WIP in UTL + UAC, mtime <120s → PROTECT). A concurrent agent's in-flight sports work
    (`extra_attrs`/`fixture_attrs`) was uncommitted in the SAME two files; staged by **filtered hunk** rather than by
    file so none of it landed in this commit — verified 0 foreign markers staged, and their WIP left intact in the
    working tree.

- **2026-07-17 (slot-3, orchestrator) — CONSUMER ENUMERATION CLOSED + 2 BLUEPRINT CORRECTIONS.** Measured, not assumed
  (grep-then-READ).
  - **Narrow-read consumer set for the raw_tick cutover — IN SCOPE (4)**: (1) MTDS `reader.py`
    (`CanonicalParquetReader`) → D3; (2) MDPS (`path_parsing.py`, `canonical_writer_shaping.py`,
    `orchestration_scanner.py`, `data_source.py`) → D3; (3) features-service
    (`cross_instrument/engine/raw_data_loader.py`
    - `cross_instrument/cli/handlers/batch_handler.py`) → D-features; (4) **NEW — execution-service
      `execution_service/algo_library/mtds_book_provider.py`**: does narrow
      `CanonicalParquetReader.read_shard(venue=, data_type=tbbo, instrument_type=, target_date=, instrument_id=)` per
      (instrument, day) → **inherits D3 for free BUT MUST BE REDEPLOYED before the cutover**. The blueprint never named
      it; it is now part of the reader-deploy gate (blueprint open-q #4).
  - **VERIFIED OUT OF SCOPE (3)**: **ml-service** — ZERO `raw_tick` refs corpus-wide (reads features/candles only);
    **batch-live-reconciliation-service** — ZERO `raw_tick`/`CanonicalParquetReader` refs; **strategy-service runtime**
    — `engine/core/canonical_vault_provider.py:126` + `canonical_perp_funding_provider.py:137` are `asset_group="defi"`
    HARDCODED, so their raw_tick reads never touch cefi. This materially shrinks the cutover blast radius from the
    blueprint's "strategy/ml/batch-live-recon" hand-wave to a concrete 4.
  - **NEW FINDING — one campaign script WILL break on the D4 rename**:
    `strategy-service/scripts/trace_arbitrage_price_dispersion.py` matches on the FILENAME LEAF
    (`leaf = blob.name.rsplit("/", 1)[-1].upper()`, :294) against hardcoded WIRE forms (`BTCUSDT.parquet`,
    `PI_BTCUSD.parquet`, `BTCUSD-PERP.parquet`, :273-274) over `asset_group=cefi` → silently mis-matches post-rename.
    `trace_carry_staked_basis.py` is a plain `.parquet` prefix scan (:206) → SAFE. Both are `# Lifecycle: campaign` /
    `# Delete-when: master_to_live_defi_2026_05_23 Phase D complete`. Our rename causes the break, so we own it →
    tracked as its own todo (fix the leaf-match to accept both forms, or confirm the delete-when is satisfied). NOT left
    silent.
  - **BLUEPRINT CORRECTION 1 (open-q #3 is partly a SURFACE CONFLATION)**: `chart-candle-delivery-flow.md:274`
    ("**Filename is the bare symbol**, not the canonical `venue:type:symbol` instrument-key") sits under the
    **`processed_candles/`** layout block (:264-283) — it documents MDPS candle-output filenames, **NOT
    `raw_tick_data/`**. It is therefore NOT a contradiction of the raw_tick filename lock and MUST NOT be "corrected" in
    Phase 2. The blueprint + the original codex audit lens both cited it as the headline stale claim; that was
    grep-then-conclude.
  - **BLUEPRINT CORRECTION 2 (the lock is BETTER-supported than stated)**: codex ALREADY documents the raw_tick stem as
    the FULL instrument_key — `instrument-pipeline-defi.md:177`
    (`raw_tick_data/.../venue={venue}/{instrument_key}.parquet`)
    - `:183` (worked example `.../venue=BINANCE-FUTURES/BINANCE-FUTURES:PERPETUAL:ETHUSDT.parquet`). So Phase-0a's
      "filename stem = FULL `instrument_id`" **corroborates** existing codex rather than contradicting it (note the
      doc's own example carries the undecomposed `ETHUSDT` payload — shape right, decomposition is exactly what D1
      fixes).
  - **The genuinely stale raw_tick docs for Phase 2 are therefore just two**: `read-time-filter-pushdown.md:69-70`
    (blesses the SUBSTRING blob gate with the wire example `.../BTCUSDT.parquet` matches `instrument_ids=["BTCUSDT"]` —
    this IS the D3 break in the MIXED window) and `per-asset-group-bucket-layouts.md:135` (shows CEFI raw_tick as
    `ticks.parquet` only, missing the per-instrument stem split; reconciled by `pipeline-coverage-matrix.md:360-361`).

- **2026-07-17 (slot-3) — FIX 0 UAC HALF SHIPPED: `CeFiWireCanonicalMap` contract SSOT landed —
  `unified-api-contracts@825878f7`.** T0 lands first, before its MTDS/MDPS consumers (dependency order). NEW
  `unified_api_contracts/canonical/domain/cefi_wire_canonical.py` (203 L) + `tests/unit/test_cefi_wire_canonical_map.py`
  (253 L, 21 tests) + root `__all__` export. **Full `quality-gates.sh` GREEN (exit 0, 342s)**; basedpyright 0 errors/0
  warnings; pure — pandas-free, I/O-free (both MTDS and MDPS depend on UAC, never on each other, so each supplies its
  own thin catalogue loader and feeds `from_rows()`).
  - **Decisions made + documented (no operator round-trip needed):**
    1. **Constructor named `from_rows`**, not the blueprint's provisional `from_triples` — the blueprint (§ 2 FIX 0)
       flagged the arity mismatch and explicitly delegated the choice ("pick one and export it"). The KEY is a 3-tuple
       but each input ROW is a 4-quad, so `from_triples` misnames the input. Exported + internally consistent.
    2. **Map fields are PUBLIC** (`canonical_by_wire` / `wire_by_canonical` / `ambiguous_wire_keys`) vs the blueprint's
       underscore-prefixed sketch (`_canonical_by_wire`). Rationale: the D1 resolver's **fail-loud-on-empty-map** check
       and the writer/reader honest-unresolved WARNING both need to read map size + the ambiguous set from outside the
       class. Underscored fields would force private access at every consumer.
    3. **Reverse map preserves `raw_symbol` case verbatim** (not uppercased) and is built from ALL valid rows —
       **including forward-ambiguous ones**. Reverse is keyed on `instrument_key`, which stays unique even when the wire
       symbol collides, so it is still injective and must keep working for candidate-stem recovery. Case is preserved
       because the D3 reader rebuilds on-disk filename stems from this value and the wire spelling is what is actually
       on the object (BINANCE writes lowercase `btcusdt`) — this is also why the reader's candidate list can
       meaningfully carry both the reverse value AND its `.upper()`.
    4. **Fail-loud on an empty catalogue stays the CALLER's job**, not this pure contract's: `from_rows([])`
       legitimately returns an empty map (a valid pure value). The blueprint's fail-loud rule (blocking-risk #4) binds
       the _registered prod resolver_ — "disabled-by-default for tests is achieved by NOT registering a builder".
       Raising here would make the empty case unrepresentable and break that design. Asserted in
       `test_from_rows_empty_builds_empty_map`.
  - **Regression guard for the whole program is live**: `test_both_bybit_rows_resolve_neither_excluded` asserts BOTH
    `(BYBIT, SPOT_PAIR, BTCUSDT)` → `BYBIT:SPOT_PAIR:BTC-USDT` and `(BYBIT, PERPETUAL, BTCUSDT)` →
    `BYBIT:PERPETUAL:BTC-USDT@LIN` resolve and NEITHER is excluded — a regression to a 2-tuple key fails this test
    loudly. Also covered: `BITFINEX-FUTURES/PERPETUAL/ADAF0:USTF0` wrapped-wire quad, a synthetic genuinely-ambiguous
    3-tuple (`canonical_for(...) is None` AND present in `ambiguous_wire_keys`), reverse round-trip, case-insensitivity
    on both build and lookup, and blank-field skipping.
  - **Finding (in-file, fixed same commit):** QG flagged `from_rows()` at 51 L over the function-size limit; extracted a
    module-level `_iter_normalized()` row-normalizer. Note the size check printed a red ❌ while the run still exited 0
    — it did not fail the gate; caught by reading the output rather than trusting the summary line.
  - **Next**: MTDS half (`CeFiCatalogReader.build_raw_symbol_map()`) — parallel agent; then D1/D1-live/D2/D3 consume
    this contract. The FIX 0 box stays UNTICKED until the MTDS half lands.

- **2026-07-17 (slot-3) — PHASE -1 GATE MEASURED: RED (2 narrow defects) + 3-TUPLE DESIGN EMPIRICALLY CONFIRMED.**
  Measured directly against the live catalogue
  (`gs://instruments-store-cefi-prd-central-element-323112/prod/catalog.parquet`, 8.26 MiB, written
  2026-07-17T09:09:54Z, 424,699 rows; single-object read, no walk):
  - **GATE 1 FAIL — 9 rows carry a `:PERP:` id**: HYPERLIQUID 5 (`HYPERLIQUID:PERP:ARK`, `…:DOOD`, `…:FTT`, `…:MATIC`),
    EXTENDED-STARKNET 2, ASTER 1 (`ASTER:PERP:IPUSDT`), LIGHTER-ZKSYNC 1. Confirms blueprint open-q #10 (the on-chain
    venues were never refreshed to `PERPETUAL@LIN`). Narrow + tractable.
  - **GATE 2 FAIL — 511 rows where `instrument_id != canonical_instrument_id`** (BINANCE-DELIVERY 177, OKX-FUTURES 140,
    COINBASE-CDE 99, BINANCE-FUTURES 48, DERIBIT 47). **NEW FINDING — the direction matters and vindicates the
    blueprint's "read `instrument_id`, NEVER `canonical_instrument_id`" rule**: `instrument_id` holds the CORRECT
    canonical form (`BINANCE-DELIVERY:FUTURE:ADA-USD@INV-20200926`) while `canonical_instrument_id` still holds the
    STALE raw-glued form (`…:ADAUSD_200925`). So `instruments-service@79d4dbcb`'s `_canonicalize_cefi_future_id()`
    roll-up fix updated `instrument_id` but NOT `canonical_instrument_id` — the latter is a stale/vestigial column. Gate
    2 as originally worded is therefore the WRONG gate: the fix is to canonicalize (or delete — delete-deprecated-code)
    the `canonical_instrument_id` column, not to "correct" `instrument_id`.
  - **3-TUPLE CLAIM CONFIRMED (blueprint blocking-risk #1)**: 2-tuple `(venue, raw_symbol)` → 423,691 keys, **781
    ambiguous**; 3-tuple `(venue, instrument_type, raw_symbol)` → 424,035 keys, **439 ambiguous** — the 3-tuple rescues
    **342 keys** from honest-unresolved. The reviewer's marquee example reproduces exactly: `(BYBIT, BTCUSDT)` maps to
    BOTH `BYBIT:SPOT_PAIR:BTC-USDT` AND `BYBIT:PERPETUAL:BTC-USDT@LIN` → the 2-tuple would have EXCLUDED it → writer
    falls through to wrapped-wire → non-joining against the migration's decomposed id. The 3-tuple resolves each to
    exactly 1 id. **The single honest-unresolved number is 439** (pinned 3-tuple, this catalogue) — supersedes the
    divergent 297/777/781 figures (blueprint open-q #7); re-measure after the Phase -1 rebuild.
  - **Next**: fix the 2 catalogue defects (9 `:PERP:` + 511 stale `canonical_instrument_id`) → re-run the gate → then
    FIX 0 (shared 3-tuple builder), which is decision-independent and can be written in parallel.

- **2026-07-17 (slot-3)**: **Blueprint workflow complete → `_cefi_canonical_blueprint_2026_07_17.md`.** Adversarial
  design review verdict `NEEDS-REDESIGN`; the blueprint IS the redesign. Caught 5 data-corruption risks in the naive
  plan: (1) 2-tuple key under-resolves the BYBIT/OKX/BINANCE-FUTURES majors into non-joining ids → mandated ONE 3-tuple
  key + ONE shared builder; (2) re-enabling writers post-migration re-corrupts unless the 3-tuple code is deployed
  first; (3) live/on-chain write paths bypass `derive_row_instrument_id` → NEW FIX D1-live for the
  `PartitionedTickWriter` column; (4) silent corpus-wide degrade on empty catalogue → fail-loud; (5) reader
  normalize-on-read left ambiguous majors non-canonical → 3-tuple forward map. Also: filename stem locked to FULL
  `instrument_id`; shard atom WITH `pipeline_mode`; D3 reader bridge must deploy to ALL narrow-read consumers before the
  D4 cutover; Phase -1 catalogue rebuild is a hard prerequisite. Todos above rewritten to the redesign. Next: verify
  Phase -1 catalogue state + implement FIX 0 (the foundational shared builder), which is decision-independent.
- **2026-07-17 (slot-3, earlier)**: Program opened. Two audit workflows (filename + three-questions) completed,
  adversarially verified: Q1 reader-path = PARTIAL, Q2 every-parquet = PARTIAL, Q3 manifest-everywhere = NO. Operator
  recorded 4 decisions (execution in-session/this-doc; autonomous prod mutations; migrate filenames; decompose all
  venues). Phased todos authored. Then: implementation blueprint workflow (design specs + migration-script designs),
  then Phase-0 code fixes.
