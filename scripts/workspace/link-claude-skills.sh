#!/usr/bin/env bash
# link-claude-skills.sh — ensure a `.claude/skills/<name>` discovery symlink for every
# `unified-trading-pm/cursor-configs/skills/<name>/` so Claude Code surfaces each `/<name>`
# slash-command at the workspace (slot) root.
#
# The SKILL.md files are the git-tracked SSOT (inside the PM repo). These symlinks are LOCAL,
# uncommitted, and regenerated on demand — the SAME model as the workspace-root `.claude/CLAUDE.md`
# symlink (also a local, setup-generated artifact, not committed). Regenerating them on every QG
# run means a freshly-cloned slot surfaces every skill with no manual step.
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
SKILLS_SRC="${WORKSPACE_ROOT}/unified-trading-pm/cursor-configs/skills"

if [ ! -d "$SKILLS_SRC" ]; then
    echo "[link-claude-skills] no ${SKILLS_SRC} — nothing to do"
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
