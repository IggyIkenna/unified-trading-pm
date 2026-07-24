---
doc_type: issue
title:
  Orphan-reaper kills an in-flight detached quickmerge whose QG is actively CPU-progressing, on a frozen-pane slot —
  producing a false-done (task marked done server-side, code committed-but-unpushed) with no automatic push path
summary: >-
  On a slot whose worker pane freezes (worker_alive=false, tmux_alive=true), a quickmerge launched detached (reparents
  to PPID=1) keeps running its QG independently of the pane. The frozen-pane kicker reads the waiting pane as
  kind=frozen/ping_advanced=false and the orphan-reaper then KILLS the detached quickmerge — even while its QG pytest is
  actively CPU-progressing (measured 66.8pct CPU, full features-service unit suite + coverage) — before it can push. No
  exit file is written (killed, not clean-exit), the code stays committed-but-unpushed in the slot clone (ahead=2), and
  because the worker already posted /done (accepted on evidence at 21:02), the task reads done server-side while the
  code never lands. spawn_retry_cap_reached + worker death then leave no automatic retry. Confirmed on-host 2026-07-24
  for sports_closeout_batch1_ao_ready-010 (slot 9, ip-172-31-5-118): features-service ahead=2 unchanged ~80min,
  quickmerge PID 2949777 (PPID=1) reaped after 5+min of progressing QG with no /tmp/qm_detached2.exit written.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags:
  [agent-orchestrator, worker-lifecycle, quickmerge, orphan-reaper, frozen-pane, false-done, kicker, detached-process]
related:
  [
    /plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-24
last_updated: 2026-07-24
priority: P1
parent_epic: orchestrator_master
source: "review(slot-1) msgs 1884/1887 + main on-host process investigation, 2026-07-24"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
---

# Reaper kills in-flight detached quickmerge → false-done + orphaned unpushed commit

## What happens (on-host evidence, ip-172-31-5-118, slot 9, 2026-07-24)

1. Slot 9 works `sports_closeout_batch1_ao_ready-010` (features-service sports middle-leg check), commits the code
   (features-service `ahead=2`, clean, no `index.lock`), posts `/done` at 21:02 — the server accepts it on the cited
   evidence and marks the task `done` server-side.
2. Under host CPU contention (load spiked to 38 on 8 cores from ~11 concurrent QG), slot 9's pane goes heartbeat-silent;
   its quickmerge is launched **detached** (PID 2949777, `PPID=1`) so it survives the pane. Its QG is a full
   features-service unit suite + coverage run — minutes long, longer under load.
3. The frozen-pane kicker reads the waiting pane
   (`pane_tail: "Waiting for the detached quickmerge process to complete"`) as `kind=frozen`, `ping_advanced=false`;
   `worker_kicked` fires repeatedly (21:34–21:48), `spawn_retry_cap_reached` at 21:45, and `orphan_process_reaped` fires
   (21:48–21:49).
4. The reaper **kills the in-flight detached quickmerge while its QG pytest is actively CPU-progressing** (measured PID
   3064155 at 66.8% CPU, correctly parented under the quickmerge chain 2949777→2949778→2991728). No
   `/tmp/qm_detached2.exit` is written — it was killed, not a clean non-zero exit.
5. Net: the code never pushes (stays `ahead=2`), the worker dies (`worker_alive=false`), retry cap is reached, and the
   task reads `done` with the code **absent from origin ~80min later** — a false-done + orphaned committed-unpushed work
   with no automatic push path (same terminal state as
   `/plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`).

## Why it matters

Two distinct defects compound:

- **Reaper over-eagerness**: a detached quickmerge whose QG subprocess is actively CPU-progressing is a legitimate
  in-flight operation, not an orphan to reap. Reaping it wastes the QG run and guarantees the commit never lands.
- **/done accepted before code-on-origin**: the server marked `-010` done on evidence at 21:02 while the push was still
  in flight (and then never completed). A `/done` whose code is not yet on origin should not read as durably done — this
  is the false-done surface (task says done, `git-health` says `ahead=2`).

## Todos

- [ ] [INFRA] P1. Make the orphan-reaper / frozen-pane kicker NOT kill a detached quickmerge whose QG child is actively
      CPU-progressing (check the descendant process tree for a running pytest/basedpyright/ruff with recent CPU before
      classifying `kind=frozen` + reaping). A pane waiting on a live detached quickmerge is not frozen. **Done when**: a
      slow (>5min) detached quickmerge on a heartbeat-silent pane completes + lands rather than being reaped; add a
      regression covering "pane waiting on CPU-progressing detached child".
- [ ] [INFRA] P1. Close the false-done gap: gate `/done` acceptance (or a fast follow-up verifier) on the task's code
      actually being on origin for code tasks — a `/done` with the slot clone still `ahead>0` on the touched repo should
      flip the task back to a landing-pending state, not read as durably done. Cross-ref
      `check_evidence_backed_completion.py`.
- [ ] [INFRA] P1. Recover `-010` now: land slot 9's orphaned features-service commit (`ahead=2`, clean) via a live-pane
      path (respawn slot 9 so a fresh worker re-runs quickmerge with a non-orphaned pane, OR operator lands the
      committed SHA), then confirm `-010` code is on origin. Do NOT leave it false-done.

## Notes

- Operator flagged 2026-07-24 (host load + this defect). Fleet otherwise healthy (12 working, done-count climbing) —
  this is isolated to slot 9's frozen-pane case, not a fleet-wide stall.
- Sibling: /plans/active/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md (the orphaned
  commit terminal state); this doc adds the specific reaper-vs-in-flight-quickmerge mechanism that produces it.
