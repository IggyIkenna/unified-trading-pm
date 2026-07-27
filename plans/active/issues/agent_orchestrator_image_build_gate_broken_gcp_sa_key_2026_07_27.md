---
doc_type: issue
title: >-
  agent-orchestrator's image-build-gate has failed on every run for 20+ hours — GCP_SA_KEY secret content is
  empty/corrupted (dated to the 2026-06-07 native-repo-recreation migration), and the WIF fallback secrets were never
  provisioned either
summary: >
  `image-build-gate` (the reusable `image-build-validate.yml` gate, invoked by `agent-orchestrator`'s promote workflow)
  has failed on EVERY run since at least 2026-07-26T04:09:27Z (15+ consecutive failures spanning 20+ hours, confirmed
  via `gh run list --workflow=image-build-gate`) — this means `agent-orchestrator` cannot ship a new Docker image via
  its normal promote pipeline right now. Live log inspection (`gh run view <id> --log`, run 30229000654) shows the
  actual failure is GCP auth, not the build itself:

  1. **WIF (primary) auth fails**: `google-github-actions/auth failed with: the GitHub Action workflow must
     specify exactly one of "workload_identity_provider" or "credentials_json"!` — `secrets.WORKLOAD_IDENTITY_PROVIDER`
     is empty on this repo (`gh secret list --repo IggyIkenna/agent-orchestrator` confirms it is simply absent,
     along with `GCP_SERVICE_ACCOUNT`).
  2. **Legacy SA-key fallback ALSO fails**: `failed to parse service account key JSON credentials: unexpected end
     of JSON input` — `GCP_SA_KEY` IS present (`gh secret list` confirms it exists, `updated 2026-06-07T15:45:49Z`)
     but its VALUE is empty or truncated, not merely missing.

  **The 2026-06-07 date is the smoking gun**: it exactly matches `org_migration_to_odumresearch_2026_06_07.md`'s
  documented action "Recreated `IggyIkenna/agent-orchestrator` native" (the repo was a fork of
  `CosmicTrader/orchastrator` and had to be re-created as a native repo, not transferred). The most likely explanation
  is the `GCP_SA_KEY` secret was re-set during that repo recreation with an empty/truncated value (a copy-paste or
  empty-stdin mistake), and — per `codex/07-security/gha-wif-migration.md`'s own fleet audit table — the WIF pool for at
  least one other repo/workflow in this exact migration was already flagged `BLOCKED-OPERATOR (WIF pool not
  provisioned)`, so agent-orchestrator's WIF secrets were likely never provisioned at all (not lost — never set).

  **Why not fixed in this session**: regenerating/rotating a live GCP service-account-key secret (or provisioning a new
  WIF pool binding) for `agent-orchestrator` — the repo that hosts the very AO dispatch system running the fleet's
  background workers — is a credential-provisioning action with meaningfully high blast radius if done wrong (wrong SA,
  wrong IAM scope, or a key that silently doesn't match what Cloud Build's trigger expects). This session has read-only
  `gcloud`/`gh` access sufficient to diagnose but did not attempt to mint a new key or touch IAM. Per the codex's own
  precedent (an identical WIF-not-provisioned gap on another repo was marked `BLOCKED-OPERATOR`, not self-fixed), the
  same disposition applies here.

  **Scope/impact check**: `Escalate to Orchestrator` and `Slack — Escalation Dispatch` workflows (a DIFFERENT concern
  raised earlier the same session, see `related`) hit the orchestrator's `/api/escalate` HTTP endpoint, which is
  unrelated to this Docker-image-build path — confirmed the orchestrator API itself is reachable (`curl .../health` →
  HTTP 200) and worker dispatch is unaffected; this is scoped to agent-orchestrator's own CI/CD image-publish pipeline
  only, not its runtime.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [agent-orchestrator]
scope: [admin]
tags:
  [
    ci-cd,
    gcp,
    gcp-auth,
    workload-identity-federation,
    service-account-key,
    image-build-gate,
    secrets,
    agent-orchestrator,
    blocked-operator,
  ]
related:
  [
    /codex/07-security/gha-wif-migration.md,
    /plans/active/org_migration_to_odumresearch_2026_06_07.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: 2026-07-27
parent_epic: infrastructure_master
priority: P1
source: >-
  /autonomous fleet CI health sweep, 2026-07-27 — investigating a repeated `Escalate to Orchestrator` failure pattern
  surfaced a broader fleet scan, which found `agent-orchestrator`'s `image-build-gate` red on every run for 20+ hours.
  Root-caused via `gh run view --log` + `gh secret list` (live, direct evidence, not inferred).
assigned_vm: NA
execution_scope: local-only
assigned_role: devops
drift_direction: advance-code
last_updated: 2026-07-27
locked_by:
resolved_by:
depends_on: []
---

# agent-orchestrator image-build-gate broken — GCP_SA_KEY empty + WIF never provisioned

## 1. Evidence

- `gh run list --repo IggyIkenna/agent-orchestrator --workflow=image-build-gate --limit 15` — 15/15 `failure`, earliest
  checked 2026-07-26T04:09:27Z, latest 2026-07-27T01:06:16Z (run 30229000654). Chronic, not a blip.
- `gh run view 30229000654 --repo IggyIkenna/agent-orchestrator --log` — two auth failures in sequence:
  - `##[error]google-github-actions/auth failed with: the GitHub Action workflow must specify exactly one of "workload_identity_provider" or "credentials_json"!`
  - `##[error]google-github-actions/auth failed with: failed to parse service account key JSON credentials: unexpected end of JSON input`
- `gh secret list --repo IggyIkenna/agent-orchestrator` — only `GCP_SA_KEY` present (updated 2026-06-07T15:45:49Z);
  `WORKLOAD_IDENTITY_PROVIDER` and `GCP_SERVICE_ACCOUNT` absent entirely.
- Compare `gh secret list --repo IggyIkenna/instruments-service` (a repo whose `image-build-gate` is currently green) —
  also lacks `WORKLOAD_IDENTITY_PROVIDER`/`GCP_SERVICE_ACCOUNT` but its `GCP_SA_KEY` value clearly parses (its gate
  passes), confirming the difference is specifically agent-orchestrator's `GCP_SA_KEY` VALUE, not the overall
  secret-name scheme.
- `.github/workflows/image-build-validate.yml` (this workspace-shared reusable workflow, in `unified-trading-pm`) tries
  WIF first (`if: secrets.WORKLOAD_IDENTITY_PROVIDER != ''`), falls back to `credentials_json: secrets.GCP_SA_KEY` —
  this IS the intended legacy-fallback safety net per `/codex/07-security/gha-wif-migration.md`; the fallback itself is
  broken here, not just unused.

## 2. Recommended fix (either resolves it; WIF is the fleet target state per the codex)

1. **Fastest**: regenerate a GCP service-account JSON key for whatever SA `agent-orchestrator`'s Cloud Build trigger
   expects (check `cloudbuild.yaml` / the GCP project's existing Cloud Build trigger config for the SA email actually in
   use — not confirmed in this session, needs a live `gcloud builds triggers describe` or console check), then
   `gh secret set GCP_SA_KEY --repo IggyIkenna/agent-orchestrator < new-key.json`, delete the local key file immediately
   after.
2. **Correct long-term fix** (matches the fleet's WIF target state): provision a Workload Identity Federation pool
   binding for `agent-orchestrator` (`principalSet://.../attribute.repository/IggyIkenna/agent-orchestrator`, matching
   the pattern already live for other repos per `gha-wif-migration.md`), then set `WORKLOAD_IDENTITY_PROVIDER` +
   `GCP_SERVICE_ACCOUNT` secrets — this removes the legacy-key rotation burden permanently.

Both require either GCP IAM admin access or GitHub repo-secret write access this session did not exercise, given the
credential-provisioning risk to a repo that hosts the live AO dispatch fleet.

## 3. Progress Log

- **2026-07-27** — Root-caused during a standing `/autonomous` fleet CI health sweep. Confirmed orchestrator API itself
  (`/api/escalate`, `/health`) is unaffected and reachable — this is scoped to the image-publish pipeline only. Filed
  `BLOCKED-OPERATOR` pending a credential decision (regenerate SA key vs. provision WIF) and the actual SA email/IAM
  binding this repo's Cloud Build trigger expects.
