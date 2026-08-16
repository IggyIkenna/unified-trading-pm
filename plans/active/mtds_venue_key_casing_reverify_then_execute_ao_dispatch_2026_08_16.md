---
doc_type: plan
title: Re-verify then execute WS_FEED_CONNECTOR_FACTORIES venue-key UPPERCASE canonicalization (operator-ruled 2026-08-16)
summary: >-
  Operator asked to dispatch the 2026-07-10-ruled, never-executed WS_FEED_CONNECTOR_FACTORIES venue-key
  UPPERCASE canonicalization, with an explicit instruction to re-verify the design still matches current code
  first (time has elapsed since the 2026-08-13 investigation). Re-check the file list
  (`websocket_streaming_handler.py`, `curve_defi_ws.py`, `orca_defi_ws.py`, `raydium_defi_ws.py`, `phoenix_ws.py`,
  `morpho_defi_ws.py`, `kalshi_ws.py`, `jito_defi_ws.py`, `polymarket_ws.py`, `polymarket_clob_ws.py`) and the
  exact lowercase keys are still accurate against live code before executing the rename — then execute if
  confirmed.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [market-tick-data-service]
scope: [engineer]
tags: [cross-cutting, mtds, venue-registry, casing, canonicalization]
related:
  [
    /plans/active/issues/mtds_venue_key_casing_canonicalization_unexecuted_2026_08_13.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: observability_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.6
assigned_role: backend_engineer
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 10, 2026-08-16 — operator asked to re-verify design against current code first"
locked_by:
context_scope:
  [
    /plans/active/issues/mtds_venue_key_casing_canonicalization_unexecuted_2026_08_13.md,
    market-tick-data-service/market_tick_data_service/engine/connectors/websocket_streaming_handler.py,
  ]
locked_since:
resolved_by:
---

# Re-verify then execute WS_FEED_CONNECTOR_FACTORIES venue-key casing canonicalization

## Todos

- [ ] [CODE] P2. **RULED 2026-08-16 (operator): dispatch, but re-verify the design against current code first.**
      (1) Re-confirm live: `websocket_streaming_handler.py`'s case-insensitive-fallback lookup
      (`.get(venue) or .get(venue.lower()) or .get(venue.upper())`) is still what's deployed, and the exact
      lowercase venue keys (`polymarket`/`jito`/`curve`/`orca`/`raydium`/`phoenix`/`morpho`/`kalshi`, plus
      `jito`'s dual-registration and `polymarket`'s cross-connector dual-casing) are unchanged since 2026-08-13
      — a `git log --since=2026-08-13` check on the named files. If the file list or keys have drifted, update
      the plan before proceeding. (2) Canonicalize every key in `WS_FEED_CONNECTOR_FACTORIES` to UPPERCASE (per
      the 2026-07-10 ruling) and every producer of a venue string that keys into it (shard-specs, launch
      scripts). Remove the case-insensitive fallback entirely — the registry itself must be consistent, not
      papered over at lookup time. QG green. Repo: market-tick-data-service.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 10, operator ruling — scoped)**: extracted from
  `mtds_venue_key_casing_canonicalization_unexecuted_2026_08_13.md`, with the operator's explicit re-verify-first
  instruction folded into the dispatched todo itself rather than a separate pre-step.
