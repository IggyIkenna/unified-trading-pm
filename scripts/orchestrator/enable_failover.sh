#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# enable_failover.sh — SSM script to enable ORCHESTRATOR_FAILOVER_ENABLED on ONE VM.
#
# IMPORTANT: Run this on vm-orchestrator ONLY.
# FailoverLoop is designed as a single decision source — enabling it on multiple
# VMs simultaneously causes them to race on the same failover decisions.
#
# Usage (run via AWS SSM SendCommand on vm-orchestrator):
#   bash scripts/orchestrator/enable_failover.sh
#
# What it does:
#   1. Writes a systemd drop-in that sets ORCHESTRATOR_FAILOVER_ENABLED=true
#   2. daemon-reload + restart orchestrator
#   3. Reports current slot + tmux session state so operator can verify.
#
# To verify FailoverLoop is armed: check orchestrator logs for
#   "FailoverLoop started (interval=..." within ~10s of restart.
#
# To simulate offline host: stop sending heartbeats from the target VM for
#   > 10 min, then watch logs for "failover: re-routed N task(s)".
#
# Safe to re-run — idempotent (drop-in is overwritten, restart is harmless).
set -euo pipefail

DROPIN_DIR="/etc/systemd/system/orchestrator.service.d"
DROPIN_FILE="$DROPIN_DIR/failover.conf"

echo "=== enable_failover.sh ==="
echo "VM: $(hostname)"
echo "Drop-in: $DROPIN_FILE"
echo "WARNING: only run on vm-orchestrator — single failover decision source"

# Write the drop-in
mkdir -p "$DROPIN_DIR"
cat > "$DROPIN_FILE" <<'EOF'
[Service]
Environment=ORCHESTRATOR_FAILOVER_ENABLED=true
EOF

echo "Written: $DROPIN_FILE"
cat "$DROPIN_FILE"

# Reload and restart
systemctl daemon-reload
systemctl restart orchestrator
echo "orchestrator restarted"

# Report current slot + tmux state
echo ""
echo "--- Slot / tmux state after restart ---"
tmux ls 2>/dev/null | grep "orch-slot" || echo "(no orch-slot tmux sessions)"
echo "--- systemd failover env ---"
systemctl show orchestrator --property=Environment | grep -i failover || echo "(FAILOVER env not visible via systemctl show — check drop-in)"
echo "=== done ==="
