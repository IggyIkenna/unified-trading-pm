#!/usr/bin/env bash
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
# link-claude-skills.sh — ensure the per-(slot)-root Claude Code agent symlinks:
#   1. top-level `<root>/CLAUDE.md`        → unified-trading-pm/cursor-configs/CLAUDE.md
#   2. `<root>/.claude/skills`             → unified-trading-pm/cursor-configs/skills/   (ONE dir link)
#   3. `<root>/.claude/settings.json`      → unified-trading-pm/cursor-configs/settings.json
#   4. `<root>/.claude/hooks`              → unified-trading-pm/cursor-configs/hooks/   (ONE dir link)
#   5. `<root>/.claude/settings.local.json`  — strips duplicate UserPromptSubmit/PreCompact
#      hooks already covered by (3)'s settings.json (stale duplicates cause double-firing)
# so Claude Code (a) auto-loads the PM ruleset at startup when an agent's CWD is the root, and
# (b) surfaces each `/<name>` slash-command, and (c) picks up team policy (permissions,
# bypassPermissions default, MCP servers, the destructive-command hook) at the project-settings
# layer. Orchestrator-spawned agents launch with CWD = the slot root (.tabs/<N>/) and an isolated
# CLAUDE_CONFIG_DIR, so the TOP-LEVEL CLAUDE.md is the only reliable startup-load point —
# `<root>/.claude/CLAUDE.md` is NOT a path Claude Code reads as memory.
#
# WHY #3 EXISTS (added 2026-07-23, see
# /plans/archive/issues/claude_code_settings_symlink_chain_broken_2026_07_23.md): unlike CLAUDE.md and
# skills/, cursor-configs/settings.json WAS gitignored when this was written (personal model/effort drift jammed
# slot-cron-ff-pull's dirty-check — see .gitignore) — so it never arrives via `git pull` and must be
# manually re-seeded per clone. NO LONGER TRUE: it was RE-TRACKED 2026-07-23, so it DOES arrive via
# `git pull` — which is what lets a team-policy hook registered there reach every slot and machine. This script does NOT invent or copy that content across clones (there
# is no single git-tracked source of truth to copy from); it only links `.claude/settings.json` to
# `cursor-configs/settings.json` WHEN that file already exists in THIS root's own PM clone, and skips
# cleanly (non-blocking) otherwise. Before this fix, NO root on the human-planning VM had this
# symlink at all — settings.json was measured absent in the workspace root and both `.tabs/1`,
# `.tabs/2` slots, meaning team policy (incl. the destructive-command PreToolUse hook) silently never
# loaded anywhere. See codex/05-infrastructure/claude-code-settings-symlink.md for the full model.
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

# ── (0) Self-heal: personal keys (model/effortLevel/theme) don't belong in the team file ──
# Runs BEFORE anything else touches settings.json — see migrate-personal-settings-keys.sh header
# for the full story (/plans/archive/issues/claude_code_settings_symlink_chain_broken_2026_07_23.md).
# Best-effort: that script never fails loudly, so no guard needed here.
_migrate_script="${_self}/migrate-personal-settings-keys.sh"
[ -x "$_migrate_script" ] && bash "$_migrate_script" "${PM_CFG}/settings.json"

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

# ── (3) `<root>/.claude/settings.json` → PM SSOT (team policy), IFF this clone already has it ──
# cursor-configs/settings.json is gitignored (see header note above) — never invented/copied here,
# only linked when this root's own PM clone already has the file on disk. Placed here (before the
# skills block below, NOT after it) because the skills block below has multiple early `exit 0` paths
# (already-linked, no source dir) that would otherwise skip this entirely — measured: an earlier
# version of this patch placed the settings.json block at the end of the file and it silently never
# ran on any of the 3 roots on this host, because skills was already linked on all 3.
_settings_src="${PM_CFG}/settings.json"
_settings_dest="${WORKSPACE_ROOT}/.claude/settings.json"
_settings_target="../unified-trading-pm/cursor-configs/settings.json"

if [ ! -f "$_settings_src" ]; then
    echo "[link-claude-skills] no ${_settings_src} (gitignored + per-clone — re-seed manually, see codex/05-infrastructure/claude-code-settings-symlink.md) — settings.json link skipped for this root"
elif [ -L "$_settings_dest" ]; then
    if [ "$(readlink "$_settings_dest")" = "$_settings_target" ]; then
        echo "[link-claude-skills] ${_settings_dest} → ${_settings_target} (already linked)"
    elif rm -f "$_settings_dest" 2>/dev/null && ln -sfn "$_settings_target" "$_settings_dest" 2>/dev/null; then
        echo "[link-claude-skills] updated ${_settings_dest} → ${_settings_target}"
    else
        echo "[link-claude-skills] could not update ${_settings_dest} (non-blocking)" >&2
    fi
elif [ -e "$_settings_dest" ]; then
    # A real file here is a deliberate personal override — never clobber it.
    echo "[link-claude-skills] ${_settings_dest} exists as a regular file → leaving it untouched (personal override)" >&2
else
    mkdir -p "${WORKSPACE_ROOT}/.claude" 2>/dev/null
    if ln -sfn "$_settings_target" "$_settings_dest" 2>/dev/null; then
        echo "[link-claude-skills] ensured ${_settings_dest} → ${_settings_target}"
    else
        echo "[link-claude-skills] could not link ${_settings_dest} (non-blocking)" >&2
    fi
fi

# ── (4.5) Heal settings.local.json — strip hooks that must not run locally ──
# UserPromptSubmit: the SSOT settings.json (linked above) already registers it. A stale
# settings.local.json that ALSO registers it causes the hook to fire TWICE on every prompt —
# once from the canonical script, once from a potentially-stale local copy.
# PreCompact: the SSOT deliberately registers NOTHING here as of 2026-08-06 (operator ruling —
# client-side auto-compact is the last-resort safety net against a context-saturated session
# and must stay ENABLED; see /plans/active/issues/ao_worker_context_saturation_unrecoverable_
# 2026_08_06.md). Any PreCompact hook surviving in a local file is a stale copy of the retired
# `precompact-block-auto.sh` auto-compact kill, so stripping it here is what actually re-enables
# auto-compact on a machine that still carries the old registration.
_local_settings="${WORKSPACE_ROOT}/.claude/settings.local.json"
# GUARD (2026-08-11): refuse to rewrite through a symlink. `echo > "$_local_settings"` follows a
# symlink, so where settings.local.json points AT the team SSOT, this block's jq
# `del(.hooks.UserPromptSubmit)` strips that hook FROM THE GIT-TRACKED TEAM FILE and jq's
# pretty-printer reformats the rest — leaving the clone permanently dirty with a diff no agent
# recognises as its own, so nobody ever commits or reverts it. Measured on this host: `.tabs/3` and
# `.tabs/6` had both symptoms and had been running without context-threshold-nudge.sh; `.tabs/1`
# carried the same symlink un-fired. This matters more under bypassPermissions, where
# `permissions.deny` is discarded and hooks are the ONLY surviving guardrail
# (see agent-orchestrator/scripts/hooks/block_destructive_commands.py header).
# settings.local.json must be a REAL per-clone file — it is personal, gitignored state.
if [ -L "$_local_settings" ]; then
    echo "[link-claude-skills] ${_local_settings} is a SYMLINK → $(readlink "$_local_settings") — refusing to rewrite through it (would corrupt the team SSOT). Remove it: settings.local.json must be a real per-clone file." >&2
elif [ -f "$_local_settings" ] && command -v jq >/dev/null 2>&1; then
    _cleaned="$(jq '
      if .hooks then
        .hooks |= (
          del(.["UserPromptSubmit"])
          | del(.["PreCompact"])
          | if (. | length) == 0 then empty else . end
        )
      else . end
    ' "$_local_settings" 2>/dev/null)" || true
    if [ -n "$_cleaned" ] && ! echo "$_cleaned" | jq --slurpfile orig "$_local_settings" '. == $orig[0]' 2>/dev/null | grep -q true; then
        echo "$_cleaned" > "$_local_settings" && echo "[link-claude-skills] stripped hooks from ${_local_settings} (UserPromptSubmit is in SSOT settings.json; PreCompact must stay unregistered so client-side auto-compact runs)"
    fi
fi

# ── (4) `<root>/.claude/hooks` → PM SSOT (ONE dir link, mirrors the skills pattern) ──
# Promotes local-only Claude Code hook scripts (e.g. context-threshold-nudge.sh)
# to a git-tracked, symlinked home so an edit propagates to every
# root instead of living only on whichever machine authored it. Added 2026-07-23 — see
# /plans/archive/issues/claude_code_settings_symlink_chain_broken_2026_07_23.md. Placed before
# the skills block (same reason as the settings.json block above): the skills block has early
# `exit 0` paths that would otherwise skip this.
HOOKS_SRC="${PM_CFG}/hooks"
_hooks_dest="${WORKSPACE_ROOT}/.claude/hooks"
_hooks_target="../unified-trading-pm/cursor-configs/hooks"

if [ ! -d "$HOOKS_SRC" ]; then
    echo "[link-claude-skills] no ${HOOKS_SRC} — hooks dir-link step skipped"
elif [ -L "$_hooks_dest" ]; then
    if [ "$(readlink "$_hooks_dest")" = "$_hooks_target" ]; then
        echo "[link-claude-skills] ${_hooks_dest} → ${_hooks_target} (already linked)"
    elif rm -f "$_hooks_dest" 2>/dev/null && ln -sfn "$_hooks_target" "$_hooks_dest" 2>/dev/null; then
        echo "[link-claude-skills] updated ${_hooks_dest} → ${_hooks_target}"
    else
        echo "[link-claude-skills] could not update ${_hooks_dest} (non-blocking)" >&2
    fi
elif [ -d "$_hooks_dest" ]; then
    # Real dir → migrate to a symlink ONLY if every entry is content-identical to the SSOT
    # copy (i.e. it's a prior local-only copy of exactly this content). Any mismatch or
    # foreign file → refuse, leave the whole dir alone (never guess, never delete someone's
    # local hook).
    _foreign=0
    for _e in "$_hooks_dest"/* "$_hooks_dest"/.[!.]*; do
        [ -e "$_e" ] || continue
        _name="$(basename "$_e")"
        if [ ! -f "$_e" ] || ! cmp -s "$_e" "${HOOKS_SRC}/${_name}" 2>/dev/null; then
            _foreign=1
            echo "[link-claude-skills] FOREIGN or content-mismatched (left in place): ${_e}" >&2
        fi
    done
    if [ "$_foreign" -eq 1 ]; then
        echo "[link-claude-skills] ${_hooks_dest} holds local content that doesn't match ${HOOKS_SRC} → REFUSING to convert it to a dir symlink." >&2
    else
        rm -f "$_hooks_dest"/* "$_hooks_dest"/.[!.]* 2>/dev/null
        if rmdir "$_hooks_dest" 2>/dev/null && ln -sfn "$_hooks_target" "$_hooks_dest" 2>/dev/null; then
            echo "[link-claude-skills] migrated local ${_hooks_dest} → symlink → ${_hooks_target}"
        else
            echo "[link-claude-skills] could not migrate ${_hooks_dest} (non-blocking, dir left as-is)" >&2
        fi
    fi
else
    mkdir -p "${WORKSPACE_ROOT}/.claude" 2>/dev/null
    if ln -sfn "$_hooks_target" "$_hooks_dest" 2>/dev/null; then
        echo "[link-claude-skills] ensured ${_hooks_dest} → ${_hooks_target}"
    else
        echo "[link-claude-skills] could not link ${_hooks_dest} (non-blocking)" >&2
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
