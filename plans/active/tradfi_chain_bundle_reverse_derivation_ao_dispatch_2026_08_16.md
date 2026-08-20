---
doc_type: plan
title: Fix tradfi chain-bundle raw-symbol reverse derivation (operator-ruled direction 2026-08-16)
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 8) on
  tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md: raw→canonical stays authoritative
  (`canonicalize_raw_tradfi_id`'s forward direction is correct and must not change). The break is in the
  REVERSE direction — recovering the original raw root token (e.g. `XAU`) from a sector-identity-mapped
  canonical name, which `derive_canonical_id_for_row` (in
  `rewrite_tradfi_chain_bundle_content_id_2026_07_25.py`) needs and currently gets `QUARANTINE_UNPARSEABLE` for.
  Per the ruling: build the reverse path by DERIVING it from the authoritative forward
  (`canonicalize_raw_tradfi_id`) mapping — e.g. an explicit reverse-lookup table built FROM the forward
  function's own EXCHANGE_CODE_TO_NAME-driven output, not a separately hand-maintained reverse function that can
  drift out of sync with the forward direction again (which is what broke it this time, per
  `unified-api-contracts@00b2de54`'s sector-identity convergence). Once fixed, re-enable the skipped test.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts]
scope: [engineer]
tags: [tradfi, canonicalization, reverse-derivation, chain-bundle]
related:
  [
    /plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-20"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.7
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 8, 2026-08-16 — operator ruling: raw→canonical authoritative"
locked_by:
context_scope:
  [
    /plans/active/issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md,
    unified-api-contracts/unified_api_contracts/internal/reference/tradfi_id_canonicalizer.py,
    market-tick-data-service/market_tick_data_service/scripts/rewrite_tradfi_chain_bundle_content_id_2026_07_25.py,
    market-tick-data-service/tests/unit/scripts/test_rewrite_tradfi_chain_bundle_content_id_2026_07_25.py,
  ]
locked_since:
resolved_by:
---

# Fix tradfi chain-bundle raw-symbol reverse derivation

## Todos

- [ ] [DATA] P2. **Fix the REVERSE direction of tradfi chain-bundle canonicalization** —
      `derive_canonical_id_for_row` (`rewrite_tradfi_chain_bundle_content_id_2026_07_25.py`) needs to recover
      the original raw root token (e.g. `XAU` from `XAUH0`) from a sector-identity-mapped canonical name; it
      currently gets `QUARANTINE_UNPARSEABLE`. **RULED 2026-08-16 (operator): raw→canonical
      (`canonicalize_raw_tradfi_id`) stays authoritative — do not change its behavior.** Build
      this as an explicit reverse-lookup DERIVED FROM the authoritative forward mapping's own
      `EXCHANGE_CODE_TO_NAME`-driven output (not a separately hand-maintained reverse function — that's exactly
      what drifted out of sync when `unified-api-contracts@00b2de54`'s sector-identity convergence landed).
      Re-enable the skipped test
      (`tests/unit/scripts/test_rewrite_tradfi_chain_bundle_content_id_2026_07_25.py::test_derive_future_id_from_raw_databento_symbol`)
      once the reverse path resolves `CME:FUTURE:XAU-USD@LIN-...` correctly again. Repos: market-tick-data-service,
      unified-api-contracts.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 8, operator ruling)**: extracted from
  `tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`'s P2-OPERATOR-DECISION todo, since the parent doc
  stays `assigned_vm: NA` (other todos in that doc remain genuinely dependency/operator-blocked).
- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
