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
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch3_finalize_2026_07_26.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-31"
last_updated: "2026-08-07"
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
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch4_2026_07_31.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
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

- [x] ✅ [REVIEW] P1. **Reconcile all 7 distinct source docs' checkboxes.** Batch 4's 7 todos draw from 7 source docs:
      `issues/bybit_futures_chain_write_shape_2026_07_13.md`,
      `/plans/archive/2026_08/cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30.md`,
      `issues/cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md`,
      `issues/cefi_content_migration_shard13_network_error_and_checkpoint_resume_bug_2026_07_31.md`,
      `/plans/archive/issues/cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md`,
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

- [x] ✅ [REVIEW] P1. **Re-check batch4's own Deferred items for cleared gates.** Walk each Deferred entry in
      `cefi_satellite_ao_dispatch_batch4_2026_07_31.md` and re-verify its specific blocking condition: (a) the PARKED
      cross-tranche `estate_orphan_assessment_2026_07_21.md` todo-6 boundedness conflict — has the operator ruled which
      tranche's verdict wins? (b) the shard24 operator-gate — has the `deployment-api` build+deploy landed (check
      `UPDATE_TIME` on the live Cloud Run monitor service against `2026-07-31T08:06:31Z`)? (c) the
      `onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` items 1-3 — has a delete-safety reversibility check
      (`gcs_bucket_soft_delete_retention_seconds()` ≥604800s, fresh same-run) been run against the live split-brain
      state, clearing items 1-2 for a future batch? For any gate that has cleared, record it as ready for a `batch5`
      extraction — **do not draft the todo here**, this finalize plan's scope is reconciliation, not fresh drafting. For
      any still open, record an explicit re-verified confirmation. **Done when**: each Deferred entry carries either a
      "gate cleared → batch5 candidate" note or a dated re-verification that it is still blocked. — **DONE 2026-08-07
      (slot-2, `worker`, `cefi_satellite_ao_dispatch_batch4_2026_07_31_finalize-002`)**: (a) `estate_orphan_assessment`
      todo 6: still BLOCKED — 2-1 KEEP-NA tally reaffirmed, no operator ruling. (b) shard24: FULLY CLEARED — image
      UPDATE_TIME=2026-08-07T09:32:43 + test `test_sweep_early_preemption_no_marker_falls_back_to_op_checker` confirmed
      passing (QG sentinel `6b4be78` on origin/live-defi-rollout is ancestor-newer than `09a2374`); shard 24 relaunch →
      batch5 candidate. (c) onchain_venues items 1-2: delete-safety CLEARED —
      `gcs_bucket_soft_delete_retention_seconds('market-data-tick-cefi-prd-central-element-323112')` = 604800s (fresh
      same-run 2026-08-07) → batch5 candidates. Item 3 (PACIFICA-SOLANA): unchanged, human/NA.

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

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-verified context_scope (4 entries) unchanged — `_finalize` gate doc, no source-code
  paths added per the skip-source carve-out; all 4 entries confirmed resolving on disk.
- **2026-08-07 (slot-2, `worker`, `cefi_satellite_ao_dispatch_batch4_2026_07_31_finalize-002`)**: Todo 2 DONE — all 3
  Deferred gates re-verified. (a) estate_orphan_assessment todo 6: still blocked (no operator ruling, 2-1 KEEP-NA). (b)
  shard24 gate: fully cleared (image 2026-08-07T09:32:43, test confirmed); shard 24 relaunch → batch5. (c)
  onchain_venues items 1-2: delete-safety cleared (bucket retention 604800s fresh); items 1-2 → batch5. Item 3
  (PACIFICA-SOLANA) unchanged/human-NA. All notes recorded in batch4 Deferred sections.
- **2026-08-07 (slot-9, `backend_engineer`, `cefi_satellite_ao_dispatch_batch4_2026_07_31_finalize-001`)**: Todo 1 DONE
  — all 7 source docs verified and reconciled. All 8 batch4-cited commits verified reachable on
  `origin/live-defi-rollout` (`market-tick-data-service@1a32b6e7`, `unified-trading-library@89eabac2`,
  `deployment-service@4ee514e`, `unified-trading-library@f135d4fd8`, `unified-trading-pm@aa30fcaf2`,
  `market-tick-data-service@878b750b`, `deployment-service@cca27b3`, `unified-trading-library@a4779c8b`). Per-doc
  remaining-open count (explicitly restated, not assumed): (1) `bybit_futures_chain_write_shape_2026_07_13.md` — 0
  batch4-related open; `locked_by: live-defi-rollout` + operator-gated 490-duplicate cleanup stays open outside scope.
  (2) `cefi_consolidated_vm_aster_data_landing_recheck_2026_07_30.md` — 0; `status: resolved` + archived. (3)
  `cefi_content_apply_memory_freeze_recurs_post_fix_and_registry_false_reap_2026_07_31.md` — 3 open P3 corroborating
  items (not batch4 scope; feeding the separate shard-16 investigation). (4)
  `cefi_content_migration_shard13_network_error_and_checkpoint_resume_bug_2026_07_31.md` — 0; `status: resolved` +
  archived. (5) `cefi_legacy_bucket_deleted_before_l3_gate_2026_07_28.md` — 0; `status: resolved` + archived. (6)
  `mtds_backfill_vm_memory_hang_large_chunk_2026_07_22.md` — 1 open: sports-scoped P1 BLOCKED-CREDENTIALS (deliberately
  excluded per batch4's scope, consistent with plan's "leave the sports-scoped item open" instruction). (7)
  `onchain_venues_mislabeled_batch_tardis_lane_2026_07_20.md` — 3 open: items 1-3 (re-partitions from the
  too-large-or-risky Deferred section, each retaining their explicitly-excluded residual per batch4). Docs 4 and 5
  already zero open; docs 2, 6, 7 retain only deliberately-excluded residuals — none were silently overlooked.
