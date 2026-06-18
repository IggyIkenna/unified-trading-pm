---
title: "Operator IAM permission parity for Harsh — GCP + AWS audit + grants (manage infra without hitting walls)"
created: 2026-06-18
author: harshkantariya [slot-3·laptop]
status: active
priority: P2
locked_by: live-defi-rollout
parent_epic: infrastructure_master
source:
  - 2026-06-17 wall — harshkantariya lacks setIamPolicy (could not grant unified-trading-sa the dashboard cloudbuild-viewer role)
  - 2026-06-18 wall — harshkantariya lacks cloudbuild.builds.editor (could not run a Cloud Build trigger for the fleet image-build phase)
  - 2026-06-18 audit (harsh-slot-3) — full GCP + AWS role audit + GSM stored-credential reuse check
---

# Operator IAM permission parity — Harsh, GCP + AWS

> **For Ikenna — one grant per cloud and we stop hitting infra walls.** The CLAUDE.md model says operators have admin
> ADC and don't pause for infra ops, but `harshkantariya`'s account is under-provisioned vs that intent. Scope requested:
> **everything needed to manage infra in any form — builds, deploys, GCS, VMs, AR, secrets, IAM grants, SA impersonation
> — EXCEPT the genuinely Owner-only destructive/billing powers (project deletion, billing, org policy), which stay with
> you.** Audit + reuse-check below; grant commands at the end.

## GCP audit (`central-element-323112`)

**`harshkantariya@odum-research.com` ALREADY has** (so these are NOT the problem): `run.admin` (deploy Cloud Run),
`storage.admin`/`objectAdmin` (GCS), `compute.instanceAdmin`/`.v1` (VMs), `secretmanager.secretAccessor` (read secrets),
`cloudscheduler.admin`, `artifactregistry.reader`, `bigquery.*`, `pubsub.publisher`, `iam.serviceAccountUser`,
`logging.viewer`, `browser`, `viewer`.

**MISSING — the actual walls + the infra task each blocks:**

| Missing role | Infra task it unblocks | Wall hit |
| --- | --- | --- |
| `roles/cloudbuild.builds.editor` | **Run** Cloud Build triggers / start builds (fleet image-build phase, manual rebuilds) | 2026-06-18 |
| `roles/artifactregistry.writer` | Push / delete / tag-cleanup images (build-push, registry hygiene) | — (reader only) |
| `roles/resourcemanager.projectIamAdmin` | **Grant SAs/users roles** (e.g. the `unified-trading-sa` cloudbuild-viewer fix, WIF role bindings) — WITHOUT Owner | 2026-06-17 |
| `roles/iam.serviceAccountTokenCreator` | **Impersonate SAs** (the keyless "act as the deploy SA" / mint OIDC-ID-token operator pattern) | — (impersonation of `github-actions-deploy` failed) |

**GSM stored-credential REUSE check (per the ask — can we avoid new grants?):** Largely **no**.
- The only GCP SA key in GSM is **`github-actions-sa-key` → `github-actions-deploy`**, which has `artifactregistry.writer`
  + `run.admin` + `storage.admin` but **only `cloudbuild.builds.viewer`** — activating it would add image-push but **NOT
  build-run**. The SAs that DO hold `cloudbuild.builds.editor` (`github-deploy`, `github-cloudbuild-trigger`) have **no key
  in GSM** and aren't impersonable (no `tokenCreator`). So **reuse cannot unblock running builds** — the
  `cloudbuild.builds.editor` (or Editor) grant is unavoidable. (Net: the keyless/SA-attached model means high-priv infra
  creds are deliberately NOT sitting in GSM — good security, but it means we grant the operator account directly.)

## AWS audit (`427895769566`)

**`harsh-worker` is locked down** — it cannot even introspect its own policies (`iam:ListAttachedUserPolicies`,
`ListUserPolicies`, `ListGroupsForUser` all `AccessDenied`) and lacks `codebuild:ListProjects` (Phase-3 wall). So it is
far below the operator infra need.

**GSM reuse check:** `harsh-worker-aws-creds` (= the current locked-down creds, no upgrade) and `ikenna-worker-aws-creds`
(Ikenna's worker — **would only use with your explicit sign-off**, and it's cleaner to fix `harsh-worker` than to
operate as your identity). No stored high-priv "deploy/admin" AWS credential to reuse.

## Recommended grants

**GCP — the clean operator bundle (everything-except-Owner-destructive):**
- **`roles/editor`** — supersets all resource management (Cloud Build *editor*, Artifact Registry *writer*, Cloud Run,
  Compute/VMs, GCS, Pub/Sub, Cloud Scheduler, monitoring, secrets read). Editor **deliberately excludes** billing, org
  policy, project deletion, and project-level `setIamPolicy` — exactly the "Ikenna keeps delete/billing" boundary.
- **`roles/resourcemanager.projectIamAdmin`** — the one thing Editor lacks that we DO need: granting SAs/users roles
  (yesterday's wall) — without going to full Owner.
- **`roles/iam.serviceAccountTokenCreator`** — SA impersonation (keyless "act as the deploy/build SA"); not in Editor.

(Granular alternative if you prefer least-privilege over Editor: add `cloudbuild.builds.editor` + `artifactregistry.writer`
+ `secretmanager.admin` + `pubsub.editor` to Harsh's existing set, plus the two IAM roles above. Editor is simpler and
won't leave a forgotten gap.)

```bash
# Ikenna (Owner) — GCP operator parity for Harsh:
for ROLE in roles/editor roles/resourcemanager.projectIamAdmin roles/iam.serviceAccountTokenCreator; do
  gcloud projects add-iam-policy-binding central-element-323112 \
    --member="user:harshkantariya@odum-research.com" --role="$ROLE" --condition=None
done
```

**AWS — attach `PowerUserAccess` to `harsh-worker`** (the AWS analog of Editor: full access to every service EXCEPT IAM
management):
```bash
aws iam attach-user-policy --user-name harsh-worker \
  --policy-arn arn:aws:iam::aws:policy/PowerUserAccess
```
…and IF we should also own AWS IAM-role creation (the WIF-role-creation kind of task, e.g. the
`gcp-cloudrun-codebuild-reader` role you made), add a scoped IAM-write policy (or `IAMFullAccess`) — flagged separately
since IAM management is the sensitive one and may be the piece you'd rather keep.

All grants are **reversible** (`remove-iam-policy-binding` / `detach-user-policy`).

## Why it matters

- Every infra task in the workspace model (run builds, deploy services, launch backfill VMs, push images, grant SAs the
  roles a new feature needs, rotate creds) currently risks a Harsh-side permission wall — each one round-trips through
  Ikenna, stalling autonomous infra work the CLAUDE.md explicitly says operators should not pause on.
- This is parity-with-the-intended-model, not a privilege escalation: Ikenna + femi already hold `roles/owner`; the
  request is the **operator tier below Owner** (manage everything, but not delete/bill the project).
- Not a live outage → **P2**. Reversible.

## Composes with
- Blocks the GCP build phase of `plans/active/test_fleet_image_builds_from_current_code_2026_06_17.md`.
- Same operator model: CLAUDE.md "Plans Run To Actual Completion … ADC admin perms on GCP + AWS — do NOT pause for
  operator approval on infra ops."
