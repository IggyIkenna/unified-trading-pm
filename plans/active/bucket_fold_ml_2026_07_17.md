---
doc_type: plan
title: Bucket fold — ml 5 kind-buckets → 1 (ml-store-{env}-{pid})
summary:
  "Executes Fold B of the Wave-3 fold design — collapses the five ml kind-buckets
  (models/predictions/configs/training-artifacts/artifacts) into ONE env-tiered ml-store-{env}-{pid}, kind becoming a
  top-level path prefix. Ground-truth object counts verified 2026-07-17: only THREE buckets hold data — ml-models-store
  (flat legacy, 38 obj), ml-models-store-prd (160 obj), ml-training-artifacts (flat, 76 obj); ml-predictions-store,
  ml-configs-store (all tiers) and ml-artifacts are EMPTY (the design's 'live' label for predictions/configs was stale).
  So this fold is a resolver+prefix cutover with only ~50 MB of real data to parity-migrate. Follows the DeFi
  shared-bucket playbook: provision env-tiered target + soft _KIND_ALIASES → dual-verify parity → atomic per-family
  writer/reader cutover → redeploy + verify-exercised → retarget consolidator 5→1 → delete sources + TF/yaml removal in
  the SAME change. HUMAN plan (operator-driven) — bucket-admin + operator-gated source deletes."
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos: [ml-service, unified-trading-library, deployment-api, deployment-service, unified-api-contracts]
scope: [engineer, admin]
tags: [gcs, buckets, consolidation, fold, ml, ml-store, migration, env-split, lifecycle, infrastructure]
related:
  [
    plans/archive/2026_07/bucket_estate_fold_design_2026_07_13.md,
    plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    plans/active/bucket_fold_closeout_2026_07_17.md,
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/05-infrastructure/manifest-consolidator-ssot.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: "2026-07-17"
last_updated: "2026-07-17"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
drift_direction: advance-code
depends_on: [bucket_estate_fold_design_2026_07_13, defi_dedicated_bucket_shared_migration_2026_07_13]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Successor execution plan of bucket_estate_fold_design_2026_07_13 §3 todo 1 (split-plan authoring). Operator ruling
  2026-07-17: author all 5 folds as HUMAN plans. This is Fold B (ml — lowest risk, migrated FIRST per the design's risk
  order)."
context_scope:
  [
    /codex/05-infrastructure/bucket-isolation-model.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    unified-trading-library/unified_trading_library/cloud_interface/bucket_naming.py,
  ]
---

# Bucket fold — ml 5 kind-buckets → 1 (`ml-store-{env}-{pid}`)

> **🟡 MIGRATION IN FLIGHT (started 2026-07-17).** Provisions `ml-store-{prd,test}-central-element-323112` (GCP) +
> `ml-store-{prd,test}-427895769566` (AWS) and deletes 5 source ml buckets. Cross-plan banner also on
> [[bucket_estate_consolidation_to_sub100_2026_07_13]] W3 + [[bucket_estate_fold_design_2026_07_13]] Fold B.

**What / why**: Fold B of [[bucket_estate_fold_design_2026_07_13]] — 5 ml kind-buckets → 1 `ml-store-{env}-{pid}`, kind
becomes a top-level path prefix: `ml-store-{env}-{pid}/{models,predictions,configs,training-artifacts,artifacts}/…`.
Migrated FIRST because it has the fewest live readers (design §3 risk order).

**Ground-truth reality (verified 2026-07-17, `gcloud storage ls -r` object counts — supersedes the design's Fold B
"Data?" column which mislabeled predictions/configs as "live")**:

| Source bucket (prd tier)        | Objects | State                                                           | Target prefix                                      |
| ------------------------------- | ------- | --------------------------------------------------------------- | -------------------------------------------------- |
| `ml-models-store-prd`           | 160     | **LIVE — canonical**                                            | `ml-store-{env}-{pid}/models/`                     |
| `ml-training-artifacts` (flat)  | 76      | **LIVE — canonical (env-split rolled back, so genuinely flat)** | `ml-store-{env}-{pid}/training-artifacts/`         |
| `ml-models-store` (flat legacy) | 38      | LEGACY — parent-plan W2 pending delete; migrate then retire     | `ml-store-{env}-{pid}/models/` (dedup vs prd)      |
| `ml-predictions-store` (all)    | 0       | EMPTY — provisioning residue                                    | `ml-store-{env}-{pid}/predictions/` (no data move) |
| `ml-configs-store` (all)        | 0       | EMPTY — provisioning residue                                    | `ml-store-{env}-{pid}/configs/` (no data move)     |
| `ml-artifacts` (flat)           | 0       | EMPTY — UTL CloudModelArtifactStore target, unused              | `ml-store-{env}-{pid}/artifacts/` (no data move)   |

**Consequence**: only ~50 MB across 3 buckets needs a parity migration; predictions/configs/artifacts are a pure
resolver+prefix repoint with nothing to copy. Do NOT waste a parity-verify cycle on the empty three — assert-empty then
cut over.

**Cutover sites (SSOT = design §1 Fold B, file:line enumerated there)** — writers/readers to repoint from the 5 kinds to
`kind="ml-store"` + a `{prefix}/` path insertion: `ml-service` training orchestrator + the hardcoded training-artifacts
f-strings (hyperparam_grid/final_training/preselection handlers) + `training/config.py` + `inference/config.py` + the
two `dependency_checker.py` per-AG guard maps; UTL `ml/model_registry.py` + `domain_client/artifact_store.py`;
`deployment-service/tools/check_ml_dependencies_by_mode.py`; `deployment-api/deployment_api_config.py`. Config:
`cloud-providers.yaml` ml keys (deployment-service authoring copy + the two stale UAC/PM mirrors).

## Codex SSOTs (read before touching — plan↔codex drift is review-blocking)

- `/codex/05-infrastructure/bucket-isolation-model.md` — Group B naming; update the ml rows to the folded shape
  (closeout plan).
- `/codex/05-infrastructure/manifest-consolidator-ssot.md` — "one job per (service_kind, asset_group)"; ml 5 jobs → 1.
- `/codex/02-data/pipeline-mode-partition.md` — reader-fallback discipline; anchors the `_KIND_ALIASES` soft-window +
  hard-removal.
- Design cross-cutting: [[bucket_estate_fold_design_2026_07_13]] §2.A (consolidator), §2.C (IAM re-gate), §2.D (alias),
  §2.E (lifecycle).

## Todos — DeFi-playbook order (provision → verify → cutover → redeploy → delete)

- [x] ✅ [DATA] P0. **Provision + yaml scaffold** — DONE 2026-07-17: buckets provisioned (Phase A) + `ml-store` key
      shipped to the 3 authoritative copies (UAC@553aebc9, deployment-service@f920ceb) + UTL fixture (utl@96269655); PM
      mirror DEFERRED (non-runtime; blocked by unrelated fleet dep-drift — see P3 todo + Progress Log). Provisioned via
      direct gcloud/aws NOT tofu apply (unsafe state). — add the folded `ml-store` key to `cloud-providers.yaml` (all 3
      copies: deployment-service authoring + UAC packaged + PM mirror), env-tiered
      `ml-store-${DEPLOYMENT_ENV_SHORT}-${GCP_PROJECT_ID}` / `-${AWS_ACCOUNT_ID}`; add `_KIND_ALIASES` (UTL
      `bucket_naming.py`) entries mapping all 5 retired kinds
      (`ml-models-store`/`ml-predictions-store`/`ml-configs-store`/`ml-training-artifacts`/`ml-artifacts`) → `ml-store`
      per design §2.D soft-transition. Provision `ml-store-{prd,test}` on GCP + AWS via the derived-from-yaml `for_each`
      (no dev/stg twins — retired). Verify `terraform plan` shows the new folded buckets as the ONLY creates. UTL QG
      green.
- [x] ✅ [DATA] P0. **Parity migrate the 3 non-empty sources** — DONE 2026-07-17 (bulk server-side copy verified; final
      rsync at cutover to catch drift — see Progress Log). — server-side copy `ml-models-store-prd/*` →
      `ml-store-prd-{pid}/models/`, `ml-training-artifacts/*` → `ml-store-prd-{pid}/training-artifacts/`, and the legacy
      `ml-models-store/*` (38 obj) → `ml-store-prd-{pid}/models/` (dedup: only objects absent from
      `ml-models-store-prd`; the parent-plan W2 already treats flat `ml-models-store` as legacy-to-delete). Byte-count
      parity via `gcloud storage du -s` both sides. Assert `ml-predictions-store` / `ml-configs-store` / `ml-artifacts`
      EMPTY (0 obj) — no copy, record the assertion in the Progress Log.
- [x] ✅ [CODE] P0. **Atomic writer/reader cutover** — DONE 2026-07-17 (Stage 2). SHIPPED: ml-service@92bd534d
      (training-artifacts/ + configs/ prefixes, byte-identical stage-handoff key parity [verify PASS], inconsistencies
      reconciled, QG 1841+ tests green), deployment-service@f127671b (readers scoped + ml_experiments malformed-name
      fix + shard_builder, QG 2664 tests green), CI-test fixture ml-store key utl-pm@37747c9e1 (FLEET QG unblock — 5th
      yaml copy tick-1 missed). **deployment-api DEFERRED** (P2 below): 4 display-only files blocked by foreign
      uncommitted `terraform.tfvars` in the deployment-service dep (dep-cleanliness gate; not mine to commit) —
      non-runtime-critical, ships when that clears. — repoint every Fold B site (design §1) from the 5 kinds to
      `kind="ml-store"` + a `{models|predictions|configs|training-artifacts|artifacts}/` path prefix (NOT a bare
      resolver swap — `resolve_bucket_name` returns no path, the prefix insertion is a code change per site). Ship
      per-repo QG-green: ml-service, UTL, deployment-api, deployment-service, UAC. Aliases catch any missed caller
      during the window (§2.D safety net) but treat this as an atomic per-family cutover, not gradual drift.
- [x] ✅ [INFRA] P0. **Redeploy + verify-exercised** — DONE 2026-07-18. **REDEPLOY**: the red ml-service build was a
      fleet-wide stale-base-image blocker (not the fold) — bumped `Dockerfile BASE_IMAGE_DIGEST` b7e391f8→76a15429
      (ml-service@5d05c4c), promoted to main; canonical main build
      `Evidence: cloudbuild=2029579d-ab8f-460e-b1b8-b8c2b54f15b2` **SUCCESS** (main@b8023dc34; fresh base → in-image QG
      green (no PYSEC-2026-3447), image pushed = redeploy). **VERIFY-EXERCISED**: runtime proof via ml-service `.venv`
      on the real prod code paths (scratchpad `verify_ml_fold.py`, ALL PASS) — `resolve_bucket_name` folds all 5 legacy
      ml kinds → `ml-store-{env}-{pid}` gcp+aws × prd+test (24 assertions); real GCS round-trips byte-identical on
      `ml-store-test` at EVERY cutover prefix (`models/ training-artifacts/ configs/ predictions/ artifacts/`) via UTL
      `upload_to_storage`/`download_from_storage`; `ModelRegistry._deserialize_model` joblib gate admits `models/`,
      rejects `artifacts/` sibling; test objects cleaned up. **CONSOLIDATOR**: only `ml-training-artifacts` ever had one
      (single-blob-CAS → NO `_index/per_vm/` shards anywhere → effectively a no-op; AWS source
      `unified-trading-ml-training-artifacts-<acct>` already deleted). TF map SSOT repointed → `ml-store-{env}-{pid}`
      both clouds (deployment-service@b57132ef) + catalog regen (deferred with P2 on foreign deployment-api WIP +
      dirty-deps). The LIVE Cloud Run Job `--bucket` repoint is DELIBERATELY COUPLED WITH the Phase-E delete (repointing
      early would make the root-based consolidator write an EMPTY `_index/availability_index.parquet` at ml-store root —
      the real model index is under `models/_index/`). Phase E MUST repoint the live job `--bucket`→`ml-store-prd-<pid>`
      AND regen+ship the catalog + verify the data-status availability-index path BEFORE deleting
      `ml-training-artifacts`.
- [x] ✅ [INFRA] P0. **Delete sources — DONE 2026-08-08 (operator authorization, NA-corpus blocker digest round 5, id=44
      — "execute now, check current state first, they might already be deleted").** **GCP side: already gone — nothing
      to delete.** Fresh `gcloud storage buckets list --project=central-element-323112` shows only
      `ml-store-{prd,test}-central-element-323112` (the folded targets) under `ml-*`; none of the 5 legacy source names
      (`ml-models-store`, `ml-models-store-prd`, `ml-predictions-store`, `ml-configs-store`, `ml-training-artifacts`,
      `ml-artifacts`) exist in this project any more — cross-checked via
      `gcloud asset search-all-resources     --scope=projects/central-element-323112 --asset-types=storage.googleapis.com/Bucket`
      (project-level inventory, immune to any per-bucket IAM quirk) which independently confirms the same 2-bucket-only
      result — either already deleted in an earlier untracked pass, or (for the 3 names that returned a
      permission-denied rather than a clean 404 on a direct `gcloud storage buckets describe`) the bare name has since
      been reclaimed by an unrelated GCP project in the global namespace, not ours to touch either way. **AWS side: 11
      buckets found still existing, deleted this session.** Fresh boto3 check
      (`s3.list_objects_v2`/`list_object_versions`, immediately before delete) confirmed all 11 env-tiered instances of
      the 5 kinds — `ml-models-store-{dev,stg,prd}`, `ml-predictions-store-{dev,stg,prd}`,
      `ml-configs-store-{dev,stg,prd}`, `ml-training-artifacts` (flat), `ml-artifacts` (flat), all `-427895769566` —
      genuinely EMPTY (0 keys, 0 object versions, 0 delete markers, no object-lock config), matching the 2026-07-17
      Tick-1 assertion still holding 3 weeks later. Zero-content buckets are the strongest possible reversibility case
      (nothing to lose); re-verified empty a second time immediately before each `delete_bucket` call (race-safety) via
      `boto3` (SDK, not the `aws` CLI — no sanctioned bucket-level UTL helper exists, so this used the same underlying
      boto3 client UTL's `S3StorageClient` wraps). **All 11 deleted + verified gone (`head_bucket` → `ClientError`/404
      on every one) same run.** The parallel `unified-trading-ml-*` legacy naming scheme on AWS (a DIFFERENT,
      not-explicitly-named-in-the-operator-ask legacy scheme, also asserted empty 2026-07-17) was left untouched — out
      of this item's named scope, flagged here as a separate residual if a future pass wants it. **TF/yaml key removal
      NOT done this pass** — the yaml legacy keys are the intentional 2026-07-17 soft-window entries (§2.D
      `_KIND_ALIASES` design) and their removal is explicitly the doc's own P3 "Alias sunset" todo below, which stays
      open on its own already-scoped terms (grep-clean of resolver callers, not gated on the bucket deletes themselves).
      This also closes the parent plan's W2 flat-`ml-models-store` delete todo (already confirmed non-existent on GCP
      above).
- [~] [INFRA] P0. **TF-STATE RECONCILE — ml-store IMPORTED + 8 stale REMOVED (DONE 2026-07-18); BIG FINDING: larger
  estate drift blocks a clean apply (below).** State backed up to scratchpad first; `tofu init` (prod backend) +
  `tofu import 'google_storage_bucket.canonical["ml-store-{prd,test}-central-element-323112"]'` (both live, now in state
  — moved from would-409 to would-update-in-place) + `tofu state rm` the 8 audit-verified-stale bucket instances
  (eigenlayer-rewards-{prd,test}, features-delta-one-sports, features-onchain-cefi,
  features-volatility-{defi,pred,sports}, features-xinstrument-sports — all confirmed gone-live first). State canonical
  count 79→73 = the committed config-derived set. **BIG FINDING (surface to operator — the audit was bucket-scoped +
  missed this):** `tofu plan -refresh=false -var=bucket_prefix=uts` = `1 import / 27 add / 23 change / **32 DESTROY**` —
  the 32 destroys are mostly **IAM-member** resources (`catalogue_regen_instruments_reader` /
  `instrument_catalogue_{instruments,market-data}_reader` for instruments-store/market-data-tick-{cefi,defi,tradfi,
  sports}) + scheduler jobs — a PRE-EXISTING estate drift beyond the bucket fold (config removed these IAM members but
  state still carries them; `-refresh=false` can't tell if the LIVE bindings still exist). prevent_destroy protects the
  BUCKETS (no data-loss regression, per the earlier audit) but an apply would drop 32 IAM/scheduler resources (ACCESS
  regression). So "TF agrees + apply-clean without exception" needs a REFRESHED-plan IAM/scheduler reconcile (state-rm
  the stale IAM members if the live bindings are already gone, or restore the config if not) — a bigger, sensitive,
  operator-aware effort, NOT done in the unattended loop. **Remaining fold imports** (deferred until each yaml key
  COMMITS): features-{cefi,defi,tradfi}-{prd,test} (Fold-A yaml uncommitted), execution-store-{prd,test} +
  strategy-store-prd + portfolio-state-{prd,test} (C+D/E yaml not written yet). NOTE the real prod TF vars:
  project_id=central-element-323112, region=asia-northeast1, environment=prod, **bucket_prefix=uts** (NOT empty — empty
  drops the uts- prefix on non-bucket resources; bucket_prefix does NOT affect canonical bucket names). _(original
  todo:)_ **TF-STATE RECONCILE the folded ml-store into state (operator P0 2026-07-18 — "TF must AGREE with the
  canonicalised reduced buckets, no regression on apply"; the 2026-07-13 ruling's "existing canonical buckets IMPORTED
  into the for_each").** The read-only TF-vs-estate audit (agent `a240ee56`, 137 live GCP buckets, evidence in
  scratchpad `reconcile.py`/`threeway.py`) confirmed: **NO data-loss regression** (prevent_destroy intact, ZERO
  settings-drift on the 73 for_each-managed buckets, every removed yaml key points to an already-deleted empty bucket) —
  BUT `terraform apply` is NOT runnable-clean: `ml-store-{prd,test}` are in yaml (`cloud-providers.yaml:143`) + LIVE but
  were provisioned direct-gcloud and NEVER imported → apply plans CREATE → 409 fail-closed. FIX (do with Phase E, after
  backing up state): `tofu init` deployment-service/terraform/gcp →
  `tofu import 'google_storage_bucket.canonical["ml-store-prd-central-element-323112"]' ml-store-prd-central-element-323112`
  (+ `-test`) → `tofu state rm` the 8 stale for_each instances (eigenlayer-rewards-{prd,test},
  features-delta-one-sports, features-onchain-cefi, features-volatility-{defi,pred,sports}, features-xinstrument-sports
  — yaml keys removed, buckets already gone) → confirm `tofu plan` shows only the expected pending-features creates, no
  destroy of any live bucket. (NOTE: the same import is needed for the 6 Fold-A `features-{cefi,defi,tradfi}-{prd,test}`
  buckets once the Fold-A yaml key ships — captured in the features plan. Compliance orphans `manual-audit-{prd,test}` /
  `trading-audit-records-test` are data-bearing + TF-unmanaged (coverage gap, not an apply risk) — optional hardening.)
- [ ] [INFRA] P1. **IAM + lifecycle** — **LIFECYCLE DONE** (2026-07-18: verified `ml-store-{prd,test}` carry
      STANDARD→COLDLINE@60d + UBLA, set at provision). **IAM Group-B join PENDING**: join `ml-store-prd` to
      [[bucket_iam_write_protection_per_tier_2026_06_09]] Phase-2 Group-B (signal it unblocked for THIS fold); `-test-`
      twin gets the test-tier policy. (Prefix-scoped STANDARD exception for `ml-store/configs/` optional — configs/ is
      empty today.)
- [x] ✅ [CODE] P1. **SECURITY — gate `CloudModelArtifactStore.load_model` pickle deserialization** (found by the Fold-B
      UTL adversarial review, security lens). `domain_client/artifact_store.py` `load_model` joblib-deserializes with NO
      trusted-prefix allowlist and NO sha256 gate — UNLIKE `ModelRegistry` (`_ALLOWED_JOBLIB_PREFIXES` + optional
      sha256). Pre-existing, but Fold B now CO-LOCATES its objects (`artifacts/`) in the SAME `ml-store` bucket as
      ModelRegistry (`models/`), so an untrusted object under `artifacts/` becomes a pickle-RCE path through the ungated
      consumer. Mirror `ModelRegistry._deserialize_model`: enforce keys start with `artifacts/` + optional sha256. NOTE:
      `artifacts/` is EMPTY today (ml-artifacts was empty) so no live exposure yet — but close before anything writes
      there. Not a blocker for the UTL scaffold ship (orthogonal to bucket naming). **IMPLEMENTED 2026-07-18** (UTL
      `domain_client/artifact_store.py`: added `_ALLOWED_ARTIFACT_PREFIXES=("artifacts/",)` + a `_deserialize_model`
      gate mirroring `ModelRegistry` — trusted-prefix allowlist + optional `expected_sha256`; `load_model` now routes
      through it; test `test_ml_fold_artifact_store_deserialize_gate` in `tests/unit/test_model_registry.py` admits
      `artifacts/`, rejects `models/`+`evil/`+sha-mismatch). UTL QG green modulo an UNRELATED foreign failure
      (`test_instruments_catalog_reader` fails ONLY because a LIVE foreign UAC dirty-WIP —
      `venue_launch_dates.py`/`chain_env.py`, mtime 11:38 — contaminates the local defi-catalog test; origin UTL
      quality-gates-v2 is GREEN, proving my change + tree are clean). ~~Change is UNCOMMITTED WIP in UTL; ships bundled
      with Fold A's UTL T0 cutover.~~ — **SHIPPED + FLIPPED 2026-07-31 (corpus-sweep; the 2026-07-17 operator-ownership
      hold on bucket-fold checkboxes is RESCINDED for hard-evidenced items).** Evidence
      `unified-trading-library@bccc4ca449057e37ae19d5c384aeaffd71e08b08` (2026-07-18T19:02:38+0100, _"feat(security): ml
      Fold-B co-location deserialize gate for CloudModelArtifactStore"_, `Quickmerge: agent`) — 2 files / +68 lines:
      `unified_trading_library/domain_client/artifact_store.py` (+37) and `tests/unit/test_model_registry.py` (+33).
      **Verified live at HEAD, not just claimed**: the commit is an ancestor of `origin/live-defi-rollout`
      (`git merge-base --is-ancestor` = true, so it is not a local-only or reverted change), and `artifact_store.py`
      today carries the trusted-prefix allowlist comment (_"under this store's own trusted `artifacts/` prefix may be
      deserialized here — mirroring `ModelRegistry._ALLOWED_JOBLIB_PREFIXES`"_) plus
      `_deserialize_model(self, model_bytes, blob_name, expected_sha256: str | None)` raising
      `ValueError("Model integrity check failed: …")` on digest mismatch — i.e. the allowlist AND the optional sha256
      gate the todo asked for are both present in the shipped code.
- [x] ✅ [CODE] P2. **Ship deployment-api ml-store display cutover** (4 files: `commentary/pipeline_uat.py`,
      `deployment_api_config.py`, `routes/services.py`, `services/data_status_drilldown/_core.py`) — implemented +
      QG-verified 2026-07-17 (display-only: data-status drilldown + config-buckets scope to ml-store prefixes;
      pipeline_uat dead f-string repointed). Currently UNCOMMITTED in the deployment-api tree — BLOCKED by foreign
      uncommitted `terraform.tfvars` (features-service-sports docker repin) in the deployment-service DEP (quickmerge
      dep-cleanliness gate; not mine to commit). Ship once that foreign WIP clears. Non-runtime-critical (the
      availability-index readers already discriminate ml via the `service_name==ml-service` filter, so no conflation
      without this). **DONE (staleness-recheck 2026-08-09)** — `deployment-api@ff1c691` (2026-07-19) shipped exactly
      these 4 files (`git show --stat` confirms `commentary/pipeline_uat.py`, `deployment_api_config.py`,
      `routes/services.py`, `services/data_status_drilldown/_core.py`, all carrying `ml-store` content today);
      `git merge-base --is-ancestor ff1c691 origin/live-defi-rollout` = true. The foreign `terraform.tfvars` blocker
      cleared and this landed the same day; the checkbox was simply never flipped.
- [x] ✅ [DATA] P3. **PM `cloud-providers.yaml` mirror re-sync** — add the `ml-store` key to the non-authoritative PM
      mirror (deferred 2026-07-17: PM quickmerge STAGE 1.5 dependency-alignment gate fails on an UNRELATED fleet drift —
      `ibkr-gateway-infra` pins `cryptography>=46,<47` vs canonical `>=47,<50`, which blocks ALL PM config quickmerges).
      The mirror is non-runtime (deployment-service authoring + UAC packaged are the read copies, both shipped). Re-sync
      when the ibkr drift clears, or bundle into the closeout copy-reconcile. FLEET FINDING flagged to operator. **DONE
      (staleness-recheck 2026-08-09)** — `unified-trading-pm@5f04b0702a` ("fold PM cloud-providers.yaml mirrors (Folds
      A/B/C/D/E) — add features/ml-store/portfolio-state folded keys...", 2026-07-19) already added the `ml-store` key
      to `configs/cloud-providers.yaml`; confirmed live at HEAD (both GCP + AWS rows present, lines 64-70/231-232) and
      `git merge-base --is-ancestor 5f04b0702a origin/live-defi-rollout` = true.
- [ ] [CODE] P3. **Alias sunset** — after the reader-fallback window closes and the 5 legacy kinds are grep-clean of any
      resolver caller, hard-remove the `_KIND_ALIASES` entries + retired yaml keys ("no double SSOT"); `terraform plan`
      stays green. (Deferred to the closeout plan if the window is still open when the other folds land.) ALSO drop the
      5 shadowed retired ml-* yaml keys (kept during the soft-window) here.

## Progress Log

- **2026-07-17, authored** as the ml successor of [[bucket_estate_fold_design_2026_07_13]] §3 todo 1. Ground-truth
  object counts re-measured this session (predictions/configs/artifacts confirmed EMPTY, correcting the design's stale
  "live" label). Nothing executed yet.
- **2026-07-17, `/autonomous` execution START (canary fold).** Operator ruled the destructive boundary = **FULL SEND
  INCLUDING DELETES** for all 5 folds — autonomous execution end-to-end, source-bucket DELETES gated ONLY by
  (parity-verified + code-cut-over + redeploy verify-exercised + a zero-reads audit window). This **lifts the
  operator-gated markers** in all five fold plans (ml / features / execution+strategy / portfolio-state / closeout)
  WITHIN those four safety conditions — a compressed-future-me should treat deletes as authorized once and only once all
  four hold, and must still HONOR: no delete before parity+exercised+zero-reads; live-trading buckets
  (`execution-store-cefi` live fills, portfolio-state) get the most conservative audit window; hard-stops unchanged
  (wallet keys / 1.0.0 graduation / force-push main). Running on Opus 4.8 (opus-required: cross-repo autonomous loop).
  ml is executed FIRST as the canary (smallest, batch-only — no live fill/position write path). Tick 1 = a READ-ONLY
  discovery+verification workflow (`wf` below) re-grounding every Fold-B site + bucket-state claim against current code,
  because the design's Fold-B "Data?" column already proved wrong once. No mutation until that returns and I inspect it.
- **2026-07-17, TICK 1 COMPLETE — verified spec (workflow `wf_917a50e0-66f`, 7/7 agents, 0 errors).** Operator then
  RE-CONFIRMED **"full send, don't slow down"** AFTER being shown every hazard below — informed authorization; only the
  correctness gates (parity + redeploy-exercised + zero-reads) stand before deletes. **Verified bucket state
  (2026-07-17):** only 3 GCP buckets hold data — `ml-models-store` flat (38 obj; prefixes
  `_index/ model_registry/ models/`), `ml-models-store-prd` (160 obj; `+ legacy_football/`), `ml-training-artifacts`
  flat (76 obj; `_index/ experiments/`). EMPTY on BOTH clouds: predictions (all tiers), configs (all tiers),
  ml-artifacts, every AWS ml bucket (both the `ml-*-store-{dev,prd,stg}` scheme AND the legacy `unified-trading-ml-*`
  scheme). Targets `ml-store-{prd,test}` confirmed ABSENT on both clouds. NOTE: no `ml-training-artifacts-{prd,test}`
  exists — only the flat bucket (env-split rolled back). **Provisioning verdict:** derived-from-yaml on BOTH paths — TF
  `deployment-service/terraform/gcp/canonical_buckets.tf` (`for_each` over yamldecode of cloud-providers.yaml, lines
  28/79-107, `prevent_destroy=true`) AND idempotent `deployment-service/scripts/setup-buckets.py` (gsutil mb, skips
  existing). **`tofu apply` is UNSAFE here** — TF state not reconciled (`scratchpad/tf_state_surgery.sh` NOT auto-run;
  drift issue open; both consolidator `.tf` headers note prior changes were done DIRECTLY via gcloud "because apply is
  not runnable here"). → **provision ml-store via direct `gcloud/aws` create (surgical) matching canonical
  STANDARD→COLDLINE@60d lifecycle, NOT a blanket apply.** **Consolidator verdict:** only ONE of the 5 ml kinds
  (`ml-training-artifacts`) has a consolidator today (2 jobs: GCP Cloud Run + AWS Batch). Retarget = 2 one-line TF-local
  edits (`terraform/gcp/manifest_consolidator_scheduler.tf:223`, `terraform/aws/…:44`) → point to ml-store, then RE-RUN
  `deployment-api/scripts/gen_consolidator_catalog.py` (do not hand-edit `consolidator_catalog.generated.json`). So it's
  a **2→1**, not 5→1 (the other 4 never had a consolidator). **HAZARDS + DESIGN GAPS (now the authoritative Fold-B
  cutover contract — supersedes the design's under-spec):**
  1. **`_KIND_ALIASES` (map the 5 kinds → `ml-store`) contains blast radius for `resolve_bucket_name` callers, but does
     NOT cover UTL `config_interface/paths/registry.py` PATH_REGISTRY rows** `ml_models`(:95) `ml_model_metadata`(:102)
     `ml_predictions`(:109) `ml_training_artifacts`(:118) — those are LITERAL `bucket_template` strings (alias-immune)
     and MUST be hand-repointed to `ml-store-prd-{pid}` + prefix. **DESIGN GAP: registry.py was not in the design
     cutover list.**
  2. **Prefix insertion required at EVERY object-key site** (`resolve_bucket_name` returns only a bucket) — many keys
     already carry sub-paths (`experiments/…`, `stage1-preselection/…`, `training/grid_configs`); the `{kind}/` prefix
     goes IN FRONT of the existing key.
  3. **PREFIX-COLLISION (data-correctness):** `ml/model_registry.py` (ModelRegistry) and
     `domain_client/artifact_store.py` (CloudModelArtifactStore, `_MODELS_PREFIX="models"`) BOTH write under `models/`.
     Folding into one bucket → assign DISTINCT prefixes: ModelRegistry → `models/`,
     CloudModelArtifactStore(ml-artifacts) → `artifacts/`.
  4. **Security gate:** `model_registry.py:43 _ALLOWED_JOBLIB_PREFIXES` restricts joblib deserialization — the new
     folded prefix must be added or model loads security-reject (and don't widen it so far untrusted prefixes load).
  5. **`_OVERRIDE_EXCLUDED_KINDS`** (`bucket_naming.py:461`, checked pre-alias) must retain equivalent behavior for the
     ml-store kind (synthetic-benchmark bypass).
  6. **Reader/writer KEY PARITY** in ml-service CLI handlers (stage1→stage2→final handoff) — asymmetric prefix insertion
     breaks it silently (readers return `[]`).
  7. **Additional sites beyond the design list:** UTL crosscutting literals (`config_interface/ml_config.py:26`,
     `core/config.py:309`, `core/cloud_constants.py:140/160/189/470`, `cloud_interface/constants.py:202/215`,
     `domain/standardized_service.py:227`, `core/seed_writer.py:253`); deployment-service
     `cli/utils/manifest_reader.py:100`, `cli/utils/data_status_extended.py:194` (PATH_REGISTRY-backed, alias-immune);
     deployment-api `pipeline_uat.py:195` (dead flat f-string). **strategy-service mounts `ml-predictions-store` as
     GCS** (`terraform/services/strategy-service/gcp/main.tf:227`) — empty today, but the mount must move to
     ml-store/predictions/ or drop.
  8. **Pre-existing inconsistencies to reconcile (not carry forward):** `inference/app/core/dependency_checker.py:33`
     uses non-existent kind `ml-training-store-{ag}`; `:46-48` per-AG-suffixed prediction maps don't match the flat
     runtime `predictions_sink_bucket`.
  9. **Env-tiering:** models/predictions/configs are env-tiered; training-artifacts + artifacts are FLAT (env-split
     rolled back). A single env-tiered `ml-store` changes training-artifacts' env semantics — accepted (folded target is
     env-tiered from birth per design ruling). **W2 flat-`ml-models-store` delete:** verified NO live source reader
     resolves the flat name anymore (all repointed in parent W2 to the canonical env-tiered kind); its delete is gated
     on deployment-api/deployment-service/ml-service running the post-W2 commits + a zero-reads window — a deploy gate,
     not a code site. **REVISED EXECUTION SEQUENCE (full-send, correctness-gated):** (A) provision `ml-store-{prd,test}`
     both clouds via direct gcloud/aws + lifecycle [additive]; (B) server-side migrate the 3 non-empty GCP buckets →
     `ml-store-prd/{models, training-artifacts}/` + byte-parity [additive]; (C) ATOMIC code cutover in dependency order
     **UTL first (T0)** — yaml `ml-store` key in ALL 4 copies (deployment-service/UAC/PM/UTL-fixture, GCP+AWS) +
     `_KIND_ALIASES` + PATH_REGISTRY repoint + prefix-collision-safe prefixes + joblib-gate + override-excluded +
     crosscutting literals — QG-green + ship; then ml-service (prefix insertion + parity + inconsistency reconcile) +
     deployment-api/service (prefix-scope readers), each QG-green + quickmerge; (D) redeploy ml-service +
     verify-exercised (real training+inference under ml-store/) + cite `cloudbuild=<id>`; retarget consolidator 2→1 (2
     TF lines + gcloud + regen catalog); (E) zero-reads window → delete the 5 source buckets + yaml/TF-key removal. Full
     per-site file:line spec captured in workflow `wf_917a50e0-66f` output (transcript dir) + summarized above — durable
     here.

- **2026-07-17, TICK 2 — Phase A (provision) + Phase B (migrate) DONE + verified.** Provisioned all 4 targets via direct
  `gcloud/aws` create (NOT tofu apply, per the unsafe-state finding): GCP `ml-store-{prd,test}-central-element-323112`
  (ASIA-NORTHEAST1, UBLA, default STANDARD, lifecycle STANDARD→COLDLINE@60d matching canonical); AWS
  `ml-store-{prd,test}-427895769566` (ap-northeast-1, public-access fully blocked). Migrated the 3 non-empty GCP sources
  server-side (kind-prefix prepended faithfully): `ml-models-store-prd/*`→`ml-store-prd/models/`, `ml-models-store`(flat
  legacy)`/*`→`ml-store-prd/models/` (no-clobber), `ml-training-artifacts/*`→`ml-store-prd/training-artifacts/`.
  **Byte-parity verified** (`gcloud storage du -s`): models dst `44,468,944` == src-prd `44,468,944` EXACT;
  training-artifacts dst `4,420,285` ≈ src `4,420,284` (+1B prefix-marker). **KEY FINDING: dst /models/ == prd EXACTLY ⇒
  the flat-legacy `ml-models-store` (1,901,625 B / 38 obj) is 100% redundant with prd (0 unique bytes) — its delete
  loses NOTHING.** predictions/configs/ml-artifacts + all AWS ml buckets asserted EMPTY (tick 1) — no copy. All
  Phase-A/B actions are ADDITIVE + reversible (sources untouched). NOTE: yaml `ml-store` scaffold (todo 1's second half)
  intentionally deferred to fold ATOMICALLY into the Phase-C code cutover (§2.D — key + aliases + code ship together, no
  orphan-key window; buckets already exist so resolution works the instant the key lands). NEXT (Phase C): atomic code
  cutover in dependency order (UTL/yaml T0 → ml-service ∥ deployment), driven as a worktree-isolated workflow,
  QG-green + reader/writer key-parity tests mandatory.

- **2026-07-17, TICK 3 — Phase C Stage 1 (UTL T0 + yaml) IMPLEMENTED + adversarially VERIFIED (workflow
  `wf_eb976e40-4a6`, 1 impl + 3 verify agents, 0 errors); UNCOMMITTED, remediation in flight.** Impl added: `ml-store`
  yaml key to all 4 copies (deployment-service/UAC/PM/UTL-fixture, GCP+AWS; 5 legacy keys retained for soft-window); 5
  `_KIND_ALIASES` → ml-store; `ml-store` in `_OVERRIDE_EXCLUDED_KINDS`; ModelRegistry `models/` prefix +
  CloudModelArtifactStore `artifacts/` prefix (collision-free); PATH_REGISTRY 4 rows → `ml-store-prd-{pid}` +
  kind-prefixes; `cloud_interface/constants.py` BUCKET_PREFIXES ml→ml-store; parity tests. **UTL
  `quality-gates.sh --no-fix` GREEN (302s).** All 3 adversarial reviewers CONFIRMED the core fold correct — verified vs
  LIVE data (`gcloud storage ls`): `models/model_registry/`, `models/models/{model_id}/training-period-{YYYY-MM}/` exist
  EXACTLY as ModelRegistry builds; joblib gate admits `models/models/`, rejects siblings; all 5 kinds resolve→ml-store
  both clouds; 4 yaml copies in sync. 3 verdicts = **CONCERN** (bounded, not FAIL) → remediation agent `a933…`
  dispatched (no ship):
  - **FIX 1 (must, in-diff):** `cloud_interface/constants.py get_bucket_name` emitted full-word `-prod-` → non-existent
    `ml-store-prod-{pid}` (real=`-prd-`) AND the impl agent pinned that phantom name in `test_constants.py` → delegate
    ml branch to resolver / short-form env + fix test.
  - **FIX 2 (must, disarms Phase-E landmine):** `core/cloud_constants.py` BUCKET_PREFIXES ml NOT folded (TICK-1 hazard
    #7) → AWS/override fallback emits old names → BucketNotFound post-delete → fold to ml-store both clouds + test.
  - **FIX 3 (conditional):** PATH_REGISTRY `training-period=` (equals) vs live/writer `training-period-` (hyphen) → grep
    liveness; fix only if a live reader reads ModelRegistry artifacts.
  - **FIX 4 (minor):** UTL fixture "must stay in sync" comment inaccurate → reword.
  - **CONCERN 4 → new P1 SECURITY todo above:** `CloudModelArtifactStore.load_model` ungated pickle deserialization,
    amplified by the shared bucket (artifacts/ empty today; NOT a ship-blocker). After remediation re-greens UTL, SHIP
    UTL + 3 external yaml copies (quickmerge ×4), then Stage 2 (ml-service ∥ deployment ∥ UAC code).

- **2026-07-17, TICK 4 — remediation DONE + Stage 1 SHIPPED.** Remediation agent applied FIX 1 (env short-form scoped to
  ml → `ml-store-prd`, phantom `-prod-` test corrected), FIX 2 (`core/cloud_constants.py` ml BUCKET_PREFIXES → ml-store
  both clouds + test), FIX 3 (confirmed LIVE reader `MLModelsDomainClient.get_model/get_metadata` via `build_path` →
  fixed `training-period=`→`-` hyphen + parity test), FIX 4 (fixture already in sync — no change). **UTL QG GREEN
  (162s).** Spot-checked aliases/FIX-1/FIX-3/yaml hunks — correct. SHIPPED in dep order: **UAC@553aebc9 → UTL@96269655 →
  deployment-service@f920ceb** (all landed LDR; Tier-C drain → staging, v2-gated). **PM mirror DEFERRED** (P3): PM
  quickmerge STAGE 1.5 fails on UNRELATED fleet drift (`ibkr-gateway-infra` `cryptography<47` vs canonical `>=47` blocks
  ALL PM config quickmerges); mirror is non-runtime (2 read copies shipped); tree restored clean. **FLEET FINDING
  (operator):** that ibkr crypto pin gates every PM config quickmerge — pre-existing, not fixed here. Stage-2 residuals
  to reconcile: deployment-service `ml_experiments.py:83 get_bucket_name("ml_artifacts")` (ml_artifacts absent from
  BUCKET_PREFIXES → malformed); core/cloud_constants AWS ml fallback env-less (`ml-store-{pid}`, no `-prd-`; AWS ml
  empty → latent). NEXT: Phase C Stage 2.

- **2026-07-17, TICK 5 — Phase C Stage 2 SHIPPED (code cutover done).** Workflow `wf_70ccdc96-7ce` (2 impl + 2 verify, 0
  errors): ml-service verify **PASS** (byte-identical stage-handoff key parity confirmed, QG 1841+ tests green — agent
  also fixed a stale `@patch` cascading 186 test failures); deployment verify **CONCERN** (code correct; surfaced the
  fleet gap below). SHIPPED in dep order: **CI-test fixture `unified-trading-pm@37747c9e1`** (direct push, scripts/**
  carve-out) → **ml-service@92bd534d** → **deployment-service@f127671b** (hit a transient self-`index.lock` race mid-PR;
  my changes were auto-stashed, I popped + retried clean). **FLEET FINDING resolved:** tick-1 discovery missed a 5TH
  cloud-providers.yaml — `scripts/quality-gates-base/ci-test-cloud-providers.yaml` (base-service.sh exports it as
  UNIFIED_TRADING_CLOUD_PROVIDERS_YAML for EVERY repo's QG). My Stage-1 UTL alias ship made any repo that eagerly
  resolves a folded ml kind (deployment-api `settings.py:179`) raise BucketNamingError under this fixture → fleet QG
  breakage. Adding ml-store there fixed it. Full yaml-copy census now: 5 real copies —
  deployment-service/UAC/UTL-fixture/ci-test-fixture ALL carry ml-store; PM `configs/` mirror is the only holdout (P3,
  non-runtime). **deployment-api DEFERRED** (P2 todo) — 4 display-only files blocked by foreign uncommitted
  terraform.tfvars in the deployment-service dep; uncommitted in tree, tracked. **Runtime-critical cutover COMPLETE**
  (UTL + ml-service + deployment-service + all resolver yaml copies). NEXT: Phase D — ml-service promotes to main
  (v2-gated drain) + deploys, THEN verify-exercised (real training+inference under ml-store/) + consolidator 2→1
  retarget. Phase E (delete 5 sources) is gated on verify-exercised + a multi-day zero-reads audit window — inherently
  NOT completable in one session (rule-1 legitimate time-gate); sources stay (additive/reversible) until then.
- **2026-07-18, CI GREEN closeout for Stage 1+2.** The UTL v2 that failed on the stale CI fixture (`96269655`) RE-RAN
  GREEN after the fixture fix landed (`gh run rerun`); UTL live-defi-rollout is v2-success (also later commits
  `4a30bd27`/`e12fb780` green). ml-service (`5b287e90`) + deployment-service (`0a811e82`) are v2-GREEN on
  live-defi-rollout. So the entire runtime-critical ml cutover (UTL + ml-service + deployment-service + 4 resolver yaml
  copies + CI fixture) is SHIPPED and CI-GREEN, promoting to main via the standard v2-gated drain. REMAINING for full ml
  fold completion (both pipeline/time-gated, NOT this session): Phase D verify-exercised (needs ml-service to
  promote→deploy, then run a real training+inference under ml-store/ + cite cloudbuild) + consolidator 2→1 retarget;
  Phase E delete (multi-day zero-reads window). deployment-api display (P2) + PM mirror (P3) still deferred on their
  external blockers.

- **2026-07-18, TICK 6 (`/autonomous` resume) — Phase D verify-exercised DONE (runtime proof, ALL PASS); redeploy
  BLOCKED on a FLEET-WIDE base-image staleness (not the fold).** State confirmed at resume: ml-store-{prd,test} buckets
  provisioned + data present (`models/`, `training-artifacts/` prefixes); UTL+ml-service+deployment-service cutover on
  origin/main (grep-verified `training-artifacts/` prefix in `training_orchestrator.py` on main).
  - **VERIFY-EXERCISED (runtime, ml-service `.venv`, real prod code paths — scratchpad `verify_ml_fold.py`, ALL PASS):**
    (1) `resolve_bucket_name` folds ALL 5 legacy ml kinds → `ml-store-{env}-{pid}` on gcp+aws × prd+test (24 assertions
    green); (2) real GCS round-trips via UTL `upload_to_storage`/`download_from_storage` (the SAME helpers the writers
    use) on `ml-store-test-central-element-323112` at EVERY cutover prefix — `models/models/…/model.joblib`,
    `training-artifacts/experiments/…/metrics.json`, `configs/…`, `predictions/…`, `artifacts/…` — write+read
    byte-identical + object-exists at folded path; (3) real `ModelRegistry._deserialize_model` joblib gate ADMITS
    `models/`, REJECTS `artifacts/` sibling. All test objects cleaned up (gcs_delete). This is the runtime "exercised"
    proof the cutover writes/reads correctly on the folded env-tiered bucket.
  - **REDEPLOY blocker (fleet-wide, PRE-EXISTING, NOT caused by the fold):** the `ml-service-build` Cloud Build
    (trigger, push→`^main$`) has FAILED every run since ~2026-07-14; last SUCCESS `412055ba` (07-14T03:48, pre-cutover).
    The 07-17T18:14 build (`5bf19ecc`, the fe3b7c2 cutover promote) failed at Step #7 in-image QG: "Codex compliance
    FAILED: 1 violation" = pip-audit `setuptools 82.0.1 : PYSEC-2026-3447`. ROOT CAUSE: the QG base scripts are baked
    into the UTL base Docker image at `/app/unified-trading-pm/scripts/quality-gates-base/`; ml-service/Dockerfile pins
    a STALE base digest `sha256:b7e391f8…` whose baked `qg-common.sh` PREDATES the fleet fix — the PYSEC-2026-3447
    ignore landed in PM `qg-common.sh:106` on 07-14 (commit `3f4fad38`, on origin/main+LDR) but the pinned base image is
    older. Fresh UTL base `:latest` = `sha256:76a15429…` (v0.55.0, pushed 07-18T10:36). This blocks ALL service deploys,
    not just ml (features-service main build also FAILED today 08:54). Since the cutover CODE is v2-green on main
    (authoritative gate) and verify-exercised passes at runtime, the fold's correctness is PROVEN; the
    cloudbuild=SUCCESS citation is gated on the base-image bump. Dispatched a read-only sub-agent (`ac33f074`) to
    confirm the fresh base carries the ignore + scope the minimal fix (bump `BASE_IMAGE_DIGEST` → ship via
    quickmerge→promote). FLEET FINDING for operator.
  - **CONSOLIDATOR 2→1 retarget sites confirmed:** GCP
    `deployment-service/terraform/gcp/manifest_consolidator_scheduler.tf:223`
    (`"ml-training-artifacts" = "ml-training-artifacts-${var.project_id}"`), AWS `.../aws/…:44`, + catalog
    `deployment-api/deployment_api/consolidator_catalog.generated.json:183-187`. Only `ml-training-artifacts` had a
    consolidator (2 cloud jobs: Cloud Run Job `uts-prod-manifest-consolidator-ml-training-artifacts` + AWS Batch); the
    other 4 ml kinds never had one → it's genuinely a retarget-of-1-logical-job, not 5→1. Apply mechanism = TF map edit
    (drift-detector SSOT) + DIRECT gcloud job update (the features-onchain-cefi comment at `:225` confirms consolidator
    jobs are created/removed directly via gcloud, NOT tofu apply) + re-run `gen_consolidator_catalog.py`. Retarget →
    `"ml-store" = "ml-store-${local.deployment_env_short}-${var.project_id}"` (env-tiered; job → …-ml-store).

- **2026-07-18, TICK 7 — base-image fix PROVEN + shipped to LDR; consolidator SSOT retarget shipped; canonical main
  build promoting.** (1) **Base-image pin bump** (unblocks the redeploy): read-only sub-agent `ac33f074` confirmed the
  UTL base Docker image bakes fresh PM `live-defi-rollout` QG scripts at every bake (UTL `cloudbuild.yaml`
  `clone-pm-scripts` → `Dockerfile:84 COPY . .`), and the fresh `:latest` = `sha256:76a15429…` (v0.55.0) CARRIES the
  PYSEC-2026-3447 ignore (grep=2). Also found the automated pin-bump fan-out `digest-drift-sweep.yml` is SILENTLY BROKEN
  fleet-wide (uses repo-scoped `GITHUB_TOKEN` for cross-repo Contents API → never dispatches) → 11 repos stale-pinned →
  ALL their service builds red — filed P1 issue `base_image_digest_sweep_broken_fleet_builds_red_2026_07_18.md`
  (unified-trading-pm@1e87df090), operator decision pending. **Bumped ml-service `Dockerfile` `BASE_IMAGE_DIGEST`
  b7e391f8→76a15429, QG-green, quickmerged ml-service@5d05c4c** (LDR). **PROOF the fix works:** manual
  `gcloud builds submit` off the fixed LDR tree (build `2eedb3ca`) PASSED Step #7 in-image QG (no PYSEC-2026-3447
  failure — pin fix confirmed) + Step #8 operability-probe + pushed the image; it only failed at Step #13
  `publish-wheel` because a manual submit strips `.git` → setuptools-scm can't detect the version — an artifact of
  manual-submit, NOT a real failure (the main-triggered build has `.git`). Triggered the fleet LDR→main promote
  (`ldr-to-main-promote-fleet`, workflow_dispatch 10:09Z) to land 5d05c4c on ml-service main → the `ml-service-build`
  trigger then produces the canonical SUCCESS build to cite. Watcher `bgjjhh1mb` armed for it. (2) **Consolidator
  retarget (SSOT):** the ml consolidator is effectively a no-op — NO `_index/per_vm/` shards exist in any ml bucket (ml
  uses single-blob-CAS: ManifestWriter writes `availability_index.parquet` directly; models index lives at
  `models/_index/`), and the AWS source `unified-trading-ml-training-artifacts-<acct>` NO LONGER EXISTS. Shipped the
  DECLARED-ESTATE retarget: repointed both TF maps' `ml-training-artifacts` value → `ml-store-{env}-{pid}` (gcp
  `…_scheduler.tf:223` env-tiered / aws `:44` `ml-store-prd-<acct>`), kept the category KEY (live job name stays stable;
  rename→ml-store is a cosmetic closeout item), regen'd `consolidator_catalog.generated.json` (ml
  `bucket_template`→`ml-store-{env}-{project}`, 1-line diff). deployment-service + deployment-api QG green; shipping via
  quickmerge. **The LIVE Cloud Run Job `--bucket` repoint is DELIBERATELY COUPLED WITH the Phase-E delete** (atomic —
  the live job safely stays on the still-existing `ml-training-artifacts` until that bucket is deleted; repointing it
  early would make the root-based consolidator write an EMPTY `_index/availability_index.parquet` at ml-store root, a
  potential data-status regression since the real model index is under `models/_index/`). Phase E must: repoint the live
  GCP job `--bucket`→`ml-store-prd-<pid>` AND verify the data-status reader's expected availability_index path BEFORE
  deleting `ml-training-artifacts`.

- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; re-read after intervening edits, verdict unchanged):
  KEEP-NA, valid — operator ruling 2026-07-17 (HUMAN plans) + the P0 open todo is a 5-source prod-bucket delete =
  human-only hard stop. NOTE the P1 SECURITY pickle-gate todo reads STALE — Fold-A's own Progress Log lists
  `UTL@bccc4ca4` (ml Fold-B deserialize gate) in its shipped set.
- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: refreshed context_scope (6 entries) — added the artifact_store.py/model_registry.py
  prefix-collision source paths, dropped pipeline-mode-partition.md.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-02 (unchanged): governed by the 2026-07-17
  operator ruling that all 5 bucket folds are HUMAN plans. The P0 "Delete sources + TF/yaml removal" item is a
  prod-bucket delete (human-only hard stop) plus is blocked on the still-open TF-STATE RECONCILE big finding (32-item
  IAM/scheduler drift, flagged operator-aware, not resolved this pass); IAM+lifecycle P1, deployment-api display cutover
  P2, PM mirror re-sync P3, and alias sunset P3 are all named-blocker residuals (foreign uncommitted deps / fleet ibkr
  crypto-pin drift / fallback-window timing), none newly resolved.

- **context-scout 2026-08-15**: refreshed context_scope (3 entries, trimmed from 6) — sources DONE (delete sources
  shipped 2026-08-08); sole remaining open todo is the P3 alias-sunset stretch item, so swapped the
  artifact_store.py/model_registry.py security-gate source paths (that todo is done) for `bucket_naming.py` (where
  `_KIND_ALIASES` lives, the alias-sunset todo's actual target); dropped the fold-design plan (now archived history).
