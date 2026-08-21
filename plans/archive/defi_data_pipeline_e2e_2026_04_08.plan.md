---
doc_type: plan
title: defi-data-pipeline-e2e
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [e2e-testing, execution-service, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: []
related: []
created: '2026-04-14'
remaining_todos_consolidated_into: consolidated_defi_data_pipeline_2026_04_15
overview: End-to-end DeFi data pipeline — backfill all MTDS operations, wire downstream consumers, build data manifest
type: mixed
epic: epic-code-completion
completion_gates: {code: C5, deployment: D3, business: B4}
repo_gates:
- {repo: market-tick-data-service, code: C0, deployment: none, business: none}
- {repo: features-onchain-service, code: C0, deployment: none, business: none}
- {repo: pnl-attribution-service, code: C0, deployment: none, business: none}
- {repo: e2e-testing, code: C0, deployment: none, business: none}
- {repo: unified-trading-system-ui, code: C0, deployment: none, business: none}
depends_on: []
todos:
- {id: phase1-gas-backfill, content: '- [x] [AGENT] P0. Multi-chain gas fee backfill — created launch_gas_fees_vm.sh, launched for 7 default chains from 2024-01-01

    ', status: done}
- {id: phase1-evm-defi-backfill, content: '- [x] [AGENT] P0. EVM DeFi handler env var fallback added (THEGRAPH_API_KEY). Snapshot-based — no backfill needed, just run daily going forward

    ', status: done}
- {id: phase1-solana-drift-backfill, content: '- [x] [AGENT] P1. Solana Drift S3 backfill — created launch_solana_drift_vm.sh (ready to launch for SOL-PERP + BTC-PERP)

    ', status: done}
- {id: phase1-eigenlayer-fix-bootstrap, content: '- [x] [AGENT] P0. Fix EigenLayer handler to work with direct invocation + env var API key fallback

    ', status: done}
- {id: phase2-manifest-operation, content: '- [x] [AGENT] P0. Built data_manifest_handler.py, registered as data-manifest operation in ServiceBootstrap

    ', status: done}
- {id: phase2-pnl-multichain-gas, content: '- [x] [AGENT] P1. Fixed pnl-attribution-service: parameterized bucket via get_bucket_name, chain_id from fill, per-chain native token price lookup

    ', status: done}
- {id: phase3-features-eigen-parquet, content: '- [x] [AGENT] P0. Wired features-onchain eigen_rewards_calculator to read MTDS parquet with DefiLlama fallback

    ', status: done}
- {id: phase3-ui-manifest, content: '- [x] [AGENT] P1. Added DeFi sub-bucket scanning to deployment-service manifest_reader (_EXTRA_BUCKETS for gas-fees and normalized DeFi data types)

    ', status: done}
- {id: phase1-handler-cli-alignment, content: '- [x] [AGENT] P0. All MTDS handlers use BatchPayload date (no internal date-range iteration). All 3 VM scripts invoke service CLI instead of MagicMock. Base handler declares self.args. EigenLayer TVL cache added.

    ', status: done}
- {id: phase4-validate, content: "- [x] [HUMAN+AGENT] P0. End-to-end validation — run full pipeline batch, verify features-onchain reads MTDS data, PnL attribution uses multi-chain gas\n  *(archived 2026-04-22 — operator E2E; execute on next scheduled defi batch rehearsal.)*\n", status: todo}
isProject: false
---

# DeFi Data Pipeline End-to-End

## Problem

MTDS had 5 operations (download, collect-gas-fees, collect-solana-defi, collect-evm-defi, collect-eigenlayer-rewards)
but data coverage was sparse. **NOTE**: evm_defi and solana_defi have been replaced by 10 normalized data types
(dex_pools, dex_swaps, lending_indices, liquidations, perp_funding, lst_rates, oracle_prices, gas_fees, rewards,
risk_params). See `mtds_defi_data_normalization_2026_04_14.md`.

**Current state:**

| Operation                  | Coverage                                                                            | Gap                                                         |
| -------------------------- | ----------------------------------------------------------------------------------- | ----------------------------------------------------------- |
| collect-eigenlayer-rewards | **594 days, 248K claims** (just backfilled)                                         | Done — but features-onchain reads DefiLlama proxy, not this |
| collect-gas-fees           | 7 days, Ethereum only                                                               | Missing 11 chains, missing history                          |
| collect-evm-defi           | **REMOVED** — replaced by per-data-type handlers (lending_indices, dex_pools, etc.) | See normalization plan                                      |
| collect-solana-defi        | **REMOVED** — split into dex_pools, perp_funding, lst_rates handlers                | See normalization plan                                      |
| download (CeFi)            | Good coverage                                                                       | N/A                                                         |

**Downstream gaps:**

- features-onchain-service: reads EigenLayer from DefiLlama API, not MTDS parquet
- pnl-attribution-service: reads gas fees only for chain_id=1 (Ethereum)
- strategy-service: uses $0.10 gas fallback (execution-service fills, not strategy)
- No data manifest or gap detection exists

## Execution DAG

```
Phase 1: BACKFILL DATA (PARALLEL)
  ├── gas-fees VM (all 12 chains)
  ├── evm-defi handler fix + VM
  ├── solana-drift S3 VM
  └── eigenlayer ✅ DONE
         │
    ── QG gate: MTDS passes ──
         │
Phase 2: MANIFEST + PNL (PARALLEL)
  ├── data-manifest MTDS operation
  └── pnl-attribution multi-chain gas
         │
    ── QG gate: MTDS + pnl-attribution pass ──
         │
Phase 3: DOWNSTREAM WIRING (PARALLEL)
  ├── features-onchain reads MTDS eigen parquet
  └── UI data-etl reads real manifest
         │
    ── QG gate: all repos pass ──
         │
Phase 4: E2E VALIDATION
  └── Full pipeline batch run + verify
```

## Pre-Audit Manifest

### Phase 1: MTDS Backfill

#### Gas Fee Handler (market-tick-data-service)

| File                              | Line   | Current                                                         | Action                                            |
| --------------------------------- | ------ | --------------------------------------------------------------- | ------------------------------------------------- |
| `cli/handlers/gas_fee_handler.py` | 32     | `DEFAULT_GAS_FEE_CHAINS = [1, 10, 56, 137, 8453, 42161, 43114]` | Keep — 7 default EVM chains                       |
| `cli/handlers/gas_fee_handler.py` | 67-87  | `preflight()` fetches Alchemy key from SM                       | Add env var fallback (same pattern as eigenlayer) |
| `cli/handlers/gas_fee_handler.py` | 90-160 | `process()` collects per-chain                                  | Verify batch date range works end-to-end          |
| GCS bucket                        | -      | `gs://gas-fees-{project}/gas_fees/chain_id={id}/date={date}/`   | Write for all 12 chains                           |
| e2e-testing                       | -      | No gas fee VM script                                            | **CREATE** `launch_gas_fees_vm.sh`                |

#### EVM DeFi Handler (market-tick-data-service)

| File                               | Line    | Current                                     | Action                                       |
| ---------------------------------- | ------- | ------------------------------------------- | -------------------------------------------- |
| `cli/handlers/evm_defi_handler.py` | 133-154 | Single-day collection, no date-range loop   | **ADD** date-range iteration like eigenlayer |
| `cli/handlers/evm_defi_handler.py` | 100-115 | The Graph API key from SM                   | Add env var fallback for VM                  |
| `cli/handlers/evm_defi_handler.py` | 127-129 | Supports AAVE, Compound, Morpho on 5 chains | Keep — protocols are correct                 |
| e2e-testing                        | -       | No EVM DeFi VM script                       | **CREATE** `launch_evm_defi_vm.sh`           |

#### Solana DeFi Handler (market-tick-data-service)

| File                                  | Line    | Current                                              | Action                                         |
| ------------------------------------- | ------- | ---------------------------------------------------- | ---------------------------------------------- |
| `cli/handlers/solana_defi_handler.py` | 338-339 | Drift S3 backfill hardcodes 2024-01-01 to 2024-12-31 | **FIX** to use CLI `--start-date`/`--end-date` |
| `cli/handlers/solana_defi_handler.py` | 71      | `--solana-drift-backfill` flag                       | Keep                                           |
| e2e-testing                           | -       | No Solana VM script                                  | **CREATE** `launch_solana_drift_vm.sh`         |

### Phase 2: Manifest + PnL

#### Data Manifest (market-tick-data-service — NEW)

| File                                       | Action                                                                |
| ------------------------------------------ | --------------------------------------------------------------------- |
| `cli/handlers/data_manifest_handler.py`    | **CREATE** — new handler, scans GCS partitions, reports coverage/gaps |
| `cli/main.py`                              | Register `"data-manifest": DataManifestHandler` operation             |
| `tests/unit/test_data_manifest_handler.py` | **CREATE** unit tests                                                 |

#### PnL Attribution Multi-Chain Gas

| File                                                  | Line   | Current                                      | Action                                                |
| ----------------------------------------------------- | ------ | -------------------------------------------- | ----------------------------------------------------- |
| `pnl_attribution_service/engine/pnl_input_builder.py` | 36     | `bucket = "gas-fees-central-element-323112"` | **FIX** use `get_bucket_name("gas-fees")` or config   |
| `pnl_attribution_service/engine/pnl_input_builder.py` | 41     | `prefix="gas_fees/chain_id=1/"`              | **FIX** accept chain_id param, read from fill's chain |
| `pnl_attribution_service/engine/pnl_input_builder.py` | 99-107 | `eth_price=Decimal("3200")` hardcoded        | **FIX** use DefiLlama or config for current ETH price |

### Phase 3: Downstream Wiring

#### Features-Onchain EigenLayer Calculator

| File                                                                   | Line    | Current                                                                  | Action                                                    |
| ---------------------------------------------------------------------- | ------- | ------------------------------------------------------------------------ | --------------------------------------------------------- |
| `features_onchain_service/app/calculators/eigen_rewards_calculator.py` | 79-138  | DefiLlama Yields API                                                     | **REFACTOR** to read from MTDS parquet via StorageClient  |
| `features_onchain_service/app/calculators/eigen_rewards_calculator.py` | 156-162 | Computes `eigen_reward_apy`, `eigen_claimable_amount` from API pool data | **ENHANCE** compute from actual on-chain claim data + TVL |

#### Deployment UI Data Coverage

| File                                   | Line  | Current                                                       | Action                                                  |
| -------------------------------------- | ----- | ------------------------------------------------------------- | ------------------------------------------------------- |
| `app/(ops)/internal/data-etl/page.tsx` | 46-50 | `MOCK_ETL_PIPELINES`, `MOCK_VENUE_COVERAGE`, `MOCK_DATA_GAPS` | **WIRE** to real API endpoint reading manifest from GCS |

## Success Criteria

### Phase 1 (Backfill)

- Gas fees: ≥100 days for all 7 default chains in GCS
- EVM DeFi: AAVE V3 + Morpho from May 2024 to present on Ethereum
- Solana Drift: SOL-PERP from Jan 2024 to present
- EigenLayer: ✅ 594 days, 248K claims

### Phase 2 (Manifest + PnL)

- `--operation data-manifest` outputs JSON with coverage per operation/venue
- pnl-attribution reads gas for chain matching the fill's chain_id

### Phase 3 (Downstream)

- features-onchain eigen calculator reads MTDS parquet (verified by comparing output)
- UI data-etl page shows real coverage data

### Phase 4 (E2E)

- Full batch run: MTDS → features-onchain → strategy → verify features include real EigenLayer reward data + multi-chain
  gas
