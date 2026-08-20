---
doc_type: plan
title: AO worker lifecycle — reap orphaned workers and reclaim stale dispatches
summary:
  Around 10 orphaned claude workers are alive on the VM right now, burning CPU and account budget and racing
  re-dispatched work, and a task dispatched to a dead slot can stay bound forever when the resume path never completes.
  Implement the orphan reap (both halves) and the stale-dispatch invariant, each with the guards that stop them killing
  healthy workers or double-dispatching a task.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, worker-lifecycle, tmux, reaper, dispatch]
related:
  [
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_dispatch_liveness_p0_2026_07_20.md,
  ]
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

> **🟢 COMPLETE 2026-07-20 — ARCHIVED.** All code todos landed and were independently re-verified 2026-07-20: `aa81706`,
> `ebe2ae3`, `95fdf9d` all exist and are ancestors of `origin/live-defi-rollout`; each diff matches its claim and every
> cited test exists by name (incl. the real `/proc` scan, not a mock). The periodic orphan sweep is flipped LIVE
> (`orphan_sweep_dry_run=False`). The one remaining item — the live 24h dispatched-count spot-check — is gated on
> calendar time, not code, and is now owned by `ao_open_issues_consolidated_close_out_2026_07_17.md` § Phase 8. Do not
> reopen this plan for it.
>
> **Correction worth carrying**: `f641968`'s typed-agent guard was at one point believed to rest on a retracted premise.
> That retraction was ITSELF later overturned — `journalctl` (not `activity_log`, which is why the first pass missed it)
> shows a real reclaim at 07:32:30 UTC. The guard stands. See `ao_scheduled_agent_hygiene_2026_07_20.md` residuals
> R1/R2.

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

- [x] [BACKEND] P1. **Orphan-process reap, half (a): the TmuxPruner kills the worker process tree whose slot config-dir
      maps to a dead/absent session.** Match by `claude_session_id` / config dir — **never by name-grep alone** (a
      name-grep reap will eventually kill an operator's own interactive session). **Gate**: a simulated
      `tmux_session_lost` leaves zero detached claude processes for that slot; the matcher is proven to not match a live
      session's PID. — `agent-orchestrator@aa81706`. Matches by `CLAUDE_CONFIG_DIR` read from `/proc/<pid>/environ`
      (never process-name grep); wired into `TmuxPruner.prune_once()`'s dead-session branch, immediately after
      `has_session()` confirms the session is gone. Gate met locally: `tests/test_orphan_process_reap.py` proves the
      matcher only touches the target slot's PID (a same-age PID on a different slot is left untouched), honours
      `boot_grace_seconds` anchored on the OS process's own start time, and includes one real `/proc` scan against an
      actual subprocess (not just mocked seams).
- [x] [BACKEND] P1. **Orphan-process reap, half (b): a periodic orphan sweep (config-dir → PID → slot liveness)**
      catching residue the pruner misses, including PPID-1 trees that have no surviving parent to notice them.
      **Required guards, all three**: (i) never kill a PID belonging to a live session; (ii) **honour
      `boot_grace_seconds` — NEVER reap inside a slot's fresh-spawn grace window**; (iii) a `--dry-run` mode that is the
      DEFAULT until the operator approves a live run. Log every kill with slot + PID + age. **Gate**: dry-run on the VM
      lists the current orphans and nothing else; after operator approval, a live sweep reports 0 orphans remaining (the
      one-time cleanup of the current ~10 included). — Code shipped `agent-orchestrator@aa81706`, VM verification done
      2026-07-20. **Dry-run pass** (read-only SSM against `i-0c9b283b31d6b5ca7`): correctly flagged the same PID (slot 9
      / 1863748 / session `6cf84cea` — the exact orphan named in the 07-17 incident doc) on every one of ~16 ticks, zero
      false positives, zero signals sent. **Found + fixed a real gap surfaced by the dry-run itself**: a slot's
      `CLAUDE_CONFIG_DIR` is reused across respawns, so "a session named `orch-slot-N` currently exists" is not proof
      every process under that dir belongs to the CURRENT occupant — confirmed live when slot 9 got a fresh dispatch
      (new session, new pane pid) while the 07-17 orphan kept running underneath, invisible to a bare `has_session()`
      check. Fixed to match per-PID against the live session's pane-process tree
      (`tmux_spawn.pid_belongs_to_live_session`, reusing the existing ancestry helpers) — `agent-orchestrator@ebe2ae3`,
      regression test added reproducing the exact reused-config-dir scenario. **Operator reviewed + approved a live
      run** (2026-07-20 chat) after the fixed dry-run surfaced the TRUE scope: 7 orphans across 6 slots (ages 21min-72h;
      three matched the 07-17 incident's named PIDs, still alive 3 days later) — the old coarse check had been masking 6
      of these 7 the moment their slots were reused. Flipped `tuning.orphan_sweep_dry_run` default to `False` —
      `agent-orchestrator@95fdf9d`. **Live sweep verified**: 9 `orphan_process_reaped` events (the original 7 + 2 more
      caught fresh on slot 4, ages 338s/473s — confirming an actively recurring leak on that slot, now caught within
      minutes instead of accumulating for days); all 8 unique PIDs confirmed GONE via direct `ps` on the VM; post-sweep
      fleet health clean (0 `watchdog_slot_killed`/`stale_dispatch_reclaimed` regressions, slot 4's actual live worker —
      task `sports_p2_history_apifootball_2015_to_present-001` — untouched with a fresh ping seconds after the sweep,
      service `NRestarts=0`). **Follow-up filed, not actioned this session**: slot 4 producing short-lived orphans
      repeatedly (2 fresh ones within ~15 min of the sweep going live) suggests a root cause on that slot specifically,
      beyond this plan's scope — tracked at `/plans/archive/issues/slot4_recurring_short_lived_orphans_2026_07_20.md`.
- ➡️ **MIGRATED 2026-07-20 → `ao_open_issues_consolidated_close_out_2026_07_17.md` § Phase 8. NOT done; not owned
  here.** Original item, for the record: [BACKEND] P1. **Stale-dispatch invariant (Defect A), resume-path aware.** The
  pruner's requeue (`ao@5b07bd3`) releases on a "requeue" verdict, but a `resume-pending` verdict keeps the task bound —
  and when the resume never happens (07-17: slots went `killed` still holding tasks), nothing reconciles. Add: a task
  `dispatched` to a slot with `worker_alive=false` AND `tmux_session IS NULL` for more than one pruner tick beyond
  `resume_attempts` exhaustion → auto-release + a `stale_dispatch_reclaimed` activity event. **It must not fight the
  resume path** — fire only after resume is exhausted or impossible. **Gate**: doc #3's regression test; live
  `dispatched` count equals live-worker-held count across a 24h spot-check; **AND an explicit no-double-dispatch
  assertion — a task released by this invariant is NEVER simultaneously live on a resumed worker.** Order the release
  strictly AFTER `resume_lifecycle` marks resume exhausted/impossible, and test the exact race (resume in-flight when
  the invariant tick fires → invariant defers, no release). — Code shipped `agent-orchestrator@aa81706`:
  `server/stale_dispatch.reclaim_stale_dispatches()`, wired into `WorkerLivenessWatchdog._tick_once`. Deliberately NOT
  gated on `resume_attempts` alone — that counter only increments on a SUCCESSFUL resume spawn, so the exact 07-17
  incident (a slot stuck resume-pending that never once succeeds) would never hit it; instead fires on a combined
  elapsed-time + activity-log-derived attempts-observed signal (soft: ≥30min AND ≥2 attempts observed AND no flagged
  backend outage; hard backstop: ≥4h regardless, so a fleet-wide capacity outage — measured to record ZERO attempts for
  every resume-pending slot it skips — can't strand a slot forever). Regression coverage + no-double-dispatch assertion
  done: `tests/test_stale_dispatch_reclaim.py` (9 tests: soft/hard triggers, outage gate,
  paused-slot/live-worker/no-anchor exclusions) + the explicit race test (invariant tick firing the INSTANT a resume
  episode starts → defers, no release). **Still open**: the live 24h dispatched-count-equals-live-worker-held spot-check
  — needs the fix live on the VM for a full day before it means anything.
- [x] [BACKEND] P2. **Prove the two mechanisms cannot fight each other.** The reap kills processes; the invariant
      releases tasks; the resume path revives workers. Write one test that runs all three against the same slot and
      asserts a coherent end state — no task both released and held, no live worker reaped, no orphan surviving.
      **Gate**: the combined test exists and bug-injection on any one mechanism turns it red. —
      `agent-orchestrator@aa81706`, `tests/test_worker_lifecycle_interaction.py`. One test drives a full dead-worker
      episode (dirty WIP → resume-pending classification → orphan reap in the same tick → invariant deferring on the
      immediate race → invariant firing once the hard backstop clears) against one slot, plus an unrelated live PID on a
      different slot proven untouched throughout. Bug-injection verified: temporarily disabling the reap's
      slot-isolation check and separately the invariant's elapsed-time/attempts gate each turned this test red;
      restored, it passes clean.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo.
- Commit only from a `quality-gates.sh`-green tree.
- **Killing the wrong process is unrecoverable work loss.** Default to dry-run, prefer a false negative (an orphan
  survives one more tick) over a false positive (a working agent dies). If a guard is inconvenient to implement, that is
  not a reason to drop it — say so and stop.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — slot/worker lifecycle.
- `/codex/04-architecture/autonomous-recovery-matrix.md` — what may self-recover autonomously vs needs a human.
- `/codex/04-architecture/recovery-defence-in-depth-layers.md` — where the pruner sits among the recovery layers.

## Progress Log

- **2026-07-20 — plan created** from Phase 2 of the consolidated close-out. Filed with an explicit `depends_on` the
  liveness P0 because both touch the lifecycle loops, and the liveness fix establishes the invariant this plan must
  preserve (predecessor state must never kill a successor).
- **2026-07-20 — todos 1a, 3, 4 code-complete + shipped; todo 1b code-complete, VM leg outstanding.** Sequencing gate
  confirmed satisfied before starting: `ao_dispatch_liveness_p0_2026_07_20.md`'s code landed on LDR and was confirmed
  live on the central VM (its own todo 5). `agent-orchestrator@aa81706695f6642060c118e14bc1bb95e535d17b`,
  `quality-gates.sh`-green (1450 tests) before commit. New modules `server/orphan_reap.py` (both reap halves) and
  `server/stale_dispatch.py` (the invariant), wired into `TmuxPruner` and `WorkerLivenessWatchdog` respectively; 33 new
  tests across `tests/test_orphan_process_reap.py`, `tests/test_stale_dispatch_reclaim.py`,
  `tests/test_worker_lifecycle_interaction.py`. Design note worth recording: todo 3's literal "resume_attempts
  exhaustion" wording would have silently never fired on the actual 07-17 incident shape — that counter only increments
  on a successful resume spawn, so a slot stuck resume-pending with zero successful attempts sits at 0 forever. Built
  instead on an activity-log-derived attempts-observed count (mirrors `EscalationQueueRow`'s attempts+timestamp pattern)
  combined with elapsed time and `autospawn.outage_active()`, per operator direction (2026-07-20 chat): not pure
  time-based, since a slow-but-recovering backend or a fleet-wide capacity outage must not be misread as "dead."
  **Deliberately NOT run against the live VM this session** — the periodic orphan sweep (todo 1b) stays dry-run-only by
  default (`tuning.orphan_sweep_dry_run=True`) and the invariant's 24h live spot-check needs the fix live for a full day
  first; both are flagged open above, pending operator go-ahead for the VM-side half.
- **2026-07-20 (same day, later) — todo 1b's VM leg run to completion, operator-approved.** Dry-run against the live
  central VM (read-only SSM) worked exactly as designed, then immediately exposed a real gap in its own detection logic:
  a slot's `CLAUDE_CONFIG_DIR` is reused across respawns, so a coarse `has_session()` check goes permanently blind to a
  stale orphan the moment its slot is reused by a fresh occupant — confirmed live (slot 9's original 07-17 orphan, PID
  1863748, still running underneath a session created seconds earlier). Fixed to a per-PID pane-tree-membership check
  (`agent-orchestrator@ebe2ae3`), which then surfaced the TRUE scope the coarse check had been hiding: 7 orphans across
  6 slots, not the 1 the naive check could see, three of them the exact PIDs named in the 07-17 incident doc, still
  alive 3 days later. Operator reviewed and approved a live run in-chat; `orphan_sweep_dry_run` flipped to `False` by
  default (`agent-orchestrator@95fdf9d`). Verified via SSM: 9 `orphan_process_reaped` events (the 7 plus 2 more caught
  fresh on slot 4 within 15 minutes, ages 338s/473s), all 8 unique PIDs confirmed gone via `ps`, zero regressions (no
  unexpected `watchdog_slot_killed`/`stale_dispatch_reclaimed`, slot 4's actual live worker untouched with a fresh ping
  seconds after the sweep, service healthy). Todo 1b fully closed. Worth flagging for a future session: slot 4 is
  producing short-lived orphans repeatedly — a root cause specific to that slot, outside this plan's scope, but the
  periodic sweep is now catching them within minutes regardless. Todo 3's live 24h spot-check remains the only open item
  on this plan.
