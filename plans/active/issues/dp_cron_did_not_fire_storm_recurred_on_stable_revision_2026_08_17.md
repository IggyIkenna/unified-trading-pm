---
doc_type: issue
title: >-
  DP_CRON_DID_NOT_FIRE storm RECURRED on a STABLE (non-redeployed) revision, ~1.5-3h after
  the 09:06-09:36Z fix verification — broader scope now includes DP-LIVE-003, not just DP-LIVE-004.
summary: >-
  6-hourly `/data-pipeline-alerts-reconcile` sweep (2026-08-17, slot 28, dispatch agt-e28b69). Fresh ground-truth
  Slack read (`slack-read-channel.py data-pipeline-alerts 24`, 150 msgs/24h) found `DP_CRON_DID_NOT_FIRE` still the
  dominant event (43 msgs), firing at a ~13-17min cadence for multiple identities as of `11:02Z-12:33Z` — violating
  the registered 1800s cooldown, live, right now. This is the SAME symptom `dp_cron_did_not_fire_dedup_volatile_field_
  2026_08_17.md` / `dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective_2026_08_17.md` (both already
  investigated + closed today by 3 prior dispatches) chased and fixed twice already (`alerting-service@cd60a3e595`
  volatile-field exclusion, then `alerting-service@166f291f44` resolved-bookend severity-override fix) — the second
  fix was CONFIRMED 1800s-compliant via live re-sample at `09:06Z/09:20Z/09:36Z` on revision `dp-alerting-subscriber-
  00105-bkq` (deployed 08:53:51Z). This sweep confirms the storm is back, live, as of `12:33Z` — but with two new
  wrinkles the prior investigations did not have: (1) the recurrence happened on the SAME STABLE revision
  (`-00105-bkq` ran unchanged from 08:53:51Z until a NEW revision `-00106-dqd` deployed at `11:39:14Z`, and the
  storm's fires at `11:02Z`/`11:05Z`/`11:20Z`/`11:36Z`/`11:48Z` all predate that redeploy) — this RULES OUT
  "redeploy wiped in-memory dedup state" as the explanation for THIS occurrence, unlike every hypothesis the prior 2
  docs checked (which all assumed a stable process); (2) the storm now also includes `DP-LIVE-003`
  (`missing_live_producer_watcher.py`'s LONG_LIVED_LIVE producer-prefix check, `EscalationTier.PAGE_OPERATOR`) for
  prefixes `mdps-features-live-tradfi-` and `prediction-arb-detector-` — a DIFFERENT emit call site than the
  previously-fixed `DP-LIVE-004` (`live_stream_watcher.check_live_capture_productivity`), sharing only the event
  name `DP_CRON_DID_NOT_FIRE` and the router-level cooldown map entry, not the code path. Both identity classes'
  `details` dicts were checked against `alerting-service/alerting_service/core/dedup.py`'s current
  `_VOLATILE_DETAIL_KEYS`/`_VOLATILE_DETAIL_KEY_SUFFIXES` and contain no unexcluded volatile field (DP-LIVE-003's
  `asset_group`/`vm_prefix`/`lifecycle_class` are all constant per prefix). Separately, the service has been
  redeployed unusually often today (10 revisions in ~18h, `-00098` through `-00107`, several within the last 2h,
  most recently `-00107-t97` at `12:36:59Z`) — itself worth a look (each redeploy IS a genuine, if partial, cause of
  cooldown-violating re-fires, just not the cause of THIS specific pre-redeploy occurrence) but not chased further
  this sweep (proportionate-scope: root-causing an in-memory-state-degrading-over-time bug needs the same live
  Cloud-Logging trace depth the prior 2 docs each spent a full dispatch on).
status: open
nature: issue
asset_group: [cefi, tradfi, cross-cutting] # was [cefi, tradfi] — fleet-wide alerting_service dedup-layer defect (parent_epic: security_and_cross_cutting_master), matches its most-similar sibling dp_cron_did_not_fire_dedup_state_lost_on_redeploy_2026_08_18.md's [cefi, tradfi, cross-cutting] tagging (reconciled per ag_closeout_audit_tradfi_parked_2026_08_19.md's classification-inconsistency finding)
stage: [live]
repos: [alerting-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    data-pipeline-alerts,
    dp-live-003,
    dp-live-004,
    dp-cron-did-not-fire,
    alert-dedup,
    alerting-service,
    live-capture-stall,
    deploy-churn,
  ]
related:
  [
    /plans/active/issues/dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md,
    /plans/archive/issues/dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective_2026_08_17.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-08-17
author: data_pipeline_alerts_reconciler (slot 28, one-shot dispatch agt-e28b69)
parent_epic: security_and_cross_cutting_master
priority: P1
milestone: M3
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
assigned_role:
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
last_updated: 2026-08-18
locked_since:
context_scope:
  [
    /plans/active/issues/dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md,
    /plans/active/cefi_satellite_ao_dispatch_batch21_2026_08_17.md,
    alerting-service/alerting_service/core/dedup.py,
    alerting-service/alerting_service/notifiers/router.py,
    deployment-service/deployment_service/data_pipeline_monitors/missing_live_producer_watcher.py,
    deployment-service/deployment_service/data_pipeline_monitors/live_stream_watcher.py,
  ]
source: >-
  6-hourly data_pipeline_alerts_reconciler dispatch (agt-e28b69, 2026-08-17, slot 28), running the
  /data-pipeline-alerts-reconcile skill's mandatory ground-truth Slack read + registry cross-check + live-infra
  cross-check.
---

# DP_CRON_DID_NOT_FIRE storm recurred on a stable revision — broader scope than previously fixed

## What was found (ground truth, this sweep)

`slack-read-channel.py data-pipeline-alerts 24` (150 msgs/24h) + a follow-up 1h re-pull, both 2026-08-17:

- `DP_CRON_DID_NOT_FIRE=43`, `DP_RUN_MOSTLY_EMPTY=36`, `DP_VM_PREEMPTED=32`, `DP_VM_PREEMPTED_NO_RELAUNCH=11`,
  `DP_VM_EXIT_NONZERO=9`, `DP_DIVERGENT_EMPTY=7`, `DP_VM_PREEMPTED_RECOVERED=4`, `DP_SHARD_PILLAR_FAIL=3`,
  `DP_PHANTOM_ROWS=3`. Only 13 RESOLVED bookends in the 24h window.
- `DP_CRON_DID_NOT_FIRE` fire timestamps for the two dominant identity families, 1h re-pull confirms it is
  CURRENTLY firing every ~13-17min (well under the registered 1800s/30min cooldown):
  - `LONG_LIVED_LIVE producer prefix 'mdps-features-live-tradfi-'` / `'prediction-arb-detector-'` (DP-LIVE-003,
    `missing_live_producer_watcher.py`): `11:05Z, 11:20Z, 11:36Z, 11:48Z, 12:03Z, 12:20Z, 12:33Z`.
  - `DP-LIVE-004` shards (`mtds-live-cefi-consolidated-20260817-025031`/BYBIT-FUTURES all 5 data_types;
    `mtds-live-tradfi-cme-trades-20260809-163443`/CME trades): same cadence, same window.

## Why this is a DIFFERENT finding from the 2 already-closed docs today, not a re-report

Both `dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md` (dedup identity-hash fix,
`alerting-service@cd60a3e595`) and the archived `dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective_2026_08_17.md`
(resolved-bookend severity-override fix, `alerting-service@166f291f44`) chased this exact symptom today and each
closed with a CONFIRMED-compliant live re-sample — the second one specifically at `09:06Z/09:20Z/09:36Z` on revision
`dp-alerting-subscriber-00105-bkq`.

Two things this sweep found that neither prior doc had:

1. **The storm's `11:02Z-11:48Z` fires all happened on the SAME revision** (`-00105-bkq`, deployed `08:53:51Z`) —
   the next revision (`-00106-dqd`) didn't deploy until `11:39:14Z`, and the storm was already underway before that.
   `gcloud run revisions list --service=dp-alerting-subscriber --region=asia-northeast1`:
   ```
   dp-alerting-subscriber-00107-t97  2026-08-17T12:36:59Z
   dp-alerting-subscriber-00106-dqd  2026-08-17T11:39:14Z
   dp-alerting-subscriber-00105-bkq  2026-08-17T08:53:51Z   <- storm's 11:02-11:48Z fires ran on THIS revision
   dp-alerting-subscriber-00104-pwq  2026-08-17T08:09:15Z
   ```
   This rules out "a fresh deploy wiped the in-memory `AlertDeduplicator._seen` dict" as the explanation for THIS
   occurrence — a hypothesis neither prior doc needed to consider because neither observed a stable-revision
   recurrence. The dedup state degraded (or a repeat slipped past it) WITHIN a single long-running process, roughly
   2-3h after being confirmed compliant on that exact process.
2. **A second registry id is now affected**: `DP-LIVE-003` (`missing_live_producer_watcher.py:227`,
   `EscalationTier.PAGE_OPERATOR`) emits the identical `DP_CRON_DID_NOT_FIRE` event name via a DIFFERENT call site
   than the previously-fixed `DP-LIVE-004` (`live_stream_watcher.check_live_capture_productivity`). Its `details`
   dict (`asset_group`, `vm_prefix`, `lifecycle_class` — all constant per prefix, checked against the current
   `_VOLATILE_DETAIL_KEYS`/`_VOLATILE_DETAIL_KEY_SUFFIXES` in `dedup.py`) has no unexcluded volatile field, so this
   is not a re-occurrence of the ORIGINAL `attempted_age_hours` bug either. Both identity families are firing on the
   same cadence, suggesting a shared, generic dedup-layer defect (something in `router.py`'s `is_duplicate()` call
   path or `_evict_expired`), not a per-detector `details`-shape bug.

## Separately worth a look: unusually high deploy churn today

`dp-alerting-subscriber` has deployed 10 times in ~18h (`-00098` @ `2026-08-16T18:13Z` through `-00107` @
`2026-08-17T12:36:59Z`), several within the last 2h. This is a real, independent finding — even a CORRECT dedup
implementation gets defeated every time the single `minScale=1/maxScale=1` instance restarts (fresh process = empty
`_seen` dict), and today's chase-fix-deploy-verify cycle for this exact bug is itself generating much of that churn.
Not chased further this sweep (proportionate scope), but the next investigation should check whether a stray
CI/CD trigger (e.g. an unrelated repo change re-triggering `alerting-service-build`) is ALSO contributing beyond the
deliberate fix-deploys.

## What was NOT re-attempted this sweep (proportionate scope)

A full live Cloud-Logging trace (the depth `dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective_2026_08_17.md`'s
slot-24 root-cause pass used — pulling `ALERT_ROUTED`/`ALERT_SENT` log lines directly) was not repeated here; this
sweep is a bounded reconciliation pass, not an open-ended runtime investigation, and that trace-level work is best
done by a dedicated follow-up dispatch with the evidence above as its starting point (candidates: does
`_evict_expired`/`is_duplicate` have a bug that fires under sustained insert volume over ~2-3h; is there a SECOND
delivery path for `DP-LIVE-003` specifically that bypasses `_deduplicator.is_duplicate()`; does the deploy-churn
itself explain more of the window than the timestamp cross-check above suggests once exact per-fire timestamps are
checked against exact revision-swap timestamps to the second).

## Todos

- [ ] [SCRIPT] P1. Root-cause why `DP_CRON_DID_NOT_FIRE`'s 1800s cooldown, confirmed compliant at `09:06-09:36Z` on
      revision `dp-alerting-subscriber-00105-bkq`, was violated again on the SAME stable revision by `11:02Z` (~1.5h
      later, no redeploy in between) — start from a live Cloud-Logging `ALERT_ROUTED`/`ALERT_SENT` trace for the
      `mdps-features-live-tradfi-` (DP-LIVE-003) identity specifically, since it's a new call site the prior 2 fixes
      never examined. (repo: alerting-service)
- [ ] [SCRIPT] P2. Once root-caused, re-sample live fire-cadence for BOTH DP-LIVE-003 and DP-LIVE-004 identities to
      confirm 1800s compliance, then close this doc. (repo: alerting-service)
- [ ] [SCRIPT] P3. Check whether `dp-alerting-subscriber`'s 10-deploys-in-18h churn today has a cause beyond the
      deliberate dedup-bug fix-deploy cycle (stray trigger, unrelated repo change re-triggering the same Cloud Build
      trigger). (repo: alerting-service)
- [x] ✅ [SCRIPT] P1. Promote `route_event()`'s DEBUG-only "Duplicate alert suppressed" log to a structured
      `log_event("ALERT_DEDUPLICATED", ...)` call (both call sites, `router.py`) so a future Cloud-Logging trace can
      actually see suppression, not just delivery — additive-only, no behavior change, QG-green.
      Evidence: `alerting-service@4135b078cd`, ancestry-verified against `origin/live-defi-rollout`.

## Progress Log

- 2026-08-17: `data_pipeline_alerts_reconciler` (slot 28, dispatch agt-e28b69) ran the 6-hourly
  `/data-pipeline-alerts-reconcile` sweep. Ground-truth Slack read + a targeted 1h re-pull confirmed
  `DP_CRON_DID_NOT_FIRE` is CURRENTLY firing every ~13-17min for `DP-LIVE-003` + `DP-LIVE-004` identities, live, as
  of `12:33Z` — despite 2 prior fixes today each confirmed 1800s-compliant on live re-samples. Cross-checked against
  `gcloud run revisions list` to establish the storm's `11:02-11:48Z` fires ran on the SAME stable revision the
  prior fix was verified on, ruling out simple redeploy-state-reset for this occurrence and narrowing scope to a
  genuine in-process dedup-layer defect plus a newly-affected second call site (`DP-LIVE-003`). Filed this issue
  rather than re-attempting the full live-trace root-cause (proportionate to a one-shot bounded sweep) — flagged P1
  for the next dispatch.
- **na-eligibility-audit 2026-08-17 (cefi tranche, first audit pass)** [body-hash:49b09b47e001d79a]: KEEP-NA, valid — fresh doc (created today), no prior marker. All 3 open items are open-ended live-system root-cause investigation (a recurring DP_CRON_DID_NOT_FIRE storm whose two prior same-day fixes both independently verified compliant then regressed) — GENUINE_WORK, not bounded/deterministic. This doc's population is worked by the data_pipeline_alerts_reconciler's own 6-hourly scheduled sweep, not generic AO backlog dispatch. Doc stays assigned_vm: NA.
- **na-eligibility-audit 2026-08-18 (cefi tranche, re-verify)** [body-hash:dc7d6fe93a6fb8da]: KEEP-NA, valid — reaffirmed after the 2026-08-18 `data_pipeline_alerts_reconciler` follow-up sweep (slot 23) shipped the observability fix (`alerting-service@4135b078cd`, now [x]) and added new investigation findings without root-causing the actual TTL violation. All 3 remaining open items stay genuinely NA: P1 root-cause is open-ended live-system investigation (GENUINE_WORK — several hypotheses now ruled out, no confirmed cause yet), P2 re-sample is DEPENDENCY_BLOCKED on P1 completing first, P3 deploy-churn check is GENUINE_WORK and explicitly proportionate-scope-deferred. Still owned by the data_pipeline_alerts_reconciler's 6-hourly sweep, not generic AO backlog dispatch. Doc stays assigned_vm: NA.
- **context-scout 2026-08-17**: refreshed context_scope (6 entries, unchanged count) — fingerprint match:
  `alerting-service@cd60a3e595` and revision `dp-alerting-subscriber-00103-zhw`/build
  `821c691f-8da4-426e-b7b1-9d0614097064` (this doc's cited first-fix evidence) also appear in
  `plans/active/cefi_satellite_ao_dispatch_batch21_2026_08_17.md`'s item 1 (independently verified the same
  deploy-chain that day); swapped in as a 2nd entry, dropping the now-redundant archived
  `dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective_2026_08_17.md` (its content is already fully re-narrated
  in this doc's own "What was found" section above).
- **data_pipeline_alerts_reconciler 2026-08-18 (slot 23, dispatch agt-c5c423), follow-up sweep**: fresh ground-truth
  Slack read (`slack-read-channel.py data-pipeline-alerts 24`, full 24h window = 1868 msgs, not just the 200-line
  tail) confirms the storm is STILL LIVE as of `01:36Z` today — `DP_CRON_DID_NOT_FIRE=766` msgs/24h, 414 of them for
  a single identity family on `mtds-live-cefi-consolidated-20260817-025031` (BYBIT-FUTURES trades/derivative_ticker/
  book_snapshot_5/depth_of_book_10 + ASTER liquidations), gap pattern for BYBIT-FUTURES/trades over 65 fires:
  alternating short (~14-16min) and near-compliant (~29-31min) gaps — i.e. roughly every OTHER sweep leaks past the
  1800s cooldown, not a total dedup bypass. New findings this pass, none conclusive enough to ship a fix on:
  1. **Confirmed single stable Cloud Run instance for the CURRENT window**: `gcloud logging read` for revision
     `dp-alerting-subscriber-00113-2vg` (deployed `00:55:55Z`) over the prior 6h returned exactly 1 distinct
     `run.googleapis.com/instanceId` across 3000 log lines — rules out mid-window instance recycling as the
     explanation for at least this window's leaks (same negative result the prior dispatch got for its own window;
     the "recurs every 1.5-3h on a stable revision" mechanism is still unexplained).
  2. **uvicorn runs with no `--workers` flag** (`Dockerfile` CMD: `uvicorn alerting_service.api.main:app --host 0.0.0.0
     --port 8080`) — single process confirmed, ruling out a multi-worker-process split of the `_deduplicator` module
     singleton as the cause.
  3. **`_dedup_window_for` verified NOT the culprit**: traced `dp_run_mostly_empty_static_backlog.dedup_window_override`
     — it only special-cases `DP_RUN_MOSTLY_EMPTY`; for `DP_CRON_DID_NOT_FIRE` it falls straight through to the
     caller's `default` (`_RECURRING_ALERT_COOLDOWNS["DP_CRON_DID_NOT_FIRE"] = 1800.0`), so the effective TTL is not
     silently degrading to the deduplicator's 60s fallback via this path.
  4. **Real observability gap found and NOT yet fixed**: `route_event()`'s suppression branch
     (`alerting_service/notifiers/router.py`) logs via bare `logger.debug("Duplicate alert suppressed: %s", event_name)`
     — Python-stdlib DEBUG level, not the structured `log_event()` used for `ALERT_ROUTED`/`ALERT_SENT`/etc. Cloud Run's
     default log level does not surface DEBUG, so **every suppressed alert is invisible in Cloud Logging** — a live
     Cloud-Logging trace (as P1's todo below prescribes) can prove when an alert WAS delivered but cannot distinguish
     "0% suppression happening" from "90% suppression happening, we only see the 10% that leak" without this fixed
     first. Recommend the next dispatch promote this one suppression log line to a structured `log_event("ALERT_
     DEDUPLICATED", ...)` (mirroring `ALERT_COALESCED`'s pattern already in the same function) BEFORE attempting the
     P1 root-cause trace — otherwise the trace is working with an artificially incomplete picture, same failure mode
     this doc's own point 2 already hit once when a `--region` omission produced a false "no results" read.
  5. Shipped the point-4 observability fix only (`alerting-service@4135b078cd`) — no candidate root-cause
     explanation for the actual TTL-violation reached the confidence bar `does_not: guess at an ambiguous fix`
     requires, so no behavioral change was attempted. The root-cause todo (P1 below) stays open for the next
     dispatch, now with `ALERT_DEDUPLICATED` events available for its Cloud-Logging trace. Storm classification
     unchanged: § 1(b) routing/dedup bug, in-process, not a live-infra failure — both flagged live-capture-stall VMs
     are a SEPARATE, already-tracked `[OPERATOR]` item in the sibling doc
     `dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md`.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
