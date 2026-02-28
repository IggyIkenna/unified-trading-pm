#!/bin/bash
# ==============================================================================
# Q&A for Documentation Gaps - Interactive Spec Gathering
# ==============================================================================
#
# This script runs Q&A sessions for all 10 identified documentation gaps.
# After Q&A, it generates markdown docs based on answers.
#
# Usage:
#   bash qa-doc-gaps.sh [--gap NUMBER] [--all]
#
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CODEX_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
OUTPUT_DIR="$CODEX_ROOT/.qa-outputs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

mkdir -p "$OUTPUT_DIR"

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_question() {
    echo -e "${CYAN}[Q]${NC} $1"
}

# ==============================================================================
# Gap 1: Live Market Data Architecture
# ==============================================================================

qa_gap_1() {
    log_info "Gap 1: Live Market Data Architecture"
    echo ""

    cat > "$OUTPUT_DIR/gap-1-live-market-data.json" <<'EOF'
{
  "gap_id": 1,
  "title": "Live Market Data Architecture",
  "priority": "P0-critical",
  "target_file": "04-architecture/live-market-data-architecture.md",
  "questions": [
    {
      "id": "1.1",
      "question": "WebSocket Connection Pooling: How many connections per venue?",
      "prompt": "Options: (A) 1 connection per instrument, (B) 1 connection per venue (multiplex), (C) N connections with load balancing",
      "answer": ""
    },
    {
      "id": "1.2",
      "question": "Multi-subscriber fanout: How do multiple services subscribe to the same feed?",
      "prompt": "Options: (A) Pub/Sub topic per instrument, (B) In-memory fanout queue, (C) Redis Streams",
      "answer": ""
    },
    {
      "id": "1.3",
      "question": "Reconnection logic: How to recover from disconnect?",
      "prompt": "Options: (A) Full snapshot + replay, (B) Incremental catch-up from sequence number, (C) Just reconnect (lose some data)",
      "answer": ""
    },
    {
      "id": "1.4",
      "question": "Order book incremental updates: How to apply deltas?",
      "prompt": "Options: (A) Replace entire book on update, (B) Merge deltas (update/delete specific levels), (C) Use venue-specific format",
      "answer": ""
    },
    {
      "id": "1.5",
      "question": "Rate limit management: How to handle venue request quotas?",
      "prompt": "Example: Binance = 1200 requests/min. How to track and throttle?",
      "details": "Token bucket? Leaky bucket? Per-connection or global?",
      "answer": ""
    }
  ]
}
EOF

    # Interactive Q&A
    local answers_file="$OUTPUT_DIR/gap-1-answers.json"

    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}Gap 1: Live Market Data Architecture${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""

    # Question 1.1
    log_question "1.1: WebSocket Connection Pooling Strategy"
    echo "  Options:"
    echo "    A) 1 connection per instrument (simple, many connections)"
    echo "    B) 1 connection per venue with multiplexing (efficient, complex)"
    echo "    C) N connections with load balancing (scalable, moderate complexity)"
    echo ""
    echo -n "  Your choice (A/B/C): "
    read -r answer_1_1

    # Question 1.2
    echo ""
    log_question "1.2: Multi-subscriber Fanout Pattern"
    echo "  Options:"
    echo "    A) Pub/Sub topic per instrument (decoupled, durable)"
    echo "    B) In-memory fanout queue (fast, not durable)"
    echo "    C) Redis Streams (fast, durable, replay)"
    echo ""
    echo -n "  Your choice (A/B/C): "
    read -r answer_1_2

    # Question 1.3
    echo ""
    log_question "1.3: Reconnection & Snapshot Recovery"
    echo "  Options:"
    echo "    A) Full snapshot + replay missed messages (safest, slowest)"
    echo "    B) Incremental catch-up from last sequence number (fast, requires seq tracking)"
    echo "    C) Just reconnect, accept data loss (fastest, risky)"
    echo ""
    echo -n "  Your choice (A/B/C): "
    read -r answer_1_3

    # Question 1.4
    echo ""
    log_question "1.4: Order Book Incremental Updates"
    echo "  Options:"
    echo "    A) Replace entire book on every update (simple, bandwidth-heavy)"
    echo "    B) Merge deltas (update/delete specific price levels) (efficient, complex)"
    echo "    C) Use venue-specific format (optimized per venue)"
    echo ""
    echo -n "  Your choice (A/B/C): "
    read -r answer_1_4

    # Question 1.5
    echo ""
    log_question "1.5: Rate Limit Management"
    echo "  Example: Binance = 1200 requests/min, Deribit = 20 requests/sec"
    echo ""
    echo -n "  Strategy (token-bucket/leaky-bucket/sliding-window): "
    read -r answer_1_5

    echo -n "  Scope (per-connection/global): "
    read -r answer_1_5_scope

    # Save answers
    cat > "$answers_file" <<EOF
{
  "gap_id": 1,
  "answers": {
    "1.1": "$answer_1_1",
    "1.2": "$answer_1_2",
    "1.3": "$answer_1_3",
    "1.4": "$answer_1_4",
    "1.5": "$answer_1_5 ($answer_1_5_scope)"
  }
}
EOF

    log_success "Answers saved to $answers_file"
    echo ""
}

# ==============================================================================
# Gap 3: Risk Monitor Policy Engine
# ==============================================================================

qa_gap_3() {
    log_info "Gap 3: Risk Monitor Policy Engine"
    echo ""

    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}Gap 3: Risk Monitor Policy Engine${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════${NC}"
    echo ""

    log_question "3.1: Position Cap Thresholds by Risk Tier"
    echo "  We need 5 tiers (1 = lowest risk, 5 = highest risk)"
    echo ""

    echo "  Max Position Size (BTC equivalent):"
    echo -n "    Tier 1: "
    read -r tier1_pos
    echo -n "    Tier 2: "
    read -r tier2_pos
    echo -n "    Tier 3: "
    read -r tier3_pos
    echo -n "    Tier 4: "
    read -r tier4_pos
    echo -n "    Tier 5: "
    read -r tier5_pos

    echo ""
    echo "  Max Notional (USD):"
    echo -n "    Tier 1: "
    read -r tier1_notional
    echo -n "    Tier 2: "
    read -r tier2_notional
    echo -n "    Tier 3: "
    read -r tier3_notional
    echo -n "    Tier 4: "
    read -r tier4_notional
    echo -n "    Tier 5: "
    read -r tier5_notional

    echo ""
    log_question "3.2: Override Approval Workflow"
    echo -n "  Who can approve overrides? (comma-separated roles): "
    read -r approvers

    echo -n "  Approval timeout (minutes): "
    read -r approval_timeout

    echo -n "  Require multi-sig? (yes/no): "
    read -r multi_sig

    # Save answers
    cat > "$OUTPUT_DIR/gap-3-answers.json" <<EOF
{
  "gap_id": 3,
  "thresholds": {
    "tier1": {"position": "$tier1_pos", "notional": "$tier1_notional"},
    "tier2": {"position": "$tier2_pos", "notional": "$tier2_notional"},
    "tier3": {"position": "$tier3_pos", "notional": "$tier3_notional"},
    "tier4": {"position": "$tier4_pos", "notional": "$tier4_notional"},
    "tier5": {"position": "$tier5_pos", "notional": "$tier5_notional"}
  },
  "override": {
    "approvers": "$approvers",
    "timeout_minutes": $approval_timeout,
    "multi_sig": "$multi_sig"
  }
}
EOF

    log_success "Answers saved to $OUTPUT_DIR/gap-3-answers.json"
    echo ""
}

# ==============================================================================
# Main - Run All Q&A Sessions
# ==============================================================================

main() {
    echo "===================================================================="
    echo "Documentation Gaps Q&A - Interactive Spec Gathering"
    echo "===================================================================="
    echo ""
    echo "This will walk you through Q&A for all 10 identified gaps."
    echo "Your answers will be saved and used to generate documentation."
    echo ""
    echo "Gaps to cover:"
    echo "  1. Live Market Data Architecture (P0-critical)"
    echo "  2. Position Monitor Consumer Protocol (P0-critical)"
    echo "  3. Risk Monitor Policy Engine (P0-critical)"
    echo "  4. PnL Attribution Residual Thresholds (P0-critical)"
    echo "  5. Observability Metric Definitions (P1-high)"
    echo "  6. Service-to-Service Auth (P1-high)"
    echo "  7. Settlement Backend (P1-high)"
    echo "  8. Multi-Tenant Data Model (P2-medium)"
    echo "  9. Disaster Recovery Automation (P3-low)"
    echo "  10. Cloud Agent Orchestration (P3-low)"
    echo ""
    echo -e "${YELLOW}This will take ~30-45 minutes. Ready to start? (yes/no)${NC}"
    read -r confirm

    if [[ "$confirm" != "yes" ]]; then
        log_info "Cancelled"
        exit 0
    fi

    echo ""

    # Run Q&A for critical gaps
    qa_gap_1
    qa_gap_3

    # TODO: Add qa_gap_2, qa_gap_4, etc.

    log_success "Q&A complete! Answers saved to $OUTPUT_DIR/"
    echo ""
    echo "===================================================================="
    echo "Next Steps"
    echo "===================================================================="
    echo "1. Review answers: ls $OUTPUT_DIR/"
    echo "2. Generate docs: bash generate-docs-from-qa.sh"
    echo "3. Run delta audit: bash run-delta-audit-all-services.sh"
    echo ""
}

main "$@"
