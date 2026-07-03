---
doc_type: plan
title: mock-data-dev-project-seeding-2026-03-10
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [system-integration-tests, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
overview: Create a systematic seeded dataset covering all 4 asset classes with schema-validated synthetic data so any developer gets a complete GCP dev environment within 5 minutes, zero live API calls.
type: infra
epic: epic-infra
completion_gates: {code: C5, deployment: none, business: none}
repo_gates:
- {repo: unified-trading-pm, code: C3, deployment: none, business: none, readiness_note: 'DR N/A: local developer tooling — no cloud deployment required. BR N/A: internal tooling, no commercial KPI.'}
- {repo: system-integration-tests, code: C1, deployment: none, business: none, readiness_note: 'DR N/A: local developer tooling — no cloud deployment required. BR N/A: internal tooling, no commercial KPI.'}
depends_on: [api_keys_and_auth, dev_environment_automated_onboarding_2026_03_10]
todos:
- {id: p0-seed-spec, content: Create unified-trading-pm/scripts/dev/fixtures/seed_spec.yaml, status: done, note: DONE 2026-03-11}
- {id: p0-data-format-validation, content: 'Define Parquet format, UTC timestamps, UAC schema requirements for seed data', status: done, note: DONE 2026-03-11}
- {id: p1-generator, content: 'Create generate_synthetic_data.py with GBM price series, DeFi yields, sports odds', status: done, note: DONE 2026-03-11}
- {id: p1-instruments-seeder, content: Create seed_instruments.py for 100 instruments across all asset classes, status: done, note: DONE 2026-03-11}
- {id: p2-seed-script, content: Create seed-dev-project.sh orchestrating all seed steps, status: done, note: DONE 2026-03-11}
- {id: p2-feature-seeder, content: Create seed_features.py running all 8 feature services in batch mode, status: done, note: DONE 2026-03-11}
- {id: p2-ml-artifact-seeder, content: Create seed_ml_artifacts.py for lightweight model artifacts, status: done, note: DONE 2026-03-11}
- {id: p3-pubsub-setup, content: Create setup-dev-pubsub.sh for all Pub/Sub topics and subscriptions in unified-trading-dev, status: todo, note: ''}
- {id: p3-bigquery-setup, content: Create setup-dev-bigquery.sh with correct schemas for all dev tables, status: todo, note: ''}
- {id: p4-seed-validator, content: Create seed_validator.py for UAC/UIC schema validation of all seed data, status: done, note: DONE 2026-03-11}
- {id: p4-ci-seed-check, content: Add nightly SIT CI check for dev seed data freshness and schema validity, status: todo, note: ''}
isProject: false
---

# Plan: Mock Data Dev Project Seeding (No Prod APIs)

## Context

Services can run in `CLOUD_MOCK_MODE=true` (no real GCS) or with VCR cassettes (no live API calls). However, no
systematic seeded dataset exists that: (a) covers all 4 asset classes (CeFi, DeFi, TradFi, Sports), (b) spans enough
history to test feature pipelines (1 year minimum), (c) is schema-validated against UAC/UIC, (d) is committed/scripted
so any developer gets a complete system immediately. VCR cassettes from `api_keys_and_auth.md` cover real-time venue
calls. This plan covers the batch/historical layer. Goal: `bash seed-dev-project.sh --quick` gives any developer a
complete, schema-valid dataset in the GCP dev project within 5 minutes, zero live API calls.

---

## Phase 0: Define seed data spec

### P0.1 — Seed spec file ✅ DONE 2026-03-11

File: `unified-trading-pm/scripts/dev/fixtures/seed_spec.yaml`

```yaml
date_range:
  start: "2024-01-01"
  end: "2025-01-01" # 1 year

instruments:
  crypto_cefi:
    - { symbol: "BTC/USDT", venue: binance, interval: 1m }
    - { symbol: "ETH/USDT", venue: binance, interval: 1m }
    - { symbol: "SOL/USDT", venue: binance, interval: 1m }
    - { symbol: "BTC-PERP", venue: deribit, interval: 1m }
    - { symbol: "ETH-PERP", venue: deribit, interval: 1m }
  crypto_defi:
    - { protocol: uniswap_v3, pair: "ETH/USDC", interval: 5m, chain: ethereum }
    - { protocol: aave_v3, asset: USDC, interval: 1h, chain: ethereum }
    - { protocol: curve, pool: 3pool, interval: 1h, chain: ethereum }
    - { protocol: lido, asset: stETH, interval: 1h, chain: ethereum }
  tradfi:
    - { symbol: SPY, venue: databento, interval: 1d }
    - { symbol: QQQ, venue: databento, interval: 1d }
    - { symbol: AAPL, venue: databento, interval: 1d }
    - { symbol: TSLA, venue: databento, interval: 1d }
    - { symbol: GLD, venue: databento, interval: 1d }
  sports:
    - { league: premier_league, venue: pinnacle, type: match_odds }
    - { league: nba, venue: odds_api, type: moneyline }

instruments_total: 100 # across all asset classes

modes:
  quick: # fast dev start (1 month, 5 symbols)
    date_range_override: "2024-12-01 to 2025-01-01"
    symbols_override: [BTC/USDT, ETH/USDT, SPY, ETH/USDC, premier_league]
  full: # complete (1 year, all symbols above)
    date_range_override: null
    symbols_override: null
```

### P0.2 — Data format validation ✅ DONE 2026-03-11

All seed data must:

- Pass UAC schema validation: `CanonicalOHLCV`, `CanonicalTick`, `CanonicalMatchOdds`
- Use UTC timestamps throughout
- Include all required fields with correct types
- Parquet format, partitioned by `{symbol}/{YYYY}/{MM}/{DD}/`

---

## Phase 1: Synthetic data generator

### P1.1 — Generator script ✅ DONE 2026-03-11

File: `unified-trading-pm/scripts/dev/generate_synthetic_data.py`

Generates realistic (not random) synthetic OHLCV using Geometric Brownian Motion:

```python
class SyntheticDataGenerator:
    """
    Generates realistic price series with:
    - GBM drift + volatility calibrated per asset (BTC: vol=0.8, drift=0.0; SPY: vol=0.18, drift=0.12)
    - Realistic volume profiles (higher at open/close, lower at lunch)
    - BTC/ETH/SOL correlations preserved (rho_btc_eth=0.85, rho_btc_sol=0.75)
    - DeFi APY series: mean-reverting around realistic long-run values
    - Sports odds: realistic pre-match → in-play movement profiles
    - All output validates against UAC schemas before writing
    """
    def generate_ohlcv(self, symbol: str, start: date, end: date, interval: str) -> pd.DataFrame: ...
    def generate_defi_yields(self, protocol: str, asset: str, ...) -> pd.DataFrame: ...
    def generate_match_odds(self, league: str, ...) -> pd.DataFrame: ...
```

### P1.2 — Instruments metadata seeder ✅ DONE 2026-03-11

File: `unified-trading-pm/scripts/dev/seed_instruments.py`

Creates `instruments.json` with 100 instruments:

- 30 crypto CeFi (top coins × 3 venues)
- 20 crypto DeFi (LP pairs, lending pools)
- 30 TradFi (US equities, bonds, commodities, FX)
- 20 Sports (leagues × team matchups)

All validated against UIC `InstrumentSchema` before writing.

---

## Phase 2: GCS seed script

### P2.1 — Main seed script ✅ DONE 2026-03-11

File: `unified-trading-pm/scripts/dev/seed-dev-project.sh`

```bash
#!/usr/bin/env bash
# Usage: seed-dev-project.sh [--quick|--full] [--dry-run]
# Requires: GOOGLE_APPLICATION_CREDENTIALS pointing to unified-trading-dev SA key

MODE="${1:-quick}"
DRY_RUN="${2:-}"

step() { echo "==> $1"; }

step "Generating synthetic data (mode=$MODE)"
python scripts/dev/generate_synthetic_data.py --mode "$MODE" --output /tmp/seed_data/

step "Validating generated data against UAC schemas"
python scripts/dev/seed_validator.py /tmp/seed_data/ --strict

step "Seeding instruments metadata"
python scripts/dev/seed_instruments.py --project unified-trading-dev $DRY_RUN

step "Uploading tick data to GCS"
# gs://unified-trading-dev-tick-data/{venue}/{symbol}/YYYY/MM/DD/*.parquet
gsutil -m cp -r /tmp/seed_data/tick/ gs://unified-trading-dev-tick-data/ $DRY_RUN

step "Pre-computing and uploading features"
python scripts/dev/seed_features.py --mode "$MODE" --project unified-trading-dev $DRY_RUN

step "Seeding ML model artifacts"
python scripts/dev/seed_ml_artifacts.py --project unified-trading-dev $DRY_RUN

step "Done. Seed data available in unified-trading-dev project."
```

### P2.2 — Feature seeder ✅ DONE 2026-03-11

File: `unified-trading-pm/scripts/dev/seed_features.py`

Runs all 8 feature services in batch mode against synthetic tick data, writes to dev GCS. This is faster than running
feature services live — pre-computed fixtures.

Sequence:

1. Run `features-delta-one`, `features-volatility`, `features-calendar`, `features-onchain` in parallel
2. Run `features-cross-instrument`, `features-commodity` in parallel
3. Run `features-multi-timeframe` (depends on above)

### P2.3 — ML artifact seeder ✅ DONE 2026-03-11

File: `unified-trading-pm/scripts/dev/seed_ml_artifacts.py`

Creates lightweight model artifacts (fast to load, not for real trading):

- Logistic regression model for each strategy (small, fast inference)
- Pre-fitted scaler for each feature service
- Versioned: `gs://unified-trading-dev-models/v{version}/`

---

## Phase 3: Pub/Sub and BigQuery dev setup

### P3.1 — Pub/Sub setup

File: `unified-trading-pm/scripts/dev/setup-dev-pubsub.sh`

Creates all Pub/Sub topics and subscriptions in `unified-trading-dev`:

- Reads topic/subscription names from `unified-trading-pm/configs/runtime-topology.yaml`
- Adds `-dev` suffix to distinguish from production
- Retention: 7 days (vs 30 days in prod)
- Idempotent: skip if already exists

### P3.2 — BigQuery dev setup

File: `unified-trading-pm/scripts/dev/setup-dev-bigquery.sh`

Creates BigQuery dataset + tables with correct schemas:

- `unified_trading_dev.pnl_attribution` — empty, schema-correct
- `unified_trading_dev.order_history` — empty
- `unified_trading_dev.position_snapshots` — empty
- `unified_trading_dev.signal_history` — minimal seed data for dashboard testing

---

## Phase 4: Schema validation

### P4.1 — Seed validator ✅ DONE 2026-03-11

File: `unified-trading-pm/scripts/dev/seed_validator.py`

```python
def validate_seed_data(data_dir: str, strict: bool = True) -> ValidationReport:
    """
    For each file in data_dir:
    - Parse Parquet
    - Validate against UAC/UIC schema (CanonicalOHLCV, CanonicalTick, etc.)
    - Check: no NaN in required fields, timestamps in UTC, symbol format correct
    Returns: ValidationReport with pass/fail per file, row counts, date range
    """
```

### P4.2 — CI seed check

Add to SIT CI workflow: nightly check that dev seed data is present and schema-valid. Alert if seed data is stale (>30
days since last refresh).

---

## Verification Gates

- [ ] `bash seed-dev-project.sh --quick` completes in <5 minutes
- [ ] `bash seed-dev-project.sh --full` completes in <30 minutes
- [ ] `seed_validator.py` — all files pass schema validation
- [ ] Portable backtests from `e2e_smoke_and_portable_backtests` pass on seeded dev data
- [ ] Zero live API calls during seeding (all synthetic)
- [ ] `instruments.json` contains exactly 100 instruments, all schema-valid

## Files Created

- `unified-trading-pm/scripts/dev/generate_synthetic_data.py` (new)
- `unified-trading-pm/scripts/dev/seed-dev-project.sh` (new)
- `unified-trading-pm/scripts/dev/seed_instruments.py` (new)
- `unified-trading-pm/scripts/dev/seed_features.py` (new)
- `unified-trading-pm/scripts/dev/seed_ml_artifacts.py` (new)
- `unified-trading-pm/scripts/dev/setup-dev-pubsub.sh` (new)
- `unified-trading-pm/scripts/dev/setup-dev-bigquery.sh` (new)
- `unified-trading-pm/scripts/dev/fixtures/seed_spec.yaml` (new)
- `unified-trading-pm/scripts/dev/seed_validator.py` (new)
- `system-integration-tests/tests/fixtures/seed_validator_sit.py` (new — SIT integration)

## Dependencies

- `unified-api-contracts` (schemas for validation — already exists)
- `api_keys_and_auth.md` (VCR cassettes complement seeded data for live data layer)
- `dev_environment_automated_onboarding_2026_03_10.md` (setup-dev-environment.sh calls this)
