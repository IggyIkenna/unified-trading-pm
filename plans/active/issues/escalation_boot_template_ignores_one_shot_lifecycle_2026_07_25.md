---
doc_type: issue
title: >-
  agent-orchestrator's shared boot-message composer (server/prompts.py::_compose) tells every SLOTTED role — including
  one-shot escalation roles (cicd/conflict_resolver/data_pipeline_failure) — to call the worker `/boot` queue-drain
  endpoint, directly contradicting those roles' own `does_not` rule against entering the worker boot heartbeat loop
summary: >-
  Found live during a `cicd` escalation (agt-e0a637, plan_health wall on unified-trading-pm). My initial boot message
  (generated server-side) had a "STEP 2 — boot: POST $SERVER_URL/api/slots/$SLOT_ID/boot ... The response carries your
  task" instruction, so I called it. It returned `already_in_progress: true` with a completely unrelated, stale leftover
  task (`sports_odds_markets_...-004`) from a PRIOR generic-worker occupant of the same slot number — not my escalation
  at all. Only by then reading `agents/cicd.md` (which explicitly lists `does_not: Enter the worker /boot heartbeat loop
  (it is one-shot, not a queue-drainer)`) did I realize the boot message's own STEP 2 was wrong for this role and I
  should ignore it, working instead directly off the `$WALL_TYPE`/`$CONTEXT`/`$ESCALATION_ID` session vars already
  present in the boot message.

  Root cause (read `server/prompts.py` + `server/escalation.py` to confirm, not just inferred): `_compose()` branches
  the STEP 2/STEP 3 text purely on `slot_id is not None` (prompts.py:127-171). Every escalation worker IS spawned with a
  real `slot_id` (it borrows a fleet slot), so it always takes the "slot worker" branch and always gets the generic
  `/boot` instruction — the composer never looks at `lifecycle` at all. Meanwhile `escalation.py` DOES set
  `lifecycle="one_shot"` on the AgentRow (escalation.py:503-506) — but only for reaper/watchdog bookkeeping ("its
  session ending is EXPECTED, not a stale-agent incident"), never threaded into the boot-text composer. The three
  escalation role docs (`agents/cicd.md`, `agents/conflict_resolver.md`, `agents/data_pipeline_failure.md`) all declare
  `lifecycle: one_shot` + an explicit `does_not: Enter the worker /boot heartbeat loop` — so the generated boot message
  and the role's own canonical doc directly contradict each other for all three roles, every time.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    escalation,
    boot-sequence,
    prompts,
    one-shot,
    lifecycle,
    cicd,
    conflict_resolver,
    data_pipeline_failure,
  ]
related: []
created: "2026-07-25"
parent_epic: orchestrator_master
assigned_vm: planning
priority: P1
locked_by:
resolved_by: agent-orchestrator@6495d52
source:
  "found live during cicd escalation agt-e0a637 (unified-trading-pm#1465, plan_health wall); filed during the session's
  /pre-compact durability sweep, 2026-07-25"
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# agent-orchestrator boot-template STEP 2 contradicts one-shot escalation roles' `does_not` rule

## What I found

`server/prompts.py::_compose()` decides which boot-message shape to emit using a single condition: `slot_id is not None`
(see `parts += [...]` blocks around lines 127 and 156). Any role spawned onto a real fleet slot — which includes every
escalation worker (`cicd`, `conflict_resolver`, `data_pipeline_failure` — they borrow a slot to run in) — gets the "slot
worker" boot shape, whose STEP 2 unconditionally reads:

```
STEP 2 — boot: POST $SERVER_URL/api/slots/$SLOT_ID/boot with your session vars AND
"read_files": [...]. ... The response carries your task.
```

But all three escalation role docs explicitly forbid exactly this:

- `agents/cicd.md` frontmatter:
  `does_not: [..., "Enter the worker /boot heartbeat loop (it is one-shot, not a queue-drainer)"]`
- `agents/conflict_resolver.md`:
  `does_not: [..., "Enter the worker /boot heartbeat loop (one-shot, not a queue-drainer)"]`
- `agents/data_pipeline_failure.md`:
  `does_not: [..., "Enter the worker /boot heartbeat loop (one-shot escalation, not a queue-drainer)"]`

`escalation.py` DOES know these are one-shot — it stamps `lifecycle="one_shot"` on the `AgentRow` at spawn (line
~503-506) — but that value is only consumed by the reaper/watchdog, never passed into `prompts.py`'s composer. So the
composer has no way to know, and always emits the generic worker-loop STEP 2/3 text for any slotted spawn.

**Live reproduction (this session, escalation agt-e0a637):** I followed my boot message's STEP 2 literally and POSTed
`/api/slots/7/boot`. The response was
`{"already_in_progress": true, "task": {"id": "sports_odds_markets_outcomes_settlements_arbitrage_expected_since_2024_zero_captured-004", ...}, "dispatch_reason": "resume"}`
— a completely unrelated task left on slot 7 by whatever generic worker occupied it before my escalation spawned.
Nothing in the `/boot` response referenced my escalation, `$ESCALATION_ID`, or `$WALL_TYPE` at all. I only avoided
actually working that stale task because I had already read `cicd.md`'s `does_not` line per STEP 1 and recognized the
contradiction. A worker that reads STEP 1 more superficially, or a role file that's missing/stale for some reason, could
plausibly start executing whatever `already_in_progress` task the `/boot` response hands back — which is a completely
different piece of work than the escalation it was actually dispatched to fix.

## Why it matters

- **Correctness risk, not just noise**: `/boot`'s `already_in_progress`/`resume` response returns real, actionable task
  data. An escalation worker that trusts its own boot message (reasonable — that's the contract every other role
  follows) can be steered onto stale unrelated work instead of the wall it was actually paged for, silently defeating
  the whole point of the escalation (the real wall stays unresolved while the worker burns its one-shot budget on
  someone else's leftover task).
- **Every future cicd / conflict_resolver / data_pipeline_failure escalation hits this**, not just this one instance —
  it's a template bug, deterministic given a slotted one-shot role + any pre-existing slot task state.
- **The contradiction is invisible unless you read both documents side by side** — the boot message itself looks
  authoritative and self-consistent; only cross-checking against the role file's `does_not` list catches it. That's a
  fragile safety margin to depend on for every single escalation dispatch.

## Recommended decision

Thread `lifecycle` (or equivalently, `role in {"cicd", "conflict_resolver", "data_pipeline_failure"}`) into
`_compose()`'s branch condition so one-shot escalation roles get boot text that matches their actual contract: STEP 0
heartbeat + STEP 1 reads unchanged, but STEP 2 should point at the escalation's own session vars
(`$ESCALATION_ID`/`$WALL_TYPE`/`$REPO`/`$PR_NUMBER`/`$CONTEXT` — already present in the session-vars block) as the task
source, not `/boot`. STEP 3 (completion) can stay the same one-shot-complete `/done` call, since that part is already
correct and consistent with the role docs.

- [x] [CODE] P1. ✅ `agent-orchestrator@6495d52`. Added a module-level `_ONE_SHOT_ESCALATION_ROLES` frozenset
      (`{"cicd", "conflict_resolver", "data_pipeline_failure"}`) and branched `_compose()` on
      `role in     _ONE_SHOT_ESCALATION_ROLES` (checked before the generic `slot_id is not None` branch, not instead of
      it — STEP 0/1 stay identical). The one-shot branch's STEP 2 text deliberately never mentions the `/boot` endpoint
      at all (not even in a "do NOT call X" warning — the recommended decision's exact wording would itself have
      contained the literal substring the test forbids), just points at the session-vars block already present. STEP 3
      is unchanged (the existing one-shot `/done` line was already correct). Added 5 tests to `tests/test_prompts.py`: a
      parametrized test asserting no `/boot` substring for all 3 roles + STEP 2/3 shape, a STEP 0/1-unchanged check, and
      a regression guard that regular slot workers still get told to `/boot`. Full `quality-gates.sh` green (1647 tests,
      ruff + basedpyright clean). (repo: agent-orchestrator)
