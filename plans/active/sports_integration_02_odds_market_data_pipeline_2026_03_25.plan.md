---
name: sports-integration-02-odds-market-data-pipeline
locked_by: live-defi-rollout
locked_since: 2026-03-25
overview: |
  MTDS --category SPORTS produces historical odds with human-readable instrument IDs
  and multi-horizon time buckets (T-24h, T-6h, T-1h, T-0). Pinnacle sharp odds via
  Odds API (pinnacle is a bookmaker key, no separate API needed). MTDS owns betting
  market instrument ID generation (documented exception to instruments-service SSOT).
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C4
  deployment: D1
  business: B1

repo_gates:
  - repo: market-tick-data-service
    code: C4
    notes: "DONE: time_bucket partition added, source=ODDS_API path, L2 validated (248K rows, 16min/day)"
  - repo: unified-market-interface
    code: C4
    notes:
      "DONE: OddsApiAdapter FULLY REWRITTEN with per-fixture timestamps, bm_time, credit tracking, tier support,
      validate_team_resolution()"

isProject: false
todos:
  # ============================================================================
  # PHASE 1 — Time-bucket odds fetching  [SEQUENTIAL]
  # ============================================================================
  - id: p1a-time-bucket-logic
    content: |
      - [x] [AGENT] P0. Add time-bucket logic to UMI OddsApiAdapter.download_batch().
        DONE (2026-03-27): OddsApiAdapter FULLY REWRITTEN with per-fixture timestamps,
        bm_time as ground truth, credit tracking with auto-stop at <10 credits,
        empty-date guard (zero API calls on non-matchday), Tier 1 (12 ML buckets) and
        Tier 2 (57 arb buckets), source=ODDS_API path (not venue=ODDS_API), 5-minute
        rounding for cross-league dedup, validate_team_resolution() for fail-loud on
        unknown teams, discovery-based fixture pre-filtering (expected_event_ids),
        corrupt bookmakers removed (boylesports, betway, leovegas).
        File: unified_market_interface/adapters/sports/odds_api_adapter.py
    status: done
  - id: p1b-partition-path
    content: |
      - [x] [AGENT] P1. Add time_bucket to GCS partition path.
        DONE (2026-03-27): GCS path updated to use source=ODDS_API (not venue=ODDS_API)
        per adapter rewrite. Columns added: fetch_utc, staleness_seconds,
        minutes_to_kickoff, bm_time.
        File: market_tick_data_service/engine/orchestrator.py
        Path: raw_tick_data/by_date/day={date}/source=ODDS_API/ticks.parquet
    status: done

  # ============================================================================
  # PHASE 2 — Pinnacle verification  [PARALLEL with Phase 1]
  # ============================================================================
  - id: p2-pinnacle-verification
    content: |
      - [x] [AGENT] P1. Verify Pinnacle odds in Odds API output.
        DONE (2026-03-28): Pinnacle confirmed present in Odds API output (bookmaker_key:
        "pinnacle"). Cross-validated vs OddsPapi: T-2h prices match, T-10m Odds API is
        10-76 min stale per bookmaker. Pinnacle is the CLV reference benchmark.
        10 CLEAN bookmakers identified via cross-validation. Betfair cross-validation
        also completed.
    status: done

  # ============================================================================
  # PHASE 3 — Validation  [SEQUENTIAL]
  # ============================================================================
  - id: p3-validation
    content: |
      - [ ] [AGENT] P0. Run 1-week validation (Phase 2 of e2e validation).
        The adapter rewrite is DONE. This is the 1-week continuous validation run.
        Verify: same fixture has odds at T-24h, T-6h, T-1h, T-0
        Verify: Pinnacle bookmaker_key present
        Verify: credit usage <= 15,000 per date
        Verify: instrument IDs human-readable across all buckets
        Verify: no regressions over 7 consecutive matchdays
        REMAINING: 1-week validation run not yet executed.
    status: pending
    blocked_by: p1a-time-bucket-logic, p1b-partition-path

  # ============================================================================
  # PHASE 4 — Schema enrichment (2026-04-02)  [DONE in this session]
  # ============================================================================
  - id: p4a-fixture-id-column
    content: |
      - [x] [AGENT] P0. Add fixture_id standalone column to odds parquet output.
        DONE (2026-04-02): build_fixture_id() called with league_canonical, home_id,
        away_id, date_str, kickoff HHMM. Enables cross-feature join with team form,
        xG, standings, referee features. Also added: league_id, season, home_team_id,
        away_team_id as standalone columns (no more parsing instrument_id).
        File: unified_market_interface/adapters/sports/odds_api_adapter.py
    status: done
  - id: p4b-bookmaker-tier
    content: |
      - [x] [AGENT] P0. Add BookmakerTier enum to UAC (SHARP/EXCHANGE/SOFT).
        DONE (2026-04-02): BookmakerTier(StrEnum) with classify_bookmaker() and
        BOOKMAKER_TIER_MAP in canonical_ids.py. SHARP=pinnacle,matchbook.
        EXCHANGE=betfair_ex_*,smarkets. SOFT=all others (default).
        File: unified_api_contracts/canonical/domain/sports/canonical_ids.py
    status: done
  - id: p4c-manifest-writer
    content: |
      - [x] [AGENT] P0. Add ManifestWriter to MTDS for SPORTS dates (0-row marker).
        DONE (2026-04-02): MTDS now writes availability_index entries for every SPORTS
        date including 0-row days. Enables --force=False skip on subsequent runs.
        File: market_tick_data_service/engine/orchestrator.py
    status: done
  - id: p4d-mtds-venues-fix
    content: |
      - [x] [AGENT] P0. Fix --venues argparse conflict (duplicate in ServiceCLI + MTDS).
        DONE (2026-04-02): Removed duplicate --venues from MTDS _add_service_args()
        since ServiceCLI base class already provides it.
        File: market_tick_data_service/cli/main.py
    status: done

  # ============================================================================
  # PHASE 5 — MDPS bucket assignment (L2.5)  [PENDING — design finalized]
  # ============================================================================
  - id: p5a-mdps-bucket-assignment
    content: |
      - [x] [AGENT] P0. Implement bm_time-driven bucket assignment in MDPS.
        DONE (2026-04-03): SportsBucketAssignmentAdapter registered as
        (SPORTS, "odds_horizon_bucket") in MDPS. Vectorised assignment via
        assign_horizon_buckets_vectorised(). 8 Tier 1 horizons with graduated
        staleness caps: T-24h:60min, T-12h:45min, T-6h:30min, T-4h:20min,
        T-2h:15min, T-1h:10min, T-10m:5min, T-0:5min. Causality filter
        (bm_time <= fetch_utc). Dedup per (fixture, bookmaker, market_type,
        horizon) keeping closest-to-target. process_to_bucketed_df() for
        features-service consumption (richer than CandleOutput). Also fixed:
        all 4 sports adapters now registered in main __init__.py (were missing).
        File: market_data_processing_service/app/adapters/sports/bucket_assignment_adapter.py
    status: done
  - id: p5b-retention-test
    content: |
      - [ ] [AGENT] P1. Retention test on sample day (e.g. 2020-10-31, 43K rows).
        Pull from GCS, check per-bucket: how many bookmakers survive each staleness
        cap vs how many are stale holdovers. Find knee point.
    status: pending

  # ============================================================================
  # PHASE 6 — FSS enrichment  [PENDING]
  # ============================================================================
  - id: p6a-opening-odds
    content: |
      - [ ] [AGENT] P0. Derive opening odds from T-24h bucket in FSS exporter.
        T-24h = opening line. Label earliest horizon per fixture as opening.
        Compute odds_movement = closing / opening - 1 for each outcome.
    status: pending
  - id: p6b-bookmaker-tier-tagging
    content: |
      - [ ] [AGENT] P0. Tag bookmakers by BookmakerTier in FSS exporter.
        Import classify_bookmaker() from UAC. Group by tier for:
        sharp_consensus, soft_consensus, sharp_soft_delta, exchange_price,
        bookmaker_disagreement (within-tier and cross-tier).
    status: pending
  - id: p6c-clv-features
    content: |
      - [ ] [AGENT] P1. Compute CLV features in FSS.
        CLV = closing_odds / opening_odds - 1 (T-0 / T-24h).
        Settlement/results from instruments-service L0 data (already backfilled).
        closing_line_predictability = correlation(CLV, settlement).
    status: pending

  # ============================================================================
  # PHASE 7 — Halftime odds validation  [PENDING — design finalized]
  # ============================================================================
  - id: p7a-halftime-real-time
    content: |
      - [ ] [AGENT] P1. Source real halftime timestamps from API-Football.
        API-Football fixture.status.elapsed + event timestamps give actual HT.
        Use as ground truth for T+60 bucket filter window.
    status: pending
  - id: p7b-halftime-odds-stability
    content: |
      - [ ] [AGENT] P1. Validate HT via odds stability detection.
        Find 5-10min window of small odds changes = half-time break.
        Fallback when API-Football HT time unavailable.
    status: pending
  - id: p7c-halftime-arb-crossval
    content: |
      - [ ] [AGENT] P2. Cross-validate HT with arb availability.
        Compare arb size at HT window vs 20min before/after (in-play).
        Small arbs + converged odds at HT vs wild swings in-play.
        Test on 1-2 busy matchdays before full backfill.
    status: pending

  # ============================================================================
  # PHASE 8 — Historical backfill (2026-04-02)  [IN PROGRESS]
  # ============================================================================
  - id: p8a-l0-reference-backfill
    content: |
      - [x] [SCRIPT] P0. L0 reference data backfill (2020-06-01 → 2026-03-28).
        DONE (2026-04-02): instr-backfill-sports VM completed 71/71 chunks.
        2,127 date partitions written to instruments-store-sports bucket.
        Rate limiter (1 req/sec) + 5-retry + 5s base delay reduced 429s by 93%.
    status: done
  - id: p8b-l1-odds-backfill
    content: |
      - [ ] [SCRIPT] P0. L1 odds backfill (2020-06-01 → 2026-03-28).
        IN PROGRESS (2026-04-03): VM3 (mtds-backfill-sports-odds-3, asia-northeast1-b)
        launched with updated tarball containing all fixes: BookmakerTier, fixture_id
        columns, source=ODDS_API path, no --venues conflict. Full re-run with --force,
        Tier 1 ML buckets, 7-day chunks, 15M credit budget, auto-shutdown.
        VM1 covered 2020-06-01→2020-10-31 (old schema). VM2 had old code too.
    status: in_progress
---

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
- Halftime odds validated via real HT time + odds stability + arb cross-validation
