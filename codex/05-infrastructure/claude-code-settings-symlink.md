# Claude Code settings — symlink to the shared canonical

**Owner:** infra · **Cadence:** once per machine / per new slot · **Verifier:** `readlink ~/.claude/settings.json` and `readlink .tabs/<N>/.claude/settings.json` both resolve to a `cursor-configs/settings.json` · **last_executed:** 2026-06-27

## Why

Claude Code reads its settings from `~/.claude/settings.json` (user scope) and `<project>/.claude/settings.json`
(project scope). The team's shared config — `permissions.defaultMode: bypassPermissions` + a denylist (`ask`) of only
the destructive commands, the enabled plugins, and the MCP servers (playwright) — lives in the tracked file
`unified-trading-pm/cursor-configs/settings.json`. Symlinking the Claude-read paths at that canonical file means every
slot inherits the shared config and you don't re-approve commands per slot. **The canonical file only exists inside slot
clones** (there is no non-slot checkout copy), so the symlink target is `…/unified-trading-pm/cursor-configs/settings.json`.

## Procedure

**User scope (covers every slot at once — do this once per machine):**

```bash
ln -sfn "$PWD/unified-trading-pm/cursor-configs/settings.json" ~/.claude/settings.json   # run from a slot dir
readlink ~/.claude/settings.json                                                          # verify
```

**Per-slot project scope (self-contained; safe to run for every slot — idempotent):**

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

A slot is skipped when it hasn't pulled the commit that adds `cursor-configs/settings.json` — re-run after
`git pull --ff-only` and it will be picked up.

## Caveats (read before committing anything)

- **`model` / `effortLevel` / `theme` / `workspaces` are PERSONAL, not team config — but they currently live in this
  TRACKED file.** Picking a model (`/model`) writes back into whatever `settings.json` Claude is using; via the symlink
  that edits the tracked `cursor-configs/settings.json`, showing as a diff (committed default is `model: sonnet`). **Do
  not commit that drift** — committing `model: opus[1m]` would force Opus on the whole fleet (violates the
  Sonnet-default rule in `codex/06-coding-standards/model-tier-selection.md`). Durable fix (TODO): strip the personal
  keys out of the tracked file so it carries only team-shared keys, and keep personal prefs in a real
  `~/.claude/settings.json` (not a symlink). Until then, `git restore cursor-configs/settings.json` before any PM commit.
- **Still getting allow-prompts after symlinking?** That's the session's permission MODE, not the symlink.
  `bypassPermissions` in the settings file is the *default*; a session launched in "default/ask" mode overrides it
  (and persists each grant into `.claude/settings.local.json`). Toggle the mode (Shift+Tab in the IDE extension) or
  relaunch.
- The per-slot symlink lives in `.tabs/<N>/.claude/` which is **not** inside any git repo, so the symlink itself is
  never committed.
```
