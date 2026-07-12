---
doc_type: issue
title:
  backlog regen silently drops hand-tuned prereqs.conditions + priority tuning on every cycle — contradicts RULES.md
  §4's documented preservation behavior
summary: |
  Main agent attached `prereqs.conditions` (a false-valued gate condition) + dropped `priority` to 999 on two
  recurring-redispatch backlog tasks (`mvp_backfill_defi_onchain_v10-001`, `sports_manifest_canonicalisation-001`)
  via the sanctioned yaml-tuning exception in `unified-trading-pm/agents/RULES.md` §4 ("Adding new conditions
  mid-cycle"). Within minutes each time, the edit was silently reverted — `priority` back to its original derived
  value (10 / 20) and the `conditions:` block dropped entirely — confirmed 3 times in ~15 minutes
  (2026-07-12T03:54Z, ~03:58Z, ~04:01Z). RULES.md §4 explicitly documents "the regen PRESERVES hand-tuned prereqs
  on derived entries" — observed behavior directly contradicts this. Whatever process is rewriting
  `agent-orchestrator/data/config/backlog.yaml` on this cadence (PlanRegenLoop tick, or another regen path) is
  either not preserving `prereqs.conditions`/`priority` on already-derived entries, or is doing a full
  re-derive-from-scratch that discards any field not present in the plan-derivation template. Net effect: the ONE
  documented mechanism for parking a recurring/unresolvable-without-operator-input task (attach a false condition +
  drop priority) does not hold, so redispatch churn on gated tasks continues despite correct use of the sanctioned
  tuning path — wasting agent-slot cycles on tasks known to be blocked pending an operator ruling.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [backlog, regen, prereqs, conditions, redispatch-churn, orchestrator-bug]
related:
  [
    defi_perp_funding_mvp_scope_contradiction_2026_06_29.md,
    mvp_backfill_defi_onchain_v10_2026_06_27.md,
    sports_manifest_canonicalisation_2026_06_01.md,
  ]
created: 2026-07-12
last_updated: 2026-07-12
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
drift_direction: advance-code
source: main-agent-observed-2026-07-12
resolved_by:
locked_by:
depends_on: []
---

# backlog regen drops hand-tuned prereqs.conditions + priority tuning

## Evidence

Task `mvp_backfill_defi_onchain_v10-001` (agent-orchestrator/data/config/backlog.yaml):

- Original derived state: `priority: 10`, `prereqs: {completed_tasks: [], prerequisites: []}` (no `conditions` key).
- 2026-07-12T03:54Z — main agent edited: `priority: 999`, added
  `prereqs.conditions: [drift_perp_funding_helius_throughput_ruled]` (condition already existed, created by slot 7 via
  `POST /api/prerequisites/`, value=false). Reloaded via `POST /api/backlog/reload`.
- Confirmed reverted to original state (priority=10, no conditions block) at next check, ~03:58Z.
- Redone at 03:58Z. Confirmed reverted again ~04:01Z.
- Redone a 3rd time at 04:01Z, then a 4th time at 04:08Z after another confirmed revert.

Task `sports_manifest_canonicalisation-001`: identical pattern, `priority: 20 -> 999` +
`prereqs.conditions: [defi-c0-c-green]` (condition created by main agent), reverted on the same cadence.

Two `/blocked` questions (`BLK-744b63fd`, `BLK-ec149df1`) were filed by workers reporting the task still dispatchable at
the ORIGINAL priority (10/20) shortly after main agent's fix had (at that moment) landed on disk — consistent with the
revert happening on a tight cycle relative to worker dispatch checks.

## Contradicts documented behavior

`unified-trading-pm/agents/RULES.md` §4 ("Adding new conditions mid-cycle"), step 2:

> ATTACH it to a task: add `prereqs.conditions: [<condition-name>]` on the task's entry in `data/config/backlog.yaml`,
> then `POST /api/backlog/reload`. This attachment is the ONE tuning that is still yaml-only — the regen does NOT yet
> derive per-task `prereqs.conditions` from plan todos ... **and the regen PRESERVES hand-tuned prereqs on derived
> entries.**

Observed: hand-tuned `prereqs.conditions` AND the co-located `priority` override are both dropped on regen, directly
contradicting the bolded claim above.

## Suspected root cause (unconfirmed — no Cloud Logging / gcloud access from this agent to verify)

Likely `server/regen_backlog_from_plan.py` (or the `PlanRegenLoop`/reload path it feeds) re-derives each task entry from
its plan todo on every cycle and only merges/preserves fields it explicitly special-cases — if `priority` and
`prereqs.conditions` aren't in that preserved-field allowlist (only e.g. `prereqs.prerequisites`/ `completed_tasks`
might be), a full re-derive silently clobbers them. `new_tasks: 0` was reported on every observed reload (i.e. no _new_
task rows were created), consistent with existing rows being overwritten in place rather than a fresh-insert path — the
corruption is on the UPDATE/merge side, not task discovery.

## Impact

- The only documented mechanism for parking a task pending operator input (condition + priority=999) is not durable —
  any task gated this way will silently un-gate itself and resume redispatching within minutes.
- This directly compounds the wasted-agent-time problem it was meant to solve: instead of N workers each independently
  rediscovering an unresolvable blocker, the gate itself becomes a source of repeat rediscovery/re-filing
  (`BLK-744b63fd`, `BLK-ec149df1` were both stale-state artifacts of this bug, not new information).
- Any other in-flight or future use of this sanctioned tuning path (parking, condition-based gating generally) is
  unreliable until fixed.

## Todos

- [x] [DATA] P0. Reproduce directly: attach `prereqs.conditions` + non-default `priority` to a throwaway/test backlog
      task entry, trigger `POST /api/backlog/regen` (not just `/reload`) and separately wait out one natural
      `PlanRegenLoop` cycle, and diff the entry before/after each to isolate which code path drops the fields. — done
      2026-07-12 by slot 5, see "Investigation results" below.
- [ ] [SCRIPT] P0. Read `server/regen_backlog_from_plan.py` (and whatever calls it on a timer) to find the
      merge/preserve logic for already-derived entries; identify why `prereqs.conditions` and `priority` aren't in the
      preserved set despite RULES.md §4 documenting that they are.
- [ ] [SCRIPT] P1. Fix: extend the preserved-field set to include hand-tuned `prereqs.conditions` and `priority`
      overrides on already-derived task rows, OR (if the current design intentionally treats these as fully plan-derived
      and the RULES.md claim is simply stale/wrong) correct RULES.md §4 to describe the actual supported mechanism and
      point main-agent/operator at that instead.
- [ ] [DATA] P2. Add a regression check (or a quick manual verification step documented in RULES.md) so the next time
      someone attaches a condition this way, they know to re-verify persistence after 1-2 regen cycles before trusting
      it's durable, until the P0/P1 fix lands.

## Interim mitigation in use

Main agent is re-applying the gating edit reactively each time a duplicate `/blocked` question surfaces citing the stale
(un-gated) priority, and auto-answering those duplicates directly (citing this issue doc) rather than escalating each
one to the operator. `skip-current-task` per-slot-per-dispatch remains available as a secondary, DB-backed (not
yaml-based) mitigation that is NOT subject to this bug, since `slot_skips` is a separate table from `backlog.yaml`.

## Investigation results (2026-07-12, slot 5, task `backlog_regen_drops_handtuned_prereqs-001`)

**Root cause is fully confirmed and precisely isolated — two independent defects, not one.** Method: static read of
`agent-orchestrator/server/backlog.py` + `server/regen_backlog_from_plan.py`, then an ISOLATED sandbox reproduction
(temp PM-repo + temp `backlog.yaml`, importing the actual `server.backlog` / `server.regen_backlog_from_plan` modules) —
no live orchestrator state was touched; `ORCHESTRATOR_PM_REPO_PATH` / `ORCHESTRATOR_BACKLOG` / `ORCHESTRATOR_VM_ID` env
vars redirected all resolution into the tempdir.

### Defect A — `prereqs.conditions` is not a real field; it is silently dropped by pydantic on ANY load, not preserved-vs-dropped by any merge logic

`server/backlog.py` `TaskPrereqs`:

```python
class TaskPrereqs(BaseModel):
    completed_tasks: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
```

There is no `conditions` field, and neither `TaskPrereqs` nor `BacklogTask` sets `model_config = ConfigDict(extra=...)`,
so pydantic v2's default `extra="ignore"` applies: `load_backlog()` → `Backlog.model_validate(data)` silently drops any
on-disk `conditions:` key at PARSE time (confirmed empirically: `hasattr(loaded_task.prereqs, 'conditions')` is `False`
immediately after `load_backlog()`). `save_backlog()` → `backlog.model_dump()` then naturally omits it from whatever
gets written back to disk, because the in-memory object never held it in the first place. This is not a
missing-preserve-allowlist bug — the field structurally cannot round-trip through the current schema at all.

**The field RULES.md §4 documents (`prereqs.conditions`) does not exist. The real, wired field is
`prereqs.prerequisites`** (`TaskPrereqs.prerequisites: list[str]`) — confirmed as the live dispatch gate in
`server/dispatch.py`:

```python
# line 171: for cond in task.prereqs.prerequisites:
# line 196: return all(prerequisites.get(cond, False) for cond in task.prereqs.prerequisites)
```

which checks each name against the `Backlog.prerequisites: dict[str, bool]` condition registry — exactly the registry
`POST /api/prerequisites/<name>` seeds (RULES.md §4 step 1 is correct; only step 2's field name is wrong). This is very
likely a doc-rot artifact of a rename: `server/bootstrap.py` has `_migrate_conditions_table_to_prerequisites()`
(renaming the legacy SQLite `conditions` table → `prerequisites` "preserving data") — the YAML-schema field was almost
certainly renamed the same way at some point, and the RULES.md §4 snippet was never updated to match.

**Practical consequence**: every time main agent (or anyone) writes `prereqs.conditions: [...]` per the RULES.md §4
recipe, it is DOA — gone on the very next `load_backlog()` anywhere in the process (reload, regen, dispatch startup,
...), regardless of any merge/preserve logic. Using `prereqs.prerequisites: [...]` instead is the actual supported
mechanism and does NOT hit this defect (that field round-trips fine — it's a real, declared model field).

### Defect B — `priority` is unconditionally re-derived on every regen tick for any task whose brief still matches its plan's open todo

`server/regen_backlog_from_plan.py` `_reconcile_task_fields()` (lines 1231–1270), called from `regen()`'s per-todo loop
whenever a todo's brief matches an already-derived task from the SAME plan (the "RC-1 reconcile-in-place" fix,
2026-07-07, intended to let a plan retier/re-home/reorder reach an already-queued task):

```python
if task.priority != priority:
    task.priority = priority
    changed = True
```

`priority` here is always the PLAN-DERIVED value (`_PRIORITY_MAP` keyed off the todo's `P<n>` tag — line 1067),
recomputed fresh every call. There is no check for "was this hand-overridden" — RC-1 has no concept of a hand-tuned
field, so a `priority: 999` override reverts to the plan's original P-tag value (10, 20, ...) on literally every regen
tick, as long as the todo line itself is still open (unchecked) in the plan file. This is INDEPENDENT of Defect A — it
fires purely from the todo/brief match, with no involvement of `prereqs` at all.

**Both `POST /api/backlog/regen` and every natural `PlanRegenLoop` tick call the exact same `regen()` function**
(`server/routes/backlog.py:141` and `server/regen_backlog_from_plan.py:1650` respectively) — so both paths trigger
Defect B identically. A bare `POST /api/backlog/reload` does NOT call `regen()` or `_reconcile_task_fields()` at all
(`server/routes/backlog.py:91`, `reload_backlog()` only calls `load_backlog()` — no save, no reconcile), so `/reload`
alone cannot revert `priority`; it CAN still silently lose `conditions` from the in-memory served copy (Defect A fires
on load alone) even though it leaves the on-disk YAML text byte-for-byte unchanged.

### Empirical confirmation (sandbox, live orchestrator untouched)

Sequence: seed-derive a throwaway task from a temp plan → hand-tune it exactly per the RULES.md §4 recipe
(`priority: 999` + `prereqs.conditions: [test-condition]`) → test each path in isolation, reading the actual on-disk
YAML (not a raw substring match — the test task's title/brief happen to contain the word "conditions" as prose, which
would false-positive a naive text search):

| Path exercised                                                                       | `prereqs.conditions` key present after? | `priority` after? |
| ------------------------------------------------------------------------------------ | --------------------------------------- | ----------------- |
| Hand-tune applied (baseline)                                                         | present                                 | 999               |
| Bare `load_backlog()` + `save_backlog()` round-trip (no `regen()`, no plan-matching) | **gone**                                | 999 (unchanged)   |
| Full `regen()` (== `/api/backlog/regen` == every `PlanRegenLoop` tick)               | **gone**                                | **10** (reverted) |

This isolates the two symptoms to two distinct mechanisms exactly as todo 1 asked:

- The `conditions` key is lost on ANY load — it's a schema defect (Defect A), not a regen-specific merge bug. It would
  be lost even by a hypothetical `/reload`-then-immediate-`save`, though the actual `/reload` endpoint today never calls
  `save_backlog()`, so in the wild it only actually hits disk via `regen()` (manual or looped).
- The `priority` revert is regen()-specific (Defect B) — a bare load/save round-trip does not touch it; only the
  todo-reconcile loop inside `regen()` does, and that loop runs identically from `POST /api/backlog/regen` and from
  every `PlanRegenLoop._run_one_tick()`.

### Recommendation for todo 3 (the fix)

Two separate fixes, since these are two separate defects:

1. **Defect A**: this is a documentation bug, not a code bug — `prereqs.prerequisites` already IS the durable, wired
   mechanism. Fix RULES.md §4 step 2 to say `prereqs.prerequisites: [<condition-name>]` (not `prereqs.conditions`), and
   drop the now-inaccurate "regen does NOT yet derive per-task prereqs.conditions... and the regen PRESERVES hand-tuned
   prereqs" framing — replace with "prereqs.prerequisites round-trips normally; it's a real schema field, nothing
   special to preserve." (Optional secondary hardening: reject/warn on an unrecognized `conditions` key in `TaskPrereqs`
   via `model_config = ConfigDict(extra="forbid")` so a future stale-doc mistake fails loud on next load instead of
   silently vanishing — flagged as an option, not mandatory, since `extra="forbid"` would also break on ANY other
   unrecognized key such as an operator experimenting with a new field name before the model supports it.)
2. **Defect B**: real code bug in `_reconcile_task_fields()` — it needs a way to know a `priority` value was hand-set
   and should NOT be overwritten by the plan-derived P-tag on subsequent ticks. Two viable approaches: (a) track a
   `priority_override: bool` (or `priority_source: "plan" | "hand"`) field on `BacklogTask`, set it True whenever
   `priority` is edited outside of `_reconcile_task_fields`, and have `_reconcile_task_fields` skip the priority branch
   when that flag is set; or (b) treat `priority == 999` as a reserved "manually parked" sentinel that
   `_reconcile_task_fields` never touches (simpler, but overloads a magic number — the parking convention RULES.md §4
   already documents `priority: 999` as "pushes to back of queue", so this reuse is at least consistent with existing
   intent, though it forecloses ever wanting a legitimately-priority-999 plan-derived task). Recommend (a) for
   correctness; (b) is a faster patch if todo 3's agent wants a same-day fix.

Repro script (not shipped — throwaway, sandbox-only, deleted after the run):
`/tmp/claude-1000/.../scratchpad/repro_backlog_regen_bug.py` on slot 5, run via
`cd agent-orchestrator && uv run python <script>`. Not committed anywhere; the empirical table above is the durable
evidence.
