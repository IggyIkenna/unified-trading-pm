---
name: mtds_features_contract_audit_2026_05_20
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: research
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 2.4
status: complete
deadline: 2026-05-23
priority: P0
parent_epic: manifest_evolution_SUPERSEDED_2026_05_21
parent_plan: master_to_live_defi_2026_05_23.md
related_plans:
  - is_mtds_contract_audit_2026_05_20.md
  - is_features_contract_audit_2026_05_20.md
  - honest_coverage_formula_consolidation_2026_05_19.md
  - writegate_honest_coverage_endtoend_2026_05_06.md
---

# MTDS → features-service Contract Audit — 2026-05-20

> **C4 audit in the C-series** (C0 = IS→MTDS complete, C1 = IS→features complete). Trigger: A-phase diagnostics
> (2026-05-20) surfaced: A3 236k MISSING_EXPECTED + 765 DIVERGENT_EMPTY in MTDS; A5 warn-but-proceed violations in
> features-service commodity adapters; A6 13 BATCH_ONLY cells in MTDS (features-service downstream of those cells will
> receive no live data); schema drift (Int64→Datetime) in the perp_funding path confirmed in
> smoke_b_perp_funding_type_schema_drift_2026_05_17.md (subsumed by this audit). This document captures the full
> MTDS→features contract state at commit snapshot: **market-tick-data-service@fae9416 / features-service@33e85297**.

---

## 0. Header block

```yaml
pair: market-tick-data-service (MTDS) → features-service
auditor: slot-4 / ikenna (tab-4)
audit_date: 2026-05-20
audit_file: plans/audit/mtds_features_contract_audit_2026_05_20.md
feeds_ordering_step: D4 (MTDS adapters preflight plan) + D5 (features missing-data downgrade plan)
status: complete
upstream_sha: market-tick-data-service@fae9416
downstream_sha: features-service@33e85297
```

---

## The architectural contract (SSOT)

```
                    ┌────────────────────────────────┐
                    │  market-tick-data-service       │
                    │  (MTDS)                         │
                    │  ─ writes raw tick parquets     │
                    │    to market-data-tick-*,       │
                    │    perp-funding-*, lending-     │
                    │    indices-*, oracle-prices-*,  │
                    │    lst-rates-*, dex-pools-*     │
                    │    GCS buckets                  │
                    │  ─ writes manifest rows to      │
                    │    _index/availability_index.   │
                    │    parquet per (data_type,      │
                    │    shard_key, date)              │
                    └────────────┬───────────────────┘
                                 │
                                 ▼ read-only GCS parquets (no manifest preflight today)
                    ┌────────────────────────────────┐
                    │  features-service               │
                    │  ─ onchain family reads MTDS    │
                    │    bypass buckets directly      │
                    │    (perp_funding, rate_indices, │
                    │    oracle_prices, etc.) via     │
                    │    OnChainDataLoader            │
                    │  ─ cefi family reads MTDS       │
                    │    derivative_ticker via        │
                    │    resolve_bucket_name ✅       │
                    │  ─ NO MTDS manifest preflight   │
                    │    in any family ❌             │
                    │  ─ NO DependencyError on MTDS   │
                    │    missing data in onchain or   │
                    │    commodity families ❌        │
                    └────────────────────────────────┘
```

**The contract violations**:

1. features-service NEVER reads the MTDS `_index/availability_index.parquet` before computing features
2. features-service commodity adapters warn-but-proceed when upstream data returns empty (A5 violation)
3. 13 MTDS BATCH_ONLY cells mean features-service's live path silently gets no data for those (venue, data_type)
4. MTDS perp_funding parquets have timestamp stored as Int64 epoch-nanos instead of Datetime — features-service has a
   runtime cast workaround but the root is unfixed in MTDS

---

## Pre-audit grep evidence

### P1 — Hardcoded URL constants (in features-service as MTDS downstream)

```
features_service/commodity/adapters/open_meteo.py: _API_URL = "https://api.open-meteo.com/v1/forecast"
features_service/commodity/adapters/yahoo_finance.py: _YF_API_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
features_service/commodity/adapters/eia_crude.py: _BASE_URL = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
features_service/commodity/adapters/eia_ng.py: _BASE_URL = "https://api.eia.gov/v2/natural-gas/stor/wkly/data/"
features_service/commodity/adapters/baker_hughes.py: _DATA_URL = "https://rigcount.bakerhughes.com/..."
features_service/calendar/adapters/polygon_corporate_actions_adapter.py: _BASE_URL = "https://api.polygon.io"
features_service/calendar/engine/calculators/economic_calendar_loader.py: FRED_API_BASE = "https://api.stlouisfed.org/..."
```

**Assessment**: Commodity and calendar adapters fetch from their OWN upstream data sources (EIA, BH, CFTC, FRED,
Polygon), not from MTDS. These are not MTDS-owned URLs — the P1 IS→MTDS "hardcoded URL" violation pattern does not apply
here. These are P2 findings in C1 (IS→features). **Not a C4 violation.**

### P1 — Hardcoded token/market/venue lists

```bash
rg '[A-Z_]+_TOKENS\s*=\s*\[' features_service/ --type py → 0 hits
rg '[A-Z_]+_MARKETS\s*=\s*\[' features_service/ --type py → 0 hits
rg '[A-Z_]+_VENUES\s*=\s*\[' features_service/ --type py → 0 hits
```

No hardcoded universe lists found. **P1 universe-hardcode: CLEAN** (consistent with C1 finding).

### P1 — Upstream catalogue read calls (does features-service read MTDS manifest?)

```bash
rg 'availability_index|manifest' features_service/ --type py → 0 hits
rg 'record_captured|record_empty|record_failed' features_service/ --type py → count: 0 hits in MTDS-consumer path
```

**Features-service has ZERO reads of the MTDS availability_index.parquet.** The DependencyChecker probes MTDS GCS
prefixes for parquet file existence (`list_blobs`), but does NOT read the MTDS manifest rows to check `capture_status`
or `error_reason`. This means features-service cannot distinguish:

- An MTDS cell that is `attempted_failed` (bug — should raise DependencyError)
- An MTDS cell that is `empty_confirmed` (legitimate — should emit `record_empty` on features side)
- An MTDS cell that is `expected_unattempted` (not ready — should skip gracefully)

### P2 — Manifest emission in features-service handlers

```bash
rg 'record_captured|record_empty|record_failed|record_expected' features_service/ --type py
```

Files with manifest emission calls:

- `features_service/cefi/cli/handlers/perp_funding_handler.py` — 2 calls (record_empty ref in docstring; actual call
  commented out at line 81)
- `features_service/delta_one/cli/handlers/_expected_unattempted.py` — 1 call
- `features_service/sports/cli/handlers/batch_handler.py` — 5 calls ✅
- `features_service/volatility/cli/handlers/batch_handler.py` — 1 call ✅
- `features_service/onchain/calculators/perp_funding_rates_defi.py` — in docstring only; caller responsible
- Other manifest writers exist in `common/manifest_window_guard.py`, `common/manifest_leg_guard.py`,
  `cross_instrument/app/calculators/paired_spec_resolver.py`

Handlers with **zero** manifest emission:

- `features_service/onchain/cli/handlers/batch_handler.py` — **0 record\_\* calls** (6 except blocks)
- `features_service/commodity/cli/handlers/batch_handler.py` — **0 record\_\* calls**
- `features_service/multi_timeframe/cli/handlers/batch_handler.py` — **0 record\_\* calls**
- `features_service/cross_instrument/cli/handlers/batch_handler.py` — **0 record\_\* calls** (resolver has them)

### P5 — MTDS manifest preflight check

```bash
rg 'DependencyError|StaleUpstreamError' features_service/ --type py → 0 hits
rg 'availability_index|manifest' features_service/ --type py → 0 hits
```

**Zero** `DependencyError` raises found in features-service. **Zero** MTDS manifest reads before compute. The
`DependencyChecker` in `onchain/app/core/dependency_checker.py` checks GCS prefix existence (`list_blobs`) but not MTDS
manifest `capture_status`. All MTDS deps declared as `"required": False` for DEFI (lines 91-123 of
`dependency_checker.py`). This means: when MTDS has 236k MISSING_EXPECTED cells (A3), features-service silently proceeds
with empty inputs — no DependencyError, no manifest signal.

### P6 — Error classification at the boundary

```bash
rg 'classify_venue_error|ADAPTER_FETCH_FAILED' features_service/ --type py → 0 hits
```

**Zero** `classify_venue_error()` calls in features-service. Uses `classify_and_emit_error` (UTL wrapper) in commodity
adapters, or plain `logger.warning` + `return {}` in EIA adapters.

The specific A5 finding:

- `features_service/commodity/adapters/eia_ng.py:70` — `self.logger.warning("EIA storage API returned no data rows")`
  then `return {}` — warn-but-proceed
- `features_service/commodity/adapters/eia_crude.py:61` — identical pattern:
  `self.logger.warning("EIA crude storage API returned no data rows")` then `return {}`

Neither emits `record_empty(reason=SOURCE_RETURNED_ZERO)` — the manifest never receives the empty signal. Operator
confirmed these as REVIEW-BLOCKING at A5 audit (mega_audit issue, line 154-155).

### P7 — Bucket SSOT compliance

```bash
rg 'resolve_bucket_name' features_service/ --type py → confirmed in:
  onchain/engine/feature_observation_writer.py ✅
  onchain/calculators/perp_funding_rates_defi.py ✅
  cefi/calculators/perp_funding_rates.py ✅
  tests/conftest.py ✅
  tests/onchain/unit/test_feature_observation_writer.py ✅
```

Inline `f"gs://{bucket}/..."` f-strings found in:

- `onchain/engine/feature_observation_writer.py` (line 67) — bucket from `resolve_bucket_name`, URI f-string
  post-resolution (noqa annotated in C1)
- `onchain/calculators/perp_funding_rates_defi.py` — same pattern
- `cefi/calculators/perp_funding_rates.py` — same pattern
- `volatility/core/data_loader.py` — 7 violations (A1 CSV)

**Assessment**: Bucket name resolution IS wired via `resolve_bucket_name`. The f-string URI construction post-resolution
is a cosmetic violation — the bucket name itself is correct. **P7 PARTIALLY COMPLIANT.** No inline
`gs://market-data-tick-*` f-string that bypasses resolution found.

---

## 4-dimensional audit matrix (2026-05-20 snapshot)

### Dim 1 — MTDS adapter coverage per asset_group (upstream side)

| asset_group | Working MTDS adapters (batch)                                                                                                                                                                        | BATCH_ONLY (no live)                                                                                            | MISSING_BOTH                                                                                                  |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| DeFi        | dex_pools, dex_swaps, lending_indices, oracle_prices, lst_rates, perp_funding (Hyperliquid+Aster+GMX), vault_share_price, gas_fees, governance, mev, eigenlayer, flash_loan, bridge, token_transfers | curve(dex_pools/dex_swaps), jito(lst_rates), morpho(lending_indices)                                            | 89 cells (aavev3/aave_v2/compound/uniswap/balancer/curve/sushi/pancakeswap/phoenix/orca/raydium/drift/… many) |
| CeFi        | derivative_ticker (Hyperliquid batch S3), some trades                                                                                                                                                | hyperliquid(book_snapshot_5/derivative_ticker/liquidations/trades), aster(liquidations/trades), deribit(trades) | 31 cells                                                                                                      |
| Sports      | (not primary MTDS scope)                                                                                                                                                                             | —                                                                                                               | 12                                                                                                            |
| Prediction  | polymarket/kalshi trades                                                                                                                                                                             | polymarket(trades), kalshi(trades)                                                                              | 0                                                                                                             |
| TradFi      | —                                                                                                                                                                                                    | 0                                                                                                               | 14                                                                                                            |

**Key for C4**: The 13 BATCH_ONLY cells in MTDS (A6 finding) mean features-service's live-mode path will silently
receive no data for those (venue, data_type) pairs. The live computation proceeds with empty inputs — no signal emitted.

**236k MISSING_EXPECTED cells (A3)** across all asset_groups. **765 DIVERGENT_EMPTY cells in DeFi alone.** These
propagate to features-service as silently-empty compute runs.

### Dim 2 — features-service MTDS-consumption status per family

| Family / Key module                                                               | MTDS read mechanism                                                                              | Status                                                                                               | Evidence      |
| --------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------- | ------------- |
| `onchain/app/core/data_loader.py` — `load_derivative_ticker()`                    | `_resolve_mtds_parquet_files("perp_funding", date_str)` → `list_blobs` on perp-funding bucket    | ⚠ Reads MTDS GCS directly; NO manifest preflight; has Int64→Datetime cast workaround (lines 529-543) | lines 509-548 |
| `onchain/app/core/data_loader.py` — `load_rate_indices()`                         | `_resolve_mtds_parquet_files("rate_indices", date_str)` → `list_blobs` on lending-indices bucket | ⚠ Reads MTDS GCS directly; NO manifest preflight; empty = silent return                              | lines 433-464 |
| `onchain/app/core/data_loader.py` — `load_oracle_prices()`                        | `_resolve_mtds_parquet_files("oracle_prices", date_str)` → `list_blobs` on oracle-prices bucket  | ⚠ Reads MTDS GCS directly; NO manifest preflight                                                     | lines 475-506 |
| `onchain/adapters/mtds_canonical_reader.py` — `read_canonical_defi_parquets()`    | `list_blobs` on MTDS DeFi buckets; legacy category= fallback                                     | ⚠ Reads MTDS GCS; NO manifest preflight; silent empty on missing data                                | lines 85-138  |
| `cefi/calculators/perp_funding_rates.py` — `compute_cefi_funding_rates()`         | Direct `pl.read_parquet(gcs_uri)` on MTDS market-data-tick-cefi bucket                           | ⚠ Direct parquet read; NO manifest preflight; exception → `_empty_schema()`                          | lines 96-105  |
| `onchain/calculators/perp_funding_rates_defi.py` — `compute_defi_funding_rates()` | Direct `pl.read_parquet(gcs_glob)` on MTDS perp-funding-defi bucket                              | ⚠ Direct parquet read; NO manifest preflight; exception → `_empty_schema()`                          | lines 89-98   |
| `onchain/app/core/dependency_checker.py` — `check_dependencies()`                 | `DependencyChecker.UPSTREAM_DEPS_DEFI` probes GCS prefix existence (list_blobs)                  | ⚠ Existence check only — does NOT read MTDS manifest capture_status                                  | lines 91-176  |
| `commodity/adapters/eia_ng.py` — `EIAWeeklyStorageAdapter.fetch()`                | External EIA API (not MTDS); empty rows → warn + `return {}`                                     | **❌ A5 VIOLATION — warn-but-proceed; no manifest record_empty**                                     | lines 69-71   |
| `commodity/adapters/eia_crude.py` — `EIAWeeklyCrudeStorageAdapter.fetch()`        | External EIA API (not MTDS); empty rows → warn + `return {}`                                     | **❌ A5 VIOLATION — warn-but-proceed; no manifest record_empty**                                     | lines 60-62   |

### Dim 3 — Manifest emission discipline per handler (features-service output side)

| Handler                                          | Status                                                                                                                             | Evidence                 |
| ------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| `sports/cli/handlers/batch_handler.py`           | ✅ Emits `record_captured`, `record_empty(reason=...)`, `record_failed` per shard                                                  | lines 394-427, 488-515   |
| `volatility/cli/handlers/batch_handler.py`       | ✅ `record_captured` + `record_expected_unattempted` via `_record_out_of_scope_instruments`                                        | lines 281-322            |
| `cefi/cli/handlers/perp_funding_handler.py`      | ⚠ `record_empty` call **commented out** at line 81; docstring says caller should invoke it but caller (CLI dispatcher) has no wire | line 81                  |
| `onchain/cli/handlers/batch_handler.py`          | **❌ Silent absence** — 6 except blocks; all exit with `logger.warning` only; 0 `record_*` calls                                   | lines 97-161             |
| `commodity/cli/handlers/batch_handler.py`        | **❌ Silent absence** — commodity family has no manifest writes; batch runs invisibly                                              | grep: 0 record\_\* calls |
| `multi_timeframe/cli/handlers/batch_handler.py`  | **❌ Silent absence** — 0 manifest record\_\* calls found                                                                          | grep: 0 hits             |
| `cross_instrument/cli/handlers/batch_handler.py` | ⚠ `paired_spec_resolver.py` has record calls; top-level handler unclear; A1 CSV shows 4 violations                                 | A1 CSV                   |
| `calendar/engine/calendar_orchestrator.py`       | ⚠ `record_empty(reason="SOURCE_RETURNED_ZERO")` emitted but uses string literal not enum                                           | line 317                 |

### Dim 4 — Manifest schema version (MTDS output + features-service manifest)

| Bucket / domain                                                           | Schema version                                                                                                    | Action            |
| ------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- | ----------------- |
| `gs://market-data-tick-{cefi,defi,tradfi,sports,prediction}-prd-*`        | v8 (per is_mtds_contract_audit_2026_05_20.md Dim 4 — confirmed)                                                   | OK                |
| `gs://perp-funding-prd-*`                                                 | v8 (per is_mtds_contract_audit_2026_05_20.md)                                                                     | OK                |
| `gs://lending-indices-prd-*`                                              | v8                                                                                                                | OK                |
| `gs://features-onchain-*`                                                 | Not directly audited; UTL ManifestWriter defaults to v8; no hardcoded `schema_version=[1-7]` in features_service/ | Verify at runtime |
| `gs://features-sports-prd-*`                                              | Not directly audited; same assumption                                                                             | Verify at runtime |
| Code-level hardcodes: `rg 'schema_version\s*=\s*[1-7]' features_service/` | **0 hits**                                                                                                        | Clean             |

**P3 Assessment**: No code-level schema version hardcodes in features-service. The more fundamental problem (Dim 3) is
that 4 handler families have NO manifest writes at all — their schema version question is moot.

---

## Findings summary — severity classified

### P0 Findings (review-blocking — MUST fix before May-23)

**F1 — perp_funding Int64→Datetime schema drift (MTDS upstream root)**

- Component: `market-tick-data-service/market_tick_data_service/cli/handlers/perp_funding_handler.py`
- Symptom confirmed: Smoke B VM `features-onchain-defi-20260517-171908` —
  `ERROR: type Int64 is incompatible with expected type Datetime('ns', 'UTC')` on perp_funding parquets for dates
  2026-04-10..12
- Root: MTDS `perp_funding_handler.py` writes `timestamp` column as `Int64` epoch-nanoseconds; downstream expects
  `Datetime('ns','UTC')`
- Workaround in place: `features_service/onchain/app/core/data_loader.py` lines 532-543 cast Int64→Datetime at read time
- Why workaround is insufficient: mixed-precision files (same parquet has some Int64 shards, some Datetime) cause
  `pl.concat` failures before the post-concat cast reaches them; per smoke_b issue 4 of 5 dates still errored after the
  workaround
- Fix required: MTDS `perp_funding_handler.py` MUST write `timestamp` as `Datetime('us', 'UTC')` (canonical schema);
  remove the cast workaround in features-service after MTDS fix + re-backfill
- Impact: Every features-service compute touching `perp_funding` for CeFi and DeFi is at risk of silent date-drop or
  type error

**F2 — features-service onchain family: ZERO manifest emissions (silent absence)**

- File: `features_service/onchain/cli/handlers/batch_handler.py`
- Pattern: 6 except blocks; all paths exit with `logger.warning` only; 0 `record_captured`, `record_empty`, or
  `record_failed` calls anywhere in the handler body
- Impact: Every onchain feature group × date combination is DIVERGENT_EMPTY in the manifest — the operator has no signal
  when onchain features fail silently; data-status dashboard cannot distinguish "ran clean" from "silently failed"
- Fix: Wire `ManifestWriter` into `BatchHandler`; add `record_captured` / `record_empty(reason=...)` / `record_failed`
  at each shard completion path

**F3 — features-service commodity family: ZERO manifest emissions (A5 REVIEW-BLOCKING)**

- Files: `features_service/commodity/adapters/eia_ng.py:70`, `features_service/commodity/adapters/eia_crude.py:61`
- Pattern: When EIA API returns 0 data rows, adapter logs `logger.warning(...)` and `return {}` — no
  `record_empty(reason=SOURCE_RETURNED_ZERO)`, no `DependencyError`
- Operator confirmation: A5 finding marked REVIEW-BLOCKING in mega_audit_and_plan_beefup_progression_2026_05_20.md lines
  154-155
- Impact: Commodity (TradFi) feature runs silently skip days when EIA is down or returns empty; manifest shows
  `MISSING_EXPECTED` instead of `empty_confirmed`; strategy-service has no freshness signal for commodity features
- Fix: Add `record_empty(reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO)` in the empty-rows path; raise
  `DependencyError(fail_fast=True)` when the API fetch itself fails (not just empty)

**F4 — features-service: NO MTDS manifest preflight for any family**

- File: `features_service/onchain/app/core/dependency_checker.py`
- Pattern: `DependencyChecker` probes MTDS GCS prefixes for file existence (`list_blobs`) but does NOT read MTDS
  `_index/availability_index.parquet` to check `capture_status` / `error_reason`
- Impact: features-service cannot distinguish `attempted_failed` (should raise `DependencyError`) from `empty_confirmed`
  (should `record_empty`) from `captured` (proceed normally). With 236k MISSING_EXPECTED + 765 DIVERGENT_EMPTY in MTDS,
  features-service silently computes on empty inputs
- Fix: Extend `DependencyChecker.check_dependencies()` to read MTDS manifest rows for the requested (date, asset_group,
  venue, data_type) set. Raise `DependencyError(fail_fast=True)` when MTDS cell is `attempted_failed`. Emit
  `record_empty(reason=EXPECTED_UPSTREAM_EMPTY)` when MTDS cell is `empty_confirmed` with a legitimate reason

**F5 — cefi perp_funding_handler: record_empty commented out**

- File: `features_service/cefi/cli/handlers/perp_funding_handler.py`, line 81
- Pattern: `# manifest_writer.record_empty(reason=EXPECTED_NO_FUNDING_RATE_TICKS)` — intentionally commented out in the
  empty-result branch (lines 75-96)
- Impact: Empty funding-rate days (e.g. exchange downtime, data gap) are NOT recorded in manifest; manifest shows
  `MISSING_EXPECTED` for those dates; strategy cannot distinguish "no funding rate data" from "features-service didn't
  run"
- Fix: Uncomment and wire the `record_empty` call; ensure `ManifestWriter` is injected into `run_batch()`

**F6 — 13 MTDS BATCH_ONLY cells block features-service live path**

- Source: A6 audit `batch_live_adapter_parity_2026_05_20_summary.md`
- Cells: hyperliquid(book_snapshot_5/derivative_ticker/liquidations/trades), aster(liquidations/trades),
  deribit(trades), curve(dex_pools/dex_swaps), jito(lst_rates), morpho(lending_indices), kalshi(trades),
  polymarket(trades)
- Impact: features-service live-mode computes on these (venue, data_type) pairs will produce empty outputs; no live
  adapter means no live tick data; live features = 0 for affected strategies
- Fix in MTDS: Build live adapter equivalents for each BATCH_ONLY cell per "Batch = Live" HARD RULE
- Fix in features-service: Add `record_empty(reason=EXPECTED_UPSTREAM_EMPTY)` when MTDS live path returns no data for
  these known-BATCH_ONLY cells; do NOT silently return empty DataFrame

### P1 Findings (should fix before May-23, non-blocking if P0s done)

**F7 — multi_timeframe batch handler: zero manifest emissions**

- File: `features_service/multi_timeframe/cli/handlers/batch_handler.py`
- Pattern: 0 `record_*` calls; multi-timeframe feature runs invisible to data-status dashboard
- Fix: Wire ManifestWriter; emit record_captured / record_empty per (feature_group, date) shard

**F8 — cross_instrument batch handler: manifest emission coverage unclear**

- File: `features_service/cross_instrument/cli/handlers/batch_handler.py`
- Pattern: `paired_spec_resolver.py` has record calls but top-level batch handler body is unclear; A1 CSV shows 4
  violations
- Fix: Audit `cross_instrument/cli/handlers/batch_handler.py` end-to-end; confirm every (pair, date) shard ends with a
  `record_*` call

**F9 — MTDS perp_funding: BATCH_ONLY for Hyperliquid derivative_ticker (no live feed)**

- Source: A6 batch_live_adapter_parity summary
- Impact: features-service cefi `compute_cefi_funding_rates()` reads `derivative_ticker` from MTDS market-data-tick-cefi
  bucket; this is BATCH_ONLY — no live WebSocket adapter exists for Hyperliquid derivative_ticker in MTDS
- Fix (MTDS): Add live WebSocket adapter for Hyperliquid derivative_ticker (per Batch=Live rule)
- Fix (features-service): In `perp_funding_rates.py`, when live MTDS path is empty for known-BATCH_ONLY venue, emit
  `record_empty(reason=EXPECTED_UPSTREAM_EMPTY)` + log a MTDS live-gap warning

**F10 — calendar orchestrator: string literal reason in record_empty**

- File: `features_service/calendar/engine/calendar_orchestrator.py:317`
- Pattern: `record_empty(reason="SOURCE_RETURNED_ZERO")` — string literal not
  `EmptyConfirmedReason.SOURCE_RETURNED_ZERO` enum
- Impact: Type-safety gap; UAC reason enum changes silently bypass detection
- Fix: Import `EmptyConfirmedReason` from `unified_api_contracts` (not deep path); replace string literals

---

## Detailed finding: perp_funding schema drift (P0 — F1)

This finding was first captured in `smoke_b_perp_funding_type_schema_drift_2026_05_17.md` and has been subsumed by this
C4 audit per mega_audit triage (issue file line 13).

**Evidence chain**:

1. MTDS `perp_funding_handler.py` writes timestamp as epoch-nanoseconds integer (`Int64`) in some shards
2. `features_service/onchain/app/core/data_loader.py` `load_derivative_ticker()` (lines 529-543) added a per-shard cast:
   `if part["timestamp"].dtype in (pl.Int64, pl.Int32): part = part.with_columns(pl.col("timestamp").cast(pl.Datetime("ns", "UTC")))`
3. A post-concat cast was also added: `df.with_columns(pl.from_epoch(pl.col("timestamp"), time_unit="ns"))`
4. Despite both casts, 4 of 5 dates still errored in Smoke B VM `features-onchain-defi-20260517-191412`
5. Shard-level isolation (`except (ConnectionError, TimeoutError, OSError, ValueError)`) catches type errors and
   silently skips the shard — so the smoke VM continued but those dates had 0 perp_funding features

**Root cause in MTDS** (the upstream fix required):

- `market-tick-data-service/market_tick_data_service/cli/handlers/perp_funding_handler.py` writes timestamp as plain
  integer epoch rather than casting to `pl.Datetime("us", "UTC")` before writing
- The canonical schema for MTDS output requires `timestamp: Datetime[us, UTC]` (per UAC `InstrumentType` output
  contracts)
- Mixed files (some shards Int64, some Datetime) cause `pl.concat(frames, how="diagonal_relaxed")` to produce a column
  with dtype `Int64` that post-concat cast cannot recover

**Schema comparison (MTDS writes vs features-service expects)**:

| Field                               | MTDS actual (some shards)   | features-service expected                          | Status                              |
| ----------------------------------- | --------------------------- | -------------------------------------------------- | ----------------------------------- |
| `timestamp`                         | `Int64` (epoch nanoseconds) | `Datetime('ns', 'UTC')` or `Datetime('us', 'UTC')` | **DRIFT**                           |
| `funding_rate`                      | `Float64` or `Decimal`      | `Float64`                                          | OK (Decimal→float cast at line 145) |
| `symbol` / `instrument_id` / `coin` | varies by shard origin      | dynamic fallback (lines 102-105)                   | ⚠ fragile                           |

---

## QG-ratchet phase

### Phase Q — QG enforcement (the gates that should have caught this)

| Pattern                          | QG script                                       | Status in features-service QG                                |
| -------------------------------- | ----------------------------------------------- | ------------------------------------------------------------ |
| P2 — Manifest emission           | `no_silent_absence_handlers.sh`                 | **GAP** — not wired into features-service `quality-gates.sh` |
| P4 — Honest-absence reasons      | inline `rg 'record_empty.*reason\s*=\s*""'`     | **GAP**                                                      |
| P5 — expected_coverage preflight | MTDS manifest read (not a QG script yet)        | **GAP**                                                      |
| P6 — Error classification        | `no_adapter_contract_regression.sh` (STEP 5.83) | SHIPPED (wired line 71 of features-service QG)               |
| P7 — Bucket SSOT                 | `check_inline_bucket_uri.py` (STEP 5.69)        | Via base-service.sh (need to verify ratchet baseline)        |

**Gaps to add**:

```bash
# In features-service quality-gates.sh — add after STEP 5.83:

# STEP TBD: No silent absence in features-service handlers
log_section "[5.X/6] NO SILENT ABSENCE — FEATURES HANDLERS"
QG_SCRIPTS_DIR="${WORKSPACE_ROOT}/unified-trading-pm/scripts/qg"
if [[ -f "${QG_SCRIPTS_DIR}/no_silent_absence_handlers.sh" ]]; then
    run_timeout 60 bash "${QG_SCRIPTS_DIR}/no_silent_absence_handlers.sh" "${WORKSPACE_ROOT}/features-service" \
        || log_error "Silent absence handler detected in features-service"
fi

# STEP TBD: No blank reason strings in record_empty calls
log_section "[5.X/6] NO BLANK RECORD_EMPTY REASONS"
if rg -q 'record_empty\s*\(.*reason\s*=\s*""' --type py "$SOURCE_DIR"; then
    log_error "Blank reason= in record_empty() — raises LegacyBlankErrorReasonError at runtime"
fi
```

---

## Phased execution DAG (remediation)

```
Phase 1 — MTDS perp_funding timestamp fix (upstream root cause)
   │  Fix: perp_funding_handler.py writes Datetime not Int64
   │  After: remove workaround cast in features-service data_loader.py
   │
   ├── Phase 2 — features-service manifest emission wiring
   │  Fix F2: onchain BatchHandler wire ManifestWriter
   │  Fix F3: commodity eia_ng/eia_crude emit record_empty + DependencyError
   │  Fix F5: cefi perp_funding_handler uncomment record_empty
   │  Fix F7: multi_timeframe handler wire ManifestWriter
   │
   ├── Phase 3 — MTDS manifest preflight in features-service DependencyChecker
   │  Fix F4: DependencyChecker reads MTDS availability_index before compute
   │  Raises DependencyError(fail_fast=True) on attempted_failed MTDS cells
   │  Emits record_empty(reason=EXPECTED_UPSTREAM_EMPTY) on empty_confirmed MTDS cells
   │
   ├── Phase 4 — MTDS BATCH_ONLY live adapter gap (13 cells, F6)
   │  Fix in MTDS: build live adapter equivalents per Batch=Live rule
   │  Fix in features-service: record_empty on known-BATCH_ONLY live gaps
   │
   └── Phase Q — QG enforcement
      Wire no_silent_absence_handlers.sh + blank-reason check into features-service QG
```

**Foundation-completion-gate rule**: Phase 2 (manifest emission) must be GREEN before Phase 3 (MTDS manifest preflight)
ships — you cannot validate the preflight without emission wired.

---

## Continuous-verification column

| Pattern                     | Continuous-verification path                                             | Cadence               | Last verified                                        |
| --------------------------- | ------------------------------------------------------------------------ | --------------------- | ---------------------------------------------------- |
| P1 — Hardcoded URLs         | `no_hardcoded_venue_urls.sh` (base-service.sh)                           | every push            | 2026-05-20 (0 hits)                                  |
| P2 — Manifest emission      | `no_silent_absence_handlers.sh` in QG (ONCE ADDED)                       | every push            | NOT YET WIRED                                        |
| P3 — Schema version         | inline `rg 'schema_version\s*=\s*[1-7]'` (ONCE ADDED)                    | every push            | 2026-05-20 (0 code hits; manifest bucket unverified) |
| P4 — Honest-absence reasons | `LegacyBlankErrorReasonError` at runtime + inline rg (ONCE ADDED)        | every push            | NOT YET WIRED                                        |
| P5 — MTDS preflight         | `DependencyChecker` MTDS manifest read (ONCE BUILT)                      | every batch run       | NOT YET BUILT                                        |
| P6 — Error classification   | `no_adapter_contract_regression.sh` (STEP 5.83)                          | every push            | 2026-05-20 (shipped)                                 |
| P7 — Bucket SSOT            | `check_inline_bucket_uri.py` (STEP 5.69 via base-service.sh)             | every push            | 2026-05-20 (partial — see is_features C1)            |
| perp_funding schema drift   | `load_derivative_ticker` cast workaround active; MTDS root not fixed     | every batch run       | 2026-05-20 (workaround active, root open)            |
| MTDS BATCH_ONLY propagation | Post-hoc divergence scanner (A3-style) against features-service manifest | daily scheduled audit | NOT YET RUN                                          |

---

## Scope exclusions

**P3 (schema-version)**: No code-level `schema_version=[1-7]` hardcodes in features-service. The concern is moot for the
4 handler families with no manifest writes (Dim 3 gap is the upstream problem).

**P1 (SSOT-owned reference — hardcoded URLs)**: Commodity + calendar URL constants are external API endpoints (EIA, BH,
CFTC, FRED, Polygon) that instruments-service does not catalogue. These are a C1 finding, not a C4 finding. Not a
MTDS→features contract violation.

**P1 (token/market lists)**: `0 hits` — features-service has no hardcoded universe lists post-C1 is consistent with
pre-existing C0 cleanup. Verified clean.

---

## Known A-phase findings incorporated

| Phase         | Finding                                                                       | Incorporated as                                                               |
| ------------- | ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| A3            | 236k MISSING_EXPECTED + 765 DIVERGENT_EMPTY in MTDS                           | F4 context (no MTDS manifest preflight); F2/F3 impact (silent empty features) |
| A5            | eia_ng.py:70 + eia_crude.py:61 warn-but-proceed (REVIEW-BLOCKING)             | F3 (P0 finding)                                                               |
| A6            | 13 BATCH_ONLY cells in MTDS — no live adapter                                 | F6 (P0 finding)                                                               |
| A1            | 215 record_emission violations workspace-wide; features-service top offender  | F2, F3, F5, F7 (P0/P1 findings)                                               |
| Smoke B issue | perp_funding Int64→Datetime drift (subsumed per mega_audit triage 2026-05-20) | F1 (P0 finding — full root cause documented here)                             |

---

## Remediation items (plan todos)

- [ ] **P0. F1. Fix MTDS perp_funding_handler.py timestamp dtype** — write `pl.Datetime("us", "UTC")` not Int64;
      re-backfill affected dates; remove cast workaround in features-service `data_loader.py` after MTDS fix verified.
      Owner: MTDS team.
- [ ] **P0. F2. Wire ManifestWriter into features-service onchain BatchHandler** — add `record_captured` /
      `record_empty(reason=...)` / `record_failed` at each shard completion; remove EnhancedError-only error paths.
      Owner: features-service.
- [ ] **P0. F3. Fix commodity eia_ng + eia_crude warn-but-proceed (REVIEW-BLOCKING per A5)** — replace
      `logger.warning + return {}` on empty rows with `record_empty(reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO)`;
      raise `DependencyError(fail_fast=True)` on API fetch failure. Owner: features-service.
- [ ] **P0. F4. Build MTDS manifest preflight in features-service DependencyChecker** — read MTDS
      `_index/availability_index.parquet` for requested (date, asset_group, venue, data_type) before compute; raise
      `DependencyError` on `attempted_failed`; emit `record_empty(reason=EXPECTED_UPSTREAM_EMPTY)` on `empty_confirmed`.
      Owner: features-service.
- [ ] **P0. F5. Uncomment record_empty in cefi perp_funding_handler.py line 81** — wire ManifestWriter into
      `run_batch()`; ensure empty-result days record `record_empty(reason=EXPECTED_NO_FUNDING_RATE_TICKS)`. Owner:
      features-service.
- [ ] **P0. F6. Build live adapter equivalents for 13 BATCH_ONLY MTDS cells** — per Batch=Live HARD RULE; highest
      priority: hyperliquid(derivative_ticker), jito(lst_rates), morpho(lending_indices). Owner: MTDS team (tracked in
      D4 plan).
- [ ] **P1. F7. Wire ManifestWriter into multi_timeframe BatchHandler.** Owner: features-service.
- [ ] **P1. F8. Audit cross_instrument batch handler end-to-end for manifest emission coverage.** Owner:
      features-service.
- [ ] **P1. F9. Add record_empty for known-BATCH_ONLY upstream gaps in live mode.** Owner: features-service.
- [ ] **P1. F10. Replace string literal reasons with EmptyConfirmedReason enum in calendar_orchestrator.py.** Owner:
      features-service.
- [ ] **Phase Q. Wire no_silent_absence_handlers.sh + blank-reason rg check into features-service quality-gates.sh.**
      Owner: features-service.

---

## Temporary states + their canonical follow-up plans

- `load_derivative_ticker` Int64→Datetime cast workaround at `features_service/onchain/app/core/data_loader.py:529-543`
  — TEMPORARY. Retires when MTDS `perp_funding_handler.py` writes canonical Datetime dtype + affected dates
  re-backfilled. Plan: D4 MTDS adapters preflight plan (Phase Phase 1 of remediation DAG above).
- `DependencyChecker.UPSTREAM_DEPS_DEFI` with all MTDS deps as `"required": False` — TEMPORARY. Retires when MTDS
  manifest preflight (F4) ships and correct `required=True` / `DependencyError` logic is in place.
- The `record_empty` commented out at `cefi/cli/handlers/perp_funding_handler.py:81` — TEMPORARY workaround. Retires
  when ManifestWriter is wired (F5 above).

---

## Cross-plan references

- **D4 (MTDS adapters preflight plan)**: F1 (perp_funding dtype fix), F4 (MTDS manifest preflight), F6 (BATCH_ONLY live
  gaps) feed directly into D4's scope.
- **D5 (features missing-data downgrade plan)**: F2, F3, F4, F5, F7 (manifest emission + DependencyError wiring) are the
  core deliverables of D5.
- **C0 (IS→MTDS contract audit, complete)**: confirmed v8 manifest + no-silent-absence + no-hardcoded-URLs in MTDS —
  those are GREEN. C4 picks up from MTDS output downstream.
- **C1 (IS→features contract audit, complete)**: identified F2/F3/F5/F7 manifest emission gaps first; C4 adds the
  MTDS-specific causal chain (F1 dtype drift, F4 preflight, F6 batch_only).
