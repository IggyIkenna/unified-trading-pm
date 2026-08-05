---
doc_type: issue
title:
  PUFFER-style declared-vs-actual lst_rates mismatch in PROTOCOL_CAPABILITIES affects 13 venues across 6 protocols; 5
  additional protocols have no entry at all
summary: >-
  Cross-reference audit of all 101 phase="live" DeFi venues against PROTOCOL_CAPABILITIES declarations. Found 13 venues
  across 6 protocols where lst_rates is actually written (per expected_coverage.py + lst_rates_handler.py) but NOT
  declared in PROTOCOL_CAPABILITIES — the same PUFFER-style mismatch class. 5 additional live protocols (BINANCE,
  COINBASE, ROCKETPOOL, SANCTUM, SOLBLAZE) have NO PROTOCOL_CAPABILITIES entry at all. 3 protocols (LIDO, ETHERFI,
  EIGENLAYER) declare "rewards" with no matching handler operation.
status: open
nature: issue
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, market-tick-data-service, instruments-service]
scope: [engineer]
tags: [defi, protocol-capabilities, lst-rates, honest-coverage, data-type-mismatch, audit]
related:
  [
    /plans/active/issues/defi_six_lst_vault_venues_missing_protocol_capabilities_2026_07_31.md,
    /codex/02-data/honest-coverage-model.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
created: "2026-08-05"
author: slot-7 (data_engineering craft)
last_updated: "2026-08-05"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
resolved_by:
source: >-
  AO-dispatched audit (slot-7) completing defi_six_lst_vault_venues_missing_protocol_capabilities_2026_07_31.md todo 2
  (P3). Cross-referenced PROTOCOL_CAPABILITIES (_defi.py), DEFI_VENUE_PHASE (defi_venues.py), expected_coverage.py
  per-venue data_types, lst_rates_handler.py token→protocol mapping, and the 2026-07-22 RESTAKING_LRT_VENUES re-stamp
  scripts.
locked_by:
locked_since:
context_scope:
  [
    unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py,
    unified-api-contracts/unified_api_contracts/registry/expected_coverage.py,
    unified-api-contracts/unified_api_contracts/registry/defi_venues.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/lst_rates_handler.py,
  ]
---

# PUFFER-style PROTOCOL_CAPABILITIES lst_rates audit

## What I found

Cross-referenced all 101 `phase="live"` DeFi venues' `PROTOCOL_CAPABILITIES` entries (`_defi.py`) against two
independent sources of ground truth for what MTDS actually writes:

1. **`expected_coverage.py`** — per-venue `data_type` lists that `measure_honest_coverage.py` uses for its EXPECTED
   matrix
2. **`lst_rates_handler.py`** token→protocol mapping (`"pufETH": "puffer"`, etc.)

Three finding classes:

### Finding A — PUFFER-style: `lst_rates` written but NOT declared (13 venues, 6 protocols)

These protocols declare `staking_yields` and/or `oracle_prices` in PROTOCOL_CAPABILITIES but `expected_coverage.py`
independently maps them to `["lst_rates"]` — confirming the lst_rates_handler actually writes `data_type="lst_rates"`
for them. This is the SAME mismatch class as PUFFER (the original finding that prompted this audit).

| Protocol | Venues affected                          | Declared data_types           | Actual (per expected_coverage.py) |
| -------- | ---------------------------------------- | ----------------------------- | --------------------------------- |
| KELPDAO  | ETHEREUM                                 | staking_yields, oracle_prices | **lst_rates**                     |
| RENZO    | ETHEREUM, ARBITRUM                       | staking_yields, oracle_prices | **lst_rates**                     |
| BEEFY    | ETHEREUM, ARBITRUM, BASE, AVALANCHE, BSC | staking_yields                | **lst_rates**                     |
| IDLE     | ETHEREUM                                 | staking_yields                | **lst_rates**                     |
| PENDLE   | ETHEREUM, ARBITRUM                       | staking_yields, oracle_prices | **lst_rates**                     |
| YEARN_V3 | ETHEREUM, ARBITRUM                       | staking_yields, oracle_prices | **lst_rates**                     |

Root cause: the 2026-07-22 `RESTAKING_LRT_VENUES` re-stamp (`canonicalize_restaking_lrt_catalog_2026_07_22.py`)
reclassified KELPDAO/RENZO/PUFFER catalogue rows from `instrument_type=LST` → `RESTAKING`, and
`restamp_restaking_lrt_availability_index_2026_07_22.py` restamped the availability index too — but neither script
updated `PROTOCOL_CAPABILITIES` to add `lst_rates` to these protocols' `data_types`. For BEEFY/IDLE/PENDLE/YEARN_V3 the
lst_rates path was wired independently (vault pricePerShare/getRate handlers) without a corresponding
PROTOCOL_CAPABILITIES update.

Evidence:

- `expected_coverage.py:364-369` maps KELPDAO/RENZO/YEARN_V3/BEEFY/IDLE/PENDLE to `["lst_rates"]`
- `lst_rates_handler.py:540` maps `"pufETH": "puffer"` (same handler writes for all LST tokens)
- `restamp_restaking_lrt_availability_index_2026_07_22.py:57`:
  `RESTAKING_LRT_VENUES = {"ETHERFI", "RENZO", "KELPDAO", "PUFFER"}`
- `defi_venue_capabilities.py:315`: PUFFER already has `"lst_rates": "2024-02-01"` added

### Finding B — Live venues with NO PROTOCOL_CAPABILITIES entry (6 venues, 5 protocols)

These are `phase="live"` and have real captured data, but NO key exists in `PROTOCOL_CAPABILITIES` at all:

| Venue               | expected_coverage says              |
| ------------------- | ----------------------------------- |
| BINANCE-ETHEREUM    | lst_rates                           |
| BINANCE-BSC         | lst_rates                           |
| COINBASE-ETHEREUM   | (no entry — oracle_prices inferred) |
| ROCKETPOOL-ETHEREUM | (no entry)                          |
| SANCTUM-SOLANA      | lst_rates                           |
| SOLBLAZE-SOLANA     | (no entry)                          |

BINANCE writes `lst_rates` for wBETH (confirmed in `expected_coverage.py:363` + `venue_launch_dates.py:268-274`). The
others are Solana LST venues or EVM LST venues whose PROTOCOL_CAPABILITIES entries were never authored.

### Finding C — "rewards" declared with no handler operation (3 protocols)

LIDO, ETHERFI, and EIGENLAYER declare `"rewards"` in `data_types` but have no `collect-rewards` operation in
`mtds_operations`. ETHERFI has a live WS connector (`etherfi_ethereum_ws.py`) that handles rewards — but the operation
isn't wired into the MTDS CLI's `--operation` dispatch table. These are aspirational declarations.

## Why it matters

- **Layer-1 honest-coverage denominator**: `_venue_itype_is_valid()` gates every (venue, instrument_type, data_type)
  tuple through PROTOCOL_CAPABILITIES. Protocols missing `lst_rates` from their declared `data_types` silently exclude
  those tuples from the EXPECTED matrix — actual captured data exists but is invisible to the completeness metric.
- **Finding A** is the same documented failure mode as PUFFER (the original issue's source):
  `measure_honest_coverage.py --diagnose-layer1` reports lower completeness than reality because the declared set
  doesn't match what handlers write.
- **Finding B** is strictly worse: these venues have NO tuples in EXPECTED at all, so their capture status is wholly
  invisible to Layer-1.
- **Finding C** is low-severity (declared but not yet collected) but contributes to the system's 57-missing/83-stray
  Layer-1 baseline.

## Recommended decision

Fix Finding A + B by adding `lst_rates` to the affected protocols' PROTOCOL_CAPABILITIES entries (and creating entries
for the 5 missing protocols). Finding C is a separate, lower-priority wiring item.

## Todos

- [x] ✅ [DATA] P2. Add `lst_rates` to KELPDAO PROTOCOL_CAPABILITIES data_types — unified-api-contracts@881faded
- [x] ✅ [DATA] P2. Add `lst_rates` to RENZO PROTOCOL_CAPABILITIES data_types — unified-api-contracts@27b7881a
- [x] ✅ [DATA] P2. Add `lst_rates` to BEEFY PROTOCOL_CAPABILITIES data_types — unified-api-contracts@394fdbf0
- [x] ✅ [DATA] P2. Add `lst_rates` to IDLE PROTOCOL_CAPABILITIES data_types — unified-api-contracts@e1639234
- [x] ✅ [DATA] P2. Add `lst_rates` to PENDLE PROTOCOL_CAPABILITIES data_types — unified-api-contracts@96070f2b
- [x] ✅ [DATA] P2. Add `lst_rates` to YEARN_V3 PROTOCOL_CAPABILITIES data_types — unified-api-contracts@e4e4e5a9
- [x] ✅ [DATA] P2. Create PROTOCOL_CAPABILITIES entries for BINANCE, COINBASE, ROCKETPOOL, SANCTUM, SOLBLAZE —
      unified-api-contracts@8feaea84
- [x] ✅ [DATA] P3. Removed `rewards` from LIDO/ETHERFI aspirational data_types; EIGENLAYER's `rewards` stays (genuinely
      collected by `collect-eigenlayer-rewards` handler) — unified-api-contracts@bc397b93

## Progress Log

- **2026-08-05 (slot-7, data_engineering craft)**: audit complete — cross-referenced all 101 live venues'
  PROTOCOL_CAPABILITIES declarations against expected_coverage.py + lst_rates_handler.py. Filed with 8 actionable todos.
- **2026-08-05 (slot-13, data_engineering craft)**: todo 8 — removed aspirational `rewards` from LIDO/ETHERFI
  PROTOCOL_CAPABILITIES data_types. EIGENLAYER's `rewards` stays (genuinely collected by `collect-eigenlayer-rewards`
  handler which writes both `rewards` + `eigenlayer_rewards` data_types). LIDO/ETHERFI had no `collect-rewards` handler
  (ETHERFI's WS connector is BLOCKED-CREDENTIALS scaffold); wiring one would require new API credentials + handler
  implementation not in scope for this P3. All 8 todos now done.
