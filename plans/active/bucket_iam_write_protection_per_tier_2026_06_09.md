---
title: Bucket IAM write-protection — per-tier/per-domain SAs replace the project-wide god-SA (§8 implementation)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
execution_scope: cloud-apply
estimate_class: infra
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
created: 2026-06-09
locked_by: live-defi-rollout
locked_since: 2026-06-09
related_plans:
  - plans/active/cicd_contract_hardening_2026_06_01.md
  - plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md
Codex SSOTs:
  - codex/05-infrastructure/bucket-isolation-model.md
  - codex/16-strategy-playbooks/infra-spec/stage-3e-g2-env-split.md
---

# Bucket IAM write-protection — per-tier/per-domain SAs (§8 implementation)

## What I found

The bucket isolation model is **designed but only half-implemented**.

- **Designed** ([bucket-isolation-model.md §8](../../codex/05-infrastructure/bucket-isolation-model.md)): batch/live SAs
  read+write **scoped to their domain**; CI/CD + developer SAs **read-only on prod, read+write on mock/dev**; env tier
  lives in the bucket name (Group B: `…-{mock|dev|prod}-{project}`).
- **Implemented**: bucket **naming/tier** (`unified-cloud-interface` `get_bucket_name`/`get_bucket_environment`) + the
  runtime guard that makes `CLOUD_MOCK_MODE=true` / `ENVIRONMENT=dev` never resolve to a prod bucket name. This is a
  **code-level** safety net only.
- **NOT implemented (the gap)**: the live service account
  [`unified-trading-sa`](../../../deployment-service/terraform/gcp/main.tf#L1833) holds **`roles/storage.objectAdmin`
  project-wide** — so it can write **every** bucket in the project, including prod-tier. The §8 IAM write-protection is
  not enforced. The only thing stopping a staging/dev process (or a migration script, or a bug) writing a prod bucket is
  the code-level name resolver — credential-level isolation does not exist yet.
- There is **no dedicated migration SA**, so the documented "exceptions for migration scripts" has nothing to except
  from — everything already runs as the one god-SA.

### Bucket-name target (sync with in-flight migrations — do NOT invent)

The IAM model keys off the **actual** bucket env suffix produced by the mandated SSOT
[`resolve_bucket_name`](../../../unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py)
(`_DEPLOYMENT_ENV_SHORT_FORM`), **not** a new scheme:

| Workspace env           | Bucket suffix |
| ----------------------- | ------------- |
| dev / development       | `-dev-`       |
| **staging / stg**       | **`-stg-`**   |
| prod / prd / production | `-prd-`       |
| (E2E) test              | `-test-`      |

- **4 effective name tiers (`dev`/`stg`/`prd` + ephemeral `test`); staging is DISTINCT (`-stg-`), not folded into dev.**
- **`mock` is NOT a name suffix** — it is `CLOUD_MOCK_MODE` + scenario prefixes _inside_ buckets.
- **Two drift facts blocking clean sync:**
  - **Codex stale**: [bucket-isolation-model.md](../../codex/05-infrastructure/bucket-isolation-model.md) §4 claims
    "staging shares the dev tier" (3-tier via `get_bucket_environment`) — **contradicts** `resolve_bucket_name`.
    Resolver is the mandated SSOT → doc must be corrected (P3 below).
  - **Group A vs B differ TODAY**: Group A (raw — `market-data-tick`, `instruments-store`) is **env-tiered live**
    (canonicalisation migrations already run on `…-prd-central-element-323112`); Group B (derived — `features-*`,
    `strategy-store`, `execution-store`, `ml-*`) is **env-split ROLLED BACK** (non-env-split today), and its named
    successor `plans/active/bucket_env_split_rollout_2026_06.md` **does not exist** (dangling reference in
    `deployment-service/configs/cloud-providers.yaml`). Group B IAM cannot key on a tier suffix the buckets don't carry.

## Why it matters

Operator intent (2026-06-09): "read from anything but only WRITE to the bucket with our SA credentials (exceptions for
migration scripts) … lock services from accidentally editing prod whilst working on staging." Today a single credential
can write all tiers, so the lock is advisory (code), not enforced (IAM). Composes with the same isolation goal behind
the cloud-build-router fix (deploy-time isolation) — this plan covers the **runtime data-bucket** half.

## Sequencing gate (HARD)

Two independent gates because Group A and Group B are at different stages:

1. **Group A (raw, already env-tiered)**: do NOT scope IAM until the in-flight canonicalisation walks complete
   (`master_data_canonicalisation_migration_catalogue_2026_06_07.md` + the per-AG
   `*_manifest_canonicalisation_2026_06_01` plans) — they do cross-tier whole-corpus writes on the `-prd-` buckets with
   the current broad-grant SA; scoping mid-migration breaks them. Gate = P0.1.
2. **Group B (derived, env-split rolled back)**: BLOCKED on the bucket env-split rollout landing first — the buckets do
   not carry a tier suffix today, so there is nothing to scope by. Successor
   [`bucket_env_split_rollout_2026_06.md`](bucket_env_split_rollout_2026_06.md) (created 2026-06-09) provisions +
   migrates Group B to the `-{env}-` shape; this plan's Group B IAM follows its Phase 1/2.

## Open design decisions (resolve before terraform)

- [x] ✅ **Tier set — RESOLVED**: `dev` / `stg` / `prd` (+ ephemeral `test`) per `resolve_bucket_name`; **staging is a
      distinct `-stg-` tier** (the codex 3-tier "staging≡dev" framing is stale). `mock` is mode-based, not a name
      suffix. — provenance: UTL `_DEPLOYMENT_ENV_SHORT_FORM` (mandated SSOT) + operator 2026-06-09.
- [x] ✅ [DESIGN] P0. **Per-tier only vs per-domain×tier SAs.** Decision: **(a) one SA per tier**. Per-domain×tier (b)
      deferred — blast-radius benefit doesn't justify the binding-count cost before full tier isolation is in place.
      Final SA set: `uts-dev-sa` (rw `-dev-*`, r `-stg-*`/`-prd-*`), `uts-stg-sa` (rw `-stg-*`, r `-dev-*`/`-prd-*`),
      `uts-prd-sa` (rw `-prd-*`, r `-dev-*`/`-stg-*`), `uts-migration-sa` (cross-tier rw, sanctioned exception).
      — unified-trading-pm@HEAD 2026-06-12

## Phased execution

### Phase 0 — Gates + design

- [x] ✅ P0.0. **`bucket_env_split_rollout_2026_06.md` created** (2026-06-09) — env-split everywhere (Group A confirm +
      Group B un-rollback). Group B IAM (Phase 2) depends on its Phase 1/2 (provision + migrate + legacy delete).
- [ ] [INFRA] P0.1. **Group A migration-completion gate**: confirm the master canonicalisation catalogue + per-AG
      `*_manifest_canonicalisation_2026_06_01` plans are DONE and no whole-corpus walk is scheduled. Blocks Group A IAM.
- [x] ✅ [DESIGN] P0.2. Resolved in P0 above: option (a) per-tier SAs. Final SA list:
      `uts-dev-sa`, `uts-stg-sa`, `uts-prd-sa`, `uts-migration-sa` (cross-tier exception).
      — unified-trading-pm@HEAD 2026-06-12

### Phase 1 — IAM model in terraform (Group A + dev/stg first, no prod write-removal)

- [ ] [TERRAFORM] P1.1. Define per-tier SAs (`uts-dev-sa`, `uts-stg-sa`, `uts-prd-sa`) + a dedicated **migration SA**
      (`uts-migration-sa`, cross-tier write — the sanctioned exception, used only by
      `*_service/scripts/migration_*.py`).
- [ ] [TERRAFORM] P1.2. Replace the project-wide `roles/storage.objectAdmin` with **per-suffix bindings**: dev SA →
      `objectAdmin` on `*-dev-*`; stg SA → `*-stg-*`; prd SA → `*-prd-*`; all SAs + CI/CD + developer identities →
      `objectViewer` broadly (read-anything) but **read-only on `*-prd-*`**. Apply to **Group A buckets first** (they
      carry the suffix today).
- [ ] [TERRAFORM] P1.3. Verify dev/stg workloads read everything, write their own tier, and are **IAM-denied** a `-prd-`
      write (negative test). No prod write-grant removal until P2.

### Phase 2 — Prod cutover + wiring

- [ ] [TERRAFORM] P2.1. Apply `-prd-` write-scope; remove the god-SA `objectAdmin`. Verify live/batch prod workloads
      retain `-prd-` write; verify a dev/stg credential is **denied** a `-prd-` write (IAM-level, not just
      name-resolver). **Group B buckets join here only after `bucket_env_split_rollout_2026_06.md` provisions their
      `-{env}-` form.**
- [ ] [CODE] P2.2. Wire each runtime to its tier SA (deployment-service launchers / Cloud Run service identities);
      migration scripts opt into `uts-migration-sa` explicitly.
- [ ] [TEST] P2.3. Negative tests: `ENVIRONMENT=staging` write to a `*-prod-*` bucket → `403` at IAM; migration SA →
      allowed. Add as a deployment-service QG check.

### Phase 3 — Codex alignment

- [ ] [DOCS] P3.1. Update [bucket-isolation-model.md §8](../../codex/05-infrastructure/bucket-isolation-model.md) from
      "designed" to "enforced", documenting the SA names + the migration-SA exception. Update CLAUDE.md one-liner.

## Success criteria

- IAM (not code) denies a dev/staging credential a prod-bucket write (negative test passes).
- Live/batch prod + dev workloads unaffected (read-anything preserved; tier writes preserved).
- Migration SA is the single sanctioned cross-tier writer; no remaining project-wide `objectAdmin`.
- Codex §8 reflects enforced reality.
