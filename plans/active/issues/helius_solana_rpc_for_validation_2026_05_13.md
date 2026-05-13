---
title: Add Helius Solana RPC for Phase 2 SOLANA_CLMM + SOLANA_AMM golden-fixture capture
created: 2026-05-13
author: ikenna-slot-6
source:
  - plans/active/defi_simulation_realism_2026_05_10.md (Phase 2F SOLANA_CLMM + SOLANA_AMM)
  - execution-service/scripts/capture_golden_swaps.py (DEFERRED-SOLANA branch in agent close-out 2026-05-13)
locked_by: live-defi-rollout
locked_since: 2026-05-13
severity: P1
suggested_owner: operator (Helius signup + key provisioning) → slot 6 (wire into capture script)
---

## What I found

Phase 2 AMM golden-fixture validation harness (`execution-service/scripts/capture_golden_swaps.py` shipped at
`626d4c8af`) covers all Ethereum-mainnet shapes (V3 / V2 / Curve / Balancer / Solidly) using the workspace Alchemy key.
**Solana shapes (`SOLANA_CLMM` Raydium+Orca, `SOLANA_AMM` Raydium V4) are NOT captured** — Alchemy's standard plan only
covers Ethereum + L2s, not Solana mainnet.

The matchers (`execution-service/execution_service/matching_engine/solana_clmm.py:SolanaCLMMPool` + `SolanaAMMPool`)
already exist and pass synthetic unit tests. The gap is real on-chain swap-event corpora for the golden fixture, which
requires an archive-capable Solana RPC.

## Why it matters

- **Coverage gap**: Phase 2 codex matrix targets ≥30 swaps per shape (Raydium ≥ 30, Orca ≥ 30). Without real-data
  validation, we have no on-chain ground truth for `SolanaCLMMPool` / `SolanaAMMPool` matchers.
- **May-23 cutover**: `arbitrage_price_dispersion` archetype includes Solana DEX legs. Validating the matchers against
  real on-chain swaps is a prerequisite to trusting their fill simulation.
- **Adjacent unblocks**: same Helius access unblocks Pyth/Solana price-feed adapter work + DRIFT/Jupiter venue work in
  other plans.

## Recommended decision

**Two-step provisioning** (operator-confirmed 2026-05-13):

1. **Free tier today** — sign up at `https://helius.dev`; 100k credits/day + 10 RPS + archive history. Sufficient for a
   one-shot golden capture of ~30 swaps per Solana shape (≈ 200 RPC calls total). Store key in GCP Secret Manager as
   `helius-api-key`.
2. **Upgrade to Developer ($49/mo)** once we move to recurring weekly validation + light production polling. Gives 10M
   credits/mo + 50 RPS.

After key provisioning:

- Add `HELIUS_API_KEY` to the lending-rate + amm-golden VM launchers (alongside Alchemy key).
- Extend `capture_golden_swaps.py` to dispatch to Helius RPC for SOLANA_CLMM + SOLANA_AMM shapes (per-shape
  `_get_archive_client(pool_shape)` factory; reuse the per-swap slot-1 snapshot pattern).
- Capture ≥30 swaps from Raydium SOL/USDC CLMM + Orca SOL/USDC Whirlpool + Raydium V4 standard pool.
- Flip Phase 2F SOLANA fixtures `**DEFERRED-SOLANA**` → `[x] real-corpora` in defi_simulation_realism plan.

**Out of scope here**: Pyth price-feed adapter (separate plan path); Jupiter quote API (covered by Phase 2G already).

## Execution metadata

```yaml
execution:
  owner: operator (signup) → slot 6 (wire-in) → amm-golden VM launcher (recurring validation)
  cadence: one-shot for golden capture; weekly thereafter via amm-golden-solana-* VM
  verifier:
    pass-rate ≥ 90% within 10 bps per Solana shape; stored at
    gs://central-element-323112-defi-validation/results/amm/<date>/solana_*/
  last_executed: NEVER
```
