# AI-GENERATED — awaiting user review and promotion

---

slug: corporate-actions-migration-to-calendar type: code epic: epic-code-completion status: proposed created: 2026-03-24
repos:

- features-calendar-service
- instruments-service
- unified-internal-contracts completion_gates: code: C5 deployment: D2 business: B1 repo_gates:
- repo: features-calendar-service code: C0 deployment: D0 business: B0
- repo: instruments-service code: C0 deployment: D0 business: B0
- repo: unified-internal-contracts code: C0 deployment: D0 business: B0

---

# Corporate Actions Migration: instruments-service → features-calendar-service

## Motivation

Corporate actions (dividends, stock splits, earnings dates) are **calendar-structured events**. They have calendar
dates, affect forward pricing signals, and belong architecturally alongside other scheduled economic events (FOMC, NFP,
elections). `instruments-service` should focus on instrument definitions and metadata — not event calendars.

`features-calendar-service` already owns `time_features` and `economic_events` with a mature `process_day()` + GCS
write + `--dry-run` + batch/live/recon pattern. Corporate actions fit naturally as a new `FEATURE_CATEGORY`.

---

## Architectural Decision

### Trigger Pattern: Batch-Only

Corporate actions are **not real-time events** — they are scheduled on known future dates. The correct pattern:

- Daily Cloud Scheduler → CLI batch → process a rolling window of N days → GCS
- **No Pub/Sub subscription required** (unlike `live_handler.py` which subscribes to `features-delta-one-ready-sub`)
- Corporate actions run as a **standalone CLI operation** (e.g. `--operation corporate_actions --mode batch`)
- The backfill path mirrors existing `generate_date_views` / `corporate_actions_backfill` CLI handlers

This means we add a `CorporateActionsBatchHandler` following the `CalendarBatchModeHandler` pattern, registered
alongside `time_features` and `economic_events` — but **not** in `FEATURE_CATEGORIES` (which drives the shared
orchestrator loop). Instead, it is a separate `--operation` to keep fetch logic (yfinance with rate limiting, per-ticker
registry, backfill/update modes) cleanly separated from the 24-row-per-day temporal/economic pattern.

### "Results vs Expectations" (Validation) Methodology

`features-calendar-service` validates output in three ways — all of which apply to corporate actions:

1. **Runtime schema check**: `validate_timestamp_date_alignment(df, date=processing_date)` before every GCS write. This
   is the "gate before write" pattern already enforced in `calendar_orchestrator.py`.

2. **`--dry-run` mode**: All handlers write to `data/sample/<category>/day={date}/` instead of GCS. This gives you the
   actual output locally without touching production storage. Run with `--dry-run` to inspect results.

3. **T+1 reconciliation (`--run-tag t1-recon`)**: `docs/GCS_PATHS.md` documents a reconciliation namespace. The pattern
   is: primary run writes to `calendar/corporate_actions/by_date/day={date}/`, the T+1 recon run writes to a separate
   path. Comparing the two gives "what we computed yesterday" vs "what we'd compute today with fresh data" — catching
   late dividend announcements, revised earnings estimates, etc.

4. **Unit tests with fixture tickers**: tests assert output shape/schema from a small fixed set of known tickers (AAPL,
   MSFT, etc.) with hardcoded expected dividend dates/amounts. These are **not golden parquets** — they are schema +
   count assertions on mocked yfinance responses.

There is **no separate "results mode"** — you run the same batch handler with `--dry-run` or `--run-tag` to inspect
without side effects. The production run and test run use the same code path.

### Schema Placement (per schema governance rules)

- `DividendRecord`, `StockSplitRecord`, `EarningsRecord`, `CorporateActionsBundle`, `CorporateActionType` currently live
  in `instruments_service/corporate_actions/models.py`.
- Per `service-domain-schema-in-uic.mdc`: domain output schemas that cross repo boundaries belong in
  `unified-internal-contracts/unified_internal_contracts/domain/corporate-actions/`.
- The yfinance fetch adapter (`CorporateActionsAdapter`) is an **external API adapter** → the raw response models belong
  in UAC (`unified_api_contracts_external/yfinance/schemas.py`), but the business-level records (DividendRecord etc.)
  are internal domain types → UIC.

---

## Work Items

### Phase 1: Move domain models to unified-internal-contracts [C1]

- Create `unified_internal_contracts/domain/corporate_actions/__init__.py`
- Move `DividendRecord`, `StockSplitRecord`, `EarningsRecord`, `CorporateActionsBundle`, `CorporateActionType` from
  `instruments_service/corporate_actions/models.py`
- Export from `unified_internal_contracts/__init__.py`
- Update all instruments-service imports to use `from unified_internal_contracts import ...`
- Add `unified-internal-contracts` to `features-calendar-service` pyproject.toml if not already present
- Run `uv lock` in both repos after pyproject.toml changes
- Tests: `test_corporate_actions_models.py` in UIC with basic validation assertions

### Phase 2: Move yfinance adapter to features-calendar-service [C1]

- Create `features_calendar_service/adapters/yfinance_corporate_actions_adapter.py`
  - Copy `CorporateActionsAdapter` logic from `instruments_service/corporate_actions/adapter.py`
  - Use `from unified_internal_contracts import DividendRecord, StockSplitRecord, EarningsRecord`
  - Follow cloud-agnostic import patterns (no direct `os.getenv` for API keys)
- Remove `instruments_service/corporate_actions/adapter.py` (delete — no backward compat shim)

### Phase 3: Create calculator in features-calendar-service [C1]

- Create `features_calendar_service/app/calculators/corporate_actions_calculator.py`
  - Wraps adapter; produces per-ticker DataFrames
  - `validate_timestamp_date_alignment` before returning
  - Returns `dividends_df`, `splits_df`, `earnings_df` — one parquet per sub-type per day

### Phase 4: CLI handler — batch + backfill + incremental [C1]

- Create `features_calendar_service/cli/handlers/corporate_actions_handler.py`
  - `CorporateActionsBatchModeHandler(BaseModeHandler)` — date range loop
  - Backfill subcommand: full ticker history (mirrors `corporate_actions_backfill_handler.py`)
  - Incremental update: ticker registry YAML tracking last-fetch per ticker
  - `--dry-run` writes to `data/sample/corporate_actions/`
  - `--run-tag` for T+1 reconciliation namespace
- Wire into `features_calendar_service/cli/parser.py` as `--operation corporate_actions`

### Phase 5: GCS paths [C1]

Output path structure:

```
calendar/corporate_actions/by_date/day={YYYY-MM-DD}/dividends.parquet
calendar/corporate_actions/by_date/day={YYYY-MM-DD}/splits.parquet
calendar/corporate_actions/by_date/day={YYYY-MM-DD}/earnings.parquet
```

Ticker registry:

```
calendar/corporate_actions/metadata/ticker_registry.yaml
calendar/corporate_actions/metadata/coverage_report.json
```

Update `features-calendar-service/docs/GCS_PATHS.md` and `unified-trading-pm/configs/data-catalogue.*.yaml` for any
service that consumes corporate actions data.

### Phase 6: Tests [C2]

- **Unit** (`tests/unit/test_corporate_actions_handler.py`): mock yfinance → assert parquet columns, row counts,
  empty-frame schema consistency
- **Unit** (`tests/unit/test_corporate_actions_calculator.py`): fixture DividendRecord objects → DataFrame shape
- **Integration** (`tests/integration/test_corporate_actions_integration.py`): live yfinance for 3 known tickers (AAPL,
  MSFT, JPM), last 90 days, assert non-empty dividends returned
- **Backfill** coverage: mock full history run, verify ticker_registry.yaml written correctly
- Check `MIN_COVERAGE` in `scripts/quality-gates.sh` after new tests are added

### Phase 7: Remove from instruments-service [C1 in instruments-service]

Delete these files (no backward compat shims):

- `instruments_service/corporate_actions/` (entire module — models.py, adapter.py, `__init__.py`)
- `instruments_service/cli/handlers/corporate_actions_handler.py`
- `instruments_service/cli/handlers/corporate_actions_backfill_handler.py`
- `instruments_service/cli/handlers/corporate_actions_update_handler.py`
- `instruments_service/cli/handlers/corporate_actions_production_handler.py`
- `instruments_service/cli/handlers/generate_date_views_handler.py`
- Remove corporate actions operations from `instruments_service/cli/parser.py` and `instruments_service/cli/main.py`
- Delete tests: `tests/unit/test_corporate_actions_handler.py`, `tests/unit/test_generate_date_views_handler.py`
  (equivalent tests now live in features-calendar-service)

Keep `instruments_service/config/instrument_definitions.py` `corporate_actions_start_date` if it's still needed for
backfill config; otherwise remove.

### Phase 8: Downstream consumers audit [C1]

Run `rg "corporate_actions_output\|by_ticker.*dividends\|by_ticker.*splits" --type yaml` across unified-trading-pm
configs to find any Cloud Scheduler jobs, DAGs, or data-catalogue entries pointing at the old GCS paths. Update to new
`calendar/corporate_actions/` paths.

---

## What Is NOT Changing

- instruments-service still owns `InstrumentDefinition`, `InstrumentAvailability`, `defi_processor`, venue adapters —
  all instrument identity/metadata logic stays
- `CorporateActionsAdapter`'s yfinance integration for **earnings dates** overlaps with the economic calendar concept
  already in `features-calendar-service`; `EarningsRecord` should eventually be merged with the `economic_events`
  pipeline, but that is a follow-on task (do not block this migration on it)

---

## Dependency Note

- `features-calendar-service` does NOT currently depend on `unified-internal-contracts` at the Python level (check
  pyproject.toml before Phase 1 starts). If UIC is not already a dep, add it and run `uv lock` + update
  `workspace-manifest.json` dependencies array.

---

## Quickmerge Order

1. `unified-internal-contracts` — new models (no breaking changes, MINOR bump via `feat:`)
2. `features-calendar-service` — new adapter + calculator + handler (after UIC ships)
3. `instruments-service` — delete corporate actions module (after features-calendar-service ships)
