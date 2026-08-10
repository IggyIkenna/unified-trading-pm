#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# cleanup-stale-tmp-parquet-scratch.sh — TTL reaper for large one-off parquet
# scratch on the shared orchestrator host.
#
# The shared host mounts /tmp as a fixed 8GB RAM-backed tmpfs (independent of the
# healthy root disk) that has repeatedly hit 100% from accumulated one-off parquet
# scratch — breaking unrelated pytest runs fleet-wide with "No space left on device"
# (host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md). Root-cause fix is ROUTING
# (instruments-service scripts now stage their large enum-univ-*/cefi-corrector-*
# parquets in $HOME/.cache/instruments-scratch on the root disk, not /tmp), but the
# tmpfs still needs a belt-and-suspenders reaper for: (a) any one-off ad-hoc script
# that still writes a parquet to /tmp, and (b) orphans left in the ROUTED scratch dir
# when a run is SIGKILLed before its `finally: os.unlink()` runs.
#
# Same liveness-gated pattern as cleanup-stale-qg-tmp.sh /
# cleanup-stale-manifest-consolidate-tmp.sh: never touches a file with a live holder.
#
# Usage:
#   cleanup-stale-tmp-parquet-scratch.sh                   # sweep, 6h threshold
#   cleanup-stale-tmp-parquet-scratch.sh --min-age 720     # custom threshold (minutes)
#   cleanup-stale-tmp-parquet-scratch.sh --dry-run         # report only, don't delete
#   cleanup-stale-tmp-parquet-scratch.sh --quiet           # only print removals, not no-ops
#
# Cron install: scripts/dev/install-cleanup-stale-tmp-parquet-scratch-cron.sh
#
# Codex SSOT: codex/05-infrastructure/shared-host-tmp-tmpfs-capacity.md,
#             codex/05-infrastructure/per-tab-worktrees.md § "Cron-based FF puller"
#             (same self-pull / idempotent-install convention as the FF-pull cron)

set -euo pipefail

MIN_AGE_MIN=360 # 6h: comfortably past a single run's runtime, short enough that an
                # 8G tmpfs can't accumulate to 100% from a killed run between sweeps.
DRY_RUN=0
QUIET=0

while [[ $# -gt 0 ]]; do
    case "$1" in
        --min-age) MIN_AGE_MIN="$2"; shift 2;;
        --dry-run) DRY_RUN=1; shift;;
        --quiet) QUIET=1; shift;;
        -h|--help) sed -n '2,35p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

# Candidate roots: (1) the routed instruments-service scratch dir (root disk — this
# is where large enum-univ-*/cefi-corrector-* parquets now land; orphaned here on a
# SIGKILL, harmless to the tmpfs but worth reclaiming), and (2) /tmp itself for any
# one-off ad-hoc parquet scratch that still defaults there.
CANDIDATE_ROOTS=("${HOME}/.cache/instruments-scratch" "/tmp")

# Name globs for one-off parquet/scratch files. Scoped to the recurring offender
# classes — deliberately NOT pytest-of-* (owned by cleanup-stale-qg-tmp.sh) nor
# claude-* (owned by cleanup-stale-claude-session-tmp.sh).
NAME_GLOBS=("*.parquet" "enum-univ-*" "enum-shard-*" "cefi-corrector-*" "cefi-corrector-out-*"
    "avail_idx*" "cefi_availability_index*" "repro-*" "regen-ldr-plans-*" "node-compile-cache"
    "actionlint*" "kalshi_*.json" "ao_clone_check")

log() {
    # $1=kind: "removal"/"summary" always print; "live" (skip-live noop) suppressed by --quiet.
    local kind="$1"; shift
    if [ "${QUIET}" = "1" ] && [ "${kind}" = "live" ]; then
        return 0
    fi
    echo "$*"
}

is_in_use() {
    # $1=path. True (0) if something still holds an open fd on it.
    local path="$1"
    if command -v fuser >/dev/null 2>&1; then
        fuser -s "${path}" 2>/dev/null && return 0
        return 1
    fi
    # fuser unavailable: fall back to mtime-only gating (already applied via -mmin below).
    return 1
}

removed=0
skipped_live=0

for root in "${CANDIDATE_ROOTS[@]}"; do
    [ -d "${root}" ] || continue
    for glob in "${NAME_GLOBS[@]}"; do
        # Sweep BOTH files and dirs (the offender classes include dirs like
        # repro-venv / node-compile-cache / regen-ldr-plans-*). `-mmin` on a dir
        # reflects the newest entry under it (a live dir is perpetually fresh, so
        # the mtime gate keeps us well clear of active work), and the liveness
        # gate below is the real safety.
        while IFS= read -r -d '' f; do
            if is_in_use "${f}"; then
                skipped_live=$((skipped_live + 1))
                log live "[skip-live] ${f}"
                continue
            fi
            if [ "${DRY_RUN}" = "1" ]; then
                log removal "[dry-run] would remove ${f}"
            else
                rm -rf -- "${f}"
                removed=$((removed + 1))
                log removal "[removed] ${f}"
            fi
        done < <(find "${root}" -maxdepth 1 \( -type f -o -type d \) -name "${glob}" -mmin "+${MIN_AGE_MIN}" -print0 2>/dev/null)
    done
done

log summary "[done] removed=${removed} skipped_live=${skipped_live} min_age_min=${MIN_AGE_MIN} dry_run=${DRY_RUN}"
exit 0
