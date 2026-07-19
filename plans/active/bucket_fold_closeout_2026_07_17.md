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
- [x] ✅ [DOCS] P3. **Parent-plan + issue-doc bookkeeping** — **DONE 2026-07-19.** ✅ Parent W3 execute todo already
      flipped ([[bucket_estate_consolidation_to_sub100_2026_07_13]] line 331). ✅
      [[bucket_estate_fold_design_2026_07_13]] §3 draft skeleton flipped (all executed-via-split-plan todos → done +
      pointers; IAM re-gating + alias-sunset left honestly open with tracking pointers). ✅ Hygiene sweep (0 hard
      failures) + inventory (0 orphans) verified. ✅ 3 audit issue docs ASSESSED — **none fully fold-resolved, all stay
      OPEN** with a "Wave-3 fold assessment" note added: (1) `terraform_bucket_estate_drift_resurrection` — per-fold TF
      import/state-rm + COLDLINE@60d done, BROADER main.tf reconcile (32-destroy drift, yaml-mirror sync, e2e polluter)
      remains; (2) `strategy_store_split_brain` — bucket side resolved (Fold D + 07-14 delete), reader-code legs
      (deployment-api defaults + UAC enumerate_envelope) remain = closeout 4c/4d; (3)
      `recon_bucket_missing_nightly_recon_failing` — OUT of fold scope (recon bucket fixed separately
      blrs@2f0380b/ds@ccfaca26; upstream producer chain is its own lifecycle). ✅ **Parent codex-audit todo (line ~355)
      DONE: PM@c6f97b239** — CLAUDE.md storage rule + `bucket-naming-and-config.md` stub (frontmatter `superseded_by` +
      summary + banner + read-instead list) repointed from the dead CLAUDE "(b+)" section + the archived
      `bucket_name_ssot` plan → the live `codex/05-infrastructure/bucket-isolation-model.md`;
      `per-asset-group-bucket-layouts.md` assessed NOT stale (covers Group A raw + path divergences; Group B folded
      shapes live in bucket-isolation-model.md, already updated PM@8ea8abd89).

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
- **2026-07-19, `/autonomous` closeout tick (cont.) — HYGIENE VERIFIED.** Ran `run_hygiene_sweep.sh` (**0 hard
  failures**, 1 soft warning = a plan's 500-line soft cap, non-blocking) + `regenerate_active_plan_inventory.py` (**114
  plans, 0 orphans, 0 TBD** — orphan count 0 satisfies the review-blocking threshold). The inventory-table refresh was
  NOT committed (the main-orchestrator owns that regen on its morning/EOD cadence; my run was verification-only,
  restored to avoid off-cadence churn on ~30 non-mine plans' recomputed cal-left). Parent W3 "execute the folds" todo
  already flipped (`bucket_estate_consolidation_to_sub100` line 331). **Still open in bookkeeping todo 4** (deferred to
  a later tick): flip `bucket_estate_fold_design_2026_07_13` §3 remaining todos; close the 3 audit issue docs
  (terraform-drift / recon / strategy-store-split-brain) IF the folds resolved them (needs per-doc read); the parent
  plan's own broader codex-audit todo (line 355 — `bucket-naming-and-config.md` superseded-pointer fix +
  `per-asset-group-bucket-layouts.md`).
- **2026-07-19, `/autonomous` closeout tick — BOOKKEEPING TODO 4 fully DONE.** Flipped
  [[bucket_estate_fold_design_2026_07_13]] §3 draft skeleton (all 15 executed-via-split-plan todos → done + per-fold
  pointers; the two genuinely-open items — IAM re-gating [tracked in
  [[bucket_iam_write_protection_per_tier_2026_06_09]]]
  - alias sunset [gated] — left honestly `[ ]`). Assessed the 3 audit issue docs → **none fully fold-resolved, all stay
    OPEN with a "Wave-3 fold assessment" note added** documenting what the folds DID resolve + what remains
    (terraform-drift: per-fold TF slice done, broader main.tf reconcile remains; strategy-store-split-brain: bucket side
    done, reader-code legs = 4c/4d; recon: out-of-fold-scope). Shipped the **parent codex-audit todo (line ~355)**:
    PM@c6f97b239 (promote-PR #1179) repointed CLAUDE.md's storage-rule SSOT + the `bucket-naming-and-config.md`
    superseded stub (frontmatter/summary/ banner/read-instead) from the dead CLAUDE "(b+)" section + the archived
    `bucket_name_ssot` plan → the live `codex/05-infrastructure/bucket-isolation-model.md`;
    `per-asset-group-bucket-layouts.md` assessed NOT stale. **Discovered (out-of-scope finding, not fixed)**: a mangled
    bucket-SSOT rule-shorthand ("(b+)" / "ln") appears in several other codex docs (artifact-versioning,
    ml-experiment-lifecycle, defi/tradfi/prediction-data-types-catalog, data-catalogue-schema,
    data-lineage-MTDS-features-ml) — pre-existing, not fold-caused, ambiguous to auto-fix; a doc-hygiene follow-up, not
    this closeout's scope. **CLOSEOUT STATUS: only the soft-window-gated alias sunset (todo 1)
  - the code loose-ends (4c deployment-api stash / 4d UAC WIP / 4e dormant helpers) remain.**
- **2026-07-19, `/autonomous` closeout tick — DIAGNOSTIC (no code ship; remaining items are gated/risky/half-baked).**
  Investigated the 3 remaining code loose-ends + the alias-sunset gate; all deferred with precise diagnoses:
  - **Alias-sunset gate check (todo 1) — QUANTIFIED, stays GATED.** Grepped every retired kind for live
    `resolve_bucket_name(kind="…")` callers: **features-\* / ml-\* still have 2–9 callers EACH** (features-delta-one 3,
    -volatility 3, -onchain 4; ml-models-store 9, ml-training-artifacts 7, ml-predictions/configs/artifacts 2 each) —
    consumers deliberately keep the OLD kind vocab (that's the alias design), so sunset needs a full per-consumer
    REPOINT to the folded kind, NOT just a redeploy. 8 kinds ARE current-code-grep-clean (features-xinstrument,
    features-mtf, execution-store-prediction, positions-store, pnl-attribution-store, risk-metrics-store,
    pnl-attribution-output, position-store-sports) but the soft-window/old-deployment gate still applies, and
    `archetype-state` now has 1 caller (the `tenderly_budget.py` fixed earlier this session). Verdict: partial sunset of
    the 8 grep-clean kinds is _possible_ but the full sweep is a multi-repo repoint of features/ml consumers — a real
    task, correctly left gated.
  - **4e dormant helpers — DEFERRED (risky-for-low-value).** `id_conventions.get_execution_bucket`/`get_strategy_bucket`
    are dormant (UTL → `__init__` `_from_id`/`_for_category` alias → execution-service re-export, zero call sites) AND
    un-tiered (`execution-store-{pid}` missing `-{env}-`). BUT there are THREE same-named function sets in UTL
    (`cloud_constants.py`, `id_conventions.py`, `cloud_interface/constants.py`) and the `cloud_constants` bare
    `get_execution_bucket` is ACTIVELY used on execution-service's trading-adjacent grid path
    (grid_generator_cli.py:334, grid_batch.py, live_execution_handler.py:646 — already Fold-C-updated). A multi-site
    deletion of same-named functions on a trading-adjacent codebase, autonomously, for dormant low-value code carries
    mistake-risk > benefit; tiering has a utils→cloud_interface circular-import risk + breaks the project_id test
    contract. Needs a bounded dedicated refactor (consolidate the 3 sets onto `resolve_bucket_name`) or operator input —
    NOT an autonomous quick tier/delete.
  - **4c deployment-api stash — DEFERRED (half-baked, partially superseded).** `stash@{0}` is folded-bucket
    DISPLAY/config WIP (11 files: deployment_api_config, batch_config_utils, services,
    consolidator_catalog.generated.json, pipeline_uat, path_combinatorics, service_status_execution, +
    data_status/manifest which OVERLAP origin's already-shipped axis-census). Grep-clean for strategy-store (so it does
    NOT advance strategy_store_split_brain — that reader leg is a separate un-started change). Moderate-value
    observability WIP, delicate to reconcile (origin moved the base on overlapping files), uncommitted/untested.
    Preserved in the deployment-api clone's `stash@{0}` ("slot3-deployment-api-wip-superseded-check-2026-07-19") for a
    careful operator-aware session — do NOT autonomously force half-baked display WIP into the live devops backend.
  - **4d UAC replay WIP + AWS recount — DEFERRED** (UAC stash = half-baked replay/source-capability WIP,
    operator-started; AWS = operator-deprioritized). **VERDICT: the Wave-3 fold mission + closeout are SUBSTANTIALLY
    COMPLETE** — core folds 100% done, 3/4 closeout todos done. Every remaining item is genuinely gated (alias sunset),
    a bounded refactor needing care/operator-input (4e), or operator-started half-baked WIP (4c/4d). Winding the loop to
    a long cadence; the right next actor for the remainder is the operator (or a dedicated, non-autonomous session), not
    a forced autonomous change.
- **2026-07-19, `/autonomous` RE-INVOKED — resuming the remaining loose-ends to actual DONE (AUTONOMOUS_AGENT_RULES rule
  1: no DEFERRED/BLOCKED end-states; the prior "substantially complete, deferred" was the anti-pattern that contract
  kills). LOOSE-END 4e DONE: UTL@0e749c35 + execution-service@724459569.** Deleted the dormant, un-tiered
  `id_conventions` `get_execution_bucket`/`get_strategy_bucket` (returned `execution-store-{pid}`/`strategy-store-{pid}`
  — missing the `-{env}-` tier the folds require; zero call sites, pure UTL→`_from_id`/`_for_category`
  alias→execution-service re-export chain). Removed: the 2 functions (UTL `utils/id_conventions.py`, kept
  `resolve_category` between them), the 2 `__init__` alias imports + `__all__` entries, the `TestBucketHelpers` unit
  class, the `UTL_ADOPTION_MATRIX.md` entry, and execution-service's dead `get_strategy_bucket_for_category` re-export.
  **Kept** the actively-used `cloud_constants` bare `get_execution_bucket` (execution-service grid path, already
  Fold-C-updated) + the `cloud_interface/constants` version — those are NOT dormant. Pre-audit grep-clean confirmed zero
  external importers. Shipped dep-first (UTL then execution-service) so UTL never lacks a symbol execution-service still
  imports; both QG-green, staging-first via Tier-C drain. NEXT: alias sunset (Phase 1 code-clean kinds → repoints) +
  4c/4d stashes + AWS recount, all to DONE.
- **2026-07-19, ALIAS SUNSET Phase 1 (todo 1 — PARTIAL): UTL@c8f5bf39.** Removed the 3 alias-ONLY, production-grep-clean
  retired kinds — `pnl-attribution-store`, `risk-metrics-store`, `pnl-attribution-output` — from UTL `_KIND_ALIASES` +
  the `test_bucket_naming_cell_sweep` GCP+AWS assertions. Verified via exhaustive grep: zero
  `resolve_bucket_name(kind=…)` callers (the flat trio's SSOT is the folded PATH_REGISTRY; writers call
  `kind="portfolio-state"` directly + carry their own object-key prefix — e.g. `venue_balance_tracker.py:86`,
  `tenderly_budget.py`), and these three NEVER had yaml keys (alias-only) so removal has **no yaml/terraform coupling**.
  **Todo 1 remains OPEN** — still-aliased retired kinds + their sunset dependencies: (a) `positions-store`
  (`cloud_constants.py:154` legacy `"positions"→"positions-store"` mapping) + `archetype-state` (`tenderly_budget.py`
  caller) need a trivial caller repoint→`portfolio-state` first; (b) `position-store-sports` / `archetype-state` /
  `execution-store-prediction` retain **yaml keys** across 5 copies → removal is coupled to the terraform
  derived-from-yaml reconciliation ([[terraform_bucket_estate_drift_resurrection_2026_07_13]], operator-aware 32-destroy
  drift — do NOT tofu-apply piecemeal); (c) `features-{delta-one,volatility,onchain}` (3–4 callers each) + `ml-*-store`
  (4–13 callers) still deliberately use the retired vocab (the alias's designed soft-transition) → Phase-2 caller
  repoints (behaviorally no-op renames kind="features-delta-one"→"features"; prefix stays caller-derived). The alias
  sunset is a large behaviorally-no-op refactor; Phase 1 shipped the zero-coupling safe slice. Prioritizing 4c/4d
  (operator's actual half-built functionality — higher value) next, then Phase-2 repoints.
- **2026-07-19, LOOSE-END 4c DONE: deployment-api@ff1c691.** The deployment-api `stash@{0}` WIP was NOT half-baked —
  it's coherent fold-awareness work, so per rule 1 it was FINISHED, not discarded. Reconciled it against origin's
  already-shipped axis-census (popped the stash → 2 conflicts in `data_status/__init__.py` + `manifest.py`, both
  resolved to ORIGIN which was a strict superset — origin already had my `ValueError` catch @manifest.py:585 + a
  superset of the axis-census imports, so nothing unique lost; content-survival verified). Shipped 8 files: fold-aware
  config-bucket docstrings (`deployment_api_config.py` — execution-store flat / ml-configs→ml-store /
  asset_group→prefix), the **features caller repoint** `kind="features-delta-one/volatility/onchain"→"features"`
  (`batch_config_utils.py` — ALSO advances alias-sunset Phase 2 for deployment-api), fold-aware display paths
  (`services.py` — `{ag}/`, `configs/` prefixes), + `service_status_execution.py` / `_core.py` / `path_combinatorics.py`
  / `pipeline_uat.py`, and the **regenerated** `consolidator_catalog.generated.json` (ran
  `scripts/gen_consolidator_catalog.py` rather than commit the stale stashed copy → reflects the folded consolidators:
  execution 3→1 single-root, strategy-store env-tiered). QG-green, staging-first. Consumed stash dropped. **⚠️ FINDING
  (not mine, preserved — needs owner decision, NOT bucket-fold scope)**: deployment-service
  `terraform/services/features-service-sports/gcp/terraform.tfvars` had an uncommitted change REVERSING the committed
  digest-pin fix (ds@6c47fa1 "pin features-service-sports-job to verified fixed image digest") back to tag-tracking
  `:latest`. It blocked the deployment-api dep pre-flight. Verified idle (not live — stayed clean after stash; only this
  tab's session touches this clone; other Claude sessions are in separate `.tabs/2`/`.tabs/4` clones). Preserved in
  deployment-service `git stash` "slot3-INHERITED-features-sports-tfvars-digest-unpin-PRESERVE"; the working tree is
  back at the committed **pinned** (correct-per-the-fix) state. The `:latest`-vs-digest-pin tradeoff
  (matches-other-services vs staleness-risk-that-ran-a-broken-image-5-weeks) is a real infra decision for the
  features-service-sports owner — NOT decided autonomously.
- **2026-07-19, LOOSE-END 4d — RESOLVED (bucket-fold UAC leg already DONE; replay stashes are a SEPARATE feature,
  out-of-scope).** The bucket-fold UAC leg (the `strategy_store_split_brain` UAC leg) is **already cut over**:
  `scripts/enumerate_envelope.py:1061` = `f"strategy-store-prd-{_PROJECT_ID}"` and
  `unified_api_contracts/canonical/gcs_paths.py:124` both use the folded flat env-tiered `strategy-store-prd` bucket
  (Fold D, 2026-07-18) — grep-clean of any per-AG `strategy-store-cefi` code hardcode (only explanatory comments
  remain). The UAC working tree is CLEAN. The 4 UAC stashes (`uac-replay-source-capability-wip-part3/part2`,
  `cascade-64579`, a "sibling WIP round 2") are a **DIFFERENT feature** (replay / source-capability / pipeline-mode —
  e.g. stash@{0} = `test_possible_manifest.py`, 5 replay lines / 0 bucket-fold lines), NOT bucket-fold; possibly a
  sibling's WIP. Per findings-triage they're annotated + LEFT (not finished/reverted — deciding a different feature's
  WIP is out of the bucket-fold closeout's scope + collision-risk). They don't block bucket-fold UAC ships (all landed;
  tree clean).
- **2026-07-19, LOOSE-END AWS recount — DONE + FINDING.** AWS (acct 427895769566) = **230 S3 buckets** (vs GCP 114). The
  AWS side of the Wave-3 folds is **INCOMPLETE by operator deprioritization** ("AWS deprioritized; GCP is where the real
  data is"): the folded TARGETS exist (`features-{ag}-{prd,test}`, `execution-store-pred-prd`) but the fold SOURCE
  buckets still linger EMPTY/unused — `features-delta-one-{cefi,defi,tradfi,pred}`, `features-volatility/onchain-*`,
  `ml-models-store-{prd,dev,stg}`, `ml-training-artifacts`, `execution-store-{cefi,defi,tradfi}`,
  `positions-store-defi-*`, `archetype-state-prd`. The code cutover repointed writers to the folded kinds (same yaml
  resolves the folded AWS buckets), so the sources are producer-less. **NOT autonomously deleting AWS buckets**:
  operator-descoped + irreversible
  - entangled with the terraform derived-from-yaml destroys ([[terraform_bucket_estate_drift_resurrection_2026_07_13]],
    do-NOT-tofu-apply). AWS fold-completion (source deletion) is an operator-gated follow-up on the terraform-drift
    issue.
