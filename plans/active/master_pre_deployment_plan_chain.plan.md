---
name: Master Pre-Deployment Plan Chain
overview: Ordered plan sequence (1–9) with parallel-work split for 2 people. CI/CD resolves conflicts. Deadlines: plans complete March 12, live trading week March 20.
todos:
  - id: plans-1-2-7
    content: Week 1 — Workspace quickmerge, UI validation, portable backtests DUE
    status: pending
  - id: plans-3-4
    content: Week 2 — Coverage 70%, strict basedpyright (parallel by tier)
    status: pending
  - id: plans-5-6-6a-8
    content: Week 3 — Coding standards audit, unit tests, Arb structure check, AWS migration
    status: pending
  - id: plan-9-audit
    content: "Week 4 — Full audit (trading_system_audit_prompt.plan.md all sections PASS); live trading week SUCCESS. SUCCESS DEFINITION: (1) PnL: breakeven or better across the 5-day week (total net PnL ≥ 0); (2) Reliability: ≤3 unhandled exceptions logged across all services; zero circuit breaker trips; (3) Execution: all orders placed within 500ms of signal emission (measured via execution_alpha.json latency field); (4) Coverage: at least one completed live trade per strategy category (sports arb, CEFI ML signal, TradFi ML signal, at least one DeFi MVP); (5) Audit: trading_system_audit_prompt.plan.md achieves grade A or better (no FAIL items, ≤3 WARN)."
    status: pending
  - id: branch-isolation
    content: Use --dep-branch for conflict resolution; merge in dependency order
    status: pending
isProject: false
---

# Master Pre-Deployment Plan Chain

**Purpose:** Ordered plan sequence with parallel-work split for 2 people. CI/CD resolves conflicts.

---

## Deadlines

| Milestone                               | Date               |
| --------------------------------------- | ------------------ |
| All plans complete + portable backtests | **March 12, 2026** |
| Successful week of live trading         | **March 20, 2026** |

---

## Strategy Scope (by March 20)

At least one strategy per category:

| Category   | Strategy                                                | Reference                                 |
| ---------- | ------------------------------------------------------- | ----------------------------------------- |
| **Sports** | Arb                                                     | sports-integration-plan, strategy-service |
| **CEFI**   | ML signal                                               | mvp-universe strategies.cefi_mvp          |
| **TradFi** | ML signal                                               | mvp-universe strategies.tradfi_mvp        |
| **DeFi**   | 4 MVP: staking, lending, recursive staking, basis trade | mvp-universe strategies.defi_mvp          |

---

## Order Chain (Labels 1–9)

| Order | Plan                                 | Person A                                      | Person B                                                    | Conflict Risk              |
| ----- | ------------------------------------ | --------------------------------------------- | ----------------------------------------------------------- | -------------------------- |
| 1     | WORKSPACE_QUICKMERGE_VALIDATION_PLAN | Script + T0–T2                                | T3–services                                                 | Low (different repos)      |
| 2     | UI_VALIDATION_PLAN                   | deployment-ui, batch-audit-ui, ml-training-ui | execution-analytics-ui, strategy-ui, etc.                   | Low (different UIs)        |
| 3     | COVERAGE_70_PERCENT_PLAN             | T0–T1 libraries                               | T2–T3 + services                                            | Low (tier split)           |
| 4     | STRICT_BASEDPYRIGHT_COMPLIANCE_PLAN  | T0–T1                                         | T2–T3 + services                                            | Low (tier split)           |
| 5     | CODING_STANDARDS_CODEX_AUDIT_PLAN    | Audit + fix T0–T2                             | Audit + fix T3–services                                     | Low (different repos)      |
| 6     | UNIT_TESTS_ALL_PASSING_PLAN          | Fix T0–T2 tests                               | Fix T3–service tests                                        | Medium (shared deps)       |
| 6a    | **Arb structure check (C.1)**        | —                                             | Check batch→live flow; document in plans/active or plans/ai | Low                        |
| 7     | PORTABLE_BACKTESTS_PLAN              | Strategy backtests (CEFI, TradFi, DeFi)       | Sports arb backtest                                         | Low (different strategies) |
| 8     | AWS_MIGRATION_PLAN                   | Cloud-agnostic verification                   | buildspec.aws.yaml per service                              | Low (different repos)      |
| 9     | FULL_AUDIT_PLAN                      | Run after 1–8                                 | —                                                           | Sequential                 |

---

## Parallel-Work Split (2 People)

### Person A (Track 1)

- Repos: T0–T2 libraries, deployment-ui, batch-audit-ui, ml-training-ui, live-health-monitor-ui
- Plans: 1 (T0–T2), 2 (first 4 UIs), 3 (T0–T1), 4 (T0–T1), 5 (T0–T2), 6 (T0–T2), 7 (CEFI/TradFi/DeFi backtests), 8 (cloud-agnostic)

### Person B (Track 2)

- Repos: T3, services, remaining UIs
- Plans: 1 (T3–services), 2 (remaining UIs), 3 (T2–T3 + services), 4 (T2–T3 + services), 5 (T3–services), 6 (T3–services), 6a (Arb structure check), 7 (Sports arb backtest), 8 (buildspec.aws.yaml)

---

## CI/CD Conflict Resolution

1. **Branch isolation:** Each person uses `--dep-branch "person-a"` or `--dep-branch "person-b"`
2. **Quickmerge cascade:** Dependencies merged first; quickmerge validates before commit
3. **Staging merge order:** Person A merges first (T0–T2), then Person B (T3–services)
4. **Or:** Work on different tiers; merge staging in dependency order (T0→T1→T2→T3→services)
5. **Same repo:** Split by directory (e.g. Person A: engine/, Person B: adapters/) — coordinate merge order

---

## Same-Repo Strategy

When both touch same repo:

- **Option A:** Person A completes Plan 3 for repo; Person B does Plan 4 after. Sequential.
- **Option B:** Split by directory; use `--files` in quickmerge to stage only changed paths; merge A→B or B→A.
- **Option C:** Person A: one repo; Person B: different repo. Avoid same repo when possible.

---

## Execution Flow

```
Week 1 (to Mar 12): Plans 1–2, 7 (portable backtests DUE)
Week 2: Plans 3–4 (Parallel by tier)
Week 3: Plans 5–6, 6a (Arb structure), 8 (Parallel by tier)
Week 4 (to Mar 20): Plan 9 (Full audit); live trading week SUCCESS
```

---

## Options / Post-Sprint (C.2–C.7)

**Sprint end:** March 12th. These items are not blocking first deployment.

| ID  | Item                                                      | Notes                                                                                           |
| --- | --------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| C.2 | Alerting-Service → Slack + PagerDuty                      | Critical → PagerDuty; warning → Slack. Likely post–first-deployment.                            |
| C.3 | API Audit (Compliance, Reporting, Analytics, Backtesting) | Separation of concerns; create focused plan post-sprint.                                        |
| C.4 | Reconciliation and Rebalancing                            | ic-rebalance-instruction, reconciliation-service; defer unless blocking.                        |
| C.5 | Execution Services Cleanup                                | 57 fail (VWAP/sports/mocks); UI violation (visualizer embedded). Triage: blocks vs post-sprint. |
| C.6 | Repo Audit (Repo-by-Repo)                                 | run_validators.py --scope/--repo-type; REPO_AUDIT_CHECKLIST.md.                                 |
| C.7 | Anything Else From Plans Not Done                         | Scan consolidated_remaining_work; extract to SPRINT_BACKLOG. No \*\_SUMMARY.md.                 |

## References

- quickmerge.sh (--dep-branch, cascade)
- always-use-quickmerge.mdc
- feature-branch-workflow.md
- plans_to_deployable_unified_audit.plan.md
- AWS_MIGRATION_PLAN.md
- PORTABLE_BACKTESTS_PLAN.md
