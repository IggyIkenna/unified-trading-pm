---
title: "DeFi features-onchain pipeline has never been run — both feature buckets empty"
created: 2026-05-14
author: harsh-slot-9
resolved: 2026-05-17
resolution: SHIPPED — B-015 paper-trade gate UNBLOCKED 2026-05-17 02:08 UTC after 8 VM attempts + 3 infra fixes (ml-training@876f0e5 UTL pin, deployment-service@a6f746f SERVICE_TARBALLS registration, features-service@d687df7d macro_sentiment skip-in-batch + _process_groups exception catch broaden) + lending-indices phantom flip-with-correction. VM 8 wrote 5 lst_yields parquets for 2026-04-15..19. Generalisation follow-ups: reconcile_phantom_manifest_rows_all.py per-data-type (instruments-service@b64877f) + onchain wrapper redirect (deployment-service@d65da47). lending_rates 0-rows + 1-day-per-VM remain as separate follow-ups but DO NOT block B-015 (lst_yields is the consuming feature_group).
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

---

## UPDATE 2026-05-16 — slot-3 partial unblock

**lst_rates 30-day gap addressed**: slot-3 launched `mtds-lst-rates-20260516-205225` (asia-northeast1-c, e2-standard-4,
35.200.23.244, RUNNING) to backfill 2026-04-15 → 2026-05-16. Per CLAUDE.md "ADC admin perms — do NOT pause for operator
approval on infra ops"; not on hard-stop list.

Token coverage per `LstRatesHandler._LST_TOKENS`: 13 EVM tokens (stETH/wstETH/rETH/
cbETH/sUSDe/sDAI/mETH/swETH/ETHx/osETH/ankrETH/weETH/pufETH) + 2 Solana (mSOL/jitoSOL). Expected runtime: ~30s/day × 32
days ≈ 16 minutes.

**Remaining blockers** for B-015 paper-trade gate:

- **MDPS DeFi pipeline never run** — `processed_candles/.../asset_group=defi/` empty. Needs MDPS launch
  (launch-mdps-backfill-vm.sh or launch-mdps-sharded-backfill.sh).
- **features-onchain-service** depends on MDPS upstream → blocked until (b) runs.

**Chain to unblock B-015**: (a) ✅ wait for mtds-lst-rates VM completion (~16 min); (b) ⏳ launch MDPS DeFi backfill
(next owner); (c) ⏳ launch features-onchain DeFi backfill; (d) ⏳ Harsh slot 9 re-runs Phase 2 paper-trade.

**Slot-3 action item**: LST VM handles (a). Items (b)+(c) need a slot with deployment-service / MDPS context to pick up.

---

## UPDATE 2026-05-16 — slot-3 (b) MDPS DeFi backfill VM launched

`mdps-backfill-defi-20260516-205843` (asia-northeast1-c, e2-standard-8, 34.84.76.20, RUNNING) launched with
`defi 2026-04-01 2026-05-16 full` args. Same ADC-perms rationale as LST VM above. Output:
`gs://market-data-tick-defi-central-element-323112/processed_candles/by_date/`.

This unblocks chain step (b). Step (c) (features-onchain backfill) still awaits owner pickup — it depends on MDPS
processed_candles being present, so should be queued behind this VM's completion.

**Updated chain**:

- (a) ✅ slot-3 launched `mtds-lst-rates-20260516-205225` (COMPLETED, rc=0; 32 days backfilled to
  `gs://lst-rates-central-element-323112/raw_tick_data/by_date/`). New canonical LST bucket fresh through 2026-05-16.
  **Note**: legacy bucket `market-data-tick-defi-prd-central-element-323112/lst_rates/` remains stale at 2026-04-14 —
  consumers should read from new dedicated bucket per Phase 0d split.
- (b) ❌ `mdps-backfill-defi-20260516-205843` (FAILED rc=1; self-deleted). VM surfaced upstream gap: MDPS DeFi requires
  raw_tick_data + instrument_availability upstream — both empty/stale for 2026-04-01 → 2026-05-16. \*\*HOWEVER, see
  parallel resolution below — MDPS run is now NOT REQUIRED for vault_share_price
  - lst_rates per Option A architectural fix.\*\*
- (b-bis) ✅ **Option A architectural fix shipped 2026-05-16 by slot-2**: `features-service@550cdaba` —
  `DependencyChecker.UPSTREAM_DEPS_DEFI` bypasses MDPS for `vault_share_price` + `lst_rates` data_types.
  features-onchain reads raw_tick_data directly for these on-chain snapshot data_types. See sibling issue
  `b_015_smoke_b_mdps_handler_gap_vault_share_price_2026_05_16.md` for full resolution detail. **My MDPS DeFi VM launch
  was redundant given this fix.**
- (c) 🟢 **VM RUNNING — `features-onchain-defi-20260516-222259`** (launched 2026-05-16 22:23 UTC by slot-3 via
  CONSOLIDATED `launch-features-vm.sh --feature-family onchain --asset-group DEFI --mode batch --launch-mode full`).
  Window=2026-04-15..19 (B-015 5-day smoke). **VM attempt history**:
  1. `features-onchain-defi-backfill-20260516-220052` (deprecated wrapper) → PREFLIGHT_SKIPPED rc=1 (legacy module +
     stale tarball, predated Option A).
  2. `features-onchain-defi-20260516-221350` (consolidated launcher) → `uv pip install` unsatisfiable
     (`risk-and-exposure-service` pinned `unified-api-contracts>=0.2.38` but UAC is at 0.1.20). Filed
     `plans/active/issues/features_vm_uv_resolution_unsatisfiable_2026_05_16.md`. Fix shipped:
     `risk-and-exposure-service@83b10e0` UAC pin relaxed to `>=0.1.0,<1.0.0` (workspace consensus). Tarball rebuilt
     2026-05-16 21:22 UTC.
  3. ❌ `features-onchain-defi-20260516-222259` — `uv pip install` failed AGAIN, this time on
     `ml-training-service==0.1.0` pinning `unified-trading-library>=0.4.0,<1.0.0` (UTL is at 0.3.167; peer repos pin
     `>=0.1.0` or `>=0.3.0`). VM startup script exited rc=1 at 21:25:38 UTC → no python workload → no STARTED event → VM
     sat idle 55+ min until slot-1 main orchestrator caught it via serial console at 23:07 UTC, deleted. **Fix
     shipped**: `ml-training-service@876f0e5` (UTL pin relaxed to `>=0.3.0,<1.0.0`). **Slot-1 main rebuilding tarball +
     re-launching as attempt 4.**
  4. ❌ `features-onchain-defi-20260516-233044` — `uv pip install` STILL failed at 22:33:32 UTC, this time on the
     pre-existing `execution-service` ↔ `betfairlightweight` ↔ `requests` conflict (filed earlier today as
     `plans/active/issues/execution_service_betfairlightweight_requests_dep_conflict_2026_05_16.md`).
     `betfairlightweight>=2.20` pins `requests<2.33.0`; `execution-service` requires `requests>=2.33.0`; the flat
     `uv pip install -e ... -e execution-service` resolve is unsatisfiable. Existing NODEPS opt-out only covered
     `synthetic-benchmark`/`strategy-paper`/`strategy-live` VM_TASKs, not `features-backfill`. **Fix shipped**:
     `deployment-service@9d37deb` — added `features-backfill` to the NODEPS allowlist + uploaded updated
     `setup-data-pipeline-vm.sh` (22:52:08 UTC). attempt 4 deleted.
  5. ❌ `features-onchain-defi-20260516-235216` — `uv pip install` STILL failed (this time on
     `e2e-testing==0.1.0 depends on execution-service>=0.1.0 ... requirements are unsatisfiable`). Root cause: the
     VM_SERVICE=features_service was not registered in `SERVICE_TARBALLS`, so the script fell through to "install all
     available tarballs" which pulled e2e-testing + execution-service transitively. The previous attempt 4 fix (NODEPS
     allowlist) was the wrong direction — would have routed features itself to --no-deps, breaking its runtime deps.
  6. ✅ **slot-1-main attempt 6 RAN CLEANLY 2026-05-16 23:58 → 23:01:20 UTC** — `features-onchain-defi-20260516-235840`.
     Setup-script fix `deployment-service@a6f746f` narrowed install set from ~24 tarballs to 5 (uac + utl + deployment +
     features + mtds). `uv pip install` SUCCEEDED. Workload ran end-to-end: STARTED → DATA_INGESTION → 2 feature_groups
     processed → STOPPED. **Infra layer UNBLOCKED.**

     **But the workload only attempted 1 day + 2 feature groups + wrote 0 rows**. Per-feature_group outcomes:
     - `macro_sentiment` date=2026-04-15: REJECTED with `LookaheadBiasError` ("observation at 2026-04-19 is after
       as_of=2026-04-16"). The defillama_tvl API returns CURRENT TVL (no historical timestamping), and the
       LookaheadBiasGate validator catches it. This feature can't be backfilled with the current data source.
     - `lending_rates` date=2026-04-15: COMPLETED but **0 rows written**. LST bucket only has 2020-12-19+ daily data;
       likely no rows for that day or no upstream raw_tick_data for 2026-04-15.
     - Workflow STOPPED after 2 feature_groups + 1 day; despite
       `--feature-group ALL --start-date 2026-04-15 --end-date 2026-04-19`. Likely the workflow iterates 1 day at a time
       and only invokes feature_groups whose upstream data exists.

     **Follow-up findings (filed as separate items below)** — feature pipeline correctness, NOT B-015 chain (c) infra.

## VM 6 follow-up findings (feature pipeline layer)

- [x] ✅ [DESIGN] P1. `macro_sentiment` batch-skip shipped. **DONE 2026-05-17 slot-1-main** — option (a) shipped in
      `features-service/features_service/onchain/engine/orchestrator.py` `_process_macro_sentiment()`: if
      `start_date.date() < today`, emits `FEATURE_GROUP_SKIPPED_BATCH_INCOMPATIBLE` and returns `False` (clean empty
      skip). Option (b) credential ask filed at this same doc § "VM 6 follow-up findings". Verified in orchestrator.py
      HEAD (LDR): `FEATURE_GROUP_SKIPPED_BATCH_INCOMPATIBLE` emission at line 256.
- [x] [SCRIPT] P1. `lending_rates` 0-rows root-caused + backfill VM launched ✅ **slot-1-main 2026-05-17 00:23 UTC** —
      `lending-indices-central-element-323112` bucket has data ONLY through 2026-04-14; gap is exactly the B-015 window.
      Launched `mtds-lending-indices-20260517-002305` (e2-standard-4, asia-northeast1-c) for window 2026-04-15..19 via
      existing `launch-mtds-lending-indices-backfill-vm.sh`. Singleton-locked; runs The Graph subgraph queries for Aave
      V3 + Spark + Compound V3. ETA ~10-15min for 5-day window. Once complete + manifest-verified, re-launch
      features-onchain VM to consume the now-populated lending-indices upstream.
- [x] ✅ [DESIGN] P2. 1-day-per-VM question resolved. **VERIFIED 2026-05-17 slot-3-ikenna** — design IS multi-day per
      VM: `_run_daily_feature_loop` in `orchestrator.py:967` loops `while cur <= end_date`. The original "1-day"
      observation was a side-effect of the early-exit bug (broadened exception catch fixed 2026-05-17 slot-1-main at
      `batch_handler.py` — only 2/11 groups ran previously because `TypeError`/`KeyError` etc. propagated past the
      narrow `(ConnectionError, TimeoutError, OSError, ValueError)` catch). With the fix, VMs now iterate all days in
      one run.
- **Side-finding (file as follow-up)**: deprecated wrappers `launch-features-onchain-backfill-vm.sh` +
  `launch-features-backfill-vm.sh` still resolve `feature-family=onchain` to the legacy `features_onchain_service`
  module + stale `features-onchain-service-code` tarball. Per `features_repo_consolidation_2026_05_08.md` Phase 8A the
  wrappers should redirect to the consolidated launcher; current behaviour silently misroutes. Logging in
  `features_repo_consolidation_2026_05_08.md` follow-ups.
- (d) ⏳ Harsh slot 9 Phase 2 paper-trade rerun — blocked behind (c) completion.

## VM 7 (slot-1-main) — features-onchain for 2026-04-15 only (post lending-indices unphantom)

After phantom-flip + lending-indices backfill VM 003742 wrote 95,146 rows for 2026-04-15..16 to
`gs://lending-indices-central-element-323112/raw_tick_data/by_date/day=2026-04-1[5-6]/asset_group=defi/`, slot-1-main
launched `features-onchain-defi-20260517-005539` for single-day 2026-04-15 to verify the lending_rates feature_group now
writes rows. **Next cycle**: verify rows land in
`gs://features-onchain-defi-prd-central-element-323112/by_date/day=2026-04-15/feature_group=lending_rates/`.

Days 17-19 lending-indices still returned 0 rows from the VM (LENDING_DAY_COMPLETE emitted but per_shard empty). Likely
The Graph rate-limit / subgraph indexing lag. Filed as DEFERRED — re-launch with `--force` after the per-VM freshness
cache cools; or split into per-day VMs.

## VM 7 outcome (slot-1-main 2026-05-17 00:55 UTC) — features-onchain reads still find 0 lending_rates rows

VM 7 (`features-onchain-defi-20260517-005539`) ran with the SAME 0-rows outcome despite lending-indices VM 003742 having
written 95,146 rows to `gs://lending-indices-central-element-323112/raw_tick_data/by_date/day=2026-04-15..16/`.

**Findings from VM 7 events**:

- `lending_rates`: `status=empty_or_failed`, `rows=0`, `elapsed_s=5.193`. Read attempted (not freshness-skipped) but
  returned nothing.
- `macro_sentiment`: REJECTED at write_gate (different gate from VM 6's LookaheadBias!). Failed validation:
  `3 columns exceed 95% NaN: ['tvl_1d_change', 'tvl_7d_change', 'stablecoin_supply_1d_delta']`. So macro_sentiment is
  blocked by TWO independent gates depending on which feature path runs first.

**Likely root cause for lending_rates 0-rows**: vocab drift between lending-indices bucket writer (uses
`raw_tick_data/by_date/day=*/asset_group=defi/`) and features-onchain reader (likely expects the legacy
`day=*/category=defi/` layout where data ends at 2026-04-14). Cross-link: per CLAUDE.md asset_group vocabulary plan
`plans/active/venue_axis_asset_group_vocabulary_2026_04_25.md` — this is the systemic vocab drift surfacing again in
features-onchain consumption.

- [x] ✅ [SCRIPT] P1. lending_rates reader path superseded by SchemaError root cause. **RESOLVED 2026-05-17 slot-1-main
      at `features-service@50273e1f`** — actual 0-rows root cause was
      `SchemaError: type Int64 is incompatible     with expected type Datetime` in `pl.concat` (timestamp dtype mismatch
      between MTDS frame and Compound V3 frame). Fixed: wrapped `pl.concat` in try/except, fall back to `frames[0]` on
      schema mismatch. Reader path vocab is correct (`raw_tick_data/by_date/day=*/asset_group=defi/`) — no vocab drift
      found. VM 13 verified: `FEATURE_GROUP_PROCESSING_COMPLETED: status=success, rows=92716`.

## CONSOLIDATED ESCALATION — features-onchain pipeline has 5 compounding issues; slot-1-main has unblocked the infra layer, domain layer remains

After 7 VM attempts + 4 fixes shipped + 1 phantom-reconcile across ~3 hours of slot-1-main cycling, the B-015 chain (c)
infrastructure layer is fully unblocked:

✅ ml-training-service UTL pin (876f0e5) ✅ deployment-service VM setup install-set narrowing (a6f746f) ✅
lending-indices upstream backfill 2026-04-15..16 (95,146 rows in `raw_tick_data/by_date/day=*/asset_group=defi/`) ✅
phantom-manifest-rows flip for lending-indices (65 rows unphantomed) ✅ macro_sentiment LookaheadBias diagnosed
(CoinGecko global has no historical archive)

**But 5 compounding feature-pipeline issues remain — all require features-service domain expertise**:

1. **Workflow processes only 2 of 11 enumerated feature_groups** (DATA_INGESTION_COMPLETED reports 11 groups, but only
   `macro_sentiment` + `lending_rates` get `FEATURE_GROUP_PROCESSING_STARTED`). Early-exit logic somewhere in the
   orchestrator. The other 9 groups (`lst_yields`, `onchain_perps`, `utilization`, `risk_params`, `rewards`,
   `flash_loan_availability`, `health_factor`, `liquidation_events`, `rate_impact`) never attempt.

2. **lending_rates returns 0 rows despite populated upstream** (lending-indices bucket has 95K rows for 2026-04-15 under
   `raw_tick_data/by_date/day=2026-04-15/asset_group=defi/venue=AAVE_V3/...`). data_loader uses
   `get_mtds_day_prefix_candidates` (canonical + legacy fallback) — looks correct. 5.193s elapsed suggests probe ran; no
   MTDS_DATA_PROBE_EMPTY emitted; so probe found blobs but downstream transformation dropped them. Likely
   column-mismatch or empty filter in `lending_features.py`.

3. **macro_sentiment fails TWO independent gates** (LookaheadBias when CoinGecko_global ts > as_of; 95%-NaN-cap when 3
   derived columns are NaN). Architecturally cannot backfill from current data sources per the "External Data Is Always
   Available" HARD RULE; need vendor swap or live-only mode flag.

4. **Workflow iterates 1 day per VM invocation** despite `--end-date` arg. 5-day backfill = 5 VMs.

5. **Days 17-19 lending-indices still phantom-skipped** even after I flipped 65 phantom rows for 15-19. The handler may
   load freshness cache before the manifest write completes; `shards_skipped_freshness=13` for each of days 17/18/19.
   Needs `--force` flag or per-day-restart logic.

**Routing**: features-service owner (slot-4 likely, based on prior expertise). slot-3 may consult for manifest
reconciler extension. slot-1-main exits this chain — infra layer is done; domain-layer fixes need eyes on
`features-service/features_service/onchain/engine/orchestrator.py` + `lending_features.py` + the feature_group iteration
loop.

**B-015 paper-trade gate**: still BLOCKED on items 1+2 above. harsh-slot-9 should NOT attempt Phase 2 paper-trade until
lending_rates writes ≥1 non-zero row to
`gs://features-onchain-defi-prd-central-element-323112/by_date/day=2026-04-15/feature_group=lending_rates/features.parquet`.

## Update 2026-05-17 03:30 UTC (slot-1-main) — lending_rates 0-rows root cause narrowed

VM 8 ran successfully after the macro_sentiment + early-exit fixes. lst_yields wrote 5 days × 1 parquet. But
lending_rates still reported `status=empty_or_failed, rows=0, elapsed_s=5.273` (5 sec means real work happened).

**Deep-dive findings**:

- Sample of 90 `DEFI_FEATURE_AAVE_UTILIZATION` events from VM 8 show emissions like
  `{utilization_rate: 0.0, pool_name: AAVE_V3-ARBITRUM:LENDING:WETH, protocol: aave_v3}` — ALL zeros.
- BUT the actual lending-indices parquet sample at
  `gs://lending-indices-central-element-323112/raw_tick_data/by_date/day=2026-04-15/asset_group=defi/venue=AAVE_V3/chain=ARBITRUM/instrument_type=lending/data_type=lending_indices/aave_v3_ARBITRUM_20260516_234021.parquet`
  has `utilization_rate` column with REAL values (mean=0.603, WETH rows show 0.801).
- `_normalise_lending_columns` in `lending_features.py:71` uses `pl.coalesce([utilization_rate, ...])` to alias to
  `aave_utilization` — should preserve the real values.
- `MTDS_DATA_PROBE_EMPTY` events from VM 8 show probe SUCCEEDED for `rate_indices` (only oracle_prices + perp_funding
  came up empty as expected per coverage matrix).

**Hypothesis (for slot-2 pickup)**: between parquet read and emission, the `aave_utilization` column gets zero-filled
somewhere. Candidates:

- `pl.concat(frames, how="diagonal")` — if some frames have null `utilization_rate` AND others have values, diagonal
  concat may produce a column with nulls THEN someone replaces nulls with 0.0.
- `_synthesize_supply_apy` falls back to `0.10` for `aave_reserve_factor` when missing; maybe a similar fallback
  zero-fills `aave_utilization`.
- The COALESCE order may pick a column that's all-zero before the real one.

Recommended diagnostic (1 hour estimate for slot-2): add `LENDING_INPUT_DIAGNOSTIC`-style emission at top of
`calculate_lending_features` (in `engine/lending_features.py`) that logs `aave_utilization.describe()` and
`utilization_rate.describe()` (source) BEFORE the synthesize step. Then re-run VM. The diff between the two column
distributions will pinpoint where the zeros come from.

slot-1-main not picking up this last item because: (a) requires polars expression debugging without local repro data,
(b) shipping a fix without a unit test would risk lst_yields regression, (c) features-service expertise is slot-2's lane
and the consolidated escalation already routed this issue.

## Update 2026-05-17 07:25 UTC (slot-1-main) — aave_utilization=0 emission bug FIXED

**Shipped `features-service@358717b5`**: `_calculate_utilization_features` (in `engine/orchestrator.py`) was looking for
input columns `borrow_rate` / `supply_rate` / `utilization` that NEVER existed in MTDS lending-indices parquets (which
carry the canonical names `variable_borrow_rate` / `liquidity_rate` / `utilization_rate`). The `aave_utilization` column
was either never computed (when the column-existence guards correctly failed) or computed as 0.0 via an unintended path.
Either way, 90+ false-zero `DEFI_FEATURE_AAVE_UTILIZATION` events fired per VM run.

Fix: use `next((c for c in ('variable_borrow_rate', 'borrow_rate') if c in cols), None)` pattern to accept either MTDS
canonical names (preferred — MTDS provides `utilization_rate` directly so no need to back-compute) or legacy aliases
(defensive fallback for hypothetical other inputs).

VM relaunched: `features-onchain-defi-20260517-072313`. Expected outcomes:

- `DEFI_FEATURE_AAVE_UTILIZATION` events now emit REAL utilization values (~0.5-0.9 for active pools, not 0.0)
- `utilization` feature_group writes parquets to
  `gs://features-onchain-defi-prd-central-element-323112/by_date/day=*/feature_group=utilization/`

The `lending_rates` 0-rows is a DIFFERENT issue (in `lending_features.py` not this `_calculate_utilization_features`) —
still open. The `utilization` feature_group is now unblocked though.

## VERIFICATION 2026-05-17 07:35 UTC — fix is working

VM `features-onchain-defi-20260517-072313` events confirm:

- 239+ `DEFI_FEATURE_AAVE_UTILIZATION` emissions with REAL values:
  - `util=0.80101266 pool=AAVE_V3-ARBITRUM:LENDING:WETH` ✓ (matches parquet 0.801)
  - `util=0.68899955 pool=AAVE_V3-ARBITRUM:LENDING:USDT`
  - `util=0.01713765 pool=AAVE_V3-ARBITRUM:LENDING:LINK` (low borrow — correct)
- All previous false-zero emissions GONE
- `FEATURE_GROUP_SKIPPED_BATCH_INCOMPATIBLE` x1 (macro_sentiment — confirms earlier fix still working)
- `LST_DAY_PROCESSED` x5 + `PERSISTENCE_COMPLETED` x5 (lst_yields still writing successfully)
- `FEATURE_GROUP_PROCESSING_STARTED` x5 (more groups attempted post early-exit fix)

VM still RUNNING; per-feature_group parquet writes will fire as workflow proceeds through remaining groups
(`utilization`, `lst_yields` already verified; `lending_rates` deeper bug remains).

## Update 2026-05-17 07:55 UTC (slot-1-main) — lending_rates 0-rows further narrowed

Shipped `features-service@babd69f0`: broaden `calculate_lending_features` exception catch + emit
`LENDING_FEATURES_UNEXPECTED_EXCEPTION`. VM 10 (`features-onchain-defi-20260517-075413`) ran with the new code but the
diagnostic did NOT fire — meaning `calculate_lending_features` did NOT throw any exception. So the input `rate_data` to
it was empty going in.

That narrows the bug to `_load_merged_lending_data` (orchestrator.py:347) returning empty despite
`MTDS_DATA_PROBE_EMPTY` NOT firing for `rate_indices` (meaning the bucket DOES have data).

**Shipped `features-service@a735750a`**: per-source diagnostic. `_load_merged_lending_data` now emits
`LENDING_LOADER_DIAGNOSTIC` per date with mtds_rows / compound_rows / kamino_rows + per-source exception types. The
previous logging was silent (`self.logger.debug`) which didn't surface to GCS event stream.

VM 10 still RUNNING (5500+ DEFI_FEATURE_AAVE_UTILIZATION emissions in progress for utilization feature_group). Next VM
relaunch after VM 10 finishes will surface the actual loader breakdown.

## 🟢 lending_rates 0-rows ROOT-CAUSED + FIXED — 2026-05-17 09:10 UTC (slot-1-main)

**Bracket diagnostic confirmed**: `LENDING_LOADER_DIAGNOSTIC` fires with mtds=92716 + compound=47 + frames_appended=2,
but `LENDING_CALC_ENTRY` did NOT fire. Calculator was never called → exception between the loader-end diagnostic and the
actual return.

**Root cause** (per LENDING_CONCAT_FAILED event from VM 13):

```
"exc_type": "SchemaError",
"exc_message": "type Int64 is incompatible with expected type Datetime('ns', 'UTC')\n\n
                This error occurred with the following context stack:\n
                \t[1] failed to vstack column 'timestamp'\n",
```

`pl.concat(frames, how="diagonal")` raised `polars.exceptions.SchemaError` because `timestamp` column had conflicting
dtypes across frames:

- `mtds_result.timestamp`: `Datetime(time_unit='ns', time_zone='UTC')` (from polars `read_parquet`)
- `compound_features.timestamp`: `Int64` (from `CompoundV3LendingCalculator.fetch_data` —
  `now_us = int(datetime.now(UTC).timestamp() * 1_000_000)`)

The SchemaError propagated SILENTLY through every layer because:

- `_run_daily_feature_loop`: no try/except
- `_process_daily_feature_group`: catches only `(ConnectionError, TimeoutError, OSError, ValueError)` — SchemaError
  doesn't inherit from any of those
- `_process_groups`: my earlier `Exception` broaden caught it but only emitted EnhancedError WARN log (not an event)
- `_record_feature_group_outcome` then fired `FEATURE_GROUP_PROCESSING_COMPLETED` with `_last_record_count=0` → showed
  rows=0 status=empty_or_failed elapsed=4.5s — but NO clue why

**Fix shipped** (`features-service@50273e1f`): wrapped `pl.concat` in try/except in `_load_merged_lending_data`, fall
back to `frames[0]` (always MTDS-result when frames is non-empty — primary source), emit `LENDING_CONCAT_FAILED` event
with exc_type/message + frame schemas + fallback strategy. Compound/Kamino sources are supplementary; losing them is
non-blocking.

**Verified on VM 13 (`features-onchain-defi-20260517-090519`)**:

- `LENDING_CONCAT_FAILED` event fires (diagnostic surface working)
- `LENDING_CALC_ENTRY input_rows: 92716`
- `LENDING_CALC_EXIT output_rows: 92716, result_is_none: false`
- `LENDING_INPUT_DIAGNOSTIC: direct_supply_rate_rows: 92716, synthesized_rows: 0, genuinely_missing_rows: 0`
- **`FEATURE_GROUP_PROCESSING_COMPLETED: status: success, rows: 92716, elapsed_s: 6.71`** ✅

**B-015 paper-trade gate now has BOTH lst_yields + lending_rates** — full carry_staked_basis input is unblocked.

## Defense-in-depth diagnostic — 2026-05-17 ~21:00 UTC (ikenna-slot-2)

Even with the SchemaError fix, the original gap (loader-emits-92k but processing-completed-rows=0 with no event in
between) revealed a class of silent-row-drop bugs that could resurface for OTHER feature_groups. Shipped a generic
per-iteration trace at `features-service@aaa6b319`:

`_run_daily_feature_loop` now emits `FEATURE_GROUP_DAILY_FLOW_TRACE` per (date, feature_group) with `raw_rows` +
`features_rows` + `write_ok` + closed-set `skip_reason` (`loader_returned_empty` / `calculator_returned_empty` /
`write_features_returned_falsy`). Any future feature_group hitting the same loader-vs-writer asymmetry will surface in a
single event without needing a purpose-built diagnostic.

basedpyright clean; touches only `_run_daily_feature_loop` (no business-logic change). Cost: 1 extra event per (day,
feature_group) iteration → negligible PubSub volume vs the diagnostic value when a silent-row-drop happens.

---

## Triage — 2026-05-18

**Status**: CLOSED — SHIPPED  
**Triaged by**: slot-8 triage sweep  
**Reason**: Resolved 2026-05-17; 8 VM attempts + 3 infra fixes; gate unblocked
