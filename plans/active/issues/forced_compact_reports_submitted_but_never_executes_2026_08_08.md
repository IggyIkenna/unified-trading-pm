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
status: open
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
resolved_by:
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

- [ ] [BACKEND] P1. **Detect the queued-message state and do not spend the force latch on it.** Add a
      `pane_has_queued_messages()` probe to `server/tmux_spawn.py` and have `context_lifecycle`'s force path hold the
      latch un-spent until the queue drains, rather than re-sending (a second `/compact` would compact twice and lose
      context unnecessarily). Needs a new `_TargetState` field for "submitted but not yet executed". **➡️ EXTRACTED
      2026-08-09 to `ao_satellite_ao_dispatch_batch12_2026_08_09.md` todo 9 — do NOT action here.**
- [ ] [BACKEND] P1. **Verify the compaction by its EFFECT, not by its submission.** The authoritative proof a compaction
      ran is a new `compact_boundary` record in the session transcript — `server/context_probe.py` already parses these
      and exposes `stale_after_compaction`. Confirming the boundary appeared is a far stronger check than a cleared
      input box, and needs no pane parsing at all. **➡️ EXTRACTED 2026-08-09 to
      `ao_satellite_ao_dispatch_batch12_2026_08_09.md` todo 10 — do NOT action here.**
- [ ] [BACKEND] P2. **Reproduce deliberately** — submit `/compact` to a pane mid-turn and confirm it queues rather than
      executes, and that `submit_to_pane` still returns True. The mechanism above is inferred from a live pane capture
      plus five consistent ineffective forces, not from a controlled repro. **➡️ EXTRACTED 2026-08-09 to
      `ao_satellite_ao_dispatch_batch12_2026_08_09.md` todo 11 — do NOT action here.**
- [ ] [BACKEND] P3. **Re-measure the wedge rate once the above lands.** Baseline to beat, measured on the clean fleet
      after `c6e6d982a`/`9b269c0ce`: ~3.5 wedges/hr with forces distributed 62-97. Pre-measurement-fix baseline was
      ~9.7/hr with every force at 91-100.

## Codex SSOTs

- `/codex/04-architecture/agent-orchestrator-worker-liveness.md` — pane classification + inject contract

## Progress Log

- **2026-08-08 (interactive session, slot 1)**: Isolated while validating the context-measurement fix. The measurement
  fix did not cause this — it uncovered it. Mitigated in the same session by `agent-orchestrator@989592628`, which stops
  a slot with headroom from being recycled over a compaction that will not run; that is a containment, not the fix.
- **context-scout 2026-08-09**: populated context_scope (5 entries).
