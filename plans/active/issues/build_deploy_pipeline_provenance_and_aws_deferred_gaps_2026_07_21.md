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
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm, deployment-service, deployment-api]
scope: [engineer, admin]
tags: [ci-cd, cloud-build, image-builds, tarballs, aws-deferred, deployment-observability, provenance]
related:
  [
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    /plans/archive/issues/change_freeze_calendar_protects_nothing_for_much_of_the_year_2026_07_20.md,
    /plans/archive/issues/cloudbuild_template_behind_repos_rollout_would_regress_fleet_2026_07_20.md,
  ]
created: 2026-07-21
author: unknown
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
context_scope:
  [
    /plans/active/artifact_pipeline_observability_2026_07_17.md,
    unified-trading-pm/.github/workflows/freeze-deferred-build-replay.yml,
    unified-trading-pm/.github/workflows/cloud-build-router-aws.yml,
    deployment-service/scripts/vm/lib/aws_ec2_launch_lib.sh,
    deployment-service/scripts/vm/create-code-tarballs.sh,
  ]
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

### #1 — GCP image tags lost their version (SHA-only) ~late June — **RESOLVED 2026-07-24, NOT A BUG**

Registry evidence: GCP Artifact Registry image tags went `version+SHA` → SHA-only around late June, and the one still-
pushing ECR repo (`market-tick-data-service`) is `latest`-only. The routers read `client_payload.version`
(`cloud-build-router.yml`, `-aws.yml`), so if the `qg-passed` dispatch omits `version`, the tag loses it. **Root cause
CONFIRMED 2026-07-24 (operator)**: the semver-agent that would compute + send `version` in the build dispatch payload is
**dead, deliberately** — "we have kept it dead deliberately." SHA-only tagging is the expected, intentional consequence,
not a defect. **Not a bug — no fix needed.** (Source: `artifact_pipeline_observability_2026_07_17.md` Progress Log
2026-07-24; the source doc itself flagged this correction as an owed follow-up to this issue doc.)

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

- [x] ✅ [DEVOPS] P2. **#4 — SHIPPED 2026-08-07, `unified-trading-pm@b87cc06fcf`.** Operator: "do the code fixes, just
      don't permanently run live vms or do heavy backfills on aws until we have credits again." Widened both
      `freeze-deferred-build-replay.yml` filters (lines 112, 189) to match either `deferred-build-` or
      `deferred-aws-build-`. **Not verified by a real freeze-window replay** — AWS stays intentionally parked, per the
      operator's own constraint; verify live once AWS resumes.
- [x] ✅ [DEVOPS] P2. **#7 — SHIPPED 2026-08-07, `deployment-service@61cf93f44`.** Fixed `lc_aws_code_bucket()` + the
      log-upload trap block in `aws_ec2_launch_lib.sh`, plus the same hardcoded wrong bucket name duplicated in all 6
      AWS launcher heredocs
      (`launch-{cefi-sharded-backfill,defi-backfill-vm,features-backfill-vm, instruments-backfill-vm,mtds-backfill-vm,mdps-backfill-vm}-aws.sh`)
      — all now point at `uts-prod-deployment-state`, matching `create-code-tarballs.sh`'s real uploader target. Wider
      than the originally-cited 2 line numbers: the same wrong bucket was duplicated 6 more times in launcher heredocs,
      not caught by the original finding. **Not verified by a real AWS tarball VM launch** — same AWS-deferred
      constraint as #4.
- [x] ✅ [DEVOPS] P3. **#1** — RESOLVED 2026-07-24 (operator confirmed): the semver-agent is dead deliberately; SHA-only
      tagging is the expected, intentional consequence, not a defect. No dispatch-payload inspection or fix needed.
      Evidence: `artifact_pipeline_observability_2026_07_17.md` Progress Log 2026-07-24.
- [ ] [DEVOPS] P3. **#3** — confirm whether the cicd-events ledger should carry `build_id`; low priority.

## Progress Log

- **2026-07-21** — Filed. Re-verified all 2026-07-17 artifact-pipeline audit findings against current code (the CI area
  was actively fixed 2026-07-20). Result: #5 already fixed, #2 not-a-bug, #6 plan-tracked; only #4 + #7 (both AWS-lane,
  AWS-deferred) and the GCP-side #1/#3 remain open. Live probe confirmed
  `unified-trading-deployment-scripts-427895769566` is 404 and `uts-prod-deployment-state/code/` is populated. No
  existing issue doc covered these; the adjacent `change_freeze_…` doc (resolved) is about the freeze calendar, not the
  replay-filter naming. Loop Ikenna in before any fix — every open item lives in a file in his active CI area.
- **context-scout 2026-08-01**: populated context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries, unchanged) — verified all still accurate and
  resolve.

## na-eligibility-audit verdict

**na-eligibility-audit 2026-07-30** (tranche `ci`, autonomous): KEEP-NA, valid — carries an explicit dated operator
ruling at the top of the doc ("Page-first, do NOT fix here", operator 2026-07-21). #4 and #7 are AWS-lane and gated on
AWS credits resuming; #1 and #3 are explicitly framed as "do not assume it is a bug" judgment calls in an
actively-edited CI area requiring coordination. Ruling confirmed present, not re-derived.

**na-eligibility-audit 2026-08-02** (tranche `ci`, autonomous): **CONFIRMS the verdict above, unchanged.** Re-read
end-to-end; all 4 open todos re-verified against the rubric (#4 + #7 AWS-lane gated on credits resuming, #1 + #3
explicit "do not assume it is a bug" / "confirm whether" judgment calls). The only change since the last marker is the
2026-08-01 context-scout `context_scope` backfill — pure metadata, zero content movement, so nothing to re-verdict. The
operator ruling was re-confirmed present verbatim, not re-derived.

**na-eligibility-audit 2026-08-03** (tranche `ci`, autonomous, `agt-4acc10`): **CONFIRMS the verdict above, unchanged.**
Re-read end-to-end; only change since the last marker is a `context_scope backfill batch 2/5` commit (metadata-only,
verified via diff — one line added to the `context_scope` list, zero content movement). All 4 items re-verified against
the same top-of-doc operator ruling and file-ownership coordination gates; cross-checked against
`ci_satellite_ao_dispatch_batch1_2026_07_26.md` D26 (verbatim match, all 4 items, consistent un-dispatched status). No
RECLASSIFY, no ARCHIVE.

- **context-scout 2026-08-05**: re-scouted; context_scope re-verified (5 entries), unchanged.

**na-eligibility-audit 2026-08-06**: KEEP-NA, valid — operator ruling Page-first, AWS-lane gated on credits

- **context-scout 2026-08-07**: refreshed context_scope (5 entries) — fixed the two `.github/workflows/*.yml` entries to
  carry their real repo prefix (`unified-trading-pm/...`, not `deployment-service/...` — those workflow files actually
  live in the PM repo; confirmed both are absent from `deployment-service/.github/workflows/`).

**na-eligibility-audit 2026-08-07** (tranche `ci`, autonomous, `agt-cbbd1f`): KEEP-NA, valid — re-verified all 4 open
items. Only change since the last marker was a `related:` path fixup (one archived-doc reference corrected), zero
content/todo change — confirmed via `git show 50b8643dc`. Dated operator ruling ("Page-first, do NOT fix here",
2026-07-21) still governs #4/#7 (AWS-lane, credit-gated); #1/#3 remain explicit judgment calls in a CI area under active
named-owner coordination. No `assigned_vm` change.

- **2026-08-08 (ui_satellite_ao_dispatch_batch1-002, slot 10)**: Applied confirmed-dead-semver-agent finding to `#1`
  section and todo — root cause confirmed 2026-07-24 by operator: "the semver-agent that was supposed to write the
  version is dead right now and we have kept it dead deliberately." SHA-only tagging is intentional, not a defect; `#1`
  is not a bug. Closed `#1` todo `[x]`. Source: `artifact_pipeline_observability_2026_07_17.md` Progress Log 2026-07-24
  (flagged as owed follow-up to this doc) + `/plans/active/ui_satellite_ao_dispatch_batch1_2026_08_06.md` todo 2.
  **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid — the sole remaining open item (`#3`,
  confirm whether the cicd-events ledger should carry `build_id`) checked against today's 9 operator-Q&A precedents;
  none apply — it is a low-confidence "confirm whether" judgment call, not an IAM gap, a carve/tiering/context_scope/
  escalation/deletion/Option-B/AWS question, or a script gap with an exact sibling precedent. The doc's standing
  "page-first, do NOT fix here" operator ruling (2026-07-21) still governs the file-ownership coordination posture. No
  `assigned_vm` change.
- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.

**na-eligibility-audit 2026-08-09** (ci tranche, autonomous, dispatch agt-4e0ea5) [body-hash:c53f3136e574ad22]: KEEP-NA,
valid — re-verified the sole open item (#3, cicd-events ledger `build_id`), still an explicit low-confidence judgment
call. Independently re-confirmed by today's batch7 fresh full read ("0 extractable... explicit low-confidence judgment
call"). No `assigned_vm` change.
