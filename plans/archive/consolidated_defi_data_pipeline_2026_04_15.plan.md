---
doc_type: plan
title: consolidated-defi-data-pipeline
summary: 'Consolidated remaining DeFi data pipeline work from 6 source plans.

  Covers: MTDS normalization remaining (Solana lending, oracles, verification), DeFi E2E validation,

  data coverage, instrument pipeline, multichain expansion, MEV protection.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-api, deployment-service, deployment-ui, e2e-testing, instruments-service]
scope: [engineer, admin]
tags: []
related: []
created: "2026-04-16"
type: mixed
epic: epic-code-completion
reconciliation_status: yaml_to_markdown_converted
reconciliation_date: 2026-04-25
reconciliation_evidence: _reconciliation_evidence_map_2026_04_25.md
completion_gates: { code: C5, deployment: D3, business: B4 }
repo_gates:
  - { repo: market-tick-data-service, code: C1 }
  - { repo: features-onchain-service, code: C1 }
  - { repo: instruments-service, code: C1 }
  - { repo: unified-api-contracts, code: C1 }
  - { repo: unified-trading-library, code: C1 }
  - { repo: deployment-api, code: C1 }
  - { repo: deployment-service, code: C1 }
  - { repo: deployment-ui, code: C0 }
  - { repo: execution-service, code: C0 }
  - { repo: market-data-processing-service, code: C1 }
depends_on: []
source_plans:
  [
    mtds_defi_data_normalization_2026_04_14,
    defi_data_pipeline_e2e_2026_04_08,
    defi_full_data_coverage_2026_04_09,
    defi_instrument_pipeline_and_rewards_2026_04_01,
    multichain_defi_expansion_2026_03_28,
    mev_protection_and_execution_enhancements_2026_04_01,
  ]
isProject: false
---

> **Reconciliation note (2026-04-25):** YAML `todos:` block converted to canonical Cursor markdown checkboxes per
> `PLAN_FORMAT.md`. 5 todos flipped to `[x]` with cited commit evidence; 28 remain open. DeFi data-type cleanup + 8 new
> handlers (UAC `13db4a9`/`56feaff`, MTDS `a5a9b71`/`2095d1b`/`8f6a5d5`, instruments-service Phase 2.5 `9ea51af`)
> shipped. See `_reconciliation_evidence_map_2026_04_25.md` for evidence anchors (consolidated_defi_data_pipeline block
> ~line 193).

# Consolidated DeFi Data Pipeline

Remaining work from 6 source plans. Largest block is MTDS normalization verification (10 smoke tests). Solana lending
collectors (Marginfi, Solend) shipped via MTDS `8f6a5d5`; Kamino still pending. DeFi data-type cleanup (drop OddsJam /
PredictIt / Betdaq / Smarkets, add 8 new DeFi types) shipped per UAC `13db4a9` + `c8191bb` + `56feaff` and MTDS
`2095d1b`.

## Todos

### Group A — MTDS Per-Instrument Sharding & Skip Logic

- [ ] [AGENT] P1. mtds-s1b-mdps-underlying: Update MDPS to read/write per-underlying for options/futures.
- [ ] [AGENT] P1. mtds-s1b-mdps-skip-no-upstream: MDPS skip-if-no-upstream — don't fail if MTDS data doesn't exist (plan
      [x] — verify).

### Group B — Solana & Multi-Chain DeFi Data Collectors

- [x] [AGENT] P0. mtds-s3-3-marginfi: Add Marginfi lending collector (Solana). Evidence: MTDS `8f6a5d5` (Marginfi
      protocol-TVL + Solend chart-replay backfill in collect-solana-defi).
- [x] [AGENT] P0. mtds-s3-4-solend: Add Solend lending collector (Solana). Evidence: MTDS `8f6a5d5` (same commit covers
      Solend chart-replay backfill).
- [ ] [AGENT] P0. mtds-s3-5-pyth-oracle: Add Pyth oracle prices for Solana assets via Hermes (HTTPS pull, batch) +
      PythNet (Solana RPC, live). Scope: Solana-only price feeds for SOL / jitoSOL / mSOL / bSOL / SPL token reads
      needed by `carry_staked_basis` LST yields.
      <!-- UNBLOCKED 2026-05-06: Pyth UNBANNED for Solana-only scope per master_to_live_defi_2026_05_23.md Q&A 9 + CLAUDE.md "Removed providers". Chainlink covers EVM only; no viable Switchboard wiring; LST yields need on-chain Solana prices. -->
- [ ] [AGENT] P0. mtds-s3-6-multi-chain-oracle: Extend oracle_prices to multi-chain EVM (Chainlink on Arb/Base/Polygon).
      NOT for Solana — Solana uses Pyth per mtds-s3-5.
- [ ] [AGENT] P1. mtds-s3-7-solana-lst-onchain: Add mSOL/jitoSOL on-chain exchange rate tracking to lst_rates_handler.
- [ ] [AGENT] P1. mtds-s3-8-features-solana-lending: Add Solana lending feature calculations (after Kamino Lend).
- [ ] [HUMAN] P1. mtds-s5-7-kamino-lend: Run Kamino Lend data collection on VM.

### Group C — Data Status & Deployment UI

- [ ] [AGENT] P1. mtds-s3-9-data-status-underlying: Update deployment-api tree builder to show per-underlying
      breakdowns.
- [ ] [AGENT] P1. mtds-s3-10-deployment-ui-types: Update deployment-ui to render new normalized data types.

### Group D — Sports Data Leakage & Provider Fixes (cross-cutting)

- [x] [AGENT] P0. mtds-s3c-4-sfi-progressive: Implement SFI progressive stats pipeline. Evidence: deployment-service
      `885131e` (launch-sfi-backfill-vm.sh — multi-year SFI LEAGUES + PROGRESSIVE_STATS backfill); features-sports
      pipeline shipped through `c7a363d` (per-fixture denormalisation join).
- [ ] [AGENT] P1. mtds-s3c-5-weather-backfill: Backfill weather data (after venue master table).

### Group E — Migrations & Manifest Rescan

- [ ] [HUMAN+AGENT] P0. mtds-s4-10-rescan-all-manifests: Re-scan ALL availability indexes after all migrations.

### Group F — Verification & Smoke Tests

- [ ] [AGENT] P1. mtds-s6-1-block-resolver-verify: Verify block resolver — fetch Camelot V3 pools for date BEFORE
      2023-06-14.
- [ ] [AGENT] P1. mtds-s6-2-bulk-options-verify: Verify bulk OPTIONS — download one day of Deribit options_chain.
- [ ] [AGENT] P1. mtds-s6-3-shard-failure-verify: Verify shard failure — simulate one instrument failing.
- [ ] [AGENT] P1. mtds-s6-4-per-instrument-verify: Verify per-instrument files — download perps for one venue.
- [ ] [AGENT] P1. mtds-s6-5-schema-validation-verify: Verify schema validation — send malformed DataFrame.
- [ ] [HUMAN] P1. mtds-s6-6-data-status-verify: Verify data status page — check CeFi/DeFi/TradFi percentages.
- [ ] [AGENT] P1. mtds-s6-7-solana-buckets-verify: Verify Solana data writes to normalized buckets.
- [ ] [AGENT] P1. mtds-s6-8-tick-windows-verify: Verify tick_windows — CME tbbo expected only in May 2023 + July 2024.
- [ ] [AGENT] P1. mtds-s6-9-jito-verify: Verify Jito collector returns exchange rate + APY data.
- [ ] [AGENT] P1. mtds-s6-10-instrument-count-audit: Audit instrument counts per venue/date vs instruments-service.

### Group G — Documentation

- [x] [AGENT] P1. mtds-s7-1-claude-md: Update CLAUDE.md in affected repos for data type name changes. Evidence: project
      CLAUDE.md "Removed providers" + "DeFi pipeline flow" sections current; UAC `13db4a9` + `56feaff` deletions
      reflected.
- [ ] [AGENT] P1. mtds-s7-2-codex-docs: Update codex architecture docs for DeFi data type normalization.
- [ ] [AGENT] P1. mtds-s7-3-vm-scripts: Update VM scripts / deployment docs with new CLI flags.

### Group H — E2E Validation (from smaller plans)

- [ ] [HUMAN+AGENT] P0. defi-e2e-validate: DeFi pipeline E2E validation — run full batch, verify features-onchain reads
      MTDS, PnL uses multi-chain gas.
- [ ] [HUMAN+AGENT] P0. defi-coverage-validate: DeFi full coverage — run each handler locally for 1 day, verify GCS
      output.
- [x] [AGENT] P0. defi-ip-1a-audit: Audit all instruments needed across DeFi strategies vs what exists upstream.
      Evidence: instruments-service Phase 2.5 instruments-first refactor `9ea51af` + UAC `13db4a9` (8 DeFi data types
      added) cover the audit + extension; data_catalogue_cleanup_2026_04_24 carries follow-up.
- [x] [AGENT] P0. defi-ip-1c-mtds-coverage: Ensure MTDS adapters cover all required instruments + venues. Evidence: MTDS
      `a5a9b71` (8 DeFi data-type handlers for defi_data_types_completeness) + `9ea51af` (Phase 2 consumer wiring) +
      `8f6a5d5` (Marginfi + Solend).
- [ ] [AGENT] P1. multichain-qg-sweep: QG sweep on all 8 repos + bridge E2E + WETH wrap/unwrap testnet.
- [ ] [AGENT] P1. mev-3a-e2e: Add MEV + execution scenarios to e2e-testing.

## Absorbed from sibling plans (2026-05-06)

Items folded in from `defi_phase3_infrastructure_2026_03_30` (since archived). Most Phase 3 / Phase 5 todos in that plan
(run instruments-service / MTDS / MDPS / features-onchain for March 2026; generate per-strategy P&L plots; compare
strategy returns vs Ethena benchmark; P&L attribution breakdown) are already covered by `defi_e2e_pipeline_2026_04_30`
Fork 1+2 closure work — not duplicated here. The single genuinely-open infra item that hasn't shipped:

- [ ] [AGENT] P1. **Copper sandbox integration test** — validate `CopperCustodyProvider` (in
      `execution_service/custody/copper.py`, shipped per source plan's Phase 4B) against Copper's sandbox API
      end-to-end: HMAC-SHA256 auth → `POST /platform/orders` → `POST /platform/orders/{id}/sign` → poll for completion.
      Ref: `/codex/04-architecture/copper-custody-integration.md`. Required before live wallet flips per master-plan
      Group F item 19 (Copper for DeFi-side custody).

Items folded in from `defi_strategies_phase2_2026_03_29` (since archived): the March plan's strategy-archetype
vocabulary (lending / basis / recursive) has been superseded by codex `09-strategy/strategy-summary.md` canonical names
(`YIELD_ROTATION_LENDING`, `CARRY_BASIS_PERP`, `CARRY_RECURSIVE_STAKED`, `CARRY_STAKED_BASIS`, `YIELD_STAKING_SIMPLE`).
The 4 Phase-2F open todos (Clean GCS state / 7-day run / generate plots / compare returns) are absorbed by
`defi_e2e_pipeline_2026_04_30` Fork 2 batch closure verification — no new work folded.
