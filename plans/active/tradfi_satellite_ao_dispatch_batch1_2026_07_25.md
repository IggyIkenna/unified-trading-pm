---
doc_type: plan
title: TradFi satellite AO batch 1 — conflict-cleared extraction from the 2026-07-25 orphan audit
summary: >-
  First AO-dispatch batch for tradfi (tradfi has never had one before, unlike sports). Extracted from the 2026-07-25
  orphan-audit's 21 genuinely-orphaned tradfi satellite docs (of 23 audited; the 91% orphan rate reflects that
  `tradfi_consolidated_closeout_2026_07_18.md`'s own dispatched checkboxes cover DIFFERENT scope than its satellite
  docs' actual open items — those only appear in the closeout's "Aggregated source docs (referenced, not duplicated)"
  digest section, an explicit non-coverage index, same pattern confirmed on sports). A 21-agent AO-eligibility-triage
  workflow found 43 candidate AO-eligible todos, but the large majority carried a flagged CONFLICT against the master
  closeout's own open todos. Per the operator's explicit 2026-07-25 instruction to never silently resolve a conflict,
  this batch contains ONLY the 5 todos that survived review (zero-conflict docs, plus one item whose flagged "conflicts"
  were themselves confirmed non-blocking by the triage agent's own text — see each todo's provenance). The remaining 38
  conflict-gated candidates are preserved and queued for the operator, not dropped.
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-1, satellite-docs, conflict-checked]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/ag_closeout_audit_rollout_2026_07_25.md,
    /plans/active/issues/autonomous_session_operator_decisions_2026_07_25.md,
    /plans/active/sports_satellite_ao_dispatch_batch3_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /autonomous session 2026-07-25, driven by the /ag-closeout-audit skill Phase 3 (conflict-checked next-batch drafting)
  after the tradfi orphan-audit found 21 genuinely orphaned docs (of 23). Triage workflow `wf_92bc129c-2a8` (21 agents,
  0 errors) produced 43 AO-eligible candidates; this doc is the conflict-cleared subset only (5 of 43).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# TradFi satellite AO batch 1 — conflict-cleared extraction

> **Status: draft.** Per CLAUDE.md's plan-destination rule and the ag-closeout-audit skill's autonomous-mode guidance, a
> skill-drafted AO batch is never auto-shipped to `active` — flip this frontmatter's `status` to `active` only after
> operator review. All 5 todos below are same-priority and touch distinct files (verified against the triage journal,
> `subagents/workflows/wf_92bc129c-2a8/journal.jsonl`) so they are safe to dispatch concurrently once activated. This is
> a deliberately SMALL first batch — 38 of 43 AO-eligible candidates the triage found were excluded because they carried
> a flagged conflict against `tradfi_consolidated_closeout_2026_07_18.md`'s own open todos; see the Deferred section.

## Todos

- [ ] [REVIEW] P1. Exhaustively diff `EXCHANGE_CODE_TO_NAME` between
      `unified_api_contracts/registry/tradfi_instrument_universe.py` and
      `unified_api_contracts/registry/tradfi_symbology.py` — enumerate EVERY key present in only one dict and every key
      whose value disagrees between the two (the doc's own banner names only 2 spot-checked entries, `HO` and `NG` — the
      full disagreement set is not yet enumerated), and append the complete comparison table to this issue doc's
      evidence trail for operator review. This is a pure enumeration/audit task — it does NOT decide which dict is
      authoritative or merge them (that decision is human-only). Repo: unified-api-contracts. **Done when**: a
      key-by-key comparison covering the full union of keys in both dicts is produced and committed (either a small
      comparison script under unified-api-contracts plus its printed/saved output, or a markdown table appended directly
      to the issue doc's evidence trail) — every key in either dict is accounted for as match / value-mismatch /
      present-in-only-one, 0 keys skipped or sampled. No dict is edited and no authoritative choice is made by this
      todo. Source: `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`.
- [ ] [REVIEW] P1. **Close out the two non-blocked remaining todos in
      `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` in one pass** (combined into one todo because both edit
      the SAME doc file and would collide if dispatched as two concurrent AO todos): (1) Verify or correct the doc's
      "cefi + sports already done" claim (frontmatter `summary:` + the BLOCKED-OPERATOR-DECISION todo's banner prose) —
      search the corpus, starting with `plans/active/issues/sports_legacy_duplicate_triage_2026_07_22.md` (already
      measures 0 of 34,385 sports `B_legacy_duplicate` rows passing the 5-part delete-safety proof as of 2026-07-22,
      refreshed 2026-07-25), for evidence sports's legacy-twin population has since fully closed; if found, cite it and
      leave the claim as-is; if not found (the existing evidence strongly suggests not), edit the summary + banner text
      to state sports is NOT yet done, with the real current state + citation. (2) Run the dry-run — never `--apply` —
      `cleanup_legacy_twins.py --asset-group tradfi     --report-uri _index/audit/orphan_sweep_tradfi.parquet --dry-run`
      (`instruments-service/scripts/cleanup_legacy_twins.py`) against the 995 `B_legacy_duplicate` candidate rows in
      `gs://market-data-tick-tradfi-prd-central-element-323112/_index/audit/orphan_sweep_tradfi.parquet`, and post the
      dry-run output (report path + row count + byte-verify result) into the doc's Progress Log as the evidence the
      BLOCKED-OPERATOR-DECISION todo needs for the sign-off ask. Both edits land in the same commit to the one doc.
      Repos: unified-trading-pm, instruments-service. **Done when**: (a) the doc's "cefi + sports already done" claim is
      either cited-and-kept with evidence, or corrected to the real state with a citation; (b) the dry-run output
      (report path + row count) is posted into the doc's Progress Log; `--apply` is NOT run in either step. Source:
      `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`.
- [ ] [DIAG] P1. Confirm the terminal-state of the in-flight CBOE force+skip re-verification VM launched at the
      2026-07-24 session's wrap-up
      (`data-pipeline-check-mtds --asset-group TRADFI --venue CBOE --data-types     ohlcv_1s,ohlcv_1m --day 2026-07-13 --legs force,skip --require-captured --auto-day`,
      against code tarball `mtds-code@0205eaab...`) — read the VM's `run.log` and/or the manifest state to determine
      whether CBOE force+skip for both ohlcv_1s and ohlcv_1m passed cleanly, or failed; if the original VM/its artifacts
      are no longer reachable (>24h elapsed since launch), re-run the identical command fresh against the current
      `market-tick-data-service` codebase rather than searching for a phantom VM. Record the definitive verdict +
      evidence citation in this doc, replacing the "Still in-flight" note. Repo: market-tick-data-service. **Done
      when**: a definitive pass/fail verdict for CBOE ohlcv_1s+ohlcv_1m force+skip legs is recorded in
      `plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md` with an evidence citation (a VM run.log GCS path, or a
      `plans/audit/results/` report path if freshly re-run), replacing the "Still in-flight at session end" row in the
      Deferred-work table. Source: `tradfi_phase_d_terminal_gate_2026_07_24.md`.
- [ ] [DOC] P1. Add the two Phase-D pipeline-check launcher name patterns as named candidates in
      `vm_fleet_preemption_autorecovery_gap_2026_07_23.md`'s item 8/9 scoping list. `mtds-backfill-*-pipelinecheck-*`
      and `instr-backfill-*-pipelinecheck-*` are registered in the fleet relaunch machinery by launcher-prefix match but
      were never named as candidates for the native-shutdown-script (`lc_write_preemption_signal_file`)
      early-preemption-blind-window fix that 3 other launchers already carry, despite exhibiting the exact same
      early-boot `vm_self_deleted_no_exit_status` preemption pattern this Phase-D terminal-gate work measured repeatedly
      on single-shard smoke-test VMs. This is a doc-only scoping addition (alongside the already-listed
      `launch-mtds-dex-swaps-backfill-vm.sh` example) — NOT the code fix itself, which remains that issue doc's own
      future work. Repo: unified-trading-pm. **Done when**:
      `plans/active/issues/vm_fleet_preemption_autorecovery_gap_2026_07_23.md`'s item 8 and/or item 9 candidate list
      explicitly names both `mtds-backfill-*-pipelinecheck-*` and `instr-backfill-*-pipelinecheck-*` as candidates for
      the native-shutdown-script pattern rollout. Source: `tradfi_phase_d_terminal_gate_2026_07_24.md`.
- [ ] [CODE] P1. **Extend the 1-4 leg hard cap + logged-drop behavior to Deribit's existing combo builders** — mirror
      the pattern already implemented for CME/CBOE spreads in
      `instruments_service/reference_data/adapters/tradfi/databento/symbology.py` (operator spec 2026-07-09: 1-4 real
      legs captured as structured `InstrumentLeg`s; a genuine 5+-leg combo is dropped — NOT captured, NOT truncated —
      with the real leg count logged) onto Deribit's two existing combo leg-parsers:
      `instruments_service/reference_data/adapters/cefi/deribit_combo_adapter.py::_build_legs()` and
      `instruments_service/reference_data/adapters/cefi/tardis/combos.py::_parse_deribit_combo_legs()`. Verified live
      (2026-07-25) neither file currently has any max-leg-count check or drop-and-log path — `tardis/combos.py`'s
      `_STRUCTURES` table tops out at 4-leg shapes (condors/jelly-rolls) but nothing rejects/logs a genuine 5+-leg raw
      combo, and `deribit_combo_adapter.py::_build_legs()` has no leg-count bound at all. **Conflict-check note**: the
      triage's own flagged "conflicts" for this item are BOTH explicitly non-blocking — one is
      `tradfi_consolidated_closeout_2026_07_18.md`'s own digest citing this exact item verbatim (a pointer, not a
      competing claim, per the triage agent's own text: "not an independent or conflicting claim"); the other names two
      DIFFERENT, merely Deribit-combo-adjacent findings (a mistagging root-cause investigation and a candle-path
      classification investigation) that the triage agent itself flagged only "for the operator's awareness" while
      stating neither directly conflicts. Repo: instruments-service. **Done when**: both
      `deribit_combo_adapter.py::_build_legs()` and `tardis/combos.py::_parse_deribit_combo_legs()` cap at 4 legs and
      drop (not truncate) any input with 5+ real legs, emitting a log record with the real leg count — mirroring the
      CME/CBOE 5-leg-drop unit-test coverage pattern (`test_g1c_xcbf_spreads_decompose_to_combo`'s 5-leg-drops case) —
      with new/updated unit tests in `tests/unit/test_deribit_combo_adapter.py`,
      `tests/unit/test_cefi_deribit_combo_boost.py`, and/or `tests/unit/test_cefi_tradfi_comprehensive.py` asserting the
      5-leg case is dropped-and-logged, not silently truncated to 4; `quality-gates.sh --no-fix` green. Source:
      `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`.

## Deferred — conflict-gated (NOT dispatched; queued for operator review)

The 21-agent triage workflow (`wf_92bc129c-2a8`) found 38 more AO-eligible candidates across 14 more docs (corrected
2026-07-25 plan-reconcile — the doc list below always had 14 entries, matching the 33+5=38 candidate math; "16" was a
stale count) that carried a flagged conflict against `tradfi_consolidated_closeout_2026_07_18.md`'s own open todos. Per
the operator's 2026-07-25 instruction, these are NOT silently resolved or dispatched here. Full detail (todo text +
conflict quote) is in the triage journal (`subagents/workflows/wf_92bc129c-2a8/journal.jsonl`). Docs with conflict-gated
candidates: `data_completion_tradfi_2026_07_15.md` (4 items), `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` (9
items), `issues/cme_combo_underlying_extraction_garbage_2026_07_19.md` (1),
`issues/databento_default_executor_dns_starvation_risk_2026_07_17.md` (1),
`issues/tradfi_backfill_oom_remediation_2026_06_24.md` (2),
`issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md` (1),
`issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md` (2),
`issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` (0 AO-eligible but 1 conflict logged against the doc
generally), `issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md` (2),
`issues/tradfi_todo_cells_below_vendor_discovery_floor_2026_07_20.md` (1),
`issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` (1),
`tradfi_backfill_throughput_followups_2026_07_24.md` (7), `tradfi_multisource_backfill_2026_06_22.md` (2).

Also deferred entirely (flagged `doc_too_large_or_risky_for_batch` by the triage — needs its own dedicated triage/design
pass): `tradfi_manifest_content_recovery_completion_2026_07_24.md` (5 AO-eligible candidates found, 5 conflicts —
genuinely needs its own batch, not folded in here).

**2026-07-25 re-check (batchN methodology, `/ag-closeout-audit`)**: this section's 33 conflict-gated candidates were
re-checked against `tradfi_consolidated_closeout_2026_07_18.md`'s live content + a git-log sweep of the relevant repos.
20 cleared (11 shipped independently outside AO between this triage and the re-check, 9 resolved by re-mapping each
conflict to its actual target candidate rather than the whole source doc), landing in
`tradfi_satellite_ao_dispatch_batch2_2026_07_25.md` (11 dispatchable todos after same-file-collision combining); 8
remain genuinely conflict-gated (see that plan's own Deferred section for the current per-item status).
`tradfi_manifest_content_recovery_completion_2026_07_24.md` is still excluded from both batches — still needs its own
dedicated pass.

Every other orphaned doc's remaining work is human-only (operator sign-off, unbuilt safety tooling, time-gated accrual,
or a genuine design/judgment call) — see the triage journal for the full breakdown (~95 human-only items across the 21
docs).

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`tradfi_satellite_ao_dispatch_batch1_finalize_2026_07_25.md`
(`depends_on: [tradfi_satellite_ao_dispatch_batch1_2026_07_25]`

- `gate_on_depends: true`), mirroring the sports batch2/batch3 finalize-plan pattern.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc.
