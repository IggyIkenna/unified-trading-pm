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
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer, admin]
tags:
  [agent-orchestrator, worker-lifecycle, quickmerge, orphan-reaper, frozen-pane, false-done, kicker, detached-process]
related:
  [
    /plans/archive/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-24
author: unknown
last_updated: 2026-07-24
priority: P1
parent_epic: orchestrator_master
source: "review(slot-1) msgs 1884/1887 + main on-host process investigation, 2026-07-24"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
  "All 3 todos done: reaper CPU-progressing guard `agent-orchestrator@f91b4d0` (2026-08-08), `/done` sha-on-origin gate
  `tuning.done_require_origin` (pre-2026-08-14), orphaned-commit recovery closed moot 2026-08-10 (superseding commit
  `features-service@7ea10aaa` confirmed a live origin ancestor). Codex-aligned into
  `/codex/04-architecture/agent-orchestrator-worker-liveness.md` and `…-backlog-state-alignment.md`. Archived 2026-08-14
  (code-audit sweep)."
locked_by:
context_scope:
  [
    /plans/archive/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    agent-orchestrator/server/orphan_reap.py,
    scripts/quality_gates/check_evidence_backed_completion.py,
    /plans/archive/issues/watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md,
  ]
depends_on: []
---

> **🟢 ARCHIVED 2026-08-14** — `status: resolved`, all 3 todos `[x]`, unlocked; archived per
> [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md).
> The reaper CPU-progressing guard is codex-aligned at
> [`/codex/04-architecture/agent-orchestrator-worker-liveness.md`](/codex/04-architecture/agent-orchestrator-worker-liveness.md)
> § "`orphan_reap.py::sweep_orphan_processes` spares a CPU-progressing detached quickmerge"; the `/done` sha-on-origin
> gate is aligned at
> [`/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md`](/codex/04-architecture/agent-orchestrator-backlog-state-alignment.md)
> § "`/done`-time completion-acceptance gates". Sibling doc:
> [`orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md`](/plans/archive/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md)
> (archived same session, same `/done`-handler file-collision this doc's Progress Log tracked).

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
   `/plans/archive/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md`).

## Why it matters

Two distinct defects compound:

- **Reaper over-eagerness**: a detached quickmerge whose QG subprocess is actively CPU-progressing is a legitimate
  in-flight operation, not an orphan to reap. Reaping it wastes the QG run and guarantees the commit never lands.
- **/done accepted before code-on-origin**: the server marked `-010` done on evidence at 21:02 while the push was still
  in flight (and then never completed). A `/done` whose code is not yet on origin should not read as durably done — this
  is the false-done surface (task says done, `git-health` says `ahead=2`).

## Todos

- [x] ✅ [INFRA] P1. Make the orphan-reaper / frozen-pane kicker NOT kill a detached quickmerge whose QG child is
      actively CPU-progressing (check the descendant process tree for a running pytest/basedpyright/ruff with recent CPU
      before classifying `kind=frozen` + reaping). A pane waiting on a live detached quickmerge is not frozen. **Done
      when**: a slow (>5min) detached quickmerge on a heartbeat-silent pane completes + lands rather than being reaped;
      add a regression covering "pane waiting on CPU-progressing detached child". — agent-orchestrator@f91b4d0
      (`fix(orphan-reap): spare CPU-progressing detached quickmerge from sweep`): `_has_cpu_progressing_descendant`
      helper + guard in `sweep_orphan_processes`; two discriminator regression tests added in
      `test_orphan_process_reap.py` (CPU-progressing → spared; idle → still reaped).
- [x] ✅ [INFRA] P1. Close the false-done gap: gate `/done` acceptance (or a fast follow-up verifier) on the task's code
      actually being on origin for code tasks — a `/done` with the slot clone still `ahead>0` on the touched repo should
      flip the task back to a landing-pending state, not read as durably done. Cross-ref
      `check_evidence_backed_completion.py`. **✅ VERIFIED DONE 2026-08-14 (code-audit sweep)** —
      `agent-orchestrator/server/config.py:1235` `tuning.done_require_origin` (default `True`) gates
      `server/routes/slots_worker.py:2403-2429`, which 409s (`sha_not_on_origin`) any `/done` whose sha verifies locally
      but isn't found on any origin branch, per commit history tied to the now-archived
      `ao_done_require_origin_not_enforced_2026_07_29` doc.
- [x] ✅ [INFRA] P1. ~~Recover the orphaned commits on BOTH victim slots via a live-pane path, then confirm code on
      origin~~ — **CLOSED MOOT 2026-08-10 (ao full-tranche sweep, group 3)**. The 2026-07-31 conflict-gated re-triage
      flagged this as "very likely moot" (both source plans fully archived with 0 open todos) but left the actual
      "5-minute direct check" undone. Ran it: the sports pipeline-middle-leg-check work these `-010`/`-011` tasks were
      both attempting is confirmed landed via a later, independent, SQUASHED commit —
      `plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md:337` records **`features-service@7ea10aaa`**
      explicitly as a "corrected citation — `4639106a` never reached origin; quickmerge hit repeated host-contention
      timeouts + a strict-quickmerge trailer conflict from two separate manual commits, resolved by squashing to one
      commit before the final green quickmerge run" — i.e. the orphaned slot-9/slot-8 work was superseded/re-shipped as
      one clean commit rather than needing individual recovery. Independently confirmed `7ea10aaa` is a live ancestor of
      `origin/live-defi-rollout` (`git merge-base --is-ancestor` from a live `features-service` checkout, 2026-08-10).
      No recovery action needed; the orphaned local commits in slots 9/8's now-long-gone clones were simply abandoned in
      favor of this superseding work.

## Second occurrence — slot 8 / `-011` (review slot-1 flag + main verify, 2026-07-24)

Confirmed a **second victim** of the same mechanism (review slot-1 msg 1892; main on-host verify 22:5x):

- Slot 8 has been `working` `sports_closeout_batch1_ao_ready-011` continuously since ~20:52 (>2h), `worker_alive=false`
  - `tmux_alive=true` (stale/dead pane), `last_msg: "↻ resumed after heartbeat-silence (context intact)"` — the
    worker_alive flag flaps true/false with repeated heartbeat-silence resumes and no landed commit.
- features-service diverged `ahead=2, behind=7` unchanged since 20:33:48 (committed-but-unpushed, and now also stale
  behind the branch).
- Root-cause detail added by this instance: slot 8's own earlier `last_msg` cited **full `quality-gates.sh` killed 5× by
  severe shared-host memory/CPU contention** — directly linking this defect to the host-oversubscription condition
  already operator-flagged 2026-07-24. The QG never completes → the detached quickmerge never lands → the pane reads
  frozen → reaper/kicker churn, same terminal state.
- Impact: `-011` is the **sole** remaining prereq blocking `sports_closeout_batch1_finalize-001` — this is not an
  isolated cosmetic false-done, it is holding the sports-closeout critical path.

## Notes

- Operator flagged 2026-07-24 (host load + this defect). Now confirmed **NOT isolated to slot 9** — slot 8 is a second
  victim on the critical path (>2h), so the fix + recovery scope must cover both, and the shared-host QG-kill root cause
  (memory/CPU contention) is a shared driver with the host-oversubscription flag.
- Sibling: /plans/archive/issues/killed_slot_orphans_committed_unpushed_work_no_push_path_2026_07_21.md (the orphaned
  commit terminal state); this doc adds the specific reaper-vs-in-flight-quickmerge mechanism that produces it.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — all 3 open todos are held by established rulings in
  `ao_satellite_ao_dispatch_batch1_2026_07_26.md`: the `[INFRA] P1` reaper fix is named in the conflict-gated
  worker-liveness cluster, the `[INFRA] P1` `/done` on-origin gate 'must land as one change' with
  `orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md`'s `/done` item and interacts with the unresolved
  operator-merge-gate question, and the `[INFRA] P1` slot-8/slot-9 commit recovery is in the operator-decision list
  ('needs foreign-worktree access plus a judgment call on whether specific commits are superseded').
- **2026-07-31 (conflict-gated re-triage)**: Three findings. (1) The `/done`-on-origin gate item's blocking governance
  question is now ANSWERED — `watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md`'s gate-aware sweep
  shipped `agent-orchestrator@49c919d`; this item is unblocked and ready to work directly (still unbuilt). (2) The
  reaper-overeagerness item (CPU-progress-on-descendant-process-tree check) is a DIFFERENT check than the shipped fix
  (which gates on `last_ping`/blocked-queue state, not process-tree CPU) — confirmed by direct code read, still unbuilt,
  not resolved by anything shipped so far. (3) **The slot-8/slot-9 commit-recovery item is very likely MOOT** — both
  source plans that carried the blocked critical-path work
  (`/plans/archive/2026_07/sports_closeout_batch1_ao_ready_2026_07_24.md`,
  `/plans/archive/2026_07/sports_closeout_batch1_finalize_2026_07_24.md`) are now fully ARCHIVED with 0 open todos and
  evidenced completion on every item, including the sports middle-leg feature work this doc's `-010`/`-011` tasks were
  part of. Neither archived plan names this doc directly or these specific slot/sha pairs, so this is inference from
  "the blocking critical path fully landed and archived" rather than a direct commit citation — worth a 5-minute direct
  check (does `features-service` have BOTH commits from slots 9 and 8 on origin, or did only one supersede the other)
  before formally closing this item, but not treated as still-live work.
- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries) — added
  `/plans/archive/issues/watchdog_unpushed_sweep_defeats_operator_merge_gate_2026_07_26.md`, the archived doc whose
  shipped gate-aware sweep (`agent-orchestrator@49c919d`) unblocked the still-open `/done`-on-origin-gate todo.
- **context-scout 2026-08-03** (re-scout pass, updated methodology): re-verified all 5 entries resolve on disk (sibling
  issue + codex SSOT + reaper source + evidence-gate QG check + the archived unblocking fix) — no changes.
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).

- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 3)**: closed the orphaned-commit-recovery todo as MOOT
  (see the checkbox above for the evidence chain -- features-service@7ea10aaa confirmed the superseding landed work,
  independently re-verified as a live origin ancestor). **The remaining [INFRA] P1 item (gate /done acceptance on
  code-on-origin) stays KEEP-NA** -- it touches the same /done completion path (server/routes/slots_worker.py) that 2
  OTHER currently-active docs (cicd_escalation_agentrow_archived_prematurely_mid_session_2026_07_29.md,
  data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md) also have real open work against -- a genuine
  file/logic-collision risk on dispatch-critical-path completion-acceptance code, not a stale gate. Doc goes from 2 open
  items to 1.
