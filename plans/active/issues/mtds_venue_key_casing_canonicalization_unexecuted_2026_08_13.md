---
doc_type: issue
title: >-
  MTDS WS_FEED_CONNECTOR_FACTORIES venue-key casing canonicalization was RULED 2026-07-10 but never executed — the
  case-insensitive-lookup workaround the operator explicitly rejected is what's actually live
summary: >-
  fleet_data_acquisition_health_2026_06_21.md (archived) recorded a 2026-07-10 operator ruling: canonicalize every venue
  key in `WS_FEED_CONNECTOR_FACTORIES` to UPPERCASE, not a runtime case-insensitive fallback. Verified live 2026-08-13:
  the fallback is exactly what's deployed, DeFi/prediction venue keys are still lowercase, and no commit touching
  venue-key canonicalization has landed since the ruling.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer]
tags: [data-correctness, mtds, venue-registry, live-pipeline, technical-debt]
related:
  [
    /plans/archive/2026_08/issues/fleet_data_acquisition_health_2026_06_21.md,
    /plans/active/issues/instruments_remaining_work_audit_2026_07_10.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: 2026-08-13
author: main-agent (blocked-question BLK-00e5bdf7 follow-up)
source:
  "Re-verification of fleet_data_acquisition_health_2026_06_21.md's own unexecuted-fix caveat, prompted while archiving
  that doc as part of resolving blocked-question BLK-00e5bdf7."
assigned_vm: NA
execution_scope: local-only
assigned_role: data_engineering
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.4
drift_direction: advance-code
parent_epic: mtds_mdps_master
depends_on: []
resolved_by:
locked_by:
last_updated: 2026-08-13
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/connectors/websocket_streaming_handler.py,
    market-tick-data-service/market_tick_data_service/live/connectors/polymarket_ws.py,
    market-tick-data-service/market_tick_data_service/live/connectors/polymarket_clob_ws.py,
    market-tick-data-service/market_tick_data_service/live/connectors/jito_defi_ws.py,
  ]
---

# MTDS venue-key casing canonicalization: ruled, never executed

## What this is

`fleet_data_acquisition_health_2026_06_21.md` (archived 2026-08-13) documented a registry-casing bug: CeFi venues in
`WS_FEED_CONNECTOR_FACTORIES` are UPPERCASE (`BYBIT`, `KRAKEN-FUTURES`, `HYPERLIQUID`, `ASTER`), DeFi/prediction venues
are lowercase (`polymarket`, `jito`, `curve`, `orca`, `raydium`, `phoenix`, `morpho`, `kalshi`) — a shard-spec passing
`POLYMARKET` (uppercase) hit `NotImplementedError: no WSFeedConnector for 'POLYMARKET'`. **RULED 2026-07-10 (operator,
revised from an earlier case-insensitive-lookup proposal that a later review flagged as a workaround)**: canonicalize
every venue key to UPPERCASE — not a runtime fallback that leaves the registry itself inconsistent.

## Verified 2026-08-13: the ruling was never executed

Direct code read + `git log --since=2026-07-10` on the relevant files:

- **The rejected workaround is exactly what's live**: `websocket_streaming_handler.py:138-142` —
  `WS_FEED_CONNECTOR_FACTORIES.get(venue) or .get(venue.lower()) or .get(venue.upper())`. `git blame` on those lines
  shows commit `5830cc81c` dated 2026-06-21 — **before** the 2026-07-10 ruling, meaning the ruling was never acted on at
  all, not even attempted and reverted.
- **DeFi/prediction keys are still lowercase**, unchanged: `curve_defi_ws.py:386` → `"curve"`, `orca_defi_ws.py:48` →
  `"orca"`, `raydium_defi_ws.py:48` → `"raydium"`, `phoenix_ws.py:305` → `"phoenix"`, `morpho_defi_ws.py:258` →
  `"morpho"`, `kalshi_ws.py:320` → `"kalshi"`. `jito_defi_ws.py:242-243` registers both `"jito"` and `"JITO-SOLANA"` — a
  one-off patch for one venue, not the canonicalization the ruling asked for.
- **`polymarket` is registered in BOTH casings from two different connectors** — `polymarket_ws.py:324` (Gamma API,
  lowercase) and `polymarket_clob_ws.py:547` (CLOB, uppercase, explicitly kept distinct) — itself a sign the registry
  was never unified.
- `git log --since=2026-07-10` on `websocket_streaming_handler.py`, `connector_registry.py`, `polymarket_ws.py`,
  `polymarket_clob_ws.py`, `jito_defi_ws.py` shows no commits touching venue-key casing since the ruling (only unrelated
  `IS_TEST_RUN` bucket-routing commits on 2026-07-18).

## Why this matters

The fallback lookup masks the underlying inconsistency well enough that nothing pages on it — which is exactly why it
sat unexecuted for over a month. It is not urgent (live capture works via the fallback), but it is the SSOT's own
documented decision going silently unimplemented, and a new venue integration that doesn't know to register both casings
(or relies on the fallback existing) will re-inherit this fragility.

## Todos

- [ ] [CODE] P2. Canonicalize every key in `WS_FEED_CONNECTOR_FACTORIES` to UPPERCASE (and every producer of a venue
      string that keys into it — shard-specs, launch scripts) per the 2026-07-10 ruling. Scope: `polymarket_ws.py`,
      `polymarket_clob_ws.py` (reconcile the two `polymarket` registrations to one canonical key),
      `jito_defi_ws.py`/`curve_defi_ws.py`/`orca_defi_ws.py`/`raydium_defi_ws.py`/`phoenix_ws.py`/`kalshi_ws.py`. Keep
      the `websocket_streaming_handler.py:138-142` fallback in place during the transition (defense in depth), remove it
      only once every registration is confirmed canonical. **Done when**: every venue key in the registry is UPPERCASE,
      a live shard-spec dispatch for each affected venue is confirmed working, and a follow-up removes the now-redundant
      lowercase/uppercase fallback branches.
