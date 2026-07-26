#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# cleanup-stale-qg-tmp.sh — belt-and-suspenders sweep for stale QG scratch dirs.
#
# The P2 fix for shared_host_tmp_tmpfs_exhaustion_2026_07_08 redirects pytest's
# TMPDIR (and QG_CACHE_ROOT) to ${HOME}/.cache/qg-tmp, a root-partition path with
# ~95G free vs the host's 2G /tmp tmpfs — this fully resolves cross-slot QG
# contention on its own. This script is the P3 belt-and-suspenders follow-up:
# a periodic cleanup of scratch dirs left behind by (a) an interrupted/killed QG
# run under the new TMPDIR target, and (b) any tool that still defaults to the
# real /tmp (bypassing TMPDIR) and drops pytest-of-<user> dirs there.
#
# Never touches a dir with a live holder: skips anything with an open fd or a
# still-running process under it (via `fuser`/`lsof` if available, else a
# conservative mtime-only threshold well past any single QG run's runtime).
#
# Usage:
#   cleanup-stale-qg-tmp.sh                # sweep with default 60-min threshold
#   cleanup-stale-qg-tmp.sh --min-age 120   # custom threshold (minutes)
#   cleanup-stale-qg-tmp.sh --dry-run       # report what would be removed; don't delete
#   cleanup-stale-qg-tmp.sh --quiet         # only print removals, not no-ops
#
# Cron install: scripts/dev/install-cleanup-stale-qg-tmp-cron.sh
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Cron-based FF puller"
#             (same self-pull / idempotent-install convention as the FF-pull cron)

set -euo pipefail

MIN_AGE_MIN=60
DRY_RUN=0
QUIET=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --min-age) MIN_AGE_MIN="$2"; shift 2;;
        --dry-run) DRY_RUN=1; shift;;
        --quiet) QUIET=1; shift;;
        -h|--help) sed -n '2,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

# Candidate roots: the new QG scratch target (primary) + legacy /tmp pytest dirs
# (belt-and-suspenders — covers a tool that still defaults to /tmp, ignoring TMPDIR).
QG_TMP_ROOT="${HOME}/.cache/qg-tmp"
CANDIDATE_PATTERNS=(
    "${QG_TMP_ROOT}/pytest-of-*"
    "/tmp/pytest-of-*"
)

log() {
    # $1=kind: "removal"/"summary" always print; "live" (skip-live noop) suppressed by --quiet.
    local kind="$1"; shift
    if [ "${QUIET}" = "1" ] && [ "${kind}" = "live" ]; then
        return 0
    fi
    echo "$*"
}

is_in_use() {
    # $1=path. True (0) if something still holds an open fd under this dir.
    local path="$1"
    if command -v fuser >/dev/null 2>&1; then
        fuser -s "${path}" 2>/dev/null && return 0
        # fuser only checks the dir inode itself; also check open files beneath it.
        # Collect into an array first, and only invoke fuser when non-empty -- `xargs -r`
        # exits 0 (success) on empty stdin, which would otherwise make an EMPTY dir look
        # "in use" on every call (found while building cleanup-stale-claude-session-tmp.sh,
        # which mirrors this function -- there it was a 344/363 false-positive skip rate).
        local beneath=()
        while IFS= read -r -d '' f; do beneath+=("${f}"); done < <(find "${path}" -type f -print0 2>/dev/null)
        if [ "${#beneath[@]}" -gt 0 ] && fuser -s "${beneath[@]}" 2>/dev/null; then
            return 0
        fi
        return 1
    fi
    # No fuser available: fall back to mtime-only gating (already applied via -mmin below).
    return 1
}

removed=0
skipped_live=0
for pattern in "${CANDIDATE_PATTERNS[@]}"; do
    root_dir="$(dirname "${pattern}")"
    name_glob="$(basename "${pattern}")"
    [ -d "${root_dir}" ] || continue
    while IFS= read -r -d '' stale_dir; do
        if is_in_use "${stale_dir}"; then
            skipped_live=$((skipped_live + 1))
            log live "[skip-live] ${stale_dir}"
            continue
        fi
        if [ "${DRY_RUN}" = "1" ]; then
            log removal "[dry-run] would remove ${stale_dir}"
        else
            rm -rf -- "${stale_dir}"
            removed=$((removed + 1))
            log removal "[removed] ${stale_dir}"
        fi
    done < <(find "${root_dir}" -maxdepth 1 -name "${name_glob}" -mmin "+${MIN_AGE_MIN}" -print0 2>/dev/null)
done

log summary "[done] removed=${removed} skipped_live=${skipped_live} min_age_min=${MIN_AGE_MIN} dry_run=${DRY_RUN}"
exit 0
