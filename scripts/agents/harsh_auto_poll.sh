#!/usr/bin/env bash
# harsh_auto_poll.sh — mechanical orchestrator poller for Harsh side
#
# Purpose: do the boring 80% of orchestrator polling without invoking Claude.
# Scans slot ping files for new activity, performs mechanical LEDGER flips,
# logs cycle results, and emits operator-visible alerts ONLY when human
# judgment is needed (BLOCKED ping, BIG finding, DONE-without-queue).
#
# Reduces main-orchestrator (Claude) invocations by ~80% — Claude only
# spawned for: cross-side handoffs, BLOCKED triage, BIG findings.
#
# Schedule via cron (~3 min cadence) OR run manually as a polling loop.
#
# Usage:
#   bash scripts/agents/harsh_auto_poll.sh           # one-shot poll
#   bash scripts/agents/harsh_auto_poll.sh --watch   # loop every 3 min until killed
#   bash scripts/agents/harsh_auto_poll.sh --dry-run # show what would change, no edits
#
# Exit codes:
#   0 = clean poll, no action needed
#   1 = mechanical flips applied (LEDGER updated)
#   2 = operator attention needed (BLOCKED ping / DONE-no-queue / cross-side)
#   3 = error (git failure, missing files, etc.)
#
# Status: DRAFT — review with operator before cron-scheduling.

set -euo pipefail

WORKSPACE_ROOT="${UNIFIED_TRADING_WORKSPACE_ROOT:-/home/hk/unified-trading-system-repos}"
PM_REPO="${WORKSPACE_ROOT}/unified-trading-pm"
PINGS_DIR="${PM_REPO}/harsh_orchestrator/pings"
LEDGER="${PM_REPO}/harsh_orchestrator/LEDGER.md"
CROSS_SIDE="${PM_REPO}/plans/active/_agent_pings.md"
LOG_DIR="${PM_REPO}/harsh_orchestrator/auto_poll_log"
LOG_FILE="${LOG_DIR}/$(date -u '+%Y-%m-%d').log"
STATE_FILE="${LOG_DIR}/.last_seen_state"

DRY_RUN=false
WATCH=false
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=true ;;
    --watch) WATCH=true ;;
  esac
done

mkdir -p "$LOG_DIR"

log() {
  local ts="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  echo "[$ts] $*" | tee -a "$LOG_FILE"
}

alert_operator() {
  # Append to a watch file the operator can tail (or set up a Telegram bot hook)
  local ts="$(date -u '+%Y-%m-%d %H:%M:%S UTC')"
  echo "[$ts] 🚨 OPERATOR ALERT: $*" | tee -a "$LOG_FILE" >&2
  echo "[$ts] $*" >> "${LOG_DIR}/operator_alerts.log"
}

run_poll() {
  log "Poll cycle start"
  local needs_main=0
  local mechanical_edits=0

  # 1. Fetch latest origin/live-defi-rollout (read-only — no rebase, no push)
  cd "$PM_REPO"
  if ! git fetch origin live-defi-rollout --quiet 2>/dev/null; then
    log "ERROR: git fetch failed; skipping cycle"
    return 3
  fi

  local incoming
  incoming=$(git log --oneline HEAD..origin/live-defi-rollout 2>/dev/null | wc -l)
  if [ "$incoming" -gt 0 ]; then
    log "Incoming commits: $incoming"
    if [ "$DRY_RUN" = false ]; then
      # FF-only pull. If non-FF, leave for human main to resolve.
      if git merge-base --is-ancestor HEAD origin/live-defi-rollout 2>/dev/null; then
        git pull --ff-only origin live-defi-rollout --quiet 2>&1 | tail -3 | while read l; do log "  $l"; done
        log "Fast-forwarded local to origin/live-defi-rollout"
      else
        alert_operator "Local HEAD has commits NOT on origin/live-defi-rollout — auto-poll cannot FF; needs human main to rebase + push"
        return 2
      fi
    fi
  fi

  # 2. Scan slot pings for NEW activity since last poll
  for slot in 2 3 4 5 6 7 8 9; do
    local ping_file="${PINGS_DIR}/slot_${slot}.md"
    [ -f "$ping_file" ] || continue

    # Get last line (most recent ping)
    local last_line
    last_line=$(tail -1 "$ping_file")

    # State signature: hash of last line
    local sig
    sig=$(echo -n "$last_line" | sha1sum | cut -c1-12)
    local state_key="slot_${slot}"
    local prev_sig
    prev_sig=$(grep "^${state_key}=" "$STATE_FILE" 2>/dev/null | cut -d= -f2 || echo "")

    if [ "$sig" = "$prev_sig" ]; then
      continue  # No change since last poll
    fi

    log "Slot ${slot}: new ping detected (sig: $prev_sig → $sig)"

    # Classify the new ping
    case "$last_line" in
      *"[main → slot"*|*"[main →"*)
        # This is a direction ping from main — ignore, slot will act on it
        log "  → main-directed ping (no auto-action)"
        ;;
      *"STARTED"*|*"started"*)
        # STARTED ping — mechanical flip in LEDGER from 🟡 AWAITING to 🟢 IN FLIGHT
        log "  → STARTED ping; flipping LEDGER row"
        if [ "$DRY_RUN" = false ]; then
          # Find the slot row and replace state column
          # Pattern: "| <slot> | **theme** | 🟡 AWAITING..."  →  "| <slot> | **theme** | 🟢 IN FLIGHT..."
          # We use sed with a targeted pattern. Slot row matches "| <slot> |".
          if grep -q "^| ${slot} | " "$LEDGER"; then
            local current_state
            current_state=$(grep "^| ${slot} | " "$LEDGER" | head -1)
            if echo "$current_state" | grep -q "🟡 AWAITING"; then
              sed -i "s|^\(| ${slot} | [^|]* | \)🟡 AWAITING[^|]*|\1🟢 IN FLIGHT (auto-flipped by poll $(date -u '+%H:%M UTC'))|" "$LEDGER"
              mechanical_edits=1
              log "  → LEDGER row flipped to 🟢 IN FLIGHT"
            else
              log "  → LEDGER already not in AWAITING; no flip needed"
            fi
          fi
        fi
        ;;
      *"DONE"*|*"done"*|*"✅"*)
        # DONE ping — needs main judgment for next-task pick. Alert operator.
        log "  → DONE ping detected"
        alert_operator "Slot ${slot} pinged DONE. Main needs to: (a) verify SHAs, (b) pick next item from slot ${slot}'s continuation prompt queue OR BACKLOG, (c) drop direction ping."
        needs_main=1
        ;;
      *"BLOCKED"*|*"blocked"*|*"🛑"*)
        # BLOCKED ping — MUST surface to operator immediately
        log "  → BLOCKED ping detected"
        alert_operator "Slot ${slot} BLOCKED. Triage required. Last ping: ${last_line:0:200}"
        needs_main=1
        ;;
      *"🚨"*|*"BIG"*|*"CRITICAL"*|*"P0"*)
        # BIG finding — surface immediately
        log "  → BIG finding detected"
        alert_operator "Slot ${slot} BIG finding. Read ping immediately: ${last_line:0:200}"
        needs_main=1
        ;;
      *)
        log "  → unclassified ping (operator may want to review)"
        ;;
    esac

    # Persist new state sig
    if [ "$DRY_RUN" = false ]; then
      grep -v "^${state_key}=" "$STATE_FILE" 2>/dev/null > "${STATE_FILE}.tmp" || true
      echo "${state_key}=${sig}" >> "${STATE_FILE}.tmp"
      mv "${STATE_FILE}.tmp" "$STATE_FILE"
    fi
  done

  # 3. Check cross-side ping ledger for new Ikenna → harsh-main pings
  if [ -f "$CROSS_SIDE" ]; then
    local cross_sig
    cross_sig=$(tail -50 "$CROSS_SIDE" | sha1sum | cut -c1-12)
    local prev_cross
    prev_cross=$(grep "^cross_side=" "$STATE_FILE" 2>/dev/null | cut -d= -f2 || echo "")
    if [ "$cross_sig" != "$prev_cross" ]; then
      log "Cross-side ledger changed"
      # Look for "ikenna" → "harsh" patterns in the tail
      if tail -50 "$CROSS_SIDE" | grep -qE "ikenna[a-z-]* → harsh"; then
        alert_operator "Cross-side: new ikenna → harsh ping in plans/active/_agent_pings.md tail. Main triage needed."
        needs_main=1
      fi
      if [ "$DRY_RUN" = false ]; then
        grep -v "^cross_side=" "$STATE_FILE" 2>/dev/null > "${STATE_FILE}.tmp" || true
        echo "cross_side=${cross_sig}" >> "${STATE_FILE}.tmp"
        mv "${STATE_FILE}.tmp" "$STATE_FILE"
      fi
    fi
  fi

  # 4. Commit + push mechanical LEDGER flips if any
  if [ "$mechanical_edits" -eq 1 ] && [ "$DRY_RUN" = false ]; then
    cd "$PM_REPO"
    if [ -n "$(git status --porcelain harsh_orchestrator/LEDGER.md)" ]; then
      git add harsh_orchestrator/LEDGER.md
      git commit -m "chore(orchestrator): auto-poll LEDGER flip — slot STARTED detected" --quiet
      if ! git push origin live-defi-rollout --quiet 2>/dev/null; then
        log "Push rejected; will try rebase-on-reject"
        git fetch origin live-defi-rollout --quiet
        git rebase origin/live-defi-rollout --quiet || {
          alert_operator "Auto-poll rebase failed on LEDGER flip — needs human triage"
          git rebase --abort 2>/dev/null || true
          return 3
        }
        git push origin live-defi-rollout --quiet || {
          alert_operator "Auto-poll push failed after rebase"
          return 3
        }
      fi
      log "LEDGER flip pushed to origin"
    fi
  fi

  # 5. Exit code semantics
  log "Poll cycle complete (needs_main=$needs_main, mechanical_edits=$mechanical_edits)"
  if [ "$needs_main" -eq 1 ]; then
    return 2
  elif [ "$mechanical_edits" -eq 1 ]; then
    return 1
  else
    return 0
  fi
}

# Main entry point
if [ "$WATCH" = true ]; then
  log "Starting watch mode (3-min cadence)"
  while true; do
    run_poll || exit_code=$?
    sleep 180  # 3 minutes
  done
else
  run_poll
fi
