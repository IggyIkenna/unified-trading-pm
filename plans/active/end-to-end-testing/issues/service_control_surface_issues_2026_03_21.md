---
title: "Service Control Surface — Issues Found During Testing"
created: 2026-03-21
source_session: service_protocol_resolution testing
locked_by: live-defi-rollout
locked_since: 2026-03-21
---

# Service Control Surface — Issues Found During Testing

## Why This List Exists

These issues were discovered while testing `instruments-service` with the new ServiceRuntime control surface. **If one
service has these bugs, other services almost certainly do too.** Every issue here should be audited across all 14+
services and stamped out before they reach staging. Pattern-level bugs propagate — fix them at the root.

---

## Issues

### 1. `load_dotenv(override=True)` defeats command-line env vars

- **Found in:** instruments-service ([main.py:29](../../instruments-service/instruments_service/cli/main.py))
- **Severity:** P1
- **Impact:** `CLOUD_MOCK_MODE=true python -m service.cli` is silently overridden by `.env`'s `CLOUD_MOCK_MODE=false`.
  The operator thinks they're running in mock mode but writes go to real GCS. Dangerous in prod debugging scenarios.
- **Root cause:** `load_dotenv(dotenv_path=_env_path, override=True)` — `override=True` means `.env` wins over shell env
  vars.
- **Fix:** Change to `override=False` in every service entry point. Shell env vars (explicit operator intent) must
  always win over `.env` defaults.
- **Audit scope:** All services that call `load_dotenv`. Search: `rg "load_dotenv.*override" --type py --glob '!.venv*'`
- [x] instruments-service (was only violation — fixed 2026-03-21)
- [x] market-tick-data-service (already override=False or no override kwarg)
- [x] features-onchain-service (already no override kwarg)
- [ ] features-delta-one-service
- [ ] features-volatility-service
- [ ] strategy-service
- [ ] execution-service
- [ ] ml-training-service
- [ ] ml-inference-service
- [ ] pnl-attribution-service
- [ ] position-balance-monitor-service
- [ ] alerting-service
- [ ] risk-and-exposure-service
- [ ] features-calendar-service

### 2. `--dry-run` flag parsed but never enforced

- **Found in:** instruments-service (all 8 BaseModeHandler wrappers)
- **Severity:** P1
- **Impact:** Operator passes `--dry-run` expecting no writes. ServiceCLI puts it in `config["_cli_dry_run"]` and
  `runtime` is constructed, but no handler checks it. GCS writes happen regardless.
- **Root cause:** ServiceCLI framework parses the flag but enforcement is left to handlers. No handler implemented it.
- **Fix options:**
  - **(A) Framework-level guard:** ServiceCLI wraps the DataSink with a no-op sink when `--dry-run` is set. Zero handler
    changes needed.
  - **(B) Handler-level check:** Each handler checks `self.config.get("_cli_dry_run")` before writing. Requires touching
    every handler.
  - **(C) ServiceRuntime property:** `runtime.dry_run` → UCI `get_data_sink()` returns `LocalDataSink()` when
    dry_run=True.
  - **Recommended:** Option A or C — framework-level, not per-handler.
- **Audit scope:** All services using ServiceCLI + `--dry-run`.
- [ ] instruments-service (8 handlers)
- [ ] market-tick-data-service
- [ ] features-onchain-service
- [ ] features-delta-one-service
- [ ] features-volatility-service
- [ ] strategy-service
- [ ] execution-service
- [ ] ml-training-service
- [ ] ml-inference-service

### 3. `.env` contains hardcoded bucket names that should be derived by UCI

- **Found in:** instruments-service (old `.env` had `INSTRUMENTS_GCS_BUCKET_CEFI=...` etc.)
- **Severity:** P2
- **Impact:** Bucket names in `.env` override UCI's `get_bucket_name()` convention. When project ID or environment
  changes, `.env` is stale and writes go to wrong bucket. Also masks bugs in UCI bucket naming.
- **Root cause:** Historical — buckets were configured before UCI had `get_bucket_name()`.
- **Fix:** Remove all `*_GCS_BUCKET_*` env vars from `.env` files. UCI derives them from `CLOUD_PROVIDER` +
  `GCP_PROJECT_ID` + `ENVIRONMENT` + domain.
- **Status:** Fixed in instruments-service. Agent created clean `.env` for 8 more services.
- **Audit scope:** Any `.env` or deployment config with hardcoded bucket names.
- [x] instruments-service (fixed 2026-03-21)
- [x] strategy-service (fixed 2026-03-21)
- [ ] deployment-service (check Terraform/Cloud Build configs)
- [ ] Other services with legacy `.env` files

### 4. `ENVIRONMENT=development` not accepted by UIC `EnvironmentMode`

- **Found in:** instruments-service `.env` had `ENVIRONMENT=development`
- **Severity:** P2 (caught by startup validation — fails loud)
- **Impact:** Service fails to start with `STARTUP_VALIDATION_FAILED: Invalid ENVIRONMENT='development'`. Clear error,
  but frustrating for dev.
- **Root cause:** `EnvironmentMode` only had `dev`/`staging`/`prod`. Real-world `.env` files use the long form
  `development`.
- **Fix:** Added `DEVELOPMENT = "development"` and `PRODUCTION = "production"` to `EnvironmentMode`.
- **Status:** Fixed in UIC modes.py (2026-03-21).
- [x] Fixed

### 5. `TESTNET_MODE=mainnet` rejected by UnifiedCloudConfig (Pydantic `bool` field)

- **Found in:** unified-config-interface `cloud_config.py` — `testnet_mode: bool` field
- **Severity:** P2 (caught by Pydantic — fails loud)
- **Impact:** Service fails to start when `.env` has `TESTNET_MODE=mainnet` because Pydantic can't parse `"mainnet"` as
  bool.
- **Root cause:** Config field was `bool` but the canonical UIC schema is `TestnetMode` (mainnet/testnet string enum).
  Mismatch between config-interface and contracts.
- **Fix:** Added `_parse_testnet_mode` field validator to `cloud_config.py` accepting both `bool` and `str` values.
- **Status:** Fixed in unified-config-interface (2026-03-21).
- **Follow-up:** Long-term, change the field type from `bool` to `str` and use `TestnetMode` enum. This is a breaking
  change for any code that does `if config.testnet_mode:` (bool truthy check).
- [x] Fixed (validator added)
- [ ] Long-term: migrate field type to `TestnetMode` str enum

### 6. Asyncio nesting — `asyncio.run()` inside `async def run()`

- **Found in:** instruments-service `instrument_handler.py:320`, `live_mode_handler.py:83`
- **Severity:** P1
- **Impact:** Service crashes with `RuntimeError: asyncio.run() cannot be called from a running event loop` when invoked
  via ServiceCLI (which wraps handlers in `asyncio.run()`).
- **Root cause:** Inner handlers are sync methods that call `asyncio.run()` for async operations. When ServiceCLI wraps
  the outer `async def run()` in `asyncio.run()`, the inner call is nested.
- **Fix:** `_run_sync_handler_in_thread()` runs sync handlers in a `ThreadPoolExecutor`, giving them their own event
  loop.
- **Status:** Fixed in instruments-service (2026-03-21) — all 8 handlers updated.
- **Audit scope:** Any service where `BaseModeHandler.run()` calls sync code that internally uses `asyncio.run()`.
- [x] instruments-service (fixed 2026-03-21)
- [ ] market-tick-data-service (known issue from prior session — `DownloadOperation` uses `run_in_executor`)
- [ ] Other services with async/sync boundary in handlers

### 8. PREDICTION category falls through to all categories

- **Found in:** instruments-service category sweep
- **Severity:** P1
- **Impact:** `--category PREDICTION` processes all CeFi+TradFi+DeFi instruments instead of PREDICTION-specific
  instruments. The handler uses boolean flags (`cefi=True/False`) and PREDICTION has no corresponding flag, so when none
  are set the service defaults to "process everything".
- **Root cause:** `_resolve_categories()` maps category strings to lowercase booleans (`config["cefi"] = True`).
  PREDICTION is not in the map, so all booleans stay False, and the handler interprets all-False as "process all".
- **Fix:** Add `prediction` boolean to the handler, or refactor to use `MarketCategory` enum directly instead of loose
  booleans.
- **Audit scope:** Any service that uses boolean category flags instead of the enum.
- [ ] instruments-service
- [ ] market-tick-data-service
- [ ] features-onchain-service

### 9. SPORTS category resolves to 0 venues in instruments-service

- **Found in:** instruments-service category sweep
- **Severity:** P2
- **Impact:** `--category SPORTS` produces no instruments. "No API keys required for requested venues" + "Validated API
  keys for 0 venues". The sports instrument adapters (sportsbook reference data) may not be wired into the instrument
  handler's venue resolution.
- **Root cause:** The instruments handler uses Tardis/CCXT venue lists for CeFi and specific TradFi adapters. SPORTS
  venues (Pinnacle, Betfair, etc.) use unified-sports-reference-interface (USRI) which has a separate integration path
  via the `sports` boolean flag, but it may not be routing to any actual data fetch.
- **Fix:** Verify sports instruments are generated by a separate code path (USRI adapter) and that `sports=True`
  triggers it.
- [ ] instruments-service

### 13. Expired instruments not filtered — 355K dead options in 360K Deribit total

- **Found in:** instruments-service CEFI category — Deribit had 359,811 instruments but only 4,004 are active
- **Severity:** P0 (data quality — 99% of Deribit data is expired garbage)
- **Impact:** Every downstream service (market-tick-data, features, strategy) processes 355K dead instruments. Wastes
  compute, storage, and creates false instrument counts.
- **Root cause:** Two case-mismatch bugs:
  1. `_is_past_expiry()` checks `normalized_instrument_type in ["FUTURE", "OPTION"]` (uppercase) but the actual values
     from Tardis are lowercase (`"future"`, `"option"`, `"spread"`). Filter never triggers.
  2. `_resolve_available_to()` also has the same uppercase check, so `available_to_datetime` is never populated from
     `expiry` for expired instruments.
- **Fix:** `.upper()` on the comparison: `(normalized_instrument_type or "").upper() in ("FUTURE", "OPTION", "SPREAD")`.
  Applied in both `instrument_processing_handlers.py` and `cefi_processor.py`.
- **Verification:** Re-run CEFI for 1 day, expect ~4K Deribit instruments (not 360K).
- [x] instruments-service URDI path (fixed 2026-03-21 — `instrument_sync.py`)
- [x] instruments-service cefi_processor.py (fixed 2026-03-21 — case comparison)
- [x] instruments-service cefi_orchestration.py (fixed 2026-03-21 — `_filter_expired_instruments`)
- [x] instruments-service Databento URDI path (fixed 2026-03-21)
- [x] **Verified**: CEFI 27,989 (was 389,245), TRADFI 887,276 (was 1,212,352)

### 14. CME options classified as `spot` instead of `option` (711K instruments)

- **Found in:** instruments-service TRADFI category — CME data analysis
- **Severity:** P1 (data quality — affects downstream filtering)
- **Impact:** 711,291 CME options have `instrument_type=spot` instead of `option`. Symbols clearly show Call/Put +
  Strike (e.g. `COOX7 C1450`, `2MGJ6 P5150`). Downstream services filtering by instrument_type will miss these or
  misclassify them.
- **Root cause:** Databento URDI adapter (`DatabentoReferenceDataAdapter`) doesn't normalize `instrument_type` correctly
  for CME options. The raw Databento `rtype` field maps to `spot` when it should detect Call/Put patterns in the symbol.
- **Verification:** 767K CME total. 55,852 correctly as `future`. 711,291 wrong as `spot` (should be `option`).
- **Fix:** In the URDI Databento adapter, detect option patterns in the symbol (contains ` C` or ` P` followed by
  strike) and classify as `option`. Or use Databento's `instrument_class` field if available.
- **Note:** The 767K count is real — CME genuinely has this many active options. Not an expiry filter issue.
- [ ] unified-reference-data-interface Databento adapter

### 11. DeFi instruments written to CEFI bucket instead of DEFI bucket

- **Found in:** instruments-service DEFI category E2E test
- **Severity:** P1
- **Impact:** DeFi instruments (Aave, Uniswap, Curve etc.) are uploaded to
  `instruments-store-cefi-central-element-323112` instead of `instruments-store-defi-central-element-323112`. Data lands
  in wrong bucket. Downstream services reading from DEFI bucket get nothing.
- **Root cause:** The DeFi processor stores instruments with `category_str="CEFI"` instead of `"DEFI"`. The venue names
  like `AAVEV3-ETHEREUM` are being classified as CEFI in the storage layer. The `market_category` field in the DataFrame
  needs to be populated correctly before the storage write.
- **Fix:** Trace the market_category assignment in the DeFi processor. Ensure DeFi instruments have
  `market_category=DEFI` before `_upload_venue_to_datasink()` is called.
- [ ] instruments-service DeFi processor

### 12. USRI not installed in instruments-service venv

- **Found in:** instruments-service SPORTS category E2E test
- **Severity:** P1
- **Impact:** `No module named 'unified_sports_reference_interface'` — SPORTS instruments can't be generated. The
  SportsOrchestrator imports USRI which isn't in the service's venv.
- **Fix:** `uv pip install -e ../unified-sports-reference-interface/ --python .venv/bin/python`
- **Follow-up:** Check if USRI is in instruments-service's `pyproject.toml` dependencies.
- [ ] instruments-service

### 10. instruments-service `instruments` operation: GCS per-venue writes may not be landing

- **Found in:** instruments-service Phase 3 real write test
- **Severity:** P1
- **Impact:** The `instruments` operation fetches from 19 CeFi exchanges, generates CSV samples (confirmed 100 rows),
  but **0 new files appeared in GCS in the last hour** after the run. The GCS CEFI bucket has only 4 files total (2
  aggregated, 1 instrument_definitions, 1 live). Either per-venue per-date parquet writes are routing to a wrong path,
  or the write is silently failing without error.
- **Root cause:** Under investigation. Need to trace `CloudInstrumentStorage` write path and check if dry-run flag
  leaked or if the storage handler is broken.
- **Evidence:** CSV sample at `data/samples/instruments_20260321_20260321_160557.csv` has 100 rows of valid BINANCE-SPOT
  data. GCS bucket `instruments-store-cefi-central-element-323112` has 0 files modified in last hour.
- **Next step:** Trace the write path from `generate_instruments_for_date()` → storage handler. Check if `skip_storage`
  is being set. Check if dry-run mode leaked from previous test.
- [ ] Investigate write path
- [ ] Verify with explicit `--force` flag
- [ ] Confirm parquet files land in expected GCS path

### 7. `.env` contains raw API keys

- **Found in:** instruments-service old `.env` had `DATABENTO_API_KEY=db-cyWEG...`
- **Severity:** P0 (security)
- **Impact:** API key in plaintext in a file that could accidentally be committed. Even though `.gitignore` protects it,
  `.env` files get copied, shared, and end up in screenshots/logs.
- **Root cause:** Historical — keys were put in `.env` before Secret Manager was wired.
- **Fix:** Only Secret Manager reference names in `.env` (e.g. `DATABENTO_SECRET_NAME=databento-api-key`). Actual keys
  fetched at runtime from SM.
- **Status:** Fixed in instruments-service and 8 other services (2026-03-21).
- **Audit scope:** All `.env` files and `.env.example` templates.
- [x] instruments-service (fixed 2026-03-21)
- [x] 8 other services (agent-created clean `.env` files)
- [ ] deployment-service
- [ ] unified-trading-library
