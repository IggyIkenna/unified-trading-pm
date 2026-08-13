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
asset_group: [ao]
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
    /plans/archive/issues/orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md,
    /plans/active/issues/orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    /codex/04-architecture/runtime-deployment-topology.md,
  ]
created: 2026-07-25
author: unknown
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
context_scope:
  [
    /plans/active/issues/reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md,
    /plans/active/issues/cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md,
    /plans/active/issues/data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md,
    agent-orchestrator/server/routes/slots_worker.py,
    agent-orchestrator/server/dispatch.py,
  ]
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

- [x] [BACKEND] P2. Before re-dispatching a `failover_allowed` task off an apparently-silent owner, require a positive
      release signal (lease expiry with a liveness re-check, e.g. `kill -0` the owner's worker PID, or an explicit
      owner-side release) rather than ping-staleness alone — a long `quality-gates.sh` run must not look like death.
      **Done when**: a worker that goes silent for a full QG run (>~4min) but is provably alive (PID up, forward
      progress in its pane/log) does NOT have its in-flight task re-dispatched, with a test simulating a
      silent-but-alive owner. — **Shipped `agent-orchestrator@7911083`** (dispatched + executed via
      `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_2026_08_01.md`, full evidence there). Confirmed root
      cause: `WorkerLivenessWatchdog._reconcile_unacked_dispatches` (`server/worker_liveness_watchdog.py:963`) released
      a `dispatched` task past the 1800s ACK timeout back to `queued` on a SINGLE non-"working" pane-classify snapshot
      alone, with no real liveness check — then `dispatch.py`'s R5 `_target_slot_is_dead()` (600s ping-silence
      threshold, shorter than the 1800s that had just fired) let a DIFFERENT slot's `pick_next_task` claim the
      freshly-queued task moments later, while the true owner's pane was still alive. Fix requires `_pane_is_dead`
      (reusing the exact discriminator `_sweep_dirty_slots` already uses) before releasing. Proven by 3 new tests in
      `tests/test_worker_liveness_watchdog.py` replaying incident 1 and incident 2's slot shapes; the silent-but-alive
      test confirmed to FAIL pre-fix with the exact `"...requeued (pinned)"` warning. Full `quality-gates.sh` green.
- [x] [BACKEND] P3. On re-dispatch, clear/curl-invalidate the prior owner's slot-side `current_task` (and surface a loud
      log naming both slot ids + the task) so `/api/state` never shows one task `working` in two slots — makes the
      condition observable instead of something main has to catch by pane inspection. — **Shipped
      agent-orchestrator@82578c3** (dispatched + executed via
      `/plans/active/ao_satellite_ao_dispatch_batch6_2026_08_04.md`, full evidence there) — checkbox flipped by
      plan_reconciler agt-c7578b 2026-08-10, independently re-verified: `82578c3` confirmed ancestor of
      `origin/live-defi-rollout` and its commit message explicitly cites this exact todo. (batch6-finalize's own todo 2,
      which would normally do this reconciliation, is still open — flipping directly here since the source doc exited
      the 12h grace window and the evidence bar was independently met.)
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

## Incident 5 — perp-funding observed-cadence drift tracker on market-tick-data-service (slots 9 & 12), ~2026-08-03

- Surfaced by review (fleet-git-health, msg #3590, 2026-08-03) + confirmed by main (agt-1756f6): slots 9 AND 12 each
  independently produced the SAME feature commit on market-tick-data-service — slot-9 `0c5a472d` and slot-12 `e93d54ac`,
  both titled `feat(perp-funding): add observed-cadence drift tracker (GCS-persisted)`, slot-12 committed ~18:12Z /
  slot-9 ~19:02Z. Both are 1-ahead-unpushed and already safely captured on wip-preserve refs (no work lost); neither
  shipped.
- **TIMING — this is a POST-FIX recurrence, not stale residue** (verified by review #3593 via `git show`): the
  release-confirmation fix `agent-orchestrator@7911083` landed **2026-08-01T08:39Z**, but both dupe commits are
  **2026-08-03** (slot-12 18:12Z, slot-9 19:02Z) — ~2 days AFTER the fix. So the shipped `WorkerLivenessWatchdog`
  liveness-re-check did NOT prevent this occurrence.
- **HYPOTHESIS — possibly a DIFFERENT mechanism than Incidents 1-4** (for the backend/doc owner to confirm, not a
  main/review priority call): Incidents 1-4 were failover-RELEASE races (a task re-dispatched off an apparently-silent
  owner). This one presents as two slots concurrently building the SAME feature FROM SCRATCH — which could instead be a
  claim-time race (the same queued task claimed by two slots), a path the release-confirmation fix wouldn't cover. Worth
  a backend look at whether @7911083's gate covers concurrent-claim, or whether that's an uncovered delta.
- Resolution of THIS instance is a WORKER dedup (pick one commit, verify it meets the perp-funding done-definition, ship
  it, drop the other); main cannot push code, so it's flagged here rather than resolved by main.
- **RESOLVED — race self-resolved earliest-wins, no duplicate landed** (review msg #3602 + main agt-1756f6 verify,
  2026-08-03 ~22:10Z): there was actually a THIRD, EARLIER sibling — slot-10 `fd9efc85` (`17:30:57Z`, same
  `feat(perp-funding): add observed cadence-drift tracker`) — and IT is the one that LANDED (verified ancestor of
  origin/live-defi-rollout, 422L script + 371L test, single-walk + CAS + honest-skips). The two later dupes here
  (slot-12 `e93d54ac` ~18:12Z, slot-9 `0c5a472d` ~19:02Z) came AFTER and never became ancestors (confirmed not-on-LDR).
  So the concurrent-build race did occur (3 slots, not 2), but the ship-side gate held: **earliest-wins, exactly one
  landed, zero duplicate work reached origin.** This partially closes the HYPOTHESIS above — the
  claim-time/concurrent-build race is real (worth the backend look at whether @7911083 covers concurrent-claim), but its
  BLAST RADIUS on this occurrence was contained to wasted worker cycles on the two losing slots, not a duplicate
  landing. Loose end from this incident was a stale wrong-SHA citation in
  `/plans/archive/2026_08/issues/perp_funding_data_semantics_and_cadence_2026_06_16.md` (cited `840c816d` instead of the
  winner `fd9efc85`) — corrected 2026-08-03 (unified-trading-pm@8c75172e5).

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — all 3 open todos are held by established conflict-gated rulings
  in `ao_satellite_ao_dispatch_batch1_2026_07_26.md`: the `[BACKEND] P2` release-signal/liveness re-check 'turns on the
  same "is a silent worker actually dead" judgment as the [worker-liveness] cluster … so it must be sequenced after that
  ordering is ruled', and the `[BACKEND] P3` `/done` idempotency item shares `server/routes/slots_worker.py`'s `/done`
  handler with `reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md` ('must land as one change') and
  interacts with the unresolved operator-merge-gate governance question.
- **2026-07-31 (conflict-gated re-triage)**: Mixed. The `/done`-idempotency item's blocking governance question is now
  ANSWERED (`watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md` shipped `agent-orchestrator@49c919d`) —
  unblocked, still needs the combined `/done`-handler change with the reaper doc's item, still unbuilt. **The
  `[BACKEND] P2` release-signal/liveness-check item is STILL GATED, on a different basis than recorded**: verified by
  direct code read that the shipped kicker fix (`agent-orchestrator@64b5310`, `_progress_marker_shields_kick`) lives in
  `server/worker_liveness/__init__.py` and only shields the LIVENESS KICKER from false `worker_kicked` events — it does
  not touch the actual FAILOVER/re-dispatch path this item is about. Searched for the redispatch mechanism
  (`failover_allowed` is only ever consumed by `server/failover.py`, which is the cross-HOST/multi-VM module confirmed
  dead-in-practice, `fleet_registry_entries: 0`, per `ao_open_issues_consolidated_close_out_2026_07_17.md`'s B3 finding
  — NOT same-VM slot-to-slot failover) — the actual mechanism producing the observed same-VM double-dispatch incidents
  is not yet identified with confidence (checked `server/stale_dispatch.py::reclaim_stale_dispatches`, but it only fires
  when `tmux_session IS NULL`, which doesn't match "worker silently alive mid-QG-run" from the incident writeups). This
  item needs a real root-cause investigation before a fix can be scoped — flagging as a genuine open question, not a
  quick fix.
- **2026-07-31 (root-cause candidate found)**: `WorkerLivenessWatchdog._reconcile_unacked_dispatches`
  (`worker_liveness_watchdog.py:963`) is a strong candidate the original hypothesis missed. Any `status="dispatched"`
  task past `dispatch_ack_timeout_seconds` (default **1800s/30min**) with NO explicit ack event
  (`slot_progress`/`slot_done*`/`slot_blocked` — a worker doing normal tool-use turns for 30+ min without ever calling
  one of these emits none) AND whose pane does NOT classify `"working"` (spinner-present) **at the exact check instant**
  is released back to `queued` — `slot.current_task` is cleared if it matches, and a fresh dispatch can then hand the
  SAME task to a different slot while the original session is still alive and unaware. This matches "long silent
  quality-gates.sh run, no heartbeat" far better than `failover_allowed`. Two things keep this from being a confirmed
  root cause yet: (1) `classify_pane` returns `"working"` on a spinner, and a live QG subprocess call normally DOES show
  one — the mechanism would need a pane-read miss (host-load race, same class as
  `host_saturation_false_worker_kicks_stall_fleet_completions_2026_07_26.md`) or a genuinely spinner-less state (e.g. a
  DETACHED quickmerge, matching `reaper_kills_inflight_detached_quickmerge_false_done_2026_07_24.md`'s "waiting for the
  detached process" pane text) to actually misfire; (2) the reclaim PINS the task back to the SAME slot
  (`target_slot`+`affinity=high`), which mostly explains a slot re-claiming its own task, not necessarily a DIFFERENT
  slot picking it up — whether `affinity=high` is a hard filter or just a scoring bias against `dispatch.py`'s
  `_blocks_affinity` wasn't checked this pass. **Next step to confirm**: correlate the 4 incidents' timestamps against
  `slot_dispatch_unacked` activity-log rows for the same `task_id` — if present at the right time, this is confirmed; a
  live orchestrator DB query (read-only SSM), not something checkable from a dev checkout.

- **2026-08-01** (`ao_satellite_ao_dispatch_batch1_finalize_2026_07_26.md` todo 3): the watchdog-cluster ordering
  decision this `[BACKEND] P2` release-signal item was sequenced behind is ruled + shipped
  (`agent-orchestrator@64b5310`/`@77fc60a`). Re-checked for file-collision against the whole `plans/active` corpus —
  zero hits on `server/failover.py` — and drafted into
  `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_2026_08_01.md` (renamed from a mistakenly-numbered "batch 2"
  2026-08-01 — batches 2 and 3 already existed; `status: active`, operator-approved). The `[BACKEND] P3`
  `/done`-idempotency sibling is NOT included — it remains file-collision-held against `server/routes/slots_worker.py`
  (2 other active docs' open todos on the same file:
  `cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md`,
  `data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md`).

- **2026-08-01 (`[BACKEND] P2` shipped)**: confirmed the true call path is the two-stage chain the 2026-07-31 entries
  above were converging on — `_reconcile_unacked_dispatches` (release trigger, single pane-classify snapshot, no
  liveness check) followed by `dispatch.py`'s R5 `_target_slot_is_dead()` (the actual "different slot claims it"
  mechanism, via a shorter 600s ping-silence threshold than the 1800s ACK timeout that had just released the task).
  Fixed by requiring `_pane_is_dead` (reused, no new liveness logic) before release — `agent-orchestrator@7911083`.
  Proven by 3 tests replaying incident 1 (slots 2&8) and incident 2 (slots 4&11)'s shapes; the silent-but-alive test
  confirmed to fail against the pre-fix code with the exact recorded `"...requeued (pinned)"` warning. Full evidence +
  test names in `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch4_2026_08_01.md`'s own todo + Progress Log.
  `[BACKEND] P3` (`/done` idempotency) is untouched, still file-collision-held as recorded above.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid — of the 2
  remaining open items: the `/done`-idempotency item is genuinely still file-collision-held against
  `server/routes/slots_worker.py` (shared with 2 other active docs), a real current gate. The
  current_task-clearing-on-redispatch item's original conflict basis has since cleared (the watchdog-cluster ordering it
  was gated on is now ruled+shipped), and it now reads as bounded/deterministic on its own — but it still touches the
  same dispatch-critical-path territory (`dispatch.py`/`worker_liveness_watchdog.py`) the just-landed P2 fix and sibling
  batch3/batch4 plans deliberately sequenced around to avoid file collision. Since this corpus has no per-todo prereq
  syntax, flipping the whole doc's `assigned_vm` would expose the still-gated `/done` item to premature dispatch
  alongside it — correctly left NA as a doc, with the current_task-clearing item flagged as a candidate for its own
  future scoped AO-dispatch batch (a decision for `/ag-closeout-audit` or a future satellite-batch draft, not this run's
  verdict rubric, which only flips `assigned_vm` in place — never splits a doc).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) — dropped the now-archived `batch1` plan and the
  general single-vm-architecture codex (background, not load-bearing for the 2 remaining todos); added the 2 sibling
  docs sharing the `/done`-handler file-collision gate on `slots_worker.py` plus `dispatch.py` (the
  current_task-clearing item's other touched file).
- **Incident-6 — 2026-08-04 (review agt-10313c #3636 + main agt-1756f6 verify) — RESOLVED, earliest-wins held again**:
  `cve_affected_pinned_deps_remediation-006` (agent-orchestrator cryptography CVE-2026-69247 bump, from the fleet sweep
  main dispatched) double-dispatched to slots 10 and 11. Slot 11 won the race and shipped `agent-orchestrator@8b1ae78`
  (main-verified ON origin/live-defi-rollout — the CVE is genuinely closed); slot 10 (since killed) held a functionally
  IDENTICAL redundant local unpushed copy `1040985` (same override-dependencies pin/version, only comment wording +
  insertion point differ), never pushed, nothing unique to rescue. Same benign pattern as Incident-5: concurrent-build
  race occurred but the ship-side gate held — exactly one landed, zero duplicate reached origin. Slot 10's copy is
  cleaned by the pre-spawn drift-quarantine gate on its next respawn (no action needed). Recurrence of the class (now 6
  incidents) keeps this doc's dispatcher-dedup todos live: the backlog still occasionally hands one todo to two slots
  simultaneously — the earliest-wins ship gate is the working backstop, but the dispatch-side dedup remains the real
  fix.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
- **Incident-7 — 2026-08-09 (self-observed by slot 16) — RESOLVED, earliest-wins held again**:
  `sports_taxonomy_p3_consumers-004` ("wire the new sports arb detector into a live/batch producer") was live in both
  slot 16 (this worker) and slot 24 `current_task` simultaneously — this session's own `SessionStart` collision hook had
  already warned of a second live `claude` process in this slot's cwd, consistent with the general pattern. Both
  independently built a FULL working implementation from scratch (not doc-only, like Incidents 1/2/4): same 4 files
  (`features_service/sports/arb/runner.py`, `cli/handlers/arb_detect_handler.py`, `cli/main.py` diff,
  `tests/sports/unit/arb/test_runner.py`), materially different designs (slot 16 read raw per-bookmaker ticks via
  `read_odds_data`; slot 24 read MDPS's already-bucketed `read_bucketed_odds` with `scan_days`/dry-run support — the
  more complete design). Slot 24 won the race: committed + quickmerged `features-service@67de878d` (QG green) and
  flipped the plan checkbox with evidence at 17:51:01Z, all before slot 16's own QG run (queued ~14min behind a 6-deep
  host-governor backlog) had even finished. Slot 16 discovered the collision only by chance — a routine pre-commit
  `git status`/ahead-behind check surfaced `behind=1` against a locally-fetched `origin/live-defi-rollout` moments
  before its own (still-uncommitted) duplicate would have been shipped on top, which would have produced a same-file
  conflict-on-push (unlike incidents 1/2/4's doc-only convergence, or 5/6's never-touching-the-same-tracked- file
  races). Slot 16 discarded its uncommitted duplicate (`git restore` + `rm` the 3 untracked files — safe, never pushed)
  and fast-forwarded onto slot 24's shipped commit; zero duplicate landed, zero conflict. **New data point vs. Incidents
  5/6**: this is the closest call yet — the two implementations touched the exact same 4 file paths (unlike 5/6's
  byte-identical-diff CVE bump or independent single-file features), so a few more minutes' delay on slot 16's QG queue
  would have turned this into a genuine same-file push conflict rather than a clean discard. Corroborates the root-cause
  note above: no ping-staleness/silence was involved on slot 16's side (it was actively working, QG running) — this
  reads as the same concurrent-claim-time race flagged as an open hypothesis under Incident 5, now observed a second
  time on a CODE task with overlapping file paths.
