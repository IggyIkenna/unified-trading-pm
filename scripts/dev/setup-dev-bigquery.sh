#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# RETIRED 2026-03-13 — Referenced unified-trading-dev as a separate GCP project (never created).
# Dev resources now live in central-element-323112 with -dev suffix, provisioned via Terraform:
#   cd deployment-service/terraform/gcp
#   terraform apply -var="environment=dev" -var="project_id=central-element-323112"
# See: deployment-service/docs/dev-environment.md
#
# setup-dev-bigquery.sh — Create BigQuery dev dataset and 4 core tables (schema-correct, empty).
#
# Tables created (BigQuery OLAP analytics layer — NOT GCS persistence):
#   1. instruments_universe      — canonical instrument records
#   2. raw_tick_data             — raw venue tick data (trade/orderbook/ohlcv)
#   3. processed_candles_ohlcv   — standardised OHLCV candles
#   4. execution_results         — execution fills (audit-grade, 7-year retention)
#
# Idempotent — safe to re-run (uses --skip_leading_rows, not --replace).
#
# Usage:
#   setup-dev-bigquery.sh [--project PROJECT] [--dataset DATASET] [--location LOCATION] [--dry-run]
#
# Requires:
#   - bq CLI (part of Google Cloud SDK)
#   - Authenticated gcloud session with BigQuery admin rights

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

PROJECT="unified-trading-dev"
DATASET="trading_analytics"
LOCATION="US"
DRY_RUN=false

for arg in "$@"; do
    case "$arg" in
        --project=*)  PROJECT="${arg#*=}" ;;
        --project)    shift; PROJECT="${1:-unified-trading-dev}" ;;
        --dataset=*)  DATASET="${arg#*=}" ;;
        --dataset)    shift; DATASET="${1:-trading_analytics}" ;;
        --location=*) LOCATION="${arg#*=}" ;;
        --location)   shift; LOCATION="${1:-US}" ;;
        --dry-run)    DRY_RUN=true ;;
        *)
            echo "Unknown argument: $arg" >&2
            echo "Usage: $0 [--project PROJECT] [--dataset DATASET] [--location LOCATION] [--dry-run]" >&2
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

run_bq() {
    if [[ "${DRY_RUN}" == "true" ]]; then
        echo "  [dry-run] bq $*"
        return 0
    fi
    bq "$@"
}

dataset_exists() {
    bq ls --project_id="${PROJECT}" --format=json 2>/dev/null \
        | python3 -c "import sys, json; ds = json.load(sys.stdin); print(any(d.get('datasetReference',{}).get('datasetId') == '${DATASET}' for d in ds))" 2>/dev/null || echo "False"
}

table_exists() {
    local table="$1"
    bq show --project_id="${PROJECT}" "${DATASET}.${table}" &>/dev/null 2>&1
}

create_table() {
    local table="$1"
    local schema="$2"
    local description="$3"
    local partition_field="${4:-}"

    if [[ "${DRY_RUN}" == "true" ]]; then
        echo "  [dry-run] create table: ${DATASET}.${table}"
        return 0
    fi

    if table_exists "${table}"; then
        echo "  SKIP (exists): ${DATASET}.${table}"
        return 0
    fi

    local extra_flags=()
    if [[ -n "${partition_field}" ]]; then
        extra_flags+=(--time_partitioning_field "${partition_field}" --time_partitioning_type DAY)
    fi

    echo "${schema}" | run_bq mk \
        --project_id="${PROJECT}" \
        --table \
        --description="${description}" \
        "${extra_flags[@]}" \
        "${DATASET}.${table}" \
        /dev/stdin

    echo "  CREATE table: ${DATASET}.${table}"
}

section() {
    echo ""
    echo "--- $1 ---"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

echo "======================================================="
echo " unified-trading dev BigQuery setup"
echo " project=${PROJECT}  dataset=${DATASET}  location=${LOCATION}  dry_run=${DRY_RUN}"
echo "======================================================="

# Create dataset (idempotent via --nodefault_dataset / mk check)
section "Dataset"
if [[ "${DRY_RUN}" == "true" ]]; then
    echo "  [dry-run] create dataset: ${PROJECT}:${DATASET} (${LOCATION})"
else
    if bq ls --project_id="${PROJECT}" --format=json 2>/dev/null \
        | python3 -c "import sys, json; ds=json.load(sys.stdin); exit(0 if any(d.get('datasetReference',{}).get('datasetId')=='${DATASET}' for d in ds) else 1)" 2>/dev/null; then
        echo "  SKIP (exists): ${PROJECT}:${DATASET}"
    else
        bq mk \
            --project_id="${PROJECT}" \
            --dataset \
            --location="${LOCATION}" \
            --description="unified-trading dev analytics dataset" \
            "${DATASET}"
        echo "  CREATE dataset: ${PROJECT}:${DATASET}"
    fi
fi

# ---------------------------------------------------------------------------
# Table 1: instruments_universe
# Schema mirrors unified_internal_contracts InstrumentRecord core fields
# ---------------------------------------------------------------------------
section "Table: instruments_universe"
create_table "instruments_universe" \
    "instrument_id:STRING,venue:STRING,symbol:STRING,base_asset:STRING,quote_asset:STRING,instrument_type:STRING,category:STRING,tick_size:FLOAT64,lot_size:FLOAT64,min_order_size:FLOAT64,is_active:BOOL,listed_at:TIMESTAMP,delisted_at:TIMESTAMP,ingested_at:TIMESTAMP" \
    "Canonical instrument universe — indexed per venue and instrument type" \
    "ingested_at"

# ---------------------------------------------------------------------------
# Table 2: raw_tick_data
# Schema: venue tick (trade/orderbook/ohlcv) as ingested from MTDH
# ---------------------------------------------------------------------------
section "Table: raw_tick_data"
create_table "raw_tick_data" \
    "event_id:STRING,venue:STRING,symbol:STRING,instrument_type:STRING,data_type:STRING,exchange_ts:TIMESTAMP,ingest_ts:TIMESTAMP,price:FLOAT64,quantity:FLOAT64,side:STRING,bid_price:FLOAT64,ask_price:FLOAT64,bid_qty:FLOAT64,ask_qty:FLOAT64,open:FLOAT64,high:FLOAT64,low:FLOAT64,close:FLOAT64,volume:FLOAT64,timeframe:STRING,raw_json:STRING" \
    "Raw venue tick data (trades, orderbook snapshots, OHLCV) as ingested" \
    "exchange_ts"

# ---------------------------------------------------------------------------
# Table 3: processed_candles_ohlcv
# Schema: standardised OHLCV candles from MDPS
# ---------------------------------------------------------------------------
section "Table: processed_candles_ohlcv"
create_table "processed_candles_ohlcv" \
    "candle_id:STRING,venue:STRING,symbol:STRING,instrument_type:STRING,timeframe:STRING,open_ts:TIMESTAMP,close_ts:TIMESTAMP,open:FLOAT64,high:FLOAT64,low:FLOAT64,close:FLOAT64,volume:FLOAT64,trade_count:INT64,vwap:FLOAT64,is_complete:BOOL,processed_at:TIMESTAMP" \
    "Standardised OHLCV candles produced by market-data-processing-service" \
    "open_ts"

# ---------------------------------------------------------------------------
# Table 4: execution_results
# Schema: execution fills (MiFID/FCA audit, 7-year retention)
# ---------------------------------------------------------------------------
section "Table: execution_results"
create_table "execution_results" \
    "fill_id:STRING,client_order_id:STRING,venue_order_id:STRING,venue:STRING,symbol:STRING,instrument_type:STRING,side:STRING,order_type:STRING,fill_price:NUMERIC,fill_quantity:NUMERIC,commission:NUMERIC,commission_asset:STRING,exchange_timestamp:TIMESTAMP,ack_timestamp:TIMESTAMP,strategy_id:STRING,client_id:STRING,subaccount_id:STRING,venue_response_id:STRING,is_partial:BOOL,execution_state:STRING,recorded_at:TIMESTAMP" \
    "Execution fills — MiFID/FCA audit trail (7-year retention). NUMERIC fields for Decimal precision." \
    "exchange_timestamp"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "======================================================="
echo " BigQuery setup complete"
echo " Dataset: ${PROJECT}:${DATASET} (${LOCATION})"
echo " Tables:  instruments_universe, raw_tick_data,"
echo "          processed_candles_ohlcv, execution_results"
echo "======================================================="
