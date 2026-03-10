# QG Issues Log — quality_gates_full_fix_2026_03_10

**Last baseline run:** 2026-03-10 (in progress) **Updated by:** master agent after each fix agent reports

---

## Status Key

- `open` — identified, not yet assigned to agent
- `in_progress` — fix agent running
- `fixed` — agent committed fix
- `verified` — re-ran QG for repo and confirmed passing

---

## Issues

| #   | Repo                               | Issue Type           | Details                                                                                 | Agent | Status   |
| --- | ---------------------------------- | -------------------- | --------------------------------------------------------------------------------------- | ----- | -------- |
| 1   | unified-market-interface           | test_fail + coverage | Fixed: `uv pip install -e` reinstalled editable wheel → 1994 passed, 0 failed, 82.11% ✓ | —     | verified |
| 2   | unified-trade-execution-interface  | test_fail            | Fixed: `uv pip install -e` reinstalled editable wheel → 964 passed, 0 failed, 90.32% ✓  | —     | verified |
| 3   | unified-trading-library            | coverage             | Manifest stale — actual 81.27%, 1180 passed, 0 failed ✓                                 | —     | verified |
| 4   | execution-algo-library             | coverage             | Manifest was stale — actual 96.65%, 201 passed, 0 failed. Already ✓                     | —     | verified |
| 5   | unified-sports-execution-interface | coverage             | Already fixed in prior session — 437 passed, 0 failed, 81.09% ✓                         | —     | verified |
| 6   | features-multi-timeframe-service   | test_fail + coverage | 57% coverage; 1 failure RC-C: CLOUD_PROVIDER env-leak in test_config                    | —     | open     |
| 7   | features-onchain-service           | coverage             | Manifest stale — actual 71.28%, 286 passed, 0 failed ✓                                  | —     | verified |
| 8   | features-volatility-service        | coverage             | 35% coverage < 70%                                                                      | —     | open     |
| 9   | ml-training-service                | coverage             | 35% coverage < 70%                                                                      | —     | open     |
| 10  | pnl-attribution-service            | test_fail + coverage | Fixed: env-leak patched + coverage already 90.3% → 120 passed, 0 failed ✓ (commit 87ac6b3) | —     | verified |
| 11  | position-balance-monitor-service   | test_fail            | 77% coverage (ok); 1 failure RC-C env-leak                                              | —     | open     |
| 12  | alerting-service                   | test_fail            | Already fixed in prior session — 108 passed, 0 failed, 88.84% coverage ✓                | —     | verified |
| 13  | client-reporting-api               | coverage             | Manifest stale; was 89.95%, improved to 96.13% → 82 passed, 0 failed ✓ (commit dea967c) | —     | verified |
| 14  | execution-results-api              | coverage             | 66% coverage < 70%                                                                      | —     | open     |
| 15  | features-cross-instrument-service  | coverage             | Manifest stale — actual 91.47%, 270 passed, 0 failed ✓ (threshold: fail_under=90)      | —     | verified |
| 16  | instruments-service                | coverage             | 53% coverage < 70%                                                                      | —     | open     |
| 17  | trading-agent-service              | coverage             | Fixed: 4 failing tests fixed (starlette stub in sys.modules) → 177 passed, 0 failed, 94.90% ✓ | —     | verified |
| 18  | features-sports-service            | test_fail            | 1 failure RC-C env-leak (87% coverage ok)                                               | —     | open     |
| 19  | features-calendar-service          | test_fail            | 1 failure RC-C env-leak (72% coverage ok)                                               | —     | open     |
| 20  | ml-inference-api                   | unknown              | New repo — coverage unknown                                                             | —     | open     |
| 21  | ml-training-api                    | unknown              | New repo — coverage unknown                                                             | —     | open     |
| 22  | trading-analytics-api              | unknown              | New repo — coverage unknown                                                             | —     | open     |

---

## Fix Agent Results

_(Append here as each agent completes)_
