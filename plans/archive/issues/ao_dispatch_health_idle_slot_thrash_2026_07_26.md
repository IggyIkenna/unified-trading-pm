---
doc_type: issue
title:
  Idle slots correctly out of dispatchable work get misclassified as loop-dead, thrash-kicked, and respawn-churned for
  no net progress
summary:
  Live-diagnosed while investigating why fleet headroom sat open with real queued backlog work unclaimed for 27+ minutes
  straight during the 2026-07-26 backlog surge. Root cause — `HealthMonitor.check_once`'s idle-silence pass
  (server/health.py) cannot distinguish a task-less slot correctly following agents/worker.md's "final idle heartbeat
  then wait quietly" contract from a genuinely dead worker loop — both present identically (status=idle, live tmux
  session, 5+ min silence). It flips the correctly-idle slot to `stale`, firing `worker_polling_dead` and a
  `WorkerLivenessKicker` "frozen" nudge that can never produce real work (confirmed `ping_advanced=False` on every
  kick), and the slot is eventually torn down and respawned into the SAME unchanged backlog state. Confirmed live on
  slot 10 — 4 full respawn cycles in ~30 minutes, zero net dispatch progress. A separate, unrelated bug surfaced during
  the same investigation — `cursor-configs/hooks/context-threshold-nudge.sh`'s SINCE-LAST-COMPACT windowing (2026-07-25)
  crashes on every prompt submission for any session that hasn't yet compacted (the common case) due to a
  `grep`-under-`pipefail` exit-code bug, surfacing as noisy "UserPromptSubmit hook error" spam.
status: resolved
nature: record
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [orchestrator, health, worker-liveness, dispatch, idle-thrash, hooks, bash]
related:
  [
    /plans/archive/issues/ao_review_agent_spawn_db_lock_under_load_2026_07_26.md,
    /plans/archive/2026_06/orchestrator_spawn_reliability_db_lock_2026_06_10.md,
  ]
created: 2026-07-26
last_updated: 2026-07-26
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.2
source:
  Live-diagnosed via a dispatch-health watcher deployed this session (dispatch_health_watch.py, running on the
  orchestrator VM) that flagged sustained free-headroom-with-queued-work as an anomaly; traced through /api/state, the
  real activity log, and a read-only run of the orchestrator's own dispatch-eligibility filter chain
  (first_blocking_filter) against the live DB, then a full activity-log timeline for slot 10 showing the exact boot ->
  idle -> polling_dead -> kicked -> boot cycle repeating.
resolved_by: interactive session, 2026-07-26, agent-orchestrator@222a4be, unified-trading-pm (this commit)
locked_by:
supersedes:
superseded_by:
---

> **🟢 RESOLVED 2026-07-26** — both fixes shipped and verified in the same session; regression tests added for each,
> bug-injection-confirmed load-bearing before restoring.

# Idle-slot thrash: correctly-idle workers misclassified as loop-dead

## What I found

### Finding 1 (primary): idle-with-no-dispatchable-work gets treated as loop-dead

While investigating a dispatch-health watcher anomaly (free fleet-cap headroom + real queued backlog work unclaimed for
27+ minutes straight), I pulled slot 10's real activity-log timeline (`/api/activity?limit=500`, filtered to
`slot_id=10`). The pattern repeats identically across multiple respawns within the same 30-minute window:

1. `slot_boot` — a fresh Claude Code session boots.
2. The worker dispatches and correctly completes 2-3 real backlog tasks (with substantive GATED-skip reasoning
   re-verifying live state before declining premature dispatch — genuinely good engineering work, not stuck).
3. It runs out of dispatchable work for its role/constraints and correctly reports `idle_blocker_inferred`
   (`"idle: N task(s) blocked on task X (n), ..."` — the summary
   `server/worker_liveness/_git_alerts.py::_maybe_explain_idle_slot` produces). This is the documented
   `agents/worker.md` contract: report a final idle heartbeat, then wait quietly.
4. ~5 minutes later: `slot_idle_stale` + `worker_polling_dead` fire (silence ≥ `IDLE_STALE_THRESHOLD`, 5 min) — the
   health monitor's idle-silence pass flips `SlotRow.status` from `idle` to `stale`.
5. `WorkerLivenessKicker` sees `status != idle`, so its
   `if slot.status == "idle" and slot.current_task is None: continue` exemption (which exists SPECIFICALLY for this
   "task-less slot at the prompt is the contract, not a wedge" case) does not apply — it kicks the slot with a generic
   nudge (`"proceed now"`, `"check on it"`, `"check the dashboard for a new escalation"`). The kick
   `submit_verified: True`s but `ping_advanced: False` — it never produces a real heartbeat, because there is genuinely
   nothing new for the worker to act on.
6. The slot gets torn down and respawned. Go to step 1 — the backlog state has not changed, so the fresh worker runs out
   of work again within minutes and the whole cycle repeats.

Confirmed live on slot 10: boots at 09:44:42, 09:50:59, 09:57:35, 10:15:43 UTC — **4 full boot-work-idle-kick-respawn
cycles in ~30 minutes**, each ending in a kick with `ping_advanced: False`. Zero net dispatch progress from the churn
itself (the real backlog work each cycle DID complete was genuine, but the subsequent kick-respawn added no value — it
was already correctly idle).

**Root cause** (`server/health.py::HealthMonitor.check_once`, the idle-silence pass): the 2026-06-12 fix
(`orchestrator_spawn_reliability_db_lock_2026_06_10` Phase 2, `_git_alerts.py` "idle-available vs loop-dead" reasoning)
already distinguishes a **cleanly `/done`-exited** worker (idle + frozen ping + **no tmux session**) from a genuinely
dead loop — but only for that one case. It never considered the DIFFERENT, equally-legitimate case of a worker whose
session is **still alive**, correctly idle, and has **already explained** (via `last_msg`) that it has no dispatchable
work. Both a genuinely-dead loop and a correctly-idle-and-waiting worker present identically to the 5-minute silence
check (`status=idle`, live session, no heartbeat) — the check could not tell them apart, so it always assumed the worse
case.

### Finding 2 (unrelated, surfaced during the same investigation): hook crash on every uncompacted-session prompt

While reading slot 10's live tmux pane for corroborating evidence, I saw repeated `UserPromptSubmit hook error` /
`Failed with non-blocking status code` lines. Traced to `cursor-configs/hooks/context-threshold-nudge.sh` (the
`/pre-compact` context-budget nudge, registered as a `UserPromptSubmit` hook in `cursor-configs/settings.json`). Its
2026-07-25 SINCE-LAST-COMPACT windowing addition:

```bash
LAST_BOUNDARY_OFFSET=$(grep -abo '"subtype":"compact_boundary"' "$TRANSCRIPT_PATH" 2>/dev/null | tail -1 | cut -d: -f1)
```

runs under `set -euo pipefail`. `grep` exits 1 (not an error — "no match found") for any session that has not yet hit a
compaction boundary, which is the **common case** — under `pipefail` that propagates as the pipeline's exit status, and
`set -e` aborts the **entire hook** right there. Reproduced standalone (both isolated and via the real script end-to-end
against a realistic 50k-line, no-boundary transcript): exit code 1, confirmed. This means the hook silently crashed on
nearly every prompt submission for any session with zero prior compactions — noisy, and a real defect, though
non-blocking (Claude Code logs the hook failure and continues normally; it is not what caused Finding 1's dispatch
behavior — traced separately and independently via the activity log).

## Fix

### Finding 1: `server/health.py`

In the idle-silence pass, right after the existing "no session = idle-available, skip" branch, added a second exemption:
a task-less slot (`current_task is None`) whose `last_msg` is the idle-blocker-inference summary (starts with `"idle:"`)
has already determined there is no dispatchable work and is correctly following the wait-quietly contract — skip the
stale flip and alert entirely (mirrors the existing branch's exact reasoning, just for a still-live session).
Discriminator is precise: a slot that still has a `current_task` (stopped mid-task) is unaffected and still gets
flagged, even if a stale `last_msg` happens to start with `"idle:"` — regression test
`test_idle_slot_with_a_real_task_still_flags_even_with_idle_prefixed_msg` pins this.

- [x] ✅ [BACKEND] P1. Extend `HealthMonitor.check_once`'s idle-silence pass to skip the stale-flip/alert for a
      task-less slot with an explained idle-blocker `last_msg`. Regression tests
      `test_idle_task_less_slot_with_explained_blocker_never_flips_stale` +
      `test_idle_slot_with_a_real_task_still_flags_even_with_idle_prefixed_msg` added to
      `tests/test_health_alert_dedup.py`; bug-injected (reverted the fix, kept the tests) — confirmed the primary test
      fails at the exact intended assertion, the discriminator test still passes (proving it isn't a trivial
      always-pass); restored, both green; full `bash scripts/quality-gates.sh` green. (repo: agent-orchestrator)

### Finding 2: `cursor-configs/hooks/context-threshold-nudge.sh`

Added `|| true` after the `grep | tail | cut` pipeline so "no compaction boundary found yet" is treated as the expected,
non-fatal outcome it actually is, instead of aborting the whole hook.

- [x] ✅ [SCRIPT] P2. Fix the `grep`-under-`pipefail` exit-code bug in the SINCE-LAST-COMPACT windowing offset
      calculation. New `tests/test_context_threshold_nudge.bats` (5 tests: exits 0 + fires correctly with no boundary
      marker present on both a large and a small transcript, exits 0 with no output below threshold, exits 0 and fires
      correctly WITH a boundary marker present, exits 0 on missing `session_id`); bug-injected (reverted the fix) —
      confirmed 3 of 5 tests correctly fail (the no-boundary-marker cases, regardless of transcript size — the bug fires
      unconditionally, not just on large transcripts), restored, all 5 green. (repo: unified-trading-pm)

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — worker/health/kicker lifecycle model both
  findings live in.
