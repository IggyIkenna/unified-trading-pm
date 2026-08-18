---
doc_type: issue
title: >-
  Generic price-sensitivity contract for fast execution-side repricing — real infrastructure exists
  (`DeltaProxyRepricer`) but unwired on both ends, and the pattern needs generalizing beyond market-making to
  arb-leg repricing, then applying to MEV where it genuinely fits
summary: >-
  Investigating whether strategy-service's MEV opportunity-detection logic should also own low-latency repricing
  surfaced a broader, already-real pattern: execution-service has a fully-written, unit-tested delta/gamma
  linearization engine (`DeltaProxyRepricer` + `QuoteMaintainer`) that lets strategy-service publish a reference
  price + sensitivity ONCE and have execution-service extrapolate cheaply against live market moves without a
  round-trip. It is not live end-to-end: the strategy-side dispatch point (`QuoteHandler`) was deleted 2026-08-15 as
  confirmed dead code with no replacement built, no live underlying-tick feed drives it, and UAC's `QuoteInstruction`
  schema only supports the trivial self-underlying (delta=1.0) case. The same pattern, generalized, is the right
  shape for arb-leg repricing (`price_dispersion.py`) and for MEV archetypes with tight reaction windows
  (JIT_LIQUIDITY) — but neither has ANY version of this today; price_dispersion has an unused declarative enum
  (`MultiLegDeltaOwner`) naming the concept and nothing implementing it.
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
  packet" logic all belong in execution-service) led to checking whether the DeFi/MEV equivalent — which RPC, which
  relay, block timing — was already execution-service's job (confirmed yes: `v2/mev_router.py` +
  `defi_execution/mev/*`), then to the operator's own generalization: strategy-service should compute a GENERIC local
  sensitivity (delta/gamma-style) once per decision loop and hand it to execution-service, which evaluates it cheaply
  against a live feed and routes to the right execution algo. A research pass (2026-08-18) found this exact pattern
  already exists as real, unwired code in execution-service — verified directly, not taken on the research agent's
  word alone.
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
linear (or quadratic) sensitivity approximation of how an opportunity's value moves with the market — literally
delta/gamma, generalized beyond options to arb-leg repricing and hedging. Execution-service caches this sensitivity
object, watches the live order book / chain feed directly (no round-trip), cheaply extrapolates whether the cached
opportunity is still actionable given the live move, and routes to whichever execution algorithm handles it.

## What already exists — verified directly, not just agent-reported

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

**Three concrete gaps keep it from being live**, per `quote_maintenance.py`'s own docstring (verified by direct read,
2026-08-18):

1. **UAC's `QuoteInstruction` schema** (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/schemas.py:317-324`)
   carries `instrument`, `reference_price`, `half_spread_bps`, `max_inventory_abs`, `skew_on_inventory`,
   `refresh_cadence_ms` — **no `delta`/`gamma`/`underlying_instrument_id` fields**. The wiring that exists defaults
   `underlying_instrument_id = instrument` and `delta = 1.0` — the Spot/Perp self-underlying case only. Genuine
   derivative-hedged repricing (options against a distinct underlying, using real greeks-service deltas) needs a
   schema extension that does not exist yet.
2. **The strategy-side dispatch point was deleted.** `execution_service.v2.handlers.QuoteHandler` was THIS receipt
   point — `register_quote_instruction()` was meant to be called from it on every `QuoteInstruction` — until it was
   deleted 2026-08-15 as confirmed dead code (`execution-service@37bfaeed0b`, alongside `V2InstructionRouter`; both
   lived in the now-deleted `v2/handlers.py`; full context in
   `/plans/active/issues/e2e_wiring_reachability_audit_2026_08_15.md`). No replacement has been built.
   `QuoteMaintainer(`/`register_quote_instruction` have zero non-test references anywhere in the repo today
   (independently confirmed 2026-08-18, matching the earlier 2026-08-15 finding). `quote_maintenance.py`'s own
   docstring is explicit that a future receipt path should register directly against `QuoteMaintainer`, not
   resurrect the deleted router.
3. **No live underlying-tick ingestion loop exists.** `on_underlying_tick()` is the per-tick entry point, and
   nothing in execution-service subscribes to a live tick stream and calls it — confirmed via the module's own
   docstring ("no `EventTransport` tick consumer anywhere in execution-service") and independently via a workspace
   grep. Execution-service DOES already have several live-data mechanisms that could feed this
   (`providers/l2_depth_provider.py`'s `LIVE` mode subscribing to an MDPS Redis Stream; direct venue websocket
   clients; `providers/solana_amm_depth_provider.py` for on-chain AMM state) — none of them currently call into
   `DeltaProxyRepricer`.

**A dead documentation pointer riding along with this**: both `vol_trading/options.py` (strategy-service) and
`quote_maintenance.py` (execution-service) cite `feedback_market_making_reference_price_model.md` as "the v2
architecture memo" establishing this reference-price-once design. That file does not exist anywhere in
`unified-trading-pm` today (confirmed via `find`). Either it was written and never committed, or the citation was
aspirational. Flagged as a todo below rather than fixed inline — see the note there for why.

## What does NOT exist — the arb-leg-repricing analog

`strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py` and
`execution_service/v2/atomic_leg_executor.py` (the code that actually executes a `LEADER_HEDGE` compensating leg)
have **zero** delta/reprice tracking — confirmed via direct grep of both files for
`delta|reprice|leg_delta|sensitivity`; the only hits are "delta-neutral"/"delta-hedging" as plain-English
description of the trade shape, not implemented mechanism. UAC does declare a relevant concept —
`MultiLegDeltaOwner` (`unified-api-contracts/unified_api_contracts/internal/architecture_v2/order_semantics.py:97-124`),
an enum naming WHO owns inter-leg delta risk during a fill (`ATOMIC_BUNDLE` / `EXECUTION_ALGO` / `STRATEGY_ENGINE` /
`UNMANAGED`) — but nothing in `price_dispersion.py` or `atomic_leg_executor.py` reads or acts on it. This is a
**different, currently-unbuilt** gap from the market-making case above, not a smaller version of the same fix — a
multi-leg arb's "sensitivity" is how the SPREAD moves as any one leg's price moves, not a single instrument's delta
to an underlying, and no code anywhere computes that today.

Separately, execution-service's algo-selection layer is real and substantial —
`execution_service/algorithms/selector.py::select_algorithm()` + `engine/routing/handler_registry.py`'s policy
overlay (`ExecutionPolicyResolver`, gating on venue_category/instrument_type/urgency/notional) — but it selects on
static instruction/policy attributes, never on "how far has price moved since the reference was cached." The closest
analog is `DeltaProxyRepricer`'s `max_adjustment_pct` clamp, which just silently flags `stale=True` with no re-route
or escalation to a fresh strategy decision. That gap connects directly to the epic's own 2026-08-18 W16 ruling
(missing/stale required data must fail CLOSED by default) — a silently-clamped stale repricing is arguably the same
class of gap that ruling was written to close, just not yet recognised as an instance of it.

## Per-archetype MEV applicability — do not apply this uniformly

This does **not** uniformly apply to all three MEV archetypes tracked in
`/plans/active/issues/mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md`:

- **`BACKRUN`**: reacts to a confirmed block-N swap sometime before block N+1 closes — on Ethereum, a ~12-second
  window. The existing `EventTransport` publish/subscribe seam is very likely adequate once the opportunity-detection
  calculator (tracked in the MEV doc) exists; Pub/Sub round-trip latency is nowhere near 12 seconds. **Not measured**
  — this is reasoned from the archetype's own documented tolerance window, not a real latency benchmark of this
  deployment's Pub/Sub path. See the REVIEW todo below before ruling this out permanently.
- **`LIQUIDATION_BUNDLE`**: a position crossing health_factor < 1 doesn't un-cross itself in milliseconds; the only
  thing that matters is winning the race against other liquidators, which is execution-service's job (RPC/relay
  speed via the already-real `v2/mev_router.py`), not a repricing problem. Same conclusion as BACKRUN.
- **`JIT_LIQUIDITY`**: the best fit for this pattern — its whole shape (mint LP just before an imminent swap, burn
  right after) is a delta/gamma-style repricing-and-react problem. **Important caveat, not to be lost**: applying
  this pattern does **not** by itself resolve JIT_LIQUIDITY's deeper gap — it still has no real pending-swap signal
  at all (`jit_pending_swap_size_usd_<pool>` has zero producer, per the MEV issue doc; the codex archetype doc's own
  risk section already names the fix as "a real mempool feed," the same paused Phase 9 infrastructure SANDWICH is
  blocked on). This pattern would let JIT react faster **once** it has something real to react to — it is not a
  substitute for the mempool-visibility work.

## Todos

- [ ] [DESIGN] P1. **Design the generic sensitivity contract** — extend UAC's `QuoteInstruction` with
      `delta`/`gamma`/`underlying_instrument_id` (the narrower, already-half-built path) versus author a new
      asset-group-agnostic schema shared by market-making, arb-leg repricing and any future consumer. `LedgerRow`'s
      existing `option_delta`/`gamma`/`theta`/`vega`/`rho` fields (real, but options-named/shaped, zero consumers
      outside tests) are a candidate starting point, not necessarily the final shape. This is a real design call,
      not mechanical — resolve locally before dispatching any downstream build todo.
- [ ] [BACKEND] P1. **Rebuild the strategy-side QUOTE-instruction receipt path.** `QuoteHandler` was deleted
      2026-08-15 as dead code; per `quote_maintenance.py`'s own guidance, a replacement should register directly
      against `QuoteMaintainer.register_quote_instruction()` rather than resurrect the deleted router. This is what
      lets `MARKET_MAKING` archetypes (`continuous.py`, `passive_spread.py`, `inventory_skew.py`) actually populate
      `DeltaProxyParams` today, even before the schema extension in the todo above lands (the Spot/Perp self-underlying
      case works with the CURRENT schema).
- [ ] [BACKEND] P1. **Build the live underlying-tick ingestion loop** — subscribe to ticks via the standard
      `EventTransport` facade (per `/codex/02-data/live-data-persistence-and-event-log.md`'s established live=batch
      pattern) and drive `QuoteMaintainer.on_underlying_tick()` per tick. Execution-service already has candidate
      live-data mechanisms (`providers/l2_depth_provider.py`'s LIVE mode, direct venue websocket clients) — this is
      wiring, not new data-access infrastructure.
- [ ] [BACKEND] P2. **Extend the contract with real distinct-underlying delta/gamma**, sourced from `greeks-service`
      (which already computes real Black-Scholes greeks and writes `LedgerRow.option_delta`/`gamma`, currently
      consumed by nothing). Unblocks TradFi-options / derivative-hedged market-making beyond today's Spot/Perp-only
      (delta=1.0) case. Depends on the design todo above landing first.
- [ ] [DESIGN] P2. **Design the arb-leg-repricing analog** for `price_dispersion.py` / `atomic_leg_executor.py` — how
      the LEADER_HEDGE spread's sensitivity to any one leg's price move gets computed, cached, and consumed by
      execution-service. Wire the currently-unused `MultiLegDeltaOwner` enum to something real, or replace it if the
      design lands differently. Zero existing implementation to extend from — this is genuinely new, not a variant
      of the market-making fix.
- [ ] [STRATEGY] P2. **Apply the pattern to `JIT_LIQUIDITY`** once the above lands. Explicit scope caveat, restated
      from above so it isn't lost in triage: this does NOT resolve JIT_LIQUIDITY's mempool-visibility gap (tracked in
      `mev_engines_opportunity_detection_signals_unproduced_2026_08_18.md`) — it only lets the engine react faster
      once a real pending-swap signal exists. Sequence after the mempool-feed work, or in parallel, never as a
      substitute for it.
- [ ] [REVIEW] P2. **Measure this deployment's real `EventTransport`/Pub/Sub round-trip latency** before permanently
      ruling out this pattern for `BACKRUN`/`LIQUIDATION_BUNDLE`. The "12-second Ethereum block budget is generous
      enough" conclusion above is reasoned, not measured — confirm before treating it as settled.
- [ ] [BACKEND] P2. **Extend `ExecutionPolicyResolver`/`algorithms/selector.py`'s real routing with an
      "actionable-given-current-price-move" gate.** Today `DeltaProxyRepricer`'s `stale=True` flag just silently
      clamps the adjustment with no re-route or escalation back to a fresh strategy decision — the same class of gap
      the epic's 2026-08-18 W16 ruling (missing/stale required data fails CLOSED by default) already names, just not
      yet recognised as an instance of it here.
- [ ] [AGENT] P3. **Resolve the dead `feedback_market_making_reference_price_model.md` reference** cited by both
      `vol_trading/options.py` and `quote_maintenance.py`'s docstrings — confirmed not to exist anywhere in
      `unified-trading-pm`. Either this issue doc becomes the real record (repoint both docstrings here) or the
      memo should be authored for real if it once existed elsewhere and was lost. Small, deliberately not fixed
      inline this session — touches two other repos' docstrings, out of scope for a doc-only pass.

## Progress Log

**2026-08-18 — filed.** Surfaced mid-conversation while scoping the MEV opportunity-detection todos; escalated by
the operator into its own investigation once the pattern's applicability beyond MEV became clear. Verified directly
(not solely on a research agent's word): `delta_proxy_repricer.py` and `quote_maintenance.py` read in full,
`QuoteInstruction`'s real UAC schema fields grepped directly, both large existing e2e/venue-coverage issue docs
(886 and 961 lines) read to confirm this scope is genuinely untracked elsewhere before filing a new doc. Not yet
built: everything in the Todos section above.
