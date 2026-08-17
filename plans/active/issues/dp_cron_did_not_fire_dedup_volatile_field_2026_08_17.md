---
doc_type: issue
title: >-
  DP_CRON_DID_NOT_FIRE (DP-LIVE-004) alert storm — attempted_age_hours defeated the alert
  dedup cooldown every sweep; fixed. 2 genuine live-capture stalls remain, flagged for operator.
summary: >-
  6-hourly `/data-pipeline-alerts-reconcile` sweep (2026-08-17) found 150 Slack messages in the last 24h in
  `#data-pipeline-alerts`, dominated by 69 `DP_CRON_DID_NOT_FIRE` (DP-LIVE-004, `live_stream_watcher.
  check_live_capture_productivity`) pages firing every ~15min sweep for the same 2 live VMs
  (`mtds-live-cefi-consolidated-20260814-041422` / BYBIT-FUTURES all 5 data_types, and
  `mtds-live-tradfi-cme-trades-20260809-163443` / CME trades). Root cause: the detector's `details` dict includes
  `attempted_age_hours` (recomputed every sweep), which was NOT in `AlertDeduplicator._VOLATILE_DETAIL_KEYS`'
  exact-match exclusion set — the climbing value changed the identity hash every sweep, defeating the registered
  1800s `DP_CRON_DID_NOT_FIRE` cooldown entirely for this detector (classification: routing/dedup bug, not a live
  infra failure). Fixed in `alerting-service` (`core/dedup.py`): added `attempted_age_hours` to the exact-match set
  plus a generic `*_age_hours`/`*_age_days`/`*_age_minutes`/`*_age_seconds` suffix exclusion so a future detector's
  own age-field name can't reproduce the same bug class. 2 new regression tests added.

  Both VMs are confirmed `RUNNING` (`gcloud compute instances list`) — this is NOT a VM-down issue. The underlying
  condition itself (BYBIT-FUTURES capture unproductive on `mtds-live-cefi-consolidated-20260814-041422`; CME trades
  last captured 5.0d ago on `mtds-live-tradfi-cme-trades-20260809-163443`) is a REAL, currently-live production gap
  that the dedup fix does not resolve — it only stops the page storm; the underlying condition will still page once
  per 30-min cooldown until fixed. That investigation (why is the live capture process on these 2 running VMs not
  producing rows) is out of scope for this sweep — flagged here for operator/next dispatch.
status: open
nature: issue
asset_group: [cefi, tradfi]
stage: [live]
repos: [alerting-service, deployment-service]
scope: [engineer, admin]
tags: [data-pipeline-alerts, dp-live-004, dp-cron-did-not-fire, alert-dedup, alerting-service, live-capture-stall]
related:
  [
    /plans/active/issues/dp_cron_did_not_fire_false_positive_burst_2026_08_10.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-08-17
author: data_pipeline_alerts_reconciler (slot 9, one-shot dispatch agt-112bed)
parent_epic: infrastructure_master
priority: P1
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-17
locked_since:
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    alerting-service/alerting_service/core/dedup.py,
    deployment-service/deployment_service/data_pipeline_monitors/live_stream_watcher.py,
  ]
source: >-
  6-hourly data_pipeline_alerts_reconciler dispatch (agt-112bed, 2026-08-17), running the
  /data-pipeline-alerts-reconcile skill's mandatory ground-truth Slack read + registry cross-check.
---

# DP_CRON_DID_NOT_FIRE (DP-LIVE-004) dedup-defeat + 2 real live-capture stalls

## What was found

`slack-read-channel.py data-pipeline-alerts 24` returned 150 messages / 24h:
`DP_CRON_DID_NOT_FIRE=69`, `DP_RUN_MOSTLY_EMPTY=44`, `DP_VM_EXIT_NONZERO=24`, `DP_VM_PREEMPTED=8`,
`DP_VM_PREEMPTED_RECOVERED=3`, `DP_VM_PREEMPTED_NO_RELAUNCH=1`, `DP_VM_GONE_NO_CAPTURE=1`. Only 2 RESOLVED bookends
in the window. The `DP_CRON_DID_NOT_FIRE` messages traced to exactly 2 VMs, refiring every ~15min sweep
(23:06/23:21/23:36/23:51/00:06/00:20/00:36Z), 5 data_types on the BYBIT-FUTURES VM + 1 on the CME VM per sweep —
matching § 1(b)'s "same condition re-fires every tick" bug class, not 69 independent incidents.

## Root cause

`deployment_service/data_pipeline_monitors/live_stream_watcher.py::check_live_capture_productivity` (DP-LIVE-004)
emits `details={"attempted_age_hours": attempted_age_hours, ...}` — a value recomputed fresh every sweep. The
`AlertDeduplicator._VOLATILE_DETAIL_KEYS` set (`alerting-service/alerting_service/core/dedup.py`) excludes render-only
fields from the identity hash, but only via exact key-name match (`age`, `age_hours`, `heartbeat_age`, etc.) — it did
NOT list `attempted_age_hours`. Every sweep's differing value therefore changed the SHA256 identity hash, so
`_deduplicator.is_duplicate()` never returned `True` for this detector — the registered 1800s cooldown for
`DP_CRON_DID_NOT_FIRE` (`_RECURRING_ALERT_COOLDOWNS` in `router.py`) was a complete no-op for DP-LIVE-004's emit path.

## Fix — shipped

`alerting-service@cd60a3e595` (landed `live-defi-rollout`, ancestry-verified against origin):
- Added `attempted_age_hours` to `_VOLATILE_DETAIL_KEYS`.
- Added a new `_VOLATILE_DETAIL_KEY_SUFFIXES` tuple (`_age_hours`/`_age_days`/`_age_minutes`/`_age_seconds`) and a
  suffix check in `_make_key`, so any future detector's own differently-named age field is excluded too.
- 2 new regression tests in `tests/unit/test_dedup.py`
  (`test_attempted_age_hours_does_not_break_dedup`, `test_generic_age_suffix_fields_are_volatile`).
- Evidence: `quality-gates.sh --no-fix` ALL PASSED (56s), sentinel `6d67e1a43994aeb8284c7b193c4648d72024fbf0`.

## NOT yet live-verified (§4 deploy-chain check) — flagged, not closed

This sweep's one-shot window did not extend to confirming the fix reached the LIVE `dp-alerting-subscriber` Cloud Run
revision (LDR → main promotion via `ldr-to-main-promote-fleet.yml` + a fresh Cloud Build/deploy still need to run).
Per the skill's § 4, do not consider the alert storm "fixed" until:
1. `alerting-service@cd60a3e595` (or later) is confirmed on `origin/main`.
2. A fresh Cloud Build ran against that content.
3. `dp-alerting-subscriber`'s `status.latestReadyRevisionName` is the fresh revision AND carries 100% traffic.

## Real, unresolved production finding — separate from the alerting bug

Both flagged VMs are confirmed `RUNNING` right now (`gcloud compute instances list`, 2026-08-17):
- `mtds-live-cefi-consolidated-20260814-041422` — BYBIT-FUTURES capture unproductive across all 5 live data_types
  (`trades`, `derivative_ticker`, `book_snapshot_5`, `depth_of_book_10`) despite the VM actively attempting.
- `mtds-live-tradfi-cme-trades-20260809-163443` — CME trades last captured 5.0d ago, staleness budget 3d.

The dedup fix above only stops the SPAM (69 messages → ~1 page per 30-min window per condition); it does not fix the
underlying capture stall. Investigating why these 2 running VMs aren't producing rows (auth/API/schema/adapter issue
on the live capture process itself) is out of scope for this reconciliation sweep.

## Todos

- [x] ✅ [SCRIPT] P1. Fix `AlertDeduplicator` to exclude `attempted_age_hours` + generic `*_age_*` suffix fields from
      the identity hash. Evidence: `alerting-service@cd60a3e595`.
- [x] ✅ EXTRACTED — see `plans/active/cefi_satellite_ao_dispatch_batch21_2026_08_17.md` item 1 (na-eligibility-audit
      2026-08-17, cefi tranche, conflict-checked clear). Original: [SCRIPT] P2. Confirm the fix reached the live
      `dp-alerting-subscriber` Cloud Run revision (deploy-chain check: main ancestry, fresh Cloud Build,
      `latestReadyRevisionName` + traffic=100%) on the next `data_pipeline_alerts_reconciler` sweep or a manual check.
- [ ] [OPERATOR] P1. Investigate the 2 genuine live-capture stalls (BYBIT-FUTURES on
      `mtds-live-cefi-consolidated-20260814-041422`; CME trades on `mtds-live-tradfi-cme-trades-20260809-163443`) —
      both VMs running, both actively attempting, neither producing rows. Needs a look at the live capture
      process/adapter itself (auth, upstream API change, schema mismatch), not a VM relaunch.

## Progress Log

- 2026-08-17: `data_pipeline_alerts_reconciler` (slot 9, dispatch agt-112bed) ran the 6-hourly
  `/data-pipeline-alerts-reconcile` sweep. Ground-truth Slack read (150 msgs/24h) + registry cross-check identified
  the `DP_CRON_DID_NOT_FIRE` refire storm, root-caused it to a dedup-identity-hash bug (`attempted_age_hours` not
  excluded), fixed + shipped `alerting-service@cd60a3e595` with regression tests, and flagged the 2 real underlying
  live-capture stalls this fix does not resolve.
- **na-eligibility-audit 2026-08-17** [body-hash:26ce733728bec47c]: RECLASSIFY-SPLIT — extracted bounded item 2 (deploy-chain verification) to `cefi_satellite_ao_dispatch_batch21_2026_08_17.md` item 1, conflict-checked clear (no other active doc claims this ground). Item 3 ([OPERATOR] live-capture-stall investigation) stays genuinely NA — open-ended production debugging with unknown root cause, kept at lower confidence given the doc's own [OPERATOR] tag rather than reclassified outright. Doc stays assigned_vm: NA for that remaining item.
