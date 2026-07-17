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
- [ ] [DOCS] P3. **Post-phase codex audit (all folds)** — update `bucket-isolation-model.md` (Group-B naming table →
      folded shapes: `ml-store`, `features-{ag}`, `execution-store`, `strategy-store` tiered, `portfolio-state`);
      `manifest-consolidator-ssot.md` (target set — the collapsed job counts); `gcs-lifecycle-policies.md` (supersede
      the "intentionally NOT lifecycle'd" claim with the STANDARD→COLDLINE@60d + prefix exceptions actually applied).
      Add SUPERSEDED banners where the folds invalidated prior contracts.
- [ ] [DATA] P3. **Final estate recount** — recount live buckets (GCP + AWS) vs the design §4 target (~100 total / ~80
      non-GCP-system). Record the actual number in this Progress Log; if it overshoots, diagnose which folds
      under-deleted.
- [ ] [DOCS] P3. **Parent-plan + issue-doc bookkeeping** — flip [[bucket_estate_consolidation_to_sub100_2026_07_13]]'s
      W3 execute todo to done (cite this plan + the four fold plans); flip [[bucket_estate_fold_design_2026_07_13]] §3
      remaining todos; close the three audit issue docs (terraform drift / recon / strategy-store split-brain) if the
      folds resolved them. Run `run_hygiene_sweep.sh` + `regenerate_active_plan_inventory.py` (orphan count must be 0).

## Progress Log

- **2026-07-17, authored** as the closeout successor of [[bucket_estate_fold_design_2026_07_13]] §3 trailing
  cross-cutting todos. Gated on all four fold plans. Nothing executed yet.
