#!/usr/bin/env bash
# Epic: infrastructure_master (orchestrator VM /tmp tmpfs exhaustion remediation, 2026-08-10)
# Lifecycle: permanent
# Delete-when: NA
#
# tmpfs-disk-cleanup.sh — periodic aged-entry reclaim for the shared orchestrator VM's /tmp.
#
# WHY THIS EXISTS: /tmp on the orchestrator VM is an 8 GiB **tmpfs**, and it filled to 100%
# (15 MiB free) on 2026-08-10. A full /tmp is not a cosmetic problem there — `tmux_spawn.spawn`
# allocates under /tmp, so every escalation dispatch died with
#   tmux_spawn.spawn failed: [Errno 28] No space left on device
# which re-queued the escalation, which re-dispatched, which failed again: the PM SIT walls
# reached 190+ attempts on that treadmill. The measured contents at the time:
#   2,148 `tmp.*` mktemp dirs (2.7 GiB, a new one every ~1.3s), a 1.8 GiB
#   defi_availability_index.parquet, 2x 225 MiB mfest_cfe_v*.parquet, a 1.5 GiB pmgate_ci.* QG
#   scratch dir and an 808 MiB repro-venv — none with an open handle.
#
# WHY systemd-tmpfiles IS NOT ENOUGH (the thing that was already in place): the VM carries
# /etc/tmpfiles.d/tmp-aggressive-cleanup.conf (`D /tmp 1777 root root 1d`), which correctly
# overrides Ubuntu's 30d default — but it is swept by systemd-tmpfiles-clean.timer, which runs
# ONCE A DAY. A leak producing ~65k dirs/day plus multi-GiB parquet fills 8 GiB many times over
# between two sweeps, so the daily sweep can only ever clean up after the outage it failed to
# prevent. This script is the same idea at a cadence matched to the actual fill rate. It does NOT
# replace the tmpfiles.d policy; it runs alongside it.
#
# This is the disk-side sibling of docker-disk-cleanup.sh (same host, same deploy pattern,
# same one-shot-timer shape) — see that script's header for the host-wide-not-per-pool rationale.
#
# DELIBERATELY NEVER TOUCHED (the denylist below is the load-bearing safety property):
#   - /tmp/tmux-*            tmux server sockets. Removing these unaddresses every live
#                            `orch-slot-N` session at once — a worse outage than a full disk.
#   - /tmp/ao-fleet-tmux     the fleet's tmux server socket dir since the 2026-08-13
#                            TMUX_TMPDIR isolation fix (ao_tmux_session_loss_mid_task_root_cause_2026_08_10)
#                            moved it off the ambient `tmux-<uid>` path this script already denies —
#                            same rationale as the entry above, just a name this list didn't know about
#                            yet. The live open-handle check below is the actual safety net regardless of
#                            basename, but a name match is a cheaper, blast-radius-scoped first line of
#                            defense and should track every known tmux-socket home, not just the default one.
#   - /tmp/systemd-private-* systemd per-unit private dirs for RUNNING units.
#   - /tmp/snap-private-*    snap confinement dirs (the SSM agent itself lives behind one).
#   - /tmp/.X11-unix, /tmp/.ICE-unix, and any other .*-unix socket dirs.
#   - ANYTHING with a live open file handle, regardless of age (checked per entry).
set -euo pipefail

LOG_PREFIX="[tmpfs-disk-cleanup]"

# Age floor in minutes. An entry younger than this is assumed in-flight and is never considered,
# even if nothing holds it open — a process between mktemp and first write has no handle yet.
# 120 is the value verified safe by hand on 2026-08-10 (every entry older than 2h was orphaned).
AGE_MIN="${TMPFS_CLEANUP_AGE_MIN:-120}"
# Loud-warn threshold: if /tmp is still above this after a pass, the leak is outrunning us and
# the fill rate itself needs fixing (see the issue doc), not a shorter interval here.
WARN_PCT="${TMPFS_CLEANUP_WARN_PCT:-85}"

_usage_pct() { df --output=pcent /tmp 2>/dev/null | tail -1 | tr -dc '0-9'; }
_avail_h() { df -h --output=avail /tmp 2>/dev/null | tail -1 | tr -d ' '; }

echo "${LOG_PREFIX} before: $(_usage_pct)% used, $(_avail_h) avail"

# Entries we refuse to consider, matched against the BASENAME. Anchored so `tmux-1000` matches
# but a hypothetical `my-tmux-scratch` does not.
_is_protected() {
    case "$1" in
        # `.*-unix` already covers .X11-unix / .ICE-unix / .font-unix — listing them separately
        # is a shellcheck SC2222 dead branch, not extra safety. `ao-fleet-tmux` added 2026-08-13:
        # the fleet's tmux socket dir since the TMUX_TMPDIR isolation fix, doesn't match `tmux-*`.
        tmux-* | ao-fleet-tmux | systemd-private-* | snap-private-* | snap.* | .*-unix) return 0 ;;
        *) return 1 ;;
    esac
}

# An entry is reclaimable only when nothing holds it (or anything beneath it) open. `lsof +D`
# descends the tree, which is what we want for a scratch DIRECTORY — a stale-looking dir whose
# single file is still being written must survive. lsof exits non-zero when there are no matches,
# which is precisely the "safe to remove" case, so the negation is the whole test.
_has_open_handle() { lsof +D "$1" >/dev/null 2>&1 || lsof "$1" >/dev/null 2>&1; }

removed=0
skipped_open=0
skipped_protected=0

# -mindepth/-maxdepth 1: only top-level entries. Never recurse into a dir to delete PART of it —
# an entry is reclaimed whole or left entirely alone.
while IFS= read -r -d '' entry; do
    base="$(basename "$entry")"
    if _is_protected "$base"; then
        skipped_protected=$((skipped_protected + 1))
        continue
    fi
    if _has_open_handle "$entry"; then
        skipped_open=$((skipped_open + 1))
        continue
    fi
    if rm -rf -- "$entry" 2>/dev/null; then
        removed=$((removed + 1))
        # Per-path logging (2026-08-13): counts alone left a real incident forensically unrecoverable —
        # no way to confirm after the fact whether a specific path was actually in a given run's reclaim
        # set. journalctl retains this at the default vacuum policy far longer than the entry itself lived.
        echo "${LOG_PREFIX} reclaimed: ${entry}"
    fi
done < <(find /tmp -mindepth 1 -maxdepth 1 -mmin "+${AGE_MIN}" -print0 2>/dev/null)

echo "${LOG_PREFIX} reclaimed=${removed} skipped_open=${skipped_open} skipped_protected=${skipped_protected} (age floor ${AGE_MIN}min)"
echo "${LOG_PREFIX} after: $(_usage_pct)% used, $(_avail_h) avail"

pct="$(_usage_pct)"
if [ -n "${pct}" ] && [ "${pct}" -ge "${WARN_PCT}" ]; then
    # Not a failure exit: a still-full /tmp is a fill-RATE problem upstream (a banned subprocess
    # `gsutil` streaming a multi-GiB parquet through /tmp, a test suite leaking fixtures), and
    # failing the unit would only mask the next successful pass. Make it visible instead.
    echo "${LOG_PREFIX} ::warning:: /tmp still at ${pct}% after cleanup — the fill RATE is the bug, not the sweep interval."
fi
