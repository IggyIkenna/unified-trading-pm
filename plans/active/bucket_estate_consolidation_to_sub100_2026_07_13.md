---
doc_type: plan
title: Bucket estate consolidation — 241 → <100 (waves 0-3, single-migration env-split fold)
summary:
  "Executes the 2026-07-13 full bucket estate audit — current estate 241 buckets (132 empty), canonical floor 87
  (prd+test). Wave 0 stops the estate regrowing (terraform reconcile after the 2026-07-12 apply resurrected ~30
  cleanup-deleted buckets; stale UAC/PM cloud-providers.yaml copies; stale provisioning scripts). Wave 1 deletes 81
  confirmed-empty buckets (list in appendix — self-contained, no session scratch dependency). Wave 2 tracks/completes
  the in-flight deletions owned by other plans (DeFi dedicated buckets, legacy flat tick/instruments twins, football, ml
  legacy) + fixes the recon/strategy-store/config-store bucket breakages found by the audit. Wave 3 designs the
  structural folds (features 25→5 per-AG, ml 8→2, unified stores) — per the operator ruling 2026-07-13, the folded
  Group-B buckets are env-tiered from birth, absorbing bucket_env_split_rollout_2026_06.md in ONE migration. HUMAN plan
  (operator-driven) — several steps need bucket-admin/terraform permissions and operator-gated data deletions."
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos:
  [
    deployment-service,
    unified-api-contracts,
    unified-trading-pm,
    unified-trading-library,
    deployment-api,
    unified-trading-system-ui,
    batch-live-reconciliation-service,
    e2e-testing,
    execution-service,
  ]
scope: [engineer, admin]
tags: [gcs, buckets, consolidation, terraform, migration, env-split, lifecycle, infrastructure]
related:
  [
    plans/active/issues/terraform_bucket_estate_drift_resurrection_2026_07_13.md,
    plans/active/issues/recon_bucket_missing_nightly_recon_failing_2026_07_13.md,
    plans/active/issues/strategy_store_split_brain_2026_07_13.md,
    plans/archive/2026_07/bucket_env_split_rollout_2026_06.md,
    plans/active/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    plans/active/gcs_bucket_estate_cleanup_2026_07_10.md,
    plans/active/data_completion_to_100_all_ag_2026_06_21.md,
    plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
  ]
created: "2026-07-13"
last_updated: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
assigned_role: infra
drift_direction: advance-code
depends_on: [defi_dedicated_bucket_shared_migration_2026_07_13]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Operator, 2026-07-13 — requested full estate audit ('i really dont see how we need more than 100 gcs buckets'), then
  ruled env-split merges into the folds ('execute env split plan as written but fold in so that we dont have double
  migrates') and chose HUMAN plan destination when asked per the plan-destination HARD RULE."
---

# Bucket estate consolidation — 241 → <100

> **🟡 OPERATOR RULINGS BAKED IN (2026-07-13, all decided)**: (1) env-split STANDS but merges into the Wave-3 folds —
> consolidated Group-B buckets env-tiered from birth, ONE migration ([[bucket_env_split_rollout_2026_06]] unlocked +
> archived same day, superseded by this plan); (2) this is a HUMAN plan; (3) terraform = **derived-from-yaml** (one
> `for_each` bucket block generated from cloud-providers.yaml's canonical names; hand-written blocks only for genuine
> infra buckets; `terraform plan` becomes the drift detector); (4) lifecycle = **cold-tier move at 60d** (operator
> verbatim "nearlcoldline nmove after 60d" — encoded as STANDARD→COLDLINE@60d replacing the untracked @14d; if a
> NEARLINE@60→COLDLINE-later ladder was intended, say so before the W0 todo executes); (5) dev/stg tiers **retired**
> (prd+test remain the provisioned estate).

**Audit provenance (2026-07-13 session)**: authoritative 241-bucket listing + full metadata read via orchestrator-VM
admin credential; classification cross-checked against an 845-name resolver/grep candidate probe; 5-agent research
fan-out over codex/plans/configs/code; 7-agent adversarial verification of the load-bearing claims. Issue docs above
carry the per-finding evidence (file:line). Numbers: 241 live · 132 empty · canonical floor 60 (prd) / 87 (prd+test) ·
after W1 ≈ 160 · after W2 ≈ 139 · after W3 ≈ ~100 total (~80 excluding GCP-system).

Codex SSOTs: `codex/05-infrastructure/bucket-isolation-model.md`, `codex/05-infrastructure/gcs-lifecycle-policies.md`,
`codex/05-infrastructure/gcs-object-operations.md`, `codex/02-data/pipeline-mode-partition.md`,
`codex/05-infrastructure/manifest-consolidator-ssot.md`.

## Wave 0 — stop the bleeding (nothing else sticks until this lands)

- [ ] [INFRA] P0. **Terraform reconcile** (`deployment-service/terraform/gcp/main.tf` +
      `modules/shared-infrastructure/gcp/main.tf`): remove every `google_storage_bucket` resource whose bucket the
      07-10/07-12 cleanups deleted or whose name no resolver path emits — long-env Group-B blocks (main.tf:807-1357),
      legacy-kind tests gas-fees-test/solana-defi-test/ evm-defi-test (:736-799), full-word `-prediction-test-` (:353,
      :685, :970, :1151) — with matching `terraform state rm`; keep resources tracking LIVE buckets (legacy flat
      tick/instruments, the 3 dedicated DeFi `-prd` — those leave TF only in the same change that deletes the bucket,
      see W2). Until this lands: **no `terraform apply` from anyone** (each apply regrows ~30 empty buckets). Evidence
      bar — `terraform plan` shows zero bucket creates against the post-W1 estate.
- [ ] [INFRA] P0. **RULED 2026-07-13 — terraform derived-from-yaml**: implement one `for_each` `google_storage_bucket`
      block generated from cloud-providers.yaml's canonical (prd+test) names, import the existing canonical buckets into
      it, keep hand-written blocks only for genuine infra buckets (deployment-scripts, state, events, …). Document the
      model in `codex/05-infrastructure/bucket-isolation-model.md`.
- [ ] [CONFIG] P0. **Sync the stale cloud-providers.yaml copies** to the canonical 36-kind file:
      `unified-api-contracts/unified_api_contracts/config/cloud-providers.yaml` (the packaged runtime fallback — ship
      via quickmerge, this one is a real runtime divergence for standalone installs) +
      `unified-trading-pm/configs/cloud-providers.yaml`; also reconcile
      `unified-trading-library/tests/fixtures/cloud-providers.yaml` if the kind removals changed parametrized tables
      (estate-cleanup §5b lesson — grep `rg -l '<kind>'` workspace-wide, 4 copies + shadows).
- [ ] [INFRA] P0. **RULED 2026-07-13 — cold-tier move at 60d**: replace the untracked STANDARD→COLDLINE@14d rules with
      STANDARD→COLDLINE@60d on the data buckets, encoded in the derived-from-yaml terraform (the ONE tracked place per
      the ruling above) + update `codex/05-infrastructure/gcs-lifecycle-policies.md` (its "intentionally NOT
      lifecycle'd" claim for tick buckets is superseded). Operator verbatim "nearlcoldline nmove after 60d" — if a
      NEARLINE@60→COLDLINE-later ladder was intended instead of straight COLDLINE@60d, correct here before executing.
- [ ] [SCRIPT] P1. **Retire the stale provisioning surfaces**: `deployment-service/scripts/setup-buckets.py` (reads
      `dependencies.yaml`'s pre-canonical scheme, emits literal `{category_lower}`) — delete or rewrite on
      `resolve_bucket_name`; fix `e2e-testing/scripts/common/setup-gcp-fixtures.sh:39-53` (provisions transposed
      non-canonical names — active pollution source) and `deployment-service/scripts/setup-gcs-lifecycle-policies.sh`
      (targets legacy flat names).

## Wave 1 — delete the 81 confirmed-empty buckets (AFTER Wave-0 terraform reconcile)

- [ ] [SCRIPT] P0. Delete the 81 buckets in Appendix A. Protocol per estate-cleanup precedent: re-verify emptiness
      immediately before each delete (shallow root `ls` — provably complete); zero overlap with the never-touch list;
      log per-bucket; independently re-count the estate after (expect ≈160). Two gated exceptions inside the list:
      `positions-store-test` — verify no test-mode PATH_REGISTRY caller first (the `dex-pools-test` false-positive
      precedent, estate cleanup §"false-positive caught"); `strategy-store-defi`/`strategy-store-tradfi` — delete only
      AFTER the split-brain repoint below (deployment-api defaults still reference them).
- [x] ✅ [OPERATOR] P1. **RULED 2026-07-13 — retire BOTH dev/stg tiers** (operator answer to the audit question set; 20
      of 21 canonical dev/stg buckets empty). Remaining action rides the W1 delete todo above; the sole content-bearing
      exception `instruments-store-sports-dev` gets inspect + migrate/drop there. Resolver keeps supporting the tiers;
      we just stop keeping empty buckets for them.

## Wave 2 — in-flight completions + audit-found breakages (estate ≈139 after)

- [ ] [DATA] P0. **recon bucket** ([[recon_bucket_missing_nightly_recon_failing_2026_07_13]]): operator decides kind vs
      prefix; provision; repoint `batch_live_reconciliation_service/config.py` to the resolver; fix launcher doc;
      end-to-end T1 chain run; next scheduled run green; wire Cloud Run failure alerting (55 silent failures).
- [ ] [CODE] P1. **strategy-store split-brain** ([[strategy_store_split_brain_2026_07_13]]): repoint deployment-api
      defaults + UI catalogue route + `enumerate_envelope.py` to the flat kind; migrate-or-regenerate the cefi bucket's
      `configs/` + `catalogue/`; then retire `strategy-store-{cefi,tradfi,defi}-{pid}` (cefi last) + their TF resources.
- [ ] [CODE] P1. **config-store split-brain**: flat `config-store-{pid}` AND canonical `config-store-prd-{pid}` both
      exist with content; `unified_trading_library/config_interface/__init__.py:170` + `bucket_config.yaml` still emit
      the flat name. Repoint to resolver, verify hot-reload consumers, migrate + retire the flat bucket.
- [ ] [DATA] P0. Track to completion the deletions OWNED BY OTHER PLANS (checkpoint only, do not duplicate):
      `dex-pools-prd`/`lst-rates-prd`/`perp-funding-prd` (−3, [[defi_dedicated_bucket_shared_migration_2026_07_13]]
      todos 6-9 incl. the TF-resource removal added 2026-07-13); `lending-indices`+`-prd` (−2, same plan / estate
      cleanup §5i, gated on VM `mtds-lending-indices-20260712-112557` completion); legacy flat tick+instruments twins
      (−8, M-1 `data_completion_to_100_all_ag_2026_06_21` L6, operator-gated version-aware deletes — millions of
      noncurrent versions).
- [ ] [OPERATOR] P1. **football-\* (4 buckets)** — no canonical destination exists (estate cleanup §5g): rule
      archive-tier-and-dated-delete vs migrate `odds/`+`parquet_backup/` into the sports pipeline first.
- [ ] [DATA] P1. **ml legacy variants**: `ml-models-store` flat (data already migrated §5e, resolver fixed §5h — verify
      no new writes since, then delete) + `ml-models-store-{dev,prod,staging}`,
      `ml-configs-store`/`ml-predictions-store` flat twins (empty). Verify
      `deployment-api/deployment_api_config.py:642`'s flat `ml-configs-store-{pid}` default is repointed first.
- [ ] [DATA] P2. Disposition the 4 ops-tooling buckets found unregistered (`{pid}-honest-coverage`,
      `{pid}-phantom-triage`, `{pid}-rescan-triage`, `{pid}-benchmark-reports`): register (yaml kind or documented infra
      list) or fold into `{pid}-data-status-rollups` prefixes; same for `{pid}-deployment-events` (live QG snapshots,
      unregistered).

## Wave 3 — structural folds to <100 (design first; env-tiered from birth per ruling)

- [x] ✅ [INFRA] P1. **Fold design doc** (its own deliverable; READ task_template before authoring the successor
      plan(s), ASK operator for their destination): features 25 per-AG/kind buckets → 5 per-AG env-tiered
      (`features-{ag}-{env}-{pid}`, kind as path prefix, mirroring the DeFi shared-bucket data_type precedent); ml
      {models,predictions,configs,training-artifacts,artifacts} → `ml-store-{env}-{pid}`; unified
      `execution-store-{env}-{pid}` (strategy-store already unified flat → gains its tier in the same move);
      positions/pnl-attribution/risk-metrics/pnl-attribution-output/archetype-state → a portfolio-state bucket. Design
      must enumerate per bucket: readers/writers to cut over (audit's shadow-registry + hardcoded-sweep tables),
      manifest/consolidator wiring, BQ `feature_external` external tables (M-1 A11 — root-mounted URIs), IAM
      write-protection re-gating ([[bucket_iam_write_protection_per_tier_2026_06_09]] Phase 2 re-gates on this),
      lifecycle rules (prefix-scoped where retention differs). — DONE 2026-07-13 (autonomous dispatch):
      plans/active/bucket_estate_fold_design_2026_07_13.md (status: draft, never ingested; 5 folds with per-site
      file:line cutover tables, 18-todo sequencing, estate math 139→~100, \_KIND_ALIASES soft-transition
      recommendation). Successor-plan destination + portfolio-state human-only + lifecycle-ladder confirm are parked as
      that doc's operator-decisions section.
- [ ] [DATA] P2. Execute the folds per design (likely 2-3 split plans for parallelism — features / ml / stores), each
      with the DeFi-migration playbook: parity verify → reader cutover → redeploy+verify-exercised → delete + TF/yaml
      removal in the same change. Target end-state ≈100 total (≈80 excluding GCP-system).
- [ ] [DOCS] P2. **Post-phase codex audit**: give the bucket-SSOT rule a live codex home (audit found
      `bucket-naming-and-config.md` superseded pointing at a CLAUDE.md section that no longer exists + CLAUDE.md
      pointing at an archived plan — fix both); update `bucket-isolation-model.md`, `gcs-lifecycle-policies.md`,
      `per-asset-group-bucket-layouts.md`; final estate re-count; flip [[bucket_env_split_rollout_2026_06]] to
      complete/superseded per its banner; close the three audit issue docs.

## Appendix A — Wave-1 deletion list (81, all confirmed empty 2026-07-13; suffix `-central-element-323112` omitted)

**Resurrected/legacy `-prod-`/`-staging-` env artifacts (32)** — TF resources must be gone first:
execution-store-{cefi,defi,prediction,sports,tradfi}-prod · features-delta-one-{cefi,defi,prediction,sports,tradfi}-prod
· features-onchain-{cefi,defi}-prod · features-volatility-{cefi,defi,prediction,sports,tradfi}-prod ·
ml-configs-store-{prod,staging} · ml-models-store-{prod,staging} · ml-predictions-store-{prod,staging} ·
ml-training-artifacts-prod · strategy-store-cefi-{prod,staging} · strategy-store-defi-{prod,staging} ·
strategy-store-{prediction,sports}-prod · strategy-store-tradfi-{prod,staging}

**Dead-scheme / retired-kind / stale-naming empties (29)**: evm-defi-test · gas-fees-test · solana-defi-test ·
features-cross-instrument-prediction · features-delta-one-prediction · features-delta-one-prediction-test ·
features-delta-one-{defi,sports,tradfi}-test · features-onchain-{cefi,defi}-test · features-volatility-prediction ·
features-volatility-prediction-test · features-volatility-{cefi,defi,sports,tradfi}-test ·
instruments-store-prediction-test · market-data-tick-prediction-test · positions-store-test (verify test-mode callers
first) · risk-store-defi-prd · strategy-store-cefi-{dev,test} · strategy-store-defi (gated on split-brain repoint) ·
strategy-store-defi-{dev,test} · strategy-store-tradfi (gated on split-brain repoint) · strategy-store-tradfi-{dev,test}

**Empty canonical dev/stg tier (20)** — retirement RULED 2026-07-13, delete with the rest:
execution-store-pred-{dev,stg} · features-pred-{dev,stg} · features-sports-{dev,stg} · instruments-store-pred-{dev,stg}
· instruments-store-sports-stg · manual-audit-{dev,stg} · market-data-tick-pred-{dev,stg} ·
market-data-tick-sports-{dev,stg} · ml-configs-store-dev · ml-models-store-dev · ml-predictions-store-dev ·
strategy-store-pred-{dev,stg}

**Explicitly NOT in Wave 1** (empty but expected-empty or compliance-scaffolded): the 13 gap buckets created
2026-07-12T02:39Z (writers exist, data pending — e.g. `position-store-sports-prd`, `execution-store-sports`),
`{pid}-client-statements`, `archetype-state-prd`, `manual-audit-prd`, `trading-audit-records-prd`, every `-test-` bucket
of a LIVE canonical kind (the smoke-check tier), and everything on the estate-cleanup never-touch list.

## Progress Log

- **2026-07-13, S1/S2 landings (autonomous tick).** `unified-api-contracts@f84e5b37` — packaged cloud-providers.yaml
  synced byte-identical to authoring SSOT (37 kinds both clouds, 10 dead kinds gone, recon present), QG green 376s, CI
  healthy; enumerate_envelope.py repointed to flat strategy-store. Follow-up in flight for the two remaining same-class
  sites the agent flagged (`gcs_paths.py:118 STRATEGY_STORE_BUCKET_TEMPLATE`, `enumerate_availability.py:43`).
  `unified-trading-library@3382cc7c` — config-store fallback now resolves kind="config-store" (function-local import;
  real circular-import risk documented), fixture yaml synced to 37 kinds, dynamic cell sweep picked up recon with no
  table edits, QG green 246s. **Data-safety finding**: flat vs prd config-store diff = prd already holds ALL real config
  md5-identical; the only flat-only object is `_tardis_concurrency_lease/lease.json` (ephemeral 900s lock, written by
  MTDS via TARDIS_CONCURRENCY_LEASE_BUCKET, currently HELD by live VM cefi-okx-swap-2022-light-20260713) → flat
  config-store bucket must NOT be deleted until that lease mechanism is repointed or the VM completes — added to
  Deferred. Also recorded for Deferred: flat config-store literals remain in instruments-service
  scripts/generate_domain_config.py:258 + system-integration-tests tests/smoke/test_cloud_infra_smoke.py:113. W3 fold
  design drafted + committed earlier this tick (pm@346af1b62, todo flipped).

- **2026-07-13, /autonomous dispatch started (operator away ~3h — "do everything possible without asking").** Staged
  execution: S1 = UAC packaged-yaml sync (36+recon=37 kinds) + enumerate_envelope flat repoint · UI strategy-store route
  repoint (catalogue/+configs/ copied cefi→flat first, server-side, verified) · W3 fold-design draft agent. S2 = UTL
  config-store resolver repoint + fixture sync · deployment-service TF reconcile (machine-verified 42-resource
  REMOVE_STALE list) + derived-from-yaml `canonical_buckets.tf` (COLDLINE@60d per ruling) + provisioning-scripts
  retirement. S3 = deployment-api store-defaults repoint · BLRS recon repoint + e2e fixtures fix. S4 = SSM ops on the
  orchestrator VM (terraform install — VM has none; state surgery: rm/mv/import per generated script; plan gate: apply
  ONLY if plan shows no unexpected create/destroy; W1 81-bucket sweep AFTER; ml legacy deletes; recon buckets arrive via
  TF apply). Decisions made under decide-and-document: `recon` = new env-tiered yaml kind (37th) — consistency with
  resolver architecture over prefix-in-existing-bucket, +2 buckets; UAC's enumerate_envelope repoint uses the flat
  literal template (UAC cannot import UTL's resolver — tier inversion); UI routes get the flat literal (TS, no
  resolver); `positions-store-test` verified code-unreachable (PATH_REGISTRY has no env axis; zero literals) → cleared
  for W1. Ship order honors tiers: UAC → UTL → deployment-service/deployment-api/BLRS; ≤2 concurrent QGs instructed.

- **2026-07-13, plan created.** Follows the same-day full estate audit (241 buckets; findings shipped as the three issue
  docs in `related:` + 2 discovery todos in the DeFi migration plan, pm@38238d3a7; env-split ruling recorded
  pm@4bd5c0765). Estate snapshot + per-bucket classification published as a session artifact; the durable subset (Wave-1
  list, counts, rulings) is inlined above so nothing depends on session scratch state.
