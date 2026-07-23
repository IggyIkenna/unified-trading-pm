---
doc_type: codex-ssot
title: Quality Gates & Coverage Audit Report
summary:
  Historical 2026-03-04 coverage + quality-gate snapshot across 43 Python repos — audit score 21/100, 13/43 repos ≥70%
  coverage, 0/41 quality gates passing; common failures were G201 logging, ruff-version mismatch, and import errors.
  Point-in-time state, long superseded by later QG hardening.
status: stale
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [alerting-service, client-reporting-api, deployment-api, deployment-service, execution-service, features-service]
scope: [engineer, admin]
tags: [quality-gates, coverage, audit, ssot-audit]
related: [/codex/10-audit/FOUNDATIONAL-REPOS-AUDIT-2026-03-07.md, /codex/10-audit/QUALITY_GATE_BYPASS_AUDIT.md]
created: 2026-03-27
authoritative_for: [2026-03-04 workspace coverage and quality-gate snapshot]
referenced_by: [/codex/10-audit/FOUNDATIONAL-REPOS-AUDIT-2026-03-07.md, /codex/10-audit/QUALITY_GATE_BYPASS_AUDIT.md]
owner:
last_reviewed:
code_refs:
---

# Quality Gates & Coverage Audit Report

**Generated:** 2026-03-04 (UTC) **Source:** Parallel agent run across all Python repos in workspace **Target:** 70%
coverage minimum; quality-gates.sh --unit-only pass

---

## Audit Score Summary

| Metric                            | Value  | Target |
| --------------------------------- | ------ | ------ |
| **Audit Score**                   | 21/100 | 100    |
| Repos with coverage ≥70%          | 13/43  | 43     |
| Quality gates pass                | 0/41   | 41     |
| Coverage measurable (pytest runs) | 22/43  | 43     |

**Score formula:** 40% coverage attainment + 40% QG pass + 20% measurable

---

## Coverage by Repo

### Pass (≥70%)

| Repo                                       | Coverage | Status |
| ------------------------------------------ | -------- | ------ |
| features-service (sports family)           | 100.0%   | ok     |
| unified-api-contracts (internal/)          | 99.8%    | ok     |
| unified-trading-library                    | 97.1%    | ok     |
| unified-ml-interface                       | 93.4%    | ok     |
| position-balance-monitor-service           | 88.6%    | ok     |
| features-service (calendar family)         | 84.3%    | ok     |
| features-service (cross-instrument family) | 81.5%    | ok     |
| execution-service                          | 80.9%    | ok     |
| execution-algo-library                     | 72.1%    | ok     |
| unified-trading-pm                         | 72.5%    | ok     |
| system-integration-tests                   | 70.2%    | ok     |

### Below 70%

| Repo                              | Coverage | Gap    |
| --------------------------------- | -------- | ------ |
| execution-service                 | 62.7%    | -7.3%  |
| unified-cloud-interface           | 54.6%    | -15.4% |
| features-service (onchain family) | 54.0%    | -16.0% |
| unified-domain-client             | 45.0%    | -25.0% |
| pnl-attribution-service           | 37.2%    | -32.8% |
| client-reporting-api              | 32.6%    | -37.4% |
| unified-trading-library           | 26.2%    | -43.8% |
| unified-trading-library           | 0.0%     | -70.0% |

### Error (pytest fails before coverage)

alerting-service, deployment-api, deployment-service, execution-results-api, execution-service, features-service
(delta-one family), features-service (multi-timeframe family), features-service (volatility family),
instruments-service, market-data-processing-service, market-tick-data-service, matching-engine-library,
ml-inference-service, ml-training-service, position-balance-monitor-service, risk-and-exposure-service,
strategy-service, unified-api-contracts, unified-config-interface,
market-tick-data-service/market_tick_data_service/market_interface, instruments-service, execution-service

---

## Quality Gates Status

**All 41 Python repos with quality-gates.sh: FAIL**

Common failure causes:

- **G201:** Logging `.exception(...)` should be used instead of `.error(..., exc_info=True)`
- **Ruff version:** Expected 0.15.0, found 0.15.4 (or downstream mismatch)
- **Basedpyright:** Type errors, import errors
- **Coverage:** Below 70% threshold
- **Tests:** Failing unit tests
- **Import errors:** Missing deps, conftest issues

---

## Next Steps

1. Fix G201 logging rule across repos (ruff auto-fix or manual)
2. Align ruff to 0.15.0 in all pyproject.toml / uv.lock
3. Fix import errors (path deps, workspace venv)
4. Add tests for repos below 70% coverage
5. Re-run: `bash scripts/quality-gates.sh --unit-only --no-fix` per repo

---

## Report History

| Date       | Audit Score | Coverage 70%+ | QG Pass |
| ---------- | ----------- | ------------- | ------- |
| 2026-03-04 | 21          | 13/43         | 0/41    |
