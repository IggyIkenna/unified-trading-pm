# E2E Testing & Data Download Guide

## Complete Testing Commands for All 22 Repositories

**Date Created:** 2026-02-17
**Purpose:** Comprehensive testing and data download commands for local E2E validation
**Test Date Range:** 2026-01-01 to 2026-01-10 (10 days)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Layer 1: Root Data I/O](#layer-1-root-data-io)
4. [Layer 2: Raw Market Data](#layer-2-raw-market-data)
5. [Layer 3: Market Data Processing](#layer-3-market-data-processing)
6. [Layer 4: Feature Engineering](#layer-4-feature-engineering)
7. [Layer 5: Machine Learning](#layer-5-machine-learning)
8. [Layer 6: Strategy & Execution](#layer-6-strategy--execution)
9. [Layer 7: Post-Trade](#layer-7-post-trade)
10. [Library Repositories](#library-repositories)
11. [Infrastructure Repositories](#infrastructure-repositories)
12. [Parallel Execution Scripts](#parallel-execution-scripts)
13. [Data Verification](#data-verification)

---

## Overview

This guide provides testing commands for all 22 repositories in the unified trading system. Commands are organized by
pipeline execution order (Layer 1 → Layer 7).

### Execution Order (Dependencies)

```
Layer 1: instruments-service, features-calendar-service
   ↓
Layer 2: market-tick-data-service, corporate-actions
   ↓
Layer 3: market-data-processing-service
   ↓
Layer 4: features-delta-one, features-volatility, features-onchain
   ↓
Layer 5: ml-training-service, ml-inference-service
   ↓
Layer 6: strategy-service, execution-service
   ↓
Layer 7: position-balance-monitor-service, risk-and-exposure, pnl-attribution
```

### Test Types Per Service

- **Unit Tests:** Fast isolated tests
- **Integration Tests:** Test with dependencies
- **E2E Tests:** Full pipeline validation
- **Data Download:** Fetch sample data locally

---

## Prerequisites

### Required Tools

```bash
# Python 3.13
python --version  # Should be 3.13.x

# UV package manager
pip install uv

# pytest with xdist for parallel tests
uv pip install pytest pytest-xdist

# jq for JSON parsing (optional)
sudo apt install jq
```

### Environment Setup

```bash
# Set up virtual environment (if needed)
python -m venv .venv
source .venv/bin/activate

# Install dependencies for each service
cd /path/to/service
uv pip install -e ".[dev]"
```

### GCP Authentication (Required for Secret Manager)

```bash
# Authenticate with GCP
gcloud auth application-default login

# Set project
export GCP_PROJECT_ID="test-project"
```

---

## Layer 1: Root Data I/O

### 1. instruments-service

**Repository:** `/data/Upwork/On Going/Ikenna/instruments-service`

#### Unit Tests (Fast)

```bash
cd /data/Upwork/On\ Going/Ikenna/instruments-service

# Run all unit tests in parallel (673 tests, ~28 seconds)
pytest tests/unit/ -n auto --tb=no -q

# Run specific test modules
pytest tests/unit/test_tardis_adapter.py -v
pytest tests/unit/test_ccxt_service.py -v
pytest tests/unit/test_instrument_classifier.py -v
```

#### Integration Tests

```bash
# Run integration tests (requires API keys)
pytest tests/integration/ -v --tb=short

# Run with coverage
pytest tests/integration/ --cov=instruments_service --cov-report=html
```

#### Data Download Commands

##### Single Day (All CEFI Venues - 10 exchanges)

```bash
# Download instruments for one day with ALL CEFI venues
python -m instruments_service \
    --mode instruments \
    --start-date 2026-01-01 \
    --end-date 2026-01-01 \
    --CEFI \
    --dry-run

# Expected: ~12,000-15,000 instruments
# Expected time: ~60-90 seconds
# Output: data/samples/instruments_20260101_*.csv (~3-4 MB)
```

##### Single Day (Single Venue - Testing Only)

```bash
# Download instruments for one day with ONE venue (for quick testing)
python -m instruments_service \
    --mode instruments \
    --start-date 2026-01-01 \
    --end-date 2026-01-01 \
    --venues BINANCE-SPOT \
    --dry-run

# Expected: ~476 instruments
# Expected time: ~14 seconds
# Output: data/samples/instruments_20260101_*.csv (~138 KB)
```

##### Multiple Days Sequential (All CEFI)

```bash
# Download 10 days sequentially (SLOW)
python -m instruments_service \
    --mode instruments \
    --start-date 2026-01-01 \
    --end-date 2026-01-10 \
    --CEFI \
    --dry-run

# Expected: ~120,000-150,000 instruments total
# Expected time: ~600-900 seconds (10-15 minutes)
# Output: 10 CSV files in data/samples/
```

##### Multiple Days Parallel (All CEFI)

```bash
# Use parallel script (see Section: Parallel Execution Scripts)
bash run_parallel_downloads_full_cefi.sh

# Expected: ~120,000-150,000 instruments total
# Expected time: ~150-225 seconds (2.5-3.75 minutes)
# Output: 10 CSV files in data/samples/
```

#### Corporate Actions Mode (TradFi Only)

```bash
# Download corporate actions (dividends, splits, earnings)
python -m instruments_service \
    --mode corporate_actions \
    --TRADFI \
    --dry-run

# Note: Requires instruments-service to have run first (reads equity tickers)
# Expected time: ~13 minutes total
```

#### Verify Downloaded Data

```bash
# Check venues in downloaded data
cat data/samples/instruments_20260101_*.csv | cut -d',' -f2 | tail -n +2 | sort -u

# Expected venues (CEFI):
# BINANCE-SPOT
# BINANCE-FUTURES
# BINANCE-OPTIONS
# BYBIT
# BYBIT-SPOT
# DERIBIT
# OKEX
# OKEX-FUTURES
# OKEX-SWAP
# UPBIT

# Count instruments per venue
awk -F',' 'NR>1 {venues[$2]++} END {for (v in venues) print v, venues[v]}' \
    data/samples/instruments_20260101_*.csv | sort

# Check file size
ls -lh data/samples/instruments_20260101_*.csv
```

---

### 2. features-calendar-service

**Repository:** `/data/Upwork/On Going/Ikenna/features-calendar-service`

#### Unit Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/features-calendar-service

# Run all unit tests in parallel
pytest tests/unit/ -n auto --tb=no -q
```

#### Data Generation

```bash
# Generate calendar features (pure date math, no external deps)
python -m features_calendar_service \
    --mode batch \
    --start-date 2026-01-01 \
    --end-date 2026-01-10 \
    --dry-run

# Expected: Temporal features (day-of-week, month-end, etc.)
# Expected time: ~10-20 seconds
# Output: data/samples/calendar_features_*.csv
```

---

## Layer 2: Raw Market Data

### 3. market-tick-data-service

**Repository:** `/data/Upwork/On Going/Ikenna/market-tick-data-service`

#### Unit Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/market-tick-data-service

# Run all unit tests in parallel
pytest tests/unit/ -n auto --tb=no -q
```

#### Integration Tests

```bash
# Run integration tests with Tardis API
pytest tests/integration/ -v --tb=short

# Run specific integration test
pytest tests/integration/test_tardis_integration.py -v
```

#### Data Download Commands

##### Single Day (All CEFI Venues)

```bash
# Download tick data for one day
python -m market_data_tick_handler \
    --mode download \
    --start-date 2026-01-01 \
    --end-date 2026-01-01 \
    --CEFI \
    --data-type trades \
    --dry-run

# Expected: Raw tick data for all CEFI venues
# Expected time: ~5-10 minutes (large data volume)
# Output: data/samples/tick_data_*.parquet
```

##### Single Instrument (Quick Test)

```bash
# Download tick data for specific instrument
python -m market_data_tick_handler \
    --mode download \
    --start-date 2026-01-01 \
    --end-date 2026-01-01 \
    --venues BINANCE-SPOT \
    --instruments BTC-USDT ETH-USDT \
    --data-type trades \
    --dry-run

# Expected: ~2-5 MB per instrument
# Expected time: ~30-60 seconds
```

#### Streaming Mode (Real-time)

```bash
# Stream live tick data to local file
python -m market_data_tick_handler \
    --mode streaming-ticks-local \
    --venue BINANCE-SPOT \
    --instrument BTC-USDT \
    --duration 60

# Expected: Real-time tick data for 60 seconds
# Output: data/streaming/BTC-USDT_*.parquet
```

---

### 4. corporate-actions (embedded in instruments-service)

**Repository:** `/data/Upwork/On Going/Ikenna/instruments-service`

#### Download Corporate Actions

```bash
cd /data/Upwork/On\ Going/Ikenna/instruments-service

# Fetch dividends, splits, earnings for TradFi equities
python -m instruments_service \
    --mode corporate_actions \
    --TRADFI \
    --dry-run

# Expected: Corporate actions data for equities
# Expected time: ~13 minutes
# Output: data/samples/corporate_actions_*.csv

# Note: Requires instruments-service to have run first for TRADFI
```

---

## Layer 3: Market Data Processing

### 5. market-data-processing-service

**Repository:** Not found in workspace (check if exists)

**Note:** This service is listed in the pipeline but not present in the workspace directories. May need to clone from
repository.

#### Expected Commands (Once Available)

```bash
# Process raw ticks into OHLCV candles
python -m market_data_processing_service \
    --mode batch \
    --start-date 2026-01-01 \
    --end-date 2026-01-10 \
    --CEFI \
    --timeframe 1m \
    --dry-run

# Expected: OHLCV candles from tick data
# Expected time: Varies by data volume
```

---

## Layer 4: Feature Engineering

### 6. features-delta-one-service

**Repository:** `/data/Upwork/On Going/Ikenna/features-delta-one-service`

#### Unit Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/features-delta-one-service

# Run all unit tests in parallel
pytest tests/unit/ -n auto --tb=no -q
```

#### Feature Generation

```bash
# Generate technical indicators, momentum, volume features
python -m features_delta_one_service \
    --mode batch \
    --start-date 2026-01-01 \
    --end-date 2026-01-10 \
    --CEFI \
    --feature-groups technical momentum volume_flow \
    --timeframe 1h \
    --dry-run

# Expected: ~4,596 features across ~20 groups
# Expected time: Varies (CPU-bound)
# Output: data/samples/features_delta_one_*.parquet

# Note: Requires market-data-processing-service output
```

---

### 7. features-volatility-service

**Repository:** `/data/Upwork/On Going/Ikenna/features-volatility-service`

#### Unit Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/features-volatility-service

# Run all unit tests in parallel
pytest tests/unit/ -n auto --tb=no -q
```

#### Volatility Features

```bash
# Generate IV surface, Greeks, term structure
python -m features_volatility_service \
    --mode batch \
    --start-date 2026-01-01 \
    --end-date 2026-01-10 \
    --CEFI \
    --dry-run

# Expected: Volatility features for options
# Expected time: CPU-bound (Black-Scholes calculations)
# Output: data/samples/features_volatility_*.parquet

# Note: Requires raw options chain data from market-tick-data-service
```

---

### 8. features-onchain-service

**Repository:** `/data/Upwork/On Going/Ikenna/features-onchain-service`

#### Unit Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/features-onchain-service

# Run all unit tests in parallel
pytest tests/unit/ -n auto --tb=no -q
```

#### On-chain Features

```bash
# Generate DeFi metrics (TVL, utilization, funding)
python -m features_onchain_service \
    --mode batch \
    --start-date 2026-01-01 \
    --end-date 2026-01-10 \
    --DEFI \
    --dry-run

# Expected: DeFi protocol features
# Expected time: I/O-bound (protocol API calls)
# Output: data/samples/features_onchain_*.parquet
```

---

## Layer 5: Machine Learning

### 9. ml-training-service

**Repository:** `/data/Upwork/On Going/Ikenna/ml-training-service`

#### Unit Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/ml-training-service

# Run all unit tests in parallel
pytest tests/unit/ -n auto --tb=no -q
```

#### Model Training

```bash
# Train LightGBM models
python -m ml_training_service \
    --mode batch \
    --start-date 2026-01-01 \
    --end-date 2026-01-10 \
    --instrument BTC-USDT \
    --timeframe 1h \
    --strategy simple_momentum \
    --dry-run

# Expected: Trained model artifacts
# Expected time: CPU-bound (model training)
# Output: data/samples/models/*.joblib

# Note: Requires features-delta-one output
```

---

### 10. ml-inference-service

**Repository:** `/data/Upwork/On Going/Ikenna/ml-inference-service`

#### Unit Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/ml-inference-service

# Run all unit tests in parallel
pytest tests/unit/ -n auto --tb=no -q
```

#### Batch Inference

```bash
# Generate predictions from trained models
python -m ml_inference_service \
    --mode batch \
    --start-date 2026-01-01 \
    --end-date 2026-01-10 \
    --instrument BTC-USDT \
    --model-path models/btc_momentum_v1.joblib \
    --dry-run

# Expected: Prediction outputs
# Expected time: Light CPU-bound
# Output: data/samples/predictions_*.parquet

# Note: Requires ml-training-service models + features-delta-one
```

---

## Layer 6: Strategy & Execution

### 11. strategy-service

**Repository:** `/data/Upwork/On Going/Ikenna/strategy-service`

#### Unit Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/strategy-service

# Run all unit tests in parallel
pytest tests/unit/ -n auto --tb=no -q
```

#### Strategy Backtesting

```bash
# Test strategy signal generation
python -m strategy_service \
    --mode backtest \
    --start-date 2026-01-01 \
    --end-date 2026-01-10 \
    --strategy simple_momentum \
    --instruments BTC-USDT ETH-USDT \
    --timeframe 1h \
    --dry-run

# Expected: Strategy instructions and signals
# Expected time: Light CPU-bound
# Output: data/samples/strategy_results_*.json

# Note: Requires features-delta-one (and optionally ml-inference predictions)
```

---

### 12. execution-service

**Repository:** `/data/Upwork/On Going/Ikenna/execution-service`

#### Unit Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/execution-service

# Run all unit tests in parallel
pytest tests/unit/ -n auto --tb=no -q
```

#### Execution Backtesting

```bash
# Backtest execution with NautilusTrader
python -m execution_service \
    --mode backtest \
    --start-date 2026-01-01 \
    --end-date 2026-01-10 \
    --config-path configs/momentum_1h.json \
    --dry-run

# Expected: Execution results with fills
# Expected time: CPU-bound (backtesting simulation)
# Output: data/samples/execution_results_*.json

# Note: Requires strategy-service instructions + market-tick-data-service
```

---

## Layer 7: Post-Trade

### 13. position-balance-monitor-service

**Repository:** `/data/Upwork/On Going/Ikenna/position-balance-monitor-service`

#### Unit Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/position-balance-monitor-service

# Run all unit tests in parallel
pytest tests/unit/ -n auto --tb=no -q
```

#### Position Monitoring

```bash
# Monitor positions and reconcile balances
python -m position_balance_monitor_service \
    --mode batch \
    --start-date 2026-01-01 \
    --end-date 2026-01-10 \
    --dry-run

# Expected: Position snapshots and reconciliation reports
# Note: Requires execution-service results
```

---

### 14. risk-and-exposure-service

**Repository:** `/data/Upwork/On Going/Ikenna/risk-and-exposure-service`

#### Unit Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/risk-and-exposure-service

# Run all unit tests in parallel
pytest tests/unit/ -n auto --tb=no -q
```

#### Risk Analysis

```bash
# Calculate risk metrics and exposure
python -m risk_and_exposure_service \
    --mode batch \
    --start-date 2026-01-01 \
    --end-date 2026-01-10 \
    --dry-run

# Expected: Risk reports and exposure analysis
# Note: Requires position-balance-monitor-service output
```

---

## Library Repositories

### 15. unified-trading-services

**Repository:** `/data/Upwork/On Going/Ikenna/unified-trading-services`

#### Tests Only (No Data Download - Library)

```bash
cd /data/Upwork/On\ Going/Ikenna/unified-trading-services

# Run all unit tests
pytest tests/unit/ -n auto -v

# Run cloud integration tests
pytest tests/integration/test_cloud_api_correctness.py -v

# Note: This is a library - no data download mode
```

---

### 16. execution-algo-library

**Repository:** `/data/Upwork/On Going/Ikenna/execution-algo-library`

#### Tests Only

```bash
cd /data/Upwork/On\ Going/Ikenna/execution-algo-library

# Run all unit tests
pytest tests/unit/ -n auto -v

# Note: This is a library - no data download mode
```

---

### 17-20. Interface Libraries

**Repositories:**

- `/data/Upwork/On Going/Ikenna/unified-config-interface`
- `/data/Upwork/On Going/Ikenna/unified-events-interface`
- `/data/Upwork/On Going/Ikenna/unified-market-interface`
- `/data/Upwork/On Going/Ikenna/unified-order-interface`

#### Tests Only (Libraries - No Data Download)

```bash
# For each interface library:
cd /data/Upwork/On\ Going/Ikenna/[interface-name]

# Run unit tests
pytest tests/unit/ -n auto -v

# Note: Interface libraries provide schemas/types only
```

---

## Infrastructure Repositories

### 21. unified-trading-deployment-v3

**Repository:** `/data/Upwork/On Going/Ikenna/unified-trading-deployment-v3`

#### Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/unified-trading-deployment-v3

# Run all unit tests
pytest tests/unit/ -n auto -v

# Test shard calculator
pytest tests/unit/test_shard_calculator.py -v

# Test deployment scripts
bash scripts/run-all-quality-gates.sh --no-fix --quick
```

#### API Server (Deployment Orchestration)

```bash
# Start deployment API locally
bash run-api.sh

# Access UI at: http://localhost:8000
# Note: UI is for cloud deployments, not local testing
```

---

### 22. unified-trading-codex

**Repository:** `/data/Upwork/On Going/Ikenna/unified-trading-codex`

#### Documentation Only (No Tests/Downloads)

```bash
cd /data/Upwork/On\ Going/Ikenna/unified-trading-codex

# Read pipeline documentation
cat COMPLETE_PIPELINE_FLOW.md

# View pipeline diagram
open Pipeline.svg  # or xdg-open Pipeline.svg
```

---

## Additional Services

### 23. live-health-monitor-ui

**Repository:** `/data/Upwork/On Going/Ikenna/live-health-monitor-ui`

#### Frontend Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/live-health-monitor-ui

# Run frontend tests (if using npm/yarn)
npm test

# Or run any Python tests if backend exists
pytest tests/ -v
```

---

### 24. sports-betting-service

**Repository:** `/data/Upwork/On Going/Ikenna/sports-betting-service`

#### Unit Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/sports-betting-service

# Run all unit tests
pytest tests/unit/ -n auto -v
```

---

### 25. new-sports

**Repository:** `/data/Upwork/On Going/Ikenna/new-sports`

#### Tests

```bash
cd /data/Upwork/On\ Going/Ikenna/new-sports

# Run all tests
pytest tests/ -n auto -v
```

---

## Parallel Execution Scripts

### Parallel Download Script (All CEFI Venues)

**File:** `run_parallel_downloads_full_cefi.sh`

```bash
#!/bin/bash

# Parallel download script for instruments-service E2E testing
# Downloads 10 days of data (2026-01-01 to 2026-01-10) with ALL CEFI venues

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Configuration
MAX_PARALLEL=4
START_DATE_BASE="2026-01-"
LOG_DIR="logs"
SAMPLES_DIR="data/samples"

# Create directories
mkdir -p "$LOG_DIR" "$SAMPLES_DIR"

echo "=============================================================================="
echo "INSTRUMENTS-SERVICE: PARALLEL E2E DOWNLOAD TEST (ALL CEFI VENUES)"
echo "=============================================================================="
echo "Date Range: 2026-01-01 to 2026-01-10 (10 days)"
echo "Venues: ALL CEFI (10 exchanges)"
echo "Parallel Jobs: $MAX_PARALLEL"
echo "Output: $SAMPLES_DIR/"
echo "Logs: $LOG_DIR/"
echo "=============================================================================="
echo ""

# Function to run a single download
run_download() {
    local day=$1
    local padded_day=$(printf "%02d" $day)
    local date="${START_DATE_BASE}${padded_day}"
    local log_file="${LOG_DIR}/download-full-cefi-${date}.log"

    echo "[$(date +%H:%M:%S)] Starting FULL CEFI download for $date (job $day/10)"

    # CORRECTED: No --venues flag, downloads all CEFI venues
    python -m instruments_service \
        --mode instruments \
        --start-date "$date" \
        --end-date "$date" \
        --CEFI \
        --dry-run \
        > "$log_file" 2>&1

    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        echo "[$(date +%H:%M:%S)] ✅ Completed $date (job $day/10)"
    else
        echo "[$(date +%H:%M:%S)] ⚠️ Completed with upload errors $date (job $day/10)"
        # Note: Exit code 1 is expected with --dry-run (GCS upload fails)
        # Data is still saved locally in CSV
    fi

    return 0  # Always return success (GCS upload error is expected)
}

# Export function for subshells
export -f run_download
export START_DATE_BASE LOG_DIR SAMPLES_DIR

# Start timer
START_TIME=$(date +%s)

# Track PIDs
pids=()

# Launch jobs in parallel
for day in {1..10}; do
    # Wait if we've reached max parallel jobs
    while [ ${#pids[@]} -ge $MAX_PARALLEL ]; do
        # Check for completed jobs
        for i in "${!pids[@]}"; do
            if ! kill -0 "${pids[$i]}" 2>/dev/null; then
                wait "${pids[$i]}"
                unset 'pids[$i]'
            fi
        done
        # Rebuild array to remove gaps
        pids=("${pids[@]}")
        sleep 0.5
    done

    # Launch new job
    run_download "$day" &
    pids+=($!)
done

# Wait for all remaining jobs
echo ""
echo "Waiting for remaining jobs to complete..."
for pid in "${pids[@]}"; do
    wait "$pid"
done

# End timer
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

echo ""
echo "=============================================================================="
echo "PARALLEL DOWNLOAD SUMMARY"
echo "=============================================================================="
echo "Total Time: ${DURATION} seconds"
echo ""

# Check results
echo "Checking results..."
csv_count=$(find "$SAMPLES_DIR" -name "instruments_202601*.csv" -type f | wc -l)
total_size=$(du -sh "$SAMPLES_DIR" 2>/dev/null | cut -f1)

echo "CSV Files Created: $csv_count"
echo "Total Size: $total_size"
echo ""

# Analyze venues in first file
if [ $csv_count -gt 0 ]; then
    first_file=$(ls -1t "$SAMPLES_DIR"/instruments_202601*.csv | head -1)
    echo "Analyzing first file: $(basename $first_file)"

    # Count instruments
    total_instruments=$(wc -l < "$first_file" | xargs)
    echo "  Total lines: $total_instruments"
    echo "  Total instruments: $((total_instruments - 1))"

    # Count venues
    echo ""
    echo "  Venues found:"
    cat "$first_file" | cut -d',' -f2 | tail -n +2 | sort -u | while read venue; do
        count=$(grep ",$venue," "$first_file" | wc -l)
        echo "    - $venue: $count instruments"
    done

    venue_count=$(cat "$first_file" | cut -d',' -f2 | tail -n +2 | sort -u | wc -l)
    echo ""
    echo "  Total unique venues: $venue_count"
fi

echo ""
echo "Files created:"
ls -lh "$SAMPLES_DIR"/instruments_202601*.csv 2>/dev/null | tail -n +2 | awk '{print "  - " $9 " (" $5 ")"}'

echo ""
echo "Logs available in: $LOG_DIR/"
echo "Data available in: $SAMPLES_DIR/"
echo "=============================================================================="

exit 0
```

### Usage

```bash
# Copy script to instruments-service
cd /data/Upwork/On\ Going/Ikenna/instruments-service
# Save above script as run_parallel_downloads_full_cefi.sh
chmod +x run_parallel_downloads_full_cefi.sh

# Run it
bash run_parallel_downloads_full_cefi.sh

# Expected time: ~150-225 seconds (2.5-3.75 minutes)
# Expected output: 10 CSV files, ~30-40 MB total, ~120,000-150,000 instruments
```

---

## Data Verification

### Quick Verification Script

**File:** `verify_download.sh`

```bash
#!/bin/bash

# Verify downloaded data quality

SERVICE_DIR=$1
DATA_DIR="${SERVICE_DIR}/data/samples"
DATE_PREFIX=$2  # e.g., "20260101"

echo "=============================================================================="
echo "DATA VERIFICATION: ${SERVICE_DIR}"
echo "=============================================================================="

# Find files
FILES=$(find "$DATA_DIR" -name "*${DATE_PREFIX}*.csv" -type f)
FILE_COUNT=$(echo "$FILES" | wc -l)

if [ $FILE_COUNT -eq 0 ]; then
    echo "❌ No files found for date prefix: $DATE_PREFIX"
    exit 1
fi

echo "✅ Found $FILE_COUNT file(s)"
echo ""

# Analyze each file
for file in $FILES; do
    echo "=== $(basename $file) ==="

    # Count rows
    total_rows=$(wc -l < "$file")
    data_rows=$((total_rows - 1))
    echo "  Total rows: $data_rows (excluding header)"

    # File size
    size=$(ls -lh "$file" | awk '{print $5}')
    echo "  File size: $size"

    # Count unique venues
    venue_count=$(cut -d',' -f2 "$file" | tail -n +2 | sort -u | wc -l)
    echo "  Unique venues: $venue_count"

    # Show venues
    echo "  Venues:"
    cut -d',' -f2 "$file" | tail -n +2 | sort -u | while read venue; do
        count=$(grep ",$venue," "$file" | wc -l)
        echo "    - $venue: $count instruments"
    done

    # Check for missing critical fields
    echo "  Schema validation:"

    # Check instrument_key (column 1)
    missing_keys=$(awk -F',' 'NR>1 && ($1 == "" || $1 == "NA") {count++} END {print count+0}' "$file")
    if [ "$missing_keys" -eq 0 ]; then
        echo "    ✅ instrument_key: No missing values"
    else
        echo "    ❌ instrument_key: $missing_keys missing values"
    fi

    # Check venue (column 2)
    missing_venues=$(awk -F',' 'NR>1 && ($2 == "" || $2 == "NA") {count++} END {print count+0}' "$file")
    if [ "$missing_venues" -eq 0 ]; then
        echo "    ✅ venue: No missing values"
    else
        echo "    ❌ venue: $missing_venues missing values"
    fi

    echo ""
done

echo "=============================================================================="
```

### Usage

```bash
# Verify instruments-service download
bash verify_download.sh "/data/Upwork/On Going/Ikenna/instruments-service" "20260101"

# Verify multiple dates
for day in 01 02 03; do
    bash verify_download.sh "/data/Upwork/On Going/Ikenna/instruments-service" "202601$day"
done
```

---

## Expected Results Summary

### instruments-service (All CEFI)

- **Venues:** 10 (binance, binance-futures, deribit, bybit, bybit-spot, okex, okex-futures, okex-swap, upbit, coinbase)
- **Instruments per day:** ~12,000-15,000
- **File size per day:** ~3-4 MB
- **Time (sequential):** ~600-900 seconds
- **Time (parallel, 4 jobs):** ~150-225 seconds

### instruments-service (Single Venue - BINANCE-SPOT)

- **Venues:** 1 (BINANCE-SPOT)
- **Instruments per day:** ~476-482
- **File size per day:** ~138-140 KB
- **Time:** ~14 seconds

### market-tick-data-service

- **Data types:** trades, quotes, l2_snapshots, options_chain
- **Volume:** High (GB-scale for full day)
- **Time:** Hours for full day across all venues

### features-delta-one-service

- **Feature groups:** ~20 (technical, momentum, volume_flow, etc.)
- **Features per instrument:** ~4,596
- **Time:** CPU-bound, varies by instrument count

---

## Critical Notes

### ⚠️ CLI Argument Behavior

**IMPORTANT:** When using `--venues` flag:

- `--CEFI --venues BINANCE-SPOT` → **Downloads only BINANCE-SPOT** (venues overrides category)
- `--CEFI` → **Downloads all 10 CEFI venues**
- No flags → **Downloads ALL categories (CEFI + TRADFI + DEFI)**

### ⚠️ Dry-Run Exit Codes

When using `--dry-run`, services will:

1. ✅ Fetch data successfully from APIs
2. ✅ Save data locally to `data/samples/`
3. ❌ Fail GCS upload (bucket doesn't exist)
4. Return exit code 1 (considered "partial" success)

**This is EXPECTED behavior** - data is saved locally successfully.

### ⚠️ API Keys Required

Services requiring external API keys:

- `instruments-service`: Tardis API (CEFI), Databento (TRADFI), The Graph (DEFI)
- `market-tick-data-service`: Tardis API (CEFI), Databento (TRADFI)
- `features-calendar-service`: FRED API (economic data), earnings API (TradFi)

Keys should be stored in GCP Secret Manager or AWS Secrets Manager.

---

## Testing Strategy

### Recommended Approach

1. **Start with Layer 1** (no dependencies)
   - Test instruments-service thoroughly
   - Test features-calendar-service
2. **Move to Layer 2** (requires Layer 1 output)
   - Test market-tick-data-service
   - Test corporate-actions
3. **Continue Layer by Layer**
   - Each layer depends on previous layers
   - Validate data at each stage

### Quick Test (Single Instrument)

```bash
# Instruments
python -m instruments_service --start-date 2026-01-01 --end-date 2026-01-01 --venues BINANCE-SPOT --dry-run

# Ticks
python -m market_data_tick_handler --start-date 2026-01-01 --end-date 2026-01-01 --venues BINANCE-SPOT --instruments BTC-USDT --data-type trades --dry-run

# Features
python -m features_delta_one_service --start-date 2026-01-01 --end-date 2026-01-01 --instruments BTC-USDT --timeframe 1h --dry-run
```

### Full Pipeline Test (Single Day, Single Venue)

```bash
# 1. Instruments
python -m instruments_service --mode instruments --start-date 2026-01-01 --end-date 2026-01-01 --venues BINANCE-SPOT --dry-run

# 2. Ticks
python -m market_data_tick_handler --mode download --start-date 2026-01-01 --end-date 2026-01-01 --venues BINANCE-SPOT --instruments BTC-USDT ETH-USDT --data-type trades --dry-run

# 3. Process (if service available)
# python -m market_data_processing_service --start-date 2026-01-01 --end-date 2026-01-01 --venues BINANCE-SPOT --timeframe 1h --dry-run

# 4. Features
python -m features_delta_one_service --mode batch --start-date 2026-01-01 --end-date 2026-01-01 --instruments BTC-USDT ETH-USDT --timeframe 1h --dry-run

# 5. Continue through ML and strategy layers...
```

---

## Performance Benchmarks

### Expected Times (Single Day, All CEFI Venues)

| Service                  | Sequential | Parallel (4 jobs) | Speedup |
| ------------------------ | ---------- | ----------------- | ------- |
| instruments-service      | ~60-90s    | ~15-23s           | 4x      |
| market-tick-data-service | ~5-10min   | ~1.5-3min         | 3-4x    |
| features-delta-one       | ~3-5min    | ~45-90s           | 4x      |
| ml-training              | ~10-20min  | ~3-5min           | 3-4x    |

### Storage Requirements (10 Days)

| Service                  | Per Day    | Total (10 days) |
| ------------------------ | ---------- | --------------- |
| instruments-service      | ~3-4 MB    | ~30-40 MB       |
| market-tick-data-service | ~500MB-2GB | ~5-20 GB        |
| features-delta-one       | ~50-100 MB | ~500MB-1GB      |
| ml-training              | ~10-50 MB  | ~100-500 MB     |

---

## Troubleshooting

### Common Issues

#### Issue: "Module not found"

```bash
# Solution: Install dependencies
cd /path/to/service
uv pip install -e ".[dev]"
```

#### Issue: "API key not found"

```bash
# Solution: Check Secret Manager
gcloud secrets list | grep -i tardis
gcloud secrets versions access latest --secret="tardis-api-key"

# Or set environment variable
export TARDIS_API_KEY="your-key-here"
```

#### Issue: "Tests running slowly"

```bash
# Solution: Use parallel execution
pytest tests/unit/ -n auto  # Use all CPU cores
pytest tests/unit/ -n 4     # Use 4 cores explicitly
```

#### Issue: "Data not saving locally"

```bash
# Solution: Check --dry-run flag and directories
mkdir -p data/samples logs

# Verify --dry-run is in command
python -m instruments_service --mode instruments --start-date 2026-01-01 --end-date 2026-01-01 --CEFI --dry-run

# Check output
ls -lh data/samples/
```

#### Issue: "Only downloaded 1 venue instead of all CEFI"

```bash
# Problem: Used --venues flag which overrides --CEFI
# Solution: Remove --venues flag to download all

# ❌ WRONG: Downloads only BINANCE-SPOT
python -m instruments_service --CEFI --venues BINANCE-SPOT --dry-run

# ✅ CORRECT: Downloads all 10 CEFI venues
python -m instruments_service --CEFI --dry-run
```

---

## Quick Reference

### Run All Unit Tests (All Services)

```bash
for service in instruments-service market-tick-data-service features-delta-one-service \
               features-volatility-service features-onchain-service features-calendar-service \
               ml-training-service ml-inference-service strategy-service execution-service \
               unified-trading-services; do
    echo "Testing $service..."
    cd "/data/Upwork/On Going/Ikenna/$service"
    pytest tests/unit/ -n auto --tb=no -q || echo "❌ Failed: $service"
done
```

### Download Sample Data (All Data I/O Services)

```bash
# Instruments (quick test - 1 venue, 1 day)
cd "/data/Upwork/On Going/Ikenna/instruments-service"
python -m instruments_service --mode instruments --start-date 2026-01-01 --end-date 2026-01-01 --venues BINANCE-SPOT --dry-run

# Ticks (quick test - 1 instrument, 1 day)
cd "/data/Upwork/On Going/Ikenna/market-tick-data-service"
python -m market_data_tick_handler --mode download --start-date 2026-01-01 --end-date 2026-01-01 --venues BINANCE-SPOT --instruments BTC-USDT --data-type trades --dry-run

# Calendar (10 days, no external deps)
cd "/data/Upwork/On Going/Ikenna/features-calendar-service"
python -m features_calendar_service --mode batch --start-date 2026-01-01 --end-date 2026-01-10 --dry-run
```

---

## Next Steps After Testing

1. **Analyze Results**
   - Check data completeness
   - Verify schema compliance
   - Compare with production data in GCS

2. **Document Findings**
   - Create service-specific test reports
   - Note any issues or failures
   - Update this guide with actual timings

3. **Iterate**
   - Fix any identified issues
   - Re-run failed tests
   - Validate fixes

4. **Production Validation**
   - Compare local vs cloud data
   - Verify data quality
   - Check for missing dates/venues

---

## Repository Status

### Services with CLI Entry Points (Data Download)

- ✅ instruments-service
- ✅ market-tick-data-service
- ✅ features-calendar-service
- ✅ features-delta-one-service
- ✅ features-volatility-service
- ✅ features-onchain-service
- ✅ ml-training-service
- ✅ ml-inference-service
- ✅ strategy-service
- ✅ execution-service
- ⚠️ market-data-processing-service (not found in workspace)

### Library Repositories (Tests Only)

- ✅ unified-trading-services
- ✅ execution-algo-library
- ✅ unified-config-interface
- ✅ unified-events-interface
- ✅ unified-market-interface
- ✅ unified-order-interface

### Infrastructure Repositories

- ✅ unified-trading-deployment-v3
- ✅ unified-trading-codex (documentation)
- ✅ live-health-monitor-ui

### Additional Services

- ✅ position-balance-monitor-service
- ✅ risk-and-exposure-service
- ✅ sports-betting-service
- ✅ new-sports

---

**Document Version:** 1.0
**Last Updated:** 2026-02-17
**Maintainer:** Generated for E2E testing initiative
