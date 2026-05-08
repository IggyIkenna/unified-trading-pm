---
scope: [engineer, admin]
---

# Venue Availability SSOT

> **See also:** `codex/02-data/availability-manifest-and-data-status.md` for the complete availability manifest schema
> (v7 — current; `MANIFEST_SCHEMA_VERSION = 7` in UTL `manifest_writer.py`), per-service shard dimensions, data status
> page hierarchy, availability % calculation, and integrity principles. This document covers venue launch dates and
> instrument availability specifically.

## What This Is

Venue availability (launch dates, supported instrument types, active chains) is the single source of truth for
determining which instruments existed at a given historical date. This prevents backtesting on data that didn't exist
yet and ensures instruments-service only returns instruments that were live at the query time.

## Where Availability Lives

### UAC VenueMapping (primary SSOT)

`unified_api_contracts.registry.venue_mapping.VenueMapping` — canonical venue metadata including launch date:

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

| Removed                                  | Reason                                  |
| ---------------------------------------- | --------------------------------------- |
| Bitstamp                                 | Low volume, removed from strategy scope |
| Elysium, Arkham, Bloxroute, Infura       | Deleted providers                       |

Do not add these back to any adapter or venue mapping.

**Pyth — UNBANNED 2026-05-06** (Solana-only). Originally listed above as a deleted provider; re-added for Solana
on-chain price feeds (LST yields jitoSOL / mSOL / bSOL). Chainlink covers EVM-only chains (Arb / Base / Polygon);
Pyth fills the Solana gap via Hermes (HTTPS pull) for batch and PythNet (Solana RPC) for live. Scope is
Solana-only — other chains continue using Chainlink. SSOT: CLAUDE.md "Pyth — UNBANNED 2026-05-06" rule.

## Adding a New Venue

1. Add `VenueEntry` to `unified_api_contracts/registry/venue_mapping.py` with `launch_date`
2. Create or update an adapter in `instruments_service/reference_data/adapters/`
3. Set `available_from_datetime` in `InstrumentRecord` from the known deploy/TGE date
4. Register adapter in `factory.py` (`CANONICAL_VENUE_TO_ADAPTER`, `_ADAPTERS`)
5. Add to MTDS venue list in `market_tick_data_service/config/venues.yaml`

## Key Files

| File                                                        | Purpose                           |
| ----------------------------------------------------------- | --------------------------------- |
| `unified_api_contracts/registry/venue_mapping.py`           | VenueEntry registry (SSOT)        |
| `instruments_service/reference_data/factory.py`             | Adapter registry                  |
| `instruments_service/reference_data/adapters/eigenlayer.py` | `_EIGEN_DEPLOY_DATE = 2024-09-17` |
| `instruments_service/reference_data/adapters/ethfi.py`      | `_ETHFI_DEPLOY_DATE = 2024-03-18` |
| `instruments_service/reference_data/adapters/lido.py`       | `_LIDO_DEPLOY_DATE = 2020-12-18`  |
| `unified_trading_library/reference_data/validation.py`      | `validate_venue_names()`          |

## Related Docs

- `codex/02-data/instrument-pipeline-defi.md` — How instruments flow into MTDS/MDPS/features
- `codex/04-architecture/batch-live-architecture.md` — How `as_of_date` works in batch vs live (single SSOT)
