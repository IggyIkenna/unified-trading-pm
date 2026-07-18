---
doc_type: plan
title: Bucket fold — features 25 per-AG/kind → 5 per-AG (features-{ag}-{env}-{pid})
summary:
  "Executes Fold A of the Wave-3 fold design — collapses the ~25 per-AG/kind feature buckets
  (delta-one/volatility/onchain/xinstrument/mtf × cefi/defi/tradfi/sports/pred) into FIVE per-asset-group env-tiered
  buckets features-{ag}-{env}-{pid}, with the feature KIND becoming a top-level path prefix (mirroring the DeFi
  shared-bucket data_type precedent). Largest fold by bucket count (−16 to −20 prd names) and the only one that also
  re-mounts BigQuery feature_external external tables at the new prefix. Follows the DeFi playbook: provision env-tiered
  targets + soft _KIND_ALIASES → dual-verify parity (incl. the features-onchain-defi flat-vs-prd twin reconcile) →
  atomic per-AG writer/reader cutover → re-mount BQ external tables → redeploy + verify-exercised → retarget the feature
  consolidator jobs → delete ~20 source buckets + TF/yaml removal same change. HUMAN plan (operator-driven)."
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos:
  [features-service, ml-service, unified-trading-library, deployment-api, deployment-service, unified-api-contracts]
scope: [engineer, admin]
tags: [gcs, buckets, consolidation, fold, features, migration, env-split, bigquery, lifecycle, infrastructure]
related:
  [
    plans/active/bucket_estate_fold_design_2026_07_13.md,
    plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    plans/active/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    plans/active/bucket_fold_closeout_2026_07_17.md,
    codex/05-infrastructure/bucket-isolation-model.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
    codex/02-data/pipeline-mode-partition.md,
  ]
created: "2026-07-17"
last_updated: "2026-07-17"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 3.2
assigned_role: infra
drift_direction: advance-code
depends_on: [bucket_estate_fold_design_2026_07_13, defi_dedicated_bucket_shared_migration_2026_07_13]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Successor execution plan of bucket_estate_fold_design_2026_07_13 §3 todo 1. Operator ruling 2026-07-17: all 5 folds
  as HUMAN plans. This is Fold A (features — second in the design's risk order, after ml)."
---

# Bucket fold — features 25 per-AG/kind → 5 per-AG (`features-{ag}-{env}-{pid}`)

> **🟡 MIGRATION IN FLIGHT (started 2026-07-17).** Provisions `features-{cefi,defi,tradfi,sports,pred}-{prd,test}-{pid}`
> (GCP + AWS), re-mounts BQ `feature_external` external tables, deletes ~20 source feature buckets. Cross-plan banner on
> [[bucket_estate_consolidation_to_sub100_2026_07_13]] W3 + [[bucket_estate_fold_design_2026_07_13]] Fold A.

**What / why**: Fold A of [[bucket_estate_fold_design_2026_07_13]] — the ~25 per-AG/kind feature buckets → 5 per-AG
env-tiered buckets, kind as a top-level path prefix:
`features-{ag}-{env}-{pid}/{delta-one|volatility|onchain|xinstrument|mtf}/…`. This is the largest fold (−16 to −20 prd
names, design §4) and the ONLY one that also re-points BigQuery external tables.

**Cutover sites (SSOT = design §1 Fold A + §2.B)** — writers: the per-kind `feature_writer.py`
(delta_one/volatility/onchain/xinstrument/mtf); readers: `batch_config_utils.py`, the ml feature consumers,
`trace_all_carry_archetypes.py`. Config: `cloud-providers.yaml` features keys (all 3 copies) incl. the `_KIND_ALIASES`
`features-cross-instrument`→`features-xinstrument` / `features-multi-timeframe`→`features-mtf` that already exist. BQ:
external tables mounted at bucket ROOT (Hive auto-discovery) must move to `gs://features-{ag}-{env}-{pid}/{kind}/` — a
DDL re-issue (external tables hold no data), gated on the writer cutover.

**Known data hazard — the `features-onchain-defi` twin** (design §3 features-provision todo): a flat
`features-onchain-defi-{pid}` (~712 obj) and a `-prd-` variant (~76 obj) both exist. Reconcile BEFORE migrate — copy
only flat objects ABSENT from prd; do not blind-merge. Re-verify the current object counts at execution time (the
design's counts are 2026-07-13).

## Codex SSOTs (read before touching — plan↔codex drift is review-blocking)

- `codex/05-infrastructure/bucket-isolation-model.md` — Group B naming; features rows → folded per-AG shape (closeout).
- `codex/05-infrastructure/manifest-consolidator-ssot.md` — N per-AG feature consolidator jobs → 5 per-AG-bucket jobs.
- `codex/02-data/pipeline-mode-partition.md` — reader-fallback discipline; `_KIND_ALIASES` soft-window.
- Design cross-cutting: [[bucket_estate_fold_design_2026_07_13]] §2.A (consolidator), §2.B (BQ external tables), §2.C
  (IAM), §2.D (alias), §2.E (lifecycle).

## Todos — DeFi-playbook order

- [ ] [DATA] P1. **Provision + yaml scaffold** — add the 5 folded `features-{cefi,defi,tradfi,sports,pred}` keys to
      `cloud-providers.yaml` (all 3 copies), env-tiered; add `_KIND_ALIASES` entries mapping every retired per-kind key
      → its per-AG folded key (extend the existing xinstrument/mtf aliases, §2.D). Provision `features-{ag}-{prd,test}`
      on GCP + AWS via the derived-from-yaml `for_each` (no dev/stg). Verify `terraform plan` shows only the new folded
      buckets as creates. UTL QG green.
- [ ] [DATA] P1. **Reconcile the features-onchain-defi twin THEN parity migrate** — first reconcile
      flat(~712)-vs-prd(~76) per the hazard note (re-measure counts; copy flat objects absent from prd only). Then
      server-side copy each source kind-bucket → `features-{ag}-{env}-{pid}/{kind}/`; byte-count parity both sides per
      (ag, kind). Assert-empty any source with 0 objects (re-measure at execution — several per-AG/kind slots may be
      empty residue) and skip its copy, recording the assertion.
- [ ] [CODE] P1. **Atomic writer/reader cutover** — repoint every Fold A writer/reader (design §1) to
      `kind="features-{ag}"` + a `{kind}/` path prefix. Ship per-repo QG-green: features-service, UTL, ml-service,
      deployment-api, deployment-service, UAC.
- [ ] [CODE] P1. **Re-mount BQ feature_external external tables** — for every affected external table, re-point
      `sourceUris` + `hivePartitioningOptions.sourceUriPrefix` to `gs://features-{ag}-{env}-{pid}/{kind}/` and re-create
      the table (DDL re-issue via UTL `bq_catalog.create_external_table`, §2.B). Gated on the writer cutover landing.
      Verify a query returns rows against the new prefix.
- [ ] [INFRA] P1. **Redeploy + verify-exercised** — redeploy features-service; verify a feature WRITE lands under
      `features-{ag}/{kind}/` and a downstream ml READ resolves it (diff real output). Cite `Evidence: cloudbuild=<id>`
      SUCCESS. Retarget the feature manifest-consolidator jobs → 5 per-AG-bucket jobs (prefix-scoped `_index` per kind);
      no legacy consolidator cron left pointing at a soon-deleted bucket.
- [ ] [INFRA] P1. **Delete sources + TF/yaml removal (SAME change)** — after verify-exercised + a passive read-audit
      window on the ~20 legacy names shows zero reads, delete them (GCP + AWS) and remove their TF/yaml keys in the same
      change; `terraform plan` stays green.
- [ ] [INFRA] P2. **IAM + lifecycle** — join each `features-{ag}-prd` to
      [[bucket_iam_write_protection_per_tier_2026_06_09]] Phase-2 Group-B (signal unblocked per fold); `-test-` twins
      get the test-tier policy. STANDARD→COLDLINE@60d whole-bucket in the derived-from-yaml terraform.
- [ ] [CODE] P3. **Alias sunset** — after the fallback window closes + retired feature kinds are grep-clean, hard-remove
      the `_KIND_ALIASES` entries + retired yaml keys; `terraform plan` green. (May defer to the closeout plan.)

## Progress Log

- **2026-07-17, authored** as the features successor of [[bucket_estate_fold_design_2026_07_13]] §3 todo 1. Object
  counts NOT re-measured this session (larger corpus) — the executor must re-measure per (ag, kind) at provision time,
  especially the features-onchain-defi twin. Nothing executed yet.
- **2026-07-18, DISCOVERY complete (workflow `wf_cff0c0d3-08f`, 4/5 agents; bucket-state agent hit a transient
  ENOTFOUND, re-measure at execution).** Verified Fold-A ground truth — this plan is now execution-ready (mirrors the ml
  Fold-B playbook, which is code-complete + CI-green as the reference). **Current features yaml keys + shapes**
  (deployment-service authoring copy; 5 canonical copies total — the same set as ml incl. the
  `scripts/quality-gates-base/ci-test-cloud-providers.yaml` CI fixture that tick-1 for ml originally missed, so Fold-A
  MUST add its folded keys to ALL 5): per-kind families are **PER-AG DICTS, NON-env-tiered** (env-split rolled back) —
  `features-delta-one` (CEFI/TRADFI/DEFI/PRED, L58-62), `features-volatility` (CEFI/TRADFI only — DEFI/PRED/SPORTS
  removed 2026-07-17, L71-73), `features-onchain` (DEFI only — CEFI removed, L84-85), `features-xinstrument`
  (CEFI/TRADFI/DEFI/PRED, L104-108), `features-mtf` (CEFI/TRADFI/DEFI, L119-122); FLAT env-tiered: `features-sports`
  (L160), `features-calendar` (L189), `features-prediction`→`features-pred-{env}` (L193); FLAT non-env legacy:
  `features-commodity`→`commodity-signals-batch-{pid}` (L167). AWS mirror same shapes (bare `features-…` names in yaml).
  **Aliases** (UTL bucket_naming.py:94-95): `features-cross-instrument`→`features-xinstrument`,
  `features-multi-timeframe`→`features-mtf` already exist; Fold-A extends these + adds folded per-AG destinations.
  **Provisioning:** derived-from-yaml (canonical_buckets.tf for_each handles flat-string-vs-per-AG-dict at L58-61 +
  setup-buckets.py), tiers prd+test — adding the 5 folded env-tiered keys auto-yields 10 buckets; **tofu-apply unsafe →
  provision via direct gcloud/aws** (same as ml). **Consolidator:** GCP **8** feature jobs, AWS **9**
  (`manifest_consolidator_buckets_extended` maps) — **AWS DRIFT: AWS still carries `features-onchain-cefi` (aws
  scheduler.tf:35) that GCP removed 2026-07-17** (reconcile in the retarget). NO consolidator today for
  `features-xinstrument`/`features-mtf`/`features-prediction`. N→5 retarget = rewrite the `_extended` maps to the 5
  folded bucket names + fix the AWS IAM S3 policy loop (aws scheduler.tf:186-187). **PATH_REGISTRY alias-immune rows**
  (`config_interface/paths/registry.py:180,187,194,201`) — literal templates, MUST be hand-repointed (the ml fold proved
  aliases don't cover these). **BQ external tables (Fold-A-unique):** feature buckets mount as BQ external tables at
  bucket ROOT (Hive auto-discovery) via UTL `bq_catalog.create_external_table` + `providers/gcp.py`; folding inserts a
  leading `{kind}/` prefix → every affected external table's `sourceUris`+`sourceUriPrefix` must re-point to
  `gs://features-{ag}-{env}-{pid}/{kind}/` and the table be re-created (DDL re-issue, external tables hold no data),
  gated on the writer cutover. **onchain-defi twin:** `features-onchain-defi-central-element-323112` measured
  EMPTY/ABSENT this session — the design's flat(~712)-vs-prd(~76) hazard is LIKELY STALE (the netflow_xsec_research
  corpus was relocated to onchain-research per [[features_onchain_bare_bucket_not_asset_group_migratable_2026_07_15]]);
  re-measure at execution but expect no reconcile needed. Folded targets `features-{ag}-{prd,test}` confirmed ABSENT.
  **Full per-repo cutover-site + BQ-table lists** in workflow `wf_cff0c0d3-08f` output (transcript dir). NEXT: Fold-A
  execution is the biggest fold (BQ re-mount) — run as its own focused cutover pass (provision+migrate → UTL/yaml+alias
  T0 → features-service+consumers prefix cutover → BQ re-mount → redeploy+verify → consolidator N→5 → zero-reads
  delete), same implement-then-adversarially-verify shape as ml.
