---
doc_type: codex-ssot
title: Agent-Orchestrator Alerting — actionable-only channel + daily digest
summary:
  The contract for what reaches the agent-orchestrator-alerts Slack channel. Automatic backend lifecycle events
  (plan_health / escalation dispatches, auto-respawns, recoveries) are NOT paged — they log to AO logs + the GCS ledger
  and are rolled into one daily digest. Only operator-actionable events page (failures, worker BLOCKED questions,
  unresolved escalations). Standing conditions dedup by state-transition (fire on change / RESOLVED / a re-remind
  interval), never every tick.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer, admin]
tags: [alerts, slack, agent-orchestrator, observability, dedup, notifications]
related: [/codex/04-architecture/autonomous-recovery-matrix.md, /codex/04-architecture/runtime-deployment-topology.md]
created: 2026-07-13
authoritative_for: [agent-orchestrator Slack alert routing, daily-summary digest, git-health guard dedup]
referenced_by:
owner:
last_reviewed: 2026-08-09
code_refs:
  - agent-orchestrator/server/notifications/slack.py
  - agent-orchestrator/server/daily_summary.py
  - agent-orchestrator/scripts/fleet-git-health-guard.sh
  - agent-orchestrator/server/context_lifecycle.py
---

# Agent-Orchestrator Alerting

The `agent-orchestrator-alerts` Slack channel is **actionable-only**: a message there means _a human should look_.
Everything else lives in AO logs, the GCS alert ledger (`GET /api/alerts`), and the daily digest. This is the standing
contract established by `alert_channel_cleanup_2026_07_13` (a 7-day audit found 1,598 messages / 40 shapes, top-4 = 74%,
of which ~87% were automatic lifecycle churn or one unsuppressed repeat).

## What does NOT page (logged + digested, never Slack)

Automatic backend lifecycle events — the orchestrator handled them, no human is needed:

- `notify_plan_health_dispatched`, `notify_escalation_dispatched` — periodic/automatic dispatch **success**.
- `notify_agent_stuck_respawned` — an auto-respawn (self-healing).
- `notify_slot_recovered`, `notify_spawn_recovered` — recovery/closure bookends. (`notify_escalation_resolved` is now
  conditional — it PAGES a ✅ closure when the wall previously paged, else logs; see "Alert-lifecycle closure
  bookends".)
- `notify_spawn_failed` (fired via `autospawn.alert_spawn_failed` on the AutoSpawn + escalation paths) — a hard spawn
  failure (session died before the boot paste). **AutoSpawn retries and the watchdog self-heal**, so it is not per-event
  actionable (operator 2026-07-13). It keeps its GCS-ledger persist (so `GET /api/alerts` still records it) and is
  counted in the digest via the `autospawn_failed` / `escalation_dispatch_failed` activity events the callers write; a
  _persistent_ inability to spawn shows as a rising count there. **If the spawn failure is actually a dead token**, the
  definitive-code classification below turns it into the `notify_account_auth_failed` page — so a genuine credential
  failure is never buried in the summary.

- `notify_agent_stuck_escalation` ("Auto-respawn FAILED"), `notify_autospawn_flap`, `notify_stash_on_done` — automatic
  self-healing / lifecycle events (a respawn a guard skipped, an AutoSpawn retry loop backing off, a worker stashing WIP
  to pass the /done gate). All log + digest, none page (operator 2026-07-13 full audit). The one respawn/quarantine case
  that still pages is a slot actively **starving** escalation dispatch (`notify_slot_quarantined`). **Verified live
  2026-07-25** (`plans/archive/2026_07/ao_fleet_throughput_incident_2026_07_25.md` — 3 independent fires, journal +
  Slack-200 confirmed): the starvation condition was `escalation.count_queued_walls() > 0` — this counted only queued
  CI-escalation walls, NOT the (usually much larger) plain backlog-task queue, so a quarantine with backlog tasks queued
  but zero escalation walls queued would have silently paged the quiet path instead. **Fixed
  `agent-orchestrator@9c73579`**: the condition is now `count_queued_walls() > 0 or count_queued_backlog_tasks() > 0`,
  and `notify_slot_quarantined`'s Slack copy names whichever queue(s) triggered it — see
  `plans/archive/issues/branch_quarantine_alert_blind_to_backlog_queue_2026_07_25.md`.
- **A backward-HEAD discard already preserved on `wip-preserve/orchestrator-slot-<N>-<sha>`** — `HeadBackwardCanary`
  (2026-07-27 fix): the orphan-wip inherit flow (`_orphan.py`) always pushes a discarded commit to that ref BEFORE its
  own `git checkout -B` realign, so the content is safe forever, not merely reflog-recoverable — this is the routine
  by-design outcome of a task-less slot handoff, not a data-loss event. Logged INFO only
  (`HeadBackwardCanary.tick_once`'s `preserved_hits`); `notify_head_backward_dataloss` is only ever called with the
  remaining `real_hits` (no matching preserve ref found) — see the "DOES page" entry below.

Each of these calls `logger.info(...)` (the "D11 downgrade" convention) instead of `slack._post(...)`. Their events are
recorded in the DB **activity log** (`log_activity`) by the callers, which is what the digest reads.

## What DOES page (operator-actionable)

- **Failures** — `notify_plan_health_dispatch_failed` (deduped 1h; the plan_health do_spawn failure branch was
  previously Slack-silent); **unresolved / re-escalation-cap escalations** (`_mark_unresolved_and_maybe_reescalate`,
  CRITICAL — a stuck wall past deadline). (Generic spawn failures are NOT here — see the summary-only list above.)
- **Dead/expired token** — `notify_account_auth_failed` (CRITICAL, re-mint action). This is the one auth alert the
  operator cares about; see the code-based classification below.
- **Worker BLOCKED questions** — `notify_slot_blocked` (a worker asks the main/review agent or the operator). Renders
  the structured `question` + `options` (bulleted) + `recommendation` on their own full-width sections.
- **Account auth RECOVERED** — `notify_account_auth_recovered` (kept a page **by design**: an account returning to
  rotation is operationally significant, not churn; test-locked by `test_account_auth_recovered_still_pages`).
- **The digest job failing** — `notify_daily_summary_failed` (a dead digest must not be silent).
- **Silent backward-HEAD data-loss** — `notify_head_backward_dataloss` (CRITICAL — a slot repo's committed-but-unpushed
  commit was discarded by an out-of-band `branch: Reset to origin` and is now recoverable only via reflog; the page
  carries the per-clone `git cherry-pick <sha>` recovery. Fired by the `HeadBackwardCanary`
  (`server/head_backward_canary.py`), first-tick-baselined + persisted-seen deduped so it pages each new loss exactly
  once; the detection sister to the `slot11_silent_branch_reset_data_loss` realign-guard fix). **CALLER-FILTERED
  (2026-07-27 follow-up to `agent_orchestrator_alert_channel_cleanup_2026_07_13`)**: `HeadBackwardCanary` checks each
  discarded SHA for a matching `wip-preserve/orchestrator-slot-<N>-<sha>` ref on origin BEFORE calling this notifier —
  the orphan-wip inherit flow (`worktree_clean_check/_orphan.py`) always pushes there before its own realign, so that
  case is safe forever, not merely reflog-recoverable, and is logged INFO only (see "does NOT page" above). Measured
  live 2026-07-27: ~80% of all backward-HEAD discards fleet-wide are this benign preserve-then-realign case; only the
  ~20% with no matching preserve ref (a genuinely wedged/misclassified worker) still page here.
- **Alert-lifecycle closure bookends** — an actionable alert's CLOSE is posted in-channel so the operator can tell an
  OPEN page from a resolved one (see the dedicated section below).

**Rule: dispatch/lifecycle SUCCESS is silent; the corresponding FAILURE pages.** Removing a success ping must never
blind the operator to that job failing.

## Alert-lifecycle closure bookends — every actionable OPEN gets a visible CLOSE (operator 2026-07-18)

The actionable-only contract kept the channel from drowning in lifecycle churn, but it left the _inverse_ gap: an alert
PAGED its **open** and then closed silently, so scrolling the channel you couldn't tell a resolved incident from a
still-open one. Two concrete misses the operator hit: a `:octagonal_sign:` BLOCKED question that was answered (or
auto-resolved by the reconciliation sweep) vanished from the dashboard (`unanswered_only`) with **no Slack signal at
all**; and a `:rotating_light: git RED` re-remind looked byte-identical to the first page, so a persisting episode read
as a fresh problem. The fix: **post a ✅ closure bookend for every actionable alert that previously paged**, and make
re-reminders self-identifying. Webhook-only correlation (Slack here is an incoming webhook — no bot token / Web API, so
no true threading): each bookend carries the original page's **opened-at timestamp + stable identity** (slot / repo+wall
/ `blocked_id`) so the operator eyeballs which OPEN it closes.

- **BLOCKED question answered / auto-resolved** — `notify_slot_blocked_answered` (PAGE, ✅). Fired from BOTH close
  paths: the human/main-agent answer (`routes/backlog.py::answer_blocked_endpoint`, FINAL answers only — a `partial`
  keeps the row open + re-paging, so no bookend) and the auto reconciliation-sweep (`blocked_reconcile.reconcile_once`,
  `auto=True` → "auto-resolved by"). Names WHO answered + the answer + a "closes the BLOCKED question opened `<ts>`
  (`<blocked_id>`)" line. Every BLOCKED question pages on creation, so its close is symmetric — not churn.
- **Git-staleness re-remind + RECOVERED** — `notify_git_staleness_red(is_reminder=…, opened_at=…, episode_min=…)`: the
  4h re-remind renders "Slot N git **STILL RED — reminder**" + an "Open since `<ts>` (red `<N>`m)" field so a persisting
  episode is visually distinct from a first page. `notify_git_staleness_resolved(opened_at=…)` adds a "closes the RED
  alert opened `<ts>`" line. Caller `worker_liveness/_git_alerts.py` (`_staleness_red_since` is the opened-at source).
- **Escalation / CI-wall resolved** — `notify_escalation_resolved(paged=…)`: a closure bookend PAGES **only when the
  wall previously paged** an UNRESOLVED / ABANDONED alert (detected by `_clear_unresolved_page_cooldown` returning
  `True` — a live unresolved-page cooldown means it paged). A resolution that never paged an OPEN stays log-only (a
  closure with no matching open is churn) — this preserves the WS-A treatment for the common auto-dispatch→auto-resolve
  path. Test-locked by `test_escalation_resolved_pages_only_when_it_previously_paged`.

## Complete pager audit (2026-07-13) — the SSOT for every `slack._post` notifier

Every notifier that _can_ post to `#agent-orchestrator-alerts`, and its verdict. **Before adding or restoring a page,
check it against this table** — the default for any automatic/self-healing/lifecycle event is summary-only.

| Notifier                                                                                                                                                                                                                                                                                                                                                                                                          | Verdict                                  | Why                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `notify_slot_blocked`                                                                                                                                                                                                                                                                                                                                                                                             | **PAGE**                                 | worker asks the operator/main agent a question                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| `notify_operator_gated_blocked`                                                                                                                                                                                                                                                                                                                                                                                   | **PAGE**                                 | an operator decision is required                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `notify_account_auth_failed`                                                                                                                                                                                                                                                                                                                                                                                      | **PAGE**                                 | dead/expired token (code-based 401/403) — re-mint                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `notify_account_auth_recovered`                                                                                                                                                                                                                                                                                                                                                                                   | **PAGE**                                 | account back in rotation — operationally significant (test-locked)                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `notify_setup_token_expiring`                                                                                                                                                                                                                                                                                                                                                                                     | **PAGE**                                 | proactive 30d/7d expiry — act before it dies                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| `notify_all_accounts_unusable`                                                                                                                                                                                                                                                                                                                                                                                    | **PAGE**                                 | fleet-wide outage (no usable account)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `notify_slot_quarantined`                                                                                                                                                                                                                                                                                                                                                                                         | **PAGE**                                 | a quarantined slot is **starving** escalation dispatch (velocity loss)                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `notify_watchdog_kill`                                                                                                                                                                                                                                                                                                                                                                                            | **PAGE** _(cap-hit only)_                | plain kills already log; only the daily-cap-hit (watchdog dormant) pages                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |
| `notify_watchdog_dormant`                                                                                                                                                                                                                                                                                                                                                                                         | **PAGE**                                 | fleet self-healing is OFF (daily kill cap hit). The STANDING condition `notify_watchdog_kill` leaves behind — that one fires from inside the single kill that crosses the cap, so while dormant it can neither re-remind nor close. Transition-deduped on a disk latch (`dedup_state.watchdog_dormant_alerted_path`), evaluated every watchdog tick.                                                                                                                                                                                        |
| `notify_watchdog_dormant_resolved`                                                                                                                                                                                                                                                                                                                                                                                | **PAGE**                                 | ✅ CLOSE bookend for the above — fires the first tick the kill budget is available again (UTC-day rollover or an operator cap reset)                                                                                                                                                                                                                                                                                                                                                                                                        |
| `notify_escalation_unresolved`                                                                                                                                                                                                                                                                                                                                                                                    | **PAGE**                                 | a CI wall stuck past deadline                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| `notify_escalation_abandoned`                                                                                                                                                                                                                                                                                                                                                                                     | **PAGE**                                 | escalation gave up on a wall (terminal — human needed)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `notify_plan_health_dispatch_failed`                                                                                                                                                                                                                                                                                                                                                                              | **PAGE**                                 | the plan_health job failed to dispatch (was Slack-silent)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `notify_daily_summary`                                                                                                                                                                                                                                                                                                                                                                                            | **PAGE**                                 | the digest itself                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| `notify_daily_summary_failed`                                                                                                                                                                                                                                                                                                                                                                                     | **PAGE**                                 | a dead digest must not be silent                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `notify_head_backward_dataloss`                                                                                                                                                                                                                                                                                                                                                                                   | **PAGE**                                 | a slot repo's committed-but-unpushed commit was silently discarded by an out-of-band branch reset (`HeadBackwardCanary`; baseline-seeded + persisted-seen dedup, pages each new loss once)                                                                                                                                                                                                                                                                                                                                                  |
| `notify_backlog_sibling_reset_guard_refused`                                                                                                                                                                                                                                                                                                                                                                      | **PAGE**                                 | `sync_backlog_to_db`'s sibling-reset guard refused to recycle a `done`+`done_sha` task_id row onto a positionally-collided NEW checkbox — a silent-dispatch-loss failure (the new todo now reads as done and never dispatches); deduped by the CALLER keyed on `(task_id, incoming brief_hash)` — `dedup_state.backlog_sibling_reset_guard_alerted_path()` (ao_backlog_collision_alert_and_remediation_ui_2026_07_26)                                                                                                                       |
| `notify_context_saturation_detected`                                                                                                                                                                                                                                                                                                                                                                              | **PAGE**                                 | a target (main/review/worker) has sat at/above the saturation threshold (`context_saturation_alert_pct`, default falls back to `resume_fresh_context_pct`) for ≥`context_saturation_alert_window_seconds` (default 1800s) with no `context_compact_observed` in that window — the compaction safety net itself failing, not routine work; state-transition dedup (one page per streak), re-reminds every `context_saturation_realert_seconds` (default 4h) while still saturated (`ao_context_saturation_never_alerts_2026_08_09` todo 1/2) |
| `notify_context_saturation_resolved`                                                                                                                                                                                                                                                                                                                                                                              | **PAGE**                                 | ✅ closure bookend for the above — fires only for an episode that actually paged (mirrors `notify_escalation_resolved`'s "no page, no bookend" rule); correlates via the episode's `opened_at`                                                                                                                                                                                                                                                                                                                                              |
| `notify_agent_stuck_escalation`                                                                                                                                                                                                                                                                                                                                                                                   | summary                                  | "Auto-respawn FAILED" — automatic self-healing escalation                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `notify_autospawn_flap`                                                                                                                                                                                                                                                                                                                                                                                           | summary                                  | AutoSpawn retry loop (self-healing backoff)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `notify_stash_on_done`                                                                                                                                                                                                                                                                                                                                                                                            | summary                                  | worker stashed WIP to pass the /done gate (lifecycle)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                       |
| `notify_spawn_failed`                                                                                                                                                                                                                                                                                                                                                                                             | summary                                  | hard spawn failure — self-heals; a dead token is re-routed to the auth page                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| `notify_spawn_recovered` / `notify_slot_recovered` / `notify_agent_stuck_respawned`                                                                                                                                                                                                                                                                                                                               | summary                                  | recovery/closure bookends                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `notify_plan_health_dispatched` / `notify_escalation_dispatched`                                                                                                                                                                                                                                                                                                                                                  | summary                                  | dispatch success                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| `notify_work_picked_up`                                                                                                                                                                                                                                                                                                                                                                                           | summary _(default-off)_                  | env-gated, off by default                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   |
| `notify_slot_blocked_answered`                                                                                                                                                                                                                                                                                                                                                                                    | **PAGE**                                 | ✅ closure bookend when a BLOCKED question is answered (human/main) or auto-resolved (`reconciliation-sweep`) — names who + the answer + a closes-the-question-opened-`<ts>` line (operator 2026-07-18; FINAL answers only, a `partial` stays open)                                                                                                                                                                                                                                                                                         |
| `notify_escalation_resolved`                                                                                                                                                                                                                                                                                                                                                                                      | **PAGE** _(only if it previously paged)_ | ✅ closure bookend for a CI/CD wall that PAGED unresolved/abandoned; log-only otherwise (a closure with no matching open is churn) — gated by `_clear_unresolved_page_cooldown` returning `True` (operator 2026-07-18)                                                                                                                                                                                                                                                                                                                      |
| `notify_git_staleness_red`                                                                                                                                                                                                                                                                                                                                                                                        | **PAGE**                                 | repo red ≥30 min sustained (operator 2026-07-14; state-transition dedup: once per episode, 4h re-remind); the re-remind renders "STILL RED — reminder" + an Open-since age so it's distinct from a fresh page (operator 2026-07-18)                                                                                                                                                                                                                                                                                                         |
| `notify_git_staleness_resolved`                                                                                                                                                                                                                                                                                                                                                                                   | **PAGE**                                 | closes the RED page in-channel with the episode summary + a "closes the RED opened `<ts>`" correlation line (operator 2026-07-14 / 2026-07-18)                                                                                                                                                                                                                                                                                                                                                                                              |
| `notify_disk_space_low`                                                                                                                                                                                                                                                                                                                                                                                           | **PAGE**                                 | orchestrator VM root filesystem free space dropped below `tuning.disk_space_min_free_gb` (default 60G) — `DiskSpaceCanary` (`server/disk_space_canary.py`, infra_satellite_ao_dispatch_batch10_2026_08_09 todo 3), 300s cadence; closes the gap both the 2026-06-28 full-disk wedge and the 2026-08-08 175G abandoned `manifest-consolidate-*` scratch find exposed (caught by a human, not a monitor). State-transition dedup on `dedup_state.disk_space_breach_path()`                                                                    |
| `notify_disk_space_resolved`                                                                                                                                                                                                                                                                                                                                                                                      | **PAGE**                                 | ✅ closure bookend for the above — fires the first tick free space is observed back above threshold                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| `notify_spawn_failure` / `notify_slot_stale` / `notify_slot_failed` / `notify_unpushed_plans` / `notify_main_agent_rate_limited` / `notify_worker_usage_frozen` / `notify_account_pool_exhausted` / `notify_plan_health_findings` / `notify_account_rotated` / `notify_context_burn` / `notify_likely_claude_outage` / `notify_account_usage_high` / `notify_gh_rate_limit_threshold` / `notify_run_volume_spike` | summary                                  | already `logger.info` (prior downgrades)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    |

## Self-monitoring detector registry — owner / cadence / verifier

A silent-detection-gap incident (`/plans/archive/issues/ao_context_saturation_never_alerts_2026_08_09.md` — a saturated
main-agent context paged nobody for hours) produced two "is the safety net itself still working" detectors. Per the
runbook declaration rule (`/codex/15-runbooks/README.md` § "Cross-link conventions" — every operator-facing procedure
declares `owner`/`cadence`/`verifier`/`last_executed` so it can't silently rot), these are registered here too, even
though this doc is a codex-ssot rather than a `15-runbooks/` playbook — the whole point of this incident family is that
an undeclared detector is indistinguishable from a working one until something looks. `cadence` below means "how often
the detector itself runs," not an operator-run schedule; `last_executed` doesn't apply to a continuous in-process check
and is omitted in favor of `verifier`, which is how you'd confirm it's still alive.

| Detector                                                                                                                                                                               | Owner                                                | Cadence                                                                                                                                                                                                                                                                                                                       | Verifier                                                                                                                                                                                                                                                                                                                                                                | Code                                                                 |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Context-saturation-without-compaction (`_is_saturated_without_compaction` / `ContextLifecyclePolicy._tick_saturation_detector`) — pct at/above threshold for ≥30min with no compaction | backend_engineer craft (AO on-call: operator ikenna) | every `ContextLifecyclePolicy.tick` (main-agent-keeper loop, `main_agent_interval_seconds` = 60s), for every target (main/review/worker)                                                                                                                                                                                      | `tests/test_context_lifecycle.py::test_saturation_detector_*` (8 tests: fires/doesn't-fire/dedup/reminder/resolve) + `tests/test_alert_quality_overhaul.py::test_context_saturation_{detected,resolved}_*` (2 tests, direct `_post`-capture proof); live confirm = `context_saturation_detected`/`_resolved` activity-log rows + a page in `#agent-orchestrator-alerts` | `agent-orchestrator@bb81c7b` (detector) + `@e8818aa` (Slack routing) |
| Context-activity-silence ("silent-disarm": no context-lifecycle activity event of ANY type for a role with a live session for ≥`context_activity_silence_alert_seconds`, default 4h)   | backend_engineer craft (AO on-call: operator ikenna) | every `ContextLifecyclePolicy.tick` (main-agent-keeper loop, `main_agent_interval_seconds` = 60s), for every target (main/review/worker) — queries the activity log's latest matching event per `slot_id` directly rather than an in-memory streak, so a target already silent before an orchestrator restart is still caught | `tests/test_context_lifecycle.py::test_activity_silen*` / `test_activity_silence_detector_*` (6 tests: pure-predicate fires/doesn't-fire/disabled + end-to-end fires-on-all-quiet + does-not-fire-when-activity-logged + resolves-on-reappearance); live confirm = `context_activity_silence_detected`/`_resolved` activity-log rows                                    | `agent-orchestrator@55bd730`                                         |
| Disk-space-low (`DiskSpaceCanary.tick_once` — root filesystem free space below `tuning.disk_space_min_free_gb`, default 60G)                                                           | infra craft (AO on-call: operator ikenna)            | own daemon thread, `tuning.disk_space_interval_seconds` = 300s                                                                                                                                                                                                                                                                | `tests/test_disk_space_canary.py` (20 tests: pure `assess()` boundary cases + state-transition dedup + mocked-probe `tick_once` synthetic-trigger fires/resolves + start/stop lifecycle); live confirm = `disk-space-breach` sentinel flip + a page in `#agent-orchestrator-alerts`                                                                                     | `agent-orchestrator@bb85164`                                         |

**RETIRED 2026-07-28 (RULE-11 prove-then-retire)**: the daily `:broom: Plan-hygiene sweep FAILED` PM Cloud Run cron
(`uts-prod-plan-hygiene-sweep`, 05:00) described below no longer exists — the job + its Cloud Scheduler + terraform were
deleted, superseded by the daily deep `plan-reconciler` agent (01:00 UTC, systemd timer on the central orchestrator VM)
which fixes findings instead of just re-posting the same unchanged Slack failure. See
`/codex/11-project-management/plan-hygiene.md` § "Daily deep reconciler" for the full record. Preserved below for
history (the dedup gap it names never got fixed — moot now that the job is gone):

> the daily `:broom: Plan-hygiene sweep FAILED` was a PM **Cloud Run cron** (`uts-prod-plan-hygiene-sweep`, 05:00) that
> re-posted the same unchanged failure every day with no dedup — it did not flow through `slack._post`.

## Token failures are classified by the DEFINITIVE HTTP code, never guessed

The Anthropic API returns unambiguous codes, so account health is decided by the **code**, not by inferring from a
frozen pane (operator 2026-07-13: _"the api codes are already known, why are we guessing?"_). Two detectors, one rule:

- **Poller (`UsagePoller`, continuous):** probes every account's OAuth token each tick — `401/403` → dead/expired token
  → `notify_account_auth_failed` (CRITICAL, re-mint) + mark `auth_failed`; `429` → `rate_limited` (marked, **no page** —
  transient/self-clearing); `200` → clears any standing auth flag.
- **Spawn-time (`autospawn._classify_spawn_failure_via_token_probe`):** when a spawn dies at startup, **probe the token
  for the real code** instead of pattern-matching the pane-tail — `401/403` → drop from rotation + the same CRITICAL
  re-mint page; `429` → mark `rate_limited` (no page); `200` → the token is healthy, so the failure is a tmux/heartbeat
  issue → the summary-only `notify_spawn_failed` record (a working account is **never** dropped on a misleading pane);
  `5xx`/network → transient, no mark (never false-positive a blip). This replaced the old pane-substring guess
  (`_spawn_failure_is_auth_shaped`), which mislabelled a busy-but-alive worker as a possible dead token.

**Net:** a genuine dead/expired token pages CRITICAL (actionable — re-mint `claude setup-token`); a rate-limit is silent
(transient); everything else is summary-only. No alert guesses a cause the codes already state.

## Daily digest (`DailySummaryLoop`)

`server/daily_summary.py` runs a supervised daemon loop (default 24h, `ORCHESTRATOR_DAILY_SUMMARY_INTERVAL_SECONDS`,
enabled by default via `ORCHESTRATOR_DAILY_SUMMARY_ENABLED`). Each tick rolls the DB activity log since a persisted
cursor (`dedup_state.daily_summary_cursor_path`, key `last_summary`) into one `notify_daily_summary` message — counts by
event type + a failure roll-up + total — then advances the cursor. `_tick_and_report` wraps the tick so any exception
fires `notify_daily_summary_failed`. The cursor makes a digest cover exactly "since the last summary" across restarts.

The `Activity` list shows the **top-25 event types by frequency**. A failure-typed row (name contains `fail` / `error` /
`abandon`) that ranks below #25 is **appended anyway** (🔴-marked) rather than truncated — the fail-count line points
the operator "see the counts below", so hiding the very failures it announces would defeat the digest
(`alert_channel_cleanup` WS-B follow-up).

## Digest anatomy — field reference

Each digest (`notify_daily_summary` → the `:bar_chart: AO daily activity digest` message) has these fields:

| Field                                                 | Meaning                                                                                                                                                                                                                                 |
| ----------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Since**                                             | Window start — the timestamp of the previous digest (the persisted `last_summary` cursor). The window is `[Since, now]`; the next digest's `Since` is this run's `now`. So every event is counted exactly once across the whole series. |
| **Total events**                                      | Count of **all** activity-log rows in the window (the sum of every row in the Activity list, including types beyond the shown top-25). This is total orchestrator throughput, not an error count.                                       |
| **N failure event(s)** / _No failures ✅_             | `fail_total` = the summed **count** (not the number of distinct types) of every event type whose name contains `fail` / `error` / `abandon`. `:rotating_light:` when non-zero; a green check when clean.                                |
| **Activity (by type, most frequent first)**           | `event_type — count`, top-25 by count, plus any 🔴-marked failure rows pulled up from below #25 (see above). `count` is occurrences in the window.                                                                                      |
| **Footer** (`open dashboard \| from: <host> \| <ts>`) | `open dashboard` links the AO dashboard; `from:` is the emitting host (e.g. `vm-planning` = the central orchestrator VM); `<ts>` is when the digest was rendered (UTC).                                                                 |

## Digest event glossary — what each `event_type` means

Every row is a DB activity-log event (`log_activity`). Most only appear in the digest (they no longer page — that is the
point of the actionable-only contract); `slot_blocked` and any failure-typed row **also** page live. Grouped by
lifecycle stage (code ref = the `log_activity` call site in `agent-orchestrator/`):

**Boot / spawn**

- `slot_boot` — a worker slot booted and confirmed its mandatory role read-files; it is registered and ready
  (`server/routes/slots_worker.py`).
- `boot_read_unconfirmed` — a boot handshake was **rejected** (HTTP 428) because the worker didn't confirm reading the
  expected role prompts; slot state was left unmutated and the worker must re-boot (`slots_worker.py`).
- `autospawn_succeeded` — the AutoSpawn loop launched a worker into a slot that had queued work (`server/autospawn.py`).

**Task lifecycle**

- `task_dispatched` — a queued task was assigned to a slot (routine) (`slots_worker.py`, `routes/slots_worker.py`).
- `slot_task_skipped` — a slot's assigned task was released back to the queue / cleared (with a `reason`, e.g. an
  orphaned stale marker) (`server/routes/slots_ops.py`).
- `slot_progress` — a worker reported forward progress (a heartbeat carrying a state delta) (`slots_worker.py`,
  `worker_liveness_watchdog.py`).
- `slot_done` — a worker signalled its task complete (`slots_worker.py`).
- `slot_done_verified` — the completion claim was verified (review-agent / watchdog confirmed) (`slots_worker.py`).
- `agent_replied` — an agent posted a reply (e.g. the main/review agent answered a worker) (`server/routes/agents.py`).
- `agent_message_sent` — an inter-agent message was sent (`routes/agents.py`).

**Git health**

- `git_status_reported` — a slot's `slot-git-status-report.sh` cron posted its per-repo git status (`host`,
  `repo_count`). A high-volume, purely informational heartbeat — usually the #1 row (`server/routes/git_health.py`).
- `idle_blocker_inferred` — for an **idle** slot the orchestrator inferred _why_ it is blocked (top blockers + blocked
  task count); logged on change or hourly while still blocked (`server/worker_liveness/_git_alerts.py`).

**Liveness / self-healing** (the watchdog auto-recovers; these are informational — no manual action)

- `worker_kicked` — the WorkerLivenessKicker nudged a wedged worker and **verified** it resumed (spinner appeared or the
  heartbeat advanced past its pre-kick value). Its failure counterpart `worker_kick_failed` is a failure-typed row
  (`server/worker_liveness/__init__.py`).
- `slot_idle_stale` — a slot went silent past the idle threshold and was marked `stale` (`server/health.py`).
- `worker_polling_dead` — operator-tier signal: a worker hasn't heartbeat'd in N min; the watchdog auto-reclaims the
  wedged session and AutoSpawn respawns it when work is queued (no manual action needed) (`server/health.py`).
- `watchdog_heartbeat_resumed` — the watchdog resumed a slot after heartbeat-silence, context intact
  (`worker_liveness_watchdog.py`).
- `tmux_session_lost` — a slot's tmux session disappeared / was pruned (`server/tmux_pruner.py`).
- `slot_compacted` — a worker's context window was compacted (`slots_worker.py`).
- `session_checkpoint` — a periodic GCS session checkpoint was written (`server/gcs_sync.py`).
- `slot_retire_audit_needed` — a slot's task queue is exhausted; signals the review agent to run the 6-step retire audit
  (`slots_worker.py`).

**Plan-health / escalation** (the automatic backend jobs WS-A stopped paging individually — see "What does NOT page")

- `plan_health_dispatch_initiated` — the plan_health job started a dispatch cycle (`server/plan_health.py`).
- `escalation_dispatch_initiated` — an escalation dispatch cycle started (`server/escalation.py`).
- `escalation_dispatched` — an escalation was dispatched (`escalation.py`).
- `escalation_resolved` — an escalation closed / resolved (`escalation.py`).
- `slot_blocked` — a worker posted a **BLOCKED question** (needs main/review-agent or operator input). This is the one
  digest row that **also pages** live via `notify_slot_blocked`; the digest simply counts it like any other activity row
  (`slots_worker.py`, `worker_liveness_watchdog.py`).

**Reading a digest:** a healthy window is dominated by `git_status_reported` + `worker_kicked` + `slot_boot` (heartbeat
churn) with `No failure events ✅`. A `:rotating_light:` line means look at the 🔴-marked rows: `*_fail` / `*_failed` /
`*_error` / `*_abandon*` events are the ones worth investigating (most page individually too, so the digest is a
cross-check, not the primary signal).

## Standing-condition dedup (state-transition)

A condition that stays true must not re-page every tick. Two mechanisms:

- **In-process / server:** `server/dedup_state.py` (`diff_keys`, cooldown dicts) — page on the true→false transition + a
  RESOLVED bookend, persisted to `STATE_DIR` so a restart does not re-arm a flood.
- **Per-VM cron (`fleet-git-health-guard.sh`):** a local state file (`GIT_HEALTH_GUARD_STATE_DIR`) holds the last
  problem signature + timestamp. It posts only on a **new/changed** signature, on **RESOLVED**, or on a **re-remind
  interval** (`GIT_HEALTH_GUARD_REMIND_SECS`, default 1h) — not every 15-min tick.
  `bash fleet-git-health-guard.sh --self-test` proves the state machine. The guard is a genuine actionable alert (a real
  fsck failure once produced 369 duplicates in 4 days) — dedup makes it **visible**, it does not downgrade it.

## Git-staleness paging (restored 2026-07-14 — operator directive)

The 2026-07-13 cleanup downgraded `notify_git_staleness_red` / `notify_unpushed_plans` to log-only; combined with the
alerts being evaluated ONLY inside the WorkerLivenessKicker's live-worker "working" branch, the root PM clone sat dirty
for 2 days with zero pages (slot 0 = the main workspace is `paused` → never scanned). Operator directive 2026-07-14
restores the page with the standing-condition dedup this doc mandates:

- **Coverage is snapshot-driven, not worker-driven**: `_git_surfaces_pass()` in `_tick_once` evaluates EVERY
  `(host, slot_id)` with a reporter snapshot — including paused slot 0 and slots with no live tmux worker. The
  worker-directed commit NUDGE stays gated on a live worker (no one to nudge otherwise), and is the one consumer that
  stays intentionally local-host-only (below).
- **Host-qualified, every reporting host — not just the AO server's own machine** (2026-08-10, SlotGitStatusRow
  single-source-of-truth migration): coverage used to silently stop at the server's own host. `set_slot_git_status`
  always wrote the real per-`(host, slot_id)` `SlotGitStatusRow`, but ALSO mirrored onto a legacy `SlotRow.git_status_*`
  column set that `_git_alerts.py` actually read — and that mirror only ever populated when the reporting host matched
  the AO server's own machine. A laptop's (or any other non-server host's) dirty worktree was therefore structurally
  invisible to this pager no matter how long it sat dirty — confirmed live 2026-08-10: a root PM clone on a laptop sat
  139 commits behind, dirty, for 2+ hours, completely unpaged, discovered only by chance. `maybe_alert_git_staleness`
  and `maybe_alert_unpushed_plans` now read `SlotGitStatusRow` directly (keyed by `(host, slot_id)` — two different
  hosts' identically-numbered slots are independent episodes, own throttle entries, own Slack episode). The Slack
  message itself now names the actual reporting `host` (previously it always showed the AO server's own fixed
  `_HOST_LABEL`, which never varied regardless of which machine was actually dirty). `maybe_nudge_on_red_repos` and
  `routes/state.py`'s `/api/state` dashboard view stay scoped to `state_store.this_process_hostname()` by design — a
  nudge pokes a local tmux worker's inbox that no remote host has, and `/api/state`'s `SlotRow` view is inherently
  per-AO-worker-slot (AO workers only run on the server's own host). `failover.py`'s dormant `_slots_for_host` (offline
  → slot lookup) was migrated the same way — it also read the now-removed legacy mirror by `slot_id` alone, so a
  genuinely offline REMOTE host's slots could never resolve even once multi-VM failover is re-enabled.
- **90-min sustain** (raised from 30 → 50 → 90 min across 2026-07-24 and 2026-07-26 — see `GIT_RED_SUSTAIN_S`'s own
  comment history for the two measured false-positive bursts that drove each raise): a repo pages only when red (dirty
  via `dirty_oldest_mtime`; ahead / diverged / clean-but-behind via `not_clean_since`) for ≥90 min — transient
  ahead-between-commit-and-push never pages.
- **4h re-remind**: one page per RED episode, re-fired every 4h while still red (`GIT_RED_REALERT_S`); throttle is
  disk-persisted so a server restart never re-fires a still-red page.
- **Reporter-cron silence ≥15 min is itself red** (`REPORTER_STALE_S` = 3 missed 5-min ticks — the old 5-min gate sat ON
  the reporter cadence and flapped alert→resolved every tick).
- **RESOLVED bookend carries the episode summary** ("recovered after Xm — was: <red repos>"); episode context is
  in-memory, so a bookend after a mid-episode restart is summary-less by design.
- `notify_unpushed_plans` stays log-only — its content is covered by the staleness page's per-repo dirty lines.
- **Recovery must be SUSTAINED, not a single clean tick** (`GIT_CLEAN_CONFIRM_S`, fix 2026-07-14): the day the
  30-min-sustain page went live it flapped — the live channel showed dozens of RED/RECOVERED pairs across several slots,
  "recovered after 0m" repeating every few minutes for hours. Root cause: `slot-git-status-report.sh` rebuilds each
  slot's ENTIRE repo snapshot via a bash walk that can transiently drop one repo for a single ~5-min cycle (a
  `pushd`/`git status` hiccup) — that one blip read as "nothing red," which fired the RESOLVED bookend AND cleared the
  4h re-alert throttle, so the very next real-red tick re-alerted immediately. Fix: a clean reading must be sustained
  past `GIT_CLEAN_CONFIRM_S` (15 min, ~3x the reporter cadence) before it clears the throttle — a lone blip now leaves
  the episode fully armed (no bookend, no re-page); only a genuine, sustained recovery fires RESOLVED. Any red tick
  cancels an in-progress clean streak (`kicker._staleness_clean_since`, in-memory, same restart semantics as the other
  episode dicts).

Code: `agent-orchestrator/server/worker_liveness/_git_alerts.py` (`GIT_RED_SUSTAIN_S` / `GIT_RED_REALERT_S` /
`REPORTER_STALE_S` / `GIT_CLEAN_CONFIRM_S`), `server/worker_liveness/__init__.py` (`_git_surfaces_pass`,
`_staleness_clean_since`), `server/notifications/slack.py`, `server/state_store/slots.py` (`SlotGitStatusRow` CRUD +
`this_process_hostname`), `server/routes/git_health.py` (the `/api/slots/{id}/git-status` POST/GET),
`server/routes/state.py` (`/api/state`'s per-slot dashboard view), `server/failover.py` (`_slots_for_host`, dormant).
The ORM source of truth is `SlotGitStatusRow` in `server/orm.py` — see its docstring for the `(host, slot_id)`
composite-key rationale.

## Repeat-page hardening (2026-07-14) — dedup race + escalation over-creation

A same-day operator sweep of the live channel (24h pull, post the 2026-07-13 cleanup) found two more repeat-page sources
beyond the git-staleness flap above — both fixed in `agent-orchestrator@50557aa`:

- **`notify_plan_health_dispatch_failed` — dedup race, not a missing dedup.** The 1h cooldown
  (`plan_health.py _alert_dispatch_failed`) does a read-check-write on a disk-persisted cooldown dict with no lock. The
  server runs single-process (`uvicorn` with no `--workers`), but two near-concurrent dispatch attempts (e.g. a
  client-side retry racing the still-in-flight original request) could each read the cooldown before either wrote it —
  observed live as the same slot's failure paging twice 6 minutes apart, and a different slot's failure paging twice 21
  minutes apart. Fixed with an in-process `threading.Lock` around the read-check-write section
  (`plan_health._dispatch_failed_lock`) — the Slack POST itself stays outside the lock so a slow network call never
  blocks a concurrent caller's dedup check.
- **`notify_escalation_unresolved` — repeated pages are a symptom of escalation OVER-CREATION, not a missing
  notification dedup.** `_find_open_escalation`'s idempotency guard only collapses a duplicate trigger while the
  existing escalation for that (repo, wall_type) is non-terminal (queued/dispatched); once one goes terminal
  (`unresolved`, cap hit), a wall still red spawns a BRAND NEW escalation that repeats its own full
  re-escalate-then-cap-hit page pair. Observed live: 7 "NOT resolved" pages for one repo in under 3 hours, all
  legitimately distinct escalation rows. Rather than change escalation-creation/self-healing semantics (retrying a
  broken wall with a fresh worker is correct behavior — the noise is purely in re-telling the operator), the page itself
  is now cooldown-deduped per `{repo}:{wall_type}:{reescalating|cap_hit}` (`UNRESOLVED_PAGE_COOLDOWN_HOURS = 3`,
  `escalation._unresolved_page_allowed` / `dedup_state.escalation_unresolved_path`). The two stages of ONE lifecycle
  (re-escalating → cap hit) always both page — that transition is a genuine severity increase — while a fresh escalation
  repeating the SAME stage within the cooldown collapses. `_mark_resolved` clears both stage cooldowns on resolution
  (`escalation._clear_unresolved_page_cooldown`) so a later, genuinely NEW break on the same wall pages immediately
  rather than inheriting a stale suppression window.

Code: `agent-orchestrator/server/plan_health.py` (`_dispatch_failed_lock`), `server/escalation.py`
(`_unresolved_page_allowed`, `_clear_unresolved_page_cooldown`, `UNRESOLVED_PAGE_COOLDOWN_HOURS`),
`server/dedup_state.py` (`escalation_unresolved_path`).
