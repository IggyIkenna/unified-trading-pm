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

- [x] ✅ [INFRA] P0. **Terraform reconcile** (`deployment-service/terraform/gcp/main.tf` +
      `modules/shared-infrastructure/gcp/main.tf`): remove every `google_storage_bucket` resource whose bucket the
      07-10/07-12 cleanups deleted or whose name no resolver path emits — long-env Group-B blocks (main.tf:807-1357),
      legacy-kind tests gas-fees-test/solana-defi-test/ evm-defi-test (:736-799), full-word `-prediction-test-` (:353,
      :685, :970, :1151) — with matching `terraform state rm`; keep resources tracking LIVE buckets (legacy flat
      tick/instruments, the 3 dedicated DeFi `-prd` — those leave TF only in the same change that deletes the bucket,
      see W2). Until this lands: **no `terraform apply` from anyone** (each apply regrows ~30 empty buckets). Evidence
      bar — `terraform plan` shows zero bucket creates against the post-W1 estate. — DONE 2026-07-13 (autonomous
      dispatch): deployment-service@ccfaca26 (42 stale + 11 double-declare resources removed; module Group-B excised —
      `create_gcs_buckets=true` confirmed the resurrection path) + @42d4035 (manual-audit excluded: locked 220752000s
      retention forces a prevent_destroy-blocked replacement). State surgery executed on the orchestrator VM against
      terraform/state/prod (the committed backend prefix terraform/state/dev is a stub; per-env prefixes come from
      bootstrap_gcp.sh): backup → 42 rm + 11 mv + 68 import. Final targeted plan: 2 add (recon-prd/test) / 77 change / 0
      destroy / 0 replace → APPLIED (rc=0).
- [x] ✅ [INFRA] P0. **RULED 2026-07-13 — terraform derived-from-yaml**: implement one `for_each`
      `google_storage_bucket` block generated from cloud-providers.yaml's canonical (prd+test) names, import the
      existing canonical buckets into it, keep hand-written blocks only for genuine infra buckets (deployment-scripts,
      state, events, …). Document the model in `codex/05-infrastructure/bucket-isolation-model.md`. — DONE (code):
      canonical_buckets.tf shipped + applied; 79 canonical buckets under for_each (81 minus manual-audit pair, excluded
      with audit-records for locked retention); recon-prd/test created by the apply. Codex doc update rides the Deferred
      table (docs-only).
- [x] ✅ [CONFIG] P0. **Sync the stale cloud-providers.yaml copies** to the canonical 36-kind file:
      `unified-api-contracts/unified_api_contracts/config/cloud-providers.yaml` (the packaged runtime fallback — ship
      via quickmerge, this one is a real runtime divergence for standalone installs) +
      `unified-trading-pm/configs/cloud-providers.yaml`; also reconcile
      `unified-trading-library/tests/fixtures/cloud-providers.yaml` if the kind removals changed parametrized tables
      (estate-cleanup §5b lesson — grep `rg -l '<kind>'` workspace-wide, 4 copies + shadows). — DONE: UAC packaged copy
      uac@f84e5b37 (byte-identical, 37 kinds, v2 CI green); UTL fixture utl@3382cc7c (37 kinds, cell sweep auto-covers
      recon); PM mirror synced in this commit (37 kinds verified).
- [x] ✅ [INFRA] P0. **RULED 2026-07-13 — cold-tier move at 60d**: replace the untracked STANDARD→COLDLINE@14d rules
      with STANDARD→COLDLINE@60d on the data buckets, encoded in the derived-from-yaml terraform (the ONE tracked place
      per the ruling above) + update `codex/05-infrastructure/gcs-lifecycle-policies.md` (its "intentionally NOT
      lifecycle'd" claim for tick buckets is superseded). Operator verbatim "nearlcoldline nmove after 60d" — if a
      NEARLINE@60→COLDLINE-later ladder was intended instead of straight COLDLINE@60d, correct here before executing. —
      DONE: encoded in canonical_buckets.tf (STANDARD→COLDLINE@60) and APPLIED via the targeted terraform apply;
      live-verified age=60 on market-data-tick-defi-prd + instruments-store-cefi-prd (was untracked @14d).
      gcs-lifecycle-policies.md codex update rides the Deferred table.
- [x] ✅ [SCRIPT] P1. **Retire the stale provisioning surfaces** — `e2e-testing@16efd49`: deleted
      `e2e-testing/scripts/common/setup-gcp-fixtures.sh` (zero callers workspace-wide — grepped every
      `*.sh/*.py/*.yml/     *.yaml/*.md` in e2e-testing + Makefile/docker-compose/GHA, none reference it; the modern,
      actively-used SSOT replacement is `deployment-service/scripts/provision-test-buckets.sh` wrapping
      `setup-buckets.py`, already KEPT + documented below). All three sub-items now resolved: `setup-buckets.py` KEPT
      (prior tick, live consumers documented above); `setup-gcs-lifecycle-policies.sh` deleted (prior tick); e2e
      fixtures script deleted (this tick) — no other `gsutil mb`/bucket-create call exists elsewhere in e2e-testing
      (repo-wide grep clean).

## Wave 1 — delete the 81 confirmed-empty buckets (AFTER Wave-0 terraform reconcile)

- [x] ✅ [SCRIPT] P0. Delete the 81 buckets in Appendix A. Protocol per estate-cleanup precedent: re-verify emptiness
      immediately before each delete (shallow root `ls` — provably complete); zero overlap with the never-touch list;
      log per-bucket; independently re-count the estate after (expect ≈160). Two gated exceptions inside the list:
      `positions-store-test` — verify no test-mode PATH_REGISTRY caller first (the `dex-pools-test` false-positive
      precedent, estate cleanup §"false-positive caught"); `strategy-store-defi`/`strategy-store-tradfi` — delete only
      AFTER the split-brain repoint below (deployment-api defaults still reference them). — DONE 2026-07-13: 79/79
      DELETED (positions-store-test verified code-unreachable and included; the 2 strategy-store per-AG twins deferred
      to post-deployment-api-prod-redeploy). Per-bucket re-verify-empty → delete → 404-verify log:
      gs://deployment-scripts-central-element-323112/migration-bundle/staging/w1_deletion_log_2026_07_13.tsv. Estate
      independently re-counted: 241 → 164 (−79 +2 recon).
- [x] ✅ [OPERATOR] P1. **RULED 2026-07-13 — retire BOTH dev/stg tiers** (operator answer to the audit question set; 20
      of 21 canonical dev/stg buckets empty). Remaining action rides the W1 delete todo above; the sole content-bearing
      exception `instruments-store-sports-dev` gets inspect + migrate/drop there. Resolver keeps supporting the tiers;
      we just stop keeping empty buckets for them.

## Wave 2 — in-flight completions + audit-found breakages (estate ≈139 after)

- [ ] [DATA] P0. **recon bucket** ([[recon_bucket_missing_nightly_recon_failing_2026_07_13]]) — PARTIAL 2026-07-13: kind
      `recon` added to all 4 yaml copies (autonomous decide-and-document: env-tiered kind over prefix); recon-prd/test
      buckets created via terraform apply; BLRS config resolver-repointed blrs@2f0380b (v2 green); launcher doc fixed
      (ds@ccfaca26). REMAINING: prod image pickup (rides the automated BASE_IMAGE_DIGEST fan-out + LDR→main promote),
      the upstream t1-recon ML/strategy producer chain (never ran anywhere — job stage0 will still gate until producers
      write \_SUCCESS markers), green scheduled run, Cloud Run failure alerting. Original todo: operator decides kind vs
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

## Deferred work after 2026-07-13 (autonomous dispatch session end)

| #   | Item                                                                                                                                                                                                             | Why deferred                                                                                                                                                                                                                                 | Unblock condition / next step                                                                                                                                                        |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 1   | Delete `strategy-store-{defi,tradfi}-{pid}` (empty) + retire `strategy-store-cefi-{pid}` (content copied to flat; verify staleness dedupe first)                                                                 | prod deployment-api still runs pre-6da793b defaults until redeployed                                                                                                                                                                         | after deployment-api prod redeploy; then gcloud delete + confirm catalogue regen writes flat                                                                                         |
| 2   | Delete flat ml trio (`ml-models-store`, `ml-configs-store`, `ml-predictions-store` `-{pid}`)                                                                                                                     | UTL PATH_REGISTRY ml rows still resolve the flat names (live deployment-api data-status readers)                                                                                                                                             | W3 ml fold (bucket_estate_fold_design_2026_07_13) repoints PATH_REGISTRY; delete then                                                                                                |
| 3   | Delete flat `config-store-{pid}`                                                                                                                                                                                 | MTDS `TARDIS_CONCURRENCY_LEASE_BUCKET` writes an ephemeral lease there; live Tardis VM held it at check time; 2 more flat literals: instruments-service scripts/generate_domain_config.py:258, SIT tests/smoke/test_cloud_infra_smoke.py:113 | repoint lease env default + 2 literals, wait for VM completion, then delete (prd copy verified md5-identical for all durable config)                                                 |
| 4   | recon end-to-end green run                                                                                                                                                                                       | upstream t1-recon ML/strategy producers never ran anywhere; BLRS prod image needs digest fan-out + main promote                                                                                                                              | investigate producer chain per issue doc fix-direction #3; then `gcloud builds triggers run batch-live-reconciliation-service-build --branch=main`; verify 06:00Z run; wire alerting |
| 5   | Non-bucket terraform drift (7 undeployed adds: odum_portal domain mapping, 2 scheduler crons, 2 Cloud Run jobs; ~36 Cloud Run job in-place changes; 2 catalogue-IAM replacements riding the flat-bucket repoint) | pre-existing drift outside tonight's bucket scope; targeted apply deliberately excluded it                                                                                                                                                   | operator review + full `terraform apply` from deployment-service@42d4035 (safe for buckets now — plan gate: 0 bucket destroys)                                                       |
| 6   | W2 checkpoint deletions owned by other plans: dex-pools/lst-rates/perp-funding-prd (−3), lending-indices pair (−2), legacy flat tick/instruments twins (−8, L6 operator-gated), football ×4, ASTER originals     | owned by defi_dedicated_bucket_shared_migration / M-1 L6 / operator rulings — deliberately not force-run tonight                                                                                                                             | those plans' own gates                                                                                                                                                               |
| 7   | Codex doc updates: bucket-isolation-model.md (derived-from-yaml model), gcs-lifecycle-policies.md (COLDLINE@60d supersedes "not lifecycle'd")                                                                    | docs-only, end of dispatch window                                                                                                                                                                                                            | mechanical edit + prek commit                                                                                                                                                        |
| 8   | setup-buckets.py + bucket_config.yaml resolver rewrite                                                                                                                                                           | live consumers (setup-dev-project.sh, provision-test-buckets.sh, SIT conftest); rewrite exceeds blast radius                                                                                                                                 | W3 or dedicated small plan                                                                                                                                                           |
| 9   | UAC `mapping_resolver.py` hardcoded `instruments-store-sports-test-project` (broken name, live package code) + UI vendored copy                                                                                  | found by audit, out of tonight's repo scopes                                                                                                                                                                                                 | small fix + ship                                                                                                                                                                     |
| 10  | `ml_jobs_ikenova`-class ops singletons registration (honest-coverage/phantom-triage/rescan-triage/benchmark-reports/deployment-events)                                                                           | W2 P2, not reached                                                                                                                                                                                                                           | fold-or-register per W3 design §ops                                                                                                                                                  |

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

- **2026-07-13, S3 BLRS recon repoint + e2e fixtures fix landed (autonomous tick).**
  `batch-live-reconciliation-service@2f0380b` — `config.py` repointed: `recon_bucket` now
  `resolve_bucket_name(kind="recon")` (the fix for [[recon_bucket_missing_nightly_recon_failing_2026_07_13]]'s broken
  default), `events_bucket` → `kind="events"` and `execution_store_bucket` →
  `kind="execution-store", asset_group="cefi"` (both behavior-identical refactors — verified via direct import:
  local-mode f-string fallback preserved byte-for-byte for `test_config.py`'s assertions; GCP/prod mode resolves
  `recon-prd-central-element-323112` / `central-element-323112-events` / `execution-store-cefi-central-element-323112`;
  `RECON_BUCKET` env override still wins). Extracted `_derive_cross_cutting_buckets()` to keep `model_post_init` under
  the 50-line method-size ceiling (the inline version hit 59L, a new codex-compliance violation). QG green (45s),
  quickmerge → live-defi-rollout. **Image rebuild/redeploy path for whoever runs Stage 5** (this fix does NOT reach the
  prod Cloud Run job until the image is rebuilt with a base image that carries the recon kind): verified live via
  `gcloud builds`/`gcloud artifacts` — UTL's own Cloud Build trigger `unified-trading-library-live-defi-rollout` clones
  **UAC's `live-defi-rollout` branch directly** (not `main`) in its `clone-uac-source` step, so it already picked up
  `unified-api-contracts@f84e5b37` (the recon-kind yaml) the moment that trigger next fired — build `dcfbc5c0`
  (2026-07-13 20:17:42→20:24:19Z) SUCCEEDED and produced base image digest
  `sha256:3772351a7fb24893860373aaa1aa9e9136c76e67aadaa03834b7cc1d74b720c4` (confirmed = current
  `unified-trading-library:latest`). BUT `batch-live-reconciliation-service/Dockerfile:5`'s `ARG BASE_IMAGE_DIGEST=` is
  still pinned to `sha256:b7e391f8...` — the PRIOR base build (17:37→17:44Z), which predates the recon-kind fix
  (confirmed by commit timestamps: base-pin-bump commit landed 20:05:01Z, UAC's recon-kind commit landed 20:11:34Z — so
  `sha256:b7e391f8` does NOT contain it). **So: my config.py fix + a fresh BLRS Cloud Build alone is NOT sufficient —
  the Dockerfile digest pin must be bumped to `sha256:3772351a...` FIRST** (or to whatever
  `unified-trading-library:latest` digest is current at execution time — re-verify with
  `gcloud artifacts docker images describe asia-northeast1-docker.pkg.dev/central-element-323112/unified-trading-library/unified-trading-library:latest --format='value(image_summary.digest)'`),
  then a BLRS rebuild picks up both the digest bump and this commit. BLRS's own Cloud Build trigger
  (`batch-live-reconciliation-service-build`) fires automatically on push to **`main`** (not LDR) — so once the
  Dockerfile bump + this fix are both promoted LDR→main (existing Tier-C drain, ≤15min, or force via `gh workflow run`
  on the promote workflow), the image rebuild is automatic; no manual `gcloud builds submit` needed. If a synchronous
  rebuild is wanted instead:
  `gcloud builds triggers run batch-live-reconciliation-service-build --branch=main --project=central-element-323112 --region=asia-northeast1`.
  The Cloud Run JOB `uts-prod-batch-live-reconciliation-service` was NOT inspected for how it picks up the new image
  (tag vs digest pin) — that's the remaining unknown for Stage 5 to confirm before/after the rebuild.
  `e2e-testing@16efd49` — `scripts/common/setup-gcp-fixtures.sh` **DELETED** (not fixed): grepped every
  `*.sh/*.py/*.yml/*.yaml/*.md` in e2e-testing + Makefile/docker-compose/GHA workflows, zero callers anywhere (its own
  `teardown.sh` doesn't even reference the same bucket names); the canonical, actively maintained replacement already
  exists and is already KEPT/wired to the yaml SSOT: `deployment-service/scripts/provision-test-buckets.sh` wrapping
  `setup-buckets.py` (derives `-test-` siblings from `dependencies.yaml`+`cloud-providers.yaml`, `--test-only` never
  touches prod). Repo-wide grep for other `gsutil mb`/bucket-create calls in e2e-testing: clean (only this one file had
  any). Wave-0 "retire the stale provisioning surfaces" todo flipped — all 3 sub-items (setup-buckets.py KEPT,
  setup-gcs-lifecycle-policies.sh deleted, e2e fixtures deleted) now resolved. QG green (43s), quickmerge →
  live-defi-rollout.

- **2026-07-13, S4 COMPLETE + S5 bookkeeping (autonomous tick).** Targeted terraform apply SUCCEEDED on the orchestrator
  VM (gate: 2 add / 77 change / 0 destroy / 0 replace): recon-prd/test created, COLDLINE@60d live on all 79 canonical
  for_each buckets (verified age=60 on tick-defi-prd + instruments-cefi-prd), 2 catalogue-IAM replacements deferred with
  the non-bucket drift. manual-audit discovered retention-LOCKED (220752000s) at first live plan → excluded from
  for_each beside audit-records (ds@42d4035, QG green). W1 sweep: **79/79 DELETED**, 0 failures, per-bucket
  re-verify-empty + 404-verify, log uploaded to deployment-scripts staging. **Estate: 241 → 164.** State surgery final
  tallies: 42 rm + 11 mv + 68 import after the generated script's guards mis-skipped (fixed deterministically by
  classifying the plan's own destroy list). PM mirror yaml synced (37 kinds) in this commit. Deferred table added below
  (10 items with unblock conditions).

- **2026-07-13, S3 landings + S4 state-surgery iteration (autonomous tick).** `deployment-api@6da793b` — strategy-store
  defaults collapse to flat via resolver (all 3 per-AG props), execution-store default → CEFI (decide-and-document: sole
  consumer is a global /config-buckets entry with no AG context; CEFI is the only live-traffic AG), ml-configs-store →
  env-tiered resolver; +1 live dead literal fixed in commentary/pipeline_uat.py. QG 86s green.
  `batch-live-reconciliation-service@2f0380b` (v2 SUCCESS) — recon/events/execution-store resolved via canonical
  resolver; prod-mode now resolves recon-prd-{pid}. **S5 dependency discovered**: BLRS image reaches prod only after its
  Dockerfile BASE_IMAGE_DIGEST pin is bumped past the 20:24Z base build (which carries uac@f84e5b37) AND its main-push
  trigger fires — manual: `gcloud builds triggers run batch-live-reconciliation-service-build --branch=main`.
  `e2e-testing@16efd49` (v2 SUCCESS) — setup-gcp-fixtures.sh DELETED (zero callers; canonical replacement =
  provision-test-buckets.sh); W0 provisioning-surfaces checkbox flipped by that agent (pm@a1ff00f5c). **S4 terraform
  surgery** (orchestrator VM, deployment-service@ccfaca26 clone, prod state terraform/state/prod — the committed backend
  prefix terraform/state/dev is a stub; per-env prefixes are passed by bootstrap_gcp.sh): state backed up; 68 canonical
  imports OK; generated script's rm/mv guards mis-skipped → plan showed 55 destroys/20 adds and was correctly GATED (not
  applied). Deterministic fixer now re-classifying every planned bucket destroy into state-rm (stale) vs state-mv
  (canonical rename) from the plan log itself; re-plan gate: creates = recon-prd/test only, zero bucket destroys,
  changes = COLDLINE@60d lifecycle/labels. Apply will be TARGETED at google_storage_bucket.canonical (+ catalogue
  scheduler) — the plan also surfaced pre-existing non-bucket drift (odum_portal domain mapping, 2 cron jobs, 2 Cloud
  Run jobs undeployed from config) which is NOT tonight's scope → Deferred. W1 sweep staged: 79 names
  (strategy-store-{defi,tradfi} deferred to post-deployment-api-redeploy).

- **2026-07-13, S2/S3 landings + S4 started (autonomous tick).** `deployment-service@ccfaca26` (+266/−1547) — TF
  reconcile: 42 REMOVE_STALE + 11 double-declare hand blocks removed; module Group-B section removed (module WAS live:
  `create_gcs_buckets = true` in terraform/shared/gcp/terraform.tfvars — the resurrection mechanism confirmed + closed);
  dangling outputs fixed; `canonical_buckets.tf` shipped (yamldecode-driven for_each, 81 canonical prd+test names,
  COLDLINE@60d, prevent_destroy); `tf_state_surgery.sh` generated (59 rm / 11 mv / 68 import / 2 create, guarded,
  syntax-checked); setup-buckets.py + bucket_config.yaml KEPT (live consumers found: setup-dev-project.sh,
  provision-test-buckets.sh, SIT conftest + smoke — full resolver rewrite deferred, documented);
  setup-gcs-lifecycle-policies.sh deleted; recon launcher header fixed; catalogue_regen_scheduler.tf repointed to flat
  strategy-store (3 sites). `unified-trading-system-ui@2796d38b` — both catalogue routes repointed to flat bucket
  (content verified present first); +`@1bf1bc1a` pre-existing gate blocker fixed (capability-verdict-matrix sync);
  issue-doc UI leg flipped (pm@71c9dfb1c by the agent). `unified-api-contracts@155093a1` —
  STRATEGY_STORE_BUCKET_TEMPLATE
  - enumerate_availability repointed; facade test updated; v2 CI GREEN on that exact SHA (run 29282411405); agent
    verified MDPS BaseDependencyChecker consumes generic_bucket_template, NOT strategy_store_bucket — unaffected. S4 in
    flight: terraform 1.5.7 installed on orchestrator VM, deployment-service@ccfaca26 cloned there, state surgery
    (backup → 59 rm → 11 mv → 68 import) + plan running; apply gated on plan showing ONLY recon-prd/test creates +
    lifecycle/label updates on canonical buckets, NO bucket destroys.

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
