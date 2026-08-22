#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# prune-prek-patch-cache.sh — bounded retention sweep for the shared prek stash-patch cache.
#
# prek's `UnstagedChangesRestorer::restore()` never deletes a patch file after
# successfully applying it (happy path AND failure path both leak), and `prek cache gc`
# (the one cache-pruning command prek ships) does NOT touch `patches/` either — confirmed
# directly: ran it against a populated isolated PREK_HOME, output was "Nothing to clean"
# with the patches still present after. So `~/.cache/prek/patches/` (HOME-level, shared by
# every slot/session on this host) grows without bound as long as any hook runs a stash
# cycle — 520 files / 6.7MB measured on one host in one investigation session alone.
#
# This is a bounded-retention prune, NOT a root-cause fix for the separate (and more
# severe) prek stash/restore corruption bug tracked in the same issue doc — see
# plans/archive/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md.
# A patch is only ever read by the same in-process struct that wrote it (never re-selected
# by a directory scan/mtime-newest lookup — confirmed against prek's own keeper.rs source),
# so an old patch file sitting in this directory is dead weight, not live state a future
# prek invocation could still consume.
#
# Usage:
#   prune-prek-patch-cache.sh                    # sweep with default 7-day retention
#   prune-prek-patch-cache.sh --patches-dir <path>
#   prune-prek-patch-cache.sh --min-age-days <N>  # retention threshold in days (default 7)
#   prune-prek-patch-cache.sh --dry-run           # report what would be removed; don't delete
#   prune-prek-patch-cache.sh --quiet             # only print removals + summary, not skip-live noise
#
# Cron install: scripts/dev/install-prune-prek-patch-cache-cron.sh
#
# plans/archive/issues/prek_patch_cache_replays_stale_diff_onto_unrelated_files_2026_07_29.md
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Cron-based FF puller"
#             (same self-pull / idempotent-install convention as the FF-pull cron)

set -euo pipefail

MIN_AGE_DAYS=7
DRY_RUN=0
QUIET=0
PATCHES_DIR="${HOME}/.cache/prek/patches"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --patches-dir) PATCHES_DIR="$2"; shift 2;;
        --min-age-days) MIN_AGE_DAYS="$2"; shift 2;;
        --dry-run) DRY_RUN=1; shift;;
        --quiet) QUIET=1; shift;;
        -h|--help) sed -n '2,26p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

log() {
    # $1=kind: "removal"/"summary" always print; "live" (skip-live noop) suppressed by --quiet.
    local kind="$1"; shift
    if [ "${QUIET}" = "1" ] && [ "${kind}" = "live" ]; then
        return 0
    fi
    echo "$*"
}

is_in_use() {
    # $1=file path. True (0) if some process still holds an open fd on this exact file —
    # belt-and-suspenders on top of the mtime gate; a patch this old should never still be
    # open, but a hung/stuck prek invocation is exactly the case worth not touching.
    local path="$1"
    if command -v fuser >/dev/null 2>&1; then
        fuser -s "${path}" 2>/dev/null && return 0
        return 1
    fi
    # No fuser available: fall back to mtime-only gating (already applied via -mmin below).
    return 1
}

if [ ! -d "${PATCHES_DIR}" ]; then
    log summary "[skip] patches dir does not exist: ${PATCHES_DIR}"
    exit 0
fi

min_age_min=$(( MIN_AGE_DAYS * 24 * 60 ))
before_kb=$(du -sk "${PATCHES_DIR}" 2>/dev/null | cut -f1 || echo 0)
before_count=$(find "${PATCHES_DIR}" -maxdepth 1 -name '*.patch' 2>/dev/null | wc -l | tr -d ' ')

removed=0
skipped_live=0

while IFS= read -r -d '' stale_patch; do
    if is_in_use "${stale_patch}"; then
        skipped_live=$((skipped_live + 1))
        log live "[skip-live] ${stale_patch}"
        continue
    fi
    if [ "${DRY_RUN}" = "1" ]; then
        log removal "[dry-run] would remove ${stale_patch}"
    else
        rm -f -- "${stale_patch}"
        removed=$((removed + 1))
        log removal "[removed] ${stale_patch}"
    fi
done < <(find "${PATCHES_DIR}" -maxdepth 1 -name '*.patch' -mmin "+${min_age_min}" -print0 2>/dev/null)

after_kb=$(du -sk "${PATCHES_DIR}" 2>/dev/null | cut -f1 || echo 0)
after_count=$(find "${PATCHES_DIR}" -maxdepth 1 -name '*.patch' 2>/dev/null | wc -l | tr -d ' ')
freed_mb=$(( (before_kb - after_kb) / 1024 ))

log summary "[done] patches_dir=${PATCHES_DIR} before_count=${before_count} after_count=${after_count} removed=${removed} skipped_live=${skipped_live} freed_mb=${freed_mb} min_age_days=${MIN_AGE_DAYS} dry_run=${DRY_RUN}"
exit 0
