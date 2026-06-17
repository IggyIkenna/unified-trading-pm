---
title: "Deployed dashboard Image column blank + GCP/AWS toggle is a no-op in prod — IAM gap now, multi-cloud build-status architecture to decide"
created: 2026-06-17
status: active
priority: P2
locked_by: live-defi-rollout
source:
  - 2026-06-17 operator report — deployed deployment-ui Repos-CI "Image" column shows "unknown" for all 25 repos while localhost populates it
  - 2026-06-17 diagnosis (harsh-slot-3) — Cloud Run SA IAM gap + CloudProviderContext base-URL analysis + UTL secret-provider decoupling
parent_epic: deployment_and_user_management_master
---

# Deployed dashboard Image column blank + multi-cloud build-status architecture

> **For Ikenna** — the immediate blank-column fix is a one-line IAM grant I cannot run (needs Owner/IAM-admin; my
> `harshkantariya` account + the deploy SA both lack `setIamPolicy`). The bigger decision is whether/how the GCP/AWS
> toggle should actually show per-cloud build status in the deployed dashboard. Both written up below.

## What I found

The operator-facing dashboard at `https://uts-shared-deployment-api-cldtjniqvq-an.a.run.app/repos` shows the **Image**
column (last build SHA + SUCCESS/FAILURE/stale badge) as **"unknown" for all 25 repos**, while the identical UI on
`localhost:5183` populates it fully. The deployed frontend IS the latest code (verified: served image tag `8c5052c` ==
deployment-api `main` HEAD; this was a *separate* promotion fix, now done — both repos' `main` == LDR).

Three distinct findings, in order of how deep they go:

1. **Immediate root cause — IAM gap (fixable in one line).** The Image column is live data from `_latest_builds_by_repo()`
   (`deployment-api/deployment_api/routes/repo_ci.py:360`), which calls **GCP Cloud Build v1 `list_builds`** in
   `asia-northeast1`. It is best-effort by design: "any cloud failure (missing perms, inactive provider) yields {} → the
   image signal reads honest-unknown" (`repo_ci.py:366-368`). The deployed Cloud Run service runs as
   **`unified-trading-sa@central-element-323112`**, whose only roles are `bigquery.dataEditor`, `pubsub.editor`,
   `compute.instanceAdmin.v1`, `iam.serviceAccountUser`, `run.invoker`, `secretmanager.secretAccessor`,
   `storage.objectAdmin` — **no Cloud Build read**. So the `list_builds` call 403s, is swallowed, and every cell renders
   "unknown". Local works only because the operator's ADC (`harshkantariya`) happens to have build-viewer rights. The
   deployed `/api/repo-ci/overview` confirms `last_build_status: None` for all 25 repos.

   **Fix (needs Owner/IAM-admin — Ikenna):**
   ```bash
   gcloud projects add-iam-policy-binding central-element-323112 \
     --member="serviceAccount:unified-trading-sa@central-element-323112.iam.gserviceaccount.com" \
     --role="roles/cloudbuild.builds.viewer" --condition=None
   gcloud projects add-iam-policy-binding central-element-323112 \
     --member="serviceAccount:unified-trading-sa@central-element-323112.iam.gserviceaccount.com" \
     --role="roles/artifactregistry.reader" --condition=None
   ```
   Both are **read-only**, project-scoped, reversible (`remove-iam-policy-binding`). Column populates within ~5 min
   (IAM propagation + the in-process 300s `_builds_cache` TTL). `artifactregistry.reader` covers the adjacent
   build-dropdown / `deployed_version` resolution that reads Artifact Registry. This is exactly the permission the local
   ADC already has and the prod SA lacks.

2. **The GCP/AWS toggle is a no-op in the deployed bundle.** The header has a GCP/AWS toggle
   (`deployment-ui/src/components/Header.tsx:239-254`) that, by design, switches the **API base URL** to a per-cloud
   backend (`CloudProviderContext.tsx` → `client.ts:setApiBaseUrl`). But `getApiBaseUrl()`
   (`CloudProviderContext.tsx:34-57`) returns the **relative `/api`** for *any* non-localhost host — so in the deployed
   single-image Cloud Run, **both GCP and AWS buttons hit the same single backend** (`CLOUD_PROVIDER=gcp`). The toggle
   only genuinely switches clouds in the local "two backends on 8004/8005" mode. Net: clicking AWS in the deployed
   dashboard shows the *same GCP backend* — it does not reach any AWS build data.

3. **The backend endpoints take no provider param.** `/api/repo-ci/overview` is `async def get_overview()` with no args,
   and `_latest_builds_by_repo()` dispatches on the **server-side** `is_aws_provider()` / `CLOUD_PROVIDER` env
   (`repo_ci.py:375`), never a per-request param. So even if the toggle *did* reach this backend, there's no wire for it
   to ask for the other cloud's status.

**On "are we building on AWS or GCP?"** — both (multi-cloud). GCP Cloud Build actively builds the fleet (11 distinct
repo triggers ran recently in asia-northeast1); AWS CodeBuild also builds (the `AWS CodeBuild ap-northeast-1
(deployment-api)` status check is live). But the dashboard you're looking at is the **GCP** deployment reading the GCP
side — so the AWS angle does not change finding #1's fix.

## Why it matters

- **Deploy observability is blind on the deployed dashboard.** Operators can't see which repos have a failed/stale image
  build from the hosted dashboard — only from a laptop running the stack locally. That defeats the point of hosting it.
- **The multi-cloud toggle silently lies in prod.** A button that looks like it switches cloud views but actually
  re-queries the same GCP backend is worse than no button — it implies AWS status is being shown when it isn't.
- This is operator-tooling, not a trading-path correctness issue → **P2**, not P0/P1. No data/funds impact.

## Recommended decision

**Step 1 (do now, regardless of the rest): grant the two read roles above.** It unblocks the only view the deployed
bundle actually serves today (GCP), is required for *both* strategic options below, and is safe + reversible.

**Step 2 (the architecture call — Ikenna to choose): how should the toggle show per-cloud build status in prod?**

- **Option A — two backends, toggle switches URL (matches the existing local model).** Deploy a separate AWS-hosted
  `deployment-api` (`CLOUD_PROVIDER=aws`, AWS CodeBuild read on its task role) and wire its **absolute URL** into the
  deployed bundle so the AWS toggle targets it (`getApiBaseUrl` returns that URL for `aws` instead of relative `/api`).
  Cleanest separation; needs a real second deployment + its own IAM.
- **Option B — one backend, provider param.** Add `?provider=gcp|aws` to `/api/repo-ci/overview` (+ peers), have
  `_latest_builds_by_repo(provider)` honor it, and give the single Cloud Run service read access to **both** clouds.
  Less infra (one deploy), but the public-facing GCP service then needs AWS read access.

**On Option B's "AWS creds on a GCP service" worry — don't share static keys; use federation.**

- Static AWS access key in GSM → boto3 is an **anti-pattern**: long-lived bearer secret, manual rotation, and it welds
  the AWS security boundary onto your most-exposed (internet-facing) service. Avoid.
- **Workload Identity Federation, GCP→AWS (keyless)** is the right shape: AWS IAM trusts the GCP SA's OIDC token →
  `AssumeRoleWithWebIdentity` → short-lived (≤1h), read-only STS creds scoped to `codebuild:BatchGetBuilds` /
  `ListBuildsForProject`. No AWS key stored anywhere; blast radius is a 1-hour read-only token. boto3 supports it
  natively. This removes the discomfort that makes naive Option B unappealing.

**On "almost all secrets are in GSM — can AWS services read GSM too?" — yes, the abstraction already supports it.** The
secrets provider is decoupled from the compute cloud: `_detect_secrets_provider()`
(`unified-trading-library/.../cloud_interface/factory.py:103-110`) checks a dedicated **`SECRETS_CLOUD_PROVIDER`** env
var *first*, only falling back to the compute provider. So an AWS-hosted service can set `SECRETS_CLOUD_PROVIDER=gcp` and
`get_secret_client()` returns the GCP client regardless of host cloud. **The one catch — the bootstrap credential:** to
read GSM from AWS the GCP client needs a GCP credential, so you cannot put *literally every* secret in GSM. Resolve the
single GCP-bootstrap cred via **AWS→GCP WIF** (GCP has first-class AWS identity-pool support) so the AWS task role *is*
the credential — keyless, no GCP SA JSON key stored in AWS Secrets Manager.

**The real trade-off for Ikenna to weigh (secrets SSOT):**

- **Single SSOT in GSM, read cross-cloud via WIF** — one place to manage/rotate; but every AWS workload then hard-depends
  on GSM reachability + the federation trust (a GCP/GSM outage degrades AWS-side secret resolution).
- **Per-cloud native stores (GSM + AWS Secrets Manager, replicated)** — each workload self-sufficient + outage-resilient;
  cost is sync tooling to keep the two stores consistent.

Given the system is GCP-primary (GSM holds almost everything; the live deployment is Cloud Run), **single-SSOT-in-GSM +
AWS→GCP WIF** is defensible *if* we accept the AWS-depends-on-GCP coupling. Most multi-cloud setups otherwise lean to
per-cloud native stores for availability.

**My recommendation:** Step 1 now (IAM grant). For Step 2, **Option B with GCP→AWS WIF** — it keeps one deployment, adds
a small provider-param surface, and uses a keyless short-lived read-only AWS identity (no static cross-cloud secret), so
it sidesteps both the blast-radius and the secrets-bootstrap problems. But this is genuinely Ikenna's call — Option A is
the cleaner isolation if we expect the AWS deployment to grow beyond build-status.

## Follow-up todos

- [ ] [INFRA] P2. Grant `roles/cloudbuild.builds.viewer` + `roles/artifactregistry.reader` to
  `unified-trading-sa@central-element-323112` (Owner/IAM-admin — Ikenna). Verify the deployed `/api/repo-ci/overview`
  returns non-null `last_build_status` and the dashboard Image column populates. **Target repo:** infra/GCP IAM (no code).
- [ ] [DESIGN] P2. Decide Option A vs Option B for per-cloud build status in the deployed dashboard (this doc). Owner: Ikenna.
- [ ] [BUG] P3. Deployed GCP/AWS toggle is a no-op (`CloudProviderContext.getApiBaseUrl` returns relative `/api` for all
  non-localhost hosts) — either wire the chosen option's provider routing or hide/disable the toggle in the bundled
  build so it doesn't imply AWS status is shown. **Target repo:** deployment-ui (needs `pw:L2 ✓` + regression spec per UI gate).
