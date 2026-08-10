---
doc_type: codex-ssot
title: Local tmux precompact watcher — personal context-checkpoint automation per tab
summary:
  "A personal, per-tab analog of agent-orchestrator's context_lifecycle.py: run `claude` inside a tmux pane
  (launch-tab-precompact-session.sh) and a standalone watcher (precompact-watcher.py) that nudges, then force-injects,
  /pre-compact followed by /compact via `tmux send-keys` once context usage crosses a threshold — no operator action
  required. Covers setup (fresh machine + per-tab replication), the Cursor/VS Code extension-panel vs terminal-CLI
  distinction (only a real pty is tmux-reachable), safety/idle-detection guarantees ported from AO, and how this
  composes with the separate UserPromptSubmit/PreCompact Claude Code hooks."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm, agent-orchestrator]
scope: [engineer]
tags: [infrastructure, tmux, precompact, context-lifecycle, tabs, cursor, claude-code]
related: [/codex/05-infrastructure/per-tab-worktrees.md, /codex/05-infrastructure/claude-code-settings-symlink.md]
created: 2026-07-23
authoritative_for: [local per-tab tmux precompact-watcher setup]
referenced_by: []
owner:
last_reviewed: 2026-10-25
code_refs:
  [
    unified-trading-pm/scripts/dev/launch-tab-precompact-session.sh,
    unified-trading-pm/scripts/dev/precompact-watcher.py,
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/tmux_spawn.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
  ]
---

# Local tmux precompact watcher — personal context-checkpoint automation per tab

## What this is, in one sentence

A tmux-wrapped `claude` CLI session plus a small watcher process that reads the session's own displayed context
percentage and, once it's high enough, injects `/pre-compact` then `/compact` for you — via `tmux send-keys`, the exact
mechanism agent-orchestrator already uses in production to manage its own worker fleet (`context_lifecycle.py`). This
doc is the personal, single-session, no-agent-orchestrator-required version of that same idea.

## Why this exists / how it relates to the other pieces already in place

There are now **three** independent layers of context-checkpoint automation in this workspace. They compose; they are
not redundant:

1. **Claude Code hooks** (`UserPromptSubmit` nudge + `PreCompact` auto-block) — set up per-session in
   `.claude/settings.local.json`. These run _inside_ Claude Code's own hook system, so they work regardless of transport
   (extension chat panel, terminal CLI, anything). They can nudge and can block silent auto-compaction, but they cannot
   _force_ an action from outside — a hook can't type into its own pane.
2. **This doc's tmux watcher** — an _external_ process that can force `/pre-compact` then `/compact` by literally typing
   them into the session's pane. Requires the session to be a real terminal-hosted `claude` CLI process (see the
   Cursor/VS Code caveat below) — it is the stronger, fully-automatic layer, but only reaches sessions run this way.
3. **agent-orchestrator's `context_lifecycle.py`** — the same idea, but for AO-managed worker/main/review sessions on
   the planning VM, driven by AO's own backlog/plan data instead of a human operator.

If you're not sure which one applies to a given session: the hooks always apply; this doc's watcher only applies to
sessions launched via `launch-tab-precompact-session.sh` (or any tmux-wrapped `claude` CLI session).

## The Cursor / VS Code caveat (read this before setting anything up)

Claude Code's Cursor/VS Code **extension chat panel** (the sidebar UI) is not confirmed to be tmux-reachable — its docs
don't specify the internal transport, and the architecture (webview + IPC to a background process) suggests there's no
exposed pty for `tmux send-keys` to reach. A plain `claude` **CLI** session run in any real terminal — including
Cursor/VS Code's own **built-in integrated terminal tab** — is a genuine pty and unambiguously reachable.

**Practical implication**: you keep using Cursor as your editor exactly as before. For a tab you want this automation
on, talk to Claude Code through a terminal tab (Cursor's built-in one is fine — no separate terminal app needed) instead
of the sidebar chat panel. Everything else about your workflow (editing files, reviewing diffs in Cursor) is unaffected.

---

## Setup — one tab, from scratch

Prerequisites: `tmux` (`brew install tmux` if you don't have it — check with `tmux -V`), `python3` (ships with macOS),
and the `claude` CLI already installed/authenticated.

**Step 1 — launch the tmux session for a tab:**

```bash
bash unified-trading-pm/scripts/dev/launch-tab-precompact-session.sh <tab-dir> [session-name]
# Example, for this workspace's tab 3:
bash unified-trading-pm/scripts/dev/launch-tab-precompact-session.sh \
  ~/Code/unified-trading-system-repos/.tabs/3 claude-tab3
```

This creates a detached tmux session named `claude-tab3` (or your chosen name), `cd`'d into the tab directory, running
`claude`. If a session with that name already exists, it attaches you to it instead of creating a duplicate — safe to
re-run any time.

**Step 2 — attach and use it interactively, exactly as normal:**

```bash
tmux attach -t claude-tab3
```

You see the live, fully interactive Claude Code TUI — nothing about typing, reading responses, or scrollback is any
different from running `claude` directly. Detach without stopping it: `Ctrl-b` then `d`. The session keeps running in
the background; reattach any time with the same command.

**Step 3 — start the watcher, once per session (a separate terminal tab):**

```bash
python3 unified-trading-pm/scripts/dev/precompact-watcher.py claude-tab3
```

Leave this running in the background (or `&` it, or run it under a process supervisor if you want it to survive a
terminal close — a plain backgrounded shell job is enough for personal use). It polls every 15s by default and logs each
action it takes with a timestamp. Stop it any time with `Ctrl-C` — it exits cleanly and does nothing further; your tmux
session is untouched.

### What the watcher actually does (tuning knobs)

Two tiers, cooperative-first — it never interrupts an active turn, a non-empty input box, or a running child process (a
build, a QG, a background command) under the pane's shell:

| Flag                    | Default | Meaning                                                                           |
| ----------------------- | ------- | --------------------------------------------------------------------------------- |
| `--guidance-pct`        | 50      | Context% at which it submits a one-time reminder to run `/pre-compact`            |
| `--force-after-seconds` | 2700    | Seconds an unacked reminder waits before it starts force-injecting                |
| `--idle-observations`   | 3       | Consecutive idle polls required before it will force-inject anything              |
| `--poll-interval`       | 15      | Seconds between checks                                                            |
| `--context-window-k`    | 1000    | Context window size (K tokens, i.e. 1M) used for the token-usage-readout fallback |

Tier 1 (nudge): once, when context% crosses `--guidance-pct` and the pane is idle, it submits a plain reminder message
asking Claude to run `/pre-compact` at its next natural checkpoint.

Tier 2 (forced): if that reminder goes unacked for `--force-after-seconds` **and** the pane has been idle for
`--idle-observations` consecutive polls with nothing pending, it force-injects `/pre-compact`, waits for the pane to go
idle again (proof the checkpoint actually finished), then force-injects `/compact`. A large context drop observed
between polls (self-compaction, or the forced sequence completing) resets the state for a fresh episode.

---

## Replicating across multiple tabs

Each `.tabs/N` slot needs its own tmux session + its own watcher process — there is no shared state between them (each
watcher is a single, independent, in-memory-state process scoped to one tmux session name). Repeat the two commands
above per tab, e.g.:

```bash
bash unified-trading-pm/scripts/dev/launch-tab-precompact-session.sh ~/Code/.../.tabs/1 claude-tab1
bash unified-trading-pm/scripts/dev/launch-tab-precompact-session.sh ~/Code/.../.tabs/2 claude-tab2
bash unified-trading-pm/scripts/dev/launch-tab-precompact-session.sh ~/Code/.../.tabs/3 claude-tab3
# ...one watcher per session, each in its own terminal tab or backgrounded:
python3 unified-trading-pm/scripts/dev/precompact-watcher.py claude-tab1 &
python3 unified-trading-pm/scripts/dev/precompact-watcher.py claude-tab2 &
python3 unified-trading-pm/scripts/dev/precompact-watcher.py claude-tab3 &
```

**Session naming**: use distinct names where none is a prefix of another if you can (`claude-tab1` vs `claude-tab10`) —
both scripts already use tmux's exact-match target syntax (`={name}` / `={name}:`) internally to avoid the
prefix-collision class of bug (`tmux_spawn.py:exact_pane_target`'s own docstring covers the incident this guards
against), so this is a defense-in-depth note, not a hard requirement.

**Resource cost**: running 10 tmux sessions is trivial — tmux itself has near-zero overhead (it's just managing ptys).
The real ceiling is how many concurrent `claude` processes/API calls your machine and account can sustain, which is the
same constraint this workspace's fleet already documents (`codex/12-agent-workflow` "max 10 parallel agents"), not
something this tooling adds.

---

## Colleagues / other machines — full copy-paste setup

Send a colleague this: clone or pull `unified-trading-pm` (the two scripts live in `scripts/dev/`), then run the Setup
section above verbatim, substituting their own tab directory and a session name of their choice. Nothing here is
machine-specific or requires any credentials/config beyond `tmux` + `python3` + an already-working `claude` CLI — the
scripts take the tab directory and session name as plain arguments.

---

## Troubleshooting

- **`tmux: command not found`** — `brew install tmux`.
- **Watcher exits immediately with "No tmux session named ..."** — run `launch-tab-precompact-session.sh` first; the
  watcher expects the session to already exist.
- **Watcher logs "Session '...' is gone — nothing more to watch, exiting."** — the tmux session was killed (or `claude`
  exited); this is expected, not an error. Relaunch the session and restart the watcher.
- **The forced `/pre-compact`/`/compact` never fires** — check the watcher's log for repeated silence; the most likely
  cause is the pane never goes idle long enough (e.g. you're actively working, or something is continuously printing).
  This is by design — it will never force over active work.
- **Nudge/force text appears while I'm mid-typing something else** — should not happen: both tiers check
  `pane_input_pending`/idle-classification before injecting anything, exactly mirroring the safety checks
  `context_lifecycle.py` uses in production. If you do see this, it's a real bug — file an issue doc.

## Code references

- `unified-trading-pm/scripts/dev/launch-tab-precompact-session.sh` — the tmux launch/attach wrapper.
- `unified-trading-pm/scripts/dev/precompact-watcher.py` — the watcher; ported regexes/verified-submit pattern cite
  their exact AO source lines in its module docstring and inline comments.
- `agent-orchestrator/server/context_lifecycle.py`, `server/tmux_spawn.py`, `server/worker_liveness/__init__.py` — the
  SSOT this tooling is a personal-scale port of. Any future change to the pane-parsing regexes or the verified-submit
  pattern there should be mirrored here (and vice versa) to avoid drift.
