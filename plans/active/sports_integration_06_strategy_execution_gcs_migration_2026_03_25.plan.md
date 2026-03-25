---
name: sports-integration-06-strategy-execution-gcs-migration
locked_by: live-defi-rollout
locked_since: 2026-03-25
overview: |
  Wire arbitrage detection + ML-based betting + execution routing.
  ArbitrageStrategy reads MTDS odds, MLSportsStrategy reads ML predictions.
  Execution routes through USEI (Betfair, Pinnacle via Odds API, paper trading).
  GCS migration is LAST — old buckets to hive format, needs user approval before execute.
type: code
epic: epic-code-completion
status: active

completion_gates:
  code: C4
  deployment: D3
  business: B4

repo_gates:
  - repo: strategy-service
    code: C0
    notes: "Wire ArbitrageStrategy + MLSportsStrategy to data sources"
  - repo: execution-service
    code: C0
    notes: "Verify sports routing through USEI"
  - repo: unified-sports-execution-interface
    code: C0
    notes: "Verify Betfair + paper trading adapters"
  - repo: unified-trading-pm
    code: C0
    notes: "GCS migration script"

depends_on:
  - sports-integration-05-ml-training-pipeline

isProject: false
todos:
  - id: p1-arbitrage-wiring
    content: |
      - [ ] [AGENT] P1. Verify ArbitrageStrategy reads from MTDS GCS output.
        File: strategy_service/engine/strategies/sports/arbitrage.py
        Input: odds parquet (64 bookmakers per fixture)
        Logic: GROUP BY fixture + market + selection, compare max/min prices
        Output: TradeSignal with venue pair, odds, implied profit
    status: pending
  - id: p2-ml-strategy-wiring
    content: |
      - [ ] [AGENT] P1. Verify MLSportsStrategy reads from ml-inference output.
        File: strategy_service/engine/strategies/sports/ml_sports_strategy.py
        Input: model probabilities (home/draw/away)
        Logic: Kelly sizing, confidence gate, max-odds gate
        Output: TradeSignal with venue, odds, stake
    status: pending
  - id: p3-execution-routing
    content: |
      - [ ] [AGENT] P1. Verify execution-service routes sports signals through USEI.
        File: execution_service/adapters/sports_router.py
        Routing: TradeSignal.venue -> USEI adapter (Betfair, Pinnacle, paper)
        Paper mode: all signals to PaperBettingAdapter
    status: pending
  - id: p4-paper-trading
    content: |
      - [ ] [AGENT] P0. Run paper trade for March 22 fixtures.
        ArbitrageStrategy: scan 35K odds for arbs
        MLSportsStrategy: apply predictions with Kelly
        Execution: route to PaperBettingAdapter
        Verify: signals generated, routed, paper-filled
    status: pending
    blocked_by: p1-arbitrage-wiring, p2-ml-strategy-wiring, p3-execution-routing

  # ============================================================================
  # GCS MIGRATION — WAIT FOR USER APPROVAL
  # ============================================================================
  - id: p5a-audit-buckets
    content: |
      - [ ] [HUMAN] P2. Audit old GCS buckets.
        Run: gsutil ls -r gs://instruments-store-sports-{project}/
        Document: bucket names, sizes, path formats
    status: pending
  - id: p5b-migration-script
    content: |
      - [ ] [AGENT] P2. Write GCS migration script.
        File: unified-trading-pm/scripts/sports/migrate_sports_gcs_to_hive.sh
        Pattern: market-tick-data-service/scripts/migrate_gcs_path_to_hive.py
        Transforms: day-YYYY-MM-DD -> day=YYYY-MM-DD, by-date -> by_date
        Features: dry-run mode, date range filter, server-side copy
        WAIT: Do not execute until user says "go"
    status: pending
    blocked_by: p5a-audit-buckets
  - id: p5c-execute-migration
    content: |
      - [ ] [HUMAN] P2. Execute GCS migration after user approval.
        1. Dry-run: review output
        2. Execute: server-side copy
        3. Verify: row counts match
        4. Archive old buckets (30-day grace)
    status: pending
    blocked_by: p5b-migration-script
---

# Sports Integration Plan 6: Strategy, Execution & GCS Migration

Part of the 6-plan sports integration series.
This is the FINAL plan — depends on all others.
GCS migration requires explicit user approval before execution.

## Success Criteria
- ArbitrageStrategy produces arb signals from MTDS odds
- MLSportsStrategy produces Kelly-sized signals from ML predictions
- Paper trading executes cleanly for 1 day
- GCS migration script passes dry-run (execution needs user approval)
