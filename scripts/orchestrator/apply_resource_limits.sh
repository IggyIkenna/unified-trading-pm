#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# apply_resource_limits.sh — Apply systemd MemoryHigh/MemoryMax/TasksMax limits
# to orchestrator.service on the central API host (i-0c9b283b31d6b5ca7).
#
# Context: pytest QG runs on this host consumed 32-57 GB RAM, causing OOM events
# and StatusCheckFailed_Instance impairments. These limits ensure OOM-killer fires
# on orchestrator *before* the host goes impaired — orchestrator restart is fast
# vs a full host reboot.
#
# Host: m8i.4xlarge (64 GB RAM). Limits sized for 75% / 87.5% of host RAM.
#   MemoryHigh=48G  — soft ceiling; kernel starts reclaiming aggressively
#   MemoryMax=56G   — hard ceiling; OOM-killer fires on orchestrator if exceeded
#   TasksMax=10000  — guards against process/thread leak
#
# Plan: unified-trading-pm/plans/active/api_host_chronic_impairment_2026_05_29.md § Phase 5
#
# Usage (run via AWS SSM SendCommand on i-0c9b283b31d6b5ca7):
#   bash scripts/orchestrator/apply_resource_limits.sh
#
# Safe to re-run — idempotent (drop-in is overwritten, restart is harmless).
# Also apply to the orch-watchdog service (Phase 5 task 2).
set -euo pipefail

DROPIN_DIR="/etc/systemd/system/orchestrator.service.d"
DROPIN_FILE="$DROPIN_DIR/resource-limits.conf"

WATCHDOG_DROPIN_DIR="/etc/systemd/system/orch-watchdog.service.d"
WATCHDOG_DROPIN_FILE="$WATCHDOG_DROPIN_DIR/resource-limits.conf"

echo "=== apply_resource_limits.sh ==="
echo "Host: $(hostname)"
echo "orchestrator drop-in: $DROPIN_FILE"

# --- orchestrator.service limits ---
mkdir -p "$DROPIN_DIR"
cat > "$DROPIN_FILE" <<'EOF'
[Service]
# Memory limits for orchestrator on m8i.4xlarge (64 GB host).
# MemoryHigh = soft ceiling — kernel reclaims aggressively above this.
# MemoryMax  = hard ceiling — OOM-killer fires on orchestrator, NOT host.
# Trade: orchestrator restart (~10s) vs full host reboot (~3 min + StatusCheckFailed).
MemoryHigh=48G
MemoryMax=56G
TasksMax=10000
EOF

echo "Written: $DROPIN_FILE"
cat "$DROPIN_FILE"

# --- orch-watchdog.service limits (if service exists) ---
if systemctl list-unit-files | grep -q "orch-watchdog"; then
    mkdir -p "$WATCHDOG_DROPIN_DIR"
    cat > "$WATCHDOG_DROPIN_FILE" <<'EOF'
[Service]
# Keep watchdog memory-bounded so it can't itself trigger the OOM it monitors.
MemoryHigh=256M
MemoryMax=512M
TasksMax=50
EOF
    echo "Written: $WATCHDOG_DROPIN_FILE"
    cat "$WATCHDOG_DROPIN_FILE"
else
    echo "(orch-watchdog.service not found — skipping watchdog drop-in)"
fi

# Reload and restart
systemctl daemon-reload
systemctl restart orchestrator
echo "orchestrator restarted"

# Verify
echo ""
echo "--- Memory limits active ---"
systemctl show orchestrator --property=MemoryHigh,MemoryMax,TasksMax 2>/dev/null || true
echo ""
echo "--- Current memory usage ---"
systemctl status orchestrator --no-pager 2>/dev/null | grep -E "(Memory|Tasks)" || echo "(check journalctl for current usage)"
echo "=== done ==="
