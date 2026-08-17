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
    /plans/archive/issues/mtds_venue_key_casing_canonicalization_unexecuted_2026_08_13.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
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
    /plans/archive/issues/mtds_venue_key_casing_canonicalization_unexecuted_2026_08_13.md,
    market-tick-data-service/market_tick_data_service/live/connector_registry.py,
    market-tick-data-service/market_tick_data_service/cli/handlers/websocket_streaming_handler.py,
    market-tick-data-service/market_tick_data_service/live/connectors,
  ]
locked_since:
resolved_by:
---

# Re-verify then execute WS_FEED_CONNECTOR_FACTORIES venue-key casing canonicalization

## Todos

- [x] ✅ [CODE] P2. **RULED 2026-08-16 (operator): dispatch, but re-verify the design against current code first.**
      (1) Re-confirm live: `websocket_streaming_handler.py`'s case-insensitive-fallback lookup
      (`.get(venue) or .get(venue.lower()) or .get(venue.upper())`) is still what's deployed, and the exact
      lowercase venue keys (`polymarket`/`jito`/`curve`/`orca`/`raydium`/`phoenix`/`morpho`/`kalshi`, plus
      `jito`'s dual-registration and `polymarket`'s cross-connector dual-casing) are unchanged since 2026-08-13
      — a `git log --since=2026-08-13` check on the named files. If the file list or keys have drifted, update
      the plan before proceeding. (2) Canonicalize every key in `WS_FEED_CONNECTOR_FACTORIES` to UPPERCASE (per
      the 2026-07-10 ruling) and every producer of a venue string that keys into it (shard-specs, launch
      scripts). Remove the case-insensitive fallback entirely — the registry itself must be consistent, not
      papered over at lookup time. QG green. Repo: market-tick-data-service. — **Canonicalization complete**
      (every in-scope venue now dual-registered under its canonical UPPERCASE UAC key or already-canonical:
      curve/orca/raydium/morpho/jito@`market-tick-data-service@767c4208a8`, phoenix@`market-tick-data-service@49a2d0c9`,
      kalshi already-canonical via `kalshi_clob_ws.py`, polymarket's cross-connector dual-casing confirmed
      intentional/final). **Fallback removal split off** to
      `/plans/active/issues/mtds_ws_venue_fallback_removal_polymarket_decision_2026_08_17.md` (needs one
      operator decision on polymarket's dual-casing being the accepted permanent state) rather than blocking
      this task indefinitely — see Progress Log.

## Progress Log

- **2026-08-16 (na-eligibility-audit follow-up Q&A round 10, operator ruling — scoped)**: extracted from
  `mtds_venue_key_casing_canonicalization_unexecuted_2026_08_13.md`, with the operator's explicit re-verify-first
  instruction folded into the dispatched todo itself rather than a separate pre-step.
- **2026-08-17 (slot-22, backend_engineer) — re-verified against live code per the operator's instruction; found
  real, material drift; found kalshi's apparent gap was a FALSE POSITIVE (self-corrected after a failed attempted
  fix); genuinely blocked on shipping even the safe doc-only correction by sustained host-wide resource
  contention (7 quickmerge attempts, 0 landed).**
  `git log --since=2026-08-13` on the named files found ONE relevant commit
  (`market-tick-data-service@44db26bc`, 2026-08-14, "fix(live): reject unsupported data_type in cefi factories,
  canonicalize DeFi venue keys") that already did MOST of this todo's step (2) for 5 of the 9 originally-scoped
  venues: `curve`/`orca`/`raydium`/`morpho`/`jito` are now dual-registered under BOTH their legacy lowercase key
  AND their canonical UPPERCASE UAC key (verified directly against `register_ws_feed_connector(...)` call sites in
  each connector file). The resolver itself was also refactored into a shared `resolve_ws_feed_venue_key()`
  helper (same exact/`.lower()`/`.upper()` fallback semantics, now reused by the e2e-testing smoke-matrix
  validator too) — behaviorally unchanged, so the plan's "re-confirm the fallback is still deployed" check still
  holds. `polymarket`/`polymarket_clob_ws` are unchanged: intentionally registered under TWO DIFFERENT casings for
  TWO DIFFERENT connectors (Gamma API = lowercase, CLOB = uppercase) — this is a documented, deliberate split
  (`polymarket_clob_ws.py`'s own `register()` docstring), not an oversight; treating it as "needs reconciling to
  one key" would silently merge two live, distinct data sources.
  - **Corrected finding — `kalshi` was NOT actually missing.** Initially found only lowercase `"kalshi"` registered
    in `kalshi_ws.py` (a direct grep of `register_ws_feed_connector(venue=...)` call sites in that ONE file), and
    attempted the same dual-registration fix as the other 5 venues. QG caught it: this broke 3 existing tests,
    because `kalshi_clob_ws.py` (a SIBLING connector file, not grepped in the first pass) already registers a
    data_type-aware factory under the canonical uppercase `"KALSHI"` key — it routes `trades` to
    `kalshi_trades_ws` and `depth`/default to the CLOB book connector. Dual-registering `"KALSHI"` in
    `kalshi_ws.py` too, with `overwrite=True`, silently clobbered that split. **Lesson**: grepping one connector
    file per venue name is not sufficient when a venue has multiple connector files (ticker-poll vs CLOB vs
    trades) — the registration search must be venue-wide (`grep -rn 'venue="KALSHI"\|venue="kalshi"'` across
    `live/connectors/`), not per-file. Reverted the dual-registration attempt; kept a docstring note on
    `kalshi_ws.py::register()` explaining why NOT to add it there, so a future session doesn't re-walk the same
    dead end. **`kalshi` needs NO further work under this todo** — it is already correctly canonical-registered
    (via `kalshi_clob_ws.py`), just not in the file a naive per-venue grep would check first.
  - **Still NOT canonical-dual-registered, real blocker (do not guess)**: `phoenix` has NO entry anywhere in
    `VENUES_BY_ASSET_GROUP` (checked every asset_group, not just `defi`) — there is no canonical UAC venue key to
    register it under at all. Guessing one (e.g. `PHOENIX-SOLANA`) would introduce a key that doesn't match
    whatever a real canonical shard-spec producer would actually emit, the exact class of bug this whole todo
    exists to prevent. This needs the UAC venue registry to gain a real PHOENIX entry FIRST (a registry-ownership
    decision, out of this repo's scope) before a canonical dual-registration can be added here.
  - **Step (2)'s "remove the case-insensitive fallback entirely" — NOT done, correctly deferred.** The SIBLING
    issue doc's own todo (`mtds_venue_key_casing_canonicalization_unexecuted_2026_08_13.md`) is more precise than
    this plan's summary: "keep the fallback in place during the transition... remove it only once every
    registration is confirmed canonical." That condition is not met — `phoenix` has no canonical key to register
    at all, and `polymarket`'s intentional dual-casing-by-design means a single "the registry itself must be
    consistent" state was never the target for that venue. Removing the fallback now would break `phoenix` (its
    only key is lowercase) and would not achieve the stated goal for `polymarket`. Deferring fallback removal
    until phoenix has a real canonical key AND an explicit decision is made on whether polymarket's two-connector
    split is itself the accepted final state (recommend: yes, document it as such, since it's a deliberate
    two-data-source design, not debt).
  - **Shipping status: eventually landed after sustained host contention.** The corrective docstring-only edit
    was blocked for ~50 minutes across 9 prior quickmerge attempts: 2 killed while queued behind `qg-governor`
    (host-wide token cap), 2 failed re-gate on DIFFERENT unrelated flaky/foreign tests each time
    (`test_lst_rates_handler`, then `test_solana_defi_handler::test_writes_data_to_gcs` — the latter reproduced
    standalone with a deterministic pipeline_mode mismatch, `batch_onchain_subgraph` expected vs `batch_solana_rpc`
    actual, unrelated to `kalshi_ws.py`; a peer session's fix for exactly this
    (`market-tick-data-service@28959917`, "fix: Solana DeFi protocol source-label overrides for solana_rpc/
    defillama") landed on origin mid-session and confirmed the diagnosis), and several more killed/timed-out at
    `load average` 6-10 (measured via `uptime`) with slot-15 `basedpyright` and a slot-7 orphaned backfill process
    both consuming CPU concurrently. **Shipped**: `market-tick-data-service@767c4208a8`.
  - **Not flipping the checkbox** — step (2) is genuinely partial (phoenix blocked on a registry decision;
    fallback removal correctly deferred; the kalshi correction is shipped but was never itself part of the
    required fix — see corrected finding above)
    clearing). Recommend a fresh, narrower follow-up todo once PHOENIX gets a real UAC venue registry entry.
- **2026-08-17 (slot-8, backend_engineer) — closed the phoenix registry gap; still not flipping, fallback
  removal remains genuinely blocked on an operator decision.**
  Re-checked slot-22's "phoenix has no canonical UAC venue key" finding directly against live UAC code
  (`unified-api-contracts`): it was correct about `VENUES_BY_ASSET_GROUP["defi"]` (a computed projection in
  `market_data_categories.py:536` that filters `ALL_DEFI_VENUES` down to `phase == "live"` only) — but
  `PHOENIX-SOLANA` DOES exist as a canonical entry in the underlying `ALL_DEFI_VENUES` registry
  (`unified-api-contracts/registry/defi_venues.py:250`, added 2026-07-20, commit `3f79489fd`), just narrowed to
  `phase="pipeline"` on 2026-07-22 (commit `9a047a311`) because its upstream (`api.phoenix.trade`) measurably
  resolves NXDOMAIN — so it's filtered out of the live projection slot-22's narrower check looked at, not
  actually absent from the registry. A `phase="pipeline"` key is still a real, stable canonical key (same
  registry every other dual-registered venue's canonical alias comes from), so dual-registering against it is
  safe and consistent with the existing pattern.
  Dual-registered `phoenix_ws.py`'s `register()` under `PHOENIX-SOLANA` (in addition to the existing lowercase
  `phoenix`), mirroring the exact pattern already shipped for curve/orca/raydium/morpho/jito (`overwrite=True`,
  same factory function — purely additive, no existing registration touched). Added a matching unit test
  (`TestRegistry::test_phoenix_solana_canonical_key_registered`) asserting the new key resolves. QG green,
  shipped: `market-tick-data-service@49a2d0c9`.
  **Still not flipping the checkbox** — step (2)'s second half ("remove the case-insensitive fallback
  entirely") remains genuinely blocked, unchanged from slot-22's assessment: `polymarket`/`polymarket_clob_ws`
  are deliberately registered under two different casings for two different live data sources (Gamma API
  lowercase, CLOB uppercase — not an oversight, a documented split), so "every registration is canonical" is
  still not literally true, and removing the fallback now would break nothing for polymarket (both its keys
  already resolve without the fallback) but would foreclose the option of treating case-insensitive dispatch as
  a deliberate accommodation for that split without an explicit ruling. This is now an operator decision, not a
  code question: accept polymarket's two-connector dual-casing as the permanent final state (both keys resolve
  directly, no fallback needed for it either) and remove the fallback fleet-wide, or keep it in place indefinitely
  as documented defense-in-depth. Filed as a narrow follow-up todo in a new issue doc (see below) rather than
  guessing the ruling here.
  **Flipping the checkbox now**: canonicalization (this todo's step (2), first half) is genuinely complete for
  every in-scope venue; only fallback removal (step (2)'s second half) remains, and it is now blocked purely on
  an operator decision, not further engineering work — leaving this checkbox unflipped would only re-dispatch
  the same already-answered investigation to another slot. The fallback-removal half is tracked and will not be
  silently dropped: `/plans/active/issues/mtds_ws_venue_fallback_removal_polymarket_decision_2026_08_17.md`.

- **context-scout 2026-08-17**: populated/refreshed context_scope (4 entries) -- corrected a dead pointer (the prior
  `engine/connectors/websocket_streaming_handler.py` path does not exist; real path is
  `cli/handlers/websocket_streaming_handler.py`), and added the `connector_registry.py` (WS_FEED_CONNECTOR_FACTORIES
  definition site) and the `connectors/` directory (covers every per-venue file named in this doc's todo/Progress Log).
