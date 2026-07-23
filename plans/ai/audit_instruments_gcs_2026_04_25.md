# Instruments Audit — GCS Buckets → API → UI List

**Date:** 2026-04-25 **Scope:** How instrument data flows from GCS to the instruments list page in the UI. What exists,
what is wired, and what needs to change.

---

## 1. The 5 buckets (SSOT: `/codex/02-data/per-category-bucket-layouts.md`)

| Category   | GCS bucket (prod)                           | Path layout                                                                       |
| ---------- | ------------------------------------------- | --------------------------------------------------------------------------------- |
| CeFi       | `instruments-store-cefi-{project_id}`       | `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet`    |
| TradFi     | `instruments-store-tradfi-{project_id}`     | `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet`    |
| DeFi       | `instruments-store-defi-{project_id}`       | `instrument_availability/by_date/day={date}/venue={venue}/instruments.parquet`    |
| Sports     | `instruments-store-sports-{project_id}`     | `sports_reference/by_date/day={date}/entity={entity}/{entity}.parquet`            |
| Prediction | `instruments-store-prediction-{project_id}` | `instrument_availability/by_date/day={date}/instruments.parquet` (no venue level) |

**Critical quirk:** Sports uses a completely different path tree (`sports_reference/`, not `instrument_availability/`)
and a different partition key (`entity=` not `venue=`). Any code that iterates instruments uniformly across categories
**must** dispatch on category at the path level. This caused a prod incident (documented in the SSOT doc above).

Test-mode buckets append `-test-`: `instruments-store-cefi-test-{project_id}`.

---

## 2. Backend data flow

```
External sources (exchanges, sports APIs, DeFi chains, etc.)
  ↓
instruments-service (daily batch per category)
  ↓ writes Parquet
GCS buckets (5 categories)
  ↓ reads via get_data_sink / ManifestWriter (UTL)
instruments-service schema: CanonicalInstrument (UAC)
  ↓ served by
unified-trading-api (FastAPI, unified_trading_api/routes/instruments.py)
  ↓ 3 endpoints
  GET /instruments/list     — filters: venue, asset_group; pagination
  GET /instruments/catalogue — full metadata per instrument
  GET /instruments/registry  — filters: venue, category, instrument_type, status; pagination
  ↓
UI
```

---

## 3. CanonicalInstrument schema (UAC, `canonical/domain/reference/__init__.py`)

Key fields for the UI list:

| Field                                           | Type                    | Notes                                                                                         |
| ----------------------------------------------- | ----------------------- | --------------------------------------------------------------------------------------------- |
| `instrument_key`                                | `str` (required)        | Format: `VENUE:INSTRUMENT_TYPE:SYMBOL`                                                        |
| `venue`                                         | `str` (required)        | e.g. `BINANCE-SPOT`, `AAVE_V3-ETHEREUM`                                                       |
| `instrument_type`                               | `InstrumentType` enum   | `SPOT_PAIR`, `PERPETUAL`, `FUTURE`, `OPTION`, `POOL`, `LENDING`, `LST`, `ETF`, `EQUITY`, etc. |
| `symbol`                                        | `str` (required)        | e.g. `BTC-USDT`                                                                               |
| `asset_class`                                   | `AssetClass` enum       | `crypto`, `equity`, `fx`, `commodity`, `fixed_income`                                         |
| `base_asset`                                    | `str \| None`           |                                                                                               |
| `quote_asset`                                   | `str \| None`           |                                                                                               |
| `available_from_datetime`                       | `AwareDatetime \| None` |                                                                                               |
| `available_to_datetime`                         | `AwareDatetime \| None` | null = still active                                                                           |
| `tick_size`                                     | `Decimal \| None`       |                                                                                               |
| `min_size`                                      | `Decimal \| None`       |                                                                                               |
| `contract_size`                                 | `Decimal \| None`       |                                                                                               |
| `strike`, `option_type`, `expiry`, `underlying` |                         | Options-specific                                                                              |
| `pool_address`, `pool_fee_tier`                 |                         | DeFi-specific                                                                                 |
| `ltv`, `liquidation_threshold`                  |                         | DeFi lending-specific                                                                         |
| `trading_hours_open/close`                      | `str \| None`           | TradFi-specific                                                                               |

`InstrumentType` enum values (canonical, UPPERCASE): `SPOT_PAIR`, `PERPETUAL`, `FUTURE`, `OPTION`, `POOL`, `LENDING`,
`LST`, `YIELD_BEARING`, `A_TOKEN`, `DEBT_TOKEN`, `STAKING`, `SPOT_ASSET`, `ETF`, `EQUITY`, `COMMODITY`, `CURRENCY`,
`INDEX`, `BOND`, `CDS`, `COMBO`, `PREDICTION_MARKET`, `EXCHANGE_ODDS`, `FIXED_ODDS`, `PROP`

---

## 4. UI current state

### 4a. What exists

| File                                                              | Role                                                                                 | Using real data?                                   |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------- |
| `lib/registry/instruments.ts` + `instruments-snapshot.json`       | Static JSON snapshot of 31,961 instruments from real GCS (2026-03-27)                | YES — from GCS, but 29 days old                    |
| `hooks/api/use-instruments.ts` (`useInstruments`, `useCatalogue`) | React Query hooks that call `/api/instruments/list` and `/api/instruments/catalogue` | NOT USED on instruments page                       |
| `app/(platform)/services/data/instruments/page.tsx`               | The instruments finder/browser page                                                  | Uses `MOCK_INSTRUMENTS` only                       |
| `components/data/instruments-finder-config.tsx`                   | Finder column config                                                                 | Uses `MOCK_INSTRUMENTS` + `MOCK_INSTRUMENT_COUNTS` |
| `lib/types/data-service.ts` (`InstrumentEntry`)                   | UI-local instrument type for the finder                                              | NOT aligned with `CanonicalInstrument`             |
| `lib/mocks/fixtures/data-service.ts` (`MOCK_INSTRUMENTS`)         | Hand-crafted mock instruments                                                        | Real venue/symbol names, wrong schema shape        |

### 4b. Snapshot counts (2026-03-27)

| Category   | Count      |
| ---------- | ---------- |
| cefi       | 4,542      |
| tradfi     | 15,563     |
| defi       | 4,864      |
| sports     | **0**      |
| prediction | 6,992      |
| **Total**  | **31,961** |

Sports = 0 because the snapshot generator uses the standard `instrument_availability/` path which doesn't exist for
sports (sports data lives in `sports_reference/`). The snapshot generator would need a sports-specific read path.

---

## 5. Gaps

### G1 — Finder page is mock-only, hooks unused

**What:** The instruments finder page (`/services/data/instruments`) uses `MOCK_INSTRUMENTS` from `data-service.ts`. The
live hooks (`useInstruments`, `useCatalogue`) and the real snapshot (`ALL_INSTRUMENTS`) are imported in other places but
NOT wired to the finder. **Impact:** The instruments list shows a small fabricated subset, not the real ~32K
instruments. **Fix path:** Wire `ALL_INSTRUMENTS` from the snapshot into the finder, or call `/instruments/registry`
with server-side pagination (preferred for scale).

### G2 — Two instrument schemas with incompatible shapes

**What:**

- UI `InstrumentEntry` (data-service.ts): `instrumentKey`, `folder` (not `instrument_type`),
  `baseCurrency`/`quoteCurrency` (not `base_asset`/`quote_asset`), `dataTypes` (data-service concept, no backend
  equivalent per-instrument), `category` uses UI enum (`cefi`, `onchain_perps`, `prediction_market`)
- Backend `CanonicalInstrument`: `instrument_key`, `instrument_type`, `base_asset`, `quote_asset`, no `folder`, no
  `dataTypes`, category handled via `asset_class` enum or API filter param

**Impact:** Dropping `MOCK_INSTRUMENTS` and using real data requires either: (a) adapting `InstrumentEntry` to match
`CanonicalInstrument`, or (b) writing a transform function `CanonicalInstrument → InstrumentEntry`

Option (b) is safer short-term (no sweeping type changes); option (a) is cleaner long-term.

### G3 — `DataCategory` ↔ backend `category` param mismatch

**What:** UI has 6 categories: `cefi`, `tradfi`, `defi`, `onchain_perps`, `prediction_market`, `sports`. Backend
`/instruments/registry` accepts `category` param with: `cefi`, `tradfi`, `defi`, `sports`, `prediction` (5 values).

Mismatches:

- `prediction_market` (UI) → `prediction` (backend)
- `onchain_perps` (UI) → no backend equivalent; it's a subset of `cefi` (Hyperliquid) or `defi`

**Fix:** A small mapping table `UI_CATEGORY_TO_BACKEND`:

```ts
const UI_CATEGORY_TO_BACKEND: Record<DataCategory, string | null> = {
  cefi: "cefi",
  tradfi: "tradfi",
  defi: "defi",
  onchain_perps: null, // filter cefi venues: [HYPERLIQUID] client-side
  prediction_market: "prediction",
  sports: "sports",
};
```

### G4 — `instrument_key` format divergence

**What:** UI mocks use `"{venue}:{folder}:{symbol}"` (lowercase, folder-based), e.g. `"binance:perpetuals:BTCUSDT"`.
Backend uses `"VENUE:INSTRUMENT_TYPE:SYMBOL"` (uppercase, type-based), e.g. `"BINANCE-FUTURES:PERPETUAL:BTC-USDT"`.
**Impact:** Any code that parses or constructs `instrumentKey` from mock data will produce keys that don't match backend
keys. This will break cross-referencing between instruments and positions/orders once the system goes live.

### G5 — Sports instruments = 0 in snapshot; finder shows mock sports

**What:** Sports data in GCS lives under `sports_reference/` (fixtures, teams, odds) — not in the standard
`instrument_availability/` Parquet format that represents tradeable instruments. The snapshot generator doesn't handle
this path variant. **Impact:** Clicking "Sports" in the finder shows only mock data (`api_football`, `footystats` venues
with fabricated instruments). **Fix options:** (a) Add sports-specific read to snapshot generator (reads
`sports_reference/by_date/.../fixtures.parquet`, maps to fixture-as-instrument representation) (b) Accept that sports
isn't a standard instrument list — show league/fixture browser instead (different UX model)

Option (b) is probably correct given sports reference data structure. Sports fixtures are not "instruments" in the
CeFi/TradFi sense.

### G6 — Snapshot staleness (29 days)

**What:** `instruments-snapshot.json` was generated 2026-03-27. No CI/CD job regenerates it. **Impact:** New instruments
added in the last month (especially DeFi pools, prediction markets) are absent from the UI's reference data. **Fix:**
Add a scheduled job (PM automation or CI) that runs `generate_instrument_snapshot.py` weekly and commits the updated
file. The script already exists at `unified-trading-pm/scripts/openapi/generate_instrument_snapshot.py`.

### G7 — No server-side pagination wired

**What:** `/instruments/registry` and `/instruments/list` support `page` + `page_size`. `useInstruments()` calls
`/instruments/list` but passes no page param. `useCatalogue()` has no pagination at all. **Impact:** At 32K+
instruments, loading them all at once is not viable. The finder needs virtualization + server-side page loading.
**Fix:** The finder already has a `paginate: true` flag on the instrument column. Wire it to call
`/instruments/registry?page=N&page_size=50` as the user scrolls/pages.

---

## 6. Decisions

| #   | Decision                                                                        | Rationale                                                                                     |
| --- | ------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- |
| D1  | Use `/instruments/registry` (not `/list`) as primary source                     | Registry has richer filter params (`instrument_type`, `status`) and better pagination support |
| D2  | Transform `CanonicalInstrument → InstrumentEntry` at the hook layer             | Avoids sweeping type changes across all consumers of `InstrumentEntry`                        |
| D3  | `onchain_perps` category stays UI-only, filtered client-side from CeFi          | No backend equivalent; Hyperliquid lives under cefi                                           |
| D4  | Sports: replace instrument list with fixture/league browser                     | Sports reference data is not in instrument-availability format; wrong UX model                |
| D5  | Snapshot serves as static fallback + initial render; live API for search/filter | Best of both: fast initial load, live filtering                                               |

---

## 7. Implementation sequence (for future work)

**Step 1 — Create adapter function** (no breaking changes) `lib/api/adapters/instrument-adapter.ts`:
`CanonicalInstrument → InstrumentEntry` transform. Unit-testable.

**Step 2 — Wire `useInstruments`/`useInstrumentRegistry` to finder** Replace `MOCK_INSTRUMENTS` in
`instruments-finder-config.tsx` with real data from `useInstrumentRegistry` hook. Keep mock as fallback when
`NEXT_PUBLIC_MOCK_API=true`.

**Step 3 — Category mapping table** Add `UI_CATEGORY_TO_BACKEND` mapping, pass correct `category` param to registry
endpoint.

**Step 4 — Pagination** Wire finder's `paginate: true` to API page calls. The finder already supports it structurally.

**Step 5 — Snapshot refresh CI job** Scheduled weekly via PM automation. Output committed to
`lib/registry/instruments-snapshot.json`.

**Step 6 — Sports UX (separate)** Replace sports instrument list with fixture/league browser reading `sports_reference/`
data via a dedicated API route.

---

## 8. What is NOT a gap

- `VENUES_BY_CATEGORY` in data-service.ts uses lowercase venue names (`binance`, not `BINANCE-SPOT`). This is fine for
  the finder UI display layer — it's presentation, not an identifier.
- Mock `MOCK_INSTRUMENT_COUNTS` are fabricated. Fine for now — these will be replaced by aggregated counts from
  `/instruments/registry` grouped by category.
- `CanonicalInstrument` has DeFi/TradFi-specific fields (`pool_address`, `trading_hours_open`, etc.) with `None`
  defaults — the adapter just passes `undefined` for these, no problem.

---

## Cross-references

- Bucket layout SSOT: `/codex/02-data/per-category-bucket-layouts.md`
- `CanonicalInstrument`: `unified-api-contracts/unified_api_contracts/canonical/domain/reference/__init__.py:59`
- `InstrumentType` enum: `unified-api-contracts/unified_api_contracts/_instrument_enums.py:17`
- Backend instrument routes: `unified-trading-api/unified_trading_api/routes/instruments.py`
- Snapshot generator: `unified-trading-pm/scripts/openapi/generate_instrument_snapshot.py`
- UI snapshot: `unified-trading-system-ui/lib/registry/instruments-snapshot.json`
- UI finder config: `unified-trading-system-ui/components/data/instruments-finder-config.tsx`
- UI instruments page: `unified-trading-system-ui/app/(platform)/services/data/instruments/page.tsx`
- UI hooks: `unified-trading-system-ui/hooks/api/use-instruments.ts`
- Mock fixtures: `unified-trading-system-ui/lib/mocks/fixtures/data-service.ts`
