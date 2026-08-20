---
doc_type: plan
title: Finalize — TradFi purge extension + twin-delete lookup-bug fix
summary: Gated finalize companion for tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [tradfi, finalize]
related:
  [
    /plans/active/tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md,
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: review
effort: max
drift_direction: advance-code
depends_on: [tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16]
gate_on_depends: true
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 3, 2026-08-16"
locked_by:
context_scope: [/plans/active/tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md]
locked_since:
resolved_by:
---

# Finalize — TradFi purge extension + twin-delete lookup-bug fix

- [ ] [REVIEW] P2. Confirm the residual-leg purge landed with evidence and the canonical_twin_path() lookup-bug
      investigation concluded (fixed + re-measured, or found to be a false lead) with the fresh coverage % recorded
      in `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`; archive that plan once done and unlocked.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (1 entry).
