---
name: master-pre-deployment-plan-chain
overview: Ordered plan sequence (1–9) with parallel-work split for 2 people. CI/CD resolves conflicts. Deadlines: plans complete March 12, live trading week March 20.
type: mixed
epic: none
status: active

completion_gates:
  code: C5
  deployment: D3
  business: none

repo_gates:
  - repo: unified-trading-pm
    code: C5
    deployment: none
    business: none
    readiness_note: "C5: all quality gates passing. DR N/A: orchestration plan tracking ordered plan execution — no direct cloud deployment artifact. BR N/A: plan-chain sequencing does not gate on commercial sign-off."

depends_on: []

todos:
  - id: phase0-environment
    content: "Phase 0 — Audit Remediation (phase0_audit_remediation.plan.md). All 5 streams complete: secrets/UCI/config (S1), UTL/FDS (S2), instruments/strategy/ml-training/deployment (S3), execution/MTDS/sports (S4), WARN cleanup (S5)."
    status: done
    notes: "DONE 2026-03-07. All todos in archive/phase0_audit_remediation.plan.md marked done. Grade D → remediated."
  - id: phase0b-audit-standards
    content: "Phase 0b — Workspace Audit Remediation 2026-03-07 (workspace_audit_remediation_2026_03_07.plan.md). 10 FAILs + 47 WARNs resolved. Two pending items remain: fix-cloudbuild-template-drift (P4, low) and fix-coverage-pct-placeholders (P4, low)."
    status: done
    notes: "DONE 2026-03-07. All P0/P1/P2/P3 items completed. Two P4 (low) items remain but do not block Phase 1 or Phase 2."
  - id: phase1-foundation
    content: "Phase 1 — Foundation & Prep (archive/phase1_foundation_prep.plan.md). Three streams: STREAM A (CI/CD: quickmerge rollout, commit-msg hooks, pipeline wiring), STREAM B (deployment structure: visualizer extract, UTD V3 four-way split, UI audit, infra merge, hybrid live seam), STREAM C (QG baseline: cursor rules, manifest schema, quality gates, Cloud Build audit, AWS parity). All todos marked done or completed."
    status: done
    notes: "DONE 2026-03-06. Plan archived. All STREAM A/B/C items complete. Phase 1 done criteria met: 55 repos have quickmerge + version-bump.yml; deployment-service/api/ui/system-integration-tests split; all 3 cursor rules created; manifest schema extended; QG baseline recorded; AWS parity (buildspec.aws.yaml on all 45 repos)."
  - id: import-audit-b9-terraform
    content: "import_audit_2026_03_08 — B9 Terraform verification. Check deployment-service/terraform/gcp/ and deployment-service/terraform/aws/ exist and are complete (moved from ibkr-gateway-infra/ per infra-merge-utdv3 task in Phase 1)."
    status: done
    notes: "VERIFIED 2026-03-08. deployment-service/terraform/gcp/ contains main.tf, outputs.tf, secret_rotation.tf, variables.tf. deployment-service/terraform/aws/ contains main.tf, outputs.tf, variables.tf. Terraform files complete — B9 closed."
  - id: plans-1-2-7
    content: "Week 1 — Workspace quickmerge validation, UI validation DUE. NOTE: Plan 7 (portable backtests) runs Days 8–9 (start of Week 2) — see e2e_smoke_and_portable_backtests.plan.md which states 'Day 8–9 in execution sequence'. Week 1 deadline applies to Plans 1–2 only."
    status: in_progress
    notes: "Plans 1–2 (quickmerge rollout + UI validation) functionally complete as part of Phase 1 Foundation. Plan 7 (portable backtests) is active in e2e_smoke_and_portable_backtests.plan.md — pending execution of backtest runs."
  - id: plans-3-4
    content: "Weeks 2–3 — Phase 2 library tier hardening: coverage 70% + strict basedpyright. INVARIANT: T0 must reach D5 green before T1 starts; T1 before T2; T2 before T3. Each tier is a full day minimum. Global violation sweep (p2-global-violation-sweep) runs ONCE across all repos before tier work begins. Realistic span: T0 Day 2, T1 Day 3, T2 Days 4–5, T3 Day 6. Person A: T0–T2 (library-heavy); Person B: T2–T3 (interface-heavy). See phase2_library_tier_hardening.plan.md INVARIANT section."
    status: in_progress
    notes: |
      Phase 2 status (2026-03-08):
        p2-global-violation-sweep: DONE — T0/T1/T2/T3 source packages all clean.
        t0-tests-first: DONE — Layer 0 contract alignment tests pass; all 6 T0 repos unit tests pass (D2).
        t0-progressive-validation: IN_PROGRESS — D1/D2/D3 PASS (ruff clean, 71/71 UEI, 666/666 AC, 608/608 UIC, 227/227 URDI, 94/94 EAL, 83/83 MEL tests). D4/D5 (quickmerge) not yet run per session rules.
        t0-deploy-structure: pending (not yet started).
        t0-code-rewrite: pending.
        T1/T2/T3 all pending (T0 not yet at D5 green — invariant blocks T1 start).
  - id: plans-5-6-6a-8
    content: "Week 3 (overlap with Phase 2 T3) + Week 4 — Coding standards audit, unit tests, arb structure check, AWS migration. NOTE: Plans 5–6 cannot start until Phase 2 T0+T1 are green (Week 2). Plans 6a and 8 can run in parallel once T2 is green. Phase 3 service hardening begins in Week 3 after all library tiers (T0–T3) reach D5."
    status: pending
    notes: "Blocked on Phase 2 T0 reaching D5 green. AWS parity (buildspec.aws.yaml) already complete as part of Phase 1 (DONE 2026-03-06 — all 45 repos). Arb structure check (6a) can begin independently."
  - id: plan-9-audit
    content: "Week 4 — Full audit (trading_system_audit_prompt.plan.md all sections PASS); live trading week SUCCESS. SUCCESS DEFINITION: (1) PnL: breakeven or better across the 5-day week (total net PnL ≥ 0); (2) Reliability: ≤3 unhandled exceptions logged across all services; zero circuit breaker trips; (3) Execution: all orders placed within 500ms of signal emission (measured via execution_alpha.json latency field); (4) Coverage: at least one completed live trade per strategy category (sports arb, CEFI ML signal, TradFi ML signal, at least one DeFi MVP); (5) Audit: trading_system_audit_prompt.plan.md achieves grade A or better (no FAIL items, ≤3 WARN)."
    status: in_progress
    notes: "trading_system_audit_prompt.plan.md active (2026-03-08). Section 1 (manifest/versions) completed. Sections 2–10 all pending. Audit report in progress — full run pending after Phase 2 T0 green."
  - id: branch-isolation
    content: >
      Conflict resolution via automatic branch detection from workspace-manifest.json active_feature_branch
      (currently: live-defi-rollout). Merge in dependency order (T0→T1→T2→T3→T4).
      NOTE (2026-03-13 audit): REMOVED --dep-branch reference. CLAUDE.md rules state "NEVER use --dep-branch
      in agent/Claude Code sessions — it is a human-only flag." Quickmerge reads the branch automatically
      from active_feature_branch in workspace-manifest.json. For conflicts: commit dep repo first, then
      re-run downstream repo.
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

## Phase Status Summary (as of 2026-03-08)

| Phase                  | Plan File                                      | Status      | Notes                                                                                   |
| ---------------------- | ---------------------------------------------- | ----------- | --------------------------------------------------------------------------------------- |
| Phase 0 — Environment  | archive/phase0_audit_remediation.plan.md       | **DONE**    | All 5 streams complete (2026-03-07)                                                     |
| Phase 0b — Audit       | workspace_audit_remediation_2026_03_07.plan.md | **DONE**    | 10 FAILs + 47 WARNs resolved; 2 P4 items remain (non-blocking)                          |
| Phase 1 — Foundation   | archive/phase1_foundation_prep.plan.md         | **DONE**    | All STREAM A/B/C items complete (2026-03-06); plan archived                             |
| B9 Terraform           | (import_audit_2026_03_08 item)                 | **DONE**    | deployment-service/terraform/gcp/ + aws/ verified complete                              |
| Phase 2 — Library Tier | phase2_library_tier_hardening.plan.md          | IN_PROGRESS | T0 D1/D2/D3 PASS; D4/D5 pending; T1–T3 not yet started (T0 invariant)                   |
| Phase 3 — Services     | phase3_service_hardening_integration.plan.md   | PENDING     | Blocked on Phase 2 T0–T3 all green (D5)                                                 |
| Phase 4 — Integration  | (schema robustness + layer 1 tests)            | IN_PROGRESS | Layer 0 contract tests done; Layer 1 schema robustness in plan todos; Layer 2–3 blocked |
| Phase 5 — Pre-Deploy   | (deploy infra gates)                           | PENDING     | Blocked: deploy infrastructure not yet provisioned                                      |
| Phase 6 — Cloud Build  | aws_migration.plan.md                          | PENDING     | buildspec.aws.yaml complete on all repos; blocked on AWS account/CodeBuild access       |
| Phase 7 — Final Audit  | trading_system_audit_prompt.plan.md            | IN_PROGRESS | Section 1 done (2026-03-08); full audit run pending Phase 2 completion                  |
| Plan 9 — Live Trading  | (March 20 gate)                                | PENDING     | All phases must complete first                                                          |

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
- Plans: 1 (T0–T2), 2 (first 4 UIs), 3 (T0–T1), 4 (T0–T1), 5 (T0–T2), 6 (T0–T2), 7 (CEFI/TradFi/DeFi backtests), 8
  (cloud-agnostic)

### Person B (Track 2)

- Repos: T3, services, remaining UIs
- Plans: 1 (T3–services), 2 (remaining UIs), 3 (T2–T3 + services), 4 (T2–T3 + services), 5 (T3–services), 6
  (T3–services), 6a (Arb structure check), 7 (Sports arb backtest), 8 (buildspec.aws.yaml)

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
Week 1 (Mar 1–7):  Plans 1–2 (quickmerge validation, UI validation DUE)      ← DONE
                   Phase 0 audit remediation (parallel companion)              ← DONE
Week 2 (Mar 8–11): Plan 7 (portable backtests: Day 8–9)                       ← IN_PROGRESS
                   Phase 2 T0 global sweep → T0 D5 green → T1 D5 green        ← IN_PROGRESS (T0 D1/D2/D3 done)
                   [INVARIANT: T0 must fully green before T1 starts]
Week 3 (Mar 11–14): Phase 2 T2 D5 green → T3 D5 green                        ← PENDING
                   Plans 5–6 (coding standards, unit tests) begin after T0+T1 green
                   Plans 6a, 8 (arb check, AWS) after T2 green
Week 4 (Mar 15–20): Phase 3 service hardening begins (after all T0–T3 green)  ← PENDING
                   Plan 9 (full audit) gating live trading week
Live trading week: March 20
```

> **Phase 2 invariant (from phase2_library_tier_hardening.plan.md):** Never touch tier N until tier N-1 is fully green
> (all D5 passes). T0→T1→T2→T3 is a hard sequential constraint — parallelism is within a tier only (repos within T0 can
> be parallel; repos in T1 can run in parallel after ALL T0 repos pass D5). The master chain timeline above reflects
> this constraint. Plans 3–4 (Coverage + basedpyright) map 1:1 to Phase 2 and span Weeks 2–3.

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
- phase-gate-checklist.md (unified-trading-pm/docs/)
