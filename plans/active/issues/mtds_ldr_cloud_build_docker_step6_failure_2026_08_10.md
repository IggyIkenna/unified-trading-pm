---
doc_type: issue
title:
  market-tick-data-service LDR Cloud Build fails at docker step 6 — genuine image-build break, distinct from the
  (expected) missing -prod trigger it was conflated with
summary: >-
  `cloud-build-failure-watcher` paged CRITICAL at 2026-08-10T13:32Z for `market-tick-data-service@f6b7f8b`, build
  `b5342e0a-3a83-4096-b004-4a66e03fc528`. Confirmed via `gcloud builds describe`: status FAILURE, `USER_BUILD_STEP`,
  "Build step failure: build step 6 `gcr.io/cloud-builders/docker` failed: step exited with non-zero status: 1", fired
  by the `market-tick-data-service-live-defi-rollout` trigger in `central-element-323112` / `asia-northeast1`. This is a
  REAL image-build break and is NOT yet diagnosed — the failing step's log has not been read. It surfaced in the same
  window as a `cloud-build-router` NOT_FOUND for market-tick-data-service, and the two are DIFFERENT things that are
  easy to conflate (see § "Do not conflate" below).
status: open
nature: issue
asset_group: [cefi, cross-cutting]
stage: [meta]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [ci, cloud-build, docker, image-build, mtds, live-incident]
related:
  - /plans/active/issues/ldr_docs_gate_red_but_silent_inherited_e_aborts_verdict_2026_08_10.md
  - /plans/active/issues/na_corpus_ratchet_diff_base_vs_lagging_main_deadlocks_promotion_2026_08_10.md
  - /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md
created: 2026-08-10
author: /ci-reconcile (interactive, slot-2·laptop)
parent_epic: infrastructure_master
priority: P2
source: >-
  /ci-reconcile sweep of #ci-failures, 2026-08-10 — the third of three alerts in the 13:07-13:36Z window (the other two,
  the cloud-build-router empty-error-detail bug and the PM quality-gates false CRITICAL, are both root-caused and
  fixed).
assigned_vm: NA
execution_scope: local-only
drift_direction: advance-infra
depends_on: []
locked_by:
supersedes:
superseded_by:
resolved_by: ""
last_updated: 2026-08-10
context_scope:
  [
    market-tick-data-service/Dockerfile,
    market-tick-data-service/cloudbuild.yaml,
    unified-trading-pm/.github/workflows/cloud-build-router.yml,
  ]
---

# MTDS LDR image build fails at docker step 6

## Evidence (measured, not inferred)

```
$ gcloud builds describe b5342e0a-3a83-4096-b004-4a66e03fc528 \
    --project=central-element-323112 --region=asia-northeast1
FAILURE   market-tick-data-service-live-defi-rollout   USER_BUILD_STEP
Build step failure: build step 6 "gcr.io/cloud-builders/docker" failed: step exited with non-zero status: 1
```

`USER_BUILD_STEP` means the build's own step failed — this is not infra, quota, or a config rejection. The step-6 log
has NOT been read yet; that is the first action below.

## Do not conflate these two — they appeared together and are unrelated

1. **This issue**: the `-live-defi-rollout` trigger EXISTS, fired, and its build FAILED in docker step 6. Real break.
2. **A separate `cloud-build-router` NOT_FOUND for market-tick-data-service** (run 31391433509, 13:09Z): the router
   looked for an MTDS **`-prod`** trigger and got `NOT_FOUND`. MTDS has `market-tick-data-service-build`,
   `-feature-build` and `-live-defi-rollout` in `asia-northeast1`, but **no `-prod`**. Per the router's own UTL alert
   text, a missing prod trigger is an intentional pre-cutover state for every repo EXCEPT `unified-trading-library`
   ("This is NEVER an intentional pre-cutover state (unlike other repos' prod triggers)"). So MTDS having no `-prod`
   trigger is most likely EXPECTED — but that has NOT been verified against the cutover register, hence the todo below
   rather than a closed finding.

Related and already fixed this session: the router's `build_error_detail` was reaching Slack EMPTY on every gcloud
failure (Actions refuses an output containing a masked secret, and gcloud embeds the SA identity in every error), which
is why these two MTDS conditions were hard to tell apart from the alert alone.

## Todos

- [ ] [BACKEND] P2. **Read step 6's log and fix the build.**
      `gcloud builds log b5342e0a-3a83-4096-b004-4a66e03fc528     --project=central-element-323112 --region=asia-northeast1`
      (or the console link in the alert), identify which docker invocation step 6 is in
      `market-tick-data-service/cloudbuild.yaml`, and fix the root cause. Check first whether it is a knock-on of the
      stale UTL base image every service Dockerfile `FROM`s — `unified-trading-library` publishing has been the subject
      of repeated router alerts, and a stale/missing base tag surfaces exactly as a non-zero docker step. Repo:
      market-tick-data-service. Done-when: a fresh LDR build for MTDS reaches SUCCESS.
- [ ] [OPERATOR] P3. **Confirm MTDS having no `-prod` Cloud Build trigger is intentional** (pre-cutover), not an
      accidental deletion like the UTL one that
      `utl_prod_cloud_build_trigger_missing_fleet_stale_base_image_2026_07_25.md` tracks. If intentional, note it in the
      cutover register so the next sweep does not re-investigate; if not, recreate it mirroring
      `instruments-service-prod`. Repo: unified-trading-pm (register) / GCP.
- [ ] [BACKEND] P3. **`scripts/self-hosted-runners/hosted-baseline/cloud-build-router.yml` is now stale** vs the live
      workflow — this session fixed `build_error_detail` (credential-preamble strip + SA/credential-path scrub) in the
      LIVE `.github/workflows/cloud-build-router.yml` only. That baseline is a `derived` snapshot per its own
      `MANIFEST.tsv` (regenerated by `hosted-baseline.sh`), and NO QG check enforces parity, so the drift is silent.
      Re-run `hosted-baseline.sh` (or document that the snapshot is intentionally pinned). Repo: unified-trading-pm.

## Progress Log

- **2026-08-10 (/ci-reconcile, slot-2·laptop)** — Filed while checkpointing at ~67% context. The build failure itself is
  UNDIAGNOSED by design of the handoff: the operator asked for it to be taken next, and it needs the step-6 log read
  with fresh context rather than a guess appended here. Everything else from that alert window is already fixed and
  pushed (`cloud-build-router` empty-error-detail + credential scrub; the PM quality-gates false CRITICAL, which was an
  hourly LDR `workflow_dispatch` measuring the whole unpromoted backlog and NOT the innocent codex-docs commit the alert
  named).
