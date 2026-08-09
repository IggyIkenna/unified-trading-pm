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
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ao-dispatch, assigned-vm, plan-hygiene, validity-audit, reclassification, ag-closeout-audit, orphan-detection]
related:
  [
    /plans/archive/issues/blank_assigned_vm_dispatch_classification_gap_2026_07_26.md,
    /plans/archive/issues/ag_closeout_audit_scope_widening_triage_2026_07_26.md,
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
context_scope:
  [
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/task_template.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
    scripts/plan-hygiene/generate_na_doc_tranche_inventory.py,
  ]
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

- [x] ✅ [SCRIPT] P1. **Fix the blank/NA detection script's known false-positive** before running any bulk sweep: a
      single-line `grep -lE '^assigned_vm:\s*$'` misses a multi-line YAML value (key on its own line, value on an
      indented continuation line — found live on `sports_consolidated_closeout_2026_07_19.md` this session, caught only
      by `check_frontmatter_schema.py` rejecting a duplicate before it shipped). Parse frontmatter properly (PyYAML on
      the extracted `---...---` block) rather than line-grepping for this and every future sweep. **DONE 2026-07-27 —
      unified-trading-pm@ea3456087** — promoted `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` (PyYAML
      frontmatter parse), fixing this exact P1 todo (per this doc's own 2026-07-27 Progress Log entry).
- [x] ✅ [SCRIPT] P2. Generate the current, re-verified list of `assigned_vm: NA` + `status` ∈ {active, open} docs,
      split by which of the 9 tranches (cefi/defi/tradfi/prediction/sports/cross-cutting/ao/ci/infra) each belongs to —
      reuse `/ag-closeout-audit`'s now-fixed (2026-07-26) membership rule (sweeps `asset_group: infrastructure`/`meta`
      too, not just `cross-cutting`). **DONE 2026-07-27 — unified-trading-pm@ea3456087** — same commit shipped
      `generate_na_doc_tranche_inventory.py` and reported the resulting fresh count (389 docs / 127 zero-open-todo), per
      this doc's own 2026-07-27 Progress Log entry.

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

> **Status as of 2026-07-27: the 9 checkboxes above stay honestly unflipped — real work happened in every tranche, but
> not to this section's own "every NA doc" bar, so flipping them would overclaim.** What actually ran (2026-07-27, same
> session): 19 parallel sub-agents (9 for `doc_type:plan`, 10 for `doc_type:issue`) verdicted every NA doc that had ≥1
> open todo — 142 plan docs + 214 issue docs, 356 total — across all 9 tranches, with cefi/defi/sports/
> cross-cutting/meta getting dedicated per-tranche agents and **tradfi+prediction combined into one shared agent** (11
> docs — the smallest 2 tranches, judged low-enough-volume to combine; not yet re-verified this was sufficient depth vs.
> a dedicated pass each) and **ao/ci folded into the cross-cutting/meta batches** rather than getting their own
> dedicated split. Docs with **zero open todos** were never in scope at all (nothing to reclassify), which is why ~444
> NA docs existed but only 356 got a verdict. The gap: **~314 of the ~451 original NA docs never got individual
> attention this session** (444 live-status minus 356 covered, plus a handful of already-excluded paused/false-positive
> docs) — some genuinely have 0 open todos (correctly out of scope), but that hasn't been confirmed doc-by-doc, only
> inferred from the corpus-wide grep. Two concrete follow-ups, not yet started:

- [x] [REVIEW] P2. **DONE 2026-07-27 — tradfi/prediction/ao/ci each got a genuinely DEDICATED classification agent** in
      the fresh `/ag-closeout-audit all` run (see Phase 3 entry below), directly answering this spot-check rather than
      inferring from finding-density. Result: prediction's combined-pass depth was NOT the problem — all 13 prediction
      candidates turned out to be already-covered (see below), a stronger and more specific finding than a density
      comparison would have produced.
- [x] [REVIEW] P2. **DONE 2026-07-27 — the "~314" figure was an arithmetic error in this plan's own prior-session
      notes**, not a real gap: `444 - 356 = 88`, never 314 (neither `444` nor `451` minus `356` produces 314 under any
      reading). Rebuilt the sweep with `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` (proper PyYAML
      frontmatter parse, fixing this plan's own Phase 0 P1 todo) — found and fixed a REAL instance of the predicted bug
      class along the way: a `* [ ]` star-bullet checkbox (vs. the regex's `- [ ]`-only assumption) was invisible to the
      original sweep, hiding one genuine open todo in `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md`
      (confirmed corpus-wide: only 2 files use the star variant, the other — `crypto_alpha_research_2026_07_24.md` — was
      already correctly KEEP-NA'd for an unrelated wallet-key reason). Current honest count (2026-07-27): 389 total
      `assigned_vm:NA`+active/open docs, 127 with zero open todos — mostly hub/digest docs (`*_consolidated_closeout_*`,
      `active_plan_inventory_dashboard`) and already-reviewed KEEP-NA judgment docs, not silently-excluded candidates.

## Phase 2 — Consolidate RECLASSIFY findings into AO-eligible satellite batches

> **Status as of 2026-07-27: overtaken by Phase 3's actual result, not executed as originally scoped.** This phase
> assumed a large RECLASSIFY yield (40-60/AG, per `/ag-closeout-audit`'s own historical batches) needing satellite-batch
> consolidation to stay under the line-cap. The fresh Phase-3 run below found only 3 genuine new AO-eligible orphans
> total across all 9 tranches — small enough to reclassify each directly (issue docs, exempt from the finalize-gate), no
> batch-doc machinery needed. Leaving both todos below open for the ORIGINAL scale scenario (a future
> `/ag-closeout-audit` batchN run against a specific AG finding a real 40-60-doc yield), not deleting them.

- [ ] [DOC] P2. Per tranche, for every doc/todo verdicted RECLASSIFY in Phase 1: run the SAME conflict-check methodology
      `/ag-closeout-audit` already uses (against every currently-active plan + this session's newly flipped batches)
      before drafting, then extract into a new (or the tranche's next-numbered) satellite `_ao_dispatch_batchN` + gated
      `_finalize` pair — canonical `task_template.md` AO frontmatter (`assigned_vm: planning`,
      `execution_scope: orchestrator-agent`, `parent_epic`, `assigned_role`, 10-100 todos, `[TAG] P#.` format),
      `status: draft` until explicitly flipped (same ask-before-creating discipline as tonight).
- [x] [REVIEW] P2. ✅ **Fold in the standing debt from tonight's own work**: the 30 docs
      `blank_assigned_vm_dispatch_classification_gap_2026_07_26.md` flipped to `assigned_vm: planning` still need this
      same conflict-check before their content is trusted for dispatch — do not re-audit them from scratch, just run the
      conflict-check step against them here. **DONE (na-eligibility-audit 2026-08-03)** — the cited doc's own 4th todo
      did exactly this before it archived: population re-derived live (30→13 docs/46 open todos after 4 days of
      independent drain), conflict-check run on all 13 (5 parallel investigation sub-agents), verdict tally 32 CLEAR /
      11 CONFLICT / 2 STALE-DONE / 1 CLEAR-with-flag, all 14 non-CLEAR todos annotated in place across their 6 source
      docs — see `plans/archive/issues/blank_assigned_vm_dispatch_classification_gap_2026_07_26.md`'s Progress Log
      "slot-15 2026-07-30" entry for the full per-doc breakdown.

## Phase 3 — Re-run the orphan-detector to verify total coverage

- [x] [REVIEW] P1. **DONE 2026-07-27 — see Progress Log for the full run.** Ran a scoped version of
      `/ag-closeout-audit     all`, not the original done-when's literal baseline-count comparison: a full per-doc
      re-read of the whole ~672-doc corpus was judged infeasible in one session (consistent with this plan's own prior
      two deferrals of this exact item), so built a cheap citation-based pre-filter first
      (`generate_ag_closeout_audit_candidates.py`, shipped `unified-trading-pm@ea3456087`) narrowing 770
      tranche-memberships down to 78 docs never cited by any real covering doc, then dispatched 11 real per-doc
      classification agents (Workflow tool) against exactly that narrowed set — every tranche got its own dedicated
      agent(s), directly closing the tradfi/prediction/ao/ci gap flagged above. Net: 3 genuine new AO-eligible orphans
      reclassified, 3 sibling candidates the agents flagged ao_eligible but were kept NA on review (reasoning in
      Progress Log), 5 archivable_now candidates found and NOT yet archived (new follow-up todo below), and one real
      corpus-quality finding (cross-cutting membership over-broad for ao/ci content sharing `infrastructure_master`)
      logged as a tooling follow-up, not a data bug.
- [x] [REVIEW] P2. **DONE 2026-07-27 — 35 of the 37 archivable_now/ARCHIVABLE candidates actually archived**
      (`unified-trading-pm@bec54efeb` content + `@42d570211` cleanup, see below), per issue-doc-lifecycle.md (33 issue
      docs: status->resolved/superseded + resolved_by evidence + banner + git mv to `plans/archive/issues/`) and the
      fuller plan-archival ritual (2 plan docs: `sports_legacy_bucket_cutover_2026_07_16.md`,
      `github_actions_cost_reduction_options_analysis_2026_07_15.md` -> `plans/archive/2026_07/`, referrers repointed).
      **2 of the original 37 candidates were NOT archived on re-verification** (the mandated "don't trust blind" re-read
      caught real problems): `/plans/archive/2026_07/github_actions_ci_cost_reduction_2026_07_15.md`'s own text
      explicitly says it's "kept only so existing cross-references still resolve" — a deliberate permanent redirect
      stub, not an archival candidate (overrides both this session's and the PRIOR session's `/ag-closeout-audit`
      classification of it); `ao_worker_session_continuity_and_resume_threshold_2026_07_27.md` was found already
      independently archived by a real concurrent AO worker before I got to it — confirms independent convergence on the
      same verdict. A concurrent-agent lint violation (`check_na_corpus_ratchet.py`, part of a live in-flight
      `na-eligibility-audit` skill build, since shipped `unified-trading-pm@f355c0b2a`) blocked the tree-wide QG scan;
      fixed 2 mechanical issues (line-length, import-at-top) without touching that agent's logic or staging its file.
      The archival also broke 26 structured referrer links across 8 consolidated-closeout/sources hub docs
      (`run_validators.py --scope     all` catches this; `check_reference_paths.py` did not — different validators,
      different scope) — all repointed to the new archive paths in the same commit. **Real defect found + fixed
      post-land**: `bec54efeb` landed with the delete-side of all 35 renames silently dropped (repeated stash-restore
      cycles across 10 retry attempts on this one commit — an exceptionally busy branch that night — eventually lost the
      staged deletion half while the archive/-side content landed correctly), leaving 35 stale duplicate copies live in
      `plans/active/` alongside the correct `plans/archive/` copies. Caught by directly diffing `git show <sha> --stat`
      against expectations (a `git log` success message and clean `rev-list` alone were NOT sufficient evidence — this
      is now the standing verification bar for every future quickmerge on a busy branch: check the actual committed
      diff, not just the exit code). 31 of the 35 duplicates fixed via a clean pure-deletion follow-up
      (`unified-trading-pm@42d570211`). **4 duplicates deliberately left unresolved**:
      `manifest_hygiene_red_2026_06_27.md`, `manifest_hygiene_red_2026_06_29.md`,
      `mtds_plan_reconciliation_2026_06_29.md`, `phantom_captures_tradfi_2026_06_28.md` carry a genuine pre-existing
      `locked_by: live-defi-rollout` in their ORIGINAL frontmatter (confirmed real for these 4 specifically, not the
      wider corpus-wide boilerplate coincidence most `locked_by: live-defi-rollout` values are — the
      locked-plan-deletion gate correctly blocked their removal). Per CLAUDE.md, unlocking requires an explicit operator
      `[unlock-plan]` — never autonomous — so both copies (stale `plans/active/issues/` + correct
      `plans/archive/issues/`) currently coexist for these 4 pending that decision. New follow-up todo below.
- [x] [REVIEW] P2. **RETAGGED 2026-07-28 (stale-tag audit — this item's own operator gate already resolved and executed,
      `[OPERATOR]` never removed).** 4 duplicate doc pairs needed an explicit `[unlock-plan]` decision before the stale
      `plans/active/issues/` copy could be removed — unified-trading-pm@0703cb288 (`[unlock-plan]`, operator-granted).
      Verified: all 4 stale `plans/active/issues/` copies removed, `plans/archive/issues/` copies confirmed present and
      correct, 7 live referrers repointed onto the archive path.
- [ ] [SCRIPT] P3. **Widen `generate_ag_closeout_audit_candidates.py`'s cross-cutting membership rule** — currently
      `parent_epic in DATA_EPICS` alone lets ci/infra-scoped docs sharing `infrastructure_master` leak into
      cross-cutting's candidate pool (confirmed: 37 of 40 cross-cutting candidates in the fresh run were genuinely
      ci/infra content, correctly caught by the real Phase-1 agent read, not a data bug — but it means the cheap
      pre-filter itself over-includes for this one tranche pairing). Fix: for `cross-cutting`, additionally require the
      doc is NOT already cited in `ci`/`infra`/`ao`'s own covering docs before counting it as a cross-cutting candidate
      (mirrors the `peer_cited` exclusion already correct in `generate_na_doc_tranche_inventory.py`).
- [ ] [SCRIPT] P2. **Wire `scripts/plan-hygiene/check_na_duplicate_staleness.py` (new, 2026-08-03) into this skill's own
      scheduled cadence** — it currently exists only as a standalone script, invoked by hand. It mechanically flags
      `assigned_vm: NA` docs whose open checkbox is duplicate-tracked by an active `planning` doc (via `Source:`
      citations) where the AO-side copy already shipped `[x]` but the NA-side original was never reconciled — exactly
      the "KEEP-NA-STALE (already-duplicated)" verdict class this skill's own rubric already names, just without a
      mechanical pre-filter. First run found 65 such candidates + 56 more via a looser any-doc-reference check; a
      129-candidate hand-verification pass the same session found roughly a third were genuine closes, the rest false
      positives (citation existed but didn't cover the specific blocked checkbox) — confirming the tool is a candidate
      filter for Phase 1, not an auto-closer. **Done when**: this script's candidate list is read as part of Phase 0 (or
      a new Phase 0.5) on the `na-eligibility-auditor.timer` cadence, so this class of staleness gets caught by the
      existing 2-hourly cron instead of requiring another one-off manual session. the zero-open-todo classification pass
      (99 docs, 7 agents) found 8 genuine `PERMANENT_REFERENCE` docs (correct as-is, no action) and 16 genuine
      `KEEP_NA_VALID` (correct as-is), but also 24 `RECLASSIFY_CANDIDATE` (real, bounded, worker-determinable remaining
      work stated only as numbered prose, never given a checkbox — a stronger signal than plain conversion) and 19
      `NEEDS_CHECKBOX_CONVERSION` (real remaining work in prose, AO-eligibility not yet assessed). Neither bucket was
      executed this pass — converting prose to checkboxes is real editorial judgment per doc (exact wording,
      `[TAG] P#.`, done-when clause), the same care applied to the 6 orphan candidates above, not a mechanical batch op.
      RECLASSIFY_CANDIDATE (24): `ag_closeout_audit_asset_group_comment_grep_blindspot_2026_07_26`,
      `ao_m3_verify_plan_flip_blind_to_archival_rename_2026_07_26`,
      `blocking_gcs_writes_on_event_loop_cross_asset_group_2026_07_18`,
      `cefi_available_at_wallclock_despite_deterministic_row_timestamp_2026_07_24`,
      `cefi_backfill_per_day_catalogue_reload_2026_07_20`, `defi_citation_ratchet_tabs_path_exclusion_bug_2026_07_21`,
      `defi_lst_oracle_timestamp_glued_instrument_id_2026_07_20`,
      `defi_venue_phase_live_definition_contradiction_2026_07_22`,
      `digest_drift_sweep_silent_noop_github_token_scope_2026_07_16`, `fixtures_manifest_legacy_backfill_2026_07_24`,
      `host_root_disk_full_transient_2026_07_13`, `kalshi_live_capture_regression_and_drift_2026_07_13`,
      `lst_exchange_rate_data_availability_2026_07_21`, `pipeline_smoke_sweep_findings_2026_07_20`,
      `recon_bucket_missing_nightly_recon_failing_2026_07_13`, `rotate_exchange_keys_stale_venue_registry_2026_07_23`,
      `silent_wrong_answer_audit_candidates_2026_07_20`,
      `sports_clv_target_pit_gated_out_of_odds_features_export_2026_07_26`,
      `sports_derived_features_fabricated_corpus_scope_2026_07_20`, `sports_league_id_namespace_migration_2026_07_20`,
      `sports_odds_team_name_alias_gap_south_america_2026_07_09`,
      `sports_peripheral_bucket_league_vocabulary_contamination_2026_07_20`,
      `tradfi_manifest_writer_legacy_id_regression_2026_07_21`,
      `two_agents_slot3_collision_and_yahoo_finance_red_tree_2026_07_15` (all `plans/active/issues/`).
      NEEDS_CHECKBOX_CONVERSION (19): `defi_venue_lst_rates_residual_2026_07_24` (`plans/active/`),
      `aave_rate_impact_structural_zero_defillama_borrow_gap_2026_07_26`,
      `architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16`,
      `cefi_chain_drop_root_cause_and_heavy_io_vm_rule_2026_07_24`,
      `cross_cutting_manifest_canonicalisation_findings_2026_07_11`,
      `dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21`,
      `defi_catalog_engine_config_key_contract_drift_2026_07_23`,
      `defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25`,
      `defi_kalshi_perp_perp_funding_source_not_registered_2026_07_23`,
      `deployment_ui_capability_bundle_stale_drift_pacifica_2026_07_16`,
      `e2e_testing_collateral_validation_dead_import_2026_07_23`,
      `features_onchain_featureless_shards_and_vocabulary_split_2026_07_20`, `human_led_audit_pool_2026_05_21`,
      `mtds_backfill_vm_startup_oom_rc137_2026_07_14`,
      `mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23`,
      `onchain_manifest_dishonest_and_recompute_blocked_2026_07_21`, `phantom_audit_estate_coverage_gap_2026_07_10`,
      `plan_issue_epic_consolidation_2026_06_30`,
      `sports_odds_naming_migration_uncommitted_wip_and_checkbox_drift_2026_07_25` (all `plans/active/issues/` unless
      noted). Full per-doc reasoning in the workflow journal (`wf_f263f118-37a`, `whqfflv82.output`) — do not re-derive
      verdicts, re-read each doc against its own cited evidence before converting.
- [x] [SCRIPT] P2. **DONE (2026-08-03) — re-ran `check_na_duplicate_staleness.py`'s candidate list (65 dup-stale + 57
      plain-stale = 122 unique docs) and hand-verified every item with 10 parallel agents (one crashed mid-run on a
      transient API error, retried clean).** Result: 8 checkboxes closed across 6 docs
      (`sports_odds_feature_naming_canonicalization_2026_07_21` ×3, `lst_rate_honest_coverage_2026_07_21` [see the
      line-cap blocker below — closed in-session but reverted before commit],
      `ao_orphan_audit_followup_triage_2026_07_30`, `batch_live_recon_cloud_run_job_stage0_never_succeeded_2026_07_30`,
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24`, `reference_path_convention_2026_07_23`), the rest (114
      of 122) confirmed false positives on full-context reading — reaffirms the prior finding that citation-presence
      alone is a weak signal; every close required reading both the flagged checkbox's own surrounding text AND the
      citing task's actual scope, not just checking a `Source:` line exists. Several docs already carried same-dated
      `na-eligibility-audit 2026-08-03` verdict markers from a concurrent process when opened — confirms this class of
      audit is now also running on another schedule/slot in parallel; no conflicting edits resulted since agents
      verified content directly rather than trusting pre-existing markers.
- [ ] [DOC] P2. **`lst_rate_honest_coverage_2026_07_21.md` line 381 (A2 staking leg, `[STRATEGY] P2`) verified DONE**
      (`strategy-service@e93902d8`, cited at `defi_satellite_ao_dispatch_batch3_2026_07_26.md:191`) but the checkbox
      flip could not be committed: the doc is 1017L, over the 1000L hard cap, and the SCOPED-mode small-marker-append
      exception (operator ruling 2026-08-02) requires zero deletions in the staged diff — a same-line `[ ]`→`[x]`
      replace is 1 insertion + 1 deletion, so it does not qualify even though total line count doesn't change. This is
      one of the 4 docs the exception's own docstring already names as chronically stuck
      (`lst_rate_honest_coverage_2026_07_21.md`, `data_completion_to_100_all_ag_2026_06_21.md`,
      `instruments_completion_tracker_2026_07_06.md`, `master_data_canonicalisation_migration_catalogue_2026_06_07.md`)
      — a checkbox flip on any of them hits the same wall. **Done when**: the doc is split/condensed under 1000L (or a
      future operator ruling extends the append-only exception to cover a single same-line checkbox flip specifically),
      then this A2 staking-leg checkbox gets flipped with the evidence above.

## Phase 4 — Final QA on everything this plan touched

- [x] [SCRIPT] P2. **DONE — ran on every batch as it shipped, not deferred to the end.** `check_frontmatter_schema.py`
      (16+16+60+58+1 = 151 docs verified clean across every commit), `check_todo_format.sh` (non-blocking pre-existing
      numbering warnings only, nothing introduced by this pass), `check_line_caps.sh` (one HARD violation caught —
      `instrument_id_format_canonicalization_2026_07_08.md` at 1,309L — fixed via the Phase-3 split, not skipped).
- [x] [SCRIPT] P3. **DONE 2026-07-27 (`unified-trading-pm@665a49d21`).** Grep-checked all 77 reclassified docs against
      their tranche's consolidated-closeout hub: 50 already mentioned somewhere, 27 genuinely NOT — confirming this
      finding's own predicted bug class actually recurred. Root cause split two ways: 1
      (`mdps_odds_horizon_bucket_     reprocess_launch_prep`) needed no fix, already claimed+resolved+archived by a real
      AO worker mid-session; the other 26 got a discoverability-only append (no existing content touched) to their
      tranche's hub — cefi (2), defi (5), sports (4), cross-cutting (4), meta/infrastructure (11, routed to
      `infra_consolidated_closeout` per `ag_closeout_audit_scope_widening_triage_2026_07_26.md`'s own precedent for that
      asset_group pairing). `asset_group`/`tags` on all 77 were already verified correct at classification time (Phase
      1/2), not re-checked here.
- [x] [DOC] P3. **DONE** — final tallies recorded in the 2026-07-27 Progress Log entries above (77 reclassified, 64
      stale-checkbox-corrected, 1 split, live-fleet execution proof for at least 1 of the 77).

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
     evidence): `mtds_retry_safe_default_audit_2026_07_14` (archived →
     `../archive/2026_08/mtds_retry_safe_default_audit_2026_07_14.md`) → batch1b; `l0_doc_index_generator_2026_06_24` →
     infra batch1; `agent_orchestrator_alert_channel_cleanup_2026_07_13` → infra batch1;
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
     `/plans/archive/2026_08/tradfi_multisource_backfill_2026_06_22.md` (archived 2026-08-03) /
     `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20` / `tradfi_backfill_throughput_followups_2026_07_24` /
     `data_completion_tradfi_2026_07_15` → tradfi batch1/2/4;
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

- **2026-07-27 — Phase 2 executed same session, immediately after Phase 1.** 10 parallel read-only sub-agents (cefi
  split ×2, defi, tradfi+prediction combined, sports split ×2, cross-cutting split ×3, meta) classified all 214
  `doc_type:issue`, `assigned_vm:NA` docs with open todos (665 todos total, re-counted fresh — differs slightly from
  Phase 1's earlier 299/677 estimate because several docs had since been archived/resolved by concurrent sessions). Same
  3-verdict rubric as Phase 1, but this population needed a third bucket since issue docs are typically single-finding
  bug reports rather than multi-phase epics: **KEEP-NA** (genuine judgment/operator/credential gate), **KEEP-NA-STALE**
  (content already duplicated verbatim in an active satellite batch — needs a checkbox citation fix, not
  reclassification), **RECLASSIFY** (genuinely bounded, zero or non-competing conflicts).

  **Headline finding: the issue-doc population is FAR richer in genuinely-new AO-eligible content than the plan-doc
  population was.** Roughly 90 of 214 docs verdicted KEEP-NA-STALE (this week's satellite batches already absorbed their
  content, checkboxes just never got flipped — same root cause as Phase 1's bucket 2) and roughly 60-70 verdicted
  genuine KEEP-NA (a disproportionate share of these are AO/orchestrator-infrastructure bug reports —
  `ao_db_lock_storm_and_stuck_shutdown_outage`, `orchestrator_failover_double_dispatch_duplicate_work`,
  `one_shot_worker_completes_but_no_clean_exit_signal_watchdog_rekicks`,
  `reaper_kills_inflight_detached_quickmerge_false_done`, etc. — correctly excluded per an explicit extra-caution
  instruction given to every sub-agent: a wrong fix to the orchestrator's own dispatch/git/state machinery risks
  corrupting the very backlog this audit depends on, so those stay human-reviewed even when a fix "looks mechanical").
  But **~61 docs verdicted genuinely clean RECLASSIFY** (zero or non-competing conflicts) — more than triple Phase 1's
  yield from a similarly-sized population, because issue docs are narrower bug reports that this week's PLAN-level
  satellite-batch drafting simply never reached.

  **Executed: 60 of the 61 clean docs flipped `assigned_vm: NA → planning`**
  (`unified-trading-pm@<pending, see next commit>`) directly, with no companion finalize doc — confirmed via reading
  `check_finalize_plan_coverage.py`'s source that it only globs the top-level `plans/active/*.md`, never
  `plans/active/issues/*.md`, so issue docs are structurally exempt from that gate. One candidate,
  `issues/instrument_id_format_canonicalization_2026_07_08.md`, was otherwise clean but already sits at 1,309 lines
  (pre-existing, not caused by this pass) — over the 1,000-line hard cap — so it was reverted back to `NA` and left for
  a future split-then-reclassify pass rather than blocking the other 60. Full per-doc evidence is in each sub-agent's
  transcript; representative highlights: `cross_ag_instrument_type_casing_100pct_directive_2026_07_24` (blocked only by
  3 docs exceeding the old 1000L cap — since split, the block cleared, nobody re-checked),
  `defi_plasma_chain_onboarding_gap_2026_07_26` (explicitly filed "out of scope here" by an active batch, left genuinely
  undispatched), `mdps_t1_recon_job_oom_failing_7_days_2026_07_26` (first OOM cause already fixed, but a SECOND distinct
  OOM with its own stated investigative approach was never picked up),
  `manifest_reprocessing_generic_utility_2026_07_07` (a ~90%-complete template to generalize, never claimed by any
  batch), `catalogue_census_equivalents_inventory_2026_07_24`
  - `cli_shard_split_flag_coverage_audit_2026_07_24` (both had their main audits shipped, small bounded follow-ups left
    unclaimed).

  **Notable KEEP-NA verified, not touched** (selection): `production_readiness_checklist_file_missing_2026_07_24` (doc's
  own text: "genuinely needs a human decision on which checklist is authoritative");
  `ao_operator_delete_gating_aws_iam_and_corpus_sweep_2026_07_27` (an empirically-verified hard IAM blocker, doc's own
  Final Report: "not a judgment call"); `pnl_interest_accrual_wrong_engine_and_banned_formula_2026_07_21` (money-path
  NAV change under repeated operator rulings); `defi_archetype_universe_no_curtailment_mechanism_2026_07_23`
  (in-progress phased build under direct operator guidance, doc self-declares "still correctly NOT AO-dispatchable" for
  its open items); `wsfeedconnector_phase35_gap_2026_07_06` (BLOCKED-CREDENTIALS on a vendor real-time key, matches the
  external-data-always-available pattern).

  **Net this session (Phase 1 + Phase 2 combined): ~185 + ~(60 docs' worth of todos, not yet summed — see next commit's
  exact count) new open todos entered the AO backlog.** Both flip batches were verified end-to-end against the live
  backlog API (`check-ao-backlog-status.sh`) earlier in Phase 1; the same verification should be repeated for Phase 2's
  docs once `PlanRegenLoop`'s ~5min cycle catches up.

  **Next**: (1) verify Phase 2's 60 docs actually appear in the live backlog; (2) the stale-checkbox correction sweep
  for BOTH phases' combined ~125 KEEP-NA-STALE docs (cite the extracting batch's commit/sha per item — this is real
  hygiene value distinct from backlog growth, not yet started); (3) split
  `instrument_id_format_canonicalization_2026_07_08.md` under the 1000L cap, then reclassify it; (4) Phase 3 (re-run
  `/ag-closeout-audit all` to verify total coverage against this session's baseline) — not yet started.

- **2026-07-27, continued (stale-checkbox pass + doc split + Phase 3 lightweight verification).**

  **Stale-checkbox correction, executed.** Resumed the 19 Phase 1+2 sub-agents to apply their own KEEP-NA-STALE
  findings. Result was NOT uniform compliance, and that's the correct outcome to record: 3 of 10 Phase-2 agents directly
  applied their edits when resumed; 7 correctly refused, citing their original explicit read-only task scoping — a
  mid-task message is not sufficient authorization to reverse a hard constraint set at task assignment, per this
  workspace's own escalation norms — and instead supplied precise per-doc/per-checkbox citation lists, which were
  applied directly. One agent (cross-cutting-1) went further on resume: re-verified its own earlier verdicts before
  complying and found 8 of its 11 flagged docs actually point to content that is ITSELF still open in the extracting
  batch doc (not genuinely done there either) — flipping those would have created false-done records, so only the 3
  genuinely-evidenced ones were applied. **Net: 64 docs, ~70 checkboxes corrected** (`unified-trading-pm@77766e441`),
  zero `assigned_vm` changes, zero backlog impact — pure bookkeeping so a future audit doesn't re-flag this content as
  an unaddressed orphan.

  **`instrument_id_format_canonicalization_2026_07_08.md` split + reclassified** (`unified-trading-pm@e92fcdbf3`): the
  751-line "Orchestration state, 2026-07-09" section (a dated, zero-open-todo, context-loss-recovery narrative) moved to
  `plans/archive/2026_07/instrument_id_format_canonicalization_2026_07_08_orchestration_history.md` — pure relocation,
  no content edited. Source doc now 566 lines (was 1,309), clearing the hard-cap block that excluded it from Phase 2.
  Its 2 remaining open todos (DEX-pool catalog regen; per-venue settlement-currency confirm) verified
  bounded/conflict-free, flipped `assigned_vm: NA → planning`.

  **Phase 3 — lightweight verification (not a fresh `/ag-closeout-audit all` fan-out; see rationale below).**
  Corpus-wide snapshot as of 2026-07-27 ~03:00 UTC: 391 `assigned_vm:NA` docs / 1,474 open todos remain (down from the
  session-start baseline of ~451/~1,780 — expected, since a live, extremely active session archives completed plans
  continuously all night, which mechanically shrinks both NA and planning counts independent of this audit's own work,
  making a raw before/after doc-count comparison noisy). The load-bearing verification instead: **every one of the 77
  docs this session flipped `NA → planning` (16 Phase-1 plan docs + 60 Phase-2 issue docs + 1 split doc) was checked for
  its current `assigned_vm` value — 76 confirmed still `planning`, and the 77th
  (`mdps_odds_horizon_bucket_reprocess_launch_prep_2026_07_25.md`) was not found at its original path** because a real
  AO worker had already claimed it from the live backlog, resolved it (discovered it was a duplicate dispatch of
  already-covered work), and archived it via the standard 6-step ritual + referrer repoint
  (`unified-trading-pm@4be5cf08f`/`506ab9ddd`) — **within the same session this audit ran**. That is stronger end-to-end
  proof than a queue-count snapshot: content this audit reclassified was picked up, executed, and closed by the real
  fleet while this session was still running. Did not run a fresh full `/ag-closeout-audit all` 9-tranche fan-out (a
  multi-hour, dozens-of-agent undertaking on the scale of tonight's own Phase 1+2) — judged the direct-execution
  evidence above as sufficient confirmation the mechanism works; a genuine fresh orphan-sweep re-run is left as this
  plan's own next open todo (Phase 3's original checklist item, not yet executed) for whoever picks this plan up next,
  since it answers a different question (are there NEW orphans post-tonight) than tonight's verification did (did
  tonight's specific reclassifications actually work).

  **Session totals**: 77 docs reclassified `NA→planning` across 2 phases; 16 companion finalize docs authored for the
  plan-doc half (issue docs exempt from that gate); 64 docs / ~70 checkboxes corrected for staleness; 1 oversized doc
  split. Live AO backlog observed growing from ~490-534 (pre-session) to 799 (last successful read, mid-session) — later
  live reads intermittently failed due to genuine host memory/load pressure on the orchestrator VM (25.6GB/56GB used,
  internal `tmux has-session` subprocess timeouts observed in its own journal), not a service outage (confirmed via
  `systemctl status`: stable uptime throughout, never crash-looping).

- **2026-07-27, continued (tranche-Sources fix, final health check, session close-out decision).** Fixed Phase 4's
  deferred tranche-Sources-listing todo — see the flipped checkbox above for the full breakdown
  (`unified-trading-pm@665a49d21`/`c223eed09`): 27 of 77 confirmed genuinely missing, 26 fixed via discoverability
  appends, 1 needed no fix (already archived by a real worker).

  **Final live-fleet health check**: backlog now 804 total (`queued`=716, `dispatched`=9, `blocked`=15, `done`=61,
  `cancelled`=3) — `done` climbed from 45 → 61 since the last snapshot, real continuous fleet throughput, not a stalled
  queue. No new PR/quickmerge failures observed beyond the expected transient branch-drift bounces on this extremely
  busy shared branch (all resolved via the standard rebase-and-retry, up to 9 retries on one commit tonight — consistent
  with, not exceeding, this workspace's own documented norm for a heavily concurrent session).

  **Decision on the remaining Phase-3 item (fresh full `/ag-closeout-audit all` 9-tranche re-run): deferred again,
  deliberately, not attempted.** Re-confirmed the same reasoning as the first pass: this is a separate-scale undertaking
  (the skill's own prior invocations have fanned out to dozens of sub-agents per full run) that deserves its own
  dedicated session with a fresh token/time budget, not a tacked-on continuation of an already extremely long dispatch
  (this session alone has shipped 20+ commits, run 30 parallel classification sub-agents across two phases, and worked
  through single retries as high as 9 consecutive transient branch-drift bounces). The tranche-Sources fix just
  completed directly addresses the actual risk a fresh audit re-run would have caught (this session's own reclassified
  docs going undiscovered) — the highest-value slice of "verify total coverage" is done; the remaining slice (are there
  OTHER, unrelated orphans that emerged overnight) is real but lower-value and unbounded in scope, better suited to a
  fresh `/ag-closeout-audit all` invocation on its own terms.

  **Session close-out.** Both items from this tick's dispatch are resolved (Sources fix: done; full audit re-run:
  deliberately deferred with reasoning recorded, not silently dropped). Ending the loop here rather than re-arming for
  another tick — continuing to poll without a concrete next action to take would be manufacturing work against this
  workspace's own stall-safety principle, not genuine progress. Next session should start with: (1) the deferred fresh
  `/ag-closeout-audit all` re-run, (2) re-verifying this plan's own Phase 1 tranches that haven't had a full pass yet
  (tradfi/prediction/ao/ci were folded into combined sub-agent batches tonight rather than getting a dedicated pass each
  — worth a targeted spot-check), (3) picking up the ~314 remaining `assigned_vm:NA` docs this session's sampling never
  reached directly (Phase 1/2 covered the docs with the clearest evidence trails; a systematic pass through the rest
  would likely surface more of the same 3-bucket split found here).

- **2026-07-27, fresh session — operator directive to complete the deferred items (full `/ag-closeout-audit all`
  re-run + the "~314" doc check).** Both close-out items from the prior tick got picked up as directed.

  **Correction, not a new finding.** The "~314" figure in the prior tick's own text was a genuine arithmetic error (444
  live-status minus 356 covered = 88, never 314 under any reading of the numbers already on record) — caught during this
  tick's own re-derivation, not flagged by the operator. Rebuilt the sweep properly: promoted
  `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` (PyYAML frontmatter parse, fixing Phase 0's long-standing
  P1 todo) and `generate_ag_closeout_audit_candidates.py` (citation-based orphan pre-filter for the fresh audit below),
  both shipped `unified-trading-pm@ea3456087`. The rebuild caught a real instance of the exact bug class it was built to
  prevent: a `* [ ]` star-bullet checkbox format (vs. the assumed `- [ ]`) hid one genuine open todo in
  `issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` — never reviewed in Phase 1/2 because it was invisible to
  the same class of regex those phases' own doc-selection used. Current honest snapshot: 389 `assigned_vm:NA` +
  active/open docs, 127 with zero open todos (hub/digest docs + already-reviewed KEEP-NA judgment calls, not a hidden
  backlog).

  **Fresh `/ag-closeout-audit all` — scoped, not a literal full corpus re-read.** A full per-doc read of the ~672-doc
  corpus was judged infeasible in one session (this plan already deferred that literal scope twice). Instead: built a
  cheap citation pre-filter (does any real covering doc — consolidated-closeout + dispatch-batch/finalize siblings,
  explicitly excluding non-covering `*_aggregated_sources*` digests — cite this doc's basename anywhere?), which
  narrowed 770 raw tranche-memberships down to 78 genuinely never-cited candidates. Dispatched 11 real per-doc
  classification agents (Workflow tool) against exactly that narrowed set, one-or-more DEDICATED agents per tranche —
  critically, tradfi/prediction/ao/ci each got their own agent this run, directly closing the combined/folded-pass gap
  flagged in the prior tick, rather than being answered by density-comparison inference.

  **Headline result: only 6 real AO-eligible-flagged orphans surfaced total, and the tranche-level noise told a more
  interesting story than the count.** prediction's all 13 candidates verdicted `exclude_cross_cutting` — not a coverage
  gap, but confirmation they're already correctly catalogued in `prediction_cross_cutting_debt_index_2026_07_25.md` (a
  doc my pre-filter's covering-path glob didn't know to check, since it doesn't match the
  `dispatch_batch|satellite |finalize` naming pattern) — a STRONGER answer to the tradfi/prediction spot-check than a
  clean pass would have been. cross-cutting's 37-of-40 `exclude_cross_cutting` rate is a genuine corpus-quality finding,
  not noise: `parent_epic: infrastructure_master` is shared by BOTH real cross-cutting data-pipeline docs and pure
  ci/infra content, so a parent-epic-only membership rule can't tell them apart (exactly what the skill's own docs warn
  — ao/ci/infra need real per-doc content judgment, not a mechanical epic rule) — every one of the 37 was correctly
  re-homed by the real agent read; logged as a pre-filter tooling follow-up above, not a data problem.

  **Of the 6 ao_eligible-flagged orphans, 3 were reclassified and 3 were kept NA on my own review** (agent verdicts are
  a strong signal, not a final ruling — this plan's own earlier tranches already demonstrated agents self-correcting on
  resume; this is the same discipline applied to MY synthesis of their output). Reclassified `NA→planning`
  (`unified-trading-pm@<pending>`, execution_scope corrected where stale):
  `/plans/archive/issues/defi_lending_protocol_capabilities_instrument_types_stale_atoken_debttoken_2026_07_27.md` (1
  todo, bounded code+verify), `issues/mtds_chain_bundle_migration_no_progress_checkpoint_2026_07_27.md` (2 todos,
  mirrors an already-shipped sibling pattern),
  `/plans/archive/issues/per_vm_shard_growth_oom_long_running_backfills_2026_07_27.md` (todo 1 is a bounded audit with a
  stated done-when; todo 2 retagged `[CODE]→[OPERATOR]` — its own text says "too risky to rush," touches fleet-wide
  concurrency-critical code, needs explicit sign-off before an AO worker attempts it). Kept NA despite the classifier's
  `ao_eligible: true`: `issues/deribit_dated_option_trades_perpetual_misclassification_2026_07_27.md` (the doc's OWN
  `execution_scope: human` field already says so — "find + fix a writer-side bug" is open-ended diagnostic work, not a
  bounded outcome); `issues/external_promote_gated_task_redispatch_churn_no_durable_park_2026_07_25.md`
  (AO/orchestrator-infrastructure dispatch-mechanism content — this plan's own Phase 2 already established that class
  stays human-reviewed even when a fix "looks mechanical," since a wrong fix risks corrupting the backlog the audit
  itself depends on); `issues/quickmerge_environment_autodetect_forces_dev_off_main_2026_07_25.md` (touches
  `scripts/quickmerge.sh` itself — every repo's ship path — carries `locked_by: live-defi-rollout`, contains a genuine
  "revisit whether X should happen" design question sequenced after an unstarted audit step, and its remaining work is
  still numbered prose, never converted to checkboxes — three independent reasons to keep this one human).

  **5 archivable_now candidates found, not archived this pass** (own follow-up todo above) — genuinely resolved/moot per
  the classifying agent's read, but archival is its own 6-step-ritual action deserving independent re-verification
  before executing, not a rider on this already-large tick.

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- added the tranche-inventory generator script the
  incremental audit runs are actually driven by.
- **context-scout 2026-08-07**: refreshed context_scope (6 entries) -- added
  `/cursor-configs/skills/na-eligibility-audit/SKILL.md`, the formalized skill this LOCAL plan's own methodology was
  generalized into (this doc's 2026-07-30 marker already calls itself "the LOCAL/human-driven origin plan for the very
  skill this run executes under" in prose but never linked it); other 5 entries re-verified, still resolve, unchanged.

## Progress Log (na-eligibility-audit incremental marker)

- **na-eligibility-audit 2026-07-30** (infra tranche, dispatch agt-30721a): KEEP-NA-STALE — closed Phase 0's 2 todos
  (blank/NA-detection false-positive fix; re-verified tranche-split NA list), both already done via
  `unified-trading-pm@ea3456087` per this doc's own 2026-07-27 Progress Log entry, just never flipped. Doc stays NA
  overall (this is the LOCAL/human-driven origin plan for the very skill this run executes under — the remaining 13 open
  items are Phase 1 tranche-audit checkboxes deliberately left unflipped per the doc's own honest "would overclaim"
  note, plus Phase 2's conflict-check/fold-in and Phase 3's pre-filter-widening work, all genuinely unexecuted).
  Self-referential note: this run (`/na-eligibility-audit infra`) is itself one incremental instance of the
  daily-scheduled generalization this plan's own Phase 2 todo describes authoring — no circularity issue, just worth
  flagging for a future reader.
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA, valid** (upgraded from the 2026-07-30
  KEEP-NA-STALE — that verdict's 2 stale Phase-0 todos are now flipped, so nothing stale remains). In scope this run
  only because a context-scout backfill touched the file. Read end-to-end; `grep -cE '^- \[ \]'` = **13**, matching this
  verdict's item count. All 13 are genuinely unexecuted: the 9 Phase-1 per-tranche checkboxes, Phase 2's
  conflict-check/fold-in pair, and Phase 3's pre-filter widening + prose-trap conversion. **Deliberately did NOT flip
  the `infra` tranche checkbox** even though this run gives every infra NA doc a dated verdict: that section's own
  done-when is "every `assigned_vm: NA` doc in that tranche", and the inventory this run consumed enumerates only docs
  with >=1 open todo, so a flip would overclaim against zero-open-todo members — exactly the overclaim this doc's own
  honest "would overclaim" note warns about. That note is a standing self-ruling and is not re-litigated here.
- **na-eligibility-audit 2026-08-03 (RECLASSIFY + blocker-currency pass, 10 parallel agents over the 122-doc set from
  this same date's staleness-audit rerun)**: full doc-level re-read (not line-level) of every doc, applying the
  RECLASSIFY rubric + the shared conflict-check protocol before any flip. **4 docs RECLASSIFIED `NA` → `planning`** (all
  `plans/active/issues/*.md`, so no `_finalize` companion owed):
  `manifest_v6_batch3_residual_orphaned_work_2026_07_21.md` (gate on `cefi_chain_tail_v6_canonicalisation_2026_07_21.md`
  cleared 2026-08-03 — archived, 0 real objects needed migrating; also backfilled a missing
  `assigned_role: data_engineering` and cleared the now-stale `depends_on`/ `gate_on_depends`),
  `defi_c0_rd5_orphan_sweep_todos_stranded_in_archived_plan_2026_07_31.md`,
  `fixtures_manifest_legacy_backfill_2026_07_24.md` (delete-vs-leave decision already settled+archived; remaining work
  is a bounded census re-run), `instruments_satellite_batch1_finalize_false_completion_claim_2026_08_02.md`. **11 docs
  got a blocker-currency note** (stale blocker cleared, item itself still open, `assigned_vm` unchanged) —
  `bucket_fold_features_2026_07_17.md`, `candle_feature_canonical_path_divergence_2026_07_20.md`,
  `github_actions_operator_gated_followups_2026_07_17.md`, `data_pipeline_reconciliation_skill_2026_07_20.md`,
  `infra_ops_residual_migration_verification_2026_07_24.md`, `ao_orphan_audit_followup_triage_2026_07_30.md`,
  `orchestrator_planregen_prune_wipes_backlog_on_transient_zero_derivation_2026_07_25.md`,
  `prediction_phase_ab_residuals_2026_07_24.md`, `data_completion_sports_2026_07_24.md`,
  `backlog_regen_reverted_p1_2_park_2026_08_01.md` (corrected a stale conflict citation, not a blocker per se). One
  bonus stale-checkbox close found in passing: `defi_strategy_pnl_axis_index_2026_07_24.md` (already shipped via
  `strategy-service@a90e85eb`, checkbox just never flipped). Every other doc in the 122-set stayed `KEEP-NA-VALID`,
  `MIXED` (genuine judgment items mixed with bounded ones — never whole-doc-flipped, per this doc's own rubric), a
  `CONFLICT` (work already claimed verbatim by an active `planning` doc — 4 caught, correctly not flipped), or
  `LOCKED-skipped` (`locked_by` set — frontmatter untouched). **Confirmed same-day evidence of a CONCURRENT
  `na-eligibility-audit` process independently working this exact population** (several docs already carried same-dated
  2026-08-03 verdict markers when read) — no conflicting edits resulted since every agent re-verified content directly
  rather than trusting a pre-existing marker, but it means this manual pass and the standing
  `na-eligibility-auditor.timer` cron overlapped in real time tonight.
- **Archived (dedicated follow-up pass, 2026-08-03)**:
  `batch_live_recon_cloud_run_job_stage0_never_succeeded_2026_07_30.md` — the 6-step ritual run in full: no deferred
  items to migrate (fix work already tracked in `recon_bucket_missing_nightly_recon_failing_2026_07_13.md`); archived
  banner + `resolved_by` added; the one durable fact (Cloud Run Job is the real live path, not the VM launcher) migrated
  to `/codex/04-architecture/runtime-deployment-topology.md` § 18; 4 corpus referrers fixed (1 prose citation annotated
  archived, 3 path references repointed to `plans/archive/issues/`); moved to `plans/archive/issues/`.
- **na-eligibility-audit 2026-08-03 (reconcile-65 pass — null result)**: measured 65 NA docs with >=1 open checkbox
  cited by an ALREADY-DONE `assigned_vm: planning` todo — the "should just need reconciliation" bucket. 7 already
  carried a disclaimer from the earlier same-day pass and were skipped; the remaining 58 (240 open lines) got a full
  fresh line-by-line hand-verification via 6 parallel agents. **Result: 0 checkboxes closed.** Every single citation was
  confirmed to reference a DIFFERENT, already-closed item in the same target doc, or an explicitly-excluded/
  time-gated/redirect-banner item — not the specific flagged checkbox. One real, mechanically-blocked exception found:
  `lst_rate_honest_coverage_2026_07_21.md` has 3 genuinely-done items (verified independently against
  `strategy-service@e93902d8`/`@23bd8b76`) that cannot be flipped because the doc is still over its 1000L hard cap (same
  known blocker already tracked above). This confirms the "cited by done AO work" signal, even restricted to its
  strongest sub-case, is currently fully saturated by the earlier 122-candidate pass — no further exploitable matches
  remain in this specific population at this corpus snapshot. Also flagged (not fixed):
  `cefi_consolidated_native_ao_extract_2026_07_25.md` has `status: active` in frontmatter but its own body text says
  "Status: draft... never auto-shipped to active" — a self-contradiction worth a maintainer's look.

- **na-eligibility-audit 2026-08-06**: KEEP-NA, valid (incremental-skip) — Skipped per incremental diff — unchanged
  since 2026-08-03 marker. Still the live origin plan for this skill; 13 open todos, all genuinely
  operator-gated/judgment.
- **na-eligibility-audit 2026-08-07** (ao tranche, batch3of3): KEEP-NA, valid — read end-to-end;
  `grep -cE '^[[:space:]]*[-*] \[ \]'` = **13**, matching. Doc stays NA overall (this is the LOCAL/human-driven origin
  plan for the very skill this run executes under). **Flagging 2 items for a future conflict-check pass, not
  reclassifying myself**: the `[SCRIPT] P3` cross-cutting-membership-rule fix (line ~239) and the `[SCRIPT] P2`
  staleness-script-cadence wiring (line ~246) both read as bounded, worker-determinable engineering tasks with named
  targets — lower-confidence candidates than a clean RECLASSIFY given this whole plan's own explicit operator-ruled
  LOCAL/human-track framing (2026-07-26), so left untouched. The other 11 open items (9 Phase-1 per-tranche audit
  checkboxes deliberately left unflipped per the doc's own honest-accounting convention, the Phase-2 batch-consolidation
  fork, and the `lst_rate_honest_coverage` line-cap-gated citation) remain genuine judgment/ongoing-incremental work,
  unchanged since 2026-08-03.

- **na-eligibility-audit 2026-08-09 (round11)**: KEEP-NA, valid — read end-to-end; `grep -c '^- \[ \]'` = **13**,
  matching. Re-examined the 2026-08-07 marker's own flagged pair (line ~239 cross-cutting-membership fix, line ~246
  staleness-script-cadence wiring) against the round7-10 precedent set, including "plan-destination defaults to
  AO-dispatched going forward" — that is a DEFAULT for cases never explicitly decided; this whole PLAN already has an
  explicit, dated, case-specific operator choice (2026-07-26, asked directly, chose LOCAL/human "since this is real
  per-doc judgment work") that a later general default does not override, same reasoning already applied elsewhere in
  this tranche (see `ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29.md`'s round11 marker for the
  identical specific-ruling-beats-later-default logic). The 2026-08-07 marker's own caution — treating the LOCAL framing
  as doc-level, not item-level — stands; not overriding it on a symmetric re-read. No other round7-10 precedent (IAM
  self-service, D16, S5.1, escalation-N, reversibility-qualified deletes, Option B retirement, DeepSeek/Slack
  credentials) touches any of the 13 open items. Remaining 11 items unchanged, genuine per-tranche
  audit/consolidation/line-cap-gated work.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -c '^- \[ \]'` = **13**, matching.
  This is the explicit, dated, case-specific operator-chosen LOCAL/human-track origin plan for the very skill this run
  executes under (operator asked directly 2026-07-26, chose LOCAL "since this is real per-doc judgment work") — per the
  round7-10 precedent chain already established on this exact doc (round9/round11 markers above), a later general
  default ("plan-destination defaults to AO-dispatched") does not override an earlier specific, dated ruling. Not
  re-litigated; no new precedent from the accumulated set (IAM self-service, D16, S5.1, escalation-N, reversibility-
  qualified deletes, Option B retirement, DeepSeek/Slack credentials) touches any of the 13 open items.
