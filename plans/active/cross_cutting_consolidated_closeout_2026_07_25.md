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
  `/plan-reconcile cross-cutting` pass and replaced with its measured outcome, so no unresolved in-flight prose remains
  below — the per-marker breakdown is in the history companion (see below), deliberately not re-tallied here (a
  hardcoded count re-stales on the next pass). Keep doing that: re-verify a dated marker before trusting it.
  **2026-08-09 line-cap trim** (had grown to 1007 lines, over the 1000L hard cap): Tracks 14/18-22 (still-open,
  observability/self-monitoring-themed) forked verbatim to
  `cross_cutting_closeout_observability_and_monitoring_2026_08_09.md`; Track 15 (closed/retriage-only) + the full
  Progress Log through 2026-08-08 forked verbatim to `cross_cutting_consolidated_closeout_history_2026_08_09.md` — see
  the Split notice section below.
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
    /plans/archive/2026_07/bucket_estate_fold_design_2026_07_13.md,
    /plans/active/bucket_estate_consolidation_closeout_2026_07_24.md,
    /plans/active/bucket_iam_write_protection_per_tier_2026_06_09.md,
    /plans/archive/2026_07/instruments_mtds_subset_consistency_remediation_2026_06_17.md,
    /plans/active/data_pipeline_reconciliation_skill_2026_07_20.md,
    /plans/archive/issues/silent_wrong_answer_bucket_resolution_class_2026_07_20.md,
    /plans/archive/issues/silent_wrong_answer_audit_candidates_2026_07_20.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md,
    /plans/archive/2026_08/cross_cutting_consolidated_closeout_history_2026_08_09.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch4_2026_08_09.md,
    /plans/archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08.md,
    /plans/archive/2026_08/citadel_satellite_ao_dispatch_batch1_2026_08_08_finalize.md,
  ]
created: 2026-07-25
last_updated: "2026-08-09"
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
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md,
    /codex/02-data/data-pipeline-correctness-hard-rule.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/pipeline-mode-partition.md,
    /codex/02-data/honest-coverage-model.md,
  ]
depends_on:
  [cross_cutting_closeout_observability_and_monitoring_2026_08_09, citadel_satellite_ao_dispatch_batch1_2026_08_08]
gate_on_depends:
  false # tracking-only linkage (task_template.md finding I) — none of this parent's remaining Tracks
  # depend on either listed doc's open work landing first. First entry is a line-cap fork (0 open todos in its own
  # history companion, not listed separately). Second entry (added ag-closeout-audit cross-cutting 2026-08-10,
  # iterative-drain round) is a content-named satellite batch (citadel_*, not cross_cutting_*-prefixed) that
  # generate_ag_closeout_audit_candidates.py's filename-pattern discovery structurally cannot see — listing it here
  # is the documented mechanism (see that script's _covering_paths() docstring) for its depends_on:-resolution path
  # to pick it up, closing a real discoverability gap: citadel_satellite_ao_dispatch_batch1_2026_08_08.md (+its
  # finalize) already actively extracts citadel_paper_batch_live_reconciliation_2026_06_19.md's agent-shippable
  # items (14 citations in the batch body, 5 in the finalize) but was invisible to every prior audit round as a
  # covering doc for it. The history companion carries 0 open todos so it is not listed here (mirrors how tradfi's
  # history companion is related:-only, not depends_on).
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

## Split notice (2026-08-09 — plan-hygiene line-cap remediation)

> **This plan was trimmed from 1007 lines and forked 2 ways**, dispatched via
> `/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch4_2026_08_09.md` todo 2, mirroring the split pattern
> already used by `tradfi_consolidated_closeout_2026_07_18.md` / `sports_consolidated_closeout_2026_07_19.md` /
> `prediction_consolidated_closeout_2026_07_18.md`. Every Track and every Progress Log line was moved **verbatim** to
> its destination, nothing was summarized, rewritten, or dropped.
>
> | Child plan                                                                                                                                             | Carries                                                                                                                                                                             |
> | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
> | [`cross_cutting_closeout_observability_and_monitoring_2026_08_09.md`](/plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md) | Tracks 14, 18-22 — scheduled-job reliability, manifest-consolidator throughput, self-monitoring, data-status, alerting, manifest-hygiene/phantom-capture (all still genuinely open) |
> | [`cross_cutting_consolidated_closeout_history_2026_08_09.md`](/plans/archive/2026_08/cross_cutting_consolidated_closeout_history_2026_08_09.md)        | Track 15 (closed/retriage-only) + the full 2026-07-25 through 2026-08-08 Progress Log — pure historical record                                                                      |
>
> **Retained here**: Tracks 1-13, 16-17, 23 (still-open, not observability-themed), Track 24 (already a pointer stub
> since its own 2026-07-26 extraction), the Reachability map, the "Known non-orphan dispositions" section (its own text
> requires it stay here permanently — see that section), the ground-truth MVP-scope context, and the Codex SSOT index.

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
24. **Strategy/execution cross-AG determinism + capability-registry** → EXTRACTED 2026-07-26, see
    [cross_cutting_strategy_execution_determinism_2026_07_26.md](/plans/active/cross_cutting_strategy_execution_determinism_2026_07_26.md)

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

**Sources**: `infra_capture_and_devops_leftovers_2026_07_06.md` (**UPDATED 2026-08-02**: 6/9 done; 3 remain — ASTER
live-data-landing verification (freeze already lifted 2026-07-28, connector shipped; landing itself unconfirmed — see
the doc's own issue-doc pointer), the Live-ODDS second-source scaffold (no longer operator-decision-gated — the quota
decision itself cleared 2026-07-28/29 — but the api_football scaffold half is still unwired), and the rate-limit-probe
VM sanction (still genuinely operator-decision-gated). MANTLE gas-fees RPC cleared for real 2026-07-29
(`unified-api-contracts@1924bfed`, no Secret Manager grant needed after all).)

- [`infra_capture_and_devops_leftovers_finalize_2026_07_25.md`](/plans/archive/2026_08/infra_capture_and_devops_leftovers_finalize_2026_07_25.md)
  (**now archived** — the earlier "deliberately not archived" note here is stale: the doc was archived by a later
  session, and a 2026-08-11 backmerge artifact briefly resurrected a stale active-path duplicate of it, which has since
  been deleted; the archived path above is the current, correct location). Its own single todo is `[x]`; a 2026-08-02
  re-reconciliation found MANTLE (of the original 4 named `BLOCKED-*` items) has fully cleared and the Live-ODDS quota
  decision-component cleared, but 3 checkboxes remain open on the parent (ASTER data-landing verification, Live-ODDS
  second-source scaffold, rate-limit-probe VM) — parent updated with citations, archival still deferred. **Archiving it
  would break a hard shared gate**: it is the parent's ONLY `depends_on`+`gate_on_depends: true` coverage, so removing
  it from `plans/active/` regresses `scripts/quality_gates/check_finalize_plan_coverage.py` from baseline 1 to 2 — a
  post-gate `exit 1` blocking every future `unified-trading-pm` commit (empirically verified by simulating the move; see
  that doc's own 🟡 banner). Re-attempt archival only once the parent's remaining items clear (archive both together) or
  the coverage-gate design changes.

**Close-out criterion**: not AO-eligible as a whole — the remaining items each need a human credential/decision, a
scaffold shipped, or a live-data confirmation; this Track stays a pointer until all clear.

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
[`issues/datapoint_validation_results_bucket_missing_2026_07_21.md`](/plans/archive/issues/datapoint_validation_results_bucket_missing_2026_07_21.md)
(**DONE, archived 2026-07-26** — all 7 todos closed, `status: resolved`).

**Close-out criterion (updated)**: `bucket_iam_write_protection_per_tier`'s Phase 1 SA design re-derived against the
real `-test-`/`-prd-` naming, then P1.1-P1.3 terraform authored + applied;
`datapoint_validation_results_bucket_missing`'s 3 residual items closed.

**Close-out criterion**: operator runs the handed-off commands; Phase 1 terraform ships once bucket names are verified;
the `DATA_WRITE` auditConfigs entry removed; `datapoint_validation_results_bucket_missing`'s 3 residual items closed
independent of the credential gate.

## Track 7 — Instruments-service / MTDS SSOT reconciliation + foundation overlap · P1

**Sources**: `/plans/archive/issues/instruments_service_plan_reconciliation_2026_06_29.md` +
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
AO-eligible) + `instruments_service_e2e_live_mock_observability_2026_07_27.md` (added 2026-07-27, found never-cited by
the schema-expansion plan's Phase-2 verification pass — re-scoped from the never-completed Phases 5-7 of the archived
2026-03 instruments-service E2E audit: live-mode 15-min clock alignment, mock-mode failure scenarios,
observability/logging checks, all 0 done / fully open).

**Close-out criterion**: ICE connector lands once credentialed; **the honest-coverage case-fix is VERIFIED landed
(2026-07-25, evidence above) — this Track's one hard sequencing dependency on the CeFi cutover is DISCHARGED, no
re-check needed before the cutover fires**; `instrument_record_schema_completeness`'s 6 todos closed;
`mtds_retry_safe_default`'s 5 residuals closed; the E2E Phases 5-7 audit's 3 checks land.

## Track 10 — Cross-AG features/ML pipeline + fleet monitoring/health · P2

**Sources (pipeline)**: `bigquery_feature_ml_compute_engine_option_2026_06_08.md` (partial — BQ-SQL/BQML/write-back
paths blocked on 3 unanswered operator "open questions" + the canonical-v9 migration landing),
`colocated_feature_ pipeline_in_memory_handoff_2026_06_21.md` (4 bounded refactors, none started),
`features_service_e2e_pipeline_test_ 2026_05_26.md` (Phases 0-5 shipped, but stuck behind a **STALE hold banner** citing
a release channel retired 2026-07-04 — the doc's own 2026-07-12 annotation flags this but never lifts it; escalate to
the operator to lift it explicitly rather than silently re-dispatching),
`mdps_features_reduced_artifact_tracker_2026_06_28.md` (coordination hub; **CORRECTED 2026-07-27**: Plan 3 —
`mvp_for_mdps_and_features_universe_uac` — was NOT never-authored, it shipped in full and archived 2026-06-30
(`plans/archive/2026_06/mvp_for_mdps_and_features_universe_uac_2026_06_28.md`, content-verified: `mdps_mvp_universe`
uac@682cffb5, `feature_perp_representative` uac@6f0c4bf8, `execution_spot_representative` uac@6cf967c2, 5-AG test matrix
uac@6a2f6aab, consumed by features-service@48fa8377); none of Plans 2/6/9 were actually blocked on it (2 and 9 already
independently complete/active, 6 has a stable dependency contract but just isn't implemented yet) — this tracker has 0
own checkbox todos, slated for archival), `mtds_file_size_refactor_2026_06_08.md` (operator directed 2026-07-27:
**resume**, no longer parked), `issues/features_service_coverage_and_script_canon_2026_06_10.md` (2/8 done; 3 bounded
items + 2 needing an owner design call + 1 large repo-wide sweep).

**Sources (fleet health)**: `issues/backfill_vm_slack_alert_e2e_verification_2026_06_23.md` (likely superseded by
already-shipped fixes — verify before re-dispatching), `issues/fleet_audit_triad_deferred_followups_2026_06_01.md`
(**explicit operator "let it be" — exclude from dispatch**), `issues/fleet_data_acquisition_health_2026_06_21.md`
(mostly done; small residuals: sports ODDS_API recheck, footystats 0-byte log check, a `book_snapshot` key-mismatch
fix), `/plans/archive/issues/live_tardis_machine_and_hl_aster_s3_batch_2026_06_21.md` (ARCHIVED 2026-07-27, both
architecture asks shipped+proven; the backfill-over-full-ranges ask absorbed via the archived
`mvp_backfill_cefi_tick_v10_2026_06_27.md` → `cefi_completion_program_2026_07_15.md`; ongoing HL/ASTER batch-gap work
continues in `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md`),
`/plans/archive/issues/monitor_jobs_auto_repin_and_alerting_cli_wiring_2026_06_24.md` (ARCHIVED 2026-07-27, all 5/5
done), `/plans/archive/issues/dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md` (nearly all done; 1 bounded
terraform-image-sync item + 1 tradfi OOM fix blocked-on-land by a concurrent dirty-dep conflict).

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
`bucket_estate_consolidation_to_sub100`) + `/plans/archive/issues/silent_wrong_answer_audit_candidates_2026_07_20.md`
(archived 2026-07-28, a broader 10-lens follow-up spinoff, NOT duplicate of the above — 7/24 candidates survived
adversarial review, 4 shipped, **2 formerly-deferred now RECONCILED 2026-07-28** — `paired_dispatch.py` was already
shipped independently via `features-service@57f8b45d9`, `smoke_matrix.py` fixed fresh via `features-service@ab53855b` —
1 needs a schema-contract decision, tracked in
`/plans/active/issues/silent_wrong_answer_audit_untracked_followups_2026_07_28.md`; **one residual is a direct deepening
of the other doc's finding #1**: the bucket-NAME fix landed, but the gas-fee PATH within that bucket still resolves
nowhere — unfixed, but as of **2026-07-30 no longer tracked in the untracked-followups doc and no longer an open
research question**: it was split out to
`/plans/archive/issues/strategy_service_gas_fee_reader_hardcodes_1_gwei_2026_07_30.md` (`assigned_vm: planning`, P0),
which verified against current code exactly where gas-fee data lives — MTDS writes it to the SAME bucket under the
canonical `venue=ALCHEMY`/`chain=<CHAIN>`/`data_type=gas_fees` partition path, so it is a reader-prefix fix, not a
data-location unknown) + `distinct_values_noncanonical_audit_2026_07_20.md` (mostly done, PURGE worklist verified EMPTY;
**census refresh DONE 2026-07-25**, `unified-trading-pm@b2b170cd6` — 175 → 45 non-canonical distinct values, plus a
rollup-overwrite gotcha filed; was: "[IN FLIGHT 2026-07-25] … running now". 2 unrelated todos remain open: reconcile
every drift cluster to an owning plan, and the MDPS `canonical_writer_shaping.py::_type_token_from_canonical_id` bug).

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

**EXTRACTED 2026-08-09** (line-cap trim) into
[cross_cutting_closeout_observability_and_monitoring_2026_08_09.md](/plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md)
— see that doc's own Track 14 for Sources + close-out criterion.

## Track 15 — Test/CI hygiene + closed/retriage-only · P2/P3

**EXTRACTED 2026-08-09** (line-cap trim, closed-only content) into
[cross_cutting_consolidated_closeout_history_2026_08_09.md](/plans/archive/2026_08/cross_cutting_consolidated_closeout_history_2026_08_09.md)
— pure historical record, nothing left in flight; see that doc's own Track 15 for the full close-out narrative.

## Track 16 — UAC/manifest/catalogue schema-wide audits · P1/P2

> **Added 2026-07-25** — these 8 docs are genuinely cross-cutting data-pipeline content that got epic-tagged into
> `agent_operating_framework_master`/`orchestrator_master` instead of one of the 4 epics this doc originally scoped
> from, so they were missed in the first authoring pass. Already correctly `asset_group: cross-cutting`, no retag needed
> — just folded in here for coverage.

**Sources**:
[asset_class_to_asset_group_rename_2026_07_21.md](/plans/active/asset_class_to_asset_group_rename_2026_07_21.md) (UAC
domain-level `AssetClass`→`AssetGroup` enum rename across all 5 AGs + 7 repos) ·
[issues/catalogue_census_equivalents_inventory_2026_07_24.md](/plans/archive/issues/catalogue_census_equivalents_inventory_2026_07_24.md)
(manifest/catalogue distinct-values census gaps across strategy/features/fixtures/UAC registries) ·
[issues/cli_shard_split_flag_coverage_audit_2026_07_24.md](/plans/archive/issues/cli_shard_split_flag_coverage_audit_2026_07_24.md)
(shard-key CLI convention coverage audit across instruments-service/MDPS/features-service — RESOLVED 2026-07-28,
features-service@87e73cee) ·
[issues/coverage_percent_symmetric_inclusion_audit_2026_07_24.md](/plans/archive/issues/coverage_percent_symmetric_inclusion_audit_2026_07_24.md)
(coverage-percent formula symmetric-inclusion invariant audit, honest-coverage-model) ·
[/plans/archive/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md](/plans/archive/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md)
(UAC capability-manifest/strategy-catalogue data gaps) ·
[issues/features_service_catalogue_completeness_inventory_2026_07_24.md](/plans/archive/issues/features_service_catalogue_completeness_inventory_2026_07_24.md)
(features-service catalogue completeness across all 9 modules) ·
[issues/mvp_scope_resolver_code_read_2026_07_24.md](/plans/archive/issues/mvp_scope_resolver_code_read_2026_07_24.md)
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
not one AG) +
[issues/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md](/plans/archive/2026_08/mdps_features_live_launcher_exec_dispatch_never_wired_2026_07_27.md)
(added 2026-07-27, retagged out of a `[cefi, cross-cutting]` Orthogonality-HARD-CHECK mistag — the specific verification
VM happened to be a CeFi run, but the bug itself, `setup-data-pipeline-vm.sh`'s exec-dispatch never wired for a compound
`VM_SERVICE` + neither MDPS's nor features-service's CLI supporting the launcher's per-asset-group premise, is
asset-group-agnostic, applies to every AG's live launch).

**Close-out criterion**: the hive-partition migration lands on the next scheduled whole-corpus walk (single-walk
discipline applies — do not schedule a dedicated walk just for this); the hot-path decoupling design ships; the
live-launcher exec-dispatch gap gets real design work (two independent fixes needed: the compound-service run-command
branch, and a shard/family-iteration mode neither service's CLI currently supports).

## Track 18 — Manifest-consolidator throughput + data-feed SLA/self-healing · P1/P2

**EXTRACTED 2026-08-09** (line-cap trim) into
[cross_cutting_closeout_observability_and_monitoring_2026_08_09.md](/plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md)
— see that doc's own Track 18 for Sources + close-out criterion.

## Track 19 — Data-pipeline hardening/self-monitoring family · P0/P1

**EXTRACTED 2026-08-09** (line-cap trim) into
[cross_cutting_closeout_observability_and_monitoring_2026_08_09.md](/plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md)
— see that doc's own Track 19 for Sources + close-out criterion.

## Track 20 — Data-status family · P1

**EXTRACTED 2026-08-09** (line-cap trim) into
[cross_cutting_closeout_observability_and_monitoring_2026_08_09.md](/plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md)
— see that doc's own Track 20 for Sources + close-out criterion.

## Track 21 — Data-pipeline alert/monitoring bugs · P1

**EXTRACTED 2026-08-09** (line-cap trim) into
[cross_cutting_closeout_observability_and_monitoring_2026_08_09.md](/plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md)
— see that doc's own Track 21 for Sources + close-out criterion.

## Track 22 — Manifest-hygiene / phantom-capture monitor instances · P2

**EXTRACTED 2026-08-09** (line-cap trim) into
[cross_cutting_closeout_observability_and_monitoring_2026_08_09.md](/plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md)
— see that doc's own Track 22 for Sources, close-out criterion, the tradfi cross-reference, and the ownership note.

## Track 23 — Manifest schema bump: write-time MVP precompute · P2

**Source**:
[sports_prediction_mvp_writetime_precompute_2026_07_24.md](/plans/active/sports_prediction_mvp_writetime_precompute_2026_07_24.md)
— despite the AG-sounding filename, this bumps UTL's shared `AvailabilityRecord` manifest schema (v9→v10), the ONE
dataclass written by every asset_group and every producer service — a genuine fleet-wide schema/manifest change (a
caching/perf optimization, not sports/prediction business logic), not a per-AG doc.

**Close-out criterion**: the write-time `mvp: bool` stamp added to `AvailabilityRecord`, schema bumped 9→10,
manifest-consolidator schema-evolution handling verified, historical rows backfilled.

## Track 24 — Strategy/execution cross-AG determinism + capability-registry · P1/P2

**EXTRACTED 2026-07-26** (resolved `autonomous_session_operator_decisions_2026_07_25.md` entry #19, option A) into its
own child plan:
[cross_cutting_strategy_execution_determinism_2026_07_26.md](/plans/active/cross_cutting_strategy_execution_determinism_2026_07_26.md)
— ~121 open todos across 8 docs, a genuinely different (strategy/execution/capability-registry) angle from this doc's
other 23 data-pipeline Tracks, too large to drain in one closeout pass. See that doc for the Sources + close-out
criterion; it also carries the `v2_engine_venue_buildout` over-count caveat this Track's audit flagged.

## Known non-orphan dispositions (recorded here so a mechanical rescan never re-raises them)

**Why this section exists (added 2026-08-08)**: `generate_ag_closeout_audit_candidates.py`'s "never cited" signal is
citation-based — a doc is only "covered" if its basename appears somewhere in this closeout doc or a live batch/finalize
doc. A doc `exclude_cross_cutting`-verdicted (a mistag) or genuinely-cross-cutting-but-operator-gated by a `batchN`
doc's own "Not orphaned — checked, not assumed" section LOSES that coverage the moment `batchN` archives (confirmed
2026-08-08: `cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md`'s archival on/around 2026-08-07 caused 3
already-classified docs — `checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md`,
`gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`,
`strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md` — to resurface as false "never cited" candidates in the very
next day's scan). This doc never archives, so a citation recorded HERE is permanent. Each entry below is a markdown link
(not a bare backtick filename — prettier can wrap a long bare filename across a line break and silently break the
substring match both `generate_ag_closeout_audit_candidates.py` and `check_ag_closeout_linkage.py` rely on).

### Mistags awaiting owning-tranche retag (verdicted `exclude_cross_cutting` — NOT this tranche's doc to retag, per the

2026-07-30 concurrent-sharded-worker primary-owner rule; full evidence in the dated parked-findings issue doc cited per
batch)

- **ao**:
  [`checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md`](/plans/active/issues/checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md)
  (evidence: `ag_closeout_audit_cross_cutting_parked_2026_08_01.md` finding 2),
  [`ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md`](/plans/active/issues/ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md),
  [`context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`](/plans/active/context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md)
  (dual-tagged `[ao, cross-cutting]`, orthogonality mistag),
  [`slot2_wedged_pre_boot_watchdog_resume_loop_no_respawn_2026_08_04.md`](/plans/active/issues/slot2_wedged_pre_boot_watchdog_resume_loop_no_respawn_2026_08_04.md)
  — evidence for the latter 3: `ag_closeout_audit_cross_cutting_parked_2026_08_08.md`.
- **ci**:
  [`agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md`](/plans/archive/2026_08/issues/agent_orchestrator_stale_pm_workflow_ref_blocks_promotion_2026_08_06.md)
  (archived 2026-08-09, resolved),
  [`deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md`](/plans/active/issues/deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md),
  [`glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md`](/plans/archive/2026_08/issues/glue_pool_starvation_monitor_stale_jobs_after_runner_revert_2026_08_07.md),
  [`glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`](/plans/active/issues/glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md),
  [`image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md`](/plans/active/issues/image_build_validate_stranded_on_deregistered_glue_runners_2026_08_07.md),
  [`mtds_type_ignore_ratchet_blocks_prek_intel_mac_fix_2026_08_03.md`](/plans/active/issues/mtds_type_ignore_ratchet_blocks_prek_intel_mac_fix_2026_08_03.md),
  [`promote_ref_orphaned_on_manual_pr_close_2026_08_06.md`](/plans/active/issues/promote_ref_orphaned_on_manual_pr_close_2026_08_06.md),
  [`provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`](/plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md),
  [`workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md`](/plans/active/issues/workflow_template_runs_on_placeholder_prettier_mangled_fleetwide_2026_08_07.md)
  — evidence: `ag_closeout_audit_cross_cutting_parked_2026_08_07.md` findings 1/5/6, `…_2026_08_08.md` for the rest.
- **infrastructure**:
  [`autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md`](/plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md),
  [`claude_code_agent_deletes_active_canonical_migration_vm_2026_08_07.md`](/plans/active/issues/claude_code_agent_deletes_active_canonical_migration_vm_2026_08_07.md),
  [`deployment_api_events_global_state_leak_flaky_metadata_probe_2026_08_06.md`](/plans/active/issues/deployment_api_events_global_state_leak_flaky_metadata_probe_2026_08_06.md)
  (ci also defensible),
  [`deployment_service_prod_terraform_drift_2026_08_07.md`](/plans/active/issues/deployment_service_prod_terraform_drift_2026_08_07.md),
  [`gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`](/plans/active/issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md)
  (evidence: `ag_closeout_audit_cross_cutting_parked_2026_08_01.md` finding 4) — evidence for the rest:
  `ag_closeout_audit_cross_cutting_parked_2026_08_08.md`.
- **ui**:
  [`deployment_api_prod_disable_auth_true_2026_08_06.md`](/plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md)
  (⚠️ live P1 unauthenticated-prod-endpoint exposure, all 4 fix steps still open as of 2026-08-08 — 2 days stale),
  [`unified_trading_system_ui_block_list_parity_test_failing_2026_08_04.md`](/plans/active/issues/unified_trading_system_ui_block_list_parity_test_failing_2026_08_04.md)
  (very likely already resolved on `main`, needs verify-and-archive not a fresh fix) — evidence:
  `ag_closeout_audit_cross_cutting_parked_2026_08_07.md` findings 4/carry-3.
- **meta** (genuinely process-spanning, no single owning tranche):
  [`governance_sweep_deferred_followups_2026_08_06.md`](/plans/active/issues/governance_sweep_deferred_followups_2026_08_06.md).
- **Ambiguous, dual-tagged `[defi, cross-cutting]`** (real owner `ci` or `infrastructure`, needs whichever tranche's
  audit claims it first):
  [`over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md`](/plans/active/issues/over_cap_live_plan_is_permanently_unverdictable_2026_08_02.md).

### Genuinely cross-cutting, operator-gated (NOT a mistag — tracked here pending an operator ruling, not a retag)

- [`strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md`](/plans/active/issues/strategy_config_hot_reload_doc_vs_shipped_2026_07_31.md)
  — `drift_direction: needs-decision`: is `/codex/04-architecture/live-strategy-config-hot-reload.md`'s documented
  safe-field allow-list/`UnsafeConfigChangeError` the target to BUILD, or is the doc wrong and the shipped
  unconditional-swap behavior the accepted state? Unruled since 2026-07-31.

### Genuinely cross-cutting, real open work, currently uncovered (orphaned_never_touched)

- [`honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md`](/plans/active/issues/honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md)
  — `measure_honest_coverage.py --asset-group all`'s GCE VM OOM'd (root cause undetermined: organic growth / gc-loop
  leak / data-shape burst), no fix shipped, fire-and-forget launcher gap unaddressed. 3 of 4 remaining items are
  operator-gated/judgment calls; 1 (fix the stale `TASK=features-backfill` VM metadata label) is small and bounded but
  not enough alone to justify a fresh batch — held for a future batch or direct pickup.

## Todos

- [ ] [DOC] P1. **Track open items are not tracked as checkbox work in this digest** — e.g. Track 1's G5 ("no AG has
      started backfill-to-100%", gated but not tracked as executable work anywhere in this corpus) and Track 14's
      CF-manifest-audit job (`uts-prod-cf-manifest-audit` Cloud Run Job, failing daily since 2026-07-04, fully open and
      unresolved).

## Codex SSOTs (read before touching a track)

`/codex/02-data/availability-manifest-and-data-status.md`, `…/pipeline-mode-partition.md`,
`/codex/04-architecture/instruments-service-as-ssot-for-mtds.md`, `/codex/05-infrastructure/bucket-isolation-model.md`,
`…/gcs-object-operations.md`, `/codex/02-data/honest-coverage-model.md`,
`/codex/11-project-management/doc-frontmatter-schema.md`.

## Progress Log

<!-- Append newest entries at the top: `- **YYYY-MM-DD** — <what landed> (<repo>@<sha> / evidence).` -->

> **Full history through 2026-08-08 moved to**
> [`cross_cutting_consolidated_closeout_history_2026_08_09.md`](/plans/archive/2026_08/cross_cutting_consolidated_closeout_history_2026_08_09.md)
> (2026-08-09 line-cap trim) — verbatim, nothing summarized or dropped. New entries append here going forward.

- **2026-08-09** — Line-cap trim (dispatched via
  `/plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch4_2026_08_09.md` todo 2; parent had grown to 1007
  lines, over the 1000L hard cap). Forked Tracks 14/18-22 (still-open, observability/ self-monitoring-themed) verbatim
  into
  [cross_cutting_closeout_observability_and_monitoring_2026_08_09.md](/plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md);
  forked Track 15 (closed/retriage-only) + the full 2026-07-25 through 2026-08-08 Progress Log verbatim into
  [cross_cutting_consolidated_closeout_history_2026_08_09.md](/plans/archive/2026_08/cross_cutting_consolidated_closeout_history_2026_08_09.md).
  Each forked Track's header stays in place as a short pointer stub (mirroring how Track 24 was already extracted
  2026-07-26) so existing cross-references by Track number stay valid. See the "Split notice" section above.
