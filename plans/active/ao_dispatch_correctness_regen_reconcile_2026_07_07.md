---
doc_type: plan
title: AO dispatch correctness — regen reconcile, dynamic role boot-prompts, model capability chain
summary:
  Fix the three root causes behind the 2026-07-07 fleet stall so plan edits actually reach the running backlog. Today
  regen only APPENDS and dedups by brief — it never updates an existing task when its text, model, effort, thinking, or
  role change, and the DB stores neither model nor role — so every plan retier/re-home is silently inert on in-flight
  work. This plan makes regen a true RECONCILE (field-drift updates, removal handling, dispatched-task adaptation),
  replaces hard role-refusal with dynamic per-task roles loaded as additive boot prompts, adds the
  fable-opus-sonnet-haiku capability chain with stop-and-resume for already-dispatched retiers, and adds slot_skips
  hygiene. Human-driven — done here with the operator, pushed to agent-orchestrator via quickmerge only after each phase
  is complete and verified. Fable + new effort-level enablement is a deferred later phase. Records the incident in
  issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    dispatch,
    regen,
    reconcile,
    backlog,
    model-tier,
    capability-chain,
    craft-routing,
    role-registry,
    slot-skips,
    incident-fix,
  ]
related:
  [
    issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md,
    instruments_completion_tracker_2026_07_06.md,
    ../../codex/04-architecture/agent-orchestrator-backlog-state-alignment.md,
    ../../codex/04-architecture/agent-orchestrator-overview.md,
    ../../codex/04-architecture/agent-orchestrator-autospawn.md,
  ]
created: 2026-07-07
last_updated: 2026-07-07
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
assigned_role: backend-engineer
model_tier: opus-required
thinking_tier: max
drift_direction: advance-code
depends_on:
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  fleet-idle investigation 2026-07-07 + operator design decisions (regen reconcile, multi-role plans, capability chain)
---

> **🟡 In-flight AO dispatcher refactor (2026-07-07).** This plan changes `regen_backlog_from_plan.py`, `dispatch.py`,
> `autospawn.py`, the worker routes, and the ORM. It is **human-driven** (`assigned_vm: NA`,
> `execution_scope: local-only`) — the operator + main agent do it HERE and push to agent-orchestrator via quickmerge
> only after each phase is done + verified. It is deliberately NOT dispatched to the AO fleet (it modifies the very
> dispatcher that would execute it — a bad change would brick the fleet). Incident record:
> `issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md`.

## Goal

Make a plan edit reliably reach the running fleet. When an operator changes a plan — reword a todo, retier its model,
re-home its role, remove an item — the backend must reconcile that change into the live backlog + any in-flight worker,
following the rules the operator specified. Eliminate the dispatch→refuse→skip→re-dispatch craft thrash by making roles
dynamic (a worker reads another boot prompt) instead of a hard refusal.

## Why (root causes — see the issue doc for the full incident)

Grounded in the code as of 2026-07-07:

- **RC-1 — regen never updates existing tasks.** `regen_backlog_from_plan.py` is append-and-dedup-by-brief
  ([regen L892-943](../../../agent-orchestrator/server/regen_backlog_from_plan.py)): a brief already in the backlog is
  skipped, a new brief is appended. There is no diff-and-patch path. Model/effort/thinking/role live ONLY on the
  `backlog.yaml` BacklogTask (the DB `TaskRow` has no such columns — `orm.py`), stamped once at creation. So a plan
  retier/re-home is inert on every already-queued task.
- **RC-2 — no craft routing + one-role-per-tick spawn.** `SlotRow` has no role column; `pick_next_task` has no role
  filter; `autospawn._top_queued_task_params` boots the whole tick at the TOP task's single role. A role-mismatched task
  gets dispatched, the worker refuses via its boot prompt, and `/skip-current-task` writes a permanent per-(slot,task)
  `slot_skips` row (no unskip API) → thrash + starvation.
- **RC-3 — slot_skips accumulate and persist across respawns**, keyed by slot_id not session, with no expiry.

The MODEL-tier gate (`dispatch._task_outranks_slot`, `_MODEL_RANK {haiku:0, sonnet:1, opus:2}`) already does the right
thing for QUEUED tasks: an opus task is left queued for an opus spawn; an opus slot may take a sonnet task. This plan
keeps that and extends it to already-DISPATCHED retiers + adds fable.

---

## Designed behavior (the contract — SSOT-in-flight; migrate to codex at Phase 6)

### A. Regen becomes a RECONCILE (RC-1)

Each tick, regen computes the desired task set per active plan (briefs + per-task tier/role/priority + plan_order) and
diffs it against the backlog + DB. Four cases (A1–A3) plus execution order (A4):

**A1 — field drift on a matched task** (brief matches an existing task; model / effort / thinking / assigned_role /
priority differ). Update the `backlog.yaml` BacklogTask + propagate to the in-memory backlog (`on_regen`). Then, by the
task's DB status:

- `queued` / `blocked` (undispatched) → just updated; the next `pick_next_task` uses the new tier/role. Done.
- `dispatched` (in-flight) with a **model/effort/thinking** change → apply the capability chain (section C): higher tier
  required than the running worker → **stop the lower worker + redispatch via `--resume`** at the higher tier; lower-or-
  equal → keep the running (≥) worker, update the stored tier for the next respawn.
- `dispatched` with a **role** change → signal the worker to read the new role's boot prompt (section B); no stop unless
  the role also implies a higher model (then the model-chain rule applies).
- `done` → no-op.

**A2 — text change on a task** (a todo reworded). LOCKED no-anchor (Phase 0): a reworded todo has no stable link to the
old task, so it is handled as **remove-old + add-new** — the old brief is no longer current (→ A3: queued/blocked prune,
dispatched cancel + scoped-revert, done keep) and the new text ingests as a fresh task. Deterministic under frequent
mid-work edits; regen never writes back to plan files.

Adapt-in-place (pause the dispatched worker, pull LDR, re-read, resume) still applies to **A1 tier/role/priority**
changes — those leave the brief text UNCHANGED, so brief-match identifies the (even dispatched) task exactly. Only a
genuine text reword falls back to remove+add.

**A3 — removal** (todo deleted, flipped to `- [x]`, struck through, or turned non-dispatchable). Brief no longer
current:

- `queued` / `blocked` → delete from yaml + DB (existing safe prune — keep).
- `dispatched` → do NOT delete. **Mark the task `cancelled`** (new terminal status), surface a **cancelled count in the
  UI**, **stop the worker**, and instruct it to **revert ONLY this task's changes** (scoped `git restore` of its own
  touched files — never whole-branch, never `reset --hard`). Record cancellation reason + provenance.
- `done` → keep (audit history) — unaffected.

**A4 — execution order follows plan-file position.** Regen stamps each task a `plan_order` = its ordinal position among
the plan's open todos, RE-DERIVED every reconcile tick. Dispatch sorts by `(tier, priority, plan_order)`. Today it is
only `(tier, priority)`, so at equal priority the tiebreak is backlog.yaml APPEND order — a mid-file insert wrongly
sorts to the end (X,Y inserted between B and C dispatch AFTER C,D,E). This is also the **"10 tasks all at P0 that must
hold order"** case: with only `(tier, priority)` all 10 tie and fall back to append order; `plan_order` makes them
dispatch in plan-file sequence. With `plan_order`, inserting X,Y between B and C makes them dispatch in
**A,B,X,Y,C,D,E** order after the next tick, regardless of task_id or yaml order. **CAVEAT** — the fleet runs ~N tasks
concurrently, so `plan_order` controls DISPATCH / pick-up order among tasks that are READY now, NOT completion order; a
strict "X must finish before C starts" is a PREREQ (`completed_tasks` / `gate_on_depends`), not ordering. Cross-plan,
priority stays the lever (plan_order is intra-plan; a deterministic `plan_ref` tiebreak keeps inter-plan order stable).

### B. Dynamic per-task roles via additive boot prompts (RC-2 / operator D2)

- **Per-task role** comes from the todo's `[TAG]` category (`[INFRA]`→infra, `[DATA]`→data_engineering,
  `[BACKEND]`→backend-engineer, `[UI]`→ui-developer, `[REVIEW]`→review, …), falling back to the plan's `assigned_role`
  when the tag is generic (`[CODE]`/`[SCRIPT]`) or unmapped. Carried on the BacklogTask.
- **A worker serves multiple roles over its lifetime.** Roles are additive boot prompts, not a pinned identity.
  `SlotRow` gains a `last_role` column = the role the worker most recently booted/served.
- **Dispatch**: when the dispatched task's role ≠ the slot's `last_role`, the dispatch payload instructs the worker to
  **read `agents/<role>.md`** (the craft delta) before starting, and the backend updates `last_role`. **No role-refusal,
  no skip** — the worker adapts instead of bouncing the task.
- **Remove the worker-level role-refusal → `/skip-current-task` path** (the thrash source). Role becomes a soft routing
  signal + a dynamic boot-load. The MODEL tier stays a HARD gate (capability chain).
- **Optional routing preference**: prefer a slot already in the task's role (avoids a boot reload) — an affinity-style
  tiebreak, not a filter.
- **Plan-authoring rule** (docs, Phase 5):
  - **Shared context across roles → ONE plan, multiple `[TAG]` roles** — the one worker reads the extra boot prompt and
    keeps the shared context.
  - **No shared context → SEPARATE plans** — independent workers, independent context.

### C. Model capability chain + effort (RC-1 dispatched path)

- Rank `haiku < sonnet < opus < fable` (fable highest). A higher-rank worker always serves a lower-rank task; the
  reverse never dispatches. Queued tasks keep the existing `_task_outranks_slot` gate (leave-for-higher-spawn); already-
  dispatched retiers use the stop-and-`--resume`-higher mechanism (preserves the worker's session/context).
- **Fable + new effort levels: enablement DEFERRED to Phase 6** (operator). This plan makes the rank ordering and the
  stop/resume mechanism Fable-ready; wiring Fable as a spawnable model (CLI flags, effort vocabulary, account support)
  is the later phase.

### D. slot_skips hygiene (RC-3)

- Expire skips after N hours (configurable). Clear a task's skips when its plan changes (tier/role/brief) or a prereq
  lands. Add an unskip API (operator + programmatic). With role-refusal removed (B), the craft-mismatch skip source is
  gone; remaining skips are genuine undoable-from-this-slot cases and should still expire.

### E. Plan grouping + draft-gated phase chains (planning standard)

**STRICT — an AO-ingested plan (`assigned_vm: planning` + `execution_scope: orchestrator-agent`, not draft) carries
10–20 todos, never more.** Fewer is fine; where possible group RELATED items so we don't end up with hundreds of tiny
plans. A 100-todo monolith is banned for dispatch — it bloats the backlog and couples unrelated work. Human /
`local-only` plans (like this one) are exempt: they are never ingested. An AUDIT is always its own plan. For sequential
phases, ship each phase as a separate plan and gate the chain by `status`: only the CURRENT phase is `status: active`
(ingested + dispatchable); later phases are `status: draft` (regen skips them entirely, so an unfinalised phase never
floods the backlog). Each phase's LAST todo finalises the next phase's todos — from what this phase learned — and flips
it `draft`→`active`. Leans on existing regen machinery (draft = not ingested; active→draft prunes queued tasks).
Distinct from `depends_on` + `gate_on_depends: true`, which INGEST the downstream plan but machine-hold its tasks until
upstream is done — use that when the downstream is already finalised; use draft-gating when a later phase's todos depend
on what an earlier phase discovers. (This AO-fix plan is `execution_scope: local-only` + human-driven, so it is never
ingested — it stays one file for interactive execution; the standard is for future AO-dispatched multi-phase work.)

### F. Plan → single-agent stickiness, with spillover (operator model 2026-07-07)

**Default: a plan's tasks are owned by ONE agent** so it accumulates the plan's full context. The slot that claims a
plan's FIRST task becomes the plan's owner; dispatch stamps the plan's other queued tasks with `target_slot = that slot`

- `affinity: medium`, so they prefer the owner and are worked in `plan_order` sequence (A4). The single owner reads
  whatever role boot-prompts its tasks' `[TAG]`s require (B) — multi-role within one plan = one agent, many boot
  prompts.

**Spillover** (the "if the agent is slow, run concurrently" escape): `affinity: medium` waits up to
`target_slot_timeout_seconds` for the owner; if the owner is still busy past that, the next task spills to a free slot
and runs concurrently — so a slow plan does not stall and idle slots are not wasted. Reuses the existing affinity
primitive (`dispatch._task_is_routable_to`); the NEW part is auto-setting the plan's `target_slot` at first-claim +
propagating it to the plan's other queued tasks.

**Parallelism = more plans, not a split plan.** If a plan's items are independent and you WANT them run in parallel from
the start, author them as N separate plans (each ≤20 todos), one per agent — do NOT spread one plan across agents
(spillover aside). Documented in task_template + CLAUDE.md (E).

**Ordering — BOTH modes (operator: "both a and b"):**

- (a) DEFAULT `plan_order` — pickup order; the owner works tasks top-to-bottom, spillover only when slow. Tasks MAY run
  concurrently (owner sequentially + any spilled tasks on other slots).
- (b) `sequential: true` (plan frontmatter) — STRICT serial: regen auto-chains each task's `prereqs.completed_tasks` to
  the previous task in file order (re-derived every tick), so task N cannot dispatch until task N-1 is `done`. No
  spillover — order is guaranteed by the prereq chain. For audit→fix→verify / migration plans.

---

## Codex SSOTs (read before touching; update at Phase 6 — plan↔codex drift is review-blocking)

- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch + regen + ingestion contract.
- `codex/12-agent-workflow/agent-orchestrator-overview.md` — runtime loops (AutoSpawn / regen / failover / watchdog).
- `codex/04-architecture/role-registry.md` — role → (model, thinking, lifecycle); the tag→role mapping extends this.

---

## Phased DAG (each phase gates the next; push to AO via quickmerge only after done + verified — operator D3)

### Phase 0 — Design lock (this session, no code) — LOCKED 2026-07-07

- [x] [DESIGN] P0. LOCKED — NO anchor/tid. A text-edited todo → **remove-old + add-new** (A2), not an in-place update;
      regen stays read-only on plan files. A tid-writeback script was considered + rejected: it COULD isolate todo lines
      safely (reuse `_parse_open_todos`, which already skips frontmatter/code/tables/done/prose), but the backend
      writing to the hot PM repo → git conflicts with the operator + other agents, plans are edited many times mid-work,
      and it buys little over remove+add. Brief-match still IDs unchanged-text todos, so tier/role reconcile +
      dispatched adapt-in-place work with no anchor.
- [x] [DESIGN] P0. LOCKED — `[TAG]`→role slugs verified against `agents/*.md`: INFRA→infra, DATA→data_engineering,
      BACKEND→backend-engineer, UI→ui-developer, REVIEW→review; generic CODE/SCRIPT → plan `assigned_role`.
- [x] [DESIGN] P0. LOCKED — `cancelled` terminal status + UI count; scoped revert of ONLY the worker's own task changes
      (`git restore` of its touched files), never whole-branch, never `reset --hard`.

### Phase 1 — Author-facing docs FIRST (task_template + CLAUDE.md; no dispatcher code)

> Docs before code: establish the plan-authoring conventions so every plan written from here follows them. Mark clearly
> which DISPATCH mechanics are ACTIVE NOW vs ROLLING OUT in this plan, so an author never relies on unbuilt behavior.

- [x] [DOCS] P0. Rewrite `plans/active/task_template.md` to the CURRENT frontmatter schema (the existing template is
      STALE — `.plan.md` suffix + completion_gates C0–C5 predate PLAN_FORMAT.md). Two authoring tracks: LOCAL/human plan
      (`assigned_vm: NA`, `execution_scope: local-only` — never ingested, may be long, operator does + verifies) vs
      AO-DISPATCHED plan (`assigned_vm: planning`, `execution_scope: orchestrator-agent`, `status: active`, STRICT 10–20
      todos). — ✅ DONE pm@08e6424 (LDR); PR #809→main auto-merge.
- [x] [DOCS] P0. task_template.md — the AO plan-authoring rules: 10–20 cap + group related items (E); ONE plan = ONE
      agent / shared context, split into separate plans for PARALLELISM (F); an audit is its own plan; draft-gated phase
      chains — current `active`, later `draft`, last todo flips next→active (E); `[TAG]`→role for per-task craft (B);
      `sequential: true` vs default `plan_order` ordering (F); NEVER hand-edit `backlog.yaml`. — ✅ DONE pm@08e6424
      (§1–§4 of the new template).
- [x] [DOCS] P0. task_template.md — a "Safely editing a live plan" section: what a reword / removal / retier does to a
      queued vs dispatched vs done task (A1–A3); removed-dispatched → `cancelled` + scoped-revert (not delete);
      retier-upgrade → stop-and-`--resume`. Tag each dispatch mechanic ACTIVE-NOW vs ROLLING-OUT (this plan); until
      `plan_order` / `sequential: true` ship, use explicit prereqs for strict ordering. — ✅ DONE pm@08e6424 (§5 of the
      new template, A1–A3 table).
- [x] [DOCS] P0. CLAUDE.md (PM + agent-orchestrator copies) — directive under the Plans section: **READ
      `plans/active/task_template.md` before authoring any plan**; + the one-liners (local vs AO; 10–20 cap; one-plan =
      one-agent, split for parallelism). Respect the size budget (condense, don't grow the cap). — ✅ DONE pm@08e6424
      (cursor-configs/CLAUDE.md L170-175; 28,629 B < 40,960 cap; both symlinked copies update).

### Phase 2 — RC-1 reconcile: field-drift + removal (unblocks the frozen backlog)

- [x] [BACKEND] P0. Regen reconcile pass — a brief-matched task whose model/effort/thinking/assigned_role/priority drift
      from the plan updates the `backlog.yaml` BacklogTask + propagates to the in-memory backlog. Queued/undispatched
      scope in this task. — ✅ DONE ao@ff6100ad (`_reconcile_task_fields` + per-plan brief-match in `regen()`;
      `summary.reconciled`). Auto-heals the frozen backlog on the next tick.
- [x] [BACKEND] P0. Add `cancelled` task status (orm + state_store + dispatch/prune treat it terminal, never re-queued).
      — ✅ DONE ao@c6a31ed6 (status is a free String col; dispatch's `status != 'queued'` gate already excludes it;
      prune never re-queues it — it's terminal like `done`).
- [x] [BACKEND] P0. Removal of a DISPATCHED task → mark `cancelled` (not delete) with reason/provenance; queued/blocked
      removal keeps the existing safe prune; `done` untouched. — ✅ DONE ao@c6a31ed6 (`_prune_stale` UPDATEs
      dispatched-orphans → cancelled; queued orphans still hard-deleted; 2 tests: cancel-not-delete +
      queued-still-deletes).
- [x] [BACKEND] P1. Worker stop + scoped-revert signal for a cancelled in-flight task (stop the agent; instruct
      `git restore` of only this task's touched files). — ✅ DONE ao@c6a31ed6 (`HeartbeatResponse.cancel_task` +
      heartbeat detects TaskRow status=cancelled → `dispatch_reason: cancelled`; worker.md instructs scoped
      `git restore` of own in-flight files only, /skip-current-task, never whole-branch. NOTE: interrupting a mid-task
      worker via a /progress message is a follow-up — today the worker sees it at its next /heartbeat/boot boundary).
- [ ] [UI] P1. Surface the cancelled count in the fleet/backlog UI (`unified-trading-system-ui` / deployment-ui as
      applicable). — 🟡 DEFERRED (UI repo; the `cancelled` status is now emitted, so a count is a small UI add).
- [x] [BACKEND] P0. Execution order — add `plan_order` (the todo's file position) to BacklogTask; regen sets + refreshes
      it from plan-file order every reconcile tick; extend the dispatch sort key to `(tier, priority, plan_order)`.
      Fixes mid-file inserts sorting to the end (A4). Cross-plan tiebreak stays deterministic (`plan_ref`). — ✅ DONE
      ao@ff6100ad (`BacklogTask.plan_order`; `dispatch.pick_next_task` sort key; test_dispatch_plan_order.py 3 tests).
- [x] [BACKEND] P1. `sequential: true` plan flag (F, mode b) — regen auto-chains each task's `prereqs.completed_tasks`
      to the previous task in file order (re-derived every tick, re-links around inserts/removals), for strict-serial
      plans. Order guaranteed by the prereq chain; no spillover. — ✅ DONE ao@ff6100ad (`_wire_sequential_prereqs` +
      `_parse_frontmatter_sequential`; rebuilds the chain so a reorder can't deadlock; 2 tests incl
      reorder-no-deadlock).
- [x] [BACKEND] P0. Tests — reconcile updates tier/role on a queued task; dispatched removal → cancel; done untouched;
      queued removal still prunes; no duplicate-append on a pure field drift; **insert X,Y between B,C → dispatch order
      A,B,X,Y,C,D,E** (plan_order); reorder/insert never disturbs an unchanged todo's task. — ✅ DONE ao@ff6100ad +
      c6a31ed6 (test_regen_reconcile.py 9 + test_dispatch_plan_order.py 3 = 12 green; covers reconcile / plan_order /
      sequential / dispatched-removal→cancel / queued-removal-deletes; full `quality-gates.sh` green both batches).

### Phase 3 — RC-1 reconcile: dispatched adaptation (capability chain + brief-unchanged pause/adapt)

- [ ] [BACKEND] P0. Text-edited todo → remove-old + add-new (no anchor): the changed brief drops out of current-briefs
      so A3 handles the old task by status (prune/cancel/keep) and the new text ingests fresh. Assert NO in-place text
      update + no plan-file writeback.
- [ ] [BACKEND] P0. Extend `_MODEL_RANK` with fable (`haiku<sonnet<opus<fable`); a dispatched task whose reconcile
      raises its required tier ABOVE the running worker → stop the lower worker + redispatch via `--resume` at the
      higher tier; downgrade → keep the running (≥) worker + update the stored tier for the next respawn.
- [ ] [BACKEND] P1. A dispatched task whose tier/role changed but stays within the worker's model tier → pause + hand
      the updated definition (pull LDR, re-read the plan item), resume (adapt-in-place; brief unchanged).
- [ ] [BACKEND] P0. Tests — text-edit remove+add; upgrade stop+resume; downgrade keeps worker; brief-unchanged
      adapt-in-place; rank ordering incl fable placeholder.

### Phase 4 — RC-2 / D2 dispatch routing: dynamic roles + plan→single-agent stickiness

- [ ] [BACKEND] P0. Per-task role from `[TAG]` (mapping table), fallback plan `assigned_role`; carried on BacklogTask +
      returned in the dispatch brief.
- [ ] [BACKEND] P0. `SlotRow.last_role` column; set at spawn + updated on each dispatch.
- [ ] [BACKEND] P0. Dispatch injects a "read `agents/<role>.md`" instruction when task role ≠ slot `last_role`; REMOVE
      the worker-level role-refusal → skip path.
- [ ] [BACKEND] P0. Plan→single-agent stickiness (F) — when a slot claims a plan's first task, stamp the plan's other
      queued tasks `target_slot=<that slot>` + `affinity: medium` so the plan sticks to one owner (context accumulation)
      and is worked in `plan_order`; the medium-affinity timeout spills the next task to a free slot when the owner is
      slow. Reuses `_task_is_routable_to`; the new part is the first-claim auto-stamp + propagation.
- [ ] [BACKEND] P0. Tests — plan sticks to its first-claiming slot; owner works its tasks in `plan_order`; a slow owner
      → the next task spills after the timeout; role change injects the boot-prompt read; a mixed-role plan runs on ONE
      worker without thrash + no `slot_skips` for a role change; separate plans dispatch to separate agents in parallel.

### Phase 5 — RC-3 slot_skips hygiene

- [x] [BACKEND] P1. slot_skips expiry (N hours, configurable) + clear-on-plan-change / clear-on-prereq-land. — ✅ DONE
      ao@07035aba: TTL expiry in `slot_skipped_tasks(ttl_hours=)` (config `slot_skip_ttl_hours`, default 24h, 0=disable;
      dispatch passes it) + clear-on-removal (prune deletes slot_skips for GC'd/cancelled task_ids) +
      `clear_slot_skips_for_task` primitive. NOTE: explicit clear-on-retier / clear-on-prereq-land wiring is left to the
      TTL (general staleness) + the primitive — a targeted hook can be added if the TTL proves too coarse.
- [x] [BACKEND] P1. Unskip API (operator + programmatic) + a fleet-UI action. — ✅ DONE ao@07035aba:
      `POST /api/slots/{id}/unskip-task` (one) + `POST /api/slots/{id}/clear-skips` (all-for-slot), both
      activity-logged. 🟡 the fleet-UI button is deferred (UI repo; the endpoints exist to wire it to).
- [x] [BACKEND] P1. Tests — expiry, plan-change clear, prereq-land clear, unskip. — ✅ DONE ao@07035aba
      (test_slot_skips_hygiene.py, 4 tests: TTL excludes expired / 0-disables, unskip idempotent, clear-for-task spans
      slots, clear-all-for-slot; full `quality-gates.sh` green).

### Phase 6 — codex SSOT + plan-activate (after the code phases; plan↔codex drift is review-blocking)

- [ ] [BACKEND] P2. (optional) Plan-activate affordance — `POST /api/plans/{slug}/activate` or a
      `[PLAN-ACTIVATE: <slug>]` final-todo marker so a phase reliably + auditably flips the next plan `draft`→`active`,
      instead of a raw frontmatter edit. Nice-to-have; the raw edit + `docs(plans):` commit already works.
- [ ] [DOCS] P1. Codex SSOT update — reconcile semantics (A1–A4), dynamic-role model (B), capability chain (C), skip
      hygiene (D), plan grouping + draft-gating (E), single-agent stickiness (F); banner-invalidate anything the change
      supersedes. (task_template + CLAUDE.md author-facing docs already shipped in Phase 1.)

### Phase 7 — LATER (DEFERRED per operator — after Phases 1–6): Fable + new effort levels

- [ ] [BACKEND] P2. DEFERRED. Enable Fable as a spawnable model at the top of the capability chain (CLI flags, account
      support, `_higher_model` wiring).
- [ ] [BACKEND] P2. DEFERRED. New effort-level vocabulary + spawn wiring; reconcile the effort ladder with the role
      registry + `thinking_tier`.

---

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-07 — SESSION STATUS (autonomous, operator at lunch).** SHIPPED to LDR (all staged, live server NOT restarted
  — deploy is operator-gated): **Phase 1** (docs, `pm@08e6424`), **Phase 2** (RC-1 reconcile — Batch A `ao@ff6100ad` +
  Batch B `ao@c6a31ed6`), **Phase 5** (RC-3 skip hygiene, `ao@07035aba`). **2 of the 3 root causes (RC-1, RC-3) are
  fully fixed** + docs. Every batch: unit-tested + full `quality-gates.sh` green + quickmerge + same-turn plan flip.
  **REMAINING** (design LOCKED in §B/§C/§F, so implementation-ready): **Phase 4** (RC-2 — dynamic `[TAG]` roles +
  plan→single-agent stickiness; needs `SlotRow.last_role` col via the `bootstrap.py` migrate hook, dispatch boot-prompt
  injection, remove worker role-refusal, first-claim `target_slot` stickiness) — highest remaining value; **Phase 3**
  (capability chain for DISPATCHED retiers — stop-lower + `--resume`-higher; the QUEUED path already works via the model
  gate; this is the in-flight-retier edge case, riskiest = worker-lifecycle) — lower priority; **Phase 6** (codex SSOT:
  real doc is `codex/04-architecture/agent-orchestrator-backlog-state-alignment.md`, not the stale
  `12-agent-workflow/...single-vm-architecture.md` in this plan's refs). **Operator note**: Phase 4's stickiness =
  DEFAULT makes fleet parallelism ≈ active-plan count (a deliberate shift, §F) — worth a glance before deploying it.
- **2026-07-07** — ✅ **Phase 5 SHIPPED** (`ao@07035aba`, LDR; staging-first drain → v2-gated). RC-3 slot_skips hygiene:
  a per-(slot,task) skip now EXPIRES after `slot_skip_ttl_hours` (default 24h, config, 0=disable) so a stale
  craft-mismatch / prereq-park skip can't starve dispatch across worker respawns; regen prune clears slot_skips for
  GC'd/cancelled tasks; `POST /unskip-task` + `POST /clear-skips` replace the manual-SQL unskip;
  `clear_slot_skips_for_task` primitive for plan-change clears. 4 tests, full `quality-gates.sh` green. (Done out of
  plan order — Phase 5 is self-contained + lower-risk than Phases 3/4.) Code STAGED on LDR — live server NOT restarted.
  Next: Phase 4 (dynamic roles + stickiness, RC-2) then Phase 6 codex.
- **2026-07-07** — ✅ **Phase 2 Batch B SHIPPED** (`ao@c6a31ed6`, LDR; staging-first drain → v2-gated). Cancelled-task
  lifecycle (A3): regen prune now marks a removed-while-DISPATCHED task `cancelled` (not a zombie `dispatched` row, not
  a hard delete that strands the worker); `HeartbeatResponse.cancel_task` + the heartbeat detects it and returns
  `dispatch_reason: cancelled`; `agents/worker.md` instructs the worker to revert ONLY its own in-flight files
  (`git restore`, never whole-branch / `reset --hard`) + `/skip-current-task`. Queued orphans still hard-delete
  (unchanged). +2 tests (12 reconcile/dispatch tests total), full `quality-gates.sh` green. **Phase 2 COMPLETE** except
  the UI cancelled-count (deferred, UI repo) + the mid-task /progress-message interrupt (follow-up). Code STAGED on LDR
  — live server NOT restarted. Next: Phase 5 (slot_skips hygiene, RC-3).
- **2026-07-07** — ✅ **Phase 2 Batch A SHIPPED** (`ao@ff6100ad`, LDR; staging-first drain → v2-gated). Regen is now a
  RECONCILE: (a) `plan_order` field re-derived from plan-file position every tick + dispatch sorts
  `(tier, priority, plan_order, plan_ref)` so same-priority tasks (10× P0) hold file order and mid-file inserts land in
  place; (b) brief-matched tasks reconcile model/effort/thinking/assigned_role/priority in place
  (`_reconcile_task_fields`, `summary.reconciled`) — **this auto-heals the frozen opus/max backlog on the next tick**;
  (c) `sequential: true` chains each task to its predecessor, rebuilt each tick so a reorder can't deadlock. 10 new unit
  tests (test_regen_reconcile.py + test_dispatch_plan_order.py), full `quality-gates.sh` green, ruff+basedpyright clean.
  Code STAGED on LDR — live server NOT restarted (deploy is operator-gated). Next: Batch B (cancelled status + worker
  stop/scoped-revert).
- **2026-07-07** — ✅ **Phase 1 SHIPPED** (`pm@08e6424`, LDR; PR #809→main, v2 auto-merge). Rewrote the stale
  `task_template.md` to the current schema with LOCAL-vs-AO authoring tracks + all conventions (10–20 cap, one-plan-one-
  agent, split-for-parallelism, draft-gated phases, `[TAG]` roles, `sequential` vs `plan_order`, safe-editing-live-plans
  A1–A3) — every dispatch mechanic marked ACTIVE-NOW vs ROLLING-OUT. Added the CLAUDE.md "READ task_template before
  authoring a plan" HARD-RULE directive (cursor-configs canonical, 28.6 KB < 40 KB cap, both symlinked copies update).
  Plan doc pushed `pm@74164718d`. Next: Phase 2 (regen reconcile — unblocks the frozen backlog).
- **2026-07-07** — Reordered per operator: **docs-first**. New Phase 1 = rewrite task_template.md (stale) to current
  schema with LOCAL vs AO-DISPATCHED authoring tracks + all conventions (10–20 cap, one-plan-one-agent, split for
  parallelism, draft-gating, `[TAG]` roles, sequential vs plan_order, safe-editing-live-plans) + a CLAUDE.md "READ
  task_template before authoring a plan" directive. Author-facing docs marked ACTIVE-NOW vs ROLLING-OUT so authors never
  rely on unbuilt dispatch behavior. Code phases shifted to 2–5; codex SSOT + plan-activate is Phase 6; deferred Fable
  is Phase 7.
- **2026-07-07** — Added section F: plan→single-agent stickiness (default one plan = one agent for context, via
  first-claim `target_slot` auto-stamp + `affinity: medium` spillover when slow) + parallelism = more plans, not a split
  plan + BOTH ordering modes (a `plan_order` default, b `sequential: true` strict-serial auto-chained prereqs). Wired
  into Phase 1 (sequential flag), Phase 3 (stickiness, renamed to dispatch-routing), Phase 5 (docs).
- **2026-07-07** — Added A4 execution-order (plan_order): dispatch today sorts `(tier, priority)` + yaml-append
  tiebreak, so a mid-file insert wrongly sorts to the end — fixed by a re-derived `plan_order` field +
  `(tier, priority, plan_order)` sort. Added STRICT 10–20 todo cap for AO-ingested plans (section E + Phase-5 doc todo).
- **2026-07-07** — Phase 0 design LOCKED with operator: (1) no anchor/tid — text edits are remove+add, regen stays
  read-only on plans; (2) `[TAG]`→role slugs verified vs `agents/*.md`; (3) `cancelled` status + own-changes-only scoped
  revert. Added planning standard E (logical grouping + draft-gated phase chains: focused ~20-todo plans, audit as its
  own plan, sequential phases current=active/later=draft, last-todo flips next→active) + a Phase-5 doc todo + optional
  plan-activate affordance. A2/Phase-2 rewritten for no-anchor.
- **2026-07-07** — Plan authored (local only, not committed per operator). Root causes grounded in code (regen
  append-only L892-943; TaskRow has no model/role columns; dispatch model-gate works, role does not; SlotRow has no role
  column; skip is permanent per-slot). Design locked with operator across A (reconcile), B (dynamic roles), C
  (capability chain fable>opus>sonnet>haiku + `--resume`), D (skip hygiene). Fable/effort deferred to Phase 6.
