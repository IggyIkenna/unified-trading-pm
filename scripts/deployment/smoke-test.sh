#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# smoke-test.sh — Lightweight post-deploy smoke test for Cloud Run services.
#
# Hits /health and /readiness endpoints and verifies response shape.
# This is the scripts/deployment/ canonical version (Task 4 of pipeline hardening).
#
# Usage:
#   bash scripts/deployment/smoke-test.sh <SERVICE_URL> [MAX_RETRIES] [RETRY_INTERVAL]
#
# Arguments:
#   SERVICE_URL      Base URL of the deployed service
#   MAX_RETRIES      Number of retries per endpoint (default: 5)
#   RETRY_INTERVAL   Seconds between retries (default: 30)
#
# Exit codes:
#   0 = all checks passed
#   1 = one or more checks failed after retries

set -euo pipefail

SERVICE_URL="${1:?Usage: smoke-test.sh <SERVICE_URL> [MAX_RETRIES] [RETRY_INTERVAL]}"
MAX_RETRIES="${2:-5}"
RETRY_INTERVAL="${3:-30}"

# Strip trailing slash
SERVICE_URL="${SERVICE_URL%/}"

echo "=== Post-Deploy Smoke Test ==="
echo "Service: $SERVICE_URL"
echo "Max retries: $MAX_RETRIES, interval: ${RETRY_INTERVAL}s"
echo ""

# ─── Helper: Check endpoint with response shape validation ──────────
check_endpoint() {
  local endpoint="$1"
  local url="${SERVICE_URL}${endpoint}"
  local attempt=0

  while [ "$attempt" -lt "$MAX_RETRIES" ]; do
    attempt=$((attempt + 1))
    echo "  Attempt $attempt/$MAX_RETRIES: GET $url"

    HTTP_CODE=$(curl -s -o /tmp/smoke_response_body.json -w "%{http_code}" \
      --connect-timeout 10 --max-time 30 "$url" 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
      echo "  $endpoint returned 200 OK"

      # Validate response is valid JSON
      if ! jq empty /tmp/smoke_response_body.json 2>/dev/null; then
        echo "  WARNING: Response is not valid JSON (non-fatal)"
        return 0
      fi

      # Validate response shape: expect at least a "status" field
      RESPONSE_STATUS=$(jq -r '.status // empty' /tmp/smoke_response_body.json 2>/dev/null || echo "")
      if [ -n "$RESPONSE_STATUS" ]; then
        echo "  Response shape OK: status=\"$RESPONSE_STATUS\""

        # For /health, check for expected fields
        if [ "$endpoint" = "/health" ]; then
          VERSION=$(jq -r '.version // empty' /tmp/smoke_response_body.json 2>/dev/null || echo "")
          if [ -n "$VERSION" ]; then
            echo "  Reported version: $VERSION"
          fi
        fi

        # For /readiness, check for dependencies readiness
        if [ "$endpoint" = "/readiness" ]; then
          DEPS_OK=$(jq -r '.dependencies // empty | length' /tmp/smoke_response_body.json 2>/dev/null || echo "0")
          if [ "$DEPS_OK" != "0" ]; then
            echo "  Dependencies reported: $DEPS_OK"
          fi
        fi
      else
        echo "  WARNING: No 'status' field in response (non-fatal — endpoint returned 200)"
      fi

      return 0
    fi

    echo "  $endpoint returned HTTP $HTTP_CODE"

    if [ "$HTTP_CODE" = "000" ]; then
      echo "  Connection failed — service may still be starting"
    fi

    if [ "$attempt" -lt "$MAX_RETRIES" ]; then
      echo "  Retrying in ${RETRY_INTERVAL}s..."
      sleep "$RETRY_INTERVAL"
    fi
  done

  echo "  FAILED: $endpoint did not return 200 after $MAX_RETRIES attempts"
  return 1
}

# ─── Run checks ─────────────────────────────────────────────────────
HEALTH_OK=0
READINESS_OK=0

echo "Checking /health..."
if check_endpoint "/health"; then
  HEALTH_OK=1
fi

echo ""
echo "Checking /readiness..."
if check_endpoint "/readiness"; then
  READINESS_OK=1
fi

echo ""
echo "=== Smoke Test Results ==="
echo "  /health:    $([ "$HEALTH_OK" = "1" ] && echo "PASS" || echo "FAIL")"
echo "  /readiness: $([ "$READINESS_OK" = "1" ] && echo "PASS" || echo "FAIL")"

if [ "$HEALTH_OK" = "1" ] && [ "$READINESS_OK" = "1" ]; then
  echo ""
  echo "Smoke test PASSED"
  exit 0
else
  echo ""
  echo "Smoke test FAILED"
  exit 1
fi
