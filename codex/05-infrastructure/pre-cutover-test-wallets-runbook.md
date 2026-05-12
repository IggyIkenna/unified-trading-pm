---
scope: [admin, operator]
---

# Pre-cutover test-wallet operator runbook

> **Created 2026-05-12** by slot 4 per operator 2026-05-12 clarification:
> *"for test we need our own setup with trust wallets or metamask and cefi
> wallets we have both setup on ethereum already for sol and non evm chain
> i guess its operator led just need to tell em what to setup for tests."*
>
> Captures the operator-action setup for pre-cutover testing wallets. POD
> client-managed Copper + CEFFU custody activates June-1; this doc covers
> the now → 2026-05-23 cutover → 2026-06-01 window where we use OUR own
> wallets (not POD's capital).
>
> Composes with:
> [`codex/14-customer-journeys/pod-elysium-client-onboarding.md`](../14-customer-journeys/pod-elysium-client-onboarding.md)
> § 3.1 — pre-cutover test wallet table.

---

## § 1 — Coverage status

| Chain | Wallet provider | Setup status (per operator 2026-05-12) |
|---|---|---|
| ETHEREUM mainnet | MetaMask / Trust Wallet | ✅ Already set up |
| ETHEREUM Sepolia | MetaMask | ✅ Already set up (CeFi wallets on Ethereum confirmed) |
| Arbitrum / Base / Polygon (mainnet + testnets) | MetaMask | ✅ Already set up (operator extends MetaMask to new networks per § 2.1) |
| Holesky (Lido + EigenLayer testnet) | MetaMask | ⚪ Operator add network per § 2.2 |
| **Solana mainnet** | Phantom OR solana-cli | 🟡 **OPERATOR ACTION** per § 3 |
| **Solana devnet** | Phantom OR solana-cli | 🟡 **OPERATOR ACTION** per § 3 |
| CeFi venues (Bybit / OKX / Deribit / etc.) | Per-venue institutional sandbox | ⚪ Per-venue operator onboarding (out of agent scope) |

---

## § 2 — EVM chains (operator can do via MetaMask UI)

### 2.1 Add new EVM networks to existing MetaMask

For each new chain, operator clicks Settings → Networks → Add Network → fills:

| Chain | Chain ID | RPC URL | Currency | Block Explorer |
|---|---|---|---|---|
| Arbitrum mainnet | 42161 | https://arb1.arbitrum.io/rpc | ETH | https://arbiscan.io |
| Arbitrum Sepolia | 421614 | https://sepolia-rollup.arbitrum.io/rpc | ETH | https://sepolia.arbiscan.io |
| Base mainnet | 8453 | https://mainnet.base.org | ETH | https://basescan.org |
| Base Sepolia | 84532 | https://sepolia.base.org | ETH | https://sepolia.basescan.org |
| Polygon mainnet | 137 | https://polygon-rpc.com | MATIC | https://polygonscan.com |
| Polygon Amoy testnet | 80002 | https://rpc-amoy.polygon.technology | MATIC | https://amoy.polygonscan.com |
| Holesky | 17000 | https://ethereum-holesky-rpc.publicnode.com | ETH | https://holesky.etherscan.io |

After adding, operator funds the wallet from a testnet faucet:
- Sepolia: <https://sepoliafaucet.com>
- Arbitrum Sepolia: <https://faucet.quicknode.com/arbitrum/sepolia>
- Base Sepolia: <https://www.alchemy.com/faucets/base-sepolia>
- Polygon Amoy: <https://faucet.polygon.technology/>
- Holesky: <https://holesky-faucet.pk910.de/>

### 2.2 Handing the test PK to slot 4 agent

For agent to envelope-encrypt + provision per
[`custody-onboarding-checklist.md`](custody-onboarding-checklist.md) § B.3:

1. Operator clicks MetaMask account → Account details → Show private key.
2. Operator pastes PK into a single-use temp file on cold-laptop OR shares
   securely (1Password Secure Note / Signal disappearing message — NEVER
   plain-text email / Slack).
3. Slot 4 agent runs envelope-encrypt:
   ```bash
   PROJECT_ID=central-element-323112
   CMK="projects/${PROJECT_ID}/locations/asia-northeast1/keyRings/wallets-staging/cryptoKeys/trading-defi-master-v1"
   # ↑ STAGING CMK for testnet PKs. Use wallets-prod CMK only for mainnet small-amount test PKs.
   echo -n "${PK_HEX}" | gcloud kms encrypt \
       --key="${CMK}" \
       --plaintext-file=/dev/stdin \
       --ciphertext-file=- \
       --project=${PROJECT_ID} | base64 > /tmp/test-pk-wrapped.b64
   gcloud secrets create test-eth-sepolia-pk-wrapped --data-file=/tmp/test-pk-wrapped.b64
   shred -u /tmp/test-pk-wrapped.b64
   ```
4. Slot 4 populates `WalletProvisioningConfig`:
   ```json
   {
     "wallet_id": "test-eth-sepolia",
     "chain": "SEPOLIA",
     "kind": "HOT_TRADING",
     "signing_surface": "CLOUD_KMS_ENCRYPTED",
     "kms_key_uri": "projects/central-element-323112/locations/asia-northeast1/keyRings/wallets-staging/cryptoKeys/trading-defi-master-v1",
     "private_key_secret_ref": "test-eth-sepolia-pk-wrapped",
     "allowed_protocols": ["AAVE_V3", "UNISWAP_V3", "LIDO"],
     "spending_caps": {"per_tx_usd": "100", "per_day_usd": "1000"},
     "kill_switch_id": "KILL_PER_ASSET_GROUP_DEFI",
     "archetype_id": "test"
   }
   ```

---

## § 3 — Solana setup (operator one-time)

Solana wallet setup is operator-led because there's no MetaMask-equivalent
already configured. Choose Phantom (browser UX) OR solana-cli (terminal).

### 3.1 Phantom (recommended for operator UX)

1. Install Phantom browser extension: <https://phantom.app>
2. Create new wallet → save seed phrase (12 words) to 1Password Secure Note.
3. Switch to devnet: Settings → Developer Settings → Change Network → Devnet.
4. Copy the wallet's public address.
5. Fund via Solana faucet:
   ```bash
   solana airdrop 2 <YOUR_PUBKEY> --url devnet
   ```
   OR via <https://faucet.solana.com> (devnet 2 SOL per request).
6. Export PK: Settings → Show Private Key → reveal the base58-encoded PK.
7. Hand to slot 4 agent per § 2.2 envelope-encrypt flow (replace
   `test-eth-sepolia-pk-wrapped` with `test-sol-devnet-pk-wrapped`).

### 3.2 solana-cli (alternative)

```bash
# Install solana-cli (one-time)
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Generate new keypair (devnet — workstation OK; mainnet — cold laptop)
solana-keygen new --outfile ~/.config/solana/uts-test-sol-devnet.json

# Get the pubkey
solana-keygen pubkey ~/.config/solana/uts-test-sol-devnet.json

# Configure CLI to use devnet
solana config set --url devnet

# Airdrop SOL for gas
solana airdrop 2

# Hand the keypair JSON to slot 4 agent for envelope-encrypt
```

The keypair JSON contains the base58 array form of the PK. Slot 4 agent
encrypts the JSON file directly (or converts to hex first; either works
with web3py-equivalent Solana SDK).

### 3.3 Mainnet small-amount Solana test wallet

Same as 3.1 / 3.2 BUT:
- Use a **cold laptop** for keypair generation (per § B.3.1 of
  [`custody-onboarding-checklist.md`](custody-onboarding-checklist.md)).
- Fund with ≤$10 SOL only for first sign-and-broadcast smoke.
- Envelope-encrypt with `wallets-prod` CMK (not staging).

---

## § 4 — Per-chain test wallet registry

Once all wallets are provisioned per § 2-3, slot 4 agent maintains a
registry at
`gs://wallet-config-central-element-323112/testnet/wallet_provisioning.json`
mirroring the prod template shape at
[`cutover_wallet_provisioning_mainnet_template.json`](../../unified-api-contracts/unified_api_contracts/config/cutover_wallet_provisioning_mainnet_template.json).

Each entry uses `signing_surface=LOCAL_KEY` (for raw-key testnet) OR
`signing_surface=CLOUD_KMS_ENCRYPTED` (for envelope-encrypted testnet/mainnet
small-amount tests).

---

## § 5 — Continuous verification

```yaml
execution:
  owner: ikennaigboaka (operator) + slot 4 agent
  cadence: one-shot setup → daily smoke until 2026-06-01 (POD cred handover)
  verifier: `credential-probe.sh --mode paper` returns 100% pass for test wallets
  last_executed: NEVER
```

Pre-cutover gate (2026-05-22): smoke-test sign-and-broadcast on every test
wallet (Sepolia + Arbitrum Sepolia + Base Sepolia + Polygon Amoy + Holesky
+ Solana devnet). Operator records tx hashes in deployment-UI Live Tab.

---

## § 6 — Cross-references

- [`pod-elysium-client-onboarding.md`](../14-customer-journeys/pod-elysium-client-onboarding.md) — POD entity SSOT.
- [`custody-onboarding-checklist.md`](custody-onboarding-checklist.md) § B.3 — envelope-encrypt operator runbook.
- [`per-archetype-wallet-isolation.md`](per-archetype-wallet-isolation.md) — N×M wallet model.
- [`hsm-wallet-signing.md`](hsm-wallet-signing.md) — 5-tier HSM ladder.
- [`cutover_wallet_provisioning_mainnet_template.json`](../../unified-api-contracts/unified_api_contracts/config/cutover_wallet_provisioning_mainnet_template.json) — prod template.
- [`api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md) Phase 4.D.3 + 4.D.6 + 4.D.7.
