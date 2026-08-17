---
doc_type: issue
title: CEFI live position-read and order-placement dispatch both broken for 9 of 12 major venues — canonical venue ID never normalized to legacy factory vocabulary
summary: >-
  strategy-service's position-adapter factory and execution-service's order-adapter factory each maintain their
  own hand-written venue-match table using a legacy bare-token vocabulary ("binance", "bybit", "okx") that was
  never extended to recognize the canonical dash-suffixed venue IDs ("BINANCE-FUTURES", "OKX-SWAP", etc.) the rest
  of the system uses. Result: 9 of cefi's 12 major venues (BINANCE/BYBIT/OKX/COINBASE/KRAKEN families) cannot read
  a live position OR place a live order under their real canonical name today — both raise an unhandled
  ValueError. Found during the venue_e2e_wiring_2026_08_16 cefi batch sweep, steps 6+8 (strategy + execution).
status: open
nature: issue
asset_group: [cefi]
stage: [strategy, execution]
repos: [strategy-service, execution-service]
scope: [engineer]
tags: [venue-readiness, live-trading, position-read, order-execution, ssot-drift, financial-correctness]
related:
  [
    /plans/active/cefi_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md,
  ]
created: 2026-08-16
author: interactive-session
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2.5
estimate_calibrated_ai_days: 2.0
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found 2026-08-16 during cefi_venue_e2e_batch1_2026_08_16.md's steps 6 and 8 (position-adapter + execution-adapter
  wiring) contract sweep — 2 independent dedicated research passes across strategy-service and execution-service,
  each checking every one of 12 major cefi venues' real dispatch path (not just adapter-class existence), that
  converged on the identical root cause.
context_scope:
  [
    strategy-service/strategy_service/position/position_interface/factory.py,
    strategy-service/strategy_service/position/core/reconciliation_engine.py,
    execution-service/execution_service/trade_execution/factory.py,
    execution-service/execution_service/cli/handlers/live_execution_handler.py,
    unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py,
  ]
---

# CEFI live position-read and order-placement dispatch both broken for 9 of 12 major venues

## What I found

Two independent factories — one in `strategy-service` (which venue reads a live position), one in
`execution-service` (which venue can place a live order) — each hand-maintain a venue-match table keyed on a
**legacy bare lowercase token** (`"binance"`, `"bybit"`, `"okx"`, `"deribit"`, `"hyperliquid"`, `"kraken"`), not
the **canonical dash-suffixed venue ID** (`BINANCE-FUTURES`, `OKX-SWAP`, `KRAKEN-SPOT`, etc.) that
`position.venue`, UAC's venue registries, and this sweep's own row list all use as the real identifier. Neither
factory was ever extended with a normalization layer to bridge the two vocabularies, and neither was extended
consistently even within its own legacy vocabulary — the result is a broken, inconsistent match table in both
services, independently, with the same root disease.

**Position factory** — `strategy_service/position/position_interface/factory.py::_get_cefi_adapter` (lines
44-84), called via the sole production path
`AccountQueryClient._get_adapter` (`account_query_client.py:100`) ←
`ReconciliationEngine.reconcile_all_positions` (`reconciliation_engine.py:176-177`, passing
`position.venue` — confirmed canonical dash-form by the factory's own docstring, `factory.py:308-313`):

```python
match v:  # v = venue.lower().replace("-", "_")
    case "binance" | "binance_futures" | "binance_spot": ...   # only BINANCE got suffix variants
    case "bybit": ...                                          # bare only — "bybit_spot" falls through
    case "okx": ...                                             # bare only — "okx_futures"/"okx_spot"/"okx_swap" fall through
    case "deribit": ...
    case "hyperliquid": ...
    case _:
        return None                                             # COINBASE, KRAKEN: no case at all, always None
```

`get_position_adapter(venue="BYBIT-SPOT", mode=LIVE)` → `ValueError: Unknown venue: 'BYBIT-SPOT'`
(`factory.py:346,354-362`) — confirmed directly. Live PASS for exactly 3/12: BINANCE-FUTURES, BINANCE-SPOT, BYBIT.
The other 9 (BYBIT-SPOT, COINBASE-CDE/FUTURES/SPOT, KRAKEN-FUTURES/SPOT, OKX-FUTURES/SPOT/SWAP) raise unhandled.

**Execution factory** — `execution_service/trade_execution/factory.py::get_order_adapter`'s `CCXT_VENUES` set
(lines 36-45) has the identical shape: only bare `"binance"`/`"bybit"`/`"okx"`/`"coinbase"` (plus explicit
`DIRECT_REST_VENUES` entries for `"kraken-spot"`/`"kraken-futures"`, `factory.py:56,351-368`). The real production
caller, `LiveExecutionHandler._create_orchestrator_for_venue` (`live_execution_handler.py:332-359`), passes the
canonical dash-suffixed string straight through — confirmed canonical via
`unified_api_contracts/registry/venue_adapter_keys.py:78-115` and
`execution_service/utils/nautilus_compatibility.py:12-27`. `_resolve_venue_str` (`factory.py:139-146`) only strips
a suffix for a `Venue` enum input, never for the plain string this call site actually passes. Live order placement
PASS for exactly 3/12: BYBIT (bare-token match), KRAKEN-SPOT, KRAKEN-FUTURES (explicit compound-string entries).
The other 9 raise `ValueError: Unsupported venue` at orchestrator-construction time, before any order adapter is
even built — even though the real per-venue CCXT adapter classes underneath (`binance_ccxt.py`, `okx_ccxt.py`,
etc.) are genuine, working implementations; they are simply unreachable under the canonical name.

**UAC's `VENUE_TO_ADAPTER_KEY` registry does not help here** — confirmed a separate, unrelated table
(instruments-service's reference-data adapter-key resolver), never imported by either the position or execution
call path.

## Why it matters

This is a live-trading readiness gap on venues the workspace already treats as the flagship/mature asset group
and already routes real strategy logic through: **OKX-FUTURES is a live target of real carry-strategy code**
(`strategy_service/engine/strategies/v2/target_universe/catalog_carry.py:245,471`), and
BINANCE/BYBIT/OKX/KRAKEN-FUTURES are all named as real funding-rate-bearing venues
(`strategy_service/engine/core/canonical_perp_funding_provider.py:105`). A live carry position on any of the 9
broken venues cannot have its position reconciled or its order placed under its real name today.

The position-side failure mode is especially dangerous because it is **silent**:
`ReconciliationEngine.reconcile_all_positions` catches the `ValueError` per-position and `continue`s
(`reconciliation_engine.py:127-137`) — no `DISCREPANCY`/`CRITICAL` snapshot is ever produced for that venue, only
a `logger.exception` line. A position at one of the 9 broken venues simply never appears in reconciliation output,
rather than surfacing as a loud failure.

## What I have NOT verified

- Whether the same legacy-vocabulary disease recurs at other call sites not covered by this sweep's 12-venue scope
  (the remaining ~58 cefi rows, or other asset groups' major venues).
- Whether a pre-existing test would have caught either gap: confirmed it would not for the position side
  (`tests/position/position_interface/integration/test_adapter_factory.py` only parametrizes bare lowercase
  tokens, never a dash-form or suffix-form token) — the execution-side test suite was not audited for the same gap.

## Relation to existing tracked docs

`plans/active/issues/venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md` (lines 74-80) frames CeFi
position-read coverage as "effectively broad... reachable via `venue="ccxt", exchange_id="<id>"`." That framing is
true only for a manually-constructed call — nothing in the real production call path
(`AccountQueryClient`/`ReconciliationEngine`) ever translates a canonical dash-form venue token into that
`ccxt`+`exchange_id` pair (`execution_service`'s own `routing.py::_map_venue_to_ccxt`, the one place that could,
also has no `coinbase`/`kraken` entries — `routing.py:174-189`). This issue doc is a genuine refinement of that
finding, not a duplicate, and is worth surfacing to that doc's owner. No other plan or issue doc tracks this
specific factory-dispatch gap (grepped `plans/active/` + `plans/active/issues/` before filing).

## Todos

- [ ] [BACKEND] P0. **Fix `strategy_service/position/position_interface/factory.py::_get_cefi_adapter`** so all 12
      canonical dash-form venue tokens (and ideally every cefi venue, not just these 12) resolve to a real
      adapter. Done-when: `get_position_adapter(venue, mode=LIVE)` succeeds for every canonical cefi venue ID
      without a `ValueError`, and a regression test using dash-form tokens exists (the current suite only covers
      bare lowercase forms).
- [ ] [BACKEND] P0. **Fix `execution_service/trade_execution/factory.py::get_order_adapter`'s `CCXT_VENUES` /
      `DIRECT_REST_VENUES` dispatch** the same way. Done-when: `get_order_adapter` succeeds for every canonical
      cefi venue ID this sweep covered, with a regression test using dash-form tokens.
- [ ] [BACKEND] P1. **Build one shared venue-token normalization helper** (canonical dash-form → whatever internal
      key a given adapter registry needs) instead of patching both dispatch tables independently — the same
      disease will recur at the next call site (or the next new venue) otherwise. Done-when: both factories above
      route through the shared helper, and a fleet-wide grep for other hand-written venue-match tables with the
      same shape is done and any additional hits are filed as follow-up todos (not fixed silently without a
      record).
- [ ] [BACKEND] P2. **Audit whether this same disease exists for non-CEFI major venues** (the other 4 asset
      groups' own venue-e2e batches) — done-when: a cited answer, yes or no per asset group, filed as its own
      follow-up if any hit.

## Progress Log

- **2026-08-16**: Filed during the cefi AG batch's steps 6+8 (position-read + execution) venue-readiness sweep —
  2 independent research passes across strategy-service and execution-service converged on the identical root
  cause. Both specific claims (the position-factory `match` statement and the execution-factory `CCXT_VENUES` set)
  independently spot-checked by direct file read before filing.
