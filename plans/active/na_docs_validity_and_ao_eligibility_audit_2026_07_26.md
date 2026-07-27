---
doc_type: plan
title: >-
  Audit the ~444 `assigned_vm: NA` active docs — validity-check, reclassify AO-eligible content into satellite batches,
  re-verify total coverage
summary: >-
  Scoped 2026-07-26 per operator directive, for a FUTURE session (not this one). The 2026-07-25/26 `/ag-closeout-audit`
  9-tranche run + this session's mass-flip only ever acted on ORPHANED docs (no active plan covering them) — it never
  re-examined the ~450 already-`assigned_vm: NA` docs' individual content, since those are "owned" (an active LOCAL plan
  already exists), not orphaned, by the skill's own definition. Sampling that population this session found it is a
  genuine MIX: correctly-scoped human/design work (majority, expected), real stale bloat (`v2_engine_venue_buildout` has
  a `DECOMMISSIONED — BLOCKED-OPERATOR-DECISION` item still sitting as an open checkbox instead of closed;
  `org_migration_to_odumresearch` is correctly `status: paused` and NOT actually a gap), and — the population this plan
  exists to find — genuinely AO-eligible bounded work that was simply defaulted to NA and never mined. This plan is the
  systematic version of that sampling: per-doc validity audit + reclassification, not another orphan sweep (orphan
  sweeps are already correctly excluding this population by design).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, assigned-vm, plan-hygiene, validity-audit, reclassification, ag-closeout-audit, orphan-detection]
related:
  [
    /plans/active/issues/blank_assigned_vm_dispatch_classification_gap_2026_07_26.md,
    /plans/active/issues/ag_closeout_audit_scope_widening_triage_2026_07_26.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/task_template.md,
    /plans/PLAN_FORMAT.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 12
estimate_calibrated_ai_days: 14.4
assigned_role: backend_engineer
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  Operator directive 2026-07-26, immediately after this session's mass-flip work surfaced (a) a naming-convention miss
  in the first flip pass, (b) 58 docs with a genuinely blank assigned_vm never classified either way, and (c) the
  structural question of why ~1,780 open todos still sit in already-active assigned_vm:NA docs post-audit. Operator
  explicitly scoped this as NEXT-session work, and explicitly chose the LOCAL/human track over AO-dispatched when asked
  (2026-07-26).
drift_direction: advance-code
---

# Audit the ~444 `assigned_vm: NA` docs for validity + AO-eligibility

> **Why this is its own plan, not a continuation of tonight's mass-flip**: the mass-flip (and the `/ag-closeout-audit`
> runs before it) operate on ORPHANED docs — those with no active plan already covering their remaining work. An
> `assigned_vm: NA`, `status: active` doc is, by definition, NOT orphaned (it has an owner: itself) — the orphan-sweep
> correctly never touches it. This plan is a DIFFERENT question: "is this doc's OWN `NA` self-classification still
> correct, and is its content still true?" That is real per-doc judgment work — hence LOCAL, per the operator's explicit
> choice when asked (2026-07-26) — not a mechanical sweep to hand to AO blind.

## Numbers as of 2026-07-26 (re-verify at session start — they will have moved)

- ~451 docs currently `assigned_vm: NA`, ~1,780 open todos across them (vs. ~592 now `planning`-tagged after tonight's
  two mass-flip rounds + the blank-`assigned_vm` classification pass).
- 444 of those 451 are in a LIVE status (`open`/`active`) — only ~2 are `status: paused`/correctly excluded already; the
  rest are the real audit population.
- 2 concrete stale-bloat examples already found this session (do NOT re-derive, just apply):
  `v2_engine_venue_buildout_2026_06_15.md` (32 open todos, split into 5 AO children 2026-07-13, parent has ≥1 stale
  `DECOMMISSIONED` item still open) and `org_migration_to_odumresearch_2026_06_07.md` (27 todos, `status: paused` since
  2026-07-12 — confirmed NOT a gap, correctly excluded already, exclude from re-audit).
- Separately-tracked, adjacent gaps NOT to duplicate here: `ag_closeout_audit_scope_widening_triage_2026_07_26.md` (~44
  remaining `asset_group: infrastructure`/`meta` docs never swept by any tranche) and the 30 docs this session's
  `blank_assigned_vm_dispatch_classification_gap_2026_07_26.md` just flipped to `planning` (those 30 still need the
  standard conflict-check before their todos are trusted for dispatch — fold that check into Phase 2 below rather than
  re-doing it separately).

## Phase 0 — Tooling (re-verify before trusting, don't re-derive from scratch)

- [ ] [SCRIPT] P1. **Fix the blank/NA detection script's known false-positive** before running any bulk sweep: a
      single-line `grep -lE '^assigned_vm:\s*$'` misses a multi-line YAML value (key on its own line, value on an
      indented continuation line — found live on `sports_consolidated_closeout_2026_07_19.md` this session, caught only
      by `check_frontmatter_schema.py` rejecting a duplicate before it shipped). Parse frontmatter properly (PyYAML on
      the extracted `---...---` block) rather than line-grepping for this and every future sweep.
- [ ] [SCRIPT] P2. Generate the current, re-verified list of `assigned_vm: NA` + `status` ∈ {active, open} docs, split
      by which of the 9 tranches (cefi/defi/tradfi/prediction/sports/cross-cutting/ao/ci/infra) each belongs to — reuse
      `/ag-closeout-audit`'s now-fixed (2026-07-26) membership rule (sweeps `asset_group: infrastructure`/`meta` too,
      not just `cross-cutting`).

## Phase 1 — Per-tranche validity + classification audit (the real work — read every doc end-to-end, not checkbox counts)

For EACH of the 9 tranches, read every `assigned_vm: NA` doc belonging to it (per Phase 0's list) and, per doc, record
one of four verdicts with evidence:

1. **KEEP-NA, valid** — genuinely human/design/judgment work, content still accurate. No action.
2. **KEEP-NA, stale items** — some open checkboxes are superseded/decommissioned/already-done-elsewhere (like
   `v2_engine_venue_buildout`'s pattern) — close those specific items with evidence, doc stays NA otherwise.
3. **RECLASSIFY → planning** — the doc's remaining open work (in whole or in part) is bounded/deterministic-outcome and
   was simply defaulted to NA, never actually assessed. Extract into Phase 2.
4. **ARCHIVE** — fully resolved or fully moot (like a stale `org_migration`-shaped doc), 6-step archival ritual.

- [ ] [REVIEW] P2. cefi tranche — audit all `assigned_vm: NA` cefi-tagged docs per the 4-verdict rubric above.
- [ ] [REVIEW] P2. defi tranche — same.
- [ ] [REVIEW] P2. tradfi tranche — same.
- [ ] [REVIEW] P2. prediction tranche — same.
- [ ] [REVIEW] P2. sports tranche — same (note: `sports_consolidated_closeout_2026_07_19.md` is explicitly OUT of scope
      here — it already carries a 2026-07-23 operator ruling to stay NA, verified this session, do not re-open).
- [ ] [REVIEW] P2. cross-cutting tranche — same.
- [ ] [REVIEW] P2. ao tranche — same.
- [ ] [REVIEW] P2. ci tranche — same.
- [ ] [REVIEW] P2. infra tranche — same.

**Done when** (per tranche): every `assigned_vm: NA` doc in that tranche has a recorded verdict + evidence, either
inline in the doc itself (Progress Log entry) or in a per-tranche audit-results doc under `plans/audit/results/`.

## Phase 2 — Consolidate RECLASSIFY findings into AO-eligible satellite batches

- [ ] [DOC] P2. Per tranche, for every doc/todo verdicted RECLASSIFY in Phase 1: run the SAME conflict-check methodology
      `/ag-closeout-audit` already uses (against every currently-active plan + this session's newly flipped batches)
      before drafting, then extract into a new (or the tranche's next-numbered) satellite `_ao_dispatch_batchN` + gated
      `_finalize` pair — canonical `task_template.md` AO frontmatter (`assigned_vm: planning`,
      `execution_scope: orchestrator-agent`, `parent_epic`, `assigned_role`, 10-100 todos, `[TAG] P#.` format),
      `status: draft` until explicitly flipped (same ask-before-creating discipline as tonight).
- [ ] [REVIEW] P2. **Fold in the standing debt from tonight's own work**: the 30 docs
      `blank_assigned_vm_dispatch_classification_gap_2026_07_26.md` flipped to `assigned_vm: planning` still need this
      same conflict-check before their content is trusted for dispatch — do not re-audit them from scratch, just run the
      conflict-check step against them here.

## Phase 3 — Re-run the orphan-detector to verify total coverage

- [ ] [REVIEW] P1. Run `/ag-closeout-audit all` across all 9 tranches AFTER Phase 1+2 land. **Done when**: the orphan
      count for every tranche reflects the post-reclassification corpus (docs archived in Phase 1 no longer appear; docs
      reclassified to `planning` in Phase 2 are correctly excluded as "covered"; nothing NEW shows up as orphaned that
      wasn't already known). Compare against tonight's baseline orphan counts per tranche (recorded in
      `ag_closeout_audit_rollout_2026_07_25.md`'s Round 6/7 sections) to confirm real movement, not just re-measuring
      the same numbers.

## Phase 4 — Final QA on everything this plan touched

- [ ] [SCRIPT] P2. Run `check_frontmatter_schema.py`, `check_todo_format.sh`, and `check_line_caps.sh` across every doc
      touched or created in Phases 1-2 (archived docs, reclassified docs, new batch/finalize pairs). Fix anything red
      before considering this plan done — same standard this session held itself to on every commit.
- [ ] [SCRIPT] P3. Verify every new/touched doc carries correct tags per its tranche (`asset_group`, `stage`, `tags`)
      and is listed in its tranche's consolidated-closeout Sources — a doc that's been reclassified but not added to its
      tranche's Sources list is exactly the "orphan invisible to the sweep" bug this session already fixed twice (entry
      #18/#25 in `autonomous_session_operator_decisions_2026_07_25.md`) recurring in a new form.
- [ ] [DOC] P3. Update this plan's own Progress Log with final tallies (docs archived / reclassified / kept-NA /
      stale-items-closed, per tranche), matching the Round-N summary discipline
      `ag_closeout_audit_rollout_2026_07_25.md` already established.

## Codex / SSOTs to read before starting

- `plans/active/task_template.md` §1-4 (LOCAL vs AO track, AO frontmatter, todo format, AO-dispatched strict rules).
- `cursor-configs/skills/ag-closeout-audit/SKILL.md` (the orphan-detection + conflict-check methodology Phase 1-3 above
  deliberately reuses — this plan generalizes it to an already-owned population, not orphans).
- `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md` § "Dispatch-scope eligibility" (the
  determinable-outcome-by-the-worker-alone bar for what may move to `planning` in Phase 2).

## Progress Log

- **2026-07-26** — Scoped by operator directive for a future session, immediately after this session's mass-flip (30
  draft batch/native_ao_extract plans flipped across 2 rounds) + the blank-`assigned_vm` classification pass (57 docs,
  198 todos surfaced) revealed the deeper structural gap this plan exists to close. Operator explicitly chose the
  LOCAL/human track (not AO-dispatched) when asked. Not started.

- **2026-07-27 — Phase 1 executed same-night (operator override via `/autonomous`, not deferred to next session as
  originally scoped).** 9 parallel read-only sub-agents (one per tranche: cefi/defi/tradfi/prediction/sports/meta +
  cross-cutting split into 3 batches) classified all 142 `doc_type:plan`, `assigned_vm:NA` docs with open todos (1,202
  todos total; `sports_consolidated_closeout` and this plan itself pre-excluded). Full per-doc verdict tables are in
  each sub-agent's transcript (not reproduced here in full to respect the line cap) — this entry is the durable
  summary + every actionable finding.

  **Headline finding: the population splits into three very different shapes, not one.**
  1. **Genuine KEEP-NA** (majority, ~95 of 142 docs) — real, dated, evidenced exclusions: explicit operator rulings
     (`BLK-*` codes), machine `depends_on`+`gate_on_depends` gates on still-open prerequisites, `status: paused`,
     hard-stops (wallet keys, kill-switch, prod-bucket deletes without §3a qualification), or genuinely open-ended
     design/research work. These are NOT defaults — almost every one cites a specific date/ruling/gate.
  2. **RECLASSIFY but ALREADY-DUPLICATED** (the largest surprise, ~35 docs) — the doc's own remaining open checkboxes
     describe work that this session's OWN earlier satellite-batch drafting (batch1-6 across all 9 tranches, shipped
     hours earlier tonight) already extracted verbatim into an active `assigned_vm: planning` doc. The source doc's
     checkboxes were simply never flipped `[x]` to cite the extraction. Flipping these source docs' `assigned_vm`
     directly would dispatch DUPLICATE AO todos for work already queued or done — explicitly NOT done this pass.
     **Follow-up needed** (not yet executed): a stale-checkbox correction sweep citing the extracting batch doc, tranche
     by tranche. Docs in this bucket (source doc → extracting batch, non-exhaustive, see sub-agent transcripts for full
     evidence): `mtds_retry_safe_default_audit_2026_07_14` → batch1b; `l0_doc_index_generator_2026_06_24` → infra
     batch1; `agent_orchestrator_alert_channel_cleanup_2026_07_13` → infra batch1;
     `data_feed_sla_registry_and_active_self_healing_2026_06_19` → batch2; `instruments_completion_tracker_2026_07_06` /
     `mtds_venue_backfill_and_ops_hardening_residuals_2026_07_24` /
     `instruments_store_cf_canonicalization_single_walk_2026_07_24` / `data_source_provenance_enforcement_2026_07_24` /
     `data_completion_to_100_all_ag_2026_06_21` / `instruments_mtds_consistency_remediation_residuals_2026_07_24` /
     `legacy_bucket_dual_write_decommission_2026_07_24` / `instruments_foundation_phase0_cross_cutting_2026_07_24` /
     `pipeline_mode_source_batch_live_replay_standardisation_2026_06_05` /
     `infra_ops_residual_migration_verification_2026_07_24` / `repo_scripts_governance_audit_2026_06_18` /
     `data_status_tab_and_downloads_remediation_2026_06_16` → cross-cutting batch1/batch1b;
     `data_pipeline_ag_residual_backfill_decisions_2026_07_24` / `data_pipeline_alert_substrate_residual_2026_07_24` /
     `instrument_record_schema_completeness_extra_forbid_2026_07_18` / `ui_build_warm_cache_2026_06_17` /
     `colocated_feature_pipeline_in_memory_handoff_2026_06_21` / `bucket_estate_consolidation_closeout_2026_07_24` →
     cross-cutting batch2; `sports_canonical_universe_and_apifootball_reference_expansion_2026_06_24` /
     `sports_fixtures_browser_single_catalogue_source_2026_07_24` (partial) /
     `sports_odds_feature_naming_canonicalization_2026_07_21` / `sports_odds_bookmaker_coverage_enumeration_2026_06_20`
     (partial) / `sports_prelaunch_cf5_verify_residual_2026_07_24` (partial) → sports batch2/batch5;
     `instruments_tradfi_g1_g5_gate_execution_2026_07_24` (partial) /
     `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08` / `tradfi_phase_d_terminal_gate_2026_07_24`
     (partial) / `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24` (partial) /
     `tradfi_multisource_backfill_2026_06_22` / `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20` /
     `tradfi_backfill_throughput_followups_2026_07_24` / `data_completion_tradfi_2026_07_15` → tradfi batch1/2/4;
     `market_tick_data_service_lending_instrument_type_historical_restamp_2026_07_24` /
     `data_completion_defi_2026_07_15` (partial) / `defi_migration_audit_log_2026_07_24` (partial) /
     `defi_track01_per_instrument_and_canon_id_2026_07_24` (partial) /
     `defi_dedicated_bucket_shared_migration_2026_07_13` / `lst_rate_honest_coverage_2026_07_21` → defi batch1/2/3;
     `prediction_cross_venue_arb_and_coverage_2026_07_24` / `prediction_phase_ab_residuals_2026_07_24` /
     `prediction_live_clob_depth_capture_2026_07_24` / `prediction_phase_d_formal_smoke_and_backfill_2026_07_24` /
     `predictions_ml_walk_forward_and_arb_2026_06_20` / `prediction_capture_incident_remediation_2026_07_06` →
     prediction batch1/2/4/5/native-extract; `data_pipeline_alerts_batch_remediation_2026_07_15` → already-closed tradfi
     doc + an issue doc; `github_actions_staging_machinery_shutdown_2026_07_24` → an issue doc.
  3. **RECLASSIFY, genuinely clean, no conflict** (~16 docs, ~185 todos) — **executed this pass**, see below.

  **Executed: 16 docs flipped `assigned_vm: NA → planning`** (`unified-trading-pm@<pending, see next commit>`), each
  individually verified conflict-free (zero or milestone-only references, not verbatim duplicates) before flipping;
  `execution_scope` corrected to `orchestrator-agent` where stale, 2 docs also flipped `status: draft → active`
  (`is_daily_enum_capture_heal_2026_07_07` — a genuine orphan found via a 2026-06-27 blanket "pause AO dispatch on 19
  active plans" commit, `468a0f580`, that swept it off `planning` for reasons unrelated to its own merits and it was
  never revisited; `mdps_candle_manifest_population_disconnect_2026_07_25`), 5 docs got a missing `assigned_role` filled
  in (`data_engineering` ×4, `infra` ×1): `docker_artifact_registry_cleanup_policy_2026_07_24` (16 todos) ·
  `mtds_available_at_cross_asset_backfill_2026_07_13` (9, also had a genuine `execution_scope`/`assigned_vm` field-drift
  — its own Progress Log records 15+ real AO dispatches already happened under its task ids) ·
  `tradfi_manifest_content_recovery_completion_2026_07_24` (7, flagged unaddressed by 3 PRIOR `/ag-closeout-audit`
  passes) · `is_daily_enum_capture_heal_2026_07_07` (3) · `mdps_candle_manifest_population_disconnect_2026_07_25` (8) ·
  `cefi_deribit_binance_futures_bundle_verification_2026_06_20` (2) ·
  `canonical_id_builder_retrofit_checklist_2026_07_08` (9) · `defi_onchain_derivable_values_and_date_drift_2026_06_20`
  (2) · `defi_pipeline_e2e_and_coverage_validation_2026_06_20` (3) · `data_completion_cefi_2026_07_15` (25, note: ~5 of
  its many todos were partially covered by cefi batch1 — dedup on next pass) ·
  `data_pipeline_check_mdps_features_2026_07_20` (28,
  `depends_on: [candle_canonical_path_migration_execution_2026_07_24]` — flipped together in the same batch) ·
  `candle_canonical_path_migration_execution_2026_07_24` (16) · `deployment_redesign_cherrypicks_2026_07_20` (3) ·
  `bucket_iam_write_protection_per_tier_2026_06_09` (7) · `codex_vs_repo_docs_ssot_audit_2026_06_01` (23) ·
  `mvp_backfill_defi_onchain_v10_2026_06_27` (1, `depends_on: [mvp_catalogue_finalization_v10_2026_06_27]` — verified
  archived/done, not a live block). **Net: ~185 new open todos entered the AO backlog this pass.**

  **Notable KEEP-NA verified, not touched** (selection — full evidence in sub-agent transcripts):
  `ao_fleet_observability_kpis_2026_07_20` (an explicit, dated 2026-07-26 operator ruling defers its one bounded item to
  "whoever picks this up on/after 2026-07-27" rather than an AO batch — genuinely correct, not a default);
  `org_migration_to_odumresearch_2026_06_07` (re-confirmed `status: paused` since 2026-07-12, 0/27 executed);
  `v2_engine_venue_buildout_2026_06_15` (has one known-stale `DECOMMISSIONED` item deliberately left `[ ]` per an
  established "ruled-out, not completed" convention in that doc — NOT a bug, do not "fix" it);
  `deployment_ui_observability_ux_tracker_2026_07_17` ("🟡 TRACKER — DO NOT DISPATCH THIS FILE, EVER" banner);
  `bucket_fold_*` family (2026-07-17 operator ruling: "all 5 folds as HUMAN plans"); `crypto_alpha_research_2026_07_24`
  / `cefi_ml_directional_continuous_live_2026_06_20` (live-trading judgment/wallet-key hard-stops);
  `defi_lending_writer_retire_prerequisite_2026_07_20` (a live, in-progress Session-3 operator WON'T-DO ruling — do not
  touch, another session owns it right now).

  **Cross-cutting process finding**: `ag_closeout_audit_asset_group_comment_grep_blindspot_2026_07_26.md` (filed by the
  prediction sub-agent) documents that `prediction_cqg_residual_2026_07_24` was invisible to 3 prior
  `/ag-closeout-audit` passes purely because its `asset_group` line carries a trailing YAML comment that broke a
  grep-based membership check — the same class of bug as the `assigned_vm` multi-line false-positive found earlier
  tonight. **Any future re-run of a grep-based membership/classification sweep over this corpus should parse frontmatter
  properly (PyYAML), not grep** — this is now the second confirmed instance of the exact failure mode, not a one-off
  (Phase 0's `[SCRIPT] P1` todo above already scopes the general fix; this is the second piece of evidence it needs to
  happen, not a new todo).

  **Next**: stale-checkbox correction sweep for the ~35 already-duplicated docs (bucket 2 above); Phase 2 (the 299
  `doc_type:issue` NA docs, 677 todos) — not yet started.
