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

## What I found

During B-015 Phase 1 prereq check (carry_staked_basis paper backtest pipeline-state
verification, item (c) — features-service DeFi feature parquets), both DeFi feature
buckets are empty:

- `features-onchain-central-element-323112` — bucket exists, `gsutil du -s` = 0 bytes
- `features-delta-one-defi-prd-central-element-323112` — bucket exists, `gsutil du -s` = 0 bytes

The `colocated_engine.py` paper backtest engine reads from `features-onchain-central-element-323112`
for the `DEFI` category (line 138: `"DEFI": "features-onchain-central-element-323112"`), using
path template: `onchain_features/by_date/day={date}/feature_group={group}/features.parquet`
with feature groups: `["aave_lending_rates", "aave_utilization", "rate_impact", "onchain_perps"]`.

Both buckets have 0 bytes — the features-onchain service (or whatever service produces DeFi
feature parquets for carry_staked_basis) has never been run against GCS production buckets.

**Technical consequence**: `_load_features_for_date()` (colocated_engine.py:817) returns `{}`
silently when parquets are missing (line 845: `except Exception: pass`). The engine emits ticks
with empty feature dicts. The carry_staked_basis strategy will receive no signal data — either
never trades or trades on zero signals. The paper backtest P&L report would be meaningless.

## Secondary gap: MTDS DeFi parquets are stale

- `market-data-tick-defi-prd-central-element-323112` exists but:
  - `raw_tick_data/by_date/` last day = `day=2026-05-08` (6 days stale as of 2026-05-14)
  - `lst_rates/` last date = `date=2026-04-14` (30 days stale) — this is the primary
    staking-rate signal for `carry_staked_basis`

The lst_rates gap is especially significant: carry_staked_basis needs current LST
staking yields (stETH, rETH, cbETH, JitoSOL) to size the carry leg. 30-day stale data
means the backtest would use April 14 staking rates for May signals.

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

- **B-015 paper backtest is blocked** until DeFi feature parquets exist in GCS. Running the
  backtest on empty features produces a meaningless P&L report.
- **May-23 live DeFi gate requires feature pipeline green** (Group B — data-correctness
  readiness check item B.3 in master readiness checklist). An empty feature bucket is
  pre-flight blocking.
- **carry_staked_basis archetype requires** `aave_lending_rates`, `aave_utilization`,
  `rate_impact`, `onchain_perps` feature groups — none exist in GCS.
- **LST staking rate staleness** (lst_rates 30 days old) means MTDS needs a catch-up run
  before the backtest date window is valid.

## Recommended decision

Operator triage required on two items:

**1. DeFi features pipeline: has the features-onchain service ever been pointed at prod?**
   - If yes but bucket wrong: need to locate where features parquets actually landed
     and either copy or repoint the engine.
   - If no: need to schedule a features-onchain backfill run (DeFi asset_group, 2026-04-14
     to 2026-05-14 at minimum for the B-015 window). This requires:
     (a) identifying the features-service responsible for DeFi carry_staked_basis signals
     (likely `unified-features-interface` or a `features-onchain-service`)
     (b) confirming that service's CLI + GCS output bucket
     (c) running the backfill on a VM with ADC

**2. MTDS lst_rates catch-up: has the LST rates handler been paused?**
   - `lst_rates/` is 30 days stale — this looks like a handler outage, not expected gap.
   - Needs MTDS operator investigation: which handler produces `lst_rates/` data and why
     it stopped at 2026-04-14.

**B-015 unblocking path**: resolve items 1 and 2, then re-run Phase 1 prereq check before
launching Phase 2 (paper backtest).

## Cross-side ping filed

Cross-side ping filed at `plans/active/_agent_pings.md` simultaneously with this issue doc.
Blocking on Ikenna ACK per B-015 Phase 1 protocol.

## Suggested owner

Ikenna (operator triage on DeFi feature pipeline architecture + MTDS lst_rates gap).
Harsh slot 9 standing by; will resume Phase 2 launch on Ikenna ACK + pipeline green.
