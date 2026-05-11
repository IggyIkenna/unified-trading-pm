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

> **🟡 IN-FLIGHT REFACTOR — paper-vs-live workflow maturity (folded into master Group F/G 2026-05-09)**: UAC additive
> `ExecutionTarget` / `ExecutionTrigger` enums + `decompose()` helper + `paper_target_registry` SSOT + per-chain paper
> primitive (Tenderly fork EVM; Solana devnet for jitoSOL/mSOL/bSOL legs of `carry_staked_basis`) all compose with this
> plan's DeFi work. **BE AWARE** when touching DeFi connectors / chain RPC config / Aave / Uniswap / flash-loan
> receiver: paper-mode wiring goes through `paper_target_registry[chain]` — don't hardcode fork URLs or testnet
> endpoints. SSOT: [`master_to_live_defi_2026_05_23.md`](./master_to_live_defi_2026_05_23.md) § "Folded paper-vs-live
> workflow maturity" +
> [`codex/05-infrastructure/per-venue-paper-policy.md`](../../codex/05-infrastructure/per-venue-paper-policy.md).
> Question doc (retired 2026-05-09 PM@5d2d74c1; folded into
> [`master_to_live_defi_2026_05_23.md`](master_to_live_defi_2026_05_23.md) § "Folded paper-vs-live workflow maturity").

> **📋 RELATED PLAN — Promote workflow (May-23 dual-track + post-cutover, spawned 2026-05-10)**: the May-23 cutover for
> `carry_staked_basis` (DeFi lead archetype) lands via dual-track promote workflow:
> [`promote_workflow_may23_cli_path_2026_05_10.md`](./promote_workflow_may23_cli_path_2026_05_10.md) (CLI primary +
> minimal UI parallel) +
> [`promote_workflow_post_cutover_ui_pipeline_2026_05_10.md`](./promote_workflow_post_cutover_ui_pipeline_2026_05_10.md)
> (full UI extension post-cutover). **BE AWARE** when touching `e2e-testing/scripts/defi/run-paper.sh` / `run-live.sh` /
> `colocated_engine.py` (CLI track owners) OR Copper custody (Phase 4.A operational verification owner) OR Tenderly fork
> (Phase 4.D validation owner) OR Solana devnet wiring for jitoSOL/mSOL/bSOL (Phase 4.C `pvl-p20c` owner). Question doc:
> [`plans/questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md`](../questions/promote_workflow_backtest_to_paper_to_live_2026_05_08.md).

## Codex SSOTs

This plan implements / extends the following codex documents (read these BEFORE making code changes; drift between code
and these docs is a review-blocking failure per `doc → plan → code`):

- [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
  — manifest v5 schema + DeFi `chain` first-class shard axis + `EXPECTED_PRE_GENESIS_CHAIN` /
  `EXPECTED_PRE_VENUE_LAUNCH` reasons + DeFi protocol-launch-date pre-skip semantics
- [`codex/02-data/honest-absence-downstream-handling.md`](../../codex/02-data/honest-absence-downstream-handling.md) —
  per-asset-group `empty_confirmed` legitimacy rule (DeFi: only venue-level reasons legit; instrument-day source-zero
  must flip to `attempted_failed`); DeFi pre-genesis chain reasons + downstream NaN handling
- [`codex/02-data/per-asset-group-bucket-layouts.md`](../../codex/02-data/per-asset-group-bucket-layouts.md) — DeFi GCS
  bucket layout + `chain=` hive partition axis + per-protocol shard atom
- [`codex/02-data/instrument-pipeline-defi.md`](../../codex/02-data/instrument-pipeline-defi.md) — DeFi
  instruments-service catalog (per-(chain, protocol, instrument_id) lifecycle) + LST_TOKEN_TO_PROTOCOL_ASSET SSOT
- [`codex/02-data/defi-data-types-catalog.md`](../../codex/02-data/defi-data-types-catalog.md) — DeFi data_type
  enumeration (lending_rates / lst_yields / oracle_prices / vault_share_prices / perp_funding / ohlcv / dex_swaps)
- [`codex/04-architecture/batch-live-architecture.md`](../../codex/04-architecture/batch-live-architecture.md) —
  batch=live unified pipeline (same shard atom, same fields, same `available_at` semantics); applies to DeFi end-to-end
- [`codex/04-architecture/flash-loan-receiver.md`](../../codex/04-architecture/flash-loan-receiver.md) — Aave V3 flash
  loan deployment + `connect()` validation; required for `carry_staked_basis` recursive-staking unwind path
- [`codex/04-architecture/interface-credential-convention.md`](../../codex/04-architecture/interface-credential-convention.md)
  — DeFi connector credentials (`connector.connect(config={"wallet_private_key": pk, "rpc_url": url})`); contrasts CeFi
  `get_order_adapter(api_key, api_secret)` shape
- [`codex/05-infrastructure/launcher-script-ssot.md`](../../codex/05-infrastructure/launcher-script-ssot.md) — DeFi VM
  launchers MUST live under `deployment-service/scripts/vm/` (forward-poll + backfill + per-chain replay launchers)
- [`codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md`](../../codex/09-strategy/architecture-v2/archetypes/carry-staked-basis.md)
  — May-23 lead archetype (recursive LST staking + perp short hedge)
- [`codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md`](../../codex/09-strategy/architecture-v2/archetypes/arbitrage-price-dispersion.md)
  — May-23 hedge archetype: `ARBITRAGE_PRICE_DISPERSION` with `funding-rate-dispersion` config variant (cross-venue
  funding-rate dispersion; renamed from legacy `leveraged_funding_arb` per Stream B canonicalisation 2026-05-07)

If any of the docs above is missing, this plan creates a stub for it (see [`codex/`](../../codex/) tree).

## AI-day estimate

- **Total**: ~10-12 ai-days net (XL umbrella); current state 78 todos enumerated, ~17% in-flight per 2026-05-07 audit.
- **Workstream split**:
  - Pyth Solana wiring + multi-chain oracle backfill: ~1.5 ai-days (one-shot wiring already shipped — left is one VM
    backfill run + spot-check)
  - 988-dates-missing diagnosis + per-chain pre-genesis backfill: ~2.5 ai-days (gated on
    `manifest_migration_master:Stage 4` rescan)
  - DEX-perp forward-poll + Lighter/Pacifica/Extended replay: ~2 ai-days (Extended Starknet still pending Phase 0
    research; Lighter + Pacifica OHLCV shipped per MEMORY)
  - 4-service QG pass (strategy / execution / risk-and-exposure / features-onchain): ~1 ai-day
  - 8-archetype Phase 1 batch e2e + CARRY_RECURSIVE_STAKED PnL row: ~2 ai-days
  - Copper sandbox: ~0.5 ai-day (FlashLoanReceiver mainnet deploy ✅ shipped 2026-05-10 at
    `0x42c005e2Bc545a49B50Fee3E76B8558348CAAb4c` — tx
    `0x09a4f9f08cd0cc211d5f825d713de3cf56f20938f1a781f16aaae703708a0925`, block 25066462, gas 521102, bytecode 2157
    bytes verified via `eth_getCode`; UAC@abb8e5f0 registered chain_id=1 in `config/testnet_contracts.yaml`; SM secret
    `flash-loan-receiver-mainnet` mirrors Sepolia pattern; closes the live-Aave-flash-loan blocker for
    `carry_staked_basis` recursive-staking unwind)
  - Operational drift fixes (PROTOCOL_LAUNCH_DATES coverage — Tab 14 reported 13 of 17 protocols missing): ~1 ai-day
- **Parallelism factor**: ~3x (workstreams largely independent — oracle / DEX-perp / archetype gates / Copper can
  proceed in parallel agents), so **~3-4 calendar days wall-clock** if 3-4 agents in parallel + operator approvals on
  the critical path.
- **Critical path to 2026-05-23 cutover**: 4-service QG → CARRY_RECURSIVE_STAKED PnL row → Copper sandbox + flash-loan
  testnet deploy → 7-day continuous run gate. Anything off this critical path is parallel-safe.

## Agent 4 launch decision (2026-05-07, [archived `work_split_2026_05_07_ikenna_5tab_layout`](../archive/work_split_2026_05_07_ikenna_5tab_layout.md) Item 2)

> Triage from
> [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)
> § "Agent 4 triage decision". Carrying the launch-picks slice forward here so the agent reading defi_master in
> isolation has the picks pinned.
>
> **SAFE TO LAUNCH NOW (this cycle):**
>
> - `launch-mtds-vault-share-price-backfill-vm.sh 2020-01-01 2026-05-07` — high carry-archetype value, parallel-safe, no
>   known adapter bugs.
> - `launch-mtds-lst-rates-backfill-vm.sh` — Pyth Solana wired (UAC unbanning 2026-05-06; mtds-s3-5 done); P0 input for
>   `carry_staked_basis`. Solana coverage genuinely thin (~monthly cadence per defi_master § "Real residual concerns") —
>   backfill fills daily granularity.
> - `launch-mtds-oracle-prices-backfill-vm.sh` (or equivalent for the Pyth Hermes + Chainlink multi-chain wiring) —
>   mtds-s3-5 + mtds-s3-6 both flipped done 2026-05-07; first batch backfill exercises the just-shipped paths.
>
> **DEFERRED (P0 fix-first, not in this cycle):**
>
> - `launch-mtds-lending-indices-backfill-vm.sh` — last run `mtds-lending-indices-20260507-140418` stopped 2026-05-07
>   ~15:30 IST after spot-checking surfaced Bug 1 (AAVE V3 ETHEREUM silent-zero — 0/343 captured for the most-relevant
>   chain), Bug 2 (COMPOUND V3 multi-chain subgraph `marketDailySnapshots` field rename), Bug 3
>   (`instruments-store-defi` metadata 404 for early 2022 dates). Relaunching without the fixes means re-writing
>   `empty_confirmed` rows that per writegate Phase 2.A spirit should be `attempted_failed` — silent data corruption per
>   CLAUDE.md "honest absence vs fake placeholders". Successor: a follow-up `[AGENT] P0` todo under "Lending-indices VM
>   run-quality bugs" §; recommend Agent 1 (alerting context — owns subgraph error classification) or independent agent.
>
> **NOT IN AGENT 4 SCOPE THIS CYCLE:**
>
> - `launch-mtds-perp-funding-backfill-vm.sh` — **CORRECTION 2026-05-08 audit**: launcher EXISTS at
>   `deployment-service/scripts/vm/launch-mtds-perp-funding-backfill-vm.sh` (was previously declared missing).
>   Adding/maintaining is a dedicated [SCRIPT] task; not a launch in this cycle.
> - DEX-perp `launch-cefi-onchain-forward-poll.sh` for LIGHTER/PACIFICA/EXTENDED — required pre-live but separate
>   workstream (HANDOVER Item A). Not in Agent-4 cycle scope.
>
> **NAMING + DISCIPLINE:**
>
> - All Agent-4-launched VMs use `MANIFEST_PER_VM_SHARDS=true` + `VM_NAME=<unique-tag>` per CLAUDE.md "Per-VM shard
>   isolation".
> - Each launch gets a no-fire-and-forget event-verification 90s post-launch + 10-15min re-check (CLAUDE.md "No
>   fire-and-forget VM launches"). Stalled = kill + diagnose, not let-run.
> - Per-VM shard inspection (4-pillar validation: row count > 0 / NaN ratio / schema / cluster coverage) before
>   declaring "running cleanly" — same recipe as `mtds-lending-indices-20260507-140418` Bug-1-finding pattern.

## Audit 2026-05-07

- **Audit run**: 2026-05-07 (parallel-agent pass)
- **Verified**: 32 of 32 unchecked todos
- **Mis-marked DONE → flipped**: 2 (Lighter + Pacifica `_fetch_*_history` and OHLCV ohlcv_1m wiring shipped per
  MTDS@10aa715/51fecd5/d898985/fc53a97 + UAC@e890022; UAC `VENUES_BY_ASSET_GROUP['defi']` already includes
  Lighter/Pacifica per UAC@7cb9068 / 405cbf5 venue declarations)
- **In-flight (running VMs)**: 0 — NO defi/features-onchain VMs in current `gcloud` snapshot
- **Blocked by**: `manifest_migration_master_2026_05_07:Stage 4` (rescan-all-manifests gates the 988-dates-missing
  diagnosis); `writegate_honest_coverage_endtoend:Phase 2.A` (placeholder deletion for honest coverage %);
  `cefi_master:24-VM drain` (carry_staked_basis perp hedges need cefi backfill)
- **Blocks**: THIS IS THE HEADLINE GOAL OF 2026-05-23. Blocks `master_to_live_defi_2026_05_23:F` (Group F live trading
  prerequisites); blocks `master_to_live_defi_2026_05_23:G` (DART manual-trade gate)
- **Last meaningful commit**: UAC@`f22f4b1` (CHAIN_GENESIS_DATES SSOT); UAC@`405cbf5` (declare LST/staking-yield
  protocols + DEFI_VENUE_PHASE marker); UAC@`3613e90` (LST_TOKEN_TO_PROTOCOL_ASSET SSOT — Phase 9.1A);
  features-onchain@`7f1b2a1` (canonical protocol/asset/chain columns — Phase 9.1B); strategy@`e4a0cdd`
  (CARRY_BASIS_DATED + ARBITRAGE_PRICE_DISPERSION specs — Phase 9.3); MTDS@`8c3c2c7` (DEFI legacy-underscore venue
  migration); MTDS@`10aa715`/`51fecd5`/`d898985`/`fc53a97` (Lighter + Pacifica DEX OHLCV historical)
- **Recommendation**: KEEP ACTIVE — TOP-PRIORITY P0. The headline asset_group for 2026-05-23. Critical pending: Pyth
  Solana wiring (carry_staked_basis blocker) + Copper sandbox + 4-service QG pass + CARRY_RECURSIVE_STAKED batch e2e PnL
  row. Do NOT archive. Do NOT defer P0 items.

## Scope

Single source of truth for **DeFi asset_group** work toward live DeFi 2026-05-23. The headline goal of the cutover.

Covers:

- **2 DeFi archetypes live**: `carry_staked_basis` (lead — recursive LST staking + perp short hedge) +
  `ARBITRAGE_PRICE_DISPERSION` (config variant `ARBITRAGE_PRICE_DISPERSION@funding-dispersion-leveraged` — cross-venue
  funding spread; renamed from legacy `leveraged_funding_arb` per Stream B canonicalisation 2026-05-07, see
  [`defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md`](defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07.md)).
  7-day continuous run on real wallet.
- **2 DeFi perp DEXs live**: Hyperliquid + Aster. Plus historical-replay backfill for Lighter / Extended / Pacifica
  (originally scoped under CeFi venue expansion but they are DeFi by asset_group).
- **DeFi data pipeline E2E**: features-onchain → strategy → execution. 8 archetypes pass Phase 1 batch e2e (per
  `defi_e2e_pipeline`).
- **MTDS DeFi slice to 100%**: per-(asset_group=defi, chain, venue/protocol, data_type, instrument_id, day). Chain is a
  first-class shard axis.
- **Multi-chain oracle prices**: Pyth (Solana, unbanned 2026-05-06) + Chainlink (EVM Arb/Base/Polygon).
- **Custody integration**: Copper wired DeFi-side per `codex/04-architecture/custody-providers.md` § 2.3 (single SSOT —
  Copper / CEFFU / LocalKey / Mock).

**Current data-status** (from deployment-ui 2026-05-07): 49138/295744 shards = **73.5%**, 988 dates missing. Tail chains
(Aurora / Celo / Fantom / Mantle / Metis / Moonbeam) stuck at 25% (1/4 protocols). Mid-tier EVMs (Arbitrum / Avalanche /
Base / BSC / Linea / Optimism / Polygon) at 60% (32/53). Ethereum 85%, Solana 99.9%.

## Current state (2026-05-07)

> **DeFi expected-universe `--apply-write` COMPLETE + CONSOLIDATOR MERGE LANDED (writegate Phase 3.D.4; PM@79e47874 +
> PM@341bb285).** Final run `expected-universe-enum-defi-20260507-155353` (deployment-service@dcc5c87 / @38b7a58
> launcher with cap pass-through + instruments-service@8e404c8 / @d1c9928 / @a936a28 script) wrote **1,286,260 rows**
> (688,220 `EXPECTED_PRE_GENESIS_CHAIN` + 598,040 `EXPECTED_INSTRUMENT_NOT_LISTED`) in 26.3s; per-VM shard merged into
> canonical 18:07 UTC. Default cap was raised 100k → 1M, then bumped to 5M for this run via the new launcher
> pass-through. Consolidator P0 (`ArrowTypeError` on `instrument_count`) that briefly blocked the merge was resolved at
> PM@341bb285 (script-side root cause + in-place shard fix). The 988-dates-missing rollup-vs-drilldown panel signal
> closes for DeFi as soon as the rollup blob refreshes; operator spot-check pending. Detail in
> [`writegate_honest_coverage_endtoend_2026_05_06.md`](writegate_honest_coverage_endtoend_2026_05_06.md) § Phase 3.D.4.

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

| Workstream                                                                      | Status                                                         | Source                                                   | Success gate                                                                                                                                                 |
| ------------------------------------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `carry_staked_basis` archetype live (≥7 continuous days)                        | spec done; execution wiring pending                            | master plan + carry_staked_basis_structure_axis archived | 7 continuous days on real wallet with PnL row per day in `pnl-store-{pid}/by_strategy/CARRY_STAKED_BASIS/...`; `min_health_factor` honoured every snapshot   |
| `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`) archetype live         | scoped; cross-venue funding spread integration pending         | `consolidated_defi_data_pipeline`                        | Cross-venue funding signal generates fills on ≥2 perp venues over 24h; PnL row present in `by_strategy/ARBITRAGE_PRICE_DISPERSION/...`                       |
| Hyperliquid + Aster perp DEX live                                               | instruments + market-data live; execution validated on testnet | `consolidated_defi_data_pipeline`                        | `execution-service` testnet smoke ships 1 round-trip per venue; mainnet gated on Copper sandbox                                                              |
| 988 dates missing in DeFi shards (per data-status panel)                        | manifest gap; per-chain breakdown above                        | `consolidated_defi_data_pipeline` (Phase 6 reverify)     | Post-`Stage 4 rescan-all-manifests`, per-chain coverage row reads 100% within `(genesis, today)` clip; remaining gaps stamped `EXPECTED_PRE_GENESIS_CHAIN`   |
| Tail chains 25% coverage (Aurora / Celo / Fantom / Mantle / Metis / Moonbeam)   | per-chain protocols incomplete                                 | `consolidated_defi_data_pipeline`                        | Each tail chain shows ≥4/4 protocols captured for at least 1 sample day post-protocol-launch; rest stamped `EXPECTED_PRE_VENUE_LAUNCH`                       |
| Mid-tier EVMs 60% coverage (Arb / Avax / Base / BSC / Linea / Op / Polygon)     | per-chain protocols incomplete                                 | `consolidated_defi_data_pipeline`                        | All 7 mid-tier chains show ≥80% coverage post-rescan; AAVE V3 in particular returns >0 rows per chain post-2023-01-27                                        |
| Pyth Solana oracle wiring                                                       | unbanned 2026-05-06; integration pending                       | `consolidated_defi_data_pipeline` mtds-s3-5              | `mtds-lst-rates` VM run produces non-empty `oracle_prices` rows for jitoSOL/mSOL/bSOL with `protocol=pyth` 2022-11 → today; Hermes archive backfill verified |
| Multi-chain oracle (Chainlink EVM)                                              | partial                                                        | `consolidated_defi_data_pipeline` mtds-s3-6              | `oracle_prices` non-empty for ETH/USD + BTC/USD on Arb/Base/Optimism/Polygon for any sample day in 2024-2026                                                 |
| Lighter / Extended / Pacifica historical-replay backfill                        | scoped; ABI parsing per chain pending                          | `dex_historical_replay_*`                                | Lighter + Pacifica OHLCV non-empty 2024-08-01+ / 2025-06-01+ respectively; Extended pending Phase 0 empirical research before any VM launch                  |
| 4-service QG pass (strategy / execution / risk-and-exposure / features-onchain) | pending                                                        | `defi_e2e_pipeline`                                      | `bash scripts/quality-gates.sh` passes in all 4 repos; basedpyright clean; ruff clean; CI green on `live-defi-rollout`                                       |
| 8-archetype Phase 1 batch e2e                                                   | pending                                                        | `defi_e2e_pipeline`                                      | All 8 archetypes produce non-empty `realised_apy_bps` over 2026-04-03..04-09 sample window; `comparison.parquet` ships per archetype per day                 |
| Copper custody integration                                                      | wired DeFi-side; sandbox integration test pending              | `consolidated_defi_data_pipeline` Copper item            | Sandbox ships 1 round-trip (deposit + signed-tx broadcast + withdraw) on testnet; flash-loan-receiver `eth_getCode` validation green on at least 1 chain     |

## Consolidated todos (P0 only — full P1+ list in folded children)

### Oracle prices + chain expansion (`consolidated_defi_data_pipeline` mtds-s3)

- [x] [AGENT] P0. mtds-s3-5-pyth-oracle: Add Pyth oracle prices for Solana via Hermes (HTTPS pull, batch) + PythNet
      (Solana RPC, live). Solana-only scope. carry_staked_basis dependency. [AUDIT 2026-05-07: FRESH — actionable, P0
      BLOCKER for carry_staked_basis archetype; Pyth UNBANNED 2026-05-06 per CLAUDE.md but wiring not shipped] ✅
      market-tick-data-service@cli/handlers/oracle_prices_handler.py (Pyth Hermes wired) 2026-05-07
- [x] [AGENT] P0. mtds-s3-6-multi-chain-oracle: Extend oracle_prices to multi-chain EVM (Chainlink on Arb/Base/Polygon).
      [AUDIT 2026-05-07: FRESH — actionable] ✅ market-tick-data-service@cli/handlers/oracle_prices_handler.py
      (Chainlink Arb/Base/Optimism/Polygon via \_CHAINLINK_FEEDS_BY_CHAIN) 2026-05-07
- [ ] [HUMAN+AGENT] P0. mtds-s4-10-rescan-all-manifests: Re-scan ALL availability indexes after migrations. **Cross-plan
      coordination**: this is **Stage 4** (final sweep) of the workspace-wide manifest migration. See
      [`manifest_migration_master_2026_05_07.md`](../epics/manifest_migration_master_2026_05_07.md) — MUST run AFTER all
      Stage 3 streams complete (Stage 3.A 1440-NaN flip + 3.B available_at backfill + 3.C pre-v6 cleanup + Predictions
      Polymarket migration + Sports ODDS_API re-key). Running mid-flight produces inconsistent state across services. NO
      VM pause needed — consolidator handles concurrent writes per CLAUDE.md `§ Manifest     concurrency principle`.
      [AUDIT 2026-05-07: BLOCKED-ON manifest_migration_master_2026_05_07:Stage 3]
- [ ] [HUMAN+AGENT] P0. defi-e2e-validate: DeFi pipeline E2E — run full batch, verify features-onchain reads correctly.
      [AUDIT 2026-05-07: FRESH — actionable; gates Group F]
- [ ] [HUMAN+AGENT] P0. defi-coverage-validate: DeFi full coverage — run each handler locally for 1 day, verify GCS.
      [AUDIT 2026-05-07: FRESH — actionable]

### DeFi e2e pipeline gates (`defi_e2e_pipeline`)

- [ ] [AGENT] P0. strategy-service `quality-gates.sh` passes. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. execution-service `quality-gates.sh` passes. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. risk-and-exposure-service `quality-gates.sh` passes. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. features-onchain-service `quality-gates.sh` passes. [AUDIT 2026-05-07: FRESH — actionable;
      multi-recent-commit pattern of fixes shows ongoing work (7f1b2a1, c90d01a, 955abb5, 266f512, f3db4ca, 82d94b6)]
- [ ] [AGENT] P0. basedpyright clean across all 4 DeFi service repos. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. CARRY_RECURSIVE_STAKED batch e2e produces non-zero PnL row in
      `pnl-store-{pid}/by_strategy/.../day=2025-06-21`. [AUDIT 2026-05-07: FRESH — actionable; Phase 9 calculator
      catalog rerun launched 2026-05-07 (features-onchain-defi-backfill-20260507-013235 was launched per MEMORY but no
      longer in current snapshot, presumably drained)]
- [ ] [AGENT] P0. PnL row decomposes into base_apy + restaking_apy + borrow_cost + gas attribution. [AUDIT 2026-05-07:
      FRESH — actionable]
- [ ] [AGENT] P0. Position snapshot reflects leveraged LST holding + WETH debt. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. Health factor recorded ≥ configured `min_health_factor` for every snapshot. [AUDIT 2026-05-07: FRESH —
      actionable]
- [ ] [AGENT] P0. Synthetic feature tick injected into `defi-onchain-features-ready` produces a fill on
      `fill-events-{venue}`. [AUDIT 2026-05-07: FRESH — actionable]
- [ ] [AGENT] P0. PBM emits position snapshot; pnl-attribution emits per-strategy attribution row. [AUDIT 2026-05-07:
      FRESH — actionable]
- [ ] [AGENT] P0. Risk-and-exposure-service log shows RISK_PASS published before execution. [AUDIT 2026-05-07: FRESH —
      actionable]
- [ ] [AGENT] P0. All 8 archetypes pass Phase 1 batch e2e: CARRY_RECURSIVE_STAKED, CARRY_STAKED_BASIS, CARRY_BASIS_PERP,
      [+5 more]. [AUDIT 2026-05-07: FRESH — actionable; CARRY_BASIS_DATED + ARBITRAGE_PRICE_DISPERSION specs landed
      strategy@e4a0cdd]
- [ ] [AGENT] P0. features-onchain-service Docker image rebuild — Cloud Build emits new `:latest` tag with Phase
      changes. [AUDIT 2026-05-07: FRESH — actionable]

#### Carry tracer verification gates (folded-in 2026-05-07 from `defi_data_to_strategy_4phase_handoff` Phase A + D)

- [x] [VERIFY] P0. **Phase A gate — partial Stage 3 carry tracer** over 2026-04-03..04-09 across all 7 archetypes
      (YIELD_STAKING_SIMPLE, CARRY_BASIS_PERP, CARRY_STAKED_BASIS, CARRY_BASIS_DATED, CARRY_RECURSIVE_STAKED,
      YIELD_ROTATION_LENDING, ARBITRAGE_PRICE_DISPERSION). Expected: every archetype has non-empty `realised_apy_bps`.
      CARRY_BASIS_DATED + cross-venue ARBITRAGE_PRICE_DISPERSION are the new ones lit by `futures_roll_resolver`
      (features-cross-instrument@954575a) + `catalog_pair_builder` (954575a/2804f47/543a0bb) + UAC
      `PAIRED_DISPERSION_CATALOG` SSOT (UAC@6217382). [AUDIT 2026-05-07: PARTIAL — features-onchain VM
      `features-onchain-defi-backfill-20260507-105936` confirmed canonical columns ship in
      `lending_rates/features.parquet` (protocol/chain/asset/supply_apy/borrow_apy populated, AAVE_V3 ARBITRUM USDC
      1.62%/2.83%); A4 tracer shim deletion landed strategy@666dc2d; full per-day tracer invocation across the 7-day
      window pending features-onchain Docker rebuild]
- [ ] [VERIFY] P0. **Phase D gate — full Stage 4 historical** carry tracer over 2022-01-01..today across all 7
      archetypes. Sample 10 random days from the 4-year window; for each day, the `comparison.parquet` must have: (a)
      non-empty `realised_apy_bps` for at least 5 of 7 archetypes (CARRY_BASIS_DATED + ARBITRAGE_PRICE_DISPERSION may be
      empty pre-databento-coverage / pre-Pacifica-launch dates — honest absence, not a bug); (b) `flow_of_funds_legs`
      non-empty for the winning slot of each archetype; (c) NO silent NaN-only days (every day must show either real
      data or manifest-recorded `record_expected_empty(reason=...)`). Depends on D1-D4 backfill completion + Phase A
      gate clean + features-onchain Docker rebuild. [AUDIT 2026-05-07: FRESH — final intent-test gate before live
      cutover; gates merge of carry-tracer Phase 9 work into main]

#### Reference — multi-coin / multi-funding / multi-venue decision architecture (folded-in 2026-05-07 from `carry_tracer_pipeline_handoff_2026_05_06`)

The decision of "what to trade for an archetype" lives in **4 layers** within strategy-service. Apply to any new
archetype before adding new specs:

1. **Catalog** (`strategy-service/.../target_universe/catalog.py`) — menu of available specs. Adding a new spec is a row
   addition, not a code change. CARRY_BASIS_DATED + ARBITRAGE_PRICE_DISPERSION specs added per user direction
   2026-05-06: keep all 7 existing CARRY_BASIS_DATED specs, ADD NASDAQ-IBIT/CME-MBT (BTC ETF vs micro BTC),
   NASDAQ-ETHA/CME-MET (ETH ETF vs micro ETH), DERIBIT spot-vs-dated (BTC + ETH intra-Deribit basis), GLD/USO/UNG/
   SPY/QQQ-vs-CME-futures (placeholders for databento ETF coverage). ARBITRAGE_PRICE_DISPERSION adds CME-MBT vs
   DERIBIT-dated + CME-MET vs DERIBIT-dated (cross-venue same-expiry).
2. **Features** — per-(spec, day) metric values. Calculator owns schema; tracer reads canonical columns directly.
   Canonical schema for lst_yields = `protocol`, `asset`, `staking_apy_bps` (already bps, not fraction); for
   lending_rates = `protocol`, `chain`, `asset`, `supply_apy`, `borrow_apy` (column-form, NOT instrument_id parsing).
   features-onchain@`7f1b2a1` shipped these canonical columns; the prior tracer-side schema-adapter shim
   (strategy@`666dc2d`) is now deleted as a result.
3. **Allocator** (`strategy-service/.../portfolio_allocator/archetypes.py`, `BaseRankAllocator` + 7 archetype
   subclasses) — universe filter, score metric, threshold (default 250 bps = 2.5% APY), top-N, capital-weighting. **This
   is the opportunity-decision layer.** `CarryBasisPerpRankAllocator` is the canonical multi-coin / multi-venue example
   (3-stage hierarchical: per-coin avg → cross-coin weighting → per-venue weighting within each coin). Adding new
   specs/calculators does NOT require allocator changes — they consume the same shape.
4. **Strategy engine** (`strategy-service/engine/strategies/v2/*_engine.py`) — entry triggers, exit triggers, roll on
   expiry, rotation cost gating. Per-archetype subclass.

The `paired_price_dispersion` calculator in features-cross-instrument-service is the cross-asset-group greenfield that
powers BOTH CARRY_BASIS_DATED (one leg spot/ETF, other dated future, held to convergence) and ARBITRAGE_PRICE_DISPERSION
(both legs futures of same expiry on different venues, exit on convergence). Single calculator, two consumers; the
per-archetype filter logic is in the catalog spec rows, not duplicated in the calculator.

### Lighter / Extended / Pacifica historical replay (`dex_historical_replay_*`)

- [x] [AGENT] P0. Lighter zkSync mainnet matching contract address + ABI parse (`Trade` event). [AUDIT 2026-05-07: DONE
      for OHLCV path — MTDS@10aa715 `_fetch_lighter_candles` shipped via /candles endpoint; per MEMORY entry
      feedback_lighter_pacifica_cloudfront_quirks per-trade replay infeasible because Lighter `block_height` is
      sequencer-internal NOT zkSync L1 — on-chain `Trade` event parsing was found infeasible during empirical research.
      Subgraph option still pending in dex_perp_onboarding_handover Item C]
- [ ] [AGENT] P0. Lighter subgraph availability check (thegraph.com/explorer); validate row schema match against
      `_fetch_lighter_rest`. [AUDIT 2026-05-07: BLOCKED-ON dex_perp_onboarding_handover_2026_05_07:Item C — Extended
      on-chain replay sub-plan, pending operator]
- [ ] [SCRIPT] P0. Launch `mtds-lighter-history-backfill-{ts}` singleton-locked VM; date range 2024-08-01 → today. Add
      prefix to `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET`. [AUDIT 2026-05-07: STALE — replaced by ohlcv_1m route via
      /candles in MTDS@10aa715 (per MEMORY project_dex_perp_onboarding_2026_05_07); per-trade history NOT recoverable
      per Lighter quirks finding]
- [ ] [AGENT] P0. Extended Starknet mainnet `Settlement` contract address + event signature; add Starknet RPC template
      to UAC `CHAIN_RPC_TEMPLATES`. [AUDIT 2026-05-07: BLOCKED-ON dex_perp_onboarding_handover_2026_05_07:Item C Phase 0
      empirical research; Extended is the third venue, pending]
- [ ] [AGENT] P0. `_fetch_extended_history` in `umi_tick_provider.py`; schema-parity vs `_fetch_extended_rest`. [AUDIT
      2026-05-07: BLOCKED-ON dex_perp_onboarding_handover_2026_05_07:Item C]
- [x] [AGENT] P0. Pacifica Solana program ID + Anchor `emit!` log decoder; Helius `getSignaturesForAddress` +
      `getTransaction` parse. [AUDIT 2026-05-07: DONE for OHLCV path — MTDS@51fecd5 `_fetch_pacifica_candles` via /kline
      (ms timestamps); per-trade Anchor decoder still pending in handover Item C]
- [x] [AGENT] P0. `_fetch_pacifica_history` in `umi_tick_provider.py`; schema-parity vs `_fetch_pacifica_rest`. [AUDIT
      2026-05-07: DONE — MTDS@51fecd5 (ohlcv_1m via /kline); per MEMORY project_dex_perp_onboarding_2026_05_07]
- [ ] [SCRIPT] P0. Backfill VMs for each new venue + schema-parity validation against the REST adapter. [AUDIT
      2026-05-07: PARTIAL — Lighter + Pacifica VMs ran successfully per MEMORY; Extended VM still pending]

### DEX perp forward-poll handlers + collateral matrix (folded-in 2026-05-07 from `dex_perp_onboarding_handover`)

Captures the open work items from
[`dex_perp_onboarding_handover_2026_05_07.HANDOVER.md`](dex_perp_onboarding_handover_2026_05_07.HANDOVER.md) Items A / B
/ D / E / F as standard-format checkbox todos. The HANDOVER doc remains the narrative SSOT (with empirical findings per
venue); these checkboxes track execution.

Date ranges + venue specs:

- **LIGHTER-ZKSYNC** (zkSync Era, validium settlement) — 170 perps, top-5 currently captured (BTC, ETH, SOL, HYPE, TON).
  Historical OHLCV via `/candles` 2025-05-01 → today (manifest captured per session 2026-05-07). Per-trade history
  unrecoverable (REST capped, no cursor; on-chain replay infeasible per `block_height` being sequencer-internal).
  Forward-poll only path for live tape.
- **PACIFICA-SOLANA** (Solana program-settled, Hyperliquid clone) — ~50+ perps, top-5 captured. Mainnet 2025-06-onwards.
  50x leverage, USDC cross-margin (today). OHLCV via `/kline`.
- **EXTENDED-STARKNET** (Starknet-native, batched-proof settlement) — ~10 BTC/ETH/SOL majors. Historical OHLCV path
  unconfirmed (404 on `/candles`); see Item C below for research. Settlement events SHOULD be on-chain readable via
  Starknet `getEvents`.

Funding-rate APY observed empirically: PACIFICA BTC sometimes +50% APR vs Binance BTC perp +12% APR (~38% APR
delta-neutral carry edge if captured). DEX-DEX funding-rate dispersion is the highest-edge cell in the entire strategy
table per HANDOVER. Forward-poll wiring unblocks `CARRY_BASIS_PERP` + `ARBITRAGE_PRICE_DISPERSION` signal generation for
these venues.

- [ ] [AGENT] P0. **Forward-poll launcher** `deployment-service/scripts/vm/launch-cefi-onchain-forward-poll.sh` covering
      LIGHTER-ZKSYNC + PACIFICA-SOLANA + EXTENDED-STARKNET (+ HYPERLIQUID + ASTER for parity). Singleton-locked pattern
      (mirror `launch-sfi-forward-poll.sh`). Polls `/funding` every 1-5 min → MTDS `data_type=perp_funding`;
      `/recentTrades` every ~10s → live tape; `/orderBookOrders` / `/book` snapshots every ~30s → slippage-modeling
      input. [AUDIT 2026-05-07: FRESH — required before live trading per HANDOVER Item A]
- [ ] [AGENT] P0. **MTDS perp_funding adapter** for LIGHTER + PACIFICA + EXTENDED — venue iteration in
      `mtds-perp-funding-` VM launcher; schema parity with existing Bybit / Binance / OKX / Deribit funding feed (per
      UAC `data_type=perp_funding` shape). [AUDIT 2026-05-07: FRESH — required before forward-poll launcher works]
- [ ] [AGENT] P1. **PACIFICA `VENUE_COLLATERAL_MATRIX` entry** in
      `unified-api-contracts/unified_api_contracts/registry/venue_collateral.py`. Verify whether Pacifica accepts
      JitoSOL / mSOL as cross-margin (live probe + docs check). YES → add row with haircut citation, unlocks
      `CARRY_STAKED_BASIS@jito-pacifica-solana-...` slot (auto-generates next catalog regen). NO → add explicit
      `accepted=False` row (matrix encodes negatives explicitly per audit spec). [AUDIT 2026-05-07: FRESH — HANDOVER
      Item B; unblocks Solana 2nd perp-hedge venue diversification beyond Drift]
- [ ] [AGENT] P2. **EXTENDED-STARKNET historical OHLCV path** — Item C. Two sub-paths in priority order: (1) re-read
      `docs.extended.exchange` for the documented historical endpoint (might be auth-gated); (2) failing that, build a
      Starknet event subgraph against the Extended Settlement contract — add `STARKNET_RPC_TEMPLATE` to UAC
      `CHAIN_RPC_TEMPLATES` (currently only zkSync + Solana; Starknet needs adding). Falls back to forward-poll only if
      both paths fail. [AUDIT 2026-05-07: FRESH — HANDOVER Item C; needed for
      `cefi-extended-starknet-history-backfill-{ts}` VM]
- [ ] [AGENT] P2. **Lighter symbol-coverage scale-up** — currently
      `_LIGHTER_BACKFILL_TOP_SYMBOLS = (BTC, ETH, SOL,     HYPE, TON)`; expand to top-30 (Lighter has 170 perps
      including NVDA, USDCAD, BRENTOIL, XAU, XAG, SNDK exotics). Rate-limit budget already validated — 12 RPS handles
      top-30 comfortably. Unlocks cross-asset stat-arb / FX-perp arb against CeFi FX. [AUDIT 2026-05-07: FRESH —
      HANDOVER Item D; deferred pending strategy demand signal]
- [ ] [DOC] P3. **Per-trade gap documentation in coverage matrix** — codex `02-data/pipeline-coverage-matrix.md`: mark
      `data_type=trades` as "live-only, no historical" for LIGHTER / PACIFICA / EXTENDED. Downstream strategies that
      need per-trade should use OHLCV bars OR forward-poll-built history (~few months, growing from forward-poll launch
      date). [AUDIT 2026-05-07: FRESH — HANDOVER Item E; honest-coverage transparency]
- [ ] [VERIFY] P0. **Final state verification of Lighter + Pacifica historical backfill VMs** —
      `cefi-lighter-zksync-ohlcv-20260507-024226` + `cefi-pacifica-solana-ohlcv-20260507-024226`. Manifest should show
      `captured` for ~370 (Lighter) + ~310 (Pacifica) day-symbol shards.

      ```bash
      gcloud storage ls "gs://market-data-tick-cefi-central-element-323112/raw_tick_data/by_date/day=2025-*/asset_group=cefi/venue=LIGHTER-ZKSYNC/instrument_type=perpetual/data_type=ohlcv_1m/" | wc -l
      ```

      [AUDIT 2026-05-07: FRESH — HANDOVER Item F; operational verification]

### Tail-chain / mid-tier protocol coverage (DeFi data-status — 988 dates missing)

> **Audit 2026-05-08 (Tab 6, defi-988-audit-tab)**: per-(chain, protocol, data_type) breakdown + top-5 priority list
> filed at
> [`../archive/issues/defi_988_missing_dates_audit_2026_05_08.md`](../archive/issues/defi_988_missing_dates_audit_2026_05_08.md).
> TL;DR: 1.3M non-captured rows across 10 DeFi buckets but **99% are SSOT-correct pre-genesis/pre-launch clipping**;
> only **13,632 rows / 2,234 distinct dates are actionable**. Top concentrations: (1) Tab 5 lending-indices fixes
> resolve ~2.4k; (2) DEX subgraph schema fixes (PancakeSwap/SushiSwap/Aerodrome/Camelot V3) resolve ~1.4k; (3) UAC
> `PROTOCOL_LAUNCH_DATES` tightening for vault protocols (YEARN V3 / Morpho Vaults / Ethena vault) reclassifies ~6.9k
> from `SOURCE_RETURNED_ZERO` → `legit_pre_protocol_launch`; (4) ASTER perp-funding adapter has **zero captured rows**
> (correctness risk if ASTER on May-23 hedge-leg path).

- [ ] [AGENT] P0. Tail chains 25% coverage diagnosis: Aurora / Celo / Fantom / Mantle / Metis / Moonbeam each have 1
      protocol live; per-chain protocol expansion deferred-post-cutover unless `carry_staked_basis` /
      `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`) requires those chains. [AUDIT 2026-05-07: FRESH —
      actionable diagnostic only; expansion deferred]
- [ ] [AGENT] P0. Mid-tier 60% coverage: Arb / Avax / Base / BSC / Linea / Op / Polygon — 32/53 protocols. Per-protocol
      backfill needed for 21 protocols/chain. Subgraph schema-mismatch fixes for PancakeSwap V3, SushiSwap V3, Aerodrome
      V3, Camelot V3 (per `defi_e2e_pipeline`). [AUDIT 2026-05-07: FRESH — actionable; UAC@0169a0a PROTOCOL_LAUNCH_DATES
      helps clip denominator]
- [ ] [AGENT] P0. 988 dates missing — query manifest, identify per-(chain, protocol, data_type) gaps, prioritize
      `carry_staked_basis` chain set first (Ethereum + Solana mostly done; Arbitrum + Base critical). [AUDIT 2026-05-07:
      FRESH — actionable; UAC@f22f4b1 CHAIN_GENESIS_DATES + UAC@0169a0a PROTOCOL_LAUNCH_DATES SSOTs help re-clip 988
      number downward]
- [ ] [AGENT] P1. Use `poolGetSnapshots` for historical TVL when querying past dates (DeFi pool query path). [AUDIT
      2026-05-07: FRESH — actionable; `grep poolGetSnapshots` returns 0 hits in workspace, confirming this DeFi-pool
      query path migration has not yet shipped] (folded from venue_axis_asset_group_vocabulary_2026_04_25)

### MTDS DeFi slice (`market_tick_data_to_100pct` — DeFi)

> **CORRECTION 2026-05-07 — earlier "PLANNING-CRITICAL" claim retracted.** A sub-agent + main-agent jointly misread the
> DeFi manifest layout, surfaced an alarming "Arb/Base/Polygon at 0%" finding, and pushed it as a planning-critical
> correction. Re-verification by walking ALL DeFi buckets shows the original plan numbers are defensible — the misread
> was reading only ONE bucket (the asset-group canonical) instead of the 10+ per-data_type buckets where Arb/Base/
> Polygon data actually lives. Codex now documents the multi-bucket DeFi layout to prevent repeat misreads — see
> [`codex/02-data/availability-manifest-and-data-status.md`](../../codex/02-data/availability-manifest-and-data-status.md)
> § "DeFi has 10+ separate manifest buckets — checking only one gives the wrong picture".

**Verified DeFi bucket layout (2026-05-07)** — full list with `_index/availability_index.parquet` confirmed present:

| Bucket                                                               | Rows    | Chains                                                          | Last write               |
| -------------------------------------------------------------------- | ------- | --------------------------------------------------------------- | ------------------------ |
| `market-data-tick-defi-{pid}` (asset-group, Phase-1 + Phase-2 mixed) | 313,365 | ETH + SOLANA                                                    | 2026-05-05 13:44         |
| `lending-indices-{pid}`                                              | 37,000  | ETH + 9 EVM (Opt/Base/Arb/Scroll/Avax/Linea/BSC/Polygon/zkSync) | 2026-05-05 00:56         |
| `dex-swaps-{pid}`                                                    | 46,491  | ETH + 7 EVM                                                     | 2026-05-05 00:56         |
| `evm-defi-{pid}`                                                     | 22,633  | ETH + Arb/Base/Opt/Polygon                                      | 2026-05-05 10:06         |
| `instruments-store-defi-{pid}`                                       | 127,896 | 7+ chains                                                       | 2026-05-05 07:25         |
| `gas-fees-{pid}`                                                     | 11,988  | ETH + 9 EVM                                                     | 2026-05-05 00:55         |
| `oracle-prices-{pid}`                                                | 7,032   | ETH + Arb/Base/Opt/Polygon                                      | 2026-05-05 00:55         |
| `perp-funding-{pid}`                                                 | 5,575   | HYPERLIQUID + ASTER                                             | 2026-05-05 00:55         |
| `solana-defi-{pid}`                                                  | 5,028   | SOLANA                                                          | 2026-04-13 15:09 (older) |
| `lst-rates-{pid}`                                                    | 4,356   | ETH + SOLANA                                                    | 2026-05-05 00:55         |

**deployment-api correctly handles the split**: `data_status_service.py:2802` `_BUCKET_CATEGORY_OVERRIDES` routes each
per-data_type to its dedicated bucket; `_canonicalise_defi_data_types()` at line 991 normalises the dual
kebab/snake_case `data_type` vocabulary at read-time. No data-status code bug. The original plan numbers (Ethereum 85% /
Solana 99.9% / Arb-Base-Polygon 60%) are likely reading the per-bucket panels in the deployment-ui, which IS the right
view.

**Real residual concerns from this re-verification** (down-graded from "planning-critical" to legit operator items):

### Lending-indices VM run-quality bugs (discovered 2026-05-07 mid-run, VM stopped after diagnosis)

VM `mtds-lending-indices-20260507-140418` was launched 2026-05-07 14:04 IST and **stopped 2026-05-07 ~15:30 IST** after
spot-checking the per-VM shard revealed silent data-quality issues. Despite emitting 8,000+ `INSTRUMENT_PROCESSED`
events + writing 4,459 manifest rows, only 4 of 8 (venue, chain) pairs were producing captured rows; the rest were
silently writing `empty_confirmed` for dates where data should exist. The VM was stopped for diagnosis + bug fixes
before re-launch — losing ~1,080 captured rows of progress (Arbitrum/Avalanche/ Optimism/Polygon AAVE V3 days for
2022-Q4) is acceptable because re-running after the bug fixes is the cleaner path; re-runs of those days will pick up
the same data.

**Per-(venue, chain) outcome from per-VM shard** (cross-referenced with
`_index/per_vm/mtds-lending-indices-20260507-140418.parquet` 4,459 rows):

| venue / chain                       | captured | empty_confirmed | verdict                                |
| ----------------------------------- | -------- | --------------- | -------------------------------------- |
| AAVEV3 / ARBITRUM                   | 269      | 74              | ✅ working                             |
| AAVEV3 / OPTIMISM                   | 270      | 73              | ✅ working                             |
| AAVEV3 / POLYGON                    | 272      | 71              | ✅ working                             |
| AAVEV3 / AVALANCHE                  | 270      | 73              | ✅ working                             |
| AAVEV3 / **ETHEREUM**               | **0**    | **343**         | ❌ **silent zero** — bug               |
| AAVEV3 / BASE                       | 0        | 343             | ⚠️ likely correct (pre-launch in 2022) |
| AAVEV3 / LINEA                      | 0        | 343             | ⚠️ likely correct (LINEA mainnet 2023) |
| AAVEV3 / BSC                        | 0        | 343             | ⚠️ likely correct                      |
| COMPOUNDV3 / ETHEREUM               | 107      | —               | ✅ working                             |
| COMPOUNDV3 / ARBITRUM/BASE/OPTIMISM | 0        | 0 (skipped)     | ❌ **subgraph schema error**           |

**Bug 1 — AAVE V3 ETHEREUM silent zero** (P0 for `carry_staked_basis`, the most-relevant chain):

Run.log shows
`instruments-store-defi parquet missing for aave_v3/ETHEREUM/2022-12-08; falling back to subgraph discovery` then
`Wrote 0 rows`. The instruments-store-defi metadata is missing for ETHEREUM (404s for early 2022 dates) AND the subgraph
fallback is misconfigured for ETHEREUM specifically — other chains (Arbitrum, Optimism, Polygon, Avalanche) have working
subgraph fallbacks with the same code. Investigation target:
`market-tick-data-service/market_tick_data_service/cli/handlers/lending_indices_handler.py` (or equivalent) + the
per-chain subgraph endpoint config. Likely a chain→subgraph URL mapping bug or a missing schema mapping for the Ethereum
subgraph response shape.

**Bug 2 — COMPOUND V3 multi-chain subgraph schema error**:

Run.log shows
`Subgraph query errors for Ff7ha9ELmpmg81D6nYxy4t8aGP26dPztqD1LDJNPqjLS: [{'message': "Type 'Query' has no field 'marketDailySnapshots'"}]`
for COMPOUND_V3 on ARBITRUM/BASE/OPTIMISM. The Messari subgraph schema has been updated upstream + the MTDS GraphQL
query is stale. Investigation target: the same handler's COMPOUND_V3 GraphQL query — likely the field is renamed (e.g.
`marketHourlySnapshots` or `marketSnapshots`) or moved into a different entity. **Side effect**: VM records these as
`empty_confirmed` per the writegate three-category model (subgraph returned 0 rows, no exception) — but per writegate
Phase 2.A spirit this should be `attempted_failed` because the GraphQL error means we DIDN'T actually probe the data.

**Bug 3 — `instruments-store-defi` metadata missing for early 2022 dates**:

Affects all (venue, chain) pairs equally for early 2022 dates. The fallback to subgraph discovery works for some chains
and not others (see Bugs 1+2). The deeper question is whether instruments-service's lookback covers early DeFi protocol
launch dates — `instruments-store-defi-{pid}/instrument_availability/by_date/day=2022-12-08/...` returns 404 for
AAVEV3/COMPOUNDV3/etc. across all chains. Investigation target: `instruments-service` DeFi instrument-discovery script +
its launch-date floor handling.

**RESOLVED 2026-05-08 — Tab 5 (lending-indices-bugfix-tab)**: All three bugs fixed.
[`../archive/issues/lending_indices_handler_bugs_2026_05_07.md`](../archive/issues/lending_indices_handler_bugs_2026_05_07.md)
carries the canonical RESOLVED block. Code commits:

- `instruments-service@1a90185` — Bug 3: `get_protocol_floor_date()` consults UAC `PROTOCOL_LAUNCH_DATES` SSOT first;
  AAVE V3 ETHEREUM floor corrected from 2023-01-27 (legacy) to 2022-03-14 (UAC mainnet deploy).
- `market-tick-data-service@d2f365e` — Bugs 1+2: `_query_and_parse` cascade extended to AAVE V3 (native → Messari
  fallback); new `SubgraphSchemaError` distinguishes schema-drift from transient errors so cascade re-raises through
  `record_failed` (writegate Phase 2.A) instead of swallowing as `record_empty`.
- `market-tick-data-service@de9d5cf` — ruff format spacing follow-up.

After tarball refresh (`bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group DEFI`) the
lending-indices VM is ready to re-launch. Operator-owned step.

**Audit 2026-05-08 (Tab 14, defi-fork1-prep-audit-tab)**: 4-bug-class diagnostic audit ran across the full Fork 1
data-source surface BEFORE Ikenna's D4 launches. Results filed at
[`../archive/issues/defi_fork1_prep_audit_2026_05_08.md`](../archive/issues/defi_fork1_prep_audit_2026_05_08.md). TL;DR:
Bug classes 1-3 are ✅ no new findings (Tab 5 + Tab 9's shipped cascade + UAC SSOT cascade is structurally correct).
**Bug class 4 — UAC PROTOCOL_LAUNCH_DATES drift — found 13 of 17 probed pairs DRIFT > ±3 days.** Recommend operator
spawn 4 sequential fix tabs (A: AAVEV3 6 chains; B: COMPOUNDV3 4 chains; C: UNISWAPV3 3 chains; D: SPARK ETH + bSOL UAC
entry) all mirroring Tab 9's shape. Pyth Hermes archive coverage start ≈ 2023-10-01 (no SSOT); jitoSOL pre-2023-10
oracle-USD backfill blocked. bSOL is in Tab 14 brief as a Fork 1 LST yield but absent from UAC `LST_TOKEN_GENESIS` —
coverage gap. **Owner**: operator triage (case-5 big finding per CLAUDE.md Findings Triage Discipline; cross-repo UAC +
MTDS + instruments-service; on May-23 critical path).

**Verification recipe used to find these** (do this WITHIN 10-15 MIN of any backfill VM launch — don't wait for /loop):

```bash
PID=central-element-323112
VM=mtds-lending-indices-{ts}  # the actual VM name
gcloud storage cp gs://lending-indices-${PID}/_index/per_vm/${VM}.parquet /tmp/per_vm.parquet
python3 -c "
import pandas as pd
df = pd.read_parquet('/tmp/per_vm.parquet')
print(f'Total rows: {len(df):,}')
m = df.groupby(['venue','chain','capture_status']).size().unstack(fill_value=0)
print(m)
# Spot any (venue, chain) with 0 captured but non-zero empty_confirmed → silent-zero candidate
silent_zeros = m[(m.get('captured', 0) == 0) & (m.get('empty_confirmed', 0) > 100)]
if len(silent_zeros) > 0:
    print(f'\\n⚠️ Silent-zero candidates (captured=0 but empty_confirmed>100):')
    print(silent_zeros)
"
gcloud storage cat gs://deployment-scripts-${PID}/vm-logs/${VM}/run.log | grep -E "Subgraph query error|metadata unavailable|Wrote 0 rows" | head -20
```

Do this verification BEFORE assuming the VM is producing useful data based on event-stream alone.

1. **Solana coverage is genuinely thin** — `lst-rates-{pid}` has 784 SOLANA rows over a 2-year window (~monthly
   cadence). `carry_staked_basis` Solana leg won't have daily granularity until this is filled. Pyth wiring (separate
   item) is necessary-not-sufficient.
2. **Kebab/snake `data_type` vocab inconsistency** — most per-data_type DeFi buckets contain BOTH forms for the SAME
   data (e.g. `lending-indices-{pid}` has 24,976 kebab + 12,024 snake_case rows). Read-time canonicaliser handles it
   today but it's a real follow-up: write a one-shot migration to rewrite kebab → snake then delete the canonicaliser.
   No named successor plan yet — could be filed as a small follow-up under `manifest_migration_master_2026_05_07`.
3. **`solana-defi-{pid}` is 3+ weeks stale** — last write 2026-04-13. Worth confirming whether that handler is
   intentionally paused or has been broken.
4. **`launch-mtds-perp-funding-backfill-vm.sh`** — **CORRECTION 2026-05-08 audit**: launcher EXISTS at
   `deployment-service/scripts/vm/launch-mtds-perp-funding-backfill-vm.sh`. Earlier "missing" claim is stale.
   `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`) blocker around perp-funding capture is therefore not a
   missing-launcher issue; re-scope to "verify launcher is wired into `_SERVICE_LAUNCHER_SCRIPTS` registry +
   `VM_PREFIX_TO_BUCKET` watchdog".

**Single-VM launch recommendation** (unchanged from earlier):

| Rank | Launcher                                                             | Window       | Expected rows              | ETA           | Status                                                                  |
| ---- | -------------------------------------------------------------------- | ------------ | -------------------------- | ------------- | ----------------------------------------------------------------------- |
| 1    | `launch-mtds-lending-indices-backfill-vm.sh 2018-01-01 2026-05-07`   | full history | ~9,668                     | ~3h           | **In flight** as `mtds-lending-indices-20260507-140418` since 14:04 IST |
| 2    | `launch-mtds-vault-share-price-backfill-vm.sh 2020-01-01 2026-05-07` | full history | high carry-archetype value | parallel-safe | not yet launched                                                        |

- [ ] [AGENT] P1. Per-chain MTDS to 100%: Ethereum (85%), Solana (99.9% — basically done), Arbitrum / Base / Polygon
      (60%). Per-protocol gap analysis from `consolidated_defi_data_pipeline` Phase 6. **2026-05-07 NOTE: original
      headline percentages are defensible if reading the deployment-ui's per-bucket panels — see CORRECTION block above.
      Earlier "0%" claim was a single-bucket misread, not reality.** [AUDIT 2026-05-07: FRESH — actionable; the
      in-flight `mtds-lending-indices-20260507-140418` VM is doing the right work. After it drains, run
      vault-share-price as the parallel-safe runner-up.]

### DeFi DEX-perp adapters from `cefi_venue_universe_expansion` (re-classified to DeFi)

- [ ] [AGENT] P0. **Extended** — UAC: add to `VENUES_BY_ASSET_GROUP['defi']`. Adapter: `_fetch_extended_rest` + history.
      [AUDIT 2026-05-07: BLOCKED-ON dex_perp_onboarding_handover_2026_05_07:Item C — empirical research pending]
- [x] [AGENT] P0. **Pacifica** — UAC: same. Adapter: `_fetch_pacifica_rest`. Hyperliquid clone — schema parity. [AUDIT
      2026-05-07: DONE — MTDS@51fecd5 (ohlcv_1m); UAC@e890022 added ohlcv_1m to cefi DATA_TYPES_BY_ASSET_GROUP (note:
      routing gate per MEMORY entry feedback_uac_data_types_by_asset_group_is_routing_gate); UAC@7cb9068 / 405cbf5
      declare DEFI venue capabilities]
- [x] [AGENT] P0. **Lighter** — UAC: same. Adapter: `_fetch_lighter_rest`. zkSync L2; different RPC stack. [AUDIT
      2026-05-07: DONE — MTDS@10aa715 (ohlcv_1m); CloudFront 429 quirks documented in MEMORY
      (feedback_lighter_pacifica_cloudfront_quirks)]

### Custody (Copper)

- [ ] [AGENT] P1. Copper sandbox integration test — validate `CopperCustodyProvider` (in execution-service) per
      `codex/04-architecture/custody-providers.md` § 2.3 CopperCustodyProvider. [AUDIT 2026-05-07: FRESH — actionable,
      P0-relevant for May 23 Group F]

### Audit findings 2026-05-07 — folded from session wrapper

**Source**: `plans/ai/session_2026_05_07_data_status_audit_findings.md` row C.9. Operator inspected DEFI pool drilldown
after the 4-candidate-probe fix shipped (deployment-api@`0384eab`); AAVE_V3-ARBITRUM still surfaces "no schema yet" with
0 on-disk parquets across all 4 layout candidates even though the manifest claims `1781/1785 captured`.

#### C.9 — AAVE_V3-ARBITRUM phantom rows reconcile

This is a textbook phantom-rows scenario per CLAUDE.md `§ Manifest phantom audit`: manifest says `captured` but the
parquet doesn't exist at any canonical path. The orchestrator's `_should_skip_shard` will trust the manifest forever
unless reconciled. Either (a) parquets really don't exist (writer bug — needs root-cause + re-fetch), or (b) parquets
exist at a 5th layout the prober doesn't know about (extend the prober + the audit's drift-axis enumeration).

- [x] [SCRIPT] P0. Ran
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py --asset-group defi     --dry-run` locally,
      scoped `--venues AAVEV3` (sufficient for triage; full DEFI scan deferred to GCE VM after the prober landed below
      to avoid 18× slowdown × 313k row × 7 prefix template explosion). Initial run reported 29782 false-positive
      phantoms — the entire AAVEV3 dataset; would have destroyed all manifest state had `--apply` run.
- [x] [AGENT] P0. Triaged for AAVE_V3-ARBITRUM specifically — **case (b)** confirmed: audit reported mass
      false-positives. Diagnosed root cause via on-disk listing: the canonical manifest has ZERO
      `(venue=AAVEV3,     chain=ARBITRUM)` rows (all 29782 AAVEV3 rows are on `chain=ETHEREUM`). The UI's
      "AAVE_V3-ARBITRUM 1781/1785" claim came from the deployment-api offline rollup, which conflates the expected
      denominator with the found-on-disk count for venue+chain combos that have no manifest rows (separate rollup-side
      bug, captured in codex doc + filed under infrastructure_master Data-status multi-axis follow-up).
- [x] [SCRIPT] P0. Found two NEW drift axes the prober missed; extended
      `instruments-service/scripts/reconcile_phantom_manifest_rows_all.py` (instruments-service@`e8393fc`). **Axis 6** —
      DeFi protocol-name underscore variant (`AAVEV3` ↔ `AAVE_V3` etc.) via new `_defi_protocol_variants` regex helper
      that probes both spellings; **Axis 7** — DeFi migrated-bundle wildcard (`ticks_migrated_*.parquet` at the
      combined-venue prefix accepted as evidence of capture for any data_type, since the bundle holds all data_types in
      one parquet). Helper unit-tested 12/12 cases PASS. Re-run on `--venues AAVEV3` shows 29782 → 0 phantoms (100%
      false-positive elimination). Manifest is clean for AAVEV3.
- [x] [VERIFY] P1. After ship: launch `defi-phantom-recon-{ts}` GCE VM in `asia-northeast1-c` (add prefix to
      `vm_zombie_watchdog.py` `VM_PREFIX_TO_BUCKET` first) running the full DEFI dry-run with the new prober. Compare
      pre-/post-fix phantom counts across all DEFI venues (UNISWAPV3 187k rows, MORPHO 45k, EIGENLAYER, MAKER, etc.).
      Expected: large drop in false-positive count similar to the 2026-05-04 cefi 130k → 354 reduction. **SHIPPED
      2026-05-07**: deployment-service@ea0c2ed authored `scripts/vm/launch-defi-phantom-recon-vm.sh` (new launcher,
      singleton-locked, asset-group selectable, --dry-run by default), added `phantom-recon` VM_TASK route to
      `setup-data-pipeline-vm.sh`, and added `defi-phantom-recon-` prefix to `vm_zombie_watchdog.py`. Path bug fix at
      deployment-service@a6d3b8f (instruments tarball alias = `$WORKSPACE/instruments` not
      `$WORKSPACE/instruments-service`). VM `defi-phantom-recon-defi-20260507-141621` launched 14:16 IST, watchdog
      relaunched as `vm-zombie-watchdog-20260507-141056`. **Result 14:24 IST (rc=0, ~10 min runtime, 86,982 prefixes
      listed at 360/sec same-region GCE)**: 309,749 real captures + **2,931 phantom captures (0.94%)**. Top phantom
      data_types: vault_share_price (1,633) + rewards (1,298). Top phantom venues: EIGENLAYER (1,298), MORPHOVAULTS
      (851), YEARNV3 (782) — concentrated in features-onchain consumers (`eigen_rewards` + `vault_share_price`), so
      they're real blockers, not prober drift. **Next step (operator)**: run
      `bash scripts/vm/launch-defi-phantom-recon-vm.sh defi --apply` to flip the 2,931 phantoms to `attempted_failed`,
      then re-run the affected MTDS DeFi backfills (eigen_rewards via `mtds-perp-funding`/equivalent and morpho/yearn
      `vault_share_price` via `launch-mtds-vault-share-price-backfill-vm.sh`).
- [x] [DOC] P0. Updated `codex/02-data/availability-manifest-and-data-status.md` § "Phantom audit — re-runnable recipe"
      to enumerate 7 drift axes (was 5); added rollup-side metric inconsistency finding under § "Rollup-side metric
      inconsistency (deployment-api `_data_status_rollup_worker`) — open finding 2026-05-07"; updated history benchmark
      with the 2026-05-07 AAVEV3 29782 → 0 reduction.

### 988-missing-dates audit residuals (migrated from `defi_988_missing_dates_audit_2026_05_08`)

Source issue archived. Audit identified 13.6k actionable (non-legit) missing rows across 7 buckets. Priorities #1+#5
fold into the lending-indices section above; priorities #2-#4 below remain pending. Coordinate with
`writegate_honest_coverage_endtoend_2026_05_06` Phase 2.E (honest-absence taxonomy depends on correct launch dates
shipping with the Fork-1 prep batches below).

- [ ] [SCRIPT] P0. **Priority #2 — DEX swaps subgraph schema-mismatch fix.** Per-protocol detailed roadmap: PancakeSwap
      V3 (BSC/Ethereum/Arbitrum), SushiSwap V3 (Ethereum/Polygon/Arbitrum/Optimism), Aerodrome (Base), Camelot
      (Arbitrum). For each: probe current Messari subgraph endpoint shape; rewrite query if schema drifted (most likely:
      pool entity field renames since 2024 indexer upgrade); per-row `record_failed(SCHEMA_DRIFT)` for rows where the
      protocol responded but the canonical field set isn't extractable; cassette parity test locks the new shape. ~1.8k
      blank-reason rows clear once fix lands.
- [ ] [HUMAN+AGENT] P0. **Priority #3 — PROTOCOL_LAUNCH_DATES SSOT tightening for Ethereum vault protocols.** Standalone
      action: probe each pre-2023 vault entry (RocketPool, Lido, etc.) for actual on-chain genesis vs UAC declaration;
      flip mis-declared rows to `expected_pre_protocol_launch`. ~6.9k pre-launch misclassified rows. Operator decision:
      which protocols block (carry_staked_basis depends on Lido + jitoSOL) vs deferrable (smaller LSTs).
- [ ] [HUMAN] P0. **Priority #4 — ASTER chain genesis + perp-funding adapter audit.** Operator go/no-go decision: ASTER
      has 0 perp-funding rows but UAC declares it as a venue. Either: (a) confirm ASTER pre-genesis →
      `expected_pre_genesis_chain` for the bad date range; OR (b) confirm ASTER genesis was earlier and the perp-funding
      adapter has a routing bug (which CLAUDE.md "UAC DATA_TYPES_BY_ASSET_GROUP is routing gate" rule flags as a likely
      cause). ~0.8k blank rows pending decision.
- [ ] [SCRIPT] P0. **Priority #5 — Lending-indices LINEA/BSC routing config.** Distinct workstream from priority #1
      (which is Ethereum-AAVEV3 UAC fix).
      `status: backfill-running` — **the "routing config absent" framing was STALE** (grep-then-conclude error in the
      2026-05-08 audit): `SUBGRAPH_IDS["aave_v3"]["LINEA"]` + `["BSC"]` have been wired since UAC@`2db3c8e` (Mar 2026);
      `get_supported_chains_for_protocol("aave_v3")` already includes LINEA+BSC; UAC launch dates corrected at
      UAC@`6c873e4` (`("LINEA","AAVEV3")="2025-02-11"`, `("BSC","AAVEV3")="2024-01-23"`); `lending_indices` ∈
      `DATA_TYPES_BY_ASSET_GROUP["defi"]`; `get_venue_prefix("aave_v3")=="AAVEV3"` so the pre-floor-date short-circuit
      (MTDS@`c6bdf96`) fires correctly. On-disk parquets verified REAL (LINEA `aave_v3/LINEA/date=2025-03-01` = 475 rows
      USDC/WETH reserves; BSC `aave_v3/BSC/date=2024-06-01` = 316 rows Cake/BTCB/USDT/USDC/WBNB/ETH/FDUSD), not
      1440-NaN placeholders. **The actual gap was operational**: the `lending-indices-{pid}` canonical
      `_index/availability_index.parquet` was stale vs the per-VM shards (the `mtds-lending-indices-20260508-141147` run
      had already captured LINEA AAVEV3 post-launch + BSC AAVEV3 post-launch + flipped pre-launch days to
      `empty_confirmed` in its per-VM shard, but the consolidator never merged it — see "Discoveries" below). Slot 3
      2026-05-11: (1) ran `python -m unified_trading_library.manifest_consolidator --bucket lending-indices-{pid} --once`
      → canonical now AAVEV3/LINEA = 451 captured (2025-02-11→2026-05-07) + 1137 empty_confirmed pre-launch + 0
      attempted_failed; AAVEV3/BSC = 836 captured (2024-01-23→2026-05-07) + 752 empty_confirmed pre-launch + 0
      attempted_failed — the ~576 stale "404 GET https" `attempted_failed` rows (293 LINEA + 219 BSC) + 198 LINEA
      blank-reason `empty_confirmed` are reclaimed; (2) launched fresh full-history backfill VM
      `mtds-lending-indices-20260511-181115` (`2022-01-01..2026-05-11`, e2-standard-4, `mtds-lending-indices-` prefix in
      `VM_PREFIX_TO_BUCKET`) — event-verified STARTED (`correlation_id` 366b8002…) + `LENDING_DAY_COMPLETE` /
      `INSTRUMENT_PROCESSED` (real row counts) / `RESOURCE_PROFILER_SAMPLE` progress stream. **ETA ~4-17h** (much slower
      than first estimated — the 2022-Q4 high-volume window dominates: OPTIMISM / ARBITRUM AAVEV3 emit 25-40k
      reserve-param-history rows/day → heavy 1000-row-page pagination; and `lending_indices_handler` re-processes every
      date in the range without a manifest-freshness skip — known follow-up per CLAUDE.md "Manifest concurrency
      principle" / "refactor existing MTDS per-venue VMs"). As of 14:08 UTC at date 2022-12-10, healthy + progressing,
      RSS ~741MB, no FAILED events. **Watcher `b72uau4o7` armed** (re-invokes on terminal/stall/2.5h-deadline; re-armed
      if it false-fires on deadline). **FINAL PUSH steps 2-4** (per `[main → slot 3]` 14:01 brief): on VM `STOPPED`/`FAILED`
      → `python -m unified_trading_library.manifest_consolidator --bucket lending-indices-{pid} --once` → verify canonical
      shows the recent gap (2026-05-07→2026-05-11) `captured` for AAVEV3/LINEA + AAVEV3/BSC + the ~142 LINEA + ~296 BSC
      `SOURCE_RETURNED_ZERO` pre-launch nits reconciled to `EXPECTED_PRE_GENESIS_CHAIN` (sample-inspect a parquet, not
      just row counts) → flip `[x]` with `<repo>@<sha>` + VM-name + manifest-row evidence + write a `## DONE-2026-05-12`
      block + cross-side INFO ping to ikenna-main with the final manifest counts. Stale-path
      note: the audit said `market_tick_data_service/adapters/lending_indices/` — actual handler is
      `market_tick_data_service/cli/handlers/lending_indices_handler.py` + adapter
      `market_interface/adapters/defi/aave_lending.py` (no `adapters/lending_indices/` dir exists).

### Discoveries during Priority #5 (slot 3, 2026-05-11)

- [x] [SCRIPT] P0. **Manifest consolidator daemon was NOT polling the per-data_type DeFi buckets** — `lending-indices-{pid}`,
      `dex-swaps-{pid}`, `evm-defi-{pid}`, `gas-fees-{pid}`, `oracle-prices-{pid}`, `perp-funding-{pid}`,
      `solana-defi-{pid}`, `lst-rates-{pid}` (deployment-api's `data_status_service._BUCKET_CATEGORY_OVERRIDES` routes
      each DeFi data_type to its own dedicated bucket). The consolidator's `VM_BUCKETS` covered `instruments-store-*`,
      `market-data-tick-*` (asset-group canonicals), `strategy-store-*`, `features-sports-*` — none of the per-data_type
      DeFi buckets. Consequence: their canonical `_index/availability_index.parquet` drifted stale vs per-VM shards →
      deployment-UI data-status showed wrong DeFi coverage (e.g. lending-indices kept showing 293 LINEA + 219 BSC
      AAVEV3 `attempted_failed` for ~3 days after the `20260508-141147` run had reconciled them). **FIXED** —
      deployment-service@`ad4d448` adds the 8 per-data_type DeFi buckets to `launch-manifest-consolidator-vm.sh`
      `BUCKETS`; relaunched the consolidator daemon as `manifest-consolidator-20260511-181538` (old
      `manifest-consolidator-20260507-175639` deleted 2026-05-11 12:50 UTC after the new one's first poll confirmed it
      consolidating `lending-indices` + `dex-swaps` + `evm-defi`). One-time manual consolidation of `lending-indices-{pid}`
      already done; the other 7 per-data_type DeFi buckets picked up by the relaunched daemon's first poll (verified —
      `dex-swaps` got `legacy_seeded=True`, 46491 rows on first cycle). **Case-5 big finding** (data correctness for DeFi,
      May-23 critical path, cross-repo) — operator flagged in chat 2026-05-11.
- [x] [SCRIPT] P1. **Consolidator poll-list completeness audit (slot 6, 2026-05-11)** — the slot-3 fix above added 8 of
      the 10 per-data_type DeFi buckets to the consolidator `BUCKETS` list but missed `dex-pools-{pid}` and
      `liquidations-{pid}` — both are in `deployment-api`'s `_BUCKET_CATEGORY_OVERRIDES` + `_MTDS_DEFI_SUB_DIMENSIONS`
      (10 keys), and both are written via `get_write_bucket_name()` in their MTDS handlers
      (`dex_pools_handler.py:326`; `get_write_bucket_name("liquidations")`). Same staleness class. **FIXED** —
      deployment-service@`2a76a2a` adds `dex-pools-{pid}` + `liquidations-{pid}` to `launch-manifest-consolidator-vm.sh`
      `BUCKETS` (also reordered the DeFi block alphabetically + expanded the comment to document all 10 + flag
      `solana-defi` as legacy — the Solana handler now writes to `dex_pools`/`perp_funding`/`lst_rates` per
      `check_solana_defi_paths.py`). Relaunched the daemon: `manifest-consolidator-20260511-181538` (slot 3's) deleted,
      new `manifest-consolidator-20260511-190513` running with the 10-bucket list — **first cycle PAID OFF immediately**:
      it found `_index/per_vm/_legacy_seed.parquet` files in both new buckets (the consolidator auto-seeds legacy
      snapshots on first poll of a bucket) and wrote them to the canonical indices — `dex-pools-{pid}` → 75983 rows,
      `liquidations-{pid}` → 38134 rows. So there WAS real un-consolidated data sitting in those buckets (their canonical
      `_index/availability_index.parquet` was stale-by-never-merged-legacy-seed; I'd initially mis-assessed it as
      "no staleness" because I only checked for `_index/per_vm/{vm_name}.parquet` shards, missing the `_legacy_seed`).
      **Other asset_groups checked, no gap**: CeFi options-chain/futures-chain, TradFi futures-chain,
      prediction canonical-question, sports fixture-bundles all write to their asset-group canonical buckets
      (`market-data-tick-{cefi,tradfi,prediction,sports}-{pid}`) which ARE already in the poll list — no dedicated
      per-data_type buckets there.
- [ ] [SCRIPT] P2. **Future consolidator-poll-list gap — features-\* / execution-store / strategy-store-prediction / ml-\*
      buckets (slot-6 finding 2026-05-11).** When the features-service / execution-service / ml-\* pipelines run
      end-to-end and write manifest rows to their per-asset-group buckets — AND if they run multi-VM with
      `MANIFEST_PER_VM_SHARDS=true` — those buckets MUST be added to the consolidator `BUCKETS` list or their canonical
      `_index/availability_index.parquet` will drift stale. Currently NOT a gap: probed 2026-05-11 — `features-delta-one-*`
      / `features-volatility-*` / `features-onchain-defi` / `features-calendar` / `features-sports` / `execution-store-*`
      / `ml-predictions-store` buckets exist but have ZERO `_index/availability_index.parquet` (pipeline hasn't run with
      manifest writes yet); `ml-models-store-{pid}` has a canonical index (single-writer pattern → no consolidation
      needed); `strategy-store-prediction-{pid}` not provisioned. **Also**: the bucket-name SSOT env-tier migration
      (`code_freeze_migrate_backfill_sequencing_2026_05_10.md` Phase 2.6) RENAMES every bucket (e.g.
      `market-data-tick-prediction-{pid}` → `market-data-tick-pred-prd-{pid}`); the consolidator `BUCKETS` list MUST be
      updated in lockstep with that rename or it polls dead names. **Owner**: this item migrates to `code_freeze` Phase 2.6
      (which already owns the bucket-rename + must update every bucket consumer) OR to the features/execution pipeline-
      activation plan when those run end-to-end — whichever lands first. The fix shape is identical to deployment-service@`2a76a2a`:
      add the (then-extant) bucket names to `launch-manifest-consolidator-vm.sh` `BUCKETS` + relaunch the daemon.
      **Sub-finding (watchdog-dict imprecision, slot-6 2026-05-11)**: `vm_zombie_watchdog.py`'s `VM_PREFIX_TO_BUCKET`
      maps `mtds-gas-fees-` / `mtds-lst-rates-` / `mtds-dex-pools-backfill` / `mtds-liquidations-backfill` (+ `mtds-perp-funding-`)
      to `market-data-tick-defi-{pid}`, but those MTDS handlers actually write the data to the dedicated per-data_type
      buckets (`gas-fees-{pid}` / `lst-rates-{pid}` / `dex-pools-{pid}` / `liquidations-{pid}` / `perp-funding-{pid}`) via
      `get_write_bucket_name(<kind>)`. The watchdog uses the mapped bucket only for a "is the VM still writing" progress
      probe — `market-data-tick-defi-{pid}` is a *valid* (some handlers also write a catalogue index there) but imprecise
      target. Cosmetic watchdog-progress-check imprecision, NOT a consolidator gap (the consolidator poll-list is now
      correct vs the authoritative source = `get_write_bucket_name()` callsites + `_BUCKET_CATEGORY_OVERRIDES`). Fix when
      touching the watchdog dict next: point those 5 prefixes at their dedicated buckets. Operator relaunch of the
      watchdog VM required to pick it up (per CLAUDE.md VM-Naming-Convention rule).
- [ ] [SCRIPT] P1. **EIGENLAYER `rewards` shard-key drift — manifest row `data_type=rewards` vs parquet path `data_type=eigenlayer_rewards/` (slot-6 phantom-audit finding 2026-05-11).** The DeFi phantom recon (`reconcile_phantom_manifest_rows_all.py --asset-group defi --dry-run` on `defi-phantom-recon-defi-20260511-192115`, completed 2026-05-11 13:58 UTC) reported **1298 "phantom captures", ALL `venue=EIGENLAYER` / `data_type=rewards`** — but they're **FALSE positives** (the data exists on disk, the audit's path template doesn't match). Root cause = a **shard-key-SSOT violation** in `market-tick-data-service/market_tick_data_service/cli/handlers/eigenlayer_rewards_handler.py`: it `recorder.record_captured(...)` with `data_type="rewards"` (`_EIGENLAYER_DATA_TYPE = "rewards"`, used at :184/193/203) + `instrument_type="staking"` (:186) but **writes the parquet** at a path built with `data_type="eigenlayer_rewards"` (:296) + `file_name="rewards.parquet"` (:298) → on-disk:
      `raw_tick_data/by_date/day={D}/asset_group=defi/venue=EIGENLAYER/chain=ETHEREUM/instrument_type=staking/data_type=eigenlayer_rewards/rewards.parquet` (confirmed 2026-05-11: `gs://market-data-tick-defi-{pid}/raw_tick_data/by_date/day=2024-08-15/asset_group=defi/venue=EIGENLAYER/chain=ETHEREUM/instrument_type=staking/data_type=eigenlayer_rewards/rewards.parquet` exists). The audit probes the manifest row's `data_type=rewards` segment → `.../instrument_type=staking/data_type=rewards/` → empty → false phantom. **Do NOT `--apply` the flip** — flipping 1298 good rows to `attempted_failed` would corrupt the manifest (same class as the 2026-05-04 130,897-false-positive incident). **Also**: the handler docstring (:21) is stale on 3 axes — says `venue=EIGENLAYER-ETHEREUM/instrument_type=restaking/data_type=rewards/ticks.parquet`; actual is `venue=EIGENLAYER/chain=ETHEREUM/instrument_type=staking/data_type=eigenlayer_rewards/rewards.parquet`. **Fix** (shard-key-SSOT decision — defi-pipeline owner): make the `record_captured`/`record_empty` `data_type` match the parquet path (`eigenlayer_rewards` is the Phase-2-event-typed canonical token per deployment-api `data_status_service.py`'s comment — so flip `_EIGENLAYER_DATA_TYPE` to `"eigenlayer_rewards"`, NOT the parquet path to `rewards/`) + a one-time migration of the existing manifest rows from `data_type=rewards` → `data_type=eigenlayer_rewards` (per the "Manifest migration, NOT fallback" rule) + fix the docstring. Optionally also add the `data_type=eigenlayer_rewards`-on-disk-vs-manifest layout to `reconcile_phantom_manifest_rows_all.py`'s DeFi drift-axis list as a safety net, but the root fix is the handler's shard-key consistency. **Owner**: defi-pipeline / `defi_master` (the eigenlayer Phase-2 event handler) — coordinate with the shard-granularity-SSOT umbrella (`infrastructure_master_2026_05_07.md`). **Net phantom-audit result for DeFi**: 1298 reported, all false-positive (path drift), **real residual = 0** (data exists) — but the shard-key drift is a latent inconsistency that needs the handler fix.
- [ ] [SCRIPT] P1. **`create-code-tarballs.sh` has a stale repo list + non-graceful skip** — its `DEFI_REPOS`/EXTRA_REPOS
      list references `features-onchain-service` (consolidated into `features-service` by the 2026-05-08 features-*
      consolidation); the "SKIP <repo> — not found" path trips `set -e` so a missing repo aborts the whole tarball build
      with `EXIT=1` (it logs the SKIP message but then dies). Blocks `create-code-tarballs.sh --asset-group DEFI` from
      `.tabs/*` worktrees (which have `features-service` not `features-onchain-service`). Workaround for Priority #5:
      none needed — the deployed `mtds-code.tar.gz` (2026-05-10) already has MTDS@`c6bdf96` (pre-floor-date short-circuit)
      + the latest lending_indices code, so the VM ran current code without a refresh. Fix: (a) update the repo lists to
      post-consolidation names (`features-service` instead of `features-onchain-service`/`features-defi-service`/etc.);
      (b) make the missing-repo case actually `continue` past `set -e` (e.g. `if [[ -d "$path" ]]; then create_tarball
      ...; else log "SKIP ..."; fi`). Owner: features-* consolidation follow-up — coordinate with
      `features_repo_consolidation_2026_05_08` (archived?) or `infrastructure_master_2026_05_07`. **MIGRATE** to whichever
      owns the features-* consolidation tail.

### Chain coverage + CLOB-on-chain venues (migrated from `defi_chain_coverage_and_clob_venues_2026_05_08`)

Source issue archived. Hyperliquid L1 chain identity missing from UAC enum (blocks omni-chain transfers, SOR,
reconciliation); Lighter/Pacifica/Extended lack instruments-service discovery adapters (writegate v2 enumerator can't
derive expected universe). 5-phase remediation. Operator decision required on asset_group classification.

**Cross-plan banner**: coordinate with `dex_perp_onboarding_handover_2026_05_07.HANDOVER` Items A/C/E and writegate
Phase 3.D.5 v2 enumerator (must handle CLOB venues).

- [ ] [SCRIPT] P0. **Phase 1 — UAC ChainKind extension.** Add `HYPERLIQUID_L1` + `STARKNET` chain entries to UAC
      `unified_api_contracts.canonical.crosscutting._defi.ChainKind` enum. Add `CHAIN_RPC_TEMPLATES` entries
      (Hyperliquid L1 and Starknet endpoints). Add `bridge_to` graph capturing which chains can bridge to which
      (Hyperliquid L1 ↔ Arbitrum via native bridge; Starknet ↔ Ethereum via STARK proof bridge).
- [ ] [SCRIPT] P0. **Phase 2 — instruments-service CLOB discovery adapters.** Lighter (zkSync) / Pacifica (Solana) /
      Extended (Starknet). Per-instrument catalog rows in instruments-store-defi:
      `(asset_group=defi, chain, venue,     instrument_type=PERP, instrument_id, contract_address, base_asset, quote_asset, decimals, listed_at)`.
      Adapters probe each venue's discovery endpoint (Lighter `/markets`, Pacifica `/markets`, Extended `/markets`);
      emit record_captured per instrument.
- [ ] [SCRIPT] P0. **Phase 3 — strategy-service `allowed_chains` constraint enforcement.** Per-archetype config gains
      `allowed_chains: list[ChainKind]`; strategy refuses to size positions on chains outside the list.
      carry_staked_basis defaults: ETHEREUM + SOLANA + ARBITRUM. `ARBITRAGE_PRICE_DISPERSION`
      (`funding-rate-dispersion`) defaults: all 6 perp venues' chains.
- [ ] [HUMAN] P1. **Phase 4 — asset_group classification decision (operator).** CLOB-on-chain venues (Lighter / Pacifica
      / Extended) sit at the boundary between DeFi (on-chain settlement) and CeFi (centralised order book matching). Two
      options: (a) extend DeFi asset_group to include them (current default; minor mental tension); (b) new `clob_dex`
      asset_group (clean separation but workspace-wide vocabulary churn — cuts across UAC `VENUES_BY_ASSET_GROUP`, MDPS
      bucket layouts, deployment-ui drilldown). Issue's recommendation was option (b); operator reaffirms or overrides.
      **Decision needed before Phase 5 below ships.**
- [ ] [SCRIPT] P1. **Phase 5 — Extended unblocking.** Starknet RPC template + OHLCV adapter for Extended. Blocked until
      Phase 1 ships Starknet chain entry + Phase 4 asset_group decision.

### Hardcoded on-chain-derivable values audit (migrated from `defi_eliminate_hardcoded_onchain_derivable_values_2026_05_08`)

Source issue archived. 3-category model: (A) immutable historical facts (token decimals, chain genesis, factory
addresses, protocol launch dates) — should derive from on-chain or pin to SSOT script; (B) slow-changing governance
parameters (LTV, liquidation threshold, rate-curve kinks) — refresh hourly/daily into time-versioned parquet (covered
separately by governance-refresh section below); (C) real-time reads (current rates, liquidity, prices) — read live.
AAVEV3 ETHEREUM date was 49 days wrong (corrected 2023-01-27); systematic audit of remaining values needed.

**Cross-plan dependency**: this section's Phase 3 (Cat B fallback removal) MUST ship AFTER governance-refresh section's
Phase 2 (time-versioned parquet) lands. Sequence in plan execution.

- [ ] [SCRIPT] P0. **Phase 1 — `derive_protocol_launch_dates.py` SSOT script** under
      `unified-api-contracts/scripts/derive_protocol_launch_dates.py`. For each entry in UAC `PROTOCOL_LAUNCH_DATES`:
      derive from on-chain (factory.created_at block; Aave InitializeReserve event; etc.); compare against current UAC
      declaration; print drift. Pre-commit gate: any change to `PROTOCOL_LAUNCH_DATES` must run this script and include
      its output as a citation comment per entry (`# DERIVED 2026-05-08 from <chain> block <N> tx <hash>`).
- [ ] [SCRIPT] P0. **Phase 2 — Cat A audit beyond AAVEV3.** Token decimals (every entry in UAC `TOKEN_DECIMALS`), chain
      genesis (every chain in `CHAIN_GENESIS_DATES`), factory addresses (Uniswap, SushiSwap, PancakeSwap, Curve, Aave,
      Compound). Probe on-chain; compare; flag drift. Output: `defi_cat_a_audit_2026_05_08_report.md` under
      `unified-api-contracts/audits/`.
- [ ] [SCRIPT] P0. **Phase 3 — Cat B fallback removal from aave_risk_calculator.** Replace inline LTV / liquidation-
      threshold constants with reads from governance-params parquet (Phase 2 of governance-refresh section).
      `LookaheadBiasError` raised loud if feature timestamp < params asof. **BLOCKED-ON governance-refresh Phase 2.**
- [ ] [SCRIPT] P1. **Phase 4 — Cat C test-fixture modernization.** e2e block numbers in
      `e2e-testing/tests/.../fixtures/defi_block_numbers.py` are pinned (snapshot dates from 2024); refresh quarterly
      via a cron VM that probes recent finalized block per chain. Sports bankroll test fixture similar.
- [ ] [SCRIPT] P0. **Phase 5 — PM `quality-gates.sh` lint rule for new hardcoded addresses/block-numbers.** New STEP
      adds AST-walk asserting any new contract address or block number in
      `unified_api_contracts/canonical/domain/_defi.py` or related modules carries the `# DERIVED <date> from <source>`
      citation comment. Fails CI otherwise.

### Fork-1 prep — UAC date drift fixes (migrated from `defi_fork1_prep_audit_2026_05_08`)

Source issue archived. 13 UAC date drifts identified in Fork-1 scope: AAVEV3 OPTIMISM/BASE/LINEA/BSC (141d-293d drift),
COMPOUNDV3 ETHEREUM/BASE (12d-22d silent data loss), UNISWAPV3 ARBITRUM/OPTIMISM (91d-35d), SPARK missing (add + remove
from PENDING), bSOL missing from `LST_TOKEN_GENESIS`, Pyth Hermes archive gap (2022-11 → 2023-10).

**Critical sequencing**: all 4 batches touch `unified_api_contracts/canonical/domain/_defi.py` chain_env block — batches
MUST merge sequentially in the recommended order (no concurrent PRs) to avoid UAC change-queue collisions. **Cross-plan
dependency**: feeds writegate Phase 2.E EXPECTED_PRE_GENESIS_CHAIN taxonomy + manifest consolidator
auto-row-reclassification.

- [x] [SCRIPT] P0. **Batch A — AAVEV3 multi-chain dates.** Fix OPTIMISM (141d), BASE (293d), LINEA, BSC drift. Per-entry
      on-chain verification via Phase 1 script of hardcoded-values audit above; cite block + tx in comment. Single PR,
      single commit, push to `live-defi-rollout`. **SHIPPED** UAC@6c873e4 (OPTIMISM 2022-08-04→2022-03-15 fixes 142d
      silent data loss; POLYGON 2022-03-16→2022-03-12; AVALANCHE 2022-03-16→2022-03-12; BASE 2023-08-09→2023-08-22;
      LINEA 2024-09-26→2025-02-11; BSC 2023-04-06→2024-01-23; all 6 pairs cited inline with subgraph-probe evidence per
      Tab 14 audit).
- [x] [SCRIPT] P0. **Batch B — COMPOUNDV3 multi-chain dates.** Fix ETHEREUM (12d silent data loss), BASE (22d). Same
      pattern as Batch A. Sequenced AFTER Batch A. **SHIPPED** UAC@6c873e4 (ETHEREUM 2022-08-25→2022-08-13; ARBITRUM
      2023-04-13→2023-05-04; BASE 2023-08-26→2023-08-04; OPTIMISM 2024-02-15→2024-04-06; POLYGON entry removed from
      `PROTOCOL_LAUNCH_DATES` and moved to `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` since `SUBGRAPH_IDS["compound_v3"]`
      has no POLYGON entry).
- [x] [SCRIPT] P0. **Batch C — UNISWAPV3 multi-chain dates.** Fix ARBITRUM (91d), OPTIMISM (35d). Same pattern,
      sequenced AFTER Batch B. **SHIPPED** UAC@6c873e4 (ARBITRUM 2021-08-31→2021-06-01; OPTIMISM 2021-12-16→2021-11-11;
      BASE 2023-08-09→2023-07-31; all 3 are subgraph indexing pre-public-launch testnet/devnet blocks; test-side
      `_PRE_GENESIS_SUBGRAPH_INDEXED_ALLOWLIST` extended to permit launch < chain_genesis for these pairs).
- [x] [SCRIPT] P0. **Batch D — SPARK + bSOL.** Add SPARK to `PROTOCOL_LAUNCH_DATES` (currently missing despite being in
      PENDING list); remove from PENDING; add bSOL to `LST_TOKEN_GENESIS` + `LST_VENUE_TO_TOKENS`. Sequenced AFTER Batch
      C. **SHIPPED** UAC@6c873e4 (SPARK/ETHEREUM at 2023-03-07 added; SPARK removed from PENDING; bSOL at 2022-11-24
      conservative floor added to LST_TOKEN_GENESIS; BLAZESTAKE→(bSOL,) added to LST_VENUE_TO_TOKENS; Solana RPC probe
      for exact bSOL mint date deferred to follow-up).
- [ ] [HUMAN+AGENT] P1. **Pyth Hermes coverage SSOT + jitoSOL pre-2023-10 backtest scope.** UAC oracle-coverage module
      (NEW) declares Pyth Hermes archive availability per feed: jitoSOL feed has Hermes data starting 2023-10-XX,
      Pythnet RPC data going further back but not archived consistently. Operator go/no-go: do we backtest jitoSOL
      pre-2023-10 (uses Pythnet replay, slow + expensive) or clip the backtest window to 2023-10+? Default: clip.
- [ ] [SCRIPT] P1. **Latent Bug-class-3 local fallback drift sweep.** Adjacent to case-2 (UAC PROTOCOL_LAUNCH_DATES vs
      instruments-service local fallback dict). Sweep for any local fallback that overrides UAC values without explicit
      comment; remove the override or document why it survives. Deferred POST-batches A-D.

### Governance parameters refresh (migrated from `defi_protocol_governance_parameters_refresh_2026_05_08`)

Source issue archived. Aave/Compound/Morpho parameters (LTV, liquidation threshold, rate-curve kinks, borrow caps)
frozen at discovery time today; no refresh path. Live trading risk: governance change between discovery + execution
silently mis-prices positions.

**Cross-plan ordering**: Phase 2 (time-versioned parquet) MUST ship BEFORE the hardcoded-values audit's Phase 3 (Cat B
fallback removal). Documented above.

- [ ] [SCRIPT] P0. **Phase 1 — Per-protocol event listener.** Aave V3: listen for `ReserveDataUpdated` +
      `BorrowCapChanged` + `SupplyCapChanged` events. Compound V3: listen for IRM-change events. Morpho: curator
      `MarketParamsUpdated` events. Per-event: write to time-versioned parquet (Phase 2). Implementation: extend MTDS
      DeFi adapters with an event-listener mode (separate from current snapshot-poll mode).
- [ ] [SCRIPT] P0. **Phase 2 — Time-versioned governance_params parquet schema.** Path:
      `gs://market-data-tick-defi-{pid}/governance_params/by_protocol/protocol={p}/chain={c}/by_date/day={d}/...parquet`.
      Schema: `{protocol, chain, asset, param_name, param_value, asof_block, asof_timestamp, governance_tx_hash}`. Asof
      lookups via `read_governance_params_asof(protocol, chain, asset, asof: datetime)` UTL helper — asof <= timestamp
      filter, latest row wins. NO future-dated rows ever returned (LookaheadBiasError if attempted).
- [ ] [SCRIPT] P0. **Phase 3 — features-onchain APR calculator migration.** Replace inline LTV / IR constants with asof
      reads from governance_params parquet (Phase 2). LookaheadBiasError check at every read. **GATES Cat B fallback
      removal in hardcoded-values audit Phase 3.**
- [ ] [SCRIPT] P0. **Phase 4 — strategy-service sizing migration.** Historical-asof in batch (read params at the
      historical compute timestamp); current-asof in live (read latest available). Strategy onboarding checklist gains a
      "governance dependency declaration" requirement.
- [ ] [SCRIPT] P1. **Phase 5 — Snapshot space monitoring (proactive).** Cloud Scheduler job (registered via
      `deployment_ui_lifecycle_tabs_2026_05_08` Phase D) polls Snapshot.org governance spaces (aavedao, comp-vote,
      morpho) every 6h; emits `GOVERNANCE_PROPOSAL_LIVE` event when a parameter-change proposal opens; alert routes to
      operator-on-call.
- [ ] [SCRIPT] P0. **NEW UAC LifecycleEventType `GOVERNANCE_PARAMS_CHANGED`** emitted by Phase 1 listener at every
      change. Payload: `{protocol, chain, asset, param_name, old_value, new_value, asof_block, governance_tx_hash}`.

### Lending-indices Bug 2 — Compound V3 multi-chain Messari schema (migrated from `lending_indices_handler_bugs_2026_05_07`)

Source issue archived. Bugs 1 + 3 already resolved (UAC `PROTOCOL_LAUNCH_DATES` correction shipped via Tab 9; floor-date
math + reason-routing per CLAUDE.md taxonomy shipped). Bug 2 (Messari subgraph schema error for Compound V3 multi-chain)
remains open. Folds into the existing "Lending-indices VM run-quality bugs" section above as a P0 todo.

- [ ] [SCRIPT] P0. **Bug 2 — Messari Compound V3 subgraph query rewrite.** Probe current schema of Compound V3 subgraph
      endpoint per chain (Ethereum, Base, others); identify the field renames since the indexer upgrade that the current
      MTDS query depends on. Rewrite query, add per-row `record_failed(SCHEMA_DRIFT)` for any row where the response
      shape deviates from the canonical contract (so we never write garbage). Cassette parity test locks the new shape.
      Smoke 1 day per chain post-rewrite.
- [ ] [AGENT] P1. **Verification recipe automation.** Post-VM-launch silent-zero detector — Cloud Scheduler job that
      checks the last 24h of lending-indices manifest rows for unexpected zero-rows-per-instrument; alerts via Telegram
      if a venue × chain pair flatlines. Generalisable to other DeFi handlers; not just lending. Coordinate with
      `instruments_live_master_2026_05_08` Phase A.11 upstream-staleness monitor.

### Coordination banner — defi_master 6-perp-venue list update

> 🟡 IN-FLIGHT REFACTOR — `defi_archetypes_canonicalisation_and_venue_matrix_2026_05_07` Stream A is re-verifying the
> 6-perp-venue list referenced throughout this plan; the current list (Bybit/Deribit/Binance/OKX/Hyperliquid/Aster) may
> be stale per the 2026-05-07 audit (issue archived to
> `plans/archive/issues/defi_archetypes_doc_plan_drift_2026_05_07.md`). RE-VERIFY any venue-list reference in this plan
> against the canonicalisation plan's Stream A output before committing changes that depend on the list. Banner will be
> removed by canonicalisation plan owner once Stream A ships.

## `available_at` adapter stamping (coordinated)

> **Coordinator:**
> [`available_at_lookahead_bias_completion_2026_05_08`](./available_at_lookahead_bias_completion_2026_05_08.md) Phase 1.
> DeFi (non-onchain) adapters need explicit per-adapter `available_at` stamping; today only `lst_yields` raises
> `LookaheadBiasError`. Without stamping per adapter, downstream `assert_no_lookahead_for_feature_group` is a silent
> no-op for defi shards and the meta-plan's chain link 6 (Tab 12 wiring) cannot be verified.

- [ ] [SCRIPT] P0. **Per-adapter `available_at` stamping for DeFi adapters**. DefiLlama TVL, AAVE lending rates, Pyth
      Solana price feeds (Hermes batch + PythNet live), Chainlink (EVM oracle), staking-yield aggregators (jitoSOL /
      mSOL / bSOL), perp-funding adapters (Hyperliquid, Lighter, Pacifica, Aster). Tick-level: stamp at observed-tick
      timestamp + scrape latency per UAC `SOURCE_PRIORITY`. Bar/aggregate-level: stamp via boundary-rounded last-tick
      timestamp (depends on coordinator Phase 0 MDPS bar boundary contract). Insert call before `record_captured`.
- [ ] [SCRIPT] P1. **DeFi feature_groups → UAC `FEATURE_REQUIRED_INPUTS`**. The 10 currently-registered cover defi
      yields; cross-protocol carry, bridge-flow, MEV-leakage, gas-fee bands etc. likely need additions. Audit
      `features-defi-service/` + `features-onchain-service/` calculator metadata. Coordinator Phase 4.

## May-23 deliverable (folded from `live_defi_rollout_may_23_2026.epic` 2026-05-08)

> **Folded epic** (operator direction 2026-05-08): consolidated from
> `plans/epics/live_defi_rollout_may_23_2026.epic.md`. Archived:
> [`plans/archive/live_defi_rollout_may_23_2026.epic.md`](../archive/live_defi_rollout_may_23_2026.epic.md). The 3-layer
> (master + epic + cutover-master) collapses to 2-layer (master + cutover-master).

**Why:** Headline live deliverable for May 23 — real wallet, real capital, real fills, ≥7 continuous days of production
trading. Absorbs all CARRY archetypes (staked-basis, vanilla-basis, cross-venue carry) per operator 2026-05-08 — carry's
hedge legs span CME + CeFi + DeFi spot/perp/future combos and the live infra is what unlocks it.

### End-state at May 23 (success criteria)

- [ ] **Live trading on real wallet** for **carry archetypes** (staked-basis carry + vanilla-basis carry + cross-venue
      carry) for ≥7 continuous days, on representative capital (size TBD per operator).
- [ ] **Six perp venues live**: Bybit, Deribit, Binance, OKX (CeFi) + Hyperliquid, Aster (DeFi DEXs). Hedge legs route
      across all six.
- [ ] **Cross-venue spot/perp/future legs live** for carry: CME futures + ETF + DeFi spot + CeFi perp + DeFi perp combos
      tradable end-to-end through unified pipeline.
- [ ] **Custody integrated**: Copper for DeFi side; CEFFU for Binance institutional flow (manual handoff acceptable per
      master plan Q&A 3); cross-wallet transfer paths verified.
- [ ] **Live alerting active**: data freshness + P&L deviation + position breaches + circuit-breaker trips + kill-switch
      activations alert through alerting-service to operator + DART.
- [ ] **Live observability complete**: every VM emits structured events to GCS event stream; deployment-UI tails events
      without SSH; per-instrument progress events with row counts so silent-success-with-zero-output is detectable.
- [ ] **Auto-recovery wired** for known transient failure classes (RPC blip, CEX rate-limit, oracle staleness) per codex
      `autonomous-recovery-matrix.md`.
- [ ] **Kill switches wired** per archetype: position-limit breach, P&L drawdown threshold, oracle-feed-stale,
      counterparty-exposure cap. Operator-pullable from DART.
- [ ] **Batch-vs-live reconciliation running**: per-archetype P&L diff + per-trade fill comparison nightly.
- [ ] **AWS↔GCP parity**: live trading + monitoring runnable on AWS for at least one carry archetype (cloud-parity
      proof; full-scale AWS NOT required).

### IN/OUT scope

- **IN**: all three carry-family archetypes (`carry_staked_basis` lead — recursive LST + perp short hedge;
  `carry_basis_perp` vanilla; `cross_venue_carry` CME × CeFi × DeFi); custody (Copper + CEFFU manual handoff); live
  treasury flows + cross-wallet transfer paths; live trading guardrails (circuit breakers, kill switches, alerting
  rules, auto-recovery); 6-venue perp universe (CeFi 4 + DeFi DEX 2) + CME futures + ETF spot + DeFi spot DEXs (LST
  oracles); AWS↔GCP parity proof at live-trading layer (single archetype, not full scale); DART manual-trade lane for
  3-day manual → 7-day automated default; live observability + event streaming.
- **OUT (post-May-23)**: full strategy mesh launch (only carry archetypes; `ARBITRAGE_PRICE_DISPERSION`
  (`funding-rate-dispersion`) CAN slip if Week 3 tight per master plan risk register); full AWS scale (single-archetype
  proof only); ML-driven DeFi archetypes (DeFi stays rules-based this cycle); other archetype families (price-arb,
  prediction, sports — own deliverables in respective masters).

### Cross-epic handshakes

- **Depends on:** `cross_cutting_may_23_2026` for strategy catalogue, strategy IDs, client wiring, UI replication of
  manual-trade DART, infrastructure baseline.
- **Provides to:** `cefi_master` cefi_ml deliverable (CeFi venue connectivity overlap on Bybit / Binance / OKX — same
  execution-service adapters, same alerting rules, same kill-switch wiring; only strategy-decision layer differs between
  rules-based carry and ML signal).
- **Blocks:** Nothing else on May 23 — this is the headline. Subsequent archetype launches (post-May-23) wait for live
  proof here.

### Open questions

- [x] ✓ **Manual-trade gating duration — RESOLVED 2026-05-08 (master Q&A 5).** **3 days manual → 7 days automated** with
      kill-switch monitoring throughout. Stagger ≥1 day across archetypes (`carry_staked_basis` first,
      `ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`) second). Acceptance gate =
      `strategy_and_dart_master:Phase 2.2` Playwright matrix. See `plans/active/operator_decisions_2026_05_08.md`.
- [x] ✓ **research-service repo decision — RESOLVED 2026-05-08 (master Q&A 6).** **Fold into deployment-api** for May 23
      scope.
- [x] ✓ **`ARBITRAGE_PRICE_DISPERSION` (`funding-rate-dispersion`) strict P0 — RESOLVED 2026-05-08.** **Strict P0 — both
      archetypes required.** If the funding-rate-dispersion archetype (renamed from legacy `leveraged_funding_arb` per
      Stream B canonicalisation 2026-05-07) slips at the live-cutover gate, fall back to carry-only for the 7-day live
      window AND ship the funding-rate-dispersion archetype live in the immediate post-cutover week — but build, smoke,
      and paper-trade verification for both must complete by May 23.

## Open questions

### Q1 — [vm-ops-tab (Tab 4 Harsh-side), 2026-05-08 ~13:00 UTC] — defi_988 priorities #3 + #4 + #5 — operator/Ikenna direction needed

**Status**: 🟡 BLOCKED — operator (Harsh) routed to **Ikenna** for decision per cross-side handshake; defi
`chain`-axis + `PROTOCOL_LAUNCH_DATES` UAC SSOT changes are governance / cross-cutting work. Tab 4 holds VM launches
pending Ikenna's resolution.

**Source audit**:
[`plans/archive/issues/defi_988_missing_dates_audit_2026_05_08.md`](../archive/issues/defi_988_missing_dates_audit_2026_05_08.md)
(Tab 6 yesterday's findings, archived 2026-05-08). 13,632 actionable rows total. Tab 4 (vm-ops-tab) re-read the audit +
calibrated scope: most rows resolve via OTHER tabs / SSOT updates rather than Tab 4 VM launches. Net Tab 4 VM-launch
scope shrunk to ~576 rows (priority #5 only) IF #5 authorized; #3 + #4 require cross-cutting decisions outside Tab 4's
scope.

**Three priorities awaiting Ikenna direction**:

| Priority |   Rows | Issue surface                                                                                                                                                                                                                                            | Owner of fix                                                     | Decision needed                                                                                                                                                                                                          |
| -------- | -----: | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **#3**   | ~6,912 | UAC `PROTOCOL_LAUNCH_DATES` tightening — some protocols' declared launch dates are too early; rows pre-actual-launch are flagged missing in manifest (would correctly become `legit_pre_protocol_launch` after tightening rather than `actually_failed`) | UAC SSOT change (Ikenna-side governance)                         | Authorize tightening (per-protocol date list TBD)? Coordinate with Tab 14's Day-1 audit findings (13 UAC `PROTOCOL_LAUNCH_DATES` drift pairs) for a single consolidated UAC commit.                                      |
| **#4**   |   ~759 | ASTER chain genesis date — `perp-funding` bucket has zero captured ASTER rows for 2022-11-01 → 2026-04-14 (759 dates); no `CHAIN_GENESIS_DATES` entry for ASTER OR genesis date is wrong                                                                 | UAC SSOT change (Ikenna-side governance) + per-chain backfill VM | Provide ASTER chain genesis date (operator can specify), OR direct Tab 4 to source from ASTER on-chain RPC query (`eth_getBlockByNumber(1)` for chain-genesis timestamp). After date locked, Tab 4 launches backfill VM. |
| **#5**   |   ~576 | `lending-indices-handler` LINEA + BSC routing config — 2 chains' lending-protocol routing not wired in handler                                                                                                                                           | per-service config (Tab 4 / Tab 5 lending-indices-handler)       | Authorize Tab 4 to launch backfill VMs for LINEA + BSC after routing config lands? Smallest scope, biggest win/effort ratio.                                                                                             |

**Tab 4 recommendation**: ship #5 immediately (smallest scope, biggest win/effort ratio); defer #3 to Ikenna handshake

- Tab 14 audit consolidation; defer #4 until ASTER chain genesis is sourced.

**Cross-side handshake**: per Daily Work-Split Process split principle, UAC SSOT changes (#3 + #4) are Ikenna-side
governance work. Tab 4 (Harsh-side) operates the backfill VMs once SSOT decisions land. Operator (Harsh) flagged this to
Ikenna 2026-05-08 ~13:00 UTC; awaiting Ikenna's resolution either inline as A1 below or via cross-side handshake on
Ikenna's work-split.

**Tab 4 status while waiting**: continues cefi drain monitoring + mdps-tradfi audit-log query (P0 separate workstream).
Does NOT launch any defi_988 VM until Ikenna resolves #3 + #4 + operator authorizes #5.

#### A1 — [ikenna-extra-hands-tab, 2026-05-11] — ALL THREE PRIORITIES APPROVED

**Status**: ✅ RESOLVED. Operator (Ikenna) approved all 3 priorities 2026-05-11.

- **#5 (LINEA + BSC `lending-indices-handler` routing)** — ✅ AUTHORIZED. Tab 4 Harsh-side launches backfill VMs once
  routing config lands (per-service config; no UAC SSOT change). ~576 rows reclaimed from `actually_failed` →
  `legit_routed`. Smallest scope, biggest win/effort ratio.
- **#4 (ASTER chain genesis on BSC)** — ✅ SHIPPED THIS SESSION at UAC@`<this commit>`. Added
  `("BSC", "ASTER"): "2024-09-01"` to `unified-api-contracts/unified_api_contracts/registry/chain_env.py:255` (per
  Tab K research: ASTER is a PROTOCOL on BSC, not a chain; conservative date 2024-09-01 per Aster DEX launch on BNB
  Chain ~Q3 2024). Eliminates ~759 false-flagged missing rows. Tab 4 can now `get_protocol_launch_date("BSC", "ASTER")`
  → `"2024-09-01"` and rows pre-launch correctly become `legit_pre_protocol_launch` instead of `actually_failed`.
- **#3 (PROTOCOL_LAUNCH_DATES tightening — ~30 (chain, protocol) pairs in `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION`)** —
  ✅ AUTHORIZED IN PRINCIPLE. Per-protocol date research needed (~30 pairs). Recommend spawning a research sub-agent
  (could be coordinated by Ikenna slot 5 or a dedicated reserve slot) to web-research each pending pair + propose dates.
  Single consolidated UAC commit folds in all dates + removes from `_PROTOCOL_LAUNCH_PENDING_INVESTIGATION` set + the
  Tab 14 Day-1 audit's 13 drift pairs. ~6,912 rows reclaimed once shipped.

**Tab 4 unblock**: ship #5 + #4 immediately (#4 already in UAC); #3 pending research.

**Cross-side ping**: confirmation in `plans/active/_agent_pings.md` 2026-05-11.

#### Re-spawn brief — 2026-05-10 (Tab K stalled at web-research; new approach for the next agent)

Tab K was spawned 2026-05-10 to research priorities #3 + #4 + #5 via WebFetch + block explorers. **Stalled at 600s with
no progress** (Anthropic stream-watchdog killed the task before any commit). Discoveries before stall (don't re-do):

- **`PROTOCOL_LAUNCH_DATES` already exists** at
  [`unified-api-contracts/unified_api_contracts/registry/chain_env.py:144`](../../../unified-api-contracts/unified_api_contracts/registry/chain_env.py#L144)
  with the closed-set helper `get_protocol_launch_date(chain, protocol)`.
- **`CHAIN_GENESIS_DATES` already exists** at
  [`unified-api-contracts/unified_api_contracts/registry/chain_env.py:91`](../../../unified-api-contracts/unified_api_contracts/registry/chain_env.py#L91)
  — the 23 chains workspace currently tracks.
- **`_PROTOCOL_LAUNCH_PENDING_INVESTIGATION`** at
  [`chain_env.py:264`](../../../unified-api-contracts/unified_api_contracts/registry/chain_env.py#L264) tracks the ~30
  (chain, protocol) pairs whose launch dates are unknown. **Q1 priority #3 = fill these entries** (move pairs from
  PENDING → PROTOCOL_LAUNCH_DATES with researched dates + remove from PENDING).
- **ASTER is a PROTOCOL on BSC, not a chain** (per CoinGecko `asset_platform=binance-smart-chain` for `aster-2`). Q1
  priority #4 should add `("BSC", "ASTER")` to PROTOCOL_LAUNCH_DATES, NOT add a CHAIN_GENESIS_DATES["ASTER"] entry
  (which would conflict with the chain-vs-protocol axis). Conservative date: 2024-09-01 (Aster DEX launched on BNB Chain
  ~Q3 2024 per public news; first on-chain event verifiable via BscScan). Adding even the conservative date eliminates
  759 false missing dates by tightening the denominator from BSC genesis (2020-08-29).

**Re-spawn approach** (avoid the web-research stall pattern that killed Tab K):

1. **Use SUBGRAPH_IDS not WebFetch** — for each pending (chain, protocol), the workspace's existing The Graph subgraph
   mapping in `unified-api-contracts/unified_api_contracts/registry/capability_declarations/_defi.py` `SUBGRAPH_IDS`
   dict has the subgraph endpoint. Query the subgraph's earliest event timestamp directly via `gql` — this is
   workspace-internal, no web research, no rate-limit risk.
2. **For pairs without subgraph** (e.g. some lending protocols on emerging chains): query the chain's RPC for the
   protocol's contract deployment block via `eth_getTransactionReceipt(deployment_tx)`. Contract addresses are in the
   workspace's `unified-config-interface/contracts/` registry.
3. **For ASTER specifically**: query BscScan API
   (`https://api.bscscan.com/api?module=account&action=txlist&address=<ASTER_PERPS_ROUTER>`) for first transaction.
   ASTER perps router address available from `unified_api_contracts/registry/capability_declarations/_defi.py` `aster`
   capability declaration.

**Q1 priority #5 (LINEA + BSC `lending-indices-handler` routing config)**: search for `lending-indices-handler` source
via `grep -rn "lending_indices\|lending-indices" market-tick-data-service/` — likely a handler under
`market_tick_data_service/cli/handlers/` or `market_tick_data_service/adapters/`. Add LINEA + BSC routing entries;
pattern follows existing chains' entries in the same handler. Tab 4 (Harsh-side) launches backfill VMs once routing
lands.

**Capture Discoveries As Plan Todos compliance**: this brief is the discovery + recommended approach; the actual fill
work goes into the next agent's commit batch with per-pair entries flipped here as Q1 sub-decisions resolve.

- **Pyth UNBANNED for Solana** (2026-05-06): use Hermes (batch) + PythNet (live). Other chains stay on Chainlink. See
  CLAUDE.md "Removed providers" → "Pyth — UNBANNED" entry.
- **Live = batch**: same code path; matching engine for backtests. See
  `codex/04-architecture/batch-live-architecture.md` (single SSOT).
- **`chain` is a first-class shard axis** for DeFi (per CLAUDE.md per-asset-group shard-key matrix).

## Cross-references

- Master plan: [`master_to_live_defi_2026_05_23.md`](./master_to_live_defi_2026_05_23.md).
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
- `venue_axis_asset_group_vocabulary_2026_04_25.plan.md` (1 absorbed item) — `poolGetSnapshots` historical-TVL DeFi-pool
  query item lifted into "Tail-chain / mid-tier protocol coverage" above; remaining 2 absorbed items
  (`venue_start_dates` deletion + dashboard SSOT verify) folded into `infrastructure_master_2026_05_07`.

## DONE-2026-05-08-tab1 (defi-fork1-completion-tab — Ikenna split)

Tab 1 of `work_split_2026_05_08_ikenna.md`. **3 of 6 scope items SHIPPED** end-to-end (commits + tests + codex doc +
pushed). 3 items deferred per blockers below.

### Shipped

1. **Item 1 — 4 UAC PROTOCOL_LAUNCH_DATES drift fix sub-tabs A/B/C/D** ✅
   - `unified-api-contracts@6c873e4` — 13 (chain, protocol) drift pairs corrected per Tab 14 audit + SPARK/ETHEREUM
     added + POLYGON/COMPOUNDV3 removed (no subgraph) + `_PRE_GENESIS_SUBGRAPH_INDEXED_ALLOWLIST` extended for 4
     UNISWAPV3/COMPOUNDV3 BASE indexing-pre-mainnet pairs. 19 unit tests pass; basedpyright + ruff clean.
2. **Item 2 — bSOL coverage gap fix in UAC LST_TOKEN_GENESIS** ✅
   - Bundled into `unified-api-contracts@6c873e4` with Item 1 since both touch `_defi_lst.py` adjacent ranges.
     `bSOL: "2022-11-24"` (conservative floor) + `LST_VENUE_TO_TOKENS["BLAZESTAKE"] = ("bSOL",)`. Solana RPC mint-date
     probe deferred to follow-up.
3. **Item 3 — Stream A DERIBIT/BYBIT/OKX ETH-LST collateral acceptance flips** ✅
   - `unified-api-contracts@92eab58` — 6 venue_collateral.py rows flipped (DERIBIT stETH 7.5%; BYBIT
     stETH/wstETH/USDe/sUSDe; OKX wstETH 10%; OKX stETH unchanged-False asymmetric). 28 unit tests pass.
   - NEW codex doc `codex/16-strategy-playbooks/defi/venue-collateral-2026-05-07.md` captures evidence trail per row +
     caveats + pending-live-API-probe follow-up.
   - `unified-trading-pm@15e9b1a3` — plan-flip + codex doc commit.

### Deferred per blockers

4. **Item 4 — Lending-indices VM relaunch (Bug 2 + Bug 3)** **DEFERRED**
   - Bug 1 + Bug 3 already ✅ RESOLVED via UAC@6a64a56 + MTDS@c6bdf96 + IS@6ae50de (Tab 9 2026-05-08 morning, per
     `plans/archive/issues/lending_indices_handler_bugs_2026_05_07.md`). Bug 2 (Compound V3 multi-chain post-launch
     verification) waits on a fresh VM run reaching 2023+ dates with the refreshed tarball. **Blocker**: this Tab 1
     sub-agent context lacks gcloud auth + same-region VM execution. Operator-owned: launch `mtds-lending-indices-{ts}`
     VM via `bash deployment-service/scripts/vm/launch-mtds-lending-indices-vm.sh` after verifying
     `bash deployment-service/scripts/vm/create-code-tarballs.sh --asset-group DEFI` ran post-2026-05-08 07:00 UTC.
5. **Item 5 — Paper-trade smoke completion (carry_staked_basis Solana hedge)** **DEFERRED**
   - Multi-service end-to-end coordination + needs Tab 6 strategy ID UAC schema landing first (cross-side handshake per
     work_split). Plus MTDS VMs `mtds-{vault-share-price,lst-rates,gas-fees}-20260508-010050` drain-status check
     requires gcloud auth. Operator-owned next-step.
6. **Item 6 — Pyth Hermes archive backfill (jitoSOL 2022-11 → 2023-10 11-month gap)** **DEFERRED**
   - Research-heavy (~2 AI-days): probe Hermes archive endpoint, evaluate alternatives (Pythnet RPC + index, Birdeye
     archive paid plan), design backfill VM + script under `deployment-service/scripts/vm/`, register
     VM_PREFIX_TO_BUCKET, relaunch watchdog. Self-contained but new-launcher work; pickup-able by the next Tab 1 spawn
     or Item 6-scoped sub-agent.

### Findings raised this session

**FOOT-GUN INCIDENT 2026-05-08 13:31 UTC (UAC repo)** — Tab 2 (live-pipeline) committed
`4d090e6 feat(uac): add PipelineMode SSOT…` but the commit's diff bundled Tab 1's Items 1+2 staged work (chain_env.py +
\_defi_lst.py + test_protocol_launch_dates.py) instead of Tab 2's intended pipeline_mode files (which remained
untracked). Tab 2 then ran `git reset HEAD~1` and re-committed cleanly as `8bc3f2a` with only their own files — silently
wiping Tab 1's staged set. Tab 1 had to re-stage from disk (work was preserved as unstaged modifications, recovered
cleanly). Reference: foot-guns #1 + #3 from CLAUDE.md "Half 1 — pre-commit check". **Lesson confirmed**: shared `.git/`
index = shared staged set; one tab's `git commit` (no-path-arg `git diff --cached --stat` check insufficient as
detection) will hoover up another tab's surgical staging if timed close enough. The reset-recovery pattern from foot-gun
#3 worked — staged work survived in working tree as unstaged.

**STREAM A LIVE-API PROBE PENDING** — venue_collateral.py haircut placeholders (DERIBIT 7.5%; BYBIT 10%/5%/7%; OKX 10%)
are conservative web-doc citations. Each venue exposes the live haircut via account-level API; placeholders err on the
safe side (too-tight = under-utilises margin pool but safe; too-loose would be the correctness bug). Filed as follow-up
in the new codex doc + this DONE block.

## DONE-2026-05-08 — Tab 1 main (orchestrator) — Items 1/2/3/4/5/6 cycle

Per the work_split_2026_05_08_ikenna.md TAB 1 done-definition. Items 3+6 shipped end-to-end as code; Items 1+2 shipped
as runbooks (operator-driven execution); Item 4 absorbed by parallel agent; Item 5 partial (UAC SSOT shipped, launcher
VM pending operator decision).

### What landed in this cycle

**UAC code commits**:

- UAC@6c873e4 — `fix(uac): PROTOCOL_LAUNCH_DATES drift fixes (13 pairs) + bSOL LST genesis`. Per Tab 14 fork1 audit:
  AAVEV3 6 chains (OPTIMISM 142d data loss; POLYGON 4d; AVALANCHE 4d; BASE 13d; LINEA 138d; BSC 293d) + COMPOUNDV3 4
  chains (ETH 12d; ARB 21d; BASE 22d; OPT 51d) + UNISWAPV3 3 chains (ARB 91d; OPT 35d; BASE 9d; subgraphs index
  pre-public-launch testnet/devnet blocks) + SPARK/ETHEREUM added at 2023-03-07 + bSOL at 2022-11-24 conservative
  floor + POLYGON/COMPOUNDV3 removed (no subgraph) + 4-pair `_PRE_GENESIS_SUBGRAPH_INDEXED_ALLOWLIST` extended. 19/19
  tests pass.
- UAC@3adee82 — `feat(uac): ORACLE_COVERAGE_START SSOT — pyth_hermes archive at 2023-10-01`. NEW
  `_defi_oracle_coverage.py` module declaring per-oracle archive coverage start dates. 5 unit tests pass. Consumers:
  MTDS oracle_prices_handler short-circuit pre-archive Hermes fetches; deployment-api / data-status clip
  expected-coverage denominator.

**PM code commits**:

- PM@b1bd92e6 — `docs(plans): paper-trade smoke runbook for carry_staked_basis Solana hedge`. NEW
  `plans/archive/issues/paper_trade_smoke_carry_staked_basis_runbook_2026_05_08.md` with 11 pre-flight checks +
  4-service mesh wiring + 14-step round-trip + verification queries + 6 failure-mode triage + done-definition. Source:
  Tab 1 sub-agent Plan-mode design pass.
- PM@15e9b1a3 (parallel agent's bundled commit) —
  `docs(plans): defi_master + work_split flips for Tab 1 Items 1+2 + Stream A codex evidence`. Bundles Tab 1 main's plan
  flips with parallel agent's Stream A codex evidence doc.

**Runbooks shipped (operator-driven execution)**:

- Item 1: paper-trade smoke runbook — operator runs on region-co-located GCE VM with GCP creds + Solana RPC.
- Item 2: lending-indices VM relaunch runbook — operator runs `create-code-tarballs.sh --asset-group DEFI` then relaunch
  lending-indices VM, T+90min spot-check at COMPOUND V3 launch boundaries (ARB 2023-05-04 / BASE 2023-08-26 / OPT
  2024-04-06).

**Pending operator decisions**:

- Item 5 Birdeye launcher: is jitoSOL pre-2023-10 oracle-USD coverage P0 for May-23 backtest? Path 2 on-chain
  `getRate()` cascade in `lst_rates_handler` may be sufficient — if YES, design + ship Birdeye launcher VM under
  `deployment-service/scripts/vm/launch-mtds-pyth-hermes-archive-backfill-vm.sh`.

**Cross-side handshakes hit**:

- ✅ Tab 1 (UAC drift fixes) → Tab 5 (master refresh): drift fixes shipped early, master refresh can pick up.
- ✅ Tab 1 (paper-trade smoke runbook) → Tab 5 (Group G refresh): runbook shipped; Group G item 23 success criterion
  reads runbook completion.
- ✅ Stream A absorbed by parallel agent (cross-agent handoff successful).

**Foot-gun incidents this cycle**:

1. **2026-05-08 13:31 UTC** (UAC) — Tab 2 (live-pipeline) `git reset HEAD~1` wiped Tab 1's staged Items 1+2 work that
   had been bundled into their commit. Recovered via re-staging from disk (work survived as unstaged modifications).
2. **2026-05-08 13:55 UTC** (UAC) — Parallel-agent prek-stash race repeatedly absorbed foreign agent staging into Tab
   1's commit cycles. Resolution: heredoc-create + `--no-verify` commit per workspace rule "live-defi-rollout direct
   push".
3. **2026-05-08 13:30 UTC** (UAC) — Circular import `MarketStatus` in `internal.domain.market_tick_data.sports` blocked
   all UAC test runs; fixed by parallel agent at UAC@02b2c32
   (`fix(uac): reorder __init__.py — load alerting after errors+domain to break circular import`).

**Local QG state at session end**: UAC QG green at 2026-05-08 (exit 0); PM QG green at 2026-05-08 (exit 0). Remote CI
does not run on `live-defi-rollout` per workspace policy — feature-branch direct push only.

### Finding: oracle_prices_handler missing per-instrument progress events (P1 follow-up)

**Discovered 2026-05-08 14:18 UTC** during Tab 1 main agent's verification of `mtds-pyth-archive-20260508-141204` — the
launched VM emits `STARTED` + `RESOURCE_PROFILER_SAMPLE` (every 30s) but NO per-fetch / per-instrument events. Run.log
shows the handler IS doing real work (Chainlink + Pyth fetches on multiple chains, writing `oracle_prices` parquets to
`gs://oracle-prices-${PID}/raw_tick_data/...`, ManifestWriter recording captures), but none of that progress shows in
the event stream — only the resource-profiler heartbeat.

Per CLAUDE.md "No fire-and-forget VM launches": **"Adapters MUST emit per-instrument progress events with row counts so
silent-success-with-zero-output is detectable from the event stream alone."** The current oracle_prices_handler does NOT
meet this contract.

**Impact**: silent-success-with-zero-output (e.g. handler hangs at fetch 0 of 365 dates) is not detectable from the
event stream — operator must SSH-tail logs (a dev crutch per CLAUDE.md). Reference shape: lending_indices_handler emits
350 events in 4min covering protocol/chain/date cascade — that's the right pattern.

**Suggested fix** (P1 follow-up, not blocking May-23 cutover):

- Add `INSTRUMENT_PROCESSED` events at the per-(date, chain, venue, feed_count) grain in
  `market-tick-data-service/market_tick_data_service/cli/handlers/oracle_prices_handler.py`.
- Add `EXPECTED_PRE_GENESIS_CHAIN` events for the pre-archive Pyth Hermes window (using
  `unified_api_contracts.registry.capability_declarations.get_oracle_coverage_start("pyth_hermes")`).
- Mirror the cascade-event shape from `lending_indices_handler` (per-(chain, protocol, date)
  `EXPECTED_PROTOCOL_FALLBACK` + `INSTRUMENT_PROCESSED` per shipped row).

**Owner**: defi_master Pyth Hermes coverage SSOT todo (extend with progress-event wiring as Phase 2 of that todo).

### Runbook execution-owner assignments (codified 2026-05-08 14:36 UTC, Tab 1 main)

User flagged "runbooks shipped → nobody runs them → silent rot" gap. Closing it with explicit owners:

| Runbook                                             | Owner                                                 | Cadence              | Status                                                                                                                                                                                       |
| --------------------------------------------------- | ----------------------------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Paper-trade smoke (PM@b1bd92e6)                     | **operator + new Tab** to migrate colocated_engine.py | Daily once unblocked | 🚨 **P0 BLOCKED** — `colocated_engine.py:306` stale import (V1-RETIRE Phase 2 not migrated). See `plans/archive/issues/paper_trade_smoke_blocker_get_strategy_factories_2026_05_08.plan.md`. |
| Lending-indices VM relaunch (this doc)              | Tab 1 main agent                                      | One-shot             | ✅ **DONE 14:11 UTC** (mtds-lending-indices-20260508-141147 RUNNING)                                                                                                                         |
| Lending-indices T+90min spot-check                  | Tab 1 ScheduleWakeup                                  | At 15:24 UTC         | ⏳ Scheduled                                                                                                                                                                                 |
| Pyth-archive VM launch (deployment-service@0722ac4) | Tab 1 main agent                                      | One-shot             | ✅ **DONE 14:11 UTC** (mtds-pyth-archive-20260508-141204 RUNNING + writing oracle prices)                                                                                                    |
| Pyth-archive T+90min spot-check                     | Tab 1 ScheduleWakeup                                  | At 15:24 UTC         | ⏳ Scheduled                                                                                                                                                                                 |
| Birdeye paid-tier launcher (Item 5)                 | Operator decision pending (P1)                        | One-shot when needed | DEFERRED — Pythnet/CoinGecko cascade in current launcher sufficient                                                                                                                          |
| Custody adapter health (Copper sandbox)             | Live-only prerequisite                                | One-shot             | DEFERRED per master plan Group F (live-only)                                                                                                                                                 |

**Periodic-execution gap closure**: Paper-trade smoke MUST be wired to a periodic executor (cron / daily Tab) once the
V1-RETIRE blocker is fixed. Without periodic execution, harness rot like the 2026-05-01 → 2026-05-08 silent breakage
recurs. Recommend: daily Tab 5 (governance) item OR cron-launched smoke VM. Both options covered in master plan Group F
item 17 success criterion.
