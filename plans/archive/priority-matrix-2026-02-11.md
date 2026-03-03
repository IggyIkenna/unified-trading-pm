# Priority Matrix (Eisenhower Matrix)

**Last Updated:** 2026-02-11
**Based on:** Audit Stage 3 findings (110-item checklist)

---

## Purpose

This matrix organizes all work items from the batch and live roadmaps using the Eisenhower Matrix framework:

- **Urgent + Important (Do First):** P0 items that block production
- **Important but Not Urgent (Schedule):** P1 items that should be done before production
- **Urgent but Not Important (Delegate):** Quick wins and tech debt
- **Neither (Eliminate):** P3 items and future enhancements (do later or never)

## Program Context (Audit Gaps + New Requests)

This matrix is not only for new capability requests. It is the primary planning surface for:

- existing audit-remediation deficits (current non-compliance against codex standards),
- and normalized new requests from the request-card intake flow.

Both groups run through the same PM lifecycle:

`pending -> in_progress -> ready_for_testing -> uat_accepted -> done`

Defaults for owner bootstrap in triage:

- Sports -> Harsh
- Strategy/ML -> Ikenna
- Infrastructure/deployment -> Femi
- PM/specification/baseline -> Ikenna
- Production hardening/finish-line -> Harsh

Owner defaults are initialization only and can be overridden per item.

---

## Quadrant 1: Urgent + Important (Do First)

**Priority:** P0
**Timeline:** Weeks 1-4
**Total Effort:** 328 hours

These items block production deployment. Cannot go live without resolving.

### Security (Critical Risk)

| ID     | Work Item                                              | Service                     | Effort | Owner              | Status      |
| ------ | ------------------------------------------------------ | --------------------------- | ------ | ------------------ | ----------- |
| SEC-05 | Remove service account key JSON from git history       | ALL (12/12)                 | 16h    | DevOps Lead        | NOT_STARTED |
| SEC-06 | Implement client credential isolation (per-client SAs) | execution-service, strategy | 48h    | Security Engineer  | PLANNED     |
| COD-20 | Replace hardcoded `test-project` project ID            | ALL (12/12)                 | 24h    | All service owners | NOT_STARTED |

**Total:** 88 hours

---

### Workflows (Operational Risk)

| ID     | Work Item                                           | Service                           | Effort               | Owner           | Status  |
| ------ | --------------------------------------------------- | --------------------------------- | -------------------- | --------------- | ------- |
| WRK-03 | Implement batch position reconciliation (EOD)       | execution-service, strategy       | 40h                  | Trading Systems | PLANNED |
| WRK-04 | Implement live position reconciliation (continuous) | execution-service, reconciliation | 64h                  | Trading Systems | PLANNED |
| WRK-01 | Document disaster recovery procedures               | ALL                               | 40h                  | DevOps Lead     | PLANNED |
| WRK-02 | Implement automatic failover for critical services  | execution-service, strategy       | (included in WRK-01) | DevOps Lead     | PLANNED |
| WRK-06 | Implement rollback procedures                       | ALL                               | 24h                  | DevOps Lead     | PLANNED |

**Total:** 168 hours

---

### Architecture (System Stability)

| ID            | Work Item                                            | Service           | Effort | Owner             | Status  |
| ------------- | ---------------------------------------------------- | ----------------- | ------ | ----------------- | ------- |
| BATCH-03      | Implement data catalogue                             | ALL (pipeline)    | 24h    | Data Engineer     | PLANNED |
| BATCH-04      | Verify pipeline dependency chain + DATA_READY events | ALL (pipeline)    | 16h    | Data Engineer     | PLANNED |
| BATCH-04-LIVE | Extend DATA_READY to live mode (in-process EventBus) | All live services | 32h    | Platform Engineer | PLANNED |

**Total:** 72 hours

---

## Quadrant 2: Important but Not Urgent (Schedule)

**Priority:** P1
**Timeline:** Weeks 5-10
**Total Effort:** 500 hours

These items should be completed before production but don't block initial deployment. Schedule deliberately.

### Observability (Operational Visibility)

| ID     | Work Item                                    | Service                         | Effort | Owner           | Status      |
| ------ | -------------------------------------------- | ------------------------------- | ------ | --------------- | ----------- |
| OBS-05 | Add log_event() calls to source code         | market-tick-data-service        | 8h     | MTHD Owner      | PARTIAL     |
| OBS-07 | Add log_event() calls to source code         | features-delta-one              | 8h     | Features Owner  | PARTIAL     |
| OBS-08 | Add log_event() calls to source code         | ml-inference                    | 8h     | ML Owner        | PARTIAL     |
| COD-08 | Replace print() with logger                  | execution-service (210+ prints) | 10h    | Execution Owner | NOT_STARTED |
| COD-08 | Replace print() with logger                  | market-tick-data-service, MDPS  | 6h     | Service owners  | NOT_STARTED |
| OBS-14 | Implement alerting system (Slack, PagerDuty) | alert-manager                   | 40h    | DevOps Lead     | PLANNED     |
| OBS-15 | Implement monitoring UI (Grafana dashboards) | Grafana                         | 60h    | DevOps Lead     | PLANNED     |

**Total:** 140 hours

---

### Coding Standards (Code Quality)

| ID     | Work Item                          | Service                               | Effort | Owner              | Status  |
| ------ | ---------------------------------- | ------------------------------------- | ------ | ------------------ | ------- |
| COD-24 | Remove try-except import fallbacks | ALL (6+ services)                     | 12h    | All service owners | FAILING |
| COD-09 | Move imports to module level       | ml-training, MDPS, features-delta-one | 8h     | Service owners     | FAILING |

**Total:** 20 hours

---

### Infrastructure (Developer Experience)

| ID     | Work Item        | Service                      | Effort | Owner          | Status  |
| ------ | ---------------- | ---------------------------- | ------ | -------------- | ------- |
| INF-03 | Add .env.example | features-delta-one, strategy | 4h     | Service owners | FAILING |

**Total:** 4 hours

---

### Data (Schema Governance)

| ID     | Work Item                                | Service           | Effort               | Owner             | Status  |
| ------ | ---------------------------------------- | ----------------- | -------------------- | ----------------- | ------- |
| DAT-19 | Implement normalized publish interface   | ALL (10 pipeline) | 40h                  | Platform Engineer | PLANNED |
| DAT-20 | Implement normalized subscribe interface | ALL (10 pipeline) | (included in DAT-19) | Platform Engineer | PLANNED |

**Total:** 40 hours

---

### Live Modes (Real-Time Trading)

| ID      | Work Item                                        | Service                  | Effort | Owner          | Status  |
| ------- | ------------------------------------------------ | ------------------------ | ------ | -------------- | ------- |
| LIVE-01 | Implement live mode for market-tick-data-service | market-tick-data-service | 48h    | MTHD Owner     | PARTIAL |
| LIVE-02 | Implement live mode for market-data-processing   | market-data-processing   | 40h    | MDPS Owner     | PLANNED |
| LIVE-03 | Implement live mode for features-delta-one       | features-delta-one       | 48h    | Features Owner | PLANNED |
| LIVE-04 | Implement live mode for features-volatility      | features-volatility      | 40h    | Features Owner | PLANNED |
| LIVE-05 | Implement live mode for features-onchain         | features-onchain         | 40h    | Features Owner | PLANNED |
| LIVE-06 | Implement live mode for ml-inference             | ml-inference             | 32h    | ML Owner       | PLANNED |
| LIVE-07 | Implement live mode for strategy-service         | strategy-service         | 48h    | Strategy Owner | PLANNED |

**Total:** 296 hours

---

## Quadrant 3: Urgent but Not Important (Delegate/Quick Wins)

**Priority:** P2
**Timeline:** Weeks 8-14 (can parallelize with Quadrant 2)
**Total Effort:** 292 hours

These items provide quick wins or address tech debt. Can delegate to junior engineers or tackle during slow periods.

### Technical Debt

| ID     | Work Item                                                     | Service                                        | Effort | Owner          | Status  |
| ------ | ------------------------------------------------------------- | ---------------------------------------------- | ------ | -------------- | ------- |
| COD-25 | Split large files (instruments: 5600 lines, MDPS: 1500 lines) | instruments, MDPS, features-delta-one          | 40h    | Service owners | FAILING |
| COD-19 | Consolidate wasteful documentation files                      | features-delta-one (14 files), MDPS (10 files) | 8h     | Service owners | FAILING |
| COD-21 | Add regression tests for known bugs                           | ALL                                            | 16h    | QA Engineer    | PARTIAL |

**Total:** 64 hours

---

### Architecture (Maintainability)

| ID     | Work Item                             | Service                                          | Effort | Owner             | Status  |
| ------ | ------------------------------------- | ------------------------------------------------ | ------ | ----------------- | ------- |
| ARC-11 | Implement batch-live symmetry pattern | 5 services (MTHD, features, inference, strategy) | 60h    | Platform Engineer | PLANNED |

**Total:** 60 hours

---

### Operations (Performance & Cost)

| ID     | Work Item                                       | Service           | Effort | Owner                | Status  |
| ------ | ----------------------------------------------- | ----------------- | ------ | -------------------- | ------- |
| ANL-05 | Performance benchmarking (establish SLOs)       | All live services | 40h    | Performance Engineer | PLANNED |
| INF-07 | Multi-region deployment                         | Critical services | 48h    | DevOps Lead          | PLANNED |
| ANL-06 | Cost optimization (GCS lifecycle, right-sizing) | ALL               | 32h    | FinOps               | PLANNED |

**Total:** 120 hours

---

### Compliance (Audit Trail)

| ID     | Work Item                        | Service             | Effort | Owner               | Status  |
| ------ | -------------------------------- | ------------------- | ------ | ------------------- | ------- |
| WRK-05 | Implement compliance audit trail | execution, strategy | 24h    | Compliance Engineer | PLANNED |

**Total:** 24 hours

---

### Testing (Quality Assurance)

| ID      | Work Item                            | Service           | Effort | Owner       | Status  |
| ------- | ------------------------------------ | ----------------- | ------ | ----------- | ------- |
| TEST-01 | Add integration tests for live modes | All live services | 24h    | QA Engineer | PLANNED |

**Total:** 24 hours

---

## Quadrant 4: Neither Urgent nor Important (Eliminate/Defer)

**Priority:** P3
**Timeline:** Post-production (defer indefinitely)
**Total Effort:** 24 hours

These items have low ROI. Consider eliminating or deferring to post-launch.

### Code Quality (Nice-to-Have)

| ID     | Work Item                                          | Service | Effort | Owner            | Status  |
| ------ | -------------------------------------------------- | ------- | ------ | ---------------- | ------- |
| COD-23 | Add type hints to public APIs                      | ALL     | 24h    | Junior Engineers | PARTIAL |
| COD-22 | Remove TODO/FIXME comments (move to GitHub issues) | ALL     | 8h     | Junior Engineers | FAILING |

**Total:** 32 hours

---

### Analysis (Future Enhancements)

| ID     | Work Item                                      | Service               | Effort | Owner         | Status  |
| ------ | ---------------------------------------------- | --------------------- | ------ | ------------- | ------- |
| ANL-07 | Implement live performance tracking dashboard  | analytics-service     | 40h    | Analyst       | PLANNED |
| DOM-05 | Expand asset class coverage (futures, options) | instruments, features | 80h    | Domain Expert | PLANNED |

**Total:** 120 hours (defer to Phase 2 roadmap)

---

## Summary by Quadrant

| Quadrant                    | Priority | Total Effort    | Timeline    | Risk if Skipped                                        |
| --------------------------- | -------- | --------------- | ----------- | ------------------------------------------------------ |
| **1: Urgent + Important**   | P0       | 328 hours       | Weeks 1-4   | Cannot go live (security breach, operational failure)  |
| **2: Important Not Urgent** | P1       | 500 hours       | Weeks 5-10  | Risky production (poor observability, no live trading) |
| **3: Urgent Not Important** | P2       | 292 hours       | Weeks 8-14  | Technical debt accumulates, performance issues         |
| **4: Neither**              | P3       | 152 hours       | Post-launch | Minimal risk (nice-to-have improvements)               |
| **Total**                   |          | **1,272 hours** | 14 weeks    |                                                        |

---

## Recommended Execution Order

### Phase 1 (Weeks 1-4): Quadrant 1 Only

**Focus:** P0 blockers. Must complete before any production deployment.

**Critical Path:**

1. SEC-05: Remove credential files (Week 1)
2. COD-20: Remove hardcoded project ID (Week 1-2)
3. WRK-03: Position reconciliation batch (Week 2-3)
4. BATCH-03/04: Data catalogue and dependency chain (Week 3-4)
5. WRK-01/06: Disaster recovery and rollback (Week 4)

**Gate:** Cannot proceed to Phase 2 until all Quadrant 1 items PASS.

---

### Phase 2 (Weeks 5-10): Quadrant 2

**Focus:** P1 high-priority items. Prepare for live trading.

**Parallel Workstreams:**

- **Observability Team:** OBS-05/07/08, COD-08, OBS-14/15
- **Platform Team:** DAT-19/20, LIVE modes
- **Testing Team:** Integration tests, E2E tests

**Gate:** Cannot go live until all Quadrant 2 items PASS.

---

### Phase 3 (Weeks 8-14): Quadrant 3 (Parallel with Phase 2)

**Focus:** Tech debt and quick wins. Can parallelize with Phase 2.

**Junior Engineers / Intern Projects:**

- COD-25: Split large files
- COD-19: Consolidate docs
- COD-21: Regression tests

**Senior Engineers (when not blocked):**

- ARC-11: Batch-live symmetry
- ANL-05/06: Performance and cost optimization

**Gate:** ≥50% of Quadrant 3 items completed before launch.

---

### Phase 4 (Post-Launch): Quadrant 4

**Focus:** Low-priority enhancements. Defer indefinitely.

**Revisit Quarterly:** Re-assess if these items become more important based on user feedback.

---

## Risk-Based Prioritization

If resources are constrained, prioritize by risk:

### Highest Risk (Must Do)

- SEC-05 (credential leak)
- COD-20 (hardcoded project ID)
- WRK-03/04 (position reconciliation)
- SEC-06 (client credential isolation)

### High Risk (Should Do)

- WRK-01/02/06 (disaster recovery, rollback)
- BATCH-03/04 (data catalogue, dependency chain)
- OBS-05/07/08 (event logging)
- OBS-14 (alerting)

### Medium Risk (Nice to Do)

- LIVE modes (can launch with batch-only initially)
- OBS-15 (monitoring UI - can use Cloud Console initially)
- DAT-19/20 (normalized pub/sub - can refactor later)

### Low Risk (Defer)

- All Quadrant 3 and 4 items

---

## Resource Allocation

### Minimum Viable Team (1.5 FTE)

- **1 Senior Full-Stack Engineer:** Quadrant 1 + 2 (critical path)
- **0.5 DevOps Engineer:** Infrastructure (SEC-05, WRK-01/06, INF-07)

**Timeline:** 20 weeks to 90% live readiness

---

### Recommended Team (3 FTE)

- **1 Senior Full-Stack Engineer:** Quadrant 1 + Quadrant 2 Platform work
- **1 Full-Stack Engineer:** Quadrant 2 Live modes
- **0.5 DevOps Engineer:** Infrastructure (SEC-05, WRK-01/06, INF-07, OBS-14/15)
- **0.5 Junior Engineer:** Quadrant 3 (tech debt, regression tests)

**Timeline:** 14 weeks to 90% live readiness

---

### Aggressive Team (5 FTE)

- **2 Senior Full-Stack Engineers:** Quadrant 1 + 2 (parallel workstreams)
- **1 Full-Stack Engineer:** Quadrant 2 Live modes
- **1 DevOps Engineer:** Infrastructure + Observability
- **1 Junior Engineer:** Quadrant 3 + testing

**Timeline:** 10 weeks to 90% live readiness

---

## Dependencies Between Quadrants

Some Quadrant 2 items depend on Quadrant 1 completion:

- **DAT-19/20** depends on **BATCH-03** (data catalogue)
- **LIVE modes** depend on **OBS-05/07/08** (event logging)
- **WRK-04** (live reconciliation) depends on **WRK-03** (batch reconciliation)
- **SEC-06** (client isolation) depends on **SEC-05** (credential cleanup)

**Critical Path:** Quadrant 1 → Observability (OBS-05/07/08) → Live modes → Live reconciliation

---

## Monthly Check-ins

### Month 1 (Weeks 1-4): Quadrant 1 Review

**Goals:**

- [ ] All Quadrant 1 items completed
- [ ] Re-run audit: batch readiness ≥60%

**Decisions:**

- Proceed to Quadrant 2?
- Adjust timeline based on actual velocity?

---

### Month 2 (Weeks 5-8): Quadrant 2 Progress Check

**Goals:**

- [ ] ≥50% of Quadrant 2 items completed
- [ ] At least 3 services support live mode

**Decisions:**

- Are we on track for Week 10 completion?
- Do we need more engineers?

---

### Month 3 (Weeks 9-12): Quadrant 2 Completion + Quadrant 3 Start

**Goals:**

- [ ] All Quadrant 2 items completed
- [ ] Re-run audit: live readiness ≥85%
- [ ] ≥30% of Quadrant 3 items completed

**Decisions:**

- Ready for first client go-live?
- Defer any Quadrant 3 items to post-launch?

---

### Month 4 (Weeks 13-14+): Launch Readiness

**Goals:**

- [ ] Re-run audit: live readiness ≥90%
- [ ] Disaster recovery drill successful
- [ ] First client onboarded to paper trading

**Decisions:**

- Go/No-Go decision for live trading
- Which Quadrant 4 items to revisit post-launch?

---

## Blockers and Escalation

### Blocker Criteria

A work item is blocked if:

- Waiting on another team >3 days
- Waiting on external vendor (e.g., exchange API access)
- Requires GCP permissions not yet granted
- Requires hardware/infrastructure not yet provisioned

### Escalation Path

1. **Engineer → Service Owner** (same day)
2. **Service Owner → Tech Lead** (within 1 day)
3. **Tech Lead → Engineering Manager** (within 2 days)
4. **Engineering Manager → CTO** (if still blocked after 3 days)

---

## Success Metrics

### Quadrant 1 Success

- [ ] Zero P0 items remaining
- [ ] Batch readiness ≥60%
- [ ] Zero credential files in git history
- [ ] Zero hardcoded project IDs

### Quadrant 2 Success

- [ ] Zero P1 items remaining
- [ ] Live readiness ≥85%
- [ ] All 7 services support live mode
- [ ] Alerting and monitoring operational

### Quadrant 3 Success

- [ ] ≥50% of P2 items resolved
- [ ] Technical debt reduced (large files split, docs consolidated)
- [ ] Performance SLOs met (<200ms latency P95)

### Overall Success (90% Live Ready)

- [ ] All Quadrant 1 items PASS
- [ ] All Quadrant 2 items PASS
- [ ] ≥50% Quadrant 3 items PASS
- [ ] Live readiness ≥90% on audit
- [ ] First client paper trading successfully

---

## Owner: Engineering Lead

## Last Review: 2026-02-11

## Next Review: 2026-03-11 (monthly)
