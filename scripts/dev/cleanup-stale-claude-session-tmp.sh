#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# cleanup-stale-claude-session-tmp.sh — belt-and-suspenders sweep for stale Claude Code
# per-session /tmp scratch. Closes the gap left by cleanup-stale-qg-tmp.sh, which only
# sweeps pytest/QG scratch under ${HOME}/.cache/qg-tmp + legacy /tmp/pytest-of-* and never
# touches the harness's OWN scratch.
#
# shared_host_tmp_tmpfs_exhaustion recurred on 2026-07-26 (first hit 2026-07-08) because
# Claude Code's per-session scratch under /tmp/claude-<uid>/<project-slug>/<session-id>/
# {scratchpad,tasks} was never swept by anything. On this host it alone measured 1.8G of the
# 2G tmpfs at the time this script was written (363 session dirs, 294 of them >24h old).
#
# A session can be idle-but-alive for HOURS during a long background wait (a dispatched
# sub-agent, a VM watch, ScheduleWakeup) — mtime-only staleness is NOT a safe sole gate here.
# Mirrors cleanup-stale-qg-tmp.sh's is_in_use() (fuser/lsof open-fd check) near-verbatim: a
# session dir is only removed when BOTH the staleness threshold AND the liveness check pass.
# If neither fuser nor lsof is available, the dir is treated as in-use (skip) rather than
# falling back to mtime-only — unlike the QG script's pytest scratch (short-lived runs),
# a session's liveness cannot be safely inferred from mtime alone.
#
# Usage:
#   cleanup-stale-claude-session-tmp.sh                # sweep with default 180-min threshold
#   cleanup-stale-claude-session-tmp.sh --min-age 60    # custom threshold (minutes)
#   cleanup-stale-claude-session-tmp.sh --dry-run       # report what would be removed; don't delete
#   cleanup-stale-claude-session-tmp.sh --quiet         # only print removals, not no-ops
#
# Cron install: scripts/dev/install-cleanup-stale-claude-session-tmp-cron.sh
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Cron-based FF puller"
#             (same self-pull / idempotent-install convention as the FF-pull cron)

set -euo pipefail

MIN_AGE_MIN=180
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

# Session dirs live two levels below /tmp/claude-<uid>: <project-slug>/<session-id>/.
# Only the invoking user's own tree is swept (per-uid, mirrors the /tmp/claude-<uid> layout
# itself) — a shared host with multiple uids needs one cron per uid, same as the layout.
CLAUDE_TMP_ROOT="/tmp/claude-$(id -u)"

log() {
    # $1=kind: "removal"/"summary" always print; "live" (skip-live noop) suppressed by --quiet.
    local kind="$1"; shift
    if [ "${QUIET}" = "1" ] && [ "${kind}" = "live" ]; then
        return 0
    fi
    echo "$*"
}

is_in_use() {
    # $1=path. True (0) if something still holds an open fd under this dir, OR if liveness
    # can't be checked at all (no fuser/lsof) — in that case we refuse to guess.
    local path="$1"
    if command -v fuser >/dev/null 2>&1; then
        fuser -s "${path}" 2>/dev/null && return 0
        # fuser only checks the dir inode itself; also check open files beneath it.
        # Collect into an array first, and only invoke fuser when non-empty -- `xargs -r`
        # exits 0 (success) on empty stdin, which would otherwise make an EMPTY dir (no
        # regular files, e.g. a scratchpad nobody wrote to) look "in use" on every call.
        local beneath=()
        while IFS= read -r -d '' f; do beneath+=("${f}"); done < <(find "${path}" -type f -print0 2>/dev/null)
        if [ "${#beneath[@]}" -gt 0 ] && fuser -s "${beneath[@]}" 2>/dev/null; then
            return 0
        fi
        return 1
    fi
    if command -v lsof >/dev/null 2>&1; then
        [ -n "$(lsof +D "${path}" 2>/dev/null)" ] && return 0
        return 1
    fi
    return 0
}

removed=0
skipped_live=0
if [ -d "${CLAUDE_TMP_ROOT}" ]; then
    while IFS= read -r -d '' session_dir; do
        if is_in_use "${session_dir}"; then
            skipped_live=$((skipped_live + 1))
            log live "[skip-live] ${session_dir}"
            continue
        fi
        if [ "${DRY_RUN}" = "1" ]; then
            log removal "[dry-run] would remove ${session_dir}"
        else
            rm -rf -- "${session_dir}"
            removed=$((removed + 1))
            log removal "[removed] ${session_dir}"
        fi
    done < <(find "${CLAUDE_TMP_ROOT}" -mindepth 2 -maxdepth 2 -type d -mmin "+${MIN_AGE_MIN}" -print0 2>/dev/null)
fi

log summary "[done] removed=${removed} skipped_live=${skipped_live} min_age_min=${MIN_AGE_MIN} dry_run=${DRY_RUN} root=${CLAUDE_TMP_ROOT}"
exit 0
