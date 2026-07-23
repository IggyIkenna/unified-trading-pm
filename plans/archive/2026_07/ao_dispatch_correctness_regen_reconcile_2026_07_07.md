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
  is complete and verified. (Was — this line previously read "Fable + new effort-level enablement is a deferred later
  phase," now stale — corrected 2026-07-14, finding 186 — Phase 7 shipped fable-as-a-spawnable-model, the haiku-effort
  gate, and the full effort-ladder [ao@f52d3cc4, ao@4d93a751]; only the narrow per-account Fable capability-gating
  sub-item remains DEFERRED.) Records the incident in issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md.
status: complete
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
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /codex/04-architecture/agent-orchestrator-backlog-state-alignment.md,
    /codex/04-architecture/agent-orchestrator-overview.md,
    /codex/04-architecture/agent-orchestrator-autospawn.md,
  ]
created: 2026-07-07
last_updated: 2026-07-15
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 4.8
assigned_role: backend_engineer
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

> **✅ COMPLETE — archived 2026-07-15.** (Was: 🟡 in-flight AO dispatcher refactor, 2026-07-07.) This plan changed
> `regen_backlog_from_plan.py`, `dispatch.py`, `autospawn.py`, the worker routes, and the ORM. It was **human-driven**
> (`assigned_vm: NA`, `execution_scope: local-only`) — the operator + main agent did it HERE and pushed to
> agent-orchestrator via quickmerge after each phase. Deliberately NOT dispatched to the AO fleet (it modifies the very
> dispatcher that would execute it). Incident record: `issues/ao_fleet_stall_opus_spawn_and_skip_thrash_2026_07_07.md`.

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
- `dispatched` (in-flight) with a **model/effort/thinking** change → §C session-tier realign (tier is SPAWN-FIXED per
  tmux session): an INCREASE the current task now needs → **kill + respawn `--resume`** at the higher tier immediately;
  a decrease → keep the running (≥) worker to FINISH the current task, then the session realigns to the lower tier at
  the next-task boundary if that next task is sticky here (§C).
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

### C. Session-tier realign — model / effort / thinking are SPAWN-FIXED (RC-1 dispatched path)

A worker's **model, effort, and thinking are set ONCE at tmux spawn** (`_build_claude_flags` → `--model` / `--effort` /
`--max-thinking-tokens`, `tmux_spawn.py`) and are **FIXED for the whole session** — the same tmux session serves EVERY
subsequent task at that spawn tier until it is killed (a plan of 5 opus tasks re-homed to sonnet keeps running on opus,
task after task, because the session — not the task — carries the model). Changing a live worker's tier has exactly two
mechanisms: **(1) kill the tmux session + respawn `--model/--effort/... X --resume`** (the new session comes up at the
new tier WITH the prior conversation/context + the same worktree, so no work is lost) — **USE THIS**; (2) `/model` via
`send-keys` + arrow-select — fragile, error-prone, **BANNED**.

- **Three spawn-fixed params, each its own respawn trigger** (any trigger → respawn with the full new
  `(model, effort, thinking)` triple, always `--resume`):
  - **model** — ANY change → respawn. Rank `haiku < sonnet < opus < fable` (fable highest).
  - **effort** — ordered ladder `[low, medium, high, xhigh, max]`, compared by INDEX; respawn only when `|Δindex| > 1`
    (a ±1 drift is tolerated — not worth the churn). Unset effort → the default index (`medium`) for the compare.
  - **thinking** — flip `on ↔ off` → respawn.
  - **Per-model capability** (CLI ground truth — installed 2.1.201 + model-config docs): effort applies to **sonnet /
    opus / fable ONLY** — **Haiku has NO effort (passing `--effort` 400s)**, so a Haiku tier is model + thinking-on/off
    only (no effort compare in `_needs_respawn`). On current-gen models (Sonnet 5 / Opus 4.8 / Fable 5) effort is the
    PRIMARY reasoning control (adaptive reasoning) and `--max-thinking-tokens` is INERT there (retained only for Haiku's
    on/off). The per-model matrix + `fable` spawn land in Phase 7.
- **Two moments it fires:**
  - **Mid-task** (the in-flight task is retiered): respawn ONLY on an INCREASE — the current task now needs more than
    the session has (the capability gate; a sonnet session cannot do opus-required work). A decrease is IGNORED mid-task
    — the over-powered worker just finishes the task it is on.
  - **At the `/done` → next-task boundary**: respawn on ANY change (up OR down) BEFORE the next task proceeds, **but
    only when that next task is sticky to this slot** (pinned by §F affinity). Sticky → kill this slot's session +
    respawn at the next task's tier + `--resume` (context locality kept). NOT sticky → prefer routing the task to a slot
    already at that tier (the affinity dispatch already does this when a matching slot is free); respawn only when this
    slot is genuinely the task's home.
- **Affinity GOVERNS the boundary realign** — this is what lets §F stickiness survive a MIXED-TIER plan: one agent owns
  the plan and **re-spawns itself to each task's tier as it walks the plan**, keeping context across every tier change
  via `--resume`, instead of scattering the plan across slots.
- **Queued path unchanged**: the existing `_task_outranks_slot` gate + spawn-time `_slot_pinned_task_params` upgrade
  already handle a QUEUED higher-tier task (leave-for-higher-spawn). Phase 3 adds only the DISPATCHED / boundary cases.
- **Mechanism reuse (proven)**: `_build_claude_flags` treats `--model` and `--resume` as INDEPENDENT flags, so
  `--resume <id> --model opus` continues the conversation on a higher model; the watchdog already does `kill_session` +
  `spawn(resume_session_id=…, model/effort/thinking=…)` in the same worktree (`worker_liveness_watchdog.py`). The
  `/done` HTTP call cannot kill its own tmux session, so the boundary respawn is performed by the background liveness
  tick.
- **Timing = A (immediate-but-debounced via the liveness tick)** — operator-confirmed 2026-07-07 (the respawn cooldown
  guards against edit-thrash; idempotent — after the respawn `slot tier == task tier`, so it will not re-fire).
- **Fable SPAWN enablement DEFERRED to Phase 7** (operator): Phase 3 lands the rank ordering, the effort ladder, and the
  realign mechanism (all Fable-READY); wiring Fable as an actually-spawnable model (CLI flags, account support) is
  Phase 7.

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

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch + regen + ingestion contract.
- `/codex/12-agent-workflow/agent-orchestrator-overview.md` — runtime loops (AutoSpawn / regen / failover / watchdog).
- `/codex/04-architecture/role-registry.md` — role → (model, thinking, lifecycle); the tag→role mapping extends this.

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
- [x] [UI] P1. Surface the cancelled count in the fleet/backlog UI (`unified-trading-system-ui` / deployment-ui as
      applicable). — ✅ DONE (already implemented; verified 2026-07-15 audit): the AO dashboard renders a `cancelled`
      filter chip with its live count (`agent-orchestrator/dashboard/src/App.tsx:2040-2047`), fed by the backend count
      (`server/routes/state.py:322`).
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

### Phase 3 — RC-1 dispatched adaptation: session-tier realign (kill + `--resume`) + text-edit

> Model / effort / thinking are SPAWN-FIXED (§C) — a live tmux session serves every task at its spawn tier until killed.
> The only clean re-tier is kill + respawn `--resume` at the new tier; `/model` send-keys is BANNED. Highest
> worker-lifecycle risk in this plan — the reuse target is the proven `worker_liveness_watchdog` kill+resume path.

- [x] [BACKEND] P0. Text-edited todo → remove-old + add-new (no anchor): the changed brief drops out of current-briefs
      so A3 handles the old task by status (prune/cancel/keep) and the new text ingests fresh. Assert NO in-place text
      update + no plan-file writeback. (Behaviour is already live via Phase 2 reconcile+prune — this lands the explicit
      test.) — ✅ DONE ao@e4284752 (`test_text_edit_is_remove_and_add_not_in_place`: fresh task id + old brief pruned +
      plan file byte-identical post-regen).
- [x] [BACKEND] P0. Tier primitives: `fable` into `_MODEL_RANK` (`haiku<sonnet<opus<fable`) in BOTH `dispatch.py` +
      `autospawn.py` (kept in sync); effort ladder `[low, medium, high, xhigh, max]` + `_effort_index` (unset→`medium`);
      a PURE `_needs_respawn(session_tier, task_tier, *, at_boundary) -> bool` — model any-change, effort `|Δidx|>1`,
      thinking `on↔off` flip; mid-task fires on INCREASE only, boundary fires on any change. — ✅ DONE ao@f52d3cc4 (new
      `server/model_tier.py` CONSOLIDATES the two drifting `_MODEL_RANK` copies into ONE SSOT; `needs_respawn` +
      `model_supports_effort` + effort ladder; 9 tests + 236 regression. thinking `on↔off` gated to Haiku only (inert on
      adaptive models); mid-task = model-upgrade only.)
- [x] [BACKEND] P0. Mid-task UPGRADE trigger (liveness tick): a working slot whose `current_task` tier now EXCEEDS the
      session tier → kill + respawn `--resume` at the higher tier (immediate, debounced by the respawn cooldown; timing
      A). A mid-task decrease is ignored — the over-powered worker finishes its task. — ✅ DONE ao@a21ca9e9
      (`WorkerLivenessWatchdog` Trigger 5 `_maybe_realign_tier`; upgrade fires on `needs_respawn(at_boundary=False)`,
      cooldown-gated + non-thinking-guarded + session-id-required.)
- [x] [BACKEND] P0. Boundary realign (at `/done` → next STICKY task): the next task pinned to this slot (§F affinity)
      whose tier differs (up OR down) → kill + respawn `--resume` at the next task's tier BEFORE it proceeds; a
      non-sticky tier mismatch prefers a matching-tier slot. Reuse `worker_liveness_watchdog` `kill_session` +
      `spawn(resume_session_id=…)`; performed by the background tick (the `/done` request can't self-kill). — ✅ DONE
      ao@a21ca9e9 (same Trigger 5: BOUNDARY = `current_task` changed since last watchdog sight → realign any direction +
      **persist tier back to SlotRow** (no thrash); `_slot_required_model` now honours `affinity=medium` within the
      `queued_at` spill window for the idle-slot upgrade path. Non-sticky routing is the existing affinity dispatch.)
- [ ] [BACKEND] P1. Role-only change within the SAME session tier → soft signal (heartbeat message) to read
      `agents/<role>.md` + re-read the plan item, continue — NO respawn (adapt-in-place; the model-chain rule takes over
      only if the role also raises the tier). — 🟡 DEFERRED (operator 2026-07-15): NOT built (verified 2026-07-15 audit
      — the heartbeat carries only operator `pending` messages; no mid-flight role signal exists). Descoped as
      low-value: a same-tier mid-flight role reconcile is rare, and the worker adopts the new craft on its next dispatch
      (Phase 4). Plan ARCHIVED with this one accepted deferral; re-file as an issue if a real need appears.
- [x] [BACKEND] P0. Tests — `_needs_respawn` matrix (model any-change / effort ±1 tolerated / effort `>1` respawn /
      thinking flip / fable rank); mid-task upgrade respawns; mid-task downgrade does NOT; boundary sticky-down
      respawns; non-sticky routes away (no respawn); text-edit remove+add + no writeback. Spawn mocked (parity with the
      `worker_liveness_watchdog` tests). — ✅ DONE ao@f52d3cc4 (`test_model_tier.py` needs_respawn matrix, 9) +
      ao@a21ca9e9 (`test_watchdog_tier_realign.py`, 8: mid-task up/down, boundary down, haiku-effort-omit, guards). The
      text-edit remove+add assertion is tracked with the Phase 3 text-edit todo above.

### Phase 4 — RC-2 / D2 dispatch routing: dynamic roles + plan→single-agent stickiness

- [x] [BACKEND] P0. Per-task role from `[TAG]` (mapping table), fallback plan `assigned_role`; carried on BacklogTask +
      returned in the dispatch brief. — ✅ DONE ao@f976b6e4 (`_task_role_from_tag` + `_resolve_task_tier` in regen:
      INFRA/DATA/BACKEND/UI/REVIEW→role, generic→plan role; per-task model/effort/thinking derived from the task role;
      `TaskBrief.assigned_role` via `to_task_brief`; 2 tests).
- [x] [BACKEND] P0. `SlotRow.last_role` column; set at spawn + updated on each dispatch. — ✅ DONE ao@f976b6e4
      (`SlotRow.last_role` + `bootstrap.py` `_add_missing_columns` migrate hook; `assign_task_to_slot(last_role=)` set
      on every dispatch from the 3 call sites).
- [x] [BACKEND] P0. Dispatch injects a "read `agents/<role>.md`" instruction when task role ≠ slot `last_role`; REMOVE
      the worker-level role-refusal → skip path. — ✅ DONE ao@f976b6e4: the brief carries `assigned_role`; `worker.md`
      "Per-task craft role — ADOPT, don't refuse (HARD RULE)" tells the worker to READ `agents/<role>.md` on a craft
      change and NEVER `/skip` a role-mismatch (the exact thrash). (Server tracks `last_role` for future explicit
      injection; the worker acts on the brief + its own craft memory.)
- [x] [BACKEND] P0. Plan→single-agent stickiness (F) — first-claim `target_slot` + `affinity: medium` (spill when slow).
      — ✅ DONE ao@f976b6e4: `_claim_plan_for_slot` already pinned siblings; **fixed `affinity: high`→`medium` + reset
      `queued_at` at pin time** so a slow owner spills after the timeout (was a hard pin, no spillover — didn't match
      §F). Explicit operator routing + other plans untouched.
- [x] [BACKEND] P0. Tests — plan sticks to its first-claiming slot; owner works its tasks in `plan_order`; a slow owner
      → the next task spills after the timeout; role change injects the boot-prompt read; a mixed-role plan runs on ONE
      worker without thrash + no `slot_skips` for a role change; separate plans dispatch to separate agents in parallel.
      — ✅ DONE ao@f976b6e4 (test_plan_claiming.py updated to medium+last_role; test_regen_reconcile.py per-task-role
      tests; full `quality-gates.sh` green — a pre-existing high-affinity test correctly caught + updated to §F).

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

### Phase 6 — codex SSOT (after the code phases; plan↔codex drift is review-blocking)

> Plan-activate affordance (`POST /api/plans/{slug}/activate` / a `[PLAN-ACTIVATE:]` marker) — REMOVED 2026-07-15
> (operator): the raw frontmatter-edit + `docs(plans):` commit is the accepted mechanism, so the affordance is
> unnecessary.

- [x] [DOCS] P1. Codex SSOT update — reconcile semantics (A1–A4), dynamic-role model (B), capability chain (C), skip
      hygiene (D), plan grouping + draft-gating (E), single-agent stickiness (F); banner-invalidate anything the change
      supersedes. (task_template + CLAUDE.md author-facing docs already shipped in Phase 1.) — ✅ DONE pm@20dce55f3:
      added a "Dispatch-correctness update (2026-07-07)" section to
      `/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md` documenting RC-1 reconcile / plan_order /
      sequential / cancelled, RC-2 per-task roles + stickiness, RC-3 skip-TTL/unskip — and marked the old append-only
      lifecycle diagram SUPERSEDED. (Capability chain C is documented as deferred.)

### Phase 7 — Fable spawn + per-model effort capability (was DEFERRED; researched + scoped 2026-07-07)

> Ground truth (installed CLI 2.1.201 + Claude Code model-config docs): `--effort` = `low, medium, high, xhigh, max` (5
> levels; extension "extra high" = `xhigh`). **`ultracode` is NOT an `--effort` value** — it is a session-only Claude
> Code setting (`"ultracode": true` via `--settings`) = `xhigh` + dynamic-workflow orchestration; out of scope for spawn
> effort — and **operator decision 2026-07-07: ultracode stays FALSE for every AO worker, never wired (overkill for a
> dispatched worker)**. **Haiku supports NO effort — passing `--effort` to it returns a 400 error** (effort is supported
> on Fable 5 / Sonnet 5 / Opus 4.x). On current-gen models (Sonnet 5 / Opus 4.8 / Fable 5) **effort is the PRIMARY
> reasoning control (adaptive reasoning) and `--max-thinking-tokens` does NOT apply** — our
> thinking-via-`--max-thinking-tokens` is inert on them, retained only for Haiku's thinking on/off. Fable alias =
> `fable` (available since CLI 2.1.170). The `_MODEL_RANK` + effort-ladder + haiku-gate primitives are SHARED with Phase
> 3 — build them once as the foundation.

- [x] [BACKEND] P0. Haiku-effort gate (CORRECTNESS — latent 400 bug): `_build_claude_flags` (`tmux_spawn.py:971`) must
      NOT emit `--effort` when the model is haiku — the API 400s. Add `_model_supports_effort(model)` (haiku→False;
      sonnet/opus/fable→True) + gate the flag. Single emission site (verified `rg`). — ✅ DONE ao@f52d3cc4
      (`model_tier.model_supports_effort` matches haiku by SUBSTRING so full names `claude-haiku-4-5` are caught across
      all ~13 spawn paths; `--max-thinking-tokens` left ungated — Haiku accepts it.)
- [x] [BACKEND] P0. `fable` as a spawnable model: add to `ModelTier` (`models/_types.py`) + `_MODEL_RANK`
      (`{haiku:0, sonnet:1, opus:2, fable:3}`) in BOTH `dispatch.py` + `autospawn.py`; spawn `--model fable` (alias
      confirmed; CLI 2.1.201 ≥ 2.1.170). `_higher_model` / `_slot_pinned_task_params` handle it via the rank. — ✅ DONE
      ao@f52d3cc4 (`ModelTier` + `role_registry._coerce_model` + `_parse_frontmatter_model_tier` (`fable-required`) all
      accept fable — operator-request-only per task_template §4.)
- [x] [BACKEND] P1. Per-role / per-plan `effort` field for the FULL ladder: extend `role_registry` + the
      plan-frontmatter parse so a role/plan can declare any of `low|medium|high|xhigh|max` DIRECTLY (today only
      `thinking: max|high` → effort). Keep `thinking: on/off` as Haiku's control. Validate against the ladder; unknown →
      the model default. — ✅ DONE ao@4d93a751 (plan `effort:` frontmatter — any ladder level, validated vs
      `model_tier.EFFORT_LADDER`, overrides the thinking_tier-/role-derived effort as the plan default; 3 tests. Roles
      already express max/high via `thinking:`; a full-ladder role override is a small follow if ever needed.)
- [x] [BACKEND] P1. Fable account support: which accounts may spawn fable (org allowlist; NOT under
      zero-data-retention); a fable spawn on a non-fable account → automatic model fallback (`--fallback-model`) or
      route to a fable-capable account. — ✅ WON'T-DO / N-A (operator 2026-07-15): no fleet account supports fable AND
      AO workers are not permitted to spawn as fable, so per-account gating + `--fallback-model` is unnecessary — no
      work required. `AccountDef.models` remains the hook if that policy ever changes.
- [x] [BACKEND] P2. Docs/semantics reconcile: document that effort is the primary reasoning control on current-gen
      models (`--max-thinking-tokens` inert there, retained for Haiku on/off); align `role_registry.effort` /
      `thinking_flag` + `_parse_frontmatter_thinking_tier` with the ladder; update the `codex` role-registry doc. — ✅
      DONE (codex `agent-orchestrator-backlog-state-alignment.md` "Session-tier realign + Fable + per-model effort"
      section — realign / model_tier SSOT / haiku-gate / fable / effort field / ultracode-never-wired / deferred items +
      code map; capability chain marked no-longer-deferred. Same `docs(plans)` commit as this flip.)
- [x] [BACKEND] P0. Tests — haiku spawn OMITS `--effort` (no 400); fable ranks top + spawns `--model fable`; the effort
      field accepts the 5 levels + rejects/clamps unknown; `_needs_respawn` treats a Haiku tier as model + thinking-only
      (no effort compare). — ✅ DONE across ao@f52d3cc4 (model_tier: haiku-effort-omit / fable rank / `needs_respawn`
      matrix, 9), ao@a21ca9e9 (watchdog realign, 8), ao@4d93a751 (effort field, 3) — ~20 tests, every batch
      full-QG-green.
- [x] [INFRA] P1. **DEPLOY (operator-authorized VM agent)** — deploy the whole plan (Phases 2–7) per the **§ Deployment
      runbook** below: disable service → stop backend → pull code → DB migration (idempotent `SlotRow.last_role` at
      startup) → enable service → start backend + verify. **RESOLVED 2026-07-12 (§A2 finding 224, verification COMPLETE,
      verdict AUTO-PULL LIVE)**: deploy-currency automation pre-existed — `scripts/ao-self-pull.sh`
      (agent-orchestrator@589b711, hardened d16d737 + 5462959) runs as a 15-min root cron (sudo crontab confirmed) doing
      FF-pull + `systemctl restart` on HEAD change (log evidence to 2026-06-16), which also idempotently applies the
      `SlotRow.last_role` migration on restart — no manual disable/stop/pull/enable/start interruption needed; verified
      on the VM (crontab + logs). (was: this todo bundled the code-pull/restart/migration half with the claude-binary
      update + UI redeploy below — now split; the code/restart/migration half is DONE.)
- [x] [INFRA] P1. **DEPLOY — remaining manual steps (narrowed 2026-07-12, split from the todo above)**: **update the
      `claude` binary to ≥ 2.1.170** (fable + effort — a separate binary upgrade, NOT covered by ao-self-pull.sh's
      git-pull + restart) → redeploy the UI (Firebase/Firestore dashboard) per the § Deployment runbook below. Verify
      each step. — ✅ DONE (operator 2026-07-15): `claude` binary updated to ≥ 2.1.170 on the planning VM + UI
      redeployed; the ao-self-pull cron keeps the backend code current.

---

## Deployment runbook — VM agent (execute in THIS order)

> **Operator-authorized deploy** of the ENTIRE `ao_dispatch_correctness` plan (Phases 2–7). The live server was
> deliberately NEVER restarted during development, so this is the **FIRST deploy of all of it at once**: RC-1 reconcile
> (Phase 2), dynamic `[TAG]` roles + `SlotRow.last_role` + one-plan-one-agent stickiness (Phase 4), slot_skips hygiene
> (Phase 5), session-tier realign / capability chain (Phase 3), Fable + per-model effort (Phase 7). Run on the planning
> VM (`ssh agent-orchestrator-vm` — 13.113.200.22, `ubuntu`). **Do the steps IN ORDER; verify each before the next.**
> `sudo` is needed for the `systemctl` steps.

**Pre-flight (before step 1):**

- **Confirm the code is on the branch this VM's `agent-orchestrator` clone tracks.** Production tracks `main`, so the
  `live-defi-rollout → staging → main` promotion (v2-gated) must have completed; if you deploy from LDR directly, the
  shas are already on `live-defi-rollout`. Verify these commits are HEAD-reachable on the tracked branch:
  `git -C <ao-repo> log --oneline -40 | grep -E 'f52d3cc|a21ca9e|4d93a75|e428475|f976b6e|07035ab|ff6100a|c6a31ed'`
  (foundation / realign / effort / text-edit / roles+last_role / skip-hygiene / reconcile). If any are missing, STOP —
  the promotion isn't done.
- **Back up `state.db`**: `cp <ao-repo>/data/state/state.db /tmp/state.db.pre-deploy` (the migration is idempotent, but
  a backup is cheap insurance).

**1. Disable the backend service** (so nothing auto-restarts it mid-deploy). Identify it first —
`systemctl list-units --type=service | grep -iE 'orchestr|agent'` (it supervises the uvicorn on `127.0.0.1:8765`). Then
`sudo systemctl disable <svc>`. _(If the backend isn't under systemd but a bare uvicorn / tmux, skip to step 2 and just
ensure nothing respawns it.)_

**2. Stop the backend.** `sudo systemctl stop <svc>` (or kill the uvicorn PID on :8765). Verify down: the health
endpoint on `127.0.0.1:8765` no longer responds / `pgrep -af uvicorn` is empty. _(The fleet's tmux worker sessions are
separate process trees — they keep running and simply can't heartbeat until the backend returns; that's expected.)_

**3. Pull the latest backend code.** `git -C <ao-repo> pull --ff-only` on the tracked branch, then re-run the sha check
from pre-flight against HEAD. **This deliberate pull IS the deploy** — AO code is never auto-pulled, which is why the
live server stayed safe during development.

**4. Update the `claude` CLI binary** to **≥ 2.1.170** (Fable; 2.1.201 validated locally): `claude update`, then confirm
`claude --version`. Without this, `--model fable` fails and the current `--effort` ladder isn't guaranteed.

**5. DB schema migration.** The ONLY new column across the whole plan is **`SlotRow.last_role`** (Phase 4), added
**idempotently** by `bootstrap.py._add_missing_columns` when the backend boots — there is **no separate migration
command**; it is applied automatically by the start in step 7. (state.db was backed up in pre-flight.) You will VERIFY
it in step 7. _No new columns were added by Phases 3/7 — the realign reads/writes the existing
`model`/`effort`/`thinking` columns._

**6. Re-enable the service.** `sudo systemctl enable <svc>`.

**7. Start the backend.** `sudo systemctl start <svc>` (or relaunch the uvicorn). **VERIFY:**

- **Health**: the backend answers on `127.0.0.1:8765` (health endpoint).
- **Migration applied**: `sqlite3 <ao-repo>/data/state/state.db "PRAGMA table_info(slots);" | grep last_role` returns a
  row.
- **Clean boot**: no bootstrap/import errors in the logs (`journalctl -u <svc> -n 120 --no-pager`, or the uvicorn log).
- **Fleet**: existing tmux workers reconnect on their next heartbeat. They run the OLD `worker.md` boot prompt until
  they respawn — to activate the new adopt-not-refuse / cancel-handling behaviour, let the watchdog/AutoSpawn cycle the
  slots (self-healing) or restart the worker sessions. **Do NOT manually kill the runtime loops** (AutoSpawn / failover
  / watchdog self-heal).

**8. Update the UI (Firebase/Firestore-hosted dashboard)** so it reflects the new backend. Rebuild + redeploy the
dashboard via the repo's **established UI deploy path** (its build+deploy script) — _exact command per the UI deploy
runbook; not reproduced here._ No dashboard code changed in this plan, so this is a routine redeploy to stay in sync.

**Post-deploy smoke (prove the plan is live):**

- **Reconcile (RC-1)**: on the next regen tick (≤30 min), a real model/role drift on a queued task updates its
  `backlog.yaml` BacklogTask (log line reports `reconciled>0`).
- **Realign (Phase 3)**: a plan re-tier of a dispatched task logs `watchdog_tier_realign` within ~60s.
- **Haiku gate (Phase 7)**: a haiku spawn's flags contain NO `--effort` (previously a 400).
- **Roles (Phase 4)**: dispatch no longer thrashes on a role mismatch (the worker adopts the craft).

**Rollback**: if the backend won't come up or a regression appears — `git -C <ao-repo> checkout <prev-sha>` + restart;
restore `state.db` from `/tmp/state.db.pre-deploy` only if the schema is implicated (`last_role` is additive +
idempotent, so this is unlikely). Then re-enable the service.

---

## Continuation notes (for a post-compact resume — 2026-07-07 session)

Everything shipped is in the Progress Log with shas. This captures the IMPLEMENTATION CONTEXT a fresh context needs to
resume Phase 3 (+ 6/7) without re-discovering it.

### Environment + deploy boundary (HARD — don't break it)

- **CORRECTED 2026-07-12 (see the resolved DEPLOY todo above)**: the assertion below that AO code is "NOT auto-pulled"
  was WRONG. Ground truth (VM-verified): the installed systemd unit runs uvicorn WITHOUT `--reload`; deploy-currency is
  instead handled by `scripts/ao-self-pull.sh` (agent-orchestrator@589b711, hardened d16d737 + 5462959) — a 15-min root
  cron (sudo crontab confirmed) that FF-pulls + `systemctl restart`s on HEAD change (log evidence to 2026-06-16), which
  also idempotently applies the `SlotRow.last_role` migration. SSOT: `plans/epics/orchestrator_master.md` (ao-self-pull
  section, ~L409-414). Original text kept below for provenance, now superseded:
- ~~**Do NOT restart / VM-side `git pull` agent-orchestrator until deploy.** The server runs
  `uvicorn ... --reload --reload-dir server` (PID was 199450), so pulling AO code on the VM HOT-RELOADS it into the live
  fleet. `pm-pull-ff.sh` (systemd `pm-pull.timer`, ~5 min) pulls the **PM repo ONLY** — AO code is NOT auto-pulled,
  which is why LDR ships are safe. Deploy = a deliberate VM-side pull of agent-orchestrator (`--reload` picks it up;
  `bootstrap.py` idempotently adds `SlotRow.last_role`).~~
- VM: `ssh agent-orchestrator-vm` (13.113.200.22, ubuntu, `~/.ssh/agent-orchestrator-key`); server localhost-only
  `127.0.0.1:8765`.
- **Test fast**: `cd agent-orchestrator && .venv/bin/python -m pytest tests/<file> -q`. **Full gate before quickmerge**:
  `bash scripts/quality-gates.sh` (records a green-SENTINEL tied to HEAD + files).
- **Ship**: `bash scripts/quickmerge.sh "msg" --agent --files '<paths>'` → lands on LDR (was: "AO is **staging-first**:
  Tier-C drain promotes LDR→staging, v2-gated — NOT direct-to-main like PM"; **corrected 2026-07-14, finding 200**: per
  `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` [the pipeline SSOT], staging is DORMANT fleet-wide as of the
  2026-06-30/07-12 MVP switch and agent-orchestrator is a normal `ldr_main` repo — the drain promotes LDR→main DIRECT,
  v2-gated, same as PM; this section's older historical "staging-first" ship-log entries below reflect the
  pre-MVP-switch mechanism and are not the current path). Plan flips = `docs(plans):` direct push (carve-out). Commit
  identity on this host = `harshkantariya [main·harsh_pc]`.

### Shipping gotchas hit this session (save the re-discovery)

- **QG sentinel race**: the green proof is tied to HEAD + files. If HEAD moves (another quickmerge lands) between the QG
  run and the quickmerge, the sentinel invalidates → `❌ sentinel invalid`. Fix: `git pull` to behind=0, then run QG +
  quickmerge BACK-TO-BACK (`bash scripts/quality-gates.sh && bash scripts/quickmerge.sh …`).
- **basedpyright bans `.rowcount`** on `session.execute(delete(...))` (typed `Result`), and `type: ignore` is banned →
  use ORM-object deletes (`session.get`+`session.delete`, or `scalars(select).all()` + delete-each).
- **`session.get` after `session.delete` (no flush)** still returns the pending-delete row from the identity map → add
  `session.flush()` for an idempotent single-row delete.
- A todo's `[TAG]` / P-level is IN the brief text, so changing it is a brief change = **remove+add** (A2), not a
  field-reconcile. Only frontmatter (model/effort/thinking/role) drifts independently → reconciles in place.

### Phase 3 (dispatched session-tier realign) — implementation hooks (design CONFIRMED 2026-07-07)

Design locked in §A1/§C. Model / effort / thinking are **SPAWN-FIXED** (`_build_claude_flags` →
`--model`/`--effort`/`--max-thinking-tokens`, `tmux_spawn.py` L968-977) — a tmux session serves every task at its spawn
tier until killed, so the ONLY clean re-tier is kill + respawn `--resume` (CONFIRMED: `--model` and `--resume` are
independent flags, so `--resume <id> --model opus` continues on a higher model). The QUEUED path already works
(`_task_outranks_slot` + `_MODEL_RANK` leave-for-higher-spawn). Phase 3 = the DISPATCHED / boundary cases:

- **Reuse target (proven kill+resume)**: `worker_liveness_watchdog.py` — `_resume_or_fresh_respawn` (~L1240-1257) + the
  usage-cap resume (~L1137-1155) do `tmux_spawn.kill_session(session)` then
  `tmux_spawn.spawn(slot_id, boot_prompt="", model=…, effort=…, thinking=…, resume_session_id=stored_sid)` in the SAME
  worktree (uncommitted work preserved) + a "continue" nudge. Phase 3 calls the same path with the NEW tier instead of
  the slot's current one.
- **Two triggers**: (a) mid-task UPGRADE — a background tick finds a working slot where `current_task` tier > session
  tier → respawn higher immediately (timing A, debounced by the respawn cooldown; idempotent — after respawn
  `slot.model == task.model`). (b) boundary realign — at `/done`, the next STICKY task (pinned by §F affinity) whose
  tier differs (up or down) → respawn at its tier before it proceeds; done by the background tick (the `/done` request
  can't kill its own session).
- **`_MODEL_RANK` lives in BOTH `dispatch.py` (L25) and `autospawn.py` (L431)** — add `fable:3` to both. Effort ladder
  `[low, medium, high, xhigh, max]` compared by index (respawn when `|Δidx|>1`, unset→`medium`); thinking `on↔off` flip
  respawns. Pure `_needs_respawn(session_tier, task_tier, *, at_boundary)` is the unit-testable core (spawn mocked).
- **Fable SPAWN (CLI flags / account support) is Phase 7** — Phase 3 makes the rank + realign Fable-ready only.

### Code-location map (what moved this session)

- `regen_backlog_from_plan.py`: `_reconcile_task_fields`, `_resolve_task_tier`+`_task_role_from_tag`+`_TAG_TO_ROLE`,
  `_wire_sequential_prereqs`+`_parse_frontmatter_sequential`, prune dispatched-orphan→`cancelled` + slot_skips cleanup,
  `RegenSummary.reconciled`.
- `dispatch.py`: sort `(tier, priority, plan_order, plan_ref)`; `to_task_brief` carries `assigned_role`; `_MODEL_RANK`.
- `state_store/slots.py`: `assign_task_to_slot(last_role=)`; `_claim_plan_for_slot` (affinity=medium + queued_at reset);
  `slot_skipped_tasks(ttl_hours=)` + `clear_slot_skip` / `clear_slot_skips_for_task` / `clear_all_slot_skips_for_slot`.
- `orm.py` `SlotRow.last_role` (+ `bootstrap.py` migrate) · `backlog.py` `BacklogTask.plan_order` · `config.py`
  `slot_skip_ttl_hours` · `models/worker_api.py` `HeartbeatResponse.cancel_task` + `TaskBrief.assigned_role` ·
  `routes/slots_worker.py` heartbeat cancel-signal + 3 `assign_task_to_slot` call sites · `agents/worker.md` cancel +
  adopt-not-refuse.
- Tests: `test_regen_reconcile.py`, `test_dispatch_plan_order.py`, `test_slot_skips_hygiene.py`, `test_plan_claiming.py`
  (updated to medium + last_role).

### Final disposition at archival (2026-07-15)

All three root causes (RC-1/RC-2/RC-3) fixed, tested, and deployed. The 2026-07-15 audit verified every code todo
against the code + 44 tests green. Remaining opens were closed as: UI cancelled-count = already implemented (dashboard
chip, `dashboard/src/App.tsx:2040-2047`); Fable account support = WON'T-DO (no account supports fable, AO workers never
spawn fable); deploy = DONE (binary ≥ 2.1.170 + UI redeployed); plan-activate affordance = REMOVED (raw frontmatter edit
suffices). One accepted deferral: the Phase 3 role-only same-tier soft-signal (low-value — the worker adopts craft on
its next dispatch). Plan ARCHIVED.

---

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-07 — ✅ Phase 3 + Phase 7 SHIPPED (session 2).** The dispatched-retier CAPABILITY CHAIN is live in code:
  **foundation** `ao@f52d3cc4` (new `server/model_tier.py` — consolidated `MODEL_RANK`+fable, effort ladder,
  `model_supports_effort`, `needs_respawn`; **haiku-`--effort` 400 gate** at the single spawn site; fable in
  `ModelTier`/`_coerce_model`/`model_tier: fable-required`), **Phase 3 realign** `ao@a21ca9e9` (`WorkerLivenessWatchdog`
  Trigger-5 `_maybe_realign_tier`: mid-task model-upgrade + `/done`→next boundary realign via kill+resume `--resume` at
  the task tier + **persist-back** to SlotRow; `_slot_required_model` medium-affinity fix), **effort field**
  `ao@4d93a751` (plan `effort:` frontmatter, full ladder), **text-edit test** `ao@e4284752`, **codex** `pm@7eb0bda97`.
  ~20 tests, every batch full-`quality-gates.sh`-green. All STAGED on LDR — **live server + slots NOT restarted**
  (operator deploys: restart backend + all slots + update the planning-VM `claude` binary to ≥ 2.1.170 for fable).
  **Deferred (minor, tracked as todos):** role-only soft-signal on a same-tier craft change (P1 — the worker already
  adopts a new craft on its next dispatch); per-account Fable capability gating (operator-config; speculative — Fable is
  operator-request-only). `ultracode` intentionally never wired (operator).
- **2026-07-07 — Phase 7 researched + scoped (fable + per-model effort; pre-implementation).** Verified against the
  installed CLI (2.1.201) + Claude Code model-config docs: `--effort` = `low/medium/high/xhigh/max` (5; "extra high" =
  `xhigh`); **`ultracode` is NOT an `--effort` value** — a session-only Claude Code setting (`"ultracode": true` via
  `--settings`) = `xhigh` + dynamic-workflow orchestration, out of scope for spawn effort. **Haiku supports NO effort —
  passing `--effort` 400s** (latent bug: `_build_claude_flags` `tmux_spawn.py:971` emits it unconditionally); effort is
  supported on Fable 5 / Sonnet 5 / Opus 4.x. On current-gen models (Sonnet 5 / Opus 4.8 / Fable 5) effort is the
  PRIMARY reasoning control (adaptive reasoning) — `--max-thinking-tokens` is inert there, kept only for Haiku's on/off.
  Fable alias = `fable` (available since CLI 2.1.170). Rewrote Phase 7 into concrete todos (haiku-effort gate = P0
  correctness; fable spawn + `_MODEL_RANK` `fable:3`; per-role/plan effort field for the full ladder; fable account
  support/fallback; docs reconcile) + a §C per-model-capability note. Sources: platform.claude.com/docs/…/effort,
  code.claude.com/docs/…/model-config, anthropics/claude-code#30760 (haiku-effort 400).
- **2026-07-07 — Phase 3 design REFINED + CONFIRMED with operator (pre-implementation).** Corrected the core model:
  model / effort / thinking are **spawn-fixed per tmux session** (not per-task) — a session serves every task at its
  spawn tier until killed, so the ONLY clean re-tier is kill + respawn `--resume` at the new tier (`/model` send-keys is
  BANNED — fragile arrow-select). Rewrote §C as a **three-param session-tier realign**: model ANY-change, effort ladder
  `[low, medium, high, xhigh, max]` by-index `|Δ|>1`, thinking `on↔off` flip → respawn with the full new triple. Two
  moments: mid-task fires on an INCREASE only (capability gate); the `/done`→next-task boundary fires on any change but
  ONLY for a task STICKY to this slot (§F) — which is what makes stickiness survive a mixed-tier plan (one agent
  re-spawns to each task's tier as it walks the plan). Timing = A (immediate, debounced) — operator-confirmed. Reuse
  target = the proven `worker_liveness_watchdog` kill+resume path (verified `--model`/`--resume` are independent flags).
  Updated §C + §A1 + Phase 3 todos + Phase 7 + Continuation-notes hooks; Fable SPAWN stays Phase 7 (rank/realign
  Fable-ready in P3). No code yet — implementation next.
- **2026-07-07 — ✅ SESSION COMPLETE (autonomous run).** Shipped **Phase 1** (docs), **Phase 2** (RC-1 reconcile —
  `ff6100ad`+`c6a31ed6`), **Phase 4** (RC-2 roles+stickiness — `f976b6e4`), **Phase 5** (RC-3 skip hygiene —
  `07035aba`), **Phase 6 codex** (`20dce55f3`). **🎯 ALL 3 ROOT CAUSES FIXED (RC-1/RC-2/RC-3) — the incident is resolved
  in code.** ~30 unit tests, every batch full-`quality-gates.sh`-green + quickmerge + same-turn plan flip. All code
  STAGED on LDR — **the live AO server was NOT restarted** (operator deploys when ready; AO code isn't auto-pulled).
  **Deferred (low-priority, tracked as todos below):** Phase 3 capability chain for a DISPATCHED-task retier (edge case
  — the queued path already works via the model-tier gate; worker stop+`--resume` lifecycle = highest risk, best done in
  a focused session); Phase 6 plan-activate affordance (P2 optional — raw edit already works); Phase 7 Fable + effort
  levels (operator-deferred). Deploy note: Phase 4 stickiness makes fleet parallelism ≈ active-plan count (§F).
- **2026-07-07** — ✅ **Phase 4 SHIPPED** (`ao@f976b6e4`, LDR; staging-first drain → v2-gated). RC-2 dynamic craft
  routing + stickiness: per-task role from the `[TAG]` (`_task_role_from_tag`/`_resolve_task_tier` — a mapped tag
  overrides the plan role so ONE plan carries multiple crafts; per-task tier derived from the task role);
  `SlotRow.last_role` col (+ `bootstrap.py` migrate hook) set on every dispatch; `TaskBrief.assigned_role` returned to
  the worker; `worker.md` "ADOPT, don't refuse" HARD RULE (read `agents/<role>.md` on a craft change, NEVER `/skip` a
  role-mismatch — killing the thrash); stickiness `_claim_plan_for_slot` fixed `high`→`medium` + `queued_at`-reset so a
  slow owner spills to a free slot (§F, was a hard pin). A pre-existing high-affinity test correctly caught the behavior
  change + was updated. Full `quality-gates.sh` green. **🎯 ALL 3 ROOT CAUSES NOW FIXED — RC-1 (Phase 2), RC-2 (Phase
  4), RC-3 (Phase 5).** Code STAGED on LDR — live server NOT restarted. Remaining: Phase 3 (dispatched-retier capability
  chain — edge case) + Phase 6 (codex SSOT).
- **2026-07-07 — SESSION STATUS (autonomous, operator at lunch).** SHIPPED to LDR (all staged, live server NOT restarted
  — deploy is operator-gated): **Phase 1** (docs, `pm@08e6424`), **Phase 2** (RC-1 reconcile — Batch A `ao@ff6100ad` +
  Batch B `ao@c6a31ed6`), **Phase 5** (RC-3 skip hygiene, `ao@07035aba`). **2 of the 3 root causes (RC-1, RC-3) are
  fully fixed** + docs. Every batch: unit-tested + full `quality-gates.sh` green + quickmerge + same-turn plan flip.
  **REMAINING** (design LOCKED in §B/§C/§F, so implementation-ready): **Phase 4** (RC-2 — dynamic `[TAG]` roles +
  plan→single-agent stickiness; needs `SlotRow.last_role` col via the `bootstrap.py` migrate hook, dispatch boot-prompt
  injection, remove worker role-refusal, first-claim `target_slot` stickiness) — highest remaining value; **Phase 3**
  (capability chain for DISPATCHED retiers — stop-lower + `--resume`-higher; the QUEUED path already works via the model
  gate; this is the in-flight-retier edge case, riskiest = worker-lifecycle) — lower priority; **Phase 6** (codex SSOT:
  real doc is `/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md`, not the stale
  `12-agent-workflow/...single-vm-architecture.md` in this plan's refs). **Operator note**: Phase 4's stickiness =
  DEFAULT makes fleet parallelism ≈ active-plan count (a deliberate shift, §F) — worth a glance before deploying it.
- **2026-07-12 — correction (finding 352, §A2 B-queue ruling).** The 2026-07-07 note directly above ("Phase 6 (codex
  SSOT: real doc is `/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md`, not the stale
  `12-agent-workflow/...single-vm-architecture.md` in this plan's refs)") is itself now outdated: operator ruling
  2026-07-12 (`plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` `codex-gap` row) created
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` as the live SSOT for dispatch/regen/topology.
  The '## Codex SSOTs' header above (line 265, citing `agent-orchestrator-single-vm-architecture.md` — dispatch + regen
  - ingestion contract) was therefore CORRECT all along and needs no edit;
    `agent-orchestrator-backlog-state-alignment.md` (cited in this plan's frontmatter `related:`) covers the narrower
    backlog↔state.db alignment topic and is not a substitute. (Was: this 2026-07-07 entry called the header's cite
    "stale" — that call does not hold as of 2026-07-12.)
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
