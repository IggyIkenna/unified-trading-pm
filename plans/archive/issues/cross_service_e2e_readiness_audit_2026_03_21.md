---
title: "Cross-Service E2E Readiness Audit"
created: 2026-03-21
archived: 2026-05-07
source: service_control_surface_issues_2026_03_21.md + instruments-service E2E testing
status:
  archived — load_dotenv override=False shipped across all listed services (verified 2026-05-07); residual items shipped
  or superseded by writegate / Group F / instruments+MTDS-completion umbrellas
---

# Cross-Service E2E Readiness Audit

Audits all services against the 10 issues found during instruments-service E2E testing. Goal: ensure every service is
ready for its own E2E test (following the instruments-service 7-phase pattern) before reaching staging.

---

## Issue #1: `load_dotenv(override=True)` defeats shell env vars

**Library-level fix confirmed:** instruments-service fixed to `override=False`.

| Service                     | Call Site                            | override=             | Status    |
| --------------------------- | ------------------------------------ | --------------------- | --------- |
| instruments-service         | cli/main.py:29                       | `False`               | FIXED     |
| market-tick-data-service    | config.py:332, config_manager.py:460 | **default (True)**    | NEEDS FIX |
| features-onchain-service    | cli/main.py:30                       | **default (True)**    | NEEDS FIX |
| features-delta-one-service  | cli/main.py:47                       | **default (True)**    | NEEDS FIX |
| features-volatility-service | cli/service_entry.py:50              | **default (True)**    | NEEDS FIX |
| features-commodity-service  | cli/main.py:25                       | **default (True)**    | NEEDS FIX |
| execution-service           | **init**.py:34                       | `False`               | OK        |
| execution-service           | cli/backtest.py:43                   | **default (True)**    | NEEDS FIX |
| unified-trading-api         | main.py (consolidated gateway)       | `False`               | OK        |
| ml-training-service         | cli/handlers/**init**.py:20          | **default (no args)** | NEEDS FIX |
| ml-inference-service        | cli/main.py:54                       | `False`               | OK        |
| strategy-service            | cli/main.py:40                       | `False`               | OK        |
| unified-trading-library     | **init**.py:51                       | `False`               | OK        |

**`load_dotenv()` with no args defaults to `override=False`** in python-dotenv >=1.0. But `load_dotenv(path)` with just
a path also defaults to `override=False`. Services calling `load_dotenv(env_path)` without explicit `override=False` are
OK on current python-dotenv but should be explicit for clarity.

**CRITICAL:** `ml-training-service` calls bare `load_dotenv()` at module import time (cli/handlers/**init**.py:20) —
this runs before any CLI parsing, so `.env` values are loaded early. Not dangerous (override=False default) but should
be moved to CLI entry point for consistency.

### Verdict: 6 services need `override=False` added explicitly

---

## Issue #2: `--dry-run` parsed but never enforced

**Framework-level fix confirmed:** ServiceCLI (UTL service_cli.py:214) calls `set_dry_run(True)` on UCI factory, which
swaps DataSink to no-op.

| Service                          | Uses ServiceCLI       | Handler checks dry_run              | Status |
| -------------------------------- | --------------------- | ----------------------------------- | ------ |
| instruments-service              | Yes                   | Yes (cli/main.py)                   | OK     |
| market-tick-data-service         | Yes                   | Yes (cli/main.py:303)               | OK     |
| features-onchain-service         | Yes                   | Yes (handlers/batch_handler.py:108) | OK     |
| features-delta-one-service       | Yes                   | Yes (cli/main.py:82)                | OK     |
| features-volatility-service      | Yes                   | Yes (handlers/)                     | OK     |
| strategy-service                 | Yes                   | Assumed (uses ServiceCLI)           | VERIFY |
| execution-service                | Partial               | Yes (cli/backtest.py:172)           | OK     |
| ml-training-service              | Yes                   | Yes (cli/handlers/:317,355)         | OK     |
| ml-inference-service             | Yes                   | Yes (cli/main.py:182)               | OK     |
| pnl-attribution-service          | Yes                   | Unknown                             | VERIFY |
| position-balance-monitor-service | Custom ServiceCLI     | Unknown                             | VERIFY |
| alerting-service                 | No (standalone)       | N/A                                 | N/A    |
| risk-and-exposure-service        | Unknown               | Unknown                             | VERIFY |
| reconciliation-service           | No (batch-live-recon) | Yes (all 6 stages check)            | OK     |

**Key finding:** batch-live-reconciliation-service has EXCELLENT dry-run enforcement — every stage explicitly checks and
logs "DRY RUN" with skip behavior. This is the gold standard other services should follow.

### Verdict: 4 services need verification, 0 confirmed broken

---

## Issue #3: Hardcoded bucket names in .env files

| Location                           | Violation                                                    | Status                 |
| ---------------------------------- | ------------------------------------------------------------ | ---------------------- |
| execution-service/.env.mock        | 4 hardcoded bucket names (mock-\*)                           | ACCEPTABLE (mock-only) |
| .env.dev.template (workspace root) | 5 hardcoded bucket patterns (\*-unified-trading-dev)         | NEEDS FIX              |
| deployment-service/.env.local      | STATE_BUCKET=deployment-orchestration-central-element-323112 | NEEDS FIX              |

**Note:** Mock-mode `.env.mock` files with `mock-*` prefixes are acceptable — they're used for local testing. Real
bucket names with project IDs are the violation.

### Verdict: 2 files need remediation

---

## Issue #6: Asyncio nesting — `asyncio.run()` inside async context

| Service                          | Location                | Risk   | Details                                                                                              |
| -------------------------------- | ----------------------- | ------ | ---------------------------------------------------------------------------------------------------- |
| position-balance-monitor-service | cli/service_entry.py:54 | HIGH   | Custom ServiceCLI calls `asyncio.run(handler.run())` — will nest if migrated to canonical ServiceCLI |
| position-balance-monitor-service | cli/main.py:123,136     | MEDIUM | Two sequential `asyncio.run()` calls (not nested, but should consolidate)                            |
| alerting-service                 | **main**.py:7           | NONE   | Standalone entry — no nesting risk                                                                   |
| trading-agent-service            | **main**.py:145         | NONE   | Standalone entry — no nesting risk                                                                   |

**Key finding:** The canonical ServiceCLI (UTL service_cli.py:235) calls `asyncio.run(handler.run())`. Any service with
a CUSTOM ServiceCLI that also calls `asyncio.run()` will double-nest when migrated. Only
position-balance-monitor-service has this pattern.

### Verdict: 1 service (position-balance-monitor-service) needs migration to canonical ServiceCLI

---

## Issue #7: Raw API keys in .env files

| Location                              | Violation                                          | Severity |
| ------------------------------------- | -------------------------------------------------- | -------- |
| odum-research-website/.env.local      | Firebase API key, project ID, app ID, client email | P1       |
| odum-research-website/.env.production | Same Firebase credentials duplicated               | P1       |
| deployment-service/.env.local         | GCP project ID, service accounts, bucket names     | P2       |

**Note:** Firebase API keys are technically "public" (restricted by Firebase Security Rules, not by key secrecy), but
the pattern is still wrong — credentials should come from Secret Manager or environment injection, not checked-in files.

### Verdict: 3 files need remediation (2 P1, 1 P2)

---

## Issue #8: PREDICTION category falls through to all categories

| Service                  | Category Method                      | PREDICTION handling               | Risk |
| ------------------------ | ------------------------------------ | --------------------------------- | ---- |
| instruments-service      | Boolean flags                        | Falls through to ALL              | HIGH |
| market-tick-data-service | argparse choices                     | Not in choices — argparse rejects | OK   |
| strategy-service         | Enum choices                         | Not in choices — argparse rejects | OK   |
| ml-training-service      | Enum choices ["CEFI","TRADFI","ALL"] | Not in choices — argparse rejects | OK   |
| features-\* services     | Enum choices per service             | Not in choices — argparse rejects | OK   |

**Key finding:** Only instruments-service uses the boolean flag pattern where unknown categories silently fall through.
All other services use argparse `choices=` which rejects unknown values at parse time. The fix is instruments-specific:
add validation in `_resolve_categories()`.

### Verdict: 1 service (instruments-service) — instruments-specific bug

---

## Issue #9: SPORTS category resolves to 0 venues

| Service                     | SPORTS supported        | What happens                                  | Status    |
| --------------------------- | ----------------------- | --------------------------------------------- | --------- |
| instruments-service         | Parsed, not wired       | 0 venues resolved                             | ISSUE     |
| market-tick-data-service    | In download loop        | Processes SPORTS venues from UAC              | VERIFY    |
| features-sports-service     | Implicit (only service) | Always processes SPORTS                       | OK        |
| strategy-service            | Explicitly filtered OUT | `MarketCategory.SPORTS` excluded from choices | BY DESIGN |
| ml-training-service         | Not in choices          | Rejected at parse                             | BY DESIGN |
| features-onchain-service    | Not in choices          | Rejected at parse                             | BY DESIGN |
| features-delta-one-service  | Not in choices          | Rejected at parse                             | BY DESIGN |
| features-volatility-service | Not in choices          | Rejected at parse                             | BY DESIGN |

**Key finding:** SPORTS is correctly handled only by features-sports-service (dedicated). Strategy and ML services
explicitly exclude SPORTS because they don't have sports strategies/models yet. instruments-service is the only one
where SPORTS is accepted but not wired — this is instruments-specific.

### Verdict: 1 service (instruments-service) — instruments-specific wiring gap

---

## Issue #4 & #5: EnvironmentMode / TestnetMode parsing

**Fixed at library level (UIC + UCI). Applies globally. No per-service audit needed.**

---

## Issue #10: GCS writes may not be landing

**instruments-service-specific.** The CloudInstrumentStorage write path needs tracing. Not applicable to other services
until their E2E Phase 3 (real writes).

---

## E2E Readiness Summary Per Service

Services ordered by pipeline position (upstream → downstream):

### Tier 1: Data Pipeline Head (no upstream deps)

| Service                      | Pipeline Position           | Blocking Issues                                                     | E2E Ready?       |
| ---------------------------- | --------------------------- | ------------------------------------------------------------------- | ---------------- |
| **instruments-service**      | #1                          | #8 (PREDICTION fallthrough), #9 (SPORTS 0 venues), #10 (GCS writes) | NO — 3 issues    |
| **market-tick-data-service** | #2 (depends on instruments) | load_dotenv default, SPORTS venue verification needed               | ALMOST — 2 minor |

### Tier 2: Feature Services (depend on tick data)

| Service                              | Blocking Issues                    | E2E Ready?       |
| ------------------------------------ | ---------------------------------- | ---------------- |
| **features-onchain-service**         | load_dotenv default                | ALMOST — 1 minor |
| **features-delta-one-service**       | load_dotenv default                | ALMOST — 1 minor |
| **features-volatility-service**      | load_dotenv default                | ALMOST — 1 minor |
| **features-technical-service**       | Need to verify ServiceCLI adoption | VERIFY           |
| **features-microstructure-service**  | Need to verify ServiceCLI adoption | VERIFY           |
| **features-orderflow-service**       | Need to verify ServiceCLI adoption | VERIFY           |
| **features-alternative-service**     | Need to verify ServiceCLI adoption | VERIFY           |
| **features-cross-sectional-service** | Need to verify ServiceCLI adoption | VERIFY           |
| **features-sentiment-service**       | Need to verify ServiceCLI adoption | VERIFY           |
| **features-sports-service**          | No ServiceCLI, custom CLI          | VERIFY           |
| **features-commodity-service**       | load_dotenv default                | ALMOST — 1 minor |

### Tier 3: Strategy & Execution

| Service               | Blocking Issues            | E2E Ready?       |
| --------------------- | -------------------------- | ---------------- |
| **strategy-service**  | Verify dry-run enforcement | ALMOST           |
| **execution-service** | load_dotenv in backtest.py | ALMOST — 1 minor |

### Tier 4: Post-Trade

| Service                              | Blocking Issues                                          | E2E Ready?    |
| ------------------------------------ | -------------------------------------------------------- | ------------- |
| **pnl-attribution-service**          | Verify dry-run enforcement                               | VERIFY        |
| **position-balance-monitor-service** | Custom ServiceCLI (asyncio nesting risk), verify dry-run | NO — 2 issues |
| **risk-and-exposure-service**        | Verify ServiceCLI adoption + dry-run                     | VERIFY        |
| **alerting-service**                 | Standalone (no ServiceCLI) — verify mock mode            | VERIFY        |
| **reconciliation-service**           | Excellent dry-run enforcement                            | ALMOST        |

### Tier 5: ML Pipeline

| Service                  | Blocking Issues                    | E2E Ready?       |
| ------------------------ | ---------------------------------- | ---------------- |
| **ml-training-service**  | load_dotenv at import time (minor) | ALMOST — 1 minor |
| **ml-inference-service** | None found                         | YES              |

---

## Priority Fix Order

### P0 — Must fix before any E2E testing

1. **instruments-service #10**: Trace GCS write path (blocking real-write testing)
2. **position-balance-monitor-service**: Migrate to canonical ServiceCLI (asyncio nesting)

### P1 — Fix before staging

3. **instruments-service #8**: Add PREDICTION validation in `_resolve_categories()`
4. **instruments-service #9**: Wire SPORTS venues to USRI adapter
5. **.env credential cleanup**: Remove raw keys from odum-research-website, deployment-service
6. **load_dotenv explicit override=False**: 6 services need the flag added

### P2 — Fix for robustness

7. **.env.dev.template**: Remove hardcoded bucket names
8. **ml-training-service**: Move `load_dotenv()` from module import to CLI entry
9. **Verify dry-run** in strategy-service, pnl-attribution-service, risk-and-exposure-service

---

## E2E Test Template (from instruments-service)

Each service E2E test should follow this 7-phase structure:

| Phase                 | What                               | Validates                             |
| --------------------- | ---------------------------------- | ------------------------------------- |
| 1. Startup Validation | Env var combos (valid + invalid)   | Config parsing, fail-loud             |
| 2. Dry-Run            | All operations with --dry-run      | No writes, correct output             |
| 3. Real Writes        | Dev environment, CSV sampling      | Data lands in correct path            |
| 4. Category Sweep     | Each supported category            | Correct venues, correct data          |
| 5. Live Mode          | --operation live --mode batch/live | Event logging, topology               |
| 6. Mock Mode          | CLOUD_MOCK_MODE=true + scenarios   | Mock data generated, local sink       |
| 7. Observability      | ServiceRuntime log, UEI events     | Shard isolation, error classification |

Next E2E test doc to create: `002_market_tick_data_service.md`
