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
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [backlog, regen, verification, done-gate, cross-repo, false-negative]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/archive/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md,
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

- [x] ✅ [SCRIPT] P2. **DONE 2026-07-27 (slot-11) — agent-orchestrator@5623ee6.** **Root-caused
      `regen_backlog_from_plan.py`'s brief-extraction — the suspected "nearby/pattern-based text grab" is REFUTED.**
      `_parse_open_todos` (`server/regen_backlog_from_plan.py:990`) matches `_UNCHECKED_RE` against ONE `raw_line` at a
      time and sets `description = m.group(1)` from THAT line's own capture only — it cannot cross into a neighbouring
      bullet's text, by construction. Proved this against the REAL repro text from `unified-trading-pm@35591f5c3` (the
      commit that produced -012's wrong brief): two new tests,
      `test_parse_adjacent_same_opening_phrase_todos_anchor_to_     own_line` (direct `_parse_open_todos` check) and
      `test_regen_adjacent_same_collision_group_todos_get_distinct_     briefs` (end-to-end `regen()` check, both todos
      auto-deriving the identical `script:partitioned_writer.py` collision_group), both PASS today — each todo's brief
      is correctly anchored to its own line. **The actual mechanism is a different, already-tracked bug class**: task
      ids are derived POSITIONALLY (`_make_task_id`/`next_index = max(used)+1`), not from content — fully documented in
      `regen_positional_task_ids_not_content_stable_2026_07_17.md`. Commit 35591f5c3 reworded BOTH adjacent todos'
      opening lines in one edit (prepending the Conflict-check sentence), which orphans the OLD single-line brief for
      each (the hard-wrap boundary shifted — the same "reworded todo = fresh id" A2 design already documented in
      `_migrate_parking_state`'s docstring) and mints fresh tasks for the post-edit text. If a freed positional id later
      gets reused for a DIFFERENT todo while a WORKER is still `dispatched` under it (id-slot reuse,
      `backlog_regen_id_reuse_stale_status_2026_07_15`), `sync_backlog_to_db` (`server/bootstrap.py:354-374`) silently
      resets `status`→`queued` and overwrites `brief_hash` to the NEW content on brief-hash mismatch — this reset guard
      protects `done` rows (refuses to reset, per `ao_backlog_regen_integrity_2026_07_20.md` todo 1, confirmed live by
      `test_sync_refuses_to_reset_a_done_row_on_id_reuse`) but has **NO equivalent protection for a `dispatched` row**
      (confirmed live by the EXISTING `test_sync_resets_terminal_fields_when_id_reused_for_different_checkbox`, which
      asserts the reset DOES fire for `status="dispatched"`) and sends **no notification to the in-flight worker** (no
      `cancel_task` signal, unlike the operator-removal path in `_prune_stale`'s dispatched-orphan-cancel logic). A
      worker (slot-5) dispatched under the OLD, correct understanding of its own todo keeps working — legitimately — and
      only discovers the mismatch at `/done` time, when the live stored `brief` has already been silently repointed to a
      different todo. This is a genuinely NEW gap beyond what
      `regen_positional_task_ids_not_content_stable_2026_07_17.md` already covers (that doc's guard analysis was scoped
      to `done`-row sibling-reset destroying audit history, not the `dispatched`-row
      silent-reset-with-no-worker-notification case) — added as a new todo there rather than re-implemented here, since
      that doc is the correct SSOT home for this bug class and any fix (guard the dispatched row too, or emit
      `cancel_task`) is a runtime-dispatch-safety change deserving its own scoped review, not a same-commit addendum to
      this root-cause todo. Tests: `agent-orchestrator/tests/test_regen_backlog_from_plan.py` (2 new, both green); full
      `quality-gates.sh` pending. Repo: agent-orchestrator.
- [x] ✅ [SCRIPT] P2. **DONE 2026-07-28 (slot-14) — agent-orchestrator@09cda29.** **Shipped option (b): a
      `POST /api/backlog/{task_id}/reconcile-brief` admin endpoint** (`server/routes/backlog.py`) for main/operator to
      correct a provably-wrong stored `brief` in place, once evidence like this doc is filed. Refuses (400) unless
      `new_brief` matches, verbatim, a currently-existing `- [ ]` OR `- [x]` line in the task's resolved `plan_ref` file
      on this host's PM checkout — never a free-form claim (two new helpers in `server/verify.py`:
      `_brief_is_currently_unchecked` sibling of the existing `_brief_is_currently_checked`, both tried in turn so the
      correction is accepted whether the true todo is still open or already shipped-under-the-correct-text, the exact
      scenario `cefi_satellite_ao_dispatch_batch1-012` — todo 3 below — hit). Updates BOTH surfaces in one transaction:
      `backlog.yaml`'s `brief` (the only place the literal text lives — `TaskRow` has no `brief` column) AND
      `TaskRow.brief_hash`, so the next `sync_backlog_to_db` tick sees the hash already matching and does NOT trip the
      sibling-reset guard (`server/bootstrap.py`) — never touches `status`/`done_sha`, so it's safe to call while a task
      is still `dispatched` to a live worker. New request model `ReconcileBriefRequest` (`server/models/worker_api.py`).
      Tests: `agent-orchestrator/tests/test_backlog_reconcile_brief.py` (8 new, covering both matched-state branches,
      the 400 unverified-claim refusal, both 404s, the `plans/active/issues/` stale-plan_ref fallback, activity-event
      logging, and dispatched-row safety); full `quality-gates.sh` green (1821 passed, basedpyright/ruff/dashboard
      clean). Repo: agent-orchestrator.
- [ ] [SCRIPT] P1. **Retagged from `[OPERATOR]` (2026-07-28 gate-cleanup pass)** — the todo's own stated unblocking
      condition (the `/api/backlog/<id>/reconcile-brief` endpoint existing) is now met: it shipped in the second todo
      above (`agent-orchestrator@09cda29`), which is exactly the "normal, audit-logged, non-operator action" path this
      todo said to wait for — no more raw out-of-band SQL write needed, so the `ao_backlog_done_row_disappearance` noise
      concern this todo was held on no longer applies. **Manually resolve `cefi_satellite_ao_dispatch_batch1-012`'s
      dispatched-but-undone state** — the work is genuinely complete and verified (market-tick-data-service@94b4aff5,
      unified-trading-pm@dadf5db6e). Call `POST /api/backlog/cefi_satellite_ao_dispatch_batch1-012/reconcile-brief` with
      `new_brief` set to the currently-checked todo text this task actually corresponds to —
      `cefi_satellite_ao_dispatch_batch1_2026_07_25.md`'s "DONE 2026-07-27 (slot-5) — market-tick-data-service@94b4aff5.
      Widened `_update_cluster_and_chain_counts`…" line (originally cited at `:386`, now at `:411` after subsequent plan
      edits — resolve the CURRENT line number at execution time, don't assume either cited number) — then confirm the
      task's stored `brief`/`brief_hash` now match and the row's `dispatched`-but-undone state is resolved. Filed as
      `/blocked` question `BLK-35875b16` with the same evidence; that question can now be closed citing this resolution
      path instead of left open.

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
