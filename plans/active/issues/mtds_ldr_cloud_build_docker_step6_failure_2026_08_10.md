---
doc_type: issue
title:
  market-tick-data-service LDR Cloud Build fails at docker step 6 — genuine image-build break, distinct from the
  (expected) missing -prod trigger it was conflated with
summary: >-
  `cloud-build-failure-watcher` paged CRITICAL at 2026-08-10T13:32Z for `market-tick-data-service@f6b7f8b`, build
  `b5342e0a-3a83-4096-b004-4a66e03fc528`. Confirmed via `gcloud builds describe`: status FAILURE, `USER_BUILD_STEP`,
  "Build step failure: build step 6 `gcr.io/cloud-builders/docker` failed: step exited with non-zero status: 1", fired
  by the `market-tick-data-service-live-defi-rollout` trigger in `central-element-323112` / `asia-northeast1`.
  ROOT-CAUSED and FIXED 2026-08-10 (market-tick-data-service@0eb8aa2c8e): three compounding defects in step 6's
  workspace-dep install — a registry fallthrough that could never succeed (`--no-sources` drops UTL's local path pin,
  and uv does not read pip.conf so the Artifact Registry index is invisible to it), a base-image-inherited
  `SETUPTOOLS_SCM_PRETEND_VERSION` mis-stamping both staged clones, and `--no-sources` silently defeating UAC's
  patched-fork `prek` pin. NOT the stale base image this doc originally guessed at. It surfaced in the same window as a
  `cloud-build-router` NOT_FOUND for market-tick-data-service, and the two are DIFFERENT things that are easy to
  conflate (see § "Do not conflate" below).
status: open
nature: issue
asset_group: [cross-cutting]
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

`USER_BUILD_STEP` means the build's own step failed — this is not infra, quota, or a config rejection.

## Root cause (three compounding defects, all in step 6's workspace-dep install)

Step 5 `pull-base-image` COMPLETED. The failure is step 6's `RUN uv pip install ... -e .deps/unified-trading-library`:

```
× No solution found when resolving dependencies:
╰─▶ Because unified-api-contracts was not found in the package registry and
    unified-trading-library==0.76.3 depends on unified-api-contracts>=0.110.0,<1.0.0 ...
```

**1 — Registry fallthrough that could never succeed.** `--no-sources` disables UTL's own
`[tool.uv.sources.unified-api-contracts]` path pin, so installing UTL ALONE left no local UAC in that resolution and uv
fell through to a package registry. **uv does not read pip's config files**, so the `extra-index-url` in the `pip.conf`
the Dockerfile copies (and the one baked into the base image) is invisible to it — uv only ever saw PyPI, which has no
`unified-api-contracts` at all. Measured, not inferred: UAC `0.109.0` was published to Artifact Registry at
**11:22:01Z** and builds at 11:38 / 11:47 / 11:52 / 12:07 still failed with "not found in the package registry" while
requiring `>=0.109.0`. **Publishing the wheel can never unblock this** — the tempting wrong remediation.

**2 — Why it stayed hidden.** The registry path was never EXERCISED while the UAC baked into the base image satisfied
UTL's floor: uv resolved the constraint from the already-installed package and never looked outward. UTL re-pinning its
floor past the baked version (`0.109.0` @10:22:18Z `bc046fab`, `0.110.0` @12:52:08Z `f23097ac`) exercised it for the
first time. Onset matches exactly — last SUCCESS 09:22Z, first FAILURE 10:22:12Z, then 20 consecutive failures across
BOTH `live-defi-rollout` and `main`. **The detonator is a floor bump in a DIFFERENT repo, so this repo gets no local
signal before it fires.**

**3 — Version mis-stamp, which defeats the obvious fix.** The base image bakes `ENV SETUPTOOLS_SCM_PRETEND_VERSION`
(`unified-trading-library/Dockerfile`), so it is live in every `RUN` and both hatch-vcs clones get stamped with the BASE
IMAGE's UTL version. In the last green build UAC installed as **`0.76.3`** while its staged tag was `v0.108.0`. MTDS's
"placed BEFORE the ENV below on purpose" note guards against THIS repo's own ARG but cannot guard against one inherited
from the base image. Consequence: merely putting both editables in one resolution is NOT enough — the UAC in it is still
stamped `0.76.3`, still fails `>=0.110.0`, and still goes to the registry.

**The fix**: one `uv pip install` with BOTH editables, `--no-sources` DROPPED, and
`env -u SETUPTOOLS_SCM_PRETEND_VERSION` scoped to that command only. `--no-sources` is dropped rather than moved because
UAC pins **`prek` — a RUNTIME dependency — to a patched fork by URL** (upstream silently drops uncommitted work on a
stash-restore conflict); `--no-sources` would have quietly resolved prek from stock PyPI and reintroduced that bug.

## Verification (done BEFORE shipping, not after)

Reproduced locally against fresh clones of both repos at LDR tip (`uv pip install --dry-run` into a throwaway venv, with
`SETUPTOOLS_SCM_PRETEND_VERSION=0.76.3` exported to simulate the base image's inherited ENV):

- **Old form** — `--no-sources -e .deps/unified-trading-library` alone → reproduces the production error
  **byte-for-byte, including `unified-trading-library==0.76.3`**, confirming that version in the prod log is the leaked
  pretend-version and not a real UTL version.
- **`env -u` added, nothing else changed** → version becomes the true `0.77.1.dev634+g336f2b3b6` but resolution **still
  fails**. This isolates the two defects and proves BOTH fixes are required; neither alone suffices.
- **New form** — one resolution, both editables, no `--no-sources`, `env -u` → **resolved 191 packages, exit 0**, UAC
  from the local `file://` path, and `prek` from the patched-fork URL (confirming the pin survives).

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

- [x] [BACKEND] P2. ✅ **Read step 6's log and fix the build.** Root-caused to the three compounding defects documented
      above and fixed in `market-tick-data-service/Dockerfile` — market-tick-data-service@0eb8aa2c8e (quickmerge,
      post-push ancestry verified against `origin/live-defi-rollout`). The stale-UTL-base-image hypothesis in this
      todo's original text was WRONG — step 5 `pull-base-image` completed fine. Verified by local reproduction before
      shipping (§ "Verification"). The done-when (a fresh LDR build reaching SUCCESS) is carried by the next todo.
- [x] [BACKEND] P2. ✅ **Confirm the fix build is green.** `Evidence: cloudbuild=6fee191d-5133-407b-a384-d81e702f3803` —
      SUCCESS, 15:11:50Z → 15:20:09Z (8m19s), market-tick-data-service@0eb8aa2, `live-defi-rollout`. Step 6 cleared and
      the log proves all three defects fixed at once: `+ unified-api-contracts==0.110.1.dev910+gc48238266` and
      `+ unified-trading-library==0.77.1.dev636+g640466d22` (both TRUE git-derived versions, replacing the mis-stamped
      `0.76.3`), both installed from local `file://` paths with no registry lookup, and the UAC version now satisfies
      UTL's `>=0.110.0` floor locally. First green MTDS image build since 09:22Z, ending 20 consecutive failures. NOTE:
      MTDS builds on `main` stay red until LDR→main promotion carries this sha across — expected, self-resolving, not a
      separate defect.
- [ ] [BACKEND] P3. **Sibling repos mis-stamp their own package version from the same inherited ENV.** The UTL base
      image bakes `ENV SETUPTOOLS_SCM_PRETEND_VERSION`, and every repo that `FROM`s it inherits that value live in each
      `RUN`. Measured 2026-08-10: `strategy-service` and `greeks-service` declare
      `ARG SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0.dev0` but their `cloudbuild.yaml` never passes `--build-arg`, so their
      images are stamped `0.0.0.dev0` while the image around them is TAGGED with the real `$VERSION` — provenance
      disagrees with itself. Both already compute `$VERSION` in `extract-version` and use it for the image tag; the
      one-line fix is to pass it as `--build-arg SETUPTOOLS_SCM_PRETEND_VERSION=$$VERSION`. Version METADATA only — NOT
      build-breaking as in MTDS's case, because those repos don't resolve a floor against a sibling. **CORRECTION
      (2026-08-10): `execution-service` is NOT affected** and was wrongly named in the first version of this todo. It
      uses `uv sync --frozen --no-dev --no-install-project`, so its own package is never installed into the image and
      therefore never stamped. The original claim came from grepping its Dockerfile for `SETUPTOOLS_SCM`, finding
      nothing, and inferring inheritance — without reading how it actually installs. Repos: strategy-service,
      greeks-service. **BLOCKED — neither could be landed 2026-08-10, both for reasons unrelated to the change itself:**
      `strategy-service`'s own quality gate is RED at its committed LDR tip, so quickmerge refuses ANY commit into the
      repo (tracked in
      /plans/active/issues/strategy_service_ldr_tip_fails_own_quality_gate_blocks_all_commits_2026_08_10.md).
      `greeks-service` has a peer's uncommitted pre-migration `.github/workflows/semver-agent.yml` in its working tree;
      HEAD is post-migration (it now calls the shared reusable workflow), so quickmerge's autostash/pop conflicts on
      that file EVERY run, leaving `UU` conflict markers that then fail the workflow-YAML gate. Observed and reverted to
      status quo ante 2026-08-10 — do NOT retry there until that stale WIP is cleared, or you will re-corrupt a peer's
      working tree for a cosmetic version stamp.
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

## Lessons (would otherwise be re-learned the hard way)

- **A failing docker step does not implicate the base image.** The first hypothesis here — and the one the alert invites
  — was "stale UTL base image". It was wrong, and chasing it would have burned a base-image rebuild cycle. Read the
  failing step's own log before believing the plausible story.
- **"Publish the missing wheel" is the seductive wrong fix.** It fails slowly: you publish, rebuild, and it still
  breaks, because the consumer never reads that index. The discriminating evidence was cheap — compare the Artifact
  Registry publish timestamp against builds that failed AFTER it.
- **uv ignores `pip.conf`.** Any `extra-index-url` configured for pip does nothing for a `uv pip install`. Anywhere in
  this fleet that relies on pip.conf to reach Artifact Registry while invoking uv is latently broken the same way.
- **An inherited `ENV` from a base image beats instruction ORDER in the child Dockerfile.** A comment reasoning about
  "placed before the ENV below" is only sound if no ancestor sets the same variable — check the base Dockerfile before
  trusting that class of ordering argument.
- **`--no-sources` is not a safe blanket flag.** It disables path pins AND security-motivated URL pins in one stroke;
  here it would have silently swapped a patched `prek` fork for the vulnerable upstream. Prefer making the local
  resolution correct over disabling source resolution.

## Progress Log

- **2026-08-10 15:20Z (/ci-reconcile, slot-2·laptop)** — **VERIFIED GREEN.**
  `Evidence: cloudbuild=6fee191d-5133-407b-a384-d81e702f3803` SUCCESS (8m19s) on market-tick-data-service@0eb8aa2 —
  first green MTDS image build since 09:22Z, ending 20 consecutive failures. The step-6 log confirms the predicted
  outcome exactly: both workspace deps installed from local `file://` paths at their TRUE git-derived versions
  (`unified-api-contracts==0.110.1.dev910`, `unified-trading-library==0.77.1.dev636`) instead of the mis-stamped
  `0.76.3`. The build-break todos are closed; this issue stays OPEN only for its three P3s (the `-prod` trigger
  confirmation, the stale `hosted-baseline` snapshot, and the sibling-repo version mis-stamp).
- **2026-08-10 ~15:15Z (/ci-reconcile, slot-2·laptop)** — Root-caused and FIXED; shipped
  market-tick-data-service@0eb8aa2c8e. Build `6fee191d-5133-407b-a384-d81e702f3803` fired on that sha and was WORKING at
  15:11Z — this issue stays OPEN until it reaches SUCCESS. Two corrections to earlier text in this doc: the
  stale-base-image hypothesis was wrong, and the `0.76.3` in the build log is a leaked pretend-version, not a real
  `unified-trading-library` version. Also filed a P3 for three sibling repos mis-stamping their version from the same
  inherited ENV (metadata-only). Note for whoever edits this doc next: this update was rebased onto origin's copy after
  finding the local checkout 130 commits behind — a peer had already narrowed `asset_group` to `[cross-cutting]`, which
  is preserved here rather than reverted.
- **2026-08-10 (/ci-reconcile, slot-2·laptop)** — Filed while checkpointing at ~67% context. The build failure itself is
  UNDIAGNOSED by design of the handoff: the operator asked for it to be taken next, and it needs the step-6 log read
  with fresh context rather than a guess appended here. Everything else from that alert window is already fixed and
  pushed (`cloud-build-router` empty-error-detail + credential scrub; the PM quality-gates false CRITICAL, which was an
  hourly LDR `workflow_dispatch` measuring the whole unpromoted backlog and NOT the innocent codex-docs commit the alert
  named).
