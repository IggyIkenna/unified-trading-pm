---
doc_type: issue
title: >-
  DP_CRON_DID_NOT_FIRE dedup fix — deploy chain CONFIRMED clean (all 3 conditions met), but the
  1800s cooldown is STILL violated live (~6h post-deploy) — a separate, unresolved runtime defect.
summary: >-
  Follow-up to `dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md` item 2 (extracted to
  `cefi_satellite_ao_dispatch_batch21_2026_08_17.md` item 1). That item's 3-part deploy-chain check is now
  CONCLUSIVELY CONFIRMED: (1) `origin/main:alerting_service/core/dedup.py` carries `attempted_age_hours` in
  `_VOLATILE_DETAIL_KEYS` + the `_VOLATILE_DETAIL_KEY_SUFFIXES` tuple; (2) Cloud Build `821c691f-8da4-426e-b7b1-9d0614097064`
  (region `asia-northeast1`, trigger `alerting-service-build`) SUCCEEDED at `2026-08-17T00:48:57Z`, producing
  `alerting-service` image `sha256:6a513332d17214fb5cbae9d4328e3f6021d0f79d3e34cd5c0e8dba0676d9809a` tagged
  `0.63.36,a545ea9,latest` (matching `origin/main`'s tip commit); (3) `dp-alerting-subscriber`'s
  `status.latestReadyRevisionName` is `dp-alerting-subscriber-00103-zhw` (created `2026-08-17T00:54:00Z`, running that
  exact image digest) at 100% traffic — verified by `docker pull` + extracting `core/dedup.py` directly from the running
  image (confirmed the fix's source is actually present in the deployed container, not just Artifact Registry metadata).
  Despite this, a fresh live-behavior check (Slack `data-pipeline-alerts`, `08-17 06:35Z/06:50Z/07:06Z`) shows
  `mtds-live-cefi-consolidated-20260817-025031`/BYBIT-FUTURES/`book_snapshot_5`+`derivative_ticker` STILL firing every
  15-16 minutes — the same cooldown-violation pattern the prior sweep (agt-f4501d) found at 06:35-06:50Z, now confirmed
  to persist a further cycle to 07:06Z, ~6h15m after the fix commit landed. Checked and RULED OUT as causes: per-request
  deduplicator re-instantiation (`_deduplicator` is a `router.py` MODULE-LEVEL singleton, not per-call); horizontal
  multi-instance fragmentation (`dp-alerting-subscriber` is `minScale=1, maxScale=1`); wrong cooldown constant
  (`_RECURRING_ALERT_COOLDOWNS["DP_CRON_DID_NOT_FIRE"] == 1800.0`, confirmed in the deployed source); the
  DP_RUN_MOSTLY_EMPTY static-backlog override function (`dedup_window_override` falls through to the caller's default
  unchanged for any non-static-backlog event, confirmed by reading `dp_run_mostly_empty_static_backlog.py`); an
  unaccounted-for volatile field in DP-LIVE-004's own `details` dict (`live_stream_watcher.py` lines ~538-547 — every
  field other than the now-excluded `attempted_age_hours` is stable: `label`/`vm_name`/`venue`/`data_type`/`bucket` are
  constant per shard, `last_captured_at` is `None` for a "never captured" shard and does not change sweep-to-sweep).
  None of these explain the observed behavior — the actual mechanism (instance recycling between sweeps, a delivery
  path that bypasses `route_event`'s `is_duplicate()` gate, a Pub/Sub redelivery quirk, or something not yet examined)
  needs a fresh, deeper investigation. Flagged for next dispatch — this is a live, currently-firing production alert
  storm (CRITICAL severity, paging every ~15min instead of every 30min), not a stale/theoretical concern.
status: resolved
nature: issue
asset_group: [cefi, tradfi]
stage: [live]
repos: [alerting-service, deployment-service]
scope: [engineer, admin]
tags:
  [
    data-pipeline-alerts,
    dp-live-004,
    dp-cron-did-not-fire,
    alert-dedup,
    alerting-service,
    live-capture-stall,
    deploy-verification,
  ]
related:
  [
    /plans/active/issues/dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md,
    /plans/active/cefi_satellite_ao_dispatch_batch21_2026_08_17.md,
    /codex/05-infrastructure/data-pipeline-alerts.md,
  ]
created: 2026-08-17
author: data_engineering worker (slot 18, backend_engineer craft task cefi_satellite_ao_dispatch_batch21-5517a0a936a2)
parent_epic: infrastructure_master
priority: P1
assigned_vm: planning
execution_scope: orchestrator-agent
estimate_class: infra
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by: slot 10, backend_engineer craft, task dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective-3243f3d899f0
last_updated: 2026-08-17
locked_since:
context_scope:
  [
    alerting-service/alerting_service/notifiers/router.py,
    alerting-service/alerting_service/core/dedup.py,
    deployment-service/deployment_service/data_pipeline_monitors/live_stream_watcher.py,
    /plans/active/issues/dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md,
  ]
source: >-
  Deploy-chain verification for `cefi_satellite_ao_dispatch_batch21_2026_08_17.md` item 1 (na-eligibility-audit
  extraction of `dp_cron_did_not_fire_dedup_volatile_field_2026_08_17.md` item 2), performed by a backend_engineer-craft
  data_engineering worker (slot 18).
---

# DP_CRON_DID_NOT_FIRE dedup fix — deploy chain clean, live behavior still broken

## What was found

**Deploy chain — CONFIRMED CLEAN, all 3 conditions met (closes batch21 item 1's done-when bar):**

1. **Content on `origin/main`**: `git show origin/main:alerting_service/core/dedup.py` contains `attempted_age_hours`
   in `_VOLATILE_DETAIL_KEYS` and the `_VOLATILE_DETAIL_KEY_SUFFIXES` tuple. (`git merge-base --is-ancestor cd60a3e595
   origin/main` reports false — expected on a squash-merge promotion PR per the prior sweep's own §4 caveat; content
   match is the correct substitute test.)
2. **Fresh Cloud Build**: `gcloud builds list --region=asia-northeast1` — build `821c691f-8da4-426e-b7b1-9d0614097064`,
   `SUCCESS`, `createTime=2026-08-17T00:48:57Z`, produced `alerting-service:latest`. Cross-checked against Artifact
   Registry (`gcloud artifacts docker images list ... --include-tags`): the resulting digest
   `sha256:6a513332d17214fb5cbae9d4328e3f6021d0f79d3e34cd5c0e8dba0676d9809a` carries tags `0.63.36`, `a545ea9`
   (matching `origin/main`'s current tip commit), `latest`.
3. **Live revision + traffic**: `gcloud run services describe dp-alerting-subscriber --region=asia-northeast1` —
   `status.latestReadyRevisionName = dp-alerting-subscriber-00103-zhw`, 100% traffic, `metadata.creationTimestamp =
   2026-08-17T00:54:00Z`, running `spec.containers[0].image` == the exact digest from (2).
4. **Container-content ground-truth (beyond registry metadata)**: `docker pull` + `docker run --entrypoint cat` against
   that exact image digest confirms `/app/alerting-service/alerting_service/core/dedup.py` inside the RUNNING
   container actually contains the fix (not just the Artifact Registry tag pointing there in principle). Also
   confirmed a second, unrelated `gateway/dedup.py` exists in the same image (incident-gateway `incident_key` hashing —
   a completely different mechanism, not a candidate for the bug).

**Live behavior — STILL BROKEN, ~6h15m after the fix deployed:**

Fresh `slack-read-channel.py data-pipeline-alerts 3` read, filtered to the exact identity the prior sweep (agt-f4501d)
sampled: `mtds-live-cefi-consolidated-20260817-025031` / `BYBIT-FUTURES` / `book_snapshot_5` + `derivative_ticker`
fired at `06:35Z`, `06:50Z` (15min gap), `07:06Z` (16min gap) — three consecutive sweeps, no suppressed cycle in
between. This is the SAME 1800s-cooldown violation the prior sweep found at `06:35→06:50Z`, now confirmed to continue
through a further cycle. No RESOLVED bookend for this identity anywhere in the sampled window.

## Hypotheses checked and RULED OUT

- **Per-call re-instantiation of `AlertDeduplicator`** — `alerting_service/notifiers/router.py:68`:
  `_deduplicator = AlertDeduplicator(ttl_seconds=60.0)` is a MODULE-LEVEL singleton, not created per-request. Ruled out.
- **Horizontal multi-instance fragmentation** — `gcloud run services describe` shows
  `autoscaling.knative.dev/minScale: '1'` and `maxScale: '1'`. A single, persistent instance; no cross-instance
  dedup-state fragmentation possible. Ruled out.
- **Wrong/stale cooldown constant** — `_RECURRING_ALERT_COOLDOWNS["DP_CRON_DID_NOT_FIRE"] == 1800.0`, confirmed present
  in the exact deployed source (extracted from the running container, not just the repo checkout). Ruled out.
- **`_dedup_window_for`'s STATIC BACKLOG override clobbering the window** — `dedup_window_override()`
  (`dp_run_mostly_empty_static_backlog.py`) only special-cases `DP_RUN_MOSTLY_EMPTY`; for every other event name
  (including `DP_CRON_DID_NOT_FIRE`) it falls through to the caller's `default` (1800.0) unchanged. Ruled out.
- **A remaining volatile field in DP-LIVE-004's own `details` dict** — `live_stream_watcher.py`
  `check_live_capture_productivity`, `details={...}` (~line 538): `label`/`vm_name`/`venue`/`data_type`/`bucket` are
  constant per shard; `last_captured_at` is `None` for a "never captured" shard (BYBIT-FUTURES's state per the fired
  summary text) and does not change sweep-to-sweep; `attempted_age_hours` is now correctly excluded. No unaccounted
  volatile field found in this exact emission's identity.

## What's still unexplained (needs the next investigation, not closed here)

None of the above explains a stable-identity-hash alert still bypassing a 1800s in-memory cooldown on a single
persistent process 6+ hours after the fix deployed. Candidates NOT yet checked (out of this task's scope — a
backend_engineer deploy-chain verification task, not an open-ended runtime investigation):

- Does the Cloud Run instance actually stay warm continuously, or does something (health-check failure, OOM,
  `run.googleapis.com/cpu-throttling` interaction, a redeploy trigger elsewhere) recycle it between sweeps, silently
  resetting the in-memory `_seen` dict even with `minScale=1`?
- Is there a SECOND delivery path for `DP_CRON_DID_NOT_FIRE` (e.g. a direct Slack-mirror call in
  `_mirror_to_data_pipeline_slack` / `_route_data_pipeline_event`) that bypasses `route_event`'s
  `_deduplicator.is_duplicate()` gate entirely for the DP_* family specifically?
- Pub/Sub push redelivery/retry semantics — could `dp-alerting-subscriber` be receiving genuinely-new distinct
  messages more often than the ~15min sweep cadence suggests (e.g. `live_stream_watcher`'s own sweep interval is
  actually ~15min as designed, but something upstream double-publishes)?
- Was this specific identity's `_seen` entry perhaps registered ONCE at low TTL before the fix deployed (with the
  OLD, pre-fix volatile hash) and never correctly evicted/replaced — i.e. is there a stale-entry-poisoning edge case
  in `_evict_expired`/`is_duplicate` around a deploy-time boundary?

## Todos

- [x] ✅ [SCRIPT] P1. Root-cause why `DP_CRON_DID_NOT_FIRE`'s 1800s dedup cooldown is still violated live
      (`mtds-live-cefi-consolidated-20260817-025031`/BYBIT-FUTURES, confirmed firing every 15-16min as of 07:06Z) despite
      the deployed `alerting-service` image (`dp-alerting-subscriber-00103-zhw`) containing the correct
      `attempted_age_hours`-exclusion fix. Start from the 4 unruled-out candidates above — instance-recycling check
      (Cloud Run instance/container start-time vs. sweep timestamps), and a direct trace of the `DP_CRON_DID_NOT_FIRE`
      delivery path in `router.py`/`_route_data_pipeline_event` for a second, dedup-bypassing route. (repo:
      alerting-service) — Evidence: `alerting-service@166f291f44`.
- [x] ✅ [SCRIPT] P2. Once root-caused, re-sample the live fire-cadence for the same identity to confirm the 1800s
      cooldown is actually respected post-fix, and close this doc. (repo: alerting-service) — Evidence: deploy chain
      reverified clean + live fire-cadence confirmed 1800s-compliant post-fix, see Progress Log.

## Progress Log

- **2026-08-17 (slot 18, backend_engineer craft, task cefi_satellite_ao_dispatch_batch21-5517a0a936a2)**: ran the
  3-part deploy-chain check for `cefi_satellite_ao_dispatch_batch21_2026_08_17.md` item 1. All 3 conditions confirmed
  with hard evidence (content-on-main, Cloud Build id, live revision+traffic, plus a container-extraction ground-truth
  check the prior sweep didn't reach). The deploy chain is NOT the problem. Live behavior is still broken — filed this
  doc to track the residual, unexplained runtime defect separately so the deploy-verification todo can close cleanly
  on its own done-when bar.
- **2026-08-17 (slot 24, backend_engineer craft, task dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective-093d4d6697ee)**:
  root-caused via live Cloud Logging evidence, not guesswork. Confirmed `dp-alerting-subscriber` stayed on the SAME
  container instance the whole window (only 2 "AlertSubscriber initialized" starts, both at the 00:54Z fix-deploy
  boundary, none since through 07:36Z) — RULES OUT candidate 1 (instance recycling). Pulled the exact ALERT_ROUTED /
  ALERT_SENT log lines for `DP_CRON_DID_NOT_FIRE` in the observed 06:36Z/07:06Z window and found the 06:36Z cluster
  was `severity=INFO` in `consumed+routed` (`meta_watchers.reconcile_resolved`'s "condition cleared" bookend), yet
  STILL produced the SAME doubled `ALERT_ROUTED`/`ALERT_SENT` pair a genuine CRITICAL page produces. Traced this to
  `router._route_data_pipeline_event`: it is called with `dp_rule.severity` (the registry's STATIC CRITICAL for
  `DP_CRON_DID_NOT_FIRE`), not the emitted event's actual severity, so a `resolved=True` INFO bookend from
  `meta_watchers.reconcile_resolved` (`log_event(event, severity="INFO", details={"resolved": True, ...})`) still hit
  `if severity is AlertSeverity.CRITICAL: route_event_with_explicit_channels(...)` and paged PagerDuty/Telegram. Its
  `details` shape (`resolved`/`label`/`registry_id="DP-RESOLVED"`/`message`/`cloud`) is entirely different from a real
  fire's identity (`vm_name`/`venue`/`data_type`/`bucket`/...), so it was ALSO never caught by the 1800s dedup
  cooldown — every time the underlying (still-flapping) detector's miss/resolve state toggled, a fresh, un-deduped
  CRITICAL page fired. This is candidate 2 from the prior sweep's list ("a second, dedup-bypassing route"), just via
  severity-override rather than a literal second call site. Fixed: `_route_data_pipeline_event` now forces `severity
  = AlertSeverity.INFO` whenever `details.get("resolved")` is truthy, before the CRITICAL-page branch — mirrors the
  existing STATIC BACKLOG downgrade in the same function. 2 new regression tests
  (`TestResolvedBookendNeverPages`) added to `test_router_dp_mirror_live.py`. Evidence: `quality-gates.sh` ALL PASSED
  (53s), sentinel `166f291f4433198adf95a2ac8898c23ef390d7a0`; shipped `alerting-service@166f291f44`, ancestry-verified
  against `origin/live-defi-rollout`. Investigated (but did NOT fix, to keep this change surgical) a SEPARATE,
  independently-real quirk: a CRITICAL DP_* event runs through TWO independent `AlertDeduplicator.is_duplicate()`
  calls with DIFFERENT hashes (`route_event`'s own check on bare `details`, then
  `route_event_with_explicit_channels`'s check on `{**details, "severity": ...}`) — this causes a DOUBLE
  ALERT_ROUTED/ALERT_SENT per genuine fire (already flagged, pre-existing, in
  `test_router_dp_mirror_live.py::test_run_failed_still_pages_unaffected`'s own docstring) but does NOT by itself
  explain the cooldown-defeat symptom (each of the two states is STILL correctly 1800s-TTL'd on its own key, so an
  identical repeat fire is still suppressed by each independently) — confirmed by direct attempt: excluding
  `"severity"` from the dedup identity to unify the two states makes the INNER call's key collide with the key the
  OUTER check JUST recorded moments earlier in the SAME call stack, silently suppressing the CRITICAL PagerDuty/
  Telegram delivery entirely on every first occurrence (a much worse regression than the bug being chased) — reverted.
  Left as a known, separate, lower-priority follow-up (double-delivery-not-double-firing) rather than risking that
  regression in this task's scope.
- **2026-08-17 (slot 24, same task)**: root-cause + fix closed above. Todo 2 (re-sample live fire-cadence post-fix)
  needs the fix to actually be LIVE first (LDR→main promote + a fresh Cloud Build + `dp-alerting-subscriber` revision
  — same 3-part deploy-chain check this doc's own history already establishes the pattern for) before it can be
  meaningfully re-sampled; left open for the next dispatch/sweep rather than attempted here.
- **2026-08-17 (slot 10, backend_engineer craft, task dp_cron_did_not_fire_dedup_fix_deployed_but_ineffective-3243f3d899f0)**:
  todo 2 CLOSED. Deploy-chain re-verified clean, all 3 conditions with hard evidence: (1) content-on-main — `git show
  origin/main:alerting_service/notifiers/router.py` contains the `severity = AlertSeverity.INFO if
  details.get("resolved")` fix; (2) fresh Cloud Build `d6ab1c6f-645e-4dcf-86a7-6bc5454cdf8c` on the `alerting-service-build`
  trigger, SUCCESS at `2026-08-17T08:47:58Z`, commit `1a8c49f447d8b7a578b531dfe44e1dd155a351da` == `origin/main` tip
  at check time, produced image digest `sha256:7d18667756998faccae45a04a164566d41e62a5350bd5612682bba64e0df9770`; (3)
  `dp-alerting-subscriber`'s live revision `dp-alerting-subscriber-00105-bkq` (created `2026-08-17T08:53:51Z`, 100%
  traffic) confirmed running that exact digest (`gcloud run revisions describe`). Then re-sampled the same identity
  (`mtds-live-cefi-consolidated-20260817-025031`/BYBIT-FUTURES/`book_snapshot_5`+`derivative_ticker`, via
  `slack-read-channel.py data-pipeline-alerts`): fired at `09:06Z`, correctly SUPPRESSED at the `09:20/21Z` sweep
  (other, unrelated DP_CRON_DID_NOT_FIRE identities fired normally in that same sweep, confirming the sweep itself ran
  — this identity specifically was deduped), then fired again at `09:36Z` — exactly 30min after `09:06Z`, the exact
  cadence a correctly-functioning 1800s cooldown produces. Both data_types show the identical pattern. CONFIRMED: the
  1800s `DP_CRON_DID_NOT_FIRE` cooldown is now genuinely respected live. Updated
  `/codex/05-infrastructure/data-pipeline-alerts.md`'s DP-LIVE-004 note with the full two-bug resolution (was stale,
  describing only the still-open state as of the 06:38Z follow-up sweep). Doc fully resolved — archiving.
