---
doc_type: plan
title: Prediction satellite AO batch 10 — finalize (reconcile 4 source docs + archive)
summary: >-
  Gated closeout for prediction_satellite_ao_dispatch_batch10_2026_08_09.md — machine-held via depends_on +
  gate_on_depends: true until all 4 of that plan's todos are done. Reconciles each of the 4 source docs' own checkboxes
  (prediction_live_clob_depth_capture_2026_07_24.md, prediction_capture_incident_remediation_2026_07_06.md,
  issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md,
  issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md), then archives batch10 via the standard
  6-step ritual. Authored `status: active` (not draft) per the skill's no-double-gate finding — `gate_on_depends: true`
  already machine-holds every task here until batch10's own todos are done, regardless of batch10's own draft/active
  status, so a second manual flip on this plan would be a redundant gate.
status: complete
nature: process
asset_group: [prediction]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-10, satellite-docs, archival]
related:
  [
    /plans/archive/2026_08/prediction_satellite_ao_dispatch_batch10_2026_08_09.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /plans/archive/2026_08/issues/is_polymarket_dead_fixture_cross_reference_2026_07_31.md,
    /plans/active/issues/mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-10"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/archive/2026_08/prediction_satellite_ao_dispatch_batch10_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
depends_on: [prediction_satellite_ao_dispatch_batch10_2026_08_09]
gate_on_depends: true
source: >-
  Scheduled /ag-closeout-audit prediction run 2026-08-09, per task_template.md §4's finalize-plan-coverage rule.
assigned_role: data_engineering
effort: medium
sequential: true
drift_direction: advance-code
---

# Prediction satellite AO batch 10 — finalize

> **🟢 ARCHIVED 2026-08-10 — COMPLETE.** All 5 todos done: todos 1-3 reconciled all 4 source docs' checkboxes (slot 8),
> todo 4 re-checked the 4 Deferred items with explicit still-held/cleared verdicts (slot 30), todo 5 archived batch10
> via the 6-step ritual (`status: complete` + ARCHIVED banner, `git mv` to `plans/archive/2026_08/`, all leading-slash
> referrers repointed, INDEX.md regenerated — slot 30). The gated dependency (`depends_on` + `gate_on_depends: true` on
> `prediction_satellite_ao_dispatch_batch10_2026_08_09`) is satisfied — batch10 is archived alongside. This finalize
> plan is now fully complete and archived per the plan-completion-and-archival-discipline HARD RULE.

**status: complete — batch10 archived 2026-08-10, gated dependency satisfied.**

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile `prediction_live_clob_depth_capture_2026_07_24.md`**: confirmed "DEFERRED-CROSS-DEP"
      checkbox flipped `[x]` — batch10 todo 1 SHIPPED (slot 22, 2026-08-10), live manifest rows >0 (4 dates, 648K rows),
      mtds@82ba5399/0a6ad2de, batch VM launched, live=batch architecture. Repo: unified-trading-pm.
- [x] ✅ [REVIEW] P1. **Reconcile `prediction_capture_incident_remediation_2026_07_06.md`**: confirmed Phase 6's second
      checkbox flipped `[x]` — batch10 todo 3 SHIPPED (instruments-service@d4e5c23d, 2026-08-10), 18 dates reclassified
      (162,692 instruments, 69,292→correct CQGs, 12,051 genuine OTHER), backup:
      `gs://instruments-store-pred-prd-central-element-323112/_index/backups/reclassify_kalshi_other/`. Repo:
      unified-trading-pm.
- [x] ✅ [REVIEW] P1. **Reconcile the 2 dead-code issue docs**: both confirmed `[x]` flipped. (1)
      `is_polymarket_dead_fixture_cross_reference_2026_07_31.md` — archived `status: resolved`, batch10 todo 4:
      instruments-service@4b55c57b, QG green (`.qg_last_passed_sha=4b55c57b`), verified on origin. (2)
      `mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md` — batch10 todo 5:
      market-tick-data-service@a0b4957e. Repo: unified-trading-pm.
- [x] ✅ [DOC] P2. **Re-check the 4 Deferred (not-extracted) items** from batch10's own Deferred section — in particular
      whether `data_completion_prediction_2026_07_15.md`'s Phase-B migration has finally gotten its own dedicated plan
      (now 6 audit passes deep without one), and whether `sports_master:Group E` has cleared for
      `predictions_ml_walk_forward_and_arb_2026_06_20.md`. Repo: unified-trading-pm. Done when: an explicit still-held /
      cleared verdict is recorded for each of the 4. **Verdicts: (1) STILL-HELD** — no dedicated Phase-B plan; (2)
      CLEARED — operator-ruled DELETE 2026-08-07, extracted to batch10 todos 3/4, both done; (3) STILL-HELD — Group E
      gate still unchecked; (4) STILL-HELD — infra/ci tranche scope, no infra/ci batch extracted it. Full evidence in
      the Progress Log.
- [x] ✅ [DOC] P1. **Archive `prediction_satellite_ao_dispatch_batch10_2026_08_09.md`** via the standard 6-step ritual
      (per `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`): confirm the prior 4 todos' verdicts
      are recorded, add the archived-banner cross-reference, run the post-phase codex audit, confirm no new CLAUDE.md
      contract is owed, update every corpus referrer, `git mv` to `plans/archive/2026_08/`. Repo: unified-trading-pm.
      Done when: batch10 is at its archived path with every referrer updated and this finalize plan's own todos all
      `[x]`. — **DONE 2026-08-10**: `git mv` to `plans/archive/2026_08/`, `status: complete` + ARCHIVED banner, all
      referrers repointed, INDEX.md regenerated. Full evidence in the Progress Log.

## Progress Log

- 2026-08-09 (ag_closeout_auditor, slot 14, dispatch agt-465129): drafted alongside batch10, `status: active`, gated via
  `depends_on` + `gate_on_depends: true`. No work started — waiting on the operator to approve + flip batch10 to
  `active`, then on its dispatch + completion.

- 2026-08-10 (slot 8, review, todo 1): Reconciled `prediction_live_clob_depth_capture_2026_07_24.md`'s
  DEFERRED-CROSS-DEP checkbox — confirmed `[x] ✅` flipped (line 247) with batch10 todo 1's full evidence chain: live
  manifest rows >0 (4 dates, 648K rows), shipped code fixes (mtds@82ba5399/0a6ad2de), batch VM launched, live=batch
  architecture. Verdict: reconciled, no orphaned gap. Todo 1 flipped.

- 2026-08-10 (slot 8, review, todo 2): Reconciled `prediction_capture_incident_remediation_2026_07_06.md`'s Phase 6
  second checkbox (historical Kalshi OTHER-bucket reclassify) — confirmed `[x] ✅` flipped (line 337) with batch10 todo
  3's full evidence: instruments-service@d4e5c23d, 18 dates (2026-07-12→2026-07-29), 162,692 instruments, 69,292
  reclassified to correct CQGs, 12,051 genuine OTHER (22.0% noise floor matches expected ~21%), 39 unique CQGs in window
  (was 1). Backup location for future auditability:
  `gs://instruments-store-pred-prd-central-element-323112/_index/backups/reclassify_kalshi_other/`. Verdict: reconciled,
  backup location recorded. Todo 2 flipped.

- 2026-08-10 (slot 8, review, todo 3): Reconciled both dead-code issue docs. (1)
  `is_polymarket_dead_fixture_cross_reference_2026_07_31.md` — archived `status: resolved`, sole todo `[x] ✅`, batch10
  todo 4: instruments-service@4b55c57b, QG green, verified on origin. (2)
  `mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md` — sole todo `[x] ✅`, batch10 todo 5:
  market-tick-data-service@a0b4957e. Verdict: both reconciled, no orphaned gaps. Todo 3 flipped.

- 2026-08-10 (slot 30, data_engineering, todo 4): Re-checked all 4 Deferred (not-extracted) items from batch10's
  Deferred section with fresh live reads (2026-08-10) of each source doc + the 2026-08-09 parked-findings doc + the
  sports_master epic. Verdicts recorded:
  - **(1) `data_completion_prediction_2026_07_15.md` Phase-B OBJECT-layer CQG-bundle migration — STILL-HELD.** Still no
    dedicated plan authored: grepped `plans/active/*.md` for `source:` referencing `data_completion_prediction` and for
    Phase-B/OBJECT-layer-CQG-bundle dedicated plans — zero 2026-08-09/08-10 plans are a dedicated Phase-B plan. The only
    2026-08-10 "Phase-B" hit (`cross_cutting_satellite_ao_dispatch_batch12_2026_08_10.md`) is a DIFFERENT Phase-B (CeFi
    MDPS top-up), not prediction's OBJECT-layer CQG-bundle migration. Source doc itself still `assigned_vm: NA`, 19 open
    items, headline Phase-B cluster confirmed uncovered by 6 independent audit passes (batch1/2/3/4/6 + 2026-08-09 run);
    this is the 7th confirmation. 2026-08-09 parked doc Finding 1 still recommends operator decides among (a) author the
    dedicated plan / (b) leave parked / (c) deprioritize — no decision recorded yet. Still-HELD.
  - **(2) `ag_closeout_audit_prediction_parked_2026_07_31.md` Finding 1 (operator-gated adapter dead-code judgment call)
    — CLEARED.** Its 2 linked adapter dead-code docs (`is_polymarket_dead_fixture_cross_reference_2026_07_31.md`,
    `mtds_prediction_adapters_dead_rest_polling_interface_2026_07_31.md`) were operator-ruled DELETE (option A)
    2026-08-07 and extracted to batch10 todos 3/4 — both now done (`instruments-service@4b55c57b`,
    `market-tick-data-service@a0b4957e`), reconciled by this plan's todo 3. The 07-31 Finding 1's wait-condition ("no
    action unless operator/next worker picks (A)/(B)") is satisfied. Per 2026-08-09 parked doc Finding 2, the 07-31
    doc's own `[DOC] P3` informational todo should now be flipped `[x]` — folded into THIS finalize's scope.
  - **(3) `predictions_ml_walk_forward_and_arb_2026_06_20.md` (time-gated on `sports_master:Group E`) — STILL-HELD.**
    `sports_master.md:644` `[GATE] P0` "Block predictions Group E until FSS produces ≥95% non-NULL features" is still
    UNCHECKED (live read), and `predictions_ml_walk_forward_and_arb`'s P0 `[SCRIPT]`/`[ANALYSIS]` todos are still
    `- [ ]` BLOCKED-ON that gate. External cross-tranche dependency not cleared; correctly non-dispatchable. Still-HELD.
  - **(4) `prediction_cross_venue_arb_and_coverage_2026_07_24.md` `[OPS] P2` tarball-overwrite-race — STILL-HELD
    (infra/ci tranche scope).** OPS P2 checkbox still `- [ ]`; zero infra/ci batch has extracted it (grep of
    `plans/active/*.md` for `tarball-overwrite`/`create-code-tarballs` finds no infra/ci-named plan carrying it). Per
    2026-08-09 Finding 4, correctly left to the infra/ci tranche's own audit (primary-owner rule). Sub-note: the
    fixture-pairing residual (`[DESIGN] P1`, parts 3a/3b/3c) — batch6's `[DATA] P2` team-name alias tables (3c) IS done
    (`unified-api-contracts@41c13454`, `strategy-service@217e5b0e`, 2026-08-05), but parts 3a/3b remain unverified:
    `mapped_sport_event_id`/`PredictionMarketCrossVenueMapping` are NOT populated in instruments-service (fresh grep, 0
    hits), and `instruments-service@62a8b1d8` only stamps `canonical_instrument_id` via `build_fixture_id` (3a
    registry-resolution partial), not 3b's mapping population. This is the 2026-08-09 Finding 5 verification gap —
    `prediction_cross_venue_arb_and_coverage`'s fixture-pairing RESIDUAL sub-todo stays open on 3a/3b. Both still-held.
    All 4 verdicts explicit. Todo 4 flipped.

- 2026-08-10 (slot 30, data_engineering, todo 5): Archived `prediction_satellite_ao_dispatch_batch10_2026_08_09.md` via
  the standard 6-step ritual. Steps performed:
  - Prior 4 todos' verdicts confirmed recorded (todo 1-3 in the Progress Log above + this plan's todo 4 verdicts).
  - `git mv` to `plans/archive/2026_08/prediction_satellite_ao_dispatch_batch10_2026_08_09.md`; frontmatter
    `status: active -> complete`, `last_updated: 2026-08-10`; added the `> **🟢 ARCHIVED 2026-08-10 — COMPLETE.**`
    banner with the full evidence summary (todo 1 book_snapshot_5 row-proof + mtds@82ba5399/0a6ad2de; todo 2 fallback
    fix mtds@5738858d; todo 3 Kalshi reclassify instruments-service@d4e5c23d; todo 4 is_polymarket deletion
    instruments-service@4b55c57b; todo 5 MTDS dead-REST deletion market-tick-data-service@a0b4957e), replacing the stale
    "Status: draft" dispatch banner.
  - Codex-alignment check (step 3): no new codex contract owed — the batch shipped launcher-VM-prefix + reclassify
    mechanics that resolve under existing codex entries; the 4 Deferred items' verdicts live in the parked-findings doc
    (not a new codex contract). No CLAUDE.md change owed (step 4).
  - Referrer sweep (step 5): repointed every leading-slash reference to batch10's old active path
    (`/plans/active/prediction_satellite_ao_dispatch_batch10_2026_08_09.md`) to its archive home
    (`/plans/archive/2026_08/prediction_satellite_ao_dispatch_batch10_2026_08_09.md`) in 6 files
    (`prediction_satellite_ao_dispatch_batch10_2026_08_09_finalize.md`,
    `prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md`,
    `prediction_live_clob_depth_capture_2026_07_24.md`, `prediction_phase_ab_residuals_2026_07_24.md`,
    `ag_closeout_audit_prediction_parked_2026_08_09.md`, `is_polymarket_dead_fixture_cross_reference_2026_07_31.md`);
    regenerated `plans/active/INDEX.md` (`regenerate_active_plan_index.py`) so batch10's own row dropped from the active
    index (its `_finalize` twin stays — still active until this plan's own archival). Epic `../active/...` relative
    links left per the batch9-archival precedent (archived batch4/6 refs remain there too; not leading-slash path-form).
  - Lock: none (`locked_by:` empty) — cleared/confirmed.
  - `run_hygiene_sweep.sh --precommit` green on the staged set. Done when met: batch10 at archived path, every
    leading-slash referrer updated, this plan's own todos now all `[x]` (todo 5 flipped). Todo 5 flipped.

## Deferred work — migrated to:

- N/A — the `DEFERRED-CROSS-DEP` token above (todo 1) is a citation of
  `prediction_live_clob_depth_capture_2026_07_24.md`'s own deferred checkbox, not a deferral owned by this doc; this
  plan's own todo tracks reconciling that item, not deferring further work. See that doc's own Deferred section for the
  live tracking.
