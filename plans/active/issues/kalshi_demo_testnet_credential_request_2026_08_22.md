---
doc_type: issue
title: KALSHI demo/testnet account credential gap — operator provisioning request filed
summary: >-
  KALSHI is the only Prediction venue with a declared testnet (POLYMARKET has none, `supports_testnet=False`), but
  its demo host (demo-api.kalshi.co) rejects the production-provisioned kalshi-api-key-id/kalshi-private-key-pem
  secrets with HTTP 401 — Kalshi's demo requires its own separately-provisioned demo account + key, which does not
  exist and is not self-provisionable from an agent session. Files the operator credential-provisioning ask per
  the external-data-always-available-rule HARD RULE (BLOCKED-CREDENTIALS taxonomy, not a descope).
status: open
nature: issue
asset_group: [prediction]
stage: [execution]
repos: [execution-service]
scope: [engineer, admin]
tags: [kalshi, prediction, testnet, credential-request, blocked-credentials, venue-readiness]
related:
  [
    /plans/active/prediction_venue_smoke_batch1_2026_08_20.md,
    /plans/active/venue_smoke_test_bar_2026_08_16.md,
    /codex/02-data/external-data-always-available-rule.md,
  ]
created: 2026-08-22
author: slot-18 (backend_engineer craft)
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
drift_direction: advance-code
depends_on: []
source: ["prediction_venue_smoke_batch1_2026_08_20.md todo 3 — 'file an operator credential request when a credential gap is confirmed'"]
resolved_by:
locked_by:
locked_since:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/prediction_venue_smoke_batch1_2026_08_20.md,
    /codex/02-data/external-data-always-available-rule.md,
    execution-service/execution_service/sports_execution/adapters/exchanges/kalshi.py,
    execution-service/tests/sports_execution/unit/test_kalshi_adapter.py,
  ]
---

# KALSHI demo/testnet credential request

## What I found

`VENUE_TO_ASSET_GROUP["prediction"]` declares exactly two venues — KALSHI and POLYMARKET
(`unified-api-contracts/unified_api_contracts/registry/market_data_categories.py:658-662`). Their UAC
`SourceCapability` declarations diverge on testnet:

- **KALSHI** — `supports_testnet=True`, `base_urls={"mainnet": ..., "testnet": "https://demo-api.kalshi.co"}`
  (`unified-api-contracts/unified_api_contracts/registry/capability_declarations/_sports.py:140-157`). The execution
  adapter carries the same demo host as a named constant
  (`execution-service/execution_service/sports_execution/adapters/exchanges/kalshi.py:100`,
  `KALSHI_DEMO_BASE = "https://demo-api.kalshi.co"`).
- **POLYMARKET** — `supports_testnet=False`, no `"testnet"` key at all (`_sports.py:222-239`). No testnet/sandbox
  reference exists anywhere in execution-service/instruments-service/MTDS Polymarket code. Already the honest answer:
  `PolymarketCLOBAdapter.simulate_order_fill()` / `.paper_place_order()` (matching-engine simulation against a real
  captured/live order book). No credential gap on this venue.

KALSHI's demo host was live-probed 2026-08-09
(`execution-service/tests/sports_execution/unit/test_kalshi_adapter.py:454-461`) using the real provisioned
production secrets (`kalshi-api-key-id`/`kalshi-private-key-pem`) — **rejected with HTTP 401
authentication_error/NOT_FOUND**. Kalshi's demo environment requires its own, separately-provisioned demo
account + API key; it is not derivable from the production credential and is not self-provisionable from this
session (no self-serve demo signup reachable without an operator-owned Kalshi account/email).

## Why it matters

Per `venue_smoke_test_bar_2026_08_16.md`'s definition-of-done, "every venue has a recorded testnet verdict,
including 'none, simulate via our matching engine' where that is the answer" — KALSHI's verdict IS recorded
(HAS-TESTNET, credential gap open), but the venue cannot advance past that recorded-gap state to an actual
testnet-verified smoke result without the missing demo credential. Per
`/codex/02-data/external-data-always-available-rule.md`, an exhausted/unprovisionable credential path is an
operator ask, never a silent descope — this doc is that ask, filed alongside `BLK-3d8c3d9e`
(`POST /api/slots/18/blocked` on task `prediction_venue_smoke_batch1-0330ea6859d9`, 2026-08-22).

## Recommended decision

- **(A) [RECOMMENDED]** Operator (or a worker with Secret Manager WRITE access) creates/provisions a Kalshi demo
  account (self-signup at `https://demo-api.kalshi.co`, or via Kalshi support) and stores its key material as new
  GSM secrets (e.g. `kalshi-demo-api-key-id` / `kalshi-demo-private-key-pem`), distinct from the production
  `kalshi-api-key-id`/`kalshi-private-key-pem` pair. Once provisioned, a follow-up todo wires
  `KalshiAdapter(base_url=KALSHI_DEMO_BASE)` against the new demo secrets for a genuine live-probed testnet smoke
  result.
- **(B)** Accept KALSHI as permanently `BLOCKED-CREDENTIALS` for testnet (no demo account ever provisioned) and
  treat it identically to POLYMARKET — matching-engine-simulation-only for both Prediction venues. This is a valid
  but strictly weaker outcome than (A); (A) costs only the demo-account signup, not a real-money exposure (per the
  operator's existing 2026-08-06 ruling that touching the LIVE mainnet exchange stays disallowed regardless — demo
  is the intended verification surface for exactly this reason).

## Status

`BLOCKED-CREDENTIALS` — awaiting operator [ack] on `BLK-3d8c3d9e`. Not a blocker for `prediction_venue_smoke_batch1`'s
own P1 todo 3, whose gate ("every attempted path has a measured terminal result" / "file an operator credential
request when a credential gap is confirmed") is satisfied by this doc + the filed blocked-question.
