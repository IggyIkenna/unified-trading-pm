---
doc_type: issue
title: Plan Reconciler Findings — tradfi tranche (2026-08-06)
summary: >-
  Daily plan_reconciler run for the tradfi tranche (agt-041a96, 2026-08-06). Scanned ~60 tradfi-tagged docs. Zero
  archivable candidates (3 locked, 1 exempt, 1 cross-tranche). One zero-checkbox doc with prose-hidden work found but
  grace-deferred. No mechanical missed flips. Hunters: zero-checkbox, archival eligibility, missed flips.
status: open
nature: issue
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, tradfi, auto-generated]
related: []
created: 2026-08-06
author: plan_reconciler
source: agt-041a96
parent_epic: plan_hygiene_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.1
estimate_calibrated_ai_days: 0.04
assigned_role: infra
drift_direction: advance-code
locked_by: plan_reconciler — run in progress
resolved_by:
---

# Plan Reconciler Findings — tradfi tranche (2026-08-06)

**Run**: `agt-041a96` | **Tranche**: `tradfi` | **Date**: 2026-08-06 **Scope**: ~60 tradfi-tagged docs in
`plans/active/` + `plans/active/issues/` + `plans/epics/tradfi_master.md` + normative refs + codex **Grace window**: 39+
docs in grace (modified <12h ago) — READ-ONLY

## Flips verified

(None — no mechanical missed flips with hard evidence found in non-grace tradfi docs)

## Contradictions

(None confirmed — hunters still running)

## Doc-drift

(None confirmed — hunters still running)

## Hygiene fixes

(None applied — no mechanical hygiene fixes identified in non-grace tradfi docs)

## Filed

- [ ] [DOC] P2. **Zero-checkbox conversion deferred**:
      `mtds_pipeline_check_process_killed_during_skip_leg_poll_2026_08_06.md` has 3 concrete prose follow-ups
      (strace/setsid repro, host cgroup-reaper check, host-wide pkill-guard rollout) in its "Suggested follow-up"
      section — should be converted to canonical `- [ ]` todos per the zero-checkbox sweep standing rule. **Deferred**:
      doc is in 12h grace window (created today 2026-08-06, mtime ~04:10 UTC). Source: zero-checkbox hunter (agt-041a96
      run).

## Archive candidates (operator review)

**5 fully-done (0 open todos) non-grace tradfi docs assessed**:

| Doc                                                                | Locked?                     | Cross-refs?                                           | Verdict           | Reason                                                                                               |
| ------------------------------------------------------------------ | --------------------------- | ----------------------------------------------------- | ----------------- | ---------------------------------------------------------------------------------------------------- |
| `instruments_satellite_ao_dispatch_batch1_2026_07_27.md`           | No (`archive_exempt: true`) | No                                                    | **EXEMPT**        | Archival routed through `instruments_satellite_batch1_finalize_false_completion_claim_2026_08_02.md` |
| `issues/tradfi_recovery_quarantine_registration_gap_2026_07_27.md` | Yes (`live-defi-rollout`)   | No                                                    | **LOCKED**        | Cannot auto-archive; suggest in findings                                                             |
| `issues/tradfi_backfill_oom_remediation_2026_06_24.md`             | Yes (`live-defi-rollout`)   | Yes (ag_closeout_audit, tradfi_consolidated_closeout) | **LOCKED**        | Cannot auto-archive; suggest in findings                                                             |
| `issues/tradfi_canonical_path_migration_design_2026_07_19.md`      | Yes (`live-defi-rollout`)   | Yes (ag_closeout_audit, tradfi_consolidated_closeout) | **LOCKED**        | Cannot auto-archive; suggest in findings                                                             |
| `issues/autonomous_session_operator_decisions_2026_07_25.md`       | No                          | Yes (6 tranches!)                                     | **CROSS-TRANCHE** | Sharded run cannot safely archive; leave for `all` pass                                              |

**Verdict**: 0 archivable this run (3 locked, 1 exempt, 1 cross-tranche).

## Refuted (dropped by verify)

- **Terminal-status violations from hygiene sweep**: the 3 flagged docs are not tradfi-primary (one is `omniroute_*`
  sports-adjacent, one is `instruments_service_sports_*` sports, and `ag_closeout_audit_rollout` has a comment "was:
  complete" but is correctly `status: active` after being reopened). No tradfi-primary action needed.

## Coverage (hunters / batches / docs)

- Non-grace tradfi plans: 14
- Non-grace tradfi issues: 20
- Grace docs (read-only): ~39
- Epic: `tradfi_master.md` (locked, `locked_by: live-defi-rollout`)
- Zero-checkbox sweep: 3 docs found (1 actionable, deferred; 1 this run's own scaffold; 1 false positive
  `task_template.md`)
- Hunters launched: 3 (zero-checkbox ✓, archival eligibility ✓, missed flips — running)

## Plans not reached

(None — all non-grace tradfi docs were catalogued; hunters covered key candidate classes)
