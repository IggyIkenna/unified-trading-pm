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
last_updated: "2026-07-14"
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
      we just stop keeping empty buckets for them. — `instruments-store-sports-dev` sub-item DONE 2026-07-14: full
      investigation + retirement, see Progress Log entry "instruments-store-sports-dev full retirement".

## Wave 2 — in-flight completions + audit-found breakages (estate ≈139 after)

- [ ] [DATA] P0. **recon bucket** ([[recon_bucket_missing_nightly_recon_failing_2026_07_13]]) — UPDATED 2026-07-14 (this
      session, see item D in the Round-2 table + Progress Log for full detail): prod image pickup is now DONE + verified
      (BLRS's Dockerfile needed a SECOND digest bump — the first landed a UTL base image whose bundled UAC snapshot
      predated the actual recon-kind commit by ~3.5h; `blrs@be056b1` fixes it, live-verified via a real triggered
      execution that Stage 0 now resolves the bucket correctly and gates on the RIGHT, already-documented reason). The
      upstream t1-recon ML/strategy producer chain investigation is COMPLETE and the finding is precisely scoped:
      execution-service's config-snapshot job and ml-service's t1-recon job were BOTH NEVER PROVISIONED (Cloud Scheduler
      fires daily into a 404); strategy-service's job existed but its container-exec config was broken (FIXED this
      session, `ds` terraform + a direct `gcloud run jobs update` — now runs but hits a missing required `--date` arg
      one layer deeper); no producer in this chain (ml or strategy) implements the `--run-tag`/`_SUCCESS`-marker writer
      convention at all (ml-service parses a dead `--run-tag` flag that nothing consumes; strategy-service has no such
      flag). Standing up the real end-to-end chain is multi-repo feature work
      (execution-service/ml-service/strategy-service/features-service) — OUT OF SCOPE for this plan, left as a
      precisely-characterized open item. Cloud Run failure alerting (55 silent failures) remains untouched — not reached
      this session, still open. Original todo: operator decides kind vs prefix; provision; repoint
      `batch_live_reconciliation_service/config.py` to the resolver; fix launcher doc; end-to-end T1 chain run; next
      scheduled run green; wire Cloud Run failure alerting (55 silent failures).
- [x] ✅ [CODE] P1. **strategy-store split-brain** ([[strategy_store_split_brain_2026_07_13]]) — DONE 2026-07-13/14: all
      code legs shipped (uac@f84e5b37+@155093a1, ui@2796d38b, dapi@6da793b, ds catalogue scheduler @ccfaca26);
      deployment-api prod VERIFIED live-serving flat (revision 00158-m5x); catalogue/+configs/ copied to flat; cefi
      residuals (105 obj) preserved at flat legacy_cefi/; strategy-store-{cefi,defi,tradfi} buckets DELETED. Original:
      repoint deployment-api defaults + UI catalogue route + `enumerate_envelope.py` to the flat kind;
      migrate-or-regenerate the cefi bucket's `configs/` + `catalogue/`; then retire
      `strategy-store-{cefi,tradfi,defi}-{pid}` (cefi last) + their TF resources.
- [x] ✅ [CODE] P1. **config-store split-brain** — DONE 2026-07-14:
      `unified_trading_library/config_interface/__init__.py` was already resolver-backed (pre-existing `3382cc7c`,
      confirmed live re-read, not newly fixed this pass). Flat bucket deleted (by a concurrent session executing the
      same dispatched migrate-then-delete instructions — see `data_completion_to_100_all_ag_2026_06_21.md`'s 2026-07-14
      entry for the full re-verification + a documented near-miss: the delete ran ~4.7 min ahead of the VM-completion
      gate, assessed fail-open/no-crash from source but not the documented safe order). Remaining 2 literals repointed +
      1 newly-found `bucket_config.yaml` provisioning entry retired this session: instruments-service@0782f9af,
      system-integration-tests@36d7654, deployment-service@7485657. Original: flat `config-store-{pid}` AND canonical
      `config-store-prd-{pid}` both exist with content; `unified_trading_library/config_interface/__init__.py:170` +
      `bucket_config.yaml` still emit the flat name. Repoint to resolver, verify hot-reload consumers, migrate + retire
      the flat bucket.
- [ ] [DATA] P0. Track to completion the deletions OWNED BY OTHER PLANS (checkpoint; UPDATED 2026-07-14: DeFi trio —
      parity re-verified by agent incl. closing a 6,941-object gap, lst-rates-prd + perp-funding-prd DELETED,
      dex-pools-prd purge-lifecycle armed (24h async; disarm window if concerns), kinds removed from all 5 yaml copies
      (34), TF state clean; L6 twins — cefi/defi/tradfi tick+instruments purge-lifecycle armed (sports pair HELD for
      sports-plan E1/E8; bucket deletes = follow-up one-liner once purged); lending pair still HELD — Morpho VM
      completed but write-target verification inconclusive): `dex-pools-prd`/`lst-rates-prd`/`perp-funding-prd` (−3,
      [[defi_dedicated_bucket_shared_migration_2026_07_13]] todos 6-9 incl. the TF-resource removal added 2026-07-13);
      `lending-indices`+`-prd` (−2, same plan / estate cleanup §5i, gated on VM `mtds-lending-indices-20260712-112557`
      completion); legacy flat tick+instruments twins (−8, M-1 `data_completion_to_100_all_ag_2026_06_21` L6,
      operator-gated version-aware deletes — millions of noncurrent versions).
- [x] ✅ [OPERATOR] P1. **football-\* (4 buckets)** — RULED + DONE 2026-07-14: migrated count-verified into canonical
      homes (backtest-results/football 455 obj; ml-models-store-prd/legacy_football 119;
      instruments-store-sports-prd/legacy_football/{mapped_consolidated 107, raw_all_sources 37}) and all 4 deleted.
      Original: no canonical destination existed (estate cleanup §5g): rule archive-tier-and-dated-delete vs migrate
      `odds/`+`parquet_backup/` into the sports pipeline first.
- [ ] [DATA] P1. **ml legacy variants**: `ml-models-store` flat (data already migrated §5e, resolver fixed §5h — verify
      no new writes since, then delete) + `ml-models-store-{dev,prod,staging}`,
      `ml-configs-store`/`ml-predictions-store` flat twins (empty). Verify
      `deployment-api/deployment_api_config.py:642`'s flat `ml-configs-store-{pid}` default is repointed first.
- [x] ✅ [DATA] P2. Disposition the 4 ops-tooling buckets found unregistered (`{pid}-honest-coverage`,
      `{pid}-phantom-triage`, `{pid}-rescan-triage`, `{pid}-benchmark-reports`): register (yaml kind or documented infra
      list) or fold into `{pid}-data-status-rollups` prefixes; same for `{pid}-deployment-events` (live QG snapshots,
      unregistered). — DONE 2026-07-14: registered all 5 (documented infra list, the simplest-correct option per this
      todo — not a new yaml-kind scheme for 5 one-off singletons) in `bucket_config.yaml`'s `infrastructure_buckets.gcp`
      list, mirroring the terraform-state/deployment-orchestration/build-metadata entries already there —
      deployment-service@2246e11. Full QG green (`bash scripts/quality-gates.sh --no-fix`).

- [x] ✅ [CODE] P1. **Asset-group parity sweep — 12 producer-less feature buckets deleted + the class gated shut**
      (operator-raised 2026-07-17: "why do these intuitively exist, is there even code paths to them"). Root cause:
      `cloud-providers.yaml` declares feature kinds as per-asset-group dicts, and BOTH provisioning surfaces
      (`setup-buckets.py`, `terraform/gcp/canonical_buckets.tf`'s `for_each`) enumerate the YAML keys — never the code.
      Nothing tied the two together, so invented combinations became live orphan buckets that look identical to
      real-but-empty ones. The retired `bucket_config.yaml` `validation.invalid_combinations` block had hand-encoded one
      fragment of the rule ("No volatility for DEFI") and was deleted as dead config in item 8 above — this restores it
      as a derived gate.

  - **⚠️ CORRECTION MID-TASK — READ THIS BEFORE TRUSTING ANY "orphan asset_group" CLAIM.** This sweep FIRST ran with
    `scripts/<family>/smoke_matrix.py`'s `SUPPORTED_ASSET_GROUPS` as its authority and, on that basis, wrongly deleted
    `features-xinstrument-defi` (both clouds). **That constant is the SMOKE-TEST COVERAGE list, not the family's
    capability** — note `ALL_ASSET_GROUPS` declared beside it. cross-instrument's CLI accepts DEFI and
    `cli/handlers/batch_handler.py::_ingest_delta_one` explicitly serves "CEFI/TRADFI/DEFI"; the bucket was empty
    because DeFi cross-instrument had never been RUN, which is NOT evidence it cannot be. Caught by
    `tests/cross_instrument/unit/test_service_startup.py` failing in QG. **Fully restored**: buckets recreated on GCP +
    AWS with sibling-matching settings (asia-northeast1/ap-northeast-1, STANDARD, uniform access, AES256, COLDLINE@60d
    lifecycle — verified identical to `features-xinstrument-cefi-*`), yaml keys restored in all 5 copies, test
    re-passes. Nothing lost (empty). Gate REBUILT on the correct authority: the family's **CLI `asset_group_choices`** —
    the set the family can be invoked for, hence the set `resolve_bucket` is called with. NOTE the 2026-07-10
    `features-mtf` PREDICTION/SPORTS removal made the SAME mistake citing the same constant — outcome later confirmed
    correct by operator ruling, but the reasoning was unsound and left a real week-long bug (below).
  - **6 orphan keys × 2 clouds = 12 buckets DELETED** (each re-verified empty immediately before delete + 404-verified
    after, per the W1 estate-cleanup protocol; per-bucket log:
    gs://deployment-scripts-central-element-323112/migration-bundle/staging/asset_group_parity_deletion_log_2026_07_17.tsv
    — that log records the pre-correction 14; `features-xinstrument-defi` GCP+AWS were subsequently restored):
    `features-volatility-{defi,pred,sports}` (operator ruling: no DeFi options, no sports options),
    `features-xinstrument-sports`, `features-delta-one-sports`, `features-onchain-cefi`. The last two were NOT in the
    operator's list — the sweep found them. `features-mtf-defi` was checked and KEPT (MTF genuinely supports DEFI; empty
    only because DeFi MTF has never run).
  - **+2 more: the 2026-07-10 sweep's unfinished AWS side.** That sweep deleted `features-mtf-{pred,sports}` on GCP but
    left the AWS twins (`features-mtf-pred-427895769566`, `features-mtf-sports-427895769566`) alive with no yaml key —
    unregistered and invisible, the exact state this plan exists to eliminate. Both confirmed empty and deleted under
    the same operator ruling. **The AWS per-AG features estate now matches `aws.storage` in cloud-providers.yaml
    EXACTLY** (set-diff verified, zero residue) — the strongest end-state check available, and the reason the AWS twins
    surfaced.
  - **CLI choices corrected at source** (the accepted-but-unserveable surface is what justified provisioning these):
    `volatility/cli/parser.py` ASSET_GROUP_CHOICES dropped DEFI (operator ruling — it accepted DEFI despite there being
    no DeFi options); `multi_timeframe/cli/main.py` dropped PREDICTION. The latter fixes a **live latent bug**: the
    2026-07-10 sweep deleted `features-mtf-pred` + its yaml key but left the CLI advertising `--asset-group PREDICTION`,
    so that shard had been dying mid-run on `BucketNamingError` for a week. The corrected gate surfaced it on its first
    run — exactly the MISSING direction it exists to catch.
  - **`features-onchain-cefi` was operator-ruled** (only non-empty one: 2 regenerable consolidator `_index/` artifacts,
    no payload; unreachable 3 ways — `onchain/config.py:22` hardcodes `_ONCHAIN_ASSET_GROUP="defi"` and
    `get_output_bucket()` ignores its asset_group arg, deployment-api scopes the service to `frozenset({"DEFI"})`,
    openapi.json documents "only ships defi"); its live Cloud Run job + cron
    (`uts-prod-manifest-consolidator-features-onchain-cefi[-cron]`) were consolidating a bucket no producer ever wrote
    to — both deleted via gcloud + the TF `manifest_consolidator_buckets_extended` entry removed (gas-fees precedent),
    catalog regenerated 24→23.
  - **Second-SSOT drift fixed**: all 3 `dependency_checker.py` `OUTPUT_BUCKETS`/`_TEST` ClassVars were hardcoded
    duplicates of the bucket-name SSOT that nothing read — which is why their errors survived (delta_one named
    `features-delta-one-prediction-{pid}`, a bucket that has NEVER existed — real name is `-pred-`; onchain named the
    legacy flat bucket + offered CEFI/TRADFI for a DeFi-only family; volatility carried a dead DEFI entry + `_TEST`
    twins naming `-test-` buckets absent from the estate). All deleted; volatility now delegates to
    `VolatilityServiceConfig.get_output_bucket()` (what every production writer already used) and its now-inert
    `project_id` param was removed rather than left silently ignored.
  - **Gate**: QG STEP 5.104 `features-service/scripts/quality_gates/check_asset_group_parity.py` — AST-reads each
    family's **CLI `asset_group_choices`** (NOT the smoke matrix; the docstring's Authority section carries the full
    warning + the cross-instrument worked example so nobody re-points it), resolves the constant refs (`CATEGORIES`,
    `ASSET_GROUP_CHOICES`) and the one constant-authority family (onchain pins `_ONCHAIN_ASSET_GROUP="defi"`, no CLI
    choice), checks the UAC-packaged yaml the resolver actually resolves through, and fails BOTH directions — EXTRA key
    = orphan bucket, MISSING key = runtime `BucketNamingError`. Proven four ways: exit 0 on the corrected tree; exit 1
    catching all 14 violations on the pre-fix yaml (`git show HEAD:configs/cloud-providers.yaml`); exit 1 on a kind
    deleted from BOTH clouds (a silent-pass hole found + closed during review — `declared is None` used to `continue`);
    exit 2 on unreadable inputs (never a silent pass).
  - **Two pre-existing features-service test failures fixed to reach a genuinely green tree** (both proven pre-existing
    by stashing this session's changes and re-running; both the same shape as the bug above — a stale assumption nobody
    rechecked): (1) `tests/sports/.../test_run_new_calculators_coverage_gate.py` asserted transfermarkt PLAYER_VALUES
    coverage starts 2019-01-01 and probed 2018-06-01 expecting `out_of_coverage`; the real registered start is
    2018-01-01, so the gate correctly ran the calculator — code was right, test was stale. Rewritten to DERIVE the
    pre-launch date from the UAC window (public `unified_api_contracts.sports` surface, not a deep `canonical.*` path) +
    added the missing in-coverage boundary case. (2) `tests/multi_timeframe/unit/test_orchestrator.py` — a UNIT test
    issuing REAL GCS uploads to `features-mtf-cefi-test-project`: `run_batch`'s `_write_batch_manifest` constructs its
    own `ManifestWriter`, bypassing the injected storage mock, and its
    `except (ValueError, OSError, RuntimeError, KeyError, TypeError)` doesn't cover
    `google.api_core.exceptions.NotFound`, so the 404 escaped whenever ADC creds were present (hence "flaky"; green in
    CI). Patched module-wide per the onchain precedent; suite 55s → 20s with the network calls gone.
  - **SHIPPED 2026-07-17** — `unified-api-contracts@ee8ea8f0` (packaged yaml, the copy the resolver resolves through) ·
    `unified-trading-library@449d4142` (fixture + the probe-asset_group refactor) · `deployment-service@c8f96e6` (yaml +
    the onchain-cefi consolidator TF entry) · `deployment-api@911e889` (catalog 24→23, `--check` clean) ·
    `unified-trading-pm@cba911b42` (PM yaml + ci-test mirror + the bandit-timeout fix) · `features-service@d98a1fdc`
    (via quickmerge — `Quickmerge: agent` trailer verified present, so it will not provenance-block the LDR→main
    promote; 19 files, zero foreign files swept in). Evidence: yaml byte-identical across all 4 full copies + the UTL
    fixture; **features-service QG: ALL QUALITY GATES PASSED — 17558 passed / 209 skipped, STEP 5.104 green**; **UTL QG:
    ALL QUALITY GATES PASSED** (green only AFTER the bandit fix below). **The AWS per-asset-group features estate now
    set-diffs EXACTLY against `aws.storage` — zero residue.**
  - **Bonus fix shipped in the same pass (`unified-trading-pm@cba911b42`)**: `base-library.sh` / `base-service.sh` ran
    bandit under `run_timeout 30`, but a full clean UTL scan measures ~52s (Medium 0 / High 0, exit 0). The kill lands
    in the `||` branch and the gate prints "❌ bandit issues" + V++ — a TIMEOUT reported as a SECURITY FINDING. Any
    cache-miss run on a loaded host failed the repo for a vulnerability that does not exist; UTL's gates were red for
    this reason alone, fleet-wide, for any library repo. Raised to 180s with the failure mode documented so the next
    reader does not chase a phantom vuln.
  - **2 issues filed (`unified-trading-pm@4a7816269`)**: [[promotion_lag_alert_hides_provenance_block_2026_07_17]] (the
    "PROMOTION LAG" alert is really a provenance hold — the bot is right, the alert wording sends responders at green
    CI; offender market-tick-data-service@d302f07a) and [[slot_branch_realign_discards_uncommitted_worktree_2026_07_17]]
    (the resolved slot-11 fix is keyed on AHEAD COMMITS, so a dirty tree with 0 ahead commits gets no guard at all —
    mechanism marked NOT PROVEN, reproduce first; agent-orchestrator deliberately not modified). Residual cosmetic drift
    → its own P2 todo below.

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
- [ ] [CONFIG] P2. **Residual asset-group-parity drift the 2026-07-17 sweep found but left** (all cosmetic/waste, none
      blocking; the GCP live path is fully reconciled): (a)
      `deployment-service/terraform/aws/manifest_consolidator_scheduler.tf:35` + `terraform/aws/main.tf:74` still
      declare `features-onchain-cefi` against the LEGACY `unified-trading-features-onchain-cefi-*` AWS names — same
      producer-less finding as the GCP side, but it points at legacy buckets that still exist, so it wastes a
      consolidator rather than 404-ing; fold into the dev/stg-tier retirement (item above) rather than a standalone
      apply. (b) PM catalogue placeholders naming deleted buckets:
      `configs/data-catalogue.features-volatility-service.yaml:102` (`features-volatility-defi-test-project`),
      `configs/data-catalogue.features-onchain-service.yaml:35`, `configs/checklist.prerequisites.yaml:173,400`,
      `configs/services/features-volatility-service/batch.env:12`
      (`PROTOCOL_DATA_SINK_BUCKET_DEFI=uts-prod-features-volatility-defi` — a `uts-prod-*` shape matching no live
      bucket, so likely dead already: confirm before editing). (c) legacy one-off migration scripts still listing the 7
      deleted names (`deployment-service/scripts/archive-flat-buckets.sh`,
      `scripts/aws/migrate-bucket-names-unified-to-canonical.sh`) — these are historical records of an executed
      migration; decide delete-vs-annotate per the one-off lifecycle rule rather than editing in place.
- [ ] [DOCS] P2. **Post-phase codex audit**: give the bucket-SSOT rule a live codex home (audit found
      `bucket-naming-and-config.md` superseded pointing at a CLAUDE.md section that no longer exists + CLAUDE.md
      pointing at an archived plan — fix both); update `bucket-isolation-model.md`, `gcs-lifecycle-policies.md`,
      `per-asset-group-bucket-layouts.md`; final estate re-count (corrected 2026-07-15, plan-reconcile:
      [[bucket_env_split_rollout_2026_06]] already flipped to status: superseded / archived same-day per line-68 banner,
      so that sub-clause is dropped as done); close the three audit issue docs.

## Deferred work after 2026-07-13 (autonomous dispatch session end)

| #                                                                                                                        | Item                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Why deferred                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | Unblock condition / next step                                                                                                                                                                                                                                                                                                                                                                                                          |
| ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1                                                                                                                        | ~~Delete `strategy-store-{defi,tradfi}-{pid}` + retire `strategy-store-cefi-{pid}`~~ — DONE 2026-07-14: deployment-api prod verified serving flat (rev 00158-m5x); cefi 105 residuals preserved to flat `legacy_cefi/`; all 3 buckets deleted                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | prod deployment-api still runs pre-6da793b defaults until redeployed                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | after deployment-api prod redeploy; then gcloud delete + confirm catalogue regen writes flat                                                                                                                                                                                                                                                                                                                                           |
| 2                                                                                                                        | Delete flat ml trio (`ml-models-store`, `ml-configs-store`, `ml-predictions-store` `-{pid}`)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | UTL PATH_REGISTRY ml rows still resolve the flat names (live deployment-api data-status readers)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | W3 ml fold (bucket_estate_fold_design_2026_07_13) repoints PATH_REGISTRY; delete then                                                                                                                                                                                                                                                                                                                                                  |
| 3                                                                                                                        | ~~Delete flat `config-store-{pid}`~~ — DONE 2026-07-14 (see `data_completion_to_100_all_ag_2026_06_21.md`'s 2026-07-14 entry): deleted by a concurrent session executing the same dispatched instructions (~4.7 min ahead of the VM-completion gate below — documented as a near-miss, assessed no-crash from source, not the documented safe order); 2 literals + 1 newly-found `bucket_config.yaml` provisioning entry repointed this session (instruments-service@0782f9af, system-integration-tests@36d7654, deployment-service@7485657)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | MTDS `TARDIS_CONCURRENCY_LEASE_BUCKET` writes an ephemeral lease there; live Tardis VM held it at check time; 2 more flat literals: instruments-service scripts/generate_domain_config.py:258, SIT tests/smoke/test_cloud_infra_smoke.py:113                                                                                                                                                                                                                                                                                                                                                                                                   | ~~repoint lease env default + 2 literals, wait for VM completion, then delete~~ (prd copy verified md5-identical for all durable config) — CLOSED                                                                                                                                                                                                                                                                                      |
| 4                                                                                                                        | recon end-to-end green run — SUPERSEDED, see item D in the Round-2 table + Progress Log (2026-07-14): BLRS prod image pickup DONE + verified; producer-chain investigation COMPLETE (2 missing Cloud Run Jobs + a never-implemented run-tag/\_SUCCESS convention across the chain) and precisely scoped as genuinely out-of-plan multi-repo feature work; Cloud Run failure alerting still not reached                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | upstream t1-recon ML/strategy producers never ran anywhere; BLRS prod image needs digest fan-out + main promote                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                | investigate producer chain per issue doc fix-direction #3; then `gcloud builds triggers run batch-live-reconciliation-service-build --branch=main`; verify 06:00Z run; wire alerting                                                                                                                                                                                                                                                   |
| 5                                                                                                                        | ~~Non-bucket terraform drift~~ — MY-DRIFT PORTION RECONCILED 2026-07-14 (see TF-reconcile journal entry). Residual = other-workstream committed config (odum_portal prod domain + governance/digest features + legacy-consolidator teardown) — NOT auto-applied, characterized below                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | pre-existing drift outside tonight's bucket scope; targeted apply deliberately excluded it                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                     | operator review + full `terraform apply` from deployment-service@42d4035 (safe for buckets now — plan gate: 0 bucket destroys)                                                                                                                                                                                                                                                                                                         |
| 6                                                                                                                        | W2 checkpoint deletions owned by other plans: dex-pools/lst-rates/perp-funding-prd (−3), lending-indices pair (−2), legacy flat tick/instruments twins (−8, L6 operator-gated), football ×4, ASTER originals                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | owned by defi_dedicated_bucket_shared_migration / M-1 L6 / operator rulings — deliberately not force-run tonight                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               | those plans' own gates                                                                                                                                                                                                                                                                                                                                                                                                                 |
| 7                                                                                                                        | Codex doc updates: bucket-isolation-model.md (derived-from-yaml model), gcs-lifecycle-policies.md (COLDLINE@60d supersedes "not lifecycle'd")                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | docs-only, end of dispatch window                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              | mechanical edit + prek commit                                                                                                                                                                                                                                                                                                                                                                                                          |
| 8                                                                                                                        | ~~setup-buckets.py + bucket_config.yaml resolver rewrite~~ — DONE 2026-07-14: `deployment-service@344958c1`                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | ~~live consumers (setup-dev-project.sh, provision-test-buckets.sh, SIT conftest); rewrite exceeds blast radius~~ resolved: script now enumerates cloud-providers.yaml kinds via UTL `resolve_bucket_name`, mirroring `terraform/gcp/canonical_buckets.tf`'s for_each (prd+test tiers only, `-test-` infix hack deleted); `bucket_config.yaml` trimmed to genuine infra buckets only (stale eigenlayer-rewards/ml-configs-store/features-volatility-defi twins + dead aws_bucket_mappings/test_buckets/validation sections removed); dependencies.yaml untouched (still a live consumer via `deployment_service.dependencies.DependencyLoader`) | none — verified via `--help` + `--list-only`/`--dry-run` against central-element-323112 (88/89 resolved names already exist live; the one gap is the already-tracked item #3 flat config-store bucket) + `--test-only`/`--service`/`--cloud aws`; both consumer shell scripts' CLI surface preserved; SIT conftest/smoke untouched (still parses fine, `required_gcs_buckets` fixture returns 26 buckets, well above its `>=10` floor) |
| 9                                                                                                                        | UAC `mapping_resolver.py` hardcoded `instruments-store-sports-test-project` (broken name, live package code) + UI vendored copy                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | found by audit, out of tonight's repo scopes                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                   | small fix + ship                                                                                                                                                                                                                                                                                                                                                                                                                       |
| 10                                                                                                                       | ~~`ml_jobs_ikenova`-class ops singletons registration (honest-coverage/phantom-triage/rescan-triage/benchmark-reports/deployment-events)~~ — DONE 2026-07-14: all 5 registered in `deployment-service/configs/bucket_config.yaml`'s `infrastructure_buckets.gcp` genuine-infra list, mirroring the terraform-state/deployment-orchestration/build-metadata entries already there — deployment-service@2246e11 (full QG green)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          | W2 P2, not reached                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | fold-or-register per W3 design §ops                                                                                                                                                                                                                                                                                                                                                                                                    |
| 11                                                                                                                       | ~~`deployment_service/dependencies.py`'s `DependencyLoader._check_single_dependency()` reads `dependencies.yaml`'s `bucket_template`/`path_template` fields via `str.format(**template_vars)`, but `template_vars` only ever supplies `asset_group_lower` — every upstream check whose template uses the (actual, on-disk) `{category_lower}` placeholder raises `KeyError` (caught, reported as a FAILED dependency check, never a crash)~~ — DONE 2026-07-14: added a `category_lower` alias in `vars_dict` (kept `dependencies.yaml`'s ~40 on-disk `{category_lower}` template sites unchanged — smaller, safer diff than renaming every one of them) — deployment-service@ddd9d76; new regression test `test_category_lower_template_var_resolves` added to `tests/unit/test_dependencies.py`, full QG green                                                                                                                                                                                                                                                                                                                                                                                       | found while auditing item #8's blast radius (grep-then-READ on `bucket_template` consumers turned up this genuinely separate, load-bearing consumer); same root-cause class as the setup-buckets.py bug this tick fixed, but a different file/fix and outside deployment-service's `scripts/` — exceeds this tick's scope                                                                                                                                                                                                                                                                                                                      | either rename `dependencies.yaml`'s placeholder to `{asset_group_lower}` (matches what `check_dependencies()` actually provides) or add a `category_lower` alias in `vars_dict` — small, contained fix + re-run `deployment-service/tests/unit/test_dependencies.py`                                                                                                                                                                   |
| 12                                                                                                                       | ~~`system-integration-tests/tests/conftest.py`'s `_resolve_bucket()` (feeds the `required_gcs_buckets` fixture) has the identical `{category_lower}`-never-substituted bug (replaces `{asset_group_lower}`/`{project_id}`/`{domain}`, never `{category_lower}`) — `test_required_buckets_list_non_empty` still passes (asserts only `>=10`, blind to the literal-placeholder names) but `test_all_required_gcs_buckets_accessible` would fail loudly against real GCP creds (braces aren't valid bucket-name syntax)~~ — DONE 2026-07-14: `_resolve_bucket()` now also substitutes `{category_lower}` — system-integration-tests@f73349b; added `tests/unit/test_conftest_bucket_resolution.py` exercising `_resolve_bucket()`/`_enumerate_service_buckets()` directly (proves no literal-placeholder bucket names survive enumeration), full QG green. In THIS checkout `test_required_buckets_list_non_empty`/`test_all_required_gcs_buckets_accessible` both SKIP (by design — the fixture's `deployment-service/configs` relative-path resolution is empty in this specific workspace layout, a pre-existing quirk unrelated to this fix); the fix itself is proven directly by the new unit tests | same root-cause class as #11; SIT is explicitly a conditional-only repo for item #8 ("only if conftest/smoke coupling needs a matching edit") and this bug is pre-existing + independent of the bucket_config.yaml trim that tick made (verified: SIT enumeration still returns 26 buckets post-trim)                                                                                                                                                                                                                                                                                                                                          | small fix: rename the local `_resolve_bucket()` replace target to `{category_lower}` (or add both) + re-verify `test_required_buckets_list_non_empty`/`test_all_required_gcs_buckets_accessible`                                                                                                                                                                                                                                       |
| 13                                                                                                                       | **UPDATED 2026-07-14/15 (autonomous dispatch, live-verify)** — Morpho lending-indices relaunch: ground-truth-confirmed real gap in `market-data-tick-defi-prd-central-element-323112` raw_tick_data for `venue=MORPHO`/`data_type=lending_indices`, `day=2026-03-27` through `day=2026-07-12` (108 days). **Dispatched**: `mtds-lending-indices-20260715-002613`, launched 23:26:33Z via `bash deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh --lending-protocols morpho 2026-03-27 2026-07-12` after content-verifying (unpacked + grepped the actual tarballs, not just manifest-SHA math) all 4 tarballs (mtds-code/UAC/UTL/deployment-service) carry the FULL `mtds_backfill_vm_startup_oom_rc137_2026_07_14` fix chain — see that issue doc's new live-verify section for the full chain incl. a previously-undocumented 5th fix (`unified-trading-library@a5b07ff7`, row-group predicate pushdown, 14.86GB→742MB peak) found already-shipped+tarballed at launch time. **RESULT: COMPLETE 2026-07-15T03:37Z — first genuine success of this backfill, full 108-day range captured, clean exit.**                                                                       |
| Handler init 23:29:00Z survived past every prior crash point; ran ~4h8m end-to-end. Final log lines: `Lending indices    |
| collection complete: 1604 total records ({'morpho_ETHEREUM': 1604, 'morpho_BASE': 0})`, `Batch complete: 108 results     |
| collected`(exact match to the 108-day request),`[vm-exec] command exited rc=0` (NOT rc=137 — the OOM fix chain,          |
| including the 5th previously-undocumented `unified-trading-library@a5b07ff7` row-group-pushdown fix, held for the        |
| entire run), `DEPLOYMENT_COMPLETED exit_code=0`, clean self-archive + self-delete. Independently ground-truth-verified   |
| (not trusting the VM log alone): `gcloud storage ls` on `market-data-tick-defi-prd-central-element-323112` confirms real |
| `venue=MORPHO/chain=ETHEREUM` objects now present at `day=2026-04-03` and `day=2026-07-01` (both previously-empty,       |
| mid-gap spot-checks), plus the pre-gap `day=2026-03-26` unaffected/still present. **`morpho_BASE=0` for the full run is  |
| unexplained but not investigated further here** (may be genuine — Morpho's Base deployment could postdate or have        |
| negligible activity in this window — flag for whoever next audits Base-chain DeFi coverage, not a backfill-mechanism     |
| problem). **Item 13 CLOSED.**                                                                                            | `mtds-lending-indices-20260712-112557` SIGKILLed (OOM, rc=137) mid-backfill 2026-07-13; this relaunch is the first live verification of the full `date_range`-scoping fix chain against a real backfill VM                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             | continue monitoring to completion (post-run day-partition spot-check across the full 108-day window, not just VM-log "success"); if it crashes later in the run, capture evidence + add a new dated finding to `mtds_backfill_vm_startup_oom_rc137_2026_07_14.md` rather than a duplicate doc                                                                                                                                                                                                                                                                                                                                                  |

## Round-2 final state (2026-07-14) — supersedes rows above where they conflict

**Estate: 241 → 153** (independently re-counted). Executed this round beyond the W0/W1 baseline: strategy-store per-AG
trio deleted (item 1 ✅), football ×4 migrated-to-canonical-homes + deleted, DeFi `lst-rates-prd`+`perp-funding-prd`
deleted (after closing a **6,941-object shared-bucket parity gap** — 5 dex venues, GMX/HL funding, 7 CeFi Tardis perp
shards silently absent post-cutover), flat `config-store` deleted (lease + all durable config verified in prd). DeFi
kinds removed from all 5 yaml copies (34); UAC `mapping_resolver` fixed (item 9 ✅, uac@401b0b18); setup-buckets.py
resolver rewrite (item 8 ✅); codex updated (item 7 ✅, pm@0f319f8f).

**Async purge COMPLETE 2026-07-14 (follow-up sub-task, all 6 confirmed 404-deleted).** The 6 lifecycle-purge-armed
buckets — `market-data-tick-{cefi,defi,tradfi}`, `instruments-store-{defi,tradfi}`, `dex-pools-prd` (all
`-central-element-323112`) — were re-verified live (not trusted from plan text): `gcloud storage buckets describe`
showed all 6 still existed with `versioning_enabled=true` (dex-pools-prd: no versioning field, i.e. unversioned) and
`soft_delete_policy.retentionDurationSeconds` = `604800` (the 3 tick buckets + dex-pools-prd) or `0`/disabled (the 2
instruments-store buckets); live-object listing (`gcloud storage objects list`) was already 0 on all 6. Per-bucket, ran
the safe non-destructive check the task specified — a real `gcloud storage buckets delete gs://<b> --quiet` attempt
(this errors "not empty" without deleting anything if any live-or-noncurrent version remains; GCS refuses bucket
deletion with any surviving version regardless of soft-delete config) — and all 6 **succeeded** (no "not empty" error),
confirming true zero-version state, immediately re-verified via `gcloud storage buckets describe` → **404 on all 6**:
`market-data-tick-cefi-central-element-323112`, `market-data-tick-defi-central-element-323112`,
`market-data-tick-tradfi-central-element-323112`, `instruments-store-defi-central-element-323112`,
`instruments-store-tradfi-central-element-323112`, `dex-pools-prd-central-element-323112`. Independently re-counted
estate via `gcloud storage buckets list`: **145** (vs the ~147 estimate). No force-purge was needed — the async
lifecycle had already fully drained all 6 by the ~24-48h window (armed 2026-07-13, checked 2026-07-14T10:57Z UTC).
`instruments-store-cefi` (the 7th twin, real 2019-era `instrument_availability/` data, 27k+-object legacy-vs-prd gap)
remains explicitly OUT of this sub-task's scope — separate task/owner, purge deliberately still NOT armed there.

**Still HELD / genuinely open (each with a real gate — NOT force-run):**

| # | Item | Gate | | --- |
--------------------------------------------------------------------------------------------------------------------------

|
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

|
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

| | A | `instruments-store-cefi` legacy twin | **UPDATED 2026-07-14 (this session) — the "27,225 legacy-only" figure was
a partition-SHAPE-BLIND diff-tool artifact, not a real data gap.** Read real objects on both buckets: legacy =
`instrument_availability/by_date/day=D/venue=V/{instruments,futures_contracts}.parquet` (39-col schema); canonical prd =
the SAME `day=D/` prefix plus two REQUIRED hive segments the 2026-05-19 bundled `pipeline_mode` migration added
system-wide — `pipeline_mode=batch_instruments_service/asset_group=cefi/` — before `venue=V/...` (47-col schema; this is
the exact, already-documented "legacy bare shape vs canonical `pipeline_mode=` shape" class in
`codex/02-data/pipeline-mode-partition.md`'s GCS-DELETE-SAFETY HARD RULE, not a novel problem). Re-ran the legacy-vs-prd
diff SHAPE-AWARE (keyed on (day,venue), both shapes, full corpus: 28,228 legacy objects vs 51,637 prd objects) instead
of the earlier naive relative-path-string diff that produced the false 27,225/27,725 alarm: **true legacy-only = 4
keys** (bare `venue=COINBASE`/`venue=OKX` on 2026-03-01 and 2026-03-02 only — a venue-naming-scheme transition artifact,
already superseded the same days by the now-standard split sub-venue captures `COINBASE-SPOT`/`COINBASE-FUTURES` and
`OKX-SPOT`/`OKX-FUTURES`/`OKX-SWAP`, both present canonical-side). Content-verified (not just path-matched) across 7
day/venue samples spanning 2019→2026: canonical prd ALWAYS has equal-or-more rows than legacy for the same (day,venue) —
e.g. 2019-03-30/DERIBIT legacy=6 rows/39 cols vs prd=295 rows/47 cols; 2026-05-22/ASTER legacy=19 vs prd=419 — prd is a
genuinely richer re-capture, not merely a repartitioned copy. Confirmed via SSM the detached `cefi_rsync.log` rsync (VM
`i-0c9b283b31d6b5ca7`) is NOT running (completed rc=0 in 8s on 2026-07-14T01:08Z) — that fast completion is now
explained: it was a raw relative-path `gcloud storage rsync -r legacy→prd`, and since almost all of legacy's content
already existed prd-side (independently, under the correct shape, produced by the live dual-write orchestrator — see
`instruments_service/engine/orchestrator/writers.py:150-158` unconditional bare-shape write + the separate
manifest-tracked `pipeline_mode=` write when a manifest is supplied), the sync found almost nothing new to copy. **A
SEPARATE, EARLIER blind-copy attempt (before this session, creation_time 2026-07-13T23:45Z) DID land ~6,286
legacy-shaped objects directly inside the canonical prd bucket's tree** (bare `day=D/venue=V/...`, no
`pipeline_mode=`/`asset_group=`) — these are dead/orphaned duplicates the canonical reader's
`pipeline_mode=`-prefix-match will never see (lower row counts / narrower schema than the real canonical record for the
same day+venue, confirmed byte-identical to legacy in the one spot-checked), harmless (no overwrite, no data loss) but a
hygiene issue inside the CANONICAL bucket — **flagged, not touched** (out of this task's scope: deleting from the
canonical bucket needs its own care/owner, not a unilateral action bundled into a legacy-bucket investigation). **Zero
live code anywhere in the workspace references the flat bucket name** (`rg` clean) and the resolver can no longer
construct it (dev/stg tiers retired, prd+test only per Wave-0); legacy bucket's last write was 2026-05-22 (~53 days
stale, consistent with the 2026-05-12 prd-bucket cutover + a short dual-write tail). **Purge: ARMED THEN REVERTED THIS
SESSION** — applied the same age=0(isLive)+daysSinceNoncurrentTime=0(non-live) purge-lifecycle used for the 6 siblings,
verified it took effect, then DELIBERATELY REVERTED it (~1 min later, well inside GCS's ~24h lifecycle-eval cadence —
verified a sample object still intact after revert, zero data lost) upon finding
`codex/02-data/pipeline-mode-partition.md`'s 2026-06-18 HARD RULE verbatim for this exact class of decision: _"Require
100% canonical-twin coverage per AG before executing that AG's delete-list; deletion is OPERATOR-GATED."_ This session's
shape-aware diff reaches 28,224/28,228 = 99.986% literal per-key twin coverage, not literal 100% (the 4-key residual is
confidently explained above as superseded-by-rename, not missing data, but that is an interpretive judgment, not a
path-verified twin) — so arming the actual purge/delete is correctly left for an OPERATOR go given the HARD RULE's
letter, not executed autonomously. **OPERATOR AUTHORIZED 2026-07-14 (later this session)** — operator explicitly ruled
"lets fix the below and delete old buckets after migrations confirmed," referring to this bucket + the analysis above.
Re-verified live state before acting (nothing trusted from plan text): `lifecycle_config` still the ORIGINAL reverted
rule (`NEARLINE@90` + `Delete daysSinceNoncurrentTime=30,numNewerVersions=3`), `versioning_enabled=true`,
`soft_delete_policy.retentionDurationSeconds=0` — unchanged since the prior analysis. Newest `day=` partition under
`instrument_availability/by_date/` is still `day=2026-05-22` (`day=2026-06*`/`day=2026-07*` listings both return zero
objects — no new legacy-side writes in the ~53 days since); the 4-key residual re-spot-checked directly
(`day=2026-03-01`/`day=2026-03-02` listings) still show bare `venue=COINBASE`/`venue=OKX` alongside the already-split
`COINBASE-SPOT`/`OKX-SPOT`/`OKX-FUTURES`/`OKX-SWAP` sub-venue keys for the same 2 days, exactly as documented above —
live state materially UNCHANGED, so proceeded. **Purge RE-ARMED 2026-07-14T13:31:43Z UTC** — identical lifecycle JSON to
the 6-sibling precedent, verified live via `buckets describe` immediately after arming. A baseline
`gcloud storage buckets delete --quiet` attempt right after arming correctly failed ("Bucket is not empty") — expected,
since unlike the 6 siblings (already 0 live objects before their purge was armed) this bucket still holds its full
~28,228-object legacy corpus untouched (the prior session only diffed + reverted, never deleted anything). **STATUS:
COMPLETE 2026-07-15** — follow-up
`gcloud storage buckets delete gs://instruments-store-cefi-central-element-323112 --quiet` succeeded (no "not empty"
error — proof of true zero-version state), confirmed via `buckets describe` → 404. Drain finished in well under 24h from
the 2026-07-14 13:31:43Z arm, faster than the conservative estimate above given the ~28,228-object corpus size. **Item A
CLOSED — bucket genuinely deleted.** | | B | Flat ml trio (`ml-models-store`/`ml-configs-store`/`ml-predictions-store`)
| UTL PATH_REGISTRY repointed to `-prd-` (utl@8cec8786) but the flat `ml-models-store` still has live deployment-api
data-status readers until deployment-api's prod image rebuilds off the promoted UTL. Delete after that rebuild + a
no-new-writes check. | | C | `lending-indices` + `-prd` | **UPDATED 2026-07-14 (this session) — writer fixed, real
historical data migrated, purge ARMED (not yet 404).** `_resolve_bucket()` was CONFIRMED still writing to the flat
bucket (domain string `"lending-indices"` isn't in UTL's `_DOMAIN_TO_YAML_KIND`, so `get_write_bucket_name()` fell
through the legacy no-env fallback to `lending-indices-{pid}`) — the Cloud Scheduler cron (`0 */6 * * *`, ENABLED, last
run SUCCEEDED 06:01Z) is a LIVE recurring writer via this path, confirmed via `gcloud run jobs executions list`. Fixed
to `get_write_bucket_name("market_data", "defi")`, mirroring `lending_indices_handler.py`'s own writer (same file) —
mtds@8e4d4960. The job re-clones `live-defi-rollout` HEAD every 6h run (no image pin), so the fix took effect on the
next scheduled fire with no rebuild needed. TF: the `t1_batch` IAM binding on the flat bucket
(`subgraph_health_probe_scheduler.tf:71`) removed from config (TF-unmanaged until the flat bucket is deleted, matching
the lending-indices-prd precedent) — t1_batch already has `objectAdmin` on the canonical shared bucket via
`t1_batch_defi_raw_tick_writer` (qg_snapshot_scheduler.tf), no new binding needed — ds@2399d674. VM
`mtds-lending-indices-20260712-112557` confirmed gone (`gcloud compute instances list` empty) — **but its run.log shows
it was SIGKILLed (`rc=137`) mid-Morpho-backfill, not a clean completion as this row previously assumed**; it wrote
directly to the canonical bucket (not either bucket in scope here, so no interference with this deletion) but leaves a
real Morpho lending-indices gap in canonical for ~2026-03-27→2026-07-12 — **flagged as a NEW, separate finding, NOT
fixed here** (out of this todo's narrow scope; needs its own relaunch + a fix to the `VM_SHUTDOWN_ON_COMPLETION`
watchdog not to treat a SIGKILL exit as "done"). **Real unique historical data found in BOTH buckets, not just
fingerprints** (this row's original framing undersold the scope) — three legacy path-shapes discovered by direct GCS
inspection, none previously documented: (1) `raw_tick_data/by_date/day=D/asset_group=defi/` AAVE_V3/COMPOUND_V3/SPARK
(bare pre-`pipeline_mode=` shape) — day-key diff against canonical found 78 gap-days (the 2022-01-01→2022-03-11 head of
history + 8 scattered 2025-09/11 days a second contention-free re-check caught); ALL migrated + reshaped
(`pipeline_mode=batch_onchain_subgraph/` inserted) into `market-data-tick-defi-prd`, 1898 objects, verified
byte-identical (size+md5) on every sample checked, zero errors. (2) top-level `day=D/category=defi/`
KAMINO/SOLEND/MARGINFI Solana-lending (bare pre-canonicalisation shape, `instrument_type=solana_lending` not `=lending`)
— a FULL day×venue existence check (2,776 pairs) found 2,699 missing from canonical entirely; ALL migrated

- reshaped, **2,698/2,698 copies succeeded (0 errors)**, spot-checked byte-identical. (3) legacy
  `lending_indices/{protocol}/{chain}/date=D/` tree confirmed a pure historical SUBSET of tree (1)'s date range (same
  start, ends earlier) — no separate migration needed, fully covered by (1). `_index/` (availability_index/per_vm/
  snapshots/subgraph_fingerprints) is disposable bucket-local manifest bookkeeping, not migrated (dies with the bucket,
  canonical has its own independent manifest). **Also found + fixed 2 live readers that would have broken on delete**
  (neither previously flagged in this row): `deployment-api/deployment_api/services/data_status/defi.py`'s
  `_BUCKET_CATEGORY_OVERRIDES`/`_MTDS_DEFI_SUB_DIMENSIONS` still read `lending-indices-{env}-{pid}` for the DeFi
  data-status drilldown (a same-day-earlier commit, b5641cf, dropped 9 sibling overrides but called lending-indices "the
  only survivor" — incorrectly; its write path was already broken per the fix above) — dropped the override, falls
  through to the same main-DEFI-bucket read as every other Phase-2 type now — deployment-api@963d8e8 (dirty-deps direct
  push carve-out; this repo currently has 30+ uncommitted files from a concurrent agent incl. a `NameError`-broken
  `cache.py`, unrelated to this change). `deployment-service/deployment_service/vm_prefix_registry.py`'s
  `VM_PREFIX_TO_BUCKET["mtds-lending-indices-"]` zombie-watchdog shard-check pointed at the flat bucket too — repointed
  to `_TICK_DEFI` (same canonical bucket, matching every sibling MTDS DeFi VM prefix entry) — ds@539213a. **NOT fixed,
  flagged for follow-up** (adjacent, out of this narrow todo's scope, affects siblings too): `features-service`'s
  `onchain/app/core/dependency_checker.py` `UPSTREAM_DEPS_DEFI` still has a `required: True` pre-flight dependency entry
  for `lending_indices` pointing `bucket_template` at the flat bucket (`"lending-indices-{project_id}"`) — and its 3
  sibling entries (`lst-rates`/`oracle-prices`/`perp-funding`, same file) already point at buckets deleted EARLIER this
  session, confirmed still 404 today, so this is a pre-existing, wider gap this task didn't introduce, not a new
  regression — but genuinely needs a follow-up fix (repoint all 4 to the manifest-based canonical-bucket check, matching
  how `vault_share_price`'s entry in the same dict already does it correctly). Also not fixed (low-priority, one-off,
  `# Lifecycle: oneoff` marked): `deployment-api/scripts/cleanup_ghost_venue_manifest_rows.py`'s `DEFI_MTDS_BUCKETS`
  list still names the flat bucket (9 of its 10 entries are already-deleted buckets too — this script is itself
  stale/dead, awaiting its own delete-when condition). **Purge-lifecycle ARMED on both buckets 2026-07-14T14:00Z UTC**
  (identical `age=0(isLive)+daysSinceNoncurrentTime=0(non-live)` JSON used for the 6-sibling precedent) — flat bucket
  unversioned, prd bucket `versioning_enabled=true`/`soft_delete_policy.retentionDurationSeconds=604800`, both confirmed
  live via `buckets describe` immediately after arming. **STATUS: COMPLETE 2026-07-15** — follow-up
  `gcloud storage buckets delete --quiet` on BOTH `lending-indices-central-element-323112` and
  `lending-indices-prd-central-element-323112` succeeded (no "not empty" error), both confirmed 404 via
  `buckets describe`. Drain finished within ~24h of the 2026-07-14T14:00Z arm. **Item C CLOSED — both buckets genuinely
  deleted.** Full narrative + exact evidence in the Progress Log entry below. **UPDATED 2026-07-14 (autonomous dispatch,
  separate session) — both follow-up findings this row flagged are now investigated to ground truth; see the
  "2026-07-14, autonomous dispatch — dependency-checker fix + VM watchdog investigation" Progress Log entry below for
  full evidence.** Summary: (1) the `features-service` dependency-checker gap flagged above IS fixed now —
  `onchain/app/core/dependency_checker.py`'s `UPSTREAM_DEPS_DEFI` (4 entries: lst-rates/lending/oracle/perp) and the
  base `UPSTREAM_DEPS`'s 3 sibling entries all repointed to the shared canonical
  `market-data-tick-{asset_group_lower}-{project_id}` bucket; ALSO found + fixed a deeper, previously-undiscovered
  sibling bug in the same repo — `onchain/app/core/data_loader.py::_resolve_mtds_parquet_files()` independently
  constructed the SAME now-404 dedicated bucket names via `get_bucket_name(bucket_domain)` for the actual DeFi
  feature-compute READ path (not just the preflight check) — features-service@f74b9c06 (quickmerge, QG green). Live
  investigation found this was NOT an active crash-loop (no Cloud Run job/cron/VM has invoked features-onchain-service
  DEFI in the last 3 days per the deployment registry archive) but was a 100%-reproducible landmine for the next launch.
  (2) The `VM_SHUTDOWN_ON_COMPLETION` watchdog hypothesis in this row was partially refined: the exit code (137) and
  terminal `status=failed` were ALREADY correctly captured in the raw GCS `EXIT_STATUS` blob (BUG-4, a pre-existing
  2026-05-05 fix) — NOT silently masked as success. The real, newly-found gap is one level deeper: this VM's daemon got
  SIGKILLed before it could call its own `complete()`/registry-archive step (likely mid a slow final-log-upload for its
  790K-line run.log), so the deployment registry entry sat orphaned in `active/` for ~20h until
  `unified_trading_library.deployment_registry.DeploymentsRegistry.reap_stale()` (deployment-api's 15-min leader-elected
  background reaper) finally archived it — correctly as `status=failed`, but with the GENERIC `exit_code=125` reap
  sentinel, discarding the TRUE `rc=137` that was sitting the whole time in
  `gs://deployment-scripts-central-element-323112/vm-logs/mtds-lending-indices-20260712-112557/EXIT_STATUS`
  (live-confirmed). Shipped the narrow, safe fix — `reap_stale()` now best-effort reads that blob before falling back to
  125 — unified-trading-library@f9dba076 (quickmerge, QG green, 2 new regression tests). Flagged, NOT fixed (broader
  shared-infra scope, ~150 launcher scripts): the daemon's final-upload-can-block-past-the-wrapper's-30s-SIGKILL-window
  race itself, and the ~20h `reap_stale` cadence gap (normal cadence is 15-30min; this specific gap's root cause —
  leader-election churn vs. a silently-swallowed exception in deployment-api's background_sync loop — was NOT diagnosed
  further, out of this session's scope). (3) The real Morpho lending-indices gap in canonical is GROUND-TRUTH CONFIRMED
  (direct GCS day-partition listing, not the VM log's claim nor the manifest, which itself turned out to have zero
  `capture_status=captured` rows for MORPHO anywhere — a separate, unexplained manifest-completeness quirk worth
  flagging but not chased further here): real parquet data exists for every sampled day through `day=2026-03-26` and is
  confirmed ABSENT (0 objects) for every sampled day from `day=2026-03-27` through `day=2026-07-12` (108 days) under
  `market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day={D}/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=MORPHO/`.
  Ready-to-dispatch relaunch (NOT executed this session per the task brief — out of this narrow dispatch's scope):
  `bash deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh --lending-protocols morpho 2026-03-27 2026-07-12`
  (mirrors the original launch's `--lending-protocols morpho` scoping; the original's full `2023-01-01` start is already
  fully captured through `2026-03-26` so the gap-scoped window above is the minimal correct relaunch — the launcher's
  manifest-driven idempotency also makes re-running the full original `2023-01-01 2026-07-12` window safe if a future
  session prefers not to trust this gap boundary). Repos touched: `features-service@f74b9c06`,
  `unified-trading-library@f9dba076`. No data touched, no VM launched, no repo left QG-red. | | D | recon end-to-end
  green | **UPDATED 2026-07-14 (this session) — (a) DONE + verified; (b) investigated to a precise, well-scoped
  STILL-OPEN finding, genuinely out of this plan's scope (whole missing upstream pipeline, not a config fix).** (a): the
  digest bump (`28a18fa`) + config fix (`2f0380b`) were already on `main` (content-verified) and the prod image had
  already picked them up (built off `7b65341`), but the 06:00Z 2026-07-14 scheduled run STILL failed — with a NEW error
  (`BucketNamingError: Unknown kind 'recon'`), not the originally-diagnosed one. Root cause (found via direct
  `docker pull`/`inspect` of the exact deployed image): the UTL base image digest BLRS pinned (`sha256:b7e391f8`,
  refreshed 2026-07-13T17:44Z) bundles a UAC snapshot at commit `21dde0f8` (16:39:42Z same day) — 3.5h BEFORE
  `uac@f84e5b37` (20:11:34Z) actually added the `recon` kind to `cloud-providers.yaml`. A same-day
  base-image-refresh/upstream-fix race, not a bug in BLRS's own code. Fixed by re-bumping `Dockerfile`'s
  `BASE_IMAGE_DIGEST` to `sha256:9594091a` (current UTL `:latest`, confirmed via image inspection to embed UAC commit
  `ed622d8b1`, a descendant of `f84e5b37`) — `batch-live-reconciliation-service@be056b1` (quickmerge, QG green). Built
  - verified directly off LDR
    (`gcloud builds triggers run batch-live-reconciliation-service-build --branch=live-defi-rollout`, build
    `ab591245-708a-4c84-a080-7f4d3a9d6a15`, SUCCESS, new image `sha256:763b5446` pushed to `:latest`
    2026-07-14T20:07:32Z) rather than waiting on the LDR→staging→main promotion chain. Manually triggered a real
    execution (`uts-prod-batch-live-reconciliation-service-pn4f7`) to verify: config now resolves correctly (no more
    `BucketNamingError`) and Stage 0 fails at the EXPECTED, already-documented gate — "Missing upstream data for
    2026-07-13: execution config snapshot: gs://execution-store-cefi-.../configs/snapshots/ 2026-07-13/config.json; ML
    t1-recon outputs: gs://recon-prd-.../t1-recon/ml/2026-07-13/\_SUCCESS; strategy t1-recon outputs:
    gs://recon-prd-.../t1-recon/strategy/2026-07-13/\_SUCCESS" — real, current, live-verified evidence (a) is genuinely
    closed. (b): traced the full producer chain live (Cloud Scheduler + Cloud Run Jobs + direct code reads), not
    guessed. Three concrete, independently-confirmed gaps, each already gating Stage 0 on its own: (1)
    execution-service's config-snapshot producer (00:30 UTC) — scheduler
    `uts-prod-execution-config-snapshot-t1-schedule` ENABLED, fires daily, but its target Cloud Run Job
    (`uts-prod-execution-service-config-snapshot`) has NEVER BEEN PROVISIONED (`gcloud run jobs list` — zero matches).
    (2) ml-service's t1-recon producer (03:00 UTC) — scheduler `uts-prod-ml-t1-schedule` ENABLED, fires daily, target
    Cloud Run Job (`uts-prod-ml-service-t1-recon`) also NEVER PROVISIONED (confirmed via `gcloud run jobs describe` +
    scheduler execution logs showing `NOT_FOUND`/`UNAVAILABLE` every day). ml-service DOES already have a `--run-tag`
    CLI flag (help text literally references t1-recon) but it is completely UNWIRED — grep across
    `ml_service/inference/` found zero consumers of it anywhere; no GCS writer respects it and there is no
    `_SUCCESS`-marker writer anywhere in the service. (3) strategy-service's t1-recon producer (04:00 UTC) — its Cloud
    Run Job DID exist (provisioned 2026-05-23 per a prior F-41-followup) but was fundamentally broken at the
    container-exec level: Terraform passed bare `args = ["--operation", "backtest", "--mode", "batch"]` with no
    `command` override, while strategy-service's own Dockerfile deliberately sets `ENTRYPOINT [] + CMD=uvicorn ...` (it
    is primarily a live API service) — confirmed via `docker inspect` on the exact deployed image + a local repro
    (`exec: "--operation": executable file not found in $PATH`). Every daily execution since creation (10/10 checked,
    07-05 through 07-14) failed at the OCI level with ZERO application logs. FIXED the exec bug in scope (small, safe,
    well-understood): added `command = ["python", "-m", "strategy_service"]` to the Terraform module
    (`deployment-service/terraform/gcp/audit03_cron_provisioning.tf`, a real tested CLI entrypoint — confirmed via
    `tests/unit/cli/test_cli_flag_combinations.py`) + applied directly to the live job via `gcloud run jobs update`
    (local `terraform init` hit a backend-config mismatch against the shared remote state — used the same established
    edit-source-then-gcloud-apply pattern this plan's session already relies on elsewhere, safer than a blind local
    init/migrate-state against a state other agents are concurrently touching). Re-triggered a real execution to verify:
    the container now genuinely STARTS and RUNS (real bootstrap logs, live GCS bucket connectivity, ~2min runtime vs.
    the prior <1s instant OCI crash) — but fails one layer deeper: `_resolve_date_args()` hard-requires an explicit
    `--date` or `--start-date`/`--end-date` (unlike ml-service/mdps, which self-default to T-1 when omitted) and the
    Terraform args supply neither, so it raises
    `ValueError: batch operation requires --date or both --start-date and --end-date`. Additionally (found live, not
    guessed): strategy-service has NO `--run-tag` concept anywhere in its codebase (grep-clean workspace-wide) and no
    `_SUCCESS`-marker writer — so even after fixing the date-arg gap it would still never satisfy Stage 0's poll (it
    would write to the default `batch/` thermal-backtest namespace, which the DAG doc says recon never reads).
    Separately confirmed all 7 feature-family t1-recon schedulers this chain's own DAG doc depends on
    (calendar/delta-one/volatility/cross-instrument/multi-timeframe/ commodity/sports) are in state `PAUSED` live, and
    the onchain feature family isn't even represented in `t1_batch_scheduler.tf`'s service map at all. **Conclusion: not
    a missing-scheduled-job or broken-config fix — an entire designed-but-never-built upstream pipeline** (2 missing
    Cloud Run Jobs, a `--run-tag`/`_SUCCESS`-marker convention never implemented in ANY producer despite one service
    carrying a dead CLI flag for it, a hard-required date arg with no self-default in the one producer whose exec bug
    got fixed, 7 paused + 1 unregistered feature-family schedulers upstream of ml). Standing this up needs multi-repo
    feature work across execution-service/ml-service/strategy-service/features-service — genuinely out of scope for a
    bucket-consolidation plan. Repos touched this pass: `batch-live-reconciliation-service@be056b1` (quickmerge);
    `deployment-service@ea42a699` (quickmerge — codifies a fix already applied directly to the live Cloud Run Job via
    `gcloud run jobs update`, since local `terraform apply` against this shared state wasn't safe this session; a future
    full `terraform apply` will see this as a no-op diff). Cloud Build `ab591245-708a-4c84-a080-7f4d3a9d6a15` (SUCCESS).
    Full narrative + exact evidence in the Progress Log entry below; issue doc
    `recon_bucket_missing_nightly_recon_failing_2026_07_13.md` updated in the same commit with the same findings. | | E
    | Terraform state re-import | **RESOLVED 2026-07-14** (see "TERRAFORM RECONCILIATION" log entry below) — all 6
    over-removed live resources (defi_collect_cron/job × liquidations+solana-defi, the liquidations pubsub topic+sub)
    re-imported; re-plan confirmed zero of this work pending. Residual full-apply delta (odum_portal domain,
    governance/digest features, legacy-consolidator teardown) is other-workstream, deliberately NOT auto-applied —
    owner/operator green-light needed, not a bucket-plan gate. | | F | ASTER originals | MOVED to
    `aster_cefi_data_defi_bucket_migration_2026_07_13.md` (operator ruling) — re-migrate the high_dup schema-narrower
    band, then delete there. | | G | sports legacy pair (`market-data-tick-sports`/`instruments-store-sports` flat) |
    owned by `sports_manifest_canonicalisation_2026_06_01` E1/E8 — **UPDATED 2026-07-14 (this session's extensive
    work)**: MTDS surface 140 legacy-only cells, all verified phantom-capture (accepted, not a data-loss gap). IS
    surface: 1,786+ real cells migrated this session (down from 1,854), FIXTURES cell-key mismatch fixed, 49/77 further
    anomaly rows fixed — down to 28 accepted-phantom cells remaining (not 316, that count is stale). **Actual remaining
    blocker is CF-8 (`available_at`)**: code fixed + a coordinated backfill already ran (85.3%/87.7% overall fill), but
    the real captured (non-empty) rows are only ~50-60% filled and a targeted re-emit attempt today found a genuine
    architectural gap (the manifest consolidator's dedup key includes `service_name`, and a naive backfill can never
    supersede rows owned by a different original service — rolled back cleanly, no data harm). The real operator
    (separate concurrent session) has explicitly instructed: wait for a scheduled maintenance window + a
    service_name-aware write redesign before another live attempt. Full detail:
    `plans/active/sports_manifest_canonicalisation_2026_06_01.md` +
    `plans/active/issues/sports_cf8_available_at_backfill_regression_2026_07_13.md`. **Still HELD — do not purge/delete
    either bucket.** | | H | W3 structural folds (features 25→5, ml 8→2, stores) | design drafted
    (`bucket_estate_fold_design_2026_07_13.md`, status draft) — the path from ~147 to the &lt;100 target; activate as
    its own plan(s). | | I | Findings #11/#12 (`dependencies.py` + SIT `_resolve_bucket()` `{category_lower}` bug) +
    item 10 ops-singleton registration | **DONE 2026-07-14**: Finding #11 fixed via a `category_lower` alias in
    `dependencies.py`'s `vars_dict` (deployment-service@ddd9d76, new regression test, full QG green); Finding #12 fixed
    via the identical substitution in SIT's local `_resolve_bucket()` (system-integration-tests@f73349b, new
    `tests/unit/test_conftest_bucket_resolution.py`, full QG green); item 10's 5 ops-singleton buckets
    (`{pid}-honest-coverage`/`{pid}-phantom-triage`/`{pid}-rescan-triage`/`{pid}-benchmark-reports`/
    `{pid}-deployment-events`) registered in `bucket_config.yaml`'s `infrastructure_buckets.gcp` genuine-infra list
    (deployment-service@2246e11). |

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

- **2026-07-14, autonomous dispatch — features-service dependency-checker fix + VM watchdog investigation (item C
  follow-ups).** Separate autonomous dispatch investigating the two findings item C's row flagged as NOT-fixed
  ("features-service's DeFi dependency-checker still gating on lending-indices plus 3 already-deleted sibling buckets" +
  the `mtds-lending-indices-20260712-112557` VM's SIGKILL/watchdog gap). Nothing trusted from the row text or the
  operator's framing at face value — every claim independently re-verified live before acting.

  **Finding 1 — features-service dependency-checker (URGENT per the dispatch brief, checked for active breakage
  first).** Read `features-service/features_service/onchain/app/core/dependency_checker.py` in full. Confirmed live via
  `gcloud storage buckets describe` (project `central-element-323112`): `lst-rates-central-element-323112`,
  `oracle-prices-central-element-323112`, `perp-funding-central-element-323112`, `dex-pools-central-element-323112`,
  `dex-swaps-central-element-323112` are ALL 404; `lending-indices-central-element-323112` (flat) still exists
  (mid-purge-drain per item C above). `UPSTREAM_DEPS_DEFI`'s 4 non-vault_share_price entries (lst-rates/lending/oracle/
  perp) all had `required: True` and `bucket_template` pointing at these dead flat buckets, routed through
  `_check_mtds_manifest()` — since `read_manifest_rows()` catches read errors and returns `available=False` rather than
  raising, EVERY DEFI `check_dependencies()` call would compute `required_available=False`. Traced the call chain into
  `features-service/onchain/cli/handlers/batch_handler.py`: `_handle_dependency_report()` raises `DependencyError` when
  `fail_on_missing_deps` (default `True`) is set and any required dep is missing — this propagates out of
  `run()`/`run_batch()` uncaught (only `ConnectionError/TimeoutError/OSError/ValueError` are caught there, not
  `DependencyError`), meaning the ENTIRE batch run for ANY date/DEFI would fail before a single feature group is
  processed, unless a caller explicitly passes `--skip-dependency-check`/`--no-fail-on-missing-deps`. **Checked whether
  this is ACTIVELY breaking anything right now**: `gcloud run jobs list` / `gcloud scheduler jobs list` show no live
  Cloud Run Job or cron for features-onchain-service DEFI (it is VM-launched, on-demand only, via
  `launch-features-onchain-backfill-vm.sh` → `launch-features-vm.sh --feature-family onchain --asset-group DEFI`);
  grepped the deployment-registry archive
  (`gs://deployment-scripts-central-element-323112/deployments/archive/ 2026-07-1{2,3,4}/*.json`, 1911 records) for
  "onchain" — zero hits. **Conclusion: not an active crash-loop** (nothing has invoked it in the last 3 days), but 100%
  reproducible the instant anyone launches one — a landmine, not a fire. Fixed anyway (per the task's own instruction to
  fix either way): repointed all 4 `UPSTREAM_DEPS_DEFI` entries' `bucket_template` (+ aligned `path_template`, vestigial
  for the manifest-check branch but misleading otherwise) to `"market-data-tick-{asset_group_lower}-{project_id}"` — the
  SAME canonical shared bucket the base `market-data-processing-service` and
  `market-tick-data-service-vault-share-price` entries in the same dict already correctly use, and confirmed via grep
  that `lst_rates_handler.py`/`lending_indices_handler.py`/ `oracle_prices_handler.py`/`solana_defi_drift.py` all
  actually write there via `get_write_bucket_name("market_data", "defi"/"DEFI")`. Also repointed the base
  `UPSTREAM_DEPS` dict's 3 sibling entries (required=False, so these were only ever a soft/logged warning, not a crash —
  lower priority but fixed for consistency).

  **A second, deeper, previously-undiscovered bug in the SAME repo** found while verifying the fix would actually close
  the gap: `features-service/onchain/app/core/data_loader.py::_resolve_mtds_parquet_files()` — the REAL DeFi
  feature-compute READ path for every MTDS bypass data_type (lst_rates/lending_indices/oracle_prices/perp_funding/
  dex_pool_state/dex_pool_swaps) — independently called `get_bucket_name(bucket_domain)` where `bucket_domain` came from
  `mtds_output_config.py`'s `_MTDS_OUTPUT_BUCKET_DOMAINS` dict (values: `"lending-indices"`, `"oracle-prices"`,
  `"lst-rates"`, `"perp-funding"`, `"dex-pools"`, `"dex-swaps"`). Traced `get_bucket_name()`
  (`unified_trading_library/core/cloud_constants.py`): these domain strings are NOT in `_DOMAIN_TO_YAML_KIND`, so it
  falls to the legacy fallback `f"{domain}-{pid}"` — constructing the EXACT SAME 5 confirmed-404 bucket names. This is
  reachable independently of the dependency-checker gate (e.g. via `--skip-dependency-check`, or once the gate above is
  fixed) and would have silently 404'd/emptied every bypass-type read — the actual data path, not just a preflight gate.
  Fixed: `bucket = get_bucket_name("market_data", asset_group=self.asset_group)` (asset_group-aware, matches the
  dependency-checker fix + every MTDS DeFi handler's real write target). Updated 2 test files whose mocks asserted the
  old single-arg `get_bucket_name(bucket_domain)` call shape (`test_defi_data_source_routing.py`,
  `test_onchain_data_loader.py`). Shipped: `features-service@f74b9c06` (quickmerge, `quality-gates.sh --no-fix` green).

  **Finding 2 — VM watchdog / `VM_SHUTDOWN_ON_COMPLETION` investigation.** Read the actual crashed VM's full
  `run.log`/`EXIT_STATUS` live from GCS (not the plan's paraphrase): confirmed `EXIT_STATUS=137` IS durably present at
  `gs://deployment-scripts-central-element-323112/vm-logs/mtds-lending-indices-20260712-112557/EXIT_STATUS`, and the log
  shows the workload was `Killed` (SIGKILL) immediately after successfully writing `day=2026-03-26` data, followed by
  `[vm-exec] command exited rc=137` → `received signal 15` (SIGTERM to the daemon) →
  `[vm-exec] WARN: daemon did not exit within 30s — SIGKILL` →
  `VM_SHUTDOWN_ON_COMPLETION=true — scheduling self-delete`. Traced the actual mechanism end-to-end (this VM uses the
  "Pattern A" canonical-tarball path — `setup-data-pipeline-vm.sh` →
  `deployment-service/scripts/vm/vm-exec-with-gcs-tee.sh` → `scripts/vm/heartbeat_daemon.py` →
  `deployment_service.vm.heartbeat_cli` → `unified_trading_library.lifecycle.daemon.HeartbeatDaemon` — NOT the OTHER
  `lc_log_upload_trap_block` inline-heredoc mechanism in `launcher_common.sh`, which already got an unrelated
  "RUNNING-sentinel" fix on 2026-07-13 that does not apply here):
  1. **`vm-exec-with-gcs-tee.sh`'s own shell-level rc capture is already correct** (BUG-4, fixed 2026-05-05 —
     `wait $CMD_PID` correctly returns 137 for a SIGKILLed child; `FINAL_STATUS="failed"` is set correctly since
     `RC != 0`). Its self-delete block, however, fires on `VM_SHUTDOWN_ON_COMPLETION=true` UNCONDITIONALLY — it does NOT
     gate on `$RC`/`$FINAL_STATUS` at all, so a failed run self-deletes (`--delete-disks=all`) exactly as readily as a
     successful one. This IS shared/systemic (this exact script is the canonical path for essentially the whole "Pattern
     A" VM fleet, ~150 launcher scripts reference `VM_SHUTDOWN_ON_COMPLETION`) — flagging, NOT fixed (the narrowest safe
     fix here isn't obvious: unconditional self-delete on success was itself a deliberate historical fix for VMs
     orphaning billable disks forever; changing it to skip-delete-on-failure needs its own careful design
     - a bounded-TTL cleanup fallback, out of a safe narrow-fix scope for this dispatch).
  2. **The real, previously-undocumented gap**: cross-referenced the deployment registry directly (downloaded + grepped
     `gs://deployment-scripts-central-element-323112/deployments/{active,archive/2026-07-12,archive/2026-07-13, archive/2026-07-14}/*.json`,
     ~1911 records) for this VM's `deployment_id` (`19014971-b62d-4b75-965b-72398333c6a2`, read from the run.log's own
     `[vm-exec] deployment_id=...` line — confirmed `register()` DID succeed at 2026-07-12T11:28:05Z, writing
     `gs://.../deployments/active/19014971-....json`). Found ZERO archive entry for 2026-07-12 or 2026-07-13 — the entry
     was NOT archived until **2026-07-14T12:57:05Z** (`gs://.../deployments/archive/2026-07-14/19014971-....json`,
     live-fetched + inspected), i.e. ~20 HOURS after the crash, not by the daemon's own `complete()` (which never ran —
     the daemon itself was SIGKILLed, per the run.log, before it could archive) but by
     `unified_trading_library.deployment_registry.DeploymentsRegistry.reap_stale()`'s generic zombie-reap path
     (`extras.reap_reason="vm_not_running"`). The archived entry correctly shows `"status": "failed"` (never masked as
     success — refines/corrects the dispatch brief's hypothesis) but `"exit_code": 125` — the GENERIC reap sentinel,
     discarding the TRUE `rc=137` that was sitting the whole time in the VM's own `EXIT_STATUS` blob (confirmed both
     blob and registry entry live, side-by-side, before fixing). Per a sub-agent's research (verified independently
     against the source): `reap_stale()`'s real production caller is
     `deployment-api/deployment_api/background_sync.py`'s leader-elected `auto_sync_running_deployments()` loop (15-min
     cadence, `running_vm_names` refreshed live from GCE each tick) — a ~20h gap is NOT normal cadence for this
     mechanism; root cause (leader-election churn vs. a silently-swallowed exception at `background_sync.py:77-78`,
     caught + logged only at `.debug`) was NOT diagnosed further, flagged for a future session. Also note: there are TWO
     near-duplicate `DeploymentsRegistry` classes — the live one in
     `unified-trading-library/unified_trading_library/ deployment_registry.py` (confirmed production-wired) and a dead
     fork in `deployment-service/deployment_service/ deployments_registry.py` (confirmed zero production callers, only
     its own unit tests) — flagged as a cleanup candidate, not touched (editing dead code has no runtime effect and
     wasn't worth the risk/scope here).
  3. **Fix shipped** (narrow, additive, does not change reap eligibility/cadence/self-delete behavior): added
     `_read_true_exit_code()` to `DeploymentsRegistry` — best-effort reads `gs://<bucket>/vm-logs/<vm_name>/EXIT_STATUS`
     (the same durable blob every launcher pattern already writes) before `_archive_reaped_entry()` falls back to the
     generic `125`; stamps `extras.reap_exit_code_source = "vm_exit_status_blob"` when recovered. 2 new regression tests
     (recovers 137 when the blob exists; falls back to 125 unchanged when it doesn't) + both pre-existing `reap_stale`
     tests still pass untouched (no blob pre-seeded in their fixtures → same fallback path as before). Shipped:
     `unified-trading-library@f9dba076` (quickmerge, QG green "ALL QUALITY GATES PASSED (102s)").

  **Finding 2, part 3 — the real Morpho gap, ground-truth confirmed (not the VM log's claim, not the manifest).** First
  tried the MTDS manifest (`read_availability_index` on `market-data-tick-defi-prd-central-element-323112`) — hit
  `ManifestConsolidatorStaleError` (consolidator genuinely behind, a live pre-existing condition documented separately
  in `plans/active/issues/mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`). Downloaded the consolidated
  `_index/availability_index.parquet` directly (445MB, one-time, matching the technique that issue doc's own repro used)
  and slim-filtered via pyarrow (`data_type=lending_indices`, `venue=MORPHO`): found 561,932 manifest rows, but ALL of
  them `capture_status` ∈ {`expected_unattempted`, `empty_confirmed`} with `service_name=instruments-service` — **zero
  rows anywhere show `capture_status=captured` for MORPHO specifically** (real MTDS-captured lending_indices rows exist
  for OTHER venues — 133,695 system-wide — just not Morpho), a separate, unexplained manifest-completeness quirk
  (plausibly: this VM's per-VM shard, which should have carried its real `captured` markers, is gone from
  `_index/per_vm/` — either successfully folded in with a schema/join mismatch on this specific read, or lost before
  consolidation; not chased further, flagging only). Given the manifest was inconclusive, fell back to DIRECT raw-data
  ground truth (targeted day-partition listings, not a full-corpus walk) under
  `market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day={D}/pipeline_mode=batch_onchain_subgraph/ asset_group=defi/venue=MORPHO/`
  for a spread of sample days: **real objects present for every sampled day through `day=2026-03-26` (2023-06-01,
  2025-01-01, 2026-03-20/25/26 all ≥1 object) and CONFIRMED ABSENT (0 objects) for every sampled day from
  `day=2026-03-27` through `day=2026-07-12`** (2026-03-27/28, 2026-04-01/15, 2026-05-01/15, 2026-06-01/15,
  2026-07-01/10/11/12 — all 0). This ground-truths the plan's original ~2026-03-27→2026-07-12 gap claim at the raw-data
  level — the gap is real, 108 days, Morpho-only (other lending protocols not checked, out of this finding's scope).

  **Ready-to-dispatch relaunch (NOT executed this session, per the task brief's explicit instruction not to launch a
  multi-day backfill VM from this dispatch)**:
  `bash deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh --lending-protocols morpho 2026-03-27 2026-07-12`
  — mirrors the crashed VM's own `--lending-protocols morpho` scoping exactly; the gap-scoped window above is the
  minimal correct relaunch given `2023-01-01→2026-03-26` is already fully captured. (The launcher's manifest-driven
  idempotency also makes re-running the full original `2023-01-01 2026-07-12` window safe as an alternative, if a future
  session doesn't want to trust this session's day-boundary finding without its own re-check.) Filed as Deferred-table
  item 13 below.

  Repos touched: `features-service@f74b9c06`, `unified-trading-library@f9dba076`. Both QG green before shipping. No
  bucket/data touched, no VM launched, this plan doc updated in the same commit (PM `docs(plans):` direct-push
  carve-out).

- **2026-07-14, item C (`lending-indices` + `-prd`) — writer repointed, real historical data migrated, purge ARMED
  (draining, not yet 404).** Sub-task per this plan's item C row. Nothing trusted from the row text alone — every claim
  independently re-verified live before acting, per this session's standing rule (two prior real near-misses/catches
  documented above).
  1. **`_resolve_bucket()` state check**: read `subgraph_health_probe.py` live — CONFIRMED still broken, NOT already
     fixed by a concurrent agent. `_LENDING_INDICES_BUCKET_KIND = "lending-indices"` is passed to
     `get_write_bucket_name(domain)`; traced the call into `unified_trading_library/core/cloud_constants.py` —
     `"lending-indices"` is absent from `_DOMAIN_TO_YAML_KIND` and `BUCKET_PREFIXES` (the DeFi-kind removal earlier this
     session dropped it from `cloud-providers.yaml`), so resolution falls through the legacy no-env fallback branch and
     returns `f"{domain}-{pid}"` = the flat bucket, exactly as this row predicted. **Live-verified this is an ACTIVE
     writer, not dormant**: `gcloud scheduler jobs describe uts-prod-subgraph-health-probe-cron` — `state: ENABLED`,
     `schedule: 0 */6 * * *`; `gcloud run jobs executions list` — 5 most-recent executions all `succeededCount=1`, last
     completed 2026-07-14T06:01:19Z. The Cloud Run Job entrypoint (`cron_subgraph_health_probe_entrypoint.sh`)
     `git clone --depth=10 --branch=live-defi-rollout` fresh on every 6h run (no image digest pin, unlike BLRS) —
     confirmed a code fix alone, once merged to LDR, needs no image rebuild to take effect on the next scheduled fire.
  2. **Fix shipped**: `_resolve_bucket()` → `get_write_bucket_name("market_data", "defi")`, the IDENTICAL call
     `lending_indices_handler.py`'s own writer already uses in the same file/repo (line ~592) — mirrors, doesn't invent,
     the established resolution pattern. `market-tick-data-service@8e4d4960` (quickmerge, clean QG; the pre-existing
     `bandit B105` false-positive on an unrelated line in this file, confirmed via `git stash` + re-bandit that it
     exists identically on clean HEAD, did not block — quickmerge's content-scoped QG sentinel correctly isolated it).
  3. **TF binding**: `subgraph_health_probe_scheduler.tf:71`'s
     `google_storage_bucket_iam_member. t1_batch_lending_indices_object_admin` (granting `t1_batch` SA `objectAdmin` on
     the FLAT bucket) is a live, currently-applied binding (confirmed via `gcloud storage buckets get-iam-policy` —
     `uts-prod-batch-sa` present with `objectAdmin`) — NOT the same resource ds@1dd2159 removed earlier (that one was
     the `lending-indices-prd` BUCKET resource in `main.tf`, a different resource entirely; this row's parenthetical "TF
     resource block already removed" was about that bucket resource, not this IAM binding, which was still live).
     Removed from config (TF-unmanaged until the flat bucket is deleted, matching the established resurrection-safe
     pattern); confirmed `t1_batch` already has `objectAdmin` on the canonical shared bucket via the pre-existing
     `t1_batch_defi_raw_tick_writer` binding (`qg_snapshot_scheduler.tf`) — no new binding needed.
     `deployment-service@2399d674` (quickmerge).
  4. **VM write-target verification (was "inconclusive")**: `gcloud compute instances list --filter="name~lending"` and
     the AWS equivalent both empty — VM confirmed gone. Read its full run.log
     (`gs://deployment-scripts-.../vm-logs/mtds-lending-indices-20260712-112557/run.log`) rather than trusting
     "completed" — it wrote fingerprint-adjacent Morpho lending-indices data DIRECTLY to the canonical shared bucket
     (`market-data-tick-defi-prd-.../raw_tick_data/by_date/day=2026-03-26/.../venue=MORPHO/...`, confirmed via
     `ManifestWriter: per-VM shard updated ... at market-data-tick-defi-prd-...`), so it never touched either bucket in
     this row's scope — no interference with this deletion. **But it did NOT cleanly complete**: the log's last lines
     are
     `bash: line 1: 7371 Killed .../python -m market_tick_data_service --operation collect-lending-indices ... --start-date 2023-01-01 --end-date 2026-07-12 --lending-protocols morpho`
     / `[vm-exec] command exited rc=137` (SIGKILL, likely OOM) followed immediately by
     `VM_SHUTDOWN_ON_COMPLETION=true — scheduling self-delete` — the watchdog's shutdown condition doesn't distinguish a
     killed process from a genuinely finished one. Last date it reached before being killed: 2026-03-26 (of a
     2023-01-01→2026-07-12 requested range) — leaves a real, unquantified Morpho lending-indices gap in the canonical
     bucket for roughly 2026-03-27→2026-07-12. **Flagged as a new, separate finding — NOT fixed here** (a multi-day
     Morpho backfill relaunch is well outside this narrow bucket-deletion todo's scope; needs its own plan/task, plus a
     fix to the shutdown-on-completion watchdog logic itself since this is the same "silent-skip on kill" class of bug
     documented elsewhere in this workspace).
  5. **Real unique data found in BOTH buckets (this row's original framing significantly undersold the scope — it wasn't
     just fingerprints)**: direct GCS inspection (shallow, targeted listings — not a whole-corpus walk) found FOUR
     distinct trees in the flat bucket, THREE of them real data:
     - `raw_tick_data/by_date/day=D/asset_group=defi/venue={AAVE_V3,COMPOUND_V3,SPARK}/...` (bare pre-`pipeline_mode=`
       shape, exactly the class documented in `codex/02-data/pipeline-mode-partition.md`'s GCS-DELETE-SAFETY HARD RULE)
       — day-key diff (`comm -23` on shallow day-folder listings, both buckets) against the canonical shared bucket
       found **78 gap-days**: the 2022-01-01→2022-03-11 head-of-history (70 days) plus, after a contention-free re-check
       caught 12 false-negatives from the first (heavily-loaded) pass and confirmed 8 true ones, 8 more scattered days
       (2025-09-29/30, 2025-11-25 through 2025-11-30). Migrated via per-day `gcloud storage cp -r` (day's
       `asset_group=defi` subtree → canonical, inserting the missing `pipeline_mode=batch_onchain_subgraph/` segment) —
       **1,898 objects, verified byte-identical (size + md5)** on every spot-checked object, zero copy failures.
     - Top-level `day=D/category=defi/venue={KAMINO,SOLEND,MARGINFI}/chain=SOLANA/instrument_type=solana_lending/...`
       (Solana lending protocols, a SEPARATE pre-canonicalisation shape never covered by tree 1) — a FULL existence
       check (not a sample) across all 2,776 (day,venue) pairs the flat bucket has for these 3 venues found **2,699
       missing from canonical** entirely (only 77 pre-existing, apparently from an earlier ad-hoc single-date copy).
       Migrated per (day,venue) — **2,698/2,698 succeeded (0 errors)**, spot-checked byte-identical (the 2,699th was a
       manual pre-batch test, also verified). This is the largest single tree found in this bucket and was NOT
       anticipated by this row's original framing.
     - Legacy `lending_indices/{protocol}/{chain}/date=D/...` (matches the file's own, now-stale, docstring path
       pattern) — day-range diffed against tree 1: identical start date, ends 44 days earlier — confirmed a pure
       historical SUBSET, no separate migration needed.
     - `_index/` (`availability_index.parquet`, `per_vm/*.parquet`, `snapshots/pre_migration_2026_06_01.parquet`,
       `subgraph_fingerprints/`) — bucket-local manifest/fingerprint bookkeeping, not source data; the canonical bucket
       has its own independent manifest — not migrated, dies with the bucket by design.
  6. **Two live readers found + fixed that would have broken silently on delete** (neither previously flagged in this
     row, found via a targeted cross-repo grep for the bucket-name-construction pattern, not a blind trust that "nothing
     references it"): `deployment-api/deployment_api/services/data_status/defi.py` still read
     `lending-indices-{env}-{pid}` for the DeFi data-status drilldown's sub-dimension merge — a SAME-DAY-EARLIER commit
     (b5641cf) had dropped 9 sibling dead-bucket overrides from this exact dict but explicitly called lending-indices
     "the only survivor" (incorrect — its write path was already broken per fix #2 above; the real current data has been
     in the shared bucket all along). Dropped the override + sub-dimension entry so it falls through to the same
     main-DEFI-bucket read every other Phase-2 type already uses — `deployment-api@963d8e8`. Shipped via the
     **dirty-deps direct-push carve-out**: this repo currently carries 30+ uncommitted files from a concurrent agent's
     live WIP (confirmed via mtime — one file modified within the same minute), including a `NameError: STATE_BUCKET`
     genuinely broken `cache.py` (confirmed this breaks `deployment-service`'s own test suite via cross-repo import,
     unrelated to anything in this row); staged + committed ONLY the one intended file, used
     `git pull --rebase --autostash` to reconcile a 1-commit branch-drift without disturbing the foreign WIP (verified
     diff-stat unchanged after the autostash pop), then pushed directly (quickmerge would have tried to run QG against
     the genuinely broken tree). `deployment-service/deployment_service/vm_prefix_registry.py`'s
     `VM_PREFIX_TO_BUCKET["mtds-lending-indices-"]` zombie-watchdog shard-check also pointed at the flat bucket
     (`_LENDING_INDICES` hardcoded constant) — repointed to `_TICK_DEFI` (the same canonical bucket every sibling
     `mtds-*` DeFi VM-prefix entry already uses) — `deployment-service@539213a` (quickmerge).
  7. **Not fixed, flagged for follow-up** (adjacent, wider than this row's scope): `features-service`'s
     `onchain/app/core/dependency_checker.py` `UPSTREAM_DEPS_DEFI["market-tick-data-service-lending"]` is a
     `required: True` pre-flight gate whose `bucket_template` still points at the flat bucket — but its 3 siblings in
     the SAME dict (`lst-rates`/`oracle-prices`/`perp-funding`) already point at buckets deleted EARLIER this session
     (confirmed still 404 today via live `gcloud storage buckets describe`), so this is a pre-existing, wider gap this
     task didn't create — genuinely needs its own fix (repoint all 4 to the manifest-based check `vault_share_price`'s
     entry in the same dict already correctly uses), just out of this narrow todo's scope. Also left alone
     (low-priority, self-describing as disposable): `deployment-api/scripts/cleanup_ghost_venue_manifest_rows.py`
     (`# Lifecycle: oneoff`) still lists the flat bucket among 10 target buckets, 9 of which are already-deleted — the
     script itself is stale/dead pending its own delete-when condition.
  8. **Purge-lifecycle ARMED on both buckets, 2026-07-14T~14:00Z UTC** — identical
     `{"rule":[{"action":{"type":"Delete"},"condition":{"age":0,"isLive":true}}, {"action":{"type":"Delete"},"condition":{"daysSinceNoncurrentTime":0,"isLive":false}}]}`
     JSON used for the 6-sibling precedent earlier this session, applied via
     `gcloud storage buckets update --lifecycle-file=`, verified live on both via `buckets describe` immediately after
     arming. Flat bucket: unversioned, `soft_delete_policy.retentionDurationSeconds=604800`. `-prd` bucket:
     `versioning_enabled=true`, same soft-delete retention. **STATUS: ARMED, DRAINING — NOT YET 404** (a
     `gcloud storage buckets delete --quiet` attempt on either bucket right after arming would still fail "not empty",
     exactly as expected — the migrated objects above are additive copies into the CANONICAL bucket, not removals from
     the source buckets, so both still hold their full original object counts pending the async drain). Bucket delete is
     the follow-up one-liner once the drain confirms 0 live+noncurrent (same recipe as the 6-sibling precedent: retry
     `gcloud storage buckets delete gs://<bucket> --quiet`, success ⇒ immediately re-verify 404 via `buckets describe`).
     **Terraform note for whoever next runs `terraform apply` on the live state**: this session's TF edit only removed
     the IAM-binding resource block from config (source-level, resurrection-safe); the corresponding
     `terraform state rm google_storage_bucket_iam_member.t1_batch_lending_indices_object_admin` against the live
     `terraform/state/prod` state (on the orchestrator VM) has NOT been run from this session (no orchestrator-VM access
     here) — run it before the next apply, else the config-less state entry plans a destroy that may error depending on
     the binding's live state at that time.
  9. Repos touched: `market-tick-data-service@8e4d4960`, `deployment-service@2399d674` + `@539213a`,
     `deployment-api@963d8e8`. No repo QG-red from this row's own changes (deployment-service's own full-suite QG
     failure and market-tick-data-service's bandit finding were both independently confirmed pre-existing / unrelated
     before shipping — see points 2 and 6 above).
  10. **Post-migration full re-verification CLOSED — 2,776/2,776 (day,venue) pairs confirmed present in canonical**,
      with a methodology caveat worth recording: a 20-way-parallel `gcloud storage ls`-based re-check of the Kamino/
      Solend/Marginfi tree flagged 16 pairs as "missing" (0 objects). Re-checked every one of the 16 individually
      (isolated, unbatched `gcloud storage ls` / `objects describe` calls, no concurrency) — **all 16 were false
      negatives**: the objects were confirmably present (real size + md5 via `objects describe`) every single time when
      checked in isolation, and the SAME 16 flip-flopped between "found"/"not found" across repeated identical isolated
      re-checks run seconds apart — i.e. `gcloud storage ls` on a prefix is measurably unreliable under heavy concurrent
      load in this environment (likely connection-pool/auth-token contention, not a GCS-side consistency issue —
      `objects describe` on an exact path was consistently authoritative). Defensively re-ran the copy for all 16 anyway
      (idempotent — harmless whether already present or not) before closing this out. **Net: migration is genuinely 100%
      complete, 0 real gaps** — flagging the tooling quirk so a future high-concurrency re-verification pass in this
      workspace isn't misread as a data-safety regression.

- **2026-07-14, item A (`instruments-store-cefi` legacy twin) — OPERATOR-AUTHORIZED, purge RE-ARMED, async drain IN
  FLIGHT (not yet complete).** Operator explicitly authorized proceeding on the analysis already documented in this
  plan's item A row and the "2026-07-14, item A" log entry below: "lets fix the below and delete old buckets after
  migrations confirmed." Before acting, re-pulled this plan fresh and re-verified the bucket's live state had not
  materially changed since that prior analysis (spot-check, not a full corpus re-walk — the prior session's own
  full-corpus shape-aware diff already established the 28,228/51,637 legacy/prd counts and the true 4-key residual;
  re-running that identical full diff again would itself be the kind of redundant whole-corpus walk this task's floor
  rules caution against):
  1. **Lifecycle/versioning unchanged**: `gcloud storage buckets describe` showed the exact same reverted lifecycle
     (`NEARLINE@90` + `Delete daysSinceNoncurrentTime=30,numNewerVersions=3`), `versioning_enabled=true`,
     `soft_delete_policy.retentionDurationSeconds=0` as the prior session left it — no drift.
  2. **No new legacy-side writes**: listed `instrument_availability/by_date/day=2026-06*` and `day=2026-07*` — both zero
     objects; listed all `day=2026-05*` partitions sorted — newest is still `day=2026-05-22` (today is 2026-07-14, so
     ~53 days stale, exactly matching the prior finding, consistent with the documented ~53+-day zero-live-writer
     claim).
  3. **4-key residual re-confirmed present, unchanged**: listed `day=2026-03-01/` and `day=2026-03-02/` directly — both
     still show bare `venue=COINBASE` and `venue=OKX` alongside the already-split `COINBASE-SPOT`,
     `OKX-SPOT`/`OKX-FUTURES`/`OKX-SWAP` sub-venue keys for the same 2 days, exactly as the prior session documented.
     Attempted a fresh live-object-count baseline (`gcloud storage du -s`) to gauge magnitude per the task brief — it
     did not complete within a 280s bound (consistent with a genuinely large, ~28k-object corpus, not a shrunk one); did
     not force a longer full enumeration since the partition-level spot-checks above already positively confirm no
     material change.
  4. **Conclusion: live state materially UNCHANGED from the documented analysis** — proceeded per the operator's
     authorization (which was scoped to "the analysis as documented," and it still holds).
  5. **Purge re-armed**: applied the identical lifecycle JSON used for the 6 already-deleted siblings
     (`gcloud storage buckets update gs://instruments-store-cefi-central-element-323112 --lifecycle-file=...` with
     `{"rule":[{"action":{"type":"Delete"},"condition":{"age":0,"isLive":true}},{"action":{"type":"Delete"},"condition":{"daysSinceNoncurrentTime":0,"isLive":false}}]}`)
     at **2026-07-14T13:31:43Z UTC**; immediately verified live via `gcloud storage buckets describe` (new rule
     present). Unlike the prior session's arm-then-revert-within-1-minute, this arm is being LEFT IN PLACE per the
     operator's instruction to let it run to completion.
  6. **Baseline delete attempt**:
     `gcloud storage buckets delete gs://instruments-store-cefi-central-element-323112 --quiet` immediately after arming
     → failed with "Bucket is not empty" (expected — this bucket, unlike the 6 siblings which already had 0 live objects
     before their purge was armed, still holds its full ~28,228-object legacy corpus; nothing has been deleted from it
     yet by any prior session). This failure is the correct/expected baseline, not a problem.
  7. **Bucket shell NOT yet deleted — this is an in-flight async operation, not a completed one.** GCS's lifecycle
     evaluator runs on a roughly-24h cadence and must drain an order of magnitude more objects than the near-empty 6
     siblings did, so full drain plausibly takes materially longer than their ~24-48h window. Per this task's own
     framing and the async-wait-discipline rule (`codex/12-agent-workflow/async-wait-and-poll-discipline.md`), this is
     not something to force or block on synchronously — the correct completion path is a follow-up session re-running
     the same `buckets describe`/`buckets delete --quiet` check (exactly the 6-sibling "Async purge in flight" → "Async
     purge follow-up sub-task COMPLETE" two-step pattern already used earlier today), NOT a forced
     `gcloud storage rm -r` bulk delete (which would bypass the async lifecycle path this task deliberately mirrors).
     Repos touched: none (GCS metadata + a failed delete attempt only; no code changes, no repo shipped). Evidence: live
     `gcloud storage buckets describe`/`ls` transcripts this session (lifecycle/versioning check, day-partition
     spot-checks), live `gcloud storage buckets update --lifecycle-file=...` + `buckets describe` transcript (re-arm +
     verify), live `gcloud storage buckets delete --quiet` transcript (baseline "not empty" failure). Plan doc updated
     in this same commit, `unified-trading-pm` (docs(plans) commit, this file) — direct push per the PM-plan-docs
     carve-out.

- **2026-07-14, `instruments-store-sports-dev` full retirement — investigated, compared, retired, bucket deleted +
  404-verified.** Live-verified (not trusted from plan text): a Cloud Run job
  `uts-dev-instruments-service-sports-fixtures` was firing 4x/day (00:00/06:00/12:00/18:00 UTC via
  `uts-dev-sports-fixtures-{midnight,6am,noon,6pm}-t1-schedule`) plus a separate `uts-dev-features-sports-t1-schedule`
  at 02:30 UTC.
  1. **Comparison (real content, both sides)**: `gcloud run jobs describe` on both `uts-dev-` and
     `uts-prod-instruments-service-sports-fixtures` showed byte-identical args
     (`--operation=instruments --mode=batch --asset-group=SPORTS --sports-provider=API_FOOTBALL --run-tag=t1-recon`) —
     only `DEPLOYMENT_ENV` differs. Dev's job had actually been FAILING since at least 2026-07-10
     (`gcloud run jobs executions list` — every execution 2026-07-10→2026-07-12T18:01 shows `FAILED_COUNT=1`); its first
     success was an off-cadence run at 2026-07-12T22:31:09Z, so the bucket only ever held 3 days of content
     (`day=2026-07-12/13/14`). Read real objects on both buckets for those 3 overlapping days: dev = 5 entities
     (`fixtures_outcomes`, `fixtures_schedule`, `injuries`, `standings`, `teams`); prod = 9 entities for the same days,
     including 4 dev never captured at all (`fixture_events`, `fixture_lineups`, `fixture_stats`, `player_stats`).
     League breadth: prod's `standings`/`teams` cover ~90 leagues per day vs dev's ~30; for `fixtures_schedule`
     specifically, day=2026-07-13 and day=2026-07-14 are IDENTICAL league-for-league between dev and prod (2 leagues and
     4 leagues respectively, exact same names). The one divergent day (day=2026-07-12: dev's
     `fixtures_schedule`/`fixtures_outcomes` had 8 leagues, prod only 1 — `K_LEAGUE_2`) was checked directly rather than
     assumed unique: prod's `teams` entity for that SAME day already covers all 8 of dev's leagues (`ALLSVENSKAN`,
     `ARGENTINA_PRIMERA_NACIONAL`, `BRASILEIRAO_SERIE_B`, `COPA_ARGENTINA`, `COPA_CHILE`, `ELITESERIEN`, `K_LEAGUE_1`,
     `K_LEAGUE_2`) — so prod already had full reference coverage of every league dev touched that day; the
     fixtures_schedule/outcomes narrowness that one day is best explained by dev's very first (off-cadence,
     post-multi-day-failure) successful run sweeping a broader match- calendar window than prod's steady-state per-run
     window, not a sustained unique capture. **Conclusion: dev held no genuinely unique data — prod is a strict
     superset** (deeper entities, ~3x league breadth, longer history back to 2019 and forward-scheduled to 2026-12) — no
     migration was needed or performed.
  2. **Dead scheduler found + noted**: `uts-dev-features-sports-t1-schedule` targets a Cloud Run job
     (`uts-dev-features-sports-service-t1-recon`) that has never existed on EITHER tier (`gcloud run jobs describe` 404s
     for both dev and prod variants) — confirmed via `gcloud scheduler jobs describe` `status.code=5` (NOT_FOUND) on its
     last attempt (2026-07-14T02:30:21Z) and via `gcloud logging read` showing `NOT_FOUND` errors on every fire. This
     scheduler was never writing anything on either tier — a pre-existing dead entry, not a live producer this session's
     task brief slightly overstated. The `features-sports-service-job`/`daily_workflow` Cloud Run job (a SEPARATE, real,
     already-live service under `terraform/services/features-sports-service/`) is untouched — not the same pipeline, not
     in scope.
  3. **Retirement executed**: `deployment-service@926ba192` — `terraform/gcp/t1_batch_scheduler.tf`'s
     `t1_batch_services` for_each now excludes `sports-fixtures-{6am,noon,6pm,midnight}` + `features-sports` keys when
     `var.environment == "dev"` only (staging/prod entries for this exact pipeline are byte-unchanged); QG green (201s),
     quickmerge → live-defi-rollout. Live resources deleted directly via `gcloud` (mirrors this session's earlier
     cefi/defi/sports-legacy consolidator-cron removal pattern — terraform source edited first, no blind
     `terraform apply` since dev's terraform state isn't safely applyable per this session's earlier tfvars finding):
     all 5 `uts-dev-*` Cloud Scheduler jobs (`sports-fixtures-{midnight,6am,noon,6pm}-t1-schedule` +
     `features-sports-t1-schedule`) deleted; Cloud Run job `uts-dev-instruments-service-sports-fixtures` deleted.
     Re-verified via `gcloud scheduler jobs list`/`gcloud run jobs list` post-delete: zero `uts-dev-*sports*` entries
     remain anywhere (staging's `uts-staging-features-sports-t1-schedule` and all `uts-prod-*sports*` entries are
     untouched, out of scope). Grep-clean: workspace-wide `rg` for `instruments-store-sports-dev`/`sports-dev-central`
     found zero hardcoded construction sites (only this plan's own prose + a generic `resolve_bucket_name` docstring in
     `instruments_service/reference_data/sports_dependency.py` documenting the resolver's general dev-tier support,
     which the Wave-0 ruling explicitly keeps: "resolver keeps supporting the tiers"); `_tradfi-ohlcv-launcher-lib.sh`
     checked and contains zero sports references (unrelated file for this pipeline).
     `deployment_service/ cloud_run_job_registry.py`'s stem entries for
     `instruments-service-sports-fixtures`/`features-sports-service-t1-recon` are environment-agnostic classification
     stems (used by the deployment-observability dashboard across ALL tiers) — left unchanged since staging/prod jobs
     still need them; the guard test (`test_cloud_run_job_registry_guard.py`) statically greps the raw `.tf` text for
     `name=`/`job_name=` strings (does not evaluate the `var.environment` conditional), so it still passes post-change.
  4. **Bucket deletion + 404-verify**: `gcloud storage buckets describe` confirmed no `versioning_enabled` field
     (versioning OFF) before deleting — no version-aware handling needed;
     `soft_delete_policy.retentionDurationSeconds = 604800` (7-day GCS soft-delete, does not block deletion).
     `gcloud storage rm -r gs://instruments-store-sports-dev-central-element-323112` removed all live objects (306
     parquet files across `_index/`, `instrument_availability/`, `sports_reference/`) then the bucket itself;
     immediately re-verified via `gcloud storage buckets describe` → **404 confirmed**. Estate count: −1 (this bucket
     only; no other buckets touched — tradfi/prediction and every other named-out-of-scope bucket were not touched).
     Evidence: live `gcloud run jobs describe`/`executions list`/`scheduler jobs describe`/`logging read` transcripts
     (comparison); `deployment-service@926ba192` (terraform, QG green 201s, quickmerge → live-defi-rollout); live
     `gcloud scheduler jobs delete` ×5 + `gcloud run jobs delete` ×1 transcripts (scheduler/job retirement); live
     `gcloud storage rm -r` + `buckets describe` 404 transcript (bucket deletion). Repos touched: deployment-service
     only.

- **2026-07-14, item A (`instruments-store-cefi` legacy twin) — investigated to a genuine resolution; the "27,225
  legacy-only objects" figure was a partition-shape-blind diff-tool false alarm, not a real data gap.** Full session
  (all commands run live against `central-element-323112`, nothing trusted from plan text):
  1. **Rsync process check**: `aws ssm send-command` (`AWS-RunShellScript`) against orchestrator VM
     `i-0c9b283b31d6b5ca7` (13.113.200.22) — `ps aux | grep rsync` returned nothing (not running);
     `cat /home/ubuntu/tmp/cefi_rsync.log` showed `RSYNC START` → `RSYNC_DONE rc=0` in 8 seconds
     (2026-07-14T01:08:17→01:08:25Z); the script (`/home/ubuntu/tmp/cefi_rsync.sh`) is a raw
     `gcloud storage rsync -r gs://instruments-store-cefi-$PID gs://instruments-store-cefi-prd-$PID` — a literal
     relative-path copy, no shape translation.
  2. **Real partition shapes, read from objects (not guessed)**: legacy bucket top-level = `_catalogue/`, `_index/`,
     `instrument_availability/`, `reference_data/`; legacy `instrument_availability` shape =
     `by_date/day=D/venue=V/{instruments,futures_contracts}.parquet`. Canonical prd shape = the SAME prefix but with two
     extra required hive segments inserted before `venue=`: `pipeline_mode=batch_instruments_service/asset_group=cefi/`.
     This is the documented 2026-05-19 "bundled GCS migration" pipeline_mode rollout
     (`codex/02-data/pipeline-mode-partition.md`) — a known, already-solved migration class, not a novel shape problem.
     Parquet schema diff (pyarrow, `instruments-service/.venv`): legacy = 39 cols; prd-canonical = 47 cols (superset:
     adds `canonical_instrument_id`, `product_root`, `exercise_style`, `source_archive_url_template`,
     `source_record_types`, `source_coverage_start/end`, `listed_at`, `delisted_at`, `available_at`).
  3. **Reader recognition**: confirmed via `instruments_service/engine/orchestrator/writers.py` that the CURRENT live
     orchestrator dual-writes both a bare-shape record (line ~150-158, `_gated_sink_write`, unconditional, sink prefix
     `instrument_availability/by_date`) AND, when a manifest is supplied, a `pipeline_mode=`/`asset_group=`-partitioned
     record via the manifest writer (`record_captured(pipeline_mode=...)`) — the canonical reader/consolidator
     prefix-matches on `pipeline_mode=` per the codex SSOT, so a blind bare-shape copy would be invisible to it. This is
     exactly what an EARLIER (pre-this-session) blind-copy attempt already did: found ~6,286 bare-shape objects already
     sitting inside the canonical prd bucket's own tree (creation_time 2026-07-13T23:45Z, i.e. before this session and
     before the 01:08Z rsync log), byte-identical to legacy in the one case spot-checked (crc32c/md5 match) — these are
     dead, orphaned, non-canonical duplicates the live reader ignores; harmless (no overwrite) but a hygiene issue
     **inside the canonical bucket** — flagged for a separate owner decision, NOT deleted by me (out of this task's
     scope to unilaterally clean the canonical bucket).
  4. **Verification instead of a blind bulk copy**: rather than re-partition-and-copy at scale, did a full-corpus
     SHAPE-AWARE re-diff — extracted `(day, venue)` keys from ALL 28,228 legacy objects and ALL 51,637 prd objects
     (stripping the `pipeline_mode=`/`asset_group=` segments before matching, `.bak.parquet` migration-backup files
     excluded) and `comm -23`'d them. Result: **true legacy-only = 4 keys** (`venue=COINBASE`/`venue=OKX` bare-name,
     2026-03-01 and 2026-03-02 only) — a venue-naming-scheme transition artifact (legacy used one undifferentiated
     `COINBASE`/`OKX` key those 2 days; canonical prd already has the split `COINBASE-SPOT`/`COINBASE-FUTURES` and
     `OKX-SPOT`/`OKX-FUTURES`/`OKX-SWAP` sub-venue captures for the SAME 2 days) — not a real gap. Content-verified
     (pyarrow row counts, not just path existence) across 7 day/venue samples spanning the full 2019→2026 legacy date
     range (DERIBIT/BINANCE-SPOT/BYBIT/OKX-SWAP/UPBIT/HYPERLIQUID/ASTER): canonical prd row count ALWAYS ≥ legacy,
     typically far more complete (e.g. 2019-03-30 DERIBIT: legacy=6 rows vs prd=295 rows; 2026-05-22 ASTER: legacy=19 vs
     prd=419) — prd is a genuinely richer re-capture of the same history, not a mechanical repartition of the same rows.
     Also confirmed: zero live code anywhere in the workspace (`rg -n "instruments-store-cefi(?!-)"`) references the
     flat bucket name; the resolver can no longer construct it (`configs/cloud-providers.yaml` — dev/stg tiers retired,
     prd+test only); legacy bucket's last object write was 2026-05-22 (~53 days stale — consistent with the prd bucket's
     2026-05-12 creation + a short dual-write tail before full cutover).
  5. **Purge decision — armed, then deliberately reverted**: applied the identical purge-lifecycle used for the 6
     already-deleted siblings
     (`gcloud storage buckets update gs://instruments-store-cefi-central-element-323112 --lifecycle-file=...` with
     `{"rule":[{"action":{"type":"Delete"},"condition":{"age":0,"isLive":true}}, {"action":{"type":"Delete"},"condition":{"daysSinceNoncurrentTime":0,"isLive":false}}]}`),
     verified it took (`gcloud storage buckets describe` showed the new rule live), then **reverted it ~1 minute later**
     back to the bucket's original lifecycle (`NEARLINE@90` + `Delete daysSinceNoncurrentTime=30,numNewerVersions=3`) —
     well inside GCS's ~24h lifecycle-evaluation cadence (spot-checked a sample object post-revert: still present,
     23,959 bytes, unchanged). Reason for the revert: `codex/02-data/pipeline-mode-partition.md`'s 2026-06-18-codified
     **GCS DELETE-SAFETY HARD RULE**, found mid-session and directly on point for this exact
     legacy-bare-shape-vs-canonical- pipeline_mode-shape class of decision — verbatim _"Require 100% canonical-twin
     coverage per AG before executing that AG's delete-list; deletion is OPERATOR-GATED."_ This session's shape-aware
     diff reaches 28,224/28,228 = 99.986% literal per-key twin coverage (the 4-key residual is confidently explained as
     superseded-by-rename above, not missing data — but that is an interpretive judgment, not a path-verified twin), so
     arming the actual purge/delete correctly needs an OPERATOR go per the HARD RULE's letter rather than an autonomous
     execution, even though the underlying data-safety case is strong. **No data was lost or purged — this was
     arm-then-immediately- revert, verified both ways.** Full narrative + the exact commands to re-run once the operator
     clears the 4-key finding are in item A's row above (`## Round-2 final state` table). Repos touched: none (GCS
     metadata operations only, reverted; no code changes, no repo shipped). Evidence: live
     `gcloud storage buckets describe`/`update` transcript this session (before/during-arm/after-revert), live SSM
     transcript against `i-0c9b283b31d6b5ca7`, live pyarrow schema/row-count reads of 9 sampled parquet objects across
     both buckets.

- **2026-07-14, Async purge follow-up sub-task COMPLETE — all 6 L6/dex-pools-prd twins confirmed 404-deleted.**
  Live-re-verified (not trusted from plan text) all 6 lifecycle-purge-armed buckets named in the prior "Async purge in
  flight" note: `market-data-tick-{cefi,defi,tradfi}`, `instruments-store-{defi,tradfi}`, `dex-pools-prd` (all
  `-central-element-323112`). Pre-check: `gcloud storage buckets describe` confirmed versioning + soft-delete config (3
  tick buckets + dex-pools-prd: `soft_delete_policy.retentionDurationSeconds=604800`; 2 instruments-store buckets:
  retention `0`/disabled); live-object listing already 0 on all 6. Per the task's specified safe non-destructive check,
  ran a real `gcloud storage buckets delete gs://<b> --quiet` per bucket (refuses with a "not empty" error, no deletion,
  if any live-or-noncurrent version survives) — **all 6 succeeded** on the first attempt (no force-purge needed; the
  async lifecycle had already fully drained within its ~24-48h window, armed 2026-07-13, checked 2026-07-14T10:57Z),
  each immediately re-verified 404 via `gcloud storage buckets describe`. Independently re-counted estate:
  `gcloud storage buckets list` → **145** (vs ~147 estimate). `instruments-store-cefi` (7th twin, real 2019-era data,
  27k+-object legacy-vs-prd gap) explicitly left untouched — out of this sub-task's scope, owned separately. Evidence:
  live `gcloud` describe/delete/describe transcript this session (no code changes, no repo shipped — GCS operations
  only); plan doc updated in this same commit, `unified-trading-pm` (docs(plans) commit, this file).

- **2026-07-14, Deferred #8 done — setup-buckets.py + bucket_config.yaml rewritten onto the canonical resolver.**
  `deployment-service@344958c1` (+359/−528 across `scripts/setup-buckets.py`, `configs/bucket_config.yaml`,
  `configs/BUCKET_CONFIG_SCHEMA.md`): the script no longer reads `dependencies.yaml`'s pre-canonical `bucket_template`
  scheme (whose `{category_lower}` placeholder the old local resolver never substituted — literal-placeholder names,
  confirmed by the 2026-05-10/2026-07-13 audits). It now enumerates `configs/cloud-providers.yaml`'s `<cloud>.storage`
  kinds x asset_group exactly like `terraform/gcp/canonical_buckets.tf`'s `for_each` derivation (same excluded-kinds
  set: `audit-records`/ `manual-audit`, retention-locked + hand-managed) and resolves every name through
  `unified_trading_library.resolve_bucket_name` — the same SSOT the terraform already uses, so the two stay in lockstep
  by construction rather than by hand-copied convention. Tiers are `prd` + `test` only (dev/stg retired per this plan's
  Wave-0 ruling); the `-test-` infix-string hack (`get_test_bucket_name`) is deleted — the test tier is just
  `deployment_env="test"` resolution, same mechanism as prod. `--project-id` still bootstraps a brand-new project
  (bridges into the process env the UTL resolver reads `${GCP_PROJECT_ID}`/`${AWS_ACCOUNT_ID}` from — same pattern
  `setup-dev-project.sh` already relied on). Found + fixed a pre-existing latent bug in the same area:
  `get_default_values()` unconditionally called `get_project_id()`/`get_aws_account_id()` even when the caller only
  wanted the region default, so `--project-id <new-project>` without ALSO exporting `GCP_PROJECT_ID` crashed — split
  into `get_default_region()` + `get_default_values()`. `bucket_config.yaml` is now ONLY the registry of genuine infra
  buckets (terraform-state, deployment-orchestration, build-metadata, databento-batch-registry, backtest-results,
  client-reporting-data, events, unified-deployment-state, uts-terraform-state, config-store) — stripped the stale
  `eigenlayer-rewards`/`ml-configs-store`/`features-volatility-defi` (+ `-test` twins) entries that duplicated (and for
  the first two, drifted from — they were flat, non-env-tiered) the canonical cloud-providers.yaml matrix, plus the dead
  `aws_bucket_mappings`/`test_buckets`/`validation` sections the deleted local resolver
  (`resolve_bucket_name()`/`get_test_bucket_name()`/`convert_to_aws_bucket_name()`) consumed. `dependencies.yaml` is
  UNTOUCHED — grep-then-READ on every `bucket_template` consumer turned up a genuinely separate, still-live one:
  `deployment_service.dependencies.DependencyLoader._check_single_dependency()` reads those same fields for its own
  dependency-check machinery (added to Deferred as #11, see below — it has its own, different bug in the same root-cause
  family). **Verification**: `--help` clean; `--list-only --include-test --project-id central-element-323112` produces
  89 buckets (66 prd + 23 test) with zero `{category_lower}` literals, matching the `canonical_buckets.tf` comment's
  already-verified 79-canonical-bucket count (89 total − 10 infra = 79); a REAL `--dry-run` against
  `central-element-323112` (live ADC present in-session) showed 88/89 resolved names already `[EXISTS]` on live GCS —
  only `config-store-central-element-323112` (the legacy flat name, unrelated to this tick, tracked separately as item
  #3) is genuinely absent (`gcloud storage buckets describe` confirms 404); `--test-only`,
  `--service instruments-service` (best-effort kind-name filter, replacing the old service-name join), and `--cloud aws`
  all produce correct names. SIT `system-integration-tests/tests/conftest.py`/ `tests/smoke/test_cloud_infra_smoke.py`
  untouched — simulated `required_gcs_buckets` against the trimmed `bucket_config.yaml` still returns 26 buckets (well
  above the `test_required_buckets_list_non_empty` `>=10` floor), so no SIT edit was needed. `deployment-service`
  quality-gates.sh green (83s; one non-blocking baseline-ratchet-DOWN warning on
  `no_empty_string_fallback_baseline.yaml`, left for the next agent's `--update-baseline` since it isn't blocking and
  touches a shared PM baseline file outside this tick's repo scope). **Shipped via the dirty-deps direct-push
  carve-out**, not quickmerge: `unified-trading-library` had live, foreign WIP mid-edit
  (`manifest_writer/_read_index.py` + its test, mtime <120s — liveness-gated PROTECT, left untouched) blocking
  quickmerge's pre-flight dep-audit; this change only imports UTL's long-stable
  `resolve_bucket_name`/`AssetGroup`/`BucketNamingError`, unrelated to manifest_writer, so a direct `git push` of the 3
  changed scripts/configs files (both outside the strict-quickmerge CODE-trailer requirement's scope) was the correct
  carve-out per `codex/08-workflows/ci-cd-flow.md`. **Two new findings captured as Deferred #11/#12** (same
  `{category_lower}`-vs-`asset_group_lower` root cause as the bug this tick fixed in setup-buckets.py, but in two
  different, still-live consumers this tick's repo scope didn't cover): `deployment_service/dependencies.py`'s
  `DependencyLoader` dependency-check machinery, and `system-integration-tests/tests/conftest.py`'s own separate
  bucket-enumeration helper.

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

- **2026-07-14, TERRAFORM RECONCILIATION (operator: "fix these both properly").** Both caveats resolved to the extent
  that is MINE and safe; a full `terraform apply` is now free of every landmine I introduced. Work (live prod state,
  `terraform/state/prod`, via the orchestrator VM):
  - **Caveat #1 — over-removed resources FULLY FIXED**: re-imported the 6 live resources my earlier straggler-rm wrongly
    removed (`defi_collect_cron`+`defi_collect_job` for liquidations & solana-defi, the liquidations pubsub topic +
    `liquidations-sub`). Import was blocked by a fragile for*each output that couldn't evaluate during partial-state —
    shipped a robustness fix (`defi_collect*{job,cron}\_names` now iterate in-state instances, not the local map).
    ds@39fa8c3.
  - **Purge-revert landmine FIXED**: the 5 purge-armed legacy twins (`market_data_{cefi,defi,tradfi}`,
    `instruments_{defi,tradfi}`) showed in-place lifecycle changes that a full apply would have used to REVERT my
    out-of-band purge back to NEARLINE@90 — removed their resource blocks + the one dangling output + state-rm'd them
    (they stay live/purging, TF-unmanaged until the shell is deleted; lending-indices-prd precedent). ds@39fa8c3.
  - **Stale-state cleanup**: state-rm'd the 2 already-physically-deleted `-prd` buckets (lst-rates, perp-funding) + the
    2 strategy-store-cefi IAM members (bucket deleted). Then **applied my 3 IAM bindings** (targeted apply, 3 added
    live) onto the flat strategy-store + lending buckets — completing the strategy-store split-brain + the
    subgraph-probe lending binding (item C dependency). Verified: re-plan shows ZERO of my
    strategy-store/lending/lst-rates/perp-funding work pending. No container images change on any in-place resource.
  - **Residual full-apply delta — NOT mine, deliberately NOT auto-applied** (1 import / 5 add / 10 change / 15 destroy):
    (a) **`odum_portal` domain mapping → activates `portal.odum-research.com`** (production customer domain on the
    operator's company domain — a genuine go-live decision, not a bucket-cleanup side-effect); (b) `deployment_digest` +
    `governance_snapshot_monitor` cron+job — other-workstream monitoring features, committed but unapplied; (c) 14
    legacy manifest-consolidator crons/jobs teardown (market-data/instruments `-legacy` + gas-fees) — correct downstream
    of the retired kinds, but the sports-legacy pair touches the held sports plan; (d) ONE to sanity-check:
    `t1_batch_schedule["features-onchain"]` destroy — a live feature's schedule removal from a sibling commit; confirm
    intended before applying. This residual is committed config awaiting its owners' deploy decision; applying it is
    safe from a _my-drift_ standpoint (0 of my resources, no image reverts) but activates a prod domain
    - changes a live pipeline, so it needs an owner/operator green-light, not an autonomous bucket-dispatch apply.

- **2026-07-14, ROUND 2 DISPATCH END (rule-9 report).** **Estate 241 → 153** (−88; a further ~6 pending async purge →
  ~147). Full executable-and-safe scope of the operator's round-2 GO is DONE: strategy-store trio, football ×4, DeFi
  lst/perp-prd, flat config-store all migrated-then-deleted; 6,941-object DeFi parity gap + a 27,225-object cefi
  availability shape-difference both CAUGHT before any destructive step (the cefi one correctly HELD as owner-gated, not
  forced — the single most important safety call of the round). Deferred items 3/7/8/9 CLOSED this round (config delete,
  codex, setup-buckets rewrite, UAC resolver); 2 new same-root-cause findings (#11/#12) captured. 8+ code ships across 7
  repos, every QG/v2 green. **Genuine remainder = 9 gated items (A-I above), each with a specific unblock condition,
  zero silent DEFERRED.** Observed a CONCURRENT session co-executing this dispatch (config-store deleted ~4.7min ahead
  of my own idempotent delete; plan rows co-edited) — converged rather than duplicate destructive ops (rule 4). Loop
  TERMINATED: the 3h+ window's success criteria met — W0/W1 fully applied + drift-proof, the bulk of W2 executed with
  two real data-gaps caught, W3 designed; everything left is either async-completing (purge) or genuinely
  owner/producer-gated.

- **2026-07-14, L6 pre-purge verification CAUGHT A SECOND REAL GAP.** The lean legacy-vs-prd diff found
  **instruments-store-cefi flat holds 27,725 legacy-only objects** (2020-era `instrument_availability/by_date/` trees)
  absent from the canonical `-prd` bucket — the June ratio-1.00 verification evidently covered the tick corpus, not
  instruments availability history. Purge-arm correctly HELD on all 6 twins (chain gates on any truncated gap). Verified
  clean: instruments-store-tradfi (0 legacy-only of 11,460), instruments-store-defi (0 of 69,108);
  market-data-tick-tradfi diff still running. Fix in flight: detached `gcloud storage rsync -r` legacy→prd for
  instruments-store-cefi (PID on VM, log /home/ubuntu/tmp/cefi_rsync.log); purge arms only after re-diff = 0. Estate
  count now **155** (from 241). Also shipped: deployment-service@1dd2159 (lending-indices-prd TF block removed —
  resurrection class; flat lending bucket found to have a LIVE writer: subgraph-health-probe fingerprints via t1_batch
  IAM — its `_resolve_bucket()` must be repointed before that bucket can ever be deleted). State-surgery side-note: a
  straggler sweep over-matched 7 live+declared non-bucket resources (liquidations/solana-defi collect crons+pubsub+jobs
  — data_types remain LIVE into the shared bucket; only bucket kinds were retired) — they now show as plan ADDS;
  re-import commands belong to the drift review (Deferred #5, import IDs enumerated there).

- **2026-07-13/14 (round 2 landings).** deployment-api prod VERIFIED on the flat fix without intervention (auto
  promote+build pipeline; revision 00158-m5x live-curled — all 3 strategy-store entries flat) → strategy-store per-AG
  trio RETIRED (cefi's 105 residual objects preserved to flat `legacy_cefi/`, count-verified, 3 buckets deleted).
  Football ×4 MIGRATED (455+119+107+37 objects, count-verified into backtest-results/football,
  ml-models-store-prd/legacy_football,
  instruments-store-sports-prd/legacy_football/{mapped_consolidated,raw_all_sources}) and deleted. **DeFi trio agent
  found + closed a REAL parity regression before deletion: 6,941 objects missing from the shared bucket** (5 whole dex
  venues, GMX 2021-23 funding, HL perp_daily 177d+perp_mark_price, 7 CeFi Tardis venues' perp shards silently absent
  from funding_for_day post-cutover, 5 LST venues' early history, 21 dex_pool_fees rows contradicting the earlier "zero
  rows" read) — all copied + re-verified through the deployed readers (funding_for_day 697 obs incl. all cefi venues;
  pairs_for_day == baseline). strategy-service confirmed tarball-deployed ephemeral VMs (nothing to restart; tarball
  @a4ea4fa7 sha-verified to contain the readers). DeFi kinds removed from ALL FIVE yaml copies (34 kinds; 5th copy
  found: PM scripts/quality-gates-base/ ci-test-cloud-providers.yaml): uac@252c0072, utl@1177768b, ds@f04cc39b,
  e2e@3d219d76, mtds@02a88186 (also Tardis lease default → resolver), PM@abcd47b4+@5f0efb01 (defi-plan flips). L6 twins:
  first detached rm attempt no-op'd on a FULL VM tmpfs (nothing deleted, verified all 6 EXIST); recovery = state backups
  secured to GCS, tmp freed, 6-twin in-memory legacy-vs-prd diff + gap copy, then LIFECYCLE PURGE (age=0 + noncurrent=0)
  armed — GCS purges async ~24h, bucket delete is the follow-up one-liner. Sports pair still HELD (E1). In flight: trio
  state-rm + lst-rates-prd/perp-funding-prd deletion + dex-pools-prd purge-arm (209k undiffed legacy-tree objects →
  async purge = 24h abort window) + zombie backfill VM stops (operator-flag: 16-day stall, 0 events).

- **2026-07-13 (late), ROUND 2 — operator returned + authorized the remainder.** Verbatim rulings: prod redeploys
  authorized; Tardis lease fine to move ("authenticationless"); "for the rest … why can't we migrate and delete" +
  ticked: L6 legacy twins, DeFi -prd trio (after redeploy+parity), football migrate-to-canonical-homes+delete; ASTER
  originals moved to the ASTER plan (todo added there this commit). Round-2 execution: 3 agents relaunched after a
  session-limit interrupt (deployment-api prod redeploy+verify; PATH_REGISTRY-ml/config-store literal repoints across
  UTL/IS/SIT; DeFi trio redeploy+parity+config-removal incl. MTDS lease default). Orchestrator SSM ops: legacy
  consolidator crons paused, tradfi legacy-vs-prd object diff + gap copy, football ×4 migrate→verify→delete into
  backtest-results/{football}, ml-models-store-prd/{legacy_football}, instruments-store-sports-prd/{legacy_football},
  and DETACHED version-aware deletion of the 6 verified L6 twins (market-data-tick + instruments-store ×
  cefi/defi/tradfi flat). **Sports pair HELD** — instruments-store-sports flat carries 316 legacy-only cells owned by
  sports_manifest_canonicalisation E1/E8; not covered by the June legacy⊆canonical verification. Deletions of
  strategy-store-{defi,tradfi,cefi}, flat config-store, flat ml trio remain gated on the three agents' verify reports,
  then execute this session.

- **2026-07-13, /autonomous dispatch END (rule-9 report).** Verified end-state: **estate 241 → 164** (79 W1 deletions,
  +2 recon); terraform reconciled + derived-from-yaml + APPLIED (0 bucket destroys; drift-proof for buckets —
  `terraform plan` from deployment-service@42d4035 is now the estate drift detector); COLDLINE@60d live on all 79
  canonical for_each buckets; all 4 cloud-providers.yaml copies at 37 kinds; 8 code ships across 6 repos
  (uac@f84e5b37+@155093a1, utl@3382cc7c, ui@2796d38b+@1bf1bc1a, ds@ccfaca26+@42d4035, dapi@6da793b, blrs@2f0380b,
  e2e@16efd49) with QG green each and v2 CI green where it fired. Forced-tradeoff decisions, each documented at its
  todo: recon = env-tiered yaml kind; execution-store deployment-api default = CEFI; manual-audit TF-unmanaged (locked
  retention); flat ml trio + flat config-store + strategy-store-{defi,tradfi} deletions deferred with precise unblock
  conditions. Nothing operator-blocking was skipped silently — the 10-item Deferred table above is the complete
  remainder, each row with its unblock condition. W2 items owned by other plans (DeFi -prd deletions, L6 legacy twins,
  football) were deliberately NOT force-run per their own gates. Loop terminated: success criteria for the 3h window met
  (every executable W0/W1 item done; W2 partials + W3 design landed; tracking current).

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

- **2026-07-14, item D (recon end-to-end green) — (a) BLRS prod digest issue found + fixed + verified; (b) t1-recon
  producer chain investigated to a precise, well-scoped, genuinely-out-of-plan finding.** Nothing trusted from the
  plan's prior text alone — every claim below re-verified live before acting.

  1. **(a) Checked whether the digest bump + LDR→main promote had already landed**:
     `git log`/`git show origin/main:Dockerfile` + `origin/main:batch_live_reconciliation_service/config.py` on
     `batch-live-reconciliation-service` confirmed both `28a18fa` (digest bump to `sha256:b7e391f8`) and `2f0380b`
     (resolver-repoint config fix) were already on `main` by content (`gh api compare/main...live-defi-rollout` shows
     LDR 53 ahead / 0 behind — squash-promote, so ancestry checks alone are misleading; content match on both files is
     the real proof). `gcloud artifacts docker images list` on the BLRS Artifact Registry repo showed the `:latest` tag
     was built off commit `7b65341` (2026-07-14T00:46:44Z, well after both fixes) and the live Cloud Run Job's most
     recent execution (`uts-prod-batch-live-reconciliation-service-v8jt9`, the real 06:00Z 2026-07-14 scheduled run) had
     in fact run against that exact image digest (`sha256:416b0f60`) — so the prod-pickup question was genuinely
     answered: yes, already picked up.
  2. **But that same 06:00Z run had STILL failed** — read its logs (`gcloud logging read`) rather than trusting the
     plan's "should be fixed" framing: `BucketNamingError: Unknown kind 'recon' for cloud 'gcp'` — a DIFFERENT error
     than the one this plan's history documents, thrown from inside `resolve_bucket_name()` itself, before Stage 0 even
     starts. This meant the resolver-repoint fix (2f0380b) was reachable but the runtime's own copy of
     `cloud-providers.yaml` didn't recognize `recon` as a valid kind at all.
  3. **Root-caused via direct image inspection, not guessing**: `docker pull` + `docker run --entrypoint find/grep` the
     EXACT deployed image digest (`sha256:416b0f60...`) — found it packages `unified_api_contracts` at
     `/app/.deps/unified-api-contracts/` (baked in by the UTL base image's own build), version
     `0.72.1.dev195+g21dde0f8c`. `grep -c recon` on that copy's `cloud-providers.yaml` returned 0. Checked the UAC repo:
     `21dde0f8` (2026-07-13T16:39:42Z) is confirmed an ANCESTOR of `f84e5b37` (2026-07-13T20:11:34Z, the commit that
     actually added the `recon` kind) — i.e. the UTL base image BLRS's Dockerfile pinned (`sha256:b7e391f8`, itself
     refreshed at 17:44Z that same day per its own commit message) captured a UAC snapshot from BEFORE the recon-kind
     fix existed upstream. A same-day base-image-refresh-vs-upstream-fix race, not a bug in BLRS's own code or in the
     resolver repoint.
  4. **Fix**: found the CURRENT `:latest` UTL base image (`sha256:9594091a`, built 2026-07-14T18:17:27Z) via the same
     `gcloud artifacts docker images list` + pulled it + inspected its packaged UAC copy — `grep -c recon` returned 7,
     and its UAC version (`0.72.1.dev230+ged622d8b1`) confirmed via `git merge-base --is-ancestor f84e5b37 ed622d8b1` to
     be a genuine descendant of the recon-kind commit. Bumped BLRS's `Dockerfile` `ARG BASE_IMAGE_DIGEST` to this digest
     — `batch-live-reconciliation-service@be056b1` (QG green, quickmerge `--agent --files 'Dockerfile'`). Landed on LDR
     only (this repo's quickmerge targets staging first); rather than wait on the LDR→staging→main promotion chain to
     reach the `main`-only Cloud Build trigger, ran
     `gcloud builds triggers run batch-live-reconciliation-service-build --branch=live-defi-rollout` directly (build
     `ab591245-708a-4c84-a080-7f4d3a9d6a15`) — SUCCESS, new image `sha256:763b5446` pushed + tagged `:latest`
     2026-07-14T20:07:32Z (confirmed via `gcloud artifacts docker images list`).
  5. **Verified with a real triggered execution**
     (`gcloud run jobs execute uts-prod-batch-live-reconciliation-service --wait`, execution
     `uts-prod-batch-live-reconciliation-service-pn4f7`) — read its logs: config now resolves
     `recon_bucket=recon-prd-central-element-323112` correctly (no more `BucketNamingError`), and Stage 0 fails with
     exactly the EXPECTED, already-documented message:
     `Missing upstream data for 2026-07-13: execution config snapshot: gs://execution-store-cefi-.../configs/snapshots/2026-07-13/config.json; ML t1-recon outputs: gs://recon-prd-.../t1-recon/ml/2026-07-13/_SUCCESS; strategy t1-recon outputs: gs://recon-prd-.../t1-recon/strategy/2026-07-13/_SUCCESS`.
     This is real, current, live proof that (a) is closed — the job now genuinely reaches Stage 0's real gate instead of
     crashing before it.
  6. **(b) Traced the t1-recon producer chain concretely**, per `codex/08-workflows/t1-batch-dag.md` (the SSOT for this
     DAG) cross-referenced against LIVE Cloud Scheduler + Cloud Run Job state (not code-only inference):
     - **execution-service config-snapshot** (00:30 UTC, feeds Stage 0's `configs/snapshots/{date}/config.json` check):
       `gcloud scheduler jobs describe uts-prod-execution-config-snapshot-t1-schedule` — `ENABLED`, fires daily;
       `gcloud run jobs list --filter="metadata.name~execution"` — the target Cloud Run Job
       (`uts-prod-execution-service-config-snapshot`) does not exist in the list at all (only 3 unrelated
       manifest-consolidator jobs match). This producer has never been provisioned.
     - **ml-service t1-recon** (03:00 UTC, feeds `t1-recon/ml/{date}/_SUCCESS`):
       `gcloud scheduler jobs describe uts-prod-ml-t1-schedule` — `ENABLED`, `0 3 * * *`;
       `gcloud run jobs describe uts-prod-ml-service-t1-recon` — "Cannot find job"; `gcloud logging read` on the
       scheduler's own execution history showed `NOT_FOUND` (then `UNAVAILABLE` after retry) on both 2026-07-13 and
       2026-07-14's 03:00Z fires. Also read `ml_service/inference/cli/main.py` — it DOES have a `--run-tag` argparse
       flag already (help text: "GCS output prefix tag (default: batch; use t1-recon for T+1 reconciliation)") but a
       workspace grep (`rg -n "run_tag" ml_service/inference/`) found ZERO consumers of it anywhere outside the parser
       itself — the flag is parsed into the namespace and never read again. No `_SUCCESS`-marker writer exists anywhere
       in `ml_service/inference/` either (grep-clean).
     - **strategy-service t1-recon** (04:00 UTC, feeds `t1-recon/strategy/{date}/_SUCCESS`): the Cloud Run Job DOES
       exist (`uts-prod-strategy-service-t1-recon`, provisioned 2026-05-23 per a documented F-41-followup fix in
       `deployment-service/terraform/gcp/audit03_cron_provisioning.tf`), and its scheduler is `ENABLED` (`0 4 * * *`),
       but `gcloud run jobs executions list` showed 10/10 consecutive daily executions (2026-07-05 through 2026-07-14)
       `NonZeroExitCode`, and reading the actual execution logs (`gcloud logging read` on the exact execution name)
       showed ZERO application-level output — only `WARNING Application exec likely failed` /
       `ERROR terminated: Application failed to start: The container may have exited abnormally`, an OCI-level failure
       before any Python code runs. Root-caused via `gcloud run jobs executions describe` (showed the exact args:
       `["--operation", "backtest", "--mode", "batch"]`, no `command` override) + `docker pull` +
       `docker inspect --format='{{json .Config.Entrypoint}} CMD={{json .Config.Cmd}}'` on the exact deployed image
       digest — `Entrypoint=null`, `Cmd=["uvicorn","strategy_service.api.main:app",...]` (confirmed against
       `strategy-service/Dockerfile`: `ENTRYPOINT [] + CMD=[uvicorn...]`, deliberate — it's primarily a live API
       service). Reproduced locally (`docker run <image> --operation backtest --mode batch` →
       `exec: "--operation": executable file not found in $PATH`) — proves the container was trying to exec the literal
       string `--operation` as a binary, exactly matching the OCI-level crash signature in the logs.
  7. **Fixed the strategy exec bug in scope** (small, safe, well-understood — a broken container-invocation config, not
     new pipeline feature work): read the `container-job/gcp` Terraform module's `variables.tf` — it already supports an
     optional `command` var that was simply never set for this job. Added
     `command = ["python", "-m", "strategy_service"]` to `audit03_cron_provisioning.tf`'s `strategy_t1_recon_job` module
     (confirmed `python -m strategy_service --operation backtest --mode batch` is a real, tested CLI invocation —
     `strategy_service/__main__.py` → `cli/service_entry.py`; covered by
     `tests/unit/cli/test_cli_flag_combinations.py`). Local `terraform init` on this shared backend hit "Backend
     configuration changed" (a mismatch against the live remote state other agents are concurrently touching this
     session) — did NOT force `-reconfigure`/`-migrate-state` against a shared state I don't own the context for;
     instead applied the fix directly to the LIVE Cloud Run Job via
     `gcloud run jobs update uts-prod-strategy-service-t1-recon --command="python,-m,strategy_service" --args="--operation,backtest,--mode,batch"`
     (mirrors this plan's own established pattern from earlier today — "terraform source edited first, applied via
     gcloud directly, no blind apply"). Verified with a real triggered execution
     (`gcloud run jobs execute uts-prod-strategy-service-t1-recon --wait`, execution
     `uts-prod-strategy-service-t1-recon-nfkbj`): this time the container genuinely started and ran for ~2 minutes with
     full application bootstrap logs (bucket connectivity, kill-switch subscribers, etc. — a complete change in failure
     signature from the instant prior OCI crash), then failed one layer deeper:
     `ValueError: batch operation requires --date or both --start-date and --end-date` from
     `strategy_service/cli/service_entry.py::_resolve_date_args()` — this producer has no self-default-to-yesterday
     fallback (unlike ml-service/mdps, confirmed by reading the same function), and the Terraform args pass no date at
     all.
  8. **Confirmed the deeper structural gap that makes further per-bug chasing here unproductive**: workspace-wide grep
     (`rg -n "run_tag" strategy-service`) found ZERO matches anywhere in strategy-service — there is no `--run-tag`
     concept in this service's CLI at all, and (same as ml-service) no `_SUCCESS`-marker writer exists anywhere in the
     repo. Even a fully-running, correctly-dated invocation of this job would write to the default `batch/`
     thermal-backtest namespace (per `t1-batch-dag.md`'s own "Batch vs Thermal" table), which the DAG doc states
     explicitly is NEVER read by the reconciliation orchestrator. Also checked (for completeness, live):
     `gcloud scheduler jobs describe` on all 7 feature-family t1-recon schedulers this chain depends on upstream of ml
     (calendar/delta-one/volatility/cross-instrument/multi-timeframe/commodity/sports) — all 7 are `PAUSED`; and
     `features-onchain` isn't even a key in `t1_batch_scheduler.tf`'s `t1_batch_services_all` map despite being listed
     as a producer in the codex DAG doc.
  9. **Conclusion, matching the task's own scope guidance**: this is not a "trigger a missing scheduled job" or "fix a
     broken config" situation at the chain level (even though I found and fixed exactly one of each, in scope) — it is
     an entire designed-but-never-fully-built upstream pipeline spanning execution-service, ml-service,
     strategy-service, and features-service. Implementing it for real requires: provisioning 2 missing Cloud Run Jobs
     (execution config-snapshot, ml-inference) via the same container-job Terraform pattern already used for
     strategy/mdps; implementing an actual run-tag-aware GCS writer + `_SUCCESS`-marker emission in at least ml-service
     and strategy-service (not just parsing a flag); adding a self-default date fallback to strategy-service's batch
     CLI; and un-pausing + validating 7 feature-family schedulers (plus registering the missing onchain one). That is
     genuine multi-repo feature work, correctly out of scope for a bucket-consolidation plan — left here as a
     precisely-characterized, well-scoped open item rather than attempted.
  10. **Repos touched**: `batch-live-reconciliation-service@be056b1` (quickmerge, QG green).
      `deployment-service@ea42a699` (quickmerge, QG green — `audit03_cron_provisioning.tf`'s `command` addition +
      documentation comment, landed AFTER the live Cloud Run Job was already fixed directly via `gcloud run jobs update`
      per point 7 above, so this commit codifies the live state rather than changing it — the next `terraform apply` on
      this state will see it as a no-op diff). Cloud Build `ab591245-708a-4c84-a080-7f4d3a9d6a15` (SUCCESS, real build,
      not just "should build"). No data touched, no destructive action taken, nothing bucket-related deleted or created
      this pass. Issue doc `recon_bucket_missing_nightly_recon_failing_2026_07_13.md` updated in the same commit as this
      plan file with the same findings.

- **2026-07-14/15, autonomous dispatch — Morpho lending-indices relaunch, item 13, first live verification of the
  `mtds_backfill_vm_startup_oom_rc137_2026_07_14` fix chain against a real backfill VM.** Interim status (backfill still
  running at time of this entry — see `mtds_backfill_vm_startup_oom_rc137_2026_07_14.md`'s own live-verify section for
  the full evidence chain; this entry is the plan-side pointer).

  1. **Pre-launch verification, by content not just SHA-math**: pulled the tail of the OOM issue doc + `git log` first
     (per dispatch instructions) and found the fix chain (catalog-reader scoping `d6846f1c`, single-pass membership-set
     build `0aa284e8`, `date_range` param on `ManifestFreshnessCache.__init__` `391f8196`, all 9 DeFi handlers wired
     `e3bbb2a3`) already marked DONE, plus discovered a 5th, previously-undocumented fix already on `live-defi-rollout`:
     `unified-trading-library@a5b07ff7` ("true row-group predicate pushdown for `ManifestFreshnessCache` `date_range` —
     14.86GB → 742MB peak", landed 2026-07-14T23:18:07Z+01:00 by a concurrent slot). Downloaded + unpacked the actual
     `mtds-code.tar.gz` / `unified-trading-library-code.tar.gz` from
     `gs://deployment-scripts-central-element-323112/code/` and grepped the extracted `.py` files directly (not just the
     `.manifest.json` `commit_sha`) — confirmed `_date_range_filters()` + `filters=` pushdown present in
     `manifest_freshness.py` and all 9 handlers (incl. `lending_indices_handler.py:341`) pass
     `date_range=(target_day, target_day)`. All 4 tarball manifests (`mtds-code`, `unified-api-contracts-code`,
     `unified-trading-library-code`, `deployment-service-code`) matched local `HEAD` exactly (built ~4min before launch
     by the same concurrent session that shipped `a5b07ff7`) — no rebuild needed.
  2. **Launch**:
     `bash deployment-service/scripts/vm/launch-mtds-lending-indices-backfill-vm.sh --lending-protocols morpho 2026-03-27 2026-07-12`
     (exact command from item 13, verified against the launcher's current `--lending- protocols`/positional-date-args
     CLI shape first). VM `mtds-lending-indices-20260715-002613` created 23:26:33Z, `RUNNING` at 23:26:43Z (~32s, well
     under the 60s no-fire-and-forget bar), SPOT/preemptible per the backfill-SPOT- default rule. The launcher's own
     built-in `lc_verify_tarball_freshness` gate independently confirmed all 4 tarballs current at launch time.
  3. **STARTED + past the old crash window**: `run.log` shows `DEPLOYMENT_STARTED` 23:29:00.400Z,
     `Lending indices handler initialized` 23:29:00.959Z, two healthy `RESOURCE_SAMPLE`s (rss=693MiB/mem=10.7% at
     23:29:01Z, rss=896MiB/mem=11.8% at 23:29:31Z) — the OLD code crashed within ~20-90s of this exact point every
     single time this issue doc recorded; this run sailed past it with continuous real per-pool Morpho GraphQL fetches,
     zero crash signature.
  4. **Genuine progress, ground-truth confirmed** (not just log claims): days 2026-03-27 (554 records), 2026-03-28 (479
     records), 2026-03-29 (340 records) each completed cleanly per `run.log`'s `Lending indices collection complete`
     lines; day 4 (2026-03-30) in progress as of 23:37Z. Independently verified day 1's real GCS object exists at
     `gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2026-03-27/pipeline_mode=batch_onchain_subgraph/asset_group=defi/venue=MORPHO/chain=ETHEREUM/instrument_type=lending/data_type=lending_indices/morpho_ETHEREUM_20260714_232900.parquet`
     — a real parquet landed in the canonical shared bucket, not just a log line. Pace ~2min/day ⇒ 108 days ≈ 3.5-4hr
     total; not yet complete as of this entry.
  5. **Bottom line so far**: the full fix chain (items 1-4 from the dispatch brief) plus the bonus row-group-pushdown
     fix appears to genuinely resolve the OOM for this handler on a real backfill VM — first real-world confirmation for
     `lending_indices_handler.py` specifically (every prior verification in the OOM issue doc was either synthetic/
     local or a different handler/the separate consolidator Cloud Run job). **Will update this entry again on completion
     or crash** — do not treat item 13 as closed from this entry alone.

- **2026-07-15, `instruments-store-sports` Migrate-phase dispatch — declined, collision with item G / HELD sports plan;
  no objects copied, no code shipped.** A prior-touch diff phase (already recorded, structured JSON echoed back in this
  session's dispatch) found `uniqueObjectCount=400`, `safeToDeleteWithoutMigration=false`, and two genuinely-unique
  bare-only prefixes with no `-prd` counterpart: (1) `day=2026-03-21/venue=BETFAIR/` (2 parquet objects, single
  generation each) and (2) `sports_reference_v1_archive/by_date/` (~398 day-partitions, 2018-01-02 through 2026-04-20,
  uncounted at object level — a recursive listing of just this subtree timed out at 90s, single-walk discipline
  respected, not re-attempted). The bulk of the bucket (`instrument_availability/`) is already covered by
  `sports_manifest_canonicalisation_2026_06_01`'s manifest-cell-level diff (far more rigorous than a raw object count)
  and was correctly NOT re-diffed.
  - **Why this touch did NOT execute the migrate: read this row's own item G above plus the full sister plan tail
    (`sports_manifest_canonicalisation_2026_06_01.md`, 4,145 lines) before acting.** That plan is
    `locked_by: live-defi-rollout`, actively dispatched (`assigned_vm: planning`), and its own P0 todo carries an
    explicit do-not-redispatch note; its last ~4 Progress Log entries (2026-07-14) record ~30 redispatch-churn touches,
    a STOP-gated production maintenance-window blocker (`BLK-d9137d48`), and an unapplied `prereqs.conditions` parking
    request. Item G directly above (line ~533) already states, current and unedited by me: **"Still HELD — do not
    purge/delete either bucket."** Migrating even the two prefixes outside CF-8's stated scope still means writing new
    objects + manifest rows into a bucket pair under an active, contested, churn-prone plan, mid a delicate
    operator-gated backfill-redesign wait — a unilateral copy by an unrelated dispatch is exactly the "fits another plan
    → annotate, don't fix" collision-risk case per workspace findings-triage rules, not a "small + clear ≤30 min" case.
    Terraform/scheduler/FUSE-mount/VM-launcher/~30-script live-reference surface on this bucket (found by the diff-phase
    touch) independently means a real cutover — not just a data copy — would be needed before deletion regardless,
    reinforcing that this is squarely the sister plan's territory, not a bolt-on from this dispatch.
  - **Action taken instead**: zero objects copied, zero manifest rows written, zero code shipped, zero terraform/deploy
    touched. This Progress Log entry (a `docs(plans):` edit) is the annotation — flagging for the sister plan's next
    real touch (once CF-8 is unblocked) that the two above prefixes are genuine, uncharacterized gaps outside its
    `instrument_availability/`-scoped cell-diff and should be swept before any eventual E8 bucket-deletion ask. Did not
    hand-edit the 4,145-line sister plan directly given its active-churn/lock state — a bigger edit there risks
    colliding with whichever slot picks up its next dispatch; this pointer is the lower-risk annotation surface.
  - **Verdict for the orchestrating migrate-phase task**: `instruments-store-sports` is NOT ready for
    delete/migrate-then-delete this round — reported back structurally as blocked-collides-with-sports-plan, matching
    the diff-phase touch's own recommendation (trust-and-verify confirmed, not re-derived). No regression introduced;
    bucket estate count and item G's status are unchanged by this touch.

- **2026-07-15, `market-data-tick-sports` Migrate-phase dispatch — data-side confirmed clean, but delete deferred,
  collision with item G / HELD sports plan; zero objects copied, zero manifest rows written, zero code shipped.** A
  prior-touch diff phase (already recorded, structured JSON echoed back in this session's dispatch) re-ran the manifest
  cell-diff (legacy vs. canonical `-prd-`, `capture_status=captured`) and found `uniqueObjectCount=0`,
  `safeToDeleteWithoutMigration=true`: legacy-only=140 cells, all confirmed (via ~18 targeted non-recursive prefix
  listings spread across the date range, single-walk discipline respected) to be `ODDS_API`/`ODDS`
  instrument_count=0/schema_version=4 phantom-capture rows with no backing GCS object in either bucket — same
  already-accepted class as item G's own note ("MTDS surface 140 legacy-only cells, all verified phantom-capture").
  Cloud Monitoring corroborates: legacy bucket live-object count static at 406,581 (8.08GB, unchanged 7d = frozen);
  canonical `-prd-` bucket already strictly ahead at 487,864 live objects. Re-confirmed light-touch this pass (no
  re-derivation): both buckets (`market-data-tick-sports-central-element-323112`,
  `market-data-tick-sports-prd-central-element-323112`) still exist and are unchanged via
  `gcloud storage buckets describe`; re-grepped `sports_manifest_canonicalisation_2026_06_01.md`'s latest entries — CF-8
  is still RED on the MDPS (`market-data-tick-sports-prd`) surface as of its most recent Progress Log entries (85.3%
  `available_at` non-null, unchanged, captured-row-specific gap, parking-fix not yet applied) — i.e. this bucket pair's
  E1/E8 ownership by the sister plan has NOT resolved since item G was last written.
  - **Why this touch did NOT proceed to delete despite `safeToDeleteWithoutMigration=true`**:
    `safeToDeleteWithoutMigration` only answers the data-loss question (is there unique data that would need copying
    first) — it does NOT override item G's explicit, current, unedited-by-me directive at line ~533: **"Still HELD — do
    not purge/delete either bucket"** (`market-data-tick-sports`/`instruments-store-sports`, jointly owned by
    `sports_manifest_canonicalisation_2026_06_01` E1/E8, gated on CF-8's captured-row `available_at` backfill which per
    that plan's own 2026-07-14 entries needs a scheduled maintenance window + service_name-aware write redesign before
    another live attempt). Also unresolved and un-actioned this touch, matching the diff-phase report: 3 live
    Terraform/IAM references (`google_storage_bucket.market_data_sports` resource block + `_imports_reconcile.tf` import
    block + `instrument_catalogue_scheduler.tf` for_each IAM grant) that would need coordinated `terraform state rm` +
    apply before any physical delete — deliberately not touched, since there is no delete to precede. Per workspace
    findings-triage ("fits another plan → annotate, don't fix" — collision risk), and matching the identical precedent
    set immediately above for `instruments-store-sports` on this same date: did not hand-edit the 4,145-line sister plan
    directly (active-churn, `locked_by: live-defi-rollout`); this Progress Log entry is the lower-risk annotation
    surface, flagging for the sister plan's next real touch (once CF-8 is unblocked) that the MTDS-side data diff is now
    independently reconfirmed clean and the pair is delete-ready from a pure-data standpoint the moment E1/E8's CF-8
    gate clears.
  - **Verdict for the orchestrating migrate-phase task**: migration step is genuinely a no-op (0 unique objects) —
    confirmed, not re-derived from scratch. `readyForDelete=false` for the overall bucket, NOT because of any data risk
    but because of the item-G HELD/collision status; the delete phase must wait for the sister plan's E1/E8 gate (CF-8)
    to clear on BOTH halves of the pair before this bucket can move. No regression introduced; bucket estate count and
    item G's status are unchanged by this touch.

- **2026-07-15, `market-data-tick-sports` Verify+Delete-phase dispatch — declined per the migrate-phase's own
  `readyForDelete=false` verdict, collision with item G / HELD sports plan unchanged; zero objects deleted, zero
  terraform touched, zero config touched, zero code shipped.** Dispatch instructions for this touch were explicit: "Only
  proceed if readyForDelete is true — if not, STOP and report why instead of forcing it." The immediately preceding
  migrate-phase entry (above, same date) already set `readyForDelete=false` for this exact bucket, for a reason that is
  a plan-collision/HELD-status gate, not a data-safety gate that could have changed since. Re-checked before stopping
  (light-touch, no full-corpus walk, no new manifest/data-status query — the migrate-phase already ran the
  honest-coverage/data-diff check this session and nothing about the data state can have changed in the interim): (1)
  re-grepped item G at line ~533 of THIS plan — still reads **"Still HELD — do not purge/delete either bucket"**,
  unedited since the migrate-phase touch; (2) re-grepped `sports_manifest_canonicalisation_2026_06_01.md`'s latest
  Progress Log entries (lines ~4035-4130) — CF-8 still `RED` on the MDPS (`market-data-tick-sports-prd`) surface,
  `available_at` non-null still 85.3% (1,670,401/1,958,499), unchanged from the migrate-phase's own citation, parking
  fix still not applied, sister plan still `locked_by: live-defi-rollout` (active-churn — did not hand-edit it). No
  operator or sister-plan update has landed between the migrate-phase touch and this touch that would flip the gate.
  **Verify-phase checks explicitly NOT performed given the STOP** (would be wasted/premature work ahead of an unclear
  delete): did not re-query deployment-api's data_status/honest-coverage endpoints (the migrate-phase's Cloud
  Monitoring + manifest-based diff already stands, re-deriving it adds no new information while the gate itself is
  unchanged); did not touch `deployment-service/terraform/gcp/*.tf` (the 3 live Terraform/IAM references the diff-phase
  found — `google_storage_bucket.market_data_sports`, `_imports_reconcile.tf` import block,
  `instrument_catalogue_scheduler.tf` for_each IAM grant — remain undeclared-for-removal, since removing them ahead of
  an actual delete would desync terraform state from live infra for no reason); did not touch
  `deployment-service/configs/bucket_config.yaml` or any scheduler/cron/VM-launcher config; did not run
  `gcloud storage rm`/`gcloud storage buckets delete` against either bucket. **Nothing was deleted; both buckets
  (`market-data-tick-sports-central-element-323112`, `market-data-tick-sports-prd-central-element-323112`) remain
  exactly as they were.** This Progress Log entry is the only artifact of this touch (docs-only, pushed directly per the
  PM cross-repo `docs(plans):` carve-out) — matching the same low-risk annotation pattern used by the migrate-phase
  entry and by the sibling `instruments-store-sports` touches on this same date, per workspace findings-triage ("fits
  another plan → annotate, don't fix" is the collision-risk case, and forcing a delete against an explicit STOP
  instruction plus an explicit HELD directive would be the opposite of that). **Verdict for the orchestrating
  verify+delete-phase task**: correctly declined — `readyForDelete` is still `false` for `market-data-tick-sports`, for
  the identical reason cited by the migrate-phase (item G HELD, gated on the sister plan's CF-8 backfill needing a
  scheduled maintenance window + service_name-aware write redesign), and nothing in this touch's re-check changed that.
  Re-check this bucket once `sports_manifest_canonicalisation_2026_06_01.md`'s E1/E8 CF-8 gate clears on BOTH halves of
  the sports pair (`market-data-tick-sports` AND `instruments-store-sports`).

- **2026-07-15, `features-calendar` Verify+Delete-phase dispatch — COMPLETE, flat bucket physically deleted + terraform
  state/config cleaned up.** `deployment-service@82eadd5`. Migrate-phase result for this bucket (`readyForDelete=true`,
  0 live+noncurrent objects, 0 soft-deleted objects) was re-verified fresh before acting: (1)
  `gcloud storage buckets describe gs://features-calendar-central-element-323112` resolved (bucket still existed); (2)
  `gcloud storage ls -a -r ".../**"` → `ERROR: ... matched no objects` (0 objects, includes-all-versions); (3)
  `gcloud storage ls --soft-deleted ...` → empty, exit 0. Canonical siblings
  `features-calendar-{prd,test}-central-element-323112` both `describe` OK; spot-checked `prd` has live data
  (`gcloud storage du --summarize` → 333 bytes, `_index/` present — not a full-corpus walk, single-walk discipline
  honored) confirming the canonical bucket is the one actually receiving writes, unaffected by the bare bucket's
  removal. **Terraform**: pulled the real prod state directly from GCS
  (`gs://uts-terraform-state-central-element-323112/terraform/state/prod/default.tfstate`) and confirmed
  `google_storage_bucket.features_calendar` WAS live-managed (Wave-0's 2026-07-12 apply resurrection, exactly as the
  migrate-phase note predicted) — reinit'd the working dir against the prod backend prefix
  (`terraform init -reconfigure -backend-config=prefix=terraform/state/prod`, no state migration, matched the already-
  cached prod config), ran `terraform state rm google_storage_bucket.features_calendar` BEFORE the physical delete
  (matches the `instruments_defi`/`instruments_tradfi`/`market_data_cefi`/`market_data_tradfi` purge-armed-twin
  precedent, ds@1dd2159/ds@39fa8c3), then deleted the bucket (`gcloud storage rm --recursive --continue-on-error` → 0
  objects matched as expected, then `gcloud storage buckets delete --quiet` → success). **Evidence bucket is gone**:
  `gcloud storage buckets describe gs://features-calendar-central-element-323112` now returns `404` / "not found".
  Removed the now-dangling `main.tf` resource block (398-414, replaced with a REMOVED banner citing the precedent) and
  `outputs.tf`'s `features_calendar_bucket` output (grep-confirmed zero consumers). Reverted an incidental
  `.terraform.lock.hcl` provider-version bump the reinit produced (unrelated to this task, not shipped). **Config/
  scheduler check**: `bucket_config.yaml` line 35 is a service-name list entry, not a bucket reference — no bare-name
  hit; `cloud-providers.yaml` already resolves `features-calendar` to the canonical env-tiered form (both GCP + AWS
  blocks) — no bare-name hit; `manifest_consolidator_scheduler.tf`'s `features-calendar` map entry + the live deployed
  Cloud Run Job (`uts-prod-manifest-consolidator-features-calendar`, confirmed via `gcloud run jobs describe`) already
  target `features-calendar-prd-central-element-323112` — no fix needed. Found + fixed one stale doc-comment in
  `deployment-service/scripts/vm/run-features-pipeline-backfill.sh` (Phase 4f) that hardcoded the now-deleted bare path
  in a comment — updated to the canonical env-tiered path + a decommission note (comment-only, no functional change, no
  live caller). Shipped via
  `quickmerge.sh --agent --files 'terraform/gcp/main.tf terraform/gcp/outputs.tf scripts/vm/run-features-pipeline-backfill.sh'`
  (scoped by name — a sibling agent's concurrent, unrelated `lifecycle_catalogue_scheduler.tf` WIP was live in the same
  working tree, mtime essentially real-time, and was left untouched); `quality-gates.sh --no-fix` green pre-commit;
  landed + verified ancestor-or-equal of `origin/live-defi-rollout` (`82eadd50e977b300828842aa3fb5989721148b1f`).
  **Deferred, NOT actioned this touch** (per findings-triage — out of this bucket's terraform-path scope / dormant /
  cross-repo-broad, flagged for a future small follow-up rather than folded in here): (1)
  `unified-trading-library/unified_trading_library/cloud_interface/constants.py`'s `get_features_calendar_bucket()`
  (deep/legacy `cloud_interface.constants` module, distinct from the already-correct public
  `unified_trading_library.get_features_calendar_bucket()` re-exported from `core/cloud_constants.py`, which already
  delegates to `_resolve_bucket_name`) still hardcodes the old flat/no-env-suffix model via
  `get_bucket_name ("features_calendar")` — re-grepped this touch: genuinely zero live callers workspace-wide (only its
  own tests), confirmed dead code, but fixing it cleanly means touching the same module's shared Group-A/B
  `BUCKET_NAMES` dict + docstring that also documents `instruments`/`market_data` (buckets outside this touch's scope) —
  a broader legacy- cleanup pass, not a single-bucket delete. (2)
  `deployment-service/terraform/services/features-delta-one-service/gcp/main.tf:244`'s `gcs_volumes` wiring still
  references the bare `features-calendar-${var.project_id}` bucket — re-confirmed dormant this touch
  (`gcloud run jobs list` shows no `*-features-delta-one-service-t1-recon` or `*-features-calendar-service-t1-recon`
  Cloud Run Job deployed, only the `manifest-consolidator` ones), so no live break; repoint before that module is ever
  deployed. (3) `uts-prod-features-calendar-t1-schedule` Cloud Scheduler job re-confirmed still `PAUSED` (same pattern
  as other recon-bucket findings this plan already tracks) — unrelated to this bucket's delete, needs its own triage.
  **Verdict for the orchestrating verify+delete-phase task**: DONE — bare bucket physically deleted, terraform state +
  config reconciled so a future `terraform apply` cannot resurrect it, no code/data regressions, estate count -1.

- **2026-07-15, Final audit — flat `features-*`/`instruments-store-*`/`market-data-tick-*` bucket sweep, consolidated
  across-bucket result (5-bucket workflow run).** This entry rolls up the per-bucket Verify+Delete-phase results for the
  5 buckets dispatched this sweep and re-confirms nothing else in the estate was missed. **Net estate change this sweep:
  -1 bucket** (`features-calendar` only; the other 4 are still-open follow-ups, none regressed).

  **(1) Migrated + deleted — `features-calendar` (estate count -1, DONE)**: bare
  `features-calendar-central-element-323112` confirmed 0 live/noncurrent/soft-deleted objects, physically deleted
  (`gcloud storage buckets describe` now 404), `terraform state rm google_storage_bucket.features_calendar` run before
  the delete, `main.tf`/`outputs.tf` resource+output removed with a REMOVED-banner, one stale doc-comment path fixed in
  `run-features-pipeline-backfill.sh`. Canonical siblings (`features-calendar-{prd,test}`) confirmed live and receiving
  writes. Shipped `deployment-service@82eadd50e977b300828842aa3fb5989721148b1f`. 3 small out-of-scope dead-code/config
  items deferred (dead `cloud_interface.constants.get_features_calendar_bucket()`, a dormant `gcs_volumes` bare-bucket
  ref in the never-deployed `features-delta-one-service` terraform module, and a pre-existing `PAUSED`
  `uts-prod-features-calendar-t1-schedule` scheduler — all noted in the entry above, none live/blocking). Full
  narrative: the 2026-07-15 `features-calendar` Progress Log entry immediately above this one.

  **(2) Migrate-phase code not yet shipped, live refs not yet cut over — `features-sports` (NOT deleted, blocked)**:
  bare `features-sports-central-element-323112` is genuinely legacy-flat and in-scope (distinct from the deliberately-
  held Group-B `features-*` buckets below), but this run's Verify+Delete touch correctly declined to force it —
  `readyForDelete=false` on re-verification. Two concrete blockers, both requiring a prior touch: (a) the migrate-phase
  one-off script
  `features-service/features_service/sports/scripts/migrate_features_sports_flat_bucket_gap_2026_07_15.py` is still
  untracked (`??`) — never ran through `quality-gates.sh` or `quickmerge`; (b) three live-reference surfaces still point
  at the bare bucket and need repointing before any delete: `deployment-service/terraform/gcp/main.tf:474`
  `google_storage_bucket.features_sports` (+ its `_imports_reconcile.tf:51-52` import block), the live
  features-sports-service Cloud Run job's GCS-FUSE mount, and two VM-fanout backfill launchers
  (`deployment-service/scripts/vm/launch-features-sports-parallel-backfill-vm.sh`,
  `features-service/scripts/sports/launch_parallel_backfill.sh`) whose `GCS_BUCKET` default still points at the bare
  name. Nothing modified/committed/deleted this touch — bare bucket fully intact. Follow-up: ship the migrate script
  first, then a separate touch for the terraform/launcher/FUSE-mount cutover, then re-attempt Verify+Delete.

  **(3) Blocked on an operator ruling — `features-onchain` (NOT deleted, NOT a migration gap)**: bare
  `features-onchain-central-element-323112` holds exactly 16 objects (70,768,303 bytes), all under one
  `netflow_xsec_research/` prefix — 7 parquet research datasets, a **live** `_dune_sleeve_ledger.csv`/
  `_dune_sleeve_state.json` personal trading-sleeve state, 4 PNGs, and a `STRATEGY_STATE.md`. There is zero
  `asset_group`/`pipeline_mode`/by-date hive partitioning to classify these into the canonical
  `features-onchain-{cefi,defi}` siblings, and
  `e2e-testing/scripts/onchain/{README.md, gcs_sync.py, _dune_sleeve_deploy.py}` hardcode this exact bare bucket+prefix
  as their documented "Data SSOT" with edits as recent as 2026-07-05 (a live consumer, not dead code). Deleting this
  bucket now would destroy a live personal trading-sleeve's only backing store with no replacement. Filed + confirmed
  still open: `plans/active/issues/features_onchain_bare_bucket_not_asset_group_migratable_2026_07_15.md`, which lays
  out 3 operator options (A: relocate `netflow_xsec_research/` to a dedicated research bucket + repoint e2e-testing then
  delete the bare bucket [prior agent's recommendation]; B: exclude this bucket from the features-* migration entirely;
  C: ship only the 2 non-blocking dead-code fixes now, defer the bucket decision). No operator ruling has landed yet —
  **this bucket needs an explicit operator decision before further dispatch**, re-running the same task will just
  re-produce the same STOP.

  **(4) Deliberately HELD, collision with a sister plan — `market-data-tick-sports` + `instruments-store-sports` (NOT
  deleted, NOT a gap in this plan)**: both buckets are item G of this plan but are actively owned/dispatched by
  `sports_manifest_canonicalisation_2026_06_01.md` (`locked_by: live-defi-rollout`, `assigned_vm: planning`), gated on
  CF-8 (`available_at` backfill still RED on the MDPS surface, 85.3% non-null as of the sister plan's latest entries)
  needing a scheduled maintenance window + a `service_name`-aware manifest-consolidator write redesign before any
  further backfill attempt — an architectural gap, not a quick fix. `instruments-store-sports` additionally has 400
  confirmed-unmigrated unique objects (two genuine bare-only prefixes: `day=2026-03-21/venue=BETFAIR/` and
  `sports_reference_v1_archive/by_date/` ~398 day-partitions) plus a live
  terraform/scheduler/FUSE-mount/VM-launcher/~30-script reference surface. Re-verified this run: item G's "Still HELD —
  do not purge/delete either bucket" directive (line ~533) is unchanged; no GCS/terraform/config action taken on either
  bucket. **Re-check only after `sports_manifest_canonicalisation_2026_06_01.md`'s E1/E8 CF-8 gate clears on BOTH halves
  of the pair.**

  **Group-B exclusion, explicitly re-confirmed out of scope (NOT a gap, NOT touched this sweep)**: per the
  operator-approved 2026-05-19 Phase D rollback (`plans/active/bucket_env_split_rollout_2026_06.md` Phase 1, still
  pending re-provisioning), the following remain **deliberately flat by design** and were correctly NOT migrated,
  env-split, or deleted by any of the 5 dispatched touches this sweep:
  `features-delta-one-{cefi,tradfi,defi,pred,sports}`, `features-volatility-{cefi,tradfi,defi,pred,sports}`,
  `features-onchain-cefi-{pid}` / `features-onchain-defi-{pid}` (the per-asset-group split siblings — distinct from the
  bare shared `features-onchain-{pid}` bucket in item (3) above, which IS in scope),
  `features-xinstrument-{cefi,tradfi,defi,pred,sports}`, `features-mtf-{cefi,tradfi,defi}`, `ml-artifacts-{pid}`,
  `ml-training-artifacts-{pid}`, `strategy-store-{pid}`, `execution-store-{cefi,tradfi,defi,sports}`. Re-grepped
  `deployment-service/configs/cloud-providers.yaml`'s comment block this touch (lines ~38-72) — confirms the rollback
  framing is unchanged and these are documented as intentionally flat, not accidental legacy.

  **Workspace-wide spot-check (this touch, no fresh full-corpus walk — single-walk discipline honored)**: confirmed
  `cloud-providers.yaml` already resolves all 5 assigned bucket keys (`features-calendar`, `features-sports`,
  `features-onchain` [per-AG], `market-data-tick-sports`/`market_data_cefi` family, `instruments-store-sports`) to
  canonical env-tiered names in both GCP and AWS blocks — no code-level stray references found beyond the
  already-itemized deferred items above. Consistent with the workspace-wide grep already run earlier this session (zero
  live producer/consumer code hardcoding any of the 5 bare bucket names as string literals).

  **Unrelated but found + fixed in the same session — MorphoAdapter chain-awareness fix**: `market-tick-data-service`
  commit `2b73729e` ("fix(defi): make MorphoAdapter chain-aware for market discovery + subgraph resolution") shipped
  during this session. It is **unrelated to this bucket sweep** — filed here only because it was discovered+fixed in the
  same working session and the operator asked it be noted. Natural follow-up once this bucket sweep lands: a Base-chain
  Morpho backfill relaunch (the chain-awareness fix means prior Base-chain Morpho captures may have been silently
  mis-resolved to the wrong chain's subgraph; a targeted backfill VM launch would confirm/backfill any gap).

  **Overall verdict**: 1 of 5 assigned buckets fully migrated+deleted (`features-calendar`); 2 blocked on prior-touch
  code-ship + live-reference cutover (`features-sports`) or an explicit operator ruling (`features-onchain`); 2
  correctly left untouched as a sister-plan collision (`market-data-tick-sports` + `instruments-store-sports`, item G,
  re-verified HELD); Group-B's 10 buckets/families explicitly reconfirmed out of scope; no regressions, no data loss, no
  unauthorized deletes. Estate count this sweep: **-1** (241 baseline tracking unaffected beyond the single
  `features-calendar` delete already reflected in the entry above).

- **2026-07-15, operator ruling executed (Ship phase) — `features-sports` migrate-script shipped + 2 ephemeral objects
  confirmed disposable, blocker (a) cleared**. Operator ruled 2026-07-15: finish the `features-sports` bare-bucket
  retirement now. This touch dispatched only the "Ship phase" scope from item (2)'s two blockers above (blocker (b) —
  the 3 live-reference-surface cutover + eventual delete — is a separate follow-up touch, not done here, to avoid
  collision with any parallel dispatch on the same plan). **(a) migrate-script shipped**: re-verified
  `features-service/features_service/sports/scripts/ migrate_features_sports_flat_bucket_gap_2026_07_15.py` was still
  untracked (`git status` — confirmed `??`), then re-verified the destructive step it already performed (per the prior
  workflow's report) is still correctly reflected rather than re-running it: `gsutil stat` on
  `gs://features-sports-prd-central-element-323112/sports_features/by_date/day=2020-01-01/feature_group=sfi_progressive/sfi_progressive.parquet`
  confirms the object is present (created 2026-07-15T10:05:37Z, 25,989 bytes); downloaded + read the consolidated
  `gs://features-sports-prd-central-element-323112/_index/availability_index.parquet` (161,226 rows) and confirmed
  exactly 1 matching row —
  `date=2020-01-01, feature_group=sfi_progressive, feature_family=sports, data_type=SFI_PROGRESSIVE_FEATURES, row_count=43, capture_status=captured`
  — i.e. the manifest consolidator has already merged the migration script's per-VM shard into the canonical index (the
  source flat-bucket object is correctly still present too — `gcs_copy_object` doesn't delete the source). No
  destructive step was re-run. Ran `quality-gates.sh --no-fix` on the features-service tree (sentinel
  `.qg_last_passed_sha` written == HEAD, confirming a genuine pass; pre-existing unrelated warnings surfaced in
  sibling-repo scans — `e2e-testing/scripts/sports/sharpapi_live_feed.py` ruff/complexity + a `market-tick-data-service`
  adapter contract-call baseline regression on `solana_defi_drift.py` — both out of this plan's scope, not touched).
  Shipped solo via `quickmerge --agent --files` (only this one file staged):
  `features-service@5e8b33337192a72b0cb20e6a12636e0f218c88be` ("feat(sports): ship features-sports flat-bucket gap
  migration script"), landed on `live-defi-rollout`, working tree clean after. **(2 ephemeral objects) confirmed
  genuinely disposable**: the flat bucket's other 2 live objects —
  `_vm_staging/fss_backfill/fss_backfill_codebase.tar.gz` + `_vm_staging/fss_backfill/vm_fss_features.sh` — traced to
  `features-service/scripts/sports/launch_parallel_backfill.sh` (mirrored by
  `deployment-service/scripts/vm/launch-features-sports-parallel-backfill-vm.sh`): both scripts `tar czf` a fresh local
  staging dir and re-upload to this exact `_vm_staging/fss_backfill/` prefix on every VM-fanout backfill launch — build
  scratch re-created from scratch each launch, no canonical counterpart by design, confirmed NOT migration-worthy. With
  the migrate-script now shipped + these 2 objects confirmed disposable, the flat bucket has reached zero-unique-content
  (its remaining 3 live objects are: the now-canonically-duplicated sfi_progressive parquet + the 2 confirmed-ephemeral
  VM-staging objects) — **but is NOT yet delete-eligible**: blocker (b) from the entry above (3 still-live reference
  surfaces — `deployment-service/terraform/gcp/main.tf:474` `google_storage_bucket.features_sports` + its
  `_imports_reconcile.tf:51-52` import block; the live features-sports-service Cloud Run job's GCS-FUSE mount; and the
  two VM-fanout launchers' `GCS_BUCKET` default) is unchanged and still requires a separate cutover touch before any
  Verify+Delete re-attempt. Next follow-up: repoint the 3 live-reference surfaces to the canonical `-prd-` bucket,
  re-verify `readyForDelete`, then delete.

- **2026-07-15, operator ruling executed (Execute phase) — `features-onchain` bare bucket relocated + deleted, item (3)
  CLOSED.** Operator ruled Option A on
  `plans/active/issues/features_onchain_bare_bucket_not_asset_group_migratable_2026_07_15.md`: relocate the bare
  `features-onchain-central-element-323112` bucket's only content (`netflow_xsec_research/`) to a new dedicated research
  bucket, repoint the live consumer, then delete. A prior session already provisioned
  `onchain-research-central-element-323112` (registered as kind `onchain-research` in
  `deployment-service/configs/bucket_config.yaml`'s `infrastructure_buckets.gcp` list, shipped
  `deployment-service@45c9924b`) and confirmed no live automated GCS writer races the bucket. This touch executed the
  copy/repoint/verify/delete: **(1) copy** — all 16 objects (STRATEGY_STATE.md, netflow_granular_cadence.png, 8 `data/`
  parquets, 2 `live/` files incl. the live `_dune_sleeve_ledger.csv`/`_dune_sleeve_state.json`, 4 `plots/` PNGs) copied
  via UTL `gcs_copy_object` (server-side rewrite, no subprocess `gsutil`/`gcloud`) — every object individually verified
  size+crc32c match post-copy (16/16 OK). **(2) verify** — `gcloud storage du -s` confirmed identical total corpus size
  both sides (70,768,303 bytes) before and after every subsequent step; the two live sleeve files were independently
  byte-diffed (not just crc32c) src-vs-dst twice (once immediately post-copy, once again as the final pre-delete gate) —
  both `_dune_sleeve_ledger.csv` and `_dune_sleeve_state.json` bit-for-bit identical at the new location both times.
  **(3) repoint** — grepped the whole workspace fresh (not trusting the prior session's list at face value): confirmed
  exactly 2 live-consumer hits, both in `e2e-testing/scripts/onchain/` (`gcs_sync.py`'s docstring + its `BUCKET`
  constant; `README.md`'s Data SSOT line) — `_dune_sleeve_deploy.py` re-confirmed zero `gs://`/`BUCKET`/bucket-name
  references (reads/writes only local ROOT-relative paths). Repointed both hits to
  `gs://onchain-research-central-element-323112/netflow_xsec_research` (kept the same `data/`+`live/`+`plots/`
  sub-layout under the new bucket root — smaller diff, no restructuring). Proved the repointed script actually works
  against the new bucket, not just a string-match: ran `gcs_sync.py pull` (pulled all 8 `data/` parquets, 66.6 MiB) then
  `gcs_sync.py push` (idempotent rsync — mtime-copy only, corpus byte-total unchanged post-push) live against
  `onchain-research-central-element-323112`. `quality-gates.sh --no-fix` green on e2e-testing (sentinel written ==
  HEAD); shipped solo via `quickmerge --agent --files 'scripts/onchain/README.md scripts/onchain/gcs_sync.py'` —
  `e2e-testing@a4f8bdc6` ("chore(onchain): repoint netflow research pipeline Data SSOT to dedicated onchain-research
  bucket"), landed on `live-defi-rollout`. Re-grepped post-ship: zero remaining code hits for the bare bucket name
  anywhere in the workspace (only historical/archived-plan mentions remain, not live code). The 3 env-file
  `FEATURES_ONCHAIN_BUCKET=` lines (`e2e-testing/configs/defi/local-{live,batch,paper}.env`) + `execution-service`'s
  `features_onchain_source_bucket` field + `dependency_checker.py`'s `features-onchain` bucket-template check were
  **deliberately NOT touched this session** — the prior session's investigation confirmed these feed a genuinely DEAD
  code path (zero real runtime consumers workspace-wide) and recommended DELETION (not repointing) as a distinct
  follow-up, out of scope for this repoint-and-delete-the-bucket task; flagged again here as an open deferred item.
  **(4) terraform + config check** — grepped all of `deployment-service/terraform/**` for the bare bucket name literal:
  zero hits (only the untouched `features-onchain-cefi/defi` asset-group siblings' terraform show up, per the separate
  Group-B rollback decision) — confirms the issue doc's own Finding that no `google_storage_bucket` resource ever
  managed this bare bucket, so no `terraform state rm` was needed. Checked `bucket_config.yaml`/`cloud-providers.yaml`/
  VM-launcher scripts for any bare-name reference: none found (the new `onchain-research` kind entry already carries a
  comment documenting the migration + consumer). **(5) delete** — re-ran the full pre-delete verification one final time
  immediately before the destructive step (corpus byte-total + both live-sleeve-file byte-diffs, all still matching),
  then
  `gcloud storage rm --recursive --continue-on-error gs://features-onchain-central-element-323112/ netflow_xsec_research`
  (16/16 objects removed) followed by
  `gcloud storage buckets delete gs://features-onchain-central-element-323112 --quiet`. Post-delete:
  `gcloud storage buckets describe` on the bare bucket now returns `404`; the new
  `onchain-research-central-element-323112` bucket independently re-verified still intact (70,768,303 bytes, 16 objects)
  after the source delete. No data loss, no unauthorized deletes, live sleeve state fully intact and reachable only from
  the new location now. Item (3) is CLOSED — issue doc status flipped to resolved (see issue doc for the closing note).
  Estate count this touch: **-1**.

- **2026-07-15, Cutover phase — `features-sports` 2 of 3 live-reference surfaces repointed to canonical `-prd-` bucket;
  the 3rd surface's "healthy" verification surfaced a pre-existing, unrelated production outage (STOP, operator notified
  via issue doc)**. Continuing item (2)'s blocker (b) from the entries above (ship-phase already landed the
  migrate-script + confirmed the 2 ephemeral objects): **(a) terraform data-source check** — re-grepped all of
  `terraform/gcp/**` + `configs/cloud-providers.yaml` for the bare `features-sports-${project_id}` literal: the only
  hits are the `google_storage_bucket.features_sports` resource itself + its `_imports_reconcile.tf:51-52` import block
  (both correctly left untouched — deleting the terraform resource is the NEXT phase's job, after the bucket delete) and
  `terraform/services/features-sports-service/gcp/main.tf`'s `gcs_volumes` FUSE-mount entry (item (b) below); nothing
  else references the bare name as a data source. **(b) Cloud Run job FUSE mount** — repointed
  `module.daily_job.gcs_volumes` from the bare bucket to `features-sports-prd-${project_id}` (added a small
  `bucket_env_short_map` local since this per-service terraform root had no existing env-short convention);
  `terraform plan` confirmed an in-place update only (no destroy/recreate) — applied via `terraform apply -target`
  scoped to just this one resource (deliberately NOT sweeping in two unrelated already-drifted
  `google_workflows_workflow` resources in the same plan, see below). Verified live via `gcloud run jobs describe`: the
  job spec now mounts `features-sports-prd-central-element-323112` at
  `/mnt/gcs/features-sports-prd-central-element-323112`. Manually triggered a real execution
  (`features-sports-service-job-n4l5z`, current CLI contract `--asset-group SPORTS ...`) to verify health rather than
  assume it — logs confirm GCSFuse mounted the new canonical bucket cleanly, but the job then crashed at pure Python
  import time (`ModuleNotFoundError: No module named 'unified_api_contracts.internal'`,
  `unified_trading_library/config_interface/auth/entitlements.py:15`), independent of and unrelated to the bucket mount
  (the failure fires before any GCS access, so the OLD bare-bucket mount would have failed identically). Corroborating
  evidence this is a pre-existing, weeks-old outage, not something this touch caused: the
  `features-sports-service-daily-trigger` Cloud Scheduler job is `PAUSED` (`userUpdateTime: 2026-06-08`), and the last
  `SUCCEEDED` `features-sports-service-daily` workflow execution on record is `2026-06-07` — the daily/backfill
  production sports-features pipeline has most likely been down since 2026-06-08. Also found (not applied, separate from
  the image bug): the checked-in `daily_workflow`/`backfill_workflow` Workflow-YAML sources already use `--asset-group`,
  but a full (un-targeted) `terraform plan` shows the LIVE deployed workflows still pass the retired `--category` flag —
  a second independent reason those workflows would fail even once the image is fixed. Filed
  `plans/active/issues/features_sports_service_cloud_run_job_broken_image_2026_07_15.md` (operator-notified per the
  big-finding HARD RULE — data-pipeline correctness, live production outage) with the full evidence + recommended next
  steps (locate/rebuild the actual `features-sports-service` image source — a separate repo not cloned in this workspace
  slot — then apply the `--category`→`--asset-group` workflow drift, then re-verify, then un-pause). **(c) VM launcher
  `GCS_BUCKET` defaults** — confirmed via grep that both launchers only ever use `GCS_BUCKET` to derive the ephemeral
  `_vm_staging/fss_backfill/` scratch prefix (tarball/runner-script/logs), never the actual feature-data destination
  (resolved separately at runtime via `resolve_bucket(kind="features-sports", ...)` against `cloud-providers.yaml`'s
  canonical entry) — updated both defaults from bare to `features-sports-prd-${project_id}`:
  `deployment-service/scripts/vm/launch-features-sports-parallel-backfill-vm.sh` and
  `features-service/scripts/sports/launch_parallel_backfill.sh`. `quality-gates.sh --no-fix` green on both repos
  (sentinels written == HEAD); shipped as two separate quickmerges —
  `deployment-service@d008754fba643db087164068c9b6952b48875d91` ("feat(sports): cutover features-sports Cloud Run FUSE
  mount + backfill launcher to canonical -prd- bucket") and `features-service@6be22334e36fc3846429e660fb5a34a6666eb34b`
  ("feat(sports): cutover VM-fanout backfill launcher GCS_BUCKET default to canonical -prd- bucket") — both landed on
  `live-defi-rollout`, working trees clean after. **Verdict**: 2 of 3 live-reference surfaces (a, c) fully repointed +
  verified; surface (b)'s mount repoint is applied
  - infra-verified correct, but the job it serves is NOT end-to-end healthy for a pre-existing, unrelated reason (broken
    image) — **the `features-sports` bare bucket is still NOT delete-eligible**: blocker (b) from the entry above is now
    narrower (mount fixed) but a NEW blocker (broken image + workflow-arg drift, tracked in the issue doc above) must
    clear before a genuine Verify+Delete re-attempt. No destructive action taken on the bare bucket itself this touch.

- **2026-07-15, `features-sports-service-job` root-cause + Verify/Re-enable phases — root cause CONFIRMED, deploy STILL
  BLOCKED on an operator A/B decision; scheduler correctly left PAUSED.** Two follow-on touches on the same broken-image
  finding above. **Root-cause (fix) phase**: fully confirmed the mechanism (not just the symptom) —
  `unified_trading_library`'s `entitlements.py` has required `unified_api_contracts.internal` since UAC commit
  `6bb892bc` (2026-04-02), but UTL's own `pyproject.toml` constraint on `unified-api-contracts` stayed loose
  (`>=0.1.0,<1.0.0`) through at least 2026-04-22, so any UTL base image built in that window resolved the highest
  _compatible_ wheel, `0.2.38` (published 2026-03-12 — this predates the 2026-03-26 commit that added the `internal/`
  namespace at all) instead of one that actually contains it; `features-sports-service`'s Dockerfile installs itself
  `--no-deps`, so it purely inherited the broken `0.2.38` baked into the UTL base image at its own 2026-04-22 build. Not
  applied: the fix requires first deciding the deployment source of truth, since the two candidate paths differ
  materially — (A) un-archive the GitHub-archived (2026-05-08) `features-sports-service` repo and patch/rebuild there
  (fast, minimal blast radius, but re-diverges an already- consolidated-away repo), vs (B) finish the abandoned
  2026-05-08 `features-service` consolidation by standing up a real Cloud Run job for
  `features-service/features_service/sports/*` (correct long-term state, larger scope — no live job exists there yet).
  That phase correctly stopped and escalated to the operator rather than guessing; no code/image/ deploy changes made.
  **Verify+Re-enable phase**: dispatched to deploy the rebuilt image and, only on a genuinely clean end-to-end
  execution, un-pause the scheduler — found `readyToDeploy: false` from the prior phase (the A/B decision above is still
  unresolved) and, per its own explicit instruction ("if `readyToDeploy` is false, STOP and report why"), took **no
  deploy action** (no `gcloud run jobs update`, no image rebuild, no terraform apply) and **no scheduler action** —
  `features-sports-service-daily-trigger` remains `PAUSED` exactly as it was (re-verified:
  `gcloud scheduler jobs describe features-sports-service-daily-trigger --location=asia-northeast1 --project=central-element-323112`
  unchanged from the prior entry). Updated the issue doc
  (`plans/active/issues/features_sports_service_cloud_run_job_broken_image_2026_07_15.md`) with a "Root cause CONFIRMED"
  section carrying the full mechanism + the A/B options verbatim — **status remains `open`**, NOT closed, since no fix
  was deployed. **This blocks nothing else in this plan beyond what the entry above already flagged**: the
  `features-sports` bare bucket remains NOT delete-eligible pending the operator's A/B call, then a rebuild/redeploy,
  then a genuinely clean manual execution, THEN (and only then) the scheduler un-pause and bucket Verify+Delete
  re-attempt. **Operator decision still needed** (repeated here for visibility since it gates this plan's
  `features-sports` closure): choose Path A (fast, re-diverges the archived repo) or Path B [RECOMMENDED — matches the
  completed code consolidation, avoids re-legitimizing an archived repo] or specify a hybrid/staged approach.

- **2026-07-15, `features-sports` bare-bucket Verify+Delete re-attempt — STOPPED, gate condition re-confirmed still
  unmet, bucket left untouched.** Dispatched to finish this deferred item (terraform-resource removal +
  `_imports_reconcile.tf` cleanup + physical bucket delete) contingent on `manualExecutionSucceeded: true`; the
  handed-in Verify-phase result already reported `manualExecutionSucceeded: false`, and this touch independently
  re-verified that condition with fresh evidence rather than trusting the prior report:
  `gcloud scheduler jobs describe features-sports-service-daily-trigger --location=asia-northeast1 --project=central-element-323112`
  still shows `PAUSED` / `userUpdateTime: 2026-06-08T04:16:20Z` (unchanged), and
  `gcloud run jobs executions list --job=features-sports-service-job --region=asia-northeast1 --limit=5` shows the 5
  most recent executions (`…-n4l5z` 2026-07-15T11:10, `…-vjlmz`/`…-xgw29`/`…-cmp9h` 2026-07-14T18:10, `…-6jrgw`
  2026-07-14T18:05) all with `failedCount=1` and no `succeededCount` — i.e. the job is still crashing on every
  execution, consistent with the still-open `unified_api_contracts.internal` import-time `ModuleNotFoundError`
  documented in the issue doc and the prior two Progress Log entries. Per this task's own explicit stop condition ("If
  `manualExecutionSucceeded` is false, STOP -- do not delete"), took **zero destructive or infra action**: did not touch
  `deployment-service/terraform/gcp/main.tf`'s `google_storage_bucket.features_sports` resource, did not touch
  `_imports_reconcile.tf`, did not run `terraform state rm`, did not run
  `gcloud storage rm`/`gcloud storage buckets delete` against `gs://features-sports-central-element-323112`, and did not
  touch `bucket_config.yaml` or scheduler configs. The bare bucket, its 1 real migrated object + 2 confirmed-ephemeral
  VM-staging objects, and the terraform resource all remain exactly as they were. **This item stays open, gated on the
  same unresolved operator A/B decision** (rebuild source-of-truth choice) called out in the entry above — no new
  blocker introduced, no progress lost, nothing to re-verify differently on the next attempt beyond re-checking
  `manualExecutionSucceeded` once a rebuilt image is actually deployed and a clean execution is observed.

- **2026-07-15 (~17:02Z), `features-sports` bare-bucket FinishBucketAndDocs re-dispatch — STOPPED again, gate condition
  re-confirmed still unmet, bucket left untouched.** Dispatched as the (intended) final closing touch of the whole
  `features-sports-service` consolidation thread, gated on "`schedulingReenabled` false or `realScheduledFireVerified`
  false → STOP, do not delete." Independently re-verified live rather than trusting the handoff:
  `gcloud scheduler jobs describe features-service-sports-daily-trigger --location=asia-northeast1 --project=central-element-323112`
  → `state: PAUSED`; `gcloud run jobs executions list --job=features-service-sports-job` → only the same two executions
  (`kk4dv`, `fs8sj`), both `Completed=False`/`NonZeroExitCode` — no execution has ever reached `SUCCEEDED`;
  `gcloud artifacts docker images list .../features-service --include-tags --sort-by=~CREATE_TIME` → `:latest` still
  `sha256:c204c49d...` (built 2026-07-14), still predating the UTL `c47273c1` consolidator-liveness fix. Root blocker is
  now a features-service Cloud Build reproducibly hanging inside its quality-gates test step (2/2 attempts, tracked in
  `plans/active/issues/features_service_cloud_build_quality_gates_hang_2026_07_15.md`, `status: open`) — until a build
  actually reaches `SUCCESS` and pushes a new `:latest` image, `features-service-sports-job` will keep hitting the same
  manifest-consolidator false-DOWN preflight failure on any re-attempt, so none was made. **Zero destructive or infra
  action taken**: bare bucket `gs://features-sports-central-element-323112`, its terraform resource
  (`google_storage_bucket.features_sports`), `_imports_reconcile.tf`'s import block, and all 4 linked issue docs
  (`features_sports_service_cloud_run_job_broken_image_2026_07_15.md`,
  `features_service_cloud_build_quality_gates_hang_2026_07_15.md`,
  `instruments_sports_manifest_consolidator_lock_livelock_2026_07_15.md`,
  `manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md`) all remain exactly as they were
  (statuses unchanged, all still `open`). This item stays open, gated on the SAME unresolved blocker as every touch
  since the build-hang was discovered — no new blocker introduced, no progress lost. Full evidence + next-step detail in
  the matching append to `plans/active/features_sports_service_consolidation_deploy_2026_07_15.md`'s Progress Log.
- **2026-07-15, `features-sports` bare bucket DELETED — blocker cleared, item CLOSED.** The gating blocker (the
  features-service Cloud Build hang + the resulting stale image + the manifest-consolidator false-DOWN preflight) is now
  fully resolved on the sister plan `features_sports_service_consolidation_deploy_2026_07_15.md`:
  `features-service:latest` was rebuilt (green build `fd73ca17-8d5a-435c-8ec6-9af11eb377fc`, carrying UTL `c47273c1`),
  `features-service-sports-job` reached a genuine `SUCCEEDED` on a real scheduled fire, and its scheduler is `ENABLED`.
  With the service proven healthy, the deferred `features-sports` bare-bucket delete was executed: re-confirmed the bare
  `gs://features-sports-central-element-323112` held exactly the expected 3 live objects (1 migrated
  `sfi_progressive.parquet` — verified intact in the canonical `gs://features-sports-prd-central-element-323112` at
  25,989 B — + 2 ephemeral `_vm_staging/fss_backfill/*`), all noncurrent versions collapsing to those same 3 logical
  paths; `tofu state rm google_storage_bucket.features_sports` (PROD state, prefix `terraform/state/prod`) → removed;
  the resource block in `deployment-service/terraform/gcp/main.tf` + the orphan import block in `_imports_reconcile.tf`
  removed → REMOVED comments (features-calendar precedent), `tofu validate` clean, shipped `deployment-service@bfea7928`
  (a concurrent foreign soft-delete WIP in main.tf was stash-isolated so only my hunk landed, then restored intact);
  `gcloud storage rm --recursive --all-versions` then `gcloud storage buckets delete --quiet` → `buckets describe` =
  `404 not found`. Canonical `-prd-` bucket + migrated object re-verified alive post-delete. All 4 linked issue docs
  flipped to `status: resolved` with Resolution sections. **This `features-sports` bucket-estate item is now fully
  CLOSED** — the flat legacy bucket is gone, the canonical `features-sports-prd-{pid}` is the sole SSOT. Full evidence:
  the FinishBucketAndDocs Progress Log entry in `features_sports_service_consolidation_deploy_2026_07_15.md`.
