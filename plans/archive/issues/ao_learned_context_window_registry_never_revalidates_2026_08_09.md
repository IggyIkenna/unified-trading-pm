---
doc_type: issue
title: The learned context-window registry is write-once-and-forever — no re-validation, no decay, no per-session model
summary: >-
  context_probe's learned-window registry has three properties that combine badly: calibrated_window is MONOTONIC (only
  ever raised), TOP-PRECEDENCE (beats the watermark and the model_tier prior unconditionally), and NEVER RE-VALIDATED
  once written. A wrong value is therefore permanent and fleet-wide, which is precisely how the 2026-08-09 main-agent
  incident happened. The 1.5x plausibility bound shipped that day blocks GROSS poisoning, but a wrong-but-plausible
  calibration is still permanent. Two live observations remain open underneath it: claude-opus-5 currently sits at
  watermark 222,121 / hits 1 — the exact trap the module docstring warns about — and main's true window measures ~696K
  against a 937,882 corpus figure for the same model, which the per-model design cannot express.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, context, measurement, context-probe]
related:
  [
    /plans/archive/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
  ]
created: 2026-08-09
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
drift_direction: advance-code
resolved_by: agent-orchestrator@50e91cb69, agent-orchestrator@4aabab446, agent-orchestrator@cb5bf0050
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Surfaced 2026-08-09 while fixing the poisoned-calibration incident; these are the residual weaknesses the shipped
  bound does not close.
depends_on: []
context_scope:
  [
    agent-orchestrator/server/context_probe.py,
    agent-orchestrator/server/model_tier.py,
    /plans/archive/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
  ]
---

# The learned context-window registry is write-once-and-forever

> **🟢 RESOLVED 2026-08-09** — all four todos closed. Re-validation + rejection-visibility + session-scoped watermark
> confirmation shipped (`agent-orchestrator@50e91cb69`, `@4aabab446`, `@cb5bf0050`); the per-model-vs-per-session
> divergence (todo 4) was found already investigated and closed in
> `/codex/04-architecture/agent-orchestrator-worker-liveness.md` § "Context-window learning is per-model; per-session
> divergence is expected and already floored (2026-08-09)" — no registry-key widening, the AgentRow/SlotRow self-report
> floor is the compensating control. See the Progress Log below for full detail.

## The residual weaknesses

The 2026-08-09 fix restricted WHO may calibrate (CLI-rendered percentages only) and added a plausibility bound (1.5× the
larger of the `model_tier` prior and the observed watermark). Both are write-time guards. The registry's deeper shape is
unchanged:

- **Monotonic.** `calibrated_window` is only ever raised. There is no path that lowers or clears one.
- **Top-precedence.** `context_window_for` returns `calibrated_window` unconditionally when set, ahead of the watermark
  and the prior.
- **Never re-validated.** Once written it is never checked against later evidence, however much accumulates.

So a calibration that is wrong but _within_ 1.5× is still permanent — and a 1.4× error still under-reports a 99% session
as 71%, which is below the recycle logic's expectations even though it clears the guidance threshold.

## Two open live observations

1. **`claude-opus-5` sits at `watermark_tokens: 222121, watermark_hits: 1`.** This is verbatim the trap the module
   docstring documents: _"a fresh registry learned a 222,121-token watermark from ONE in-flight claude-opus-5 session
   and reported it as 97% full when the true figure was ~22%"_. It is currently harmless only because
   `_WATERMARK_CONFIRM_HITS = 3` gates it. If two more opus-5 sessions happen to cluster near that mark, the guard
   passes and every opus-5 session starts reporting ~97%.
2. **Per-model is the wrong granularity.** main's session measured 689,570 tokens at a CLI-reported 99%, implying a real
   window near **696K**. The corpus figure for the same model (`claude-sonnet-5`) is 937,882 and the `model_tier` prior
   is 1M. A single per-model number cannot express an effective window that varies by account, session, or beta-flag —
   and the gap is large enough (~30 points) that the policy would be materially wrong without main's AgentRow floor
   covering for it.

## Todos

- [x] ✅ [BACKEND] P1. Re-validate instead of trusting forever: when a fresh CLI-rendered pct disagrees with the stored
      `calibrated_window` by more than a configurable tolerance, REPLACE it (in either direction) rather than keeping
      the larger. Preserve the monotonic behaviour for the WATERMARK, which is a genuine lower bound. Done-when: a unit
      test proves a later authoritative reading lowers an over-large `calibrated_window`. — agent-orchestrator@50e91cb69
- [x] ✅ [BACKEND] P1. Emit an activity event + log line whenever `_calibration_is_plausible` REJECTS a calibration —
      today it only logs a warning, so a caller regression that keeps feeding bad values is invisible in the dashboard.
      Done-when: the event appears in `GET /api/activity` and a unit test asserts it. — agent-orchestrator@4aabab446
- [x] ✅ [BACKEND] P2. Neutralise the opus-5 single-hit watermark before it can confirm: either require the confirming
      hits to come from DISTINCT sessions, or discard a watermark whose hits all came from one `claude_session_id`.
      Done-when: a unit test proves three observations from ONE session do not saturate a watermark, and three from
      distinct sessions do. — agent-orchestrator@cb5bf0050
- [x] ✅ [BACKEND] P2. Evaluate whether the effective window is per-session/per-account rather than per-model, using
      main's ~696K-vs-937,882 divergence as the worked example. Done-when: the finding is recorded here and either the
      registry key is widened or the divergence is documented as expected with the AgentRow floor named as the
      compensating control. — documented, no code change (see Progress Log)

## Progress Log

- 2026-08-09 — Filed as the residual of the poisoned-calibration incident. The shipped source restriction and 1.5× bound
  close the gross case; these four todos close the "wrong but plausible, and permanent" case and the two live
  observations above.
- 2026-08-09 — Todo 1 shipped (`agent-orchestrator@50e91cb69`). `observe()` now adds a
  `_CALIBRATION_REVALIDATION_TOLERANCE = 0.15`: a fresh CLI-rendered calibration that disagrees with the stored
  `calibrated_window` by more than 15% replaces it in either direction (still gated by the existing 1.5×
  `_calibration_is_plausible` bound); within tolerance the prior larger-wins behaviour is unchanged. The watermark path
  is untouched — still fully monotonic. New unit tests: `test_authoritative_reading_lowers_an_over_large_calibration`
  (the acceptance test — a later 700K-tokens-at-50% reading replaces a stored 1.4M-window calibration with 700K) and
  `test_small_calibration_disagreement_still_only_raises` (a within-tolerance disagreement does not churn the stored
  value). Full QG green (2971 backend + 262 dashboard tests); landed on `live-defi-rollout`, verified as an ancestor of
  origin.
- 2026-08-09 — Todo 2 shipped (`agent-orchestrator@4aabab446`). `_calibration_is_plausible` now also writes a
  `context_calibration_rejected` `ActivityRow` (model, calibrated_window, reference, overshoot_ratio, max_overshoot)
  alongside the existing `logger.warning`, so a rejection is visible via `GET /api/activity` instead of only a log line.
  The DB write is best-effort (mirrors `_save_learned`'s catch-and-degrade posture for its sidecar file write) — a DB
  hiccup must not turn a correctly rejected calibration into an unhandled exception, and it keeps this module's existing
  DB-free unit tests unaffected. New unit test: `test_rejected_calibration_emits_an_activity_event` (spins up an
  isolated sqlite DB via `db.reset_for_tests` + `create_all_tables`, triggers a rejection, asserts the row via
  `list_activity`). Full QG green (2961 backend + 262 dashboard tests); landed on `live-defi-rollout`, verified as an
  ancestor of origin.
- 2026-08-09 — Todo 3 shipped (`agent-orchestrator@cb5bf0050`). `observe()` gains a `claude_session_id` parameter: a
  watermark hit only confirms the FIRST time a given session contributes one (tracked via a new `watermark_hit_sessions`
  list alongside the existing int counters in the sidecar registry — `_load_learned`/ `_save_learned` now round-trip
  both shapes), so N observations from one long-running session (exactly the claude-opus-5 trap —
  `watermark_tokens: 222121, watermark_hits: 1`) can never saturate a watermark on their own; a higher ceiling still
  resets the tracked sessions, same as before. `context_used_pct` feeds the transcript filename (the transcript IS named
  `<claude_session_id>.jsonl`, confirmed in `transcript_log.py`) through as the discriminator. Callers that omit
  `claude_session_id` (direct-call unit tests, mostly pre-existing ones in this file) keep the prior
  unconditional-increment behaviour, since there is no session identity to dedupe against. New unit tests:
  `test_three_hits_from_one_session_do_not_saturate_a_watermark` (the acceptance test), plus
  `test_three_hits_from_distinct_sessions_do_saturate_a_watermark`,
  `test_repeat_hits_from_a_returning_session_do_not_double_count`,
  `test_a_higher_ceiling_still_resets_hit_sessions_even_with_session_ids`, and
  `test_omitted_session_id_keeps_the_prior_unconditional_increment_behaviour`. Full QG green (2974 backend + 262
  dashboard tests); landed on `live-defi-rollout`, verified as an ancestor of origin.
- 2026-08-09 — Todo 4 evaluated: read `context_probe.py`/`model_tier.py` and traced the compensating floor through
  `context_lifecycle.py::_main_pct()` (main) and `_read_pct()`'s `max(SlotRow.context_used_pct, probe)` (worker/review).
  Found the investigation already recorded in `/codex/04-architecture/agent-orchestrator-worker-liveness.md` §
  "Context-window learning is per-model; per-session divergence is expected and already floored (2026-08-09)" — it
  independently ruled out account tier as the driver (main's `sub-f-odum2default` account was `max20`, the same tier
  that built the 937,882 sonnet-5 corpus watermark), named `effort`/`thinking` depth as the better-supported per-session
  driver (main runs `thinking: high` vs workers' `thinking: medium`), and concluded: **no registry-key widening** —
  `context_window_for(model)` stays a per-model cold-start fallback, and the per-session/per-account divergence is
  already compensated for the one target it matters to (that session) by the self-report floor
  (`AgentRow.context_used_pct` for main, `SlotRow.context_used_pct` for worker/review) — every fleet target today
  carries one of those two floors, so no session silently under-compacts on a smaller-than-average window. This todo's
  own done-when ("recorded here … or documented as expected with the AgentRow floor named as the compensating control")
  is satisfied by that already-shipped codex section; no additional registry change or code needed. Doc-only closure —
  no `agent-orchestrator` commit.
