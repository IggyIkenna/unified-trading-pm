---
doc_type: plan
title:
  Dex-pool symbol fix/backfill/purge — finalize (reconcile source issue + parent + resolve shared cluster doc + archive)
summary: >-
  Gated closeout for defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md — machine-held via depends_on +
  gate_on_depends: true until all 5 of that plan's todos are done, so this never dispatches early. Reconciles the
  originating bug report (issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md, which this whole plan
  is a direct extraction of — flip it to resolved once the query fix + backfill + purge all land),
  defi_consolidated_closeout_2026_07_18.md's progress log, and the TRADER_JOE_V2/VELODROME_V2/CURVE cluster row in
  issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md (that doc also covers the sibling GMX cluster
  owned by /plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md — do NOT flip the issue doc's own status to
  resolved unless BOTH clusters are independently confirmed closed), then runs the standard 6-step archival ritual.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, subgraph, dex-pools, close-out, finalize, archival]
related:
  [
    /plans/active/defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md,
    /plans/active/issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md,
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
  unified-trading-pm) — defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md shipped `assigned_vm: planning` with >1
  todo and no gated finalize plan, per task_template.md §4's operator ruling 2026-07-24. Authored to bring the check
  back to baseline, mirroring sports_closeout_batch1_finalize_2026_07_24.md's reconcile-then-archive pattern (single
  self-contained parent plus its one originating issue doc, not a multi-source-doc batch extraction).
assigned_role: backend_engineer
sequential: true
drift_direction: advance-code
---

# Dex-pool symbol fix/backfill/purge — finalize

> **Machine-gated on `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`)
> — the dispatcher will not queue either todo below until all 5 tasks in that plan are `done`, INCLUDING both
> `[OPERATOR]`-tagged prod-bucket purge todos (lst_rates markers + the now-superseded old dex_pool_state data).
> `sequential: true` because todo 2 (archival) must not run before todo 1 (reconciliation) — the archive ritual's
> codex-alignment check needs the final, reconciled state.

## Todos

- [ ] [REVIEW] P2. **Reconcile fix/backfill/purge status into the referencing docs.** (1)
      `issues/defi_dex_pools_subgraph_query_missing_input_tokens_2026_07_25.md` — this whole plan is a direct extraction
      of this bug report; once the query-fix + live-test + backfill + purge todos are all `done`, flip this issue doc's
      `status: open` → `status: resolved` with `resolved_by` citing the actual shipped commit(s) — verify each cited
      commit exists (`git log`/`git show`) before citing, do not copy the parent plan's own evidence lines uncritically.
      (2) `defi_consolidated_closeout_2026_07_18.md` — update its progress-log passage describing this
      fix/backfill/purge as forward-looking to instead state it shipped, with evidence. (3)
      `issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md` — re-check its
      TRADER_JOE_V2/VELODROME_V2/CURVE cluster row: if the parent plan's purge todos landed (zero unattributed
      address-keyed `dex_pool_state` leaves remaining within the confirmed-recoverable range, per that todo's own
      done-when), this cluster's portion is resolved; **do NOT flip the doc's own top-level `status` to `resolved`**
      unless the sibling GMX cluster (owned by `/plans/archive/2026_07/defi_gmx_venue_removal_2026_07_25.md`, a separate
      in-flight plan) is ALSO independently confirmed closed — check that plan's own status first. If only this cluster
      is closed, add a dated note to the issue doc recording that half as resolved without changing its overall
      `status`. **Done when**: all 3 docs reflect the true current state with verified evidence, and the shared
      root-cause-clusters issue doc's `status` field is touched only if genuinely warranted by both clusters' real state
      (not just this plan's half).
- [ ] [DOC] P3. **Archive `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): confirm zero `DEFERRED` markers remain → add the archive banner + flip
      `status: active` → `status: complete` → run the codex-alignment check (does any codex doc describing dex-pool
      subgraph coverage or symbol resolution need a status update — e.g. `/codex/02-data/defi-canonical-naming-ssot.md`)
      → confirm no new durable contract resulted requiring a CLAUDE.md/codex change → grep the corpus for every referrer
      of `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25` (including this doc's own `depends_on` self-reference,
      this doc's `related:` list, and the docs touched in todo 1) and repoint each to the archived path → confirm
      `locked_by` is empty. **Done when**: the plan is moved to `plans/archive/2026_07/`, every corpus referrer resolves
      to the new path, and this finalize plan is archived alongside it in the same commit (nothing left to gate once
      both are done).

## Codex SSOTs

- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` — referenced by both purge todos in the parent plan;
  confirm no update needed here during the codex-alignment check.
