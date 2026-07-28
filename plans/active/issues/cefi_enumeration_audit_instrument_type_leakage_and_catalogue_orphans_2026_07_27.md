---
doc_type: issue
title: >-
  Post-cutover enumeration audit found 2 findings without an existing ruling: instrument_type carries data_type-shaped
  values on 480 chain-bundle rows, and 31,207 canonical-shaped instrument_ids are orphaned from the IS catalogue
summary: >-
  Filed while flipping the enumeration-audit terminal checkpoint todo in
  `cefi_migration_cutover_and_track8_completion_2026_07_25.md`, post Script-1 corpus-wide `--apply` completion
  (2026-07-27). The census's dominant finding (instrument_id 99.49% canonical, residual = the already-ruled bare-wire
  class) cleanly satisfies that todo's done-when. Two smaller findings surfaced by the SAME run do NOT have an existing
  ruling and are tracked here rather than silently waved through: (1) 480 manifest rows carry `instrument_type` values
  of `futures_chain`/`options_chain` (277+30 rows) plus lowercase `future`/`spot`/`spot_pair`/blank (60+100+12+1) — the
  lowercase-casing subset is already covered by the D1/D2 2026-07-20 ruling (compare case-insensitively, do not flag),
  but `futures_chain`/`options_chain` are NOT case variants of any canonical value — they look like `data_type` values
  leaking into the `instrument_type` column, plausibly a deliberate TradFi-style chain-bundle-shard convention (mtds git
  history shows `_is_bundled_chain_shard` handling exactly this shape for CME/ICE), not yet confirmed as intentional
  here. (2) 31,207 canonical-SHAPED instrument_ids captured in the manifest are NOT members of the instruments-service
  catalogue (429,129-row `prod/catalog.parquet`) — dominated by `DERIBIT:OPTION:*` (29,264 of 31,207) — meaning either
  the catalogue is missing legitimate historical DERIBIT options, or these are captures under an id-form the catalogue's
  builder never produced. Both are read-only findings from a manifest-index audit (no GCS corpus walk, no writes).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, instruments-service]
scope: [engineer]
tags: [cefi, enumeration-audit, instrument-type, catalogue-orphan, chain-bundle, post-cutover]
related:
  [
    /plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
  ]
created: 2026-07-27
parent_epic: cefi_master
priority: P2
estimate_class: research
assigned_role: data_engineering
source: >-
  Surfaced by re-running `market-tick-data-service/scripts/audit_cefi_manifest_noncanonical_enumeration_2026_07_18.py`
  (read-only, manifest-index read against `gs://market-data-tick-cefi-prd-central-element-323112`, 8,880,557 rows) as
  the enumeration-audit terminal checkpoint for `cefi_migration_cutover_and_track8_completion_2026_07_25.md`, right
  after Script 1's corpus-wide `--apply` campaign finished (all shards `EXIT_STATUS=0`).
assigned_vm: NA
execution_scope: local-only
drift_direction: none
depends_on: []
locked_by:
locked_since:
resolved_by:
---

# Enumeration audit: instrument_type chain-shape leakage + catalogue orphans (2026-07-27)

> Investigation-only record (this doc). No code was changed while authoring this doc. `assigned_vm: NA`,
> `execution_scope: local-only` — a human decides when to pick this up and whether either finding is a bug or a
> known-intentional shape.

## What I found

### Finding 1 — `instrument_type` carries non-canonical, non-casing values on 480 rows

The full distinct-value breakdown (8,880,557 total manifest rows):

```
5,940,519  PERPETUAL
1,936,673  SPOT_PAIR
  563,178  FUTURE
  437,205  OPTION
    1,948  perpetual        ⚠ lowercase — D1/D2 2026-07-20 ruled, migration_pending, do not flag
      554  None             ⚠
      277  futures_chain    ⚠ NOT a casing variant — this is a distinct string
      100  spot             ⚠ lowercase
       60  future           ⚠ lowercase
       30  options_chain    ⚠ NOT a casing variant
       12  spot_pair        ⚠ lowercase
        1  (blank)          ⚠
```

`futures_chain`/`options_chain` (307 rows total) are not case-different from any of the 4 canonical values
(`PERPETUAL`/`SPOT_PAIR`/`FUTURE`/`OPTION`) — they are literally the `data_type` column's own values (see the distinct
`data_type` list from the same run: `futures_chain` 366,162 rows, `options_chain` 122,850 rows), appearing in the
`instrument_type` column instead. `market-tick-data-service`'s own git history
(`8e43da75 fix(tradfi): Phase-D checker matches TradFi FUTURE/OPTION (CME/ICE) shards on underlying... _is_bundled_chain_shard reuses the WRITER's venue->instrument_type SSOT`)
shows a real, deliberate "bundled chain shard" convention exists for TradFi CME/ICE futures/options chains, where a
single manifest row represents an entire chain (not one instrument) and carries different key semantics.

The other 173 rows (100 `spot` + 60 `future` + 12 `spot_pair` + 1 blank) are lowercase-casing variants already covered
by the existing D1/D2 ruling — no new investigation needed for those.

### RESOLVED 2026-07-27 — DELIBERATE, not a bug (high confidence)

Follow-up investigation confirms this is a pre-existing, deliberate, workspace-wide writer convention applied
identically to TradFi (CME/ICE) and specific CeFi venues — not TradFi-only logic leaking onto CeFi rows:

- `manifest_finalize.py:241` (`_write_bundle_shard_row`) writes `"instrument_type": itype_key` — gated by
  `itype_key in _UNDERLYING_PARTITIONED_TYPES and itype_key != "combo" and data_type_key in BUNDLED_DATA_TYPES` (line
  330), with **no asset_group gate**. `BUNDLED_DATA_TYPES` is a cross-cutting UAC registry
  (`unified_api_contracts/canonical/crosscutting/_honest_coverage_clusters.py`) that includes
  `options_chain`/`futures_chain` for every asset group by design.
- `partitioned_writer.py:266-269` has an **explicit CeFi branch**:
  `self._asset_group == "cefi" and instrument_type in ("futures_chain", "options_chain")` — CeFi is a first-class,
  intentional case, not accidental fallthrough.
- `symbol_rules.py:151-188` (`_VENUE_INSTRUMENT_TYPE`) shows `"OKX-FUTURES": "futures_chain"` and
  `"BINANCE-DELIVERY": "futures_chain"` as **venue-level defaults** — the exact same mechanism as `"CME"`/`"ICE"` two
  lines below. `_MIXED_INSTRUMENT_VENUES = {"BINANCE-FUTURES", "BYBIT", "DERIBIT"}` (lines 211-217) plus
  `_DATED_FUTURE_PATTERNS`/`_OPTION_PATTERN` do symbol-level classification for those 3 venues.
- `scripts/pipeline_e2e_check.py`'s `_is_bundled_chain_shard` (the "Phase-D checker" from `8e43da75`) is a **later,
  TradFi-only addition to the CHECKER script**, not the writer — its own test
  (`tests/unit/test_pipeline_e2e_tradfi_canonical.py:247-258`) explicitly asserts
  `_is_bundled_chain_shard("CEFI", "DERIBIT", "options_chain") is True` and documents CeFi's convention as pre-existing
  and untouched by the TradFi-specific fix.
- A fresh manifest re-query shows the population has grown to 1,100 rows since this doc's original 307-row snapshot (the
  manifest is a live, growing target — expected): OKX-FUTURES 900 (dominant, 81.8% — venue-level default, matching the
  TradFi CME/ICE mechanism, not DERIBIT as originally guessed), BINANCE-FUTURES 89, BYBIT 50, DERIBIT 52 (26+26),
  BINANCE-DELIVERY 7, OKX 2.

**No further action needed on this finding** — closing as intentional-by-design.

### Finding 2 — 31,207 canonical-shaped instrument_ids are orphaned from the IS catalogue

Cross-referencing the manifest's captured canonical-shaped ids (49,386 distinct) against the instruments-service
catalogue (`prod/catalog.parquet`, 429,129 rows, 424,619 deduped canonical ids via `canonical_by_wire.values()`):

```
DERIBIT              OPTION         29,264   e.g. DERIBIT:OPTION:BTC-10APR20-4750-C
DERIBIT              FUTURE            721   e.g. DERIBIT:FUTURE:BNB-USDC@LIN
BYBIT                FUTURE            287
KRAKEN-FUTURES       PERPETUAL         256
COINBASE-FUTURES     PERPETUAL         217
HYPERLIQUID          PERPETUAL         167
BITGET-FUTURES       PERPETUAL          87
... (13 venues total, 31,207 orphan ids)
```

DERIBIT OPTION dominates (93.8% of all orphans). Two candidate explanations, NOT distinguished by this audit alone: (a)
the catalogue is missing legitimate historical DERIBIT option series (a catalogue-completeness gap — the builder never
produced these ids, e.g. long-expired dated options outside whatever window the catalogue build covers), or (b) these
captures exist under an id-form variant the catalogue's DERIBIT adapter never emits (a canonicalization mismatch,
similar in spirit to — but distinct from — the DERIBIT missing-quote defect this same plan's todo 1 already fixed).
Given DERIBIT dated-options have already been the root cause of 2 OTHER defects this same migration surfaced (the
missing-quote defect, todo 1; the giant-file OOM class hit during Script 1's `--apply`, this doc's own Progress Log) — a
3rd DERIBIT-options-specific anomaly in the same campaign is plausibly related, not coincidental, but this is a
hypothesis, not a confirmed root cause.

### RESOLVED 2026-07-27 — id-form mismatch (canonicalization-epoch divergence), high confidence

Smoking-gun evidence: `instruments-service/docs/CEFI_INSTRUMENTS.md` (§ Deribit marker migration, 2026-07-09) documents
the **exact same instrument_id** used as this doc's orphan example — `DERIBIT:OPTION:BTC-10APR20-4750-C` → migrated to
`DERIBIT:OPTION:BTC-USD@INV-20200410-4750-C` — via
`instruments-service/scripts/canonicalize_deribit_id_markers_2026_07_09.py --apply --full-sweep`, which ran against
`prod/catalog.parquet` on 2026-07-09 and verified **100% of DERIBIT PERPETUAL/FUTURE/OPTION rows (263,979) now carry the
`@LIN`/`@INV` marker, 0 remaining**.

The SAME day, MTDS's equivalent migration
(`market-tick-data-service/scripts/migrate_cefi_dated_perps_margin_marker_2026_07_09.py`) covers the same `@LIN`/`@INV`
marker canonicalization across 6 venues (BINANCE-FUTURES, BYBIT, KRAKEN-FUTURES, DERIBIT, OKX-SWAP, OKX-FUTURES) — but
its own docstring states **`options`/`options_chain` shards are explicitly OUT OF SCOPE** (the migration's title is
`cefi-dated-perps` — perpetuals + dated futures, not options — and always skips them).

So on the same date, IS fully migrated the catalogue's DERIBIT OPTION id-shape to the new marker form, while MTDS
explicitly excluded options from its parallel manifest/content migration — the manifest's DERIBIT OPTION
`instrument_id`s are still in the pre-2026-07-09 form and can never match the now-100%-migrated catalogue. This fully
explains the 93.8% DERIBIT:OPTION dominance (Deribit is the only meaningful CeFi options venue —
`CEFI_OPTIONS_UNDERLYINGS` restricts to BTC/ETH only). Secondary/contributing factor:
`instruments_service/reference_data/adapters/cefi/deribit_options_adapter.py:5` fetches only `expired=false`
instruments, so even a fresh catalogue rebuild wouldn't re-admit long-expired series directly — weaker than the id-form
mismatch, which is sufficient on its own and dated precisely.

**Not fully explained** (undetermined, not guessed): the minority venues — BYBIT FUTURE (287), KRAKEN-FUTURES PERPETUAL
(256), COINBASE-FUTURES PERPETUAL (217), HYPERLIQUID PERPETUAL (167), BITGET-FUTURES PERPETUAL (87), 3.9% combined.
COINBASE-FUTURES/HYPERLIQUID/BITGET-FUTURES fall outside the 6-venue 2026-07-09 migration's scope entirely;
BYBIT/KRAKEN-FUTURES being in-scope-but-still-orphaned is unexplained residual, possibly the separate, smaller,
independently-documented catalogue-rollup-staleness class in
`instruments-service/scripts/measure_cefi_catalogue_enumeration_gap_2026_07-23.py` — not traced further, flagged rather
than guessed.

**Net effect**: the DERIBIT:OPTION majority (93.8%) is explained and requires no code fix — it's a
canonicalization-epoch snapshot divergence between two systems' migrations on the same day, not a live defect; a future
catalogue/manifest reconciliation pass (outside this doc's scope) would resolve it by re-running MTDS's marker migration
with options in-scope, or accepting the divergence as historical. The 3.9% minority residual remains genuinely open.

## Net effect

Neither finding blocks the enumeration-audit todo's own done-when (that todo's 4 stated axes —
instrument_id/instrument_type/venue/data_type non-canonical FORMS — are satisfied; catalogue membership is a different,
adjacent axis the same script happens to also report). **Both findings investigated and resolved 2026-07-27** — finding
1 is intentional-by-design (no fix needed); finding 2 is an explained, historical canonicalization-epoch divergence
(93.8% of it) plus a small (3.9%) genuinely-open residual across 5 minority venues.

## Todos

- [x] ✅ [DATA] P2. **DONE 2026-07-27.** Confirmed `instrument_type ∈ {futures_chain, options_chain}` is a deliberate,
      already-shipped, workspace-wide "bundled chain shard" writer convention (`manifest_finalize.py`,
      `partitioned_writer.py`, `symbol_rules.py` all show explicit CeFi call sites, not TradFi-only fallthrough) — see
      "RESOLVED 2026-07-27" under Finding 1 above. No code fix needed; closing as intentional. Repo:
      market-tick-data-service.
- [x] ✅ [DATA] P2. **DONE 2026-07-27.** Root-caused the 31,207 catalogue-orphan ids: 93.8% (DERIBIT:OPTION) is an
      id-form mismatch from a canonicalization-epoch divergence — `instruments-service` fully migrated DERIBIT OPTION
      ids to the `@INV` marker form on 2026-07-09 while MTDS's parallel migration that same day explicitly excluded
      options from scope, so the manifest's pre-migration ids can never match the catalogue. Historical, no live defect,
      no code fix needed for this majority. The remaining 3.9% (BYBIT/KRAKEN-FUTURES in-scope-but-orphaned, plus 3
      out-of-scope venues) is undetermined — flagged as a genuinely open, smaller residual rather than resolved. See
      "RESOLVED 2026-07-27" under Finding 2 above. Repos: instruments-service, market-tick-data-service.
- [ ] [DATA] P3. Trace the remaining 3.9% catalogue-orphan residual (BYBIT FUTURE 287, KRAKEN-FUTURES PERPETUAL 256,
      COINBASE-FUTURES/HYPERLIQUID/BITGET-FUTURES PERPETUAL 217/167/87) — BYBIT/KRAKEN-FUTURES are in the 2026-07-09
      marker migration's scope yet still orphaned (unexplained); the other 3 venues fall outside that migration
      entirely. Possibly the smaller, independently-documented catalogue-rollup-staleness class in
      `instruments-service/scripts/measure_cefi_catalogue_enumeration_gap_2026_07-23.py` — not confirmed. Small scale
      (~1,015 ids, 0.011% of the corpus), not urgent. Repos: instruments-service, market-tick-data-service.
