---
doc_type: issue
title: KrakenCeFiAdapter(futures=True) routes every private call through the Kraken SPOT REST API, not Kraken Futures — place/cancel/amend all hit the wrong venue
summary: >-
  execution-service's KrakenCeFiAdapter (execution_service/trade_execution/adapters/kraken_rest_adapter.py) accepts
  a `futures: bool` constructor flag and derives `venue_name = "KRAKEN-FUTURES" if futures else "KRAKEN-SPOT"`, but
  every private-endpoint method (place_order, cancel_order, get_order_status, and the amend_order added by
  cefi_execution_cancel_amend_fake_success_stub_2026_08_16.md's P2 fix) calls the SAME
  `_do_private_post()`/`_KRAKEN_REST_BASE_URL` (Kraken SPOT's `https://api.kraken.com`, HMAC-SHA512
  API-Key/API-Sign signing) regardless of `self.futures`. Kraken Futures is a genuinely separate REST surface
  (`https://futures.kraken.com/derivatives/api/v3/...`, APIKey/Authent header auth) that this adapter never
  implements. Found 2026-08-17 while researching amend_order's real per-venue wiring for the P2 todo above — the
  class's own docstring even says "For futures testnet, use KrakenFuturesCeFiAdapter", a class that does not exist
  anywhere in this repo, suggesting the futures-specific implementation was planned but never built.
status: open
nature: issue
asset_group: [cefi]
stage: [execution]
repos: [execution-service]
scope: [engineer]
tags: [execution, order-management, financial-correctness, live-money-risk, stub-code, venue-readiness, kraken]
related:
  [
    /plans/active/issues/cefi_execution_cancel_amend_fake_success_stub_2026_08_16.md,
    /plans/active/cefi_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
  ]
created: 2026-08-17
author: interactive-session
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: backend_engineer
drift_direction: advance-code
depends_on: []
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Found 2026-08-17 while wiring cefi_execution_cancel_amend_fake_success_stub_2026_08_16.md's P2 todo (per-venue
  atomic-amend verification) — confirmed by reading kraken_rest_transport.py's _do_public_get/_do_private_post in
  full: both hard-code `_KRAKEN_REST_BASE_URL` from kraken_rest_mapping.py with no branch on self.futures anywhere
  in the adapter, transport, or mapping modules.
context_scope:
  [
    execution-service/execution_service/trade_execution/adapters/kraken_rest_adapter.py,
    execution-service/execution_service/trade_execution/adapters/kraken_rest_transport.py,
    execution-service/execution_service/trade_execution/adapters/kraken_rest_mapping.py,
  ]
---

# KRAKEN-FUTURES silently uses the Kraken SPOT REST API today

## What I found

`KrakenCeFiAdapter.__init__` derives `venue_name = "KRAKEN-FUTURES" if futures else "KRAKEN-SPOT"`
(`kraken_rest_adapter.py:159`) and stores `self.futures`, but `self.futures` is never read again anywhere in the
class. Every private-endpoint method — `place_order` (line 260), `cancel_order` (line 311),
`get_order_status` (line 358), and `amend_order` (added by this session) — calls
`self._do_private_post(f"{_KRAKEN_API_VERSION}/private/<Op>", data)`, which is defined once in
`KrakenRestTransportMixin` (`kraken_rest_transport.py:127-162`) and unconditionally builds its request URL as
`f"{_KRAKEN_REST_BASE_URL}{url_path}"` — `_KRAKEN_REST_BASE_URL` is a single module constant in
`kraken_rest_mapping.py` pointing at Kraken's **Spot** REST base (`https://api.kraken.com`), signed with Kraken
Spot's HMAC-SHA512 `API-Key`/`API-Sign` scheme (`_sign_kraken_request`).

Kraken Futures is a genuinely separate product with its own REST base
(`https://futures.kraken.com/derivatives/api/v3/...`) and its own auth headers (`APIKey`/`Authent`, a different
signing algorithm) — confirmed via Kraken's own official docs
(`https://docs.kraken.com/api-reference/order-management/edit-order`,
`https://docs.kraken.com/api/docs/futures-api/trading/edit-order-spring/`) while researching this session's amend
todo. This adapter never implements that surface. The class's own docstring even references a
`KrakenFuturesCeFiAdapter` ("For futures testnet, use KrakenFuturesCeFiAdapter") — grepped the entire repo, no such
class exists, suggesting a planned-but-never-built split.

**Practical effect**: constructing `KrakenCeFiAdapter(futures=True)` and calling `place_order`/`cancel_order`/
`get_order_status`/`amend_order` sends every request to the Kraken **Spot** account instead of Kraken Futures. With
real credentials that happen to be valid for both (Kraken issues separate API keys per product, so this would most
likely surface as an auth/permission failure or an "order not found" error rather than silently succeeding against
the wrong book) — but the failure mode isn't guaranteed benign, and either way KRAKEN-FUTURES trading is completely
non-functional through this adapter today, not merely degraded.

## Why it matters

Same live-money-correctness class as `cefi_execution_cancel_amend_fake_success_stub_2026_08_16.md`: a caller
configuring the system to trade KRAKEN-FUTURES has no way to know from this adapter's behavior that it is silently
misrouted. Unlike that issue's stub endpoints, this doesn't fake success — Kraken Spot will genuinely reject an
order/cancel/amend request carrying a Futures-only order ID or exceeding Spot-only credential scope, so the
failure mode is likely a loud auth/not-found error rather than a silent wrong-fill. That's a materially safer
failure shape than a fake success, which is why this is filed as its own P0 rather than escalated as a "big
finding" interrupt — but it still means KRAKEN-FUTURES is completely non-functional, not degraded, through this
code path.

## What I have NOT verified

- Whether KRAKEN-FUTURES is currently reachable via any OTHER path in execution-service (a different adapter class,
  a factory branch that never actually constructs `KrakenCeFiAdapter(futures=True)` in practice) — this issue is
  scoped to what `kraken_rest_adapter.py` itself does, not a full reachability sweep like the parent issue's P0
  todo did for cancel/amend.
- The exact HTTP-level failure Kraken Spot returns for a Futures-only credential/order — inferred from Kraken's
  separate-per-product credential model, not observed against live credentials (this repo has no Kraken
  credentials — Kraken's own status in this codebase is BLOCKED-CREDENTIALS, see the class's own
  `CREDENTIALS_STATUS`).

## Todos

- [ ] [BACKEND] P0. **Confirm real-world reachability of `KrakenCeFiAdapter(futures=True)`** — grep every
      construction site (factory/adapter-registry code) to determine whether anything in production actually
      instantiates it with `futures=True` today, mirroring the reachability-first approach the parent issue's own
      P0 todo used. Done-when: a cited LIVE-REACHABLE or DEAD-CODE-TODAY verdict with the construction site(s)
      named (or their absence confirmed).
- [ ] [BACKEND] P0. **Implement the real Kraken Futures REST transport** — either a new `futures.kraken.com`-aware
      branch inside `KrakenRestTransportMixin` (selected by `self.futures`) or a dedicated
      `KrakenFuturesCeFiAdapter` class (matching the docstring's original intent), implementing the distinct
      APIKey/Authent auth scheme per Kraken's official Futures API docs
      (`https://docs.kraken.com/api-reference/order-management/edit-order`,
      `https://docs.kraken.com/api/docs/futures-api/trading/order-management/`). Done-when: `place_order`/
      `cancel_order`/`get_order_status`/`amend_order` for `futures=True` genuinely hit
      `https://futures.kraken.com/derivatives/api/v3/...`, verified via a unit test asserting the request URL/host,
      not just that a mock was called.
- [ ] [BACKEND] P1. **Audit for the same class of gap on any other multi-product adapter in this repo** (a single
      adapter class serving two API surfaces via a boolean flag) — this exact shape (constructor flag set, never
      read again in the transport layer) is easy to reintroduce. Done-when: a cited sweep result (found N more /
      found none) across `execution_service/trade_execution/adapters/`.

## Progress Log

- **2026-08-17**: Filed while wiring `cefi_execution_cancel_amend_fake_success_stub_2026_08_16.md`'s P2 amend todo
  — the amend implementation for `KrakenCeFiAdapter` necessarily inherits this pre-existing gap (documented inline
  at the call site with a pointer to this issue) rather than silently fixing the whole class's transport layer as
  unplanned scope within that session.
