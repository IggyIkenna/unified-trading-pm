---
doc_type: plan
title: Finalize — MTDS venue-key casing canonicalization
summary: Gated finalize companion for mtds_venue_key_casing_reverify_then_execute_ao_dispatch_2026_08_16.md.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cross-cutting, finalize]
related:
  [
    /plans/active/mtds_venue_key_casing_reverify_then_execute_ao_dispatch_2026_08_16.md,
    /plans/active/issues/mtds_venue_key_casing_canonicalization_unexecuted_2026_08_13.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: review
effort: max
drift_direction: advance-code
depends_on: [mtds_venue_key_casing_reverify_then_execute_ao_dispatch_2026_08_16]
gate_on_depends: true
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 10, 2026-08-16"
locked_by:
context_scope: [/plans/active/mtds_venue_key_casing_reverify_then_execute_ao_dispatch_2026_08_16.md]
locked_since:
resolved_by:
---

# Finalize — MTDS venue-key casing canonicalization

- [ ] [REVIEW] P2. Confirm the canonicalization landed with evidence (QG green, fallback removed, no live
      venue-key lookup miss); flip the source todo to done; archive this plan once done and unlocked.
