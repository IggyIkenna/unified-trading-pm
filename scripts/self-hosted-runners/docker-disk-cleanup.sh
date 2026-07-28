#!/usr/bin/env bash
# Epic: infrastructure_master (orchestrator VM disk-IO contention remediation, 2026-07-28)
# Lifecycle: permanent
# Delete-when: NA
#
# docker-disk-cleanup.sh — host-wide (NOT per-runner-pool) periodic docker reclaim on the
# shared orchestrator VM.
#
# WHY THIS EXISTS: unlike per-runner toolcache (deliberately per-pool, see setup-glue-runners.sh's
# own header comment on the actions/setup-python delete-then-create race) and per-runner _work
# (already cleaned per-job via job-cleanup.sh / the JIT wrapper), docker images/build-cache/
# containers are a SINGLE shared daemon resource across every pool and had NO cleanup automation
# at all as of 2026-07-28 (confirmed live: `docker system df` showed 51GB images / 12.89GB
# immediately reclaimable, `systemctl list-timers` + `crontab -l` showed nothing targeting it —
# only the generic systemd-tmpfiles-clean.timer, which doesn't touch docker's own storage driver).
#
# Deliberately does NOT touch: RUNNING containers or images they reference (docker's own "unused"
# accounting already excludes these — this is why `-a` combined with an age filter is safe here,
# unlike the toolcache-sharing idea this doc's sibling issue explicitly rejected).
#
# Deployed ONCE, host-wide, at /usr/local/sbin (NOT under any POOL_TAG's ${RUNNER_BASE}) — this is
# deliberately not part of setup-glue-runners.sh's per-pool install loop, since running it 25x
# (once per pool) would be redundant against the one shared docker daemon.
set -euo pipefail

LOG_PREFIX="[docker-disk-cleanup]"

echo "${LOG_PREFIX} before:"
docker system df 2>&1 || { echo "${LOG_PREFIX} docker not available, nothing to do"; exit 0; }

# -a: also remove unused (not just dangling) images. Safe specifically because docker's own
# accounting already excludes anything referenced by a running or stopped-but-restartable
# container; `until=24h` is the safety margin so a job that just pulled an image for later reuse
# today doesn't get it evicted mid-shift.
docker image prune -af --filter "until=24h" 2>&1 | sed "s/^/${LOG_PREFIX} /"
docker container prune -f --filter "until=24h" 2>&1 | sed "s/^/${LOG_PREFIX} /"
docker builder prune -af --filter "until=24h" 2>&1 | sed "s/^/${LOG_PREFIX} /"

echo "${LOG_PREFIX} after:"
docker system df 2>&1
