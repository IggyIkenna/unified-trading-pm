#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# enable_worker_watchdog.sh — SSM script to enable ORCHESTRATOR_WORKER_WATCHDOG_ENABLED on one VM.
#
# Usage (run via AWS SSM SendCommand on each target VM, one at a time):
#   bash scripts/orchestrator/enable_worker_watchdog.sh
#
# What it does:
#   1. Writes a systemd drop-in that sets ORCHESTRATOR_WORKER_WATCHDOG_ENABLED=true
#   2. daemon-reload + restart orchestrator
#   3. Reports current slot + tmux session state so operator can verify watchdog is armed.
#
# Roll sequentially — canary on vm-orchestrator first. Watch 1h for false-positive kills
# (a legitimately-thinking worker should NOT be killed). Expand to next VM only after
# confirming <5% false-positive rate on the canary.
#
# Safe to re-run — idempotent (drop-in is overwritten, restart is harmless).
set -euo pipefail

DROPIN_DIR="/etc/systemd/system/orchestrator.service.d"
DROPIN_FILE="$DROPIN_DIR/watchdog.conf"

echo "=== enable_worker_watchdog.sh ==="
echo "VM: $(hostname)"
echo "Drop-in: $DROPIN_FILE"

# Write the drop-in
mkdir -p "$DROPIN_DIR"
cat > "$DROPIN_FILE" <<'EOF'
[Service]
Environment=ORCHESTRATOR_WORKER_WATCHDOG_ENABLED=true
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
echo "--- systemd watchdog env ---"
systemctl show orchestrator --property=Environment | grep -i watchdog || echo "(WATCHDOG env not visible via systemctl show — check drop-in)"
echo "=== done ==="
