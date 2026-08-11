---
doc_type: issue
title:
  link-claude-skills.sh strips a hook from the TRACKED team settings by writing through a settings.local.json symlink
summary: >-
  `link-claude-skills.sh` block (4.5) heals `.claude/settings.local.json` with `jq 'del(.hooks.UserPromptSubmit) |
  del(.hooks.PreCompact)'` and writes it back via `echo > "$file"`. In three clones (.tabs/1, .tabs/3, .tabs/6) that
  path was a SYMLINK to the git-tracked `unified-trading-pm/cursor-configs/settings.json`, so the redirect followed the
  link and stripped `UserPromptSubmit` from the TEAM SSOT, with jq reformatting the rest. `.tabs/3` and `.tabs/6` had
  both symptoms and had been running without context-threshold-nudge.sh; `.tabs/1` carried the same symlink un-fired.
  Guard applied 2026-08-11 (refuse to rewrite through a symlink) and all three symlinks removed. Matters more than it
  looks: under bypassPermissions `permissions.deny` is discarded, so hooks are the ONLY surviving guardrail — a
  mechanism that silently deletes hook registrations is a safety regression.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [claude-code, workspace-config, symlink, hooks, silent-failure, multi-agent]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /codex/05-infrastructure/claude-code-settings-symlink.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
  ]
created: 2026-08-11
author: ikennaigboaka
parent_epic: infrastructure_master
priority: P1
source:
  [
    "2026-08-11 — surfaced while cleaning up the team allow-list: a clone-by-clone status sweep found 4/12 clones with
    the tracked settings.json dirty, 2 of them from an unattributed rewrite",
  ]
assigned_vm: NA
resolved_by:
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-11
context_scope:
  [
    scripts/workspace/link-claude-skills.sh,
    scripts/workspace/migrate-personal-settings-keys.sh,
    unified-trading-pm/cursor-configs/settings.json,
    /codex/05-infrastructure/claude-code-settings-symlink.md,
  ]
locked_by:
locked_since:
---

# Hook stripped from the team SSOT via a settings.local.json symlink

> **CORRECTION (2026-08-11).** This doc originally blamed Claude Code for rewriting `.claude/settings.json` through its
> symlink. **That was wrong.** Reading the bootstrap scripts found our own `link-claude-skills.sh` doing it, and the
> symlink at fault is `settings.local.json`, not `settings.json`. The originally-proposed fix (replace the
> `settings.json` symlink with a managed copy) is therefore unnecessary and was NOT applied. Kept visible rather than
> silently edited because the wrong diagnosis is itself the lesson: the observed diff was equally consistent with two
> very different causes, and only reading the writer settled it.

## What I measured (2026-08-11, this host)

| Fact                                                                          | Value                                                                                          |
| ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Clones carrying `cursor-configs/settings.json`                                | 12 (root clone + `.tabs/1..11`)                                                                |
| Clones with that tracked file dirty from an unattributed rewrite              | 2 — `.tabs/3` (mtime 05:35), `.tabs/6` (mtime 05:14)                                           |
| Those two diffs                                                               | byte-identical, `f13abdbded` → `b2f8d29f31`                                                    |
| What the rewrite did                                                          | reformatted `mcpServers.playwright.args`; **deleted the entire `UserPromptSubmit` hook block** |
| Consequence                                                                   | both slots ran without `hooks/context-threshold-nudge.sh`                                      |
| Clones where `.claude/settings.local.json` was a **symlink** to the team file | 3 — `.tabs/1`, `.tabs/3`, `.tabs/6`                                                            |
| Overlap with the contaminated clones                                          | exact — `.tabs/3` + `.tabs/6`; `.tabs/1` was un-fired                                          |
| Is `unified-trading-system-repos/` or `.tabs/N/` a git repo?                  | no — `.claude/` is outside version control everywhere                                          |

## Mechanism (proven, not inferred)

`link-claude-skills.sh` block **(4.5) "Heal settings.local.json"**:

```bash
_local_settings="${WORKSPACE_ROOT}/.claude/settings.local.json"
_cleaned="$(jq '... del(.["UserPromptSubmit"]) | del(.["PreCompact"]) ...' "$_local_settings")"
echo "$_cleaned" > "$_local_settings"
```

Both symptoms fall out of that one line:

1. `>` **follows a symlink.** Where `settings.local.json` pointed at `cursor-configs/settings.json`, the write landed on
   the git-tracked team file.
2. `del(.["UserPromptSubmit"])` is exactly the hook that vanished — the block's stated purpose, applied to the wrong
   file.
3. **jq pretty-prints its output**, which is exactly the `mcpServers.playwright.args` one-line → multi-line reformat in
   the diff.

The block's intent is correct — a stale local registration of `UserPromptSubmit` really does double-fire the hook. It
simply never anticipated its target being a link into the SSOT it was protecting.

The `.claude/settings.json` → team-file symlink is **not** implicated and needs no change. `settings.local.json` is
personal, gitignored, per-clone state and must never be a link to anything.

## Why this is a safety issue, not cosmetics

Under `bypassPermissions` — now the fleet default via Cursor's `claudeCode.initialPermissionMode` — the
`permissions.deny` list is **discarded**, and a `PreToolUse` hook is the only mechanism that can still refuse a tool
call (documented in `agent-orchestrator/scripts/hooks/block_destructive_commands.py` header). Hooks are the entire
remaining guardrail. Any mechanism that silently deletes hook registrations from the SSOT can therefore disarm the
fleet's only enforcement. The hook actually lost here (`context-threshold-nudge.sh`) is benign; the class of failure is
not.

Second-order: nothing ever cleans it up. An agent in `.tabs/3` sees a dirty tracked file it never touched, and the
multi-agent rules correctly forbid committing or reverting another party's uncommitted change — so the diff persists
indefinitely and the clone silently diverges from the SSOT.

## Fix applied 2026-08-11 — unified-trading-pm@9307f909af

1. **Guard in `link-claude-skills.sh`** — block (4.5) now refuses when `$_local_settings` is a symlink and prints the
   readlink target plus why, instead of writing through it.
2. **Removed the three bogus symlinks** in `.tabs/1`, `.tabs/3`, `.tabs/6` (they live outside any repo, so no git state
   was touched; absent is the correct state — 7 other clones already have no such file).
3. **Restored** `.tabs/3` and `.tabs/6` via `git checkout -- cursor-configs/settings.json`; both clean, hook back.
   Pre-restore contents saved off-repo first.

## Todos

- [ ] [SCRIPT] P1. Add a hygiene-sweep check that fails when `cursor-configs/settings.json` is dirty in any clone, OR
      when any `.claude/settings.local.json` is a symlink. The guard above prevents recurrence via this one code path;
      the check catches any other writer that reaches the same file.
- [ ] [INVESTIGATE] P2. Find where the `settings.local.json` symlinks came from — three clones had them and nine did
      not, so some older bootstrap path or a manual step created them. Until that's known, the guard is a backstop
      rather than a root-cause fix.
- [ ] [DOCS] P2. Update `/codex/05-infrastructure/claude-code-settings-symlink.md`: record that `settings.local.json`
      must be a real per-clone file and never a link, and that `cursor-configs/settings.json` is git-TRACKED (the
      `link-claude-skills.sh` header still says it is gitignored, which is stale and was actively misleading during this
      investigation).
- [ ] [DOCS] P2. Record the Cursor permission-mode fix (see Progress Log) in the same codex doc, flagged as
      **per-machine setup**: `claudeCode.allowDangerouslySkipPermissions` + `claudeCode.initialPermissionMode` live in
      Cursor's user settings, which is deliberately personal and untracked, so it does NOT propagate via git — every
      operator machine needs it applied once. State explicitly that `permissions.defaultMode` in settings.json does not
      control IDE sessions.
- [ ] [INVESTIGATE] P2. Decide whether `DISABLE_AUTOUPDATER: "1"` in the team settings is still wanted, now that it pins
      the CLI (1.0.112) a full generation behind the Cursor extension (2.1.227). Document the reason if it stays.
- [ ] [INVESTIGATE] P3. Memory: the `pyright-lsp@claude-plugins-official` plugin spawned one basedpyright language
      server per Claude session — 6 servers against slot 1 alone, 1.6 GB, each independently indexing a 31-repo
      workspace with no sharing. Disabled in the team + personal settings 2026-08-11 at operator direction (in-editor
      diagnostics only; `quality-gates.sh` runs basedpyright itself, so the gate is unaffected). Confirm no workflow
      depended on the in-session diagnostics before making it permanent.

## Progress Log

**2026-08-11** — Filed, then corrected (see banner). Measured the clone sweep, proved the mechanism by reading the
writer rather than inferring from the diff, applied the guard, removed the three symlinks, and restored the two
contaminated clones. Mechanism change to the `settings.json` symlink deliberately NOT made — it was never the culprit.

**2026-08-11 — permission-prompt question RESOLVED (the thread that started this session).** Symptom: constant Bash
permission prompts in the Cursor panel despite `permissions.defaultMode: bypassPermissions` in both the team and
personal settings. Root cause: the Cursor extension resolves its own session permission mode and
**`permissions.defaultMode` in any settings.json does not reach it** — sessions landed in `acceptEdits` (confirmed in
session transcripts: `"permissionMode":"acceptEdits"`).

Fix — two **Cursor** settings, not Claude Code settings, in `~/Library/Application Support/Cursor/User/settings.json`:

```json
"claudeCode.allowDangerouslySkipPermissions": true,
"claudeCode.initialPermissionMode": "bypassPermissions"
```

Verified working. Both are user-level, so they apply to every tab and slot on the machine and live outside all 12 repos
— no contamination.

**Two dead ends recorded so nobody re-walks them**: (1) editing `permissions.allow` is not the lever — neither a
95-entry `Bash(cmd:*)` prefix list nor `Bash(*)` changed which commands prompted, and in bypass mode the allow list is
not consulted at all; (2) `permissions.defaultMode` in the team or personal settings.json is inert for IDE sessions. The
extension setting is the only control. Note that the rest of settings.json stays fully load-bearing under bypass —
hooks, `mcpServers`, `env`, `enabledPlugins` all still apply; only the `permissions` block goes inert.
