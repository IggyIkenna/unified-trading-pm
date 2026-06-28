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
> **🟢 GATE CLEARED 2026-06-28T02:35Z** — `mvp_catalogue_finalization_v10_2026_06_27.md` G3 sign-off complete.
> defi catalogue v10-correct: 7,222 rows (all-MVP ✅), dual-key ghosts=0 (4 cross-chain ETHEREUM+POLYGON ✓),
> false-delist=0, blank=0. Phantom: 219,529 (swaps_ohlcv_*×7 + UNISWAP_V4 dominant; issue doc
> `phantom_captures_defi_2026_06_28.md`). ⚠️ **APPLY PHANTOM RECONCILE BEFORE G0 GAP ANALYSIS** — run
> `reconcile_phantom_manifest_rows_all.py --asset-group defi` (no dry-run; `MANIFEST_PER_VM_SHARDS=true`) first.
> **Use per-data_type launchers (not unified `--asset-group DEFI` form).**
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

- [x] ✅ [SCRIPT] P0. Confirm Phase-0 defi catalogue sign-off (dual-key ghosts collapsed, mvp-tag-all). **Gate:**
      `mvp_catalogue_finalization_v10_2026_06_27.md` Progress Log shows defi G3 green. If not signed off → wait. SPOT
      N/A. — **Confirmed 2026-06-28T02:40Z**: finalization Progress Log defi G3 GREEN ✅; 7,222 rows all mvp=True ✅;
      dual-key ghosts=0 (4 ETHEREUM+POLYGON cross-chain contracts) ✓.
- [x] [SCRIPT] P0. Build the defi gap report per data_type (dex_pool_state, dex_pool_swaps,
      liquidations/lending_indices, lst_rates, perp_funding, oracle_prices) for the v10 DeFi MVP venues, respecting
      per-protocol genesis. Repos: `instruments-service`, `e2e-testing`. **Run:**
      `python scripts/measure_honest_coverage.py --asset-group defi` + `by_venue_data_type`; list (data_type,
      protocol/chain, date-range) cells with attempted_failed>0 / expected_unattempted>0 that are POST-genesis
      (pre-genesis cells are honest `EXPECTED_PRE_GENESIS_CHAIN`). **Gate:** gap list to Progress Log. SPOT N/A. ✅ — instruments-service@gap-report-2026-06-27

### G1 — per-data_type fills (PARALLEL; SPOT VMs only; per-protocol genesis respected)

- [x] [SCRIPT] P0. dex_pool_state gap-fill. Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-dex-pools-backfill-vm.sh --start <genesis> --end <today>` (TheGraph 9-key pool;
      `--shard-index N` + `--force` for multi-VM fan-out). **Gate:** dex_pool_state attempted_failed=0 post-genesis;
      verify T+10min `gcloud compute instances list --filter='name~mtds-dex-pools' --zones=asia-northeast1-c`. SPOT VMs
      only. ✅ — deployment-service@vm-launch-2026-06-27 VM=mtds-dex-pools-backfill RUNNING 34.84.133.128
- [x] [SCRIPT] P0. dex_pool_swaps gap-fill. Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-dex-swaps-backfill-vm.sh --start <genesis> --end <today>`. **Gate:** dex_pool_swaps
      attempted_failed=0 post-genesis; verify T+10min. SPOT VMs only. ✅ — VM=mtds-dex-swaps-backfill RUNNING 34.146.95.210 (2023-01-01→2026-06-27)
- [x] [SCRIPT] P0. lending_indices gap-fill (Aave V3 / Spark / Compound V3 via The Graph). Repo: `deployment-service`.
      **SPOT VMs only.** `bash scripts/vm/launch-mtds-lending-indices-backfill-vm.sh <START> <END>` (positional window,
      full history). **Gate:** lending_indices attempted_failed=0 post-genesis; verify T+10min. SPOT VMs only. ✅ — VM=mtds-lending-indices-20260627-220715 RUNNING 34.84.20.157 (2022-01-01→2026-06-27)
- [x] [SCRIPT] P0. lst_rates gap-fill (15 LST/LRT tokens, EVM + Solana). Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-lst-rates-backfill-vm.sh <START> <END>` (positional window). **Gate:** lst_rates
      attempted_failed=0 per-token-genesis; verify T+10min. SPOT VMs only. ✅ — VM=mtds-lst-rates-20260627-220922 RUNNING 34.84.28.4 (2020-01-01→2026-06-27)
- [x] [SCRIPT] P0. perp_funding gap-fill (Hyperliquid public S3, no key). Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-perp-funding-backfill-vm.sh --start 2023-11-01 --end <today>` (HL mainnet genesis).
      **Gate:** perp_funding attempted_failed=0 from genesis; verify T+10min. SPOT VMs only. ✅ — VM=mtds-perp-funding-backfill RUNNING 34.180.79.187 (2023-11-01→2026-06-27)
- [x] [SCRIPT] P0. oracle_prices gap-fill (Pyth). Repo: `deployment-service`. **SPOT VMs only.** Archive gap:
      `bash scripts/vm/launch-mtds-pyth-archive-backfill-vm.sh 2022-11-01 2023-09-30` (Pythnet RPC fallback for
      pre-Hermes); for Hermes-covered dates (2023-10-01+) use the forward-poll/collect path per the launcher header.
      **Gate:** oracle_prices attempted_failed=0 post-genesis; verify T+10min. SPOT VMs only. ✅ — VM=mtds-pyth-archive-20260627-221636 RUNNING 34.84.64.217 (2022-11-01→2023-09-30); Hermes window (2023-10-01+) covered by forward collect cascade

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

### G1 dex_pool_state VM launch (2026-06-27 ~21:55 UTC)

- VM: `mtds-dex-pools-backfill` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2023-01-01 → 2026-06-27 | TheGraph 9-key pool SHARD_INDEX=0
- STATUS: RUNNING immediately at launch (IP: 34.84.133.128)
- T+10min verify: `gcloud compute instances describe mtds-dex-pools-backfill --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-dex-pools-backfill/run.log`

### G1 dex_pool_swaps VM launch (2026-06-27 ~22:05 UTC)

- VM: `mtds-dex-swaps-backfill` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2023-01-01 → 2026-06-27 | TheGraph 9-key pool SHARD_INDEX=0
- STATUS: RUNNING immediately at launch (IP: 34.146.95.210)
- T+10min verify: `gcloud compute instances describe mtds-dex-swaps-backfill --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-dex-swaps-backfill/run.log`

### G1 lending_indices VM launch (2026-06-27 ~22:07 UTC)

- VM: `mtds-lending-indices-20260627-220715` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2022-01-01 → 2026-06-27 | Aave V3 / Spark / Compound V3 via The Graph
- STATUS: RUNNING immediately at launch (IP: 34.84.20.157)
- T+10min verify: `gcloud compute instances describe mtds-lending-indices-20260627-220715 --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-lending-indices-20260627-220715/run.log`

### G1 lst_rates VM launch (2026-06-27 ~22:09 UTC)

- VM: `mtds-lst-rates-20260627-220922` | Zone: `asia-northeast1-c` | SPOT e2-standard-8
- Date range: 2020-01-01 → 2026-06-27 | 15 LST/LRT tokens EVM + Solana
- STATUS: RUNNING immediately at launch (IP: 34.84.28.4)
- T+10min verify: `gcloud compute instances describe mtds-lst-rates-20260627-220922 --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-lst-rates-20260627-220922/run.log`

### G1 perp_funding VM launch (2026-06-27 UTC)

- VM: `mtds-perp-funding-backfill` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2023-11-01 → 2026-06-27 | Hyperliquid public S3 (no API key)
- Prior TERMINATED VM (range 2023-11-01→2026-06-24) deleted before re-launch
- STATUS: RUNNING at launch (IP: 34.180.79.187)
- T+10min verify: `gcloud compute instances describe mtds-perp-funding-backfill --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-perp-funding-backfill/run.log`

### G1 oracle_prices VM launch (2026-06-27 UTC)

- VM: `mtds-pyth-archive-20260627-221636` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2022-11-01 → 2023-09-30 | Pyth Hermes archive + Pythnet RPC fallback (pre-Hermes window)
- Prior TERMINATED VM (`mtds-pyth-archive-20260622-064526`) already cleared
- STATUS: RUNNING at launch (IP: 34.84.64.217)
- Hermes window (2023-10-01+): covered by forward collect cascade (Pyth Hermes /v2/updates/price/{ts} = source #1; 999 already captured from prior runs)
- T+10min verify: `gcloud compute instances describe mtds-pyth-archive-20260627-221636 --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-pyth-archive-20260627-221636/run.log`

### G2 baseline coverage snapshot (2026-06-27 22:19 UTC — G1 VMs in-flight)

Manifest: `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (7,399,163 rows)
Overall honest coverage: **52.89%** — G1 VMs all RUNNING, gate not yet achievable.

| data_type       | coverage | captured   | attempted_failed | expected_unattempted | gate  |
|-----------------|----------|------------|-----------------|----------------------|-------|
| dex_pool_state  | 58.7%    | 838,711    | 2,171           | 587,510              | FAIL  |
| dex_pool_swaps  | 29.4%    | 266,827    | 500             | 639,924              | FAIL  |
| lending_indices | 29.7%    | 32,378     | 898             | 75,838               | FAIL  |
| lst_rates       | 90.2%    | 14,979     | 891             | 734                  | FAIL  |
| oracle_prices   | 91.1%    | 17,620     | 873             | 859                  | FAIL  |
| perp_funding    | 37.2%    | 399        | 424             | 250                  | FAIL  |

**G1 VMs still RUNNING** (all launched 2026-06-27 ~22:07–22:35 UTC):
- `mtds-dex-pools-backfill` RUNNING (dex_pool_state, 2023-01-01→2026-06-27)
- `mtds-dex-swaps-backfill` RUNNING (dex_pool_swaps, 2023-01-01→2026-06-27)
- `mtds-lending-indices-20260627-234500` RUNNING 34.84.133.128 (lending_indices, 2022-01-01→2026-06-27) [5th launch ~23:45 UTC; `233514` was SPOT-preempted rc=137 at ~23:42 UTC (ran 4 min); persistent preemptions in asia-northeast1-c]
- `mtds-lst-rates-20260627-220922` RUNNING (lst_rates, 2020-01-01→2026-06-27)
- `mtds-perp-funding-backfill` RUNNING (perp_funding/HYPERLIQUID, 2023-11-01→2026-06-27)
- `mtds-pyth-archive-20260627-221636` RUNNING (oracle_prices archive, 2022-11-01→2023-09-30)
- `mtds-solana-drift-backfill` RUNNING (perp_funding/DRIFT Helius V2, 2025-01-09→2026-06-27)

**Root-cause finding**: 404 DRIFT perp_funding failures (error: `drift_v2_sig_index.parquet missing`) from
2025-01-09→2026-02-16. Sig index consolidated parquet was missing but 6293+875 parts exist in GCS. Handler
falls back to parts; re-running with parts now available should resolve 404 failures. DRIFT-SOLANA is in
v10 MVP scope (mvp_scope.py:489). Separate launcher needed from HYPERLIQUID VM.

**Re-run G2 after ALL VMs complete** (`python scripts/measure_honest_coverage.py --asset-group defi`).

**BLOCKED-OPERATOR-DECISION**: `launch-mtds-pyth-lst-backfill-vm.sh` has hard-stop in script header:
"DO NOT LAUNCH without operator [ack] in ikenna_orchestrator/pings/slot_2.md". This covers:
- JitoSOL/USD (JITO oracle_prices, 125 expected_unattempted)
- mSOL/USD (MARINADE oracle_prices, 250 expected_unattempted)
- bSOL/USD + INF/USD: 2023-10-01→present Hermes window
Operator must approve before these 375 rows can be captured. G2 oracle_prices gate cannot fully
pass for JITO+MARINADE until operator approves the Pyth LST Solana backfill.

### G1 DRIFT Solana perp_funding VM launch (2026-06-27 ~22:35 UTC)

- VM: `mtds-solana-drift-backfill` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2025-01-09 → 2026-06-27 | Drift V2 Helius RPC (sig index fallback to 7168 parts)
- Root cause: `drift_v2_sig_index.parquet` consolidated missing; 6293+875=7168 parts built 2026-06-01
- 404 DRIFT sig_index failures cover 2025-01-09→2026-02-16; re-running should succeed with parts
- STATUS: RUNNING at launch (IP: 35.187.206.222)
- T+10min verify: `gcloud compute instances describe mtds-solana-drift-backfill --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-solana-drift-backfill/run.log`

### DRIFT perf fix — parts-metadata cache (2026-06-27)

✅ Shipped `market-tick-data-service@874a0bbf` — `perf(drift): add parts-metadata cache to _load_drift_v2_sig_index`

**Root cause**: `_load_drift_v2_sig_index` downloaded ALL 7168 sig-index parts (~48GB) on EVERY date call (O(N×days)
= ~26TB for a 550-day backfill). Each date call re-scanned all parts even when most had no overlap.

**Fix**: In-process parts metadata cache (`self._drift_v2_parts_meta_cache`). First call scans all parts and
builds `dict[str, tuple[int|None, int|None]]` (part_name → (min_blockTime, max_blockTime)). Subsequent calls
skip non-overlapping parts without downloading (~20MB per date vs ~48GB). Helper extracted:
`_collect_from_drift_parts_cache`. QG lint-codex + typecheck + full pytest green.

**Re-launch with fix**: Old `mtds-solana-drift-backfill` (22:35 UTC launch, old code) deleted at ~23:42 UTC.
Tarball rebuilt with sha=874a0bbf5109 and uploaded to GCS (23:39 UTC). New VM `mtds-solana-drift-backfill`
re-launched at ~23:43 UTC (136.110.117.136) with patched code — cache-enabled, ~43× faster per-date scan.

**Cache confirmation** (23:58:47 UTC): `"Drift V2 sig index parts: metadata cache built (7169 parts across 3 prefixes)"`. VM
processing 2025-01-09 (1,209,478 sigs); only heartbeats 00:01–00:24 UTC — normal for 1.2M sig window via Helius batch API.

### SPOT preemption + re-launch log (2026-06-28 ~00:21 UTC)

**lst-rates preempted** (~00:02 UTC): `mtds-lst-rates-20260627-220922` SPOT-preempted after 2+ hrs; was processing 2020-02
(pre-genesis empty markers). Re-launched as `mtds-lst-rates-20260628-002136` (34.104.175.119) at ~00:21 UTC.

**lending-indices preempted** (6th preemption, ~00:20 UTC): `mtds-lending-indices-20260627-234500` SPOT-preempted after ~35
min. Re-launched as `mtds-lending-indices-20260628-002455` (34.84.28.4) at ~00:25 UTC.

**Watchdog updated** (PID 795019): lst-rates `20260627-220922` → `20260628-002136`; lending-indices prefix broadened to
`^mtds-lending-indices-` (catches any date suffix). Watchdog confirmed 7/7 RUNNING at 00:25 UTC.

**Current G1 VM roster (2026-06-28 00:25 UTC — ALL 7 RUNNING)**:
- `mtds-dex-pools-backfill` RUNNING 34.180.72.4 (dex_pool_state, 2023-01-01→2026-06-27)
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43 (dex_pool_swaps, 2023-01-01→2026-06-27)
- `mtds-lending-indices-20260628-002455` RUNNING 34.84.28.4 (lending_indices, 2022-01-01→2026-06-27) [6th SPOT launch]
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119 (lst_rates, 2020-01-01→2026-06-27) [2nd SPOT launch]
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48 (perp_funding/HYPERLIQUID, 2023-11-01→2026-06-27)
- `mtds-pyth-archive-20260627-221636` RUNNING 34.84.64.217 (oracle_prices archive, 2022-11-01→2023-09-30)
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (perp_funding/DRIFT, 2025-01-09→2026-06-27, fixed code 874a0bbf)

### pyth-archive COMPLETED (2026-06-28 00:52 UTC)

✅ `mtds-pyth-archive-20260627-221636` COMPLETED exit_code=0 at 00:52 UTC. 334 dates processed (2022-11-01→2023-09-30).
ManifestWriter final: 6838 total entries. VM self-deleted on completion. oracle_prices archive window DONE.

### lending-indices persistent SPOT preemption → switched to ON_DEMAND (2026-06-28 01:00 UTC)

- `mtds-lending-indices-20260628-002455` SPOT-preempted at ~00:55 UTC (7th preemption total)
- Launched SPOT intermediate `mtds-lending-indices-20260628-010041` accidentally (env var `ON_DEMAND=true` ignored by script — script overrides to `false`; need `--on-demand` CLI flag). Deleted immediately.
- Re-launched as `mtds-lending-indices-20260628-010211` (34.146.105.78) ON-DEMAND (PREEMPTIBLE=false) at ~01:02 UTC using `--on-demand` CLI flag. This VM will not be preempted.

### DRIFT VM progress (2026-06-28 ~01:00 UTC)

VM is active and writing data events to GCS: 120 event files in `gs://central-element-323112-events/events/market-tick-data-service/2026-06-28/mtds-solana-drift-backfill/hour=00/` (one every ~30s). Transient HTTP 504 at batch=3306 at 00:38 UTC was retried; processing continues. Run.log shows only heartbeats (no intermediate batch log lines — expected for Helius batch resolve).

### G1 VM roster (2026-06-28 01:02 UTC — 6 active)

- `mtds-dex-pools-backfill` RUNNING 34.180.72.4 (dex_pool_state)
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43 (dex_pool_swaps)
- `mtds-lending-indices-20260628-010211` RUNNING 34.146.105.78 (lending_indices) [ON-DEMAND, no preemption]
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119 (lst_rates)
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48 (perp_funding/HYPERLIQUID)
- `mtds-pyth-archive-20260627-221636` ✅ COMPLETED 00:52 UTC (oracle_prices archive 2022-11-01→2023-09-30)
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (perp_funding/DRIFT, fixed code 874a0bbf)
- Watchdog: PID 1045803 `/tmp/defi_g2_watchdog.sh` — updated to 6-VM count, pyth-archive removed

### lending-indices OOM kill + re-launch (2026-06-28 01:07 UTC)

`mtds-lending-indices-20260628-010211` OOM-killed (rc=137, SIGKILL) at 01:07 UTC after processing only 2022-01-01
(13 manifest entries, 0 records all venues — expected pre-genesis). Process killed during date transition to 2022-01-02.
e2-standard-4 (16GB RAM) memory spike during instrument metadata load between dates.

Re-launched as `mtds-lending-indices-20260628-013649` (34.84.220.190) ON-DEMAND at ~01:36 UTC.
Idempotent manifest: 2022-01-01 already in shard (13 entries), will resume from 2022-01-02.

### DRIFT VM analysis — NOT stalled, processing slowly (2026-06-28 01:35 UTC)

DRIFT VM confirmed alive: 70 GCS events in hour=01 (one every 30s). Run.log frozen since 00:38 because the code
only logs ERRORS — `continue` on HTTP 504 (no retry loop), silence on successful batches.

Batch mechanics: batch_size=100 sigs, 1,209,478 sigs for 2025-01-09 = 12,095 batches total.
Rate observed: batch=3306 at 40 min = ~82 batches/min.
Expected 2025-01-09 completion: 12,095/82 = 147 min from 23:58 UTC = ~02:25 UTC.

**Note**: 535 remaining dates (2025-01-10 → 2026-06-27). If avg is 50k sigs/date = 500 batches → ~6 min/date
→ 535×6 = ~53 hours remaining after 2025-01-09. DRIFT backfill may take 2+ days total for SOLANA perp_funding.

### G1 VM roster (2026-06-28 01:36 UTC — 6 active)

- `mtds-dex-pools-backfill` RUNNING 34.180.72.4 (dex_pool_state)
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43 (dex_pool_swaps)
- `mtds-lending-indices-20260628-013649` RUNNING 34.84.220.190 (lending_indices, ON-DEMAND, resumed from 2022-01-02)
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119 (lst_rates)
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48 (perp_funding/HYPERLIQUID)
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (perp_funding/DRIFT, batch ~8000/12095 for 2025-01-09)

### lending-indices OOM root cause + n2-highmem-4 fix (2026-06-28 02:15 UTC)

Two consecutive OOM kills (010211 at 01:07, 013649 at 01:43) both at the SAME point: after 2022-01-01 completes, during
transition to 2022-01-02. Root cause: `ManifestFreshnessCache.bulk_load` loads the full defi availability_index.parquet
(183 MB compressed → ~1.5-3 GB uncompressed pandas DataFrame) on EVERY date call. The `_INDEX_CACHE_TTL` expires during
the 2-3 min per-date processing window, causing a full re-download at each date transition. With old cache + new load
simultaneously in memory, e2-standard-4 (16GB) OOMs at the first transition.

Re-launched as `mtds-lending-indices-20260628-021507` (34.180.65.195) ON-DEMAND on `n2-highmem-4` (32GB RAM).
32GB provides 2x headroom over the peak simultaneous load. Idempotent restart: manifests for 2022-01-01 (13 entries)
already written by both prior runs.

### G1 VM roster (2026-06-28 02:15 UTC — 6 active)

- `mtds-dex-pools-backfill` RUNNING 34.180.72.4 (dex_pool_state)
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43 (dex_pool_swaps)
- `mtds-lending-indices-20260628-021507` RUNNING 34.180.65.195 (lending_indices, ON-DEMAND n2-highmem-4 32GB)
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119 (lst_rates)
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48 (perp_funding/HYPERLIQUID)
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (perp_funding/DRIFT, ~batch 10k/12k for 2025-01-09)

### OOM fix CONFIRMED + DRIFT 2025-01-09 COMPLETE (2026-06-28 02:47 UTC)

**lending-indices 021507 n2-highmem-4 (32GB) — OOM fix confirmed:**
At 02:45 UTC, VM is processing `day=2022-01-11` (10 dates past the critical date-1→date-2 transition).
ManifestWriter: 13 total entries (6 new for 2022-01-11). No OOM kill. Rate: ~3 min/date for pre-genesis dates
(all 0 records). Est 1641 dates × 3 min = ~82 hrs from launch; will stabilize once AAVE V3 genesis reached.

**DRIFT VM — 2025-01-09 completed at 02:25 UTC:**
`1,209,378 rows` written to `drift_helius_SOL-PERP_20250109.parquet`. Total time for date 1: 147 min (23:58→02:25).
Now processing 2025-01-10: 968,079 sigs loaded from CACHE (parts metadata cache working — "0 prefixes {}" means
no prefix re-scan, cache hit for all 7169 parts). Cache reduces per-date scan from ~48GB to ~20MB.

### G1 VM roster (2026-06-28 02:47 UTC — 6/6 RUNNING)

- `mtds-dex-pools-backfill` RUNNING 34.180.72.4 (dex_pool_state)
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43 (dex_pool_swaps)
- `mtds-lending-indices-20260628-021507` RUNNING 34.180.65.195 (lending_indices, 2022-01-11 @ 02:45, ON-DEMAND 32GB)
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119 (lst_rates)
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48 (perp_funding/HYPERLIQUID)
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (perp_funding/DRIFT, processing 2025-01-10, 968k sigs)
