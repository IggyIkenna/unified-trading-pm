---
title: Bucket env-split rollout — re-enable -{dev,stg,prd}- everywhere (Group A confirm + Group B un-rollback)
parent_epic: infrastructure_master
assigned_vm: vm-cross-cutting
priority: P1
status: active
execution_scope: cloud-apply
estimate_class: infra
estimate_baseline_ai_days: 4.0
estimate_calibrated_ai_days: 3.2
created: 2026-06-09
locked_by: live-defi-rollout
locked_since: 2026-06-09
related_plans:
  - plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md
  - plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md
  - plans/active/bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md
Codex SSOTs:
  - codex/05-infrastructure/bucket-isolation-model.md
---

# Bucket env-split rollout — re-enable `-{dev,stg,prd}-` everywhere

> **This is the named successor** referenced by `deployment-service/configs/cloud-providers.yaml` ("Re-enable when:
> bucket_env_split_rollout_2026_06.md Phase 1 provisions + migrates data") — it was a dangling reference until now.
> **Operator directive 2026-06-09: env-splits everywhere** (Group A _and_ Group B, all kinds). The temporary Group B
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
- **Codex drift**: [bucket-isolation-model.md](../../codex/05-infrastructure/bucket-isolation-model.md) §4 says "staging
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
      (`…-{ag}-{env}-{pid}`), and which hold data. Confirm `resolve_bucket_name` emits the tiered shape for each kind.
      — unified-trading-pm@690376cd5 (slot-5 2026-06-12). GCS census + UTL resolver verified.

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
- [ ] [INFRA] P0.2. Confirm Group A tiered shape is consistent across all consumers (no NO-ENV fallback survives — see
      the defi cross-AG dead-bucket finding in `defi_manifest_canonicalisation_2026_06_01.md`).

### Phase 1 — Provision + migrate Group B (after canonicalisation gate)

- [ ] [TERRAFORM] P1.1. Provision env-tiered Group B buckets (`-prd-` first; `-dev-`/`-stg-` as needed) for all 9 kinds
      × AGs via `deployment-service/terraform`.
- [ ] [SCRIPT] P1.2. Migrate flat→tiered data (single-walk, `gcs_copy_object`/`gcs_delete_object`, manifest-verified).
- [ ] [CONFIG] P1.3. Re-add `${DEPLOYMENT_ENV_SHORT}-` to the Group B kinds in `cloud-providers.yaml`; remove the
      "ROLLED BACK" / "Temporary env-split rollback" notes; delete the flat-bucket legacy entries.
- [ ] [TEST] P1.4. Verify every consumer resolves the tiered name; no NO-ENV form survives (grep + facade tests).

### Phase 2 — Legacy delete

- [ ] [INFRA] P2.1. After parity-verified, delete the flat (non-env) Group B buckets. Snapshot first.

### Phase 3 — Unblock IAM

- [ ] [HANDOFF] P3.1. Signal `bucket_iam_write_protection_per_tier_2026_06_09.md` Phase 2 (Group B) unblocked.

### Phase 4 — Codex alignment

- [ ] [DOCS] P3. Update [bucket-isolation-model.md](../../codex/05-infrastructure/bucket-isolation-model.md): tier set
      = `dev`/`stg`/`prd` (+`test`) via `resolve_bucket_name`; staging is its own `-stg-` tier; `mock` is mode-based.
      Reconcile the stale `get_bucket_environment` 3-tier framing.

## Success criteria

- All Group A + Group B buckets carry the `-{dev,stg,prd}-` env tier; no flat NO-ENV bucket holds live data.
- `resolve_bucket_name` is the only path; facade/consumer tests green.
- IAM plan's Group B phase unblocked; codex §4 corrected.
