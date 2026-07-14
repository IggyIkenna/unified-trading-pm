---
doc_type: issue
title:
  MTDS sports odds-api ingestion re-serves the SAME stale cached fixture odds under every new day's partition for
  low-activity leagues — root cause of the exact-68.6% ML-readiness cluster (9 dates) + 8 other sub-95% odds days
summary:
  "Diagnosis of sports_p2_features_history_to_ml_ready-003 (9-day exact-68.6% ML-readiness cluster). Root cause is NOT
  simple honest-absence from low fixture volume (that's a contributing factor, but not sufficient to explain the
  finding) — it is a genuine MTDS odds-api ingestion bug: when the live odds pull for a low-activity league (Russia
  Premier League, Australia A-League, etc.) returns no NEW fixture for a given day, the ingest path re-serves the LAST
  KNOWN cached odds snapshot for that league and writes it under the CURRENT day's `day=<D>` partition as if it were
  fresh. Proven with 5 independent dates (2025-09-02/03/09, 10-07, 11-11) all carrying the byte-identical Russia Premier
  League fixture_id=a4a57e155f2e9d54fd7bca72470db842 / bookmaker=bovada / kickoff_utc=2022-03-05T16:00:00Z row, and a
  second instance (Australia A-League fixture_id=237d3bb63e77fb7661f7aa531cb3c609, kickoff_utc=2025-05-31) repeating on
  09-03 and 09-09. Because the re-served row is a stale singleton (never actually re-scraped at multiple horizons for
  the real kickoff), it only ever lands in ONE MDPS horizon bucket (T-24h or T-0), so every downstream cross-horizon
  odds_features column (velocity_*, acceleration_*, steam_*, clv_*, delta_prob_6h/1h_*, move_direction/sign_*,
  market_reversal/chop_*, exchange_price_*, velocity_prob_*/acceleration_prob_*  — 43/137 columns) is honestly NaN for
  that row — a fixed 94/137=68.6131% non-null ratio independent of the day's row count, which is why the same exact
  percentage recurs on days with 1 fixture AND on the 3-fixture day (2025-10-23). 8 of the 9 cluster dates fall inside
  the Sep 1-9 / Oct 6-14 / Nov 10-18 2025 FIFA international windows, when domestic top leagues pause and
  low-market-interest leagues dominate the day's (already thin) fixture count with stale re-served rows.
  features-service's odds_features exporter and ml_readiness_check.py are both behaving CORRECTLY (honest-absence
  discipline, no silent placeholders, no compute bug) — the defect is entirely upstream in MTDS's raw odds-api
  ingestion/caching for low-activity leagues."
status: open
nature: issue
asset_group: [sports]
stage: [data]
repos: [market-tick-data-service, features-service]
scope: [engineer]
tags: [sports, odds, mdps, data-correctness, honest-absence, ml-readiness, stale-cache]
related:
  [
    plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    plans/active/sports_features_readiness_for_predictions_2026_06_20.md,
    codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-14
parent_epic: sports_master
assigned_vm: NA
execution_scope: local-only
priority: P1
source: [data_engineering worker, slot 4, sports_p2_features_history_to_ml_ready-003 diagnosis 2026-07-14]
resolved_by:
locked_by:
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
---

# MTDS sports odds-api ingestion re-serves stale cached fixture odds under new day partitions

> **NOTIFY-OPERATOR (cross-repo data-correctness finding).** This is not a features-service bug and not simple
> honest-absence — MTDS's odds-api ingestion for low-activity leagues appears to cache the last successfully fetched
> fixture's odds and re-emit that SAME row (unchanged fixture_id/kickoff_utc/bookmaker) under every subsequent day's
> `day=<D>` GCS partition when the live pull returns nothing new, instead of correctly recording zero rows /
> honest-absence for that league on that day. The `verify_ml_readiness.py` gate correctly flags the downstream symptom
> (85–95% and an exact-68.6% floor); this doc traces it to the actual root cause.

## Evidence (GCS paths + real data, 2026-07-14)

**The gate + its downstream symptom**
(`features-service/scripts/sports/verify_ml_readiness.py --start-date 2025-09-01 --end-date 2025-11-30 --bucket features-sports-prd-central-element-323112`):
74/91 pass, 17 fail, avg 95.3%. 9 of the 17 fail at EXACTLY 68.6131% (94/137 non-null cells): 2025-09-02/03/04/09/10,
10-07/14/23, 11-11/13. The other 8 fail between 70.1% and 94.9% (09-17/18/25, 10-20/21, 11-19/27).

**Column-level analysis** (`features_service.sports.calculators.odds_columns.ODDS_COLUMNS`, 137 total) of every one of
the 9 cluster dates' `odds_features/features.parquet` at T-24h/T-1h: the SAME 43 columns are 100% NaN on every date,
regardless of row count (1 fixture on 8/9 dates, 3 fixtures on 2025-10-23) — `odds_movement_{home,draw,away}`,
`velocity_{home,away}_{24h_to_6h,6h_to_1h,1h_to_0}`, `acceleration_{home,away}`,
`steam_{detected,magnitude}_{home,away}`, `exchange_price_{home,draw,away}`, `{sharp_,}clv_{home,draw,away}`,
`clv_direction_{home,draw,away}`, `delta_prob_{6h,1h}_{home,away}`, `{velocity,acceleration}_prob_{home,away}`,
`move_{direction_agreement,sign_consistency}_{home,away}`, `market_{reversal_flag,chop_score}_{home,away}`. 94/137 =
68.6131% — the fixed ratio, independent of row count. The other 8 sub-95% dates show the identical column SET as
_partially_ null (some fixtures in coverage, some not) — same root cause, non-degenerate case.

**Why the block is always-null**: these columns all require ≥2 distinct horizon snapshots (velocity/acceleration/CLV/
delta_prob/move-agreement) or a specific bookmaker tier that didn't quote (`exchange_price_*`, from
`compute_tier_features`). `features_service/sports/exporters/odds_features_exporter.py:_find_best_snapshot` (by design,
per its own docstring) falls back to the nearest earlier snapshot when the exact target horizon is absent — so when only
ONE snapshot horizon exists for a fixture, both the "T-24h" and "T-1h" export rows are populated from that single
snapshot, and everything that needs a second, distinct snapshot is honestly NaN. This part of features-service is
correct, honest-absence behavior.

**Root cause — traced into MDPS's bucketed odds**
(`market-data-tick-sports-prd-central-element-323112/processed/ by_date/day=<D>/pipeline_mode=batch_mdps_odds_horizon_bucket/asset_group=sports/data_type=odds_horizon_bucket/`):
every cluster date has only 1-3 `league_id=<x>/timeframe=<y>/bucketed.parquet` shards total, each with exactly ONE
`horizon_name` value (never the full T-24h→T-0 ladder). Inspecting the Russia Premier League shard's row content across
5 INDEPENDENT dates:

| date       | fixture_id                       | bookmaker | kickoff_utc          | horizon |
| ---------- | -------------------------------- | --------- | -------------------- | ------- |
| 2025-09-02 | a4a57e155f2e9d54fd7bca72470db842 | bovada    | 2022-03-05T16:00:00Z | T-24h   |
| 2025-09-03 | a4a57e155f2e9d54fd7bca72470db842 | bovada    | 2022-03-05T16:00:00Z | T-24h   |
| 2025-09-09 | a4a57e155f2e9d54fd7bca72470db842 | bovada    | 2022-03-05T16:00:00Z | T-24h   |
| 2025-10-07 | a4a57e155f2e9d54fd7bca72470db842 | bovada    | 2022-03-05T16:00:00Z | T-24h   |
| 2025-11-11 | a4a57e155f2e9d54fd7bca72470db842 | bovada    | 2022-03-05T16:00:00Z | T-24h   |

The SAME fixture (kickoff over 3.5 years in the past) is re-emitted byte-identically under 5 different `day=`
partitions, spanning 2 months of wall-clock scrape time (`fetch_utc` advances each day; every other field —
`fixture_id`, `commence_time`, `kickoff_utc`, `bm_time`, `price` — is frozen). A second instance confirms this isn't a
one-off: Australia A-League `fixture_id=237d3bb63e77fb7661f7aa531cb3c609` (bookmaker betmgm, kickoff_utc
2025-05-31T09:52:00Z) repeats identically on 2025-09-03 and 2025-09-09. Raw pre-bucket ticks
(`raw_tick_data/by_date/day=2025-10-23/pipeline_mode=batch_odds_api/.../venue=PINNACLE/league_id= SOCCER_RUSSIA_PREMIER_LEAGUE/instrument_type=odds/data_type=trades/ticks.parquet`)
confirm the same pattern one level upstream: 49 rows, all with `bm_time=2022-03-04T16:19:40Z` and `commence_time` values
in March 2022, but `fetch_utc=2025-10-23T12:00:00Z` (today's real scrape timestamp) and `date=2025-10-23` (today's
partition).

**Why this produces the exact 68.6% cluster and not just generic sub-95% noise**: on FIFA international-break weeks (Sep
1-9, Oct 6-14, Nov 10-18 2025 — 8 of the 9 cluster dates fall inside these windows), most domestic leagues pause, so
real fixture volume for the day's odds_features already craters to near-zero. When the only rows contributed are these
stale re-served singletons (not real, live-scraped fixtures), 100% of that day's fixtures hit the always-null column
block, giving the exact deterministic 94/137 ratio. On days with a few genuine live fixtures mixed with a stale
re-serve, the ratio lands somewhere in the partial 70-95% range (the other 8 dates).

## Non-actions (explicit)

- **verify_ml_readiness.py / ml_readiness_check.py need no code change** — they correctly measure honest coverage; the
  gate is doing its job by surfacing this.
- **odds_features_exporter.py's nearest-earlier-snapshot fallback is correct, documented behavior** — not the bug.
- **No relaunch of the GW recompute** — this issue is entirely on the MTDS odds side, untouched by the
  derived/fixture-features recompute this plan's other todos concern.

## Todos

- [ ] [CODE] P1. **market-tick-data-service: stop re-serving a stale cached fixture as if it were a fresh day's odds.**
      Find the sports odds-api ingestion/backfill path that populates
      `processed/by_date/day=<D>/pipeline_mode=batch_mdps_odds_horizon_bucket/.../data_type=odds_horizon_bucket/` for
      low-activity league_ids (start with `soccer_russia_premier_league`, `soccer_australia_aleague`) and determine why
      a fixture whose `kickoff_utc` is far in the past (or far from the target `day=<D>`) gets written under that day's
      partition at all. Likely candidates: (a) the raw odds-api historical/current-odds fetch falls back to the last
      cached response when the live query for that league/day returns empty, and that fallback response gets persisted
      under the new day instead of being recognized as stale and dropped; or (b) a date-filter is missing between the
      odds-api response and the GCS write, so any fixture the API still happens to return (regardless of how old) gets
      bucketed. Fix: either drop rows where `kickoff_utc` falls outside a sane window of `day=<D>` (record
      honest-absence/zero rows instead), or fix the fetch to only return live/ current-window fixtures per league.
- [ ] [DATA] P2. **market-tick-data-service: sweep for the extent of the contamination.** Once the ingestion bug is
      fixed, scan `processed/by_date/*/pipeline_mode=batch_mdps_odds_horizon_bucket/.../data_type=odds_horizon_bucket/`
      for repeated (fixture_id, bookmaker_key, kickoff_utc) tuples spanning multiple `day=` partitions (the same
      signature found here) to size the blast radius across leagues/dates, and purge/re-derive the contaminated shards +
      their downstream `odds_features` + manifest rows. Single-walk discipline applies — do this via the manifest index,
      not a fresh whole-corpus GCS walk.
- [ ] [DATA] P3. **Re-run `verify_ml_readiness.py --start-date 2025-09-01 --end-date 2025-11-30` after the P1/P2 fix**
      to confirm the 17 failing dates clear (or shrink to genuine honest-absence-only misses), then reassess whether the
      strict per-day gate (vs the already-precedented aggregate ≥95% pass bar from 2026-07-12) is still the right pass
      criterion for near-empty international-break days.
