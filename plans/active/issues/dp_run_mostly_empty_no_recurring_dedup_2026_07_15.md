---
doc_type: issue
title:
  DP_RUN_MOSTLY_EMPTY (DP-FETCH-007/009) re-fires byte-identical CRITICAL alerts every meta-sweep tick — no
  recurring-alert dedup wired
summary:
  "`#data-pipeline-alerts` posted byte-identical `DP_RUN_MOSTLY_EMPTY` CRITICAL alerts (same
  attempted_failed/attempted/ratio) ~14 min apart at 2026-07-15 ~12:03 and ~12:17 for many (asset_group, data_type)
  cells (e.g. sports/trades 112277/522276, 21.5%). Root cause: `check_high_attempted_failed` (meta_watchers.py) has only
  an ONSET gate (MissTracker, min_consecutive=2) — no ongoing re-fire suppression — and re-emits unconditionally every
  `dp-meta-watchers` cron tick (`*/15 * * * *`) while the manifest cell stays high; the downstream alerting-service
  `AlertDeduplicator` cannot bridge that gap because DP_RUN_MOSTLY_EMPTY is CRITICAL and was never added to
  `_RECURRING_WARN_EVENTS` (router.py) so it inherits the 60s default TTL, far shorter than the 900s sweep cadence."
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service, alerting-service]
scope: [engineer, admin]
tags: [monitoring, alerting, data-pipeline, observability, dedup, slack-spam]
related:
  [
    codex/05-infrastructure/data-pipeline-alerts.md,
    codex/15-runbooks/incidents/rb_data_001.md,
    plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    plans/active/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md,
  ]
created: 2026-07-15
parent_epic: observability_master
priority: P1
source: ["operator report: #data-pipeline-alerts duplicate DP_RUN_MOSTLY_EMPTY spam, 2026-07-15 ~12:03/12:17"]
assigned_vm:
resolved_by:
locked_by:
locked_since:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-15
---

## What I found

Verified from code (no changes made — diagnosis only):

1. **Detector — onset-gated, never re-nag-gated.** `check_high_attempted_failed`
   (`deployment-service/deployment_service/data_pipeline_monitors/meta_watchers.py:577-673`) reads the consolidated
   manifest `_index` (`AVAILABILITY_INDEX_BLOB`) every sweep and computes `attempted_failed`/`ratio` per
   `(asset_group, data_type)` cell. A `MissTracker` (GCS-persisted consecutive-miss counter,
   `_high_attempted_failed_miss_key`, lines 620-636) gates the **onset** — a cell must be HIGH for `min_consecutive=2`
   sweeps before it first pages. Once past that threshold there is **no further gate**: every subsequent sweep where
   `cell.high` is still True calls `_emit()` unconditionally (lines 647-672), producing an identical `PipelineFinding`
   (same `asset_group`/`data_type`/`captured`/`attempted_failed`/`ratio` — nothing retries the failed cells between
   sweeps, so the numbers never change). The only cross-sweep state that reacts to the condition CLEARING is
   `reconcile_resolved()` (lines 102-160), which posts a `RESOLVED` bookend when a key drops out of the emitted set — it
   does nothing to suppress a re-fire while the condition is still true.
2. **Cadence = exactly the observed gap.** The detector runs inside the `dp-meta-watchers` Cloud Run Job on
   `google_cloud_scheduler_job.dp_meta_watchers_cron`, `schedule = "*/15 * * * *"`
   (`deployment-service/terraform/gcp/data_pipeline_fleet_monitor_scheduler.tf:245-248`) — matching the observed
   ~14-minute gap between the 12:03 and 12:17 duplicates.
3. **Downstream dedup exists but its TTL is far shorter than the cadence it needs to bridge, and CRITICAL is
   deliberately excluded from the longer cooldown.** `alerting-service/alerting_service/notifiers/router.py`'s
   `route_event()` does call
   `_deduplicator.is_duplicate(event_name, details, ttl_override=_dedup_window_for(event_name))` (line 552) before the
   DP_* branch. But: `_deduplicator = AlertDeduplicator(ttl_seconds=60.0)` (line 66) — default TTL 60s.
   `_dedup_window_for()` (lines 85-88) only grants a longer TTL (`_RECURRING_WARN_COOLDOWN_SEC = 1800.0`, 30 min) to
   events in `_RECURRING_WARN_EVENTS = {"DP_VM_STALL", "DP_EVENT_LOOP_STARVED"}` (lines 76-82) — both WARN. The comment
   at lines 68-75 is explicit: _"CRITICAL events (DP_VM_GONE_NO_CAPTURE / CONSOLIDATOR_DOWN) are intentionally NOT here
   — they keep the short default so their incident page is not over-suppressed."_ `DP_RUN_MOSTLY_EMPTY` was never added
   to either set, so it inherits the 60s default — evicted long before the next 900s sweep tick, so the dedup NEVER
   actually catches the repeat (this is not a hashing bug; the identity-hash would correctly collapse two
   truly-simultaneous fires — it is a pure TTL-vs-cadence mismatch, same failure class the codex-cited CI-alerting rule
   was written to prevent: _"cooldowns track a condition's MEASURED cadence, not its declared cron"_).
4. _\*The codex-documented "incident gateway # dedup/ack/re-nag/recovery-verify (CRITICAL only)"
   (`alerting-service/alerting_service/gateway/*`, e.g. `gateway/dedup.py`'s `compute_incident_key`, 5-min window) is
   real, wired code — but it is NOT in the DP_* code path._\* `_route_data_pipeline_event` (router.py:357-397) mirrors
   to Slack + fires PagerDuty/Telegram directly and returns; the gateway machinery (`wrap_legacy_alert` /
   `IncidentStateMachine` / `RecoveryVerifier`) is only reached via the separate `route_legacy_alert()` →
   `route_incident()` path (router.py:996-1009), keyed on
   `service/component/problem_type/strategy_id/venue/instrument_id` — a scope tuple that has no `asset_group`/
   `data_type` field and is used for execution/strategy incidents, not the DP_* family. So the codex diagram's "incident
   gateway" box for CRITICAL DP alerts describes design intent, not current code — a genuine codex/code drift, not just
   a missing cooldown entry. (Even if it were wired, its 5-min window is still shorter than the 15-min sweep cadence, so
   it would need the same cadence-aware fix.)
5. **Why `DP_VM_EXIT_NONZERO` resolved cleanly ~5 min later but `DP_RUN_MOSTLY_EMPTY` doesn't**: `DP_VM_EXIT_NONZERO`
   comes from a _different_ detector (`exit_code_fleet_monitor.py`, `*/5` cron) whose finding source is a VM's terminal
   exit state — a one-shot condition per VM that naturally clears once the VM is reaped/relaunched, so the cross-sweep
   RESOLVED bookend (extended to all 3 fleet sweeps in the 2026-06-23 flood-triage pass,
   deployment-service@a19bbda/2763578) closes it out fast. `DP_RUN_MOSTLY_EMPTY`'s condition (failed manifest cells) has
   no such natural clearing — nothing re-attempts the cells — so it repeats identically, unbounded, every 15 minutes
   until a human manually re-runs the backfill for that cell.

## Not previously tracked

`plans/active/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` (the prior flood-triage pass, which
_shipped_ the `_RECURRING_WARN_EVENTS` cooldown pattern + the cross-sweep RESOLVED bookend) covered `DP_VM_STALL`,
`DP_CRON_DID_NOT_FIRE`, `DP_VM_GONE_NO_CAPTURE`, `DP_CATALOG_NOT_RUNNING`, `DP_ZOMBIE_WATCHDOG_DOWN` — but never
`DP_RUN_MOSTLY_EMPTY` (it did not exist as an alert until DP-FETCH-009 reused the event, per the meta_watchers.py module
docstring). `codex/05-infrastructure/data-pipeline-alerts.md` documents the intended incident-gateway model but doesn't
flag this gap; `codex/15-runbooks/incidents/rb_data_001.md` documents `DP_RUN_MOSTLY_EMPTY` as page_operator and states
"the RESOLVED bookend posts" on recovery, without addressing the un-suppressed repeat while still-firing. This is a new
finding.

## Recommended fix (scoped)

1. **[alerting-service] Generalize the recurring-alert cooldown to cover sustained CRITICAL conditions, not just WARN.**
   Replace `_RECURRING_WARN_EVENTS: frozenset[str]` with a `dict[str, float]` (event → cooldown seconds) so a CRITICAL
   event whose underlying condition is a _static, re-scanned-every-tick_ signal (not a flappy one-shot) can opt into a
   cooldown ≥ its detector's measured cadence. Add `DP_RUN_MOSTLY_EMPTY: 1800.0` (30 min, matching the existing
   convention and ≥ the 900s meta-sweep cadence) to that map; rename `_dedup_window_for` accordingly. This preserves
   "CRITICAL still pages" (re-nags every 30 min while unresolved) while eliminating the literal every-15-min duplicate.
2. **[deployment-service, defense-in-depth] Give `check_high_attempted_failed` its own re-nag interval**, mirroring
   `MissTracker` but persisting a `last_alerted_at` timestamp per `(asset_group, data_type)` key (not just a
   consecutive-miss counter) so the detector itself only re-emits after a cooldown elapses since its last emission for
   that cell — matching the CLAUDE.md CI-alerting rule ("fire on change / RESOLVED / re-remind, never every tick") at
   the source rather than relying solely on the downstream generic dedup.
3. **[docs]** Update `codex/05-infrastructure/data-pipeline-alerts.md`'s emit→route→escalate diagram to reflect that the
   "incident gateway" box is NOT currently wired for the DP_* family (only `route_legacy_alert`/`route_incident` reaches
   it) — either wire DP_* CRITICAL events through it, or correct the diagram so it doesn't overstate current coverage.

## Open work (tracked todos)

- [x] [CODE] P1. `alerting-service`: add a cadence-aware cooldown for `DP_RUN_MOSTLY_EMPTY` (and audit the rest of the
      CRITICAL DP-\* family for the same "re-scanned every tick, no ongoing suppression" shape — e.g. any future
      manifest-scan-derived CRITICAL alert) per fix #1 above; +regression test asserting two identical
      `DP_RUN_MOSTLY_EMPTY` fires 900s apart collapse to one delivered alert. —
      `alerting-service@fe76ded34a46f0cfa880c563fe462c155d50809f`
- [ ] [CODE] P2. `deployment-service`: add a persisted re-nag interval to `check_high_attempted_failed` per fix #2
      (defense-in-depth, source-side fix independent of the alerting-service cooldown table).
- [x] [DOCS] P2. Correct/update the incident-gateway wiring claim in `codex/05-infrastructure/data-pipeline-alerts.md`
      per fix #3. — unified-trading-pm (this commit): added a wiring caveat to the emit→route→escalate diagram
      documenting that DP_\* CRITICAL events bypass the incident gateway entirely (only reachable via
      `route_legacy_alert()`/`route_incident()` for execution/strategy incidents) and rely on the `AlertDeduplicator` +
      per-event cooldown map instead.

## Progress Log

- 2026-07-15: Filed by background research agent (diagnosis only, no code changes). Fix #1 (alerting-service) and fix #2
  (deployment-service) dispatched to parallel sub-agents in the same session, tracked in
  `plans/active/data_pipeline_alerts_batch_remediation_2026_07_15.md`. Fix #3 (this doc's docs todo) done directly in
  this commit.
- 2026-07-15: Fix #1 shipped — `alerting-service@fe76ded34a46f0cfa880c563fe462c155d50809f`. Replaced
  `_RECURRING_WARN_EVENTS: frozenset[str]` (`router.py`) with `_RECURRING_ALERT_COOLDOWNS: dict[str, float]` (event →
  cooldown seconds), preserving `DP_VM_STALL`/`DP_EVENT_LOOP_STARVED` at 1800.0s and adding
  `"DP_RUN_MOSTLY_EMPTY": 1800.0` (≥ the 900s meta-sweep cadence). `_dedup_window_for()` now does a plain dict lookup
  (`.get(event_name)`); the "CRITICAL events intentionally NOT here" comment was rewritten to state the real criterion —
  a CRITICAL event opts in only when its condition is a static, re-scanned-every-tick signal (not a flappy one-shot)
  with a cooldown ≥ its detector's measured cadence, so it still re-nags/pages every cooldown window while unresolved,
  it just stops literally duplicating every tick. Added a route_event-level regression test
  (`tests/unit/rules/test_data_pipeline_rules.py::TestRouteEventDataPipeline::test_dp_run_mostly_empty_collapses_across_meta_sweep_cadence`)
  asserting two identical `DP_RUN_MOSTLY_EMPTY` fires 900s apart collapse to one delivered alert (mirror + PagerDuty/
  Telegram page both fire once) and a third fire at 1801s IS delivered again (re-nag boundary), plus a
  `_dedup_window_for("DP_RUN_MOSTLY_EMPTY") == 1800.0` unit assertion in `tests/unit/notifiers/test_router.py`. Full
  `quality-gates.sh --no-fix` green (tests + basedpyright + codex compliance); shipped via quickmerge --agent scoped to
  the 3 touched files. Did not touch todo 2 (deployment-service) — being handled by a parallel agent per this doc's
  Progress Log above.
