---
doc_type: issue
title: >-
  Generic price-sensitivity contract for fast execution-side repricing — real infrastructure exists
  (`DeltaProxyRepricer`, `order_semantics.py`'s gap registry) but unwired on every end, and the pattern needs a
  full 3-layer design (strategy intent -> execution trigger cache -> order-fill algo) before it can generalize
  from market-making to arb-leg hedging and MEV
summary: >-
  Investigating whether strategy-service's MEV opportunity-detection logic should also own low-latency repricing
  surfaced a much broader, mostly-already-real pattern spanning three services. Execution-service has a
  fully-written, unit-tested delta/gamma linearization engine (`DeltaProxyRepricer` + `QuoteMaintainer`) that lets
  strategy-service publish a reference price + sensitivity ONCE and have execution-service extrapolate cheaply
  against live market moves without a round-trip — unwired on every end (deleted receipt point, no live tick loop,
  self-underlying-only schema). UAC separately already has a formal, honest gap registry
  (`internal/architecture_v2/order_semantics.py`) naming almost this exact pattern as declared-but-unwired
  capabilities (`TimeInForce.POST_ONLY`, `RefPricingMode.DELTA_ADJUSTED_TO_UNDERLYING`, `MultiLegDeltaOwner`) —
  zero venues have any of them wired end-to-end today. The arb-leg `LEADER_HEDGE` mechanism is real but uses a
  fixed pre-computed hedge price with ZERO slippage tolerance plus a blunt time deadline, not a live credit-banded
  reprice. The order-fill algorithm layer (`algorithms/selector.py`) is real and substantial but has no true
  one-shot `MARKET` option on the automated path (manual-only) and 3 parallel, non-unified execution routers.
  Strategy-service's own `ExposureAggregator` already computes real net/"effective" exposure — whether
  execution-service's preflight gate actually reads it is unconfirmed. 11 judgment calls for the operator, only one
  resolved this session (credit-tolerance is optional, a "flavor," never a mandatory field).
status: open
nature: issue
asset_group: [cross-cutting]
stage: [strategy, execution]
repos: [execution-service, strategy-service, unified-api-contracts]
scope: [engineer]
tags:
  [
    execution-architecture,
    market-making,
    mev,
    latency,
    delta-proxy,
    quote-maintenance,
    sensitivity-contract,
    order-semantics,
    tier-isolation,
    w16,
  ]
priority: P1
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
created: 2026-08-18
source: >-
  Surfaced in an interactive session investigating whether ARBITRAGE_MEV_BACKRUN/_JIT_LIQUIDITY/_LIQUIDATION_BUNDLE's
  latency needs meant strategy-service was architecturally the wrong home for their trigger logic. The operator's own
  CeFi analogy (IP rotation, hot-connection websockets, pre-cached "if price hits X, fire without re-parsing the
  packet" logic all belong in execution-service) led to checking whether the DeFi/MEV equivalent was already
  execution-service's job (confirmed yes), then to the operator's own generalization across market-making, arb-leg
  hedging and options liquidity-taking via a shared "credit" concept, then to a full 3-layer design pass (strategy
  intent / execution trigger cache / order-fill algorithm) once the operator explicitly asked for the code SHAPE to
  support future co-location and a later Python-to-Rust hot-path migration without a redesign. Every claim below was
  verified by direct read this session, not taken on a research agent's word alone.
related:
  [
    /plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md,
    /plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
    /plans/epics/system_readiness_master.md,
  ]
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
drift_direction: advance-code
depends_on: []
context_scope:
  [
    execution-service/execution_service/engine/delta_proxy_repricer.py,
    execution-service/execution_service/engine/quote_maintenance.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/order_semantics.py,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py,
    execution-service/execution_service/v2/atomic_leg_executor.py,
    execution-service/execution_service/algorithms/selector.py,
    /codex/04-architecture/risk-rule-taxonomy.md,
  ]
---

# Generic price-sensitivity contract for fast execution-side repricing

## The pattern under discussion

Strategy-service is architecturally forbidden from importing execution-service directly (T4 tier isolation) and
communicates only via the async `EventTransport` publish/subscribe seam — confirmed via
`strategy-service/strategy_service/engine/strategies/v2/live_routing.py` and
`/plans/archive/issues/prediction_arb_live_execution_bridge_2026_07_20.md` (the ruled 2026-07-28 precedent for
exactly this seam shape). For latency-sensitive opportunities, re-running strategy-service's full tick decision and
re-publishing on every market move is too slow for some archetypes.

The proposed fix, generalized beyond options pricing: strategy-service periodically computes and publishes a LOCAL
linear (or quadratic) sensitivity approximation of how an opportunity's value moves with the market — delta/gamma,
generalized beyond options to arb-leg repricing, hedging, and liquidity-taking/pulling. Execution-service caches
this, watches the live order book / chain feed directly (no round-trip), cheaply extrapolates whether the cached
opportunity is still actionable given the live move, and routes to whichever order-fill algorithm handles it. This
turned out to require three genuinely distinct layers, detailed below — collapsing them was the main risk in
earlier passes at this design.

## Layer 1 — what strategy-service should publish (intent, not mechanics)

Already effectively ruled, just not yet named as a rule for this new work: `e2e_wiring_reachability_audit_2026_08_15.md`'s
"Artefact disclosure boundary" table already draws this exact line — strategy tells execution **that** `urgency`
steers aggressive-vs-passive and **that** venue/algo choice follows policy; **which** algo fires under which
condition is execution-service's own call. Applied here: strategy-service publishes reference price(s), a
sensitivity coefficient, an OPTIONAL credit band (see Layer 2), and an intent hint (urgency / aggressiveness /
max-loss) — never "split into 10 pieces" or a literal algo name. Mechanics stay entirely downstream.

## Layer 2 — the trigger/sensitivity cache (execution-service, real code, unwired)

`execution_service/engine/delta_proxy_repricer.py` (module docstring, lines 1-21) is this pattern, already written,
almost verbatim:

```
underlying_move = current_underlying - reference_price
effective_delta = delta + gamma * underlying_move   (if gamma set)
price_adjustment = underlying_move * effective_delta
new_bid = original_bid + price_adjustment
new_ask = original_ask + price_adjustment
```

`DeltaProxyRepricer._reprice()` (lines 192-239) implements this exactly, with a `max_adjustment_pct` (default 5%)
staleness clamp that flags `stale=True` rather than extrapolating past a sane bound. Real dataclasses
(`DeltaProxyParams`, `RepricedQuote`), real unit tests. `execution_service/engine/quote_maintenance.py`'s
`QuoteMaintainer` wires it to a `QuoteVenueSubmitter` protocol for actual order submission.

**Three concrete gaps keep it from being live**, per `quote_maintenance.py`'s own docstring (verified by direct
read):

1. **UAC's `QuoteInstruction` schema** (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py:317-324`)
   carries `instrument`, `reference_price`, `half_spread_bps`, `max_inventory_abs`, `skew_on_inventory`,
   `refresh_cadence_ms` — **no `delta`/`gamma`/`underlying_instrument_id` fields**. The wiring that exists defaults
   `underlying_instrument_id = instrument` and `delta = 1.0` — the Spot/Perp self-underlying case only.
2. **The strategy-side dispatch point was deleted.** `execution_service.v2.handlers.QuoteHandler` was THIS receipt
   point until deleted 2026-08-15 as confirmed dead code (`execution-service@37bfaeed0b`, alongside
   `V2InstructionRouter`; full context in `/plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md`). No
   replacement built. `quote_maintenance.py`'s own docstring says a future receipt path should register directly
   against `QuoteMaintainer`, not resurrect the deleted router.
3. **No live underlying-tick ingestion loop exists.** Confirmed via the module's own docstring and independently via
   a workspace grep — "no `EventTransport` tick consumer anywhere in execution-service." Candidate live-data
   mechanisms already exist (`providers/l2_depth_provider.py`'s LIVE mode subscribing to an MDPS Redis Stream, direct
   venue websocket clients, `providers/solana_amm_depth_provider.py`) — none call into `DeltaProxyRepricer`.

**A dead documentation pointer riding along with this**: both `vol_trading/options.py` (strategy-service) and
`quote_maintenance.py` (execution-service) cite `feedback_market_making_reference_price_model.md` as "the v2
architecture memo" for this design. Confirmed via `find`: that file does not exist anywhere in `unified-trading-pm`.

### The generic contract this session's design settled on (proposal, not yet ruled)

Two deliberately SEPARATE things — conflating them was a real risk flagged and avoided:

```
ExecutionSensitivityEntry:
  provenance:  strategy_id, instruction_id, archetype   # audit/attribution ONLY — never read by algo logic
  references:  list[{ instrument_id, reference_price, sensitivity_coefficient, second_order_coefficient? }]
               # N=1 is MM/options (one underlying). N=2 is the arb-leg case. A basket/multi-leg options structure
               # is just a longer list — same shape, no later schema rewrite (this session already found
               # GreekTargets/ClusterGreekTargets computing multi-underlying portfolios today).
  credit:      { entry_threshold, abandon_threshold }   # BOTH OPTIONAL — see "credit is a flavor" below
  trigger:     { watched_field, comparison }            # usually net-move-vs-credit; see judgment call 2
  staleness:   { valid_until_utc, refresh_cadence_ms }  # fail-closed on expiry, no exception (see W16 tie-in below)
  requested_execution: { order_type, algo_hint, urgency }  # feeds Layer 3, doesn't reinvent it

AmbientMarketLean:  keyed by instrument/instrument-group, NOT by instruction — deliberately separate from the above
  direction, magnitude, confidence, source (audit only), decay rule
  # An algo MAY consult this to widen/narrow how aggressively it acts on an already-triggered entry (e.g. an
  # ML/RL-fed directional lean updating every second) — it is never itself a trigger source. "What fired this" and
  # "how should I feel about acting on it right now" are different concerns; merging them makes both harder to test.
```

**Credit-tolerance is a flavor, not a mandatory field — resolved this session.** Different execution styles consume
the same cached entry differently: pure-passive-wait, fire-immediately-with-no-tolerance-check, and
patient-then-escalate-aggressive are all valid consumers; `credit` stays optional on the schema.

## Layer 3 — the order-fill algorithm (real, substantial, three parallel paths, two real gaps)

Verified directly by reading `execution_service/algorithms/selector.py` in full. This is the "how you buy/sell
stuff" layer — TWAP/VWAP/slicing style vs. one-shot — and it is genuinely separate from Layer 2's "when/whether to
act" decision.

- **`ALGORITHMS_BY_INSTRUCTION_TYPE`** for `TRADE`: `BENCHMARK_FILL`, `TWAP`, `VWAP`, `ADAPTIVE_TWAP`,
  `ALMGREN_CHRISS`, `POV_DYNAMIC`, `HYBRID_OPTIMAL`, `PASSIVE_AGGRESSIVE_HYBRID`. For `SWAP`:
  `SMART_ORDER_ROUTER`/`SOR_TWAP`/`SWAP_TWAP`/`MAX_SLIPPAGE`. `ExecutionPolicyResolver` +
  `engine/routing/handler_registry.py::HandlerRegistry.select_algorithm()` layer a per-`(client_id, slot_label)`
  policy overlay on top, gating on venue_category/instrument_type/urgency/notional — real, already wired.
- **Real gap 1 — no automated "just go for it."** A true one-shot `MARKET` order exists in the code but is in
  `MANUAL_ONLY_ALGOS`, deliberately excluded from this canonical/automated selector — the module's own comment: it
  "cannot be realistically backtested (no queue-position modeling)," same reason `ICEBERG` is excluded. So a
  strategy-triggered "go for it" has no true aggressive one-shot option today; the closest real thing is
  `PASSIVE_AGGRESSIVE_HYBRID` or a short-horizon `ALMGREN_CHRISS`. Whether an ALREADY-cleared credit/trigger check
  changes that calculus is judgment call 7 below.
- **Real gap 2 — GHOST algos.** `OPTIONS_COMBO`/`FUTURES_ROLL`/`PREDICTION_BET`/`SPORTS_BET`/`SPORTS_EXCHANGE` each
  declare a default algo (`SEQUENTIAL_LEGS`/`SPREAD_ROLL`/`BEST_PRICE`/`KELLY_STAKE`) with **no implementation
  class** — routing through one fails LOUD (`ValueError`), per the module's own comment, not a silent misexecution.
  Not a live problem today because nothing routes those instruction types through THIS selector — but a real trap
  if Layer 2 is built generically and someone assumes this is the universal entry point.
- **Real topology fact — three parallel, non-unified execution paths, not one router.** This selector covers
  TRADE/SWAP/OPTIONS_COMBO-style instructions. The arb-leg `LEADER_HEDGE` case
  (`execution_service/v2/atomic_leg_executor.py`, read in full this session) bypasses it entirely and calls
  `SportsAdapter.place_bet` directly. MEV bundles go through a third path, `v2/mev_router.py`. Layer 2 needs to know
  WHICH of the three a given trigger belongs to — that routing is itself a decision (judgment call 8), not a detail.

### The arb-leg `LEADER_HEDGE` mechanism — verified, and it is a THIRD distinct pattern from both DeltaProxyRepricer and a true credit-band reprice

Read `atomic_leg_executor.py` in full. It sequences leader-then-hedge (`AtomicLegExecutor.execute`: place leader
first, only then place hedge legs), but the hedge leg's price is decided **upfront**, at signal time, inside
`build_prediction_arb_legs` — not re-evaluated against how the market actually moved between leader-fill and
hedge-placement. `atomic_leg_to_bet_order` sets `max_acceptable_odds=requested_odds` — **zero slippage tolerance**,
not a credit band. The only other guard is `hedge_deadline_ms` (10s default) — a pure **time** cutoff with no
awareness of how far price moved during that window. So today's mechanism is "decide both legs' prices once,
upfront, then race a clock on the second one" — genuinely distinct from a live credit-banded reprice (which would
let the hedge leg's acceptable price band move, live, against how the OTHER leg's market has actually moved since
the leader filled — the worked example this session's discussion used: chase the hedge down to parity if filled at
the expected level, but only within a bounded negative-credit tolerance if the market moved against you first).
This is a real, currently-nonexistent fourth mechanism, distinct from all three found so far.

## What does NOT exist — the arb-leg-repricing analog

`price_dispersion.py` and `atomic_leg_executor.py` have **zero** delta/reprice tracking beyond the fixed-price
sequencing above — confirmed via direct grep of both files for `delta|reprice|leg_delta|sensitivity`; the only hits
are "delta-neutral"/"delta-hedging" as plain-English description, not implemented mechanism. UAC does declare a
directly relevant enum, `MultiLegDeltaOwner`
(`unified-api-contracts/unified_api_contracts/internal/architecture_v2/order_semantics.py:97-124`) — WHO owns
inter-leg delta risk during a fill (`ATOMIC_BUNDLE` / `EXECUTION_ALGO` / `STRATEGY_ENGINE` / `UNMANAGED`) — but
nothing reads or acts on it.

## The bigger find while verifying `MultiLegDeltaOwner`: `order_semantics.py` is a formal, honest gap registry for almost this entire issue

Read `internal/architecture_v2/order_semantics.py` in full. It already declares, as real UAC enums, several of the
exact concepts this whole design has been reasoning toward from first principles:

- **`TimeInForce.POST_ONLY`** — "order is rejected or cancelled if it would take liquidity." This is precisely the
  "enforce a non-crossing limit" behavior discussed this session, and the schema already supports BOTH enforcement
  points the operator asked about: `VenueOrderSemantics.honored_tif` (does the adapter even SEND this TIF) and
  `post_only: bool` (does the venue's mechanism work end-to-end) are tracked SEPARATELY per venue — i.e., "enforce
  at the algo/parameter level" vs. "enforce at the venue/order-type level" are already modeled as two independent
  facts, not an either/or. Currently `post_only=False` for every backfilled venue (hyperliquid, deribit) — "POST_ONLY
  not explicitly mapped."
- **`RefPricingMode.DELTA_ADJUSTED_TO_UNDERLYING`** — "Entry price is delta-adjusted relative to underlying movement
  between instruction generation and execution ('premium-on-delta'). Required for options and some structured
  spread trades." This IS the formal, already-declared name for the DeltaProxyRepricer pattern. Every backfilled
  venue currently only declares `[RefPricingMode.FIXED]` — zero venues have delta-adjusted pricing enabled.
- **`VenueOrderSemantics`** itself is the pattern this whole issue should probably extend, not duplicate — it is a
  real, per-venue, citation-backed ("every entry cites source file:line, nothing invented") capability-gap registry
  already covering TIF, post-only, make/take, ref-pricing mode and multi-leg delta ownership in one place.

## Position vs "effective position" — real, and execution-service's access to it is now CONFIRMED absent

`strategy-service/strategy_service/risk/core/exposure_aggregator.py`'s `ExposureAggregator` is real: computes
`gross_exposure`/`net_exposure`/`long_exposure`/`short_exposure` via UTL's `gross_exposure`/`net_signed_exposure`
helpers, aggregated across venues and instruments. This is exactly "effective position" (what you'd still be
exposed to after netting correlated/offsetting positions) — already built, not epic-level aspiration.

**Judgment call 10, RESOLVED by direct verification 2026-08-19** (was "unconfirmed," now confirmed): read
`execution-service/execution_service/engine/risk/preflight_gate.py` in full. It has its own `gross_exposure_usd` /
`net_exposure_usd` trigger keys (`MaxGrossExposureTrigger`/`MaxNetExposureTrigger` → field-name mapping, lines
113-114, 184-185) but **contains no import of, or call into, `ExposureAggregator` or
`exposure_aggregator`** — grepped directly, zero hits. Same-named fields, no cross-service consumption found. This
is the fourth instance of the "declared-but-unwired" / dual-path shape `service_config_ownership_and_instruction_contract_2026_08_12.md`'s
J-register already tracks (alongside `WalletMappingConfig`, `ClientsYaml`, `ExecutionPolicyArtifact`) — a
same-named field on both sides with no verified single source of truth between them. Whatever populates
`gross_exposure_usd`/`net_exposure_usd` in execution-service's `RuleEvalContext` today is either a separate,
possibly-diverging computation, or unpopulated — not yet traced to its source in this pass.

**Trace completed 2026-08-19 (cross_cutting_satellite_ao_dispatch_batch18 item 2, slot 7, independent code read)**:
the sole production call-site is `execution_service/engine/orchestrator.py:246` `execute_instruction`, which calls
`run_risk_preflight(instruction, reference_price=...)` with NO `account_state` — so `_copy_account_state_into_ctx`
never runs on the live path, `gross_exposure_usd`/`net_exposure_usd` are unpopulated, and `_can_evaluate` drops
`MaxGrossExposureTrigger`/`MaxNetExposureTrigger` rules for lack of the context key (silently skipped, not an
independent computation). Definite yes/no for this item: preflight_gate does NOT consume strategy-service's
`ExposureAggregator` (0 `ExposureAggregator`/`exposure_aggregator` hits repo-wide in execution-service).

## Reference position, credit ownership, and the generic per-position adjustment — resolved 2026-08-19

Operator-driven design session extending Layer 1/2 above. Core idea: **`reference_price` alone only tells
execution-service what the world looked like at instruction time — it doesn't tell execution-service whether its
own view of strategy's POSITION matches strategy's view.** A price can legitimately differ from the reference (the
underlying moved) but a position mismatch is a real integrity problem — the two services disagree about ground
truth, not about a moving market. This generalizes the price-only design in Layers 1-2 above into three added
pieces, all resolved this session:

### 1. `reference_position` — per-venue, on the envelope, mismatch reuses `RiskRuleConsequence`

> **CORRECTED 2026-08-19 (later revision, same day) — the shape below is SUPERSEDED.** The operator reviewed this
> while the client artefact was being drafted and ruled `dict[venue, Decimal]` incomplete: it solves the venue axis
> (needed for `SOR_AT_EXECUTION`) but not the instrument axis — a strategy instance can hold a universe of many
> instruments, not one. Operator's own framing: "a chain of them per instrument in the universe, so surely a vector
> of tuples." The venue-axis reasoning immediately below is NOT wrong, it's nested one level too shallow — see
> § "The reference triple is a vector per instrument, not a scalar per instruction" further down for the correction
> and the open questions it raises. Left in place rather than deleted, per this doc's own correct-in-place
> convention.

**Shape: `dict[venue, Decimal]`, matching `venue_constraints`'s existing shape** — RESOLVED over the alternative of
requiring `target_venue` to be set, specifically to stay meaningful under `venue_routing_mode: SOR_AT_EXECUTION`,
where the venue isn't chosen until execution time. Strategy states its believed position on every eligible venue;
whichever one SOR ultimately picks, execution-service can still check it against the venue it actually reads.

**On mismatch: reuse the existing `RiskRuleConsequence` vocabulary** (`BLOCK` / `SCALE_DOWN` / `MONITOR` /
`TEST_ONLY`, already the four outcomes `preflight_gate.py` supports for any fired `RiskRule`) rather than inventing
a second decision model. Default consequence is `BLOCK` (per the operator: "if it doesn't see the same position,
that's an issue"), but treating it as a `RiskRuleTrigger` means a specific rule config can downgrade it later
without a new mechanism. This is deliberately an INSTANT, per-instruction check — the same-instrument,
same-venue position execution-service already has to know to route the order at all — not a periodic
reconciliation (that is a separate, slower mechanism, § 3 below).

**The "hard rule" this rides on**: one strategy instance executes a given instrument on one venue, so the
same-instrument/same-venue position check is unambiguous — there is exactly one number on each side to compare.

### 2. Credit is strategy-owned and strategy-computed, execution-consumed

Extending Layer 2's `credit: {entry_threshold, abandon_threshold}` (already resolved as optional, a "flavor," not
mandatory): **strategy-service computes and owns the actual credit numbers**, execution-service just consumes
whatever is cached and decides HOW to act on it per its own algo config — the same intent-vs-mechanics split
`execution_policy_ref` already establishes elsewhere. Two worked examples from this session, both real archetype
shapes, neither requiring a new mechanism beyond what's already proposed:
- **Market-making**: credit expressed as a band width around the reference price (e.g. "stay within 1bp") —
  `entry_threshold`/`abandon_threshold` map directly.
- **Arbitrage**: credit expressed as a hard fire-or-don't threshold — only `entry_threshold` is meaningful,
  `abandon_threshold` can be unset (consistent with credit already being optional per-field, not just optional as
  a whole).

### 3. The generic per-position adjustment — one symmetric slope, on RAW position, NOT effective position

**Resolved: one symmetric bps-per-unit-of-risk coefficient** (not two asymmetric add/reduce slopes) — matches the
existing precedent of `QuoteInstruction.skew_on_inventory` being a single coefficient today, generalized off that
one field rather than inventing new shape. **Resolved: this coefficient applies against the RAW,
single-instrument/single-venue position — the same one `reference_position` reconciles against — not the
`ExposureAggregator`-computed effective/net position.** The strategy↔execution CONTRACT stays single-position; it
still SENDS whatever effective-position context it has, but nothing on the execution-service main path consumes it
for this purpose today.

**Effective position is real, but scoped to a different, explicitly-stubbed-for-now module**: the operator's own
framing — "when another instrument trades, you want a separate module in execution-service that is a quick
approximation of what strategy-service would do when it comes to the adjustment of position A based on position
B" — names a FOURTH, distinct mechanism from the three (DeltaProxyRepricer / arb-leg `LEADER_HEDGE` / this
per-position adjustment): a fast-path **cross-instrument position-impact approximator**, live inside
execution-service, that estimates how a fill in instrument B should move the acceptable adjustment on instrument
A, without waiting for strategy-service's own (slower) recomputation. Explicitly **relevant only where A and B are
non-fungible** — the worked examples: a cross-chain staked-basis leg, or options across different terms/strikes.
**This module is a stub for this pass, not a build** — only `ExposureAggregator`-style effective-position
awareness needs to live THERE, and it does not need to exist on the strategy↔execution schema contract at all.

**The named end-state, for the record**: strategy-service computes reference price / reference position / credit /
adjustment SLOWLY (its own tick cadence); execution-service's fast-path layer (DeltaProxyRepricer today,
the cross-instrument approximator once built) does the equivalent computation in REAL TIME off live market/trade
data from every venue and instrument it can see directly (not just the one instrument being traded), feeding a
final decision into the order-fill algorithm layer. Wiring the actual fast-data routes into that layer is
out of scope for this pass — same "put in the hooks, not the infrastructure" boundary the rest of this issue
already draws.

### 4. This is the SAME intent-vs-mechanism split the envelope already draws — restated for the new fields

Clarified 2026-08-19: `credit`, `reference_position`, and the per-position adjustment slope are all strategy-set
GOVERNING BOUNDARIES, not execution instructions — the identical relationship the existing `hedge_deadline_ms` on
`AtomicInstruction` already has with the algo layer today (strategy says "I don't want outright exposure for
longer than this"; the algo decides how it actually operates within that window). None of the three new concepts
change that split; they extend the same boundary vocabulary strategy already speaks, with execution's own
per-`(client_id, slot_label)` algo policy (§ B of `service_config_ownership_and_instruction_contract_2026_08_12.md`)
still deciding mechanics, same as it does for urgency and `execution_policy_ref` today.

### 5. Reconciliation cadence — the SAME idempotent re-emission channel, plus a separate SLA-based staleness escalation

**Resolved: no new transport.** The idempotent re-emission already proposed for refreshing `reference_price`/
`credit` doubles as the reconciliation heartbeat — every re-emit is also a fresh instant position check (§ 1
above) once execution-service has processed intervening fills. **A second, explicitly slower mechanism catches
what the fast check can't**: strategy-service should track, per venue (SLA duration is venue-dependent, not a
single global constant), whether it has SEEN the trades/position-updates it expects to receive back from
execution-service within that SLA window. If not — "execution-service thinks it's trading, and strategy-service
isn't seeing it" — that is the trigger for a heavier reconciliation pass, separate from and slower than the
per-instruction instant check, and it must never block or slow down execution-service's own fast path (it is a
strategy-side, asynchronous watch, not a gate execution waits on).

## The reference triple is a vector per instrument, not a scalar per instruction — corrected 2026-08-19

**Operator ruling, same day, later revision — corrects § "Reference position, credit ownership..." above where it
conflicts.** While drafting the client-facing artefact, the operator reviewed the `dict[venue, Decimal]` shape
resolved above for `reference_position` and ruled it incomplete: it solves the venue axis but not the instrument
axis. A strategy instance can hold a universe of many instruments at once — a single `reference_price`, a single
`reference_position: dict[venue, Decimal]`, and a single `credit` on the envelope can only ever describe ONE
instrument's reference state, however the venue axis inside `reference_position` is shaped.

### The shape was already half-right, earlier in this same document

Layer 2's `ExecutionSensitivityEntry` design (§ "The generic contract this session's design settled on," above)
already proposed exactly this instrument-axis vector, for the price/sensitivity pair:

```
references: list[{ instrument_id, reference_price, sensitivity_coefficient, second_order_coefficient? }]
# N=1 is MM/options (one underlying). N=2 is the arb-leg case. A basket/multi-leg options
# structure is just a longer list — same shape, no later schema rewrite.
```

The "Reference position, credit ownership..." section, added later the same day, did not build on that list — it
bolted `reference_position`/`credit` onto the envelope as flat, single-instrument fields instead, quietly
regressing to the scalar shape Layer 2 had already moved past. That is the actual defect the operator caught, not a
requirement invented from nothing.

### Proposed shape (illustrative — not finalized; this is what needs resolving, not what's decided)

The natural fix nests `reference_position` and `credit` INTO each entry of the list Layer 2 already proposed,
keeping the venue axis inside each instrument entry rather than flattening the whole thing:

```
class InstrumentReferenceEntry:
    instrument_id: str
    reference_price: Decimal
    reference_position: dict[str, Decimal]  # per-venue — the venue-axis resolution above stays correct,
                                             # just nested one level deeper
    credit: CreditBand | None = None
    position_adjustment_bps_per_unit_risk: Decimal | None = None
    sensitivity_coefficient: Decimal | None = None       # ties back into Layer 2's ExecutionSensitivityEntry
    second_order_coefficient: Decimal | None = None

# proposed addition to StrategyInstructionEnvelope
references: list[InstrumentReferenceEntry] = []
```

Every design decision already made in this doc stays intact — the per-venue dict still exists and still serves
`SOR_AT_EXECUTION`; `credit` is still optional and still strategy-owned; the symmetric bps-per-unit-risk coefficient
still applies to RAW position — this just nests them one level under a per-instrument list instead of the flat
envelope. It is explicitly NOT the final word: which container this list lives on, and how it reconciles against
`QuoteInstruction.reference_price: Decimal` (currently REQUIRED — narrows the envelope's optional field, a
single-instrument override that itself assumes a scalar) is unresolved.

### OPERATOR RULING 2026-08-21 — Q12-Q16 answered IN THE LEGACY FRAMING; implement THROUGH the factor-state model

**Scope correction, same day**: Q12-Q16 were already superseded by the factor-state model (§11-16) and its codex
SSOT `/codex/04-architecture/cross-domain-state-fabric.md` (R1-R16) before this ruling was recorded. The answers
below are durable DIRECTIONAL signal — they refine, and are consistent with, the fabric contract — but the
implementation shape is the fabric's snapshot/factor-state contract (per-instrument J_i/H_i/Theta_i against
canonical factors, reference positions and the A-matrix in the versioned snapshot with watermarks), NOT literal
scalar delta/gamma/theta fields on `StrategyInstructionEnvelope`. Q3 (position vectors) is RESOLVED as fabric R22 — three vectors, opt-in per archetype, q_worst venue-derived — reconfirmed by operator 2026-08-21. Genuinely-still-open: the five Wave-0 rulings, carried in the codex doc.

- **Q12**: the vector `references: list[InstrumentReferenceEntry]` is the ONE home on
  `StrategyInstructionEnvelope`; N=1 is a list of one; no envelope-level scalar duplication. Each entry is the
  full per-instrument reference matrix for the strategy instance's universe: `reference_price`, per-venue
  `reference_position`, `credit`, `position_adjustment_bps_per_unit_risk`, `sensitivity_coefficient` (delta),
  `second_order_coefficient` (gamma), and — added by this ruling, operator named it explicitly — an optional
  `time_decay_coefficient` (theta). `QuoteInstruction.reference_price` reconciles to the vector (single-
  instrument override narrows the list-of-one, not a parallel scalar).
- **Q13**: venue axis nested per-instrument (no `(instrument_id, venue)` cross-product); the one-venue-per-
  instrument-per-instance hard rule stands.
- **Q14**: `credit` is per-entry (independent thresholds per arb leg), still optional and strategy-owned.
- **Q15**: the new position-mismatch `RiskRuleTrigger` subtype evaluates PER ENTRY
  (BLOCK/SCALE_DOWN/MONITOR/TEST_ONLY per entry, default BLOCK); needs the UAC PR per risk-rule-taxonomy.md.
- **Q16**: `position_adjustment_bps_per_unit_risk` is per-entry.

### Open questions for the operator — do not resolve unilaterally

12. **Does `references: list[InstrumentReferenceEntry]` live on `StrategyInstructionEnvelope` directly, or does the
    envelope keep single-instrument convenience fields (today's `reference_price`) for the common N=1 case, with the
    vector reserved for cases that actually need N>1?** Duplicating the shape in two places is worse than picking
    one; recommend the vector as the ONE home, with N=1 as the trivial list-of-one case — but `QuoteInstruction`
    narrowing `reference_price` to required today would need to change too.
13. **Is the venue axis nested per-instrument (as drafted above), or does the vector need a full
    `(instrument_id, venue)` cross-product** — can a strategy legitimately hold different believed positions on the
    SAME instrument across different venues within one instruction's reference state? The existing "hard rule" (one
    strategy instance executes a given instrument on one venue) suggests nesting is sufficient, but that rule
    predates the vector shape — worth re-confirming once N>1 instruments are in play.
14. **Does `credit` vary per-entry, or is one credit policy shared across the whole vector?** Moot for N=1; for the
    arb-leg N=2 case, do the two legs carry independent thresholds, or one shared band?
15. **Does the position-mismatch `RiskRuleTrigger` (todo below) fire once per instruction or once per vector
    entry?** Verified this session: none of the 13 existing `RiskRuleTrigger` subtypes
    (`/codex/04-architecture/risk-rule-taxonomy.md`) covers a position/reference mismatch — adding one needs a UAC PR
    regardless of scalar-vs-vector shape, per that doc's own "adding a new trigger requires a UAC PR" rule; the
    vector shape changes whether the new trigger's required-field shape is per-instruction or per-entry.
16. **Does `position_adjustment_bps_per_unit_risk` also move per-entry**, now the shape is proven multi-instrument,
    rather than staying one coefficient for the whole instruction?

Default lean, stated for the record, not as a ruling: the vector is the one home (no envelope-level duplication),
venue nested per-instrument (not a full cross-product), credit per-entry, the new `RiskRuleTrigger` subtype
evaluates per-entry, and the adjustment coefficient moves per-entry too — all following the "the vector was already
right in Layer 2" reasoning above.

## Side-finding: DeFi liquidation monitoring has the same "fast trigger, not slow poll" pattern this issue is about

Verified 2026-08-19 while correcting `codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html`
§03's `carry_staked_basis` config example per a separate operator ruling — noted here because it's the same lesson
this whole issue documents (execution-side reaction without a strategy-side round trip), just for DeFi liquidation
risk. `execution_service/defi_execution/monitors/health_factor_monitor.py`'s `HealthFactorMonitor` (near-block-time
per-chain poll/WS loop) and `execution_service/algo_library/deleverage_executor.py`'s `DeleverageExecutor`
(MarginEvent-driven auto-deleverage) are both real, substantial code — but `HealthFactorMonitor(` has zero
constructor call sites found in execution-service outside its own module this pass, the same "declared-but-unwired"
shape documented elsewhere in this issue. Separately, `strategy_service/configs/carry_staked_basis.yaml`'s
`strategy_id` carries a stale `_SCE_1H` suffix — `hold-policy.md` rules DeFi strategies "NEVER SCE"; the config's
functional `execution_mode: continuous` field is correct, only the id string is wrong, and the same suffix recurs
across several other DeFi configs (grepped, not exhaustively enumerated). Neither fixed here — strategy-service is
outside this pass's owned files. Tracked as todos below.

## Fast-loop cadence vs. strategy's refresh cadence — two different speeds, one already named

`QuoteInstruction.refresh_cadence_ms` already names how often STRATEGY refreshes the cache. Execution-service's own
loop (reading live ticks and re-evaluating the cached entry) runs on a genuinely different, faster cadence — often
continuous/tick-driven, not timer-based. These should stay two explicit, separately-named concepts, not conflated
into one field. This connects directly to the per-archetype `topology_requirements.co_location`/`latency_budget_ms`
fields already declared on every archetype's codex doc (confirmed this session: 58 of 60 archetypes declare this)
— that field is the existing mechanism that should determine which venues/positions an execution-service instance
can read on its OWN fast path (co-located) versus which require a network hop back to strategy-service or another
execution-service instance (not co-located) — the exact distinction the operator drew between "tick moves in venues
I subscribe to directly" and "positions/moves that happen in other instruments/deployments."

## Explicit non-goal for this pass

The immediate ask is that the Python code's SHAPE (the abstractions, the layer boundaries, the schema) accommodate
future co-location, multi-region execution-service instances cross-communicating on price moves and positions, and
eventually a hot-path migration off Python — NOT to build any of that now. "Put in the hooks" — verified by
confirming the shape exists or is missing at each layer above — is the deliverable for this pass; the
infrastructure investment is future work, sequenced separately.

## Per-archetype MEV applicability — do not apply this uniformly

- **`BACKRUN`**: reacts to a confirmed block-N swap sometime before block N+1 closes — on Ethereum, a ~12-second
  window. The existing `EventTransport` seam is very likely adequate once the opportunity-detection calculator
  (tracked in the MEV doc) exists. **Not measured** — reasoned from the archetype's own tolerance window, not a
  benchmark. See the REVIEW todo below.
- **`LIQUIDATION_BUNDLE`**: winning the race against other liquidators is execution-service's job (RPC/relay speed
  via the already-real `v2/mev_router.py`), not a repricing problem. Same conclusion as BACKRUN.
- **`JIT_LIQUIDITY`**: the best fit — but applying this pattern does **not** by itself resolve its deeper gap (zero
  real pending-swap signal, tracked in the MEV issue doc). This pattern only lets it react faster once it has
  something real to react to.

## Judgment calls for the operator — only #6 resolved this session

1. **One credit threshold or two, independently tunable?** `entry_threshold` (minimum edge to act) vs.
   `abandon_threshold` (max adverse move tolerated once committed) may want genuinely different magnitudes, not a
   mirror-image pair.
2. **Does every trigger reduce to a price-sensitivity comparison?** `LIQUIDATION_BUNDLE`'s health-factor and
   `JIT_LIQUIDITY`'s pending-swap-size are state thresholds, not literally "price moved by delta×X." Does
   `watched_field` support non-price fields from day one?
3. **Fixed 2-leg shape now, or an arbitrary list from day one?** Recommend list — the N=1/N=2 cases are trivial
   instances, and this session already found multi-underlying portfolio math (`GreekTargets`) elsewhere.
4. **How is "never branch on archetype" enforced** — convention, or is `provenance` structurally excluded from the
   object the algo's own function signature receives?
5. **Staleness default** — inherit the epic's 2026-08-18 W16 fail-closed ruling as-is, or does a brand-new schema
   need its own explicit ruling?
6. **RESOLVED this session: credit-tolerance is optional, a flavor of Layer 2's behavior — never a mandatory field.**
7. **Should an automated, strategy-triggered instruction get access to true `MARKET` execution** (today
   `MANUAL_ONLY`, excluded from the canonical selector for backtest-realism reasons) once it has already cleared a
   real, live credit/trigger check — does the backtest-realism concern still apply at that point?
8. **Does Layer 2 need to explicitly select among the three parallel execution paths** (canonical
   `algorithms/selector.py`, `atomic_leg_executor.py`, `v2/mev_router.py`), or is a fourth, unifying router worth
   building — given the three serve genuinely different settlement models (single order / atomic multi-leg /
   on-chain bundle)?
9. **Should the new generic contract reuse `order_semantics.py`'s existing vocabulary directly**
   (`TimeInForce.POST_ONLY`, `RefPricingMode.DELTA_ADJUSTED_TO_UNDERLYING`, `MultiLegDeltaOwner`) rather than
   inventing parallel concepts in a separate schema — given it is already a real, per-venue, cited gap registry
   covering nearly this exact surface?
10. **Does execution-service's `engine/risk/preflight_gate.py` need to consume strategy-service's
    `ExposureAggregator`-computed net/"effective" exposure** via a network call, given `topology_requirements`
    co-location means the two may not always be deployed together — or is a simpler, execution-service-local view
    sufficient, with the gap named explicitly rather than assumed away?
11. **Is `POST_ONLY` enforcement genuinely composable** — algo-level self-check (approximate via live tick data
    before submitting) AND venue-level native order-type flag, usable independently or together, as the operator's
    own framing implied — recommend yes, modeled as two independent fields (matching `VenueOrderSemantics`'s
    existing `honored_tif`/`post_only` split), not an either/or.

Default lean on all eleven, stated for the record, not as a ruling: independent thresholds, non-price triggers in
scope, list-shaped references, structural provenance separation, inherit fail-closed, MARKET available once a real
trigger has fired, explicit per-path routing over a premature fourth router, reuse `order_semantics.py`'s vocabulary
rather than duplicate it, execution-service reads the real aggregator rather than duplicate exposure logic, and
POST_ONLY as two independently composable fields.

## Todos

- [ ] [DESIGN] P1. **Design `ExecutionSensitivityEntry` + `AmbientMarketLean`**, resolving judgment calls 1-5 and 9
      above. Extend UAC's `QuoteInstruction` narrowly, or author the new asset-group-agnostic schema proposed in
      this doc — and decide whether it should literally extend `order_semantics.py`'s `VenueOrderSemantics` pattern
      rather than live as a separate module. Real design call, not mechanical — resolve locally first.
- [ ] [BACKEND] P1. **Rebuild the strategy-side QUOTE-instruction receipt path.** Register directly against
      `QuoteMaintainer.register_quote_instruction()` per its own docstring guidance, not a resurrected router. Lets
      `MARKET_MAKING` archetypes populate `DeltaProxyParams` even before the schema extension lands.
- [ ] [BACKEND] P1. **Build the live underlying-tick ingestion loop** via the standard `EventTransport` facade,
      driving `QuoteMaintainer.on_underlying_tick()`. Wiring, not new data-access infrastructure — candidate feeds
      already exist (`l2_depth_provider.py`, venue websockets).
- [ ] [BACKEND] P2. **Extend the contract with real distinct-underlying delta/gamma**, sourced from `greeks-service`
      (real Black-Scholes greeks, currently written to `LedgerRow.option_delta`/`gamma` and consumed by nothing).
      Depends on the design todo above.
- [ ] [DESIGN] P2. **Design the arb-leg-repricing analog** for `price_dispersion.py`/`atomic_leg_executor.py` —
      replace the fixed-price + zero-slippage + time-deadline hedge mechanism with an optional live credit-band
      reprice, wiring the currently-unused `MultiLegDeltaOwner` enum to something real.
- [ ] [STRATEGY] P2. **Apply the pattern to `JIT_LIQUIDITY`** once the above lands — explicit restated caveat: does
      NOT resolve its mempool-visibility gap (tracked separately), only lets it react faster once a real signal
      exists.
- [x] ✅ [REVIEW] P2. **Measure this deployment's real `EventTransport`/Pub/Sub round-trip latency** before permanently
      ruling out this pattern for `BACKRUN`/`LIQUIDATION_BUNDLE` — today's "12s block budget is generous enough" is
      reasoned, not measured. **EXTRACTED 2026-08-19 (na-eligibility-audit, cross-cutting tranche, conflict-check
      clear)** — see `cross_cutting_satellite_ao_dispatch_batch18_2026_08_19.md` item 1.
- [ ] [BACKEND] P2. **Extend `ExecutionPolicyResolver`/`algorithms/selector.py` with an
      actionable-given-current-price-move gate** — today `DeltaProxyRepricer`'s `stale=True` just silently clamps
      with no re-route, the same class of gap the epic's W16 fail-closed ruling already names.
- [ ] [DESIGN] P2. **Resolve judgment call 7** — should a strategy-triggered instruction gain access to real
      `MARKET` execution (today `MANUAL_ONLY`) once a live credit/trigger check has already fired?
- [ ] [REVIEW] P2. **Audit which instruction_types Layer 2 will ever emit and confirm none silently hits a GHOST
      algo** (`BEST_PRICE`/`SEQUENTIAL_LEGS`/`SPREAD_ROLL`/`KELLY_STAKE` — no implementation class, fails loud via
      `ValueError`) through the canonical `algorithms/selector.py` — build the missing implementation, or route
      those instruction types through their existing bespoke path (e.g. `atomic_leg_executor.py`) instead.
- [ ] [DESIGN] P2. **Resolve judgment call 8** — does Layer 2 need explicit per-path routing among the three
      parallel execution paths, or is a fourth unifying router worth its cost?
- [ ] [BACKEND] P2. **Wire `RefPricingMode.DELTA_ADJUSTED_TO_UNDERLYING` and `TimeInForce.POST_ONLY` end-to-end for
      at least one real venue** — today zero venues have either wired, per `VENUE_ORDER_SEMANTICS`'s own honest gap
      registry. This is the formal, already-declared name for the pattern this whole issue is about; wiring it real
      for one venue is arguably the cleanest first concrete deliverable, ahead of the broader generic-contract work.
- [x] ✅ [REVIEW] P2. **Confirm whether execution-service's `engine/risk/preflight_gate.py` reads strategy-service's
      real `ExposureAggregator`-computed net/effective exposure**, or maintains an independent view — resolve
      judgment call 10 with a real answer, not an assumption. **EXTRACTED 2026-08-19 (na-eligibility-audit,
      cross-cutting tranche, conflict-check clear)** — see `cross_cutting_satellite_ao_dispatch_batch18_2026_08_19.md`
      item 2.
- [x] ✅ [AGENT] P3. **Resolve the dead `feedback_market_making_reference_price_model.md` reference** cited by both
      `vol_trading/options.py` and `quote_maintenance.py`'s docstrings — confirmed not to exist anywhere in
      `unified-trading-pm`. Either this issue doc becomes the real record (repoint both docstrings here) or the memo
      should be authored for real if it once existed elsewhere and was lost. **EXTRACTED 2026-08-19
      (na-eligibility-audit, cross-cutting tranche, conflict-check clear)** — see
      `cross_cutting_satellite_ao_dispatch_batch18_2026_08_19.md` item 3.
- [ ] [DESIGN] P1. **SUPERSEDED 2026-08-19 (later revision, same day).** ~~Design and add
      `reference_position: dict[venue, Decimal]` to `StrategyInstructionEnvelope`~~ — the scalar-per-instruction
      shape was ruled wrong (see § "The reference triple is a vector per instrument..."); the venue-axis reasoning
      survives, nested one level deeper inside a per-instrument vector. Superseded by the next todo.
- [ ] [DESIGN] P1. **Design `InstrumentReferenceEntry` + `references: list[...]`** on `StrategyInstructionEnvelope`
      (or reconcile it with Layer 2's `ExecutionSensitivityEntry.references`, which already proposed this exact
      per-instrument list shape) — resolves judgment calls 12-16. Must reconcile against
      `QuoteInstruction.reference_price: Decimal`'s existing required-field narrowing.
- [ ] [BACKEND] P1. **Wire the position-mismatch check as a `RiskRuleTrigger`** consumed by `preflight_gate.py`,
      reusing the existing `RiskRuleConsequence` vocabulary (`BLOCK`/`SCALE_DOWN`/`MONITOR`/`TEST_ONLY`), default
      `BLOCK`. **Note 2026-08-19 (later revision): scoped per-entry of the `references` vector (judgment call 15),
      not per-instruction — verified none of the 13 existing `RiskRuleTrigger` subtypes covers this, so it needs a
      UAC PR, not a pure consumption of an existing subtype.**
- [ ] [BACKEND] P2. **Add a `position_mismatch` `RiskRuleTrigger` subtype via a UAC PR** — verified 2026-08-19 that
      none of the 13 existing typed subtypes (`/codex/04-architecture/risk-rule-taxonomy.md`) covers a
      reference-position mismatch; the closed union requires a UAC PR to extend, per that doc's own anti-patterns
      section (`unified_api_contracts/canonical/crosscutting/risk_rule/_triggers.py`).
- [ ] [DESIGN] P2. **Design the generic per-position adjustment field** (one symmetric bps-per-unit-of-risk
      coefficient, applied against the RAW single-instrument/single-venue position) on the shared envelope,
      generalizing off `QuoteInstruction.skew_on_inventory` rather than inventing new shape. **Note 2026-08-19 (later
      revision): now likely per-vector-entry (judgment call 16), not per-instruction — unresolved.**
- [ ] [AGENT] P2. **Trace whether `HealthFactorMonitor`/`DeleverageExecutor` are wired to a real production
      entrypoint** (service bootstrap constructing the monitor per-chain; a real Pub/Sub subscription calling
      `deleverage_executor.handle()`) or are declared-but-unwired like the rest of this issue's findings.
- [ ] [BACKEND] P3. **Fix the stale `_SCE_1H` suffix on DeFi strategy_ids** (`carry_staked_basis.yaml` and siblings)
      — DeFi is never SAME_CANDLE_EXIT per `hold-policy.md`; rename to the correct hold-policy abbreviation across
      the config, `close_all/__init__.py`'s dispatch dict, and `close_all/carry_staked_basis.py`'s `STRATEGY_ID`
      constant together (a rename needs every consumer migrated in the same change).
- [ ] [DESIGN] P3. **Stub — do NOT build — the cross-instrument fast-path position-impact approximator** in
      execution-service (estimates how a fill in instrument B should move the acceptable adjustment on instrument
      A, for non-fungible pairs only: cross-chain staked-basis legs, cross-term/cross-strike options). This is
      where `ExposureAggregator`-style effective-position awareness belongs — NOT on the strategy↔execution
      contract itself. Explicit non-goal for this pass, tracked so it isn't lost.
- [ ] [BACKEND] P2. **Build the SLA-based staleness reconciliation escalation** — strategy-side, venue-dependent
      watch for whether expected trades/position-updates have arrived back from execution-service within an SLA
      window; separate from and strictly slower than the per-instruction instant `reference_position` check; must
      never block or slow execution-service's own fast path.
- [ ] [AGENT] P2. **Trace what currently populates execution-service's `gross_exposure_usd`/`net_exposure_usd`
      `RuleEvalContext` fields**, given the confirmed-2026-08-19 finding that `preflight_gate.py` has zero
      `ExposureAggregator` imports — either wire it to the real aggregator, or document the independent
      computation explicitly so the two same-named fields stop reading as one source of truth.
- [ ] [INFRA] P2. **Provision the EventTransport seam's `-reader` pull subscriptions** (`persist-{ag}-{dt}-reader`)
      — confirmed absent 2026-08-19 (measurement run, slot 14): production `persist-*` topics carry only
      `warm-sink-*` GCS push subscriptions, so `PubSubTransport.read()` fails against them today. Includes
      provisioning the missing `persist-all-atomic-instruction` topic (already a known codex gap) so the
      strategy→execution seam is actually readable in live.
- [ ] [REVIEW] P2. **Re-evaluate the BACKRUN / LIQUIDATION_BUNDLE "12s block budget is generous enough" reasoning
      with the measured transport cost** — measured 2026-08-19 (slot 14, `unified-trading-library@418ce99c`):
      EventTransport `PubSubTransport` publish→receive round-trip ~2.2–2.7s median / ~4.7–5.0s p95 / ~4.9–5.0s max
      (n=20 × 2 runs, ephemeral topic on `central-element-323112`) = ~18% median / ~39–42% p95–max of the 12s window
      before strategy detection / execution / relay are counted. The per-archetype MEV-applicability §'s "very likely
      adequate" claim needs updating or a fast-path latency budget.

## Progress Log

**2026-08-18 — filed and substantially deepened across one extended interactive session.** Started from a single
MEV-latency question and grew into a full 3-layer design (strategy intent / execution sensitivity cache / order-fill
algorithm) after the operator pushed on CeFi-execution analogies, the generic "credit"/delta concept across arb
legs and options, and finally the code-shape-for-future-infrastructure framing. Every claim verified by direct file
read this session (`delta_proxy_repricer.py`, `quote_maintenance.py`, `atomic_leg_executor.py`,
`prediction_venue_dispersion.py`, `algorithms/selector.py`, `order_semantics.py`, `exposure_aggregator.py` — all
read in full, not summarized secondhand), not taken on a research agent's word alone. 11 judgment calls now stand
for the operator, one resolved (credit-tolerance is optional). Nothing in the Todos section has been built yet.

- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): RECLASSIFY per-todo split — 3 of 14 open todos
  (latency measurement, a preflight_gate fact-check, a dead-doc-reference cleanup) are pure read/measure/cleanup
  tasks independent of the 11 unresolved operator judgment calls and touch no live-execution behavior; extracted to
  `cross_cutting_satellite_ao_dispatch_batch18_2026_08_19.md`. The other 11 stay KEEP-NA — genuine design/judgment
  work or explicitly dependent on it, appropriately NA given this is live execution-critical-path (order
  pricing/repricing) machinery. Doc's own `assigned_vm: NA` unchanged.
- **context-scout 2026-08-19**: populated context_scope (6 entries).

**2026-08-19 — extended with `reference_position` + credit ownership + generic per-position adjustment, while
drafting the strategy-service deep-dive client artefact.** Judgment call 10 moved from "unconfirmed" to
CONFIRMED: `preflight_gate.py` has zero `ExposureAggregator` imports. Four new operator design decisions resolved
(§ "Reference position, credit ownership, and the generic per-position adjustment"): `reference_position` is a
per-venue dict on the envelope, mismatch reuses `RiskRuleConsequence` (default `BLOCK`); credit is strategy-owned
and strategy-computed; the per-position adjustment is one symmetric bps-per-unit-of-risk coefficient against RAW
position, with effective/net-position awareness explicitly scoped OUT to a new, stub-only, execution-internal
cross-instrument position-impact module (non-fungible pairs only); reconciliation reuses the same idempotent
re-emission channel plus a separate, slower, venue-dependent SLA staleness escalation that never blocks
execution's fast path. Also confirmed: all of this sits at the same intent-vs-mechanism boundary
`hedge_deadline_ms`/`execution_policy_ref` already draw — strategy sets governing boundaries, execution's own algo
policy decides mechanics within them. 6 new todos added. Nothing built yet; this session's output is design only.
`codex/14-customer-journeys/commercial-model/strategy-service-deep-dive.html` §02 is being updated to reflect this
as explicit target-state (`planned`/`assumed` grading), not as a live claim.

**2026-08-19 — corrected per two operator rulings while updating the client-facing artefacts.** (1) The
`reference_position`/`credit` shape resolved earlier the same day was WRONG: it solved the venue axis but not the
instrument axis. Corrected in § "The reference triple is a vector per instrument, not a scalar per instruction" —
folds `reference_position`/`credit` into the `references: list[...]` shape Layer 2 already proposed, rather than
the flat envelope fields added later. 5 new judgment calls (12-16), none resolved, explicit default leans stated.
Verified along the way: none of the 13 existing `RiskRuleTrigger` subtypes covers a position mismatch — a new
subtype needs a UAC PR, not just consumption of an existing one. (2) While correcting the artefact's
`carry_staked_basis` config example (a separate operator ruling — the example wrongly implied same-candle-exit),
verified the real DeFi liquidation-trigger path: `HealthFactorMonitor` (near-block-time per-chain monitor) and
`DeleverageExecutor` (MarginEvent-driven auto-deleverage) are real code, decoupled from the strategy's own `1h`
config timeframe (which is a feature/backtest bar resolution, not a risk cadence) — but `HealthFactorMonitor`
appears to have zero production callers in this pass. Also found: the config's `_SCE_1H` strategy_id suffix is
stale (DeFi is never SAME_CANDLE_EXIT per `hold-policy.md`); the functional `execution_mode: continuous` field is
correct. Neither the wiring gap nor the naming mismatch was fixed here (out of this pass's owned files); both
tracked as new todos. Nothing in either correction was built — design/finding only.

### 6. UNDERLYING is a first-class axis — reference price is per underlying, not per instrument

Operator ruling 2026-08-20, refining sections 1-3 above.

**Reference price is NOT one per instrument.** Many instruments move off the same underlying:

- A thousand option instruments all move on their sensitivity to **one** underlying.
- A base strategy per coin underlying — BTC; or ETH versus staked ETH versus wrapped ETH — where every leg shares
  the **same ETH underlying**.

So the structure factorises:

| Level | Carries |
| ----- | ------- |
| **Underlying** (M of them) | the **reference price** |
| **Instrument** (N of them, N >> M) | its **delta / gamma / theta sensitivity to that underlying**, plus credit and adjustment |

**Why this matters for the fast path — the point of the ruling.** One move in an underlying can be propagated to
every instrument that references it, via each instrument's own sensitivity approximation. Execution therefore does
**far less work per tick**: it recomputes from M underlying moves rather than maintaining N independent reference
prices. The operator's words: *"it just means you have to put less effort in execution services to do the
approximation on the fast path, because one move in an underlying can affect more than one instrument."*

**This generalises what `DeltaProxyRepricer` already does.** Its existing arithmetic is already underlying-shaped —
`effective_delta = delta + gamma * underlying_move`, `price_adjustment = underlying_move * effective_delta`. And
the current wiring's known limitation is precisely the degenerate case of this model: `QuoteInstruction` defaults
`underlying_instrument_id = instrument` and `delta = 1.0`, i.e. every instrument is its own underlying with unit
sensitivity — correct for spot/perp self-underlying, wrong for everything else. This ruling is the general case
that defaulting was standing in for.

**Open design question worth settling before build — the matrix and the underlying factorisation overlap.**
Instruments sharing an underlying are already near-maximally coupled through their deltas, which is the
correlation = 1 case of § 4. So the N x N adjustment matrix and the underlying model express overlapping
information. Decide explicitly whether: (a) the matrix subsumes the underlying axis, (b) the underlying axis
carries the shared component and the matrix carries only the **residual / cross-underlying** correlation, or
(c) both are maintained independently. Option (b) is the natural reading of this ruling and would shrink the
matrix substantially — but it must be a decision, not an accident. Building both independently would duplicate the
same concern in two places.

- [ ] [DESIGN] P0. **Make underlying a first-class axis in the cache design** — reference price keyed by
      underlying, per-instrument sensitivity (delta/gamma/theta) referencing it. Supersedes any per-instrument
      reference-price shape.
- [ ] [DESIGN] P0. **Rule on the matrix-vs-underlying overlap** (options a/b/c above) before either is built.
- [ ] [BACKEND] P1. **Retire the `underlying_instrument_id = instrument`, `delta = 1.0` default** once the general
      model lands — it is the self-underlying special case, and leaving it as a silent default will hide missing
      sensitivity data exactly the way other silent fallbacks have this week.

### 11. FACTOR-STATE MODEL — adopted direction, 2026-08-20 (supersedes parts of sections 3-10)

An external HFT-practice document was reviewed against this design. Its central idea is **stronger than the
suppression rule we were about to specify**. Recorded here because it changes several earlier rulings.

**The unified fair-value function.** Do not treat premium, greeks and position adjustment as separate instructions
with separate reaction rules. The slow path publishes a versioned approximation of the whole reservation-price
function; the fast path holds two mutable inputs — market-factor displacement `Dz` and position displacement `Dq`:

```
F_i(t) = U_i0 + J_i.Dz + 0.5 Dz' H_i Dz + Theta_i.Dt + a_i0 + [A Dq]_i + c_i
   where Dz = z_hat_t - z_0 ,  Dq = q_t - q_0 ,  Dt = t - t_0
```

No more "Binance moved therefore move OKX" / "position changed therefore add adjustment" / "time passed therefore
decay". Those events merely update state variables in one function.

**Canonical FACTORS, not per-venue prices — this dissolves double-reaction.** `Dz` must NOT be each venue's raw
price change; that recreates the problem. The vector is common-BTC, USDT/USD, KRW/USD, CME basis, perp/funding
basis, per-venue transient basis residuals, vol factors. A Binance move updates the *posterior* on common BTC
(+$75, not +$100, because OKX already moved $20). When OKX catches up the observation is already predicted, `Dz`
barely changes, and **the greeks do not fire twice**. No debounce, no per-venue-pair threshold. Explicitly rejects a
crude price+time debounce in favour of computing residual innovation.

**Supersedes section 10's primary/correlated split**: all venues load onto canonical factors; defensive vs
aggressive becomes a **confidence threshold on `(F_i, sigma_F_i)`**, not a second mechanism. Upbit does not move
common BTC one-for-one — part loads onto KRW and Korea-local-premium factors.

**Transmit states, not reactions.** Hot messages carry *absolute* factor state with epoch + sequence, not deltas.
Newer replaces older; a missed packet heals on the next image. Over UDP that beats any retransmit scheme.

**A is position-independent (operator ruling) but NOT market-independent.** An option position's delta moves with
the underlying; inverse-contract risk per unit moves with price. Needs cross-tensors `A^(k)` for important factors,
or a tighter trust region forcing earlier refresh. OPEN — section 15.

**Snapshot watermarks are a CORRECTNESS requirement.** Snapshot carries generation, reference time/factors/
positions, per-venue fill watermarks, market-data watermarks, coefficient version, basis-model version. Without the
fill watermark, fills landing while a snapshot is in flight are double-applied or dropped, silently. Rebase =
verify monotonic generation -> replay only events after the watermarks -> evaluate new snapshot at CURRENT state ->
compare against old model at the same state -> quarantine unexplained discontinuity -> atomic switch.

**Validity envelope** (concrete form of our warn/error thresholds): max |Dz_k|, max |Dq_j|, max Dt, per-output
approximation error, supported source-health regimes, hard expiry. Outside it: request refresh, disable aggression,
widen/withdraw passive, keep defensive cancellation while the stale approximation stays conservative.

**Absolute recomputation is the correctness backstop** — incremental column updates for speed, periodic full
re-evaluation from the immutable snapshot to stop numerical drift.

**Repricing thousands of options cheaply.** Precompute per option the next upper/lower underlying levels at which
its bid tick, ask tick, size tier or cancel/replace policy changes; a small move recomputes only instruments whose
thresholds crossed; SIMD/SoA scan for large or multi-factor shocks. **Publish only when the desired ORDER STATE
changes** (price >=1 tick, size, cancel/replace, risk permission). Illustrative: 128-byte factor state at 20k/s is
~2.56 MB/s per receiver; 5,000 option values at 16 bytes would be ~1.6 GB/s. Ship the model once, compute locally.

**Feed arbitration.** No single "fastest feed" — choose per (venue, instrument, event class, regime, action). Race
*exact duplicates* by venue sequence/event id (CME A/B: process first valid, discard processed, recover on gap).
*Complementary* feeds are conditioned, not discarded: a later BBO confirming a trade contributes ~zero price
innovation but may reduce uncertainty and unlock aggression. Measure pairwise lead using local monotonic NIC/kernel
receive timestamps, never exchange clocks.

**Per-colo factor engine.** No central global fair everyone waits for. Venue-local adapters decode and de-duplicate;
compact source observations cross the WAN; each colo fuses remote observations with its faster local feed and
publishes its own factor state locally. Regions legitimately hold different information sets at the same instant.

**Cloud multicast billing may invalidate part of section 10.** Cited: AWS Transit Gateway bills per-receiver data
processing and warns TGW multicast may not suit HFT; GCP charges multicast infrastructure/processing and has no
cross-region multicast. If so, multicast cuts producer serialisation and NIC bandwidth while billed bytes still
scale with receivers -> transport becomes substrate-conditional (colo L2 -> multicast; cloud -> reconsider).
**VERIFY BEFORE BUILDING.**

**Also verify**: quoted venue feed specifics (Binance ~20ms incremental depth / 50ms top-20, OKX 10ms BBO +
tick-by-tick, Coinbase 250ms trade aggregation). Venue-specific, time-varying, and the arbitration policy keys off
them.

### 12. Currency, numeraire and the anchor (operator, 2026-08-20)

**USD is the global canonical numeraire.** FX and stablecoin rates are their own explicit fast factors.

**Prices in quote currency, risk in USD.** `U_i0` is published in the instrument's quote currency (BTC/KRW in KRW —
what you send to Upbit) with the FX loading carried in `J_i`. Positions and the adjustment matrix operate in USD
canonical risk units via `q = Lp`, where `L` absorbs contract multipliers, inverse-vs-linear and FX/stablecoin
conversion. Prices in quote ccy, risk in USD, `L` is the bridge.

**Same infra handles BTC/USD, BTC/USDT and BTC/KRW** — one row of loadings each, no new code path. Adding a venue or
quote currency adds a row and sometimes a factor. Spot and perps as joint canonical influencers are two rows.

**The trap**: a slow path embedding an FX or stablecoin assumption inside `U_i0` without exposing it as a factor
leaves the fast path no lever. Every conversion must appear in `z` with a loading in `J`. Corollary — **any basis
that can move materially inside one slow-path interval MUST be an explicit fast factor** (USDT/USD during a depeg
worst case; also KRW/USD, perp funding). Ask this per factor before building.

**Structure is configured; loadings are calibrated.** Config says which factors an instrument loads on; it cannot
say how much of an Upbit move is common-BTC vs KRW vs local premium — empirical and regime-dependent. An
under-specified factor vector fails silently: omit local-premium and Upbit observations have nowhere to go but
common BTC, and the model mis-attributes confidently.

### 13. Rebase without jaggedness (operator, 2026-08-20)

Execution has the faster feed; strategy is delayed. The rebase must not jump.

**`z_0` is an ANCHOR, not a price opinion.** Execution never adopts it as current state — it keeps its fresher
`z_hat` and evaluates the new coefficients AT THE CURRENT STATE. Both generations evaluated at the same state, so
strategy's delay is absorbed by replaying forward from the watermarks. What remains in `F_new - F_old` is genuine
model change plus approximation error. Strategy sends the SHAPE; execution supplies the STATE.

**`t_0` must be the validity time of strategy's inputs, not publish time** (strategy timestamps its own delay).
Otherwise `Dt` is understated, theta under-applied, and a systematic bias reads as jitter.

**Natural damper**: publish-only-on-order-state-change means a sub-tick revision produces zero wire traffic.
Jaggedness reaches the venue only when a revision crosses a tick — a real signal. **Do not blend/ramp** between old
and new fair: it quotes a number neither generation believes and corrupts the rebase error measurement. Accept the
new fair, let tick thresholds gate the wire; if extra caution is wanted gate *aggression* for a beat — posture, not
price.

**The real risk**: if strategy is slow relative to market movement, `Dz` is already large at rebase, so the snapshot
lands where its Taylor approximation is least accurate — possibly already outside its own envelope. Fix is faster
cadence or cheaper slow-path compute, NOT a wider envelope (which hides use outside validity). **Instrument
`Dz`-at-rebase as a distribution from day one**; if p99 approaches the envelope the cadence is wrong for that
universe. This is the honest input to the per-slot cadence ruling.

**Separate the two causes of the rebase gap**: approximation error (quality signal, trips warn/error) vs genuine
model update (slow path recalibrated). Measuring only the total makes every legitimate recalibration look like an
approximation failure. Coefficient version and basis-model version exist for this.

### 14. The anchor is an ESTIMATE, and it lives in FEATURES-SERVICE (operator, 2026-08-20)

**Last-trade is not fair value.** One aggressive order sweeping levels prints a number that was never fair value; if
`z_0` adopts it the fast path carries that offset until the next snapshot. The slow path runs the same factor
machinery properly: `z_0` is a posterior estimate of the common efficient price given all venue observations,
weighted by liquidity, spread and staleness — microprice/imbalance-weighted rather than mid, prints evaluated
against the book state at the time.

**Spike immunity falls out of the factor model**: a single-venue spike no other venue echoes does not look like a
common-BTC move — it loads onto that venue's basis residual.

**Internal consistency protects the basis.** Absolute anchor error is common-mode and largely cancels in a spread;
independent per-instrument error does not. **Every `U_i0` in a generation must derive from ONE consistent `z_0`** —
price the factors once, then project through `J`. Pricing instruments independently and inferring the basis
afterwards builds noise into the exact relative values being traded. Same reason the snapshot needs a coherent time
slice (leg A at t, leg B at t+50ms is an unrecoverable basis error).

**Uncertainty travels with the estimate.** `Sigma_z` alongside `z_hat`; a suspicious print should WIDEN uncertainty
rather than move the mean, so the action layer quotes less aggressively instead of confidently quoting wrong.

**The slow path should be SMOOTHER than the fast path, not merely slower.** Its job is an unbiased anchor plus
accurate coefficients — not a fresh price, which execution already has. A slow path chasing every tick manufactures
snapshot-to-snapshot jitter, surfacing as rebase discontinuity.

**PLACEMENT RULING: the efficient-price/factor estimator, and any smoothing, EMA or averaging, belong in
FEATURES-SERVICE** — alongside the volatility and greeks computation already there. MDPS owns normalisation and
canonical book/trade state; features-service owns factor estimate + uncertainty + greeks + vol; strategy-service
consumes those and adds valuation, the adjustment matrix and credit. Each strategy deriving its own fair value gives
N disagreeing estimators for one BTC — duplication, and two strategies quoting inconsistent prices on the same
underlying. Consistent with the standing "strategy reads only processed data, never MTDS directly" invariant.

### 15. OPEN — needs an operator ruling next session

1. **Market-state dependence of A** — cross-tensors `A^(k)` for important factors + trust-region the rest (external
   doc's recommendation), full `Dz' B_i Dq`, or keep A fixed relying on trust region + refresh cadence?
2. **Formally adopt the factor model** in place of section 10's primary/correlated split? (Recommend yes — strictly
   more general, removes per-venue-pair suppression tuning.)
3. **Position vectors** — adopt `q_confirmed` / `q_pricing` (fill-probability-weighted) / `q_worst`? Do not weight a
   pending order at 100% through `A` AND treat it as full inventory risk elsewhere unless deliberately conservative.
4. **Substrate-conditional transport** — should derived topology take deployment substrate as input (colo L2 ->
   multicast; cloud -> unicast/relay) given per-receiver cloud multicast billing?
5. Five outstanding Wave-0 rulings: CloudKmsCustodyProvider wallet check, UAC `__init__` restructure scope,
   instruments catalogue ratification, instrument-universe hot-swap safety, venue-eligibility generalisation shape.

- [ ] [DOC] P0. **Write the full build spec** — a CTO-level document covering slow/fast split, worked examples,
      infrastructure, feed arbitration, instrument selection for fast updates, and the options fast path. A peer
      agent was asked for one; reconcile it against sections 11-14 if it arrives, otherwise author it.
- [ ] [REVIEW] P0. **Verify before building**: cloud multicast billing (AWS TGW per-receiver, GCP no cross-region)
      and the quoted venue feed latencies. Decision-changing and inherited from a summary, not measured.
- [ ] [BACKEND] P1. **Instrument `Dz`-at-rebase** as a distribution per strategy slot — the empirical input to the
      sync-cadence decision.

- **context-scout 2026-08-20**: refreshed context_scope (7 entries — slightly above the usual 2-6 target, justified
  by this doc's size and ongoing 3-layer design scope).

### 16. RESOLVED — the external build spec arrived, and 16 rulings landed (2026-08-20)

The CTO-level build spec requested in the section-15 `[DOC] P0` **arrived** as
`Cross_Venue_Factor_Repricing_Platform_Technical_Specification` v1.0. Reviewed in full and reconciled against sections
11-15 in an operator Q&A session the same day.

**Both outputs are now durable and are the SSOT for everything below:**

- **The contract + the 16 rulings**: [/codex/04-architecture/cross-domain-state-fabric.md](/codex/04-architecture/cross-domain-state-fabric.md)
- **The external text, verbatim**: [/plans/audit/results/external_hft_factor_repricing_spec_2026_08_20.md](/plans/audit/results/external_hft_factor_repricing_spec_2026_08_20.md)

**What this changes in THIS document.** Three corrections, all of which scope earlier sections rather than reverse
them:

1. **Section 11's `F_i` is the CONTINUOUS-QUOTE KERNEL, not universal.** An AMM is an exact reserve/tick-math
   simulation; a sports instrument is a finite-state posterior. The universal invariant is "evaluate current absolute
   state against an immutable reference generation" — not delta/gamma everywhere.
2. **Retraction is one envelope operation across every profile**, not a DeFi-specific reorg path. A chain reorg, a
   sports scoring correction and a voided market are the same mechanism.
3. **Semantic profile and performance tier are orthogonal.** A DeFi mempool race can be more latency-critical than a
   thin CeFi venue. Profile bounds the achievable tier (block time is a floor) but does not determine it.

**Section 15's open list now resolves as**: Q1 (market-dependence of `A`) -> R8, low-rank `L R + D`. Q2 (adopt the
factor model) -> R15, adopted **as the continuous-quote kernel**. Q4 (substrate-conditional transport) -> R3, the
contract is substrate-neutral and the transport follows locality. **Q3 (position vectors) and the five Wave-0 rulings
remain OPEN** — carried into the codex doc's section 10.

- [x] ✅ [DOC] P0. **Build spec written** — unified-trading-pm, codex SSOT + verbatim external reference, both linked
      above. The peer agent's document arrived and was reconciled rather than accepted wholesale; three of its framings
      were corrected by operator ruling — see the R1-R16 register in /codex/04-architecture/cross-domain-state-fabric.md section 9.
- [ ] [BACKEND] P0. **Split the live tick timestamp and add receive order + region** (R4) — tracked in full at
      [/plans/active/issues/market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md](/plans/active/issues/market_data_timestamp_semantics_collapsed_to_one_field_2026_08_20.md).
      **CORRECTION 2026-08-20**: this todo previously claimed no receive-time capture existed, citing zero hits for
      `receive_time|recv_time|rx_time|local_receive`. That was a search reported as a conclusion, and the operator
      corrected it. `local_timestamp` exists in 44 files; `unified_api_contracts/internal/events.py:17` already
      MANDATES `["exchange_timestamp", "local_timestamp", "sequence_number"]` for MARKET_DATA. The real defect is
      narrower and worse: the LIVE path collapses both into one `ReceivedTick.timestamp` whose meaning varies by
      adapter — Databento aliases exchange time in, Binance and Hyperliquid write arrival time. A missing field fails
      loudly on first use; an ambiguous one never fails. Still the prerequisite for per-region equivalence and the
      delay estimator.
- [ ] [BACKEND] P0. **Build the cross-region delay estimator** (R9) — properties and its four consumers are in the
      codex doc section 8. It gates the multi-region build, so it belongs alongside the cloud-multicast-billing check.
- [ ] [BACKEND] P0. **Extend the UAC venue capability registry with the manifest fields** (R10/R11) — profile defaults
      throughout, with `finality_model` and `ordering_key` having NO default and requiring explicit per-venue
      declaration. A fourth parallel venue registry is forbidden.
- [ ] [BACKEND] P1. **Fold greeks-service into features-service** (R7) — one home for model coefficients, so a snapshot
      generation cannot be assembled half-and-half across a service boundary.
- [ ] [REVIEW] P1. **Add a reorg row to the DeFi failure matrix and audit barrier-1 dedup keys for the reorg trap** —
      a key on `tx_hash` alone wrongly suppresses the same transaction re-included under a different block hash.
      Measured 2026-08-20: `reorg` has ZERO hits across execution-service, strategy-service and features-service.
