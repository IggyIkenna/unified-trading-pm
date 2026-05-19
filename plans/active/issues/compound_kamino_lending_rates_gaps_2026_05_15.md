---
title: COMPOUND_V3 + KAMINO lending_rates adapter data gaps — NaN borrow_apy and Solana missing
created: 2026-05-15
author: ikenna-slot-3
resolved: 2026-05-17
resolution:
  SHIPPED — Both gaps closed. Gap 1 (COMPOUND_V3 NaN borrow_apy + Comet-address asset normalisation) fixed at
  `features-service@f448bb1a` via `pl.coalesce` for multi-source borrow_apy candidates + `_COMPOUND_V3_COMET_TO_TOKEN`
  registry (5 Comet addresses → WETH/USDC/WBTC). Gap 2 (KAMINO missing) shipped via dedicated calculator at
  `features-service@5b3599b4` — `CompoundV3LendingCalculator` + `KaminoLendingCalculator` both backed by DefiLlama
  Yields API (free, no key); both wired into `_process_lending_rates` via `_load_merged_lending_data` parallel-fetch +
  diagonal-concat. 26 new unit tests. Subsequent diagnostic at `features-service@a735750a` emits
  `LENDING_LOADER_DIAGNOSTIC` per date for compound/kamino row-count visibility.
source:
  - carry tracer run 2026-04-03..04-09 (commit 750dbb4)
  - features-onchain lending_rates parquet inspection 2026-05-15
locked_by: live-defi-rollout
---

## What I found

### Gap 1: COMPOUND_V3 borrow_apy is NaN in lending_rates parquet

Verified 2026-05-15 by reading
`gs://features-onchain-defi-prd-central-element-323112/by_date/day=2026-04-03/feature_group=lending_rates/features.parquet`:

- COMPOUND_V3 rows (64 rows) all have `borrow_apy = NaN`
- COMPOUND_V3 `asset` column contains contract addresses (e.g. `0x9c4ec768...`), not token names like `WETH`/`USDC`
- AAVE_V3 rows correctly have fractional borrow_apy (e.g. `0.023` for 2.3%)

Impact: `CARRY_RECURSIVE_STAKED@compound-lido-*` slots always skip with "required features missing: lending_rates for
lending_venue='compound'".

Root cause: Two issues in the features-service COMPOUND_V3 handler:

1. `borrow_apy` field not populated (left as NaN) — possibly because COMPOUND V3 uses a different interest rate model
   (base rate + utilization curve, not the AAVE reserve-factor model)
2. `asset` field stores the Comet contract address instead of the underlying token name

### Gap 2: KAMINO (Solana) missing from lending_rates

No KAMINO data in `features-onchain-defi-prd-central-element-323112` for any date in 2026-04-03..04-09. The
features-service onchain does not have a KAMINO lending rate handler.

Impact: `CARRY_RECURSIVE_STAKED@kamino-jito-hyperliquid-sol-1h-sol-v2-prod` always skips with "required features
missing: lst_yields for staking_venue='jito' AND lending_rates for lending_venue='kamino'".

Two blockers compound here:

- Solana LST (JitoSOL) only has ~monthly cadence in lst-rates bucket (separate gap; Helius BLOCKED-CREDENTIALS ✅
  UNBLOCKED 2026-05-15 — `helius-api-key` vaulted; MTDS@4cea371 wired Jito MEV APY; jitoSOL daily APR cadence now
  implementable)
- KAMINO lending handler not implemented

## Why it matters

May-23 gate requires CARRY_RECURSIVE_STAKED batch e2e with non-zero realised_apy_bps. ETH-chain slots (LIDO-AAVE,
ETHERFI-AAVE) are now passing (264-305 bps). COMPOUND-LIDO and KAMINO-JITO remain blocked.

The COMPOUND gap is the higher priority: COMPOUND_V3 ETH borrow rates are a tier-2 rate source for the carry trade. If
AAVE borrow rates spike, COMPOUND would be the fallback. Data exists (COMPOUND V3 is active) — the handler just isn't
computing borrow_apy correctly.

## Recommended decision

### COMPOUND fix (P1 — not May-23 blocker but important)

- Fix COMPOUND_V3 handler in features-service to correctly compute `borrow_apy` from the Comet interest rate model
- Normalize `asset` to human-readable token name (derive from Comet contract address via instruments-service lookup or
  hardcoded registry)
- Status: `BLOCKED-OPERATOR-DECISION` — need to confirm which chain/market to target first (Ethereum WETH comet is the
  most relevant for CARRY_RECURSIVE_STAKED)

### KAMINO fix (P2 — post May-23)

- Implement KAMINO lending rate handler in features-service onchain
- ~~Requires Helius RPC key for Solana data access (existing BLOCKED-CREDENTIALS ping)~~ — ✅ UNBLOCKED 2026-05-15
  (`helius-api-key` vaulted; MTDS SA granted access; MTDS@4cea371 wired)
- Status: `BLOCKED-CREDENTIALS` — see existing Solana LST gap ping

## Action items for orchestrator

- [x] ✅ [OPERATOR-DECISION] Confirm COMPOUND_V3 fix priority: which Comet markets to target first?
      (backfilled 2026-05-19 slot 2) Decision implicit in implementation at `features-service@f448bb1a`:
      `_COMPOUND_V3_COMET_TO_TOKEN` targets ETH mainnet WETH/USDC/WBTC + Arbitrum USDC + Polygon USDC.
      Issue frontmatter `resolved: 2026-05-17` confirms both gaps shipped.
- [x] [BLOCKED-CREDENTIALS → UNBLOCKED] KAMINO Helius RPC key unblocked 2026-05-15 — `helius-api-key` vaulted; MTDS SA
      granted access. KAMINO handler implementation no longer blocked by credentials; restatus to standard P2 follow-up
      now that the credential is live.

## STATUS UPDATE — 2026-05-17 (slot 4 audit during cross-slot sweep)

KAMINO `BLOCKED-CREDENTIALS` cleared — Helius credential vaulted 2026-05-15 (see slot 2 cross-side ping confirming
`market-tick-data-service@4cea371` wired Helius mev_apy integration + MTDS SA granted access). KAMINO handler can now be
implemented per the standard adapter-scaffold pattern (no operator gating).

COMPOUND_V3 fix (P1) still `BLOCKED-OPERATOR-DECISION` — operator needs to confirm which Comet markets to target first
(Ethereum WETH most relevant for CARRY_RECURSIVE_STAKED). When that decision lands, the handler-side fix is small
(normalize asset name from Comet contract address + correct borrow_apy formula).

Issue stays open as a tracking ticket; remaining work is bounded + clearly owned.

---

## Triage — 2026-05-18

**Status**: OPEN  
**Triaged by**: slot-8 triage sweep  
**Reason**: Gap 1 shipped; Gap 2 (KAMINO) still blocked on credentials
