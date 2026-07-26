---
doc_type: plan
title:
  Cross-cutting consolidated close-out — data-pipeline concerns spanning IS/MTDS/features-service/data-status/
  manifest/GCS-path/UAC/UTL across all 5 asset groups
summary: >-
  New 6th "asset-group-style" umbrella (alongside cefi/defi/tradfi/prediction/sports) for data-pipeline (+ a small
  strategy/execution-determinism angle, Track 24) work that genuinely spans multiple asset groups rather than belonging
  to one. Authored 2026-07-25 from a 5-agent audit of an initial 68-doc epic-filtered candidate corpus
  (infrastructure_master's data-relevant subset + instruments_master + mtds_mdps_master + manifest_master +
  features_and_ml_master), then extended the SAME day with a corpus-wide sweep (all `asset_group: cross-cutting` docs
  across EVERY parent_epic — 234 total) to make the AG↔topic partition genuinely total: found ~40 more genuine
  cross-cutting docs missed by the epic-filter (Tracks 16-24, mostly from `observability_master`/`deployment_and_
  user_management_master`/`orchestrator_master`/`agent_operating_framework_master`/`strategy_master`) plus 19 more real
  asset_group-tag mistags (single-AG content wrongly tagged cross-cutting, or a fork that inherited its parent
  coordinator's tag verbatim — see the ag-closeout-audit skill's Orthogonality HARD CHECK section for the full pattern +
  every fixed example). The same corpus-wide sweep also classified the REMAINDER (docs that are genuinely NOT
  asset-group-specific data-pipeline content) into 3 new sibling tranches — `ao` (agent-orchestrator, ~35 docs), `ci`
  (CI/CD, ~33 docs), `infra` (generic repo/dependency/terraform/org hygiene, ~29 docs) — so the full partition (5 AGs +
  cross-cutting + ao + ci + infra) covers the entire plans/issues corpus with zero unaccounted docs. Now organizes 24
  Tracks with a Reachability map, mirroring the structure of the 5 existing `<ag>_consolidated_closeout_*.md` docs. A
  same-day light-residual-closeout workflow executed ~12 bounded fixes + an archival sweep against named items below;
  every one of its `[IN FLIGHT 2026-07-25]` markers was then re-verified against reality on 2026-07-26 by a
  `/plan-reconcile cross-cutting` pass and replaced with the measured outcome (5 landed, 2 never started, 1 deliberately
  not-archived, 1 superseded-not-actioned), so no unresolved in-flight prose remains below. Keep doing that: re-verify a
  dated marker before trusting it.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    instruments-service,
    market-tick-data-service,
    market-data-processing-service,
    features-service,
    unified-api-contracts,
    unified-trading-library,
    deployment-service,
    deployment-api,
    deployment-ui,
    strategy-service,
    ml-service,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags:
  [
    cross-cutting,
    close-out,
    consolidation,
    data-pipeline,
    manifest,
    gcs,
    instruments-service,
    mtds,
    uac,
    utl,
    bucket-estate,
  ]
related:
  [
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /plans/active/bucket_estate_fold_design_2026_07_13.md,
    /plans/active/bucket_estate_consolidation_closeout_2026_07_24.md,
    /plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    /plans/archive/2026_07/instruments_mtds_subset_consistency_remediation_2026_06_17.md,
    /plans/active/data_pipeline_reconciliation_skill_2026_07_20.md,
    /plans/active/issues/silent_wrong_answer_bucket_resolution_class_2026_07_20.md,
    /plans/active/issues/silent_wrong_answer_audit_candidates_2026_07_20.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: 2026-07-25
last_updated: "2026-07-26"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 12.0
estimate_calibrated_ai_days: 9.6
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  5-agent parallel triage of the epic-filtered cross-cutting candidate corpus (unified-trading-pm, 2026-07-25) at
  operator request ("build the cross-cutting-AG layer in canonical form, same as the 5 existing AGs, so
  ag-closeout-audit and plan-reconcile can reconcile its orphans too"). Candidate scoping used parent_epic filtering per
  operator suggestion (5 data-relevant epics), then a manual per-doc classification pass for the mixed
  infrastructure_master subset (23 data-relevant of 60 — CI/CD/build/security/repo-hygiene docs excluded).
---

# Cross-cutting consolidated close-out

> **Purpose.** One place to see + close ALL remaining data-pipeline work that genuinely spans multiple asset groups (IS
> → MTDS → features-service → data-status UI → manifest/GCS-path → UAC → UTL). This plan **references** the source docs;
> it does not duplicate their content. Close a track by closing its source doc(s), then tick it here. Authored from a
> 5-agent parallel audit (2026-07-25) of 68 candidate docs, after fixing 7 real orthogonality mistags found during
> scoping (2 single-AG-content-tagged-cross-cutting, 1 bare-cross-cutting-mistag, 4 forks that inherited a parent
> coordinator's tag verbatim — all now correctly retagged; see `cursor-configs/skills/ag-closeout-audit/ SKILL.md`'s
> Orthogonality HARD CHECK for the full pattern).

## How this AG differs from the other 5

Unlike cefi/defi/tradfi/prediction/sports, "cross-cutting" has no single owning team/venue axis — its 68 candidate docs
are held together only by NOT being specific to one asset group. This means: (1) several Tracks below are genuinely
small, near-done, or already-closed loose ends rather than large in-flight programs; (2) the corpus contains one
genuinely enormous coordinator (`master_data_canonicalisation_migration_catalogue_2026_06_07.md`) whose own gate DAG
(G0–G5) already organizes ~8 of the 68 docs — Track 1 below is a reachability map INTO that DAG, not a duplicate of it;
(3) a few docs turned out to be near-duplicates of existing per-AG closeout content (flagged explicitly per Track, not
silently double-tracked).

## Reachability map

1. **Coordinator + gate DAG** → Track 1 (the master coordinator + G0/G1/G2/G3.5 children)
2. **Cross-cutting manifest correctness findings** → Track 2
3. **Independent infra/devops leftovers (credential-gated)** → Track 3
4. **MVP scope + manifest bug hygiene** → Track 4
5. **GCS bucket-estate structural fold (Wave-3)** → Track 5
6. **Bucket IAM / credential-gated hygiene** → Track 6 (commands already handed to the operator, see Progress Log)
7. **Instruments-service / MTDS SSOT reconciliation + foundation overlap** → Track 7
8. **Instruments↔MTDS F1-N9 + venue-onboarding split family** → Track 8
9. **WSFeedConnector + cutover-sequencing hazards + small IS hygiene** → Track 9
10. **Cross-AG features/ML pipeline + fleet monitoring/health** → Track 10
11. **Macro/econ coverage + perp funding semantics** → Track 11
12. **Silent-wrong-answer class + distinct-values census** → Track 12
13. **Reconciliation-skill follow-through + bucket split-brain/missing buckets** → Track 13
14. **Scheduled-job reliability + concurrency/OOM defects + manifest reprocessing tooling** → Track 14
15. **Test/CI hygiene + closed/retriage-only** → Track 15
16. **UAC/manifest/catalogue schema-wide audits** → Track 16 (added 2026-07-25, epic-scoping gap)
17. **pipeline_mode partition + live-pipeline hot-path decoupling** → Track 17 (added 2026-07-25)
18. **Manifest-consolidator throughput + data-feed SLA/self-healing** → Track 18 (added 2026-07-25)
19. **Data-pipeline hardening/self-monitoring family** → Track 19 (added 2026-07-25)
20. **Data-status family** → Track 20 (added 2026-07-25)
21. **Data-pipeline alert/monitoring bugs** → Track 21 (added 2026-07-25)
22. **Manifest-hygiene / phantom-capture monitor instances** → Track 22 (added 2026-07-25)
23. **Manifest schema bump: write-time MVP precompute** → Track 23 (added 2026-07-25)
24. **Strategy/execution cross-AG determinism + capability-registry** → Track 24 (added 2026-07-25, different angle —
    flag as the first extraction candidate if this doc ever needs a line-cap split)

## Track 1 — Coordinator + gate DAG (entry point) · P0

**Source**: `master_data_canonicalisation_migration_catalogue_2026_06_07.md` — a pure sequencer coordinator (executes
nothing itself). Gate board as of 2026-07-12: G0🟢 · G1🟢(dry)/🟡(real-data) · G2🟡(per-AG)/🟢(cross-cutting) · G3🟢 ·
G3.5=gate-only · **G4🟢 all 5 AGs applied** (defi/cefi/sports/prediction 2026-06-29; tradfi 2020-2026 span, 7 VMs, done
2026-07-06) · **G5🔴 no AG has started backfill-to-100%** (a real gap — G5 is gated but not tracked as executable work
anywhere in this corpus; flag to the operator whether it needs its own per-AG plan).

- Open: 1 unowned P1 finding (G1-ENUM phantom `expected_unattempted` seed for combo/chain bundles, 3 fix options given,
  no owner picked one yet); 2 self-named DEFERRED items (prediction cqg-seed → moved to `predictions_master` Phase 3;
  full-2018-history seed extension, gated on an operator index-size review).
- **G0** → `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05.md` — narrow tracker fully green (9/9);
  broader Work-units list still open: M6 capability-driven startup gate, M7 autonomous-recovery replay triggers, T+1
  batch/live reconciliation + live-TTL, M8 cadence column-wiring, 1 stale codex doc, UI reference-data regen (stale
  token), a reverted `_merge_dataframes` dedup-key fix needing a real design. **2 CICD findings + 1 sports test item
  misfiled here belong to `cicd_retire_staging_branch_2026_06_27.md`/sports — migrate, don't work in place.**
- **G1** → `is_catalogue_g1_root_audit_log_2026_07_24.md` (verbatim coordinator extract; 3 genuinely open: G1.run once
  the v9 migration below lands, G1.run-full-history + G1.run-prediction both operator-decision-gated) ← feeds from
  `instruments_store_cf_canonicalization_single_walk_2026_07_24.md` (its "Folded-in I-2" section: 7 open P0/P1 —
  C0/C-source/C-reasons/E3-E6 drain/dry-VM/rebuild/post-walk-audit — + ~12 P2/P3 cleanup items; E6 legacy-bucket delete
  is the terminal operator-gated hop).
- **G2/M-1** → `data_completion_to_100_all_ag_2026_06_21.md` (mostly historical shell, AG-specific work moved to 5
  per-AG siblings; residual: VM-launcher canon-gate check, CeFi Extended-Starknet backfill, oracle-prices launcher run
  [BLOCKED-OPERATOR pyth ack], manifest_consolidator CAST hardening, CF-2/CF-3 ~703-date gap,
  `uts-prod-cf- manifest-audit` never-succeeded (**NOT started — see Track 14**; was: "[IN FLIGHT 2026-07-25]", which
  contradicted Track 14's own "fully open, unresolved" and is not borne out by history: the owning doc
  `issues/cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md` still reads 3 open / 0 done and its last content
  commit is `unified-trading-pm@98090f60a`, 2026-07-23, a corpus-wide reference-path migration), bybit-futures delete
  [BLOCKED-OPERATOR]) → forks `data_source_provenance_enforcement_2026_07_24.md` (~17 open todos: source-column
  backfills, cefi empty/failed-path forwarding, 23 remaining MTDS handlers needing DeFi-catalog preflight, prod
  source-distribution audit, a dedup-key decision needing human sequencing) and
  `legacy_bucket_dual_write_decommission_2026_07_24.md` (prediction AG fully closed; cefi/defi/tradfi/sports all still
  open — per-AG mechanical steps once each L3 canon plan reaches green, a tarball-migration blocker, a legacy-scheduler
  migrate-vs-retire decision).
- **G3.5** → `infra_ops_residual_migration_verification_2026_07_24.md` (9 open: a non-operator-gated full sweep, a
  RESUME-runbook un-pause gated on tradfi fleet-drain, rollup Cloud Run image-lag fix, deployment-ui could-exist-vs-
  capture surfacing, local-dev flakiness, `unique_instruments` precompute, an irreversible `schema_version` re-stamp
  needing operator sign-off, 2 pointer-only items).

**Close-out criterion**: the coordinator's own registry shows 0 orphans; G0/G1/G3.5's AO-eligible items above closed or
explicitly re-deferred with a named successor; **G5's execution ownership resolved** (currently a gap — no doc in this
corpus tracks per-AG backfill-to-100%, likely needs an operator ruling on whether that's in-scope here or lives entirely
inside each AG's own consolidated closeout).

## Track 2 — Cross-cutting manifest correctness findings · P1

**Sources**: `issues/cross_cutting_manifest_canonicalisation_findings_2026_07_11.md` (prediction green; sports/
tradfi/defi relabel work confirmed stale-as-already-done; **cefi NOT adjudicated** — CF-4 blank-source 54%, CF-5 189,665
untyped reasons, Era-B 521,513 chain-rows, CF-1 string schema_version all still open; legacy-bucket delete ×4 AGs is
human-hard-stop; tradfi 13,971-row v4 tail is fleet-drain-gated) +
`issues/manifest_v6_batch3_residual_ orphaned_work_2026_07_21.md` (mostly closed; 2 items correctly
`depends_on`+`gate_on_depends`-gated on cefi's own v6 migration landing).

**⚠️ Overlap flag**: both docs are downstream of cefi's own v6/G2 tracks and may already be substantially covered by
`cefi_consolidated_closeout_2026_07_18.md`'s Track 3/Track 8 — cross-link, do not re-own; a fresh
`/ag-closeout-audit cefi` pass should confirm no double-dispatch risk before either doc's AO-eligible items are batched.

**Close-out criterion**: cefi's CF-1/CF-4/CF-5/Era-B items fixed or explicitly handed to the cefi closeout;
`manifest_v6_batch3`'s 2 gated items close once the cefi v6 migration lands.

## Track 3 — Independent infra/devops leftovers (credential-gated) · P2

**Sources**: `infra_capture_and_devops_leftovers_2026_07_06.md` (5/9 done; 4 remain, ALL credential/operator-gated —
ASTER live VM cost-freeze hold, MANTLE gas-fees RPC key, live ODDS quota + 2nd source, rate-limit-probe VM sanction)

- [`infra_capture_and_devops_leftovers_finalize_2026_07_25.md`](/plans/active/infra_capture_and_devops_leftovers_finalize_2026_07_25.md)
  (**DONE but DELIBERATELY NOT ARCHIVED — do not move this file**; was: "[IN FLIGHT 2026-07-25] … a workflow is
  re-verifying + archiving it now"). Its own single todo is `[x]` and the 2026-07-26 re-verification confirmed the
  parent's 4 blockers all still genuinely hold. **Archiving it would break a hard shared gate**: it is the parent's ONLY
  `depends_on`+`gate_on_depends: true` coverage, so removing it from `plans/active/` regresses
  `scripts/quality_gates/check_finalize_plan_coverage.py` from baseline 1 to 2 — a post-gate `exit 1` blocking every
  future `unified-trading-pm` commit (empirically verified by simulating the move; see that doc's own 🟡 banner).
  Re-attempt archival only once the parent's 4 blockers clear (archive both together) or the coverage-gate design
  changes.

**Close-out criterion**: not AO-eligible as a whole — every remaining item needs a human credential/decision; this Track
stays a pointer until the operator resolves at least one of the 4 gates.

## Track 4 — MVP scope + manifest bug hygiene · P2

**Sources**: `mvp_scope_catalogue_tagging_2026_06_08.md` (5/7 phase items + all 3 config-versioning items shipped; open:
features/strategy MVP rules+consumer [AO-eligible], models MVP taxonomy [BLOCKED-OPERATOR-DECISION], a real-data
MVP-toggle denominator re-verify [AO-eligible]) +
[manifest_consolidator_dtype_at_source_fix_2026_07_07.md](/plans/archive/2026_07/manifest_consolidator_dtype_at_source_fix_2026_07_07.md)
(**RESOLVED + ARCHIVED 2026-07-25** — was: "[IN FLIGHT 2026-07-25]"; DuckDB write-path dtype-loss bug, fix already
shipped `unified-trading-library@02fc4661`, verified live against both previously-poisoned buckets, both todos done).

**Close-out criterion**: `mvp_scope_catalogue_tagging_2026_06_08.md`'s AO-eligible residuals shipped (the
manifest-consolidator doc is fully closed, no longer a close-out blocker); the models-MVP-taxonomy item stays parked
pending an operator ruling.

## Track 5 — GCS bucket-estate structural fold (Wave-3) · P1

**Source**: `bucket_estate_fold_design_2026_07_13.md` (design doc — fully executed, all 4 domain folds ran to completion
2026-07-18/19, now pure historical reference) → `bucket_fold_ml_2026_07_17.md` (~90% done; open: delete legacy sources +
TF/yaml removal, a real unresolved **32-item TF plan drift finding** — pre-existing IAM-member/ scheduler DESTROYs
unrelated to the fold, blocking a clean `apply`, still unresolved and worth flagging to whoever owns Track 6's IAM
work), `bucket_fold_features_2026_07_17.md` (**post-cutover redeploy+verify DONE 2026-07-26**,
`unified-trading-pm@e3a1174aa` — was: "[IN FLIGHT 2026-07-25] … being run now"; the fold cutover itself is complete, 2
lower-priority items remain: a P2 IAM+lifecycle join and a P3 alias sunset),
`bucket_fold_execution_strategy_2026_07_17.md` (done 2026-07-18, byte-parity + adversarial-verify evidence),
`bucket_fold_portfolio_state_2026_07_17.md` (done; open: an operator retention-window decision — live-trading snapshots
may need longer than the default 60-day STANDARD-before-COLDLINE) → `bucket_estate_consolidation_closeout_2026_07_24.md`
(**2 of the 3 in-flight items landed 2026-07-26**, `unified-trading-pm@a9b57d752` — the 11-alias `_KIND_ALIASES`
hard-removal re-verified already-shipped and the cosmetic asset-group-parity drift cleaned up; the ml-legacy-bucket
delete stays OPEN as a prod-bucket operator hard stop [re-verified safe, deliberately not executed]; recon-bucket E2E
producer-chain stand-up stays explicitly descoped, cross-plan-deletion checkpoint stays tracking-only, 3 audit-issue
docs need re-confirm).

**Close-out criterion**: the closeout doc's remaining todos all closed or re-deferred with a named owner (count
deliberately not restated here — read the doc); the ml-fold's 32-item TF/IAM drift finding handed to Track 6; the
portfolio-state retention question ruled by the operator.

## Track 6 — Bucket IAM / credential-gated hygiene · P1 — **✅ both credential blockers cleared 2026-07-25**

**Sources**: `bucket_iam_write_protection_per_tier_2026_06_09.md` (Phase 0 done, Group A gate MET 2026-07-22; Phase 1's
bucket-enumeration blocker cleared — operator ran `gcloud storage buckets list` via personal ADC and found the Group-A
naming assumption itself was WRONG: real buckets are two-tier `-test-`/`-prd-`, not the assumed three-tier
`-dev-`/`-stg-`/`-prd-` — the per-tier SA design needs re-deriving against this before P1.1-P1.3 terraform lands, not
yet done) +
[`plans/archive/2026_07/gcs_data_access_audit_log_cost_2026_07_24.md`](/plans/archive/2026_07/gcs_data_access_audit_log_cost_2026_07_24.md)
(**DONE, archived** — operator removed the `DATA_WRITE` `auditConfigs` entry via ADC `setIamPolicy` with an explicit
`updateMask` — the API's default mask is `bindings,etag` only and would have silently no-opped on `auditConfigs`
otherwise; verified via an independent re-read) +
[`issues/datapoint_validation_results_bucket_missing_2026_07_21.md`](/plans/active/issues/datapoint_validation_results_bucket_missing_2026_07_21.md)
(~85% resolved; 3 small residual verify/hardening items, not credential-blocked, unaffected by the above).

**Close-out criterion (updated)**: `bucket_iam_write_protection_per_tier`'s Phase 1 SA design re-derived against the
real `-test-`/`-prd-` naming, then P1.1-P1.3 terraform authored + applied;
`datapoint_validation_results_bucket_missing`'s 3 residual items closed.

**Close-out criterion**: operator runs the handed-off commands; Phase 1 terraform ships once bucket names are verified;
the `DATA_WRITE` auditConfigs entry removed; `datapoint_validation_results_bucket_missing`'s 3 residual items closed
independent of the credential gate.

## Track 7 — Instruments-service / MTDS SSOT reconciliation + foundation overlap · P1

**Sources**: `issues/instruments_service_plan_reconciliation_2026_06_29.md` +
`issues/mtds_plan_reconciliation_2026_ 06_29.md` (explicit companion pair, same date/method — nearly all
C1-C9/M-C1-M-C10 verdicts resolved; real remainders: instruments-side C5 Deribit-"G1-complete"-false-claim [🔄 with
Ikenna] + C6/C7/C9 minor [⏸ awaiting Ikenna]; MTDS-side M-C7 warm-GCS-parts live-persistence sink [designed, not built,
awaiting greenlight] + M-C10 [5 consumer plans need an HC-v2 two-layer-model update]) +
`instruments_completion_tracker_2026_07_06.md` (869 lines, 8/38 checked — **checkbox count is likely STALE**: it
dispatched 6 AO plans 2026-07-06 that have since archived/ superseded, but its own Stage checkboxes were never
reconciled against that — needs a fresh reconciliation pass before trusting the 30-open count) +
`instruments_foundation_completeness_2026_06_24.md` (5/12 done; slimmed 2026-07-24 into a process-SSOT over children, 2
of which — cefi/tradfi G1→G5 execution — are **missing from this corpus's 68-doc scope**, flag for a future audit
pass) + `instruments_foundation_phase0_cross_cutting_2026_07_24.md` (2/15 done; GATE 0 not signed off — 10 open Phase-0
items, mostly AO-eligible scripts, 2 needing design judgment).

**Close-out criterion**: both reconciliation docs unlock (`locked_by: live-defi-rollout`) once their few remaining items
resolve; `instruments_completion_tracker`'s Stage checkboxes reconciled against its own archived AO children; GATE 0's
10 items land; the missing cefi/tradfi G1→G5 children get pulled into a future corpus refresh.

## Track 8 — Instruments↔MTDS F1-N9 + venue-onboarding split family · P1

**Sources**: `instruments_mtds_subset_consistency_remediation_2026_06_17.md` (**RE-VERIFIED + ARCHIVED 2026-07-26** —
parent/index, 0 todos of its own by design, trimmed 2026-07-24 to a pure `entry_point_for:` pointer to 3 children;
re-verified all 3 children are real/findable with matching todo counts, corpus-wide referrer paths fixed to point at the
correct child instead of the trimmed stub, then moved to `plans/archive/2026_07/`) → children
`instruments_mtds_consistency_remediation_residuals_2026_07_24.md` (29/43 done; open: F1 Kraken 6yr backfill verify,
F6/F7 tradfi option-encoding + defi pre-genesis check, N5r/N6r DeFi rebuild-for-real-replace, N1b cefi UNCLASSIFIED
reconcile, N8 pred label drift, an operator-gated legacy-GCS delete of 1.08M cefi objects, a research-bucket `_index`
relocation) + `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24.md` (16/38 done; open: Kalshi adapter wiring,
Extended candle-truncation hardening, dual-Extended-path consolidation, a Databento `ohlcv-1s` `BarTimeframe` gap,
fleet-wide v9-column populate for cefi/tradfi/defi, SFI/TM backfill-completion verify, sports catalogue `mvp` column
fix, gas/SFI parallelization follow-ons, a Kalshi tarball rebuild+relaunch, a UAC ratchet re-baseline). **The 3rd
sibling, `instruments_store_cf_canonicalization_single_walk_2026_07_24.md`, is already covered under Track 1's G1 entry
— no duplicate ownership, just two different reachability paths into it.**

**Close-out criterion**: both children's AO-eligible residuals (mostly bounded scripted diffs) close; the legacy-GCS
delete stays `[OPERATOR]`-gated per this workspace's delete-safety protocol.

## Track 9 — WSFeedConnector + cutover-sequencing hazards + small IS hygiene · P1 — **✅ the URGENT cutover-sequencing hazard is CLEARED (2026-07-25/26)**

**Sources**: `issues/wsfeedconnector_phase35_gap_2026_07_06.md` (16/17 done — only ICE WSFeedConnector remains,
BLOCKED-CREDENTIALS on a Databento Real-Time key; near-closeable once that key arrives) +
[`honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md`](/plans/archive/issues/honest_coverage_harness_instrument_type_case_break_on_d1_migration_2026_07_20.md)
(**✅ RESOLVED + ARCHIVED** — was: "⚠️ URGENT, [IN FLIGHT 2026-07-25] … a workflow is fixing it now, re-verify before
assuming the cutover is safe". The hazard was: the Honest-Coverage v2 harness read `instrument_type` case-sensitively,
so the already-ratified D1 UPPERCASE migration — drain-gated under the CeFi migration-cutover critical path in
`cefi_migration_cutover_and_track8_completion_2026_07_ 25.md` — would have silently cratered coverage for every migrated
AG. **The re-verification is now done, so nobody needs to re-run it**: the doc is `status: resolved`
(`resolved_by: instruments-service@867b68f6`) and archived to `plans/archive/issues/` by `unified-trading-pm@4c42f71b7`.
Both its todos are `[x]` with evidence — the Layer-1 normaliser and the cefi Layer-2 MVP read gate were already
case-robust, and the one genuinely case-sensitive site,
`instruments-service/scripts/measure_honest_coverage.py::_compute_coverage`'s `by_venue_instrument_type` /
`by_venue_instrument_type_data_type` `groupby`, now case-folds the grouping key, with regression tests
`TestInstrumentTypeCaseInsensitivity::{test_lowercase_and_uppercase_rows_merge_into_one_shard,test_uppercase_only_shard_counts_as_covered_same_as_lowercase}`.
**The CeFi cutover is no longer blocked on this item.**) +
`instrument_record_schema_completeness_ extra_forbid_2026_07_18.md` (0/6 done, fully open — get authoritative
`extra='forbid'` violation list, per-field disposition, schema/caller fixes, flip the forbid flag, codex audit) +
`mtds_retry_safe_default_audit_2026_07_14.md` (**NOT started** — was: "[IN FLIGHT 2026-07-25] … being closed now", which
never happened: the doc still reads 5 open / 0 done and its last content commit is `unified-trading-pm@98090f60a`,
2026-07-23, a corpus-wide reference-path migration. 5 small self-contained P3 residuals, genuinely still open and
AO-eligible).

**Close-out criterion**: ICE connector lands once credentialed; **the honest-coverage case-fix is VERIFIED landed
(2026-07-25, evidence above) — this Track's one hard sequencing dependency on the CeFi cutover is DISCHARGED, no
re-check needed before the cutover fires**; `instrument_record_schema_completeness`'s 6 todos closed;
`mtds_retry_safe_default`'s 5 residuals closed.

## Track 10 — Cross-AG features/ML pipeline + fleet monitoring/health · P2

**Sources (pipeline)**: `bigquery_feature_ml_compute_engine_option_2026_06_08.md` (partial — BQ-SQL/BQML/write-back
paths blocked on 3 unanswered operator "open questions" + the canonical-v9 migration landing),
`colocated_feature_ pipeline_in_memory_handoff_2026_06_21.md` (4 bounded refactors, none started),
`features_service_e2e_pipeline_test_ 2026_05_26.md` (Phases 0-5 shipped, but stuck behind a **STALE hold banner** citing
a release channel retired 2026-07-04 — the doc's own 2026-07-12 annotation flags this but never lifts it; escalate to
the operator to lift it explicitly rather than silently re-dispatching),
`mdps_features_reduced_artifact_tracker_2026_06_28.md` (coordination hub; Plan 3 —
`mvp_for_mdps_and_features_universe_uac` — was **never authored**, a real gap blocking 3 downstream plans; needs a human
UAC-universe scoping pass before it can be AO-dispatched), `mtds_file_size_refactor_2026_06_08.md` (operator-parked, do
not dispatch), `issues/features_service_coverage_and_script_canon_2026_06_10.md` (2/8 done; 3 bounded items + 2 needing
an owner design call + 1 large repo-wide sweep).

**Sources (fleet health)**: `issues/backfill_vm_slack_alert_e2e_verification_2026_06_23.md` (likely superseded by
already-shipped fixes — verify before re-dispatching), `issues/fleet_audit_triad_deferred_followups_2026_06_01.md`
(**explicit operator "let it be" — exclude from dispatch**), `issues/fleet_data_acquisition_health_2026_06_21.md`
(mostly done; small residuals: sports ODDS_API recheck, footystats 0-byte log check, a `book_snapshot` key-mismatch
fix), `issues/live_tardis_machine_and_hl_aster_s3_batch_2026_06_21.md` (mostly done; one substantial open item — run the
HL/ASTER batch launcher over the 2023→26/2024→26 ranges, 48.5k `attempted_failed` cells, code proven, backfill not yet
run), `issues/monitor_jobs_auto_repin_and_alerting_cli_wiring_2026_06_24.md` (1/4 done; 2 bounded verify/config items),
`issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` (nearly all done; 1 bounded terraform-image-sync item + 1
tradfi OOM fix blocked-on-land by a concurrent dirty-dep conflict).

**Excluded (mistag, fixed 2026-07-25)**: `issues/features_service_defi_data_loading_blockers_2026_05_29.md` — its own
`master:` field names `defi_manifest_canonicalisation_2026_06_01.md` as owner; retagged `[defi]`, route to the DeFi
closeout instead. Its 3 incidental cross-repo MDPS findings (tz-naive-vs-aware join mismatch, canonical_writer
column-order drift, filter-pushdown 150× memory overhead) are worth a one-line pointer only — verify independently
whether already superseded by the Polars-engine work in `mtds_file_size_refactor_2026_06_08.md`.

**Close-out criterion**: the e2e-test stale hold explicitly lifted or escalated (not silently re-dispatched); Plan 3
authored or re-scoped; the HL/ASTER 48.5k-cell backfill run to completion; the tradfi OOM fix lands once its dep
conflict clears; all other bounded residuals closed.

## Track 11 — Macro/econ coverage + perp funding semantics · P2

**Sources**: `issues/macro_micro_econ_data_capture_audit_2026_06_05.md` (reference/audit doc, no live dispatch-ready
todos of its own — 4 unanswered operator questions on altdata sourcing; execution lives externally in
`data_ completion_to_100_all_ag_2026_06_21.md`) + `issues/perp_funding_data_semantics_and_cadence_2026_06_16.md` (2/9
done; open: exact discrete per-settlement funding model, historical cadence tracker, Aster funding backfill run, Aster
pre-funding-genesis backfill [blocked on GAP4], Aster live book WS connector, margining reverify, and **GAP4** —
reconcile `expected_start_dates.yaml`'s trades entry, which must precede the pre-genesis backfill).

**Close-out criterion**: the 4 macro operator questions answered (execution tracked elsewhere, this stays a pointer);
GAP4 lands first, then the perp-funding items ship in dependency order.

## Track 12 — Silent-wrong-answer class + distinct-values census · P0/P1

**Sources**: `issues/silent_wrong_answer_bucket_resolution_class_2026_07_20.md` (root cause fixed + shipped, 5 confirmed
instances fixed; **both in-flight items now settled 2026-07-26**, was: "[IN FLIGHT 2026-07-25] … being closed now" — the
`aave_rate_impact` backfill RAN (`unified-trading-pm@b6ab05bd5`, data-only) and spun out a new structural-zero finding
`issues/aave_rate_impact_structural_zero_defillama_borrow_gap_2026_07_26.md`; the 23 sports-cell UAC registration was
deliberately **NOT actioned — its premise is superseded by a later operator ruling** and is left unflipped on purpose,
do not re-dispatch it as if it were pending work; a stray empty-test-bucket delete stays human-only, deferred to
`bucket_estate_consolidation_to_sub100`) + `issues/silent_wrong_answer_audit_candidates_2026_07_20.md` (a broader
10-lens follow-up spinoff, NOT duplicate of the above — 7/24 candidates survived adversarial review, 4 shipped, 2
deferred [blocked on reconciling a peer's concurrent commit], 1 needs a schema-contract decision; **one residual is a
direct deepening of the other doc's finding #1**: the bucket-NAME fix landed, but the gas-fee PATH within that bucket
still resolves nowhere — unfixed, needs a data-pipeline research answer on where gas-fee data actually lives) +
`distinct_values_noncanonical_audit_2026_07_20.md` (mostly done, PURGE worklist verified EMPTY; **census refresh DONE
2026-07-25**, `unified-trading-pm@b2b170cd6` — 175 → 45 non-canonical distinct values, plus a rollup-overwrite gotcha
filed; was: "[IN FLIGHT 2026-07-25] … running now". 2 unrelated todos remain open: reconcile every drift cluster to an
owning plan, and the MDPS `canonical_writer_shaping.py::_type_token_from_canonical_id` bug).

**Close-out criterion**: the bucket-resolution doc's residuals settled (`aave_rate_impact` ✅ run; sports-cells ✅
superseded-not-actioned; empty-test-bucket delete still operator-gated); the audit-candidates doc's 2 deferred
stash-fixes recovered, the gas-fee-data-location question answered, the schema-contract decision made; **the census
table is refreshed ✅** — what remains in `distinct_values_noncanonical_audit` is the drift-cluster reconcile + the MDPS
`_type_token_from_canonical_id` fix.

## Track 13 — Reconciliation-skill follow-through + bucket split-brain/missing buckets · P0/P1

**Sources**: `data_pipeline_reconciliation_skill_2026_07_20.md` (the `/data-pipeline-reconciliation` skill itself is
DONE — kept as a pure cross-reference, not something to close; **its last 2 plan todos CLOSED 2026-07-26**,
`unified-trading-pm@7ae64f4c2` — the candle GCS-object↔manifest disconnect filed as its own MDPS plan and the per-AG
candle audit run, outputs under `plans/audit/results/data_pipeline_reconciliation_candles_*`; was: "[IN FLIGHT
2026-07-25] … being executed now". The doc now reads **0 open / 42 done** — see the archival question in the Progress
Log) + `issues/recon_bucket_missing_nightly_recon_failing_2026_07_13.md` (the narrow bug — missing recon bucket, stale
digest — is fixed+verified; the broader goal, a real green nightly batch-live recon, needs NEW multi-repo feature work
across 4 services and is **explicitly NOT AO-eligible as-is** — needs an operator ASK for a properly-scoped new plan
first) + `issues/strategy_store_split_brain_2026_07_13.md` (bucket side resolved via the Wave-3 fold; **both remaining
reader-code legs are now VERIFIED LANDED (code read 2026-07-26)** — `deployment-api`'s `deployment_api_config.py`
`effective_strategy_store_{cefi,tradfi,defi}_bucket` all now return `resolve_bucket_name(kind="strategy-store")` (the
FLAT kind), and UAC `scripts/enumerate_envelope.py` now writes `strategy-store-prd-{project_id}` with the old per-AG
name surviving only in an explanatory comment. Was: "tracked in `bucket_fold_closeout_2026_07_17.md`, outside this
corpus" — **that tracker has since been archived** (`plans/archive/2026_07/`, folded by `unified-trading-pm@58801d799`)
and it folded only its `_KIND_ALIASES` checkbox, not these two Progress-Log loose ends, so the legs were briefly
untracked; the code read above discharges them directly. Live `gcloud storage ls` probes 2026-07-26 also confirm all 3
per-AG buckets are **404 / retired** and the flat `strategy-store-prd-*` holds the real content. **The doc still stays
OPEN for a newly-found leg**: the _per-service_ Terraform stack
`deployment-service/terraform/services/strategy-service/gcp/{terraform.tfvars:19-21,main.tf:202-204,234-236}` still
mounts the three DELETED per-AG buckets via GCSFuse — a `terraform apply` there would fail or re-create them. Captured
as a new P1 `[INFRA]` todo in that doc).

**Close-out criterion**: the reconciliation-skill's 2 todos ✅ closed; the recon-bucket doc's broader goal gets an
operator-scoped new plan (not worked in place); **the split-brain doc's ORIGINAL closure condition is MET** (both reader
legs verified in code + all 3 per-AG buckets probed 404, not re-implemented) — it now closes on its one new P1 Terraform
todo instead.

## Track 14 — Scheduled-job reliability + concurrency/OOM defects + manifest reprocessing tooling · P1/P2

**Sources**: `issues/cf_manifest_audit_scheduled_job_daily_failure_2026_07_13.md` (fully open, unresolved — the
`uts-prod-cf-manifest-audit` Cloud Run Job has never successfully produced output, failing daily since 2026-07-04;
affects all 5 AGs' daily CF-audit) + `issues/pipeline_smoke_sweep_findings_2026_07_20.md` (mostly done — 3 tooling
false-green defects fixed, a 15h CeFi outage caught + a watchdog added; residual: prediction/sports staleness
re-checks) + `issues/blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18.md` (3 of 4+ findings fixed
same-day; open: DeFi handlers have zero concurrency at any level, needs an `asyncio.gather`+`Semaphore` refactor, plus
per-site verification across ~12 DeFi handlers — not a mass edit, needs care) +
`issues/manifest_index_read_oom_ canonical_cache_2026_06_24.md` (operationally mitigated; the durable fix — bound
`_CANONICAL_CACHE` per bucket — is undone, touches the LIVE cefi/sports/tradfi manifest path, validate carefully) +
`issues/manifest_reprocessing_ generic_utility_2026_07_07.md` (fully open, 4 todos — design → implement
`select_shards_for_reprocess()` → wire as an IS CLI subcommand → optionally retire 13 near-identical one-off scripts;
concrete design already specified).

**Close-out criterion**: the CF-manifest-audit job green for all 5 AGs with cited evidence; the smoke-sweep residuals
re-verified (not re-fixed if already resolved elsewhere); the DeFi concurrency refactor shipped; the manifest-OOM bound
implemented (Option A minimum) and measured to not regress the sports warm-cache win; the generic reprocessing utility
designed+implemented+wired.

## Track 15 — Test/CI hygiene + closed/retriage-only · P2/P3

**Sources (hygiene — ✅ all 3 RESOLVED + ARCHIVED 2026-07-25, nothing left in flight)**: was "(hygiene, all [IN FLIGHT
2026-07-25])"; verified 2026-07-26 that every one of the three has landed in `plans/archive/issues/` —
[`local_storage_provider_shared_tempdir_test_state_leak_2026_07_20.md`](/plans/archive/issues/local_storage_provider_shared_tempdir_test_state_leak_2026_07_20.md)
(bind to pytest `tmp_path`; archived `unified-trading-pm@e1580ac0a`) +
[`pytest_posixpath_str_drv_attributeerror_flake_2026_07_17.md`](/plans/archive/issues/pytest_posixpath_str_drv_attributeerror_flake_2026_07_17.md)
(archived `unified-trading-pm@74df80162`) +
[`instruments_service_codex_compliance_ceiling_drift_2026_07_20.md`](/plans/archive/issues/instruments_service_codex_compliance_ceiling_drift_2026_07_20.md)
(archived `unified-trading-pm@e1580ac0a`).

**Sources (closed or needs-retriage only, no active work)**:

- [`cross_ag_never_seeded_backlog_scan_2026_07_06.md`](/plans/archive/issues/cross_ag_never_seeded_backlog_scan_2026_07_06.md)
  — **DONE + ARCHIVED** (`unified-trading-pm@b5805e7aa`, all 7 markers closed). Was self-contradictory here, reading
  both "(ARCHIVED)" and "a workflow is … archiving it now" in the same sentence; the archival is finished.
- `issues/mtds_uac_adapter_contract_baseline_regression_2026_07_09.md` — **RESOLVED-IN-PLACE 2026-07-25**: all 4
  originally-flagged files (book_microstructure_handler.py / perp_funding_handler.py / honest_coverage.py /
  source_priority.py) confirmed non-regressions (baseline already regenerated by `unified-trading-pm@ba098a7cc`,
  re-verified this pass) — `status: resolved`, all 4 todos closed, no code change needed. **Archival to
  `plans/archive/issues/` deliberately NOT done**: the doc carries `locked_by: live-defi-rollout`, and
  `quality-gates.sh`'s locked-plan-deletion gate requires an operator-approved `[unlock-plan]` commit tag to delete a
  locked file from `plans/active/` (CLAUDE.md: that tag is ask-first, never autonomous) — flagged as a named follow-up
  in the doc itself, and still awaiting that approval as of 2026-07-26.
- `issues/empty_reprobe_ disagreement_2026_06_22.md` (stale — auto-filed over a month ago, `locked_by` looks like an
  abandoned lock; likely much of its scope superseded by Track 12's audits; recommend a fresh re-probe or archive rather
  than direct dispatch).
- `issues/instruments_remaining_work_audit_2026_07_10.md` (a CeFi-consolidated-closeout-style discoverability index, now
  15 days stale relative to 2026-07-25 — several docs it indexed have since split/archived; valuable as a structural
  template for THIS doc, but needs a "historical snapshot" banner, not treated as current inventory).

**Close-out criterion**: **the hygiene items are all closed ✅ (3 archived 2026-07-25)**;
`mtds_uac_adapter_contract_baseline_regression` is resolved but its archival stays pending an operator `[unlock-plan]`
approval; `empty_reprobe_disagreement` re-triaged or archived; `instruments_remaining_work_audit` gets a
historical-snapshot banner.

## Track 16 — UAC/manifest/catalogue schema-wide audits · P1/P2

> **Added 2026-07-25** — these 8 docs are genuinely cross-cutting data-pipeline content that got epic-tagged into
> `agent_operating_framework_master`/`orchestrator_master` instead of one of the 4 epics this doc originally scoped
> from, so they were missed in the first authoring pass. Already correctly `asset_group: cross-cutting`, no retag needed
> — just folded in here for coverage.

**Sources**:
[asset_class_to_asset_group_rename_2026_07_21.md](/plans/active/asset_class_to_asset_group_rename_2026_07_21.md) (UAC
domain-level `AssetClass`→`AssetGroup` enum rename across all 5 AGs + 7 repos) ·
[issues/catalogue_census_equivalents_inventory_2026_07_24.md](/plans/active/issues/catalogue_census_equivalents_inventory_2026_07_24.md)
(manifest/catalogue distinct-values census gaps across strategy/features/fixtures/UAC registries) ·
[issues/cli_shard_split_flag_coverage_audit_2026_07_24.md](/plans/active/issues/cli_shard_split_flag_coverage_audit_2026_07_24.md)
(shard-key CLI convention coverage audit across instruments-service/MDPS/features-service) ·
[issues/coverage_percent_symmetric_inclusion_audit_2026_07_24.md](/plans/active/issues/coverage_percent_symmetric_inclusion_audit_2026_07_24.md)
(coverage-percent formula symmetric-inclusion invariant audit, honest-coverage-model) ·
[issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md](/plans/active/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md)
(UAC capability-manifest/strategy-catalogue data gaps) ·
[issues/features_service_catalogue_completeness_inventory_2026_07_24.md](/plans/active/issues/features_service_catalogue_completeness_inventory_2026_07_24.md)
(features-service catalogue completeness across all 9 modules) ·
[issues/mvp_scope_resolver_code_read_2026_07_24.md](/plans/active/issues/mvp_scope_resolver_code_read_2026_07_24.md)
(code-read of the paper/live strategy-universe resolver vs UAC `MVP_SCOPE`, across all 5 AG plans) ·
`data_pipeline_e2e_milestones_gate_2026_07_24.md` (already cited — the 14-criteria gate doc itself; kept here as a
pointer, not duplicated, since Track 1 already references its `related:` graph indirectly).

**Close-out criterion**: each audit's own open todos closed or handed to the specific AG closeout its finding lands in.

## Track 17 — pipeline_mode partition + live-pipeline hot-path decoupling · P1

**Sources**:
[pipeline_mode_partition_migration_2026_06_01.md](/plans/active/pipeline_mode_partition_migration_2026_06_01.md)
(promotes `pipeline_mode` to an on-disk hive partition across every asset group's next whole-corpus manifest walk) +
[issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md](/plans/active/issues/live_pipeline_persistence_hot_path_decoupling_2026_06_24.md)
(MTDS/MDPS live-pipeline persistence/hot-path architecture, log-spine decoupling — applies to the whole live pipeline,
not one AG).

**Close-out criterion**: the hive-partition migration lands on the next scheduled whole-corpus walk (single-walk
discipline applies — do not schedule a dedicated walk just for this); the hot-path decoupling design ships.

## Track 18 — Manifest-consolidator throughput + data-feed SLA/self-healing · P1/P2

**Sources**:
[consolidator_throughput_backlog_monitor_2026_07_09.md](/plans/active/consolidator_throughput_backlog_monitor_2026_07_09.md)
(per-AG manifest-consolidator backlog/throughput + "did the run produce its expected data" verdict; open: the v2
truthful merged-per-tick histogram, currently DESCOPED pending WS-H's structured-progress spine, + the deployments-page
split) +
[data_feed_sla_registry_and_active_self_healing_2026_06_19.md](/plans/active/data_feed_sla_registry_and_active_self_healing_2026_06_19.md)
(open: build the single declarative SLA registry consolidating scattered freshness thresholds, plus active
re-fetch-on-stale self-healing).

**Close-out criterion**: both open items ship or are explicitly re-deferred to WS-H's spine landing first.

## Track 19 — Data-pipeline hardening/self-monitoring family · P0/P1

**Sources**:
[data_pipeline_hardening_self_monitoring_2026_06_22.md](/plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md)
(the canonical anti-silent-misclassification hardening doc, explicitly "across all 5 asset groups" — an otherwise-
shipped detect→auto_recover→file_issue→page loop) + its 3 residual forks (all 2026-07-24):
[data_pipeline_ag_residual_backfill_decisions_2026_07_24.md](/plans/active/data_pipeline_ag_residual_backfill_decisions_2026_07_24.md)
(tradfi `attempted_failed` retries, a UAC image-packaging bug, tradfi `ohlcv_15s` spurious-aggregation bug, defi
DIVERGENT_EMPTY backfill-vs-scope campaign) ·
[data_pipeline_alert_substrate_residual_2026_07_24.md](/plans/active/data_pipeline_alert_substrate_residual_2026_07_24.md)
(alert-substrate/digest/writer-invariant residuals, alerting-service app-log visibility) ·
[data_pipeline_self_healing_completion_residual_2026_07_24.md](/plans/active/data_pipeline_self_healing_completion_residual_2026_07_24.md)
(Phase 6-C self-heal actuator wiring/packaging/scheduling).

**Close-out criterion**: all 3 forks' residual items closed; the parent's detect→recover→file→page loop verified live
end-to-end for all 5 AGs.

## Track 20 — Data-status family · P1

**Sources**:
[data_status_catalogue_true_source_phase2_2026_07_24.md](/plans/active/data_status_catalogue_true_source_phase2_2026_07_24.md)
(Phase-2 true-catalogue/expected-universe source via instruments-service) ·
[data_status_cell_grid_rearchitecture_2026_07_18.md](/plans/active/data_status_cell_grid_rearchitecture_2026_07_18.md)
(bound/stream/precompute cell-grid rewrite to kill a deployment-api OOM reading the whole manifest) ·
[data_status_page_ux_and_canonicalisation_2026_07_16.md](/plans/active/data_status_page_ux_and_canonicalisation_2026_07_16.md)
(honest-coverage fix + P1-P8 UX/canonicalisation: instrument-type canonicalisation, catalogue explorer, cefi chain-axis
drift, sports league-drilldown) ·
[data_status_tab_and_downloads_remediation_2026_06_16.md](/plans/active/data_status_tab_and_downloads_remediation_2026_06_16.md)
(data-status tab bugs + instruments CSV download regressions, gated on the v9 manifest migration) ·
[deployment_redesign_cherrypicks_2026_07_20.md](/plans/active/deployment_redesign_cherrypicks_2026_07_20.md)
(cherry-picks from a superseded branch: triage panel, dark-theme default, `reason_summary`/`reason_category`, mock-mode
coverage-summary, flat `capture_status` matrix endpoint — all data-status/API items).

**Close-out criterion**: all 5 docs' open P1/P2 items ship; the v9-migration gate on `_tab_and_downloads_remediation`
re-checked before dispatch (do not surface pre-migration data through the UI, per the data-pipeline-correctness rule).

## Track 21 — Data-pipeline alert/monitoring bugs · P1

**Sources**:
[issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md](/plans/active/issues/data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md)
(DP_NOT_V9/rate-limit alert false-positives tied to the manifest schema v9 migration + consolidation lag) ·
[issues/dp_event_pubsub_delivery_gap_2026_06_22.md](/plans/active/issues/dp_event_pubsub_delivery_gap_2026_06_22.md)
(DP_* events have no PubSub→subscriber→router path to `#data-pipeline-alerts`) ·
[issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md](/plans/active/issues/honest_coverage_nightly_cron_undersized_and_launcher_ssot_drift_2026_07_16.md)
(nightly cron VM undersized + launcher SSOT drift across 4 conflicting launcher artifacts → partial `coverage.json`) ·
[issues/live_mode_event_sink_topic_missing_2026_06_21.md](/plans/active/issues/live_mode_event_sink_topic_missing_2026_06_21.md)
(fleet-wide latent bug: live-mode lifecycle event sink publishes to non-existent PubSub topics, MTDS/MDPS).

**Close-out criterion**: all 4 alerting bugs fixed + verified live (the false-positive fix, the missing PubSub route,
the cron launcher-SSOT reconcile, the missing `{service_name}-events` topic creation for live-mode launches).

## Track 22 — Manifest-hygiene / phantom-capture monitor instances · P2

**Sources**: dated outputs of 2 standing cross-cutting monitors —
[issues/manifest_hygiene_red_2026_06_27.md](/plans/active/issues/manifest_hygiene_red_2026_06_27.md) (defi instance) +
[issues/manifest_hygiene_red_2026_06_29.md](/plans/active/issues/manifest_hygiene_red_2026_06_29.md) (cefi instance) —
both from `manifest_hygiene_daily.py`;
[issues/phantom_captures_prediction_2026_06_28.md](/plans/active/issues/phantom_captures_prediction_2026_06_28.md)

- [issues/phantom_captures_tradfi_2026_06_28.md](/plans/active/issues/phantom_captures_tradfi_2026_06_28.md) — both from
  the G3 phantom-manifest audit (`reconcile_phantom_manifest_rows_all.py`).

**Close-out criterion**: each candidate CSV triaged (real gap → backfill, code bug → fix adapter/writer, intentional new
venue → extend the UAC oracle); the prediction/tradfi phantom rows reconciled via `--apply` flips to `attempted_failed`.

## Track 23 — Manifest schema bump: write-time MVP precompute · P2

**Source**:
[sports_prediction_mvp_writetime_precompute_2026_07_24.md](/plans/active/sports_prediction_mvp_writetime_precompute_2026_07_24.md)
— despite the AG-sounding filename, this bumps UTL's shared `AvailabilityRecord` manifest schema (v9→v10), the ONE
dataclass written by every asset_group and every producer service — a genuine fleet-wide schema/manifest change (a
caching/perf optimization, not sports/prediction business logic), not a per-AG doc.

**Close-out criterion**: the write-time `mvp: bool` stamp added to `AvailabilityRecord`, schema bumped 9→10,
manifest-consolidator schema-evolution handling verified, historical rows backfilled.

## Track 24 — Strategy/execution cross-AG determinism + capability-registry · P1/P2

> **A different angle than Tracks 1-23** — these 10 docs are cross-cutting from a STRATEGY/EXECUTION/capability-
> registry angle (spanning multiple AGs' strategy archetypes or the paper=batch=live determinism guarantee), not a
> data-pipeline angle. Kept in this same doc (one asset_group = one consolidated closeout, matching the other 5 AGs'
> pattern) rather than forking a second competing "primary" doc — but flagged distinctly since a future split (if this
> doc nears the line-cap) should extract this Track as its own child first, being the most thematically separable.

**Sources**:
[carry_staked_basis_funding_scan_experiment_2026_06_16.md](/plans/active/carry_staked_basis_funding_scan_experiment_2026_06_16.md)

- [carry_strategy_ensemble_productionization_2026_07_24.md](/plans/active/carry_strategy_ensemble_productionization_2026_07_24.md)
- [cross_venue_funding_reversion_research_2026_07_24.md](/plans/active/cross_venue_funding_reversion_research_2026_07_24.md)
  (the carry_staked_basis family — combines DeFi LST staking with CeFi perp funding across venues; open: live/broad-
  universe coverage-completion work) ·
  [citadel_paper_batch_live_reconciliation_2026_06_19.md](/plans/active/citadel_paper_batch_live_reconciliation_2026_06_19.md)
- [issues/batch_live_reconciliation_service_audit_2026_05_27.md](/plans/active/issues/batch_live_reconciliation_service_audit_2026_05_27.md)
- [issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md](/plans/active/issues/honest_coverage_smoke_harness_4ag_verify_2026_07_06.md)
  (the paper==batch-rerun==live determinism-spine family — finishing the ε=0 proof machinery + BLRS audit remediation
- the 4-AG smoke-harness discrepancy set) ·
  [defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md](/plans/active/defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md)
- [issues/capability_wizard_analysis_findings_2026_06_11.md](/plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md)
- [issues/capability_wizard_gap_discovery_2026_06_11.md](/plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md)
  (the capability-wizard family — full-taxonomy coverage across the 53-57 archetype registry, spans DeFi/CeFi treasury
  splits + options/vol) · [v2_engine_venue_buildout_2026_06_15.md](/plans/active/v2_engine_venue_buildout_2026_06_15.md)
  (confirmed multi-AG: CeFi venues, DeFi/GMX, sports/betfair-smarkets, TradFi/CME options, prediction/ML_LEAN engines,
  one buildout).

**Close-out criterion**: the carry_staked_basis ensemble ships live coverage; the determinism-spine ε=0 proof lands

- BLRS audit items close; the capability-wizard's drift-check/gap-tracker items close across the full taxonomy;
  v2_engine_venue_buildout's per-venue items close.

## Codex SSOTs (read before touching a track)

`/codex/02-data/availability-manifest-and-data-status.md`, `…/pipeline-mode-partition.md`,
`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`, `/codex/05-infrastructure/bucket-isolation-model.md`,
`…/gcs-object-operations.md`, `/codex/02-data/honest-coverage-model.md`,
`/codex/11-project-management/doc-frontmatter-schema.md`.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

- **2026-07-26** — `/plan-reconcile cross-cutting` (autonomous, topic-scoped shard; 104 tranche docs inventoried).
  **Every `[IN FLIGHT 2026-07-25]` marker in this doc was re-verified against the filesystem + git and replaced with its
  measured outcome** — the doc's own frontmatter asked for exactly this re-check. Measured: **5 landed** (Track 5
  `bucket_fold_features` redeploy+verify `@e3a1174aa`; Track 5 `bucket_estate_consolidation_closeout` 2 of 3
  `@a9b57d752`; Track 12 census refresh `@b2b170cd6`; Track 12 `aave_rate_impact` backfill `@b6ab05bd5`; Track 13
  recon-skill's last 2 todos `@7ae64f4c2`); **1 RESOLVED+ARCHIVED** (Track 9's ⚠️ URGENT honest-coverage
  `instrument_type`-case hazard — `resolved_by: instruments-service@867b68f6`, archived `@4c42f71b7` — **the CeFi
  migration cutover is no longer blocked on it**, which the stale prose was still warning about); **3 archived hygiene
  docs** in Track 15 (`@e1580ac0a` ×2, `@74df80162`) plus `cross_ag_never_seeded_backlog_scan` (`@b5805e7aa`), whose
  entry had been self-contradictory ("(ARCHIVED)" and "archiving it now" in one sentence); **2 never started** (Track
  1's `uts-prod-cf-manifest-audit`, which also contradicted Track 14's own "fully open, unresolved"; Track 9's
  `mtds_retry_safe_default_audit`, untouched since `@98090f60a` 2026-07-23 — both were advertising work nobody did); **1
  deliberately NOT archived** (Track 3's `infra_capture_and_devops_leftovers_finalize` — archiving it regresses
  `check_finalize_plan_coverage.py` 1→2 and hard-fails PM `quality-gates.sh` for everyone; the old prose said a workflow
  was archiving it _now_); **1 superseded-not-actioned** (Track 12's 23 sports-cell UAC registration). Track 13
  side-finding, verified not assumed: `issues/strategy_store_split_brain_2026_07_13.md`'s named tracker archived without
  carrying its 4c/4d loose ends — both reader legs are in fact LANDED (deployment-api + UAC `enumerate_envelope.py` code
  reads) and all 3 per-AG buckets probe **404**, but the per-service Terraform stack still GCSFuse-mounts those deleted
  buckets; captured as a new P1 `[INFRA]` todo in that doc. **2 decisions parked** (not auto-applied) in
  `issues/autonomous_session_operator_decisions_2026_07_25.md` #10-#11: archiving the 2 fully-done-but-soft-evidenced
  docs (`data_pipeline_e2e_milestones_gate_2026_07_24.md`, `data_pipeline_reconciliation_skill_2026_07_20.md`), and the
  `[unlock-plan]` needed to archive `issues/mtds_uac_adapter_contract_baseline_regression_2026_07_09.md`.

- **2026-07-25** — Doc authored from a 5-agent parallel triage (Agent tool, not Workflow — this session's ultracode flag
  was off at triage time) of the 68-doc epic-filtered candidate corpus. Scoping itself surfaced + fixed 7 real
  orthogonality mistags (2 single-AG-tagged-cross-cutting, 1 bare-mistag, 4 fork-inherited-parent-tag — see
  `cursor-configs/skills/ag-closeout-audit/SKILL.md` for the pattern + `check_frontmatter_yaml.py`-verified fixes, all
  shipped `unified-trading-pm@a49e5a249`/`7a1df0a74`). IAM-credential-gated commands (Track 6) handed to the operator
  directly (bucket enumeration + an `auditConfigs` read-modify-write recipe), awaiting their run + report. A same-day
  Workflow (`wf_1290040b-63e`) launched immediately after authoring to close ~12 bounded residual todos named across
  Tracks 4/5/9/10/12/13/15 above + archive 3+ confirmed-fully-done docs — re-verify every `[IN FLIGHT 2026-07-25]`
  marker against that workflow's actual result before trusting this doc's prose. **This doc is `status: active` /
  `assigned_vm: NA` (LOCAL track) — per the operator's explicit 2026-07-25 gate, do NOT flip to `assigned_vm: planning`
  until they confirm they've personally run `/ag-closeout-audit` + `/plan-reconcile` for this AG (and the other 5) on
  the planning VM.**
