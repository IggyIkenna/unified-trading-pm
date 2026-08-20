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
parent_epic: security_and_cross_cutting_master
priority: P1
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-20
locked_since:
context_scope:
  [
    /codex/05-infrastructure/data-pipeline-alerts.md,
    alerting-service/alerting_service/core/dedup.py,
    deployment-service/deployment_service/data_pipeline_monitors/live_stream_watcher.py,
    /plans/active/issues/dp_cron_did_not_fire_false_positive_burst_2026_08_10.md,
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
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
- **data_pipeline_alerts_reconciler 2026-08-17 (slot 28, dispatch agt-f4501d), follow-up sweep**: fresh ground-truth
  Slack read (`slack-read-channel.py data-pipeline-alerts 24`) found the storm SIGNIFICANTLY WORSE than the earlier
  sweep captured, not resolved: 2993 total messages / 24h (990 `DP_CRON_DID_NOT_FIRE`, 544 `DP_RUN_MOSTLY_EMPTY`, plus
  large VM-churn volume). Attempted the item-2 deploy-chain verification (now tracked as
  `cefi_satellite_ao_dispatch_batch21_2026_08_17.md` item 1):
  1. **Commit content on main**: CONFIRMED — `git show origin/main:alerting_service/core/dedup.py` contains
     `attempted_age_hours` in `_VOLATILE_DETAIL_KEYS` and the `_VOLATILE_DETAIL_KEY_SUFFIXES` tuple.
     `git merge-base --is-ancestor cd60a3e595 origin/main` reports false (expected on a squash-merge promotion PR per
     this skill's own §4 caveat — content-check is the correct test here, not ancestry).
  2. **Live behavioral check**: sampled one identity's fire cadence directly from Slack
     (`HYPERLIQUID`/`derivative_ticker` on `mtds-live-cefi-consolidated-20260817-025031`): fires at 03:21, 04:06
     (45min gap), 04:22 (16min — **violates the 1800s cooldown**), 04:51 (29min), 05:06 (15min — **violates**), 05:36
     (30min), 06:07 (31min), RESOLVED 06:21. The alternating ~30min/~15min pattern is inconsistent with a correctly
     working 1800s dedup cooldown as late as 06:07Z — i.e. ~5h after the fix commit landed on main.
  3. **Cloud Build / Cloud Run provenance**: `gcloud run services describe dp-alerting-subscriber` shows live revision
     `dp-alerting-subscriber-00103-zhw` (100% traffic), created 2026-08-17T00:54:00Z — 12min after the fix commit
     (00:42:49Z), which read as suggestive at first. But `gcloud builds list` (initially run WITHOUT `--region`,
     which silently scopes to the `global` region and misses everything — a methodology error, corrected mid-sweep)
     found no `global`-region build near that time; `gcloud builds triggers list --region=asia-northeast1` located
     the real `alerting-service-build` trigger in that region. A `--region=asia-northeast1` build-history query
     against that trigger returned nothing conclusive on the first pass (a bad `--filter` field name produced a
     "filter key not present" warning rather than a real 0-result answer), but a broader unfiltered regional query
     showed **live build activity for this trigger in the last ~10 minutes of this sweep** (builds `WORKING`/`SUCCESS`
     between 06:36:58Z and 06:43:30Z) — i.e. concurrent with this sweep, not provably tied to `cd60a3e595`.
  4. **Verdict**: items (1) partially confirmed (content on main, ancestry inconclusive as expected), (2) and (3) of
     the skill's §4 three-part check are **NOT conclusively confirmed** — the live-behavior evidence in point 2 leans
     toward "fix not yet effectively live," but I could not pin an exact broken link in the deploy chain with the
     `gcloud` access/permissions available this session (Container Analysis API is disabled on this project, blocking
     image-provenance lookup by label; `containeranalysis.googleapis.com` enablement was not attempted — that's an
     API-enablement action beyond this sweep's proportionate scope to request unprompted). The build activity
     observed in point 3 in the final minutes of this sweep may resolve this on its own; a follow-up sweep should
     re-check the live fire-cadence for the same identity to see if it now respects the 1800s cooldown.
  5. Registry hygiene (§6 of the skill) done separately this sweep: DP-WATCHER-005/006, DP-VM-012, DP-LIVE-001/002/003/004
     transcribed into `data-pipeline-alerts.md` + `.registry.yaml` (were code-registered but doc-stale since
     2026-08-15/16 per this doc's own flagged gap).
  6. **CONFIRMED, not just "leans toward" (re-sampled 06:50Z, after the build activity window closed)**: pulled a
     fresh 1h Slack window and found `mtds-live-cefi-consolidated-20260817-025031`/BYBIT-FUTURES/`book_snapshot_5`
     fired at 06:35Z and again at 06:50Z — exactly 15min apart, a second, cleaner cooldown-violation than point 2's
     sample (no ambiguity from alternating gaps this time), and `derivative_ticker` on the same VM/venue shows the
     same 06:35→06:50 pattern. This is well past the 06:36:58-06:43:30Z build-activity window noted in point 3, so
     that build activity — whatever it was — did NOT fix the live cadence. **Verdict upgraded from "leans toward
     not-live" to CONFIRMED not-live as of 06:50Z, ~6h after the fix commit landed on main.** The deploy-chain break
     is real and current, not a stale/already-resolving observation.
  - Todo 2 (extracted to batch21 item 1) left **unflipped** — the done-when bar ("all 3 conditions confirmed" or "a
    fresh Cloud Build is triggered and its result cited") is not yet met; the next sweep or AO dispatch of that item
    should re-check the live fire-cadence first (cheapest, most direct signal) before re-attempting the build/image
    provenance chase.
- **2026-08-17 (slot 18, backend_engineer craft, task cefi_satellite_ao_dispatch_batch21-5517a0a936a2)**: batch21 item
  1 (the extracted deploy-chain check) now CLOSED — all 3 conditions confirmed with hard evidence (content-on-main;
  Cloud Build `821c691f-8da4-426e-b7b1-9d0614097064` SUCCESS `00:48:57Z`; live revision `dp-alerting-subscriber-00103-zhw`
  @ 100% traffic, container-content-verified via `docker pull`+extract — the running container genuinely has the fix,
  not just the registry tag). The deploy chain was never actually broken. But a fresh live-behavior re-check
  (`06:35Z/06:50Z/07:06Z`) confirms the SAME identity is still firing every 15-16min, ~6h15m post-deploy — a separate,
  unresolved runtime defect (several obvious hypotheses ruled out: singleton deduplicator, minScale=1/maxScale=1,
  correct 1800s constant, no override-function interference, no other volatile field in this emission's details).
  Filed as `/plans/archive/issues/dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective_2026_08_17.md` (P1, 2 new
  todos) for the next dispatch to root-cause — RESOLVED + archived 2026-08-17: root-caused (severity-override on
  resolved bookends bypassing dedup), fixed (`alerting-service@166f291f44`), and live fire-cadence reconfirmed
  1800s-compliant post-fix.
- **na-eligibility-audit 2026-08-17 (re-verify, cefi tranche)** [body-hash:7afccc51e9054fa6]: KEEP-NA, valid — re-confirmed after this morning's extraction (batch21 item 1) closed out and the runtime-defect follow-up resolved + archived separately, leaving exactly the 1 open item already covered by this doc's own earlier na-eligibility-audit marker above. Line 116 ([OPERATOR] P1, investigate the 2 genuine live-capture stalls on BYBIT-FUTURES/CME) OPERATOR_QUESTION — explicit `[OPERATOR]` tag, open-ended production debugging with unknown root cause (auth/API/schema) on live-capture-critical-path VMs. Doc stays assigned_vm: NA.
- **data_pipeline_alerts_reconciler 2026-08-18 (slot 23, dispatch agt-d52c5d)**: REGRESSION — re-sampled the exact identity this doc's own history confirmed 1800s-compliant at `09:06Z/09:36Z` 2026-08-17 and found it firing every 15-17min again as of `01:21Z-02:06Z` 2026-08-18, ~16.5h later. Root-caused to a NEW, distinct cause (not the volatile-field or RESOLVED-bookend bugs already fixed here): Cloud Run revision churn (5 `dp-alerting-subscriber` redeploys in 3.25h, one gap only 17min) wipes `AlertDeduplicator`'s in-memory `_seen` state faster than the 1800s cooldown window. Filed as its own doc rather than reopening this one (the fixes shipped HERE are still correct and still present in the deployed code — verified via `git show origin/main`) — see `/plans/active/issues/dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md` for full evidence + recommended fix (GCS-persist the `_RECURRING_ALERT_COOLDOWNS` subset, mirroring `RenagTracker`).
- **na-eligibility-audit 2026-08-18** [body-hash:4d31b0845c46f9a3]: KEEP-NA, valid — reaffirmed after today's REGRESSION entry
  (dedup-state-lost-on-redeploy, filed separately as its own doc). Sole open item (line 116, [OPERATOR] P1, investigate
  the 2 genuine live-capture stalls on BYBIT-FUTURES/CME) is unaffected by the regression finding — still open-ended
  production debugging with unknown root cause (auth/API/schema), explicit [OPERATOR] tag. Doc stays assigned_vm: NA.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
