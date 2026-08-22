#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# slot-master-rebase.sh — slot-master reconciliation helper.
#
# Wraps `git fetch origin live-defi-rollout && git rebase origin/live-defi-rollout`
# with structured conflict reporting so the slot master agent can classify the
# conflict shape per the plan-aware merge resolution protocol.
#
# Usage:
#   slot-master-rebase.sh                  # rebase current repo's slot branch
#   slot-master-rebase.sh --all            # rebase every repo's slot worktree in this slot
#
# Run from inside a slot worktree (e.g. ${WORKSPACE_ROOT}/.tabs/3/unified-trading-pm).
#
# On conflict, emits a `[CONFLICT]` block per conflicted file:
#   [CONFLICT] <file>
#     shape: <append-section | checkbox-flip | paragraph-rewrite | code | unknown>
#     incoming: <sha-short> <subject>
#     local:    <sha-short> <subject>
#   <conflict-marker excerpt>
#
# Codex SSOT: codex/05-infrastructure/plan-aware-merge-resolution.md
# Plan      : plans/active/per_agent_worktrees_2026_05_10.md

set -euo pipefail

INTEGRATION_BRANCH="live-defi-rollout"
MODE="single"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --all)      MODE="all"; shift;;
        -h|--help)
            sed -n '2,22p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0;;
        *)          echo "Unknown arg: $1" >&2; exit 1;;
    esac
done

log() { printf '[slot-master-rebase] %s\n' "$*"; }

classify_conflict() {
    # Heuristic conflict-shape classifier. Reads <file> with `<<<<<<<` markers
    # and emits one of: append-section / checkbox-flip / paragraph-rewrite / code / unknown.
    local file="$1" ext shape="unknown"
    ext="${file##*.}"

    # Markdown files: examine the marker contents for plan-shape hints.
    if [[ "${ext}" == "md" ]]; then
        # If conflict region contains "- [x]" or "- [ ]" → checkbox-flip.
        if grep -q '^- \[[ x]\]' <(sed -n '/<<<<<<</,/>>>>>>>/p' "${file}"); then
            shape="checkbox-flip"
        # If conflict region is bullet-list-only (every line starts with `-` or `*` or whitespace) → append-section.
        elif sed -n '/<<<<<<</,/>>>>>>>/p' "${file}" | grep -v '^<<<<<<<\|^=======\|^>>>>>>>' \
            | grep -vE '^\s*([-*]|$)' > /dev/null; then
            shape="paragraph-rewrite"
        else
            shape="append-section"
        fi
    elif [[ "${ext}" == "py" || "${ext}" == "ts" || "${ext}" == "tsx" || "${ext}" == "js" ]]; then
        shape="code"
    fi
    printf '%s' "${shape}"
}

rebase_one() {
    local repo_dir="$1" branch incoming local_sha
    pushd "${repo_dir}" >/dev/null
    branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
    log "Repo $(basename "${repo_dir}") on ${branch}: fetch + rebase onto origin/${INTEGRATION_BRANCH}"

    git fetch --quiet origin "${INTEGRATION_BRANCH}" 2>/dev/null || {
        log "  WARN: fetch failed (offline?); skipping."
        popd >/dev/null
        return 0
    }

    incoming=$(git log --oneline -1 "origin/${INTEGRATION_BRANCH}")
    local_sha=$(git log --oneline -1 HEAD)

    if git rebase --quiet "origin/${INTEGRATION_BRANCH}" 2>/dev/null; then
        log "  CLEAN rebase. ${branch} now ahead of origin/${INTEGRATION_BRANCH} by $(git rev-list --count origin/${INTEGRATION_BRANCH}..HEAD) commit(s)."
        popd >/dev/null
        return 0
    fi

    # Conflict path — emit structured report per conflicted file.
    log "  CONFLICT detected. Reporting structured shape per file:"
    log "    incoming: ${incoming}"
    log "    local:    ${local_sha}"
    while IFS= read -r conflicted; do
        [[ -z "${conflicted}" ]] && continue
        local shape
        shape=$(classify_conflict "${conflicted}")
        printf '\n[CONFLICT] %s\n  shape: %s\n  incoming: %s\n  local:    %s\n' \
            "${conflicted}" "${shape}" "${incoming}" "${local_sha}"
        printf '  excerpt:\n'
        sed -n '/<<<<<<</,/>>>>>>>/p' "${conflicted}" | head -30 | sed 's/^/    /'
    done < <(git diff --name-only --diff-filter=U 2>/dev/null)

    log ""
    log "  Resolution options:"
    log "    1. Auto-resolve per protocol shape (see codex/05-infrastructure/plan-aware-merge-resolution.md):"
    log "       - append-section → union; --continue."
    log "       - checkbox-flip  → keep [x] + merge evidence; --continue."
    log "       - paragraph-rewrite / code → ESCALATE to operator + Open questions Q-entry."
    log "    2. Abort rebase: git rebase --abort"
    log ""
    log "  Slot branch left in rebase-conflict state. Resolve, git add, git rebase --continue."
    popd >/dev/null
    return 2
}

if [[ "${MODE}" == "single" ]]; then
    rebase_one "$(pwd)"
else
    # --all: walk every repo worktree under the current slot dir.
    slot_dir="$(pwd)"
    # If we're inside a per-repo worktree, climb one level to slot dir.
    if [[ -f .git ]]; then
        slot_dir="$(cd .. && pwd)"
    fi
    for d in "${slot_dir}"/*/; do
        [[ -d "${d}" ]] || continue
        [[ -d "${d}.git" || -f "${d}.git" ]] || continue
        rebase_one "${d}" || true   # continue across all repos even if one conflicts
    done
fi
