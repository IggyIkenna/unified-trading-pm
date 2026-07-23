---
doc_type: issue
title:
  "gate_on_depends silently no-ops when the upstream `depends_on` plan is `local-only`/`NA` (never ingested) — root
  cause of the recurring manifest_v6_batch3 re-dispatch"
summary: >-
  `manifest_v6_batch3_residual_orphaned_work_2026_07_21.md`'s API/UI todos have been dispatched to 4 workers now (this
  session included) despite `gate_on_depends: true` and `depends_on:
  [cefi_chain_tail_v6_canonicalisation_2026_07_21.md]` — each time correctly finding the upstream still has open todos
  and declining to implement, then escalating via /blocked without diagnosing WHY the gate isn't holding. Traced the
  actual root cause in agent-orchestrator's regen_backlog_from_plan.py + dispatch.py: the upstream plan is
  `execution_scope: local-only` / `assigned_vm: NA`, which means it is NEVER INGESTED into the backlog at all — it
  produces zero BacklogTask rows. gate_on_depends wires prereqs by looking up the upstream plan's OWN backlog task ids;
  when that list is empty, `_wire_gate_on_depends_prereqs` treats it as "nothing to gate on" and skips wiring entirely
  (fail-open), because the exact same empty-list signature is also what a genuinely-finished, fully-pruned upstream plan
  produces — the two cases are indistinguishable at that data layer. Filing as its own
  backend_engineer/agent-orchestrator task rather than fixing it live mid-session, since a dispatch-logic change has
  fleet-wide blast radius and deserves its own reviewed, tested change.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, dispatch-logic, gate_on_depends, plan-discipline, root-cause, recurring-bug]
related:
  [
    plans/active/issues/manifest_v6_batch3_residual_orphaned_work_2026_07_21.md,
    plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md,
  ]
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
drift_direction: advance-code
source: [manifest_v6_batch3_residual_orphaned_work-002]
resolved_by: agent-orchestrator@7b3f909
locked_by:
depends_on: []
---

# What I found

`manifest_v6_batch3_residual_orphaned_work_2026_07_21.md`'s todo 2 (deployment-api `quote_asset`/`margin_type` API
field) and todo 3 (deployment-ui heatmap filter) both carry
`depends_on: [plans/active/issues/cefi_chain_tail_v6_canonicalisation_2026_07_21.md]` + `gate_on_depends: true`, added
specifically because the doc's own history shows the gate being ADDED after a first mis-dispatch, then the SAME todo
re-dispatching TWICE more afterward (slot-7, then slot-2) — each worker correctly re-verified the upstream is still open
and declined to implement, but neither diagnosed why the machine gate itself wasn't holding. I was dispatched this same
todo a fourth time this session; before repeating the same "confirm blocked, /blocked again" cycle, I traced the actual
dispatcher code.

**Root cause** (`agent-orchestrator/server/regen_backlog_from_plan.py`):

1. `_wire_gate_on_depends_prereqs` (line ~1522) builds `file_to_ids: dict[str, list[str]]` — a map from
   upstream-plan-stem → the list of that plan's OWN backlog task ids — by scanning `backlog.tasks`.
2. For each gated downstream plan, it looks up `upstream_ids = file_to_ids.get(dep, [])` for every `depends_on` entry.
   **If `upstream_ids` ends up empty, line ~1549 `if not upstream_ids: continue` skips wiring ANY prereq for that
   downstream plan** — i.e., the gate becomes a complete no-op.
3. The upstream plan here, `cefi_chain_tail_v6_canonicalisation_2026_07_21.md`, is tagged
   `execution_scope: local-only` + `assigned_vm: NA`. Per this same file's own `_parse_frontmatter_execution_scope`
   docstring (line ~556): `local-only` is "the signal for the ingester to skip the plan [ingestion] entirely." So this
   upstream plan **produces ZERO backlog tasks, ever** — not because it's done, but because it was never a dispatch
   target in the first place (it's a human/operator-tracked issue doc with real open `- [ ]` todos 5-8, confirmed still
   unchecked as of this session).
4. `file_to_ids.get(dep, [])` for a never-ingested plan is indistinguishable from a **fully-completed-and-pruned** plan
   (same empty-list signature) — and the empty-list-means-"nothing to gate" behavior was DELIBERATELY added to fix a
   real prior bug: `dispatch.py`'s `_completed_task_satisfied` (line ~636) treats "absent from both the DB and backlog"
   as SATISFIED specifically so a genuinely-finished upstream plan (whose task ids naturally disappear once done+pruned)
   doesn't deadlock its downstream forever (the 2026-06-29 whole-fleet-idle-block fix, per that function's own
   docstring). That fix is correct for its target case but has the side effect of also silently defeating
   `gate_on_depends` for this different case: an upstream that was **never ingested at all** because it's tagged
   local-only/NA, yet still has real, unfinished, human-tracked work.
5. **A synthetic/fake prereq id does not work as a fix** — I checked: `_completed_task_satisfied` treats ANY id absent
   from both DB and backlog as satisfied, by design (that's the exact mechanism at fault), so inventing a never-real
   `completed_tasks` id to force a block would immediately read as satisfied too, same bug.

# Why it matters

This is a genuine, fleet-wide dispatch correctness gap, not a one-off mis-scoped plan: **`gate_on_depends` cannot
currently express "block on a `local-only`/`NA` upstream plan that still has open work"** — which is a very plausible
and likely-common pattern (an investigation/audit issue doc is frequently `assigned_vm: NA` / `local-only` while still
gating real follow-on code work). Each silent re-dispatch here cost a full worker cycle (boot, fresh-pull, read the
plan, re-verify the same still-open dependency, escalate) — 3 times before this session, a 4th time now. The fix belongs
in `agent-orchestrator` itself (this repo is explicitly in the `backend_engineer` role's scope), but a dispatch-logic
change affects every plan on the fleet using `gate_on_depends`, so it needs its own reviewed change with new unit tests
(mirroring `tests/test_dispatch_completed_prereqs.py`) — not a live patch squeezed into an unrelated P3 feature task.

# Recommended decision

Fix `_wire_gate_on_depends_prereqs` (or the layer that consumes it) to distinguish "upstream never ingested but still
open" from "upstream ingested and now fully done+pruned":

- When `upstream_ids` is empty for a `dep`, don't immediately treat it as satisfied. Instead check the upstream plan
  file directly via the existing `_parse_open_todos(pm_path / dep)` helper (already used elsewhere in this same module
  for exactly "does this plan file still have live checkboxes"): if it returns any open todos, the gate must still hold;
  if it returns none, treat as done (matches today's behavior for the completed-and-pruned case).
- Because `completed_tasks`'s "absent = satisfied" collapse can't express a real block (per finding 5 above), the hold
  needs to route through `prereqs.prerequisites` (named boolean conditions, which default false and don't suffer this
  collapse) instead of `completed_tasks` for this specific case: auto-derive/maintain a condition like
  `gate-upstream-open:<upstream-stem>` set to `!_parse_open_todos(upstream)` on every regen tick, and wire it into the
  downstream tasks' `prereqs.prerequisites`.
- Add a unit test: a gated downstream plan whose upstream is `execution_scope: local-only` with an open checkbox must
  NOT be dispatchable; once the upstream's last checkbox is checked, it must become dispatchable on the next regen tick.

## Todos

- [x] ✅ [BACKEND] P1. Fix `_wire_gate_on_depends_prereqs`/`_completed_task_satisfied` (or add a new named-prerequisite
      derivation) in `agent-orchestrator/server/regen_backlog_from_plan.py` + `dispatch.py` so `gate_on_depends`
      correctly blocks on a `local-only`/`NA` upstream plan that still has open `- [ ]` todos, per the design above. Add
      regression tests mirroring `tests/test_dispatch_completed_prereqs.py`. (repo: agent-orchestrator) —
      agent-orchestrator@7b3f909. Fixed a SECOND compounding bug found while implementing: `depends_on` entries authored
      with a directory prefix (the real-world form this doc itself uses) never matched the wiring pass's bare-stem
      lookup, so the gate never fired regardless of upstream state — normalized both sides via a shared `_stem()`. For
      the never-ingested-upstream case, added a derived named prerequisite (`gate-upstream-open:<stem>`) read from the
      upstream plan's own live open-todo count and synced into `state.db.prerequisites` every regen tick (dispatch.py's
      `_prereqs_met` already honours named prerequisites — no dispatch.py change needed). 4 new regression tests in
      `test_regen_backlog_from_plan.py` (directory-qualified `depends_on` match, never-ingested-with-open-todos holds,
      DB condition lifecycle 0→1 on upstream completion), all passing; full `quality-gates.sh` green (basedpyright 0
      errors, 1567 tests passed).

## Codex SSOTs

`codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`,
`codex/11-project-management/doc-frontmatter-schema.md` (`depends_on` / `gate_on_depends` / `execution_scope`
semantics).
