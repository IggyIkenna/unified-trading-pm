---
doc_type: issue
title: >-
  A worker self-parking via /skip-current-task {"reason_code":"GATED"} never pages Slack — invisible in the UI/alerts
  channel until the operator happens to notice the task sitting queued
summary: >-
  A worker slot that hits a genuinely-blocking condition it cannot resolve itself (e.g. expired credentials needed to
  execute a required action) calls `/skip-current-task {"reason_code": "GATED"}` rather than the formal `/blocked`
  question flow. This correctly parks the task (`task_auto_parked` activity event, `condition: auto_unpark__<task_id>`)
  but never triggers a Slack notification — unlike the genuine `/blocked` question flow (`POST
  /api/slots/{slot_id}/blocked` -> `ss.add_blocked` -> pages per `/codex/04-architecture/agent-orchestrator-
  alerting.md`'s "worker BLOCKED questions page" rule). The operator has no visibility into a GATED park until they
  happen to notice the task sitting queued in the dashboard. Confirmed via a fresh sub-agent investigation this session:
  the GATED skip-park code path never calls anything in `server/notifications/slack.py`, and this is not offset by the
  separate `_alert_unanswered_operator_gated_blocks` mechanism in `server/bootstrap.py` (that one pages for
  `[OPERATOR]`-tagged BACKLOG todos synced from a plan file — a structurally different condition from a live worker
  calling `/skip-current-task` mid-task).
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [agent-orchestrator, alerting, slack, gated, skip-current-task, auto-park, observability]
related:
  [
    /codex/04-architecture/agent-orchestrator-alerting.md,
    /plans/active/issues/orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md,
  ]
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.2
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
source: >-
  Operator noticed a GATED-parked task (blocked on expired gcloud credentials the worker couldn't fix itself, see
  orchestrator_gcloud_active_account_wif_poisoning_2026_07_25.md) with no corresponding Slack alert, and asked why —
  investigated via a dispatched sub-agent this session (full read of the GATED skip-park handler, the genuine /blocked
  flow, server/bootstrap.py's _alert_unanswered_operator_gated_blocks, and
  /codex/04-architecture/agent-orchestrator-alerting.md).
resolved_by:
  agent-orchestrator@fd749e3b6 (P2, with 4+ named regression tests); P3 audit delegated to
  ao_satellite_ao_dispatch_batch1_2026_07_26.md
locked_by:
locked_since:
---

> **🟢 RESOLVED 2026-07-25 -- both todos verified done/delegated. Archived per issue-doc-lifecycle.**

# GATED skip-parks are silent — no Slack page, unlike the formal /blocked flow

## Confirmed via investigation this session

- The `/skip-current-task` handler's `reason_code == "GATED"` path logs `task_auto_parked` (activity log only) and never
  calls anything in `server/notifications/slack.py` — confirmed by reading the full handler, not just grepping.
- This is a real gap, not a deliberate design choice found in any comment or commit message explaining it.
- `server/bootstrap.py::_alert_unanswered_operator_gated_blocks` (the mechanism that DOES page, for `[OPERATOR]`-tagged
  plan todos synced into the blocked-queue as `BLK-op-*` rows) is a SEPARATE code path keyed off backlog-sync, not off a
  live worker's `/skip-current-task` call — it does not cover this condition either.
- The genuine `/blocked` question flow (`POST /api/slots/{slot_id}/blocked`) correctly pages via `ss.add_blocked` —
  confirmed working end-to-end this session (a real `/blocked` question was asked, answered by "main" via Slack within a
  minute, per a live Slack thread the operator shared).

## Recommendation (not implemented — investigation + recommendation only)

Add a `notify_task_auto_parked(task_id, reason_code, skip_count, condition)` function to
`server/notifications/slack.py`, mirroring the existing `notify_operator_gated_blocked` pattern (header + task/reason/
skip_count fields + a "Respond" deep-link pointing at the dashboard, or the literal
`POST /api/prerequisites/{condition}` unpark hint already computed at park time). Call it from wherever
`task_auto_parked` is logged (`server/auto_park.py`, right after the `ss.log_activity(...)` call for the park event).

**Do NOT page on every GATED/BLOCKED/PARKED skip indiscriminately** — only at the actual park-escalation point,
consistent with the existing `notify_watchdog_kill` cap-hit-only precedent, and mindful of a pre-existing noise concern
(117/day) that motivated the cooldown store already in place for other alert classes. A GATED park should page once when
it happens, and get a "resolved" bookend when the condition clears (`auto_unpark` fires or the task is manually
completed) — mirroring the existing "every actionable alert gets a ✅ CLOSE bookend" convention.

## Todos

- [x] ✅ [BACKEND] P2. Implement `notify_task_auto_parked` + wire it into the GATED skip-park path per the
      recommendation above. Add a paired "RESOLVED" notification when the park condition clears (auto-unpark fires, or
      the underlying task completes/is cancelled while parked). **Done when**: a unit test simulates a GATED skip-park
      and asserts the Slack notify function is called exactly once (not once per tick/poll), and a simulated auto-unpark
      asserts a resolved/close notification fires; `quality-gates.sh` green. — **DONE** `agent-orchestrator@fd749e3b6`
      (2026-07-25 19:42:39Z, "feat(dashboard): surface auto-parked tasks in health strip + Slack alert on park/unpark").
      **Verified 2026-07-26 (/plan-reconcile ao)** by reading the shipped code + tests, not by grep alone: the call
      chain is live end-to-end — `server/routes/slots_ops.py:677` (`/skip-current-task`, reason_code one of
      BLOCKED/PARKED/GATED) → `auto_park.maybe_auto_park(...)` → `server/auto_park.py:103` `notify_task_auto_parked`
      (immediately after the `ss.log_activity` park event, exactly where this doc's Recommendation said to put it); the
      RESOLVED half is `server/auto_park.py:147` `notify_task_auto_unparked`. Tests:
      `tests/test_auto_park.py::test_park_fires_slack_notify_exactly_once` (`assert_called_once` + asserts
      `reason_code`/`skip_count`/`condition` kwargs), `::test_repeat_skip_past_threshold_does_not_re_notify` (no re-page
      per tick), `::test_unpark_fires_resolved_notify_exactly_once`, and a park-survives-a-Slack-outage test, plus 6
      rendering tests in `tests/test_slack_notifications.py`. The doc's **Notes** item (wire
      `BacklogSummary.auto_parked` as a UI-visible counter) also landed in the same commit — see its subject line.
- [x] [BACKEND] P3. Audit whether any OTHER `reason_code` values passed to `/skip-current-task` have the same silent gap
      (this investigation was scoped to `GATED` specifically, prompted by one live incident — confirm the finding
      generalizes or is GATED-specific before assuming full coverage). — already covered by
      plans/active/ao_satellite_ao_dispatch_batch1_2026_07_26.md (see that doc for execution).

## Notes

Also worth checking (not yet done): whether the dashboard's `BacklogSummary.auto_parked` field (a separately-noticed
dead/unused TS type field, unrelated root cause) should be wired up as a UI-visible counter alongside the Slack fix, so
an operator glancing at the dashboard sees parked-task count even without reading Slack.

## Progress Log

- **2026-08-01 — Todo 2's audit executed** (via `ao_satellite_ao_dispatch_batch1_2026_07_26.md`, AUDIT-ONLY, no code
  changed). `SkipCurrentTaskRequest.reason_code` (`server/models/slots.py:116`) is a closed 4-value
  `Literal["BLOCKED", "PARKED", "GATED", "OTHER"]` — exhaustive, no other value can reach `/skip-current-task`.
  `auto_park.maybe_auto_park` (`server/auto_park.py:50`) has exactly one call site in production code
  (`server/routes/slots_ops.py:816`), fed directly from that field. Per-code table:

  | `reason_code` | Reaches durable park?                                                                                         | Pages Slack on park?                                                                                                             |
  | ------------- | ------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
  | `BLOCKED`     | YES — in `_ESCALATING_REASON_CODES`, escalates past `dispatch_cooldown_auto_park_skip_threshold` skips        | YES — `_park_task` (the one park call site) calls `notify_task_auto_parked` unconditionally                                      |
  | `PARKED`      | YES — same path as `BLOCKED`                                                                                  | YES — same path as `BLOCKED`                                                                                                     |
  | `GATED`       | YES — same path as `BLOCKED`                                                                                  | YES — this doc's own fix (`agent-orchestrator@fd749e3b6`)                                                                        |
  | `OTHER`       | NO — `maybe_auto_park` returns `None` immediately (`reason_code not in _ESCALATING_REASON_CODES`, line 56-57) | N/A — never reaches the durable-park mechanism at all; stays a per-slot skip only (`slot_skips` table, visible via dashboard/DB) |

  **Verdict: the fix fully generalizes, no uncovered code found.** `_park_task` is the single call site for
  `notify_task_auto_parked` and does not branch on `reason_code` value — it treats BLOCKED/PARKED/GATED identically (the
  doc comment at `server/auto_park.py:96` cites this doc's own slug, confirming the fix was written to close the gap for
  all three, not just GATED). `OTHER` is structurally exempt — it never reaches `_park_task` at all, so it cannot
  exhibit this class of silent gap. This clears
  `/plans/active/issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md`'s GATED prerequisite
  — its implementation todo can now dispatch.
