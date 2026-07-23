---
doc_type: codex-ssot
title: Futures Rolls and Combo Creation (Cross-Cutting)
summary:
  Service-level spec for dated-future rolling — a representative-future-service ranks candidate contracts by liquidity
  features (OI/volume/depth) with expiry-buffer + confirmation-window guards and emits REPRESENTATIVE_FUTURE_CHANGED;
  position-holding strategies on -dated- slots emit a FUTURES_ROLL (ATOMIC mode=CALENDAR_ROLL); execution-service
  resolves listed-combo → synthetic-combo → LEADER_HEDGE with a synthetic fair-value slippage guardrail; circuit
  breakers + batch=live replay equivalence.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [execution-service, features-service, strategy-service]
scope: [engineer, admin]
tags: [strategy, execution, features, tradfi, migration]
related:
  [
    ../category-instrument-coverage.md,
    ../uac-registry-gaps.md,
    ../../../04-architecture/strategy-execution-protocol.md,
    ../archetypes/carry-basis-dated.md,
    /codex/09-strategy/architecture-v2/cross-cutting/execution-policies.md,
  ]
created: 2026-04-20
authoritative_for:
  [dated-future roll service spec (representative-future-service + FUTURES_ROLL/CALENDAR_ROLL combo resolution)]
referenced_by: [/codex/09-strategy/architecture-v2/uac-registry-gaps.md]
owner:
last_reviewed:
code_refs:
---

# Futures Rolls and Combo Creation (Cross-Cutting)

> **Status:** Spec as of 2026-04-19. Paired with
> [`../category-instrument-coverage.md §Dated-future rolls`](../category-instrument-coverage.md#dated-future-rolls-and-representative-futures)
> (SSOT for the slot-label convention) and
> [`../uac-registry-gaps.md #11`](../uac-registry-gaps.md#11-representativefutureregistry--representative_future_changed-event)
> (the registry + event contract). This doc is the **service-level spec** — what runs where, what the wire contracts
> look like, what fails how.
>
> **Scope:** Applies to every archetype that trades `dated_future` instruments via the default rolling-continuous
> convention. Does not apply to `VOL_TRADING_OPTIONS` (expiry-aware by design) or to expiry-anchored instances using the
> `-fixed-{contract}-` slot label.

---

## Motivation

A dated-future strategy is not meaningfully expiry-aware — an ML directional model on CME ES doesn't care whether it's
trading ESZ5 or ESH6; it cares about the S&P e-mini front-month tape. Forcing each archetype to hand-roll expiry
management would duplicate logic 6+ times (ML continuous, rules continuous, stat-arb pairs, stat-arb cross-sectional,
arbitrage price-dispersion, event-driven, basis-dated default mode).

We factor this out: an **underlying** resolves at any instant to a **representative future** chosen deterministically
from liquidity features. When the representative changes, a single event ripples through to all subscribed strategies,
which respond by emitting a roll instruction. Execution-service handles the roll as a single combo order (listed or
synthesized).

## Components

### 1. Underlying identity

Pre-existing concept; this doc only formalises it for dated futures. An **underlying** is a stable identifier that
survives expiry:

```
BTC-USD-DERIBIT-DATED
ETH-USD-DERIBIT-DATED
ES-USD-CME
NQ-USD-CME
RTY-USD-CME
YM-USD-CME
CL-USD-CME
GC-USD-CME
NG-USD-CME
HG-USD-CME
6E-USD-CME
6B-USD-CME
6J-USD-CME
BRENT-USD-ICE
GASOIL-USD-ICE
```

Registered in `RepresentativeFutureRegistry` (UAC — see
[uac-registry-gaps.md #11](../uac-registry-gaps.md#11-representativefutureregistry--representative_future_changed-event)).

### 2. Liquidity feature group

A named, versioned feature group published by `features-service` that emits the per-contract liquidity measure the roll
decision is based on. Declared in each `UnderlyingDeclaration.roll_policy.liquidity_feature_group_ref`.

**Required feature columns per (underlying, contract_code) tuple:**

| Column                       | Type  | Description                                 |
| ---------------------------- | ----- | ------------------------------------------- |
| `open_interest`              | int   | Current OI in contracts                     |
| `volume_24h`                 | int   | Rolling 24h volume in contracts             |
| `bid_ask_depth_notional_usd` | float | Top-5 level depth in USD at the current mid |
| `expiry_at_utc`              | str   | ISO 8601 expiry timestamp                   |
| `measured_at_utc`            | str   | ISO 8601 measurement timestamp              |

Strategy-service never reads these directly — it reads the derived `representative_future` mapping output below.

### 3. representative-future-service

A new thin service (or sub-module of `features-service` if co-location is acceptable). Responsibilities:

1. Subscribe to the liquidity feature group for every underlying in `RepresentativeFutureRegistry`.
2. Compute `representative_future(underlying_id)` deterministically on each new liquidity tick:
   - Rank candidate contracts by the declared liquidity measure (typically `open_interest` or a weighted blend of
     `open_interest + volume_24h`).
   - Apply the `expiry_buffer_days` guard — don't switch if the current rep is within N days of expiry and the next
     candidate is not yet ahead by at least `liquidity_margin_bps`.
   - Apply the `liquidity_confirmation_windows` guard — the next candidate must lead for N consecutive windows before a
     switch is declared (prevents thrashing on tick noise).
3. On state transition, emit `REPRESENTATIVE_FUTURE_CHANGED` (schema in UAC — see #11) over Pub/Sub + in-process
   notifier.
4. Publish a snapshot table `gs://{project}-reference-artifacts/representative_future/{underlying_id}.json` read by
   batch jobs and new subscribers on startup.
5. Expose a REST / gRPC endpoint `GET /representative/{underlying_id}?as_of={iso_ts}` for deterministic replay (backtest
   mode uses this to resolve the representative at any historical instant).

Service properties:

- **Stateless per event** — decision is a pure function of current liquidity features + policy. State is recomputed from
  features on restart; no hidden cursor.
- **Deterministic replay** — given a snapshot of features and the policy content hash, the sequence of
  `REPRESENTATIVE_FUTURE_CHANGED` events is reproducible. Backtest mode replays features in order and derives the
  historical representative at each tick.
- **Isolation tier** — shared across clients and strategies; single instance per region. Not in the client-isolation
  scope (no PII, no trade data).

### 4. Strategy-service subscription

Each strategy instance on a slot using `-dated-` scope subscribes to `REPRESENTATIVE_FUTURE_CHANGED` filtered by the
underlying(s) the strategy cares about. Subscription is automatic from slot label parsing — no explicit config.

On receiving the event, the strategy:

1. Looks up its current net position in `prior_contract` (from PBMS projection).
2. If net position is zero → no-op; accept the new representative for future opens.
3. If net position is non-zero → emit a single `FUTURES_ROLL` instruction (variant of `ATOMIC` — see §5).
4. Update the strategy's internal `current_contract` field to `new_contract`. Subsequent signal-driven instructions
   target the new contract.

Strategy engines that hold positions across the tick boundary (`CARRY_BASIS_DATED`, `STAT_ARB_PAIRS_FIXED`,
`ML_DIRECTIONAL_CONTINUOUS` in `HOLD_UNTIL_FLIP` mode) implement this flow. Engines that don't hold positions
(`RULES_DIRECTIONAL_CONTINUOUS` in `SAME_CANDLE_EXIT` mode, event-driven one-shots) simply accept the new representative
and emit against it on next signal.

### 5. `FUTURES_ROLL` instruction variant

Expressed as an `ATOMIC` `StrategyInstructionEnvelope` with a `roll_context`:

```python
# Pseudocode — actual schema lives in UAC
AtomicInstruction(
    correlation_id=<from REPRESENTATIVE_FUTURE_CHANGED.correlation_id>,
    mode="CALENDAR_ROLL",  # new ATOMIC mode — joins LEADER_HEDGE / SYNCHRONIZED / SEQUENTIAL
    roll_context=RollContext(
        underlying_id="BTC-USD-DERIBIT-DATED",
        prior_contract="BTC-26DEC25",
        new_contract="BTC-27MAR26",
        max_roll_slippage_bps=20,          # from UnderlyingDeclaration
        synthetic_fair_value_ref="legs_mid",  # execution-service computes from both legs
    ),
    legs=(
        TradeInstruction(
            action="TRADE",
            instrument="BTC-26DEC25",
            target_position_units=Decimal("0"),  # close prior leg
        ),
        TradeInstruction(
            action="TRADE",
            instrument="BTC-27MAR26",
            target_position_units=current_net,    # open new leg
        ),
    ),
)
```

**Emission guarantees:**

- Only the strategy that holds the position emits the roll — PBMS attribution ensures correct strategy ownership.
- Multiple strategies sharing the same venue account each emit independently; execution-service serialises per account.
- Roll instruction has priority `P0` for scheduling — precedes new-signal instructions on the same instrument.

### 6. Execution-service combo resolution

On receiving a `FUTURES_ROLL` / `ATOMIC` with `mode=CALENDAR_ROLL`:

```
Step 1. Look up venue capability: does the venue list a calendar-spread combo ticker for
        (prior_contract, new_contract)?

   IF venue.multi_leg_order_capability.supports_listed_combos AND
      venue has a listed combo ticker covering this leg pair:

      → Execute as single order against combo ticker.
        Example: CME ES calendar spread ticker "ES Z5-H6".
        Venue guarantees simultaneous fill; slippage = |executed_net - expected_mid_spread|.

   ELSE IF venue.multi_leg_order_capability.supports_synthetic_combos AND
           legs fit under max_legs:

      → Execute as synthetic combo: venue accepts a multi-leg order as single submission.
        Example: Deribit combo market order — venue matches both legs atomically internally.

   ELSE:

      → Fall back to LEADER_HEDGE with hard slippage guard:
        - Submit the more-liquid leg first (typically the new_contract — in the direction of
          the roll).
        - On fill, submit the hedge leg within `leader_hedge_min_interval_ms`.
        - If hedge leg doesn't fill within the window, abort and unwind the leader.

Step 2. Synthetic fair-value guardrail (applies to all three paths):

   synthetic_fair_value = mid(new_contract) - mid(prior_contract)
   if abs(executed_spread - synthetic_fair_value) > max_roll_slippage_bps:
       → emit FUTURES_ROLL_FAILED + unwind leader leg (if LEADER_HEDGE mode)
       → do NOT open new leg
       → hard stop for this underlying; ops escalation if it persists

Step 3. On success:
   → emit FUTURES_ROLL_COMPLETED {correlation_id, prior_contract, new_contract,
                                  executed_spread, synthetic_fair_value, slippage_bps, at}
   → PBMS rewrites position attribution from prior_contract → new_contract
```

### 7. Circuit breakers

| Trigger                                                                                  | Action                                                                                                                 |
| ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| Roll slippage > `max_roll_slippage_bps`                                                  | Hard stop. Unwind leader leg (LEADER_HEDGE mode); do not open new leg. Emit `FUTURES_ROLL_FAILED`. Ops alert.          |
| Representative-future-service feed stale > `feed_staleness_soft_freeze_seconds`          | Soft freeze. All subscribers pause new opens; existing positions held. Ops alert.                                      |
| Consecutive roll failures > `consecutive_failure_escalation_threshold` for an underlying | Full ops escalation. Strategy-service auto-pauses all strategies on that underlying pending human review.              |
| `REPRESENTATIVE_FUTURE_CHANGED` event but no combo resolution path exists                | Emit `FUTURES_ROLL_FAILED` with `reason=NO_COMBO_RESOLUTION`. Block until venue capability declares multi-leg support. |

All circuit-breaker events emit via UTL `log_event` with canonical `KillSwitchReason` where applicable.

### 8. Backtest-mode equivalence

`batch=live` principle (CLAUDE.md): backtest must exercise the identical code path. For rolls:

1. Historical feature stream is replayed via `features-service` → representative-future-service emits the historical
   sequence of `REPRESENTATIVE_FUTURE_CHANGED` events at the original wall-clock offsets.
2. Strategy-service subscribers (V2EngineOrchestrator via V2BatchHarness) receive the events and emit `FUTURES_ROLL`
   instructions identically.
3. Execution-service matching engine models the roll as a synthetic combo fill: slippage and commission computed from
   historical OHLC + depth snapshots of both legs.
4. Execution alpha = (live combo fill) − (matching-engine combo fill). Isolates strategy P&L from roll-execution
   quality, same as ordinary TRADE instructions.

Backtest parity tests (Phase 1e of the finalisation plan) must include at least one rolling-underlying scenario that
crosses an actual historical roll boundary.

## Service-boundary diagram

```
                    ┌──────────────────────────────┐
                    │   features-service           │
                    │   (delta-one liquidity       │
                    │    feature group)            │
                    └───────────────┬──────────────┘
                                    │ liquidity snapshots
                                    ▼
                    ┌──────────────────────────────┐
                    │ representative-future-service │
                    │  - applies RollTriggerPolicy  │
                    │  - emits state transitions   │
                    └───────────────┬──────────────┘
                                    │ REPRESENTATIVE_FUTURE_CHANGED
                                    │ (Pub/Sub + in-proc notifier)
                                    ▼
              ┌─────────────────────────────────────────────┐
              │  strategy-service                            │
              │  V2EngineOrchestrator + per-instance         │
              │  subscribers on `-dated-` slots              │
              └─────────────────────┬───────────────────────┘
                                    │ ATOMIC {mode=CALENDAR_ROLL}
                                    ▼
              ┌─────────────────────────────────────────────┐
              │  execution-service                           │
              │  ATOMIC handler →                            │
              │    1) listed combo ticker (preferred)         │
              │    2) synthetic combo (venue multi-leg)       │
              │    3) LEADER_HEDGE fallback                   │
              │  Synthetic fair-value guardrail on all paths │
              └─────────────────────┬───────────────────────┘
                                    │ FUTURES_ROLL_COMPLETED
                                    │ or FUTURES_ROLL_FAILED
                                    ▼
              ┌──────────────────────────────┐  ┌─────────────────┐
              │ PBMS — rewrites attribution  │  │ R&E — circuit    │
              │ prior_contract → new_contract │  │ breaker + alert │
              └──────────────────────────────┘  └─────────────────┘
```

## Interaction with other cross-cutting concerns

- **[risk-gates](risk-gates.md)** — roll instructions pass through all four layers. Layer-2 pre-flight checks that the
  combined position post-roll doesn't breach margin. Layer-3 venue-account pre-flight validates leg-level margin on both
  legs.
- **[execution-policies](execution-policies.md)** — per-venue `CalendarRollPolicy` entry in the execution-policy
  registry declares slippage tolerances + LEADER_HEDGE window per venue, consumed by the combo resolver.
- **[benchmark-fills](benchmark-fills.md)** — roll instructions receive a benchmark fill at the synthetic fair-value
  mid. Strategy alpha (which comes from holding the underlying continuously) is unaffected by roll execution alpha.
- **[transfer-rebalance](transfer-rebalance.md)** — rolls don't require cross-venue capital movement (both legs are on
  the same venue). No interaction.
- **[portfolio-allocator](portfolio-allocator.md)** — allocator is unaware of rolls; it sees strategy equity
  continuously. The roll is internal to the strategy, not a portfolio-level event.

## Migration

| Current state                                                                                | Target state                                                                     |
| -------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| Dated-future strategies launched with `-fixed-{contract}-` slot labels; ops rotates manually | All dated-future strategies use `-dated-` slot labels; roll service auto-rotates |
| Each archetype doc has expiry warnings in "Hold policy" / "Not in this archetype" sections   | Archetype docs point to this doc as the canonical rolls reference                |
| No `RepresentativeFutureRegistry` in UAC                                                     | UAC registry populated (see uac-registry-gaps.md #11)                            |
| No `representative-future-service`                                                           | Service scaffolded + deployed + producing events                                 |
| `ATOMIC` has 3 modes (LEADER_HEDGE, SYNCHRONIZED, SEQUENTIAL)                                | Fourth mode `CALENDAR_ROLL` added                                                |
| execution-service combo resolution only uses synthetic multi-leg                             | Combo resolution picks listed combo ticker when available; synthesises otherwise |

Migration is phased via a new Phase 11 in the active finalisation plan
(`strategy_architecture_v2_finalization_2026_04_19.plan.md`).

## Not in this spec

- **Option rolls** — `VOL_TRADING_OPTIONS` manages its own weekly/monthly/quarterly serial roll; separate mechanism,
  same slot-label convention (`-dated-` implies rolling term structure).
- **LST rotation** — `YIELD_STAKING_SIMPLE` multi-LST rotation is not a roll; it's a cross-asset rebalance. Handled by
  the normal allocation-directive path.
- **Lending-market rotation** — `YIELD_ROTATION_LENDING` cross-chain rotation is handled by the strategy's own cadence +
  transfer-rebalance service. Not a roll.
- **Soft-forks / hard-forks that rename a token** — covered by instrument-registry migration, not by this spec.

## See also

- [`../category-instrument-coverage.md#dated-future-rolls-and-representative-futures`](../category-instrument-coverage.md#dated-future-rolls-and-representative-futures)
  — SSOT for the slot-label convention and which archetypes use it.
- [`../uac-registry-gaps.md#11-representativefutureregistry--representative_future_changed-event`](../uac-registry-gaps.md#11-representativefutureregistry--representative_future_changed-event)
  — UAC registry + event schema.
- [`../../../04-architecture/strategy-execution-protocol.md`](../../../04-architecture/strategy-execution-protocol.md) —
  full polymorphic instruction spec; `CALENDAR_ROLL` is a new `ATOMIC` mode under rule #3.
- [`../archetypes/carry-basis-dated.md`](../archetypes/carry-basis-dated.md) — primary dated-future archetype; default
  mode uses `-dated-` rolling.
