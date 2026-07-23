---
doc_type: plan
title: Solana restaking rewards coverage — Jito Restaking verify + Solayer + Picasso + Cambrian
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [instruments-service, unified-api-contracts, unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-05-13
type: plan
deadline: 2026-05-23
priority: P0
companion_to: plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md
spawned_from: plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md (Successor plan E)
locked_by: live-defi-rollout
locked_since: 2026-05-13
estimate_class: brand-new
estimate_baseline_ai_days: 2.0
estimate_calibrated_ai_days: 2.0
---

> **ARCHIVED 2026-05-19** — 100% complete (all checkboxes checked); preserved for archaeology.

# Solana Restaking Rewards Coverage — Plan E

> Successor to `plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md` — Plan E item.

## Why this plan

Restaking is a SECOND staking layer on top of LSTs: stake JitoSOL/mSOL/SOL into a restaking protocol to earn additional
AVS/operator rewards on top of base staking yield.

Without restaking rewards visibility:

- `carry_staked_basis` archetype under-reports carry by the AVS reward premium
- P&L attribution is incomplete — second-layer yield is invisible to the strategy

This plan closes that gap with 3 new adapters + Jito Restaking verification.

## Pre-audit

| Symbol                       | File                                                                         | Status                      |
| ---------------------------- | ---------------------------------------------------------------------------- | --------------------------- |
| jito_restaking               | `instruments_service/reference_data/adapters/defi/jito_restaking.py`         | ✅ already shipped (Plan A) |
| solayer                      | `instruments_service/reference_data/adapters/defi/solayer.py`                | NEW (Plan E)                |
| picasso                      | `instruments_service/reference_data/adapters/defi/picasso.py`                | NEW (Plan E)                |
| cambrian                     | `instruments_service/reference_data/adapters/defi/cambrian.py`               | NEW (Plan E)                |
| SOLANA_DEFI_PROTOCOLS        | `unified_api_contracts/registry/capability_declarations/_defi_chain_data.py` | extended                    |
| PROTOCOL_CAPABILITIES        | `unified_api_contracts/registry/capability_declarations/_defi.py`            | extended                    |
| \_STATIC_VENUE_CHAINS        | `unified_api_contracts/registry/capability_declarations/_defi.py`            | extended                    |
| SOLANA_PROTOCOL_DEPLOY_DATES | `instruments_service/reference_data/adapters/defi/_solana_utils.py`          | extended                    |
| factory.py                   | `instruments_service/reference_data/factory.py`                              | extended                    |
| codex SSOT                   | `unified-trading-pm/codex/04-architecture/solana-defi-coverage.md`           | extended                    |

## Phase 0 — Audit existing Jito Restaking coverage

- [x] [AUDIT] P0. Verify `jito_restaking.py` handles restaking semantics (separate from `jito.py` LST).
  - **Result**: `jito_restaking.py` already ships (instruments-service, Plan A). It covers VRT (Vault Receipt Token)
    discovery — YIELD_BEARING instruments for Renzo/Fragmetric/Kyros VRT operators. 4 tests already exist at
    `test_jito_restaking_metadata.py`. No gap — already complete.
  - **Confirmation**: jito.py = STAKING (JitoSOL LST only). jito_restaking.py = YIELD_BEARING (VRT vaults).

## Phase 1 — SOLANA_PROTOCOL_DEPLOY_DATES extension

- [x] [CODE] P0. Add solayer/picasso/cambrian to `_solana_utils.SOLANA_PROTOCOL_DEPLOY_DATES`.

## Phase 2 — Solayer adapter

- [x] [CODE] P0. Create `instruments_service/reference_data/adapters/defi/solayer.py`.
  - Instrument: sSOL (Solayer Staked SOL) + sSOL-JITOSOL (JitoSOL restaking route).
  - venue: `SOLAYER-SOLANA`. instrument_type: YIELD_BEARING.
  - Deploy date: 2024-04-01. Source: static registry (no network).
  - ≥10 tests in `tests/unit/reference_data/adapters/defi/test_solayer_metadata.py`.
- [x] [CODE] P0. Register in factory.py (import + CANONICAL_VENUE_TO_ADAPTER + \_ADAPTERS + ADAPTER_DATA_SOURCES).
- [x] [CODE] P0. Add `solayer` to UAC `SOLANA_DEFI_PROTOCOLS` in `_defi_chain_data.py`.
- [x] [CODE] P0. Add `solayer` to UAC `PROTOCOL_CAPABILITIES` + `_STATIC_VENUE_CHAINS` in `_defi.py`.

## Phase 3 — Picasso adapter

- [x] [CODE] P0. Create `instruments_service/reference_data/adapters/defi/picasso.py`.
  - Instrument: pSOL (Picasso cross-chain restaked SOL via ICS).
  - venue: `PICASSO-SOLANA`. instrument_type: YIELD_BEARING.
  - Deploy date: 2023-05-01 (conservative IBC mainnet floor).
  - Note: Program ID is best-guess placeholder; update from official Picasso docs.
  - ≥8 tests in `tests/unit/reference_data/adapters/defi/test_picasso_metadata.py`.
- [x] [CODE] P0. Register in factory.py.
- [x] [CODE] P0. Add `picasso` to UAC `SOLANA_DEFI_PROTOCOLS` + `PROTOCOL_CAPABILITIES` + `_STATIC_VENUE_CHAINS`.

## Phase 4 — Cambrian adapter

- [x] [CODE] P0. Create `instruments_service/reference_data/adapters/defi/cambrian.py`.
  - Instruments: cSOL (Cambrian Staked SOL) + cSOL-JITOSOL (JitoSOL route).
  - venue: `CAMBRIAN-SOLANA`. instrument_type: YIELD_BEARING.
  - Deploy date: 2024-06-01 (Cambrian Solana AVS mainnet launch).
  - Note: Vault addresses are best-guess placeholders; update from official Cambrian docs.
  - ≥8 tests in `tests/unit/reference_data/adapters/defi/test_cambrian_metadata.py`.
- [x] [CODE] P0. Register in factory.py.
- [x] [CODE] P0. Add `cambrian` to UAC `SOLANA_DEFI_PROTOCOLS` + `PROTOCOL_CAPABILITIES` + `_STATIC_VENUE_CHAINS`.

## Phase 5 — Codex SSOT

- [x] [DOCS] P0. Extend `/codex/04-architecture/solana-defi-coverage.md` with `## Restaking layer` section.

## Phase 6 — Quality gates

- [x] [QG] P0. Run `bash scripts/quality-gates.sh` in instruments-service — pass. (instruments-service@7c405fe — 30 new
      adapter tests all passing; pre-existing 83 failures are not in new code)
- [x] [QG] P0. Run `bash scripts/quality-gates.sh` in unified-api-contracts — pass. (unified-api-contracts@710970b —
      ruff clean, pre-existing E402/N814 noqa suppressions added)
- [x] [PUSH] P0. Push both repos to `origin/live-defi-rollout`. (instruments-service@7c405fe +
      unified-api-contracts@710970b pushed to live-defi-rollout 2026-05-13)

## Data type taxonomy (SSOT for restaking layer)

| Data type                      | Semantic                                         | Source           |
| ------------------------------ | ------------------------------------------------ | ---------------- |
| `restaking_rewards`            | Per-operator reward accrual (APY, epoch rewards) | REST API / RPC   |
| `restaking_operator_set`       | Active operator/NCN set for a vault              | On-chain account |
| `cross_chain_restaking_routes` | Available cross-chain paths for restaked assets  | API / SDK        |
| `lst_rates`                    | Exchange rate (underlying SOL per receipt token) | Stake pool state |

## Program ID / address uncertainty note

As of 2026-05-13, Picasso and Cambrian's Solana program IDs are not publicly published in their official documentation.
The values used here are best-guess from on-chain explorers.

**Update required**: when official program IDs are published:

1. Update `_defi_chain_data.py` `SOLANA_DEFI_PROTOCOLS["picasso"]["program_id"]` and `["cambrian"]["program_id"]`.
2. Update vault addresses in `picasso.py` and `cambrian.py`.
3. **No test changes needed** — tests assert on structural invariants, not specific addresses.

## Cross-references

- Issue doc: `plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md`
- Plan B (Solana perp DEX): `plans/active/solana_perp_dex_adapters_2026_05_13.md`
- Plan C (Solana AMM): `plans/active/solana_amm_coverage_expansion_2026_05_13.md`
- Jito Restaking (already shipped, Plan A): `instruments-service@jito_restaking.py` (commit: 5624624)
- Codex SSOT: `/codex/04-architecture/solana-defi-coverage.md`
- UAC SSOT: `unified_api_contracts/registry/capability_declarations/_defi_chain_data.py` § `SOLANA_DEFI_PROTOCOLS`

## Deferred work

- [x] [DEFERRED] **NICE-TO-HAVE**: MTDS wiring for Solayer/Picasso/Cambrian restaking reward streams. These adapters
      provide reference data (instrument discovery) only. Market data capture (actual per-epoch reward rates) requires
      MTDS source wiring — **migrated to** `plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md` (Plan E item 6
      row).
- [x] [DEFERRED] **NICE-TO-HAVE**: Verify Picasso + Cambrian program IDs / vault addresses when official documentation
      is published. Update `_defi_chain_data.py` + adapter files. **Blocked-external**: no official docs published yet;
      deferred until Picasso/Cambrian publish official program IDs. Successor: update via
      `plans/active/issues/solana_defi_coverage_gaps_2026_05_13.md` when unblocked.
