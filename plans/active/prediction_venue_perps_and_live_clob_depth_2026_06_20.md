---
title: Kalshi + Polymarket perpetual futures + live CLOB depth/quotes (funding/basis/dispersion arb)
created: 2026-06-20
author: ikennaigboaka [slot-main·human-planning]
parent_epic: predictions_master
assigned_vm: human-planning
estimate_class: brand-new
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 8
locked_by: live-defi-rollout
---

# Kalshi + Polymarket perps + live CLOB depth

Operator 2026-06-20: Kalshi (May–Jun 2026, 13 CFTC crypto perps BTC+alts) and Polymarket (Apr 21 2026 beta, crypto+stocks, 10–20x) both launched **perpetual futures**. Add them to the universe, map them, download data — for **basis trades, funding-rate arb, and cross-venue dispersion**. Also: historical prediction data is trades-only, but **live we can record CLOB quotes + depth** — capture + dump it live for proper arb backtesting.

## Architecture decision (HARD)

Kalshi/Polymarket **perps are crypto perpetuals with funding** — NOT prediction YES/NO markets. They belong in the **crypto-perp instrument universe** (alongside Binance/Bybit/OKX/Hyperliquid perps), mapping `BTC-PERP`/`ETH-PERP`/… to the **SAME canonical perp instrument** the CeFi venues use → so funding-rate arb + basis + dispersion work cross-venue out of the box. Do NOT route them through the prediction question-group canonical (that's the separate Kalshi-Q&A-parser work, `instruments_mtds_subset_consistency_remediation_2026_06_17.md`). New venue tokens: `KALSHI_PERP` + `POLYMARKET_PERP` (or reuse KALSHI/POLYMARKET with instrument_type=perp — decide in P0 after API research).

## Phase 0 — API research (verify before building; no false premises)

- [ ] [RESEARCH] P0. Document the Kalshi perps API: market/contract list endpoint, trades (historical window), funding-rate endpoint, orderbook/depth (REST + websocket), auth (public read vs RSA-PSS), rate limits. Sources: kalshi.com/perps, help.kalshi.com/collections/19654073, trade-api/v2. Repo: instruments-service (research note in the plan Progress Log, NOT a summary doc).
- [ ] [RESEARCH] P0. Same for Polymarket perps: contract list, trades, funding, CLOB book/depth (REST + ws), auth, limits. Confirm whether perps share the existing Polymarket CLOB/Gamma infra or a new endpoint. Repo: instruments-service.

## Phase 1 — universe + venue mapping (crypto-perp canonical)

- [ ] [UAC] P1. Add KALSHI_PERP + POLYMARKET_PERP venues to the crypto-perp universe + `VENUES_BY_ASSET_GROUP`, with launch dates (Kalshi ~2026-05-29, Polymarket ~2026-04-21) in `venue_launch_dates.py` + `coverage_starts.py`. Map their BTC/ETH/alt perps to the SHARED canonical perp instrument (mirror the CeFi perp instrument universe). Repo: unified-api-contracts.
- [ ] [SCRIPT] P1. instruments-service — perp-contract enumerator for both venues (list contracts → write to the instruments store under the crypto-perp asset_group), mirroring the existing perp/cefi instrument enumeration. Repo: instruments-service.

## Phase 2 — historical download (trades) + funding

- [ ] [SCRIPT] P1. market-tick-data-service — adapters to download Kalshi + Polymarket perp **trades** (historical window) + **funding rates** into the canonical perp schema (mirror the CeFi perp-funding handler `perp_funding_handler.py`). Honest-absence pre-launch (record_empty EXPECTED_PRE_VENUE_LAUNCH before the venue launch date). Repo: market-tick-data-service.

## Phase 3 — LIVE CLOB depth + quotes (the arb-backtest data)

- [ ] [SCRIPT] P1. market-tick-data-service — LIVE websocket connectors recording **CLOB quotes (BBO) + order-book depth** for Kalshi + Polymarket perps (and, where available, their prediction Q&A markets too — historical=trades-only, live=full book). Dump to the canonical live tick schema (book_snapshot/depth), `pipeline_mode=live_<source>`. This is the proper arb-backtest dataset (depth → slippage calibration). Mirror the existing live ws connectors (`live/connectors/`). Repo: market-tick-data-service.
- [ ] [SCRIPT] P2. deployment-service — live-recording launcher + forward-poll for the perp CLOB streams (mirror `launch-prediction-forward-poll.sh`); ensure live=batch schema parity. Repo: deployment-service.

## Phase 4 — arb wiring

- [ ] [DESIGN] P2. strategy-service — wire Kalshi/Polymarket perp funding into the funding-rate-arb + basis archetypes (cross-venue dispersion vs CeFi perps), now that they share the canonical perp instrument. Repo: strategy-service.

## Codex SSOT updates

- [ ] [DOCS] P2. codex/02-data — new prediction-perps sourcing doc; update the prediction/crypto-perp instrument-universe docs to include KALSHI_PERP/POLYMARKET_PERP. Repo: unified-trading-pm.
