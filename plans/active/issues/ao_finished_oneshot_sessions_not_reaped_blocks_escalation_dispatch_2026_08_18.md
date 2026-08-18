---
doc_type: issue
title: >-
  Finished one-shot escalation sessions (slots 31/32/33) never torn down — `_pick_free_slot` sees them
  as occupied, so new escalations retry "no free configured slot" indefinitely despite a genuinely
  finished, idle worker sitting in every reserved slot
summary: >-
  Live-confirmed 2026-08-18: escalation `agt-3896a8` (market-tick-data-service, data_pipeline_failure)
  sat `status=queued`, `last_error="no free configured slot to dispatch escalation onto"` for 28
  attempts / ~28 minutes while the CI-escalation reserve (slots 32/33) and the sched reserve (29-31)
  all showed `status: idle` / `worker_alive: false` in the dashboard. Direct SSM `tmux list-sessions`
  + `tmux capture-pane` on the orchestrator VM showed all 5 slots have a LIVE tmux session right now,
  each one sitting at an idle interactive prompt (`❯`) having already finished real one-shot work
  (a `plan_reconciler` run on 31, a DP-monitor redeploy fix on 32, the exact `DP-WATCHER-006`
  escalation `agt-0c542c` on 33). `escalation.py::_pick_free_slot` requires
  `not tmux_spawn.has_session(...)` to treat a slot as free — by design, correctly refusing to hijack
  an occupied slot — but the boot prompt's own "COMPLETE THEN STOP" contract states `/done` triggers
  "the reaper cleans your session," and that isn't happening: a genuinely-finished one-shot worker's
  tmux session survives indefinitely, permanently removing that slot from the free pool until
  something else notices and kills it.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao, escalation, slot-reclaim, reaper, tmux, one-shot-lifecycle, capacity]
related:
  [
    /plans/active/issues/ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md,
    /codex/04-architecture/agent-orchestrator-scheduled-jobs.md,
  ]
created: "2026-08-18"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
assigned_role: infra
drift_direction: none
source: >-
  Interactive session 2026-08-18, slot 3 — operator noticed a live dashboard screenshot showing
  slots #28-33/#9001 all IDLE with "✓ done" badges while a real escalation sat queued 28 attempts
  waiting for a free slot, and pushed back on my earlier (incomplete) account-exhaustion framing.
  Direct code read of `escalation.py::_pick_free_slot` + live `tmux list-sessions`/`capture-pane`
  on the orchestrator VM confirmed the real mechanism.
resolved_by:
locked_by:
depends_on: []
---

# Finished one-shot sessions never reaped — blocks escalation dispatch onto their own slots

## What I found

`escalation.py::_pick_free_slot`'s docstring is explicit about its own contract: a slot is "free" only
when it has **no** `orch-slot-N` tmux session at all — `killed` status is fine (that's exactly the
capacity a watchdog reap frees), but a live session, regardless of what's happening inside it,
disqualifies the slot unconditionally. This is correct, deliberate design (protects against
hijacking a slot mid-work).

The gap is on the OTHER side: `agents/data_pipeline_failure.md`'s boot prompt (and presumably every
other one-shot escalation boot prompt) tells the worker that calling `/done` with
`one_shot_complete: true` causes "the backend archives your AgentRow `lifecycle-complete`, frees
your slot, and the reaper cleans your session" — i.e., the WORKER's job is just to call `/done`;
tearing down the tmux session is supposed to be someone else's (the reaper's) job, asynchronously.

Live-confirmed this isn't happening reliably. All three reserve-pool slots I inspected
(`orch-slot-31`, `orch-slot-32`, `orch-slot-33`) have live tmux sessions RIGHT NOW, each sitting at
an idle `❯` prompt having already finished a real piece of work:

- **Slot 31**: finished a `plan_reconciler` dispatch (shipped `unified-trading-pm@e1c1634518`),
  ended with `✻ Sautéed for 15m 56s`, sitting at an empty prompt since.
- **Slot 32**: finished a DP-monitor Cloud Build redeploy fix, then received a FOLLOW-UP interactive
  prompt ("check the agent-orchestrator dashboard for any other open escalations") — not just idle,
  actually mid-conversation with something/someone.
- **Slot 33**: finished escalation `agt-0c542c` (DP-WATCHER-006, `deployment-service@03be2c2ada` +
  `unified-trading-pm@81a76ef37c`), sitting at an empty prompt since.

Meanwhile `GET /api/escalations/active` showed a genuinely NEW escalation, `agt-3896a8`
(market-tick-data-service, `data_pipeline_failure`), stuck `status=queued`, `attempts=28`,
`last_error="no free configured slot to dispatch escalation onto"` — every one of its 28 dispatch
attempts correctly found zero slots satisfying `_pick_free_slot`'s no-live-session requirement,
because the pool's actual free capacity is smaller than the dashboard's `status`/`worker_alive`
fields suggest. The DB fields say "idle"; the physical tmux state says "occupied" — the two have
drifted apart.

## Why it matters

This silently shrinks the effective escalation-reserve pool over time: every one-shot worker that
finishes cleanly (the GOOD outcome) still permanently removes its own slot from the free pool unless
something else notices and kills the leftover session. Under sustained load this can degrade toward
the exact "no free configured slot" starvation already documented in the sibling issue
(`ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md`) — but THAT doc's root cause was the reserve
slots being administratively `paused` on an exhausted account; THIS is a distinct mechanism (slots
that were never paused, never exhausted, just never reaped after finishing) producing the identical
user-visible symptom. Conflating the two would misdiagnose a future recurrence.

## Recommended decision

Needs a real investigation into "the reaper," not a guess:

- Identify the actual reaper/pruner mechanism this boot-prompt comment refers to (`tmux_pruner.py`
  is the obvious candidate — confirm it's the right module, not assumed) and determine why it isn't
  clearing these three sessions: is it not running/ticking, does it require a signal this `/done`
  call isn't sending, or does it deliberately leave a session alive for some reason (e.g. giving an
  operator a window to review the transcript) that conflicts with the free-pool's needs?
- Slot 32's mid-conversation follow-up prompt suggests at least SOME of these sessions are being
  kept alive deliberately (an operator or another process continuing to use them) rather than purely
  a reaper bug — worth distinguishing "reaper isn't running" from "reaper is correctly NOT killing a
  session someone is still using" before proposing a fix, since a blind more-aggressive reaper could
  kill a session mid-legitimate-use.
- Consider whether a stuck-escalation retry (`agt-3896a8`-style, N attempts with the identical
  no-free-slot error) should itself trigger a check for exactly this condition (idle-at-prompt,
  post-`/done`, tmux-still-alive) as a distinct, page-worthy signal, separate from genuine account
  exhaustion.

## Todos

- [ ] [SCRIPT] P1. Identify why the finished one-shot sessions on slots 31/32/33 (and check the rest
      of the fleet for the same pattern, not just these three) still have live tmux sessions after
      `/done` — read `tmux_pruner.py` (or whichever module is actually responsible) and determine
      root cause live, not from the docstring's stated intent alone. Repo: agent-orchestrator.
- [ ] [SCRIPT] P2. Once root-caused, fix it so a one-shot worker's slot genuinely returns to
      `_pick_free_slot`'s free pool promptly after `/done` (bounded by whatever grace period, if any,
      is intentional for post-completion review) — cite the fix + a live re-verification that a
      subsequently-queued escalation actually claims a freshly-reaped slot. Repo: agent-orchestrator.
