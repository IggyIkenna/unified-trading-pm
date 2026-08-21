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
# setup-dev-pubsub.sh — Create all PubSub topics and subscriptions for unified-trading-dev.
#
# Reads topic templates from configs/runtime-topology.yaml and expands them using
# a representative dev venue/instrument_type set. Idempotent — safe to re-run.
#
# Usage:
#   setup-dev-pubsub.sh [--project PROJECT] [--dry-run] [--emulator]
#
# Modes:
#   Default:    Creates topics/subscriptions in GCP project (requires gcloud auth)
#   --emulator: Uses PUBSUB_EMULATOR_HOST (defaults to localhost:8085)
#
# Dev venue subset used for topic expansion:
#   venues: binance okx bybit coinbase hyperliquid
#   instrument_types: spot futures
#   data_types: trade ohlcv orderbook
#   timeframes: 1m 5m 15m 1h
#   feature_categories: momentum volatility regime
#   categories: cefi defi

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
TOPOLOGY_FILE="${SCRIPT_DIR}/../../configs/runtime-topology.yaml"

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

PROJECT="unified-trading-dev"
DRY_RUN=false
USE_EMULATOR=false

for arg in "$@"; do
    case "$arg" in
        --project=*) PROJECT="${arg#*=}" ;;
        --project)   shift; PROJECT="${1:-unified-trading-dev}" ;;
        --dry-run)   DRY_RUN=true ;;
        --emulator)  USE_EMULATOR=true ;;
        *)
            echo "Unknown argument: $arg" >&2
            echo "Usage: $0 [--project PROJECT] [--dry-run] [--emulator]" >&2
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Emulator setup
# ---------------------------------------------------------------------------

if [[ "${USE_EMULATOR}" == "true" ]]; then
    export PUBSUB_EMULATOR_HOST="${PUBSUB_EMULATOR_HOST:-localhost:8085}"
    echo "Using Pub/Sub emulator at ${PUBSUB_EMULATOR_HOST}"
fi

# ---------------------------------------------------------------------------
# Dev expansion sets (representative subset — not all production shards)
# ---------------------------------------------------------------------------

VENUES=(binance okx bybit coinbase hyperliquid)
INSTRUMENT_TYPES=(spot futures)
DATA_TYPES=(trade ohlcv orderbook)
TIMEFRAMES=(1m 5m 15m 1h)
FEATURE_CATEGORIES=(momentum volatility regime)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

CREATED_TOPICS=0
SKIPPED_TOPICS=0
CREATED_SUBS=0

run_gcloud() {
    if [[ "${DRY_RUN}" == "true" ]]; then
        echo "  [dry-run] gcloud $*"
        return 0
    fi
    gcloud "$@" 2>&1
}

topic_exists() {
    local topic="$1"
    gcloud pubsub topics describe "projects/${PROJECT}/topics/${topic}" \
        --project="${PROJECT}" &>/dev/null 2>&1
}

sub_exists() {
    local sub="$1"
    gcloud pubsub subscriptions describe "projects/${PROJECT}/subscriptions/${sub}" \
        --project="${PROJECT}" &>/dev/null 2>&1
}

create_topic() {
    local topic="$1"
    if [[ "${DRY_RUN}" == "true" ]]; then
        echo "  [dry-run] create topic: ${topic}"
        CREATED_TOPICS=$((CREATED_TOPICS + 1))
        return 0
    fi
    if topic_exists "${topic}"; then
        echo "  SKIP (exists): ${topic}"
        SKIPPED_TOPICS=$((SKIPPED_TOPICS + 1))
        return 0
    fi
    run_gcloud pubsub topics create "${topic}" --project="${PROJECT}" >/dev/null
    echo "  CREATE topic: ${topic}"
    CREATED_TOPICS=$((CREATED_TOPICS + 1))
}

create_subscription() {
    local sub="$1"
    local topic="$2"
    local ack_deadline="${3:-60}"
    if [[ "${DRY_RUN}" == "true" ]]; then
        echo "  [dry-run] create sub: ${sub} -> ${topic}"
        CREATED_SUBS=$((CREATED_SUBS + 1))
        return 0
    fi
    if sub_exists "${sub}"; then
        echo "  SKIP (exists): ${sub}"
        return 0
    fi
    run_gcloud pubsub subscriptions create "${sub}" \
        --topic="${topic}" \
        --project="${PROJECT}" \
        --ack-deadline="${ack_deadline}" \
        --message-retention-duration="7d" >/dev/null
    echo "  CREATE sub: ${sub}"
    CREATED_SUBS=$((CREATED_SUBS + 1))
}

section() {
    echo ""
    echo "--- $1 ---"
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

echo "======================================================="
echo " unified-trading dev PubSub setup"
echo " project=${PROJECT}  dry_run=${DRY_RUN}  emulator=${USE_EMULATOR}"
echo "======================================================="

# instruments-service: instrument-events-{venue}
section "instruments-service"
for venue in "${VENUES[@]}"; do
    topic="instrument-events-${venue}"
    create_topic "${topic}"
    create_subscription "${topic}-sub" "${topic}"
done

# market-tick-data-service: raw-ticks-{venue}-{instrument_type}-{data_type}
section "market-tick-data-service"
for venue in "${VENUES[@]}"; do
    for itype in "${INSTRUMENT_TYPES[@]}"; do
        for dtype in "${DATA_TYPES[@]}"; do
            topic="raw-ticks-${venue}-${itype}-${dtype}"
            create_topic "${topic}"
            create_subscription "${topic}-sub" "${topic}"
        done
    done
done

# market-data-processing-service: processed-candles-{venue}-{instrument_type}-{timeframe}
section "market-data-processing-service"
for venue in "${VENUES[@]}"; do
    for itype in "${INSTRUMENT_TYPES[@]}"; do
        for tf in "${TIMEFRAMES[@]}"; do
            topic="processed-candles-${venue}-${itype}-${tf}"
            create_topic "${topic}"
            create_subscription "${topic}-sub" "${topic}"
        done
    done
done

# features-delta-one-service: features-delta-one-{feature_category}-{venue}
section "features-delta-one-service"
for fc in "${FEATURE_CATEGORIES[@]}"; do
    for venue in "${VENUES[@]}"; do
        topic="features-delta-one-${fc}-${venue}"
        create_topic "${topic}"
        create_subscription "${topic}-sub" "${topic}"
    done
done

# features-volatility-service: features-volatility-{feature_category}-{venue}
section "features-volatility-service"
for fc in "${FEATURE_CATEGORIES[@]}"; do
    for venue in "${VENUES[@]}"; do
        topic="features-volatility-${fc}-${venue}"
        create_topic "${topic}"
        create_subscription "${topic}-sub" "${topic}"
    done
done

# features-cross-instrument-service: features-cross-instrument-{feature_category}
section "features-cross-instrument-service"
for fc in "${FEATURE_CATEGORIES[@]}"; do
    topic="features-cross-instrument-${fc}"
    create_topic "${topic}"
    create_subscription "${topic}-sub" "${topic}"
done

# ml-inference-service: ml-predictions-{venue}
section "ml-inference-service"
for venue in "${VENUES[@]}"; do
    topic="ml-predictions-${venue}"
    create_topic "${topic}"
    create_subscription "${topic}-sub" "${topic}"
done

# strategy-service: strategy-signals
section "strategy-service"
create_topic "strategy-signals"
create_subscription "strategy-signals-sub" "strategy-signals"

# execution-service: execution-orders, execution-fills, circuit-breaker-events
section "execution-service"
for t in execution-orders execution-fills circuit-breaker-events; do
    create_topic "${t}"
    create_subscription "${t}-sub" "${t}"
done

# alerting-service: system-alerts
section "alerting-service"
create_topic "system-alerts"
create_subscription "system-alerts-sub" "system-alerts"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
echo "======================================================="
echo " PubSub setup complete"
echo " Created topics:        ${CREATED_TOPICS}"
echo " Skipped (existing):    ${SKIPPED_TOPICS}"
echo " Created subscriptions: ${CREATED_SUBS}"
echo "======================================================="
