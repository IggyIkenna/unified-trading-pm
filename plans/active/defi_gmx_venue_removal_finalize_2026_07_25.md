---
doc_type: plan
title: GMX venue removal — finalize (reconcile parent/issue docs + resolve deferred purge todo + archive)
summary: >-
  Gated closeout for defi_gmx_venue_removal_2026_07_25.md — machine-held via depends_on + gate_on_depends: true until
  all 8 of that plan's todos are done, so this never dispatches early. Reconciles GMX-removal status back into
  defi_consolidated_closeout_2026_07_18.md's progress log and
  issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md's GMX cluster row (that issue doc also covers
  the sibling TRADER_JOE_V2/VELODROME_V2/CURVE cluster owned by defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md —
  do NOT flip the issue doc's own status to resolved unless BOTH clusters are independently confirmed closed), re-checks
  the parent plan's `[OPERATOR]`-tagged GCS-purge todo (deliberately un-gated at authoring time, timing left to operator
  judgment) to confirm it actually landed before archiving, then runs the standard 6-step archival ritual.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [defi, gmx, venue-removal, close-out, finalize, archival]
related:
  [
    /plans/active/defi_gmx_venue_removal_2026_07_25.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
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
depends_on: [defi_gmx_venue_removal_2026_07_25]
gate_on_depends: true
source: >-
  Quality-gates finalize-plan-coverage post-gate regression (2026-07-25, ldr_qg_failure escalation on
  unified-trading-pm) — defi_gmx_venue_removal_2026_07_25.md shipped `assigned_vm: planning` with >1 todo and no gated
  finalize plan, per task_template.md §4's operator ruling 2026-07-24. Authored to bring the check back to baseline,
  mirroring sports_closeout_batch1_finalize_2026_07_24.md's reconcile-then-archive pattern (single self-contained
  parent, not a multi-source-doc batch extraction).
assigned_role: backend_engineer
sequential: true
drift_direction: advance-code
---

# GMX venue removal — finalize

> **Machine-gated on `defi_gmx_venue_removal_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) — the dispatcher
> will not queue either todo below until all 8 tasks in that plan are `done`, INCLUDING the `[OPERATOR]`-tagged
> GCS-purge todo (which was deliberately left un-gated/timing-at-operator-judgment in the parent — todo 1 below
> re-verifies it actually landed, since `gate_on_depends` alone doesn't distinguish "code todos done" from "the operator
> todo also done"). `sequential: true` because todo 2 (archival) must not run before todo 1 (reconciliation) — the
> archive ritual's codex-alignment check needs the final, reconciled state.

## Todos

- [x] ✅ [REVIEW] P2. **Reconcile GMX-removal status into the referencing docs.** (1)
      `defi_consolidated_closeout_2026_07_18.md` — its progress log (around the GMX/FLAGGED-marker discussion, ~line
      642-660) currently describes the removal as a forward-looking decision ("operator decided: remove GMX entirely —
      `defi_gmx_venue_removal_2026_07_25.md` (8 todos, AO-dispatched...)"); update that passage to state the removal
      shipped, citing the actual commit(s) across the 6 code repos + the GCS-purge evidence — verify each cited commit
      exists (`git log`/`git show`) before citing, do not copy the parent plan's own evidence lines uncritically. (2)
      `issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md` — re-check its GMX cluster row/section: if
      the parent plan's `[OPERATOR]` GCS-purge todo has landed (zero `venue=GMX` objects/manifest rows, per that todo's
      own done-when), the GMX portion of this issue doc is resolved; **do NOT flip the doc's own top-level `status` to
      `resolved`** unless the sibling TRADER_JOE_V2/VELODROME_V2/CURVE cluster (owned by
      `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`, a separate in-flight plan) is ALSO independently
      confirmed closed — check that plan's own status first. If only the GMX cluster is closed, add a dated note to the
      issue doc recording that half as resolved without changing its overall `status`. **Done when**: both docs reflect
      the true current state with verified evidence, and the shared issue doc's `status` field is touched only if
      genuinely warranted by both clusters' real state (not just this plan's half). — unified-trading-pm (this commit).
      Verified all 8 GMX-removal commits exist (`git log`, not copied uncritically): unified-api-contracts@18d53d63,
      market-tick-data-service@68407ae5, instruments-service@0214bb3c+2de3418e, execution-service@09a828ed,
      strategy-service@ca818ff8, unified-trading-library@f22e516f, plus the `[OPERATOR]` GCS+manifest purge (5,374
      `venue=GMX` manifest rows dropped, zero objects remain) and the docs commit (unified-trading-pm@bfda5df5b).
      Updated `defi_consolidated_closeout_2026_07_18.md`'s GMX passage from forward-looking to shipped-with-citations.
      Re-checked `defi_dex_pool_symbol_fix_backfill_purge_2026_07_25.md`: still 0/5 todos done — added a dated note to
      `issues/defi_migrated_marker_flagged_root_cause_clusters_2026_07_25.md` confirming the GMX cluster closed while
      explicitly leaving the doc's overall `status: open` untouched (sibling TRADER_JOE_V2/VELODROME_V2/CURVE +
      lst_rates-MAKER/ETHENA clusters remain unshipped).
- [ ] [DOC] P3. **Archive `defi_gmx_venue_removal_2026_07_25.md`** via the standard 6-step ritual (per CLAUDE.md's
      plan-archival rule): confirm zero `DEFERRED` markers remain (the parent plan has none by design — its `[OPERATOR]`
      todo is timing-gated by operator judgment, not a deferral) → add the archive banner + flip `status: active` →
      `status: complete` → run the codex-alignment check (does `/codex/02-data/defi-canonical-naming-ssot.md` or any
      other codex doc still list GMX as a supported venue — update if so) → confirm no new durable contract resulted
      requiring a CLAUDE.md/codex change → grep the corpus for every referrer of `defi_gmx_venue_removal_2026_07_25`
      (including this doc's own `depends_on` self-reference, this doc's `related:` list, and the two docs touched in
      todo 1) and repoint each to the archived path → confirm `locked_by` is empty. **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize plan is archived
      alongside it in the same commit (nothing left to gate once both are done).
