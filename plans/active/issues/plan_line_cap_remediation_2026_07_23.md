---
doc_type: issue
title: Plan line-cap remediation — triage of the 30 plans blocking the quality-gates.sh hard-fail rollout
summary: >-
  The operator ruled that quality-gates.sh should hard-fail on plan line-count caps (500 soft-warn / 1000 hard-fail;
  umbrella trackers get a 2000-line hard cap instead of no cap). `check_line_caps.sh` currently flags 30 plans in
  plans/active/ over the 1000L hard cap (several already over the 2000L umbrella ceiling too). This doc classifies each
  of the 30 into one of four buckets -- (a) stale-not-moved, (b) genuinely-umbrella-just-unmarked, (c) needs a real
  split, (d) unclear/operator call -- with a concrete proposed action per plan. TRIAGE ONLY: no plan was edited, moved,
  split, or archived while producing this doc. Bucket (b) came back EMPTY: every flagged plan either has substantive
  inline work (disqualifying it from a pure index/hub read) or is already over the 2000L ceiling where umbrella-flagging
  alone cannot help. 14 of 30 are bucket (d) because locked_by=live-defi-rollout is set -- CLAUDE.md/PLAN_FORMAT.md
  require an operator "[unlock-plan]" grant before any of those can be touched.
status: open
nature: issue
asset_group: [cross-cutting, meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-hygiene, line-cap, triage, plan-split, archival, quality-gates]
related:
  [
    task_template,
    PLAN_FORMAT,
    sports_manifest_canonicalisation_2026_06_01,
    sports_p2_history_apifootball_2015_to_present_2026_06_27,
    sports_consolidated_closeout_2026_07_19,
  ]
created: "2026-07-23"
priority: P1
parent_epic: agent_operating_framework_master
source: >-
  Operator request 2026-07-23: quality-gates.sh line-cap hard-fail rollout is blocked because 30 plans in plans/active/
  already exceed today's un-enforced caps. Triage requested via `bash scripts/plan-hygiene/check_line_caps.sh`,
  classified against plans/active/task_template.md §4 and plans/PLAN_FORMAT.md's umbrella/locking rules before any split
  is executed.
execution_scope: local-only
drift_direction: correct-codex
depends_on: []
locked_by:
locked_since:
assigned_vm: NA
resolved_by:
---

# Plan line-cap remediation — 30-plan triage

> **STOP — this is a proposal, not an execution log.** Nothing in plans/active/ or plans/archive/ was touched to produce
> this doc. Per the operator's instructions, execution is gated on review of this table, especially the bucket (c)
> splits and the bucket (d) operator asks below.

## How this was produced

30 plans came back from `bash scripts/plan-hygiene/check_line_caps.sh` as HARD (over the 1000L cap, or over the 2000L
umbrella ceiling). Each was read in full — frontmatter plus body — by an independent agent, classified per the bucket
rubric in `plans/active/task_template.md` §4 and `plans/PLAN_FORMAT.md`'s locking/umbrella rules. **Quality note**: 2 of
the first 30 agent runs (`data_pipeline_hardening_self_monitoring_2026_06_22.md` and
`migration_verification_orphan_safety_2026_06_10.md`) returned literal placeholder/stub text ("Test short reasoning")
instead of real analysis — caught on review, both were re-run independently and produced full analysis; their real
results are reflected below.

**Scope note**: the 30 plans below are exactly the HARD-flagged set. `tradfi_massive_dual_source_2026_05_28.md` is
_also_ `status: superseded` sitting in `plans/active/` (a 3rd stale-not-moved case) but it's only 527 lines (SOFT tier,
not HARD) — outside this triage's 30-plan scope, flagged here as a bonus finding for a future hygiene pass, not actioned
in this doc.

## Bucket definitions (condensed — full text in the per-agent prompts)

- **(a) STALE-NOT-MOVED**: `status` is superseded/resolved/complete/cancelled but still in `plans/active/`. Archival
  mechanics only — `git mv` to `plans/archive/2026_07/<same-filename>` (archived plans keep their original name, per
  actual archive contents).
- **(b) GENUINELY-UMBRELLA, JUST UNMARKED**: legitimate hub/index doc, 1000-2000L, not yet `umbrella: true`. Fix =
  frontmatter flag only. **Cannot apply to anything over 2000L** (2026-07-23 ruling: the ceiling is real, not waivable).
- **(c) NEEDS A REAL SPLIT**: bloated with completed/historical content or independent workstreams jammed together.
  Concrete child-plan slugs proposed below, with split type (clean-partition / depends_on-gated / sequential-chain /
  draft-gated-phase-chain).
- **(d) UNCLEAR / OPERATOR CALL**: `locked_by` is set (needs `[unlock-plan]` first — CLAUDE.md hard rule), or the split
  boundary is a genuine judgment call. Where (d) is lock-driven, the agent still analyzed what bucket it WOULD be and
  what split it WOULD propose once unlocked, so the operator has a ready answer either way.

## Bucket counts

| Bucket                     | Count  | Meaning                                                                                                                            |
| -------------------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------- |
| (a) stale-not-moved        | 2      | Pure archival-mechanics gap                                                                                                        |
| (b) umbrella-just-unmarked | **0**  | None of the 30 qualify — see note below                                                                                            |
| (c) needs a real split     | 14     | Concrete child plans proposed, no lock blocking execution                                                                          |
| (d) operator call          | 14     | 14/14 are locked_by=live-defi-rollout; 13 of those would be (c) if unlocked, 1 has a second orthogonal judgment call even unlocked |
| **Total**                  | **30** |                                                                                                                                    |

**Why bucket (b) is empty**: every plan that reads hub-like at a glance is either (i) over the 2000L ceiling already (so
the ceiling itself disqualifies it — `citadel_paper_batch_live_reconciliation`, `data_completion_to_100_all_ag`,
`data_pipeline_hardening_self_monitoring`, `instruments_mtds_subset_consistency_remediation`,
`master_data_canonicalisation_migration_catalogue` [already has `umbrella: true` set and is STILL over the cap],
`master_to_live_defi`, `sports_manifest_canonicalisation`), or (ii) contains substantial actual inline work rather than
merely indexing child plans (`sports_master_closeout` — despite carrying `entry_point_for:`,
`monitoring_control_plane_master`, `mtds_data_status_page_parity`, etc.). The 2000L ceiling being a hard wall now (not
an exemption) is doing real work here — it correctly forces splits on trackers that used to just get waved through.

---

## Full classification table

| #   | Plan                                                             |     Lines |             Todos | Locked            | Bucket | Proposed action (condensed)                                                                                                                                                                                                            |
| --- | ---------------------------------------------------------------- | --------: | ----------------: | ----------------- | :----: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `bucket_estate_consolidation_to_sub100_2026_07_13.md`            |      2129 |      21 (15 done) | —                 | **c**  | Fork 6 open mop-up todos → `bucket_estate_consolidation_closeout_2026_07_23.md`; archive parent (history intact)                                                                                                                       |
| 2   | `capability_wizard_and_manifest_2026_06_11.md`                   |      1092 |      67 (65 done) | live-defi-rollout | **d**  | Ask unlock; would-be (a) — 2 residuals, mostly ready to archive                                                                                                                                                                        |
| 3   | `carry_staked_basis_funding_scan_experiment_2026_06_16.md`       |      1426 |                54 | live-defi-rollout | **d**  | Ask unlock; would-be (c) — 3-way clean split (carry harness / cross-venue reversion research / ensemble productionization)                                                                                                             |
| 4   | `cefi_consolidated_closeout_2026_07_18.md`                       |      2059 |                27 | —                 | **c**  | Extract 1566-line Progress Log → `cefi_4surface_migration_execution_log_2026_07_18.md`; trim parent to coordination index                                                                                                              |
| 5   | `citadel_paper_batch_live_reconciliation_2026_06_19.md`          |      2660 |               123 | live-defi-rollout | **d**  | Ask unlock; would-be (c) — extract alpha-research + paper-POC track (plan's OWN text already proposed this, never executed) → `crypto_alpha_research_2026_06_23.md`                                                                    |
| 6   | `data_completion_to_100_all_ag_2026_06_21.md`                    |      4153 |    224 (164 done) | live-defi-rollout | **d**  | Ask unlock + 2 judgment calls; would-be (c) — 2 still-inline folded sections (from an already-superseded 2026-06-01 batch) → `legacy_bucket_dual_write_decommission_2026_07_23.md`, `data_source_provenance_enforcement_2026_07_23.md` |
| 7   | `data_pipeline_alerts_batch_remediation_2026_07_15.md`           |      1075 |      18 (14 done) | —                 | **c**  | Extract closed history → `data_pipeline_alerts_batch_remediation_closeout_2026_07_16.md`; trim parent to 2 genuinely-open todos                                                                                                        |
| 8   | `data_pipeline_check_mdps_features_2026_07_20.md`                |      1299 |                34 | —                 | **c**  | Extract the discovered 8-phase candle-canonical-path migration epic → `candle_canonical_path_migration_execution_2026_07_21.md` (depends_on-gated from parent's backfill todo)                                                         |
| 9   | `data_pipeline_hardening_self_monitoring_2026_06_22.md`          |      2545 |     120 (91 done) | live-defi-rollout | **d**  | Ask unlock; would-be (c) — 4-way split (alert substrate / self-healing completion / AG backfill decisions / live-VM-outage check) + excise 1 mis-filed terraform-drift item entirely                                                   |
| 10  | `data_status_page_ux_and_canonicalisation_2026_07_16.md`         |      2133 |      67 (62 done) | —                 | **c**  | 2 disjoint open workstreams → `data_status_catalogue_true_source_phase2_2026_07_23.md`, `sports_fixtures_browser_single_catalogue_source_2026_07_23.md`                                                                                |
| 11  | `defi_consolidated_closeout_2026_07_18.md`                       |      3252 |                48 | —                 | **c**  | Extract Strategy/PnL index + 1800-line historical log → `defi_strategy_pnl_axis_index_2026_07_23.md`, `defi_consolidated_closeout_history_2026_07_18.md`                                                                               |
| 12  | `distinct_values_noncanonical_audit_2026_07_20.md`               |      1627 |                21 | —                 | **c**  | 2 disjoint open workstreams → `market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_23.md`, `instruments_service_restaking_ship_and_availability_index_restamp_2026_07_23.md`                                   |
| 13  | `github_actions_ci_cost_reduction_2026_07_15.md`                 |      2094 |                42 | —                 | **c**  | 3-way split: completed migration (archive-bound) / operator-gated followups / new same-day Phase-6 staging-shutdown                                                                                                                    |
| 14  | `instruments_foundation_completeness_2026_06_24.md`              |      1617 |                50 | live-defi-rollout | **d**  | Ask unlock + ruling on internal sign-off tensions (GATE 0/G1 never recorded); would-be (c) — 4-way split (Phase-0 cross-cutting / cefi gates / tradfi gates / slim umbrella)                                                           |
| 15  | `instruments_mtds_subset_consistency_remediation_2026_06_17.md`  |      2168 |               114 | live-defi-rollout | **d**  | Ask unlock; would-be (c) — 3-way split (CF single-walk lineage / core F1-N9 residuals / venue+ops hardening residuals)                                                                                                                 |
| 16  | `master_data_canonicalisation_migration_catalogue_2026_06_07.md` |      2360 |                69 | live-defi-rollout | **d**  | Ask unlock; would-be (c) — de-dupe a verbatim-repeated ~105-line block + extract 2 AG-specific audit logs, already has `umbrella: true` but still over cap                                                                             |
| 17  | `master_to_live_defi_2026_05_23.md`                              |      2272 | 157 (168/172=98%) | live-defi-rollout | **d**  | Ask unlock + a bigger call: 98% done, target date 2 months past — recommend closing whole vs. 4-way split                                                                                                                              |
| 18  | `migration_verification_orphan_safety_2026_06_10.md`             |      1379 |                47 | live-defi-rollout | **d**  | Ask unlock; would-be (c) — durable rules already migrated to codex (V7); archive history + 4 small residual children                                                                                                                   |
| 19  | `monitoring_control_plane_master_2026_06_10.md`                  |      1019 |      71 (70 done) | live-defi-rollout | **d**  | Ask unlock; would-be (c) — split CI-dashboard tail from an unrelated orchestrator-e2e-hardening scope-creep section                                                                                                                    |
| 20  | `mtds_data_status_page_parity_2026_07_21.md`                     |      1068 |      18 (17 done) | —                 | **c**  | Extract sole open todo → `sports_prediction_mvp_writetime_precompute_2026_07_23.md`; archive parent                                                                                                                                    |
| 21  | `mvp_backfill_defi_onchain_v10_2026_06_27.md`                    |      4993 |      12 (11 done) | live-defi-rollout | **d**  | Ask unlock; would-be (c) — pure hygiene split, no todo/gate changes: extract 4500-line operational log verbatim, keep active plan as-is otherwise                                                                                      |
| 22  | `prediction_consolidated_closeout_2026_07_18.md`                 |      1478 |                31 | —                 | **c**  | 4-way split along the plan's own Phase A-E boundaries (one depends_on-gated: Phase E gated on B+D)                                                                                                                                     |
| 23  | `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`       |      2354 |                85 | live-defi-rollout | **d**  | Ask unlock; would-be (c) — 3-way split (parked crypto-perps / live CLOB-depth capture / cross-venue arb+coverage)                                                                                                                      |
| 24  | `sports_legacy_bucket_cutover_2026_07_16.md`                     |      2847 |      49 (45 done) | —                 | **c**  | 2 disjoint open items → `sports_mtds_odds_trades_index_correctness_followup_2026_07_23.md`, `sports_legacy_cutover_closeout_tasks_2026_07_23.md`                                                                                       |
| 25  | `sports_manifest_canonicalisation_2026_06_01.md`                 |      4733 |    123 (119 done) | live-defi-rollout | **a**  | `status: superseded`, banner confirms fold-in verified bidirectionally — `git mv` to archive, needs unlock first                                                                                                                       |
| 26  | `sports_master_closeout_2026_07_21.md`                           |      1120 |                21 | —                 | **c**  | Extract 6-wave, 440-line Progress Log → `sports_master_closeout_progress_log_2026_07_21.md`; fix an exact-duplicate section too                                                                                                        |
| 27  | `sports_p2_features_history_to_ml_ready_2026_06_27.md`           |      4343 |        6 (5 done) | live-defi-rollout | **d**  | Ask unlock + a 2nd orthogonal call (overlap with sports_consolidated_closeout's Track C1/F, plan's own banner says don't resolve unilaterally)                                                                                         |
| 28  | `sports_p2_history_apifootball_2015_to_present_2026_06_27.md`    |      3900 |      17 (13 done) | —                 | **a**  | `status: superseded`, banner + migration confirmed, no lock — plain `git mv` to archive                                                                                                                                                |
| 29  | `tradfi_consolidated_closeout_2026_07_18.md`                     | 2378→2469 |                50 | —                 | **c**  | 3-way split (manifest/content completion / backfill-throughput / Phase-D terminal gate); parent can take `umbrella: true` once trimmed under 2000L                                                                                     |
| 30  | `tradfi_v9_stage1_finish_2026_07_06.md`                          |      1440 |      13 (11 done) | —                 | **c**  | Extract operator-gated legacy-twin-delete signoff; fold 1 item into `tradfi_consolidated_closeout_2026_07_18.md` (merge, not new file)                                                                                                 |

---

## Bucket (a) — stale-not-moved (2 plans)

Both already carry `status: superseded` + `superseded_by: sports_consolidated_closeout_2026_07_19.md`, with a banner in
the body confirming the fold-in and listing exactly which residual items were carried forward. Neither needs a content
split — the classification is clean. **Both need an operator ask before the `git mv` can happen**, but for different
reasons:

- **`sports_manifest_canonicalisation_2026_06_01.md`** (4733L) — `locked_by: live-defi-rollout` is still set, so the
  archive move needs `[unlock-plan]` per PLAN_FORMAT.md's locking rule, in addition to the routine archival commit.
- **`sports_p2_history_apifootball_2015_to_present_2026_06_27.md`** (3900L) — `locked_by` is empty, so this one can move
  with a plain `docs(plans):` commit, no unlock needed, as soon as the operator green-lights execution.

**Proposed action for both** (pending go-ahead): `git mv plans/active/<file> plans/archive/2026_07/<same file name>` —
zero content edits, since each file's own banner already documents the supersession.

---

## Bucket (c) — needs a real split (14 plans, no lock blocking execution)

These can be split as soon as the operator approves the boundaries below — no `[unlock-plan]` is required for any of
them (none carry `locked_by`). Every split proposed is a **clean partition** (independent files/repos, no
`depends_on`/`sequential` needed) except two which have an internal gate, called out explicitly.

| Parent                                                   | Proposed children                                                                                                                                                                                                                    | Split type                                                                                                                                               |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `bucket_estate_consolidation_to_sub100_2026_07_13.md`    | `bucket_estate_consolidation_closeout_2026_07_23.md` (6 todos: recon-bucket closeout, cross-plan deletion checkpoint, ml legacy variants, `_KIND_ALIASES` removal, asset-group-parity drift, 3 audit issue-doc closures)             | clean-partition                                                                                                                                          |
| `cefi_consolidated_closeout_2026_07_18.md`               | `cefi_4surface_migration_execution_log_2026_07_18.md` (the entire 1566-line Progress Log, still actively updated — KRAKEN-SPOT apply attempt-3 in flight as of 2026-07-23)                                                           | clean-partition                                                                                                                                          |
| `data_pipeline_alerts_batch_remediation_2026_07_15.md`   | `data_pipeline_alerts_batch_remediation_closeout_2026_07_16.md` (historical narrative, archive-bound); parent trimmed to 4 items (2 stale-checkbox flips + 2 real opens)                                                             | clean-partition                                                                                                                                          |
| `data_pipeline_check_mdps_features_2026_07_20.md`        | `candle_canonical_path_migration_execution_2026_07_21.md` (16 todos: the 8-phase candle-canonical-path migration the parent's own text calls "an EPIC, not a cheap migration")                                                       | **depends_on-gated** — parent's backfill-execution todo gets `depends_on: [candle_canonical_path_migration_execution_2026_07_21], gate_on_depends: true` |
| `data_status_page_ux_and_canonicalisation_2026_07_16.md` | `data_status_catalogue_true_source_phase2_2026_07_23.md` (4 todos), `sports_fixtures_browser_single_catalogue_source_2026_07_23.md` (3 todos) — file-disjoint (deployment-api catalogue route vs fixtures_browser.py+UI)             | clean-partition                                                                                                                                          |
| `defi_consolidated_closeout_2026_07_18.md`               | `defi_strategy_pnl_axis_index_2026_07_23.md` (3-todo index pointer), `defi_consolidated_closeout_history_2026_07_18.md` (archive-bound, 1800L history + the 95%-closed 75-finding audit)                                             | clean-partition                                                                                                                                          |
| `distinct_values_noncanonical_audit_2026_07_20.md`       | `market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_23.md` (5 todos), `instruments_service_restaking_ship_and_availability_index_restamp_2026_07_23.md` (4 todos)                                           | clean-partition                                                                                                                                          |
| `github_actions_ci_cost_reduction_2026_07_15.md`         | `github_actions_self_hosted_runner_migration_2026_07_15.md` (0 todos, archive-bound), `github_actions_operator_gated_followups_2026_07_17.md` (8 todos), `github_actions_staging_machinery_shutdown_2026_07_23.md` (3 todos)         | clean-partition                                                                                                                                          |
| `mtds_data_status_page_parity_2026_07_21.md`             | `sports_prediction_mvp_writetime_precompute_2026_07_23.md` (5 todos — schema-version-bump work deliberately deferred); parent then archives                                                                                          | clean-partition                                                                                                                                          |
| `prediction_consolidated_closeout_2026_07_18.md`         | `prediction_phase_c_data_status_ui_2026_07_23.md` (4), `prediction_phase_ab_residuals_2026_07_23.md` (7), `prediction_phase_d_formal_smoke_and_backfill_2026_07_23.md` (3), `prediction_phase_e_football_arb_live_2026_07_23.md` (4) | **depends_on-gated** — Phase E child depends on Phase B+D children per the parent's own stated "Phase E (gated on B+D)"                                  |
| `sports_legacy_bucket_cutover_2026_07_16.md`             | `sports_mtds_odds_trades_index_correctness_followup_2026_07_23.md` (2 P0 DATA todos), `sports_legacy_cutover_closeout_tasks_2026_07_23.md` (2 P1/P2 admin todos)                                                                     | clean-partition                                                                                                                                          |
| `sports_master_closeout_2026_07_21.md`                   | `sports_master_closeout_progress_log_2026_07_21.md` (0 todos, 6-wave history); parent also needs an exact-duplicate section (`3. MOOT-AFTER-WIPE`, appears twice verbatim) de-duplicated                                             | clean-partition                                                                                                                                          |
| `tradfi_consolidated_closeout_2026_07_18.md`             | `tradfi_manifest_content_recovery_completion_2026_07_23.md` (11), `tradfi_backfill_throughput_followups_2026_07_23.md` (6), `tradfi_phase_d_terminal_gate_2026_07_23.md` (7)                                                         | clean-partition (parent becomes umbrella-eligible once trimmed <2000L)                                                                                   |
| `tradfi_v9_stage1_finish_2026_07_06.md`                  | `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_23.md` (2 todos, human-signoff-gated); 1 item **merges into** the existing `tradfi_consolidated_closeout_2026_07_18.md` rather than a new file                                    | clean-partition                                                                                                                                          |

**Common pattern across all 14**: the line-cap violation is overwhelmingly driven by **historical Progress Log narrative
for already-shipped work sitting inline next to a small tail of genuinely open todos** — not by unrelated work being
crammed in from day one. Every proposed split is lossless: content moves verbatim into a named child or archive-bound
doc, nothing is deleted (per the execute-phase conservation-check requirement already in the plan template).

---

## Bucket (d) — operator call required (14 plans, all locked)

**Every single bucket-(d) plan landed there because `locked_by: live-defi-rollout` is set** — none were classified (d)
purely for being a hard judgment call on content alone, except one (#27, which has a second, independent judgment-call
trigger even setting the lock aside). Per CLAUDE.md's multi-agent-safety rule and PLAN_FORMAT.md's locking rules,
touching any of these needs an explicit operator `[unlock-plan]` grant first — this is a **blanket ask**, not 14
separate asks, but the individual splits below are what would execute once granted.

**Consolidated operator decision list:**

1. **Blanket unlock question**: for the 14 locked plans below, do you want to `[unlock-plan]` them now so the line-cap
   splits can proceed, or leave them locked (meaning they stay over-cap and the corpus-wide hard-fail gate would need a
   carve-out for currently-locked plans until live-defi-rollout work concludes)?
2. **`master_to_live_defi_2026_05_23.md`** (98% done — 168/172 checkboxes, target date 2 months past) — simpler
   question: close the whole thing out as complete/superseded (bucket-a-shaped resolution) instead of a 4-way split?
   Recommended, given how little is actually still open.
3. **`capability_wizard_and_manifest_2026_06_11.md`** — similarly near-done (65/67); same question — archive outright
   once its 2 residuals (a CI-runner-blocked item + a named-but-unauthored DEFERRED successor) are forked out, or split
   properly?
4. **`instruments_foundation_completeness_2026_06_24.md`** — beyond the unlock, needs a ruling on 4 internal
   sign-off-sequencing tensions the plan's own 2026-07-14 doc-reconciliation pass already flagged (GATE 0/G1 never
   recorded signed off; G4 SIGNED-OFF vs a contesting 2026-07-03 ruling; sports re-homing vs the cefi-block rule) —
   these determine the correct `depends_on` shape of any split.
5. **`data_completion_to_100_all_ag_2026_06_21.md`** — beyond the unlock, needs a ruling on whether historical per-AG
   log entries should fold into the existing `data_completion_{cefi,defi,tradfi,prediction}_2026_07_15.md` siblings, and
   whether sports should get a parity `data_completion_sports_2026_07_23.md` sibling (4 of 5 AGs already got one in a
   2026-07-15 split; sports didn't).
6. **`sports_p2_features_history_to_ml_ready_2026_06_27.md`** — beyond the unlock, the plan's own 2026-07-23 banner
   flags its one open todo as overlapping `sports_consolidated_closeout_2026_07_19.md`'s Track C1/F and explicitly says
   not to resolve that unilaterally — needs a ruling on which plan owns it.
7. **The remaining 8 locked plans** (`carry_staked_basis_funding_scan_experiment_2026_06_16.md`,
   `citadel_paper_batch_live_reconciliation_2026_06_19.md`, `data_pipeline_hardening_self_monitoring_2026_06_22.md`,
   `instruments_mtds_subset_consistency_remediation_2026_06_17.md`,
   `master_data_canonicalisation_migration_catalogue_2026_06_07.md`,
   `migration_verification_orphan_safety_2026_06_10.md`, `monitoring_control_plane_master_2026_06_10.md`,
   `mvp_backfill_defi_onchain_v10_2026_06_27.md`, `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`) have
   unambiguous would-be-(c) splits proposed in the classification table above — once unlocked, no further operator
   judgment call is needed beyond confirming the split boundaries.

**Detail — the would-be-(c) split for each locked plan** (for the operator's reference, so an unlock decision can be
made informed; not to be executed without the unlock):

- **`capability_wizard_and_manifest_2026_06_11.md`** → would-be (a): fork 2 residuals (CI-runner-blocked openapi regen;
  DEFERRED "client-lite wizard" successor) into a small follow-up plan, then archive.
- **`carry_staked_basis_funding_scan_experiment_2026_06_16.md`** → would-be (c), clean-partition 3-way: keep original
  slug for the core carry-scan harness (24 todos); new `cross_venue_funding_reversion_research_2026_06_18.md` (6 todos,
  a genuinely distinct strategy that only got journaled here); new
  `carry_strategy_ensemble_productionization_2026_06_18.md` (10 todos).
- **`citadel_paper_batch_live_reconciliation_2026_06_19.md`** → would-be (c): extract the alpha-research +
  paper-trading-POC track (~30 todos) into `crypto_alpha_research_2026_06_23.md` — the plan's own text (lines 150-165)
  already proposed this migration and it was never executed.
- **`data_completion_to_100_all_ag_2026_06_21.md`** → would-be (c): 2 still-inline folded sections from an
  already-superseded 2026-06-01 batch → `legacy_bucket_dual_write_decommission_2026_07_23.md` (20 todos),
  `data_source_provenance_enforcement_2026_07_23.md` (15 todos).
- **`data_pipeline_hardening_self_monitoring_2026_06_22.md`** → would-be (c), 4-way:
  `data_pipeline_alert_substrate_residual_2026_07_23.md` (~14),
  `data_pipeline_self_healing_completion_residual_2026_07_23.md` (~7),
  `data_pipeline_ag_residual_backfill_decisions_2026_07_23.md` (~6-8), plus a status-check (not a plan) on a month-stale
  live-VM-outage item, and excise one mis-filed prod-terraform-drift item to a general infra plan entirely (not a
  data-pipeline-hardening concern).
- **`instruments_foundation_completeness_2026_06_24.md`** → would-be (c), 4-way (gated):
  `instruments_foundation_phase0_cross_cutting_2026_07_23.md` (10),
  `instruments_cefi_g1_g5_gate_execution_2026_07_23.md` (15, depends_on Phase-0 for GATE 0),
  `instruments_tradfi_g1_g5_gate_execution_2026_07_23.md` (12, same), slimmed umbrella retained at current filename (5).
- **`instruments_mtds_subset_consistency_remediation_2026_06_17.md`** → would-be (c), clean-partition 3-way:
  `instruments_store_cf_canonicalization_single_walk_2026_07_23.md` (19),
  `instruments_mtds_consistency_remediation_residuals_2026_07_23.md` (12),
  `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_23.md` (12).
- **`master_data_canonicalisation_migration_catalogue_2026_06_07.md`** → would-be (c): de-dupe an exact ~105-line
  verbatim-repeated block first (zero content loss), then extract `defi_migration_audit_log_2026_06_07.md` (8),
  `is_catalogue_g1_root_audit_log_2026_06_07.md` (2); trimmed coordinator (15) retains its existing `umbrella: true` and
  lands under 2000L.
- **`master_to_live_defi_2026_05_23.md`** → see decision #2 above; if the operator prefers a split anyway:
  `may23_cutover_historical_audit_archive_2026_07_23.md` (0, archive-bound),
  `may23_readiness_checklist_and_verification_2026_07_23.md` (30, the only piece that could still be "live"),
  `active_plan_inventory_dashboard_2026_07_23.md` (0, script-regenerated, not May-23-specific),
  `may23_new_workstreams_post_cutover_backlog_2026_07_23.md` (5).
- **`migration_verification_orphan_safety_2026_06_10.md`** → would-be (c): the durable protocol already migrated to
  codex (V7 todos fold CF-15..CF-21 into `canonical_form_cross_service_audit_checklist.md`), so this plan is a narrative
  citation, not the mechanism SSOT — archive the historical log to the existing
  `plans/audit/results/migration_orphan_safety_goalpost_verification_2026_06_10.md`, then 4 small residual children
  (prediction-cqg, sports pre-launch+CF-5 verify, defi-venue+lst-rates, infra/ops residuals), each 2-5 todos.
- **`monitoring_control_plane_master_2026_06_10.md`** → would-be (c):
  `monitoring_control_plane_remaining_items_2026_07_23.md` (7, CI-dashboard/fleet-git-health tail),
  `orchestrator_vm_e2e_hardening_2026_06_12.md` (3, a scope-creep section covering agent-orchestrator bootstrap/watchdog
  hardening, file-disjoint from the CI-dashboard work).
- **`mvp_backfill_defi_onchain_v10_2026_06_27.md`** → would-be (c): pure hygiene split, zero gate/todo changes — keep
  the same slug/file with all 12 todos verbatim, extract the ~4500-line verbatim operational log into
  `mvp_backfill_defi_onchain_v10_operational_log_2026_07_23.md` (0 todos).
- **`prediction_venue_perps_and_live_clob_depth_2026_06_20.md`** → would-be (c), clean-partition 3-way:
  `prediction_perps_kalshi_polymarket_parked_2026_07_23.md` (15, parked per a 2026-07-14 operator ruling),
  `prediction_live_clob_depth_capture_2026_07_23.md` (20), `prediction_cross_venue_arb_and_coverage_2026_07_23.md` (15).
- **`sports_manifest_canonicalisation_2026_06_01.md`** → bucket (a), see above.
- **`sports_p2_features_history_to_ml_ready_2026_06_27.md`** → see decision #6 above; not a clean (c) even unlocked.

---

## What "done" looks like once approved

Per the execute-phase instructions already in this issue's parent request:

1. Bucket (a): `git mv` to `plans/archive/2026_07/<same filename>` (2 plans; 1 needs unlock first).
2. Bucket (b): N/A this round (0 plans qualify).
3. Bucket (c): for each approved split, `grep -rn '<old-plan-slug>'` across `plans/`, `codex/`, and `scripts/` first to
   find every reference and update it, THEN move content, THEN verify the todo-count conservation check (total todos
   across old+new files must not shrink).
4. Bucket (d): operator grants `[unlock-plan]` (blanket or per-plan) + rules on the 4 flagged judgment calls above, then
   each plan executes per its would-be-(c) (or would-be-(a)) split already documented.
5. After every change: `bash scripts/plan-hygiene/run_hygiene_sweep.sh` must show 0 hard failures, and
   `check_line_caps.sh` must no longer list the touched file(s).
6. Commit with `docs(plans):` prefix, one commit per plan or logical batch, never `git add -A`.

**Execution status (2026-07-24): 21 of 30 DONE, 3 of the remaining 9 fixed, 6 + 1 outstanding.** Operator approved all
30 rows via interactive Q&A on 2026-07-24; execution ran as two workflows (`wf_65688dca-5ac` then a targeted fix pass
`wf_22001490-e9b`). Shipped: `unified-trading-pm@67e47f9b` (21 plans: 2 archived, 2 closed out whole, 5 split clean, 9
split-after-unlock, 3 duplicate-file bugs fixed, 13 reference-path fixes, 6 invalid `assigned_role` values fixed, 1
`.gitleaks.toml` false-positive allowlisted) + `unified-trading-pm@5a47210fe` (3 more:
`cefi_consolidated_closeout_2026_07_18`, `github_actions_ci_cost_reduction_2026_07_15`,
`data_pipeline_alerts_batch_remediation_2026_07_15` — all now well under the 1000L cap, verified clean).

## Deferred work after 2026-07-24

| Item                                                                                                                                                                                                                                                                           | State              | Blocked on                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `defi_consolidated_closeout_2026_07_18.md` still not trimmed (3385L, was supposed to shrink after `defi_strategy_pnl_axis_index_2026_07_24.md` + `defi_consolidated_closeout_history_2026_07_18.md` were extracted — children exist and are correct, parent was never trimmed) | Not done           | Nobody — pick up directly: diff parent vs the 2 children, remove the now-duplicated Strategy/PnL section + historical Progress Log + 75-finding audit narrative from the parent                                                                                                                                                 |
| `data_pipeline_check_mdps_features_2026_07_20.md` partially trimmed (1299→1200L, not enough — child `candle_canonical_path_migration_execution_2026_07_24.md` is correct)                                                                                                      | Not done           | Nobody — the Option-A migration section (8-phase epic detail) is still sitting in the parent, remove it                                                                                                                                                                                                                         |
| `data_status_page_ux_and_canonicalisation_2026_07_16.md` barely changed (2133→2078L)                                                                                                                                                                                           | Not done           | Nobody — per the original fix-job hint, most of this file's length is LEGITIMATE historical record that should stay; only the small duplicated P6-phase-2/P10-B slice needs removing, verify against `data_status_catalogue_true_source_phase2_2026_07_24.md` + `sports_fixtures_browser_single_catalogue_source_2026_07_24.md` |
| `prediction_consolidated_closeout_2026_07_18.md` untouched (1486L)                                                                                                                                                                                                             | Not done           | Nobody — 4 children exist and are correct (`prediction_phase_{c,ab,d,e}_*_2026_07_24.md`), parent Progress Log + Phase A-E bodies need condensing/removing                                                                                                                                                                      |
| `citadel_paper_batch_live_reconciliation_2026_06_19.md` untouched (2194L)                                                                                                                                                                                                      | Not done           | Nobody — child `crypto_alpha_research_2026_07_24.md` is correct, more alpha-research Progress Log content still duplicated in parent needs removing                                                                                                                                                                             |
| `data_pipeline_hardening_self_monitoring_2026_06_22.md` untouched (2182L)                                                                                                                                                                                                      | Not done           | Nobody — 4 children exist and are correct, bulk historical Progress Log (~60% of file) still duplicated in parent needs removing                                                                                                                                                                                                |
| `distinct_values_noncanonical_audit_2026_07_20.md` re-scoped re-dispatch never started (still 1627L, unchanged)                                                                                                                                                                | Not done           | Nobody — fork ONLY the MTDS lending-restamp workstream into `market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24.md`; leave the RESTAKING content in place (already fully shipped, git-verified, not open work)                                                                                      |
| `check_todo_regression.sh` still flags plans in this batch as having "lost" todos vs origin                                                                                                                                                                                    | Cannot be done yet | Needs either a script fix (teach it about intentional cross-file splits, e.g. a manifest) or continued per-commit manual reconciliation — not a blocker, just a known-noisy gate                                                                                                                                                |

**Recommended next item**: resume the fix-workflow exactly where it left off —
`Workflow({scriptPath: "/home/ubuntu/.claude/projects/-home-ubuntu-unified-trading-system-repos-unified-trading-pm/bf7b63d8-82c9-458e-bec5-f4738124ec0c/workflows/scripts/plan-line-cap-fix-trims-wf_22001490-e9b.js", resumeFromRunId: "wf_22001490-e9b"})`
— completed agent() calls (the 3 already fixed + verified) return cached instantly; only the 6 unfinished + the rescoped
distinct_values redispatch re-run live. After it completes: re-verify each parent's line count actually dropped (do not
trust the self-report alone — this exact class of bug, a job claiming success without actually trimming the parent, is
what caused this deferred-work list to exist), re-run `check_reference_paths.py` + `run_hygiene_sweep.sh`, then commit +
push per plan/logical batch.

**Lessons carried forward** (so the next session does not re-learn these):

- **A job's self-report is not proof of its action.** This batch had 2 stub/placeholder agent results caught by content
  review, 1 job that claimed reference-path fixes it never made (verified via `git diff --stat` showing zero change),
  and 9 jobs that created the correct child file but never removed the duplicated content from the parent — always
  verify with an independent measurement (line count, `grep`, `git diff --stat`), never trust the return text alone.
- **This is a heavily concurrent, multi-operator repo.** Encountered: a git index-lock collision from a different live
  session (`main·laptop`) mid-commit, ~168 files staged by an unrelated process that had to be `git restore --staged`
  before my own commit (never `git add -A` — review `git diff --cached --stat` with no path arg first), and a background
  Workflow task that was silently stopped with no completion record (its partial progress was still on disk and had to
  be discovered by direct measurement, not trusted from a status check).
- **Todo-conservation checks need the SAME regex as the enforcing gate.** Different counting methods (nested vs
  top-level checkboxes) produced different totals for the same file; always reconcile using `check_todo_regression.sh`'s
  own `^- \[[ xX]\]` regex, not an ad hoc count.
