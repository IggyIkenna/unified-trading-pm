---
doc_type: codex-ssot
title: Strategy Availability and Locking (Cross-Cutting)
summary:
  "One combinatoric strategy universe powers both the SaaS (DIY client) and Investment-Management (fund) businesses via
  a per-slot `availability_state` (PUBLIC / INVESTMENT_MANAGEMENT_RESERVED / CLIENT_EXCLUSIVE / RETIRED) — the split is
  visibility + RBAC + lock state, not code-path duplication; allocation is authorised at `AllocationDirective`
  reception."
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service, unified-trading-system-ui]
scope: [engineer, admin]
tags: [strategy, availability, registry, uac, ui, rbac]

  [
    ../category-instrument-coverage.md,
    ../uac-registry-gaps.md,
    /codex/09-strategy/architecture-v2/cross-cutting/capital-client-isolation.md,
    /codex/09-strategy/architecture-v2/cross-cutting/portfolio-allocator.md,
    ../../../14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md,
  ]
created: 2026-04-20
authoritative_for:
  [
    strategy availability lock-state model (4-state PUBLIC/IM_RESERVED/CLIENT_EXCLUSIVE/RETIRED + RBAC allocation
    authorisation across one SaaS/IM universe),
  ]
referenced_by:
  [
    /codex/09-strategy/architecture-v2/category-instrument-coverage.md,
    /codex/09-strategy/architecture-v2/uac-registry-gaps.md,
    /codex/14-customer-journeys/_ssot-rules/03-same-system-principle.md,
    /codex/14-customer-journeys/_ssot-rules/06-show-dont-show-discipline.md,
    /codex/14-customer-journeys/experience/dart-briefing.md,
    /codex/14-customer-journeys/glossary.md,
    /codex/14-customer-journeys/playbook-concepts/catalogue-strategy.md,
    /codex/14-customer-journeys/shared-core/same-system-principle.md,
  ]
owner:
last_reviewed:
code_refs:
---

# Strategy Availability and Locking (Cross-Cutting)

> **Status:** Canonical as of 2026-04-19. SSOT for how the single combinatoric strategy universe powers **both** the
> Strategy-as-a-Service (SaaS, DIY client) business **and** the Investment Management (IM, fund) business without
> code-path duplication. The difference between the two businesses is **visibility + RBAC + lock state**, not different
> code.
>
> **Companion docs:** [`../category-instrument-coverage.md`](../category-instrument-coverage.md) (the universe);
> [`../uac-registry-gaps.md`](../uac-registry-gaps.md) (runtime registry — gap #12 added here);
> [`capital-client-isolation.md`](capital-client-isolation.md) (per-client capital).

---

## The principle

**There is ONE combinatoric strategy universe.** Every possible
`(family, archetype, category, instrument_type, venue_scope, instrument_scope, share_class)` slot is defined by the SSOT
matrix. This universe powers:

1. **Strategy-as-a-Service (SaaS) — DIY clients.** A client logs in, browses the catalogue, and allocates capital to one
   or more strategies. They see the available slots + can build variant instances (parameterised configs).
2. **Investment Management (IM) — our own funds.** Our investment management desk runs strategies for firm-managed
   capital (sometimes pooled investor subscriptions in fund mode). They see the **same** universe.

The separation is not "two strategy systems". It is **one system with an availability axis**. Each slot carries a lock
state that determines which audience sees it and who can allocate.

> **This is important to document** because we get questions from clients, investors, and investment-management
> stakeholders about how we run our own fund and also sell strategies to clients. Short answer: we don't fork the code;
> we lock specific slot instances. The same `ML_DIRECTIONAL_CONTINUOUS@hyperliquid-btc-perp-5m-usdt-prod` engine runs
> whether IM is operating it or a DIY client is.

## Four lock states

Every strategy **slot instance** (instance-level identity — slot label + client_id) carries an `availability_state`. It
defaults to `PUBLIC` and transitions via explicit admin action.

| State                            | Who sees it                            | Who can allocate               | When to set                                                                         |
| -------------------------------- | -------------------------------------- | ------------------------------ | ----------------------------------------------------------------------------------- |
| `PUBLIC`                         | SaaS catalog + IM desk + Admin         | Any DIY client + IM desk       | Default — nothing bespoke yet                                                       |
| `INVESTMENT_MANAGEMENT_RESERVED` | IM desk + Admin                        | IM desk only                   | IM desk adopts for a fund; we don't want DIY clients piling onto the same slot      |
| `CLIENT_EXCLUSIVE`               | IM desk (read-only) + Admin + Client X | Client X only (IM may observe) | Bespoke client contract signed, client's strategy is locked to them during the term |
| `RETIRED`                        | Admin only (in historical view)        | Nobody                         | Strategy no longer offered; migration destination marked                            |

> `INVESTMENT_MANAGEMENT_RESERVED` and `CLIENT_EXCLUSIVE` are **not mutually exclusive with IM visibility**. When a slot
> is client-exclusive, IM can still see and read it (for risk oversight and to avoid duplicating capital into the same
> slot via a different wrapper), but they cannot allocate new capital. IM reservation is typically about preventing DIY
> clients from piling on rather than preventing internal overlap.

Some bespoke contracts allow the off-the-shelf version to remain PUBLIC ("client wants a custom variant, but the vanilla
flavour stays available to other clients"). In that case we create a **new slot instance version** (new `slot_label`
with `v{N}` suffix) and the new instance is `CLIENT_EXCLUSIVE`; the base `PUBLIC` slot keeps running.

## Actors and their surfaces

### Admin / operator

Sees the full universe with all states. Can toggle lock state, review lock transitions, audit who did what.

**UI surface:** `/admin/strategy-lock` (new) + `/coverage` (full master matrix with lock-state overlay).

### SaaS (DIY client)

Sees only `PUBLIC` slots (and any `CLIENT_EXCLUSIVE` slots where they are the bound client). Allocates capital, picks
share classes, builds configured variants within the slot.

**UI surface:**

- [`/services/research/strategy/families`](<../../../../unified-trading-system-ui/app/(platform)/services/research/strategy/families/page.tsx>)
  — family landing; lists archetypes
- `/services/research/strategy/families/[family]` — archetype cards; DIY-filtered
- [`/services/research/strategy/catalog`](<../../../../unified-trading-system-ui/app/(platform)/services/research/strategy/catalog/page.tsx>)
  — slot-instance catalog; DIY-filtered
- `/services/research/strategy/catalog/[strategyId]` — slot detail + allocate action

### Investment Management

Sees the full universe (all lock states). Can operate on `PUBLIC` and `INVESTMENT_MANAGEMENT_RESERVED`. Can see
`CLIENT_EXCLUSIVE` read-only.

**UI surface:** `/investment-management/catalog` (new landing) + overlays on `/coverage`.

## Why this architecture

- **Zero code-path duplication.** `V2EngineOrchestrator` runs the same way; the engine doesn't know about lock states.
  Lock state is pure metadata checked at allocation time (`AllocationDirective` rejects if client isn't authorised for
  that slot's state).
- **One catalogue, many views.** The master `/coverage` matrix is the source-of-truth; audience-specific pages filter by
  audience + lock state.
- **Hundreds of funds without affecting SaaS.** IM can run as many bespoke fund variants as they want — each is a
  slot-version + `INVESTMENT_MANAGEMENT_RESERVED` label. SaaS catalogue stays clean.
- **Reversible.** `CLIENT_EXCLUSIVE` → `PUBLIC` at contract end. `INVESTMENT_MANAGEMENT_RESERVED` → `PUBLIC` at fund
  wind-down. Clean transitions without re-engineering.
- **Regulatory umbrella orthogonality.** Regulation applies equally to both sides (same custody models, same risk
  controls — see [`../../README.md#regulatory-quick-reference-by-strategy-family--asset-group`](../README.md)). Lock
  state is a business axis, not a regulatory axis.

## Strategy combinatorics — bounded growth, unbounded diversity

Because lock state is metadata, we can sustainably grow the IM business without either:

- **Running out of strategies** — the combinatoric universe is ~240 near-term slots growing to ~300-350 at
  venue-coverage ceiling.
- **Cannibalising SaaS** — each IM-reserved slot removes one line from the SaaS catalogue but adds hundreds of unchanged
  lines remain available. SaaS clients never "notice" normal IM reservations.

When demand requires differentiation (e.g., IM and a bespoke client both want the same strategy shape with different
risk parameters), we mint **new slot versions** with the `v{N}` suffix — each version has its own independent lock
state. One physical strategy family, many versioned slots, each with its own audience.

## Data model

### UAC registry (companion gap — see `uac-registry-gaps.md` #12 below)

```python
from pydantic import BaseModel, ConfigDict
from enum import StrEnum

class StrategyAvailabilityState(StrEnum):
    PUBLIC = "PUBLIC"
    INVESTMENT_MANAGEMENT_RESERVED = "INVESTMENT_MANAGEMENT_RESERVED"
    CLIENT_EXCLUSIVE = "CLIENT_EXCLUSIVE"
    RETIRED = "RETIRED"


class StrategyAvailabilityEntry(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    slot_label: str                      # fully-spelled ARCHETYPE@venue-...-env
    state: StrategyAvailabilityState
    # Non-empty when state is CLIENT_EXCLUSIVE. One client_id per exclusive slot.
    exclusive_client_id: str | None
    # Non-empty for INVESTMENT_MANAGEMENT_RESERVED; the fund or internal book that adopted it.
    reserving_business_unit_id: str | None
    # ISO 8601 timestamp of the most recent state transition.
    changed_at_utc: str
    # Reason for the lock (e.g., "bespoke contract with X", "fund Y adopted", ...).
    reason: str
    # For time-bounded locks — when the lock is expected to revert. None for open-ended.
    expires_at_utc: str | None
    # Optional base slot this one derives from; used when we mint v{N}+1 while keeping the base PUBLIC.
    base_slot_label: str | None


STRATEGY_AVAILABILITY_REGISTRY: tuple[StrategyAvailabilityEntry, ...] = (...)


def availability_for(slot_label: str) -> StrategyAvailabilityEntry:
    """Default is PUBLIC if not explicitly registered."""
    ...


def slots_visible_to(actor: Literal["admin", "im_desk", "saas", "client"], client_id: str | None = None) -> Iterator[str]:
    """Yields slot_labels the actor can see given their role + optional client_id."""
    ...
```

### Events (UTL)

Lock transitions emit canonical lifecycle events:

```python
# unified_trading_library/events/event_types.py — additions
STRATEGY_AVAILABILITY_CHANGED = "STRATEGY_AVAILABILITY_CHANGED"
STRATEGY_LOCKED = "STRATEGY_LOCKED"
STRATEGY_UNLOCKED = "STRATEGY_UNLOCKED"
```

Payload (event schema in UAC):

```python
class StrategyAvailabilityChangedEvent(BaseModel):
    slot_label: str
    prior_state: StrategyAvailabilityState
    new_state: StrategyAvailabilityState
    prior_exclusive_client_id: str | None
    new_exclusive_client_id: str | None
    reason: str
    actor_id: str                        # who made the change
    changed_at_utc: str
    correlation_id: str
```

Every transition emits via UTL `log_event`. Audit ledger auto-built by subscribing to these.

### RBAC enforcement

Allocation path checks at `AllocationDirective` reception:

```python
def validate_allocation_authorised(
    slot_label: str,
    client_id: str,
    business_unit: Literal["saas", "im_desk", "admin"],
) -> None:
    entry = availability_for(slot_label)
    if entry.state == StrategyAvailabilityState.RETIRED:
        raise StrategyRetiredError(slot_label)
    if entry.state == StrategyAvailabilityState.INVESTMENT_MANAGEMENT_RESERVED and business_unit != "im_desk":
        raise StrategyNotAvailableError(slot_label, reason="IM-reserved")
    if entry.state == StrategyAvailabilityState.CLIENT_EXCLUSIVE:
        if business_unit == "im_desk":
            return  # IM can observe; allocation still rejected downstream if no read-only clause
        if client_id != entry.exclusive_client_id:
            raise StrategyNotAvailableError(slot_label, reason="client-exclusive")
    # PUBLIC — anyone allocates.
```

Called from portfolio-allocator + strategy-service on any new allocation.

## UI specifics

### `/coverage` (admin master matrix)

Each cell in the `(archetype × category × instrument_type)` matrix shows:

- Status badge (SUPPORTED / PARTIAL / BLOCKED / N/A)
- **Lock state overlay** — coloured border/ribbon per `availability_state`:
  - PUBLIC — no overlay (default)
  - IM_RESERVED — blue ribbon
  - CLIENT_EXCLUSIVE — amber ribbon with client_id tooltip
  - RETIRED — grey strike-through
- Click cell → side panel shows per-slot-label list; each slot has its own lock-state badge + who-holds-it info.
- Admin action buttons: "Lock for IM", "Lock for Client X", "Unlock", "Retire".

### `/services/research/strategy/families` (SaaS path)

Filter: only `PUBLIC` slots + `CLIENT_EXCLUSIVE` where viewer is the bound client. Catalogue looks smaller than master
matrix; this is expected. A "More?" button opens a contact-sales form — "Investment Management team offers additional
strategies not in this public catalogue."

### `/investment-management/catalog` (IM landing — new)

Shows full universe. Per-slot view reveals:

- Availability state
- Who's using it (PUBLIC/IM_RESERVED/CLIENT_EXCLUSIVE_CLIENT_X)
- Live P&L for slots IM is operating
- Ability to request `INVESTMENT_MANAGEMENT_RESERVED` for new slots

### `/coverage/by-combination` (admin — leg-picker)

The "show me all perp-to-perp arb" surface — see
[`../category-instrument-coverage.md`](../category-instrument-coverage.md). Lock-state overlay applies same as
`/coverage`.

### Badge vocabulary

Reusable components ([`components/architecture-v2/`](../../../../unified-trading-system-ui/components/architecture-v2)):

```tsx
<StatusBadge status="SUPPORTED" />
<LockStateBadge state="CLIENT_EXCLUSIVE" clientId="firm-x" />
<RollModeBadge rollMode="rolling" />
<CategoryChip category="CEFI" />
<InstrumentTypeChip instrumentType="perp" />
<SignalVariantBadge variant="funding_rate" />
```

Used on all of `/coverage`, `/families`, `/catalog`, `/investment-management/*`.

## Operational notes

- **Lock state is orthogonal to regulatory state.** A `CLIENT_EXCLUSIVE` SaaS-mode strategy still runs under the same
  SMA / fund regulatory framework as `PUBLIC`. See
  [`../README.md#regulatory-quick-reference-by-strategy-family--asset-group`](../README.md).
- **Lock state is orthogonal to roll state.** A `-dated-` rolling-future strategy can be PUBLIC or IM_RESERVED; the roll
  mechanism is the same.
- **Lock state is orthogonal to deploy state.** A locked slot can still be in shadow, paper, or prod env. Env is a
  separate axis in the slot label (`-prod`, `-paper`, `-shadow`).
- **Admin action audit trail.** Every `STRATEGY_AVAILABILITY_CHANGED` event is retained indefinitely — this is the audit
  trail for "why can't my client allocate to strategy X today?".

## Migration

Today the UI implicitly treats every strategy as PUBLIC — there is no lock mechanism. Migration is phased in the
finalisation plan (Phase 10.5, see `strategy_architecture_v2_finalization_2026_04_19.plan.md`):

1. Add `StrategyAvailabilityRegistry` to UAC with every currently-defined slot at `PUBLIC`.
2. Add events + UI badges + filters.
3. Add admin toggle UI + RBAC enforcement in allocator.
4. No behavioural change at launch — all slots stay PUBLIC.
5. Operator manually transitions slots as client / fund contracts land.

## Current Lock State Snapshot (2026-04-20)

As of 2026-04-20, only `STAT_ARB_PAIRS_FIXED` × crypto cells are `PUBLIC`. All other archetype × instrument × venue
combinations in [`../category-instrument-coverage.md`](../category-instrument-coverage.md) default to
`INVESTMENT_MANAGEMENT_RESERVED` per Odum's forward plan. This snapshot is the runtime state the catalogue registry
reads.

### IM_RESERVED cells — currently running for own IM

| Archetype                    | Category | Instrument    | Venues                              | Status            | Notes                                                              |
| ---------------------------- | -------- | ------------- | ----------------------------------- | ----------------- | ------------------------------------------------------------------ |
| ML_DIRECTIONAL_CONTINUOUS    | CEFI     | spot          | Binance, Coinbase, Hyperliquid      | Jun 2026 go-live  | BTC ML for 10 IM clients × $500k                                   |
| ML_DIRECTIONAL_CONTINUOUS    | CEFI     | perp          | Binance-perp, Hyperliquid           | Jun 2026 go-live  | BTC ML perp companion                                              |
| ML_DIRECTIONAL_CONTINUOUS    | TRADFI   | dated_future  | CME (S&P futures)                   | Sept 2026 go-live | CME co-invest ($500k → $5M ramping)                                |
| VOL_TRADING_OPTIONS          | TRADFI   | option        | NSE (India options)                 | Oct 2026 go-live  | India Options delta trading for convex payouts ($5-10M allocation) |
| ML_DIRECTIONAL_EVENT_SETTLED | SPORTS   | event_settled | Betfair, Betradar, specific leagues | Jun 2026 go-live  | Sports ML for 2 clients × $50-100k (capacity-bound)                |

### External wrappers and per-client overrides

**BTC Fund of Funds** is an **external wrapper** — Odum allocates a BTC mandate to an external fund-of-funds and does
not operate the strategy on Odum infrastructure. It is **NOT in the strategy catalogue** at all (no cell, no
`lock_state`); it surfaces only in `client-reporting` for that specific wrapper mandate.

**Per-client overrides** (Elysium, Desmond) leave catalogue cells at their default `INVESTMENT_MANAGEMENT_RESERVED` and
grant operational access via per-client entitlement. Elysium runs `CARRY_BASIS_PERP`, `CARRY_STAKED_BASIS`,
`YIELD_ROTATION_LENDING` (plus upsell `CARRY_RECURSIVE_STAKED`) on our infrastructure — cells remain IM_RESERVED for
catalogue defaults; Elysium's entitlement grants them operational access only. Desmond uses the same mechanic for
`ARBITRAGE_PRICE_DISPERSION` on CEFI perps.

### Canonical source + enforcement

Canonical source-of-truth matrix:
[`../../../14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md`](../../../14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md).
Enforcement points:

- UI mirror — `unified-trading-system-ui/lib/architecture-v2/availability.ts`
- strategy-service runtime registry — `strategy_service/availability/`
- UAC combo registry — `unified_api_contracts/internal/architecture_v2/strategy_availability.py`
  (`StrategyAvailabilityRegistry`, gap #12)

## See also

- [`../category-instrument-coverage.md`](../category-instrument-coverage.md) — the universe we lock over.
- [`../uac-registry-gaps.md`](../uac-registry-gaps.md) — registry shape for `StrategyAvailabilityRegistry` (gap #12).
- [`capital-client-isolation.md`](capital-client-isolation.md) — per-client capital isolation (related but distinct).
- [`portfolio-allocator.md`](portfolio-allocator.md) — where allocation authorisation check lives.
- [`../../../14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md`](../../../14-customer-journeys/shared-core/strategy-allocation-lock-matrix.md)
  — canonical current-state snapshot.
