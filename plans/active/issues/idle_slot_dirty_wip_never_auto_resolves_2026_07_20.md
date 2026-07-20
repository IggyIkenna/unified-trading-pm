---
doc_type: issue
title: Idle-slot dirty WIP never auto-resolves — FM8 orphan-inherit only fires on spawn
summary:
  Slot 14 paged `agent-orchestrator-alerts` "STILL RED" for 40+ hours (dirty uv.lock) with NO live tmux session at all —
  nothing was ever going to trigger the existing FM8 orphan-WIP inherit mechanism, because that mechanism only runs at
  pre-spawn, and nothing was trying to spawn into slot 14.
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, fleet-health, liveness, orphan-wip, dirty-worktree]
related:
  [
    plans/active/ao_fleet_infra_hardening_2026_07_20.md,
    plans/active/ao_worker_lifecycle_reap_2026_07_20.md,
    plans/active/ao_uniform_agent_liveness_contract_2026_07_20.md,
  ]
created: 2026-07-20
parent_epic: orchestrator_master
priority: P2
resolved_by:
source: ao_fleet_infra_hardening_2026_07_20.md todo-6 alert follow-up (2026-07-20)
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-20
locked_by:
locked_since:
---

# Idle-slot dirty WIP never auto-resolves

## What I found

Investigating a live `agent-orchestrator-alerts` page ("Slot 14 git STILL RED — reminder ... instruments-service: dirty
1 file(s) for 2433m"), during the `ao_fleet_infra_hardening_2026_07_20.md` fleet sweep:

- Slot 14's `.agent-claim` had `expires_at: 2026-07-18T19:02:07Z` — over 21h expired.
- `tmux list-sessions` on the orchestrator VM showed NO `orch-slot-14` session at all (slots 1-3,5-10 all had one; 14
  did not).
- The dirty file (`uv.lock`, one new package pin) had sat uncommitted since 2026-07-18.

`server/worktree_clean_check/_orphan.py`'s `commit_and_push_dirty_repos` — the mechanism that inherits exactly this
class of dead-maker dirty WIP (`chore(orphan-wip)` commit → push to a content-addressed `wip-preserve/` ref → realign to
a clean `origin/<base>`) — is invoked from the **pre-spawn dirty-state gate** (`resolve_dirty_state`, called by
`server.py::spawn_slot` / `autospawn._do_spawn` / the auto-respawn paths). All of those triggers require an attempt to
**spawn into the slot**. Slot 14 had no live session and, evidently, nothing was attempting to respawn into it either —
so the dirty state just sat there, un-inherited, for 40+ hours, with `slot-git-status-report.sh`'s dirty-streak detector
paging every cycle and nothing on the resolution side ever firing.

This is not a one-off: any slot that goes idle (dispatch finishes, claim expires, and AutoSpawn doesn't pick a new task
for that specific slot) with dirty tracked content will alarm forever until either (a) an operator manually resolves it,
or (b) something eventually spawns into that exact slot again.

## What I did (stopgap, not a fix)

Manually replicated `commit_and_push_dirty_repos` via SSM for the three affected clones (VM slots 4/14/15
`instruments-service` — all independently classified "dead"/"absent" per the FM8 liveness discriminator) plus laptop
slot 5's `unified-trading-pm` (landed properly via `quickmerge` since it was coherent plan content, not code). All four
now measure dirty=0. See `ao_fleet_infra_hardening_2026_07_20.md` Progress Log (2026-07-20 entries) for the full
per-clone detail and evidence.

## Recommendation (not yet actioned)

Give the dirty-streak DETECTOR (`slot-git-status-report.sh`, every 5 min) a resolution-side complement instead of
relying solely on the next spawn attempt:

- Simplest: a periodic sweep (cron or orchestrator background loop) that runs the SAME `resolve_dirty_state` /
  `commit_and_push_dirty_repos` path against every slot that is CURRENTLY dirty + has no live tmux session — i.e. treat
  "detected dirty + provably dead" as its own trigger, not just "about to spawn here."
- Reuses existing, tested code (`_orphan.py` + the FM8 liveness gate) — no new resolution logic, just a new caller.
- Gate: a deliberately-idle dirty slot (no tmux, expired/absent claim) gets inherited within one sweep interval, without
  needing a spawn attempt first.

## Codex SSOTs

- `codex/05-infrastructure/per-tab-worktrees.md` § "Pre-spawn branch-state + liveness-gated dirty resolution" — the
  existing FM8 mechanism this gap sits next to.
- `agent-orchestrator/server/worktree_clean_check/_orphan.py`, `_liveness.py` — the code to reuse.
