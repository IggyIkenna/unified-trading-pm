# Full Quickmerge + Act Staging Rollout — All Tiers (Excluding UI)

**Created:** 2026-03-17 **Type:** infra | **Epic:** epic-infra **Scope:** Run full quickmerge (QG + act, no bypasses)
across all tiers L0–L12, excluding UI repos. Push to staging. Parallelize same-tier repos via background agents.

---

## Execution Rules

- **Full quickmerge:** NO `--quick`, NO `--agent` — act runs locally for every repo
- **Branch:** `live-defi-rollout` → PR to `staging` (branch protection requires PR)
- **Parallel:** Same-tier repos run in parallel via `mcp_task` background agents
- **Order:** Complete tier N before starting tier N+1 (dependency order)
- **Status:** Update this plan with status/summary for each repo as completed

---

## Tier 0 — unified-trading-pm

| Repo               | Status     | Summary |
| ------------------ | ---------- | ------- |
| unified-trading-pm | ⏳ PENDING | —       |

---

## Tier 1 — unified-trading-codex

| Repo                  | Status     | Summary |
| --------------------- | ---------- | ------- |
| unified-trading-codex | ⏳ PENDING | —       |

---

## Tier 2 — T0 Foundation

| Repo                     | Status     | Summary                                                                       |
| ------------------------ | ---------- | ----------------------------------------------------------------------------- |
| unified-api-contracts    | ✅ DONE    | PR #40 to staging; full QG+act passed                                         |
| unified-cloud-interface  | ⏳ BLOCKED | 2 test failures (ENVIRONMENT=development vs prod bucket names)                |
| unified-events-interface | ✅ DONE    | PR #26 to staging; full QG+act passed; test fix for STANDARD_LIFECYCLE_EVENTS |

---

## Tier 3 — T1 Libraries

| Repo                             | Status     | Summary                                                                                          |
| -------------------------------- | ---------- | ------------------------------------------------------------------------------------------------ |
| unified-config-interface         | ❌ BLOCKED | Codex: backward-compat re-export in venue_config.py — remove per no-backward-compat-shims        |
| unified-internal-contracts       | ✅ DONE    | PR #21 to staging; full QG+act passed; added UCI integration test                                |
| unified-reference-data-interface | ✅ DONE    | PR #9 to staging; full QG+act passed                                                             |
| unified-trading-library          | ❌ BLOCKED | Codex: function size (simulate_price_movement 61L, check_and_emit 92L); test_domain_clients 954L |

---

## Tier 4 — T2 Core Libraries

| Repo                               | Status  | Summary                               |
| ---------------------------------- | ------- | ------------------------------------- |
| matching-engine-library            | ✅ DONE | PR #16 to staging; full QG+act passed |
| execution-algo-library             | ✅ DONE | PR #20 to staging; full QG+act passed |
| unified-feature-calculator-library | ✅ DONE | PR #5 to staging; full QG+act passed  |

---

## Tier 5 — T3 Interfaces

| Repo                               | Status     | Summary                                                                |
| ---------------------------------- | ---------- | ---------------------------------------------------------------------- |
| unified-domain-client              | ✅ DONE    | PR #11 to staging; full QG+act passed                                  |
| unified-market-interface           | ❌ BLOCKED | Codex: empty fallback, deep UAC import, backward-compat, function size |
| unified-ml-interface               | ✅ DONE    | PR #4 to staging; full QG+act passed                                   |
| unified-position-interface         | ✅ DONE    | PR #4 to staging; full QG+act passed                                   |
| unified-trade-execution-interface  | ✅ DONE    | PR #4 to staging; full QG+act passed                                   |
| unified-features-interface         | ⏸️ SKIP    | Not in workspace                                                       |
| unified-sports-reference-interface | ⏸️ SKIP    | Not in workspace                                                       |

---

## Tier 6 — DeFi/Sports Execution

| Repo                                  | Status     | Summary                     |
| ------------------------------------- | ---------- | --------------------------- |
| unified-defi-execution-interface      | ⏳ PENDING | —                           |
| unified-sports-execution-interface    | ⏳ PENDING | —                           |
| unified-feature-orchestration-library | ⏳ PENDING | — (may not be in workspace) |

---

## Tier 7 — Foundational Service

| Repo                | Status     | Summary |
| ------------------- | ---------- | ------- |
| instruments-service | ⏳ PENDING | —       |

---

## Tier 8 — Services (17 repos)

| Repo                              | Status     | Summary |
| --------------------------------- | ---------- | ------- |
| alerting-service                  | ⏳ PENDING | —       |
| execution-service                 | ⏳ PENDING | —       |
| features-calendar-service         | ⏳ PENDING | —       |
| features-cross-instrument-service | ⏳ PENDING | —       |
| features-delta-one-service        | ⏳ PENDING | —       |
| features-multi-timeframe-service  | ⏳ PENDING | —       |
| features-onchain-service          | ⏳ PENDING | —       |
| features-sports-service           | ⏳ PENDING | —       |
| features-volatility-service       | ⏳ PENDING | —       |
| market-data-processing-service    | ⏳ PENDING | —       |
| market-tick-data-service          | ⏳ PENDING | —       |
| ml-inference-service              | ⏳ PENDING | —       |
| ml-training-service               | ⏳ PENDING | —       |
| pnl-attribution-service           | ⏳ PENDING | —       |
| strategy-service                  | ⏳ PENDING | —       |
| features-commodity-service        | ⏳ PENDING | —       |
| trading-agent-service             | ⏳ PENDING | —       |

---

## Tier 9 — APIs

| Repo                             | Status     | Summary                     |
| -------------------------------- | ---------- | --------------------------- |
| batch-audit-api                  | ⏳ PENDING | —                           |
| client-reporting-api             | ⏳ PENDING | —                           |
| execution-results-api            | ⏳ PENDING | —                           |
| market-data-api                  | ⏳ PENDING | —                           |
| ml-inference-api                 | ⏳ PENDING | —                           |
| ml-training-api                  | ⏳ PENDING | —                           |
| position-balance-monitor-service | ⏳ PENDING | —                           |
| risk-and-exposure-service        | ⏳ PENDING | —                           |
| trading-analytics-api            | ⏳ PENDING | —                           |
| config-api                       | ⏳ PENDING | — (may not be in workspace) |

---

## Tier 10 — Deployment + UI Kit

| Repo                              | Status     | Summary |
| --------------------------------- | ---------- | ------- |
| batch-live-reconciliation-service | ⏳ PENDING | —       |
| deployment-api                    | ⏳ PENDING | —       |
| deployment-service                | ⏳ PENDING | —       |
| unified-trading-ui-kit            | ⏳ PENDING | —       |

---

## Tier 11 — UI (SKIPPED)

All UI repos excluded per user request.

---

## Tier 12 — IaC + Post-Deploy

| Repo                     | Status     | Summary                     |
| ------------------------ | ---------- | --------------------------- |
| elysium-defi-system      | ⏳ PENDING | — (may not be in workspace) |
| ibkr-gateway-infra       | ⏳ PENDING | —                           |
| system-integration-tests | ⏳ PENDING | —                           |

---

## Agent Context (pass to each sub-agent)

```
WORKSPACE_ROOT: /home/hk/unified-trading-system-repos
Branch: live-defi-rollout
Target: staging (via PR — branch protection)

Task: Run full quickmerge for <REPO>:
  cd $WORKSPACE_ROOT/<REPO>
  git checkout live-defi-rollout && git pull origin live-defi-rollout
  # If nothing to commit: add trivial change (e.g. trailing newline in README)
  bash scripts/quickmerge.sh "chore: full QG+act for staging"
  # NO --quick, NO --agent — act must run

Rules: uv not pip; quickmerge not git push; follow unified-trading-pm cursor rules.
```

---

## Progress Log

- 2026-03-17: Plan created. T2: UAC ✅, UEI ✅, UIC ✅. UCI blocked (ENV test). T0, T1 done in prior session.
- 2026-03-17: T3 parallel agents: UCI ❌ (backward-compat), URI ✅ PR #9, UTL ❌ (function/test size limits).
- 2026-03-17: T4 parallel agents: MEL ✅ PR #16, EAL ✅ PR #20, UFCL ✅ PR #5.
- 2026-03-17: T5 parallel agents: UDC ✅ PR #11, UMI ❌ (codex), UMI-ml ✅ PR #4, UPI ✅ PR #4, UTEI ✅ PR #4.
