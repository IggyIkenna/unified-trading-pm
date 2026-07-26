---
doc_type: issue
title: >-
  aave_rate_impact backfill now runs and writes real rows, but every output column is a deterministic zero — DefiLlama
  Yields never populates totalBorrowUsd, so utilization is 0 for every pool, every day, forever
summary: >-
  Running the AaveRateImpactCalculator backfill (silent_wrong_answer_bucket_resolution_class_2026_07_20.md § 6, item 1)
  surfaced a second, deeper bug of the SAME class the parent doc catalogs: non-empty, non-NaN data that is numerically
  meaningless. DefiLlama's public /pools endpoint returns totalBorrowUsd=None for all 16,092 pools it serves (verified,
  not just the 71 Aave-v3-Ethereum ones), so total_borrow_usd defaults to 0 for every symbol. Utilization =
  borrow/supply is therefore always 0, and the Aave V3 rate-model math (supply_rate = borrow_rate * utilization * (1 -
  reserve_factor)) makes projected_supply_apy / rate_impact_supply_bps mathematically zero for every pool. Because every
  UAC rate-model default's base_rate is also 0.00, borrow_rate itself collapses to 0 at zero utilization too, so
  projected_borrow_apy / rate_impact_borrow_bps are also zero. The calculator has never produced a non-zero value and
  structurally cannot, from this data source, regardless of when it is run. Separately (already tracked, not duplicated
  here): strategy-service's reader is still keyed to the pre-2026-07-21-rename name `aave_rate_impact`, not the writer's
  `rate_impact`, so even a real (non-zero) value would not reach the P&L engine yet.
status: open
nature: issue
asset_group: [defi]
stage: [data, features]
repos: [features-service, unified-api-contracts, strategy-service]
scope: [engineer]
tags: [silent-failure, data-correctness, false-zero, defi, aave, feature-groups]
related:
  [
    /plans/active/issues/silent_wrong_answer_bucket_resolution_class_2026_07_20.md,
    /plans/active/issues/features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md,
    /plans/active/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md,
    /plans/archive/issues/aave_irm_slope_capture_dropped_2026_05_12.md,
  ]
created: 2026-07-26
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
assigned_role: backend
drift_direction: advance-code
depends_on: []
source:
  [
    "found 2026-07-26 while executing the 'run the aave_rate_impact backfill' residual todo from
    silent_wrong_answer_bucket_resolution_class_2026_07_20.md — the backfill ran and wrote real rows, but every feature
    column read back as exactly zero, which itself is the silent-wrong-answer class the parent doc exists to catch",
  ]
resolved_by:
locked_by:
---

# aave_rate_impact — real rows, deterministic zeros

## 1. What was run

`features-service`'s onchain CLI, targeting the only date this calculator can ever serve (see § 3):

```
GCP_PROJECT_ID=central-element-323112 CLOUD_PROVIDER=gcp ENVIRONMENT=prod .venv/bin/python -m features_service \
  --feature-family onchain --operation compute --mode batch --asset-group DEFI --feature-group rate_impact \
  --start-date 2026-07-26 --end-date 2026-07-26 --force --skip-dependency-check
```

`--skip-dependency-check` is used because the blanket onchain preflight gate (`DependencyChecker`, asset-group-wide)
requires same-day MTDS `vault_share_price`/`lst_rates`/`lending_indices`/`oracle_prices`/`perp_funding` manifests — none
of which `AaveRateImpactCalculator` reads (it fetches DefiLlama Yields directly, see
`features_service/onchain/app/calculators/aave_rate_impact_calculator.py::fetch_data`). This is the documented flag for
exactly this case, not a workaround for a real missing dependency.

**Result**: `Fetched 16092 yield pools from DefiLlama` →
`Wrote 71 rows to gs://features-defi-prd-central-element-323112/onchain/by_date/day=2026-07-26/feature_group=rate_impact/features.parquet`
→ manifest index updated (1 new entry). Non-empty, non-NaN: confirmed by reading the parquet back — 71 rows, 8 columns,
**zero** `NaN`/`None` across every column.

## 2. Why "non-empty, non-NaN" is not "real"

Read back and inspected all 71 rows:

| column                   | value across ALL 71 rows |
| ------------------------ | ------------------------ |
| `projected_supply_apy`   | `0.0000`                 |
| `projected_borrow_apy`   | `0.00`                   |
| `rate_impact_supply_bps` | `0`                      |
| `rate_impact_borrow_bps` | `0`                      |

Every symbol — `WEETH`, `WBTC`, `WETH`, `USDC`, `AAVE`, `DAI`, 65 others — computes to literal zero. This is not a
coincidence of today's market state; it is structurally guaranteed:

1. **`fetch_data`** pulls `tvlUsd` (→ `total_supply_usd`, real: e.g. WETH `$615,235,389`) and `apyBase` (real, e.g. WETH
   `1.49478`), but `totalBorrowUsd` (→ `total_borrow_usd`) and `apyBaseBorrow` come back `None` for **every one of the
   16,092 pools** DefiLlama's `/pools` endpoint returns — confirmed directly, not sampled: `0` non-`None`
   `totalBorrowUsd` values across the full feed, not just the 71 Aave-v3-Ethereum ones. `pool_float()` defaults `None` →
   `0.0`, so `total_borrow_usd=0` for every pool.
2. **`compute_utilization(total_supply, total_borrow) = total_borrow / total_supply`** is therefore `0` for every pool
   (`unified_api_contracts/internal/domain/defi/rate_model.py:289`).
3. **`compute_supply_rate(utilization, borrow_rate, reserve_factor) = borrow_rate * utilization * (1 - reserve_factor)`**
   (`rate_model.py:328`) — multiplying by `utilization=0` zeroes the supply side regardless of `borrow_rate`.
4. **`compute_borrow_rate`** at `utilization=0` reduces to `base_rate` alone (`rate_model.py:314-318`). Every entry in
   `AAVE_V3_RATE_MODEL_DEFAULTS_BY_ASSET` **and** `AAVE_V3_RATE_MODEL_DEFAULT_FALLBACK` sets `base_rate=Decimal("0.00")`
   (`rate_model.py:84-153`), so the borrow side is ALSO zero, not just the supply side.

Every one of the 4 output columns is therefore a deterministic `0` for every symbol, every day, regardless of real
market conditions — the calculator has never produced (and cannot produce, from this data source, unmodified) a non-zero
value. This is the identical shape to the `aave_utilization` false-zero bug already fixed once in this codebase
(`orchestrator_calculators.py` — a defensive path silently computing `0.0` instead of failing loud) and to the parent
doc's own catalogue: a lookup that cannot fail (defaults `None`→`0.0`) feeding a formula that cannot fail
(multiplication by zero), so the wrong answer wears the shape of a right one — non-empty, non-NaN, plausible column
names, real symbols, `captured` in the manifest.

## 3. Why this can only ever be run for "today" (separate, already-documented constraint)

`_process_rate_impact` (`orchestrator.py:645-718`) skips any `start_date < today` as
`FEATURE_GROUP_SKIPPED_BATCH_INCOMPATIBLE` (`empty_confirmed`, not a false `captured` row) — documented in-code as a
2026-05-17 fix: "DefiLlama Yields returns CURRENT pool state only — no historical snapshot API. Backfilling any date
before today causes `LookaheadBiasError`." So "run the backfill" for this feature_group can only ever mean "run it for
today," which is what was done here. A true historical backfill is not possible against this data source without a
vendor switch (tracked: `plans/archive/issues/aave_irm_slope_capture_dropped_2026_05_12.md` Step 4 tail — "migrate
`fetch_data()` from DefiLlama Yields to the MTDS `lending_indices` parquet," never executed).

## 4. Not fixed here, and why

- **The fix is a data-source change, not a backfill.** MTDS's `lending_indices` handler (per-block Aave subgraph
  capture, `market-tick-data-service/.../aave_lending.py`) already carries real `total_borrow_usd`-shaped fields — this
  is the exact migration `aave_irm_slope_capture_dropped_2026_05_12.md` Step 4 left as an explicit, un-executed tail
  item ("~1 cal AI-day; the override path is dormant until then"). That is new engineering scope (swap the calculator's
  `fetch_data()` source), not something to fold into a "run the backfill" todo.
- **Even with real numbers, the P&L read path is separately broken.** `strategy-service/pnl/engine/orchestrator.py:144`
  reads `feature_group=aave_rate_impact`; the writer (both before and after this run) has only ever written
  `feature_group=rate_impact` (the UAC-registry name since the 2026-07-21 vocabulary ruling in
  `features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md`). That doc explicitly flags this as its own
  open item, not something to silently re-point as a side effect of a backfill.

## 5. Recommendation

Not closing via this doc — filing so the zero-value finding isn't lost. Durable close needs, in order: (1) decide
whether to migrate `AaveRateImpactCalculator.fetch_data()` off DefiLlama Yields onto MTDS `lending_indices` (real
`total_borrow_usd`) per the already-identified tail item, or accept a different data source with real borrow-side data;
(2) once real, non-degenerate values exist, re-point strategy-service's reader to `rate_impact` (or resolve that
vocabulary gap however `features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md` ultimately rules). Until
both land, `rate_impact`/`aave_rate_impact` should be treated as **structurally unproduced** for P&L-adjustment purposes
even though a `captured` manifest row with real-looking rows now exists for 2026-07-26 — flagging this explicitly so no
downstream consumer mistakes the presence of the row for the presence of signal.
