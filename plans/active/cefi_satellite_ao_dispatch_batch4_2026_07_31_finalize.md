---
doc_type: plan
title: CeFi satellite AO batch 4 — finalize (reconcile source docs + re-check deferrals + archive)
summary: >-
  Gated closeout for cefi_satellite_ao_dispatch_batch4_2026_07_31.md — machine-held via depends_on + gate_on_depends:
  true until all 7 of that plan's todos are done. Mirrors the batch1/batch2/batch3 finalize pattern: reconcile each
  source doc's checkboxes once its batch-4 todo lands, re-check batch4's own Deferred items (the parked cross-tranche
  estate_orphan_assessment conflict, the shard24 operator-gate, and the onchain_venues_mislabeled prod-GCS residual) for
  any whose gate has since cleared, then archive batch4 via the standard 6-step ritual.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-4, satellite-docs, archival]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch4_2026_07_31.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/active/cefi_satellite_ao_dispatch_batch3_finalize_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-31"
last_updated: "2026-07-31"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.35
estimate_calibrated_ai_days: 0.28
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_satellite_ao_dispatch_batch4_2026_07_31]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-31 (scheduled autonomous dispatch, agent-orchestrator slot 4), per
  task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs a companion gated finalize plan,
  mirroring the cefi batch1/batch2/batch3 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# CeFi satellite AO batch 4 — finalize

> **Status: active from the start (2026-07-30 ruling — no double gate).** `gate_on_depends: true` already machine-holds
> every todo below until batch4's own 7 tasks are `done`, regardless of batch4's own `status` (draft or active) — see
> `cefi_satellite_ao_dispatch_batch3_finalize_2026_07_26.md`'s own header for the ruling record. Only the batch itself
> needs `status: draft` + explicit operator approval; this finalize plan carries no independent judgment call.

> **Machine-gated on `cefi_satellite_ao_dispatch_batch4_2026_07_31.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 7 tasks in that plan are `done`. `sequential: true` because todo 2
> depends on todo 1's reconciliation, and todo 3 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 7 distinct source docs' checkboxes.** Batch 4's 7 todos draw from 7 source docs:
      `issues/bybit_futures_chain_write_shape_2026_07_13.md`,
      `issues/cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30.md`,
      `issues/cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md`,
      `issues/cefi_content_migration_shard13_network_error_and_checkpoint_resume_bug_2026_07_31.md`,
      `issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md`,
      `issues/mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` (cefi-scoped checkboxes only — leave the
      sports-scoped item open), `issues/onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` (item 4 of 4 only —
      leave items 1-3 open, they were deliberately not batched). For each landed batch-4 todo, flip the corresponding
      checkbox/section in its named source doc citing the shipping commit — **verify the commit exists and is reachable
      on `origin/live-defi-rollout` before citing it**. Then, per source doc, re-check whether it now has 0 open items
      remaining in **both** checkbox AND prose form, and only flip `status: resolved` on a genuine zero (note in
      advance: `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` and
      `onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` will NOT reach zero by design — each retains a
      deliberately-excluded residual item). **Done when**: every landed todo's source checkbox is flipped with a
      verified commit, and each source doc's remaining-open count is explicitly re-stated rather than assumed.

- [ ] [REVIEW] P1. **Re-check batch4's own Deferred items for cleared gates.** Walk each Deferred entry in
      `cefi_satellite_ao_dispatch_batch4_2026_07_31.md` and re-verify its specific blocking condition: (a) the PARKED
      cross-tranche `estate_orphan_assessment_2026_07_21.md` todo-6 boundedness conflict — has the operator ruled which
      tranche's verdict wins? (b) the shard24 operator-gate — has the `deployment-api` build+deploy landed (check
      `UPDATE_TIME` on the live Cloud Run monitor service against `2026-07-31T08:06:31Z`)? (c) the
      `onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` items 1-3 — has a delete-safety reversibility check
      (`gcs_bucket_soft_delete_retention_seconds()` ≥604800s, fresh same-run) been run against the live split-brain
      state, clearing items 1-2 for a future batch? For any gate that has cleared, record it as ready for a `batch5`
      extraction — **do not draft the todo here**, this finalize plan's scope is reconciliation, not fresh drafting. For
      any still open, record an explicit re-verified confirmation. **Done when**: each Deferred entry carries either a
      "gate cleared → batch5 candidate" note or a dated re-verification that it is still blocked.

- [ ] [DOC] P1. **Archive `cefi_satellite_ao_dispatch_batch4_2026_07_31.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate every remaining Deferred item to a tracked todo elsewhere (todo 2 above
      should have resolved or re-confirmed each — verify none silently vanish) → add the archive banner → run the
      codex-alignment check (batch4 creates no new durable contract; confirm still true) → grep the corpus for every
      referrer of `cefi_satellite_ao_dispatch_batch4_2026_07_31` and repoint each to the archived path → clear
      `locked_by` (already empty, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every corpus
      referrer resolves to the new path, `run_hygiene_sweep.sh` stays green, and this finalize doc is archived alongside
      it in the same commit.

## Codex SSOTs

- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual this plan's todo 3
  executes.
- `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` § 3a — the reversibility bar todo 2(c) checks for before
  any `onchain_venues_mislabeled_batch_tardis_lane` re-partition candidate can move to a future batch.
