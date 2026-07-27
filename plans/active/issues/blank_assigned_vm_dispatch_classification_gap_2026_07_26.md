---
doc_type: issue
title: 58 active docs (198 open todos) have blank `assigned_vm` — never classified LOCAL vs AO-dispatchable
summary: >-
  Auditing the mass-flip of AO-dispatch batch plans (2026-07-26) surfaced a THIRD population beyond "flipped" and
  "correctly `NA`/LOCAL": 58 active docs carry a genuinely blank `assigned_vm:` frontmatter field (not `planning`, not
  `NA` — literally unset), 34 of which still have open todos (198 total). `regen_backlog_from_plan.py` walks BOTH
  `plans/active/*.md` AND `plans/active/issues/*.md` (verified by reading the source, not assumed), so these ARE
  structurally eligible to be picked up the moment `assigned_vm` is set to `planning` — they are sitting outside the
  dispatch pipeline not because they were deliberately scoped LOCAL, but because nobody ever filled in the field. 57 of
  the 58 are `doc_type: issue`; the one `doc_type: plan` is `sports_consolidated_closeout_2026_07_19.md` (37 open
  todos), which almost certainly SHOULD be `NA` to match the established consolidated-closeout hub pattern (ci/ao/infra
  hubs are pure zero-todo digests by design) but was never explicitly set either way. This is a DIFFERENT failure mode
  from the two already-tracked coverage gaps: `ag_closeout_audit_scope_widening_triage_2026_07_26.md` (asset_group:
  infrastructure/meta invisible to the tranche sweep) and the batch-flip naming-convention miss (resolved this session,
  Round 2) — those were docs the audit SAW but scoped out or missed by pattern; these are docs the 9-tranche audit
  likely never even considered a dispatch candidate because their frontmatter doesn't cleanly say "LOCAL" or "AO" either
  way.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao-dispatch, assigned-vm, plan-hygiene, frontmatter, triage, backlog]
related:
  [
    /plans/active/issues/ag_closeout_audit_scope_widening_triage_2026_07_26.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /agent-orchestrator/server/regen_backlog_from_plan.py,
    /plans/PLAN_FORMAT.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: agent_operating_framework_master
assigned_vm: NA
priority: P2
locked_by:
resolved_by:
source: >-
  Found while re-auditing the 2026-07-26 mass-flip's real coverage after an operator challenge ("~600 docs, only ~250
  tasks — sure the sweep ran properly?") — that challenge correctly predicted a real gap; this doc + the batch-flip
  naming-convention miss are the two concrete findings it produced.
execution_scope: local-only
drift_direction: advance-code
depends_on: []
---

# 58 docs with blank `assigned_vm` — 198 open todos never classified

## The 34 docs with open todos (sorted by count)

37 sports_consolidated_closeout_2026_07_19.md (the one `doc_type: plan`) · 30
capability_wizard_gap_discovery_2026_06_11.md · 14 cefi_hl_aster_batch_data_gaps_2026_06_22.md · 12
issue_docs_remediation_sweep_2026_06_02.md · 11 uv_pin_fleet_drift_2026_06_22.md · 11
capability_wizard_analysis_findings_2026_06_11.md · 9 perp_funding_data_semantics_and_cadence_2026_06_16.md · 8
fleet_audit_triad_deferred_followups_2026_06_01.md · 8 e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md · 6
features_service_coverage_and_script_canon_2026_06_10.md · 5
tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md · 5 cve_affected_pinned_deps_remediation_2026_06_18.md · 4
sports_golden_window_attempted_failed_remediation_2026_06_24.md · 4
service_dockerfile_pattern_normalization_2026_06_17.md · 3 plan_hygiene_precommit_and_agentic_resolution_2026_06_10.md ·
3 dp_catalog_not_running_sports_prediction_2026_07_15.md · 3
deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md · 3
data_pipeline_alerts_dp_not_v9_and_rate_limited_false_positives_2026_06_27.md · 2
monitor_jobs_auto_repin_and_alerting_cli_wiring_2026_06_24.md · 2 dp_event_pubsub_delivery_gap_2026_06_22.md · 2
dp_alert_flood_triage_and_monitor_fixes_2026_06_23.md · 2 defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md · 2
cefi_batch_download_oom_crashloop_capture_halt_2026_07_24.md · 1 (each)
tradfi_eu_not_draining_source_axis_drift_2026_06_24.md, tradfi_backfill_oom_remediation_2026_06_24.md,
test_build_index_deterministic_races_on_concurrent_corpus_writes_2026_07_25.md,
strategy_store_split_brain_2026_07_13.md, solana_perp_dex_cull_drift_pacifica_2026_07_16.md,
production_readiness_checklist_file_missing_2026_07_24.md,
playwright_reuse_existing_server_cross_slot_false_results_2026_07_20.md,
plan_reconciler_doc_hygiene_findings_2026_06_17.md,
execution_service_aioresponses_to_adapter_mock_migration_2026_06_23.md,
e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md, defi_code_codex_drift_2026_05_27.md,
aiohttp_cve_2026_34993_vcrpy_deadlock_2026_06_03.md (all `plans/active/issues/`).

**Skew note**: most of these predate 2026-07 (several from 2026-06-01 through 2026-06-24), i.e. they likely predate the
`assigned_vm` field becoming a strictly-enforced required field for issue docs — a plausible root cause for WHY the
field is blank rather than deliberately set, though that doesn't change that real work is sitting unclassified.

**CORRECTION (2026-07-26, same pass)**: `sports_consolidated_closeout_2026_07_19.md` was NOT actually in this population
— the initial `grep -lE '^assigned_vm:\s*$'` detection was a false positive caused by a multi-line YAML value
(`assigned_vm:` on its own line, with `NA # ⛔ DO NOT flip to planning directly (operator ruling 2026-07-23)...` as an
indented continuation line, not a blank scalar). The doc was already correctly `NA` with an explicit, detailed operator
ruling attached — a single-line `grep` for "the value after the colon" cannot see a YAML value that legally lives on the
NEXT line. Caught by `check_frontmatter_schema.py` rejecting a "NA NA" duplicate before anything shipped; the file was
verified back to its original, untouched, correct state (`git diff` clean). **Lesson for whoever re-runs a similar
sweep**: verify blank-`assigned_vm` detections against the actual multi-line YAML parse, not a single-line grep, and
re-check `check_frontmatter_schema.py` passes after any bulk frontmatter edit before shipping.

## Todos

- [x] [REVIEW] P2. ✅ **DONE 2026-07-26.** Classified the 33 genuine docs (34 minus the false-positive
      `sports_consolidated_closeout`) via a cheaper, reliable signal than manual judgment: `execution_scope` was already
      correctly filled in on all of them even though `assigned_vm` was blank (7 `local-only` → set `assigned_vm: NA`; 51
      `orchestrator-agent` → set `assigned_vm: planning`, only 30 of which carry the real 198 open todos, the other 21
      are already fully resolved and just needed the field completed). Verified `check_todo_format.sh` clean (canonical
      `[TAG] P#.` on all open items) and `check_frontmatter_schema.py` clean on the full 57-file set (the 58th,
      sports_consolidated_closeout, needed no change — see correction above). `unified-trading-pm@<pending>`.
- [x] [DOC] P2. ✅ N/A — `sports_consolidated_closeout_2026_07_19.md` was never actually blank (see correction); no edit
      needed.
- [ ] [SCRIPT] P3. Add a hygiene check (`run_hygiene_sweep.sh` or `check_frontmatter_schema.py`) flagging any active
      plan/issue doc with a blank `assigned_vm` as a HARD violation — the field should never be silently absent; `NA`
      and `planning` are both valid, blank is not. This closes the root cause, not just today's backlog. **Extend the
      checker to also catch the multi-line-continuation false-positive shape** found above (a scalar value living on an
      indented line after a bare `key:`), not just a same-line-blank pattern — a naive fix for this todo could itself
      reintroduce the exact bug this correction just fixed.
- [ ] [REVIEW] P2. **The 30 now-`planning`-tagged docs with real open todos still need the standard conflict-check
      against currently-active plans before their content is trusted for dispatch** (per `/ag-closeout-audit`'s own
      Phase-3 methodology) — flipping `assigned_vm` makes them backlog-eligible, it does not itself verify no other
      active plan already covers the same file/ground. Not done in this pass; flagged for the next tranche audit or a
      dedicated follow-up.
