---
title: Crypto-venue single-stock perps + tokenized stocks (Binance/OKX/Bybit) — equity basis/dispersion arb
created: 2026-06-20
parent_epic: cefi_master
assigned_vm: human-planning
estimate_class: brand-new
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 6
locked_by: live-defi-rollout
priority: P2
status: active
---

# Crypto-venue equity perps + tokenized stocks

Operator 2026-06-20: crypto venues now list **single-stock perpetuals + tokenized stocks** — opportunity surface for equity basis/dispersion arb. Verified (web, 2026-06):
- **Binance**: 7,000 US stocks/ETFs + tokenized **bStocks**; single-stock perps incl. `SPCXUSDT` (SpaceX, its #2 product), Meta/NVDA/GOOG 24/7; US stock service live 2026-06-01.
- **OKX**: 17 US equity perpetual contracts (24/7) + Samsung/SK Hynix/Hyundai + **pre-IPO perps**.
- **Bybit**: stock perps (TSLA/AAPL) + `AAPLX` tokenized.

## Architecture decision (HARD)
Crypto-venue equity perps/tokenized-stocks are derivatives TRACKING a real equity → map to the **SAME canonical equity instrument** as the Databento (DBEQ.BASIC) real equity, as new venue×instrument cells, so **basis/dispersion arb (crypto-venue stock-perp vs real equity) + 24/7-vs-market-hours overnight-gap arb** work cross-venue. Funding-bearing perps also map to the crypto-perp funding canonical (sister of `prediction_venue_perps_and_live_clob_depth_2026_06_20.md`). **Pre-IPO / SpaceX** instruments have NO real-equity twin → standalone canonical (no basis leg, dispersion only across crypto venues).

## Phase 0 — research + opportunity sizing
- [ ] [RESEARCH] P0. Per venue (Binance/OKX/Bybit), document: equity-perp + tokenized-stock contract list endpoint, symbol↔real-ticker mapping (SPCXUSDT→SPACEX, AAPLX→AAPL), trades/funding/orderbook-depth endpoints (REST+ws), 24/7 vs market-hours, auth, rate limits. Identify which symbols HAVE a Databento real-equity twin (basis-arb-able) vs pre-IPO/uniques (dispersion-only). Repo: instruments-service (findings → plan Progress Log).
- [ ] [RESEARCH] P1. Tardis coverage check — do our existing Tardis/CeFi feeds already carry these equity-perp symbols (so historical comes free via the existing CeFi pipeline) or is a new fetch path needed?

## Phase 1 — universe + canonical mapping
- [ ] [UAC] P1. Add the equity-perp / tokenized-stock symbols to the crypto-perp/cefi instrument universe with a `tracks_equity=<canonical ticker>` link to the Databento equity canonical (mirror `cme_polymarket_link.py` cross-venue-link pattern). Venue tokens already exist (BINANCE/OKX/BYBIT) — new instrument_type (`equity_perp` / `tokenized_equity`). Repo: unified-api-contracts.

## Phase 2 — download (likely rides existing CeFi pipeline)
- [ ] [SCRIPT] P1. market-tick-data-service — if Tardis/CeFi feeds carry these symbols, just add them to the CeFi venue universe (trades + funding + book already handled by the CeFi adapters); else add a fetch path. Verify historical + live. Repo: market-tick-data-service.

## Phase 3 — live CLOB depth (shared with the prediction-perps plan's Phase 3)
- [ ] [SCRIPT] P2. Live BBO+depth recording for these equity perps (for basis-arb slippage calibration) — reuse the CeFi live-ws book connectors. Repo: market-tick-data-service.

## Phase 4 — arb wiring
- [ ] [DESIGN] P2. strategy-service — equity basis/dispersion archetype: crypto-venue stock-perp vs Databento real equity (basis), cross-crypto-venue (dispersion), 24/7-vs-market-hours overnight gap. Repo: strategy-service.

## Codex SSOT updates
- [ ] [DOCS] P2. codex/02-data + codex/09-strategy — crypto-venue equity-perp sourcing + the equity-basis arb archetype. Repo: unified-trading-pm.
