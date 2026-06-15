---
title: "GCP Cloud Build image builds fail for sibling-COPY service repos — build context doesn't stage sibling repos (AWS CodeBuild does)"
created: 2026-06-15
source:
  - "deploy-UI Image column showing red/stale images; fleet promotion unstall 2026-06-15"
locked_by: live-defi-rollout
priority: P2
status: active
---

## RESOLVED 2026-06-15 — Option (B) implemented + validated

Operator chose **(B): make GCP also build these**. Done for all sibling-COPY GCP repos:

- **`stage-siblings` step** added to each `cloudbuild.yaml` (clones the sibling repos
  `@live-defi-rollout` via the `GH_PAT` secret as an http extraheader — mirrors the AWS
  `buildspec.aws.yaml` pre_build), wired into the `build` step's `waitFor`. Repos:
  execution-service (`f55bda1a`), alerting-service (`cad896c`), greeks-service (`b151e49e`),
  strategy-service (`61f8bd40`). deployment-api already had the equivalent `vendor-deps` step.
- **`_RUN_INIMAGE_QG` skip-guard** added (mirrors deployment-api): the in-image
  `quality-gates.sh` is redundant (QG enforced at `quickmerge` Pass-1 + `quality-gates-v2`
  at the promotion PR) AND impossible (no `unified-trading-pm` harness in the image →
  `log_section: command not found` exit 127), so it's skipped (`_RUN_INIMAGE_QG: "false"`).
  Repos: execution-service (`6ac30574`), alerting-service (`ef0a3a6`), greeks-service
  (`6d73fb0`), strategy-service (`e3398957`).
- **Validated end-to-end**: GCP build `ec826e1b` (execution-service, both fixes, on LDR) =
  **SUCCESS** — `stage-siblings` ✅ → `build`(COPY) ✅ → `quality-gates`(skipped) ✅ → `push` ✅.

All edits are on `live-defi-rollout`, draining to main via the (now-working) promotion
pipeline, so the `<svc>-build` (push:^main^) triggers produce fresh GCP images going forward.
This issue is closed — archive on next sweep.

## What I found

After the fleet promotion pipeline was unstalled (main caught up to LDR 2026-06-15), the
post-main-advance image builds revealed a build-PROVIDER asymmetry:

- **AWS CodeBuild = GREEN** for the service repos with AWS projects (deployment-api, execution-service,
  strategy-service, instruments-service, deployment-service, alerting-service, features-service,
  market-tick-data-service, …). Its `buildspec.aws.yaml` `pre_build` clones/rsyncs the sibling repos
  (unified-api-contracts, unified-trading-library, deployment-service, strategy-service) into the
  build context, so the Dockerfiles' `COPY <sibling>/` / `COPY _<sibling>/` steps succeed.
  (Verified SUCCEEDED in the last hour: deployment-api 10:50, execution 09:41, strategy 09:41,
  instruments 09:25.)

- **GCP Cloud Build = RED** for those same repos. The GCP `<svc>-build` triggers run a context that
  does NOT stage the sibling repos, so the build dies at e.g.
  `COPY failed: ... stat unified-api-contracts/: file does not exist` (execution-service) /
  `COPY _unified-api-contracts/` (deployment-api). GCP builds GREEN only for leaf repos that COPY no
  siblings (unified-api-contracts, unified-trading-library, market-tick-data-service).

Two distinct image-build buckets:
1. **AWS path** = the canonical, working image build for service repos (siblings staged).
2. **GCP path** = redundant/secondary for the same repos and currently failing (no sibling staging).
   `deployment-api/cloudbuild.yaml` was edited 2026-06-15 10:47 and has no sibling-staging step.

Separately fixed in the same session (NOT this issue): the `uv sync --frozen --no-dev --system` bug
(uv ≥0.11 removed `--system` from `uv sync`) for the **GCP-only** repos market-data-processing-service,
ml-service, fund-administration-service, trading-agent-service — Dockerfiles corrected to
`uv sync --frozen --no-dev` + `.venv` on PATH (landed on LDR; rebuild on GCP once drained to main).

## Why it matters

The deploy-UI Image column reads build history from BOTH providers (`_cloud_builds_history.py` /
`BuildSignal`), so the GCP reds surface as red/"stale" image cells even though the AWS image is fresh
and green — the visible symptom that prompted "are the images completing". It also generates spurious
build-failure noise/alerts.

## Recommended decision

Operator decision needed on the canonical image-build provider for service repos:
- **(A) AWS is canonical, GCP `<svc>-build` triggers are vestigial** → disable/remove the GCP
  Cloud Build triggers for sibling-COPY service repos (keep GCP for leaf libs), and make the deploy-UI
  image column prefer/only-read the canonical provider so it stops showing redundant-path reds.
- **(B) GCP must also build these** → add the sibling-staging step to each repo's GCP
  `cloudbuild.yaml` (mirror `buildspec.aws.yaml` pre_build: clone UAC/UTL/siblings@live-defi-rollout
  into the context before `docker build`), so the GCP path stages what the Dockerfile `COPY`s.

Until decided, the real (AWS) service images ARE completing green; the GCP reds are a redundant-path
symptom, not a deploy blocker.
