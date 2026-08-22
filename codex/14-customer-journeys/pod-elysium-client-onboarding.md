---
doc_type: codex-ssot
title: POD / Elysium DeFi-allocator client — onboarding model
summary: "Onboarding model for POD (DeFi allocator, sub-entity of Elysium AIFM Ireland; BVI fund) — entity stack, the
  POD-vs-UTS custody/venue ownership split, and the pre-cutover Trust-Wallet test-wallet credential model vs the June-1
  Copper/CEFFU cutover (Fireblocks OUT OF SCOPE)."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service]
scope: [admin, engineer]
tags: [defi, cefi, onboarding, custody, wallets, credentials, client]
related:
  [
    /codex/04-architecture/custody-providers.md,
    /codex/04-architecture/transfer-architecture.md,
    /codex/15-runbooks/custody-onboarding-checklist.md,
    /codex/15-runbooks/pre-cutover-test-wallets-runbook.md,
    /plans/active/w23_pod_collateral_delegation_transfer_rail_2026_08_22.md,
  ]
created: 2026-05-12
authoritative_for: [POD/Elysium DeFi-allocator client onboarding model]
referenced_by:
  [
    /codex/04-architecture/custody-providers.md,
    /codex/05-infrastructure/credentials-matrix.md,
    /codex/15-runbooks/pre-cutover-test-wallets-runbook.md,
    /codex/14-customer-journeys/commercial-model/elysium-account-trajectory-2026-05-14.md,
    /codex/14-customer-journeys/commercial-model/elysium-managed-sla-2026-05-14.md,
  ]
owner:
last_reviewed:
code_refs:
---

# POD / Elysium DeFi-allocator client — onboarding model

> **Created 2026-05-12** by slot 4 per operator clarification: _"called POD which is sub entity of elysium which is a
> fund admin and AIFM Ireland regulated investment manager fund is bvi they are our first DeFi allocators and manage the
> custody and exchange onboarding directly with them. For test we need our own setup with trust wallets or metamask and
> cefi wallets we have both setup on ethereum already for sol and non evm chain i guess its operator led just need to
> tell em what to setup for tests."_
>
> Disambiguates from the deprecated "Elysium" MEV-route provider listed in CLAUDE.md
> (`Removed providers: Elysium, Arkham, Bloxroute, Infura`). The entities are **unrelated** — one is a banned MEV-route,
> the other is our first DeFi-allocator client.

---

## § 1 — Entity stack

```
ELYSIUM (Ireland) — AIFM, fund administrator, regulated investment manager
   │
   └── POD (sub-entity) — DeFi-specific allocator + our first client
        │
        └── BVI Fund — capital pool, beneficial owner of trading positions
```

| Entity     | Role                                                    | Jurisdiction           | Regulated                                    |
| ---------- | ------------------------------------------------------- | ---------------------- | -------------------------------------------- |
| Elysium    | Fund admin + AIFM (Alternative Investment Fund Manager) | Ireland                | Yes (Central Bank of Ireland)                |
| POD        | DeFi-specific sub-entity / allocator                    | Ireland                | Inherited from Elysium AIFM                  |
| Fund (BVI) | Capital vehicle                                         | British Virgin Islands | Per BVI Securities + Investment Business Act |

**Our (UTS) role**: trading infrastructure service to POD. We execute trades on behalf of the BVI Fund using credentials
delegated to us by POD.

---

## § 2 — Custody + venue onboarding ownership

> **⚠️ "Managed" here means OPERATIONAL RESPONSIBILITY, never IP ownership (clarified 2026-08-11).** The "UTS-managed /
> trading code" row below has been read as "we own the trading code", which is **wrong on the face of the contract**:
> Consulting Agreement Art. 4.1–4.2 makes all Work Product the exclusive, perpetually-assigned property of the Elysium
> Group, and Art. 4.6 retains only "generic programming methods and open-sourced components" for us. Read this section
> as "who runs it and who holds the relationship", and take ownership exclusively from
> [`/codex/14-customer-journeys/commercial-model/contracts/elysium-consulting-agreement-2025-03.md`](/codex/14-customer-journeys/commercial-model/contracts/elysium-consulting-agreement-2025-03.md)
> § "Read this first".

**POD-managed** (not us):

- Copper.co institutional onboarding + KYB.
- CEFFU institutional KYB.
- Binance institutional account (OES bilateral mirror at CEFFU).
- Per-venue institutional onboarding at the 6 perp venues + spot venues POD allocates to (Bybit / OKX / Deribit /
  Hyperliquid / Aster / Kraken / Bitfinex / Bitget — subject to POD venue-list approval).

**UTS-operated** (we run it; ownership per Art. 4 is a separate question — see the banner):

- Pre-cutover testing infrastructure (MetaMask / Trust Wallet / sandbox).
- Trading code (execution-service + strategy-service + per-archetype config) — **we build and operate it; the Work
  Product it constitutes is the Elysium Group's under Art. 4.1–4.2.**
- Cloud HSM CMKs (provisioned 2026-05-12 for envelope-encrypted test PK signing; replaced by POD-delivered Copper/CEFFU
  creds June-1).
- Per-wallet `WalletProvisioningConfig` rows in `gs://wallet-config-{pid}/{chain_env}/wallet_provisioning.json`.

---

## § 3 — Pre-cutover vs cutover credential model

### 3.1 Pre-cutover (now → 2026-05-23 → 2026-06-01)

**Test setup** uses our own wallets — no client capital at risk.

**Canonical wallet = Trust Wallet** (per operator 2026-05-12 _"yeah seems trust wallet is the direction we're going"_).
Single BIP-39 seed → EVM PK + Solana keypair (different Ed25519 key under same mnemonic).

| Chain                                                                        | Wallet                                                                    | Secret Manager refs                                                                                                                                                                                                                       | `SigningSurface`                                                                         |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| ETHEREUM mainnet + Sepolia + 5 EVM testnets (Arb / Base / Polygon / Holesky) | **Trust Wallet** EVM PK                                                   | `defi-wallet-trust` (addr) + `defi-wallet-private-key` (PK) + `defi-wallet-private-key-wrapped` (CMK-encrypted)                                                                                                                           | `CLOUD_KMS_ENCRYPTED` via `wallets-staging/trading-defi-master-v1` (verified 2026-05-12) |
| Solana mainnet + devnet                                                      | **Trust Wallet Solana wallet** (separate Ed25519 keypair under same seed) | `defi-wallet-solana` + `defi-wallet-solana-private-key` + `defi-wallet-solana-private-key-wrapped` (🟡 PENDING operator export — see [`pre-cutover-test-wallets-runbook.md`](/codex/15-runbooks/pre-cutover-test-wallets-runbook.md) § 3) | `CLOUD_KMS_ENCRYPTED` via same staging CMK                                               |
| Tenderly fork + chain RPCs (EVM all)                                         | n/a (RPC creds)                                                           | `tenderly-api-key` + `tenderly-fork-rpc-url` + `alchemy-api-key`                                                                                                                                                                          | n/a (RPC auth, not signing)                                                              |
| CeFi (BYBIT / BINANCE / etc.)                                                | Per-venue institutional sandbox                                           | Per-venue secrets `<venue>-{read,trade,withdraw}-*` (sandbox suffixed)                                                                                                                                                                    | n/a (venue-managed)                                                                      |
| MetaMask (secondary, NOT canonical)                                          | Address-only — no PK in Secret Manager                                    | `defi-wallet-metamask`                                                                                                                                                                                                                    | n/a unless operator provisions per-runbook § 4.A                                         |

**Tenderly fork + Sepolia + EVM testnets: ✅ FULLY SORTED** — Tenderly access

- fork RPC URL + Alchemy chain RPCs all confirmed present in Secret Manager 2026-05-12.

**Solana: 🟡 PARTIAL** — Trust Wallet's Solana wallet (same seed, different keypair) is the chosen route, but the Solana
PK has NOT YET been exported from Trust Wallet to Secret Manager. Operator runbook in
[`pre-cutover-test-wallets-runbook.md`](/codex/15-runbooks/pre-cutover-test-wallets-runbook.md) § 3.1.

CeFi test wallets (BYBIT / BINANCE / etc.) on **Ethereum already set up** by operator pre-2026-05-12; awaiting
confirmation of per-venue institutional sandbox availability (out of slot 4 scope; per-venue operator onboarding).

### 3.2 Cutover (2026-06-01 onwards)

POD delivers institutional credentials:

| Surface                               | Provider                   | Provisioned by                     | `signing_surface`                                                                                      |
| ------------------------------------- | -------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------ |
| DeFi (Ethereum + L2s + Solana)        | Copper.co MPC              | POD → operator via secure handover | `COPPER_MPC`                                                                                           |
| Binance perp                          | CEFFU OES bilateral mirror | POD → operator                     | `COPPER_MPC` (Copper signs CEFFU's OES instructions) OR separate `CEFFU_OES` if separate adapter ships |
| Spot + non-Binance CeFi institutional | CEFFU direct custody       | POD → operator                     | per-venue (see Custody Coverage Matrix)                                                                |

**OUT OF SCOPE**: Fireblocks. Per operator 2026-05-12: _"i think they plan to use copper and ceffu only"_.
`SigningSurface.FIREBLOCKS_MPC` stays in the enum for future flexibility but is NOT a May-23 / June-1 target for POD.

---

## § 4 — Solana + non-EVM test-wallet operator runbook

Operator must provision Solana test wallets (devnet for daily smoke; mainnet small-amount for production smoke):

### 4.1 Solana devnet test wallet (operator one-shot)

```bash
# Install solana-cli on operator workstation (one-time)
sh -c "$(curl -sSfL https://release.solana.com/stable/install)"

# Generate a new keypair (cold-laptop preferred but devnet is acceptable on workstation)
solana-keygen new --outfile ~/.config/solana/uts-test-sol-devnet.json --no-bip39-passphrase

# Export pubkey
PUBKEY=$(solana-keygen pubkey ~/.config/solana/uts-test-sol-devnet.json)
echo "Test Solana devnet wallet: ${PUBKEY}"

# Airdrop SOL for gas
solana airdrop 2 ${PUBKEY} --url devnet

# Export PK base58 string for UTS Secret Manager
solana-keygen pubkey ~/.config/solana/uts-test-sol-devnet.json  # address
cat ~/.config/solana/uts-test-sol-devnet.json  # JSON array; needs base58 conversion via helper
```

Then operator hands the keypair JSON to slot 4 agent who:

- For LOCAL_KEY surface (testnet only): stores keypair JSON in
  `gcloud secrets create uts-sol-test-devnet-pk --data-file=<file>`.
- For CLOUD_KMS_ENCRYPTED surface (mainnet small-amount test): envelope-encrypts via
  `gcloud kms encrypt --key=projects/central-element-323112/locations/asia-northeast1/keyRings/wallets-staging/cryptoKeys/trading-defi-master-v1 --plaintext-file=<file> --ciphertext-file=- | base64`
  then provisions wrapped to Secret Manager.

### 4.2 Solana mainnet small-amount test wallet (operator one-shot)

Same flow as 4.1 but use a **cold laptop** for keypair generation. Fund with ≤$10 SOL for first sign-and-broadcast
smoke. Envelope-encrypt via `wallets-prod/trading-defi-master-v1` CMK.

### 4.3 Other non-EVM chains (TBD)

Sui / Aptos / TON — not in May-23 cutover scope. When in scope: same pattern as 4.1/4.2 with the per-chain CLI tool.

---

## § 5 — Codex updates required by POD scope shift

- [x] [`pod-elysium-client-onboarding.md`](pod-elysium-client-onboarding.md) — THIS doc (created 2026-05-12).
- [ ] [`/codex/04-architecture/custody-providers.md`](/codex/04-architecture/custody-providers.md) § R9 RESOLVED banner
      — add POD entity reference; clarify Fireblocks is OUT OF SCOPE per POD's stack choice (Copper + CEFFU only).
- [ ] [`/codex/15-runbooks/custody-onboarding-checklist.md`](/codex/15-runbooks/custody-onboarding-checklist.md) § C —
      reframe: Fireblocks section is _future-spec_; not a May-23/June-1 actionable item for POD.
- [ ] [`/codex/05-infrastructure/credentials-matrix.md`](/codex/05-infrastructure/credentials-matrix.md) — confirm
      `fireblocks-*` Secret Manager paths stay declared but tagged `pod_out_of_scope: true`.
- [x] CLAUDE.md disambiguation — NOT in this commit (would touch shared config); deferred to operator decision on
      whether the deprecated "Elysium" MEV-route entry needs replacement or stays as-is.

---

## § 6 — Cross-references

- [`custody-providers.md`](/codex/04-architecture/custody-providers.md) — architectural SSOT.
- [`transfer-architecture.md`](/codex/04-architecture/transfer-architecture.md) § "Custodian-mediated collateral
  delegation (`CUSTODIAN_COLLATERAL_DELEGATION`, 2026-08-22)" — POD is building an API where we instruct a
  cross-venue collateral move and POD internally resolves the custodian address + exchange account (no signing, no
  wallet addresses on our side); this is the transfer rail that carries POD's instructions, wired as a generic
  `BusTransferType` member (not POD-specific) through the existing `TransferAdapter`/`TransferHandler` path. Build
  tracked in
  [`/plans/active/w23_pod_collateral_delegation_transfer_rail_2026_08_22.md`](/plans/active/w23_pod_collateral_delegation_transfer_rail_2026_08_22.md).
- [`custody-onboarding-checklist.md`](/codex/15-runbooks/custody-onboarding-checklist.md) — operator runbook.
- [`fireblocks-integration-spec.md`](/codex/05-infrastructure/fireblocks-integration-spec.md) — future-spec only per POD
  scope.
- [`per-archetype-wallet-isolation.md`](/codex/05-infrastructure/per-archetype-wallet-isolation.md) — multi-wallet
  model.
- [`plans/active/api_keys_wallets_accounts_readiness_2026_05_10.md`](../../plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md)
  — parent plan; POD scope clarification 2026-05-12 captured in plan body.
