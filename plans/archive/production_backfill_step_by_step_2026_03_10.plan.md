---
doc_type: plan
title: production-backfill-step-by-step-2026-03-10
summary:
status: superseded
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [execution-service, instruments-service, market-data-processing-service, market-tick-data-service, system-integration-tests, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-10'
overview: Define the exact 5-step sequenced backfill runbook (instruments → tick data → features → ML training → validation backtest) with gate scripts at each step and recovery procedures, must complete before live trading week 2026-03-20.
type: infra
epic: epic-infra
superseded_by: defi_keys_data_integration_2026_03_13
superseded_date: 2026-03-13
completion_gates: {code: C5, deployment: D3, business: none}
repo_gates:
- {repo: unified-trading-pm, code: C0, deployment: none, business: none, readiness_note: 'C0: not started. DR N/A: local runbook scripts and gate tooling only — cloud deployment readiness tracked at plan completion_gates level (D3). BR N/A: infrastructure runbook plan, no commercial KPI.'}
depends_on: [cloud_infra_bucket_auth_2026_03_10, api_keys_and_auth, phase3_service_hardening_integration]
isProject: false
---

# Plan: Production Backfill — Step-by-Step Runbook

status: superseded superseded_by: defi_keys_data_integration_2026_03_13 superseded_date: 2026-03-13

## Context

Before live trading begins, production GCP needs: complete instruments metadata, ≥1 year of historical tick data per
venue/symbol, pre-computed historical features for model training, trained ML models, and portable backtest validation.
Four individual backfill scripts exist but they are not sequenced or validated as a pipeline. An incorrect sequence
(features before instruments) produces silent garbage. This plan defines the exact execution sequence, validation gates
at each step, and recovery procedures.

---

## Pre-conditions (must ALL pass before starting backfill)

- [ ] All GCS buckets provisioned (`cloud_infra_bucket_auth_2026_03_10` plan complete)
- [ ] All Secret Manager secrets loaded (`api_keys_and_auth` plan complete, all phases)
- [ ] All services deployed to Cloud Run (`phase3_service_hardening` plan complete)
- [ ] API keys valid: run `python unified-trading-pm/scripts/ops/test-all-api-keys.py`
- [ ] Circuit breakers CLOSED for all venues
- [ ] `instruments_service` importable and healthy:
      `python -c "from instruments_service import health_check; health_check()"`

---

## Step 1: Instruments backfill

**Gate: must complete before ANY other step.**

### 1a — Crypto CeFi instruments

```bash
cd instruments-service
.venv/bin/python -m instruments_service \
  --mode batch --task backfill-instruments \
  --asset-classes crypto_cefi \
  --from 2020-01-01 --to $(date +%Y-%m-%d)
```

Verify: `gs://unified-trading-prod-instruments/crypto_cefi/instruments.json` exists, row count >1000

### 1b — TradFi instruments

```bash
.venv/bin/python -m instruments_service \
  --mode batch --task backfill-instruments \
  --asset-classes tradfi --from 2020-01-01
```

Verify: equities (US, EU, APAC), bonds, commodities, FX pairs all present

### 1c — DeFi instruments

```bash
.venv/bin/python -m instruments_service \
  --mode batch --task backfill-instruments \
  --asset-classes defi \
  --chains ethereum,arbitrum,base,polygon,solana
```

Verify: token metadata + LP positions for all 14 supported protocols present

### 1d — Sports instruments

```bash
.venv/bin/python -m instruments_service \
  --mode batch --task backfill-instruments \
  --asset-classes sports \
  --leagues premier_league,nba,nfl,nhl,mlb
```

### 1e — Corporate actions (TradFi)

```bash
.venv/bin/python -m instruments_service \
  --mode batch --task corporate-actions-backfill --from 2020-01-01
```

### 1f — Date views

```bash
.venv/bin/python -m instruments_service \
  --mode batch --task generate-date-views
```

**Gate script:**

```bash
python unified-trading-pm/scripts/ops/validate-instruments-completeness.py
# Must print: PASS — all asset classes present, count within expected range
```

---

## Step 2: Market tick data backfill (in priority order)

**Dependency: Step 1 gate must pass.** **Estimated time: 48–72 hours total (API rate limits dominate).**

### 2a — Priority 1: CeFi tick data

```bash
cd market-tick-data-service

# Tardis — crypto historical tick data
.venv/bin/python -m market_tick_data_service --mode batch \
  --source tardis \
  --symbols BTC-PERP,ETH-PERP,SOL-PERP,BTC/USDT,ETH/USDT,SOL/USDT,BTC/ETH \
  --venues binance,bybit,okx,deribit \
  --from 2023-01-01 --interval 1m
```

### 2b — Priority 2: TradFi

```bash
.venv/bin/python -m market_tick_data_service --mode batch \
  --source databento \
  --symbols SPY,QQQ,AAPL,TSLA,NVDA,GLD,TLT,VIX,DXY,MSFT,AMZN,META,GOOGL \
  --from 2020-01-01 --interval 1d
```

### 2c — Priority 3: DeFi onchain

```bash
# TheGraph — DEX/lending protocol data
.venv/bin/python -m market_tick_data_service --mode batch \
  --source thegraph \
  --protocols uniswap_v3,aave_v3,curve,balancer \
  --chains ethereum,arbitrum,base \
  --from 2022-01-01 --interval 1h

# Alchemy — block-level + token data
.venv/bin/python -m market_tick_data_service --mode batch \
  --source alchemy \
  --chains ethereum,arbitrum,base,polygon,solana \
  --from 2023-01-01
```

### 2d — Priority 4: Alt data

```bash
# Glassnode — on-chain metrics
.venv/bin/python -m market_tick_data_service --mode batch \
  --source glassnode --metrics sopr,nupl,mvrv,nvt,ssr,spent_output_price_distribution \
  --from 2020-01-01

# Coinglass — liquidation + funding
.venv/bin/python -m market_tick_data_service --mode batch \
  --source coinglass --metrics liquidation_heatmap,funding_rates,open_interest \
  --from 2022-01-01
```

### 2e — Priority 5: Sports

```bash
.venv/bin/python -m market_tick_data_service --mode batch \
  --source odds_api --leagues premier_league,nba,nfl --from 2023-01-01

.venv/bin/python -m market_tick_data_service --mode batch \
  --source pinnacle --leagues premier_league,nba --from 2023-01-01
```

**Gate script:**

```bash
python unified-trading-pm/scripts/ops/validate-tick-data-completeness.py
# Checks row counts per symbol per day, flags gaps >2 days
```

---

## Step 3: Features backfill (strict DAG order)

**Dependency: Step 2 gate must pass.**

```
MTDH → MDPS → [FDS, FVS, FCS, FOS, FCM] parallel → FCIS → FMTF → FSS
```

### 3a — MTDH

```bash
cd market-tick-data-history-service
.venv/bin/python -m market_tick_data_history_service --mode batch \
  --from 2023-01-01 --asset-classes crypto_cefi,tradfi
```

### 3b — MDPS

```bash
cd market-data-processing-service
.venv/bin/python -m market_data_processing_service --mode batch --from 2023-01-01
```

### 3c — Feature services (parallel batch jobs)

```bash
for service in delta-one volatility calendar onchain commodity; do
  (cd features-${service}-service && \
    .venv/bin/python -m features_${service//-/_}_service \
      --mode batch --from 2023-01-01 >> /tmp/features_${service}.log 2>&1) &
done
wait && echo "Step 3c complete"
```

### 3d — Cross-instrument (depends on 3c)

```bash
cd features-cross-instrument-service
.venv/bin/python -m features_cross_instrument_service --mode batch --from 2023-01-01
```

### 3e — Multi-timeframe (depends on 3c + 3d)

```bash
cd features-multi-timeframe-service
.venv/bin/python -m features_multi_timeframe_service --mode batch --from 2023-01-01
```

### 3f — Sports features (independent)

```bash
cd features-sports-service
.venv/bin/python -m features_sports_service --mode batch --from 2023-01-01
```

**Gate script:**

```bash
python unified-trading-pm/scripts/ops/validate-features-completeness.py
# Checks feature coverage per symbol: % of trading days with all features present
# Target: >95% coverage per symbol
```

---

## Step 4: ML model training

**Dependency: Step 3 gate must pass.**

```bash
cd ml-training-api
.venv/bin/python -m ml_training_api \
  --task train-all \
  --from 2023-01-01 --to 2024-12-31 \
  --train-val-split 0.8
# Writes versioned artifacts: gs://unified-trading-prod-models/v{semver}/
```

**Gate script:**

```bash
python unified-trading-pm/scripts/ops/validate-model-artifacts.py
# Verifies: artifacts exist, schema valid, inference latency <500ms
```

---

## Step 5: Validation backtest

**Dependency: Steps 1–4 all gates passing.**

```bash
cd execution-service

# Run all 4 portable backtests
.venv/bin/python scripts/runners/run_fresh_backtest.py \
  --strategy cefi_momentum --period 6m --output /tmp/cefi_backtest.json

.venv/bin/python scripts/runners/run_defi_backtests.py \
  --strategy defi_basis --period 6m --output /tmp/defi_backtest.json

.venv/bin/python scripts/runners/run_tradfi_l1_l2_backtests.py \
  --period 6m --output /tmp/tradfi_backtest.json

.venv/bin/python scripts/runners/run_fresh_backtest.py \
  --strategy sports_arb --period 6m --output /tmp/sports_backtest.json
```

**Acceptance criteria** (from `e2e_smoke_and_portable_backtests` reference):

- CeFi: PnL > 0, max drawdown < 5%
- DeFi: PnL > 0
- TradFi: PnL > 0
- Sports: PnL > 0

Direction must match reference (positive). Magnitude may differ ±50% due to longer lookback.

---

## Estimated timeline

| Step                | Duration    | Notes                      |
| ------------------- | ----------- | -------------------------- |
| Step 1: Instruments | 2–4 hours   | API calls + GCS writes     |
| Step 2: Tick data   | 48–72 hours | Rate-limited API calls     |
| Step 3: Features    | 8–12 hours  | Parallel batch computation |
| Step 4: ML training | 4–8 hours   | CPU-bound                  |
| Step 5: Backtest    | 30 minutes  |                            |
| **Total**           | **~4 days** | Start by 2026-03-16        |

---

## Recovery procedures

### Step 2 fails mid-run (rate limit / key expiry)

```bash
# Check progress
python unified-trading-pm/scripts/ops/check-tick-data-progress.py --verbose
# Restart with narrowed date range (idempotent — skips already-downloaded dates)
.venv/bin/python -m market_tick_data_service --mode batch \
  --source <source> --from <last_completed_date>
```

### Step 3 fails (missing upstream data)

```bash
# Find gaps
python unified-trading-pm/scripts/ops/validate-tick-data-completeness.py --verbose
# Re-run Step 2 for gap dates only, then retry failed service
```

### Step 5 backtests fail (wrong PnL direction)

```bash
# Debug with verbose logging
.venv/bin/python scripts/runners/run_fresh_backtest.py \
  --strategy <strategy> --log-level DEBUG --period 1m
# Check feature completeness for the backtest period
python unified-trading-pm/scripts/ops/validate-features-completeness.py \
  --from <backtest_start> --to <backtest_end>
```

---

## Verification Gates Summary

- [ ] Step 1 gate: `validate-instruments-completeness.py` — PASS
- [ ] Step 2 gate: `validate-tick-data-completeness.py` — PASS
- [ ] Step 3 gate: `validate-features-completeness.py` — PASS (>95% coverage)
- [ ] Step 4 gate: `validate-model-artifacts.py` — PASS
- [ ] Step 5: All 4 backtest strategies produce positive PnL

## Files Created

- `unified-trading-pm/runbooks/production-backfill.md` (human-readable runbook)
- `unified-trading-pm/scripts/backfill/run-full-backfill.sh` (orchestrates all 5 steps)
- `unified-trading-pm/scripts/ops/validate-instruments-completeness.py` (new)
- `unified-trading-pm/scripts/ops/validate-tick-data-completeness.py` (new)
- `unified-trading-pm/scripts/ops/validate-features-completeness.py` (new)
- `unified-trading-pm/scripts/ops/validate-model-artifacts.py` (new)
- `unified-trading-pm/scripts/ops/validate-full-backfill.py` (new — runs all 4 gates)
- `unified-trading-pm/scripts/ops/check-tick-data-progress.py` (new)
- `unified-trading-pm/scripts/ops/test-all-api-keys.py` (new)
- `system-integration-tests/tests/e2e/test_backfill_completeness.py` (new)

## Dependencies

- `cloud_infra_bucket_auth_2026_03_10` (GCS buckets must exist)
- `api_keys_and_auth` (all API keys loaded in Secret Manager)
- `phase3_service_hardening` (services deployed and healthy)
- `e2e_smoke_and_portable_backtests` (reference PnL values for Step 5 acceptance)
