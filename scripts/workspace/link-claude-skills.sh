#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# link-claude-skills.sh — ensure the per-(slot)-root Claude Code agent symlinks:
#   1. top-level `<root>/CLAUDE.md`        → unified-trading-pm/cursor-configs/CLAUDE.md
#   2. `<root>/.claude/skills/<name>`      → unified-trading-pm/cursor-configs/skills/<name>/
# so Claude Code (a) auto-loads the PM ruleset at startup when an agent's CWD is the root, and
# (b) surfaces each `/<name>` slash-command. Orchestrator-spawned agents launch with CWD = the
# slot root (.tabs/<N>/) and an isolated CLAUDE_CONFIG_DIR, so the TOP-LEVEL CLAUDE.md is the only
# reliable startup-load point — `<root>/.claude/CLAUDE.md` is NOT a path Claude Code reads as memory.
#
# The CLAUDE.md / SKILL.md sources are the git-tracked SSOT (inside the PM repo). These symlinks are
# LOCAL, uncommitted, and regenerated on demand. Regenerating them on every QG run means a freshly-
# cloned slot loads the rules + surfaces every skill with no manual step.
#
# Design properties (intentional — do not "tidy" these away):
#   • RELATIVE symlink targets only (`../../unified-trading-pm/...`) → user/root/abs-path
#     independent + relocatable. No `/Users/<name>` or `$HOME` ever baked into the link.
#   • Idempotent (`ln -sfn`); safe to run repeatedly.
#   • Best-effort: ALWAYS exits 0. Safe to call from quality-gates.sh without a guard — it can
#     never fail the gate.
#   • No-op in CI: GHA runners have no slot tree and nothing reads `.claude/skills` there, so we
#     skip before touching the filesystem (avoids stray dirs in a runner checkout).
#
# Usage: link-claude-skills.sh [WORKSPACE_ROOT]
#   WORKSPACE_ROOT defaults to the parent of the PM repo this script lives in.
set -u

# ── CI skip (harmless to skip; avoids disrupting GHA QG runners that lack the slot layout) ──
if [ -n "${CI:-}" ] || [ -n "${GITHUB_ACTIONS:-}" ]; then
    echo "[link-claude-skills] CI detected → skipping (.claude/skills is a local-dev convenience)"
    exit 0
fi

_self="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Default WORKSPACE_ROOT = parent of the PM repo (…/unified-trading-pm/scripts/workspace → up 3).
WORKSPACE_ROOT="${1:-$(cd "${_self}/../../.." && pwd)}"
PM_CFG="${WORKSPACE_ROOT}/unified-trading-pm/cursor-configs"
SKILLS_SRC="${PM_CFG}/skills"

# ── (1) Top-level CLAUDE.md → PM SSOT (RELATIVE target; the startup-load point for agents) ──
# Done first + independently of skills so a root with no skills dir still gets its rules.
#
# WORKSPACE_ROOT here is EITHER a slot (.tabs/N — when QG runs from a slot's PM clone) or the true
# workspace root (the dir that CONTAINS .tabs/). The SLOT-level CLAUDE.md is the legit one every
# session loads → always create it. A copy at the TRUE workspace root, though, double-loads the whole
# ruleset into every nested slot session, because Claude Code scans cwd + all parent dirs (and reads
# .claude/CLAUDE.md as memory too) — wasted + stale. So skip it at the true root EXCEPT on the
# human-planning VM, where humans open sessions at the bare root. Why: operator 2026-06-25.
# Opt in once per machine: git config --global slotIdentity.rootWorkspaceClaudeMd true
_is_true_workspace_root() { [ -d "${WORKSPACE_ROOT}/.tabs" ]; }
_keep_root_workspace_claude_md() {
    case "${ORCHESTRATOR_VM_ID:-}${VM_NAME:-}" in *human-planning*) return 0 ;; esac
    [ "$(git config --global slotIdentity.rootWorkspaceClaudeMd 2>/dev/null)" = "true" ] && return 0
    [ -n "${WORKSPACE_ROOT_CLAUDE_MD:-}" ] && return 0
    return 1
}
if [ -f "${PM_CFG}/CLAUDE.md" ]; then
    if _is_true_workspace_root && ! _keep_root_workspace_claude_md; then
        echo "[link-claude-skills] skip ROOT CLAUDE.md at ${WORKSPACE_ROOT} (non human-planning host — avoids slot double-load)"
    elif ln -sfn "unified-trading-pm/cursor-configs/CLAUDE.md" "${WORKSPACE_ROOT}/CLAUDE.md" 2>/dev/null; then
        echo "[link-claude-skills] ensured ${WORKSPACE_ROOT}/CLAUDE.md → PM/cursor-configs/CLAUDE.md"
    else
        echo "[link-claude-skills] could not link ${WORKSPACE_ROOT}/CLAUDE.md (non-blocking)" >&2
    fi
fi

if [ ! -d "$SKILLS_SRC" ]; then
    echo "[link-claude-skills] no ${SKILLS_SRC} — skills step skipped"
    exit 0
fi

_dest="${WORKSPACE_ROOT}/.claude/skills"
if ! mkdir -p "$_dest" 2>/dev/null; then
    echo "[link-claude-skills] cannot create ${_dest} (non-blocking)" >&2
    exit 0
fi

_n=0
for _sd in "$SKILLS_SRC"/*/; do
    [ -d "$_sd" ] || continue
    _name="$(basename "$_sd")"
    # RELATIVE target: from <ws>/.claude/skills/ go up two to <ws>, then into the PM repo.
    if ln -sfn "../../unified-trading-pm/cursor-configs/skills/${_name}" "${_dest}/${_name}" 2>/dev/null; then
        _n=$((_n + 1))
    else
        echo "[link-claude-skills] skipped ${_name} (non-blocking)" >&2
    fi
done

echo "[link-claude-skills] ensured ${_n} skill symlink(s) under ${_dest}"
exit 0
