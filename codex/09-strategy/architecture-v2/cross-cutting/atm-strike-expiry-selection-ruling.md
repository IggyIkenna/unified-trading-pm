---
doc_type: codex-ssot
title: ATM Strike + Expiry Selection Ruling (VOL_TRADING_OPTIONS)
summary:
  "Operator ruling 2026-08-08: VOL_TRADING_OPTIONS resolves its option instrument as strike NEAREST TO SPOT (ATM) and
  the NEAREST WEEKLY EXPIRY with >= 7 DTE. Implemented in `vol_trading/atm_straddle_resolver.py::resolve_atm_straddle`,
  a pure function of (underlying, venue, mid_price, now_utc, min_dte). This is currently the ONLY option-structure
  selection rule the engine implements — `expression` (strangle/butterfly/calendar/iron_condor) is not built (see A3,
  the 4 dead VOL_TRADING_OPTIONS catalogue keys)."
status: current
nature: ssot
asset_group: [cefi, tradfi]
stage: [meta]
repos: [strategy-service]
scope: [engineer]
tags: [strategy, archetype, vol-trading, options, atm, strike-selection, expiry]
related:
  [
    /codex/09-strategy/architecture-v2/archetypes/vol-trading-options.md,
    /plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md,
  ]
created: 2026-08-13
authoritative_for: [VOL_TRADING_OPTIONS ATM strike + expiry selection rule and its operator provenance]
referenced_by: []
owner:
last_reviewed: 2026-08-13
code_refs: [strategy-service/strategy_service/engine/strategies/v2/vol_trading/atm_straddle_resolver.py]
---

# ATM strike + expiry selection ruling — VOL_TRADING_OPTIONS

## The ruling (operator, 2026-08-08)

> Select the strike **nearest to spot** (ATM) and the **nearest weekly expiry with ≥ 7 days to expiry (DTE)**. Resolve
> `call_instrument` / `put_instrument` from that pair.

## Why this doc exists

Before 2026-08-13 this ruling existed in exactly ONE place: a docstring inside `vol_trading/atm_straddle_resolver.py`.
No codex doc under `codex/09-strategy/` recorded it — the only `ATM` hit in that tree outside archived pre-v2 material
was a _proposed_ `ATM_ONLY` enum member in `uac-registry-gaps.md`, which is a gaps register, not a ruling record. This
was found because `check_plan_operator_ruling_evidence` rejected a citation of the ruling for lack of a durable home —
the gate was right. A ruling whose only copy is a source docstring dies the next time someone refactors that module
without realizing it's load-bearing; this doc is the durable copy. The docstring now points here instead of carrying the
full rationale itself.

## The implementation

`resolve_atm_straddle(underlying, venue, mid_price, now_utc, min_dte=7)` in
`strategy_service/engine/strategies/v2/vol_trading/atm_straddle_resolver.py` is a **pure, total function** — no I/O, no
randomness — of exactly those five inputs:

1. **Strike selection.** Round `mid_price` to the nearest valid strike increment for the underlying
   (`{"btc": 1000, "eth": 100, "spx": 25}`, else `1`), using `ROUND_HALF_UP`. This is the "nearest to spot" half of the
   ruling.
2. **Expiry selection.** Snap `now_utc + min_dte` forward to the next Friday (`_nearest_weekly_expiry`) — the nearest
   weekly expiry that clears the ≥ 7 DTE floor. `min_dte` defaults to 7 per the ruling but is a parameter, not a
   hardcoded literal, so a caller can widen it.
3. **Symbol formatting.** Deribit-grammar option symbols: `{ASSET}-{DD}{MON}{YY}-{STRIKE}-{C|P}`, e.g.
   `BTC-01AUG26-84000-C`.
4. Raises `ValueError` on `mid_price <= 0` or `min_dte < 0` — no silent fallback to a nonsensical strike/expiry.

Called from `vol_trading/options.py::VolTradingOptionsEngine.on_tick()` ONLY as a fallback — `options.py` prefers
explicit `call_instrument`/`put_instrument` params when supplied, and resolves via `resolve_atm_straddle` only when
they're absent. This precedence (explicit params win, resolver is the fallback) is correct, not a gap: it lets an
operator pin a specific contract while still getting a sane default when they don't.

## Determinism

Because the resolver is a pure, total function of its five inputs (no I/O, no randomness), a batch rerun re-derives the
identical instrument id for the same `(underlying, venue, mid_price, now_utc, min_dte)` — the ε=0 determinism spine
(`/codex/09-strategy/operational/paper-batch-live-reconciliation.md`) holds through instrument resolution.

## What this ruling does NOT cover

**Only ATM straddle is implemented.** `strike_selection` takes exactly one value across the entire repository (`"ATM"`,
no OTM/delta-targeted/skew alternative), and this resolver is the only option-structure rule that exists. The catalogue
previously declared an `expression` axis (straddle/strangle/butterfly/calendar/ iron_condor) that nothing read —
resolved 2026-08-13 by deleting the dead keys and collapsing the catalogue to the one structure the engine actually
implements (see `unified-trading-pm/plans/active/strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md` §
"Resolve the four dead VOL_TRADING_OPTIONS catalogue keys"). A strangle needs two OTM strikes, a butterfly three, a
calendar two expiries — none is expressible through this ATM-only resolver. Building those is new engine capability with
its own schema keys and resolver logic, not a re-interpretation of this ruling.

## Provenance

Operator ruling, 2026-08-08, quoted in `atm_straddle_resolver.py`'s module docstring since that date. This doc is the
durable record, authored 2026-08-13 (A8 follow-up,
`unified-trading-pm/plans/active/service_config_ownership_and_instruction_contract_2026_08_12.md` § J7 dispatch /
`strategy_service_expansion_overlays_config_and_wizard_2026_08_12.md` § "Record the option-instrument selection rule in
codex").
