---
doc_type: issue
title:
  Backlog `brief` cross-wired between adjacent same-collision-group todos — blocks /done's cross-repo checkbox-flip
  verification
summary: >-
  Task `cefi_satellite_ao_dispatch_batch1-012`'s stored `brief` (the exact text `regen_backlog_from_plan.py` uses for
  the cross-repo `/done` diff-verification match) is the opening text of a DIFFERENT, adjacent todo in the same plan
  (both share `collision_group: script:partitioned_writer.py`), not the todo this task's own
  `plan_ref`/`done_definition` actually points to. This made a genuine, fully-shipped completion
  (market-tick-data-service@94b4aff5, plan checkbox correctly flipped at unified-trading-pm@dadf5db6e) hard-reject at
  `/done` with `reason: cross_repo_pm_file_touched_no_checkbox_flip`, since the verifier's exact-text diff match
  (`_diff_flips_checkbox`) can never succeed against a brief belonging to a different line, and the fallback
  (`_brief_is_currently_checked`) also can't succeed since that OTHER todo is genuinely still open (real, separate, much
  larger unshipped work — must not be marked done to route around this).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [backlog, regen, verification, done-gate, cross-repo, false-negative]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P2
source: "slot-5, discovered while calling /done for cefi_satellite_ao_dispatch_batch1-012, 2026-07-27"
resolved_by:
locked_by:
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# Backlog `brief` cross-wired between adjacent same-collision-group todos

## What I found

`GET /api/backlog` for task `cefi_satellite_ao_dispatch_batch1-012` returns:

```json
{
  "id": "cefi_satellite_ao_dispatch_batch1-012",
  "collision_group": "script:partitioned_writer.py",
  "plan_ref": "plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md",
  "brief": "[DATA] P1. **Conflict-check (2026-07-25 plan-reconcile): shares `partitioned_writer.py`'s `write_chunk`→",
  "done_definition": "Checkbox flipped in plan + code shipped."
}
```

That `brief` string is the **literal opening text of a different todo** —
`plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md:386` (the "Conflict-check ... v6-canonicalisation-proof"
todo, a separate GCS-migration-heavy piece of work: prove the W1 v6 fix end-to-end, enumerate + migrate real v5 cefi
chain objects, record the cutover in `canonical-cutover-register.md`). It is NOT the text of the todo my task's
`plan_ref`/`done_definition` actually resolved to, which was the ADJACENT todo just below it (line ~407 pre-edit):
"Conflict-check (2026-07-25 plan-reconcile): shares the same `partitioned_writer.py` call chain as the P1
v6-canonicalisation-proof todo above — run this one FIRST, then the P1 proof, never concurrently.\*\* **Widen the cefi
chain-tail cluster-counts bookkeeping key to include quote/margin.**"

Both todos:

- Share `collision_group: script:partitioned_writer.py` (both touch `partitioned_writer.py`).
- Are adjacent in the plan (todo A ends at line 388, todo B — mine — starts at line 389/407 depending on concurrent
  edits during the session).
- Both open with the phrase "**Conflict-check (2026-07-25 plan-reconcile): shares ...**" (a plan-reconcile convention
  for flagging same-file-collision todos), which is very likely what confused whatever text-extraction step in
  `regen_backlog_from_plan.py` assigns `brief` — probably a regex/heading match that grabbed the FIRST occurrence of
  that phrase pattern in the vicinity rather than the one anchored to this specific todo's own checkbox line.

## Why it matters

`/done`'s cross-repo verification (`server/verify.py::_diff_flips_checkbox` / `_brief_is_currently_checked`) requires an
**exact literal match** between the stored `brief` and either (a) a removed `- [ ] <brief>` / added `- [x] ...` pair in
a recent PM-worktree commit, or (b) a currently-existing `- [x] <brief>` line. When `brief` belongs to a DIFFERENT todo:

1. (a) can never succeed — my commit correctly flips MY todo's checkbox, but that diff's removed line will never
   textually equal the OTHER todo's brief.
2. (b) can also never succeed **safely** — the only way to satisfy it would be to mark the OTHER (genuinely unfinished,
   much larger) todo as `[x]` too, which would be a **false-progress lie**, not a workaround.

Net effect: a fully legitimate, shipped, plan-flipped completion is **permanently unable to pass `/done`** through any
means available to the dispatched worker — not a transient race, not fixable by retrying, not fixable by re-wording the
worker's own flip (since the mismatch is in the STORED brief, not the worker's diff). This is worse than the already-
tracked `backlog_task_done_status_diverges_from_plan_checkbox_2026_07_16.md` class (that one was about a **stale** brief
after the plan changed later; this is a **wrong-todo** brief from the moment the row was generated, not staleness over
time) — it will recur for any other collision-group-mate pair phrased with a shared leading convention.

## Recommended decision

- [ ] [SCRIPT] P2. **Root-cause `regen_backlog_from_plan.py`'s brief-extraction for todos in the same
      `collision_group`/adjacent-in-plan family** — confirm whether the extraction anchors on the todo's OWN checkbox
      line position (correct) or does a nearby/pattern-based text grab that can cross adjacent todos sharing an opening
      phrase convention (the suspected bug here). Add a regression test: two adjacent todos, same `collision_group`,
      both opening with an identical "Conflict-check (...): shares ..." phrase — assert each generated task's `brief` is
      anchored to ITS OWN checkbox line, not the sibling's. Repo: agent-orchestrator.
- [ ] [SCRIPT] P2. **Add an escape hatch to `/done`'s cross-repo verification for this exact failure mode** — when
      neither `_diff_flips_checkbox` nor `_brief_is_currently_checked` can match (a real backlog-brief bug, not a
      missing flip), the worker currently has NO path to complete other than a human manually reconciling the DB row.
      Consider: (a) a `/done` field letting a worker cite the ACTUAL checkbox line text it flipped (verified against the
      plan_ref file directly, independent of the stored `brief`) as an alternate proof, gated so it still requires a
      genuine `- [ ]`→`- [x]` diff to exist somewhere in the file (not a free-form claim); or (b) a
      `/api/backlog/<id>/reconcile-brief` admin endpoint for main/operator to correct a provably-wrong stored brief
      in-place once evidence like this doc is filed. Repo: agent-orchestrator.
- [ ] [OPERATOR] P1. **Manually resolve `cefi_satellite_ao_dispatch_batch1-012`'s dispatched-but-undone state** — the
      work is genuinely complete and verified (market-tick-data-service@94b4aff5, unified-trading-pm@dadf5db6e). Filed
      as `/blocked` question `BLK-35875b16` with the same evidence; this todo exists so the fix is tracked even if the
      blocked question is answered out-of-band. **Kept operator-gated on re-triage 2026-07-27**: even though the
      evidence for THIS row is airtight, the only available fix today is a raw, out-of-band SQL write against the live
      `state.db` (no `/api/backlog/<id>/reconcile-brief` endpoint exists yet — that's the second todo above, unshipped).
      `ao_backlog_done_row_disappearance_2026_07_25.md` is an OPEN, unexplained investigation into exactly this class of
      out-of-band write silently corrupting `done`-row audit history on this same DB — adding another untracked manual
      UPDATE right now would add noise to that investigation's evidence trail, not just fix one row. Land the
      reconcile-brief endpoint (or resolve the other investigation) first, then this becomes a normal, audit-logged,
      non-operator action.

## Evidence

- Task record: `GET /api/backlog` → id=`cefi_satellite_ao_dispatch_batch1-012`, `brief` ends `→` (literal arrow, not a
  display truncation — confirmed via the raw JSON API response, not a client-side render).
- Sibling todo owning that brief text: `plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md:386`, still `- [ ]`
  (genuinely unfinished) at time of filing.
- My actual flip: `unified-trading-pm@dadf5db6e`, diff shows
  `- [ ] [DATA] P1. **Conflict-check (2026-07-25 plan-reconcile): shares the same \`partitioned_writer.py\` call chain
  as the`removed and`+ - [x] ✅ [DATA] P1. **DONE 2026-07-27 (slot-5) — market-tick-data-service@94b4aff5.** Widened`
  added — a real, unambiguous flip of the CORRECT todo.
- Code evidence: `market-tick-data-service@94b4aff5` — 6978 unit tests green, full `quality-gates.sh` green
  (sentinel-verified), shipped via quickmerge.
