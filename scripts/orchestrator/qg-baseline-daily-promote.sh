#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
#
# qg-baseline-daily-promote.sh — daily QG resource-baseline freshness promotion (governor
# Trigger 3, wired 2026-08-16 per ci_satellite_ao_dispatch_batch15_2026_08_16.md).
#
# WHY: qg_host_adaptive_resource_governor_2026_07_14.md's "baseline freshness loop" — each
# run's observed peak-RSS should promote into the committed
# scripts/dev/qg_resource_baseline.json DAILY, so no repo silently outgrows its reservation
# and OOMs against a stale committed value. Batch13 wired governor Triggers 1-2 (per-run
# RSS-cap overrun Slack alert, host-RAM-pressure abort); this closes Trigger 3.
#
# HOW: runs the existing measure-qg-baseline.sh (real, full quality-gates.sh runs — the SAME
# tool used for every manual re-baseline) across every repo the committed baseline already
# tracks, env=vm (this VM). measure-qg-baseline.sh itself now carries the anomaly guard
# (2026-08-16): a repo whose freshly observed peak is >=20% above its committed value is NOT
# silently promoted — it fires a Slack WARNING via qg-host-governor.sh's
# _qg_governor_slack_alert() and leaves the committed baseline untouched, so a real
# regression (or a measurement fluke) gets a human look instead of a silent bump. --force
# (never passed here) is the deliberate-manual-re-baseline bypass — this daily job never
# uses it, by design.
#
# jobs=3 mirrors qg_host_adaptive_resource_governor_2026_07_14.md's own cross-host table
# ("61 GB worker VM ... ~3 heavy" concurrency) — daily promotion competes with live worker
# QG traffic on the same host, so it stays inside the governor's own admission gates rather
# than trying to run every repo at once; the governor's reservation ledger still admits/queues
# each repo's run exactly as it would any other quality-gates.sh caller.
#
# Usage (systemd — see install_qg_baseline_daily_promote.sh):
#   bash scripts/orchestrator/qg-baseline-daily-promote.sh
#
# Manual test (safe — real QG runs, --no-fix, never mutates the working tree; a repo's own
# baseline only ever moves via the anomaly-guarded merge):
#   bash scripts/orchestrator/qg-baseline-daily-promote.sh
#
# Env overrides:
#   WORKSPACE_ROOT   — root containing the unified-trading-pm checkout (default matches every
#                       other orchestrator systemd unit, e.g. ldr-to-main-promote-heartbeat.sh)
#   QG_BASELINE_JOBS — wave concurrency passed to measure-qg-baseline.sh --jobs (default 3)
#
# SSOT: plans/active/qg_host_adaptive_resource_governor_2026_07_14.md ("Baseline freshness
#       loop"), plans/active/ci_satellite_ao_dispatch_batch15_2026_08_16.md.

set -uo pipefail # deliberately NOT -e: one repo's measurement failing must not skip the rest

WORKSPACE_ROOT="${WORKSPACE_ROOT:-/home/ubuntu/unified-trading-system-repos}"
PM_DIR="${WORKSPACE_ROOT}/unified-trading-pm"
MEASURE_SCRIPT="${PM_DIR}/scripts/dev/measure-qg-baseline.sh"
BASELINE_JSON="${PM_DIR}/scripts/dev/qg_resource_baseline.json"
JOBS="${QG_BASELINE_JOBS:-3}"

if [[ ! -f "$MEASURE_SCRIPT" ]]; then
    echo "FATAL: ${MEASURE_SCRIPT} not found" >&2
    exit 1
fi
if [[ ! -f "$BASELINE_JSON" ]]; then
    echo "FATAL: ${BASELINE_JSON} not found" >&2
    exit 1
fi
command -v python3 >/dev/null 2>&1 || { echo "FATAL: python3 required" >&2; exit 1; }

# Repo list = every repo the committed baseline already tracks. A repo only ever JOINS this
# set via a deliberate manual --force re-baseline of measure-qg-baseline.sh — never
# auto-added here — so onboarding a new repo's baseline stays an explicit, reviewed action.
REPOS="$(python3 -c "
import json
d = json.load(open('${BASELINE_JSON}'))
print(' '.join(sorted(d.keys())))
")"
if [[ -z "$REPOS" ]]; then
    echo "FATAL: no repos found in ${BASELINE_JSON}" >&2
    exit 1
fi

echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] qg-baseline-daily-promote: env=vm jobs=${JOBS} repos=${REPOS}"
bash "$MEASURE_SCRIPT" --env vm --repos "$REPOS" --jobs "$JOBS"
STATUS=$?
echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] qg-baseline-daily-promote: exit=${STATUS}"
exit "$STATUS"
