---
title:
  "B-015 Smoke B re-run blocker — MDPS has no vault_share_price handler; features-onchain pre-flight gate is
  over-reaching"
created: 2026-05-16
author: ikenna-slot-8
resolved: 2026-05-16
resolution:
  SHIPPED — Option A architectural fix (features-service@550cdaba) bypasses MDPS for vault_share_price + lst_rates per
  DependencyChecker.UPSTREAM_DEPS_DEFI; features-onchain reads raw_tick_data directly for on-chain snapshot data_types.
source:
  - "Cross-side ping plans/active/_agent_pings.md § 2026-05-16 11:16 UTC (operator confirms B-015 Option (b))"
  - "harsh-slot-9 → ikenna-main § 2026-05-15 (Smoke B failed dep check: 'MDPS processed_candles missing for
    2026-04-15..19/DEFI')"
  - "VM `mdps-backfill-defi-20260516-121940` exit_code 0 — DATA_INGESTION_COMPLETED severity='no files' (12:21:52 UTC)"
  - "gs://market-data-tick-defi-central-element-323112/raw_tick_data/by_date/day=2026-04-15..19/ ← 7 vault_share_price
    parquets per day (ETHENA/FRAX/MAKER/MORPHOVAULTS/MORPHO_VAULTS/YEARNV3/YEARN_V3)"
  - "market-data-processing-service/market_data_processing_service/app/adapters/defi/ ← 5 adapters: book_snapshot_5,
    dex_swaps, fx_rates, market_state, liquidity (NO vault_share_price)"
severity: P0 (blocks B-015 paper-trade gate; affects DeFi May-23 critical path)
locked_by: live-defi-rollout
locked_since: 2026-05-16
---

## What I found

Operator confirmed B-015 Option (b) at 2026-05-16 11:16 UTC: slot-8 launches MDPS for 2026-04-15..19/DEFI to fill the
upstream gap blocking features-onchain Smoke B re-launch. Slot-8 launched `mdps-backfill-defi-20260516-121940` at
12:19:40 UTC; VM ran clean (STARTED → 5× PROCESSING_STARTED → 5× PROCESSING_COMPLETED → STOPPED) in 3 minutes with
`exit_code 0`.

**BUT** every `DATA_INGESTION_COMPLETED` event landed with `severity: "no files"`, and post-run inspection of
`gs://market-data-tick-defi-central-element-323112/processed_candles/by_date/` shows the path doesn't exist at all.

### Root cause (diagnosed)

The raw_tick_data for the target window EXISTS — 7 vault_share_price parquets per day (one per yield-bearing protocol on
ETHEREUM):

```
gs://market-data-tick-defi-central-element-323112/raw_tick_data/by_date/day=2026-04-15/asset_group=defi/
  venue=ETHENA/chain=ETHEREUM/instrument_type=yield_bearing/data_type=vault_share_price/ETHENA_ETHEREUM_1776254400.parquet
  venue=FRAX/.../FRAX_ETHEREUM_1776254400.parquet
  venue=MAKER/.../MAKER_ETHEREUM_1776254400.parquet
  venue=MORPHOVAULTS/.../...
  venue=MORPHO_VAULTS/.../...
  venue=YEARNV3/.../...
  venue=YEARN_V3/.../...
```

MDPS DeFi adapter coverage (per `market-data-processing-service/market_data_processing_service/app/adapters/defi/*.py`):

| Adapter file               | `data_type =`     |
| -------------------------- | ----------------- |
| `book_snapshot_adapter.py` | `book_snapshot_5` |
| `swap_adapter.py`          | `dex_swaps`       |
| `fx_rate_adapter.py`       | `fx_rates`        |
| `market_state_adapter.py`  | `market_state`    |
| `liquidity_adapter.py`     | `liquidity`       |

**`vault_share_price` is NOT in the MDPS DeFi adapter set.** MDPS sees the raw_tick_data, discovers no matching adapter
for the `data_type=vault_share_price` partition, emits `"no files"`, exits clean.

### Why MDPS doesn't handle vault_share_price (architectural)

`vault_share_price` is a per-vault daily/hourly snapshot of `pricePerShare` (or equivalent) from on-chain reads. It's
already at the canonical sampling rate the strategy consumes — no tick→candle aggregation needed. Compare with CeFi
where MTDS emits raw trades (sub-second) and MDPS aggregates to 1m/5m/1h candles.

The architecturally-correct consumer of `vault_share_price` is `features-onchain` reading **raw_tick_data directly**,
not waiting on an MDPS pre-flight gate that doesn't apply.

## Why it matters

- **B-015 paper-trade gate BLOCKED**: per current Smoke B pre-flight, features-onchain refuses to run because it can't
  find processed_candles for vault_share_price — but those will NEVER exist because MDPS doesn't process this data_type.
- **DeFi May-23 critical path at risk**: `carry_staked_basis` archetype depends on vault_share_price reads for LST APR
  computation; without features-onchain running clean, the strategy can't compute.
- **Cross-slot coordination wasted**: Smoke A clean + operator routing + slot-8 VM launch all assumed MDPS would fill
  the gap. Diagnosis points to features-onchain's pre-flight contract, not MDPS.

## Recommended decision (operator review)

Pick one path:

**Option A (architectural fix; recommended)**: Update `features-onchain`'s pre-flight dependency check to read
**raw_tick_data** directly for `data_type=vault_share_price` (and any other on-chain snapshot data_types). MDPS
processed_candles only required for data_types MDPS actually aggregates (book_snapshot_5 / dex_swaps / fx_rates /
market_state / liquidity). Smoke B then runs and validates the actual feature-computation, not a stale upstream gate.

**Option B (defer architectural; tactical re-route)**: Add a no-op `vault_share_price_adapter.py` to MDPS DeFi that
passes raw → processed_candles 1:1 (rename, no transform). Quick scaffold; ships in <1 day; bypasses the deeper fix.
Adds operational complexity (a useless MDPS run for every DeFi date).

**Option C (descope from B-015)**: declare B-015 verified on Smoke A alone (lst_rates clean); move features-onchain
vault_share_price wiring + Smoke B to post-cutover. Risk: paper-trade P&L for `carry_staked_basis` won't include LST
vault-yield contributions until post-cutover.

Suggested owner: Harsh-side MTDS handler maintainers (features-onchain pre-flight check lives there) OR Ikenna
strategy-features-onchain maintainer.

## Cross-references

- Predecessor: `plans/active/issues/b_015_smoke_vms_phantom_manifest_silent_skip_2026_05_15.md` (Smoke A/B framing)
- Operator direction: `plans/active/_agent_pings.md` § 2026-05-16 11:16 UTC (Option b confirmed)
- VM evidence:
  `gs://central-element-323112-events/events/market-data-processing-service/2026-05-16/mdps-backfill-defi-20260516-121940/hour=11/`
  (35 events, STOPPED at 11:21:54)
- MDPS DeFi adapter catalogue:
  `market-data-processing-service/market_data_processing_service/app/adapters/defi/{book_snapshot,swap,fx_rate,market_state,liquidity}_adapter.py`
- features-onchain pre-flight site: `features-service/features_service/onchain/dependency_checker.py` (probable; needs
  spot-check)
- Related: `plans/active/defi_master_2026_05_07.md` § paper-trade gate (carry_staked_basis path)

## VM disposition

`mdps-backfill-defi-20260516-121940` STOPPED cleanly at 11:21:54 UTC (5 dates processed, no files matched, no downstream
side-effects). Auto-delete via `VM_SHUTDOWN_ON_COMPLETION=true` metadata. No manual cleanup needed.

execution: owner: "ikenna-slot-2 implemented features-service@550cdaba; verifier = harsh-slot-9 re-launches
features-onchain Smoke B" cadence: "one-shot — closed after Smoke B re-launch verified" verifier: "features-onchain
Smoke B re-run reaches STARTED + manifest captured > 0 for 2026-04-15..19/DEFI vault_share_price" last_executed:
"2026-05-16 (Option A implemented at features-service@550cdaba; Smoke B re-launch pending Harsh slot 9 cross-ping)"

## RESOLVED 2026-05-16 — Option A shipped

Operator-confirmed Option A implemented at `features-service@550cdaba`:

- `DependencyChecker.UPSTREAM_DEPS_DEFI` ClassVar added with MDPS `required: False` + raw_tick_data bypass entries for
  `vault_share_price` (substring filter) + `lst_rates` + existing lending/oracle/perp bypasses.
- `check_dependencies(date, asset_group)` overridden to dispatch DEFI (non-test_mode) to `UPSTREAM_DEPS_DEFI`;
  CEFI/TRADFI/test_mode unchanged.
- 7 new unit tests in `TestDefiPreflightBypassesMdps`
  (`features-service/tests/onchain/unit/test_defi_data_source_routing.py`).
- All 38 onchain routing tests pass; basedpyright clean on `dependency_checker.py`.

Cross-ping to Harsh slot 9 filed at `plans/active/_agent_pings.md` § 2026-05-16 requesting Smoke B re-launch with unique
`VM_NAME`. Issue will be archived once Smoke B reaches STARTED + manifest captured > 0.
