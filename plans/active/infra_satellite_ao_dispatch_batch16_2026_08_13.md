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
    /plans/archive/2026_08/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md,
    /plans/archive/2026_08/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md,
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
- [x] ✅ [CODE] P2. Record the Cursor claudeCode.allowDangerouslySkipPermissions / initialPermissionMode per-machine fix
      in the same codex doc Source: `plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md` —
      unified-trading-pm (this batch): added "Cursor permission-mode: two PER-MACHINE settings, not Claude Code
      settings" section to `/codex/05-infrastructure/claude-code-settings-symlink.md` with the exact keys, the
      per-machine (non-propagating) framing, and the two recorded dead ends.
- [x] ✅ [CODE] P2. Confirm no workflow depended on the disabled pyright-lsp in-session diagnostics before making the
      disable permanent Source: `plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md` —
      unified-trading-pm (this batch): grepped every `.json`/`.md`/`.sh`/`.py`/`.yml`/`.yaml` file in the repo for
      `pyright-lsp`/`pyright_lsp` — the only live hit is `cursor-configs/settings.json:35`
      (`"pyright-lsp@claude-plugins-official": false`); no skill (`cursor-configs/skills/`), codex doc (`codex/`), CI
      workflow, or script references the plugin or its "in-session diagnostics" (grepped for "language server"/"lsp"/
      "in-session diagnostic" across both trees — zero hits). `quality-gates.sh` runs `basedpyright` itself
      independently of the plugin, so the QG gate is unaffected either way (already noted in the source issue). The
      disable is already the tracked, git-committed team default (`e5be0047c1`, 2026-07-23, "re-track
      cursor-configs/settings.json") and propagates fleet-wide via `git pull` — nothing further needs to ship to make it
      permanent.
- [x] ✅ [CODE] P2. Re-verify (live find/ls) whether codex_vs_repo_docs_ssot_audit_2026_06_01.md's
      MDPS/instruments-service [x] items have the same DELETE-half-unshipped pattern already confirmed for 3 other
      items. Source: `plans/active/issues/plan_reconciler_findings_infra_2026_08_10.md` — unified-trading-pm (this
      batch): live `git ls-files` check in both repo clones found ALL 7 DELETE-class docs (5 MDPS + 2
      instruments-service, per the SSOT audit's refreshed 2026-07-27 registries) genuinely absent — suspicion REFUTED,
      no half-done pattern found; full writeup in the source issue doc's 2026-08-14 Filed-item update.
- [x] ✅ [CODE] P2. Fix fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md's todo 5/6 repo-count
      off-by-ones (states 23/'22 of 23', enumerated lists count 24) and defi_compute_gcp_migration_2026_08_08.md's
      missing related: back-reference to its finalize twin. Source:
      `plans/active/issues/plan_reconciler_findings_infra_2026_08_10.md` — re-counted both enumerated repo lists
      programmatically (comma-split, parentheticals stripped): todo 5's list = 24 entries (text said "23" — the plan's
      own todo 4 already established 24 as the correct non-PM fleet-repo count, matching); todo 6's list = 23 entries
      (text said "22 of 23" — should be "23 of 24", since todo 6 assesses the same 24-repo fleet minus the 1
      `deployment-service` exception that kept its local copy). Fixed both stated counts to match their enumerated lists
      in `fleet_workflow_template_dedup_to_unified_trading_ci_2026_08_06.md` todos 5+6. Added the missing
      one-directional `related:` back-reference from `defi_compute_gcp_migration_2026_08_08.md` to its finalize twin
      `/plans/active/defi_compute_gcp_migration_2026_08_08_finalize_2026_08_08.md` (which already pointed at the
      parent). unified-trading-pm@6ea81d3e15
- [x] ✅ [CODE] P2. Fix prod_terraform_drift_backlog_reconcile_2026_07_24.md:177's dangling 'finding W' citation to
      point at the actual section name in orchestrator-cloud-identity-self-service.md. Source:
      `plans/active/issues/plan_reconciler_findings_infra_2026_08_10.md` — unified-trading-pm (this batch): the doc has
      no "finding W" section; the actual anchor for the self-fixable-permission-gap rule is `## The rule`. Reworded the
      citation to `... § "The rule"` and dropped the undefined "finding W" phrasing (incl. its self-reference in the
      surrounding prose).
- [x] ✅ [INFRA] P2. Verify quickmerge isolation on a second (service) repo with a heavier suite and confirm the cached
      venv (~/.cache/qm-iso-venv/<repo>) refreshes correctly across a dependency-lock bump, before flipping
      laptop-default isolation back on. Done when: two repos pass an isolated --isolated quickmerge end-to-end and the
      cache is shown to refresh on a lock change. Source:
      `plans/archive/2026_08/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md` —
      execution-service@866acb2496 (581-test suite, `--isolated` end-to-end + cache-refresh proof; full writeup in the
      source issue doc's flipped todo + 2026-08-14 Progress Log entry). Also filed
      `plans/active/issues/execution_service_contributing_doc_stale_2026_08_14.md` (unrelated stale-doc finding hit
      while picking the verification vehicle).
- [x] ✅ [CODE] P2. Coordinated pip-audit dependency bump for pyarrow 23.0.0->24.0.0 (needs a PM canonical-range widen,
      same pattern as the already-shipped lxml unit) + twisted/mako/ujson in-range bumps, execution-service +
      unified-trading-pm Source: `plans/active/codex_violations_ratchet_to_five_2026_06_10.md` — RE-INVESTIGATED
      2026-08-14: mako/twisted/ujson were already at their fixed versions (untracked earlier pass); pyarrow 23.0.1's
      only cited advisory is already fixed at this version and live pip-audit + a full `QG_SLICE=lint-codex` run show
      zero vulnerabilities fleet-default, so the PM canonical-range widen has no live security driver and was NOT
      executed. execution-service@bb49911d27 ratchets `CODEX_MAX_VIOLATIONS` 3→0 on the strength of this; full writeup
      in the source doc's own flipped todo.
- [x] ✅ [SCRIPT] P2. Fix _VERDICT_MARKER_LINE_RE (or replace with a proper multi-line-block strip) in
      generate_na_doc_tranche_inventory.py so a marker's full continuation-line span is excluded from
      body_content_hash(); add the stated regression test asserting hash-before ==
      hash-after-writing-the-declared-hash-marker; verify against real multi-line markers in the corpus. Source:
      `plans/active/issues/na_eligibility_multiline_marker_continuation_lines_never_stripped_from_hash_2026_08_10.md` —
      STALE-CHECKBOX CORRECTION (already-shipped-elsewhere, per
      `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3.4): this item was carved into
      this batch citing the source issue doc's own todo 1, but that todo was already `[x]` at
      `unified-trading-pm@fcaaa677f1` before this batch dispatched — verified live: `fcaaa677f1` is an ancestor of
      `origin/live-defi-rollout`, `_VERDICT_MARKER_LINE_RE` in
      `scripts/plan-hygiene/generate_na_doc_tranche_inventory.py` already strips the full marker block (not just the
      first line), and both named regression tests (`test_body_content_hash_stable_across_own_multiline_marker`,
      `test_body_content_hash_multiline_marker_stops_at_next_bullet`) exist in
      `tests/unit/test_generate_na_doc_tranche_inventory.py`. No new code needed; flipping this checkbox to match
      reality — unified-trading-pm@fcaaa677f1 (pre-existing).
- [ ] [SCRIPT] P3. Once fixed, spot-check docs with old (pre-fix) markers to confirm the next na-eligibility-audit run
      correctly reports incremental_skip: true when no real content changed. Source:
      `plans/active/issues/na_eligibility_multiline_marker_continuation_lines_never_stripped_from_hash_2026_08_10.md`
- [x] ✅ [CODE] P2. Make the swallowed ImportError loud in unified-trading-pm/scripts/quality_gates/_capability_gaps.py
      (~line 864) Source: `plans/archive/2026_08/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md`
      — STALE-CHECKBOX CORRECTION (already-shipped-elsewhere, per
      `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3.4): the source issue doc's own
      todo 2 was already `[x] ✅ 2026-08-13` at `unified-trading-pm@c7c237d804` + `a5182bdbfc` before this batch
      dispatched — verified live: `c7c237d804` is an ancestor of `origin/live-defi-rollout`, the actual file is
      `scripts/openapi/_capability_gaps.py` (the batch todo's `quality_gates` path was a transcription slip), its
      `extract_param_schema` already raises `RuntimeError` naming the offending venv path + underlying message on
      `import_error` (line ~857-863) instead of degrading to `{}`, and the regression test
      `test_import_error_fails_loud` exists in `tests/unit/test_capability_param_schema.py:116`. No new code needed;
      flipping this checkbox to match reality — unified-trading-pm@c7c237d804 (pre-existing).
- [x] ✅ [CODE] P2. Measure whether other slots and the AO VM carry the same fastapi staleness; report per-slot
      installed-vs-declared table Source:
      `plans/archive/2026_08/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md` — STALE-CHECKBOX
      CORRECTION (already-shipped-elsewhere, per
      `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3.4): the source issue doc's own
      todo 3 was already `[x] ✅ 2026-08-13` at `unified-trading-pm@4f7c5f827b` before this batch dispatched — verified
      live: `4f7c5f827b` is an ancestor of `origin/live-defi-rollout`, and the source doc's Progress Log already carries
      the full per-slot table (all 33 slots + the AO VM's runtime venv swept, 239 fastapi-carrying venvs, zero below the
      `>=0.137.0` floor). No new measurement needed; flipping this checkbox to match reality —
      unified-trading-pm@4f7c5f827b (pre-existing).
- [x] ✅ [CODE] P2. Add a preflight/QG check that fails when an installed distribution is below its own pyproject.toml
      floor Source: `plans/archive/2026_08/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md` —
      STALE-CHECKBOX CORRECTION (already-shipped-elsewhere, per
      `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3.4): the source issue doc's own
      todo 4 was already `[x] ✅ 2026-08-13` at `unified-trading-pm@45d9248d68` before this batch dispatched — verified
      live: `45d9248d68` is an ancestor of `origin/live-defi-rollout`,
      `scripts/quality_gates/check_installed_satisfies_pyproject.py` exists and is wired into both
      `scripts/quality-gates-base/base-service.sh` and `base-library.sh` right after the frozen-lock floor gate, and it
      correctly PASSES when invoked with the venv's own python (`.venv/bin/python`) and correctly FLAGS violations when
      mis-invoked with the wrong interpreter — confirmed live against slot 27's own PM venv. No new code needed;
      flipping this checkbox to match reality — unified-trading-pm@45d9248d68 (pre-existing).
- [x] ✅ [CODE] P2. Add a one-line pointer to this doc from the 9 referencing docs once todo 1 lands Source:
      `plans/archive/2026_08/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md` — STALE-CHECKBOX
      CORRECTION (already-shipped-elsewhere, per
      `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` § 3.4): the source issue doc's own
      todo 5 was already `[x] ✅ 2026-08-13 — slot-6` before this batch dispatched — verified live:
      `rg -l "Owner for the stale-venv" plans/` finds the pointer already present in all 10 referencing docs (9 listed
      in the source doc's Prior-art section + `fleet_venv_drift_after_pull_no_resync_2026_08_11.md`) plus the archive
      sibling `sports_fast_t1_recon_oom_live_capture_outage_2026_08_01_progress_log_archive_2026_08_14.md` (landed via
      the source doc's own todo 6, 2026-08-14). No new code needed; flipping this checkbox to match reality —
      unified-trading-pm (this batch, pre-existing content).
- [x] ✅ [CODE] P2. **DONE 2026-08-14 (slot 27) — same investigation as the source doc's own final todo, RETAINED, not
      dead weight.** Confirm the 4 .stale-pre-history-rewrite-* archive dirs are dead weight and can be removed, or
      document why retained Source:
      `plans/archive/2026_08/issues/stale_service_venvs_below_declared_fastapi_floor_2026_08_11.md` — investigated
      directly (not just a checkbox-mirror): each dir is a live git clone with a real `origin` remote (not orphaned),
      carries no `.venv` fleet-wide (0/80 dirs), and its `HEAD` is byte-identical to its live sibling repo's `HEAD`
      (actively FF-realigned, not frozen). Decisive: this exact question was already ruled on 2026-08-10 in
      `/plans/archive/issues/git_health_scan_exclusion_infra_routing_2026_08_10.md` — main confirmed these `*.stale-*`
      dirs are intentional 08-05 pre-history-rewrite backups and directed "no deletions"; the git-health
      scan/reporter/FF-cron already exclude them from drift noise (`agent-orchestrator@b4ab17e84e` +
      `unified-trading-pm@71f10bc0f`). No repo/code changes; retained by existing operator/main ruling. Corroborated by
      slot 20's independent 6-slot sample the same day (same no-`.venv` fact; slot 27's citation of the 2026-08-10
      ruling is the authoritative verdict).
- [ ] [CODE] P2. Execute the 'immediately-safe ~40' script deletions (UI 2026-03 .tsx.bak splitters/codemods, done
      deployment-service bucket migrations, the 5 dead checkers) -- the sub-list this doc's own Delete-execution item
      names as unconditionally safe, distinct from the campaign-gated cohort it's bundled with Source:
      `plans/active/repo_scripts_governance_audit_2026_06_18.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
