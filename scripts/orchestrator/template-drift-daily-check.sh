#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# template-drift-daily-check.sh — daily workflow-template drift verdict refresh (rollout-ratchet
# panel backend, wired 2026-08-17 per
# plans/active/issues/rollout_ratchet_panel_ui_only_mis_scoped_needs_backend_2026_08_17.md).
#
# WHY: monitoring_control_plane_master_2026_06_10.md's rollout-ratchet dashboard panel needs a
# live per-repo workflow-template-drift signal. detect_template_drift.py has a --json mode but is
# wired ONLY as a pre-commit/QG gate — no scheduled fleet-wide run exists, so no API-readable
# status exists anywhere deployment-api could read.
#
# HOW: detect_template_drift.py reads every repo's scripts/quality-gates.sh via a pure LOCAL file
# read (_qg_path(workspace_root, repo_name).read_text()) — no gh-api fallback the way
# assert_version_coherence.py has. A bare ubuntu-latest GH Actions runner only checks out the PM
# repo itself, so it cannot run this fleet-wide (same constraint that made
# qg-baseline-daily-promote.sh a systemd timer instead of a workflow). This VM's root PM checkout
# has the full multi-repo workspace as siblings, so a systemd timer here is the correct home.
# Runs write_template_drift_verdicts.py (the driver), which subprocess-invokes
# detect_template_drift.py --json and CAS-writes one Firestore doc per repo (collection
# template_drift_verdicts) via verdict_store.py.
#
# Usage (systemd — see install_template_drift_daily_check.sh):
#   bash scripts/orchestrator/template-drift-daily-check.sh
#
# Env overrides:
#   WORKSPACE_ROOT — root containing the unified-trading-pm checkout (default matches every other
#                    orchestrator systemd unit, e.g. qg-baseline-daily-promote.sh)
#
# SSOT: plans/active/issues/rollout_ratchet_panel_ui_only_mis_scoped_needs_backend_2026_08_17.md,
#       plans/active/monitoring_control_plane_master_2026_06_10.md (rollout-ratchet panel).

set -uo pipefail # deliberately NOT -e: one repo's Firestore write failing must not abort the run

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/home/ubuntu/unified-trading-system-repos}"
PM_DIR="${WORKSPACE_ROOT}/unified-trading-pm"
DRIVER_SCRIPT="${PM_DIR}/scripts/cicd/write_template_drift_verdicts.py"

if [[ ! -f "$DRIVER_SCRIPT" ]]; then
    echo "FATAL: ${DRIVER_SCRIPT} not found" >&2
    exit 1
fi
command -v python3 >/dev/null 2>&1 || {
    echo "FATAL: python3 required" >&2
    exit 1
}

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] template-drift-daily-check: workspace_root=${WORKSPACE_ROOT}"
python3 -c "import google.cloud.firestore" 2>/dev/null ||
    python3 -m pip install --quiet "google-cloud-firestore>=2,<3"
(cd "$PM_DIR" && python3 "$DRIVER_SCRIPT")
STATUS=$?
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] template-drift-daily-check: exit=${STATUS}"
exit "$STATUS"
