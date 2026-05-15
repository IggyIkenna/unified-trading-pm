---
title: "DeFi features-onchain pipeline has never been run — both feature buckets empty"
created: 2026-05-14
author: harsh-slot-9
source:
  - "B-015 Phase 1 prereq check (defi_master_2026_05_07.md § paper-trade gate)"
  - "harsh_orchestrator/pings/slot_9.md"
severity: P1
locked_by: live-defi-rollout
locked_since: 2026-05-14
---

> **🔴 OPERATOR ESCALATION REQUIRED — B-015 blocked by MTDS DeFi protocol collection gap. See § "MDPS smoke findings"
> below. All three smoke runs completed; root cause identified as deeper than originally scoped.**

## Smoke run results (2026-05-14)

Both smoke VMs launched at 14:38 UTC completed quickly (auto-deleted on exit). Results:

**MTDS lst_rates smoke `mtds-lst-rates-20260514-143803` (2026-04-15→2026-04-19) — rc=0, SKIPPED ALL 5 DAYS**

- "Skipping LST rates for 2026-04-15 — all expected sentinels already captured" × 5 days
- Finding: lst_rates data already exists in `market-data-tick-defi-central-element-323112/lst_rates/` back to
  2020-01-01. Coverage confirmed through at least 2026-04-14 (gsutil ls tail) and 2026-04-19 (sentinel captured).
- The original issue's "lst_rates 30 days stale" observation used `market-data-tick-defi-prd-central-element-323112`
  (different bucket). The non-prd bucket that services actually use has full coverage.

**features-onchain smoke `features-onchain-defi-backfill-20260514-143829` (2026-04-08→2026-04-13) — rc=1, FAILED**

```
ERROR DEPENDENCY CHECK FAILED
Missing: market-data-processing-service
Path: gs://market-data-tick-defi-central-element-323112/processed_candles/by_date/day=2026-04-08/
Date: 2026-04-08 / Asset group: DEFI
```

**Root cause (corrected)**: features-onchain-service requires **MDPS processed_candles** as its primary upstream
dependency, NOT MTDS lst_rates directly. The dependency chain is:

```
MTDS raw_tick_data → MDPS processed_candles → features-onchain → features-onchain-central-element-323112
```

MDPS has NEVER been run for DeFi. The bucket `market-data-tick-defi-central-element-323112/processed_candles/` is
completely empty (0 objects).

**Corrected unblocking path for B-015**:

1. ✅ MTDS raw_tick_data — `market-data-tick-defi-central-element-323112/raw_tick_data/` exists from 2020-01-01
2. ✅ MTDS lst_rates — `market-data-tick-defi-central-element-323112/lst_rates/` exists from 2020-01-01 through at least
   2026-04-19
3. 🟢 **MDPS DeFi backfill** — `mdps-backfill-defi-20260514-152157` launched 2026-05-14 15:22 UTC for
   2026-04-08→2026-04-12 (5 days, pre-authorized). Will produce
   `market-data-tick-defi-central-element-323112/processed_candles/`
4. ⏳ features-onchain — will rerun for 2026-04-08→2026-04-12 once MDPS completes
5. ⏳ B-015 carry_staked_basis paper backtest — target window **2026-04-08→2026-04-12**

**B-015 window correction**: original ping to Harsh slot 9 cited 2026-05-01→2026-05-07. That window has no lst_rates
data (coverage ends 2026-04-14 in prd bucket; non-prd also ends ~2026-04-19). Corrected window: **2026-04-08 →
2026-04-12** (5 days; all three sources confirmed present in non-prd bucket).

**MDPS smoke `mdps-backfill-defi-20260514-152157` (2026-04-08→2026-04-12) — rc=0, 0 CANDLES PRODUCED**

MDPS ran successfully but produced 0 processed_candles. Log reveals:

```
Processing missing data_types for defi/2026-04-08: ['dex_swaps']
Listed 0 files from raw_tick_data/by_date/day=2026-04-08/ for data_type=dex_swaps
Skipped 1 data_types with no upstream data for defi/2026-04-08: ['dex_swaps']
Total: 0 candles, 0 success, 0 failed
```

**Root cause (final)**: The MDPS manifest has all DeFi data_types (except `dex_swaps`) marked as `empty_confirmed` —
meaning MTDS has confirmed "no raw tick data available" for them. Raw tick data bucket inspection confirms: **MTDS has
only collected `vault_share_price` data (ETHENA, FRAX) for DeFi. The strategy-required data_types have NEVER been
collected by MTDS:**

| Data type needed for B-015                   | MTDS collection status                               |
| -------------------------------------------- | ---------------------------------------------------- |
| `lending_indices` (Aave base/supply rates)   | ❌ `empty_confirmed` — never collected               |
| `risk_params` (Aave utilization/LTV params)  | ❌ `empty_confirmed` — never collected               |
| `perp_funding` (Drift/GMX funding rates)     | ❌ `empty_confirmed` — never collected               |
| `oracle_prices` (Chainlink/Pyth price feeds) | ❌ `empty_confirmed` — never collected               |
| `dex_swaps` (Uniswap/Curve swap data)        | ❌ no raw files (not in manifest = never processed)  |
| `vault_share_price` (ETHENA/FRAX yields)     | ✅ raw files exist but `empty_confirmed` in manifest |

**Corrected unblocking path (requires operator direction):**

1. ⛔ **MTDS DeFi protocol collection** — MTDS handlers for `lending_indices` (Aave), `risk_params` (Aave),
   `perp_funding` (Drift/GMX), `oracle_prices` need to be identified and run. These are the handlers that collect DeFi
   protocol-level on-chain data. Without this step, MDPS has nothing to aggregate and features-onchain has nothing to
   read.
2. → MDPS DeFi aggregation (will produce processed_candles once raw data exists)
3. → features-onchain (will compute features from processed_candles)
4. → B-015 backtest

**Operator questions (needed to unblock):**

- Q1: Has the MTDS Aave lending adapter (`lending_indices` handler) ever been run? Is there a VM launcher script for it?
  (e.g., `launch-mtds-aave-backfill-vm.sh` or similar)
- Q2: Has the MTDS perp funding adapter for DeFi venues (Drift, GMX) ever been run?
- Q3: What date range does each DeFi protocol handler support (Aave V3 launch = 2023-01-27)?
- Q4: Is the B-015 window (2026-04-08→2026-04-12) within MTDS DeFi protocol coverage, or do we need to run a full
  history backfill first?

---

## What I found (original)

During B-015 Phase 1 prereq check (carry_staked_basis paper backtest pipeline-state verification, item (c) —
features-service DeFi feature parquets), both DeFi feature buckets are empty:

- `features-onchain-central-element-323112` — bucket exists, `gsutil du -s` = 0 bytes
- `features-delta-one-defi-prd-central-element-323112` — bucket exists, `gsutil du -s` = 0 bytes

The `colocated_engine.py` paper backtest engine reads from `features-onchain-central-element-323112` for the `DEFI`
category (line 138: `"DEFI": "features-onchain-central-element-323112"`), using path template:
`onchain_features/by_date/day={date}/feature_group={group}/features.parquet` with feature groups:
`["aave_lending_rates", "aave_utilization", "rate_impact", "onchain_perps"]`.

Both buckets have 0 bytes — the features-onchain service (or whatever service produces DeFi feature parquets for
carry_staked_basis) has never been run against GCS production buckets.

**Technical consequence**: `_load_features_for_date()` (colocated_engine.py:817) returns `{}` silently when parquets are
missing (line 845: `except Exception: pass`). The engine emits ticks with empty feature dicts. The carry_staked_basis
strategy will receive no signal data — either never trades or trades on zero signals. The paper backtest P&L report
would be meaningless.

## Secondary gap: MTDS DeFi parquets are stale

- `market-data-tick-defi-prd-central-element-323112` exists but:
  - `raw_tick_data/by_date/` last day = `day=2026-05-08` (6 days stale as of 2026-05-14)
  - `lst_rates/` last date = `date=2026-04-14` (30 days stale) — this is the primary staking-rate signal for
    `carry_staked_basis`

The lst_rates gap is especially significant: carry_staked_basis needs current LST staking yields (stETH, rETH, cbETH,
JitoSOL) to size the carry leg. 30-day stale data means the backtest would use April 14 staking rates for May signals.

## Verification

```bash
# Both DeFi feature buckets empty
gsutil du -s gs://features-onchain-central-element-323112/
# → 0  gs://features-onchain-central-element-323112

gsutil du -s gs://features-delta-one-defi-prd-central-element-323112/
# → 0  gs://features-delta-one-defi-prd-central-element-323112

# MTDS DeFi market data stale
gsutil ls gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/ | tail -5
# → last entry: .../day=2026-05-08/

gsutil ls gs://market-data-tick-defi-prd-central-element-323112/lst_rates/ | tail -5
# → last entry: .../date=2026-04-14/
```

## Why it matters

- **B-015 paper backtest is blocked** until DeFi feature parquets exist in GCS. Running the backtest on empty features
  produces a meaningless P&L report.
- **May-23 live DeFi gate requires feature pipeline green** (Group B — data-correctness readiness check item B.3 in
  master readiness checklist). An empty feature bucket is pre-flight blocking.
- **carry_staked_basis archetype requires** `aave_lending_rates`, `aave_utilization`, `rate_impact`, `onchain_perps`
  feature groups — none exist in GCS.
- **LST staking rate staleness** (lst_rates 30 days old) means MTDS needs a catch-up run before the backtest date window
  is valid.

## Recommended decision

Operator triage required on two items:

**1. DeFi features pipeline: has the features-onchain service ever been pointed at prod?**

- If yes but bucket wrong: need to locate where features parquets actually landed and either copy or repoint the engine.
- If no: need to schedule a features-onchain backfill run (DeFi asset_group, 2026-04-14 to 2026-05-14 at minimum for the
  B-015 window). This requires: (a) identifying the features-service responsible for DeFi carry_staked_basis signals
  (likely `unified-features-interface` or a `features-onchain-service`) (b) confirming that service's CLI + GCS output
  bucket (c) running the backfill on a VM with ADC

**2. MTDS lst_rates catch-up: has the LST rates handler been paused?**

- `lst_rates/` is 30 days stale — this looks like a handler outage, not expected gap.
- Needs MTDS operator investigation: which handler produces `lst_rates/` data and why it stopped at 2026-04-14.

**B-015 unblocking path**: resolve items 1 and 2, then re-run Phase 1 prereq check before launching Phase 2 (paper
backtest).

## Cross-side ping filed

Cross-side ping filed at `plans/active/_agent_pings.md` simultaneously with this issue doc. Blocking on Ikenna ACK per
B-015 Phase 1 protocol.

## Suggested owner

Ikenna (operator triage on DeFi feature pipeline architecture + MTDS lst_rates gap). Harsh slot 9 standing by; will
resume Phase 2 launch on Ikenna ACK + pipeline green.
