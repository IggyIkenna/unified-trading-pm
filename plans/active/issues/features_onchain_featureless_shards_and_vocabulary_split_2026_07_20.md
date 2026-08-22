---
doc_type: issue
title: >-
  features-onchain: five of seven feature groups are byte-identical FEATURE-LESS shards stamped `captured`, six
  never-produced groups carry false `captured` manifest rows, and three vocabularies disagree about what a feature_group
  is called
summary: >-
  A question about feature_group naming uncovered a larger P0. On any given day, five of the seven on-chain feature
  groups written to features-defi-prd are BYTE-IDENTICAL parquets containing only ['timestamp','instrument_id',
  'timestamp_out'] — 153,956 rows and zero feature columns — and every one is stamped capture_status=captured. Six
  further groups have false `captured` manifest rows with zero GCS objects, traced 1:1 to six batch-skip sites that
  `return True` with a zero row count. Separately, the UAC feature registry, the features-service CLI, the writer
  literals and ml-service each use a different vocabulary for feature_group, so four consumer repos read names that no
  writer emits and each swallows the miss into an empty result. The vocabulary question needs an operator ruling
  (registry-authoritative is REFUTED; adopting writer names would ratify a dishonest manifest; renaming is a PROD data
  migration). The producer and loudness fixes do not need one and are being applied.
status: open
nature: issue
asset_group: [defi]
stage: [data, features]
repos:
  [
    features-service,
    strategy-service,
    ml-service,
    e2e-testing,
    deployment-api,
    unified-api-contracts,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: [silent-failure, data-correctness, feature-groups, manifest-honesty, ssot-contradiction, defi]
related:
  [
    /plans/archive/issues/silent_wrong_answer_bucket_resolution_class_2026_07_20.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /plans/archive/issues/defi_dex_pools_delete_order_stale_2026_07_20.md,
  ]
created: 2026-07-20
author: unknown
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend
drift_direction: advance-code
depends_on: []
source:
  [
    "adversarial adjudication workflow run 2026-07-20 after noticing that the feature_group the P&L engine reads is not
    the one the producer writes; the naming question was masking the feature-less-shard P0",
  ]
resolved_by:
locked_by:
context_scope:
  [
    features-service/features_service/onchain/engine/orchestrator_calculators.py,
    features-service/features_service/onchain/engine/orchestrator.py,
    /plans/archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md,
    /plans/active/defi_consolidated_closeout_2026_07_18.md,
    /codex/02-data/honest-absence-downstream-handling.md,
  ]
---

# features-onchain — feature-less shards, false captures, and a three-way vocabulary split

> **Read this before acting on section 6 of [[silent_wrong_answer_bucket_resolution_class_2026_07_20]]** — that section
> originally said `aave_rate_impact` merely needed a backfill. It does not. Running the calculator writes `rate_impact`,
> which the reader still cannot see.

## 1. P0 — five of seven written feature groups contain NO features

On `day=2026-03-05` in `gs://features-defi-prd-central-element-323112/onchain/`:

| feature_group             | md5                        | verdict                         |
| ------------------------- | -------------------------- | ------------------------------- |
| `flash_loan_availability` | `hnf702rMHOEF1FQOiCGffw==` | **byte-identical, no features** |
| `health_factor`           | `hnf702rMHOEF1FQOiCGffw==` | **byte-identical, no features** |
| `liquidation_events`      | `hnf702rMHOEF1FQOiCGffw==` | **byte-identical, no features** |
| `rewards`                 | `hnf702rMHOEF1FQOiCGffw==` | **byte-identical, no features** |
| `risk_params`             | `hnf702rMHOEF1FQOiCGffw==` | **byte-identical, no features** |
| `lending_rates`           | `KNXwk8qjFOXb3km/JII9ww==` | real — 15 columns               |
| `lst_yields`              | (absent that day)          | real — 8 columns, 15 days only  |

Those five files are 153,956 rows of `['timestamp','instrument_id','timestamp_out']` and **nothing else**. Reproduced
independently on a second day (`2026-05-20`). 118 days each.

**Mechanism** (`features_service/onchain/engine/orchestrator_calculators.py`, ~221-320): each calculator builds its
output column list defensively —

```python
for c in ("ltv", "liquidation_threshold"):
    if c in rate_data.columns:
        cols.append(c)
return rate_data.select(cols)
```

When the upstream `load_rate_indices()` payload lacks the feature columns, this returns a **non-empty** frame of base
columns. The writer sees rows, writes the parquet, returns `result=True`, and the manifest stamps `captured`. The lookup
cannot fail and the caller cannot fail — the same shape as [[silent_wrong_answer_bucket_resolution_class_2026_07_20]],
and the same shape as the `aave_utilization` false-zero bug already documented **in this very file** at
`orchestrator_calculators.py:183-191`, fixed there and left in place everywhere else.

To every downstream consumer these are indistinguishable from real shards: right path, right name, plausible row count,
`captured` in the manifest.

## 2. P0 — six false `captured` manifest rows, explained exactly

`onchain/_index/availability_index.parquet` holds 13 rows, all `date=2026-01-25`, all
`capture_status=captured / expected=True / available=True`. Six carry `instrument_count=0` and have **zero GCS
objects**: `perp_funding_rates`, `macro_sentiment`, `lst_native_rates`, `rate_impact`, `onchain_perps`, `utilization`.

`features_service/onchain/engine/orchestrator.py` contains exactly **six** `FEATURE_GROUP_SKIPPED_BATCH_INCOMPATIBLE`
sites (~225, ~466, ~508, ~642, ~709, ~811), each doing `self._last_record_count = 0; return True`. The wrapper at
:176-179 writes a **captured** manifest row on any `True`. Six skip sites → six false rows. A 1:1 mechanical match.

This is the banned "empty placeholder rows that look populated" pattern, verbatim.

## 3. The vocabulary split — three (arguably four) names for one concept

| source                                   | example names                                                                                       |
| ---------------------------------------- | --------------------------------------------------------------------------------------------------- |
| UAC registry (`FEATURE_GROUP_TO_FAMILY`) | `aave_lending_rates`, `aave_risk_params`, `aave_rate_impact`, `lst_staking_yields`, `eigen_rewards` |
| features-service CLI (`FEATURE_GROUPS`)  | `lending_rates`, `risk_params`, `rate_impact`, `lst_yields`, `rewards`                              |
| writer literals / GCS partition values   | `lending_rates`, `risk_params`, `lst_yields`, `rewards`, `health_factor`, `liquidation_events`      |
| ml-service `DEFI_FEATURE_GROUPS`         | a fourth set, defined twice in two files                                                            |

**Zero objects exist under any registry-canonical name.** No alias layer exists anywhere.

**Registry-authoritative is REFUTED**, and the reason matters: `lending_rates` is a genuine **multi-protocol merge** —
on `day=2026-03-05` its `protocol` column is AAVE_V3 152,961 / COMPOUND_V3 36 / SPARK 9 / null 950, produced by
`_load_merged_lending_data` gathering Aave + Compound + Kamino into one frame. Renaming it to `aave_lending_rates` would
**mislabel 995 non-Aave rows** — manufacturing a fresh silent wrong answer of exactly the class being killed. The
registry also has no name at all for `health_factor` or `liquidation_events` (118 days each), and declares
`onchain_regime`, which has no calculator and no data. A vocabulary that cannot name existing production shards cannot
be authoritative over them.

**But writer-authoritative cannot simply be ratified either**: 11 of the writer's 13 names are unbacked — six have zero
objects, five are the feature-less placeholders above. Ratifying it into UAC would enshrine a manifest that positively
asserts never-produced data as captured.

That is why the naming question is an operator ruling and not an engineering choice.

## 4. Confirmed downstream consumers, all failing SILENTLY

| repo             | site                               | reads                      | what happens                                                                   |
| ---------------- | ---------------------------------- | -------------------------- | ------------------------------------------------------------------------------ |
| strategy-service | `pnl/engine/orchestrator.py:125`   | `aave_rate_impact`         | swallowed → `{}` → **unadjusted P&L + 0 bps presented as adjusted**            |
| e2e-testing      | `scripts/defi/colocated_engine.py` | wrong prefix + wrong names | per-group `except: pass` → **backtests complete green on ZERO features**       |
| ml-service       | `cloud_feature_provider.py:384`    | a fourth vocabulary        | total miss → empty DataFrame behind a `logger.warning` → **trains on nothing** |
| deployment-api   | `breakdowns_core.py:325`           | 11 registry names          | the 7 real groups can never appear → **11 phantom coverage gaps rendered**     |

## 5. Coverage stops at 2026-05-22

The `onchain/` prefix has 118 day partitions ending `day=2026-05-22`, though the objects were _written_ 2026-07-18 — so
the pipeline runs, its date range simply ends two months back. **Any DeFi P&L or model training against a recent date
gets nothing under ANY vocabulary.** The manifest is simultaneously frozen at 1 of 118 days and the consolidator reports
`shards_scanned=1 / rows_in=0` against 723 live objects, so the manifest has also stopped self-correcting. This may
outrank the naming question entirely.

## 6. Operator rulings — RESOLVED 2026-07-21

1. **Which vocabulary is canonical for `feature_group`?** ✅ **RULED: option A (adopt writer/CLI names).** The UAC
   onchain registry was reconciled to the writer vocabulary — `unified-api-contracts@e9faf32e`: renamed
   `aave_lending_rates→lending_rates`, `aave_utilization→utilization`, `aave_risk_params→risk_params`,
   `lst_staking_yields→lst_yields`, `eigen_rewards→rewards` (protocol-agnostic), `aave_rate_impact→rate_impact`; ADDED
   `health_factor` + `liquidation_events`; DROPPED `onchain_regime` / `defillama_tvl` / `protocol_rewards` (no writer
   dispatch). Final = the CLI's 13. No GCS partition renamed, no prod-data migration. deployment-api auto-follows.
   **Follow-up (not blocking): DONE 2026-07-30** (defi_satellite_ao_dispatch_batch1 finalize reconciliation), see
   defi_satellite_ao_dispatch_batch1_2026_07_25.md todo 40 for full evidence — two adjacent vocabularies still carried
   the old names, `required_inputs.py` (`FEATURE_REQUIRED_INPUTS`, currently dormant, no runtime call site) and
   `internal/schemas/_feature_contracts.py` (own consumers/test); both renamed to the ratified names + dropped
   `onchain_regime`/`defillama_tvl`/`protocol_rewards`, shipped `unified-api-contracts@edf5122d`.
2. **Any rename is a PROD DATA MIGRATION** — moot under ruling #1 (writer names are already what's on disk; the registry
   reconciliation moves NO objects).
3. **The six false `captured` rows** + **4. the five feature-less shard families** — ✅ **RULED: mark→recompute**, but
   BOTH are BLOCKED on deeper defects (a frozen onchain index/consolidator, and the missing MTDS chain-field collection)
   — the producer honesty already shipped (`features-service@907e17b4`); the durable close is fix-consolidator →
   re-derive-index → build-MTDS-collectors → recompute. Full analysis:
   [[onchain_manifest_dishonest_and_recompute_blocked_2026_07_21]]. Do NOT hand-edit the frozen prod index.
4. **Registry membership corrections** — ✅ done as part of ruling #1 (`health_factor`/`liquidation_events` added,
   `onchain_regime` dropped) in `e9faf32e`.
5. **Does DeFi ML training run in prod today?** ✅ **RULED: no.** The ml-service empty-DataFrame guard
   (`ml-service@93309c5`) stands as a latent correctness guard, not an active P0.

## 7. Being applied now (correct under EVERY surviving hypothesis, no ruling needed)

These are producer-honesty and loudness fixes. None renames anything, none touches prod data.

- Calculators declare a required-output-column set; a frame lacking them is **not written** — `record_failed` /
  `record_empty` with an explicit reason.
- The captured-manifest write is gated on the frame carrying at least one non-base column, not merely on non-emptiness.
- The six batch-skip sites stop returning `True` into a captured write.
- strategy-service splits honest absence (404) from a real error and propagates `rate_impact_unavailable`, so an
  unadjusted P&L is never presented as adjusted.
- e2e `colocated_engine.py` prefix `onchain_features/` → `onchain/` (that prefix exists under no hypothesis), and a run
  resolving zero feature groups **fails** instead of emitting empty ticks. Group names deliberately **not** re-pointed —
  three of the four writer equivalents are the feature-less placeholders, so "fixing" the names would convert a total
  miss into a quiet partial success, which is worse.
- ml-service raises on a DeFi total miss instead of returning an empty frame behind a warning; the duplicated
  `DEFI_FEATURE_GROUPS` definitions are collapsed so they cannot drift apart.
- deployment-api emits observed-but-unexpected groups as an explicit mismatch bucket, so vocabulary drift renders as
  drift rather than as a coverage hole.
- A machine check enumerating all three vocabularies and reporting the diff, so this can never drift silently again. —
  DONE 2026-07-30 (defi_satellite_ao_dispatch_batch1 finalize reconciliation), see
  defi_satellite_ao_dispatch_batch1_2026_07_25.md todo 41 for full evidence: `e2e-testing@bc6a7be`
  (`scripts/defi/onchain_feature_group_vocabulary_check.py`); re-run live confirms features-service == UAC-onchain
  (13/13 identical), ml-service diverges (pre-existing, separately-tracked drift, correctly reported not asserted-away).

## 8. Two unverified signals, recorded but NOT asserted

- The written parquets appear to contain exact duplicate rows (same `timestamp` + `instrument_id` repeated).
- Manifest `instrument_count` is identical (14,630,914) across six different groups, which is implausible as a per-group
  count.

Both warrant a look. Neither was verified, and neither should be repeated as fact until it is.

## VERIFIED 2026-07-28 (slot-7) — both §8 signals CONFIRMED, root causes established (investigation only, no fix)

Read-only, per todo's stated scope (`defi_satellite_ao_dispatch_batch1-040`). Repos touched: features-service,
unified-trading-library (read-only inspection of the live `features-defi-prd-central-element-323112` bucket via UTL's
`get_storage_client()`/`download_bytes` — no writes).

**(a) Exact duplicate rows — CONFIRMED, sampled evidence from both reference days.**

Downloaded and read the real `onchain/by_date/day={day}/feature_group={g}/features.parquet` shards (note: the actual
canonical prefix is `onchain/by_date/day=.../`, not the bare `onchain/day=.../` shorthand used in §1 above — confirmed
via a direct `list_blobs` on the bucket) for all 6 groups that have real objects on disk
(`flash_loan_availability`/`health_factor`/`lending_rates`/`liquidation_events`/`rewards`/`risk_params`; `lst_yields`
has no object on either sampled day — consistent with its 15-day-only coverage noted in §1):

| day          | rows written | exact-duplicate `(timestamp, instrument_id)` rows | fraction |
| ------------ | -----------: | ------------------------------------------------: | -------: |
| `2026-03-05` |      153,956 |                                           111,341 |   ~72.3% |
| `2026-05-20` |       84,331 |                                            65,087 |   ~77.2% |

Every one of the 5 feature-less groups is still byte-identical (md5-confirmed) to each other on both days, matching §1's
finding independently. **Verdict: YES, confirmed — the majority of rows in every sampled shard are exact duplicates on
the (timestamp, instrument_id) key**, on both reference days named in the todo.

**(b) `instrument_count` identical across six groups — CONFIRMED, root cause found (NOT a live-orchestrator bug).**

Read the manifest directly (`onchain/_index/availability_index.parquet` AND its sole source shard
`onchain/_index/per_vm/_legacy_seed.parquet` — both byte-for-byte reproduce the same 13 rows). Confirmed live: exactly
six `feature_group` rows (`lending_rates`, `health_factor`, `rewards`, `liquidation_events`, `risk_params`,
`flash_loan_availability` — precisely the 6 groups that route through `_process_daily_feature_group()` in
`orchestrator.py` and have real GCS objects) all carry `instrument_count=14630914`, `date=2026-01-25`,
`capture_status=captured`.

Traced the live-orchestrator code path first (`features_service/onchain/engine/orchestrator.py:177` +
`orchestrator_daily_loop.py:202`): `self._last_record_count` is explicitly reset to `0` at the top of
`process_feature_group()` **before** dispatch to any specific `_process_*` method, and reset again inside
`_process_daily_feature_group()` — so the live per-call `ManifestWriter.add(row_count=self._last_record_count, ...)`
path (`orchestrator_manifest.py:90-96`) cannot itself produce a value shared across groups; each call gets its own fresh
counter. **This rules out a live-code cross-group state-leak as the cause.**

Root cause is instead in the artifact itself: `_index/per_vm/_legacy_seed.parquet` is UTL's own documented "permanently
frozen, never pruned" bootstrap-seed shard convention (`manifest_consolidator.py` — "so the historical rows appear in
[the availability index]"), not a live per-day write. Directly verified the number's provenance: summing
`flash_loan_availability`'s real per-day row count (via parquet metadata `num_rows`, no full download) across **all 118
real day-partitions** currently on disk (`day=2026-01-25` .. `day=2026-07-26`) gives **exactly 14,630,914** — an exact
match, not an approximation. So the seed row's `instrument_count` is a **whole-corpus cumulative row-count SUM**,
stamped onto one synthetic manifest entry dated `2026-01-25` (apparently the first backfill day, used as a placeholder
date) with `capture_status=captured`, rather than a genuine single-day shard count.

It is identical across all six groups **not because of a copy-paste/shared-variable bug in the seeding process**, but as
a direct, deterministic consequence of §1's own root defect: all six calculators consume the SAME
`load_rate_indices()`/merged-loader output and only differ in which COLUMNS they retain (five drop every real feature
column defensively; `lending_rates` keeps its real columns but drops no ROWS) — so their row cardinality is identical,
day-for-day, corpus-wide. Six independently-computed 118-day sums over row-identical inputs are mathematically bound to
land on the same total. **This is not a second, independent bug — it is signal (b) surfacing the same §1 defect from a
different angle** (row-count/manifest side rather than row-content side).

This also corroborates §5's "manifest frozen at 1 of 118 days" finding: the legacy-seed bootstrap row was never
superseded by real per-day manifest writes because the consolidator has been stalled since 2026-07-18 (confirmed:
`onchain/_index/per_vm/` contains only this one shard, `last_modified=2026-07-18T11:02:45Z`, alongside a
`consolidator_stall_state.json` sentinel) — the same already-tracked consolidator-stall blocker named in
[[onchain_manifest_dishonest_and_recompute_blocked_2026_07_21]].

**Not determined**: the exact one-off script/process that originally generated `_legacy_seed.parquet` (no matching
seed/backfill script was found in the current features-service/unified-trading-library/instruments-service trees — it
was likely an uncommitted or since-deleted ad hoc bootstrap run). The DATA-level mechanism (whole-corpus sum,
byte-exact-matched) is conclusively established regardless of which script produced it.

**Disposition**: both signals are real and now asserted as fact. No fix applied (investigation-only per this todo's
scope) — the fix path is already the one this doc's ruling #3 names (fix-consolidator → re-derive-index →
build-MTDS-collectors → recompute), not a new one.

## INVESTIGATED 2026-08-21 — health_factor / LTV-liq-threshold-for-5-protocols / Radiant reserve reader

Session scope: the "build-MTDS-collectors → recompute" remaining scope from the todo below, narrowed to 3 sub-questions.
Real, live-verified findings only — no code shipped this session (see disposition per item).

**(1) `health_factor` protocol-aggregate source — STOP, premise contradicted, no build attempted.**
`REQUIRED_OUTPUT_COLUMNS["health_factor"]` (`orchestrator_calculators.py:47-55`) names
`aave_health_factor`/`aave_total_collateral_eth`/`aave_total_debt_eth`/`aave_available_borrows_eth`/
`aave_current_liquidation_threshold`. These are **exactly** Aave V3 `Pool.getUserAccountData(address user)`'s return
tuple (`totalCollateralBase`, `totalDebtBase`, `availableBorrowsBase`, `currentLiquidationThreshold`, `ltv`,
`healthFactor` — confirmed against `aave/aave-v3-core` `IPool.sol`), the canonical **wallet/account-scoped** call — not
a guess, the field names are a 1:1 match. `AaveProtocolDataProvider`/`Pool.getReserveData()` (reserve-level, already in
`market-tick-data-service/market_interface/adapters/defi/aave_positions.py` `_RESERVE_DATA_ABI`) has zero
health-factor-shaped fields (liquidityIndex/borrow-rates/aToken addresses only) — reserves don't carry a "total
collateral" or "health factor" at all; that concept only exists per-account. Aave itself exposes no
protocol-wide-aggregate health factor (averaging `getUserAccountData()` over every borrower isn't an Aave-published
metric — it would be re-deriving wallet data in aggregate, the exact pattern the prior session rejected). **The
orchestrator.py `_process_health_factor` docstring's claim ("protocol-level aggregates, not wallet-specific") is
asserted, not backed by any real source** — this is very likely the origin of the false framing this task started
from. Per the task's own stop condition: reporting precisely rather than building. **No fix applied; this shard stays
`attempted_failed`/unwritten under the existing `_require_declared_outputs` gate — correctly, since no real
protocol-aggregate source exists.** Follow-up needs an **operator ruling**: either (a) accept `health_factor` as
genuinely wallet-scoped and re-route it through position-risk-centralization instead of the on-chain
protocol-aggregate feature pipeline, or (b) retire the feature_group as unbuildable.

**(2) LTV/liquidation-threshold for COMPOUND_V3/EULER_V2/FLUID/VENUS/BENQI — real sources found for 3, no build (architecture blocker).**
- **Compound V3 (Comet)**: `Comet.getAssetInfoByAddress(asset)` — **live eth_call CONFIRMED** 2026-08-21 against the
  real mainnet USDC Comet (`0xc3d688B66703497DAA19211EEdff47f25384cdc3`, from
  `compound-finance/comet/deployments/mainnet/usdc/roots.json`) for WETH collateral: returns an 8-word
  `AssetInfo` struct (offset, asset, priceFeed, scale, `borrowCollateralFactor`, `liquidateCollateralFactor`,
  liquidationFactor, supplyCap) — real, non-zero values observed on-chain.
- **Venus (BSC)**: Compound-fork `Comptroller.markets(vTokenAddress)` exposes `collateralFactorMantissa` +
  `liquidationThresholdMantissa` per market (confirmed via `VenusProtocol/venus-protocol` `ComptrollerStorage.sol` +
  `docs-v4.venus.io`) — real, not live-called this session.
- **BENQI (Avalanche)**: same Compound-fork Comptroller shape (`collateralFactorMantissa` via `markets(qiTokenAddress)`)
  — real pattern, but only the Isolated-Markets Comptroller address was found this session
  (`0xfc8C7271BdC3816D7AB1fc802216bad387692Ce1`); the Core-Markets Comptroller address (the one this codebase actually
  needs) was not resolved.
- **Euler V2**: per-vault `LTVConfig` (distinct `borrowLTV`/`liquidationLTV`, ramping fields) confirmed via
  `euler-xyz/euler-vault-kit` docs + audit — real, queried through Euler's Lens contracts, not live-called this
  session (no vault address resolved yet).
- **Fluid**: NOT confirmed. Fluid's LTV/liquidation data lives behind its Vault `Resolver` contracts
  (`docs.fluid.instadapp.io`), not a simple single-call getter like the other 4 — needs deeper research before a
  calculator can be scoped. Still BLOCKED.

**Architecture blocker (applies to all 4 confirmed sources above, not just Fluid)**: every existing features-service
on-chain calculator (`compound_v3_liquidity_calculator.py`, `euler_v2_liquidity_calculator.py`, `aave_risk_calculator.py`,
etc.) fetches over **HTTP** (DefiLlama Yields API) — features-service does not own chain RPC credentials.
`features_service/onchain/collectors/chain_event_scanners.py`'s own docstring states this explicitly: "features-onchain-
service does not own chain credentials; the runner pulls keys from Secret Manager via `ApiKeyReloader`". The 4 real
sources above are all **on-chain `eth_call`s**, not HTTP APIs — building `<protocol>_risk_calculator.py` files that
call them directly from features-service would need new RPC-credential plumbing that doesn't exist in this service
today (MTDS owns that, via Alchemy clients — see `aave_positions.py`), or an MTDS-side collector (mirroring the
existing Radiant oracle-price collection pattern) that features-service's `data_loader` then reads, matching the
`load_rate_indices()` precedent every other calculator in this file already uses. **Scoping and building that
plumbing is a real, larger follow-up** — not attempted this session to avoid a same-file cross-service-boundary
violation (`NO service↔service deps` — features-service depends only on UTL/UAC/`unified-*-interface`, never imports
MTDS directly). No calculator files were created.

**reward_rate**: not investigated this session (budget). Still open/unresearched — do not assume `EigenRewardsCalculator`
generalizes; genuinely unresearched, not "still blocked" in the confirmed sense.

**(3) RADIANT reserve reader — getLendingPool() CONFIRMED live; ABI-shape finding; no build (same architecture blocker + a real ABI mismatch).**
Live-verified independently 2026-08-21 (own `eth_call`, not just reading the pre-existing note in
`market-tick-data-service/.../_oracle_prices_constants.py`, which has an unrelated **uncommitted, stale** (~8h old)
local diff in that repo — not touched, not mine, per multi-agent safety rules):
`LendingPoolAddressesProvider.getLendingPool()` on `0x454A8DAF74b24037ee2FA073ce1BE9277ED6160A` (Arbitrum) resolves to
`0xE23B4AE3624fB6f7cDEF29bC8EAD912f1Ede6886`, matching the local uncommitted note exactly.

**Real finding — the task's premise ("combine with `AavePositionsMixin`'s existing `_RESERVE_DATA_ABI`") does not hold
as stated**: calling `getReserveData(asset)` against Radiant's `LendingPool` for WETH/ARB/USDC returns **12 words**
(V2-shaped: configuration, liquidityIndex, variableBorrowIndex, currentLiquidityRate, currentVariableBorrowRate,
currentStableBorrowRate, lastUpdateTimestamp, aTokenAddress, stableDebtTokenAddress, variableDebtTokenAddress,
interestRateStrategyAddress, id) — **not** the 15-word V3 struct `AavePositionsMixin._RESERVE_DATA_ABI` decodes
(that ABI has `accruedToTreasury`/`unbacked`/`isolationModeTotalDebt` and a different field order). This matches
Radiant's own docstring ("Aave-V2-fork") but contradicts reusing the V3-shaped ABI verbatim — a genuinely new
12-field ABI is needed, not a straight reuse. Confirmed available-liquidity computable
(`aToken.totalSupply() - variableDebtToken.totalSupply()`, e.g. USDC: 18,956,249,967 - 6,191,028,812 =
12,765,221,155 raw units) via 2 extra ERC20 `totalSupply()` calls per reserve.

Also found: `instruments-service/instruments_service/reference_data/adapters/defi/radiant.py`'s curated
`vault_address` values (e.g. rWETH `0xF4B1486DD74D07706052A33d31d7c0AAFD0659E1`) do **not** match the real aToken
address `getReserveData()` returns for WETH (`0xfb6f79db694ab6b7bf9eb71b3e2702191a91df56`) — worth a separate look,
not chased further this session (out of this todo's scope; flagging per the "misled you → fix or flag" rule).

Same architecture blocker as (2) applies: this reader belongs on the MTDS side (same repo as `aave_positions.py` and
the existing Radiant oracle collector), not bolted directly onto features-service. No calculator files were created.

## INVESTIGATED 2026-08-22 — health_factor operator ruling RESOLVED: real collector already exists, in strategy-service not MTDS; no build needed

Corrected framing from the operator (this session): we don't need a protocol-wide aggregate — for OUR OWN Aave
positions we already know the wallets, so wallet-scoped `getUserAccountData()` for those specific wallets is a
legitimate, bounded use. Tasked to build this MTDS-side, reusing MTDS's existing `aave_positions.py`/
`_radiant_oracle_collection.py` infra. **Investigation found the premise needs one correction: the real,
live-wired wallet-scoped collector already exists — in `strategy-service`, not MTDS — and MTDS has zero
wallet-scoped on-chain read infra to reuse.**

**(1) Real wallet source — CONFIRMED, two independent real sources, not invented:**
- **Own-client wallets**: `strategy-service/strategy_service/position/config_reloaders.py`'s
  `DefiWalletDomainConfig` (`wallets: dict[client_id, dict[chain, wallet_address]]`), a GCS-backed hot-reloadable
  domain config (`ConfigReloaderBase(domain="defi_wallets", ...)`), resolved via `get_active_defi_wallets()` /
  `chains_for_client(client_id)`.
- **Third-party candidate wallets** (for liquidation-hunting archetypes, not our own positions):
  `aave_candidate_discovery.py`'s subgraph-sourced watch-list, via `discover_aave_borrower_candidates()`.

**(2) Real collector — CONFIRMED ALREADY LIVE-WIRED, not a gap:**
`strategy-service/strategy_service/position/position_interface/adapters/aave.py::AavePositionAdapter.get_lending_position()`
already makes exactly the call this task specified: `getUserAccountData(address)` (selector `0xbf92857c`,
verified against 4byte.directory 2026-08-18) on the Aave V3 Pool
(`0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`), decodes the 6-word return tuple, and emits
`health_factor`/`ltv_ratio`/`collateral_usd`/`debt_usd` — i.e. the 5 `REQUIRED_OUTPUT_COLUMNS["health_factor"]`
columns this doc's 2026-08-21 investigation matched to this exact call. It correctly reports `health_factor=None`
(honest-absence) rather than Aave's uint256-max "no risk" sentinel when a wallet carries zero debt. Two real
callers already wire it to the two wallet sources above:
`strategy_service/position/core/defi_health_poller.py::poll_client_defi_wallets()` (own-client wallets →
`risk.py::update_lending_positions()` → `margin_health_cache`) and
`strategy_service/position/core/candidate_wallet_health_poller.py::poll_candidate_wallet()` (candidate wallets →
`margin_health_cache.record_margin_health()` directly).

**(3) Live-verified 2026-08-22 (real eth_call, no credentials — public RPC)**: replayed the exact call
`AavePositionAdapter` makes — `eth_call` to `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`,
data=`0xbf92857c` + 32-byte-padded address — against `https://ethereum-rpc.publicnode.com` (no API key) for the
zero address. Real mainnet response decodes to `totalCollateralBase=11929042313` ($119.29 at 8-decimal base-currency
convention), `totalDebtBase=0`, `availableBorrowsBase=4875399593` ($48.75), `currentLiquidationThreshold=7800`
(78.00% at 4-decimal bps), `ltv=4087` (40.87%), `healthFactor=uint256-max` — matching
`AavePositionAdapter`'s documented decimal conventions and its zero-debt sentinel handling exactly. The
selector, target address, decode shape, and sentinel logic are confirmed correct against live chain state.

**(4) Why no MTDS build was made — the real consumers already bypass the GCS `health_factor` feature_group
entirely, so building a collector to feed it would be building for a dead pipe:**
`strategy-service/strategy_service/engine/core/gcs_feature_provider.py`'s own docstring states the GCS
`health_factor` feature_group parquet is one of five **byte-identical placeholder** shards — base identity
columns only, zero real feature columns. The two archetypes that actually gate on health factor —
`engine/strategies/v2/arbitrage_structural/liquidation_capture.py` and
`engine/strategies/v2/mev/liquidation_bundle.py` — do **not** read that GCS feature group at all; both read
"the centralized margin-health cache" (`margin_health_cache.py`), which `defi_health_poller.py`/
`candidate_wallet_health_poller.py` already populate from real `AavePositionAdapter` eth_calls. So the GCS
`health_factor` feature_group schema this doc's `REQUIRED_OUTPUT_COLUMNS` names is not on the real data path at
all — it is vestigial. Building a second MTDS-side `getUserAccountData()` collector (duplicating the selector/
decode/sentinel logic `AavePositionAdapter` already gets right) to write into that placeholder parquet would
(a) violate "reuse infrastructure, don't build a parallel one" — the real infra is one repo over, and (b) feed a
pipe nothing downstream reads.

**Ruling applied**: **(b)-adjacent** — not "retire as unbuildable" (it IS buildable and already built), but
**retire the GCS `health_factor` feature_group / `REQUIRED_OUTPUT_COLUMNS["health_factor"]` schema as the wrong
target** — the real wallet-scoped health-factor pipeline already exists end-to-end in strategy-service and is
already the live data path the archetypes use. No MTDS code shipped this session (none was correctly scoped to
ship). If a genuinely new consumer needs health_factor via the GCS/features-service path specifically (not the
live cache), the correct follow-up is wiring strategy-service's *existing* `AavePositionAdapter` output to also
write a GCS parquet in the canonical shard shape — reusing the adapter, not re-deriving it in MTDS — tracked as
a new todo below, not built blind this session.

- [ ] [BACKEND] P2. If a real consumer needs `health_factor` via the GCS/features-service parquet path (distinct
      from the live `margin_health_cache` path `liquidation_capture.py`/`liquidation_bundle.py` already use),
      wire `strategy-service`'s existing `AavePositionAdapter.get_lending_position()` (already real,
      live-verified 2026-08-22) to also persist a GCS parquet in the canonical `health_factor` feature_group
      shard shape for `DefiWalletDomainConfig`'s known wallets — do not re-implement the eth_call/decode logic in
      MTDS. Confirm a real consumer exists before building (name it) — this todo is a placeholder for the
      possibility, not a confirmed requirement as of 2026-08-22.

## Todos

- [ ] [DATA] P0. **PARTIALLY CLOSED by batch-6 todo 18 (slot-4, 2026-07-30, features-service@d8a643a0).** Fix onchain
      features consolidator → re-derive-index → build-MTDS-collectors → recompute — the mark→recompute fix for the 6
      false-`captured` rows and 5 feature-less shard families (ruling #3) is tracked in
      `archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md`. **Premise corrected 2026-07-30
      (/na-eligibility-audit defi)**: the "BLOCKED on the frozen onchain manifest/consolidator" framing is STALE — that
      sibling doc's own 2026-07-28 (slot-12) root-cause update REFUTED it (`_index/latest.json` shows a healthy
      ~1-minute cron; the frozen 13-row index is an ORPHANED migration artifact at `onchain/_index/` with no live
      consolidator owner, not a broken consolidator). The sibling doc's own retagged [DATA] P1 todo (delete the orphaned
      tree under a fresh finding-T reversibility check + bulk-register the historical corpus into the LIVE root
      manifest) — ✅ **SHIPPED 2026-07-30, features-service@d8a643a0** (batch-6 todo 18; sibling doc now archived; real
      corpus was 1538 objects not 724, 1508 rows registered). **This todo's remaining genuine scope is narrower than its
      own title implies**: only "build-MTDS-collectors → recompute" is left (new upstream MTDS collection for
      ltv/liquidation_threshold/reward_rate/flash_loan_liquidity/health-factor inputs, then rerun the 5 feature-less
      calculators) — the consolidator/re-derive-index portion is now moot (there was never a broken consolidator to
      fix).
- [x] [OPERATOR] P2. **RESOLVED 2026-08-22** — see "INVESTIGATED 2026-08-22" section above. health_factor is
      inherently wallet-scoped (confirmed 2026-08-21); the wallet-scoped pipeline already exists end-to-end and
      live-wired in strategy-service (`AavePositionAdapter` + `defi_health_poller.py` +
      `candidate_wallet_health_poller.py`, real wallets from `DefiWalletDomainConfig` +
      `aave_candidate_discovery.py`), live-verified 2026-08-22 via a real eth_call against public mainnet RPC.
      The GCS `health_factor` feature_group `REQUIRED_OUTPUT_COLUMNS` schema is retired as the wrong target — the
      real consumers (`liquidation_capture.py`/`liquidation_bundle.py`) already read the live
      `margin_health_cache` path instead, not that GCS parquet. Do not build a calculator against this schema.
- [ ] [BACKEND] P2. Scope + build the MTDS-side on-chain risk-parameter collector infrastructure for
      COMPOUND_V3/VENUS/EULER_V2 (real sources confirmed 2026-08-21: Comet.getAssetInfoByAddress() live-verified;
      Venus/BENQI Comptroller markets() mapping; Euler V2 per-vault LTVConfig via Lens) -- this is RPC-credentialed
      on-chain data, so it belongs in market-tick-data-service (mirrors aave_positions.py /
      _radiant_oracle_collection.py, not a features-service HTTP-API calculator) with features-service's data_loader
      consuming it, matching the load_rate_indices() precedent. BENQI needs its Core-Markets Comptroller address
      resolved first (only the Isolated-Markets address was found). Fluid needs its Resolver-contract shape
      researched before it can be scoped at all -- separate sub-item.
- [x] ✅ [BACKEND] P2. **SHIPPED 2026-08-22 — `market-tick-data-service@33c728d2`.** Built the Radiant
      reserve-data reader (`lending_indices_radiant.py`, real direct-RPC collector using the V2-shaped
      `getLendingPool()`/`getReserveData()` path, wired into the lending-indices dispatch alongside
      fluid/morpho's dedicated-collector pattern). **Also found and fixed a real silent-wrong-answer bug in
      the process**: `_oracle_prices_constants.py`'s `_RADIANT_ORACLE_ADDRESS` was derived from
      `0xa97684ead0e402dC232d5A977953DF7ECBaB3CDb` — Arbiscan-labeled "Aave: Pool Addresses Provider V3",
      i.e. AAVE's OWN AddressesProvider (Aave reuses this exact address across chains via CREATE2). Every
      historical `oracle_prices` row captured under `venue=RADIANT` was actually AAVE's Arbitrum oracle
      price, mislabeled. Corrected to Radiant's own AddressesProvider (live eth_call-confirmed against
      docs.radiant.capital). **Historical GCS rows under the wrong label have NOT been purged/recaptured** —
      that's separate scope, see the new todo below. `instruments-service/radiant.py`'s curated
      `vault_address` values still don't match the real on-chain aToken addresses — not checked in this
      shipment, flagging for whoever builds against it next.
- [ ] [BACKEND] P2. **New 2026-08-22.** Purge/recapture the historical `oracle_prices` GCS rows mislabeled
      `venue=RADIANT` (they're actually AAVE's Arbitrum oracle price, per the bug above) — a real data-quality
      fix, not just a code fix. Scope: find the affected date range (RADIANT-ARBITRUM genesis 2022-07-25
      onward, until `market-tick-data-service@33c728d2` landed), decide whether to delete-and-recapture or
      relabel-in-place, per this workspace's GCS/manifest delete-safety protocol (human-gated for prod
      deletes unless reversibility-qualified).
- [ ] [BACKEND] P3. Investigate reward_rate general per-protocol reward-token source -- not researched in the
      2026-08-21 session (budget). EigenRewardsCalculator is EIGEN-specific; unknown whether a general pattern
      exists across protocols. Genuinely unresearched, not confirmed-blocked.

## Progress Log

- **na-eligibility-audit 2026-07-30**: KEEP-NA-STALE: its sole todo's premise ('BLOCKED on the frozen onchain
  manifest/consolidator') was REFUTED by the cited sibling's own 2026-07-28 root-cause update (orphaned migration
  artifact, not a broken consolidator). Citation corrected; the work is owned by that sibling's todo
- **na-eligibility-audit 2026-08-03**: KEEP-NA valid — **correcting the 2026-07-30 entry above: the ownership claim was
  backwards.** The sibling doc (`archive/issues/onchain_manifest_dishonest_and_recompute_blocked_2026_07_21.md`, now
  archived, all its own todos shipped) explicitly disclaims ownership of the remaining scope in its own final Progress
  Log entry: "Remaining recompute scope (build missing MTDS chain-field collectors for the 5 featureless groups) is
  genuinely new work, already tracked as its own open todo in
  `features_onchain_featureless_shards_and_vocabulary_split_2026_07_20.md` — not duplicated here." So THIS doc owns the
  work, not the (archived) sibling — there is no other active doc to cite for a checkbox-citation fix. Verdict on the
  merits: KEEP-NA valid, not RECLASSIFY — independently cross-confirmed by
  `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s own Phase-1 classification of this exact remaining scope (its
  Deferred/non-batchable list, citing this doc by name): "steps 2-4 (new MTDS chain-field collectors for
  ltv/liquidation_threshold/reward_rate/health-factor inputs + recompute) are 'genuinely new scope (upstream
  collection)... size them as their own work' per the doc author" — i.e. building 5 protocol-specific on-chain data
  collectors from scratch needs a human sizing/scoping pass (which on-chain source per protocol/field) before any
  worker-determinable todo exists, not a bare mechanical build. Doc stays `assigned_vm: NA`.
- **context-scout 2026-08-03**: populated/refreshed context_scope (5 entries).
- **context-scout 2026-08-06**: re-scouted; context_scope re-verified (5 entries), unchanged.
- **na-eligibility-audit 2026-08-06** (tranche=defi, dispatch agt-e00d37): KEEP-NA valid — third consecutive
  confirmation (07-30 STALE correction, 08-03 corrected back to valid, 08-06 re-confirmed). Independently re-verified
  both supporting citations (archived sibling's final Progress Log disclaiming ownership;
  `defi_satellite_ao_dispatch_ batch3_2026_07_26.md`'s Deferred/non-batchable list) against their live source files
  rather than trusting the prior audit's word — both still accurate. Only change since the 2026-08-03 marker was a
  context-scout metadata-only touch. Doc stays `assigned_vm: NA`.
- **round11-sweep 2026-08-09** (defi tranche, satellite-extraction + RECLASSIFY re-check): re-read end to end (1 open
  `[DATA] P0` item at entry: build the missing MTDS chain-field collectors for the 5 featureless on-chain feature
  groups, then recompute). Checked against every accumulated round11 precedent (IAM self-service, D16 all-repos, S5.1
  tiering, plan-destination-defaults-AO-dispatched, escalation-N=3-days, reversibility-qualified deletes, Option B
  retired, GSM secret + 5 Slack webhooks now existing) — none apply: the remaining scope is building 5
  protocol-specific on-chain data collectors from scratch (which on-chain source per protocol/field), a genuine human
  sizing/scoping decision per the doc's own author note and `defi_satellite_ao_dispatch_batch3_2026_07_26.md`'s
  Deferred/non-batchable classification — not a bare mechanical build. No satellite-extraction candidate found. Doc
  stays `assigned_vm: NA` (KEEP-NA valid, round11).
- **na-eligibility-audit 2026-08-16** [body-hash:eb6c098a1e58cc26]: KEEP-NA, valid — Single open [DATA] P0 todo's title implies a broad consolidator/re-derive-index/build-MTDS-collectors/recompute chain, but the todo's own updated text narrows it: the consolidator/re-derive-index portion is now moot (already shipped 2026-07-30, features-service@d8a643a0, per a sibling doc's root-cause correction) — only 'build-MTDS-collectors → recompute' remains, i.e.
- **context-scout 2026-08-17**: re-verified context_scope (5 entries), unchanged.
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **investigation 2026-08-21**: Investigated the 3 open sub-questions (health_factor source, 5-protocol LTV sources,
  Radiant reserve reader) with live eth_call verification (own RPC calls, not just re-reading prior notes). No code
  shipped -- see the INVESTIGATED section above for full findings and the 4 new todos this added. Headline: (1)
  health_factor's REQUIRED_OUTPUT_COLUMNS are Aave getUserAccountData()'s exact field names -- inherently
  wallet-scoped, contradicts the "protocol aggregate" framing this task started from, operator ruling needed; (2)
  real sources confirmed for Compound V3 (live-verified)/Venus/Euler V2, Fluid still unresearched, BENQI
  Core-Markets address unresolved; (3) Radiant's getLendingPool() independently re-confirmed live, but its
  getReserveData() is V2-shaped (12 words), not V3-shaped like AavePositionsMixin's existing ABI -- a real ABI
  mismatch, not a straight reuse. All 3 need on-chain RPC calls, which features-service's existing calculators don't
  do (HTTP-only, DefiLlama) -- building requires MTDS-side collector work, scoped as follow-up todos rather than a
  same-session cross-service-boundary build.
