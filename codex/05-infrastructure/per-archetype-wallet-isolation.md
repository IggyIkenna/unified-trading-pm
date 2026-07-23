---
doc_type: codex-ssot
title: Per-archetype wallet isolation (N × M multi-wallet model)
summary:
  "N archetypes × M chains = N×M wallet topology (May-23: 2 archetypes × 5 chains = 10 HOT_TRADING + 5 shared
  GAS_RESERVE). Per-archetype-per-chain isolation gives a capital firewall, granular KILL_PER_ARCHETYPE/KILL_PER_WALLET
  kill-switch, and per-wallet PnL attribution. Covers WalletProvisioningConfig schema mapping, per-WalletKind
  SpendingCaps hierarchy, per-wallet nonce queues; cross-archetype rebalancing is post-cutover."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [defi, wallet, custody, execution, strategy, infrastructure]
related:
  [
    /codex/04-architecture/custody-providers.md,
    /codex/05-infrastructure/hsm-wallet-signing.md,
    /codex/05-infrastructure/secret-manager-naming.md,
    /codex/05-infrastructure/credentials-matrix.md,
    /codex/04-architecture/wallet-hierarchy-and-capital-flow.md,
  ]
created: 2026-05-11
authoritative_for: [per-archetype per-chain wallet isolation topology]
referenced_by:
  [
    /codex/04-architecture/interface-credential-convention.md,
    /codex/05-infrastructure/aws-iam-matrix.md,
    /codex/05-infrastructure/credentials-matrix.md,
    /codex/05-infrastructure/fireblocks-integration-spec.md,
    /codex/05-infrastructure/hsm-wallet-signing.md,
    /codex/15-runbooks/pre-cutover-test-wallets-runbook.md,
    /codex/05-infrastructure/secret-manager-naming.md,
    /codex/14-customer-journeys/pod-elysium-client-onboarding.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Per-archetype wallet isolation (N × M multi-wallet model)

> **Created 2026-05-12** by slot 4 per
> [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
> Phase 9.E. Codifies the N archetypes × M chains = N×M wallet topology introduced by Phase 4.A.

---

## § 1 — Why per-archetype-per-chain isolation

A single shared wallet per chain creates correlated risk: a bug in `carry_staked_basis` can drain capital allocated to
`ARBITRAGE_PRICE_DISPERSION`. Per-archetype-per-chain isolation enforces:

1. **Capital firewall** — each archetype's wallet has its own `SpendingCaps` + `allowed_protocols` + `kill_switch_id`. A
   breach in archetype A cannot move capital out of archetype B's wallet.
2. **Granular kill-switch** — `kill_switch_id="KILL_PER_ARCHETYPE_*"` (or the finer-grain `KILL_PER_WALLET` sentinel)
   freezes one archetype on one chain without affecting siblings.
3. **Per-wallet attribution** — P&L per archetype is computable without inferring strategy-attribution from on-chain tx
   history (which would require manual labelling).
4. **HD-derivation friendliness** — under Fireblocks (June-1+), each wallet maps to a distinct derivation path under the
   master vault key.

---

## § 2 — May-23 cutover topology

2 archetypes × 5 chains = 10 HOT_TRADING wallets + 5 GAS_RESERVE (shared per-chain) + (treasury wallets per share class,
separate model).

```
carry_staked_basis × {ETHEREUM, ARBITRUM, BASE, POLYGON, SOLANA}
  → csb-eth-hot-lido-v1
  → csb-arb-hot-lido-v1
  → csb-base-hot-aave-v1
  → csb-poly-hot-aave-v1
  → csb-sol-hot-jito-v1

ARBITRAGE_PRICE_DISPERSION × {ETHEREUM, ARBITRUM, BASE, POLYGON, SOLANA}
  → apd-eth-hot-uniswap-v1
  → apd-arb-hot-uniswap-v1
  → apd-base-hot-uniswap-v1
  → apd-poly-hot-uniswap-v1
  → apd-sol-hot-raydium-v1

GAS_RESERVE (shared per chain)
  → gas-reserve-eth-v1
  → gas-reserve-arb-v1
  → gas-reserve-base-v1
  → gas-reserve-poly-v1
  → gas-reserve-sol-v1
```

Full template:
[`unified-api-contracts/config/cutover_wallet_provisioning_mainnet_template.json`](../../unified-api-contracts/config/cutover_wallet_provisioning_mainnet_template.json).

---

## § 3 — Schema mapping

Per-wallet rows live in
[`unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py`](../../unified-api-contracts/unified_api_contracts/internal/domain/defi/wallet_config.py)
`WalletProvisioningConfig`:

| Field               | Role                                                               | Example                                 |
| ------------------- | ------------------------------------------------------------------ | --------------------------------------- |
| `wallet_id`         | Unique identifier                                                  | `csb-eth-hot-lido-v1`                   |
| `archetype_id`      | Strategy binding (REQUIRED for HOT_TRADING)                        | `carry_staked_basis`                    |
| `chain`             | Chain canonical                                                    | `ETHEREUM`                              |
| `kind`              | `HOT_TRADING` / `TREASURY` / `GAS_RESERVE` / `FLASH_LOAN_RECEIVER` | `HOT_TRADING`                           |
| `signing_surface`   | HSM tier                                                           | `CLOUD_KMS_ENCRYPTED` (May-23)          |
| `allowed_protocols` | Closed-set frozen set                                              | `{"LIDO", "AAVE_V3", "UNISWAP_V3"}`     |
| `spending_caps`     | per_tx + per_hour + per_day + per_protocol                         | per § 4 below                           |
| `kill_switch_id`    | Closed-set scope reference                                         | `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` |
| `derivation_path`   | HD derivation path (Fireblocks future)                             | `m/44'/60'/0'/0/0` (empty pre-June-1)   |

---

## § 4 — Per-wallet `SpendingCaps` discipline

Closed-set hierarchy: per-wallet ≤ per-archetype ≤ per-asset_group ≤ global.

For May-23 cutover, recommended caps per `WalletKind`:

| Kind                      | per_tx_usd                    | per_hour_usd | per_day_usd | Rationale                             |
| ------------------------- | ----------------------------- | ------------ | ----------- | ------------------------------------- |
| `HOT_TRADING` (carry leg) | 50_000                        | 250_000      | 1_000_000   | Match per-archetype daily allocation  |
| `HOT_TRADING` (arb leg)   | 25_000                        | 150_000      | 500_000     | Higher tx velocity but smaller per-tx |
| `TREASURY`                | varies per client             | varies       | varies      | Set per client agreement              |
| `GAS_RESERVE`             | 1_000 (ETH) / 200 (L2)        | 10_000       | 50_000      | Gas-only; per-chain native amount cap |
| `FLASH_LOAN_RECEIVER`     | per flash-loan contract limit | n/a          | n/a         | Receiver contract itself enforces     |

`per_protocol_usd` map adds protocol-specific caps (e.g. AAVE_V3 ceiling across all wallets pointing at Aave).

---

## § 5 — Cross-archetype rebalancing flow

**Out-of-scope for May-23 cutover.** Captured as Phase 4.A sub-residual.

> **[DELTA 2026-05-22]** **Current state:** For May-23, manual rebalancing only via deployment-UI operator action.
> Copper + CEFFU target June-1; Fireblocks further out. Automated meta-strategy rebalancing is post-cutover. **Planned
> delta:** Meta-strategy design tracked under `plans/epics/defi_master.md`. **Target architecture:** Meta-strategy emits
> `REBALANCE` instructions → custodian-internal transfer (Copper / Fireblocks vault-to-vault) — no on-chain hop, no gas.

Post-cutover target: a meta-strategy emits `REBALANCE` instructions that move capital between archetype wallets via
custodian-internal transfer (Copper / Fireblocks vault-to-vault) — no on-chain hop, no gas. The meta-strategy reconciles
`archetype_id_from → archetype_id_to` allocation against the fund's strategy AUM targets.

For May-23: manual rebalancing only via deployment-UI operator action; no automated meta-strategy. Successor plan: TBD
post-cutover.

---

## § 6 — Per-wallet kill-switch wiring

Per `KillSwitchId.KILL_PER_WALLET` sentinel (UAC@`5c2d70b`):

```python
# Arm wallet-tier freeze:
arm_request = KillSwitchArmRequest(
    switch_id=KillSwitchId.KILL_PER_WALLET,
    target_wallet_id="csb-eth-hot-lido-v1",
    provenance=KillSwitchProvenance.OPERATOR_MANUAL,
    requested_by="operator-ikenna",
    arm_timestamp=datetime.now(UTC),
)
kill_switch_bus.arm(arm_request)
```

Subscribers (execution-service signer, position-balance-monitor, strategy-service signal generators) MUST consume both
`switch_id` AND `target_wallet_id` when the former is `KILL_PER_WALLET`. Routing logic:

```python
if event.switch_id == KillSwitchId.KILL_PER_WALLET:
    if signing_request.wallet_id == event.target_wallet_id:
        raise WalletKillSwitchActiveError(wallet_id=signing_request.wallet_id)
```

Broader scopes cascade (e.g. `KILL_PER_ARCHETYPE_CARRY_STAKED_BASIS` freezes all 5 chain wallets bound to that
archetype; `KILL_ALL_LIVE` freezes everything).

---

## § 7 — Per-wallet nonce queue management (sub-residual)

**Out-of-scope for May-23 cutover.** Captured as Phase 4.A sub-residual.

Multi-wallet per-chain implies multi-EOA per-chain. Each wallet maintains its own nonce — RPC sequencing handled
per-wallet by execution-service's `NonceTracker` (NEW or extend existing). No shared nonce queue.

Per-wallet RPC rate-limit sub-budget also per-wallet — RPC provider (Alchemy / Helius) sees N requests from N distinct
origin wallets, so rate-limit budget is N× a single-wallet baseline.

---

## § 8 — References

- [`custody-providers.md`](/codex/04-architecture/custody-providers.md) §1 + §2.3 — `CustodyProvider` protocol.
- [`wallet-hierarchy-and-capital-flow.md`](/codex/04-architecture/wallet-hierarchy-and-capital-flow.md) — treasury / hot
  wallet hierarchy.
- [`credentials-matrix.md`](credentials-matrix.md) — workspace credential SSOT.
- [`secret-manager-naming.md`](secret-manager-naming.md) — per-wallet wrapped-PK naming pattern.
- [`hsm-wallet-signing.md`](hsm-wallet-signing.md) — HSM tier discipline.
- [`unified-api-contracts/config/cutover_wallet_provisioning_mainnet_template.json`](../../unified-api-contracts/config/cutover_wallet_provisioning_mainnet_template.json)
  — 10 HOT + 5 GAS template for May-23.
- [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
  Phase 4.A — multi-wallet plan source.
