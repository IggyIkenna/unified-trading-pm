# Session 2 of DeFi data → strategy 4-phase handoff (2026-05-07)

You are the next agent. The prior session (this one) shipped A2 + A3 part 1 of the original 4-phase handoff
(`defi_data_to_strategy_4phase_handoff_2026_05_07.md`). Pick up from where this session left off.

## What this session shipped

| Commit    | Repo                              | What                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --------- | --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `954575a` | features-cross-instrument-service | A2 — `futures_roll_resolver.py` + 26 tests. `(root, as_of_date) → FrontMonth(symbol, expiry, days_to_expiry)`. Covers 4 listing cycles: CME quarterly (HMUZ), CME monthly (all 12), COMEX gold (GJMQVZ), DERIBIT crypto last-Friday, NASDAQ/NYSE ETF pass-through. Roll-on-DTE cushion advances on day-of-roll. Round-trips with UAC `parse_futures_expiry`.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| `2804f47` | features-cross-instrument-service | A3 part 1 — `catalog_pair_builder.py` + 12 tests. `(archetype, params, as_of) → list[PairSpec]`. Bridges 4 catalog shapes: commodity / equity-index ETF / crypto spot-dated / cross-venue match-expiry. Skips `databento_pending`. Out-of-scope shapes (lending arb, sports books) return empty list. Also registered `spx`/`ndx` in `ROOT_CYCLES` as `is_etf=True` (CBOE cash indices).                                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| `190bea1` | features-cross-instrument-service | A3 part 2 — `paired_dispatch.py` + 30 tests + `batch_handler` wiring. Venue-aware `to_delta_one_instrument_id(venue, root, symbol, expiry) → "{VENUE}:{INSTRUMENT_TYPE}:{SYMBOL}"` formatter calibrated against probed delta-one shapes (`BINANCE-FUTURES:PERPETUAL:BTC-USDT`, `NASDAQ:EQUITY:AAPL-USD`); predicted shapes for CME / DERIBIT-dated / COINBASE / CBOE / ICE / NYMEX. `run_paired_price_dispersion(catalog_rows, date, sc, project_id)` orchestrates: catalog → builder → multi-asset-group delta-one read → resolver → kernel. `_compute_one_group()` extracted from `_process_features` for complexity gate; routes `paired_price_dispersion` to dispatcher. Bug fix: `_pair_specs_to_resolver_specs` now infers per-leg expiry — cash/spot leg uses `date.max` sentinel, dated leg uses spec expiry (basis pairs were dropping cash leg before). |

Total: 68 new tests, all pass. 3 commits pushed to `live-defi-rollout` on features-cross-instrument-service. No QG
regressions introduced (3 mode-handler test failures are pre-existing on origin per session-start audit). Coverage
cleared: 79.12% (was 77.81% session-start, target 79%).

## What's still on the original 4-phase handoff

The full original handoff is at `unified-trading-pm/plans/ai/defi_data_to_strategy_4phase_handoff_2026_05_07.md`. Open
work in dependency order:

### Phase A — Data foundations (continued)

**A1 — features-onchain DEFI rerun VM** (gcloud-blocked, was blocked when this session started too). Launch:

```bash
FORCE=1 SKIP_DEPENDENCY_CHECK=1 \
  bash deployment-service/scripts/vm/launch-features-backfill-vm.sh \
    onchain DEFI 2026-04-03 2026-04-09 full
```

Wait for STARTED → DATA_INGESTION_STARTED → PROCESSING events. Verify a sample `lending_rates` parquet has populated
`protocol`/`chain`/`asset`/ `supply_apy`/`borrow_apy` columns. Required BEFORE A4 (tracer shim delete).

**A3 part 2 — batch_handler dispatch wiring** ✅ SHIPPED `190bea1`. After probing the GCS layout (see "GCS layout
verified" below), wired the dispatcher reading from features-delta-one (NOT raw_tick_data — delta-one already provides
the OHLCV close prices the kernel needs). Two open follow-ups:

1. **Catalog source**: `_load_catalog_rows_for_paired_dispatch` returns `[]` until the strategy-service catalog is
   exposed via UAC (cross-service dependency would violate the import graph). Until then, the dispatch produces an empty
   kernel output (which the writegate handles as honest absence). Lift required: copy the `CARRY_BASIS_DATED` +
   `ARBITRAGE_PRICE_DISPERSION` row builders from
   `strategy-service/strategy_service/engine/ strategies/v2/target_universe/catalog.py` into UAC, then point the loader
   at the UAC SSOT.
2. **Calibrate `_LEG_TO_DELTA_ONE_ID`** when CME / DERIBIT-dated / COINBASE / CBOE / ICE / NYMEX delta-one parquets
   first land. The formatter is calibrated against the empirical shapes available 2026-05-07
   (`BINANCE-FUTURES:PERPETUAL:BTC-USDT`, `NASDAQ:EQUITY:AAPL-USD`); other shapes are predicted.

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
- Phase 9 archived plan:
  `unified-trading-pm/plans/archive/carry_tracer_phase_9_catalog_paired_dispersion_2026_05_06.plan.md`
- DEX perp handover: `unified-trading-pm/plans/active/dex_perp_onboarding_handover_2026_05_07.HANDOVER.md`
- Resolver:
  `features-cross-instrument-service/features_cross_instrument_service/app/calculators/futures_roll_resolver.py`
- Builder: `features-cross-instrument-service/features_cross_instrument_service/app/calculators/catalog_pair_builder.py`
