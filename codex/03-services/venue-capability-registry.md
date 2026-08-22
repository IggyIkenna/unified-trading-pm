---
doc_type: codex-ssot
title: venue-capability-registry
summary: "The authoritative source of what each venue supports (operations, instruments, collateral/LTV, margin spec,
  commission structure, liquidation, rate limits, regional restrictions) — declared in UAC
  registry/capability_declarations/_{category}.py, queried via a typed facade by strategy/execution/risk/allocator;
  static at deploy time (consumers pin UAC major), no mid-run hot-reload except commission-tier values."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, strategy-service, unified-api-contracts]
scope: [engineer]
tags: [venue-capability, registry, uac, execution, strategy, cefi, defi]
related:
  [
    /codex/02-venues/venue-registry-reference.md,
    /codex/03-services/portfolio-allocator.md,
    /codex/04-architecture/capital-efficiency-patterns.md,
    /codex/02-data/contracts-scope-and-layout.md,
  ]
created: 2026-04-17
authoritative_for: [venue capability registry, venue capability declaration schema]
referenced_by:
  [
    /codex/02-venues/prime-brokers.md,
    /codex/02-venues/unity-integration.md,
    /codex/02-venues/venue-registry-reference.md,
    /codex/03-services/portfolio-allocator.md,
    /codex/06-coding-standards/artifact-naming.md,
  ]
owner:
last_reviewed:
code_refs:
---

# venue-capability-registry

> **What it is:** The authoritative source of what each venue supports (operations, instruments, collateral rules,
> margin spec, commission structure, regional restrictions, liquidation rules). Lives in UAC
> `registry/capability_declarations/` and is accessible via a typed facade. Every service that makes routing, risk, or
> pre-flight decisions queries this registry.

## Why a dedicated registry

Without a registry:

- Each service hard-codes venue knowledge (duplication)
- Adding a venue requires updating N codebases
- Capability assumptions drift (one service thinks Binance supports X; another doesn't)
- Regulatory restrictions leak

With the registry:

- Single source of truth
- Versioned + consumer-opt-in
- New venue = one declaration file + adapter
- Capability queries are type-safe

## Scope

The registry covers:

1. **Venue identity** — venue_id, venue_type, category
2. **Operations** — what actions are supported (TRADE, SWAP, LEND, ...)
3. **Instruments** — spot/perp/options/lending markets/pools
4. **Collateral rules** — LTV, haircuts, eligible collateral
5. **Margin spec** — isolated, cross, portfolio; netting rules
6. **Commission structure** — fee tiers, maker/taker, commissions per child book
7. **Liquidation spec** — triggers, fees, queue mechanics
8. **Rate limits** — per endpoint, per second
9. **Regional restrictions** — blocked jurisdictions
10. **Pass-through flags** — cross-margin supported, portfolio margin supported, sub-account supported

## Storage location

Per CLAUDE.md:

- UAC: `unified-api-contracts/unified_api_contracts/registry/capability_declarations/`
- Sub-files per venue category:
  - `_cefi.py` — Binance, OKX, Bybit, Hyperliquid, Deribit
  - `_tradfi.py` — IBKR, CME, ICE
  - `_defi.py` — All DeFi protocols + CHAIN_RPC_TEMPLATES
  - `_sports.py` — Unity, Betfair, direct books, aggregators
  - `_prediction.py` — Polymarket, Kalshi

## Consumer access

```python
from unified_api_contracts.registry import venue_capability_registry

cap = venue_capability_registry.get("BINANCE")
if cap.supports(operation=Op.TRADE, instrument_type=InstType.PERP):
    # route to Binance
    ...

ltv = cap.ltv_for(asset=Asset.STETH, on_protocol=Protocol.AAVE_V3)
assert ltv == Decimal("0.75")

margin_spec = cap.margin_spec(account_type=AccountType.CROSS)
required_margin = margin_spec.required_for(positions)
```

## Capability declaration schema

> **Note (2026-08-21)**: the dataclass below is the original V1-era design sketch. The real shipped registry type is
> `VenueCapabilityV2` (Pydantic, `unified_api_contracts/internal/architecture_v2/venue_capability_v2.py`) — a superset
> that has not been fully reconciled field-for-field against this doc. Its `features` set matches this doc's
> illustrative `VenueFeature` example exactly (`CROSS_MARGIN`/`PORTFOLIO_MARGIN`/`SUBACCOUNT`/`ATOMIC_MULTI_LEG` all
> survived a 2026-08-20 dedup against `VenueCapability`'s own overlapping members — 6 redundant duplicates removed,
> `DARK_POOL`/`BACK_LAY_EXCHANGE` also unique-kept, `unified-api-contracts@0d7afa29e`), so no drift there. Its transfer
> eligibility fields are new and not yet in this sketch — see "Transfer capability" below.

```python
@dataclass
class VenueCapability:
    venue_id: VenueId
    venue_type: Literal["SINGLE_VENUE", "META_BROKER", "DATA_AGGREGATOR"]
    category: Literal["CEFI", "DEFI", "SPORTS", "TRADFI", "PREDICTION"]
    supported_operations: List[OperationSpec]
    collateral_rules: Optional[CollateralRules]
    margin_spec: Optional[MarginSpec]
    liquidation_spec: Optional[LiquidationSpec]
    commission_structure: CommissionStructure
    regional_restrictions: RegionalRestrictions
    rate_limits: RateLimits
    features: Set[VenueFeature]   # e.g., CROSS_MARGIN, PORTFOLIO_MARGIN, SUBACCOUNT, ATOMIC_MULTI_LEG
    child_venues: Optional[List[ChildVenueDecl]]  # for META_BROKER
```

## Websocket-protocol axis (2026-08-21)

Every `SourceCapability` in `registry/capability_declarations/` carries `ws_protocol: WsProtocolSpec | None`
(`unified_api_contracts/registry/ws_protocol.py`) — the venue's PUBLISHED websocket contract: ping/pong initiator +
cadence, forced-disconnect window, auth-refresh mechanism/cadence, subscription/connection caps,
`duplicate_subscription_allowed` (make-before-break rotation feasibility), post-reconnect resubscribe semantics,
sequence-gap detection, and REST gap-backfill endpoints. Resolve via `resolve_ws_protocol(source)` after
`capability_data.bootstrap_capabilities()`. Honest provenance: fields default `None` (= not researched / not
published — never a guess) and `doc_url`/`doc_retrieved` carry the citation; a venue with no ws surface records
`no_websocket_surface` in `notes` explicitly. `extra="forbid"` makes a declaration typo an import-time error. Primary
consumer: the UTL `WsSessionManager` rotation policy — SSOT
`/codex/04-architecture/venue-websocket-resilience.md`.

## Operation spec

```python
@dataclass
class OperationSpec:
    operation: OperationEnum
    instruments: List[InstrumentType]
    constraints: Dict[str, Any]         # venue-specific (e.g., min_size, max_size, tick_size)
```

Example Binance:

```python
OperationSpec(operation=Op.TRADE, instruments=[SPOT, PERP_USDT, PERP_USDC, PERP_COIN, OPTIONS_EUROPEAN], ...)
OperationSpec(operation=Op.QUOTE, instruments=[SPOT, PERP_USDT], ...)
OperationSpec(operation=Op.TRANSFER, instruments=[], constraints={"intra_account_only": False, "withdraw_allowed": True})
OperationSpec(operation=Op.TICKS, instruments=[SPOT, PERP_USDT, PERP_USDC, OPTIONS]),
```

## Collateral rules schema

```python
@dataclass
class CollateralRules:
    eligible_assets: Dict[Asset, LtvAndHaircut]
    liquidation_threshold: Decimal
    interest_on_collateral: bool         # for DeFi lending

@dataclass
class LtvAndHaircut:
    max_ltv: Decimal                     # e.g., 0.75 for stETH on Aave
    haircut: Decimal                     # e.g., 1 - ltv
    liquidation_bonus: Decimal           # e.g., 0.05 (5%)
```

## Margin spec schema

```python
@dataclass
class MarginSpec:
    mode: MarginMode                     # ISOLATED | CROSS | PORTFOLIO
    initial_margin_pct: Decimal
    maintenance_margin_pct: Decimal
    netting_rules: List[NettingRule]
    portfolio_margin_greek_model: Optional[GreekModel]  # for Deribit
```

## Commission structure schema

```python
@dataclass
class CommissionStructure:
    type: Literal["FLAT", "TIERED", "PERCENT", "COMMISSION_ON_WIN"]
    tiers: List[CommissionTier]
    fee_bps_maker: Decimal
    fee_bps_taker: Decimal
    promotion_active: bool
```

For Unity child books:

```python
child_venues=[
    ChildVenueDecl(child_venue_id="VX",                  commission=Decimal("0.002"),  supported_sports=[SOCCER, TENNIS, BASKETBALL]),
    ChildVenueDecl(child_venue_id="SHARPBET",            commission=Decimal("0.002"),  ...),
    ChildVenueDecl(child_venue_id="PINNACLE_VIA_UNITY",  commission=Decimal("0.004"),  ...),
    ChildVenueDecl(child_venue_id="BETFAIR_VIA_UNITY",   commission_type="COMMISSION_ON_WIN",  commission_on_win=Decimal("0.005"), ...),
    ChildVenueDecl(child_venue_id="BROKER5",             commission=Decimal("0.030"),  ...),
    ChildVenueDecl(child_venue_id="IBCBET",              commission=Decimal("0.015"),  ...),
    ...
]
```

## Transfer capability (V2 addition, 2026-08-20)

`VenueCapabilityV2` carries a `TransferCapabilityV2` field beyond the generic `Op.TRANSFER` `OperationSpec` shown
above — declares WHICH transfer rails/custodians a venue is eligible for, not just whether transfer is supported at
all. Schema only; population is separate, tracked work (per-venue values are not yet filled in for the 192+ venue
estate — same gap as the collateral/margin fields above).

```python
class TransferCapabilityV2(BaseModel):
    copper_eligible: bool = False
    ceffu_eligible: bool = False           # CEFFU is a specific custody-provider identity Copper routes on behalf
                                            # of, not a synonym — kept independent, not merged with copper_eligible
    manual_transfer_eligible: bool = False
    prime_broker_eligible: list[str] = []  # open-set of broker names, e.g. ["IBKR", "Alpaca"] — not a closed enum,
                                            # so a new prime-broker integration never needs a schema edit
```

Every field defaults to the eligible-nowhere state. Field set sourced from
`/plans/audit/results/venue_transfer_custody_collateral_research_2026_08_18.md`. Unblocks W22 transfer routing on the
schema side (`unified-api-contracts@45a545e5ad`); still needs real per-venue population before W22 can consume live
values.

## Versioning

Venue capability declarations follow UAC semver:

- Minor bump: adding new operation/instrument support (backward compatible)
- Major bump: removing support, changing LTV semantics, renaming enums

Consumers pin UAC major version. See
[/codex/04-architecture/schema-versioning.md](/codex/04-architecture/schema-versioning.md).

## Consumers

Every decision-making service:

| Service                    | What it queries                                                            |
| -------------------------- | -------------------------------------------------------------------------- |
| strategy-service           | Operation + instrument eligibility at config time; slot-startup validation |
| execution-service          | Per-order pre-flight: supported? max size? margin?                         |
| risk-and-exposure-service  | Margin sim with haircuts; liquidation model                                |
| portfolio-allocator        | Category diversification limits lookup                                     |
| transfer-rebalance-service | Transfer types supported by venue                                          |
| pbms                       | Venue-account structure; sub-account support                               |
| client-onboarding          | Regional restrictions per jurisdiction                                     |

## Updates flow

1. New venue feature or correction: PR to UAC `registry/capability_declarations/_{category}.py`
2. Conformance tests + integration tests
3. UAC semver bump (patch/minor/major)
4. Consumer repos auto-update via `update-dependency-version.yml`
5. QG on every consumer

## Runtime refresh

UAC venue capabilities are **static at deploy time** — compiled into the dependency. Services don't hot-reload
capabilities mid-run.

If venue capability changes (new operation, new instrument), the workflow:

1. PR to UAC with new declaration
2. UAC release
3. Consumer services re-deploy
4. No mid-run hot-reload (avoid config drift)

Exception: commission tier _values_ (not structure) may be hot-reloaded via a separate "commission-snapshot" config if
volatile.

## Checking an operation

```python
def route_instruction(instruction):
    cap = venue_capability_registry.get(instruction.target_venue)
    if not cap.supports(
        operation=instruction.action.op_enum,
        instrument_type=instruction.target_instrument_type,
    ):
        raise InstructionCapabilityMismatch(...)
    ...
```

## Testing

- Per-venue conformance: every declared operation must have a corresponding adapter implementation
- No undeclared operation callable
- Regional restrictions respected in pre-flight
- Collateral haircuts match documented values (sanity tests)
- Round-trip JSON serialization (for UI reference)

## UI exposure

Venue capability registry drives the "Venue Details" screen:

- Grid of operations supported per venue
- Collateral table
- Commission table
- Regional restrictions
- Child venues (for META_BROKER)

UI consumes auto-generated types from UAC (OpenAPI pipeline).

## Cross-references

- Venue registry reference: [/codex/02-venues/venue-registry-reference.md](/codex/02-venues/venue-registry-reference.md)
- Capital efficiency (consumes this registry):
  [/codex/04-architecture/capital-efficiency-patterns.md](/codex/04-architecture/capital-efficiency-patterns.md)
- Slow-fast routing split:
  [/codex/04-architecture/slow-fast-routing-split.md](/codex/04-architecture/slow-fast-routing-split.md)
- UAC Citadel layout: [/codex/02-data/contracts-scope-and-layout.md](/codex/02-data/contracts-scope-and-layout.md)
- Schema versioning: [/codex/04-architecture/schema-versioning.md](/codex/04-architecture/schema-versioning.md)

## Not in this doc

- **Venue data paths** — [/codex/02-data/venue-availability.md](/codex/02-data/venue-availability.md) for data shards
- **Per-venue adapter code** — execution-service/adapters/
- **Per-venue credentials** — Secret Manager
- **Dynamic venue health** — execution-service runtime
- **Pricing / odds feeds** — MTDS + respective data services
