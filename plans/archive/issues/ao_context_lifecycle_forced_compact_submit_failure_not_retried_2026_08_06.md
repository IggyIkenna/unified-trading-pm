---
doc_type: issue
title:
  A wedged (unsubmitted) forced /pre-compact or /compact injection in agent-orchestrator's context_lifecycle.py
  permanently disabled further force-compact attempts for the rest of a worker's un-compacted stretch — root cause of a
  slot dashboard showing context_used_pct pinned at 94% with its last real compaction 17 minutes in the past, well past
  both the 60% force threshold and the 70% cooperative-directive gate.
summary: >-
  Operator screenshot (2026-08-06 ~08:33 UTC) showed slot #14 (`cefi_tardis_derivative_ticker_historical_gap-002`)
  status WORKING, context 94%, "COMPACTIONS 51 total · 2 in last hr · last 17m ago", with the most recent message
  reading "post-compact resume: checking DERIBIT derivative_ticker GCS evidence...". The combination is contradictory on
  its face: a real compaction was DB-recorded 17 minutes prior (`CompactionRow`/`SlotRow.compactions_total`, which
  requires a genuine >=30-point self-reported `context_used_pct` drop between two pings — `state_store/slots.py`
  `COMPACTION_DROP_THRESHOLD`), yet the slot is still actively WORKING its task 17 minutes later at 94%, well past both
  the worker force-compact threshold (`context_worker_force_compact_pct`, default 60) and the cooperative
  `compact_now`/`compact_before_next` directive gate (`context_worker_compact_gate_pct`, default 70) that should have
  intervened again long before 94%.

  Root-caused by reading `agent-orchestrator/server/context_lifecycle.py::_force_compact_now` (the unconditional worker
  force-compact path, operator ruling 2026-08-05: "the guidance isn't useful if it doesn't force" —
  `ContextLifecyclePolicy._tick_worker` calls this every ~60s keeper tick, unconditionally, once a worker's
  self-reported `context_used_pct` crosses the force threshold, re-armed only by an OBSERVED compaction). The function
  injects `/pre-compact` (phase 1) then `/compact` (phase 2) via `tmux_spawn.submit_to_pane`, which returns a verified
  `bool` — `True` only when the text demonstrably left the pane's input box (submitted or consumed by an already-running
  turn), `False` when it wedges (the exact typed-but-un-submitted class documented in
  `/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md`). The bug: BOTH
  phases set their completion timestamp (`state.precompact_forced_at` / `state.forced_at`) UNCONDITIONALLY, before even
  looking at the `submitted` return value — `submitted` was captured and logged for observability (`"submitted":
  submitted` in the activity-log details) but never used to gate anything. So a single wedged injection makes the
  in-memory state machine believe that phase is DONE, and the `state.forced_at is not None` guard in `_tick_worker` then
  skips every future force attempt for the rest of the un-compacted stretch — the ONE mechanism whose entire purpose
  (per the 2026-08-05 operator ruling and the module's own docstring) is to force a compact unconditionally, silently
  stops trying after exactly one failed attempt, with no retry and no escalation. This is consistent with the
  screenshot: a real compaction landed 17 minutes ago (a successful two-phase force, or a cooperative one), the worker
  re-armed and climbed back past 60% within that window, a fresh force attempt wedged (same failure class the still-open
  slot-4 wedge issue documents), and the state machine then sat there believing it had already handled it while context
  climbed unchecked to 94% and rising.

  Distinct from both related docs: `slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md` is about
  WHY a `/compact` confirmation wedges in the first place (still open, unresolved) and is scoped to the COOPERATIVE
  guided-compact path; `context_compact_directive_did_not_fire_slot_rode_to_96pct_2026_07_27.md` (archived, resolved)
  was a missing-activity-log bug in the separate cooperative `progress_slot` directive path. This finding is a THIRD,
  independent gap: even a CORRECTLY-detected wedge (submitted=False, verified) in the FORCED tmux-injection path was
  silently swallowed by the caller's own state machine rather than triggering a retry. Fixing the confirmation-wedge
  root cause (the other issue's open item) would reduce how often this triggers, but this fix is required regardless —
  any transient injection failure (a busy pane racing the send-keys, not just a genuine CLI-level wedge) would trip the
  same permanent-disable bug.
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags:
  [agent-orchestrator, context-lifecycle, compact, force-compact, wedge, dashboard, context-tracking, worker-liveness]
related:
  [
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
    /plans/archive/issues/context_compact_directive_did_not_fire_slot_rode_to_96pct_2026_07_27.md,
    /plans/active/issues/ao_context_pct_0_for_monitor_heavy_workers_2026_07_29.md,
  ]
created: 2026-08-06
author: main (interactive session, tabs/1)
last_updated: 2026-08-06
priority: P2
parent_epic: orchestrator_master
source:
  "operator dashboard screenshot (slot 14, cefi_tardis_derivative_ticker_historical_gap-002, context 94%, last
  compaction 17m ago) + direct ask to root-cause and fix, investigated read-then-fix in an interactive session,
  2026-08-06 ~08:35-09:15 UTC"
execution_scope: local-only
drift_direction: advance-code
depends_on: []
assigned_vm: NA
resolved_by: agent-orchestrator@b94f4f8
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md,
    /plans/archive/issues/context_compact_directive_did_not_fire_slot_rode_to_96pct_2026_07_27.md,
    agent-orchestrator/server/context_lifecycle.py,
    agent-orchestrator/server/tmux_spawn.py,
    agent-orchestrator/server/state_store/slots.py,
    agent-orchestrator/tests/test_context_lifecycle.py,
  ]
---

> **🟢 ARCHIVED 2026-08-06** — status=resolved (ACKED-INTO-CODE), 0 open todos. Fixed + shipped
> `agent-orchestrator@b94f4f8` (verified landed on `origin/live-defi-rollout` via `git merge-base --is-ancestor`, not
> just quickmerge's own message), full `quality-gates.sh` green (2493 passed, 4 skipped, 0 failed), CI green
> (`quality-gates-v2` + Deploy Dashboard both success on the shipping commit). **Live-verified on the orchestrator VM**
> (`i-0c9b283b31d6b5ca7`, read-only AWS SSM check): the running `orchestrator` systemd service's checkout HEAD
> (`de73f931b80fddb9dda49c4a860033ac5b0ae3ea`, self-pulled + restarted 2026-08-06 09:23:22 UTC) is a descendant of
> `b94f4f8` — the fix is live in production, not just merged. Archived per
> `/codex/11-project-management/issue-doc-lifecycle.md`'s archive-on-resolve rule.

# AO forced-compact injection: a wedged submit permanently disables further force attempts, letting context climb unchecked past every threshold

## Evidence

- Operator screenshot, slot 14, 2026-08-06 ~08:33 UTC: status WORKING, plan
  `cefi_tardis_derivative_ticker_historical_gap-002`, context **94%**, "COMPACTIONS 51 total · 2 in last hr · last 17m
  ago", last message "post-compact resume: checking DERIBIT derivative_ticker GCS evidence; BINANCE-FUTURES 508 and
  BYBIT 444 already confirmed; VM cefi-fwd-20260806-065837 running".
- `server/state_store/slots.py::update_slot_ping` (DB-persisted compaction detection, `COMPACTION_DROP_THRESHOLD = 30`):
  `slot.context_used_pct` is overwritten on every self-reported ping regardless of direction — a compaction is only ever
  DETECTED (`compactions_total += 1`, a new `CompactionRow`), never assumed; the "17m ago" figure is a real recorded
  drop.
- `server/context_lifecycle.py::_tick_worker` (worker force path, unconditional per the 2026-08-05 operator ruling in
  the module docstring): fires `_force_compact_now` on every ~60s keeper tick once
  `pct >= context_worker_force_compact_pct` (default 60) AND `state.forced_at is None`; re-armed only by an
  in-memory-observed compaction (`_COMPACTION_DROP_PCT = 25` drop between ticks).
- `server/context_lifecycle.py::_force_compact_now` (pre-fix): both `state.precompact_forced_at = now` and
  `state.forced_at = now` were set **unconditionally**, immediately after computing
  `submitted = tmux_spawn.submit_to_pane(...)` — the boolean was logged (`details={"submitted": submitted, ...}`) but
  never branched on.
- `server/tmux_spawn.py::submit_to_pane` docstring: "Returns True when the input demonstrably left the input box
  (submitted or consumed by an already-running turn)" — i.e. `False` is a real, verified negative, not a
  transient/unreliable signal; the caller ignoring it is the bug, not the signal itself.
- `tests/test_context_lifecycle.py`'s `_mock_submit` helper hard-coded `return True` in every pre-existing test — no
  test exercised the `submitted=False` path, so the gap had zero regression coverage.
- Grepped every other consumer of a `forced_precompact`/`forced_compact` activity-log `submitted` field: none exists.
  Contrast with the separate frozen-pane KICKER mechanism (`worker_liveness/__init__.py`), which DOES use its own
  verified-submit signal (`kick_submitted`/`submit_verified`) to drive retry/escalation — the asymmetry confirms this is
  a real gap in `context_lifecycle.py` specifically, not a deliberate design choice.

## Fix (shipped this session)

`_force_compact_now` now only advances `state.precompact_forced_at` / `state.forced_at` when `submit_to_pane` returns
`True`. On `False` it logs a distinct `forced_precompact_submit_failed` / `forced_compact_submit_failed` activity event
and returns with the phase timestamp unset, so the next ~60s keeper tick retries the SAME phase — cheap (a couple of
`tmux send-keys` calls), and it composes with the existing frozen-pane kicker/watchdog escalation for a pane that is
genuinely wedged rather than just transiently busy at the moment of injection.

Added two regression tests (`test_worker_wedged_precompact_submit_retries_next_tick_not_abandoned`,
`test_worker_wedged_compact_submit_retries_and_defers_directive_flag`) asserting: (a) a failed submit does not advance
the phase timestamp and a later successful submit does; (b) `SlotRow.context_directive_issued` (what
`worker_liveness_watchdog._context_burn_kill_ready` gates its kill decision on) stays `False` until phase 2 is verified
submitted, not merely attempted.

## Todos

- [x] ✅ [ENGINEER] P2. Fix `_force_compact_now` to gate phase-timestamp advancement on a verified `submit_to_pane`
      result, retrying on the next tick instead of permanently disabling the force mechanism. —
      `agent-orchestrator/server/context_lifecycle.py`.
- [x] ✅ [ENGINEER] P2. Add regression coverage for the wedged-submit-retries case (both phases), including the
      `context_directive_issued` deferral. — `agent-orchestrator/tests/test_context_lifecycle.py`.
- [x] ✅ [ENGINEER] P1. Unrelated pre-existing QG-red hit while verifying this fix (RULES.md §4b protocol: stashed,
      re-ran on clean HEAD, byte-identical failure) —
      `tests/test_dirty_state_resolution.py::TestDeadQuarantineArtifactAutoHeal::test_resolve_dirty_state_returns_clean_when_only_a_dead_artifact_present`
      failed with a non-fast-forward `git push` rejection, but only inside the full suite, never in isolation. Root
      cause: `_init_repo_with_remote`'s bare-repo path is `slot_dir.parent / f"{name}.git"` — safe (per-test-unique)
      whenever callers nest `slot_dir` under `tmp_path` (the pattern ~10 other tests in the file use), but TWO tests in
      `TestDeadQuarantineArtifactAutoHeal` passed `tmp_path` directly AND both reused the literal name
      "instruments-service", so their bare repos collided at the pytest-SESSION-shared tmp root — whichever ran second
      got a non-fast-forward rejection against the first one's leftover ref. Fixed by nesting both under a per-test
      `slot_dir = tmp_path / "slot10"`, matching the file's own established isolation pattern. This blocked the
      `--agent` quickmerge sentinel for ALL agent-orchestrator shipping, not just this fix — a fleet-wide blocker, same
      class as the archived `agent_orchestrator_qg_red_test_autospawn_magicmock_datetime_2026_07_30.md` precedent. —
      `agent-orchestrator/tests/test_dirty_state_resolution.py`.
- [ ] [ENGINEER] P3. The still-open
      `/plans/active/issues/slot_recurring_wedge_at_context_pct_75_compact_confirmation_2026_07_25.md` item 1 (make the
      confirmation auto-submit / self-drive past a typed-but-unsubmitted `/compact`) remains the right fix for WHY
      submissions wedge in the first place; this issue's fix only ensures a wedge is retried rather than silently
      permanent. Not duplicating that work here — cross-referenced so a fix there doesn't need to rediscover this one's
      context.

## Progress Log

- **2026-08-06 (this session)**: Diagnosed + fixed + regression-tested (2 new tests) + fixed the unrelated pre-existing
  QG-red test-isolation bug hit while verifying (RULES.md §4b protocol followed: confirmed byte-identical on a clean
  stashed tree before fixing it too). Full `bash scripts/quality-gates.sh` green (2493 passed, 4 skipped, 0 failed).
  Shipped `agent-orchestrator@b94f4f8` via `quickmerge.sh --agent`, verified landed on `origin/live-defi-rollout`
  (`git merge-base --is-ancestor` check passed, not just quickmerge's own "✅ Landed" message). CI verification and
  live-behavior confirmation on the orchestrator VM next.
