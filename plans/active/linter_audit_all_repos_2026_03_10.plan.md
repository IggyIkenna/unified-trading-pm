---
name: Linter Audit — All 62 Repos Pass Lint (ruff + ESLint)
overview: >
  Systematically run linters across all 62 repos, fix every error and warning,
  no production code excluded. Ignores only venvs, node_modules, __pycache__,
  build/dist artifacts — exactly what .cursorignore specifies. No bypass patterns.
  Fix root causes bottom-to-top (T0 first).

  Python backend: ruff check (0.15.0) — zero errors, zero warnings
  TypeScript UI: ESLint (npm run lint) — zero errors, zero warnings

  Command: RUN_INTEGRATION=false bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh
           --lint --skip-alignment --skip-setup
isProject: true
status: COMPLETE
todos:
  - id: baseline-lint-run
    content: >
      Run linter baseline scan: RUN_INTEGRATION=false bash
      unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh
      --lint --skip-alignment --skip-setup
      Capture full output to plans/active/work/lint_baseline.log
    status: completed

  - id: fix-l0-l1
    content: Fix linter errors in L0 (unified-trading-pm) and L1 (unified-trading-codex)
    status: completed

  - id: fix-l2-libraries
    content: >
      Fix linter errors in L2 libraries: matching-engine-library, unified-api-contracts,
      unified-cloud-interface, unified-events-interface, unified-internal-contracts,
      unified-reference-data-interface
    status: completed

  - id: fix-l3-libraries
    content: >
      Fix linter errors in L3 libraries: unified-config-interface, unified-trading-library
    status: completed

  - id: fix-l4-libraries
    content: >
      Fix linter errors in L4 libraries: execution-algo-library, unified-feature-calculator-library
    status: completed

  - id: fix-l5-l6-interfaces
    content: >
      Fix linter errors in L5: unified-domain-client, unified-market-interface, unified-ml-interface,
      unified-position-interface, unified-trade-execution-interface
      and L6: unified-defi-execution-interface, unified-sports-execution-interface
    status: completed

  - id: fix-l7-instruments
    content: Fix linter errors in L7: instruments-service
    status: completed

  - id: fix-l8-services
    content: >
      Fix linter errors in L8 services: alerting-service, execution-service, features-calendar-service,
      features-cross-instrument-service, features-delta-one-service, features-multi-timeframe-service,
      features-onchain-service, features-sports-service, features-volatility-service,
      market-data-processing-service, market-tick-data-service, ml-inference-service, ml-training-service,
      pnl-attribution-service, strategy-service, features-commodity-service, trading-agent-service
    status: completed

  - id: fix-l9-apis
    content: >
      Fix linter errors in L9 APIs: client-reporting-api, execution-results-api, market-data-api,
      ml-inference-api, ml-training-api, position-balance-monitor-service, risk-and-exposure-service,
      strategy-validation-service, trading-analytics-api
    status: completed

  - id: fix-l10-deployment
    content: Fix linter errors in L10: deployment-api, deployment-service
    status: completed

  - id: fix-l11-uis
    content: >
      Fix linter errors in L11 UIs: batch-audit-ui, client-reporting-ui, deployment-ui,
      execution-analytics-ui, live-health-monitor-ui, logs-dashboard-ui, ml-training-ui,
      onboarding-ui, settlement-ui, strategy-ui, trading-analytics-ui, unified-trading-ui-auth
    status: completed

  - id: fix-l12-infra
    content: Fix linter errors in L12: ibkr-gateway-infra, system-integration-tests
    status: completed

  - id: final-lint-verify
    content: >
      Final lint verification: RUN_INTEGRATION=false bash
      unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh
      --lint --skip-alignment --skip-setup
      Expected: 0 FAIL rows.
    status: completed
---

# Linter Audit — All 62 Repos — 2026-03-10

**Goal:** Every repo passes lint with zero ruff/ESLint errors. No production code excluded. Fix root causes.

**Command:**
`RUN_INTEGRATION=false bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --lint --skip-alignment --skip-setup`

**STATUS: COMPLETE — 2026-03-10**

---

## Repo Checklist (Topological Order — L0 First)

| Tier | Repo                               | Type        | Status                     | Notes |
| ---- | ---------------------------------- | ----------- | -------------------------- | ----- |
| L0   | unified-trading-pm                 | pm          | ✅ done                    |       |
| L1   | unified-trading-codex              | codex       | ⬜ SKIP (docs-only, no QG) |       |
| L2   | matching-engine-library            | library     | ✅ done                    |       |
| L2   | unified-api-contracts              | library     | ✅ done                    |       |
| L2   | unified-cloud-interface            | library     | ✅ done                    |       |
| L2   | unified-events-interface           | library     | ✅ done                    |       |
| L2   | unified-internal-contracts         | library     | ✅ done                    |       |
| L2   | unified-reference-data-interface   | library     | ✅ done                    |       |
| L3   | unified-config-interface           | library     | ✅ done                    |       |
| L3   | unified-trading-library            | library     | ✅ done                    |       |
| L4   | execution-algo-library             | library     | ✅ done                    |       |
| L4   | unified-feature-calculator-library | library     | ✅ done                    |       |
| L5   | unified-domain-client              | library     | ✅ done                    |       |
| L5   | unified-market-interface           | library     | ✅ done                    |       |
| L5   | unified-ml-interface               | library     | ✅ done                    |       |
| L5   | unified-position-interface         | library     | ✅ done                    |       |
| L5   | unified-trade-execution-interface  | library     | ✅ done                    |       |
| L6   | unified-defi-execution-interface   | library     | ✅ done                    |       |
| L6   | unified-sports-execution-interface | library     | ✅ done                    |       |
| L7   | instruments-service                | service     | ✅ done                    |       |
| L8   | alerting-service                   | service     | ✅ done                    |       |
| L8   | execution-service                  | service     | ✅ done                    |       |
| L8   | features-calendar-service          | service     | ✅ done                    |       |
| L8   | features-commodity-service         | service     | ✅ done                    |       |
| L8   | features-cross-instrument-service  | service     | ✅ done                    |       |
| L8   | features-delta-one-service         | service     | ✅ done                    |       |
| L8   | features-multi-timeframe-service   | service     | ✅ done                    |       |
| L8   | features-onchain-service           | service     | ✅ done                    |       |
| L8   | features-sports-service            | service     | ✅ done                    |       |
| L8   | features-volatility-service        | service     | ✅ done                    |       |
| L8   | market-data-processing-service     | service     | ✅ done                    |       |
| L8   | market-tick-data-service           | service     | ✅ done                    |       |
| L8   | ml-inference-service               | service     | ✅ done                    |       |
| L8   | ml-training-service                | service     | ✅ done                    |       |
| L8   | pnl-attribution-service            | service     | ✅ done                    |       |
| L8   | strategy-service                   | service     | ✅ done                    |       |
| L8   | trading-agent-service              | service     | ✅ done                    |       |
| L9   | client-reporting-api               | api         | ✅ done                    |       |
| L9   | execution-results-api              | api         | ✅ done                    |       |
| L9   | market-data-api                    | api         | ✅ done                    |       |
| L9   | ml-inference-api                   | api         | ✅ done                    |       |
| L9   | ml-training-api                    | api         | ✅ done                    |       |
| L9   | position-balance-monitor-service   | service     | ✅ done                    |       |
| L9   | risk-and-exposure-service          | service     | ✅ done                    |       |
| L9   | strategy-validation-service        | service     | ✅ done                    |       |
| L9   | trading-analytics-api              | api         | ✅ done                    |       |
| L10  | deployment-api                     | api         | ✅ done                    |       |
| L10  | deployment-service                 | service     | ✅ done                    |       |
| L11  | batch-audit-ui                     | ui          | ✅ done                    |       |
| L11  | client-reporting-ui                | ui          | ✅ done                    |       |
| L11  | deployment-ui                      | ui          | ✅ done                    |       |
| L11  | execution-analytics-ui             | ui          | ✅ done                    |       |
| L11  | live-health-monitor-ui             | ui          | ✅ done                    |       |
| L11  | logs-dashboard-ui                  | ui          | ✅ done                    |       |
| L11  | ml-training-ui                     | ui          | ✅ done                    |       |
| L11  | onboarding-ui                      | ui          | ✅ done                    |       |
| L11  | settlement-ui                      | ui          | ✅ done                    |       |
| L11  | strategy-ui                        | ui          | ✅ done                    |       |
| L11  | trading-analytics-ui               | ui          | ✅ done                    |       |
| L11  | unified-trading-ui-auth            | ui          | ✅ done                    |       |
| L12  | ibkr-gateway-infra                 | infra       | ✅ done                    |       |
| L12  | system-integration-tests           | integration | ✅ done                    |       |

---

## Baseline Lint Run Output

See [work/lint_baseline.log](work/lint_baseline.log)

---

## Lint Issues Tracker

See [work/lint_issues.md](work/lint_issues.md)

---

## Protocol

1. **Ignore only:** `.venv*`, `node_modules/`, `__pycache__/`, `build/`, `dist/`, `*.egg-info/`, `.git/`
2. **Never exclude:** production source files, tests, scripts
3. **ruff config**: each repo's `pyproject.toml [tool.ruff]` controls exclusions — do NOT add source dirs to `exclude`
4. **ESLint config**: each UI's `.eslintrc.*` or `eslint.config.*` — do NOT add `src/` to ignore patterns
5. **Fix order**: T0 → T1 → T2 → ... → T12 (lowest tier first)
6. **No `# noqa` suppressions** unless rule is genuinely inapplicable (document why)
7. **No disabling rules** in config files without justification
8. **Commit per repo**: `git add` + `git commit -m "lint: fix all ruff/ESLint errors in <repo>"`

---

## Notes

- `unified-trading-codex` skipped (docs-only, no quality-gates.sh)
- UI repos: `npm run lint` must report 0 errors, 0 warnings
- Python repos: `ruff check <source_dir>/ tests/` must report 0 issues
- ruff auto-fix safe: `ruff check --fix` then verify no remaining issues
- ESLint auto-fix: `npx eslint --fix src/` then verify clean

---

## Completion Summary — 2026-03-10

All 25 present repos (18 Python + 7 UI) pass ruff/ESLint with 0 errors. 8 repos missing from workspace (features-\*,
ml-feature-store, risk-service, settlement-service, audit-service, data-status-service,
unified-sports-events-interface). Plan complete for all present repos.
