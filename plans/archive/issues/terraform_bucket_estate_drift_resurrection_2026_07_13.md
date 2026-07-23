---
doc_type: issue
title:
  "Terraform bucket estate drift: 2026-07-12 apply resurrected ~30 buckets deleted by the estate cleanup; TF/yaml-copy/
  provisioning configs encode 4 stale naming generations, so cleanup regresses on every apply"
summary:
  "Surfaced by the 2026-07-13 full bucket estate audit (follow-on to [[gcs_bucket_estate_cleanup_2026_07_10]]): a
  terraform apply at 2026-07-12T21:59Z (GCS audit-log-verified: principal ikenna@odum-research.com, Terraform 1.5.7,
  caller IP 78.144.185.23) recreated ~30 empty buckets the cleanup had deleted on 07-10/07-12 — the -prod-/-staging-
  Group-B env artifacts, retired-kind test buckets (gas-fees-test, solana-defi-test, evm-defi-test — including the one
  the cleanup deliberately did NOT recreate), and full-word -prediction-test- names. Root cause:
  deployment-service/terraform/gcp/main.tf still declares ~71 google_storage_bucket resources spanning naming schemes
  the resolver never emits (Group-B '-${var.environment}-' with LONG env words dev/staging/prod; legacy flat tick/
  instruments names; full-word -prediction-). Estate consolidation cannot stick until Terraform (and its state) is
  reconciled with the canonical cloud-providers.yaml estate. Bundled here because they are the same config-drift class:
  (a) the UAC-packaged and PM-mirror copies of cloud-providers.yaml are STALE at 46 kinds vs canonical 36 — standalone
  installs/wheels resolve 10 deleted kinds via the packaged fallback; (b) bucket_config.yaml + setup-buckets.py read a
  4th pre-canonical scheme with literal-unsubstituted {category_lower} placeholders; (c) an out-of-band
  STANDARD→COLDLINE@14d lifecycle rule exists on 78 live buckets incl. every -prd tick bucket — no in-repo
  terraform/script applies it and codex gcs-lifecycle-policies.md says those buckets are intentionally NOT lifecycle'd
  (untracked config drift, cost-relevant for backfill re-reads of COLDLINE objects)."
status: resolved
nature: notes
asset_group: [cross-cutting]
stage: [data, meta]
repos: [deployment-service, unified-api-contracts, unified-trading-pm, unified-trading-library]
scope: [engineer, admin]
tags: [gcs, buckets, terraform, config-drift, cleanup-regression, lifecycle, data-pipeline-correctness]
related:
  [
    /plans/archive/2026_07/gcs_bucket_estate_cleanup_2026_07_10.md,
    /plans/active/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    /plans/archive/2026_07/bucket_env_split_rollout_2026_06.md,
  ]
created: "2026-07-13"
parent_epic: infrastructure_master
priority: P0
source:
  "2026-07-13 operator-requested full bucket estate audit. Live estate re-enumerated via orchestrator-VM admin
  credential (241 buckets); creation timestamps clustered a 30-bucket batch at 2026-07-12T21:59Z; GCS audit logs
  attributed the batch to a Terraform 1.5.7 apply. Multi-agent verification pass confirmed the TF resource inventory
  (file:line in body) and the yaml-copy staleness via git history (deployment-service@c72a0cb / @e898563 removals never
  propagated to the UAC/PM copies, both last touched 2026-06-10)."
execution_scope: local-only
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
assigned_vm:
resolved_by: "2026-07-19 bucket_fold_closeout tail-item sweep — all GCP directions (a/b/c/d) + tail items done"
---

# Terraform bucket estate drift — cleanup deletions resurrected by apply

## What happened (verified)

- **2026-07-12T21:59Z**: one `terraform apply` recreated ~30 buckets deleted by [[gcs_bucket_estate_cleanup_2026_07_10]]
  — all empty, all with the TF-declared lifecycle/versioning applied (the signature that distinguishes them from the
  cleanup-created gap buckets of 02:39Z the same day). GCS audit log:
  `protoPayload.methodName="storage.buckets.create"`, principal `ikenna@odum-research.com`, user agent
  `Terraform/1.5.7`, 39 create events in the window.
- Recreated sets (all confirmed existing + empty as of 2026-07-13): 26 `-prod-` Group-B names
  (`features-{delta-one,volatility,onchain}-{ag}-prod-…`, `execution-store-{ag}-prod-…`, `ml-training-artifacts-prod-…`,
  etc.), retired-kind test buckets `gas-fees-test-…` / `solana-defi-test-…` / `evm-defi-test-…` (gas-fees-test had been
  **deliberately not recreated** by the cleanup), full-word `-prediction-test-` names
  (`instruments-store-prediction-test-…`, `market-data-tick-prediction-test-…`), and the flat `features-calendar-…`
  twin.

## Root cause — TF declares 4 naming generations the resolver never emits

`deployment-service/terraform/gcp/main.tf` (verified file:line):

- Group-B env-suffixed resources with LONG env words via `-${var.environment}-` (variables.tf:12-19 validates
  {dev,staging,prod}; the resolver's short map emits {dev,stg,prd,test} — `-prod-` is unreachable by any code path):
  features-delta-one ×5 AGs (:807-879), features-volatility ×5 (:988-1060), features-onchain ×2 (:1170-1188),
  ml-models/predictions/configs/training-artifacts (:1206-1239), strategy-store ×5 (:1250-1327), execution-store ×5
  (:1283-1349). These are exactly the 63 `ROLLED_BACK_ENV_ARTIFACT` buckets the cleanup deleted.
- Legacy-kind test buckets: gas-fees-test (:736), solana-defi-test (:760), evm-defi-test (:784) — kinds removed from
  cloud-providers.yaml 2026-07-10/12.
- Full-word `-prediction-test-` resources (:353, :685, :970, :1151) — canonical token is `pred`.
- Legacy flat tick/instruments resources (`market-data-tick-{ag}-{pid}`, `instruments-store-{ag}-{pid}`, :134-272,
  :464-604) carrying the only NEARLINE@90 lifecycle, while the canonical `-prd-` buckets production actually writes to
  are **not in Terraform at all** (only `instruments-store-sports-prd` :448-462 + the 3 dedicated DeFi `-prd` stems
  :530-579).
- Forward hazard: `lst-rates-prd`/`perp-funding-prd` (:530-579) are declared and currently LIVE (correct today), but
  [[defi_dedicated_bucket_shared_migration_2026_07_13]]'s pending deletion todos will re-trigger this exact bug unless
  the TF resources + bucket_config.yaml entries are removed in the same change (oracle-prices-prd/gas-fees-prd were
  already resurrected once by a 2026-07-13 tofu apply, per main.tf's own comments :523-528, :581-586).
- `terraform/modules/shared-infrastructure/gcp/main.tf` declares another 18 env-suffixed buckets overlapping main.tf's
  names with different AG sets — two TF codepaths can fight over one bucket name.

## Same-class drift bundled here

1. **Stale cloud-providers.yaml copies (verified)**: `unified-api-contracts/unified_api_contracts/config/` and
   `unified-trading-pm/configs/` copies carry 46 kinds/cloud (incl. the 10 removed 2026-07-10/12: dex-swaps, evm-defi,
   solana-defi, lending-indices, oracle-prices, liquidations, gas-fees, pnl/positions/ risk-store-defi) vs canonical 36
   in `deployment-service/configs/`. UTL `bucket_naming.py` probe order makes the UAC packaged copy the ONLY candidate
   in a standalone install/wheel/VM-tarball-without-deployment-configs — deleted kinds still resolve there. Removals
   landed in deployment-service@c72a0cb (07-10) + @e898563 (07-12); both copies last touched 2026-06-10.
2. **bucket_config.yaml + setup-buckets.py**: 4th scheme (no env axis, `-test-` infix, `{category_lower}` placeholder
   the GCP path never substitutes); templates come from `dependencies.yaml`, not the SSOT — cleanup already bypassed it
   with raw `gcloud` (estate plan :445-452).
3. **Out-of-band lifecycle drift**: live metadata (admin-credential read, 2026-07-13) shows STANDARD→COLDLINE@14d on 78
   buckets incl. all 5 `-prd` tick buckets and 106 buckets with versioning enabled. No in-repo applier produces
   COLDLINE@14 (closest is the unapplied `docs/GCS_LIFECYCLE_AGGRESSIVE_STRATEGY.md` proposal);
   `/codex/05-infrastructure/gcs-lifecycle-policies.md:97-98` claims tick buckets are intentionally NOT lifecycle'd.
   Cost-relevant: backfill/reader re-reads of >14-day-old tick objects now pay COLDLINE retrieval.
4. **e2e fixture polluter**: `e2e-testing/scripts/common/setup-gcp-fixtures.sh:39-53` `gsutil mb`'s transposed
   non-canonical names (`market-tick-data-store-defi-…`, `processed-market-data-store-defi-…`, `pnl-store-…`).

## Direction (operator ruling needed on a-c)

a. Reconcile TF: delete every resource for a bucket the cleanup removed (+ `terraform state rm`), replace long-env
Group-B blocks; decide import-vs-unmanaged for the canonical `-prd-` buckets (importing gives lifecycle a tracked home;
unmanaged keeps applies harmless — pick one, document in codex). b. Sync the UAC-packaged + PM-mirror yaml copies with
the canonical 36-kind file (mechanical; UAC needs a ship). c. Decide the lifecycle policy actually wanted (COLDLINE@14d
out-of-band vs codex "not lifecycle'd" vs bucket_config's 365d vs TF's 90d — four contradictory declarations), then
encode it in ONE tracked place. d. Retire or resolver-backend setup-buckets.py; fix the e2e fixture script's names. e.
Re-delete the resurrected ~30 empty buckets only AFTER (a) lands, else they return on the next apply.

**Operator ruling 2026-07-13 (partial — env-split axis)**: the `bucket_env_split_rollout_2026_06.md` conflict is
resolved — env-split STANDS but merges into the estate-consolidation Group-B folds as ONE migration ("no double
migrates"); consolidated Group-B buckets are env-tiered from birth. See the ruling banner in that plan. Consequence for
(a): the long-env Group-B terraform blocks are NOT re-pointed at per-kind `-prd-` twins — they get deleted, and the
future consolidated (folded, env-tiered) buckets get authored fresh.

**Operator rulings 2026-07-13 (complete — all axes)**: (a) **terraform derived-from-yaml** — one `for_each` bucket block
generated from cloud-providers.yaml's canonical names, existing canonical buckets imported into it, hand-written blocks
only for genuine infra buckets; `terraform plan` becomes the drift detector. (c) **lifecycle = cold-tier move at 60d**
(STANDARD→COLDLINE@60d replacing the untracked @14d; operator verbatim "nearlcoldline nmove after 60d" — a
NEARLINE@60→COLDLINE ladder reading is possible, confirm before applying), encoded in the derived-from-yaml terraform

- `gcs-lifecycle-policies.md` update. Execution owned by `bucket_estate_consolidation_to_sub100_2026_07_13.md` Wave 0.
  Also ruled same day: dev/stg tiers retired (Wave 1); env-split plan unlocked + archived (superseded).

## Wave-3 fold assessment (2026-07-19) — per-fold slice DONE, broader reconcile remains → STAYS OPEN

The 5 Wave-3 folds executed the per-fold slice of direction (a)+(c): each fold **imported** its folded canonical
`-prd-`/`-test-` bucket into the derived-from-yaml Terraform `for_each` and **`state rm`'d** the deleted source buckets,
and provisioned the folded buckets **STANDARD→COLDLINE@60d** (replacing the untracked @14d for those buckets). ~30
source buckets removed; estate 114 GCP; `gcs-lifecycle-policies.md` + `bucket-isolation-model.md` +
`manifest-consolidator-ssot.md` codex updated to the folded shapes (PM@8ea8abd89). **Remaining (why this stays open)**:
the BROADER main.tf reconcile — deleting the long-env Group-B TF blocks that still declare stale naming generations (the
~32-destroy drift, operator-aware, do NOT `tofu apply` autonomously), syncing the UAC-packaged + PM-mirror yaml copies
to the canonical kind set, retiring `setup-buckets.py` / fixing the e2e fixture polluter, and re-deleting any
resurrected empties AFTER the block deletion — is NOT done. Close when the estate TF is fully derived-from-yaml with
`terraform plan` clean.

## 2026-07-19 (cont.) — PRIMARY (bucket-estate resurrection) RESOLVED; issue narrowed to non-bucket tail

The operator-requested "terraform-drift yaml-sync + destroy reconciliation" was executed to completion on real infra
(ADC admin, central-element-323112). The **bucket-estate resurrection root cause (directions a + b) is now resolved**;
`terraform plan` is the clean drift detector the rulings intended.

- **(a) TF derived-from-yaml — DONE.** The long-env Group-B `-prod-`/`-staging-` bucket blocks, the retired-kind test
  buckets (gas-fees-test / solana-defi-test / evm-defi-test), and the full-word `-prediction-test-` resources are GONE
  from `main.tf` (only migration comments remain); the canonical estate is the `canonical_buckets.tf`
  `google_storage_bucket.canonical` for_each. **End-state `tofu plan` = 0 bucket create / 0 bucket destroy** (the
  ~32-destroy resurrection drift no longer exists — nothing resurrects, nothing is orphaned).
  deployment-service@a91e520.
- **(b) yaml-copy sync — DONE.** The 13 retired bucket-kind keys stripped from ALL copies: deployment-service/configs
  SSOT (ds@a91e520), UAC-packaged (UAC@a8e7f46d), PM-mirror configs + ci-test fixture (PM@cb1fb1916), UTL test fixture
  (UTL@45957afa). Standalone-install/wheel resolution no longer surfaces deleted kinds.
- **Bonus in-path drift reconciled** (surfaced by the apply, all ds@a91e520): 4 Cloud Run jobs + 5 Cloud Scheduler crons
  that existed in GCP but were absent from TF state were **imported** (state was lost from a prior apply → they 409'd on
  re-create); the 3 catalogue-regen IAM grants were **repointed** off the deleted flat
  `strategy-store-central-element- 323112` → canonical `strategy-store-prd-…` (matches UAC
  `STRATEGY_STORE_BUCKET_TEMPLATE` + the `enumerate_*.py` writers; the [[strategy_store_split_brain_2026_07_13]] code
  side was already fixed, only the TF IAM lagged); the governance-snapshot-monitor **cpu 0.5→1** create-blocking bug was
  fixed (gen2 rejects <1 vCPU); the pre-existing imperatively-created **`odum_portal`** Cloud Run domain mapping was
  imported (was making apply try to re-create a live mapping).

**REMAINING (why this STILL stays open — but the scope is now the non-bucket tail, not the estate):** (c) the four
contradictory lifecycle declarations are reconciled to COLDLINE@60d **for the folded buckets only** — a single-source
encoding for the whole estate is not done; (d) `setup-buckets.py` / `bucket_config.yaml` 4th-scheme retirement and the
`e2e-testing/scripts/common/setup-gcp-fixtures.sh` non-canonical-name polluter are untouched; the AWS fold-completion is
operator-deprioritized; and one orthogonal residual `tofu plan` diff remains —
`google_bigquery_table.feature_external["defi__onchain_features"]` `require_partition_filter=false→true` (pre-existing,
applying risks breaking partition-filter-less consumer queries — left un-applied, not a bucket concern). Close when
(c)+(d) land.

## 2026-07-19 (tail-item sweep) — RESOLVED

Operator asked to clear the remaining tail. On inspection most were already resolved; the rest are now done, so this
issue is CLOSED (`status: resolved`). Verifications:

- **(c) lifecycle single-source — DONE.** `canonical_buckets.tf` encodes `STANDARD→COLDLINE@60d` (read straight, not a
  NEARLINE ladder — the ruling ambiguity is resolved in-code); live sampling of a canonical folded bucket
  (`features-cefi-prd`), a Group-A raw bucket (`market-data-tick-cefi-prd`), and `instruments-store-sports-prd` all show
  uniform COLDLINE@60d — the untracked @14d is gone estate-wide; `gcs-lifecycle-policies.md` documents it. The four
  contradictory declarations are reconciled to one.
- **(d) `setup-buckets.py`/`bucket_config.yaml` + e2e polluter — DONE.** `setup-buckets.py` was rewritten 2026-07-14 to
  derive every service/data bucket name from the UTL resolver (the stale `{category_lower}` 4th-scheme is gone);
  `bucket_config.yaml` is now only the genuine-infra registry. `e2e-testing/scripts/common/setup-gcp-fixtures.sh` no
  longer exists (the non-canonical-name polluter is gone).
- **Resurrected empties — DONE** (moot): `terraform plan` is 0-create/0-destroy and no long-env/retired blocks remain in
  `main.tf`, so nothing resurrects; the once-flagged `us-central1aa` run-sources cruft bucket is already deleted.
- **BQ residual — DONE.** No code SQL-queries the external table (readers hit GCS parquet), so the config's intended
  `require_partition_filter=true` is safe — applied via targeted `tofu apply` (1 changed, 0 destroyed). `tofu plan` is
  now truly 0-change on this resource.
- **AWS fold-completion** is operator-deprioritized and tracked separately (GCP is where the live data is); the
  `_KIND_ALIASES` consumer migration for the 11 coupled retired kinds is tracked in `bucket_fold_closeout_2026_07_17.md`
  todo 1 (not this issue). Neither is a GCP terraform-drift-resurrection blocker.
