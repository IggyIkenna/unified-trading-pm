---
doc_type: codex-ssot
title: Claude Code settings — team-shared vs personal split
summary:
  How Claude Code settings are layered across slots — a TEAM-shared file (permissions/bypass/plugins/mcp/hooks),
  git-tracked again since 2026-07-23 (was gitignored 2026-07-09 to 2026-07-23 — see .gitignore comment + git history)
  and inherited via a per-slot symlink that scripts/workspace/link-claude-skills.sh now creates automatically, plus a
  PERSONAL real ~/.claude/settings.json (model/theme/effort) that never pollutes git. Hook `command` strings in this
  file use `$CLAUDE_PROJECT_DIR` rather than a hardcoded absolute path, so the same file works unmodified on every
  machine/slot in the fleet.
status: current
nature: guideline
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [claude-code, settings, symlink, onboarding, permissions]
related: [per-tab-worktrees.md, plans/active/issues/claude_code_settings_symlink_chain_broken_2026_07_23.md]
created: 2026-06-27
authoritative_for: [Claude Code team-shared vs personal settings split, per-slot settings.json symlink inheritance]
referenced_by:
owner: infra
last_reviewed: 2026-07-23
code_refs:
  [
    scripts/workspace/link-claude-skills.sh,
    scripts/dev/setup-tab-worktrees.sh,
    agent-orchestrator/scripts/hooks/block_destructive_commands.py,
  ]
cadence:
  automated (link-claude-skills.sh runs from setup-tab-worktrees.sh / quality-gates.sh / workspace-bootstrap.sh);
  cursor-configs/settings.json itself is git-tracked again since 2026-07-23 and arrives via git pull like any other file
  — manual re-seed is only a fallback for the 2026-07-09→2026-07-23 gitignored window
verifier:
  readlink .tabs/<N>/.claude/settings.json resolves to ../unified-trading-pm/cursor-configs/settings.json;
  ~/.claude/settings.json is a REAL file (not a symlink) carrying your model
last_executed: 2026-07-23
---

# Claude Code settings — team-shared vs personal

Claude Code merges settings from (lowest → highest precedence): `~/.claude/settings.json` (user) → a project's
`.claude/settings.json` (shared) → a project's `.claude/settings.local.json` (local). We use that layering to keep
**team policy shared in git** while **personal preferences stay out of git**.

## The two layers

1. **TEAM (tracked, shared)** — `unified-trading-pm/cursor-configs/settings.json`. Holds ONLY team policy:
   `permissions.defaultMode: bypassPermissions` + the destructive-command `ask` denylist, `enabledPlugins`, `mcpServers`
   (playwright), and the bypass-smoothing flags. **It contains NO `model`/`theme`/`effortLevel`/ `workspaces`** — those
   are personal and must never be committed (a committed `model: opus` would silently force Opus on the whole fleet,
   violating the Sonnet-default rule in `codex/06-coding-standards/model-tier-selection.md`). Each slot inherits this
   file via a project-level symlink.

2. **PERSONAL (real file, NOT a symlink, never in git)** — your own `~/.claude/settings.json`. Holds your `model` /
   `theme` / `effortLevel` / trusted `workspaces`. Because it is user-scope (lowest precedence) it provides your
   defaults everywhere, and the team project file (which sets no `model`) never overrides them.

This split is why a per-slot symlink is now safe: the tracked file has no personal model to clobber your choice.

## Setup (new machine / new slot)

**Per-slot team inheritance is now AUTOMATED (2026-07-23)** — `scripts/workspace/link-claude-skills.sh` links
`<root>/.claude/settings.json → ../unified-trading-pm/cursor-configs/settings.json` for any workspace root (the true
workspace root, or a `.tabs/<N>` slot) whose own PM clone already has `cursor-configs/settings.json` on disk. It's
idempotent, non-destructive (never clobbers a real personal-override file, only ever replaces a symlink), and already
wired into `setup-tab-worktrees.sh`'s `seed_slot_claude_assets()` (so `--init` / `--add-slot` / `--reset-slot` all pick
it up for free) plus `quality-gates.sh` and `workspace-bootstrap.sh`. It does NOT invent or copy content across clones —
if a root's own clone doesn't have `cursor-configs/settings.json` yet (e.g. hasn't pulled the commit that re-tracked it,
see update below), the linker skips that root with a clear message and a `git pull --ff-only` resolves it; the manual
re-seed step below is only for the historical gitignored window.

**2026-07-23 update: this file is TRACKED again** (commit `e5be0047c`, root cause fixed) — a plain `git pull --ff-only`
now syncs it to every clone like any other file. The manual re-seed below is a historical fallback for the
2026-07-09→2026-07-23 gitignored window (and for any future untrack event, should the drift that caused it recur).

**Manual re-seed (only needed while this file is gitignored — see update above — or the first time a clone gets it
during that window):**

```bash
# from inside that clone's unified-trading-pm/ dir — copy the team-policy content from a known-good source
# (another clone on the same host, or reconstruct from git history — see git log cursor-configs/settings.json)
cp <known-good-source>/cursor-configs/settings.json cursor-configs/settings.json
# then re-run the linker (or just wait for the next quality-gates.sh / setup-tab-worktrees.sh run):
bash scripts/workspace/link-claude-skills.sh "$WORKSPACE_ROOT"   # WORKSPACE_ROOT = this clone's parent dir
```

**Fallback — the old manual per-slot loop (only needed if the linker script is somehow unavailable):**

```bash
ROOT="$HOME/Code/unified-trading-system-repos/.tabs"   # adjust to your workspace
for d in "$ROOT"/*/; do
  slot=$(basename "$d"); case "$slot" in (*[!0-9]*) continue;; esac
  cc="$d/unified-trading-pm/cursor-configs/settings.json"; link="$d/.claude/settings.json"
  [ -e "$cc" ] || { echo "[skip] slot $slot: no target (stale clone — FF-pull first)"; continue; }
  mkdir -p "$d/.claude"
  if [ -L "$link" ]; then echo "[ok] slot $slot";
  elif [ -e "$link" ]; then echo "[WARN] slot $slot: regular file, left untouched";
  else ln -s ../unified-trading-pm/cursor-configs/settings.json "$link" && echo "[created] slot $slot"; fi
done
```

**Personal settings (once per machine) — a REAL file, not a symlink:**

```bash
# Start from the team file, then add your personal keys (model/theme/effortLevel).
cp "$PWD/unified-trading-pm/cursor-configs/settings.json" ~/.claude/settings.json
# then edit ~/.claude/settings.json to add e.g. "model": "opus[1m]", "theme": "dark", "effortLevel": "xhigh"
```

Do NOT symlink `~/.claude/settings.json` to the tracked file — picking a model (`/model`) would write back into git.
Keep it a real, personal file.

## Hook commands: use `$CLAUDE_PROJECT_DIR`, never a hardcoded absolute path

The 3 hooks in this file's `hooks` key (`PreToolUse` → `block_destructive_commands.py`, `UserPromptSubmit` →
`context-threshold-nudge.sh`, `PreCompact` → `precompact-block-auto.sh`) reference their scripts via
`$CLAUDE_PROJECT_DIR/...`, not an absolute path. Claude Code exports `CLAUDE_PROJECT_DIR` to every hook-command
subprocess, set to the project root the session was launched from — confirmed empirically (2026-07-23) to resolve
correctly and DIFFERENTLY per launch root: a session opened at the true workspace root gets that path, one opened in
`.tabs/1` gets `.../.tabs/1`, one opened in `.tabs/2` gets `.../.tabs/2` — each then naturally resolves to that root's
OWN clone of the hook script, not the main root's. This is what makes ONE tracked `settings.json` (symlinked into every
root) work unmodified fleet-wide, regardless of username or workspace path on a given machine — no per-machine edit
needed. Official reference: [code.claude.com/docs/en/hooks.md](https://code.claude.com/docs/en/hooks.md)
(`${CLAUDE_PROJECT_DIR}` env-var table entry) — this fact was never captured anywhere in this codex before 2026-07-23,
which is why the hardcoded path crept in originally; see
`plans/active/issues/claude_code_settings_symlink_chain_broken_2026_07_23.md` for the full investigation.

**Known gap (unrelated, flagging so it isn't re-discovered the hard way)**:
`claude -p ... --dangerously-skip-permissions` (non-interactive print/headless mode) does NOT enforce `PreToolUse` hook
blocking — confirmed 2026-07-23 for both the old hardcoded-path and new `$CLAUDE_PROJECT_DIR` forms of the
destructive-command guard equally, so it's not a path-portability issue. This is undocumented in Anthropic's official
docs too. It doesn't affect real agent-orchestrator workers (`agent-orchestrator/server/tmux_spawn.py::spawn` launches a
genuine INTERACTIVE `claude` session inside a detached tmux pane and pastes the boot prompt — no `-p`/`--print` flag
anywhere in the real dispatch path), but don't assume hooks gate a `claude -p` invocation if one ever gets scripted
elsewhere. See `agent-orchestrator/scripts/hooks/block_destructive_commands.py`'s docstring for the same note at the
code site.

## Notes

- The per-slot symlink lives in `.tabs/<N>/.claude/` which is **not** inside any git repo, so it is never committed.
- **Still getting allow-prompts?** That's the session's permission MODE, not the settings. `bypassPermissions` is the
  default; a session launched in "default/ask" mode overrides it (and persists each grant into
  `.claude/settings.local.json`). Toggle the mode (Shift+Tab in the IDE extension) or relaunch.
- A slot is skipped by the setup loop when it hasn't pulled the commit that adds `cursor-configs/settings.json` — re-run
  after `git pull --ff-only`.
