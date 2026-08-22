#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# install-slot-cron-ff-pull.sh — register the 5-min FF-pull cron + symmetry-verify cron for an operator.
#
# Idempotent: re-runs are safe. Detects existing identical crontab entry and skips.
# Operator runs this ONCE per machine (not per slot — one cron run walks every slot).
#
# Usage:
#   bash unified-trading-pm/scripts/dev/install-slot-cron-ff-pull.sh
#   bash unified-trading-pm/scripts/dev/install-slot-cron-ff-pull.sh --uninstall
#   bash unified-trading-pm/scripts/dev/install-slot-cron-ff-pull.sh --interval 10   # 10-min cadence
#   bash unified-trading-pm/scripts/dev/install-slot-cron-ff-pull.sh --include-main-clones  # ALSO ff-pull root/main clones
#
# Defaults:
#   - Interval: 5 minutes (symmetric-host standard); also installs a */30 symmetry-verify cron
#   - Slot dir: ${WORKSPACE_ROOT}/.tabs/1 (uses --all-slots to walk every slot)
#   - Log file: ${XDG_RUNTIME_DIR:-/tmp}/slot-cron-ff-pull.$(id -u).log (per-uid → a root-owned log never blocks the operator cron)
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

# Guard: NEVER install the slot crons into ROOT's crontab. They run git on operator-owned repos and
# create a /tmp lock owned by the running user; a root crontab (e.g. a bootstrap that forgot to drop
# to the operator) then collides with the operator's cron — the root-owned lock blocks the operator's
# run ("Permission denied") AND git-as-root fails "dubious ownership", so the FF-pull silently stops
# fast-forwarding (incident 2026-06-16: human-planning VM ran 4 days / 688 commits behind). Bootstrap
# MUST invoke this via `sudo -u <operator>`. Override only if you genuinely intend a root crontab.
if [ "${EUID:-$(id -u)}" -eq 0 ] && [ "${ALLOW_ROOT_CRON:-0}" != "1" ]; then
    echo "Refusing to install slot crons as root (EUID=0) — they belong in the OPERATOR's per-user crontab." >&2
    echo "Re-run as the operator:  sudo -u <operator> WORKSPACE_ROOT=<workspace-root> bash $0" >&2
    echo "(set ALLOW_ROOT_CRON=1 to override — almost never correct.)" >&2
    exit 1
fi

INTERVAL=5  # CLAUDE.md § "Local slot host = VM slot host" mandates 5-min ff-pull cadence (was 15 — drift)
ACTION="install"
INCLUDE_MAIN_CLONES=0  # opt-in: ALSO FF-pull the ROOT/main clones (a host that works in the main
# clones rather than .tabs/, e.g. an interactive dispatch host). Default off — the standard model
# works in .tabs/ which --all-slots already covers, so a bootstrapped data/paper VM needs nothing extra.
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
SLOT_DIR="${WORKSPACE_ROOT}/.tabs/1"
# Per-uid logs (mirrors the per-uid LOCK in slot-cron-ff-pull.sh) so a root-owned /tmp log from a
# one-off run-as-root can NEVER block the OPERATOR cron's `>>` redirect (the 2026-06-22 outage: a
# root-owned /tmp/slot-cron-ff-pull.log silently failed every ubuntu tick for 6 days). $(id -u)
# expands at install-time to the installing operator's uid; cron-user == install-user so it's stable.
LOG_FILE="${XDG_RUNTIME_DIR:-/tmp}/slot-cron-ff-pull.$(id -u).log"
MARKER="# slot-cron-ff-pull"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --interval) INTERVAL="$2"; shift 2;;
        --uninstall) ACTION="uninstall"; shift;;
        --slot-dir) SLOT_DIR="$2"; shift 2;;
        --include-main-clones) INCLUDE_MAIN_CLONES=1; shift;;
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
#   - cmp-guarded (2026-07-14): writes ONLY when the working copy differs from origin/LDR — an
#     unconditional every-tick write left the file dirty-vs-HEAD on a behind clone, which made the
#     FF-pull's own [skip:dirty] starve the clone of the very FF that would heal it (root-PM
#     incident 2026-07-14: 1138 commits behind). ff_one()'s managed-file heal covers hosts still
#     on an older unguarded crontab line. See cron-self-pull-lib.sh for the full contract.
#   - offline-safe: `|| true` → a failed fetch/show just runs the last-good local copy.
#   - correct: files land at their real paths (script via mv, data via cmp-guarded show+mv — NOT
#     `git checkout`, which also stages the write) so the script's BASH_SOURCE-relative sibling
#     (cron-branch-overrides.txt) + --help still resolve.
# Treat these cron scripts as LDR-authoritative + QG-gated: local edits to them are overwritten each
# tick by design, so changes ship via PR→QG→LDR, never local. GHA workflows are exempt (fresh checkout).
PM_DIR="${WORKSPACE_ROOT}/unified-trading-pm"
INTEGRATION_BRANCH="live-defi-rollout"
# The syntax-gate (H6), offline-safety, and chmod-755 rationale now live in the shared emitter
# cron-self-pull-lib.sh — sourced here so the self-pull pattern is DRY across every cron-installer
# (each EMITTED crontab line is still fully self-contained). One bad commit to a managed cron script
# can never propagate fleet-wide (bash -n gate); a failed fetch falls back to the last-good local copy.
source "$(dirname "${BASH_SOURCE[0]}")/cron-self-pull-lib.sh"
SELF_PULL_FF="$(emit_cron_self_pull "${PM_DIR}" "${INTEGRATION_BRANCH}" "scripts/dev/slot-cron-ff-pull.sh" "scripts/dev/cron-branch-overrides.txt")"
SELF_PULL_VERIFY="$(emit_cron_self_pull "${PM_DIR}" "${INTEGRATION_BRANCH}" "scripts/verify-slot-host-symmetry.sh")"
SELF_PULL_STATUS="$(emit_cron_self_pull "${PM_DIR}" "${INTEGRATION_BRANCH}" "scripts/dev/slot-git-status-report.sh")"

# Periodic symmetry verify + Slack-alert-on-drift — ENFORCES the symmetric-host
# contract (CLAUDE.md § "Local slot host = VM slot host") rather than just documenting
# it: every host that has the FF-pull cron also self-checks + alerts if it drifts.
VERIFY_SCRIPT="${WORKSPACE_ROOT}/unified-trading-pm/scripts/verify-slot-host-symmetry.sh"
VERIFY_LOG="${XDG_RUNTIME_DIR:-/tmp}/slot-host-symmetry-verify.$(id -u).log"
VERIFY_MARKER="# slot-host-symmetry-verify"
VERIFY_INTERVAL=15  # operator 2026-06-04: */15 so drift/health surfaces within 15m, not 30

CRON_LINE="*/${INTERVAL} * * * * ${SELF_PULL_FF}; cd \"${SLOT_DIR}\" && bash \"${PULL_SCRIPT}\" --all-slots --quiet >> \"${LOG_FILE}\" 2>&1 ${MARKER}"
VERIFY_LINE="*/${VERIFY_INTERVAL} * * * * ${SELF_PULL_VERIFY}; cd \"${SLOT_DIR}\" && bash \"${VERIFY_SCRIPT}\" --quiet --alert >> \"${VERIFY_LOG}\" 2>&1 ${VERIFY_MARKER}"

# slot-git-status-report — runs the per-slot status reporter; offset +2m from the FF-pull
# (0,5,10…) so it observes the post-FF tree state. Self-pull added 2026-06-12 (was bare → a
# stale clone ran stale reporter code; qg_commit plan Phase C).
STATUS_SCRIPT="${WORKSPACE_ROOT}/unified-trading-pm/scripts/dev/slot-git-status-report.sh"
STATUS_LOG="${XDG_RUNTIME_DIR:-/tmp}/slot-git-status-report.$(id -u).log"
STATUS_MARKER="# slot-git-status-report"
STATUS_SCHEDULE="2,7,12,17,22,27,32,37,42,47,52,57 * * * *"
STATUS_LINE="${STATUS_SCHEDULE} ${SELF_PULL_STATUS}; cd \"${SLOT_DIR}\" && bash \"${STATUS_SCRIPT}\" --quiet >> \"${STATUS_LOG}\" 2>&1 ${STATUS_MARKER}"

# main-clone-ff-pull (opt-in via --include-main-clones) — FF-pull the ROOT/main clones
# (${WORKSPACE_ROOT}/<repo>), which the .tabs/ --all-slots sweep does NOT cover. For a host that
# does its work in the main clones (an interactive dispatch host) rather than .tabs/. Self-contained
# inline loop (no extra script): on each clean clone that is on the integration branch, fetch + FF
# only; a DIRTY clone is SKIPPED (never stomp WIP), ff-only (never a merge commit). Offset to :03 so
# it doesn't collide with the */5 .tabs sweep (:00) or the status report (:02). No `%` in the body
# (cron treats `%` as newline) — uses `date -u` default format, not `+%H`.
MAIN_CLONE_MARKER="# main-clone-ff-pull"
MAIN_CLONE_LOG="${XDG_RUNTIME_DIR:-/tmp}/main-clone-ff-pull.$(id -u).log"
MAIN_CLONE_SCHEDULE="3,8,13,18,23,28,33,38,43,48,53,58 * * * *"
# NOTE: before the dirty-skip, auto-restore uv.lock when it is dirtied ONLY by internal editable-dep
# "version =" drift (regen churn `uv sync` rewrites every run; the HARD RULE forbids committing it).
# Left dirty it [skip:dirty]s the main clone → it falls behind LDR (the fleet-wide "commits not
# flowing" cause). Restores ONLY pure-version drift — a genuine lock edit (non-version lines) is
# preserved so an interactive authoring session's in-flight work is never clobbered. POSIX-safe.
MAIN_CLONE_LINE="${MAIN_CLONE_SCHEDULE} echo \"sweep \$(date -u)\"; for r in ${WORKSPACE_ROOT}/*/; do [ -d \"\${r}.git\" ] || continue; [ \"\$(git -C \"\$r\" rev-parse --abbrev-ref HEAD 2>/dev/null)\" = \"${INTEGRATION_BRANCH}\" ] || continue; if git -C \"\$r\" ls-files --error-unmatch uv.lock >/dev/null 2>&1 && ! git -C \"\$r\" diff --quiet -- uv.lock 2>/dev/null; then nv=\$(git -C \"\$r\" diff -- uv.lock 2>/dev/null | grep -E '^[+-]' | grep -vE '^(\\+\\+\\+|---)' | sed -E 's/^[+-][[:space:]]*//' | grep -vcE '^version = \"[^\"]*\"\$'); [ \"\$nv\" = 0 ] && git -C \"\$r\" checkout -q -- uv.lock 2>/dev/null; fi; [ -n \"\$(git -C \"\$r\" status --porcelain 2>/dev/null | grep -v '^??')\" ] && continue; git -C \"\$r\" fetch -q origin ${INTEGRATION_BRANCH} 2>/dev/null && git -C \"\$r\" merge --ff-only origin/${INTEGRATION_BRANCH} >/dev/null 2>&1 && echo \"  ff \$(basename \"\$r\")\"; done >> \"${MAIN_CLONE_LOG}\" 2>&1 ${MAIN_CLONE_MARKER}"

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
    remove_cron "${STATUS_MARKER}" "slot-git-status-report"
    remove_cron "${MAIN_CLONE_MARKER}" "main-clone-ff-pull"
    exit 0
fi

ensure_cron "${MARKER}" "${CRON_LINE}" "slot-cron-ff-pull (*/${INTERVAL}m)"
if [ -x "${VERIFY_SCRIPT}" ]; then
    ensure_cron "${VERIFY_MARKER}" "${VERIFY_LINE}" "slot-host-symmetry-verify (*/${VERIFY_INTERVAL}m, Slack-alerts on drift)"
else
    echo "[skip] verify cron — ${VERIFY_SCRIPT} not found/executable"
fi
if [ -x "${STATUS_SCRIPT}" ]; then
    ensure_cron "${STATUS_MARKER}" "${STATUS_LINE}" "slot-git-status-report (offset */5m, self-pull)"
else
    echo "[skip] status-report cron — ${STATUS_SCRIPT} not found/executable"
fi
if [ "${INCLUDE_MAIN_CLONES}" = "1" ]; then
    ensure_cron "${MAIN_CLONE_MARKER}" "${MAIN_CLONE_LINE}" "main-clone-ff-pull (offset */5m; clean main clones only)"
else
    # Opt-in only: a plain install neither adds NOR removes the main-clone cron (so a deliberate
    # --include-main-clones host survives a later plain re-install). Use --uninstall to remove it.
    echo "[skip] main-clone-ff-pull — pass --include-main-clones to also FF-pull the root/main clones"
fi

echo "[done] cron entry registered:"
echo "  ${CRON_LINE}"
echo ""
echo "Verify with: crontab -l | grep slot-cron-ff-pull"
echo "First run will fire at the next */${INTERVAL}-minute mark. Logs: ${LOG_FILE}"
