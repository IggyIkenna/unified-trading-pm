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

## Phase 0 — Code fixes (MUST land + deploy before any corpus rewrite, or in-flight writes re-corrupt)

- [ ] [BACKEND] P0. **Writer: decompose ALL cefi venues.** Replace the `MARGIN_MARKER_VENUES`-only branch in
      `derive_row_instrument_id` (`tardis_shared.py:567-576`) with a catalogue-backed
      `(venue, raw_symbol)→instrument_key` resolution (via `CeFiCatalogReader`), so new Tardis writes for
      BITFINEX-FUTURES etc. stamp the fully-decomposed canonical id in the parquet column + manifest. Degrade to honest
      wire-wrapped only for the 297 ambiguous pairs. (repos: market-tick-data-service, unified-api-contracts)
- [ ] [BACKEND] P0. **Writer: canonical FILENAME stem.** Change `_file_stem_for` (`tardis_shared.py:704-715`) /
      `partitioned_writer.py:158-161` so new single-instrument writes name the object by the canonical symbol segment
      (per the 2026-07-08 raw-tick relaxation: symbol portion canonical), not the raw wire `symbol`. Keep chain-bundle
      `underlying`/`ticks.parquet` behavior. (repo: market-tick-data-service)
- [ ] [BACKEND] P0. **Reader wire→canonical bridge (fixes silent data-loss).** Add a cefi resolution path so a canonical
      id resolves to the on-disk wire filename/column via the catalogue `raw_symbol` map: MTDS `reader.py:341` (path
      build assumes `filename==instrument_id`) + `reader.py:388` (`("symbol","==",id)` pushdown against the wire
      column); MDPS `path_parsing.py:178-210` `blob_matches_canonical_instrument_id` (wire filename silently dropped);
      add a cefi branch to the TRADFI-only renormalizer `canonical_writer_shaping.py:259`. (repos:
      market-tick-data-service, market-data-processing-service)
- [ ] [BACKEND] P1. **features-service cross-instrument loader** — resolve the latent `instrument_id` (raw_tick) vs
      `instrument_key` (loader) column-name mismatch + confirm wire→canonical join on the real (non-mock) read path
      (`raw_data_loader.py:126-179`). (repo: features-service)

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

- **2026-07-17 (slot-3)**: Program opened. Two audit workflows (filename + three-questions) completed, adversarially
  verified: Q1 reader-path = PARTIAL, Q2 every-parquet = PARTIAL, Q3 manifest-everywhere = NO. Operator recorded 4
  decisions (execution in-session/this-doc; autonomous prod mutations; migrate filenames; decompose all venues). Phased
  todos above authored. Next: implementation blueprint workflow (design specs + migration-script designs, no heavy QG),
  then Phase-0 code fixes.
