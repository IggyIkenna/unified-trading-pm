---
doc_type: issue
title: Forced /compact reports submitted=True but never executes — the real remaining wedge cause
summary: >-
  After the transcript-measured context signal landed (agent-orchestrator@c6e6d982a), forced compactions fire with real
  headroom (60-85 instead of 91-100) but frequently do not reduce context at all. orch-slot-21 took FIVE forced
  /compacts, every one reporting submitted=True, with context never falling. Zero submitted=False were logged anywhere
  in a 69-minute window, so the submit-verification cannot see the failure. This is now the dominant cause of worker
  recycles, and it was masked before the measurement fix because forces only ever fired at 99-100 where a session is
  unrecoverable anyway.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, context, compaction, tmux, worker-lifecycle]
related:
  [
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-08
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: fix-regression
resolved_by: ao_satellite_ao_dispatch_batch20_2026_08_13_finalize
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Isolated by the post-deploy validation windows for the context-measurement fix (2026-08-08 interactive session, slot
  1).
depends_on: []
context_scope:
  [
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
    agent-orchestrator/server/tmux_spawn.py,
    agent-orchestrator/server/context_probe.py,
    agent-orchestrator/server/context_lifecycle.py,
  ]
---

# Forced /compact reports submitted=True but never executes

> **🟢 ARCHIVED 2026-08-14 — RESOLVED.** Zero open todos as of the 2026-08-14
> `ao_satellite_ao_dispatch_batch20_2026_08_13_finalize.md` reconciliation pass (its last open item, re-measuring the
> wedge rate post-3-fixes, was completed: **worker wedge rate 0.0104/hr**, a ~330-930x reduction vs this doc's own
> 3.5/hr and 9.7/hr baselines). `archive_exempt: true` dropped per that finalize plan's own note ("Drop `archive_exempt`
> when that todo runs").

## The evidence

`orch-slot-21`, over 28 minutes, with every submission reporting success:

```
14:36:21  forced /compact did NOT reduce context (pct=62, was 62 at force, 1 consecutive) — re-armed
14:42:56  forced /compact did NOT reduce context (pct=68, was 62 at force, 2 consecutive) — re-armed
14:52:44  forced /compact did NOT reduce context (pct=68, was 68 at force, 1 consecutive) — re-armed
14:59:11  forced /compact did NOT reduce context (pct=68, was 68 at force, 2 consecutive) — re-armed
          slot=21 reason=context-wedged at 68%
```

`journalctl ... | grep -c 'submitted=False'` over the whole 69-minute window: **0**. Every force believes it worked.

## Why the verification cannot see it

`tmux_spawn.submit_to_pane()` returns True when the text leaves the input box, and its own docstring counts "consumed by
an already-running turn" as success. A message consumed into the CLI's **queue** — the
`Press up to edit queued messages` state, caught in a live pane capture on `orch-slot-4` — has left the input box but
has NOT executed. The caller then spends its force latch on a compaction that never happens.

## Why it only became visible now

Before the transcript-measured signal (`agent-orchestrator@c6e6d982a`), forces only fired at 99-100, where a session is
past the model's hard limit and `/compact` cannot succeed by construction. Every ineffective compact was therefore ALSO
saturated, and "the compact could not run because the session is too full" was indistinguishable from "the compact was
never executed". With forces now firing from 60, the two separate cleanly — and the second one is what is left.

## Todos

- [x] ✅ [BACKEND] P1. **Detect the queued-message state and do not spend the force-compact latch on it.** — **DONE
      2026-08-10 via batch12 todo 9 (`agent-orchestrator@a1e2969`)**: added `pane_has_queued_messages()` to
      `server/tmux_spawn.py` + `_TargetState.queued_since`; `_force_compact_now` checks it first and holds the latch
      un-spent (returns without submitting or advancing `precompact_forced_at`/`forced_at`) while the pane shows a
      queued-not-yet-executed message; logs `context_force_compact_queued_hold`.
      `test_worker_force_holds_latch_unspent_while_pane_shows_queued_message` proves it across 2 queued ticks. QG green
      (3022 passed, 2 skipped). Re-verified in the batch12-finalize review.
- [x] ✅ [BACKEND] P1. **Verify the compaction by its EFFECT, not by its submission.** — **DONE 2026-08-10 via batch12
      todo 10 (`agent-orchestrator@59d9417`)**: added `context_probe.compaction_confirmed_since()` reading the
      transcript's own `compact_boundary` system record; `context_lifecycle._tick_target` now treats
      `pct_dropped OR boundary_confirmed` as "compaction observed" (boundary check only consulted once the pct-drop
      heuristic fails AND a force is outstanding — no added per-tick cost). Closes the blind spot where a worker that
      compacts then goes quiet left `pct` stuck high.
      `test_boundary_confirms_compaction_the_old_pct_check_would_have_missed` + 3 more in test_context_probe.py. QG
      green (3109 passed). Re-verified in the batch12-finalize review.
- [x] ✅ [BACKEND] P2. **Build a deliberate repro for the queued-not-executed `/compact` mechanism.** — **DONE
      2026-08-10 via batch12 todo 11 (`agent-orchestrator@66be387`)**: 8 new unit tests in
      `tests/test_tmux_spawn_targets.py` — `pane_has_queued_messages` (detect/absent/error), `submit_to_pane`
      (clears/retry/stuck/error) + `test_repro_queued_compact_returns_true_but_shows_queued` proving the full ambiguity.
      All 27 tests in the file pass (re-verified in the batch12-finalize review).
- [x] ✅ [BACKEND] P3. **Re-measure the wedge rate once the above lands.** Baseline to beat, measured on the clean fleet
      after `c6e6d982a`/`9b269c0ce`: ~3.5 wedges/hr with forces distributed 62-97. Pre-measurement-fix baseline was
      ~9.7/hr with every force at 91-100. **MEASURED 2026-08-14 — `agent-orchestrator@3ee2996783`**
      (`scripts/orchestrator/forced_compact_wedge_rate_readout.py`, permanent readout tool): worker wedge rate over a
      96h post-all-3-fixes window = **0.0104/hr** (1 wedge in 96h) — a ~330-930x reduction vs both baselines above; sole
      wedge was the expected single-force-saturation-at-pct=100 case, not the queued-message bug these fixes targeted.
      Reconciled 2026-08-14 per `ao_satellite_ao_dispatch_batch20_2026_08_13_finalize.md` todo 1 (evidence from
      `ao_satellite_ao_dispatch_batch20_2026_08_13.md`).

## Codex SSOTs

- `/codex/04-architecture/agent-orchestrator-worker-liveness.md` — pane classification + inject contract

## Progress Log

- **2026-08-14 (batch20-finalize reconciliation)**: this doc's last open todo (re-measure the wedge rate) flipped `[x]`
  — the doc now has zero open todos. **Not archived here — `archive_exempt: true` set deliberately**: real archival
  (6-step ritual + corpus referrer fixup) is explicit scope of `ao_satellite_ao_dispatch_batch20_2026_08_13_finalize.md`
  todo 2, a separate dispatched unit of work, not this reconciliation pass. Drop `archive_exempt` when that todo runs.

- **2026-08-08 (interactive session, slot 1)**: Isolated while validating the context-measurement fix. The measurement
  fix did not cause this — it uncovered it. Mitigated in the same session by `agent-orchestrator@989592628`, which stops
  a slot with headroom from being recycled over a compaction that will not run; that is a containment, not the fix.
- **context-scout 2026-08-09**: populated context_scope (5 entries).
- **na-eligibility-audit 2026-08-09 (round9)**: KEEP-NA, valid — first audit pass on this doc. The 3 code-fix items are
  already `KEEP-NA-STALE, citation-closed` (duplicated verbatim into `ao_satellite_ao_dispatch_batch12_2026_08_09.md`
  todos 9-11 by a concurrent same-day pass). The sole remaining item (re-measure the wedge rate) is explicitly gated on
  those 3 landing plus a fresh multi-hour/day fleet-observation window — genuinely time-gated, not bounded today.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep, group 1)**: KEEP-NA, valid — checked
  `ao_satellite_ao_dispatch_batch12_2026_08_09.md` live: todo 9 (queued-message detection) is `[x]` done
  (`agent-orchestrator@a1e2969`), but todos 10 (verify-by-effect) and 11 (deliberate repro) are still `[ ]` open there —
  so this doc's own gate ("re-measure once the above lands") is not yet cleared. Still genuinely time-gated, not bounded
  today.
- **Measured 2026-08-09/10 (interactive session, slot 4)**, read-only via `GET /api/activity?limit=4000` over a 3.7h
  window (19:50Z→23:30Z), while root-causing the separate main-agent poisoned-calibration incident: `forced_precompact`
  68 · `forced_compact` 65 · **`forced_compact_ineffective` 51** · `context_compact_observed` 48, all `role=worker`.
  That is **51/65 = 78% of forced compactions producing no context reduction**, ~13.8 ineffective-force events/hr.
  Recorded here as a BASELINE for the still-open todo above ("Verify forced compaction by its EFFECT, not its
  submission" — `/plans/archive/2026_08/ao_satellite_ao_dispatch_batch12_2026_08_09.md` todo 10, still `- [ ]`), NOT as
  evidence of a regression: only todo 9 (queued-message latch) has landed, so the decisive effect-verification fix has
  not been exercised yet. The figure is not directly comparable to this doc's "~3.5 wedges/hr" baseline — that counts
  WEDGES, this counts ineffective-force EVENTS — so whoever closes the re-measurement todo should state which metric
  they are reporting.
  - Contrast in the same window, same fleet: `role=main` and `role=review` used the COOPERATIVE path and succeeded —
    main `proactive_compact_guidance` 1 → `context_compact_observed` 1 (idle gate blocked only once), review
    `context_compact_observed` 16 with zero forces. The cooperative path was 100% effective on 17 compactions while the
    forced path was 22% effective on 65; that asymmetry was direct evidence for the `[OPERATOR]` ruling made 2026-08-10
    (keep main/review cooperative-first): see
    `/plans/archive/issues/ao_main_review_force_compact_idle_gate_unreachable_2026_08_09.md` and
    `/codex/04-architecture/agent-orchestrator-worker-liveness.md` § "main/review stay COOPERATIVE-first".
