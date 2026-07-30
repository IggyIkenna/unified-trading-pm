---
doc_type: plan
title: CeFi migration cutover + Track 8 completion — finalize (reconcile checkboxes + archive)
summary: >-
  Gated closeout for /plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md — machine-held
  via depends_on + gate_on_depends: true until all 5 of that plan's sequential todos are done. Reconciles the parent
  (cefi_consolidated_closeout_2026_07_18.md) Track-1/Track-8 checkboxes AND the plan's own two true source docs
  (cefi_residual_followups_after_honest_done_2026_07_17.md,
  cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md), then archives the now-fully-done
  cutover plan.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, close-out, canonicalisation, migration, cutover, archival]
related:
  [
    /plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /plans/archive/issues/cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-30"
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

> **Machine-gated on `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`**
> (`depends_on` + `gate_on_depends: true`) — the dispatcher will not queue any todo below until all 5 tasks in that plan
> are `done`. `sequential: true` because todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run
> last.

## Todos

- [x] ✅ [REVIEW] P0. **DONE — Reconciled `cefi_consolidated_closeout_2026_07_18.md`'s Track-1/Track-8 checkboxes.**
      Flipped all 5 named checkboxes with cited evidence, each commit verified as an ancestor of
      `origin/live-defi-rollout` before citing: Track-1 "Execute the minutes-gap hybrid cutover" (all 4 scripts'
      `EXIT_STATUS=0`, idempotency-verified); Operator-dispositions DERIBIT quote-fix (`instruments-service@d72edcf7` +
      `@b2e084fa`); Track 8's `:PERP:` → `:PERPETUAL:` rewrite, on-disk-rename half only (0 `:PERP:`-form rows
      before/after, DERIBIT collision class left honest-raw per its own ruling); Track 8's POST-CUTOVER
      smoke-check/downloader flip (`market-tick-data-service@a4f90769`, live-refetch residual closed 2026-07-28); Track
      8's enumeration-audit terminal checkpoint (99.49% canonical `instrument_id`, 8,790,637/ 8,880,557). Repo:
      unified-trading-pm. Evidence: `unified-trading-pm@fde8fca09`.
- [ ] [REVIEW] P1. **Reconcile the 2 true source docs.** (1) `cefi_residual_followups_after_honest_done_2026_07_17.md`'s
      own Phase-1/2 todos (the cutover's real vehicle) — flip with the same cited evidence as todo 1 above. (2)
      `cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md` — confirm its findings are now
      resolved by the POST-CUTOVER flip and update/close it accordingly. Repo: unified-trading-pm. **Done when**: both
      source docs' checkboxes/status reflect the shipped work, cited with verified commits.
- [ ] [DOC] P2. **Archive `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`** via the
      standard 6-step ritual (per CLAUDE.md's plan-archival rule): confirm no Deferred items remain untracked → add the
      archive banner → run the codex-alignment check → grep the corpus for every referrer of
      `cefi_migration_cutover_and_track8_completion_2026_07_25` and fix each path to point at the archived location →
      clear `locked_by` (already empty, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every
      corpus referrer resolves to the new path, and this finalize doc itself gets archived alongside it in the same
      commit.
