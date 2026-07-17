---
doc_type: plan
title:
  Bucket estate structural-fold design — features 25→5, ml 5→1, execution/strategy, portfolio-state (env-tiered from
  birth)
summary:
  "DESIGN doc for Wave-3 of bucket_estate_consolidation_to_sub100_2026_07_13. Specifies the five structural folds that
  take the post-Wave-2 estate (~139) to ~100 total (~80 non-GCP-system): features 25 per-AG/kind buckets → 5 per-AG
  (kind becomes a path prefix), ml {models,predictions,configs,training-artifacts,artifacts} → one ml-store,
  execution-store 4 per-AG + pred → one flat, strategy-store flat gains its env tier, and six positions/pnl/risk stores
  → one portfolio-state bucket. Per the 2026-07-13 operator ruling the consolidated Group-B buckets are env-tiered from
  birth (prd+test), absorbing bucket_env_split_rollout_2026_06 in ONE migration. Each fold enumerates its source
  buckets, target path shape, and reader/writer cutover sites (file:line), plus the cross-cutting manifest-consolidator
  / BQ-external-table / IAM / lifecycle / _KIND_ALIASES implications, a draft migration-sequencing todo list ordered by
  risk (ml → features → execution/strategy → portfolio-state LAST), and the estate arithmetic. Nobody executes this
  tonight — it is the design that spawns the split execution plans. status: draft (never ingested)."
status: draft
nature: design
asset_group: [cross-cutting]
stage: [data, meta]
repos:
  [
    features-service,
    ml-service,
    execution-service,
    strategy-service,
    deployment-api,
    deployment-service,
    unified-api-contracts,
    unified-trading-library,
    unified-trading-system-ui,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    gcs,
    buckets,
    consolidation,
    fold,
    env-split,
    migration,
    features,
    ml,
    execution-store,
    strategy-store,
    portfolio-state,
    lifecycle,
    infrastructure,
  ]
related:
  [
    plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    plans/active/issues/terraform_bucket_estate_drift_resurrection_2026_07_13.md,
    plans/active/issues/strategy_store_split_brain_2026_07_13.md,
    plans/archive/2026_07/bucket_env_split_rollout_2026_06.md,
    plans/active/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    codex/05-infrastructure/bucket-isolation-model.md,
    codex/02-data/pipeline-mode-partition.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: design
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 3.0
assigned_role: infra
drift_direction: advance-code
depends_on: [bucket_estate_consolidation_to_sub100_2026_07_13, defi_dedicated_bucket_shared_migration_2026_07_13]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "W3 design todo of bucket_estate_consolidation_to_sub100_2026_07_13, drafted under /autonomous dispatch 2026-07-13;
  operator ruling: consolidated Group-B buckets env-tiered from birth, single migration."
---

# Bucket estate structural-fold design — Wave 3

> **📐 DESIGN DOC (status: draft — NEVER ingested).** This specifies the five Wave-3 folds of
> [[bucket_estate_consolidation_to_sub100_2026_07_13]]. It is executed later as 3–4 split execution plans (one per agent
> per `task_template.md` §4), NOT by whoever reads it tonight. The draft todo list (§3) is the sequencing skeleton for
> those successor plans; before any of them is authored, ASK the operator for their destination (AO-vs-human — see §5).

> **🟡 OPERATOR RULINGS BAKED IN (2026-07-13)**: (1) consolidated Group-B buckets are **env-tiered from birth** — the
> fold and the `bucket_env_split_rollout_2026_06` env-split are ONE migration ("no double migrates"); (2) provisioned
> tiers = **prd + test only** (dev/stg retired — resolver still supports them, we just stop keeping empty buckets); (3)
> terraform is **derived-from-yaml** (one `for_each google_storage_bucket` generated from `cloud-providers.yaml`;
> `terraform plan` is the drift detector — folding a kind means the new folded key appears in the yaml and the deleted
> per-AG keys leave it); (4) lifecycle = **STANDARD→COLDLINE@60d** whole-bucket, prefix-scoped exceptions where
> retention differs.

**Codex SSOTs** (this plan REFERENCES, does not duplicate):
[`codex/05-infrastructure/bucket-isolation-model.md`](../../codex/05-infrastructure/bucket-isolation-model.md) (naming /
tiers / Group A-vs-B), [`codex/02-data/pipeline-mode-partition.md`](../../codex/02-data/pipeline-mode-partition.md) (the
`pipeline_mode=` path key is LEFT of `asset_group=` and unaffected by a bucket-name/prefix fold),
[`codex/05-infrastructure/manifest-consolidator-ssot.md`](../../codex/05-infrastructure/manifest-consolidator-ssot.md)
(one Cloud Run / Batch-Fargate job per `(service_kind, asset_group)` — folding buckets changes the consolidator target
set).

**Design invariant.** A fold changes TWO things: the bucket NAME (per-AG/per-kind → one folded name) and the object PATH
(the old kind/AG axis becomes a top-level path prefix). `resolve_bucket_name()` returns only the name, so the prefix
insertion is ALWAYS a code change in the writer/reader — an alias alone cannot do it (see §2.D). The `pipeline_mode=`
and `asset_group=`/`day=` hive keys inside the object path are untouched; only a new leading prefix is added, mirroring
the shared-DeFi-bucket `data_type` precedent already shipped in [[defi_dedicated_bucket_shared_migration_2026_07_13]].

---

## 1. Target bucket architecture (per fold: sources → target path shape → cutover sites)

All target names below carry `-{env}-` with `env ∈ {prd, test}` (dev/stg resolvable but unprovisioned). `{pid}` =
`central-element-323112` (GCP) / the AWS account id. Every cutover site is cited `file:line`; sites were enumerated by
`rg --glob '!.venv*' --glob '!build'` over the workspace for each kind's `resolve_bucket_name` callers plus the
hardcoded-name sweeps in the three audit issue docs.

### Fold A — features: 25 per-AG/kind → 5 per-AG (`features-{ag}-{env}-{pid}`)

**Kind becomes a top-level path prefix**: `features-{ag}-{env}-{pid}/{delta_one,volatility,xinstrument,mtf,onchain}/…`
(mirrors the DeFi shared-bucket `data_type` precedent). `features-calendar` stays Group A raw (env-tiered already) —
**NOT folded**. `features-sports` flat (UTL `DataSetSpec`) folds into `features-sports-{env}-{pid}`.

| Source buckets (prd names; per `cloud-providers.yaml` deployment-service:55-97) | Data? (env-split P0.1 inventory)                   | Target                                   |
| ------------------------------------------------------------------------------- | -------------------------------------------------- | ---------------------------------------- |
| `features-delta-one-{cefi,defi,tradfi,sports,pred}`                             | cefi/defi index-only (~1-3 obj)                    | `features-{ag}-{env}-{pid}/delta_one/`   |
| `features-volatility-{cefi,defi,tradfi,sports,pred}`                            | all EMPTY                                          | `features-{ag}-{env}-{pid}/volatility/`  |
| `features-onchain-{cefi,defi}`                                                  | defi ~712 obj (+`-prd` twin ~76 — reconcile first) | `features-{ag}-{env}-{pid}/onchain/`     |
| `features-xinstrument-{cefi,defi,tradfi,sports,pred}`                           | all EMPTY                                          | `features-{ag}-{env}-{pid}/xinstrument/` |
| `features-mtf-{cefi,tradfi,defi}`                                               | cefi index-only                                    | `features-{ag}-{env}-{pid}/mtf/`         |
| `features-sports` (flat, UTL `DataSetSpec`)                                     | see sports_features registry rows                  | `features-sports-{env}-{pid}/…`          |

> Name-slot reconciliation: parent plan says "25". `cloud-providers.yaml` currently declares ~20 per-AG/kind slots
> (delta-one 5 + volatility 5 + onchain 2 + xinstrument 5 + mtf 3) + `features-sports` flat; the remainder of the 25 are
> resolver-emittable AG×kind combos not yet provisioned (e.g. `features-onchain-{tradfi,sports,pred}`,
> `features-mtf-{sports,pred}`) plus the two `_KIND_ALIASES` legacy names. The fold collapses the whole **name-space**
> (25 slots) to **5** regardless of which are currently on disk.

**Writers** — `features-service/features_service/delta_one/app/core/feature_writer.py:67`
(`resolve_bucket_name(kind="features-delta-one")`); `.../volatility/core/feature_writer.py:108`
(`kind="features-volatility"`); `.../onchain/app/core/feature_writer.py` (PATH_REGISTRY user, `features-onchain`); the
xinstrument / mtf writers under `features-service/features_service/` (kinds `features-cross-instrument` /
`features-multi-timeframe`, aliased). Each writer must (a) resolve the folded kind and (b) prepend the kind path prefix.

**Readers / consumers** — `deployment-api/deployment_api/routes/batch_config_utils.py:51-53,61-62,65-67`
(delta-one/onchain/volatility per-AG resolver map); `strategy-service/scripts/trace_all_carry_archetypes.py:357`
(`features-onchain` defi); ml-service feature consumers (`ml_service/inference/app/core/dependency_checker.py` +
`training/app/core/dependency_checker.py` reference `features-delta-one-*` in guards/tests);
`deployment-ui/src/lib/mock-api.ts:3083,3094,3107` (mock catalogue — low priority, mock data only).

**Config / registry** — `deployment-service/configs/cloud-providers.yaml:55-97` (canonical) + PM mirror
`unified-trading-pm/configs/cloud-providers.yaml:68-107` + UAC packaged copy
`unified-api-contracts/unified_api_contracts/config/cloud-providers.yaml` (the runtime fallback — MUST ship, see the
terraform-drift issue doc §1); UTL `_KIND_ALIASES` `unified-trading-library/.../cloud_interface/bucket_naming.py:93-96`
(`features-cross-instrument`→`features-xinstrument`, `features-multi-timeframe`→`features-mtf`); UTL PATH_REGISTRY
`config_interface/paths/registry.py:180,187,194,201` (`bucket_template="features-sports-{project_id}"`); UAC facade
`unified-api-contracts/unified_api_contracts/canonical/gcs_paths.py` (`sports_bucket_name`, `generic_bucket_template`,
`bucket_name`).

### Fold B — ml: 5 kind-buckets → 1 (`ml-store-{env}-{pid}`)

**Kind becomes a top-level path prefix**:
`ml-store-{env}-{pid}/{models,predictions,configs,training-artifacts,artifacts}/…`

| Source buckets (prd)    | Data?                                | Target prefix                              |
| ----------------------- | ------------------------------------ | ------------------------------------------ |
| `ml-models-store`       | live (final model artefacts)         | `ml-store-{env}-{pid}/models/`             |
| `ml-predictions-store`  | live                                 | `ml-store-{env}-{pid}/predictions/`        |
| `ml-configs-store`      | live                                 | `ml-store-{env}-{pid}/configs/`            |
| `ml-training-artifacts` | flat `-{pid}` ~74 obj (experiments/) | `ml-store-{env}-{pid}/training-artifacts/` |
| `ml-artifacts`          | UTL `CloudModelArtifactStore` target | `ml-store-{env}-{pid}/artifacts/`          |

> Parent plan frames ml as "8→2"; the extra 3 of the 8 are the legacy `ml-models-store-{dev,prod,staging}` +
> `ml-configs/predictions-store` dev/prod/staging twins that **Wave 1/2 already delete** (parent Appendix A). At Wave 3
> the live surface is 5 kinds → 1 folded `ml-store`.

**Writers / readers** — `ml-service/ml_service/training/app/core/training_orchestrator.py:511-512`
(`kind="ml-training-artifacts"`); the hardcoded training-artifacts f-strings
`ml_service/training/cli/handlers/hyperparam_grid_handler.py:279,339`, `final_training_handler.py:221,236`,
`preselection_handler.py:339`; `ml_service/training/config.py:75` (`ml-configs-store` default), `:87`
(`ml-training-artifacts-{project_id}` default); `ml_service/inference/config.py:13` (`ml-models-store-{project_id}`
template), `:151` (`ml-predictions-store-{project_id}` default); the per-AG hardcoded guard maps
`ml_service/inference/app/core/dependency_checker.py:46-48` (`ml-predictions-store-*`) +
`ml_service/training/app/core/dependency_checker.py:99-101` (`ml-models-store-*`); UTL
`unified_trading_library/ml/model_registry.py:113` (`ml-models-store`) +
`unified_trading_library/domain_client/artifact_store.py:89` (`ml-artifacts`);
`deployment-service/tools/check_ml_dependencies_by_mode.py:57` (`ml-training-artifacts`);
`deployment-api/deployment_api/deployment_api_config.py:642` (`ml-configs-store-{pid}` default, `# CORRECT-LOCAL`),
`:509` (description).

**Config** — `cloud-providers.yaml:98-108` (deployment-service) + the two stale copies.

### Fold C — execution-store: 4 per-AG + pred → 1 (`execution-store-{env}-{pid}`)

**AG becomes a top-level path prefix**: `execution-store-{env}-{pid}/{cefi,defi,tradfi,sports,pred}/execution/by_date/…`
(the current `execution-store-{category}-{pid}` per-AG name collapses; the `{category}` axis moves into the path). Also
folds the `nautilus-catalog-cache/` prefix that shares the per-AG bucket today.

| Source buckets (prd)                                               | Data?                                                                  | Target                                         |
| ------------------------------------------------------------------ | ---------------------------------------------------------------------- | ---------------------------------------------- |
| `execution-store-{cefi,defi,tradfi,sports}`                        | cefi ~6142 obj (fills/configs/deployment_history/spreads); rest sparse | `execution-store-{env}-{pid}/{ag}/execution/…` |
| `execution-store-prediction` (`kind="execution-store-prediction"`) | see service_config                                                     | `execution-store-{env}-{pid}/pred/execution/…` |

**Writers / readers** — `execution-service/execution_service/service_config.py:738`
(`resolve_bucket_name(kind="execution-store-prediction")`), `:253` (comment SSOT note); UTL PATH_REGISTRY
`config_interface/paths/registry.py` `execution_fills` + `nautilus_catalog`
(`bucket_template="execution-store-{category}-{project_id}"`); `deployment-api/deployment_api_config.py:614`
(`execution-store-{pid}` default), `:481` (description); `deployment-api/routes/services.py:330` (advertised
"execution-store (main)"); `deployment-api/routes/service_status_execution.py:311,593` (config-path examples).

### Fold D — strategy-store: flat → `strategy-store-{env}-{pid}` (gains its tier only)

Already unified-flat (D6 operator decision 2026-05-20); the fold ONLY adds the `-{env}-` tier. **DEPENDS_ON** the parent
plan's Wave-2 [[strategy_store_split_brain_2026_07_13]] repoint (per-AG readers → flat kind) landing FIRST — this fold
is the "gains its tier in the same move" note in the parent's W3 todo.

| Source                                               | Data?                                                          | Target                                                  |
| ---------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------- |
| `strategy-store` (flat)                              | live (`_index/latest.json` written 2026-07-13)                 | `strategy-store-{env}-{pid}` (same layout, tiered name) |
| `strategy-store-{cefi,tradfi,defi}` (per-AG readers) | cefi real-but-stale (catalogue/ 2026-04-25); tradfi/defi EMPTY | RETIRED by W2 split-brain, not by this fold             |

**Writers (already resolve flat `kind="strategy-store"`, only re-tier)** —
`strategy-service/strategy_service/engine/core/gcs_storage_service.py:64`;
`.../position/core/venue_balance_tracker.py:75`;
`.../engine/strategies/v2/carry_and_yield/hedge_ratio_writer.py:142,185`; `.../decision_context_writer.py:154,197`;
`.../pnl/adapters/domain_adapter.py:118`. **Readers still on per-AG (fixed by W2, listed here for the tier follow-on)**
— `deployment-api/deployment_api_config.py:621,628,635` + `:488-502`; `deployment-api/routes/services.py:339-347`;
`unified-trading-system-ui/app/api/catalogue/envelope/route.ts:24` + `catalogue/instrument/route.ts:23` (hardcoded
`strategy-store-cefi-…`); `unified-api-contracts/scripts/enumerate_envelope.py:1053`, `enumerate_availability.py:43`,
`enumerate_strategy_instruments.py:12`; UAC facade `canonical/gcs_paths.py::strategy_store_bucket` (returns
`strategy-store-cefi-{pid}` — must return the flat tiered name). **Config** — `cloud-providers.yaml` `strategy-store`
flat key (add `${DEPLOYMENT_ENV_SHORT}-`).

### Fold E — portfolio-state: 6 stores → 1 (`portfolio-state-{env}-{pid}`) — LAST, live-trading-adjacent

**Per-domain path prefixes**:
`portfolio-state-{env}-{pid}/{positions,pnl-attribution,risk-metrics,pnl-attribution-output,archetype-state,position-sports}/…`.
**Heterogeneous sources** — three drivers, so the cutover touches three surfaces:

| Source bucket (prd)      | Driver / SSOT                                                                                    | Tiered today? | Target prefix                 |
| ------------------------ | ------------------------------------------------------------------------------------------------ | ------------- | ----------------------------- |
| `positions-store`        | UTL PATH_REGISTRY `registry.py:152` (`positions-store-{project_id}`, no-AG)                      | NO (flat)     | `.../positions/`              |
| `pnl-attribution-store`  | UTL PATH_REGISTRY `registry.py:159`                                                              | NO (flat)     | `.../pnl-attribution/`        |
| `risk-metrics-store`     | UTL PATH_REGISTRY `registry.py:166`                                                              | NO (flat)     | `.../risk-metrics/`           |
| `pnl-attribution-output` | bare default `strategy-service/strategy_service/pnl/config.py:15` (NOT in yaml, NOT in registry) | NO            | `.../pnl-attribution-output/` |
| `archetype-state`        | `cloud-providers.yaml:218` (`archetype-state-${DEPLOYMENT_ENV_SHORT}-${pid}`)                    | **YES**       | `.../archetype-state/`        |
| `position-store-sports`  | `cloud-providers.yaml:132` + `venue_balance_tracker.py:76`                                       | **YES**       | `.../position-sports/`        |

> Caution: the three PATH_REGISTRY stores gain their tier for the FIRST time in this fold (they were never in
> `cloud-providers.yaml` — the SSOT is the UTL `DataSetSpec` `bucket_template`, see the yaml comment
> deployment-service:190-196). `archetype-state` + `position-store-sports` already carry `-{env}-`, so folding them is a
> name+prefix move, not a re-tier. The "writer services" the yaml names (`risk-and-exposure-service` /
> `pnl-attribution-service` / `position-balance-monitor-service`) **do not exist as repos** — the real writers reach
> these buckets through UTL `DataSetSpec`, consumed by strategy-service's pnl/position modules. Redeploy those, not
> phantom services.

---

## 2. Cross-cutting implications

### A. Manifest `_index` + consolidator wiring

Each data bucket carries its own `_index/availability_index.parquet` (MTDS `data_manifest_handler.py:376`), and the
consolidator runs **one Cloud Run Job (GCP) / Batch-Fargate job (AWS) per `(service_kind, asset_group)`**
(`manifest-consolidator-ssot.md` §"one job per pair"; entrypoint
`python -m unified_trading_library.manifest_consolidator --bucket {X} --once`). **Folding changes the consolidator
target set**: N per-AG feature jobs collapse to 5 per-AG-bucket jobs (prefix-scoped `_index` under each kind prefix), ml
5 jobs → 1, execution 5 → 1, portfolio-state 6 → 1. This is the single largest downstream wiring change and rides the
same derived-from-yaml terraform (the consolidator TF modules already key off the bucket list — Phase D precedent
`deployment-service@e8e72e7`). Do NOT leave a legacy-flat consolidator cron pointed at a deleted bucket (idle-bucket
loud-fail).

### B. BQ `feature_external` external tables (M-1 A11 — root-mounted URIs)

Feature buckets are mounted as BigQuery external tables at the **bucket root** (Hive-partition auto-discovery — UTL
`domain_client/catalog/bq_catalog.py` `create_external_table`, provider `cloud_interface/providers/gcp.py:860`; writer
note `features-service/.../delta_one/app/core/feature_writer.py:593`). Folding inserts a new leading `{kind}/` prefix,
so every affected external table's `sourceUris` + `hivePartitioningOptions.sourceUriPrefix` must be re-pointed to
`gs://features-{ag}-{env}-{pid}/{kind}/` and the table re-created (external tables hold no data — a DDL re-issue, not a
copy). This is a per-fold code step, gated on the writer cutover landing.

### C. IAM write-protection per tier re-gating

[[bucket_iam_write_protection_per_tier_2026_06_09]] Phase 2 (Group B) is **explicitly re-gated on these folds** (that
plan's :105-107,154-155: "Group B buckets join here only after the consolidation plan's Wave-3 folds provision their
`-{env}-` form"). Once a fold provisions its `-prd-` target, that bucket joins the prod IAM write-protection set (SA
read+write scoped to domain; CI/dev read-only on prd). The `-test-` twin gets the test-tier (short-lived) policy. Signal
Phase 2 unblocked per-fold, not in one batch.

### D. `cloud-providers.yaml` kind-key migration — **RECOMMEND: soft `_KIND_ALIASES` during the per-fold window, hard-removed with the source-bucket delete**

UTL already ships `_KIND_ALIASES` (`bucket_naming.py:93`) mapping consumer vocab → yaml key
(`features-cross-instrument`→`features-xinstrument`, `tick-data`→`market-data`). **Recommendation**: for each fold, add
the new folded yaml key (e.g. `features-cefi`, `ml-store`, `portfolio-state`) AND add `_KIND_ALIASES` entries mapping
every old kind to the new key, so a not-yet-cutover caller's `resolve_bucket_name(kind="features-delta-one", ...)`
resolves to the folded bucket during the migration window. **Justification**: (1) it is the established workspace
pattern (the tick-data alias de-risked the DeFi shared-bucket migration the same way); (2) it makes the multi-repo
cutover non-atomic-safe — name resolution never breaks mid-flight across ~10 repos; (3) it composes with the
`pipeline-mode-partition.md` reader-fallback discipline (hard-remove aliases + old keys once the fallback window closes,
"no double SSOT"). **Caveat (why it is NOT a pure alias swap)**: the alias fixes only the NAME; the kind→path-prefix
insertion is a code change per writer/reader regardless (`resolve_bucket_name` returns no path). So treat each fold as
an **atomic per-family code cutover** (name-alias + prefix-insertion shipped together, verified), with the alias as the
safety net for any missed caller — NOT a gradual per-caller drift where a half-migrated reader writes to the bucket root
instead of `{kind}/`. Hard-remove the aliases + retired yaml keys in the SAME change that deletes the source buckets (§3
todo 17), keeping `terraform plan` (the derived-from-yaml drift detector) green.

### E. Lifecycle rules

Per operator ruling: **STANDARD→COLDLINE@60d whole-bucket** on the folded data buckets, encoded in the derived-from-yaml
terraform (the one tracked place). **Prefix-scoped exceptions** where retention differs — e.g. `ml-store/configs/`
(hot-reloaded config, keep STANDARD), `strategy-store/catalogue/` (UI-served daily, keep STANDARD), `portfolio-state/`
live-trading snapshots (confirm retention before COLDLINE). Supersede the `gcs-lifecycle-policies.md` "intentionally NOT
lifecycle'd" claim per the parent Wave-0 todo.

---

## 3. Migration sequencing — draft todo list (execute LATER as split plans; order by risk)

> Risk order (fewest live readers → most): **ml → features → execution/strategy → portfolio-state (LAST, live-trading
> adjacent)**. Every fold follows the [[defi_dedicated_bucket_shared_migration_2026_07_13]] playbook: provision
> env-tiered target → dual-verify parity → reader cutover ship → redeploy + verify-exercised → delete sources + TF/yaml
> removal in the SAME change. These are the sequencing skeleton for the successor split plans, not dispatchable todos on
> this draft doc.

- [x] ✅ [INFRA] P0. **Split-plan authoring + destination gate** — author the successor execution plans (ml / features /
      execution+strategy / portfolio-state), one per agent for parallelism (`task_template.md` §4); ASK the operator
      AO-vs-human destination per the plan-destination HARD RULE before flipping any to `active`. Each carries the
      DeFi-playbook shape below. — DONE 2026-07-17: operator ruled **all 5 folds, HUMAN plans** (`assigned_vm: NA`).
      Authored 5 successor plans: [[bucket_fold_ml_2026_07_17]], [[bucket_fold_features_2026_07_17]],
      [[bucket_fold_execution_strategy_2026_07_17]], [[bucket_fold_portfolio_state_2026_07_17]] +
      [[bucket_fold_closeout_2026_07_17]] (cross-cutting, `depends_on` all four).
- [ ] [INFRA] P0. **Alias + yaml scaffold (shared prerequisite)** — add the folded keys to `cloud-providers.yaml` (all 3
      copies) + `_KIND_ALIASES` entries for every retired kind (§2.D soft-transition); no bucket deletes yet. Verify
      `terraform plan` (derived-from-yaml) shows the new folded buckets as the only creates.

- [ ] [DATA] P0. **ml — provision** `ml-store-{prd,test}-{pid}` (GCP + AWS) via the derived-from-yaml `for_each`; no
      dev/stg twins.
- [ ] [CODE] P0. **ml — cutover** — parity-verify each source vs `ml-store/{prefix}/`; cut over all writers/readers
      (Fold B sites) to `kind="ml-store"` + kind path-prefix; ship per-repo QG-green (ml-service, UTL, deployment-api,
      deployment-service).
- [ ] [INFRA] P0. **ml — redeploy + delete** — redeploy ml-service, verify the new path is genuinely exercised (not just
      deployed); retarget the ml consolidator job(s) 5→1; delete the 5 source buckets + remove their TF/yaml keys in the
      same change.

- [ ] [DATA] P1. **features — provision** `features-{cefi,defi,tradfi,sports,pred}-{prd,test}-{pid}`; reconcile the
      `features-onchain-defi` flat(~712)-vs-`-prd`(~76) twins BEFORE migrate (copy only flat objects absent from prd).
- [ ] [CODE] P1. **features — cutover** — parity-verify; cut over writers (delta_one/volatility/onchain/xinstrument/mtf
      `feature_writer.py`) + readers (`batch_config_utils.py`, ml consumers, `trace_all_carry_archetypes.py`) to
      `features-{ag}` + kind prefix; re-mount the BQ `feature_external` external tables at the new prefix (§2.B); ship.
- [ ] [INFRA] P1. **features — redeploy + delete** — redeploy features-service, verify exercised; retarget the feature
      consolidator jobs → 5 per-AG-bucket jobs; delete the ~20 source buckets + TF/yaml removal same change.

- [ ] [DATA] P1. **execution + strategy — provision** `execution-store-{prd,test}-{pid}`; add `-{env}-` to the
      `strategy-store` flat key (this wave carries both — strategy is name-tier-only).
- [ ] [CODE] P1. **execution + strategy — cutover** — DEPENDS_ON parent W2 [[strategy_store_split_brain_2026_07_13]]
      repoint landed; parity-verify; cut over execution-store per-AG → flat + AG path-prefix (Fold C sites, incl.
      `nautilus-catalog-cache/`); re-tier strategy-store writers (Fold D sites) + the UAC `strategy_store_bucket`
      facade; ship.
- [ ] [INFRA] P1. **execution + strategy — redeploy + delete** — redeploy execution-service + strategy-service, verify
      exercised; delete source buckets + TF/yaml.

- [ ] [DATA] P2. **portfolio-state — provision** `portfolio-state-{prd,test}-{pid}`; note the heterogeneous sources (UTL
      PATH_REGISTRY flat trio gains its tier for the first time; `archetype-state` + `position-store-sports` already
      tiered).
- [ ] [CODE] P2. **portfolio-state — cutover** — parity-verify each of the 6 sources; cut over UTL PATH_REGISTRY
      (`registry.py:152,159,166`) + the `pnl-attribution-output` bare default (`pnl/config.py:15`) + the two yaml kinds
      → `portfolio-state` + per-domain prefixes; ship (UTL + strategy-service + deployment-service).
- [ ] [INFRA] P2. **portfolio-state — redeploy + delete (LAST)** — redeploy the real writers (strategy-service pnl +
      position modules), verify exercised end-to-end (this is live-trading-adjacent — diff real output, do not rush);
      delete the 6 source buckets + TF/yaml removal LAST.

- [ ] [INFRA] P2. **IAM + lifecycle** — per fold, join each new `-prd-` bucket to
      [[bucket_iam_write_protection_per_tier_2026_06_09]] Phase 2; apply STANDARD→COLDLINE@60d whole-bucket +
      prefix-scoped STANDARD exceptions (§2.E) in the derived-from-yaml terraform.
- [ ] [CODE] P3. **Alias sunset** — after each fold's reader-fallback window closes and
      `READER_FELL_BACK_TO_LEGACY_PATH`-equivalent is grep-clean, hard-remove the `_KIND_ALIASES` entries + retired yaml
      keys ("no double SSOT"); `terraform plan` stays green.
- [ ] [DOCS] P3. **Post-phase codex audit + estate recount** — update `bucket-isolation-model.md` (Group B naming table
      → folded shapes), `manifest-consolidator-ssot.md` (target set), `gcs-lifecycle-policies.md`; final estate recount
      vs the §4 target; flip the parent plan's W3 execute todo + close the audit issue docs.

---

## 4. Estate math (per-fold arithmetic)

Baselines from the parent plan: **241 live → after W1 ≈160 → after W2 ≈139 → after W3 (this design) ≈100 total (~80
non-GCP-system)**. Unit below = distinct **prd-tier bucket NAMES**; each folded target also carries a `-test-` twin, so
the provisioned-bucket reduction is ~2× the prd-name delta (dev/stg retired — no empty tier twins).

| Fold                | Source prd names                                                                                          | Target prd names                              | Δ prd names            |
| ------------------- | --------------------------------------------------------------------------------------------------------- | --------------------------------------------- | ---------------------- |
| A — features        | 20 declared (25 name-slots) + `features-sports` flat                                                      | 5 (`features-{cefi,defi,tradfi,sports,pred}`) | −16 (−20 by name-slot) |
| B — ml              | 5 (`models,predictions,configs,training-artifacts,artifacts`)                                             | 1 (`ml-store`)                                | −4                     |
| C — execution       | 5 (`cefi,defi,tradfi,sports,pred`)                                                                        | 1 (`execution-store`)                         | −4                     |
| D — strategy        | 1 flat (per-AG readers already retired by W2)                                                             | 1 (re-tiered)                                 | 0                      |
| E — portfolio-state | 6 (`positions,pnl-attribution,risk-metrics,pnl-attribution-output,archetype-state,position-store-sports`) | 1 (`portfolio-state`)                         | −5                     |
| **Total**           | **~38 prd names**                                                                                         | **9 prd names**                               | **−29 prd names**      |

Applying the `-test-` twin doubling to the folded families (and netting the dev/stg empties already removed in W1), the
provisioned estate drops **≈139 (post-W2) → ≈100 total**, consistent with the parent plan's stated envelope (~80
excluding the ~20 GCP-system/managed buckets). The remaining ~100 are the Group A raw buckets (market-data-tick /
instruments-store per-AG × prd+test, features-calendar, data-catalogue), the 9 folded Group B targets (× prd+test), the
shared DeFi tick bucket, recon/config-store/events/client-statements, and the ~13 compliance-scaffold + gap buckets the
parent plan's Appendix A explicitly keeps.

---

## 5. Open decisions for the operator

Structured per the escalation rule (options + recommendation):

**Q1 — Destination of the successor EXECUTION plans (this design stays LOCAL regardless).**

- A: **HUMAN plans** (`assigned_vm: NA`) — parent consolidation plan is human; folds need bucket-admin + operator-gated
  deletes; live-trading-adjacent portfolio-state fold wants a human at the wheel. **[WORKER REC]**
- B: **AO-dispatched** the low-risk folds (ml, features) as `planning` plans, keep execution/strategy + portfolio-state
  human.
- C: All AO-dispatched.
- Other: operator custom.

**Q2 — Is any fold too risky to automate at all (hard human-only)?**

- A: **portfolio-state (Fold E) is human-only** — it touches live-trading position/pnl/risk snapshots; a wrong-path
  write or a premature source delete is a live-trading data-integrity hazard. Automate provision + parity-verify; gate
  the reader cutover + delete on operator sign-off. **[WORKER REC]**
- B: Also make execution-store (Fold C, `execution-store-cefi` ~6142 live objects incl. fills) human-gated on the delete
  step.
- C: None — the DeFi-playbook parity+verify gates suffice for all five.
- Other: operator custom.

**Q3 — Lifecycle reading (inherited from parent Wave-0, restated because the folds encode it).** Operator verbatim was
"nearlcoldline nmove after 60d". This design assumes **straight STANDARD→COLDLINE@60d**. Confirm vs a
**NEARLINE@60d→COLDLINE-later ladder** before the terraform encodes it.

- A: Straight COLDLINE@60d whole-bucket + prefix-scoped STANDARD exceptions. **[WORKER REC — matches parent Wave-0]**
- B: NEARLINE@60d → COLDLINE@later ladder.
- Other: operator custom.

## Progress Log

- **2026-07-13, design authored** under /autonomous dispatch as the Wave-3 design deliverable of
  [[bucket_estate_consolidation_to_sub100_2026_07_13]]. Cutover sites enumerated by workspace `rg` over each fold's
  `resolve_bucket_name` callers + the hardcoded-name sweeps in the three audit issue docs (file:line inline in §1). No
  code changed — this is the design that spawns the successor split execution plans (§3 todo 1, gated on the §5 Q1
  operator destination ruling).
- **2026-07-17, §3 todo 1 executed — successor plans authored.** Operator ruled §5 **Q1 = A (all 5 folds as HUMAN plans,
  `assigned_vm: NA`)**. Five successor plans created in `plans/active/`: `bucket_fold_ml_2026_07_17`,
  `bucket_fold_features_2026_07_17`, `bucket_fold_execution_strategy_2026_07_17` (Folds C+D bundled — same services),
  `bucket_fold_portfolio_state_2026_07_17` (LAST, live-trading-adjacent, delete operator-gated per Q2-A), and
  `bucket_fold_closeout_2026_07_17` (`depends_on` all four — codex audit, estate recount, alias sunset, parent-plan
  flip). **Correction baked into the ml plan**: re-measured object counts this session show `ml-predictions-store` +
  `ml-configs-store` (all tiers) + `ml-artifacts` are EMPTY — the Fold B "Data?" column mislabeled predictions/configs
  as "live"; only `ml-models-store-prd` (160 obj), `ml-training-artifacts` flat (76 obj), and legacy `ml-models-store`
  flat (38 obj) hold data. Q3 (lifecycle STANDARD→COLDLINE@60d) carried into each fold as authored; portfolio-state
  flagged confirm-retention-before-COLDLINE. This design stays LOCAL/`draft` (never ingested). </content> </invoke>
