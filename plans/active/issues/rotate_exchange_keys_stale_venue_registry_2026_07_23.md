---
doc_type: issue
title: rotate-exchange-keys registry lists ~15 venue secret names that don't match live GCP naming
summary:
  deployment-service/functions/rotate-exchange-keys/main.py's CEFI_KEY_PATTERNS-style venue list predates the two-axis
  secret-naming model (codex/05-infrastructure/secret-manager-naming.md) — most entries (binance-api-key,
  deribit-api-key, okx-api-key, hyperliquid-api-key, etc.) don't match any real GCP secret, so key rotation likely
  silently no-ops for those venues. Found as a byproduct of the 2026-07-23 secret-naming migration; needs its own
  dedicated per-venue verification pass, not a drive-by fix.
status: open
nature: issue
asset_group: [infrastructure, cefi]
stage: [meta]
repos: [deployment-service]
scope: [engineer, admin]
tags: [secret-manager, key-rotation, security, naming]
related: [/codex/05-infrastructure/secret-manager-naming.md]
created: 2026-07-23
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: infra
source: discovered while normalizing Betfair/Polymarket secret naming per operator request
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# rotate-exchange-keys registry lists stale venue secret names

## What was found

While fixing `PolymarketAdapterConfig`/`KalshiAdapterConfig`'s wrong secret-name defaults in execution-service (see
[`secret-manager-naming.md`](/codex/05-infrastructure/secret-manager-naming.md) § 1.2 / § 2.3), the same wrong
`polymarket-api-secret` name turned up in `deployment-service/functions/rotate-exchange-keys/main.py`'s venue key list.
Pulling on that thread: most of the ~29-entry list in that file predates the 2026-07-23 two-axis naming model and does
not match live GCP Secret Manager at all:

| Listed in rotate-exchange-keys                                                  | Real GCP shape (verified 2026-07-23)                                                               |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `binance-api-key` / `-secret`                                                   | `binance-{read,trade,write}-api-key` (+ `-secret` siblings for read/trade)                         |
| `deribit-api-key` / `-secret`                                                   | `deribit-{read,trade,write}-api-key` (+ `-secret` siblings for read/trade)                         |
| `okx-api-key` / `-secret`                                                       | No pooled/house OKX secret exists at all — client-scoped `exec-{client}-okx-*` only                |
| `hyperliquid-api-key` / `-secret`                                               | `hyperliquid-trade-key` (one JSON blob: private_key/wallet_address/main_wallet)                    |
| `polymarket-api-secret`                                                         | `polymarket-secret` (no `-api-` infix)                                                             |
| `coinbase-api-key` / `-secret`, `kraken-*`, `bitfinex-*`, `bitget-*`, `upbit-*` | **Not verified in this pass** — unknown if these venues have ANY provisioned secret under any name |

`bybit-api-key`/`-secret` and `betfair-session-token`/`kalshi-api-key` in the same list DO look consistent with real GCP
names, so this is not a "delete the whole file" situation — it's genuinely mixed.

## Why this matters

If `rotate-exchange-keys` is an active scheduled/triggered rotation function, every listed name that doesn't match a
real secret means rotation silently no-ops (or errors and is swallowed) for that venue — a rotation gap that could
persist indefinitely without anyone noticing, since "key rotation didn't happen" produces no loud failure signal by
default.

## What wasn't done and why

This session fixed the ONE line directly relevant to the Betfair/Polymarket normalization task (`polymarket-api-secret`
→ matches the real name only insofar as it was already being tracked) but did **not** touch the other ~13 stale entries.
Reasons:

- Key rotation is security-sensitive infrastructure — CLAUDE.md's hard-stop domain adjacency (wallet keys / force-push
  main are explicit human-only hard-stops; key rotation isn't listed but sits in the same risk class).
- Fixing 2 lines while leaving ~13 other equally-wrong lines untouched in the same list would be a misleading partial
  fix — a future reader would reasonably assume "this list is now correct" when it isn't.
- Several venues (`coinbase`, `kraken`, `bitfinex`, `bitget`, `upbit`) were never verified against live GCP in this pass
  — need a full per-venue GCP query before touching, same rigor as this session's Binance/Deribit/Bybit/
  Hyperliquid/Polymarket/Kalshi checks.

## Todos

- [ ] [SCRIPT] P1. **Verify every venue in `rotate-exchange-keys/main.py`'s key-pattern list against live GCP Secret
      Manager** (`central-element-323112`) — for each, confirm the referenced secret name(s) actually exist; produce a
      corrected list.
- [ ] [SCRIPT] P1. **Confirm whether `rotate-exchange-keys` is actually invoked on a schedule/trigger** (Cloud Scheduler
      / Cloud Function trigger config) — if it's dead/unwired like the Polymarket/Kalshi adapter stubs were, severity
      drops; if it's live, this is a real rotation gap needing prompt attention.
- [ ] [SCRIPT] P2. **Fix the corrected venue list** in `rotate-exchange-keys/main.py` once verified, matching the
      two-axis model in `codex/05-infrastructure/secret-manager-naming.md`.

## Codex SSOTs

- `codex/05-infrastructure/secret-manager-naming.md` — the two-axis naming model this registry needs to match.
