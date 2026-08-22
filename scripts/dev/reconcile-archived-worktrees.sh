#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# reconcile-archived-worktrees.sh — remove .tabs/<N>/<repo>/ worktrees for
# every repo marked `archived: true` + `clone: false` in workspace-manifest.json.
#
# Per CLAUDE.md "Local slot host = VM slot host" HARD RULE: every host must
# converge on the same workspace shape. When a repo is archived (e.g. via
# ml_repo_consolidation_2026_05_19.md Phase -2 Bucket 1), the per-slot
# worktrees become dead weight — they point at remotes that refuse pushes,
# show up as red on the dashboard, and confuse the FF-pull cron.
#
# Usage:
#   bash unified-trading-pm/scripts/dev/reconcile-archived-worktrees.sh                # dry-run (default)
#   bash unified-trading-pm/scripts/dev/reconcile-archived-worktrees.sh --apply        # actually remove
#   bash unified-trading-pm/scripts/dev/reconcile-archived-worktrees.sh --apply --keep-stashes
#     (always — git stashes are stored in the .git of the main clone, so they
#      survive worktree removal; the flag is documentation that we know this)
#
# Cross-platform: macOS + Linux. Reads workspace-manifest.json via python3 + jq.

set -uo pipefail

APPLY=0
case "${1:-}" in
    --apply) APPLY=1 ;;
    --dry-run|"") APPLY=0 ;;
    -h|--help)
        sed -n '2,17p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
        exit 0 ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
esac

# Resolve workspace root (climb cwd to unified-trading-system-repos)
detect_workspace() {
    local d="$(pwd)"
    while [[ "$(basename "${d}")" != "unified-trading-system-repos" && "${d}" != "/" ]]; do
        d="$(dirname "${d}")"
    done
    if [[ "${d}" == "/" ]]; then
        for c in "${HOME}/Code/unified-trading-system-repos" "/home/ubuntu/unified-trading-system-repos"; do
            [[ -d "$c" ]] && d="$c" && break
        done
    fi
    echo "${d}"
}
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$(detect_workspace)}"
MANIFEST="${WORKSPACE_ROOT}/unified-trading-pm/workspace-manifest.json"

if [[ ! -f "${MANIFEST}" ]]; then
    echo "ERROR: workspace-manifest.json not found at ${MANIFEST}" >&2
    exit 1
fi

# Extract the list of archived repos that have clone:false
ARCHIVED_REPOS=$(python3 <<PY
import json
m = json.load(open("${MANIFEST}"))
for name, r in m.get("repositories", {}).items():
    if r.get("archived") and r.get("clone") is False:
        print(name)
PY
)

if [[ -z "${ARCHIVED_REPOS}" ]]; then
    echo "No repos marked archived+clone:false in manifest. Nothing to reconcile."
    exit 0
fi

echo "=== archived repos to reconcile (manifest says clone:false) ==="
echo "${ARCHIVED_REPOS}"
echo

removed=0
kept=0
for repo in ${ARCHIVED_REPOS}; do
    # Find every .tabs/<N>/<repo>/ worktree across all slots
    for slot_repo in "${WORKSPACE_ROOT}"/.tabs/*/"${repo}"; do
        [[ -d "${slot_repo}" ]] || continue
        slot=$(basename "$(dirname "${slot_repo}")")
        if [[ ${APPLY} -eq 1 ]]; then
            echo "REMOVING: ${slot_repo}"
            # Use git worktree remove to update the parent's .git/worktrees/ records
            main_clone="${WORKSPACE_ROOT}/${repo}"
            if [[ -d "${main_clone}/.git" ]]; then
                git -C "${main_clone}" worktree remove --force "${slot_repo}" 2>&1 | sed 's/^/  /'
            else
                # main clone not present — just rm the worktree dir + prune from any parent
                rm -rf "${slot_repo}"
                echo "  (no main clone for ${repo} — used rm -rf)"
            fi
            removed=$((removed + 1))
        else
            echo "WOULD REMOVE: ${slot_repo} (slot ${slot})"
            kept=$((kept + 1))
        fi
    done
done

if [[ ${APPLY} -eq 1 ]]; then
    # Prune any dangling worktree records
    for repo in ${ARCHIVED_REPOS}; do
        main_clone="${WORKSPACE_ROOT}/${repo}"
        [[ -d "${main_clone}/.git" ]] && git -C "${main_clone}" worktree prune 2>&1 | sed "s/^/  prune ${repo}: /"
    done
    echo
    echo "=== removed ${removed} worktree(s). Run the git-status-report cron to refresh dashboard. ==="
else
    echo
    echo "=== ${kept} worktree(s) would be removed. Re-run with --apply to execute. ==="
fi
