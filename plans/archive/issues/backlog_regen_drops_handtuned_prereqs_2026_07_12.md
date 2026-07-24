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
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [backlog, regen, prereqs, conditions, redispatch-churn, orchestrator-bug]
related:
  [
    /plans/archive/issues/defi_perp_funding_mvp_scope_contradiction_2026_06_29.md,
    /plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    /plans/active/sports_manifest_canonicalisation_2026_06_01.md,
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
  "Defect A (doc): unified-trading-pm@f1585fb59 (RULES.md prereqs.conditions→prereqs.prerequisites); Defect B (code):
  agent-orchestrator@8dd5763 (BacklogTask.priority_override + _reconcile_task_fields skip + 3 regression tests); P2
  verification step: unified-trading-pm@39c9854ea. Code-verified 2026-07-16 (all 4 todos [x]; status flip was the only
  gap)."
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
- [x] [SCRIPT] P0. Read `server/regen_backlog_from_plan.py` (and whatever calls it on a timer) to find the
      merge/preserve logic for already-derived entries; identify why `prereqs.conditions` and `priority` aren't in the
      preserved set despite RULES.md §4 documenting that they are. **DONE 2026-07-12 by slot 5** — fully answered by the
      "Investigation results" section below (two independent defects isolated + empirically confirmed); flipping this
      checkbox now (slot 10) since the answer was already written but the box was left unchecked.
- [x] [SCRIPT] P1. Fix: extend the preserved-field set to include hand-tuned `prereqs.conditions` and `priority`
      overrides on already-derived task rows, OR (if the current design intentionally treats these as fully plan-derived
      and the RULES.md claim is simply stale/wrong) correct RULES.md §4 to describe the actual supported mechanism and
      point main-agent/operator at that instead. **DONE 2026-07-12 (slot-10)** — both defects fixed per the
      "Recommendation for todo 3" section below. Defect A (docs): `unified-trading-pm@f1585fb59` corrects RULES.md §4's
      `prereqs.conditions` → `prereqs.prerequisites` (the real field) in both the "park a task" recipe and the "adding
      new conditions" step 2, plus the `prereqs.conditions` reference in § "Prerequisites vs blocked-questions". Defect
      B (code, approach (a) — the correctness-recommended option): `agent-orchestrator@8dd5763` adds
      `BacklogTask.priority_override: bool = False` (a real, declared schema field — round-trips normally, no special
      pydantic config needed) and makes `_reconcile_task_fields()` skip the priority-revert branch when it's `True`.
      RULES.md's park-a-task recipe now documents setting `priority_override: true` in the SAME yaml edit as
      `priority: 999`. 3 new tests: `test_reconcile_priority_override_skips_revert` (direct unit test — override set →
      no revert), `test_reconcile_priority_without_override_still_reverts` (control — confirms default behavior is
      unchanged, drift still reconciles), `test_regen_priority_override_survives_regen_tick` (end-to-end via `regen()` —
      hand-tune priority+override on disk exactly per the RULES.md recipe, re-run a full regen tick against the same
      still-open todo, assert the override survives where a bare `priority: 999` previously reverted). Full
      `quality-gates.sh` green (1191 passed, 1 skipped, ruff+basedpyright clean).
- [x] ✅ [DATA] P2. Add a regression check (or a quick manual verification step documented in RULES.md) so the next time
      someone attaches a condition this way, they know to re-verify persistence after 1-2 regen cycles before trusting
      it's durable, until the P0/P1 fix lands. **DONE 2026-07-12 (slot-3)** — `unified-trading-pm@39c9854ea` (see
      Progress Log). Since todo 3's P0/P1 fix already landed with 3 automated regression tests
      (`test_reconcile_priority_override_skips_revert`, `test_reconcile_priority_without_override_still_reverts`,
      `test_regen_priority_override_survives_regen_tick`) covering the CODE path, this todo's remaining gap was
      specifically the "quick manual verification step documented in RULES.md" option it explicitly allows as an
      alternative to a new regression check. Added one directly to the park-a-task recipe in `agents/RULES.md` §4:
      re-check `priority`/`priority_override` in `data/config/backlog.yaml` survive the NEXT regen tick (not just
      `/reload`, which doesn't exercise the revert code path), and file a fresh P0 issue doc immediately if either
      reverts, rather than silently re-applying the edit and moving on (which is exactly the pattern that let this bug
      class churn for ~15 minutes before being caught the first time).

## Interim mitigation in use

Main agent is re-applying the gating edit reactively each time a duplicate `/blocked` question surfaces citing the stale
(un-gated) priority, and auto-answering those duplicates directly (citing this issue doc) rather than escalating each
one to the operator. `skip-current-task` per-slot-per-dispatch remains available as a secondary, DB-backed (not
yaml-based) mitigation that is NOT subject to this bug, since `slot_skips` is a separate table from `backlog.yaml`.

> **Recovered fork note (2026-07-14)**: the three subsections below were written by the main-agent session in a local
> copy of this doc on the root PM clone and never committed (the clone was starved behind LDR by the cron self-pull
> dirty-artifact bug, fixed 2026-07-14 in `scripts/dev/slot-cron-ff-pull.sh` / `scripts/dev/cron-self-pull-lib.sh`).
> They ran in parallel with the slot-5/slot-10 investigation below, which explains their observations:
> `prereqs.conditions` being stripped despite `priority_override: true` is Defect A (the field structurally cannot
> round-trip), and `priority_override` surviving is todo 3's Defect-B fix landing.

### 2026-07-12 update — `priority_override: true` partially mitigates

A new field, `priority_override` (bool, default `false`), has appeared on every task entry as of this date — apparently
added by whatever regen path also introduced the reshuffle behavior noted above. Main agent tested setting
`priority_override: true` alongside the hand-tuned `priority: 999` on `mvp_backfill_defi_onchain_v10-001`: `priority`
AND `priority_override` itself both survived 3+ consecutive poll cycles (~5 min) intact, whereas without the flag they
were stripped within ~2 min every time. **However, `prereqs.conditions` is NOT covered by this flag** — on one observed
cycle with `priority_override: true` set, `priority` held at 999 but the `conditions:` block was still silently dropped
in the same pass, requiring a separate re-add. Current best-known interim recipe: set BOTH `priority: 999` and
`priority_override: true` (durable), and continue re-checking `prereqs.conditions` specifically each tick, re-adding it
if stripped (not yet durable). Rolled this recipe out to the other three currently-gated tasks:
`sports_manifest_canonicalisation-001`, `tradfi_v9_stage1_finish-003`, `defi_morpho_lending_indices_never_wired-001`.
Separately, `cefi_live_only_data_types_vs_layer1_denominator_contradiction-001` has disappeared entirely from the
current derivation (not just un-gated — the task id no longer exists in `backlog.yaml`), consistent with the
task-id-reshuffle symptom described above; nothing to re-gate there until/unless it reappears under some id. Suggests
`priority`/`priority_override` are preserved-on-merge fields but `prereqs.conditions` is unconditionally re-derived (to
empty) every cycle regardless of the flag — worth checking specifically in `server/regen_backlog_from_plan.py`'s merge
logic per the P0 todo above.

### 2026-07-12 later update — `tradfi_v9_stage1_finish-003` vanished; new task thrashes on the same bug

`tradfi_v9_stage1_finish-003` disappeared entirely from a later derivation cycle (task count 19→17), same
task-id-reshuffle symptom as the cefi Layer-1 task above — nothing to re-gate until/unless it reappears. Separately, a
newly-derived task (`cefi_batch_manifest_blank_instrument_type_on_failure-003`, gated on sibling
`tardis-concurrent-ip-lock-fix-landed`) hit the `prereqs.conditions`-stripped-despite-`priority_override:true` bug 3
times in ~10 minutes (`BLK-82c8edc3`, `BLK-e047b522`, `BLK-adcf07fa`), each time re-dispatched to a different idle
worker (slot-6, slot-8, slot-9) who independently re-verified the unmet gate and correctly declined to proceed —
confirming the interim mitigation (spot-check + re-add `conditions` each tick) works but does not fully eliminate thrash
between checks, since the strip can happen and get re-dispatched before the next main-agent tick catches it. The task
went on to thrash 6 total times (`BLK-c8842409`, `BLK-d6a8795a`, `BLK-1ed7c791` in addition to the 3 above) before the
underlying sibling decision resolved (see below), consuming worker-slot cycles across slots 6/7/8/9 in under 30 minutes
purely on this bug.

### 2026-07-12 resolution — Tardis lockout decision landed, condition flipped

The operator ruled directly on a sibling `/blocked` question (`BLK-58aea31d`, "proceed-now" = option A: GCS-lease TTL
mutex stopgap) rather than via agent chat — worth noting as a channel main agent should watch (`GET /api/blocked/<id>`
404ing on a previously-open id is a signal the operator answered it directly outside chat). Slot-7 shipped the mutex (11
unit tests, opt-in launcher flag, QG green on both repos, plan flipped; on-VM smoke-test honestly deferred as a tracked
P2 follow-up since `gcloud` is unavailable in-slot). However, the `tardis-concurrent-ip-lock-fix-landed` condition
itself remained `false` after the fix shipped — landing a fix does NOT automatically flip its gating condition; main
agent had to do that manually (`POST /api/prerequisites/tardis-concurrent-ip-lock-fix-landed {"value": true}`) after
noticing 5 slots (7/8/9/10/11) idling on `worker_polling_dead` events referencing the still-false condition. Also closed
out the original `BLK-f1417674` decision thread (still unanswered in the queue) once the actual resolution was
confirmed. Worth codifying as a pattern: shipping a fix and flipping its gating condition are two separate steps, and
the condition flip is easy to miss since nothing automatically ties a landed PR/commit to a prerequisite value.

Also: flipping `tardis-concurrent-ip-lock-fix-landed` true was premature by itself — the sibling task
(`cefi_batch_manifest_blank_instrument_type_on_failure-003`) had TWO nested gates (fix landed AND the actual re-capture
sweep completing), and only one was wired. Slot-2 caught this correctly (`BLK-ad0376ed`) rather than letting the task
dispatch on a half-satisfied gate. **Notable distinct-field finding**: this task's entry uses `prereqs.prerequisites` (a
list of condition names), which the regen appears to natively derive/preserve, NOT `prereqs.conditions` (the hand-tuned
field this issue doc is about, which the regen does NOT yet derive and repeatedly strips). Added a second name
(`cefi-recapture-sweep-complete`, false) to that `prerequisites` list — worth testing whether `prereqs.prerequisites`
survives regen cycles more reliably than `prereqs.conditions`, which would suggest routing future hand-tuned gates
through `prerequisites` instead where the task already has that field derived, though `conditions` remains the only
mechanism for tasks that don't.

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

## Addendum (2026-07-12, slot 5): a third symptom — backlog task-ID churn re-dispatches already-checked-off todos

While closing out this exact investigation, the backlog dispatched a NEW task
(`backlog_regen_drops_handtuned_prereqs-004`, `queued_at: 2026-07-12T08:27:48Z`) with the identical title/brief as todo
1 ("Reproduce directly...") — but todo 1 was already `[x]` in this file and its work already committed at `6d0e41dc6`
(which is also, confusingly, the `done_sha` currently recorded against a DIFFERENT id,
`backlog_regen_drops_handtuned_prereqs-001`, which today refers to todo 2, "Read
`server/regen_backlog_from_plan.py`..."). So the same commit's `done_sha` is attached to one id while an
already-satisfied todo gets a fresh id and a fresh dispatch. Net effect: task IDs for this plan are NOT stable across
regen ticks (`-001` referred to todo 1 when this doc's investigation was written; it now refers to todo 2), and a
checked-off (`[x]`) todo was still eligible for a fresh dispatch under its new id. This is either a third distinct
defect (regen should skip deriving a task for a checked-off todo, or should keep a stable id keyed by todo content/hash
rather than positional index) or a downstream consequence of Defect B's per-tick re-derivation — todo 3's fix and todo
4's regression-check should both account for it. No rework was done for the redundant `-004` dispatch; it was closed
citing the pre-existing `6d0e41dc6` evidence.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-12** — slot-3 (sonnet/high, data_engineering), dispatched to `backlog_regen_drops_handtuned_prereqs-006`
  (todo 4, the P2 regression-check/verification-step todo). Closed via the documented-verification-step option (todo 3's
  fix already has solid automated test coverage for the code path) — added a short "verify it actually stuck" note to
  `agents/RULES.md` §4's park-a-task recipe, telling whoever uses it to re-check persistence after the NEXT regen tick
  and file a fresh P0 issue immediately (not silently re-apply) if it reverts. Doc-only change, no code. Did not
  re-touch todos 1-3 (already done by slot-5/slot-10).
- **2026-07-12** — slot-10 (sonnet/high, data_engineering — task carried a `[SCRIPT]` craft tag; adopted per RULES.md
  "per-task craft role"), dispatched to `backlog_regen_drops_handtuned_prereqs-002` (todo 3, the P1 fix). Shipped both
  defects' fixes in one turn — see the flipped checkboxes above for the full readout. Defect A (docs-only, no code):
  `unified-trading-pm@f1585fb59` corrects RULES.md §4's stale `prereqs.conditions` field name to the real
  `prereqs.prerequisites` in 3 places (park-a-task recipe, adding-conditions step 2, § "Prerequisites vs
  blocked-questions"). Defect B (code): `agent-orchestrator@8dd5763` adds `BacklogTask.priority_override: bool` + makes
  `_reconcile_task_fields()` respect it (approach (a) from the "Recommendation for todo 3" section — the
  correctness-recommended option over the priority=999-as-magic-sentinel alternative). Also flipped todo 2's checkbox
  (the "read the code, find the merge/preserve logic" investigation) — it was already fully and correctly answered by
  slot 5's "Investigation results" section but the box itself was left unchecked; crediting slot 5's work, not mine.
  Needed a `uv sync` first (agent-orchestrator's `.venv` didn't exist yet in this slot clone) before `quality-gates.sh`
  could resolve ruff/basedpyright/pytest — incidental `uv.lock` drift from that sync (dropped version pins on 2 editable
  local packages + a cosmetic extras-list reordering) was restored, not shipped, since it wasn't part of this fix. Full
  `quality-gates.sh` green (1191 passed, 1 skipped, ruff+basedpyright clean, ~20s). Did not touch todo 4 (P2
  regression-check/verification-step todo) — separate backlog task, out of scope for this dispatch.
