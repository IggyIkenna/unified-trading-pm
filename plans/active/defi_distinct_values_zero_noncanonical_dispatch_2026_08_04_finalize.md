---
doc_type: plan
title: DeFi distinct-values zero-non-canonical dispatch — finalize
summary: >-
  Gated closeout for defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md — machine-held via depends_on +
  gate_on_depends until every todo in that plan is done. Reconciles the plan's own checkboxes (self-contained, not a
  batch extraction from other source docs) against LIVE state (the source doc itself warns every "in progress" line
  needs a live git-log/manifest check, not blind trust), re-checks whether any deferred item's gate has since cleared,
  and runs the standard 6-step archival ritual once fully done.
status: active
nature: process
asset_group: [defi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, canonicalisation, close-out, finalize]
related:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.4
assigned_role: review
effort: low
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_distinct_values_zero_noncanonical_dispatch_2026_08_04]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn the plan was reclassified assigned_vm: NA -> planning by a /na-eligibility-audit full-sweep run
  2026-08-13 (every open todo was bounded/deterministic). Ships status: active (not draft) per the /ag-closeout-audit
  skill's 2026-07-30 finding: gate_on_depends already machine-holds every task until the plan's own todos are done, so a
  second draft-gate is a redundant, easy-to-forget manual flip.
---

# DeFi distinct-values zero-non-canonical dispatch — finalize

> **Machine-gated on `/plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that plan is `done`.

## Todos

- [ ] [REVIEW] P2. Reconcile every completed todo in `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` —
      the doc explicitly says every "in progress" line needs a LIVE status check (git log / manifest read), not to be
      trusted at face value; re-verify each "done" claim against a real commit sha and re-run the axis's
      zero-non-canonical check (venues / chains / instrument_types / data_types) rather than trusting the checkbox
      alone. Re-check any deferred item's gate. Done when: every checkbox is verified evidence-backed against live
      corpus state, and every axis is confirmed zero non-canonical (not merely a reduced count).
- [ ] [REVIEW] P2. Once the source plan has zero open todos and the reconciliation above is clean, run the standard
      6-step archival ritual on `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`, then archive this
      finalize plan too. Done when: the source plan and this finalize plan are both under `plans/archive/`, and
      `regenerate_active_plan_inventory.py` reports zero orphan referrers to either.
