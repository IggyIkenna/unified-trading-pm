---
scope: [engineer, admin]
title: Live Pipeline Architecture
type: architecture
status: stub
created: 2026-05-21
last_reviewed: 2026-05-22
---

# Live Pipeline Architecture

> **STUB** — Reference: `plans/epics/defi_master.md`.

The live pipeline is the same code path as batch, operating in live mode:
`instruments-service → MTDS → features → strategy → execution`. Identical schemas and data_types; only difference is
execution fills replace simulated fills.

See CLAUDE.md "Live = batch" and `codex/02-data/availability-manifest-and-data-status.md`.

---

> **[DELTA 2026-05-22]** **Current state:** Stub. Features pipeline wired for `lst_yields`, `lst_native_rates`,
> `perp_funding_rates` (CeFi + DeFi) feature groups shipped by
> `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` Phases A-C. **Planned delta:**
> `phase5_features_streaming_carry_staked_basis_mvp_2026_05_19.md` is delivering: `perp_funding_rates` feature group
> spec (CeFi: Binance ETH-PERP; DeFi: Hyperliquid ETH-PERP), 30-day backfill 2026-04-20→2026-05-19, live runners
> (`CeFiPerpFundingComputeRunner` + `OnChainPerpFundingComputeRunner`), `lst_yields` + `lst_native_rates` live override,
> features-service Cloud Run deploy (BLOCKED-OPERATOR-DEPLOY as of 2026-05-20). **Target architecture:** Full features
> streaming: all feature_groups emitting from features-service Cloud Run; strategy `colocated_engine` merging
> `funding_rate_apy_bps` + `staking_apy_bps` + `lst_native_rate` per tick; paper VM fills > 0 within first 10 ticks.
>
> **`perp_funding_rates` feature group spec (MVP)**:
>
> - CeFi adapter: reads MTDS
>   `gs://market-data-tick-cefi-prd-{pid}/raw_tick_data/by_date/day=.../venue=.../symbol=.../derivative_ticker/*.parquet`;
>   filters to ETH-PERP; applies `annualise_funding_rate_bps(rate, venue)` (UAC `registry/perp_funding_cadence.py`).
> - DeFi adapter: reads MTDS `gs://perp-funding-{pid}/perp_funding/hyperliquid/date=.../*.parquet`; same transformation
>   pipeline.
> - Honest absence: `record_empty(reason=EXPECTED_NO_FUNDING_RATE_TICKS)` when no rows for venue+symbol+day.
> - Live runners: `CeFiPerpFundingComputeRunner` + `OnChainPerpFundingComputeRunner` both implement the
>   `FeatureComputeRunner` Protocol; both delegate to batch compute path (Live = batch HARD RULE).
> - GCS output path: `gs://features-cefi-{pid}/by_date/day={date}/feature_group=perp_funding_rates/features.parquet`
>   (CeFi) and `gs://features-onchain-{pid}/by_date/day={date}/feature_group=perp_funding_rates/features.parquet`
>   (DeFi).
> - Shipped: features-service@e43f8370 (Phase A) + features-service@a4fadcf2 (Phase B) + features-service@c9729dce
>   (Phase C).
