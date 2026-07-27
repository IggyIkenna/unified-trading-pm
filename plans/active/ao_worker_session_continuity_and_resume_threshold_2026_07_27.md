---
doc_type: plan
title: AO worker session reset policy — plan-continuity gate + resume-threshold tuning
summary: >-
  Closes the two remaining open threads from the 2026-07-25/27 Slack discussion (Ikenna/Harsh) on worker context
  carryover, distinct from the already-archived ao_worker_context_lifecycle_gap_2026_07_25.md (which gated dispatch on
  context_used_pct alone). Harsh's stated intent: a persistent plan-backlog worker should keep draining tasks in the
  SAME session only when the next task genuinely continues the SAME plan; a task from an unrelated/parallel plan should
  get a fresh session instead, relying on the plan's own Progress Log for continuity — matching the pre-existing
  operator ruling in agent-orchestrator-single-vm-architecture.md that conversational context-resume is an explicit
  NON-GOAL. Today's done_slot() has no such discrimination — it persists blanket, gated only by context_used_pct. Also
  lowers resume_lifecycle.py's resume_fresh_context_pct 90->80 (operator-directed) and documents the full
  saturated-context prune lifecycle (context_burn_kill -> classify_dead_worker requeue -> AutoSpawn fresh spawn) that
  was verified to have no coverage gap. A third thread (a described "kill blocked-and-unanswered slot after ~10min"
  mechanism) was investigated and found to have NEVER existed in this repo's git history — explicitly NOT built here,
  see Progress Log.
status: active
nature: process
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator, unified-trading-pm]
scope: [engineer]
tags: [orchestrator, context-management, worker-lifecycle, dispatch, resume]
related:
  [
    /plans/archive/2026_07/ao_worker_context_lifecycle_gap_2026_07_25.md,
    /plans/archive/2026_07/ao_worker_context_lifecycle_gap_finalize_2026_07_25.md,
    /plans/epics/orchestrator_master.md,
  ]
created: "2026-07-27"
last_updated: "2026-07-27"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 0.96
assigned_role: backend_engineer
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source: >-
  Slack thread 2026-07-25/27 (Ikenna Igboaka / Harsh Kantariya): Ikenna's "smoking gun" analysis of unbounded context
  carryover across /done-persisted tasks (fully closed by the now-archived ao_worker_context_lifecycle_gap_2026_07_25.md
  before this plan was authored); Harsh's clarification that persistence should be conditional on same-plan continuity,
  not blanket, plus that resume/respawn should gate on a lower context threshold than the shipped 90%; Ikenna's
  follow-up asking whether the reset-vs-persist policy was meant to be manually or automatically governed, and asking
  for blocked-question answers to persist onto the plan rather than needing to be re-asked. Operator (this session,
  2026-07-27) resolved the open design questions via AskUserQuestion: (1) do NOT build the described
  blocked-timeout-kill mechanism, but investigate whether it ever existed; (2) lower resume_fresh_context_pct to 80%,
  and trace who prunes a saturated worker end-to-end; (3) reset trigger = different plan_ref OR different
  assigned_role/repos; (4) implement now, this session (LOCAL plan, not AO-dispatched).
---

# AO worker session reset policy — plan-continuity gate + resume-threshold tuning

> **Codex SSOTs to check against / update on completion**:
> `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` (§ "Conversational context-resume is an
> explicit NON-GOAL", § "Worker lifecycle" — this plan adds a SECOND persistence gate alongside the context-pct one),
> `/codex/04-architecture/agent-orchestrator-worker-liveness.md` (resume_fresh_context_pct / classify_dead_worker was
> never documented there — gap predates this plan but adjacent), `unified-trading-pm/agents/worker.md` (directive field
> contract).

## Investigation findings (resolved before writing code — see Progress Log for full detail)

1. **The described "kill a blocked-and-unanswered worker after ~10 minutes" mechanism never existed.** Blamed the
   `WorkerLivenessWatchdog`'s "never kill a slot with status == 'blocked'" rule to its origin commit (`97cda3f9`,
   2026-06-01 — the watchdog's very first commit) and searched the ENTIRE git history (`git log --all -S`) for any prior
   blocked-timeout-kill concept: zero hits. Per operator direction, **not building this** — the current
   nudge-in-place-on-answer behavior stays as-is.
2. **The saturated-context worker prune lifecycle has no coverage gap.** Full chain, verified by reading
   `worker_liveness_watchdog.py` + `resume_lifecycle.py` + `config.py`: `context_worker_compact_gate_pct=70` withholds
   the next task and asks the worker to compact; if ignored, `context_burn_min_pct=80` (OR 3+ compactions) combined with
   4h+ session staleness flags `context_burn_suspected`; `context_burn_kill_min_pct=98` (with a 2-report grace window
   requiring a directive was already issued) actively KILLS the live session (WIP-preserved first via
   `_preserve_wip_before_kill`) — `context_burn_kill` defaults `True` as of the now-archived parent plan. Once dead,
   `classify_dead_worker` (`resume_lifecycle.py`) checks `context_used_pct >= resume_fresh_context_pct` and requeues
   (never resumes) a saturated session to a fresh worker. Since a killed-for-being-saturated session is always well
   above even the lowered 80% bar, lowering `resume_fresh_context_pct` cannot regress this path.

## Todos

- [x] ✅ [BACKEND] P1. Lower `resume_fresh_context_pct` default 90 -> 80 in `server/config.py` (`agent-orchestrator`),
      mirroring the existing `Field(default=..., ge=1, le=100)` pattern on the same class. Add/ update a unit test
      asserting the new default. **Done when**: `get_config().tuning.resume_fresh_context_pct` resolves to 80 by default
      in a passing test; `quality-gates.sh` green. — **`agent-orchestrator@998574b`.** Also updated 4 existing tests in
      `test_task_lifecycle_done_gate_resume.py` whose premises assumed the old 90 default (one, `..._mid_context_...`,
      exercised the now-collapsed resume_compact_first_context_pct..resume_fresh_context_pct band and was rewritten as
      `test_classifier_below_fresh_cutoff_still_resumes`). `quality-gates.sh` green (1798 passed, 2 skipped).
- [x] ✅ [BACKEND] P1. Add `plan_continuity_reset_enabled: bool = Field(default=False)` to `Tuning` in
      `server/config.py` — feature-flagged OFF by default, mirroring the `context_burn_kill` precedent (a new fleet-wide
      dispatch-behavior change ships gated, then gets an explicit operator flip once verified, rather than going live
      unreviewed). **Done when**: default resolves to `False` in a passing test; `quality-gates.sh` green. —
      **`agent-orchestrator@998574b`.** `test_plan_continuity_reset_enabled_default_is_false`.
- [x] ✅ [BACKEND] P1. Extend `DoneResponse.directive` in `server/models/worker_api.py` from
      `Literal["compact_before_next"] | None` to `Literal["compact_before_next", "reset_before_next"] | None`. **Done
      when**: a model-level test asserts the new literal value validates and serializes; existing `compact_before_next`
      tests unaffected. — **`agent-orchestrator@998574b`.**
      `test_done_response_directive_field_accepts_reset_before_next`.
- [x] ✅ [BACKEND] P0. Implement the plan-continuity reset check in `done_slot()` (`server/routes/slots_worker.py`),
      immediately after `pick_next_task` returns a real candidate (i.e. AFTER the existing context-pct gate, which takes
      priority and is unchanged). When `plan_continuity_reset_enabled` is `True` and the candidate task's `plan_ref`
      differs from the just-completed task's `plan_ref`, OR its `assigned_role` differs, OR its `repos` set differs: do
      NOT dispatch it in this response (leave it `queued`, untouched — same withhold contract the context gate already
      uses); log a new activity type `worker_plan_switch_reset` (slot_id, task_id, from/to plan_ref+role+repos); kill
      this slot's own tmux session via a daemon thread
      (`threading.Thread(target=tmux_spawn.kill_session, args=(reap_session,), daemon=True).start()` — the EXACT
      established pattern the one_shot-reap branch already uses a few lines below in the same function, " off the
      request thread so the SQLite write lock isn't held across the kill subprocess"); return
      `DoneResponse(next_task=None, status="idle", directive="reset_before_next", ...)`. When the flag is `False`
      (default), behavior is byte-for-byte unchanged from today. **Done when**: a unit test asserts (a) flag off ->
      dispatches normally even across a plan/role/repo switch (today's behavior, unchanged); (b) flag on + same plan_ref
      -> dispatches normally in the same session; (c) flag on + different plan_ref (or role, or repos) -> withholds the
      task (stays `queued`), fires the kill thread, returns `directive="reset_before_next"`; `quality-gates.sh` green. —
      **`agent-orchestrator@998574b`.** Implemented as designed, PLUS: extended the trigger to also cover a different
      `assigned_role` (matching the operator's actual answer — "different plan_ref OR different assigned_role/repos" —
      not just plan_ref alone as this todo's own first sentence undersold). Split into 3 small module-level functions
      (`_plan_switch_needs_reset`, `_plan_switch_reset_response`, `_maybe_plan_switch_reset`) rather than inlining —
      `done_slot` was already sitting at the repo's C901 complexity ceiling (26) and the inline version pushed it to 27;
      also had to extract the pre-existing account-rotation block into its own `_maybe_rotate_rate_limited_account`
      helper to claim back enough headroom. 4 new tests (flag-off unchanged, same-plan dispatches normally, different
      plan_ref resets, different role resets) in `test_task_lifecycle_done_gate_resume.py`. `quality-gates.sh` green.
- [x] ✅ [INFRA] P1. Update `unified-trading-pm/agents/worker.md`'s directive-field documentation to also cover
      `reset_before_next` (alongside the existing `compact_before_next`/`compact_now`): the worker does not need to take
      any action itself (the server has already triggered the session teardown) — document it purely for observability,
      so an agent that reads a `reset_before_next` response is not confused into thinking it must self- compact. **Done
      when**: worker.md documents both directive values in the same section; doc-lint passes. — Added a
      `reset_before_next` paragraph to the PROGRESS section's HARD RULE block, a note on the DONE section's `next_task`
      docs, and a `4c.` line in the boot-loop pseudocode — same 3-touchpoint pattern the parent plan's todo 5 used for
      `compact_before_next`.
- [x] ✅ [INFRA] P1. Update codex: add a note to `agent-orchestrator-single-vm-architecture.md`'s "Persistence is now
      GATED..." bullet (added by the parent plan's finalize) describing this SECOND, plan-continuity-based gate,
      feature-flagged and defaulting off; add the `resume_fresh_context_pct` mechanism (never previously documented) to
      `agent-orchestrator-worker-liveness.md` alongside the context-burn trigger row added by the parent finalize.
      **Done when**: both docs describe the mechanism currently shipped in code, not aspirationally. — Added a new
      bullet to `agent-orchestrator-single-vm-architecture.md` right after the context-pct-gate bullet; added a new
      "Dead-worker resume-vs-requeue gate" section to `agent-orchestrator-worker-liveness.md` covering
      `classify_dead_worker`, `resume_fresh_context_pct`/`resume_compact_first_context_pct`, and the band-collapse side
      effect, plus an explicit note that a context-burn kill can never regress into a resume (it's always well above
      even the lowered threshold).
- [x] ✅ [REVIEW] P0. Run full `quality-gates.sh` on `agent-orchestrator` after all code todos land; commit + push via
      quickmerge; flip every checkbox above in the SAME turn per the commit-push-flip HARD RULE. —
      **`agent-orchestrator@998574b`**, quickmerged to `live-defi-rollout`. Full suite: 1798 passed, 2 skipped; ruff +
      basedpyright clean; dashboard tsc + vitest (154 tests) clean.
- [x] ✅ [OPERATOR] P1. **Decide whether to flip `plan_continuity_reset_enabled` to `True`** now that it's implemented,
      tested, and quickmerged — mirrors the `context_burn_kill` precedent (ship gated, flip on operator approval once
      verified). BLOCKED-OPERATOR-DECISION until answered; not auto-flipped by this plan. — **APPROVED 2026-07-27
      (operator, in-session, verbatim: "Flip to True now")** — `agent-orchestrator@0f85d03`, same-day flip. Updated
      `test_plan_continuity_reset_enabled_default_is_false` → `..._default_is_true` and the flag-off test
      (`test_plan_continuity_reset_flag_off_dispatches_normally_across_plan_switch`) to explicitly set the flag `False`
      via `set_tuning`, since it can no longer rely on the (now-flipped) default. `quality-gates.sh` green, quickmerged
      to `live-defi-rollout`.

## Progress Log

**2026-07-27 (interactive session, operator-directed, implemented in-session per the "implement now" execution-mode
answer).** All 6 dispatchable todos landed in a single quickmerge, `agent-orchestrator@998574b`. Full detail in each
todo's own evidence line above; summary: lowered `resume_fresh_context_pct` 90->80 (+ fixed 4 tests whose premises
assumed the old default), added the feature-flagged `plan_continuity_reset_enabled` (default False), extended
`DoneResponse.directive`, implemented the plan-continuity reset check in `done_slot` (extended to also trigger on
`assigned_role` mismatch per the operator's actual answer, not just `plan_ref`), and updated both `worker.md` and two
codex docs. `quality-gates.sh`: 1798 passed, 2 skipped, ruff + basedpyright clean, dashboard tsc/vitest clean.

Only the `[OPERATOR]` todo (whether to flip `plan_continuity_reset_enabled` to `True`) remains — asked directly this
session rather than left as a silent blocker.

**2026-07-27 (same session, continued).** Operator approved the flip verbatim ("Flip to True now") — shipped
`agent-orchestrator@0f85d03` same-day, `quality-gates.sh` green. **All 7 todos in this plan are now done** — no operator
action or further work remains. This plan is ready for its own finalize/archival pass (not run in this session — the
`ao_worker_context_lifecycle_gap` precedent uses a separate gated finalize plan; this plan is small enough that a future
archival pass can fold the standard 6-step ritual directly here, or a dedicated finalize plan can be authored per the
operator's usual preference for AO-dispatched plans — this one is LOCAL, so either is fine).

## Deferred work after 2026-07-27

| Item                                                                                                                              | State              | Blocked on                                                                                                                     |
| --------------------------------------------------------------------------------------------------------------------------------- | ------------------ | ------------------------------------------------------------------------------------------------------------------------------ |
| Run the standard 6-step archival ritual on this plan (banner, codex-alignment re-check, referrer fixup, move to `plans/archive/`) | Not done           | Nobody — all 7 todos are done; this is routine closeout, not new work                                                          |
| Watch live `worker_plan_switch_reset` volume now that `plan_continuity_reset_enabled=True` is deployed                            | Cannot be done yet | Elapsed time — needs the fleet to actually dispatch across plan/role boundaries post-deploy before there's anything to observe |

**Recommended next item**: nothing needs a human right now — both remaining items are routine/observational, not
blocking. When picked up again, the archival ritual is the quick one (few minutes); the live-volume watch is better
suited to a future `/check-agent-orchestrator`-style read-only pass once the fleet has run for a while under the new
flag.
