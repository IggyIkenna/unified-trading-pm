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
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-library, unified-trading-pm, deployment-api]
scope: [engineer, admin]
tags: [ci, cloudbuild, base-image, gcp, trigger, fleet, p0, infra, deploy-blocker]
related:
  [
    /plans/archive/issues/deployment_registry_reaper_not_draining_stale_entries_2026_07_24.md,
    /plans/archive/issues/base_image_digest_sweep_broken_fleet_builds_red_2026_07_18.md,
  ]
created: 2026-07-25
parent_epic: infrastructure_master
priority: P0
assigned_vm: planning
resolved_by: unified-trading-pm@5e1a26e17
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

> **🟢 ARCHIVED 2026-07-25** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule (terminal_status_archival_backlog_sweep_2026_07_25.md).

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

- [x] ✅ [INFRA] P0. Recreate the `unified-trading-library-prod` Cloud Build trigger in GCP project
      `central-element-323112`, region `asia-northeast1` — mirror `instruments-service-prod`'s working config (GitHub
      App connection, `main` branch push filter, `cloudbuild.yaml` build config path, service account). Check Cloud
      Audit Logs around 2026-07-23T09:00-09:15Z first to understand how it disappeared (accidental delete vs IaC drift
      vs connection re-auth) so the recreate doesn't just re-break the same way. (repo: infra/GCP config, no application
      repo) — **Found already recreated 2026-07-25 (slot 2, infra)** when picking up todo 2 below:
      `gcloud builds     triggers describe unified-trading-library-prod --region=asia-northeast1` confirms it exists
      (`createTime: 2026-07-25T12:44:13Z`, `id: e9da54bb-ca66-40f6-b5fd-5caff6bfebf1`), correctly configured (push to
      `^main$`, GitHub App connection `iggyikenna-github`, `filename: cloudbuild.yaml`) — mirrors
      `instruments-service-prod`'s pattern. **Not created by this session** — no attribution/audit-log root-cause
      investigation was captured by whoever did it; flipping on the OBSERVED fact the entity now exists and is correctly
      configured, not on having done the recreate or the audit-log trace myself. If the audit-log root cause (why it
      disappeared 2026-07-23) still matters, that's a separate follow-up, not blocking this todo's own done-when (the
      trigger existing + correctly configured).
- [x] ✅ [INFRA] P1. Once the trigger is recreated, manually verify one end-to-end publish
      (`gcloud builds triggers run     unified-trading-library-prod` or a trivial UTL `main` push) and confirm the new
      image lands in
      `asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-library/unified-trading-library` with a
      fresh `UPDATE_TIME`. — **COMPLETED 2026-07-25 (slot 7, infra)**, picking up where slot 2 left off (see the entry
      above: `44922ad1` + `71dcf0f4` shipped to `live-defi-rollout`, blocked on the LDR→main promote landing). The
      promote PR churned through 2 supersessions on this high-velocity branch before landing: PR #644 (`44922ad1` →
      `main`) went `mergeable_state: blocked` on a required `sit-gate/fleet-green` check that had picked up a CANCELLED
      (not genuinely failed) `full-workspace-sit` run — root-caused via `gh api repos/.../commits/<sha>/statuses`; the
      underlying SIT run had been superseded by a newer dispatch, a known transient condition on this branch, not a real
      defect. A fresh `full-workspace-sit` run completed SUCCESS shortly after, but the standing promote-fleet cron
      hadn't ticked yet to pick it up, so manually dispatched
      `gh workflow run ldr-to-main-promote-fleet.yml --repo IggyIkenna/unified-trading-pm -f     only_repo=unified-trading-library`
      to force a re-check — this superseded #644 with fresh PR #645 (head `71dcf0f42fb2`, which already includes both
      `44922ad1` and `71dcf0f4` — confirmed via `git merge-base --is-ancestor 44922ad1... 71dcf0f4...`) carrying a clean
      green `sit-gate/fleet-green` from the new dispatch. PR #645's `quality-gates-v2` (~7 min real run) passed and it
      merged at 13:23:18Z. Verified `git show origin/main:cloudbuild.yaml` has zero unescaped `$VERSION`/`$IMAGE_TAG`
      references. Re-ran
      `gcloud builds triggers run unified-trading-library-prod --project=central-element-323112     --region=asia-northeast1 --branch=main`
      → build `4c2dbad5-e61f-430e-9f03-9592f428bfba`, no more INVALID_ARGUMENT, completed `SUCCESS` (started 13:25:14Z,
      ~6 min, all 16 steps incl. wheel build + docker base-image build/push). Confirmed via
      `gcloud artifacts docker images list     asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-library/unified-trading-library     --include-tags --sort-by="~UPDATE_TIME"`:
      fresh image tagged `0.56.0-8e8682222522` + `latest`, `UPDATE_TIME:     2026-07-25T13:31:00` (vs. the stale
      `2026-07-23T09:12:09` baseline this whole issue doc is about) — the fleet-wide stale-base-image outage is resolved
      end-to-end. The fleet-wide 15-repo instance of the same $VERSION-escape bug is tracked separately (out of this
      doc's scope) in `cloudbuild_yaml_unescaped_substitution_comments_fleet_wide_2026_07_25.md` (slot 2). Also set the
      `CLOUD_BUILD_PROD_DEPLOY_EXPECTED` repo variable to `true` for `unified-trading-library` (`gh variable set`) — an
      independent, repo-scoped hardening alongside slot 2's `notify-utl-base-image-not-configured` job (todo above);
      neither conflicts, both now cover this repo.
- [x] ✅ [BACKEND] P2. `unified-trading-pm/.github/workflows/cloud-build-router.yml`'s `route-build` job should not
      silently report `success`/green when `gcloud builds triggers run` returns `NOT_FOUND` — either fail the job loud
      or fix the condition on the existing (currently-skipped) `Slack — Build Trigger Not Configured` step so it
      actually fires for this path. This exact WARNING sat silent for 51+ hours with zero alerting. —
      **`unified-trading-pm@02f73dee2`.** Root-caused why the existing `notify-build-not-configured` job stayed
      `skipped`: it's correctly gated behind the repo variable `vars.CLOUD_BUILD_PROD_DEPLOY_EXPECTED` (confirmed via
      `gh variable list` — unset at both repo and org level), which exists to silence the SAME warning for OTHER repos
      whose `-prod` trigger is intentionally absent pre-cutover (a trading-critical service not yet auto-deploying, by
      design). Flipping that gate globally would reintroduce exactly the alert-fatigue noise it was built to prevent, so
      did NOT touch it. Instead added a new, narrowly-scoped, ALWAYS-ON job (`notify-utl-base-image-not-configured`)
      that fires unconditionally (no `CLOUD_BUILD_PROD_DEPLOY_EXPECTED` gate) specifically for
      `repo == 'unified-trading-library'` — mirroring this same file's existing `notify-permission-denied` job, whose
      own comment already states the identical reasoning ("a missing IAM binding is never an intentional pre-cutover
      state") which applies just as directly to UTL's base-image trigger: every service Dockerfile `FROM`s it, so there
      is no legitimate reading under which it's supposed to be missing. Uses
      `dedup_key: "cloud-build-not-configured:unified-trading-library-prod"` + `cooldown_min: 1440` (24h) so it pages
      once on the transition rather than on every subsequent UTL `main` push while the trigger stays broken. Verified:
      `python3 scripts/quality_gates/check_workflow_yaml_valid.py` passes (56/56 workflows parse); full
      `bash scripts/quality-gates.sh` exit 0. Shipped via `git push` (closed direct-push carve-out for PM `.github/**`
      changes per CLAUDE.md — quickmerge itself kept losing the branch-drift race on this exceptionally high-velocity
      branch across 3 consecutive attempts; each retry was a clean `git pull --rebase --autostash` with zero conflicts,
      never a blind overwrite). Confirmed live on `origin/live-defi-rollout` via `git merge-base --is-ancestor` + direct
      content read (`git show origin/live-defi-rollout:.github/workflows/cloud-build-router.yml`).
- [x] ✅ [BACKEND] P3. Harden `notify-utl-base-image-not-configured` against an empty-`repo_type` recurrence (review
      flag, msg 2012, 2026-07-25). The job's `repo_type != 'library'` guard fired correctly for the observed incident
      (run 30145190398 resolved `repo_type=service` for `unified-trading-library`, so the guard matched), but this same
      workflow already documents `repo_type` as UNRELIABLE when the dispatch payload omits it — the fallback then
      resolves to the workspace-manifest declared `type=library`, making `repo_type != 'library'` FALSE and silently
      suppressing this exact alert on a future recurrence. Gate the alert on `repo == 'unified-trading-library'`
      (identity, always known) rather than on the derived `repo_type`, or additionally fire when `repo_type` is
      empty/unknown, so a payload-omitted recurrence still pages. **Done when**: a simulated dispatch with empty
      `repo_type` for `unified-trading-library` still fires the alert. Not blocking — the shipped P2 fix fully covers
      the OBSERVED failure mode and is QG-green; this closes a latent second suppression path only. —
      **`unified-trading-pm@5e1a26e17`.** Scope turned out BROADER than the todo's literal text: the SAME
      `repo_type != 'library'` gate that would suppress the alert also gates the auth steps AND the "Trigger Cloud Build
      (Docker image)" step itself (`docker-build`, which is what SETS `build_triggered`/`build_failure_reason` — the
      exact outputs the alert's own condition checks). Patching only the alert job's `if:` would NOT have satisfied its
      own done-when: on an empty-payload dispatch, `docker-build` would still be skipped, those outputs would stay
      empty, and the alert's `build_failure_reason == 'not-configured'` check would never match regardless of how the
      `repo_type` clause was rewritten. Fixed at the single resolution point instead (`cloud-build-router.yml`'s `route`
      step, where `repo_type` is derived from the manifest fallback): when the payload omits `repo_type` AND
      `repo == 'unified-trading-library'` AND the manifest derivation lands on `library`, override it back to `service`
      — matching what `quality-gates-v2.yml`'s own dispatch already sends explicitly today (confirmed via
      `grep repo_type unified-trading-library/.github/workflows/quality-gates-v2.yml` → hardcoded
      `"repo_type": "service"`), so this is aligning the fallback path with the already-established real-world behavior,
      not introducing new semantics. This one-line-locus fix makes every downstream `repo_type != 'library'` gate
      (auth-wif, auth-key, docker-build, AND all 6 notify jobs including `notify-utl-base-image-not-configured`) behave
      correctly without re-special-casing the repo 8 separate times. Verified no regression: simulated the same
      derivation for `unified-api-contracts` (a genuine wheel-only library) — still resolves to `library`, unaffected.
      **Done-when satisfied**: simulated the empty-`repo_type` dispatch locally (`REPO=unified-trading-library`,
      `REPO_TYPE=""` → manifest derives `library` → override fires → final `service`; confirmed via
      `jq '.repositories["unified-trading-library"].type'` on `workspace-manifest.json` that the manifest genuinely says
      `library`, so the override is real, not a no-op) — every downstream gate (`repo_type != 'library'`) evaluates
      reachable, including the alert's own condition. Verified: `check_workflow_yaml_valid.py` (56/56 workflows parse),
      extracted-script `bash -n` syntax check clean, full `bash scripts/quality-gates.sh --no-fix` exit 0. Shipped via
      direct `git push` (closed `.github/**` carve-out per CLAUDE.md, same precedent as the sibling P2 fix — quickmerge
      itself is not required for this class of PM change).

## Progress Log

- **2026-07-25 (slot 7, infra) — Todo 1 IN PROGRESS, second independent blocker found + fixed.** Recreated
  `unified-trading-library-prod` in `central-element-323112`/`asia-northeast1` (`gcloud beta builds triggers import`,
  mirroring `instruments-service-prod`'s config: `filename: cloudbuild.yaml`, `push.branch: ^main$`, GitHub connection
  `iggyikenna-github/unified-trading-library` — already existed as a resource, reused from the working
  `unified-trading-library-live-defi-rollout` trigger). Checked Cloud Audit Logs 2026-07-23T08:00-10:30Z per todo 1's
  own instruction for a `DeleteBuildTrigger`/`CreateBuildTrigger` event around the 09:12:10Z last-good-publish timestamp
  — found NONE (only unrelated `compute.instances.delete` VM-cleanup entries); the trigger's disappearance left no audit
  trail visible within this account's log access, so the accidental-delete-vs-IaC-drift-vs-reauth question from todo 1
  remains genuinely UNRESOLVED — noting this as an open sub-question, not silently dropping it. **Test-fired the new
  trigger immediately** (`gcloud builds triggers run ... --branch=main`) and hit a SECOND, independent, pre-existing
  bug: Cloud Build's build-config validator rejected the build with
  `INVALID_ARGUMENT: key in the template "VERSION" is not a valid built-in substitution` — reproduced with zero custom
  substitutions passed, proving it's not about anything I supplied. Root cause:
  `unified-trading-library/cloudbuild.yaml` has 4 prose comments using a bare `:$VERSION` (single-dollar) instead of the
  shell-escaped `:$$VERSION` used everywhere else in the file; Cloud Build's static validator scans the WHOLE file
  content (including comments) for `$VAR`-shaped tokens and rejects any that aren't a recognized built-in or declared
  `_substitution`. Traced via `git log -p` to commit `08b4d89a` (2026-07-23T14:51:07Z) — AFTER the 09:12:10Z outage
  start, so this is a SEPARATE bug stacked on top of the missing-trigger root cause, not its origin; it independently
  blocks EVERY build attempt against this cloudbuild.yaml (trigger-fired or manual) regardless of whether
  `unified-trading-library-prod` exists. Fixed (4 one-line escape corrections, comments only, no behavior change),
  `quality-gates.sh` green, shipped via quickmerge to `live-defi-rollout`: `unified-trading-library@24e8cf51`. Also set
  the `CLOUD_BUILD_PROD_DEPLOY_EXPECTED` repo variable to `true` for `unified-trading-library` specifically
  (`gh variable set`, confirmed via `gh variable list` — was unset) — a durable, repo-scoped hardening independent of
  slot-6's `notify-utl-base-image-not-configured` job above; both mechanisms now cover this repo, neither conflicts.
  **BLOCKED ON ELAPSED TIME, not a decision**: the fix is on `live-defi-rollout` but has not yet reached `main` via the
  standing `*/15` LDR→main promote cron (confirmed via `gh pr list --state merged` — last promote PR #643 merged
  11:08:40Z, before this fix landed) — `unified-trading-library-prod` reads its `cloudbuild.yaml` from `main` at
  invocation time, so re-firing before the promote lands would just reproduce the same INVALID_ARGUMENT. Next step
  (queued via ScheduleWakeup): once `git show origin/main:cloudbuild.yaml` shows the `$$VERSION` fix, re-run
  `gcloud builds triggers run unified-trading-library-prod --branch=main`, poll to `SUCCESS`, confirm a fresh
  `UPDATE_TIME` in the artifact registry, then flip todos 1+2 with evidence and `/done` the orchestrator task. IAM
  verified sufficient (the SA reached real INVALID_ARGUMENT, not PERMISSION_DENIED, on every test call — the router
  code's own comments flag PERMISSION_DENIED as a known separate failure mode, ruled out here).

- **2026-08-13 (slot 7, cicd) — RECURRENCE: trigger existed + fired, but every build TIMEOUTed (governor flip). Root
  cause was NOT a missing trigger this time.** The 2026-08-10 reservation-governor flip
  (`unified-trading-pm@67c4c42f92`, "flip default mode token -> reservation fleet-wide") made the `quality-gates` step
  in UTL's prod base-image build block forever in `[qg-governor] WAIT_RAM_LIVE` inside the ephemeral ~8GB `E2_HIGHCPU_8`
  Cloud Build container — `avail < peak(5500MB unmeasured default) + floor(2048MB)` is permanently true there, and
  `_qg_ledger_with_lock`/`_qg_try_reserve` admit-check on the CONTAINER's own `/proc/meminfo`, never a shared host.
  Every `unified-trading-library-prod` build from the flip onward (2026-08-10T18:10Z last SUCCESS → every build since =
  TIMEOUT at the 30-min timeout, base image stale 3 days) died in step `quality-gates`, not in any build step. **Two
  fixes shipped (both on `live-defi-rollout` + `main` by content):**
  1. `unified-trading-library@b8357437` — cloudbuild.yaml quality-gates step now exports
     `QG_GOVERNOR_DISABLE=true QG_TOTAL_GOVERNOR_DISABLE=true` (the governor's own documented "CI / single-run" bypass —
     an ephemeral single-build container has no shared multi-tenant host to coordinate with). Verified end-to-end:
     post-promote trigger builds `af475bfa` + `d464a9ab` completed **SUCCESS** through the full QG (no WAIT_RAM_LIVE
     hang), fresh base images republished 2026-08-13T15:12-15:14Z.
  2. `unified-trading-pm@bddffcf6fb` — cloud-build-router.yml `trigger_build_in_region` now reads the build ID from
     **stdout** (`>/tmp/build_trigger_out.txt`) instead of stderr.
     `gcloud builds triggers run --format=value(metadata.build.id)` writes the ID to STDOUT on success; the old code
     grepped `/tmp/build_trigger_err.txt` (always empty on success), so EVERY successful trigger invocation fell through
     to the `not-configured` branch → false CRITICAL alert + this escalation with empty `build_error_detail`, even while
     builds WERE being created (builds at 13:13/12:06/09:48 matching router invocations, all TIMEOUT). Verified live:
     manual `gcloud builds triggers run` returned `77447139-b5c2-4ec9-a819-94927ee133b5` on stdout, stderr empty.
     **Fleet scope**: among repos with QG-in-cloudbuild, only `unified-trading-library-prod` has a prod-deploy trigger
     exercised today; `instruments-service-prod` is healthy (SUCCESS); the other service repos
     (`execution/strategy/ml/ features-…-prod`) are build-only pre-cutover (no trigger). So the hang is UTL-specific,
     not fleet-wide. Escalation `agt-774a0e` (wall_type `cloud_build_router_failure`) resolved; if this doc's
     `escalate-utl-base-image-not-configured` fires again with a real (non-empty) error detail, read the error first —
     NOT_FOUND means recreate the trigger; WAIT_RAM_LIVE/TIMEOUT means re-check the governor-disable export survived in
     `cloudbuild.yaml`.

- **2026-08-13 (slot 7, cicd) — RECURRENCE: trigger existed + fired, but every build TIMEOUTed (governor flip). Root
  cause was NOT a missing trigger this time.** The 2026-08-10 reservation-governor flip
  (`unified-trading-pm@67c4c42f92`, "flip default mode token -> reservation fleet-wide") made the `quality-gates` step
  in UTL's prod base-image build block forever in `[qg-governor] WAIT_RAM_LIVE` inside the ephemeral ~8GB `E2_HIGHCPU_8`
  Cloud Build container — `avail < peak(5500MB unmeasured default) + floor(2048MB)` is permanently true there, and
  `_qg_ledger_with_lock`/`_qg_try_reserve` admit-check on the CONTAINER's own `/proc/meminfo`, never a shared host.
  Every `unified-trading-library-prod` build from the flip onward (2026-08-10T18:10Z last SUCCESS → every build since =
  TIMEOUT at the 30-min timeout, base image stale 3 days) died in step `quality-gates`, not in any build step. **Two
  fixes shipped (both on `live-defi-rollout` + `main` by content):**
  1. `unified-trading-library@b8357437` — cloudbuild.yaml quality-gates step now exports
     `QG_GOVERNOR_DISABLE=true QG_TOTAL_GOVERNOR_DISABLE=true` (the governor's own documented "CI / single-run" bypass —
     an ephemeral single-build container has no shared multi-tenant host to coordinate with). Verified end-to-end:
     post-promote trigger builds `af475bfa` + `d464a9ab` completed **SUCCESS** through the full QG (no WAIT_RAM_LIVE
     hang), fresh base images republished 2026-08-13T15:12-15:14Z.
  2. `unified-trading-pm@bddffcf6fb` — cloud-build-router.yml `trigger_build_in_region` now reads the build ID from
     **stdout** (`>/tmp/build_trigger_out.txt`) instead of stderr.
     `gcloud builds triggers run --format=value(metadata.build.id)` writes the ID to STDOUT on success; the old code
     grepped `/tmp/build_trigger_err.txt` (always empty on success), so EVERY successful trigger invocation fell through
     to the `not-configured` branch → false CRITICAL alert + this escalation with empty `build_error_detail`, even while
     builds WERE being created (builds at 13:13/12:06/09:48 matching router invocations, all TIMEOUT). Verified live:
     manual `gcloud builds triggers run` returned `77447139-b5c2-4ec9-a819-94927ee133b5` on stdout, stderr empty.
     **Fleet scope**: among repos with QG-in-cloudbuild, only `unified-trading-library-prod` has a prod-deploy trigger
     exercised today; `instruments-service-prod` is healthy (SUCCESS); the other service repos
     (`execution/strategy/ml/ features-…-prod`) are build-only pre-cutover (no trigger). So the hang is UTL-specific,
     not fleet-wide. Escalation `agt-774a0e` (wall_type `cloud_build_router_failure`) resolved; if this doc's
     `escalate-utl-base-image-not-configured` fires again with a real (non-empty) error detail, read the error first —
     NOT_FOUND means recreate the trigger; WAIT_RAM_LIVE/TIMEOUT means re-check the governor-disable export survived in
     `cloudbuild.yaml`.
