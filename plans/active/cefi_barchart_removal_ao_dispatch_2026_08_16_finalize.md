---
doc_type: plan
title: Finalize — Barchart removal fleet-wide
summary: Gated finalize companion for cefi_barchart_removal_ao_dispatch_2026_08_16.md.
status: active
nature: process
asset_group: [cefi]
stage: [meta]
repos: [unified-api-contracts, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [cefi, finalize]
related:
  [
    /plans/active/cefi_barchart_removal_ao_dispatch_2026_08_16.md,
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: review
effort: max
drift_direction: advance-code
depends_on: [cefi_barchart_removal_ao_dispatch_2026_08_16]
gate_on_depends: true
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 6, 2026-08-16"
locked_by:
context_scope: [/plans/active/cefi_barchart_removal_ao_dispatch_2026_08_16.md]
locked_since:
resolved_by:
---

# Finalize — Barchart removal fleet-wide

- [ ] [REVIEW] P2. Confirm the removal landed with evidence (parity gate green, no `barchart` source references
      remain); flip the Phase-5 checkbox in `cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` line 248
      to done with a sha; archive this plan once done and unlocked.
