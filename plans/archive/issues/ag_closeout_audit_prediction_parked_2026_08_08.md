---
doc_type: issue
title: >-
  Prediction tranche closeout-audit findings (2026-08-08) — 1 genuine orphan found and batched (batch8); 12 carryover
  re-confirmed exclude_cross_cutting
summary: >-
  Filed by the scheduled `/ag-closeout-audit prediction` run 2026-08-08 (Phases 0-3, dispatch agt-15e876). Live re-run
  of `generate_ag_closeout_audit_candidates.py --tranche prediction --json` found `total_members=38` (was 41 on
  2026-08-07 — net corpus shrink, 3 docs archived/resolved in the interim, including
  `candle_feature_canonical_path_divergence_2026_07_20.md` which had sat `never_cited` since 07-31) and
  `never_cited_count=13` (was 13 — same headline count, but composition shifted: 1 carryover dropped off via archival, 1
  new candidate appeared). 12 of the 13 are carryover basenames already confirmed `exclude_cross_cutting` by prior
  rounds (11 unchanged since 07-31, re-verified via cheap frontmatter check this run; 1 —
  `ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md` — unchanged since 08-04/08-06,
  also re-verified). The 13th, and only genuinely fresh candidate —
  `issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md` (filed 2026-08-07 by a concurrent
  na-eligibility-audit pass) — was classified by an independent Phase-1 agent. That agent's own first-pass verdict was
  `exclude_cross_cutting` (reasoning: the fix is generic doc-hygiene mechanics, not prediction-domain work); this run
  overrode that to `orphaned_never_touched` because the doc carries only the single `asset_group: [prediction]` tag —
  unlike the 12 legitimate cross-cutting exclusions (all tagged with 4-6 real AG markers, so excluding them from
  prediction's own batch still leaves them visible to several OTHER tranches' audits), excluding a singly-tagged doc
  here would make it invisible to every tranche's candidate discovery permanently, which is exactly the invisible-orphan
  failure class the skill's own Orthogonality HARD CHECK exists to prevent (the under-tag flavor of the same bug the
  HARD CHECK's documented examples describe as a dual-tag/mistag flavor). Conflict-checked clean against all 11 covering
  plans plus the one adjacent doc that name-drops it. Extracted into a new single-todo AO-dispatch batch
  (`prediction_satellite_ao_dispatch_batch8_2026_08_08.md`, `status: draft`) + gated finalize pair. parked_findings
  ledger: 0 findings needed operator escalation this run == 0 `BLOCKED-OPERATOR-DECISION` entries in this doc (the
  classification override above was resolvable from the skill's own stated design intent, not a genuine two-sided
  judgment call).
status: resolved
nature: issue
asset_group: [prediction]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [prediction, ag-closeout-audit, orphan-audit, plan-hygiene]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/ag_closeout_audit_prediction_parked_2026_08_07.md,
    /plans/archive/2026_08/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md,
    /plans/active/prediction_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/prediction_satellite_ao_dispatch_batch8_2026_08_08_finalize.md,
    /plans/active/issues/ag_closeout_linkage_baseline_regression_87_vs_69_2026_08_06.md,
  ]
created: "2026-08-08"
author: ag_closeout_auditor
parent_epic: predictions_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.05
assigned_role: data_engineering
drift_direction: none
depends_on: []
resolved_by:
  "2026-08-08 (slot 4, ag_closeout_auditor, dispatch agt-15e876) — same-run resolution, no operator escalation needed;
  the 1 genuine orphan was extracted into batch8 (draft), not left parked"
locked_by:
locked_since:
source:
  [
    "Scheduled /ag-closeout-audit prediction run 2026-08-08 (ag_closeout_auditor, slot 4, dispatch agt-15e876), Phases
    0-3 (a real independent-agent classification of the 1 genuinely-fresh candidate, plus a frontmatter re-verification
    of the 12 already-confirmed cross-cutting docs, plus Phase 3 conflict-check + batch drafting). Operator was not
    interactively present during the run; the one judgment call this run made (the classification override) was
    resolvable from the skill's own documented design intent, so nothing needed operator escalation.",
  ]
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /scripts/plan-hygiene/generate_ag_closeout_audit_candidates.py,
  ]
---

# Prediction closeout-audit findings, 2026-08-08

> **Context.** Audit record of today's `/ag-closeout-audit prediction` pass. Written per the skill's "parked findings
> always get a durable issue doc" rule, matching every prior day's practice in this tranche (07-31, 08-04, 08-06, 08-07)
> — this time the record also documents the one genuine orphan this run found and batched.

## Headline result

Of 38 prediction-primary candidates (`generate_ag_closeout_audit_candidates.py --tranche prediction --json`), 25 are
`cited_somewhere` (covered by an active/self-dispatched plan) and 13 are `never_cited`. **Exactly 1 genuinely-orphaned
prediction-primary doc found — batched into `prediction_satellite_ao_dispatch_batch8_2026_08_08.md` (draft, awaiting
operator approval).** The other 12 never-cited candidates all classify `exclude_cross_cutting`.

- **12 re-confirmed `exclude_cross_cutting` (cheap re-verification, not a full re-read)** — 11 basenames unchanged since
  07-31 minus `candle_feature_canonical_path_divergence_2026_07_20.md` (now archived, dropped off the list) plus
  `ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md` (unchanged since 08-04/08-06).
  Each already independently confirmed cross-cutting via 2+ full Phase-1 Workflow passes in prior rounds. Re-verified
  this run via direct frontmatter re-check (`asset_group` array + `status`): all 12 still carry 4-6 real `asset_group`
  markers spanning multiple/all 5 AGs, all still `status: open`/`active`, matching the 08-07 snapshot byte-for-byte.
  Basenames: `ag_closeout_audit_rollout_2026_07_25.md`,
  `adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md`,
  `backfill_smoke_write_path_canonical_audit_2026_07_20.md`, `estate_orphan_assessment_2026_07_21.md`,
  `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`,
  `instruments_docs_audit_outstanding_items_2026_07_08.md`, `instruments_remaining_work_audit_2026_07_10.md`,
  `mdps_features_deadcode_consolidation_2026_07_20.md`,
  `ml_training_and_prediction_pipeline_launchers_stale_post_consolidation_2026_08_04.md`,
  `mtds_is_full_adapter_smoketest_findings_2026_07_07.md`,
  `mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md`,
  `uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`. Full per-doc reasoning history:
  `plans/archive/issues/ag_closeout_audit_prediction_parked_2026_08_07.md` + the 07-31/08-04/08-06 parked docs it cites.
- **1 freshly classified `orphaned_never_touched`, extracted into batch8** —
  [`issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md`](/plans/archive/2026_08/issues/prediction_cross_venue_arb_line_cap_blocks_marker_2026_08_07.md),
  created 2026-08-07 by a concurrent na-eligibility-audit pass (postdates the 08-06 audit's own candidate snapshot).
  Independent Phase-1 agent found: `asset_group: [prediction]` (single tag, no peer-AG marker),
  `parent_epic: predictions_master`, `assigned_vm: NA`. Its one open todo (extract a closed Progress Log section from
  `prediction_cross_venue_arb_and_coverage_2026_07_24.md` to clear the 1000-line hard cap it sits at) is uncited in all
  11 covering plans — confirmed by grepping the issue doc's own basename (0 hits) and the target doc's basename (6 hits,
  all about unrelated substantive prediction-domain todos, never the line-cap fix). One adjacent doc
  (`context_scope_backfill_line_cap_and_locked_doc_gap_2026_08_03.md`, itself `asset_group: [meta]`,
  `parent_epic: agent_operating_framework_master`) name-drops it but explicitly defers execution ("needs an
  operator/committer to execute it") rather than claiming it — confirmed no conflict. **Classification override,
  documented for the audit trail**: the classifying agent's own first-pass verdict was `exclude_cross_cutting`, reasoned
  from doc SUBSTANCE (generic markdown-surgery mechanics, not prediction-domain content) rather than doc TAGS. This run
  overrode to `orphaned_never_touched` — the skill's Orthogonality HARD CHECK exists to prevent an invisible-orphan
  class, and the deciding variable for that failure class is TAG VISIBILITY, not mechanism-genericness: the 12
  legitimate exclusions above all carry enough peer-AG tags to remain visible to (and correctly handled by) at least one
  other tranche's own audit even when prediction excludes them; this doc carries only `[prediction]`, so excluding it
  here would have made it invisible to literally every tranche's candidate discovery, forever. Full reasoning in
  `prediction_satellite_ao_dispatch_batch8_2026_08_08.md`'s own "Findings surfaced during extraction" section. No
  operator escalation needed — resolvable from the skill's own stated design intent.

**Corpus delta vs 2026-08-07**: `total_members` 41→38 (net shrink — 3 docs archived/resolved in the interim).
`never_cited_count` 13→13 (unchanged headline, but composition shifted: 1 carryover —
`candle_feature_canonical_path_ divergence_2026_07_20.md` — archived off the list; 1 new candidate — the
line-cap-blocks-marker doc — appeared and was this run's one genuine orphan).

**parked_findings ledger**: 0 findings needed operator escalation this run == 0 `BLOCKED-OPERATOR-DECISION` entries in
this doc. Balanced. The one judgment call this run made (the classification override above) was resolved in-run per the
skill's own documented design intent, not parked as an open question.

## Standing residuals (unchanged, cited for continuity — all non-batchable by the skill's taxonomy)

These are NOT new findings this run; they are the tranche's known standing residuals, all durably parked in prior docs,
re-confirmed unchanged today:

- **2 operator-gated dead-code docs** (07-31 parked doc Finding 1):
  `is_polymarket_dead_fixture_cross_reference_2026_07_31.md` and
  `mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md` — each 1 open todo, `assigned_vm: NA`, the (A)
  delete vs (B) keep-and-document call remains unruled by the operator. Non-batchable (operator-gated).
- **`data_completion_prediction_2026_07_15.md` Phase-B OBJECT-layer CQG-bundle migration** — un-started, uncovered,
  re-triaged "needs its own dedicated plan" by five prior batch rounds; too-large-or-risky for a batch todo.
- **`prediction_trades_migration_concurrent_dispatch_2026_07_28.md`** — ao-tranche-owned dispatch/checkpoint design
  decision; the `ao` tranche's closeout owns it, not re-drafted here.
- **5 sports-primary docs** ([sports, prediction] dual-tag, content sports-owned) — sports tranche owns; not re-drafted
  here.
- **`mtds_prediction_backfill_targets_wrong_data_type_scope_2026_08_02.md`** — covered via batch7's single dispatched
  todo (operator-approved 2026-08-06); batch7_finalize tracks reconciliation + archival, still open (2 todos).

## Live dispatch surface (covered-and-dispatched, updated)

- `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` — 0 open todos (work complete); finalize open on 1 gated
  `[DATA] P3` archival todo.
- `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` — 3 open todos (Betfair two-sided odds, Kalshi credential
  reshape + live paper-order verify, canonical-groups backfill ~24 groups); finalize 3 open (reconcile 9 source docs,
  re-check deferred population, archive).
- `prediction_satellite_ao_dispatch_batch7_2026_08_04.md` — 1 open todo (available_at consumer check), operator-
  approved 2026-08-06; finalize 2 open.
- **`prediction_satellite_ao_dispatch_batch8_2026_08_08.md` — NEW this run, 1 open todo (line-cap Progress-Log
  extraction), `status: draft` awaiting operator approval; finalize 2 open, gated.**

## Phase 3 outcome

Conflict-check step run over the 13 classified candidates: 1 orphaned prediction-primary doc found, conflict-cleared
against all 11 covering plans plus its one adjacent name-dropping doc ⇒ extracted into `batch8` (draft). No genuine
conflict surfaced ⇒ nothing parked as `BLOCKED-OPERATOR-DECISION`.

## Progress Log

- 2026-08-08 (slot 4, ag_closeout_auditor, dispatch agt-15e876): scheduled `/ag-closeout-audit prediction` run. Phase 0:
  `generate_ag_closeout_audit_candidates.py --tranche prediction --json` → 38 members / 13 never-cited (12 carryover + 1
  new; 1 prior carryover archived off the list — confirmed via `find`). Orthogonality HARD CHECK
  (prediction+cross-cutting pairing) re-checked clean — no single-AG+cross-cutting mistags found this run. Phase 1:
  cheap frontmatter re-verification of the 12 carryover candidates (tags + status unchanged vs the 08-07 snapshot) + one
  independent-agent classification (general-purpose Agent, foreground) of the 1 fresh candidate — verdict overridden
  from the agent's own `exclude_cross_cutting` to `orphaned_never_touched` (see Headline result above for the full
  reasoning). Phase 2: 1 orphan. Phase 3: conflict-checked clean against all 11 covering plans + 1 adjacent
  name-dropping doc; drafted `prediction_satellite_ao_dispatch_batch8_2026_08_08.md` (1 todo, `status: draft`) +
  `_finalize` (2 todos, `status: active`, gated). Both validated via `check_frontmatter_schema.py` +
  `check_todo_format.sh` before finalizing this report. parked_findings == 0 == entries written (the classification
  override was resolved in-run, not parked as an open question). `check_ag_closeout_linkage.py` cross-check pending (run
  after this doc is written — see this run's own completion evidence for the result).
