---
title: "DeFi manifest + data-status canonicalisation (post 2026-06-01 coverage audit)"
created: 2026-06-01
author: ikenna
parent_epic: epics/mtds_mdps_master.md
assigned_vm: vm-defi
status: active
priority: P0
estimate_class: refactor
estimate_baseline_ai_days: 9
estimate_calibrated_ai_days: 3.6
locked_by: live-defi-rollout
locked_since: 2026-05-21
source:
  - plans/audit/results/defi_master_audit_2026_06_01.md (the audit that surfaced all of this)
  - plans/audit/instructions/defi_master_audit_instructions.md (items o–y)
---

# DeFi Manifest + Data-Status Canonicalisation

> **Why this exists**: the 2026-06-01 DeFi coverage audit took many passes because the data is **not in canonical form**
> — scattered buckets, hyphen/underscore + VENUE-CHAIN + blank-chain duplicates, a phantom grid, a v4–v8 schema spread,
> mislabeled empty reasons, and (the keystone) **no materialised `expected_unattempted` state**. The hard-to-find-ness
> IS the bug. This plan makes the **data, manifest, data-status tab/UI, owner code, and docs** canonical so the next
> audit is one pass. Single-walk discipline applies — the multi-bucket sweep MUST be one bundled walk, not N ad-hoc
> walks.

## Sequencing — canonical migration is a GATE before ANY backfill (HARD RULE, operator 2026-06-01)

> Operator: "pipeline mode needs to be in legacy which needs to be migrated — this is why we keep having mess before
> more backfills. Everything must be fully migrated into the right form (env splits etc) so that manifest AND data AND
> data-status are all in their right format."

**No backfill, no B0-run, no `expected_unattempted` generation until the in-scope buckets are in canonical form.**
Backfilling into the legacy layout (no `pipeline_mode`, `category=` not `asset_group=`, no env split, v4–v8, hyphen/
VENUE-CHAIN names) just manufactures more non-canonical data to re-migrate. So **C (migration) is a foundation gate**;
C6 (Pyth backfill) / D1 (features backfill) / E1 (cefi fetch) / B0 (run the chain) are **review-blocked until C is GREEN
for the affected bucket.** Composes with single-walk discipline + the pre-migration-drain HARD RULE (stop VMs + snapshot
before cutover).

### Canonical target form — what "right format" means (every in-scope object + manifest row)

| Dimension | Legacy (now) | Canonical (target) |
| --- | --- | --- |
| Bucket env split | `oracle-prices-{project}` (no env) | `oracle-prices-{env}-{project}` (`-prd`/`-test`) — or fold into `market-data-tick-defi-{env}` |
| Asset-group key | `category=defi` | `asset_group=defi` |
| Pipeline mode | absent in path | `pipeline_mode=` hive partition (value `batch` or `live`) |
| Schema version | v4–v8 spread | v9 |
| data_type name | hyphen / `staking_yields` | underscore canonical (`lst_rates`, `dex_pools`, …) |
| Venue / chain | `UNISWAPV3-ETHEREUM`, blank chain | flat `venue` + populated `chain` |
| Empty reason | blank / `SOURCE_RETURNED_ZERO` mislabel | typed (`EXPECTED_PRE_GENESIS_CHAIN`, …) |
| 4th state | absent | `expected_unattempted` materialised by the run (B0) |

All of the above land in **one bundled single-walk** per bucket (C2–C5 + C7 + C9 + env-split), then the consolidated
`_index` + data-status reflect the canonical form, then backfills run into the correct structure.

## Architecture principle (the governing contract)

**Annotate honestly ONCE at write/consolidation-time (manifest, via the `expected_coverage()` oracle); READ everywhere
else. Never re-derive the expected set in a consumer.**

- **Manifest = canonical honest 4-state ledger.** Every IS∩UAC-expected cell carries one of: `captured` /
  `empty_confirmed[typed reason]` / `attempted_failed` / **`expected_unattempted`** (IS-listed + post-genesis +
  post-launch + in source-coverage, but no data yet). The typed empty reason IS the IS/UAC annotation.
- **Data-status summary + drilldown = VIEWS**: group/aggregate/display by READING `capture_status`; never re-derive.
  Operator filter-chips narrow at request time (never expand). The drilldown `_aggregate_counts` is generic → one fix
  serves IS/MTDS/MDPS/features.
- **Strategy/features preflight = read the SAME 4-state.** No re-deriving genesis/launch/IS rules per consumer.
- **CORRECTION 2026-06-01 (system-first save)**: `expected_unattempted` is **already canonical + the propagation chain
  is already shipped** — archived plan `expected_unattempted_propagation_chain_2026_05_12.md` (Phase 0 UAC reasons
  `EXPECTED_UPSTREAM_EMPTY`/`EXPECTED_OUTSIDE_PROCESSING_SCOPE` ✅; Phase 1 MTDS instruments-service pre-flight →
  `record_expected_unattempted` ✅; Phase 2 MDPS ✅). It is **writer/orchestrator-driven** (MTDS pre-flight reads the IS
  manifest and records owed cells on skip), **NOT** consolidator-driven. The DeFi manifest shows **0**
  expected_unattempted rows for ONE reason (deferred Phase 6,
  `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`): **no prod MTDS batch has RUN on the
  post-Phase-1+2 code yet** (defi 1.6M rows, 0 owed). So the fix is **run the existing chain + validate**, NOT build a
  parallel consolidator mechanism. (The earlier "never materialised / 0 source hits" reading was wrong — the handlers
  don't reference it because the pre-flight lives in the batch orchestrator, not per-handler.)

## `expected_unattempted` — the mechanism exists; RUN it for DeFi (corrected B0)

**Do NOT build a consolidator step (rejected — would duplicate the shipped chain).** The propagation chain already
exists (`expected_unattempted_propagation_chain_2026_05_12.md`, archived, Phases 0–2 shipped): the MTDS batch
orchestrator does an instruments-service **pre-flight** — it reads the IS manifest, and for every instrument the IS
lists that the batch will NOT attempt (outside scope / upstream empty), it calls `record_expected_unattempted(...)` with
reason `EXPECTED_OUTSIDE_PROCESSING_SCOPE` / `EXPECTED_UPSTREAM_EMPTY`. MDPS + features propagate it downstream. The
owed rows are written by the **writer**, at shard grain, gated by the **IS manifest** (which already encodes "this
instrument should exist") — exactly the operator's intent (`we have the instrument + it's post-genesis, but no data`).

**Why DeFi shows 0**: no prod MTDS batch has run on the post-Phase-1+2 code for the DeFi buckets since 2026-05-19. So
the remaining work is to **RUN the existing chain for the DeFi handlers + validate** (the deferred Phase 6), NOT
re-implement.

What to verify/wire (B0 corrected scope):

- Confirm the DeFi MTDS batch orchestrator path (oracle / perp / lst / lending / dex handlers) goes through the same
  instruments-service pre-flight that records `expected_unattempted` (Phase 1 wired CeFi/TradFi; confirm DeFi handlers
  are on that path — they may need wiring since DeFi uses dedicated buckets + a different orchestration).
- Run a DeFi MTDS dry-run on a sample date → confirm `expected_unattempted` rows generate with correct reasons.
- Then the denominator is honest automatically: `% = captured / (captured + empty + failed + expected_unattempted)` —
  consumers just read it (B1/B2/B3).
- Composes with `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md` (the deferred validation).

## Status legend: ✅ shipped · ⏳ ready/in-flight · ☐ todo · canonical todos below feed the orchestrator backlog

## A. Owner code (writers) — canonical writes

- [x] ✅ [CODE] P0. A1 pre-genesis empty-reason: oracle + evm-defi handlers classify via UAC `get_chain_genesis_date()`
      → `EXPECTED_PRE_GENESIS_CHAIN`. market-tick-data-service@840d85f1.
- [~] [DATA] P1. A2 pre-venue-launch reason — manifest migration (operator: "captured in UAC if genuinely pre venue +
      migrated in manifest"). **UAC ALREADY HAS** most launch dates in `DEFI_VENUE_LAUNCH_DATES` keyed `VENUE-CHAIN`
      (MARINADE-SOLANA 2021-08-02, JITO-SOLANA 2022-08-16, LIDO-ETHEREUM 2020-12-19, ETHERFI/ETHENA, …) — my earlier
      "None" was a wrong-key lookup (flat `LIDO` vs `LIDO-ETHEREUM`). **APPLIED 2026-06-01**:
      `plans/audit/results/defi_venue_launch_relabel_migration_2026_06_01.py --apply` relabeled **1,337** lst-rates rows
      → `EXPECTED_PRE_VENUE_LAUNCH` (ETHENA/ETHERFI/LIDO 353 each + MARINADE 278), UAC-backed + snapshotted.
- [ ] [CODE] P1. A2a populate UAC `DEFI_VENUE_LAUNCH_DATES` for the venue-chains genuinely missing it (the migration
      reports them): **perp** `ASTER`, `LIGHTER-ZKSYNC`, `PACIFICA-SOLANA`, `HYPERLIQUID` (clear new venues — add accurate
      launch dates). **DEX per-chain** (`CURVE-OPTIMISM`, `PANCAKESWAPV3-BSC`, `UNISWAPV3-POLYGON`, `BALANCER-OPTIMISM`,
      `AAVE_V3-BASE`, `SPARK-ETHEREUM`, …) — **data-quality flag**: their captured rows show a uniform first-captured
      `2021-01-01` across ALL chains incl. Base (launched 2023), which is impossible → investigate (placeholder/wrong-date
      captured rows) BEFORE adding launch dates. Do NOT bulk-add ambiguous dates. Then re-run the relabel. parent_epic: manifest_master.
- [ ] [CODE] P1. A2b wire `lst_rates_handler` (L512-535) + `solana_defi_handler` empty branches to emit
      `EXPECTED_PRE_VENUE_LAUNCH` via the `VENUE-CHAIN` launch lookup (perp_funding_handler L344-353 already does it for
      Aster — the pattern). So future writes are correct. parent_epic: mtds_mdps_master.
- [x] ✅ [CODE] P1. A3 data_type name SSOT at write — **verify-done 2026-06-01**: every DeFi handler `_DATA_TYPE`
      constant + `data_type=` literal is underscore-canonical
      (`dex_pools`/`dex_swaps`/`lending_indices`/`lst_rates`/`oracle_prices`/ `perp_funding`/`dex_pool_state`); **zero
      hyphen literals written by any handler**. The hyphen variants (`lending-indices`/`dex-pools`/`dex-swaps`) +
      `staking_yields` in the corpus are purely LEGACY data → fixed by C2.
- [ ] [CODE] P2. A4 chain dimension always populated: QG guard fails a DeFi `record_captured`/`record_empty` with blank
      `chain` for a chain-scoped data_type.
- [ ] [CODE] P1. A5 LIGHTER perp_funding adapter fix: `SOURCE_RETURNED_ZERO` across full post-launch life (zkSync
      endpoint returns nothing) — verify endpoint/auth.
- [x] ✅ [CODE] P0. A6 `expected_unattempted` is ALREADY canonical in UAC (`honest_coverage.py`:
      `EXPECTED_UPSTREAM_EMPTY` + `EXPECTED_OUTSIDE_PROCESSING_SCOPE` reasons; shipped via
      `expected_unattempted_propagation_chain_2026_05_12.md` Phase 0). No new state to add — verified 2026-06-01.
- [x] ✅ [CODE] P0. A7 **fetch-failure swallow bug — record `attempted_failed` not `empty_confirmed`** (operator 2026-06-01).
      Systemic: a fetch helper does `except Exception: … return []`, swallowing a timeout/DNS/RPC error → caller sees
      zero-rows-no-error → `record_empty(SOURCE_RETURNED_ZERO)` = a silent lie the data is genuinely empty.
      **Fixed (mtds@d3d26f56, re-raise → caller `record_failed`)**: `lst_rates_handler` L697, `oracle_prices_handler`
      L820/L948. **Swept clean**: instruments-service + features-service adapter I/O — **no swallow sites found** (the bug
      was MTDS-specific). **`lending_indices_handler` L989** (Aave RPC fallback): the handler already routes subgraph
      errors to `record_failed` (comments L736-741/L838-839 reference a prior fix for this exact class) — the residual
      `_do_rpc_walk` `return []` is an ambiguous fallback path, NOT a clear bug; flagged for careful tracing under audit
      item (i), do NOT rush a fix. Per-adapter audit codified in `defi_master`(aa)/`mtds_mdps`(i)/`instruments`(h)/
      `features_and_ml`(u). 3 mtds fixes need QG green before LDR. parent_epic: mtds_mdps_master.

## B. Manifest consolidation + data-status (owner code) — honest by default

- [ ] [DATA] P0. B0 (CORRECTED — do NOT build a consolidator step) RUN the existing expected_unattempted chain for DeFi:
      confirm the DeFi MTDS batch orchestrator goes through the instruments-service pre-flight that calls
      `record_expected_unattempted` (wire the DeFi handlers onto it if not), then run a prod DeFi MTDS batch so the owed
      rows generate; validate the denominator. **GATED on C-GREEN** — the owed rows must land in the canonical structure
      (env-split/`pipeline_mode`/`asset_group=`), so migrate first. Closes deferred
      `issues/expected_unattempted_validation_pending_phase3_2026_05_19.md`. parent_epic: manifest_master.
- [ ] [CODE] P1. B1 `coverage-summary` (`data_status_service._build_coverage_for_cat`): drop the `len(index)`
      self-referential denominator; read the 4-state (or expected-dates oracle) + `is_expected()` gate; align with
      `manifest-status`.
- [ ] [CODE] P0. B2 drilldown (`data_status_hierarchical._aggregate_counts`): count the 4th bin `expected_unattempted`
      so genuinely-missing cells appear in the tree (the most useful "where's the missing data" view). Generic path →
      fixes IS/MTDS/MDPS/features at once.
- [ ] [CODE] P1. B3 drilldown denominator: `% = captured / (captured+empty+failed+expected_unattempted)`;
      pre-genesis/launch render out_of_scope (already excluded by the oracle once B0 lands).
- [ ] [CODE] P2. B4 `data_status_rollup_worker.py`: read the 4-state, not manifest row count.
- [ ] [UI] P1. B5 deployment-ui drilldown: render the 4-state (esp. `expected_unattempted`) + per-chain split; badge
      legend. (playwright gate applies)

## C. Data / manifest migration (single-walk, bundled) — fix existing rows

> **C is the foundation gate** (see Sequencing). One bundled single-walk per bucket applies C0+C2+C3+C4+C5+C7+C9
> together (no N ad-hoc walks). Backfills (C6/D1/E1) + B0-run are blocked until C is GREEN for the affected bucket.

- [ ] [DATA] P0. C0 **path + bucket canonicalisation (the foundational migration) — RUN ON A VM (operator-confirmed
      2026-06-01)**: for each dedicated DeFi bucket, rewrite object paths to the canonical layout — `category=defi`→
      `asset_group=defi`, add the `pipeline_mode=` (`batch`/`live`) hive partition, move into the **env-split** bucket
      (`{kind}-prd-{project}`). Script ready (`plans/audit/results/defi_object_path_canonicalisation_2026_06_01.py`,
      server-side copies + dry-run). **Walk on a `vm-defi` in asia-northeast1** under the pre-migration drain + snapshot
      discipline (server-side copies but ~500k objects across 6 buckets → VM for reliability/throughput). Bundle with
      C2–C5/C7/C9 in the single walk; then delete originals after verified cutover. parent_epic: manifest_master.
- [x] ✅ [DATA] P0. C1 oracle-prices index relabel + Pyth dedup — **APPLIED 2026-06-01** via
      `plans/audit/results/defi_oracle_relabel_migration_2026_06_01.py --apply`: 728 pre-genesis relabel →
      `EXPECTED_PRE_GENESIS_CHAIN`; Pyth 1,185 chain `''`→`SOLANA` + dropped 1,034 dup empties; 9,717→8,683 rows; PYTH
      now all `chain=SOLANA` (1,447 = 1,185 captured + 262 owed). Original snapshotted →
      `_index/snapshots/pre_relabel_2026_06_01.parquet`. Fixes the consolidated index; durable until a full consolidator
      rebuild (which needs the source rows fixed too — the bundled C2–C7 walk). Writer A1 makes future writes correct.
- [ ] [DATA] P1. C2 data_type alias dedup across buckets: `lending-indices`→`lending_indices`, `dex-pools`→`dex_pools`,
      `dex-swaps`→`dex_swaps`, `staking_yields`→`lst_rates` (rename rows; data exists). ONE walk.
- [ ] [DATA] P1. C3 VENUE-CHAIN→flat: legacy `UNISWAPV3-ETHEREUM` venue strings → flat `venue` + populated `chain`. Same
      walk.
- [ ] [DATA] P1. C4 schema v4–v8 → v9 re-version across the dedicated DeFi buckets. Same walk. parent_epic:
      manifest_master.
- [ ] [DATA] P1. C5 phantom-grid delete: remove the cartesian `data_type × venue` empty grid in `market-data-tick-defi`;
      point data-status at the dedicated indexes.
- [ ] [DATA] P2. C6 Pyth ~5-week backfill (2026-04-15→present, Hermes API) on a VM. **GATED on C0/C-GREEN** (backfill
      into the canonical env-split/`pipeline_mode`/`asset_group=` structure, never the legacy layout).
- [x] ✅ [DATA] P2. C7 reason relabel — chain-genesis portion APPLIED 2026-06-01 (warmup-retry fix landed it locally) —
      `plans/audit/results/defi_chain_genesis_relabel_migration_2026_06_01.py` (snapshot-protected, idempotent,
      `get_chain_genesis_date`-driven). Dry-run across all dedicated buckets: oracle ✅ done (C1, 728 rows); **lst-rates 75
      rows (SOLANA pre-2020-03-16) pending** — apply kept failing on flaky LOCAL GCS DNS (lst-rates/lending-indices time
      out); lending/perp/dex already clean on chain-genesis. **Run this on a VM in asia-northeast1** (stable in-region
      network) to land lst-rates. **Pre-VENUE-launch portion** (PACIFICA/ASTER/ETHERFI/LIDO/MARINADE pre-launch) stays
      blocked on A2a (`DEFI_VENUE_LAUNCH_DATES` populated) — bundle into the C2–C4 walk.
- [ ] [DATA] P1. C8 fill manifest under-enumeration: UAC declares 90 defi venue-keys but manifest enumerated only lst
      14/22, lending 6/21, perp 5/8; genuine absentees DRIFT-SOLANA (Solana MVP), FRAX, MORPHO, FLUID. parent_epic:
      defi_master.
- [ ] [DATA] P1. C9 legacy DeFi bucket object paths are pre-canonical —
      `day=/category=defi/venue=/chain=/instrument_type=/data_type=/file.parquet`: **`category=` not `asset_group=`**
      AND **no `pipeline_mode=` partition** (canonical raw_tick_data layout is
      `…/day=/pipeline_mode={mode}/asset_group={ag}/…`). The manifest ROWS carry pipeline_mode (handlers pass it); the
      object PATHS don't. Normalise the dedicated DeFi bucket paths in the same single-walk as C2–C4. parent_epic:
      manifest_master.
- [x] ✅ [DATA] P0. C10 **bad start dates — phantom captured-pre-genesis fix APPLIED 2026-06-01**
      (`plans/audit/results/defi_phantom_captured_pre_genesis_fix_2026_06_01.py --apply`): **8,477** index rows falsely
      marked `captured` for a (chain, date) before the chain's UAC genesis (no backing objects — verified) →
      `empty_confirmed/EXPECTED_PRE_GENESIS_CHAIN`. dex-pools 8,410 (BASE 4,750 / ARBITRUM 1,452 / OPTIMISM 1,396 /
      ZKSYNC 812), dex-swaps 61, oracle 6. Snapshotted. Removes the false-captured coverage inflation. parent_epic: manifest_master.
- [ ] [DATA] P0. C11 **deeper phantom audit — are the REST of the dex `captured` rows object-backed?** The uniform
      first-captured `2021-01-01` across all chains (the genesis ones now fixed) is a red flag that the dex backfill
      enumerated `captured` without object-backing. Walk dex-pools/dex-swaps `captured` rows vs actual GCS objects;
      any captured row with no object → relabel honest (`MISSING_EXPECTED`/`attempted_failed`/`empty_confirmed`). Likely a
      VM job (object listing at scale). parent_epic: manifest_master.

## D. Features propagation (L3) — coverage must reach features-service

- [ ] [DATA] P0. D1 features-onchain-defi is near-empty (3 rows); features-delta-one-defi + features-volatility-defi
      have NO index → derived features (staking*apy_bps/funding_rate_apy_bps/basis_bps/realized_vol*\*) absent. Run the
      features backfill for the in-scope DeFi instruments over the captured window. **GATED on C-GREEN** (features must
      read canonical raw, else they inherit the mess). parent_epic: features_and_ml_master.

## E. CeFi perp leg (hybrid hedge) — fix-fetch

- [ ] [DATA] P0. E1 CeFi `derivative_ticker` (funding carrier) fetch failures: OKX-FUTURES + ASTER 100%
      attempted_failed; refresh to current (stale ~3–5 weeks). parent_epic: cefi_master.

## F. Docs / SSOT — record canonical forms

- [ ] [DOCS] P1. F1 `codex/02-data/defi-data-types-catalog.md`: underscore-canonical data_type names + dedicated bucket
      per type + hyphen aliases deprecated.
- [ ] [DOCS] P1. F2 `codex/02-data/availability-manifest-and-data-status.md` + `data-status-drilldown.md`: document the
      materialised `expected_unattempted` 4-state + the manifest-annotates-once/consumers-read principle + per-chain
      requirement.
- [ ] [DOCS] P2. F3 `_defi_manifest.py` reason-labeling docstring (~L213-220 "future refinement" TODO) → mark
      pre-genesis done (A1); note pre-launch (A2).
- [ ] [DOCS] P2. F4 CLAUDE.md "Manifest + honest absence" note: `expected_unattempted` is materialised at consolidation
      from the oracle; consumers read, never re-derive.

## G. Solana basis MVP — operationalisation (migrated from archived `solana_basis_trading_mvp_2026_06_01.md`)

> **Migrated 2026-06-01** from `plans/archive/solana_basis_trading_mvp_2026_06_01.plan.md` (Phases 1–4 code SHIPPED;
> these 4 follow-ups are the operationally-shipped half per CLAUDE.md "Plans Run To Actual Completion"). The Solana
> MVP plan documented: Drift V2 historical ingester + 4 Solana spot DEX ingesters (Orca/Raydium/Phoenix-stub/Jupiter)
> + 7 canonical UAC data types (PERP_TRADES, PERP_MARK_ORACLE, PERP_OPEN_INTEREST, DEX_POOL_STATE, DEX_ORDERBOOK,
> DEX_QUOTE, DEX_TRADES) + `InstrumentType.DEX_POOL` + `SolanaBasisGcsLoader` wiring into the existing
> `CARRY_BASIS_PERP@raydium-drift-sol-1h-sol-v5-prod` archetype + `--live --continuous` flag (the concrete
> realization of CLAUDE.md "Live = batch" hard rule).
>
> All four operator-launched follow-ups (G1–G4) must land in **canonical structure**
> (env-split bucket + `pipeline_mode=` partition + `asset_group=defi`) — so they are **GATED on C-GREEN for the
> dedicated DeFi buckets that hold the Solana writes** (`market-data-tick-defi-prd-…` for perp_funding/perp_trades +
> dedicated `dex-pools-prd-…` / new `dex-pool-state-prd-…` / `dex-orderbook-prd-…` / `dex-quote-prd-…` if those
> are split per A1 SSOT). If the dedicated bucket for a Solana data_type doesn't exist yet, that's a **bucket
> provisioning** prerequisite (file under C0 / `cloud-providers.yaml`) — not a license to write to the legacy
> `market-data-tick-defi-${PID}` (no env, no pipeline_mode) path.

| Dep | Item | Owner | Verification |
| --- | --- | --- | --- |
| (a) before (b) → (c) → (d) | sequential | operator | each gated on prior step's manifest-verified evidence |

- [ ] [DATA] P0. G1 Launch the full 2024-06-01 → 2026-06-01 backfill VM (Drift V2 historical + Solana spot DEX state).
      Operator-launched from laptop OR `vm-defi`. Recipe: the four CLI scripts in
      `market_tick_data_service/scripts/backfill_drift_v2_historical.py` (perp_funding + perp_trades) +
      `backfill_solana_dex_state.py` (Orca Whirlpool + Raydium classic AMM) for each day in window; estimated
      ~36GB total payload across the 730-day window. **GATED on C-GREEN for the dedicated DeFi buckets** that hold
      these writes (env-split + `pipeline_mode=batch` + `asset_group=defi`). Verification (per CLAUDE.md "Plans Run
      To Actual Completion"): `gsutil ls gs://market-data-tick-defi-prd-${PID}/raw_tick_data/by_date/day=*/pipeline_mode=batch/asset_group=defi/venue=DRIFT/chain=SOLANA/instrument_type=perpetual/data_type=perp_funding/`
      returns a parquet per day in window; sample-inspect 3 random parquets (early/mid/late window) for non-empty
      `funding_rate`, `oracle_price_twap`, `mark_price_twap` columns; manifest-verified row count > 0 per
      day-shard; equivalent checks for `perp_trades` (active days only; allow `empty_confirmed[SOURCE_RETURNED_ZERO]`
      on quiet days) + `dex_pool_state` for Orca + Raydium. **No silent gaps**: any day with 0 rows MUST carry a
      typed `empty_confirmed` reason (not `attempted_failed`). parent_epic: mtds_mdps_master. **Operator-launched
      (long wall-clock; not a dispatch).**
- [ ] [DATA] P0. G2 Launch live-mode snapshotters via `--live --continuous` (mtds@1d35c7f2 unified live/batch path).
      Terminal A: `python -m market_tick_data_service.scripts.backfill_drift_v2_historical --markets SOL-PERP --live
      --continuous --interval-seconds 3600 --data-types funding` (hourly). Terminal B:
      `python -m market_tick_data_service.scripts.backfill_solana_dex_state --venues orca,raydium --live --continuous
      --interval-seconds 60 --samples-per-day 60 --data-types pool_state` (1-min). These run as long-lived VMs on
      `vm-defi` (lifecycle_class=LONG_LIVED_LIVE per CLAUDE.md vm naming SSOT). **GATED on G1** (need backfilled
      history to be loadable as warmup) + **C-GREEN** (writes target canonical structure). Verification (per
      CLAUDE.md "Plans Run To Actual Completion"): T+5min check post-launch — both VMs RUNNING in
      `gcloud compute instances describe`; ≥1 parquet under `day=<TODAY>/pipeline_mode=live/asset_group=defi/…`
      within the first interval (1 min for DEX, 1 h for Drift funding); manifest `capture_status=captured` rows
      generated. Symptom of regression: `SolanaBasisGcsLoader` logs `no perp_funding rows for live`. Depends on
      G1 (backfill warmup) before paper trade can run a meaningful history. parent_epic: mtds_mdps_master.
      **Operator-launched.**
- [ ] [PLAY] P0. G3 Run 24h paper trade via `e2e-testing/scripts/defi/run-paper.sh --strategy SOL_BASIS`. Recipe:
      ```bash
      cd e2e-testing && bash scripts/defi/run-paper.sh --strategy SOL_BASIS --tick-interval 3600 --continuous \
          --execution-provider solana-devnet --initial-capital-usd 100000
      ```
      Engine flows `--strategy SOL_BASIS` → `colocated_engine.py` → `SolanaBasisGcsLoader` → fill-sim on devnet
      (signed, not broadcast). **GATED on G2** (live data must be flowing so the engine reads a non-stale tape).
      Verification (per CLAUDE.md "Plans Run To Actual Completion" + Promote Workflow Path SSOT): 24h wall-clock
      session writes a non-empty trade log + PnL series; Firestore `MinimalCandidateManifest` populated; Sharpe
      ratio + realised funding earnings − slippage computed; sample-inspect 3 trades for honest fill simulation
      (no NaN/inf, no fictional fills against zero-liquidity ticks); manifest path
      `gs://market-data-tick-defi-prd-${PID}/paper_trade/…` (or whichever sink the engine writes to) has the
      session's full output. **DART `ManualTradeGateDialog` enforces first-3-days hand-confirmation per CLAUDE.md
      Promote Workflow Path.** parent_epic: mtds_mdps_master. **Operator-launched (long wall-clock; not a dispatch).**
- [ ] [HUMAN] P0. G4 Promote to live wallet — **HUMAN-ONLY per CLAUDE.md hard-stop list** (`## Plans Run To Actual
      Completion`: wallet keys + kill-switch arming are human-only; agent never runs `run-live.sh`). Valid promote
      target per CLAUDE.md Promote Workflow Path is `paper_1d → live_early`; `live_full` is post-cutover. Operator
      runs:
      ```bash
      cd e2e-testing && bash scripts/defi/run-live.sh --strategy SOL_BASIS --tick-interval 3600 --continuous \
          --execution-provider <copper|ceffu|cloud_kms_encrypted> --capital <amount> --wallet <KMS_KEY_ALIAS>
      ```
      **GATED on G3** (Sharpe-positive ack required) + **C-GREEN** + **G2 live data flowing**. Verification: real
      wallet ≥7-day session per CLAUDE.md Master Plan (live DeFi 2026-05-23 gate already shipped — this is a
      Solana-archetype-specific operational gate, not a master-plan blocker). The agent **never** ticks G4 — the
      operator does after the live run completes. parent_epic: mtds_mdps_master.

### G5–G8 — post-MVP feature follow-ups (migrated 2026-06-01 from archived MVP plan body)

> **MIGRATED FROM** `plans/archive/solana_basis_trading_mvp_2026_06_01.plan.md` § "Phase 2 deferred / P1 follow-ups".
> These were orphaned in the archive body — not picked up by the inventory regenerator, not in canon §G's G1–G4
> operational chain. Restored to active inventory here so backlog-derivation crons + done-vs-left dashboards pick
> them up. None are MVP-blockers (G1–G4 are sufficient to ship the basis trade); these are post-MVP feature
> additions and depth-of-data improvements.

- [ ] [CODE] P1. G5 **Phoenix radix-slab decode (top-of-book bid + ask + size).** The market account is 1.7MB; the
      top-of-book decode is ~50-100 LOC of binary parsing against Phoenix's documented slab layout. Full L2 (deeper
      levels) is harder + can ship later. Current state: `PhoenixOrderbookIngester` (mtds@d3d26f56) fetches the market
      account successfully (proves the RPC path) but routes via `record_failed(reason="SOURCE_HANDLER_TODO_PHOENIX_DECODE")`.
      Acceptance: top-of-book parsed; `best_bid_price + best_ask_price + their sizes + spread_bps + mid_price` populated;
      `record_captured` instead of `record_failed`; 5+ unit tests cover the binary decode against known slab states.
      parent_epic: mtds_mdps_master. Not GATED on G1–G4 (independent feature add).
- [ ] [CODE] P2. G6 **Jupiter historical reconstruction.** `JupiterQuoteIngester` (mtds@d3d26f56) is forward-only —
      Jupiter doesn't expose historical quote endpoints. For the 2024-06-01 → today backtest window, reconstruct
      historical Jupiter routes by simulating Jupiter's routing algorithm against the underlying Orca/Raydium pool
      states at the same timestamps. Acceptance: per (timestamp, size-bucket) row matching forward-collected quote
      structure within ±5%; backtest harness can read Jupiter quotes for any day in window. parent_epic: mtds_mdps_master.
      GATED on G1 (need Orca + Raydium pool states backfilled).
- [ ] [CODE] P2. G7 **Orca tick-array decode** (concentrated-liquidity depth visualisation). Current MVP uses
      `sqrt_price` + `liquidity` scalars (sufficient for next-tick slippage approximation). Full tick-array decode
      enables tick-distribution depth maps + better mid-size-fill simulation. ~150-200 LOC binary parsing of the 3
      nearest tick arrays around `tick_current_index`. Acceptance: per-snapshot tick array state captured alongside
      pool state; downstream consumers can compute fill slippage at arbitrary sizes. parent_epic: mtds_mdps_master.
      Not GATED on G1–G4 (independent depth improvement).
- [ ] [CODE] P2. G8 **Raydium second WSOL/USDC pool** — extend `RaydiumClassicAmmIngester` defaults if a meaningful
      TVL pool materialises. The plan-time secondary Raydium pool dropped to $4.6K TVL by 2026-06-01 (below noise
      threshold); current default ingestion is just the top $8.8M pool. The constant scaffold is forward-compat —
      adding a pool requires only updating `_RAYDIUM_POOLS` dict. Acceptance: if a second SOL/USDC Raydium pool
      reaches > $1M TVL, add it; ingest from the canonical date; backtest harness reads both. parent_epic:
      mtds_mdps_master. Trigger: TVL probe shows > $1M.

### G — non-conflict notes (from conflict scan 2026-06-01)

- `solana_defi_legacy_migration_2026_05_27.md` (active): canonical Solana types per that plan are
  `dex_pools`+`SOLANA_AMM_POOL` (Kamino vault METADATA snapshot) vs the MVP's `DEX_POOL_STATE` (Orca/Raydium AMM
  STATE time-series for fill-sim) — **complementary, not conflicting** (different shard grain, different consumers,
  different UAC contracts). Both flow through the same dedicated-bucket SSOT (`get_write_bucket_name`); the new
  `DEX_POOL_STATE` writes target their own dedicated bucket once provisioned (C0 prerequisite).
- `plans/active/issues/bug_d_prime_drift_backfill_2026_05_31.md`: SUPERSEDED 2026-06-01 (the Helius sig-walking path
  that issue documents is OBSOLETE — Drift V2 historical now flows via `data.api.drift.trade` Velocity Data API per
  the archived MVP plan + new codex `codex/04-architecture/drift-v2-data-sources.md`). Issue doc gets a SUPERSEDED
  banner in the same archival commit.

## Verification (full-execution criterion)

Re-run `plans/audit/results/defi_strategy_coverage_query_2026_06_01.py` + the drilldown: every DeFi cell carries a
canonical data_type (underscore), flat venue + populated chain, v9 schema, a typed reason; `expected_unattempted`
materialised so `% captured = captured / (captured+empty+failed+expected_unattempted)`; coverage-summary == drilldown ==
manifest-status denominators; features-onchain-defi populated for the in-scope window; **Solana basis MVP G1–G4
operationally-shipped (G4 human-only)**; the next audit needs one pass.
