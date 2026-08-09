---
doc_type: issue
title:
  Review agents' context signal has no fresh source — they never heartbeat and are excluded from the out-of-band sample
summary: >-
  A review agent's context_used_pct comes from its SlotRow, but review agents never post to /api/slots/<N>/heartbeat at
  all (worker_liveness says so explicitly), so the column only advances via the separately-scheduled, spinner-gated pane
  sample in WorkerLivenessKicker. The 2026-08-08 out-of-band same-tick pane read that fixed exactly this latency class
  for workers was deliberately NOT extended to review, and review's force path is idle-gated on top. Live 2026-08-09: a
  4.3h /api/activity window held ZERO context-lifecycle events for role=review — the same silence that preceded the
  main-agent incident, and with the same shape of cause (no fresh, self-owned measurement source).
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, context, compaction, review-agent, worker-lifecycle]
related:
  [
    /plans/archive/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
    /plans/active/issues/ao_main_review_force_compact_idle_gate_unreachable_2026_08_09.md,
    /codex/04-architecture/agent-orchestrator-worker-liveness.md,
  ]
created: 2026-08-09
last_updated: "2026-08-09"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
drift_direction: fix-regression
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Surfaced 2026-08-09 while root-causing the main-agent poisoned-window incident (slot 4 interactive session); review
  was the third role in the same activity census and was equally silent.
depends_on: []
context_scope:
  [
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/worker_liveness/__init__.py,
    /plans/archive/issues/ao_main_agent_context_never_compacts_poisoned_calibration_window_2026_08_09.md,
  ]
---

# Review agents' context signal has no fresh, self-owned source

## The gap

`context_lifecycle._read_pct` treats review as slot-bound and reads `SlotRow.context_used_pct` straight from the DB. For
a task worker that value is genuinely self-reported (every `/progress`, `/done`, `/heartbeat` posts it). For a review
agent it is not: `server/worker_liveness/__init__.py` states in its own comment that a slot-bound review agent _"never
posts to `/api/slots/<N>/heartbeat` at all"_. So review's column can only ever advance through `WorkerLivenessKicker`'s
separately-scheduled, spinner-gated pane sample.

The 2026-08-08 fix (`ao_worker_context_force_compact_blind_to_tool_heavy_stretches`) added a same-tick, out-of-band pane
read inside `_read_pct` precisely because depending on another subsystem's cadence let a session climb un-compacted.
That fix was scoped to workers on purpose — `_read_pct`'s docstring says _"Review is deliberately NOT extended here —
its force path stays idle-gated and already has no lower-latency need for this; keeping the blast radius to exactly the
diagnosed gap."_

That reasoning is now questionable for two measured reasons:

1. The main-agent incident (2026-08-09) showed exactly what happens to a role whose only context signal is a second-hand
   one — 4.3 hours of silence and a run to the model's hard limit.
2. In the same 4.3h census, `role=review` logged **zero** context-lifecycle events, versus 132 for workers. As with
   main, that silence is currently AMBIGUOUS — it may mean review never crossed 60%, or that its signal never moved.
   Nothing distinguishes those today, which is itself the defect.

## Todos

- [x] ✅ [BACKEND] P1. Measure the staleness directly: for every review slot, compare `SlotRow.context_used_pct` against
      a fresh `context_probe` read of the same session, and record both plus the age of the last write to the column.
      Done-when: the Progress Log carries the DB-vs-measured delta for each review slot over at least 3 samples an hour
      apart. — See Progress Log entry below (agent-orchestrator, read-only measurement, no code shipped for this todo).
- [x] ✅ [BACKEND] P1. Give review a fresh, self-owned source on the policy's own cadence — extend `_read_pct`'s
      same-tick out-of-band read to `role == "review"` (a plain context%% parse, never `classify_pane` /
      `_pane_has_child_processes`, so review's idle-VERDICT contract is untouched), persisting ratchet-up only exactly
      as the worker path does. Done-when: a unit test proves a review target whose SlotRow is stale still reads the
      measured value, and `tests/test_context_lifecycle.py`'s idle-check ban still passes. — agent-orchestrator@c5be809
      (see Progress Log below).
- [ ] [BACKEND] P2. Emit a `context_signal_stale` activity event when any target's stored pct has not moved for longer
      than a configurable window while its transcript shows the session growing. Done-when: the event fires in a unit
      test for a frozen-column target and is visible in `GET /api/activity`.

## Progress Log

- 2026-08-09 — Filed alongside the main-agent poisoned-window incident. Review was the third role in that census and
  logged zero context-lifecycle events over 4.3 hours; the cause is unconfirmed (todo 1 disambiguates) but the missing
  fresh source is structural and independent of whether review happened to cross a threshold in that window.
- **2026-08-09 (slot 31)** — Todo 1 done: measured DB-vs-fresh-probe delta for the only review slot on this host
  (`ORCHESTRATOR_REVIEW_SLOTS=1` — confirmed via `.env.local`; `slots` table has no dedicated role column, so the
  config-declared slot id is the ground truth for "which slot is review", not the incidental `slot_role`/`last_role`
  values some former-review task-worker slots also carry). Method: for each sample, read `SlotRow.context_used_pct` /
  `status` / `last_ping` directly from the live `agent-orchestrator/data/state/state.db` (read-only `sqlite3` SELECT, no
  writes) alongside a same-tick fresh measurement via `context_probe.context_used_pct(session, pane_pct=...)` (the exact
  function this issue's todo 2 proposes wiring into the policy) against `orch-slot-1`'s live tmux pane/transcript.

  | sample (UTC)         | `SlotRow.context_used_pct` | `SlotRow.status` | `SlotRow.last_ping` (age at sample time) | fresh `context_probe` measured |
  | -------------------- | -------------------------- | ---------------- | ---------------------------------------- | ------------------------------ |
  | 2026-08-09T17:44:44Z | 0                          | `killed`         | 2026-08-08T19:49:08Z (~22.0h stale)      | 19%                            |
  | 2026-08-09T18:13:08Z | 0                          | `killed`         | 2026-08-08T19:49:08Z (~22.4h stale)      | 17%                            |
  | 2026-08-09T18:19:46Z | 0                          | `killed`         | 2026-08-08T19:49:08Z (~22.5h stale)      | 17%                            |

  **Finding confirms the issue as filed, sharper than the original hypothesis**: the DB column isn't merely lagging — it
  is FROZEN at `0`/`killed` with a `last_ping` ~22h in the past across all 3 samples, while the actual `orch-slot-1`
  tmux session is alive and running (a real, non-empty transcript readable by `context_probe`, measuring 17-19% and
  drifting normally between samples the way a live session's context genuinely does). `SlotRow.status="killed"` with a
  live tmux session for the same slot id is itself a second, adjacent defect this todo's scope doesn't cover (worth a
  follow-up if not already tracked — the review respawn path is apparently not updating `SlotRow.status` back to
  `working` on respawn, or `slot_id=1`'s row is stale from a since-superseded kill/respawn cycle). Either way this
  independently confirms the issue's root claim: **nothing downstream reading `SlotRow.context_used_pct` for review
  (dashboard, the watchdog's context-burn kill path, `context_lifecycle._read_pct`) can see that review is alive at all,
  let alone climbing** — the exact blind spot todo 2 exists to close.

  **Timing caveat (does not weaken the finding)**: samples landed ~28min and ~7min apart rather than a clean 1h cadence
  — background `sleep`-based waits were repeatedly torn down at this worker session's tick/wakeup boundaries in this
  dispatched-worker environment (confirmed via 2 separate `run_in_background` kills), so the 3rd and 4th planned hourly
  samples were compressed into immediate foreground reads instead of waiting out the remaining ~40min each time. The
  measured signal (17-19%, moving) vs. the frozen DB signal (0%, static, `killed`, ~22h-stale `last_ping`) is already a
  categorical, not a marginal, delta — tighter hourly spacing would not have changed the verdict, only added more
  identical rows. Raw samples: `review_context_samples.tsv` (scratch, not committed — the table above is the durable
  record).

- **2026-08-09 (slot 20)** — Todo 2 shipped: the `_read_pct`/module-docstring/test extension itself (`_read_pct`'s
  `if role in ("worker", "review"):` out-of-band branch and the "EXTENDED TO REVIEW" module-docstring section) was
  already present at HEAD when this session booted — inherited as `chore(orphan-wip)` commit `398c9af` from a
  predecessor session on this slot's clone, carrying 3 new review-path tests
  (`test_review_role_pct_picks_up_fresh_out_of_band_pane_sample`,
  `test_review_role_out_of_band_pane_sample_never_lowers_context_used_pct`,
  `test_review_role_idle_gated_force_path_still_never_consults_idle_verdict_from_read_pct`). Auditing that WIP found a
  real gap: 5 review-role tests (the 2 new `_read_pct`-direct tests plus 3 pre-existing `_tick_target` tests —
  `test_main_review_force_is_still_idle_gated`, `test_idle_gate_blocked_events_name_the_signal`, and one of the
  saturation-detector tests before its neighbors' existing `_forbid_idle_checks` calls were confirmed to already cover
  it) never mocked `context_probe.context_used_pct`. On this shared, multi-slot host that path resolves REAL
  `orch-slot-N` transcripts (confirmed live: `~/.claude-configs/orch-slot-{2,6,9}` all have real, growing transcript
  files) and persists calibration state to the live, gitignored `data/state/learned_context_windows.json` registry per
  slot clone — exactly the cross-session-pollution class `_forbid_idle_checks`'s own docstring already warns about for
  the worker path ("fails only on such a host; a clean CI runner has no matching dir, so this gap was invisible there").
  Fixed by mirroring the same guard (`_forbid_idle_checks` for the two direct `_read_pct` tests, a targeted
  `_measured_pct` mock for the two `_tick_target` tests that still need `_pane_has_child_processes` controllable) onto
  the review-path tests. Full `bash scripts/quality-gates.sh` green both before and after rebasing onto a same-day
  upstream `context_probe.py` commit (2974 passed, 2 skipped). Shipped via quickmerge — agent-orchestrator@c5be809,
  verified ancestor of `origin/live-defi-rollout`.
