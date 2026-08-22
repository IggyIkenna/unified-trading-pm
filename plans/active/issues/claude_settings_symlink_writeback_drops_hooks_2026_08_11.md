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
parent_epic: security_and_cross_cutting_master
priority: P1
source:
  [
    "2026-08-11 — surfaced while cleaning up the team allow-list: a clone-by-clone status sweep found 4/12 clones with
    the tracked settings.json dirty, 2 of them from an unattributed rewrite",
  ]
assigned_vm: planning
resolved_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-08-21
context_scope:
  [
    scripts/workspace/link-claude-skills.sh,
    scripts/workspace/migrate-personal-settings-keys.sh,
    cursor-configs/settings.json,
    /codex/05-infrastructure/claude-code-settings-symlink.md,
    scripts/plan-hygiene/check_settings_symlink_hygiene.sh,
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

- [x] ✅ [SCRIPT] P1. Add a hygiene-sweep check that fails when `cursor-configs/settings.json` is dirty in any clone, OR
      when any `.claude/settings.local.json` is a symlink. The guard above prevents recurrence via this one code path;
      the check catches any other writer that reaches the same file. — `unified-trading-pm@99a13bea88`
      (`scripts/plan-hygiene/check_settings_symlink_hygiene.sh`, wired into `run_hygiene_sweep.sh`; verified PASS on a
      clean workspace and FAIL on both violation modes). Shipped via `infra_satellite_ao_dispatch_batch16_2026_08_13.md`
      (reconciled here 2026-08-15, source doc's own checkbox had gone stale).
- [x] ✅ [INVESTIGATE] P2. Find where the `settings.local.json` symlinks came from — see 2026-08-14 Progress Log entry:
      negative-result investigation — no script, past or present, ever creates a symlink at that path; most likely a
      manual `ln -s` typo by an operator.
- [x] ✅ [DOCS] P2. Update `/codex/05-infrastructure/claude-code-settings-symlink.md`: record that `settings.local.json`
      must be a real per-clone file and never a link, and that `cursor-configs/settings.json` is git-TRACKED (the
      `link-claude-skills.sh` header still says it is gitignored, which is stale and was actively misleading during this
      investigation). — `unified-trading-pm@547e3e8bfb`. Shipped via `infra_satellite_ao_dispatch_batch16_2026_08_13.md`
      (reconciled here 2026-08-15, source doc's own checkbox had gone stale).
- [x] ✅ [DOCS] P2. Record the Cursor permission-mode fix (see Progress Log) in the same codex doc, flagged as
      **per-machine setup**: `claudeCode.allowDangerouslySkipPermissions` + `claudeCode.initialPermissionMode` live in
      Cursor's user settings, which is deliberately personal and untracked, so it does NOT propagate via git — every
      operator machine needs it applied once. State explicitly that `permissions.defaultMode` in settings.json does not
      control IDE sessions. — `unified-trading-pm@e103a86d6c`. Shipped via
      `infra_satellite_ao_dispatch_batch16_2026_08_13.md` (reconciled here 2026-08-15, source doc's own checkbox had
      gone stale).
- [ ] [INFRA] P2. Remove `DISABLE_AUTOUPDATER: "1"` from `cursor-configs/settings.json` per D50 ruling (ADOPTED-REC
      2026-08-21, "Remove unless a specific compatibility issue is guarded — the generation gap risks its own bugs")
      — unless a concrete, currently-live compatibility break against the pinned CLI (1.0.112) is found first, in
      which case document that specific guarded reason inline instead of removing. Done when: the key is removed
      (or, if kept, the settings.json comment states the specific guarded compatibility issue) and
      `quality-gates.sh` passes green.
- [x] ✅ [INVESTIGATE] P3. Memory: the `pyright-lsp@claude-plugins-official` plugin spawned one basedpyright language
      server per Claude session — 6 servers against slot 1 alone, 1.6 GB, each independently indexing a 31-repo
      workspace with no sharing. Disabled in the team + personal settings 2026-08-11 at operator direction (in-editor
      diagnostics only; `quality-gates.sh` runs basedpyright itself, so the gate is unaffected). Confirm no workflow
      depended on the in-session diagnostics before making it permanent. — confirmed via
      `infra_satellite_ao_dispatch_batch16_2026_08_13.md`: grepped every `.json`/`.md`/`.sh`/`.py`/`.yml`/`.yaml` file
      fleet-wide for `pyright-lsp`/`pyright_lsp`/"language server"/"lsp"/"in-session diagnostic" — the only live hit is
      `cursor-configs/settings.json:35`'s own disable line; no skill, codex doc, CI workflow, or script depends on it.
      Negative-result investigation, no code change needed (reconciled here 2026-08-15, source doc's own checkbox had
      gone stale).

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

**2026-08-14 — symlink-origin investigation, negative result (this todo closed).** Searched exhaustively for any
bootstrap path that ever writes a symlink to `.claude/settings.local.json`:

- `git log --all -S"settings.local.json"` and `git log --all -S"ln -s"` cross-referenced against every commit touching
  `scripts/` — the only hits are `link-claude-skills.sh` block (4.5) (reads/heals the file, never symlinks it) and this
  doc's own hygiene-check commits (`8e631c6dff`, `4874b48a52`, `99a13bea88`).
- `link-claude-skills.sh`'s settings-symlink responsibility (`398d8aaa31`, 2026-07-23) and the codex SSOT's documented
  manual per-slot loop (`claude-code-settings-symlink.md`, `3fc71129b3`) both target `.claude/settings.json` only — in
  every historical version of both, the destination variable (`_settings_dest` / `$link`) resolves to `settings.json`,
  never `settings.local.json`.
- Timeline check against the archived `claude_code_settings_symlink_chain_broken_2026_07_23.md`: on 2026-07-23,
  `.tabs/3`'s `settings.local.json` was still a REAL file (it carried redundant hook registrations that session cleaned
  up) — so that slot's symlink was created SOMETIME BETWEEN 2026-07-23 and this doc's 2026-08-11 discovery, by a path
  this investigation could not locate in any git-tracked automation.

**Conclusion**: the three symlinks were not produced by any script — they were most likely a manual `ln -s` by an
operator, plausibly a typo'd re-run of the documented `settings.json`-symlink loop that substituted
`settings.local.json` for `settings.json` (the two filenames differ by one segment, and the same three slots —
`.tabs/1`, `.tabs/3`, `.tabs/6` — were being fixed by hand during the 2026-07-23 incident's manual-fix phase, before the
automated linker existed). No further code-level root cause exists to chase. The 2026-08-11 guard (refuse to write
through a symlink) plus `check_settings_symlink_hygiene.sh` are therefore the complete fix for this failure class, not a
backstop pending a future root-cause patch.

**context-scout 2026-08-17**: refreshed context_scope (4 entries) -- corrected `unified-trading-pm/cursor-configs/settings.json`
(did not resolve from the PM repo root, since the doc lives inside that same repo -- there is no nested
`unified-trading-pm/` directory) to the repo-relative `cursor-configs/settings.json`, matching this doc's own body
convention for every other same-repo path.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)

**na-eligibility-audit 2026-08-18** (infra tranche) [body-hash:d1f41650d3b5a2cd]: KEEP-NA, valid — first audit pass
(no prior marker). Sole open item ("decide whether `DISABLE_AUTOUPDATER` is still wanted") is a policy tradeoff
decision, not a fact-finding task — not worker-determinable alone.

- **2026-08-21 — ruling D50 (Claude CLI autoupdater pin)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch authority,
  AUTONOMOUS_AGENT_RULES rule 2): Remove unless a specific compatibility issue is guarded — the generation gap
  risks its own bugs. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
