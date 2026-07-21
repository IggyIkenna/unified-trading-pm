---
doc_type: issue
title:
  "MTDS has ZERO batch/historical download support for COINBASE-CDE — `download_batch` hard-fails 'Unsupported venue:
  COINBASE-CDE' for force AND skip legs on any day, including the venue's own real launch date"
summary:
  "Triaging `CEFI:COINBASE-CDE:trades`'s force/skip failures in the 2026-07-13 clean re-sweep
  (`data_pipeline_e2e_check_2026_07_10.md` todo 25), the original hypothesis (day=2026-07-09 predates
  `venue_start_dates['COINBASE-CDE']='2026-07-10'`, an honest absence) was DISPROVED by a fresh real re-verification at
  day=2026-07-10 (the venue's own real launch date): the force-leg VM's run.log shows `WARNING Venue COINBASE-CDE: no
  download_batch support: Unsupported venue: COINBASE-CDE. Supported venues: binance, bybit, coinbase, deribit, okx`
  followed by `SHARD_INCOMPLETE ... missing: ['COINBASE-CDE']` — MTDS's batch dispatcher has NEVER been wired to route
  COINBASE-CDE to any real adapter, on ANY day, regardless of the venue's UAC registration
  (`venue_constants.py`/`venue_mapping.py`/`venue_adapter_keys.py`/`market_data_categories.py` all declare it as a real,
  native-REST `coinbase_advanced_trade_api` venue with a `trades` capability since 2026-07-10). Only a LIVE websocket
  connector exists (`live/connectors/coinbase_cde_ws.py`) — no batch/historical REST adapter was ever built for MTDS.
  This is a genuine, reproducible, day-independent gap, not a checker artifact and not the same class as the
  already-fixed `coinbase_futures_spot_pair_zero_attempts_2026_07_12.md` (a different venue, COINBASE-FUTURES, whose gap
  was a symbol misclassification, not a missing adapter entirely)."
status: resolved
nature: notes
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [coinbase-cde, cefi, mtds, batch-adapter-gap, honest-coverage, data-correctness, new-venue-onboarding]
related:
  [
    ../data_pipeline_e2e_check_2026_07_10.md,
    coinbase_futures_spot_pair_zero_attempts_2026_07_12.md,
    wsfeedconnector_phase35_gap_2026_07_06.md,
    ../../../codex/02-data/data-pipeline-correctness-hard-rule.md,
  ]
created: 2026-07-13
parent_epic: mtds_mdps_master
priority: P1
source:
  [
    data_pipeline_e2e_check_2026_07_10.md clean re-sweep CEFI cluster triage (2026-07-13),
    real gsutil run.log evidence from 2 independent VM runs (day=2026-07-09 original sweep + day=2026-07-10 fresh
    re-verification),
  ]
assigned_vm: NA
resolved_by: market-tick-data-service@28ad6b38 + @971bdd35 (real-VM force-leg verified 2026-07-13)
locked_by:
execution_scope: local-only
estimate_class: brand-new
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.5
assigned_role: data_engineering
drift_direction: unknown
depends_on: []
---

# COINBASE-CDE has no MTDS batch/historical adapter at all

## What was found (real evidence, 2 independent VM runs)

**Run 1 — original 2026-07-13 clean re-sweep, day=2026-07-09** (`mtds-backfill-cefi-pipelinecheck-...-bedd7c`):
force/skip both failed `no_parquet_under:.../pipeline_mode=batch_tardis/.../venue=COINBASE-CDE/`. Initially hypothesized
this was an honest absence — `unified_api_contracts/registry/venue_mapping.py`'s `venue_start_dates` declares
`"COINBASE-CDE": "2026-07-10"` ("brand-new venue, no historical archive"), and the re-sweep's fixed day (2026-07-09) is
literally one day before that.

**Run 2 — fresh re-verification, day=2026-07-10 (the venue's own real launch date)**, run to test that hypothesis: still
failed, IDENTICALLY. The force-leg VM's real run.log
(`gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-backfill-cefi-pipelinecheck-20260713-145048-bedd7c/run.log`):

```
2026-07-13 14:53:34,047 WARNING Venue COINBASE-CDE: no download_batch support: Unsupported venue: COINBASE-CDE.
  Supported venues: binance, bybit, coinbase, deribit, okx
2026-07-13 14:53:34,049 WARNING market-tick-data-service: SHARD_INCOMPLETE date=2026-07-10 asset_group=CEFI —
  expected 1 venues, wrote 0, missing: ['COINBASE-CDE']
```

This **disproves the day-predates-launch hypothesis outright** — the failure is identical on the venue's own real start
date, so it is not a checker/day-choice artifact. `download_batch`'s per-venue dispatch (the MTDS batch/backfill entry
point that force/skip legs exercise) has a hardcoded allowlist that has never included COINBASE-CDE — the
`Supported venues:` list in the warning (`binance, bybit, coinbase, deribit, okx`) is the exact, complete set of
Tardis-routed CEFI venues; COINBASE-CDE, a **native-REST** venue with **zero Tardis coverage** (per its own adapter
docstring — `market_tick_data_service/adapters/... `, and the UAC registry note `"COINBASE-CDE": "coinbase_cde",

# 2026-07-10, native Advanced Trade REST, zero Tardis coverage`), was never given an equivalent native-REST batch path.

## What DOES exist for COINBASE-CDE in MTDS

Only a **live** websocket connector: `market_tick_data_service/live/connectors/coinbase_cde_ws.py` (registered in
`live/connectors/__init__.py`) — built and shipped 2026-07-10 per `wsfeedconnector_phase35_gap_2026_07_06.md`'s Progress
Log ("the live connector re-keyed `coinbase_futures_ws.py` → `coinbase_cde_ws.py`"). No batch/historical REST adapter
(the equivalent of, say, `market_tick_data_service/market_interface/adapters/onchain_perps/aster_adapter.py`'s
`fetch_trades`, which IS wired into `onchain_perp_batch_handler.py`'s per-venue dispatch) was ever built for
COINBASE-CDE's `trades` data_type.

## Why this is NOT the same as `coinbase_futures_spot_pair_zero_attempts_2026_07_12.md`

That doc diagnosed COINBASE-FUTURES (a DIFFERENT, older venue on Tardis's `coinbase-international` endpoint) silently
misclassifying its real SPOT_PAIR instruments as PERPETUAL inside an EXISTING, working Tardis dispatch path — a
symbol-shape classification bug, fixed with a one-line branch. COINBASE-CDE has **no dispatch path to misclassify inside
at all** — `download_batch` rejects the venue before ever reaching per-symbol/per-type logic. This is a missing-feature
gap (a new adapter needs to be built), not a routing bug in an existing one.

## Recommended fix (not attempted this session — a real adapter build, not a safely-scoped quick fix)

Build a native-REST historical/batch adapter for COINBASE-CDE `trades` (and confirm what else Coinbase's Advanced Trade
API can serve historically — candles/OHLCV is likely available per the reference-data adapter's own `get_ohlcv` method
in `instruments-service/instruments_service/reference_data/adapters/cefi/coinbase_cde.py`, which already hits
`GET /api/v3/brokerage/market/products/{product_id}/candles` — but MTDS's OWN batch dispatcher has no equivalent), then
wire it into MTDS's `download_batch` per-venue dispatch (the same place the `Supported venues:` allowlist is defined)
alongside the existing binance/bybit/coinbase/deribit/okx Tardis routes. Needs: (1) confirming whether Coinbase Advanced
Trade's public REST exposes a genuine historical trades/fills endpoint (not just recent/live market trades — Coinbase's
public `GET /products/{id}/trades` typically only returns a recent rolling window, not arbitrary historical days; if so,
COINBASE-CDE's real backfill window may be structurally limited to "since capture started," which the venue's
`_CDE_REGISTRATION_DATE = 2026-07-10` constant already anticipates), (2) the adapter itself (REST client, pagination,
rate-limit handling, canonical row mapping — same shape as `aster_adapter.py`), (3) wiring into `download_batch`'s
dispatch + the `Supported venues:` set, (4) unit tests + a real-VM force-leg re-verification proving real rows land.
Estimated as `brand-new` (new adapter, not a refactor) — a genuine multi-hour build, correctly out of scope for a
same-pass fix in this triage session.

## Not done this session

No adapter code was written; no attempt was made to confirm whether Coinbase's public REST actually supports
arbitrary-historical-day trade queries (the open question that determines whether a batch adapter can even be fully
historical, or only forward-capturing from whenever it's first run).

## 2026-07-13 (independent re-triage pass) — the IS-side (`instruments-service`) force/skip/live legs are a SEPARATE, benign finding — not a bug

This doc's scope is MTDS's `trades` data_type. The 2026-07-13 clean re-sweep's `is__CEFI__COINBASE-CDE` job (all 3 legs:
force/skip/live) ALSO shows as a "genuine failure" in the aggregate report
(`CEFI/COINBASE-CDE/2026-07-09 | force|skip|live | no_parquet_at:.../instrument_availability/.../venue=COINBASE-CDE/`),
but this is a **different, benign, checker-tooling-limitation case**, not a code bug and not the same root cause as the
MTDS batch-adapter gap above. Reading the real JSON report
(`_pipeline_e2e_check_sweep/reports_resweep_2026_07_13/is/is__CEFI__COINBASE-CDE/data_pipeline_e2e_check_is_2026_07_09.json`):
all 3 legs show `"manifest_ok": true, "manifest_status": "empty_confirmed"` — instruments-service correctly wrote an
honest `empty_confirmed` reference-data row for every leg, because day=2026-07-09 genuinely predates
`venue_start_dates["COINBASE-CDE"] = "2026-07-10"` (confirmed correct behavior — IS has no instrument reference data to
report for a venue before its own registered launch date, exactly as designed). The checker's `passed` criterion for the
IS force/skip/live legs requires an actual parquet object to exist under
`instrument_availability/by_date/day=.../venue=COINBASE-CDE/` (`write_verified`/`no_parquet_at`) — it has no
"honestly-empty-because-pre-launch" pass path, so a correct `empty_confirmed` day still counts as a checker-level
"genuine failure" in the aggregate report. This is the same class of checker-side gap already documented elsewhere this
session (the live-leg "no PROD-sampled instrument_id" limitation) — worth a future checker enhancement (treat
`manifest_ok=true, manifest_status=empty_confirmed` + a day before the venue's own `venue_start_dates` entry as a pass,
not a failure), but NOT an IS code bug and NOT re-diagnosed further this pass. No code changed. (repo:
instruments-service / market-tick-data-service checker tooling — investigation only, no fix applied)

## 2026-07-13 (adapter BUILT + wired + live-API verified; checker fairness fix shipped)

Operator approved building the adapter (this session). Shipped:

- **`market-tick-data-service@28ad6b38`** — NEW `adapters/coinbase_cde_batch.py` (+ 13 unit tests built from real probe
  payloads): native Coinbase Advanced Trade REST batch adapter for `trades` — public market-data endpoints, ticker
  start/end windowing, pagination, rate-limit handling, canonical rows with `instrument_id`/`instrument_type` stamped
  (the ASTER missing-column class cannot recur). Days before a contract first traded produce an honest absence, never
  fake rows. **Live-API verified: 1,285 real trades returned for 2026-07-11.**
- **`market-tick-data-service@971bdd35`** — wired into the batch dispatch (`umi_tick_provider.py`
  `venue_upper == "COINBASE-CDE"` branch → `fetch_coinbase_cde_batch`, lazy import), removing the "Unsupported venue:
  COINBASE-CDE" hard-fail.
- **IS-side checker fairness case (this doc's last section) FIXED**: `instruments-service@526d2ffd` — the IS checker now
  treats `manifest_ok + empty_confirmed + day < venue_start_dates[venue]` as a PASS (the benign pre-launch-day case this
  doc documented).
- **Residual (keeps this doc open)**: the real-VM force-leg re-verification proving rows land end-to-end through a
  launched backfill VM — requires the MTDS code tarball to include 28ad6b38/971bdd35 (tarball-refresh cron picks up
  pushed LDR commits automatically); tracked as the parent plan's targeted re-run item for `CEFI:COINBASE-CDE:trades` on
  a day ≥ 2026-07-10.

## RESOLVED 2026-07-13 — real-VM force-leg verification PASSED

`pipeline_e2e_check.py --day 2026-07-11 --asset-group CEFI --venue COINBASE-CDE --data-types trades --legs force` (fresh
tarball carrying 28ad6b38+971bdd35): `CEFI:COINBASE-CDE:trades | force | passed | Parquet=52 | exit 0` — the new
native-REST adapter fetched real trades through a launched backfill VM and wrote 52 parquet chunks end-to-end. The
"Unsupported venue" hard-fail is gone. Status flipped to resolved.
