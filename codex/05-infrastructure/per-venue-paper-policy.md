---
scope: [engineer, admin]
name: per-venue-paper-policy
overview:
  "SSOT for the per-venue paper-mode policy — simulate-first floor for every venue (matching engine is the universal
  fallback); testnet upgrade where API + credentials exist. Codifies PAPER_EXECUTION_TARGETS in UAC."
type: codex-ssot
status: active
created: 2026-05-09
updated: 2026-05-15
last_reviewed: 2026-05-17
locked_by: live-defi-rollout
locked_since: 2026-05-09
spawned_from: plans/questions/paper_vs_live_workflow_maturity_2026_05_08.md
implements_in: plans/active/master_to_live_defi_2026_05_23.md # Group F items 20.A / 20.B / 20.C
---

# Per-venue paper-mode policy

> **pvl-p20a shipped 2026-05-14** (`unified_api_contracts/internal/paper_execution_targets.py`). **pvl-p20b audit
> shipped 2026-05-15** (below). **pvl-p20c shipped 2026-05-15**
> (`execution-service/execution_service/defi_execution/protocols/solana_lst_devnet.py`).

## Policy

**Simulate-first, testnet as fallback / upgrade.** Matching engine is the universal paper-mode floor for every venue
(CeFi spot/perp, DeFi, sports, prediction, TradFi). Where a venue exposes a testnet API + credentials, wire it as an
upgrade path. The matching engine is never absent — testnet is additive.

Rationale: testnet coverage is patchy across the 6 perp venues + chains we trade; the matching engine guarantees
universal paper coverage; testnet upgrades give realistic API conditions where they exist (Settled #3).

## `PAPER_EXECUTION_TARGETS` (UAC SSOT)

Shipped at `unified_api_contracts/internal/paper_execution_targets.py` (pvl-p20a, 2026-05-14). Import:
`from unified_api_contracts.internal import PAPER_EXECUTION_TARGETS, get_paper_target`.

```python
# Canonical registry — ExecutionTarget values
PAPER_EXECUTION_TARGETS: dict[str, ExecutionTarget] = {
    # EVM chains — Tenderly fork
    "ethereum": ExecutionTarget.FORK,
    "arbitrum": ExecutionTarget.FORK,
    "base":     ExecutionTarget.FORK,
    ...

    # Solana — devnet (pvl-p20c wires connector)
    "solana": ExecutionTarget.TESTNET,

    # CeFi perp venues — testnet endpoints (see audit table below)
    "DERIBIT":     ExecutionTarget.TESTNET,
    "BINANCE":     ExecutionTarget.TESTNET,
    "BYBIT":       ExecutionTarget.TESTNET,
    "OKX":         ExecutionTarget.TESTNET,
    "HYPERLIQUID": ExecutionTarget.TESTNET,
    "KRAKEN":      ExecutionTarget.TESTNET,

    # Sports + Prediction — simulation
    "BETFAIR":    ExecutionTarget.SIMULATION,
    "POLYMARKET": ExecutionTarget.SIMULATION,
    ...
}

def get_paper_target(chain_or_venue: str) -> ExecutionTarget:
    return PAPER_EXECUTION_TARGETS.get(chain_or_venue, ExecutionTarget.SIMULATION)
```

`ExecutionTarget` enum (UAC `internal/modes.py`): `MAINNET` | `TESTNET` | `FORK` | `SIMULATION`.

## pvl-p20b: CeFi perp venue testnet audit (2026-05-15)

Audited 5 venues without testnet routing before pvl-p20b. Deribit already fully wired (not in scope).

| Venue           | UAC testnet URL                                         | Auth mechanism                   | Execution-service adapter                      | Wiring status                                 |
| --------------- | ------------------------------------------------------- | -------------------------------- | ---------------------------------------------- | --------------------------------------------- |
| **Binance**     | `https://testnet.binance.vision`                        | HMAC-SHA256 (`api_key`)          | None in `venues/` — NautilusTrader abstraction | PENDING — adapter needed                      |
| **Bybit**       | `https://api-testnet.bybit.com`                         | HMAC-SHA256 (`api_key`)          | None in `venues/`                              | PENDING — adapter needed                      |
| **OKX**         | `https://www.okx.com` + `x-simulated-trading: 1` header | HMAC-SHA256 (`api_key`)          | None in `venues/`                              | PENDING — adapter needed                      |
| **Hyperliquid** | `https://api.hyperliquid-testnet.xyz`                   | L1 action signing (`api_wallet`) | `venues/hyperliquid.py` exists                 | **WIRED** — `testnet: bool` added in pvl-p20b |
| **Aster**       | `https://testnet-api.aster.finance`                     | HMAC-SHA256                      | None in `venues/`                              | PENDING — adapter needed                      |

**Hyperliquid wiring** (pvl-p20b, 2026-05-15): `HyperliquidConnector(testnet=True)` routes to testnet endpoint.
`PAPER_EXECUTION_TARGETS["HYPERLIQUID"] = ExecutionTarget.TESTNET` is already set.

**Pending 4 venues** (Binance/Bybit/OKX/Aster): testnet URLs exist in UAC `_cefi.py`; `PAPER_EXECUTION_TARGETS` already
maps them to `TESTNET`. Execution-service venue adapters need to be built before testnet can be exercised. Status:
`PENDING-ADAPTER` (not `DEFERRED` — UAC contract + target mapping are correct).

## pvl-p20c: Solana devnet wiring (2026-05-15)

Shipped `execution-service/execution_service/defi_execution/protocols/solana_lst_devnet.py`.
`PAPER_EXECUTION_TARGETS["solana"] = ExecutionTarget.TESTNET` (pvl-p20a) now has an execution-side factory:

- `get_solana_rpc_for_mode(OperationalMode.PAPER)` → `https://api.devnet.solana.com`
- `get_solana_paper_connect_config()` → `BaseSolanaConnector.connect()` config with `paper_trade=True`
- `MarinadeConnector` routes to devnet; JitoRestaking/SolBlaze run in simulation mode.
- Pyth Hermes feed IDs for jitoSOL/mSOL/bSOL/SOL shipped as `SOLANA_LST_PYTH_FEED_IDS`.

## Per-asset_group rules

### CeFi (spot + perp)

Simulate via L2 CeFi matcher by default. Testnet upgrade per `PAPER_EXECUTION_TARGETS` where the venue exposes one.
pvl-p20b audit confirms: Hyperliquid testnet wired; Binance/Bybit/OKX/Aster pending adapter construction.

### DeFi (EVM)

Tenderly fork is the canonical paper target for every EVM chain we trade. Per chain → fork URL via
`unified_api_contracts/canonical/registry/capability_declarations/_defi.py:CHAIN_RPC_TEMPLATES` (extended to carry
`fork_url` alongside `live_rpc_url`).

### DeFi (Solana / non-EVM)

Solana devnet is the working default for `carry_staked_basis` jitoSOL / mSOL / bSOL legs. Localnet / surfnet remain
options if devnet's fork-state semantics prove insufficient. Pyth via Hermes for prices (already unbanned 2026-05-06).
Same per-chain rule extends to any future non-EVM chain (Sui, Aptos, etc.) — use the chain's native testnet/fork
primitive. **pvl-p20c wired 2026-05-15**: `get_solana_rpc_for_mode(PAPER)` returns devnet; `MarinadeConnector` routed to
devnet with `paper_trade=True`; JitoRestaking + SolBlaze use simulation mode (see factory module below).

**pvl-p20c factory** (`execution_service/defi_execution/protocols/solana_lst_devnet.py`):

| Helper                                   | Description                                                                    |
| ---------------------------------------- | ------------------------------------------------------------------------------ |
| `SOLANA_LST_DEVNET_RPC`                  | `https://api.devnet.solana.com` — public, no key                               |
| `get_solana_rpc_for_mode(mode, api_key)` | Devnet for PAPER/BACKTEST; Alchemy mainnet for LIVE/MANUAL                     |
| `get_solana_paper_connect_config()`      | `BaseSolanaConnector.connect()` config for paper (devnet + `paper_trade=True`) |
| `SOLANA_LST_MINTS`                       | Canonical jitoSOL / mSOL / bSOL mint addresses (from UAC)                      |
| `SOLANA_LST_PYTH_FEED_IDS`               | Pyth Hermes feed IDs for SOL + all 3 LSTs                                      |
| `estimate_lst_staking_yield(...)`        | Yield projection for `carry_staked_basis` paper runs                           |

### Sports

`PaperBettingAdapter` ships at `execution-service/execution_service/sports_execution/adapters/paper/paper_betting.py`
with full bet placement / cancellation / settlement simulation. Canonical simulator example for the workspace; the L0
Sports TOB matcher composes.

### Prediction

Matching-engine simulation only — Polymarket / Kalshi don't expose testnets we can use. The matching engine respects
per-market lifecycle bounds (`market_created_at` / `resolution_time` / `settlement_time` per `predictions_master.md`).

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
- [`../04-architecture/flash-loan-receiver.md`](../04-architecture/flash-loan-receiver.md) — Aave V3 flash loan
  deployment validates `connect()` against fork; same shape extends to Tenderly fork validation.
- [`../04-architecture/chain-environment-resolution.md`](../04-architecture/chain-environment-resolution.md) — per-chain
  RPC + fork URL resolution.
