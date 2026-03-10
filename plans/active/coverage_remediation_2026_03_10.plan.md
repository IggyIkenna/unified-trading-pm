---
name: Coverage Remediation Plan — 2026-03-10
overview: |
  Raise test coverage to meet floor across all failing repos.
  Formula: MIN_COVERAGE = max(floor, actual_coverage - 1)
  Floors: service/api-service/infrastructure/ui = 70%; library = 80%
  Source: python3 unified-trading-pm/scripts/repo-management/coverage-audit.py
  14 repos currently below floor (audit 2026-03-10).

todos:
  - id: close-gap-execution-results-api
    content:
      "execution-results-api: DONE 2026-03-10. 66%->79% (MIN_COVERAGE=78). Fixed syntax errors and Pydantic mock data in
      agent-written tests."
    status: done

  - id: close-gap-features-cross-instrument
    content:
      "features-cross-instrument-service: DONE 2026-03-10. 64%->92% (MIN_COVERAGE=90). Was stale; added CLI+sentiment
      tests."
    status: done

  - id: close-gap-features-multi-timeframe
    content:
      "features-multi-timeframe-service: DONE 2026-03-10. 55%->86% (MIN_COVERAGE=85). Added orchestrator and calculator
      tests."
    status: done

  - id: close-gap-instruments-service
    content: "instruments-service: actual=52%, floor=70%, gap=-18%. Agent working in session — pending verification."
    status: pending

  - id: close-gap-trading-agent
    content: "trading-agent-service: DONE 2026-03-10. 50%->80% (MIN_COVERAGE=79). Added loop tests."
    status: done

  - id: close-gap-pnl-attribution
    content:
      "pnl-attribution-service: DONE 2026-03-10. 46%->75% (MIN_COVERAGE=74). Added compute handler and engine tests."
    status: done

  - id: close-gap-ml-training
    content: "ml-training-service: DONE 2026-03-10. Was already 77% (stale). fail_under recalibrated to 75."
    status: done

  - id: close-gap-features-onchain
    content: "features-onchain-service: DONE 2026-03-10. 39%->70% (MIN_COVERAGE=70). Floor reached."
    status: done

  - id: close-gap-market-data-processing
    content: "market-data-processing-service: DONE 2026-03-10. 38%->74% (MIN_COVERAGE=72). Floor reached."
    status: done

  - id: close-gap-execution-service
    content:
      "execution-service: PARTIAL 2026-03-10. 26%->32% (MIN_COVERAGE=31). 32K LOC — needs multi-session campaign to
      reach 70%."
    status: pending

  - id: close-gap-market-tick-data
    content:
      "market-tick-data-service: PARTIAL 2026-03-10. 16%->37% (MIN_COVERAGE=36). 9K LOC — needs continued test campaign
      to reach 70%."
    status: pending

  - id: close-gap-features-commodity
    content:
      "features-commodity-service: DONE 2026-03-10. 14%->99% (MIN_COVERAGE=97). Fixed missing openpyxl dep + test bug."
    status: done

  - id: close-gap-unified-trading-library
    content: "unified-trading-library: DONE 2026-03-10. 78%->81% (MIN_COVERAGE=80). Added 78 targeted unit tests."
    status: done

  - id: close-gap-unified-market-interface
    content:
      "unified-market-interface: actual=61%, floor=80% (library), gap=-19%. Agent working in session — pending
      verification."
    status: pending

  - id: recalibrate-after-fix
    content:
      "Run rollout --recalibrate once audit exits 0. Blocked by 2 partial repos (execution-service,
      market-tick-data-service) and 2 pending agent repos."
    status: pending

  - id: verify-audit-clean
    content:
      "Verify: python3 unified-trading-pm/scripts/repo-management/coverage-audit.py exits 0 (no FAIL repos). Currently 4
      FAILs remain."
    status: pending

isProject: true
---

# Coverage Remediation — 2026-03-10

**SSOT:** `unified-trading-pm/cursor-rules/testing/test-coverage-targets.mdc` **Audit tool:**
`python3 unified-trading-pm/scripts/repo-management/coverage-audit.py` **Recalibrate:**
`python3 unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py --recalibrate`

---

## Formula

```
MIN_COVERAGE = max(floor, actual_coverage - 1)
```

| Repo type                                | Floor |
| ---------------------------------------- | ----- |
| library                                  | 80%   |
| service, api-service, infrastructure, ui | 70%   |

Approved exceptions (exempt from floor): `ibkr-gateway-infra` (51%), `system-integration-tests` (0%),
`unified-trading-pm` (self-managed), `unified-trading-codex` (docs-only).

---

## Audit Snapshot — 2026-03-10

Run: `python3 unified-trading-pm/scripts/repo-management/coverage-audit.py --no-color`

### [A] FAIL — 14 repos below floor

Ordered easiest→hardest (by gap size):

| Repo                              | Type        | Actual | Floor | Gap  | Target MIN_COVERAGE |
| --------------------------------- | ----------- | ------ | ----- | ---- | ------------------- |
| execution-results-api             | api-service | 66%    | 70%   | -4%  | 69                  |
| features-cross-instrument-service | service     | 64%    | 70%   | -6%  | 69                  |
| features-multi-timeframe-service  | service     | 55%    | 70%   | -15% | 69                  |
| instruments-service               | service     | 52%    | 70%   | -18% | 69                  |
| trading-agent-service             | service     | 50%    | 70%   | -20% | 69                  |
| pnl-attribution-service           | service     | 46%    | 70%   | -24% | 69                  |
| ml-training-service               | service     | 39%    | 70%   | -31% | 69                  |
| features-onchain-service          | service     | 39%    | 70%   | -31% | 69                  |
| market-data-processing-service    | service     | 38%    | 70%   | -32% | 69                  |
| execution-service                 | service     | 26%    | 70%   | -44% | 69                  |
| market-tick-data-service          | service     | 16%    | 70%   | -54% | 69                  |
| features-commodity-service        | service     | 14%    | 70%   | -56% | 69                  |
| unified-trading-library           | library     | 78%    | 80%   | -2%  | 79                  |
| unified-market-interface          | library     | 61%    | 80%   | -19% | 79                  |

### [B] WARN — UI repos missing coverage reports (13 repos)

UI repos now have `@vitest/coverage-v8` installed and test files added (2026-03-10). These will be resolved after
`npm install` + `npm test -- --coverage --provider=v8` runs in each repo.

| Repo                    | Note                                                   |
| ----------------------- | ------------------------------------------------------ |
| client-reporting-ui     | @vitest/coverage-v8 added; test file added             |
| deployment-ui           | @vitest/coverage-v8 added; test file added             |
| execution-analytics-ui  | @vitest/coverage-v8 added; test file added             |
| live-health-monitor-ui  | @vitest/coverage-v8 added; test file added             |
| logs-dashboard-ui       | @vitest/coverage-v8 added; test file added             |
| ml-training-ui          | @vitest/coverage-v8 added; test file added             |
| onboarding-ui           | @vitest/coverage-v8 added; test file added             |
| settlement-ui           | @vitest/coverage-v8 added; test file added             |
| strategy-ui             | @vitest/coverage-v8 added; test file added             |
| trading-analytics-ui    | @vitest/coverage-v8 added; test file added             |
| unified-trading-ui-auth | @vitest/coverage-v8 added                              |
| batch-audit-ui          | playwright-only — no unit tests (expected)             |
| unified-trading-codex   | infrastructure with pyproject.toml but no coverage.xml |

### [C] INFO — 1 stale threshold

| Repo                              | Note                                         |
| --------------------------------- | -------------------------------------------- |
| unified-trade-execution-interface | MIN_COVERAGE=88 but expected 87 (actual=88%) |

---

## Execution Strategy

### Quick wins first (gap ≤ 6%)

1. **execution-results-api** (-4%): Likely missing coverage on a few API route handlers. Run
   `pytest --cov --cov-report=term-missing` to find uncovered lines, add targeted tests.
2. **features-cross-instrument-service** (-6%): Similar small gap — find uncovered branches.

### Mid-range (gap 15–25%)

3. **features-multi-timeframe-service**, **instruments-service**, **trading-agent-service**,
   **pnl-attribution-service**: Focus on core domain logic (pure functions, data transforms). Use `# pragma: no cover`
   only for CLI entrypoints.

### High effort (gap > 30%)

- **execution-service**, **market-tick-data-service**, **features-commodity-service**: These need structured test
  campaigns. Focus on the processing pipeline core, not the I/O adapters (mock those).
- **unified-market-interface**: Library floor is 80% — focus on venue factory, adapter contracts.

### Pattern for each service

```bash
cd <repo>
pytest --cov=<source_dir> --cov-report=term-missing -q 2>&1 | grep -E "(TOTAL|FAIL|%)" | tail -5
# Find uncovered lines:
pytest --cov=<source_dir> --cov-report=term-missing -q 2>&1 | grep -v "100%" | grep "%"
```

---

## Completion Criteria

- `python3 unified-trading-pm/scripts/repo-management/coverage-audit.py` exits 0
- [A] FAIL count = 0
- `rollout-quality-gates-unified.py --recalibrate` updates MIN_COVERAGE in all repos
