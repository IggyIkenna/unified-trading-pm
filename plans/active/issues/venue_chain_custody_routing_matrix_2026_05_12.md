---
title: "Venue × deposit-chain × custody-routing matrix — missing dimension blocking cutover funds-flow"
created: 2026-05-12
author: ikenna-main-slot1
source:
  - unified-api-contracts/internal/domain/execution_service/transfer_types.py
  - unified-api-contracts/registry/market_data_categories.py
  - plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md Phase 3.B + 4.A
  - plans/active/cross_asset_group_catalogue_audit_2026_05_10.md
locked_by: live-defi-rollout
locked_since: 2026-05-12
---

# Venue × deposit-chain × custody-routing matrix — missing dimension

> **Severity**: P0 — blocks May-23 cutover funds-flow design. Classification (cefi vs defi vs on-chain CLOB) alone is
> insufficient; per-venue per-chain deposit/withdraw + custody-routing must be captured + codified.
> **Suggested owner**: Ikenna slot 4 (api_keys_wallets context) + Ikenna slot 8 (cross_asset audit overlap).
> Cross-side to Harsh slot 4 (defi_simulation_realism implementation has overlap on venue connectors).

## What I found

Operator surfaced 2026-05-12 ~07 GMT: regardless of `VENUES_BY_ASSET_GROUP` classification (cefi vs defi), each venue
has 2 orthogonal operational dimensions that the current registry **doesn't capture**:

1. **Per-chain deposit/withdraw routing** — which chains can each venue accept deposits/withdrawals on?
   - Binance: USDC accepts on ETH / Polygon / BSC / Solana / Arbitrum / Base / Avalanche / TRC20 / ... (10+ chains)
   - Hyperliquid: USDC accepts on Arbitrum only (Hyperliquid native chain)
   - Aster: USDC accepts on BSC only
   - GMX-V2: USDC accepts on Arbitrum only
   - DRIFT: USDC accepts on Solana only
   - Pacifica: USDC accepts on Solana only
   - AAVE_V3 / Uniswap / Curve: per-chain native (Ethereum / Arbitrum / Base / Optimism / Polygon / Avalanche / BSC / Linea)

2. **Custody-routing model per venue** — how does the client fund the venue?
   - **(A) Direct venue wallet** (prop trading; client owns account credentials; deposits land in venue-managed wallet)
   - **(B) ClearLoop** (Binance, OKX subset; off-exchange settlement; LedgerEdge / Copper acts as settlement layer)
   - **(C) CEFFU MirrorX** (Binance, Bybit, OKX; off-exchange settlement with CEFFU custody pre-trade; non-custodial)
   - **(D) Copper sub-account** (multi-venue; client funds in Copper, sub-account routes to venue)
   - **(E) Fireblocks** (multi-venue; client funds in Fireblocks vault, MPC signing per venue)

## What exists today

- `unified_api_contracts/internal/domain/execution_service/transfer_types.py` has `VENUE_WALLET_CAPABILITIES` dict with
  `custody_provider` field (single string: `"copper"` / `"fireblocks"` / `""`). **Insufficient**: missing per-chain
  deposit routing; missing ClearLoop / CEFFU custody patterns; single-string custody_provider doesn't capture
  per-venue routing differences.
- `unified_api_contracts/registry/market_data_categories.py` `VENUES_BY_ASSET_GROUP` is the classification dimension
  (cefi / defi / tradfi / sports / prediction). **Insufficient**: doesn't address per-chain or custody routing.
- `WalletProvisioningConfig` (UAC@`d721b6a`, slot 4 shipped 2026-05-12) has `signing_surface` (CLOUD_KMS_ENCRYPTED /
  COPPER_MPC / FIREBLOCKS_MPC) + `chain` + `allowed_protocols` — **good for DeFi wallet provisioning** but doesn't
  cover cefi venue funding routing.

## Why it matters

For May-23 cutover funds-flow:

- **Funding moves**: client deposits → venue trading wallet. Need to know exact chain + custody path.
- **Withdrawal moves**: venue → client custody → next venue. Same routing data.
- **PnL attribution**: per-venue, per-chain reconciliation needs the deposit-chain matrix.
- **Treasury rebalancing**: cross-venue funding moves rely on accurate per-venue per-chain support.
- **Risk surface**: each custody path has different counterparty risk (ClearLoop = LedgerEdge/Copper; CEFFU MirrorX = CEFFU; direct = venue insolvency).

Master plan G19 item ("Treasury / custody integration: Copper for DeFi, CEFFU for Binance") names CEFFU + Copper but
not ClearLoop. Item is `manual` continuous-verification + `Last verified: NEVER`. Needs the matrix to flip.

## Recommended decision (3 sub-items)

**Item 1 — Schema extension** (UAC slot 4):
Extend `VenueWalletCapabilities` (or NEW dataclass `VenueFundsRoutingCapabilities` if cleaner separation) with:

```python
@dataclass(frozen=True)
class VenueFundsRoutingCapabilities:
    venue: str
    deposit_chains: frozenset[str]              # {"ETHEREUM", "ARBITRUM", "BSC", ...}
    withdrawal_chains: frozenset[str]           # usually == deposit_chains; explicit for asymmetry
    custody_routing: tuple[CustodyRoute, ...]   # ordered preference; first = primary
    deposit_address_per_chain: dict[str, str]   # operator-filled post-onboarding
```

```python
class CustodyRoute(StrEnum):
    DIRECT_VENUE_WALLET = "direct_venue_wallet"   # prop trading
    CLEARLOOP = "clearloop"                       # off-exchange settlement via LedgerEdge/Copper
    CEFFU_MIRRORX = "ceffu_mirrorx"               # off-exchange settlement via CEFFU
    COPPER_SUB_ACCOUNT = "copper_sub_account"     # multi-venue custody via Copper
    FIREBLOCKS = "fireblocks"                     # multi-venue custody via Fireblocks
```

**Item 2 — Per-venue routing matrix** (slot 8 audit + slot 4 schema fill):
For all 15+ venues in `VENUES_BY_ASSET_GROUP`, fill in:
- BINANCE-SPOT / BINANCE-FUTURES: deposit_chains = {ETH/Polygon/BSC/Solana/Arbitrum/Base/Avalanche/TRC20}; custody = (DIRECT_VENUE_WALLET, CLEARLOOP, CEFFU_MIRRORX)
- BYBIT: deposit_chains = {ETH/Polygon/BSC/Solana/Arbitrum/Avalanche}; custody = (DIRECT_VENUE_WALLET, CEFFU_MIRRORX, COPPER_SUB_ACCOUNT)
- OKX: deposit_chains = {ETH/Polygon/BSC/Solana/Arbitrum/Avalanche/TRC20}; custody = (DIRECT_VENUE_WALLET, COPPER_SUB_ACCOUNT)
- DERIBIT: deposit_chains = {ETH/BTC}; custody = (DIRECT_VENUE_WALLET, COPPER_SUB_ACCOUNT)
- HYPERLIQUID: deposit_chains = {ARBITRUM}; custody = (DIRECT_VENUE_WALLET via Copper signing — already in registry)
- ASTER: deposit_chains = {BSC}; custody = (DIRECT_VENUE_WALLET via Copper)
- GMX-V2: deposit_chains = {ARBITRUM}; custody = (DIRECT_VENUE_WALLET via Copper)
- DRIFT: deposit_chains = {SOLANA}; custody = (DIRECT_VENUE_WALLET via Copper)
- AAVE_V3 / UNISWAP_V3 / etc: deposit_chains per-protocol (Ethereum / Arbitrum / Base / Optimism / Polygon / etc); custody = (FIREBLOCKS, COPPER_SUB_ACCOUNT)

Need operator-input on which custody routes we actually use per venue for May-23 (prop trading vs ClearLoop vs CEFFU vs Copper). Slot 4 has Copper KYB Day-1 in flight; CEFFU is longest lead time per Phase 3.B; ClearLoop not in current plan.

**Item 3 — Master plan G19 + new G24** (slot 1 main):
Group F item 19 "Treasury / custody integration" currently names "Copper for DeFi, CEFFU for Binance". Extend to:
- Per-venue custody route declared in registry (Item 1+2)
- ClearLoop included as 3rd path option
- Add G24 "Per-venue deposit-chain matrix" with `Last verified` cadence; QG-enforced.

## Operator decisions needed

1. **Which custody routes do we actually use for May-23?**
   - (a) Prop-trading only — direct venue wallets across all cefi; Copper for DeFi
   - (b) Mixed — Copper sub-account for cefi multi-venue + direct for venues without Copper support; Copper for DeFi
   - (c) CEFFU MirrorX for Binance/Bybit + Copper sub-account for OKX/Deribit + Copper for DeFi (operator's earlier mention)
   - (d) Full custody — all venues through Copper or Fireblocks; no direct
2. **ClearLoop included for May-23 or post-cutover?** — longest lead time per Phase 3.B; CEFFU pattern; likely post-cutover.
3. **Per-venue per-chain deposit-address provisioning timing** — operator-action: which chains pre-cutover; which post.

## Composes with

- `api_keys_wallets_accounts_readiness_2026_05_10.md` Phase 3.B (CEFFU) + Phase 4.A (per-chain wallet) — schema extension lands here
- `cross_asset_group_catalogue_audit_2026_05_10.md` — venue audit dimension extension
- `master_to_live_defi_2026_05_23.md` Group F item 19 — readiness criteria extension
