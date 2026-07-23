---
title: Triage of 9 issue files per operator 2026-05-20
created: 2026-05-20
author: background agent (delegated by slot-1)
locked_by: live-defi-rollout
---

## Verdicts

| #   | File                                                                 | Bucket                      | Justification                                                                                                                                                                                                                                                                                                                                             | Recommended action                                                                                                                                                                                                                            |
| --- | -------------------------------------------------------------------- | --------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `github_pat_in_instruments_service_env_2026_05_15.md`                | **A. IN-PROGRESS**          | Frontmatter `resolved: 2026-05-15` (credential dead — HTTP 401), BUT body explicitly defers BFG history scrub as P3-hygiene + batches it into `bfg_history_scrub_sequence_2026_05_20.md`. Companion BFG plan is `ready-awaiting-operator-go`. Hygiene phase still in flight.                                                                              | KEEP — banner already cross-links the BFG sequence; will auto-archive together once BFG completes. No action now.                                                                                                                             |
| 2   | `lint_sweep_774602ea8_regression_audit_2026_05_20.md`                | **C. UNREFERENCED-SUMMARY** | Carries `🟢 RESOLVED 2026-05-20` banner (both regressed files restored at execution-service@195cf6829). Referenced from `uac_source_capability_metadata_promotion_2026_05_20.md` + mega_audit + `/codex/06-coding-standards/quality-gates.md` only as a reference incident — the QG enforcement (STEP 5.83) is shipped. Doc is a closed reference record. | ARCHIVE — `git mv plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md plans/archive/issues/`. Codex/parent-plan cross-refs survive the move (path is `plans/archive/issues/<same-filename>`).                             |
| 3   | `ml_repo_consolidation_preaudit_2026_05_19.md`                       | **B. COVERED-BY-PLAN**      | Banner already declares `🟡 COVERED BY ../ml_repo_consolidation_2026_05_19.md`. Parent verified to exist (`plans/active/ml_repo_consolidation_2026_05_19.md`, 39KB). Banner states "Stays in issues/ until parent closes, then archives with it."                                                                                                         | KEEP per the doc's own stated lifecycle (archive when parent closes). No action now — banner-marked policy already governs lifecycle.                                                                                                         |
| 4   | `resolved_issues_archive_audit_2026_05_20.md`                        | **C. UNREFERENCED-SUMMARY** | This is the closed meta-audit driving the 56-resolved-issue bulk-archive. No inbound references from any other plan/codex doc. Once its bulk-archive command runs (or is consciously deferred), it has no future use as an active issue doc.                                                                                                              | KEEP IF its Batch 1-3 archive operation hasn't run yet (still actionable); otherwise ARCHIVE. Recommend: leave KEEP until operator executes its Batch commands, then move to `plans/audit/` (it IS a meta-audit).                             |
| 5   | `trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md` | **D. STANDALONE-KEEP**      | Carries explicit "Triage 2026-05-18: Status OPEN, BLOCKED-CREDENTIALS". Visibility fix shipped but credentials gap remains; tracked under master plan `Credential asks awaiting operator`. No covering plan. Genuine open issue.                                                                                                                          | KEEP — flag: needs operator credential approval to close. Already cross-linked into master plan.                                                                                                                                              |
| 6   | `unified_api_contracts_todo_audit_2026_05_19.md`                     | **B. COVERED-BY-PLAN**      | Banner: `🟡 SUBSUMED BY MEGA AUDIT` Phase A2 + C9 per `mega_audit_and_plan_beefup_progression_2026_05_20.md`. Parent doc exists at `plans/active/issues/mega_audit_and_plan_beefup_progression_2026_05_20.md` (NOT `plans/active/`). Body explicitly says "Do NOT work standalone."                                                                       | ARCHIVE — `git mv` to `plans/archive/issues/`. Banner is the named-successor pointer. Mega-audit absorbs all 2 findings (VX front-month → C9 + TradFi OHLCV plan; coverage_starts TODOs → A2 expected_coverage).                              |
| 7   | `unused_import_audit_2026_05_18.md`                                  | **D. STANDALONE-KEEP**      | P3 ride-along cleanup with ownership-routing per repo. Referenced from `work_split_2026_05_18_harsh.md` (slot-4 item 15) and `open_issues_triage_against_mega_audit_2026_05_20.md`. No janitorial covering plan. 11 fixable F401s blocked on foreign-dirty files in slot 2/9/instruments-service.                                                         | KEEP — flag: needs a slot with clean execution-service / instruments-service / MTDS window to apply 1-line `ruff check --select F401 --fix`. No successor plan needed (ride-along).                                                           |
| 8   | `archive_deferred_migration_2026_05_19.md`                           | **D. STANDALONE-KEEP**      | 24 archived plans with un-migrated DEFERRED items. No covering janitorial plan exists. Referenced only from `open_issues_triage_against_mega_audit_2026_05_20.md`. Doc's own recommendation requires per-operator review before action.                                                                                                                   | KEEP — flag: needs operator to triage the "high priority" list (defi_simulation_realism, risk_simulations_limits_alerting, api_football_phase_3b_3c, solana_amm_coverage_expansion). Add `MIGRATED TO:` pointers per CLAUDE.md archival rule. |
| 9   | `bfg_history_scrub_sequence_2026_05_20.md`                           | **A. IN-PROGRESS**          | `status: ready-awaiting-operator-go`, `deadline: 2026-05-23`. Scoped across 5 repos. Cross-referenced as the named successor by file #1 (github_pat) and parallel gcp_sa_private_key issue.                                                                                                                                                               | KEEP — actively gated on operator GO. No banner edit needed (status already explicit).                                                                                                                                                        |

## Bulk archive command

```bash
cd /Users/ikennaigboaka/Code/unified-trading-system-repos/.tabs/1/unified-trading-pm
git mv \
  plans/active/issues/lint_sweep_774602ea8_regression_audit_2026_05_20.md \
  plans/active/issues/unified_api_contracts_todo_audit_2026_05_19.md \
  plans/archive/issues/
```

(2 files. The other 7 stay in `plans/active/issues/`.)

Optional (operator-decision): file #4 `resolved_issues_archive_audit_2026_05_20.md` → if its bulk-archive batches have
already been executed, move to `plans/audit/` (meta-audit location). Confirm by checking whether the 33 ARCHIVE-CLEAN
files it names still live in `plans/active/issues/`.

## Standalone-keep items needing follow-up

- **#5 `trading_agent_service_workspace_qg_silent_clone_fail_2026_05_16.md`** — needs operator credential rotation (PAT
  for trading-agent-service GHA). Already filed in master plan § "Credential asks awaiting operator". Non-blocking for
  May-23.
- **#7 `unused_import_audit_2026_05_18.md`** — 11 F401 fixes blocked on clean windows in execution-service (slot 2),
  instruments-service, MTDS (slot 9). Pick up when any of those slots has no foreign-dirty files. ≤5 min per repo.
- **#8 `archive_deferred_migration_2026_05_19.md`** — needs operator triage call on 4 high-priority archived plans
  (which to migrate forward vs accept as lost). Per CLAUDE.md archival rule, every un-migrated DEFERRED is a potential
  lost-work signal.

## Bucket counts

- A IN-PROGRESS: **2** (files 1, 9)
- B COVERED-BY-PLAN: **2** (files 3, 6)
- C UNREFERENCED-SUMMARY: **2** (files 2, 4)
- D STANDALONE-KEEP: **3** (files 5, 7, 8)

**Bulk-archivable now: 2 files** (#2, #6). 7 stay.

## Verdicts I'm least sure about

- **#4 `resolved_issues_archive_audit_2026_05_20.md`** — classification as UNREFERENCED-SUMMARY assumes its Batch 1-3
  archive command hasn't run yet. If it has already run (operator executed the bulk-archive), this becomes a closed
  meta-audit suitable for `plans/audit/`. Verify by checking whether the 33 ARCHIVE-CLEAN filenames it lists still exist
  under `plans/active/issues/`.
- **#3 `ml_repo_consolidation_preaudit_2026_05_19.md`** — could arguably bulk-archive NOW (banner says "stays until
  parent closes" but it IS pure pre-audit diagnostic with no remaining action items). Conservative call: respect the
  banner's stated policy. Operator may override.
