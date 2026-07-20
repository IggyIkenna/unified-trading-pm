---
doc_type: plan
title: AO dispatch liveness P0 — stop the prereq reaper killing freshly-spawned agents
summary:
  The prereq-blocked reaper keys its timer by slot id and never invalidates it when a new agent spawns into that slot,
  so any dispatch landing on a matured-timer slot is killed within one watchdog tick — measured killing the 2026-07-20
  plan_reconciler 19s after boot. Fix the timer invalidation, exclude non-backlog typed agents from the reaper, and make
  the escalation/plan_health slot race retry instead of silently failing.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dispatch, liveness, watchdog, regression]
related: [ao_open_issues_consolidated_close_out_2026_07_17.md, ao_scheduled_agent_hygiene_2026_07_20.md]
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

- [ ] [BACKEND] P0. **Invalidate the prereq timer when a new agent occupies the slot.** In
      `server/worker_liveness_watchdog.py`, pop `self._prereq_blocked_since[sid]` on every spawn into that slot — or,
      preferably, key the timer by slot + session/agent identity so a new occupant re-arms from zero rather than
      inheriting its predecessor's clock. Prefer whichever shape makes the invalidation impossible to forget at a future
      call site. **Gate**: a regression test that arms `_prereq_blocked_since` past `prereq_block_release_seconds`,
      spawns a NEW session into that slot, ticks the watchdog, and asserts the session SURVIVES + no
      `slot_released_prereq_blocked` is logged.
- [ ] [BACKEND] P0. **Exclude non-backlog typed agents from the reaper entirely.** A slot hosting a `plan_health` /
      `plan_reconciler` / escalation agent must never be selected by queue-prereq release logic, independent of todo 1.
      Identify the occupant by agent kind (`agents.agent_kind` / the slot's live agent), not by guessing from slot
      state. **Gate**: a test asserting a `plan_reconciler`-kind occupant is never selected, even with a fully matured
      timer AND a fully prereq-blocked queue.
- [ ] [BACKEND] P1. **Make the plan_health/escalation slot race retry instead of failing the dispatch.** On 2026-07-19
      the daily reconcile never spawned: `plan_health_dispatch_failed` —
      `"benign: session already exists (raced by another spawn path)"` — after the escalation dispatcher claimed the
      same slot 2 eight seconds earlier (`escalation_dispatch_initiated` 01:03:06 → reconcile initiated 01:03:14). Make
      `_pick_free_slot` + spawn atomic, or retry on the race with a different slot. **Also drop the `"benign:"` label**
      — a silently-skipped daily reconcile is not benign, and that wording is why this went unnoticed for a day.
      **Gate**: a test simulating a concurrent claim of the chosen slot asserts the dispatch lands on ANOTHER slot
      rather than failing; the failure path (genuinely no free slot) still returns 503.
- [ ] [BACKEND] P2. **Audit for other slot-keyed timers with the same inherit-the-predecessor's-clock defect.** The
      reaper bug's shape — per-slot mutable state that outlives the occupant — is a class, not an instance. Grep the
      watchdog/pruner/autospawn loops for dicts keyed by `slot_id` holding timestamps or counters, and for each one
      state whether a new occupant resets it. **Gate**: a written list of every such structure with a
      resets-on-new-occupant verdict; any that does NOT reset is either fixed or filed as its own todo with evidence.
- [ ] [BACKEND] P1. **Ship it and prove it landed on the live VM.** Commit via
      `bash scripts/quickmerge.sh "<msg>" --agent --files '<paths>'` from a `quality-gates.sh`-green tree. Then confirm
      the running orchestrator actually picked the change up — `ao-self-pull.sh` FF-pulls the AO checkout and restarts
      on change every ~15 min, so the fix is NOT live at merge time. **Gate**: the deployed commit sha is confirmed
      present in the orchestrator's own checkout AND the service restarted after that sha landed — cite both. "It
      merged" is not evidence.
- [ ] [BACKEND] P2. **Re-measure the `tmux_session_lost` rate AFTER the fix is live, and record the delta.** Baseline:
      **192 events since 2026-07-18** (measured 2026-07-20). Re-measure over a comparable window once the deploy is
      confirmed. Report the honest number either way — if the rate does NOT drop, say so plainly and record that the
      reaper was NOT the driver, so the churn investigation resumes with one hypothesis eliminated rather than being
      quietly assumed closed. **Gate**: before/after counts over comparable windows, with the verdict stated explicitly.

## Safeguards

- Never `git reset --hard` / `git clean -fd` / `git checkout` a dirty tree — other agents share this repo. Revert only
  your own files.
- Commit only from a `quality-gates.sh`-green tree; run `bash scripts/quality-gates.sh` in `agent-orchestrator`.
- **You may be killed by the very bug you are fixing.** If your session vanishes mid-task, that is the reproduction, not
  a failure — commit early, keep the Progress Log current, and on respawn record what you observed. Do not treat a lost
  session as lost work.

## Codex SSOTs

- `codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` — dispatch/spawn/slot model.
- `codex/04-architecture/autonomous-recovery-matrix.md` — what may self-recover vs what needs a human.
- `codex/12-agent-workflow/async-wait-and-poll-discipline.md` — measured-verdict discipline for the deploy + re-measure
  gates above.

## Progress Log

- **2026-07-20 — plan created** from the B4 audit. Root causes verified in code before filing (not inferred from the
  symptom): the timer-keying defect at `worker_liveness_watchdog.py` and the race at the plan_health dispatch path.
