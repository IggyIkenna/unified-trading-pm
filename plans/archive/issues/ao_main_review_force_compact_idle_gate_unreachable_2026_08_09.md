---
doc_type: issue
title: main/review forced-compact is gated behind an idle verdict a permanently-ticking loop agent never satisfies
summary: >-
  The main/review forced-compact fallback requires classify_pane == "idle" on 3 CONSECUTIVE keeper ticks, plus an empty
  input box, plus <=1 child process under the pane shell. main is a continuously-ticking loop agent, so the streak
  resets on nearly every tick and the gate is unlikely to ever open. Three consequences compound it: main's
  context_pressure is hardcoded "low" (so the pressure == "thrashing" immediate-recycle trigger is structurally
  unreachable for main), main's terminal wedge-recovery sits DOWNSTREAM of a force that may never fire, and both Tier-1
  guidance and Tier-2 recycle are sent exactly once per episode. Surfaced while root-causing the 2026-08-09 poisoned
  learned-window incident (fixed separately, agent-orchestrator@LDR): with the measurement corrected, main now reaches
  the 60% threshold and gets guidance, so whether the FORCE behind it can ever fire is now the live question.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, context, compaction, main-agent, review-agent, worker-lifecycle]
related:
  [
    /plans/archive/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
    /plans/active/issues/forced_compact_reports_submitted_but_never_executes_2026_08_08.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-09
last_updated: "2026-08-10"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: fix-regression
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Isolated 2026-08-09 (interactive session, slot 4) while diagnosing orch-agent-main pinned at 99% context. The
  measurement bug that masked this is fixed; this is the remaining structural gap underneath it.
depends_on: []
context_scope:
  [
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
    /plans/archive/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
  ]
---

> **🟢 ARCHIVED 2026-08-10** — `status: resolved`, all 7 todos `[x]`, unlocked; archived per
> [`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`](/codex/12-agent-workflow/plan-completion-and-archival-discipline.md).
> The operator's 2026-08-10 ruling (keep main/review cooperative-first, gate the reversal on an objective >=6h/>=90%
> data bar rather than a standing human ruling) is recorded at
> [`/codex/04-architecture/agent-orchestrator-worker-liveness.md`](/codex/04-architecture/agent-orchestrator-worker-liveness.md)
> § "main/review stay COOPERATIVE-first"; the machine guard proving it (`agent-orchestrator@9f8845e`,
> `test_main_and_review_never_reach_force_compact_without_the_idle_verdict`) is live on `live-defi-rollout`. Moved by
> the 2026-08-10 checkbox-flip + archive pass (slot 23).

# main/review forced-compact is gated behind an unreachable idle verdict

## The gap

`server/context_lifecycle.py` runs two policies. Workers (operator ruling 2026-08-05, "the guidance isn't useful if it
doesn't force") get an UNCONDITIONAL force the moment context crosses 60% — no idle check, no deadline. main and review
kept the older cooperative-first shape, whose forced fallback runs through `_maybe_force_compact` and requires **all**
of:

1. `classify_pane(pane) == "idle"` on **3 consecutive** keeper ticks (`_FORCE_IDLE_OBSERVATIONS`),
2. `tmux_spawn.pane_input_pending(session)` false,
3. `_pane_has_child_processes(session)` false — and that helper returns **True** (i.e. "not safe to force") on any
   failure to measure.

`classify_pane` returns `"working"` whenever a spinner is present. main is a loop agent that ticks continuously and
shells out to `gh`/`curl`/`git` on nearly every tick, so signals 1 and 3 both routinely fail. Live evidence 2026-08-09:
in a 4.3-hour `/api/activity` window there were **132** context-lifecycle events for `role=worker` and **1** for
`role=main` (a single client-side `context_compact_observed`); `proactive_compact_guidance`, `forced_precompact`,
`forced_compact` and `context_recycle_requested` were all **0** across every role.

That window is confounded — the poisoned learned window (separate issue, now fixed) meant main measured 26% and never
reached the 60% threshold at all, so the gate was never even TESTED. Which is exactly why todo 1-2 below measure before
changing policy: the gate's real open-rate is currently unknown, not known-bad.

## Three compounding defects in the same path

- **`context_pressure` is hardcoded for main.** `_read_pct` returns `(pct, "low")` for the slot-less main agent because
  pressure lives on `SlotRow`. The Tier-2 `pressure == "thrashing"` immediate-recycle trigger is therefore structurally
  unreachable for main — it can only ever recycle on compaction-count or 24h age.
- **main's terminal wedge-recovery is downstream of a force that may never fire.** `_rearm_if_force_ineffective` returns
  at its first branch when `state.forced_at is None`. The kill-session + clear-`claude_session_id` recovery for a wedged
  MAIN therefore only ever arms AFTER a force actually submitted. If the idle gate never opens, main's last-resort net
  is unreachable.
- **Guidance and recycle are one-shot per episode.** `guidance_sent_at` / `recycle_sent_at` are re-armed only by an
  observed compaction, and `_TargetState` is in-memory (reset on orchestrator restart, which also restarts the 24h
  recycle clock).

## Why this is not simply "extend the worker force to main"

The 2026-08-05 ruling deliberately kept main/review cooperative-first, with a stated rationale: _"never compact mid-work
— a single pane-snapshot 'looks idle' is untrustworthy on a days-long loop"_. main holds fleet state a worker does not.
Reversing that is an operator call (todo 5), not a worker's — so the AO-dispatchable todos here gather the evidence and
fix the two unambiguous structural defects, leaving the policy reversal explicitly gated.

## Todos

- [x] ✅ [BACKEND] P1. Instrument the gate: emit a `context_force_idle_gate_blocked` activity event (details: `role`,
      `session`, `pct`, and WHICH signal refused — `classify_pane` verdict / `pane_input_pending` / child-process count)
      on every tick where a main/review target is past `context_compact_force_after_seconds` but `_maybe_force_compact`
      declines. Done-when: the event is visible in `GET /api/activity` for a real main tick, with the blocking signal
      populated. — agent-orchestrator@279e07b (`_log_idle_gate_blocked` logs `signal` +
      `pane_verdict`/`idle_streak`/`required` detail on every decline: `pane_capture_failed` / `classify_pane` /
      `idle_streak_insufficient` / `pane_input_pending` / `child_processes`); unit-covered in
      `tests/test_context_lifecycle.py`, full QG green.
- [x] ✅ [BACKEND] P1. Measure for >=6h with the instrumentation live: how many ticks had main/review deadline-past, how
      many times the gate OPENED, and the dominant blocking signal. Record the counts in this doc's Progress Log.
      Done-when: the Progress Log carries open-vs-blocked counts for both roles. **RETARGETED 2026-08-10**: the ruling
      it was meant to inform is already made on a 3.7h sample (see the [OPERATOR] todo below), so this is no longer a
      gate on that decision — it now serves as the CONFIRMING run over a full window. Report it as confirmation that the
      cooperative path keeps working, not as new input to a pending ruling. — measured 2026-08-10 (slot 9); see Progress
      Log for the counts.
- [x] ✅ [BACKEND] P2. Machine-guard the ruling so it cannot be silently reversed: add a test asserting main and review
      route through the idle-gated `_maybe_force_compact` and never the worker unconditional-force path (the mirror of
      `_forbid_idle_checks`, which already guards the worker side). A doc-only ruling is not a gate — a future agent
      "fixing" the gate would otherwise ship the reversal green. Done-when: the test fails if a main/review target
      reaches `_force_compact_now` without the idle verdict. — agent-orchestrator@9f8845e (already shipped by slot 20,
      checkbox unflipped — found + flipped by slot 23, 2026-08-10): parametrized
      `test_main_and_review_never_reach_force_compact_without_the_idle_verdict` (main + review) proves both halves —
      structurally, `_forbid_worker_force_path` raises if either role ever touches `_tick_worker`; behaviorally, a busy
      pane blocks the force indefinitely and only 3 consecutive idle ticks let it through. Re-ran both parametrized
      cases locally: 2 passed.
- [x] ✅ [BACKEND] P1. Make main's terminal wedge-recovery reachable when no force ever fired.
      `_rearm_if_force_ineffective` returns early on `state.forced_at is None`, so the kill + `claude_session_id`
      clear + keeper respawn path cannot arm for a main that the idle gate never let through. Add a saturation-based
      entry (main above `resume_fresh_context_pct` with no `context_compact_observed` for a sustained window) that
      reaches the SAME recovery. Done-when: a unit test in `tests/test_context_lifecycle.py` proves recovery arms for a
      main target whose `forced_at` was never set. — agent-orchestrator@29f29f9 (new
      `_maybe_recover_unforced_saturation`, wired into `_tick_target` scoped to `role == "main"` only — review/worker
      keep their own separately-tested behavior, per todo 5's explicit operator-ruling gate; a first attempt applying it
      to every role broke 4 review-saturation tests by killing the session before the idle-gated force ever got a
      chance, caught by the full suite before shipping); new test
      `test_main_wedge_recovery_arms_even_when_the_force_never_fires`; full QG green (2984 passed).
- [x] ✅ [BACKEND] P2. Give main a real `context_pressure` instead of the hardcoded `"low"` in `_read_pct`, so the
      Tier-2 `pressure == "thrashing"` immediate-recycle trigger is reachable for main at all. Derive it the same way
      the SlotRow value is derived. Done-when: a unit test proves a thrashing main recycles without waiting for
      compaction-count or the 24h age clock. — agent-orchestrator@45868bc (`_read_pct` now takes `now`/`state` and, for
      the slot-less main path, derives pressure via `state_store.derive_context_pressure(pct, compactions_last_hour)` —
      the SAME function `record_slot_progress` uses for `SlotRow.context_pressure` — counting `state.compactions` in the
      trailing 1h since main has no `CompactionRow` history; new test
      `test_main_thrashing_pressure_triggers_recycle_without_compaction_count_or_age` proves the Tier-2 recycle fires on
      `pressure == "thrashing"` alone, with `context_recycle_compactions` raised to 100 and a fresh episode so the other
      two Tier-2 triggers are structurally ruled out); full QG green (3003 python + 262 dashboard tests).
- [x] ✅ [BACKEND] P2. Re-arm Tier-1 guidance on a timer as well as on an observed compaction: today `guidance_sent_at`
      clears only when a compaction is detected, so a main that silently ignores one nudge is never nudged again for the
      rest of the episode. Done-when: a unit test proves a second guidance message is enqueued after a configurable
      unacked interval with no compaction observed. — agent-orchestrator@63b8897 (new
      `context_compact_guidance_rearm_seconds` tuning knob, default 900s; `_tick_target` now clears `guidance_sent_at`
      past that interval when `forced_at is None` — no force has fired this episode, the scope this todo covers, since
      `_rearm_if_force_ineffective` already owns retries once a force DOES fire — so Tier 1 re-fires instead of staying
      permanently spent for the rest of the episode); 3 new tests in `tests/test_context_lifecycle.py` (rearm fires past
      the window, does not rearm before it elapses, does not rearm once a force has fired); full QG green (2989 passed,
      basedpyright clean).
- [x] ✅ [OPERATOR] P1. Ruling, with measured evidence in hand: **KEEP main/review idle-gated and cooperative-first.**
      The worker-style unconditional force is NOT extended to them. Operator ruling 2026-08-10
      (`/codex/04-architecture/agent-orchestrator-worker-liveness.md`), on a 3.7h live measurement: the cooperative path
      was 17/17 = 100% effective (main guidance 1 -> compaction 1, idle gate blocked only once; review 16 compactions,
      zero forces) while the forced path was 14/65 = 22% effective (`forced_compact_ineffective` 51). Extending the
      force would move the two roles that compact reliably onto the path that currently fails ~78% of the time. The
      2026-08-05 rationale survives contact with the data. Recorded in
      `/codex/04-architecture/agent-orchestrator-worker-liveness.md` section "main/review stay COOPERATIVE-first — the
      idle gate is intended, not a defect (operator ruling 2026-08-10, per the same
      `/codex/04-architecture/agent-orchestrator-worker-liveness.md`)", including the correction that the idle
      requirement is ~3 MINUTES (3 x 60s keeper ticks), not the >=6h instrumentation observation window.

## Progress Log

- 2026-08-09 — Filed from an interactive diagnosis of `orch-agent-main` pinned at 99%. The PRIMARY cause was a poisoned
  learned context window (separate issue, fixed and shipped); this doc captures the structural gaps underneath it that
  the measurement bug was masking. Live counts at filing time: 4.3h `/api/activity` window, `role=worker` = 132
  context-lifecycle events, `role=main` = 1.
- 2026-08-09 (slot 22) — Shipped todo 3 (agent-orchestrator@29f29f9): added `_maybe_recover_unforced_saturation`, a new
  saturation-based entry that reaches the same kill + `claude_session_id`-clear recovery `_rearm_if_force_ineffective`
  already provides, but for the complementary case where `state.forced_at` was NEVER set (the force never even
  submitted). Scoped to `role == "main"` only after an initial all-roles version broke 4 existing review-saturation
  tests (a saturated review target got recovered before its own idle-gated force ever had a chance to try) — caught by
  the full `test_context_lifecycle.py` suite pre-ship, not shipped broken.
- 2026-08-09 (slot 19) — Dispatched todo 1 independently and implemented the same instrumentation, then found slot 15
  had already shipped an equivalent, already-QG-green version at `agent-orchestrator@279e07b` (a known double-dispatch
  pattern per `/plans/active/issues/orchestrator_failover_double_dispatch_duplicate_work_2026_07_25.md`). Skipped my
  duplicate commit during rebase (`git rebase --skip`, no code conflict landed) and flipped this checkbox against
  279e07b instead of shipping a redundant second implementation.
- 2026-08-09 (slot 15) — Was dispatched todo 2 (the >=6h measurement) directly, before todo 1 had shipped — confirmed
  via the backlog (`GET /api/backlog`) that todo 1's task was still `queued`/unclaimed at the time, so implemented +
  shipped it first (see checkbox above) since todo 2 is unstartable without it. Deployed + verified LIVE on the
  orchestrator VM: checkout `e8818aa` (descends from `279e07b`) with `orchestrator.service` `ActiveEnterTimestamp` =
  **2026-08-09T18:00:24Z**, confirmed AFTER that pull (not a stale pre-pull process). Checked `GET /api/activity`
  post-deploy: 0 `context_force_idle_gate_blocked` events yet — expected, not a bug: the restart the deploy required
  also cleared `ContextLifecyclePolicy`'s in-memory `_TargetState` (this doc's own "Guidance and recycle are one-shot
  per episode" defect above), so every target's `guidance_sent_at`/`forced_at`/`idle_streak` reset to unset at that
  moment — main/review has to re-climb to the Tier-1 guidance threshold and then clear
  `context_compact_force_after_seconds` again before the now-instrumented gate is even reached. Starting todo 2's
  > =6h window from **2026-08-09T18:00:24Z** (the confirmed-live restart timestamp), not from filing time — no tick
  > before that point could have hit the instrumented code path at all. Releasing todo 2 back to the queue
  > (`reason_code: GATED`) rather than holding this session open for a multi-hour wall-clock wait; the next dispatch
  > (this slot or another) should read this timestamp and query `/api/activity` (`context_force_idle_gate_blocked` /
  > `forced_precompact` / `forced_compact`, `role in {main, review}`, `ts >= 2026-08-09T18:00:24Z`) once the window has
  > actually elapsed to fill in todo 2's open-vs-blocked counts.
- 2026-08-09 (slot 8) — Shipped todo 4 (agent-orchestrator@45868bc): `_read_pct` now derives main's `context_pressure`
  via `state_store.derive_context_pressure` instead of the hardcoded `"low"`, using `state.compactions` (in-memory, same
  list every role's compaction-detection block already maintains) for the trailing-1h `compactions_last_hour` count,
  since main has no `CompactionRow` history. Session resumed mid-task after a prior death; WIP was intact on re-boot, so
  no rework needed. Todos 2 and 5 remain open (2 needs the >=6h measurement window from the 2026-08-09 slot-15 note
  above; 5 is the explicit operator ruling gate).

- 2026-08-10 — **[OPERATOR] RULING: keep main/review cooperative-first; the idle gate is INTENDED.** Decided on a 3.7h
  live `/api/activity` measurement rather than first principles: cooperative 17/17 = 100% effective vs forced 14/65 =
  22%. Also corrected a misreading this doc invited — the idle requirement is ~3 minutes (3 x 60s keeper ticks), NOT
  the >=6h instrumentation observation window; the two were being conflated. Ruling recorded in
  `/codex/04-architecture/agent-orchestrator-worker-liveness.md` with an anti-pattern entry, so a future agent reading
  "the gate never opens" does not treat it as a defect and ship the reversal. Note the doc TITLE still says
  "unreachable", which the ruling supersedes: the gate is rarely reached because the cooperative nudge lands first, and
  that is working as designed. Remaining work is the confirming measurement + the machine guard.
- 2026-08-10 — **Ruling's guard RELAXED from an operator gate to a DATA gate** (operator, same day). The anti-pattern
  first read "do NOT extend the force without a new operator ruling backed by a fresh measurement", which made every
  future revisit a human bottleneck even when the evidence would be unambiguous. It now states the objective bar
  instead: a worker may extend the force to main/review with NO further ruling once a >=6h live-fleet measurement shows
  forced-path effectiveness both (a) >= the cooperative path's and (b) >= 90% absolute. Baseline to beat: cooperative
  17/17 = 100%, forced 14/65 = 22%. This keeps the protection (evidence is still required, and `submitted=True` is
  explicitly rejected as evidence) while making the condition worker-determinable, per the dispatch-scope-eligibility
  principle that a todo's outcome must be checkable by the worker alone. SSOT:
  `/codex/04-architecture/agent-orchestrator-worker-liveness.md` § "main/review stay COOPERATIVE-first".

- 2026-08-10 (slot 9) — Shipped todo 2, the confirming >=6h measurement, queried directly against `GET /api/activity` on
  the orchestrator VM (this session runs ON that VM — `localhost:8765` answers directly, so no SSM detour was needed)
  for
  `types=context_force_idle_gate_blocked,forced_precompact,forced_compact, context_force_compact_queued_hold,forced_precompact_submit_failed`
  since the confirmed-live restart timestamp `2026-08-09T18:00:24Z` through `2026-08-10T00:25:35Z` (6h25m, satisfies
  the >=6h bar). 202 total matching rows in the window. **Open-vs-blocked counts, `role in {main, review}`** (OPENED = a
  tick where the idle multi-signal verdict passed and `_force_compact_now` was entered —
  `forced_precompact`/`forced_compact`/ `context_force_compact_queued_hold`/`forced_precompact_submit_failed`; BLOCKED =
  `context_force_idle_gate_blocked`):
  - `main`: deadline-past ticks = 1, blocked = 1, opened = 0. Dominant blocking signal: `classify_pane` (1/1).
  - `review`: deadline-past ticks = 0, blocked = 0, opened = 0 — review never reached a deadline-past tick in this
    window (compacted cooperatively via Tier-1 guidance before ever crossing `context_compact_force_after_seconds`).
  - For contrast, the 201 non-main/review rows in the same window were all `role=worker` (`forced_precompact`=99,
    `forced_compact`=92, `context_force_compact_queued_hold`=9, `forced_precompact_submit_failed`=1) — the unconditional
    worker force path firing at its normal high volume, unrelated to this todo's idle-gated main/review path.
  - **Consistent with the operator's 3.7h sample** (todo 5 above: "idle gate blocked only once" for main, review
    reaching zero forces) — same shape holds over the fuller window, nothing new surfaces. Reported as the CONFIRMING
    run per the 2026-08-10 retarget, not as new input to a pending decision.

- 2026-08-10 (slot 23) — Dispatched todo 3 (the machine-guard test) and found it was already shipped at
  `agent-orchestrator@9f8845e` (slot 20, 2026-08-10T01:59:37Z) — code landed on `live-defi-rollout` but the plan
  checkbox was never flipped (a missed Half-2 of the commit+push+flip rule, not a double-dispatch collision — only one
  implementation exists). Verified the shipped test still passes on a fresh pull
  (`test_main_and_review_never_reach_force_compact_without_the_idle_verdict[main]` and `[review]`, 2 passed) before
  flipping the checkbox against the existing commit rather than reimplementing.
