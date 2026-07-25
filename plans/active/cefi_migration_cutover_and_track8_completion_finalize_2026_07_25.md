---
doc_type: plan
title: CeFi migration cutover + Track 8 completion — finalize (reconcile checkboxes + archive)
summary: >-
  Gated closeout for cefi_migration_cutover_and_track8_completion_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 5 of that plan's sequential todos are done. Reconciles the parent
  (cefi_consolidated_closeout_2026_07_18.md) Track-1/Track-8 checkboxes AND the plan's own two true source docs
  (cefi_residual_followups_after_honest_done_2026_07_17.md,
  cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md), then archives the now-fully-done
  cutover plan.
status: draft
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, close-out, canonicalisation, migration, cutover, archival]
related:
  [
    /plans/active/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /plans/active/issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_migration_cutover_and_track8_completion_2026_07_25]
gate_on_depends: true
source: >-
  Per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize
  plan. Precedent: cefi_satellite_ao_dispatch_batch1_2026_07_25.md /
  cefi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# CeFi migration cutover + Track 8 completion — finalize

> **Machine-gated on `cefi_migration_cutover_and_track8_completion_2026_07_25.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 5 tasks in that plan are `done`.
> `sequential: true` because todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P0. **Reconcile `cefi_consolidated_closeout_2026_07_18.md`'s Track-1/Track-8 checkboxes.** Flip: the
      Track-1 "Execute the minutes-gap hybrid cutover" checkbox; the Operator-dispositions DERIBIT quote-fix checkbox;
      Track 8's `:PERP:` → `:PERPETUAL:` rewrite checkbox (note the on-disk-rename half only — the writer-side half is
      reconciled separately by `cefi_consolidated_native_ao_extract_2026_07_25_finalize.md`); Track 8's POST-CUTOVER
      smoke-check/downloader-flip checkbox; Track 8's enumeration-audit terminal-checkpoint checkbox. Cite the shipped
      commit(s) for each — verify each cited commit actually exists (resolves as an ancestor of
      `origin/live-defi-rollout`) before citing it. Repo: unified-trading-pm. **Done when**: all 5 named checkboxes/
      sections in the parent doc are flipped with verified evidence.
- [ ] [REVIEW] P1. **Reconcile the 2 true source docs.** (1) `cefi_residual_followups_after_honest_done_2026_07_17.md`'s
      own Phase-1/2 todos (the cutover's real vehicle) — flip with the same cited evidence as todo 1 above. (2)
      `cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md` — confirm its findings are now
      resolved by the POST-CUTOVER flip and update/close it accordingly. Repo: unified-trading-pm. **Done when**: both
      source docs' checkboxes/status reflect the shipped work, cited with verified commits.
- [ ] [DOC] P2. **Archive `cefi_migration_cutover_and_track8_completion_2026_07_25.md`** via the standard 6-step ritual
      (per CLAUDE.md's plan-archival rule): confirm no Deferred items remain untracked → add the archive banner → run
      the codex-alignment check → grep the corpus for every referrer of
      `cefi_migration_cutover_and_track8_completion_2026_07_25` and fix each path to point at the archived location →
      clear `locked_by` (already empty, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.
