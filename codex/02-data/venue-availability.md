---
doc_type: codex-ssot
title: Venue Availability SSOT
summary:
  Venue availability SSOT — the 4 per-asset_group venue registries (VENUES_BY_ASSET_GROUP / ALL_DEFI_VENUES /
  venue_launch_dates / coverage_starts), the UPPERCASE-vs-lowercase case-folding contract, the venue-class taxonomy, and
  as_of_date / available_from_datetime instrument filtering.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [instruments, defi, backfill, data-correctness, registry, cefi]
related:
  [
    codex/02-data/availability-manifest-and-data-status.md,
    codex/02-data/instrument-pipeline-defi.md,
    codex/04-architecture/batch-live-architecture.md,
  ]
created: 2026-04-03
authoritative_for:
  [
    per-asset_group venue-availability registries and venue-class taxonomy,
    venue identifier case-folding contract,
    InstrumentRecord available_from_datetime as-of filtering,
  ]
referenced_by:
  [
    codex/02-data/availability-manifest-and-data-status.md,
    codex/02-venues/venue-registry-reference.md,
    codex/03-services/venue-capability-registry.md,
  ]
owner:
last_reviewed: 2026-05-17
code_refs:
---

# Venue Availability SSOT

> **See also:** `codex/02-data/availability-manifest-and-data-status.md` for the complete availability manifest schema
> (**v8 column-shape ratified 2026-05-09**; `MANIFEST_SCHEMA_VERSION = 7` constant transitionally pinned in UTL
> `manifest_writer.py:131` until Phase 4.DEFAULT-REMOVAL bumps to `8`), per-service shard dimensions, data status page
> hierarchy, availability % calculation, and integrity principles. This document covers venue launch dates and
> instrument availability specifically. (v8/v7 reconciliation per codex audit IN-8 2026-05-12.)

## What This Is

Venue availability (launch dates, supported instrument types, active chains) is the single source of truth for
determining which instruments existed at a given historical date. This prevents backtesting on data that didn't exist
yet and ensures instruments-service only returns instruments that were live at the query time.

## Where Availability Lives — the per-asset_group venue-registry SSOTs (clarified 2026-05-12)

**Three distinct SSOTs** in `unified_api_contracts/registry/`. Don't conflate them — case-folding / dual-classification
audits (CF-1/CF-2/CF-3, DF-3, SP-3, PR-1 per `catalogue_audit_*_2026_05_12.md`) anchor on these specific registries, NOT
on the legacy `venue_mapping.py` helper:

1. **`market_data_categories.py:VENUES_BY_ASSET_GROUP`** — primary venue catalogue per asset_group: 21 cefi / 8 tradfi /
   2 prediction / ~10 sports venue ids (UPPERCASE: `BINANCE-SPOT`, `ODDS_API`, `POLYMARKET`).
2. **`defi_venues.py:ALL_DEFI_VENUES`** + `DEFI_VENUE_PHASE` / `MTDS_DEFI_VENUES` — ~70 DeFi venue ids (UPPERCASE per
   the same case convention).
3. **`venue_launch_dates.py`** — per-venue `launch_date` for the `EXPECTED_PRE_VENUE_LAUNCH` reason taxonomy member
   (UAC@ac218dc 2026-05-07).
4. **`coverage_starts.py`** + per-asset-group `*_SOURCE_COVERAGE_START` constants — source-coverage windows for the
   `EXPECTED_PRE_SOURCE_COVERAGE_START` reason.

The `defi_venue_capabilities.py:DEFI_VENUE_DATA_TYPE_CAPABILITIES` dict (merged into `VENUE_DATA_TYPE_CAPABILITIES` at
load) is the per-`(venue, data_type)` start-date SSOT — used by adapter coverage-window clipping. Distinct from
`defi_venues.py` which is the venue-set SSOT.

### UAC VenueMapping (legacy helper — NOT the venue-set SSOT)

`unified_api_contracts.registry.venue_mapping.VenueMapping` / `VenueEntry` is a per-venue **date-helper**
(`get_venue_start_date`, `get_expected_trading_dates`) used by manifest readers (see
`availability-manifest-and-data-status.md:544-547`). It is NOT the venue-set registry — that role is split across the
four SSOTs above per asset_group. The historical "primary SSOT" framing pre-dated the per-asset-group split landed in
2026-04-25 (`market_data_categories.py` Wave 3).

## Venue identifier case-folding contract (codified 2026-05-12 per codex audit IN-3)

The 5 catalogue audits keep re-flagging case-folding drift between two distinct identifier spaces:

| Space                                                | Convention | Examples                                               | Where it lives                                                                                                                    |
| ---------------------------------------------------- | ---------- | ------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------- |
| **User-facing venue id** (manifest rows, UI, paths)  | UPPERCASE  | `BINANCE-SPOT` / `ODDS_API` / `POLYMARKET` / `AAVE_V3` | `VENUES_BY_ASSET_GROUP` + `ALL_DEFI_VENUES` UAC registries                                                                        |
| **Python symbol / secret key / source-coverage key** | lowercase  | `binance` / `odds_api` / `polymarket` / `aave_v3`      | `_BASE_VENUES_BY_ASSET_GROUP` / `SourceCapability.source` / `*_SOURCE_COVERAGE_START` / instruments-service adapter registry keys |

Until the `to_canonical_venue()` helper ships (cross-asset Phase 1D), honest-coverage clip joins MUST normalise on both
sides — e.g. `CEFI_SOURCE_COVERAGE_START["BINANCE".lower()]` (NOT `CEFI_SOURCE_COVERAGE_START["BINANCE-SPOT"]`, which
silently misses every spot venue). Reference incidents: CF-3 / CF-4 / SP-3 in
`plans/active/issues/catalogue_audit_*_2026_05_12.md`. The QG ratchet that statically enforces case-correctness is
tracked in IN-22.

## Venue-class taxonomy (codified 2026-05-12 per codex audit IN-9)

The 5 catalogue audits also kept re-flagging that the workspace uses "venue" loosely. Closed-set taxonomy:

| Class                        | Has instrument universe? | Has MTDS market-data adapter? | Has execution connector? | Examples (catalogue-audit cite)                                                                                              |
| ---------------------------- | ------------------------ | ----------------------------- | ------------------------ | ---------------------------------------------------------------------------------------------------------------------------- |
| **Market-data venue**        | ✅                       | ✅                            | depends                  | BINANCE-SPOT, AAVE_V3-ETHEREUM                                                                                               |
| **Refdata-only source**      | ✅ (universe metadata)   | ❌                            | ❌                       | POLYGON.IO instruments fetch (TF-5); OPEN_METEO (SP-2)                                                                       |
| **Execution-only connector** | ❌                       | ❌                            | ✅                       | Jupiter, Wormhole/LayerZero bridges (DF-19)                                                                                  |
| **API-capability source**    | ❌                       | partial (per data_type only)  | ❌                       | `bitstamp` / `huobi` / `kucoin` / `mexc` SourceCapabilities (CF-12); FRED / POLYGON / ECB / OPENBB / OFR / REGULATORY (TF-4) |
| **Bundled combination**      | ✅ (multi-source)        | ✅                            | ✅                       | most production market-data venues                                                                                           |

When adding a new venue id to `VENUES_BY_ASSET_GROUP`, declare its class up-front + verify each ✅ has a wired adapter /
capability / connector. QG ratchet enforcement is tracked in IN-22.

## Adding a new venue (per-asset_group SSOT touchpoints)

1. Add the UPPERCASE venue id to `VENUES_BY_ASSET_GROUP[ag]` (or `ALL_DEFI_VENUES`).
2. Declare the venue class per IN-9 taxonomy above (record in the same commit).
3. Add `launch_date` to `venue_launch_dates.py`.
4. Add source-coverage start to `*_SOURCE_COVERAGE_START` (lowercase key per the case-folding contract).
5. For DeFi: add per-(venue, data_type) start-dates to `defi_venue_capabilities.py:DEFI_VENUE_DATA_TYPE_CAPABILITIES`.
6. For instruments-service-backed venues: register adapter in `factory.py:CANONICAL_VENUE_TO_ADAPTER` (the
   instruments-service auto-registration mechanism is documented in IN-13; cross-link to `instrument-pipeline-defi.md`).

## QG ratchet — every venue id must be wired (codex audit IN-22 2026-05-12)

New QG STEP 5.7x (in-flight) statically asserts: every venue id in `VENUES_BY_ASSET_GROUP[ag]` and `ALL_DEFI_VENUES` has
at least one of:

(a) an instruments-service adapter mapping in `CANONICAL_VENUE_TO_ADAPTER` (or auto-mapped via subgraph-prefix /
protocol-indirection per IN-13), OR (b) a documented "no-instrument-universe" exemption per the IN-9 venue-class
taxonomy (execution-only / refdata-only / api-capability-source).

Motivating catalogue audits:

- CF-9 / CF-10 — bare `GMX` / `DRIFT` cefi venues with no adapter (GHOST). _(2026-07-16: `DRIFT` CULLED entirely; `GMX`
  reclassified **defi-axis** — see `../04-architecture/solana-defi-coverage.md`.)_
- DF-6 — vault venues marked "live" with no adapter, handler, OR capability anywhere.
- DF-20 — MARGINFI / SOLEND "live" ghosts.

QG script path: `unified-trading-pm/scripts/quality_gates/check_venue_adapter_coverage.py` (planned). Owner: governance

- QG maintainer. Until the QG ships, reviewers flag PRs that add a venue id to a registry without one of (a) / (b)
  checked in the same commit.

```python
@dataclass
class VenueEntry:
    venue_id: str           # canonical e.g. "EIGENLAYER-ETHEREUM"
    protocol: str           # "EIGENLAYER"
    chain: str              # "ETHEREUM"
    launch_date: date       # When the venue/protocol went live
    supported_types: list[InstrumentType]
    active: bool
```

Canonical venue format: `PROTOCOL-CHAIN` (e.g. `ETHERFI-ETHEREUM`, `LIDO-ETHEREUM`, `EIGENLAYER-ETHEREUM`).

### Instrument Adapter `available_from_datetime`

Each `InstrumentRecord` carries:

```python
available_from_datetime: datetime | None
```

Set from the on-chain deployment date or protocol TGE date. instruments-service adapters populate this from known
constants:

| Venue                  | Available From | Source                 |
| ---------------------- | -------------- | ---------------------- |
| `ETHERFI-ETHEREUM`     | 2023-11-01     | weETH deployment       |
| `LIDO-ETHEREUM`        | 2020-12-18     | stETH deployment       |
| `EIGENLAYER-ETHEREUM`  | 2024-09-17     | EIGEN token TGE        |
| `ETHERFI-GOV-ETHEREUM` | 2024-03-18     | ETHFI token TGE        |
| `BINANCE-FUTURES`      | 2019-09-13     | Binance Futures launch |
| `HYPERLIQUID`          | 2023-10-01     | Hyperliquid mainnet    |

### DeFi Adapter Historical Block Resolution

For on-chain venues, adapters resolve deployment dates to block numbers using:

- Etherscan/Alchemy `eth_getBlockByTimestamp` — converts date to nearest block number
- The Graph `block: {number: X}` — queries subgraph state at historical block

This enables accurate historical instrument discovery for backtesting.

## Filtering by Availability

instruments-service `get_instruments()` accepts an optional `as_of_date` parameter. Instruments with
`available_from_datetime > as_of_date` are excluded:

```python
instruments = await adapter.get_instruments(
    instrument_type="GOVERNANCE_TOKEN",
    as_of_date=datetime(2024, 1, 1, tzinfo=UTC),
)
# Returns [] for EIGEN (launched Sep 2024) and ETHFI (launched Mar 2024)
```

MTDS uses this to only fetch data for instruments that existed on the target date, preventing empty parquet files for
pre-launch instruments.

## Venue Name Validation

`validate_venue_names()` in UTL (`unified_trading_library.reference_data.validation`) enforces canonical venue name
format:

```python
from unified_trading_library.reference_data.validation import validate_venue_names

validate_venue_names(["ETHERFI-ETHEREUM", "LIDO-ETHEREUM"])  # OK
validate_venue_names(["etherfi", "lido"])  # raises ValueError
```

Called at service startup to catch misconfigured venue names before they cause data issues.

## Removed Venues (Do NOT Reference)

The following venues were removed from UAC and all adapters:

| Removed                            | Reason                                  |
| ---------------------------------- | --------------------------------------- |
| Bitstamp                           | Low volume, removed from strategy scope |
| Elysium, Arkham, Bloxroute, Infura | Deleted providers                       |

Do not add these back to any adapter or venue mapping.

**Pyth — UNBANNED 2026-05-06** (Solana-only). Originally listed above as a deleted provider; re-added for Solana
on-chain price feeds (LST yields jitoSOL / mSOL / bSOL). Chainlink covers EVM-only chains (Arb / Base / Polygon); Pyth
fills the Solana gap via Hermes (HTTPS pull) for batch and PythNet (Solana RPC) for live. Scope is Solana-only — other
chains continue using Chainlink. SSOT: CLAUDE.md "Pyth — UNBANNED 2026-05-06" rule.

## Adding a New Venue

1. Add the venue id to the appropriate per-asset_group SSOT:
   - DeFi: `unified_api_contracts/registry/defi_venues.py:ALL_DEFI_VENUES` (+ DEFI_VENUE_PHASE / MTDS_DEFI_VENUES if
     applicable)
   - CeFi / TradFi / Sports / Prediction:
     `unified_api_contracts/registry/market_data_categories.py:VENUES_BY_ASSET_GROUP[asset_group]`
2. Add `launch_date` entry to `unified_api_contracts/registry/venue_launch_dates.py` (for `EXPECTED_PRE_VENUE_LAUNCH`
   reason).
3. Add source-coverage window to `unified_api_contracts/registry/coverage_starts.py` (`*_SOURCE_COVERAGE_START`).
4. For DeFi: add per-`(venue, data_type)` capability rows to
   `defi_venue_capabilities.py:DEFI_VENUE_DATA_TYPE_CAPABILITIES`.
5. Create or update an adapter in `instruments_service/reference_data/adapters/<asset_group>/`.
6. Set `available_from_datetime` in `InstrumentRecord` from the known deploy/TGE date.
7. Register adapter in `factory.py` (`CANONICAL_VENUE_TO_ADAPTER`, `_ADAPTERS`).
8. Add to MTDS venue list in `market_tick_data_service/config/venues.yaml`.

## Key Files

| File                                                             | Purpose                                                                                                         |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------- |
| `unified_api_contracts/registry/market_data_categories.py`       | `VENUES_BY_ASSET_GROUP` per-asset_group venue catalogue (primary SSOT for cefi/tradfi/sports/prediction venues) |
| `unified_api_contracts/registry/defi_venues.py`                  | `ALL_DEFI_VENUES` / `DEFI_VENUE_PHASE` / `MTDS_DEFI_VENUES` (primary SSOT for DeFi venues)                      |
| `unified_api_contracts/registry/defi_venue_capabilities.py`      | `DEFI_VENUE_DATA_TYPE_CAPABILITIES` — per-(venue, data_type) start-date dict                                    |
| `unified_api_contracts/registry/venue_launch_dates.py`           | Per-venue launch_date (used by `EXPECTED_PRE_VENUE_LAUNCH` reason)                                              |
| `unified_api_contracts/registry/coverage_starts.py`              | Per-asset-group `*_SOURCE_COVERAGE_START` (used by `EXPECTED_PRE_SOURCE_COVERAGE_START`)                        |
| `unified_api_contracts/registry/venue_mapping.py`                | VenueEntry date-helper (`get_venue_start_date`, `get_expected_trading_dates`) — NOT the venue-set SSOT          |
| `instruments_service/reference_data/factory.py`                  | Adapter registry                                                                                                |
| `instruments_service/reference_data/adapters/defi/eigenlayer.py` | `_EIGEN_DEPLOY_DATE = 2024-09-17`                                                                               |
| `instruments_service/reference_data/adapters/defi/ethfi.py`      | `_ETHFI_DEPLOY_DATE = 2024-03-18`                                                                               |
| `instruments_service/reference_data/adapters/defi/lido.py`       | `_LIDO_DEPLOY_DATE = 2020-12-18`                                                                                |
| `unified_trading_library/reference_data/validation.py`           | `validate_venue_names()`                                                                                        |

## Related Docs

- `codex/02-data/instrument-pipeline-defi.md` — How instruments flow into MTDS/MDPS/features
- `codex/04-architecture/batch-live-architecture.md` — How `as_of_date` works in batch vs live (single SSOT)
