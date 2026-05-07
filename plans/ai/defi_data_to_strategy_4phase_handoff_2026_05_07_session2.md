# Session 2 of DeFi data → strategy 4-phase handoff (2026-05-07)

You are the next agent. The prior session (this one) shipped A2 + A3 part 1 of the original 4-phase handoff
(`defi_data_to_strategy_4phase_handoff_2026_05_07.md`). Pick up from where this session left off.

## What this session shipped

| Commit    | Repo                              | What                                                                                                                                                                                                                                                                                                                                                                                     |
| --------- | --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `954575a` | features-cross-instrument-service | A2 — `futures_roll_resolver.py` + 26 tests. `(root, as_of_date) → FrontMonth(symbol, expiry, days_to_expiry)`. Covers 4 listing cycles: CME quarterly (HMUZ), CME monthly (all 12), COMEX gold (GJMQVZ), DERIBIT crypto last-Friday, NASDAQ/NYSE ETF pass-through. Roll-on-DTE cushion advances on day-of-roll. Round-trips with UAC `parse_futures_expiry`.                             |
| `2804f47` | features-cross-instrument-service | A3 part 1 — `catalog_pair_builder.py` + 12 tests. `(archetype, params, as_of) → list[PairSpec]`. Bridges 4 catalog shapes: commodity / equity-index ETF / crypto spot-dated / cross-venue match-expiry. Skips `databento_pending`. Out-of-scope shapes (lending arb, sports books) return empty list. Also registered `spx`/`ndx` in `ROOT_CYCLES` as `is_etf=True` (CBOE cash indices). |

Total: 38 new tests, all pass. 2 commits pushed to `live-defi-rollout` on features-cross-instrument-service. No QG
regressions introduced (3 mode-handler test failures are pre-existing on origin per session-start audit).

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

**A3 part 2 — batch_handler dispatch wiring**. The catalog → PairSpec builder shipped in A3p1; now wire it into
`batch_handler.py`:

- When `feature_group == "paired_price_dispersion"` is in the request, bypass the standard `_ingest_delta_one` path
- Iterate the strategy-service catalog (read via UAC or co-located helper) → for each `CARRY_BASIS_DATED` /
  `ARBITRAGE_PRICE_DISPERSION` spec, call `build_pair_specs(archetype, spec.params, as_of)`
- Cross-asset-group bucket reads: CME=tradfi, DERIBIT=cefi, NASDAQ=tradfi, CBOE=tradfi. The `raw_tick_data` paths differ
  from delta-one paths — need
  `gs://market-data-tick-{asset_group}-{project_id}/raw_tick_data/by_date/day={D}/asset_group={AG}/venue={V}/data_type={DT}/...`
- The instrument_id field in raw_tick_data parquets uses the canonical symbol naming for that source. **Before wiring**:
  probe one CME parquet to verify whether `instrument_id` is `MBTM6` / `MBT_FUT_M6` / something else. The resolver emits
  `MBTM6` (CME-style); MTDS may write differently.
- Build the long-form (instrument_id, timestamp, close) frame from both buckets; pass into
  `resolve_paired_specs(df, specs)`; pass that into the kernel `PairedPriceDispersionCalculator`.

Estimated ~80 LOC + 5 tests. Hardest part is the GCS layout reconciliation; the algebra (catalog → PairSpec → resolver →
kernel) is now all shipped.

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

## Why A3 part 2 wasn't shipped

Wiring `paired_price_dispersion` dispatch into `batch_handler.py` requires verifying the raw_tick_data instrument_id
naming on CME / DERIBIT (the resolver emits canonical `MBTJ6` / `BTCM6` shapes; MTDS adapter may write differently —
e.g. `MBT_FUT_M6` or with instrument_type prefix). Without that verification, the dispatch path would silently miss
every leg. The catalog → PairSpec algebra is the load-bearing piece and now shipped; the GCS wiring layer is ~80 LOC of
bucket-aware tick concatenation that should be added in a session that can probe one CME parquet to confirm the symbol
shape. I made the call to **ship clean foundations** rather than risk a silent-empty integration.

To unblock A3p2 fastest, the next agent should:

1. Probe one CME parquet:
   ```bash
   gcloud storage ls "gs://market-data-tick-tradfi-{project}/raw_tick_data/by_date/day=2026-04-09/asset_group=tradfi/venue=CME/data_type=ohlcv_1m/" | head
   ```
2. Read the parquet to check `instrument_id` column values — match the resolver output (`MBTJ6`, `ESM6`, etc.) or tweak
   the resolver / builder to emit the on-disk shape.
3. Then wire `batch_handler` per the A3 part 2 plan above.

## Files shipped this session

```
features-cross-instrument-service/
├── features_cross_instrument_service/app/calculators/
│   ├── futures_roll_resolver.py    (NEW, 215 LOC)
│   └── catalog_pair_builder.py     (NEW, 226 LOC)
└── tests/unit/
    ├── test_futures_roll_resolver.py    (NEW, 26 tests)
    └── test_catalog_pair_builder.py     (NEW, 12 tests)
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
