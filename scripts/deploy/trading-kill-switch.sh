#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# trading-kill-switch.sh — Kill switch protocol for trading-critical deployments.
#
# Usage:
#   bash scripts/deploy/trading-kill-switch.sh halt   <GH_TOKEN> [REPO_OWNER]
#   bash scripts/deploy/trading-kill-switch.sh resume <GH_TOKEN> [REPO_OWNER]
#   bash scripts/deploy/trading-kill-switch.sh drain  <GH_TOKEN> [REPO_OWNER] [TIMEOUT_SECONDS]
#
# Functions:
#   halt   — Sends repository_dispatch "halt-order-flow" to execution-service.
#            This signals the execution service to stop accepting new orders.
#   resume — Sends repository_dispatch "resume-order-flow" to execution-service.
#            This signals the execution service to resume accepting orders.
#   drain  — Polls execution-service for in-flight order drain completion.
#            Waits up to TIMEOUT_SECONDS (default: 120) for orders to drain.
#
# The execution-service must implement handlers for these dispatch events:
#   - halt-order-flow:   Set service to reject new orders, drain in-flight orders
#   - resume-order-flow: Resume normal order acceptance
#
# Arguments:
#   ACTION        "halt", "resume", or "drain"
#   GH_TOKEN      GitHub token with repo scope for dispatching events
#   REPO_OWNER    GitHub org/user (default: IggyIkenna)
#   TIMEOUT_SECONDS  Max seconds to wait for drain (drain action only, default: 120)

set -euo pipefail

ACTION="${1:?Usage: trading-kill-switch.sh <halt|resume|drain> <GH_TOKEN> [REPO_OWNER] [TIMEOUT]}"
GH_TOKEN="${2:?Missing GH_TOKEN}"
REPO_OWNER="${3:-IggyIkenna}"
TIMEOUT="${4:-120}"

TARGET_REPO="execution-service"

dispatch_event() {
  local event_type="$1"
  local payload="${2:-{}}"

  echo "Dispatching '$event_type' to $REPO_OWNER/$TARGET_REPO..."

  HTTP_CODE=$(curl -s -o /tmp/dispatch_response.txt -w "%{http_code}" \
    -X POST \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: Bearer $GH_TOKEN" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/${REPO_OWNER}/${TARGET_REPO}/dispatches" \
    -d "{\"event_type\": \"${event_type}\", \"client_payload\": ${payload}}" \
    2>/dev/null || echo "000")

  if [ "$HTTP_CODE" = "204" ]; then
    echo "Event '$event_type' dispatched successfully"
    return 0
  else
    echo "WARNING: dispatch returned HTTP $HTTP_CODE"
    if [ -f /tmp/dispatch_response.txt ]; then
      cat /tmp/dispatch_response.txt 2>/dev/null || true
    fi
    return 1
  fi
}

halt_order_flow() {
  echo "=== KILL SWITCH: HALTING ORDER FLOW ==="
  echo "Target: $REPO_OWNER/$TARGET_REPO"
  echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""

  local payload
  payload="{\"reason\": \"pre-deployment-halt\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"

  if dispatch_event "halt-order-flow" "$payload"; then
    echo ""
    echo "Order flow halt signal sent."
    echo "Execution service should now reject new orders and begin draining in-flight orders."
  else
    echo ""
    echo "WARNING: Failed to dispatch halt signal."
    echo "Manual intervention may be required."
    return 1
  fi
}

resume_order_flow() {
  echo "=== KILL SWITCH: RESUMING ORDER FLOW ==="
  echo "Target: $REPO_OWNER/$TARGET_REPO"
  echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo ""

  local payload
  payload="{\"reason\": \"post-deployment-resume\", \"timestamp\": \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\"}"

  if dispatch_event "resume-order-flow" "$payload"; then
    echo ""
    echo "Order flow resume signal sent."
    echo "Execution service should now accept new orders."
  else
    echo ""
    echo "WARNING: Failed to dispatch resume signal."
    echo "Manual intervention required to resume trading."
    return 1
  fi
}

check_drain_complete() {
  echo "=== KILL SWITCH: CHECKING DRAIN STATUS ==="
  echo "Timeout: ${TIMEOUT}s"
  echo ""

  # In a full implementation, this would poll the execution-service's
  # /drain-status or /orders/in-flight endpoint to verify all orders
  # have been filled, cancelled, or timed out before proceeding.
  #
  # Protocol:
  #   1. After halt-order-flow, the service stops accepting new orders
  #   2. In-flight orders continue to execute until filled/cancelled/timeout
  #   3. This function polls until in-flight count reaches 0 or timeout
  #   4. Only after drain completes should deployment proceed
  #
  # Stubbed: returns success after a brief wait.
  # When execution-service exposes /drain-status, replace with real polling.

  echo "NOTE: Drain check is currently stubbed."
  echo "When execution-service exposes /drain-status endpoint, this will poll until:"
  echo "  - In-flight order count reaches 0, OR"
  echo "  - Timeout of ${TIMEOUT}s is reached"
  echo ""

  ELAPSED=0
  POLL_INTERVAL=5
  while [ "$ELAPSED" -lt "$TIMEOUT" ]; do
    # Stub: assume drain completes after 10s
    if [ "$ELAPSED" -ge 10 ]; then
      echo "Drain check: complete (stubbed)"
      return 0
    fi
    echo "  Waiting for drain... (${ELAPSED}s / ${TIMEOUT}s)"
    sleep "$POLL_INTERVAL"
    ELAPSED=$((ELAPSED + POLL_INTERVAL))
  done

  echo "WARNING: Drain timeout reached (${TIMEOUT}s)"
  echo "In-flight orders may still be active. Proceeding with caution."
  return 1
}

case "$ACTION" in
  halt)
    halt_order_flow
    ;;
  resume)
    resume_order_flow
    ;;
  drain)
    check_drain_complete
    ;;
  *)
    echo "Unknown action: $ACTION"
    echo "Usage: trading-kill-switch.sh <halt|resume|drain> <GH_TOKEN> [REPO_OWNER] [TIMEOUT]"
    exit 1
    ;;
esac
