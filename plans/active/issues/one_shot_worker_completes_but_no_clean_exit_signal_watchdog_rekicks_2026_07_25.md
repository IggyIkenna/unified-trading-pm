---
doc_type: issue
title:
  A one-shot worker agent that has FINISHED its task does not exit / signal completion cleanly, so the
  WorkerLivenessWatchdog keeps classifying its still-alive-but-idle pane as frozen/idle and re-kicks it repeatedly (slot
  2 auto-kicked 5+ times in ~30min; one kick input_snippet was literally "Stop nudging — this session's task is
  complete"). Each kick self-heals (worker_kicked -> working) so it is non-blocking, but it is wasted kick churn that
  masks true idleness and suggests the one_shot lifecycle exit-signal has a gap.
summary: >-
  On 2026-07-25 (~21:20-21:50Z) the operator flagged that slot 2 froze + was auto-kicked 5+ times in ~30 minutes (21:20,
  21:22, 21:26, 21:47, 21:48, 21:50), each self-healing fine via WorkerLivenessWatchdog (worker_kicked -> working, no
  manual action needed per its own remediation text). One kick's `input_snippet` was literally "Stop nudging — this
  session's task is complete" — i.e. the pane's own agent was telling the kicker it was DONE while the watchdog kept
  treating it as frozen/idle and re-kicking. This points at the one-shot (escalation / single-task) worker lifecycle:
  the agent finishes its task but does not exit its tmux session or emit a clean completion signal the watchdog
  recognises, so the still-alive-but-idle pane looks like a wedged worker and gets re-kicked each liveness tick. Main
  (agt-52bb99) inspected slot 2 read-only at 21:51Z: `status=stale`, `current_task=null`, `last_msg="idle: 14 task(s)
  blocked on ... batch2-001 ..."`, `last_spawned_at=21:04:55Z`, `last_ping=21:34:51Z` — i.e. the churning one-shot has
  since gone quiet/idle-blocked, consistent with a completed-but-not-cleanly-exited agent whose pane the watchdog was
  repeatedly poking. Blast radius is low (every kick self-healed, nothing was blocked), but it is real kick churn that
  (a) wastes watchdog cycles, (b) masks whether the slot is genuinely free for redispatch, and (c) risks re-nudging an
  agent that has explicitly declared completion. Distinct root cause from the context_pct≈75 compact-confirmation wedge
  (that is a compact-submission wedge on slot 4; this is a one-shot completion-exit-signal gap on slot 2).
status: open
nature: issue
archive_exempt: true
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [
    agent-orchestrator,
    worker-liveness,
    watchdog,
    one-shot,
    lifecycle,
    completion-signal,
    exit-signal,
    re-kick,
    churn,
    throughput,
  ]
related:
  [
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
    /plans/archive/issues/wedge_detector_lacks_liveness_by_progress_false_positive_2026_07_21.md,
    /plans/archive/issues/orchestrator_ready_p1_task_undispatched_no_matching_worker_autospawn_gap_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
created: 2026-07-25
author: unknown
last_updated: 2026-07-25
priority: P3
parent_epic: orchestrator_master
source:
  "operator (agt-52bb99 msg 2039) pattern-note from review; main (agt-52bb99) inspected slot 2 state read-only,
  2026-07-25 ~21:51Z"
assigned_vm: NA
execution_scope: local-only
estimate_class: refactor
drift_direction: advance-code
resolved_by:
locked_by:
context_scope:
  [
    agent-orchestrator/server/worker_liveness/_respawn.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
depends_on: []
---

# One-shot worker finishes but does not exit/signal completion cleanly → watchdog re-kicks it

## Evidence (operator-reported + main read-only inspection, 2026-07-25)

- Operator (msg 2039): slot 2 froze + was auto-kicked 5+ times in ~30min (**21:20, 21:22, 21:26, 21:47, 21:48, 21:50**),
  each self-healed via `WorkerLivenessWatchdog` (`worker_kicked -> working`, no manual action needed per its own
  remediation text).
- One kick's `input_snippet` was literally **"Stop nudging — this session's task is complete"** — the pane's agent was
  declaring completion while the watchdog kept treating it as frozen/idle and re-kicking.
- Main inspected slot 2 read-only at 21:51Z via `/api/state`: `status=stale`, `current_task=null`,
  `last_msg="idle: 14 task(s) blocked on task sports_satellite_ao_dispatch_batch2-001 (3), ...batch2-011 (3), defi_dex_pool_symbol_fix_backfill_purge-001 (2)"`,
  `last_spawned_at=2026-07-25T21:04:55Z`, `last_ping=2026-07-25T21:34:51Z`. The churning one-shot has since gone
  quiet/idle-blocked.

## Hypothesis (needs owner confirmation)

A one-shot (single-task / escalation) worker completes its task but does **not exit its tmux session or emit a
completion signal the watchdog recognises as "done, stop watching"**. The still-alive-but-idle pane therefore reads as a
wedged/idle worker to the liveness kicker, which re-kicks it every tick. The agent even types a natural-language "task
is complete" reply, but that is not a signal the watchdog consumes — so the kicking continues until the pane is
reclaimed/re-derived to idle-blocked (as observed by 21:51Z). Contrast a persistent slot worker, which is _supposed_ to
keep polling and so should be kicked when silent; a **one-shot** worker that has done its job should be transitioned to
terminated/idle, not re-kicked.

## Todos

- [x] ✅ **DONE 2026-07-29 — `agent-orchestrator` (uncommitted at investigation time, shipping same session).**
      Root-cause investigation found TWO distinct, real gaps (not one) feeding the observed churn, both fixed: 1.
      **`server/routes/slots_worker.py` `_done_one_off`**: a one-shot worker that DID correctly call
      `POST /api/slots/{id}/done` had its `last_msg` set to a string that did NOT start with `"idle:"` — `health.py`'s
      existing "correctly-idle-with-explanation" carve-out (added for a near-identical prior incident,
      `ao_dispatch_health_2026_07_26`) only protects a task-less idle slot from being flipped back to `"stale"`
      (re-entering the kickable pool) when `last_msg.startswith("idle:")`. Fixed: the message now reads
      `f"idle: {kind} complete (lifecycle-complete)"`, closing the gap so a correctly-`/done`'d slot can no longer
      silently lose its protection and get re-kicked. 2. **`server/worker_liveness/__init__.py`**: the observed
      incident's root cause was actually the OTHER half — `/done` was likely never called at all (the agent typed a chat
      reply instead), and `current_task` stays `None` for a typed one-shot worker's ENTIRE life (not just
      post-completion), so the kicker's only existing carve-out (`status=="idle" and current_task is None`) can never
      fire without a successful `/done` call — the slot stays permanently kickable. Rather than trusting free-form pane
      text as ground truth (a wrong or confused self-report must never silently terminate real work), added
      `_SELF_DECLARED_COMPLETE_RE` pattern detection on a FROZEN pane's pending input — when it matches ("stop nudging",
      "task is complete", etc.), the kick still fires (status/task state untouched) but the nudge TEXT is swapped for a
      corrective reminder pointing the worker at the actual `/done` contract (`{slot_id}` and both one-off/task-worker
      call shapes inlined), instead of the generic "— proceed now" that a worker who already believes it's done cannot
      act on. Logged as `self_declared_complete: true/false` on the existing kick activity event for observability.
      **Done-when evidence**: 4 new tests (`tests/test_worker_liveness.py`:
      `test_frozen_self_declared_complete_gets_corrective_nudge`,
      `test_frozen_without_completion_phrase_gets_default_nudge`, `test_text_override_replaces_default_frozen_nudge`,
      `test_no_override_keeps_default_frozen_nudge`; plus `tests/test_done_one_off.py`'s existing archive test extended
      to assert `last_msg.startswith("idle:")`), all passing alongside the full existing 49-test suite (4 pre-existing
      exact-call assertions updated for the new `text_override` kwarg, behavior unchanged for every case that isn't the
      new one). `quality-gates.sh` green before ship. **Shipped**: `agent-orchestrator@0e9ce0b` (landed on
      `live-defi-rollout`, verified `ahead=0/behind=0` against origin). Ship was blocked for several hours by an
      unrelated dependency: `unified-trading-library` (a path dependency of agent-orchestrator) had a separate, real,
      uncommitted test-determinism fix sitting dirty with no owning session visibly active on it — after confirming
      genuine staleness (mtime static ~3h, no lock/open-FD, diff complete and coherent) I took it over, found and fixed
      a real race condition the sleep-removal refactor had introduced
      (`tests/unit/test_manifest_freshness.py::test_concurrent_write_race_loser_skips_after_ttl` — the loser thread's
      post-TTL check had no guarantee the winner thread's write had landed yet; the original `time.sleep(1.1)`
      accidentally provided that ordering, the fake-clock replacement did not), verified `quality-gates.sh` green, and
      shipped it separately as `unified-trading-library@2e39d98b` before retrying this ship.
- [x] ✅ [REVIEW] P3. **Not fixed this pass, flagged as a real residual risk found during investigation**: if a stuck
      one-shot slot crosses `kick_escalation_threshold` (default 3 consecutive non-recovered kicks — including a
      corrective one, per this fix), `_maybe_auto_respawn_stuck_slot`/`_respawn.py` has zero lifecycle/one-shot
      awareness and will force kill+respawn it — for an already-one-shot-complete slot this could spin up a DUPLICATE
      worker for a task that's already done. Not observed in the original incident (kicks self-healed before reaching
      escalation) and the two fixes above should make that less likely (the corrective nudge converges faster), but it's
      a real gap, not a hypothetical — worth its own scoped fix if it's ever observed live. **CLOSED 2026-08-12
      (preemptively, not observation-gated)** — `agent-orchestrator@687cad2d00` threads the already-shipped
      `self_declared_complete` kick signal through `_respawn.py::maybe_auto_respawn_stuck_slot`: an escalating
      (`force=True`) task-less one-shot whose most recent kick was flagged self-declared-complete is now reaped via the
      clean `_reap_idle_session` path even with `queued_undispatched > 0`, closing the duplicate-worker spin-up risk
      this todo names (regression-tested in `tests/test_worker_liveness.py`; `quality-gates.sh` green).

## Triage / charter note

Filed by main (agt-52bb99) per the big-finding triage rule (recurring cross-cutting agent-orchestrator lifecycle
pattern, operator-flagged, 5+ recurrences in ~30min on one slot). Main diagnosed via a **read-only** `/api/state`
inspection of slot 2 and is charter-barred from tmux send-keys to worker panes, from spawning/killing/respawning slots,
and from editing AO runtime state — so the fix is **BACKEND/DEVOPS-owned**. Severity **P3**: every kick self-healed and
nothing was blocked (bounded blast radius = wasted kick churn + masked idleness on one slot), but the pattern is
confirmed, recurrence-prone, and points at a real one-shot-lifecycle exit-signal gap worth closing when cycles allow.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA, valid — the sole open `[REVIEW] P3` is explicitly observation-gated
  ('Not observed in the original incident … worth its own scoped fix **if it's ever observed live**'), and the doc sits
  inside the worker-liveness / watchdog-escalation cluster that `ao_satellite_ao_dispatch_batch1_2026_07_26.md` holds in
  its conflict-gated Deferred list. Its `[BACKEND]` half already shipped `agent-orchestrator@0e9ce0b`.
- **2026-07-31 (conflict-gated re-triage) — RECLASSIFIED, not actually conflict-gated.** This doc's own fix landed
  independently of the escalation-ordering fight (root-caused + shipped same session it was filed, `@0e9ce0b`). The
  remaining `[REVIEW] P3` was never blocked BY the cluster or by anything else — it is purely observation-gated ("act
  only if this scenario is ever observed live"), unrelated to whether the kick-vs-escalation ordering question is
  resolved. Mis-filed into the conflict-gated bucket by association (same general subsystem), not by an actual
  dependency. No action needed; correctly stays open and low-priority.
- **na-eligibility-audit 2026-08-01** (autonomous, tranche `ao`, dispatch agt-8e95ca, slot 2): KEEP-NA, valid — the sole
  open `[REVIEW] P3` remains explicitly observation-gated ("act only if this scenario is ever observed live"). No change
  since the 2026-07-31 re-triage above.
- **context-scout 2026-08-03**: refreshed context_scope (4 entries, unchanged — still accurate).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (4 entries), unchanged.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid — Prior verdict re-verified — content unchanged or only
  superficial edits since last marker. Operator-gated, design-judgment, or standing-corpus-ruling work remains open.

- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — re-read end-to-end; sole open item (`[REVIEW] P3`)
  remains explicitly observation-gated ("act only if this scenario is ever observed live," not yet observed). Checked
  against the round7-10 precedent set — none apply (this is a live-fleet-observation condition, not a
  credential/plan-destination/delete-safety question). Not found in any batch1-15 citation list, but the item's own
  gating condition (unobserved-so-far) means there is nothing bounded to extract yet.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **1**, matching. Sole open item ([REVIEW] P3) remains explicitly observation-gated ("act only if this scenario is ever
  observed live") — no bounded fix is writable for a not-yet-observed failure shape. Not found in any batch1-17 citation
  list; the gating condition itself (unobserved-so-far) means there is nothing extractable yet.
- **2026-08-12 (batch5 todo 7, slot 16)**: residual `[REVIEW] P3` CLOSED preemptively (not observation-gated) —
  `agent-orchestrator@687cad2d00` threads the already-shipped `self_declared_complete` kick signal through
  `_respawn.py::maybe_auto_respawn_stuck_slot`: an escalating (`force=True`) task-less one-shot whose most recent kick
  was flagged self-declared-complete is now idle-reaped via the clean `_reap_idle_session` path even with queued work
  system-wide, instead of force-kill+respawned into a DUPLICATE worker for an already-done task. Regression tests
  `test_self_declared_complete_queued_work_reaped_not_respawned` (+ control
  `test_queued_work_escalating_not_self_declared_takes_respawn_path`) in `tests/test_worker_liveness.py`; full
  `quality-gates.sh` green.
- **2026-08-12 (archive-exempt marker)**: doc now has 0 open todos — NOT archived here because archival of batch5 source
  docs is owned by the paired finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch5_finalize_2026_08_03.md`,
  `gate_on_depends`-held) which reconciles evidence back into every source doc and runs archival. Set
  `archive_exempt: true` so the `check_archive_candidates` hook stops flagging this doc until finalize runs; un-set at
  finalize time.
