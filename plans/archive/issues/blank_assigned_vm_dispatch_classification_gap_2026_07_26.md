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
status: resolved
nature: issue
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao-dispatch, assigned-vm, plan-hygiene, frontmatter, triage, backlog]
related:
  [
    /plans/archive/issues/ag_closeout_audit_scope_widening_triage_2026_07_26.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /agent-orchestrator/server/regen_backlog_from_plan.py,
    /plans/PLAN_FORMAT.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: agent_operating_framework_master
assigned_vm: planning
priority: P2
locked_by:
resolved_by:
  "unified-trading-pm@e88c41727 (docspec assigned_vm Req.O -> Req.R gate, closes root cause); 57-file classification +
  slot-15 conflict-check annotations landed in-place (2026-07-26/30)"
source: >-
  Found while re-auditing the 2026-07-26 mass-flip's real coverage after an operator challenge ("~600 docs, only ~250
  tasks — sure the sweep ran properly?") — that challenge correctly predicted a real gap; this doc + the batch-flip
  naming-convention miss are the two concrete findings it produced.
execution_scope: orchestrator-agent
assigned_role: infra
drift_direction: advance-code
depends_on: []
---

> **✅ ARCHIVED 2026-07-30** — all 3 todos done (57-file classification, `docspec.py` `Req.R` gate fix
> `unified-trading-pm@e88c41727`, and the shared conflict-check pass over the surviving 13/46-todo population), 0 open
> todos, unlocked. Moved to `plans/archive/issues/`.

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
- [x] [SCRIPT] P3. **DONE 2026-07-30 — unified-trading-pm@e88c41727.** `scripts/docs/docspec.py`'s `issue` doc_type
      `FieldSpec("assigned_vm", ...)` flipped `Req.O` → `Req.R` — `check_frontmatter_schema.py` (already the sole,
      whole-corpus, blocking frontmatter gate) now HARD-fails on a blank/absent `assigned_vm` on any issue doc; `NA` and
      `planning` both still pass (`registry_or_na` validator type unchanged). This closes the root cause via the SAME
      already-existing zero-violations gate, not a new checker — proven live: 4 pre-existing issue docs newly caught
      with a genuinely blank field (none from this doc's own original 58; new arrivals since), all fixed in the same
      change so the corpus stayed at its pre-existing violation count. **Multi-line-continuation false-positive immune
      by construction**: this fix uses `docspec.validate_frontmatter()`'s real `yaml.safe_load` parser (the same one
      `check_frontmatter_schema.py` always used), never a line-based grep, so the exact false-positive class this todo
      warned against (a scalar value on an indented continuation line after a bare `key:`) cannot recur here — it was
      only ever a hazard for a hand-rolled single-line grep, which this fix never introduces.
- [x] ✅ [REVIEW] P2. **DONE 2026-07-30 (slot-15).** Ran the shared conflict-check
      (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) over every doc this sweep
      flipped to `planning` that still carries real open todos. See Progress Log entry below for the full verdict
      breakdown, population-shrinkage correction, and the 6 source docs annotated with supersession notes.

## Progress Log

- **na-eligibility-audit 2026-07-30**: RECLASSIFY → planning, conflict-cleared — the one remaining `[REVIEW] P2` is a
  bounded, mechanical audit with a fixed input set and an SSOT'd procedure: run the shared conflict-check
  (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3) over the 30 docs this doc's own
  sweep flipped to `planning`, and record a per-doc clear/conflict verdict. Outcome determinable by the worker alone; no
  operator authority involved. Its 3 sibling todos are already `[x]`, including the root-cause gate fix
  (`unified-trading-pm@e88c41727`, `assigned_vm` now `Req.R` for issue docs). **Phase-2 conflict-check**: zero hits for
  a competing claim on this ground anywhere on the active planning surface. CLEAR. Set `assigned_role: infra`,
  `execution_scope: orchestrator-agent`.

- **slot-15 2026-07-30**: Ran the shared conflict-check (§ 3 above) over the population. **Population correction
  first**: re-derived the "30 docs" list from this doc's own 2026-07-26 candidate set (34 docs with open todos at that
  time, minus the sports false-positive) and checked LIVE current state, not the stale snapshot — in the 4 days since,
  the fleet independently drained 17 of those 34 to archived/resolved, 2 back to `assigned_vm: NA`, and 2 down to zero
  open todos. **Real remaining population: 13 docs / 46 open todos** (not 30/198) — a healthy sign the backlog is
  actively shrinking, not stale.

  Ran the conflict-check on all 13 (5 parallel investigation sub-agents by `parent_epic` group + 2 done directly).
  **Verdict tally**: 32 of 46 todos **CLEAR** (no overlap, safe for dispatch); **11 CONFLICT** (another currently-active
  doc already claims the same ground — real duplicate-dispatch risk if left unflagged); **2 STALE-DONE** (already
  shipped elsewhere, checkbox never flipped); **1 CLEAR-with-flag** (no duplicate claim, but an unretracted
  contradictory note elsewhere worth an operator nod before scoping). Annotated all 14 non-CLEAR todos in place, in
  their 6 source docs, with a `SUPERSEDED`/`STALE-DONE`/`PARTIAL-STALE` note citing the specific other doc/commit —
  never checked a box that wasn't actually done, per the protocol's "never resolve a conflict by guessing which claim
  should win."

  **Per-doc breakdown** (parent_epic in parens):
  - `cefi_hl_aster_batch_data_gaps_2026_06_22.md` (mtds_mdps_master, 6 todos): 4 clear, 1 CONFLICT (Slack-parity codex
    fix already extracted verbatim into `cefi_satellite_ao_dispatch_batch3_2026_07_26.md`, which cites this doc as its
    own source), 1 PARTIAL-STALE (the `perp_funding=0` sub-claim for HL/ASTER is by-design since the 2026-07-08
    `PerpFundingHandler` retirement, not a bug — the `futures_chain`/`options_chain`/`ohlcv_1m` sub-claims stay open).
  - `perp_funding_data_semantics_and_cadence_2026_06_16.md` (mtds_mdps_master, 11 todos): 9 clear, 2 CONFLICT — the
    "Backfill Aster perp funding" todo instructs running a launcher
    (`launch-mtds-perp-funding-backfill-vm.sh --perp-protocols aster`) RETIRED 2026-07-08 (would write false
    `attempted_failed` rows); the correct, currently OPERATOR-BLOCKED ground is
    `aster_perp_funding_backfill_stale_launcher_and_genesis_conflict_2026_07_28.md` (BLK-a94f446d, 3-way genesis-date
    ambiguity). The genesis rollup todo restates one of the 3 disputed dates as settled — annotated, not blocking (its
    other sub-legs stay clear).
  - `capability_wizard_analysis_findings_2026_06_11.md` (strategy_master, 5 todos): all CLEAR.
  - `e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md` (strategy_master, 2 todos): all CLEAR (one is an
    operator-ruled DEFERRED-BY-DESIGN item — gated, not conflicted).
  - `fleet_audit_triad_deferred_followups_2026_06_01.md` (infrastructure_master, 6 todos): 4 clear, 1 already
    self-annotated parked (Tardis paid-key item — no edit needed, doc already notes the paid backfill is
    dispatched/in-progress elsewhere), 1 STALE-DONE (B2 codex marker reconciliation already shipped in both cited codex
    files per `issue_docs_remediation_sweep_2026_06_02.md:375` — narrowed to the real residual, a 3-doc set still
    untouched).
  - `features_service_coverage_and_script_canon_2026_06_10.md` (infrastructure_master, 6 todos): 2 clear, 4 CONFLICT — 2
    already self-annotated RESCOPED (no edit needed), 2 newly annotated (the `--cov` crash fix + harness relocation are
    both already bundled in `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`; the fleet-wide script-homes
    sweep is claimed by BOTH `repo_scripts_governance_audit_2026_06_18.md` and that same batch1b plan).
  - `cve_affected_pinned_deps_remediation_2026_06_18.md` (infrastructure_master, 4 todos): 1 clear, 3 CONFLICT — all
    three (alerting-service test investigation, pip-floor bump, cryptography/idna re-check) are already claimed in
    `infra_satellite_ao_dispatch_batch1_2026_07_26.md`.
  - `dp_catalog_not_running_sports_prediction_2026_07_15.md` (instruments_master, 1 todo): CLEAR.
  - `deployment_ui_smoke_failures_daily_costs_nav_mobile_2026_07_21.md` (deployment_and_user_management_master, 1 todo):
    STALE-DONE — the nav-menu-dedup fix already shipped + archived
    (`plans/archive/issues/deployment_ui_fleet_git_nav_entry_regression_2026_07_28.md`, `deployment-ui@067f7cd`/
    `258986d`); this doc's own checkbox was simply never flipped (out of THIS task's scope to fix — flagging for whoever
    next touches that doc).
  - `defi_pool_chain_collision_curve_balancer_gap_2026_07_21.md` (defi_master, 1 todo): CLEAR.
  - `solana_perp_dex_cull_drift_pacifica_2026_07_16.md` (defi_master, 1 todo): CLEAR.
  - `defi_code_codex_drift_2026_05_27.md` (defi_master, 1 todo): CLEAR-with-flag — annotated (no competing claim, but an
    unretracted contradictory classification note in a sibling doc worth a quick operator nod before scoping).
  - `tradfi_backfill_oom_remediation_2026_06_24.md` (tradfi_master, 1 todo): CLEAR.

  **Net**: the conflict-check protocol earned its keep — without it, 11 todos across 5 docs would have risked
  double-dispatch (duplicate agent work on ground already claimed by an active AO-dispatch batch plan), and 2 more would
  have re-run already-shipped fixes. Sub-agent methodology: 5 parallel Explore-type read-only investigation agents, one
  per `parent_epic` group (mtds_mdps_master done directly by this session; strategy_master, infrastructure_master,
  instruments+deployment, defi+tradfi each their own agent), each running the same 4-step protocol and reporting
  per-todo verdicts; this session synthesized + applied the annotations. `unified-trading-pm@<pending>`.
