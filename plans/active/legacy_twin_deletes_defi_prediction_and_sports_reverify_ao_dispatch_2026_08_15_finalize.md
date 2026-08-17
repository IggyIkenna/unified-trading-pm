---
doc_type: plan
title: Finalize — legacy-twin deletes (defi/prediction) + sports re-verify
summary: Gated finalize companion for legacy_twin_deletes_defi_prediction_and_sports_reverify_ao_dispatch_2026_08_15.md.
status: active
nature: process
asset_group: [defi, prediction, sports]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [manifest, finalize]
related: [/plans/active/legacy_twin_deletes_defi_prediction_and_sports_reverify_ao_dispatch_2026_08_15.md]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.15
assigned_role: review
effort: max
drift_direction: advance-code
depends_on: [legacy_twin_deletes_defi_prediction_and_sports_reverify_ao_dispatch_2026_08_15]
gate_on_depends: true
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A, 2026-08-15"
locked_by:
context_scope: [/plans/active/legacy_twin_deletes_defi_prediction_and_sports_reverify_ao_dispatch_2026_08_15.md]
locked_since:
resolved_by:
---

# Finalize — legacy-twin deletes (defi/prediction) + sports re-verify

- [ ] [REVIEW] P2. Confirm all todos landed with evidence (defi/prediction delete-after-copy evidence, and the sports
      fresh twin-coverage measurement — NOT just "checked", the actual numbers against the 2 call sites and Part 5 %);
      the parent plan has grown from 2 headline todos to 5 (todos 3-5 were spawned as follow-up work during
      execution) — confirm all 5, not just the original 2; update `instruments_completion_tracker_2026_07_06.md` with
      the sports result either way; archive the parent plan once done and unlocked. [Reworded 2026-08-17
      (plan_reconciler): "both" → "all" — the parent doc now has 5 todos, not 2.]
