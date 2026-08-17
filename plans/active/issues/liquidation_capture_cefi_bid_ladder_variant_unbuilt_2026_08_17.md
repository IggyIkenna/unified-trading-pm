---
doc_type: issue
title: LIQUIDATION_CAPTURE has no CEFI implementation — capability manifest's hyperliquid cell is aspirational-only
created: 2026-08-17
author: worker-slot-11
assigned_vm: NA
source: [/plans/active/cefi_venue_e2e_batch1_2026_08_16.md]
status: open
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
`strategy-service`'s `archetype_slots_defi.py` LIQUIDATION_CAPTURE entry (2026-08-17). Two possible forward paths,
tracked as follow-ups rather than done here:

- [ ] [QUANT_DEV] P3. Design + implement a real CEFI `LIQUIDATION_CAPTURE` variant ("bid-ladder placement near
      liquidation price" per the manifest's hyperliquid note) — either extend `LiquidationCaptureEngine` with a
      CEFI-specific `on_tick` path or split into a new archetype, then add real CEFI slot(s) (repo:
      strategy-service).
- [ ] [BACKEND] P3. If the CEFI bid-ladder variant is never pursued, downgrade
      `archetype_capability_manifest.json`'s `LIQUIDATION_CAPTURE` CEFI cell from `PARTIAL` to `BLOCKED` (matching
      the existing DEFI-perp cell's pattern) so the manifest stops overclaiming an unimplemented capability (repo:
      unified-api-contracts).
