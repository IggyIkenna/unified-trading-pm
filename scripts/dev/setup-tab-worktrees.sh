#!/usr/bin/env bash
# setup-tab-worktrees.sh — provision + manage per-slot worktrees for parallel agent tabs.
#
# 3-tier isolation model (see codex/05-infrastructure/per-tab-worktrees.md):
#   Tier 1 — Operator (Ikenna ⊥ Harsh):  separate machines.
#   Tier 2 — Slot (this script's scope): per-slot worktree at .tabs/<N>/<repo>/ on
#            permanent branch tab/<operator>/<N>.  Slot is durable identity;
#            theme is daily work-split assignment.
#   Tier 3 — Sub-agents within a slot:   share the slot's worktree; master agent
#            partitions fan-out + reconciles.
#
# Usage:
#   setup-tab-worktrees.sh --init --slots <N> [--operator <name>]
#       One-time provisioning. Creates N slots; per-repo worktree on tab/<op>/<i>.
#
#   setup-tab-worktrees.sh --add-slot <N> [--operator <name>]
#       Grow fleet by one slot (e.g. 8 → 9). Idempotent (skip-if-exists).
#
#   setup-tab-worktrees.sh --reset-slot <N> [--operator <name>]
#       Prepare slot <N> for new theme. Verify clean → fetch → rebase onto
#       origin/live-defi-rollout. Abort if dirty; operator must commit / stash
#       / discard before retry.
#
#   setup-tab-worktrees.sh --list
#       List configured slots + their current themes (reads slot-theme table
#       from operator orchestrator LEDGER if available).
#
# Idempotent across all sub-commands. Sets PREK_CACHE_DIR per slot via the
# auto-generated .envrc inside each slot worktree (foot-gun #4 mitigation).
#
# Codex SSOT: unified-trading-pm/codex/05-infrastructure/per-tab-worktrees.md
# Plan      : unified-trading-pm/plans/active/per_agent_worktrees_2026_05_10.md

set -euo pipefail

# --- Resolve workspace root ------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PM_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"
WORKSPACE_ROOT="${UNIFIED_TRADING_WORKSPACE_ROOT:-$(cd "${PM_DIR}/.." && pwd)}"
TABS_DIR="${WORKSPACE_ROOT}/.tabs"
MANIFEST="${PM_DIR}/workspace-manifest.json"
INTEGRATION_BRANCH="live-defi-rollout"

# --- Arg parsing -----------------------------------------------------------
OPERATOR="${USER:-unknown}"
MODE=""
SLOT_COUNT=""
SLOT_NUM=""

usage() {
    sed -n '2,30p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit "${1:-1}"
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --init)         MODE="init";        shift;;
        --add-slot)     MODE="add-slot";    SLOT_NUM="$2"; shift 2;;
        --reset-slot)   MODE="reset-slot";  SLOT_NUM="$2"; shift 2;;
        --list)         MODE="list";        shift;;
        --slots)        SLOT_COUNT="$2";    shift 2;;
        --operator)     OPERATOR="$2";      shift 2;;
        -h|--help)      usage 0;;
        *)              echo "Unknown arg: $1" >&2; usage 1;;
    esac
done

[[ -z "${MODE}" ]] && { echo "ERROR: one of --init / --add-slot / --reset-slot / --list required" >&2; usage 1; }
if [[ "${MODE}" == "init" && -z "${SLOT_COUNT}" ]]; then
    echo "ERROR: --init requires --slots <N>" >&2; exit 1
fi

# --- Helpers ---------------------------------------------------------------
log()  { printf '[setup-tab-worktrees] %s\n' "$*"; }
err()  { printf '[setup-tab-worktrees] ERROR: %s\n' "$*" >&2; }

active_repos() {
    # Emit one repo name per line, active (not archived_into) only.
    python3 - "${MANIFEST}" <<'PY'
import json, sys
with open(sys.argv[1]) as f:
    d = json.load(f)
for k, v in d.get("repositories", {}).items():
    if not v.get("archived_into"):
        print(k)
PY
}

slot_branch() { printf 'tab/%s/%s\n' "${OPERATOR}" "$1"; }
slot_dir()    { printf '%s/%s\n' "${TABS_DIR}" "$1"; }

ensure_repo_worktree() {
    # Create worktree for one repo at one slot. Idempotent.
    local repo="$1" slot="$2"
    local branch sibling slot_repo_dir
    branch="$(slot_branch "${slot}")"
    sibling="${WORKSPACE_ROOT}/${repo}"
    slot_repo_dir="$(slot_dir "${slot}")/${repo}"

    if [[ ! -d "${sibling}/.git" ]]; then
        log "  SKIP ${repo} (no sibling clone at ${sibling})"
        return 0
    fi
    if [[ -e "${slot_repo_dir}" ]]; then
        log "  OK   ${repo} (worktree exists)"
        return 0
    fi
    mkdir -p "$(slot_dir "${slot}")"

    # Reuse branch if it exists; otherwise create from integration branch.
    if git -C "${sibling}" show-ref --verify --quiet "refs/heads/${branch}"; then
        git -C "${sibling}" worktree add "${slot_repo_dir}" "${branch}" >/dev/null
    else
        # Make sure the integration branch is up-to-date on origin before
        # branching off it (operator may not have fetched in a while).
        git -C "${sibling}" fetch --quiet origin "${INTEGRATION_BRANCH}" 2>/dev/null || true
        git -C "${sibling}" worktree add "${slot_repo_dir}" -b "${branch}" \
            "origin/${INTEGRATION_BRANCH}" >/dev/null
    fi
    log "  ADD  ${repo} → ${slot_repo_dir} (branch ${branch})"
}

write_slot_envrc() {
    # Per-slot .envrc isolates PREK_CACHE_DIR + sets WORKSPACE_ROOT.
    # Foot-gun #4 mitigation (prek patches stay per-slot, never cross-restore).
    local slot="$1" sd
    sd="$(slot_dir "${slot}")"
    mkdir -p "${sd}/.cache/prek"
    cat > "${sd}/.envrc" <<EOF
# Auto-generated by setup-tab-worktrees.sh — slot ${slot} environment.
# Sourced when shell / Cursor / direnv opens a slot worktree.
export UNIFIED_TRADING_WORKSPACE_ROOT="${sd}"
export PREK_CACHE_DIR="${sd}/.cache/prek"
export SLOT_NUMBER="${slot}"
export SLOT_OPERATOR="${OPERATOR}"
EOF
    log "  ENV  slot ${slot} .envrc written (PREK_CACHE_DIR=${sd}/.cache/prek)"
}

copy_workspace_file() {
    # Copy the canonical multi-root .code-workspace into the slot dir so the
    # operator can `File → Open Workspace from File` and get the labelled
    # multi-root view (relative paths in the workspace file resolve against
    # the slot dir; per-slot copy keeps each slot self-contained).
    local slot="$1" sd src dst
    sd="$(slot_dir "${slot}")"
    src="${WORKSPACE_ROOT}/unified-trading-system-repos.code-workspace"
    dst="${sd}/unified-trading-system-repos.code-workspace"
    if [[ -f "${src}" ]]; then
        cp "${src}" "${dst}"
        log "  WS   slot ${slot} workspace file copied (${dst})"
    else
        log "  WS   slot ${slot} skipped (no canonical .code-workspace at ${src})"
    fi
}

provision_slot() {
    local slot="$1"
    log "Provisioning slot ${slot} (branch tab/${OPERATOR}/${slot}) ..."
    write_slot_envrc "${slot}"
    copy_workspace_file "${slot}"
    while IFS= read -r repo; do
        ensure_repo_worktree "${repo}" "${slot}"
    done < <(active_repos)
}

verify_slot_clean() {
    # Walk every repo's worktree in the slot, ensure dirty=0 + ahead/behind=0/0
    # against origin/<integration-branch>. Used by --reset-slot.
    local slot="$1" sd repo dirty ah_be ok=1
    sd="$(slot_dir "${slot}")"
    [[ -d "${sd}" ]] || { err "Slot ${slot} not provisioned (no ${sd}). Run --init or --add-slot first."; return 1; }
    while IFS= read -r repo; do
        local rd="${sd}/${repo}"
        [[ -d "${rd}/.git" || -f "${rd}/.git" ]] || continue
        dirty=$(git -C "${rd}" status --porcelain=v1 2>/dev/null | wc -l | tr -d ' ')
        if [[ "${dirty}" != "0" ]]; then
            err "Slot ${slot} ${repo}: ${dirty} dirty file(s). Commit/stash/discard before --reset-slot."
            git -C "${rd}" status --short
            ok=0
        fi
    done < <(active_repos)
    return $(( ! ok ))
}

rebase_slot() {
    # For each repo's worktree, fetch origin + rebase slot branch onto
    # origin/<integration-branch>. Aborts the whole reset if any repo fails.
    local slot="$1" sd repo branch ok=1
    sd="$(slot_dir "${slot}")"
    while IFS= read -r repo; do
        local rd="${sd}/${repo}"
        [[ -d "${rd}/.git" || -f "${rd}/.git" ]] || continue
        branch="$(slot_branch "${slot}")"
        if ! git -C "${rd}" fetch --quiet origin "${INTEGRATION_BRANCH}" 2>/dev/null; then
            err "${repo}: fetch failed"; ok=0; continue
        fi
        if ! git -C "${rd}" rebase --quiet "origin/${INTEGRATION_BRANCH}" 2>/dev/null; then
            err "${repo}: rebase onto origin/${INTEGRATION_BRANCH} failed; manual resolution required."
            git -C "${rd}" rebase --abort 2>/dev/null || true
            ok=0; continue
        fi
        log "  REBASED ${repo} on origin/${INTEGRATION_BRANCH}"
    done < <(active_repos)
    return $(( ! ok ))
}

# --- Sub-commands ----------------------------------------------------------
case "${MODE}" in
    init)
        log "Initialising ${SLOT_COUNT} slots for operator '${OPERATOR}' under ${TABS_DIR}/"
        mkdir -p "${TABS_DIR}"
        for ((i=1; i<=SLOT_COUNT; i++)); do
            provision_slot "${i}"
        done
        log "Done. ${SLOT_COUNT} slots ready. Next: assign themes via the daily work-split plan + ${OPERATOR}_orchestrator/LEDGER.md slot↔theme table."
        ;;
    add-slot)
        log "Adding slot ${SLOT_NUM} for operator '${OPERATOR}'"
        mkdir -p "${TABS_DIR}"
        provision_slot "${SLOT_NUM}"
        ;;
    reset-slot)
        log "Resetting slot ${SLOT_NUM} for new theme (operator '${OPERATOR}')"
        verify_slot_clean "${SLOT_NUM}" || { err "Slot ${SLOT_NUM} dirty — see above. Aborting reset."; exit 2; }
        rebase_slot "${SLOT_NUM}" || { err "Slot ${SLOT_NUM} rebase failed. Resolve manually, then re-run."; exit 3; }
        log "Slot ${SLOT_NUM} reset complete. Ready for new theme assignment."
        ;;
    list)
        log "Slots configured under ${TABS_DIR}/:"
        if [[ ! -d "${TABS_DIR}" ]]; then
            log "  (none — run --init first)"
            exit 0
        fi
        for d in "${TABS_DIR}"/*/; do
            [[ -d "${d}" ]] || continue
            slot="$(basename "${d}")"
            pm_wt="${d}unified-trading-pm"
            if [[ -d "${pm_wt}/.git" || -f "${pm_wt}/.git" ]]; then
                br=$(git -C "${pm_wt}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')
                head_sha=$(git -C "${pm_wt}" rev-parse --short HEAD 2>/dev/null || echo '?')
                log "  slot ${slot}: branch=${br} head=${head_sha}"
            else
                log "  slot ${slot}: (PM worktree missing — partial provision; re-run --add-slot ${slot})"
            fi
        done
        ;;
esac
