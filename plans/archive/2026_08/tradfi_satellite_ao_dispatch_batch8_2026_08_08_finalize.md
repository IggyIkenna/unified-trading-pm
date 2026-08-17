---
doc_type: plan
title: TradFi satellite AO batch 8 — finalize (reconcile source docs + resolve deferrals + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch8_2026_08_08.md — machine-held via depends_on plus
  gate_on_depends: true until all 3 of that plan's todos are done. Mirrors the batch1-7-finalize pattern: reconcile each
  distinct source doc's checkboxes once its batch-8 todo lands, then re-check batch8's own Deferred sections
  (too-large-or-risky / operator-gated / conflict-gated / already-in-flight / already-drafted-elsewhere / time-gated /
  cross-tranche-flagged) for any that have since cleared, then archive batch8 via the standard 6-step ritual. Ships
  `status: active` from the start (not draft) — per the 2026-07-30 ruling this skill's SKILL.md documents, a finalize
  plan carries no independent judgment call and gate_on_depends already machine-holds every task until batch8 itself is
  done, so stacking batch8's own draft safety-rail on top of the finalize would be a redundant second gate.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-8, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md,
    /plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch7_2026_08_06_finalize.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [tradfi_satellite_ao_dispatch_batch8_2026_08_08]
gate_on_depends: true
source: >-
  /ag-closeout-audit tradfi run 2026-08-08 (autonomous mode, sharded daily `ag_closeout_auditor` worker, dispatch
  agt-ea6423, slot 6), per task_template.md section 4's finalize-plan-coverage rule — every AO-dispatched plan needs a
  companion gated finalize plan, mirroring the tradfi batch1-7 precedent.
assigned_role: data_engineering
effort: max
sequential: true
drift_direction: advance-code
context_scope:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
---

# TradFi satellite AO batch 8 — finalize

> **Machine-gated on `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md`** (`depends_on` plus `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 3 tasks in that plan are `done`. `sequential: true` because
> todo 2 (deferred re-check) needs todo 1's reconciliation done first, and todo 3 (archival) must run last. Batch8
> itself stays `status: draft` until the operator reviews and approves it — this finalize plan needs no separate flip
> either way (see summary).

## Todos

- [x] ✅ [REVIEW] P1. **Reconcile all 3 distinct source docs.** **DONE 2026-08-16 (slot 5, review) — all 3 already
      reconciled by the workers who shipped each batch8 todo (each cited "same commit"/"same session" inline in
      batch8's own now-done todo text); this pass independently VERIFIED each, not re-did the reconciliation:**
      1. `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` (`plans/active/`, `locked_by` empty) —
         checkbox already flipped citing "DONE 2026-08-09 (slot-9, data_engineering) via
         `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md` todo 1" (a data-only GCS `--apply`, no code commit to
         verify). Correctly does NOT reach 0 open items — a standing P3 `- [ ]` reconciliation todo (re-run after
         every future catalogue roll-up cycle) is explicitly perpetual/recurring, not a one-shot closeable item.
         `status` correctly stays `active` — not flipped, per this todo's own instruction not to close a doc that
         doesn't genuinely reach 0 open items.
      2. `mdps_tradfi_ohlcv_15m_24h_conversion_still_zero_2026_07_27.md` — already archived
         (`plans/archive/2026_08/issues/`), `status: resolved`, `resolved_by: slot-9, 2026-08-16`, archive banner
         present. Cited commit `market-data-processing-service@2b2cc58e` verified as an ancestor of
         `origin/live-defi-rollout` this session.
      3. `features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md` — already archived
         (`plans/archive/issues/`), `status: resolved`, `resolved_by: features-service@4caac95e38 (live-VM
         confirmed 2026-08-16, slot-32, features-e2e-tradfi-20260816-030150-1efb38)`. **This finalize todo's own
         caution above (written 2026-08-08) is now STALE, not a live concern**: by 2026-08-16 the previously
         time-gated item-2 force+skip proof itself cleared (upstream MDPS candle backfill arrived + 2 further
         root-caused bugs were fixed same-day — chain-bundle instrument-id blob-listing fallback + candle-blob-path
         gating), so the doc genuinely reached 0 open items and archived correctly, not prematurely. Cited commits
         `features-service@6d2ad5dc89` and `@4caac95e38` both verified as ancestors of `origin/live-defi-rollout`
         this session (`git merge-base --is-ancestor`, all 3 repos, all 5 cited SHAs across the 3 docs confirmed
         present on origin). All 3 docs' `locked_by` confirmed empty (none touched a locked doc). **Done when**: met
         — all 3 source docs reconciled with verified evidence; doc 1 correctly NOT flipped to resolved (genuine open
         standing todo), docs 2+3 correctly already resolved+archived.

- [x] ✅ [REVIEW] P1. **Re-check batch8's own Deferred/Flagged sections now that time has passed. DONE 2026-08-16
      (slot 5, review) — all 11 items re-checked with fresh evidence; full accounting below.**

      **Cleared (extracted or ready)**:
      1. **Conflict-gated item — CLEARED, EXTRACTED.** `governance_sweep_deferred_followups_2026_08_06.md`'s duplicate
         `[DIAG] P2` CME `instrument_id`-format todo is `[x]` DONE (verified 2026-08-14). The blocked fix itself
         (`tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md` todo 1) also independently shipped and
         verified 2026-08-16 (`features-service@a46681c84a`). Extracted the now-unblocked todo 2 (relaunch the
         TRADFI:volatility benchmark) into a new `tradfi_satellite_ao_dispatch_batch9_2026_08_16.md` (`status: draft`,
         pending operator review, mirrors the batch1-8 pattern exactly) + its companion
         `tradfi_satellite_ao_dispatch_batch9_2026_08_16_finalize.md`.
      2. **Already-in-flight item — CLEARED, but ALREADY EXTRACTED by another session same-day, not duplicated here.**
         `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` todo 3 (the twin-coverage root-cause investigation) is
         `[x]` DONE — found the 0%-coverage measurement was itself a `canonical_twin_path()` lookup-logic bug, not a
         real registration gap. This clears `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` for a
         delete-todo draft, exactly as this todo's own text anticipated — but a **2026-08-16 na-eligibility-audit
         follow-up pass already did exactly this extraction** (same day, before this dispatch), into a dedicated
         `tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md` (`assigned_vm: planning`, confirmed
         present on disk). Not re-extracting — would duplicate an already-tracked dispatch.
      3. **Time-gated item — CLEARED via natural resolution, nothing to extract.**
         `features_require_captured_misses_tradfi_processed_candles_gap_2026_07_27.md`'s item 2 (force+skip proof) —
         already confirmed fully resolved + archived as part of this finalize plan's own todo 1 (see above): by
         2026-08-16 the upstream MDPS candle backfill arrived and 2 further root-caused bugs were fixed same-day,
         clearing the force+skip proof for real. No remaining work to extract.
      4. **Operator-gated item — stale tag partially corrected, no new extraction warranted.**
         `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` — the SPECIFIC gating ground batch8 named ("which
         `EXCHANGE_CODE_TO_NAME` registry is authoritative") is now RESOLVED (operator ruled + shipped 2026-08-07,
         `unified-api-contracts@00b2de546`). The doc itself still carries other, separately-tracked open items
         (its own `[DATA]`/`[OPERATOR-DECISION]` todos, `assigned_vm: NA`) that batch8 never drafted content from —
         those are the doc's own natural lifecycle, not batch8/9 material. Corrected the stale framing here; no new
         batch9 todo drawn from this doc.
      5. **Operator-gated item — gate cleared (operator ruled 2026-08-07), READY but deliberately NOT extracted this
         pass — multi-file blast radius, recommend its own dedicated follow-up.**
         `tradfi_autonomous_session_operator_decisions_2026_07_25.md` items 5/7/8 are all "RULED 2026-08-07 ...
         Propagation not yet executed — ready to execute": (5) flip 8 draft tradfi AO plans' `status` to `active`
         (Option A, operator's literal unqualified instruction — the exact 8 plans need re-deriving, not listed
         inline in this doc); (7) add a safe-idempotent justification citation to a specific file:line; (8) fold a
         doc's remnant into an archive target + re-home its `check_ag_closeout_linkage.py` linkage anchor. Each is
         genuinely ready per the operator's ruling, but drafting all 3 correctly (esp. item 5's exact plan list and
         item 8's linkage re-homing) needs its own dedicated investigation pass, not a same-turn bundle into batch9
         alongside an unrelated data-pipeline item — flagging as ready-for-extraction (done-when option (a)) rather
         than risking an under-scoped draft.

      **Still genuinely open (re-verified, evidence cited)**:
      6. `tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md` — `status:` still `draft`, not promoted.
         Unchanged; not re-asking.
      7. `tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md` — still `assigned_vm: NA`; todo 1's own
         text confirms it stays a duplicate of `tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`'s already-`[x]`
         combined extraction todo (the actual dispatch vehicle) — disposition unchanged from batch8's own citation.
      8. **Too-large-or-risky (4 docs) — all still `status: active`/`open`, unchanged**: `data_completion_tradfi_2026_07_15.md`,
         `issues/tradfi_canonical_path_migration_design_2026_07_19.md`,
         `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s CME re-fetch,
         `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`. No evidence any has shrunk to batch-todo scope.
      9. **Cross-tranche-flagged (4 docs)** — all 4 still `status: open`, large, actively churning on OTHER
         (non-TradFi) items; no evidence the specific TradFi-relevant sub-items batch8 cited
         (`mtds_is_full_adapter_smoketest_findings_2026_07_07.md`'s 4 TradFi bugs;
         `instruments_docs_audit_outstanding_items_2026_07_08.md` §H's 4 items, TRADFI still explicitly excluded from
         that doc's own scope per its line 94 note; `uac_per_venue_seed_fallback_removal_deferred_2026_07_26.md`'s
         wiring todo, unchanged, still `cefi_master`; `honest_coverage_shard_dimension_model_definitional_data_2026_07_07.md`'s
         CME manifest-backfill todo, unchanged, still `instruments_master`) have been acted on by their owning
         tranches. Re-affirmed still open, not adopted into tradfi.

      **Done when**: met — every item has either (a) a note it's ready/extracted with its gate-clearing evidence, or
      (b) an explicit re-verified confirmation it's still open, with evidence cited (all 11 above).

- [x] ✅ [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md`. DONE 2026-08-17 (slot 32,
      data_engineering).** All 3 todos verified `[x]` with shipped evidence (direct read of todo 1/2's Progress Log
      entries above); Deferred/Flagged items re-checked by todo 2, none silently vanish (all still explicitly
      deferred/extracted with current-as-of-2026-08-16 evidence). No new durable codex contract from this plan — no
      codex drift; `/codex/11-project-management/` + `plans/PLAN_FORMAT.md` remain the correct, unchanged SSOTs.
      `locked_by` empty on both docs. Archived alongside this finalize doc in the same commit; every corpus PATH
      referrer repointed to `/plans/archive/2026_08/tradfi_satellite_ao_dispatch_batch8_2026_08_08(_finalize).md` in
      `related:`/`context_scope` frontmatter across `tradfi_databento_account_billing_suspended_2026_08_09.md`,
      `tradfi_satellite_ao_dispatch_batch9_2026_08_09.md`, `tradfi_satellite_ao_dispatch_batch9_2026_08_16.md`,
      `tradfi_satellite_ao_dispatch_batch9_2026_08_16_finalize.md`, `tradfi_consolidated_closeout_2026_07_18.md`, and
      `plans/epics/tradfi_master.md`'s `../active/` links; bare-filename prose citations in Progress Logs and the two
      `plan_reconciler_findings_*_2026_08_16.md` audit-report docs left untouched (historical narrative, not
      navigational paths — nothing there 404s). `plans/active/INDEX.md` regenerated
      (`scripts/plans/regenerate_active_plan_index.py`) to drop both now-archived entries. **Done when met**: the
      plan moved to `plans/archive/2026_08/`, every corpus PATH referrer resolves to the new path, this finalize doc
      archived alongside it in the same commit.

## Progress Log

- **2026-08-08 (ag_closeout_auditor, slot 6)**: created alongside batch8, same run.
- **context-scout 2026-08-09**: populated/refreshed context_scope (4 entries).
- **2026-08-16 (slot 5, review)**: todo 1 (reconcile all 3 source docs) DONE — verified, not re-done; all 3 source docs
  were already reconciled by the workers who shipped batch8's 3 todos. Independently confirmed all 5 cited commit SHAs
  across `unified-api-contracts`, `market-data-processing-service`, and `features-service` are real ancestors of
  `origin/live-defi-rollout`. Doc 1 (`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`) correctly stays
  `active` (genuine open standing P3 todo). Docs 2+3 correctly already `resolved`+archived. See todo 1's own entry for
  full detail, incl. why this todo's original 2026-08-08 caution about doc 3 not reaching 0 open items is now stale
  (its time-gate cleared 2026-08-16). Next: todo 2 (re-check Deferred/Flagged sections) is next in this sequential
  plan.
- **2026-08-16 (slot 5, review)**: todo 2 (re-check Deferred/Flagged sections) DONE — all 11 items re-checked with
  fresh evidence. 1 item extracted into a new `tradfi_satellite_ao_dispatch_batch9_2026_08_16.md` (+ finalize
  companion), `status: draft` pending operator review. 1 item's clearing was already independently extracted by
  another session same-day (`tradfi_purge_extension_and_twin_delete_fix_ao_dispatch_2026_08_16.md`) — not duplicated.
  1 item cleared via natural resolution (already covered by todo 1). 1 item's stale gating-ground framing corrected
  (no new extraction warranted — doc's other items are its own separate lifecycle). 1 item's gate cleared but
  deliberately not extracted this pass (multi-file blast radius, flagged for a dedicated follow-up). Remaining 6 items
  re-verified still genuinely open/unchanged, evidence cited. See todo 2's own entry for the full per-item accounting.
  Next: todo 3 (archive batch8) is next in this sequential plan.
- **2026-08-17 (slot 32, data_engineering)**: todo 3 (archive batch8) DONE — final todo in this sequential plan.
  Verified both prerequisite todos still hold (direct re-read, no new drift since 2026-08-16). Added the ARCHIVED
  banner to `tradfi_satellite_ao_dispatch_batch8_2026_08_08.md`, `git mv`'d both it and this finalize doc to
  `plans/archive/2026_08/` in the same commit as this checkbox flip (single-repo mode-1 sanctioned shape per
  `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`), repointed every corpus PATH referrer
  (6 active docs' `related:`/`context_scope` frontmatter + the epic's `../active/` links), and regenerated
  `plans/active/INDEX.md`. See the todo's own checkbox text for the full accounting.

## Codex SSOTs

No new durable contract is created by this plan. `/codex/11-project-management/` carries the archival ritual;
`plans/PLAN_FORMAT.md` carries the `status: draft` and `gate_on_depends` semantics this plan relies on.
