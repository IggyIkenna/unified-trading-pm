---
doc_type: plan
title:
  Dex-pool symbol fix/backfill/purge — finalize (reconcile source issue + parent + resolve shared cluster doc + archive)
summary: >-
  Gated closeout for /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md — machine-held via
  depends_on + gate_on_depends: true until all 5 of that plan's todos are done, so this never dispatches early.
  Reconciles the originating bug report (issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md, which
  this whole plan is a direct extraction of — flip it to resolved once the query fix + backfill + purge all land),
  defi_consolidated_closeout_2026_07_18.md's progress log, and the TRADER_JOE_V2/VELODROME_V2/CURVE cluster row in
  issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md (that doc also covers the sibling GMX cluster
  owned by /plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md — do NOT flip the issue doc's own status to
  resolved unless BOTH clusters are independently confirmed closed), then runs the standard 6-step archival ritual.
status: complete
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, subgraph, dex-pools, close-out, finalize, archival]
related:
  [
    /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md,
    /plans/archive/issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [defi_dex_pool_symbol_fix_backfill_purge_2026_07_25]
gate_on_depends: true
source: >-
  Quality-gates finalize-plan-coverage post-gate regression (2026-07-25, ldr_qg_failure escalation on
  unified-trading-pm) — /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md shipped
  `assigned_vm: planning` with >1 todo and no gated finalize plan, per task_template.md §4's operator ruling 2026-07-24.
  Authored to bring the check back to baseline, mirroring sports_closeout_batch1_finalize_2026_07_24.md's
  reconcile-then-archive pattern (single self-contained parent plus its one originating issue doc, not a
  multi-source-doc batch extraction).
assigned_role: backend_engineer
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md,
    /plans/archive/issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
---

> **🟢 COMPLETE 2026-08-02 — ARCHIVED.** Both todos landed: reconciliation (todo 1) verified all 5 fix/backfill/purge
> commits and reconciled all 3 referencing docs; archival (todo 2) moved the parent plan to
> `/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`, repointed every corpus referrer, and
> archived this finalize plan alongside it in the same commit.

# Dex-pool symbol fix/backfill/purge — finalize

> **Machine-gated on `/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`** (`depends_on` +
> `gate_on_depends: true`) — the dispatcher will not queue either todo below until all 5 tasks in that plan are `done`,
> INCLUDING both `[OPERATOR]`-tagged prod-bucket purge todos (lst_rates markers + the now-superseded old dex_pool_state
> data). `sequential: true` because todo 2 (archival) must not run before todo 1 (reconciliation) — the archive ritual's
> codex-alignment check needs the final, reconciled state.

## Todos

- [x] ✅ [REVIEW] P2. **DONE 2026-08-02 (slot-13, review craft) — `unified-trading-pm@bcafefd9c`.** Reconciled
      fix/backfill/purge status into all 3 referencing docs. (1)
      `issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md` — verified all 5 parent-plan todos `[x]`
      with real evidence (`git log`/`git merge-base --is-ancestor` confirmed `market-tick-data-service@63199601` +
      `@0f40a69f` are real, shipped, ancestors of `origin/live-defi-rollout`); flipped `status: open` →
      `status:     resolved` with a verified `resolved_by` citation, closed the `[OPERATOR]` todo by citation. (2)
      `defi_consolidated_closeout_2026_07_18.md` — updated both the FLAGGED-markers-decision passage and the
      dex_pool_state cron-resume gate note from forward-looking to shipped, with the same verified evidence. (3)
      `issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md` — re-checked the
      TRADER_JOE_V2/VELODROME_V2/CURVE + lst_rates clusters (both resolved by the parent plan's 5 todos); also
      independently verified the sibling GMX cluster's owning plan
      (`/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`) carries `status: complete` and is archived — since
      ALL 3 clusters this doc tracks are now closed, flipped its top-level `status: open` → `status: resolved` too (a
      stronger outcome than the todo's own minimum bar of "add a dated note without changing status", justified because
      the GMX check came back closed rather than still-open).
- [x] ✅ [DOC] P3. **DONE 2026-08-02 (slot-12, backend_engineer) — Archived
      `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`** via the standard 6-step ritual (per CLAUDE.md's
      plan-archival rule). Confirmed zero `DEFERRED` markers + `locked_by` empty on both the parent plan and this
      finalize plan. Added the archive banner + flipped `status: active` → `status: complete` on both. Ran the
      codex-alignment check: grepped `codex/` for `messari_basic`/`inputTokens`/`_parse_curve` (the specific
      symbol-resolution bug this plan fixed) — zero hits, no codex doc described that bug's prior-broken behavior, so
      nothing needed correcting. Checked `/codex/02-data/defi-canonical-naming-ssot.md` and the other docs that mention
      TRADER_JOE_V2/VELODROME_V2/CURVE (`instruments-foundation-and-catalogue-completeness.md`,
      `availability-manifest-and-data-status.md`) — all describe unrelated concerns (data_type collapse, G1
      source-coverage gaps, cross-chain pool-address collisions), none reference dex-pool symbol resolution — no update
      needed. No new durable contract resulted requiring a CLAUDE.md change (the two follow-on findings this plan
      surfaced — manifest per-VM-shard flush scaling, catalogue undercoverage vs. historical capture — are already
      tracked in their own separate issue docs with their own todos, not lost). Grepped the corpus for every referrer of
      `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25` (18 files) and
      `defi_dex_pool_symbol_fix_backfill_purge_finalize_2026_07_25` (9 files, 15 unique total across both slugs)
      spanning `plans/active/`, `plans/active/issues/`, `plans/archive/`, and `plans/archive/issues/` — repointed every
      path-formatted/prose `.md` citation to
      `/plans/archive/2026_08/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` (or the `_finalize` twin);
      bare-slug machine fields (`depends_on`/`related`/`source` without `.md`, and task-id references like
      `defi_dex_pool_symbol_fix_backfill_purge-001`) intentionally left untouched per the cross-reference-path
      convention. `plans/active/INDEX.md` needs no manual edit (self-corrects on next `regenerate_active_plan_index.py`
      run); the archived `active_plan_inventory_dashboard_2026_07_24.md` snapshot is a frozen historical record, not
      live-regenerated, left as-is. **Archive folder is `plans/archive/2026_08/`** (keyed on archival date 2026-08-02,
      not the docs' 2026-07-25 creation date — confirmed via existing 2026_08/ entries' commit dates). Both
      `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md` and this finalize plan moved to `plans/archive/2026_08/`
      in the same commit.

## Codex SSOTs

- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — referenced by both purge todos in the parent plan;
  confirm no update needed here during the codex-alignment check.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
