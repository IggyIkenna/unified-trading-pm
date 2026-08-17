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

- [x] ✅ [BACKEND] P0. **Fix `strategy_service/position/position_interface/factory.py::_get_cefi_adapter`** so all
      12 canonical dash-form venue tokens (and ideally every cefi venue, not just these 12) resolve to a real
      adapter. Done-when: `get_position_adapter(venue, mode=LIVE)` succeeds for every canonical cefi venue ID
      without a `ValueError`, and a regression test using dash-form tokens exists (the current suite only covers
      bare lowercase forms). **Correction to this todo's own citation**: no test file at
      `tests/position/position_interface/integration/test_adapter_factory.py` exists in this checkout —
      confirmed via a repo-wide `get_position_adapter` grep, zero hits before this fix. `get_position_adapter`
      had ZERO existing dispatch-test coverage of any kind, not "bare-forms-only" coverage as originally claimed.
      **Fixed — `strategy-service@9027c2f5a9`**. Added missing `match` arms: `bybit_spot`/`bybit_futures` (was
      bare-only), `okx_spot`/`okx_futures`/`okx_swap` (was bare-only), `coinbase_spot` and `kraken`/`kraken_spot`/
      `kraken_futures` (had NO case at all before this fix — always fell through to `None` → the generic
      "Unknown venue" error). Coinbase/Kraken route through the existing generic `CCXTPositionAdapter`
      (`exchange_id="coinbase"`/`"kraken"`/`"krakenfutures"` — confirmed all three are real, distinct CCXT
      exchange classes; Kraken Futures is a genuinely separate product/API from Kraken spot, never conflated).
      **Deeper correctness finding, mirroring the execution-side fix**: `COINBASE-FUTURES`/`COINBASE-CDE` now
      raise a specific `ValueError` (no position-read adapter for those market types) instead of either the old
      generic error or silently reading Coinbase's spot balance as if it were futures/CDE data.
      **Real collision found and fixed mid-pass**: bare `"coinbase"` is a SEPARATE, pre-existing venue token in
      `LST_VENUE_TO_TOKENS` (`unified_api_contracts/registry/capability_declarations/_defi_lst.py` — Coinbase's
      cbETH liquid-staking receipt token), routed through `_generic_token_balance_adapter`. An initial version of
      this fix added bare `"coinbase"` to the new CEFI case (matching the execution-side fix's shape), which
      broke `test_a_venue_with_no_known_address_is_not_routed` — caught by the full QG run before shipping,
      fixed by scoping the CEFI case to `"coinbase_spot"` only (bare `COINBASE` was never one of the 12 in-scope
      venues anyway; only `BYBIT` bare had that in-scope ambiguity, and it doesn't collide). 20 new/updated
      tests (`tests/unit/position/test_position_adapter_factory.py`, all 6 pre-existing LST-routing tests in
      `tests/position/position_interface/unit/test_factory_generic_token_balance_routing.py` reconfirmed green).
      6067 passed/248 skipped, full `quality-gates.sh --no-fix` green before commit.
- [x] ✅ [BACKEND] P0. **Fix `execution_service/trade_execution/factory.py::get_order_adapter`'s `CCXT_VENUES` /
      `DIRECT_REST_VENUES` dispatch** the same way. Done-when: `get_order_adapter` succeeds for every canonical
      cefi venue ID this sweep covered, with a regression test using dash-form tokens. **Fixed —
      `execution-service@fcc6bbcc2c`**. `_resolve_venue_str` now returns `(base_venue_str, inferred_futures)`;
      a new `_split_venue_suffix` strips a `-SPOT`/`-FUTURES`/`-SWAP` suffix for the 3 venue families whose
      adapter has a REAL `futures: bool` toggle (confirmed by reading each adapter class:
      `BinanceCCXTAdapter`/`BybitCCXTAdapter` gate `defaultType=spot/future`; `OKXCCXTAdapter` gates
      `defaultType=spot/swap` — OKX-FUTURES and OKX-SWAP both map to `futures=True`, a pre-existing
      simplification not introduced here since the adapter doesn't yet distinguish dated futures from
      perpetual swaps). `get_order_adapter` merges the inferred flag via `futures = futures or inferred_futures`
      — an explicit caller-supplied `futures=True` is never downgraded, only ever upgraded from the default
      `False` every existing production caller passes today.
      **Deeper correctness finding, not just the ValueError**: naively stripping the suffix for EVERY venue
      would have silently routed a `COINBASE-FUTURES`/`COINBASE-CDE` order through the existing spot-only
      `CoinbaseCCXTAdapter` — its `futures` constructor param is a documented no-op ("Unused for Coinbase; kept
      for API consistency with Binance"). Both now raise a specific `ValueError` naming the real reason instead
      of either the old generic "Unsupported venue" or (far worse) silently misrouting a derivatives order as
      spot. `COINBASE-SPOT` still resolves correctly (its own narrower suffix-strip path, since only the
      FUTURES/CDE market types lack adapter support, not spot). `KRAKEN-SPOT`/`KRAKEN-FUTURES` (already-passing
      compound `DIRECT_REST_VENUES` entries) confirmed unaffected. 14 new tests in
      `tests/trade_execution/unit/test_factory_venue_dispatch.py`; 1 pre-existing integration test
      (`test_uci_venue_enum_used_in_factory`) updated for `_resolve_venue_str`'s new tuple return shape. 8582
      passed/21 skipped, full `quality-gates.sh --no-fix` green before commit.
      **Position-factory P0 (strategy-service) is a separate, not-yet-started fix** — same root disease, but a
      different service/file/adapter-family shape (position-read, not order-placement); do not treat this
      execution-side fix as closing that todo too.
- [x] ✅ [BACKEND] P1. **Build one shared venue-token normalization helper** (canonical dash-form → whatever internal
      key a given adapter registry needs) instead of patching both dispatch tables independently — the same
      disease will recur at the next call site (or the next new venue) otherwise. Done-when: both factories above
      route through the shared helper, and a fleet-wide grep for other hand-written venue-match tables with the
      same shape is done and any additional hits are filed as follow-up todos (not fixed silently without a
      record). **Fixed — `unified-api-contracts@9264cf2adc`, `execution-service@cba9ff511d`,
      `strategy-service@c44322ddc0`**. Added `split_venue_base_and_suffix(venue) -> (base_lower, suffix_or_none)`
      to `unified_api_contracts/registry/venue_adapter_keys.py` (exported via `registry/__init__.py`), with 7
      parametrized regression tests (`tests/unit/test_venue_base_and_suffix_split.py`) covering dash-form,
      bare-form, lowercase-input, and whitespace-padded venue strings. `execution_service/trade_execution/
      factory.py`'s `_resolve_venue_str`/`_split_venue_suffix` and `strategy_service/position/position_interface/
      factory.py`'s `_get_cefi_adapter` both now delegate their venue-string splitting to this single shared
      helper instead of each hand-rolling the split. **Fleet-wide grep disclosure — targeted, not exhaustive**: a
      repo-wide grep for the same hand-rolled venue-match-table shape (`match v:` / `case "binance"` /
      `CCXT_VENUES` / `DIRECT_REST_VENUES`-style literal-venue-token dispatch) surfaced roughly 20 raw hits
      fleet-wide; the 3 strongest candidates by call-path plausibility were read in full (instruments-service's
      DeFi chain-suffix parser, market-tick-data-service's CeFi catalog reader, deployment-api's ghost-venue UI
      detector) — none share this issue's disease shape (none dispatch a live position-read or order-placement
      call on an unnormalized bare-token match). The remaining ~17 raw hits were NOT individually read; this is
      an honest partial coverage, not a claim of exhaustive fleet coverage — a full sweep is exactly the scope of
      the P2 todo below, which remains open for that reason.
- [ ] [BACKEND] P2. **Audit whether this same disease exists for non-CEFI major venues** (the other 4 asset
      groups' own venue-e2e batches) — done-when: a cited answer, yes or no per asset group, filed as its own
      follow-up if any hit.

## Progress Log

- **2026-08-17 (later, same session)**: Fixed the P1 shared-helper todo —
  `unified-api-contracts@9264cf2adc` (new `split_venue_base_and_suffix` helper + regression tests),
  `execution-service@cba9ff511d`, `strategy-service@c44322ddc0` (both factories now delegate to it). Gate+ship
  ran serially in dependency order (UAC first, since both consumers pull it as a local editable install) — the
  two consumer repos' own `quality-gates.sh` runs then ran concurrently (different repos, same-file rule doesn't
  apply). Both consumer commits also carried an unrelated, pre-existing `uv.lock` resync (picking up
  `unified-trading-library`'s already-shipped `google-cloud-monitoring` dependency, added 2026-08-14 via UTL
  commit `5d619a68`, re-pinned 2026-08-16 via `820215db`) — a genuine gate-required lockfile-propagation-lag fix,
  not scope creep, confirmed via UTL's own clean working tree before bundling it in. Fleet-wide grep for the same
  disease shape was targeted (3 of ~20 raw hits read), not exhaustive — see the todo's own disclosure; P2 remains
  the right place for the full sweep. Only the P2 non-CEFI audit remains open in this issue doc.
- **2026-08-17 (later, same session)**: Fixed the position-factory P0 todo —
  `strategy-service@9027c2f5a9`. Both P0s in this issue doc are now closed; only the P1 shared-helper todo and
  P2 non-CEFI audit remain open. Mid-fix, caught (via the full QG run, before shipping) a real collision: bare
  `"coinbase"` is a separate pre-existing LST-issuer venue token (cbETH) that an early version of this fix
  would have silently broken by intercepting it as the CEFI exchange route — scoped the fix to
  `"coinbase_spot"` only to resolve it cleanly.
- **2026-08-17**: Fixed the execution-side P0 todo — `execution-service@fcc6bbcc2c`. Also found and closed a
  deeper correctness risk while fixing the ValueError: a naive suffix-strip would have silently routed
  COINBASE-FUTURES/COINBASE-CDE orders through the spot-only CoinbaseCCXTAdapter instead of failing loud — both
  now raise a specific, honest error. Position-factory P0 (strategy-service) and the shared-helper P1 remain
  open.

- **2026-08-16**: Filed during the cefi AG batch's steps 6+8 (position-read + execution) venue-readiness sweep —
  2 independent research passes across strategy-service and execution-service converged on the identical root
  cause. Both specific claims (the position-factory `match` statement and the execution-factory `CCXT_VENUES` set)
  independently spot-checked by direct file read before filing.
