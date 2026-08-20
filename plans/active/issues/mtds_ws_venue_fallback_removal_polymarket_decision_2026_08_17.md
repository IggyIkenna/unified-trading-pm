---
doc_type: issue
title: >-
  MTDS WS_FEED_CONNECTOR_FACTORIES fallback removal blocked on one operator decision: is polymarket's
  dual-casing split the accepted permanent state?
summary: >-
  Every venue in WS_FEED_CONNECTOR_FACTORIES is now dual-registered under both its legacy lowercase key and its
  canonical UPPERCASE UAC key (curve/orca/raydium/morpho/jito/kalshi/phoenix) except polymarket, which is
  deliberately registered under TWO DIFFERENT casings for TWO DIFFERENT live connectors (Gamma API lowercase,
  CLOB uppercase). The 2026-07-10 ruling's "remove the case-insensitive fallback entirely" step needs one
  explicit decision on whether that split counts as the accepted final state before the fallback can come out.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer]
tags: [mtds, venue-registry, casing, canonicalization, operator-decision]
related: [/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
created: 2026-08-17
author: slot-8 (backend_engineer)
source: "Follow-up from mtds_venue_key_casing_reverify_then_execute_ao_dispatch_2026_08_16.md — fallback removal step deferred, needs an operator ruling, not a code investigation."
assigned_vm: NA
execution_scope: local-only
assigned_role: backend_engineer
priority: P3
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
drift_direction: advance-code
parent_epic: observability_master
depends_on: []
resolved_by:
locked_by:
last_updated: 2026-08-20
context_scope:
  [
    market-tick-data-service/market_tick_data_service/live/connectors/polymarket_ws.py,
    market-tick-data-service/market_tick_data_service/live/connectors/polymarket_clob_ws.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/websocket_streaming_handler.py,
  ]
---

# MTDS WS venue fallback removal: the one remaining decision

## What this is

The 2026-07-10 ruling (canonicalize `WS_FEED_CONNECTOR_FACTORIES` venue keys to UPPERCASE, then remove the
case-insensitive fallback lookup in `websocket_streaming_handler.py`) is now fully executed for every venue
except one: `polymarket`. As of `market-tick-data-service@49a2d0c9` (2026-08-17), every other DeFi/prediction
venue (`curve`, `orca`, `raydium`, `morpho`, `jito`, `kalshi`, `phoenix`) is dual-registered under both its
legacy lowercase key and its canonical UPPERCASE UAC key, so a canonical-key dispatch resolves for all of them
without needing the fallback.

`polymarket` is different by design, not by omission: `polymarket_ws.py` (Gamma API) registers lowercase
`"polymarket"`; `polymarket_clob_ws.py` (CLOB) registers uppercase `"POLYMARKET"` — two DIFFERENT connectors for
two DIFFERENT live data sources, each already resolving directly under its own canonical-cased key (neither
needs the fallback to work today).

## Why this matters

The fallback (`.get(venue) or .get(venue.lower()) or .get(venue.upper())`) is now redundant for every venue
except it also silently masks any FUTURE accidental collision between the two polymarket connectors (e.g. a
caller passing `"POLYMARKET"` when they meant the Gamma API one). Whether that's acceptable risk or something to
fix depends on a product/architecture call this doc doesn't have the authority to make.

## Todos

- [ ] [OPERATOR] P3. Decide: (a) accept polymarket's two-connector dual-casing split as the permanent final
      state (both keys already resolve directly; the fallback is not needed for it — so answering "yes" clears
      the way to remove the fallback fleet-wide with zero registration changes), or (b) treat it as a state that
      still needs the fallback as a documented, permanent accommodation. Once decided: if (a), remove the
      case-insensitive fallback in `resolve_ws_feed_venue_key()` (module-level) and
      `WebsocketStreamingHandler._resolve_connector` entirely and update its docstring — corrected 2026-08-19,
      plan-reconcile observability_master: the prior `:138-142` line-number citation had drifted, those lines are
      now `_resolve_connector`'s parameter list; the real fallback logic lives in `resolve_ws_feed_venue_key()`
      (module-level, lines ~63-85 as of this correction, cite the symbol not the line if it moves again); if
      (b), replace the blanket fallback with a narrower, explicitly-commented one scoped only to
      the polymarket case. Repo: market-tick-data-service.

## Progress Log

- **2026-08-17 (slot-8, backend_engineer)**: filed as the narrow follow-up
  `mtds_venue_key_casing_reverify_then_execute_ao_dispatch_2026_08_16.md`'s Progress Log recommended, after
  closing the phoenix registry gap in that plan (`market-tick-data-service@49a2d0c9`) left polymarket's
  intentional dual-casing as the sole remaining blocker on fallback removal.
- **na-eligibility-audit 2026-08-17** [body-hash:b7816f2287ce8a02]: KEEP-NA, valid -- Fresh doc (2026-08-17). Sole todo is an explicit [OPERATOR] binary product/architecture decision (accept polymarket's dual-casing split as permanent vs. treat as needing a narrower fallback) the doc's own text says it "doesn't have the authority to make." Both downstream code outcomes are fully pre-specified (websocket_streaming_handler.py:138-142); trivially AO-dispatchable once the operator answers. Cross-cutting tranche audit.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — Fresh doc (2026-08-17), 1 open todo = an explicit [OPERATOR]-tagged binary product/architecture decision the doc's own text says it lacks authority to make; both downstream code outcomes are fully pre-specified and.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
