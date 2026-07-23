---
doc_type: codex-ssot
title: UAC Registry Gaps — Additions for the Category × Instrument Coverage Matrix
summary: >-
  The 12 additive UAC declarations (ArchetypeCapabilityV2, supported_signal_variants, FlashLoanReceiverRegistry,
  LiquidationBonusScheduleV2, EventCalendarSourceCapability, RepresentativeFutureRegistry, StrategyAvailabilityRegistry,
  ...) proposed to unblock the BLOCKED/PARTIAL cells of the category x instrument coverage matrix — each with proposed
  shape, consumers, and PR phasing (A-F). Companion proposal to category-instrument-coverage.md (the SSOT).
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [deployment-service, execution-service, features-service, strategy-service, unified-api-contracts]
scope: [engineer, admin]
tags: [uac, strategy, defi, registry, execution, features, archetype, coverage-matrix]
related:
  [
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    cross-cutting/strategy-availability-and-locking.md,
    cross-cutting/futures-roll-and-combos.md,
  ]
created: 2026-04-20
authoritative_for: [UAC registry gap additions for the architecture-v2 category-instrument coverage matrix]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/block-list.md,
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/cross-cutting/futures-roll-and-combos.md,
    /codex/09-strategy/architecture-v2/cross-cutting/strategy-availability-and-locking.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3a-current-infra-audit.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3b-uac-combo-rules.md,
    /codex/16-strategy-playbooks/infra-spec/stage-3e-refactor-plan.md,
  ]
owner:
last_reviewed:
code_refs:
---

# UAC Registry Gaps — Additions for the Category × Instrument Coverage Matrix

> **Status:** Proposal as of 2026-04-19. Companion to
> [`category-instrument-coverage.md`](category-instrument-coverage.md) (the SSOT). Each section below is one additive
> UAC declaration — with proposed shape, rationale, consumers, and the cells it unblocks. Grouped together so a single
> UAC PR can land the whole set cohesively without churn.
>
> **Principle:** everything declared below lives in
> `unified-api-contracts/unified_api_contracts/registry/capability_declarations/` (matching the existing `_cefi.py`,
> `_defi.py`, `_tradfi.py`, `_sports.py` layout) and/or in `unified_api_contracts/internal/architecture_v2/` for
> archetype-facing metadata. All additions are Pydantic v2 `BaseModel` with
> `model_config = ConfigDict(frozen=True, extra="forbid")` unless declared as `StrEnum`.

---

## Summary table

| #   | Addition                                     | UAC module                                                                             | Primary consumers                                                                    | Unblocks (SSOT block-list refs)                                                                                                              |
| --- | -------------------------------------------- | -------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `ArchetypeCapabilityV2` registry             | `internal/architecture_v2/archetype_capability.py`                                     | strategy-service config validation, UI catalog                                       | cross-cutting; foundational                                                                                                                  |
| 2   | `supported_signal_variants` on VenueCap      | `internal/architecture_v2/venue_capability_v2.py`                                      | strategy-service, execution-service                                                  | BL partial cells on ARB/MM                                                                                                                   |
| 3   | `FlashLoanReceiverRegistry`                  | `registry/capability_declarations/_defi.py`                                            | execution-service DeFi connectors                                                    | ARB × DeFi × lp flash-loan                                                                                                                   |
| 4   | `LiquidationBonusScheduleV2`                 | `registry/capability_declarations/_defi.py`                                            | LIQUIDATION_CAPTURE engine, risk gates                                               | LIQUIDATION_CAPTURE precision                                                                                                                |
| 5   | `EventCalendarSourceCapability`              | `registry/capability_declarations/_altdata.py` (new area)                              | EVENT_DRIVEN engine, features-macro-service                                          | EVENT_DRIVEN across all cats                                                                                                                 |
| 6   | `IvSurfaceFidelity` + option-venue extension | `registry/capability_declarations/_cefi.py` / `_tradfi.py`                             | VOL_TRADING_OPTIONS, ARB × option                                                    | BL-1 (partial), option-vol cells                                                                                                             |
| 7   | `MultiLegOrderCapability`                    | `internal/architecture_v2/venue_capability_v2.py`                                      | execution-service, ATOMIC handler                                                    | Basket + Option MM + combos                                                                                                                  |
| 8   | `PricingFidelity` on DeFi spot venues        | `registry/capability_declarations/_defi.py`                                            | strategy-service price-feed validation                                               | ML × DeFi × spot                                                                                                                             |
| 9   | `LaySideExecutionSemantics`                  | `registry/capability_declarations/_sports.py`                                          | MARKET_MAKING_EVENT_SETTLED, execution-service                                       | MM-event-settled lay variants                                                                                                                |
| 10  | `CrossVenueRoutingPolicy`                    | `registry/capability_declarations/_tradfi.py`                                          | execution-service TradFi SOR                                                         | CARRY_BASIS_DATED × TradFi                                                                                                                   |
| 11  | `RepresentativeFutureRegistry` + event       | `internal/architecture_v2/representative_future.py` + `unified_trading_library.events` | features-service, representative-future-service, strategy-service, execution-service | BL-10 (dated-future auto-roll)                                                                                                               |
| 12  | `StrategyAvailabilityRegistry` + events      | `internal/architecture_v2/strategy_availability.py` + `unified_trading_library.events` | portfolio-allocator, strategy-service, UI (SaaS / IM / admin)                        | SaaS vs IM lock-state separation; [`cross-cutting/strategy-availability-and-locking.md`](cross-cutting/strategy-availability-and-locking.md) |

---

## 1. `ArchetypeCapabilityV2` — queryable archetype → (category, instrument) support map

**Path:** `unified_api_contracts/internal/architecture_v2/archetype_capability.py`

**Purpose:** Lift the coverage matrix out of markdown into a queryable registry. strategy-service uses it at deploy time
to reject configs that claim an unsupported `(archetype, category, instrument_type)` cell; UI uses it to render
`/coverage` without hand-maintained TS tables.

```python
from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Literal

from unified_api_contracts.internal.architecture_v2.enums import (
    StrategyArchetype,
    VenueCategoryV2,
)
from unified_api_contracts.canonical.domain.instruments import InstrumentType  # canonical enum


class CoverageStatus(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ArchetypeCoverageCell(BaseModel):
    """One cell of the (archetype × category × instrument) matrix."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    archetype: StrategyArchetype
    category: VenueCategoryV2
    instrument_type: InstrumentType
    status: CoverageStatus
    # Stable set of venue IDs (from VENUE_REGISTRY) that implement this cell.
    representative_venue_ids: tuple[str, ...]
    # One of: "price", "funding_rate", "basis", "iv_dispersion",
    # "vol_metric", "rate_spread", "liquidation_bonus", "odds",
    # "event_surprise", ...
    signal_variant: str
    # Free-form notes; MUST be non-empty when status != SUPPORTED.
    notes: str
    # References to block-list entries in category-instrument-coverage.md
    # (e.g., "BL-1", "BL-10") when status == BLOCKED; empty tuple otherwise.
    block_list_refs: tuple[str, ...] = ()


class ArchetypeCapabilityV2(BaseModel):
    """Full capability set for a single archetype."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    archetype: StrategyArchetype
    # All cells for the archetype, one per (category, instrument_type).
    cells: tuple[ArchetypeCoverageCell, ...]
    # Archetype is rolling-future-aware (subscribes to REPRESENTATIVE_FUTURE_CHANGED).
    uses_rolling_futures: bool = False


# The canonical map — one entry per StrategyArchetype value.
ARCHETYPE_CAPABILITY_V2: dict[StrategyArchetype, ArchetypeCapabilityV2] = {
    # Populated from category-instrument-coverage.md — codegen or hand-maintained
    # with a QG check that enforces every (archetype, category, instrument_type)
    # in the markdown matrix matches a cell here.
    ...
}


def coverage_for(
    archetype: StrategyArchetype,
    category: VenueCategoryV2,
    instrument_type: InstrumentType,
) -> ArchetypeCoverageCell | None:
    ...


def supported_combinations() -> Iterator[ArchetypeCoverageCell]:
    """All SUPPORTED cells across all archetypes — for UI /coverage rendering."""
    ...


def blocked_combinations() -> Iterator[ArchetypeCoverageCell]:
    """All BLOCKED cells with their block_list_refs — for UI /coverage/blocked."""
    ...
```

**Unblocks:** Every cell in the matrix. Foundational — #2, #8, #9 reference back to it.

**QG check:** `tests/test_archetype_capability_matrix_parity.py` parses
`/codex/09-strategy/architecture-v2/category-instrument-coverage.md` and asserts every row appears in
`ARCHETYPE_CAPABILITY_V2` with matching status. Markdown remains the narrative SSOT; Python mirrors it for runtime
queries.

---

## 2. `supported_signal_variants` on `VenueCapabilityV2`

**Path:** `unified_api_contracts/internal/architecture_v2/venue_capability_v2.py` (extend existing model)

**Purpose:** A venue can support `PERPETUAL` but that says nothing about whether we trade perp for price dispersion,
funding-rate dispersion, basis, or directional. Today this distinction lives in prose — strategy-service can't reject a
config that asks for funding-rate-arb on a venue that only supports price-based trading.

```python
class VenueCapabilityV2(BaseModel):
    ...  # existing fields

    # New field:
    # Maps instrument_type → list of signal variants the venue supports for that instrument.
    # Example:
    #   {
    #     "PERPETUAL": ("price", "funding_rate", "basis"),
    #     "SPOT_PAIR": ("price",),
    #     "OPTION": ("delta_as_expression", "iv_dispersion", "vol_metric"),
    #   }
    supported_signal_variants: dict[InstrumentType, tuple[str, ...]] = Field(default_factory=dict)
```

**Signal variant vocabulary:** must match `ArchetypeCoverageCell.signal_variant`. Stable registered list:

| Value                 | Meaning                                                 |
| --------------------- | ------------------------------------------------------- |
| `price`               | Spot or perp price, tick-level orderbook available      |
| `funding_rate`        | Perp funding rate tradeable (and measurable)            |
| `basis`               | Spot ↔ future / spot ↔ perp basis tradeable             |
| `iv_dispersion`       | Vol surface IV deltas between venues tradeable          |
| `vol_metric`          | IV vs RV, skew, term-structure                          |
| `rate_spread`         | Cross-venue lending rate spread                         |
| `liquidation_bonus`   | On-chain liquidator role active                         |
| `odds`                | Event-settled odds bid/ask                              |
| `event_surprise`      | Calendar events (macro / earnings / release) tradeable  |
| `delta_as_expression` | Option used to express directional view (not vol trade) |

**Unblocks:** SSOT `PARTIAL` cells on `ARBITRAGE_PRICE_DISPERSION × CeFi × perp`, `× option`; `CARRY_BASIS_PERP`
variants; strategy-service config validation against venue capability.

---

## 3. `FlashLoanReceiverRegistry` — per-chain deployed contract addresses

**Path:** `unified_api_contracts/registry/capability_declarations/_defi.py`

**Purpose:** `ARBITRAGE_PRICE_DISPERSION × DeFi × lp` flash-loan arb requires a deployed FlashLoanReceiver contract on
every target chain. Today the chain-to-address map is tracked ad-hoc in `deployment-service/contracts/` and
`unified-config-interface/testnet_contracts.py`. Strategy-service / execution connectors cannot safely validate
"flash-loan is supported on chain X" without a single authoritative registry.

```python
class FlashLoanProtocol(StrEnum):
    AAVE_V3 = "aave_v3"
    BALANCER_V2 = "balancer_v2"
    UNISWAP_V3_FLASH_SWAP = "uniswap_v3_flash_swap"


class FlashLoanReceiverDeployment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    chain: str  # ETHEREUM | ARBITRUM | OPTIMISM | POLYGON | BASE | AVALANCHE | SOLANA
    protocol: FlashLoanProtocol
    receiver_address: str  # checksum address for EVM, program ID for Solana
    deployment_commit_sha: str  # for auditability — matches deployment-service repo tag
    deployed_at_utc: str  # ISO 8601
    # Supported borrow tokens on this chain/protocol pair.
    supported_tokens: tuple[str, ...]


FLASH_LOAN_RECEIVER_REGISTRY: tuple[FlashLoanReceiverDeployment, ...] = (
    # e.g.,
    # FlashLoanReceiverDeployment(
    #     chain="ETHEREUM",
    #     protocol=FlashLoanProtocol.AAVE_V3,
    #     receiver_address="0x...",
    #     deployment_commit_sha="abc123",
    #     deployed_at_utc="2026-03-18T12:00:00Z",
    #     supported_tokens=("USDC", "WETH", "WBTC"),
    # ),
    ...
)


def flash_loan_receiver_for(
    chain: str,
    protocol: FlashLoanProtocol,
) -> FlashLoanReceiverDeployment | None: ...
```

**Unblocks:** `ARBITRAGE_PRICE_DISPERSION × DeFi × lp` flash-loan arb. Also needed by
`LIQUIDATION_CAPTURE × DeFi × lending` on chains where we liquidate via flash-loan.

**Integration:** `execution-service/execution_service/v2/defi/` connectors call
`flash_loan_receiver_for(chain, protocol)` at connect time — fail loud if not found (no silent fallback, per CLAUDE.md
rule).

---

## 4. `LiquidationBonusScheduleV2` — per-protocol per-collateral-token bonus schedules

**Path:** `unified_api_contracts/registry/capability_declarations/_defi.py`

**Purpose:** Aave V3 liquidation bonus != Compound V3 != Euler != Morpho — each has its own per-collateral-token bonus
schedule and close-factor rules. `LIQUIDATION_CAPTURE` computes edge net-of-gas using these schedules. Today they're
hardcoded in per-protocol modules under execution-service with no SSOT.

```python
class LiquidationProtocol(StrEnum):
    AAVE_V3 = "aave_v3"
    COMPOUND_V3 = "compound_v3"
    EULER = "euler"
    MORPHO = "morpho"
    KAMINO = "kamino"
    GMX_V2 = "gmx_v2"


class LiquidationBonusEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    protocol: LiquidationProtocol
    chain: str
    collateral_token: str   # WBTC | WETH | stETH | USDC | ...
    debt_token: str | None  # None means "any debt token"
    # Bonus as bps over debt repaid. Aave v3 WBTC example: 700 (7%).
    liquidation_bonus_bps: int
    # Fraction of debt that can be liquidated in a single tx; Aave v3 default 0.5.
    close_factor: float
    # Health-factor threshold below which liquidation is allowed (usually 1.0).
    health_factor_trigger: float = 1.0
    # Source reference for auditability.
    source_url: str  # e.g., Aave governance snapshot


LIQUIDATION_BONUS_SCHEDULE_V2: tuple[LiquidationBonusEntry, ...] = (...)


def liquidation_bonus_for(
    protocol: LiquidationProtocol,
    chain: str,
    collateral_token: str,
    debt_token: str | None = None,
) -> LiquidationBonusEntry | None: ...
```

**Unblocks:** `LIQUIDATION_CAPTURE` edge-calc precision across Aave, Compound, Euler, Morpho, Kamino. Also informs
`CARRY_RECURSIVE_STAKED` liquidation-risk modeling.

---

## 5. `EventCalendarSourceCapability` — declare external event sources

**Path:** `unified_api_contracts/registry/capability_declarations/_altdata.py` (extend)

**Purpose:** `EVENT_DRIVEN` strategies fire on scheduled external events: Bloomberg consensus macro releases,
TradingEconomics (open-source macro), TokenUnlocks.io (DeFi token unlocks), protocol-governance forums (Snapshot, Tally,
Aave governance), SharpAPI / SFI news feeds (sports). Today each source is referenced ad-hoc in different services. No
single declaration of "what events does source X cover?"

```python
class EventSourceType(StrEnum):
    MACRO_CONSENSUS = "macro_consensus"      # Bloomberg, TradingEconomics
    EARNINGS_CALENDAR = "earnings_calendar"  # Bloomberg, Refinitiv
    TOKEN_UNLOCKS = "token_unlocks"          # TokenUnlocks.io
    PROTOCOL_GOVERNANCE = "protocol_governance"  # Snapshot, Tally
    SLASHING_FEED = "slashing_feed"          # Lido oracle
    SPORTS_NEWS = "sports_news"              # SharpAPI, SFI


class EventCategory(StrEnum):
    MACRO_RELEASE = "macro_release"          # NFP, CPI, FOMC
    EARNINGS = "earnings"                    # AAPL Q4
    TOKEN_UNLOCK = "token_unlock"            # ARB unlock 2026-03-16
    GOVERNANCE_VOTE = "governance_vote"      # Aave rate-update vote
    SLASHING_EVENT = "slashing_event"
    SPORTS_LINEUP_RELEASE = "sports_lineup_release"
    SPORTS_INJURY_NEWS = "sports_injury_news"


class EventCalendarSource(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    source_id: str                    # "bloomberg_macro" | "token_unlocks_io" | ...
    source_type: EventSourceType
    covered_categories: tuple[EventCategory, ...]
    # Markets the source covers (for macro: country ISO codes; for earnings:
    # exchange IDs; for tokens: chain + token symbol; for sports: league IDs).
    covered_markets: tuple[str, ...]
    ingestion_latency_sla_seconds: int  # p95 from event → our system
    data_freshness_ref: str            # features-service data-freshness key
    api_auth_model: Literal["api_key", "oauth", "public"]


EVENT_CALENDAR_SOURCES: tuple[EventCalendarSource, ...] = (...)
```

**Unblocks:** All `EVENT_DRIVEN` cells — promotes from PARTIAL to SUPPORTED once a source is declared for the target
category.

---

## 6. `IvSurfaceFidelity` + option-venue extension

**Path:** `unified_api_contracts/registry/capability_declarations/_cefi.py` + `_tradfi.py`

**Purpose:** `VOL_TRADING_OPTIONS` and `ARBITRAGE_PRICE_DISPERSION × option` need to know how rich the vol surface data
is per option venue. Deribit has full surface (all strikes × all expiries with live IVs); OKX has a more limited
surface; CME options on futures are shallower still. Strategies should query this before committing to a vol-surface
model.

```python
class IvSurfaceFidelity(StrEnum):
    FULL_SURFACE = "full_surface"     # all strikes × expiries, tick-level
    ATM_ONLY = "atm_only"             # only near-ATM strikes with IV
    COARSE_GRID = "coarse_grid"       # sparse strikes, daily snapshot
    NONE = "none"                     # price only, no IV surface


class OptionVenueCapability(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    venue_id: str
    underlyings: tuple[str, ...]       # "BTC", "ETH", "SPY", "QQQ", "VIX", "ES", ...
    iv_surface_fidelity: IvSurfaceFidelity
    # How many strikes per expiry on average.
    strikes_per_expiry_p50: int
    # Expiry term structure available.
    expiries_per_underlying_p50: int
    supports_multi_leg_combos: bool
    max_combo_legs: int  # 0 if not supported
    # Supported option signal variants (from #2 vocabulary).
    supported_signal_variants: tuple[str, ...]


OPTION_VENUE_CAPABILITIES: tuple[OptionVenueCapability, ...] = (
    # Deribit — full surface, 4 legs
    # OKX options — partial surface, 4 legs
    # CBOE via IBKR — full surface on SPY/QQQ/VIX, 4 legs
    # CME options on futures — partial, 2 legs
    ...
)
```

**Unblocks:** `VOL_TRADING_OPTIONS × TradFi × option` (CME options-on-futures declaration),
`ARBITRAGE_PRICE_DISPERSION × option` (same), `MARKET_MAKING_CONTINUOUS × CeFi × option`.

---

## 7. `MultiLegOrderCapability`

**Path:** `unified_api_contracts/internal/architecture_v2/venue_capability_v2.py` (extend `VenueCapabilityV2`)

**Purpose:** Option MM, `STAT_ARB_CROSS_SECTIONAL` baskets, ATOMIC multi-leg bundles, and **calendar-spread combo
tickers for dated-future rolls** all need to know per-venue whether multi-leg is supported and the max legs allowed.

```python
class MultiLegOrderCapability(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    supports_listed_combos: bool       # venue-listed combo tickers (e.g., CME calendar spreads)
    supports_synthetic_combos: bool    # venue accepts multi-leg orders as single ATOMIC submission
    max_legs: int                      # 0 if no multi-leg support
    # Which combo types are supported as listed tickers.
    listed_combo_types: tuple[str, ...]  # "calendar_spread" | "butterfly" | "risk_reversal" | ...
    # Minimum time in ms between leg submissions for LEADER_HEDGE fallback
    # when synthetic combos aren't accepted atomically.
    leader_hedge_min_interval_ms: int = 0
```

Added to `VenueCapabilityV2`:

```python
class VenueCapabilityV2(BaseModel):
    ...
    multi_leg_order_capability: MultiLegOrderCapability | None = None
```

**Unblocks:** `VOL_TRADING_OPTIONS` (multi-leg straddles/butterflies), `MARKET_MAKING_CONTINUOUS × option`,
`STAT_ARB_CROSS_SECTIONAL` (batch orders), **BL-10 futures roll combo creation on CME / Deribit**.

---

## 8. `PricingFidelity` on DeFi spot venues

**Path:** `unified_api_contracts/registry/capability_declarations/_defi.py`

**Purpose:** `ML_DIRECTIONAL_CONTINUOUS × DeFi × spot` and `RULES_DIRECTIONAL_CONTINUOUS × DeFi × spot` both claim
SUPPORTED but are actually PARTIAL because Uniswap V3 pricing fidelity on thin pairs is not tick-level. Strategies need
to know if a spot DEX offers tick streams (usable for ML) or snapshot pricing (not usable).

```python
class PricingFidelity(StrEnum):
    TICK_STREAM = "tick_stream"      # continuous orderbook / AMM event stream; <100ms staleness
    SNAPSHOT = "snapshot"            # periodic polls; 1-60s staleness
    DERIVED_TWAP = "derived_twap"    # Uniswap V3 TWAP oracle only — lagging
    NONE = "none"                    # no reliable price feed


# Added to DeFi spot venue capability:
class DefiSpotVenueCapability(BaseModel):
    ...  # existing fields
    pricing_fidelity: PricingFidelity
    tick_stream_source: str | None  # "subgraph_events" | "websocket" | None
    pool_tvl_usd_min_for_fidelity: int  # minimum pool TVL for stated fidelity
```

**Unblocks:** Promotes `ML_DIRECTIONAL_CONTINUOUS × DeFi × spot` PARTIAL → SUPPORTED on declared tick-stream pools.

---

## 9. `LaySideExecutionSemantics` per sports/prediction venue

**Path:** `unified_api_contracts/registry/capability_declarations/_sports.py`

**Purpose:** `MARKET_MAKING_EVENT_SETTLED` needs per-venue semantics for lay-side bets:

- Betfair direct: bankroll-as-collateral, lay liability = (odds - 1) × stake, fully collateralized.
- Smarkets: same-ish, but with different commission timing (on winnings vs on turnover).
- Matchbook direct: different margin rules.
- Polymarket: no "lay" — only buy/sell binary Yes/No (so MM is CLOB-style).
- Unity: no quoting at all (Feed Connector is place-only).

Today these differences are buried in adapter code. Execution-service can't validate per-venue lay policy without a
declaration.

```python
class LayBookType(StrEnum):
    FULL_LAY = "full_lay"                    # Betfair-style lay with liability
    BINARY_CLOB = "binary_clob"              # Polymarket-style Yes/No CLOB
    BACK_ONLY = "back_only"                  # Unity child books (no lay on our side)
    EXCHANGE_LAY_NO_COMMISSION_ON_TURNOVER = "exchange_lay_no_commission_on_turnover"
    EXCHANGE_LAY_COMMISSION_ON_WIN_ONLY = "exchange_lay_commission_on_win_only"


class LaySideExecutionSemantics(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    venue_id: str
    lay_book_type: LayBookType
    # Can MM quote (add back + lay quotes to book)?
    supports_mm_quoting: bool
    # Liability multiplier: lay_liability = multiplier(odds, stake)
    # For Betfair-style: (odds - 1) * stake. For binary CLOB: fixed notional.
    liability_formula_ref: str  # name of registered formula
    # Commission charged on... winnings, turnover, or none.
    commission_basis: Literal["winnings", "turnover", "none"]
    min_quote_refresh_ms: int
    # What happens when market turns in-play: lock / soft-lock / free.
    in_play_policy: Literal["lock_new_quotes", "soft_lock", "unrestricted"]


LAY_SIDE_EXECUTION_SEMANTICS: tuple[LaySideExecutionSemantics, ...] = (...)
```

**Unblocks:** `MARKET_MAKING_EVENT_SETTLED` across Betfair / Smarkets / Matchbook / Polymarket with clear per-venue
semantics; validates that Unity MM slot is BLOCKED at config time (BL-6).

---

## 10. `CrossVenueRoutingPolicy` for TradFi

**Path:** `unified_api_contracts/registry/capability_declarations/_tradfi.py`

**Purpose:** `CARRY_BASIS_DATED × TradFi` pairs a spot ETF (IBKR) with an index future (CME). Execution-service needs to
know the cross-venue routing + settlement-currency bridge policy for legs.
`ARBITRAGE_PRICE_DISPERSION × TradFi × dated_future` needs calendar-spread cross-product routing (CME ES vs ICE Brent).

```python
class CrossVenueLegRole(StrEnum):
    SPOT_LEG = "spot_leg"
    FUTURE_LEG = "future_leg"
    OPTION_LEG = "option_leg"


class CrossVenueRoutingPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    policy_id: str
    # Origin and destination venues.
    leg_venues: tuple[str, ...]  # ("IBKR", "CME")
    # Leg roles in order.
    leg_roles: tuple[CrossVenueLegRole, ...]
    # Settlement currency reconciliation — needed for basis calculation.
    settlement_currency: str
    # Acceptable spread pre-trade (bps over synthetic fair value).
    max_execution_spread_bps: int
    # Typical latency between leg execution.
    leg_latency_p50_ms: int


CROSS_VENUE_ROUTING_POLICIES: tuple[CrossVenueRoutingPolicy, ...] = (
    # e.g. IBKR SPY ↔ CME ES index basis
    # e.g. IBKR QQQ ↔ CME NQ
    # e.g. ICE Brent ↔ CME WTI cross-product spread
    ...
)
```

**Unblocks:** `CARRY_BASIS_DATED × TradFi × (spot + dated_future)` from PARTIAL → SUPPORTED.
`ARBITRAGE_PRICE_DISPERSION × TradFi × dated_future` cross-product cells.

---

## 11. `RepresentativeFutureRegistry` + `REPRESENTATIVE_FUTURE_CHANGED` event

**Paths:**

- Registry: `unified_api_contracts/internal/architecture_v2/representative_future.py`
- Event schema: `unified_trading_library/events/event_types.py` +
  `unified_api_contracts/internal/architecture_v2/events.py`

**Purpose:** Under-pins the
[dated-future rolls mechanism](category-instrument-coverage.md#dated-future-rolls-and-representative-futures) (BL-10).
Declares the set of underlyings, the feature group that feeds the liquidity measure, and the roll-trigger policy per
underlying.

```python
# unified_api_contracts/internal/architecture_v2/representative_future.py

class UnderlyingCategory(StrEnum):
    CRYPTO_DATED = "crypto_dated"     # Deribit BTC/ETH dated futures
    EQUITY_INDEX = "equity_index"     # CME ES, NQ, RTY, YM
    COMMODITY = "commodity"           # CME CL, GC, NG, HG; ICE Brent
    FX = "fx"                         # CME 6E, 6B, 6J


class RollTriggerPolicy(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    # Feature group that provides per-contract liquidity measure.
    # Must publish at least: open_interest, volume_24h, bid_ask_depth_notional.
    liquidity_feature_group_ref: str
    # Policy: roll when next contract's rolling liquidity exceeds current's
    # by this margin for at least N consecutive measurement windows.
    liquidity_margin_bps: int            # e.g. 1000 = 10%
    liquidity_confirmation_windows: int  # e.g. 3 windows of 1h each
    # Don't roll within N days of current contract's expiry if it still has
    # higher liquidity (prevents thrashing as contract decays).
    expiry_buffer_days: int = 2


class UnderlyingDeclaration(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    underlying_id: str               # "BTC-USD-DERIBIT-DATED", "ES-USD-CME", ...
    category: UnderlyingCategory
    venue_id: str                    # "deribit" | "cme" | "ice"
    base_symbol: str                 # "BTC" | "ES" | "BRENT"
    quote_currency: str              # "USD" | "USDT"
    contract_code_format: str        # regex or strftime-like template for contract codes
    roll_policy: RollTriggerPolicy
    # Does the venue list calendar-spread combo tickers for rolls on this underlying?
    has_listed_calendar_combo: bool
    # If not listed, max permissible synthesize-combo slippage for ATOMIC fallback.
    max_roll_slippage_bps: int = 15
    # Circuit-breaker parameters.
    feed_staleness_soft_freeze_seconds: int = 60
    consecutive_failure_escalation_threshold: int = 3


REPRESENTATIVE_FUTURE_REGISTRY: tuple[UnderlyingDeclaration, ...] = (
    # e.g., UnderlyingDeclaration(
    #     underlying_id="BTC-USD-DERIBIT-DATED",
    #     category=UnderlyingCategory.CRYPTO_DATED,
    #     venue_id="deribit",
    #     base_symbol="BTC",
    #     quote_currency="USD",
    #     contract_code_format=r"BTC-\d+[A-Z]{3}\d+",
    #     roll_policy=RollTriggerPolicy(
    #         liquidity_feature_group_ref="deribit-dated-liquidity@v1",
    #         liquidity_margin_bps=1000,
    #         liquidity_confirmation_windows=3,
    #         expiry_buffer_days=2,
    #     ),
    #     has_listed_calendar_combo=True,
    #     max_roll_slippage_bps=20,
    # ),
    ...
)


def underlying_declaration_for(underlying_id: str) -> UnderlyingDeclaration | None: ...


def underlyings_by_venue(venue_id: str) -> tuple[UnderlyingDeclaration, ...]: ...
```

Event schema (paired — event contract lives in UAC, constant name in UTL for import):

```python
# unified_api_contracts/internal/architecture_v2/events.py

class RepresentativeFutureChangedEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_type: Literal["REPRESENTATIVE_FUTURE_CHANGED"] = "REPRESENTATIVE_FUTURE_CHANGED"
    underlying_id: str
    prior_contract: str           # specific contract code, e.g. "BTC-26DEC25"
    new_contract: str             # e.g. "BTC-27MAR26"
    decision_features: dict[str, float]  # snapshot of liquidity features driving the decision
    decision_at_utc: str          # ISO 8601
    policy_content_hash: str      # hash of the active RollTriggerPolicy
    # Correlation ID for tracing downstream FUTURES_ROLL instructions.
    correlation_id: str
```

```python
# unified_trading_library/events/event_types.py (addition)

REPRESENTATIVE_FUTURE_CHANGED = "REPRESENTATIVE_FUTURE_CHANGED"
FUTURES_ROLL_FAILED = "FUTURES_ROLL_FAILED"
```

**Unblocks:** BL-10 — all `-dated-` rolling slots become SUPPORTED once the registry is populated, the
representative-future-service is scaffolded, and the event contract is published via Pub/Sub. See
[`cross-cutting/futures-roll-and-combos.md`](cross-cutting/futures-roll-and-combos.md) for the full service spec.

---

## 12. `StrategyAvailabilityRegistry` — SaaS / IM / client-exclusive lock state

**Paths:**

- Registry: `unified_api_contracts/internal/architecture_v2/strategy_availability.py`
- Events: `unified_trading_library/events/event_types.py` + `unified_api_contracts/internal/architecture_v2/events.py`

**Purpose:** The Unified Trading System powers **one** combinatoric strategy universe that serves both the DIY
Strategy-as-a-Service business and the Investment Management (fund) business. The separation is metadata — a per-slot
lock state — not code-path duplication. This registry is the SSOT for which slots are `PUBLIC` (DIY-visible) vs
`INVESTMENT_MANAGEMENT_RESERVED` (IM-only) vs `CLIENT_EXCLUSIVE` (specific client contract) vs `RETIRED`.

Full principle + UI surfaces:
[`cross-cutting/strategy-availability-and-locking.md`](cross-cutting/strategy-availability-and-locking.md).

```python
# unified_api_contracts/internal/architecture_v2/strategy_availability.py

class StrategyAvailabilityState(StrEnum):
    PUBLIC = "PUBLIC"
    INVESTMENT_MANAGEMENT_RESERVED = "INVESTMENT_MANAGEMENT_RESERVED"
    CLIENT_EXCLUSIVE = "CLIENT_EXCLUSIVE"
    RETIRED = "RETIRED"


class StrategyAvailabilityEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    slot_label: str                      # fully-spelled ARCHETYPE@venue-...-env
    state: StrategyAvailabilityState
    exclusive_client_id: str | None      # set when state == CLIENT_EXCLUSIVE
    reserving_business_unit_id: str | None  # set when state == INVESTMENT_MANAGEMENT_RESERVED
    changed_at_utc: str                  # ISO 8601 of most recent transition
    reason: str
    expires_at_utc: str | None           # time-bounded locks
    base_slot_label: str | None          # for v{N} locked variants derived from PUBLIC base


STRATEGY_AVAILABILITY_REGISTRY: tuple[StrategyAvailabilityEntry, ...] = (...)


def availability_for(slot_label: str) -> StrategyAvailabilityEntry:
    """Default PUBLIC if unregistered."""
    ...


def slots_visible_to(
    actor: Literal["admin", "im_desk", "saas", "client"],
    client_id: str | None = None,
) -> Iterator[str]:
    """Yields slot_labels the actor is authorised to see given their role."""
    ...


def validate_allocation_authorised(
    slot_label: str,
    client_id: str,
    business_unit: Literal["saas", "im_desk", "admin"],
) -> None:
    """Called from portfolio-allocator on every AllocationDirective reception.
    Raises StrategyNotAvailableError if the (client, business_unit) cannot allocate to this slot.
    """
    ...
```

Events (UAC schema + UTL constants):

```python
# UTL additions
STRATEGY_AVAILABILITY_CHANGED = "STRATEGY_AVAILABILITY_CHANGED"
STRATEGY_LOCKED = "STRATEGY_LOCKED"
STRATEGY_UNLOCKED = "STRATEGY_UNLOCKED"


# UAC events schema
class StrategyAvailabilityChangedEvent(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    event_type: Literal["STRATEGY_AVAILABILITY_CHANGED"] = "STRATEGY_AVAILABILITY_CHANGED"
    slot_label: str
    prior_state: StrategyAvailabilityState
    new_state: StrategyAvailabilityState
    prior_exclusive_client_id: str | None
    new_exclusive_client_id: str | None
    reason: str
    actor_id: str
    changed_at_utc: str
    correlation_id: str
```

**Unblocks:** Entire SaaS-vs-IM visibility split + bespoke-client exclusivity + admin audit trail. Feeds UI surfaces
`/coverage` (admin master view), `/services/research/strategy/families` (SaaS-filtered),
`/investment-management/catalog` (IM view), and `/admin/strategy-lock` (operator tool).

**Integration points:**

- `portfolio-allocator` calls `validate_allocation_authorised()` on every `AllocationDirective`.
- `strategy-service` filters strategy registration at startup by audience (SaaS instance never registers an
  `IM_RESERVED` slot).
- UI reads `slots_visible_to()` per logged-in user's role + client_id.

**QG check:** `tests/test_strategy_availability_registry.py` — asserts every slot label present in the SSOT matrix is
addressable (default PUBLIC) and that state transitions emit the canonical events.

---

## Implementation Phasing

All 11 additions are additive — no existing consumer breaks. Recommended PR order:

| PR  | Additions  | Rationale                                                            |
| --- | ---------- | -------------------------------------------------------------------- |
| A   | #1, #2, #7 | Foundation for strategy-service config validation + venue capability |
| B   | #11        | Representative future registry + event contract — unblocks BL-10     |
| C   | #3, #4, #8 | DeFi gaps                                                            |
| D   | #6, #9     | Option + sports lay gaps                                             |
| E   | #5, #10    | Event calendar + cross-venue TradFi routing                          |
| F   | #12        | Strategy availability / lock-state registry — SaaS vs IM separation  |

Each PR ships with:

- `tests/test_<addition>_parity.py` — markdown ↔ python matrix parity check for #1, #8, etc.
- Downstream consumer updates (strategy-service config validation, execution-service adapter validation, UI TS mirror
  regenerated via `scripts/generate_ui_reference_data.py`).
- Version bump on `unified-api-contracts` per the semver-agent conventional-commit rules.

## Cross-references

- SSOT: [`category-instrument-coverage.md`](category-instrument-coverage.md)
- Dated-future rolls spec (for #11):
  [`cross-cutting/futures-roll-and-combos.md`](cross-cutting/futures-roll-and-combos.md)
- UAC Citadel import rules: services import via `unified_api_contracts.{domain}` facades only — never `canonical.*` or
  `normalize_utils.*`.
