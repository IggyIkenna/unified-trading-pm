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

**Provisioning (Phase 2.A) — 2/10 venues, not touched since 2026-05**: the plan's intended shape was
`<venue>-<scope>-{api-key,api-secret,passphrase}` per venue, for 10 venues (Bybit, Deribit, Binance, OKX, Hyperliquid,
Aster, Upbit, Kraken, Bitfinex, Bitget). Verified live against GCP Secret Manager (`central-element-323112`) 2026-07-23:

| Venue                           | Read/trade/write split?      | Real shape                                                              |
| ------------------------------- | ---------------------------- | ----------------------------------------------------------------------- |
| Binance                         | ✅ Yes                       | `binance-{read,trade,write}-api-key` (+ secret siblings for read/trade) |
| Deribit                         | ✅ Yes                       | `deribit-{read,trade,write}-api-key` (+ secret siblings for read/trade) |
| Bybit                           | ❌ No                        | One unscoped `bybit-api-key`/`bybit-api-secret`                         |
| OKX                             | ❌ No (client-scoped only)   | `exec-{client}-okx-*`, no pooled/house key at all                       |
| Hyperliquid                     | ❌ No                        | One wallet-style JSON blob `hyperliquid-trade-key`                      |
| Aster                           | ❌ No                        | One unscoped `aster-api-key`/`aster-secret-key`                         |
| Upbit, Kraken, Bitfinex, Bitget | **Not checked in this pass** | Unknown — need live GCP verification                                    |

The plan's own archival note flagged this as `[BLOCKED-OPERATOR]` — "Agent cannot provision venue sub-keys. Operator
must complete before May-23 cutover" — and it appears that operator step was only carried out for 2 of the 10 named
venues (or the other 8 venues never needed per-scope separation and the plan's venue list was aspirational; this issue
doesn't resolve which).

## Why this matters

If per-scope key separation is a genuine security control the operator still wants (the stated rationale: "a compromised
read-key shouldn't be able to withdraw funds"), 8 of 10 target venues currently have no scope separation at the
credential level — the `ScopedCLOBAdapter` enforcement layer works, but there's only one key to enforce scopes _against_
for those 8 venues, so a compromised single key still has full withdraw capability regardless of what scope the caller
requests.

## What this issue does NOT resolve

Whether the operator still wants this for all 8 remaining venues is a real design/priority call, not something
determinable from code or docs alone — flagging for a decision, not prescribing one.

## Todos

- [ ] [HUMAN] P2. **Decide whether per-venue scope-key provisioning should be revived** for the remaining 8 venues (or a
      subset), and if so, whether it's still a priority given only Binance/Deribit trade live volume today.
- [ ] [SCRIPT] P2. **Verify Upbit/Kraken/Bitfinex/Bitget's live GCP secret shape** (not checked in the 2026-07-23 pass)
      to complete the picture above.
- [ ] [SCRIPT] P3. **If revived**: provision `{venue}-{read,trade,write}-api-key` (+ secret siblings) for the chosen
      venues, following the pattern already live for Binance/Deribit — operator-side Secret Manager provisioning,
      agent-side wiring to `get_market_data_adapter()`/`get_withdraw_adapter()` (already built, per Phase 2.C).

## Codex SSOTs

- `/codex/05-infrastructure/secret-manager-naming.md` § 2.2 — the live read/trade/write split pattern for
  Binance/Deribit, and the note distinguishing this real pooled/house pattern from the dead per-client
  `exec-{client}-{venue}-{read,trade,withdraw}-*` design the archived plan originally also described.
