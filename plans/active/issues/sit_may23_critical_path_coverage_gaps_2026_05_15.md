---
title: "SIT May-23 Critical Path Coverage Gaps"
created: 2026-05-15
author: slot-8
source:
  - system-integration-tests/tests/scenarios/defi_scenarios.py
  - system-integration-tests/tests/overnight/test_archetype_cascade.py
  - system-integration-tests/tests/
locked_by: live-defi-rollout
---

## What I found

Audited SIT test suite (29 test files across smoke/unit/e2e/scenarios/overnight/performance/real_flow tiers) against the
May-23 critical path matrix (DeFi paper carry + DeFi paper APD + mode-switch live/batch).

**Existing DeFi scenario playbooks** (`tests/scenarios/defi_scenarios.py`) cover only infrastructure-level events:

- `defi_gas_spike` — gas price surge blocking transactions
- `defi_slippage_beyond_threshold` — DEX swap excessive slippage
- `defi_mev_attack` — MEV sandwich attack
- `defi_chain_reorg` — block reorganisation
- `defi_oracle_failure` — Chainlink oracle stale price

**Not present** — zero scenario playbooks or test functions for:

| Critical Path                                        | Required for May-23 | Gap                                                                                                   |
| ---------------------------------------------------- | ------------------- | ----------------------------------------------------------------------------------------------------- |
| `carry_staked_basis` paper mode (DeFi)               | YES — Gate A1       | ❌ No scenario                                                                                        |
| `arbitrage_price_dispersion` (APD) paper mode (DeFi) | YES — Gate A2       | ❌ No scenario                                                                                        |
| Mode-switch `paper_1d` → `live_early` gate           | YES — Gate G        | ❌ No scenario                                                                                        |
| Batch-live parity smoke (DeFi paths)                 | YES — Gate F        | ⚠️ `test_archetype_cascade.py` covers contract level only (hash parity, not DeFi-specific order flow) |

**Overnight test**: `test_archetype_cascade.py` parameterizes over UAC ASSET_GROUP_ONTOLOGY and verifies:

- State hash determinism across re-runs (batch=live parity at contract level)
- MockExecutionAlwaysFill drives one synthetic order per cell

This covers the structural contract but NOT the DeFi-specific pipeline flow: LST rates → features-onchain → strategy →
execution → PBM manifest assertion.

## Why it matters

May-23 gate requires "two DeFi archetypes live on a real wallet ≥7 days" — the SIT layer is the last automated gate
before paper → live_early promotion. Without scenario coverage for `carry_staked_basis` and `APD` paper mode, the CI
gate is missing for the most critical pre-promotion check.

Gate G (mode-switch `paper_1d` → `live_early`) has no automated test at all — a human must manually verify the promote
flow works end-to-end with each promotion.

## Recommended decision

Add 3 scenario playbooks to SIT:

1. **`defi_carry_staked_basis_paper`** — scenario: fetch LST rates (Lido/RocketPool/Aave) → strategy generates carry
   signal → execution mock fills → manifest shows `captured` rows for carry data types. Assertions: signal direction
   non-zero, fill count ≥1, manifest status `captured`.

2. **`defi_apd_paper`** — scenario: fetch DEX prices (Uniswap V3 vs Curve) + CEX marks → strategy generates APD signal →
   execution mock fills. Assertions: spread non-zero, no SKIP on DeFi error, manifest `captured`.

3. **`defi_paper_to_live_early_gate`** — scenario: MinimalCandidateManifest created → promote endpoint called → paper VM
   launch event emitted → DART gate present for first 3 days. Assertions: promote returns 200, VM event STARTED emitted,
   DART gate blocking live fills for day 1-3.

These can be added to `tests/scenarios/defi_scenarios.py` + wired into `tests/overnight/test_archetype_cascade.py` as
additional parametrized cells, or as a new `tests/scenarios/test_may23_critical_paths.py`.

**Severity**: BLOCKER for May-23 gate if CI gate is required for paper → live_early promotion. **Owner**: SIT +
strategy-service team **Estimated effort**: 1-2 AI-days per scenario (3 scenarios = 4-5 AI-days)
