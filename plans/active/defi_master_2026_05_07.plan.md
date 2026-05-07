---
name: defi-master
slug: defi_master_2026_05_07
date: 2026-05-07
owner: claude-code
status: active
priority: P0
phase: pending_approval
domain: defi
asset_group: defi
type: umbrella
locked_by: live-defi-rollout
locked_since: 2026-05-07
folds_in:
  - consolidated_defi_data_pipeline_2026_04_15
  - defi_e2e_pipeline_2026_04_30
  - dex_historical_replay_lighter_extended_pacifica_2026_05_07
  - market_tick_data_to_100pct_2026_05_05 # DeFi slice
  - cefi_venue_universe_expansion_2026_05_01 # DEX-perp half (Extended / Pacifica / Lighter)
related_plans:
  - master_to_live_defi_2026_05_23
  - writegate_honest_coverage_endtoend_2026_05_06
  - shard_granularity_ssot_propagation_2026_05_06
---

# DeFi Master — asset_group umbrella

## Scope

Single source of truth for **DeFi asset_group** work toward live DeFi 2026-05-23. The headline goal of the cutover.

Covers:

- **2 DeFi archetypes live**: `carry_staked_basis` (lead — recursive LST staking + perp short hedge) +
  `leveraged_funding_arb` (cross-venue funding spread). 7-day continuous run on real wallet.
- **2 DeFi perp DEXs live**: Hyperliquid + Aster. Plus historical-replay backfill for Lighter / Extended / Pacifica
  (originally scoped under CeFi venue expansion but they are DeFi by asset_group).
- **DeFi data pipeline E2E**: features-onchain → strategy → execution. 8 archetypes pass Phase 1 batch e2e (per
  `defi_e2e_pipeline`).
- **MTDS DeFi slice to 100%**: per-(asset_group=defi, chain, venue/protocol, data_type, instrument_id, day). Chain is a
  first-class shard axis.
- **Multi-chain oracle prices**: Pyth (Solana, unbanned 2026-05-06) + Chainlink (EVM Arb/Base/Polygon).
- **Custody integration**: Copper wired DeFi-side per `codex/04-architecture/copper-custody-integration.md`.

**Current data-status** (from deployment-ui 2026-05-07): 49138/295744 shards = **73.5%**, 988 dates missing. Tail chains
(Aurora / Celo / Fantom / Mantle / Metis / Moonbeam) stuck at 25% (1/4 protocols). Mid-tier EVMs (Arbitrum / Avalanche /
Base / BSC / Linea / Optimism / Polygon) at 60% (32/53). Ethereum 85%, Solana 99.9%.

## Current state (2026-05-07)

- **2 DeFi archetypes** live spec'd; backtest pipeline working per `consolidated_defi_data_pipeline` Phase 6
  verifications.
- **Hyperliquid + Aster perp DEXs**: instrument registry done, market-data live, execution-service connectors validated
  on testnet.
- **Lighter + Extended + Pacifica DEX-perps**: historical-replay scoping complete per `dex_historical_replay_*`;
  contract addresses + ABI parsing pending per chain.
- **Pyth oracle + multi-chain oracle**: Solana on-chain prices required for `carry_staked_basis` LST yields; UAC
  unbanning landed 2026-05-06; wiring not yet shipped.
- **DeFi data pipeline E2E**: strategy/execution/risk-and-exposure/features-onchain QG passes pending; 4 service repos
  need `quality-gates.sh` clean per `defi_e2e_pipeline`.

## Critical path

| Workstream                                                                      | Status                                                         | Source                                                   |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------- |
| `carry_staked_basis` archetype live (≥7 continuous days)                        | spec done; execution wiring pending                            | master plan + carry_staked_basis_structure_axis archived |
| `leveraged_funding_arb` archetype live                                          | scoped; cross-venue funding spread integration pending         | `consolidated_defi_data_pipeline`                        |
| Hyperliquid + Aster perp DEX live                                               | instruments + market-data live; execution validated on testnet | `consolidated_defi_data_pipeline`                        |
| 988 dates missing in DeFi shards (per data-status panel)                        | manifest gap; per-chain breakdown above                        | `consolidated_defi_data_pipeline` (Phase 6 reverify)     |
| Tail chains 25% coverage (Aurora / Celo / Fantom / Mantle / Metis / Moonbeam)   | per-chain protocols incomplete                                 | `consolidated_defi_data_pipeline`                        |
| Mid-tier EVMs 60% coverage (Arb / Avax / Base / BSC / Linea / Op / Polygon)     | per-chain protocols incomplete                                 | `consolidated_defi_data_pipeline`                        |
| Pyth Solana oracle wiring                                                       | unbanned 2026-05-06; integration pending                       | `consolidated_defi_data_pipeline` mtds-s3-5              |
| Multi-chain oracle (Chainlink EVM)                                              | partial                                                        | `consolidated_defi_data_pipeline` mtds-s3-6              |
| Lighter / Extended / Pacifica historical-replay backfill                        | scoped; ABI parsing per chain pending                          | `dex_historical_replay_*`                                |
| 4-service QG pass (strategy / execution / risk-and-exposure / features-onchain) | pending                                                        | `defi_e2e_pipeline`                                      |
| 8-archetype Phase 1 batch e2e                                                   | pending                                                        | `defi_e2e_pipeline`                                      |
| Copper custody integration                                                      | wired DeFi-side; sandbox integration test pending              | `consolidated_defi_data_pipeline` Copper item            |

## Consolidated todos (P0 only — full P1+ list in folded children)

### Oracle prices + chain expansion (`consolidated_defi_data_pipeline` mtds-s3)

- [ ] [AGENT] P0. mtds-s3-5-pyth-oracle: Add Pyth oracle prices for Solana via Hermes (HTTPS pull, batch) + PythNet
      (Solana RPC, live). Solana-only scope. carry_staked_basis dependency.
- [ ] [AGENT] P0. mtds-s3-6-multi-chain-oracle: Extend oracle_prices to multi-chain EVM (Chainlink on Arb/Base/Polygon).
- [ ] [HUMAN+AGENT] P0. mtds-s4-10-rescan-all-manifests: Re-scan ALL availability indexes after migrations. **Cross-plan
      coordination**: this is **Stage 4** (final sweep) of the workspace-wide manifest migration. See
      [`manifest_migration_master_2026_05_07.plan.md`](./manifest_migration_master_2026_05_07.plan.md) — MUST run AFTER
      all Stage 3 streams complete (Stage 3.A 1440-NaN flip + 3.B available_at backfill + 3.C pre-v6 cleanup +
      Predictions Polymarket migration + Sports ODDS_API re-key). Running mid-flight produces inconsistent state across
      services. NO VM pause needed — consolidator handles concurrent writes per CLAUDE.md
      `§ Manifest     concurrency principle`.
- [ ] [HUMAN+AGENT] P0. defi-e2e-validate: DeFi pipeline E2E — run full batch, verify features-onchain reads correctly.
- [ ] [HUMAN+AGENT] P0. defi-coverage-validate: DeFi full coverage — run each handler locally for 1 day, verify GCS.

### DeFi e2e pipeline gates (`defi_e2e_pipeline`)

- [ ] [AGENT] P0. strategy-service `quality-gates.sh` passes.
- [ ] [AGENT] P0. execution-service `quality-gates.sh` passes.
- [ ] [AGENT] P0. risk-and-exposure-service `quality-gates.sh` passes.
- [ ] [AGENT] P0. features-onchain-service `quality-gates.sh` passes.
- [ ] [AGENT] P0. basedpyright clean across all 4 DeFi service repos.
- [ ] [AGENT] P0. CARRY_RECURSIVE_STAKED batch e2e produces non-zero PnL row in
      `pnl-store-{pid}/by_strategy/.../day=2025-06-21`.
- [ ] [AGENT] P0. PnL row decomposes into base_apy + restaking_apy + borrow_cost + gas attribution.
- [ ] [AGENT] P0. Position snapshot reflects leveraged LST holding + WETH debt.
- [ ] [AGENT] P0. Health factor recorded ≥ configured `min_health_factor` for every snapshot.
- [ ] [AGENT] P0. Synthetic feature tick injected into `defi-onchain-features-ready` produces a fill on
      `fill-events-{venue}`.
- [ ] [AGENT] P0. PBM emits position snapshot; pnl-attribution emits per-strategy attribution row.
- [ ] [AGENT] P0. Risk-and-exposure-service log shows RISK_PASS published before execution.
- [ ] [AGENT] P0. All 8 archetypes pass Phase 1 batch e2e: CARRY_RECURSIVE_STAKED, CARRY_STAKED_BASIS, CARRY_BASIS_PERP,
      [+5 more].
- [ ] [AGENT] P0. features-onchain-service Docker image rebuild — Cloud Build emits new `:latest` tag with Phase
      changes.

### Lighter / Extended / Pacifica historical replay (`dex_historical_replay_*`)

- [ ] [AGENT] P0. Lighter zkSync mainnet matching contract address + ABI parse (`Trade` event).
- [ ] [AGENT] P0. Lighter subgraph availability check (thegraph.com/explorer); validate row schema match against
      `_fetch_lighter_rest`.
- [ ] [SCRIPT] P0. Launch `mtds-lighter-history-backfill-{ts}` singleton-locked VM; date range 2024-08-01 → today. Add
      prefix to `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET`.
- [ ] [AGENT] P0. Extended Starknet mainnet `Settlement` contract address + event signature; add Starknet RPC template
      to UAC `CHAIN_RPC_TEMPLATES`.
- [ ] [AGENT] P0. `_fetch_extended_history` in `umi_tick_provider.py`; schema-parity vs `_fetch_extended_rest`.
- [ ] [AGENT] P0. Pacifica Solana program ID + Anchor `emit!` log decoder; Helius `getSignaturesForAddress` +
      `getTransaction` parse.
- [ ] [AGENT] P0. `_fetch_pacifica_history` in `umi_tick_provider.py`; schema-parity vs `_fetch_pacifica_rest`.
- [ ] [SCRIPT] P0. Backfill VMs for each new venue + schema-parity validation against the REST adapter.

### Tail-chain / mid-tier protocol coverage (DeFi data-status — 988 dates missing)

- [ ] [AGENT] P0. Tail chains 25% coverage diagnosis: Aurora / Celo / Fantom / Mantle / Metis / Moonbeam each have 1
      protocol live; per-chain protocol expansion deferred-post-cutover unless `carry_staked_basis` /
      `leveraged_funding_arb` requires those chains.
- [ ] [AGENT] P0. Mid-tier 60% coverage: Arb / Avax / Base / BSC / Linea / Op / Polygon — 32/53 protocols. Per-protocol
      backfill needed for 21 protocols/chain. Subgraph schema-mismatch fixes for PancakeSwap V3, SushiSwap V3, Aerodrome
      V3, Camelot V3 (per `defi_e2e_pipeline`).
- [ ] [AGENT] P0. 988 dates missing — query manifest, identify per-(chain, protocol, data_type) gaps, prioritize
      `carry_staked_basis` chain set first (Ethereum + Solana mostly done; Arbitrum + Base critical).

### MTDS DeFi slice (`market_tick_data_to_100pct` — DeFi)

- [ ] [AGENT] P1. Per-chain MTDS to 100%: Ethereum (85%), Solana (99.9% — basically done), Arbitrum / Base / Polygon
      (60%). Per-protocol gap analysis from `consolidated_defi_data_pipeline` Phase 6.

### DeFi DEX-perp adapters from `cefi_venue_universe_expansion` (re-classified to DeFi)

- [ ] [AGENT] P0. **Extended** — UAC: add to `VENUES_BY_ASSET_GROUP['defi']`. Adapter: `_fetch_extended_rest` + history.
- [ ] [AGENT] P0. **Pacifica** — UAC: same. Adapter: `_fetch_pacifica_rest`. Hyperliquid clone — schema parity.
- [ ] [AGENT] P0. **Lighter** — UAC: same. Adapter: `_fetch_lighter_rest`. zkSync L2; different RPC stack.

### Custody (Copper)

- [ ] [AGENT] P1. Copper sandbox integration test — validate `CopperCustodyProvider` (in execution-service) per
      `codex/04-architecture/copper-custody-integration.md`.

### Audit findings 2026-05-07 — folded from session wrapper

**Source**: `plans/ai/session_2026_05_07_data_status_audit_findings.plan.md` row C.9. Operator inspected DEFI pool
drilldown after the 4-candidate-probe fix shipped (deployment-api@`0384eab`); AAVE_V3-ARBITRUM still surfaces "no schema
yet" with 0 on-disk parquets across all 4 layout candidates even though the manifest claims `1781/1785 captured`.

#### C.9 — AAVE_V3-ARBITRUM phantom rows reconcile

This is a textbook phantom-rows scenario per CLAUDE.md `§ Manifest phantom audit`: manifest says `captured` but the
parquet doesn't exist at any canonical path. The orchestrator's `_should_skip_shard` will trust the manifest forever
unless reconciled. Either (a) parquets really don't exist (writer bug — needs root-cause + re-fetch), or (b) parquets
exist at a 5th layout the prober doesn't know about (extend the prober + the audit's drift-axis enumeration).

- [x] [SCRIPT] P0. Ran `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi
      --dry-run` locally, scoped `--venues AAVEV3` (sufficient for triage; full DEFI scan deferred to GCE VM after the
      prober landed below to avoid 18× slowdown × 313k row × 7 prefix template explosion). Initial run reported 29782
      false-positive phantoms — the entire AAVEV3 dataset; would have destroyed all manifest state had `--apply` run.
- [x] [AGENT] P0. Triaged for AAVE_V3-ARBITRUM specifically — **case (b)** confirmed: audit reported mass
      false-positives. Diagnosed root cause via on-disk listing: the canonical manifest has ZERO `(venue=AAVEV3,
      chain=ARBITRUM)` rows (all 29782 AAVEV3 rows are on `chain=ETHEREUM`). The UI's "AAVE_V3-ARBITRUM 1781/1785"
      claim came from the deployment-api offline rollup, which conflates the expected denominator with the
      found-on-disk count for venue+chain combos that have no manifest rows (separate rollup-side bug, captured in
      codex doc + filed under infrastructure_master Data-status multi-axis follow-up).
- [x] [SCRIPT] P0. Found two NEW drift axes the prober missed; extended
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` (instruments-service@`e8393fc`).
      **Axis 6** — DeFi protocol-name underscore variant (`AAVEV3` ↔ `AAVE_V3` etc.) via new `_defi_protocol_variants`
      regex helper that probes both spellings; **Axis 7** — DeFi migrated-bundle wildcard (`ticks_migrated_*.parquet`
      at the combined-venue prefix accepted as evidence of capture for any data_type, since the bundle holds all
      data_types in one parquet). Helper unit-tested 12/12 cases PASS. Re-run on `--venues AAVEV3` shows 29782 → 0
      phantoms (100% false-positive elimination). Manifest is clean for AAVEV3.
- [ ] [VERIFY] P1. After ship: launch `defi-phantom-recon-{ts}` GCE VM in `asia-northeast1-c` (add prefix to
      `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` first) running the full DEFI dry-run with the new prober. Compare
      pre-/post-fix phantom counts across all DEFI venues (UNISWAPV3 187k rows, MORPHO 45k, EIGENLAYER, MAKER, etc.).
      Expected: large drop in false-positive count similar to the 2026-05-04 cefi 130k → 354 reduction.
- [x] [DOC] P0. Updated `codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit — re-runnable recipe"
      to enumerate 7 drift axes (was 5); added rollup-side metric inconsistency finding under § "Rollup-side metric
      inconsistency (deployment-api `_data_status_rollup_worker`) — open finding 2026-05-07"; updated history
      benchmark with the 2026-05-07 AAVEV3 29782 → 0 reduction.

## Anti-patterns + workspace-rule cross-references

- **Pyth UNBANNED for Solana** (2026-05-06): use Hermes (batch) + PythNet (live). Other chains stay on Chainlink. See
  CLAUDE.md "Removed providers" → "Pyth — UNBANNED" entry.
- **Live = batch**: same code path; matching engine for backtests. See `codex/04-architecture/batch-live-pipeline.md`.
- **`chain` is a first-class shard axis** for DeFi (per CLAUDE.md per-asset-group shard-key matrix).

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.plan.md`](./master_to_live_defi_2026_05_23.plan.md).
- Sibling asset_group umbrellas: `cefi_master_2026_05_07`, `tradfi_master_2026_05_07`, `sports_master_2026_05_07`,
  `predictions_master_2026_05_07`.
- Carry tracer pipeline handoff: `plans/ai/carry_tracer_pipeline_handoff_2026_05_06.md` (in-flight Phase 9 catalog).

## Folded plans (archived 2026-05-07)

- `consolidated_defi_data_pipeline_2026_04_15.plan.md` — DeFi pipeline umbrella (full P1 list lives in this archive).
- `defi_e2e_pipeline_2026_04_30.plan.md` — 4-service QG + 8-archetype e2e gates.
- `dex_historical_replay_lighter_extended_pacifica_2026_05_07.plan.md` — DEX-perp historical replay scoping.
- `market_tick_data_to_100pct_2026_05_05.plan.md` (DeFi slice) — full plan archived after split per asset_group.
- `cefi_venue_universe_expansion_2026_05_01.plan.md` (DEX-perp half) — Lighter / Extended / Pacifica re-classified to
  DeFi asset_group; CeFi venues (Bitfinex / Bitget / Kraken) lifted into `cefi_master`.
