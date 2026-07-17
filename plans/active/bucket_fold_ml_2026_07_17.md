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
    plans/active/bucket_estate_fold_design_2026_07_13.md,
    plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md,
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

- `codex/05-infrastructure/bucket-isolation-model.md` — Group B naming; update the ml rows to the folded shape (closeout
  plan).
- `codex/05-infrastructure/manifest-consolidator-ssot.md` — "one job per (service_kind, asset_group)"; ml 5 jobs → 1.
- `codex/02-data/pipeline-mode-partition.md` — reader-fallback discipline; anchors the `_KIND_ALIASES` soft-window +
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
- [ ] [INFRA] P0. **Redeploy + verify-exercised** — redeploy ml-service; verify the new `ml-store/{prefix}/` path is
      GENUINELY exercised (run a training + an inference read, diff real output — not just "deployed"). Cite
      `Evidence: cloudbuild=<id>` resolving SUCCESS. Retarget the ml manifest-consolidator job(s) 5→1 (single `ml-store`
      bucket, prefix-scoped `_index` per kind); confirm no legacy-flat consolidator cron points at a soon-deleted bucket
      (idle-bucket loud-fail).
- [ ] [INFRA] P0. **Delete sources + TF/yaml removal (SAME change)** — after verify-exercised + a passive read-audit
      window confirms zero reads on the 5 legacy names, delete the 5 source buckets (GCP + AWS) and remove their TF/yaml
      keys in the same change so `terraform plan` (derived-from-yaml drift detector) stays green. This also closes the
      parent plan's W2 flat-`ml-models-store` delete todo — flip it too.
- [ ] [INFRA] P1. **IAM + lifecycle** — join `ml-store-prd` to [[bucket_iam_write_protection_per_tier_2026_06_09]]
      Phase-2 Group-B (signal it unblocked for THIS fold); `-test-` twin gets the test-tier policy. Apply
      STANDARD→COLDLINE@60d whole-bucket in the derived-from-yaml terraform, with a prefix-scoped STANDARD exception for
      `ml-store/configs/` (hot-reloaded config).
- [ ] [CODE] P1. **SECURITY — gate `CloudModelArtifactStore.load_model` pickle deserialization** (found by the Fold-B
      UTL adversarial review, security lens). `domain_client/artifact_store.py` `load_model` joblib-deserializes with NO
      trusted-prefix allowlist and NO sha256 gate — UNLIKE `ModelRegistry` (`_ALLOWED_JOBLIB_PREFIXES` + optional
      sha256). Pre-existing, but Fold B now CO-LOCATES its objects (`artifacts/`) in the SAME `ml-store` bucket as
      ModelRegistry (`models/`), so an untrusted object under `artifacts/` becomes a pickle-RCE path through the ungated
      consumer. Mirror `ModelRegistry._deserialize_model`: enforce keys start with `artifacts/` + optional sha256. NOTE:
      `artifacts/` is EMPTY today (ml-artifacts was empty) so no live exposure yet — but close before anything writes
      there. Not a blocker for the UTL scaffold ship (orthogonal to bucket naming).
- [ ] [CODE] P2. **Ship deployment-api ml-store display cutover** (4 files: `commentary/pipeline_uat.py`,
      `deployment_api_config.py`, `routes/services.py`, `services/data_status_drilldown/_core.py`) — implemented +
      QG-verified 2026-07-17 (display-only: data-status drilldown + config-buckets scope to ml-store prefixes;
      pipeline_uat dead f-string repointed). Currently UNCOMMITTED in the deployment-api tree — BLOCKED by foreign
      uncommitted `terraform.tfvars` (features-service-sports docker repin) in the deployment-service DEP (quickmerge
      dep-cleanliness gate; not mine to commit). Ship once that foreign WIP clears. Non-runtime-critical (the
      availability-index readers already discriminate ml via the `service_name==ml-service` filter, so no conflation
      without this).
- [ ] [DATA] P3. **PM `cloud-providers.yaml` mirror re-sync** — add the `ml-store` key to the non-authoritative PM
      mirror (deferred 2026-07-17: PM quickmerge STAGE 1.5 dependency-alignment gate fails on an UNRELATED fleet drift —
      `ibkr-gateway-infra` pins `cryptography>=46,<47` vs canonical `>=47,<50`, which blocks ALL PM config quickmerges).
      The mirror is non-runtime (deployment-service authoring + UAC packaged are the read copies, both shipped). Re-sync
      when the ibkr drift clears, or bundle into the closeout copy-reconcile. FLEET FINDING flagged to operator.
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
