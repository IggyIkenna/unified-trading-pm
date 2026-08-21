---
doc_type: plan
title: >-
  Strategy-service centralization fixes — DeFi position-risk reads, venue-literal audit, config-loader unification
summary: >-
  Executes the fix work three issue docs from a same-day audit found: DeFi-leverage archetypes' liquidation
  kill-gate reads an ad-hoc, never-populated generic feature key instead of the correct (but unwired) centralized
  module; venue eligibility is hardcoded per-literal outside one family; two GCS config-loader path conventions
  diverge for the same lookup. Genuine judgment calls stay [OPERATOR]-tagged and non-dispatchable; everything else
  is bounded, symbol-referenced AGENT work. `sequential: true` because several todos have a real chain (route the
  live feed, then switch the archetypes onto it, then extend the data model) — a deliberate choice given the
  correctness stakes (this is live liquidation-risk gating), not a reflexive default.
  EXPANDED 2026-08-16 (operator) to own the GENERAL class this plan's original findings were three instances of:
  reference / registry / config information embedded inside a specific code path, reachable by one archetype, when
  many need the same fact. Adds the four-destination decision rule (service config via the reloader / UAC / UTL /
  a centralized domain module) and the audit that applies it across the 69 measured candidates.
status: active
nature: process
asset_group: [defi, cross-cutting]
stage: [execution]
repos:
  [strategy-service, execution-service, features-service, unified-api-contracts, unified-trading-library]
scope: [engineer]
tags:
  [
    defi,
    risk,
    centralization,
    health-factor,
    venue-eligibility,
    config-loader,
    architecture,
    reference-data-centralization,
  ]
related:
  [
    /plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md,
    /plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md,
    /plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md,
    /codex/04-architecture/position-risk-centralization.md,
    /plans/active/elysium_carveout_stubbed_strategy_service_2026_08_12.md,
  ]
created: 2026-08-16
last_updated: "2026-08-18"
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 10
estimate_calibrated_ai_days: 8
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
depends_on: []
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Interactive session 2026-08-16. Operator direction: audit findings must resolve into tracked plan todos, not sit
  passive in issue docs — per this workspace's own findings-triage rule ("issue resolves to folded-in-plan/AO-scope/
  operator-gated, never passive"). Operator confirmed AO-dispatched, one wrapper plan.
context_scope:
  [
    /codex/04-architecture/position-risk-centralization.md,
    strategy-service/strategy_service/position/core/margin_event_emitter.py,
    /plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md,
    /plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md,
    /plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md,
    strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py,
  ]
---

# Strategy-service centralization fixes

Full findings, root cause, and evidence for every todo below live in the three source issue docs (linked in
`related`) — this plan is the execution surface, not a duplicate of the analysis.

- [x] [OPERATOR] P0. ✅ RULED 2026-08-17 — **Decide the callable-path fix shape**: neither "in-process function
      scoped to one service" nor "build a new shared helper" — an in-process function scoped to strategy-service
      structurally cannot serve execution-service too, and a *new* shared helper risks duplicating what already
      exists. The generic collateral/exposure/health-ratio math must be asset-group-agnostic (DeFi, CeFi, TradFi
      share one core; only the per-venue-type sourcing adapter differs) and live in UTL — which it already does:
      `unified_trading_library.margin_and_liquidation` (`MarginModelProtocol`, `PortfolioInputs`, HF-mode/MMR-mode
      grading) is already this shape. Full design: [position-risk-centralization](/codex/04-architecture/position-risk-centralization.md).
      Details: [defi_leverage_archetypes_health_factor_wrong_source_2026_08_16](/plans/active/issues/defi_leverage_archetypes_health_factor_wrong_source_2026_08_16.md).
- [x] [AGENT] P0. ✅ RECONCILED 2026-08-18 (unified-trading-pm, doc-only decision) — **Reconcile the two parallel
      mechanisms before wiring anything.** Read `defi_health_aggregator.py`, `margin_event_emitter.py`,
      `risk.py` (its caller), `positions_health.py`, and the `MarginHealthSnapshot`/`DeFiAggregatedHealth` schemas
      in UAC directly rather than trusting either module's docstring claim. Findings:
      1. **A and B are not actually independent — B's DeFi path already consumes A's output.**
         `risk.py::update_lending_positions()` calls `_defi_health_aggregator.aggregate(positions)` (mechanism A)
         and immediately feeds that `DeFiAggregatedHealth` into `emit_margin_event_for_health()` (mechanism B) in
         the same call. So "retire A, converge on B" is not a straight either/or for the aggregation engine itself
         — B's DeFi emission depends on A's `aggregate()`. What *is* genuinely redundant is a **third, separate**
         piece: `positions_health.py`'s `derive_snapshot_from_lending()` independently re-derives
         collateral/debt/ltv from raw positions (not reusing `DeFiHealthAggregator`) and hardcodes
         `MarginModel.AAVE_V3` for its liquidation threshold regardless of the position's real protocol — this is
         the actual duplicate-of-A that should be deleted in favour of a route that reads the same
         `DeFiHealthAggregator`/`MarginEvent` state.
      2. **`MarginEvent`'s schema already has every field an archetype gate needs** —
         `MarginHealthSnapshot` (UAC `internal/risk.py:648`) declares `health_factor`, `ltv_ratio`,
         `liquidation_price`, `distance_to_liquidation_pct`. But **`margin_event_emitter.py::_build_event()` never
         populates `liquidation_price`/`distance_to_liquidation_pct` for the DeFi path** — every DeFi `MarginEvent`
         emitted today has both fields `None`. This must be fixed as part of wiring the archetypes on, not
         assumed already-done.
      3. **Granularity gap — MarginEvent's DeFi snapshot is portfolio-combined, not per-position.** It's built
         from `defi_health.combined_health_factor`/`combined_collateral_usd`/`combined_debt_usd` — one blended
         figure across every DeFi lending position the client holds, labelled by `riskiest_protocol`. An
         archetype like `staked_basis.py`'s `LST_AS_MARGIN` structure needs the HF of *its own* posted collateral,
         not a value diluted by unrelated positions on other protocols. `DeFiAggregatedHealth.protocols: list[
         ProtocolHealthBreakdown]` (mechanism A's per-protocol breakdown, already computed inside `aggregate()`)
         is the correct source of per-position granularity — it exists today but isn't surfaced in the published
         `MarginEvent`.
      4. **Push vs. pull — `MarginEvent` alone can't serve a synchronous `on_tick()` gate.** It's a best-effort
         Pub/Sub push, emitted only when severity crosses a non-INFO band (`_classify_hf_severity`) — there is no
         in-process subscriber/cache inside strategy-service today that an archetype could read synchronously for
         "the latest known HF for this position." `positions_health.py`'s `/positions/health` route already
         models the needed shape (pull, 5s-TTL cache) but is HTTP-only and duplicates A's math per finding 1.
      **Decision**: archetypes wire onto mechanism (B) semantically (`MarginEvent`/`MarginHealthSnapshot` stays
      the one published schema; do not build a third parallel event type) — but B is not usable as-is. The next
      three todos must, in order: (a) feed live positions into `risk.py::update_lending_positions()` (which
      already wires A→B together) rather than into `positions_health.py::update_wallet_health_from_lending`
      as originally worded (corrected below — that function feeds the redundant third cache, not
      `DeFiHealthAggregator`); (b) populate `liquidation_price`/`distance_to_liquidation_pct` in
      `_build_event()` and surface per-protocol (not just combined) HF so an archetype can read its own
      position's figures, e.g. via an in-process last-known-`DeFiAggregatedHealth` cache the archetypes call
      directly rather than only reacting to the Pub/Sub stream; (c) once that in-process read path exists,
      delete `positions_health.py`'s independent `derive_snapshot_from_lending()`/AAVE_V3-hardcoded path and
      have `/positions/health` read the same state instead of re-deriving it. Full context:
      [position-risk-centralization § Two parallel mechanisms](/codex/04-architecture/position-risk-centralization.md).
- [x] [BACKEND] P0. ✅ **SPLIT 2026-08-18 — CORRECTED PREMISE — `HealthFactorMonitor` is not "already-working."**
      Shipped the achievable, honestly-scoped piece and split the remaining genuine decision into the new
      `[OPERATOR]` todo directly below — this checkbox tracks THIS todo's investigation + shipped code, not the
      original (false-premised) done-when, which the split todo now owns. Investigated
      before wiring: `HealthFactorMonitor` (execution-service) is constructed nowhere outside its own test file — no
      production entrypoint builds one. Its intended data source, `AAVEConnector.get_user_account_data()`
      (`execution_service/defi_execution/protocols/aave.py`), returns **hardcoded placeholder values**
      (`total_collateral_eth=Decimal("10")`, `total_debt_eth=Decimal("5")`) regardless of `is_live` — already found
      and tracked separately (`recursive_loop_orchestrator.py:730-735`'s own docstring cites this; extracted to
      `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 15, per
      `venue_coverage_position_read_vs_execute_asymmetry_2026_08_14.md`). Routing "HealthFactorMonitor's live data"
      as originally worded would have routed simulation constants into the aggregator while claiming they were real.
      **Also**: `HealthFactorMonitor` runs in execution-service; `update_lending_positions()` is an in-process
      strategy-service function — no event/API bridge between the two exists today, so this path needs one built,
      not just "wired."
      **What shipped instead — `strategy-service@0a209dbba1`** (in-process, no cross-service bridge needed): finished
      `AavePositionAdapter.get_lending_position()` (`position/position_interface/adapters/aave.py`) with a real
      `getUserAccountData()` eth_call — cited pool address (reused from execution-service's own
      `aave.py::POOL_ADDRESS`), cited selector `0xbf92857c` (verified via 4byte.directory), decoding
      collateral_usd/debt_usd/ltv_ratio/health_factor from Aave's documented base-currency/bps/WAD units, with a
      correct zero-debt sentinel (uint256-max HF → `None`, not a fabricated huge number). 2 unit tests
      (`tests/position/position_interface/unit/test_aave_position_adapter.py`), both green. `supplied`/`borrowed`
      left empty (honest-absence) — per-reserve amounts need `getUserReserveData()` per reserve, not built here.
      **Not done — genuinely remains open**: nothing calls `get_lending_position()` yet. Wiring it into
      `risk.py::update_lending_positions()` on a live/paper cadence needs a NEW per-client DeFi-wallet config
      surface (which client owns which wallet address(es), which chain) that doesn't exist anywhere in
      strategy-service's config today — a real design decision, not a one-line call. Split to the new todo below
      rather than inventing that config shape unilaterally. Done-when (unchanged, not yet met): the aggregator's
      state reflects real position data after a live/paper run, verified by reading it back.
- [x] [OPERATOR] P1. ✅ RULED 2026-08-18 — **Per-client DeFi-wallet config shape: many wallets per client, keyed by
      `(client_id, chain)`, via the config reloader.** A client running DeFi archetypes isn't confined to one
      chain — `staked_basis.py`'s own `_STAKING_PROTOCOL_CHAIN` spans 8 staking protocols across multiple chains,
      and a client could run `CARRY_STAKED_BASIS` and `CARRY_RECURSIVE_STAKED` simultaneously on different chains,
      so a single wallet-per-client field can't express it. Not a new pattern — the same four-destination rule
      this plan already established: operator/client-tunable data that changes without a code release is
      **service config, always via the reloader** (never a bare module constant), not UAC (per-client operational
      mapping, not shared reference data) and not a hardcoded table. Concretely: a new config-reloader field,
      `client_id -> {chain: wallet_address}`, per `/codex/06-coding-standards/config-reloader-pattern.md`. Unblocks
      the wiring todo below.
- [x] [BACKEND] P0. ✅ SHIPPED 2026-08-18 — `strategy-service@fc1afc9425`. **CORRECTED 2026-08-18 — wrong function
      names.** Switch `staked_basis.py`'s `_resolve_setup` (line 435, not `_validate_lst_margin_slot` — that method
      doesn't exist) and `recursive_staked.py`'s `_check_safety_gates` (line 115, entry gate) plus
      `_maybe_close_family2_position` (lines 425-456, the actual close/kill gate — not `_check_family2_health_kill`,
      which also doesn't exist) off `features.get("health_factor")` onto the centralized source.
      **Built the missing prerequisite as a NEW generic module**,
      `strategy-service/strategy_service/position/core/margin_health_cache.py`:
      `record_margin_health(subject, scope, reading)` / `get_current_margin_health(subject, scope, now_utc=...)`,
      fail-closed on absent-or-stale (default SLA 900s) — a synchronous in-process read `on_tick()` can call, wired
      from BOTH `margin_event_emitter.py`'s DeFi (`cache_defi_position_health`, per-protocol, addressing
      reconciliation finding #3's per-portfolio-dilution problem) and CeFi (`emit_margin_event_for_cefi`, cached
      even on the INFO/no-publish path) sides — one generic getter, asset-group-agnostic, matching how
      `unified_trading_library.margin_and_liquidation`'s compute core already was.
      **`recursive_staked.py` is fully, correctly wired** — genuine Aave lending loop
      (`lending_protocol` param) — scope=`lending_protocol`. Entry gate moved from `_check_safety_gates` into
      `on_tick()` (needs `self.identity.client_id`, unavailable in that free function); Family-2 exit gate
      (`_maybe_close_family2_position`) inverted to fail-closed-CLOSES (a missing/stale read now closes the
      position, not holds it — the dangerous direction is leaving a leveraged loop open blind).
      **`staked_basis.py` — NEW FINDING, corrected mid-implementation**: its `health_factor` gate is NOT an Aave
      lending health factor at all — `carry-staked-basis.md:275,301,308` confirms "gates the perp short against
      LST-haircut breach" and "no `lending_protocol`/`borrow_asset`" — the LST is posted directly as margin at
      `perp_venue` (Deribit/Bybit), a CeFi/perp-margin concept, not DeFi lending. Wiring it onto the DeFi
      lending-scoped source (as this todo originally implied by bundling both files under "the centralized
      source") would have been WORSE than the original bug — reading a real but semantically-wrong signal.
      Wired onto the correct GENERIC call shape (`get_current_margin_health(client_id, perp_venue, ...)`) but no
      live sourcing adapter feeds that scope yet (no perp-margin position poll exists anywhere in the codebase) —
      correctly fails closed (blocks) until one is built, tracked as a new follow-up below. Operator-confirmed
      2026-08-18 (interactive session) this is the right sequencing: ship the correct call shape now, build the
      real sourcing adapter as separately-scoped work.
      Done-when (met): neither file reads `features.get("health_factor")` anymore; both call the centralized
      source with fail-closed-on-absent-or-stale semantics; existing archetype tests stay green (98+2626 passed
      across the affected suites) plus new tests for the missing/stale-data case
      (`test_recursive_staked_margin_health_gate.py`, `test_margin_health_cache.py`, plus fail-closed cases added
      to `test_staked_basis_validation.py`/`test_carry_basis_perp_inv_family2_on_tick.py`/`test_phase1_batch_e2e.py`).
- [x] [BACKEND] P1. ✅ SHIPPED 2026-08-18 — `strategy-service@2d461285a8`. Switched
      `arbitrage_structural/liquidation_capture.py`'s health-factor gate and `mev/liquidation_bundle.py`'s
      `liq_candidate_health_factor_*` gate onto `get_current_margin_health(subject, scope)` — candidate-wallet-
      parameterized (`subject`=wallet address, not client_id — a different call shape from the prior todo, exactly
      as scoped). Done-when met: neither reads an ad-hoc `features.get` key for this purpose anymore. **Real gap
      surfaced, not fabricated**: no live scanner populates this cache for arbitrary third-party candidate wallets
      today (would need to discover/watch candidate addresses and poll their health — a genuine new infra piece,
      out of scope for this todo), so both archetypes now correctly NEVER fire (fail-closed) rather than trusting
      an ad-hoc features key nothing ever populated either — same honest-absence treatment as before, just moved
      to the right layer. Tracked as a new follow-up below.
- [x] [OPERATOR] P1. ✅ RULED 2026-08-18 — **Wire `liquidation_proximity_circuit.py` in; do not retire it.** Read
      the file in full: it's complete, purpose-built code (Phase 8 of `defi_recursive_borrow_archetypes_2026_05_10.md`)
      that maps 6 specific `AlertCode`s (`DEFI_LIQUIDATION_IMMINENT`, `DEFI_HEALTH_FACTOR_CRITICAL`,
      `DEFI_FUNDING_RATE_FLIP`, `DEFI_PERP_VENUE_OUTAGE`, `DEFI_ORACLE_STALE_PAUSE`,
      `DEFI_RECURSIVE_LOOP_GAS_BUDGET_EXCEEDED`) to graded responses (flash-close, partial-unwind, position-pause,
      hedge-failover, oracle-buffer, mid-loop-recovery) — strictly more sophisticated than a binary kill-gate, and
      it doesn't compete with mechanism A/B: it's a downstream consumer of a `DefiAlert`, not another
      health-factor source. Zero callers because nothing upstream emits a `DefiAlert` with one of these codes
      yet — that's the actual gap, not the circuit itself.
      ✅ SHIPPED 2026-08-18 — `strategy-service@6b8c0c83f7`. Built the bridge:
      `margin_event_emitter.py::defi_alert_for_margin_reading()` classifies a `CachedMarginReading` into
      `AlertCode.DEFI_LIQUIDATION_IMMINENT`/`DEFI_HEALTH_FACTOR_CRITICAL` and constructs the matching `DefiAlert`;
      wired into `recursive_staked.py`'s Family-2 close gate (the archetype this circuit is explicitly named for),
      which already computes the qualifying `margin_reading`. **Scoped honestly**: the circuit now has a real
      caller and its `ProximityDecision` is genuinely computed + logged (audit trail), but every qualifying breach
      still fully closes as before — acting on the FULL graded taxonomy (`PARTIAL_UNWIND`'s one-loop-level
      reduction, `POSITION_PAUSE`, `HEDGE_FAILOVER`, `ORACLE_BUFFER`, `MID_LOOP_RECOVERY`) needs new
      leg-construction logic per action, not built here — that remains open, real follow-up work if the graded
      response is wanted beyond "wired in + observable."
- [x] [BACKEND] P1. ✅ SHIPPED 2026-08-18 — `strategy-service@fc1afc9425` (a), `strategy-service@2d461285a8` (c).
      **CORRECTED 2026-08-18 — split into what's honestly achievable now vs. blocked on missing data.** Three
      sub-pieces, not one:
      (a) ✅ **Build the in-process read path** — built as the GENERIC `margin_health_cache.py` (see the P0 todo
      above), not the DeFi-only `get_current_defi_health(client_id)` shape originally specced here — the shape
      generalized once staked_basis.py's real gate turned out to be CeFi/perp-margin-shaped, not DeFi-lending-
      shaped, so a DeFi-only getter would not have served both archetypes. `risk.py::update_lending_positions()`
      now calls `margin_event_emitter.cache_defi_position_health()` per-protocol on every update.
      (b) ⏸️ **Still genuinely blocked, unchanged** — `liquidation_price`/`distance_to_liquidation_pct` cannot be
      honestly populated today (`AavePositionAdapter.get_lending_position()` deliberately returns
      `supplied=[]`/`borrowed=[]`; needs a `getUserReserveData()`-per-reserve fetch, not yet built and not a
      tracked todo). Left `None`; not guessed.
      (c) ✅ Fixed `positions_health.py`'s `MarginModel.AAVE_V3`-hardcoded liquidation-threshold lookup — now
      resolves per the wallet's RISKIEST position's actual protocol (lowest health factor, mirroring
      `DeFiHealthAggregator._find_riskiest()`'s selection) via the same `margin_model_for_defi_protocol()`
      resolver (a) uses. New tests: `test_derive_snapshot_liquidation_threshold_resolves_non_aave_protocol`,
      `test_derive_snapshot_riskiest_protocol_selects_lowest_hf`.
- [x] [OPERATOR] P2. ✅ RESOLVED BY SHIPMENT 2026-08-18 — `AavePositionAdapter`'s fate: **finished, not deleted**
      (`strategy-service@0a209dbba1`, `get_lending_position()` with a real `getUserAccountData()` eth_call, 2
      green tests — see the corrected-premise Progress Log entry above). **RE-APPLYING 2026-08-18 (second time)**:
      this checkbox reverted to unresolved between my first fix and this edit, most likely lost in a concurrent
      push reconciliation (`git diff origin/<branch> -- <path>` before push would have caught it — noting for next
      time). If this reverts a third time, treat it as a genuine content-collision bug in the push path, not
      operator error, and escalate rather than silently re-fixing again.
- [x] [BACKEND] P2. ✅ SHIPPED 2026-08-18 — `features-service@7ebefe9319`. Fixed `_process_health_factor()`'s
      misleading docstring in `features-service/features_service/onchain/engine/orchestrator.py` — now describes
      the generic protocol-level rate-index data it actually reads and states plainly it is NOT used for
      strategy-service risk gating (per-wallet Aave polling was never real). Landed via quickmerge, verified
      post-push ancestor of `origin/live-defi-rollout`.
- [x] ✅ [BACKEND] P2. **Deletion half DONE 2026-08-21, `strategy-service@bfa778f4ab`; re-pointing is a
      genuinely separate follow-up, correctly split out below.** The "wallet_id → (client_id, protocol)
      mapping" concern this todo was originally gated on turned out to be MOOT, not a design call: a
      full-repo grep found `derive_snapshot_from_lending()`/`update_wallet_health_from_lending()`
      have ZERO real callers anywhere (the "called by DeFi adapters whenever they write fresh
      lending positions" docstring was never true) — nothing populates `/positions/health`'s cache
      via this path in production, so deleting it needs no client_id reconciliation at all. Deeper
      finding while verifying the route's OTHER claimed consumer: `run_wallet_preflight_checks`
      Layer-4's `position_health_fn` callback is real, but grepped execution-service end to end —
      neither of its two call sites (`manual_instruction_submit.py`, `manual_instruction_helpers.py`)
      ever passes it, so Layer 4 is always skipped in production today too. `/positions/health` is
      dead on BOTH ends, not just the writer side this todo originally scoped. Deleted the 3 dead
      functions + their 6 tests (5 real route tests remain, all passing); corrected the module
      docstring's false "consumed by Layer-4" claim. **Re-pointing `/positions/health` onto
      `margin_health_cache` is a real, separate follow-up** (new todo below) — `CachedMarginReading`
      carries a raw HF/margin-usage `value`, not the richer `ltv`/`liquidation_threshold` split this
      response shape wants; that schema mapping is a genuine design call, not invented here.
- [ ] [BACKEND] P3. **NEW 2026-08-21 — Design the schema mapping to re-point `/positions/health` onto
      `margin_health_cache.get_current_margin_health()`** instead of its now-permanently-empty local
      cache. Needs: (a) how a raw HF-mode `value` (health factor, ~1.0-2.0) or MMR-mode `value`
      (margin_usage_pct, 0-100) maps onto `PositionHealthSnapshot`'s `ltv`/`liquidation_threshold`/
      `margin_ratio`/`maintenance_margin` split — they are not the same metric; (b) the route only
      has `wallet_id` today, but `margin_health_cache` is keyed `(subject, scope)` where
      scope=protocol — decide whether to add `protocol` as a required query param (simplest, matches
      the cache's real shape) or attempt multi-protocol aggregation. P3 since nothing consumes this
      route in production today (see the finding above) — low urgency, but worth closing since a
      declared, seemingly-real endpoint that always 404s is a real trap for the next person who
      wires a Layer-4 caller assuming it works.
- [x] [BACKEND] P1. **NEW 2026-08-18 — Build the real live perp-margin sourcing adapter for `staked_basis.py`'s
      LST_AS_MARGIN gate.** ✅ 2026-08-21 — **DERIBIT `MarginModel` registry gap CLOSED** —
      unified-api-contracts@af14eee25f (`MarginModel.DERIBIT` + `LIQUIDATION_PARAMS_REGISTRY[DERIBIT]`,
      mmr_warning/critical=70/85 placeholder — Deribit support docs confirm liquidation triggers at MM-ratio=100%
      but publish no separate early-warning band, so this mirrors the same Bybit/OKX/dYdX/Hyperliquid placeholder
      pending real Deribit-specific banding data), unified-trading-library@6d7f801273 (`DeribitMarginModel` class +
      `_MODEL_REGISTRY` entry, parallel test case in `test_margin_and_liquidation.py`), strategy-service@5d3bd5a3b0
      (`CEFI_PERP_MARGIN_MODELS`/`CEFI_PERP_VENUES` now carry `"deribit"`, parallel test case in
      `test_cefi_margin_traceability.py`). `cefi_margin_tiers.py` already had `("deribit", "BTC"/"ETH")` tier data —
      no change needed there.
      **CORRECTION to this todo's own premise** (found while implementing, not assumed): `staked_basis.py`'s
      consumer-side gate was **already fully wired** before this session — `get_current_margin_health(self.identity.client_id, config.perp_venue, now_utc=now_utc)`
      exists at `staked_basis.py:836` (fail-closed on `None`/stale, matching this file's existing style) — the
      "nothing feeds that scope" framing was accurate for the SCOPE, not for the consumer call site, which was not
      new. The producer side is ALSO already-existing generic infra, not something built from scratch this
      session: `venue_balance_tracker.py::emit_live_cefi_margin_events()` iterates `CEFI_PERP_VENUES` (now
      including deribit) via `CefiVenueBalanceReader`/`AccountQueryClient`, which already routes to a real
      `DeribitPositionAdapter` (`position/position_interface/adapters/deribit.py`, live via
      `routing.py`/`factory.py`/`capabilities.py` — confirmed by grep, not assumed) — the ONLY blocker was the
      missing `MarginModel.DERIBIT`/registry entries, now fixed. `record_margin_health`'s `_key()` lowercases
      `scope`, so the `"DERIBIT"` (uppercase, from `catalog_staked_basis.py`'s `perp_venue` literal) vs `"deribit"`
      (lowercase, from `CEFI_PERP_VENUES`) casing difference collides to the same cache key — no casing bug.
      **Genuinely remaining gap (separate, NOT Deribit-specific, left open)**: `position/cli/handlers/monitor_handler.py`'s
      reconciliation loop defaults `active_venues` to `["binance"]` and calls `emit_live_cefi_margin_events` with no
      explicit `client_id` (defaults to `"default"`) — so in production this generic CeFi margin-emission loop
      still needs per-client config naming the real client_id + venue list (incl. `"deribit"`/`"bybit"`) before the
      cache is actually populated for a specific `LST_AS_MARGIN` archetype instance's own account. This affects
      every CeFi venue equally (not something this todo introduced or was scoped to fix) — tracked as a new
      follow-up below.
      Done-when: `get_current_margin_health(client_id, perp_venue)` returns a real reading for a live
      `LST_AS_MARGIN` slot, and DERIBIT has a registered `MarginModel`. **DERIBIT registration is done; the
      end-to-end live reading still depends on the monitor-loop config gap above.**
- [ ] [BACKEND] P2. **NEW 2026-08-21 — Configure `monitor_handler.py`'s CeFi reconciliation loop with the real
      per-client `client_id` + full `active_venues` list (incl. `deribit`, `bybit`).** Surfaced closing the todo
      above: `_run_reconciliation_cycle` calls `emit_live_cefi_margin_events(account_query_client=account_client,
      venues=venues)` with no `client_id` kwarg (silently defaults to `"default"`) and `venues` defaults to
      `["binance"]` unless `active_venues` is threaded in from service config — so even with DERIBIT now a
      registered `MarginModel`, `record_margin_health(client_id, "deribit", ...)` never actually fires in
      production until this is wired per-client. Not Deribit-specific (Bybit has the same gap today). Done-when:
      the live monitor loop populates `get_current_margin_health(<real client_id>, "deribit")` for at least one
      running `LST_AS_MARGIN` instance.
- [x] [BACKEND] P2. ✅ SHIPPED 2026-08-21 — `strategy-service@f56af3b94e`. **Corrected premise**: no
      `unhealthy_account_` feature key exists anywhere in `features-service` (confirmed by a full-repo grep before
      building — this todo's "likely sourced from features-onchain-service" guess did not pan out), and no
      on-chain event-scanner infra exists to build on cheaply either. Built instead, real not fabricated:
      `strategy_service/position/core/aave_candidate_discovery.py` — a bounded, TTL-cached borrower watch-list
      queried from Aave V3's public subgraph via the already-existing `UnifiedCloudConfig.thegraph_gateway_url`/
      `thegraph_secret_name` Secret-Manager-backed key pool (the same infra `market-tick-data-service`'s
      `TheGraphBaseClient` already draws from) — plus `strategy_service/position/core/
      candidate_wallet_health_poller.py`, which polls each candidate's REAL on-chain health factor via the
      existing `AavePositionAdapter.get_lending_position()` eth_call (same one `defi_health_poller.py` uses for
      own-client wallets) and writes it to `margin_health_cache.record_margin_health(subject=<address>,
      scope="aave_v3", ...)`. Wired into `monitor_handler.py`'s existing reconciliation loop alongside
      `poll_all_defi_wallets`. New tests: `test_aave_candidate_discovery.py`, `test_candidate_wallet_health_poller.py`.
      **Honest scope note — do not overclaim "both archetypes now live-functional"**: this inherits the SAME
      real limitation `defi_health_poller.py`'s own docstring already documents — no caller in strategy-service
      resolves the Alchemy RPC secret in production today, so a live poll attempt raises inside
      `resolve_defi_rpc_url()` (caught per-candidate, logged, never fabricated) until that secret-wiring lands.
      Ethereum/Aave V3-only, matching `defi_health_poller.py`'s own documented scope limit. Done-when met
      mechanically (discovery→poll→cache wiring is real and unit-tested end to end with mocked HTTP/eth_call),
      but the full chain has NOT been verified against a live discovered candidate address with real RPC
      credentials in production — that verification is gated on the pre-existing Alchemy-RPC-secret-wiring gap,
      not new work from this todo.
- [ ] [BACKEND] P2. **Corrected 2026-08-21 — the "delete dead" half of this todo is WRONG, the
      source issue doc's claim needs its own fix.** `strategy_service/config.py::load_config`/
      `load_strategy_config` are NOT dead: grepped `tests/` fresh and found 6 files with real,
      substantial fixture usage (`test_order_batch_storage_expanded.py`,
      `test_risk_monitor_edge_cases.py`, `test_order_batch_storage_load.py`,
      `test_risk_monitor_expanded.py`, `test_utility_manager_expanded.py`,
      `test_order_batch_storage.py` — 25+ call sites total) plus a dedicated
      `test_default_templates_integration.py` that end-to-end validates
      `load_strategy_config()` loading every real default template. Deleting either function
      would break all of it. `per_client_config_surface_keying_and_missing_axes_2026_08_12.md`'s
      own "zero callers found anywhere in the tree" claim (line 368) was wrong — did not grep
      `tests/`, only production code. **Genuinely remaining scope**: unify `ConfigLoader.load_config`'s
      `configs/{strategy_id}.json` vs. `load_strategy_config_gcs`'s
      `configs/strategies/{strategy_id}.json` behind one loader building on
      `get_strategy_params()`'s existing resolution seam — that half is still real and
      unaddressed, `load_config`/`load_strategy_config` just are not part of the deletable set
      alongside it. Details:
      [per_client_config_surface_keying_and_missing_axes_2026_08_12](/plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md)
      (needs its own line-368 correction — not done here, flag for the next pass on that doc).
- [x] [BACKEND] P2. Audit every hardcoded venue literal in `catalog_trading.py`/`catalog_directional.py` against
      each named venue's actual current capabilities — pm@0fa40df01d. Findings recorded in
      [venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16](/plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md):
      2 real drift findings (CME event-contract root symbols `ECES`/`ECBTC` unconfirmed against CME's live symbol
      directory; Phoenix listed as a live spot/CLMM venue is stale — Phoenix Legacy deprecated, Phoenix Perpetuals
      is private-beta only). Everything else checked (Deribit, Hyperliquid, dYdX, CME futures, Camelot,
      Kalshi/Polymarket) confirmed accurate.
- [x] ✅ [BACKEND] P2. **Corrected 2026-08-21 — already ruled, todo was stale.** The source issue doc carries a
      2026-08-21 OPERATOR RULING (citing `/codex/04-architecture/cross-domain-state-fabric.md` §12, R17 — ONE
      declarative capability-gated resolver, generalized to every family,
      fail-closed) that answers this exact question — fixed the issue doc's own stale todo to match. Remaining
      buildable scope (resolver + regression check + the 2 drift fixes) is now `[AGENT]`-tagged there, not
      operator-blocked. Evidence:
      [venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16](/plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md).
- [ ] [OPERATOR] P2. Design the mode-aware dispatch (batch / live / paper-testnet / paper-live) for the
      centralized DeFi position-risk read, once the earlier routing/switch todos land.
- [ ] [BACKEND] P3. Update
      [position-risk-centralization](/codex/04-architecture/position-risk-centralization.md) from
      "not yet complete" to reflect the landed state, once the earlier BACKEND todos land.
- [ ] [AGENT] P2. **Inventory CeFi and TradFi leverage-capable archetypes** against the same test
      `position-risk-centralization.md` already applies to DeFi (posts collateral and/or borrows/trades against it
      → needs the gate; pure supply-side → doesn't). Unclaimed work, not a stated-zero — run before the TradFi
      registry build below, since it determines how urgent that build actually is.
- [ ] [AGENT] P2. **Build the TradFi margin registry + `MarginModelProtocol` implementation.** Mirror
      `unified_api_contracts/registry/cefi_margin_tiers.py`'s shape (per-broker margin/buying-power schedule,
      cited sources) against a broker's actual documented margin API (e.g. IBKR) — the confirmed genuine gap per
      `position-risk-centralization.md` (no `*tradfi*margin*` registry exists anywhere in UAC today, while the
      CeFi equivalent does). Scaffold and draft from public broker documentation; live validation against the real
      API needs operator-provided test credentials per W14 (`/plans/epics/system_readiness_master.md`) — that part
      is `BLOCKED-CREDENTIALS`, not a descope, so build the adapter scaffold regardless.

## THE GENERAL CLASS — reference data living inside a code path (operator ruling 2026-08-16)

The three findings above are instances, not the problem. The problem is **reference / registry / config information
embedded in a specific code path**, so a fact many archetypes need is reachable by one.

**The exemplar.** `_STAKING_PROTOCOL_CHAIN` in
`strategy-service/strategy_service/engine/strategies/v2/carry_and_yield/staked_basis.py:163` maps 8 staking
protocols to their chain. Every archetype touching a staked token needs that fact; only this file has it. Its
neighbour `_ALLOWED_CHAINS` (line 159) is the same smell. **Measured scale**: 69 module-level reference-shaped
constants under `strategy_service/engine/strategies/` — this is a class, not a one-off.

**Partially-existing SSOT, measured 2026-08-16.** UAC already has `VENUE_CHAIN_MAP`
(`unified-api-contracts/unified_api_contracts/registry/venue_constants.py:907`), which by name carries lido, etherfi
and symbiotic — **3 of the 8**. Absent: rocketpool, coinbase_staking, eigenlayer, jito, marinade. So the strategy
file did not duplicate UAC, it **extended** venue→chain knowledge locally instead of upstreaming it. Note the two
are not obviously the same registry: UAC's is commented "DeFi smart order routing: shared wallet" and feeds
`SHARED_WALLET_GROUPS` — same axis, different purpose. Resolving that overlap is tracked in W2
([registry_ssot_hardening_2026_08_16](/plans/archive/2026_08/registry_ssot_hardening_2026_08_16.md)); this plan consumes that
answer rather than pre-empting it.

> **MEASUREMENT TRAP, recorded because it nearly produced a false finding here.** Probing UAC for these 8 with
> lowercase string literals (`"lido"`) returns ABSENT for all 8 — the map is keyed by CONSTANTS (`LIDO`, `ETHERFI`),
> not literals. That false-clean read says "UAC has nothing, keep the local dict." Probe the vocabulary the WRITER
> emits, per `/codex/02-data/four-surface-reconciliation-procedure.md`.

### The four destinations — apply in this order, first match wins

| # | Destination | When | Mechanism |
| - | ----------- | ---- | --------- |
| 1 | **UAC** | Another service needs the same fact, or it is contract/reference data (venues, chains, tokens, instrument types, adapter keys). | A registry module. Venue lists and adapter keys are already UAC data by standing rule. |
| 2 | **Service config** | Operator/client-tunable, or it changes without a code release. | A `config.py`-style module, **always via the config reloader** (never a bare module constant); split across files by domain ONLY where the line cap forces it, per the W3 ruling. |
| 3 | **UTL** | A generic mechanism rather than domain data — the fact is about HOW, not WHICH. | A shared library module. |
| 4 | **Centralized domain module** | Genuinely code-derived / engine-style, but needed by many archetypes in that domain. | One module in that domain every archetype calls — the same shape `liquidation_proximity_circuit.py` was meant to be. |

**Staying in place is a valid outcome** — but only for a constant that is genuinely local to one archetype's own
logic and that no second archetype could ever want. That must be stated, not assumed by inaction.

- [x] ✅ [BACKEND] P1. **Inventory and classify all 69 candidates — DONE 2026-08-21.** Full per-constant table (72
      distinct candidates measured, not 69 — see the sibling doc's "Count discrepancy" section for why: the 69 was
      measured 2026-08-16 against `_STAKING_PROTOCOL_CHAIN`, since deleted, and this plan's own Progress Log shows
      active development adding new archetype-scoped constants in the same window) moved to a sibling doc because
      this plan was already over its 500-line soft cap before the table:
      [strategy_service_reference_constants_inventory_2026_08_21](/plans/active/strategy_service_reference_constants_inventory_2026_08_21.md).
      Every candidate probed for a real SSOT by content/vocabulary, not name similarity, per the `_STAKING_PROTOCOL_CHAIN`
      measurement-trap lesson above.
- [x] ✅ [BACKEND] P1. **Migrate the unambiguous ones — DONE 2026-08-21, revised same day.** Zero candidates had both
      an unambiguous destination AND a confirmed-real, already-existing EXTERNAL SSOT (every venue/LST/chain list
      that looked plausible on name alone was checked by content and confirmed to be archetype-specific *curation*
      layered on top of UAC data, matching the `_ALLOWED_CHAINS` precedent, not a duplicate of it — the one genuine
      external-SSOT duplicate, `_STAKING_PROTOCOL_CHAIN`, was already fixed by the exemplar todo above). **Correction
      to the first pass of this todo**: `_MONTH_ABBREV` (byte-identical across `carry_and_yield/dated_contract_resolver.py`
      and `vol_trading/atm_straddle_resolver.py`) was initially left AMBIGUOUS on the reasoning "no SSOT exists to
      migrate to" — that conflates "no pre-existing external SSOT" with "no valid destination"; the parent plan's
      own destination #4 (centralized domain module) needs only a genuine multi-consumer need within the domain,
      which this had. Migrated to new shared module
      `strategy_service/engine/strategies/v2/dated_symbol_conventions.py::MONTH_ABBREV`; both local dicts deleted
      (no shims), new unit tests added. Evidence: `strategy-service` quickmerge pending as of this write, blocked on
      unrelated dirty deps in `unified-trading-library`/`unified-api-contracts` owned by other concurrent sessions
      (not force-pushed through); will land once those clear. See sibling doc's revised Summary section.
- [ ] [OPERATOR] P1. **Rule on the ambiguous ones** — 4 clusters (8 table rows, revised 2026-08-21 after
      `_MONTH_ABBREV` moved from this list to MIGRATED above) surfaced by the inventory above, full list + one
      recommendation each in
      [strategy_service_reference_constants_inventory_2026_08_21](/plans/active/strategy_service_reference_constants_inventory_2026_08_21.md)'s
      Summary section: (1) `_FAMILY_TO_ASSET_GROUP` — fold into UAC asset_group taxonomy vs. keep as a narrow
      routing-key derivation (recommend: keep local, it's a 3-entry publish-path routing key, not general reference
      data); (2) `_STRIKE_INCREMENT` — plausible instruments-service reference data, no confirmed SSOT (recommend:
      ask instruments-service whether it already owns strike-grid data before building a new registry); (3)
      `_LP_CONCENTRATED_POOLS` — pool contract addresses, no confirmed UAC LP-pool registry (recommend: build one in
      UAC only if a second consumer emerges — currently single-consumer); (4) stablecoin-preference cluster
      (`_STABLE_PREFERENCE` / `_PERP_MARGIN_STABLE_PREFERENCE` ×2 / `_STABLECOINS`, near-identical values across 3
      files) — recommend consolidating to one local shared constant in `carry_and_yield/` regardless of the
      operator's UAC-vs-local ruling, since the duplication is intra-repo either way.
- [x] ✅ [BACKEND] P1. **Fix the exemplar — DONE 2026-08-21, `strategy-service@1ea9d0b170`.**
      `_STAKING_PROTOCOL_CHAIN` was already gone (shipped earlier this session,
      `strategy-service@8a7f80e8`) — replaced with UAC's `get_chain_for_protocol()`. Verified live
      (`python -c` against the real registry, not assumed) that all 5 originally-cited "missing"
      protocols now resolve correctly: `rocketpool`→ethereum, `coinbase_staking`→ethereum,
      `eigenlayer`→ethereum, `jito`→solana, `marinade`→solana — the gap this todo was filed against
      is fully closed. `_ALLOWED_CHAINS` (a 3-chain trading-scope allow-list, not a protocol→chain
      map) verdicted STAYS LOCAL: grepped every archetype under `engine/strategies/v2/`, it's the
      only file with anything shaped like this — no second archetype wants it — and it already cites
      its own codex spec (`carry-staked-basis.md § allowed_chains`). Added an explicit
      "stays local, here's why" comment to the constant itself rather than leaving the verdict
      implicit, per this todo's own done-when bar.
- [ ] [BACKEND] P2. **Gate the regression.** A check that fails when a new module-level reference-shaped constant
      naming venues/chains/tokens/protocols appears under `engine/strategies/`. Baseline it at the post-migration
      count and ratchet DOWN only, per the workspace's shrinking-baseline convention — a hard zero would block
      legitimately-local constants.

- [ ] [BACKEND] P2. **Collapse the per-domain config-reloader and S2S-auth boilerplate** (added 2026-08-21, provenance
      `/plans/active/cross_repo_duplication_cleanup_2026_08_21.md`). `strategy_service/{pnl,position,risk}/auth_s2s.py`
      are byte-identical (shasum-verified) — collapse to one shared module. Separately, adopt UTL
      `ConfigReloaderBase` for the per-domain `config_reloaders.py` copies; UTL's own docstring states the base class
      exists to replace this boilerplate, and the equivalent files in features-service measure 3 differing lines out of
      147 between domains. Preserve every genuine per-domain difference — the goal is deleting the identical part, not
      flattening real variation. SSOT: `/codex/06-coding-standards/config-reloader-pattern.md`.

## Progress Log

- **2026-08-21 (interactive session)** — Completed the W7 inventory + migration todos. Grepped all module-level
  reference-shaped constants under `strategy_service/engine/strategies/`: 72 distinct candidates (76 raw grep
  matches, 3 index duplicates, minus `_ALLOWED_CHAINS` already covered by the exemplar todo above), not the
  claimed 69 — explained as net drift from active development in the 5 days since the 69 was measured, not a
  wrong original count. Full table in sibling doc
  [strategy_service_reference_constants_inventory_2026_08_21](/plans/active/strategy_service_reference_constants_inventory_2026_08_21.md)
  (split out because this plan was already over its 500-line soft cap). Result: 62 STAYS LOCAL (archetype-specific
  trading policy, matching the `_ALLOWED_CHAINS` precedent — every venue/LST/chain list that looked plausibly
  UAC-duplicative on name alone was checked by content and confirmed to be curation layered on real UAC data, not
  a duplicate of it), 10 rows across 5 AMBIGUOUS clusters escalated to the `[OPERATOR]` todo below with a
  recommendation each, **0 confirmed-real MIGRATE targets** — the one genuine literal duplicate this class of bug
  produced (`_STAKING_PROTOCOL_CHAIN`) was already fixed by the exemplar todo before this audit ran, so Task 2 (the
  "migrate the unambiguous ones" todo) had no rows to act on. No strategy-service code changed this session — this
  was inventory + classification only, per both todos' own done-when bars.
- **2026-08-21 (interactive session, continued — correction)** — Re-read the inventory above's `_MONTH_ABBREV` row
  (#29/#67) and found the "0 MIGRATE targets" conclusion conflated "no pre-existing external SSOT" with "no valid
  destination": `_MONTH_ABBREV` is a confirmed byte-identical dict duplicated verbatim across
  `carry_and_yield/dated_contract_resolver.py:75` and `vol_trading/atm_straddle_resolver.py:37`, and the parent
  plan's own destination #4 ("centralized domain module — genuinely code-derived, but needed by many archetypes in
  that domain") applies without requiring a pre-existing module to migrate into. Executed the migration: new module
  `strategy_service/engine/strategies/v2/dated_symbol_conventions.py::MONTH_ABBREV`, both local dicts deleted (no
  shims), both resolvers re-import under the original private name so existing call sites/tests are unchanged, new
  unit tests added (`tests/unit/engine/strategies/v2/test_dated_symbol_conventions.py`). `quality-gates.sh` green
  (6470 passed, 0 failed; first run hit a transient >300s wall-clock resource-drift gate from host contention,
  clean retry passed). Quickmerge attempted twice, both blocked by pre-flight on unrelated dirty deps in
  `unified-trading-library`/`unified-api-contracts` (another concurrent session's in-progress WS-session-manager /
  error-code work) — not force-pushed through per the multi-agent-safety rule against touching foreign uncommitted
  work; will retry quickmerge once those clear. Updated the sibling inventory doc's #29/#67 rows and Summary, and
  this plan's Task 2 checkbox + `[OPERATOR]` cluster list, to match (5→4 clusters, 10→8 ambiguous rows).
- **2026-08-18 (slot 5, backend_engineer)** — Resolved the P0 reconciliation todo. Read the actual call graph
  (`risk.py::update_lending_positions()` already chains `DeFiHealthAggregator.aggregate()` into
  `emit_margin_event_for_health()`) rather than trusting either module's docstring. A and B are not independent
  parallel paths as originally framed — B's DeFi emission depends on A's `aggregate()`; the genuinely redundant
  piece is `positions_health.py`'s separate `derive_snapshot_from_lending()` re-derivation. Also found the P0
  todo immediately below named the wrong function (`update_wallet_health_from_lending` feeds the redundant third
  cache, not `DeFiHealthAggregator`) and corrected it in place per the workspace's stale-pointer rule. Full
  decision + evidence inline on the checkbox above. No code changed this session — evidence-gathering + decision
  only, per the todo's own done-when.
- **2026-08-18 (slot 5, backend_engineer, continued)** — Investigated the live-feed todo before wiring and found
  its premise false: `HealthFactorMonitor` is never constructed in production, and its data source
  (`AAVEConnector.get_user_account_data()`) returns hardcoded placeholders (already a separately-tracked gap,
  `cross_cutting_satellite_ao_dispatch_batch15_2026_08_17.md` item 15). Shipped the achievable, honest piece
  instead: `AavePositionAdapter.get_lending_position()` (strategy-service, in-process, no cross-service bridge) —
  a real, cited `getUserAccountData()` eth_call (pool address + selector both cited), 2 green unit tests. Left the
  todo unchecked (its done-when — aggregator state reflects real data after a live/paper run — is not yet met,
  since nothing calls the new method yet) and split the remaining per-client wallet-config decision into a new
  `[OPERATOR]` todo rather than invent that config shape unilaterally.
- **2026-08-18 (interactive session, operator rulings)** — Ruled on all three `[OPERATOR]` todos this AO pass left
  open. Wallet-config shape: many wallets per client keyed by `(client_id, chain)`, via the config reloader.
  `liquidation_proximity_circuit.py`: wire it in (read the file in full first — it's complete, purpose-built
  6-code alert dispatcher, not a competing health-factor source; its only real gap is that nothing emits a
  `DefiAlert` for it to consume yet). `AavePositionAdapter`'s fate todo was stale — already resolved by the prior
  entry's shipment, retagged done. Added two new `[AGENT]` P2 todos this session surfaced: inventory CeFi/TradFi
  leverage-capable archetypes, and build the TradFi margin registry (confirmed the genuine gap, not CeFi) — both
  previously only prose in `position-risk-centralization.md`, never tracked, a real process gap now fixed.
  `runtime-deployment-topology.md`'s PBM gap note corrected in the same session: current in-process implementation
  is deliberate, not an oversight — operator confirmed a possible standalone-service decision is weeks out, ahead
  of the already-filed November 2026 target in `system_readiness_master.md` W7. No application code touched —
  this plan is actively AO-dispatched and being executed live (see the two entries above); resolving the
  OPERATOR-gated decisions is what unblocks that dispatch, not parallel hand-implementation in this session.
- **2026-08-16** — Authored from three same-day issue docs per operator direction (AO-dispatched, one wrapper
  plan). `sequential: true` set deliberately given the real chain among the first several todos — not a reflexive
  default. Companion finalize plan:
  [strategy_service_centralization_fixes_finalize_2026_08_16](/plans/active/strategy_service_centralization_fixes_finalize_2026_08_16.md).
- **context-scout 2026-08-17**: refreshed context_scope (6 entries) -- added
  `per_client_config_surface_keying_and_missing_axes_2026_08_12.md` (the config-loader todo's own cited source doc),
  `registry_ssot_hardening_2026_08_16.md` (the W2 plan the GENERAL CLASS section says this plan consumes rather than
  pre-empts), and `staked_basis.py` (the doc's own named exemplar file for the 69-candidate audit).
- **2026-08-17 (operator ruling + rescope)** — Interactive session: the operator asked how DeFi position-risk
  centralization stays asset-group-agnostic given CeFi and TradFi also carry leverage. Ruled: the generic
  collateral/exposure/health-ratio math lives in UTL, asset-group-agnostic, with per-venue-type sourcing adapters
  — and it turns out `unified_trading_library.margin_and_liquidation` already IS this shape (CeFi-aware
  `MarginModelProtocol` grading, UAC `cefi_margin_tiers.py` registry). That search also surfaced a second,
  already-live aggregation mechanism (`margin_event_emitter.py` / `MarginEvent`, already consumed by
  execution-service) that the original 2026-08-16 investigation missed entirely — added as a new P0 reconciliation
  todo above, gating the two existing live-feed-wiring todos. Codex doc renamed
  `defi-position-risk-centralization.md` → `position-risk-centralization.md` and rewritten to match; every
  referrer in this corpus updated in the same change. TradFi confirmed as the genuine gap (no margin registry
  exists yet) — CeFi is not.
- **2026-08-18 (interactive session, backend_engineer, slot 6)** — Shipped the P0 archetype switch-over + its true
  prerequisite, and the P1 liquidation-gate switch-over + `positions_health.py` fix, two quickmerges:
  `strategy-service@fc1afc9425`, `strategy-service@2d461285a8`. Operator, mid-session, asked for the ARCHITECTURE
  to be right given the whole point of this system is unifying "only so many ways" to view risk/collateral/LTV
  across asset groups — this reframed the implementation from "wire two archetypes onto a DeFi getter" into
  building the actually-missing generic piece:
  - **New module**: `strategy_service/position/core/margin_health_cache.py` — one
    `record_margin_health(subject, scope, reading)` / `get_current_margin_health(subject, scope, now_utc=...)`
    pair, fail-closed on absent-or-stale (default SLA 900s), asset-group-agnostic by construction (`subject` is a
    `client_id` for an archetype's own position OR a bare wallet address for third-party candidate monitoring;
    `scope` is a DeFi protocol or a CeFi/perp venue). This is the missing READ-BACK half of
    `unified_trading_library.margin_and_liquidation`'s already-asset-group-agnostic COMPUTE core — the compute
    core and the publish schema (`MarginEvent`/`MarginHealthSnapshot`) were already unified; only a synchronous
    in-process read for `on_tick()` gates was missing.
  - Wired from BOTH sides of `margin_event_emitter.py`: `cache_defi_position_health()` (new, per-protocol, DeFi)
    and `emit_margin_event_for_cefi()` (existing, now also caches on the INFO/no-publish path).
  - **`recursive_staked.py`**: fully correct — genuine Aave lending loop, scope=`lending_protocol`. Family-2 exit
    gate inverted to fail-closed-CLOSES (a missing/stale read now closes, not holds — the ruled default per
    `system_readiness_master.md` W16 applied to an EXIT gate is "close," not "block," since holding a leveraged
    position blind is the dangerous direction).
  - **`staked_basis.py` — the reframing's real finding**: its health gate is a perp-venue margin-haircut concept
    (`carry-staked-basis.md` confirms no lending leg exists), not an Aave lending health factor — wiring it onto
    the DeFi-scoped source (as originally worded) would have been a confidently-wrong read, worse than the
    original bug. Wired onto the correct generic call shape instead, honestly fails closed pending a real
    perp-margin sourcing adapter (new followup todo, includes the DERIBIT `MarginModel` registry gap this also
    surfaced).
  - **`liquidation_capture.py`/`liquidation_bundle.py`**: switched onto the same generic cache, candidate-wallet-
    parameterized (`subject`=wallet address). No scanner exists to populate it for arbitrary third-party wallets
    (new followup todo) — both archetypes correctly never fire until one does, same honest-absence treatment
    moved to the right layer.
  - **`positions_health.py`**: `MarginModel.AAVE_V3` hardcode fixed to resolve per the wallet's riskiest actual
    protocol, reusing the same `margin_model_for_defi_protocol()` resolver.
  - Full test suite green both times (`bash scripts/quality-gates.sh --no-fix`, exit 0) — 6146 then 6148 passed;
    the only warning both runs was a pre-existing, unrelated `e2e-testing/scripts/defi` line-length lint, never
    touched by this session. Also fixed a genuinely dead pre-existing gap found along the way: `position/
    config_reloaders.py`'s `start_domain_config_reloaders`/`stop_domain_config_reloaders` were never called from
    any production code path (only their own tests) — now wired into `monitor_handler.py`'s live startup/shutdown,
    alongside the new `defi_wallets` domain reloader this session added.
  - **Not done this session**: the DefiAlert-construction bridge (todo above, OPERATOR-ruled 2026-08-18 to wire
    `liquidation_proximity_circuit.py` in) — still open, genuinely deferred for time, not silently dropped.
- **context-scout 2026-08-20**: populated/refreshed context_scope (7 entries)
