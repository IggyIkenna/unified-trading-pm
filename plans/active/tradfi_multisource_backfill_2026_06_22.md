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

| Venue                                | expected_unattempted               | Source               | Fillable?                                  | Mechanism                                                           |
| ------------------------------------ | ---------------------------------- | -------------------- | ------------------------------------------ | ------------------------------------------------------------------- |
| CME / NASDAQ / NYSE                  | (various)                          | databento            | YES (live)                                 | GLBX.MDP3 / DBEQ.BASIC; existing launchers                          |
| CBOE — VX **futures**                | — (captured)                       | databento XCBF.PITCH | YES (captured: 134 futures_chain ohlcv_1m) | CFE subscription                                                    |
| CBOE — VIX/SPX cash **index**        | 1,614 (instrument_type=index)      | **none**             | NO — deliberately unsourced                | reclass → empty_confirmed/EXPECTED_NO_PROVIDER_COVERAGE             |
| FX (USD/KRW spot pairs)              | 3,228 (538 × 6 dt, incl ohlcv_24h) | **yahoo_finance**    | YES                                        | daily ohlcv_24h, venue-routed to `_fetch_yahoo_fx`                  |
| ICE (IFEU/IFUS — Brent/Gasoil/softs) | 530,600 (combo/futures_chain)      | **NONE AVAILABLE**   | **NO — needs ICE-data subscription ask**   | databento dropped ICE in 3-dataset lockdown; Massive carries NO ICE |

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
      market-tick-data-service@2c6425b `reclass_cboe_cash_index_no_provider.py`; APPLIED to live tradfi `_index` (snapshot
      `pre_cboe_cash_index_reclass_2026_06_22.parquet`); verified 1,614 index cells now empty_confirmed, VX
      futures_chain (134) preserved.
- [x] [SCRIPT] P1. **FX via yahoo launcher** — `launch-tradfi-bf-fx-ohlcv-24h.sh` (Yahoo daily ohlcv_24h, venue-routed;
      FX bypasses --source). FX capture itself was already code-complete in `_fetch_yahoo_fx` (venue=FX → Yahoo daily).
      — deployment-service@eab5aeb; dry-run verified.
- [x] [SCRIPT] P1. **Wave-launcher multi-source** — `LAUNCHER_FOR_VENUE` adds FX→fx-launcher; per-venue
      `VENUE_DATA_TYPES` map (FX=ohlcv_24h); FX added to PER_YEAR_VENUES; VM_NAME regex now venue+timeframe-agnostic.
      ICE intentionally absent (massive can't serve it). Dry-run confirms FX dispatch atoms appear (FX year=2025/2026 →
      fx launcher) and ICE stays out-of-scope. — deployment-service@eab5aeb.
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

## Temporary states + their canonical follow-up plans

- The CBOE-reclass + wave-launcher map are landed; the FX backfill drain + ICE credential-ask are the open todos above.
