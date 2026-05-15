---
title: COMPOUND_V3 + KAMINO lending_rates adapter data gaps — NaN borrow_apy and Solana missing
created: 2026-05-15
author: ikenna-slot-3
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

- Solana LST (JitoSOL) only has ~monthly cadence in lst-rates bucket (separate gap, Helius BLOCKED-CREDENTIALS)
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
- Requires Helius RPC key for Solana data access (existing BLOCKED-CREDENTIALS ping)
- Status: `BLOCKED-CREDENTIALS` — see existing Solana LST gap ping

## Action items for orchestrator

- [ ] [OPERATOR-DECISION] Confirm COMPOUND_V3 fix priority: which Comet markets to target first?
- [ ] [BLOCKED-CREDENTIALS] KAMINO blocked on Helius RPC key (see solana_defi_coverage_gaps_2026_05_13.md)
