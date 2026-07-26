---
doc_type: plan
title: CeFi satellite AO batch 3 — finalize (reconcile source docs + re-check deferrals + archive)
summary: >-
  Gated closeout for cefi_satellite_ao_dispatch_batch3_2026_07_26.md — machine-held via depends_on + gate_on_depends:
  true until all 5 of that plan's todos are done. Mirrors the batch1/batch2 finalize pattern: reconcile each source
  doc's checkboxes once its batch-3 todo lands, re-check batch3's own Deferred items (the parked cross-tranche
  blank-`data_type` conflict, the 4 prerequisite-gated items, and the too-large/risky doc) for any whose gate has since
  cleared, then archive batch3 via the standard 6-step ritual. Also carries the one `/plan-reconcile` hand-off this
  audit produced (2 provably-shipped stale checkboxes in the deribit-combo partition-move doc).
status: draft
nature: process
asset_group: [cefi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [cefi, ao-dispatch, close-out, batch-3, satellite-docs, archival]
related:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.25
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_satellite_ao_dispatch_batch3_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26 (autonomous), per task_template.md §4's finalize-plan-coverage rule — every
  AO-dispatched plan needs a companion gated finalize plan, mirroring the cefi batch1/batch2 + sports batch2-5
  precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# CeFi satellite AO batch 3 — finalize

> **Status: draft — NOT dispatched.** Flips to `active` only alongside its parent
> `cefi_satellite_ao_dispatch_batch3_2026_07_26.md`, and only on explicit operator approval.

> **Machine-gated on `cefi_satellite_ao_dispatch_batch3_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 5 tasks in that plan are `done`. `sequential: true` because todo 2
> depends on todo 1's reconciliation, and todo 4 (archival) must run last.

## Todos

- [ ] [REVIEW] P1. **Reconcile all 4 distinct source docs' checkboxes.** Batch 3's 5 todos draw from 4 source docs:
      `issues/cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md` (1 todo),
      `issues/cefi_hl_aster_batch_data_gaps_2026_06_22.md` (3 todos),
      `issues/cefi_backfill_per_day_catalogue_reload_2026_07_20.md` (1 todo), plus the edit target
      `data_completion_cefi_2026_07_15.md`. For each landed batch-3 todo, flip the corresponding checkbox/section in its
      named source doc citing the shipping commit — **verify the commit exists and is reachable on
      `origin/live-defi-rollout` before citing it**. Then, per source doc, re-check whether it now has 0 open items
      remaining in **both** checkbox AND prose form (this corpus's confirmed trap: real work expressed as prose with no
      checkbox), and only flip `status: resolved` on a genuine zero. Note in advance:
      `cefi_hl_aster_batch_data_gaps_2026_06_22.md` will NOT reach zero (it retains ~11 open items, several
      operator-gated or month-stale), and `cefi_backfill_per_day_catalogue_reload_2026_07_20.md` will NOT reach zero
      (its A/B architectural fork stays operator-gated — batch 3 only added read-only evidence for it). **Done when**:
      every landed todo's source checkbox is flipped with a verified commit, and each source doc's remaining-open count
      is explicitly re-stated rather than assumed.
- [ ] [REVIEW] P1. **Re-check batch3's own Deferred items for cleared gates.** Walk each Deferred entry in
      `cefi_satellite_ao_dispatch_batch3_2026_07_26.md` and re-verify its specific blocking condition: (a) the PARKED
      cross-tranche blank-`data_type` conflict — has the operator ruled which disposition wins (backfill per-row vs
      reclassify-as-malformed-aggregate)? (b) the `MANIFEST_ALLOW_STALE_FALLBACK` revert — has
      `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md`'s consolidator-restore todo landed? (c) the
      features-service day-scan — has the feature-definition shaping decision been ruled? (d) `create-code-tarballs.sh`
      — have the two prediction-tranche `[OPS] P2` claims on the same script shipped or been withdrawn? (e) the cefi
      zero-capture data_type gaps — re-measure against the live index before deciding (the 2026-06-24 numbers are
      month-stale). For any gate that has cleared, record it as ready for a `batch4` extraction — **do not draft the
      todo here**, this finalize plan's scope is reconciliation, not fresh drafting. For any still open, record an
      explicit re-verified confirmation; do not re-ask an operator question that is already outstanding. **Done when**:
      each Deferred entry carries either a "gate cleared → batch4 candidate" note or a dated re-verification that it is
      still blocked.
- [ ] [PM] P2. **Hand the 2 provably-shipped stale checkboxes to a reconcile pass.** This audit found (but deliberately
      did not flip) that `issues/deribit_combo_perpetual_partition_move_2026_07_21.md`'s two `P1` todos — the `[DESIGN]`
      cross-check against the DERIBIT-COMBO venue-registry purge, and the `[WRITER]` combo-shape guard-widen/port into
      `tardis_cefi_shards.py` — are recorded as already complete in
      `cefi_4surface_migration_execution_log_2026_07_24.md` item 7 ("INVESTIGATED, NO CODE NEEDED … the guard-widen
      already shipped this session, `mtds@2ddc6d4a` … `tardis_cefi_shards.py` already shares the fixed classifier").
      Verify `mtds@2ddc6d4a` is reachable on `origin/live-defi-rollout` and that `tardis_cefi_shards.py` genuinely
      routes through the shared fixed classifier (read the code, do not trust the claim); if both hold, flip the 2
      checkboxes citing that sha and the execution-log entry. If either fails to verify, record the discrepancy instead
      and leave the checkboxes open. Do NOT touch that doc's remaining 2 `[DATA] P2` todos — the 15,119-row
      partition-move `--apply` is held by an explicit 2026-07-23 operator ruling. Repo: unified-trading-pm. **Done
      when**: both checkboxes are flipped with verified evidence, or a written finding explains why verification failed.
- [ ] [DOC] P1. **Archive `cefi_satellite_ao_dispatch_batch3_2026_07_26.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate every remaining Deferred item to a tracked todo elsewhere (todo 2 above
      should have resolved or re-confirmed each — verify none silently vanish, especially the PARKED conflict) → add the
      archive banner → run the codex-alignment check (batch3 creates no new durable contract; confirm still true, and
      confirm todo 3's `deployment-observability.md` edit landed or was explicitly declined) → grep the corpus for every
      referrer of `cefi_satellite_ao_dispatch_batch3_2026_07_26` and repoint each to the archived path → clear
      `locked_by` (already empty, confirm). **Done when**: the plan is moved to `plans/archive/2026_07/`, every corpus
      referrer resolves to the new path, `run_hygiene_sweep.sh` stays green, and this finalize doc is archived alongside
      it in the same commit.

## Codex SSOTs

- `/codex/11-project-management/` — the 6-step archival ritual this plan's todo 4 executes.
- `/codex/05-infrastructure/deployment-observability.md` — verify batch3 todo 3's correct-codex edit landed (or was
  declined with a finding) during the codex-alignment step.
