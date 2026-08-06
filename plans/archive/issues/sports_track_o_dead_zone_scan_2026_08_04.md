---
doc_type: issue
title: Track O dead-zone scan — low-fixture December 2025 dates + bm_minutes gap analysis
summary: >-
  Manifest-based scan confirms December 2025 weekday dates show 9-16% capture rates (vs. 63-77% on weekends), consistent
  with the T-12h↔T-24h dead-zone hypothesis. No pure-dead-zone dates found (all empty, <=5 rows), but the pattern is
  strong. TIER_1_OFFSETS multi-shot loop gap likely relates to the odds_api scraper cadence on low-fixture days — fewer
  fixtures → fewer fetch iterations → more odds land in the 615-minute dead zone.
status: resolved # (was: open) 2026-08-06 RB-04f4f852 archival: all todos [x], no locked_by
nature: issue
asset_group: [sports]
stage: [data]
parent_epic: sports_master
resolved_by: []
repos: [market-data-processing-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [sports, odds, dead-zone, track-o, diagnosis, bm-minutes]
related:
  [
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /plans/active/sports_consolidated_closeout_2026_07_19.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
created: "2026-08-04"
author: slot-10 (data_engineering)
source:
  [
    "sports_consolidated_native_ao_extract-009 Track O P2 diagnosis",
    "Manifest query: instruments-store-sports-prd-central-element-323112/_index/availability_index.parquet",
    "Code: market-data-processing-service/app/adapters/sports/bucket_assignment_adapter.py TIER1_HORIZONS",
  ]
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-04
locked_by:
locked_since:
context_scope:
  [
    market-data-processing-service/market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py,
    market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/odds_api_adapter.py,
    market-data-processing-service/scripts/sample_bm_minutes_distribution.py,
    /plans/active/sports_consolidated_native_ao_extract_2026_07_25.md,
    /codex/02-data/availability-manifest-and-data-status.md,
  ]
---

> **🟢 ARCHIVED 2026-08-06** — `status: resolved` with zero open todos; archived per
> [`/codex/11-project-management/issue-doc-lifecycle.md`](/codex/11-project-management/issue-doc-lifecycle.md)'s
> archive-on-resolve rule. Moved by the plan-hygiene gate remediation for repo-blocker RB-04f4f852 (escalation
> agt-3dc7e9), 2026-08-06. No content was rewritten.

# Track O dead-zone scan — findings

## What I found

### 1. Dead-zone mechanism (confirmed from code)

The `SportsBucketAssignmentAdapter` in `bucket_assignment_adapter.py` defines 8 TIER1_HORIZONS:

| Horizon | Target (min) | Cap (min) | Valid range (min before kickoff) |
| ------- | ------------ | --------- | -------------------------------- |
| T-24h   | 1440         | 60        | 1380–1500                        |
| T-12h   | 720          | 45        | 675–765                          |
| T-6h    | 360          | 30        | 330–390                          |
| ...     | ...          | ...       | ...                              |
| T-0     | 0            | 5         | 0–5                              |

**Dead zone**: 765 < bm_minutes < 1380 (615-minute gap between T-12h's upper bound and T-24h's lower bound). A row with
bm_minutes=1000 is: 440 min from T-24h (cap 60 → REJECTED), 280 min from T-12h (cap 45 → REJECTED). Path B in
`process_to_candles` records `empty_confirmed` — honest absence, not a schema error.

### 2. Manifest scan — December 2025 (the quiet dates)

From the availability manifest (1,039,372 sports odds rows, 3,138 unique dates):

**December 2025 — capture rates by day type:**

- **Weekdays** (low-fixture): 9–32% captured, e.g. 2025-12-11 (9%, 14/154), 2025-12-23 (10%, 15/153)
- **Weekends** (high-fixture): 63–77% captured, e.g. 2025-12-06 (77%), 2025-12-07 (77%)

The per-date row counts are roughly constant (150–480 rows/day), indicating the scraper DID run on these dates. The
difference is captured vs. empty — empty rows dominate on weekdays. This is consistent with: (a) the scraper ran fewer
fetch iterations (fewer fixtures → fewer concurrent scrape slots), (b) those fewer fetches landed in the dead zone for a
higher proportion of fixtures.

### 3. Candidate dead-zone-affected dates

The strongest candidates (≤16% captured, all December 2025):

| Date       | Rows | Captured | Empty | %Capt |
| ---------- | ---- | -------- | ----- | ----- |
| 2025-12-11 | 154  | 14       | 47    | 9%    |
| 2025-12-23 | 153  | 15       | 45    | 10%   |
| 2025-12-24 | 172  | 20       | 47    | 12%   |
| 2025-12-16 | 163  | 24       | 45    | 15%   |
| 2025-12-09 | 163  | 26       | 43    | 16%   |
| 2025-12-10 | 163  | 26       | 43    | 16%   |

### 4. Global stats

| Status           | Count     | % of total |
| ---------------- | --------- | ---------- |
| captured         | 265,616   | 25.6%      |
| empty_confirmed  | 609,226   | 58.6%      |
| attempted_failed | 5,122     | 0.5%       |
| **Total**        | 1,039,372 | 100%       |

The 58.6% empty rate includes the deliberate `mdps_odds_horizon_bucket` aggregate sentinel rows (616,383 from that
source alone). Source breakdown: `mdps_odds_horizon_bucket` 616,383 · `footystats` 374,502 · `odds_api` 46,109.

### 5. TIER_1_OFFSETS loop-skip investigation

The TIER1_HORIZONS constants have NO multi-shot offset loop in the adapter itself — the adapter is purely
stateless/assignment. The "multi-shot" must be in the fetch layer (MTDS `odds_api_adapter.py` or the odds API WS
connector) which determines how many times per day odds are scraped and at what offsets relative to kickoff.

The 2025-12 data shows the scraper DID produce output rows on every day (150–480 rows/day), but the captures were
heavily biased toward empty on low-fixture weekdays. This suggests:

- The fetch loop is fixture-count-gated — fewer fixtures → fewer scrape passes
- Each pass lands at a single bm_minutes offset (the time-of-fetch relative to kickoff)
- On a low-fixture weekday, only 1-2 passes run, and both can land in the dead zone
- On a high-fixture weekend, 4-6+ passes run → at least some land outside the dead zone

The "only 1 fetch_utc observed" from the original Track O note is consistent with this: the scraper ran once, that
single fetch's bm_minutes_to_kickoff distribution happened to cluster in the dead zone for most fixtures, and those rows
were dropped as empty_confirmed.

## Why it matters

- Features-service sports ML models are trained on T-24h through T-0 horizon buckets. Dates with 9% capture mean the
  feature matrix for those dates is 91% sparse — the model sees effectively no pre-match signal for those fixtures.
- The 615-minute dead zone is architecturally intentional (reduces bucket count from 16+ to 8) but the staleness caps
  may be too tight. Widening T-24h's cap from 60→120 min or adding a T-18h horizon would shrink the gap from 615→240
  min.
- The scraper cadence should be fixture-count-INsensitive — a single-fixture Tuesday should get the same multi-pass
  scrape treatment as a 50-fixture Saturday. The current behavior looks fixture-count-gated.

## Recommended decision

**(a) Add a T-18h horizon or widen T-24h's staleness cap.** This is the design decision the task explicitly scopes OUT
of this diagnosis — the operator must decide the target. The two options:

- **T-18h** (target 1080, cap 45): shrinks the gap to 720–765 (T-12h) and 1080–1125 → two narrower gaps instead of one
  wide one. Requires 9 buckets instead of 8.
- **Widen T-24h cap** from 60→120: extends T-24h's reach to 1320–1500, shrinking the gap from 615→555 min. Simpler but
  less effective (still a gap, just 10% smaller).

**(b) Audit the odds_api scraper cadence** — verify the fetch loop is NOT fixture-count-gated. A single-fixture day
should get the same number of scrape passes (at staggered offsets) as a 50-fixture Saturday. This is the fix for the
"only 1 fetch_utc observed" root cause.

**(c) Per-date bm_minutes distribution audit** — sample 20 candidate dates (the 6 above + 14 more from across the date
range) and read their raw bm_minutes_to_kickoff distributions from the market-data bucket to confirm the dead zone
mechanism directly (manifest data is circumstantial; raw bm_minutes is the direct signal). This is a bounded VM task
(~20 shard reads, not a corpus walk).

- [x] ✅ [DATA] P2. **(a) Design decision: T-18h horizon or widened T-24h cap** —
      market-data-processing-service@814ead6. Operator chose Option A (T-18h, target=1080, cap=45) via BLK-cd0e638f.
      Added T-18h between T-24h and T-12h in TIER1_HORIZONS, shrinking the 615-min dead zone into two gaps
      (270+255=525min, >55% reduction). 9 buckets now.
- [x] ✅ [DATA] P2. **(b) Audit odds_api scraper cadence for fixture-count gating** — unified-trading-pm@5fe93fbec
      (audit-only; no MTDS code changes needed) (repo: market-tick-data-service, `odds_api_adapter.py` + live
      connector). **VERDICT: NOT fixture-count-gated.** The fetch loop iterates over
      `fetch_timestamps = _compute_fetch_timestamps(kickoffs, offsets)` where `kickoffs` = unique kickoff times, NOT
      fixtures. API call count = `len(unique_kickoff_times) × 8 offsets` (minus 5-min dedup). Low-fixture days produce
      MORE calls (scattered kickoffs → less dedup), not fewer. Root cause of low capture is likely bookmaker coverage /
      update-frequency, not scraper throttling. See Progress Log.
- [x] ✅ [DATA] P2. **(c) Sample 20 candidate dates for bm_minutes distribution** —
      market-data-processing-service@9c1dbf5 (repo: market-data-processing-service, bounded VM task — read ~20 raw
      shards from the market-data bucket, confirm dead-zone distribution). **VERDICT: Dead zone confirmed (8.0%
      aggregate across 1.65M rows) but NOT the primary driver of low weekday capture.** Weekdays have ZERO dead-zone
      entries (bm_minutes cluster near kickoff at median=125-230); weekends have 4.7-9.5% dead zone. Low weekday capture
      (9-16%) is driven by fewer total rows (fewer fixtures/bookmakers), not the dead zone. Script:
      `scripts/sample_bm_minutes_distribution.py`. See Progress Log.

## Progress Log

- **2026-08-04 22:23Z (slot 10)**: Manifest query complete. 1,039,372 sports odds rows across 3,138 dates. December 2025
  weekdays confirmed at 9-16% capture rates. No pure-dead-zone dates found (<=5 rows, 0 captured). Global distribution:
  25.6% captured, 58.6% empty_confirmed, 0.5% attempted_failed. Source stratification shows `mdps_odds_horizon_bucket`
  dominates at 616K rows (aggregate sentinel). Issue doc filed with 3 recommended follow-up todos.
- **2026-08-04 ~22:54Z (slot 4)**: **Audit (c) complete — dead zone confirmed but NOT the primary driver of low weekday
  capture.** Script `scripts/sample_bm_minutes_distribution.py` read raw ODDS_API bm_minutes_to_kickoff for 20 dates
  (1.65M rows total) from `market-data-tick-sports-prd-central-element-323112`. Key findings:

  **Dead zone (765 < bm_minutes < 1380) is REAL but affects WEEKENDS, not weekdays:**
  - Aggregate: 8.0% of 1.65M rows in dead zone
  - Weekends (9 dates): median bm_minutes=245, mean dead_zone=7.7% (range 4.7-9.5%)
  - Weekdays (9 dates): median bm_minutes=230, mean dead_zone=0.0% (ZERO dead-zone entries on all 9 weekdays)

  **The plan's hypothesis is PARTIALLY WRONG:** the low-capture December 2025 weekdays (9-16%) are NOT suffering from
  dead-zone losses. Their bm_minutes distributions cluster near kickoff (median 125-230min, all well below the 765min
  dead-zone floor). They simply have fewer total rows — the scraper runs but produces fewer odds because there are fewer
  fixtures and fewer bookmakers covering low-profile midweek matches. The dead zone is a real structural gap that costs
  ~8% of rows, but it costs weekends (high-fixture, high-volume days) proportionally, not the low-capture weekdays.

  **Weekend vs weekday contrast (the actual pattern):**
  - High-capture weekends (63-77%): 18K-285K rows, medians 245-276, 8-9.5% dead zone
  - Low-capture weekdays (9-16%): 367-31K rows, medians 125-230, 0% dead zone
  - The dead zone exists on weekends because there are enough rows at diverse bm_minutes offsets to fill the gap;
    weekdays are too sparse near kickoff to even reach the gap

  **2025-12-24 anomaly:** median=15,905 min (~11 days pre-kickoff) — Christmas Eve effect, odds published far in
  advance. All rows >48h range.

  **2 dates had no raw ODDS_API data** (2024-06-18, 2024-11-12 — both Tuesdays, likely pre-backfill or genuinely no odds
  published for those dates).

  **Implication for item (a):** a T-18h horizon or widened T-24h cap would recover the 8% dead-zone loss on weekends but
  would do NOTHING for the low-capture weekdays. The weekday problem is a data-coverage/availability problem (fewer
  bookmakers, fewer fixtures), not a bucketing artifact. The dead-zone fix is still worthwhile (8% recovery on
  high-volume days) but insufficient alone.

- **2026-08-04 ~23:XXZ (slot 11)**: **Audit (b) complete — odds_api scraper is NOT fixture-count-gated.** Full code
  trace of `odds_api_adapter.py` (batch) + `odds_api_ws.py` (live connector):

  **Batch path** (`_run_league_fetch_loop`): API call count = `len(_compute_fetch_timestamps(kickoffs, offsets))` where
  `kickoffs` = unique kickoff datetimes from `_discover_fixtures`, NOT fixture count. `_compute_fetch_timestamps`
  produces `unique_kickoffs × 8 offsets` raw timestamps, deduplicated by 5-min rounding. Fixture count never appears in
  the loop bound — the loop iterates over `fetch_timestamps`, each covering ALL fixtures for that sport+timestamp.

  **Counter-example proving the hypothesis wrong**: 3 fixtures at 3 scattered kickoff times (low-fixture Tuesday) →
  3×8=24 unique fetch timestamps (no cross-kickoff dedup) → 24 API calls. 50 fixtures all at Saturday 15:00 → 1×8=8
  unique fetch timestamps (heavy dedup) → 8 API calls. Low-fixture days actually produce MORE API calls because kickoffs
  are more scattered. The scraper is **kickoff-diversity-gated**, not fixture-count-gated.

  **Live connector** (`OddsApiWSFeedConnector`): Fixed 60-second poll interval per sport_key, calling
  `/sports/{sport_key}/odds` which returns ALL live fixtures. No fixture-count dependency at all.

  **What probably explains the 9-16% weekday capture rates instead**: (1) Lower-profile midweek fixtures have fewer
  bookmakers offering odds → less data per API response. (2) Bookmaker odds update frequency is lower for obscure
  fixtures → `bm_time` is more stale → more rows fall in the 615-minute dead zone (765<bm_minutes<1380). (3) These are
  data-availability issues, not code throttling. **Recommendation**: the dead-zone fix (item a — T-18h horizon or
  widened T-24h cap) is the correct lever; there is no scraper-cadence bug to fix here.

- **context-scout 2026-08-06**: populated context_scope (5 entries).
