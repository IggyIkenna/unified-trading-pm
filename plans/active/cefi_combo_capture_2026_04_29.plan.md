---
title: "CeFi DERIBIT combo capture (option_combo + future_combo)"
priority: P2
status: active
owner: agent
created: 2026-04-29
type: feature
epic: none
completion_gates:
  code: C3
  deployment: D2
  business: none
repo_gates:
  - repo: unified-api-contracts
    code: C2
    deployment: D0
  - repo: market-tick-data-service
    code: C2
    deployment: D0
  - repo: unified-trading-pm
    code: C0
    business: B0
depends_on: []
isProject: false
---

## Context

The 2026-04-29 audit revealed combos are wired across most of the stack but absent from market-data capture:

- ✅ `InstrumentType.COMBO` exists in UAC `_instrument_enums.py:53`
- ✅ Deribit external-schema `kind` accepts `future_combo` / `option_combo` (UAC `external/deribit/schemas.py`)
- ✅ Deribit normalize maps `future_combo → FUTURE` and `option_combo → OPTION` (UAC
  `external/deribit/normalize.py:95-97`) — these are flagged in the Tardis instruments parquet as
  `instrument_type=COMBO` (264 such rows for DERIBIT 2024-06-01)
- ✅ execution-service has `OptionsComboHandler` + DERIBIT/CBOE wiring
- ✅ Manifest v6 `combo_type` column (`call_spread` / `put_spread` / `iron_condor` / `butterfly` / `calendar_spread`)
  shipped Phase 2b 2026-04-23
- ✅ instruments-service Tardis adapter parses combo symbol patterns (`tardis.py:88` —
  `_TYPE_MAP["combo"] = InstrumentType.COMBO`, line 143 comment "Single-expiry option combos:
  BASE-CODE-EXPIRY-K1_K2[\_K3[_K4]]")
- ❌ **MTDS does NOT request combo data from Tardis.** The `options_chain` bulk endpoint returns standard options only —
  no combo rows (verified empirically: 218 unique symbols in 2020-01-04 BTC bundle, zero combo-shaped).
- ❌ `expected_coverage.py` does not enumerate combos as in-scope, so the data-status UI doesn't track them.

Tardis offers separate platform-grouped bulk endpoints:

- `https://datasets.tardis.dev/v1/deribit/options_chain/YYYY/MM/DD/OPTION-COMBOS.csv.gz`
- `https://datasets.tardis.dev/v1/deribit/futures_chain/YYYY/MM/DD/FUTURE-COMBOS.csv.gz`

(URL templates need verification against Tardis docs.)

## What we want

A clean addition that mirrors the existing options_chain bulk path:

1. **UAC** — extend `_BULK_DOWNLOAD_SYMBOLS` in MTDS Tardis adapter to include `option_combos` / `future_combos`
   data_types mapped to grouped symbols (`OPTION-COMBOS` / `FUTURE-COMBOS` per Tardis docs — to verify).

2. **MTDS combo-symbol parser** in `tardis_shared.py` —
   `parse_deribit_option_combo_symbol(s) → (base, expiry, [strikes], right)` for `BTC-29MAR24-50000_55000-C` (call
   spread), `BTC-29MAR24-45000_50000_55000_60000` (iron condor), etc. Multi-strike list, optional right. Use `legs`
   column from manifest v6 to encode the strike list.

3. **Canonical write path** — combo rows get `instrument_type=combo` (per UAC enum) at the row level. Storage-side: new
   `instrument_type=option_combos` / `instrument_type=future_combos` chain wrappers (parallel to `options_chain` /
   `futures_chain`), bundled per underlying.

4. **expected_coverage.py** — add `option_combos` / `future_combos` to
   `EXPECTED_COVERAGE_BY_ASSET_GROUP["cefi"]["DERIBIT"]` so the data-status UI tracks the new shards.

5. **Manifest** — combo shards get `combo_type` column populated from the parsed symbol (`call_spread` / `put_spread` /
   etc. per the v6 schema). Use the existing classifier in instruments-service.

## Pre-audit

| Repo / file                                                           | Action                                                                                                          |
| --------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `unified-api-contracts/registry/expected_coverage.py:65`              | Add `"option_combos"` and `"future_combos"` to DERIBIT entry                                                    |
| `unified-api-contracts/registry/market_data_categories.py`            | Confirm `option_combos` / `future_combos` are NOT misclassified as separate data_types — they're chain wrappers |
| `market-tick-data-service/.../adapters/tradfi/tardis_adapter.py:754`  | Extend `_BULK_DOWNLOAD_SYMBOLS`                                                                                 |
| `market-tick-data-service/.../adapters/cefi/tardis_shared.py`         | Add `parse_deribit_option_combo_symbol` + `parse_deribit_future_combo_symbol`                                   |
| `market-tick-data-service/.../adapters/cefi/tardis_shared.py:683-696` | Extend `shard_it` selector to map COMBO rows to `option_combos` / `future_combos` storage paths                 |
| `unified-api-contracts/canonical/.../canonical_id_builder.py`         | Ensure COMBO instrument_id format handles multi-strike lists                                                    |
| `instruments-service/...`                                             | NO change — combo classifier already exists                                                                     |
| `tests/unit/test_combo_parser.py` (NEW)                               | Coverage for call_spread / put_spread / iron_condor / butterfly / calendar_spread                               |

## Phased execution DAG

```
Phase 1 — Combo symbol parser (P0, ~2h)
   1.1 parse_deribit_option_combo_symbol for K1_K2 / K1_K2_K3_K4 patterns
   1.2 parse_deribit_future_combo_symbol for calendar spreads (BTC-29MAR24_28JUN24)
   1.3 Tests covering each combo_type from the manifest v6 enum
              ─── QG: parser handles every combo example documented in
                       instruments-service/.../tardis.py:143-200 ───
                              ↓
Phase 2 — Tardis bulk endpoint URL verification (P0, ~1h)
   2.1 Confirm Tardis URL pattern via docs
   2.2 Add option_combos / future_combos to _BULK_DOWNLOAD_SYMBOLS
   2.3 Smoke download for 2024-06-01 DERIBIT — does it return rows?
              ─── QG: at least one Tardis combo row downloaded successfully ───
                              ↓
Phase 3 — Canonical write path (P1, ~2h)
   3.1 Extend shard_it selector for COMBO → option_combos / future_combos
   3.2 Update derive_row_instrument_id for COMBO with multi-strike legs
   3.3 build_partition_path supports new chain wrappers
   3.4 finalise_and_write_cefi_shards groups combo rows by underlying
              ─── QG: a 2024-06-01 combo bundle lands at
                       day=.../instrument_type=option_combos/.../BTC.parquet ───
                              ↓
Phase 4 — Coverage enum + tarball + relaunch (P1, ~1h)
   4.1 expected_coverage.py adds option_combos / future_combos for DERIBIT
   4.2 Refresh tarballs
   4.3 Run a focused 1-week probe — verify partitions land
   4.4 Update data-status UI heuristics if needed
              ─── QG: deployment-ui shows option_combos column with
                       captured/missing classification per the
                       four-state matrix from data_status_drilldown ───
```

## Success criteria

- **Phase 1**: every combo_type pattern from the manifest v6 enum (`call_spread` / `put_spread` / `iron_condor` /
  `butterfly` / `calendar_spread`) parses cleanly from a sample symbol, returning
  `(base, expiry, [strikes], right_or_None)`.
- **Phase 2**: a single VM smoke run for DERIBIT 2024-06-01 downloads at least one OPTION-COMBOS row from Tardis without
  HTTP error.
- **Phase 3**: GCS layout
  `day=2024-06-01/asset_group=cefi/venue=DERIBIT/instrument_type=option_combos/data_type=trades/underlying=BTC/quote=USD/margin=inverse/ticks.parquet`
  exists with non-zero rows.
- **Phase 4**: deployment-ui data-status surfaces option_combos / future_combos as a tracked column with the four-state
  classifier (captured / missing / blocked-on-raw / out-of-scope).

## What we are NOT doing

- Not changing how combos are classified at the row level — `InstrumentType.COMBO` is the canonical row-level type, but
  Deribit normalize already maps `option_combo → OPTION` and `future_combo → FUTURE` for downstream consumers.
  Storage-side wraps them as `option_combos` / `future_combos` chain bundles. Don't break either contract.
- Not wiring combo handling into MDPS / strategy-service — execution-service already has `OptionsComboHandler`. MDPS
  combo-candle building is a separate workstream if ever needed.
- Not adding combo support for venues other than DERIBIT in this plan — BYBIT / BINANCE-FUTURES / OKX combos are out of
  scope (Tardis doesn't surface combos for those venues consistently). Add later venue-by-venue if needed.

## Verification

End-to-end:

1. `cd market-tick-data-service && bash scripts/quality-gates.sh` — green on combo parser tests.
2. Single-day smoke: launch one VM at e2-highmem-8 for 2024-06-01 DERIBIT — Tardis log shows
   `OPTION-COMBOS streamed N rows`, canonical write at `instrument_type=option_combos/.../ticks.parquet`.
3. deployment-ui `:5183` data-status drilldown for DERIBIT 2024-06-01 — option_combos cell renders captured (green) or
   with proper missing-state classification.
4. Run a focused 1-week backfill — `MACHINE_TYPE=e2-highmem-8 bash launch-cefi-week-test.sh 2024-06-01 2024-06-07`.

## Owner / when

P2 — pick up after the OOM auto-kill plan (which has higher operational value). Reference: 2026-04-29 v2/v3 audit +
symbol-fallback parser shipped MTDS `f9482aa`.
