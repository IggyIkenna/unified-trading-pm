---
doc_type: plan
title: Sports taxonomy P2 — finalize (prove the exception sets are empty + reconcile + archive)
summary: >-
  Gated closeout for sports_taxonomy_p2_migration_2026_08_08.md. The migration's real success criterion is not "the
  panel is green" — it is that the accepted-exception sets reached EMPTY rather than being re-populated, since a green
  panel achieved by adding exceptions is the exact failure this whole chain exists to undo. This finalize proves that
  independently, reconciles the API-Football campaign's gate release, confirms every delete ran through the §3a
  reversibility path, and archives P2.
status: active
nature: process
asset_group: [sports]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [sports, migration, finalize, archival, delete-safety, exception-sets]
related:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /plans/archive/2026_08/issues/sports_af_full_entity_completion_2026_08_03.md,
    /plans/archive/issues/sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: 2026-08-08
last_updated: 2026-08-08
parent_epic: sports_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.64
assigned_role: data_engineering
effort: high
supersedes:
superseded_by:
resolved_by:
drift_direction: advance-code
depends_on: [sports_taxonomy_p2_migration_2026_08_08]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/sports_taxonomy_p2_migration_2026_08_08.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
source: >-
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan.
locked_by:
locked_since:
---

# Sports taxonomy P2 — finalize

> **Machine-gated** on `sports_taxonomy_p2_migration_2026_08_08.md`.

## Todos

- [ ] [REVIEW] P1. **Prove the accepted-exception sets are EMPTY, measured not asserted.** Read the shipped UAC and
      confirm `SPORTS_ODDS_API_ACCEPTED_NONCANONICAL_BOOKMAKERS`, `SPORTS_VENUE_ACCEPTED_CROSS_AG_BLEED` and
      `SPORTS_DATA_TYPE_ACCEPTED_STALE_UPPERCASE_RESIDUE` all have zero members, AND that no NEW exception set was
      introduced anywhere to absorb the difference. If any set is non-empty or a new one exists, the migration is
      incomplete — file it as a `- [ ]` todo rather than passing this doc. **Done when**: all three sets are measured
      empty and no replacement set exists.
- [ ] [REVIEW] P1. **Re-run the distinct-values comparison end to end.** The rollup's distinct venue and data_type sets
      must equal the manifest's, with nothing hidden — the audit's starting state was 31 venues / 10 data types in the
      manifest against 10 / 7 rendered. Report both counts post-migration. **Done when**: rollup and manifest agree and
      the counts are recorded.
- [ ] [REVIEW] P1. **Confirm every prod delete ran through the §3a reversibility path.** For each purge todo, verify a
      FRESH, same-run `gcs_bucket_soft_delete_retention_seconds()` check of >= 604800 was recorded before the delete —
      not assumed, not carried from a prior run, not from the plan's own text. Any delete lacking its check is a
      protocol violation and must be reported, not quietly accepted. **Done when**: every delete has a recorded same-run
      check.
- [ ] [REVIEW] P1. **Reconcile the API-Football gate.** Confirm `sports_af_full_entity_completion_2026_08_03.md` had
      genuinely converged before P2's rename executed (its P0 re-census closed), and REMOVE the cross-plan banner added
      to it on 2026-08-08 (`unified-trading-pm@3bb3214bdf`) now that the ordering constraint has been discharged — a
      stale banner is misinformation for the next reader. **Done when**: convergence is evidenced and the banner is
      removed or updated to a past-tense record.
- [x] ✅ [REVIEW] P2. **DONE — already satisfied, verified 2026-08-17 (na-eligibility-audit, dispatch agt-1c51ee).**
      Correct the historical record in
      `/plans/archive/issues/sports_distinct_values_prod_freeze_and_venue_writer_bugs_2026_08_04.md` (archived this
      same date). That doc already carries a dated `⚠️ CORRECTION 2026-08-08` banner at its top stating exactly this:
      the "RESOLVED 2026-08-05... all 0/0 non-canonical" headline was produced by accepted-exceptions, not real
      canonicalisation, with the measured real counts (31 venues/10 data types vs. the panel's rendered 10/7) and a
      pointer to `sports_taxonomy_p3_consumers_2026_08_08.md` as the doc that owns genuine canonicalisation. This
      todo's own done-when ("the doc carries the correction") was met the same day this finalize plan was authored;
      it was simply never flipped.
- [ ] [DOC] P2. **Archive `sports_taxonomy_p2_migration_2026_08_08.md`** via the standard 6-step ritual, including the
      codex-alignment check against the four-surface reconciliation and delete-safety SSOTs, the corpus-wide
      referrer-path fixup, and archiving this finalize doc alongside it in the same commit. **Done when**: the plan is
      in `plans/archive/2026_08/`, every referrer resolves, and this doc is archived with it.

## Progress Log

- **2026-08-08** — Authored alongside the parent per the finalize-plan-coverage rule.
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries) -- re-verified all 4 entries still
  resolve on disk; unchanged.
