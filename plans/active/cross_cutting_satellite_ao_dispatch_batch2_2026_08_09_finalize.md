---
doc_type: plan
title: Cross-cutting satellite AO batch 2 — finalize (reconcile source docs + archive)
summary: >-
  Gated closeout for `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` — machine-held via `depends_on` +
  `gate_on_depends: true` until all 22 todos are done. Reconciles each of the 6 distinct `instruments_master` source
  docs' checkboxes independently (citing the shipped commit per todo), then archives the batch doc via the standard
  6-step ritual.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cross-cutting, ao-dispatch, close-out, batch-2, satellite-docs, archival]
related:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md,
    /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md,
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /plans/active/instruments_completion_tracker_2026_07_06.md,
    /plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md,
    /plans/archive/2026_08/mvp_scope_catalogue_tagging_2026_06_08.md,
    /plans/active/is_catalogue_g1_root_audit_log_2026_07_24.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cross_cutting_satellite_ao_dispatch_batch2_2026_08_09]
gate_on_depends: true
source: >-
  Satellite-batch-extraction sweep 2026-08-09, per `task_template.md` §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan.
assigned_role: data_engineering
effort: high
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md,
    /plans/active/instruments_foundation_phase0_cross_cutting_2026_07_24.md,
    /plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# Cross-cutting satellite AO batch 2 — finalize

> **Machine-gated on `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 22 tasks in that batch are `done`.
> `sequential: true` because todo 2 (archival) must run after todo 1 (reconciliation).

## Todos

- [ ] [REVIEW] P1. Reconcile all 6 distinct source docs' checkboxes against batch 2's 22 now-done todos — for each done
      todo, flip the corresponding checkbox/section in its named source doc (each todo's text ends with "Source:
      `<doc>.md`"), citing the batch commit(s) that shipped it (verify the cited commit actually exists before citing
      it). For each source doc, after flipping, re-check whether it now has 0 open todos remaining (checkbox AND
      prose-form) — flip `status` to `resolved` only if it genuinely reaches 0. Done when: all 22 source-doc
      checkboxes/sections are flipped with verified evidence.
- [ ] [DOC] P1. Archive `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule) once todo 1 is done: add the archive banner → run the codex-alignment check
      (confirm no new durable contract from this batch) → grep the corpus for every referrer of this doc and fix each
      path to point at the archived location → clear `locked_by` (confirm already empty). Done when: the plan is moved
      to `plans/archive/2026_08/`, every corpus referrer resolves to the new path, and this finalize doc itself is
      archived alongside it in the same commit.

## Progress Log

- **context-scout 2026-08-15**: refreshed context_scope (4 entries) -- added the plan-completion-and-archival-
  discipline codex SSOT (todo 2's 6-step ritual cites "CLAUDE.md's plan-archival rule" but not the codex doc itself);
  kept the gated parent batch doc (has all 22 todos' `Source:` citations) plus the 2 of its 6 named source docs with the
  most citations (9 mentions each) -- the other 4 source docs (`instruments_completion_tracker_2026_07_06.md`,
  `instruments_store_cf_canonicalization_single_walk_2026_07_24.md`, `mvp_scope_catalogue_tagging_2026_06_08.md`,
  `is_catalogue_g1_root_audit_log_2026_07_24.md`) are already discoverable via the batch doc's own per-todo `Source:`
  lines and this doc's `related:` frontmatter, so are not duplicated here.
