---
doc_type: issue
title:
  "OPERATOR DECISION: canonicalize instrument_id format everywhere it currently diverges — dated-derivative raw
  prefixes, DEX-pool bare addresses, PERP-vs-PERPETUAL key/field mismatch, a misspelled venue-token duplicate"
summary:
  "While backfilling real instrument_id samples into the instruments-definitions mockup (2026-07-08), found that
  instrument_id format is NOT actually canonical across the workspace — `canonical_id_builder.py` reads as the intended
  SSOT but has exactly one real caller (Polymarket), so every venue builds its own ID ad hoc. Operator reviewed one
  concrete case (KRAKEN-FUTURES:FUTURE:FF_XBTUSD_260731 — Kraken's raw, uncleaned prefix, vs the SAME venue's PERPETUAL
  which DOES get cleaned to BTC-USDT) and decided: yes, canonicalize — full scope, not just Kraken. This doc is the
  operator decision + the enumerated real scope, mirroring
  [[defi_lending_atoken_debttoken_instrument_split_2026_07_07]]'s pattern (a real, decided target-state, current-state
  vs target-state framing in the mockup, staged migration to follow — not fixed today)."
status: open
nature: notes
asset_group: [cefi, defi]
stage: [data, meta]
repos: [instruments-service, unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags:
  [
    instrument-id,
    canonicalization,
    instrument-identity,
    dated-derivatives,
    dex-pool,
    perp-vs-perpetual,
    honest-coverage,
  ]
related:
  [
    ../instruments_completion_tracker_2026_07_06.md,
    adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08.md,
    defi_lending_atoken_debttoken_instrument_split_2026_07_07.md,
  ]
created: 2026-07-08
parent_epic: instruments_master
priority: P2
source:
  'Operator, 2026-07-08, reviewing the KRAKEN-FUTURES:FUTURE entry in the drilldown mockup: "but that doesnt tell us we
  ARE moving to canonical everywhere" — then explicitly chose "Yes, decide it now — full scope" when offered the choice
  between leaving this as an unscoped finding vs a real decided target-state.'
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: local-only
model_tier: sonnet-doable
thinking_tier: medium
estimate_class: research
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4.8
last_updated: 2026-07-08
supersedes:
superseded_by:
depends_on:
assigned_role: data_engineering
drift_direction: advance-code
locked_since:
---

> **OPERATOR DECISION 2026-07-08 — target-state only, not fixed today.** Every finding below gets a canonical target
> format. None of the target formats exist in production yet — this doc (and the mockup entries it backs) show
> current-real vs target-canonical side by side, same pattern already applied to the A_TOKEN/DEBT_TOKEN decision.
> Actually migrating is staged, future work — this doc scopes it, it doesn't execute it.

## The 6 real divergences found, and their target canonical format

All verified against real `prod/catalog.parquet` reads (both `cefi` and `defi` asset groups), 2026-07-08.

1. **Dated-derivative raw venue prefixes never get cleaned, unlike the same venue's PERPETUAL.**
   `KRAKEN-FUTURES:FUTURE:FF_XBTUSD_260731` (Kraken's own raw `FF_`/`FI_` prefix, unstripped) vs the same venue's
   `KRAKEN-FUTURES:PERPETUAL:ACH-USD` (Kraken's raw `PF_ACHUSD` IS cleaned — prefix stripped, dash inserted).
   `BINANCE-FUTURES:FUTURE:BTCUSDT_260925` (raw concatenated + underscore-date) vs the same venue's
   `BINANCE-FUTURES:PERPETUAL:BTC-USDT` (cleaned). **Target**: `VENUE:FUTURE:BASE-QUOTE-margin_type-YYYYMMDD` for venues
   where margin type needs disambiguating (matching `canonical_id_builder.py`'s own already-written `_build_future` v6
   dash convention, e.g. `KRAKEN-FUTURES:FUTURE:XBT-USD-inverse-20260731`), or plain `VENUE:FUTURE:BASE-QUOTE-YYYYMMDD`
   where margin type is unambiguous.

2. **DEX-pool instrument_id is a bare on-chain pool address, zero VENUE:TYPE:SYMBOL structure, confirmed across 6,180
   real rows / 13 protocols (Uniswap V2/V3/V4, Balancer, Curve, PancakeSwap_V3, Sushiswap/\_V3, Camelot_V3,
   Aerodrome_V3, TraderJoe_V2, Velodrome_V2, GMX) — zero exceptions.** Real:
   `0x00822ba38a39b79cbc5b7f62ba1a6886a45f9e4c` (venue/chain/base_asset live in separate columns instead). **Target**:
   `VENUE-CHAIN:POOL:TOKEN0-TOKEN1[-FEE_TIER]` (matching `canonical_id_builder.py`'s own `_build_defi` docstring
   example, `UNISWAP_V3-ETHEREUM:POOL:USDC-WETH-500`) — pool_address stays as its own column for on-chain lookups, it
   just stops being the _entire_ identity key.

3. **The 5 on-chain-perp venues (HYPERLIQUID/ASTER/PACIFICA-SOLANA/EXTENDED-STARKNET/LIGHTER-ZKSYNC) all store
   instrument_type=PERPETUAL as the field but embed PERP (not PERPETUAL) in the instrument_id key** — consistent across
   all 5, but disagreeing with both the field and CeFi's own `PERPETUAL`-in-key convention (e.g.
   `BINANCE-FUTURES:PERPETUAL:BTC-USDT`). **Target**: `VENUE:PERPETUAL:...` everywhere, dropping the `PERP` shorthand.

4. **Base-quote normalization is inconsistent even within that same 5-venue on-chain-perp cluster.** Real:
   HYPERLIQUID/LIGHTER-ZKSYNC use a bare symbol (`HYPERLIQUID:PERP:BTC`, no quote at all), ASTER uses the raw
   concatenated exchange symbol (`ASTER:PERP:BTCUSDT`, no dash), PACIFICA-SOLANA's quote segment is literally the string
   `PERP` (`PACIFICA-SOLANA:PERP:SOL-PERP`, not a currency), and EXTENDED-STARKNET is the only one already
   dash-normalized with a real currency (`EXTENDED-STARKNET:PERP:ETH-USD`). **Target**: `VENUE:PERPETUAL:BASE-QUOTE`
   with a real settlement currency for all 5 — e.g. `ASTER:PERPETUAL:BTC-USDT`, `HYPERLIQUID:PERPETUAL:BTC-USD`,
   `PACIFICA-SOLANA:PERPETUAL:SOL-USDC`, `LIGHTER-ZKSYNC:PERPETUAL:BTC-USDC` (exact quote currency per venue TBD at
   implementation time — these are illustrative, not independently re-verified per-venue settlement asset).

5. **AAVE_V3-OPTIMISM has a misspelled venue-token duplicate** — `AAVEV3-OPTIMISM` (missing underscore, 4 real rows)
   coexists with the correctly-spelled `AAVE_V3-OPTIMISM` (12 real rows), fragmenting the real per-chain reserve set
   into 2 disjoint keys invisible to anything querying the correct prefix. **Target**: consolidate all rows under
   `AAVE_V3-OPTIMISM` only; the misspelled variant is retired, not migrated (it's a typo, not a distinct entity).

6. **MORPHO's market-address disambiguator uses a 3rd colon inside the symbol** —
   `MORPHO-BASE:LENDING_MARKET:USDC-EURC:0x305dd1` — colon is the reserved top-level `VENUE:TYPE:SYMBOL` delimiter, so a
   3rd colon is ambiguous to any naive `split(":")` parser. **Target**: dash-separate instead, matching the
   pool-fee-tier fix already applied elsewhere — `MORPHO-BASE:LENDING_MARKET:USDC-EURC-0x305dd1`.

## What this is NOT

- Not a claim that any of these 6 are fixed today — every target format above is illustrative only, shown in the mockup
  as an explicit "NOT REAL — target canonical" 3rd sample alongside the real captured ones, same visual pattern as the
  A_TOKEN/DEBT_TOKEN decision's current-state-vs-target-state entries.
- Not a complete enumeration — this session's real-catalog reads covered CeFi + DeFi only (not TradFi/Sports/
  Prediction), and only the venues/protocols already touched by this session's other findings. A dedicated audit pass
  would likely find more instances of the same 6 divergence classes elsewhere.
- Not asking for `canonical_id_builder.py` itself to become the enforced single builder as part of this decision —
  that's a separate, larger refactor question (does every adapter route through one shared function, or do per-domain
  builders exist but each still individually canonicalize). This doc scopes the FORMAT decision; the
  implementation-architecture decision (one builder vs many) is still open.

## Todos

- [ ] [DECISION] P2. **Confirm exact target quote-currency per on-chain-perp venue** (finding 4) — ASTER/PACIFICA/
      LIGHTER-ZKSYNC's real settlement currency needs a quick per-venue API check before the illustrative targets in
      this doc become real implementation targets (e.g. confirm ASTER really settles BTC-USDT in USDT, not some other
      stable).
- [ ] [SCRIPT] P2. **Scope the actual migration mechanics** — for each of the 6 findings, does correcting instrument_id
      require a backfill/rewrite of historical GCS rows (breaking existing joins/manifest keys), or can it be a
      go-forward-only change (old rows keep the legacy format, new rows use canonical, readers handle both)? This
      determines whether this is a cheap relabel or a real migration with downtime/backfill cost.
- [ ] [VERIFY] P2. **Check whether the manifest / deployment-api key off instrument_id VALUE anywhere** (as opposed to
      just the instrument_type field, already checked in
      [[adapter_findings_gcs_manifest_deployment_api_reconciliation_gap_2026_07_08]]) — if any downstream consumer
      pattern-matches or parses the instrument_id string itself (e.g. extracting margin type from a `-inverse-`
      substring), changing the format is a breaking change for that consumer, not just a cosmetic cleanup.
- [ ] [DECISION] P3. **Decide the builder-architecture question** (see "What this is NOT" above) — one shared
      `canonical_id_builder.py`-style function across all adapters, vs many per-domain builders that each independently
      canonicalize consistently. Affects how much of this fix is one PR vs N per-adapter PRs.

## Progress Log

- **2026-07-08** — Filed after the operator reviewed the KRAKEN-FUTURES:FUTURE mockup entry (which showed real-vs-
  illustrative-canonical as a bare 3rd sample row with no decision attached) and asked directly whether the workspace is
  actually moving to canonical everywhere. Given the choice between leaving it unscoped vs deciding now with full scope,
  operator chose full scope. All 6 divergences enumerated here were already discovered during this session's mockup
  backfill pass (2026-07-08) — this doc is the first time they're captured as a decided target-state rather than
  scattered mockup bug notes. No implementation work done yet; migration mechanics are an open todo.
