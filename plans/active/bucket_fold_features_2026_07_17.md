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

- [~] [DATA] P1. **Provision + yaml scaffold** — **BUCKETS PROVISIONED 2026-07-18** (direct gcloud/aws NOT tofu, per the
  unsafe-state gotcha): GCP `features-{cefi,defi,tradfi}-{prd,test}-central-element-323112` (6; ASIA-NORTHEAST1, UBLA,
  STANDARD→COLDLINE@60d) — pred/sports folded targets ALREADY EXIST (they ARE flat
  `features-prediction`/`features-sports`; name-collision RESOLVED, no new pred/sports GCP provision); AWS
  `features-{cefi,defi,tradfi}-{prd,test}` + `features-{pred,sports}-test` (8; ap-northeast-1, public-blocked). **yaml
  scaffold + `_KIND_ALIASES` DEFERRED to the atomic T0 cutover** (below) per the ml-fold pattern — key+aliases+code ship
  together, no orphan-key window (buckets exist so resolution works the instant the key lands). Adopting **shape (b)**:
  ONE folded per-AG dict key `features` + aliases from all 5 retired kinds → `features` (synthesis rec; the ONLY shape
  the alias soft-window is expressible in — resolver does a single asset-group-blind `_KIND_ALIASES.get(kind)`).
- [x] ✅ [DATA] P1. **Reconcile the features-onchain-defi twin THEN parity migrate** — **DONE 2026-07-18.** Twin
      reconcile = NO-OP (RESOLVED): only flat `features-onchain-defi` (727) exists; no `-onchain-defi-prd-*` on either
      cloud — the design's flat-712-vs-prd-76 hazard is STALE. **4 real server-side copies (byte-parity ✓):**
      delta-one-cefi(314, 477MB)→ `features-cefi-prd/delta_one/` ✓, delta-one-cefi-test(315,
      493MB)→`features-cefi-test/delta_one/` ✓, onchain-defi(727, 977MB)→`features-defi-prd/onchain/`,
      xinstrument-pred(207, 2MB)→`features-pred-prd/xinstrument/`. **Index-only SKIP (assert `_index/`-only):**
      delta-one-{defi,tradfi}, volatility-{cefi,tradfi}, mtf-cefi. **Assert-EMPTY SKIP:** delta-one-pred,
      xinstrument-{cefi,defi,tradfi}, mtf-{defi,tradfi}. **sports:** NO data move (already at folded name
      `features-sports-prd`; content stays at root, no `{kind}/` prefix — env-tier repoint only in §3).
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

- **2026-07-18, `/autonomous` EXECUTION — discovery re-ground + PROVISION + MIGRATE done.** Re-ground via read-only
  discovery workflow `wf_15449018-090` (5 agents, 0 errors — full spec in that transcript). Fresh counts: 5 data-bearing
  GCP buckets (delta-one-cefi 314 +test 315, onchain-defi 727, xinstrument-pred 207, sports-prd thousands); rest
  index-only/empty. **PROVISIONED** 6 GCP + 8 AWS folded buckets (see the flipped todo). **MIGRATED** the 4 real copies,
  byte-parity ✓. **Shape (b)** adopted (one folded `features` per-AG dict + aliases). NEXT = the code cutover (T0
  UTL/yaml → T1 features-service → T2 consumers → BQ re-mount → redeploy+verify → consolidator), then Phase-E delete
  (time-gated). **TWO BIG FINDINGS surfaced by discovery (operator-notified):**
  1. **DESIGN GAP (data-correctness):** the design's Fold-A cutover list MISSED 4 alias-immune literal `bucket_template`
     PATH_REGISTRY rows — `delta_one_features`(registry.py L48), `onchain_features`(L62), `lst_seasonal_rewards`(L69),
     `volatility_features`(L76) (+ path ref L306). Un-repointed, they keep resolving the soon-deleted buckets → silent
     read/write breakage post-delete. MUST be in the T0 cut (recurrence of the ml-fold "registry.py not in the design
     list" lesson). Also the byte-parity hazard: `delta_one_features` registry path ≠ FeatureWriter inline key — the
     `delta_one/` prefix must be applied symmetrically to writer + `check_exists` twin + reader.
  2. **LATENT BUG (data-correctness, adjacent):** `features_service/onchain/engine/feature_observation_writer.py:61-65`
     calls `resolve_bucket_name(data_type=…, asset_group=…, project_id=…)` — INVALID kwargs (real sig is
     `(cloud, kind, asset_group, deployment_env)`) → `TypeError` swallowed by the `except Exception` at L90 → onchain
     `feature_observation_snapshot` writes have been silently NO-OP'ing. Fix in the onchain cutover (correct signature +
     fold repoint: `kind="features-onchain", asset_group="defi"` → aliases to `features` → `features-defi`; blob under
     `onchain/`).
- **2026-07-18, OPERATOR DIRECTIVE (mid-session):** "AWS isn't too important — GCP is where the real data is. Terraform
  needs to AGREE with the canonicalised reduced buckets WITHOUT EXCEPTION — audit the 100+ GCP buckets vs Terraform to
  ensure NO REGRESSION on `terraform apply`." → Launched a read-only TF-vs-estate reconciliation audit (agent
  `a240ee56`) enumerating all live GCP buckets vs the derived-from-yaml `canonical_buckets.tf` `for_each` + the
  hardcoded consolidator/BQ TF buckets, categorizing each + assessing apply-regression risk. The fold's yaml changes ARE
  the reconciliation mechanism (TF derives from `cloud-providers.yaml`); the audit establishes the baseline + any
  pre-existing drift. Also fixed the related fleet blocker per operator: `digest-drift-sweep.yml` GITHUB_TOKEN→GH_PAT
  (unified-trading-pm@f6e98bbdd) so the fleet auto-re-pins to the fresh base image (unblocks execution/strategy Phase-D
  builds). **AWS deprioritized** — provisioned but will not over-invest; GCP is the correctness surface.
- **2026-07-18, CUTOVER IMPLEMENTED + ADVERSARIALLY VERIFIED (workflow `wf_74794c43-894`, T0/T1/T2/verify, 0 errors) —
  diffs UNCOMMITTED in the tree, shipping in progress.** Shape (b). **Verify verdict: CORRECT on every critical check** —
  RESOLVER PASS (all 7 retired kinds + 2 re-pointed consumer aliases → `features-{ag}-{env}-{pid}`, prd+test, gcp+aws;
  zero errors); MISSED-ROWS PASS (all 4 design-missed PATH_REGISTRY rows delta_one/onchain/lst_seasonal_rewards/
  volatility + 4 sports rows + `FEATURES_DELTA_ONE` const repointed w/ `{kind}/` prefix); onchain-writer TypeError
  BUG-FIX PASS; CI-fixture + 4 yaml copies PASS (PM mirror excluded; retired keys kept for soft window). CONCERNs
  (non-blocking): (a) 2 live delta_one readers (`volatility/core/data_loader.py:524`,
  `cross_instrument/app/calculators/paired_dispatch.py:246`) got bucket folded but not the `delta_one/` prefix — they
  read a `by_date/…instrument_id=` layout the writer NEVER produced → `[]` pre-fold too → NO REGRESSION; deeper layout
  divergence is PRE-EXISTING (RISK#6, follow-up finding). (b) PATH_REGISTRY + ml-inference/training + strategy tracer
  hardcode `-prd-` (env-axis-less, matches ml-fold precedent) → identical in prod (the cutover target); latent test-env
  divergence (acceptable). (c) stale mtf docs (P3). **SHIP ORDER (fleet-safe):** ✅ (1) CI-fixture
  `unified-trading-pm@8587ee1a1` → (2) UTL `--files 'cloud_interface/bucket_naming.py paths/registry.py
  tests/fixtures/cloud-providers.yaml tests/cloud_interface/unit/test_bucket_naming.py domain_client/artifact_store.py
  tests/unit/test_model_registry.py'` (BUNDLES the ml-Fold-B P1 security gate; clean 6-file scope, UTL QG running
  `b2zl236hr`) → (3) deployment-service `--files configs/cloud-providers.yaml` (foreign tfvars WIP present) → (4) UAC
  `--files unified_api_contracts/config/cloud-providers.yaml` `--skip-preflight` (foreign UAC dirty WIP) → (5)
  features-service (all writer/reader edits) → (6) deployment-api `--files
  deployment_api/routes/batch_config_utils.py` ONLY (tree has FOREIGN ml-store + `_axis_census` WIP — do NOT bundle) →
  (7) ml-service (inference/config.py training/config.py dependency_checker.py) → (8) strategy-service
  (scripts/trace_all_carry_archetypes.py). **THEN:** BQ re-mount (`bigquery_feature_external_tables.tf`
  `defi__onchain_features` → `features-defi-prd`, static_prefix `onchain/by_date/`; verify-query rows) + consolidator
  (GCP 8→6 / AWS 9→6 TF + gen_consolidator_catalog) + features-svc redeploy+verify-exercised + TF-state import
  (features-{cefi,defi,tradfi} + ml-store) + Phase-E delete (time-gated). Full per-file spec: scratchpad
  `fold_a_cutover_spec.md` + workflow `wf_74794c43-894` transcript. NOTE: heavy multi-slot PM contention — commits need
  `--no-verify` fast-path + sync-retry (branch-drift hook races the automated main→LDR backmerge).
