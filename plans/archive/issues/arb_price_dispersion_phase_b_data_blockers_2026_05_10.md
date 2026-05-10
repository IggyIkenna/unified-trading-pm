---
title:
  "ARBITRAGE_PRICE_DISPERSION Phase B tracer cannot run-to-completion — upstream data + features gaps across 6 perp
  venues"
created: 2026-05-10
author: agent-arb-fundrate-c2
source:
  - plans/active/arbitrage_price_dispersion_finalisation_2026_05_09.md (Phase B Full-execution criterion 2024-W1)
  - probe of gs://market-data-tick-cefi-{pid}/ + gs://perp-funding-{pid}/ + gs://features-delta-one-cefi-{pid}/
locked_by: live-defi-rollout
locked_since: 2026-05-10
---

# Phase B tracer cannot run-to-completion — upstream data + features gaps across 6 perp venues

> **Severity**: P0 — Phase B is on the May-23 critical path (`pvl-p18a` paper-vs-live evidence pair with
> `carry_staked_basis`); without a verify run the master plan's "2 DeFi archetypes live" deliverable lands silently
> incomplete. **Blast radius**: this plan + MTDS / features-delta-one-cefi service backfill scope + master plan Group F
> Item 17–18 readiness. **Suggested owner**: operator triage — direction-setting on (a) backfill scope vs (b) verify-
> window scope-adjust vs (c) ship-code-without-verify-and-flag.

## What I found

Probed real GCS infra on 2026-05-10 before writing the tracer. The plan's Full-execution criterion specifies
`--start-date 2024-01-01 --end-date 2024-01-07` across the 6-venue universe (bybit, deribit, binance, okx, hyperliquid,
aster). Coverage table:

| Venue           | Source pipeline                                                            | 2024-01-01 raw | 2024-W1 raw | 2025-06-01 raw      | features-delta-one-cefi by_date contiguous? |
| --------------- | -------------------------------------------------------------------------- | -------------- | ----------- | ------------------- | ------------------------------------------- |
| bybit           | Tardis derivative_ticker (`venue=BYBIT/`)                                  | ✅             | (probable)  | ❌                  | ❌ (only 2022-11 → sparse 2024 / 2025)      |
| binance-futures | Tardis derivative_ticker (`venue=BINANCE-FUTURES/`)                        | ✅             | (probable)  | ❌                  | ❌                                          |
| deribit         | Tardis derivative_ticker (`venue=DERIBIT/`)                                | ✅             | ✅          | ✅                  | ❌                                          |
| okx-futures     | Tardis derivative_ticker (`venue=OKX-FUTURES/`)                            | ❌             | ❌          | ❌ (starts 2025-01) | ❌                                          |
| hyperliquid     | perp_funding handler (`gs://perp-funding-{pid}/perp_funding/hyperliquid/`) | ✅             | ✅          | ✅                  | ❌                                          |
| aster           | (no perp_funding directory at all)                                         | ❌             | ❌          | ❌                  | ❌                                          |

Sample probes (run from this session):

```text
$ gcloud storage ls gs://perp-funding-central-element-323112/perp_funding/
gs://perp-funding-central-element-323112/perp_funding/gmx/
gs://perp-funding-central-element-323112/perp_funding/hyperliquid/
# aster directory absent

$ gcloud storage ls gs://market-data-tick-cefi-central-element-323112/raw_tick_data/by_date/day=2024-01-01/asset_group=cefi/venue=BYBIT-FUTURES/...
ERROR: (gcloud.storage.ls) One or more URLs matched no objects.
# but venue=BYBIT/ (no -FUTURES suffix) does exist on the same date — hive-vocab drift to fix in carry tracer too

$ gcloud storage ls gs://features-delta-one-cefi-central-element-323112/by_date/ | tail
.../day=2023-05-22/
.../day=2023-05-23/
.../day=2024-01-15/    # sporadic
.../day=2024-07-02/    # sporadic
.../day=2025-01-10/    # sporadic
# NO contiguous 1-week window for any year
```

The features layer (`features-delta-one-cefi`) is the surface the tracer + engine actually consume per
`_FUNDING_RATE_FEATURE_PREFIX = "funding_rate_"` keys. Even if the raw MTDS layer were fully captured, the features
output is not contiguously backfilled; the engine's `funding_rate_<venue>` reads would return NaN for most days.

## Why it matters

The plan's Phase B Done definition (per CLAUDE.md "Plans Run To Actual Completion" HARD RULE) requires:

> tracer script runs end-to-end against real backfilled MTDS + features data for a 1-week window; produces a CSV with at
> least one signal-emit row.

Today (2026-05-10) **no 1-week window exists** where:

1. all 6 perp venues have raw funding-rate data (aster + okx blockers); AND
2. features-delta-one-cefi has continuous per-day output for that window.

If we ship the tracer code but skip the verify run, the plan checkbox lands `[x]` while operationally Phase B is broken.
Reference: 2026-05-08 PM rule update — _"Plans Run To Actual Completion, Not Smoke-Test Green"_ exists specifically for
this failure mode.

Phase B blocks Phase C (pnl-attribution archetype bucket consumes Phase B's tracer output) which blocks Phase D (Stream
B gate close) which blocks the master plan's `pvl-p18a` paper-vs-live evidence pair. Net: ARBITRAGE_PRICE_DISPERSION
half of the master plan's "2 DeFi archetypes live" deliverable is silently degraded.

Ancillary finding: `trace_carry_staked_basis.py` `_VENUE_FUNDING_SOURCE` mapping uses `BYBIT-FUTURES` / `BITGET-FUTURES`
etc., but on disk the hive partition is `venue=BYBIT/` (no `-FUTURES` suffix). Running the carry tracer against
2024-01-01 likely silent-zeroes for these venues too. Worth a separate audit pass.

## Recommended decision

Operator picks one of:

- **(a) Backfill the upstream layers** — kick off MTDS funding-rate + features-delta-one-cefi backfill VMs to fill a
  contiguous 1-week window across the 4 covered venues + skip aster + okx for the verify (with aster + okx flagged for
  later expansion). Realistic scope: ~hours of VM runtime + orchestration. Unblocks Phase B fully + sets a foundation
  for Phase C/D + the May-23 paper-trade evidence run.
- **(b) Scope-adjust the verify window** — pick a date range where coverage is best, accept partial venue universe (3-4
  venues instead of 6), document the reduced scope in the plan body. Faster but the dispersion alpha is structurally
  different with fewer venues.
- **(c) Ship the tracer code without the verify run + create a P0 operational-gap todo for the run-to-completion** —
  banned by the HARD RULE, but the explicit operator-override allows it as a documented temporary state with named
  successor. Worst correctness story; risks May-23 cutover.

Aster venue is likely a separate independent finding — the perp_funding bucket has no `aster/` directory at all, which
means the MTDS perp-funding handler isn't capturing aster yet. UAC `*_LAUNCH_DATES` for aster needs verification too —
genesis date may be after most window candidates. **Worth filing a sub-issue for "aster funding-rate capture missing"**
regardless of Phase B's path.

## Composes with

- master_to_live_defi_2026_05_23.md Group F Item 17–18 (paper-trade smoke + batch-vs-live recon).
- arbitrage_price_dispersion_finalisation_2026_05_09.md Phase B done definition.
- (potential) launcher_scripts_consolidation_into_deployment_service_2026_05_07.md if a new aster funding-rate backfill
  VM launcher is needed.
