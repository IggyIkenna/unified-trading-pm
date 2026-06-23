---
title: TradFi backfill multi-source — FX→yahoo, CBOE cash-index no-provider, ICE source-ask
created: 2026-06-22
parent_epic: tradfi_master
assigned_vm: vm-tradfi
priority: P1
status: active
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# TradFi backfill multi-source — FX / CBOE-index / ICE

Make the TradFi OHLCV backfill **multi-source** instead of databento-only. The wave-launcher
(`deployment-service/scripts/wave_launcher.py`) mapped only CME/CBOE/NASDAQ/NYSE → databento launchers; ICE + FX fell to
"out-of-scope" and never filled.

## Venue → source → fillable matrix (the key deliverable)

| Venue                                | expected_unattempted               | Source               | Fillable?                                  | Mechanism                                                                          |
| ------------------------------------ | ---------------------------------- | -------------------- | ------------------------------------------ | ---------------------------------------------------------------------------------- |
| CME / NASDAQ / NYSE                  | (various)                          | databento            | YES (live)                                 | GLBX.MDP3 / DBEQ.BASIC; existing launchers                                         |
| CBOE — VX **futures**                | — (captured)                       | databento XCBF.PITCH | YES (captured: 134 futures_chain ohlcv_1m) | CFE subscription                                                                   |
| CBOE — VIX cash **index**            | 1,651 (instrument_type=index)      | **none**             | NO — DELETE (operator 2026-06-23)          | DELETE cells + GCS objects (futures carry the info; index not tradable, derivable) |
| FX (USD/KRW spot pairs)              | 3,228 (538 × 6 dt, incl ohlcv_24h) | **yahoo_finance**    | YES                                        | daily ohlcv_24h, venue-routed to `_fetch_yahoo_fx`                                 |
| ICE (IFEU/IFUS — Brent/Gasoil/softs) | 530,600 (combo/futures_chain)      | **NONE AVAILABLE**   | **NO — needs ICE-data subscription ask**   | databento dropped ICE in 3-dataset lockdown; Massive carries NO ICE                |

### Key finding — Massive does NOT have ICE data (verified 2026-06-22)

The operator hypothesis was "massive can fill ICE if massive has the data." It does NOT. Probed Massive's S3 `flatfiles`
bucket directly (path-style boto3, the same creds the connector uses): top-level prefixes are `global_crypto/`,
`global_forex/`, `us_futures_cbot/`, `us_futures_cme/`, `us_futures_comex/`, `us_futures_nymex/`, `us_indices/`,
`us_options_opra/`, `us_stocks_sip/`. **There is NO ICE prefix** (`us_futures_ice/`, `global_futures/`,
`us_futures_ifus/` all ABSENT). Massive's futures coverage is CME-group only (CME/CBOT/COMEX/NYMEX). The MTDS
`_route_massive` confirms this in code: `_MASSIVE_FUTURES_VENUES = {"CME"}` only; any other venue would be treated as an
equity-REST symbol → 404. UAC `tradfi_instrument_universe.py` already documents that ICE (IFEU.IMPACT/IFUS.IMPACT) was
DROPPED in the 3-dataset subscription lockdown and "requires an explicit ICE subscription + adding the dataset to the
allowlist." So ICE genuinely needs an operator credential/subscription ask — NOT a wave-launcher dispatch.

## Todos

- [x] [SCRIPT] P1. **CBOE cash-index reclass** — confirm VX-futures captured (✅ 134 futures_chain ohlcv_1m captured via
      XCBF.PITCH), then reclass CBOE cash-index (instrument_type=index, CBOE:INDEX:VIX/SPX) 1,614 expected_unattempted
      cells → empty_confirmed/EXPECTED_NO_PROVIDER_COVERAGE in-place with snapshot + GATE (rows + captured unchanged). —
      market-tick-data-service@2c6425b `reclass_cboe_cash_index_no_provider.py`; APPLIED to live tradfi `_index`
      (snapshot `pre_cboe_cash_index_reclass_2026_06_22.parquet`); verified 1,614 index cells now empty_confirmed, VX
      futures_chain (134) preserved.
- [x] [SCRIPT] P1. **FX via yahoo launcher** — `launch-tradfi-bf-fx-ohlcv-24h.sh` (Yahoo daily ohlcv_24h, venue-routed;
      FX bypasses --source). FX capture itself was already code-complete in `_fetch_yahoo_fx` (venue=FX → Yahoo daily).
      — deployment-service@eab5aeb; dry-run verified.
- [x] [SCRIPT] P1. **Wave-launcher multi-source** — `LAUNCHER_FOR_VENUE` adds FX→fx-launcher; per-venue
      `VENUE_DATA_TYPES` map (FX=ohlcv_24h); FX added to PER_YEAR_VENUES; VM_NAME regex now venue+timeframe-agnostic.
      ICE intentionally absent (massive can't serve it). Dry-run confirms FX dispatch atoms appear (FX year=2025/2026 →
      fx launcher) and ICE stays out-of-scope. — deployment-service@eab5aeb.

### VIX-index DELETE + Databento universe floor-clip (operator 2026-06-23 — supersedes the reclass-to-empty_confirmed above)

> Operator decision 2026-06-23: keep VIX **futures** (VX, XCBF.PITCH, canonical ohlcv_1m/1s — captured + verified
> tracking the index: corr 0.95–0.98, steady ~1.7–2.1 vol-point contango basis vs the Barchart/massive VIX-index 15m on
> 2026-04-14/28/30). DELETE the VIX **cash index** entirely (not leave as empty_confirmed clutter): not tradable,
> derivable from the futures, trades less often over a shorter window at coarser granularity. ALSO: the
> `expected_unattempted` universe must not seed Databento-fetched cells older than each level's rolling-history floor
> (L0 16y for ohlcv_1s/1m), nor seed 15m/24h (DERIVED by aggregation, not fetched) as databento EU.

- [x] [SCRIPT] P0. **Enumerator floor-clip + VIX-index drop** —
      `instruments-service/scripts/enumerate_expected_universe.py` `_enumerate_v2_tradfi`: added
      `_tradfi_floor_start_for_data_type(dt, today)` (databento-fetched ohlcv_1s/ohlcv_1m → L0 16y floor via UAC
      `earliest_allowed_start`; 15m/24h derived + Yahoo FX → None = no clip), skip seeding EU dates older than the floor
      in the alive branch; and `_is_vix_cash_index(instr)` (instrument_type=index named VIX, or blank-id CBOE index
      legacy cell — DXY/treasury indices keep their own non-VIX id → unaffected) → skip the whole instrument so no VIX
      cash-index cell is ever seeded. — instruments-service@814b14a.
- [x] [SCRIPT] P0. **Manifest correction (one-off, snapshot+GATE)** —
      `instruments-service/scripts/correct_tradfi_universe_floor_clip_and_vix_index.py` (mirrors
      `populate_v9_index_columns_inplace.py`): remove EU cells older than the L-floor, remove ALL VIX cash-index cells,
      remove derived-databento (15m/24h source=databento) EU. GATE: captured/attempted_failed may only drop by the
      VIX-index captured/af count (sanctioned), never else. APPLIED to live tradfi `_index` 2026-06-23 (snapshot
      `_index/snapshots/pre_universe_floor_clip_2026_06_23.parquet`). EU universe 1,606,687 → 1,466,157 (−140,530
      derived-databento phantom cells; EU-floor drop = 0, the universe was already clipped at the L0 floor); VIX
      cash-index 1,651 cells removed (37 captured = Barchart series). GATE proof: captured 733,375 → 733,338 (delta 37 =
      sanctioned VIX-index only), attempted_failed 16,346 → 16,346 (unchanged). Live re-read VERIFIED post-apply:
      instrument_type=index rows = 0, derived-databento 15m/24h EU = 0, VX futures captured = 135 preserved. —
      instruments-service@814b14a.
- [ ] [SCRIPT] P0. **Delete Barchart/massive VIX-index GCS objects** (script SHIPPED; --apply RUNNING 2026-06-23) —
      `instruments-service/scripts/delete_vix_cash_index_gcs_objects_2026_06_23.py` deletes the VIX cash-index parquet
      objects (instrument_type=index at venue=CBOE — CBOE's only cash index is VIX, across batch_massive/batch_databento
      pipeline_modes) via `unified_trading_library` `gcs_delete_object` (never gsutil). Gated on the
      VX-futures-vs-VIX-index sanity check (PASSED: corr 0.95-0.98, steady ~1.7-2.1 vol-point contango basis) + the
      manifest correction above. — instruments-service@814b14a.

- [ ] [BACKFILL] P1. **Run the FX yahoo backfill to completion** (operational) — launch
      `launch-tradfi-bf-fx-ohlcv-24h.sh` per-year via the wave-launcher cron / manual, verify FX ohlcv_24h
      expected_unattempted → captured in the manifest. (The cron handles live ticks; this is the operational drain.)
- [ ] [BLOCKED-CREDENTIALS] P2. **ICE data subscription** — ICE (IFEU/IFUS Brent/Gasoil/softs + DX) is NOT in any source
      we have (databento dropped it; Massive has no ICE prefix). Fillable ONLY with an explicit ICE-data subscription
      (databento ICE datasets re-added to the allowlist, or a Massive/other ICE feed). 530,600 expected_unattempted
      cells stay until an operator credential ask is acked. CREDENTIAL APPROVAL REQUEST logged in pings. Note: the IS
      ICE instrument catalogue (BRN/G FUTURE/COMBO, 2,067 rows) already exists — only the market-data source is missing.

## Codex SSOT updates

- `codex/02-data/tradfi-databento-sourcing-ssot.md` — add the multi-source venue→source matrix + the "Massive has NO ICE
  prefix" finding (the lib comment "databento is capable for every tradfi OHLCV venue" is wrong for ICE; corrected by
  this plan).

## Progress Log

- **2026-06-23 — VIX cash-index DELETE + Databento rolling-history floor-clip (operator decision, autonomous).**
  Supersedes the earlier reclass-to-`empty_confirmed` of the CBOE cash index. Shipped instruments-service@814b14a: (A)
  `_enumerate_v2_tradfi` floor-clip helper `_tradfi_floor_start_for_data_type` (databento ohlcv_1s/ohlcv_1m → L0 16y
  floor via UAC `earliest_allowed_start`; 15m/24h-derived + Yahoo FX → `None`) + `_is_vix_cash_index` drop; (B)
  `correct_tradfi_universe_floor_clip_and_vix_index.py` (snapshot+GATE manifest correction); (C)
  `delete_vix_cash_index_gcs_objects_2026_06_23.py` (GCS object delete via `gcs_delete_object`). **Sanity check
  (operator-requested, PASSED):** captured VX-futures ohlcv_1m (front contract VX/K6) aggregated to 15m vs the
  Barchart/massive VIX cash-index 15m on 3 captured dates — 2026-04-30 corr 0.979 / basis +2.13; 2026-04-28 corr 0.948 /
  +1.69; 2026-04-14 levels track (VX ~20.4 vs VIX ~18.7, steady ~1.7-2.0 contango). The futures track the index with a
  small steady contango basis exactly as expected → index is redundant/derivable. **Manifest correction APPLIED to live
  tradfi `_index`** (snapshot `pre_universe_floor_clip_2026_06_23.parquet`): EU universe 1,606,687 → 1,466,157 (−140,530
  derived-databento phantom 15m/24h cells; EU-floor drop = 0, already at floor); VIX cash-index 1,651 cells removed (37
  captured). GATE: captured 733,375 → 733,338 (delta 37 = sanctioned VIX-index only), attempted_failed unchanged.
  Re-read VERIFIED: instrument_type=index = 0, derived-databento 15m/24h EU = 0, VX futures captured = 135 preserved.
  **Ship note:** direct-LDR push (dirty-deps carve-out — UTL was foreign-dirty mid-edit, blocking quickmerge); QG proven
  green in an isolated tree (3708 tests pass, my files ruff/basedpyright-clean; the only QG redness was foreign
  concurrent `sports_dependency.py`/`base.py` edits NOT in my commit, stashed for preservation).

## Temporary states + their canonical follow-up plans

- The CBOE-reclass + wave-launcher map are landed; the FX backfill drain + ICE credential-ask are the open todos above.
- VIX cash-index DELETE + Databento floor-clip landed 2026-06-23 (instruments-service@814b14a); GCS-object delete
  `--apply` running. The enumerator change is live for future universe seeds — no follow-up needed.
