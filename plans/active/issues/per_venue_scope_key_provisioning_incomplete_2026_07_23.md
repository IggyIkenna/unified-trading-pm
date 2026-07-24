---
doc_type: issue
title: Per-venue read/trade/withdraw scope key provisioning stalled at 2/10 venues
summary: >-
  Phase 2.A/2.C of the archived api_keys_wallets_accounts_readiness plan split into an enforcement half (shipped —
  execution-service's AdapterScope/ScopedCLOBAdapter) and a Secret-Manager-provisioning half (operator-only, marked
  BLOCKED-OPERATOR at archival). Verified live against GCP 2026-07-23 — only Binance + Deribit actually have the
  {venue}-{read,trade,write}-api-key triple; the other 8 venues named in the original plan (Bybit, OKX, Hyperliquid,
  Aster, Upbit, Kraken, Bitfinex, Bitget) still have at most one unscoped/client-scoped key. No active plan currently
  owns finishing this rollout.
status: open
nature: issue
asset_group: [cefi, infrastructure]
stage: [meta]
repos: [execution-service, unified-trading-pm]
scope: [engineer, admin]
tags: [secret-manager, security, scope-separation, cefi]
related:
  [
    /codex/05-infrastructure/secret-manager-naming.md,
    /plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md,
  ]
created: 2026-07-23
parent_epic: execution_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
source:
  discovered while investigating a prior session's "R8" reference during secret-naming reconciliation — that label was a
  misnomer (R8 in the source plan is an unrelated Pyth-on-Solana oracle smoke test); the actual items are Phase 2.A
  ("Per-venue sub-key provisioning") and 2.C ("Per-scope key separation in adapters")
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# Per-venue read/trade/withdraw scope key provisioning stalled at 2/10 venues

## Correction to a prior mislabel

A prior session's investigation referred to this as "the R8 plan." That's wrong — R8 in
`plans/archive/2026_05/api_keys_wallets_accounts_readiness_2026_05_10.md` is Phase 4.E, "Pyth-on-Solana real-data
smoke," unrelated to credential scoping. The actual items are **Phase 2.A** ("Per-venue sub-key provisioning") and
**Phase 2.C** ("Per-scope key separation in adapters"). Use this doc's title/tags to find it going forward, not "R8."

## What's actually shipped vs. not

**Enforcement (Phase 2.C) — shipped, live**: `execution-service`'s `AdapterScope` + `ScopedCLOBAdapter`
(`base_adapter.py`, commit `e3f447e37`) — `get_order_adapter(venue, scope="read"|"trade"|"withdraw")` raises
`UnsupportedOperationError` if a read-scope adapter attempts `place_order`. 20 unit tests, all passing per the original
plan's verification note.

**Provisioning (Phase 2.A) — 2/10 venues as of 2026-07-23, Bybit's code wired same day**: the plan's intended shape was
`<venue>-<scope>-{api-key,api-secret,passphrase}` per venue, for 10 venues (Bybit, Deribit, Binance, OKX, Hyperliquid,
Aster, Upbit, Kraken, Bitfinex, Bitget). Verified live against GCP Secret Manager (`central-element-323112`) 2026-07-23:

| Venue                           | Read/trade/write split?        | Real shape                                                                                                                                                                                                                                                                                                                                                                   |
| ------------------------------- | ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Binance                         | ✅ Yes                         | `binance-{read,trade,write}-api-key` (+ secret siblings for read/trade)                                                                                                                                                                                                                                                                                                      |
| Deribit                         | ✅ Yes                         | `deribit-{read,trade,write}-api-key` (+ secret siblings for read/trade)                                                                                                                                                                                                                                                                                                      |
| Bybit                           | 🟡 Code ready, not provisioned | Currently one unscoped `bybit-api-key`/`bybit-api-secret`; execution-service now prefers `bybit-trade-api-key`/`bybit-trade-api-key-secret` and falls back to the unscoped pair automatically — see checklist below                                                                                                                                                          |
| OKX                             | ❌ Different model             | `exec-{client}-okx-*` (client-scoped only, no pooled/house key at all) — the read/trade/write split doesn't apply the same way to a client-scoped venue; needs its own design, not a copy of the Binance/Deribit pattern                                                                                                                                                     |
| Hyperliquid                     | ❌ Different model             | One wallet-style JSON blob `hyperliquid-trade-key` (EIP-712 agent-wallet signing, not a REST key pair) — "read vs. trade vs. withdraw" would need a different mechanism (e.g. separate agent wallets with different on-chain authorizations), not three secrets                                                                                                              |
| Aster                           | ❌ No execution adapter at all | `aster-api-key`/`aster-secret-key` exist in GCP but are consumed ONLY for MTDS market-data collection — `execution-service`'s venue-dispatch (`factory.py`'s `CCXT_VENUES`/`DIRECT_REST_VENUES`/`TRADFI_VENUES`) has no `aster` entry and no `aster_*.py` adapter file exists. Scope separation is moot until an execution adapter is built — see the build-scope note below |
| Upbit, Kraken, Bitfinex, Bitget | ❌ Zero credentials            | Confirmed 2026-07-23 — no secret under any name exists in GCP for any of these 4 venues (not even an unscoped key). Matches the plan's own 2026-05-17 note that Bitfinex/Bitget were `BLOCKED-CREDENTIALS`; Upbit/Kraken have adapter code and factory dispatch but nothing to authenticate with                                                                             |

The plan's own archival note flagged this as `[BLOCKED-OPERATOR]` — "Agent cannot provision venue sub-keys. Operator
must complete before May-23 cutover" — and it appears that operator step was only carried out for 2 of the 10 named
venues.

## Bybit — provisioning checklist (operator action required)

Create these two secrets in GCP Secret Manager (project `central-element-323112`), sourced from a Bybit API key scoped
to **trading permissions only, no withdrawal permission** (the whole point of the split — a compromised trade-scope key
can't move funds out):

- `bybit-trade-api-key` — the new key's API key value
- `bybit-trade-api-key-secret` — the new key's API secret value

No code change or deploy is needed once these exist — `execution-service`'s `_load_venue_trade_credentials` already
checks for them first and only falls back to the current unscoped `bybit-api-key`/`bybit-api-secret` if they're absent
(execution-service commit pending push, this session). The switch to the scoped key happens automatically the next time
the service reads Secret Manager.

## Aster — execution adapter doesn't exist; build-scope estimate

Aster has no execution path today, so "add scope separation" doesn't apply until an adapter is built. Good news: **CCXT
already has a working `aster` connector** (`ccxt.async_support.aster`, standard `apiKey`/`secret` `requiredCredentials`
— no Hyperliquid-style special handling needed), so this would follow the same CCXT-wrapper pattern already used for
`upbit_ccxt.py` (403 lines) / `hyperliquid_ccxt.py` (503 lines), NOT a from-scratch native REST client like
`bitfinex_native.py`/`bitget_native.py` (~370-420 lines each, built natively because CCXT support was inadequate for
those two at the time).

Scope for a real `aster_ccxt.py`:

- New adapter file mirroring `upbit_ccxt.py`'s shape (place/cancel order, fetch balance/positions/fills, sim-mode
  support).
- Add `"aster"` to `factory.py`'s `CCXT_VENUES` + a dispatch branch in `_create_ccxt_adapter()`.
- Add an `aster` case to `live_execution_handler.py`'s `_load_venue_trade_credentials` (the secrets already exist:
  `aster-api-key`/`aster-secret-key`, just need a service_config.py field + wiring — no new GCP provisioning needed for
  a first, unscoped-key version).
- Unit tests mirroring the existing CCXT-adapter test suites (~35-40 tests based on `test_hyperliquid_ccxt.py`'s count).
- Estimated at roughly 1 day of focused work (refactor-tier — following an established pattern, not novel design).

## Why this matters

If per-scope key separation is a genuine security control the operator still wants (the stated rationale: "a compromised
read-key shouldn't be able to withdraw funds"), most target venues currently have no scope separation at the credential
level — the `ScopedCLOBAdapter` enforcement layer works, but there's only one key to enforce scopes _against_ for those
venues, so a compromised single key still has full withdraw capability regardless of what scope the caller requests.

## What this issue does NOT resolve

- Whether OKX/Hyperliquid warrant their own scope-separation designs, and what those designs should look like.
- Whether Upbit/Kraken/Bitfinex/Bitget are still wanted as trading venues at all, given zero credentials months after
  the original plan targeted them.
- Whether building the Aster execution adapter is worth prioritizing given it currently has zero trading volume (no
  adapter exists to have generated any).

All three are real design/priority calls, not something determinable from code or docs alone.

## Todos

- [x] [SCRIPT] P2. **Verify Upbit/Kraken/Bitfinex/Bitget's live GCP secret shape** — done 2026-07-23, zero credentials
      confirmed for all 4 (table above).
- [x] [AGENT] P2. **Wire Bybit's trade-scope credential lookup with safe fallback** — execution-service
      `_load_venue_trade_credentials` now prefers `bybit-trade-api-key`/`-secret`, falls back to the unscoped pair; 3
      new unit tests.
- [ ] [HUMAN] P1. **Create `bybit-trade-api-key`/`bybit-trade-api-key-secret`** in GCP per the checklist above — the one
      remaining step to actually complete Bybit's scope split.
- [ ] [HUMAN] P2. **Decide on OKX/Hyperliquid's scope-separation design**, if wanted at all, since neither fits the
      Binance/Deribit pattern.
- [ ] [HUMAN] P3. **Decide whether to build the Aster execution adapter** (scoped above) and/or provision
      Upbit/Kraken/Bitfinex/Bitget credentials, given none of the 5 currently have any live trading volume.

## Codex SSOTs

- `/codex/05-infrastructure/secret-manager-naming.md` § 2.2 — the live read/trade/write split pattern for
  Binance/Deribit, and the note distinguishing this real pooled/house pattern from the dead per-client
  `exec-{client}-{venue}-{read,trade,withdraw}-*` design the archived plan originally also described.
