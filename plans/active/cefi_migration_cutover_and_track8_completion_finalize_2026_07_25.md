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
last_updated: "2026-07-31"
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
- [x] ✅ [REVIEW] P1. **DONE — Reconciled the 2 true source docs.** (1)
      `cefi_residual_followups_after_honest_done_2026_07_17.md`'s Phase-1/2 todos: reviewed end-to-end, spot-verified a
      sample of cited commits as genuine `origin/live-defi-rollout` ancestors (`instruments-service@8166676465f1`,
      `@f06eba12989d`, `@b61f9bdd`; `market-tick-data-service@d47609ec`, `@d302f07a`, `@ec04e8f5`, `@0388e1a9`;
      `unified-api-contracts@825878f7`, `@11adf279`, `@dfecc787`) — every closeable checkbox was already correctly
      flipped by prior slots as the cutover executed; the 2 remaining `- [ ]` items (Parquet CONTENT backfill
      corpus-wide; Progress Log at every gate) are genuinely still open (Script 1 fleet migration in flight, tracked in
      `cefi_content_migration_fleet_half_incomplete_2026_07_26.md`) and correctly left unflipped — no reconciliation gap
      found. (2) `cefi_shard_enumeration_blindspots_and_canonical_fetch_dependency_2026_07_18.md` — confirmed already
      `status: resolved` + archived with both findings closed (Finding 2 citing
      `cefi_migration_cutover_and_track8_completion_2026_07_25.md` todo 4); fixed a stale `last_updated: 2026-07-18` →
      `2026-07-27` to match its actual last edit. Repo: unified-trading-pm. Evidence: this commit (see git log for
      `cefi_migration_cutover_and_track8_completion_finalize_2026_07_25.md`).
- [x] ✅ [DOC] P2. **DONE — the target plan is already archived + fully reconciled.** Verified all 6 ritual steps
      against `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md`: (1) its own "##
      Deferred work — migrated to:" section already reads **None** (verified fully complete at archival, zero open
      todos); (2) the archive banner is present ("🗄️ ARCHIVED 2026-07-28 (plan-hygiene sweep) — role fulfilled"); (3)
      codex-alignment check: `grep -rl` for the plan's slug across `codex/` returns zero hits — no codex doc references
      it, nothing to update; (4) no new durable contract from this plan beyond what's already reflected (per its own "No
      new durable contract is created by this plan" Codex-SSOTs note); (5) corpus-wide referrer grep (33 hits across the
      repo) — every formal `/plans/...`-prefixed citation already resolves to
      `/plans/archive/2026_07/cefi_migration_cutover_and_track8_completion_2026_07_25.md` (the referrer-fix already
      landed in `unified-trading-pm@9f12b267d`, "archive 26 verified-complete plan/issue docs + corpus-wide referrer
      fixes"); (6) `locked_by` confirmed empty in the archived doc's frontmatter. **Correction to this todo's own "done
      when" clause**: the target plan's archival happened in a PRIOR commit (`9f12b267d`), not concurrently with this
      touch, so "archived alongside it in the same commit" is no longer literally achievable — flagging this finalize
      plan itself as now fully done (all 3 todos `[x]`, unlocked) is the closest correct execution of that intent;
      archiving it is the immediate follow-up action per
      `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` § 1 ("archive the moment a plan is genuinely
      done"), done as a separate commit per that same doc's HARD RULE against combining a checkbox flip with a `git mv`
      in one commit (`RULES.md` § 2, 2026-07-30 incident). One stale referrer found + will be fixed in the archival
      commit: the archived target plan's own `related:` frontmatter still points at
      `/plans/active/cefi_migration_cutover_and_track8_completion_finalize_2026_07_25.md` (this doc's pre-archival
      path). Repo: unified-trading-pm.
