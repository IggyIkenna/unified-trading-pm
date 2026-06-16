---
scope: [engineer, admin]
---

# External Data Is Always Available — Never Silently Defer Adapters (HARD RULE)

> **CLAUDE.md anchor**: "External Data Is Always Available — Never Silently Defer Adapters (HARD RULE codified
> 2026-05-14)".
>
> **Codified 2026-05-14** to prevent silent adapter deferrals when "free tier exhausted" or "no public API" is used as
> justification for scope removal. For every asset_group and every MVP archetype, **data exists**. The unblock is
> credentials, not adapter removal.

## The Premise

For every asset_group and every MVP archetype, **data exists**. If the public/free path is exhausted, the unblock is a
credential / subscription / account-provisioning ask to the operator — NOT a license to defer or descope the adapter.
Applies workspace-wide; primary targets are `instruments-service` and `market-tick-data-service` (MTDS)
adapters/handlers/clients, but the rule generalises (DeFi protocol-rate readers, sports/prediction feed adapters, tradfi
vendor SDKs, on-chain RPC providers).

## Banned Reasoning Patterns

Every one of these is a violation if it leads to scope removal:

- "No public API for X" → there's a paid tier (Helius for Solana, Alchemy paid for high-rate,
  Glassnode/Kaiko/IntoTheBlock for on-chain analytics, Tardis for historical CEX ticks, Databento/Polygon.io for tradfi,
  Sportradar/Footystats/The-Odds-API for sports).
- "Free tier exhausted" → upgrade the tier; this is a sub-1-hour operator credential swap, not a multi-week scope cut.
- "No test data" → mock the API contract from public docs + integration-test against the live endpoint once credentials
  land.
- "Subscription required" → that's the unblock, not the blocker. Ping operator.
- "Couldn't reproduce in sandbox" → ship the adapter, gate the integration test behind a `requires_credentials` mark.

## Required Action When Agent Hits This Wall

1. **Build the adapter scaffold anyway.** Schema + UAC contract + auth shape + retry/backoff/rate-limit semantics +
   error classification (`classify_venue_error()`) + manifest emission per writegate Phase 6.x. Unit tests against mocks
   (per docs). Integration tests marked `@pytest.mark.requires_credentials` + skipped by default.
2. **File a `pings/slot_<N>.md` operator-credential request** with exact shape:
   ```
   CREDENTIAL APPROVAL REQUEST — <adapter_name>
   Vendor: <name + tier + cost estimate>
   What I need: <API key | OAuth flow | account email + signup | hardware-2FA setup>
   Account to use: <existing operator email | new account needed>
   Unblocks: <list of asset_group × archetype combos + which May-23 gate>
   Without it: integration tests skip; unit + scaffold ship + adapter is dormant
   ```
3. **Adapter stays ON the live list.** Status = `BLOCKED-CREDENTIALS`, NOT `DEFERRED` and NOT `POST-CUTOVER`. Plan-flip
   is `- [ ] [BLOCKED-CREDENTIALS — pinging operator]` not a checkbox flip.
4. **Cross-link in master plan.** Add row to `master_to_live_defi_2026_05_23.md` § "Credential asks awaiting operator"
   so it's visible in the daily inventory regenerator. (Section auto-created if absent.)
5. **Never move the adapter to a post-cutover plan without explicit operator [ack]** on the slot ping. Silent deferral =
   blocked PR.

## Status Taxonomy (closed set)

Replaces ad-hoc "deferred" language:

- `BLOCKED-CREDENTIALS` — has named operator ask; waits for [ack]; adapter scaffold + unit tests still ship in same
  logical unit
- `BLOCKED-OPERATOR-DECISION` — closed-set design call needed (e.g. which vendor among 3 candidates); waits on operator
  pick
- `BLOCKED-UPSTREAM-OUTAGE` — third-party degraded; ping logged; auto-resumes on health check
- `DEFERRED` — only valid with NAMED successor plan in `plans/active/` + operator-acked migration line in current plan

## MVP Archetype × Asset-Group Coverage Target (May-23 gate)

Every cell in this matrix has a working batch adapter (either green or `BLOCKED-CREDENTIALS` with named ask):

|                              | DeFi                                                                                                       | CeFi (perp + spot)                                                             | TradFi                     | Sports                                  | Prediction                              |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ | -------------------------- | --------------------------------------- | --------------------------------------- |
| `carry_staked_basis`         | LST APRs (Lido stETH / RocketPool rETH / Coinbase cbETH / Solana JitoSOL / mSOL); Aave/Compound base rates | Perp funding (Binance/Bybit/OKX/Deribit/Hyperliquid/Aster/Kraken); spot prices | n/a                        | n/a                                     | n/a                                     |
| `arbitrage_price_dispersion` | DEX prices (Uniswap V3 / Curve / Balancer / Sushi / PancakeSwap / Phoenix / Orca / Raydium / Drift)        | CEX spot + perp marks (all 7+ venues)                                          | (optional) Databento ticks | (optional) odds dispersion across books | (optional) Polymarket vs Kalshi spreads |

Sports + Prediction tracks have parallel coverage targets independent of the DeFi archetypes.

## Enforcement

- Plan reviewer rejects any plan that contains "DEFERRED — no data" / "no API access" / "post-cutover — credentials"
  without an operator [ack] ping link.
- Inventory regenerator surfaces `BLOCKED-CREDENTIALS` count as a master plan column.
- QG STEP TBD scans `pyproject.toml` extras + adapter docstrings for un-acked credential asks (future codification).

## Composes With

- **Findings Triage** — this rule is the per-data-source case of "fix now if you have context"
- **Capture Discoveries As Plan Todos** — the ping IS the discovery capture
- **Commit + Push + Flip** — the `BLOCKED-CREDENTIALS` status is the plan-flip equivalent
- **Plans Run To Actual Completion** — the adapter doesn't run to completion without credentials → credentials are the
  operationally-shipped definition
