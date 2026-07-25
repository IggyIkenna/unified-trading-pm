---
doc_type: plan
title: Bucket estate consolidation — closeout residuals (6 forked mop-up todos)
summary:
  "Forks the 6 still-open todos from bucket_estate_consolidation_to_sub100_2026_07_13.md (15/21 done, archived
  2026-07-24 per the plan line-cap remediation triage) into a small standalone closeout plan: recon-bucket end-to-end
  chain characterization, the cross-plan deletion checkpoint (DeFi/lending/legacy-twin buckets owned by other plans),
  the ml legacy flat-bucket trio delete, the 11-alias `_KIND_ALIASES` hard-removal, residual asset-group-parity cosmetic
  drift, and closing/re-confirming the 3 bucket-SSOT audit issue docs. Content moved verbatim, not rewritten — see the
  archived parent's Progress Log for the full Wave 0-3 execution history."
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
tags: [gcs, buckets, consolidation, closeout, terraform, migration, lifecycle, infrastructure, plan-hygiene]
related:
  [
    /plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    /plans/active/issues/recon_bucket_missing_nightly_recon_failing_2026_07_13.md,
    /plans/active/defi_dedicated_bucket_shared_migration_2026_07_13.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
  ]
created: "2026-07-24"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
assigned_role: infra
drift_direction: advance-code
depends_on: [defi_dedicated_bucket_shared_migration_2026_07_13]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Forked 2026-07-24 from bucket_estate_consolidation_to_sub100_2026_07_13.md per the plan line-cap remediation
  (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 1) — parent hit 2129 lines against the 1000L
  hard-fail cap with only 6/21 todos still open; this plan carries those 6 forward verbatim while the parent archives
  with its Progress Log intact as history."
last_updated: 2026-06-27
---

# Bucket estate consolidation — closeout residuals

> **Forked 2026-07-24** from `bucket_estate_consolidation_to_sub100_2026_07_13.md` (archived same day to
> `/plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md`, 15/21 todos done — see its Progress Log
> for the full Wave 0-3 execution history, including the audit provenance, the operator rulings baked in, and every
> shipped commit). This plan carries forward, **verbatim, unedited**, the 6 todos that were still open at archival time
> — no scope was added or dropped in the fork.

Codex SSOTs: `/codex/05-infrastructure/bucket-isolation-model.md`, `/codex/05-infrastructure/gcs-lifecycle-policies.md`,
`/codex/05-infrastructure/gcs-object-operations.md`, `/codex/02-data/pipeline-mode-partition.md`,
`/codex/05-infrastructure/manifest-consolidator-ssot.md`.

## Wave 2 residuals — in-flight completions + audit-found breakages

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
- [ ] [DATA] P0. Track to completion the deletions OWNED BY OTHER PLANS (checkpoint; UPDATED 2026-07-25 — was:
      "dex-pools-prd purge-lifecycle armed (24h async; disarm window if concerns)", stale vs. the sibling plan's more
      final status, corrected per `defi_dedicated_bucket_shared_migration_2026_07_13.md`:221-224: DeFi trio — parity
      re-verified by agent incl. closing a 6,941-object gap, all 3 of lst-rates-prd/perp-funding-prd/dex-pools-prd
      CONFIRMED DELETED (`gcloud storage buckets list`, zero matches in any form, 2026-07-14) — dex-pools-prd was
      deleted directly by the operator on 2026-07-14T11:03:47Z, BEFORE that todo's own snapshot-before-delete step ran
      (not via the planned 24h purge-lifecycle path; no independent pre-delete object-diff of the ~209k-object legacy
      tree exists — risk assessed low, not zero, per the sibling plan's own writeup), kinds removed from all 5 yaml
      copies (34), TF state clean; L6 twins — cefi/defi/tradfi tick+instruments purge-lifecycle armed (sports pair HELD
      for sports-plan E1/E8; bucket deletes = follow-up one-liner once purged); lending pair still HELD — Morpho VM
      completed but write-target verification inconclusive): `dex-pools-prd`/`lst-rates-prd`/`perp-funding-prd` (−3,
      [[defi_dedicated_bucket_shared_migration_2026_07_13]] todos 6-9 incl. the TF-resource removal added 2026-07-13);
      `lending-indices`+`-prd` (−2, same plan / estate cleanup §5i, gated on VM `mtds-lending-indices-20260712-112557`
      completion); legacy flat tick+instruments twins (−8, M-1 `data_completion_to_100_all_ag_2026_06_21` L6,
      operator-gated version-aware deletes — millions of noncurrent versions).
- [ ] [DATA] P1. **ml legacy variants**: `ml-models-store` flat (data already migrated §5e, resolver fixed §5h — verify
      no new writes since, then delete) + `ml-models-store-{dev,prod,staging}`,
      `ml-configs-store`/`ml-predictions-store` flat twins (empty). Verify
      `deployment-api/deployment_api_config.py:642`'s flat `ml-configs-store-{pid}` default is repointed first.

## Wave 3 residuals — structural-fold closeout

- [ ] [DATA] P3. **`_KIND_ALIASES` hard-removal — 11 coupled aliases still need a per-consumer repoint before their
      alias can be removed** (folded in from `bucket_fold_closeout_2026_07_17.md`, its sole open todo). Phase 1 + Phase
      2 Part A are DONE: 6 alias-only/grep-clean kinds already hard-removed (`pnl-attribution-store`,
      `risk-metrics-store`, `pnl-attribution-output`, `positions-store`, `archetype-state`, `position-store-sports` —
      UTL@c8f5bf39/384e0b28), every LIVE `resolve_bucket_name(kind=<retired>)` consumer across ml-service,
      features-service, execution-service, UTL, deployment-service, and deployment-api now calls the folded kind
      directly (behaviorally no-op), and the yaml-key/terraform coupling that gated Part B is CLEARED (13 retired yaml
      keys stripped from all 5 copies, `tofu plan` 0 bucket-create/0 bucket-destroy). **Remaining = 11 aliases** whose
      readers deliberately still resolve the retired vocab and are NOT yet repointed:
      `features-{delta-one,volatility,onchain,xinstrument,mtf}` (features-service `run_pipeline_e2e.py`
      `_test_bucket`/`_delta_one_test_bucket` + `smoke_matrix.py` SMOKE_INPUT_KIND + data-status-drilldown service→kind
      maps + the still-present `upgrade_manifest_to_v8.py` loop resolver for xinstrument/mtf),
      `ml-{models,predictions,configs,training-artifacts,artifacts}-store` (deployment-api `deployment_api_config.py`
      resolvers + ml-service), and `execution-store-prediction` (same `upgrade_manifest_to_v8.py` loop — delete the dead
      migration OR repoint). Each needs its caller repointed to the folded kind
      (`features`/`ml-store`/`execution-store`) + an explicit object-key prefix BEFORE its `_KIND_ALIASES` entry (UTL
      `bucket_naming.py`) is removed. **KEEP permanently**: `tick-data`, `features-cross-instrument`,
      `features-multi-timeframe` (live consumer vocabulary, not retired). **Gate**: each of the 11 grep-clean of
      `resolve_bucket_name(kind=<retired>)`, its alias removed, and `terraform plan` stays green after removal. "No
      double SSOT." **Not this todo's scope, deferred separately (found during the fold, not omitted)**: a
      `deployment-service` git stash reverting a digest-pin fix on
      `terraform/services/features-service-sports/gcp/terraform.tfvars` (owner: features-service-sports, "NOT decided
      autonomously" — a real pin-vs-`:latest` tradeoff); 4 UAC git stashes (replay/source-capability WIP, a different
      feature's WIP, not bucket-fold scope). Neither is tracked anywhere else yet — flagging so they don't get lost, not
      claiming them here.
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
- [ ] [DOCS] P3. **Close (or re-confirm still-open) the three bucket-SSOT audit issue docs** referenced by the
      codex-audit todo above — assessed during that audit and deliberately left open rather than closed by the fold;
      re-verify their current status before closing.

> **Note on the "(item above)" / "the fold" cross-references above**: these two todos were extracted verbatim from the
> archived parent, where "item above" referred to the dev/stg-tier retirement (Wave 1, DONE) and "the fold" referred to
> the Wave 3 structural-fold execution (DONE) — both fully described in the archived parent's Wave 1/Wave 3 sections and
> Progress Log. Read `/plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md` for that context
> before starting either todo; it was deliberately not re-paraphrased here per the lossless-fork rule.

## Progress Log

- **2026-07-24** — Plan created. Forked verbatim from `bucket_estate_consolidation_to_sub100_2026_07_13.md`'s 6
  remaining open todos (of 21; 15 were already done) as part of the plan line-cap remediation
  (`/plans/archive/issues/plan_line_cap_remediation_2026_07_23.md`, row 1 / bucket (c)). Parent archived same day to
  `/plans/archive/2026_07/bucket_estate_consolidation_to_sub100_2026_07_13.md` with `status: complete` and
  `superseded_by: [bucket_estate_consolidation_closeout_2026_07_24.md]`; its Progress Log (Waves 0-3 execution history,
  audit provenance, operator rulings) stays intact there as the historical record. No new work executed yet under this
  plan — todo bodies are exactly as they read in the parent at fork time.
