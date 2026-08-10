---
doc_type: issue
title:
  "2026-08-10 /ag-closeout-audit prediction (sharded, agt-c11349) — strict-coverage-bar correction: 4 orphaned docs (all
  non-batchable), 0 new batch"
summary: >-
  Independent sharded `/ag-closeout-audit prediction` run (dispatch agt-c11349, slot 25) that reached a DIFFERENT orphan
  count than the earlier 2026-08-10 runs (slot 26 `all`-mode + slot 24 sharded, which reported "0 real orphans" on the
  weaker linkage signal): a full per-doc Workflow pass (34 AG-primary docs, one read-only agent per doc) under the
  skill's strict dispatched-`## Todos`-entry coverage bar finds **4 orphaned prediction docs** — all `assigned_vm: NA`,
  all carrying ONLY non-batchable remaining work (operator-gated / time-gated / design-gated per the non-batchable
  taxonomy) — so Phase 3 still correctly drafts **no** new batch (matching the prior runs' operational outcome; batch10
  remains the live dispatch surface). The delta vs the prior "0 orphans" is methodological, not a fresh finding set: the
  linkage checker's body-mention signal counts a doc as covered when a covering plan merely NAMES it, while this run's
  per-doc read applies the 2026-08-10 coverage-bar refinement (only an open `- [ ]` in a DISPATCHED covering plan's own
  `## Todos` counts). 3 docs the naive bar would call orphaned are reclassified self-dispatched (`planning`+`open`, AO
  ingests their own open checkboxes) and 1 is genuinely multi-AG — both corrections recorded here so a future run does
  not over-report them.
status: open
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prediction, ag-closeout-audit, parked-findings, orphan-audit, coverage-bar, strict]
related:
  [
    /plans/archive/2026_08/issues/ag_closeout_audit_prediction_parked_2026_08_09.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_prediction_parked_2026_08_10.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
    /scripts/plan-hygiene/check_ag_closeout_linkage.py,
  ]
created: "2026-08-10"
author: "slot-25 (ag_closeout_auditor, sharded prediction tranche)"
last_updated: "2026-08-10"
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.05
estimate_calibrated_ai_days: 0.03
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
context_scope: [/scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py]
source: >-
  `/ag-closeout-audit prediction` sharded dispatch 2026-08-10 (ag_closeout_auditor scheduled worker, slot 25, one-shot,
  `$TRANCHE=prediction` set). Full per-doc Phase-1 Workflow (34 agents) + Phase-2 synthesis; Phase 3 not run (0 new
  batchable orphans).
---

# Parked findings — 2026-08-10 `/ag-closeout-audit prediction` (sharded, strict coverage bar)

## Run summary

- **Corpus**: `generate_ag_closeout_audit_candidates.py --tranche prediction` → **34 members** (was 38 at the earlier
  2026-08-10 runs; −4 because `batch10` + its finalize and this run's predecessor parked doc were archived complete
  since, correctly absent). 11 plans + 23 issues. **13 covering docs** (consolidated closeout + 4 Phase A-E children +
  satellite batches 4/6/7/8 + their finalizes; batches 1/2/3/5/9/10 archived complete = coverage DONE).
- **Covering-plan health flagged (hygiene, not orphan)**: `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` shows
  **0 open todos / 7 done but still `status: active`** (not archived) — a done-but-unarchived plan
  (plan-reconcile/archive-candidates territory, not this skill's to fix in-run; recorded here so the operator sees it).
  Its finalize has 1 open reconcile/archive todo.
- **Orthogonality HARD CHECK** (full 9-tranche peer set): 0 prediction-primary docs carry the dangerous
  single-tranche+cross-cutting mistag shape. The 20+ docs tagged `[prediction, <other-AG>…]` are all the legitimate
  4-6-peer-AG multi-tranche pattern. `sports_prediction_mvp_writetime_precompute_2026_07_24.md` (bare `[cross-cutting]`,
  `sports_prediction_`-named) read + confirmed genuinely hybrid (shared manifest-schema/deployment infra spanning
  sports+prediction+deployment-api, `parent_epic: deployment_and_user_management_master`) — NOT a prediction mistag,
  left to the ui/cross-cutting sibling runs (concurrent workers, shared-file safety).

## Verdict counts (34 audited, excluding `exclude_cross_cutting`)

| Verdict                         | Count | Notes                                                                                                                                                                                                                                          |
| ------------------------------- | ----- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `archivable_now`                | 5     | `mtds_prediction_adapters_dead_rest_polling_interface`, `sports_odds_feature_naming_four_way_mismatch`, `kalshi_live_capture_regression_and_drift`, `predictions_other_bucket_and_ui_drilldown`, `sports_odds_feature_naming_canonicalization` |
| `archivable_after_planned_work` | 6     | 3 direct (`mtds_prediction_backfill_targets_wrong_data_type_scope`, `prediction_betfair_lay_price_adapter_scaffold_deleted`, `prediction_live_clob_depth_capture`) + **3 reclassified from orphan → self-dispatched** below                    |
| `orphaned_partial_coverage`     | 2     | `data_completion_prediction`, `prediction_cross_venue_arb_and_coverage` (both non-batchable)                                                                                                                                                   |
| `orphaned_never_touched`        | 2     | `predictions_ml_walk_forward_and_arb`, `prediction_capture_incident_remediation` (both non-batchable)                                                                                                                                          |
| `exclude_cross_cutting`         | 19    | 18 direct + 1 reclassified (`honest_coverage_shard_dimension_model_definitional_data`)                                                                                                                                                         |

**Total orphaned (strict bar): 4.** All 4 are `assigned_vm: NA` and their remaining open work is PURELY from the
non-batchable taxonomy → Phase 3 correctly drafts no new batch (skill's "stop iterating" condition: residual needs
direct human action, not another batch).

## Reclassified this run — NOT orphans (recorded so future runs don't over-report)

1. **`issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md`** — `planning`+`open`.
   Its one open checkbox (PREDICTION:delta_one benchmark, in the doc's `## Follow-ups`) IS its own dispatch vehicle:
   AO's `regen_backlog_from_plan.py::_parse_open_todos` scans the whole file (skips only frontmatter/code/
   strikethrough/done/non-dispatchable), NOT section-scoped to `## Todos`. → `archivable_after_planned_work`, not
   orphan.
2. **`issues/mtds_available_at_cross_asset_backfill_line_cap_remediation_2026_07_31.md`** — `planning`+`open`, its
   `-002` open todo is in `## Todos`. Self-dispatched → `archivable_after_planned_work`. (Note: `-002`'s target plan
   `mtds_available_at_cross_asset_backfill_2026_07_13.md` is now **archived complete** — the cross-plan
   `depends_on`+`gate_on_depends` sequencing it prescribes may be moot/stale; the self-dispatching AO worker that picks
   `-002` should verify before executing.)
3. **`issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`** — `planning`+`open`, its one open checkbox
   (historical backstamp for non-prediction venues, in `## Follow-ups`) is its own dispatch vehicle. Self-dispatched →
   `archivable_after_planned_work`, not orphan.
4. **`issues/honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`** — genuinely multi-AG
   (`asset_group: [cefi, defi, tradfi, prediction]`, `parent_epic: instruments_master`, repos span 5 services). Not a
   prediction-primary orphan → `exclude_cross_cutting` (its 8 open items span cefi/defi/tradfi/prediction
   honest-coverage model work; primary ownership is the cross-AG data-status/instruments family, not a single AG).

## Findings — 4 orphaned docs (all non-batchable, previously carried in the archived 08-09 parked doc)

Each of the 4 below was ALREADY carried in
`/plans/archive/2026_08/issues/ag_closeout_audit_prediction_parked_2026_08_09.md` (Findings 1/3/4 there) — this run
re-confirms them under the strict coverage bar rather than discovering them fresh. Not re-parked as new open items
(carried-finding rule: one doc at a time; the 08-09 doc is archived/resolved so a fresh durable record is warranted, but
the content is cross-referenced not duplicated).

### Finding 1 — `data_completion_prediction_2026_07_15.md` (orphaned_partial_coverage; too-large-or-risky / operator-gated)

18 open checkboxes; the manifest-VALUE-relabeling slice is covered (via `prediction_phase_ab_residuals_2026_07_24.md`
Phase B, NA-not-yet-dispatched), but the CQG-bundle OBJECT-LAYER migration (live-writer bundle change + historical
rollup script + drain/VM-walk/`--apply` + post-verify + legacy-object delete), the G1 full-corpus walk → E5 rebuild →
legacy DELETE, the downstream C-walks, and GAP-4 are claimed by NO dispatched covering todo. **Non-batchable**: 6 audit
passes (batch1/2/3/4/6 + this) independently re-triage it to "0 AO-eligible, needs its own dedicated design/scoping
plan". Recommendation (unchanged from 08-09 Finding 1): operator authors that dedicated Phase-B migration design plan,
or explicitly deprioritizes it — a 7th automated pass adds nothing.

### Finding 2 — `prediction_cross_venue_arb_and_coverage_2026_07_24.md` (orphaned_partial_coverage; operator-gated + infra/ci-owned)

2 open items. The fixture-pairing Finding-5 3a/3b/3c provenance check IS covered (open `[REVIEW] P3` in
`meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md`, planning+active). The **tarball-overwrite race** (a
concurrent fleet `create-code-tarballs` clobbering a fresh GCS tarball before a VM's boot-fetch) is claimed by no
dispatched todo. **Non-batchable**: an open-ended deployment-service design choice (SHA-pinned fetch vs build-lock, no
directive) — per 08-09 Finding 4, belongs to the `infra`/`ci` tranche's own sibling audit, not this tranche's to draft.

### Finding 3 — `predictions_ml_walk_forward_and_arb_2026_06_20.md` (orphaned_never_touched; time-gated)

4 open todos, all chained on the still-unchecked cross-plan `sports_master:Group E` gate (`plans/epics/sports_master.md`
line 644, re-verified unchecked live 2026-08-10). **Non-batchable**: time-gated — nothing to do until Group E clears;
re-check when `sports_master` Group E is independently touched (unchanged from 08-09 Finding 3).

### Finding 4 — `prediction_capture_incident_remediation_2026_07_06.md` (orphaned_never_touched; operator-gated)

7 unchecked `[DESCOPED-NOT-MVP 2026-07-14]` perp-repoint items (Kalshi/Polymarket PERPETUALS) behind the standing
2026-07-14 operator ruling ("not part of MVP; re-open only on an explicit announcement that access exists"). Repeated
na-eligibility audits (07-30, 08-07, 08-08, 08-09) confirm "genuinely parked, not worker-determinable today".
**Non-batchable**: operator-gated — nothing actionable until access exists. Deliberate, tracked parking, not an
accidental miss.

## Ledger

- `parked_findings` for this run: **4** (Findings 1-4 above, all orphaned docs).
- Entries written to this issue doc: **4** (Findings 1-4). **Balanced**.
- 0 new operator-decision-requiring findings beyond the carried set (all 4 already escalated in the archived 08-09 doc).
- 0 mechanical-corpus-hygiene fixes needed (no mistags found; the batch4 done-but-unarchived state is plan-reconcile's
  corpus, not an in-run fix).
- Phase 3: **not run** — 0 orphaned docs with batchable AO-eligible bounded work (all 4 orphaned docs are purely
  non-batchable). No `prediction_satellite_ao_dispatch_batch11` drafted. Batch10 remains the live dispatch surface;
  batch8 finalize's archive todo is the nearest in-flight housekeeping.

## Progress Log

- **2026-08-10** — Sharded `/ag-closeout-audit prediction` run (slot 25, dispatch agt-c11349, `$TRANCHE=prediction`).
  Phase 0: candidate-gen 34 members / 13 covering docs; covering-plan open-todo profile captured (closeout 0, phase A-E
  17 total, batch4 0/done-unarchived, batch6 2, batch7 1, batch8 0, finalizes 7 total). Orthogonality HARD CHECK clean.
  Phase 1: 34-agent Workflow, 0 errors, every doc read end-to-end incl. dated RE-TRIAGE/Progress-Log tails; strict
  dispatched-`## Todos` coverage bar. Phase 2: reconciled 8 naive orphans → **4 true orphans** (3 reclassified
  self-dispatched `planning`+`open`, 1 genuinely multi-AG) — all 4 non-batchable. Prior 08-10 "0 orphans" conclusion
  (slot 24, linkage-signal-based) corrected: the linkage checker counts body-mentions as coverage; the strict bar does
  not, which is why 4 NA docs surface here. Phase 3: no new batch (0 batchable candidates). Ledger balanced 4==4.
