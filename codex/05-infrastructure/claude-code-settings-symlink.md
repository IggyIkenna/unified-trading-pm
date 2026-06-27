---
doc_type: codex-runbook
title: Claude Code settings — team-shared vs personal split
summary: How Claude Code settings are layered across slots — a TEAM-shared tracked file (permissions/bypass/plugins/mcp) inherited via per-slot symlink, plus a PERSONAL real ~/.claude/settings.json (model/theme/effort) that never pollutes git.
owner: infra
cadence: once per machine / per new slot
verifier: "readlink .tabs/<N>/.claude/settings.json resolves to cursor-configs/settings.json; ~/.claude/settings.json is a REAL file (not a symlink) carrying your model"
last_executed: 2026-06-27
status: active
nature: guideline
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [claude-code, settings, symlink, onboarding, permissions]
related: [per-tab-worktrees.md]
created: 2026-06-27
---

# Claude Code settings — team-shared vs personal

Claude Code merges settings from (lowest → highest precedence): `~/.claude/settings.json` (user) → a project's
`.claude/settings.json` (shared) → a project's `.claude/settings.local.json` (local). We use that layering to keep
**team policy shared in git** while **personal preferences stay out of git**.

## The two layers

1. **TEAM (tracked, shared)** — `unified-trading-pm/cursor-configs/settings.json`. Holds ONLY team policy:
   `permissions.defaultMode: bypassPermissions` + the destructive-command `ask` denylist, `enabledPlugins`,
   `mcpServers` (playwright), and the bypass-smoothing flags. **It contains NO `model`/`theme`/`effortLevel`/
   `workspaces`** — those are personal and must never be committed (a committed `model: opus` would silently force
   Opus on the whole fleet, violating the Sonnet-default rule in
   `codex/06-coding-standards/model-tier-selection.md`). Each slot inherits this file via a project-level symlink.

2. **PERSONAL (real file, NOT a symlink, never in git)** — your own `~/.claude/settings.json`. Holds your
   `model` / `theme` / `effortLevel` / trusted `workspaces`. Because it is user-scope (lowest precedence) it provides
   your defaults everywhere, and the team project file (which sets no `model`) never overrides them.

This split is why a per-slot symlink is now safe: the tracked file has no personal model to clobber your choice.

## Setup (new machine / new slot)

**Per-slot team inheritance (run for every slot — idempotent):**

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

## Notes

- The per-slot symlink lives in `.tabs/<N>/.claude/` which is **not** inside any git repo, so it is never committed.
- **Still getting allow-prompts?** That's the session's permission MODE, not the settings. `bypassPermissions` is the
  default; a session launched in "default/ask" mode overrides it (and persists each grant into
  `.claude/settings.local.json`). Toggle the mode (Shift+Tab in the IDE extension) or relaunch.
- A slot is skipped by the setup loop when it hasn't pulled the commit that adds `cursor-configs/settings.json` —
  re-run after `git pull --ff-only`.
