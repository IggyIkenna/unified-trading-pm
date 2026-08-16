---
doc_type: plan
title: Finalize — OKX-FUTURES xperp wire-format fix
summary: Gated finalize companion for cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16.md.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cefi, finalize]
related:
  [
    /plans/active/cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16.md,
    /plans/active/issues/okx_futures_instid_marker_convention_mismatch_2026_07_30.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: review
effort: max
drift_direction: advance-code
depends_on: [cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16]
gate_on_depends: true
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 6, 2026-08-16"
locked_by:
context_scope: [/plans/active/cefi_okx_futures_xperp_marker_ao_dispatch_2026_08_16.md]
locked_since:
resolved_by:
---

# Finalize — OKX-FUTURES xperp wire-format fix

- [ ] [REVIEW] P2. Confirm the fix landed with evidence (parity test green, live subscriptions for xperp
      contracts confirmed non-zero); flip the `[OPERATOR]` P1 todo in
      `okx_futures_instid_marker_convention_mismatch_2026_07_30.md` to done with a sha; archive this plan once
      done and unlocked.
