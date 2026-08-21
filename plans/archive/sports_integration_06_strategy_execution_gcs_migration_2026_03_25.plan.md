---
doc_type: plan
title: sports-integration-06-strategy-execution-gcs-migration
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-25'
remaining_todos_consolidated_into: consolidated_sports_prediction_pipeline_2026_04_15
superseded_by: [consolidated_sports_prediction_pipeline_2026_04_15.md]
reconciliation_status: superseded_by_consolidator
reconciliation_date: 2026-04-25
overview: 'Wire arbitrage detection + ML-based betting + execution routing.

  ArbitrageStrategy reads MTDS odds, MLSportsStrategy reads ML predictions.

  Execution routes through execution-service sports_execution sub-package (Betfair, Pinnacle via Odds API, paper trading).

  GCS migration is LAST — old buckets to hive format, needs user approval before execute.

  '
type: code
epic: epic-code-completion
completion_gates: {code: C4, deployment: D3, business: B4}
repo_gates:
- {repo: strategy-service, code: C0, notes: Wire ArbitrageStrategy + MLSportsStrategy to data sources}
- {repo: execution-service, code: C0, notes: Verify sports routing through execution-service sports_execution sub-package}
- {repo: execution-service (sports_execution/ sub-package), code: C0, notes: Verify Betfair + paper trading adapters}
- {repo: unified-trading-pm, code: C0, notes: GCS migration script}
depends_on: [sports-integration-05-ml-training-pipeline]
isProject: false
todos:
- {id: p1-arbitrage-wiring, content: "- [x] [AGENT] P1. Verify ArbitrageStrategy reads from MTDS GCS output.\n  DONE: ArbitrageStrategy exists and reads odds parquet.\n  File: strategy_service/engine/strategies/sports/arbitrage.py\n  Input: odds parquet (64 bookmakers per fixture)\n  Logic: GROUP BY fixture + market + selection, compare max/min prices\n  Output: TradeSignal with venue pair, odds, implied profit\n", status: done}
- {id: p2-ml-strategy-wiring, content: "- [x] [AGENT] P1. Verify MLSportsStrategy reads from ml-inference output.\n  DONE: MLSportsStrategy exists and reads model probabilities.\n  File: strategy_service/engine/strategies/sports/ml_sports_strategy.py\n  Input: model probabilities (home/draw/away)\n  Logic: Kelly sizing, confidence gate, max-odds gate\n  Output: TradeSignal with venue, odds, stake\n", status: done, correction: '2026-08-15 REVERTED/CORRECTED by review (per measurement-claims-discipline — confirmed via full-repo grep + find, not a truncated read): FALSE. Neither a `MLSportsStrategy` class nor `strategy_service/engine/strategies/sports/ml_sports_strategy.py` exist anywhere in the workspace (`grep -rlP "class MLSportsStrategy\b" --include=*.py` and `find . -iname ml_sports_strategy.py` both 0 hits). No ML-probability-based sports strategy was ever shipped at this location — this row was never actually done despite the 2026-03-25 done-mark. NOT abandoned: the intended capability (ML model P(outcome) vs vig-free implied odds, confidence/max-odds gates, fractional Kelly stake, 1X2/O-U/BTTS/1H markets) now exists as the architecture-v2 ML_DIRECTIONAL_EVENT_SETTLED archetype — strategy_service/engine/strategies/v2/ml_directional/event_settled.py::MLDirectionalEventSettledEngine (substantive, 169 lines, real on_tick/_select_outcome/_evaluate_edge/_compute_stake logic, no stub markers) — wired to 3 sports slots in archetype_slots_sports.py (unity-epl-1x2-gbp-v5-prod, unity-epl-matchwinner-gbp-v5-prod, betfair-epl-halftime-gbp-v5-prod). See /codex/09-strategy/architecture-v2/archetypes/ml-directional-event-settled.md for the current spec.'}
- {id: p3-execution-routing, content: "- [ ] [AGENT] P1. Verify execution-service routes sports signals through sports_execution sub-package.\n  File: execution_service/sports_execution/adapters/sports_router.py\n  Routing: TradeSignal.venue -> sports_execution adapter (Betfair, Pinnacle, paper)\n  Paper mode: all signals to PaperBettingAdapter\n", status: pending}
- {id: p4-paper-trading, content: "- [ ] [AGENT] P0. Run paper trade for March 22 fixtures.\n  ArbitrageStrategy: scan 35K odds for arbs\n  MLSportsStrategy: apply predictions with Kelly\n  Execution: route to PaperBettingAdapter\n  Verify: signals generated, routed, paper-filled\n", status: pending, blocked_by: 'p1-arbitrage-wiring, p2-ml-strategy-wiring, p3-execution-routing'}
- {id: p5a-audit-buckets, content: "- [ ] [HUMAN] P2. Audit old GCS buckets.\n  Run: gsutil ls -r gs://instruments-store-sports-{project}/\n  Document: bucket names, sizes, path formats\n", status: pending}
- {id: p5b-migration-script, content: "- [ ] [AGENT] P2. Write GCS migration script.\n  File: unified-trading-pm/scripts/sports/migrate_sports_gcs_to_hive.sh\n  Pattern: market-tick-data-service/scripts/migrate_gcs_path_to_hive.py\n  Transforms: day-YYYY-MM-DD -> day=YYYY-MM-DD, by-date -> by_date\n  Features: dry-run mode, date range filter, server-side copy\n  WAIT: Do not execute until user says \"go\"\n", status: pending, blocked_by: p5a-audit-buckets}
- {id: p5c-execute-migration, content: "- [ ] [HUMAN] P2. Execute GCS migration after user approval.\n  1. Dry-run: review output\n  2. Execute: server-side copy\n  3. Verify: row counts match\n  4. Archive old buckets (30-day grace)\n", status: pending, blocked_by: p5b-migration-script}
---

> **SUPERSEDED 2026-04-25 by
> [consolidated_sports_prediction_pipeline_2026_04_15.md](./consolidated_sports_prediction_pipeline_2026_04_15.md).**
> Original scope retained for history. Frontmatter `remaining_todos_consolidated_into:` was already present; this commit
> formalises it as canonical `superseded_by:` and adds this banner. See `_reconciliation_evidence_map_2026_04_25.md` for
> evidence.

# Sports Integration Plan 6: Strategy, Execution & GCS Migration

Part of the 6-plan sports integration series. This is the FINAL plan — depends on all others. GCS migration requires
explicit user approval before execution.

## Success Criteria

- ArbitrageStrategy produces arb signals from MTDS odds
- MLSportsStrategy produces Kelly-sized signals from ML predictions
- Paper trading executes cleanly for 1 day
- GCS migration script passes dry-run (execution needs user approval)
