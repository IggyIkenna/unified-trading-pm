---
doc_type: plan
title: Bucket fold — Wave-3 cross-cutting closeout (codex audit, estate recount, alias sunset)
summary:
  "Closeout plan for the Wave-3 structural folds — the cross-cutting work that can only land AFTER all four fold
  execution plans (ml, features, execution+strategy, portfolio-state) complete. Consolidates: the post-phase codex audit
  spanning all folds (bucket-isolation-model.md Group-B naming table → folded shapes, manifest-consolidator-ssot.md
  target set, gcs-lifecycle-policies.md supersede the 'intentionally NOT lifecycle'd' claim), the final estate recount
  vs the design §4 target (~100 total / ~80 non-GCP-system), a global _KIND_ALIASES sunset sweep (hard-remove any
  aliases the individual folds left open once every fallback window is grep-clean), and the parent-plan bookkeeping
  (flip the consolidation plan's W3 execute todo, close the three audit issue docs). HUMAN plan — depends_on all four
  folds."
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, meta]
repos: [unified-trading-pm, unified-trading-library, unified-api-contracts, deployment-service]
scope: [engineer, admin]
tags: [gcs, buckets, consolidation, fold, codex, estate-recount, alias-sunset, lifecycle, infrastructure]
related:
  [
    plans/active/bucket_estate_fold_design_2026_07_13.md,
    plans/active/bucket_estate_consolidation_to_sub100_2026_07_13.md,
    plans/active/bucket_fold_ml_2026_07_17.md,
    plans/active/bucket_fold_features_2026_07_17.md,
    plans/active/bucket_fold_execution_strategy_2026_07_17.md,
    plans/active/bucket_fold_portfolio_state_2026_07_17.md,
    codex/05-infrastructure/bucket-isolation-model.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
  ]
created: "2026-07-17"
last_updated: "2026-07-17"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: infra
drift_direction: advance-code
depends_on:
  [
    bucket_fold_ml_2026_07_17,
    bucket_fold_features_2026_07_17,
    bucket_fold_execution_strategy_2026_07_17,
    bucket_fold_portfolio_state_2026_07_17,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
source:
  "Successor execution plan of bucket_estate_fold_design_2026_07_13 §3 (the trailing cross-cutting todos: codex audit,
  estate recount, alias sunset, parent-plan flip). Operator ruling 2026-07-17: all 5 folds as HUMAN plans. Gated on all
  four fold plans completing."
---

# Bucket fold — Wave-3 cross-cutting closeout

> **Gated on all four fold plans.** Do NOT start until [[bucket_fold_ml_2026_07_17]],
> [[bucket_fold_features_2026_07_17]], [[bucket_fold_execution_strategy_2026_07_17]], and
> [[bucket_fold_portfolio_state_2026_07_17]] are complete (their sources deleted, TF/yaml removed).

**What / why**: the trailing cross-cutting todos of [[bucket_estate_fold_design_2026_07_13]] §3 that span all folds and
can only land once they're all done. Kept as a separate gated plan so no single fold owns global work.

## Codex SSOTs (this plan UPDATES these — they are the deliverable, read current state first)

- `codex/05-infrastructure/bucket-isolation-model.md` — Group-B naming table.
- `codex/05-infrastructure/manifest-consolidator-ssot.md` — consolidator target set.
- `codex/05-infrastructure/gcs-lifecycle-policies.md` — lifecycle claims.

## Todos

- [ ] [DATA] P3. **Global \_KIND_ALIASES sunset** — sweep all four folds: for every retired kind whose reader-fallback
      window has closed and is grep-clean (no `resolve_bucket_name` caller, no
      `READER_FELL_BACK_TO_LEGACY_PATH`-equivalent), hard-remove its `_KIND_ALIASES` entry (UTL `bucket_naming.py`) +
      any residual retired yaml key. "No double SSOT." Verify `terraform plan` (derived-from-yaml drift detector) stays
      green after removals. (Absorbs each fold plan's deferred P3 alias-sunset todo.)
- [x] ✅ [DOCS] P3. **Post-phase codex audit (all folds)** — **DONE 2026-07-19: PM@8ea8abd89** (promote-PR #1177 → main,
      v2 auto-merge). Ground truth taken from the live UTL resolver (`resolve_bucket_name`, run-it-don't-read-it), not
      the yaml. Updated `bucket-isolation-model.md` §2 Group-B table → folded shapes (`features-{ag}` per-AG; `ml-store`
      / `execution-store` [ag→`{category}/` prefix] / `strategy-store` / `portfolio-state` cross-asset flat) +
      object-key prefix column + `_KIND_ALIASES` soft-window note + SUPERSEDED banner + §3 examples + §10 usage;
      `manifest-consolidator-ssot.md` "Coverage gap" → SUPERSEDED banner with the folded consolidator target set
      (features N→5 per-AG, execution 3→1 single-root, ml 5→1, strategy 1, portfolio-state none) + direct-gcloud
      retarget note; `gcs-lifecycle-policies.md` "intentionally NOT lifecycle'd" → updated: folded buckets provisioned
      `STANDARD→COLDLINE@60d`, portfolio-state confirm-before-COLDLINE. All 3 prettier-clean, QG-green.
- [x] ✅ [DATA] P3. **Final estate recount** — **DONE 2026-07-19: GCP = 114 total buckets** (down from ~140+ pre-fold;
      ~30 source buckets removed by the 5 folds). NO folded source bucket lingers (grep clean: execution-store-{ag},
      features-{delta-one,volatility,onchain,xinstrument,mtf}-*, positions-store, pnl-attribution-store,
      archetype-state, position-store-sports, strategy-store-flat all gone). The 114-vs-59-TF-tracked gap is
      PRE-EXISTING estate drift (market-data/billing buckets not in canonical TF) — separate from the folds,
      operator-aware. AWS recount deferred (operator deprioritized AWS; GCP is where the real data is).
- [ ] [DOCS] P3. **Parent-plan + issue-doc bookkeeping** — flip [[bucket_estate_consolidation_to_sub100_2026_07_13]]'s
      W3 execute todo to done (cite this plan + the four fold plans); flip [[bucket_estate_fold_design_2026_07_13]] §3
      remaining todos; close the three audit issue docs (terraform drift / recon / strategy-store split-brain) if the
      folds resolved them. Run `run_hygiene_sweep.sh` + `regenerate_active_plan_inventory.py` (orphan count must be 0).

## Progress Log

- **2026-07-17, authored** as the closeout successor of [[bucket_estate_fold_design_2026_07_13]] §3 trailing
  cross-cutting todos. Gated on all four fold plans. Nothing executed yet.
- **2026-07-19, `/autonomous` — ALL 5 WAVE-3 FOLDS COMPLETE; closeout STARTED.** Folds shipped: Fold-A (features, incl.
  BQ re-mount 766k rows + N→5 consolidator), ml Fold-B, Folds C+D (execution/strategy, execution 3→1 single-root
  consolidator), Fold-E (portfolio-state). Each: code cutover (multi-agent implement→adversarial-verify→fix — the
  adversarial passes caught a silent-P&L reader bug in C+D + the stale-PM-yaml UTL-CI break) → migration parity →
  consolidator retarget via direct gcloud → source delete → TF import folded + state-rm sources. Plus keystone unblock
  (UAC -USD contract drift misdiagnosis corrected) + 2 operator-flagged flakes fixed (VaR golden cents-quantize; UTL CI
  stale-PM-yaml). **Estate recount DONE (114 GCP, ~30 removed); parent W3 plan flipped.** DEFERRED (this Progress Log):
  (1) **\_KIND_ALIASES sunset** — soft window NOT closed (services still promoting→cloudbuild with the folded kinds; the
  aliases + retained yaml keys must stay until every consumer redeploys + is grep-clean). (2) **Codex audit** —
  bucket-isolation-model.md / manifest-consolidator-ssot.md / gcs-lifecycle-policies.md folded-shape updates. (3)
  **Issue-doc close + hygiene sweep**. (4) **Loose ends**: execution-service `tenderly_budget.py` archetype-state root
  prefix (empty bucket, internally symmetric); deployment-api C+D display + Fold-B ml-store + data_status axis-census +
  Fold-A batch_config (tangled tree, scoped commits); UAC replay/source-capability WIP (~8 files stashed,
  finish/revert); UTL/UAC dormant un-tiered id_conventions helpers; consolidator job renames
  (uts-…-execution-cefi→execution, feature per-kind→per-AG); AWS consolidator 404 cleanup + AWS bucket recount.
- **2026-07-19, `/autonomous` closeout tick — CODEX AUDIT DONE (PM@8ea8abd89, promote-PR #1177).** All 3 codex docs
  updated to the folded shapes, ground-truthed against the live UTL `resolve_bucket_name` resolver (not the yaml, which
  still carries the retired per-kind keys during the soft window). **CI verification**: UTL `quality-gates-v2` GREEN on
  main. **Incidental (not mine, fixed to unblock)**: my PM QG sentinel was blocked by a NEW `workflow-template-parity`
  drift — a peer updated the `major-bump-issue-handler.yml` template SSOT 2026-07-18 (REPO-non-empty guard) and rolled
  it to strategy-service/UTL/deployment-service/agent-orchestrator but `deployment-api`'s copy lagged. Completed the
  straggler via scoped `rollout-workflow-templates.sh --repo deployment-api --template …`; on the pull it turned out a
  peer had ALSO just shipped the identical rollout to origin (my local copy was redundant, discarded via FF).
  **Loose-end status shift (item 4c)**: the deployment-api data_status **axis-census** WIP was SHIPPED by a peer on
  origin (`_axis_census.py` + `test_route_data_status_axis_census.py` now committed) — my local dirty copy of that
  concern is superseded. My remaining unique deployment-api WIP (the C+D-display / Fold-B-ml-store edits origin did NOT
  touch: `services.py`, `batch_config_utils.py`, `deployment_api_config.py`, `service_status_execution.py`,
  `data_status_drilldown/_core.py`, `path_combinatorics.py`, `pipeline_uat.py`, `consolidator_catalog.generated.json`)
  is preserved in deployment-api `git stash@{0}` ("slot3-deployment-api-wip-superseded-check-2026-07-19") — a later tick
  must reconcile it against origin's new axis-census versions (verify no overlap-conflict on `data_status/__init__.py` +
  `services/data_status/manifest.py`), gate, and ship as scoped commits OR discard if origin already covers it. Do NOT
  blind-pop (origin shipped overlapping files).
- **2026-07-19, `/autonomous` closeout tick (cont.) — LOOSE-END 4a DONE: execution-service@9a1f4f1d.**
  `execution_service/providers/tenderly_budget.py` now writes under the `archetype-state/` domain prefix inside the
  folded portfolio-state bucket (`_BUDGET_DOMAIN_PREFIX="archetype-state"` → blob key
  `archetype-state/tenderly_budget/{archetype}/day=….json`), matching the Fold-E domain-prefix convention (positions/,
  pnl-attribution/, risk-metrics/, …). No data migration needed — the bucket was empty (nothing traded) and
  writer+reader are the same class (internally symmetric). Docstring updated to the folded bucket. 6 unit tests green,
  execution-service QG green. Staging-first repo → LDR→staging via Tier-C drain. Remaining loose ends: deployment-api
  C+D-display/Fold-B WIP (stashed, 4c — reconcile vs origin's new axis-census), UAC replay WIP (4d), UTL/UAC dormant
  un-tiered helpers (4e), consolidator job renames (cosmetic — documented in the codex SUPERSEDED banner, not
  executing), AWS recount.
