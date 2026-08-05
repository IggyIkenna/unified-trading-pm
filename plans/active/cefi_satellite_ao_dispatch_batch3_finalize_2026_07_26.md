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
status: active
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
last_updated: "2026-07-30"
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
context_scope:
  [
    /plans/active/cefi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/05-infrastructure/deployment-observability.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/archive/2026_07/cefi_satellite_ao_dispatch_batch2_2026_07_26_finalize.md,
  ]
---

# CeFi satellite AO batch 3 — finalize

> **Status: draft — NOT dispatched.** Flips to `active` only alongside its parent
> `cefi_satellite_ao_dispatch_batch3_2026_07_26.md`, and only on explicit operator approval.

> **Machine-gated on `cefi_satellite_ao_dispatch_batch3_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) — the
> dispatcher will not queue any todo below until all 5 tasks in that plan are `done`. `sequential: true` because todo 2
> depends on todo 1's reconciliation, and todo 4 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile all 4 distinct source docs' checkboxes.** — unified-trading-pm@7ce17e4d5 All 5
      shipping commits verified reachable on `origin/live-defi-rollout` before citing: `unified-trading-pm@4d90eeefe` ·
      `instruments-service@2217756f` · `unified-trading-pm@66fa926d5` · `market-tick-data-service@d2366203` ·
      `market-tick-data-service@fc64e092`. **Source-doc reconciliation:** -
      `cefi_e6_cf7_relabel_and_attempted_failed_remeasure_2026_07_26.md`: both checkboxes flipped with verified commits,
      `status→resolved` (0 open — genuine zero in both checkbox and prose form). -
      `cefi_hl_aster_batch_data_gaps_2026_06_22.md`: 3 batch3 checkboxes already flipped; line 854 now cites both
      `d2366203`+`fc64e092`. ~15 open checkboxes remain — does NOT reach zero. -
      `cefi_backfill_per_day_catalogue_reload_2026_07_20.md`: profile findings appended (batch3 todo 5 deliverable);
      `[BACKEND] P2` stays open (operator-gated). 1 open — does NOT reach zero. - `data_completion_cefi_2026_07_15.md`:
      E6 CF-7 edit verified landed (corrected 11.61% figure + COINBASE=0 + link). Many open checkboxes remain — does NOT
      reach zero.
- [x] ✅ [REVIEW] P1. **Re-check batch3's own Deferred items for cleared gates.** — unified-trading-pm@3e70f3f83 Walked
      all 6 Deferred entries in `cefi_satellite_ao_dispatch_batch3_2026_07_26.md` (2026-08-05, slot-7): **(a) 🟢 Gate
      cleared — blank-`data_type` conflict**: resolved 2026-07-28, executed as batch3 todo 6
      (`unified-trading-pm@a3922f9c9`), 0 blank-`data_type` rows, bare-OKX×7 reclassified. Already resolved within
      batch3 itself — nothing left to extract. **(b) 🟢 Gate cleared → batch4 candidate —
      `MANIFEST_ALLOW_STALE_FALLBACK` revert**: batch1b consolidator-restore `[INFRA] P1` ✅ DONE (2026-07-26), all 6
      consolidator crons healthy, cefi launcher no longer carries the flag (verified absent on disk 2026-08-05). The
      revert is effectively done; a batch4 todo can remove the flag from the GCS-uploaded `setup-data-pipeline-vm.sh` if
      still present. **(c) 🔴 Still blocked — features-service day-scan**: both `[BACKEND] P1` (schema-gap) and
      `[BACKEND] P2` (day-scan) remain OPEN in `cefi_residual_followups_after_honest_done_2026_07_17.md`. No
      feature-definition shaping decision ruled since 2026-07-17. **(d) 🔴 Still blocked — `create-code-tarballs.sh`**:
      both prediction-tranche `[OPS] P2` claims (`prediction_cross_venue_arb_and_coverage_2026_07_24.md:172` +
      `prediction_consolidated_closeout_2026_07_18.md:449`) remain OPEN — neither shipped nor withdrawn. **(e) 🔴 Still
      blocked — zero-capture `data_type` gaps**: 2026-06-24 numbers now 6 weeks stale; `perp_funding`/`ohlcv_1m` counts
      never re-measured against the live index. **(f) 🔴 Still too-large/risky — chain-drop doc**: `status: open`, 1
      open todo, migration still actively draining; batch1 exclusion rationale holds unchanged. **Summary**: 2 of 6
      gates cleared (a, b), 4 still blocked (c, d, e, f). Each Deferred entry now carries a dated re-verification note
      (2026-08-05) directly in the batch3 plan.
- [x] ✅ [PM] P2. **Hand the 2 provably-shipped stale checkboxes to a reconcile pass.** — unified-trading-pm@<sha>
      Verified 2026-08-05 (slot-11): (1) `mtds@2ddc6d4a` IS reachable on `origin/live-defi-rollout`
      (`git merge-base --is-ancestor` confirmed). (2) `tardis_cefi_shards.py:310,611` calls the shared
      `self._classify_row_instrument_type(s, venue)` — the exact method `2ddc6d4a` fixed by hoisting
      `is_deribit_combo_symbol_shape` above the venue-label branch for bare `DERIBIT`. Both ingestion paths confirmed
      covered (no duplicate classifier to port). (3) `cefi_4surface_migration_execution_log_2026_07_24.md` item 7
      independently records this as "INVESTIGATED, NO CODE NEEDED." The two P1 checkboxes in
      `issues/deribit_combo_perpetual_partition_move_2026_07_21.md` §9 (`[DESIGN] P1` + `[WRITER] P1`) are already `[x]`
      with full evidence — no flip needed, both already cite `mtds@2ddc6d4a` and the execution-log entry. The remaining
      2 `[DATA] P2` todos were NOT touched (15,119-row `--apply` still operator-gated per §7).
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

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-03**: re-verified context_scope (6 entries) unchanged — `_finalize` gate doc, no source-code
  paths added per the skip-source carve-out; all 6 entries confirmed resolving on disk.
