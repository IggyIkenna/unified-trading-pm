---
title: Instruments ↔ MTDS subset + instruments internal-consistency audit (v9 migrated manifests)
created: 2026-06-17
author: ikennaigboaka [slot-interactive·human-planning]
source:
  - operator 2026-06-17 (deep-dive: "are MTDS shards a subset of instruments? consistency across what instruments we think we should have — options/futures/venues/chains/leagues")
  - v9 projected/beta manifests: gs://{instruments-store,market-data-tick}-{ag}-prd/_index/audit/projected_index_{ag}.parquet
locked_by: live-defi-rollout
---

# Instruments ↔ MTDS subset + consistency audit

**Question (operator):** (1) Is market-tick-data a proper SUBSET of instruments — i.e. do we ever CLAIM/expect market
data on a day/venue/instrument/chain/league where no instrument is listed, the blockchain didn't exist, there's no
fixture, or the league isn't canonised? (2) Are instruments internally consistent — do we claim instrument_types
(options/futures/spot/perp) / venues / chains / leagues we don't actually have, or have data for combos we don't list?

**Method.** Phase 1 (this pass) = manifest-level audit using the v9 projected indexes (instruments-store + market-tick
per AG). Grain: INSTR = entity×date ("entity listed N instruments that day", entity = venue|chain|league_id); MTDS =
instrument×data_type×date. "Subset" tested at entity-level and (entity,date)-level over MTDS **captured** cells only.
Phase 2 (sub-agents) = OPEN sampled instruments + MTDS parquet files across venue×data_type×instrument_type×chain×league
and across years, to audit manifest-vs-reality (the slow part). **Where I sampled vs walked:** Phase 1 walked the FULL
projected indexes (no sampling); Phase 2 samples files.

## Phase 1 — manifest-level findings (FULL-index walk, no sampling)

| AG | INSTR rows | MTDS rows | MTDS capture_status | Entity subset clean? |
|----|-----------|-----------|---------------------|----------------------|
| cefi | 30,803 (all captured) | 3,886,859 | captured 2.49M / **attempted_failed 1.40M** / empty 150 | ❌ 5 unlisted venues |
| defi | 125,242 (all captured) | 1,910,046 | captured 440k / empty 1.43M / failed 41k | ✅ (19 pre-genesis cells) |
| tradfi | 20,388 (19,247 cap / 1,141 empty) | 946,360 | captured 903k / empty 37k / failed 6k | ✅ (1 CME day) |
| sports | 2,681,628 | 786,508 | captured 202k / empty 584k / failed 164 | ⚠️ 2,107 null-league cells |
| pred | 493 (all captured) | 9,447 | captured 7,116 / empty 2,330 | ✅ clean |

### F1 (P1, CEFI) — MTDS captures 5 venues with ~no instruments history — SUBSET VIOLATION (instruments backfill gap)
`KRAKEN-FUTURES` (2,334 days), `KRAKEN-SPOT` (2,212), `LIGHTER-ZKSYNC` (319), `PACIFICA-SOLANA` (310),
`EXTENDED-STARKNET` (1) have **captured** MTDS market data but **zero** instruments-store rows in the projected index.
**Phase-2 file spot-check (verified):** instruments-store DOES now carry `KRAKEN-FUTURES`/`KRAKEN-SPOT` — but **only at
`day=2026-06-17`** (added TODAY); zero files for 2023-06-15 / 2024-06-15 / 2025-06-15 / 2026-06-16. So instruments was
just given these venues with **no historical backfill**, while MTDS has 2020→2026 market data → a ~6-year instruments
backfill gap (not a from-scratch venue add). **Fix:** backfill instruments-service daily listings for these venues
across the MTDS-covered range (re-run the IS CLI per date — never copy between dates). Until then cefi coverage
denominators are wrong (MTDS > instruments universe). Lighter/Pacifica/Extended (newer perp DEXes) likely the same
class.

### F2 (P1, CEFI) — BITGET-FUTURES / BITGET-SPOT each missing 5 instrument-days that MTDS captured
Instruments lists BITGET but is absent on 5 specific days where MTDS has captured data → instruments daily-capture gaps
(5 days each). Re-run the IS CLI for those dates (instruments expire/list daily — never copy between dates).

### F3 (P0, CEFI) — 1.40M `attempted_failed` MTDS cells (36% of cefi)
Massive fetch-failure backlog (not honest-empty). Needs diagnosis by venue×data_type (which adapter/venue is failing).

### F4 (P1, SPORTS) — 2,107 captured MTDS cells with NULL `league_id`
Sports market data (`odds_horizon_bucket`, `trades`, `ODDS`) captured with no `league_id` → cannot be attributed to a
canonised league. Either the league mapping is dropping on write, or we're capturing odds for non-canonised leagues.
Violates "no market data where the league isn't canonised."

### F5 (P2, SPORTS) — INSTR sports data-quality: 6,869 blank `capture_status` rows + a literal `date='all'`
Blank capture_status (legacy/unmigrated rows the v9 walk didn't classify) and a non-date `date='all'` value in the
instruments-store-sports index. Both are index-hygiene defects to clean in the canonicalisation walk.

### F6 (P2, TRADFI) — 182k blank `instrument_type` + thin options coverage
182,842 captured MTDS tradfi cells carry blank `instrument_type` (untyped — e.g. DERIBIT-style no-suffix); and
`options_chain` (3,287) is thin vs `futures_chain` (15,875) — candidate "we list options but barely capture options"
(the operator's example). Phase 2 must open tradfi instruments files to confirm whether options ARE listed but not
captured.

### F7 (P3, DEFI) — 19 Ethereum cells pre-instruments-genesis (cosmetic)
MTDS Ethereum captured 2020-01-01..19, before instruments-store-defi's first date (2020-01-20). Pre-genesis by ~19 days
— confirm whether instruments genesis should be earlier or MTDS those days are spurious.

## Phase 2 — file-level manifest-vs-reality (5 per-AG sub-agents, DONE — opened real GCS parquets across 2020/2023/2026)

> **Cross-cutting caveat:** the v9 PROJECTED index drops `row_count` (0.0 for every captured cell), so `captured⇒rows>0`
> was verified ONLY by opening parquets (sampled), not from the index field.
> **Discarded false lead:** a sub-agent claimed the cefi-bucket projected index was "100% TradFi" — re-verified FALSE
> (it is 3,886,859 cefi-venue rows incl KRAKEN-SPOT 329k). Not propagated.

### Reframes / refutations of Phase 1
- **F3 REFRAMED (cefi attempted_failed is mostly manifest-recon NOISE, not fetch failure).** Of 1.40M `attempted_failed`:
  `LegacyBlankErrorReasonError` 762,805 + `LEGACY_THIRDKEY_DRIFT_RECON_2026_05_07` 451,799 + `WITHIN_BOUNDS_EMPTY_RECLASSIFIED`
  89,590 = ~1.30M legacy-recon artifacts; **genuine fetch failures are only `VENUE_FETCH_FAILED` 83,975 + `HTTP_429` 3,652 ≈ 88k (2.3%)**.
  Action shifts from "backfill 1.4M" → "re-classify the ~1.3M legacy-blank/recon rows in the canonicalisation walk + backfill ~88k genuine."
- **F6 REFUTED (we DO capture options).** CME instruments list options heavily (8,602/day 2023; 9,430/day 2025) AND MTDS
  captures them — opened ES `instrument_type=options_chain` = 20,956 rows. CBOE lists only VIX index (no options to miss).
  The "thin 3,287" was an `instrument_type`-count artifact; `data_type=options_chain` has **120,946** captured cells (with
  blank instrument_type). Real issue = **typing inconsistency** (options split across two encodings) + the 182k blank
  instrument_type, both from legacy GCS path shapes. NOT missing options.
- **F5 PARTIALLY-REVISED.** The 6,869 blank-`capture_status` rows are real (malformed enumerator rows: blank data_type +
  blank league_id, venues API_FOOTBALL/`api_football` case-dup). The `date='all'` is **2 rows = BY DESIGN** (TEAMS/VENUES
  date-agnostic reference entities, captured) — NOT a defect.

### NEW findings (file-level)
- **N1 (P1, CEFI correctness) — phantom `empty_confirmed` SHADOW rows.** ~57% (61,300/106,869) of real-shard
  `empty_confirmed` cells coincide with a `captured` row for the SAME date/venue/instrument/data_type — the manifest carries
  TWO rows per cell (one captured w/ instrument_type, one bogus empty_confirmed w/ blank instrument_type). e.g. 2021-01-01
  BINANCE-FUTURES book_snapshot_5 AVAXUSDT = `empty_confirmed` but the parquet has **943,196 rows**. The empty shadow is bogus.
- **N2 (P1, TRADFI correctness) — CME weekend dishonest-empty.** ALL 333 CME `empty_confirmed`/`SOURCE_RETURNED_ZERO`
  instrument-dates are **Saturdays**; instruments writes a weekend carry-forward snapshot to GCS (`venue=CME/instruments.parquet`
  = 11,526 rows incl 7,364 OPTIONs on 2025-02-08) but the manifest records zero → ~1,079 dishonest-empty cells. INST index
  rows duplicated 2×/cell.
- **N3 (P0, SPORTS) — F4 is 100%, root = consolidator drops league_id.** ALL 202,087 captured MTDS-sports cells have NULL
  `league_id` (not 2,107) — but the GCS hive path (`league_id=BUNDESLIGA`) AND the row-level `league_id` column ARE populated
  in every file opened. The consolidator does not propagate per-file league into the manifest row. ALSO: MTDS `trades` (73.7k)
  carry NULL `source` (violates the crosscutting `source=` provenance rule); venue case-dup API_FOOTBALL/`api_football`.
- **N4 (P2, SPORTS) — 194,356 instruments captured rows with `instrument_count==0`** (per-league companion rows; the global
  count lands on one row, per-league duplicates carry 0). Count-attribution smell to confirm against shard grain.
- **N5 (P1, DEFI correctness) — temporally-impossible `vault_share_price` captured phantoms.** 1,582 captured cells 2020–2023
  are ALL `vault_share_price` (VAULT 1,113 / MAKER 348 / FRAX 74 / ETHENA 47); MAKER pre-2023 + ETHENA pre-Feb-2024 (launch)
  are impossible; the 2020-01-01 VAULT cell opened as a **0-row parquet** (captured⇒no-rows phantom). (F7 is the Ethereum subset of this.)
- **N6 (P1, DEFI normalization) — dimension pollution.** `chain` column polluted with token-pair symbols (`1INCH-ETH`,
  `ETH-USDC`, `WSTETH-ETH`); `instrument_type` case-dup `pool` (227,935) vs `POOL` (158,431); `venue` dups (CURVE vs
  CURVE-ETHEREUM, MORPHOVAULTS vs MORPHO_VAULTS vs MORPHO-ETHEREUM). Breaks per-dimension grouping/denominators.
- **N7 (P2, cross-AG) — pipeline_mode migration incomplete.** defi/pred/cefi paths still carry dual `asset_group=`+`category=`
  keys and many lack the `pipeline_mode={mode}_{source}/` partition; pred's captured-max day exists ONLY in the bare/old shape
  (readers must prefix-fallback or it reads missing). Tracked by the pipeline_mode migration plan — cross-link, don't re-open.
- **N8 (P3, PRED) — index data_type label drift.** Index labels captured cells `prediction_canonical_question_group` but GCS
  paths use `prediction_trades`/`trades`; 1 `attempted_failed` cell carries a blank (untyped) reason. Subset itself CLEAN.

### Subset verdict (operator Q1), per AG
- **cefi:** ❌ VIOLATION — Kraken (+Lighter/Pacifica/Extended) MTDS history with ~no instruments backing (F1).
- **defi:** chain-subset OK, but ❌ temporally-impossible vault_share_price captured phantoms (N5/F7).
- **tradfi:** ✅ subset OK (1 CME day); options ARE captured (F6 refuted).
- **sports:** attribution moot — data IS league-attributed in files; manifest drops league_id (N3). No true data-subset violation.
- **pred:** ✅ CLEAN (no captured-before-genesis).

## Progress Log
- 2026-06-17: Phase 1 complete (full-index walk, F1–F7). Phase 2 complete (5 per-AG sub-agents opened real GCS parquets
  across 2020/2023/2026). Reframed F3 (recon-noise) + F6 (options ARE captured) + F5 (date='all' by design); escalated F4
  to 100% w/ root cause; added N1–N8. Discarded one false sub-agent claim (cefi≠tradfi). Findings → wrapper plan
  `instruments_mtds_subset_consistency_remediation_2026_06_17.md`.
