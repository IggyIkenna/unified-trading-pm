---
doc_type: codex-ssot
title: deployment-service GCP OpenTofu state + invocation runbook
summary: >-
  How to safely run `deployment-service/terraform/gcp` — the two footguns baked into the dir (backend prefix defaults to
  the near-empty DEV state, and the dir is OpenTofu so the `terraform` binary silently rewrites the provider lock) and
  the `tofu.sh` wrapper that makes the correct invocation the only easy path (requires ENV, maps it to the right backend
  prefix, refuses the wrong binary).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [infrastructure, runbook, terraform, opentofu, gcp, state, footgun]
related:
  [
    /codex/05-infrastructure/path-registry.md,
    /codex/05-infrastructure/new-repo-setup.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
  ]
created: 2026-07-15
authoritative_for: [deployment-service terraform/gcp OpenTofu invocation + backend state prefix]
referenced_by:
owner: workspace-platform
last_reviewed: 2026-07-15
code_refs:
  [
    deployment-service/terraform/gcp/tofu.sh,
    deployment-service/terraform/gcp/main.tf,
    deployment-service/scripts/bootstrap/bootstrap_gcp.sh,
  ]
type: infrastructure
cadence: re-review whenever the backend block, state layout, or provider registry for terraform/gcp changes
verifier: "ENV=prod deployment-service/terraform/gcp/tofu.sh plan  # 0 changes against live prod == healthy"
last_executed: 2026-07-15
---

# deployment-service GCP OpenTofu state + invocation runbook

**Scope:** the single Terraform/OpenTofu root at `deployment-service/terraform/gcp` — the one that provisions the shared
GCP estate (GCS buckets, BigQuery datasets, Pub/Sub, Secret Manager, the `unified-trading` service account, and ~all
Cloud Scheduler crons). It carries two invocation footguns. **Always drive it through the `tofu.sh` wrapper**, never a
bare `tofu`/`terraform` command.

## TL;DR — the safe path

```bash
cd deployment-service/terraform/gcp
ENV=prod ./tofu.sh init      # one-time / after backend or provider change
ENV=prod ./tofu.sh plan
ENV=prod ./tofu.sh apply
```

`tofu.sh` refuses to run without an explicit `ENV` (dev|staging|prod), maps it to the correct backend prefix, injects
the required vars, guards against an env/backend mismatch across invocations, and hard-fails if the `tofu` binary is
absent (it will **not** fall back to `terraform`).

## Footgun 1 — the state-prefix trap (backend defaults to DEV)

`main.tf`'s `backend "gcs"` block hardcodes:

```hcl
backend "gcs" {
  bucket = "uts-terraform-state-central-element-323112"
  prefix = "terraform/state/dev"   # <-- DEV, not prod
}
```

Terraform/OpenTofu backend blocks **cannot interpolate variables**, so the prefix is a literal default. The live PROD
resources (~198: the service account, every Cloud Scheduler/Run job, all buckets) live under `terraform/state/prod`.
`terraform/state/dev` is a near-empty (~11-entry) throwaway state.

**The trap:** a bare `tofu init && tofu apply` with no `-backend-config=prefix=...` silently binds to the DEV state.
Consequences: (a) `plan` shows the entire prod estate as "to be created" (409 ALREADY_EXISTS on apply, or a forked bogus
parallel state), or (b) you conclude prod resources are missing when they are simply in a different state key.

**The fix:** always pass `-backend-config=prefix=terraform/state/<env>` at init. `tofu.sh` does this from `ENV`, and its
cross-invocation guard reads the cached backend prefix in `.terraform/terraform.tfstate` and refuses a `plan`/`apply`
whose `ENV` disagrees with what the dir was last `init`ed for. The official bootstrap wrapper
`scripts/bootstrap/bootstrap_gcp.sh` also passes the per-env prefix (fixed 2026-06-02) — but it runs a full
enable-APIs + apply cycle and uses the `terraform` binary (see Footgun 2), so it is not the tool for a routine
plan/apply.

## Footgun 2 — this dir is OpenTofu, NOT Terraform

The committed `.terraform.lock.hcl` pins its providers from `registry.opentofu.org`:

```
provider "registry.opentofu.org/hashicorp/google" { ... }
provider "registry.opentofu.org/hashicorp/archive" { ... }
```

Running the HashiCorp **`terraform`** binary in this dir rewrites those `provider "registry.opentofu.org/..."` blocks to
`provider "registry.terraform.io/..."` in the tracked lock file — a subtle, committable regression that silently swaps
the provider supply chain for everyone. (This has already bitten the workspace once: a stray `terraform init` left a
lock-registry churn that had to be `git checkout`-restored.)

**The fix:** use the `tofu` (OpenTofu) binary only. `tofu.sh` hard-fails with install guidance if `tofu` is not on PATH
and never substitutes `terraform`. If you ever see `.terraform.lock.hcl` change its registry host in a diff, discard
that hunk — it was a `terraform` invocation, not an intended provider bump.

> **Follow-up (tracked):** `main.tf`'s backend-block default (`prefix = "terraform/state/dev"`) is still a silent
> default for anyone who bypasses the wrapper. Hardening it to fail-loud (or correcting it) was deferred because
> `main.tf` was carrying concurrent foreign WIP at fix time and the wrapper removes the trap for the normal path. See
> the features-sports consolidation plan's Progress Log (2026-07-15, FixStatePrefixTrap phase) for the deferral record.

## Related

- `path-registry.md` — canonical bucket/path SSOT.
- `scripts/bootstrap/bootstrap_gcp.sh` — the one-shot bootstrap (enable APIs + state bucket + apply); passes the per-env
  prefix but uses the `terraform` binary.
