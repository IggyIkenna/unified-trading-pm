#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# check-order-flow.sh — Pre-deploy market hours & order flow guard.
#
# For trading-critical services (execution-service, risk-and-exposure-service,
# strategy-service), checks whether it is safe to deploy by:
#   1. Verifying no active order flow via /metrics or /health endpoint
#   2. Checking IBKR market hours (NYSE: Mon-Fri 09:30-16:00 ET, TSE: Mon-Fri 09:00-15:00 JST)
#
# Usage:
#   bash scripts/deployment/check-order-flow.sh <SERVICE_URL> [--force]
#
# Arguments:
#   SERVICE_URL    Base URL of the service (e.g. https://execution-service-abc123.a.run.app)
#   --force        Bypass all guards and allow deployment regardless
#
# Environment:
#   ORDER_FLOW_THRESHOLD   Max acceptable active orders (default: 0)
#   FORCE_DEPLOY           Set to "true" to bypass (same as --force)
#
# Exit codes:
#   0 = safe to deploy
#   1 = NOT safe (active orders or market hours)
#   2 = could not reach service (warning, non-fatal)

set -euo pipefail

SERVICE_URL="${1:?Usage: check-order-flow.sh <SERVICE_URL> [--force]}"
SERVICE_URL="${SERVICE_URL%/}"

# Parse --force flag
FORCE_DEPLOY="${FORCE_DEPLOY:-false}"
for arg in "$@"; do
  if [ "$arg" = "--force" ]; then
    FORCE_DEPLOY="true"
  fi
done

ORDER_FLOW_THRESHOLD="${ORDER_FLOW_THRESHOLD:-0}"

echo "=== Pre-Deploy: Market Hours & Order Flow Guard ==="
echo "Service: $SERVICE_URL"
echo "Force deploy: $FORCE_DEPLOY"
echo "Order flow threshold: $ORDER_FLOW_THRESHOLD"
echo ""

if [ "$FORCE_DEPLOY" = "true" ]; then
  echo "FORCE_DEPLOY=true — bypassing all deployment guards."
  exit 0
fi

# ─── Step 1: IBKR Market Hours Check ────────────────────────────────
# NYSE: Mon-Fri 09:30-16:00 Eastern Time (America/New_York)
# TSE:  Mon-Fri 09:00-15:00 Japan Standard Time (Asia/Tokyo)
#
# If either market is open, warn (soft gate) about deploying trading-critical services.

check_market_hours() {
  local market_name="$1"
  local tz="$2"
  local open_hour="$3"
  local open_min="$4"
  local close_hour="$5"
  local close_min="$6"

  # Get current time in the target timezone
  local current_day current_hour current_min
  current_day=$(TZ="$tz" date +%u 2>/dev/null || echo "0")  # 1=Mon, 7=Sun
  current_hour=$(TZ="$tz" date +%H 2>/dev/null || echo "0")
  current_min=$(TZ="$tz" date +%M 2>/dev/null || echo "0")

  # Strip leading zeros for arithmetic
  current_hour=$((10#$current_hour))
  current_min=$((10#$current_min))

  # Weekend check
  if [ "$current_day" -ge 6 ]; then
    echo "  $market_name: CLOSED (weekend, day=$current_day)"
    return 1
  fi

  # Time check: convert to minutes-since-midnight
  local now_mins=$(( current_hour * 60 + current_min ))
  local open_mins=$(( open_hour * 60 + open_min ))
  local close_mins=$(( close_hour * 60 + close_min ))

  if [ "$now_mins" -ge "$open_mins" ] && [ "$now_mins" -lt "$close_mins" ]; then
    echo "  $market_name: OPEN ($tz time: ${current_hour}:$(printf '%02d' $current_min), hours: $(printf '%02d:%02d' $open_hour $open_min)-$(printf '%02d:%02d' $close_hour $close_min))"
    return 0
  else
    echo "  $market_name: CLOSED ($tz time: ${current_hour}:$(printf '%02d' $current_min), hours: $(printf '%02d:%02d' $open_hour $open_min)-$(printf '%02d:%02d' $close_hour $close_min))"
    return 1
  fi
}

MARKET_OPEN="false"
echo "Checking market hours..."

# NYSE: 09:30 - 16:00 ET
if check_market_hours "NYSE" "America/New_York" 9 30 16 0; then
  MARKET_OPEN="true"
fi

# TSE: 09:00 - 15:00 JST
if check_market_hours "TSE" "Asia/Tokyo" 9 0 15 0; then
  MARKET_OPEN="true"
fi

echo ""

if [ "$MARKET_OPEN" = "true" ]; then
  echo "WARNING: One or more markets are OPEN. Deploying trading-critical services"
  echo "during market hours carries risk of order flow disruption."
  echo ""
  echo "To override: set FORCE_DEPLOY=true or pass --force"
  echo ""
  # This is a soft gate — exit 1 to signal the caller.
  # The workflow step can choose to proceed or block.
fi

# ─── Step 2: Active Order Flow Check ────────────────────────────────
# Query the service /metrics or /health endpoint for active order counts.
# Expected: JSON response with an "active_orders" or "open_orders" field.

echo "Checking active order flow..."

METRICS_RESPONSE=""
METRICS_HTTP_CODE=$(curl -s -o /tmp/metrics_response.json -w "%{http_code}" \
  --connect-timeout 10 --max-time 15 \
  "${SERVICE_URL}/metrics" 2>/dev/null || echo "000")

if [ "$METRICS_HTTP_CODE" = "200" ]; then
  # Try to extract active order count from metrics response
  ACTIVE_ORDERS=$(jq -r '.active_orders // .open_orders // .inflight_orders // "unknown"' /tmp/metrics_response.json 2>/dev/null || echo "unknown")
  echo "  /metrics returned 200, active_orders=$ACTIVE_ORDERS"

  if [ "$ACTIVE_ORDERS" != "unknown" ] && [ "$ACTIVE_ORDERS" != "null" ]; then
    if [ "$ACTIVE_ORDERS" -gt "$ORDER_FLOW_THRESHOLD" ] 2>/dev/null; then
      echo ""
      echo "BLOCKED: $ACTIVE_ORDERS active orders exceed threshold ($ORDER_FLOW_THRESHOLD)."
      echo "Wait for orders to drain or set FORCE_DEPLOY=true to override."
      exit 1
    else
      echo "  Order flow check PASSED: $ACTIVE_ORDERS <= $ORDER_FLOW_THRESHOLD"
    fi
  else
    echo "  Could not parse active_orders from /metrics response. Proceeding with caution."
  fi
elif [ "$METRICS_HTTP_CODE" = "000" ]; then
  echo "  Could not reach $SERVICE_URL/metrics (connection failed)."
  echo "  Service may not be deployed yet. Proceeding."
  exit 2
else
  # Try /health as fallback
  HEALTH_HTTP_CODE=$(curl -s -o /tmp/health_response.json -w "%{http_code}" \
    --connect-timeout 10 --max-time 15 \
    "${SERVICE_URL}/health" 2>/dev/null || echo "000")

  if [ "$HEALTH_HTTP_CODE" = "200" ]; then
    ACTIVE_ORDERS=$(jq -r '.active_orders // .open_orders // "unknown"' /tmp/health_response.json 2>/dev/null || echo "unknown")
    echo "  /health returned 200, active_orders=$ACTIVE_ORDERS"

    if [ "$ACTIVE_ORDERS" != "unknown" ] && [ "$ACTIVE_ORDERS" != "null" ]; then
      if [ "$ACTIVE_ORDERS" -gt "$ORDER_FLOW_THRESHOLD" ] 2>/dev/null; then
        echo ""
        echo "BLOCKED: $ACTIVE_ORDERS active orders exceed threshold ($ORDER_FLOW_THRESHOLD)."
        exit 1
      else
        echo "  Order flow check PASSED: $ACTIVE_ORDERS <= $ORDER_FLOW_THRESHOLD"
      fi
    else
      echo "  Could not parse active_orders from /health response. Proceeding."
    fi
  else
    echo "  /metrics returned $METRICS_HTTP_CODE, /health returned $HEALTH_HTTP_CODE"
    echo "  Could not verify order flow state. Proceeding with caution."
  fi
fi

echo ""

# Final verdict
if [ "$MARKET_OPEN" = "true" ]; then
  echo "RESULT: Markets are open — deployment requires acknowledgement of risk."
  echo "Exiting with code 1 (market-hours guard). Use --force to override."
  exit 1
fi

echo "RESULT: All pre-deploy order flow checks passed."
exit 0
