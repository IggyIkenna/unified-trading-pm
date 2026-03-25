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
    code: C0
    notes: "Add time_bucket partition to GCS output"
  - repo: unified-market-interface
    code: C0
    notes: "Add time-bucket logic to OddsApiAdapter.download_batch()"

isProject: false
todos:
  # ============================================================================
  # PHASE 1 — Time-bucket odds fetching  [SEQUENTIAL]
  # ============================================================================
  - id: p1a-time-bucket-logic
    content: |
      - [ ] [AGENT] P0. Add time-bucket logic to UMI OddsApiAdapter.download_batch().
        File: unified_market_interface/adapters/sports/odds_api_adapter.py
        Currently: fetches odds at {date}T12:00:00Z (single snapshot)
        Change: for each prediction league, fetch at 4 timestamps:
          T-24h: {date-1}T{kickoff-24h} or {date}T00:00:00Z
          T-6h:  {date}T06:00:00Z
          T-1h:  {date}T11:00:00Z
          T-0:   {date}T14:00:00Z (typical EPL kickoff)
        Add time_bucket column: "T-24h", "T-6h", "T-1h", "T-0"
        Pattern from archive: footballbets/cli/odds_api.py STANDARD_TIME_BUCKETS
        Credit cost: 4x current (~14,400 credits per date for 30 leagues)
    status: pending
  - id: p1b-partition-path
    content: |
      - [ ] [AGENT] P1. Add time_bucket to GCS partition path.
        File: market_tick_data_service/engine/orchestrator.py
        Current partition: {"day": date, "venue": venue}
        New: {"day": date, "venue": venue, "bucket": time_bucket}
        Path: raw_tick_data/by_date/day={date}/venue=ODDS_API/bucket={T-24h|T-0}/ticks.parquet
    status: pending

  # ============================================================================
  # PHASE 2 — Pinnacle verification  [PARALLEL with Phase 1]
  # ============================================================================
  - id: p2-pinnacle-verification
    content: |
      - [ ] [AGENT] P1. Verify Pinnacle odds in Odds API output.
        Pinnacle bookmaker key: "pinnacle"
        Download existing parquet, check bookmaker_key == "pinnacle" rows.
        If missing: check if Pinnacle needs US region or different endpoint.
    status: pending

  # ============================================================================
  # PHASE 3 — Validation  [SEQUENTIAL]
  # ============================================================================
  - id: p3-validation
    content: |
      - [ ] [AGENT] P0. Run MTDS for 2026-03-22 with time buckets.
        Verify: same fixture has odds at T-24h, T-6h, T-1h, T-0
        Verify: Pinnacle bookmaker_key present
        Verify: credit usage <= 15,000 per date
        Verify: instrument IDs human-readable across all buckets
    status: pending
    blocked_by: p1a-time-bucket-logic, p1b-partition-path
---

# Sports Integration Plan 2: Odds & Market Data Pipeline

Part of the 6-plan sports integration series.

## Success Criteria
- 4 time-bucket snapshots per fixture per date
- Pinnacle sharp odds present
- Credit usage <= 15,000 per date
- All instrument IDs human-readable
