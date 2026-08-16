---
doc_type: issue
title: AO fleet regression triad — scheduled-reserve slot drift, agents dying mid-task, human-fleet multi-tab misrepresentation
summary:
  Three distinct findings from an operator live-dashboard review 2026-08-16 evening. (1) Scheduled-task "reserved"
  slots are computed dynamically per-tick from the current slot roster, not pinned — the gate's reserve-set and the
  scheduled dispatcher's own target-pick can diverge whenever the roster shifts between the two computations. (2)
  Agents have been dying mid-task for the last ~4h after ~2 days of clean operation — a real regression, root cause
  not yet found; fleet paused down to 4 backlog + escalation workers for controlled diagnosis. (3) The dashboard's
  Agent Types panel shows a single "ikenna" row (human-fleet slot 9001) as STALE, misrepresenting the operator's
  actual activity across multiple concurrent interactive tab/worktree sessions that aren't part of the human-fleet
  registration model at all.
status: open
nature: record
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [ao, agent-orchestrator, dispatch, scheduled-jobs, worker-liveness, human-fleet, dashboard, regression, incident]
related:
  [
    /plans/active/ao_open_work_consolidated_tracker_2026_08_14.md,
    /plans/active/issues/ao_human_claim_reserved_slot_bypass_2026_08_16.md,
    /plans/active/ao_human_fleet_integration_2026_08_15.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
effort: high
drift_direction: advance-code
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator live-dashboard review, 2026-08-16 evening (screenshots of Agents/Slots view + "Multiple issues — eyes on
  this" panel). Operator directive: pause the fleet down to escalation workers + 4 backlog workers for controlled
  diagnosis of finding 2 while root-causing; restore once fixed. This doc is the pre-compact checkpoint — the next
  session picks up from here.
context_scope:
  [
    agent-orchestrator/server/dispatch.py,
    agent-orchestrator/server/config.py,
    agent-orchestrator/server/plan_health.py,
    agent-orchestrator/server/orphan_reap.py,
    /plans/active/issues/ao_human_claim_reserved_slot_bypass_2026_08_16.md,
  ]
---

# AO fleet regression triad — 2026-08-16

## Finding 1 — scheduled-reserve slot set is NOT pinned, drifts from what actually runs scheduled jobs

**Operator observation** (dashboard Slots view): the slots showing the `sched reserve` badge don't consistently match
which slots are actually running scheduled jobs (`plan_reconciler`, `cefi_reconciliation_auditor`, etc.) — "doesn't
seem like we are reserving fixed slots as we should be."

**Root cause, confirmed by code read** (`server/config.py::scheduled_task_reserved_slot_ids`,
`ci_escalation_reserved_slot_ids`): both reserve sets are computed as **"the top-N non-review slot ids from the
CURRENT live roster"** (`sorted(non_review_slot_ids)[-n:]`) — never a pinned, persisted set of specific slot numbers.
The function's own docstring admits the roster is emergent ("has been observed at 15/16/17 across different fleet
sizes"). This computation runs independently at (a) `dispatch.py`'s eligibility-gate build time (blocks Class-A
backlog spawn onto reserved slots) and (b) `plan_health.py`'s own `_pick_free_slot` search for where to actually
launch a scheduled job. If the live slot count differs even slightly between these two independent computations
(a slot dies/respawns, fleet cap changes, etc.), the two derived sets disagree — a slot the GATE currently protects
may not be the same slot the SCHEDULER currently targets, and vice versa. Live evidence 2026-08-16: dashboard showed
slots #28-30 tagged `sched reserve` and actively running scheduled jobs (consistent at that instant), but the operator's
broader observation across time is that this drifts.

- [ ] [BACKEND] P1. Confirm the drift hypothesis with live evidence: sample `sorted(non_review_slot_ids)[-n:]` at two
      different points in time (e.g. compare a `dispatch.py` gate-build log/snapshot against a `plan_health.py`
      scheduler-pick log/snapshot from the same tick window) and show the two sets actually diverging, not just
      theoretically capable of it. Done-when: either live divergence is caught and logged with both sets' membership,
      or the hypothesis is refuted with evidence (state which).
- [ ] [BACKEND] P1. If confirmed: pin the reserve sets. Either (a) compute them ONCE per `PlanRegenLoop`/dispatch
      cycle and pass the SAME frozen set to both the gate and the scheduler for that cycle (single source of truth
      per tick), or (b) make the reserve genuinely static — an explicit `ORCHESTRATOR_SCHEDULED_RESERVE_SLOT_IDS`
      allowlist instead of a derived top-N — whichever better matches the "reserving fixed slots" behavior the
      operator expects. State the tradeoff (dynamic top-N adapts to fleet-size changes automatically; a pinned list
      needs manual updates when fleet size changes) before picking.
- [ ] [REVIEW] P2. Add a regression test proving the gate's reserve set and the scheduler's target set are
      byte-identical for the same roster snapshot (this is the actual invariant that was silently missing —
      `test_dispatch_scheduled_reserve_gate.py` tests the GATE alone, not gate-vs-scheduler agreement).

## Finding 2 — agents dying mid-task, last ~4h, after ~2 days of clean operation (P0, ACTIVE INCIDENT)

**Operator observation**: fleet had been running increasingly well for almost 2 days; in the last 4 hours, agents
started dying mid-task. Operator's own lead: several scheduled-task-related and other changes landed recently (see
commit list below) — check what regressed.

**Fleet paused for controlled diagnosis, 2026-08-16 ~18:4X UTC** (operator directive): all worker slots paused except
4 backlog diagnostic slots (**20, 21, 22, 24**) and the 2 `ci_escalation` reserve slots (**32, 33**). Slot 0 (main),
slot 2 (review — separately tracked, `ao_human_claim_reserved_slot_bypass_2026_08_16.md`), and slot 9001
(human/ikenna) left untouched. Verified live via `GET /api/state` post-pause — 25 slots confirmed `status: paused`.
**RESTORE THIS once root-caused and fixed** — do not leave the fleet at reduced capacity indefinitely; this is a
diagnostic-window state, not a new steady state. Restore command: `POST /api/slots/{id}/resume` for each of
`3 4 5 6 7 8 9 10 11 12 13 14 15 16 17 18 19 23 25 26 27 28 29 30 31` (mirror of the pause list above), or a fleet-wide
resume if one exists — check `server/routes/slots_ops.py` for a bulk endpoint before looping 25 individual calls.

**Live evidence gathered this session, not yet fully diagnosed**:
- `journalctl -u orchestrator.service --since "5 hours ago"` shows repeated `orphan_reap sweep: slot <N> pid <P>
  age=<S>s KILLED` entries (e.g. `slot 23 pid 2227102 age=306s KILLED`, `slot 23 pid 2227105 age=308s KILLED` at
  17:34:59) — `orphan_reap.py`'s sweep is actively killing processes it judges orphaned. Whether these are GENUINE
  orphans (correct kills) or live, legitimately-working agent processes being wrongly reaped (the actual regression)
  is **not yet determined** — this is the most concrete lead found so far and should be the first thing the next
  session traces.
- Heavy `release_task_to_queue: refused task_id=... — status='done'/'cancelled' is terminal (stale
  current_task/dispatched_to reference?)` warning volume in the same window — many refused release attempts against
  already-terminal tasks. Possibly a symptom of the same underlying issue (a slot's `current_task` pointer going
  stale/mismatched after a kill) rather than a separate bug — check whether these warnings cluster around the same
  timestamps as the `orphan_reap ... KILLED` events.
- Recent commit history in the suspect window (today, times UTC) — the operator's own lead ("we did re-enable some
  scheduled tasks recently and a bunch of other stuff") — candidates most likely to have touched the orphan-reap /
  slot-lifecycle path or scheduled-job cadence:
  - `98825ba` 15:46 `fix(scheduled-jobs): allowlist operator-paused mode as benign 503, not a paging error`
  - `efe2cb7` 17:40 `fix: exclude scheduled-task-reserved slots from Class-A backlog dispatch` (this session's own
    finding 1 area — touches `dispatch.py`)
  - `d13788e` 18:17 `fix(dispatch): guard human-claim endpoints...` (this session's own fix — touches
    `slots_worker.py`, unlikely culprit but in scope, ship time correlates with tail of the 4h window)
  - Also worth checking anything from `1af5005` 13:49 onward for interaction with `orphan_reap.py`'s liveness
    detection (the "confirm-first PostToolUse nudge" feature touches worker/task-completion signaling).
  - **Not yet checked**: whether any of today's commits touched `orphan_reap.py`, `worker_liveness_watchdog.py`, or
    the process-age/`age=Ns` threshold logic directly — `git log --since="6 hours ago" -- server/orphan_reap.py
    server/worker_liveness_watchdog.py` is the first command the next session should run.

- [ ] [DIAG] P0. Run `git log --since="8 hours ago" -p -- server/orphan_reap.py server/worker_liveness_watchdog.py
      server/tmux_spawn.py` — find any change to the reap/liveness/age-threshold logic in the suspect window. If
      found, that's the prime suspect; read the diff for a sign/off-by-one/threshold regression before assuming
      correctness.
- [ ] [DIAG] P0. For 3-5 of the `orphan_reap sweep: ... KILLED` events from the last 4h
      (`journalctl -u orchestrator.service --since "4 hours ago" | grep "orphan_reap sweep.*KILLED"`), trace the
      killed PID's slot backward: was that slot genuinely mid-task (check `current_task`/`plan_ref` at kill time via
      the activity log) or genuinely idle/orphaned? If genuinely mid-task, this confirms the regression and pinpoints
      the reap logic as the culprit.
- [ ] [BACKEND] P0. Once root-caused: fix it, add a regression test proving a legitimately-working process (recent
      heartbeat, real tmux activity) is never reaped, and re-verify against live logs post-fix (same
      `orphan_reap...KILLED` grep, expect the false-positive class to stop).
- [ ] [OPERATOR] P1. **Once fixed and verified**: resume the 25 paused slots (see restore command above) and confirm
      the fleet returns to full capacity — this is a live write action, do after the fix is confirmed, not before.
- [ ] [UI] P1. Surface "agents dying mid-task" as its own line in the dashboard's "Multiple issues — eyes on this"
      banner (top-of-page summary panel) — it currently has no dedicated visibility there despite being the most
      severe of the current issues; the operator had to notice it manually via the Agent Types table. Wire it off
      whatever signal Finding 2's fix ends up using to detect the false-reap class (e.g. a counter/rate of
      reaped-while-mid-task events), not just "Review agents down" (a different, already-covered line).

## Finding 3 — human-fleet dashboard collapses multiple real operator sessions into one misleading "STALE" row

**Operator observation**: the dashboard's Agent Types panel shows a single `ikenna` row (source: human-fleet, status:
STALE, last seen ~5h ago) as if that's the operator's only presence — but the operator runs several concurrent
interactive tab/worktree sessions (this very session is one), which the human-fleet registration model has no
awareness of at all.

**Root cause, structural**: `ao_human_fleet_integration_2026_08_15` built a SEPARATE, opt-in self-registration
mechanism (`human_heartbeat`/`human-claim`, slot 9001/9002) for an operator who wants a tracked presence in the AO
dashboard the same way a worker agent has one. It was never designed to represent — and structurally cannot represent
— the operator's ordinary interactive Claude Code sessions running in per-tab worktrees (`.tabs/<N>/`), which are a
completely different, older mechanism (`per-tab-worktrees.md`) with no AO dashboard presence at all. The STALE badge
is accurate for what it measures (slot 9001's own heartbeat hasn't fired in ~5h) — the misrepresentation is that a
casual dashboard reader has no way to tell "this is one specific opt-in registration, not the operator's overall
activity" without already knowing the two systems are unrelated.

- [ ] [UI] P2. Either (a) relabel the human-fleet row/badge to make the scope explicit (e.g. "ikenna (human-fleet
      slot 9001)" instead of bare "ikenna", and change STALE's tooltip/copy to something like "this specific
      registered session hasn't heartbeat — does not reflect other active work"), or (b) if there's appetite to
      actually unify the two presence signals, investigate whether per-tab worktree sessions could ALSO self-report
      a lightweight heartbeat so the dashboard shows genuine aggregate operator activity — scope that as a separate,
      larger follow-up if pursued, don't fold it into this todo.
- [ ] [DIAG] P3. Low-priority: confirm whether slot 9001's heartbeat is genuinely dead (worth a manual
      `python3 -c "..."`/curl heartbeat call to test it still works) or whether something silently broke the
      heartbeat POST path itself — distinguish "operator hasn't run it in 5h" from "it's broken."

## Progress Log

- **2026-08-16 (interactive session, pre-compact checkpoint)**: All three findings characterized to the depth
  possible before compacting, per operator direction ("take stock, run /pre-compact, we'll fix in a new session").
  Finding 2's fleet-pause action taken live (operator directive) and verified. No code fixes attempted in this
  session for any of the three findings — this doc + the tracker todo are the full handoff. Next session: start with
  Finding 2 (P0, active incident, fleet running at reduced capacity) via the two `[DIAG] P0` todos above.
</content>
