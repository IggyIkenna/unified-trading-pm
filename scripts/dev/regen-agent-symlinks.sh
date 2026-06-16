#!/usr/bin/env bash
# regen-agent-symlinks.sh — (re)assert the per-root Claude Code agent symlinks for THIS host:
#   • top-level   <root>/CLAUDE.md          → unified-trading-pm/cursor-configs/CLAUDE.md
#   • per-root    <root>/.claude/skills/*   → unified-trading-pm/cursor-configs/skills/*
# for the MAIN workspace root AND every slot root (.tabs/<N>/). Thin fan-out over the canonical
# link-claude-skills.sh helper (which does the actual idempotent, relative, CI-skipping symlinking).
#
# Why this exists: pm-pull-ff.sh only fast-forwards the PM git tree — it does NOT execute setup.
# Calling this from pm-pull-ff.sh (post-FF advance) + install_pm_pull.sh (one-shot at rollout) makes
# every VM self-heal the root CLAUDE.md + skills symlinks fleet-wide, with no per-VM manual step and
# no waiting for a quality-gates run. Orchestrator-spawned agents launch with CWD = the slot root, so
# the top-level CLAUDE.md is their only reliable startup-load point for the PM ruleset.
#
# Idempotent, best-effort, ALWAYS exits 0 — safe to call from a root-owned systemd unit. Run it as the
# `ubuntu` user (e.g. `sudo -u ubuntu bash regen-agent-symlinks.sh`) so the symlinks are ubuntu-owned.
set -u

_self="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# _self = <ws>/unified-trading-pm/scripts/dev  →  PM repo is up 2, workspace root is up 3.
PM_DIR="$(cd "${_self}/../.." && pwd)"
WS_ROOT="$(cd "${PM_DIR}/.." && pwd)"
LINKER="${PM_DIR}/scripts/workspace/link-claude-skills.sh"

if [ ! -f "$LINKER" ]; then
    echo "[regen-agent-symlinks] missing ${LINKER} — nothing to do"
    exit 0
fi

# Roots to refresh: the main workspace root + each bootstrapped slot root (.tabs/<N>/ that has its
# OWN PM checkout — the relative symlink targets resolve only when that PM tree is present).
_roots=("$WS_ROOT")
if [ -d "${WS_ROOT}/.tabs" ]; then
    for _d in "${WS_ROOT}/.tabs"/*/; do
        [ -d "${_d}unified-trading-pm/cursor-configs" ] || continue
        _roots+=("${_d%/}")
    done
fi

_count=0
for _r in "${_roots[@]}"; do
    bash "$LINKER" "$_r" 2>&1 | sed 's/^/  /' || true
    _count=$((_count + 1))
done

echo "[regen-agent-symlinks] refreshed ${_count} root(s)"
exit 0
