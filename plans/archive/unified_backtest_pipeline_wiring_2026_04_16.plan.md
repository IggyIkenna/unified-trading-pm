---
doc_type: plan
title: unified-backtest-pipeline-wiring
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, execution-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-17"
overview:
  Wire all standalone backtest engines into the unified pipeline. Batch=live same code path — strategy interacts with
  execution-service (matching engine), position-balance-monitor, risk-and-exposure, pnl-attribution in BOTH modes.
  Delete inline settlement. Covers sports (backtest_engine.py, sports_backtest_runner.py) and DeFi
  (colocated_engine.py).
type: code
epic: epic-code-completion
locked_by: live-defi-rollout
locked_since: 2026-04-16
completion_gates: { code: C5, deployment: none, business: B4 }
repo_gates:
  - { repo: execution-service, code: C0, deployment: none, business: none }
  - { repo: strategy-service, code: C0, deployment: none, business: none }
  - { repo: unified-api-contracts, code: C0, deployment: none, business: none }
  - { repo: position-balance-monitor-service, code: C0, deployment: none, business: none }
  - { repo: pnl-attribution-service, code: C0, deployment: none, business: none }
  - { repo: risk-and-exposure-service, code: C0, deployment: none, business: none }
  - { repo: e2e-testing, code: C0, deployment: none, business: none }
  - { repo: unified-trading-pm, code: C0, deployment: none, business: none }
depends_on: []
todos:
  - {
      id: pre-audit-violations,
      content:
        "- [ ] [AGENT] P0. Pre-audit: catalog every inline settlement, custom P&L calc, and service\n  bypass across all
        repos. Known violations:\n  (1) strategy-service/.../backtest_engine.py line 179: `returned = stake * odds if
        won else 0`\n  (2) strategy-service/.../sports_backtest_runner.py: uses SportsMatchingEngine but no
        PBMS/PnL/Risk\n  (3) e2e-testing/scripts/defi/colocated_engine.py lines 548-600: custom _compute_pnl()\n  Search
        for additional: `grep -r \"returned =.*stake.*odds\\|pnl =.*exit.*entry\\|realized_pnl.*=.*qty.*price\"
        --include=\"*.py\"` across all repos. Build manifest: repo, file, line, violation type.\n",
      status: todo,
    }
  - {
      id: uac-sports-fill-schema,
      content:
        "- [ ] [AGENT] P0. UAC: Verify CanonicalSportsFill and BetExecution schemas have all fields\n  needed by
        position-balance-monitor (fill_id, timestamp, instrument_id, quantity, price,\n  venue, client_id, strategy_id,
        commission). If missing fields, extend. SSOT:\n  unified_api_contracts/internal/domain/sports/execution.py.\n",
      status: todo,
    }
  - {
      id: uac-batch-mode-enum,
      content:
        "- [ ] [AGENT] P0. UAC: Ensure ExecutionMode enum includes BATCH_BENCHMARK (always-fill for\n  strategy alpha
        isolation) and BATCH_SIMULATED (matching engine with realistic fills for\n  execution alpha). Both return
        CanonicalFill/CanonicalSportsFill. Check\n  unified_api_contracts/internal/execution.py.\n",
      status: todo,
    }
  - {
      id: es-sports-matching-engine,
      content:
        "- [ ] [AGENT] P0. Execution-service: Create SportsMatchingEngine
        in\n  execution_service/engine/modes/batch/sports_matching_engine.py. Two modes:\n  (a) BATCH_BENCHMARK:
        always-fill at requested odds (zero execution alpha, isolates strategy P&L)\n  (b) BATCH_SIMULATED: fill with
        realistic assumptions — apply bookmaker margin (from UAC\n      EXCHANGE_COMMISSION_RATES), model
        latency-adjusted odds shift, reject if odds moved beyond\n      threshold (staleness), apply venue-specific max
        bet limits.\n  Interface: `async def match_bet(order: BetOrder, market_data: SportsMarketData) ->
        BetExecution`\n  Returns CanonicalSportsFill with fill_price, commission, slippage fields populated.\n",
      status: todo,
    }
  - {
      id: es-register-sports-matcher,
      content:
        "- [ ] [AGENT] P0. Execution-service: Register SportsMatchingEngine in BatchMatchingEngine\n  category routing
        (execution_service/engine/modes/batch/matching_engine.py). Currently\n  sports→BENCHMARK_FILL. Change to
        sports→SportsMatchingEngine dispatch, respecting\n  ExecutionMode (BATCH_BENCHMARK vs BATCH_SIMULATED).\n",
      status: todo,
    }
  - {
      id: es-sports-batch-cli,
      content:
        "- [ ] [AGENT] P1. Execution-service: Wire sports batch mode into CLI\n  `--operation execute --mode batch
        --asset-group SPORTS`. Handler reads BetOrder instructions\n  from GCS (strategy-service output), runs through
        SportsMatchingEngine, writes\n  CanonicalSportsFill to GCS for downstream consumption by PBMS and
        PnL-attribution.\n",
      status: todo,
    }
  - {
      id: qg-execution-service,
      content:
        "- [ ] [SCRIPT] P0. `cd execution-service && bash scripts/quality-gates.sh` — must pass after\n  Phases 0-1.
        Unit tests for SportsMatchingEngine (both modes), integration test verifying\n  BetOrder→CanonicalSportsFill
        round-trip.\n",
      status: todo,
    }
  - {
      id: ss-delete-inline-settlement,
      content:
        "- [ ] [AGENT] P0. Strategy-service: Delete inline settlement in backtest_engine.py.\n  Replace `returned =
        stake * Decimal(str(odds)) if won else Decimal(\"0\")` (line 179) with\n  call to execution-service matching
        engine via shared client. BacktestResult should be\n  computed from CanonicalSportsFill responses, not inline
        arithmetic. BankrollState.record_bet()\n  must consume fills, not raw odds.\n",
      status: todo,
    }
  - {
      id: ss-wire-pbms,
      content:
        "- [ ] [AGENT] P0. Strategy-service: After receiving fills from execution-service,
        forward\n  CanonicalSportsFill to position-balance-monitor-service for position state tracking.\n  In batch
        mode, PBMS runs co-located (same process or local gRPC). Strategy queries PBMS\n  for current position state
        before generating new signals. Wire into both\n  backtest_engine.py and sports_backtest_runner.py.\n",
      status: todo,
    }
  - {
      id: ss-wire-risk,
      content:
        "- [ ] [AGENT] P1. Strategy-service: Wire risk-and-exposure-service into sports batch flow.\n  After position
        updates, query risk service for exposure metrics (total committed bankroll,\n  per-venue concentration, max
        drawdown). Strategy respects risk limits before emitting new\n  signals. In batch mode, risk-service runs
        co-located.\n",
      status: todo,
    }
  - {
      id: ss-wire-pnl,
      content:
        "- [ ] [AGENT] P1. Strategy-service: Wire pnl-attribution-service into sports batch flow.\n  At end of each
        batch day, call PnL attribution with fills + positions + instructions.\n  Produces per-strategy P&L breakdown
        (edge_capture, odds_movement, commission, execution_alpha).\n  Replace BankrollState.true_roi_pct with
        PnL-attribution output.\n",
      status: todo,
    }
  - {
      id: ss-backtest-cli-integration,
      content:
        "- [ ] [AGENT] P1. Strategy-service: Integrate sports backtest into CLI\n  `--operation backtest --mode batch
        --asset-group SPORTS`. Handler orchestrates:\n  load features → generate signals → send BetOrders to
        execution-service → receive fills →\n  update PBMS → compute risk → compute PnL. Same code path as live,
        different fill source.\n",
      status: todo,
    }
  - {
      id: qg-strategy-service,
      content:
        "- [ ] [SCRIPT] P0. `cd strategy-service && bash scripts/quality-gates.sh` — must pass after\n  Phase 2. Tests
        verify: no inline settlement, fills come from execution-service, positions\n  tracked by PBMS, P&L from
        attribution service.\n",
      status: todo,
    }
  - {
      id: e2e-colocated-use-pnl-service,
      content:
        "- [ ] [AGENT] P0. e2e-testing: colocated_engine.py already imports compute_pnl_breakdown\n  from
        pnl-attribution-service but ignores it (line 550). Delete custom _compute_pnl()\n  (lines 548-600) and wire
        through the imported function. Verify P&L matches.\n",
      status: todo,
    }
  - {
      id: e2e-colocated-use-pbms,
      content:
        "- [ ] [AGENT] P0. e2e-testing: colocated_engine.py uses SharedState.positions dict for\n  manual position
        tracking (lines 252-296). Replace with position-balance-monitor-service\n  calls (co-located). delete
        update_position() custom logic.\n",
      status: todo,
    }
  - {
      id: e2e-colocated-use-risk,
      content:
        "- [ ] [AGENT] P1. e2e-testing: colocated_engine.py has custom _compute_risk(). Replace\n  with
        risk-and-exposure-service calls (co-located). Delete custom risk computation.\n",
      status: todo,
    }
  - {
      id: qg-e2e-testing,
      content:
        "- [ ] [SCRIPT] P0. `cd e2e-testing && bash scripts/quality-gates.sh` — must pass after\n  Phase 3. Verify
        colocated_engine no longer has custom P&L/position/risk logic.\n",
      status: todo,
    }
  - {
      id: pbms-sports-fill-handler,
      content:
        "- [ ] [AGENT] P1. Position-balance-monitor-service: Ensure fill handler can consume\n  CanonicalSportsFill
        (BetExecution). Sports positions are per-fixture bets, not\n  continuous positions. Position = open bet
        (fixture_id, selection, stake, odds).\n  Settlement = bet settled (win/loss/void at event end). May need
        BetPositionTracker\n  alongside existing PositionTracker.\n",
      status: todo,
    }
  - {
      id: pnl-sports-attribution,
      content:
        "- [ ] [AGENT] P1. PnL-attribution-service: Ensure sports P&L attribution handles\n  bet-level settlement.
        Components: edge_capture (win/loss), odds_movement (CLV),\n  commission (exchange fees), execution_alpha
        (requested vs filled odds).\n  Verify compute_pnl_breakdown() works with sports fill schema.\n",
      status: todo,
    }
  - {
      id: risk-sports-exposure,
      content:
        "- [ ] [AGENT] P1. Risk-and-exposure-service: Ensure sports exposure tracking works.\n  Exposure = total stake
        committed across open bets. Per-venue concentration.\n  Max single-event exposure. Per-league correlation.\n",
      status: todo,
    }
  - {
      id: qg-downstream-services,
      content:
        "- [ ] [SCRIPT] P0. Run QG on all downstream services:\n  `cd position-balance-monitor-service && bash
        scripts/quality-gates.sh`\n  `cd pnl-attribution-service && bash scripts/quality-gates.sh`\n  `cd
        risk-and-exposure-service && bash scripts/quality-gates.sh`\n",
      status: todo,
    }
  - {
      id: e2e-sports-pipeline-test,
      content:
        "- [ ] [AGENT] P0. e2e-testing: Create test_unified_sports_backtest.py that validates\n  the full pipeline:
        strategy-service emits BetOrders → execution-service\n  (SportsMatchingEngine BATCH_BENCHMARK) returns fills →
        PBMS tracks positions →\n  PnL-attribution computes P&L → risk-service computes exposure. Verify zero
        inline\n  settlement, all P&L comes from attribution service, all positions from PBMS.\n",
      status: todo,
    }
  - {
      id: e2e-defi-pipeline-test,
      content:
        "- [ ] [AGENT] P0. e2e-testing: Verify colocated_engine.py DeFi pipeline uses same\n  pattern. Strategy →
        execution-service (BatchMatchingEngine) → PBMS → PnL → risk.\n  No custom _compute_pnl or manual position
        tracking.\n",
      status: todo,
    }
  - {
      id: e2e-execution-alpha-test,
      content:
        "- [ ] [AGENT] P1. e2e-testing: Create test_execution_alpha_separation.py that validates\n  dual-mode: (1)
        BATCH_BENCHMARK run → strategy alpha only (zero execution alpha).\n  (2) BATCH_SIMULATED run → strategy alpha +
        execution alpha.\n  Verify execution_alpha = simulated_pnl - benchmark_pnl per trade.\n",
      status: todo,
    }
  - {
      id: codex-batch-live-architecture,
      content:
        "- [ ] [AGENT] P1. PM: Write codex doc `/codex/04-architecture/batch-live-pipeline.md`\n  documenting the
        unified pipeline architecture. Include: component interaction diagram\n  (strategy→execution→PBMS→PnL→risk), two
        execution modes (BENCHMARK vs SIMULATED),\n  strategy alpha vs execution alpha separation, how batch and live
        share 99% code path.\n",
      status: todo,
    }
  - {
      id: codex-update-strategy-docs,
      content:
        "- [ ] [AGENT] P2. PM: Update all sports strategy docs in codex/09-strategy/sports/ to\n  reference the unified
        pipeline (not standalone backtest). Remove any references to\n  inline settlement or standalone backtest
        engines.\n",
      status: todo,
    }
  - {
      id: qg-workspace-final,
      content:
        "- [ ] [SCRIPT] P0. Run QG on ALL affected repos:\n  execution-service, strategy-service, e2e-testing,
        position-balance-monitor-service,\n  pnl-attribution-service, risk-and-exposure-service,
        unified-trading-pm.\n  All must pass. No inline settlement in any repo.\n",
      status: todo,
    }
isProject: false
superseded_by: [strategy_architecture_v2_phase3_11_handoff_2026_04_17.md]
reconciliation_status: superseded
reconciliation_date: 2026-04-25
---

> **SUPERSEDED 2026-04-25 by
> [strategy_architecture_v2_phase3_11_handoff_2026_04_17.md](./strategy_architecture_v2_phase3_11_handoff_2026_04_17.md).**
> Phase 10 of strategy-arch-v2 covers the canonical batch=live pattern (a7b63ce, aa3c6c0, 2d05e58) Original scope
> retained for history. See `_reconciliation_evidence_map_2026_04_25.md` for evidence.

## Context

### Architectural Principle (CLAUDE.md)

Batch and live use the SAME code path, same component interactions. The ONLY difference is execution fills. This applies
to ALL categories — sports, DeFi, CeFi, TradFi.

- **Strategy P&L backtest (strategy alpha):** Execution-service in "always fill" mode (BATCH_BENCHMARK). Zero execution
  alpha. Isolates strategy P&L.
- **Execution alpha measurement:** Execution-service matching engine (BATCH_SIMULATED) with realistic fills. Execution
  alpha = live P&L - simulated P&L.

### Pre-Audit Manifest

| Repo             | File                                               | Line    | Violation                                           | Action                                         |
| ---------------- | -------------------------------------------------- | ------- | --------------------------------------------------- | ---------------------------------------------- |
| strategy-service | engine/strategies/sports/backtest_engine.py        | 179     | Inline settlement: `returned = stake * odds if won` | Delete, use execution-service fills            |
| strategy-service | engine/strategies/sports/backtest_engine.py        | 44-85   | BankrollState custom P&L tracking                   | Replace with PBMS + PnL-attribution            |
| strategy-service | engine/strategies/sports/backtest_engine.py        | 171-177 | Direct outcome computation                          | Move to execution-service settlement           |
| strategy-service | engine/strategies/sports/sports_backtest_runner.py | \*      | Uses SportsMatchingEngine but no PBMS/PnL/Risk      | Wire downstream services                       |
| e2e-testing      | scripts/defi/colocated_engine.py                   | 548-600 | Custom \_compute_pnl()                              | Use pnl-attribution-service (already imported) |
| e2e-testing      | scripts/defi/colocated_engine.py                   | 252-296 | Custom update_position()                            | Use position-balance-monitor                   |
| e2e-testing      | scripts/defi/colocated_engine.py                   | 550     | Imports compute_pnl_breakdown but ignores it        | Wire it in                                     |

### Execution DAG

```
Phase 0: Pre-audit + UAC schema gaps
    │
    ▼
Phase 1: Execution-service SportsMatchingEngine
    │
    ├── QG gate: execution-service
    │
    ▼
Phase 2: Strategy-service wiring          Phase 3: DeFi colocated fix     Phase 4: PBMS/PnL/Risk sports
    │ (PARALLEL)                               │ (PARALLEL)                     │ (PARALLEL)
    │                                          │                                │
    ├── QG gate: strategy-service              ├── QG gate: e2e-testing         ├── QG gate: downstream
    │                                          │                                │
    ▼                                          ▼                                ▼
Phase 5: E2E pipeline validation (requires Phases 2+3+4 complete)
    │
    ▼
Phase 6: Documentation
    │
    ▼
Final QG: all repos pass
```

### Success Criteria

- **C4:** `quality-gates.sh` passes on all 7 repos
- **B4:** Batch output (strategy P&L) matches within 2% of equivalent live-mock run
- **Zero inline settlement:** `grep -r "returned =.*stake.*odds" --include="*.py"` returns 0 results across all repos
- **Service mesh exercised:** Every batch backtest goes through strategy→execution→PBMS→PnL→risk
