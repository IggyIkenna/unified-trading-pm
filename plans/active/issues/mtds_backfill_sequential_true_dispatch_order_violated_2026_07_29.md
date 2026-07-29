---
doc_type: issue
title:
  "`sequential: true` plan still dispatched a downstream todo ahead of its still-queued predecessor —
  mtds_available_at_cross_asset_backfill's prediction-lane apply/resume pair"
summary: >-
  mtds_available_at_cross_asset_backfill_2026_07_13.md carries `sequential: true` (added 2026-07-14 specifically to fix
  the identical class of bug — see the plan's own "Dispatch-order finding" Progress Log entry and
  issues/dispatch_sequential_gate_fix_2026_07_24.md). Despite that, slot 14 was dispatched
  mtds_available_at_cross_asset_backfill-006 ("Resume the prediction consolidator cron") on 2026-07-29 while
  mtds_available_at_cross_asset_backfill-001 ("Apply rebuild_prediction_manifest.py" — the checkbox immediately BEFORE
  it in the plan, and its direct logical prerequisite: nothing to resume the cron FOR until the backfill is applied) was
  still `status: queued`, never dispatched to anyone, confirmed live via `GET /api/backlog`. This is a live recurrence
  of the exact failure mode the 2026-07-14 fix + the 2026-07-24 pin/fan-out fix were both meant to close, but neither
  fully closes it — `sequential: true` is present and the plan is not fanning out (matching the 2026-07-24 fix's own
  intent), yet the intra-plan ORDER guarantee (`_wire_sequential_prereqs`, referenced but not verified in
  dispatch_sequential_gate_fix_2026_07_24.md's Lessons section) did not hold for this specific pair.
status: open
nature: issue
asset_group: [ao, tradfi]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, dispatch, sequential, prereqs, backlog-regen, dispatch-order]
related:
  [
    /plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md,
    /plans/active/issues/dispatch_sequential_gate_fix_2026_07_24.md,
  ]
created: 2026-07-29
priority: P1
parent_epic: orchestrator_master
source: ["mtds_available_at_cross_asset_backfill-006, slot 14, 2026-07-29"]
assigned_vm: NA
execution_scope: local-only
estimate_class: research
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
---

# `sequential: true` did not gate dispatch order for a queued predecessor

## What I found

Dispatched `mtds_available_at_cross_asset_backfill-006` ("**No longer gated on an operator decision (retagged
2026-07-28, same ruling)** — Resume the prediction consolidator cron; record the before/after fill-rate evidence in this
plan's Progress Log", `plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md:162`).

Checked the plan's frontmatter: `sequential: true` (confirmed present — added 2026-07-14 per this same plan's own
Progress Log "Dispatch-order finding" entry, specifically to prevent this exact class of bug: a downstream todo
dispatched ahead of its undone prerequisite).

Checked the live backlog (`GET /api/backlog`, filtered to this plan's task ids):

```
mtds_available_at_cross_asset_backfill-001 | queued     | priority 20 | "Apply rebuild_prediction_manifest.py..." (line 157)
mtds_available_at_cross_asset_backfill-006 | dispatched | priority 20 | "Resume the prediction consolidator cron..." (line 162, dispatched to slot 14)
mtds_available_at_cross_asset_backfill-003 | queued     | priority 20 | tradfi-lane "Resume..." (line 289)
```

`-001` is the checkbox immediately BEFORE `-006` in the plan (line 157 vs 162), same priority (20), same asset_group
lane (prediction), and is `-006`'s direct logical prerequisite — the plan's own todo text for `-006` says "record the
before/after fill-rate evidence," which requires the apply (`-001`) to have already run. `-001` was never dispatched to
any slot (plain `queued`, not `done`, not `dispatched`) at the moment `-006` was handed to me.

This reproduces the exact failure this plan's `sequential: true` was added to prevent (see
`plans/active/mtds_available_at_cross_asset_backfill_2026_07_13.md`'s own "Dispatch-order finding — 2026-07-14 (slot 5)"
Progress Log entry) — but `sequential: true` IS present in the frontmatter this time, so the fix that closed the
2026-07-14 instance is not (or no longer) sufficient on its own.

**Not yet root-caused in agent-orchestrator code** — I did not read `server/regen_backlog_from_plan.py`'s
`_wire_sequential_prereqs` (referenced in `issues/dispatch_sequential_gate_fix_2026_07_24.md`'s Lessons section:
"Ordering for a sequential plan is still enforced independently by prereqs (`_wire_sequential_prereqs`)") — that's
agent-orchestrator backend code, outside data_engineering craft scope. Candidate hypotheses for whoever picks this up
(backend_engineer craft), none verified:

1. `_wire_sequential_prereqs` may only chain CONSECUTIVE derived-task ordinals, and this plan's task numbering has
   drifted from document order after many completed/orphaned checkboxes over its life (`-002` is already `done`+orphan,
   the ids don't currently read as a clean 1..N walk of open checkboxes) — if the prereq wiring keys off stale ordinals
   rather than re-deriving the live document-order chain on every regen, a renumbering could desync predecessor→
   successor links.
2. The prediction lane and tradfi lane are interleaved in one file (prediction todos at lines 135-164, tradfi at
   165-290) — if `_wire_sequential_prereqs` treats the WHOLE plan as one chain rather than respecting a natural
   same-asset-group sub-sequence, an off-by-one or lane-crossing bug in the chain-walk is plausible.
3. Simpler possibility: the prereq wiring works, but the specific `-001`→`-006` edge wasn't (re-)established on the
   regen tick that actually dispatched `-006` — worth checking whether prereqs get RE-derived on every regen or only at
   plan-creation time (a staleness bug, not a logic bug).

## Why it matters

Same class as `dispatch_sequential_gate_fix_2026_07_24.md` and
`blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md` — a worker acting on a wrongly-ordered
dispatch could resume a paused prod consolidator cron before its backfill actually landed, defeating the whole point of
the pause/apply/resume sequence this plan exists to execute safely (the sports CF-8 regression precedent this plan
explicitly designed around). I declined to execute `-006` as dispatched (nothing to resume — the backfill apply hasn't
run) rather than doing the wrong-order work; documented in the plan's own Progress Log per the 2026-07-14 precedent.

## Recommended decision

A `backend_engineer`-craft worker (agent-orchestrator repo) should read `_wire_sequential_prereqs` in
`server/regen_backlog_from_plan.py` directly, reproduce against this specific plan's current task rows, and determine
which of the 3 hypotheses above (or another) is the actual cause — then fix + add a regression test asserting a
`sequential: true` plan never offers a later-in-document unchecked todo while an earlier one is still `queued` (not
`done`). This is a judgment/investigation call (root-causing unfamiliar dispatch logic), not a mechanically bounded fix
— hence `assigned_vm: NA` pending that investigation; convert to an AO-dispatchable todo once the fix shape is known.

## Todos

- [ ] [BACKEND] P1. Root-cause why `_wire_sequential_prereqs` (or whichever mechanism gates sequential-plan dispatch
      order) did not block `mtds_available_at_cross_asset_backfill-006` while `-001` was still `queued`. Test one of the
      3 hypotheses above (or find the real cause), fix it in `agent-orchestrator/server/regen_backlog_from_plan.py`, and
      add a regression test. **Done when**: `quality-gates.sh` green + the new test fails on the pre-fix code and passes
      post-fix. (repo: agent-orchestrator)
- [ ] [VERIFY] P2. After the fix above ships + deploys to the live orchestrator VM, re-check this plan's live backlog
      (`GET /api/backlog`) and confirm `-001` (or whatever id the "Apply rebuild_prediction_manifest.py" todo has by
      then) is `dispatched`/`done` before its downstream "Resume cron" sibling ever leaves `queued`. (repo:
      agent-orchestrator)

## Progress Log

- 2026-07-29 (slot 14, data_engineering): found + filed. Declined to execute `-006` as dispatched (documented in the
  parent plan's own Progress Log). Not yet root-caused in AO code — out of data_engineering craft scope; needs a
  backend_engineer pass per the Recommended decision above.
- **na-eligibility-audit 2026-07-29**: KEEP_NA_VALID. Both open todos are genuinely NA-appropriate: todo 1 [BACKEND] is
  an open-ended root-cause investigation into a live dispatch-order bug in `agent-orchestrator`'s
  `_wire_sequential_prereqs`, with 3 unverified hypotheses and the doc's own text stating this is a
  judgment/investigation call, not a mechanical fix; todo 2 is a verify step gated on todo 1's fix landing. Correctly
  stays NA.
