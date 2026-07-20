---
doc_type: plan
title: AO worker lifecycle — reap orphaned workers and reclaim stale dispatches
summary:
  Around 10 orphaned claude workers are alive on the VM right now, burning CPU and account budget and racing
  re-dispatched work, and a task dispatched to a dead slot can stay bound forever when the resume path never completes.
  Implement the orphan reap (both halves) and the stale-dispatch invariant, each with the guards that stop them killing
  healthy workers or double-dispatching a task.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, worker-lifecycle, tmux, reaper, dispatch]
related: [ao_open_issues_consolidated_close_out_2026_07_17.md, ao_dispatch_liveness_p0_2026_07_20.md]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 1.6
assigned_role: backend_engineer
model_tier: sonnet-doable # single-repo; both defects diagnosed with named guards in the plan body
thinking_tier: high # process-lifetime + resume-race reasoning; killing the wrong PID is unrecoverable
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_dispatch_liveness_p0_2026_07_20.md]
source:
---

# AO worker lifecycle — orphan reap + stale-dispatch reclaim

> **Provenance**: Phase 2 of `ao_open_issues_consolidated_close_out_2026_07_17.md` (doc #3, Defects A and B). That plan
> keeps the audit record; this plan holds the work.

## ⚠️ Sequencing — read before starting

`depends_on: ao_dispatch_liveness_p0_2026_07_20.md`. That plan owns `server/worker_liveness_watchdog.py` (the prereq
reaper). **Do not start todo 2 until it has landed**, or two agents will edit the same lifecycle loops with different
mental models of when a session may be killed. Todo 1 (the process reap) is a different surface and can start
immediately — but read the liveness plan's fix first, because it establishes the principle this plan must not violate:
**a freshly-spawned worker must never be killed by state belonging to its predecessor.**

## Why this is urgent

Defect B is a **live bleed, measured**: ~10 orphaned `claude` workers were alive on the VM (16 processes vs 4 live
sessions; 3 matched the doc's named PIDs at ~4h old, one tree fully detached at PPID 1). Each burns CPU and account
budget — and worse, an orphan can still be acting on work that has since been re-dispatched to another slot.

## The guard that matters most

Both todos can cause severe harm if built naively. The reap can kill healthy workers; the invariant can double-dispatch
a task. **The 6-of-6-AutoSpawn-workers-killed-56-120s-post-spawn incident is the exact class** — a booting worker's tmux
session is not registered yet, so it looks like an orphan. `config.boot_grace_seconds` exists precisely for this.

## Execution environment — LOCAL

Operator-assigned agents on this host (`assigned_vm: NA`, `execution_scope: local-only`). Tick checkboxes by hand.
Code + tests are local (`bash scripts/quality-gates.sh`). The **live sweep** in todo 1's gate needs the central VM —
read-only SSM for counting orphans (pattern: `scripts/orchestrator/check-ao-backlog-status.sh`). **Actually killing live
processes on the VM is a PRODUCTION write — operator-gated. Build it with `--dry-run` first, show the operator what it
WOULD kill, and get approval before any real reap.**

## Todos

- [ ] [BACKEND] P1. **Orphan-process reap, half (a): the TmuxPruner kills the worker process tree whose slot config-dir
      maps to a dead/absent session.** Match by `claude_session_id` / config dir — **never by name-grep alone** (a
      name-grep reap will eventually kill an operator's own interactive session). **Gate**: a simulated
      `tmux_session_lost` leaves zero detached claude processes for that slot; the matcher is proven to not match a live
      session's PID.
- [ ] [BACKEND] P1. **Orphan-process reap, half (b): a periodic orphan sweep (config-dir → PID → slot liveness)**
      catching residue the pruner misses, including PPID-1 trees that have no surviving parent to notice them.
      **Required guards, all three**: (i) never kill a PID belonging to a live session; (ii) **honour
      `boot_grace_seconds` — NEVER reap inside a slot's fresh-spawn grace window**; (iii) a `--dry-run` mode that is the
      DEFAULT until the operator approves a live run. Log every kill with slot + PID + age. **Gate**: dry-run on the VM
      lists the current orphans and nothing else; after operator approval, a live sweep reports 0 orphans remaining (the
      one-time cleanup of the current ~10 included).
- [ ] [BACKEND] P1. **Stale-dispatch invariant (Defect A), resume-path aware.** The pruner's requeue (`ao@5b07bd3`)
      releases on a "requeue" verdict, but a `resume-pending` verdict keeps the task bound — and when the resume never
      happens (07-17: slots went `killed` still holding tasks), nothing reconciles. Add: a task `dispatched` to a slot
      with `worker_alive=false` AND `tmux_session IS NULL` for more than one pruner tick beyond `resume_attempts`
      exhaustion → auto-release + a `stale_dispatch_reclaimed` activity event. **It must not fight the resume path** —
      fire only after resume is exhausted or impossible. **Gate**: doc #3's regression test; live `dispatched` count
      equals live-worker-held count across a 24h spot-check; **AND an explicit no-double-dispatch assertion — a task
      released by this invariant is NEVER simultaneously live on a resumed worker.** Order the release strictly AFTER
      `resume_lifecycle` marks resume exhausted/impossible, and test the exact race (resume in-flight when the invariant
      tick fires → invariant defers, no release).
- [ ] [BACKEND] P2. **Prove the two mechanisms cannot fight each other.** The reap kills processes; the invariant
      releases tasks; the resume path revives workers. Write one test that runs all three against the same slot and
      asserts a coherent end state — no task both released and held, no live worker reaped, no orphan surviving.
      **Gate**: the combined test exists and bug-injection on any one mechanism turns it red.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Killing the wrong process is unrecoverable work loss.** Default to dry-run, prefer a false negative (an orphan
  survives one more tick) over a false positive (a working agent dies). If a guard is inconvenient to implement, that is
  not a reason to drop it — say so and stop.

## Codex SSOTs

- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — slot/worker lifecycle.
- `codex/04-architecture/autonomous-recovery-matrix.md` — what may self-recover autonomously vs needs a human.
- `codex/04-architecture/recovery-defence-in-depth-layers.md` — where the pruner sits among the recovery layers.

## Progress Log

- **2026-07-20 — plan created** from Phase 2 of the consolidated close-out. Filed with an explicit `depends_on` the
  liveness P0 because both touch the lifecycle loops, and the liveness fix establishes the invariant this plan must
  preserve (predecessor state must never kill a successor).
