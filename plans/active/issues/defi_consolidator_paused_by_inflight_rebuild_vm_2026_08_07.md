---
doc_type: issue
title:
  "CONSOLIDATOR_DOWN for market-data-tick-defi-prd is a KNOWN condition — cron deliberately paused by an in-flight
  canonical manifest rebuild VM, ETA multi-day, not a genuine outage"
summary: >-
  Cloud Scheduler job `uts-prod-manifest-consolidator-market-data-defi-cron` (asia-northeast1) is PAUSED
  (userUpdateTime=2026-08-06T20:16:52Z), firing a live CRITICAL `CONSOLIDATOR_DOWN` alert for bucket
  `market-data-tick-defi-prd-central-element-323112` on every fleet-monitor sweep (heartbeat_age_sec climbing past
  57000+ as of 2026-08-07 12:29 UTC). This is very likely INTENTIONAL, not a genuine outage: VM
  `canonical-migration-defi-rebuild-20260806-223130` (zone asia-northeast1-c, e2-standard-8 SPOT, created
  2026-08-06T22:31:39Z — ~2h15m after the scheduler pause) is actively running
  `market_tick_data_service.scripts.rebuild_defi_manifest --bucket market-data-tick-defi-prd-central-element-323112
  --start-date 2020-01-01 --end-date 2026-12-31 --chunk-days 90` (`VM_OPERATION=migrate-defi-rebuild`). Canonical-
  migration scripts in this workspace have an `_assert_consolidator_paused()` safety precondition — the pattern is to
  pause the scheduled consolidator merge before a manual manifest rewrite, to avoid racing the two. No direct log line
  in the VM's `run.log`/`WATCHDOG_TRACE.log` proves it paused the scheduler itself (pause/resume of the consolidator
  cron is a documented HUMAN-executed step outside the launcher script, per both `rebuild_defi_manifest.py` and
  `deployment-service/scripts/vm/launch-canonical-migration-vm.sh` — never logged by the VM), so the ~2h15m timing
  correlation + the documented operational contract is the best available evidence, not a certainty.

  SEPARATE finding, noted but NOT fixed here: this specific CONSOLIDATOR_DOWN alert currently has ZERO successful
  delivery channel — both `PagerDuty delivery failed for event CONSOLIDATOR_DOWN` and `Email fallback ALSO failed for
  CRITICAL event CONSOLIDATOR_DOWN — undelivered` fire on every occurrence (confirmed via Cloud Logging,
  `uts-prod-alerting-paging` job, e.g. 2026-08-07T12:29:40Z). Per operator decision 2026-08-07, PagerDuty is being
  deprecated in favor of Slack-only routing (to be re-added later as part of the same unified alert flow) — this doc
  does not attempt to fix PD/email delivery. Whether CONSOLIDATOR_DOWN's routing rule should also mirror to Slack (it
  currently appears to have no Slack channel configured, unlike the DP_* family) is a separate, undecided question —
  flagging it here rather than changing routing unilaterally.
status: open
nature: issue
asset_group: [defi, meta]
stage: [data]
repos: [market-tick-data-service, deployment-service, alerting-service, unified-api-contracts]
scope: [engineer, admin]
tags: [consolidator, data-correctness, defi, P2, false-alarm-likely, canonical-migration, pagerduty, delivery-failure]
related: [/codex/05-infrastructure/manifest-consolidator-ssot.md, /codex/05-infrastructure/data-pipeline-alerts.md]
created: 2026-08-07
author: unknown
priority: P2
parent_epic: observability_master
source: >-
  Traced from a live #data-pipeline-alerts Slack reconciliation session, 2026-08-07.
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
context_scope:
  [
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
    market-tick-data-service/market_tick_data_service/scripts/rebuild_defi_manifest.py,
    deployment-service/scripts/vm/launch-canonical-migration-vm.sh,
  ]
---

## What happened

`DP_CATALOG_NOT_RUNNING`'s sibling CRITICAL alert `CONSOLIDATOR_DOWN` has been firing repeatedly (every few minutes, via
the fleet-monitor sweep) for the `market-data-tick-defi-prd-central-element-323112` bucket since at least 2026-08-06
evening. Investigated 2026-08-07 as part of a broader data-pipeline-alerts Slack reconciliation session.

## Evidence

- Scheduler:
  `gcloud scheduler jobs describe uts-prod-manifest-consolidator-market-data-defi-cron --project=central-element-323112 --location=asia-northeast1`
  → state `PAUSED`, `userUpdateTime=2026-08-06T20:16:52Z`.
- VM: `canonical-migration-defi-rebuild-20260806-223130`, zone `asia-northeast1-c`, `RUNNING`, created
  `2026-08-06T22:31:39Z`, SPOT/preemptible.
  - Task:
    `market_tick_data_service.scripts.rebuild_defi_manifest --bucket market-data-tick-defi-prd-central-element-323112 --start-date 2020-01-01 --end-date 2026-12-31 --chunk-days 90`
    (`SHARD_OF=1`, single-shard).
  - Logs:
    `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-rebuild-20260806-223130/{run.log,PROGRESS.json,LAUNCH_PARAMS.json,WATCHDOG_TRACE.log}`.
  - Progress as of last check (2026-08-07T12:46:23Z): 2,724,038+ manifest entries written, continuous heartbeats every
    1-3 min, `PROGRESS.json` `monotonic:true`. Scan checkpoint `date=2023-01-30` — ~1,125 of ~2,410 target days (~47%)
    after ~14h runtime.
  - **ETA: multi-day, not hours.** Per-day shard density is climbing steeply through the corpus (single-digit/day in
    2020 → ~10,000/day by early 2023), so throughput is slowing as the scan advances — currently ~11 simulated-
    days/hour. At that rate the remaining ~1,285 days (Jan 2023 → today) is a **rough floor of 4-5+ more days**, and
    likely longer since 2024-2026 density is probably equal-or-higher than early 2023, not lower. Treat this as a
    standing, expected condition for the rest of this week, not an imminent unblock.
- Delivery failure (separate finding): `gcloud logging read` on job `uts-prod-alerting-paging`, e.g.
  `2026-08-07T12:29:40.099309Z ERROR PagerDuty delivery failed for event CONSOLIDATOR_DOWN` immediately followed by
  `2026-08-07T12:29:40.099378Z WARNING Email fallback not configured (host='' recipients=0) — skipping send` and
  `ERROR Email fallback ALSO failed for CRITICAL event CONSOLIDATOR_DOWN — undelivered`. No Slack post for the
  `CONSOLIDATOR_DOWN` event itself was found in the same window (only an unrelated `ALERT_DISPATCH_FAILED` for a
  concurrently-processed DP_FLEET_MONITOR_* message — see
  `/plans/active/issues/alerting_service_lifecycle_events_sub_dual_consumer_slack_spam_2026_08_07.md`). This means
  CONSOLIDATOR_DOWN currently has **zero successful delivery channel** for the duration of the rebuild.

## Why this is filed as "known issue," not "fix now"

Per operator instruction 2026-08-07: the consolidator pause is very likely an intentional safety precondition from the
in-flight rebuild VM (canonical-migration scripts require the consolidator cron paused before a manual manifest rewrite,
to avoid racing the scheduled merge) and should NOT be resumed by another session while unconfirmed — resuming it
mid-flight risks racing the VM's own manifest rewrite, a real correctness hazard for someone else's in-progress work. No
direct proof was found in the VM's own logs (pause/resume is a documented human step, never logged by the launcher), so
this is inference from timing + the workspace's own documented operational contract, not a confirmed fact.

## Todos

- [x] ✅ [OPERATOR] P3. **CLOSED 2026-08-09 (stale-check-defi-tranche) — independently confirmed by a separate, same-day
      escalation-triage doc, not by asking the launcher directly.**
      `plans/archive/issues/dp_consolidator_scheduler_paused_defi_recurrence_2026_08_07.md` (escalation agt-ca5798,
      DP-WATCHER-004, filed + resolved 2026-08-07, status: resolved, archived) independently traced this EXACT pause
      (same job, same `2026-08-06T20:16:52Z userUpdateTime`, same `unified-trading-sa` principal) to the SAME rebuild VM
      via live Cloud Audit Logs + the VM's own `run.log` (confirmed RUNNING + actively writing per-VM shards through
      `2026-08-07T00:18:36Z`), correlated it to the owning plan
      (`/plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s R3 relaunch chain), and registered a
      retroactive maintenance window
      (`scheduler_maintenance ... pause --locked-by defi_track01_per_instrument_and_canon_id_2026_07_24 --ttl-minutes 4320`,
      i.e. until 2026-08-10T00:20:24Z) rather than resuming — explicitly naming the deferred resume ("whoever next
      verifies `canonical-migration-defi-rebuild-20260806-223130` completed should resume the cron manually"). This
      satisfies the substance of this todo (confirm intentional + a named resume owner/mechanism) even though it wasn't
      a direct answer from the VM's launcher — treating it as a duplicate confirmation, not re-asking. Todo 2 below
      (verify actual resume once the VM completes) remains the real open item.
- [ ] [SCRIPT] P3. Once the rebuild VM completes/self-deletes, verify the consolidator scheduler was actually resumed
      (state=ENABLED) and `CONSOLIDATOR_DOWN` clears — if it doesn't auto-resume, resume it manually and confirm a real
      consolidator merge cycle runs clean.
- [ ] [SCRIPT] P3. Separately (not blocking): decide whether `CONSOLIDATOR_DOWN`'s routing rule should gain a Slack
      channel so a real (non-known-cause) consolidator outage isn't silently undelivered end-to-end the way this one
      currently is with both PagerDuty and email failing — this is an open design question, not something to change
      unilaterally.

## Progress Log

- 2026-08-07: Filed. Traced pause to the in-flight rebuild VM via timing correlation + documented
  `_assert_consolidator_paused()` pattern; confirmed VM is healthy and actively progressing (not stalled) with a
  realistic multi-day ETA; confirmed PagerDuty+email are both failing to deliver this alert (separate finding, not fixed
  here per operator's PagerDuty-deprecation decision the same day).
- **na-eligibility-audit 2026-08-07** (tranche=defi): KEEP-NA valid — first audit pass, doc filed today. All 3 open
  todos are genuinely non-worker-determinable right now: todo 1 needs the rebuild VM's actual operator to confirm intent
  (OPERATOR_QUESTION); todo 2 is DEPENDENCY_BLOCKED on the rebuild VM's own multi-day (4-5+ day) completion, not yet
  reached; todo 3 is an explicit open alert-routing design question ("not something to change unilaterally"). Doc stays
  `assigned_vm: NA`.
- **stale-check-defi-tranche 2026-08-09**: closed todo 1 by citation — a separate same-day escalation-triage doc
  (`plans/archive/issues/dp_consolidator_scheduler_paused_defi_recurrence_2026_08_07.md`, resolved+archived 2026-08-07)
  independently confirmed the exact same pause/VM correlation this todo asked for, via live Cloud Audit Logs (not just
  timing inference) — see the flipped checkbox above for the full trail. Not independently re-verified live whether the
  rebuild VM has since completed (ETA from 2026-08-07 was 4-5+ more days; only ~2 days have elapsed) — todo 2 stays open
  pending that. Doc stays `assigned_vm: NA` (2 of 3 items still genuinely open).
- **stale-check-defi-tranche 2026-08-09**: closed todo 1 by citation — a separate same-day escalation-triage doc
  (`plans/archive/issues/dp_consolidator_scheduler_paused_defi_recurrence_2026_08_07.md`, resolved+archived 2026-08-07)
  independently confirmed the exact same pause/VM correlation this todo asked for, via live Cloud Audit Logs (not just
  timing inference) — see the flipped checkbox above for the full trail. Not independently re-verified live whether the
  rebuild VM has since completed (ETA from 2026-08-07 was 4-5+ more days; only ~2 days have elapsed) — todo 2 stays open
  pending that. Doc stays `assigned_vm: NA` (2 of 3 items still genuinely open).
- **context-scout 2026-08-09**: populated context_scope (4 entries).
- **na-eligibility-audit 2026-08-09** (tranche=defi): KEEP-NA valid -- 2 open todos, both non-worker-determinable today:
  todo 1 DEPENDENCY_BLOCKED on the in-flight canonical-migration-defi-rebuild VM's multi-day completion (~2 of 4-5+ days
  elapsed); todo 2 an explicit OPERATOR_QUESTION on CONSOLIDATOR_DOWN alert-routing design. Doc stays `assigned_vm: NA`.
