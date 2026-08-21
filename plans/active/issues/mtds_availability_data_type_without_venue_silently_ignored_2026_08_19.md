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

- [ ] [BACKEND] P1. **Decide and implement the correct contract**: either reject `data_type` without `venue` with a
      422 naming the missing parameter, or make the filter work independently of `venue`. Do NOT leave a third
      option where it silently no-ops. Whichever is chosen, the API reference must be updated in the same change.
- [ ] [REVIEW] P1. **Check the sibling parameters on the same endpoint** — `asset_group`, `instrument_type` and any
      other optional filter — for the same conditional-branch bug. One was found by reading the code; the others
      were not checked.
- [ ] [AGENT] P2. **Sweep the three external routers for silent-no-op parameters generally**
      (`instruments-service/.../external.py`, `market-tick-data-service/.../external.py`,
      `execution-service/.../external_instruction_api.py`). A parameter that is accepted, ignored and returns 200 is
      indistinguishable from one that worked — this is exactly the class of defect that only shows up when a client
      trusts the result.

## Progress Log

**2026-08-19 — filed.** Not fixed; no MTDS code touched. Surfaced during client-artefact work, so it is disclosed
in the API reference as known behaviour pending this fix rather than documented as intended.

- **context-scout 2026-08-20**: populated context_scope (3 entries).
