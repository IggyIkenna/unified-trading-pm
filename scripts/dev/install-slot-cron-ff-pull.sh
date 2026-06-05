#!/usr/bin/env bash
# install-slot-cron-ff-pull.sh — register the 5-min FF-pull cron + symmetry-verify cron for an operator.
#
# Idempotent: re-runs are safe. Detects existing identical crontab entry and skips.
# Operator runs this ONCE per machine (not per slot — one cron run walks every slot).
#
# Usage:
#   bash unified-trading-pm/scripts/dev/install-slot-cron-ff-pull.sh
#   bash unified-trading-pm/scripts/dev/install-slot-cron-ff-pull.sh --uninstall
#   bash unified-trading-pm/scripts/dev/install-slot-cron-ff-pull.sh --interval 10   # 10-min cadence
#
# Defaults:
#   - Interval: 5 minutes (symmetric-host standard); also installs a */30 symmetry-verify cron
#   - Slot dir: ${WORKSPACE_ROOT}/.tabs/1 (uses --all-slots to walk every slot)
#   - Log file: /tmp/slot-cron-ff-pull.log (overwritten by puller, rotation manual)
#
# What it does:
#   1. Reads current `crontab -l`.
#   2. Checks for a line matching the slot-cron-ff-pull.sh marker.
#   3. If absent: appends a new entry running every <interval> minutes.
#   4. If present + identical: prints "already installed" and exits.
#   5. If present + differs: replaces the existing line.
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Cron-based FF puller"

set -euo pipefail

INTERVAL=5  # CLAUDE.md § "Local slot host = VM slot host" mandates 5-min ff-pull cadence (was 15 — drift)
ACTION="install"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
SLOT_DIR="${WORKSPACE_ROOT}/.tabs/1"
LOG_FILE="/tmp/slot-cron-ff-pull.log"
MARKER="# slot-cron-ff-pull"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --interval) INTERVAL="$2"; shift 2;;
        --uninstall) ACTION="uninstall"; shift;;
        --slot-dir) SLOT_DIR="$2"; shift 2;;
        -h|--help) sed -n '2,24p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

if [ ! -d "${SLOT_DIR}" ]; then
    echo "Slot dir does not exist: ${SLOT_DIR}" >&2
    echo "Set WORKSPACE_ROOT or pass --slot-dir <path>." >&2
    exit 1
fi

# Phase D guard (2026-06-05): install MUST run from the workspace-ROOT PM clone, never a slot
# worktree — else the baked-in absolute ROOT_PM/SLOT_DIR point at .tabs/N/.tabs/N and the cron
# self-pulls into the wrong tree. WORKSPACE_ROOT is the parent of .tabs/, so it must NOT contain it.
case "${WORKSPACE_ROOT}" in
    */.tabs/*|*/.tabs) echo "Refusing: WORKSPACE_ROOT='${WORKSPACE_ROOT}' is inside a slot worktree (.tabs/). Run install from the root clone." >&2; exit 1;;
esac

PULL_SCRIPT="${WORKSPACE_ROOT}/unified-trading-pm/scripts/dev/slot-cron-ff-pull.sh"
if [ ! -x "${PULL_SCRIPT}" ]; then
    echo "FF-pull script not executable at ${PULL_SCRIPT}" >&2
    exit 1
fi

# Executor self-heal (Phase B, 2026-06-05): each cron line FIRST hard-pulls its OWN script(s)
# from LDR before running, so a stale/dirty PM clone never starves the cron of current code
# (kills the chicken-and-egg that froze the top-level PM clone 195 commits behind). The self-pull
# lives in the crontab line (the immutable anchor) — NOT inside the scripts it updates. It is:
#   - surgical: overwrites ONLY the tracked cron scripts; every other dirty PM file is untouched.
#   - offline-safe: `|| true` → a failed fetch/checkout just runs the last-good local copy.
#   - correct: `git checkout origin/LDR -- <file>` lands at the real path so the script's
#     BASH_SOURCE-relative sibling (cron-branch-overrides.txt) + --help still resolve (NOT show|bash).
# Treat these cron scripts as LDR-authoritative + QG-gated: local edits to them are overwritten each
# tick by design, so changes ship via PR→QG→LDR, never local. GHA workflows are exempt (fresh checkout).
PM_DIR="${WORKSPACE_ROOT}/unified-trading-pm"
INTEGRATION_BRANCH="live-defi-rollout"
SELF_PULL_FF="cd \"${PM_DIR}\" && { git fetch -q origin ${INTEGRATION_BRANCH} 2>/dev/null; git checkout -q origin/${INTEGRATION_BRANCH} -- scripts/dev/slot-cron-ff-pull.sh scripts/dev/cron-branch-overrides.txt 2>/dev/null; } || true"
SELF_PULL_VERIFY="cd \"${PM_DIR}\" && { git fetch -q origin ${INTEGRATION_BRANCH} 2>/dev/null; git checkout -q origin/${INTEGRATION_BRANCH} -- scripts/verify-slot-host-symmetry.sh 2>/dev/null; } || true"

# Periodic symmetry verify + Slack-alert-on-drift — ENFORCES the symmetric-host
# contract (CLAUDE.md § "Local slot host = VM slot host") rather than just documenting
# it: every host that has the FF-pull cron also self-checks + alerts if it drifts.
VERIFY_SCRIPT="${WORKSPACE_ROOT}/unified-trading-pm/scripts/verify-slot-host-symmetry.sh"
VERIFY_LOG="/tmp/slot-host-symmetry-verify.log"
VERIFY_MARKER="# slot-host-symmetry-verify"
VERIFY_INTERVAL=15  # operator 2026-06-04: */15 so drift/health surfaces within 15m, not 30

CRON_LINE="*/${INTERVAL} * * * * ${SELF_PULL_FF}; cd \"${SLOT_DIR}\" && bash \"${PULL_SCRIPT}\" --all-slots --quiet >> \"${LOG_FILE}\" 2>&1 ${MARKER}"
VERIFY_LINE="*/${VERIFY_INTERVAL} * * * * ${SELF_PULL_VERIFY}; cd \"${SLOT_DIR}\" && bash \"${VERIFY_SCRIPT}\" --quiet --alert >> \"${VERIFY_LOG}\" 2>&1 ${VERIFY_MARKER}"

# Idempotent install/replace of one marked cron line. Re-reads crontab each call so
# multiple ensure_cron calls compose safely.
ensure_cron() {  # $1=marker $2=cronline $3=label
    local marker="$1" line="$2" label="$3" current existing
    current=$(crontab -l 2>/dev/null || true)
    if echo "${current}" | grep -qF "${marker}"; then
        existing=$(echo "${current}" | grep -F "${marker}" | head -1)
        if [ "${existing}" = "${line}" ]; then
            echo "[already-installed] ${label}"
            return 0
        fi
        echo "[updating] ${label} (entry differs; replacing)"
        printf '%s\n%s\n' "$(echo "${current}" | grep -vF "${marker}")" "${line}" | crontab -
    else
        echo "[installing] ${label}"
        if [ -z "${current}" ]; then printf '%s\n' "${line}" | crontab -
        else printf '%s\n%s\n' "${current}" "${line}" | crontab -; fi
    fi
}
remove_cron() {  # $1=marker $2=label
    local marker="$1" label="$2" current
    current=$(crontab -l 2>/dev/null || true)
    if echo "${current}" | grep -qF "${marker}"; then
        echo "${current}" | grep -vF "${marker}" | crontab -
        echo "[uninstalled] ${label}"
    else
        echo "[noop] no ${label} entry"
    fi
}

if [ "${ACTION}" = "uninstall" ]; then
    remove_cron "${MARKER}" "slot-cron-ff-pull"
    remove_cron "${VERIFY_MARKER}" "slot-host-symmetry-verify"
    exit 0
fi

ensure_cron "${MARKER}" "${CRON_LINE}" "slot-cron-ff-pull (*/${INTERVAL}m)"
if [ -x "${VERIFY_SCRIPT}" ]; then
    ensure_cron "${VERIFY_MARKER}" "${VERIFY_LINE}" "slot-host-symmetry-verify (*/${VERIFY_INTERVAL}m, Slack-alerts on drift)"
else
    echo "[skip] verify cron — ${VERIFY_SCRIPT} not found/executable"
fi

echo "[done] cron entry registered:"
echo "  ${CRON_LINE}"
echo ""
echo "Verify with: crontab -l | grep slot-cron-ff-pull"
echo "First run will fire at the next */${INTERVAL}-minute mark. Logs: ${LOG_FILE}"
