---
doc_type: plan
title: One liveness contract for every agent — stop teaching each reaper about roles
summary:
  One-off agents (plan_reconciler, plan_health, escalation crafts) never call /boot, so their slot reads idle for their
  whole run and every liveness subsystem must be independently taught not to kill them. Three carve-outs exist and a
  fourth reaper would need a fifth. Replace them with one protocol every agent follows, where the backend answers
  role-appropriately instead of each reaper special-casing kinds.
status: draft # NOT ingested — operator review pending (2026-07-20). Flip to `active` to start.
nature: design
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [agent-orchestrator, liveness, boot-protocol, reaper, architecture]
related:
  [
    ao_dispatch_liveness_p0_2026_07_20.md,
    ao_scheduled_agent_hygiene_2026_07_20.md,
    ao_worker_lifecycle_reap_2026_07_20.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
model_tier: sonnet-doable # single-repo protocol change; the design decision is made below, execution is staged
thinking_tier: high # a live-fleet protocol migration — the staging order is the risky part
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
---

# One liveness contract for every agent

> **Operator decision 2026-07-20**: of the two paths considered — (1) make each reaper role-aware, or (2) make every
> agent follow the same register/boot/heartbeat protocol with role-appropriate backend responses — **path 2 is chosen**.
> This plan implements it.

## ✅ UPDATE 2026-07-20 (slot-16 interactive) — the root cause IS now diagnosed; re-scope this plan accordingly

The root-cause investigation this plan was waiting on has landed (`ao_scheduled_agent_hygiene_2026_07_20.md`, the P0
todo — full evidence there). **Cause, proven from journalctl + code + git:** `agt-751738` was killed by
`WorkerLivenessWatchdog._reclaim_idle_lingering_sessions` at 07:32:30 (`kill_session`,
worker_liveness_watchdog.py:1212), because (A) its slot read `status=idle` and (B) at that moment the idle-reclaimer had
**no typed-agent exemption** — the `f641968` guard was committed 1h38m LATER (09:10 UTC vs the 07:32:30 kill). So the
death is fully explained as "unguarded idle-lingering reaper reaps a typed one-off," a **liveness-signalling** cause —
squarely in this plan's domain, NOT an unrelated API/usage cutoff.

**Consequences for this plan:**

- The line below "the motivating bug is NOT diagnosed, so this plan must not be started" — the **first clause is now
  false**. The bug is diagnosed. But **do not big-bang-start this plan either**: the cheapest correct next move is to
  verify `f641968` (already deployed) actually fixes it on todo 4's next reconcile run. The claim (in this plan and the
  hygiene plan) that "`f641968` did NOT fix this" is **unsound** — it was inferred from a death that predates `f641968`
  by 1h38m. `f641968`'s AgentRow-keyed guard plausibly works; it is simply UNTESTED. **If that one live run confirms the
  guard exempts the reconciler, this plan reverts to exactly the "pure de-duplication refactor at much lower priority"
  case it already anticipated below** — the three carve-outs are real duplication worth removing, but the urgency is
  gone. If the guard is somehow defeated (e.g. restart clears the AgentRow), that failure mode feeds directly into this
  plan's uniform-contract design. Either way: **gate flipping this to `active` on that single live observation, not on
  new code.**
- **What is still true:** "typed agents get `status='working'` on claim" (plan_health.py:283) IS the code path — but the
  reconciler was nonetheless reaped as `idle`, which means the `working` status did NOT survive to kill time
  (empirically flipped to `idle` around the 07:30 restart; the exact line is unpinned — residual R1 in the hygiene
  plan). So the "their slot reads idle" framing this plan warns against is **not simply false** after all: for a typed
  one-off it can become true in flight. That nuance belongs in the contract design (todo 1).

## ⚠️ READ FIRST — the evidence this plan was built on has been RETRACTED (2026-07-20)

This plan originally opened with a confident mechanism: that one-off agents never call `/boot`, so their slot stays
`idle` and `_reclaim_idle_lingering_sessions` reaps them mid-work. **That was wrong and is withdrawn.** The
plan_reconciler demonstrably DOES call `/boot` (`slot_boot` 07:27:03) and DOES heartbeat (`slot_progress` 07:28:18); no
reclaim event ever fired; and `tmux_session_lost` is the TmuxPruner OBSERVING an already-dead session, not killing one.
Full disproven list + the live handoff: `ao_scheduled_agent_hygiene_2026_07_20.md`, the P0 root-cause todo.

**Consequence: the motivating bug is NOT diagnosed, so this plan must not be started as an implementation.** Its
destination may well still be right — three separate per-subsystem carve-outs for "typed agents are special" do exist
(`1e7fec0`, `f641968`, `5907317`), and that duplication is real and independently worth removing. But the _route_ and
the _urgency_ both depend on a root cause nobody has established yet.

**What is still independently true** (verified, not inferred):

- Typed agents already get `status="working"` on claim (`plan_health.py:283`, `escalation.py:476`) — so any future
  argument based on "their slot reads idle" is false and must not be reintroduced.
- Three carve-outs teach three different subsystems the same fact; a fourth reaper would need a fourth.
- `agent-orchestrator@f641968` was shipped on the retracted premise. It is defensively harmless and its regression test
  is real, but it did not fix the reconciler.

**Do not flip this to `active` until the root-cause investigation lands.** If the cause turns out to be unrelated to
liveness signalling (an API/usage cutoff, a crash), this plan becomes a pure de-duplication refactor at much lower
priority — and should be re-scoped accordingly rather than executed as written.

## What "uniform" means here — and what it does not

**It does not mean identical payloads.** It means one PROTOCOL — register → boot → heartbeat → finish — with
**role-appropriate responses**. A fleet worker's `/boot` returns a task; a one-off's returns "no task, you already know
your work". Same handshake, different answer. The backend keeps the role knowledge in ONE place (the boot response)
instead of scattering it across every reaper.

**The heartbeat is the load-bearing piece, not `/boot`.** What made the reconciler look dead was `last_msg: NULL` for
seven minutes. `/boot` matters because it moves the slot off `idle`; the heartbeat matters because it is the ongoing
proof of life. Get both uniform and the carve-outs become deletable.

## ⚠️ Migration risk — this is a live fleet

Changing every agent's boot prompt at once can wedge the entire fleet: an agent that fails the new handshake never
boots, and the fleet has no workers. **Stage it.** The backend accepts BOTH contracts first, roles migrate one at a
time, and the carve-outs come out LAST — only once every role is proven on the new path.

## Execution environment — LOCAL

Operator-assigned agents on this host (`assigned_vm: NA`, `execution_scope: local-only`). Tick checkboxes by hand. Code
and tests are local (`bash scripts/quality-gates.sh`). Live confirmation needs read-only SSM (pattern:
`scripts/orchestrator/check-ao-backlog-status.sh`). **Never restart the live service without asking.**

## Todos

- [ ] [BACKEND] P1. **Write down the contract before changing any code.** One short design note: the states (registered
      → booted → working → finished), which call each agent class makes, what `/boot` returns per role, the heartbeat
      cadence expected, and — critically — **what each liveness subsystem is allowed to conclude from each state**. Name
      every current consumer (prereq reaper, idle-lingering reclaimer, TmuxPruner, HealthMonitor, AutoSpawn,
      `_pick_free_slot`) and state which signal it should read AFTER the change. **Gate**: the note exists and a reader
      can answer "why won't a one-off be reaped?" without reading any reaper's source.
- [ ] [BACKEND] P1. **Make `/boot` role-aware and accept a task-less boot.** A one-off POSTs `/boot` like anyone else;
      the response carries no task and the slot transitions out of `idle` into a state that means "occupied and
      working". Do NOT invent a parallel endpoint — that is path 1 wearing a different hat. **Gate**: a
      plan_reconciler-shaped boot returns 200 with no task, the SlotRow leaves `idle`, and an existing fleet-worker boot
      is byte-for-byte unchanged in behaviour (regression-tested).
- [ ] [BACKEND] P1. **Backend accepts BOTH contracts during migration.** Old-style one-offs (no `/boot`) must keep
      working exactly as today — including the three carve-outs, still in place — while the new path is proven.
      **Gate**: a test matrix covering {old, new} × {fleet worker, one-off} all behaving correctly; nothing regresses
      for an agent that has not migrated.
- [ ] [BACKEND] P2. **Migrate the role docs one at a time, starting with `plan_reconciler`.** Add the STEP-0 liveness
      ping + `/boot` to its boot procedure, keeping its existing `/progress` heartbeat guidance. `plan_reconciler` first
      because it is the one measurably being killed and the easiest to observe. **Gate**: one full reconcile run
      observed booting, heartbeating, and surviving past the 420s window that used to kill it — cite the dispatch_id.
- [ ] [BACKEND] P2. **Migrate the remaining one-off roles** (`plan_health`, and the escalation crafts — `cicd`,
      `conflict_resolver`, `data_pipeline_failure`). One at a time, each verified live before the next. **Gate**: each
      role has a run observed on the new contract; none regressed.
- [ ] [BACKEND] P2. **Close the startup-latency gap that made this bite.** The reconciler's first heartbeat comes after
      a startup phase (reading role docs, running the hygiene sweep) that can exceed the grace window. Either require a
      STEP-0 ping before that phase, or make the grace window measure from first-contact rather than spawn. **Gate**: a
      one-off whose startup takes 10+ minutes still proves liveness throughout — test with a deliberately slow boot.
- [ ] [BACKEND] P1. **Delete all three carve-outs — the plan is not done until they are gone.** (a) the AgentRow guard
      in the prereq reaper (`1e7fec0`), (b) the AgentRow guard in `_reclaim_idle_lingering_sessions` (`f641968`), and
      (c) the typed-spawn recognition in the boot gate (`5907317`) if the uniform contract subsumes it. Each deletion
      must be accompanied by a test proving the uniform signal now protects that agent instead. **Gate**: `rg` finds no
      typed-agent special-case left in any reaper; the regression tests from those commits still pass, now protected by
      the contract rather than the carve-out.
- [ ] [DOC] P2. **Record the contract in codex and point the role docs at it.** This is a durable architectural rule, so
      its SSOT is a codex doc, not this plan. **Gate**: a codex doc describes the contract; every role doc references it
      rather than restating it; `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` links to it.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Do not delete a carve-out before its replacement is proven live.** The carve-outs are currently the only thing
  keeping one-off agents alive; removing one early re-opens the exact bug this plan exists to close, on a live fleet.
- **Migrate one role at a time.** A big-bang boot-prompt change that fails leaves the fleet with no working agents and
  no easy way to notice, because the failure mode is silence.

## Codex SSOTs

- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — slot/worker/dispatch model this refines.
- `codex/04-architecture/recovery-defence-in-depth-layers.md` + `…/autonomous-recovery-matrix.md` — the liveness
  subsystems whose inputs this changes.
- `codex/12-agent-workflow/async-wait-and-poll-discipline.md` — measured terminal verdicts for the live gates.

## Progress Log

- **2026-07-20 — plan created** after the transcript evidence settled the design question. Worth preserving: the earlier
  hypothesis was that the reconciler was dying on spawn (an account cap or bad opus/effort flags). The transcript
  disproved it in one read — 436 KB of productive work ending mid-task. **When an agent "fails silently", read its JSONL
  before theorising about why it died; it may not have died at all.**
- **2026-07-20 — root cause landed; "premise not diagnosed" banner updated (slot-16 interactive).** The blocking
  investigation (hygiene plan P0 todo) is closed: `agt-751738` was killed by the idle-lingering reclaimer at 07:32:30
  while unguarded (the `f641968` exemption postdates the kill by 1h38m). This is a liveness-signalling cause, in this
  plan's domain. Net effect on this plan: the motivating bug is diagnosed, but the correct next step is a single live
  verification of `f641968` (not new code) — if it confirms, this plan is a lower-priority de-dup refactor (as the plan
  itself anticipated). Left `status: draft`; the flip-to-active gate is now that one live observation, per the ✅ UPDATE
  section above. See `ao_scheduled_agent_hygiene_2026_07_20.md` P0 for the full evidence trail.
