# Session 2 of DeFi data → strategy 4-phase handoff (2026-05-07)

You are the next agent. The prior session (this one) shipped A2 + A3 part 1 of the original 4-phase handoff
(`defi_data_to_strategy_4phase_handoff_2026_05_07.md`). Pick up from where this session left off.

## What this session shipped

| Commit                     | Repo                              | What                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| -------------------------- | --------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `954575a`                  | features-cross-instrument-service | A2 — `futures_roll_resolver.py` + 26 tests. `(root, as_of_date) → FrontMonth(symbol, expiry, days_to_expiry)`. Covers 4 listing cycles: CME quarterly (HMUZ), CME monthly (all 12), COMEX gold (GJMQVZ), DERIBIT crypto last-Friday, NASDAQ/NYSE ETF pass-through. Roll-on-DTE cushion advances on day-of-roll. Round-trips with UAC `parse_futures_expiry`.                                                                                                                                                                                                                                  |
| `2804f47`                  | features-cross-instrument-service | A3 part 1 — `catalog_pair_builder.py` + 12 tests. `(archetype, params, as_of) → list[PairSpec]`. Bridges 4 catalog shapes: commodity / equity-index ETF / crypto spot-dated / cross-venue match-expiry. Skips `databento_pending`. Out-of-scope shapes (lending arb, sports books) return empty list. Also registered `spx`/`ndx` in `ROOT_CYCLES` as `is_etf=True` (CBOE cash indices).                                                                                                                                                                                                      |
| `190bea1`                  | features-cross-instrument-service | A3 part 2 (initial) — `paired_dispatch.py` + 30 tests + `batch_handler` wiring. `run_paired_price_dispersion(catalog_rows, date, sc, project_id)` orchestrates: catalog → builder → multi-asset-group delta-one read → resolver → kernel. `_compute_one_group()` extracted from `_process_features`. Bug fix: per-leg expiry inferred — cash/spot leg uses `date.max` sentinel.                                                                                                                                                                                                               |
| `6217382`                  | unified-api-contracts             | UAC `PAIRED_DISPERSION_CATALOG` SSOT — 18 catalog rows (13 active + 5 databento_pending), lifted from strategy-service. Exported via `unified_api_contracts.internal.architecture_v2`.                                                                                                                                                                                                                                                                                                                                                                                                        |
| `543a0bb`                  | features-cross-instrument-service | A3 part 2 (follow-ups) — formatter delegates to UAC `build_instrument_id` (the canonical SSOT); per-venue prediction tables removed. `_load_catalog_rows_for_paired_dispatch` reads from UAC. Test assertions updated to canonical UAC IDs (`CME:FUTURE:MBT-20260619`, `DERIBIT:FUTURE:BTC-20260626`, `NASDAQ:ETF:IBIT`, `CBOE:INDEX:SPX`, `ICE:COMMODITY:CL`).                                                                                                                                                                                                                               |
| **A1** features-onchain VM | `7f1b2a1` (prior) verified        | A1 SHIPPED — `features-onchain-defi-backfill-20260507-105936` ran 2026-04-03→04-09 with FORCE=1 SKIP_DEPENDENCY_CHECK=1; STARTED → 154 events → STOPPED clean. Sample parquet `lending_rates/features.parquet` for day=2026-04-09 has all 5 canonical columns populated: `protocol=AAVE_V3 chain=ARBITRUM asset=USDC supply_apy=0.0162 borrow_apy=0.0283 instrument_id=AAVE_V3-ARBITRUM:LENDING:USDC`. 61,618 rows × 15 cols.                                                                                                                                                                 |
| **A5** Deribit light VMs   | (no commit — operational)         | A5 SHIPPED — `cefi-deribit-{2025,2026}-light-20260507-110045` both ran cleanly: DERIBIT-2025 740 events STOPPED, DERIBIT-2026 219 events STOPPED. Intra-Deribit + CME-DERIBIT cross-venue spec data captured.                                                                                                                                                                                                                                                                                                                                                                                 |
| `666dc2d`                  | strategy-service                  | A4 SHIPPED — tracer Layer 2 schema-drift shim deleted: `_TOKEN_TO_PROTOCOL_ASSET` (16-token table, replaced by UAC `LST_TOKEN_TO_PROTOCOL_ASSET`), `_tokens_for_protocol_asset`, `_parse_lending_instrument_id`, `aave_supply_apy → supply_apy → lending_apy` fallback chain in supply/borrow APY resolvers. `_filter_lending_by_id` rewritten to use canonical `protocol`/`chain`/`asset` columns directly (no more regex parsing of `instrument_id`). KEPT `_normalise_protocol_name` (catalog ↔ parquet vocab translation). Net -61 LOC.                                                  |
| `4354276c`                 | unified-trading-library           | B4 part 1 SHIPPED — `assert_no_lookahead_for_feature_group(feature_group, inputs_df, target_ts)` UTL helper that consumes UAC `FEATURE_REQUIRED_INPUTS` SSOT (29 feature_groups). Computes max_horizon across all declared inputs, raises `LookaheadBiasError` if any input row's `available_at > target_ts - horizon`. Skips silently for unregistered feature_groups, empty df, or missing `available_at` col. 9 unit tests covering clean-pass / violation-raise / unregistered-skip / empty / naive-tz / label / multi-violation. Exposed via `unified_trading_library` top-level facade. |

Total: 77 new tests, all pass. 9 commits pushed to `live-defi-rollout` across 4 repos. 3 production VMs verified
(features-onchain DEFI, DERIBIT 2025+2026 light). No QG regressions introduced (pre-existing failures on origin verified
via git blame).

## What's still on the original 4-phase handoff

The full original handoff is at `unified-trading-pm/plans/ai/defi_data_to_strategy_4phase_handoff_2026_05_07.md`. Open
work in dependency order:

### Phase A — Data foundations (continued)

**A1, A4, A5** ✅ ALL SHIPPED this session — see commits table above. Phase A is COMPLETE except Phase A verification
gate (full Stage 3 carry tracer over 2026-04-03..04-09 across all 7 archetypes).

**B4 part 2 — per-service wiring of `assert_no_lookahead_for_feature_group`** (DEFERRED). The UTL helper shipped in
`4354276c` is the load-bearing piece. Per-service wiring requires upstream `available_at` write-time stamping in each
calculator's input adapter (DefiLlama, AAVE subgraph, Lido, etc.) — once that's in place, the helper can be called at
the input-load boundary in each calculator. Suggested call site: insert before `calculate_features(raw_data)` in each
`features-onchain/app/calculators/*.py` after raw*data has been stamped. Workspace SSOT for stamping helpers:
`unified_trading_library.availability_stamping.stamp_available_at*\*`.

**B4 part 2 deferral reason** — calculator inputs (e.g. `lst_staking_calculator.calculate_features` taking
`pd.DataFrame` with `apy_base`/`project`/`symbol` cols) don't have `available_at` populated by upstream adapters yet.
Adding the helper call now would silently skip via the "missing col" branch. The right sequence is: adapter stamps
`available_at` → calculator imports helper → helper validates inputs against UAC SSOT.

---

**Original A1 launch instructions (now obsolete — A1 ran 2026-05-07 successfully):**

```bash
FORCE=1 SKIP_DEPENDENCY_CHECK=1 \
  bash deployment-service/scripts/vm/launch-features-backfill-vm.sh \
    onchain DEFI 2026-04-03 2026-04-09 full
```

Wait for STARTED → DATA_INGESTION_STARTED → PROCESSING events. Verify a sample `lending_rates` parquet has populated
`protocol`/`chain`/`asset`/ `supply_apy`/`borrow_apy` columns. Required BEFORE A4 (tracer shim delete).

**A3 part 2 — batch_handler dispatch wiring** ✅ SHIPPED `190bea1` + `543a0bb` + UAC `6217382`. Both follow-ups
RESOLVED:

1. **Catalog source RESOLVED**: UAC `PAIRED_DISPERSION_CATALOG` (architecture_v2 module) holds the 18 paired_dispersion
   catalog rows (13 active + 5 databento_pending). `_load_catalog_rows_for_paired_dispatch` reads from there. Lifted
   from strategy-service per the workspace SSOT rule.
2. **Formatter calibration RESOLVED**: `_LEG_TO_DELTA_ONE_ID` (predicted shapes) replaced with
   `_LEG_TO_INSTRUMENT_TYPE` + delegation to UAC `build_instrument_id`. UAC is now the single source of truth for
   canonical instrument IDs. Eight venues calibrated. Empirical examples produced by UAC:
   - `BINANCE-FUTURES:PERPETUAL:BTC-USDT`
   - `CME:FUTURE:MBT-20260619` (was predicted `CME:FUTURES_CHAIN:MBTM6`)
   - `DERIBIT:FUTURE:BTC-20260626` (was predicted `DERIBIT:DATED_FUTURE:BTC-26JUN26`)
   - `DERIBIT:PERPETUAL:BTC` (was predicted `DERIBIT:PERPETUAL:BTC-PERPETUAL`)
   - `NASDAQ:ETF:IBIT` (was predicted `NASDAQ:EQUITY:IBIT-USD`)
   - `CBOE:INDEX:SPX` (was predicted `CBOE:INDEX:SPX-USD`)
   - `ICE:COMMODITY:CL` (was predicted `ICE:FUTURES:CL-USD`)

### GCS layout verified (probed 2026-05-07)

- CME futures live at
  `gs://market-data-tick-tradfi-{project}/raw_tick_data/by_date/day={D}/asset_group=tradfi/ venue=CME/instrument_type=futures_chain/data_type=ohlcv_1m/underlying={ROOT}/ticks.parquet`
  — bundled per root, with per-contract symbols in the `symbol` column (e.g. `MBTJ6`, `MBTK6`, `MBTM6`, `MBTZ6` for MBT
  root).
- DERIBIT perpetuals live at
  `.../venue=DERIBIT/instrument_type=perpetual/data_type=derivative_ticker/{ASSET}- PERPETUAL.parquet`; dated futures
  use `{ASSET}-DDMMMYY` shape (e.g. `BTC-28MAR25`).
- features-delta-one shape:
  `gs://features-delta-one-{asset_group}-{project}/by_date/day={D}/feature_group={FG}/ timeframe={T}/{INSTRUMENT_ID}.parquet`.
  Instrument ID format: `{VENUE}:{INSTRUMENT_TYPE}:{SYMBOL}`. CME / DERIBIT- dated / COINBASE / CBOE / ICE / NYMEX
  delta-one parquets are not yet present (only BINANCE-FUTURES + NASDAQ shipped at probe time). Dispatch still works —
  formatter generates predicted instrument_ids; resolver returns honest absence when there's no matching instrument_id
  in the long-form frame.

**A4 — tracer `_TOKEN_TO_PROTOCOL_ASSET` shim deletion**. Lift from
`strategy-service/scripts/trace_all_carry_archetypes.py` after A1 confirms features-onchain parquets emit canonical
columns. KEEP `_normalise_protocol_name` (catalog ↔ parquet vocab translation, independent of calculator schema).

**A5 — Deribit dated/options light VM relaunch** (gcloud-blocked). Run with longer runtime:

```bash
ONLY="DERIBIT:2026:light DERIBIT:2025:light" FORCE=1 \
  bash deployment-service/scripts/vm/launch-cefi-sharded-backfill.sh
```

Verify intra-Deribit + CME-DERIBIT cross-venue futures specs in `CARRY_BASIS_DATED` + `ARBITRAGE_PRICE_DISPERSION` have
data.

**Phase A verification gate** — partial Stage 3 of carry tracer over 2026-04-03..04-09 expecting all 7 archetypes have
non-empty `realised_apy_bps`. The `CARRY_BASIS_DATED` + cross-venue `ARBITRAGE_PRICE_DISPERSION` are the new ones lit by
A2/A3/A5.

### Phase B — Honest-absence + manifest closeouts (unchanged from original)

B1, B2, B3, B4 — see original handoff.

### Phase C — Strategy + execution code path (unchanged)

C1, C2, C3, C4 — see original handoff.

### Phase D — Backfill + intent testing (unchanged)

D1, D2, D3, D4 — see original handoff.

### DEX perp onboarding handover items (separate plan)

`unified-trading-pm/plans/active/dex_perp_onboarding_handover_2026_05_07.HANDOVER.md` items A through F (forward-poll
handlers, Pacifica collateral matrix, EXTENDED-STARKNET historical, Lighter symbol scale-up, per-trade gap doc,
backfill-VM final state) — none touched this session.

## Files shipped this session

```
features-cross-instrument-service/
├── features_cross_instrument_service/
│   ├── app/calculators/
│   │   ├── futures_roll_resolver.py    (NEW, 215 LOC, 26 tests)
│   │   ├── catalog_pair_builder.py     (NEW, 226 LOC, 12 tests)
│   │   └── paired_dispatch.py          (NEW, 350 LOC, 30 tests)
│   └── cli/handlers/
│       └── batch_handler.py            (modified — paired route + _compute_one_group helper)
└── tests/unit/
    ├── test_futures_roll_resolver.py
    ├── test_catalog_pair_builder.py
    └── test_paired_dispatch.py
```

## Don't (unchanged from original handoff)

- AWS parity (work stream D) — deferred
- Live-mode services (work stream E) — deferred
- DART manual-trade lane — deferred
- "no fire-and-forget VM launches" rule — enforced
- Quickmerging while dep repos are dirty — commit + push to `live-defi-rollout` directly

## Reference paths

- Original 4-phase handoff: `unified-trading-pm/plans/ai/defi_data_to_strategy_4phase_handoff_2026_05_07.md`
- Phase 9 archived plan: `unified-trading-pm/plans/archive/carry_tracer_phase_9_catalog_paired_dispersion_2026_05_06.md`
- DEX perp handover: `unified-trading-pm/plans/active/dex_perp_onboarding_handover_2026_05_07.HANDOVER.md`
- Resolver:
  `features-cross-instrument-service/features_cross_instrument_service/app/calculators/futures_roll_resolver.py`
- Builder: `features-cross-instrument-service/features_cross_instrument_service/app/calculators/catalog_pair_builder.py`

---

## SUPERSEDED 2026-05-07 — see active plans for current SSOT

All actionable items from this handoff have been folded into active PM plans (PM commit `2cd3bbaf`). This doc is
reference-only; **new agents should read `unified-trading-pm/plans/active/` for the current source of truth**.

Mapping:

| Section here                                                                                                                                  | Active plan SSOT                                                                               |
| --------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| A1 features-onchain VM rerun + parquet verify                                                                                                 | `defi_master_2026_05_07.md` § Carry tracer verification gates (Phase A) — SHIPPED              |
| A4 tracer shim deletion                                                                                                                       | `defi_master_2026_05_07.md` (referenced via strategy@666dc2d) — SHIPPED                        |
| A5 DERIBIT light VMs                                                                                                                          | `defi_master_2026_05_07.md` (operational) — SHIPPED                                            |
| A2 / A3 carry tracer Phase 9 (futures_roll_resolver, catalog_pair_builder, paired_dispatch, UAC catalog SSOT, UAC build_instrument_id wiring) | `defi_master_2026_05_07.md` (commit refs in Audit 2026-05-07 section) — SHIPPED                |
| Phase A verification gate                                                                                                                     | `defi_master_2026_05_07.md` § Carry tracer verification gates — PARTIAL                        |
| Phase D verification gate (full Stage 4 historical)                                                                                           | `defi_master_2026_05_07.md` § Carry tracer verification gates — FRESH                          |
| B4 part 1 UTL helper                                                                                                                          | `feature_dag_uac_ssot_and_features_coverage_2026_05_06.md` Phase 2A — SHIPPED                  |
| B4 part 2 per-service wiring + adapter-stamping prereq                                                                                        | `feature_dag_uac_ssot_and_features_coverage_2026_05_06.md` Phase 2A — FRESH                    |
| B1 writegate Phase 2.B orchestrator pre-skip                                                                                                  | `writegate_honest_coverage_endtoend_2026_05_06.md`                                             |
| B2 reconcilers                                                                                                                                | `writegate_honest_coverage_endtoend_2026_05_06.md` + `manifest_migration_master_2026_05_07.md` |
| B3 manifest v6→v7 reader                                                                                                                      | `manifest_migration_master_2026_05_07.md`                                                      |
| C1 strategy v2 finalization                                                                                                                   | `strategy_architecture_v2_finalization_2026_04_19.md`                                          |
| C2 4-service QGs                                                                                                                              | `defi_master_2026_05_07.md` § DeFi e2e pipeline gates                                          |
| C3 CARRY_RECURSIVE_STAKED batch e2e                                                                                                           | `defi_master_2026_05_07.md` § DeFi e2e pipeline gates                                          |
| C4 features-onchain Docker rebuild                                                                                                            | `defi_master_2026_05_07.md` § DeFi e2e pipeline gates                                          |
| D1 MTDS DeFi 100%                                                                                                                             | `defi_master_2026_05_07.md` § MTDS DeFi slice                                                  |
| D2 tail-chain coverage                                                                                                                        | `defi_master_2026_05_07.md` § Tail-chain                                                       |
| D3 Lighter / Extended / Pacifica historical                                                                                                   | `defi_master_2026_05_07.md` § Lighter / Extended / Pacifica historical replay                  |
| D4 Pyth / Chainlink oracle                                                                                                                    | `defi_master_2026_05_07.md` § Oracle prices + chain expansion                                  |
| DEX perp follow-ups (Items A-F from HANDOVER)                                                                                                 | `defi_master_2026_05_07.md` § DEX perp forward-poll handlers + collateral matrix               |

This doc is preserved as historical context for the multi-session Phase 9 / 4-phase work.
