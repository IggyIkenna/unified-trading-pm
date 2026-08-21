---
doc_type: issue
title: MTDS external availability endpoint silently ignores data_type when venue is absent
summary: >-
  `GET /external/market-data/availability` accepts a `data_type` filter, but when `venue` is not also supplied the
  filter is silently dropped rather than rejected — the caller gets an unfiltered result and HTTP 200. Found while
  building the client-facing API reference from the router source. A counterparty filtering by data_type alone
  receives wrong data with no signal that their parameter was discarded.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer, admin]
tags: [mtds, external-api, silent-fallback, client-disclosure, measurement-integrity]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /codex/14-customer-journeys/commercial-model/platform-api-reference.html,
    /plans/archive/2026_08/issues/uac_get_venue_asset_group_silently_returns_cefi_for_all_venues_2026_08_19.md,
  ]
created: 2026-08-19
last_updated: "2026-08-19"
parent_epic: system_readiness_master
assigned_vm: NA
locked_by:
locked_since:
resolved_by:
execution_scope: local-only
priority: P1
severity: P1
source: >-
  Found 2026-08-19 by the sub-agent building platform-api-reference.html, reading
  market-tick-data-service/market_tick_data_service/api/routers/external.py:150-157 directly rather than trusting
  the endpoint's docstring.
drift_direction: advance-code
depends_on: []
context_scope:
  [
    market-tick-data-service/market_tick_data_service/api/routers/external.py,
    /codex/14-customer-journeys/commercial-model/platform-api-reference.html,
    /plans/archive/2026_08/issues/uac_get_venue_asset_group_silently_returns_cefi_for_all_venues_2026_08_19.md,
  ]
---

# `data_type` without `venue` is silently ignored

`market-tick-data-service/market_tick_data_service/api/routers/external.py:150-157` applies the `data_type` filter
only inside the branch that requires `venue`. Supplying `data_type` alone does not error and does not filter — the
caller gets HTTP 200 and an unfiltered body.

## Why it matters more than its size suggests

This is a **counterparty-facing** endpoint documented in
[platform-api-reference](/codex/14-customer-journeys/commercial-model/platform-api-reference.html). An external
caller narrowing by `data_type` will believe they received a filtered availability set. Nothing in the response
indicates otherwise.

It is the same defect shape as
[get_venue_asset_group returning cefi for everything](/plans/archive/2026_08/issues/uac_get_venue_asset_group_silently_returns_cefi_for_all_venues_2026_08_19.md):
a miss path that returns a plausible, valid-looking result instead of failing loudly. Two independent instances in
one day suggests the pattern is worth a sweep, not just two point fixes.

## Todos

- [x] ✅ [BACKEND] P1. **Decide and implement the correct contract**: either reject `data_type` without `venue` with a
      422 naming the missing parameter, or make the filter work independently of `venue`. Do NOT leave a third
      option where it silently no-ops. Whichever is chosen, the API reference must be updated in the same change.
      — market-tick-data-service@8addeac2 + evidence: chose "make the filter work independently of venue" (more
      useful than a 422, and non-breaking for existing venue+data_type callers). New `elif data_type is not None:`
      branch in `get_availability()` returns `data_type_summary_by_venue` (every venue's entry for that data_type,
      from the same `by_venue_data_type` rollup). 2 new regression tests
      (`test_data_type_without_venue_filters_across_every_venue`,
      `test_data_type_without_venue_matching_nothing_is_empty_not_fabricated`) both pass. Doc updated in the same
      pass: `platform-api-reference.html`'s "Known limitation, disclosed here" callout rewritten as the fixed
      reality with a Source citation (unified-trading-pm, same session).
- [x] ✅ [REVIEW] P1. **EXTRACTED 2026-08-21** — check the sibling parameters (`asset_group`, `instrument_type`,
      any other optional filter) on the same endpoint for the same conditional-branch bug. Extracted to
      `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md` for AO dispatch (na-eligibility-audit,
      cross-cutting tranche, batch 2 of 3).
- [x] ✅ [AGENT] P2. **EXTRACTED 2026-08-21** — sweep the three external routers for silent-no-op parameters
      generally. Extracted to `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md` for AO dispatch
      (na-eligibility-audit, cross-cutting tranche, batch 2 of 3).
- [ ] [AGENT] P3. Every todo above is done — this doc is archive-ready. Run the 6-step archival ritual
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`), including the referrer fix for the
      4 files this session found still citing this doc's path (`plans/active/cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md`,
      `codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html`,
      `plans/active/issues/external_market_data_response_leaks_vendor_pipeline_mode_2026_08_20.md`,
      `plans/audit/results/code_readiness_allocation_2026_08_19.json`). Deferred rather than done inline this
      session because 2 of those 4 files are actively-edited by other concurrent sessions (the T5 walkthrough
      wave-2 pass and the AO-dispatched batch21 plan) — touching them here risked a collision; a dedicated pass
      once those land is safer.

## Findings — sibling parameter audit (2026-08-21)

Batch21 item (`cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md`), source: this doc's todo 2 ("check the
sibling parameters ... for the same conditional-branch bug"). Read `get_availability()` in
`market-tick-data-service/market_tick_data_service/api/routers/external.py` (current HEAD, post-fix commit
`8addeac2` confirmed as an ancestor) in full. The endpoint's complete parameter set is exactly four:
`asset_group`, `venue`, `data_type`, `date` — no `instrument_type` parameter exists on this endpoint.

| Parameter | Verdict | Evidence |
| --- | --- | --- |
| `asset_group` | **UNAFFECTED** — not exposed to this bug class at all | `Query(...)` (required, not optional); FastAPI 422s the request before the handler body runs if absent, so there is no "supplied but silently ignored" path. It is also read unconditionally in every branch (`_validate_asset_group`, `enforce_market_data_entitlement`, `by_asset_group.get(ag)` in the base `result` dict built before any `venue`/`data_type` branching) — never gated behind a sibling parameter's presence. |
| `instrument_type` | **N/A — parameter does not exist** | Grepped `get_availability`'s signature (lines 121-127) and the whole file: no `instrument_type` Query parameter anywhere on this endpoint. The only `instrument_type` hit in the repo's test suite (`tests/unit/api/test_external_router.py:39`) is a literal path-segment substring inside a mocked GCS object name for the delivery-batch shard-matching tests, unrelated to a query parameter on `/availability`. The task brief's premise (that `instrument_type` is one of this endpoint's sibling filters) does not hold — there is nothing to verify affected/unaffected for a parameter that isn't there. |
| `date` | **UNAFFECTED** | Optional (`Query(None, ...)`), but consumed unconditionally before any `venue`/`data_type` branch: `candidate_dates = [date] if date is not None else _lookback_dates(...)` (line 153) feeds the coverage-file lookup loop and is echoed as `requested_date`/`resolved_date` in every response shape, regardless of whether `venue` or `data_type` is present. Never gated behind a sibling parameter. |
| `venue` | **UNAFFECTED** (the conditioning parameter itself, not a sibling being dropped) | Every branch that can fire either consumes `venue` when present (the `if venue is not None:` arm — entitlement check, `result["venue"]`, `result["venue_summary"]`) or is the `elif data_type is not None:` arm reached only when `venue` is absent. There is no code path where `venue` is supplied and silently has zero effect. |

**Not the same bug class, noted so a future reader doesn't conflate it**: the docstring (lines 141-145) documents
that an explicit single-`venue` ask 403s if out of scope, while the `data_type`-without-`venue` aggregate instead
*silently narrows* to the caller's entitled venues via `entitled_venues(...)` (never a 403). That narrowing is
deliberate entitlement scoping — the filter is still applied and still has effect (fewer venues in the response),
not a parameter whose value is discarded with no effect at all. It is not an instance of the silent-drop pattern
this todo was checking for.

**Conclusion**: only `data_type` was ever affected by the conditional-branch silent-drop bug (fixed 2026-08-19/21,
`market-tick-data-service@8addeac2`). No other current or claimed parameter on this endpoint exhibits the pattern.

## Findings — general sweep of the three external routers for silent-no-op parameters (2026-08-21)

Batch21 item ("Sweep the three external routers for silent-no-op parameters generally", source: this doc's todo 3),
pure investigation/report per that todo's own scope — nothing below was fixed. All three named routers read in
full: `instruments-service/instruments_service/api/routers/external.py`,
`market-tick-data-service/market_tick_data_service/api/routers/external.py`,
`execution-service/execution_service/api/external_instruction_api.py`.

**Method**: for the two query-param routers (instruments-service, MTDS), traced every declared `Query(...)`
parameter through its handler body to confirm it reaches a branch with real effect. For execution-service's
JSON-envelope router, traced every field on each dispatched `StrategyInstructionV2` member
(`unified_api_contracts/internal/architecture_v2/schemas.py`) through its translation function into the internal
instruction/params object, then repo-wide-grepped (`rg`, non-test files) the field name to confirm zero downstream
consumption before calling it dropped — the same bug shape this doc's own `data_type` fix instance had (accepted,
never read, HTTP 200 returned).

### instruments-service `external.py` — CLEAN

Both endpoints' full declared parameter sets thread straight into their query functions with no conditional-drop
branch: `GET /v1/instruments` (`asset_group`, `venue`, `instrument_type`, `day`, `limit`, `cursor`) all reach
`query_instruments(...)` (cursor is decoded and cross-validated against the other params, not silently ignored);
`GET /v1/instruments/bulk` (`asset_group`, `venue`, `day`) all reach `build_bulk_parquet(...)`. No silent-no-op
parameter found.

### market-tick-data-service `external.py` — CLEAN

`GET /availability`'s only historical instance of this bug class (`data_type` without `venue`) is already fixed
(`market-tick-data-service@8addeac2`, see this doc's own history above) and its full sibling-parameter set was
independently re-verified clean in the "Findings — sibling parameter audit" section above. `GET /delivery/batch`
(`asset_group`, `venue`, `data_type`, `date`, `file`, `cursor`) and `GET /delivery/stream` (`asset_group`,
`data_type`, `after`, `limit`, `topology`) both thread every declared parameter into their respective list/stream
calls with no conditional-drop branch. No silent-no-op parameter found.

### execution-service `external_instruction_api.py` — NOT CLEAN, 3 confirmed silent-no-op fields

Unlike the two query-param routers, this router accepts a typed JSON envelope per action, so the failure shape is
a schema FIELD accepted-but-never-read by the translation function, rather than a dropped query param — same
end-user-visible defect (client sets a real value, gets HTTP 200, the value has zero effect, no error surfaces):

1. **`TradeInstruction.stop_loss_price` / `TradeInstruction.take_profit_price`** (schemas.py:306-307) — both
   accepted on the envelope. `_build_strategy_instruction_from_trade` (external_instruction_api.py:263-284) reads
   only `target_venue`/`reference_price`/`max_price`/`min_price`/`direction`/`target_position_units`, then calls
   `ManualOperationHandler.build_instruction(...)` (`execution_service/operations/manual/__init__.py:207-232`),
   whose keyword-only signature has NO `stop_loss_price`/`take_profit_price` parameter at all — there is no
   downstream place for these two values to go on this path. Repo-wide grep confirms the only non-test hits for
   both names are in the unrelated BATCH/backtest instruction loaders
   (`engine/execution/instruction_loader.py`, `strategy_instructions/loader.py`,
   `utils/validation/instruction_validator.py`) — a completely different code path from this external HTTP
   surface. A caller submitting a TRADE with a stop-loss/take-profit gets HTTP 200 and a real order placed with
   neither protection wired.
2. **`BridgeInstructionV2.bridge_hint`** (schemas.py:426) — accepted on the envelope.
   `_build_execution_instruction_from_bridge` (external_instruction_api.py:505-532) builds the internal
   `ExecutionInstruction` from `chain_from`/`chain_to`/`asset`/`target_balance_at_destination` plus a hardcoded
   `metadata={"force_transfer_type": "BRIDGE"}` — `envelope.bridge_hint` is never read. Repo-wide grep confirms
   the only `bridge_hint` hit in execution-service is this router's own docstring (line 518), which documents the
   field's ABSENCE-of-a-recipient-address implication but never that the hint itself is dropped. A caller naming
   a preferred bridge route gets HTTP 200 (or a real PENDING bridge) with their route preference silently ignored
   — `LiveBridgeTransferAdapter` picks its own resolved route regardless.
3. **`QuoteInstruction.skew_on_inventory`** (schemas.py:379, default `True`) — accepted on the envelope.
   `_register_quote_instruction` (external_instruction_api.py:287-325) passes the whole envelope to
   `QuoteMaintainer.register_quote_instruction` -> `quote_instruction_to_delta_proxy_params`
   (`execution_service/engine/quote_maintenance.py:141-176`), which builds `DeltaProxyParams` from
   `reference_price`/`half_spread_bps`/`underlying_instrument_id`/`delta`/`gamma`/`max_inventory_abs` — never
   reads `instruction.skew_on_inventory`. Repo-wide grep confirms zero non-test hits for `skew_on_inventory`
   anywhere in execution-service. A caller registering a quote with inventory-skew disabled or tuned gets HTTP 200
   ("REGISTERED") with the skew behavior unchanged from whatever the repricer's own default is.

**Checked and NOT counted as a defect**: `QuoteInstruction.refresh_cadence_ms` has no execution-side consumption
either, but per its own field docstring this is BY DESIGN — it documents how often the STRATEGY side re-emits the
cached instruction (a strategy-side keep-alive cadence), not something execution-service is meant to act on;
`register_quote_instruction`'s own docstring explicitly notes it deliberately does not reset `_last_submitted` for
this reason. This is a documented, intentional non-consumption, not the silent-no-op pattern this sweep targets.

**Not investigated in this pass**: the DeFi instruction types (`SWAP`/`LEND`/`WITHDRAW`/`STAKE`/`UNSTAKE`/
`BORROW`/`REPAY`/`LP_MINT`/`LP_BURN`) and `AtomicInstruction` dispatch through `_submit_defi_instruction`/
`_submit_atomic_instruction`, which live in the sibling `external_instruction_defi.py` module, not the named
`external_instruction_api.py` file this todo scoped to sweep — out of scope for this pass, not swept.

## Progress Log

**2026-08-19 — filed.** Not fixed; no MTDS code touched. Surfaced during client-artefact work, so it is disclosed
in the API reference as known behaviour pending this fix rather than documented as intended.

- **context-scout 2026-08-20**: populated context_scope (3 entries).
- **2026-08-21 — fixed and shipped** (part of the platform-api-reference.html zero-disclosure operator directive):
  `market-tick-data-service@8addeac2` (direct-push dirty-deps carve-out — quickmerge pre-flight was blocked on a
  concurrent session's live uncommitted WIP in unified-api-contracts, unrelated to this diff). All 3 todos now
  done; archival deferred as its own todo above (2 of 4 referrers are concurrently in-flight elsewhere).
- **na-eligibility-audit 2026-08-21**: RECLASSIFY (per-todo split) — todos 2-3 (check sibling params; sweep 3
  external routers) are pure investigation tasks; extracted to
  `cross_cutting_satellite_ao_dispatch_batch21_2026_08_21.md`. Todo 1 ("Decide and implement the correct
  contract") stays `assigned_vm: NA` — explicit design decision. Doc's own `assigned_vm: NA` unchanged.
  Cross-cutting tranche, batch 2 of 3.
- **2026-08-21 (batch21 item, sibling-parameter audit)** — closed the sibling-parameter todo (batch21's own copy).
  Verdict: `asset_group` UNAFFECTED (required, not optional — no silent-drop path exists); `instrument_type` N/A
  (no such parameter exists on this endpoint at all); `date` UNAFFECTED (consumed unconditionally regardless of
  `venue`/`data_type`); `venue` UNAFFECTED (the conditioning parameter itself). Only `data_type` was ever affected,
  already fixed. Full evidence in the new "Findings — sibling parameter audit (2026-08-21)" section above.
- **2026-08-21 (batch21 item, general 3-router sweep, slot-5)** — closed the "sweep the three external routers for
  silent-no-op parameters generally" todo (this doc's todo 3). Pure investigation, no code touched.
  instruments-service `external.py` and market-tick-data-service `external.py`: CLEAN (every declared parameter
  threads through with real effect). execution-service `external_instruction_api.py`: NOT CLEAN — 3 confirmed
  silent-no-op envelope fields (`TradeInstruction.stop_loss_price`/`take_profit_price` never reach
  `ManualOperationHandler.build_instruction`; `BridgeInstructionV2.bridge_hint` never read by the bridge
  translation function; `QuoteInstruction.skew_on_inventory` never read by
  `quote_instruction_to_delta_proxy_params`). Full evidence + per-field grep confirmation in the new "Findings —
  general sweep of the three external routers for silent-no-op parameters (2026-08-21)" section above. DeFi/Atomic
  dispatch (in the sibling `external_instruction_defi.py`, not the named router file) explicitly not swept — noted
  as out of scope, not silently skipped.
