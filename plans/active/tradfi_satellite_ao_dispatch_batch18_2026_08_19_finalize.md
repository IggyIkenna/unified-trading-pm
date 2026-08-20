---
doc_type: plan
title: Finalize — tradfi satellite AO-dispatch batch 18
summary: >-
  Gated finalize twin for tradfi_satellite_ao_dispatch_batch18_2026_08_19.md. Reconciles both extracted todos'
  evidence back into their true source docs (the ETF-drift issue doc and the now-archived DXY-duplicate issue doc),
  re-checks whether the ETF-drift source doc is now fully closed and archivable, then archives this batch plan
  itself.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [tradfi, ao-dispatch, satellite-batch, finalize, na-eligibility-audit]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch18_2026_08_19.md,
    /plans/active/issues/tradfi_deprecated_etf_manifest_rows_forward_scope_drift_2026_08_18.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-19
last_updated: 2026-08-20
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: backend_engineer
effort: low
drift_direction: advance-docs
depends_on: [tradfi_satellite_ao_dispatch_batch18_2026_08_19]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch18_2026_08_19.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /plans/active/issues/tradfi_deprecated_etf_manifest_rows_forward_scope_drift_2026_08_18.md,
  ]
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  na-eligibility-audit, tradfi tranche, dispatch agt-5d34f9, 2026-08-19 — mandatory finalize twin
  (task_template.md §4).
---

# Finalize — tradfi satellite AO-dispatch batch 18

## Todos

- [ ] [REVIEW] P2. Reconcile both of batch18's todos' evidence back into their true source docs: confirm
      `tradfi_deprecated_etf_manifest_rows_forward_scope_drift_2026_08_18.md`'s todo 2 citation and the
      already-archived `plans/archive/issues/dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md`'s purge-todo
      citation both resolve to real commits/evidence (re-verify the cited SHAs exist, don't trust the source docs'
      own copy blindly).
- [ ] [REVIEW] P2. Check whether `tradfi_deprecated_etf_manifest_rows_forward_scope_drift_2026_08_18.md` is now
      fully closed (0 open todos) as a result — if so, flag it as an ARCHIVE candidate for a future
      `/na-eligibility-audit` or `/archive-candidates-audit` pass rather than archiving it here (out of this
      finalize's own scope). The DXY doc is already archived — no further action needed there beyond todo 1's
      evidence check above.
- [ ] [DOC] P1. Run the standard 6-step archival ritual on `tradfi_satellite_ao_dispatch_batch18_2026_08_19.md`
      itself (now that both its todos are done): move to `plans/archive/2026_08/`, flip `status`, add the
      superseded-by/archived banner, sweep every corpus referrer. Done when: `check_archive_candidates.sh` runs
      clean with 0 new orphans.

## Progress Log

- **2026-08-19 (na-eligibility-audit, tradfi tranche, dispatch agt-5d34f9)**: authored alongside batch18 itself,
  per `task_template.md` §4's mandatory finalize-plan-coverage rule. Not yet executed — gated on batch18's own
  todos landing.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
