---
name: per-venue-paper-policy
overview: SSOT for the per-venue paper-mode policy — simulate-first floor for every venue (matching engine is the universal fallback); testnet upgrade where API + credentials exist. Codifies `paper_target_registry: dict[chain | venue, target]` in UAC.
type: codex-ssot
status: stub
created: 2026-05-09
locked_by: live-defi-rollout
locked_since: 2026-05-09
spawned_from: plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md
implements_in: plans/active/master_to_live_defi_2026_05_23.md  # Group F items 20.A / 20.B / 20.C
---

# Per-venue paper-mode policy

> **Stub doc.** Full content fills in as `master_to_live_defi_2026_05_23.md` Group F sub-items `pvl-p20a` / `pvl-p20b` /
> `pvl-p20c` ship.

## Policy

**Simulate-first, testnet as fallback / upgrade.** Matching engine is the universal paper-mode floor for every venue
(CeFi spot/perp, DeFi, sports, prediction, TradFi). Where a venue exposes a testnet API + credentials, wire it as an
upgrade path. The matching engine is never absent — testnet is additive.

Rationale: testnet coverage is patchy across the 6 perp venues + chains we trade; the matching engine guarantees
universal paper coverage; testnet upgrades give realistic API conditions where they exist (Settled #3).

## `paper_target_registry` (UAC SSOT)

Codifies the per-target upgrade path:

```python
# unified_api_contracts/internal/paper_target_registry.py — NEW

PAPER_TARGET_REGISTRY: Mapping[ChainOrVenue, PaperTarget] = {
    # EVM chains — Tenderly Virtual TestNet fork
    "ethereum": PaperTarget.TENDERLY_FORK,
    "arbitrum": PaperTarget.TENDERLY_FORK,
    "base":     PaperTarget.TENDERLY_FORK,
    "polygon":  PaperTarget.TENDERLY_FORK,

    # Solana — non-EVM, no Tenderly; pick devnet / localnet / surfnet per fork-state semantics
    "solana": PaperTarget.SOLANA_DEVNET,  # or LOCALNET / SURFNET — TBD per pvl-p20c

    # CeFi perp venues — testnet where viable, simulate otherwise
    "deribit":     PaperTarget.DERIBIT_TESTNET,    # known viable per existing venues/deribit.py
    "bybit":       PaperTarget.MATCHING_ENGINE,    # audit pending per pvl-p20b
    "binance":     PaperTarget.MATCHING_ENGINE,    # audit pending per pvl-p20b
    "okx":         PaperTarget.MATCHING_ENGINE,    # audit pending per pvl-p20b
    "hyperliquid": PaperTarget.MATCHING_ENGINE,    # audit pending per pvl-p20b
    "aster":       PaperTarget.MATCHING_ENGINE,    # audit pending per pvl-p20b

    # Sports — PaperBettingAdapter (canonical simulator example)
    "betfair":     PaperTarget.PAPER_BETTING_ADAPTER,
    "matchbook":   PaperTarget.PAPER_BETTING_ADAPTER,

    # Prediction — matching-engine simulation
    "polymarket":  PaperTarget.MATCHING_ENGINE,
    "kalshi":      PaperTarget.MATCHING_ENGINE,
}

# Default fallback for any unmapped target: PaperTarget.MATCHING_ENGINE
```

The `PaperTarget` enum closed set:
- `MATCHING_ENGINE` — execution-service matching engine simulates fills.
- `TENDERLY_FORK` — EVM Virtual TestNet fork (per `flash-loan-receiver.md`).
- `SOLANA_DEVNET` (or `SOLANA_LOCALNET` / `SOLANA_SURFNET` per `pvl-p20c` audit).
- `DERIBIT_TESTNET` — Deribit's testnet API endpoint.
- `<VENUE>_TESTNET` — additive per-venue as `pvl-p20b` audit completes.
- `PAPER_BETTING_ADAPTER` — sports `PaperBettingAdapter` (already shipped).

## Per-asset_group rules

### CeFi (spot + perp)

Simulate via L2 CeFi matcher by default. Testnet upgrade per `paper_target_registry` where the venue exposes one.
Audit `pvl-p20b` enumerates which of the 5 unwired perp venues (Bybit / Binance / OKX / Hyperliquid / Aster) actually
expose testnets the workspace can use.

### DeFi (EVM)

Tenderly fork is the canonical paper target for every EVM chain we trade. Per chain → fork URL via
`unified_api_contracts/canonical/registry/capability_declarations/_defi.py:CHAIN_RPC_TEMPLATES` (extended to carry
`fork_url` alongside `live_rpc_url`).

### DeFi (Solana / non-EVM)

Solana devnet is the working default for `carry_staked_basis` jitoSOL / mSOL / bSOL legs. Localnet / surfnet remain
options if devnet's fork-state semantics prove insufficient. Pyth via Hermes for prices (already unbanned 2026-05-06).
Same per-chain rule extends to any future non-EVM chain (Sui, Aptos, etc.) — use the chain's native testnet/fork
primitive.

### Sports

`PaperBettingAdapter` ships at
`execution-service/execution_service/sports_execution/adapters/paper/paper_betting.py` with full bet placement /
cancellation / settlement simulation. Canonical simulator example for the workspace; the L0 Sports TOB matcher composes.

### Prediction

Matching-engine simulation only — Polymarket / Kalshi don't expose testnets we can use. The matching engine respects
per-market lifecycle bounds (`market_created_at` / `resolution_time` / `settlement_time` per
`predictions_master_2026_05_07.md`).

### TradFi

Matching-engine simulation against historical Databento data. CME doesn't offer a viable workspace-facing testnet for
paper-mode. Real-time TradFi paper would be matching-engine against live tick stream.

## Credentials

Per-venue paper credentials (testnet API keys + Tenderly tokens + Solana devnet wallets) live in a separate Secret
Manager namespace from live keys. Exact path scoping in
[`api_keys_wallets_accounts_readiness_2026_05_08.md`](../../plans/questions/api_keys_wallets_accounts_readiness_2026_05_08.md);
banner mutual.

## Composes with

- [`../04-architecture/operational-modes.md`](../04-architecture/operational-modes.md) — the canonical mode SSOT.
- [`../04-architecture/paper-vs-live-execution-seam.md`](../04-architecture/paper-vs-live-execution-seam.md) — pins the
  execution-only seam.
- [`../04-architecture/flash-loan-receiver.md`](../04-architecture/flash-loan-receiver.md) — Aave V3 flash loan deployment
  validates `connect()` against fork; same shape extends to Tenderly fork validation.
- [`../04-architecture/chain-environment-resolution.md`](../04-architecture/chain-environment-resolution.md) — per-chain
  RPC + fork URL resolution.
