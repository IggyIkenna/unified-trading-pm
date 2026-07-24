---
doc_type: issue
title: Credential configs reference IDs that don't match real Secret Manager names/model (perp hedge venues)
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-24
source:
  [
    UAC test_credentials_per_mode_archetype failure (bybit) → GCP Secret Manager audit 2026-05-24,
    composes with the active credential-alignment work (UAC@2ec9fcf3 'align credential IDs to actual SM names'),
  ]
locked_by: live-defi-rollout
priority: P2
---

> **✅ ARCHIVED 2026-05-27 `[unlock-plan]`** — RESOLVED — SM-id drift fixed on live-defi-rollout (UAC@4e3fc932
> `credentials_per_archetype.yaml` real SM ids; deployment-service@c0537bf per-client okx probe). Only residual is
> human-only wallet-PK provisioning (out of issue scope).
>
> Operator-authorized archival 2026-05-27 (issue-doc lifecycle: work shipped or fully captured in a named plan). Lock
> `live-defi-rollout` removed via `[unlock-plan]` in the archival commit.

## What I found

Fixing the failing UAC test `test_batch_mode_includes_read_scope_venue_keys` (it asserted `bybit-read-api-key`, but SM
has `bybit_api_key`; fixed in UAC@728a1353) surfaced that **`credentials_per_archetype.yaml`'s perp-hedge-venue
credential IDs broadly do not match real GCP Secret Manager** (`central-element-323112`). The config assumes a flat
`<venue>-trade-api-key` model; SM uses **four different models**:

| config id (credentials_per_archetype.yaml)               | real Secret Manager                                                                         | model                        |
| -------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ---------------------------- |
| `bybit-trade-api-key` / `-secret` / `bybit-read-api-key` | `bybit_api_key` / `bybit_api_secret`                                                        | single unscoped key          |
| `binance-trade-api-secret`                               | `binance-trade-api-key-secret`                                                              | scoped, `-key-secret` suffix |
| `deribit-trade-api-secret`                               | `deribit-trade-api-key-secret`                                                              | scoped, `-key-secret` suffix |
| `okx-trade-api-key` / `-secret` / `-passphrase`          | `exec-<client>-okx-api-key` / `-secret` / `-passphrase` (anu, gp, ik, nn, pr, sl, sl2, std) | **per-client**               |
| `hyperliquid-trade-api-key`                              | `hyperliquid-trade-key` (mainnet) / `hyperliquid-testnet-trade-key`                         | non-`-api-` naming           |
| `aster-trade-api-key`                                    | `aster-api-key` / `aster-secret-key`                                                        | single unscoped key          |

(binance/deribit read+trade `-api-key` ids DO match; bybit `bybit_api_key` now matches in `credentials_per_mode.yaml`.)

## Why it matters

- These are the **6 perp-hedge venues** for `carry_staked_basis` — live-DeFi MVP. At runtime, credential resolution for
  csb will look up `okx-trade-api-key` / `hyperliquid-trade-api-key` / `bybit-trade-api-key` etc. that **do not exist**
  in SM → the hedge leg can't authenticate. This is latent (not caught by CI: the archetype config + its tests are
  mutually consistent on the wrong names) but blocks live csb.
- **okx is per-client** (`exec-<client>-okx-*`) — this is the per-client isolation architecture
  (`/codex/04-architecture/per-client-isolation-architecture.md`), not a single shared okx key. The archetype config's
  single `okx-trade-api-key` is architecturally wrong, not just a rename.

## Recommended decision

- Owner: the active **credential-alignment** workstream (whoever owns UAC@2ec9fcf3). `credentials_per_mode.yaml` was
  aligned; `credentials_per_archetype.yaml` + its tests still need the same treatment.
- Clear renames (do as part of that work): bybit→`bybit_api_key`/`bybit_api_secret`; aster→`aster-api-key`/
  `aster-secret-key`; binance/deribit secret suffix→`-trade-api-key-secret`; hyperliquid→`hyperliquid-trade-key`.
- **Architectural (not a rename)**: okx must use the per-client `exec-<client>-okx-*` model — reconcile
  `credentials_per_archetype.yaml` with per-client isolation. Likely the archetype declares a _template_ and the
  per-client resolver fills `exec-<client>-okx-*` at runtime; confirm with the credential resolver design.
- Coordinate — `credentials_per_*.yaml` is being actively edited; do not double-edit.

## Status — RESOLVED (2026-05-24)

- [x] bybit test aligned to real SM id (UAC@728a1353) — unblocks UAC CI
- [x] `credentials_per_archetype.yaml` + tests renamed to real SM ids (UAC@4e3fc932): bybit/aster single key,
      binance/deribit `-trade-api-key-secret`, hyperliquid `-trade-key`, dropped redundant `bybit-read-api-key`; 18/18
      tests pass
- [x] okx reconciled to per-client `pattern:exec-<client>-okx-*` (UAC@4e3fc932) + `credential-probe.sh` expands &
      verifies it per client (deployment-service@c0537bf). **Live-verified**: all 8 clients × {api-key,api-secret,
      passphrase} PASS, plus bybit/binance/deribit/hyperliquid/aster all PASS against real Secret Manager
- [x] No other config/code references the old flat ids (workspace grep clean; only display-mangled docstring examples)

## Wallet `*-wrapped` probe handling — RESOLVED (deployment-service@75fc484)

`credential-probe.sh` treated `<wallet_id>-wrapped` creds as literal SM secrets and FAILed them all. Added
`probe_wrapped_wallet` with the two-regime model from UAC's wallet configs:

- **pre-cutover** (paper/batch/dev) → resolve to the operator's shared wrapped test PK `defi-wallet-private-key-wrapped`
  (`test_wallet_provisioning_pre_cutover.json`) — exists → real PASS. The **`carry_staked_basis` batch gate now reads 32
  PASS / 0 FAIL / 0 SKIP (100%)**.
- **live** → require each wallet's own provisioned PK (`cutover_wallet_provisioning_mainnet_template.json`
  `private_key_secret_ref`); FAIL with explicit `WALLET-PK-UNPROVISIONED (HUMAN-ONLY custody task)` — never fakes PASS.
  Also dropped the helius/coingecko/telegram archetype-config mismatches (UAC@dc15766f).

### Genuinely-remaining (HUMAN-ONLY — operator/custody)

The 15 mainnet wallet PKs (`csb-*`, `apd-*`, `gas-reserve-*`) are **not provisioned** in Secret Manager — only the
shared pre-cutover test key exists. Going LIVE requires wrapping each wallet's private key under the wallets CMK and
storing it as `<wallet_id>-wrapped`. **This is a hard-stop human-only action** (CLAUDE.md) — an agent cannot generate
wallet keys. The live credential gate will correctly stay <100% until the operator provisions these.
