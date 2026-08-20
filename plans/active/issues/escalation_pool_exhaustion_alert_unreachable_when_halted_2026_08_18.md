---
doc_type: issue
title:
  "escalation._maybe_alert_pool_exhaustion can never fire while is_pool_critically_exhausted() halts dispatch — the
  alert lives inside the exact code path its own halt condition skips"
summary: >-
  `server/autospawn.py:_drain_escalations` gates `escalation.retry_queued_escalations()` behind
  `if not is_pool_critically_exhausted(session):` (line ~3120-3125). `escalation._maybe_alert_pool_exhaustion` — the
  function that logs the transient "pool ceiling" INFO/WARNING and pages once on structural exhaustion
  (`server/escalation.py:1962-1965`, `:1969-2076`) — is called ONLY from inside `retry_queued_escalations`, as its
  final statement before `return dispatched`. Consequence: whenever `is_pool_critically_exhausted()` returns True,
  `retry_queued_escalations()` is skipped entirely, so `_maybe_alert_pool_exhaustion()` never runs either — the alert
  this function exists to fire is structurally unreachable in exactly the condition (pool critically exhausted) it
  exists to detect. Live-caught during a routine 3-hourly `/escalation-queue-reconcile` run (2026-08-18, dispatch
  agt-a4ff24, slot 4): 11 queued escalations sat with `attempts=0`/`dispatched_at=null` for up to ~3.7h (oldest
  `agt-29ed02`, created 03:21:37Z), while `journalctl -u orchestrator` showed zero "pool ceiling"/"POOL STRUCTURALLY
  EXHAUSTED" log lines over a 6h window despite clear corroborating evidence of real Claude-account pressure (HTTP 429
  on `sub-e-odum2default`/`sub-f-odum2default`, `weekly=99%` on `sub-g-alpavolt`) and dozens of "no headroom (Claude or
  DeepSeek) available" lines from the SEPARATE, unaffected `_drain_scheduled_jobs` path over the same window. Capacity
  self-recovered mid-run (my own scheduled dispatch landed on `sub-b-iggy2london` at 06:42:18Z) and
  `retry_queued_escalations` resumed normally — 2 of the 11 rows moved to `status=dispatched`/`attempts=1` within the
  next two ticks (RETRY_PER_TICK=2), confirming the dispatch/retry logic itself is healthy and the constants
  (`RESOLUTION_DEADLINE_MINUTES=45`/`MAX_REESCALATIONS=10`/`PAGE_AFTER_REESCALATIONS=2`/
  `RECONCILE_UNRESOLVED_WINDOW_HOURS=24`) are un-drifted — this is specifically an alerting/visibility gap, not a
  dispatch bug. Raised live to main via `BLK-94d07b76` (bounded ~2min wait, no answer — filing per the skill's
  timed-out-to-operator fallback) before filing this doc.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [escalation, escalation-watchdog, pool-exhaustion, observability, alerting-gap, ci-cd]
related: [/plans/archive/issues/escalation_watchdog_retune_and_reconcile_2026_08_07.md, /codex/04-architecture/agent-orchestrator-ci-escalation-wall-types.md]
created: 2026-08-18
author: escalation_queue_reconciler (slot 4, dispatch agt-a4ff24)
parent_epic: agent_operating_framework_master
priority: P2
# reclassified NA -> planning 2026-08-19 (na-eligibility-audit, ao tranche) — conflict-check CLEAR
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: refactor
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.16
assigned_role: backend_engineer
drift_direction: advance-code
sequential: true # todo 2 (live-verify) is explicitly gated on todo 1 (the fix) landing first
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-20
locked_since:
context_scope:
  [
    agent-orchestrator/server/escalation.py,
    agent-orchestrator/server/autospawn.py,
    /codex/04-architecture/agent-orchestrator-alerting.md,
  ]
source: >-
  Found by escalation_queue_reconciler's routine 3-hourly `/escalation-queue-reconcile` check (slot 4, dispatch
  agt-a4ff24) — Step 1's cheap check surfaced 11 queued rows well past the 45-min deadline with `attempts=0`, which
  Step 2's root-cause diagnosis traced to this structural gate/alert coupling by reading
  `server/autospawn.py:_drain_escalations`/`is_pool_critically_exhausted` and `server/escalation.py:retry_queued_escalations`/
  `_maybe_alert_pool_exhaustion` directly. Could not directly confirm `is_pool_critically_exhausted()`'s live
  minute-by-minute return value or DeepSeek's exact `account_is_usable`/`_provider_health_ok` state without deeper DB
  inspection, so a second contributing factor to tonight's specific ~3.7h stall cannot be fully ruled out — but the
  code-level gap (the alert is unreachable while halted, by construction) holds regardless of tonight's exact live
  values. Raised as `BLK-94d07b76` to main (recommended option A: file for design review, not a live 2-min fix, since
  this touches a production paging path); no answer within the bounded ~2min wait.
---

# escalation-queue-reconciler: pool-exhaustion alert can never fire while the pool-exhaustion halt is active

## What was found

**Step 1 (cheap check)**: `GET /api/escalations/active` returned 11 rows, all `status=queued`, all `dispatched_at=null`,
all `attempts=0`. Ages (vs. 2026-08-18T06:43:10Z): oldest `agt-29ed02` (market-tick-data-service,
`data_pipeline_failure`) created `03:21:37Z` (~3.7h old); 9 more rows spanning `03:27Z`-`05:42Z`; only the newest
(`agt-76461e`, created `06:37:44Z`) was within the 45-minute deadline. This is exactly Step 1's anomaly trigger
("a `queued` row's `created_at` is past ~45 min") — proceeded to Step 2.

**Step 2 (root-cause diagnosis)**:

1. **Constants un-drifted** — `server/escalation.py`: `RESOLUTION_DEADLINE_MINUTES=45` (line 2118),
   `MAX_REESCALATIONS=10` (2130), `PAGE_AFTER_REESCALATIONS=2` (2138), `RECONCILE_UNRESOLVED_WINDOW_HOURS=24` (2147) —
   all match expected values. Ruled out.
2. **`_drain_escalations()` itself is not crashing** — each of its three escalation sub-calls
   (`retry_queued_escalations`/`verify_dispatched_escalations`/`reconcile_stale_unresolved_escalations`) is wrapped in
   its own `try/except Exception: logger.exception(...)  # (continuing)`. A 6h `journalctl` search for
   `"queued-escalation retry failed"` found exactly **one** occurrence (05:01:08Z, `sqlite3.OperationalError: database
   is locked` — a single transient lock contention blip, not a sustained crash pattern). Ruled out as the primary
   cause.
3. **The actual mechanism**: `server/autospawn.py:_run_one_tick` calls `self._drain_escalations()` unconditionally
   first (before the resume pass / spawn loop). Inside `_drain_escalations` (`server/autospawn.py:~3096-3129`):

   ```python
   try:
       with session_scope() as session:
           halted = is_pool_critically_exhausted(session)
       if not halted:
           from . import escalation as _escalation
           _escalation.retry_queued_escalations()
   except Exception:
       logger.exception("AutoSpawnLoop: queued-escalation retry failed (continuing)")
   ```

   `is_pool_critically_exhausted` (`server/autospawn.py:1225-1253`) returns True only when the best Claude account's
   used-pct is `>= _CRITICAL_POOL_HEADROOM_PCT` (90) **AND** `_non_anthropic_pool_has_capacity()` (DeepSeek/other
   providers) is also False — the 2026-08-04 fix (`autospawn_pool_critical_halt_starves_deepseek`) that lets a funded
   DeepSeek pool absorb overflow instead of halting the whole fleet on Claude alone.

   `escalation.retry_queued_escalations()` (`server/escalation.py:1675-1966`) is the **only caller** of
   `escalation._maybe_alert_pool_exhaustion()` — the call sits as the function's last statement before
   `return dispatched` (line 1965: `_maybe_alert_pool_exhaustion(total_queued, dispatched)`).
   `_maybe_alert_pool_exhaustion` (`:1969-2076`) is the function that:
   - logs `"pool ceiling (transient): N escalation(s) waiting..."` on first sighting of transient ceiling exhaustion,
   - escalates that to `logger.warning("pool ceiling SUSTAINED %.1fh...")` once the condition has held
     `>= _transient_info_hours` (2.0h),
   - and pages once per episode (`slack_notify.notify_account_pool_exhausted`) on **structural** exhaustion
     (`all_accounts_unusable`).

   **The gap**: `_maybe_alert_pool_exhaustion` only ever runs as a side effect of `retry_queued_escalations` being
   invoked — which itself only happens when `not halted`, i.e. when `is_pool_critically_exhausted()` is **False**. The
   instant the pool actually IS critically exhausted (the one condition `_maybe_alert_pool_exhaustion` exists to
   surface), the code path containing it is skipped, so **the alert cannot fire in the condition it is designed to
   catch** — not the transient INFO/WARNING nudge, and not the structural PAGE.

**Corroborating evidence this window genuinely had sustained capacity pressure** (not just an idle correctness
argument): live `journalctl -u orchestrator` over the incident window showed real, repeated Claude-account exhaustion
signals — `HTTP 429` on `sub-e-odum2default` (skipped 144877s) and `sub-f-odum2default` (skipped 227677s) at 06:45:22Z,
`sub-g-alpavolt` reporting `weekly=99%` at 06:45:38Z, and "AgentKeeper: main agent capped + NO headroom account —
leaving frozen" recurring every ~3min from at least 06:01:59Z through 06:17:37Z. The **separate**
`_drain_scheduled_jobs` path logged "scheduled-job drain: na_eligibility_auditor... still deferred (no headroom
account (Claude or DeepSeek) available...)" dozens of times over the same window — that path has its own, unaffected
visibility. The escalation-specific path had none: zero `"pool ceiling"` or `"POOL STRUCTURALLY EXHAUSTED"` lines
anywhere in a 6h `journalctl` search.

**Self-recovery observed live**: my own scheduled dispatch (this very task, `agt-a4ff24`) landed on account
`sub-b-iggy2london` at 06:42:18Z, indicating capacity had returned by then. A re-check of `/api/escalations/active` at
~06:49Z showed the queue had shrunk to 9 rows (2 resolved via the pre-dispatch staleness re-probe) and **2 of the
remaining 9 had moved to `status=dispatched`/`attempts=1`** (`agt-29ed02` at `dispatched_at=06:47:25Z`, `agt-9c8949` at
`06:48:39Z`) — exactly the oldest-first, `RETRY_PER_TICK=2`-per-tick behavior the code documents. This confirms
`retry_queued_escalations`'s actual dispatch logic is healthy; the finding here is specifically the alerting/visibility
gap during the halted window, not a dispatch defect.

## Why this matters

During any future window where `is_pool_critically_exhausted()` genuinely holds True for a sustained period —
including a genuine **structural** episode (all accounts auth-failed/disabled/rate-limited, not just over
usage-pct ceilings) — queued escalations (which include `data_pipeline_failure` walls, per the data-pipeline-
correctness HARD RULE) can sit silently unserved with **zero** operator-facing signal from this specific mechanism:
no transient nudge, no sustained-WARNING, and critically, no structural PAGE. The operator would only learn about it
indirectly (via the unrelated scheduled-job-drain log line, or by noticing stale escalations manually) rather than
via the dedicated alert this function was built for.

## Recommended fix (not applied — filed for design review per BLK-94d07b76 recommendation A)

Decouple the alert check from the dispatch attempt: call `escalation.maybe_alert_pool_exhaustion(total_queued=...,
dispatched=0)` from `_drain_escalations` in the `halted` branch too (mirroring the existing reuse at
`server/autospawn.py:3091`, which already calls the same public alias from a different halted-adjacent context — see
that call site's own comment for the precedent), so the alert evaluates on every tick regardless of whether a dispatch
attempt was made. Needs care: `total_queued` must still be sourced correctly when `retry_queued_escalations` never
ran (a fresh count query), and the `dispatched=0` argument must not be conflated with "an attempt was made and
failed" vs. "no attempt was made at all" if that distinction ever becomes alert-relevant.

## Todos

- [x] [BACKEND] P2. Decouple `_maybe_alert_pool_exhaustion` from `retry_queued_escalations` so it also evaluates when
      `is_pool_critically_exhausted()` halts dispatch — see "Recommended fix" above. Add a regression test asserting
      the alert function is invoked (or an equivalent structural-exhaustion signal fires) even when the halt gate
      skips `retry_queued_escalations` entirely. Ship via quickmerge with full `quality-gates.sh` green. —
      **Found already shipped, 2026-08-20 (T5 tranche, verifying rather than re-implementing).**
      `agent-orchestrator@78a9a02c` (2026-08-19, `fix(escalation): alert on halted pool-exhaustion tick; add
      proactive worker-slot account failover`). `server/autospawn.py:_drain_escalations`'s `halted` branch now
      queries a fresh `total_queued` count and calls `_escalation.maybe_alert_pool_exhaustion(total_queued=...,
      dispatched=0)` directly — exactly the recommended fix above, and its own docstring cites this issue's slug
      verbatim. 9 regression tests confirmed passing on current code:
      `test_drain_escalations_skips_retry_but_still_verifies_when_halted`,
      `test_drain_escalations_does_not_alert_when_not_halted`,
      `test_drain_escalations_retries_normally_when_not_halted` (`tests/test_autospawn.py`) plus 6 more in
      `tests/test_escalation.py` covering the structural/transient/silent/no-headroom/sustained-ceiling cases.
- [ ] [VERIFY] P3. Once the fix lands, live-verify by checking `journalctl` across a future genuine exhaustion window
      for the "pool ceiling (transient)" INFO line firing even during a halted tick (not just during an unhalted
      one). **Still genuinely open, 2026-08-20** — this needs a real future exhaustion window's live journalctl
      output, which this pass does not have. Unit tests confirm the code path is now reachable; they do not
      substitute for the live confirmation this todo asks for.

## Progress log

- 2026-08-18 (escalation_queue_reconciler, slot 4, dispatch agt-a4ff24): Filed after Step 2 root-cause diagnosis
  during a routine 3-hourly check. Raised live to main first via `BLK-94d07b76` (recommended option A: file for
  design review); no answer within the bounded ~2min wait, filing per the skill's timed-out-to-operator fallback.
  Queue had already begun self-clearing by the time of filing (2/9 remaining rows dispatched) — no immediate operator
  action needed; this doc tracks the alerting-gap code fix only.
- **na-eligibility-audit 2026-08-19 (ao tranche)**: RECLASSIFY (whole-doc) -> `assigned_vm: planning`. Fresh (2026-08-18), root-caused, fully-scoped fix with exact call-site/mechanism citations; both todos (decouple the alert + live-verify) are bounded/deterministic, chained via `sequential: true` since todo 2 is explicitly gated on todo 1 landing. Conflict-check clear: the naming-adjacent `ao_satellite_ao_dispatch_batch21_finalize_2026_08_16.md` mention of `pool_exhaustion` refers to a DIFFERENT mechanism (DB connection pool, `orchestrator_db_pool_exhaustion_state_poll_stall_2026_07_25`), not the escalation pool-exhaustion alert this doc targets. Companion gated finalize: `escalation_pool_exhaustion_alert_unreachable_when_halted_2026_08_18_finalize_2026_08_19.md`.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
