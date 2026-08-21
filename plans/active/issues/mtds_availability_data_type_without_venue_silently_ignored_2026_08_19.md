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
