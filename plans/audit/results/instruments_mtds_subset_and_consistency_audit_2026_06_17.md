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

## Phase 2 — file-level manifest-vs-reality (sub-agents, IN PROGRESS)
Sampling spec: per AG, open instruments daily files + MTDS files across years (≥3 far-apart years), across
venue/data_type/instrument_type/chain/league combos, esp. the F1/F4/F6 flagged combos + controls. Verify: captured cell ⇒
file exists with rows; empty ⇒ no file/0 rows; instruments file lists the types/venues the manifest implies; MTDS
data_types present match instrument_types listed (options listed ⇒ options_chain captured, etc.).

## Progress Log
- 2026-06-17: Phase 1 complete (full-index walk of all 10 projected indexes). Findings F1–F7 above. Phase 2 (file
  verification) dispatched to per-AG sub-agents next.
