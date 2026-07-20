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

## The evidence that settled it

The daily `plan_reconciler` has been killed mid-work on every run since it was installed. Its JSONL transcript
(`b1a0f68f-…`, 83 entries, 436 KB) shows it **actively working at 07:32:29Z** — reading its plan-hygiene sweep output,
analysing the Phase-0 inventory — roughly 60 seconds before its session was destroyed. It was never crashing. It was
being reaped.

The mechanism, with exact arithmetic: a one-off never calls `/boot` (a fleet-worker step its role doc does not ask for),
so its `SlotRow.status` stays `idle` for its entire run. Then `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions`
counts it as a lingering session: `boot_grace_seconds` (300s) + `watchdog_idle_session_ticks` (2) ×
`watchdog_interval_seconds` (60s) = **420s**, against a measured 07:25:50→07:33:30 = **7m40s**.

**The decisive part is what happened next.** On 2026-07-20 the _prereq_ reaper was taught about typed agents
(`agent-orchestrator@1e7fec0`, via a live-AgentRow discriminator). The idle-lingering reclaimer — a different function
in the same file — never learned it, and kept killing the reconciler. A third carve-out was then shipped for that
function (`agent-orchestrator@f641968`). **Three carve-outs, same fact, three places to forget it.** A fourth reaper
would need a fourth.

That is the architectural argument, demonstrated rather than asserted: **per-subsystem role carve-outs do not compose.**
If instead every agent proves liveness the same way, "is this slot alive?" has one answer and no reaper needs to know
what kind of agent occupies it.

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
