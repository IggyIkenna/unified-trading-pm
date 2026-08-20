---
doc_type: plan
title: Fix HYPERLIQUID k-prefix coin case-sensitivity mismatch (operator-ruled 2026-08-16, canonical uppercase)
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 12): canonical uppercase — matches the
  fleet-wide UPPERCASE instrument_type/symbol convention (D1, cross-asset-canonical-target-ssot.md). Fix
  `catalogue_symbols_for_venue` (`_onchain_perp_batch_symbols.py:132`) and `_fill_to_trade_row`
  (`hyperliquid_s3.py:585`)'s mismatch: the former `.upper()`s the segment while the latter does a case-SENSITIVE
  exact `coin` match, so `kPEPE`/`kBONK`/`kSHIB` requested via the ALL-catalogue path become `KPEPE` and drop
  every real `kPEPE` fill — those instruments record zero even after backfill. Majors (BTC/ETH) unaffected.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [defi, hyperliquid, casing, k-prefix, canonicalization]
related:
  [
    /plans/archive/issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: defi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 12, 2026-08-16 — operator ruling: canonical uppercase"
locked_by:
context_scope:
  [
    /codex/02-data/cross-asset-canonical-target-ssot.md,
    /plans/archive/issues/non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md,
    market-tick-data-service/market_tick_data_service/adapters/hyperliquid_s3.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/_onchain_perp_batch_symbols.py,
  ]
locked_since:
resolved_by:
---

# Fix HYPERLIQUID k-prefix coin case-sensitivity mismatch

## Todos

- [ ] [FIX] P3. **RULED 2026-08-16 (operator): canonical uppercase.** Fix
      `_fill_to_trade_row` (`hyperliquid_s3.py:585`) to match `catalogue_symbols_for_venue`'s existing `.upper()`
      convention instead of doing a case-SENSITIVE exact `coin` match — either uppercase the incoming `coin`
      value before comparison, or maintain an explicit k-prefix uppercase alias map if a case-insensitive
      compare risks colliding with a hypothetical non-rebased `KPEPE`. Verify against real HL fills for
      kPEPE/kBONK/kSHIB (and any other k-prefix coins) that the fix actually restores non-zero captured rows.
      Repo: market-tick-data-service.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 12, operator ruling)**: extracted from
  `non_tardis_dexperp_venue_data_status_smoketest_2026_07_07.md` for AO dispatch, since the parent doc stays
  `assigned_vm: NA` (cannot flip as a unit — other items in that doc are already ruled/shipped separately).
**context-scout 2026-08-17**: populated/refreshed context_scope (4 entries)
