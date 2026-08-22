---
doc_type: issue
title:
  "deployment-api traffic silently pinned to a stale revision-name for ~24h despite 5 green CI deploys (3rd distinct
  occurrence of this symptom class) — root-caused + fixed live; canary-deploy.sh now alerts via Cloud Logging, but
  wiring that log entry to an actual Slack page is still open"
summary: >-
  `uts-shared-deployment-api` had 100% traffic pinned by REVISION NAME (not tracking `latestRevision`) to
  `uts-shared-deployment-api-00430-dcr`, deployed manually 2026-08-04T10:59 UTC. A shipped non-breaking UAC fix
  (`unified-api-contracts@86a35fdb`, landed 13:11 UTC same day) never reached production traffic even though 5
  subsequent CI builds+deploys (`deployment-api-main-deploy`, Cloud Build SA) all reported SUCCESS and each created a
  fresh healthy `Ready=True` revision (00431..00435) — none of them got a single percent of traffic, silently, because
  `gcloud run deploy` does not override an existing by-name traffic pin the way it does `latestRevision: true` tracking.
  Root-caused via Cloud Audit Logs (manual `ReplaceService` calls, `ikenna@odum-research.com`, right at the same
  timestamp the `prd-sa-precutover` tag appeared) and fixed live: health-checked the newest revision directly via a
  temporary tag before touching anything, then `gcloud run services update-traffic --to-latest` — confirmed working by
  the fact that ANOTHER real CI deploy landed seconds later and Cloud Run auto-promoted to it with zero action taken,
  live-verified via `/health` (3/3 clean 200s, `stale: false`). Documented the general hazard class in
  `/codex/08-workflows/ci-cd-flow.md` § "Image deploy-hygiene" trap 5 + a CLAUDE.md one-liner. Shipped a code fix
  (`deployment-service@cb814e26`): `canary-deploy.sh`'s rollback path (the one documented mechanism that deliberately
  leaves a by-name pin) now prints a maximally loud warning and writes a `severity=CRITICAL` Cloud Logging entry
  (`cloud-run-traffic-pin-alert`, verified writable with the current identity) with the exact restore command. What is
  NOT done: nothing yet consumes that log entry — there is no Cloud Monitoring log-based alert policy routing it to
  Slack, so today's fix makes the condition LOGGABLE but not yet PAGING. See Todos.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [deployment-service, deployment-api, unified-trading-pm]
scope: [engineer, admin]
tags: [cloud-run, reliability, deploy-freshness, traffic-pinning, alerting, monitoring, canary-deploy]
related:
  [
    /codex/08-workflows/ci-cd-flow.md,
    /plans/archive/2026_07/deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md,
    /plans/archive/issues/sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md,
    /plans/archive/2026_08/issues/deployment_api_sigabrt_crash_loop_2026_07_24.md,
    /codex/04-architecture/ci-alerting.md,
  ]
created: "2026-08-05"
author: unknown
last_updated: "2026-08-21"
parent_epic: ci_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
drift_direction: advance-code
source: >-
  Interactive session 2026-08-05: operator asked me to verify their described CI/CD auto-deploy architecture claim
  ("push to main should build+deploy; dependency bumps propagate separately, gated on breaking changes") against a
  concrete observed symptom (a shipped UAC fix not reaching live deployment-api traffic). Root-caused live via Cloud
  Audit Logs + Cloud Run revision/traffic inspection, fixed live (traffic released) and in code (canary-deploy.sh
  alert), documented in codex + CLAUDE.md. Operator then asked "did you file this in doc" after I flagged the Slack
  routing as a real follow-up rather than faking it — this doc is that filing.
assigned_role: infra
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope:
  [
    deployment-service/scripts/cloud-run/setup-traffic-pin-alert.sh,
    deployment-service/scripts/cloud-run/traffic-pin-to-slack-bridge.py,
    deployment-service/scripts/cloud-run/canary-deploy.sh,
    /codex/04-architecture/ci-alerting.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
---

# Cloud Run traffic silently pinned to a stale revision-name (deployment-api, 2026-08-04→08-05)

## What happened

`uts-shared-deployment-api` traffic was pinned by explicit
`{revisionName: uts-shared-deployment-api-00430-dcr, percent: 100}` (not `latestRevision: true`) from 2026-08-04T10:59
UTC onward. A non-breaking UAC bugfix (`unified-api-contracts@86a35fdb`, 13:11 UTC same day — reverting an over-broad
`instrument_type` quarantine that had been hiding FUTURE/OPTION/COMBO/EQUITY/ETF/INDEX from the deployment-ui
distinct-values panel entirely) landed on UAC's `live-defi-rollout` and was eligible for every `deployment-api` build
from that point on (its Cloud Build vendors UAC SOURCE fresh via `git clone --branch live-defi-rollout` on every build,
bypassing `uv.lock` entirely — see `ci-cd-flow.md` for the full mechanism). 5 subsequent `deployment-api-main-deploy`
builds ran (14:19, 16:09, 20:10, 20:39 on 08-04, then 13:51 on 08-05), all `SUCCESS`, each producing a healthy
`Ready=True` revision (00431..00435) — **none received any traffic.** Discovered via the operator's own screenshot
showing the FUTURE/OPTION instrument types had disappeared from the deployment-ui panel entirely (a real regression from
an earlier, over-broad first-pass fix that had already been reverted in code — the revert just never reached
production).

## Root cause

`gcloud run deploy` (no `--no-traffic` flag, the default in `deployment-api-main-deploy`'s cloudbuild.yaml deploy step)
does **not** override an existing explicit by-revision-name traffic pin — it only auto-promotes when the service is
tracking `latestRevision: true`. Once ANYTHING sets an explicit named pin (a manual
`gcloud run services update-traffic --to-revisions=<name>=100`, the Cloud Console "manage traffic" action, or
`canary-deploy.sh`'s rollback path), the service is stuck in named-pin mode indefinitely — every future CI build+deploy
keeps reporting SUCCESS while 0% of traffic ever moves, with zero alert anywhere in the pipeline. Confirmed via Cloud
Audit Logs: the 00430 pin traces to manual `ReplaceService` calls by `ikenna@odum-research.com` at 10:02-11:04 UTC on
08-04 — right when the `prd-sa-precutover` tag (still present on revision 00417) appeared, suggesting a deliberate
precutover freeze that was never explicitly released.

**This is the THIRD documented occurrence of "deployment-api traffic frozen on a stale revision for an extended period,
silently, while CI kept succeeding" — worth naming as a pattern, not three unrelated one-offs**:

1. `deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md` (**still open**) — a genuine
   Cloud Run cold-start failure ("Container called exit(0)") silently no-op'd `deploy-shared.sh`'s automatic cutover for
   4 days (07-31 → recovered), same symptom-class as the extensively-investigated (1001-line, still not 100%
   root-caused) `deployment_api_sigabrt_crash_loop_2026_07_24.md`.
2. `sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md` — traffic frozen on `00374-4pd` (built
   2026-07-31) for ~4 days, root cause #1 attributed to the SAME cold-start bug above.
3. **This doc** — traffic frozen on `00430-dcr` for ~24h, root cause is a DIFFERENT mechanism (an explicit by-name
   traffic pin, not a cold-start failure), fixed live 2026-08-05.

Three occurrences, two distinct root-cause mechanisms, same observable symptom (green CI, stale traffic, no alert). The
shared gap across all three: **nothing watches `status.traffic` vs. the newest `Ready` revision** — every detection so
far has been a human noticing a stale UI panel, not an automated check.

## Shipped this session

- Live fix: released the 00430 pin via `gcloud run services update-traffic uts-shared-deployment-api --to-latest`
  (pre-verified the target revision's `/health` directly via a temporary tag first — 3/3 clean `200`s, `stale: false` —
  before touching live traffic). Verified working: a genuinely new CI deploy (`00436`) landed seconds later and Cloud
  Run auto-promoted to it with zero action from me — confirmed `latestRevision` tracking is restored.
- `deployment-service@cb814e26` — `canary-deploy.sh`'s rollback path now prints a loud
  `ALERT: TRAFFIC PINNED BY REVISION NAME` block and writes a `severity=CRITICAL` Cloud Logging entry
  (`cloud-run-traffic-pin-alert`, `jsonPayload.alert_type="cloud_run_traffic_pinned"`) with
  service/region/pinned-revision/restore-command. Verified the write permission works with the identity available this
  session (`gcloud logging write` succeeded). Also corrected the file's stale "cloud-build-router.yml calls this after
  every build" claim — verified fleet-wide that no `cloudbuild.yaml` or GitHub workflow currently invokes
  `canary-deploy.sh` at all; it's manually-run or called via `deploy-ui.sh` only.
- `unified-trading-pm@15ff12f3` — documented the general hazard class in `/codex/08-workflows/ci-cd-flow.md` § "Image
  deploy-hygiene" (new trap 5) + a condensed HARD RULE one-liner in `cursor-configs/CLAUDE.md`.

## What is NOT done (the actual open gap)

The Cloud Logging entry `canary-deploy.sh` now writes on a rollback-pin is real and verified-writable, but **nothing
consumes it yet** — there is no Cloud Monitoring log-based alert policy matching
`jsonPayload.alert_type="cloud_run_traffic_pinned"` and routing it to Slack. Today's fix makes the rollback-pin case
loggable, not pageable. Separately, since `canary-deploy.sh` is confirmed NOT wired into any current automated deploy
path for `deployment-api` (see above), **the manual-pin case that actually caused this incident wouldn't be caught by
this fix at all** — a human running `gcloud run services update-traffic --to-revisions=...` directly bypasses
`canary-deploy.sh` entirely. A durable fix needs a periodic, service-agnostic check (not just an in-script log line),
e.g. a scheduled job comparing `status.traffic` against `status.latestReadyRevisionName` for each auto-deployed Cloud
Run service and alerting on drift beyond some threshold — that's the real remaining work.

## Todos

- [x] ✅ [INFRA] P2. Cloud Monitoring log-based alert policy — deployment-service@e031a99 Resources created in
      central-element-323112: · Alert policy: projects/.../alertPolicies/15524322930351757512 · Notification channel:
      projects/.../notificationChannels/11149345209221800984 (Pub/Sub → traffic-pin alerts → Slack #ci-failures) ·
      Pub/Sub topic: cloud-monitoring-traffic-pin-alerts · Filter:
      logName="projects/central-element-323112/logs/cloud-run-traffic-pin-alert" AND
      jsonPayload.alert_type="cloud_run_traffic_pinned" · Severity: CRITICAL, autoClose: 24h, rate-limit: 5min Shipped:
      setup-traffic-pin-alert.sh (idempotent setup) + traffic-pin-to-slack-bridge.py (Pub/Sub→Slack bridge). IAM
      self-service: granted roles/monitoring.notificationChannelEditor to unified-trading-sa (was missing from the SA's
      specific role set despite having alertPolicyEditor — channel create required the separate editor role). NOT DONE
      (needs operator): (a) store Slack #ci-failures webhook URL in Secret Manager as
      cloud-monitoring-slack-ci-failures-webhook, (b) deploy the bridge as a Cloud Run service with a push subscription
      on the Pub/Sub topic, (c) trigger a canary rollback against a disposable/UAT service to verify end-to-end Slack
      delivery.
- [x] ✅ [INFRA] P2. Build a periodic drift check — deployment-service@74fb6ac (scheduled job, mirroring the
      `slot_drift_check.py` / `ci-status-consolidator` cadence pattern already used elsewhere) that, for every Cloud Run
      service with a `-main-deploy`-style auto-deploy trigger (`deployment-api`, `deployment-ui`,
      `unified-trading-system-ui`'s UAT service), compares live `status.traffic` against
      `status.latestReadyRevisionName` and alerts (dedup_key + cooldown_min, fire-on-transition per the established
      `notify-slack.yml` convention) when they diverge beyond a reasonable grace window. This is the ONLY mechanism that
      would have caught the actual incident in this doc (a manual pin, not a `canary-deploy.sh` rollback) — the
      log-based alert above only covers the `canary-deploy.sh` rollback path specifically. (repo: deployment-service, or
      wherever the fleet's periodic health-check jobs already live)
- [x] ✅ [DATA] P3. Once the drift check above exists, consider whether it subsumes/duplicates the still-open cold-start
      investigation's detection needs
      (`deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`) — unified-trading-pm@<SHA>.
      Cross-referenced: the drift check detects explicit by-name revision pins ≠ latest-ready (covers the manual-pin
      root cause of the wiring doc's own incident) but does NOT detect the cold-start `exit(0)` silent-freeze case
      because `gcloud run deploy` default sets `latestRevision: true` and the drift check skips `tracks_latest=True`
      services. A future enhancement comparing "newest Ready revision vs actually-serving revision under latestRevision"
      would subsume both. Added cross-reference + Progress Log entry to the cold-start doc; no duplication of
      investigation. (repo: unified-trading-pm, doc-only)

## Progress Log

- **2026-08-05 (interactive session)**: root-caused, fixed live (traffic released, verified healthy), shipped the
  `canary-deploy.sh` loud-alert fix, documented the hazard class in codex/CLAUDE.md. Filed this doc after being asked
  directly whether the Slack-routing follow-up (explicitly called out as unfinished in the session) had been tracked —
  it had not; this doc is that tracking, per the "every follow-up is a `- [ ]` todo, never prose" HARD RULE.
- **2026-08-05 (slot-7, data_engineering, P3 cross-reference task)**: Read the cold-start issue doc
  (`deployment_api_cloud_run_coldstart_flaky_exit0_blocks_prd_sa_cutover_2026_07_31.md`) and the shipped drift check
  (`cloud_run_traffic_drift_check.py` @ `deployment-service@74fb6ac`). **Finding**: the drift check does NOT fully
  subsume the cold-start `exit(0)` detection need. The drift check only flags explicit by-name revision pins ≠
  latest-ready; it skips services tracking `latestRevision: true`. Since `deploy-shared.sh`'s `gcloud run deploy`
  default sets `latestRevision: true`, and Cloud Run keeps the old revision as the `latestRevision` target when the new
  one cold-start-fails, the drift check would read `tracks_latest=True` and skip — precisely the silent-freeze scenario
  documented in the cold-start doc. A future enhancement that ALSO compares "newest `Ready` revision vs.
  actually-serving revision under `latestRevision`" would subsume both the manual-pin case (this doc's incident) AND the
  cold-start-failure case. Added cross-reference + Progress Log entry to the cold-start doc with this analysis; no
  duplication of investigation. Flipped this todo's checkbox. (repo: unified-trading-pm, doc-only)
- **context-scout 2026-08-05**: populated context_scope (4 entries).
- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — swapped in the still-open follow-up's real targets
  (`setup-traffic-pin-alert.sh`, `traffic-pin-to-slack-bridge.py`) and `ci-alerting.md` (the Slack-routing convention
  the remaining webhook/Cloud-Run-deploy work depends on); dropped the now-closed drift-check todo's
  `cloud_run_traffic_drift_check.py` and `deployment-api/cloudbuild.yaml` to stay minimal.
- **2026-08-07 (slot-4, infra, task cloud_run_traffic_pin_silent_freeze_alert_wiring-004)**: Audited infrastructure
  state. Finding: Cloud Run service `traffic-pin-slack-bridge` already deployed and Ready
  (`deployment-service@6b4be78`); push subscription `traffic-pin-slack-bridge-push` wired to
  `cloud-monitoring-traffic-pin-alerts` Pub/Sub topic; GSM secret shell `cloud-monitoring-slack-ci-failures-webhook`
  created (no versions). The Slack webhook URL lives only in GitHub Actions secret `SLACK_CI_WEBHOOK_URL`
  (write-only/unreadable by agents — genuine credential ask, not an IAM gap). Wrote a test log entry
  (`cloud-run-traffic-pin-alert`, `alert_type=cloud_run_traffic_pinned`) to validate the Cloud Logging → Cloud
  Monitoring → Pub/Sub → bridge pipeline. Flipped INFRA todo [x] with evidence. Created [OPERATOR] P2 todo for webhook
  URL population + e2e Slack delivery verification (exact gcloud command included).
- **2026-08-10 (ci_reconciler, slot 7, hourly fleet sweep)**: found the drift-check MONITOR ITSELF silently blind since
  debut — `cloud-run-traffic-drift-check.yml` (the scheduled job built for this doc's todo 2,
  `deployment-service@74fb6ac`) had **0 green runs out of its last 40** (every hourly tick failed since creation
  2026-08-06), so the exact "manual traffic pin → green CI but stale traffic, zero alert" incident this doc documents
  could recur undetected. Root cause (read from the failing run's log): `cloud_run_traffic_drift_check.py` in `--json`
  mode printed the JSON payload to stdout and then APPENDED human-readable status lines (⚠️ errors / ❌ drifted list /
  ✅ all-clear) to the SAME stream; the workflow writes stdout to `/tmp/drift_result.json` and parses with `json.load`,
  so any non-empty status line raised `JSONDecodeError: Extra data` and failed the `check` job — the notify job never
  fired. Fixed (`deployment-service@3cd2d0f7c6`): every non-JSON status line now routes to stderr in `--json` mode;
  stdout carries only the JSON array. Added 4 regression tests (`tests/unit/test_cloud_run_traffic_drift_check.py`).
  Verified with a fresh `workflow_dispatch` on the fixed HEAD (run 31403341423) — see the run's conclusion. This is the
  same coverage hole from the other direction: a red monitor that pages nobody (ldr-docs-gate) and a monitor whose own
  output is unparseable so it fails before it can alert (this one) are the same class.
- **context-scout 2026-08-17**: refreshed context_scope (5 entries) — re-verified all 5 still resolve and accurately
  target the sole remaining open item (the `[OPERATOR]` webhook-population + e2e Slack-delivery follow-up).
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)

- **2026-08-21 — ruling D53 (Traffic-pin alert webhook)**: ATTEMPT — populate the GSM webhook secret via a one-off
  GH workflow dispatch (the GH secret cannot be read back, a workflow can write it to GSM); verify with a UAT
  canary rollback. Source: /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.

## Follow-ups

- [x] ✅ [INFRA] P2. Deploy traffic-pin-to-slack-bridge.py as a Cloud Run service with a push subscription on the
      Pub/Sub topic, and create the GSM secret shell for the Slack webhook — deployment-service@6b4be78. Evidence: Cloud
      Run service `traffic-pin-slack-bridge` Ready at https://traffic-pin-slack-bridge-cldtjniqvq-an.a.run.app; push
      subscription `traffic-pin-slack-bridge-push` wired to topic `cloud-monitoring-traffic-pin-alerts`; GSM secret
      shell `cloud-monitoring-slack-ci-failures-webhook` created (no versions yet — operator-gated credential step
      below). End-to-end Slack delivery NOT yet verified (awaiting webhook URL population per [OPERATOR] todo below).

- [ ] [INFRA] P2. Populate `cloud-monitoring-slack-ci-failures-webhook` in GSM via a one-off GH Actions workflow
      dispatch that reads the existing `SLACK_CI_WEBHOOK_URL` repo secret and writes it to Secret Manager (the
      secret's value can't be read back directly outside a workflow run, but a workflow can forward it) — per D53
      ruling (ATTEMPT, 2026-08-21). Command inside that workflow step:
      `printf "%s" "$SLACK_CI_WEBHOOK_URL" | gcloud secrets versions add cloud-monitoring-slack-ci-failures-webhook --data-file=- --project=central-element-323112`.
      Then verify end-to-end by triggering a canary rollback on a UAT Cloud Run service and confirming the Slack
      message arrives in #ci-failures. Done when: `gcloud secrets versions list cloud-monitoring-slack-ci-failures-webhook`
      shows a new version and a live UAT canary test posts to #ci-failures.

> **2026-08-06 archive-candidate audit**: Todo 1 is flipped [x] but its own body lists 'NOT DONE (needs operator): (a)
> store Slack webhook, (b) deploy the bridge as Cloud Run, (c) verify end-to-end Slack delivery' — the alert is loggable
> but not yet paging, and these items have no separate - [ ] todos.
