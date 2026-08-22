#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# post-deploy-smoke.sh — Post-deploy smoke test for Cloud Run services.
#
# Usage: bash scripts/deploy/post-deploy-smoke.sh <SERVICE_URL> [MAX_RETRIES] [RETRY_INTERVAL]
#
# Hits /health and /readiness endpoints on the deployed service.
# Returns 0 if both pass, 1 if either fails after retries.
#
# Arguments:
#   SERVICE_URL      Base URL of the deployed service (e.g. https://execution-service-abc123-an.a.run.app)
#   MAX_RETRIES      Number of retries (default: 3)
#   RETRY_INTERVAL   Seconds between retries (default: 30)

set -euo pipefail

SERVICE_URL="${1:?Usage: post-deploy-smoke.sh <SERVICE_URL> [MAX_RETRIES] [RETRY_INTERVAL]}"
MAX_RETRIES="${2:-3}"
RETRY_INTERVAL="${3:-30}"

# Strip trailing slash
SERVICE_URL="${SERVICE_URL%/}"

check_endpoint() {
  local endpoint="$1"
  local url="${SERVICE_URL}${endpoint}"
  local attempt=0

  while [ "$attempt" -lt "$MAX_RETRIES" ]; do
    attempt=$((attempt + 1))
    echo "  Attempt $attempt/$MAX_RETRIES: GET $url"

    HTTP_CODE=$(curl -s -o /tmp/smoke_response.txt -w "%{http_code}" \
      --connect-timeout 10 --max-time 30 "$url" 2>/dev/null || echo "000")

    if [ "$HTTP_CODE" = "200" ]; then
      echo "  $endpoint returned 200 OK"
      return 0
    fi

    echo "  $endpoint returned HTTP $HTTP_CODE"
    if [ "$attempt" -lt "$MAX_RETRIES" ]; then
      echo "  Retrying in ${RETRY_INTERVAL}s..."
      sleep "$RETRY_INTERVAL"
    fi
  done

  echo "  FAILED: $endpoint did not return 200 after $MAX_RETRIES attempts"
  return 1
}

echo "=== Post-Deploy Smoke Test ==="
echo "Service: $SERVICE_URL"
echo "Max retries: $MAX_RETRIES, interval: ${RETRY_INTERVAL}s"
echo ""

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
  echo "Smoke test PASSED"
  exit 0
else
  echo "Smoke test FAILED"
  exit 1
fi
