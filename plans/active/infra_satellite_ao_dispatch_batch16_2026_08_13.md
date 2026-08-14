---
doc_type: plan
title: infrastructure satellite AO dispatch batch 16 — 2026-08-13
summary: >-
  Extraction batch from the infrastructure tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep —
  18 conflict-cleared, bounded/deterministic items pulled directly from 7 source docs (RECLASSIFY_SPLIT bounded items
  from the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each
  todo cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation
  back into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: active
nature: process
asset_group: [infrastructure]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [infrastructure, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/codex_violations_ratchet_to_five_2026_06_10.md,
    /plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md,
    /plans/active/issues/na_eligibility_multiline_marker_continuation_lines_never_stripped_from_hash_2026_08_10.md,
    /plans/active/issues/plan_reconciler_findings_infra_2026_08_10.md,
    /plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md,
    /plans/active/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md,
    /plans/active/repo_scripts_governance_audit_2026_06_18.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 2.7
estimate_calibrated_ai_days: 2.2
assigned_role: infra
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# infrastructure satellite AO dispatch batch 16 — 2026-08-13

> **Operator-approved 2026-08-13 — `status: active`, dispatchable.** Every todo below was classified
> bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13 full-sweep audit
> and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [x] ✅ [CODE] P2. Add a hygiene-sweep check that fails when cursor-configs/settings.json is dirty in any clone, or
      when any .claude/settings.local.json is a symlink Source:
      `plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md` — unified-trading-pm@99a13bea88
      (`scripts/plan-hygiene/check_settings_symlink_hygiene.sh` + wired into `run_hygiene_sweep.sh`; verified PASS on a
      clean workspace and FAIL on both violation modes via a scratch fake-clone)
- [x] ✅ [CODE] P2. Find where the settings.local.json symlinks came from (which bootstrap path/manual step created
      them) Source: `plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md` —
      unified-trading-pm (this batch) — negative-result investigation: no script ever creates that symlink (exhaustive
      git-history search of every bootstrap/linker script); most likely a manual `ln -s` typo by an operator. Full
      writeup + todo closed in the source issue doc's 2026-08-14 Progress Log entry.
- [x] ✅ [CODE] P2. Update /codex/05-infrastructure/claude-code-settings-symlink.md with the corrected symlink-target
      and git-tracked-status facts Source:
      `plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md` — unified-trading-pm (this
      batch): added "`settings.local.json` must be a REAL per-clone file — never a symlink" section (mechanism, fix,
      hygiene-check pointer) + a "`cursor-configs/settings.json` git-tracked status — confirmed current" section
      flagging `link-claude-skills.sh`'s own header comments as the stale artifact, not this codex doc.
- [ ] [CODE] P2. Record the Cursor claudeCode.allowDangerouslySkipPermissions / initialPermissionMode per-machine fix in
      the same codex doc Source: `plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md`
- [ ] [CODE] P2. Confirm no workflow depended on the disabled pyright-lsp in-session diagnostics before making the
      disable permanent Source: `plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md`
- [ ] [CODE] P2. Re-verify (live find/ls) whether codex_vs_repo_docs_ssot_audit_2026_06_01.md's MDPS/instruments-service
      [x] items have the same DELETE-half-unshipped pattern already confirmed for 3 other items. Source:
      `plans/active/issues/plan_reconciler_findings_infra_2026_08_10.md`
- [ ] [CODE] P2. Fix fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md's todo 5/6 repo-count off-by-ones
      (states 23/'22 of 23', enumerated lists count 24) and defi_compute_gcp_migration_2026_08_08.md's missing related:
      back-reference to its finalize twin. Source: `plans/active/issues/plan_reconciler_findings_infra_2026_08_10.md`
- [ ] [CODE] P2. Fix prod_terraform_drift_backlog_reconcile_2026_07_24.md:177's dangling 'finding W' citation to point
      at the actual section name in orchestrator-cloud-identity-self-service.md. Source:
      `plans/active/issues/plan_reconciler_findings_infra_2026_08_10.md`
- [ ] [INFRA] P2. Verify quickmerge isolation on a second (service) repo with a heavier suite and confirm the cached
      venv (~/.cache/qm-iso-venv/<repo>) refreshes correctly across a dependency-lock bump, before flipping
      laptop-default isolation back on. Done when: two repos pass an isolated --isolated quickmerge end-to-end and the
      cache is shown to refresh on a lock change. Source:
      `plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md`
- [ ] [CODE] P2. Coordinated pip-audit dependency bump for pyarrow 23.0.0->24.0.0 (needs a PM canonical-range widen,
      same pattern as the already-shipped lxml unit) + twisted/mako/ujson in-range bumps, execution-service +
      unified-trading-pm Source: `plans/active/codex_violations_ratchet_to_five_2026_06_10.md`
- [ ] [SCRIPT] P2. Fix _VERDICT_MARKER_LINE_RE (or replace with a proper multi-line-block strip) in
      generate_na_doc_tranche_inventory.py so a marker's full continuation-line span is excluded from
      body_content_hash(); add the stated regression test asserting hash-before ==
      hash-after-writing-the-declared-hash-marker; verify against real multi-line markers in the corpus. Source:
      `plans/active/issues/na_eligibility_multiline_marker_continuation_lines_never_stripped_from_hash_2026_08_10.md`
- [ ] [SCRIPT] P3. Once fixed, spot-check docs with old (pre-fix) markers to confirm the next na-eligibility-audit run
      correctly reports incremental_skip: true when no real content changed. Source:
      `plans/active/issues/na_eligibility_multiline_marker_continuation_lines_never_stripped_from_hash_2026_08_10.md`
- [ ] [CODE] P2. Make the swallowed ImportError loud in unified-trading-pm/scripts/quality_gates/_capability_gaps.py
      (~line 864) Source: `plans/active/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md`
- [ ] [CODE] P2. Measure whether other slots and the AO VM carry the same fastapi staleness; report per-slot
      installed-vs-declared table Source:
      `plans/active/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md`
- [ ] [CODE] P2. Add a preflight/QG check that fails when an installed distribution is below its own pyproject.toml
      floor Source: `plans/active/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md`
- [ ] [CODE] P2. Add a one-line pointer to this doc from the 9 referencing docs once todo 1 lands Source:
      `plans/active/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md`
- [ ] [CODE] P2. Confirm the 4 .stale-pre-history-rewrite-* archive dirs are dead weight and can be removed, or document
      why retained Source: `plans/active/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md`
- [ ] [CODE] P2. Execute the 'immediately-safe ~40' script deletions (UI 2026-03 .tsx.bak splitters/codemods, done
      deployment-service bucket migrations, the 5 dead checkers) -- the sub-list this doc's own Delete-execution item
      names as unconditionally safe, distinct from the campaign-gated cohort it's bundled with Source:
      `plans/active/repo_scripts_governance_audit_2026_06_18.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
