---
pair: instruments-service → execution-service
auditor: slot-4 / ikenna
audit_date: 2026-05-20
audit_file: plans/audit/is_execution_contract_audit_2026_05_20.md
feeds_ordering_step: D1 (IS hardening plan)
status: complete
estimate_class: research
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 1.2
locked_by: live-defi-rollout
locked_since: 2026-05-20
---

# instruments-service ↔ execution-service Contract Audit — 2026-05-20

> **Audit scope**: instruments-service (IS) is the canonical upstream for instrument reference data (tick sizes, min
> order sizes, venue API URLs, contract specs, listing windows). execution-service is the order routing + fill-tracking
> downstream; it must source all instrument metadata from IS rather than hardcoding venue URLs, re-fetching venue APIs
> directly, or building its own universe lists.
>
> **Repo SHAs at audit time**:
>
> - `execution-service@b769cc069` (2026-05-20)
> - `instruments-service@04e49f7` (2026-05-20)
>
> **Sampling methodology**: exhaustive grep across all non-test Python source in `execution_service/` for 7 contract
> patterns; key files read in full.

---

## The architectural contract (SSOT)

```
                    ┌──────────────────────────────────────┐
                    │  instruments-service                 │
                    │  ─ enumerates venue universe         │
                    │  ─ writes InstrumentRecord           │
                    │    per (venue, instrument_id, day)   │
                    │    to instruments-store-*            │
                    │  ─ owns: tick_size, min_qty, lot_size│
                    │    venue API URLs, listed_at,        │
                    │    delisted_at, contract specs       │
                    └──────────────┬───────────────────────┘
                                   │
                                   ▼ read-only catalogue (parquet)
                    ┌──────────────────────────────────────┐
                    │  execution-service                   │
                    │  ─ InstrumentDefinitionsLoader reads │
                    │    instruments-store GCS parquets    │
                    │  ─ DependencyChecker validates IS    │
                    │    parquet exists BEFORE running     │
                    │  ─ CeFi adapters: tick_size / lot   │
                    │    sourced from IS DataFrame         │
                    │  ─ Should NOT hardcode venue API URLs│
                    │    (several still do — see Dim 2)    │
                    └──────────────────────────────────────┘
```

**The IS→execution contract differs from IS→MTDS in one important way**: execution-service is a _leaf execution
service_, not a _data capture service_. It does NOT write manifest rows to GCS — it reads instrument metadata to route
and size orders. Patterns 2 (manifest emission), 3 (schema version), and 4 (honest-absence reasons) are therefore **not
applicable** to execution-service. Patterns 1 (SSOT reference), 6 (error classification), and 7 (bucket SSOT) ARE
applicable.

---

## 4-dimensional audit matrix (2026-05-20 snapshot)

### Dim 1 — IS adapter coverage per asset_group

| asset_group | IS adapters available                                             | execution-service reads IS                                                                                                                                      | EXECUTION-uses-but-no-IS-call (the violation)                                                                          |
| ----------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| CeFi        | All CeFi venues                                                   | YES — `InstrumentDefinitionsLoader.load_for_date()` + `DependencyChecker.check_instrument_definitions()`                                                        | CeFi native adapters hardcode exchange base URLs (Binance, Bybit, OKX, Bitget, Bitfinex, Kraken) — see Dim 2           |
| DeFi        | 54 adapters (Drift, Phoenix, Orca, Raydium, Marinade, Jito, etc.) | PARTIAL — instruments module reads IS parquets for instrument resolution; DeFi connectors (`aave.py`, `deribit.py`, `uniswap.py`) query live chain/API directly | DeFi venue connectors (Deribit, ASTER, Bridge) hardcode REST base URLs                                                 |
| TradFi      | Databento, Polygon, IBKR, TradFi_Live                             | YES — `InstrumentDefinitionsLoader` + `factory_tradfi.py` reads tick_size / lot_size from IS DataFrame                                                          | None identified                                                                                                        |
| Sports      | factory + 11 per-source adapters                                  | PARTIAL — sports_adapter.py delegates to exchange adapters; no IS read for market listings                                                                      | Sports exchange adapters (Kalshi, Betfair, Matchbook, Polymarket) connect directly to venue APIs without IS pre-flight |
| Prediction  | Polymarket, Kalshi                                                | PARTIAL — `polymarket_clob.py` / `kalshi.py` connect directly; no IS cross-check                                                                                | Same as Sports                                                                                                         |

### Dim 2 — Execution handler IS-consumption status

| Component                                                    | Status                                                                                    | Citation        |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------------- | --------------- |
| `instruments/definitions_loader.py`                          | ✅ Reads IS parquets via `InstrumentDefinitionsLoader.load_for_date()`                    | lines 77-96     |
| `instruments/factory.py`                                     | ✅ Uses `InstrumentDefinitionsLoader` for GCS-backed instrument creation                  | lines 188-198   |
| `instruments/factory_tradfi.py`                              | ✅ Reads `tick_size`/`lot_size` from IS DataFrame row                                     | lines 39-57     |
| `utils/dependency_checker.py`                                | ✅ `check_instrument_definitions()` pre-flight validates IS parquet exists                | lines 548-591   |
| `engine/backtest/engine/setup.py`                            | ✅ `InstrumentsDomainClient.get_instruments_for_date()` with IS bucket path               | lines 260-290   |
| `utils/instrument_resolver.py`                               | ✅ Reads IS DEX pool parquets for pool_id resolution                                      | lines 280-340   |
| **`trade_execution/adapters/binance_native.py`**             | **❌ `_BINANCE_SPOT_BASE_URL` + `_BINANCE_FUTURES_BASE_URL` hardcoded**                   | **lines 57-58** |
| **`trade_execution/adapters/bybit_native.py`**               | **❌ `_BYBIT_BASE_URL` hardcoded**                                                        | **line 57**     |
| **`trade_execution/adapters/okx_native.py`**                 | **❌ `_OKX_BASE_URL` hardcoded**                                                          | **line 55**     |
| **`trade_execution/adapters/bitget_native.py`**              | **❌ `_BITGET_BASE_URL` hardcoded**                                                       | **line 57**     |
| **`trade_execution/adapters/bitfinex_native.py`**            | **❌ `_BFX_BASE_URL` hardcoded**                                                          | **line 57**     |
| **`trade_execution/adapters/kraken_rest_adapter.py`**        | **❌ `_KRAKEN_REST_BASE_URL` hardcoded**                                                  | **line 141**    |
| **`trade_execution/adapters/kraken_ws_client.py`**           | **❌ `_KRAKEN_WS_PUBLIC_URL` + `_KRAKEN_WS_PRIVATE_URL` hardcoded**                       | **lines 46-47** |
| **`trade_execution/ws_feeds.py`**                            | **❌ `_BINANCE_REST_BASE`, `_BINANCE_WS_BASE`, `_BYBIT_WS_URL`, `_OKX_WS_URL` hardcoded** | **lines 28-31** |
| **`venues/deribit.py`**                                      | **❌ `base_url`=`"https://www.deribit.com/api/v2"` + `ws_url` hardcoded in `__init__`**   | **lines 67-68** |
| **`defi_execution/protocols/aster.py`**                      | **❌ `ASTER_REST_BASE` hardcoded**                                                        | **line 90**     |
| **`defi_execution/protocols/bridge.py`**                     | **❌ `SOCKET_API_BASE` hardcoded**                                                        | **line 31**     |
| **`sports_execution/adapters/exchanges/kalshi.py`**          | **❌ `KALSHI_API_BASE` + `KALSHI_DEMO_BASE` hardcoded**                                   | **lines 91-92** |
| **`sports_execution/adapters/exchanges/polymarket_clob.py`** | **❌ `POLYMARKET_CLOB_BASE` hardcoded**                                                   | **line 88**     |
| **`services/bridge_cost_model.py`**                          | **❌ `ACROSS_API_BASE` hardcoded**                                                        | **line 210**    |

### Dim 3 — Manifest emission discipline

**N/A** — execution-service is a leaf execution service. It does NOT write manifest rows to GCS. It reads IS + MTDS +
strategy output; its "output" is live order fills stored in `execution-store-{asset_group}-{project_id}` parquets.

The three pattern-2 checks (`record_captured`, `record_empty`, `record_failed`) return 0 hits across the entire non-test
source tree — this is correct architecture, not a gap.

### Dim 4 — Manifest schema version per bucket

**N/A** — same rationale as Dim 3. execution-service does not maintain a manifest index.

The `execution-store-*` output buckets store raw fill parquets, not manifest indices.

---

## Pattern 6 — Error classification at the boundary

### Dim 5 — Error classification coverage

| Component                                                    | Status                                                                       | Evidence                     |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------- | ---------------------------- |
| `engine/orchestrator.py`                                     | ✅ `classify_venue_error()` + `ADAPTER_FETCH_FAILED`                         | lines 252, 348               |
| `engine/multi_leg_orchestrator.py`                           | ✅ `classify_venue_error()`                                                  | lines 334, 470               |
| `engine/routing/instruction_router.py`                       | ✅ `classify_venue_error()`                                                  | line 281                     |
| `trade_execution/adapters/_native_base.py`                   | ✅ `classify_venue_error()` in base class                                    | lines 157-167                |
| `trade_execution/adapters/kraken_rest_adapter.py`            | ✅ `classify_venue_error()`                                                  | lines 662-720                |
| `trade_execution/adapters/bybit_native.py`                   | ✅ `classify_venue_error()`                                                  | line 184                     |
| `trade_execution/adapters/okx_native.py`                     | ✅ `classify_venue_error()`                                                  | line 206                     |
| `trade_execution/adapters/bitget_native.py`                  | ✅ `classify_venue_error()`                                                  | line 180                     |
| `sports_execution/adapters/exchanges/kalshi.py`              | ✅ `classify_venue_error()` + `ADAPTER_FETCH_FAILED` at 6 callsites          | lines 254-546                |
| `sports_execution/adapters/exchanges/betfair.py`             | ✅ `classify_venue_error()` + `ADAPTER_FETCH_FAILED`                         | lines 490, 938               |
| `sports_execution/adapters/exchanges/matchbook.py`           | ✅ `classify_venue_error()` + `ADAPTER_FETCH_FAILED`                         | lines 201-207                |
| `defi_execution/protocols/aster.py`                          | ✅ `classify_venue_error()`                                                  | lines 74-81                  |
| **`trade_execution/adapters/binance_ccxt.py`**               | **⚠ `UNKNOWN_VENUE_ERROR_RECEIVED` emitted but NO `classify_venue_error()`** | **lines 281, 317, 465, 577** |
| **`trade_execution/adapters/hyperliquid_ccxt.py`**           | **⚠ NO `classify_venue_error()` — `ccxt.BaseError` caught bare**             | **lines 186, 332, 443**      |
| **`trade_execution/adapters/bybit_ccxt.py`**                 | **⚠ NO `classify_venue_error()`**                                            | all except blocks            |
| **`trade_execution/adapters/coinbase_ccxt.py`**              | **⚠ NO `classify_venue_error()`**                                            | all except blocks            |
| **`trade_execution/adapters/deribit_ccxt.py`**               | **⚠ NO `classify_venue_error()`**                                            | all except blocks            |
| **`trade_execution/adapters/okx_ccxt.py`**                   | **⚠ NO `classify_venue_error()`**                                            | all except blocks            |
| **`trade_execution/adapters/upbit_ccxt.py`**                 | **⚠ NO `classify_venue_error()`**                                            | all except blocks            |
| **`sports_execution/adapters/exchanges/polymarket_clob.py`** | **⚠ NO `classify_venue_error()`**                                            | all except blocks            |

**Note on CCXT adapters**: the `_native_base.py` base class does call `classify_venue_error()` in its HTTP-layer error
helper (line 167). CCXT adapters that inherit `BaseCLOBAdapter` may route errors through the base class — but the CCXT
adapters were confirmed NOT importing or calling `classify_venue_error()` directly. This is a partial gap: the base
class catches HTTP errors but CCXT-specific error types (`ccxt.InsufficientFunds`, `ccxt.BaseError`) escape
classification.

---

## Pattern 7 — Bucket-SSOT

### Dim 6 — Inline bucket construction vs `resolve_bucket_name()`

| Component                                | Status                                                                               | Evidence                 |
| ---------------------------------------- | ------------------------------------------------------------------------------------ | ------------------------ |
| `utils/audit_log.py`                     | ✅ `resolve_bucket_name()`                                                           | lines 8, 59              |
| `providers/tenderly_budget.py`           | ✅ `resolve_bucket_name()`                                                           | lines 32, 78             |
| `providers/l2_depth_provider.py`         | ✅ `resolve_bucket_name()`                                                           | lines 179-181            |
| `providers/solana_amm_depth_provider.py` | ✅ `resolve_bucket_name()`                                                           | lines 243-245            |
| **`utils/dependency_checker.py`**        | **❌ inline f-string bucket construction**                                           | **lines 541, 551**       |
| **`utils/loader.py`**                    | **❌ inline f-string bucket construction**                                           | **lines 19, 44, 69, 89** |
| **`utils/io/loader.py`**                 | **❌ inline f-string bucket construction**                                           | **lines 19, 44, 89**     |
| **`utils/instrument_resolver.py`**       | **❌ inline f-string with fallback**                                                 | **lines 287, 336**       |
| **`data/loader.py`**                     | **❌ `config.get_market_data_bucket(...) or f"market-data-tick-defi-{project_id}"`** | **line 463**             |
| **`data/loader_gcs.py`**                 | **❌ same inline fallback pattern**                                                  | **line 514**             |
| **`data/loaders/defi.py`**               | **❌ same inline fallback pattern**                                                  | **line 32**              |
| **`data/defi_data_loader.py`**           | **❌ inline f-string**                                                               | **line 59**              |
| **`engine/backtest/engine/setup.py`**    | **❌ `f"instruments-store-{category}-{project_id}"`**                                | **line 261**             |
| **`cli/multi_leg_config_gcs.py`**        | **❌ inline f-strings for market-data-tick-defi/cefi/tradfi buckets**                | **lines 39, 52, 102**    |
| **`config/grid_generator_v2.py`**        | **❌ `f"execution-store-{project_id}"`**                                             | **line 476**             |
| **`config/grid_v2_registry.py`**         | **❌ `f"execution-store-{project_id}"`**                                             | **line 569**             |

**P7 is the most widespread violation in execution-service.** 13 non-test source files construct bucket names as inline
f-strings instead of routing through `resolve_bucket_name()`. This is the **#1 remediation priority** (after P6 CCXT
classification gap). Many use the pattern:

```python
config.get_market_data_bucket("defi") or f"market-data-tick-defi-{project_id}"
```

The fallback is the violation — if `config.get_market_data_bucket()` returns `""`, the code falls through to an
f-string. `resolve_bucket_name()` should be the canonical path with no f-string fallback.

QG STEP 5.69 (`check_inline_bucket_uri.py`) is wired in base-service.sh and will catch new additions. However the
existing violations are covered by a `# noqa: gs-uri` comment baseline or were pre-existing before the ratchet was set.
These must be migrated.

---

## Pattern 1 — SSOT-owned reference flowing down (expanded)

### IS URL ownership context for execution-service

Unlike MTDS handlers which derive data-archive URLs from IS (`source_archive_url_template`), execution-service trade
adapters connect to **live venue trading APIs**. The question is whether IS should own these live API URLs — or whether
they are legitimately hardcoded in adapters.

**Architectural assessment (P0)**:

The CLAUDE.md codex rule states: "IS→MTDS contract: instruments-service owns all venue URLs/universe via
InstrumentRecord; MTDS handlers derive URLs from IS, never hardcode." However, execution-service adapters are in a
different category: they are _execution_ adapters, not _data ingestion_ adapters.

There are two valid interpretations:

1. **Strict**: IS should own live trading API URLs in `InstrumentRecord.source_archive_url_template` (or a new field
   `live_api_url_template`), and execution adapters should derive from IS.
2. **Pragmatic (current workspace consensus)**: Live trading API URLs are stable, public, well-known endpoints (e.g.
   `https://api.binance.com`). They do NOT belong in the IS catalog because IS is a _reference data_ service (instrument
   specs, historical data URLs), not a _connectivity_ service. The real violation is that execution-service should
   source _instrument specs_ (tick_size, min_qty, contract_size) from IS rather than re-fetching the venue API at
   runtime.

**Verdict**: The native trade adapters hardcoding `_BINANCE_SPOT_BASE_URL = "https://api.binance.com"` is **NOT a P0
violation of the IS contract** — these are connectivity constants, not instrument universe/spec data. The IS contract
violation for execution-service is narrower: execution-service should not be calling venue APIs at runtime to discover
instrument specs that IS already provides.

The **Deribit connector** (`venues/deribit.py`) _does_ call the Deribit API to fetch `tick_size` + `contract_size` at
runtime (line 505: `inst.get("tick_size")`), when IS already has Deribit InstrumentRecords with this data. **This is the
genuine IS-contract violation.**

---

## Pre-Audit Before Execution (Citadel-Grade)

Workspace-wide symbols this audit examines:

```bash
# Upstream IS consumption (the ✅ pattern):
rg 'InstrumentDefinitionsLoader|load_for_date|check_instrument_definitions' \
   execution-service/ --type py --glob '!.venv*' --glob '!tests'

# Hardcoded venue URL constants:
rg '_[A-Z_]+_URL\s*=\s*"https?://' execution-service/ --type py --glob '!tests'
rg '_[A-Z_]+_BASE\s*=\s*"https?://' execution-service/ --type py --glob '!tests'

# Hardcoded bucket f-strings (P7):
grep -rn 'f"market-data-tick\|f"instruments-store\|f"execution-store' \
   execution-service/execution_service/ --include="*.py"

# Error classification gaps (P6):
for f in execution-service/execution_service/trade_execution/adapters/*.py; do
  if ! grep -q "classify_venue_error" "$f" && grep -q "except" "$f"; then
    echo "MISSING: $(basename $f)"
  fi
done

# record_* calls (Dim 3 — expected: 0 in non-test source):
rg 'record_captured|record_empty|record_failed' execution-service/execution_service/ --type py
```

**Audit coverage**: exhaustive walk of `execution_service/` source tree (~130 files scanned). Tests excluded. Scripts
directory reviewed for bucket violations (2 found).

---

## Findings summary by severity

### P0 — Immediate remediation required

| Finding                                                                                           | Location                                                                                                                                                                                                                                                                                                  | Pattern | Remediation                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **P0-1**: 12 CCXT/sports adapters have `except` blocks with no `classify_venue_error()` call      | `trade_execution/adapters/{binance,hyperliquid,bybit,coinbase,deribit,okx,upbit}_ccxt.py`; `sports_execution/adapters/exchanges/polymarket_clob.py`                                                                                                                                                       | P6      | Add `classify_venue_error(venue, raw_code)` + `ADAPTER_FETCH_FAILED` to each CCXT adapter's except blocks; inherit from `_native_base.py` helper or call directly  |
| **P0-2**: 13 source files construct bucket names as inline f-strings                              | `utils/dependency_checker.py:541,551`; `utils/loader.py`; `utils/io/loader.py`; `data/loader.py`; `data/loader_gcs.py`; `data/loaders/defi.py`; `data/defi_data_loader.py`; `engine/backtest/engine/setup.py`; `cli/multi_leg_config_gcs.py`; `config/grid_generator_v2.py`; `config/grid_v2_registry.py` | P7      | Replace with `resolve_bucket_name(cloud, bucket_type, asset_group, project_id)` from UTL; remove f-string fallbacks                                                |
| **P0-3**: Deribit connector fetches `tick_size`/`contract_size` from live venue API instead of IS | `venues/deribit_orders.py:115-118,505-506`                                                                                                                                                                                                                                                                | P1      | Source `tick_size`/`contract_size` from IS `InstrumentDefinitionsLoader.find_by_instrument_key()` at backtest/paper-trade time; use live API only for live trading |

### P1 — Should fix pre-cutover

| Finding                                                                                                                                                                            | Location                        | Pattern       | Remediation                                                                                                                          |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| **P1-1**: `utils/dependency_checker.py` UPSTREAM_DEPS marks `instruments-service` as `"required": False` for DeFi (comment: "DeFi instruments from config. CeFi needs discovery.") | `dependency_checker.py:224-228` | P1            | DeFi instruments also come from IS as of Phase 2 (IS@919c1e2). This field should be `True` or at minimum conditional on asset_group. |
| **P1-2**: Script-level bucket f-strings (`scripts/run_lending_rate_validation.py:109`, `scripts/run_amm_golden_validation.py:100`)                                                 | `scripts/`                      | P7            | Apply same `resolve_bucket_name()` migration; scripts are under QG via peripheral-scripts rule.                                      |
| **P1-3**: `engine/preflight.py:28` uses internal service URL constant `_RISK_SERVICE_DEFAULT_URL = "http://risk-and-exposure-service:8001"`                                        | `engine/preflight.py`           | P1 (adjacent) | Not an IS violation; internal K8s service URL. Flag for service-mesh config instead.                                                 |

### Verified clean (no violation)

| Pattern                              | Finding                                                                                                   | Evidence                             |
| ------------------------------------ | --------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| P2 — Manifest emission               | N/A — leaf execution service; writes fills, not manifests                                                 | 0 `record_*` hits in non-test source |
| P3 — Schema version                  | N/A — no manifest bucket                                                                                  | (same)                               |
| P4 — Honest-absence reasons          | N/A — leaf execution service                                                                              | (same)                               |
| P5 — expected_coverage preflight     | N/A — execution-service uses `DependencyChecker` preflight, not coverage-formula                          | `backtest_checks.py:48-92`           |
| P6 (native adapters)                 | Native adapters (`_native_base.py`, kraken, bybit, okx, bitget) DO call `classify_venue_error()`          | grep confirmed                       |
| P6 (engine orchestrators)            | `orchestrator.py`, `multi_leg_orchestrator.py`, `instruction_router.py` all call `classify_venue_error()` | grep confirmed                       |
| P6 (sports — main exchanges)         | Kalshi, Betfair, Matchbook, Odds-API all emit `ADAPTER_FETCH_FAILED` + `classify_venue_error()`           | grep confirmed                       |
| IS parquet read (CeFi)               | `InstrumentDefinitionsLoader.load_for_date()` reads IS bucket for CeFi instrument specs                   | `definitions_loader.py:77-96`        |
| IS bucket dependency check           | `DependencyChecker.check_instrument_definitions()` validates IS parquet before backtest                   | `dependency_checker.py:548-591`      |
| `resolve_bucket_name()` in providers | L2 depth, Solana AMM depth, Tenderly budget, audit log all use `resolve_bucket_name()`                    | grep confirmed                       |

---

## A5 known findings reconciliation

From A5 dependency propagation scan (2026-05-20 CSV):

```
execution-service,execution_service/algo_library/deleverage_executor.py,batch_handler,False,0,0,0,0,0,0,0
execution-service,execution_service/v2/handlers.py,batch_handler,False,0,0,0,0,0,0,0
execution-service,tests/unit/defi_execution/test_health_factor_monitor.py,batch_handler,False,0,0,0,0,0,0,0
```

All 3 A5 rows show `review_blocking_violations=0`. No `DependencyError`(fail_fast) or `StaleUpstreamError` issues in
execution-service batch handlers. Clean.

The `DependencyError` the task description referenced as "3 batch handlers raising DependencyError (positive)" maps to
`dependency_checker.py:401` and `:654` — these raise on missing required deps, which IS correct behavior
(`fail_fast=True` semantics). The `StaleUpstreamError` referenced in the task description was NOT found in
execution-service source — this may refer to a different repo or a pre-existing stale citation.

---

## QG-ratchet phase

### Phase Q — QG enforcement gaps for execution-service

| Pattern                                          | QG script                                       | Status in execution-service QG                                                       |
| ------------------------------------------------ | ----------------------------------------------- | ------------------------------------------------------------------------------------ |
| P1 — SSOT URL reference (connectivity constants) | `no_hardcoded_venue_urls.sh`                    | **GAP — not wired in execution-service QG** (wired in IS + MTDS QG only)             |
| P2 — Manifest emission                           | N/A (execution is leaf service)                 | N/A                                                                                  |
| P3 — Schema version                              | N/A                                             | N/A                                                                                  |
| P4 — Honest-absence reasons                      | N/A                                             | N/A                                                                                  |
| P5 — expected_coverage preflight                 | N/A (DependencyChecker is the IS preflight)     | N/A                                                                                  |
| P6 — Error classification                        | `no_adapter_contract_regression.sh` (STEP 5.83) | **WIRED** — `quality-gates.sh:80-85`                                                 |
| P7 — Bucket SSOT                                 | `check_inline_bucket_uri.py` (STEP 5.69)        | **WIRED via base-service.sh** — but pre-existing inline URIs are in ratchet baseline |

**Gap action for P6 CCXT adapters**: STEP 5.83 (`no_adapter_contract_regression.sh`) ratchets on `classify_venue_error`
counts per file. If CCXT adapters never had `classify_venue_error()`, the ratchet floor is 0 — meaning the gap is within
the current ratchet and does not trigger a QG failure. The ratchet must be _lowered_ (adding calls) to enforce
compliance.

**Gap action for P7**: The inline-bucket f-strings predate the `check_inline_bucket_uri.py` ratchet. The ratchet
baseline currently allows them. Fix requires migrating violations AND updating the baseline.

---

## Continuous-verification column

| Pattern                                     | Continuous-verification path                                                  | Cadence        | Last verified                                       |
| ------------------------------------------- | ----------------------------------------------------------------------------- | -------------- | --------------------------------------------------- |
| P1 — IS parquet read (CeFi)                 | `DependencyChecker.check_instrument_definitions()` gates every backtest run   | every backtest | 2026-05-20 (audit grep)                             |
| P6 — Error classification (native adapters) | `no_adapter_contract_regression.sh` (STEP 5.83)                               | every push     | 2026-05-20 (QG wired)                               |
| P6 — Error classification (CCXT gap)        | **NONE** — CCXT adapters not covered by ratchet                               | **GAP**        | —                                                   |
| P7 — Bucket SSOT                            | `check_inline_bucket_uri.py` (STEP 5.69) via base-service.sh                  | every push     | 2026-05-20 (wired; existing violations in baseline) |
| IS dependency check                         | `DependencyChecker.check_instrument_definitions()` in `backtest_checks.py:48` | every backtest | 2026-05-20                                          |

---

## Phased execution DAG

```
Phase 1 — P6 CCXT error classification fix (add classify_venue_error to CCXT adapters)
   │
   ├── Phase 2 — P7 bucket SSOT migration (replace inline f-string bucket names)
   │
   ├── Phase 3 — P0-3 Deribit tick_size from IS (source from IS DataFrame, not live API)
   │
   ├── Phase 4 — P1-1 IS dependency required=True for DeFi in DependencyChecker
   │
   └── Phase Q — QG enforcement (wire CCXT classify_venue_error ratchet floor adjustment)

Phase D — Codex SSOT update after Phase Q
```

**Foundation-completion-gate**: Phases 1-4 are P0/P1 remediation items. They do not block the May-23 DeFi cutover
(execution-service already reads IS for CeFi; DeFi execution uses `InstrumentDefinitionsLoader`). However P6 CCXT gaps
leave order errors unclassified in live trading — high-severity for post-cutover operations.

---

## Scope exclusions

- **P2 (manifest emission)**: execution-service is a leaf execution service — zero manifest writes in source. Verified
  clean; continuous verification: N/A.
- **P3 (schema version)**: same. N/A.
- **P4 (honest-absence reasons)**: same. N/A.
- **P5 (expected_coverage preflight)**: execution-service uses `DependencyChecker` (GCS blob existence check) rather
  than `expected_coverage()`. This is an appropriate pattern for an execution service and is not a violation.
- **Connectivity URL constants** (`_BINANCE_BASE_URL = "https://api.binance.com"` etc.): determined to be in-scope for
  execution adapters — these are stable public endpoints. NOT violations of the IS→execution contract. IS owns
  _instrument reference data_, not _live trading connectivity URLs_.

---

## Temporary states + their canonical follow-up plans

- CCXT adapters lack `classify_venue_error()` — pre-existing since adapter creation. Remediation in Phase 1 of this
  plan. Successor: `is_execution_contract_remediation_2026_05_xx.md` (TBD).
- Inline bucket f-strings in 13 files — pre-existing before STEP 5.69 ratchet. Successor:
  bucket_name_ssot_canonicalisation_2026_05_10.md covers execution-service as in-scope.
- `DependencyChecker.UPSTREAM_DEPS["instruments-service"]["required"] = False` for DeFi — pre-existing design decision.
  Successor: this plan, Phase 4.

---

## Codex SSOT updates required

- `/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`: add section clarifying execution-service IS contract
  (IS owns _instrument specs_, not _connectivity URLs_). Distinguish data-ingestion handlers (MTDS pattern) from
  execution adapters (execution pattern).
- `/codex/04-architecture/defi-execution-overview.md`: note that IS provides tick_size/contract_size for Deribit and
  DeFi instruments; live API fetch is fallback only.

---

## Cross-references

- C2 audit (MTDS): `plans/audit/is_mtds_contract_audit_2026_05_20.md` — completed
- A5 dependency propagation CSV: `plans/audit/results/dependency_propagation_2026_05_20.csv`
- A1 codified shape compliance CSV: `plans/audit/results/codified_shape_compliance_2026_05_20.csv`
- Issue doc (method-size violations):
  `plans/active/issues/execution_service_method_size_violations_workspace_outlier_2026_05_17.md`
- Issue doc (test harness): `plans/active/issues/execution_service_test_harness_missing_methods_2026_05_18.md`
- Bucket SSOT canonicalisation plan: `plans/active/bucket_name_ssot_canonicalisation_2026_05_10.md`
