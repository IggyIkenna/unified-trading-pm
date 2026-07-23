---
doc_type: issue
title: >-
  Build/deploy pipeline gaps surfaced by the artifact-pipeline audit — two CONFIRMED AWS-lane bugs (deferred-build
  replay never matches the AWS artifact name; tarball launcher points at a nonexistent bucket) plus two GCP-side
  observability gaps; several 2026-07-17 findings verified already-fixed or not-a-bug
summary: >-
  The /ops/artifacts mock audit (plans/active/artifact_pipeline_observability_2026_07_17.md) turned up a set of
  build/deploy pipeline defects. Re-verified against CURRENT code 2026-07-21 (the CI area was actively fixed
  2026-07-20), most resolved themselves — this doc parks only what is genuinely still open. CONFIRMED still-open - (#4)
  the AWS build router names its freeze-deferred artifact `deferred-aws-build-*` (cloud-build-router-aws.yml:83) but
  freeze-deferred-build-replay.yml filters `startswith("deferred-build-")` (:112,:189), so AWS freeze-deferred builds
  never replay; (#7) the AWS tarball launcher reads `s3://unified-trading-deployment-scripts-<account>`
  (aws_ec2_launch_lib.sh:232,285) which returns 404 live, while the uploader writes to
  `s3://uts-prod-deployment-state/code/` (populated 2026-07-21) — two bucket names, no overlap. BOTH are AWS-lane and
  AWS is intentionally parked (no credits), so they are deferred-with-AWS, not urgent. Plus two GCP-side gaps - (#1)
  image tags went version+SHA -> SHA-only ~late June (root cause unconfirmed); (#3) the cicd-events ledger carries no
  build_id. VERIFIED NOT OPEN (do not re-investigate) - failure-watcher repo attribution was FIXED 2026-07-20; the
  REPO_NAME/_REPO_NAME history concern was never reproduced; the tarball VM provenance stamp is tracked as
  artifact_pipeline Phase 3c.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm, deployment-service, deployment-api]
scope: [engineer, admin]
tags: [ci-cd, cloud-build, image-builds, tarballs, aws-deferred, deployment-observability, provenance]
related:
  [
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/archive/issues/change_freeze_calendar_protects_nothing_for_much_of_the_year_2026_07_20.md,
    /plans/active/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md,
  ]
created: 2026-07-21
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
assigned_role: devops
drift_direction: advance-code
depends_on: []
source:
  [
    "surfaced 2026-07-17 during the /ops/artifacts (artifact-pipeline observability) mock audit; re-verified against
    current code 2026-07-21",
  ]
locked_by:
locked_since:
resolved_by:
---

# Build/deploy pipeline provenance + AWS-deferred gaps

**Page-first, do NOT fix here** (operator 2026-07-21): the /ops/artifacts page reads the clouds directly and works
regardless of these, so they are parked, not blockers. This is the coordination-aware home for them — most live in CI
files that **Ikenna is actively editing** (loop him in before touching any of them; he already fixed several below on
2026-07-20). **AWS context:** AWS (App Runner + ECS + ECR + the AWS tarball lane) is **intentionally deferred — no AWS
credits**; GCP is the sole active production path. The two AWS bugs here are real but deferred-with-AWS, to be fixed
when AWS resumes (fixing the code is free; only creating/deploying AWS images costs credits).

## Still open (verified against current code 2026-07-21)

### #4 — AWS freeze-deferred builds never replay (CONFIRMED · AWS-deferred)

The AWS build router names its deferred-on-freeze artifact `deferred-aws-build-<repo>-<version>-…`
(`.github/workflows/cloud-build-router-aws.yml:83`), whereas the GCP router uses `deferred-build-…`
(`cloud-build-router.yml`). But `freeze-deferred-build-replay.yml` drains only
`select(.name | startswith("deferred-build-"))` (`:112` and the stale-guard at `:189`). `deferred-aws-build-` does not
start with `deferred-build-`, so **an AWS build deferred during a change-freeze is never replayed** — it silently
expires. Impact is currently nil (AWS parked), but it will bite the moment AWS resumes and a freeze coincides with an
AWS build. **Fix (one line, when AWS resumes):** widen the filter to
`startswith("deferred-build-") or startswith("deferred-aws-build-")`, or normalise the two routers to a shared prefix.
**Owner: CI (Ikenna) — his file, edited 24h before this doc.**

### #7 — AWS tarball launcher points at a bucket that does not exist (CONFIRMED · AWS-deferred)

`aws_ec2_launch_lib.sh:232,285` derives the code bucket as `unified-trading-deployment-scripts-<account>` →
`unified-trading-deployment-scripts-427895769566`. Live check 2026-07-21: `aws s3api head-bucket` → **404 Not Found** —
the bucket does not exist. The tarball **uploader** (`create-code-tarballs.sh`) writes to
`s3://uts-prod-deployment-state/code/`, which **is** populated (e.g. `deployment-service-code.tar.gz`, uploaded
2026-07-21 09:27Z). So the two halves of the AWS tarball lane disagree on the bucket name and an AWS tarball VM launch
would fail to fetch code. (Note: this corrects the 2026-07-17 finding, which said `code/` had 0 objects — the uploader
side is now producing objects; the launcher-side bucket mismatch is the remaining defect.) **Fix (when AWS resumes):**
point both halves at one bucket. **AWS-deferred.**

### #1 — GCP image tags lost their version (SHA-only) ~late June (root cause UNCONFIRMED)

Registry evidence: GCP Artifact Registry image tags went `version+SHA` → SHA-only around late June, and the one still-
pushing ECR repo (`market-tick-data-service`) is `latest`-only. The routers read `client_payload.version`
(`cloud-build-router.yml`, `-aws.yml`), so if the `qg-passed` dispatch omits `version`, the tag loses it. **Not yet
root-caused** — could be an intentional move to SHA-only tagging rather than a defect. Needs a confirmed
dispatch-payload inspection before designing a fix. **Owner: CI (Ikenna/Harsh area) — do not assume it is a bug.**

### #3 — cicd-events ledger carries no build_id (LOW confidence · minor)

The GCS `unified-trading-cicd-events` ledger (written via `log-event.yml`) does not appear to persist a Cloud Build
`build_id`, so a ledger row can't be joined back to its build record. Low-signal observability nicety; verify before
acting. (The artifact-pipeline page does not depend on this — it reads the Cloud Build API directly.)

## Verified NOT open — do not re-investigate

- **Failure-watcher stamped its own repo / only free-text Slack — FIXED 2026-07-20.** `cloud-build-failure-watcher.yml`
  now resolves the failing repo via `REPO_KEYS = ("_REPO_NAME", "REPO_NAME", "REPO_FULL_NAME")` with fallback
  (`:137,:183`), names manual `gcloud builds submit` failures explicitly (`:211-214`), and routes through
  `notify-slack.yml` with a content `dedup_key` (transition-based, persisted). The 2026-07-17 "stamps
  `repo: unified-trading-pm`" finding is stale.
- **`REPO_NAME` vs `_REPO_NAME` build-history blind spot — NOT reproduced.** `_cloud_builds_history.py` keys on
  `REPO_NAME` (`:223`) and the code+comments assert every Cloud Build carries it; the manual-tier3 path gained a
  `_SERVICE_NAME` fallback (`:183`). The 2026-07-17 concern was UNVERIFIED then and did not reproduce on re-check.
- **Tarball VM runtime provenance stamp — tracked as artifact_pipeline Phase 3c.** The commit SHA is now measured at
  boot (`setup-data-pipeline-vm.sh:706`, used for pin/drift verification); the remaining work is stamping it onto the
  registry entry so `bom.py` can read it. Owned by `plans/active/artifact_pipeline_observability_2026_07_17.md` (Phase
  3c, audited YES-WITH-CONDITIONS), not this doc.
- **AWS App Runner PAUSED / ECR estate idle — INTENTIONAL, not bugs.** Both prod App Runner services PAUSED, 3 ECS
  services `desired=0`, ECR estate idle = **deliberate parking** (AWS deferred, no credits), not breakage. See the
  artifact_pipeline plan's "AWS is intentionally parked" section.

## Todos

- [ ] [DEVOPS] P2. **#4** — coordinate with Ikenna; when AWS resumes, widen the replay filter to also match
      `deferred-aws-build-*` (or normalise the two routers to one prefix). `freeze-deferred-build-replay.yml:112,189`.
      AWS-deferred — verify by a real freeze-window replay once AWS is live.
- [ ] [DEVOPS] P2. **#7** — point the AWS tarball uploader and launcher at one bucket (`aws_ec2_launch_lib.sh:232,285`
      vs `create-code-tarballs.sh` → `uts-prod-deployment-state/code/`). AWS-deferred — verify by a real AWS tarball VM
      launch once AWS is live.
- [ ] [DEVOPS] P3. **#1** — inspect a real `qg-passed` dispatch payload to confirm whether `version` is sent; decide if
      SHA-only tagging is intentional before any fix. Coordinate with Ikenna/Harsh (CI area).
- [ ] [DEVOPS] P3. **#3** — confirm whether the cicd-events ledger should carry `build_id`; low priority.

## Progress Log

- **2026-07-21** — Filed. Re-verified all 2026-07-17 artifact-pipeline audit findings against current code (the CI area
  was actively fixed 2026-07-20). Result: #5 already fixed, #2 not-a-bug, #6 plan-tracked; only #4 + #7 (both AWS-lane,
  AWS-deferred) and the GCP-side #1/#3 remain open. Live probe confirmed
  `unified-trading-deployment-scripts-427895769566` is 404 and `uts-prod-deployment-state/code/` is populated. No
  existing issue doc covered these; the adjacent `change_freeze_…` doc (resolved) is about the freeze calendar, not the
  replay-filter naming. Loop Ikenna in before any fix — every open item lives in a file in his active CI area.
