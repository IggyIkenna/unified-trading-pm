#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# enable_prune_stale.sh — SSM script to enable ORCHESTRATOR_REGEN_PRUNE_STALE on one VM.
#
# Usage (run via AWS SSM SendCommand on each target VM, one at a time):
#   bash scripts/orchestrator/enable_prune_stale.sh
#
# What it does:
#   1. Writes a systemd drop-in that sets ORCHESTRATOR_REGEN_PRUNE_STALE=true
#   2. daemon-reload + restart orchestrator
#   3. Waits one regen cycle (default 60 s) then prints before/after queued count
#      from state.db so the operator can confirm the prune ran.
#
# Safe to re-run — idempotent (drop-in is overwritten, restart is harmless).
set -euo pipefail

DROPIN_DIR="/etc/systemd/system/orchestrator.service.d"
DROPIN_FILE="$DROPIN_DIR/prune-stale.conf"
STATE_DB="${ORCHESTRATOR_STATE_DB:-/opt/orchestrator/data/state/state.db}"
REGEN_INTERVAL="${ORCHESTRATOR_REGEN_INTERVAL_S:-60}"

echo "=== enable_prune_stale.sh ==="
echo "VM: $(hostname)"
echo "Drop-in: $DROPIN_FILE"
echo "state.db: $STATE_DB"

# Record before-count
if [ -f "$STATE_DB" ]; then
    BEFORE=$(sqlite3 "$STATE_DB" "SELECT COUNT(*) FROM tasks WHERE status='queued' AND dispatched_to IS NULL;" 2>/dev/null || echo "N/A")
else
    BEFORE="N/A (state.db not found at $STATE_DB)"
fi
echo "Queued rows BEFORE: $BEFORE"

# Write the drop-in
mkdir -p "$DROPIN_DIR"
cat > "$DROPIN_FILE" <<'EOF'
[Service]
Environment=ORCHESTRATOR_REGEN_PRUNE_STALE=true
EOF

echo "Written: $DROPIN_FILE"
cat "$DROPIN_FILE"

# Reload and restart
systemctl daemon-reload
systemctl restart orchestrator
echo "orchestrator restarted"

# Wait for one regen tick
WAIT=$(( REGEN_INTERVAL + 10 ))
echo "Waiting ${WAIT}s for regen tick..."
sleep "$WAIT"

# After-count
if [ -f "$STATE_DB" ]; then
    AFTER=$(sqlite3 "$STATE_DB" "SELECT COUNT(*) FROM tasks WHERE status='queued' AND dispatched_to IS NULL;" 2>/dev/null || echo "N/A")
else
    AFTER="N/A"
fi
echo "Queued rows AFTER:  $AFTER"
echo "=== done ==="
