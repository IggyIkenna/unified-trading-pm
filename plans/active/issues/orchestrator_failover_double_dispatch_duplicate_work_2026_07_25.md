---
doc_type: issue
title:
  Failover double-dispatch — a task re-dispatches to a new worker while a prior owner still holds it in
  current_task=working, causing two workers to do the same task's bookkeeping in parallel (duplicate work + double-/done
  + same-issue-doc merge risk); observed 2× in one session (sigabrt slots 2&8, sports batch2-001 slots 4&11)
summary: >-
  On 2026-07-25 main (agt-52bb99) observed the same runtime pattern twice in one poll-loop window: a backlog task shows
  up in TWO slots' current_task simultaneously, both with status=working, while the backend /api/backlog record names
  exactly one dispatched_to owner. (1) deployment_api_sigabrt_crash_loop-001 was dispatched_to=8 yet slot 2 was still
  actively working it (root-cause confirmed, QG running) — both live in their panes at the same instant. (2)
  sports_satellite_ao_dispatch_batch2-001 was dispatched_to=4 (slot 4 closing it out with a re-verification note) yet
  slot 11 still held it and shipped a competing issue-doc change (committed e15b1ac0c, quickmerging). In BOTH cases the
  two workers independently converged on doc-only/bookkeeping work (each determined the real implementation had already
  landed — slot 10 for sigabrt at 05:25Z, "all 11 batches landed" for batch2-001) and reverted any code, so NO same-file
  code conflict materialised. Residual harm is real but bounded: (a) wasted duplicate effort (two workers spend a full
  work-cycle on one task), (b) double-/done risk on one task id, (c) a possible rebase/merge on the shared PM issue doc.
  Root-cause hypothesis: a task with failover_allowed=true gets re-dispatched to a freed worker when the current owner
  goes silent (e.g. a long quality-gates.sh run with no heartbeat), without first confirming the prior owner has
  actually released it — the prior owner's slot-side current_task is not cleared, so both proceed. This is a dispatcher
  throughput/correctness gap, NOT a data defect; self-mitigating today only because workers happened to self-detect the
  already-landed work.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    dispatch,
    failover,
    double-dispatch,
    duplicate-work,
    heartbeat,
    quality-gates,
    throughput,
    watchdog,
  ]
related:
  [
    /plans/active/issues/orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md,
    /plans/active/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
priority: P2
parent_epic: orchestrator_master
source:
  "main orchestrator (agt-52bb99) read-only per-task diagnosis + pane inspection during poll loop, 2026-07-25
  ~11:50-12:05Z"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

# Failover double-dispatch — same task in two slots' current_task=working while backend names one owner

## Evidence (read-only, on-host :8765, 2026-07-25, main agt-52bb99)

### Incident 1 — deployment_api_sigabrt_crash_loop-001 (slots 2 & 8), ~11:50Z

- `/api/backlog` record: `status=dispatched`, `dispatched_to=8`, `collision_group=null`, `affinity=none`.
- `/api/state`: **slot 2** `current_task=deployment_api_sigabrt_crash_loop-001, status=working` (`last_msg` "root cause
  confirmed: stale shard-count pin (test, not code)", then "quality-gates.sh (re-verify) still running") AND **slot 8**
  `current_task=deployment_api_sigabrt_crash_loop-001, status=working` at the same instant.
- Pane truth: slot 2 running QG on a test-pin fix; slot 8 had just finished a prior task, picked this up fresh, read the
  plan-of-record, verified the primary fix (post_worker_init faulthandler) was ALREADY live via slot 10 at 05:25Z (rev
  1adf54b), and shipped a PM-repo-only [REVIEW] checkbox flip, then /done. Zero deployment-api code touched by slot 8.
- Outcome: no code conflict. Slot 8 /done'd it as bookkeeping; slot 2's separate test-pin fix continued as follow-up
  cleanup. Confirmed by slot 8's reconciliation message (operator thread msg 2005): "/done returned zero warnings, PM
  push was a clean fast-forward, touched zero deployment-api code."

### Incident 2 — sports_satellite_ao_dispatch_batch2-001 (slots 4 & 11), ~12:00Z

- `/api/backlog` record: `status=dispatched`, `dispatched_to=4`, `collision_group=null`, `affinity=none`.
- `/api/state`: **slot 4** `current_task=...batch2-001` (pane: "nothing further to ship — all 11 batches landed, steps
  2/3 gated on the af-backfill lock", appending a re-verification note) AND **slot 11** `current_task=...batch2-001`
  (pane: reverted league_data_other.py back to unchanged 999 lines, "only the issue doc has real changes now", committed
  e15b1ac0c, running QG to quickmerge).
- Outcome: both converged on PM-repo doc-only work; slot 11 reverted its curated-universe code, so no same-file code
  conflict. Main messaged slot 11 to yield to owner slot 4, but slot 11 had already committed + was mid-quickmerge when
  the message arrived (same "warning after the worker already committed" timing as incident 1). Residual: a possible
  rebase/merge on the shared batch2-001 issue doc (quickmerge STAGE 0.4 auto-reconciles) and a possible double-/done
  (backend should dedup).

## Root-cause hypothesis (for a BACKEND owner to confirm against the dispatch + failover path)

A `failover_allowed=true` task appears to be re-dispatched to a freed worker when the current owner stops heartbeating
during a long silent operation (a multi-minute `quality-gates.sh` run produces no ping), WITHOUT first confirming the
prior owner has released the task. The prior owner's slot-side `current_task` is not cleared on re-dispatch, so both
workers run the same task's completion path in parallel. Candidate mechanisms: (a) the failover/stale-owner timeout is
shorter than a normal QG run, so a healthy-but-silent worker looks dead; (b) no "release confirmation" /
lease-revocation handshake before re-dispatch; (c) the freed worker's dispatch evaluation does not check whether the
task is already in-flight on another live slot.

## Todos

- [ ] [BACKEND] P2. Before re-dispatching a `failover_allowed` task off an apparently-silent owner, require a positive
      release signal (lease expiry with a liveness re-check, e.g. `kill -0` the owner's worker PID, or an explicit
      owner-side release) rather than ping-staleness alone — a long `quality-gates.sh` run must not look like death.
      **Done when**: a worker that goes silent for a full QG run (>~4min) but is provably alive (PID up, forward
      progress in its pane/log) does NOT have its in-flight task re-dispatched, with a test simulating a
      silent-but-alive owner.
- [ ] [BACKEND] P3. On re-dispatch, clear/curl-invalidate the prior owner's slot-side `current_task` (and surface a loud
      log naming both slot ids + the task) so `/api/state` never shows one task `working` in two slots — makes the
      condition observable instead of something main has to catch by pane inspection.
- [ ] [BACKEND] P3. Make `/done` idempotent + owner-checked: a second `/done` on an already-terminal task by a non-owner
      slot should no-op with a warning (not double-flip the checkbox or re-run reconciliation). Confirm current behavior
      against incidents 1 & 2 (slot 8 /done as non-owner of record for sigabrt; slot 11 potentially /done batch2-001 as
      non-owner).

## Triage / charter note

Main (agt-52bb99) diagnosed read-only (per-task `/api/backlog` + `/api/state` + sanctioned `tmux capture-pane` depth
inspection) and is charter-barred from editing dispatch/task state, killing/respawning slots, or hand-editing
backlog.yaml. Severity P2: a dispatcher correctness/throughput gap that wastes a full work-cycle per incident and risks
a double-/done, but self-mitigating so far (both incidents resolved to doc-only work with no code conflict because
workers independently detected the already-landed work — that is luck, not a guarantee). Filed per the big-finding
triage rule (cross-cutting throughput/correctness, recurred 2× in one window) and cross-linked to the same-window
autospawn-gap and DB-pool-wedge issues. Recommend a BACKEND worker confirm the failover/lease path.

## Incident 3 — deployment_registry_reaper_not_draining_stale_entries-001 (slots 3 & 5 → 3 & 6), ~11:40–12:25Z

The worst variant, and the first on a **CODE** task (deployment-api gunicorn/registry-reaper) rather than doc-only:

- The failover moved the task **AWAY from the worker holding the diagnosis**: slot 3 had root-caused it ("prod loads
  root-level gunicorn.conf.py") and was editing the fix, but went silent during repeated 14–19-min thinking runs (no
  heartbeat) → the dispatcher failed it over to slot 5 (`dispatched_to=5`), a fresh worker. Both then held it in
  `current_task=working`.
- An `ao-self-pull` `systemctl restart orchestrator` mid-incident **re-shuffled dispatch** and moved the second holder
  from slot 5 → slot 6 (`dispatched_to=6`) — the collision survived the restart, re-triggered by slot 3's ongoing silent
  runs. This shows the condition is not a one-shot race; a long-silent-but-alive owner is repeatedly re-failed-over.
- **Same-file code-conflict risk was REAL here** (not doc-only). Main coordinated read-only: messaged the fresh owner
  (slot 5, then slot 6) to HOLD and let slot 3 land its fix, then verify + `/done` as owner-of-record; told slot 3 to
  heartbeat during long runs and coordinate the `/done`.
- **Outcome: resolved WITHOUT conflict** — slot 3 shipped the fix (`deployment-api@3fe…`, "fix shipped + plan flipped"),
  slot 6 to verify + `/done`. No duplicate/conflicting commit landed. **But that clean outcome depended on main manually
  babysitting the collision across ~45min and a restart** — exactly the manual toil the BACKEND fix (todos above) should
  remove. Incident 3 upgrades the "self-mitigating / luck" caveat: on a code task the luck margin is thinner, and the
  restart-survival shows ping-staleness failover is too eager against a healthy long-silent worker.

## Incident 4 — sports_satellite_ao_dispatch_batch5-026 (slots 6 & 7), ~2026-07-26

Doc-only this time (no code collision), but a clean example of the SAME task_id live on two slots concurrently:

- Slot 6 (this worker) was dispatched `sports_satellite_ao_dispatch_batch5-026` (the CLV odds_targets export wrapper
  todo in `sports_satellite_ao_dispatch_batch5_2026_07_26.md`). Re-verified current repo state, found the two remaining
  implementation todos both required explicit operator sign-off before quickmerge and exceeded the dispatch's 1-hour
  estimate — escalated via `/blocked` (`BLK-2e9c9505`) asking whether to implement-and-hold or leave tracked/gated.
- Main's answer to `BLK-2e9c9505` revealed slot 7 held the SAME `task_id` and had ALREADY implemented the export
  (`unified-api-contracts@b95012ed` + `features-service@0f90702e`, QG-green, committed in slot 7's own clone, held
  pending a separate `BLK-ec018203` sign-off) — main explicitly flagged: "this task_id appears dispatched to both slot 6
  and slot 7 — flagging the apparent double-dispatch; the correct single owner is slot 7."
- Slot 6 stood down via `/skip-current-task` (reason: double-dispatch, same-file collision avoidance) rather than
  re-implementing the same files. No collision landed — but only because slot 6 asked before touching the files; had
  slot 6 started building blind (a reasonable move given `can_continue: true` on its own blocked question), it would
  have hit the exact same-file conflict Incident 3 warns about, on a leakage-safety-sensitive cross-repo change this
  time.
- Corroborates: the double-dispatch condition isn't limited to failover-after-silence (Incidents 1-3) — this instance
  showed no visible silence/ping-staleness trigger from slot 6's side; the SAME task_id was simply live on two slots at
  once, discovered only because slot 6 happened to ask a question before acting rather than starting an implementation
  blind.
