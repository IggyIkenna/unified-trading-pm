---
doc_type: plan
title: TradFi satellite AO batch 3 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch3_2026_07_26.md — machine-held via depends_on + gate_on_depends:
  true until all 9 of that plan's todos are done. Mirrors batch1/batch2-finalize's pattern (reconcile each distinct
  source doc's checkboxes independently once its batch-3 todo lands, then re-check the Deferred conflict-gated/
  operator-gated/too-large-or-risky items for any that have since cleared — including re-checking whether the operator
  has ruled on `tradfi_mvp_mode_unreachable_dead_gate_2026_07_08`'s DECISION per batch2_finalize's own live tracking),
  then archives batch3 via the standard 6-step ritual.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-3, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch2_finalize_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.3
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_satellite_ao_dispatch_batch3_2026_07_26]
gate_on_depends: true
source: >-
  /ag-closeout-audit skill run 2026-07-26, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched
  plan needs a companion gated finalize plan, mirroring the tradfi batch1/batch2 + cefi batch2 + defi batch2 + sports
  batch2-5 precedent.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# TradFi satellite AO batch 3 — finalize

> **Machine-gated on `tradfi_satellite_ao_dispatch_batch3_2026_07_26.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 9 tasks in that plan are `done`. `sequential: true` because
> todo 2 (deferred re-check) needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-07-26 (slot-5).** **Reconcile all 9 distinct source docs' checkboxes.** For each of
      `tradfi_satellite_ao_dispatch_batch3_2026_07_26.md`'s now-done todos: flip the corresponding checkbox/section in
      its named source doc (each todo's text ends with "Source: `<doc>.md`"), citing the batch-3 commit(s) that shipped
      it — verify the actual shipped commit exists before citing it. For each source doc: after flipping, re-check
      whether it now has 0 open todos remaining (checkbox AND prose-form — do not trust checkbox count alone). Only flip
      a doc's `status` to `resolved` if it genuinely reaches 0 open todos. **Done when**: all 9 source-doc
      checkboxes/sections are flipped with verified evidence, and any doc that genuinely reaches 0 open todos is flipped
      to `status: resolved`. — **All 9 reconciled, each commit verified live in its repo before citing**: (1)
      `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` — already flipped by the original worker
      (verified accurate, no action needed). (2) `data_completion_tradfi_2026_07_15.md` — R1/R2 already correctly
      reconciled (R1 open pending operator per the data-loss finding, R2 done). (3)
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` — G1.g/massive.py/tombstone already flipped; flipped the
      4th (by_date capture-freeze) bullet as PARTIAL (diagnosis + staleness-check ask done, underlying freeze itself
      still open, tracked via the sibling ICE/CME bullets). (4)
      `issues/cme_combo_underlying_extraction_garbage_2026_07_19.md` — all 3 Remediation items already struck
      through/done (verified); doc is `locked_by`, left status/lock as-is per its own note. (5)
      `issues/databento_default_executor_dns_starvation_risk_2026_07_17.md` — all 3 todos done; flipped
      `status: resolved` (was left open pending a CEFI aster/hyperliquid follow-up that belongs to a different
      asset_group — extracted to a new `issues/cefi_threaded_resolver_dns_starvation_risk_2026_07_26.md` so it stays
      tracked instead of blocking this doc's own closure). (6)
      `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md` — already correctly reconciled via its
      Progress Log + Deferred-work table (3 genuinely open items, stays open). (7)
      `issues/tradfi_manifest_rebuild_deletion_resurrection_gap_2026_07_20.md` — flipped the manifest-vs-disk
      consistency checkbox (`mtds@ee3d636`, verified); doc reached 0 open todos → flipped `status: resolved`. (8)
      `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md` — flipped the known-dead-cells checkbox
      (`deployment-service@01414fc`, verified); 2 unrelated todos remain open, stays `status: open`. (9)
      `issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` — flipped the VERIFY
      classification-trace checkbox (read-only trace, no commit); 1 unrelated todo remains open, stays `status: open`.
- [x] ✅ [REVIEW] P1. **DONE 2026-07-26 (slot-5).** **Re-check the 1 conflict-gated + 2 operator-gated + 1
      too-large-or-risky Deferred items from batch3's own doc**, now that time has passed. For
      `tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` specifically, check
      `autonomous_session_operator_decisions_2026_07_25.md` (or its successor) for a landed operator ruling on the
      `mvp_mode` wire-in-vs-delete DECISION — `tradfi_satellite_ao_dispatch_batch2_finalize_2026_07_25.md` already owns
      a parallel re-check for the same doc, so cross-reference rather than duplicating that check. For the other 3
      Deferred items: re-read the specific gating ground to check if it has since cleared — if so, extract it as a new
      tracked todo in a follow-up `batch4` (do not draft it directly here); if still genuinely unresolved, leave it
      explicitly deferred, do not re-surface an already-asked operator question a second time. **Done when**: each of
      the 4 Deferred items has either (a) a note that it's ready for `batch4` extraction because its gate cleared, or
      (b) an explicit re-verified confirmation the gate is still open. — **All 4 re-verified STILL GENUINELY OPEN, none
      cleared, none batch4-eligible** (notes added directly in `tradfi_satellite_ao_dispatch_batch3_2026_07_26.md`'s own
      Deferred sections with today's date): (1) conflict-gated
      FX-yahoo-backfill-vs-`tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md` — conflict doc still
      `status: open`, its own Deferred-work table still lists the historical FX re-stamp as "ready to pick up" but not
      done; the conflict is unchanged. (2) `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` — still
      `status: open`; grepped the corpus for an `EXCHANGE_CODE_TO_NAME` SSOT-contradiction ruling, zero hits; not
      re-asked. (3) `tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` — cross-referenced (not duplicated) against
      `tradfi_satellite_ao_dispatch_batch2_finalize_2026_07_25.md`, which is still `status: draft` (undispatched, so it
      hasn't and couldn't have re-checked this either); grepped `autonomous_session_operator_decisions_2026_07_25.md`
      for `mvp_mode` — zero matches, no ruling landed; not re-asked. (4)
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` — still `status: active` +
      `locked_by: live-defi-rollout`; the 2026-07-26 archived re-diagnosis's own finding stands (no successful tradfi
      features run has landed) — still genuinely too-large-or-risky.
- [ ] [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch3_2026_07_26.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved or re-confirmed all 4 — verify none silently vanish) → add the archive banner → run
      the codex-alignment check (no new durable contract from this batch, confirm still true) → grep the corpus for
      every referrer of `tradfi_satellite_ao_dispatch_batch3_2026_07_26` and fix each path to point at the archived
      location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself gets
      archived alongside it in the same commit.
