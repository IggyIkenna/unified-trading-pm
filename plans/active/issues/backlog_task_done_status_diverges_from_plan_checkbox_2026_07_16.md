---
doc_type: issue
title: >-
  agent-orchestrator backlog marks tasks `status=done` with a `done_sha` that traces to a "declining/no-action" commit,
  while the source plan's checkbox stays `[ ]` — now actively feeding `gate_on_depends`, which trusts backlog `done`
  over the plan
summary: >
  While working `sports_travel_calculator_tz_aware_kickoff_crash-001` (Todo 2, gated via `depends_on` +
  `gate_on_depends=true` on `sports_p2_features_history_to_ml_ready_2026_06_27.md`), found the live orchestrator
  (restarted `2026-07-16T18:21:11Z`, confirming `agent-orchestrator@2d6365f`'s `.md`-suffix fix is now finally in
  effect) dispatched my task with `dispatch_reason="... prereqs met ..."`. Its `prereqs.completed_tasks`
  (`sports_p2_features_history_to_ml_ready-001`, `-002`) both read `status=done` via `GET /api/backlog` — with
  `done_sha=094756d64` and `done_sha=0402f7a86` respectively. Both SHAs resolve to real commits on `unified-trading-pm`,
  but neither is a completion commit for the task it's cited on: `094756d64` = "sports P2c Todo 1 re-verify — both
  tracked VMs healthy and progressing ... no new action needed (slot-11)"; `0402f7a86` = "sports P2c Todo 3 re-verify —
  still BLOCKED-PREREQ ... (slot-8)". Both are routine "declining, no code touched, checkbox NOT flipped"
  `/skip-current-task` Progress Log commits — the exact opposite of a completion. Confirmed against the actual plan:
  after a clean fresh-pull to LDR HEAD `9d39ed2835ae` (2026-07-16T18:21:16Z),
  `sports_p2_features_history_to_ml_ready_2026_06_27.md` line 101 ("Compute features 2015→present", the task -001 maps
  to) and line 109 ("Features manifest clean over history", the task -002 maps to) are BOTH still `- [ ]` — unflipped.
  This exact plan has an unusually long, well-documented Progress Log (36 consecutive dispatches of the gated child
  task, every single one independently re-verifying Todo 1 as `[ ]` via direct grep) — so this is not a one-off misread,
  it's a confirmed, sustained ground truth that contradicts the backlog's `status=done`.
status: open
nature: notes
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [orchestrator, backlog, regen_backlog_from_plan, gate_on_depends, data-integrity, ssot-contradiction, plan-checkbox]
related:
  [
    plans/active/issues/sports_travel_calculator_tz_aware_kickoff_crash_2026_07_14.md,
    plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md,
    codex/11-project-management/,
  ]
created: 2026-07-16
parent_epic: agent_operating_framework_master
priority: P1
source:
  sports_travel_calculator_tz_aware_kickoff_crash-001 dispatch, slot 13, 2026-07-16 (Todo 2 re-check, 36th consecutive
  dispatch)
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
last_updated: 2026-07-16
locked_by:
resolved_by:
depends_on: []
---

# Backlog `status: done` diverges from the plan checkbox it's derived from

## What I found

`GET /api/backlog` (live orchestrator, restarted `2026-07-16T18:21:11Z`) for the two tasks gating
`sports_travel_calculator_tz_aware_kickoff_crash-001` (Todo 2):

```json
{"id": "sports_p2_features_history_to_ml_ready-001", "status": "done", "done_sha": "094756d64", ...}
{"id": "sports_p2_features_history_to_ml_ready-002", "status": "done", "done_sha": "0402f7a86", ...}
```

Both SHAs are real, resolvable commits on `unified-trading-pm` — but neither is a completion of the task it's attached
to:

- `094756d64` — `git show --stat`: "sports P2c Todo 1 re-verify — both tracked VMs healthy and progressing, known
  consolidator-staleness self-recovering, no new action needed (slot-11)". This is a Progress Log entry commit from a
  slot that explicitly declined the work and did NOT flip any checkbox (matches the "declining ... checkbox NOT flipped
  ... `/skip-current-task`" pattern used ~30 times in this exact saga).
- `0402f7a86` — "sports P2c Todo 3 re-verify — still BLOCKED-PREREQ, both tracked VMs healthy (slot-8)". Same pattern —
  a decline commit for a DIFFERENT todo (Todo 3), not task -002 ("Features manifest clean over history").

Ground truth check (fresh-pull to LDR HEAD `9d39ed2835ae`, 2026-07-16T18:21:16Z):

```
$ grep -n "^- \[" plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md
101:- [ ] [DATA] P0. **Compute features 2015→present** ...          <- task -001's source todo
109:- [ ] [DATA] P1. **Features manifest clean over history** ...    <- task -002's source todo
```

Both still `[ ]`. This plan's own Progress Log independently re-verified Todo 1 as `[ ]` at least 30 times across
2026-07-14 through 2026-07-16 (most recently ~14:3xZ today, ~4h before this check) — real coverage percentages tracked
each time (59.8% → 68.6% → ... , never reaching completion). So this is not a stale single read; it's a sustained,
repeatedly-reconfirmed contradiction between the backlog DB's `status: done` and the plan file's actual checkbox state,
which `codex/`/CLAUDE.md declare the SSOT (`done_definition: Checkbox flipped in plan + code shipped` on every task).

## Why it matters

This was previously invisible/inert because `gate_on_depends` never wired for `.md`-suffixed `depends_on` entries (the
bug `agent-orchestrator@2d6365f` fixed, per this issue doc's own — a sibling doc's — Progress Log, slot-12
2026-07-15T12:3xZ) **and** the live process hadn't been restarted to pick up that fix (confirmed unchanged
`server_started: 2026-07-15T07:30:19Z` on ~15 consecutive checks through 2026-07-16T14:3xZ). Now that the restart has
finally landed (`2026-07-16T18:21:11Z`), `gate_on_depends` is live — and it just handed out a dispatch
(`sports_travel_calculator_tz_aware_kickoff_crash-001` to slot 13) whose `dispatch_reason` says "prereqs met", when the
actual upstream work is NOT met by the plan's own ground truth. In other words: the exact mechanism that was fought for
across ~36 dispatches and a multi-day operator escalation to correctly gate premature dispatch is now active, but is
trusting a `done` status that itself appears to be wrong — so the fix doesn't yet deliver the safety it was built for.

If this "`status: done` without a matching plan checkbox flip" pattern is not unique to these 2 tasks, any other
`gate_on_depends`/`prereqs.completed_tasks`-gated task in the fleet could be dispatching on the same false-positive
basis — a correctness regression hiding behind what looks like the fix finally working.

## Recommended decision

Root-cause is not yet established from this task's scope (data_engineering / sports craft) — plausible candidates, in
rough order of likelihood: (a) a slot called `/done` for `-001`/`-002` citing a fresh-pull HEAD SHA as "evidence"
without actually completing/flipping the source todo (a `slot_done_no_plan_flip` warning-only violation that was never
remediated); (b) task-ID reuse/collision across a plan regen — the same numeric slot (`-001`, `-002`) getting reassigned
to a different semantic todo than an earlier `/done` was legitimately called against, while the DB's `status: done`
carried forward against the new identity; (c) a manual/erroneous DB write. Recommend an `infra`-role investigation into
`server/regen_backlog_from_plan.py` + the `/done` handler to determine which, then either (i) add a `/done`-time hard
check that a path-shaped `plan_ref` task's cited commit actually touches + flips the plan checkbox before accepting
`status: done` (upgrading the existing `no_plan_flip` warning to a blocking check for `gate_on_depends`-relevant tasks
specifically), or (ii) a one-off audit sweep cross-checking every `status: done` backlog task with a `plan_ref` against
that plan's live checkbox state and reopening any mismatches.

## Todos

- [ ] [INFRA] P1. **Root-cause how `sports_p2_features_history_to_ml_ready-001`/`-002` got `status: done`** in the live
      backlog DB while their source plan checkboxes (`plans/active/sports_p2_features_history_to_ml_ready_2026_06_27.md`
      lines 101, 109) remain `[ ]`. Check `/done` call history / activity feed around the `done_sha` commit timestamps
      (`094756d64` ~2026-07-15T10:11:59Z, `0402f7a86` ~2026-07-15T09:5xZ) for which slot called `/done` and with what
      evidence. (repo: agent-orchestrator)
- [ ] [INFRA] P1. **Add a consistency check** (either at `/done`-accept time for `gate_on_depends`-relevant tasks, or a
      standalone audit script) that flags/reopens a backlog task marked `status: done` when its `plan_ref`'s
      corresponding checkbox is not actually `[x]` — this is the specific gap that let a false-positive prereq feed
      `gate_on_depends`. (repo: agent-orchestrator)
- [ ] [DATA] P2. **Once the above is root-caused and corrected**, re-verify whether
      `sports_p2_features_history_to_ml_ready-001` (Todo 1, "Compute features 2015→present") is actually complete before
      trusting any future `gate_on_depends` dispatch of `sports_travel_calculator_tz_aware_kickoff_crash-001` Todo 2 —
      as of this doc's creation it is still genuinely in-progress per the plan's own Progress Log (~68%+ coverage, not
      100%). (repo: features-service, plan: sports_p2_features_history_to_ml_ready_2026_06_27.md)

## Progress Log

### 2026-07-16T18:2xZ UTC — data_engineering slot-13 (finding filed)

Discovered while working `sports_travel_calculator_tz_aware_kickoff_crash-001` Todo 2 (36th consecutive dispatch of that
task). Filed this issue doc per findings-triage HARD RULE (SSOT contradiction / big finding). No code changed by this
doc. See the sibling issue doc's Progress Log for the corresponding Todo 2 decline entry.
