---
title:
  "deployment-api Cloud Build broken since 2026-06-10 — template rollout dropped the fetch-ui step (cloud image frozen
  at 05-19)"
created: 2026-06-14
author: slot-3 (operator deploy request)
source:
  - gcloud builds list deployment-api-build → FAILURE on 2026-06-10 (×2) + 2026-06-11; last SUCCESS image 2026-05-19
  - git show b80f05c~1:cloudbuild.yaml has fetch-ui (10 matches); b80f05c + current LDR have 0
locked_by: live-defi-rollout
---

## What I found

The `deployment-api-build` Cloud Build trigger (fires on `main` push, asia-northeast1) has FAILED on every run since
~2026-06-10 (06-10 ×2, 06-11), at step 3 `docker build` (exit 1). Consequently the live Cloud Run service
`uts-shared-deployment-api` (https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app) is frozen on the last green
image, **built 2026-05-19** (revision 00022-kq5) — ~26 days stale.

Root cause: deployment-api's `cloudbuild.yaml` previously carried a repo-specific **`fetch-ui`** step that git-clones
`IggyIkenna/deployment-ui` into `./ui/` so the Dockerfile Stage-0 SPA bundling (`COPY ui/…`) has a populated context
(`ab3215d feat(deploy): bake deployment-ui SPA into deployment-api image`;
`a64a850 fix(cloudbuild): fetch-ui skips if ui pre-bundled`). The template rollout **`b80f05c` ci(cloudbuild):
digest-aware base pre-pull from PM template SSOT** overwrote cloudbuild.yaml with the GENERIC api template — which has
**no fetch-ui step** — so `COPY ui/` now fails on a clean cloud build context. Verified: `b80f05c~1:cloudbuild.yaml` →
10 fetch-ui/deployment-ui matches; `b80f05c` + current LDR → 0.

## Why it matters

- **Every deployment-api deploy is blocked** (devops dashboard + the shared deployment API). No image has shipped in 26
  days; promoting LDR→main does NOT help — the resulting build fails identically.
- It's a **template-SSOT regression**: the generic API template clobbers a required per-repo customisation. A naive
  per-repo restore re-drifts from the template and will be re-clobbered by the next rollout.

## Recommended decision

Fix in the PM workflow-template SSOT, not just the per-repo copy: either (a) add a guarded `fetch-ui` step to
`scripts/workflow-templates/<api cloudbuild template>` that no-ops when `./ui` is absent (so only deployment-api
populates it), or (b) exempt deployment-api's cloudbuild from the generic template + restore its fetch-ui per-repo +
baseline the drift. Then: promote LDR→main, confirm the build goes green, and
`gcloud run deploy uts-shared-deployment-api --image …:<sha>` (deploys are manual — no auto-deploy trigger; revisions
00020-22 on 05-19 were the last manual deploys). Pipeline-unblock carve-out applies (a corrected build can't pass
through the build it is fixing).
