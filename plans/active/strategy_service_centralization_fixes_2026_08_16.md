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
    /plans/archive/2026_08/registry_ssot_hardening_2026_08_16.md,
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
- [ ] [BACKEND] P2. **NEW 2026-08-18 — Delete `positions_health.py`'s redundant `derive_snapshot_from_lending()` re-derivation once its wallet-keyed HTTP contract is reconciled with the client_id-scoped cache.** The
      reconciliation todo's decision (above) and this doc's P0 done-note both said this deletion should follow
      once the in-process read path exists — it now does (`margin_health_cache.py`), but `/positions/health`'s
      route is keyed by `wallet_id` (consumed cross-service by execution-service's `run_wallet_preflight_checks`),
      while the new cache is keyed by `client_id`+scope — deleting the redundant path requires resolving a
      `wallet_id -> (client_id, protocol)` mapping first, a genuine small design decision (not build-and-ship),
      to avoid silently breaking that cross-service HTTP contract. Only the hardcoded-threshold half of this todo
      was fixed this session (see above) — the deletion half is this new todo. Done-when: `derive_snapshot_from_
      lending()`/`update_wallet_health_from_lending()` are deleted and `/positions/health` reads the same generic
      cache instead of re-deriving.
- [ ] [BACKEND] P1. **NEW 2026-08-18 — Build the real live perp-margin sourcing adapter for `staked_basis.py`'s LST_AS_MARGIN gate.** Surfaced while shipping the P0 switch-over above: `staked_basis.py`'s health gate is
      correctly wired to `get_current_margin_health(client_id, perp_venue, ...)` but nothing feeds that scope —
      `perp_venue` (Deribit/Bybit) is a CeFi/perp-margin position, not a DeFi lending position, so
      `AavePositionAdapter`/the DeFi wallet poller don't apply. Build a per-instance perp-margin read (posted LST
      value + used margin at `perp_venue` for THIS archetype's own wallet/account — `CefiVenueBalanceReader`
      (`venue_balance_tracker.py`) is the closest existing shape but is scoped to PBM's shared reconciliation-loop
      account, not a specific archetype instance's wallet) that calls
      `record_margin_health(client_id, perp_venue, ...)` via `unified_trading_library.margin_and_liquidation`'s
      generic `MarginModelProtocol.compute()` (MMR-mode), analogous to `emit_margin_event_for_cefi()`. Real
      prerequisite this surfaces: `MarginModel`/`LIQUIDATION_PARAMS_REGISTRY`/`CEFI_PERP_MARGIN_MODELS` (UAC +
      `venue_balance_tracker.py`) has no `DERIBIT` entry today, even though it's one of `staked_basis.py`'s two
      live perp venues (Deribit, Bybit) — add it (a UAC registry change + a strategy-service consumer bump).
      Done-when: `get_current_margin_health(client_id, perp_venue)` returns a real reading for a live
      `LST_AS_MARGIN` slot, and DERIBIT has a registered `MarginModel`.
- [ ] [BACKEND] P2. **NEW 2026-08-18 — Build a candidate-wallet liquidation-health scanner.** Surfaced while
      shipping `liquidation_capture.py`/`liquidation_bundle.py`'s switch-over above: both archetypes now correctly
      read `get_current_margin_health(subject=<candidate wallet>, scope=<protocol>)`, but nothing populates that
      cache for third-party wallets — this needs a discovery/watch-list mechanism (which candidate addresses to
      poll, likely sourced from features-onchain-service's `unhealthy_account_` feature keys or an on-chain event
      scanner) plus a periodic poll per watched wallet calling `record_margin_health()`, analogous in shape to the
      DeFi wallet poller (`defi_health_poller.py`) but keyed by discovered candidate address instead of a static
      per-client config. Until this lands both archetypes correctly never fire (fail-closed), which is honest but
      means neither is live-functional yet. Done-when: a live scanner populates
      `get_current_margin_health(subject=<address>, scope=<protocol>)` for at least one discovered candidate.
- [ ] [BACKEND] P2. Unify the two divergent GCS config-loader path conventions —
      `ConfigLoader.load_config`'s `configs/{strategy_id}.json` vs. `load_strategy_config_gcs`'s
      `configs/strategies/{strategy_id}.json` — behind one loader, building on `get_strategy_params()`'s existing
      resolution seam. Delete the dead local-YAML `config.py::load_strategy_config` path and its unused
      `load_config` alias. Details:
      [per_client_config_surface_keying_and_missing_axes_2026_08_12](/plans/active/issues/per_client_config_surface_keying_and_missing_axes_2026_08_12.md).
- [ ] [BACKEND] P2. Audit every hardcoded venue literal in `catalog_trading.py`/`catalog_directional.py` against
      each named venue's actual current capabilities (does OKX/Bybit/Hyperliquid/CME/IBKR/etc. genuinely support
      what each row assumes, today) — record findings as a new dated section in
      [venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16](/plans/active/issues/venue_eligibility_hardcoded_outside_carry_and_yield_2026_08_16.md),
      correcting any drift found. Useful regardless of the next todo's outcome.
- [ ] [OPERATOR] P2. Decide the venue-eligibility generalization shape — extend `venue_capabilities.py` to every
      strategy family, or accept the hardcoded catalog literals (now verified accurate by the prior todo) as
      deliberate. If generalizing, add a regression check so a catalog row whose venue lacks the assumed capability
      fails loudly at build/test time rather than shipping a slot that can't actually trade.
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

- [ ] [BACKEND] P1. **Inventory and classify all 69 candidates.** For each module-level reference-shaped constant
      under `strategy_service/engine/strategies/`, record: symbol, file:line, what fact it encodes, how many
      archetypes need that fact, whether an SSOT already exists (probing the WRITER's vocabulary, not literals), and
      the destination the table above selects. Output a table in this plan, one row per constant. Done-when: every
      one of the 69 has a row and a named destination, including "stays local" with its justification.
- [ ] [BACKEND] P1. **Migrate the unambiguous ones** — every candidate where the table selects exactly one
      destination and an SSOT already exists to receive it. Delete the local constant in the same change (no shims,
      per the workspace rule). Done-when: the local definition is gone and its consumers resolve through the SSOT.
- [ ] [OPERATOR] P1. **Rule on the ambiguous ones** — any candidate where two destinations are defensible, or where
      migrating means merging two registries that may be legitimately orthogonal (the `VENUE_CHAIN_MAP` case above is
      the type specimen). Escalate as a list with a recommendation each, not one at a time.
- [ ] [BACKEND] P1. **Fix the exemplar.** Resolve `_STAKING_PROTOCOL_CHAIN` and `_ALLOWED_CHAINS` in
      `staked_basis.py` onto whatever W2 rules for venue→chain, adding the 5 protocols UAC currently lacks
      (rocketpool, coinbase_staking, eigenlayer, jito, marinade) to the SSOT rather than to a strategy file.
      Done-when: `staked_basis.py` declares neither constant and every staking archetype reads the same source.
- [ ] [BACKEND] P2. **Gate the regression.** A check that fails when a new module-level reference-shaped constant
      naming venues/chains/tokens/protocols appears under `engine/strategies/`. Baseline it at the post-migration
      count and ratchet DOWN only, per the workspace's shrinking-baseline convention — a hard zero would block
      legitimately-local constants.

## Progress Log

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
