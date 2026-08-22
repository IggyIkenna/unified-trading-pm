#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# enable_s3_snapshot.sh — SSM script to enable ORCHESTRATOR_S3_BUCKET on one VM.
#
# Activates the S3 state-snapshot mirror (server/gcs_sync.py upload_state_to_s3 +
# backup_sqlite_to_s3, shipped agent-orchestrator@57dc8c2). No-op in code unless
# this env var is set — this script sets it + restarts so the SnapshotLoop starts
# writing to S3. Closes the AWS disaster-recovery gap.
#
# Usage (run via AWS SSM SendCommand on each target VM, one at a time):
#   bash scripts/orchestrator/enable_s3_snapshot.sh
#
# Requires: the VM's agent-orchestrator HEAD includes @57dc8c2 (the S3 functions).
#   Verify first with verify_fleet_autonomy_health.sh (behind=0). If a VM is behind,
#   pm-pull it before enabling, else the env is set but the code no-ops it.
#
# Override bucket via ORCHESTRATOR_S3_BUCKET_NAME env (default below).
# Safe to re-run — idempotent (drop-in overwritten, restart harmless).
set -euo pipefail

BUCKET="${ORCHESTRATOR_S3_BUCKET_NAME:-uts-orchestrator-state-427895769566}"
DROPIN_DIR="/etc/systemd/system/orchestrator.service.d"
DROPIN_FILE="$DROPIN_DIR/s3-snapshot.conf"

echo "=== enable_s3_snapshot.sh ==="
echo "VM: $(hostname)"
echo "Bucket: $BUCKET"
echo "Drop-in: $DROPIN_FILE"

mkdir -p "$DROPIN_DIR"
cat > "$DROPIN_FILE" <<EOF
[Service]
Environment=ORCHESTRATOR_S3_BUCKET=$BUCKET
EOF

echo "Written:"; cat "$DROPIN_FILE"

systemctl daemon-reload
systemctl restart orchestrator
echo "orchestrator restarted"

echo ""
echo "--- systemd S3 env after restart ---"
systemctl show orchestrator --property=Environment | tr ' ' '\n' | grep -i ORCHESTRATOR_S3_BUCKET \
  || echo "(S3 env not visible via systemctl show — check drop-in)"
echo "=== done ==="
