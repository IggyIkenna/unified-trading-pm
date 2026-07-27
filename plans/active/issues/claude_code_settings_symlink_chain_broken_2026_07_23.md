---
doc_type: issue
title:
  Claude Code settings.json chain silently decayed fleet-wide — team policy lost, personal/team inverted,
  destructive-command hook unwired
summary: >-
  The 2026-07-09 untrack of `cursor-configs/settings.json` (to stop personal model/effortLevel drift jamming
  slot-cron-ff-pull) correctly moved personal keys out of the tracked file, but nobody re-seeded the file's actual
  team-policy content afterward. On the human-planning VM it had decayed to a 50-byte file holding ONLY the personal
  keys the SSOT says must never live there (model/effortLevel), while every real team-policy key (permissions.allow,
  bypassPermissions default, playwright MCP server, pyright-lsp plugin, and — most importantly — the
  block_destructive_commands.py PreToolUse hook) was gone. Compounding it, `~/.claude/settings.json` was a symlink TO
  that decayed file (the SSOT explicitly forbids this), and the per-slot `.claude/settings.json` symlink documented in
  claude-code-settings-symlink.md was never created anywhere — not at the workspace root, not in `.tabs/1`, not in
  `.tabs/2` — because `setup-tab-worktrees.sh` was never wired to create it (it only ever provisions CLAUDE.md +
  skills). Net effect on this host before the fix: the destructive-command safety hook was not loaded ANYWHERE, and no
  team policy was in effect at all — every Claude Code session was running on defaults only.
status: open
nature: process
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [claude-code, settings, symlink, onboarding, permissions, infra, safety-hook]
related:
  [
    /codex/05-infrastructure/claude-code-settings-symlink.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    scripts/dev/setup-tab-worktrees.sh,
    scripts/workspace/link-claude-skills.sh,
  ]
created: 2026-07-23
parent_epic: infrastructure_master
priority: P1
source:
  [
    chat session 2026-07-23 (operator-reported "missing symlink settings.json from cursor-configs"),
    unified-trading-pm/.gitignore lines ~206-212 (untrack rationale comment),
    git log cursor-configs/settings.json (commits 692fcf969..007fd72ea9),
  ]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-23
---

## What I found

1. **`cursor-configs/settings.json` was git-rm'd + gitignored 2026-07-09** (commits `47b719bc4`, `007fd72ea9`) — correct
   move, since personal `model`/`effortLevel` edits were tripping `slot-cron-ff-pull.sh`'s dirty-check (21+ consecutive
   ticks). The `.gitignore` comment says the right thing: personal overrides belong in the real, untracked
   `~/.claude/settings.json`, not here, and "new clones must re-seed this file manually (it no longer arrives via git)."
   **Nobody actually did that re-seed** — the on-disk copy on the human-planning VM had drifted to
   `{"effortLevel": "xhigh", "model": "sonnet"}` only, i.e. exactly backwards from the SSOT (personal keys where team
   policy should be, team policy entirely absent). Last known-good team content is recoverable from commit `47cf48f8f`
   (permissions.allow list, `defaultMode: bypassPermissions`, `enabledPlugins`, `mcpServers.playwright`).
2. **`~/.claude/settings.json` was a symlink** to the same decayed file —
   `/codex/05-infrastructure/claude-code-settings-symlink.md` explicitly says "Do NOT symlink `~/.claude/settings.json`
   to the tracked file... Keep it a real, personal file," because picking a model via `/model` would otherwise write
   back into the (once-)tracked file.
3. **The per-slot `.claude/settings.json → ../unified-trading-pm/cursor-configs/settings.json` symlink documented in the
   same SSOT (§ "Setup (new machine / new slot)") was never created anywhere on this host** — not at the workspace root
   (`/home/ubuntu/unified-trading-system-repos/.claude/`), not in `.tabs/1/.claude/`, not in `.tabs/2/.claude/`. All
   three only had the `skills → ../unified-trading-pm/cursor-configs/skills` symlink (created by
   `scripts/workspace/link-claude-skills.sh`) and, at the slot roots, a personal `settings.local.json`.
4. **Root cause of #3**: `setup-tab-worktrees.sh`'s `seed_slot_claude_assets()` (called from `provision_slot()`) only
   writes `CLAUDE.md` and links `.claude/skills`. It never calls anything equivalent for `settings.json`. The only place
   the symlink-creation logic exists is a manual bash loop documented in the codex SSOT itself — nobody has ever run it,
   on any slot, on this host.
5. **Each slot's OWN `unified-trading-pm` clone had no `cursor-configs/settings.json` at all** (confirmed absent in both
   `.tabs/1/unified-trading-pm/cursor-configs/` and `.tabs/2/unified-trading-pm/cursor-configs/`) — expected, since the
   file is gitignored and therefore never arrives via the slot's own `git pull --ff-only`. The `.gitignore` comment's
   assumption ("existing per-slot symlinks... keep working off the on-disk copy") silently fails once there is neither a
   symlink nor an on-disk copy — which was the actual state here.

## Why it matters

The `block_destructive_commands.py` PreToolUse hook (referenced from the last known-good team `settings.json`) is a real
safety control — it blocks recursive-delete-class commands for autonomous workers. Because the whole settings chain was
broken, **that hook was not loaded in any Claude Code session on this host** (interactive or slot-dispatched) until this
fix. This is exactly the kind of silent regression the workspace's "rule-amnesia stop" guidance exists to catch, except
there was no hook left to catch it.

## What I already fixed (human-planning VM only, this session, 2026-07-23)

All of the following are local filesystem changes to gitignored/non-repo files — no git commit involved, verified
working live (hook fired correctly on a test destructive-command pattern):

- Rebuilt `unified-trading-pm/cursor-configs/settings.json` with team policy only (permissions.allow = union of the last
  known-good list + operator's newer tool grants, `defaultMode: bypassPermissions`, `mcpServers.playwright`,
  `enabledPlugins.pyright-lsp`, and the `block_destructive_commands.py` PreToolUse hook). No `model`/`effortLevel` in
  this file, per SSOT.
- Made `~/.claude/settings.json` a real file again (`model: sonnet`, `effortLevel: xhigh`), no longer a symlink.
- Propagated the rebuilt team file into `.tabs/1/unified-trading-pm/cursor-configs/settings.json` and
  `.tabs/2/unified-trading-pm/cursor-configs/settings.json` (manual copy — it's gitignored, this must be repeated
  whenever the team file's content changes, on every slot, on every machine).
- Created the three missing symlinks: workspace-root `.claude/settings.json`, `.tabs/1/.claude/settings.json`,
  `.tabs/2/.claude/settings.json`, all `→ ../unified-trading-pm/cursor-configs/settings.json`.

**This only fixes the human-planning VM.** Any other machine/clone in the fleet has the same gitignored file with
whatever content it happened to decay to (or none at all), and the same missing per-slot symlinks — this issue and the
todo below apply fleet-wide, not just here.

## Outstanding — todo

- [x] ✅ [SCRIPT] P1. **Wire per-slot `.claude/settings.json` symlink creation** — done via
      `scripts/workspace/link-claude-skills.sh`'s new responsibility #3 (settings.json) and #4 (hooks dir), called
      automatically from `quality-gates.sh`/`setup-tab-worktrees.sh`/`workspace-bootstrap.sh`. Also added
      `scripts/workspace/migrate-personal-settings-keys.sh` (step 0 of the linker) to self-heal any stray personal
      `model`/`effortLevel`/`theme` key that leaks back into the team file. `cursor-configs/settings.json` re-tracked in
      git (`e5be0047c`) now that personal switches can no longer land in it — this closes the original "gitignored,
      never arrives via git pull, must be manually re-seeded per clone" gap entirely (see codex doc for the current
      model; the July-23 "gitignored" framing above is superseded).
- [x] ✅ [SCRIPT] P2. **Promote the two local-only Claude Code hooks (`context-threshold-nudge.sh`,
      `precompact-block-auto.sh`) to git-tracked `cursor-configs/hooks/`**, symlinked in via `.claude/hooks` the same
      way `.claude/skills` already works (link-claude-skills.sh responsibility #4) — an edit now propagates to every
      root/slot/machine instead of living only on whichever machine authored it (`d998bfa35`).
- [x] ✅ [SCRIPT] P2. **Fixed a second, independent bug found while verifying #2 on a Mac slot (`.tabs/3`,
      2026-07-23)**: the team `cursor-configs/settings.json`'s 3 hook `command` strings were hardcoded ABSOLUTE paths
      rooted at `/home/ubuntu/unified-trading-system-repos/...` (correct for the VM this was authored/tested on, but
      silently broken on ANY other machine with a different home directory / clone location — including this Mac, and
      including every other engineer's laptop). Because the failure is silent (a hook command that doesn't resolve just
      doesn't fire — no error surfaces to the user), this meant the `block_destructive_commands.py` **PreToolUse safety
      guard** — the exact hook this whole issue is about restoring — was STILL not firing on any non-VM machine, for a
      new reason, right after being "fixed." First fix attempt (this session, on `.tabs/3`) used paths relative to the
      session's own root; a parallel session (same operator, different machine) landed first with a cleaner fix —
      **`$CLAUDE_PROJECT_DIR`-based absolute paths** (`35a3926c1`,
      `fix(claude-code): use $CLAUDE_PROJECT_DIR for     portable hook paths in settings.json`) — which superseded the
      relative-path attempt before it shipped (both were in flight concurrently; this doc reflects the version that
      actually landed). **Verified on this Mac** with `$CLAUDE_PROJECT_DIR` set to the session root:
      `block_destructive_commands.py` correctly BLOCKS `rm -rf /` (previously would have silently no-op'd, file not
      found). Also removed the now-fully-redundant personal hook wiring from this slot's own
      `.claude/settings.local.json` (the project-level file covers both hooks now; leaving both would double-fire).
      **Lesson for whoever tests a fix like this next**: verifying "it works" on the ONE machine you're sitting at does
      not prove a hardcoded path is portable — test (or at least grep for) absolute paths before calling a cross-machine
      settings fix done. **Second lesson, from this exact episode**: two sessions fixing the identical bug concurrently
      is a real, recurring cost on this repo right now (heavy multi-agent concurrent-write load) — worth a beat of
      coordination (check recent commits / active plan claims) before starting a fix that's plausibly already in flight
      elsewhere.
- [ ] [SCRIPT] P2. **Document + spot-check other fleet machines** (any other engineer's / VM's checkout of this
      workspace) for the same decayed `cursor-configs/settings.json` / symlinked-`~/.claude/settings.json` /
      missing-per-slot-symlink pattern, and apply the same fix. Should now be a no-op for any machine that just runs the
      hand-off prompt below (re-pull + `link-claude-skills.sh`), since the settings file itself is git-tracked and the
      hardcoded-path bug is fixed — but not independently re-verified on a 3rd machine as of this writing.

## Hand-off prompt for other machines / colleagues

Pull `live-defi-rollout` in your `unified-trading-pm` clone, then run `bash scripts/workspace/link-claude-skills.sh` (or
just let your next `quality-gates.sh` run do it — it calls the same script automatically). That's it. It's fully
idempotent and self-healing: it (1) fixes `~/.claude/settings.json` if it's still a symlink into the tracked team file,
(2) migrates any stray personal `model`/`effortLevel`/`theme` out of `cursor-configs/settings.json` without touching
your existing choice, and (3) creates/repairs the `.claude/settings.json`, `.claude/hooks`, `.claude/skills` symlinks at
your workspace root and every `.tabs/N` slot. Safe to run repeatedly — never fails loudly, never touches a slot with
real uncommitted/diverged git state (just skips it with a message).

**If you pulled BEFORE 2026-07-23's later commits** (i.e. you still see `/home/ubuntu/...` absolute paths in
`cursor-configs/settings.json`'s `hooks` section after linking): that's the hardcoded-path bug above, already fixed
upstream — just `git pull` again to pick it up. If your hooks (especially the destructive-command guard) seem to not be
firing at all after linking and you're not on the original VM this was authored on, check
`cat .claude/settings.json | jq .hooks` for any lingering absolute path and compare against this doc's fix.
