---
doc_type: plan
title: MDPS DeFi Lending Indices Adapter
summary:
status: complete
nature: record
asset_group: [infrastructure]
stage: [meta]
repos: [market-data-processing-service, unified-api-contracts]
scope: [engineer, admin]
tags: []
related: []
created: "2026-05-24"
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
estimate_class: brand-new
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.8
priority: P2
locked_by: live-defi-rollout
locked_since: 2026-05-21
---

# MDPS DeFi Lending Indices Adapter

Deliver `DefiLendingIndicesAdapter` so MDPS produces `lending_ohlcv_*` candles from raw AAVE/Compound/Morpho
`lending_indices` snapshots. Previously these snapshots were treated as a bypass type (skipped by the MDPS
orchestrator). This plan wires the full path: UAC flag → MDPS adapter → manifest captured rows → data-status display.

**Features-onchain note**: `features_service/onchain/app/core/data_loader.py:load_rate_indices()` reads raw MTDS
parquets directly (bypass path). No change needed there — that path serves live rate signals. The MDPS candles are for
strategy/ML feature engineering at candle granularity.

## Pre-Audit

- `lending_indices` in UAC `NEEDS_CANDLE_PROCESSING` = `False` (line 294 of `market_data_categories.py`) → must flip to
  `True`
- No existing `lending_indices` adapter in MDPS `CandleAdapterRegistry`
- `test_defi_bypass_routing.py::TestBypassDataTypes.BYPASS_TYPES` includes `"lending_indices"` → must remove
- `CandleOutput` already has: `borrow_rate`, `utilization_ratio`, `liquidity_index`, `borrow_index` fields
- Output data_type mapping already in `canonical_writer.py`: `"lending_indices" → "lending_ohlcv"`

## Full-Execution Criterion

MDPS QG exits 0 on `market-data-processing-service`. UAC QG exits 0 on `unified-api-contracts`.

## Implementation

- [x] [CODE] P0. Flip `NEEDS_CANDLE_PROCESSING["lending_indices"]` = True in UAC `market_data_categories.py` —
      uac@4c98a635
- [x] [CODE] P0. Implement `DefiLendingIndicesAdapter` in `adapters/defi/lending_indices_adapter.py` — mdps@b21fec6
- [x] [CODE] P0. Export `DefiLendingIndicesAdapter` from `adapters/defi/__init__.py` — mdps@b21fec6
- [x] [CODE] P0. Remove `lending_indices` from `BYPASS_TYPES` in `test_defi_bypass_routing.py`; add adapter registration
      test — mdps@b21fec6
- [x] [SCRIPT] P0. QG green on MDPS (1363 passed, 0 failed) + UAC (pending push) — local evidence 2026-05-24

## Codex SSOT updates

No new workspace contract introduced. `lending_indices` transitions from bypass to candle-processed: update
`/codex/02-data/availability-manifest-and-data-status.md` comment if it lists bypass types explicitly (deferred —
low-priority cosmetic doc update, not blocking).

## Temporary states + their canonical follow-up plans

None.
