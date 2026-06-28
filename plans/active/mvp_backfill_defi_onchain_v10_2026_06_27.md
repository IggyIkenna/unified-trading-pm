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
> **🟢 GATE CLEARED 2026-06-28T02:35Z** — `mvp_catalogue_finalization_v10_2026_06_27.md` G3 sign-off complete. defi
> catalogue v10-correct: 7,222 rows (all-MVP ✅), dual-key ghosts=0 (4 cross-chain ETHEREUM+POLYGON ✓), false-delist=0,
> blank=0. Phantom: 219,529 (issue doc `phantom_captures_defi_2026_06_28.md`).
>
> **🟢 G1 IN-FLIGHT 2026-06-28** — 6 SPOT VMs RUNNING: dex-pools-backfill ✅, dex-swaps-backfill ✅,
> lending-indices-20260628-021507 ✅, lst-rates-20260628-002136 ✅, perp-funding-backfill ✅, solana-drift-backfill ✅.
> Pyth-archive VM self-completed (oracle_prices: verify in G2). T+3.5h check 05:37Z: ALL 6 VMs RUNNING. Per-date
> `process_final=True` writes at 05:28-05:29Z were INTERMEDIATE shard checkpoints (per-date completion, not VM
> completion). Progress: dex-pools@2023-09-23 (~21%), dex-swaps@2023-01-27 (~2%), lst-rates@2020-07-03 (<1%),
> lending-indices@2022-03-17 (~5%), perp-funding@2023-12-21 (~5%), solana-drift@2025-01-11 (~0.4%, ~2-3h/day →
> PERFORMANCE STALL).
>
> **🔴 SOLANA-DRIFT PERFORMANCE STALL (2026-06-28T05:37Z)**: `mtds-solana-drift-backfill` resolving Helius signatures
> day-by-day via parts fallback (consolidated `drift_v2_sig_index.parquet` NotFound). Each date = ~2-3h (1.2M sigs/day
> via HTTP). At current rate: 527-day range → 44+ days. OPERATOR DECISION REQUIRED: (A) Build consolidated sig index
> parquet, (B) accept `empty_confirmed` for DRIFT perp_funding historical range, (C) stop VM + re-architect. See todos
> below.
>
> **🟡 DEFI PHANTOM RECONCILE IN-FLIGHT 2026-06-28T04:11Z** — dry-run running (~35min ETA, 1.8M GCS prefixes). Apply
> mode will follow to flip captured→attempted_failed for 219,529 phantoms. Running VMs will pick up newly-visible gaps.
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
      (pre-genesis cells are honest `EXPECTED_PRE_GENESIS_CHAIN`). **Gate:** gap list to Progress Log. SPOT N/A. ✅ —
      instruments-service@gap-report-2026-06-27

### G1 — per-data_type fills (PARALLEL; SPOT VMs only; per-protocol genesis respected)

- [x] [SCRIPT] P0. dex_pool_state gap-fill. Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-dex-pools-backfill-vm.sh --start <genesis> --end <today>` (TheGraph 9-key pool;
      `--shard-index N` + `--force` for multi-VM fan-out). **Gate:** dex_pool_state attempted_failed=0 post-genesis;
      verify T+10min `gcloud compute instances list --filter='name~mtds-dex-pools' --zones=asia-northeast1-c`. SPOT VMs
      only. ✅ — deployment-service@vm-launch-2026-06-27 VM=mtds-dex-pools-backfill RUNNING 34.84.133.128
- [x] [SCRIPT] P0. dex_pool_swaps gap-fill. Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-dex-swaps-backfill-vm.sh --start <genesis> --end <today>`. **Gate:** dex_pool_swaps
      attempted_failed=0 post-genesis; verify T+10min. SPOT VMs only. ✅ — VM=mtds-dex-swaps-backfill RUNNING
      34.146.95.210 (2023-01-01→2026-06-27)
- [x] [SCRIPT] P0. lending_indices gap-fill (Aave V3 / Spark / Compound V3 via The Graph). Repo: `deployment-service`.
      **SPOT VMs only.** `bash scripts/vm/launch-mtds-lending-indices-backfill-vm.sh <START> <END>` (positional window,
      full history). **Gate:** lending_indices attempted_failed=0 post-genesis; verify T+10min. SPOT VMs only. ✅ —
      VM=mtds-lending-indices-20260627-220715 RUNNING 34.84.20.157 (2022-01-01→2026-06-27)
- [x] [SCRIPT] P0. lst_rates gap-fill (15 LST/LRT tokens, EVM + Solana). Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-lst-rates-backfill-vm.sh <START> <END>` (positional window). **Gate:** lst_rates
      attempted_failed=0 per-token-genesis; verify T+10min. SPOT VMs only. ✅ — VM=mtds-lst-rates-20260627-220922
      RUNNING 34.84.28.4 (2020-01-01→2026-06-27)
- [x] [SCRIPT] P0. perp_funding gap-fill (Hyperliquid public S3, no key). Repo: `deployment-service`. **SPOT VMs only.**
      `bash scripts/vm/launch-mtds-perp-funding-backfill-vm.sh --start 2023-11-01 --end <today>` (HL mainnet genesis).
      **Gate:** perp_funding attempted_failed=0 from genesis; verify T+10min. SPOT VMs only. ✅ —
      VM=mtds-perp-funding-backfill RUNNING 34.180.79.187 (2023-11-01→2026-06-27)
- [x] [SCRIPT] P0. oracle_prices gap-fill (Pyth). Repo: `deployment-service`. **SPOT VMs only.** Archive gap:
      `bash scripts/vm/launch-mtds-pyth-archive-backfill-vm.sh 2022-11-01 2023-09-30` (Pythnet RPC fallback for
      pre-Hermes); for Hermes-covered dates (2023-10-01+) use the forward-poll/collect path per the launcher header.
      **Gate:** oracle_prices attempted_failed=0 post-genesis; verify T+10min. SPOT VMs only. ✅ —
      VM=mtds-pyth-archive-20260627-221636 RUNNING 34.84.64.217 (2022-11-01→2023-09-30); Hermes window (2023-10-01+)
      covered by forward collect cascade

### G1.5 — solana-drift stall intervention (OPERATOR DECISION REQUIRED)

- [ ] [OPERATOR] P0. Solana-drift backfill performance stall — decide intervention path: Consolidated sig index
      `drift_v2_sig_index.parquet` missing → VM uses 7169-part fallback → ~2-3h/day. At 527-day range this takes 44+
      days. Options: (A) Build consolidated sig index: merge 7169 parts into single parquet, upload to
      `gs://market-data-tick-defi-prd-central-element-323112/_index/drift_v2_sig_index.parquet`. VM auto-detects and
      skips parts fallback. Estimated build: ~30min of local merge + upload. (B) Accept
      `empty_confirmed[EXPECTED_PRE_VENUE_LAUNCH]` for all DRIFT perp_funding dates — mark DRIFT/SOLANA as out of MVP
      scope. Stop VM, set 424 DRIFT `attempted_failed` rows to `empty_confirmed`. (C) Stop VM + re-architect: change to
      signature-streaming approach (Helius streaming API instead of batch resolve). New VM after code fix.
      **Recommended: Option A** — building consolidated index is straightforward and unblocks the stall without
      sacrificing DRIFT data. 2025-01-11 still processing; partial data for 2025-01-09 and 2025-01-10 already captured
      (2,177,357 rows combined). Repo: `market-tick-data-service`, `instruments-service`.

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

Script: `python scripts/measure_honest_coverage.py --asset-group defi --output-path /tmp/defi_coverage.json` Manifest:
`gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (8,481,830 rows) Overall
honest coverage: **52.85%** (1,971,546 / 3,730,486 reachable)

#### Summary by data_type

| data_type       | coverage | captured | attempted_failed | expected_unattempted |
| --------------- | -------- | -------- | ---------------- | -------------------- |
| dex_pool_state  | 58.62%   | 835,351  | 2,171            | 587,510              |
| dex_pool_swaps  | 29.40%   | 266,672  | 500              | 639,924              |
| lending_indices | 29.67%   | 32,378   | 898              | 75,838               |
| lst_rates       | 90.21%   | 14,979   | 891              | 734                  |
| oracle_prices   | 91.05%   | 17,620   | 873              | 859                  |
| perp_funding    | 37.19%   | 399      | 424              | 250                  |

#### Full gap list: cells with attempted_failed>0 OR expected_unattempted>0 (POST-genesis targets for G1 fills)

| data_type       | venue          | attempted_failed | expected_unattempted | captured |
| --------------- | -------------- | ---------------- | -------------------- | -------- |
| dex_pool_state  | AERODROME_V3   | 87               | 3,864                | 51,849   |
| dex_pool_state  | BALANCER       | 522              | 265,682              | 53,780   |
| dex_pool_state  | CAMELOT_V3     | 87               | 4,457                | 11,664   |
| dex_pool_state  | CURVE          | 264              | 820                  | 43,135   |
| dex_pool_state  | GMX            | 176              | 10                   | 3,599    |
| dex_pool_state  | KAMINO         | 0                | 14,000               | 0        |
| dex_pool_state  | ORCA           | 0                | 16,250               | 0        |
| dex_pool_state  | PANCAKESWAP_V3 | 258              | 49,151               | 44,030   |
| dex_pool_state  | RAYDIUM        | 0                | 2,536                | 0        |
| dex_pool_state  | SUSHISWAP      | 88               | 500                  | 16,059   |
| dex_pool_state  | SUSHISWAP_V3   | 261              | 9,404                | 25,010   |
| dex_pool_state  | TRADER_JOE_V2  | 0                | 38,000               | 0        |
| dex_pool_state  | UNISWAP_V2     | 0                | 2,324                | 11,085   |
| dex_pool_state  | UNISWAP_V3     | 428              | 138,799              | 551,539  |
| dex_pool_state  | UNISWAP_V4     | 0                | 31,753               | 23,601   |
| dex_pool_state  | VELODROME_V2   | 0                | 9,960                | 0        |
| dex_pool_swaps  | AERODROME_V3   | 0                | 6,973                | 5,579    |
| dex_pool_swaps  | BALANCER       | 4                | 265,682              | 7,483    |
| dex_pool_swaps  | CAMELOT_V3     | 4                | 6,138                | 1,106    |
| dex_pool_swaps  | CURVE          | 477              | 1,108                | 7,213    |
| dex_pool_swaps  | GMX            | 0                | 125                  | 0        |
| dex_pool_swaps  | ORCA           | 0                | 16,250               | 0        |
| dex_pool_swaps  | PANCAKESWAP_V3 | 1                | 54,883               | 5,040    |
| dex_pool_swaps  | RAYDIUM        | 0                | 2,536                | 0        |
| dex_pool_swaps  | SUSHISWAP      | 2                | 500                  | 2,018    |
| dex_pool_swaps  | SUSHISWAP_V3   | 1                | 12,074               | 2,562    |
| dex_pool_swaps  | TRADER_JOE_V2  | 0                | 38,000               | 0        |
| dex_pool_swaps  | UNISWAP_V2     | 0                | 2,334                | 11,083   |
| dex_pool_swaps  | UNISWAP_V3     | 11               | 191,711              | 201,323  |
| dex_pool_swaps  | UNISWAP_V4     | 0                | 31,696               | 23,265   |
| dex_pool_swaps  | VELODROME_V2   | 0                | 9,914                | 0        |
| lending_indices | AAVE_V3        | 869              | 4,958                | 23,681   |
| lending_indices | COMPOUND_V3    | 12               | 0                    | 6,224    |
| lending_indices | FLUID          | 0                | 750                  | 0        |
| lending_indices | KAMINO         | 0                | 14,000               | 32       |
| lending_indices | MARGINFI       | 14               | 0                    | 16       |
| lending_indices | MORPHO         | 0                | 55,506               | 0        |
| lending_indices | SPARK          | 3                | 624                  | 2,395    |
| lst_rates       | ETHENA         | 249              | 78                   | 882      |
| lst_rates       | ETHERFI        | 256              | 78                   | 875      |
| lst_rates       | JITO           | 0                | 125                  | 8        |
| lst_rates       | LIDO           | 32               | 203                  | 2,011    |
| lst_rates       | MARINADE       | 354              | 250                  | 32       |
| oracle_prices   | EIGENLAYER     | 0                | 125                  | 0        |
| oracle_prices   | ETHENA         | 0                | 78                   | 659      |
| oracle_prices   | ETHERFI        | 0                | 78                   | 631      |
| oracle_prices   | JITO           | 0                | 125                  | 0        |
| oracle_prices   | LIDO           | 0                | 203                  | 631      |
| oracle_prices   | MARINADE       | 0                | 250                  | 0        |
| oracle_prices   | PYTH           | 873              | 0                    | 999      |
| perp_funding    | DRIFT          | 424              | 0                    | 0        |
| perp_funding    | EIGENLAYER     | 0                | 125                  | 0        |
| perp_funding    | GMX            | 0                | 125                  | 206      |

**Notes:**

- Venues with expected_unattempted only (0 captured) and large counts — KAMINO, ORCA, RAYDIUM, TRADER_JOE_V2,
  VELODROME_V2, MORPHO, FLUID — are likely Solana/newer protocols not yet backfilled; these are the primary targets for
  G1 fills.
- BALANCER, UNISWAP_V3, UNISWAP_V4, PANCAKESWAP_V3 have very large expected_unattempted counts — the pool universe is
  much larger than what's been captured.
- DRIFT (perp_funding): 424 attempted_failed, 0 captured — needs perp_funding backfill VM.
- PYTH (oracle_prices): 873 attempted_failed — needs oracle_prices archive backfill.
- Solana venues (KAMINO, ORCA, RAYDIUM, JITO, MARINADE, EIGENLAYER, DRIFT) all show expected_unattempted — targeted by
  respective G1 launcher scripts.

### G1 dex_pool_state VM launch (2026-06-27 ~21:55 UTC)

- VM: `mtds-dex-pools-backfill` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2023-01-01 → 2026-06-27 | TheGraph 9-key pool SHARD_INDEX=0
- STATUS: RUNNING immediately at launch (IP: 34.84.133.128)
- T+10min verify:
  `gcloud compute instances describe mtds-dex-pools-backfill --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-dex-pools-backfill/run.log`

### G1 dex_pool_swaps VM launch (2026-06-27 ~22:05 UTC)

- VM: `mtds-dex-swaps-backfill` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2023-01-01 → 2026-06-27 | TheGraph 9-key pool SHARD_INDEX=0
- STATUS: RUNNING immediately at launch (IP: 34.146.95.210)
- T+10min verify:
  `gcloud compute instances describe mtds-dex-swaps-backfill --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-dex-swaps-backfill/run.log`

### G1 lending_indices VM launch (2026-06-27 ~22:07 UTC)

- VM: `mtds-lending-indices-20260627-220715` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2022-01-01 → 2026-06-27 | Aave V3 / Spark / Compound V3 via The Graph
- STATUS: RUNNING immediately at launch (IP: 34.84.20.157)
- T+10min verify:
  `gcloud compute instances describe mtds-lending-indices-20260627-220715 --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-lending-indices-20260627-220715/run.log`

### G1 lst_rates VM launch (2026-06-27 ~22:09 UTC)

- VM: `mtds-lst-rates-20260627-220922` | Zone: `asia-northeast1-c` | SPOT e2-standard-8
- Date range: 2020-01-01 → 2026-06-27 | 15 LST/LRT tokens EVM + Solana
- STATUS: RUNNING immediately at launch (IP: 34.84.28.4)
- T+10min verify:
  `gcloud compute instances describe mtds-lst-rates-20260627-220922 --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-lst-rates-20260627-220922/run.log`

### G1 perp_funding VM launch (2026-06-27 UTC)

- VM: `mtds-perp-funding-backfill` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2023-11-01 → 2026-06-27 | Hyperliquid public S3 (no API key)
- Prior TERMINATED VM (range 2023-11-01→2026-06-24) deleted before re-launch
- STATUS: RUNNING at launch (IP: 34.180.79.187)
- T+10min verify:
  `gcloud compute instances describe mtds-perp-funding-backfill --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-perp-funding-backfill/run.log`

### G1 oracle_prices VM launch (2026-06-27 UTC)

- VM: `mtds-pyth-archive-20260627-221636` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2022-11-01 → 2023-09-30 | Pyth Hermes archive + Pythnet RPC fallback (pre-Hermes window)
- Prior TERMINATED VM (`mtds-pyth-archive-20260622-064526`) already cleared
- STATUS: RUNNING at launch (IP: 34.84.64.217)
- Hermes window (2023-10-01+): covered by forward collect cascade (Pyth Hermes /v2/updates/price/{ts} = source #1; 999
  already captured from prior runs)
- T+10min verify:
  `gcloud compute instances describe mtds-pyth-archive-20260627-221636 --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-pyth-archive-20260627-221636/run.log`

### G2 baseline coverage snapshot (2026-06-27 22:19 UTC — G1 VMs in-flight)

Manifest: `gs://market-data-tick-defi-prd-central-element-323112/_index/availability_index.parquet` (7,399,163 rows)
Overall honest coverage: **52.89%** — G1 VMs all RUNNING, gate not yet achievable.

| data_type       | coverage | captured | attempted_failed | expected_unattempted | gate |
| --------------- | -------- | -------- | ---------------- | -------------------- | ---- |
| dex_pool_state  | 58.7%    | 838,711  | 2,171            | 587,510              | FAIL |
| dex_pool_swaps  | 29.4%    | 266,827  | 500              | 639,924              | FAIL |
| lending_indices | 29.7%    | 32,378   | 898              | 75,838               | FAIL |
| lst_rates       | 90.2%    | 14,979   | 891              | 734                  | FAIL |
| oracle_prices   | 91.1%    | 17,620   | 873              | 859                  | FAIL |
| perp_funding    | 37.2%    | 399      | 424              | 250                  | FAIL |

**G1 VMs still RUNNING** (all launched 2026-06-27 ~22:07–22:35 UTC):

- `mtds-dex-pools-backfill` RUNNING (dex_pool_state, 2023-01-01→2026-06-27)
- `mtds-dex-swaps-backfill` RUNNING (dex_pool_swaps, 2023-01-01→2026-06-27)
- `mtds-lending-indices-20260627-234500` RUNNING 34.84.133.128 (lending_indices, 2022-01-01→2026-06-27) [5th launch
  ~23:45 UTC; `233514` was SPOT-preempted rc=137 at ~23:42 UTC (ran 4 min); persistent preemptions in asia-northeast1-c]
- `mtds-lst-rates-20260627-220922` RUNNING (lst_rates, 2020-01-01→2026-06-27)
- `mtds-perp-funding-backfill` RUNNING (perp_funding/HYPERLIQUID, 2023-11-01→2026-06-27)
- `mtds-pyth-archive-20260627-221636` RUNNING (oracle_prices archive, 2022-11-01→2023-09-30)
- `mtds-solana-drift-backfill` RUNNING (perp_funding/DRIFT Helius V2, 2025-01-09→2026-06-27)

**Root-cause finding**: 404 DRIFT perp_funding failures (error: `drift_v2_sig_index.parquet missing`) from
2025-01-09→2026-02-16. Sig index consolidated parquet was missing but 6293+875 parts exist in GCS. Handler falls back to
parts; re-running with parts now available should resolve 404 failures. DRIFT-SOLANA is in v10 MVP scope
(mvp_scope.py:489). Separate launcher needed from HYPERLIQUID VM.

**Re-run G2 after ALL VMs complete** (`python scripts/measure_honest_coverage.py --asset-group defi`).

### G1 T+3.5h status check (2026-06-28T05:37Z)

**CORRECTION to prior session's progress**: `process_final=True` in per-VM shard at 05:28-05:29Z were INTERMEDIATE
per-date checkpoint writes (each date writes `process_final=True` then the VM continues next date). NOT completions. All
6 DeFi G1 VMs remain RUNNING.

| VM                                     | Last observed date                  | Progress                      | ETA      |
| -------------------------------------- | ----------------------------------- | ----------------------------- | -------- |
| `mtds-dex-pools-backfill`              | 2023-09-23 (12,980 shard entries)   | ~21% of 2023-01-01→2026-06-27 | ~35-45h  |
| `mtds-dex-swaps-backfill`              | 2023-01-27 (1,585 shard entries)    | ~2% of 2023-01-01→2026-06-27  | ~55-65h  |
| `mtds-lending-indices-20260628-021507` | 2022-03-17 (2143 records last date) | ~5% of 2022-01-01→2026-06-27  | ~60-70h  |
| `mtds-lst-rates-20260628-002136`       | 2020-07-03 (empty markers)          | <1% of 2020-01-01→2026-06-27  | 60h+     |
| `mtds-perp-funding-backfill`           | 2023-12-21 (~51 of 942 days)        | ~5% of 2023-11-01→2026-06-27  | ~40-50h  |
| `mtds-solana-drift-backfill`           | 2025-01-11 (~2 of 527 days)         | 0.4% — **STALL** (2-3h/day)   | 44+ DAYS |

**Solana-drift stall root cause**: Consolidated `drift_v2_sig_index.parquet` missing at
`gs://market-data-tick-defi-prd-central-element-323112/_index/drift_v2_sig_index.parquet`. VM falls back to loading 7169
parts from `_index/drift_v2_sig_index_parts/` for EVERY date query, then batch-resolves 1M+ sigs per day via Helius HTTP
— ~2h/day × 527 days = 44 days total. Day 2025-01-09 took 02:30 (23:58Z→02:25Z); day 2025-01-10 took 02:02
(02:25Z→04:27Z). Day 2025-01-11 has been running since 04:27Z with HTTP 502 retries at batch #197, #3765.

**DeFi phantom reconcile gate**: Blocked until ALL G1 VMs TERMINATED. Solana-drift stall pushes gate from expected ~June
29-30 to ~mid-July unless intervention. Operator decision required.

**BLOCKED-OPERATOR-DECISION**: `launch-mtds-pyth-lst-backfill-vm.sh` has hard-stop in script header: "DO NOT LAUNCH
without operator [ack] in ikenna_orchestrator/pings/slot_2.md". This covers:

- JitoSOL/USD (JITO oracle_prices, 125 expected_unattempted)
- mSOL/USD (MARINADE oracle_prices, 250 expected_unattempted)
- bSOL/USD + INF/USD: 2023-10-01→present Hermes window Operator must approve before these 375 rows can be captured. G2
  oracle_prices gate cannot fully pass for JITO+MARINADE until operator approves the Pyth LST Solana backfill.

### G1 DRIFT Solana perp_funding VM launch (2026-06-27 ~22:35 UTC)

- VM: `mtds-solana-drift-backfill` | Zone: `asia-northeast1-c` | SPOT e2-standard-4
- Date range: 2025-01-09 → 2026-06-27 | Drift V2 Helius RPC (sig index fallback to 7168 parts)
- Root cause: `drift_v2_sig_index.parquet` consolidated missing; 6293+875=7168 parts built 2026-06-01
- 404 DRIFT sig_index failures cover 2025-01-09→2026-02-16; re-running should succeed with parts
- STATUS: RUNNING at launch (IP: 35.187.206.222)
- T+10min verify:
  `gcloud compute instances describe mtds-solana-drift-backfill --zone=asia-northeast1-c --format='value(status)'`
- Logs: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/mtds-solana-drift-backfill/run.log`

### DRIFT perf fix — parts-metadata cache (2026-06-27)

✅ Shipped `market-tick-data-service@874a0bbf` — `perf(drift): add parts-metadata cache to _load_drift_v2_sig_index`

**Root cause**: `_load_drift_v2_sig_index` downloaded ALL 7168 sig-index parts (~48GB) on EVERY date call (O(N×days) =
~26TB for a 550-day backfill). Each date call re-scanned all parts even when most had no overlap.

**Fix**: In-process parts metadata cache (`self._drift_v2_parts_meta_cache`). First call scans all parts and builds
`dict[str, tuple[int|None, int|None]]` (part_name → (min_blockTime, max_blockTime)). Subsequent calls skip
non-overlapping parts without downloading (~20MB per date vs ~48GB). Helper extracted:
`_collect_from_drift_parts_cache`. QG lint-codex + typecheck + full pytest green.

**Re-launch with fix**: Old `mtds-solana-drift-backfill` (22:35 UTC launch, old code) deleted at ~23:42 UTC. Tarball
rebuilt with sha=874a0bbf5109 and uploaded to GCS (23:39 UTC). New VM `mtds-solana-drift-backfill` re-launched at ~23:43
UTC (136.110.117.136) with patched code — cache-enabled, ~43× faster per-date scan.

**Cache confirmation** (23:58:47 UTC):
`"Drift V2 sig index parts: metadata cache built (7169 parts across 3 prefixes)"`. VM processing 2025-01-09 (1,209,478
sigs); only heartbeats 00:01–00:24 UTC — normal for 1.2M sig window via Helius batch API.

### SPOT preemption + re-launch log (2026-06-28 ~00:21 UTC)

**lst-rates preempted** (~00:02 UTC): `mtds-lst-rates-20260627-220922` SPOT-preempted after 2+ hrs; was processing
2020-02 (pre-genesis empty markers). Re-launched as `mtds-lst-rates-20260628-002136` (34.104.175.119) at ~00:21 UTC.

**lending-indices preempted** (6th preemption, ~00:20 UTC): `mtds-lending-indices-20260627-234500` SPOT-preempted after
~35 min. Re-launched as `mtds-lending-indices-20260628-002455` (34.84.28.4) at ~00:25 UTC.

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
- Launched SPOT intermediate `mtds-lending-indices-20260628-010041` accidentally (env var `ON_DEMAND=true` ignored by
  script — script overrides to `false`; need `--on-demand` CLI flag). Deleted immediately.
- Re-launched as `mtds-lending-indices-20260628-010211` (34.146.105.78) ON-DEMAND (PREEMPTIBLE=false) at ~01:02 UTC
  using `--on-demand` CLI flag. This VM will not be preempted.

### DRIFT VM progress (2026-06-28 ~01:00 UTC)

VM is active and writing data events to GCS: 120 event files in
`gs://central-element-323112-events/events/market-tick-data-service/2026-06-28/mtds-solana-drift-backfill/hour=00/` (one
every ~30s). Transient HTTP 504 at batch=3306 at 00:38 UTC was retried; processing continues. Run.log shows only
heartbeats (no intermediate batch log lines — expected for Helius batch resolve).

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

`mtds-lending-indices-20260628-010211` OOM-killed (rc=137, SIGKILL) at 01:07 UTC after processing only 2022-01-01 (13
manifest entries, 0 records all venues — expected pre-genesis). Process killed during date transition to 2022-01-02.
e2-standard-4 (16GB RAM) memory spike during instrument metadata load between dates.

Re-launched as `mtds-lending-indices-20260628-013649` (34.84.220.190) ON-DEMAND at ~01:36 UTC. Idempotent manifest:
2022-01-01 already in shard (13 entries), will resume from 2022-01-02.

### DRIFT VM analysis — NOT stalled, processing slowly (2026-06-28 01:35 UTC)

DRIFT VM confirmed alive: 70 GCS events in hour=01 (one every 30s). Run.log frozen since 00:38 because the code only
logs ERRORS — `continue` on HTTP 504 (no retry loop), silence on successful batches.

Batch mechanics: batch_size=100 sigs, 1,209,478 sigs for 2025-01-09 = 12,095 batches total. Rate observed: batch=3306 at
40 min = ~82 batches/min. Expected 2025-01-09 completion: 12,095/82 = 147 min from 23:58 UTC = ~02:25 UTC.

**Note**: 535 remaining dates (2025-01-10 → 2026-06-27). If avg is 50k sigs/date = 500 batches → ~6 min/date → 535×6 =
~53 hours remaining after 2025-01-09. DRIFT backfill may take 2+ days total for SOLANA perp_funding.

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

Re-launched as `mtds-lending-indices-20260628-021507` (34.180.65.195) ON-DEMAND on `n2-highmem-4` (32GB RAM). 32GB
provides 2x headroom over the peak simultaneous load. Idempotent restart: manifests for 2022-01-01 (13 entries) already
written by both prior runs.

### G1 VM roster (2026-06-28 02:15 UTC — 6 active)

- `mtds-dex-pools-backfill` RUNNING 34.180.72.4 (dex_pool_state)
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43 (dex_pool_swaps)
- `mtds-lending-indices-20260628-021507` RUNNING 34.180.65.195 (lending_indices, ON-DEMAND n2-highmem-4 32GB)
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119 (lst_rates)
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48 (perp_funding/HYPERLIQUID)
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (perp_funding/DRIFT, ~batch 10k/12k for 2025-01-09)

### OOM fix CONFIRMED + DRIFT 2025-01-09 COMPLETE (2026-06-28 02:47 UTC)

**lending-indices 021507 n2-highmem-4 (32GB) — OOM fix confirmed:** At 02:45 UTC, VM is processing `day=2022-01-11` (10
dates past the critical date-1→date-2 transition). ManifestWriter: 13 total entries (6 new for 2022-01-11). No OOM kill.
Rate: ~3 min/date for pre-genesis dates (all 0 records). Est 1641 dates × 3 min = ~82 hrs from launch; will stabilize
once AAVE V3 genesis reached.

**DRIFT VM — 2025-01-09 completed at 02:25 UTC:** `1,209,378 rows` written to `drift_helius_SOL-PERP_20250109.parquet`.
Total time for date 1: 147 min (23:58→02:25). Now processing 2025-01-10: 968,079 sigs loaded from CACHE (parts metadata
cache working — "0 prefixes {}" means no prefix re-scan, cache hit for all 7169 parts). Cache reduces per-date scan from
~48GB to ~20MB.

### G1 VM roster (2026-06-28 02:47 UTC — 6/6 RUNNING)

- `mtds-dex-pools-backfill` RUNNING 34.180.72.4 (dex_pool_state)
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43 (dex_pool_swaps)
- `mtds-lending-indices-20260628-021507` RUNNING 34.180.65.195 (lending_indices, 2022-01-11 @ 02:45, ON-DEMAND 32GB)
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119 (lst_rates)
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48 (perp_funding/HYPERLIQUID)
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (perp_funding/DRIFT, processing 2025-01-10, 968k sigs)

### 03:19 UTC check — 6/6 RUNNING, all nominal (2026-06-28 03:19 UTC)

**VM roster (03:03 UTC watchdog + 03:19 UTC direct check — all 6 confirmed RUNNING):**

- `mtds-dex-pools-backfill` RUNNING 34.180.72.4
- `mtds-dex-swaps-backfill` RUNNING 136.110.123.43
- `mtds-lending-indices-20260628-021507` RUNNING 34.180.65.195 (lending_indices, 2022-01-24 @ 03:18 UTC, 0 rows expected
  pre-genesis)
- `mtds-lst-rates-20260628-002136` RUNNING 34.104.175.119
- `mtds-perp-funding-backfill` RUNNING 35.189.133.48
- `mtds-solana-drift-backfill` RUNNING 136.110.117.136 (DRIFT, processing 2025-01-10 started 02:25 UTC, 968,079 sigs)

**DRIFT 2025-01-10 progress:** 968,079 sigs / 100 per batch = 9,681 batches @ ~82 batches/min = ~118 min. Expected
completion: ~04:23 UTC. Code is silent on success (only logs 504 warnings) — no action needed.

**lending-indices 021507 progress:** At 2022-01-24 @ 03:18 UTC. All 0 rows — expected pre-genesis. AAVE V3 Ethereum
genesis ~2022-03-16 (~51 more pre-genesis dates × 3 min = ~2.5 hrs). First real data rows expected ~05:45-06:00 UTC.
Still STABLE (no OOM, no crash).

### 09:47 UTC check — DRIFT 2025-01-13 ~89%; lending-indices 2022-07-02 (108d ETH gap) (2026-06-28 09:47 UTC)

**VM roster (09:34 UTC watchdog + direct 09:47 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-13:** Log silent since 09:06 (batch 7,366) — expected (success = no log). At 09:47: ~10,769/12,157
batches (89%). Est. completion ~10:04 UTC (~17 min). Projected duration ~148 min (matches Jan 9 at 147 min).
Per-date avg now: 147/122/97/92/148 = ~121 min avg → 520+ remaining dates → confirms orchestrator 44+ day stall.

**lending-indices 021507 — 2022-07-02 @ 09:44 UTC: 4,545 records:**
POLYGON=2393, AVALANCHE=1434, ARBITRUM=718. `aave_v3_ETHEREUM=0` — **108 days post-genesis**.
`aave_v3_OPTIMISM=0` also persistent. Rate: 2.31 min/date; ~1,456 dates remaining ≈ 56 hrs. Disk: 1.9G.

### 09:16 UTC check — DRIFT 2025-01-13 67%; lending-indices 2022-06-19 (95d ETH gap) (2026-06-28 09:16 UTC)

**VM roster (09:04 UTC watchdog + direct 09:16 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-13:** Batch 7,366/12,157 at 09:06 UTC (HTTP 502, `continue`). At 09:16: ~8,196 done (67%).
Rate: ~83 batches/min. Remaining: ~3,961 batches ≈ 48 min. Est. completion ~10:04 UTC.

**lending-indices 021507 — 2022-06-19 @ 09:14 UTC: 9,518 records:**
POLYGON=5108, AVALANCHE=3127, ARBITRUM=1283. `aave_v3_ETHEREUM=0` — **95 days post-genesis**. Confirmed gap.
ManifestWriter: 81 total entries (growing). Rate: 2.38 min/date; ~1,469 dates remaining ≈ 58 hrs. Disk: 1.9G.

### 08:45 UTC check — DRIFT 2025-01-13 45%; lending-indices 2022-06-06; AAVE-ETH 82d gap (2026-06-28 08:45 UTC)

**VM roster (08:34 UTC watchdog + direct 08:45 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-13:** HTTP 502 at batch 4,120 (08:27 UTC, `continue`). At 08:45: ~5,574/12,157 batches (45%).
Rate: ~80 batches/min. Est. completion ~10:07 UTC (~82 min remaining). VM healthy.

**lending-indices 021507 — 2022-06-06 @ 08:43 UTC: 14,193 records:**
POLYGON=9388, AVALANCHE=3199, ARBITRUM=1606. `aave_v3_ETHEREUM=0` — **82 days post-genesis** (2022-03-16).
Definitively confirmed data gap: either IS-derived genesis for ETH V3 markets is much later, or subgraph returns 0.
Will surface as `attempted_failed[UPSTREAM_SUBGRAPH_ZERO]` in G2 gate. Rate: 2.38 min/date; ~1,482 dates left ≈ 59 hrs.
Disk: 2.0G stable.

### 08:13 UTC check — DRIFT 2025-01-13 24%; lending-indices AAVE-ETH zero confirmed; disk 2G (2026-06-28 08:13 UTC)

**VM roster (08:04 UTC watchdog + direct 08:13 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-13:** 37 min elapsed since 07:36 start, ~24% done (~2,923/12,157 batches). No 502s visible yet.
Est. completion ~10:10 UTC. Operator decision on stall still pending.

**lending-indices 021507 — 2022-05-24 @ 08:12 UTC: 4,969 records:**
POLYGON=2395, AVALANCHE=1645, ARBITRUM=929. **`aave_v3_ETHEREUM=0` — NOW 69 DAYS POST-GENESIS (2022-03-16).**
Upgraded from "flag" to **confirmed data gap** for G2 investigation. Likely cause: IS-derived genesis for ETH AAVE V3
markets is much later than 2022-03-16, OR subgraph returning 0 rows. Rate: 2.33 min/date; ~1,495 dates remaining ≈ 58 hrs.

**Disk:** 2.0G free — stable (recovered post git-pack from 287MB critical earlier).

### 07:40 UTC check — DRIFT 2025-01-12 DONE/2025-01-13 started; disk 287MB CRITICAL (2026-06-28 07:40 UTC)

**VM roster (07:34 UTC watchdog + direct 07:40 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-12 COMPLETED at 07:36 UTC:** 722,084 rows, 92 min. Trend: 147→122→97→92 min.
**DRIFT 2025-01-13 started 07:36 UTC: 1,215,691 sigs** — SPIKE (up from 722k). 12,157 batches @ 79/min = ~154 min.
Est. completion ~10:10 UTC. Validates orchestrator stall concern: volumes NOT monotonically decreasing.

**lending-indices 021507 — 2022-05-09 @ 07:37 UTC: 14,349 records:**
POLYGON=6160, AVALANCHE=4365, ARBITRUM=3824. `aave_v3_ETHEREUM=0` persisting (7.5 weeks post-genesis 2022-03-16).
Increasing concern for G2 — may be subgraph data gap or later IS-derived genesis. Rate: 2.33 min/date.

**⚠️ DISK CRITICAL: 287MB free** (was 779MB at 07:08 — lost 492MB in 32 min from other-slot git fetches).
ms-playwright cache=1.9G, per-tab PM repos=1.4-1.5G each. Cannot clear safely without operator. Monitor closely.

### 09:02 UTC check — CeFi 18 running / TradFi 93.97% / DRIFT 2025-01-13 ~154min ETA (2026-06-28 09:02 UTC)

**VM roster:** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-13:** ETA ~10:10 UTC (12,157 batches, confirmed from 07:40 analysis). 1,215,691 sigs spike vs 722k on 2025-01-12.

**TradFi:** 714,985 captured (93.97%), ~45 VMs running, +1,133 since prior check.
**CeFi:** 18/24 wave-1 running (6 completed). Disk 745MB — launcher fix still BLOCKED-DISK.
Confirmed disk pattern: other-slot git fetches draining space. Disk at 745MB at time of this check.

### 07:08 UTC check — DRIFT 2025-01-12 ~70%; lending-indices 2022-04-26; disk 779MB (2026-06-28 07:08 UTC)

**VM roster (07:04 UTC watchdog + direct 07:08 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-12:** Log silent since 06:27 (batch 1,804) — expected (success = no log). At 07:08: estimated batch
~5,043/7,223 (70%). Est. completion ~07:35 UTC. VM RUNNING confirmed.

**lending-indices 021507:** At 2022-04-26 @ 07:06 UTC (2.33 min/date). Still processing compound_v3 venues (all 0
rows — pre-genesis for Compound V3 chains, expected). AAVE V3 multi-chain data continuing.

**Disk:** 779MB free (down 71MB from 850MB at 06:34; normal git ops). Monitoring for further pressure.

### 06:34 UTC check — DRIFT 2025-01-11 DONE/2025-01-12 33%; lending-indices 2022-04-11; DISK FULL (2026-06-28 06:34 UTC)

**VM roster (06:03+06:33 UTC watchdog + direct 06:34 UTC):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-11 COMPLETED at 06:04 UTC:** 760,205 rows, 97 min. Per-date trend: 147→122→97 min (declining volumes).
**DRIFT 2025-01-12 in progress (started 06:04 UTC):** 722,284 sigs, 7,223 batches. 2× HTTP 502 at batch 1332/1804.
At 06:34: ~2,370 done (33%). Est. completion ~07:35 UTC. Stall flag pending operator decision; slot-11 monitoring only.

**lending-indices 021507 — 2022-04-11 @ 06:31 UTC: 4,320 records:**
`aave_v3_POLYGON=3746, aave_v3_AVALANCHE=378, aave_v3_ARBITRUM=196`. `aave_v3_ETHEREUM=0` at 2022-04-11 (26 days past
genesis 2022-03-16) — may be later IS-derived genesis or subgraph data gap. Flag for G2 gate investigation.
Rate: 2.56 min/date; ~1,641 dates remaining ≈ 70 hrs.

**DISK ALERT (06:34 UTC):** Host disk hit 100% (290G). Freed ~850MB by deleting stale /tmp/*.parquet files (avail_idx*,
avail_tradfi, cefi_cat, lending_idx, tmp* — all 3+ hrs old). ENOSPC caused one plan-file truncation (recovered from
git @ 5109aa084). Current free: 850MB — sufficient for ongoing work but monitoring.

### 06:01 UTC check — DRIFT 2025-01-11 ~89%; lending-indices 2022-03-28; STALL flag noted (2026-06-28 06:01 UTC)

**VM roster (05:33 UTC watchdog + 06:01 UTC direct):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-11:** At batch 6,832/7,607 (89%) @ 05:54 UTC. 5× HTTP 502 (all `continue`). Completion est.
~06:04 UTC. NOTE: Orchestrator flagged 🔴 PERFORMANCE STALL at 05:37 UTC (527-day range @ 2-3h/date → 44+ days).
OPERATOR DECISION REQUIRED (options A/B/C in banner). Slot-11 monitoring only; not taking autonomous action.
Observed per-date trend: 2025-01-09=147min, 2025-01-10=122min, 2025-01-11=~97min (declining sig volumes may shorten later dates).

**lending-indices 021507 — 2022-03-28 @ 05:59 UTC: 1,910 records:**
`aave_v3_POLYGON=1508, aave_v3_AVALANCHE=230, aave_v3_ARBITRUM=172` — data flowing. Ethereum 0 rows at genesis
boundary (expected: sparse near genesis). VM stable.

### 06:01 UTC check — DRIFT 2025-01-11 imminently done; lending-indices 2022-03-28 (2026-06-28 06:01 UTC)

**VM roster (05:33 UTC watchdog + 06:01 UTC direct):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-11:** 5× HTTP 502 (batches 197, 3765, 5943, 6797, 6832 — all `continue`). At 05:54 UTC: batch
6,832/7,607 (89%). Remaining ~775 batches @ 79/min = ~10 min. Completion est. ~06:04 UTC.

**lending-indices 021507 — 2022-03-28 @ 05:59 UTC: 1,910 records:**
`aave_v3_POLYGON=1508, aave_v3_AVALANCHE=230, aave_v3_ARBITRUM=172` — multi-chain AAVE V3 data flowing well.
`aave_v3_ETHEREUM=0` (some dates near genesis show 0, expected per rate-update sparsity). ManifestWriter: 39 total entries.

### 05:29 UTC check — FIRST REAL lending-indices ROWS; DRIFT 2025-01-11 63% (2026-06-28 05:29 UTC)

**VM roster (05:03 UTC watchdog + 05:29 UTC direct):** All 6 G1 VMs RUNNING, no preemptions.

**lending-indices 021507 — FIRST NON-ZERO ROWS at 2022-03-14 @ 05:27 UTC:** 57 total records:
`aave_v3_ARBITRUM=20, aave_v3_OPTIMISM=14, aave_v3_POLYGON=5, aave_v3_AVALANCHE=18`. Ethereum AAVE V3 still pre-genesis
(genesis ~2022-03-16, ~2 more dates). ManifestWriter: 63 total entries. Milestone: lending data pipeline confirmed
working on n2-highmem-4 32GB VM.

**DRIFT 2025-01-11:** HTTP 502s at batch 197 (04:30) and batch 3,765 (05:15) — both `continue`, expected. Rate: 79
batches/min. Progress at 05:29: ~4,800/7,607 batches (~63%). Est. completion ~06:04 UTC.

### 04:57 UTC check — DRIFT 2025-01-10 COMPLETE, now 2025-01-11; lending-indices 2022-03-02 (2026-06-28 04:57 UTC)

**VM roster (04:33 UTC watchdog + 04:57 UTC direct):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-10 COMPLETED at 04:27 UTC:** 967,979 rows → `drift_helius_SOL-PERP_20250110.parquet`. Duration: 122 min.
**DRIFT 2025-01-11 in progress (started 04:27 UTC):** 760,705 sigs (cache hit: "0 prefixes {}"), 7,607 batches @
~79/min. Expected completion: ~06:03 UTC. One HTTP 502 at batch 197 (04:30 UTC, `continue`, expected).

**lending-indices 021507:** At 2022-03-02 @ 04:55 UTC (was 2022-02-18 at 04:24 → 12 dates in 31 min = 2.58 min/date).
AAVE V3 Ethereum genesis ~2022-03-16: ~14 more pre-genesis dates × 2.58 min = ~36 min. First real rows ~05:33 UTC.

### 04:25 UTC check — 6/6 RUNNING, DRIFT ~98% on 2025-01-10, lending-indices 2022-02-18 (2026-06-28 04:25 UTC)

**VM roster (04:03 UTC watchdog + 04:25 UTC direct):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-10 status:** Log frozen at batch 6,583/9,681 (03:48 UTC) — expected behaviour (silent on success). At
~79 batches/min, remaining ~3,098 batches complete by ~04:28 UTC. VM is RUNNING and healthy.

**lending-indices 021507:** At 2022-02-18 @ 04:24 UTC (was 2022-02-06 at 03:52 → 12 dates in 32 min = 2.67 min/date).
AAVE V3 Ethereum genesis ~2022-03-16: ~26 more pre-genesis dates × 2.67 min = ~69 min. First real rows ~05:33 UTC.

### 03:53 UTC check — 6/6 RUNNING, DRIFT 68%, lending-indices stable (2026-06-28 03:53 UTC)

**VM roster (03:33 UTC watchdog + 03:53 UTC direct):** All 6 G1 VMs RUNNING, no preemptions.

**DRIFT 2025-01-10 progress:** Batch 6,583/9,681 @ 03:48 UTC (68% complete). One HTTP 502 (batch=6583, `continue` — no
retry loop, expected). Rate: 6,583 batches in 83 min = ~79/min. Remaining: ~3,098 batches. Expected completion: ~04:27
UTC.

**lending-indices 021507 progress:** At 2022-02-06 @ 03:52 UTC (was 2022-01-24 at 03:18 → 13 dates in 34 min = 2.6
min/date). Pre-AAVE V3 Ethereum genesis (~2022-03-16): ~38 more pre-genesis dates × 2.6 min = ~99 min. First real rows
expected ~05:35 UTC. Stable — no OOM, no crash. Base chain genesis correctly detected (block=1 mapping to 2023-06-15 →
pre-genesis for 2022-02-06).
