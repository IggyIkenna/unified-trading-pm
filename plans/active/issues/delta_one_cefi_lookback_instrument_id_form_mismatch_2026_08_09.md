---
doc_type: issue
title:
  "features-service delta_one: lookback-validation candle count is always 0 for CEFI instruments passed in canonical
  (MVP-universe) id form"
created: 2026-08-09
author: slot-9
assigned_vm: planning
status: open
tags: [data-correctness, features-service, delta_one, cefi, instrument-id, manifest]
source:
  [
    citadel_satellite_ao_dispatch_batch1_2026_08_08.md item "features-service:
      recompute the corpus for the intraday BTC mean-reversion cs-ML feature",
  ]
summary:
  "`features-service` delta_one's `--feature-group returns` / `--feature-group statistical_anomaly` batch compute for
  CEFI/BTC cannot complete — it fails both the lookback pre-flight validation AND th..."
nature: process
asset_group: cefi
stage: [meta]
repos: [features-service]
scope: [engineer, admin]
related: [cefi_consolidated_closeout_2026_07_18]
parent_epic: cefi_master
resolved_by: null
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
---

## What I found

`features-service` delta_one's `--feature-group returns` / `--feature-group statistical_anomaly` batch compute for
CEFI/BTC cannot complete — it fails both the lookback pre-flight validation AND the MVP-universe instrument filter,
depending which instrument-id FORM is passed, because the two subsystems expect DIFFERENT id forms for the same
instrument and nothing translates between them:

1. **Canonical form** (`BITGET-FUTURES:PERPETUAL:BTCUSDT`, no dash, no `@LIN` suffix) — this is what the delta_one
   feature corpus itself already writes to GCS (e.g.
   `gs://features-cefi-prd-central-element-323112/delta_one/by_date/day=2026-05-03/feature_group=momentum/timeframe=15s/BITGET-FUTURES:PERPETUAL:BTCUSDT.parquet`,
   already-shipped feature groups), and what the features MVP-universe instrument filter accepts. Passed to the CLI
   (`--instruments "BITGET-FUTURES:PERPETUAL:BTCUSDT"`), the MVP-universe filter passes, BUT
   `DependencyChecker._count_candles_for_lookback` (features-service/delta_one/app/core/dependency_checker.py:854) looks
   this id up against the availability-manifest's `(venue, instrument_id)` index and finds **0 rows** — because the
   manifest stores the RAW Tardis-vendor id form for this same instrument (`BITGET-FUTURES:PERPETUAL:BTC-USDT@LIN`,
   confirmed via `read_availability_index` — capture_status=`captured` for `date=2026-05-03`). Lookback validation FAILS
   with `0/5472 candles`, even though the underlying candle parquet genuinely exists in GCS
   (`gs://market-data-tick-cefi-prd-central-element-323112/processed_candles/by_date/day=2026-05-03/pipeline_mode=batch_tardis/timeframe=15s/data_type=trades/instrument_type=PERPETUAL/venue=BITGET-FUTURES/BITGET-FUTURES:PERPETUAL:BTCUSDT.parquet`).

2. **Raw/manifest form** (`BITGET-FUTURES:PERPETUAL:BTC-USDT@LIN`) — passed to the CLI instead, the lookback
   candle-count now finds the manifest row (would pass), BUT the MVP-universe instrument filter rejects it outright:
   `WARNING No instruments remain after MVP universe filter for group=returns asset_group=CEFI (started with 1)` — 0/1
   instruments survive, so the group produces 0 output and the run fails with `record_empty(...) requires FetchEvidence`
   (correctly refusing to silently stamp a false empty).

**Neither id form lets the CLI both pass the MVP-universe filter AND pass lookback validation** — the two checks
disagree about which form is canonical for this instrument. Reproduced live 2026-08-09 (see commands below); this is NOT
specific to BTC — every BITGET-sourced CEFI instrument with a manifest raw id containing a `-`/`@` suffix is almost
certainly affected the same way (a sampling of the manifest for `date=2026-05-03` shows this raw-dash-@LIN form is the
norm for BITGET-FUTURES perpetuals, not an isolated BTC quirk).

### Repro (features-service repo, `.tabs/9/features-service`)

```bash
# Form 1 — canonical (matches GCS feature-output filenames + MVP universe) — FAILS lookback (0/5472):
ENVIRONMENT=production uv run python -m features_service.delta_one \
  --operation compute --mode batch --asset-group CEFI \
  --start-date 2026-05-03 --end-date 2026-05-03 \
  --feature-group returns --instruments "BITGET-FUTURES:PERPETUAL:BTCUSDT" --preflight-only

# Form 2 — raw manifest id (matches availability-manifest instrument_id) — FAILS MVP-universe filter (0/1 remain):
ENVIRONMENT=production uv run python -m features_service.delta_one \
  --operation compute --mode batch --asset-group CEFI \
  --start-date 2026-05-03 --end-date 2026-05-03 \
  --feature-group returns --instruments "BITGET-FUTURES:PERPETUAL:BTC-USDT@LIN" --preflight-only
```

Manifest check used to find the raw form (`unified_trading_library.read_availability_index` against
`market-data-tick-cefi-prd-central-element-323112`, `date=2026-05-03`): confirms `BITGET-FUTURES:PERPETUAL:BTC-USDT@LIN`
capture_status=`captured`, while `BITGET-FUTURES:PERPETUAL:BTCUSDT` does not appear in the manifest at all.

## Why it matters

This blocks BOTH open todos in `citadel_satellite_ao_dispatch_batch1_2026_08_08.md` that need a CEFI delta_one
`returns`/`statistical_anomaly`/`volatility_realized` backfill for BTC (the item this issue was filed from, and its
sibling "BTC trend feature corpus recompute" P2.11.16 item) — neither can reach done-when (non-null feature columns in
GCS, manifest-verified) while this id-form mismatch stands. It is also a latent blocker for ANY future CEFI delta_one
backfill that runs the CLI against BITGET-sourced instruments with a full historical/lookback window, since the lookback
pre-flight check is what silently fails, not a downstream compute step — i.e. it fails BEFORE any candles are read, for
every feature_group, not just `returns`/`statistical_anomaly`.

This is a genuine correctness gap in the shared `DependencyChecker` (features-service core, not touched by any of the
two blocked todos' own scope) — the `_count_candles_for_lookback` docstring already documents ONE canonical/raw-id
divergence it handles (CEFI/DEFI full-id vs TradFi bare-symbol vs CME chain-bundle blank), but does not yet handle a
vendor-raw-vs-service-canonical divergence WITHIN CEFI itself.

## Recommended decision

The fix belongs in `features_service/delta_one/app/core/dependency_checker.py`'s `_count_candles_for_lookback` (and/or
`_build_captured_index`) — translate the CLI/MVP-universe canonical instrument_id to the raw manifest id form (or vice
versa) before the `(venue, instrument_id)` manifest lookup, the same way the existing bare-symbol/chain-bundle fallback
chain already tries multiple key forms. This is shared, cross-cutting dependency-checker code (used by every delta_one
feature_group's lookback validation, not scoped to `returns`/`statistical_anomaly`) — too broad a blast radius to patch
inline under a single P2 corpus-recompute todo; needs its own properly-scoped fix + regression test (one BITGET-sourced
instrument with a `-`/`@`-suffixed raw manifest id, asserting lookback validation PASSES via the canonical CLI id).

- [ ] [DATA] P1. Fix `DependencyChecker._count_candles_for_lookback`
      (features-service/delta_one/app/core/dependency_checker.py) to translate between the CEFI canonical instrument_id
      form (`VENUE:TYPE:SYMBOL`, no separator/suffix — what the MVP-universe filter + feature-output filenames already
      use) and the availability-manifest's raw vendor instrument_id form (Tardis-sourced BITGET ids carry a
      `-`/`@LIN`/`@INV` suffix) when building/querying the `(venue, instrument_id)` captured-dates index, so lookback
      validation finds real manifest rows regardless of which form the caller passes. Add a unit test covering a
      BITGET-FUTURES perpetual with a raw manifest id containing `-USDT@LIN` (e.g. reproduce the `BTC-USDT@LIN` vs
      `BTCUSDT` case from this issue). Repo: features-service.
- [ ] [DATA] P2. Once the above lands, re-run this todo's own scope
      (`citadel_satellite_ao_dispatch_batch1_2026_08_08.md` "features-service: recompute the corpus for the intraday BTC
      mean-reversion cs-ML feature") — backfill `returns` + `statistical_anomaly` feature groups for cefi/BTC over the
      existing paper-trading window (`day=2026-04-22`, `day=2026-05-01..2026-05-03` — the only days currently present
      under `gs://features-cefi-prd-central-element-323112/delta_one/by_date/`), verify non-null
      `reversion_zscore_60m`/`reversion_zscore_240m` columns land (manifest-row-verified), and run
      `features-status --check-drift`, recording the result. Repo: features-service.
- [ ] [DATA] P2. Same re-run for the sibling P2.11.16 todo ("BTC trend feature corpus recompute" —
      `btc_trailing_return_{1,3,6,12}m` + `btc_realized_vol`, `returns` + `volatility_realized` groups) once the
      dependency-checker fix lands. Repo: features-service.

## Progress Log

- 2026-08-09 (slot-9): Filed from `citadel_satellite_ao_dispatch_batch1-006` (the "recompute the corpus for the intraday
  BTC mean-reversion cs-ML feature" todo). Investigated why the backfill CLI could not complete for either instrument-id
  form; confirmed genuine candle data exists in both GCS (`market-data-tick-cefi-prd-...`) and the availability manifest
  for the target dates, ruling out an honest-absence/missing-data explanation — this is purely an id-form mismatch
  inside the dependency checker. Did not attempt the fix inline (shared core code, out of this todo's scope) — filed
  this issue + the two follow-up todos instead.
