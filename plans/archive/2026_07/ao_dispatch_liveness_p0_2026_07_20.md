---
doc_type: plan
title: AO dispatch liveness P0 — stop the prereq reaper killing freshly-spawned agents
summary:
  The prereq-blocked reaper keys its timer by slot id and never invalidates it when a new agent spawns into that slot,
  so any dispatch landing on a matured-timer slot is killed within one watchdog tick — measured killing the 2026-07-20
  plan_reconciler 19s after boot. Fix the timer invalidation, exclude non-backlog typed agents from the reaper, and make
  the escalation/plan_health slot race retry instead of silently failing.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dispatch, liveness, watchdog, regression]
related:
  [
    /plans/archive/2026_08/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_07/ao_scheduled_agent_hygiene_2026_07_20.md,
  ]
created: 2026-07-20
last_updated: 2026-07-20
parent_epic: orchestrator_master
assigned_vm: NA # LOCAL execution — operator-assigned agents on this host, NOT AO-dispatched (2026-07-20)
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
model_tier: sonnet-doable # single-repo, root cause already diagnosed in the plan body; no 1M context needed
thinking_tier: high # concurrency/lifetime reasoning + tests that must actually bite — worth the effort bump, still Sonnet
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
---

# AO dispatch liveness P0 — the prereq reaper kills freshly-spawned agents

> **🟢 COMPLETE 2026-07-20 — ARCHIVED.** All 7 code todos landed and were independently re-verified 2026-07-20: every
> cited sha (`1e7fec0`, `390cdde`, `d84109a`, `f641968`) exists, is an ancestor of `origin/live-defi-rollout`, and its
> diff does what the todo claims; every cited regression test exists by name. **Deploy confirmed by SSM** (2026-07-20
> 14:19 UTC): all four shas are ancestors of the VM's deployed HEAD and the service restarted 14:15:21 UTC. The one
> remaining item — re-measuring the `tmux_session_lost` rate against the 192-event baseline — is gated on calendar time,
> not code, and is now owned by `ao_open_issues_consolidated_close_out_2026_07_17.md` § Phase 8. Do not reopen this plan
> for it.

> **Provenance**: the B4 audit (2026-07-20) of `ao_open_issues_consolidated_close_out_2026_07_17.md`. That plan holds
> the full audit record; this plan holds the WORK. Do not action the moved entries there.

## The bug, in one paragraph

`server/worker_liveness_watchdog.py` (the prereq-block release loop, ~L1180-1265) keeps
`self._prereq_blocked_since[sid]` keyed by **slot id only**, and never invalidates it when a NEW agent spawns into that
slot. Its early-out `if held_task is None and not had_session: continue` only skips slots with **no** session — so once
a fresh session appears on a slot whose timer already matured, the reaper kills it and logs the tell-tale
`released_task: null, killed_session: true`.

**Measured 2026-07-20**: `agt-99684d` (the daily `plan_reconciler`) booted on slot 3 at `01:03:41` and was killed at
`01:04:00` with `blocked_seconds: 3604` — an hour-old timer belonging to the slot's PREVIOUS occupant. This is **not**
reconciler-specific: any dispatch (backlog worker, escalation, plan_health) landing on such a slot is killed within one
watchdog tick.

## Why this matters more than it looks

The reaper's premise is "the BACKLOG queue is fully prerequisite-blocked, so idle BACKLOG workers should be released."
That says nothing about a **scheduled** agent (plan_health / plan_reconciler / escalation), which is not a backlog
worker at all and must never be selected by queue-prereq logic. The bug therefore has two independent fixes, and both
are wanted — the timer invalidation is the correctness fix, the typed-agent exclusion is the design fix.

It is also a live candidate for a chunk of the fleet's unexplained churn: 192 `tmux_session_lost` events since 07-18. Do
not treat that as proven — it is measured AFTER this lands (see the last todo).

## Execution environment — LOCAL (read this first)

This plan is executed by **operator-assigned agents on this host**, not by AO dispatch (`assigned_vm: NA`,
`execution_scope: local-only` — regen never ingests it). Tick the checkboxes here by hand as you land each item.

**Todos 1-4 are pure local work** — code + tests in the `agent-orchestrator` checkout, `bash scripts/quality-gates.sh`
to verify. No VM access needed.

**Todos 5-6 REQUIRE the live central VM** (`i-0c9b283b31d6b5ca7`, ap-northeast-1) and cannot be closed from a local
checkout. Access is read-only via AWS SSM — the working pattern is in
`agent-orchestrator/scripts/orchestrator/check-ao-backlog-status.sh` (document `AWS-RunShellScript`,
`--parameters "commands=[\"…\"]"` as a JSON list, base64-encode any non-trivial remote script). For DB probes use
`sudo python3` with `sqlite3.connect("file:/var/lib/orchestrator/state.db?mode=ro", uri=True)` — **`sqlite3` CLI is not
installed on the VM**, and a probe run as `ubuntu` does NOT inherit the systemd unit's `Environment=`, so pass the DB
path explicitly or you will silently read the wrong database. **Never write to the live DB or restart the service.** If
you lack SSM credentials, do the code work, leave 5-6 open, and say so — do not tick them on inference.

## Ordering note

Todos 1 and 2 are the same function and should land together (one commit is fine). Todo 3 is an independent file. Todo 6
is a MEASUREMENT that is only meaningful after 1-2 are deployed and `ao-self-pull` has restarted the service — it is
last for that reason, not for convenience.

## Todos

- [x] [BACKEND] P0. **Invalidate the prereq timer when a new agent occupies the slot.** In
      `server/worker_liveness_watchdog.py`, pop `self._prereq_blocked_since[sid]` on every spawn into that slot — or,
      preferably, key the timer by slot + session/agent identity so a new occupant re-arms from zero rather than
      inheriting its predecessor's clock. Prefer whichever shape makes the invalidation impossible to forget at a future
      call site. **Gate**: a regression test that arms `_prereq_blocked_since` past `prereq_block_release_seconds`,
      spawns a NEW session into that slot, ticks the watchdog, and asserts the session SURVIVES + no
      `slot_released_prereq_blocked` is logged. — `agent-orchestrator@1e7fec089`. Keyed the dict by
      `(slot_id, SlotRow.assigned_at)` instead of `slot_id` alone — `assigned_at` is already stamped fresh on every
      re-occupation path (`assign_task_to_slot`, `claim_slot_for_typed_agent`), so a new occupant's key naturally misses
      the dict and re-arms from zero with no future call site needing to remember an explicit pop. Gate test
      `test_new_occupant_survives_matured_predecessor_timer` in `tests/test_prereq_blocked_release.py` — verified it
      fails against pre-fix code (reproduces the exact `released after Ns ... killed_session=True` log line) and passes
      against the fix.
- [x] [BACKEND] P0. **Exclude non-backlog typed agents from the reaper entirely.** A slot hosting a `plan_health` /
      `plan_reconciler` / escalation agent must never be selected by queue-prereq release logic, independent of todo 1.
      Identify the occupant by agent kind (`agents.agent_kind` / the slot's live agent), not by guessing from slot
      state. **Gate**: a test asserting a `plan_reconciler`-kind occupant is never selected, even with a fully matured
      timer AND a fully prereq-blocked queue. — `agent-orchestrator@1e7fec089`. Backlog workers never get an `AgentRow`
      (only main/review/custom-chat + typed/scheduled agents do — confirmed via `register_agent` call sites), so "a live
      (non-archived) `AgentRow` exists for this slot's tmux session" is a hardcode-free discriminator — no kind-list to
      maintain as new typed-agent kinds are added. Gate test `test_typed_agent_occupant_never_selected` derives the
      timer dict's real key shape from the code (not a hardcoded literal) so it can't pass vacuously; verified it fails
      against pre-fix code and passes against the fix.
- [x] [BACKEND] P1. **Make the plan_health/escalation slot race retry instead of failing the dispatch.** On 2026-07-19
      the daily reconcile never spawned: `plan_health_dispatch_failed` —
      `"benign: session already exists (raced by another spawn path)"` — after the escalation dispatcher claimed the
      same slot 2 eight seconds earlier (`escalation_dispatch_initiated` 01:03:06 → reconcile initiated 01:03:14). Make
      `_pick_free_slot` + spawn atomic, or retry on the race with a different slot. **Also drop the `"benign:"` label**
      — a silently-skipped daily reconcile is not benign, and that wording is why this went unnoticed for a day.
      **Gate**: a test simulating a concurrent claim of the chosen slot asserts the dispatch lands on ANOTHER slot
      rather than failing; the failure path (genuinely no free slot) still returns 503. —
      `agent-orchestrator@390cdde24`. Retry (not lock/atomic) per the gate's own "lands on ANOTHER slot" framing;
      bounded at `_MAX_SLOT_PICK_ATTEMPTS=5` in both `plan_health.py` and `escalation.py` (duplicated, matching the
      pre-existing `_pick_free_slot` duplication convention between the two files). The `"benign:"` prefix is stripped
      from the reported error/alert/raised-exception text only once every retry is exhausted (still benign mid-retry —
      the AutoSpawnLoop's OWN batch-tick semantics, where `_do_spawn`'s pre-check TOCTOU message originates, are
      untouched). For escalation.py specifically: a residual benign collision after all retries still pages (real
      capacity signal for a dispatcher with no next tick) but does NOT quarantine the slot (it isn't a slot defect, just
      occupied). Gate tests `test_dispatch_retries_on_a_different_slot_after_benign_collision` +
      `test_dispatch_exhausted_retries_drops_benign_label` (plan_health) and
      `test_escalate_retries_on_a_different_slot_after_benign_collision` +
      `test_escalate_exhausted_retries_drops_benign_label_and_does_not_quarantine` (escalation) — all 4 verified to fail
      against pre-fix code and pass against the fix; `_pick_free_slot() is None` (genuinely no free slot) still raises
      immediately, untouched by the retry loop.
- [x] [BACKEND] P2. **Audit for other slot-keyed timers with the same inherit-the-predecessor's-clock defect.** The
      reaper bug's shape — per-slot mutable state that outlives the occupant — is a class, not an instance. Grep the
      watchdog/pruner/autospawn loops for dicts keyed by `slot_id` holding timestamps or counters, and for each one
      state whether a new occupant resets it. **Gate**: a written list of every such structure with a
      resets-on-new-occupant verdict; any that does NOT reset is either fixed or filed as its own todo with evidence. —
      Full written list + verdicts in the Progress Log below. One real gap found + fixed (`_heartbeat_resume_count`,
      `agent-orchestrator@1e7fec089`, regression test `test_kill_slot_clears_heartbeat_resume_count` in
      `tests/test_self_healing_hardening.py`, verified fails pre-fix/passes post-fix). One partially-mitigated residual
      risk filed as its own todo below (`_idle_session_ticks`) rather than fixed in this sitting, per the gate's "fixed
      or filed" latitude. Everything else verified self-healing (content/task/signature-diff gated) or intentionally
      slot-scoped action rate-limiting — not occupant state, correctly persists across occupants.
- [x] [BACKEND] P2. **Fix `_idle_session_ticks` the same way as `_prereq_blocked_since` (todo-4 audit followup).** In
      `WorkerLivenessWatchdog._reclaim_idle_lingering_sessions` (`server/worker_liveness_watchdog.py`), the lingering-
      session counter is keyed by `slot_id` alone. It already has a partial mitigation the prereq timer lacked — a
      fresh-spawn boot-grace check (`spawned_at` within `_BOOT_GRACE_SECONDS` → pop + skip) — which closes the exact
      race the P0 bug exploited (a just-spawned occupant caught mid-transaction while `status` still reads idle/stale).
      The residual gap: if a NEW occupant's status stays idle/stale for longer than the boot-grace window without
      `spawned_at`/`tmux_session` reflecting the true reoccupation (a narrower, more contrived scenario than the P0 bug
      — would itself indicate a separate stuck-transaction bug), it could inherit tick progress toward
      `_IDLE_SESSION_RECLAIM_TICKS` from an unrelated predecessor. Apply the same `(slot_id, assigned_at)` — or
      `(slot_id, tmux_session)` — keying used for `_prereq_blocked_since`, updating the pop/cleanup call sites
      (`_reclaim_idle_lingering_sessions` lines ~1101-1160) to match. **Gate**: a regression test mirroring
      `test_new_occupant_survives_matured_predecessor_timer` — arm the counter near `_IDLE_SESSION_RECLAIM_TICKS` under
      a stale key, land a new occupant (fresh `assigned_at`, live session, status still idle/stale past the boot-grace
      window), tick, and assert the session survives. — `agent-orchestrator@d84109a5`. Keyed by
      `(slot_id, last_spawned_at)` rather than `(slot_id, assigned_at)` — this specific function already reads
      `last_spawned_at` (as `spawned_at`) for the boot-grace check, and it's the more semantically correct field here:
      it changes exactly when a genuine new tmux session starts (including a typed agent's claim — both `plan_health.py`
      and `escalation.py` persist `last_spawned_at` at claim time), whereas `assigned_at` also changes on a plain task
      reassignment to an already-running worker — a case this `idle`/`stale`-scoped query never even sees (assigning a
      task flips status to `working` first). Gate test `test_new_occupant_survives_matured_predecessor_lingering_count`
      in `tests/test_self_healing_hardening.py` — first attempt asserted an internal dict-shape detail
      (`(6, None) in wd._idle_session_ticks`) that failed against pre-fix code for the wrong reason (an `int` vs `tuple`
      key mismatch, not the actual bug); rewritten to assert purely on the BEHAVIORAL outcome (`kill_session` call
      count), which is shape-agnostic — re-verified: against pre-fix code it fails with `kill_session` actually invoked
      (log line `"...ticks=2 -> freeing slot"`, i.e. the bug reproduced for real), and passes clean against the fix.
- [x] [BACKEND] P1. **Ship it and prove it landed on the live VM.** Commit via
      `bash scripts/quickmerge.sh "<msg>" --agent --files '<paths>'` from a `quality-gates.sh`-green tree. Then confirm
      the running orchestrator actually picked the change up — `ao-self-pull.sh` FF-pulls the AO checkout and restarts
      on change every ~15 min, so the fix is NOT live at merge time. **Gate**: the deployed commit sha is confirmed
      present in the orchestrator's own checkout AND the service restarted after that sha landed — cite both. "It
      merged" is not evidence. — Verified via read-only AWS SSM (`i-0c9b283b31d6b5ca7`, ap-northeast-1). First check
      (T+0) found the checkout already FF-pulled to `agent-orchestrator@390cdde24` but the running `orchestrator`
      systemd process still on its PRE-fix start time (`ExecMainStartTimestamp=2026-07-20 06:15:15 UTC`, before both
      commits landed at 06:26:40/06:28:12 UTC) — exactly the "checkout current, process stale" gap the gate exists to
      catch. Backgrounded a 60s-interval poller; the service cycled `deactivating→active` at 06:45:20 UTC (next
      `ao-self-pull` tick). Re-verified: `git merge-base --is-ancestor` confirms BOTH `agent-orchestrator@1e7fec089` and
      `agent-orchestrator@390cdde24` are ancestors of the current live HEAD (which has moved further via other agents'
      unrelated work in the interim — expected on a shared branch), and `ExecMainStartTimestamp=2026-07-20 06:45:20 UTC`
      (`ActiveState=active`) postdates both commits. Both halves of the gate hold.
- [x] ✅ [BACKEND] P0. **Stop `_reclaim_idle_lingering_sessions` reaping typed one-off agents mid-work (found 2026-07-20
      while verifying this plan).** The AgentRow guard added by todo 2 protects the PREREQ reaper only;
      `_reclaim_idle_lingering_sessions` is a different function in the same file that never learned it, and it was
      still killing the daily plan_reconciler. **Evidence it was mid-work, not crashing**: the agent's own JSONL
      transcript (`/home/ubuntu/.claude-configs/orch-slot-5/projects/…/b1a0f68f-….jsonl`, 83 entries, 436 KB) ends at
      07:32:29Z reading its plan-hygiene sweep output, ~60s before `tmux_session_lost` at 07:33:30Z. Arithmetic matches
      exactly: never calls `/boot` (a fleet-worker step) → SlotRow stays `idle` → `boot_grace_seconds` 300s + 2 ticks ×
      60s = **420s** vs measured **7m40s**. — `agent-orchestrator@f641968`, regression test
      `test_idle_reclaimer_never_reaps_a_typed_one_off_agent` in `tests/test_self_healing_hardening.py`, verified RED
      without the guard and GREEN with it; full `quality-gates.sh` green before ship. **This is the THIRD carve-out for
      the same fact** — which is why `ao_uniform_agent_liveness_contract_2026_07_20.md` now exists to replace all three
      with one contract; that plan's final todo deletes this guard.
- ➡️ **MIGRATED 2026-07-20 → `ao_open_issues_consolidated_close_out_2026_07_17.md` § Phase 8. NOT done; not owned
  here.** Original item, for the record: [BACKEND] P2. **Re-measure the `tmux_session_lost` rate AFTER the fix is live,
  and record the delta.** Baseline: **192 events since 2026-07-18** (measured 2026-07-20). Re-measure over a comparable
  window once the deploy is confirmed. Report the honest number either way — if the rate does NOT drop, say so plainly
  and record that the reaper was NOT the driver, so the churn investigation resumes with one hypothesis eliminated
  rather than being quietly assumed closed. **Gate**: before/after counts over comparable windows, with the verdict
  stated explicitly.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo. Revert only
  your own files.
- Commit only from a `quality-gates.sh`-green tree; run `bash scripts/quality-gates.sh` in `agent-orchestrator`.
- **You may be killed by the very bug you are fixing.** If your session vanishes mid-task, that is the reproduction, not
  a failure — commit early, keep the Progress Log current, and on respawn record what you observed. Do not treat a lost
  session as lost work.

## Codex SSOTs

- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch/spawn/slot model.
- `/codex/04-architecture/autonomous-recovery-matrix.md` — what may self-recover vs what needs a human.
- `/codex/12-agent-workflow/async-wait-and-poll-discipline.md` — measured-verdict discipline for the deploy + re-measure
  gates above.

## Progress Log

- **2026-07-20 — plan created** from the B4 audit. Root causes verified in code before filing (not inferred from the
  symptom): the timer-keying defect at `worker_liveness_watchdog.py` and the race at the plan_health dispatch path.
- **2026-07-20 — todos 1-4 shipped to LDR**: `agent-orchestrator@1e7fec089` (todos 1, 2, 4) +
  `agent-orchestrator@390cdde24` (todo 3), both `quality-gates.sh`-green before commit. Todo 5 (deploy verification on
  the live VM) still open below. Todo 4's audit — every `dict[int, ...]` in `worker_liveness_watchdog.py` /
  `autospawn.py` / `escalation.py` keyed by `slot_id`, with a resets-on-new-occupant verdict:

  | Structure                                                                                                            | File                           | Verdict                             | Why                                                                                                                                                                                                                                                                                                                                                                                                                                |
  | -------------------------------------------------------------------------------------------------------------------- | ------------------------------ | ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
  | `_prereq_blocked_since`                                                                                              | worker_liveness_watchdog.py    | **FIXED (todo 1)**                  | was slot_id-only; now `(slot_id, assigned_at)`                                                                                                                                                                                                                                                                                                                                                                                     |
  | `_heartbeat_resume_count`                                                                                            | worker_liveness_watchdog.py    | **FIXED (this todo)**               | `_kill_slot` (shared teardown for every kill trigger) never popped it — a resume-episode count from one trigger (e.g. heartbeat-silent) survived a LATER kill via a different trigger (stuck_at_prompt/context_full/usage_cap) and was inherited by the next occupant, degrading its resume budget. Fixed by popping inside `_kill_slot` itself, closing every caller at once.                                                     |
  | `_idle_session_ticks`                                                                                                | worker_liveness_watchdog.py    | **PARTIAL — filed as its own todo** | has a fresh-spawn boot-grace mitigation (`spawned_at` within `_BOOT_GRACE_SECONDS` → pop+skip) that closes the exact P0 race, but remains slot_id-keyed — a narrower residual risk remains if status stays idle/stale past the boot-grace window without a fresh `spawned_at`.                                                                                                                                                     |
  | `_stuck_ticks` / `_api_error_ticks`                                                                                  | worker_liveness_watchdog.py    | resets — self-healing               | both are gated on `pane == prev_pane` (unchanged content across ticks); a new occupant's pane content differs from its predecessor's frozen content by construction, so the "unchanged" condition can't hold across an occupant change — counter can't inherit a matured streak.                                                                                                                                                   |
  | `_prev_panes`                                                                                                        | worker_liveness_watchdog.py    | resets — always overwritten         | holds "last observed pane," rewritten every relevant tick; not a maturing timer.                                                                                                                                                                                                                                                                                                                                                   |
  | `_realign_last_task`                                                                                                 | worker_liveness_watchdog.py    | resets — correct either way         | tracks last-seen task_id to detect a task boundary; a new occupant's (different) task_id naturally reads as a boundary, and the rare same-task-id case (task requeued to the same slot) is correctly treated as mid-task too.                                                                                                                                                                                                      |
  | `_nudges_today` / `_last_nudge_at`                                                                                   | worker_liveness_watchdog.py    | intentionally persists              | per-SLOT daily nudge-rate budget (bounds nudges on a slot number regardless of occupant), not per-occupant session state — global daily reset already exists. `_last_nudge_at`'s stale-grace risk (shielding a new occupant from heartbeat-silent kill for a few extra seconds) is the OPPOSITE failure direction of the P0 bug (over-protective, not destructive) and self-corrects once the grace window elapses — not actioned. |
  | `_last_kill_at`                                                                                                      | worker_liveness_watchdog.py    | intentionally persists              | rate-limits the KILL ACTION on a slot (flap-window detection), not occupant state.                                                                                                                                                                                                                                                                                                                                                 |
  | `_BRANCH_QUARANTINE_ALERTED` / `_SPAWN_FAILED_ALERTED`                                                               | autospawn.py                   | resets — signature dedup            | keyed by slot_id → error signature; explicitly cleared on next successful spawn / naturally mismatches on a different failure. Not a maturing timer — worst case is a missed re-alert, never a wrongful kill.                                                                                                                                                                                                                      |
  | `_last_attempt_at` / `_recent_attempts` / `_flap_backoff_until` / `_last_failure_logged` / `_tier_upgrade_killed_at` | autospawn.py (`AutoSpawnLoop`) | intentionally persists              | all rate-limit the SPAWN/KILL ACTION on a slot (attempt cooldown, flap history, tier-upgrade cooldown) — correctly slot-scoped regardless of occupant, same class as `_last_kill_at`.                                                                                                                                                                                                                                              |
  | `_recently_quarantined`                                                                                              | escalation.py                  | intentionally persists              | tracks a WORKTREE/branch-state defect, which is a property of the slot's worktree, not the occupant — correctly persists across occupants until the TTL/operator fix clears it.                                                                                                                                                                                                                                                    |

  Verdict: 2 real findings, both closed this session (1 fixed directly, 1 fixed + 1 filed as a followup todo per the
  gate's "fixed or filed" latitude — `_idle_session_ticks`'s existing boot-grace mitigation made a same-sitting fix
  lower-priority than keeping this session's diff focused and reviewable). Everything else is either self-healing by
  construction or intentionally slot-scoped rate-limiting, not occupant state.

- **2026-07-20 — todo 5 closed**: deploy-live verified on the central orchestrator VM via read-only SSM (details in the
  todo-5 checkbox above). The T+0 check caught the exact "checkout current, process still on the pre-fix start time"
  window the gate is designed to catch — worth noting for future deploy-verification todos on this service: check the
  checkout FIRST, but never stop there; the running process is the thing that matters, and `ao-self-pull`'s ~15-min
  cadence means a same-tick check will very likely observe that gap, not close it. Todo 6 remains open — it needs a time
  window comparable to the 192-event/~2-day baseline (07-18→07-20) before a re-measurement means anything; closing it
  minutes after deploy would not be an honest number.
- **2026-07-20 — todo-4 followup closed**: `_idle_session_ticks` keyed by `(slot_id, last_spawned_at)`, mirroring
  `_prereq_blocked_since`'s fix — `agent-orchestrator@d84109a5`, `quality-gates.sh`-green (1415 tests). Worth recording
  the near-miss on the gate test: the first draft asserted an internal dict-shape detail that happened to fail against
  pre-fix code too, but for an unrelated reason (an `int`-vs-`tuple` key mismatch) rather than reproducing the actual
  bug. Caught by the same discipline used earlier in this plan — always read WHY a new regression test fails against
  pre-fix code, not just THAT it fails — and fixed by asserting purely on the behavioral outcome (`kill_session` call
  count) instead of internal representation. Re-verified against pre-fix code: `kill_session` fires for real
  (`"...ticks=2 -> freeing slot"` in the log), confirming the test now reproduces the bug rather than merely disagreeing
  with the old code's shape. Todo 6 (tmux_session_lost re-measure) remains the only open item.

## Flags for the plan writer

Two things found while executing that are worth your eyes, neither blocking, both left as-is (not silently edited):

1. **Todo-numbering prose is now stale.** "Execution environment" (§ above) says "Todos 1-4 are pure local work" /
   "Todos 5-6 REQUIRE the live central VM," and "Ordering note" says "Todo 6 is a MEASUREMENT that is only meaningful
   after 1-2 are deployed." Both were written against the original 6-item list. The todo-4 audit inserted a new followup
   todo (`_idle_session_ticks` fix) between the audit and "Ship it," so the list is now 7 items and the by-number
   references in those two prose sections point at the wrong items (the by-number description still describes the RIGHT
   things, just under the WRONG numbers now — e.g. "todo 6" in the Ordering note means the re-measure todo, which is
   actually the 7th item in the current list). Also worth noting: the new `_idle_session_ticks` followup is itself pure
   local work (code + tests, no VM) like todos 1-4, so if you renumber, it slots in with that group, not the
   VM-requiring one.
2. **Todo 3's gate text ("the failure path ... still returns 503") is only accurate for `plan_health.py` now, not
   `escalation.py`.** Confirmed: `PlanHealthError` → HTTP 503 at `routes/agents.py:359` (`/api/plan-health/dispatch`),
   so that half holds. But `/api/escalate` (`routes/agents.py:267`) stopped calling `escalation.escalate()`
   synchronously back on `f20195a` (2026-06-16, "enqueue + return fast — never spawn inline," Issue A) — it calls
   `escalation.enqueue()` instead, whose own docstring says "No 503 path — enqueue is a fast DB write that always
   succeeds." The ONLY two remaining live callers of `escalate()` (both inside `retry_queued_escalations`, a background
   async drain loop, not a request handler) pass `queue_on_no_capacity=False` explicitly — so `escalate()`'s DEFAULT
   `queue_on_no_capacity=True` and its "no free slot" → `EscalationError` → HTTP-503 path appear to be unreachable from
   any live production code path today, only exercised by direct/test callers. This doesn't affect what shipped here —
   the retry-on-collision + benign-label fix is exercised by both live call sites regardless of the
   `queue_on_no_capacity` value — but it's pre-existing plan text (not something I rewrote) describing an architecture
   that already drifted before this plan was even written, and it raises a real question for you: is
   `queue_on_no_capacity=True`/its default now dead code worth removing, or intentionally kept as a public API surface?
   Left for you to decide rather than assuming either answer.
