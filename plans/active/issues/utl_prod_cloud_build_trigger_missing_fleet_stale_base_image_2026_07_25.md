---
doc_type: issue
title:
  "unified-trading-library-prod Cloud Build trigger does not exist (NOT_FOUND) — the UTL base Docker image has not
  republished since 2026-07-23T09:12:10Z despite 15+ successful main pushes, silently staling every service's Docker
  build fleet-wide"
summary: >-
  Root-caused while diagnosing deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md's open P0 todo ("why
  hasn't active/ moved despite unified-trading-library@4773a3fd being live on main for 2.5h"). The deployed
  uts-shared-deployment-api container reports unified-trading-library package_version=0.55.0 via its own
  /api/cloud-builds/library-status/unified-trading-library endpoint — nowhere near current main. Traced upstream: UTL's
  quality-gates-v2.yml correctly fires a `qg-passed` repository_dispatch to unified-trading-pm on every main push
  (confirmed: job "Dispatch cloud-build trigger (main release)" succeeded on the exact push carrying 4773a3fd,
  2026-07-25T05:06:23Z). PM's cloud-build-router.yml correctly receives it and attempts `gcloud builds triggers run
  unified-trading-library-prod --region=asia-northeast1` — which fails with `NOT_FOUND: Requested entity was not found`
  (log timestamp 05:07:25Z, run 30145190398). The router treats this as a soft WARNING (not a job failure) so the run
  reports green with zero alerting, masking the outage. Confirmed via `gcloud builds triggers list --project
  central-element-323112` that no `unified-trading-library-prod` trigger exists at all (siblings like
  `instruments-service-prod` DO exist, confirming the naming convention and isolating this to UTL specifically). `gcloud
  artifacts docker images list` confirms zero images have been pushed to
  `unified-trading-library/unified-trading-library` since **2026-07-23T09:12:10Z** (the `0.55.0`/`latest` tags,
  currently 51+ hours and 15+ main-branch commits stale as of this writing, 2026-07-25T12:2xZ) — exactly the moment this
  trigger apparently went missing. Every service Dockerfile `FROM`s this digest-pinned base image, so EVERY fleet Docker
  build has been baking in a 2+-day-stale UTL since 2026-07-23, silently, with the existing digest-refresh automation
  (`update-dependency-version.yml`) working exactly as designed but having nothing new to propagate.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-library, unified-trading-pm, deployment-api]
scope: [engineer, admin]
tags: [ci, cloudbuild, base-image, gcp, trigger, fleet, p0, infra, deploy-blocker]
related:
  [
    /plans/active/issues/deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md,
    /plans/active/issues/base_image_digest_sweep_broken_fleet_builds_red_2026_07_18.md,
  ]
created: 2026-07-25
parent_epic: infrastructure_master
priority: P0
assigned_vm: planning
resolved_by:
locked_by:
locked_since:
source:
  'Found 2026-07-25 (slot 6, backend_engineer) while working
  deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md''s open P0 todo ("Determine why active/ still
  hasn''t moved despite unified-trading-library@4773a3fd being live on main for ~2.5h"). Traced the deployed
  container''s actual installed UTL version, then the full qg-passed → cloud-build-router → gcloud builds triggers run
  chain, live, via gcloud/gh CLI against production GCP + GitHub.'
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# unified-trading-library-prod Cloud Build trigger missing — fleet-wide stale base image (2026-07-25)

## What I found

**Symptom (where I started):** `deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md`'s open P0 todo asks
why GCS `deployments/active/` still hasn't converged toward the live-VM count despite `unified-trading-library@4773a3fd`
(the reaper-tick parallelization fix) being reported live on `main` for ~2.5 hours. Queried the deployed service
directly instead of re-trusting ancestry checks (this repo's own prior sessions already found
`git merge-base --is-ancestor` unreliable across the LDR→main squash-promote —
`deployment_promote_squash_ancestry_false_negative_2026_07_25.md`):

```
GET https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app/api/cloud-builds/library-status/unified-trading-library
→ {"package_version": "0.55.0", "version_in_init": "1.6.0", ...}
```

`importlib.metadata.version("unified_trading_library")` on the LIVE container reads **0.55.0** — the currently
checked-out dev tree resolves to `0.56.1.dev357+g6afe62c71` (this session's own `uv sync` output), so the deployed
container is running UTL from well before the current line, let alone `4773a3fd` (landed 2026-07-25T04:23:53Z).

**Why the digest pin didn't catch this:** `deployment-api`'s `Dockerfile` `FROM`s
`unified-trading-library/unified-trading-library@${BASE_IMAGE_DIGEST}` — a digest pinned as a checked-in `ARG` default,
refreshed by `update-dependency-version.yml` whenever UTL's base image republishes and dispatches its new digest.
Confirmed this refresh mechanism itself is working correctly (`agent-orchestrator`-style commit history: `197b233`
"chore(deps): refresh base-image digest pin", landed 2026-07-23T12:32:26Z) — **but it has had nothing new to refresh
with**, because the base image itself stopped publishing before that commit even landed.

**Traced the full publish chain, live:**

1. UTL's `.github/workflows/quality-gates-v2.yml` has a `dispatch-cloud-build` job
   (`if: github.event_name == 'push' && github.ref == 'refs/heads/main' && ...metadata_only != 'true'`) that POSTs a
   `qg-passed` `repository_dispatch` to `unified-trading-pm`. **Confirmed firing correctly**: job "Dispatch cloud-build
   trigger (main release)" succeeded on UTL's own `quality-gates-v2` run for the exact push carrying `4773a3fd`
   (`gh run view 30145177081` — conclusion `success`, 2026-07-25T05:06:23Z).
2. PM's `.github/workflows/cloud-build-router.yml` **correctly received the dispatch**
   (`gh run list --repo IggyIkenna/unified-trading-pm --workflow=cloud-build-router.yml` shows a matching run at
   05:06:53Z, run id `30145190398`, job `route-build` conclusion `success`).
3. Inside that job's log (`gh api .../jobs/89645561259/logs`), the actual trigger attempt:
   ```
   Triggering Cloud Build in central-element-323112 for unified-trading-library: (region: asia-northeast1)
   Trigger failed in asia-northeast1: ERROR: (gcloud.builds.triggers.run) NOT_FOUND: Requested entity was not found.
   Named trigger not found or failed — no regional fallback applicable
   WARNING: Cloud Build trigger not yet configured for unified-trading-library. Manual setup required.
   ```
   The router's own fallback-region logic is a no-op here (primary region == fallback region == `asia-northeast1` for
   this repo's config) — this is a missing-entity problem, not a transient regional outage.
4. **This WARNING does not fail the job or page anyone.** `route-build` still reports `conclusion: success` (by design —
   the failure branches that WOULD alert, `Slack — Build Trigger Not Configured` /
   `Slack — Build Trigger Permission Denied`, are visible in the job list but show `skipped`, meaning their trigger
   condition also didn't fire for this exact WARNING path) — the outage is completely silent in the dashboard/CI UI.
5. Confirmed directly against GCP:
   `gcloud builds triggers list --project central-element-323112 --region=asia-northeast1` lists 30 triggers including
   `instruments-service-prod` (same `<repo>-prod` naming convention, proving the pattern is right and other repos have
   it) but **no `unified-trading-library-prod` trigger exists at all**. There IS a
   `unified-trading-library-live-defi-rollout` trigger (a different branch/purpose), but nothing for `main`/prod.
6. Confirmed the actual publish gap directly against the registry:
   `gcloud artifacts docker images list asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-library/unified-trading-library --include-tags --sort-by="~UPDATE_TIME"`
   — the newest entry (tagged `0.55.0`, `latest`) is **`2026-07-23T09:12:10Z`**. Zero images (tagged or untagged) have
   landed since, despite ≥15 successful `quality-gates-v2` runs on UTL's `main` in that window
   (`gh run list --workflow=quality-gates-v2.yml --branch=main`), each of which fired the same `dispatch-cloud-build`
   step.

**Bounding the incident window:** the trigger was almost certainly present and working before 2026-07-23T09:12:10Z (that
is the last successful publish, and UTL's `cloudbuild.yaml` itself documents that image re-tagging was already firing
"many times a day" through that period). Something removed/broke the `unified-trading-library-prod` trigger at or
shortly after that timestamp. Not further diagnosed in this session (out of scope for a backend_engineer craft — this is
a GCP Cloud Build trigger/IAM/repo-connection provisioning action, not application code); worth checking Cloud Audit
Logs for a `google.devtools.cloudbuild.v1.TriggerService.DeleteBuildTrigger` (or a failed `CreateBuildTrigger`/rename)
around that timestamp to find out whether this was an accidental delete, a Terraform/IaC drift, or a
GitHub-App-connection re-auth that silently orphaned the trigger.

## Why it matters

- **Every service repo's Dockerfile `FROM`s this exact base image.** Since 2026-07-23T09:12:10Z, every fresh Cloud Build
  across the fleet (deployment-api, execution-service, strategy-service, ml-service, alerting-service, etc. — the same
  repo set as the related `base_image_digest_sweep_broken_fleet_builds_red_2026_07_18.md`'s blast radius) has been
  baking in an UTL that is now 51+ hours and 15+ commits behind `main`, including the exact
  `deployment_registry_reaper_not_draining_stale_entries` fix this session was dispatched to verify, plus whatever else
  has landed on UTL `main` in that window (bug fixes, security patches, new symbols other services may already depend on
  — recall `base_image_digest_sweep_broken_fleet_builds_red_2026_07_18.md`'s own addendum describes a near-identical
  `ImportError: cannot import name 'gcs_read_object_range'` incident from the SAME class of drift).
- **The existing digest-refresh automation (`update-dependency-version.yml`) is working correctly and is NOT the problem
  this time** — worth stating explicitly so nobody re-diagnoses that mechanism again; it has nothing new to propagate
  because the true upstream source (the base-image publish trigger) is the broken link.
- **This is completely silent.** No alert fires, the router job shows green, and the only visible symptom is individual
  services' code appearing to "not take effect" in production despite `main` looking correct — exactly the trap this
  session fell into before tracing it upstream. Per workspace HARD RULE ("Data pipeline correctness is the heartbeat" /
  cross-repo + infra findings require operator notification), this should not be left as a per-service point-fix
  (re-pinning digests manually, as the related 07-18 doc's `deployment-api@2531d925` and `ml-service@5d05c4c` did) — the
  trigger itself needs to exist again or the drift recurs indefinitely.

## Recommended decision

This is a GCP infra/provisioning action (recreate or repair the `unified-trading-library-prod` Cloud Build trigger in
`central-element-323112`, region `asia-northeast1`, mirroring the working `instruments-service-prod` trigger's config —
GitHub App connection, `main` branch filter, `cloudbuild.yaml` path, substitutions) — outside a backend_engineer's craft
scope and outside this session's authority to blind-fire (`gcloud builds triggers create` against a fleet-wide shared
base-image pipeline without confirming the correct source config/IAM/connection first). Recommend:

1. **Operator/infra-role todo**: inspect why `unified-trading-library-prod` disappeared (Cloud Audit Logs around
   2026-07-23T09:00-09:15Z) and recreate it, cloned from `instruments-service-prod`'s working config.
2. Once recreated, manually fire one `gcloud builds triggers run unified-trading-library-prod` (or push a trivial commit
   to UTL `main`) to confirm the publish path end-to-end, and verify `update-dependency-version.yml` picks up the fresh
   digest fleet-wide within its normal cadence.
3. **Harden against silent recurrence**: the router's `route-build` job should not report `success` when the actual
   `gcloud builds triggers run` call hits `NOT_FOUND` — either fail the job or reliably fire the existing
   `Slack — Build Trigger Not Configured` step (it's already wired but did not fire for this exact path; worth a
   follow-up BACKEND todo in `unified-trading-pm` to find why its condition didn't match this WARNING branch).
4. Once the trigger is confirmed working and a fresh UTL base image has published, re-run
   `deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md`'s Todo 4 verification (`active/` count vs
   live-VM count) — that todo cannot be closed correctly until the deployed container actually carries `4773a3fd`, which
   requires this fix first.

## Todos

- [ ] [INFRA] P0. Recreate the `unified-trading-library-prod` Cloud Build trigger in GCP project
      `central-element-323112`, region `asia-northeast1` — mirror `instruments-service-prod`'s working config (GitHub
      App connection, `main` branch push filter, `cloudbuild.yaml` build config path, service account). Check Cloud
      Audit Logs around 2026-07-23T09:00-09:15Z first to understand how it disappeared (accidental delete vs IaC drift
      vs connection re-auth) so the recreate doesn't just re-break the same way. (repo: infra/GCP config, no application
      repo)
- [ ] [INFRA] P1. Once the trigger is recreated, manually verify one end-to-end publish
      (`gcloud builds triggers run     unified-trading-library-prod` or a trivial UTL `main` push) and confirm the new
      image lands in
      `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-library/unified-trading-library` with a
      fresh `UPDATE_TIME`.
- [ ] [BACKEND] P2. `unified-trading-pm/.github/workflows/cloud-build-router.yml`'s `route-build` job should not
      silently report `success`/green when `gcloud builds triggers run` returns `NOT_FOUND` — either fail the job loud
      or fix the condition on the existing (currently-skipped) `Slack — Build Trigger Not Configured` step so it
      actually fires for this path. This exact WARNING sat silent for 51+ hours with zero alerting.
