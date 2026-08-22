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
last_updated: 2026-08-21
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

- [ ] [BACKEND] P3. Remove the case-insensitive venue-key fallback fleet-wide — per D103 ruling (2026-08-21,
      issues_corpus_completion_dispatch_2026_08_21.md ledger): every venue's dual-registration makes it redundant;
      both polymarket connectors already resolve under canonical keys. Remove the fallback logic in
      `resolve_ws_feed_venue_key()` (module-level — cite the symbol, its line range has already drifted once, see
      the 2026-08-19 correction below) and `WebsocketStreamingHandler._resolve_connector`, and update both
      docstrings. Done-when: a live dispatch test confirms every registered venue (including both polymarket
      connectors under their own canonical-cased keys) still resolves correctly with the fallback removed, and
      `quality-gates.sh` is green. Repo: market-tick-data-service.

## Progress Log

- **2026-08-17 (slot-8, backend_engineer)**: filed as the narrow follow-up
  `mtds_venue_key_casing_reverify_then_execute_ao_dispatch_2026_08_16.md`'s Progress Log recommended, after
  closing the phoenix registry gap in that plan (`market-tick-data-service@49a2d0c9`) left polymarket's
  intentional dual-casing as the sole remaining blocker on fallback removal.
- **na-eligibility-audit 2026-08-17** [body-hash:b7816f2287ce8a02]: KEEP-NA, valid -- Fresh doc (2026-08-17). Sole todo is an explicit [OPERATOR] binary product/architecture decision (accept polymarket's dual-casing split as permanent vs. treat as needing a narrower fallback) the doc's own text says it "doesn't have the authority to make." Both downstream code outcomes are fully pre-specified (websocket_streaming_handler.py:138-142); trivially AO-dispatchable once the operator answers. Cross-cutting tranche audit.
- **na-eligibility-audit 2026-08-19** (cross-cutting tranche): KEEP-NA, valid — Fresh doc (2026-08-17), 1 open todo = an explicit [OPERATOR]-tagged binary product/architecture decision the doc's own text says it lacks authority to make; both downstream code outcomes are fully pre-specified and.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
- **na-eligibility-audit 2026-08-21**: KEEP-NA, valid — reaffirmed unchanged. Sole todo is still an explicit
  [OPERATOR] binary product/architecture decision the doc's own text says it lacks authority to make; both
  downstream code outcomes are already fully pre-specified once the decision lands. Cross-cutting tranche, batch
  2 of 3.
- **2026-08-21 — ruling D103 (Venue-key case fallback removal)**: ADOPTED-REC 2026-08-21 (autonomous-dispatch
  authority, AUTONOMOUS_AGENT_RULES rule 2): Remove — every venue's dual-registration makes it redundant; both
  polymarket connectors already resolve under canonical keys. Source:
  /plans/active/issues_corpus_completion_dispatch_2026_08_21.md ledger.
