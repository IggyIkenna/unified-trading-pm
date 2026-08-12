---
doc_type: plan
title: Add OKX + Bybit tokenized equities to MVP instruments/catalogue — IS registration from real listing dates
summary: >-
  Register OKX and Bybit's tokenized-equity SPOT products (e.g. Bybit AAPLX) as MVP-scoped instruments in the UAC
  catalogue and instruments-service, using each symbol's REAL historical listing date (not a blanket floor) — separate
  from and complementary to the already-in-flight equity-PERP backfill in
  cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md, which is at its 1000-line hard cap and cannot absorb this
  new scope directly.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [instruments-service, unified-api-contracts, market-tick-data-service]
scope: [engineer, admin]
tags: [cefi, tokenized-equity, okx, bybit, mvp-scope, instrument-catalogue]
related:
  [
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    /codex/02-data/cefi-capture-universe.md,
    /codex/02-data/mvp-scope-canonical.md,
  ]
created: 2026-08-12
last_updated: 2026-08-12
parent_epic: cefi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: research
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source:
  "Operator ask, 2026-08-12 interactive session, following the OKX/Bybit equity-perp listing-date research done the same
  session"
resolved_by:
locked_by:
locked_since:
context_scope:
  [
    /plans/active/cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md,
    unified-api-contracts/unified_api_contracts/registry/venue_launch_dates.py,
    unified-api-contracts/unified_api_contracts/canonical/crosscutting/crypto_equity_link.py,
  ]
---

# Add OKX + Bybit tokenized equities to MVP instruments/catalogue

## Why this is a separate plan, not a section in the equity-perps doc

`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` is the existing SSOT for crypto-venue single-stock perps +
tokenized stocks and already covers Binance/OKX/Bybit **equity PERPS** (that backfill launch is in-flight as of
2026-08-12, dispatched separately). It is at **999 of its 1000-line hard cap** — no room to extend. This plan covers the
narrower, distinct **tokenized-equity SPOT** product class (Bybit `AAPLX`-style tokens; OKX's equivalent, if confirmed
to exist — see Todo 1) — a different `instrument_type` (`SPOT_PAIR`, not `PERPETUAL`) with its own listing-date research
and MVP-tagging needs.

## What's already known (2026-08-12 research, this session)

- **Bybit**: confirmed has tokenized-equity spot products, `AAPLX` being the named example in prior research
  (`cryptovenue_equity_perps_and_tokenized_stocks_2026_06_20.md` line 57: "stock perps (TSLA/AAPL) + `AAPLX`
  tokenized"). Full symbol list and per-symbol listing dates NOT yet gathered — Todo 1.
- **OKX**: prior research documents "17 US equity perpetual contracts... + pre-IPO perps" but does **not** confirm a
  tokenized-equity SPOT offering distinct from the perps — unverified, needs a live API check (Todo 1) before assuming
  OKX has this product class at all.
- **Equity-perp listing dates** (a related but DISTINCT product, gathered this session for cross-reference, NOT the
  scope of this plan): OKX TSLA/AMZN-USDT-SWAP 2026-02-25/26, NVDA/GOOGL/MSFT/AAPL/META/SPY-USDT-SWAP 2026-03-04; Bybit
  META/GOOGL/MSFT-USDT 2026-04-27, AMZN/AAPL-USDT 2026-04-28, NVDA-USDT 2026-05-06 — live-queried via
  `GET .../api/v5/public/instruments?instType=SWAP` (OKX) and `GET .../v5/market/instruments-info?category=linear`
  (Bybit). Reuse this exact method for the tokenized-equity SPOT query in Todo 1 (swap `instType=SWAP`→`SPOT` /
  `category=linear`→`spot`).

## Todos

- [ ] [RESEARCH] P1. Live-query OKX's SPOT instruments endpoint
      (`GET     https://www.okx.com/api/v5/public/instruments?instType=SPOT`) and Bybit's SPOT endpoint
      (`GET     https://api.bybit.com/v5/market/instruments-info?category=spot`) for the full tokenized-equity symbol
      set on each venue (equity-ticker heuristic match, mirroring the equity-perp query method above) — confirm OKX
      actually has this product class before assuming it does, and get every real per-symbol `listTime`/`launchTime` for
      both venues. Repo: instruments-service (findings → this plan's Progress Log).
- [ ] [UAC] P1. Add confirmed tokenized-equity symbols to the CeFi instrument universe with
      `instrument_type=SPOT_PAIR` + a `tracks_equity=<canonical ticker>` link to the Databento real-equity twin,
      mirroring the `crypto_equity_link.tracks_equity()` pattern already shipped for equity perps
      (`unified-api-contracts@e4606ac0` per the sibling plan). Repo: unified-api-contracts.
- [ ] [UAC] P1. Add the confirmed symbols to the CeFi MVP scope rule (mirror how equity-perp bases were unioned into
      `CEFI_EQUITY_PERP_BASE_UNIVERSE`) so they count toward the MVP completeness denominator and are picked up by the
      standard capture/coverage tooling. Repo: unified-api-contracts.
- [ ] [SCRIPT] P1. instruments-service — register an `InstrumentRecord` for each confirmed tokenized-equity symbol dated
      to its REAL historical listing date from Todo 1 (not a blanket floor — mirrors the equity-perp sibling plan's own
      per-symbol-date discipline, motivated by the same regime/coverage-window correctness concern that plan's Progress
      Log documents for XAU/XAG/SPY). Repo: instruments-service.
- [ ] [SCRIPT] P2. Once IS enumerates the new symbols, launch the CeFi Tardis/venue-native backfill for the
      tokenized-equity SPOT window (existing launcher — verify whether OKX/Bybit SPOT tokenized-equity trades ride the
      same Tardis archive as the equity perps, or need their own adapter check first). Repo: deployment-service.
- [ ] [DOCS] P2. Propagate to `/codex/02-data/mvp-scope-canonical.md` and `/codex/02-data/cefi-capture-universe.md` once
      the above lands.

## Progress Log

- 2026-08-12: plan created (human/local track per operator ruling — AO's central server is confirmed down at authoring
  time, per `plans/active/issues/dxy_duplicate_vm_billing_waste_ao_outage_2026_08_12.md`). Equity-perp listing-date
  research (a related but distinct product class) done the same session and cross-referenced above for convenience; not
  itself part of this plan's scope.
