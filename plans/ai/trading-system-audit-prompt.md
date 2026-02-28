# Trading System Codebase Audit Prompt

**Purpose:** Generic auditor prompt for evaluating any trading system codebase against institutional-grade standards covering code quality, security, safety, schema governance, error handling, observability, and data feed architecture.

**Format:** Score each category `PASS / WARN / FAIL`. Provide per-item evidence (file path + line). Output as structured table + findings list.

---

## AUDITOR INSTRUCTIONS

You are auditing a trading system codebase. For each section below, evaluate every listed criterion. Return results in this format:

```
CATEGORY | CRITERION | STATUS | EVIDENCE
```

Where STATUS = `PASS` | `WARN` | `FAIL` | `N/A`.

At the end, output:
- Overall grade: PASS (0 FAILs) / CONDITIONAL (≥1 WARNs, 0 FAILs) / FAIL (≥1 FAILs)
- Top 5 blocking findings with file:line references

---

## SECTION 1 — CODE QUALITY GATES

### 1.1 Linting & Formatting

| # | Criterion | Blocking |
|---|-----------|----------|
| 1.1.1 | Ruff linter runs with zero errors (`ruff check --no-fix`) | YES |
| 1.1.2 | Ruff formatter is applied (`ruff format --check`) | YES |
| 1.1.3 | Line length ≤ 100 chars enforced (E501 in ruff config, not globally ignored) | YES |
| 1.1.4 | No bare `except:` or `except Exception: pass` anywhere (E722 not in global ignore) | YES |
| 1.1.5 | No `# noqa` or `# type: ignore` used to hide architectural violations | YES |
| 1.1.6 | basedpyright (or pyright strict) passes with zero reportAny / reportUnknown errors | YES |
| 1.1.7 | Import order correct — stdlib → third-party → local; no imports inside functions | YES |

### 1.2 Type Safety

| # | Criterion | Blocking |
|---|-----------|----------|
| 1.2.1 | No `Any` types except in documented bypass audit file | YES |
| 1.2.2 | All dict parameters typed as `dict[str, SpecificType]`, not `dict[str, Any]` | YES |
| 1.2.3 | No `TypedDict` fields typed as `Any` | YES |
| 1.2.4 | Protocol types used for duck typing instead of `Any` | WARN |
| 1.2.5 | TypeVar used for generic functions instead of `Any` | WARN |
| 1.2.6 | Built-in generics used: `list[X]`, `dict[K,V]`, `tuple[X,...]` — not `typing.List`, `typing.Dict` | WARN |

### 1.3 File & Function Size

| # | Criterion | Blocking |
|---|-----------|----------|
| 1.3.1 | No source file exceeds 900 lines | YES |
| 1.3.2 | No function exceeds 50 lines | WARN |
| 1.3.3 | No class exceeds 300 lines | WARN |
| 1.3.4 | Files split by Single Responsibility Principle (no god files mixing adapters + schemas + CLI) | WARN |

### 1.4 Dependency Management

| # | Criterion | Blocking |
|---|-----------|----------|
| 1.4.1 | `uv` used as package manager — no bare `pip install` in any script or Dockerfile | YES |
| 1.4.2 | `uv.lock` is committed and up to date | YES |
| 1.4.3 | `pyproject.toml` is canonical — no `requirements.txt` as parallel dependency source | WARN |
| 1.4.4 | All dependency versions pinned or range-bounded; no unbounded `>=` without upper bound on critical deps | WARN |
| 1.4.5 | Dev dependencies separated from production (`[project.optional-dependencies.dev]`) | WARN |

---

## SECTION 2 — SECURITY & SECRETS

| # | Criterion | Blocking |
|---|-----------|----------|
| 2.1 | No API keys, passwords, or credentials hardcoded anywhere in source | YES |
| 2.2 | All secrets retrieved from Secret Manager (not `os.getenv()` with empty fallback) | YES |
| 2.3 | No credential JSON files in repository (`.gitignore` uses `*credentials*.json`, not allowlist exclusions) | YES |
| 2.4 | No hardcoded project IDs — parameterised via `GCP_PROJECT_ID` env var or config class | YES |
| 2.5 | `GOOGLE_CLOUD_PROJECT` not used as primary env var (use `GCP_PROJECT_ID`) | YES |
| 2.6 | No auth bypass flags in production code (e.g., `verify=False` in HTTP clients) | YES |
| 2.7 | PII fields tagged in schema definitions (`pii: True` metadata or equivalent) | WARN |
| 2.8 | Wallet addresses, account IDs, user IDs identified and tagged for regulatory retention | WARN |
| 2.9 | Endpoint registry marks unconfirmed or blacklisted credentials as `BLACKLISTED_NO_FREE_SOURCE` | WARN |
| 2.10 | AUTH_FAILURE events logged with `auth_type`, `username`, `failure_reason` — no silent auth failure | YES |
| 2.11 | SECRET_ACCESSED events logged with `secret_name`, `caller_identity`, `success` | WARN |
| 2.12 | CONFIG_CHANGED events logged with `config_file`, `changed_by`, `authorized` | WARN |

---

## SECTION 3 — ERROR HANDLING

| # | Criterion | Blocking |
|---|-----------|----------|
| 3.1 | No empty `except Exception: pass` blocks anywhere in production code | YES |
| 3.2 | Every error type has an assigned strategy: retry / fail-fast / exit-job / exit-process / circuit-breaker | YES |
| 3.3 | Transient errors (rate limit, network blip) use bounded retry with exponential backoff | YES |
| 3.4 | Fatal errors (config corrupt, unrecoverable) trigger clean shutdown with FAILED lifecycle event | YES |
| 3.5 | Circuit breakers used for upstream dependencies that fail repeatedly | WARN |
| 3.6 | All external API errors normalised to typed error schema — no raw exception propagation across boundaries | YES |
| 3.7 | Validation failures at API boundaries route to dead-letter queue — never silently passed through | YES |
| 3.8 | `EnhancedError` (or equivalent typed error) used at all service boundaries — no bare `Exception` | YES |
| 3.9 | Dead-letter records include `correlation_id` and `trace_id` for cross-service incident reconstruction | WARN |
| 3.10 | Request-response-error schema symmetry at every layer (external / normalised / internal) | YES |
| 3.11 | No `try/except ImportError` fallback imports — fail loud on missing dependencies | YES |

---

## SECTION 4 — OBSERVABILITY & LOGGING

| # | Criterion | Blocking |
|---|-----------|----------|
| 4.1 | No `print()` statements in production code — all output through structured logger | YES |
| 4.2 | Lifecycle events emitted: STARTED, VALIDATION_STARTED, VALIDATION_COMPLETED, DATA_INGESTION_STARTED, DATA_INGESTION_COMPLETED, PROCESSING_STARTED, PROCESSING_COMPLETED, DATA_BROADCAST / PERSISTENCE_STARTED / PERSISTENCE_COMPLETED, STOPPED / FAILED | YES |
| 4.3 | Service never exits without logging STOPPED or FAILED | YES |
| 4.4 | No `setup_cloud_logging` — use structured event logging system | YES |
| 4.5 | Events logged with structured metadata (not free-form strings) | WARN |
| 4.6 | Correlation IDs propagated through all events for trace reconstruction | WARN |
| 4.7 | `datetime.now(timezone.utc)` used — never `datetime.now()`, `datetime.utcnow()`, or `datetime.today()` | YES |
| 4.8 | All timestamps in stored schemas are timezone-aware UTC | YES |
| 4.9 | Metrics / health checks exist for live services | WARN |

---

## SECTION 5 — CONFIGURATION & ENVIRONMENT

| # | Criterion | Blocking |
|---|-----------|----------|
| 5.1 | No `os.getenv()` in service code — all config via typed config class (e.g., Pydantic BaseSettings) | YES |
| 5.2 | No `os.getenv('KEY', '')` empty fallbacks — required values must fail loudly if absent | YES |
| 5.3 | Config class validates all required fields at startup — not lazily on first use | YES |
| 5.4 | No hardcoded environment-specific values (bucket names, topic names, project IDs) | YES |
| 5.5 | Bucket / topic names parameterised by environment (e.g., `market-data-{category}-{project_id}`) | YES |
| 5.6 | Runtime config changes supported via hot-reload mechanism — no manual restart required | WARN |
| 5.7 | `MAX_WORKERS` set based on workload type: I/O-bound=16, CPU-bound=1-3 | WARN |
| 5.8 | Adaptive RAM thresholds implemented: 85% → reduce workers; 90% → emergency shutdown | WARN |

---

## SECTION 6 — ARCHITECTURE & DESIGN

### 6.1 Batch-Live Symmetry

| # | Criterion | Blocking |
|---|-----------|----------|
| 6.1.1 | Service supports `--mode batch\|live` with a single shared engine (≥90% shared logic) | YES |
| 6.1.2 | No `if mode == "batch": ... else: ...` inside engine business logic | YES |
| 6.1.3 | Only 4 seams differ by mode: data source, data sink, persistence, trigger | YES |
| 6.1.4 | Business logic, validation, schema, event logging are mode-agnostic | YES |

### 6.2 Service Architecture

| # | Criterion | Blocking |
|---|-----------|----------|
| 6.2.1 | Services are thin orchestrators — no business logic in CLI or main entry point | WARN |
| 6.2.2 | Engine / adapters / CLI structure enforced | WARN |
| 6.2.3 | Adapters are thin — delegate normalisation to unified libraries, not reimplemented | YES |
| 6.2.4 | No duplicate schema definitions that already exist in shared contracts library | YES |
| 6.2.5 | No parallel code paths (old + new schema, old + new import) — single source of truth per function | YES |
| 6.2.6 | Deprecated code deleted, not commented out or aliased | YES |
| 6.2.7 | No `_old.py`, `_legacy.py`, `_deprecated.py` copies in source tree | YES |

### 6.3 Async & Concurrency

| # | Criterion | Blocking |
|---|-----------|----------|
| 6.3.1 | `aiohttp` used for HTTP in async contexts — no `requests.get()` inside `async def` | YES |
| 6.3.2 | `asyncio.sleep()` used — not `time.sleep()` in async functions | YES |
| 6.3.3 | No `asyncio.run()` called inside a running event loop | YES |
| 6.3.4 | WebSocket connections never shared across threads (one thread per connection) | YES |
| 6.3.5 | `ClientSession` reused — not created per-request | WARN |
| 6.3.6 | `ThreadPoolExecutor` always given `max_workers` limit | YES |

---

## SECTION 7 — SCHEMA GOVERNANCE & DATA CONTRACTS

### 7.1 Schema Ownership

| # | Criterion | Blocking |
|---|-----------|----------|
| 7.1.1 | Three-tier schema separation: external (api-contracts) → normalised (canonical) → internal (service) | YES |
| 7.1.2 | Each service owns its output schema — not defined in shared library | YES |
| 7.1.3 | `validate_timestamp_date_alignment()` called before every storage write | YES |
| 7.1.4 | `schema_version` field present on all internal contract models | WARN |
| 7.1.5 | `SchemaRegistry` documents compatibility matrix for all versioned schemas | WARN |
| 7.1.6 | Breaking changes (field removal, type narrowing, Optional→required) require version bump | YES |

### 7.2 External API Contracts (api-contracts layer)

| # | Criterion | Blocking |
|---|-----------|----------|
| 7.2.1 | Every external API response parsed through a Pydantic model before any processing | YES |
| 7.2.2 | Per-venue schemas exist for all data types the system consumes | YES |
| 7.2.3 | VCR cassettes exist for all external API interactions used in tests | WARN |
| 7.2.4 | VCR cassette coverage ≥ 80% of external endpoints (not relying on live calls in CI) | WARN |
| 7.2.5 | Consumer-driven contract tests: consuming services declare `consumed_schemas.py` | WARN |
| 7.2.6 | SDK version alignment check runs in CI (`check_sdk_version_alignment.py` pattern) | WARN |

### 7.3 Canonical Schema Completeness

Verify the following data type groups have canonical schemas with appropriate Optional fields:

| Data Type | Required Fields | Optional Pattern |
|-----------|----------------|-----------------|
| Trade | instrument_key, venue, timestamp, price, size, side, trade_id | is_liquidation |
| OrderBook | instrument_key, venue, timestamp, bids, asks, levels | - |
| OHLCV | instrument_key, venue, timestamp, interval, open/high/low/close, volume, source_enum | vwap, trade_count |
| DerivativeTicker | instrument_key, venue, timestamp, mark_price, index_price | funding_rate, predicted_funding_rate, open_interest, borrow rates |
| Liquidation | instrument_key, venue, timestamp, side, price, size | order_id, liquidated_account_value |
| OptionsChain | underlying, expiry, strike, put_call, bid, ask | iv, greeks, oi, volume |
| LiquidityPool | pool_address, protocol, chain, token0/1, fee_tier, reserves, tvl | apy, tick fields (V3) |
| LendingRate | protocol, chain, asset, supply_apy, borrow_apy_variable | borrow_apy_stable, borrow_shares |
| OraclePrice | feed_id, protocol, asset, price, publish_time | confidence |
| InstrumentRecord | instrument_key, venue, asset_class, instrument_type, base, quote | expiry, strike, pool_address, ltv |
| Position (CeFi) | instrument_key, venue, side, size, entry_price, mark_price, unrealized_pnl | liquidation_price |
| Position (DeFi LP) | pool_address, protocol, token amounts, liquidity, fee_income | in_range, tick bounds (V3) |

| # | Criterion | Blocking |
|---|-----------|----------|
| 7.3.1 | All consumed data types have a canonical schema | YES |
| 7.3.2 | Absent fields (venue does not provide) are `Optional` — not absent from schema | YES |
| 7.3.3 | `?` (unconfirmed) fields have VCR TODO stub test | WARN |
| 7.3.4 | `source` enum on OHLCV: `NATIVE_CANDLE \| COMPUTED_FROM_TICKS` | WARN |
| 7.3.5 | No monolithic position schema mixing CeFi + DeFi | WARN |

### 7.4 Normalisation Pipeline Integrity

| # | Criterion | Blocking |
|---|-----------|----------|
| 7.4.1 | Every adapter follows two-step contract: parse via api-contracts → map to canonical | YES |
| 7.4.2 | Validation failure at step 1 raises typed error + routes to dead-letter — no silent pass-through | YES |
| 7.4.3 | Abstract `_parse_raw()` enforced in base adapter class | WARN |
| 7.4.4 | Services are source-agnostic (same canonical output regardless of batch/Tardis vs live/exchange WS) | YES |
| 7.4.5 | `VenueCapabilities` schema declares per-venue supported data types | WARN |

### 7.5 Dead-Letter & DLQ

| # | Criterion | Blocking |
|---|-----------|----------|
| 7.5.1 | Dead-letter queue exists for failed validation records | YES |
| 7.5.2 | `DeadLetterRecord` schema includes: original_payload, error_type, error_message, venue, timestamp | YES |
| 7.5.3 | `correlation_id` and `trace_id` in `DeadLetterRecord` for tracing | WARN |
| 7.5.4 | DLQ depth monitored and alerted | WARN |

---

## SECTION 8 — TESTING STANDARDS

| # | Criterion | Blocking |
|---|-----------|----------|
| 8.1 | Test coverage ≥ 50% (unit + integration) | WARN |
| 8.2 | `tests/unit/test_event_logging.py` exists and is not skipped | YES |
| 8.3 | Unit tests never skip due to missing cloud credentials — mocks used instead | YES |
| 8.4 | GCP auth uses `google.auth.default()` pattern — not `pytest.skip` on missing credentials file | YES |
| 8.5 | Integration tests marked `@pytest.mark.integration` and skipped gracefully without credentials | YES |
| 8.6 | No `create_test_*_extended.py` — expand existing test files instead | WARN |
| 8.7 | No duplicate fixtures across test files — singleton fixtures in `conftest.py` | WARN |
| 8.8 | No `central-element-323112` or real project IDs in tests — use `test-project` placeholder | YES |
| 8.9 | AWS unit tests mock `boto3` fully — pass without AWS credentials | YES |
| 8.10 | VCR cassettes used for external API tests — no live calls in CI | WARN |
| 8.11 | Consumer-driven contract tests exist for cross-service schema dependencies | WARN |
| 8.12 | Schema breaking-change detection script runs in CI | WARN |

---

## SECTION 9 — CI/CD & DEPLOYMENT

| # | Criterion | Blocking |
|---|-----------|----------|
| 9.1 | Quality gates run INSIDE the built Docker image — not by cloning source in CI | YES |
| 9.2 | Image pushed only after tests pass | YES |
| 9.3 | Library version bumped before publishing (idempotent publish: same commit = skip, different = fail) | YES |
| 9.4 | Pre-commit hooks installed and running (`prek install`) | WARN |
| 9.5 | Branch protection blocks direct push to main | YES |
| 9.6 | Quickmerge (or equivalent) used — never standalone quality gates | YES |
| 9.7 | `uv.lock` committed alongside `pyproject.toml` changes | YES |
| 9.8 | No git token or SA key embedded in Dockerfile or Cloud Build YAML | YES |
| 9.9 | SSOT alignment validation runs as pre-commit hook (no banned terms, canonical names) | WARN |

---

## SECTION 10 — DATA FEED UNIVERSE COMPLETENESS

*Applicable to systems with multi-venue market data ingestion.*

### 10.1 Venue Coverage Matrix

For each venue the system claims to support, verify:

| # | Criterion | Blocking |
|---|-----------|----------|
| 10.1.1 | api-contracts schema exists for every data type the venue provides | YES |
| 10.1.2 | Normalizer function exists in adapter for each confirmed data type | YES |
| 10.1.3 | `✓` data types have VCR cassette test (not live call) | WARN |
| 10.1.4 | `–` (absent) data types documented in VenueCapabilities — not just missing | YES |
| 10.1.5 | `?` (unconfirmed) data types have `Optional` schema field + TODO VCR stub | WARN |

### 10.2 Batch-Live Source Symmetry

| # | Criterion | Blocking |
|---|-----------|----------|
| 10.2.1 | Canonical output identical whether data sourced from aggregator (Tardis/CCXT) or direct exchange WS | YES |
| 10.2.2 | Source choice is a config concern, not hardcoded in engine | YES |
| 10.2.3 | OHLCV schema includes `source` enum: `NATIVE_CANDLE \| COMPUTED_FROM_TICKS` | WARN |
| 10.2.4 | Batch reference data types and live reference data types declared in `VenueCapabilities` | WARN |

### 10.3 DeFi Data Completeness

| # | Criterion | Blocking |
|---|-----------|----------|
| 10.3.1 | DeFi schemas support V2/V3/V4 liquidity pools (V3-specific fields Optional) | WARN |
| 10.3.2 | Lending schemas include: supply APY, borrow APY, utilization, health factor, LTV | WARN |
| 10.3.3 | Oracle price schemas cover both Pyth and Chainlink formats | WARN |
| 10.3.4 | Live DeFi streaming adapters exist (TheGraph WS / Alchemy WS / Pyth WS) | WARN |
| 10.3.5 | Staking rate schemas exist for LST protocols | WARN |

### 10.4 Order Type Coverage

| # | Criterion | Blocking |
|---|-----------|----------|
| 10.4.1 | `POST_ONLY` implemented as `TimeInForce` modifier, not standalone `OrderType` | WARN |
| 10.4.2 | `TRAILING_STOP_LIMIT` and `TRAILING_TAKE_PROFIT` implemented (not generic `TRAILING_STOP`) | WARN |
| 10.4.3 | Per-venue order type support declared in `VenueCapabilities` schema | WARN |
| 10.4.4 | Order lifecycle state machine: `PENDING_NEW → NEW → PARTIALLY_FILLED → FILLED / CANCELLED / REJECTED / EXPIRED` | WARN |

---

## SECTION 11 — SAFETY & RISK CONTROLS

| # | Criterion | Blocking |
|---|-----------|----------|
| 11.1 | Position limits enforced before order submission | YES |
| 11.2 | Margin state checked before every leveraged trade | YES |
| 11.3 | `MarginState` fields all non-optional and required from every adapter | YES |
| 11.4 | Gas cost estimated before every DeFi transaction — never unlimited gas | YES |
| 11.5 | Slippage tolerance enforced on all DEX swaps | YES |
| 11.6 | `health_factor` checked before additional borrowing (DeFi) | YES |
| 11.7 | Liquidation threshold monitored with alerts | WARN |
| 11.8 | Circuit breaker exists for P&L drawdown limits | WARN |
| 11.9 | All order amounts validated against tick size and lot size constraints | YES |
| 11.10 | Regulatory retention periods defined for trade records (min 7 years for most jurisdictions) | WARN |
| 11.11 | `schema_version` on all stored records enables forward-compatible migration | WARN |

---

## SECTION 12 — ANTI-PATTERN SCAN

Run a targeted scan for the following patterns. Each `FOUND` = automatic FAIL.

```
PATTERN                          | SEARCH                              | BLOCKING
os.getenv(                       | rg "os\.getenv" src/                | YES
requests.get(                    | rg "requests\.get\|requests\.post"  | YES (async contexts)
datetime.now()                   | rg "datetime\.now\(\)"              | YES
datetime.utcnow()                | rg "datetime\.utcnow"               | YES
except Exception: pass           | rg "except Exception:\s*pass"       | YES
except:                          | rg "^except:$"                      | YES
from typing import List/Dict     | rg "from typing import.*List\|Dict" | WARN
# type: ignore                   | rg "# type: ignore"                 | WARN (each instance)
Any                              | rg ": Any\|-> Any"                  | YES (unaudited)
pip install                      | rg "pip install" scripts/           | YES
git push origin main             | rg "git push origin main"           | YES
GOOGLE_CLOUD_PROJECT             | rg "GOOGLE_CLOUD_PROJECT"           | YES
hardcoded project ID             | rg "central-element|my-project-id"  | YES
_old.py / _legacy.py             | find . -name "*_old.py"             | YES
try/except ImportError           | rg "except ImportError"             | YES
print(                           | rg "^\s*print(" src/               | WARN
time.sleep(                      | rg "time\.sleep" async contexts     | YES
```

---

## SECTION 13 — CODEX ALIGNMENT (Documentation Drift)

| # | Criterion | Blocking |
|---|-----------|----------|
| 13.1 | All bucket names match parameterised pattern (not hardcoded) | YES |
| 13.2 | Venue names use canonical form (e.g., BINANCE-SPOT / BINANCE-FUTURES, not BINANCE) | WARN |
| 13.3 | Lifecycle event names match canonical list (no custom event names like `INGESTING_DATA`) | YES |
| 13.4 | Architectural changes accompanied by codex doc update in same PR | WARN |
| 13.5 | Cross-service schema changes documented with migration playbook | WARN |
| 13.6 | Multi-repo rollout tracked — "plan complete" only when ALL in-scope repos updated | WARN |

---

## SCORING GUIDE

| Grade | Criteria |
|-------|----------|
| **PASS** | 0 FAIL items |
| **CONDITIONAL PASS** | 0 FAIL, ≤5 WARN (with remediation plan) |
| **FAIL** | ≥1 FAIL item |

**Automatic FAIL triggers (any one is sufficient):**
- Hardcoded API key or credential in source
- `except Exception: pass` in production code
- Validation failure silently passed through (no dead-letter)
- `os.getenv()` with empty string fallback for required config
- No lifecycle STOPPED/FAILED event on service exit
- `basedpyright` reportAny errors present
- `Any` type in schema models at API boundaries
- Tests skipped due to missing credentials (unit test scope)
- Direct `git push main` bypassing quality gates

---

## OUTPUT TEMPLATE

```
## Audit Report — [System Name] — [Date]

### Summary
- Total criteria evaluated: N
- PASS: X | WARN: Y | FAIL: Z | N/A: W
- Overall grade: PASS / CONDITIONAL PASS / FAIL

### Blocking Findings (FAIL)
1. [SECTION] [ID] — [description] — [file:line]
...

### Warning Findings (WARN)
1. [SECTION] [ID] — [description] — [file:line]
...

### Anti-Pattern Scan Results
[table of patterns found / not found]

### Recommended Remediation Priority
1. [highest risk item]
...
```
