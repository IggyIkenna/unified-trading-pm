---
title: features-service DeFi end-to-end test blocked on multiple data layer issues
created: 2026-05-29
author: harsh (claude opus 4.7)
status: open
source:
  - features-service@9f6bc119
  - market-data-tick-defi-central-element-323112 (legacy)
  - market-data-tick-defi-prd-central-element-323112 (prd)
locked_by: live-defi-rollout
---

## What I found

While trying to run a smoke test of features-service `delta_one` against real DeFi data (operator-directed 2026-05-29 after the CeFi MDPS canary VM failed), I hit a cascade of issues at the data-layer boundary that need workspace-level decisions before features-service work can resume against either bucket.

### Issue 1 — PRD bucket uses different `data_type` names for V3 pools, features-service code can't find them

PRD's manifest reports 1,569,407 rows of DeFi index data with venue/data_type distribution:

| data_type            | rows in PRD manifest |
| -------------------- | -------------------- |
| `dex_pool_swaps`     | 114,322              |
| `dex_pool_state`     | 113,613              |
| `dex_swaps`          | **94,672**           |
| `oracle_prices`      | 69,366               |
| `lending_indices`    | 64,404               |
| …                    | …                    |

**Crucially**, the physical PRD layout for `data_type=dex_swaps` on 2026-05-22 contains only 9 venues — none of which are UNISWAP:

```
BALANCER-ARBITRUM, BALANCER-AVALANCHE, BALANCER-BASE, BALANCER-ETHEREUM,
BALANCER-OPTIMISM, BALANCER-POLYGON, CURVE-AVALANCHE, CURVE-ETHEREUM, SUSHISWAP-ARBITRUM
```

`features_service.delta_one.engine.orchestrator.DEFI_DATA_TYPE_OVERRIDES` hardcodes `volume_analysis`, `vwap`, `microstructure` → `dex_swaps`. With this mapping, **all UNISWAP V3 data is invisible to features-service in PRD** — the V3 concentrated-liquidity pools are written under `dex_pool_swaps`, not the old constant-product `dex_swaps` name.

### Issue 2 — Legacy bucket manifest is incomplete for the most-important pools

The legacy bucket (`market-data-tick-defi-central-element-323112`) physically has the UNISWAP V3 ETH/USDC pool (`0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640`) under `data_type=dex_swaps/venue=UNISWAP_V3-ETHEREUM/` for every day from at least 2024-07-01 onward (verified via direct GCS probe — 162-171 parquets per day, all 6 timeframes present, file-level data passes invariants).

But the bucket's `_index/availability_index.parquet` has **1,812,297 total rows** of which **zero** match this pool. The MDPS canonical writer never registered these instruments in the legacy manifest after the bucket migration.

Downstream effect: `data_loader._collect_daily_frames` queries the manifest first, gets nothing, falls back to per-day `blob_exists` probes (legacy code path). The fallback finds *some* files but not consistently — see Issue 4.

### Issue 3 — `PROTOCOL_DATA_SOURCE_BUCKET_DEFI` workaround required to read legacy

`features_service.delta_one.app.core.data_loader._get_source_bucket` resolves the source bucket via:

```
UCI get_data_source(routing_key="defi") → fallback to resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="defi")
```

Both resolve to the env-tiered `market-data-tick-defi-prd-central-element-323112` (the new SSOT). To read the legacy bucket where the historical data actually lives, set:

```bash
PROTOCOL_DATA_SOURCE_BUCKET_DEFI=market-data-tick-defi-central-element-323112
```

This is **the only documented workaround** as of 2026-05-29. The features-service code intentionally moved off the legacy bucket because it's "deprecated + un-consolidated (stale manifest, thousands of accumulated per-VM shards, full pre-migration history)" — per the docstring at `features_service/delta_one/app/core/data_loader.py:42-50`. The workaround is for TESTING ONLY; **production must use PRD**.

### Issue 4 — Lookback loader only pulls partial days (79 rows when 240 expected)

With the legacy-bucket workaround in place:
- Target: 2024-07-22, base timeframe 1h, lookback-buffer-days 10
- Expected: 10 days × 24 hours = 240 candles
- Loaded: **79 candles** (32% of expected)
- 4h compute fails: `"Insufficient data for volume_analysis: have 79 rows, need 120"`

DeFi (like CeFi) operates 24/7 — there is no legitimate reason for a multi-day window of an active top-3 pool to return only 79 hourly candles. Either the manifest gap (Issue 2) is making the loader silently drop dates the manifest doesn't know about, or there's a per-day filter / partial-load path being exercised. **Root cause not yet identified beyond the manifest hypothesis** — full trace would need DEBUG-level logging across the inner loop and per-day cardinality assertion.

### Issue 5 — `data_type=dex_swaps` OHLC values look wrong (price ≈ 1.0 for ETH/USDC)

The single parquet I downloaded for verification (UNISWAP V3 ETH/USDC 0x88e6a0c2... 2024-07-15, 1h):

| field            | value                          |
| ---------------- | ------------------------------ |
| open             | 1.000513                       |
| high             | 1.001652                       |
| low              | 0.998193                       |
| close            | 0.999771                       |
| volume           | 1.187e7                        |
| volume_quote_usd | **1.187e7** (identical to `volume`) |
| trade_count      | 392                            |
| swap_count       | **392** (identical to `trade_count`) |

ETH on 2024-07-15 was ~$3,200. ETH/USDC OHLC should show prices in the $3,000-3,500 range. The pool address `0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640` IS verified as the canonical USDC/WETH 0.05% pool (chain probe of pool metadata confirms). So either:

- (a) the `open/high/low/close` columns are NOT the spot ETH/USDC price — they're some normalized quantity (price-relative-to-previous? sqrt-tick-ratio? token0/token1 with one side near zero?), OR
- (b) MDPS aggregation for V3 pools is computing the wrong field, OR
- (c) the schema does NOT use spot price as `open/high/low/close` for DEX swaps at all and we're misreading the contract.

Additionally:
- `volume` == `volume_quote_usd` to last decimal across all 24 rows
- `trade_count` == `swap_count` to last digit across all 24 rows

Either these are duplicate columns by design (then the contract should drop one and document it) or one of each pair is being silently overwritten by the other during canonical-writer compute. Either way it's a UAC schema cleanup target.

## Why it matters

We **cannot** validate features-service `delta_one` against either DeFi bucket today:

- **PRD**: features-service `dex_swaps` mapping misses all UNISWAP V3 (the biggest data set in PRD). Only Balancer/Curve/Sushi reachable.
- **Legacy**: workaround required; lookback partial (Issue 4); OHLC values look semantically wrong (Issue 5).

This blocks the operator-directed "validate features-service against the data we have" workstream until at least one of these is resolved.

CeFi has the same shape (different mechanism — operator/Sonnet-4.6 canary VM failure 2026-05-28; raw exists but processed is sparse — see `mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md`).

## Recommended decision

**Operator-only design calls needed**:

1. **DEFI data_type mapping** — Should `features_service.delta_one.engine.orchestrator.DEFI_DATA_TYPE_OVERRIDES` map `volume_analysis`/`vwap`/`microstructure` to `dex_pool_swaps` (the V3 concentrated-liquidity schema) instead of / in addition to `dex_swaps`? This is the unblock for PRD-based testing. Probably needs a UAC `resolve_data_type_for_feature_group()` reconciliation (per the comment at orchestrator.py:124).
2. **Legacy bucket consolidation runner** — Should we run a one-shot manifest-rebuild over the legacy bucket so the existing data becomes discoverable for the testing-only window? Or formally declare the legacy bucket read-only-historical-archive and never load from it via features-service?
3. **dex_swaps OHLC contract** — what DO the `open/high/low/close` columns represent? File a UAC contract doc if they're a normalized metric, or raise an MDPS bug if they should be spot price.
4. **Duplicate columns** — drop `swap_count` (==trade_count) and `volume_quote_usd` (==volume) from `DEX_SWAPS_SCHEMA` as a UAC cleanup, OR document why they're separate.

**Things I can implement once those decisions land**:

- Update `DEFI_DATA_TYPE_OVERRIDES` to the new data_type names.
- Run a smoke test against PRD with the corrected mapping.
- Update the env-var workaround documentation (or remove it once legacy is fully decommissioned).

## Provenance / how to reproduce

```bash
# 1. Confirm legacy bucket has the pool physically
gcloud storage ls "gs://market-data-tick-defi-central-element-323112/processed_candles/by_date/day=2024-07-15/timeframe=1h/data_type=dex_swaps/venue=UNISWAP_V3-ETHEREUM/UNISWAP_V3-ETHEREUM:POOL:0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640.parquet"
# → present

# 2. Confirm legacy manifest does NOT have the pool
.venv/bin/python -c "
import polars as pl, io
from google.cloud import storage
b = storage.Client().bucket('market-data-tick-defi-central-element-323112')
df = pl.read_parquet(io.BytesIO(b.blob('_index/availability_index.parquet').download_as_bytes()))
print(df.filter(df['instrument_id'].str.contains('0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640')).shape)
"
# → (0, 32)

# 3. Confirm PRD physically lacks UNISWAP venues under dex_swaps
gcloud storage ls 'gs://market-data-tick-defi-prd-central-element-323112/processed_candles/by_date/day=2026-05-22/timeframe=1h/data_type=dex_swaps/' | grep -i uniswap
# → empty

# 4. Confirm feature-service mapping
grep -A 20 "DEFI_DATA_TYPE_OVERRIDES" features-service/features_service/delta_one/engine/orchestrator.py
# → maps volume_analysis/vwap/microstructure → dex_swaps

# 5. Feature compute attempt (legacy + workaround)
PROTOCOL_DATA_SOURCE_BUCKET_DEFI=market-data-tick-defi-central-element-323112 \
GCP_PROJECT_ID=central-element-323112 \
features-service --feature-family delta_one --operation compute --mode batch \
  --asset-group DEFI --start-date 2024-07-22 --end-date 2024-07-22 \
  --feature-group volume_analysis --timeframe 1h \
  --instruments "UNISWAP_V3-ETHEREUM:POOL:0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640" \
  --max-workers 1 --skip-preflight --skip-dependency-check \
  --lookback-buffer-days 10 --dry-run
# → "Insufficient data for volume_analysis: have 79 rows, need 120"
```

## Related plans

- `plans/active/mdps_filter_pushdown_memory_audit_and_fix_2026_05_28.md` — CeFi MDPS memory pathology + canary VM failure (parallel issue, different bucket / mechanism)
- `plans/active/features_calc_efficiency_and_correctness_2026_05_27.md` — original 4h/24h blocking issue § 1.0b
- `plans/active/features_registry_status_versioning_2026_05_28.md` — yesterday's shipped registry / status / version work (downstream consumer of whatever data layer fix lands here)
- `codex/02-data/feature-formula-versioning.md` — codex SSOT for downstream feature versioning

## Status taxonomy

`BLOCKED-OPERATOR-DECISION` — operator must pick between (1) extend DEFI_DATA_TYPE_OVERRIDES to PRD's data_type names, (2) rebuild legacy manifest, or (3) wait for MDPS refactor + canonical migration to finish before any features-service work against DeFi. Until one of these lands, features-service smoke tests against real DeFi data cannot proceed.
