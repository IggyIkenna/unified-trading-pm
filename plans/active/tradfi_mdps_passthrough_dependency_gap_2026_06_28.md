---
doc_type: plan
title: MDPS — TradFi processed-candle passthrough + dependency-checker instrument_id fix
summary:
  "Close the TradFi MDPS gap: MDPS produces right-edge processed candles for TradFi ohlcv_1m (passthrough/normalization)
  so features-delta-one has an upstream, and fix the dependency-checker bug that looks up instrument_id when the
  manifest stores it blank for CME futures."
status: active
nature: process
asset_group: [tradfi]
stage: [data, features]
repos: [market-data-processing-service]
scope: [engineer, admin]
tags: [tradfi, mdps, passthrough, ohlcv_1m, dependency-checker, cme, instrument-id, bar-edge]
related:
  [
    ./mdps_features_reduced_artifact_tracker_2026_06_28.md,
    ../active/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md,
    ../epics/mtds_mdps_master.md,
  ]
created: 2026-06-28
parent_epic: mtds_mdps_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-28
locked_by: NA
locked_since:
supersedes:
superseded_by:
depends_on:
source: [../active/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md]
---

# MDPS — TradFi processed-candle passthrough + dependency-checker fix

Per issue `features_delta_one_tradfi_mdps_dependency_gap_2026_06_24` (P0): TradFi has **no MDPS processed-candle
layer**. MTDS writes `ohlcv_1m`/`ohlcv_1s` straight from Databento (no `trades`), while features-delta-one expects MDPS
trades→candle aggregates (the CeFi shape). Three VM runs failed with "No upstream MDPS data for CME:FUTURES:ES". If the
candle is the universal artifact, TradFi must pass through MDPS so its bars carry the same schema (minus the CeFi-only
book columns) and the same right-edge contract.

**Execution model:** Sonnet — bounded single-repo work against a precise issue diagnosis. The 3-layer format mismatch
(Massive raw `trades` → MDPS `trades` → build-continuous reads `ohlcv_1m`) needs care but is well-scoped.

## Two defects to close

1. **No TradFi MDPS pass.** Either (a) a TradFi-specific MDPS adapter that reads `ohlcv_1m`/`ohlcv_1s` and emits the
   canonical processed-candle (passthrough + right-edge stamp + schema-align), or (b) a features-side read path — the
   issue prefers MDPS doing the translation so the candle stays the single artifact. **Adopt (a).**
2. **Dependency-checker `instrument_id=''` bug.** MTDS manifest stores blank `instrument_id` for CME futures;
   `dependency_checker.py` stores `("CME", "")` but looks up `("CME", "ES")` → always 0 candles → false "no upstream".

## Todos

- [ ] [IMPLEMENT] P0. TradFi MDPS passthrough adapter: read TradFi `ohlcv_1m` (+ `ohlcv_1s` where present), emit
      canonical processed candles aligned to the shared schema (book columns null), **right-edge `t_close`** per the
      bar-edge convention (TradFi Databento open-edge alias already converted at MTDS ingestion — assert, don't
      re-shift). Resolve the `data_type=trades` vs `ohlcv_1m` naming mismatch in build-continuous. — Gate:
      `process     --TRADFI` over one CME ES day writes processed candles readable by features-delta-one.
- [ ] [IMPLEMENT] P0. Fix `dependency_checker.py` to key on the manifest's actual `instrument_id` (blank-aware): match
      on (venue, symbol) via the canonical instrument key, not a literal blank string. — Gate: the checker reports the
      true candle count for CME:FUTURES:ES (non-zero where data exists); a unit test covers the blank-id case.
- [ ] [TEST] P0. Tests: passthrough preserves OHLCV values + right-edge timestamps (1m bar at 00:01:00 covers
      [00:00:00,00:01:00)); dependency-checker blank-id resolution. — Gate: tests pass in MDPS `quality-gates.sh`.
- [ ] [VERIFY] P0. Full-run: MDPS TradFi pass over a real CME ES month-slice on real infra, then run features-delta-one
      `technical_indicators` against it and confirm it no longer fails "No upstream MDPS data". — Gate: named commands +
      GCS paths + the feature group writing non-zero rows for ES.
- [ ] [AGENT] P0. MDPS QG green; quickmerge `--agent --files`; flip the issue doc to `resolved` with the sha + evidence
      in the SAME turn. — Gate: QG green; CI `quality-gates-v2` green; issue `status: resolved`.

## Current-state delta (audited 2026-06-28)

- **MTDS reality:** `market-data-tick-tradfi-prd-*/_index/` carries ~700k captured `ohlcv_1m`/`ohlcv_1s` rows direct
  from Databento — NO `trades`. MDPS has no trades input to aggregate.
- **Passthrough adapter exists but mismatches:** `ohlcv_passthrough.py` is registered (ohlcv_1s/1m/15m/24h) but the
  killed VM run (`mdps-backfill-tradfi-...`) showed a 3-layer format mismatch — Massive raw `data_type=trades` → MDPS
  output `data_type=trades` → build-continuous reads `data_type=ohlcv_1m`; plus filename `ESH0.parquet` vs Databento
  `CME:FUTURE:ES-<date>`. Output must emit `data_type=ohlcv_1m` on the canonical processed path.
- **Dependency-checker bug:** CME manifest rows store `instrument_id=''`; `dependency_checker.py` looks up `(CME, ES)` →
  always 0 candles → false "No upstream MDPS data".
- **Decision (adopted):** Option B — MDPS passthrough emits `ohlcv_1m` + build-continuous reads it (candle stays the
  single artifact), over Option A (features read MTDS ohlcv direct + inline panama roll).

## Notes

- This unblocks TradFi shards in Plan 6 (coverage) and Plan 7 (benchmark) — a CME ES month becomes a RUNNABLE shard.
- Related: features-volatility-tradfi has the same gap CONFIRMED (issue); fixing the MDPS pass should serve both, but
  this plan's scope is the MDPS layer + dependency checker only — a separate features-volatility plan owns its read path
  if one is still needed after (a) lands.
