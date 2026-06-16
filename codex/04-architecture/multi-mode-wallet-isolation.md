---
scope: [engineer, admin]
title: Multi-Mode Wallet Isolation — Paper + Live on Shared Wallet
updated: 2026-05-15
owner: topology_qgroup_gap_closure_2026_05_09 Phase 4
closes: GAP-13
last_reviewed: 2026-05-17
---

# Multi-Mode Wallet Isolation

## Decision (2026-05-15)

**Selected approach: virtual ledger overlay (Option B)**

When paper and live modes run simultaneously on the same wallet, position-balance-monitor (PBMS) tracks paper positions
off-chain via a virtual ledger overlay. On-chain positions belong exclusively to the live mode. Paper positions are
accounted in PBMS memory + emitted as `CanonicalPosition` records tagged `mode=paper`.

**Rationale for Option B over Option A (separate sub-accounts)**:

- May-23 target venues (Binance, Bybit, OKX) all support sub-accounts, but provisioning + permission setup takes 3-5
  business days per venue — too late for May-23.
- Virtual ledger works on any venue without new account provisioning.
- Off-chain paper position tracking is auditable: every `CanonicalPosition(mode=paper)` record is written to BigQuery
  with the same schema as live fills, enabling post-hoc parity analysis.

**Post-cutover (June+)**: migrate to sub-account isolation (Option A) once provisioning is complete. Sub-accounts give
cleaner on-chain audit trails and simplify margin attribution.

## Implementation Contract

### CanonicalPosition mode tag

`CanonicalPosition.mode` (str): `"live"` | `"paper"`. PBMS writes all positions with the `mode` field set. Downstream
consumers (risk service, analytics) MUST filter by mode before aggregating exposure.

### PBMS split rule

PBMS maintains two independent position ledgers per instrument per venue:

- `_live_positions: dict[str, Decimal]` — derived from real fills (CanonicalFill stream)
- `_paper_positions: dict[str, Decimal]` — derived from simulated fills (BatchMatchingEngine output)

Live and paper ledgers MUST NOT be summed together. Any code path that aggregates positions without a mode filter is a
correctness bug.

### Fill routing

| Fill source                                     | Destination ledger | Mode tag on CanonicalPosition |
| ----------------------------------------------- | ------------------ | ----------------------------- |
| Live exchange (CanonicalFill via venue adapter) | `_live_positions`  | `"live"`                      |
| BatchMatchingEngine (simulated fill)            | `_paper_positions` | `"paper"`                     |

### Risk service

Risk-and-exposure service queries PBMS with `mode` filter. The carry_staked_basis live archetype queries `mode=live`
only. Paper archetype queries `mode=paper` only. Operator dashboards show both, labelled.

### Margin attribution

Live margin is computed from `_live_positions` only. Paper archetype has no real margin impact — PBMS returns
`margin_used=Decimal("0")` for all paper positions. This simplifies margin accounting: the live archetype owns 100% of
actual margin.

## Integration Test Gate

`execution-service/tests/integration/test_multi_mode_wallet_isolation.py` MUST:

1. Inject two fills for the same instrument: one from the live fill stream, one from BatchMatchingEngine
2. Assert PBMS `_live_positions` contains only the live fill delta
3. Assert PBMS `_paper_positions` contains only the simulated fill delta
4. Assert `CanonicalPosition(mode="live")` and `CanonicalPosition(mode="paper")` are emitted separately
5. Assert live margin attribution excludes paper positions

This test gates the May-23 carry-live + funding-arb-paper ramp. Without green, the dual-mode launch is blocked.

## Post-Cutover Migration Path

After June-1 sub-account provisioning:

1. Provision sub-accounts at each venue (Binance `PAPER_<strategy_id>`, Bybit `PAPER_<strategy_id>`)
2. PBMS switches to reading real sub-account balances for paper mode instead of virtual ledger
3. Virtual ledger is retired; `_paper_positions` dict removed
4. `CanonicalPosition.mode` field remains — now sourced from sub-account label

Migration plan to be written when sub-account provisioning completes.
