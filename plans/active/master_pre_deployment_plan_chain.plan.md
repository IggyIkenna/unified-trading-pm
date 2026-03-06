---
name: Master Pre-Deployment Plan Chain
overview: Ordered plan sequence (1–9) with parallel-work split for 2 people. CI/CD resolves conflicts. Deadlines: plans complete March 12, live trading week March 20.
todos:
  - id: plans-1-2-7
    content: "Week 1 — Workspace quickmerge validation, UI validation DUE. NOTE: Plan 7 (portable backtests) runs Days 8–9 (start of Week 2) — see e2e_smoke_and_portable_backtests.plan.md which states 'Day 8–9 in execution sequence'. Week 1 deadline applies to Plans 1–2 only."
    status: pending
  - id: plans-3-4
    content: "Weeks 2–3 — Phase 2 library tier hardening: coverage 70% + strict basedpyright. INVARIANT: T0 must reach D5 green before T1 starts; T1 before T2; T2 before T3. Each tier is a full day minimum. Global violation sweep (p2-global-violation-sweep) runs ONCE across all repos before tier work begins. Realistic span: T0 Day 2, T1 Day 3, T2 Days 4–5, T3 Day 6. Person A: T0–T2 (library-heavy); Person B: T2–T3 (interface-heavy). See phase2_library_tier_hardening.plan.md INVARIANT section."
    status: pending
  - id: plans-5-6-6a-8
    content: "Week 3 (overlap with Phase 2 T3) + Week 4 — Coding standards audit, unit tests, arb structure check, AWS migration. NOTE: Plans 5–6 cannot start until Phase 2 T0+T1 are green (Week 2). Plans 6a and 8 can run in parallel once T2 is green. Phase 3 service hardening begins in Week 3 after all library tiers (T0–T3) reach D5."
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
Week 1 (Mar 1–7):  Plans 1–2 (quickmerge validation, UI validation DUE)
                   Phase 0 audit remediation (parallel companion — blocks Phase 1)
Week 2 (Mar 8–11): Plan 7 (portable backtests: Day 8–9 per e2e_smoke_and_portable_backtests.plan.md)
                   Phase 2 T0 global sweep → T0 D5 green → T1 D5 green
                   [INVARIANT: T0 must fully green before T1 starts — no shortcuts]
Week 3 (Mar 11–14): Phase 2 T2 D5 green → T3 D5 green
                   Plans 5–6 (coding standards, unit tests) begin after T0+T1 green
                   Plans 6a, 8 (arb check, AWS) after T2 green
Week 4 (Mar 15–20): Phase 3 service hardening begins (after all T0–T3 green)
                   Plan 9 (full audit) gating live trading week
Live trading week: March 20
```

> **Phase 2 invariant (from phase2_library_tier_hardening.plan.md):** Never touch tier N until tier N-1 is fully green (all D5 passes). T0→T1→T2→T3 is a hard sequential constraint — parallelism is within a tier only (repos within T0 can be parallel; repos in T1 can run in parallel after ALL T0 repos pass D5). The master chain timeline above reflects this constraint. Plans 3–4 (Coverage + basedpyright) map 1:1 to Phase 2 and span Weeks 2–3.

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
