---
doc_type: plan
title: Finalize — CME expected_coverage narrowing
summary: Gated finalize companion for tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16.md.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-api-contracts, deployment-api]
scope: [engineer]
tags: [tradfi, finalize]
related:
  [
    /plans/active/tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16.md,
    /plans/archive/issues/tradfi_cme_expected_coverage_venue_capabilities_drift_2026_08_15.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: review
effort: max
drift_direction: advance-code
depends_on: [tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16]
gate_on_depends: true
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 8, 2026-08-16"
locked_by:
context_scope: [/plans/active/tradfi_cme_expected_coverage_narrow_ao_dispatch_2026_08_16.md]
locked_since:
resolved_by:
---

# Finalize — CME expected_coverage narrowing

- [ ] [REVIEW] P3. Confirm the narrowing landed with evidence (QG green both repos, denominator math verified);
      flip the source `[DESIGN] P3` todo to done; archive this plan once done and unlocked.

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (1 entry).
