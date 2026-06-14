---
title:
  "deployment-api Cloud Build broken since 2026-06-10 — template rollout dropped the fetch-ui step (cloud image frozen
  at 05-19)"
created: 2026-06-14
source:
  - gcloud builds list deployment-api-build → FAILURE on 2026-06-10 (×2) + 2026-06-11; last SUCCESS image 2026-05-19
  - git show b80f05c~1:cloudbuild.yaml has fetch-ui (10 matches); b80f05c + current LDR have 0
locked_by: live-defi-rollout
priority: P2
status: active
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

## Resolution log (2026-06-14)

The fetch-ui drop was only the FIRST of several stacked breakages. Full chain, all fixed:

1. **`fetch-ui` dropped** (above) — restored to the PM api-cloudbuild template `configs/cloudbuild-api-template.yaml`,
   self-guarded to `deployment-api` (no-op for other api repos), rolled out to deployment-api + client-reporting-api.
2. **Private-repo clone auth** — deployment-ui is PRIVATE; the restored `git clone` failed `could not read Username`.
   Fixed: fetch `GH_PAT` from Secret Manager (default Cloud Build SA already has `secretAccessor`) and pass it as an
   http **Basic** extraheader (`bearer` is rejected by GitHub for a PAT).
3. **Missing `--build-arg PROJECT_ID`** — the api template's `build` step never passed it, so the digest-pinned base
   `FROM .../unified-trading-library@${BASE_IMAGE_DIGEST}` expanded to an invalid reference. Added (service template
   already had it).
4. **Missing `pull-base-image` step** — the in-build base pull was unauthenticated → `denied`. Added the digest-aware
   pre-pull step (copied from the service template).
5. **`.gitignore data/` strips `ui/src/data/` from the `gcloud builds submit` upload** — deploy-shared.sh PRE-BUNDLES
   ui into the upload context, and `gcloud builds submit` filters by `.gitignore` (no `.gcloudignore`). The unanchored
   `data/` rule (line 87) also matches `ui/src/data/` → the `capability-manifest-loader.ts` / `capability-verdict-
   matrix-loader.ts` app sources were stripped → in-image `tsc` failed `Cannot find module '../data/…'` (+ cascading
   TS7006/TS2366). Fixed by adding a `deployment-api/.gcloudignore` that anchors `/data/` to root only (keeps
   `ui/src/data/`). The trigger build escaped this only because it git-clones ui IN-CONTAINER (after upload).

**The real deploy path is `deployment-service/scripts/cloud-run/deploy-shared.sh` → `cloudbuild-tier3.yaml`**, NOT the
bare `deployment-api-build` trigger. The script rsyncs the sibling repos (`ui/`, `_deployment-service/`,
`_unified-api-contracts/`) and materialises the PM symlinks (`codex-data/`, `pm-plans/`, `pm-configs/`) into the build
context, then `gcloud builds submit` + `gcloud run deploy`.

## Residual decision (the trigger path is fundamentally incomplete for deployment-api)

The `deployment-api-build` trigger (fires on `main` push, builds `cloudbuild.yaml`) **cannot** build deployment-api even
with fixes 1-4: the Dockerfile `COPY _unified-api-contracts/ /tmp/_uac/` (+ `_deployment-service/`, `codex-data/`,
`pm-plans/`, `pm-configs/`) require those vendored dirs in the build context, which ONLY deploy-shared.sh materialises.
The trigger fetches just the deployment-api git ref → those COPYs fail. Decide one of:

- (a) Add authenticated in-build vendoring steps to the trigger's cloudbuild (clone the 3 sibling repos via GH_PAT, like
  fetch-ui) so `main`-push auto-builds work end-to-end; or
- (b) Formally retire/disable the `deployment-api-build` trigger and make `deploy-shared.sh` the sole, documented deploy
  path (a scheduled or manual operator action), since deploys are already manual (no auto-deploy trigger).

Until then: deploys are via `deploy-shared.sh` (build + Cloud Run roll in one). Pipeline-unblock carve-out applied to the
cloudbuild/.gcloudignore commits (a corrected build can't pass through the build it is fixing).
