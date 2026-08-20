---
doc_type: plan
title: Sports taxonomy P3 — finalize (reconcile the 6 absorbed source docs + archive)
summary: >-
  Gated closeout for sports_taxonomy_p3_consumers_2026_08_08.md. P3 absorbs the open todos of six separate sports docs
  (ml-service --family, the T-2h/T-6h model horizon, the verify_ml_readiness pass bar, the fixture-grain catalogue
  dispatch, the fixtures-browser freshness posture, and the sports_dependency mapping scope), so this finalize flips
  each source doc's own checkbox with verified evidence, archives any source doc left at zero open todos, and confirms
  the distinct-values panel genuinely stopped hiding values before archiving P3.
status: active
nature: process
asset_group: [sports]
stage: [features]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, consumers, finalize, archival, distinct-values, ml]
related:
  [
    /plans/active/sports_taxonomy_p3_consumers_2026_08_08.md,
    /plans/archive/2026_08/issues/ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md,
    /plans/active/issues/sports_features_layer_findings_sweep_2026_07_18.md,
    /plans/archive/2026_08/issues/sports_odds_stale_fixture_reinjection_2026_07_14.md,
    /plans/active/sports_catalog_league_grain_only_scope_2026_07_08.md,
    /plans/active/sports_fixtures_browser_single_catalogue_source_2026_07_24.md,
    /plans/active/issues/sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md,
  ]
created: 2026-08-08
last_updated: 2026-08-17
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
assigned_role: backend_engineer
effort: medium
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
depends_on: [sports_taxonomy_p3_consumers_2026_08_08]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/sports_taxonomy_p3_consumers_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
source: >-
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
locked_by:
locked_since:
---

# Sports taxonomy P3 — finalize

> **Machine-gated** on `sports_taxonomy_p3_consumers_2026_08_08.md`.

## Todos

- [ ] [REVIEW] P1. **Flip each of the six absorbed source docs' OWN checkboxes with re-verified evidence.**
      `ml_service_sports_clv_training_pipeline_never_functional_2026_07_26.md` (--family wired),
      `sports_features_layer_findings_sweep_2026_07_18.md` (T-2h + T-6h added),
      `sports_odds_stale_fixture_reinjection_2026_07_14.md` (aggregate >=95% bar),
      `sports_catalog_league_grain_only_scope_2026_07_08.md` (fixture-grain dispatch, all 4 todos),
      `sports_fixtures_browser_single_catalogue_source_2026_07_24.md` (staleness labelled), and
      `sports_dependency_check_manifest_vs_gcs_path_2026_07_08.md` (caller audit outcome). Confirm each cited commit
      exists via `git log` — do not trust a source doc's own evidence line. **Done when**: all six are flipped with
      confirmed commits.
- [ ] [REVIEW] P1. **Archive any of the six left at zero open todos** via the same 6-step ritual — the batch-extraction
      omission that previously caused a real hygiene-sweep hard-fail. **Done when**: each of the six is either still
      open with todos, or archived.
- [ ] [REVIEW] P1. **Prove the panel stopped hiding values, from the rendered output not the code.** Fetch the live
      distinct-values response for sports and confirm it now lists every raw manifest value — including
      accepted-exception venues, the blank sentinel, and any uppercase residue — each badged rather than dropped. The
      audit's starting state was 10 of 31 venues and 7 of 10 data types rendered. **Done when**: the rendered value
      counts equal the manifest's, with badges.
- [ ] [REVIEW] P2. **Confirm the sibling asset_groups' masking report was filed.** P3's cross-AG re-check must have
      produced a per-AG count of hidden values for cefi/defi/tradfi/prediction, with `- [ ]` follow-ups filed where
      material. A silent pass is not acceptable — this masking class was AG-generic. **Done when**: the per-AG counts
      are recorded and follow-ups exist where material.
- [ ] [REVIEW] P2. **Confirm the T-2h/T-6h retrain reported a MEASURED delta**, not an assumed improvement. If the added
      horizons degraded model performance, that is a finding requiring a `- [ ]` follow-up, not a silent acceptance of
      the operator's ruling to add them. **Done when**: the coverage and performance delta are recorded.
- [ ] [DOC] P2. **Archive `sports_taxonomy_p3_consumers_2026_08_08.md`** via the standard 6-step ritual, including the
      codex-alignment check (the ML label lineage note is a real codex change), the corpus-wide referrer-path fixup, and
      archiving this finalize doc alongside it in the same commit. **Done when**: the plan is in
      `plans/archive/2026_08/`, every referrer resolves, and this doc is archived with it.

## Progress Log

- **2026-08-08** — Authored alongside the parent per the finalize-plan-coverage rule.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries) -- re-verified all 3 entries still
  resolve on disk; unchanged.
