#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# prune-uv-cache.sh — periodic sweep of the shared `.uv-cache` to bound its growth.
#
# plans/active/issues/host_root_disk_full_transient_2026_07_13.md: the host's root
# filesystem hit 100% full (0 bytes free) TWICE in one session. Investigation found
# the shared UV_CACHE_DIR (${WORKSPACE_ROOT}/.uv-cache — every one of the 16 slots'
# `uv sync` calls reads/writes it) had grown to 12G with no prune schedule. A single
# manual `uv cache prune` run (2026-07-13) reclaimed 5.7GiB in ~3s — `uv cache prune`
# (no `--force`) only removes objects unreachable from any current lockfile/environment
# and does its own in-use checks, so it's safe to run unconditionally on a schedule
# even while OTHER slots are mid-`uv sync` (per `uv cache prune --help`: `--force`
# is the flag that "ignores in-use checks" — the default respects them).
#
# This is the SHARED-CACHE half of the disk-growth finding. The other, larger driver
# (~150-200G across 16 slots' per-repo `.venv` dirs, ~1.3-2.6G each for the
# numpy/pandas/pyarrow/duckdb/scikit-learn-heavy repos) is NOT touched here — those
# are LIVE, in-use by whichever slot is mid-session, and deleting one out from under
# an active agent risks breaking its `quality-gates.sh`/`quickmerge.sh` mid-run
# (the same "never overwrite live foreign WIP without a liveness check" principle
# codified for VM launchers in
# plans/active/issues/features_sports_parallel_backfill_vm_name_collision_2026_07_13.md).
# A per-slot `.venv` prune needs its OWN liveness-aware follow-on (todo below), not a
# blanket cron.
#
# Usage:
#   prune-uv-cache.sh                # prune with defaults
#   prune-uv-cache.sh --cache-dir <path>
#   prune-uv-cache.sh --quiet        # suppress the [noop]/summary line's byte count on stdout
#
# Cron install: scripts/dev/install-prune-uv-cache-cron.sh
#
# Codex SSOT: codex/05-infrastructure/per-tab-worktrees.md § "Cron-based FF puller"
#             (same self-pull / idempotent-install convention as the FF-pull cron)

set -euo pipefail

QUIET=0
CACHE_DIR="${UV_CACHE_DIR:-${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}/.uv-cache}"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --cache-dir) CACHE_DIR="$2"; shift 2;;
        --quiet) QUIET=1; shift;;
        -h|--help) sed -n '2,29p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0;;
        *) echo "Unknown arg: $1" >&2; exit 2;;
    esac
done

if [ ! -d "${CACHE_DIR}" ]; then
    echo "[skip] cache dir does not exist: ${CACHE_DIR}"
    exit 0
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found on PATH — cannot prune" >&2
    exit 1
fi

before_kb=$(du -sk "${CACHE_DIR}" 2>/dev/null | cut -f1 || echo 0)

output="$(UV_CACHE_DIR="${CACHE_DIR}" uv cache prune 2>&1)"
rc=$?

after_kb=$(du -sk "${CACHE_DIR}" 2>/dev/null | cut -f1 || echo 0)
freed_mb=$(( (before_kb - after_kb) / 1024 ))

if [ "${QUIET}" = "1" ]; then
    echo "[done] cache_dir=${CACHE_DIR} freed_mb=${freed_mb} rc=${rc}"
else
    echo "${output}"
    echo "[done] cache_dir=${CACHE_DIR} before_mb=$((before_kb / 1024)) after_mb=$((after_kb / 1024)) freed_mb=${freed_mb} rc=${rc}"
fi

exit "${rc}"
