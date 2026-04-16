---
name: consolidated-defi-data-pipeline
overview: |
  Consolidated remaining DeFi data pipeline work from 6 source plans.
  Covers: MTDS normalization remaining (Solana lending, oracles, verification), DeFi E2E validation,
  data coverage, instrument pipeline, multichain expansion, MEV protection.
type: mixed
epic: epic-code-completion
status: active

completion_gates:
  code: C5
  deployment: D3
  business: B4

repo_gates:
  - repo: market-tick-data-service
    code: C1
  - repo: features-onchain-service
    code: C1
  - repo: instruments-service
    code: C1
  - repo: unified-api-contracts
    code: C1
  - repo: unified-trading-library
    code: C1
  - repo: deployment-api
    code: C1
  - repo: deployment-service
    code: C1
  - repo: deployment-ui
    code: C0
  - repo: execution-service
    code: C0
  - repo: market-data-processing-service
    code: C1

depends_on: []

source_plans:
  - mtds_defi_data_normalization_2026_04_14
  - defi_data_pipeline_e2e_2026_04_08
  - defi_full_data_coverage_2026_04_09
  - defi_instrument_pipeline_and_rewards_2026_04_01
  - multichain_defi_expansion_2026_03_28
  - mev_protection_and_execution_enhancements_2026_04_01

todos:
  # ══════════════════════════════════════════════════════════════
  # GROUP A — MTDS Per-Instrument Sharding & Skip Logic
  # ══════════════════════════════════════════════════════════════
  - id: mtds-s1b-mdps-underlying
    content: "Update MDPS to read/write per-underlying for options/futures"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s1b-mdps-skip-no-upstream
    content: "MDPS skip-if-no-upstream: don't fail if MTDS data doesn't exist (plan [x] — verify)"
    status: todo
    source: mtds_defi_data_normalization

  # ══════════════════════════════════════════════════════════════
  # GROUP B — Solana & Multi-Chain DeFi Data Collectors
  # ══════════════════════════════════════════════════════════════
  - id: mtds-s3-3-marginfi
    content: "Add Marginfi lending collector (Solana)"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s3-4-solend
    content: "Add Solend lending collector (Solana)"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s3-5-pyth-oracle
    content: "Add Pyth oracle prices for Solana assets"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s3-6-multi-chain-oracle
    content: "Extend oracle_prices to multi-chain EVM (Chainlink on Arb/Base/Polygon)"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s3-7-solana-lst-onchain
    content: "Add mSOL/jitoSOL on-chain exchange rate tracking to lst_rates_handler"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s3-8-features-solana-lending
    content: "Add Solana lending feature calculations (after Kamino Lend)"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s5-7-kamino-lend
    content: "[HUMAN] Run Kamino Lend data collection on VM"
    status: todo
    source: mtds_defi_data_normalization

  # ══════════════════════════════════════════════════════════════
  # GROUP C — Data Status & Deployment UI
  # ══════════════════════════════════════════════════════════════
  - id: mtds-s3-9-data-status-underlying
    content: "Update deployment-api tree builder to show per-underlying breakdowns"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s3-10-deployment-ui-types
    content: "Update deployment-ui to render new normalized data types"
    status: todo
    source: mtds_defi_data_normalization

  # ══════════════════════════════════════════════════════════════
  # GROUP D — Sports Data Leakage & Provider Fixes (cross-cutting)
  # ══════════════════════════════════════════════════════════════
  - id: mtds-s3c-4-sfi-progressive
    content: "Implement SFI progressive stats pipeline"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s3c-5-weather-backfill
    content: "Backfill weather data (after venue master table)"
    status: todo
    source: mtds_defi_data_normalization

  # ══════════════════════════════════════════════════════════════
  # GROUP E — Migrations & Manifest Rescan
  # ══════════════════════════════════════════════════════════════
  - id: mtds-s4-10-rescan-all-manifests
    content: "[HUMAN+AGENT] Re-scan ALL availability indexes after all migrations"
    status: todo
    source: mtds_defi_data_normalization

  # ══════════════════════════════════════════════════════════════
  # GROUP F — Verification & Smoke Tests
  # ══════════════════════════════════════════════════════════════
  - id: mtds-s6-1-block-resolver-verify
    content: "Verify block resolver: fetch Camelot V3 pools for date BEFORE 2023-06-14"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s6-2-bulk-options-verify
    content: "Verify bulk OPTIONS: download one day of Deribit options_chain"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s6-3-shard-failure-verify
    content: "Verify shard failure: simulate one instrument failing"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s6-4-per-instrument-verify
    content: "Verify per-instrument files: download perps for one venue"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s6-5-schema-validation-verify
    content: "Verify schema validation: send malformed DataFrame"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s6-6-data-status-verify
    content: "[HUMAN] Verify data status page: check CeFi/DeFi/TradFi percentages"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s6-7-solana-buckets-verify
    content: "Verify Solana data writes to normalized buckets"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s6-8-tick-windows-verify
    content: "Verify tick_windows: CME tbbo expected only in May 2023 + July 2024"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s6-9-jito-verify
    content: "Verify Jito collector returns exchange rate + APY data"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s6-10-instrument-count-audit
    content: "Audit instrument counts per venue/date vs instruments-service"
    status: todo
    source: mtds_defi_data_normalization

  # ══════════════════════════════════════════════════════════════
  # GROUP G — Documentation
  # ══════════════════════════════════════════════════════════════
  - id: mtds-s7-1-claude-md
    content: "Update CLAUDE.md in affected repos for data type name changes (plan [x] — verify)"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s7-2-codex-docs
    content: "Update codex architecture docs for DeFi data type normalization"
    status: todo
    source: mtds_defi_data_normalization
  - id: mtds-s7-3-vm-scripts
    content: "Update VM scripts / deployment docs with new CLI flags"
    status: todo
    source: mtds_defi_data_normalization

  # ══════════════════════════════════════════════════════════════
  # GROUP H — E2E Validation (from smaller plans)
  # ══════════════════════════════════════════════════════════════
  - id: defi-e2e-validate
    content:
      "[HUMAN+AGENT] DeFi pipeline E2E validation — run full batch, verify features-onchain reads MTDS, PnL uses
      multi-chain gas"
    status: todo
    source: defi_data_pipeline_e2e
  - id: defi-coverage-validate
    content: "[HUMAN+AGENT] DeFi full coverage — run each handler locally for 1 day, verify GCS output"
    status: todo
    source: defi_full_data_coverage
  - id: defi-ip-1a-audit
    content: "Audit all instruments needed across DeFi strategies vs what exists upstream"
    status: todo
    source: defi_instrument_pipeline_and_rewards
  - id: defi-ip-1c-mtds-coverage
    content: "Ensure MTDS adapters cover all required instruments + venues"
    status: todo
    source: defi_instrument_pipeline_and_rewards
  - id: multichain-qg-sweep
    content: "QG sweep on all 8 repos + bridge E2E + WETH wrap/unwrap testnet"
    status: todo
    source: multichain_defi_expansion
  - id: mev-3a-e2e
    content: "Add MEV + execution scenarios to e2e-testing"
    status: todo
    source: mev_protection_and_execution_enhancements

isProject: false
---

# Consolidated DeFi Data Pipeline

Remaining work from 6 source plans. Largest block is MTDS normalization verification (10 smoke tests). Solana lending
collectors (Marginfi, Solend, Kamino) are the main new code work.
