---
doc_type: issue
title: "unified-trading-pm (slot-3 checkout) has 26 accumulated git stash entries — not cleaned, not investigated"
summary: >-
  Observed 2026-07-26 during an interactive session: `git stash list` in this slot's unified-trading-pm checkout shows
  26 entries (mostly `autostash`, one named `quickmerge-30831`). This accumulated across many `git pull --rebase
  --autostash` calls this session, several of which reported "Applying autostash resulted in conflicts" without a clean
  pop. Not investigated or cleaned — per the multi-agent safety hard rule ("never `git stash drop` a foreign WIP"), none
  were touched. Flagging so a human (or a session with time to diff each one) decides whether these are safe-to-drop
  noise or contain real, never-recovered WIP.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [git-hygiene, multi-agent-safety, stash]
related: []
created: 2026-07-26
priority: P2
parent_epic: infrastructure_master
source: "slot 3, interactive session, 2026-07-26, discovered mid-task while committing an unrelated fix"
assigned_vm: NA
execution_scope: local-only
sequential: false
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
drift_direction: NA
---

# 26 accumulated stash entries in unified-trading-pm (slot 3) — uninvestigated

## What was observed

`git stash list` returned 26 entries (`stash@{0}` through `stash@{25}`), almost all named `autostash` (the
auto-generated name from `git pull --rebase --autostash`), plus one named `quickmerge-30831`. During this session, at
least one `git pull --rebase --autostash` explicitly reported `Applying autostash resulted in conflicts` — the rebase
itself succeeded, but re-applying the stashed working-tree changes did not cleanly restore, and per this workspace's own
multi-agent safety rule ("never `git stash drop`/`clean` a foreign WIP"), nothing was touched to investigate or clear
it.

## Why this matters

Each stash entry could be: (a) genuinely stale noise from a long-running dirty tree that gets re-stashed every pull
cycle (harmless, just clutter), or (b) real uncommitted work from some other slot/session that never made it back into
the working tree after a conflicted pop — i.e. silent, undetected data loss risk sitting latent in the stash rather than
the working tree. Nobody currently knows which. The pile growing unbounded also raises the risk of an eventual
accidental `git stash clear` (a real, if unlikely, destructive action).

## Recommended next step

- [ ] [DATA] P2. Audit the 26 stash entries in this checkout (`git stash show -p stash@{N}` for each, or `--stat` first
      to triage size): for each, determine whether its diff is (a) already reflected in the current working tree / HEAD
      (safe to drop), or (b) contains real, not-yet-recovered content (needs manual recovery — `git     stash apply` to
      a scratch branch, review, then decide). Report findings before dropping anything. This is a genuinely open-ended
      judgment call (per-entry content review), not a bounded fact-check — best done interactively, not
      blind-dispatched.

## Codex SSOTs

`/codex/05-infrastructure/per-tab-worktrees.md` (multi-agent safety — inherited-dirty-WIP liveness gating).
