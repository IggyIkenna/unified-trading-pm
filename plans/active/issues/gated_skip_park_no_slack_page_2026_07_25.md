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
status: open
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
locked_by:
locked_since:
---

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
