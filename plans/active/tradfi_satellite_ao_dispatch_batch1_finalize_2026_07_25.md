---
doc_type: plan
title: TradFi satellite AO batch 1 — finalize (reconcile source docs + resolve conflict-gated deferrals + archive)
summary: >-
  Gated closeout for tradfi_satellite_ao_dispatch_batch1_2026_07_25.md — machine-held via depends_on + gate_on_depends:
  true until all 5 of that plan's todos are done. Mirrors the sports batch2_finalize/ batch3_finalize pattern (reconcile
  each of the 4 distinct source docs' checkboxes independently), plus one batch1-specific addition: re-check the 38
  conflict-gated Deferred items once the operator has ruled on the queued decision in
  autonomous_session_operator_decisions_2026_07_25.md.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-1, satellite-docs, archival]
related:
  [
    /plans/active/tradfi_satellite_ao_dispatch_batch1_2026_07_25.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-30"
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
depends_on: [tradfi_satellite_ao_dispatch_batch1_2026_07_25]
gate_on_depends: true
source: >-
  /autonomous session 2026-07-25, per task_template.md §4's finalize-plan-coverage rule — every AO-dispatched plan needs
  a companion gated finalize plan.
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# TradFi satellite AO batch 1 — finalize

> **Machine-gated on `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue any todo below until all 5 tasks in that plan are `done`. `sequential: true` because
> todo 2 needs todo 1's reconciliation done first, and todo 3 (archival) must run last.

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 — Reconciled all 4 distinct source docs' checkboxes.** Per-doc verdict (each
      commit verified reachable via `git cat-file -e` before citing): -
      `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (todo 1, the `EXCHANGE_CODE_TO_NAME` diff) —
      **already reconciled**, no edit needed: `unified-trading-pm@67c4cab32` ("exhaustive EXCHANGE_CODE_TO_NAME diff —
      flip tradfi_satellite_ao_dispatch_batch1-001") already appended the full diff table into this doc on 2026-07-26.
      Doc keeps `status: open` — its sole checkbox (a P1-OPERATOR-DECISION re: CBOE/VX) is a genuinely different,
      still-open item. - `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` (todo 2, the combined
      cefi/sports-claim-verify + dry-run) — **already reconciled**, no edit needed: both applicable checkboxes already
      read `[x]` (flipped 2026-07-25 and 2026-07-30 respectively, both citing their evidence in-doc). Doc keeps
      `status: active` — its remaining DELETE checkbox is genuinely open (gated on a fresh Part-5 twin-coverage +
      retention check, which the doc's own 2026-07-30 dry-run measured at 0%, not the required 100%). -
      `tradfi_phase_d_terminal_gate_2026_07_24.md` (todos 3 + 4, the CBOE terminal-state DIAG + the VM-preemption
      launcher-naming DOC addition) — todo 3's section ("2026-07-27 — CBOE terminal-state re-check") was **already
      present verbatim**, no edit needed. Todo 4's backtick-wrapped VM-fleet-preemption note was **flipped to a real
      `[x]`** this pass, citing `unified-trading-pm@3ebdd1a4e` (doc-scoping addition) + `deployment-service@db5d3c7`
      (the launcher code fix, already cited in-doc). Doc keeps `status: active` — 2 genuinely open, operator-gated P0/P1
      checkboxes remain (MVP backfill readiness gate; post-backfill reconciliation checkpoint). -
      `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` (todo 5, the Deribit 1-4 leg cap extension) —
      its one remaining `[ ]` checkbox was **flipped to `[x]`** this pass, citing `instruments-service@9416be7d`. Doc
      keeps `status: active` despite reaching 0 open checkboxes — genuine prose-form remaining work survives in the
      "Scope migration mechanics" item (historical catalog `--apply` rewrite deferred pending operator confirmation,
      non-durable against the self-refreshing `prod/catalog.parquet` roll-up until
      `tradfi_canonical_path_migration_design_2026_07_19.md`'s upstream migration lands). **No doc genuinely reached 0
      open todos (checkbox AND prose-form)**, so no `status: resolved` flips were made — each doc's remaining open item
      (or prose-form caveat) is real and independently verified, not an oversight.
- [x] ✅ [REVIEW] P1. **DONE 2026-07-30 (slot 5) — Resolved the 38 conflict-gated Deferred items from batch1's own
      Deferred section.** Correction to this todo's own premise first: neither
      `autonomous_session_operator_decisions_2026_07_25.md` NOR the tradfi-specific
      `issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md` (the actually-relevant doc — read in full, all
      10 tradfi items) carries an operator ruling on this specific 38-item Deferred set; both docs' own "Open todo"
      sections still read "once you've answered items 1-3/5-9" — nothing has been answered. So the re-check below is a
      **fresh evidence-shipped re-verification**, not a ruling-driven one, exactly as the todo's own fallback clause
      ("check if it has since shipped") anticipates.

      **Provenance first**: batch1's own Deferred section already documents that a 2026-07-25 re-check (same-day
          follow-up) cleared 20 of the original 38 candidates into `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`
          (now `status: active`, dispatched), leaving 8 genuinely conflict-gated across 5 docs in batch2's own Deferred
          section, plus the always-excluded `tradfi_manifest_content_recovery_completion_2026_07_24.md`. Independently
          spot-verified today that the other 9 original items (across `issues/cme_combo_underlying_extraction_garbage_2026_07_19.md`,
          `archive/issues/databento_default_executor_dns_starvation_risk_2026_07_17.md` (resolved+archived),
          `issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md` (resolved+archived)) are genuinely accounted
          for via batch2's active dispatch — not silently dropped. This todo's real remaining job was to fresh-re-check the
          8-item/5-doc residual + the excluded doc against TODAY's corpus state (5 days and 3 more batches — batch3
          archived, batch4 archived, batch5 active — have landed since 2026-07-25).

          **Per-doc re-check (2026-07-30, live-verified against current HEAD)**:
          1. `data_completion_tradfi_2026_07_15.md` — **still genuinely conflict-gated.** Both competing closeout claims
             (Phase C "Denominator/catalogue-completeness" todo, line 232; the BLOCKED-INFRA P0 "Certify tradfi Layer-1"
             gate, line 302) live in `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`, confirmed still `[ ]` open
             AND that whole doc is still `status: draft` (undispatched) — the competing claim has not shipped. Left
             deferred.
          2. `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` (the ES CME futures ohlcv + ES_OPT lock candidates) —
             **still genuinely conflict-gated.** The competing claim (re-verify every MVP cell via a fresh
             `data-pipeline-check-is`/`-mtds` run) is now tracked in `tradfi_consolidated_native_ao_extract_2026_07_25.md`
             (status: active, dispatched) but its own todo (line 104) is confirmed still `[ ]` open — unshipped. Left
             deferred.
          3. `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md` (purge/reclassify 1,242 dead CBOE `ohlcv_15m`
             rows) — **still genuinely conflict-gated**, same Phase C denominator todo as item 1, confirmed still open.
             Left deferred.
          4. `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md` — **conflict CLEARED, already covered
             (no new todo needed).** The competing closeout claim is now `[x]` in
             `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md` (line 160): the ICE/KRX/FX source-mislabeling root
             cause is fixed (`unified-trading-library@f237b75a`, 2026-07-26, regression-tested, green QG) and the FX
             `SPOT_PAIR` manifest-`instrument_id` write path for new captures is fixed
             (`market-tick-data-service@020b703e`, 2026-07-25); the billing-guard sub-question was separately
             operator-closed 2026-07-28 (P0→P3). The only genuinely remaining work — backfilling the historically
             mis-stamped rows — is **already** tracked as its own open todo in the same doc ("NEW 2026-07-29 — execute
             the two historical backfills..."), so extracting a duplicate new todo here would create redundant tracking;
             noting the clearance is the correct resolution per this todo's own "redundant/already-covered" clause.
          5. `tradfi_multisource_backfill_2026_06_22.md` (FX yahoo backfill-to-completion) — **left conflict-gated, WITH
             a flagged evidence discrepancy for whoever picks this up next.** `tradfi_satellite_ao_dispatch_batch5_2026_07_29.md`'s
             own Deferred section (authored 2026-07-29/30) asserts "the FIX HASN'T SHIPPED yet, so the sequencing risk is
             unchanged" — but per finding 4 immediately above, the write-path root-cause fix this candidate's risk
             actually depends on (mis-stamping NEW writes) shipped 2026-07-25/26, predating batch5's own authoring date.
             batch5's phrasing appears to conflate that already-shipped write-path fix with the still-open *historical*
             re-stamp (a different, non-blocking concern for NEW writes). Given this is a real GCS-writing VM launch
             (blast radius + CLAUDE.md's VM-launch-justification gate), I am NOT unilaterally clearing it — flagging the
             discrepancy here with citations rather than silently resolving it, per the operator's standing
             never-silently-resolve-a-conflict instruction. Left explicitly deferred; batch5's Deferred section itself
             (a separate active plan, out of this todo's edit scope) should be corrected by whoever next re-triages tradfi.

          **Recommendation for the large/risky doc** — `tradfi_manifest_content_recovery_completion_2026_07_24.md`: **it
          already got its own dedicated pass**, so no new batch is warranted. It was reclassified `assigned_vm: NA` →
          `planning` on 2026-07-27 by `na_docs_validity_and_ao_eligibility_audit_2026_07_26.md` Phase 1 (bounded/
          deterministic, conflict-free against active AO plans), is `status: active`/dispatched, has shipped 17 of 20
          todos, and already carries its own gated finalize plan
          (`tradfi_manifest_content_recovery_completion_2026_07_24_finalize_2026_07_27.md`, `depends_on` +
          `gate_on_depends: true`) to reconcile + archive once its remaining 3 todos land. Nothing further needed from
          this todo.

          **Done-when verified**: all 13 conflict-gated docs (+ 1 special-cased 0-candidate doc, `tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md`,
          already fully RULED+shipped 2026-07-29/30 — see batch5's todo 1) have either (a) a shipped/redundant-already-tracked
          resolution (`tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`, mvp_mode, + the 9 items that cleared
          into batch2 on 2026-07-25) or (b) an explicit, freshly re-verified confirmation the conflict is still open
          (`data_completion_tradfi_2026_07_15.md`, `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`,
          `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md`, `tradfi_multisource_backfill_2026_06_22.md` — the
          last one with a flagged evidence discrepancy for correction); the large/risky doc has a recorded recommendation
          (already covered, no action needed). No repo code changed by this todo — doc-only reconciliation.

- [ ] [DOC] P1. **Archive `tradfi_satellite_ao_dispatch_batch1_2026_07_25.md`** via the standard 6-step ritual (per
      CLAUDE.md's plan-archival rule): migrate any remaining Deferred items to a tracked todo elsewhere (todo 2 above
      should have already resolved all of them — verify none remain) → add the archive banner → run the codex-alignment
      check → grep the corpus for every referrer of `tradfi_satellite_ao_dispatch_batch1_2026_07_25` and fix each path
      to point at the archived location → clear `locked_by` (already empty here, confirm). **Done when**: the plan is
      moved to `plans/archive/2026_07/`, every corpus referrer resolves to the new path, and this finalize doc itself
      gets archived alongside it in the same commit.
