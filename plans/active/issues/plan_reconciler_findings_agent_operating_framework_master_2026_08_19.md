---
doc_type: issue
title: "plan_reconciler epic-scoped run — agent_operating_framework_master, 2026-08-19"
summary: >-
  Findings from a full /plan-reconcile agent_operating_framework_master pass (71 child docs: 18 plans + 53 issues,
  5 parallel hunter batches). Mechanical/HARD-evidence classes were auto-fixed directly in the same pass (~49
  corrections across 26 files — see Progress Log). This doc parks the remainder: items needing an operator ruling,
  a class-level finding too large to fix by hand in one pass, and a small number of self-referential-corpus items
  (task_template.md itself) flagged rather than auto-edited per this run's explicit conservative instruction.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan-reconcile, agent-operating-framework, ao, findings]
related: []
created: 2026-08-19
source: plan-reconcile-agent_operating_framework_master-2026-08-19
author: plan_reconciler
parent_epic: agent_operating_framework_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
resolved_by:
locked_by:
locked_since:
context_scope: [plans/epics/agent_operating_framework_master.md, plans/active/task_template.md]
drift_direction: advance-code
depends_on: []
---

# plan_reconciler epic-scoped run — agent_operating_framework_master (2026-08-19)

## 1. NEEDS-RULING (operator authority/preference — not settled by evidence alone)

None found this pass that are pure authority/preference calls. Every routed item below is either genuinely
still-open ordinary work (investigation not yet finished) or a self-referential-corpus edit flagged out of
conservatism, not a judgment call with multiple defensible answers.

## 2. STILL-OPEN — genuine remaining work (not a ruling, just not yet done)

- [ ] [REVIEW] P2. **`operator_ruling_record_plan_reconcile_ao_2026_08_18.md` was left genuinely incomplete by its
      own prior run.** That doc's own text (lines ~159-167) states hunters 1/2/4/7 of the 2026-08-18 `/plan-reconcile
      ao` run had "not yet reported as of this doc's creation" and promises an update "before the run's final Phase 6
      report" — no such update was ever appended (only a 2026-08-19 na-eligibility-audit marker restating it's still
      not final). This run cannot fabricate those 4 missing hunters' findings. Done when: someone re-runs (or
      recovers the output of) that prior run's hunters 1/2/4/7 and appends their rulings to that doc, or the doc is
      explicitly closed as abandoned with a note.
- [ ] [REVIEW] P2. **`meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md` todo 13's target premise is stale
      but not confirmed superseded.** It asks to "complete the stalled `plan_reconciler_findings_tradfi_2026_08_09.md`
      run from STEP 4 onward" — that doc is now archived (`[unlock-plan]`d 2026-08-10) with a banner pointing back to
      this exact todo 13, but ~20 fresh `/plan-reconcile tradfi` passes have run since (most recently 2026-08-18) and
      a grep for the archived doc's 5 named P0/P1 candidate phrases in the newer tradfi findings docs returns zero
      hits. Not flipped (soft evidence only — the candidates may have been silently subsumed or may still be a live
      gap). Done when: a worker reads `plan_reconciler_findings_tradfi_2026_08_16.md` and `..._2026_08_18.md` in full
      and confirms whether the 5 original candidates (billing-suspension self-contradiction, batch5-archived-vs-cited-
      active, massive.py stale plan claim, PAYG-billing-stale, batch6 line-1-completeness) were addressed.
- [ ] [REVIEW] P3. **`ag_closeout_audit_rollout_2026_07_25.md`'s repeated "needs a dedicated cross-cutting
      close+archive pass" recommendation (lines ~124-126, 162-163, 170-172) may point at a doc that doesn't exist.**
      `plans/active/cross_cutting_closeout_observability_and_monitoring_2026_08_09.md` exists but its scope
      (observability/monitoring) doesn't obviously match "close+archive the mass-flip finalization work." Done when:
      a worker confirms whether that doc — or a different one — actually covers this, and either repoints the
      recommendation or authors the missing pass.

## 3. Class-level finding: bare (missing-leading-slash) `/plans/...` body citations

`check_reference_paths.py`'s "format" check (`BARE_CODEX_RE`) only validates bare `codex/...` refs — it does NOT
check bare `plans/...` refs at all, so this class is real (violates the CLAUDE.md HARD RULE that both `/codex/` and
`/plans/` citations carry a leading slash) but structurally invisible to the mechanical gate. This run's 5 hunters
found **~50+ individual line instances** of a bare `plans/active/...`/`plans/archive/...` citation missing its
leading slash, concentrated in: `gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md` (8),
`operator_action_items_consolidated_2026_08_08.md` (12), `blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28.md`
(10), `safe_doc_push_orphaned_patch_describes_unshipped_ci_fix_2026_08_17.md` (4, 2 already fixed this pass),
`cross_cutting_satellite_ao_dispatch_batch16_2026_08_17.md` (1 remaining), `mdps_qg_tests_slice_oserror_cannot_send_recurrence2_2026_08_19.md`
(3), `task_template.md` itself (4, see §4 below). **8 of the highest-visibility instances were fixed directly in
this pass** (see Progress Log); the remainder is logged here rather than hand-fixed one-by-one in this session given
the volume.

- [ ] [DOC] P3. Sweep and fix the remaining ~40+ bare `/plans/...`-missing-slash instances enumerated above.
      Consider widening `check_reference_paths.py`'s format check (`BARE_CODEX_RE`) to also match bare
      `plans/[0-9a-z_/-]+\.md` the same way it already does for `codex/`, so this class becomes mechanically gated
      instead of requiring a manual hunter sweep every time. Done when: a fresh `/plan-reconcile
      agent_operating_framework_master` pass finds 0 bare-plans-ref instances in this epic's corpus.

## 4. Flagged, NOT auto-fixed: `task_template.md` self-issues (conservative per this run's instructions)

`task_template.md` is the plan-authoring SSOT every other check in this run measures docs against — this run's
brief explicitly asked for extra care that a fix here doesn't itself violate the very rules it documents, and while
it is not `codex/**`/`CLAUDE.md` (so not hard-gated the same way), its blast radius (every future plan-authoring
agent reads it) argues for flagging rather than a same-pass edit.

- [ ] [DOC] P3. **Verbatim duplicate blockquote** — the "Why specificity here isn't just correctness"
      callout appears twice, back-to-back, near-identical wording (lines ~166-172 and ~174-180). Mechanical dedup
      (delete the second copy), low risk, but left for a dedicated follow-up rather than bundled into this pass.
- [ ] [DOC] P3. **4 bare `plans/...` refs in the doc's own body** (lines ~55, 135, 402, 525) — ironic given this is
      the doc anchoring the corpus's cross-reference convention (its OWN frontmatter `related:` correctly uses the
      leading slash). Mechanical 4-line fix, same conservatism note as above.
- [ ] [DOC] P3. **`gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md`'s live unresolved
      "zero-derived-parent-row" gate_on_depends failure mode is not caveated in `task_template.md`'s
      unqualified `depends_on`+`gate_on_depends` description** (§4-ish, "makes every task of THIS plan wait on
      every task of the named upstream plan(s)"). Once that doc's root-cause investigation closes, add a footnote.

## 5. Other genuine remaining work (informational, correctly still open — not new findings)

Near-complete (≤1 open todo, flagged per this skill's mechanical criterion, **explicitly not folded** per
`/plan-reconcile`'s own carve-out rules): `ag_closeout_audit_rollout_2026_07_25.md`,
`glue_runner_units_stopped_fleet_ci_outage_2026_08_04.md`, `check_agent_orchestrator_ssm_send_command_access_denied_2026_08_09.md`,
`subagent_wrote_to_foreign_checkout_bare_repo_path_2026_08_18.md`, `context_scout_completion_and_plan_brainstorm_skill_2026_07_30.md`,
`multi_agent_slot_collision_root_cause_and_safe_doc_push_rollout_2026_08_01.md`, `ao_stuck_escalation_mtds_no_free_slot_2026_08_18.md`,
`todo_cancelled_disposition_format_breaks_todo_regression_check_2026_08_09.md`, `zero_checkbox_sweep_all_tranches_2026_07_31.md`
(deliberately-permanent standing register), `na_audit_progress_log_extracted_checkbox_never_flipped_pattern_2026_08_16.md`,
`gate_on_depends_wiring_gap_defi_dex_pool_finalize_2026_07_25.md`, `na_doc_tranche_inventory_stale_citation_membership_cross_contamination_2026_07_29.md`,
`backlog_regen_reverted_p1_2_park_2026_08_01.md`, `data_pipeline_failure_one_shot_done_no_agentrow_2026_07_29.md`.
No fold target recommended for any of these per the skill's own guidance (fold destination is a preference call;
the ongoing audit cadence, not a one-off sweep, is the correct mechanism).

Two low-confidence items hunters flagged but did NOT recommend fixing (left as-is): `check_reference_paths_silent_skip_and_quiet_hides_violation_2026_08_12.md:125`
(bold clause borderline-complete on line 1); `na_audit_multi_tranche_shared_doc_ownership_and_draft_p0_park_2026_07_30.md:271`
(action verb present, target file only on line 2 — minor).

## Refuted

- None. Every hunter-reported candidate that reached this doc or the same-pass auto-fix set survived a direct
  re-check (SHA ancestry verified for the one done-but-unchecked SHA cited across 5 flips; file-existence verified
  for every bare-ref/dangling-ref fix; frontmatter status verified for the slot2_wedged/batch22 contradiction).

## Progress Log

- 2026-08-19 (plan_reconciler, `/plan-reconcile agent_operating_framework_master`): Created after a 5-hunter-batch
  sweep of all 71 epic-scoped docs (18 plans, 53 issues). ~49 mechanical corrections applied directly across 26
  files this same pass (5 done-but-unchecked flips with verified SHA-ancestry evidence, ~21 line-1-completeness
  rewrites, 8 bare-ref leading-slash fixes, 5 `[OPERATOR]` dispatch-safety retags, 1 dangling-ref moved-target
  repoint, 2 ordering-not-machine-enforced notes, 2 contradiction/misleading-content corrections, 2 structural
  fixes, 1 zero-checkbox-doc conversion, 1 epic-roster mechanical regen, 1 Phase -1 stale-prior-finding
  resolution). This doc parks what that pass could not settle from evidence alone.
- **context-scout 2026-08-20**: populated/refreshed context_scope (2 entries)
