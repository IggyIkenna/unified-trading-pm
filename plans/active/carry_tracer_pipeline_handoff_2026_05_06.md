---
plan_type: handoff
asset_group: defi
owner: ikenna
created: 2026-05-06
locked_by: live-defi-rollout
locked_since: 2026-05-06
name: carry-tracer-pipeline-handoff-2026-05-06
status: active
supersedes: carry_tracer_pipeline_handoff_2026_05_05.md
---

# NEXT-AGENT PROMPT — Carry tracer pipeline (Session 2 — 2026-05-06)

> Picking up from yesterday's handoff (`carry_tracer_pipeline_handoff_2026_05_05.md`). Today's session went deep on the on-chain feature pipeline + uncovered three new schema-drift classes the user's strategies need fixed. **Read this whole file before any action**. Eight VMs are still running and will finish overnight; don't relaunch them.

## TL;DR — what changed today

- **Stage 2 on-chain side ALL PASS**: lst_yields (465 rows / 31 days), lending_rates (2.03M rows / 99.9% direct on-chain liquidity_rate), MTDS lending_indices (1.8M rows / 8× pagination uplift). All three feature groups have real values written to the canonical `gs://features-onchain-central-element-323112/by_date/day=*/feature_group=*/features.parquet` paths for 2026-03-15..04-14.
- **Stage 3 partial tracer ran end-to-end** for 3 archetypes — but every slot returned `skipped_reason` due to schema drift between tracer column expectations and feature output. Pipeline alive; just needs adapter layer.
- **Eight VMs still running** (MDPS × 4 for CEFI 30-day reprocess, Deribit-light × 3 for futures+options backfill 2024/2025/2026, plus your 82 cefi-* venue backfills you launched separately). They'll keep grinding overnight.
- **Architectural audit done** identifying three distinct layers of follow-up work + greenfield CARRY_BASIS_DATED enablement.

## Commits shipped today on `origin/live-defi-rollout`

| Repo | Commit | What |
|---|---|---|
| market-tick-data-service | `2a9b638` | Aave V3 lending_indices captures `liquidityRate` + `reserveFactor` per tick |
| market-tick-data-service | `459825d` | Field-name fix `optimalUsageRatio` → `optimalUtilisationRate` (British spelling — Aave V3 / Messari schema). Earlier `fba1afe` had wrong name → 0 Aave V3 rows for whole 30-day window. |
| market-tick-data-service | `c2b23d3` | Cursor pagination + INSTRUMENT_PROCESSED + LENDING_DAY_COMPLETE + EXPECTED_PROTOCOL_FALLBACK on instruments 404. **Pagination uncovered 8× more data** (1.8M rows vs 7.5k/day cap — 95% was being silently truncated). |
| market-tick-data-service | `fba1afe` | (predecessor of 459825d) Captures all 5 rate-model params per Reserve sub-selection on `reserveParamsHistoryItems` |
| unified-api-contracts | `c9ea9e6` | UAC SSOT for Aave V3 per-asset rate model defaults (7 assets) — `AAVE_V3_RATE_MODEL_DEFAULTS_BY_ASSET` + `get_aave_v3_rate_model_defaults` |
| features-onchain-service | `955abb5` | Per-day write fix (Blocker 1) + `liquidity_rate→aave_supply_apy` rename + per-row reserve_factor synthesis + `LENDING_INPUT_DIAGNOSTIC` event |
| features-onchain-service | `fd18d41` | Refactor: `aave_rate_impact_calculator` imports rate-model defaults from UAC SSOT. Removes duplicated hardcodes. |
| features-onchain-service | `c90d01a` | **Path-prefix fix**: reader probes canonical `raw_tick_data/by_date/day=DATE/` first, falls back to legacy `day=DATE/`. Without this, lending_rates was reading old pre-pagination data (0.4% direct on-chain rate; post-fix 99.9%). |
| features-delta-one-service | `3f0f76c` | (yesterday's subagent) Persist-events port from features-onchain `266f512`: PERSISTENCE_COMPLETED at upload site with `rows_written`, FEATURE_WRITE_REJECTED with `reason` enum. |
| deployment-service | `4756d16` | `launch-mtds-lending-indices-backfill-vm.sh` singleton-locked launcher + watchdog `mtds-lending-indices-` prefix |

PM (this repo) — handoff doc + session memory only.

## VMs running RIGHT NOW (don't relaunch)

| VM | Purpose | ETA from launch | Output bucket |
|---|---|---|---|
| `mdps-backfill-cefi-20260506-161103` | MDPS CEFI 2026-03-17..03-23 (7d) | ~3hr | `market-data-tick-cefi-{pid}/processed_candles/` |
| `mdps-backfill-cefi-20260506-161117` | MDPS CEFI 2026-03-24..03-30 (7d) | ~3hr | same |
| `mdps-backfill-cefi-20260506-161135` | MDPS CEFI 2026-03-31..04-06 (7d) | ~3hr | same |
| `mdps-backfill-cefi-20260506-161149` | MDPS CEFI 2026-04-07..04-14 (8d, includes funding_oi target 04-09) | ~3hr | same |
| `cefi-deribit-2024-light-20260505-152418` | Deribit `derivative_ticker;options_chain;futures_chain` 2024 | hours | `market-data-tick-cefi-{pid}/raw_tick_data/by_date/day=*/asset_group=cefi/venue=DERIBIT/instrument_type={future,futures_chain,option,options_chain}/` |
| `cefi-deribit-2025-light-20260506-191740` | Same 2025 | hours | same |
| `cefi-deribit-2026-light-20260506-191740` | Same 2026-01..04-17 | hours (includes 30-day window) | same |
| 82× `cefi-binance/bybit/...` | User's separate raw market-data full-history backfill | days | `market-data-tick-cefi-{pid}/raw_tick_data/by_date/day=*/asset_group=cefi/venue=*/...` |

**Verification protocol after each VM completes** (per CLAUDE.md no-fire-and-forget rule):

```bash
# events check
gcloud storage ls "gs://central-element-323112-events/events/{service}/{YYYY-MM-DD}/{vm-name}/hour=*/"
# look for INSTRUMENT_PROCESSED + final summary event with rows_written>0; not just STOPPED
# cross-check against actual bucket output (sample a parquet, check row count + columns)
```

## What's left — three layers + one greenfield + funding_oi loader fix

### Layer 2 — fastest unblock (~30 min)

**Tracer schema adapters** in `strategy-service/scripts/trace_all_carry_archetypes.py`. Today's partial Stage 3 tracer ran cleanly but every slot returned `skipped_reason: "feature 'X' not present"` because:

| Tracer expects | features-onchain writes |
|---|---|
| `staking_apy_total` (fraction × 10000 = bps) | `staking_apy_bps` (already bps) |
| `(protocol, asset)` filter columns | `token` column (single string like `stETH`, `jitoSOL`) |
| `supply_apy` | `aave_supply_apy` |
| `(asset, chain)` filter columns | `instrument_id` like `AAVE_V3-ARBITRUM:LENDING:USDC` |
| `funding_rate_apy_bps` | `funding_rate_annualized` (per features-delta-one calculator output) |

**Fix shape** (write in tracer; data is correct, naming + grouping just needs adapter):
1. `_TOKEN_TO_PROTOCOL_ASSET` lookup table (stETH→(LIDO, ETH), wstETH→(LIDO_WRAPPED, ETH), rETH→(ROCKET_POOL, ETH), cbETH→(COINBASE, ETH), weETH→(ETHERFI, ETH), ankrETH→(ANKR, ETH), mETH→(MANTLE, ETH), swETH→(SWELL, ETH), ETHx→(STADER, ETH), osETH→(STAKEWISE, ETH), pufETH→(PUFFER, ETH), sUSDe→(ETHENA, USDE), sDAI→(SPARK, DAI), jitoSOL→(JITO, SOL), mSOL→(MARINADE, SOL))
2. `_resolve_yield_staking_simple` (line 293-323): use the lookup, read `staking_apy_bps` directly (no ×10000).
3. `_resolve_yield_rotation_lending` (line 452-490): regex-parse `instrument_id` pattern `{PROTOCOL}-{CHAIN}:LENDING:{ASSET}` → derive `asset` and `chain` columns inline; fallback chain `aave_supply_apy → supply_apy → lending_apy`.
4. Same fallback chain in `_resolve_arbitrage_price_dispersion` resolvers (line 551, 570).
5. funding_oi resolver (line 326): fallback `funding_rate_annualized → funding_rate_apy_bps → funding_apy_bps`.

After this: 6/7 archetypes (everything except CARRY_BASIS_DATED) produce real APY values flowing through the allocator → real ranking → real comparison parquet.

### Layer 1 — better long-term (~1-2 day)

**Calculator-side enrichment** in `features-onchain-service`:
- `lst_yields` calculator (`features_onchain_service/engine/orchestrator.py:_compute_lst_features_for_day`): emit `protocol` + `asset` columns alongside `token` (don't replace — add). Source the mapping from a UAC SSOT (file Phase 9 plan to add `LST_TOKEN_TO_PROTOCOL_ASSET` to `unified_api_contracts.internal.domain.defi`).
- `lending_rates` calculator (`features_onchain_service/engine/orchestrator.py:_calculate_lending_features`): regex-parse `instrument_id` to add `protocol` + `chain` + `asset` as separate columns (keep `instrument_id` for canonical reference). Rename `aave_supply_apy → supply_apy` (or emit BOTH for backwards-compat during transition).
- After landing + 30-day re-run: tracer adapter from L2 becomes safety net, not load-bearing.

### Layer 3 — greenfield (~2-3 day per item)

**`paired_price_dispersion` calculator** in `features-cross-instrument-service` (cross-asset-group is its mandate). Single calculator handles BOTH archetypes:
- Input: raw_tick_data spot/future/equity OHLC for catalog-defined (left_venue, left_root) + (right_venue, right_root) pairs
- Output: per-(left_venue, left_root, right_venue, right_root, day) → `spread_bps`, `annualised_apy_bps`, `days_to_expiry`
- Two consumers:
  - `CARRY_BASIS_DATED` filters spec rows where one leg is spot/ETF and the other is dated future (held to convergence/expiry)
  - `ARBITRAGE_PRICE_DISPERSION` filters spec rows where both legs are futures of same expiry on different venues (exit on convergence)

### Catalog updates per user's direction (this session, 2026-05-06)

User's instruction:

> "For the carry basis dated, don't remove the ones you have. Just add those ones that we've mentioned. and refactor the future to future cross venue stuff out of carry basis arb into price arb archetype that exists. and for the futures, for the commodities and things like that, you would need to do basically the ETF versus the futures for the basis to make sense there. We don't have all the instruments necessarily saved, based on instrument definitions. The ones that exist, you can still assume that we'll have, like, a gold ETF or something. At some point, I assume we will. If databento has it, then we should put it at some point, because this strategy catalogue is supposed to be universal."

**`CARRY_BASIS_DATED` (`strategy-service/.../target_universe/catalog.py:_build_carry_basis_dated`)** — keep all 7 existing specs, ADD:

| spot venue | future venue | asset | Notes |
|---|---|---|---|
| NASDAQ (IBIT) | CME (MBT) | BTC | US BTC ETF vs micro BTC future |
| NASDAQ (ETHA) | CME (MET) | ETH | US ETH ETF vs micro ETH future |
| DERIBIT (spot index) | DERIBIT (dated) | BTC | intra-Deribit basis (after 2026-light VM finishes) |
| DERIBIT (spot index) | DERIBIT (dated) | ETH | intra-Deribit basis |
| **Future ETF placeholders** (assume databento adds): GLD-CME-GC, USO-CME-CL, UNG-CME-NG, SPY-CME-ES, QQQ-CME-NQ — design specs now, leave instrument_id placeholders documented. User: "should follow the patterns that make sense in terms of the venues and instruments that they cover" |

**`ARBITRAGE_PRICE_DISPERSION` (`strategy-service/.../target_universe/catalog.py:_build_arbitrage_price_dispersion`)** — keep existing DeFi lending pair specs, ADD:

| long venue | short venue | asset |
|---|---|---|
| CME (MBT) | DERIBIT (dated) | BTC same expiry |
| CME (MET) | DERIBIT (dated) | ETH same expiry |
| (future) other cross-venue futures pairs — design pattern is venue × root × expiry-match |

**No changes to allocators** — `CarryBasisDatedRankAllocator` + `ArbitragePriceDispersionRankAllocator` already exist and just need the new spec rows + new calculator output. Decision-making (universe filter, score, threshold, top-N, weighting) is identical for added specs.

### funding_oi loader path drift in features-delta-one (separate fix)

After MDPS 30-day finishes, the funding_oi single-day VM will fail again unless we fix the features-delta-one loader. Per yesterday's diagnosis (`carry_tracer_pipeline_handoff_2026_05_05.md` Blocker 3), the `_load_pool_metadata_from_instruments` path or the underlying candle-loader uses an old layout. Real symptom (from VM `features-delta-one-cefi-backfill-20260506-163448` run.log):

```
404 GET .../processed_candles/by_date/day=2026-04-07/timeframe=15s/data_type=derivative_ticker/BTC-PERPETUAL.parquet
404 GET .../processed_candles/by_date/day=2026-04-07/.../data_type=derivative_ticker/instrument_type=perpetuals/venue=DERIBIT/DERIBIT:PERPETUAL:BTC-PERPETUAL@LIN.parquet
```

But MDPS actually writes to `data_type=derivative_ticker/venue=BINANCE-FUTURES/BINANCE-FUTURES:PERPETUAL:BTCUSDT.parquet` (different venue partition; no `instrument_type=perpetuals/` middle segment; canonical instrument_id pattern). Loader needs updating.

Affected file: `features-delta-one-service/features_delta_one_service/app/.../candle_loader.py` (or similar — find via `grep -rn "processed_candles/by_date" features-delta-one-service/`).

## Multi-coin / multi-funding / multi-venue rotation (decision-making architecture)

User asked: "How do we decide what we're choosing for an ARB? That kind of stuff, like the decision-making."

**Answer documented in this session** — for handoff continuity:

The decision lives in 4 layers:
1. **Catalog** (`target_universe/catalog.py`) — menu of available specs.
2. **Features** — per-(spec, day) metric values.
3. **Allocator** (`portfolio_allocator/archetypes.py`, `BaseRankAllocator` + 7 archetype subclasses) — universe filter, score metric, threshold (default 250 bps = 2.5% APY), top-N, capital-weighting. **This is the opportunity-decision layer.**
4. **Strategy engine** (`engine/strategies/v2/*_engine.py`) — entry triggers, exit triggers, roll on expiry, rotation cost gating.

`CarryBasisPerpRankAllocator` is the canonical multi-coin/multi-venue example (3-stage hierarchical: per-coin avg → cross-coin weighting → per-venue weighting within each coin). Ships already; no allocator change needed when we add new specs/calculators — they consume the same shape.

## START HERE

1. Read this file + read `carry_tracer_pipeline_handoff_2026_05_05.md` (yesterday's handoff for context).
2. Check VM state: `gcloud compute instances list --zones=asia-northeast1-c --filter='name~"^(mdps-backfill-cefi|cefi-deribit|features-)" AND status=RUNNING'`. If MDPS 4 VMs done, audit MDPS output completeness with day-by-day count over 2026-03-17..04-14.
3. **First action**: Layer 2 tracer adapters (~30 min). After this, 6/7 archetypes produce real APY values via end-to-end Stage 3.
4. **Second action**: funding_oi loader path fix in features-delta-one (small, well-scoped).
5. **Third action**: re-run partial Stage 3 with all 6 working archetypes, then verify cross-archetype comparison parquet has real winners with real APY values + plausible flow_of_funds_legs.
6. **Fourth action**: file Phase 9 plan for catalog spec additions + `paired_price_dispersion` calculator + UAC `LST_TOKEN_TO_PROTOCOL_ASSET` SSOT.
7. **Fifth action** (Stage 4 — overnight): once everything works on 30 days, fan out to full historical (2022-01-01 → today).

## Don't

- Re-run MDPS for 2026-03-15..04-14 — 4 parallel VMs already on it (after the user's call to scope-delete + scoped-MDPS earlier; we deleted the 3 days that had stale processed_candles + launched 4 parallel VMs covering 03-17..04-14).
- Re-launch Deribit dated/options ingestion — 3 light VMs running (2024 + 2025 + 2026).
- `git push` from a worktree with dep repos dirty — see CLAUDE.md "Two teammates × multiple parallel agents". Workspace has multiple agents in flight; check `git status` everywhere before commit.
- Fabricate row data when feature group is missing — emit `skipped_reason` per the honest-absence rule. Today's tracer does this correctly.
- Skip CLAUDE.md no-fire-and-forget verification: every VM launch needs paired event-stream check; structured progress events are the SSOT for "is it really doing work" not gcloud STATUS=RUNNING.
