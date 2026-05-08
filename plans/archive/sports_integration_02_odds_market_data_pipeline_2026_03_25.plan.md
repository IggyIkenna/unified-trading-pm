> **ARCHIVED 2026-05-05 — DO NOT REVIVE TIER 2 / 57-BUCKET FRAMING.** This plan references a 57-bucket "Tier 2"
> arb-grade collection grid that was sketched but never built. Predictions don't need it: MDPS
> [`SportsBucketAssignmentAdapter`](../../market-data-processing-service/market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py)
> implements an 8-bucket ML horizon grid (T-24h / T-12h / T-6h / T-4h / T-2h / T-1h / T-10m / T-0) that runs on the
> existing 288M re-keyed rows with zero API credits. Live successor:
> [`sports_predictions_e2e_2026_05_05`](../active/sports_predictions_e2e_2026_05_05.md).

---

name: sports-integration-02-odds-market-data-pipeline remaining_todos_consolidated_into:
consolidated_sports_prediction_pipeline_2026_04_15 superseded_by:
[consolidated_sports_prediction_pipeline_2026_04_15.md] reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25 overview: | MTDS --asset-group SPORTS produces historical odds with human-readable
instrument IDs and multi-horizon time buckets (T-24h, T-6h, T-1h, T-0). Pinnacle sharp odds via Odds API (pinnacle is a
bookmaker key, no separate API needed). MTDS owns betting market instrument ID generation (documented exception to
instruments-service SSOT). type: code epic: epic-code-completion status: active

completion_gates: code: C4 deployment: D1 business: B1

repo_gates:

- repo: market-tick-data-service code: C4 notes: "DONE: time_bucket partition added, source=ODDS_API path, L2 validated
  (248K rows, 16min/day)"
- repo: unified-market-interface code: C4 notes: "DONE: OddsApiAdapter FULLY REWRITTEN with per-fixture timestamps,
  bm_time, credit tracking, tier support, validate_team_resolution()"

isProject: false todos:

# ============================================================================

# PHASE 1 — Time-bucket odds fetching [SEQUENTIAL]

# ============================================================================

- id: p1a-time-bucket-logic content: |
  - [x] [AGENT] P0. Add time-bucket logic to UMI OddsApiAdapter.download_batch(). DONE (2026-03-27): OddsApiAdapter
        FULLY REWRITTEN with per-fixture timestamps, bm_time as ground truth, credit tracking with auto-stop at <10
        credits, empty-date guard (zero API calls on non-matchday), Tier 1 (12 ML buckets) and Tier 2 (57 arb buckets),
        source=ODDS_API path (not venue=ODDS_API), 5-minute rounding for cross-league dedup, validate_team_resolution()
        for fail-loud on unknown teams, discovery-based fixture pre-filtering (expected_event_ids), corrupt bookmakers
        removed (boylesports, betway, leovegas). File: unified_market_interface/adapters/sports/odds_api_adapter.py
        status: done
- id: p1b-partition-path content: |
  - [x] [AGENT] P1. Add time_bucket to GCS partition path. DONE (2026-03-27): GCS path updated to use source=ODDS_API
        (not venue=ODDS_API) per adapter rewrite. Columns added: fetch_utc, staleness_seconds, minutes_to_kickoff,
        bm_time. File: market_tick_data_service/engine/orchestrator.py Path:
        raw_tick_data/by_date/day={date}/source=ODDS_API/ticks.parquet status: done

# ============================================================================

# PHASE 2 — Pinnacle verification [PARALLEL with Phase 1]

# ============================================================================

- id: p2-pinnacle-verification content: |
  - [x] [AGENT] P1. Verify Pinnacle odds in Odds API output. DONE (2026-03-28): Pinnacle confirmed present in Odds API
        output (bookmaker_key: "pinnacle"). Cross-validated vs OddsPapi: T-2h prices match, T-10m Odds API is 10-76 min
        stale per bookmaker. Pinnacle is the CLV reference benchmark. 10 CLEAN bookmakers identified via
        cross-validation. Betfair cross-validation also completed. status: done

# ============================================================================

# PHASE 3 — Validation [SEQUENTIAL]

# ============================================================================

- id: p3-validation content: |
  - [ ] [AGENT] P0. Run 1-week validation (Phase 2 of e2e validation). The adapter rewrite is DONE. This is the 1-week
        continuous validation run. Verify: same fixture has odds at T-24h, T-6h, T-1h, T-0 Verify: Pinnacle
        bookmaker_key present Verify: credit usage <= 15,000 per date Verify: instrument IDs human-readable across all
        buckets Verify: no regressions over 7 consecutive matchdays REMAINING: 1-week validation run not yet executed.
        status: pending blocked_by: p1a-time-bucket-logic, p1b-partition-path

# ============================================================================

# PHASE 4 — Schema enrichment (2026-04-02) [DONE in this session]

# ============================================================================

- id: p4a-fixture-id-column content: |
  - [x] [AGENT] P0. Add fixture_id standalone column to odds parquet output. DONE (2026-04-02): build_fixture_id()
        called with league_canonical, home_id, away_id, date_str, kickoff HHMM. Enables cross-feature join with team
        form, xG, standings, referee features. Also added: league_id, season, home_team_id, away_team_id as standalone
        columns (no more parsing instrument_id). File: unified_market_interface/adapters/sports/odds_api_adapter.py
        status: done
- id: p4b-bookmaker-tier content: |
  - [x] [AGENT] P0. Add BookmakerTier enum to UAC (SHARP/EXCHANGE/SOFT). DONE (2026-04-02): BookmakerTier(StrEnum) with
        classify*bookmaker() and BOOKMAKER_TIER_MAP in canonical_ids.py. SHARP=pinnacle,matchbook.
        EXCHANGE=betfair_ex*\*,smarkets. SOFT=all others (default). File:
        unified_api_contracts/canonical/domain/sports/canonical_ids.py status: done
- id: p4c-manifest-writer content: |
  - [x] [AGENT] P0. Add ManifestWriter to MTDS for SPORTS dates (0-row marker). DONE (2026-04-02): MTDS now writes
        availability_index entries for every SPORTS date including 0-row days. Enables --force=False skip on subsequent
        runs. File: market_tick_data_service/engine/orchestrator.py status: done
- id: p4d-mtds-venues-fix content: |
  - [x] [AGENT] P0. Fix --venues argparse conflict (duplicate in ServiceCLI + MTDS). DONE (2026-04-02): Removed
        duplicate --venues from MTDS \_add_service_args() since ServiceCLI base class already provides it. File:
        market_tick_data_service/cli/main.py status: done

# ============================================================================

# PHASE 5 — MDPS bucket assignment (L2.5) [PENDING — design finalized]

# ============================================================================

- id: p5a-mdps-bucket-assignment content: |
  - [x] [AGENT] P0. Implement bm_time-driven bucket assignment in MDPS. DONE (2026-04-03): SportsBucketAssignmentAdapter
        registered as (SPORTS, "odds_horizon_bucket") in MDPS. Vectorised assignment via
        assign_horizon_buckets_vectorised(). 8 Tier 1 horizons with graduated staleness caps: T-24h:60min, T-12h:45min,
        T-6h:30min, T-4h:20min, T-2h:15min, T-1h:10min, T-10m:5min, T-0:5min. Causality filter (bm_time <= fetch_utc).
        Dedup per (fixture, bookmaker, market_type, horizon) keeping closest-to-target. process_to_bucketed_df() for
        features-service consumption (richer than CandleOutput). Also fixed: all 4 sports adapters now registered in
        main **init**.py (were missing). File:
        market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py status: done
- id: p5b-retention-test content: |
  - [x] [AGENT] P1. Retention test on 2020-10-31 (448K rows, 356 fixtures). DONE (2026-04-03): Derived
        bm_minutes_to_kickoff from bm_time/kickoff_utc. 50.5% retention (226K → 59K after dedup, 73.9% dedup reduction).
        6/8 buckets healthy (12 bookmakers, 320+ fixtures each). T-4h: 0 rows (old VM1 Tier 2 fetch offsets had no
        240min snapshot). T-2h: 98 rows (3 bookmakers, 20 fixtures — partial overlap only). VM3 Tier 1 offsets
        explicitly include 240min and 120min, will fill gaps. Staleness caps validated: no bucket has excessive stale
        holdovers. status: done

# ============================================================================

# PHASE 6 — FSS enrichment [PENDING]

# ============================================================================

- id: p6a-opening-odds content: |
  - [x] [AGENT] P0. Derive opening odds from T-24h bucket in FSS exporter. DONE (2026-04-03): compute*opening_odds()
        added to odds_calculator.py. T-24h = opening line. Earliest horizon per fixture as opening.
        odds_movement*{outcome} = closing / opening - 1 for each outcome. 6 new columns: opening*{home,draw,away}\_odds,
        odds_movement*{home,draw,away}. File: features_sports_service/calculators/odds_calculator.py status: done
- id: p6b-bookmaker-tier-tagging content: |
  - [x] [AGENT] P0. Tag bookmakers by BookmakerTier in FSS exporter. DONE (2026-04-03): compute*tier_features() added to
        odds_calculator.py. classify_bookmaker() from UAC. 16 new columns: sharp_consensus*_, soft*consensus*_,
        exchange*price*_, sharp*soft_delta*_, sharp*disagreement*_, soft*disagreement*_, bookmaker*count*\*. File:
        features_sports_service/calculators/odds_calculator.py status: done
- id: p6c-clv-features content: |
  - [x] [AGENT] P1. Compute CLV features in FSS. DONE (2026-04-03): compute*clv_features() added to odds_calculator.py.
        CLV = closing_odds / opening_odds - 1 (T-0 / T-24h). Sharp CLV uses Pinnacle only. Generic CLV uses median of
        all bookmakers. 9 new columns: clv*{home,draw,away}, sharp*clv*{home,draw,away}, clv*direction*{home,draw,away}.
        File: features_sports_service/calculators/odds_calculator.py status: done

# ============================================================================

# PHASE 7 — Halftime odds validation [RE-OPENED — needs empirical test]

# ============================================================================

- id: p7a-halftime-empirical-test content: |
  - [ ] [SCRIPT] P1. Empirically test Odds API at offset -60 (HT) for recent match. Pick a completed fixture (e.g. EPL
        2026-03-22). Fetch historical odds at kickoff + 60min. Check bm_time in response: is it AFTER kickoff? If yes,
        bookmakers ARE updating in-play and Odds API captures it. If bm_time is BEFORE kickoff, odds are stale closing
        line. This determines whether HT odds are feasible from Odds API. Test with 1 fixture, 1 API call (60 credits).
        Previous assumption (pre-match only) was not empirically validated. status: pending
- id: p7b-halftime-odds-analysis content: |
  - [ ] [ANALYSIS] P1. If P7a shows real in-play bm_time: analyse HT odds quality. Check: how many bookmakers update
        during match? Which markets (h2h, totals)? Check: are prices meaningfully different from closing line? If HT
        odds are real: keep -60 offset in Tier 2, add HT features to FSS. If HT odds are stale: remove -60 offset,
        document as pre-match only. status: pending blocked_by: p7a-halftime-empirical-test

# ============================================================================

# PHASE 9 — FootyStats match data backfill [PENDING — needs API key]

# ============================================================================

- id: p9a-footystats-match-backfill content: |
  - [ ] [SCRIPT] P1. Backfill FootyStats match-level data to GCS. FootyStats API has per-half data (ht_goals, 2hg_goals,
        fh_corners, 2h_corners, per-half xG) that no other source provides. The UMI FootystatsAdapter exists but is
        BLACKLISTED_NO_ACCESS (no API keys). Steps: 1) Obtain FootyStats API key. 2) Implement fetch_matches() in
        FootystatsAdapter. 3) Backfill 33 prediction leagues x 5.8 years. 4) Write to GCS with entity=footystats_matches
        partition. Schema: FTMatchRaw in UAC (60+ columns including HT/FH/2H splits). Normalizer already wires HT fields
        through to CanonicalFixture. status: pending

# ============================================================================

# PHASE 10 — Manifest completeness tracking [PARALLEL with Phase 8]

# ============================================================================

- id: p10a-mtds-manifest content: |
  - [x] [AGENT] P0. MTDS ManifestWriter writes availability_index for SPORTS dates. DONE (2026-04-02): MTDS writes
        entries for every SPORTS date including 0-row days. --force=True overwrites existing entries. --force=False
        (default) skips dates with existing manifest entries. Enables idempotent re-runs. status: done
- id: p10b-mdps-manifest content: |
  - [x] [AGENT] P0. MDPS ManifestWriter writes availability_index for bucketed output. DONE (2026-04-03): Already wired
        via CandleOrchestrationService.\_write_manifest_records(). Writes granular entries
        (venue="ODDS_API:odds_horizon_bucket") and summary entry (venue="odds_horizon_bucket") with candle counts.
        check_shard_freshness() handles --force skip logic with schema_version + max_age_hours checks. status: done
- id: p10c-completeness-checker content: |
  - [ ] [SCRIPT] P1. Build completeness checker script for odds pipeline. Read availability_index from MTDS + MDPS GCS
        buckets. Report: dates with data, dates missing, % complete for date range. Report: per-horizon coverage (T-24h
        through T-0), bookmaker count per date. Output: completeness_report.json with per-date status. CLI: python
        scripts/check_odds_completeness.py --start 2020-06-01 --end 2026-03-28 Flag dates needing --force re-run (schema
        mismatch, low row count). status: pending blocked_by: p10a-mtds-manifest, p10b-mdps-manifest

# ============================================================================

# PHASE 11 — Phased rollout strategy [SEQUENTIAL]

# ============================================================================

- id: p11a-one-month-validation content: |
  - [ ] [SCRIPT] P0. Run odds pipeline for 1 month (2025-03-01 to 2025-03-31). MTDS fetch → MDPS bucket assignment →
        verify all 8 horizons populated. Verify: manifest 100% for 31 dates, all horizons have rows, Pinnacle present.
        Only proceed to full backfill after 1-month validation passes. status: pending blocked_by:
        p5a-mdps-bucket-assignment
- id: p11b-full-period-rollout content: |
  - [ ] [SCRIPT] P0. Roll out odds pipeline to full period (2020-06-01 to 2026-03-28). Run MTDS with --force=False (skip
        dates already in manifest). Run MDPS with --force=False on all dates with MTDS data. Completeness checker must
        show >= 99% date coverage before declaring done. VM3 backfill (in progress) covers L1 raw odds. This item covers
        L2.5 MDPS pass. status: pending blocked_by: p11a-one-month-validation

# ============================================================================

# PHASE 8 — Historical backfill (2026-04-02) [IN PROGRESS]

# ============================================================================

- id: p8a-l0-reference-backfill content: |
  - [x] [SCRIPT] P0. L0 reference data backfill (2020-06-01 → 2026-03-28). DONE (2026-04-02): instr-backfill-sports VM
        completed 71/71 chunks. 2,127 date partitions written to instruments-store-sports bucket. Rate limiter (1
        req/sec) + 5-retry + 5s base delay reduced 429s by 93%. status: done
- id: p8b-l1-odds-backfill content: |
  - [ ] [SCRIPT] P0. L1 odds backfill (2020-06-01 → 2026-03-28). IN PROGRESS (2026-04-03): VM3
        (mtds-backfill-sports-odds-3, asia-northeast1-b) launched with updated tarball containing all fixes:
        BookmakerTier, fixture_id columns, source=ODDS_API path, no --venues conflict. Full re-run with --force, Tier 1
        ML buckets, 7-day chunks, 15M credit budget, auto-shutdown. VM1 covered 2020-06-01→2020-10-31 (old schema). VM2
        had old code too. status: in_progress

---

> **SUPERSEDED 2026-04-25 by
> [consolidated_sports_prediction_pipeline_2026_04_15.md](./consolidated_sports_prediction_pipeline_2026_04_15.md).**
> Original scope retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit
> formalises it as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence.

# Sports Integration Plan 2: Odds & Market Data Pipeline

Part of the 6-plan sports integration series.

## Success Criteria

- 8 time-bucket snapshots per fixture per date (Tier 1: T-24h/12h/6h/4h/2h/1h/10m/0)
- Pinnacle sharp odds present with BookmakerTier classification
- fixture_id join key in every row (canonical human-readable format)
- Credit usage tracked via remaining count in API response
- All instrument IDs human-readable
- MDPS assigns buckets by bm_time with graduated staleness tolerance
- Opening odds (T-24h) and CLV (T-0/T-24h) computed by FSS
- HT odds empirically tested (offset -60) — real in-play or stale closing determined
- Manifest tracks 100% of dates for both MTDS (L1) and MDPS (L2.5)
- 1-month validation passes before full-period rollout
- Full period (2020-06-01 to 2026-03-28) >= 99% odds coverage
- --force overwrites existing manifest entries, default skips (idempotent)
