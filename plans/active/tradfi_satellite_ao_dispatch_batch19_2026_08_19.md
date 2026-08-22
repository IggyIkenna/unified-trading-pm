---
doc_type: plan
title: TradFi satellite AO-dispatch batch 19 — /ag-closeout-audit Phase 1 orphan extraction (12 conflict-clear items)
summary: >-
  Extracted from `/ag-closeout-audit tradfi`'s 2026-08-19 Phase 0-2 run: a 71-agent Workflow classified every
  tradfi-primary candidate doc (generated via `generate_ag_closeout_audit_candidates.py`) against the tranche's
  32-doc covering-plan family (consolidated closeout + its 4 forked children + batches 9/12/13/15-18 + 4 named
  ao_dispatch pairs, all with finalize pairs). Result: 23 exclude_cross_cutting (mostly already-multi/cross-tagged
  docs whose tradfi slice is closed/trivial — see the parked-findings doc for the handful with a genuine tag-drift
  worth a dedicated fix), 3 archivable_now, 11 archivable_after_planned_work, 34 orphaned (13 never_touched + 21
  partial_coverage). Of the 34 orphaned, this batch extracts the 12 items whose Phase-1 agent tagged
  `gating_category: none` (clean, bounded, no operator/time/too-large/conflict/human-only gate) AND that this
  Phase-3 conflict-check found no live collision for. The other 22 orphaned docs' remaining work is genuinely gated
  (operator-decision, time-gated, too-large-for-a-batch-todo, conflict-gated, or human-only-permanent) — tracked in
  `## Deferred` below per the skill's non-batchable taxonomy, not silently dropped.
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos:
  [
    instruments-service,
    market-tick-data-service,
    features-service,
    deployment-service,
  ]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-19, satellite-docs, ag-closeout-audit, conflict-checked]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md,
    /plans/active/issues/tradfi_vm_resource_utilization_downsize_2026_08_10.md,
    /plans/active/issues/tradfi_fred_forward_capture_and_backfill_gap_2026_08_13.md,
    /plans/active/issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md,
    /plans/active/issues/tradfi_instrument_type_lowercase_residual_381k_2026_08_15.md,
    /plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md,
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md,
    /plans/active/data_completion_tradfi_2026_07_15.md,
    /plans/archive/issues/ag_closeout_audit_tradfi_parked_2026_08_19.md,
  ]
created: 2026-08-19
last_updated: 2026-08-19
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
milestone: POST
estimate_class: infra
estimate_baseline_ai_days: 2.6
estimate_calibrated_ai_days: 2.08
assigned_role: data_engineering
effort: medium
sequential: false
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
supersedes:
superseded_by:
locked_by:
locked_since:
source: >-
  `/ag-closeout-audit tradfi` Phase 0-3, dispatch agt-8b4230, slot 29, 2026-08-19. Phase 1 ran a 71-agent Workflow
  (one agent per candidate doc, medium/default effort, structured-schema verdicts). Phase 3 conflict-check: for
  each of the 12 items below, grepped the tradfi consolidated-closeout's own Todos, every batch 9-18 + finalize
  pair, the 4 named ao_dispatch pairs, and the one still-draft `batch9_2026_08_16` for a competing claim on the
  same file/fix — none found (each Phase-1 agent's own coverage-grep already surfaced zero hits against the
  32-doc covering family; this pass additionally checked the one draft-batch surface the per-doc agents were not
  given, per the skill's Phase 3 "4th surface" instruction). Per the skill's autonomous-mode contract this batch
  ships `status: draft` regardless of how clean the conflict-check came back — flipping to `active` is an operator
  decision, never autonomous.
---

# TradFi satellite AO-dispatch batch 19

> 12 items, all independent (no ordering constraint), touching disjoint files — dispatch concurrently. Item 5 wraps
> its source doc's todo1+todo4 into one unit (todo4 is explicitly sequenced after todo1 in the source doc, so they
> are combined per the skill's "internally-sequential work becomes ONE combined todo" rule). Item 7 combines 3
> independent CME/databento-adapter-area bug fixes from the same source doc into one unit purely to avoid a
> same-file concurrent-edit collision with itself (not a true sequential dependency between the 3 sub-fixes).

## Todos

- [ ] [DATA] P3. **Standing catalogue-reconciliation re-run.** Re-run `canonicalize_cboe_vx_combo_catalog_2026_07_08.py`
      and `canonicalize_dbeq_stock_class_catalog_2026_07_08.py` dry-run against the live `prod/catalog.parquet`
      (instruments-service). If residual CBOE `SPOT_PAIR` / DBEQ `SPOT_PAIR` rows are found (>0), run `--apply`,
      re-verify 0 residual, and flip the source doc's standing-reconciliation checkbox citing fresh evidence (row
      counts + timestamp). This is a recurring check — last executed 2026-08-09 (batch8); no batch since has picked
      up the next `build_instrument_catalogue.py` roll-up cycle instance.
      Done when: dry-run evidence posted to the source doc's Progress Log, `--apply` run (if needed) with
      before/after counts, checkbox re-flipped.
      Source: `plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` (sole open item, lines
      213-224).

- [ ] [DATA] P2. **Re-measure downsized TradFi OHLCV fleet throughput/CPU.** On the downsized (e2-highmem-8,
      `TRADFI_OHLCV_BATCH_DATE_CONCURRENCY=20`) fleet, re-measure throughput + CPU utilization using a genuinely
      comparable completed CME/NQ/ES/GC-class heavy-root VM run (the CFE/VX and CBOE-idx samples gathered so far are
      explicitly not comparable per the source doc's own notes). Done when: throughput is within ~10% of the
      historical ~46.9k rows/min/VM CME baseline AND the CPU pattern is still brief-burst (not sustained
      near-100%). If either leg fails: delete the `TRADFI_OHLCV_BATCH_DATE_CONCURRENCY=20` override in
      `deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh` (reverts to the auto-derived value of 10 on 8
      vCPU), then re-measure once more before considering any further downsize.
      Source: `plans/active/issues/tradfi_vm_resource_utilization_downsize_2026_08_10.md` (sole open item, lines
      106-115).

- [ ] [DATA] P2. **Root-cause FRED `attempted_failed` accrual post-fix.** Investigate why prod continued to accrue
      `attempted_failed` `ohlcv_15m`/`ohlcv_1s` FRED rows across 2026-07-29→2026-08-05, after the FRED
      capability-filter fix had already shipped. Fix inline if the cause is clear from the investigation; otherwise
      file a narrower, specifically-scoped follow-up issue doc.
      Done when: root cause identified and either fixed (with before/after evidence) or handed off via a new,
      narrowly-scoped issue doc citing this investigation's findings.
      Source: `plans/active/issues/tradfi_fred_forward_capture_and_backfill_gap_2026_08_13.md` (Finding 1, lines
      79-88).

- [ ] [DATA] P2. **Confirm/resume FRED historical backfill toward the 1962-1970 floor.** Confirm current FRED
      backfill VM/state (none found in the launcher fleet as of the 2026-08-07 audit); re-verify the
      99-captured-dates / zero-1962-1970-floor-dates read against current prod. Then either launch/resume the
      backfill toward the 1962-1970 floor, or — if the floor genuinely isn't reachable/needed — correct the
      "self-sufficient to completion" claim at `macro_micro_econ_data_capture_audit_2026_06_05.md:515`.
      Done when: either a live FRED backfill VM is confirmed running/completed with evidence, or the stale claim is
      corrected with a citation to why the floor doesn't apply.
      Source: `plans/active/issues/tradfi_fred_forward_capture_and_backfill_gap_2026_08_13.md` (Finding 2, lines
      79-88).

- [ ] [DATA] P0. **Execute the operator-approved CF11 shard-atom-mismatch purge, then re-measure the dependent
      alert ratio.** Run `retire_tradfi_cf11_bundle_grain_shard_atom_mismatch_2026_07_30.py --apply` — already
      operator-RULED GO-AHEAD (2026-08-07, agent-executable) and already dry-run-verified, retiring 81,454
      confirmed-safe stale CME+CBOE manifest rows. Its prior dispatch vehicle (`batch5_2026_07_29`) was archived
      without ever running it. Once landed, re-measure the `DP_RUN_MOSTLY_EMPTY` CME `ohlcv_1s`/`ohlcv_1m` ratio to
      confirm the alert's denominator is no longer inflated by the now-purged false-positive population.
      Delete-safety: prior explicit 2026-08-07 operator ruling is the citation (per CLAUDE.md's AO-delete-gating
      rule) — script was purpose-built + dry-run-verified for this exact purge, no fresh `[OPERATOR]` tag needed.
      Done when: `--apply` completes with before/after row counts, self-verify shows 0 remaining CF11
      shard-atom-mismatch rows, and the re-measured `DP_RUN_MOSTLY_EMPTY` ratio is posted to the source doc.
      Source: `plans/active/issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md` (todo1 lines
      256-267 + todo4 lines 280-281, combined — todo4 is explicitly sequenced after todo1).

- [ ] [DIAG] P3. **Identify the writer behind 787 blank-instrument_type manifest rows.** 787 tradfi manifest rows
      carry `capture_status=captured` but blank `instrument_type`+`instrument_id`, all sharing the exact
      `written_at=2026-07-16T07:04:10` (CME/NASDAQ/NYSE, `ohlcv_1m`/`tbbo`, source=databento). Identify the
      writer/script responsible and determine whether these are safely re-derivable from other manifest columns, or
      declare them an accepted legacy gap (with reasoning).
      Done when: writer identified (or genuinely exhausted the search and said so), and either a derivation fix
      ships or the doc's open item is closed with an explicit accepted-legacy-gap note.
      Source: `plans/active/issues/tradfi_instrument_type_lowercase_residual_381k_2026_08_15.md` (open todo A,
      lines 396-404).

- [ ] [FIX] P2. **3 CME/databento adapter defects (combined — same code area, avoid a same-file race).**
      (a) CME event contracts are misclassified as `OPTION` instead of `EVENT_CONTRACT`:
      `databento/adapter.py:764-766` assumes `instrument_class='BAG'`, but Databento actually returns `C`/`P` for
      these — fix the classification logic. (b) CME/ICE live combo-spread legs are silently dropped with a
      WARNING-only log and no failure signal surfaced (assessed 2026-07-14, never fixed) — surface a real failure
      signal or handle the leg correctly. (c) 2 anomalous Sundays (2024-06-02, 2024-10-06) in the CME
      instrument-definitions manifest hard-fail instead of writing an honest `empty_confirmed` row — fix the
      adapter to write the honest row instead of hard-failing.
      Done when: all 3 sub-fixes ship with a regression test each (or a cited reason one is infeasible), and the 2
      source docs' respective open items are updated to cite this todo's evidence.
      Source: `plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md` (2 newly-identified
      prose findings + the partial P2/P3 sweep item, line 447) and
      `plans/active/issues/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` (Deferred-work table item 2,
      line 671).

- [ ] [FIX] P2. **Fix silent ICE/CBOE INDEX instrument failures.** `umi_tick_provider.py:123,493,499` falls through
      to Databento instead of an explicit Yahoo early-return for ICE/CBOE INDEX instruments, returning empty with
      no error signal. Add explicit routing (or an explicit, logged early-return) so this fails loudly instead of
      silently.
      Done when: fix ships with a regression test proving an ICE/CBOE INDEX instrument now either resolves via
      Yahoo or surfaces a real error, not a silent empty result.
      Source: `plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md` (newly-identified prose
      finding, never a todo).

- [ ] [FIX] P3. **Fix Yahoo fetch functions ignoring the `instrument_ids` filter.** `_umi_yahoo.py`'s
      `fetch_yahoo_fx`/`fetch_yahoo_equities` never respect the `instrument_ids` filter argument — they always
      fetch the full static registry instead. Concrete symptom: `KRX:INDEX:KOSPI-USD` is unreachable as a result.
      Done when: both functions honor `instrument_ids` when provided, with a regression test covering the
      KOSPI-USD case.
      Source: `plans/active/issues/mtds_is_full_adapter_smoketest_findings_2026_07_07.md` (newly-identified prose
      finding, never a todo).

- [ ] [CODE] P2. **Wire the dead-code raw-Databento-symbol resolver into the chain-bundle sampler.** The
      already-shipped `_canonical_underlying_to_raw_databento()` is dead code — wire it into
      `sample_live_instrument()`'s bundled-chain branch in `pipeline_e2e_check.py`, plus add a regression test
      proving a CME/CBOE chain-bundle force-leg resolves to a raw code instead of a canonical name.
      Done when: fix ships, regression test passes, and the source doc's Todo 1 (currently DEPENDENCY_BLOCKED on
      this landing) is re-verified against fresh CBOE data.
      Source: `plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (Todo 4, line 291).

- [ ] [DATA] P2. **Run the now-unblocked EIA live integration test + backfill.** `test_eia_live` + the EIA backfill
      were blocked on a credential; the key is now provisioned. Run the live integration test, then run/verify the
      EIA backfill.
      Done when: `test_eia_live` passes against the live API, and the EIA backfill either completes or its current
      progress + remaining ETA is posted to the source doc.
      Source: `plans/active/data_completion_tradfi_2026_07_15.md` (line 529).

- [ ] [DATA] P2. **Re-run the phantom-manifest reconciliation dry-run on a dedicated VM.** A prior attempt to run
      `reconcile_phantom_manifest_rows_all.py --asset-group tradfi --dry-run` was aborted 2026-07-30 on the shared
      planning host (memory-bound discipline). Re-run it on a dedicated VM per
      `/codex/05-infrastructure/vm-launcher-runbook.md` § "Heavy COMPUTE/MEMORY on the shared planning-vm" instead
      of the shared host.
      Done when: the dry-run completes on a dedicated VM with a full results summary posted to the source doc's
      Progress Log.
      Source: `plans/active/data_completion_tradfi_2026_07_15.md` (line 416).

## Deferred — non-batchable (taxonomy per `cursor-configs/skills/ag-closeout-audit/SKILL.md`)

**Too-large-or-risky-for-a-batch-todo:**

- `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` Deferred-work item 1 (line 670): full CME
  instrument-definitions re-fetch for 2020-01-01→2026-06-18 (~2,368 days) to pick up the post-lockdown EC*
  event-contract + DBEQ.BASIC consolidated universe. Scoped but genuinely VM-scale backfill work — needs its own
  dedicated plan (sizing, spot-VM launch, rightsizing check), not a single mechanical batch line.
- `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` Todo 1 (line 221): CBOE/VX cross-venue canonical-root
  mismatch — explicitly DEPENDENCY_BLOCKED on this batch's item 10 (Todo 4) landing first, then needs a fresh
  non-stale CBOE force-leg re-verification. Candidate for batch20 once item 10 ships.
- `data_completion_tradfi_line_cap_blocks_e7_stale_item_close_2026_08_16.md` (Phase-1 gating: too-large-or-risky) —
  its own doc name says why (line-cap-blocked).
- `plan_reconciler_findings_tradfi_2026_08_16.md` (Phase-1 gating: too-large-or-risky).
- `tradfi_deprecated_etf_manifest_rows_forward_scope_drift_2026_08_18.md` (Phase-1 gating: too-large-or-risky —
  distinct residual beyond what batch18 already extracted).

**Operator-gated (business/credential/whole-bucket-destroy judgment, per finding U's positive test — not reflexive):**

- `databento_ice_opra_subscription_ask_2026_08_09.md` — BLOCKED-CREDENTIALS, ICE/OPRA subscription billing decision.
- `tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md` — BLOCKED-CREDENTIALS, residential-proxy
  account provision (well-documented since 2026-08-10, still unactioned).
- `tradfi_databento_account_billing_suspended_2026_08_09.md` — billing/account-status decision.
- `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` — explicit sign-off-gated bucket delete.
- `tradfi_catalogue_regen_scheduler_silently_not_paused_2026_08_08.md` — Phase-1 gating: human-only-permanent.
- 4× `dp_vm_001_*` relaunch-bound-page docs (`mdps_tradfi_2021_exit_nonzero_stale_tarball_rootcause_2026_08_16`,
  `mdps_tradfi_2026_exit_nonzero_relaunch_bound_page_2026_08_14`,
  `tradfi_bf_cme_ohlcv_1m_btc_2020_exit137_stall_relaunch_bound_page_2026_08_16`, plus 3 more `bf_cme_ohlcv_1m`
  stall/relaunch pages with `orphaned_partial_coverage`) — each is a live-incident relaunch-bound page; per this
  workspace's DP-VM-001 convention these page-and-track, they are not batch-todo material.
- `tradfi_tbbo_unclassified_adapter_error_dp_fetch_009_2026_08_15.md`,
  `tradfi_underlying_rename_apply_size_only_verification_gap_2026_08_12.md`,
  `tradfi_reconciliation_2026_08_17_findings_2026_08_17.md`,
  `features_service_calendar_domain_manifest_tracking_gap_2026_08_18.md`,
  `plan_reconciler_findings_tradfi_2026_08_18.md` — each Phase-1-verdicted operator-gated; see each doc's own text
  for the specific gate.

**Time-gated:**

- `source_column_blank_on_external_cells_2026_08_15.md` — gated on elapsed real time per Phase 1.

**Conflict-gated (re-triageable in a future batch once the conflict clears):**

- `tradfi_legacy_twin_candidates_already_absent_unexplained_2026_08_14.md` — P2 item already explicitly PARKED
  `BLOCKED-OPERATOR-DECISION` since 2026-08-16, reconfirmed 2026-08-19 (na-eligibility-audit, same day). Re-check
  next batch per the standard "check the prior park first" step.

**Process/meta findings (not tradfi content work) — see `ag_closeout_audit_tradfi_parked_2026_08_19.md`:**

- The 23 `exclude_cross_cutting` verdicts (mistag/multi-tag observations, most "working as designed" but a few
  genuine tag-drift worth a dedicated fix) and one live inconsistency between two Phase-1 agents on sibling
  DP_CRON docs.

## Progress Log

- **2026-08-19, ag_closeout_auditor (dispatch agt-8b4230, slot 29)**: batch drafted per `/ag-closeout-audit tradfi`
  Phase 3. 12 items extracted from 34 orphaned docs (22 deferred per the non-batchable taxonomy above). Conflict
  check clean against the full 32-doc covering family + the one still-draft `batch9_2026_08_16`. `status: draft` —
  awaiting operator review/flip per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE.
