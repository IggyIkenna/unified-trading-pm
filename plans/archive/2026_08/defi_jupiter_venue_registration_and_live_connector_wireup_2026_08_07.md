---
doc_type: plan
title: Jupiter DeFi venue registration (full-stack) + wire in 3 orphaned MTDS live-connector building blocks
summary: >-
  Executes the operator's 2026-08-07 ruling on defi_adapter_dead_code_audit_2026_07_24.md §6 — register Jupiter (Solana
  DEX aggregator) as a live DeFi venue across UAC/instruments-service/MTDS/execution-service, and wire
  onchain_event_poller.py's Aave-liquidation path into a real MTDS live connector. 2 of the operator's 5 named Jupiter
  surfaces (execution-service support, MVP-venue-list inclusion) turned out to already exist / be automatic — see "Scope
  corrections vs the operator's framing" below.
status: complete
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, execution-service, unified-trading-pm]
scope: [engineer]
tags: [defi, jupiter, solana, venue-registration, live-connectors, honest-coverage, execution, ao-build]
related:
  [
    /plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md,
    /plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_2026_07_30.md,
    /plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_finalize_2026_07_30.md,
    defi_jupiter_venue_registration_and_live_connector_wireup_finalize_2026_08_07,
  ]
created: "2026-08-07"
last_updated: "2026-08-11"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 4
estimate_calibrated_ai_days: 4
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Operator ruling 2026-08-07 (interactive session, via consolidated NA-blocker-digest audit) on
  plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md §6, items 1 and 3. Verbatim: "jupiter is a huge solana
  dex should be in manifest, instrument service and catalogue, mvp venues, have is, mtds adaptors yes and execution
  service" (item 1); "wire in, do not delete" for onchain_event_poller.py +
  defi_live/{alchemy_adapter,thegraph_ws_adapter} (item 3).
context_scope:
  [
    /plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md,
    /codex/04-architecture/solana-defi-coverage.md,
    /codex/04-architecture/instrument-universe-registry-consolidation.md,
    /codex/02-data/live-data-persistence-and-event-log.md,
    /codex/04-architecture/defi-execution-overview.md,
    /plans/archive/2026_08/defi_venue_pipeline_to_live_ao_build_2026_07_30.md,
  ]
---

> **🟢 ARCHIVED 2026-08-11.** All 8 todos done + evidence independently re-verified on origin (slot-17 review,
> 2026-08-11): unified-api-contracts@ad003d03 (UAC JUPITER-SOLANA live venue), instruments-service@06c6f2dd
> (JupiterReferenceDataAdapter wired), market-tick-data-service@9e9c9817 + @73abd655 (Jupiter + Aave-liquidation live
> connectors), execution-service@507093de (JupiterConnector wired into DeFiAdapter), unified-trading-pm@c328a59f20
> (audit-doc §6 close-out + codex `solana-defi-coverage.md` update), the two WS-frame cassettes (xfails removed from
> `test_ws_cassette_coexistence.py`), and the xfail-tracked-todo rule (unified-trading-pm@32c5440a8d). Archived with its
> finalize companion `defi_jupiter_venue_registration_and_live_connector_wireup_finalize_2026_08_07.md` to
> `/plans/archive/2026_08/`. Source issue doc `plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md` stays
> ACTIVE (its governance-params-poller re-verify todo remains open, out of this plan's scope).

# Jupiter DeFi venue registration + MTDS live-connector wire-in (2026-08-07)

## Why this plan exists

`defi_adapter_dead_code_audit_2026_07_24.md` §6 flagged Jupiter (`instruments-service`'s `JupiterReferenceDataAdapter`)
as fully built, tested, and registered nowhere, and separately flagged 5 MTDS "defi live" building blocks as fully
built, tested, and never wired into the real `live/connectors/register_all()` mechanism. The operator ruled on 2 of
those 4 open items on 2026-08-07: register Jupiter as a live venue full-stack, and wire in 3 of the 5 MTDS files
(`onchain_event_poller.py` + `defi_live/{alchemy_adapter.py,thegraph_ws_adapter.py}`). This plan executes both rulings.
(The governance-params-poller re-verify, item 2 of 4, remains unruled — out of scope here.)

## Scope corrections vs the operator's framing (read before dispatching)

Investigation this session found the real per-surface shape differs from the operator's own framing on 2 of the 5 named
Jupiter surfaces, and narrowed the wire-in track from 3 files to 1:

- **"MVP-venues list inclusion" is not a separate edit.** There is no standalone editable "MVP venues" list for DeFi.
  `unified_api_contracts.canonical.crosscutting._mvp_scope_rules.py::_mvp_defi_venues()` returns
  `VENUES_BY_ASSET_GROUP["defi"]` verbatim (v13 ruling, 2026-07-09: "DeFi MVP == everything we currently capture"), and
  `VENUES_BY_ASSET_GROUP["defi"]` (`unified_api_contracts/registry/market_data_categories.py:493`) is itself
  auto-derived: `[v for v in _ALL_DEFI_VENUES if _DEFI_VENUE_PHASE.get(v) == "live"]`. Flipping
  `DEFI_VENUE_PHASE["JUPITER-SOLANA"]` to `"live"` (todo 1 below) automatically makes it MVP — no separate list to
  touch.
- **"execution-service support... does not exist today" is wrong — it already exists, unwired.**
  `execution_service/defi_execution/protocols/jupiter.py::JupiterConnector` is a complete, tested Solana swap connector
  (real Jupiter v6 quote+swap API calls, wallet signing via `BaseSolanaConnector`, paper-trade mode) — the exact same
  "built but never wired" pattern the audit already found for the IS-side `jupiter.py`. It is exported from
  `execution_service/defi_execution/protocols/__init__.py` but NOT re-exported from the top-level
  `execution_service/defi_execution/__init__.py`, and `execution_service/adapters/defi_adapter.py` only imports
  `AAVEConnector`/`LidoConnector`/`UniswapConnector`. This shrinks todo 4 from "build execution support" to "wire an
  existing, tested connector into the existing dispatch pattern" — same shape as todo 2's IS-side registration.
- **Wire-in track narrowed from 3 files to 1.** Of the operator's 3 named files, only `onchain_event_poller.py` has a
  concretely determinable wiring target (see todo 5). `alchemy_adapter.py::AlchemyLiveAdapter` and
  `thegraph_ws_adapter.py::TheGraphWsAdapter` are generic, multi-chain/multi-protocol WS-message parsers with no single
  natural venue target — see "Open questions" below. Per `task_template.md`'s dispatch-scope-eligibility bar (finding
  S), these are NOT forced into a todo; they need operator/design input first.
- **None of the 3 wire-in files are `WSFeedConnector`-conforming classes that self-register.** Unlike the operator's
  "this is wiring, not new implementation" framing, none of `OnChainEventPoller`/`AlchemyLiveAdapter`/
  `TheGraphWsAdapter` implements the `connect`/`subscribe`/`unsubscribe`/`stream`/`close`/`pop_reconnect_flag` Protocol
  or calls `register_ws_feed_connector()` — "wiring" requires a new thin wrapper module (mirroring `curve_defi_ws.py`'s
  established polling-connector pattern), not a one-line `register_all()` tuple addition. This is still
  bounded/dispatchable (the pattern to mirror is concrete and the hard parsing logic already exists in the named
  classes) — just bigger than "add a tuple entry."

## Codex SSOTs

- `/codex/04-architecture/solana-defi-coverage.md` — already documents Jupiter's intended shape ("JUPITER: Swap route
  history via Jupiter API (batch + live)" under "MTDS role (NOT yet wired)") — **needs a post-ship update** (todo 6
  below) once this plan lands, mirroring how METEORA/PHOENIX/DRIFT are already documented as shipped.
- `/codex/04-architecture/instrument-universe-registry-consolidation.md` — UAC-owns-venue-truth / IS-is-thin-resolver
  split this plan's todos 1-2 follow exactly.
- `/codex/02-data/live-data-persistence-and-event-log.md` — the "Live = batch, no live-only data_types" rule that
  informs todo 5's explicit exclusion of the Uniswap-Swap-topic half of `OnChainEventPoller`.
- `/codex/04-architecture/defi-execution-overview.md` — DeFi execution credential convention + error-code classification
  todo 4 must follow.

## Open questions (NOT todos — need operator/design input before dispatch)

1. **`AlchemyLiveAdapter` + `TheGraphWsAdapter` target venue(s).** Both parse generic WS payloads (`chain=`/`protocol=`
   constructor params, not venue-bound). Alchemy is explicitly classified in MTDS's `INFRA_PROVIDER_REGISTRY`
   ("transport layer, NOT a venue — we don't trade on these, we use them to reach venues"), so registering either class
   directly under its own `WS_FEED_CONNECTOR_FACTORIES` venue key would contradict that established distinction. The
   real question is which REAL venue's live connector should adopt one of these as its transport (e.g., a future
   Aave/Uniswap connector using Alchemy WS push instead of RPC polling, or a future pool-state connector using a
   TheGraph WS subscription instead of the 30s HTTP polling `dex_swap_uniswap_v3_ws.py` already uses) — and whether
   that's even worth the churn given the existing polling connectors already work and were deliberately designed the way
   they are (see todo 5's Uniswap-exclusion reasoning). Needs an operator/local-plan decision before either becomes a
   real todo.

## Todos

- [x] ✅ [DATA] P1. **UAC: register `JUPITER-SOLANA` as a live DeFi venue.** In
      `unified-api-contracts/unified_api_contracts/registry/venue_adapter_keys.py`, add
      `VENUE_TO_ADAPTER_KEY["JUPITER-SOLANA"] = "jupiter"` (currently absent — the file's own comment "Jupiter is
      execution-only (swap aggregator), not instrument discovery" near the DeFi section is stale now that
      `JupiterReferenceDataAdapter` does real instrument (token-pair) discovery; remove/correct that comment). In
      `unified-api-contracts/unified_api_contracts/registry/defi_venues.py`, flip `DEFI_VENUE_PHASE["JUPITER-SOLANA"]`
      from `"pipeline"` to `"live"` (correct its "JUPITER is execution-only aggregator, no IS adapter" comment — also
      stale). Do NOT separately edit any MVP list — see "Scope corrections" above; the MVP flip is automatic. Done-when:
      `unified-api-contracts` `quality-gates.sh` green, and a targeted check confirms
      `"JUPITER-SOLANA" in VENUES_BY_ASSET_GROUP["defi"]` resolving to adapter key `"jupiter"`. —
      unified-api-contracts@ad003d03 QG green; targeted check confirms JUPITER-SOLANA ∈ VENUES_BY_ASSET_GROUP["defi"]
      with adapter key "jupiter"

- [x] ✅ [DATA] P1. **instruments-service: wire `JupiterReferenceDataAdapter` into the live factory + venue list.**
      Depends on todo 1 (this repo's `unified-api-contracts` dependency must be bumped to the version containing todo
      1's change first). In `instruments-service/instruments_service/reference_data/factory.py`: add
      `from .adapters.defi.jupiter import JupiterReferenceDataAdapter`, add `"jupiter": JupiterReferenceDataAdapter` to
      `_ADAPTERS`, and add `"jupiter": ""` to `ADAPTER_DATA_SOURCES` (Jupiter's lite API needs no key — same shape as
      `"kamino": ""`/`"raydium": ""`/`"orca": ""` already in that dict). In
      `instruments-service/instruments_service/engine/orchestrator/defi.py`, add `"JUPITER-SOLANA"` to
      `_SOLANA_DEFI_VENUES` (remove the now-stale `# Jupiter is execution-only... not instrument discovery` comment
      above the list). Done-when:
      `tests/unit/test_orchestrator_helpers.py::test_defi_set_equals_uac_denominator_drift_guard` passes, a targeted
      test confirms `get_adapter_for_canonical_venue("JUPITER-SOLANA")` returns a `JupiterReferenceDataAdapter`
      instance, and `instruments-service` `quality-gates.sh` is green. — instruments-service@06c6f2dd QG green; drift
      guard + factory targeted checks PASSED

- [x] ✅ [BACKEND] P2. **market-tick-data-service: new live connector for Jupiter market data.** No existing MTDS
      adapter covers Jupiter (batch `market_interface/factory.py::VENUE_REGISTRY` has no `jupiter` entry; no
      `live/connectors/jupiter*.py` file exists). Create
      `market_tick_data_service/live/connectors/jupiter_solana_ws.py`, mirroring
      `market_tick_data_service/live/connectors/raydium_defi_ws.py` / `orca_defi_ws.py`'s established pattern almost
      verbatim (both already poll `lite-api.jup.ag/swap/v1/quote` for THEIR OWN venue's price via a `dexes=<name>`
      filter param): poll the SAME Jupiter quote endpoint (`get_solana_protocol_url("jupiter")`) WITHOUT a `dexes=`
      filter (Jupiter itself is the aggregator — unfiltered IS the correct semantics), reuse the SAME token-pair set
      already defined in
      `instruments-service/instruments_service/reference_data/adapters/defi/jupiter.py::_CORE_ROUTABLE_PAIRS` for
      cross-adapter consistency, instrument_type `SPOT_PAIR` (matching the IS adapter's own instrument_type choice —
      Jupiter has no owned pools, so `POOL` per the Raydium/Orca precedent does not fit), data_type `dex_pool_swaps`
      (the closest currently-declared UAC defi data_type to `/codex/04-architecture/solana-defi-coverage.md`'s informal
      "spot_trades" label for Jupiter — flag the label mismatch for the post-ship codex update in todo 6). Register via
      `register_ws_feed_connector(venue="JUPITER-SOLANA", ...)` and add the module to
      `live/connectors/__init__.py::register_all()`'s tuple. Done-when: `market-tick-data-service` `quality-gates.sh`
      green and a targeted test confirms the connector is present in `WS_FEED_CONNECTOR_FACTORIES` under
      `JUPITER-SOLANA` after `register_all()`. — market-tick-data-service@9e9c9817 QG green (10108 passed, 0 failed);
      TestJupiterRegistry::test_jupiter_solana_registered_after_register_all PASSED confirming JUPITER-SOLANA in
      WS_FEED_CONNECTOR_FACTORIES after register_all(); 27/27 Jupiter-specific tests passed.

- [x] ✅ [BACKEND] P2. **execution-service: wire the already-built `JupiterConnector` into `DeFiAdapter`.** In
      `execution_service/defi_execution/__init__.py`, add `JupiterConnector` to the existing
      `from .protocols import (...)` block and its `__all__` (it is already exported one level down, from
      `execution_service/defi_execution/protocols/__init__.py` — this file just never re-exports it). In
      `execution_service/adapters/defi_adapter.py`: import `JupiterConnector`, add a
      `jupiter_connector: JupiterConnector | None = None` constructor param (mirroring `uniswap_connector`), and extend
      the venue dispatch inside `_execute_swap()` (currently `if "UNISWAP" not in venue: raise ValueError(...)`) so a
      venue containing `"JUPITER"` routes to a new `_execute_jupiter_swap()` helper that calls
      `self._jupiter.get_swap_quote(input_mint=..., output_mint=..., amount=...)` then
      `self._jupiter.execute_swap(quote)` — note `JupiterConnector` takes Solana mint addresses, not EVM token symbols,
      unlike `UniswapConnector.swap_exact_input`, so the param-extraction logic cannot be copy-pasted verbatim from
      `_execute_swap`'s existing Uniswap branch, only its overall shape (retry/classify wrapping stays in the shared
      `_execute_with_retries`/`_dispatch_defi_operation` path, unchanged). Done-when: a new unit test (mirroring the
      existing `test_execute_swap` shape in `tests/unit/test_defi_adapter.py`) confirms `execute_instruction()` with
      venue `"JUPITER-SOLANA"` dispatches to `JupiterConnector.execute_swap()`, and `execution-service`
      `quality-gates.sh` is green. — execution-service@507093de QG green; test_execute_swap_jupiter PASSED confirming
      JUPITER-SOLANA routes to JupiterConnector.execute_swap()

- [x] [BACKEND] P2. **market-tick-data-service: wire `OnChainEventPoller`'s Aave-liquidation path into a real live
      connector — Uniswap-Swap-topic half deliberately excluded.** Create
      `market_tick_data_service/live/connectors/aave_liquidations_ethereum_ws.py`, mirroring `curve_defi_ws.py`'s
      polling-`WSFeedConnector` wrapper pattern: internally construct
      `OnChainEventPoller(rpc_url=..., contracts=[<AAVE V3 Pool address>], topics=[OnChainEventPoller's own default `_AAVE_LIQUIDATION_TOPIC`])`
      from `market_tick_data_service/market_interface/adapters/defi/live/onchain_event_poller.py`, translate each
      yielded raw log dict (`address`/`tx_hash`/`block_number`/`timestamp`, per that class's existing
      `tests/market_interface/unit/test_defi_live_feeds.py::TestOnChainEventPoller` shape) into a `ReceivedTick` with
      `instrument_type` reflecting a liquidation event and `data_type="liquidations"` (already a declared
      `DATA_TYPES_BY_ASSET_GROUP["defi"]` entry). Register via
      `register_ws_feed_connector(venue="AAVE_V3-ETHEREUM", ...)` and add the module to
      `live/connectors/__init__.py::register_all()`'s tuple. **Do NOT also wire the poller's Uniswap-Swap-topic path** —
      `dex_swap_uniswap_v3_ws.py`'s own module docstring documents that a raw `eth_subscribe`/log-decode connector for
      Uniswap swaps was deliberately rejected in favor of subgraph-polling specifically to guarantee
      `paper(W)==batch-rerun(W)` (the same data source live and batch, per
      `/codex/02-data/live-data-persistence-and-event-log.md`'s hard rule); reusing `OnChainEventPoller`'s raw
      `eth_getLogs` topic filter for Uniswap swaps would reintroduce exactly the anti-pattern that connector's own
      docstring documents avoiding. Done-when: `market-tick-data-service` `quality-gates.sh` green and a targeted test
      (mocking a log payload shaped like `OnChainEventPoller`'s existing tests) confirms the new connector registers
      under `AAVE_V3-ETHEREUM` and yields a `ReceivedTick` with `data_type="liquidations"`. 5. ✅
      market-tick-data-service@73abd655 — `aave_liquidations_ethereum_ws.py` created; `OnChainEventPoller` wrapped with
      `topics=[_AAVE_LIQUIDATION_TOPIC]`; registered under `AAVE_V3-ETHEREUM` (`overwrite=True`); 20 unit tests green;
      QG green.

- [x] ✅ [DOC] P3. **Close out the audit doc + refresh the Solana-DeFi codex SSOT.** In
      `plans/active/issues/defi_adapter_dead_code_audit_2026_07_24.md` §6, flip the two now-superseded checkboxes
      (Jupiter venue registration; the `onchain_event_poller.py` + `defi_live/{alchemy_adapter,thegraph_ws_adapter}`
      wire-in item) to `- [x]`, each citing this plan's slug
      (`defi_jupiter_venue_registration_and_live_connector_wireup_2026_08_07`) — do not duplicate this plan's content
      into that doc, just point to it — and add a Progress Log entry noting the wire-in scope was narrowed to
      `onchain_event_poller.py` only (see this plan's "Scope corrections" + "Open questions" sections) so the doc's
      remaining-open-work framing stays accurate for `alchemy_adapter.py`/ `thegraph_ws_adapter.py`. In
      `/codex/04-architecture/solana-defi-coverage.md`, update the "MTDS role (NOT yet wired)" JUPITER line to reflect
      the now-shipped connector (mirror how METEORA/PHOENIX/DRIFT are documented as shipped in that same table), and
      correct the informal "spot_trades" label to the real UAC data_type used (`dex_pool_swaps`, per todo 3). Done-when:
      both docs reflect the true post-ship state, citing real commit SHAs. — DONE 2026-08-10: audit-doc §6 Jupiter
      checkbox flipped + Progress Log entry added; codex `solana-defi-coverage.md` JUPITER line + `spot_trades` →
      `dex_pool_swaps` updated, citing unified-api-contracts@ad003d03, instruments-service@06c6f2dd,
      market-tick-data-service@9e9c9817, execution-service@507093de, market-tick-data-service@73abd655.

- [x] ✅ [TEST] P2. **Capture the two missing WS frame cassettes that are currently held open by `pytest.xfail`.**
      `unified-api-contracts/tests/test_ws_cassette_coexistence.py` xfails BOTH `jupiter_solana_ws` (2026-08-07) and
      `aave_liquidations_ethereum_ws` (2026-08-08, `unified-api-contracts@12bed42e`) because each connector landed
      without a cassette + venue mapping. Both xfails are honestly written ("needs a real WS capture, not a fabricated
      cassette" — the right call over inventing one), but **neither had a tracked follow-up until now**, which is how
      disabled coverage becomes permanent. Capture real WS frames for both and remove the xfails. Do NOT fabricate a
      cassette to close this. **Done when**: both connectors have real cassettes + venue dirs and
      `test_ws_cassette_coexistence.py` passes with no xfail for either.
- [x] ✅ [REVIEW] P3. **Add the standing rule that an `xfail`/`skip` needs a tracked todo.** Found 2026-08-08 during the
      fleet-wide "tests weakened rather than fixed" sweep: an xfail with a good reason and no remediation todo is
      indistinguishable, six months later, from coverage that was never written. Either wire a check (every
      `pytest.xfail`/`mark.skip` reason must cite a plan/issue slug) or record in codex why that is not worth enforcing.
      **Done when**: the check exists, or the decision is recorded with rationale. — unified-trading-pm@32c5440a8d:
      check wired (QG STEP 5.107 service / 5.102 library via `check_xfail_skip_tracked.py`, shrinking ratchet
      `xfail_skip_tracked_baseline.yaml` 43 baselined at bootstrap; `skipif` + reason-bearing `pytest.skip()` calls
      exempt by design — boundary recorded in codex quality-gates.md). PM QG green incl. STEP 5.107; 29 unit tests pass.

## Progress Log

- **2026-08-07 (interactive session)**: plan authored per operator ruling on
  `defi_adapter_dead_code_audit_2026_07_24.md` §6 items 1 and 3. Full cross-repo investigation done before drafting (UAC
  `venue_adapter_keys.py`/`defi_venues.py`/`_mvp_scope_rules.py`, IS `factory.py`/`engine/orchestrator/defi.py`, MTDS
  `market_interface/factory.py`/`live/connectors/__init__.py`/`raydium_defi_ws.py`/`curve_defi_ws.py`/
  `dex_swap_uniswap_v3_ws.py`, execution-service `defi_adapter.py`/`defi_execution/__init__.py`/
  `defi_execution/protocols/jupiter.py`) — see "Scope corrections vs the operator's framing" for what changed vs the
  operator's own framing.
