---
name: is_features_contract_audit_2026_05_20
locked_by: live-defi-rollout
locked_since: 2026-05-20
estimate_class: research
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 3.6
status: complete
deadline: 2026-05-23
priority: P0
parent_epic: manifest_evolution_SUPERSEDED_2026_05_21
parent_plan: master_to_live_defi_2026_05_23.md
related_plans:
  - is_mtds_contract_audit_2026_05_20.md
  - honest_coverage_formula_consolidation_2026_05_19.md
  - writegate_honest_coverage_endtoend_2026_05_06.md
---

# instruments-service → features-service Contract Audit — 2026-05-20

> **C1 audit in the C-series** (C0 = IS→MTDS, complete). Trigger: A-phase diagnostics (2026-05-20) found sports
> bookmakers 100% `MISSING_EXPECTED`, warn-but-proceed patterns in commodity adapters, and zero `classify_venue_error`
> usage in the onchain batch handler. This audit documents the full IS→features contract state at commit snapshot:
> **instruments-service@04e49f7 / features-service@33e85297**.

## 0. Header block

```yaml
pair: instruments-service → features-service
auditor: slot-4 / ikenna (tab-4)
audit_date: 2026-05-20
audit_file: plans/audit/is_features_contract_audit_2026_05_20.md
feeds_ordering_step: D1 (IS hardening) + D5 (features missing-data downgrade)
status: complete
upstream_sha: instruments-service@04e49f7
downstream_sha: features-service@33e85297
```

## The architectural contract (SSOT)

```
                    ┌────────────────────────────────┐
                    │  instruments-service           │
                    │  ─ enumerates venue universe   │
                    │  ─ writes InstrumentRecord /   │
                    │    PoolRecord / SportsFixture  │
                    │    per (venue, instrument_id,  │
                    │    day) to instruments-store-* │
                    │  ─ owns archive metadata,      │
                    │    coverage_start/end,         │
                    │    listed_at/delisted_at        │
                    └────────────┬───────────────────┘
                                 │
                                 ▼ read-only GCS catalogue
                    ┌────────────────────────────────┐
                    │  features-service              │
                    │  ─ reads IS GCS output for     │
                    │    sports (gcs_reader.py) ✅   │
                    │  ─ delta_one reads IS for      │
                    │    instrument_type filter ✅   │
                    │  ─ volatility HARDCODES        │
                    │    universe (BTC+ETH only) ❌  │
                    │  ─ onchain / commodity /       │
                    │    calendar: NO IS reads ❌    │
                    │  ─ cefi: NO IS reads ❌        │
                    └────────────────────────────────┘
```

**The contract violation**: features-service families outside `sports` and `delta_one` do NOT read instruments-service
GCS output to enumerate their universe. They either hardcode it (volatility: `["BTC", "ETH"]`) or implicitly derive it
from upstream MTDS data — neither is the canonical IS-first path.

---

## Pre-audit grep evidence

### P1 grep — hardcoded URL constants

```
features_service/calendar/adapters/polygon_corporate_actions_adapter.py:26: _BASE_URL = "https://api.polygon.io"
features_service/commodity/adapters/open_meteo.py:88: _API_URL = "https://api.open-meteo.com/v1/forecast"
features_service/commodity/adapters/yahoo_finance.py:38: _YF_API_URL = "https://query1.finance.yahoo.com/v8/finance/chart"
features_service/commodity/adapters/eia_crude.py:27: _BASE_URL = "https://api.eia.gov/v2/petroleum/stoc/wstk/data/"
features_service/commodity/adapters/eia_ng.py:48: _BASE_URL = "https://api.eia.gov/v2/natural-gas/stor/wkly/data/"
features_service/commodity/adapters/baker_hughes.py:53: _DATA_URL = "https://rigcount.bakerhughes.com/static-files/..."
```

**Assessment**: These are external API endpoint URLs — NOT venue-universe or archive-metadata URLs that
instruments-service owns. They are commodity/calendar data source endpoints that IS does not catalog today. The
IS→downstream SSOT pattern applies when IS has written `InstrumentRecord.source_archive_url_template` for the venue; IS
has no commodity/calendar adapters. **These URLs are a separate, lower-priority finding (P2) — IS would need commodity
adapter family expansion to make this contract applicable.**

### P1 grep — hardcoded token/market/venue lists

```
rg '[A-Z_]+_TOKENS\s*=\s*\[' features_service/ --type py → 0 hits
rg '[A-Z_]+_MARKETS\s*=\s*\[' features_service/ --type py → 0 hits
rg '[A-Z_]+_VENUES\s*=\s*\[' features_service/ --type py → 0 hits
```

No token or market list hardcodes found in features-service (unlike MTDS pre-C0).

### P1 grep — IS catalogue read calls

```
rg 'load_.*_metadata_for_date|load_.*_catalog' features_service/ --type py → 0 hits
```

Zero `load_*_metadata_for_date()` calls. Features-service does NOT use the canonical MTDS-style IS read pattern. Sports
uses a lower-level GCS parquet read (`gcs_reader.py` → `resolve_instruments_bucket()`) which is valid but not the typed
API.

### P2 grep — manifest emission

Files using `record_captured|record_empty|record_failed`:

- `common/manifest_window_guard.py` ✅
- `common/manifest_leg_guard.py` ✅
- `onchain/calculators/perp_funding_rates_defi.py` ✅
- `cross_instrument/app/calculators/paired_spec_resolver.py` ✅
- `delta_one/cli/handlers/_expected_unattempted.py` ✅
- `volatility/cli/handlers/batch_handler.py` ✅
- `sports/compute/coverage_gate.py` ✅
- `sports/cli/handlers/batch_handler.py` ✅
- `calendar/engine/calendar_orchestrator.py` ✅
- `cefi/calculators/perp_funding_rates.py` ✅
- `cefi/cli/handlers/perp_funding_handler.py` ✅

Families with **no manifest emission** found in batch/live handlers:

- `onchain/cli/handlers/batch_handler.py` — 6 except blocks, **0 record\_\* calls** in handler body
- `commodity/cli/handlers/batch_handler.py` — **no record\_\* calls** found
- `multi_timeframe/cli/handlers/batch_handler.py` — **no record\_\* calls** found
- `cross_instrument/cli/handlers/batch_handler.py` — `paired_spec_resolver.py` has record calls, top-level handler
  unclear

### P4 grep — honest-absence reason taxonomy

String literal reasons (not enum):

```
features_service/calendar/engine/calendar_orchestrator.py:317: reason="SOURCE_RETURNED_ZERO"
features_service/sports/cli/handlers/batch_handler.py:405:   reason="SOURCE_RETURNED_ZERO"
features_service/sports/cli/handlers/batch_handler.py:496:   reason="SOURCE_RETURNED_ZERO"
```

These use string literals `"SOURCE_RETURNED_ZERO"` instead of `EmptyConfirmedReason.SOURCE_RETURNED_ZERO`. The UAC
`ManifestWriter.record_empty` MUST receive the enum or a string matching the closed set. At runtime,
`LegacyBlankErrorReasonError` only fires on blank `""` — but using raw strings bypasses type safety.

One confirmed UAC deep-path import (P6 sub-finding):

```
features_service/cefi/cli/handlers/perp_funding_handler.py:20:
  from unified_api_contracts.canonical.crosscutting.honest_coverage import EmptyConfirmedReason
```

This is a deep import (`canonical.*`) — A1 violation. Should be
`from unified_api_contracts import EmptyConfirmedReason`.

### P6 grep — error classification

```
rg 'classify_venue_error' features_service/ --type py → 0 hits
rg 'ADAPTER_FETCH_FAILED' features_service/ --type py → 0 hits
```

Features-service uses `classify_and_emit_error` (from UTL) as a wrapper — NOT the UAC `classify_venue_error()`. This is
a **semantic difference**: `classify_and_emit_error` is a general-purpose error classifier (not venue-specific);
`classify_venue_error()` routes errors through the UAC error taxonomy (30-code DefiErrorCode + per-venue FAIL/RETRY/SKIP
routing). Per CLAUDE.md and the workspace contract, every adapter MUST call `classify_venue_error()` from UAC.

Key violation: `onchain/cli/handlers/batch_handler.py` has **6 except blocks, 0 classify_venue_error calls**. Sports
batch handler has 12 except blocks, 4 `classify_and_emit_error` calls (not `classify_venue_error`).

### P7 grep — bucket SSOT

`resolve_bucket_name` usage confirmed in:

- `cefi/calculators/perp_funding_rates.py` ✅
- `onchain/engine/feature_observation_writer.py` ✅
- `onchain/calculators/perp_funding_rates_defi.py` ✅
- `common/__init__.py` (wrapper `resolve_features_bucket`) ✅

Inline `f"gs://{...}"` f-strings found in multiple files, BUT all carry `# noqa: gs-uri` comments asserting bucket name
is resolved by caller. **Assessment**: **P7 is PARTIALLY COMPLIANT** — bucket resolution via `resolve_bucket_name` is
wired, but f-string URI construction is still used post-resolution (cosmetically violates the intent; bucket name itself
is resolved correctly). A1 CSV confirms 7 violations in `volatility/core/data_loader.py` alone.

---

## 4-dimensional audit matrix (2026-05-20 snapshot)

### Dim 1 — IS adapter coverage per asset_group

| asset_group | IS adapters (can supply features-service)                              | features-service IS reads                                                                                 | Violation                                                |
| ----------- | ---------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | -------------------------------------------------------- |
| DeFi        | 54 adapters (Drift, Phoenix, Orca, Raydium, LST protocols, Aave, etc.) | **None** — onchain family reads MTDS GCS directly, derives universe from upstream data                    | ❌ onchain skips IS catalogue entirely                   |
| CeFi        | Aster, Deribit, Tardis, CCXT, Hyperliquid                              | **None** — cefi family reads MTDS GCS, no IS catalogue call                                               | ❌ cefi skips IS                                         |
| TradFi      | Databento, Polygon, IBKR                                               | **None** — volatility `_get_instruments()` hardcodes `["BTC", "ETH"]` for CEFI and `[]` for others        | ❌ hardcoded; empty list for TradFi = no TradFi features |
| Sports      | 11 per-source sports adapters (fixtures, odds, teams, leagues)         | ✅ `gcs_reader.py` reads `instruments-store-sports-*` GCS output; `resolve_instruments_bucket()` via UTL  | ✅ Compliant                                             |
| Prediction  | Polymarket, Kalshi                                                     | **None** — cross_instrument family processes prediction data from MTDS but no IS catalogue read confirmed | ❌ gap                                                   |
| Commodity   | **None** — IS has no commodity adapters today                          | N/A — no IS-owned commodity reference data                                                                | **GAP in IS** (not features-service violation)           |
| Calendar    | **None** — IS has no economic-calendar adapters                        | N/A                                                                                                       | **GAP in IS**                                            |

### Dim 2 — features-service handler IS-consumption status

| Family / Handler                                 | Status                                                                                                               | Evidence                    |
| ------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- | --------------------------- |
| `sports/data/gcs_reader.py`                      | ✅ Reads IS sports reference output via `resolve_instruments_bucket()` + GCS parquet walk                            | lines 1-9, 135-179, 440-477 |
| `delta_one/cli/handlers/batch_handler.py`        | ✅ Partial — reads IS `instrument_availability/` GCS output for type filter; falls back to ID-pattern when IS empty  | lines 735-760               |
| `volatility/cli/handlers/batch_handler.py`       | ❌ `_get_instruments()` hardcodes `["BTC", "ETH"]` for CEFI and `[]` for all other groups — no IS read               | lines 274-279               |
| `onchain/cli/handlers/batch_handler.py`          | ❌ No IS read; derives universe from MTDS-backed DependencyChecker; processes whatever feature groups are enumerated | lines 88-162                |
| `cefi/cli/handlers/perp_funding_handler.py`      | ❌ No IS read; reads MTDS `perp-funding` bucket directly                                                             | full file                   |
| `commodity/cli/handlers/batch_handler.py`        | N/A — IS has no commodity adapters; commodity family must self-enumerate from EIA/BH/CFTC                            | —                           |
| `calendar/cli/handlers/batch_handler.py`         | N/A — IS has no calendar adapters; calendar family self-enumerates from Polygon/FRED                                 | —                           |
| `multi_timeframe/cli/handlers/batch_handler.py`  | ⚠ Depends on upstream delta_one features; no direct IS call; acceptable if delta_one IS-consumption is correct      | —                           |
| `cross_instrument/cli/handlers/batch_handler.py` | ⚠ Processes paired instruments from MTDS catalog; no direct IS call; universe derived from paired instrument list   | —                           |

### Dim 3 — Manifest emission discipline per handler

| Family / Handler                                 | Status                                                                                                                                                                  | Evidence                 |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| `sports/cli/handlers/batch_handler.py`           | ✅ Emits `record_captured`, `record_empty(reason=...)`, `record_failed` per shard                                                                                       | lines 394-427, 488-515   |
| `volatility/cli/handlers/batch_handler.py`       | ✅ Emits `record_captured` + `record_expected_unattempted` via `_record_out_of_scope_instruments`                                                                       | lines 281-322            |
| `cefi/cli/handlers/perp_funding_handler.py`      | ⚠ `record_empty(reason=EXPECTED_NO_FUNDING_RATE_TICKS)` documented in docstring; actual emission call commented out at line 81 (`# manifest_writer.record_empty(...)`) | line 81                  |
| `onchain/cli/handlers/batch_handler.py`          | ❌ **Silent absence** — 6 except blocks catch exceptions with EnhancedError wrapping + `logger.warning` but NO `record_*` call in any path                              | lines 97-161             |
| `commodity/cli/handlers/batch_handler.py`        | ❌ **Silent absence** — commodity family has no manifest write calls; commodity batch runs, emits signal, but no manifest record                                        | grep: 0 record\_\* calls |
| `calendar/engine/calendar_orchestrator.py`       | ⚠ `record_empty(reason="SOURCE_RETURNED_ZERO")` emitted on empty day, but uses string literal not enum                                                                 | lines 314-323            |
| `multi_timeframe/cli/handlers/batch_handler.py`  | ❌ **Silent absence** — no manifest record\_\* calls found                                                                                                              | grep: 0 hits             |
| `cross_instrument/cli/handlers/batch_handler.py` | ⚠ `paired_spec_resolver.py` has record calls; top-level batch handler unclear — A1 CSV shows 4 violations                                                              | A1 CSV                   |

### Dim 4 — Manifest schema version per bucket

| Bucket                              | Schema version                                                                                              | Action                                   |
| ----------------------------------- | ----------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| `gs://features-onchain-defi-prd-*/` | Not audited (no schema_version hardcode found in code; bucket uses UTL ManifestWriter which defaults to v8) | Verify at runtime                        |
| `gs://features-sports-prd-*/`       | Not audited (ManifestWriter via UTL — should be v8)                                                         | Verify at runtime                        |
| `gs://features-volatility-*/`       | Not audited (ManifestWriter via UTL — should be v8)                                                         | Verify at runtime                        |
| Code-level hardcodes                | `rg 'schema_version\s*=\s*[1-7]' features_service/ → 0 hits`                                                | Clean — no hardcoded v4 like solana-defi |

**P3 Assessment**: No code-level schema version hardcodes found. The concern is that many features-service handlers have
no manifest writes at all (Dim 3), which means their "schema version" question is moot — there are no manifest rows to
migrate.

---

## Findings summary — severity classified

### P0 Findings (review-blocking, must fix before May-23)

**F1 — onchain batch handler: 0 manifest emissions (silent absence)**

- File: `features_service/onchain/cli/handlers/batch_handler.py`
- Pattern: 6 except blocks; all paths exit with `logger.warning` only; no `record_captured`, `record_empty`,
  `record_failed`
- Impact: DIVERGENT_EMPTY cells for every onchain feature group × date; operator has no signal when onchain features
  fail silently
- Fix: Add `record_captured` / `record_empty` / `record_failed` at each shard completion path; wire through
  `ManifestWriter`

**F2 — commodity batch handler: 0 manifest emissions (silent absence)**

- File: `features_service/commodity/cli/handlers/batch_handler.py`
- Pattern: Commodity batch pipeline emits `CommoditySignal` to event bus but writes no manifest rows
- Impact: No manifest coverage for commodity (tradfi) features; strategy reads commodity features without any
  data-freshness signal
- Fix: Add ManifestWriter to commodity batch handler; emit `record_captured` / `record_empty` per (commodity, date)
  shard

**F3 — multi_timeframe batch handler: 0 manifest emissions (silent absence)**

- File: `features_service/multi_timeframe/cli/handlers/batch_handler.py`
- Pattern: 0 `record_*` calls found
- Impact: Multi-timeframe feature runs invisible to data-status dashboard
- Fix: Same as F1/F2 — wire ManifestWriter

**F4 — volatility handler hardcodes instrument universe**

- File: `features_service/volatility/cli/handlers/batch_handler.py`, lines 274-279
- Pattern: `_get_instruments()` returns `["BTC", "ETH"]` for CEFI and `[]` for all other groups
- Impact: TradFi volatility features never computed (empty list); DeFi volatility never computed; instruments-service
  volatility adapter output is never consulted
- Fix: Replace `["BTC", "ETH"]` with an IS catalogue read; replace `[]` with IS-enumerated underlyings per asset_group

**F5 — cefi perp_funding: record_empty commented out**

- File: `features_service/cefi/cli/handlers/perp_funding_handler.py`, line 81
- Pattern: `# manifest_writer.record_empty(reason=EXPECTED_NO_FUNDING_RATE_TICKS)` — intentionally commented out
- Impact: Empty funding-rate days not recorded; manifest shows `MISSING_EXPECTED` instead of `empty_confirmed`
- Fix: Uncomment the `record_empty` call; ensure `ManifestWriter` instance is wired into the handler

**F6 — onchain batch handler: 0 classify_venue_error calls (P6 violation)**

- File: `features_service/onchain/cli/handlers/batch_handler.py`
- Pattern: 6 except blocks use `EnhancedError` + `logger.warning`; no `classify_venue_error()` from UAC
- Impact: Onchain adapter errors not routed through the 30-code DefiErrorCode taxonomy; FAIL/RETRY/SKIP routing absent
- Fix: Replace `EnhancedError` error handling with `classify_venue_error()` + `recorder.record_failed()`

**F7 — sports batch handler: 8+ unclassified except blocks (partial P6)**

- File: `features_service/sports/cli/handlers/batch_handler.py`
- Pattern: 12 except blocks total; only 4 use `classify_and_emit_error` (UTL wrapper — not UAC's `classify_venue_error`)
- Impact: Sports errors classified at generic severity level, not through sports/venue-specific taxonomy
- Fix: Replace `classify_and_emit_error` with `classify_venue_error()` where applicable

### P1 Findings (should fix before May-23, non-blocking if P0s done)

**F8 — sports + calendar: string literal reasons in record_empty**

- Files: `sports/cli/handlers/batch_handler.py:405,496`, `calendar/engine/calendar_orchestrator.py:317`
- Pattern: `reason="SOURCE_RETURNED_ZERO"` (string) vs `reason=EmptyConfirmedReason.SOURCE_RETURNED_ZERO` (enum)
- Impact: Type-safety gap; future UAC reason enum changes won't be caught at import time
- Fix: Import `EmptyConfirmedReason` + replace string literals with enum members

**F9 — cefi handler: UAC deep-path import (A1 violation)**

- File: `features_service/cefi/cli/handlers/perp_funding_handler.py:20`
- Pattern: `from unified_api_contracts.canonical.crosscutting.honest_coverage import EmptyConfirmedReason`
- Impact: Breaks if UAC internal layout changes; violates `from unified_api_contracts import X` rule
- Fix: `from unified_api_contracts import EmptyConfirmedReason`

**F10 — volatility data_loader: 7 inline gs:// f-strings (A1 resolve_bucket_name violations)**

- File: `features_service/volatility/core/data_loader.py` (7 violations per A1 CSV)
- Pattern: `f"gs://{self.bucket}/processed_candles/..."` — bucket resolved upstream, f-string used for path construction
- Impact: QG ratchet counts these; needs `# noqa: gs-uri` suppression comments or refactor to URI helper
- Fix: Add `# noqa: gs-uri — URI construction; bucket resolved by caller` comments to match existing pattern in other
  files

**F11 — sports bookmaker universe: IS-driven or self-enumerated?**

- Files: `sports/data/gcs_reader.py`, `sports/tracking/_registry_data_b_part2.py`
- Pattern: `gcs_reader.py` reads IS sports reference (fixtures, teams, leagues) via `resolve_instruments_bucket()`.
  However, bookmaker universe (Pinnacle, Betfair, etc.) appears in feature registry entries
  (`_registry_data_b_part2.py:14,49-52`) as hardcoded feature keys — these are feature names, not a universe list. The
  actual bookmaker odds universe is sourced from MTDS tick data reads, not hardcoded lists.
- Assessment: **Not a P0 violation**. The A3 finding (100% MISSING_EXPECTED for sports bookmakers) is an IS adapter gap
  (IS sports adapters don't write bookmaker metadata), not a features-service hardcode.

### P2 Findings (post-cutover unless easy)

**F12 — commodity adapters: IS has no coverage + hardcoded external API URLs**

- Files: `commodity/adapters/eia_ng.py:48`, `eia_crude.py:27`, `baker_hughes.py:53`, `yahoo_finance.py:38`,
  `open_meteo.py:88`
- Assessment: IS has no commodity adapters today; these are public API endpoints for data sources IS doesn't own.
  Contract violation is N/A until IS expands to commodity. These URLs would only become a violation if/when IS ships
  commodity InstrumentRecord adapters.
- Fix (if IS expands): Migrate URLs to `InstrumentRecord.source_archive_url_template` in commodity IS adapters

**F13 — QG enforcement gaps: P1/P2/P3/P4/P5 ratchet scripts not wired in features-service**

- File: `features_service/scripts/quality-gates.sh`
- Pattern: Only STEP 5.83 (`no_adapter_contract_regression.sh`) is wired. `no_silent_absence_handlers.sh`,
  `no_hardcoded_venue_urls.sh`, `no_hardcoded_venue_universe.sh` (the three STEP 5.70 scripts) are NOT wired.
- Impact: P0 violations F1-F3 (silent absence) and F4 (hardcoded universe) have no automated gate; can re-regress
- Fix: Wire STEP 5.70 trio into features-service `quality-gates.sh`

---

## A-phase diagnostic cross-check

| A-phase finding                                                 | Root cause (this audit)                                                                                                                                                                                                                                                                                                                     | Severity             | Plan phase                           |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------- | ------------------------------------ |
| A3: sports bookmakers 100% MISSING_EXPECTED (25k cells)         | IS sports adapters don't write bookmaker metadata; features-service sports reads IS correctly but finds no bookmaker rows. Root cause is IS gap, not features hardcode.                                                                                                                                                                     | P1 for IS            | D1 (IS hardening)                    |
| A5: `eia_ng.py:70` + `eia_crude.py:61` warn-but-proceed         | Confirmed: `logger.warning("EIA storage API returned no data rows"); return {}` on empty fetch — silently returns empty dict. No `record_empty` at caller site either. Combined with F2 (commodity handler has no manifest writes).                                                                                                         | P0 (F1+F2)           | D5 (features missing-data downgrade) |
| A6: no BATCH_ONLY/GREEN for sports or tradfi in parity matrix   | Sports: live handler exists (`sports/cli/handlers/live_handler.py`) — correctly uses same code path. TradFi (volatility): live handler exists but `_get_instruments()` returns `[]` for TradFi (F4) — so live path never processes TradFi. Assessment: **BATCH_ONLY is a TradFi volatility universe bug (F4)**, not a missing live handler. | P0 (F4)              | D5                                   |
| A1: 995 UAC import surface violations; features-service has 230 | Features-service contributes 230 violations (4th worst repo). Main findings: `cefi/cli/handlers/perp_funding_handler.py:20` (F9 confirmed). Remaining 229 are in tests + smoke scripts (resolve_bucket_name pattern mostly).                                                                                                                | P1 (F9) + P2 (tests) | QG ratchet phase                     |

---

## QG-ratchet phase shape

### Phase Q — QG enforcement (gates that should have caught this)

| Pattern                          | QG script                                                       | Status in features-service                                                                        |
| -------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| P1 — SSOT-owned reference        | `no_hardcoded_venue_urls.sh` + `no_hardcoded_venue_universe.sh` | **GAP — NOT wired in features-service `quality-gates.sh`**                                        |
| P2 — Manifest emission           | `no_silent_absence_handlers.sh`                                 | **GAP — NOT wired**                                                                               |
| P3 — Schema-version              | `rg 'schema_version\s*=\s*[1-7]'` inline check                  | Passes clean (0 hits) — no step needed                                                            |
| P4 — Honest-absence reasons      | `rg 'record_empty.*reason\s*=\s*""'` check                      | **GAP — no QG for string-literal reasons**                                                        |
| P5 — expected_coverage preflight | Not implemented in features-service                             | **GAP**                                                                                           |
| P6 — Error classification        | `no_adapter_contract_regression.sh` (STEP 5.83)                 | **Partially wired** — but checks for `classify_and_emit_error` only, not `classify_venue_error()` |
| P7 — Bucket SSOT                 | `check_inline_bucket_uri.py` (STEP 5.69)                        | **NOT confirmed in features-service QG**                                                          |

Key gap: **STEP 5.70 trio (`no_silent_absence_handlers.sh` + `no_hardcoded_venue_urls.sh` +
`no_hardcoded_venue_universe.sh`) is wired into instruments-service and MTDS but NOT features-service.** This is why
F1-F4 reached prod.

---

## Phased execution DAG (remediation plan)

```
Phase 1 — Manifest emission wiring (F1-F3, F5)
   ├── onchain/cli/handlers/batch_handler.py: add ManifestWriter + record_* at each shard path
   ├── commodity/cli/handlers/batch_handler.py: add ManifestWriter + record_* per (commodity, date)
   ├── multi_timeframe/cli/handlers/batch_handler.py: add ManifestWriter + record_*
   └── cefi/cli/handlers/perp_funding_handler.py: uncomment record_empty call

Phase 2 — IS catalogue reads (F4)
   ├── volatility: replace hardcoded ["BTC", "ETH"] with IS-enumerated underlyings
   └── cefi: add IS consultation for perp funding rate universe (once IS cefi adapter exists)

Phase 3 — Error classification (F6, F7)
   ├── onchain: replace EnhancedError with classify_venue_error() + record_failed
   └── sports: replace classify_and_emit_error with classify_venue_error() where applicable

Phase 4 — Honest-absence reason strings (F8, F9)
   ├── sports + calendar: replace reason="SOURCE_RETURNED_ZERO" with EmptyConfirmedReason.SOURCE_RETURNED_ZERO
   └── cefi: fix UAC deep-path import

Phase 5 — Re-backfill (after Phase 1 ships)
   └── Re-run onchain/commodity/multi_timeframe batch for affected date ranges with manifest now emitting

Phase Q — QG enforcement
   ├── Wire STEP 5.70 trio into features-service quality-gates.sh
   ├── Wire STEP 5.69 (check_inline_bucket_uri.py) into features-service
   └── Add P4 string-literal-reason check
```

**Foundation-completion-gate**: Phase 1 (manifest emission) must be GREEN before Phase 5 (re-backfill) starts. Phase 2
(IS reads) is independent and can run in parallel with Phase 1.

---

## Continuous verification

| Pattern                          | Continuous-verification path                                    | Cadence         | Last verified      |
| -------------------------------- | --------------------------------------------------------------- | --------------- | ------------------ |
| P1 — IS-owned reference          | `no_hardcoded_venue_universe.sh` (once wired)                   | every push      | 2026-05-20 (audit) |
| P2 — Manifest emission           | `no_silent_absence_handlers.sh` (once wired)                    | every push      | 2026-05-20 (audit) |
| P3 — Schema-version              | 0 hardcodes confirmed clean                                     | —               | 2026-05-20 (audit) |
| P4 — Honest-absence reasons      | `LegacyBlankErrorReasonError` at runtime; QG check (once added) | every batch run | 2026-05-20 (audit) |
| P5 — expected_coverage preflight | Post-hoc DIVERGENT_EMPTY scanner (A3-style)                     | daily           | TBD                |
| P6 — Error classification        | `no_adapter_contract_regression.sh` (STEP 5.83)                 | every push      | 2026-05-20 (audit) |
| P7 — Bucket SSOT                 | `check_inline_bucket_uri.py` (once wired)                       | every push      | 2026-05-20 (audit) |

---

## Scope exclusions (verified clean)

**P3 (schema-version)**: No hardcoded `schema_version < 8` found in features-service source. All manifest writes go
through UTL `ManifestWriter` which defaults v8. Clean — no remediation needed.

**P7 (bucket SSOT) — partial clean**: `resolve_bucket_name` IS imported and used. The f-string URIs in
`volatility/core/data_loader.py` are path-construction patterns (bucket resolved by caller), not inline bucket-name
construction. Most carry `# noqa: gs-uri` comments already. The A1 ratchet baseline should absorb these; only genuinely
new inline bucket constructions need fixing.

**Sports bookmaker universe (F11)**: Confirmed NOT a hardcode. Sports family reads IS GCS output correctly via
`gcs_reader.py`. The A3 MISSING_EXPECTED issue is an IS adapter gap (IS needs to write bookmaker reference rows), not a
features-service hardcode violation.

---

## Temporary states + their canonical follow-up plans

- **commodity/multi_timeframe batch handlers without manifest** — temporary until Phase 1 ships. Downstream consumers
  reading features manifests should treat these families as `MISSING` (not `captured`). Named successor: this plan
  (Phase 1).
- **volatility hardcoded `["BTC", "ETH"]` universe** — temporary; TradFi/DeFi volatility features silently skip until
  Phase 2 ships. Named successor: this plan (Phase 2).
- **cefi record_empty commented out** — temporary stub; ships in Phase 1. Named successor: this plan.

---

## Deferred work after 2026-05-20 audit session

| Item                                           | Status                    | Next action                                    |
| ---------------------------------------------- | ------------------------- | ---------------------------------------------- |
| P0 F1: onchain manifest emission               | UNSTARTED                 | Phase 1 — next slot                            |
| P0 F2: commodity manifest emission             | UNSTARTED                 | Phase 1 — next slot                            |
| P0 F3: multi_timeframe manifest emission       | UNSTARTED                 | Phase 1 — next slot                            |
| P0 F4: volatility IS universe enumeration      | UNSTARTED                 | Phase 2 — next slot                            |
| P0 F5: cefi record_empty uncomment             | UNSTARTED                 | Phase 1 — next slot                            |
| P0 F6: onchain classify_venue_error            | UNSTARTED                 | Phase 3 — next slot                            |
| P0 F7: sports classify_venue_error             | UNSTARTED                 | Phase 3 — next slot                            |
| P1 F8: string literal reasons → enum           | UNSTARTED                 | Phase 4                                        |
| P1 F9: cefi UAC deep-path import fix           | UNSTARTED                 | Phase 4                                        |
| P2 F10: volatility data_loader noqa comments   | UNSTARTED                 | QG Phase                                       |
| P2 F13: Wire STEP 5.70 + 5.69 into features QG | UNSTARTED                 | Phase Q                                        |
| IS bookmaker metadata gap (A3 root cause)      | BLOCKED-OPERATOR-DECISION | IS adapter expansion needed — flag to operator |
