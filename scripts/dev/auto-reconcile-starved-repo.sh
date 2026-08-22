#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# auto-reconcile-starved-repo.sh — safe automatic reconciliation for ONE FF-starved repo worktree.
#
# ff-starvation-detect.sh is explicitly documented as detector-only: "It does NOT auto-resolve
# the collision (that needs the stash-by-name + adjudicate judgment from the two-teammates HARD
# RULE)." This script IS that resolution step, but only for the subset of starved repos where the
# fix is genuinely mechanical and independently verified — never a blind stash/pull/pop.
#
# Built from a live incident (2026-08-19, operator-directed manual reconcile of slots 4/5/6's
# unified-trading-pm) that surfaced two things worth automating AND one thing that must never be:
#   1. The SAFE pattern is `git pull --rebase --autostash`, not hand-rolled `stash push -- <files>`
#      / pull / `stash pop` — the latter is the documented cause of silent content loss under high
#      branch velocity (plans/active/issues/git_stash_push_pop_silently_drops_content_under_high_branch_velocity_2026_08_17.md).
#   2. A CLEAN, non-conflicting `git pull --rebase --autostash` exit is NOT proof nothing was lost
#      (same doc). This script verifies by CONTENT (do a dirty file's own added lines survive
#      somewhere in its post-pop state?), not by exit code alone — exactly the manual check that
#      caught a real regression in the source incident (a pre-existing, already-broken conflict-
#      marker mess baked into a file from an EARLIER, unrelated botched stash cycle).
#   3. What must never be automated: deciding WHICH SIDE is correct once a real conflict or
#      suspected loss is found. That stays a human call (git log -S blame, judgment) — this script
#      only ever detects and reports it, never resolves it.
#
# Safety gates (all must pass before ANY git-mutating step runs):
#   - Re-derives starvation itself via ff-starvation-detect.sh (never acts on a merely-behind-but-
#     healthy repo; keeps the "is this actually starved" definition in ONE place).
#   - Declines if any currently-dirty tracked file already contains raw conflict markers
#     (<<<<<<< / ||||||| / ======= / >>>>>>>) — that means an EARLIER cycle left this repo in a
#     broken state; layering another automated stash cycle on top of already-corrupted content is
#     exactly how the source incident's loss happened.
#   - Declines if a live pytest/quality-gates/basedpyright/prek/git-commit process has its cwd
#     inside this repo (exact-match via _cwd_of, never a substring/argv-text match — see
#     cursor-configs/hooks/lib/slot-collision-detect.sh's own docstring for why substring matching
#     is a documented false-negative trap), or if HEAD committed within the last 10 minutes
#     (mirrors agent-orchestrator's _worktree_has_live_progress liveness-by-progress gate).
#
# Output contract (mirrors ff-starvation-detect.sh so callers can reuse the same ping/dedup path):
#   Not starved, or fully reconciled with content verified              -> prints NOTHING, exit 0.
#   Starved but declined (pre-existing markers / live process / recent commit),
#   OR the pull left a real conflict, OR content-integrity check fails  -> prints the ORIGINAL
#     starve payload plus an appended "AUTO-RECONCILE:" section explaining what was tried and why
#     it stopped (with the backup patch path + recovery recipe when relevant), exit 0.
# Always cron-safe: never destructive, never `git stash drop`, never `git reset --hard`, never
# resolves a conflict on the caller's behalf. Exits 0 in every branch (signal script, not gate).
#
# Usage:
#   auto-reconcile-starved-repo.sh <repo_dir> [--branch BR] [--slot N] [--workspace PATH] [--dry-run]
# Env-var defaults (mirror ff-starvation-detect.sh where they overlap):
#   FF_STARVE_COMMIT_THRESHOLD / FF_STARVE_AGE_HOURS / FF_BEHIND_BACKSTOP_COMMITS /
#   FF_BEHIND_BACKSTOP_HOURS / INTEGRATION_BRANCH — passed straight through to the detector.
#   AUTO_RECONCILE_LIVENESS_WINDOW_S   default 600  (recent-HEAD-commit liveness window, seconds)
#   AUTO_RECONCILE_BACKUP_RETAIN       default 20    (backups kept per repo before pruning)
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Step 7 — troubleshooting"

set -uo pipefail   # NOT set -e: one failing git/python call must not abort the reporting path.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STARVE_DETECTOR="${SCRIPT_DIR}/ff-starvation-detect.sh"
COLLISION_LIB="${AUTO_RECONCILE_COLLISION_LIB:-$(cd "${SCRIPT_DIR}/../.." && pwd)/cursor-configs/hooks/lib/slot-collision-detect.sh}"

INTEGRATION_BRANCH="${INTEGRATION_BRANCH:-live-defi-rollout}"
SLOT_ID=""
REPO_DIR=""
WORKSPACE_PATH="${WORKSPACE_PATH:-}"
DRY_RUN=0
LIVENESS_WINDOW_S="${AUTO_RECONCILE_LIVENESS_WINDOW_S:-600}"
BACKUP_RETAIN="${AUTO_RECONCILE_BACKUP_RETAIN:-20}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --branch)    INTEGRATION_BRANCH="$2"; shift 2;;
        --slot)      SLOT_ID="$2"; shift 2;;
        --workspace) WORKSPACE_PATH="$2"; shift 2;;
        --dry-run)   DRY_RUN=1; shift;;
        -h|--help)
            sed -n '2,45p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
            exit 0;;
        -*) echo "Unknown arg: $1" >&2; exit 2;;
        *)  if [[ -z "${REPO_DIR}" ]]; then REPO_DIR="$1"; shift; else echo "Unexpected arg: $1" >&2; exit 2; fi;;
    esac
done

# AUTO_RECONCILE_LIB_ONLY=1 skips argument validation + main() entirely, for tests that source
# this file to unit-test its helper functions directly with no real repo_dir arg (mirrors
# SLOT_CRON_FF_PULL_LIB_ONLY in slot-cron-ff-pull.sh) — everything below this point that assumes
# REPO_DIR is set and valid must stay inside the corresponding guard at the bottom of the file.
if [[ "${AUTO_RECONCILE_LIB_ONLY:-0}" != "1" ]]; then
    if [[ -z "${REPO_DIR}" ]]; then
        echo "usage: auto-reconcile-starved-repo.sh <repo_dir> [--branch BR] [--slot N] [--dry-run]" >&2
        exit 2
    fi
    [[ -d "${REPO_DIR}" ]] || { echo "not a directory: ${REPO_DIR}" >&2; exit 2; }
fi

# ── source the collision-detect lib for _cwd_of (best-effort — degrades to "no signal", never
#    errors; a missing lib means the liveness gate simply can't confirm a live process, which is
#    the FAIL-SAFE direction here since the recent-HEAD-commit half of the gate still applies) ──
if [[ -f "${COLLISION_LIB}" ]]; then
    # shellcheck source=/dev/null
    source "${COLLISION_LIB}"
fi

REPO_NAME="$(basename "${REPO_DIR:-unknown}")"

# ── conflict-marker detector — reused by both the pre-check and the post-pop check ────────────
_has_conflict_markers() {
    # $1 = repo dir, $2.. = repo-relative file paths (dirty tracked files only)
    local dir="$1"; shift
    local f
    for f in "$@"; do
        [[ -f "${dir}/${f}" ]] || continue
        if grep -qE '^(<<<<<<< |\|\|\|\|\|\|\| |=======$|>>>>>>> )' "${dir}/${f}" 2>/dev/null; then
            printf '%s\n' "${f}"
        fi
    done
}

# ── liveness gate: a real pytest/quality-gates/basedpyright/prek/commit process with its EXACT
#    cwd inside this repo, or a HEAD commit inside the last LIVENESS_WINDOW_S seconds. Exact-cwd
#    match via _cwd_of only — never a substring/argv-text test (the documented false-negative
#    class named in this script's own header). Missing pgrep/lib/git degrades to "no signal". ──
_is_live_in_repo() {
    local dir="$1" here_real cand pid
    here_real="$(cd "${dir}" && pwd)"
    if command -v pgrep >/dev/null 2>&1 && declare -F _cwd_of >/dev/null 2>&1; then
        for pid in $(pgrep -f 'pytest|quality-gates|basedpyright|prek|git commit' 2>/dev/null || true); do
            cand="$(_cwd_of "${pid}" 2>/dev/null || true)"
            if [[ -n "${cand}" && "${cand}" == "${here_real}" ]]; then
                echo "live process pid=${pid} cwd=${cand}"
                return 0
            fi
        done
    fi
    local last_ct now
    last_ct="$(git -C "${dir}" log -1 --format=%ct 2>/dev/null || echo "")"
    if [[ -n "${last_ct}" ]]; then
        now="$(date -u +%s 2>/dev/null || echo 0)"
        if [[ "${now}" -gt 0 && $(( now - last_ct )) -lt "${LIVENESS_WINDOW_S}" ]]; then
            echo "HEAD committed $(( now - last_ct ))s ago (< ${LIVENESS_WINDOW_S}s liveness window)"
            return 0
        fi
    fi
    return 1
}

# ── content-integrity check for ONE file that went dirty -> clean across the pull. Extracts this
#    file's added ("+") lines from the pre-pull backup patch (dropping blank/trivial <12-char
#    lines to tolerate a reformatting hook without false-flagging), then checks whether AT LEAST
#    ONE survives verbatim in the current committed content. Requiring only one (not all) absorbs
#    legitimate reformatting (prettier/prosewrap) the same way the safe-doc-push precedent test
#    does; requiring zero would defeat the entire point of this check. ──
_check_content_integrity() {
    local repo_dir="$1" patch_file="$2" rel_path="$3"
    python3 - "${patch_file}" "${rel_path}" "${repo_dir}" <<'PYEOF'
import sys

patch_path, rel_path, repo_dir = sys.argv[1], sys.argv[2], sys.argv[3]

def extract_added_lines(patch_text, path):
    added = []
    in_file = False
    marker = f" b/{path}"
    for line in patch_text.splitlines():
        if line.startswith("diff --git"):
            in_file = line.endswith(marker) or (marker + "\t") in line
        elif in_file and line.startswith("+") and not line.startswith("+++"):
            content = line[1:]
            if len(content.strip()) >= 12:
                added.append(content)
    return added

try:
    with open(patch_path, encoding="utf-8", errors="replace") as fh:
        patch_text = fh.read()
except OSError:
    print("NO_PATCH")
    sys.exit(0)

added_lines = extract_added_lines(patch_text, rel_path)
if not added_lines:
    print("NO_ADDED_CONTENT")
    sys.exit(0)

try:
    with open(f"{repo_dir}/{rel_path}", encoding="utf-8", errors="replace") as fh:
        current = fh.read()
except OSError:
    print(f"FILE_MISSING total_added={len(added_lines)}")
    sys.exit(1)

found = sum(1 for l in added_lines if l in current)
if found == 0:
    print(f"SUSPECTED_LOSS total_added={len(added_lines)} found=0")
    sys.exit(1)
print(f"OK total_added={len(added_lines)} found={found}")
sys.exit(0)
PYEOF
}

_emit_decline() {
    # $1 = original starve payload, $2 = reason line(s)
    printf '%s\n\nAUTO-RECONCILE: declined — %s\nNo git-mutating step was attempted; this repo needs the normal manual reconcile.\n' "$1" "$2"
}

_emit_needs_resolution() {
    # $1 = original starve payload, $2 = detail block, $3 = backup patch path
    printf '%s\n\nAUTO-RECONCILE: attempted, needs manual resolution\n%s\nBackup of the pre-pull dirty state (for recovery/comparison): %s\nWorking tree left exactly as git left it -- do not run another automated cycle on top of this.\n' "$1" "$2" "$3"
}

main() {
    # ff-starvation-detect.sh deliberately never fetches (pure read-only detector; in the cron
    # sequence it runs moments after slot-cron-ff-pull.sh's own fetch already refreshed the local
    # origin/<branch> ref). This script must be correct standalone too, so fetch explicitly —
    # read-only, never mutates the working tree, safe to call unconditionally.
    git -C "${REPO_DIR}" fetch --quiet origin "${INTEGRATION_BRANCH}" 2>/dev/null || true

    local starve_payload
    starve_payload="$(FF_STARVE_COMMIT_THRESHOLD="${FF_STARVE_COMMIT_THRESHOLD:-25}" \
                       FF_STARVE_AGE_HOURS="${FF_STARVE_AGE_HOURS:-6}" \
                       FF_BEHIND_BACKSTOP_COMMITS="${FF_BEHIND_BACKSTOP_COMMITS:-75}" \
                       FF_BEHIND_BACKSTOP_HOURS="${FF_BEHIND_BACKSTOP_HOURS:-6}" \
                       INTEGRATION_BRANCH="${INTEGRATION_BRANCH}" \
                       bash "${STARVE_DETECTOR}" "${REPO_DIR}" --branch "${INTEGRATION_BRANCH}" ${SLOT_ID:+--slot "${SLOT_ID}"} 2>/dev/null || true)"
    [[ -n "${starve_payload}" ]] || return 0   # not starved -- nothing to do, nothing to report

    local dirty_files
    dirty_files="$(git -C "${REPO_DIR}" status --porcelain --untracked-files=no 2>/dev/null | sed -E 's/^...//')"

    # Gate 1: pre-existing conflict markers already baked into a dirty file.
    local pre_markers
    pre_markers="$(_has_conflict_markers "${REPO_DIR}" ${dirty_files})"
    if [[ -n "${pre_markers}" ]]; then
        _emit_decline "${starve_payload}" "pre-existing unresolved conflict markers already present in: $(echo "${pre_markers}" | tr '\n' ' ')(from an earlier, unrelated stash cycle -- needs a human to pick the correct side before anything else touches this file)"
        return 0
    fi

    # Gate 2: live process / recent commit.
    local live_reason
    if live_reason="$(_is_live_in_repo "${REPO_DIR}")"; then
        _emit_decline "${starve_payload}" "this worktree looks actively in use right now (${live_reason}) -- not touching it"
        return 0
    fi

    if [[ "${DRY_RUN}" -eq 1 ]]; then
        printf 'DRY-RUN: would reconcile %s (slot %s) -- all safety gates passed\n' "${REPO_NAME}" "${SLOT_ID:-?}"
        return 0
    fi

    # Backup: full diff (unstaged + staged) of every currently-dirty file, independent of
    # whatever git's own stash does with it -- the source incident's whole point is that a clean
    # git exit is not proof of survival, so this backup is the recovery path of last resort.
    local backup_dir backup_file ts
    backup_dir="$(_resolve_backup_dir)"
    mkdir -p "${backup_dir}" 2>/dev/null || true
    ts="$(date -u +%Y%m%dT%H%M%SZ 2>/dev/null || echo now)"
    backup_file="${backup_dir}/${ts}.patch"
    { git -C "${REPO_DIR}" diff; git -C "${REPO_DIR}" diff --cached; } > "${backup_file}" 2>/dev/null

    # Prune old backups for this repo (keep newest BACKUP_RETAIN).
    if [[ -d "${backup_dir}" ]]; then
        # shellcheck disable=SC2012
        ls -t "${backup_dir}"/*.patch 2>/dev/null | tail -n "+$(( BACKUP_RETAIN + 1 ))" | xargs -r rm -f 2>/dev/null || true
    fi

    git -C "${REPO_DIR}" pull --rebase --autostash origin "${INTEGRATION_BRANCH}" > "${backup_dir}/${ts}.pull-output.log" 2>&1
    local pull_exit=$?

    # Post-check 1: any unmerged path, or literal conflict markers left in the tree.
    local unmerged post_markers
    unmerged="$(git -C "${REPO_DIR}" status --porcelain 2>/dev/null | grep -E '^(UU|AA|DD|AU|UA|UD|DU) ' || true)"
    post_markers="$(_has_conflict_markers "${REPO_DIR}" ${dirty_files})"
    if [[ "${pull_exit}" -ne 0 || -n "${unmerged}" || -n "${post_markers}" ]]; then
        _emit_needs_resolution "${starve_payload}" "pull exit=${pull_exit}; unmerged paths: $(echo "${unmerged}" | tr '\n' ' ' || echo none); conflict markers in: $(echo "${post_markers}" | tr '\n' ' ' || echo none)" "${backup_file}"
        return 0
    fi

    # Post-check 2: content-integrity, only for files that went dirty -> clean (a file still
    # dirty is unambiguously still there; the risk class this exists for is silent convergence-
    # or-loss on a file that now reads as clean).
    local f now_dirty suspected=()
    now_dirty="$(git -C "${REPO_DIR}" status --porcelain 2>/dev/null | sed -E 's/^...//')"
    for f in ${dirty_files}; do
        case "${now_dirty}" in *"${f}"*) continue;; esac   # still dirty -- nothing to verify
        local verdict
        verdict="$(_check_content_integrity "${REPO_DIR}" "${backup_file}" "${f}")"
        case "${verdict}" in SUSPECTED_LOSS*|FILE_MISSING*) suspected+=("${f}: ${verdict}");; esac
    done
    if [[ "${#suspected[@]}" -gt 0 ]]; then
        _emit_needs_resolution "${starve_payload}" "content-integrity check found suspected silent loss:
$(printf '  - %s\n' "${suspected[@]}")" "${backup_file}"
        return 0
    fi

    # Full success -- log locally, print nothing (caller suppresses the ping on empty output).
    printf '[%s] reconciled %s (slot %s) cleanly, content verified, backup at %s\n' \
        "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${REPO_NAME}" "${SLOT_ID:-?}" "${backup_file}" \
        >> "${backup_dir}/success.log" 2>/dev/null || true
    return 0
}

_resolve_backup_dir() {
    local ws="${WORKSPACE_PATH}" cwd
    if [[ -z "${ws}" ]]; then
        cwd="$(cd "${REPO_DIR}" && pwd)"
        while [[ "$(basename "${cwd}")" != "unified-trading-system-repos" && "${cwd}" != "/" ]]; do
            cwd="$(dirname "${cwd}")"
        done
        [[ "${cwd}" != "/" ]] && ws="${cwd}"
    fi
    if [[ -n "${ws}" ]]; then
        printf '%s/.tabs/.auto-reconcile-backups/slot-%s/%s' "${ws}" "${SLOT_ID:-na}" "${REPO_NAME}"
    else
        printf '%s/.auto-reconcile-backups/slot-%s/%s' "${TMPDIR:-/tmp}" "${SLOT_ID:-na}" "${REPO_NAME}"
    fi
}

if [[ "${AUTO_RECONCILE_LIB_ONLY:-0}" != "1" ]]; then
    main
fi
