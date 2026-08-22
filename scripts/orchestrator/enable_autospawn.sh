#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# enable_autospawn.sh — SSM script to enable ORCHESTRATOR_AUTOSPAWN_ENABLED on one VM.
#
# Usage (run via AWS SSM SendCommand on each target VM, one at a time):
#   bash scripts/orchestrator/enable_autospawn.sh
#
# What it does:
#   1. Writes a systemd drop-in that sets ORCHESTRATOR_AUTOSPAWN_ENABLED=true
#   2. daemon-reload + restart orchestrator
#   3. Reports current slot + tmux session state so operator can verify autospawn is armed.
#
# To verify autospawn fires: after enabling, kill a slot's worker:
#   tmux kill-session -t orch-slot-1
# Then watch orchestrator logs for "autospawn_succeeded" within ~60s.
#
# Safe to re-run — idempotent (drop-in is overwritten, restart is harmless).
set -euo pipefail

DROPIN_DIR="/etc/systemd/system/orchestrator.service.d"
DROPIN_FILE="$DROPIN_DIR/autospawn.conf"

echo "=== enable_autospawn.sh ==="
echo "VM: $(hostname)"
echo "Drop-in: $DROPIN_FILE"

# Write the drop-in
mkdir -p "$DROPIN_DIR"
cat > "$DROPIN_FILE" <<'EOF'
[Service]
Environment=ORCHESTRATOR_AUTOSPAWN_ENABLED=true
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
echo "--- systemd autospawn env ---"
systemctl show orchestrator --property=Environment | grep -i autospawn || echo "(AUTOSPAWN env not visible via systemctl show — check drop-in)"
echo "=== done ==="
