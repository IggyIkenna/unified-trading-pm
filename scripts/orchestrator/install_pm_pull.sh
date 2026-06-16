#!/usr/bin/env bash
# install_pm_pull.sh — Install pm-pull.timer + regen-interval drop-in on an orchestrator VM.
#
# Installs:
#   1. /usr/local/bin/pm-pull-ff.sh          — smart FF-pull script (from PM repo)
#   2. pm-pull.service + pm-pull.timer       — pull every 5 min
#   3. orchestrator regen-interval drop-in   — tighten PlanRegenLoop to 30 min
#
# Plan: unified-trading-pm/plans/active/plan_hygiene_silent_failure_capture_2026_05_29.md § Phase 6
#
# Usage (run via AWS SSM SendCommand on each target epic VM):
#   bash /home/ubuntu/unified-trading-system-repos/unified-trading-pm/scripts/orchestrator/install_pm_pull.sh
#
# Prerequisites:
#   - unified-trading-pm cloned at /home/ubuntu/unified-trading-system-repos/unified-trading-pm
#   - ubuntu user exists
#   - systemd available
#
# Safe to re-run — idempotent.
set -euo pipefail

PM_REPO="/home/ubuntu/unified-trading-system-repos/unified-trading-pm"
AO_REPO="/home/ubuntu/unified-trading-system-repos/agent-orchestrator"
PULL_SCRIPT_SRC="$PM_REPO/scripts/dev/pm-pull-ff.sh"
PULL_SCRIPT_DST="/usr/local/bin/pm-pull-ff.sh"
SYSTEMD_DIR="/etc/systemd/system"
ORCH_DROPIN_DIR="/etc/systemd/system/orchestrator.service.d"
ORCH_REGEN_DROPIN="$ORCH_DROPIN_DIR/regen-interval.conf"

echo "=== install_pm_pull.sh ==="
echo "Host: $(hostname)"
echo "PM repo: $PM_REPO"

# --- 1. Ensure PM repo is up to date ---
if [ -d "$PM_REPO" ]; then
    cd "$PM_REPO"
    sudo -u ubuntu git fetch --quiet origin live-defi-rollout 2>&1 || echo "(fetch failed — continuing)"
    sudo -u ubuntu git merge --ff-only --quiet origin/live-defi-rollout 2>&1 || echo "(non-FF merge needed — PM may be behind)"
    echo "PM repo: $(git rev-parse --short HEAD)"
else
    echo "ERROR: PM repo not found at $PM_REPO"
    exit 1
fi

# --- 2. Install pm-pull-ff.sh ---
cp "$PULL_SCRIPT_SRC" "$PULL_SCRIPT_DST"
chmod +x "$PULL_SCRIPT_DST"
echo "Installed: $PULL_SCRIPT_DST"

# --- 2b. One-shot: regen per-root agent symlinks (top-level CLAUDE.md + skills) immediately ---
# pm-pull-ff.sh only regenerates on a FF *advance*; if the VM is already at latest, the symlinks
# would otherwise wait for the next PM change. Run the fan-out once here so a fresh rollout makes the
# root CLAUDE.md + skills links live now. Best-effort (always exits 0); run as ubuntu for ownership.
REGEN_SCRIPT="$PM_REPO/scripts/dev/regen-agent-symlinks.sh"
if [ -f "$REGEN_SCRIPT" ]; then
    sudo -u ubuntu bash "$REGEN_SCRIPT" 2>&1 | sed 's/^/  /' || true
    echo "Regenerated per-root agent symlinks"
fi

# --- 3. Write pm-pull.service ---
cat > "$SYSTEMD_DIR/pm-pull.service" <<'EOF'
[Unit]
Description=pm-pull — fast-forward unified-trading-pm to live-defi-rollout
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/pm-pull-ff.sh
StandardOutput=journal
StandardError=journal
User=root
EOF

echo "Written: $SYSTEMD_DIR/pm-pull.service"

# --- 4. Write pm-pull.timer ---
cat > "$SYSTEMD_DIR/pm-pull.timer" <<'EOF'
[Unit]
Description=pm-pull timer — pull unified-trading-pm every 5 minutes

[Timer]
OnBootSec=60
OnUnitActiveSec=300
AccuracySec=10
Persistent=true

[Install]
WantedBy=timers.target
EOF

echo "Written: $SYSTEMD_DIR/pm-pull.timer"

# --- 5. Enable and start timer ---
systemctl daemon-reload
systemctl enable pm-pull.timer
systemctl start pm-pull.timer
systemctl start pm-pull.service  # immediate first pull

echo "pm-pull.timer enabled and started"
systemctl status pm-pull.timer --no-pager | head -10

# --- 6. Regen-interval drop-in (tighten from 6h to 30 min) ---
if systemctl list-unit-files | grep -q "^orchestrator.service"; then
    mkdir -p "$ORCH_DROPIN_DIR"
    cat > "$ORCH_REGEN_DROPIN" <<'EOF'
[Service]
Environment=ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS=1800
EOF
    echo "Written: $ORCH_REGEN_DROPIN"
    systemctl daemon-reload
    systemctl restart orchestrator
    echo "orchestrator restarted with ORCHESTRATOR_PLAN_REGEN_INTERVAL_SECONDS=1800"
    systemctl show orchestrator --property=Environment | grep -i regen || echo "(regen env — check drop-in)"
else
    echo "(orchestrator.service not found — skipping regen-interval drop-in)"
fi

echo ""
echo "--- Verification ---"
echo "pm-pull.timer: $(systemctl is-active pm-pull.timer 2>/dev/null || echo unknown)"
journalctl -u pm-pull.service -n 5 --no-pager 2>/dev/null || true
echo "=== done ==="
