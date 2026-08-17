#!/usr/bin/env bash
# Epic: infrastructure_master (ci_vm_io_starvation_audit_findings_and_optimization_2026_08_05.md
#   Part 4 / Part 8 "Cut sibling-clone I/O": shared bare repos + git worktree +
#   --filter=blob:none for dep repos, required to get peak throughput under the EBS baseline a
#   smaller CI instance imposes)
# Lifecycle: permanent
# Delete-when: the shared bare-repo dep-clone fast path (clone_repo_via_shared_bare() in
#   unified-trading-ci's python-quality-gates-v2.yml) is retired.
#
# prune-shared-bare-repo-worktrees.sh — sweep every shared bare-repo mirror under
# SHARED_BARE_ROOT and prune stale `git worktree` administrative entries left behind when a
# job's `_work` directory is wiped (job-cleanup.sh for the long-lived pool; the JIT-ephemeral
# pool's own ExecStart wrapper) WITHOUT a matching `git worktree remove` — each such job leaves a
# dangling worktree registration under `<bare>/worktrees/<name>/` that only `git worktree prune`
# reclaims, and (worse) that dangling entry makes git REFUSE to fetch into the affected branch at
# all ("refusing to fetch into branch ... checked out at ...") until pruned.
#
# The fast path itself already prunes opportunistically before every fetch it makes, so in
# steady state this timer finds nothing to do. It exists as the backstop for a bare repo that
# stops being actively used (a dep repo drops out of DEP_REPOS, or the host sits idle) — nothing
# would otherwise ever trigger that opportunistic prune again, and the leak would accumulate
# forever (measured precedent: the governor's own marker-file leak, same source doc, 344 stale
# files at ~115/day).
#
# Host-wide, not tied to any single runner pool — mirrors docker-disk-cleanup.sh's own framing.
set -euo pipefail

: "${SHARED_BARE_ROOT:=/opt/glue-shared-bare-repos}"

log() { printf '[prune-shared-bare-repos] %s\n' "$*"; }

if [ ! -d "${SHARED_BARE_ROOT}" ]; then
  log "no ${SHARED_BARE_ROOT} on this host — nothing to prune"
  exit 0
fi

pruned=0
shopt -s nullglob
for bare in "${SHARED_BARE_ROOT}"/*.git; do
  [ -d "${bare}" ] || continue
  before=$(git -C "${bare}" worktree list --porcelain 2>/dev/null | grep -c '^worktree ' || true)
  if ! git -C "${bare}" worktree prune --expire now 2>/dev/null; then
    log "WARN: prune failed for ${bare}"
    continue
  fi
  after=$(git -C "${bare}" worktree list --porcelain 2>/dev/null | grep -c '^worktree ' || true)
  removed=$(( before - after ))
  if [ "${removed}" -gt 0 ]; then
    log "$(basename "${bare}"): pruned ${removed} stale worktree entries"
    pruned=$(( pruned + removed ))
  fi
done
shopt -u nullglob

log "done — ${pruned} stale worktree entries pruned across ${SHARED_BARE_ROOT}"
