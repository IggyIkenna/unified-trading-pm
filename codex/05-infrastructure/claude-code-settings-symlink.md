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
related:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    /plans/archive/issues/claude_code_settings_symlink_chain_broken_2026_07_23.md,
  ]
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
   (playwright), the registered `hooks` (`PreToolUse`/`UserPromptSubmit`/`SessionStart`/`PostToolUse`, see below), and
   the bypass-smoothing flags. **It contains NO `model`/`theme`/`effortLevel`/ `workspaces`** — those are personal and
   must never be committed (a committed `model: opus` would silently force Opus on the whole fleet, violating the
   Sonnet-default rule in `/codex/06-coding-standards/model-tier-selection.md`). Each slot inherits this file via a
   project-level symlink.

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

The hooks in this file's `hooks` key — `PreToolUse` → `block_destructive_commands.py`, `UserPromptSubmit` →
`context-threshold-nudge.sh`, `SessionStart` → `session-start-collision-check.sh`, `PostToolUse` → `batching-nudge.py`
(2026-08-10) — reference their scripts via `$CLAUDE_PROJECT_DIR/...`, not an absolute path. (This said "the 2 hooks"
until 2026-08-10, having rotted as hooks were added — enumerate, never re-add a count.) Claude Code exports
`CLAUDE_PROJECT_DIR` to every hook-command subprocess, set to the project root the session was launched from — confirmed
empirically (2026-07-23) to resolve correctly and DIFFERENTLY per launch root: a session opened at the true workspace
root gets that path, one opened in `.tabs/1` gets `.../.tabs/1`, one opened in `.tabs/2` gets `.../.tabs/2` — each then
naturally resolves to that root's OWN clone of the hook script, not the main root's. This is what makes ONE tracked
`settings.json` (symlinked into every root) work unmodified fleet-wide, regardless of username or workspace path on a
given machine — no per-machine edit needed. Official reference:
[code.claude.com/docs/en/hooks.md](https://code.claude.com/docs/en/hooks.md) (`${CLAUDE_PROJECT_DIR}` env-var table
entry) — this fact was never captured anywhere in this codex before 2026-07-23, which is why the hardcoded path crept in
originally; see `/plans/archive/issues/claude_code_settings_symlink_chain_broken_2026_07_23.md` for the full
investigation.

**Known gap (unrelated, flagging so it isn't re-discovered the hard way)**:
`claude -p ... --dangerously-skip-permissions` (non-interactive print/headless mode) does NOT enforce `PreToolUse` hook
blocking — confirmed 2026-07-23 for both the old hardcoded-path and new `$CLAUDE_PROJECT_DIR` forms of the
destructive-command guard equally, so it's not a path-portability issue. This is undocumented in Anthropic's official
docs too. It doesn't affect real agent-orchestrator workers (`agent-orchestrator/server/tmux_spawn.py::spawn` launches a
genuine INTERACTIVE `claude` session inside a detached tmux pane and pastes the boot prompt — no `-p`/`--print` flag
anywhere in the real dispatch path), but don't assume hooks gate a `claude -p` invocation if one ever gets scripted
elsewhere. See `agent-orchestrator/scripts/hooks/block_destructive_commands.py`'s docstring for the same note at the
code site.

## `PostToolUse` → `batching-nudge.py`: how a behavioural hook reaches the WHOLE fleet (2026-08-10)

Registered because a written rule had already failed at this problem: `SUB_AGENT_MANDATORY_RULES.md` has carried a
batching directive since ~2026-08-05 (measured then: ~11% of fleet turns batched >1 call), yet a controlled measurement
five days later still found 57.3% of ALL calls in collapsible same-tool chains. In-loop feedback at the moment of the
behaviour is a different mechanism from a rule read once at session start. Rationale + baseline:
`/codex/06-coding-standards/tool-call-batching.md`.

**Propagation — the reason a hook is worth writing at all:**

| Piece                                      | How it reaches other slots / machines                                                                                 |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------- |
| `cursor-configs/hooks/batching-nudge.py`   | git-tracked, mode `100755` (`core.fileMode=true`), so the exec bit survives the pull                                  |
| the `PostToolUse` registration             | lives in `cursor-configs/settings.json`, **git-tracked** since 2026-07-23                                             |
| the `<root>/.claude/settings.json` symlink | created by `scripts/workspace/link-claude-skills.sh` — run by `workspace-bootstrap.sh` AND `scripts/quality-gates.sh` |

A slot or teammate machine that pulls `live-defi-rollout` and has bootstrapped (or has simply run PM's quality gate
once) picks this up with no further action. **Real agent-orchestrator workers are covered**: `tmux_spawn.spawn()`
launches a genuine INTERACTIVE `claude` in a detached tmux pane, so hooks apply — the `claude -p` gap noted above is
explicitly NOT the dispatch path. AO workers get their own `CLAUDE_CONFIG_DIR` (user-level, seeded only with
`autoUpdates: false`); hooks here are PROJECT-level and resolve from the slot's own checkout.

**It nudges, never blocks.** `PostToolUse` (the call already ran), every failure path exits 0 silently, and it HOLDS its
counter rather than advancing when calls arrive within `SAME_MESSAGE_WINDOW_SECONDS` — so an agent already batching
correctly is never nudged. A naive same-tool counter would fire hardest at correct behaviour, the one outcome that would
make this hook worse than nothing.

## `PreCompact` stays UNREGISTERED — client-side auto-compact must remain enabled (HARD RULE, 2026-08-06)

This file registers **no** `PreCompact` hook, and must not gain one that blocks compaction. Until 2026-08-06 it wired
`matcher: "auto"` → `precompact-block-auto.sh`, which `exit 2`'d every automatic compaction fleet-wide; that script is
now DELETED and the registration removed (operator ruling).

Why it can't come back: auto-compact is the **last-resort safety net** under the backend's own forced path
(`agent-orchestrator/server/context_lifecycle.py` — `/pre-compact` then `/compact`, injected via
`tmux_spawn.submit_to_pane`). If the forced injection does not land — the latch is stuck, the pane is wedged, the
orchestrator is restarting — the session keeps growing until it exceeds the model's hard context limit, at which point
**every** request 400s, `/compact` INCLUDED (compaction has to send the whole history to summarize it), and the session
is unrecoverable. That is not hypothetical: prod slot 3 reached exactly that state on 2026-08-06 (~971k message tokens
against a 1,048,576 limit) and had to be destroyed by hand. Blocking auto-compact removes the one net that catches this
class, and it costs real money — the wedged stretch burned 76.4M cache-read tokens completing zero calls.

The concern the block was protecting against — a bare compact discarding in-flight findings — is handled by ordering,
not by blocking: `/pre-compact` runs FIRST and asks the agent to write anything context-only into its plan/issue docs,
so a later compact loses nothing durable. A hook that blocks auto-compact protects nothing that `/pre-compact` has not
already protected, and it forfeits the net.

Stale local registrations are swept: `scripts/workspace/link-claude-skills.sh` step (4.5) strips any `PreCompact` key
from a machine's `.claude/settings.local.json`, so a host still carrying the retired block gets auto-compact back on its
next run. SSOT for the failure mode: `/plans/archive/issues/ao_worker_context_saturation_unrecoverable_2026_08_06.md`.

## `settings.local.json` must be a REAL per-clone file — never a symlink (2026-08-11)

`.claude/settings.local.json` is personal, gitignored, per-clone state (allow-prompt grants, stale local hook
registrations `link-claude-skills.sh` block (4.5) heals via `jq ... | echo > "$file"`). If it is ever a **symlink**
(observed in `.tabs/1`, `.tabs/3`, `.tabs/6`, 2026-08-11) — most likely a manual `ln -s` typo substituting
`settings.local.json` for `settings.json` in the per-slot symlink loop above, not created by any script (exhaustive
`git log -S` search found none) — that healing write follows the link. When the link pointed at the TRACKED
`cursor-configs/settings.json`, the write landed on the team SSOT instead: `del(.hooks.UserPromptSubmit)` silently
stripped that hook from the shared file, and jq's pretty-print reformatted the rest, so two clones ran for a time
without `context-threshold-nudge.sh`. Under `bypassPermissions` (the fleet default), `permissions.deny` is discarded, so
hooks are the ONLY surviving guardrail — a mechanism that can silently delete hook registrations from the SSOT is a
safety regression, not cosmetics. Fixed 2026-08-11 (`unified-trading-pm@9307f909af`): `link-claude-skills.sh` (4.5) now
refuses to write when `settings.local.json` is a symlink, and `scripts/plan-hygiene/check_settings_symlink_hygiene.sh`
(wired into `run_hygiene_sweep.sh`) fails the hygiene sweep if `cursor-configs/settings.json` is dirty in any clone OR
any `.claude/settings.local.json` is a symlink — never create one by hand. Full investigation:
`/plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md`.

## `cursor-configs/settings.json` git-tracked status — confirmed current (2026-08-11 re-check)

Re-verified during the same 2026-08-11 investigation: `cursor-configs/settings.json` **is git-tracked**, per the
"2026-07-23 update" note above — this is not stale. The one place that IS still stale is
`scripts/workspace/link-claude-skills.sh`'s own header/inline comments (lines ~21-22, ~113, ~124), which still describe
the file as gitignored and instruct a manual re-seed; that script text was actively misleading during the 2026-08-11
investigation and needs its own follow-up fix (tracked in the source issue doc above) — this codex doc's facts, not that
script's comments, are authoritative.

## Cursor permission-mode: two PER-MACHINE settings, not Claude Code settings (2026-08-11)

Constant Bash permission prompts in the Cursor IDE panel despite `permissions.defaultMode: bypassPermissions` in both
the team and personal `settings.json` — root cause: **the Cursor extension resolves its own session permission mode, and
`permissions.defaultMode` in any `settings.json` (team or personal) does not reach it.** Sessions silently landed in
`acceptEdits` (confirmed in session transcripts: `"permissionMode":"acceptEdits"`).

Fix — two **Cursor** settings (not Claude Code's `settings.json`), in Cursor's own user settings
(`~/Library/Application Support/Cursor/User/settings.json` on macOS; the equivalent per-OS Cursor user-settings path
elsewhere):

```json
"claudeCode.allowDangerouslySkipPermissions": true,
"claudeCode.initialPermissionMode": "bypassPermissions"
```

**This is deliberately PER-MACHINE, not fleet-propagating.** Cursor's user settings are personal and untracked by design
(same reasoning as `~/.claude/settings.json` above) — they live outside all 12 repos, so a `git pull` never carries
them, and every operator machine needs this applied once, by hand. Both keys are user-level, so once set they apply to
every tab/slot on that machine.

Two dead ends confirmed during the 2026-08-11 investigation, recorded so they aren't re-walked:

1. Editing `permissions.allow` is not the lever — neither a 95-entry `Bash(cmd:*)` prefix list nor a bare `Bash(*)`
   changed which commands prompted; in bypass mode the allow list is not consulted at all.
2. `permissions.defaultMode` in the team OR personal `settings.json` is inert for IDE sessions — the Cursor extension
   setting above is the only control that reaches it.

Note the rest of `settings.json` stays fully load-bearing under bypass mode — hooks, `mcpServers`, `env`,
`enabledPlugins` all still apply; only the `permissions` block goes inert. Full investigation:
`/plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md`.

## Notes

- The per-slot symlink lives in `.tabs/<N>/.claude/` which is **not** inside any git repo, so it is never committed.
- **Still getting allow-prompts?** That's the session's permission MODE, not the settings. `bypassPermissions` is the
  default; a session launched in "default/ask" mode overrides it (and persists each grant into
  `.claude/settings.local.json`). Toggle the mode (Shift+Tab in the IDE extension) or relaunch.
- A slot is skipped by the setup loop when it hasn't pulled the commit that adds `cursor-configs/settings.json` — re-run
  after `git pull --ff-only`.
