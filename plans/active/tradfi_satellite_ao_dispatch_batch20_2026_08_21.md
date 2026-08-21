---
doc_type: plan
title: TradFi satellite AO-dispatch batch 20 — chain-bundle underlying convergence + reverse-translation wiring
summary: >-
  Extracts 2 genuinely bounded, worker-determinable items from
  `plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` that multiple prior
  na-eligibility-audit passes (2026-08-07 through 2026-08-21) independently flagged as AO-eligible/
  MISCLASSIFIED_LIKELY_AO_ELIGIBLE but never actually extracted, because the source doc's own remaining 2 todos
  (CBOE/VX cross-venue mismatch, the underlying reverse-derivation OPERATOR_QUESTION) stayed genuinely
  dependency/operator-gated and blocked a whole-doc reclassify. This is exactly the extraction the 2026-08-08
  na-eligibility-audit pass recommended: "the next /ag-closeout-audit tradfi pass draft it explicitly, carrying
  both caveats above" (source doc Progress Log, 2026-08-08 entry).
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [tradfi, canonicalization, chain-bundle, ao-dispatch, satellite-batch, underlying-migration]
related:
  [
    /plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md,
    /plans/active/tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16.md,
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
  ]
created: 2026-08-21
last_updated: "2026-08-21"
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.2
estimate_calibrated_ai_days: 0.96
assigned_role: data_engineering
effort: high
drift_direction: advance-code
context_scope:
  [
    /plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    market-tick-data-service/scripts/pipeline_e2e_check.py,
    unified-api-contracts/unified_api_contracts/registry/tradfi_symbology.py,
  ]
depends_on: []
supersedes:
superseded_by:
locked_by:
locked_since:
resolved_by:
source:
  [
    "/ag-closeout-audit tradfi tranche, Phase 3 sweep, 2026-08-21 — re-verified both items are still genuinely open and
    still bounded before extraction (not just trusting the parked audit doc's classification); todo 1 carries a
    2026-08-07 operator sign-off already on record, todo 2 was independently flagged AO-eligible by the source doc's
    own 2026-08-15 Progress Log entry.",
  ]
---

# TradFi satellite AO-dispatch batch 20

## Conflict-check (both todos)

Grepped `plans/active/*.md` + `plans/active/issues/*.md` for the distinguishing terms of each item below
("sector-identity", "MICRO-AUD", "tradfi_roots.py", "Surface A-D", `_canonical_underlying_to_raw_databento`,
`sample_live_instrument`) before drafting — zero hits outside the source doc itself and this batch. Neither item is
claimed by any other active/draft doc. The source doc's own sibling extraction
(`tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16.md`) covers a DIFFERENT todo (the raw-root reverse
derivation for `derive_canonical_id_for_row`) — not a duplicate of either item below.

## Todos

- [ ] [DATA] P1. **Converge existing GCS chain-bundle + manifest data onto the `EXCHANGE_CODE_TO_NAME` registry
      values shipped 2026-08-07** (operator sign-off already recorded — "not just a copy and leave duplicate values,
      a purge/deletes/apply/migration, agents can do it all"). Source: `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`
      todo 2 (the "NEW 2026-08-07" item, verbatim below).

  Mirrors `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s Surface A-D `-USD@LIN` migration playbook
  (dry-run measure → review → `--apply`, never a blind rewrite). Two candidate populations:

  1. **Sector-identity codes** — any live shard/manifest row with
     `underlying=XAB|XAF|XAI|XAK|XAP|XAU|XAV|XAY` needs re-canonicalizing to
     `MATERIALS_SECTOR|ENERGY_SECTOR|INDUSTRIALS_SECTOR|TECH_SECTOR|CONSUMER_STAPLES_SECTOR|UTILITIES_SECTOR|HEALTHCARE_SECTOR|CONSUMER_DISC_SECTOR`
     respectively.
  2. **Micro-contract codes** — any live shard/manifest row with
     `underlying=M6A|M6B|M6C|M6E|M6J|M6N|M6S|M2K|MCL|MGC|MHG|MNG|MNQ|MSI|MYM` (written unresolved/raw, since these
     codes did not exist in the live registry before) needs re-canonicalizing to
     `MICRO-AUD|MICRO-GBP|MICRO-CAD|MICRO-EUR|MICRO-JPY|MICRO-NZD|MICRO-CHF|MICRO-RUSSELL2000|MICRO-CRUDE|MICRO-GOLD|MICRO-COPPER|MICRO-NATGAS|MICRO-NASDAQ100|MICRO-SILVER|MICRO-DOW`
     respectively.

  **A pre-migration measurement must first confirm these rows are genuinely keyed under the raw micro code and not
  already silently folded into their standard-size sibling under some other historical write path** — do not assume
  the "unresolved passthrough" theory is the only failure mode until a live count confirms it. If the dry-run
  surfaces already-conflated/silently-folded data instead of the assumed unresolved-passthrough shape, route that
  anomalous subset to a fresh operator escalation rather than guessing at it (mirrors
  `tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md`'s CME 32,864-row "unresolved residual
  deliberately left untouched by design" precedent).

  **Also converge the 3rd copy found during the original investigation**:
  `unified_api_contracts/canonical/domain/derivatives/tradfi_roots.py` carries its OWN independent `RootMetadata`
  dataclass table with the pre-fix verbose values (`HEATING_OIL`/`SOYBEAN_OIL`/`SOYBEAN_MEAL`/`TREASURY_30Y`/etc.,
  NOT touched by the 2026-08-07 registry edit) — its own reverse-lookup shim (`SOYOIL`→`ZL` etc.) shows live
  manifest data already leans toward the compact form. Converge `tradfi_roots.py` onto the same values (breaking
  change for its existing tests — update alongside, not after).

  **Heavy-I/O rule applies (CLAUDE.md, unconditional)**: the GCS/manifest measure-and-migrate phase runs on a VM,
  never interactively from a dev checkout — reuse `launch-canonical-migration-vm.sh`'s pattern (extend with a new
  category, or add a `--underlying-remap` mode).

  **Ambiguity to resolve before `--apply`, not guess at**: whether "purge duplicates" means real GCS object deletes
  (old-path objects post-rename) vs. pure manifest CAS rewrites — if real object deletes are involved, cite
  `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §3a (bucket retention check) before any delete.

  **Done when**: dry-run counts cited for both populations, `--apply` migration completes with before/after
  evidence per `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md` §8d evidence format
  (`manifest-delta=`/`gcs-op=` as applicable), `tradfi_roots.py` + its tests converged, `quality-gates.sh` green in
  both `unified-api-contracts` and `market-tick-data-service`. Repos: unified-api-contracts,
  market-tick-data-service.

- [ ] [DATA] P2. **Wire the already-shipped `_canonical_underlying_to_raw_databento()` into
      `sample_live_instrument()`'s bundled-chain branch** — currently dead code (zero call sites). Source:
      `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` todo 4 (the "NEW 2026-08-15" item, verbatim below).

  `batch11`'s claimed fix (`MTDS@3cec6a00`, "`_canonical_underlying_to_raw_databento()` shipped in
  `pipeline_e2e_check.py` — covers CME (standard + MICRO-prefix → M-prefixed raw) and CBOE VIX→VX") is genuinely
  shipped, tested code but is never invoked: `sample_live_instrument()`'s bundled-chain branch
  (`scripts/pipeline_e2e_check.py:1407-1426`) still samples the manifest's canonical `underlying` verbatim (only
  filtering garbage values via `is_recognized_tradfi_underlying`) and passes it straight through as
  `instrument_id_or_root` — the reverse-translation function is simply never called, so the checker's force-leg for
  a TRADFI bundled-chain shard still hits `instrument_ids filter ['SP500'] matched nothing` for CME/CBOE.

  **Not currently blocking real MVP backfills** (already verified by the source doc): the production backfill
  launcher (`deployment-service/scripts/vm/launch-tradfi-bf-cme-ohlcv-1m.sh`'s `CME_ROOTS` array) resolves raw
  Databento symbols directly from its own hardcoded table and never calls `sample_live_instrument()` — this fix is
  scoped to the Phase-D smoke-test checker's own force-leg verification of bundled-chain shards, not the real
  backfill/write path.

  **Done when**: `_canonical_underlying_to_raw_databento()` is actually called from `sample_live_instrument()`'s
  bundled-chain branch (TRADFI-scoped, mirroring the existing `is_recognized_tradfi_underlying` guard's scoping)
  before the sampled value is returned as `instrument_id_or_root`, with a regression test proving a CME/CBOE
  chain-bundle force-leg now resolves a raw code instead of a canonical name. Repo: market-tick-data-service.

## Progress Log

- **2026-08-21 (ag-closeout-audit tradfi tranche, Phase 3 sweep)**: drafted. Both items re-verified against the
  source doc's own live content (not just the parked audit doc's one-line orphan-table summary) before extraction —
  todo 1 carries an explicit, broad 2026-08-07 operator sign-off already on record and a precedented safe
  methodology (Surface A-D playbook); todo 2 is a self-contained wire-an-existing-tested-function fix with a clear
  Done-when and zero design ambiguity, explicitly assessed "AO-eligible on its own next dispatch" by the source
  doc's own 2026-08-15 Progress Log entry. Neither depends on the source doc's 2 remaining genuinely-gated todos
  (CBOE/VX cross-venue P1-OPERATOR-DECISION, the underlying-reverse-derivation OPERATOR_QUESTION — already extracted
  separately to `tradfi_chain_bundle_reverse_derivation_ao_dispatch_2026_08_16.md`). `status: draft` /
  `assigned_vm: NA` pending operator review before dispatch, per this batch's own drafting instructions.
