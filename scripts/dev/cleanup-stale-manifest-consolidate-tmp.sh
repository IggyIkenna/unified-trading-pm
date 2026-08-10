#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# cleanup-stale-manifest-consolidate-tmp.sh — TTL reaper for abandoned
# manifest-consolidator scratch on this host.
#
# `unified_trading_library.manifest_consolidator._duckdb_merge_payload` opens
# `tempfile.TemporaryDirectory(prefix="manifest-consolidate-")` while merging
# canonical + shard parquet in DuckDB. Per
# `/codex/05-infrastructure/manifest-consolidator-ssot.md` this code is meant
# to run ONLY inside the per-asset_group `manifest-consolidator-{ag}` Cloud
# Run Job (ephemeral container, destroyed after each execution) — never on a
# persistent host. The 2026-08-08 finding
# (`plans/active/issues/shared_host_home_filesystem_full_2026_07_26.md` §
# "Orphaned manifest-consolidator scratch") shows this DOES land on a
# persistent VM disk when the code is invoked directly on a host instead
# (e.g. an ad-hoc/manual local run for debugging) — 3 dirs under
# `/home/ubuntu/tmp` totaling 175G, `lsof +D` empty, quiescent 3 days,
# abandoned mid-cycle with no automated owner to clean it up.
#
# No single deterministic in-repo "writer" exists to fix at the source — the
# only code path that creates this prefix is the Cloud Run Job's own merge
# step, and Cloud Run containers don't persist scratch across executions, so
# a host-level accumulation implies a one-off manual/local invocation each
# time, not a recurring bug to patch. Per
# `infra_satellite_ao_dispatch_batch10_2026_08_09.md` todo 2's own accepted
# alternative resolution ("if a legitimate VM-side spill is unavoidable,
# build a TTL reaper"), this is that reaper — same liveness-check pattern as
# `cleanup-stale-qg-tmp.sh` (never touches a dir with a live holder).
#
# Usage:
#   cleanup-stale-manifest-consolidate-tmp.sh                  # sweep, 48h threshold
#   cleanup-stale-manifest-consolidate-tmp.sh --min-age 60     # custom threshold (minutes)
#   cleanup-stale-manifest-consolidate-tmp.sh --dry-run        # report only, don't delete
#   cleanup-stale-manifest-consolidate-tmp.sh --quiet          # only print removals, not no-ops
#   cleanup-stale-manifest-consolidate-tmp.sh --root /some/dir # add an extra candidate root
#
# Cron install: scripts/dev/install-cleanup-stale-manifest-consolidate-tmp-cron.sh
#
# Codex SSOT: codex/05-infrastructure/manifest-consolidator-ssot.md,
#             codex/05-infrastructure/per-tab-worktrees.md § "Cron-based FF puller"
#             (same self-pull / idempotent-install convention as the FF-pull cron)

set -euo pipefail

MIN_AGE_MIN=2880 # 48h, per the todo's own done-when threshold
DRY_RUN=0
QUIET=0
EXTRA_ROOTS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --min-age) MIN_AGE_MIN="$2"; shift 2;;
        --dry-run) DRY_RUN=1; shift;;
        --quiet) QUIET=1; shift;;
        --root) EXTRA_ROOTS+=("$2"); shift 2;;
        -h|--help) sed -n '2,33p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

# Candidate roots: the two locations this scratch has been observed under —
# the documented default (`tempfile.gettempdir()` with no TMPDIR override,
# i.e. /tmp) plus the home-dir scratch path the 2026-08-08 finding actually
# recorded (`/home/ubuntu/tmp`, implying TMPDIR was redirected there for that
# invocation — the same home-dir-redirect idiom `cleanup-stale-qg-tmp.sh`'s
# own precedent fix established for the tmpfs-exhaustion class of bug).
CANDIDATE_ROOTS=("/tmp" "${HOME}/tmp" "${EXTRA_ROOTS[@]}")

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
    # fuser, not lsof: `lsof +D` exits non-zero on this host even when it DOES
    # find an open file, because of an unrelated tracefs-stat WARNING
    # ("can't stat() tracefs file system /sys/kernel/debug/tracing") that
    # makes lsof report its own output as "incomplete" and exit 1 regardless
    # of whether the search itself succeeded — confirmed live during this
    # script's own synthetic-trigger test (an fd held open on a scratch file
    # was still swept because `lsof +D ... >/dev/null 2>&1` masked BOTH the
    # real match and the spurious warning behind the same non-zero exit).
    # fuser's exit code is unaffected by this and is the SAME primary check
    # `cleanup-stale-qg-tmp.sh` already uses for this exact dead-scratch-vs-
    # live-scratch distinction — mirrored here rather than reintroducing a
    # second, less reliable mechanism.
    local path="$1"
    if command -v fuser >/dev/null 2>&1; then
        fuser -s "${path}" 2>/dev/null && return 0
        local beneath=()
        while IFS= read -r -d '' f; do beneath+=("${f}"); done < <(find "${path}" -type f -print0 2>/dev/null)
        if [ "${#beneath[@]}" -gt 0 ] && fuser -s "${beneath[@]}" 2>/dev/null; then
            return 0
        fi
        return 1
    fi
    # fuser unavailable: fall back to mtime-only gating (already applied via
    # -mmin below) — conservative but not silently unsafe.
    return 1
}

removed=0
skipped_live=0

for root in "${CANDIDATE_ROOTS[@]}"; do
    [ -d "${root}" ] || continue
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
    done < <(find "${root}" -maxdepth 1 -type d -name "manifest-consolidate-*" -mmin "+${MIN_AGE_MIN}" -print0 2>/dev/null)
done

log summary "[done] removed=${removed} skipped_live=${skipped_live} min_age_min=${MIN_AGE_MIN} dry_run=${DRY_RUN}"
exit 0
