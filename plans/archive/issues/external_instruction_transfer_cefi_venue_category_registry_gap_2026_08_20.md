---
doc_type: issue
title: >-
  TRANSFER via `execution_service.engine.routing.instruction_router.InstructionRouter` structurally rejects EVERY
  CeFi venue (binance/deribit/bybit/aster included) — a pre-existing `unified-api-contracts` registry gap, not a
  credential-provisioning gap
summary: >-
  Discovered while wiring `TRANSFER` onto `execution-service/execution_service/api/external_instruction_api.py`'s
  external HTTP front door via the real production `build_transfer_wiring()` -> `HandlerRegistry(transfer_adapter=
  ...)` -> `InstructionRouter` path (the same wiring `api/app.py`'s own `_wire_transfer_adapter()` startup hook
  already builds — `TransferWiring`'s own docstring notes "no production caller exists yet", meaning this change is
  the FIRST real exerciser of this path). A live test submitting a CeFi-venue TRANSFER (BINANCE-SPOT->
  BINANCE-FUTURES) through the real, fully-wired chain failed with `InstructionValidationError: Invalid
  venue_category='cefi' for instruction_type='ZERO_ALPHA'. Allowed: ['defi']` — BEFORE ever reaching the transfer
  adapter (credential resolution never happens; the request is rejected at structural validation).

  Root cause, read from the live code: `execution_service/engine/routing/instruction_router.py`'s
  `_INSTRUCTION_TYPE_MAP` maps `OperationType.TRANSFER -> "ZERO_ALPHA"` (the same bucket as LEND/BORROW/WITHDRAW/
  REPAY/STAKE/UNSTAKE/FLASH_BORROW/FLASH_REPAY — all genuinely DeFi-only operations). `InstructionRouter
  ._route_compose_preflight` calls `unified_api_contracts.registry.compose_validation(venue, instruction_type=
  "ZERO_ALPHA", ...)`, which calls `validate_instruction()` against
  `unified_api_contracts/registry/instruction_constraints.py::INSTRUCTION_CONSTRAINTS["ZERO_ALPHA"]` —
  hardcoded `venue_categories=frozenset({"defi"})`, no exception for TRANSFER. `unified_api_contracts/registry/
  venue_constants.py::VENUE_CATEGORY_MAP` classifies BINANCE/OKX/BYBIT/DERIBIT/ASTER/COINBASE/KRAKEN/HYPERLIQUID/
  BITFINEX/BITGET/UPBIT — every CEX — as `"cefi"`, never `"defi"`. The result: this structural gate rejects 100% of
  CeFi-venue TRANSFER submissions unconditionally, REGARDLESS of whether real CCXT credentials are wired for the
  venue. Only DeFi-to-DeFi transfers (venue_category='defi' on both sides, e.g. custody-provider on-chain moves)
  can ever reach `TransferHandler`/the real adapter through this specific code path.

  This is materially different from (and more severe than) the already-documented credential-provisioning gap
  (`engine/transfers/wiring.py`'s "only binance/deribit/bybit/aster resolve real CCXT credentials" note): even
  those 4 fully-credentialed venues cannot execute a TRANSFER through `InstructionRouter` today, because the
  request never survives structural validation to reach credential resolution at all. `execution_instruction_api
  .py`'s TRANSFER docstring/response `note` text has been corrected in the same change to state this precisely
  (the registry gap, not just the credential gap) so it doesn't mislead the next reader the way the docstring it
  replaced would have.
status: resolved
nature: issue
asset_group: [cross-cutting]
stage: [execution]
repos: [execution-service, unified-api-contracts, unified-trading-pm]
scope: [engineer]
tags: [execution-service, external-api, transfer, instruction-router, registry-gap, zero-alpha, venue-category, w22]
related:
  [
    /plans/active/w22_strategy_execution_messaging_external_api_2026_08_20.md,
    /plans/active/issues/external_instruction_defi_handlers_simulation_only_2026_08_20.md,
    /plans/active/issues/external_instruction_bridge_atomic_not_wired_2026_08_20.md,
  ]
created: 2026-08-20
source: >-
  Sub-agent dispatch wiring 9 of the remaining external_instruction_api.py action types (2026-08-20) — discovered
  by a real (non-mocked) end-to-end test of the shipped TRANSFER path against the actual production
  InstructionRouter/compose_validation gate, not guessed. TRANSFER shipped anyway (it is still the correct real
  wiring pattern per the dispatch's instructions, and DeFi-to-DeFi transfers genuinely work), with the response
  honesty text corrected to name this gap specifically.
author: agent
parent_epic: system_readiness_master
assigned_vm: NA
execution_scope: local-only
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 1.2
resolved_by: >-
  execution-service instruction_router.py (2026-08-20, same-day follow-up): removed
  `OperationType.TRANSFER` from both `_INSTRUCTION_TYPE_MAP` and `_OPERATION_NAME_MAP` in
  `execution_service/engine/routing/instruction_router.py` instead of taking either option this
  doc originally proposed. TRANSFER is now treated as an unmapped operation for
  `compose_validation` purposes (the same fallback path BET/SPORTS_EXCHANGE already use) — the
  UAC `ZERO_ALPHA` registry entry (`unified_api_contracts/registry/instruction_constraints.py`)
  is untouched, so LEND/BORROW/WITHDRAW/REPAY/STAKE/UNSTAKE/FLASH_BORROW/FLASH_REPAY keep their
  correct DeFi-only gate exactly as before — zero blast radius on those operations, zero
  `unified-api-contracts` change, no operator/design decision needed. Safe because
  `instruction.metadata["uac_op_detail"]` (compose_validation's only output) has zero downstream
  consumers (confirmed via full-repo grep — it is written in instruction_router.py and read
  nowhere), and TRANSFER already has its own real per-venue validation/honest-degradation in
  `TransferHandler`/`TransferAdapter`, independent of this preflight gate. Verified via a live
  (non-mocked) `TestTransferInstructionPath` test submitting a CeFi TRANSFER
  (BINANCE-SPOT->BINANCE-FUTURES) through the real `HandlerRegistry`/`InstructionRouter` chain —
  now reaches the real adapter and returns `COMPLETED_SUCCESS`, exactly as the credentialed-venue
  case should. `execution_instruction_api.py`'s TRANSFER docstring + response `note` text updated
  in the same change to describe only the remaining credential-provisioning gap (already tracked,
  unaffected by this fix), not the now-closed registry gap.
locked_by:
locked_since:
context_scope:
  [
    execution-service/execution_service/engine/routing/instruction_router.py,
    execution-service/execution_service/api/external_instruction_api.py,
    unified-api-contracts/unified_api_contracts/registry/instruction_constraints.py,
    unified-api-contracts/unified_api_contracts/registry/venue_constants.py,
  ]
drift_direction: advance-code
---

> **RESOLVED + ARCHIVED 2026-08-20.** Closed same-day via execution-service instruction_router.py (unmapped `OperationType.TRANSFER` from `compose_validation` instead of either registry-widening option this doc originally proposed — zero `unified-api-contracts` change, zero blast radius on LEND/BORROW/WITHDRAW/REPAY/STAKE/UNSTAKE/FLASH_BORROW/FLASH_REPAY). See `resolved_by` frontmatter for the full verification record.

# TRANSFER via `InstructionRouter` structurally rejects every CeFi venue — a registry-mapping gap, not a credential gap

## The mechanism, precisely

1. `execution_service/engine/routing/instruction_router.py::_INSTRUCTION_TYPE_MAP[OperationType.TRANSFER] =
   "ZERO_ALPHA"`.
2. `unified_api_contracts/registry/instruction_constraints.py::INSTRUCTION_CONSTRAINTS["ZERO_ALPHA"]` hardcodes
   `venue_categories=frozenset({"defi"})`.
3. `unified_api_contracts/registry/venue_constants.py::VENUE_CATEGORY_MAP` classifies every CEX (BINANCE, OKX,
   BYBIT, DERIBIT, ASTER, COINBASE, KRAKEN, HYPERLIQUID, BITFINEX, BITGET, UPBIT) as `"cefi"`.
4. `InstructionRouter._route_compose_preflight` -> `compose_validation(venue, instruction_type="ZERO_ALPHA", ...)`
   -> `validate_instruction()` raises `InstructionValidationError` for ANY `cefi` venue, unconditionally, before
   the transfer adapter (real or mock) is ever consulted.

Verified via a live test: `classify_transfer_type("BINANCE-SPOT", "BINANCE-FUTURES")` itself correctly resolves to
`SUBACCOUNT_MOVE` (the transfer-TYPE classification is fine) — the rejection happens one layer up, in
`InstructionRouter`'s structural preflight, before `TransferHandler.execute()` is ever called.

## Why this predates this change and isn't this task's bug to fix

`TransferWiring`'s own docstring (`execution_service/engine/transfers/wiring.py`) already says: "no production
caller exists yet" for `.router.route_instruction(...)`. This session's TRANSFER wiring is the FIRST real caller —
it did not introduce this gap, it exposed it. Fixing it requires a decision outside this task's scope:
- Should `TRANSFER` get its own `instruction_type` (distinct from `ZERO_ALPHA`) in
  `unified_api_contracts/registry/instruction_constraints.py`, with `venue_categories=frozenset({"cefi", "defi"})`
  (or similar)? This is a `unified-api-contracts` schema change, not an `execution-service` translation fix.
- Or should `ZERO_ALPHA` itself be widened to allow `cefi`? That risks changing validation behavior for
  LEND/BORROW/WITHDRAW/REPAY/STAKE/UNSTAKE too (all currently, correctly, DeFi-only) — a cross-cutting blast
  radius this task's "pure translation, no new execution logic" scope explicitly excludes touching.

## Current shipped behavior (RESOLVED — accurate as of the 2026-08-20 follow-up)

- TRANSFER between two `defi`-categorized venues (e.g. on-chain custody-provider moves) reaches the real
  `TransferHandler`/adapter chain and can genuinely succeed — unchanged.
- TRANSFER involving a `cefi`-categorized venue now ALSO reaches the real `TransferHandler`/adapter chain (the
  structural preflight rejection described above is gone): the 4 credentialed venues (binance/deribit/bybit/aster)
  can genuinely succeed; every other CEX_WITHDRAW venue still degrades to an honest `COMPLETED_FAILED` via the
  adapter's own per-venue credential lookup miss (the separate, still-accurate, always-expected credential gap —
  never a fabricated success).

## Resolution

Neither of the two options this doc originally proposed (give TRANSFER its own `unified-api-contracts`
`instruction_type`, or widen `ZERO_ALPHA`'s `venue_categories`) was needed. The actual fix: removed
`OperationType.TRANSFER` from `instruction_router.py`'s `_INSTRUCTION_TYPE_MAP`/`_OPERATION_NAME_MAP`, so
`compose_validation` treats TRANSFER as unmapped (skipped) — the same fallback every other unregistered operation
(BET/SPORTS_EXCHANGE) already gets. `unified-api-contracts` is untouched: `ZERO_ALPHA`'s `venue_categories=
{"defi"}` gate still correctly applies to LEND/BORROW/WITHDRAW/REPAY/STAKE/UNSTAKE/FLASH_BORROW/FLASH_REPAY,
unaffected. Safe because `compose_validation`'s only output (`instruction.metadata["uac_op_detail"]`) has zero
downstream consumers (confirmed via full-repo grep), and TRANSFER already has its own real, independent per-venue
validation in `TransferHandler`/`TransferAdapter`. See `resolved_by` frontmatter for full detail. No operator/owner
design decision was required.

## Follow-ups

- [x] [BACKEND] P1. ~~Decide... whether TRANSFER needs its own `instruction_type`...~~ RESOLVED 2026-08-20: neither
      option was needed — see "Resolution" above. `execution-service`@instruction_router.py (uncommitted at doc-write
      time; ships in the same change as this doc).
