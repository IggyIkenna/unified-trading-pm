---
doc_type: issue
title: PM quality-gates.sh RED — plan-discipline ratchet (121 > baseline 120) + frontmatter-schema violation
summary: >-
  unified-trading-pm's quality-gates.sh fails repo-wide on 2 pre-existing, unrelated checks (plan-discipline ratchet 121
  > baseline 120; a frontmatter-schema gap on sports-2020-06-data-floor.md), blocking the green-tree ship gate for any
  non-docs(plans) PM commit.
status: resolved
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, plan-discipline, frontmatter-schema, governance]
related: []
created: "2026-07-21"
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
resolved_by:
  unified-trading-pm@5225b4a08 — all todos [x], plan-discipline ratchet re-baselined 19 → 0 via --baseline-write (line
  325-327)
locked_by:
source: [deployment_ui_vm_log_viewer_2026_07_20.md]
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

# What I found

> **🟢 ARCHIVED 2026-07-25** — status=resolved, archived per /codex/11-project-management/issue-doc-lifecycle.md's
> archive-on-resolve rule (terminal_status_archival_backlog_sweep_2026_07_25.md).

Running `bash scripts/quality-gates.sh` in `unified-trading-pm` (needed to ship an unrelated 1-line
`configs/cloud-providers.yaml` sync fix) fails on 2 pre-existing, unrelated checks:

1. **Plan discipline regression** — `scripts/quality_gates/check_plan_discipline.py` reports 121 violations vs the
   committed baseline of 120 (`scripts/quality_gates/plan_discipline_baseline.yaml`). Breakdown:
   42×`A-deferred-no-banner` (a plan contains `DEFERRED` but no `## Deferred work — migrated to:` banner), 79×
   `C-archive-no-successor`. This is off-by-one over baseline — some plan committed since the baseline was last written
   tipped it over (fleet-wide plan churn, not attributable to any single commit I can find without a full `git bisect`
   across dozens of concurrent slots).
2. **Frontmatter schema violation** — `/codex/02-data/sports-2020-06-data-floor.md`: `referenced_by` optional key is
   absent (schema requires present-but-empty, not fully absent).

Verified pre-existing: my only staged change was `configs/cloud-providers.yaml` (a data-only sync, see
`unified-api-contracts@83506de0` / `unified-trading-library@e22e40f1` for the same fix in the other 2 copies of this
file). Neither failing check references that file.

# Why it matters

`unified-trading-pm`'s `quality-gates.sh` gates EVERY quickmerge ship through this repo (plan authoring, cross-repo
`docs(plans):` flips land via raw push and are unaffected, but any non-plan PM commit — like this config sync — needs
the full gate green to get a quickmerge sentinel). With ~50+ backlog tasks draining concurrently across slots, this repo
is high-churn; a ratchet regression here silently blocks anyone who needs a non-`docs(plans):` PM commit to ship
normally.

# Recommended decision

- Re-run `scripts/quality_gates/check_plan_discipline.py` to enumerate the 121 current violations, diff against
  `plan_discipline_baseline.yaml`, and either (a) add the missing `## Deferred work — migrated to:` banners / archive
  successor refs for the 1 (or more) new offenders, or (b) if the regression is legitimate accumulated debt from many
  small plan edits fleet-wide, re-baseline with `--baseline-write` per the check's own remedy text, with an operator
  sign-off note on why the ratchet moved.
- Add the missing `referenced_by: []` (or equivalent empty-but-present key) to
  `/codex/02-data/sports-2020-06-data-floor.md` frontmatter.

## Todos

- [x] [DOCS] P2. ✅ Fix `/codex/02-data/sports-2020-06-data-floor.md` frontmatter — add the missing `referenced_by` key
      (present-but-empty is enough to pass `scripts/docs/seed_frontmatter.py --apply`) — unified-trading-pm@3122de370.
      Ran the remedy tool as-instructed; it also seeded the elective `implementation_status` key.
      `check_frontmatter_schema.py` now reports zero violations across all 1739 docs; full `quality-gates.sh` for this
      repo now passes clean end-to-end (both todos in this issue doc closed — plan-discipline ratchet fix landed
      @522dcdf92). (repo: unified-trading-pm)
- [x] [DOCS] P2. ✅ Triage the 121 plan-discipline violations (42 `A-deferred-no-banner` + 79 `C-archive-no-successor`)
      against baseline 120 in `scripts/quality_gates/plan_discipline_baseline.yaml` — unified-trading-pm@522dcdf92. Real
      fix, not a blind re-baseline: enumerated all 121, classified each by whether an honest templated banner applies.
      19/79 archived `C-archive-no-successor` plans had **zero open `- [ ]` items** (100%-closed) — applied the
      established `## Deferred work — migrated to: **None** — successor: not applicable` banner (same template as
      precedent commit `835ef6114`). This is the ONLY subset a scripted fix can honestly close — everything else needs
      real per-plan judgment: 60/79 archived plans still have open items (1–139 each) and 42/42 active
      `A-deferred-no-banner` plans have un-qualified DEFERRED mentions, both requiring a human/plan-owner call on the
      actual successor, not a generic banner. Net: 121 → 102 violations, comfortably clears baseline 120 without gaming
      it (an improvement, not just a ratchet raise) — re-baselined 120 → 102 via `--baseline-write` to codify. Remaining
      102 (42 A + 60 C) is genuine accumulated fleet-wide plan-corpus debt, not attributable to one commit; tracked as a
      fresh P3 follow-up todo below rather than force-fit into this P2 task's scope. (repo: unified-trading-pm)
- [x] [DOCS] P3. ✅ Partial: real per-plan fixes for the 4 most tractable `C-archive-no-successor` cases (all
      zero/near-zero open items) — unified-trading-pm@6538ead51. `incident_gateway_and_state_machine_2026_05_23` and
      `reconciliation_age_tracking_and_escalation_2026_05_23` already had honest "all items completed" banners but in
      wording the regex didn't recognize (no literal `successor:`/`MIGRATED TO:` token) — reworded to the established
      template, for the second one naming its REAL already-documented successor (`observability_master` epic P3) instead
      of a generic "not applicable". `instrument_universe_registry_consolidation_2026_06_29` had zero open items and its
      only "DEFERRED" hits were incidental prose ("verdict deferred to the investigation result", "no deferred `- [ ]`
      left in this plan") — added the honest closing banner. `vm_launcher_durable_log_observability_2026_06_19` had
      exactly 1 open item, already correctly migrated to
      `plans/archive/issues/long_lived_vm_logs_not_backed_up_2026_07_02.md` in prose but in a form (`& MIGRATED** to` +
      markdown link, no literal `successor:`/`MIGRATED TO:`/`→ plans/active/` token) the regex didn't recognize — added
      a proper banner naming that real successor doc. Verified each via direct re-run of `check_plan_discipline.py`: 102
      → 98 (all 4 confirmed resolved, no other counts moved). Re-baselined 102 → 98 via `--baseline-write` (real
      fix-driven improvement, no operator sign-off needed — matches the P2 precedent's own reasoning). Did NOT touch
      `leveraged_leg_controller_2026_05_01` (2 open items: a real unshipped test-coverage gap + an operator-side Docker
      rebuild gate, neither has an existing successor plan) or
      `transfermarkt_sfi_team_mapping_cache_and_drift_detection_2026_04_22` (2 unchecked `[HUMAN]` gates on an
      already-archived-complete plan — ambiguous whether they were satisfied out-of-band; no fabricated checkmarks) —
      both need real operator/plan-owner judgment, not a scripted close; left for the split-out todos below. (repo:
      unified-trading-pm)
- [x] [DOCS] P3. ✅ Remaining archived-plan debt, batch 1 — sports/predictions (14 plans, 3–49 open items each) —
      unified-trading-pm@\<pending\>. Fanned out 14 parallel read-only research agents (one per plan) to extract every
      open item's context and search `plans/active/` for an existing successor; made the closure call myself on each (no
      blanket-close). Result: **all 14 plans got a real `## Deferred work — migrated to:` banner** naming their actual
      successor(s) — `apifootball_enrichment_historical_backfill_2026_04_21` →
      `sports_p2_history_apifootball_2015_to_present_2026_06_27`; `features_sports_pipeline_deployment_2026_04_21` →
      `features_sports_service_consolidation_deploy_2026_07_15` + `sports_p2_features_history_to_ml_ready_2026_06_27`;
      `features_sports_upstream_coverage_gaps_2026_04_21` →
      `instruments_mtds_subset_consistency_remediation_2026_06_17`; `sports_ml_may_23_2026` →
      `sports_consolidated_closeout_2026_07_19` + `sports_master_closeout_2026_07_21` +
      `sports_manifest_canonicalisation_2026_06_01`; `sp_prediction_may_23_2026` →
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20` + `master_to_live_defi_2026_05_23`;
      `sports_fixtures_truthset_recovery_2026_05_06` → `data_completion_to_100_all_ag_2026_06_21` +
      `sports_pipeline_to_100pct_golden_window_first_2026_06_27`; `sports_phantom_recon_and_failure_triage_2026_05_01` →
      `sports_data_sources_canonical_completion_2026_07_13` +
      `reconcile_phantom_manifest_rows_stale_read_overwrite_2026_07_12`; `sports_data_available_at_rename_2026_05_07` →
      `sports_master` epic; `sports_e2e_validation_2026_03_27` → `sports_p2_features_history_to_ml_ready_2026_06_27`;
      `sports_predictions_e2e_2026_05_05` → `sports_master_closeout_2026_07_21` +
      `predictions_ml_walk_forward_and_arb_2026_06_20`; `sp500_ml_readiness_master_2026_05_05` →
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20`; `prediction_markets_may_23_2026` → `predictions_master`
      epic; `predictions_canonical_question_group_polymarket_migration_2026_05_06` →
      `data_completion_prediction_2026_07_15` + `predictions_other_bucket_and_ui_drilldown_2026_06_20`;
      `features_sports_honest_coverage_2026_05_05` → `sports_consolidated_closeout_2026_07_19` +
      `sports_halftime_odds_sfi_vs_inplay_2026_07_16` + `features_sports_service_consolidation_deploy_2026_07_15`. **3
      genuinely-orphaned findings filed as fresh issue docs** (not blanket-closed): (1)
      `plans/active/issues/unified_trading_library_data_available_at_rename_silently_reverted_2026_07_21.md` (P1) — a
      **real live regression**: the UTL `data_available_at`→`available_at` rename shipped
      `unified-trading-library@     94e43e8c` but was silently reverted the next day by an unrelated commit
      (`988ab287`), so the no-lookahead scan on sports data has been a silent no-op since 2026-05-23; (2)
      `plans/active/issues/sports_predictions_live_mode_and_backtest_execution_orphaned_2026_07_21.md` (P3) — bundles
      the recurring `spread_calculator`/strategy+execution backtest/live-mode-activation gap found independently in 3 of
      the 14 plans; (3)
      `plans/archive/issues/features_sports_deployment_ui_coverage_tab_and_registry_playbook_2026_07_21.md` (P3,
      resolved + archived 2026-07-24) — the deployment-ui honest-coverage tab + codex feature-registration playbook that
      Phase 8 of `features_sports_honest_coverage` never shipped. Also surfaced (not separately filed, just noted in
      each banner): 10 of the 14 archived plans still carry `locked_by: live-defi-rollout` never cleared at archival — a
      process-hygiene gap for the operator, not blocking. Re-ran `check_plan_discipline.py` before/after: 96 → 82
      violations (exactly the 14 `C-archive-no-successor` fixes, 0 side effects), re-baselined 96 → 82 via
      `--baseline-write`. (repo: unified-trading-pm)
- [x] ✅ [DOCS] P3. Remaining archived-plan debt, batch 2 — cefi/defi (9 plans, 9–35 open items each) —
      unified-trading-pm@8cf0be7b2. Real per-plan judgment on all 9, verified via grep against the live active-plan
      corpus (not guessed): **7/9 got a successor banner naming a real active plan** — `price_arbitrage_may_23_2026` →
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20` (traced through the archived `tradfi_master_2026_05_07`
      intermediate); `cefi_ml_may_23_2026` → `cefi_ml_directional_continuous_live_2026_06_20`;
      `defi_data_types_completeness_2026_04_24` → `data_completion_defi_2026_07_15`; `live_defi_rollout_may_23_2026` →
      `defi_consolidated_closeout_2026_07_18`; `defi_e2e_pipeline_2026_04_30` → `defi_consolidated_closeout_2026_07_18`
      (17/19 items — 2 strategy-engine items from a folded-in `leveraged_leg_controller_2026_05_01` sub-plan left
      explicitly flagged as unresolved, deferring to batch 4's own investigation of that same source plan rather than
      guessing); `cefi_venue_universe_expansion_2026_05_01` → `cefi_consolidated_closeout_2026_07_18` (all 6 venues —
      BITFINEX/BITGET/KRAKEN/EXTENDED/PACIFICA/LIGHTER — confirmed shipped and under active canonical-id hardening
      there); `dex_historical_replay_lighter_extended_pacifica_2026_05_07` → `cefi_consolidated_closeout_2026_07_18`.
      **1/9** (`cefi_phase2_gap_audit_2026_05_01`, 615-line root-cause audit) got a domain-level successor citation
      (`cefi_consolidated_closeout_2026_07_18` + `data_completion_cefi_2026_07_15`) without line-by-line item tracing —
      noted explicitly as unverified-at-item-level. **1/9** (`defi_recursive_borrow_archetypes_2026_05_08`, a
      question-doc) resolved to "None — not applicable": traced its full `spawned_plan` chain (`…_2026_05_10` →
      `…_post_cutover_2026_06_01`, both archived with 0 open items, `status: complete`) confirming the work fully
      shipped. Verified via direct re-run: `check_plan_discipline.py` 96 → 87 for this batch alone (later fell to 40 as
      concurrent batches 1/3/4/5 also landed); re-baselined via `--baseline-write` at each step. Shipped after ~25 lost
      sentinel-races under heavy fleet doc-push contention on this repo (see
      `plans/active/issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md` — a
      pre-existing known throughput issue, not something introduced here; no work was lost, only wall-clock). (repo:
      unified-trading-pm)
- [x] ✅ [DOCS] P3. Remaining archived-plan debt, batch 3 — instruments/market-data/manifest (9 plans, 3–90 open items
      each) — unified-trading-pm@\<pending\>. Fanned out 9 parallel read-only research agents (~222 open items total),
      made closure judgments myself. All 9 files got a real `## Deferred work — migrated to:` banner:
      `manifest_429_per_vm_sharding_2026_04_25` → `manifest_v6_batch3_residual_orphaned_work_2026_07_21` +
      `consolidator_throughput_backlog_monitor_2026_07_09`;
      `instruments_service_orchestrator_reliability_fixes_2026_04_21` →
      `sports_data_sources_canonical_completion_2026_07_13` + `sports_consolidated_audit_2026_07_19`;
      `shard_granularity_ssot_propagation_2026_05_06.HANDOVER.md` → `master_to_live_defi_2026_05_23` +
      `data_status_page_ux_and_canonicalisation_2026_07_16`; `shard_granularity_ssot_propagation_2026_05_06.plan.md` →
      `writegate_honest_coverage_endtoend_2026_05_06` + `sports_p2_features_history_to_ml_ready_2026_06_27` +
      `manifest_writer_record_captured_available_at_never_persisted_2026_07_13` +
      `mtds_available_at_cross_asset_backfill_2026_07_13`; `manifest_schema_v6_quote_margin_combo_2026_04_23` →
      `cefi_chain_tail_v6_canonicalisation_2026_07_21` + `manifest_v6_batch3_residual_orphaned_work_2026_07_21`;
      `run_lifecycle_events_ssot_2026_05_05` → `codex_violations_ratchet_to_five_2026_06_10`;
      `instruments_and_market_tick_data_completion_2026_05_01` → the per-AG consolidated-closeout family +
      `data_completion_to_100_all_ag_2026_06_21`; `instruments_to_100pct_eod_2026_05_04` → same family +
      `macro_micro_econ_data_capture_audit_2026_06_05`; `market_tick_data_to_100pct_2026_05_05` (largest, 90 items) →
      `data_completion_to_100_all_ag_2026_06_21` + `instruments_mtds_subset_consistency_remediation_2026_06_17` +
      `sports_master_closeout_2026_07_21`. **2 genuinely-orphaned findings bundled into 1 fresh issue doc** (not
      blanket-closed): `plans/active/issues/manifest_v6_batch3_residual_orphaned_work_2026_07_21.md` (P3) — (1) the
      legacy `_write_with_generation_match` CAS-path deletion needs re-scoping (current architecture now also reuses it
      for canonical-index force-rewrites, so a blind delete would be wrong), (2) deployment-api/deployment-ui never
      surfaced `quote_asset`/`margin_type` filtering. Also surfaced (not separately filed): all 7 of 9 files still carry
      `locked_by: live-defi-rollout` never cleared at archival — noted in each banner, a recurring
      archival-ritual-step-5 gap for the operator. Re-ran `check_plan_discipline.py` before/after: 58 → 49 violations
      (exactly the 9 `C-archive-no-successor` fixes; baseline had moved 82→58 from concurrent batch-2 work by another
      slot), re-baselined 58 → 49 via `--baseline-write`. (repo: unified-trading-pm)
- [x] [DOCS] P3. ✅ Remaining archived-plan debt, batch 4 — strategy/UI + the 2 held-back small plans (8 plans found,
      2–67 open items each) — unified-trading-pm@16aa0e958. Per-plan judgment, not blanket-close: 3 got a **direct
      successor banner** naming a verified real active epic — `dart_ux_cockpit_refactor_2026_04_29` +
      `strategy_architecture_v2_finalization_2026_04_19` both declared a `superseded_by:` pointing at
      `strategy_and_dart_master_2026_05_07.md`, a file that no longer exists (it was itself superseded 2026-05-21 and
      split into `strategy_master.md` + `dart_and_promote_master.md`) — retargeted at whichever half actually owns the
      content (dart_ux → `dart_and_promote_master.md`; strategy_architecture_v2_finalization → `strategy_master.md`,
      content-verified against its "Owns" section); `strategy_architecture_v2_phase3_11_handoff_2026_04_17` had no
      declared successor at all but its residual items (allocator archetypes, action handlers, shadow mode, Unity/MEV
      routing) are a direct content match for `strategy_master.md`'s "Owns" section. The other 5 have genuinely orphaned
      or mixed-domain residuals with no honest single successor: filed
      `plans/active/issues/batch4_strategy_ui_archived_plan_residuals_2026_07_21.md` naming each — 2 `[HUMAN]` gates
      pending operator sign-off (`leveraged_leg_controller_2026_05_01`'s Docker rebuild,
      `transfermarkt_sfi_team_mapping_cache_and_drift_detection_2026_04_22`'s cache-speedup validation), 1 where the
      writer-side code shipped but the migration/cleanup residual is unverified (`combo_bundle_aggregation_2026_04_30` —
      confirmed bundling live in `market-tick-data-service/.../symbol_rules.py:256`), 1 where the plan's SSOT artifacts
      shipped via other work but granular items need re-audit after 4 months of drift
      (`ui_quality_gates_parity_2026_03_16`), and 1 genuinely mixed-domain plan needing an item-by-item split between
      two different active plans (`dart_ui_strategy_filtering_and_onboarding_2026_04_24` —
      `marketing_site_three_route_consolidation_2026_04_26` for the UI funnel vs
      `capability_wizard_and_manifest_2026_06_11` for the archetype-capability tail). Verified via direct re-run of
      `check_plan_discipline.py`'s `_check_rule_c`: all 8 confirmed cleared, no other plans' counts moved. Reconciled
      `plan_discipline_baseline.yaml` against sibling batch-1's concurrent landing (82 after their fix) — combined
      re-baseline 82 → 74. (repo: unified-trading-pm)
- [x] ✅ [DOCS] P3. Remaining archived-plan debt, batch 5 — infra/orchestrator/deployment/codex/misc (16 plans, 4–139
      open items each) — `unified-trading-pm@2fd0231ba`. Real per-plan judgment for all 16, no blind-close: **13 MOOT**
      (`ICLOUD_MIGRATION_CHECKLIST` — superseded by live dependency-alignment enforcement;
      `deployment_service_build_infrastructure_repair_2026_04_22` — each item's goal independently achieved via later
      plans; `orchestrator_strict_vm_matching_and_plan_frontmatter_governance_2026_06_24` — open items live in a section
      the plan's own banner already disowns as superseded; `_HANDOFF_expected_universe_enumerator_2026_05_07` —
      deliverable shipped under an evolved name; `WORKFLOW_RESIDUAL_ITEMS` — every named repo renamed/merged/ retired
      since 2026-03; `codex_refactor_2026_05_08` — frontmatter already declared shipped, D.4 cross-refs verified
      resolved; all 4 `work_split_*` files — confirmed personal day-splitting coordination docs
      (`type: coordination-doc`), every substantive item tracked+completed elsewhere). **3 with real named successors**:
      `quality_gate_hardening.plan` → `cicd_mvp_ldr_to_main_pipeline_2026_06_30` (operator 2026-06-30 decision replaced
      build-platform gating with `quality-gates-v2` required-check branch protection);
      `sfi_chunk_parallel_backfill_2026_04_22` → `sports_pipeline_to_100pct_golden_window_first_2026_06_27` (the full
      2015→present SFI backfill is explicitly tracked `⬜ not started` as "P2b" there);
      `data_pipeline_completion_2026_04_18` → `data_completion_to_100_all_ag_2026_06_21` (documented `supersedes:`
      chain, folded 2026-07-13 into per-AG children). **2 split-verdict**:
      `orchestrator_consolidated_remaining_2026_06_25` (WS-D items moot — human-planning VM migration + 37GB-OOM fix
      both shipped; WS-E items real but explicitly deferred-to-next-quarter by
      `plans/epics/agent_operating_framework_master.md` itself); `stub_completion_interfaces_and_infra` +
      `phase3_service_hardening_integration` (Tracks G/H moot — UPI/UMI fully eliminated; but BOTH plans independently
      still reference the SAME genuinely orphaned code TODO, `risk-batch-compute-unimplemented` in
      `strategy-service/strategy_service/risk/cli/handlers/compute_handler.py` — it bounced between these two archived
      plans for 4+ months without ever landing on an active tracker). Filed ONE new issue doc for that shared orphan:
      `issues/strategy_service_batch_risk_compute_unimplemented_2026_07_21.md` (P2, closes both plans' open item at
      once). Also fixed a pre-existing frontmatter YAML bug in `phase3_service_hardening_integration` (an `overview:`
      multi-line plain scalar with an embedded colon broke the parser — surfaced by the plan-hygiene pre-commit hook the
      first time this file was touched; quoted as a block scalar). Re-ran `check_plan_discipline.py` before/after
      (combined with concurrent batch-1/batch-4 fixes landing in parallel): violations dropped to 58, re-baselined via
      `--baseline-write`. (repo: unified-trading-pm)
- [x] [DOCS] P3. ✅ Precisely 3-way classified all 42 active-plan `A-deferred-no-banner` violations by re-scanning each
      plan's actual `_DEFERRED_RE` hit context (not just presence of the word) — unified-trading-pm@6538ead51. My FIRST
      pass (before landing) assumed most were the CLAUDE.md-sanctioned `DEFERRED-OPERATOR-DECISION` / `-CREDENTIALS` /
      `-UPSTREAM-OUTAGE` qualifier pattern — that assumption was WRONG on direct inspection. Real breakdown: **(1) 2
      plans** (`cicd_mvp_ldr_to_main_pipeline_2026_06_30`, `monitoring_control_plane_master_2026_06_10`) had EVERY hit
      as a genuine all-caps `DEFERRED-<QUALIFIER>` tag (`DEFERRED-OPERATOR-DECISION`, `DEFERRED-BY-HEADROOM`) — fixed
      mechanically with the exact `f6df716e7` precedent banner ("See inline `DEFERRED-<QUALIFIER>` annotations... for
      the specific successor/blocker"). **(2) 10 plans** had EVERY hit as an INCIDENTAL compound-word/filename false
      positive — `_DEFERRED_RE`'s `\bDEFERRED\b\s*[—\-]` matches "deferred-" as a lowercase compound modifier with NO
      governance meaning at all (e.g. `deferred-table item 13`, `deferred-import adapter pattern`,
      `deferred-build-replay` — a GHA workflow NAME), the exact same loose-regex-matches-an-incidental-substring bug
      class fixed today in `check_evidence_backed_completion.py` — these need a CHECKER fix (see the new todo below),
      not a plan edit. **(3) 30 plans** have at least one genuine BARE
      `**DEFERRED**`/`[DEFERRED]`/`DEFERRED — <description>` mention (a real unqualified defer, not a false positive,
      not a formal qualifier tag either) — these need real per-plan judgment same as the archived batches. Landed the 2
      mechanical fixes; re-scanned full corpus (starting from 98, after the archived-plan batch above): 98 → 96,
      re-baselined 98 → 96 via `--baseline-write`. Split the remaining 40 into the 2 todos below instead of guessing
      further. (repo: unified-trading-pm)
- [x] ✅ [SCRIPT] P3. Tighten `check_plan_discipline.py`'s `_DEFERRED_RE` (rule A) + `_ARCHIVE_OK_TOKENS_RE` (rule C) so
      lowercase `deferred-<word>` compound modifiers / filenames (not the all-caps `DEFERRED-<QUALIFIER>` governance
      convention, and not a real bare `DEFERRED —`/`**DEFERRED**` marker) stop false-positiving — same bug class as
      `check_evidence_backed_completion.py` fixed earlier this session (same-clause / precise-token-shape fix, not a
      whole-block substring match) — unified-trading-pm@002f2cba8. New `_DEFERRED_RE` matches only: `**DEFERRED**` /
      `[DEFERRED]`, `DEFERRED-[A-Z]...` (qualifier tag — char right after the hyphen must be uppercase), or
      `DEFERRED\s+[—-]` (bare marker — requires whitespace between the word and the dash, distinguishing it from the
      no-space qualifier form). Rule C's `_ARCHIVE_OK_TOKENS_RE` had its own bare `\bDEFERRED\b` (case-insensitive, no
      dash requirement at all — an even looser instance of the same bug) removed; `_check_rule_c` now ORs against the
      same tightened `_DEFERRED_RE` instead of duplicating the token shape. Verified all 10 named fixtures individually
      cleared post-fix (`bucket_estate_consolidation_to_sub100_2026_07_13`,
      `carry_staked_basis_funding_scan_experiment_2026_06_16`, `data_pipeline_hardening_self_monitoring_2026_06_22`,
      `defi_consolidated_closeout_2026_07_18`, `github_actions_ci_cost_reduction_2026_07_15` +
      `github_actions_cost_reduction_options_analysis_2026_07_15`, `infra_capture_and_devops_leftovers_2026_07_06`,
      `l2_book_microstructure_capture_2026_07_13`, `pipeline_mode_partition_migration_2026_06_01`,
      `sports_data_sources_canonical_completion_2026_07_13`), plus a standalone Python unit-test of the regex against
      all 12 false-positive strings (should-NOT-match) and 7 real-marker strings (should-match, incl.
      `DEFERRED-OPERATOR-DECISION`/`DEFERRED-BY-HEADROOM`/`DEFERRED-INDEFINITELY` qualifier tags) — all passed exactly
      as intended. Also confirmed the 2 already-banner-fixed qualifier plans
      (`cicd_mvp_ldr_to_main_pipeline_2026_06_30`, `monitoring_control_plane_master_2026_06_10`) stay clean (banner
      already satisfies rule A). Re-scanned full corpus: 40 → 19 violations (11 MORE of the "30 has-bare-or-mixed" list
      turned out to be false-positive-only once the regex is precise, beyond the 10 explicit fixtures) — re-baselined 40
      → 19 via `--baseline-write` (real fix-driven improvement, no operator sign-off needed, same precedent as the P2/P3
      batches above). Rule C (archive) stayed at 0 violations throughout, no regression. Lost the quickmerge sentinel
      race twice to concurrent PM doc-pushes before landing on the 3rd attempt (known throughput issue, see
      `plans/active/issues/quickmerge_sentinel_race_retry_storm_under_pm_doc_push_contention_2026_07_21.md` — not a
      defect, no work lost). Shipped via PR #1301 (live-defi-rollout→main, auto-merge). The remaining 19 genuinely
      bare/mixed plans are the corrected, precise list for the next todo below (its original 30-item list is now stale
      by 11 entries). (repo: unified-trading-pm)
- [x] [DOCS] P3. ✅ The remaining 19 active plans (re-classified — see the checker-fix todo above, which corrected the
      original 30-item list down to these 19 confirmed-genuine hits; the other 11 were incidental compound-word/
      filename false positives, now cleared) have a genuine bare/unqualified `DEFERRED` mention needing real per-plan
      judgment (add a `DEFERRED-<QUALIFIER>` tag if a `f6df716e7`-style qualifier honestly applies, or a
      `## Deferred work — migrated to:` banner naming an actual successor) — do NOT blanket-apply the generic "see
      inline annotations" template to these, it would be false (they don't all carry qualifier tags). List:
      `ao_fleet_observability_kpis_2026_07_20`, `ao_worker_lifecycle_dispatch_context_2026_07_21`,
      `capability_wizard_and_manifest_2026_06_11`, `cefi_ml_directional_continuous_live_2026_06_20`,
      `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20`, `data_completion_to_100_all_ag_2026_06_21`,
      `data_completion_tradfi_2026_07_15`, `data_feed_sla_registry_and_active_self_healing_2026_06_19`,
      `data_status_tab_and_downloads_remediation_2026_06_16`, `features_service_e2e_pipeline_test_2026_05_26`,
      `features_sports_service_consolidation_deploy_2026_07_15`,
      `instruments_mtds_subset_consistency_remediation_2026_06_17`,
      `master_data_canonicalisation_migration_catalogue_2026_06_07`, `master_to_live_defi_2026_05_23`,
      `migration_verification_orphan_safety_2026_06_10`, `mtds_file_size_refactor_2026_06_08`,
      `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05`,
      `prediction_venue_perps_and_live_clob_depth_2026_06_20`, `sports_manifest_canonicalisation_2026_06_01`. (repo:
      unified-trading-pm) — `unified-trading-pm@0c51e381a` + `@885a1410b` + `@b3c486381` + `@5225b4a08` (4 parallel
      sub-agent batches of 5/5/5/4 plans, no file overlap). Real per-plan judgment throughout, no blanket-closing —
      banner types used per plan: **named-successor** (a real active plan/epic identified, e.g.
      `sports_manifest_canonicalisation_2026_06_01` → `data_completion_to_100_all_ag_2026_06_21` after tracing through
      an archived intermediate; `data_feed_sla_registry_and_active_self_healing_2026_06_19` →
      `aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03`), **resolved-in-place** (the DEFERRED text described a finding
      whose fix had already shipped later in the SAME doc — several hits in `data_completion_to_100_all_ag_2026_06_21`
      and `features_service_e2e_pipeline_test_2026_05_26`), **qualifier-tag-pointer** (the established `f6df716e7`
      precedent banner, for plans genuinely dominated by formal `DEFERRED-<QUALIFIER>` tags, e.g.
      `master_to_live_defi_2026_05_23`'s ~100+ tagged hits; `prediction_venue_perps_and_live_clob_depth_2026_06_20`'s
      `DEFERRED-CROSS-DEP` — that plan was split + archived 2026-07-24 per the plan line-cap remediation, the
      `DEFERRED-CROSS-DEP` item now lives in `plans/active/prediction_live_clob_depth_capture_2026_07_24.md`), and
      **not-yet-identified** (honest "no successor exists yet, this plan remains the owner" for genuinely unowned items,
      e.g. `mtds_file_size_refactor_2026_06_08`, `migration_verification_orphan_safety_2026_06_10`) — never fabricated a
      successor that doesn't exist. Verified via
      `.venv/bin/python scripts/quality_gates/check_plan_discipline.py --strict`: **0 violations** (down from the
      19-plan baseline; re-baselined 19 → 0 via `--baseline-write`, closing this entire issue doc — both original todos
      plus every P3 follow-up are now done). (repo: unified-trading-pm)
