---
scope: [admin, engineer]
last_reviewed: 2026-05-17
execution:
  owner: "operator (ikenna) — wallet generation + KMS encryption"
  cadence: "one-shot (per cutover) — re-run only on wallet rotation"
  verifier: "gcloud secrets list --filter='name~wallet_' + verify Tenderly testnet balances seeded per archetype"
  last_executed: "pending May-23 cutover (test-wallet ramp)"
---

# Pre-cutover test-wallet operator runbook

> **Created 2026-05-12** by slot 4. **Updated 2026-05-12** with operator confirmation: _"yeah seems trust wallet is the
> direction we're going"_ — Trust Wallet is the canonical pre-cutover test wallet across all 5 EVM testnets. MetaMask
> remains a secondary lookup (address-only secret; no PK provisioned).
>
> POD client-managed Copper + CEFFU custody activates June-1; this doc covers the now → 2026-05-23 cutover → 2026-06-01
> window where we use OUR own wallets (not POD's capital).
>
> Composes with:
> [`codex/14-customer-journeys/pod-elysium-client-onboarding.md`](../14-customer-journeys/pod-elysium-client-onboarding.md)
> § 3.1 — pre-cutover test wallet table.

---

## § 0 — Canonical test wallet (where to find it)

**Canonical EVM test wallet** (confirmed operator-direction 2026-05-12):

| Surface                                                           | Value                                                         | Secret Manager entry                                                                                                                            |
| ----------------------------------------------------------------- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| **Trust Wallet EVM address** (canonical for EVM testnets)         | `0x992ebFe04DB05f964C45BCE3D73Ca4c81715a79f`                  | [`defi-wallet-trust`](#)                                                                                                                        |
| **Trust Wallet EVM PK** (raw 0x-hex)                              | (66-char hex; never logged)                                   | [`defi-wallet-private-key`](#)                                                                                                                  |
| **Trust Wallet EVM PK wrapped** (May-23 cutover signing path)     | (233-byte base64 ciphertext)                                  | [`defi-wallet-private-key-wrapped`](#) — envelope-encrypted via `wallets-staging/trading-defi-master-v1` CMK on 2026-05-12, round-trip-verified |
| MetaMask address (NOT canonical — secondary)                      | `0x0056801778F9A5dE5C8a5225B676859b797fA88B`                  | [`defi-wallet-metamask`](#) — address only, NO PK                                                                                               |
| **Trust Wallet Solana keypair** (operator-action — see § 3 below) | (needs export from Trust Wallet → Solana network → reveal PK) | `defi-wallet-solana-private-key` + `defi-wallet-solana-private-key-wrapped` (both pending operator export)                                      |

### Tenderly fork + chain RPC coverage (sorted)

Pre-cutover testing also depends on chain-RPC + Tenderly fork credentials. All confirmed present in Secret Manager
2026-05-12:

| Surface                | Secret Manager entry    | Use                                                                                                            |
| ---------------------- | ----------------------- | -------------------------------------------------------------------------------------------------------------- |
| Tenderly access        | `tenderly-api-key`      | Authenticated Tenderly API (fork creation + simulation)                                                        |
| Tenderly fork RPC      | `tenderly-fork-rpc-url` | RPC endpoint for batch/paper mode (consumed per `credentials_per_mode.yaml` Phase 7.A `paper` + `batch` modes) |
| Alchemy mainnet/L2 RPC | `alchemy-api-key`       | EVM chain RPCs (ETH / Arb / Base / Polygon mainnet + Sepolia variants)                                         |

**Sepolia coverage**: same Trust Wallet EVM PK (Sepolia uses the same secp256k1 key shape as mainnet). Operator funds
the wallet via Sepolia faucet (see § 2.1 below).

**End-to-end smoke verified 2026-05-12**: `CloudKmsCustodyProvider` fetched `defi-wallet-private-key-wrapped` → Cloud
HSM KMS Decrypt → web3.py `from_key` → derived address matched `defi-wallet-trust`. The signing pipeline that goes live
on 2026-05-23 is operationally proven against this wallet.

**Wallet provisioning JSON** (consumed at runtime by trading VM):
[`unified-api-contracts/unified_api_contracts/config/test_wallet_provisioning_pre_cutover.json`](../../unified-api-contracts/unified_api_contracts/config/test_wallet_provisioning_pre_cutover.json)
— 5 EVM testnet entries (`test-eth-sepolia-trust` / `test-arb-sepolia-trust` / `test-base-sepolia-trust` /
`test-poly-amoy-trust` / `test-holesky-trust`), all pointing at the wrapped PK + same Trust Wallet address.

---

## § 1 — Coverage status

| Chain                                          | Wallet provider                     | Setup status (per operator 2026-05-12)                                                                          |
| ---------------------------------------------- | ----------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| ETHEREUM mainnet                               | **Trust Wallet** (canonical)        | ✅ Already set up — PK in `defi-wallet-private-key`                                                             |
| ETHEREUM Sepolia                               | Trust Wallet (same EVM PK)          | ✅ Already set up (CeFi wallets on Ethereum confirmed)                                                          |
| Arbitrum / Base / Polygon (mainnet + testnets) | Trust Wallet (same EVM PK)          | ✅ Already set up — same EVM PK works across chains                                                             |
| Holesky (Lido + EigenLayer testnet)            | Trust Wallet (same EVM PK)          | ⚪ Operator add network per § 2.2                                                                               |
| **Solana mainnet**                             | Phantom OR solana-cli               | 🟡 **OPERATOR ACTION** per § 3                                                                                  |
| **Solana devnet**                              | Phantom OR solana-cli               | 🟡 **OPERATOR ACTION** per § 3                                                                                  |
| CeFi venues (Bybit / OKX / Deribit / etc.)     | Per-venue institutional sandbox     | ⚪ Per-venue operator onboarding (out of agent scope)                                                           |
| MetaMask (secondary)                           | `defi-wallet-metamask` address only | ⚪ No PK in Secret Manager. Operator may provision separately if MetaMask wallet should also be live (see § 5). |

---

## § 2 — EVM chains (operator can do via Trust Wallet / MetaMask UI)

### 2.1 Add new EVM networks to existing Trust Wallet (canonical) or MetaMask

For each new chain, operator clicks Settings → Networks → Add Network → fills:

| Chain                | Chain ID | RPC URL                                     | Currency | Block Explorer               |
| -------------------- | -------- | ------------------------------------------- | -------- | ---------------------------- |
| Arbitrum mainnet     | 42161    | https://arb1.arbitrum.io/rpc                | ETH      | https://arbiscan.io          |
| Arbitrum Sepolia     | 421614   | https://sepolia-rollup.arbitrum.io/rpc      | ETH      | https://sepolia.arbiscan.io  |
| Base mainnet         | 8453     | https://mainnet.base.org                    | ETH      | https://basescan.org         |
| Base Sepolia         | 84532    | https://sepolia.base.org                    | ETH      | https://sepolia.basescan.org |
| Polygon mainnet      | 137      | https://polygon-rpc.com                     | MATIC    | https://polygonscan.com      |
| Polygon Amoy testnet | 80002    | https://rpc-amoy.polygon.technology         | MATIC    | https://amoy.polygonscan.com |
| Holesky              | 17000    | https://ethereum-holesky-rpc.publicnode.com | ETH      | https://holesky.etherscan.io |

After adding, operator funds the wallet from a testnet faucet:

- Sepolia: <https://sepoliafaucet.com>
- Arbitrum Sepolia: <https://faucet.quicknode.com/arbitrum/sepolia>
- Base Sepolia: <https://www.alchemy.com/faucets/base-sepolia>
- Polygon Amoy: <https://faucet.polygon.technology/>
- Holesky: <https://holesky-faucet.pk910.de/>

### 2.2 Handing the test PK to slot 4 agent

For agent to envelope-encrypt + provision per [`custody-onboarding-checklist.md`](custody-onboarding-checklist.md) §
B.3:

1. Operator clicks MetaMask account → Account details → Show private key.
2. Operator pastes PK into a single-use temp file on cold-laptop OR shares securely (1Password Secure Note / Signal
   disappearing message — NEVER plain-text email / Slack).
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
     "spending_caps": { "per_tx_usd": "100", "per_day_usd": "1000" },
     "kill_switch_id": "KILL_PER_ASSET_GROUP_DEFI",
     "archetype_id": "test"
   }
   ```

---

## § 3 — Solana setup — Trust Wallet path (operator-confirmed direction)

**Confirmed operator-direction 2026-05-12** (_"or can we use trust wallet for solana too?"_): yes — Trust Wallet
supports Solana via the **same BIP-39 mnemonic seed** but derives a **different keypair** (Ed25519 for Solana vs
secp256k1 for EVM). The EVM PK in `defi-wallet-private-key` therefore **cannot be reused on Solana** — operator must
export the Solana keypair separately from Trust Wallet's Solana wallet view.

### 3.1 Trust Wallet → Solana keypair export (recommended)

1. Open Trust Wallet (mobile or browser extension) — the same wallet that holds the EVM seed in `defi-wallet-trust` /
   `defi-wallet-private-key`.
2. Switch to the **Solana wallet** view (Trust Wallet's left-side wallet selector → Solana).
3. Note the **Solana public address** (base58-encoded, no `0x` prefix).
4. **Reveal Solana private key**: Settings → Wallets → (selected wallet) → Show Recovery Phrase (or "Show Private Key"
   if exposed at wallet level). Trust Wallet UI: tap the Solana wallet → Settings → Show Private Key. The Solana PK is a
   base58-encoded string (NOT the EVM 0x-hex format).
5. Hand the **Solana private key** + **Solana public address** to slot 4 agent via secure channel (1Password Secure Note
   / Signal disappearing message — NEVER plain-text email / Slack).

Slot 4 agent then:

```bash
PROJECT_ID=central-element-323112
CMK="projects/${PROJECT_ID}/locations/asia-northeast1/keyRings/wallets-staging/cryptoKeys/trading-defi-master-v1"

# Provision the raw Solana address + PK
gcloud secrets create defi-wallet-solana --data-file=- <<< "${SOLANA_ADDRESS}"
gcloud secrets create defi-wallet-solana-private-key --data-file=- <<< "${SOLANA_PK_BASE58}"

# Envelope-encrypt + provision wrapped version (mirrors EVM Trust Wallet flow)
gcloud secrets versions access latest --secret=defi-wallet-solana-private-key --project=${PROJECT_ID} \
  | gcloud kms encrypt --key=${CMK} --plaintext-file=- --ciphertext-file=- --project=${PROJECT_ID} \
  | base64 \
  | gcloud secrets create defi-wallet-solana-private-key-wrapped --data-file=- --project=${PROJECT_ID}
```

Then add to
[`test_wallet_provisioning_pre_cutover.json`](../../unified-api-contracts/unified_api_contracts/config/test_wallet_provisioning_pre_cutover.json):

```json
{
  "wallet_id": "test-sol-mainnet-trust",
  "chain": "SOLANA",
  "kind": "HOT_TRADING",
  "signing_surface": "CLOUD_KMS_ENCRYPTED",
  "kms_key_uri": "projects/central-element-323112/locations/asia-northeast1/keyRings/wallets-staging/cryptoKeys/trading-defi-master-v1",
  "private_key_secret_ref": "defi-wallet-solana-private-key-wrapped",
  "address": "<SOLANA_BASE58_PUBKEY>",
  "allowed_protocols": ["JITO", "MARINADE", "RAYDIUM", "ORCA", "JUPITER"],
  "spending_caps": { "per_tx_usd": "100", "per_day_usd": "1000" },
  "kill_switch_id": "KILL_PER_ASSET_GROUP_DEFI",
  "archetype_id": "test_carry_staked_basis"
}
```

### 3.2 Solana devnet wallet (optional — operator can use mainnet small-amount)

The Trust Wallet Solana wallet from § 3.1 is **mainnet by default**. For devnet-only testing (zero capital risk), two
options:

(a) **Reuse the mainnet Trust Wallet keypair on devnet** — Solana mainnet keypairs work on devnet as identity (no
economic risk on devnet; same public address). Just airdrop devnet SOL to the same pubkey:

```bash
solana airdrop 2 <SOLANA_PUBKEY> --url devnet
```

(b) **Generate a fresh devnet-only keypair** via solana-cli — separate identity from the Trust Wallet mainnet wallet.
Useful if operator wants strict mainnet/devnet wallet separation:

```bash
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"
solana-keygen new --outfile ~/.config/solana/uts-test-sol-devnet.json
solana airdrop 2 $(solana-keygen pubkey ~/.config/solana/uts-test-sol-devnet.json) --url devnet
# Hand keypair JSON to slot 4 agent for wrapping via staging CMK
```

### 3.3 Phantom (NOT recommended now that Trust Wallet path is chosen)

Phantom remains a valid alternative wallet provider per <https://phantom.app>, but per operator 2026-05-12 direction the
canonical path is Trust Wallet (same seed across EVM + Solana for operational simplicity). Phantom flow only if operator
decides to provision a **separate** Solana keypair distinct from Trust Wallet — not the current direction.

### 3.4 RPC credentials (Solana mainnet + devnet)

Solana RPC endpoint credentials needed beyond the wallet:

- **Public devnet RPC** (`https://api.devnet.solana.com`): public, no auth required — sufficient for low-rate test
  smoke.
- **Production-grade RPC** (Helius / QuickNode / Triton): NOT YET in Secret Manager. Operator-action P1 if
  production-rate Solana RPC needed.
- **Pyth Hermes** (oracle prices, mainnet + devnet): public HTTPS endpoint per UAC `oracle_prices_handler.py` — no auth
  needed.

---

## § 4 — Per-chain test wallet registry

Once all wallets are provisioned per § 2-3, slot 4 agent maintains a registry at
`gs://wallet-config-central-element-323112/testnet/wallet_provisioning.json` mirroring the prod template shape at
[`cutover_wallet_provisioning_mainnet_template.json`](../../unified-api-contracts/unified_api_contracts/config/cutover_wallet_provisioning_mainnet_template.json).

Each entry uses `signing_surface=LOCAL_KEY` (for raw-key testnet) OR `signing_surface=CLOUD_KMS_ENCRYPTED` (for
envelope-encrypted testnet/mainnet small-amount tests).

---

## § 4.A — Optional: separate MetaMask wallet provisioning

`defi-wallet-metamask` holds the MetaMask EVM address (`0x0056801778F9A5dE5C8a5225B676859b797fA88B`) but **no private
key**. This means MetaMask is NOT currently a usable test wallet — only Trust Wallet is.

If operator wants MetaMask as a second usable test wallet (e.g. for parallel-strategy smoke tests, dual-wallet
liquidation drills, or operator-vs-system signing separation), follow the same envelope-encrypt flow as Trust Wallet:

```bash
# Operator opens MetaMask → Account → Show private key → reveal PK
# Operator hands PK to slot 4 agent via secure channel.
# Slot 4 agent runs:
PROJECT_ID=central-element-323112
CMK="projects/${PROJECT_ID}/locations/asia-northeast1/keyRings/wallets-staging/cryptoKeys/trading-defi-master-v1"
echo -n "${METAMASK_PK}" \
  | gcloud kms encrypt --key=${CMK} --plaintext-file=- --ciphertext-file=- --project=${PROJECT_ID} \
  | base64 \
  | gcloud secrets create defi-wallet-metamask-private-key-wrapped --data-file=- --project=${PROJECT_ID}
# (Also create defi-wallet-metamask-private-key with raw PK if LOCAL_KEY surface needed.)
```

Then add MetaMask-prefixed entries to `test_wallet_provisioning_pre_cutover.json` mirroring the Trust Wallet shape
(`test-eth-sepolia-metamask` / etc.) pointing at the new `defi-wallet-metamask-private-key-wrapped` secret.

**Not blocking May-23 cutover**; pure NICE-TO-HAVE.

---

## § 5 — Continuous verification

```yaml
execution:
  owner: ikennaigboaka (operator) + slot 4 agent
  cadence: one-shot setup → daily smoke until 2026-06-01 (POD cred handover)
  verifier: `credential-probe.sh --mode paper` returns 100% pass for test wallets
  last_executed: NEVER
```

Pre-cutover gate (2026-05-22): smoke-test sign-and-broadcast on every test wallet (Sepolia + Arbitrum Sepolia + Base
Sepolia + Polygon Amoy + Holesky

- Solana devnet). Operator records tx hashes in deployment-UI Live Tab.

---

## § 6 — Cross-references

- [`pod-elysium-client-onboarding.md`](../14-customer-journeys/pod-elysium-client-onboarding.md) — POD entity SSOT.
- [`custody-onboarding-checklist.md`](custody-onboarding-checklist.md) § B.3 — envelope-encrypt operator runbook.
- [`per-archetype-wallet-isolation.md`](per-archetype-wallet-isolation.md) — N×M wallet model.
- [`hsm-wallet-signing.md`](hsm-wallet-signing.md) — 5-tier HSM ladder.
- [`cutover_wallet_provisioning_mainnet_template.json`](../../unified-api-contracts/unified_api_contracts/config/cutover_wallet_provisioning_mainnet_template.json)
  — prod template.
- [`api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md)
  Phase 4.D.3 + 4.D.6 + 4.D.7.
