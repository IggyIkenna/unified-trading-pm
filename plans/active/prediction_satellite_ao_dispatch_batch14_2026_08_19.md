---
doc_type: plan
title: prediction satellite AO dispatch batch 14 — 2026-08-19
summary: >-
  Extraction batch from the prediction tranche's 2026-08-19 /ag-closeout-audit full sweep (17-doc Phase 1
  classification via Workflow, 0 errors) — 4 conflict-cleared, bounded, UNGATED items pulled from 2 source docs
  (prediction_phase_ab_residuals_2026_07_24.md items 2/3, data_completion_prediction_2026_07_15.md's GAP-4, and
  prediction_cross_venue_arb_and_coverage_2026_07_24.md's tarball-race item). Each todo cites its exact source doc;
  source docs are NOT touched by this batch (checkbox reconciliation happens in the paired finalize plan). Sibling
  plan `prediction_satellite_ao_dispatch_batch15_2026_08_19.md` holds the 3 items that ARE conflict-clear but gated
  on `prediction_phase_ab_residuals_2026_07_24`/`prediction_phase_d_formal_smoke_and_backfill_2026_07_24` reaching 0
  open todos — kept in a SEPARATE plan (not prose-gated inline here) per today's batch11 fix
  (`depends_on`+`gate_on_depends:true` machine-holds it; prose-only gating already wasted 2 workers' round-trips on
  batch11 before that fix landed). Conflict-checked against every active planning doc under `parent_epic:
  predictions_master`, the tranche's consolidated closeout, and every existing prediction satellite batch (1-13,
  incl. today's own batch6/11/12/13 + finalizes) before drafting — zero of the 8 live dispatchable covering docs cite
  any of these 4 source items in their own open Todos sections (confirmed via the Phase 1 Workflow's per-doc grep).
  `status: draft` — a skill-drafted AO batch is never auto-shipped; flipping to `active` to dispatch is an operator
  decision (CLAUDE.md "Plan destination — ASK BEFORE CREATING" HARD RULE).
status: draft
nature: process
asset_group: [prediction]
stage: [data]
repos:
  [
    market-tick-data-service,
    instruments-service,
    features-service,
    strategy-service,
    market-data-processing-service,
    deployment-service,
  ]
scope: [engineer]
tags: [prediction, ao-dispatch, satellite-batch, ag-closeout-audit]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/data_completion_prediction_2026_07_15.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_satellite_ao_dispatch_batch15_2026_08_19.md,
  ]
created: "2026-08-19"
last_updated: "2026-08-19"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
gate_on_depends: false
source: >-
  ag_closeout_auditor (slot 21, dispatch agt-6a0a6b), scheduled daily /ag-closeout-audit run scoped to the
  `prediction` tranche, 2026-08-19. Phase 0 discovered 30 raw prediction-tagged AG-primary docs (script:
  generate_ag_closeout_audit_candidates.py), of which 9 are the tranche's own self-dispatched covering docs
  (consolidated closeout + batch6/11/12/13 + their finalizes, all confirmed status:active/assigned_vm:planning —
  mechanically "not orphaned," no Phase 1 agent spent on them) and 20 are genuinely cross-AG per the Phase-0.3
  orthogonality filter (dual-tagged with a peer tranche other than the blessed prediction+sports pairing). The
  remaining 17 went through a Phase 1 Workflow (one agent per doc, full end-to-end read + 8-covering-doc citation
  grep): 3 archivable_now, 2 archivable_after_planned_work, 4 orphaned_partial_coverage, 8 orphaned_never_touched.
  This batch extracts the ungated conflict-clear residual from 4 of those 12 orphaned docs; the gated residual is
  `prediction_satellite_ao_dispatch_batch15_2026_08_19.md`; everything else is recorded in this doc's own Deferred
  section below (too-large-for-a-batch-todo, time-gated behind item 1 of this same Deferred section, genuinely
  operator/credential-gated, or out-of-prediction-tranche-scope).
context_scope:
  [
    /plans/active/prediction_phase_ab_residuals_2026_07_24.md,
    /plans/active/data_completion_prediction_2026_07_15.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /codex/02-data/prediction-data-types-catalog.md,
  ]
---

# Prediction satellite AO dispatch batch 14 — 2026-08-19

## Todos

- [ ] [DATA] P0. **Backfill the fixture-match attributes (A4 columns) across historical Polymarket + Kalshi soccer
      markets.** Resolve `af_fixture_id` per market from the fixtures parquet (canonical `home_id`/`away_id` +
      `af_league_id` + `fixture_date`) OR by parsing the human-readable canonical name, stamping
      `af_fixture_match_status`. The resolver/schema/writer already shipped — this todo is the historical backfill
      EXECUTION, not new code. Honest nulls where unresolved; log a match-rate summary line per (league, day).
      Repos: market-tick-data-service, instruments-service. Source: `prediction_phase_ab_residuals_2026_07_24.md`
      item at line 429 (verbatim: "Backfill the fixture-match attributes (A4 columns) across historical Polymarket +
      Kalshi soccer"). **Done when**: a fresh manifest/parquet read shows the backfill applied across the full
      historical Polymarket+Kalshi soccer population, with the per-(league,day) match-rate summary committed to this
      todo's evidence and the source doc's own item flipped citing it.

- [ ] [DATA] P0. **Re-verify + close the `instrument_type` casing/canonicalisation gap to literal 100% for
      prediction.** The last fresh live read (2026-07-27) found 176 genuinely-malformed (non-casing) rows, not 0 —
      diagnose the writer/path producing them (candidates include the per-CID bundle-finalize path, already
      confirmed to mis-stamp on a related axis) and either ship a fix + re-verify 0 remaining, or record the
      residual as accepted with a stated reason if a live source proves un-fixable within this todo's scope. Target:
      a FRESH live manifest read shows literal 0 non-canonical `instrument_type` rows AND the deployment-ui
      data-status Distinct Values panel confirms 0 non-canonical entries for prediction (the same cross-AG 100% bar
      tradfi/cefi/sports all target). Repo: market-tick-data-service. Source:
      `prediction_phase_ab_residuals_2026_07_24.md` item at line 453 (verbatim: "Re-verify + close the
      `instrument_type` casing/canonicalisation gap to literal 100%"). **Done when**: fresh count = 0, cited with
      the read's timestamp and method, and the source doc's own item flipped citing it. No file overlap with the
      A4-backfill todo above expected (fixture-id resolution vs. instrument_type-casing writer path are distinct
      code) — verify live before running concurrently regardless, per this plan's default concurrency rule.

- [ ] [CODE] P2. **Add a v9 schema-column assertion + loud WARN-on-drift to every manifest-read consumer.** Assert
      the canonical v9 schema columns are present on manifest read across features-service, strategy-service, and
      market-data-processing-service's prediction-manifest consumers; ship a loud WARN log (not a hard failure) when
      a mixed-version/legacy-schema row is encountered, so schema drift is caught operationally instead of silently
      propagating. This is a defensive read-path addition, independent of the (deferred, see below) CQG-bundle
      migration — it does not require that migration to land first. Repos: features-service, strategy-service,
      market-data-processing-service. Source: `data_completion_prediction_2026_07_15.md` item at line 410 (GAP-4,
      verbatim: "assert v9 schema columns on manifest read across features-service/strategy-service/MDPS consumers,
      ship as loud WARN on mixed-version drift"). **Done when**: all 3 consumers assert the v9 columns on read, a
      synthetic mixed-version row triggers the WARN in a test, `quality-gates.sh` is green across all 3 repos, and
      the source doc's own item flipped citing the SHAs.

- [ ] [OPS] P2. **Scope + fix the tarball-overwrite race in the fleet code-tarball build/fetch path.** A concurrent
      fleet `create-code-tarballs` run (from a clone behind LDR) can clobber a freshly-rebuilt GCS tarball/setup
      script before a new VM's boot-fetch, so a launch in the race window gets stale code (hit repeatedly launching
      the prediction detector, 2026-06-24; unresolved since, per this item's own 2026-08-16 progress-pointer:
      "needs a scoping pass before it's cleanly AO-dispatchable"). Evaluate the 2 mitigations the source doc names —
      (a) SHA-pinned tarball fetch (`VM_*_SHA`) in the launchers for just-shipped code, or (b) a build-lock around
      `create-code-tarballs` — record a brief written tradeoff (a build-lock adds cross-fleet coordination
      complexity; SHA-pinning is simpler but requires every launcher to thread a SHA parameter through) and
      implement the one you recommend as the default. This is an ordinary internal-infra engineering choice, not an
      operator-gated business/credential/destructive decision (per `task_template.md` finding U's positive test) —
      make the call and ship it, flag the alternative you didn't pick in the commit message for visibility. Repo:
      deployment-service. Source: `prediction_cross_venue_arb_and_coverage_2026_07_24.md` item at line 174.
      **Done when**: the recommended mitigation is implemented + tested (a synthetic concurrent-tarball-build repro
      no longer clobbers a fresh build, or an equivalent unit/integration proof), `quality-gates.sh` green on
      deployment-service, and the source doc's own item flipped citing the SHA + the tradeoff recorded.

## Deferred

Every item below was considered and NOT drafted as a todo above, tagged by why (per
`cursor-configs/skills/ag-closeout-audit/SKILL.md`'s non-batchable taxonomy):

- **Too-large-or-risky-for-a-batch-todo (recurring — 5th+ decline, see note).** The Phase-B CQG-bundle object-layer
  migration (`data_completion_prediction_2026_07_15.md` items at lines 319-338, same underlying migration as
  `prediction_phase_ab_residuals_2026_07_24.md`'s line-379 item's remaining CQG-bundle-normalization/
  `--remove-stragglers`/base_asset-dedupe residual): coordinated live-writer code change across MTDS+UAC+MDPS, a
  historical rollup migration script, a pre-migration drain+VM walk+apply, a post-verify CF-audit, and a
  content-verified delete of superseded objects. `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s own
  Deferred section already recorded this as "un-started and uncovered... needs a dedicated design/scoping plan," and
  batch1/2/3/4 each independently re-triaged it to 0 AO-eligible before that. **This is now a 5th consecutive
  decline across 5 separate audit passes spanning 2026-07-25→2026-08-19.** Per this skill's own carried-finding
  rule ("if a finding survives 3 re-confirmations, stop re-confirming and escalate it"), this is flagged here as a
  genuine operator/planning-attention item: the migration needs a dedicated scoping plan authored directly (not
  another satellite-batch re-triage), or an explicit operator ruling that it stays deferred indefinitely.
- **Time-gated on the item above.** `data_completion_prediction_2026_07_15.md`'s Per-AG Phase-0/G1-full-corpus
  dry-run walk (line 370), the downstream-C-walks umbrella (line 378), and the 4 individual MDPS/features/strategy/
  execution C-walks + post-walk CF audit (lines 431-447) all explicitly sequence AFTER the CQG-bundle migration
  above lands or at least starts. Not independently actionable until then.
- **Time-gated on the same migration.** `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`'s 2 remaining
  3x-cadence mid-migration smoke-test top-up reps (data-pipeline-check-is/mtds, lines 159/171) and its MVP backfill
  readiness gate (line 189) need the migration to be mid-flight or complete respectively before they mean anything.
- **Operator-gated, genuine (destructive-write carve-out) — already correctly NA, no action needed.**
  `prediction_batch4_deferred_residuals_2026_08_16.md` todo 1 (38,020-row out-of-lifecycle POLYMARKET manifest
  `--apply` reclassification): confirmed a "permanent OPERATOR hard-stop... reserved for human execution forever"
  by the archived `prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md` ruling and re-confirmed KEEP-NA
  by 3 separate na-eligibility-audit passes since. Correctly excluded from this batch.
- **Operator-gated, genuine (credential carve-out) — already tracked, just retagged this run.**
  `prediction_betfair_lay_price_adapter_scaffold_deleted_2026_08_09.md` todo 4 (live-verify Betfair back+lay):
  blocked on Betfair's `ACCOUNT_PENDING_PASSWORD_CHANGE` account state, needing the operator/account-holder to reset
  the password via Betfair's portal + update the GSM `betfair-password` secret. Already tracked via
  `prediction_satellite_ao_dispatch_batch6_2026_07_29.md`'s open `[INFRA]` todo, which this same audit run retagged
  `[BLOCKED-CREDENTIALS][INFRA]` in-place (mechanical hygiene fix, applied directly per the skill's own HARD rule —
  not parked here).
- **Inert / no action owed today.** `data_completion_prediction_2026_07_15.md`'s `grain_for_instrument_type` HOLD
  finding (line 132) explicitly states "not owed now" — a conditional note, not a live todo.
- **Out-of-prediction-tranche-scope (genuinely cross-AG, not re-drafted here).**
  `mdps_fleet_duplicate_relaunch_explosion_2026_08_15.md`'s possible `[OPERATOR]` mistag (lines 395-397) and
  `mtds_pipeline_e2e_check_driver_vm_oom_full_mvp_sweep_2026_08_14.md`'s unconfirmed DEFI-VM terminal status are
  both real findings from `plan_reconciler_findings_prediction_2026_08_16.md`, but both source docs carry
  `asset_group` tags spanning 5-6 tranches (defi/cefi/tradfi/sports/prediction[/cross-cutting]) — genuinely
  cross-AG, owned by whichever tranche's own audit claims them (ao/cross-cutting), not re-drafted into a
  prediction-exclusive batch.
- **Tooling/skill-owner judgment, not prediction-specific.**
  `plan_reconciler_findings_prediction_2026_08_18.md`'s systemic `last_updated` frontmatter-staleness finding (the
  context-scout/na-eligibility-audit/plan_reconciler skills edit doc bodies but never bump `last_updated`) needs a
  skill-owner decision on whether/how to change that shared behavior — out of this tranche's scope to resolve
  unilaterally.
- **Verified this run: already correctly covered, not a real duplication risk.**
  `plan_reconciler_findings_prediction_2026_08_16.md` flagged `prediction_satellite_ao_dispatch_batch11_2026_08_13.md`'s
  2 todos as possibly duplicating `prediction_phase_d_formal_smoke_and_backfill_2026_07_24.md`'s P0 todos. This
  run's Phase 1 pass on phase_d independently confirmed this is the INTENDED extraction relationship, not a risk:
  batch11's 2 open todos are explicitly Source-cited to phase_d's items 1/2 and cover exactly that content, no more
  no less. No action needed; flagging the concern as resolved-by-verification.
- **Likely already resolved — flagged for the citing doc's next touch, not fixed here (outside this run's
  grace-checked target).** `plan_reconciler_findings_prediction_2026_08_16.md`'s open item asking for "a fresh
  live-code re-check" of `prediction_live_clob_depth_capture_2026_07_24.md:470`'s event-time-keying checkbox: this
  run's own Phase 1 pass on that doc independently re-verified (full 934-line read + dual-mode grep) 0 open
  checkboxes, matching that doc's own same-day (2026-08-19) na-eligibility-audit self-certification — which
  postdates and appears to supersede the 08-16 concern. Not re-verified as a fresh "live-code" check in the sense
  the 08-16 finding meant (that would mean re-reading the actual event-time-keying source code, not just the doc);
  flagging for whoever next touches `plan_reconciler_findings_prediction_2026_08_16.md` to close or re-scope.

## Progress Log

- **2026-08-19 (ag_closeout_auditor, prediction tranche, dispatch agt-6a0a6b)**: drafted from the tranche's full
  Phase 0-2 audit (17 docs classified via Workflow, 0 errors) + Phase 3 conflict-check (grepped all 8 live
  dispatchable covering docs for each candidate's basename — zero hits on any of the 4 items above). Same run
  applied 4 mechanical hygiene fixes directly to `prediction_satellite_ao_dispatch_batch6_2026_07_29.md` (Betfair
  tag retag + line-1-completeness reorder + 2 stale-text corrections) per the skill's in-run-fix HARD rule, and
  flipped the corresponding findings in `plan_reconciler_findings_predictions_master_2026_08_19.md` (+ the 2 stale
  duplicate copies in the `_08_16`/`_08_18` findings docs) to `[x]` citing the fix.
