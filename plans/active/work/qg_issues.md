# QG Issues Log — quality_gates_full_fix_2026_03_10

**Last baseline run:** 2026-03-10 (in progress) **Updated by:** master agent after each fix agent reports

---

## Status Key

- `open` — identified, not yet assigned to agent
- `in_progress` — fix agent running
- `fixed` — agent committed fix
- `verified` — re-ran QG for repo and confirmed passing

---

## Issues (Original 22)

| #   | Repo                               | Issue Type           | Details                                                                                                                      | Agent | Status   |
| --- | ---------------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------- | ----- | -------- |
| 1   | unified-market-interface           | test_fail + coverage | Fixed: wheel reinstall + 57 new DeFi tests → 1994 passed, 0 failed, 84.88%                                                   | —     | verified |
| 2   | unified-trade-execution-interface  | test_fail            | Fixed: uv pip install -e reinstalled editable wheel → 964 passed, 0 failed, 90.32%                                           | —     | verified |
| 3   | unified-trading-library            | coverage             | Manifest stale — actual 81.27%, 1180 passed, 0 failed                                                                        | —     | verified |
| 4   | execution-algo-library             | coverage             | Manifest was stale — actual 96.65%, 201 passed, 0 failed                                                                     | —     | verified |
| 5   | unified-sports-execution-interface | coverage             | Already fixed in prior session — 437 passed, 0 failed, 81.09%                                                                | —     | verified |
| 6   | features-multi-timeframe-service   | test_fail + coverage | RC-C env-leak fixed + 35 new tests (cli/orchestrator) → 370 passed, 0 failed, 97.65%                                         | —     | verified |
| 7   | features-onchain-service           | coverage             | Manifest stale — actual 71.28%, 286 passed, 0 failed                                                                         | —     | verified |
| 8   | features-volatility-service        | coverage             | Manifest stale — actual 73.88%, 423 passed, 0 failed (threshold fail_under=73)                                               | —     | verified |
| 9   | ml-training-service                | coverage             | Fixed: missing starlette dep + 3 test logic bugs → 774 passed, 0 failed, 75.31%                                              | —     | verified |
| 10  | pnl-attribution-service            | test_fail + coverage | Fixed: env-leak patched + coverage 90.3% → 120 passed, 0 failed (commit 87ac6b3)                                             | —     | verified |
| 11  | position-balance-monitor-service   | test_fail            | RC-C env-leak fixed (@patch.dict isolation) commit 3f4881b; 77% coverage                                                     | —     | verified |
| 12  | alerting-service                   | test_fail            | Already fixed in prior session — 108 passed, 0 failed, 88.84% coverage                                                       | —     | verified |
| 13  | client-reporting-api               | coverage             | Manifest stale; improved to 96.13% → 82 passed, 0 failed (commit dea967c)                                                    | —     | verified |
| 14  | execution-results-api              | coverage             | Fixed: 8 tests fixed (GCP_PROJECT_ID mock) + 24 new fill_store tests → 570 passed, 0 failed, 78.74%                          | —     | verified |
| 15  | features-cross-instrument-service  | coverage             | Manifest stale — actual 91.47%, 270 passed, 0 failed (threshold: fail_under=90)                                              | —     | verified |
| 16  | instruments-service                | coverage             | Fixed: 110 new tests (error_counter, sports normalizer, fixture_parser, venue_config) → 1469 passed, 72.65% (commit f4699d0) | —     | verified |
| 17  | trading-agent-service              | coverage             | Fixed: 4 failing tests fixed (starlette stub) → 177 passed, 0 failed, 94.90%                                                 | —     | verified |
| 18  | features-sports-service            | test_fail            | RC-C env-leak fixed (@patch.dict isolation) commit 931af2b; 87% coverage                                                     | —     | verified |
| 19  | features-calendar-service          | test_fail            | RC-C env-leak fixed (@patch.dict isolation) commit 41ddb31; 72% coverage                                                     | —     | verified |
| 20  | ml-inference-api                   | unknown              | New repo — 22 passed, 0 failed, 78.21%                                                                                       | —     | verified |
| 21  | ml-training-api                    | unknown              | New repo — 38 passed, 0 failed, 95.37%                                                                                       | —     | verified |
| 22  | trading-analytics-api              | unknown              | New repo — 42 passed, 0 failed, 98.95%                                                                                       | —     | verified |

---

## Issues (Discovered in "Other 41" scan)

| #   | Repo               | Issue Type           | Details                                                                                                                                 | Agent | Status      |
| --- | ------------------ | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----- | ----------- |
| 23  | deployment-api     | test_fail + coverage | Fixed: 74 test API-mismatch failures (UCI StorageClient) + missing helpers re-exports → 1749 passed, 70.57% (commits 4d9bbf6 + earlier) | —     | verified    |
| 24  | deployment-service | test_fail            | 12 turbo/missing-data tests fail: old GCS mock API vs UCI StorageClient; fix agent running                                              | af8d1 | in_progress |

---

## Fix Agent Results

_(Append here as each agent completes)_
