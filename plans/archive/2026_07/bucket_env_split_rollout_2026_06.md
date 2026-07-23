---
doc_type: plan
title: Bucket env-split rollout — re-enable -{dev,stg,prd}- everywhere (Group A confirm + Group B un-rollback)
summary: >-
  Re-enables env-tiered bucket names (-dev-/-stg-/-prd- per UTL resolve_bucket_name _DEPLOYMENT_ENV_SHORT_FORM)
  everywhere: Group A (raw) already tiered — verify only; Group B (derived: features-*, strategy/execution/ml stores)
  un-rolls-back the 2026-05-19 non-env-split shapes. Gated on the in-flight canonicalisation walks finishing
  (single-walk discipline); unblocks the per-tier bucket-IAM write-protection plan's Group B phase.
status: superseded
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, unified-trading-library, unified-trading-pm]
scope: [engineer, admin]
tags: [infrastructure, canonicalisation, migration, single-walk, ssot-audit, data-pipeline]
related:
  [
    plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md,
  ]
created: 2026-06-09
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
last_updated: 2026-06-29
locked_by:
locked_since:
supersedes:
superseded_by: bucket_estate_consolidation_to_sub100_2026_07_13
depends_on:
source:
Codex SSOTs: [/codex/05-infrastructure/bucket-isolation-model.md]
drift_direction: advance-code
---

# Bucket env-split rollout — re-enable `-{dev,stg,prd}-` everywhere

> **📦 ARCHIVED 2026-07-13 — SUPERSEDED by [[bucket_estate_consolidation_to_sub100_2026_07_13]]** (operator
> `[unlock-plan]` given 2026-07-13 in the same session as the ruling below; lock cleared, status → superseded). The
> env-split direction is NOT abandoned — it executes inside the consolidation plan's Wave-3 folds per the ruling below.

> **🟡 OPERATOR RULING 2026-07-13 — env-split STANDS, but execution MERGES with the bucket-estate consolidation folds
> (single migration, "no double migrates").** Context: the 2026-07-13 full estate audit
> ([[terraform_bucket_estate_drift_resurrection_2026_07_13]]) found (a) the 2026-07-10 estate cleanup deleted the 63
> env-tiered Group-B buckets this plan re-provisions (the two plans never referenced each other), and (b) executing
> P1.1–P2.1 as-written adds ~30+ buckets and would be followed by a second migration when the estate consolidation folds
> Group-B kinds (features 25→5 per-AG, unified ml/strategy/execution stores). Ruling: do it ONCE — the **consolidated
> Group-B buckets are env-tiered from birth** (e.g. `features-{ag}-{env}-{pid}`), and data migrates flat →
> consolidated-tiered directly. P1.1/P1.2 as-written (per-kind same-shape tiered twins + same-kind migrate) are
> SUPERSEDED by that combined design; P1.3/P1.4/P2.1/P3.1's intent (yaml re-tiering, consumer verify, flat deletion, IAM
> unblock) carries over into the consolidation plan, which becomes this plan's executor. Do NOT provision per-kind
> tiered twins of the current 25-bucket Group-B layout.

> **This is the named successor** referenced by `deployment-service/configs/cloud-providers.yaml` ("Re-enable when:
> bucket*env_split_rollout_2026_06.md Phase 1 provisions + migrates data") — it was a dangling reference until now.
> **Operator directive 2026-06-09: env-splits everywhere** (Group A \_and* Group B, all kinds). The temporary Group B
> rollback to non-env-split names is to be undone.

## What I found

- **Bucket-name tier SSOT** is UTL
  [`resolve_bucket_name`](../../../unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py)
  (`_DEPLOYMENT_ENV_SHORT_FORM`): `dev`→`-dev-`, **`staging`→`-stg-`** (distinct), `prod`→`-prd-`, plus E2E
  `test`→`-test-`. `mock` is `CLOUD_MOCK_MODE` + scenario prefixes, **not** a name suffix.
- **Group A (raw)** — `market-data-tick`, `instruments-store`, `features-calendar`, `data-catalogue` — already
  **env-tiered live**: the canonicalisation migrations operate on `…-prd-central-element-323112`.
- **Group B (derived)** — `features-delta-one`, `features-volatility`, `features-onchain`, `features-xinstrument`,
  `features-mtf`, `strategy-store`, `execution-store`, `ml-artifacts`, `ml-training-artifacts` — **env-split ROLLED
  BACK** in `cloud-providers.yaml` (non-env-split `…-cefi-{pid}` shapes) because the env-split buckets were
  empty/non-existent at the 2026-05-19 inventory.
- **Codex drift**: [bucket-isolation-model.md](/codex/05-infrastructure/bucket-isolation-model.md) §4 says "staging
  shares the dev tier" (3-tier) — stale vs the resolver's distinct `-stg-`. Fixed in P4.

## Why it matters

Env-tier-in-name is the foundation the per-tier bucket-IAM write-protection
([bucket_iam_write_protection_per_tier_2026_06_09.md](bucket_iam_write_protection_per_tier_2026_06_09.md)) keys on —
that plan's Group B phase is BLOCKED on this one. "Env splits everywhere" is the operator target, so Group B must rejoin
the env-tiered shape.

## Sequencing gate (HARD)

**Do NOT migrate Group B buckets until the in-flight canonicalisation walks finish** (`master_data_canonicalisation_…`

- per-AG `*_manifest_canonicalisation_2026_06_01`). A second whole-corpus walk concurrent with theirs violates the
  single-walk discipline. Group A is already tiered (no action beyond verification); Group B is the migration work here.

## Phased execution

### Phase 0 — Inventory + confirm

- [x] ✅ [INFRA] P0.1. Inventory on-disk Group B buckets per AG: which are flat (`…-{ag}-{pid}`) vs tiered
      (`…-{ag}-{env}-{pid}`), and which hold data. Confirm `resolve_bucket_name` emits the tiered shape for each kind. —
      unified-trading-pm@690376cd5 (slot-5 2026-06-12). GCS census + UTL resolver verified.

      **Findings (GCP prod `central-element-323112`):**

                                                                                                                          All Group B flat buckets exist. `resolve_bucket_name` currently emits flat (rolled-back) names; with
                                                                                                                          `${DEPLOYMENT_ENV_SHORT}` re-added to the YAML it would emit canonical `…-{ag}-prd-{pid}` for prod.

                                                                                                                          **FLAT buckets WITH DATA (need migration in P1.2):**
                                                                                                                          | Bucket | Objects (est.) | Notes |
                                                                                                                          |--------|----------------|-------|
                                                                                                                          | `features-delta-one-cefi-{pid}` | ~1 (index only) | |
                                                                                                                          | `features-delta-one-defi-{pid}` | ~3 (index only) | |
                                                                                                                          | `features-onchain-defi-{pid}` | ~712 | ⚠️ tiered `features-onchain-defi-prd-{pid}` ALSO has ~76 objects — reconcile before migrate |
                                                                                                                          | `features-mtf-cefi-{pid}` | ~1 (index only) | |
                                                                                                                          | `strategy-store-{pid}` | ~23 | backtests/hedge_ratio/strategy_instructions/tracer_runs |
                                                                                                                          | `ml-training-artifacts-{pid}` | ~74 | experiments/ |
                                                                                                                          | `execution-store-cefi-{pid}` | ~6142 | largest; fills/configs/deployment_history/spreads |

                                                                                                                          **FLAT buckets EMPTY (provision-only; no migration data):**
                                                                                                                          `features-delta-one-{tradfi,pred,sports}`, all `features-volatility-*`, `features-onchain-cefi`,
                                                                                                                          all `features-xinstrument-*`, `features-mtf-{defi,tradfi,pred,sports}`,
                                                                                                                          `execution-store-{defi,tradfi,sports}`, `ml-artifacts`.

                                                                                                                          **Stale wrong-form tiered buckets (old long `prod`/`staging` env strings, all EMPTY — delete in P2.1):**
                                                                                                                          `execution-store-{cefi,defi,tradfi}-{prod,staging,dev}-{pid}`,
                                                                                                                          `strategy-store-{cefi,defi,tradfi}-{prod,staging,dev}-{pid}`.

                                                                                                                          **`resolve_bucket_name` tiered-form mapping (DEPLOYMENT_ENV=prod → `prd`):**
                                                                                                                          - `features-delta-one/{ag}` → `features-delta-one-{ag}-prd-{pid}` (cefi/defi/tradfi/sports/pred)
                                                                                                                          - `features-volatility/{ag}` → `features-volatility-{ag}-prd-{pid}`
                                                                                                                          - `features-onchain/{cefi,defi}` → `features-onchain-{ag}-prd-{pid}`
                                                                                                                          - `features-xinstrument/{ag}` → `features-xinstrument-{ag}-prd-{pid}`
                                                                                                                          - `features-mtf/{ag}` → `features-mtf-{ag}-prd-{pid}`
                                                                                                                          - `execution-store/{cefi,defi,tradfi,sports}` → `execution-store-{ag}-prd-{pid}`
                                                                                                                          - `strategy-store` → `strategy-store-prd-{pid}` (flat string kind needs env-split re-add)
                                                                                                                          - `ml-artifacts` → `ml-artifacts-prd-{pid}`
                                                                                                                          - `ml-training-artifacts` → `ml-training-artifacts-prd-{pid}`

                                                                                                                          `execution-store/prediction` is NOT in the YAML (no prediction entry); needs adding if required.
                                                                                                                          `features-onchain-defi-prd-{pid}` already provisioned with data → **no `terraform apply` needed for this one**;
                                                                                                                          other `-prd-` buckets exist but are empty (provisioned but unpopulated).

- [x] ✅ [INFRA] P0.2. Confirm Group A tiered shape is consistent across all consumers (no NO-ENV fallback survives —
      see the defi cross-AG dead-bucket finding in `defi_manifest_canonicalisation_2026_06_01.md`). —
      deployment-api@6ad269f (slot-5 2026-06-12). Fleet grep across all repos: 1 NO-ENV survivor found in
      `deployment_api/routes/service_status_checkers.py` `SERVICE_OUTPUT_BUCKETS` (hardcoded f-string `{_pid}` names for
      instruments-store + market-data-tick); all other Group A consumers (UAC gcs_paths, UTL
      instrument_lifecycle_loader, deployment-service bucket_config, batch_config_utils) already routing through
      `resolve_bucket_name` or env-tiered YAML. Fix: replaced hardcoded dict with
      `resolve_bucket_name(cloud="gcp", kind=..., asset_group=...)` calls; QG green; quickmerge landed
      deployment-api@6ad269f on live-defi-rollout.

### Phase 1 — Provision + migrate Group B (after canonicalisation gate)

- [ ] [TERRAFORM] P1.1. Provision env-tiered Group B buckets. **PARTIAL — REOPENED 2026-06-29**: GCS census
      (`gsutil ls`/`list_blobs`) revealed MOST `prd` Group B buckets already exist (features-delta-one-_-prd,
      features-onchain-_-prd, features-volatility-_-prd, features-xinstrument-_-prd, features-mtf-\*-prd,
      ml-artifacts-prd); BUT the following `prd` buckets are MISSING (terraform at
      `deployment-service/terraform/gcp/main.tf` used `${var.environment}="prod"` instead of `"prd"` for these):
      `execution-store-cefi-prd-{pid}`, `execution-store-tradfi-prd-{pid}`, `execution-store-defi-prd-{pid}`,
      `execution-store-sports-prd-{pid}`, `ml-training-artifacts-prd-{pid}`, `strategy-store-prd-{pid}`,
      `features-delta-one-pred-prd-{pid}`, `features-mtf-pred-prd-{pid}`. The `prod`-named variants exist
      (`execution-store-cefi-prod-{pid}` etc.) as stale wrong-form per P0.1 note. **BLOCKED-OPERATOR**: SA
      `unified-trading-sa` lacks `storage.buckets.create`. Fix options: (A) Update
      `deployment-service/terraform/gcp/main.tf` Group B resources to use `"prd"` not `${var.environment}`, run
      `terraform apply`; (B) grant SA `storage.admin` temporarily; (C) run `gsutil mb` as operator. The `prd` naming is
      canonical per UTL `_DEPLOYMENT_ENV_SHORT_FORM` + Group A precedent.
- [ ] [SCRIPT] P1.2. Migrate flat→tiered data (single-walk, `gcs_copy_object`/`gcs_delete_object`, manifest-verified).
      **BLOCKED-DEPENDENCY**: gate = (1) all 5 AG G4 `--apply` walks complete [TradFi+Prediction in-flight 2026-06-29];
      (2) P1.1 missing `prd` buckets provisioned. Once both gates clear, run:
      `bash deployment-service/scripts/migrate-flat-to-env-tiered.sh --env prod --cloud gcp --apply` (script fixed
      2026-06-29: `bucket_exists` now uses `list_blobs` not `get_bucket` to work with SA permissions; `strategy-store`
      flat-non-AG pair added). For `features-onchain-defi`: reconcile existing 76 prd objects vs 712 flat objects before
      applying (prd bucket has newer data — copy only flat objects NOT in prd). Script handles AWS side too
      (`--cloud aws`). ⚠️ **SCOPE WARNING**: dry-run 2026-06-29 showed the script covers Group A (market-data-tick,
      instruments-store, dex-pools etc.) — 10.7M objects / 19 TB — NOT just Group B. Running `--apply` as-is would
      re-copy 18 TB of market-data-tick-cefi data unnecessarily (prd bucket already has canonical content). P1.2 scope
      is Group B ONLY: `features-onchain-defi` (708 obj, 976 MB), `ml-models-store` (37 obj), and the blocked ones
      above. Before running: scope the script to only Group B bucket pairs, or use targeted `gcs_copy_object` calls.
- [ ] [CONFIG] P1.3. Re-add `${DEPLOYMENT_ENV_SHORT}-` to the Group B kinds in `cloud-providers.yaml`; remove the
      "ROLLED BACK" / "Temporary env-split rollback" notes; delete the flat-bucket legacy entries. Prerequisite: P1.1
      fully done (all `prd` destination buckets exist) + P1.2 data migrated.
- [ ] [TEST] P1.4. Verify every consumer resolves the tiered name; no NO-ENV form survives (grep + facade tests).

### Phase 2 — Legacy delete

- [ ] [INFRA] P2.1. After parity-verified, delete the flat (non-env) Group B buckets. Snapshot first.

### Phase 3 — Unblock IAM

- [ ] [HANDOFF] P3.1. Signal `bucket_iam_write_protection_per_tier_2026_06_09.md` Phase 2 (Group B) unblocked.

### Phase 4 — Codex alignment

- [x] ✅ [DOCS] P4. Update [bucket-isolation-model.md](/codex/05-infrastructure/bucket-isolation-model.md): tier set =
      `dev`/`stg`/`prd` (+`test`) via `resolve_bucket_name`; staging is its own `-stg-` tier; `mock` is mode-based.
      Reconciled stale `get_bucket_environment` 3-tier framing; SSOT pointer updated from UCI to UTL. — pm@<sha>
      (2026-06-29).

## Success criteria

- All Group A + Group B buckets carry the `-{dev,stg,prd}-` env tier; no flat NO-ENV bucket holds live data.
- `resolve_bucket_name` is the only path; facade/consumer tests green.
- IAM plan's Group B phase unblocked; codex §4 corrected.
