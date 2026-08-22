---
doc_type: issue
title: LIQUIDATION_CAPTURE has no CEFI implementation — capability manifest's hyperliquid cell is aspirational-only
summary: >-
  LIQUIDATION_CAPTURE's engine is a DeFi-only flash-loan atomic bundle, structurally inapplicable to CEX order
  books. The 5 CEFI venues showing as CSV "consumers" are a generate_venue_work_list.py data_type-name false
  positive. The capability manifest's one CEFI cell (hyperliquid, PARTIAL) describes a different, unimplemented
  bid-ladder mechanism with zero code. CEFI exclusion confirmed intentional in strategy-service@f89c6d8235; a real
  CEFI variant is unbuilt new archetype design, tracked here as follow-ups.
status: open
nature: issue
asset_group: [cefi]
stage: [strategy]
repos: [strategy-service, unified-api-contracts]
scope: [engineer]
tags: [cefi, liquidation_capture, archetype_slot, capability_manifest, plan-authoring]
related:
  - /plans/archive/2026_08/cefi_venue_e2e_batch1_2026_08_16.md
  - /plans/active/cefi_consolidated_closeout_2026_07_18.md
created: "2026-08-17"
author: worker-slot-11
source:
  - cefi_venue_e2e_batch1_2026_08_16.md LIQUIDATION_CAPTURE gap todo (task cefi_venue_e2e_batch1-86f64bd3ee20)
assigned_vm: NA
parent_epic: security_and_cross_cutting_master
resolved_by:
locked_by:
priority: P3
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    strategy-service/strategy_service/engine/strategies/v2/arbitrage_structural/liquidation_capture.py,
    strategy-service/strategy_service/engine/strategies/v2/archetype_slots_defi.py,
    unified-api-contracts/scripts/generate_venue_work_list.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json,
    /plans/archive/2026_08/cefi_venue_e2e_batch1_2026_08_16.md,
  ]
---

# What I found

`cefi_venue_e2e_batch1_2026_08_16.md`'s LIQUIDATION_CAPTURE gap todo asked whether at least one CEFI venue can be
added to `LIQUIDATION_CAPTURE`'s slot declaration, or whether the CEFI exclusion should be confirmed intentional.
Investigation (strategy-service):

- `LiquidationCaptureEngine.on_tick` (`strategy_service/engine/strategies/v2/arbitrage_structural/liquidation_capture.py`)
  assembles a flash-loan atomic bundle — `BORROW` from a lending `protocol` → `REPAY` underwater debt → `SEIZE`
  collateral → `SWAP` → `REPAY` flash loan — executed `ATOMIC_ON_CHAIN`. This is structurally an on-chain lending-
  protocol mechanism; a CEX order book has no external flash-loan seizure opportunity (the exchange's own engine
  matches/settles liquidations internally).
- The 5 CEFI venues the plan's CSV lists as LIQUIDATION_CAPTURE "consumers" (BINANCE-FUTURES, BYBIT,
  COINBASE-FUTURES, KRAKEN-FUTURES, OKX-SWAP) only show up because
  `unified-api-contracts/scripts/generate_venue_work_list.py::_data_type_to_archetypes` keys purely on `data_type`
  name (`liquidations`), not on asset_group or mechanism — the same false-positive shape as this plan's already-
  confirmed `MARKET_MAKING_PREDICTION` finding.
- `archetype_capability_manifest.json` DOES carry one CEFI cell for `LIQUIDATION_CAPTURE` (`hyperliquid`,
  `status: PARTIAL`, `signal_variants: [liquidation_bonus]`, notes: "edge limited to bid-ladder placement near liq
  price") — but this describes a genuinely different mechanism (passive order placement near known liquidation
  price levels, not flash-loan collateral seizure) that has **zero code implementation anywhere** in the engine.
  It is also for `hyperliquid`, not any of the 5 venues this plan batch scoped.

# Why it matters

The capability manifest currently overclaims: it lists a `PARTIAL` CEFI cell for an archetype with no CEFI code
path at all. Building the real bid-ladder mechanism is new strategy/archetype design (quant_dev craft — reads
features, defines new signal logic, a new `on_tick` code path), not a slot-declaration wiring gap a backend_engineer
task can close. Fabricating a CEFI slot entry that reuses the flash-loan engine against a CEX venue would silently
misrepresent capability that doesn't exist — the same "claims success, does nothing" shape this exact plan spent
several P0 todos eliminating (CCXT withdraw stub, cancel/amend stub).

# Recommended decision

CEFI exclusion for `LIQUIDATION_CAPTURE` is confirmed intentional at the current code state — cited in
`strategy-service`'s `archetype_slots_defi.py` LIQUIDATION_CAPTURE entry (strategy-service@f89c6d8235). Two possible
forward paths, tracked as follow-ups rather than done here:

- **[CODE] P3. CANCELLED — SUPERSEDED 2026-08-22 (D89 ruling: downgrade the capability manifest instead of
      building the CEFI variant — cheap, stops the capability manifest overclaiming; the real CEFI bid-ladder
      variant, originally scoped as quant_dev craft, will not be pursued).**
- [ ] [BACKEND] P3. Downgrade `archetype_capability_manifest.json`'s `LIQUIDATION_CAPTURE` CEFI cell (hyperliquid)
      from `PARTIAL` to `BLOCKED`, matching the existing DEFI-perp cell's pattern, so the manifest stops overclaiming
      an unimplemented capability. Per D89 ruling (2026-08-22): downgrade decided — cheap, stops the overclaim.
      Repo: unified-api-contracts.

## Progress Log

- **na-eligibility-audit 2026-08-17 (cefi tranche)** [body-hash:b5bfdc3cca5afe6d]: KEEP-NA, valid — first audit pass (fresh doc, created 2026-08-17, no prior marker). Both open items sit on either side of one undecided build/no-build fork. Item 1 (design + implement a real CEFI LIQUIDATION_CAPTURE variant) GENUINE_WORK — brand-new archetype/signal design, quant_dev craft, not a slot-declaration wiring gap. Item 2 (downgrade the capability manifest's PARTIAL→BLOCKED cell if the variant is never pursued) DEPENDENCY_BLOCKED — mechanically trivial once triggered, but its trigger condition (a decision NOT to pursue item 1) is not yet made; doc frames both paths as still-live options. Doc stays assigned_vm: NA.
- **na-eligibility-audit 2026-08-17 (re-verify, cefi tranche)** [body-hash:dc77ef79f6a7a88a]: KEEP-NA, valid — re-confirmed, hash drift only (no new staleness). Same 2 open items as the first-pass marker above: item 1 GENUINE_WORK (brand-new CEFI archetype/signal design), item 2 DEPENDENCY_BLOCKED (trigger condition — a decision not to pursue item 1 — still unmade). Doc stays assigned_vm: NA.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **2026-08-22 — ruling D89 (CEFI liquidation-capture variant)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Downgrade — cheap, stops the capability manifest overclaiming. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
