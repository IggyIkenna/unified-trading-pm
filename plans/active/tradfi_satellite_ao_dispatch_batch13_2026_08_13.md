---
doc_type: plan
title: tradfi satellite AO dispatch batch 13 — 2026-08-13
summary: >-
  Extraction batch from the tradfi tranche's 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full sweep — 20
  conflict-cleared, bounded/deterministic items pulled directly from 14 source docs (RECLASSIFY_SPLIT bounded items from
  the NA audit, orphaned_never_touched/orphaned_partial_coverage bounded items from the AG-closeout audit). Each todo
  cites its exact source doc; the source docs themselves are NOT touched by this batch (checkbox reconciliation back
  into each source doc happens in the paired finalize plan). Conflict-checked against every existing active
  batch/finalize plan for this tranche via basename-citation cross-reference before drafting — no item here duplicates
  ground an existing dispatched Todos entry already claims.
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer]
tags: [tradfi, ao-dispatch, satellite-batch, na-eligibility-audit, ag-closeout-audit]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/issues/dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md,
    /plans/active/issues/mtds_combo_chain_rename_broke_three_tests_2026_08_11.md,
    /plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md,
    /plans/active/issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md,
    /plans/active/issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md,
    /plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md,
    /plans/active/issues/tradfi_fx_krw_usd_phantom_rows_fresh_confirmation_2026_08_12.md,
    /plans/active/issues/tradfi_underlying_rename_apply_size_only_verification_gap_2026_08_12.md,
    /plans/active/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md,
    /plans/active/issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md,
    /plans/active/tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md,
    /plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md,
    /plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md,
    /plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 3.0
estimate_calibrated_ai_days: 2.4
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/na-eligibility-audit/SKILL.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
source: >-
  Drafted by the 2026-08-13 /na-eligibility-audit + /ag-closeout-audit full-corpus sweep (interactive session). status:
  draft per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE — needs explicit operator approval (flip to
  status: active) before dispatch.
---

# tradfi satellite AO dispatch batch 13 — 2026-08-13

> **`status: draft` — NOT ingested/dispatched.** Flip to `status: active` only after operator review. Every todo below
> was classified bounded/deterministic (worker-determinable outcome, no open design/judgment call) by the 2026-08-13
> full-sweep audit and conflict-checked against this tranche's existing active batches before being drafted here.

## Todos

- [ ] [DATA] P1. NEW 2026-08-07 (operator sign-off recorded -- agent-executable, full pipeline: measure, migrate, purge
      duplicates). Converge existing GCS chain-bundle + manifest data onto the registry values just shipped above (8
      sector-identity codes XAB/XAF/XAI/XAK/XAP/XAU/XAV/XAY -> *_SECTOR names; 15 micro-contract codes
      M6A/M6B/M6C/M6E/M6J/M6N/M6S/M2K/MCL/MGC/MHG/MNG/MNQ/MSI/MYM -> MICRO-<ROOT> form; plus converge
      unified_api_contracts/canonical/domain/derivatives/tradfi_roots.py's own RootMetadata table onto the same values,
      updating its 2 existing tests). Dry-run measure -> review -> --apply via the extended
      launch-canonical-migration-vm.sh pattern, mirroring the Surface A-D playbook; done when dry-run counts are cited,
      --apply completes with before/after evidence, tradfi_roots.py + tests converged, quality-gates.sh green in both
      unified-api-contracts and market-tick-data-service. Source:
      `plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`
- [ ] [CODE] P2. Add a codified requirement to /codex/02-data/tradfi-databento-sourcing-ssot.md that Databento
      billing-health verification must include one real scoped data-pull, never list_datasets()/warmup() alone Source:
      `plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`
- [ ] [CODE] P2. Sweep and repoint the 9 identified referrer files' citations, then archive this doc via the standard
      6-step ritual Source: `plans/active/issues/tradfi_databento_account_billing_suspended_2026_08_09.md`
- [ ] [CODE] P2. Todo 1: re-run the dry-run with the fixed canonical_twin_path, confirm 100% twin-coverage, re-check
      bucket retention, execute delete via sanctioned UTL helpers if both checks clear - fully specified dispatch shape
      per the section 3a ruling Source: `plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`
- [ ] [CODE] P2. Harden _apply_one's destination-exists branch in migrate_tradfi_underlying_display_names_2026_08.py to
      do a real content/byte comparison before deleting the source, not size-only Source:
      `plans/active/issues/tradfi_underlying_rename_apply_size_only_verification_gap_2026_08_12.md`
- [ ] [SCRIPT] P2. Determine whether any manual-launcher-invocation path has a dedup/collision check against
      already-running VMs for the same shard. Source:
      `plans/active/issues/dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md`
- [ ] [DATA] P3. Confirm the killed duplicate DXY VMs' partial/redundant writes left no non-idempotent side-effects.
      Source: `plans/active/issues/dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md`
- [ ] [CODE] P2. Confirm ccb84c57c9 promoted LDR->main cleanly (gh run/PR check) and flip doc status to resolved +
      archive Source: `plans/active/issues/mtds_combo_chain_rename_broke_three_tests_2026_08_11.md`
- [ ] [CODE] P2. Re-run rebuild_tradfi_manifest.py in market-tick-data-service and verify the live manifest recount
      shows 0 instrument_type=FUTURE rows with populated underlying + null instrument_id Source:
      `plans/active/issues/tradfi_cme_future_typed_blank_instrument_id_2026_08_09.md`
- [ ] [CODE] P2. Land the accurate 'S&P index options' MVP-cell row text (already drafted, cited verbatim) into the
      now-under-cap tradfi_consolidated_closeout_2026_07_18.md Source:
      `plans/active/issues/tradfi_consolidated_closeout_over_line_cap_blocks_routine_edits_2026_08_09.md`
- [ ] [CODE] P2. Todo 1: implement operator-ruled Option A asset-group-aware _resolve_spot_perp fix once CME
      instrument_id string format is confirmed against live catalogue Source:
      `plans/active/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`
- [ ] [CODE] P2. Todo 2: relaunch TRADFI:volatility benchmark once todo 1 lands Source:
      `plans/active/issues/tradfi_volatility_no_perp_fx_underlyings_code_gap_2026_08_06.md`
- [ ] [CODE] P2. Todo 3: reconcile BASE_ASSET/manifest underlying string-naming drift if found to cause accounting
      issues Source: `plans/active/issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md`
- [ ] [CODE] P2. Confirm the correct rolling next-week/last-week JSON access pattern for ForexFactory - does not need
      the residential-proxy credential Source:
      `plans/active/tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md`
- [ ] [CODE] P2. P0 MVP backfill readiness gate: now that the chain-bundle-sampler blocker is code-resolved via batch11,
      run the tradfi MVP backfills and verify manifest-counted canonical rows per MVP cell Source:
      `plans/active/tradfi_phase_d_terminal_gate_2026_07_24.md`
- [ ] [CODE] P2. VERIFY CME mbp_10/trades/tbbo billing-gated declaration Source:
      `plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`
- [ ] [CODE] P2. VERIFY KRX equities registry-vs-adapter mismatch fix still holds live Source:
      `plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`
- [ ] [CODE] P2. Run distinct-values/axis-value census for tradfi and confirm 0 non-canonical values Source:
      `plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`
- [ ] [CODE] P2. Run the tradfi Databento by_date re-feed chain to completion, now genuinely runnable since billing
      access was confirmed live 2026-08-10 Source:
      `plans/active/tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`
- [ ] [CODE] P2. Surgical phantom-row-targeted re-capture of the confirmed KRW/USD (pair,date) cells — fold into/mirror
      the archived remediation plan's design intent, no blind --force-recapture across all 12 FX pairs Source:
      `plans/active/issues/tradfi_fx_krw_usd_phantom_rows_fresh_confirmation_2026_08_12.md`

## Deferred

None — every item drafted here already cleared the conflict-check. Items that did NOT clear (genuinely operator-gated,
time-gated, or too-large-for-a-batch-todo) were left in their source docs and are not duplicated here; see the
2026-08-13 audit's full classification data for the complete list.
