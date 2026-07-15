---
doc_type: issue
title:
  Perp funding canonicalisation — derivative_ticker for ALL perps + perp_funding schema conformance + cross-source
  parity
summary:
  Operator ruling 2026-07-15 — derivative_ticker at the highest source resolution is the canonical home of RAW funding
  for every perp venue (capture it even where the source has no open interest; OI fields nullable); perp_funding stays
  the per-interval canonical view (annualized_rate is fine) but the Drift-only funding_rate_24h/7d/30d window aggregates
  are a schema divergence to remove; and a cross-data_type funding parity check (perp_funding vs derivative_ticker
  settlements) must run once the DRIFT backfill grind completes.
status: open
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [defi, perp-funding, derivative-ticker, canonicalisation, funding-rates, data-correctness, parity]
related:
  [
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    plans/active/issues/defi_perp_funding_mvp_scope_contradiction_2026_06_29.md,
  ]
created: 2026-07-15
parent_epic: defi_master
priority: P1
source: [operator ruling 2026-07-15 (main session), funding dual-capture investigation same session]
assigned_vm: NA
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-15
locked_since:
---

# Perp funding canonicalisation — derivative_ticker for all perps (2026-07-15)

> **Operator ruling (verbatim intent, 2026-07-15):** "Annualising funding rates is fine, but the highest-resolution
> derivative_ticker data should be run for ALL perps — even if they don't have OI at the data source — for
> canonicalisation of where raw funding is. Aggregations into 7d, 30d etc. for Drift alone seems like a weird
> divergence."

## Established facts (verified this session)

- `perp_funding` is the canonical DeFi funding data_type (`defi-data-types-catalog.md` §4): schema
  `symbol, ts_event, venue, chain, funding_rate, annualized_rate`; one row per market per funding interval; MVP gate
  data_type on `mvp_backfill_defi_onchain_v10`.
- `derivative_ticker` carries the same funding at settlement/tick grain for several defi perp venues — Drift's adapter
  docstring: "one row per funding-rate settlement with funding_rate/mark_price"
  (`market-tick-data-service/.../adapters/drift_adapter.py:16,147-165`); HYPERLIQUID verified capturing both legs
  (derivative_ticker WS + perp_funding REST, 2026-07-14); ASTER/PACIFICA/EXTENDED/LIGHTER have derivative_ticker paths.
  CeFi perps use `derivative_ticker` as their ONLY funding source (`data-lineage-MTDS-features-ml.md`).
- Divergence: the Drift `perp_funding` writer adds `funding_rate_24h/7d/30d` window aggregates no other venue writes
  (`cli/handlers/solana_defi_drift.py:105-107`) — raw-layer aggregation, one venue special-cased.
- No documented cross-check exists that `perp_funding` and `derivative_ticker` agree for the same (venue, market,
  interval).

## Todos

- [ ] [SCRIPT] P1. Enumerate derivative_ticker coverage per DeFi perp venue (DRIFT-SOLANA, HYPERLIQUID, ASTER, GMX,
      PACIFICA, EXTENDED, LIGHTER, + any other `instrument_type=perpetual` venue in the registry): live + batch capture
      paths present or missing, source's available resolution (settlement events / tick stream / poll), whether the
      source exposes OI. Append the coverage table here. Repo: market-tick-data-service (read-only pass).
- [ ] [CODE] P1. Wire `derivative_ticker` capture for every perp venue missing it, at the highest resolution the source
      offers — per the ruling this INCLUDES venues with no OI at the source (OI/mark/index fields nullable;
      funding_rate + ts_event mandatory). Update UAC expected-coverage/registry so the manifest expects the new (venue,
      derivative_ticker) cells; enumerator picks them up via the standing daily crons. Live=batch: same code path both
      modes. Repo: market-tick-data-service + unified-api-contracts.
- [ ] [CODE] P2. Remove the Drift-only `funding_rate_24h/7d/30d` aggregates from the `perp_funding` write path (keep
      `funding_rate` + `annualized_rate` per the canonical schema — annualizing is explicitly fine). Aggregation windows
      belong downstream (features), not in raw capture. Decide + document disposition of already-written rows carrying
      the extra columns (reader tolerance vs restamp; prefer tolerance if readers project columns). DO NOT disrupt the
      currently-running backfill VM — land for future runs. Repo: market-tick-data-service.
- [ ] [VERIFY] P1 (GATED on the DRIFT perp_funding backfill completing its 2025-01→2026-07 grind). Cross-source funding
      parity: per (venue, market, funding interval), `perp_funding.funding_rate` vs the `derivative_ticker` settlement
      row within ε; DRIFT-SOLANA/HYPERLIQUID/ASTER first; honest report (match %, divergence distribution, worst
      offenders) appended here; genuine divergences filed per findings-triage. Repo: market-tick-data-service (read-only
      analysis script with lifecycle marker).
- [ ] [DOCS] P2. Codex updates recording the ruling: `defi-data-type-taxonomy.md` + `defi-data-types-catalog.md` §4 (+
      derivative_ticker section) + `data-lineage-MTDS-features-ml.md` — derivative_ticker = canonical raw-funding home
      for ALL perps (highest resolution, OI-optional); perp_funding = the per-interval canonical view with
      annualized_rate; no venue-specific raw-layer aggregates. Repo: unified-trading-pm.

## Progress log

- 2026-07-15: Filed from the operator's ruling in the main session, following the funding dual-capture investigation
  (perp_funding vs derivative_ticker). Parity check deliberately gated on the DRIFT backfill grind finishing so it
  compares complete data.
