---
doc_type: issue
title: The learned context-window registry is write-once-and-forever — no re-validation, no decay, no per-session model
summary: >-
  context_probe's learned-window registry has three properties that combine badly: calibrated_window is MONOTONIC
  (only ever raised), TOP-PRECEDENCE (beats the watermark and the model_tier prior unconditionally), and NEVER
  RE-VALIDATED once written. A wrong value is therefore permanent and fleet-wide, which is precisely how the
  2026-08-09 main-agent incident happened. The 1.5x plausibility bound shipped that day blocks GROSS poisoning, but a
  wrong-but-plausible calibration is still permanent. Two live observations remain open underneath it: claude-opus-5
  currently sits at watermark 222,121 / hits 1 — the exact trap the module docstring warns about — and main's true
  window measures ~696K against a 937,882 corpus figure for the same model, which the per-model design cannot express.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, context, measurement, context-probe]
related:
  [
    /plans/active/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
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
resolved_by:
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
    /plans/active/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
  ]
---

# The learned context-window registry is write-once-and-forever

## The residual weaknesses

The 2026-08-09 fix restricted WHO may calibrate (CLI-rendered percentages only) and added a plausibility bound (1.5×
the larger of the `model_tier` prior and the observed watermark). Both are write-time guards. The registry's deeper
shape is unchanged:

- **Monotonic.** `calibrated_window` is only ever raised. There is no path that lowers or clears one.
- **Top-precedence.** `context_window_for` returns `calibrated_window` unconditionally when set, ahead of the
  watermark and the prior.
- **Never re-validated.** Once written it is never checked against later evidence, however much accumulates.

So a calibration that is wrong but *within* 1.5× is still permanent — and a 1.4× error still under-reports a 99%
session as 71%, which is below the recycle logic's expectations even though it clears the guidance threshold.

## Two open live observations

1. **`claude-opus-5` sits at `watermark_tokens: 222121, watermark_hits: 1`.** This is verbatim the trap the module
   docstring documents: *"a fresh registry learned a 222,121-token watermark from ONE in-flight claude-opus-5 session
   and reported it as 97% full when the true figure was ~22%"*. It is currently harmless only because
   `_WATERMARK_CONFIRM_HITS = 3` gates it. If two more opus-5 sessions happen to cluster near that mark, the guard
   passes and every opus-5 session starts reporting ~97%.
2. **Per-model is the wrong granularity.** main's session measured 689,570 tokens at a CLI-reported 99%, implying a
   real window near **696K**. The corpus figure for the same model (`claude-sonnet-5`) is 937,882 and the `model_tier`
   prior is 1M. A single per-model number cannot express an effective window that varies by account, session, or
   beta-flag — and the gap is large enough (~30 points) that the policy would be materially wrong without main's
   AgentRow floor covering for it.

## Todos

- [ ] [BACKEND] P1. Re-validate instead of trusting forever: when a fresh CLI-rendered pct disagrees with the stored
      `calibrated_window` by more than a configurable tolerance, REPLACE it (in either direction) rather than keeping
      the larger. Preserve the monotonic behaviour for the WATERMARK, which is a genuine lower bound. Done-when: a
      unit test proves a later authoritative reading lowers an over-large `calibrated_window`.
- [ ] [BACKEND] P1. Emit an activity event + log line whenever `_calibration_is_plausible` REJECTS a calibration —
      today it only logs a warning, so a caller regression that keeps feeding bad values is invisible in the
      dashboard. Done-when: the event appears in `GET /api/activity` and a unit test asserts it.
- [ ] [BACKEND] P2. Neutralise the opus-5 single-hit watermark before it can confirm: either require the confirming
      hits to come from DISTINCT sessions, or discard a watermark whose hits all came from one `claude_session_id`.
      Done-when: a unit test proves three observations from ONE session do not saturate a watermark, and three from
      distinct sessions do.
- [ ] [BACKEND] P2. Evaluate whether the effective window is per-session/per-account rather than per-model, using
      main's ~696K-vs-937,882 divergence as the worked example. Done-when: the finding is recorded here and either the
      registry key is widened or the divergence is documented as expected with the AgentRow floor named as the
      compensating control.

## Progress Log

- 2026-08-09 — Filed as the residual of the poisoned-calibration incident. The shipped source restriction and 1.5×
  bound close the gross case; these four todos close the "wrong but plausible, and permanent" case and the two live
  observations above.
