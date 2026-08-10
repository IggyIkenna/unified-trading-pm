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
repos: [market-data-processing-service, market-tick-data-service, features-service]
scope: [engineer]
tags: [sports, odds, mdps, data-correctness, honest-absence, ml-readiness, stale-cache]
related:
  [
    plans/archive/2026_07/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    plans/active/sports_features_readiness_for_predictions_2026_06_20.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
created: 2026-07-14
author: unknown
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
context_scope:
  [
    market-data-processing-service/market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py,
    features-service/scripts/sports/verify_ml_readiness.py,
    features-service/features_service/sports/data/writer.py,
    /codex/02-data/honest-absence-downstream-handling.md,
    /plans/epics/sports_master.md,
    market-tick-data-service/scripts/sweep_sports_odds_horizon_bucket_zombie_contamination_2026_07_27.py,
  ]
---

> **✅ OPERATOR RULING 2026-08-08 — switch to the precedented aggregate >=95% pass bar.** The open todo asks whether the
> strict per-day `verify_ml_readiness.py` gate is still right for near-empty international-break days. Ruled: **use the
> aggregate >=95% bar** (already precedented 2026-07-12). The exact-68.6% floor on FIFA-international-break weeks is
> honest absence, not a data defect, and a gate that fails on honest absence is measuring the wrong thing. **Ordering
> constraint unchanged**: the P1/P2 zombie-tick fixes in this doc must land FIRST, and the re-run must confirm the floor
> is gone before the bar is switched — otherwise the change would mask a real regression rather than remove a false one.
> Implemented by `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md`.

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

## Verification + mechanism refinement (2026-07-14 tick-4 diagnosis dispatch — adversarial re-check, all original evidence CONFIRMED, root-cause mechanism CORRECTED)

Independently re-verified from the real buckets (fresh downloads, per-column analysis over `ODDS_COLUMNS` at
T-24h/T-1h):

- **Column block CONFIRMED**: 3 cluster days (09-02, 09-09, 10-23) each show the IDENTICAL 43-column all-NULL set
  (intersection == union), zero partial-null columns, exact 94/137 = 68.6131% non-null; passing day 2025-09-06 = 100.0%
  with zero NULL columns. **All 43 columns match `WRITE_GATE_CONFIG.sparse_columns["odds_features"]` prefixes (0
  unmatched)** — the entire block is already documented-sparse in the WriteGate
  (`features_service/sports/data/writer.py:181-200`), which is the P1d-archived proposal's premise
  (`plans/archive/2026_07/sports_p1_golden_window_features_2026_06_27.md` 2026-07-12 entry: per-date gate could exempt
  the WriteGate sparse set — still unimplemented).
- **Root-cause mechanism CORRECTED — it is NOT an MTDS client-side cache re-serve.** Raw
  `day=2025-09-02/.../venue=BETFAIR_EX_UK/league_id=SOCCER_EPL/.../ticks.parquet` shows LIVE scrapes in the same pass:
  fresh `bm_time=2025-09-02T11:55:16Z`, 11 EPL events all kicking off Sep 13-20 (next matchday after the break,
  15,810-25,890 min out — correctly beyond every horizon bucket). The staleness is UPSTREAM: the-odds-api itself keeps
  returning frozen bookmaker boards for dead/idle league keys (`soccer_russia_premier_league` board frozen at the
  Mar-2022 CSKA Moscow fixture; `soccer_australia_aleague` off-season board frozen at a 94-days-past fixture,
  `minutes_to_kickoff=-135,488`). Original P1 candidate (a) (cache fallback) is DISPROVEN; candidate (b) (missing
  date/staleness filter) is CONFIRMED, with the precise locus:
  **`market-data-processing-service/market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py`** —
  buckets purely on `bm_minutes_to_kickoff` (line ~374/487); its "staleness cap" is only the bm-relative deviation from
  the bucket target (`TIER1_HORIZONS` ±60/45/.../5 min), and `bm_minutes < 0 → T-0`; it NEVER checks `staleness_seconds`
  (fetch_utc − bm_time ≈ 3.5 YEARS for the zombie) or fetch-vs-kickoff distance. A frozen board whose
  bm_minutes_to_kickoff happens to sit near a target (russia: 1423 ≈ T-24h) re-buckets under EVERY fetch day forever; a
  frozen in-play/past board (A-League: −113) lands T-0/HT forever. Raw MTDS ingestion honestly records what the live API
  returned (fetch_utc real, staleness_seconds carried) — the defect is the processed layer ACCEPTING arbitrarily stale
  ticks.
- **Third event class found (NOT contamination): single-snapshot REAL fixtures.** The other 2 events on 2025-10-23 are
  genuine China Superleague fixtures (kickoff 2025-10-24T11:35Z, fresh bm_time 2025-10-23T11:5x, 11 bookmakers) caught
  at exactly ONE horizon (T-24h) by the once-daily ~12:00Z snapshot wave; their T-12h→T-0 snapshots fall on the kickoff
  day and land under `day=2025-10-24` (a passing day). Honest absence within day=D's partition, structural
  (fetch-day-partitioned atom), not a bug. Partial-range days confirmed as the graduated form: 2025-10-20 = 4 events
  100% (full ladder) + 9 events 79.6-89.8% (14-28 null cols, shallow ladders) → 91.1% day total, no zombies required to
  explain.
- **Break-day honest absence PROVEN (nothing to re-capture)**: on 2025-09-02 every covered league's live board shows
  zero fixtures within 24h — next kickoffs MLS Sep 7, Argentina Sep 11+, EPL Sep 13-20. The odds-api historical endpoint
  has nothing more to serve for these days (the boards WERE fetched live and contained no in-window fixtures) —
  **re-capture cost = 0 because re-capture target = ∅; no fetch plan filed, quota untouched.** After the P2 purge the 9
  cluster days become 0-row days, so P3 must pair the purge with gate semantics for zero-in-window-fixture days (vacuous
  pass or expected-fixture-aware skip) + the P1d sparse-column exemption for shallow-ladder days.

## Todos

> **PARTIAL FIX LANDED 2026-07-16 — `MDPS@3bf56ff` (lookahead-leak leg).** The `bm_minutes < 0 → T-0` half of the P1
> locus below is **fixed**: post-kickoff rows are now REJECTED (`-1`) in both `assign_horizon_bucket` (which hardcoded
> `return N_BUCKETS - 1` before any staleness check) and `assign_horizon_buckets_vectorised` (where the override ran
> AFTER the staleness rejection and resurrected already-dropped rows). This kills the **A-League zombie class** (frozen
> in-play/past boards at `bm=-113` / `minutes_to_kickoff=-135,488` that "land T-0/HT forever") — they no longer reach
> any bucket. **What REMAINS open in P1**: the `staleness_seconds` (`fetch_utc − bm_time`) cap and the
> `kickoff_utc`-vs-fetch-day check. Those still matter for the **Russia Premier League zombie class**, which is
> **pre-kickoff-positive** (`bm≈1423 ≈ T-24h`) and therefore **untouched by the post-kickoff fix** — a 3.5-year-stale
> board whose `bm_minutes` happens to sit near a target still re-buckets under every fetch day. Full-census evidence +
> blast radius (T-0 = 39.83% post-kickoff, 146,738/368,366 rows; all 7 other timeframes PROVEN CLEAN at 0/4,151,352):
> `./sports_halftime_odds_sfi_vs_inplay_2026_07_16.md` § Progress Log 2026-07-16.

- [x] ✅ [CODE] P1. **Stop stale/zombie ticks at bucket assignment (fix locus: MDPS, not MTDS raw ingestion — see
      refinement above).** Primary fix in
      `market-data-processing-service/.../adapters/sports/bucket_assignment_adapter.py`: drop rows whose
      `staleness_seconds` (fetch_utc − bm_time) exceeds a sane cap (hours-scale, ≥ the largest horizon window) or whose
      `kickoff_utc` is far outside the fetch day's horizon reach, BEFORE horizon assignment — record honest-absence/zero
      rows for that league-day instead. Optionally also drop >N-days-past-kickoff rows at MTDS raw ingestion, but the
      raw layer honestly recording the live API response is defensible; the processed layer accepting 3.5-year-stale
      ticks is the bug. Original sub-question retained below for context: Find the sports odds-api ingestion/backfill
      path that populates
      `processed/by_date/day=<D>/pipeline_mode=batch_mdps_odds_horizon_bucket/.../data_type=odds_horizon_bucket/` for
      low-activity league_ids (start with `soccer_russia_premier_league`, `soccer_australia_aleague`) and determine why
      a fixture whose `kickoff_utc` is far in the past (or far from the target `day=<D>`) gets written under that day's
      partition at all. Likely candidates: (a) the raw odds-api historical/current-odds fetch falls back to the last
      cached response when the live query for that league/day returns empty, and that fallback response gets persisted
      under the new day instead of being recognized as stale and dropped; or (b) a date-filter is missing between the
      odds-api response and the GCS write, so any fixture the API still happens to return (regardless of how old) gets
      bucketed. Fix: either drop rows where `kickoff_utc` falls outside a sane window of `day=<D>` (record
      honest-absence/zero rows instead), or fix the fetch to only return live/ current-window fixtures per league. —
      SHIPPED 2026-07-25 (slot 7, data_engineering): added `STALENESS_CAP_SECONDS` (48h) + `KICKOFF_PAST_CAP_SECONDS` (7
      days) checks to `_prepare_tick_data()` — the shared choke point both `process_to_candles()` and
      `process_to_bucketed_df()` already call before horizon assignment (mirrors the existing `bm_time <= fetch_utc`
      causality filter's placement there, rather than duplicating the check inside `assign_horizon_bucket()`/
      `assign_horizon_buckets_vectorised()` themselves). 5 new tests (both zombie classes rejected, a fresh scrape and a
      genuine near-term kickoff NOT dropped, partial-drop still processes valid rows) — 67/67 pass, QG fresh green. **P2
      (contamination sweep) below is now unblocked but NOT started this session** — this todo only stops NEW zombie
      ticks from being bucketed going forward; existing contaminated shards in the corpus are untouched.
      market-data-processing-service@aa6e8ac.
- [x] [DATA] P2. **market-tick-data-service: sweep for the extent of the contamination.** Once the ingestion bug is
      fixed, scan `processed/by_date/*/pipeline_mode=batch_mdps_odds_horizon_bucket/.../data_type=odds_horizon_bucket/`
      for repeated (fixture_id, bookmaker_key, kickoff_utc) tuples spanning multiple `day=` partitions (the same
      signature found here) to size the blast radius across leagues/dates, and purge/re-derive the contaminated shards +
      their downstream `odds_features` + manifest rows. Single-walk discipline applies — do this via the manifest index,
      not a fresh whole-corpus GCS walk. **Purge discriminator (tick-4 refinement)**: zombie rows are cheaply separable
      by `staleness_seconds` / |fetch_utc − kickoff_utc| (years-scale on zombies, ≤~26h on genuine rows); do NOT purge
      the single-snapshot REAL-fixture class (fresh bm_time, kickoff within ~24-36h of fetch — e.g. the 2 China
      Superleague events on day=2025-10-23), which is honest data. — already covered by
      `plans/active/sports_satellite_ao_dispatch_batch4_2026_07_25.md` (extracted as a read-only DIAG item sourced from
      this doc; see that doc for execution).

      **Update (2026-07-30, finalize-001 reconciliation, slot-13/review) — sizing HALF done, purge HALF still open.**
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      Batch4's DIAG item shipped `market-tick-data-service@76ca401f` (verified ancestor of live-defi-rollout): a
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      read-only, manifest-driven sweep of the 17 sparse leagues (<=30 distinct captured days) — the 26 actively-fetched
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      leagues were explicitly NOT swept (a full-corpus sweep is ~118k GCS reads, HEAVY I/O, belongs on a dedicated VM).
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      **Findings**: `RUSSIA_PREMIER_LEAGUE` zombie CONFIRMED STILL LIVE — 18 distinct `day=` partitions (wider than the
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      5 originally documented here), 3 bookmakers (bovada/williamhill/pinnacle) × 18 days = 54 contaminated rows / 20
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      contaminated shards, `staleness_seconds` ≈1349.8 days. `AUSTRALIA_ALEAGUE`'s zombie instance is NO LONGER PRESENT
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      (resolved by intervening work). `CHINA_SUPER_LEAGUE`'s 2025-10-23 genuine-fixture control correctly EXCLUDED (0
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      contamination). **This todo's own "purge/re-derive the contaminated shards" clause is NOT yet done** — batch4's
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      DIAG scope was deliberately read-only (0 GCS objects/manifest rows deleted/overwritten/re-derived this pass). See
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      the new todo below for the tracked follow-up (per the HARD RULE that every follow-up is a `- [ ]` todo, never
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      left as prose).

- [ ] [DATA] P2. **Purge/re-derive the confirmed `RUSSIA_PREMIER_LEAGUE` zombie contamination** (20 contaminated
      `odds_horizon_bucket` shards / 54 rows across 18 `day=` partitions, sized by the read-only sweep above,
      `market-tick-data-service@76ca401f`) — purge the contaminated rows and re-derive their downstream
      `odds_features` + manifest rows. Repo: market-tick-data-service. Scope is bounded to the confirmed
      `RUSSIA_PREMIER_LEAGUE` contamination sized above, not a speculative full 43-league sweep (the remaining 26
      actively-fetched leagues would need a dedicated VM-run full sweep per the sizing todo's own note — file that
      separately if population-wide certainty is ever needed). Done-when: 0 contaminated `RUSSIA_PREMIER_LEAGUE` rows
      remain in the swept partitions, re-verified via the same sweep script, and downstream `odds_features`/manifest
      rows for those (date, league) pairs are re-derived from honest-absence (not the zombie tick).
- [ ] [DATA] P3. **Re-run `verify_ml_readiness.py --start-date 2025-09-01 --end-date 2025-11-30` after the P1/P2 fix**
      to confirm the 17 failing dates clear (or shrink to genuine honest-absence-only misses), then reassess whether the
      strict per-day gate (vs the already-precedented aggregate ≥95% pass bar from 2026-07-12) is still the right pass
      criterion for near-empty international-break days. **Expected post-purge state (tick-4 refinement)**: the 9
      cluster days become 0-row/near-0-row days (the gate currently scores empty = not-passed), so the gate fix is
      two-part — (i) zero-in-window-fixture days pass vacuously (or are skipped via an expected-fixture count from IS
      fixtures), and (ii) the per-date cell count exempts `WRITE_GATE_CONFIG.sparse_columns["odds_features"]` prefixes
      (the P1d 2026-07-12 proposal — ALL 43 always-null cluster columns verified inside that set, 0 unmatched), which
      also fixes the shallow-ladder partial days (e.g. 2025-10-20 at 91.1%). No re-capture/re-fetch is part of this path
      — verified nothing re-fetchable exists for these days (live boards had zero in-window fixtures).

## RE-TRIAGE (2026-07-23)

**Verdict: STILL OPEN, ACCURATE** (as already partially-updated by the doc's own 2026-07-16 progress note — re-verified
current code shows no further movement since).

Evidence (current code, re-read 2026-07-23):

- `market-data-processing-service/market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py` —
  `assign_horizon_bucket()`/`assign_horizon_buckets_vectorised()` still reject only two things: `bm_minutes < 0`
  (post-kickoff — the 2026-07-16 `mdps@3bf56ff` fix, confirmed present) and `|bm_minutes − target| > _HORIZON_CAPS` (the
  pre-existing graduated per-horizon cap). Neither check looks at `staleness_seconds` (`fetch_utc − bm_time`) or
  `kickoff_utc` vs the fetch day. `git log` on the file since `3bf56ff` shows only unrelated fixes (bookmaker/fixture-id
  coalescing, loss-guard, MalformedTickFieldError reclassification, K1 dual-accept) — no staleness-cap commit. A
  separate `bm_time <= fetch_utc` causality filter exists (`:567-575`) but that only rejects a bookmaker timestamp
  claiming to be from the future relative to fetch — it does not bound how far in the PAST `bm_time` can be, so it does
  not catch the Russia-Premier-League-style zombie (a board frozen 3.5 years in the past, `bm_minutes_to_kickoff` still
  landing near a legitimate horizon target by coincidence of `kickoff_utc − bm_time` staying roughly constant).
- The A-League post-kickoff zombie class remains fixed (per the doc's own 2026-07-16 note); the Russia-Premier-League
  pre-kickoff-positive zombie class remains unfixed, exactly as the doc's own last update states.

No new evidence found that changes this file's own already-correct self-assessment. Not touched by K1/K2 (data_type
casing), the pre-floor registry fix, or the shard-enumeration/honest-coverage work — orthogonal MDPS-side gap.

## Progress Log

- **2026-07-30 (slot-13, review craft, sports_satellite_ao_dispatch_batch4_finalize-001)**: Reconciled todo 2 against
  batch4's shipped DIAG sweep (`market-tick-data-service@76ca401f`, verified ancestor of live-defi-rollout) — added the
  concrete findings (RUSSIA_PREMIER_LEAGUE zombie confirmed still live across 18 partitions; AUSTRALIA_ALEAGUE resolved;
  CHINA_SUPER_LEAGUE correctly excluded) and filed the still-open purge/re-derive work as a new tracked `- [ ]` todo
  (batch4's DIAG scope was deliberately read-only, per its own text). `status: open` correctly unchanged — this doc now
  has 2 genuinely open todos (the new purge todo + the pre-existing P3 gate-reassessment todo), not 0.
- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid (sports tranche) — the sole remaining `[DATA] P3` bundles a
  bounded re-run of `verify_ml_readiness.py` with an open judgment ('then reassess whether the strict per-day gate vs
  the aggregate >=95% bar is still the right pass criterion for near-empty international-break days') plus a two-part
  gate redesign — the reassessment is the dispatch blocker, not the re-run
- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **na-eligibility-audit 2026-08-01**: KEEP-NA, valid (sports tranche) — CORRECTION to the 2026-07-30 marker, which
  addressed only the `[DATA] P3` todo and missed that this doc carries 2 open todos (confirmed via `grep -cE '^- \[ \]'`
  = 2, matching this doc's own 2026-07-30 slot-13 Progress Log note "this doc now has 2 genuinely open todos ... not
  0"). Both independently justify KEEP-NA: the `[DATA] P2` Russia-Premier-League purge is bounded/scoped with a stated
  done-when, but is a GCS delete/re-derive operation tagged `[DATA]` not `[OPERATOR]` and carries no delete-safety-cite
  or stated safe-idempotent justification, so it does not meet the GCS-delete AO-dispatch gating bar as currently
  written; the `[DATA] P3` gate-reassessment bundles a bounded re-run with an open judgment call (whether the strict
  per-day gate is still the right pass criterion for near-empty international-break days). Neither is a bare-flip
  RECLASSIFY candidate as currently written.
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — kept the prior 5, added
  `sweep_sports_odds_horizon_bucket_zombie_contamination_2026_07_27.py` (`market-tick-data-service@76ca401f`), the exact
  read-only sweep script the still-open `[DATA] P2` purge/re-derive todo re-verifies against.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (6 entries), unchanged.
- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid (sports tranche) — re-verified, unchanged since 2026-08-01 (only
  context-scout touches since). Both open todos still independently justify NA: the RUSSIA_PREMIER_LEAGUE purge is a GCS
  delete/re-derive operation tagged `[DATA]` not `[OPERATOR]` with no delete-safety-cite or stated safe-idempotent
  justification; the gate-reassessment todo bundles a bounded re-run with an open judgment call.
- **round-9 RECLASSIFY+satellite sweep 2026-08-09**: KEEP-NA-STALE, already-duplicated — found BOTH open todos
  (`[DATA] P2` purge, `[DATA] P3` gate-reassessment) are already bundled into ONE combined todo in
  `sports_satellite_ao_dispatch_batch5_2026_07_26.md` (line ~116, `assigned_vm: planning`, status: active, unlocked,
  citing `Source: sports_odds_stale_fixture_reinjection_2026_07_14.md`) — "execute the zombie-tick purge/re-derive +
  close out ML-readiness verification, using batch4's sweep report as input" covers the purge (part a), the
  `verify_ml_readiness.py` re-run (part b), AND the two-part gate-semantics fix (part c) in one done-when. That
  extraction predates this doc's widened 18-partition finding (2026-07-30) but explicitly gates on "batch4's... sweep
  todo... has produced its contamination report" — batch4's sweep (the same one that produced the 18-partition finding,
  `market-tick-data-service@76ca401f`) is done, so batch5's todo is current, not stale. **Correction to
  `sports_satellite_ao_dispatch_batch11_2026_08_09.md`'s Deferred-ledger entry for this doc** (which read "not
  extracted; every prior na-eligibility-audit pass reached the identical conclusion") — that appears to be an oversight;
  batch5's extraction has existed since 2026-07-26 and was missed. Also ran the delete-safety check batch11 said was
  blocked by host auth: `gcloud storage buckets describe gs://market-data-tick-sports-prd-central-element-323112`
  succeeded this session, `softDeletePolicy.retentionDurationSeconds=604800` — exactly meets the ≥604800s
  reversibility-qualified bar (task_template.md finding O path (c)) for whoever executes batch5's todo; not
  re-extracting here since batch5 already owns the dispatch. Doc stays `assigned_vm: NA`.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, both open todos re-verified, doc stays NA. (1)
  `[DATA] P3` (re-run `verify_ml_readiness.py`, then reassess the strict-per-day-vs-aggregate-≥95% gate) — the judgment
  half is now resolved by the dated `✅ OPERATOR RULING 2026-08-08` banner at the top of this doc ("switch to the
  precedented aggregate ≥95% pass bar"), implemented by `/plans/active/sports_taxonomy_p3_consumers_2026_08_08.md`; that
  same ruling restates this doc's own ordering constraint verbatim ("the P1/P2 zombie-tick fixes in this doc must land
  FIRST... otherwise the change would mask a real regression") — i.e. it is gated on THIS doc's own still-open
  `[DATA] P2` purge below, not yet clear to dispatch on its own. (2) `[DATA] P2` (purge the confirmed
  RUSSIA_PREMIER_LEAGUE zombie contamination, 20 shards/54 rows) — considered for RECLASSIFY against today's
  reversibility-qualified-delete precedent (task_template.md finding O path (c): a FRESH same-run
  `gcs_bucket_soft_delete_retention_seconds()` check ≥604800s self-justifies a GCS delete without an `[OPERATOR]` tag).
  **Not reclassified this pass** — path (c) requires the check to be actually run and its real value stated inline
  ("verified, not asserted"; the codex's own canonical negative example is a sports-plan todo that self-justified on
  soft-delete WITHOUT querying the real policy), and this audit pass did not execute a live GCS policy query. Both items
  stay open, doc stays NA; flagging the purge as a good target for a future pass that runs the live check.
- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).
- **2026-08-09 (slot 16, data_engineering)**: Dispatched (via `sports_satellite_ao_dispatch_batch5_2026_07_26.md`'s
  extraction of this doc's `[DATA] P2`) to execute the RUSSIA_PREMIER_LEAGUE purge. Found a blocking architectural gap —
  the real contaminated shards live at a legacy GCS path (pre-2026-07 bucket-cutover, preserved not migrated) that
  `reprocess_sports_odds.py` explicitly refuses to touch, while `features-service`'s reader falls back to exactly that
  path whenever canonical is empty (which it always is for these historical dates). The purge cannot succeed via the
  mechanism this todo assumed. Full evidence:
  `issues/sports_odds_horizon_bucket_reader_writer_path_mismatch_defeats_zombie_purge_2026_08_09.md` (P1, filed this
  session). Both open todos here stay open + blocked on that new issue's resolution.
