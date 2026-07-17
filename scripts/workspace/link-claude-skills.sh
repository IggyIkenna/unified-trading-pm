#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# link-claude-skills.sh — ensure the per-(slot)-root Claude Code agent symlinks:
#   1. top-level `<root>/CLAUDE.md`        → unified-trading-pm/cursor-configs/CLAUDE.md
#   2. `<root>/.claude/skills`             → unified-trading-pm/cursor-configs/skills/   (ONE dir link)
# so Claude Code (a) auto-loads the PM ruleset at startup when an agent's CWD is the root, and
# (b) surfaces each `/<name>` slash-command. Orchestrator-spawned agents launch with CWD = the
# slot root (.tabs/<N>/) and an isolated CLAUDE_CONFIG_DIR, so the TOP-LEVEL CLAUDE.md is the only
# reliable startup-load point — `<root>/.claude/CLAUDE.md` is NOT a path Claude Code reads as memory.
#
# The CLAUDE.md / SKILL.md sources are the git-tracked SSOT (inside the PM repo). These symlinks are
# LOCAL, uncommitted, and regenerated on demand. Regenerating them on every QG run means a freshly-
# cloned slot loads the rules + surfaces every skill with no manual step.
#
# WHY ONE DIRECTORY SYMLINK, NOT PER-SKILL LINKS (changed 2026-07-17, operator):
#   The old layout made `.claude/skills/` a REAL dir holding one symlink per skill, so every NEW
#   skill needed a re-run of this script on every root or it silently never surfaced. That drift was
#   real and measured, not theoretical: at cut-over `pre-compact` existed in cursor-configs but was
#   linked in NO root, and slot 3 carried only 2 of 7 skills. A single dir link makes "add a skill"
#   a pure `git pull` — the new dir appears in every root with zero re-linking.
#   Verified on Claude Code 2.1.201: skill discovery DOES follow a symlinked `.claude/skills` dir
#   (the docs bless a symlinked `<skill-name>` child but are silent on the parent — hence the probe).
#   If a future Claude Code ever stops following the dir link, skills vanish silently → re-test with
#   a throwaway `<root>/.claude/skills -> <dir with a probe SKILL.md>` and `claude -p "list skills"`.
#
# Design properties (intentional — do not "tidy" these away):
#   • RELATIVE symlink target only (`../unified-trading-pm/...`, resolved from `<root>/.claude/`) →
#     user/root/abs-path independent + relocatable, and IDENTICAL on every host. No `/Users/<name>`,
#     no `/active/...`, no `$HOME` ever baked into the link.
#   • Idempotent (`ln -sfn`); safe to run repeatedly.
#   • Self-healing migration: an old per-skill dir is converted in place on the next run of ANY
#     caller (quality-gates.sh, workspace-bootstrap.sh, setup-tab-worktrees.sh, …), so hosts need no
#     manual step. The migration is NON-DESTRUCTIVE — it removes ONLY symlinks that resolve into
#     cursor-configs/skills, and REFUSES (leaving the dir untouched) if the root holds any local
#     content, so a host-authored skill is never deleted.
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
# RELATIVE target, resolved from the link's OWN dir (<ws>/.claude/) → up ONE to <ws>, then into the
# PM repo. (Per-skill links lived one level deeper and needed `../../` — an easy off-by-one here.)
_target="../unified-trading-pm/cursor-configs/skills"

# Portable realpath-of-a-dir: `cd` follows symlinks, `pwd -P` prints the physical path. Avoids
# `readlink -f`, which BSD/macOS readlink lacks. Empty output = does not resolve.
_real_dir() { (cd "$1" 2>/dev/null && pwd -P); }
_SRC_REAL="$(_real_dir "$SKILLS_SRC")"

# ── Heal SSOT pollution from a PRE-2026-07-17 copy of this script ──
# MEASURED, not hypothetical: the old per-skill version run against the NEW dir-link layout does
# `ln -sfn <target> <root>/.claude/skills/<name>`, which resolves THROUGH the dir link onto the real
# `cursor-configs/skills/<name>/` dir. `ln -sfn` does NOT refuse an existing real dir (`-n` only
# guards symlinks-to-dirs) — it links INSIDE it, creating `cursor-configs/skills/<name>/<name>`:
# junk in a GIT-TRACKED dir. That only happens on a stale/rolled-back clone (a slot migrates itself
# only once it has THIS version), but the blast radius is the SSOT repo, so heal it on every run.
# Narrow by construction: only a symlink named after its own parent skill dir, AND either carrying
# the old script's VERBATIM link string or resolving back to its own parent. Note the artefact is
# normally a BROKEN link — `../../` from `skills/<name>/<name>` lands in `cursor-configs/`, not the
# root — so a "does it resolve to its parent?" test alone silently misses it (measured).
for _sd in "$SKILLS_SRC"/*/; do
    [ -d "$_sd" ] || continue
    _sd="${_sd%/}"
    _name="$(basename "$_sd")"
    _junk="${_sd}/${_name}"
    [ -L "$_junk" ] || continue
    _jt="$(readlink "$_junk")"
    _jr="$(_real_dir "$_junk")"
    if [ "$_jt" = "../../unified-trading-pm/cursor-configs/skills/${_name}" ] \
        || { [ -n "$_jr" ] && [ "$_jr" = "$(_real_dir "$_sd")" ]; }; then
        rm -f "$_junk" 2>/dev/null && echo "[link-claude-skills] pruned junk link ${_junk} (pre-2026-07-17-script artefact)"
    fi
done

if [ -L "$_dest" ]; then
    # Already a symlink. Canonical + resolving → done. Anything else (abs path from an older
    # script, stale/broken target) → replace it.
    if [ "$(readlink "$_dest")" = "$_target" ] && [ -n "$(_real_dir "$_dest")" ]; then
        echo "[link-claude-skills] ${_dest} → ${_target} (already linked)"
        exit 0
    fi
    rm -f "$_dest" 2>/dev/null || {
        echo "[link-claude-skills] cannot replace existing link ${_dest} (non-blocking)" >&2
        exit 0
    }
elif [ -d "$_dest" ]; then
    # ── Legacy per-skill layout → migrate to the single dir link ──
    # Delete ONLY symlinks resolving into cursor-configs/skills (regenerable) or broken ones (they
    # surface nothing). A real dir/file, or a symlink to anything else (e.g. a host-authored or
    # personal skill), is FOREIGN → refuse and leave the whole dir alone. Silently deleting someone's
    # skill is far worse than leaving a stale layout that a human can look at.
    _foreign=0
    for _e in "$_dest"/* "$_dest"/.[!.]*; do
        [ -e "$_e" ] || [ -L "$_e" ] || continue          # unmatched glob
        if [ ! -L "$_e" ]; then
            _foreign=1
            echo "[link-claude-skills] FOREIGN (not a symlink): ${_e}" >&2
            continue
        fi
        _e_real="$(_real_dir "$_e")"
        case "${_e_real}" in
            "${_SRC_REAL}"/*) : ;;                        # ours → regenerable
            "") : ;;                                      # broken link → surfaces nothing
            *)
                _foreign=1
                echo "[link-claude-skills] FOREIGN (links outside cursor-configs/skills): ${_e} → ${_e_real}" >&2
                ;;
        esac
    done
    if [ "$_foreign" -eq 1 ]; then
        echo "[link-claude-skills] ${_dest} holds local content → REFUSING to convert it to a dir symlink." >&2
        echo "[link-claude-skills] Move that content into ${SKILLS_SRC} (the git-tracked SSOT), then re-run me." >&2
        exit 0
    fi
    find "$_dest" -mindepth 1 -maxdepth 1 -type l -exec rm -f {} + 2>/dev/null
    # rmdir (NOT rm -rf) is the safety net: it succeeds only on an empty dir, so anything we failed
    # to classify above still stops the migration rather than getting blown away.
    if ! rmdir "$_dest" 2>/dev/null; then
        echo "[link-claude-skills] ${_dest} not empty after pruning our links → leaving it as-is (non-blocking)" >&2
        exit 0
    fi
    echo "[link-claude-skills] migrated legacy per-skill layout at ${_dest}"
elif [ -e "$_dest" ]; then
    echo "[link-claude-skills] ${_dest} exists and is not a dir/symlink → leaving it (non-blocking)" >&2
    exit 0
fi

if ! mkdir -p "${WORKSPACE_ROOT}/.claude" 2>/dev/null; then
    echo "[link-claude-skills] cannot create ${WORKSPACE_ROOT}/.claude (non-blocking)" >&2
    exit 0
fi

if ln -sfn "$_target" "$_dest" 2>/dev/null && [ -n "$(_real_dir "$_dest")" ]; then
    # Trailing slash → find follows the dir symlink and counts the skills now surfaced.
    _n="$(find "$_dest"/ -mindepth 1 -maxdepth 1 -type d -print 2>/dev/null | wc -l | tr -d ' ')"
    echo "[link-claude-skills] ensured ${_dest} → ${_target} (${_n} skill(s) surfaced, no per-skill linking needed)"
else
    echo "[link-claude-skills] could not link ${_dest} → ${_target} (non-blocking)" >&2
fi
exit 0
