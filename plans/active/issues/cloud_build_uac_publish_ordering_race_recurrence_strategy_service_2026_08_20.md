---
doc_type: issue
title:
  strategy-service Cloud Build FAILURE = recurrence of the unified-api-contracts publish-ordering race — transient,
  self-healed once the wheel landed; no code fix warranted
summary: >-
  `cloud-build-failure-watcher` paged CRITICAL for strategy-service build `77fbf981` (main @ `bb3ff1b`,
  2026-08-20T11:02:18Z): docker step 6 `uv pip install` failed "× No solution found ... strategy-service==0.79.2
  depends on unified-api-contracts>=0.149.0,<1.0.0", while the newest wheel on `unified-libraries`@asia-northeast1 at
  that moment was only `0.148.1.dev1` (published 10:43:57Z). ROOT-CAUSED as a recurrence of the publish-ordering race
  documented in
  /plans/archive/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md: the
  `chore(deps): re-pin unified-api-contracts to 0.149.0 (major/breaking floor)` commit (`51471024`) was promoted to main
  and fired the Cloud Build ~12 min BEFORE UAC `0.149.0`'s wheel was published (11:14:57Z). NOT a code defect —
  strategy-service's GAR auth path (BuildKit-secret `gar_token` + `UV_EXTRA_INDEX_URL` + retry wrapper, shipped in the
  fleet-wide 2026-07-29/30 rollout) is present and correct, and the failing build log proves uv reached AR (it found the
  index, just not the version). VERIFIED RESOLVED by re-running the same commit: build `10283751` SUCCESS (7m47s) with
  log line `+ unified-api-contracts==0.149.0` and a fresh `strategy-service:latest` digest pushed. Systemic gap worth
  triaging: the floor-bump-promoted-before-wheel-published ordering race recurred ~3 weeks after the 2026-07-29 storm
  and hit at least 4 repos in the same window.
status: open
nature: issue
asset_group: [ci]
stage: [meta]
repos: [strategy-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: [ci, cloud-build, publish-ordering, artifact-registry, unified-api-contracts, race-condition, live-incident]
related:
  - /plans/archive/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md
  - /plans/active/issues/mtds_ldr_cloud_build_docker_step6_failure_2026_08_10.md
created: 2026-08-20
author: cloud-build-failure-watcher escalation (cicd, slot-11)
parent_epic: ci_master
priority: P2
source: cloud-build-failure-watcher CRITICAL for strategy-service build 77fbf981 (2026-08-20T11:02:18Z)
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-infra
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
last_updated: 2026-08-20
context_scope:
  [
    strategy-service/Dockerfile,
    strategy-service/pyproject.toml,
    strategy-service/cloudbuild.yaml,
    /plans/archive/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md,
  ]
---

# strategy-service Cloud Build — UAC publish-ordering race (recurrence, self-healed)

## Evidence (measured, not inferred)

- **Failing build** `77fbf981-185c-4a18-884b-814bac36b9b0` (main @ `bb3ff1b3`, 2026-08-20T11:02:18Z) — FAILURE,
  docker step 6 (the `RUN --mount=type=secret,id=gar_token UV_EXTRA_INDEX_URL=... uv pip install --system --no-sources -e .`
  retry-wrapper layer). Log:
  ```
  × No solution found when resolving dependencies:
  ╰─▶ Because only unified-api-contracts<=0.148.1.dev1+gfd4391914
      is available and strategy-service==0.79.2 depends on
      unified-api-contracts>=0.149.0,<1.0.0, we can conclude that ...
  uv pip install failed after 3 attempts
  ```
- **Wheel-availability timeline** (`gcloud artifacts versions list`): `0.148.1.dev1` @10:43:57Z →
  `0.149.0` @**11:14:57Z** (~12 min AFTER the failed build) → `0.149.1.dev1` @11:17:19Z. The floor-bump commit
  `51471024` in strategy-service pinned `unified-api-contracts>=0.149.0,<1.0.0` (pyproject.toml) and was promoted to
  main (`bb3ff1b3 chore(promote): LDR → main`) before the wheel existed.
- **Re-run build** `10283751-dc24-4cd7-aab0-9d76fbfcc77b` on the SAME commit `bb3ff1b3`: **SUCCESS** 11:30:26 →
  11:38:13Z (7m47s). Log line: `+ unified-api-contracts==0.149.0` (downloaded from AR, replacing the base-image-pinned
  dev version). Fresh `strategy-service:latest` pushed (digest `sha256:c3a451b2e31d...`); scan-check + notify-deployment
  steps finished.
- **Not a uv/pip.conf structural gap** (unlike the MTDS 2026-08-10 case): the failing log says "`unified-api-contracts`
  was found on https://asia-northeast1-python.pkg.dev/.../simple/ but not at the requested version" — uv reached AR, so
  publishing the wheel genuinely unblocks it. The BuildKit-secret auth pattern (fleet rollout in the 2026-07-29 doc) is
  present and correct.
- **Same-window sibling failures** (likely the same class, each its own wall/dispatch — NOT investigated here):
  `features-service-build` 11:14:32Z (20s BEFORE the wheel published), `instruments-service-prod` 11:03:50Z,
  `fund-administration-service-build` 11:03:20Z.

## Root cause

Recurrence of the **publish-ordering race**: a consuming repo's `chore(deps): re-pin unified-api-contracts to X.Y.0
(major/breaking floor)` lands on `live-defi-rollout`, gets promoted to `main`, and fires its Cloud Build **before**
`unified-api-contracts`'s own wheel for that version is published+propagated to Artifact Registry. The build then fails
with a now-fixed version requirement. Once the wheel lands, a re-build succeeds. Exactly the class documented (and
closed) in `cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md` — that incident's *structural* fix
(uv actually reaching AR) was shipped fleet-wide, but the *ordering* coordination itself was never enforced, so the
race recurs on the fleet's routine floor-bump cadence.

## Why this matters

- The GH Actions `quality-gates-v2` gate can be green while the Cloud Build image pipeline is red — separate pipelines
  (per the watcher's dispatch context). A stale red build looks like a persistent break when it is a transient window.
- 2nd occurrence of this class in ~3 weeks, 4 repos this window → without an ordering guard, every future
  `re-pin unified-api-contracts` floor-bump that races its wheel publish re-pages the watcher.

## Todos

- [x] ✅ [CICD] P1. **Diagnose + verify resolved.** Root-caused to the publish-ordering race; re-ran the
      `strategy-service-build` trigger on the same failing commit (`bb3ff1b3`) → build `10283751` SUCCESS; log confirms
      `+ unified-api-contracts==0.149.0`; fresh `:latest` pushed. Wall closed, no strategy-service code change made.
- [ ] [OPERATOR] P3. **Decide whether to enforce wheel-published-before-promotion ordering** for
      `unified-api-contracts` floor-bumps (e.g. a release-pipeline gating step, or a wider build-time retry window) so
      this class stops recurring — 2nd storm in ~3 weeks (2026-07-29 ×7 repos, 2026-08-20 ×≥4 repos). Judgment call on
      mechanism + effort; leave this issue `open` until decided. Repo: unified-trading-pm / unified-api-contracts.

## Progress Log

- **2026-08-20 (cicd slot-11, escalation `agt-8ab43f`)** — Verified resolved LIVE: failing build `77fbf981` root-caused
  to the UAC publish-ordering race; UAC `0.149.0` wheel confirmed live+resolvable on AR (HTTP 200); re-ran
  `strategy-service-build` on the same main HEAD → `10283751` SUCCESS (11:30:26→11:38:13Z), log shows
  `+ unified-api-contracts==0.149.0` installed from AR and `strategy-service:latest` re-pushed. No code change shipped —
  the pipeline was never structurally broken. Sibling failures noted for their own walls. Escalation closed.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries).
