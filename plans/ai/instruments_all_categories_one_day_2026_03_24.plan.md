# AI-GENERATED — awaiting user review and promotion

---

type: code epic: epic-code-completion completion_gates: code: C5 deployment: D3 business: B1

repo_gates:

- repo: instruments-service code: C2 notes: "Core fixes in progress; SPORTS/TRADFI need API key provisioning"
- repo: unified-cloud-interface code: C1 notes: "catalogue.py blob_path fix needed"
- repo: unified-reference-data-interface code: C1 notes: "Binance canonical venue names fixed; other adapters need
  review"
- repo: unified-trading-library code: C1 notes: "GcsEventSink datetime serialization fixed"
- repo: deployment-service code: C0 notes: "Prediction bucket created manually; needs terraform/lifecycle update"

---

## Objective

Get all 5 instrument categories (DEFI, CEFI, TRADFI, SPORTS, PREDICTION) writing correct instrument records to their
respective GCS buckets for a single requested date. Target:
`instruments_service --operation instruments --mode batch --category {X} --date 2026-03-22` produces correct,
date-filtered instrument records with no data quality issues.

## Status per Category (as of 2026-03-24 live run)

| Category   | Status         | Records                | Root Cause                                                                    |
| ---------- | -------------- | ---------------------- | ----------------------------------------------------------------------------- |
| DEFI       | ⚠️ Partial     | 464 (8/12 venues)      | Uniswap/Aave need The Graph API key injection to URDI capability registry     |
| CEFI       | ⚠️ Count wrong | 374,802 → ~3k expected | Fixed: date filtering now applied; also Coinbase goes direct not via Tardis   |
| TRADFI     | ❌ 0           | 0 (shard fail)         | Databento key exists but CLI was crashing with datetime error (fixed)         |
| SPORTS     | ❌ 0           | 0 (shard fail)         | Betfair/API Football API keys not injected to URDI                            |
| PREDICTION | ❌ 0           | no venues              | get_venues_for_categories has no PREDICTION branch (user handling separately) |

## Fixes Applied (do not redo)

- ✅ `unified-cloud-interface/catalogue.py` — `path=` → `blob_path=` in `upload_bytes()`
- ✅ `instruments-service/engine/orchestrator.py` — category-specific bucket routing via UCI
- ✅ `instruments-service/engine/orchestrator.py` — date filtering via `filter_instruments_by_date()`
- ✅ `instruments-service/scripts/run_local.sh` — stale private function names
- ✅ `unified-trading-library/event_sink.py` — `default=str` on all `json.dumps()` calls
- ✅ `unified-reference-data-interface/adapters/binance.py` — `BINANCE-SPOT`/`BINANCE-FUTURES` per instrument type
- ✅ `gs://instruments-store-prediction-central-element-323112` — bucket created
- ✅ `deployment-service/scripts/setup-gcs-lifecycle-policies.sh` — sports + prediction added

## Remaining Work Items

### 1. CEFI — Coinbase goes direct, not via Tardis

`COINBASE-SPOT` adapter in URDI calls `https://api.coinbase.com/api/v3/brokerage/products` directly, returning 401
Unauthorized. But `ADAPTER_DATA_SOURCES["coinbase"] = "tardis"`, implying it SHOULD use Tardis. The adapter class
(`BinanceCoinbaseReferenceDataAdapter` or similar) is inconsistent.

**Action:** Check URDI `adapters/coinbase.py` — if Coinbase instruments are available via Tardis, replace the direct API
call with a Tardis fetch. If Coinbase requires direct API, provision `coinbase-api-key` in Secret Manager and add to UAC
`DATA_SOURCE_TO_SECRET`.

**File:** `unified-reference-data-interface/adapters/coinbase.py`

### 2. DEFI — Uniswap/Aave return 0 despite The Graph key existing

The URDI capability registry marks these venues as `refdata_preflight_skip`. The `graph-api-key` secret exists in Secret
Manager and is fetched by `validate_api_keys_for_venues()`. But the key doesn't reach the Uniswap/Aave adapters because
the capability registry pre-filters them.

**Action:** Update URDI's capability registry to mark uniswap_v2, uniswap_v3, uniswap_v4, aave_v3 as capable (i.e.
remove the `refdata_preflight_skip`).

**File:** `unified-reference-data-interface/factory.py` (capability registry section)

### 3. TRADFI — Verify after datetime fix

TradFi venues (CME, CBOE, NASDAQ, NYSE, ICE, FX) all use `databento-api-key` which exists in Secret Manager. The CLI
path was previously crashing with "datetime not JSON serializable" before process() could run. Now that GcsEventSink is
fixed, rerun:

```bash
IS_TEST_RUN=true bash scripts/run_local.sh TRADFI 2026-03-22
```

Expected: Databento fetches thousands of tradfi instrument definitions.

### 4. SPORTS — API key provisioning via URDI

`betfair-api-key` and `betfair-app-key` exist in Secret Manager (as `betfair-api-key`, `betfair-app-key`,
`BETFAIR_APP_KEY` — three formats; canonical is `betfair-api-key`). `api-football-api-key` also exists.

UAC `DATA_SOURCE_TO_SECRET` already has `'betfair': 'betfair-api-key'` and `'api_football': 'api-football-api-key'`. The
keys should flow through `validate_api_keys_for_venues()` → URDI adapters automatically.

**Verify:** Does `betfair-api-key` work for historical fixture data? Betfair uses session tokens (OAuth), not a simple
API key. Betfair's `betfair-api-key`, `betfair-username`, `BETFAIR_APP_KEY` may all be needed together. The URDI betfair
adapter needs to handle multi-credential authentication.

**File:** `unified-reference-data-interface/adapters/betfair.py`

### 5. API Keys via Hot-Reload Config (architectural improvement)

Currently, API keys are fetched from Secret Manager once in `preflight()` via `validate_api_keys_for_venues()`. To
support key rotation without service restart, consider moving API key caching to UTL's `DomainConfigReloader` pattern:

- Keys are read from ConfigStore (GCS YAML) not Secret Manager at startup
- Secret Manager remains the source of truth; the YAML is populated by a bootstrap script
- When keys rotate, the ConfigStore YAML is updated → DomainConfigReloader picks up change → service uses new key on
  next cycle

This is an architectural improvement, not a blocking fix. Add `api_keys_bucket: str` to `InstrumentsServiceConfig`
alongside `config_store_bucket`.

### 6. CEFI — Other adapter canonical names

After the Binance fix, check other CEFI adapters for the same `venue = "lowercase"` issue:

- `bybit.py` → `BybttReferenceDataAdapter.venue` should be `"BYBIT"` / `"BYBIT-FUTURES"`
- `okx.py` → `venue` should be `"OKX"` etc.
- `deribit.py` → `"DERIBIT"`

Pattern: any adapter where `venue` property returns lowercase is a bug.

### 7. PREDICTION — Stub (user handling separately)

User is adding PREDICTION venue stubs to `get_venues_for_categories`. Once that's done, the URDI Polymarket adapter
(`CANONICAL_VENUE_TO_ADAPTER["POLYMARKET"] = "polymarket"`) should handle prediction market instruments.
`polymarket-api-key` exists in Secret Manager. `odds-api-key` should be added to UAC `DATA_SOURCE_TO_SECRET` for
Prediction.

### 8. QG Integration Test — Secret Manager Key Names

See `plans/ai/secret_manager_key_registry_qg_2026_03_24.plan.md` for the plan to add a QG check that verifies
`DATA_SOURCE_TO_SECRET` names exist in Secret Manager.

## Expected Output After All Fixes

```
DEFI:        ~600 instruments   (Morpho, Balancer, Curve, + Uniswap/Aave with Graph key)
CEFI:        ~8,000 instruments (filtered by active_on_date; not 374k all-time)
TRADFI:      ~5,000 instruments (Databento: CME, CBOE, NYSE, NASDAQ, ICE, FX)
SPORTS:      ~1,000 instruments (fixtures for date from API Football + Betfair markets)
PREDICTION:  ~500 instruments   (Polymarket active markets for date)
```

Each category writes to its own GCS bucket:

```
gs://instruments-store-defi-central-element-323112/instrument_availability/by_date/day=2026-03-22/
gs://instruments-store-cefi-central-element-323112/...
gs://instruments-store-tradfi-central-element-323112/...
gs://instruments-store-sports-central-element-323112/...
gs://instruments-store-prediction-central-element-323112/...
```

## Unit Tests Added

Three organized sections in `tests/unit/test_new_orchestrator.py`:

**DATE FILTERING** (6 tests)

- `test_date_filter_keeps_always_active_instrument`
- `test_date_filter_keeps_instrument_active_on_date`
- `test_date_filter_removes_instrument_listed_after_requested_date`
- `test_date_filter_removes_instrument_delisted_before_requested_date`
- `test_date_filter_bulk_reduction` — simulates Bitstamp 365k → few active
- `test_date_filter_on_exact_boundaries`

**BUCKET NAMES PER CATEGORY** (5 tests)

- DEFI, CEFI, PREDICTION category-specific bucket names
- IS_TEST_RUN=true routes to test bucket with category prefix
- No-category fallback to flat bucket

**VENUE NAME CANONICALIZATION** (2 tests)

- `test_process_instruments_uses_primary_category_for_bucket`
- `test_filter_instruments_by_date_preserves_record_integrity`
