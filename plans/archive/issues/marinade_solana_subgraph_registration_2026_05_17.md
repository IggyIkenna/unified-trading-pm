---
doc_type: issue
title: Marinade (Solana mSOL) historical APR coverage — subgraph registration / Helius enrich
summary:
status: resolved
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-17
author: ikenna-slot-3
source:
  [
    plans/active/issues/lst_apr_sourcing_method_validated_2026_05_14.md P2 follow-up action item,
    plans/active/solana_lst_native_staking_adapters_2026_05_14.md (companion),
  ]
locked_by: live-defi-rollout
locked_since: 2026-05-17
resolved: 2026-05-20
severity: P2 — Tier 2 mSOL historical coverage; not blocking carry_staked_basis paper trade gate
---

> **🟢 RESOLVED 2026-05-20** — operator picked **Option (b) Helius archive paid tier**. Credentials are already in place
> per ikenna 2026-05-20. mSOL historical APR will source from Helius RPC archive endpoint. Successor implementation
> lands in MTDS solana defi handler (Phase D4 MTDS preflight beef-up of mega audit). Archiving.

## What I found

Per `lst_apr_sourcing_method_validated_2026_05_14.md` § "Plan-flip checkboxes" P2 DESIGN item, Marinade (mSOL) lacks the
historical coverage other LSTs have:

- **Lido (stETH)** — full on-chain `exchangeRate()` history via Ethereum mainnet RPC (Alchemy free tier works back to
  2020-12-19, contract genesis).
- **RocketPool (rETH)** — same shape, full history via mainnet RPC.
- **Coinbase (cbETH)** — public unauth `https://api.exchange.coinbase.com/wrapped-assets/CBETH` endpoint, full history.
- **JitoSOL** — Jito Kobe API + Solana RPC via Helius (operator-vaulted 2026-05-15 + `market-tick-data-service@4cea371`
  wired native_staking handler).
- **mSOL (Marinade)** — **TIER 2 GAP**: Marinade's on-chain pool state has a `m_sol_to_sol_ratio` field that updates per
  epoch, but the historical sequence requires either:
  1. Marinade's own subgraph (registered with The Graph — needs operator account / API key for sustained quota), OR
  2. Helius RPC archive history at the Marinade state PDA (Solana state-history paid tier).

Free public endpoint Marinade exposes (https://api.marinade.finance/) is rate-limited + only returns CURRENT pool state
— no historical APR time series. Confirmed via slot-3 manual probe 2026-05-17.

## Why it matters

`carry_staked_basis` archetype § "LST-margin venue table" (codex
`09-strategy/architecture-v2/archetypes/carry-staked-basis.md` line 115-118) declares DRIFT-SOLANA as the mSOL
margin-eligible venue with a 10% haircut. The strategy backtest needs:

- mSOL historical APR (per-epoch, ~2-day cadence) for entry/exit signal decisions
- mSOL vs SOL price-spread time series for the carry leg P&L

Without Tier 2 coverage, mSOL slots fall back to a static APR assumption (declared in codex as "approximate ~6.5%")
instead of the per-epoch realised rate. This is acceptable for **paper trade** but NOT for May-23 live cutover if mSOL
is in the active universe.

## Recommended decision

**Operator decision needed**:

1. **Path A — Marinade subgraph via The Graph**:
   - Sign up at `https://thegraph.com/studio/` (free tier: 100k queries/month sufficient for daily historical pull)
   - Find the Marinade subgraph slug (search: `marinade-finance` or `marinade-solana`)
   - Store key in Secret Manager as `the-graph-api-key`
   - Slot-3 wires the new adapter in `market-tick-data-service/.../adapters/defi/lst_marinade_adapter.py` (~2-3 hours
     work)

2. **Path B — Helius archive state-PDA queries**:
   - Operator already vaulted `helius-api-key`. Confirm tier covers Solana state-history queries (Developer $49/mo tier
     — likely yes, free tier — no).
   - Slot-3 wires Helius `getProgramAccounts` queries against Marinade state PDA per Slot 2 state-snapshot pattern in
     `mtds_native_staking` handler (~3-4 hours).

3. **Path C — declare mSOL OUT-OF-SCOPE for May-23**:
   - Document mSOL as `BLOCKED-CREDENTIALS-POST-CUTOVER` in `master_to_live_defi_2026_05_23.md`.
   - JitoSOL covers Solana LST margin-eligible for May-23.
   - mSOL becomes post-cutover work via either Path A or Path B.

**Default if no operator response by 2026-05-19**: Path C (out-of-scope; JitoSOL covers Solana LST for May-23).
Plan-flip lst_apr_sourcing P2 DESIGN item as `BLOCKED-OPERATOR-DECISION` until then.

## Cross-references

- Parent: `plans/active/issues/lst_apr_sourcing_method_validated_2026_05_14.md` § "Plan-flip checkboxes"
- Companion: `plans/active/solana_lst_native_staking_adapters_2026_05_14.md` (JitoSOL canonical path)
- Codex archetype: `/codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md` § "LST-margin venue table"

execution: owner: operator (Path decision) → slot-3 (wire-in once decided) cadence: one-shot verifier: mSOL APR parquet
emitted to gs://lst-rates-{pid}/raw_tick_data/by_date/day=\*/asset_group=defi/venue=MARINADE/chain=SOLANA/...
last_executed: NEVER
