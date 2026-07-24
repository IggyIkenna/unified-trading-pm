---
doc_type: issue
title:
  "github-actions-deploy SA granted project-wide secretmanager.secretAccessor — should be scoped to 2 secrets, deferred
  pending secretmanager.admin access"
summary:
  While root-causing a gcloud PERMISSION_DENIED for github-actions-deploy@central-element-323112.iam.gserviceaccount.com
  reading SLACK_ALERTS_READER_BOT_TOKEN, granted that SA roles/secretmanager.secretAccessor at the PROJECT level
  (2026-07-24, via harshkantariya@odum-research.com's projectIamAdmin role) to unblock the immediate need. On reflection
  this contradicts the codebase's own established pattern — every other real Secret Manager need was resolved via a
  narrow, purpose-built SA (github-deploy scoped to just GH_PAT; ibkr-gateway-sa scoped to IBKR creds) rather than
  broadening an already-powerful CI/CD SA (which also holds storage.admin, run.admin, compute.instanceAdmin.v1) to read
  every secret in the project. Operator agreed the grant should be scoped down to the 2 secrets with real evidenced
  need, but the scoped (per-secret) grant needs roles/secretmanager.admin, which the currently-available login lacks —
  deferred rather than granting yet another broad role to fix an over-broad-role problem.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer]
tags: [gcp, iam, secret-manager, least-privilege, service-account]
related: []
created: 2026-07-24
last_updated: 2026-07-24
priority: P2
parent_epic: orchestrator_master
source:
  "Operator review of a same-day IAM grant — flagged that granting broad access to every account defeats the purpose of
  having separate, scoped service accounts. Operator ruling 2026-07-24: leave the project-wide grant for now, fix later."
assigned_vm: NA
execution_scope: local-only
estimate_class: infra
drift_direction: advance-code
resolved_by:
locked_by:
depends_on: []
---

## What was done (2026-07-24)

```
gcloud projects add-iam-policy-binding central-element-323112 \
  --member="serviceAccount:github-actions-deploy@central-element-323112.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

Run as `harshkantariya@odum-research.com` (has `roles/resourcemanager.projectIamAdmin`, which covers project-level IAM
binding changes). Verified working: the SA can now read `SLACK_ALERTS_READER_BOT_TOKEN`.

## Why this should be narrowed

- `github-actions-deploy` already holds broad roles (`storage.admin`, `run.admin`, `compute.instanceAdmin.v1`,
  `cloudbuild.builds.editor`, `artifactregistry.reader/writer`, `datastore.user`,
  `iam.serviceAccountTokenCreator/User`). Adding blanket secret-read on top means a compromised/misused credential (or a
  malicious CI workflow change) now exposes **every secret in the project**, not just the ones it actually needs.
- The codebase's own established convention is per-secret, purpose-built SAs: `github-deploy@central-element-323112`
  holds `secretmanager.secretAccessor` scoped ONLY to `GH_PAT`; a prior IBKR-credentials need was routed to a dedicated
  `ibkr-gateway-sa` rather than broadening an existing SA. This grant breaks that pattern.
- The only two evidenced real needs are:
  1. `SLACK_ALERTS_READER_BOT_TOKEN` (our local Slack-triage use, since this SA's key also gets used as a fallback
     interactive gcloud identity on dev/slot machines — itself a separately-flagged fragile pattern, not re-litigated
     here).
  2. `DATA_PIPELINE_ALERTS_SLACK_WEBHOOK` (a shipped CI job in
     `unified-trading-pm/.github/workflows/cloud-build-router.yml` — `notify-instruments-build-data-pipeline` — that
     already tries to read this secret under this SA's identity today, currently silently degraded via a
     `2>/dev/null || echo ""` fail-open).

## Why it wasn't fixed immediately

The scoped (per-secret) version needs `roles/secretmanager.admin` (or Owner) to set IAM policy on an individual secret
resource — a DIFFERENT permission from the project-level `resourcemanager.projectIamAdmin` that made the broad grant
possible. Per the live IAM policy dump (2026-07-24), only `ikenna@odum-research.com` currently holds
`roles/secretmanager.admin` on `central-element-323112`. Granting `harshkantariya@odum-research.com` that role too, just
to fix an over-broad-role problem, would repeat the same pattern this issue is about — so it was deferred instead of
compounding it. Operator ruling: leave the project-wide grant in place for now, fix later.

## Open todos

- [ ] [OPERATOR] P2. Log in as (or have) `ikenna@odum-research.com` run the two secret-scoped bindings:
      `     gcloud secrets add-iam-policy-binding SLACK_ALERTS_READER_BOT_TOKEN \       --member="serviceAccount:github-actions-deploy@central-element-323112.iam.gserviceaccount.com" \       --role="roles/secretmanager.secretAccessor"     gcloud secrets add-iam-policy-binding DATA_PIPELINE_ALERTS_SLACK_WEBHOOK \       --member="serviceAccount:github-actions-deploy@central-element-323112.iam.gserviceaccount.com" \       --role="roles/secretmanager.secretAccessor"     `
- [ ] [OPERATOR] P2. Once the scoped bindings above are confirmed working (re-test both secret reads under this SA),
      remove the project-wide grant:
      `     gcloud projects remove-iam-policy-binding central-element-323112 \       --member="serviceAccount:github-actions-deploy@central-element-323112.iam.gserviceaccount.com" \       --role="roles/secretmanager.secretAccessor"     `
      **Gate**: re-run
      `gcloud secrets versions access latest --secret=SLACK_ALERTS_READER_BOT_TOKEN --account=github-actions-deploy@...`
      AFTER the removal to confirm the scoped binding alone still allows it (not just leftover propagation of the
      project-wide one).
- [ ] [BACKEND] P3. Separately noted (not this issue's scope): `deployment-service/configs/gcp_service_accounts.yaml` —
      the per-service SA/IAM registry — has no entry at all for `unified-trading-sa@central-element-323112`
      (deployment-api's actual runtime SA) and its own footer admits `last_executed: NEVER`. Worth a follow-up pass to
      sync this registry against live IAM reality rather than leaving it aspirational.

## Progress Log

- **2026-07-24**: Filed after operator review of the same-day broad grant. Confirmed via live
  `gcloud projects get-iam-policy` that only `ikenna@odum-research.com` holds `secretmanager.admin` on this project.
  Deferred per operator ruling — project-wide grant stays in place until the scoped fix is convenient.
