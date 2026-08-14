---
doc_type: codex-ssot
title: Contracts Scope and Layout — SSOT
summary:
  SSOT for UAC scope + layout — the external/canonical surface is a T0 leaf that must not import internal
  (internal→canonical is the only permitted direction), the Citadel facade package structure, canonical-vs-internal type
  ownership, deleted-directory bans, the universal v9 source column, and canonical data_type naming.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos:
  [deployment-api, execution-service, features-service, instruments-service, market-tick-data-service, strategy-service]
scope: [engineer, admin]
tags: [uac, canonicalisation, refactor, data-pipeline, ssot-audit, tradfi]
related:
  [
    /codex/02-data/canonical-schema-groups.md,
    /codex/02-data/vcr-cassette-ownership.md,
    /codex/04-architecture/tier-and-import-architecture.md,
  ]
created: 2026-03-27
authoritative_for: [UAC external/canonical/internal scope + import-direction rules]
referenced_by:
  [
    /codex/02-data/README.md,
    /codex/02-data/canonical-schema-groups.md,
    /codex/02-data/data-lineage-MTDS-features-ml.md,
    /codex/02-data/per-source-colocation.md,
    /codex/02-data/pipeline-mode-and-batch-live-reconciliation.md,
    /codex/02-data/prediction-data-types-catalog.md,
    /codex/02-data/schema-governance.md,
    /codex/02-data/vcr-cassette-ownership.md,
  ]
owner:
last_reviewed: 2026-06-25
code_refs:
---

# Contracts Scope and Layout — SSOT

**SSOT for:** AC vs UIC scope, dependency rule (AC cannot import UIC), and package layout. For full detail:
unified-api-contracts/docs/PACKAGE_LAYOUT_AND_SCOPE.md. VCR:
[02-data/vcr-cassette-ownership.md](vcr-cassette-ownership.md).

**Repo:** [unified-api-contracts](https://github.com/central-element/unified-api-contracts) — raw external schemas
(`unified_api_contracts/external/`) and normalised canonicals (`unified_api_contracts/canonical/`). An auto-generated
**schema audit matrix** (`docs/SCHEMA_AUDIT_MATRIX.md`) lists Provider × Schema Type with ✓/~/— and canonical target.
Regenerate via `python scripts/generate_schema_audit_matrix.py`. Use for auditing usage, orphaned schemas, import
errors, and missing functionality in downstream consumers.

---

## Dependency rule (blocking)

**The `unified_api_contracts.external` and `unified_api_contracts.canonical` sub-packages must not import from
`unified_api_contracts.internal`.** The external/canonical surface is a Tier 0 leaf with no internal-contracts
dependency. Internal contracts (the `internal/` subpackage) can depend on the canonical surface; the canonical surface
cannot depend on the internal subpackage.

Therefore **all schemas needed for mapping must remain in `unified_api_contracts.canonical` or
`unified_api_contracts.external`**, including:

- Canonical instrument IDs and venue identifiers used in normalization
- Venue enums / manifest used by `normalize.py` and external→canonical mapping
- Any type that `unified_api_contracts.canonical` or venue adapters need to produce canonical output

---

## Scope rule

- **unified-api-contracts (external/canonical surface)** = **external API contracts** + **mapping surface**. Schemas for
  third-party APIs (exchanges, data providers, cloud SDKs) and anything required to map them to canonical types.
- **unified_api_contracts.internal** = **internal contracts only**. Schemas used to contract our codebase to our
  codebase (no external API surface). If a schema is **not** used for any external API contract and **not** needed for
  mapping, it does **not** belong in the external/canonical surface — it belongs in `unified_api_contracts.internal`.

---

## Normalization ideology

- **UAC = normalization layer** — like an internal CCXT/TARDIS. unified-api-contracts maps raw venue responses to
  canonical types.
- **Interfaces** (UMI, UTEI, USEI, UDEFI) are **venue routers** — they choose venue but return normalized data only.
- **Raw venue responses must never flow to services** — always normalize via UAC before returning.
- **Scope:** all response types — trades, orderbooks, tickers, positions, balances, liquidations, funding, OHLCV, market
  info, errors, WebSocket, sports, alt data.
- **Domain split:** canonical with optional fields; sub-types only when structures are incompatible; group by
  instruction type (TRADE, SWAP, LEND, BORROW, etc.).

---

## Layout rule

Top-level packages under `unified_api_contracts/` are grouped into three buckets:

| Bucket                              | Purpose                                                                                                |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **shared**                          | Cross-venue shared types, errors, quotas                                                               |
| **unified_api_contracts/external**  | Raw per-venue request/response/errors; venue_manifest, sports, nautilus, prime_broker, fix, regulatory |
| **unified_api_contracts.canonical** | Canonical domain/execution/errors + normalize                                                          |

Internal-only schemas (e.g. risk, VaR, stress testing) belong in `unified_api_contracts.internal`.

---

## Import direction rules

- **unified-api-contracts (external/canonical surface)**: stdlib + pydantic only; **no `unified-*` imports at all** —
  not even in tests. `test_ac_uic_alignment.py` (which imports from `unified_api_contracts.internal` inside the UAC
  external test suite) is a **known CIRCULAR violation** and must be moved to `unified_api_contracts/internal/tests/`.
  **Successor plan (per CLAUDE.md "Temporary state must have a named successor plan" rule + codex audit D-11
  2026-05-12)**: was tracked as a sub-task under `uac_citadel_architecture_2026_05_07.md` (UAC import-surface
  enforcement workstream) — that plan file no longer exists; `plans/archive/INDEX.md`'s citadel section records the
  topic as "superseded by completed execution plan," with no successor filename findable on disk (2026-08-05
  docs-reconcile). Whether the described move (`test_ac_uic_alignment.py` → `unified_api_contracts/internal/tests/`) has
  actually landed in the `unified-api-contracts` repo is unverified by this note — until confirmed, the file is
  permitted under the existing `internal → canonical` cross-surface exception; no new circular-violating test files may
  be added (QG step `check_uac_internal_imports.py` enforces).
- **unified_api_contracts.internal**: stdlib + pydantic + **permitted to import from `unified_api_contracts.canonical`**
  (normalization canonicals re-used in messaging). No cloud SDKs. `internal` → `canonical` is the **only** permitted
  cross-surface import direction within UAC.
- **Tier formalization:** UAC canonical/external surface = true T0 leaf (no workspace imports).
  `unified_api_contracts.internal` = T0-with-canonical-dependency. Build order must place canonical (L2a) before
  internal (L2b) in CI/CD.

## Canonical type ownership (normalization vs messaging)

- **Canonical types output by normalizers** (e.g. CanonicalOrderBook, CanonicalTrade, CanonicalTicker) → defined in UAC
  `unified_api_contracts/canonical/`, re-exported by UIC `market_data/__init__.py` for messaging use.
- **Canonical types used only in internal messaging** (e.g. CanonicalOHLCV, CanonicalBookUpdate, CeFiPosition) → defined
  in `unified_api_contracts.internal`.
- **Duplicate or conflict**: If the same concept has different definitions in both surfaces, resolve by determining
  which side is the normalizer output (canonical) vs messaging contract (internal). Known conflicts: InstrumentRecord
  (CONFLICT — canonical 76-field warehouse schema vs internal 31-field adapter contract), CanonicalOraclePrice,
  CanonicalStakingRate, CanonicalOptionsChainEntry (DUPLICATE — must resolve ownership).

## Domain schema placement

- **Service domain data schemas** (Pydantic BaseModel, TypedDict, @dataclass used as cross-repo contracts) belong in
  `unified_api_contracts.internal` under `internal/domain/<service-name>/`.
- Services access their domain schemas via `unified-trading-library` or `unified-domain-client`, not by defining them
  locally.
- **SchemaDefinition / ColumnSchema** (parquet infrastructure from unified-trading-library) stay in the service's
  `schemas/output_schemas.py` — these are enforcement descriptors, not data contracts.
- Audit: see `plans/archive/SCHEMA_CONTRACTS_AUDIT.md` Section 3b for all known violations.

## Quality gates and schema organization checks

Quality gates enforce schema placement:

- **UAC external/canonical** (`scripts/check_schema_organization.py`): Schemas in
  `unified_api_contracts/canonical/domain/` or `unified_api_contracts/canonical/crosscutting/` must be used in at least
  one of: `unified_api_contracts/normalize_utils/`, `unified_api_contracts/external/`, or `tests/`. If not used, the
  schema is internal-only and should live in `unified_api_contracts.internal`.
- **UAC internal** (`scripts/check_schema_organization.py`): Domain schemas under `internal/domain/<service-name>/`;
  imports from `unified_api_contracts.canonical` only.
- **Other repos** (`unified-trading-pm/scripts/validation/check_schema_provenance.py`): Local
  BaseModel/TypedDict/dataclass definitions should import from `unified_api_contracts` (canonical surface) or
  `unified_api_contracts.internal`. Cross-repo contracts must come from one of those two.

### Exception: schemas required in UAC canonical surface for normalization/testing

If a schema that looks internal (`internal/`-style) is **actually used** in the canonical surface for normalization or
testing, it must remain in the canonical/external surface to avoid circular imports (canonical surface cannot import
`internal`). Add `# SCHEMA_UAC_REQUIRED` in the first 20 lines of the file to exempt it from the UAC organization check.

### Exception: internal-only schemas in services

If a service defines a schema that is purely internal (not a cross-repo contract), add `# SCHEMA_PROVENANCE_EXEMPT` in
the first 20 lines to exempt from the provenance check.

---

## Internal schema reference locations

| Schema                   | SSOT                                                             | Consumers                                     |
| ------------------------ | ---------------------------------------------------------------- | --------------------------------------------- |
| **InstrumentDefinition** | `unified_api_contracts.internal.reference.instrument_definition` | instruments-service, market-tick-data-service |

Import: `from unified_api_contracts.internal import InstrumentDefinition`

---

## UAC Citadel Architecture (v2 layout)

UAC follows a **facade pattern** with strict import surface rules. The top-level package `unified_api_contracts/`
exposes thin facade modules that re-export from internal sub-packages.

### Package structure

| Package                             | Purpose                                                                                                                                                          |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `canonical/`                        | Canonical normalized types, grouped by domain                                                                                                                    |
| `canonical/domain/`                 | Domain-specific canonicals (market_data, execution, defi, sports, etc.)                                                                                          |
| `canonical/domain/derivatives/`     | TradFi derivatives SSOTs: `tradfi_etfs.py` (ETF catalogue) + `tradfi_roots.py` (futures-root catalogue)                                                          |
| `canonical/crosscutting/`           | Cross-domain canonicals (errors, pagination, metadata)                                                                                                           |
| `canonical/asset_group_registry.py` | **Cross-asset-group entry-point** — `get_canonical_inventory(asset_group)` → `AssetGroupInventory` (venues + data_types + source_coverage_start). Phase 5C SSOT. |
| `registry/`                         | Capability registry + venue manifest                                                                                                                             |
| `registry/capability/`              | Per-source capability declarations (modes, envs, operations)                                                                                                     |
| `registry/venue_manifest/`          | Venue metadata, connection params, rate limits                                                                                                                   |
| `external/`                         | Raw per-source external schemas, flat layout (one module per source)                                                                                             |
| `normalize_utils/`                  | Internal normalization helpers (not part of public import surface)                                                                                               |

### Import surface rules

1. **Services and libraries** import from the top-level facade only:
   `from unified_api_contracts import CanonicalTrade, CanonicalOrderBook`
2. **Internal sub-packages** (`canonical/`, `registry/`, `external/`) are implementation detail. Direct imports from
   sub-packages are permitted but not required.
3. **`normalize_utils/`** is internal-only. Never import from outside UAC.
4. **`external/`** modules are flat (one file per source). No nesting beyond one level.

### Cross-asset-group canonical inventory (Phase 5C SSOT)

`canonical/asset_group_registry.py` is the single entry-point that answers "give me everything for asset_group X":

```python
from unified_api_contracts.canonical.asset_group_registry import get_canonical_inventory

inv = get_canonical_inventory("cefi")
inv.venues                  # tuple[str, ...] — canonical venue IDs
inv.data_types              # tuple[str, ...] — canonical data_type strings
inv.source_coverage_start   # dict[str, date] — venue/source → earliest available date
```

**`KNOWN_ASSET_GROUPS`** (frozenset): `cefi` / `defi` / `tradfi` / `sports` / `prediction`.

**`AssetGroupInventory`** fields:

| Field                   | Type              | Source SSOT                                                              |
| ----------------------- | ----------------- | ------------------------------------------------------------------------ |
| `asset_group`           | `str`             | key passed in (lowercased)                                               |
| `venues`                | `tuple[str, ...]` | `registry.market_data_categories.VENUES_BY_ASSET_GROUP`                  |
| `data_types`            | `tuple[str, ...]` | `registry.market_data_categories.DATA_TYPES_BY_ASSET_GROUP`              |
| `source_coverage_start` | `dict[str, date]` | per-asset-group `*_SOURCE_COVERAGE_START` in `canonical.coverage_starts` |

Resolves § A1 problem from 2026-05-08 catalogue audit (data spread across 3 separate dicts). Migration of consumers to
this surface: Phase 6 of `cross_asset_group_catalogue_audit_2026_05_10.md`.

### Capability registry

Each source declares its capabilities in `registry/capability/` via `SourceCapability` (Pydantic model in
`registry/capability.py`):

- Supported modes (batch, live, replay)
- Supported environments (prod, sandbox, testnet)
- Supported operations (trades, orderbook, ohlcv, etc.)
- API key scope requirements (prod vs test keys)

**Phase 1 metadata fields (2026-05-20)** — 4 structured fields added to `SourceCapability`:

| Field                  | Type                      | Canonical values                                                                                                                                                                                                                      | Purpose                                      |
| ---------------------- | ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------- |
| `chain`                | `str \| None`             | `"ethereum"`, `"starknet"`, `"solana"`, `"hyperevm"`, `"polygon"`, `"dydx-chain"`, `None` for pure CEX/data                                                                                                                           | Underlying settlement layer                  |
| `kind`                 | `Literal[...] \| None`    | `"perp_dex"`, `"spot_dex"`, `"perp_cex"`, `"spot_cex"`, `"options_cex"`, `"options_dex"`, `"prediction_dex"`, `"sports_book"`, `"lending_protocol"`, `"staking_protocol"`, `"amm_dex"`, `"vault_protocol"`, `None` for data providers | Venue class taxonomy                         |
| `mandatory_user_agent` | `str \| None`             | `"odum-group-unified-trading/extended-mtds"` for Extended Starknet; `None` otherwise                                                                                                                                                  | REST/WS clients MUST send this header if set |
| `coverage_start`       | `dict[str, date] \| None` | keys = workspace-canonical data_type names (e.g. `"candles"`, `"funding_rates"`, `"rates"`); values = ISO dates                                                                                                                       | Earliest available data per data_type        |

All 4 default to `None` (backwards-compatible). QG STEP 5.85 enforces explicit `chain=` and `kind=` kwargs on every
`SourceCapability(...)` instantiation in `capability_declarations/_*.py` (even `None` is acceptable — the rule enforces
explicit declaration, not non-null values).

Consumers: `is_before_source_coverage_start(venue, data_type, check_date)` in `registry/expected_coverage.py` reads
`coverage_start[data_type]` to emit `EXPECTED_PRE_SOURCE_COVERAGE_START` reason in `record_empty()` calls.

Fail-fast error classes in UTL (`unified_trading_library.core.capability_errors`) are raised BEFORE any network call
when an adapter is called with an unsupported mode, environment, or auth scope. Error classes: `UnsupportedModeError`,
`UnsupportedEnvironmentError`, `ApiKeyScopeMismatchError`, `CapabilityResolutionError`, `UnsupportedOperationError`.

### Deleted directories — do NOT reference

The following sub-packages have been removed from UAC and must not be imported, recreated, or referenced in any new
code, plan, or test:

| Deleted path           | Notes                                                                                                                                       |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `canonical/normalize/` | Normalization helpers moved; consumers use `normalize_utils/`                                                                               |
| `external/sports/`     | Sports schemas migrated to canonical domain layout                                                                                          |
| `external/cloud_sdks/` | Cloud SDK contracts removed (belong in `unified_cloud_interface`, not UAC)                                                                  |
| `external/onchain/`    | On-chain schemas migrated to `canonical/domain/defi/` and `canonical/crosscutting/defi.py`                                                  |
| `external/macro/`      | Macro schemas removed                                                                                                                       |
| `schemas/`             | Formerly a top-level schemas directory; migrated into the canonical/external split                                                          |
| `shared/`              | Formerly a top-level shared directory; content redistributed to canonical/internal                                                          |
| `external/kaiko/`      | Kaiko removed as a data provider                                                                                                            |
| `external/polygon/`    | Polygon.io removed as a TradFi data provider (Polygon L2 blockchain in `canonical/crosscutting/defi.py` is intact — do not confuse the two) |

Agents that encounter an import path starting with any of these segments must treat it as a stale reference and file a
triage issue rather than referencing the deleted module.

### Global ledger SSOT

**Shipped:** Phase 2 (2026-05-23).

**Import path:** `unified_api_contracts.canonical.crosscutting.ledger`

The ledger SSOT defines the cross-cutting financial record types used by the four ledgers that track as-if-filled state
across the system (paper, batch, and live trading paths).

**Key exports:**

| Symbol                              | Kind        | Description                                                                                                |
| ----------------------------------- | ----------- | ---------------------------------------------------------------------------------------------------------- |
| `LedgerRow`                         | Pydantic    | Base schema for all ledger entries                                                                         |
| `InstructionLedgerRow`              | alias       | `LedgerRow` alias — the instruction tape (SIGNAL/ORDER/FILL/CANCEL events)                                 |
| `PassiveLedgerRow`                  | alias       | `LedgerRow` alias — accruals (DeFi yield, funding, borrow costs)                                           |
| `TreasuryLedgerRow`                 | alias       | `LedgerRow` alias — treasury / capital-flow entries                                                        |
| `PricingLedgerRow`                  | alias       | `LedgerRow` alias — mark-to-market / pricing entries                                                       |
| 5 StrEnums                          | StrEnum × 5 | Ledger-specific enumerations (event types, directions, etc.)                                               |
| `CrossClientTransferForbiddenError` | Exception   | Raised when a transfer would cross client boundaries (enforced by execution-service `TransferCoordinator`) |

**Downstream SSOTs:**

- Architecture + four-ledger design: `/codex/04-architecture/global-ledger-architecture.md`
- Event taxonomy (all 11 lifecycle events): `/codex/02-data/ledger-event-taxonomy.md`

---

## Canonical data type names — 2026-05-23 cross-service alignment

**SSOT**: `registry/market_data_categories.py` → `DATA_TYPES_BY_ASSET_GROUP`.

All services (MTDS adapters, YAML configs, features-service, execution-service, deployment-api) MUST use the names from
this dict. Three-way divergence found in 2026-05-23 audit — now resolved. Banned aliases below must never reappear in
non-test Python source or YAML config:

| UAC canonical name  | Banned alias   | Where alias existed (now removed)                              |
| ------------------- | -------------- | -------------------------------------------------------------- |
| `dex_swaps`         | `swaps`        | venue_data_types.yaml, MTDS DEX adapters, features/execution   |
| `dex_pools`         | `liquidity`    | venue_data_types.yaml, MTDS DEX adapters, execution-service    |
| `lending_indices`   | `rate_indices` | venue_data_types.yaml, MTDS lending adapters, features-service |
| `mev_events`        | `mev_bundles`  | MDPS orchestration_scanner                                     |
| `bridge_events`     | `bridge_flows` | MDPS orchestration_scanner                                     |
| `flash_loan_events` | `flash_loans`  | MDPS orchestration_scanner                                     |
| `perp_funding`      | `perp-funding` | strategy-service probe script (hyphen form)                    |

**DeFi types added to `DATA_TYPES_BY_ASSET_GROUP["defi"]`** (UAC@`7511207a`):

`utilization`, `flash_loan_availability`, `vault_apy`, `vault_tvl`

**TradFi reference types added to `DATA_TYPES_BY_ASSET_GROUP["tradfi"]`**:

`corporate_action_confirmed`, `earnings_result`, `macro_result`, `mbp_10`

**Sports types added to `DATA_TYPES_BY_ASSET_GROUP["sports"]`**:

`markets`, `outcomes`, `settlements`

**Prediction data types** — dual casing coexists intentionally:

- `"market_lifecycle"` (lowercase) — MTDS/YAML on-disk hive partition key
- `"MARKET_LIFECYCLE"` (uppercase) — instruments-service GCS write key (preserved for backward-compat)

Both entries live in `DATA_TYPES_BY_ASSET_GROUP["prediction"]`. Services keying on instruments-service GCS output use
uppercase; MTDS path resolution uses lowercase.

**GCS path caveat — single-walk discipline**: `dex_pools` logical data type maps to on-disk hive segment
`data_type=dex_pool_state` (legacy name from before the rename). This mapping lives in
`onchain/app/core/mtds_output_config.py` in features-service. The on-disk segment is NOT re-keyed — the rename is
deferred to the next scheduled Phase 2 GCS migration window per `gcs_migration_bundle_pipeline_mode_2026_05_08.md`.

**Regression tests** (all green as of 2026-05-23):

- `unified-api-contracts/tests/test_data_type_canonicalization.py` — YAML × UAC cross-check
- `market-tick-data-service/tests/unit/test_adapter_data_type_canonicalization.py` — adapter SUPPORTED_DATA_TYPES × UAC
- `execution-service/tests/unit/test_amm_data_type_canonicalization.py` — AMM book_type_requirements × UAC

**Verification grep** (must return zero non-test hits):

```bash
grep -r "\"swaps\"\|\"liquidity\"\|\"rate_indices\"\|\"mev_bundles\"\|\"bridge_flows\"\|\"flash_loans\"\|\"perp-funding\"" \
  --include="*.py" --exclude-dir=".venv*" --exclude-dir="tests" .
```

---

## TradFi canonical schema — dual-source `source` column (Phase 3+)

**Plan SSOT**: `plans/active/tradfi_massive_dual_source_2026_05_28.md` Phases 1–3.

### `source` column — every TradFi parquet + manifest row

From Phase 3 (UTL@c7bfa427, MANIFEST_SCHEMA_VERSION=9), every TradFi parquet **must** carry a `source: str` column.

- **Writer enforcement**: `record_captured(source=...)` raises `MissingSourceError` when `category=="tradfi"` and
  `source` is omitted. QG STEP 5.64 enforces via `check_tradfi_source_explicit_at_record_captured.py`.
- **Schema version**: TradFi parquets are v9 (v8 → v9 bump at Phase 3). The `MANIFEST_SCHEMA_VERSION` constant in UTL
  reflects this.
- **`source` is NOT a hive partition key** — it is a row-level column within the parquet. Co-mingled sources under the
  same `day=…/asset_group=tradfi/venue=…/` prefix are disambiguated by the `source` column value, not by a separate hive
  shard.
- **Backfill**: pre-Phase-3 TradFi parquets are retroactively stamped `source='databento'` by
  `market_tick_data_service/scripts/backfill_tradfi_source_column.py`. Run only after the pre-migration drain (operator
  step) per the single-walk discipline.

Canonical source strings for TradFi:

| Source value  | Meaning                                                      |
| ------------- | ------------------------------------------------------------ |
| `"databento"` | Databento historical/live TradFi data                        |
| `"massive"`   | Massive (formerly Polygon.io) batch REST data (Starter tier) |
| `"yahoo"`     | Yahoo Finance rolling 60-day fallback (VIX 15m only)         |
| `"barchart"`  | Barchart preload (VIX 15m only)                              |

### SOURCE_PRIORITY — multi-source TradFi cells

`unified_api_contracts.canonical.crosscutting.source_priority.SOURCE_PRIORITY` records ordered source lists per
`(asset_group, data_type)` cell. TradFi cells after Phase 1 of `tradfi_massive_dual_source_2026_05_28.md`:

```python
SOURCE_PRIORITY = {
    ("tradfi", "trades"):        ["databento", "massive"],
    ("tradfi", "tbbo"):          ["databento", "massive"],
    ("tradfi", "ohlcv_1m"):      ["databento", "massive"],
    # databento primary; massive secondary; yahoo/barchart: VIX 15m rolling fallback
    ("tradfi", "ohlcv_15m"):     ["databento", "massive", "yahoo", "barchart"],
    ("tradfi", "options_chain"): ["databento", "massive"],
    ("tradfi", "futures_chain"): ["databento", "massive"],
    ...
}
```

Tie-breaker rule: first-in-list = primary (databento emits before Massive's 15-min delayed feed). When databento is
absent and massive is present, `select_primary_available_source()` returns `"massive"` automatically.

Emission latency for massive: 900,000 ms (15 min Starter-tier delayed feed).

### Multi-source merge helpers (Phase 2)

| Helper                                                             | Returns                                                |
| ------------------------------------------------------------------ | ------------------------------------------------------ |
| `get_all_sources_with_priority(asset_group, data_type)`            | `list[tuple[str, PipelineMode]]` — ordered source list |
| `select_primary_available_source(asset_group, data_type, avail)`   | `str` — highest-priority available source              |
| `detect_dual_source_conflicts(source_a, keys_a, source_b, keys_b)` | `list[tuple]` — conflicting rows (logs WARNING)        |

Conflict rows are emitted to the manifest with `divergence_kind=DUAL_SOURCE_DUPLICATE` — never silently dropped.

Import surface:
`from unified_api_contracts.canonical.crosscutting.source_priority import (SOURCE_PRIORITY, get_all_sources_with_priority, select_primary_available_source, detect_dual_source_conflicts)`.

### Generalised beyond TradFi — `source` is universal across ALL asset groups (2026-06-01)

`data_source_provenance_all_asset_groups_2026_06_01.md` generalised the `source` column from TradFi-only to **every
external-vendor market-data cell** (cefi / defi / sports / prediction / tradfi). The write-path gate is
**registry-driven, not asset_group-hardcoded** and uses the **universal-stamping** (auto-stamp) form:

- `source_required(asset_group, data_type)` — True iff the cell has **>1 external source** (must pass `source=`).
- `default_source(asset_group, data_type)` — the sole external source for a single-source cell (the writer
  **auto-stamps** it; no explicit `source=` needed). Universal stamping for swap-resilience: every external cell carries
  `source` even when one vendor exists today, so a later vendor swap/addition stays distinguishable.
- `COMPUTED_SOURCES` / `external_sources_for(...)` — internal emitters (`execution_service` / `strategy_service` /
  `features_onchain_service` / `cross_instrument`) are **exempt** (lineage is the upstream cell, not a vendor).
- UTL `ManifestWriter._resolve_and_validate_source` applies this in `record_captured` **and** legacy `add`; raises
  `MissingSourceError` on a blank multi-source cell or a source not in the cell's `SOURCE_PRIORITY` list.

Multi-source cells beyond TradFi: defi `oracle_prices` (`pyth_hermes`/`chainlink`) + `native_staking_rates`
(`solana_rpc`/`helius_rpc`); sports `FIXTURES` (`api_football`/`footystats`). The merge helpers above are
asset-group-agnostic (verified for cefi/defi/sports, uac@559dc81b). Landed: uac@aab101ad / utl@0f7198f2 / mtds@2ef636a6
/ instruments-service@6bbd6919.

---

## Audit-confirmed canonical picks — 2026-05-12 SSOT cleanup (Phase 1)

Six canonical decisions codified by the 2026-05-08/05-12 cross-asset-group catalogue audit
(`cross_asset_group_catalogue_audit_2026_05_10.md` Phase 1). These correct previously ambiguous or fragmented SSOTs.

| #   | Finding                                                                                                                                                                                                                               | Canonical resolution                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        | Key symbol / location                                                                                                                    |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | **Dual prediction module** — `canonical/domain/prediction/` (singular) and `canonical/domain/predictions/` (plural) appeared redundant                                                                                                | Both are canonical and non-redundant: singular = `PredictionMarketMapper` (venue→canonical mapping); plural = `PredictionCanonicalQuestionGroup` taxonomy. Services use facade: `from unified_api_contracts.prediction import ...`                                                                                                                                                                                                                                                                                                          | `unified_api_contracts/prediction.py` facade                                                                                             |
| 2   | **Radiant orphan adapter** — `instruments-service/adapters/defi/radiant.py` existed with no UAC protocol entry                                                                                                                        | `RADIANT-ARBITRUM` + `RADIANT-BSC` added to `DEFI_VENUE_DATA_TYPE_CAPABILITIES` (lending_indices + oracle_prices)                                                                                                                                                                                                                                                                                                                                                                                                                           | `registry/defi_venue_capabilities.py` UAC@`6dd274b`                                                                                      |
| 3   | **GMX + DRIFT dual-classification** — present in both `VENUES_BY_ASSET_GROUP["cefi"]` and defi registries                                                                                                                             | Retain in defi registries for protocol-coverage tracking; add `DEFI_VENUE_AXIS_OVERRIDES` dict to flag axis="cefi" for market-data routing. Consumers of defi registries must check this dict before routing. **⚠️ SUPERSEDED 2026-07-16 (operator ruling)**: **DRIFT CULLED** entirely (removed from all registries — no `drift.py`); **GMX is now defi-axis-only** (DEX-pool perp, `instrument_type=perpetual`) — the cefi `DEFI_VENUE_AXIS_OVERRIDES` no longer applies to either. See `/codex/04-architecture/solana-defi-coverage.md`. | `registry/defi_venues.py` `DEFI_VENUE_AXIS_OVERRIDES` UAC@`7c8482e`                                                                      |
| 4   | **Case-folding drift** — venue IDs used inconsistently (BLAZESTAKE vs SOLBLAZE, TRADERJOEV2 vs TRADER_JOEV2)                                                                                                                          | `VENUES_BY_ASSET_GROUP` uppercase keys are canonical user-facing IDs. `to_canonical_venue(venue_id)` helper in `defi_venues.py` normalises aliases. New aliases: BLAZESTAKE→SOLBLAZE-SOLANA, TRADERJOEV2→TRADER_JOEV2-AVALANCHE.                                                                                                                                                                                                                                                                                                            | `registry/defi_venues.py` `to_canonical_venue` UAC@`b73949d`                                                                             |
| 5   | **LST_TOKEN_TO_PROTOCOL_ASSET location unknown**                                                                                                                                                                                      | Confirmed at `unified_api_contracts.internal.domain.defi.lst` as `LST_TOKEN_TO_PROTOCOL_ASSET: dict[str, tuple[str, str]]` (LST token symbol → (protocol, base_asset)) + helpers `iter_lst_tokens_for_protocol` / `resolve_lst_protocol_asset`. Placement under `internal/` is correct (resolver scope, not contract-facing schema).                                                                                                                                                                                                        | `unified_api_contracts/internal/domain/defi/lst.py`                                                                                      |
| 6   | **Chain-set fragmentation** — `MAINNET_CHAIN_IDS` (19), `CHAIN_GENESIS_DATES` (21), `GAS_FEE_CHAIN_START_DATES` (14) were inconsistent subsets                                                                                        | Invariant: `MAINNET_CHAIN_IDS ⊇ CHAIN_GENESIS_DATES keys ⊇ GAS_FEE_CHAIN_START_DATES keys`. SCROLL+ZKSYNC added to `MAINNET_CHAIN_IDS`/`TESTNET_CHAIN_IDS`; BLAST+MODE+GNOSIS+SCROLL+ZKSYNC added to `GAS_FEE_CHAIN_START_DATES` (14→19 entries). Mainnet now 21 chains.                                                                                                                                                                                                                                                                    | `registry/chain_env.py` UAC@`6dd274b`                                                                                                    |
| 7   | **Kalshi API host migration** — `trading-api.kalshi.com` became `api.elections.kalshi.com` (election markets endpoint). 17 code sites across 5 repos pointed at the old host. Bug was dormant while Kalshi was `BLOCKED-CREDENTIALS`. | All UAC external schemas + 9 REST URL files + 1 WS URL file updated to new host. Cassettes re-recorded against new host. Phases 2-4 (live diff + credential unblock + canary) gated on Kalshi API key provisioning. Demo URL `demo-api.kalshi.co` unchanged.                                                                                                                                                                                                                                                                                | `unified_api_contracts/external/kalshi/` + instruments-service@`79ad855` + MTDS@`28b84ce` + execution-service@`8a3cbe48` (UAC@`5729197`) |

---

## TradFi `source` column — v9 canonical schema addition (2026-05-30)

**Plan**: `tradfi_massive_dual_source_2026_05_28.md` Phase 3 (task -017). **Manifest schema version**: bumped 8 → 9
(`MANIFEST_SCHEMA_VERSION = 9` in `unified_trading_library/manifest_writer.py`).

### What it is

Every TradFi parquet shard now carries a `source: str` column identifying which upstream data provider produced the
rows. This resolves the dual-source ambiguity introduced when Massive (formerly Polygon.io) was added alongside
Databento as a second TradFi feed.

### Closed-set values

Values mirror the `SOURCE_PRIORITY` source strings defined in `unified_api_contracts` (§7 above shows the full
`("tradfi", "ohlcv_15m")` cell with all 4 current values):

| Value         | Provider                      | Notes                                                                                                                                                                                                                                                              |
| ------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `"databento"` | Databento                     | All pre-Phase-3 TradFi data. Stamped by Phase 5 backfill script.                                                                                                                                                                                                   |
| `"massive"`   | Massive (formerly Polygon.io) | New feed added by this plan. `MassiveTradfiRestConnector` stamps this value.                                                                                                                                                                                       |
| `"yahoo"`     | Yahoo Finance                 | VIX 15m rolling fallback; confirmed live-stamped (`unified-trading-library` `test_manifest_writer_source.py`).                                                                                                                                                     |
| `"barchart"`  | Barchart                      | VIX 15m rolling fallback per `SOURCE_PRIORITY` — CLAUDE.md's TradFi/Databento sourcing rules note Barchart RETIRED; this row's current live-vs-retired status needs re-verification against `/codex/02-data/tradfi-databento-sourcing-ssot.md`, not asserted here. |

This table previously listed only `databento`/`massive` and called the set "intentionally closed" at that size — that
undercounted the doc's own `SOURCE_PRIORITY` code block 2 sections above, which already showed 4 values for the
`ohlcv_15m` cell. Adding a genuinely new TradFi source (beyond the 4 above) requires: (1) a new `SOURCE_PRIORITY` entry
in UAC, (2) an explicit string constant in the adapter (`MASSIVE_SOURCE`, `DATABENTO_SOURCE`, etc.), and (3) a `source=`
kwarg at every `record_captured` callsite for that category.

### Enforcement

`MissingSourceError` (UTL `manifest_writer.py`) is raised when `record_captured(category="tradfi", ...)` is called
without a non-empty `source=` kwarg. At the time this section was written (2026-05-30), non-TradFi categories (`cefi`,
`defi`, `onchain`, etc.) were unaffected — `source` defaulted to `""` for those cells.

> **Superseded by the 2026-06-01 generalization above** (§ "Generalised beyond TradFi"): `MissingSourceError` now also
> fires for any **multi-source** cell in ANY asset group, not just TradFi — e.g. defi `oracle_prices`/
> `native_staking_rates`, sports `FIXTURES`. A non-TradFi category is only "unaffected" when it has a single external
> source (`default_source()` auto-stamps it) or no external source at all.

QG STEP 5.64 (`check_tradfi_source_explicit_at_record_captured.py`, wired into
`unified-trading-library/scripts/quality-gates.sh`) performs a static AST walk to catch new `record_captured` callsites
that omit `source=`. Callsites that forward `source` via `**kwargs` must carry the
`# QG-allow: tradfi-source-not-applicable` inline marker.

### Dual-source cell example

A TradFi OHLCV cell covering a day where both Databento and Massive ran produces two separate shards, distinguished by
`source`:

```
raw_tick_data/by_date/day=2026-05-30/asset_group=tradfi/venue=NYSE/data_type=ohlcv_1m/source=databento/SPY.parquet
raw_tick_data/by_date/day=2026-05-30/asset_group=tradfi/venue=NYSE/data_type=ohlcv_1m/source=massive/SPY.parquet
```

Consumers that need the best-available signal consult `SOURCE_PRIORITY` to select the preferred shard; consumers that
need auditable provenance can read both.

### Manifest row wiring

`AvailabilityRecord` gained a `source: str = ""` field (v9). The manifest `_ROW_KEY_COLUMNS` tuple includes `"source"`
after `"pipeline_mode"`. Rows written by pre-v9 code have `source=""` until the Phase 5 backfill script
(`backfill_tradfi_source_column.py`) stamps `source="databento"` on every legacy TradFi parquet.

### Phase 5 backfill

The backfill script is at `market-tick-data-service/market_tick_data_service/scripts/backfill_tradfi_source_column.py`.
It performs a single GCS walk over all TradFi parquets under `raw_tick_data/by_date`, stamps `source="databento"` on
rows where the column is absent or empty, and rewrites the file in-place (idempotent). A `--dry-run` mode prints what
would change without touching GCS.

**Pre-execution operator checklist** (execution blocked pending scheduling — see task -029):

1. Stop all TradFi-writing VMs
2. Consolidate the manifest
3. Snapshot `catalogue.parquet` to `_index/snapshots/pre_dual_source_2026_05_28.parquet`
4. Run the backfill script
5. Run the post-backfill audit (task -030/-031)
6. Resume TradFi VMs
