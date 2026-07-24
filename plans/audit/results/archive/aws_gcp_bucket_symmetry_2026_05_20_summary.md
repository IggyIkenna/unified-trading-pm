---
doc_type: audit-result
title: AWS↔GCP Bucket-Name Symmetry Audit — Phase 1 Summary
summary:
  AWS↔GCP bucket-name symmetry audit of cloud-providers.yaml — 64 kind×asset_group rows, 24 kinds with prefix_drift + 10
  with infix_missing need drop_prefix/add_store_infix/add_tick_infix YAML fixes; 0 of 63-char cap violations; 2
  spawning-script drift fixes applied.
status: partial
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [audit, canonicalisation, migration, infrastructure, defi, ssot-audit]
related:
  [
    /plans/audit/results/archive/batch_live_adapter_parity_2026_05_20_summary.md,
    /plans/audit/results/archive/mega_audit_phase_a_issues_human_readable_2026_05_20.md,
  ]
created: 2026-05-20
audited_scope:
  All aws.storage bucket kinds in deployment-service/configs/cloud-providers.yaml vs GCP counterparts (per-asset-group
  dicts one row each) + every deployment-service/scripts/ script that provisions/references buckets on either cloud
date: 2026-05-20
auditor: ikenna-slot-10
parent_epic: batch_live_symmetry_master
severity: P1
resulting_plan:
lib_version:
doc_versions_checked:
---

# AWS↔GCP Bucket-Name Symmetry Audit — Phase 1 Summary

**Date**: 2026-05-20 **Audited file**: `deployment-service/configs/cloud-providers.yaml` **Output**:
`plans/audit/results/aws_gcp_bucket_symmetry_2026_05_20.csv` **Worker**: ikenna-slot-10 (overnight autonomous operation)

---

## Scope

All `aws.storage` bucket kinds in `cloud-providers.yaml` were compared against their GCP counterparts. Per-asset-group
dict kinds produce one CSV row per asset_group. GCP-only kinds (e.g. `defi-validation`, `events` env-less variant) are
noted but not AWS-audited.

---

## Totals

| Metric                           | Count  |
| -------------------------------- | ------ |
| Total rows (kind × asset_group)  | 64     |
| Unique kinds analysed            | 37     |
| Kinds with `prefix_drift`        | **24** |
| Kinds with `infix_missing`       | **10** |
| Kinds `already_symmetric`        | 3      |
| 63-char cap violations (current) | **0**  |
| 63-char cap violations (target)  | **0**  |

Worst current name: `unified-trading-features-xinstrument-tradfi-427895769566` (56 chars, well under 63). Worst target
name after fix: `features-xinstrument-tradfi-427895769566` (40 chars).

---

## Issue Type Breakdown

### prefix_drift — 24 kinds, 41 rows

All AWS templates that carry the `unified-trading-` prefix where GCP uses no such prefix. Action required:
**drop_prefix** on AWS side in the YAML.

Kinds:

- `archetype-state`
- `audit-records` _(GCP uses `trading-audit-records-`; AWS uses `unified-trading-audit-records-` — drop `unified-`
  component)_
- `client-reports`
- `client-statements`
- `config-store`
- `dex-pools`
- `dex-swaps`
- `eigenlayer-rewards`
- `events`
- `evm-defi`
- `features-calendar`
- `features-commodity`
- `features-delta-one` (Group B — env-split rolled back; 5 asset_groups)
- `features-mtf` (Group B — 5 asset_groups)
- `features-onchain` (Group B — 2 asset_groups)
- `features-prediction`
- `features-sports`
- `features-volatility` (Group B — 5 asset_groups)
- `features-xinstrument` (Group B — 5 asset_groups)
- `instruments-store-prediction`
- `manual-audit`
- `ml-artifacts` (Group B)
- `ml-training-artifacts` (Group B)
- `solana-defi`

### infix_missing — 10 kinds, 20 rows

AWS templates that have both the `unified-trading-` prefix AND a missing structural infix (`-store-` or `tick-`). Action
required: **drop_prefix + add_store_infix** or **drop_prefix + add_tick_infix**.

| Kind                          | asset_groups               | Missing infix                                             | Action                       |
| ----------------------------- | -------------------------- | --------------------------------------------------------- | ---------------------------- |
| `strategy-store`              | cefi, tradfi, defi         | `-store-` (AWS: `unified-trading-strategy-cefi-…`)        | drop_prefix\|add_store_infix |
| `execution-store`             | cefi, tradfi, defi         | `-store-` (AWS: `unified-trading-execution-cefi-…`)       | drop_prefix\|add_store_infix |
| `instruments-store`           | cefi, defi, tradfi, sports | `-store-` (AWS: `unified-trading-instruments-cefi-…`)     | drop_prefix\|add_store_infix |
| `strategy-store-prediction`   | n/a                        | `-store-` (AWS: `unified-trading-strategy-pred-…`)        | drop_prefix\|add_store_infix |
| `execution-store-prediction`  | n/a                        | `-store-` (AWS: `unified-trading-execution-pred-…`)       | drop_prefix\|add_store_infix |
| `market-data`                 | cefi, defi, tradfi, sports | `tick-` (AWS: `unified-trading-market-data-cefi-…`)       | drop_prefix\|add_tick_infix  |
| `market-data-tick-prediction` | n/a                        | `tick-` (AWS: `unified-trading-market-data-pred-…`)       | drop_prefix\|add_tick_infix  |
| `ml-models-store`             | n/a                        | `-store` suffix (AWS: `unified-trading-ml-models-…`)      | drop_prefix\|add_store_infix |
| `ml-predictions-store`        | n/a                        | `-store` suffix (AWS: `unified-trading-ml-predictions-…`) | drop_prefix\|add_store_infix |
| `ml-configs-store`            | n/a                        | `-store` suffix (AWS: `unified-trading-ml-configs-…`)     | drop_prefix\|add_store_infix |

### already_symmetric — 3 kinds

Per Q7(b) operator decision 2026-05-13: `unified-trading-` prefix already dropped. No YAML change required.

- `pnl-store-defi`
- `positions-store-defi`
- `risk-store-defi`

---

## market-data tick- Infix Direction

The `tick-` infix on GCP (`market-data-tick-{ag}-{env}-{pid}`) is a GCP-specific historical naming artifact from MTDS
service naming. The current YAML comment documents the asymmetry as deliberate ("Per-cloud template captures the
asymmetry; resolver hides it behind same kind key").

**Audit finding**: AWS buckets are newly provisioned (env-tiered names provision in code_freeze Phase 2.6 per YAML
notes). The target direction per this audit is **ADD `tick-` to AWS** (align AWS to GCP), not drop `tick-` from GCP,
because:

1. GCP has existing on-disk data in `market-data-tick-*` bucket names (Phase 2.6 migration in progress).
2. Dropping `tick-` from GCP would require renaming 4 existing GCP buckets with data.
3. Adding `tick-` to AWS aligns to the canonical GCP shape at zero migration cost (AWS env-tiered buckets are
   provisioned fresh in Phase 2.6 anyway).

**Operator confirm required** before executing: if master plan says to DROP `tick-` from GCP instead, the `market-data`
rows should be reclassified as `gcp_only_change` with GCP YAML edits.

---

## Group B Env-Split Rollback Consistency

All 9 Group B kinds (`features-delta-one`, `features-volatility`, `features-onchain`, `features-xinstrument`,
`features-mtf`, `strategy-store`, `execution-store`, `ml-artifacts`, `ml-training-artifacts`) correctly have **no
`${DEPLOYMENT_ENV_SHORT}`** in both GCP and AWS templates. The rollback is symmetric. No `env_split_rollback` rows in
the CSV.

---

## 63-Character Cap Status

**No violations — all clear.**

- All 64 current AWS names (resolved with env=`stg`, account=`427895769566`): max 56 chars.
- All 64 target AWS names after fixes: max 40 chars.
- Longest current: `unified-trading-features-xinstrument-tradfi-427895769566` (56 chars).
- Longest target: `features-xinstrument-tradfi-427895769566` (40 chars).

---

## Recommended YAML Changes

The following 34 kinds need an update to `aws.storage` in `cloud-providers.yaml`.

**High priority — structural infix missing (10 kinds, affects query correctness):**

1. `strategy-store` — add `-store-` between `strategy` and `{ag}` in all 3 asset_group templates
2. `execution-store` — add `-store-` between `execution` and `{ag}` in all 3 asset_group templates
3. `instruments-store` — add `-store-` between `instruments` and `{ag}` in all 4 asset_group templates
4. `strategy-store-prediction` — add `-store-` between `strategy` and `pred`
5. `execution-store-prediction` — add `-store-` between `execution` and `pred`
6. `market-data` — add `tick-` infix in all 4 asset_group templates
7. `market-data-tick-prediction` — add `tick-` infix between `market-data-` and `pred`
8. `ml-models-store` — add `-store` suffix (currently `ml-models-…`, target `ml-models-store-…`)
9. `ml-predictions-store` — add `-store` suffix (currently `ml-predictions-…`, target `ml-predictions-store-…`)
10. `ml-configs-store` — add `-store` suffix (currently `ml-configs-…`, target `ml-configs-store-…`)

**Standard prefix drop only (24 kinds):**

Drop `unified-trading-` prefix from: `features-delta-one`, `features-volatility`, `features-onchain`,
`features-xinstrument`, `features-mtf`, `ml-training-artifacts`, `ml-artifacts`, `features-sports`,
`features-commodity`, `features-calendar`, `instruments-store-prediction`, `features-prediction`, `dex-pools`,
`dex-swaps`, `evm-defi`, `eigenlayer-rewards`, `solana-defi`, `events`, `config-store`, `archetype-state`,
`client-reports`, `client-statements`, `manual-audit`.

For `audit-records`: change `unified-trading-audit-records-` to `trading-audit-records-` (align to GCP
`trading-audit-records-` prefix).

---

## Notes / Caveats

- `events` (GCP): still env-less (`${GCP_PROJECT_ID}-events`) per YAML — high blast radius, needs operator confirm
  before env-tiering. AWS `events` is env-tiered (`unified-trading-events-${DEPLOYMENT_ENV_SHORT}-…`). After prefix
  drop, AWS would be `events-${DEPLOYMENT_ENV_SHORT}-${AWS_ACCOUNT_ID}` — structurally different from GCP. This
  structural divergence is pre-existing and outside Phase 1 scope.
- `client-reports` / `client-statements`: GCP uses pid-prefix flat format (`${GCP_PROJECT_ID}-client-reports`); AWS
  would become `client-reports-${DEPLOYMENT_ENV_SHORT}-${AWS_ACCOUNT_ID}` after fix — structurally different from GCP.
  Pre-existing structural divergence; env-tier on GCP is post-Phase-1.
- `defi-validation`: Both GCP (`${pid}-defi-validation`) and AWS (`unified-trading-defi-validation-${account}`) are
  intentionally env-less (validation runs target mainnet; environment-neutral). Structural divergence documented in
  `check_symmetry.py` `_KNOWN_STRUCTURAL_DIVERGENCES`.
- All changes are YAML-only (template string edits). On-disk bucket renaming / data migration follows code_freeze Phase
  2.6 schedule.

---

## Spawning Scripts Audit

**Date**: 2026-05-20 (slot 8 Phase 1B) **Scope**: every script in `deployment-service/scripts/` that provisions or
references buckets on either cloud.

| Script                                               | Key line(s)        | Status             | Notes                                                                                                                                                                                                    |
| ---------------------------------------------------- | ------------------ | ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `scripts/aws/setup-defi-buckets.sh`                  | L8, L44–45, L71–86 | ✅ SSOT-consult    | Reads cloud-providers.yaml templates; Phase 1 symmetry fix applied (deployment-service@b9029ad). One env-less `events` bucket hardcoded (intentional — matches YAML).                                    |
| `scripts/aws/provision-aws-buckets.sh`               | L6–8               | ✅ SSOT-consult    | Delegates entirely to setup-defi-buckets.sh; no direct bucket name construction.                                                                                                                         |
| `scripts/aws/apply-bucket-policies.sh`               | —                  | ✅ no provisioning | Applies IAM policies to existing buckets; reads bucket names via aws CLI, does not construct names.                                                                                                      |
| `scripts/aws/migrate-defi-buckets-prod-to-prd.sh`    | —                  | ✅ migration only  | Renames `prod`→`prd` on existing on-disk buckets; no SSOT drift (uses resolved names).                                                                                                                   |
| `scripts/setup-buckets.py`                           | —                  | ✅ SSOT-consult    | Reads cloud-providers.yaml + dependencies.yaml via `load_bucket_config()`; no hardcoded names.                                                                                                           |
| `scripts/provision-test-buckets.sh`                  | —                  | ✅ no drift        | Test bucket names derived from kind names; no `unified-trading-` prefix.                                                                                                                                 |
| `scripts/provision_manual_audit_buckets.sh`          | L28                | ⚠️ DRIFT FIXED     | Was `unified-trading-manual-audit-${1}-${account}` → fixed to `manual-audit-${1}-${account}` (deployment-service@this-commit). Aligns to cloud-providers.yaml `aws.storage.manual-audit`.                |
| `scripts/provision_audit_records_retention_lock.sh`  | L31                | ⚠️ DRIFT FIXED     | Was `unified-trading-audit-records-${env}-${account}` → fixed to `trading-audit-records-${env}-${account}` (deployment-service@this-commit). Aligns to cloud-providers.yaml `aws.storage.audit-records`. |
| `scripts/bootstrap/bootstrap_aws.sh`                 | L130–137           | 🔵 LEGACY          | Hardcoded `unified-trading-instruments-*` + `unified-trading-market-data-*` names from pre-Phase-1. Bootstrap script only; not used in normal provisioning. On-disk buckets renamed in Phase 5.          |
| `scripts/setup-gcs-lifecycle-policies.sh`            | —                  | ✅ GCP-only        | GCS lifecycle rules only; no bucket name construction.                                                                                                                                                   |
| `scripts/infra/configure_audit_bucket_versioning.sh` | —                  | ✅ SSOT-consult    | Reads GCP_BUCKET from env + applies versioning; caller supplies name from resolver.                                                                                                                      |

**Summary**: 2 drift fixes applied. 1 legacy script (bootstrap_aws.sh) uses old names — intentional, as it is not
invoked in normal deployment flows (superseded by `setup-buckets.py`). Automated check:
`bash scripts/bucket_naming/check_symmetry.sh` exits 0 (65 kind×ag pairs checked; 4 known structural divergences
exempted with documentation).

**Automated symmetry check**: `deployment-service/scripts/bucket_naming/check_symmetry.sh` — run after any future
cloud-providers.yaml edit to detect regressions.
