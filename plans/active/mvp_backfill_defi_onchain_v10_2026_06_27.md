---
doc_type: plan
title: "MVP backfill — DeFi all on-chain data_types (SPOT-only, per-protocol genesis, reconcile-then-fill)"
summary:
  "Backfill all DeFi on-chain data_types (dex_pool_swaps/state, lending_indices, lst_rates, perp_funding, oracle_prices)
  for the v10 DeFi MVP scope on SPOT VMs, respecting per-protocol genesis."
nature: process
stage: [data-ingestion]
repos: [deployment-service, market-tick-data-service, instruments-service]
scope: [engineer, admin]
tags: [mvp, backfill, defi, on-chain, dex, lending, lst, perp-funding, oracle, spot-vm, v10]
related: []
created: 2026-06-27
parent_epic: defi_master
priority: P0
status: active
assigned_vm: planning
assigned_role: data_engineering
drift_direction: advance-code
last_updated: 2026-06-27
execution_scope: orchestrator-agent
estimate_class: infra
estimate_baseline_ai_days: 6
estimate_calibrated_ai_days: 4.8
locked_by: live-defi-rollout
locked_since: 2026-06-27
depends_on: [mvp_catalogue_finalization_v10_2026_06_27]
related_plans:
  - plans/active/mvp_catalogue_finalization_v10_2026_06_27.md
  - plans/active/defi_pipeline_e2e_and_coverage_validation_2026_06_20.md
  - plans/active/defi_manifest_canonicalisation_2026_06_01.md
  - plans/active/path_to_100pct_backfill_mtds_is_2026_06_17.md
asset_group: defi
---

> **🟢 OPERATOR-AUTHORIZED background execution (2026-06-27).** Part of the remaining MVP arc handed to the
> agent-orchestrator (`planning` VM). One agent, one craft (`data_engineering`), Sonnet/high.
>
> **🟡 GATED on Phase 0** — does NOT begin until `mvp_catalogue_finalization_v10_2026_06_27.md` signs off a v10-correct
> **defi** catalogue (dual-key ghosts collapsed). DeFi market-data needs the per-data_type `collect-*` MTDS ops — the
> unified `--asset-group DEFI` form SKIPS the venues (known gotcha from `path_to_100pct`), so use the per-data_type
> launchers below.
>
> **Canonical MVP SSOT (the ONLY scope authority):** `mvp_scope.py` v10 + `codex/02-data/mvp-scope-canonical.md`. This
> plan REFERENCES it. **DeFi v10 = MVP-tag-all today** (`defi_mvp_tag_all_2026_06_26`): data_types
> `dex_pool_state / dex_pool_swaps / lst_rates / lending_indices / perp_funding / oracle_prices`. **LIGHTER / EXTENDED /
> PACIFICA are CeFi, NOT DeFi** (v10 decision #4) — do NOT backfill them here. Any older plan treating them as DeFi is
> stale and SUBORDINATE (Phase-4 reconciliation).

## Codex SSOTs (READ before executing)

- `codex/02-data/mvp-scope-canonical.md` § DeFi — the 6 data_types + MVP-tag-all short-circuit.
- `codex/02-data/defi-canonical-naming-ssot.md` — DeFi data gotchas; canonical venue naming / dual-key collapse.
- `codex/02-data/honest-absence-downstream-handling.md` — `EXPECTED_PRE_GENESIS_CHAIN`, `EXPECTED_PROTOCOL_PAUSED`,
  `UPSTREAM_SUBGRAPH_ZERO` (subgraph 0-rows on an alive day → attempted_failed, NOT silent empty); per-protocol genesis.
- `codex/05-infrastructure/spot-vms-for-backfill.md` — SPOT-by-default.

## Definition of 100%

`captured` covers 100% of the v10 defi MVP could-exist universe → `attempted_failed = 0` AND `expected_unattempted = 0`
per data_type. Honest `empty_confirmed` excluded (pre-genesis-chain, protocol-paused windows). A subgraph returning 0
rows on an alive day is `attempted_failed[UPSTREAM_SUBGRAPH_ZERO]` (a gap to fix), NOT empty.

## Budget posture

DeFi on-chain is cheap (<$250 total per the budget reality) — The Graph keys (9-key pool) + Hyperliquid S3 + Pyth
archive, no Tardis tick cost. Launch all data_types in parallel on SPOT VMs. Reconcile-then-fill: respect per-protocol
genesis (do not launch pre-genesis shards — those are honest-empty).

---

## Todos (G0 gate+reconcile, then parallel per-data_type fills, then verify)

### G0 — gate + reconcile

- [ ] [SCRIPT] P0. Confirm Phase-0 defi catalogue sign-off (dual-key ghosts collapsed, mvp-tag-all). **Gate:**
      `mvp_catalogue_finalization_v10_2026_06_27.md` Progress Log shows defi G3 green. If not signed off → wait. SPOT
      N/A.
- [x] [SCRIPT] P0. Build the defi gap report per data_type (dex_pool_state, dex_pool_swaps,
      liquidations/lending_indices, lst_rates, perp_funding, oracle_prices) for the v10 DeFi MVP venues, respecting
      per-protocol genesis. Repos: `instruments-service`, `e2e-testing`. **Run:**
      `python scripts/measure_honest_coverage.py --asset-group defi` + `by_venue_data_type`; list (data_type,
      protocol/chain, date-range) cells with attempted_failed>0 / expected_unattempted>0 that are POST-genesis
      (pre-genesis cells are honest `EXPECTED_PRE_GENESIS_CHAIN`). **Gate:** gap list to Progress Log. SPOT N/A. ✅ — instruments-service@gap-report-2026-06-27

### G1 — per-data_type fills (PARALLEL; SPOT VMs only; per-protocol genesis respected)

- [ ] [SCRIPT] P0. dex_pool_state gap-fill. Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-dex-pools-backfill-vm.sh --start <genesis> --end <today>` (TheGraph 9-key pool;
      `--shard-index N` + `--force` for multi-VM fan-out). **Gate:** dex_pool_state attempted_failed=0 post-genesis;
      verify T+10min `gcloud compute instances list --filter='name~mtds-dex-pools' --zones=asia-northeast1-c`. SPOT VMs
      only.
- [ ] [SCRIPT] P0. dex_pool_swaps gap-fill. Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-dex-swaps-backfill-vm.sh --start <genesis> --end <today>`. **Gate:** dex_pool_swaps
      attempted_failed=0 post-genesis; verify T+10min. SPOT VMs only.
- [ ] [SCRIPT] P0. lending_indices gap-fill (Aave V3 / Spark / Compound V3 via The Graph). Repo: `deployment-service`.
      **SPOT VMs only.** `bash scripts/vm/launch-mtds-lending-indices-backfill-vm.sh <START> <END>` (positional window,
      full history). **Gate:** lending_indices attempted_failed=0 post-genesis; verify T+10min. SPOT VMs only.
- [ ] [SCRIPT] P0. lst_rates gap-fill (15 LST/LRT tokens, EVM + Solana). Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-lst-rates-backfill-vm.sh <START> <END>` (positional window). **Gate:** lst_rates
      attempted_failed=0 per-token-genesis; verify T+10min. SPOT VMs only.
- [ ] [SCRIPT] P0. perp_funding gap-fill (Hyperliquid public S3, no key). Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-perp-funding-backfill-vm.sh --start 2023-11-01 --end <today>` (HL mainnet genesis).
      **Gate:** perp_funding attempted_failed=0 from genesis; verify T+10min. SPOT VMs only.
- [ ] [SCRIPT] P0. oracle_prices gap-fill (Pyth). Repo: `deployment-service`. **SPOT VMs only.** Archive gap:
      `bash scripts/vm/launch-mtds-pyth-archive-backfill-vm.sh 2022-11-01 2023-09-30` (Pythnet RPC fallback for
      pre-Hermes); for Hermes-covered dates (2023-10-01+) use the forward-poll/collect path per the launcher header.
      **Gate:** oracle_prices attempted_failed=0 post-genesis; verify T+10min. SPOT VMs only.

### G2 — verify honest-complete

- [ ] [SCRIPT] P0. Final defi MVP verification: all 6 data_types attempted_failed=0 AND expected_unattempted=0
      post-genesis; subgraph-0-row-on-alive-day cells are `attempted_failed[UPSTREAM_SUBGRAPH_ZERO]` (re-run to fill,
      never silent); pre-genesis/protocol-paused are typed honest empties. Repos: `instruments-service`, `e2e-testing`.
      **Run:** `python scripts/measure_honest_coverage.py --asset-group defi`;
      `python3 e2e-testing/scripts/audit/manifest_hygiene_daily.py --asset-group defi --mode full`;
      `python scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run`. **Gate:** both failure
      buckets zero per data_type; 0 phantom; 0 dual-key ghost; verdict to Progress Log. **Full-execution criterion:**
      VM-list + coverage CLI output recorded per data_type. SPOT N/A.

---

## Progress Log

### G0.2 — Gap report (2026-06-27 21:51 UTC)

Script: `python scripts/measure_honest_coverage.py --asset-group defi --output-path /tmp/defi_coverage.json`
Manifest: `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (8,481,830 rows)
Overall honest coverage: **52.85%** (1,971,546 / 3,730,486 reachable)

#### Summary by data_type

| data_type       | coverage | captured   | attempted_failed | expected_unattempted |
|-----------------|----------|------------|-----------------|----------------------|
| dex_pool_state  | 58.62%   | 835,351    | 2,171           | 587,510              |
| dex_pool_swaps  | 29.40%   | 266,672    | 500             | 639,924              |
| lending_indices | 29.67%   | 32,378     | 898             | 75,838               |
| lst_rates       | 90.21%   | 14,979     | 891             | 734                  |
| oracle_prices   | 91.05%   | 17,620     | 873             | 859                  |
| perp_funding    | 37.19%   | 399        | 424             | 250                  |

#### Full gap list: cells with attempted_failed>0 OR expected_unattempted>0 (POST-genesis targets for G1 fills)

| data_type       | venue           | attempted_failed | expected_unattempted | captured  |
|-----------------|-----------------|-----------------|----------------------|-----------|
| dex_pool_state  | AERODROME_V3    | 87              | 3,864                | 51,849    |
| dex_pool_state  | BALANCER        | 522             | 265,682              | 53,780    |
| dex_pool_state  | CAMELOT_V3      | 87              | 4,457                | 11,664    |
| dex_pool_state  | CURVE           | 264             | 820                  | 43,135    |
| dex_pool_state  | GMX             | 176             | 10                   | 3,599     |
| dex_pool_state  | KAMINO          | 0               | 14,000               | 0         |
| dex_pool_state  | ORCA            | 0               | 16,250               | 0         |
| dex_pool_state  | PANCAKESWAP_V3  | 258             | 49,151               | 44,030    |
| dex_pool_state  | RAYDIUM         | 0               | 2,536                | 0         |
| dex_pool_state  | SUSHISWAP       | 88              | 500                  | 16,059    |
| dex_pool_state  | SUSHISWAP_V3    | 261             | 9,404                | 25,010    |
| dex_pool_state  | TRADER_JOE_V2   | 0               | 38,000               | 0         |
| dex_pool_state  | UNISWAP_V2      | 0               | 2,324                | 11,085    |
| dex_pool_state  | UNISWAP_V3      | 428             | 138,799              | 551,539   |
| dex_pool_state  | UNISWAP_V4      | 0               | 31,753               | 23,601    |
| dex_pool_state  | VELODROME_V2    | 0               | 9,960                | 0         |
| dex_pool_swaps  | AERODROME_V3    | 0               | 6,973                | 5,579     |
| dex_pool_swaps  | BALANCER        | 4               | 265,682              | 7,483     |
| dex_pool_swaps  | CAMELOT_V3      | 4               | 6,138                | 1,106     |
| dex_pool_swaps  | CURVE           | 477             | 1,108                | 7,213     |
| dex_pool_swaps  | GMX             | 0               | 125                  | 0         |
| dex_pool_swaps  | ORCA            | 0               | 16,250               | 0         |
| dex_pool_swaps  | PANCAKESWAP_V3  | 1               | 54,883               | 5,040     |
| dex_pool_swaps  | RAYDIUM         | 0               | 2,536                | 0         |
| dex_pool_swaps  | SUSHISWAP       | 2               | 500                  | 2,018     |
| dex_pool_swaps  | SUSHISWAP_V3    | 1               | 12,074               | 2,562     |
| dex_pool_swaps  | TRADER_JOE_V2   | 0               | 38,000               | 0         |
| dex_pool_swaps  | UNISWAP_V2      | 0               | 2,334                | 11,083    |
| dex_pool_swaps  | UNISWAP_V3      | 11              | 191,711              | 201,323   |
| dex_pool_swaps  | UNISWAP_V4      | 0               | 31,696               | 23,265    |
| dex_pool_swaps  | VELODROME_V2    | 0               | 9,914                | 0         |
| lending_indices | AAVE_V3         | 869             | 4,958                | 23,681    |
| lending_indices | COMPOUND_V3     | 12              | 0                    | 6,224     |
| lending_indices | FLUID           | 0               | 750                  | 0         |
| lending_indices | KAMINO          | 0               | 14,000               | 32        |
| lending_indices | MARGINFI        | 14              | 0                    | 16        |
| lending_indices | MORPHO          | 0               | 55,506               | 0         |
| lending_indices | SPARK           | 3               | 624                  | 2,395     |
| lst_rates       | ETHENA          | 249             | 78                   | 882       |
| lst_rates       | ETHERFI         | 256             | 78                   | 875       |
| lst_rates       | JITO            | 0               | 125                  | 8         |
| lst_rates       | LIDO            | 32              | 203                  | 2,011     |
| lst_rates       | MARINADE        | 354             | 250                  | 32        |
| oracle_prices   | EIGENLAYER      | 0               | 125                  | 0         |
| oracle_prices   | ETHENA          | 0               | 78                   | 659       |
| oracle_prices   | ETHERFI         | 0               | 78                   | 631       |
| oracle_prices   | JITO            | 0               | 125                  | 0         |
| oracle_prices   | LIDO            | 0               | 203                  | 631       |
| oracle_prices   | MARINADE        | 0               | 250                  | 0         |
| oracle_prices   | PYTH            | 873             | 0                    | 999       |
| perp_funding    | DRIFT           | 424             | 0                    | 0         |
| perp_funding    | EIGENLAYER      | 0               | 125                  | 0         |
| perp_funding    | GMX             | 0               | 125                  | 206       |

**Notes:**
- Venues with expected_unattempted only (0 captured) and large counts — KAMINO, ORCA, RAYDIUM, TRADER_JOE_V2, VELODROME_V2, MORPHO, FLUID — are likely Solana/newer protocols not yet backfilled; these are the primary targets for G1 fills.
- BALANCER, UNISWAP_V3, UNISWAP_V4, PANCAKESWAP_V3 have very large expected_unattempted counts — the pool universe is much larger than what's been captured.
- DRIFT (perp_funding): 424 attempted_failed, 0 captured — needs perp_funding backfill VM.
- PYTH (oracle_prices): 873 attempted_failed — needs oracle_prices archive backfill.
- Solana venues (KAMINO, ORCA, RAYDIUM, JITO, MARINADE, EIGENLAYER, DRIFT) all show expected_unattempted — targeted by respective G1 launcher scripts.
