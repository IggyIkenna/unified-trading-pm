---
title: "pyproject.toml workspace-wide audit — ruff line-length drift + coverage floor gaps"
created: 2026-05-15
author: slot-8
source:
  - all repos' pyproject.toml + pyrightconfig.json
locked_by: live-defi-rollout
---

## What I found

Scanned all 24 repos with pyproject.toml (12 repos have no pyproject.toml — features sub-services + UI repos).

### Finding 1: ruff line-length=100 in 15 repos (should be 120)

CLAUDE.md specifies `ruff format --line-length 120`. E501 enforced. "Never add E501 to global ignore."

15 repos are set to `line-length = 100`:

| Repo                              | Current | Expected |
| --------------------------------- | ------- | -------- |
| alerting-service                  | 100     | 120      |
| batch-live-reconciliation-service | 100     | 120      |
| client-reporting-api              | 100     | 120      |
| deployment-api                    | 100     | 120      |
| deployment-service                | 100     | 120      |
| ibkr-gateway-infra                | 100     | 120      |
| market-data-processing-service    | 100     | 120      |
| ml-inference-service              | 100     | 120      |
| ml-training-service               | 100     | 120      |
| pnl-attribution-service           | 100     | 120      |
| position-balance-monitor-service  | 100     | 120      |
| risk-and-exposure-service         | 100     | 120      |
| strategy-service                  | 100     | 120      |
| unified-trading-library           | 100     | 120      |
| unified-trading-api               | 100     | 120      |

Repos already at 120: execution-service, features-service, instruments-service, market-tick-data-service,
system-integration-tests, unified-api-contracts, trading-agent-service, ibkr-gateway-infra (100), risk (100).

### Finding 2: coverage fail_under below workspace floor (70) — 3 repos

| Repo                               | fail_under | Notes                                                          |
| ---------------------------------- | ---------- | -------------------------------------------------------------- |
| `features-service`                 | 0          | Explicitly set to 0 — QG MIN_COVERAGE=70 may be the only guard |
| `position-balance-monitor-service` | 58         | Below 70 floor                                                 |
| `unified-trading-library`          | 65         | Below 70 floor; UTL is a library (80% target per CLAUDE.md)    |
| `ml-inference-service`             | 66         | ISS-031 comment says lowered from 74                           |
| `e2e-testing`                      | 0          | Expected for E2E testing repo                                  |
| `ibkr-gateway-infra`               | 51         | CR2 fix aligned with QG MIN_COVERAGE=51 — gateway special case |
| `system-integration-tests`         | 15         | SIT has live-service dependencies, can't be higher in CI       |

Outstanding high coverage repos (above 80): `pnl-attribution-service` (89), `unified-api-contracts` (84).

### Finding 3: 12 repos missing pyproject.toml entirely

Features sub-services (8 repos): `features-calendar-service`, `features-commodity-service`,
`features-cross-instrument-service`, `features-delta-one-service`, `features-multi-timeframe-service`,
`features-onchain-service`, `features-sports-service`, `features-volatility-service`

UI repos (3): `unified-trading-system-ui`, `deployment-ui`, `user-management-ui`

Admin: `fund-administration-service`

Features sub-services likely inherit config from `features-service/` — this needs verification.

### Finding 4: unified-trading-pm uses standard typeCheckingMode (not strict)

`unified-trading-pm/pyrightconfig.json` has `"typeCheckingMode": "standard"` instead of `"strict"`. PM is not a Python
package (no importable module) so this is partially expected, but PM scripts should still be type-checked with strict
mode per workspace rules.

## Why it matters

- `line-length=100` vs 120: any line between 101-120 characters that passes ruff locally (using 120) will FAIL in a repo
  configured with 100. Creates inconsistent formatting when contributors switch repos. Also means the QG may be
  auto-fixing lines to different lengths in different repos, creating churn on PRs. **This is the primary source of E501
  violations being silently ignored in these repos.**

- `fail_under` below 70 floor: position-balance-monitor-service (58) and UTL (65) can regress below 70% without failing
  pytest, even though QG MIN_COVERAGE=70 is set. The pyproject `fail_under` is the authoritative gate for `pytest --cov`
  runs; QG MIN_COVERAGE is a secondary check. Gap between them means coverage could actually be at 60% and pytest passes
  while QG warns.

## Recommended decision

**Priority 1 (mechanical fix, P2)**: Update all 15 repos' `line-length = 100` → `line-length = 120` in pyproject.toml.
Then run `ruff format --line-length 120` on each repo to reformat. Each repo needs a passing QG run after reformatting
(risk of cascading `# noqa: E501` changes, but those should be removed not added). Estimated: 15 min per repo via
script; total 4-6 AI-hours.

**Priority 2 (P3)**: Align `fail_under` with QG `MIN_COVERAGE` in repos where they diverge:

- `position-balance-monitor-service`: raise 58 → 70
- `unified-trading-library`: raise 65 → 80 (library target)
- `ml-inference-service`: verify whether 66 is still accurate or can be restored to 70+

**Priority 3 (P3)**: Verify features sub-services inherit config from `features-service/` correctly.

**Owner**: Per-repo teams; mechanical line-length fix can be scripted.

---

## Status

`PARTIALLY RESOLVED — 2026-05-15 (slot-2)`

**Priority 1 DONE** — line-length 100→120 applied to all 14 eligible repos (deployment-api skipped = slot 7):

| Repo | SHA |
|---|---|
| alerting-service | f052e21 |
| batch-live-reconciliation-service | de72ab7 |
| client-reporting-api | 163374e |
| ibkr-gateway-infra | 5f8d354 |
| deployment-service | 560af4d |
| market-data-processing-service | b2b8dd5 |
| ml-inference-service | 0f49311 |
| ml-training-service | 4957ed8 |
| pnl-attribution-service | f99d33d |
| position-balance-monitor-service | 06cba56 |
| risk-and-exposure-service | e148b45 |
| strategy-service | 00af7ed |
| unified-trading-library | 623b0cd |
| unified-trading-api | 6d9ca22 |

Note: deployment-api (15th repo from Finding 1) assigned to slot 7 — skipped per conflict rules.

**Priority 2+3 OPEN** — coverage floor alignment (`position-balance-monitor-service` 58→70, `unified-trading-library` 65→80, `ml-inference-service` verify 66) + features sub-service inheritance verification. Requires per-repo QG runs. Deferred to per-repo owners.
