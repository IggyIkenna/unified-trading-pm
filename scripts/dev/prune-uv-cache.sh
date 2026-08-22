#!/usr/bin/env bash
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
# prune-uv-cache.sh — periodic sweep of the shared `.uv-cache` to bound its growth.
#
# plans/active/issues/host_root_disk_full_transient_2026_07_13.md: the host's root
# filesystem hit 100% full (0 bytes free) TWICE in one session. Investigation found
# the shared UV_CACHE_DIR (${WORKSPACE_ROOT}/.tabs/.uv-cache — every one of the 16 slots'
# `uv sync` calls reads/writes it) had grown to 12G with no prune schedule. (Relocated
# INSIDE .tabs/ 2026-08-09 — see tabs_mount_boundary_defeats_uv_cache_hardlink_dedup_2026_08_09.md.) A single
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
# INSIDE .tabs/ (tabs_mount_boundary_defeats_uv_cache_hardlink_dedup_2026_08_09): a cache
# dir sibling of .tabs/ sits on a different mount boundary than .tabs/<N>/<repo>/.venv on
# this host — hardlink() returns EXDEV across it and uv falls back to a full copy per slot.
# Must match base-service.sh's / install-uv-cache-shell-env.sh's relocated default or this
# prunes a directory the fleet no longer writes to.
CACHE_DIR="${UV_CACHE_DIR:-${WORKSPACE_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}/.tabs/.uv-cache}"

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

# Resolve `uv` explicitly — do NOT rely on an inherited PATH (2026-07-16).
#
# This script's whole purpose is to run FROM CRON, and cron's PATH is
# `/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/snap/bin` — it does NOT
# include `~/.local/bin`, which is where the uv installer puts the binary and where every
# host in this fleet actually has it. A LOGIN shell picks it up via .profile, so
# `command -v uv` succeeds when a human tests it by hand and fails under the cron it was
# written for. Measured on the central VM 2026-07-16: interactive PATH finds
# /home/ubuntu/.local/bin/uv; the non-interactive PATH does not.
#
# The failure was silent-by-design: the script exits 1 with a message the cron redirects
# into a log nobody reads, so `crontab -l` shows the job installed and the cache is never
# pruned. The install would have looked done and achieved nothing — which is exactly the
# class of not-actually-running failure the 2026-07-16 audit kept finding.
_resolve_uv() {
    if command -v uv >/dev/null 2>&1; then command -v uv; return 0; fi
    local _c
    for _c in "${HOME}/.local/bin/uv" "${HOME}/.cargo/bin/uv" /usr/local/bin/uv /opt/uv/bin/uv; do
        [[ -x "${_c}" ]] && { printf '%s\n' "${_c}"; return 0; }
    done
    return 1
}
if ! UV_BIN="$(_resolve_uv)"; then
    echo "uv not found (checked PATH, ~/.local/bin, ~/.cargo/bin, /usr/local/bin, /opt/uv/bin) — cannot prune" >&2
    exit 1
fi

before_kb=$(du -sk "${CACHE_DIR}" 2>/dev/null | cut -f1 || echo 0)

output="$(UV_CACHE_DIR="${CACHE_DIR}" "${UV_BIN}" cache prune 2>&1)"
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
