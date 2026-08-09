---
doc_type: issue
title: Capability wizard — gap discovery tracker
summary:
  "**Purpose**: running pool of gaps surfaced by the capability wizard/manifest work (operator rule 2026-06-11: as much
  as possible scripted; issues found get tests built around them; agents only when..."
status: open
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [agent-orchestrator, e2e-testing, execution-service, features-service, fund-administration-service, greeks-service]
scope: [engineer, admin]
tags: [strategy, registry, ssot-audit, execution, ml, ui, uac]
related:
  [
    /plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md,
    ../../archive/2026_07/capability_wizard_and_manifest_2026_06_11.md,
  ]
created: 2026-06-11
author: unknown
parent_epic: strategy_master
priority: P2
source: [gaps surfaced by capability wizard/manifest work 2026-06-11]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-30
context_scope:
  [
    /plans/active/issues/capability_wizard_analysis_findings_2026_06_11.md,
    /plans/archive/2026_07/capability_wizard_and_manifest_2026_06_11.md,
    /plans/archive/issues/cefi_margin_model_hyphenated_instrument_id_misclassification_2026_07_27.md,
    unified-api-contracts/unified_api_contracts/internal/architecture_v2,
    scripts/openapi,
  ]
---

# Capability wizard — gap discovery tracker

**Purpose**: running pool of gaps surfaced by the capability wizard/manifest work (operator rule 2026-06-11: as much as
possible scripted; issues found get tests built around them; agents only when scripts cannot answer). Items here are
UNACKED scope — they graduate into todos on
[`capability_wizard_and_manifest_2026_06_11.md`](../../archive/2026_07/capability_wizard_and_manifest_2026_06_11.md) or
successor plans.

**Gap taxonomy**: `missing_registry` (no declarative source of truth) · `missing_extraction` (registry exists,
generators don't walk it) · `needs_code_scan` (answer only derivable by reading code → agent-orchestrator candidate) ·
`logical_dead_end` (correctly impossible — record so the wizard explains it, not a defect).

## Seeded 2026-06-11 (session audit)

### Generator-suite drift — `missing_extraction` (Phase 0 of the plan)

- [x] ✅ [SCRIPT] P0. SERVICE_REGISTRY in `scripts/openapi/generate_unified_spec.py` lists 10+ phantom pre-consolidation
      services (8× `features-*-service`, `ml-inference/-training-service`, `pnl-attribution-service`,
      `position-balance-monitor-service`, `risk-and-exposure-service`) and misses `features-service`, `ml-service`,
      `fund-administration-service`, `greeks-service`. — ALREADY FIXED (checkbox was stale) unified-trading-pm@50bdbcd36
      (2026-06-11, same day as this issue doc): `SERVICE_REGISTRY` is now built by `_load_service_registry()` from
      `workspace-manifest.json` + disk presence (auto-discovery), no hardcoded phantom list remains. Verified
      2026-07-27: `grep SERVICE_REGISTRY generate_unified_spec.py` shows
      `SERVICE_REGISTRY = _load_service_registry(workspace_root)` at line 583.
- [x] ✅ [SCRIPT] P0. `generate_ui_reference_data.py` never extracts `architecture_v2` (StrategyArchetype ×53,
      StrategyFamily ×9, ARCHETYPE_CAPABILITY_REGISTRY, AtomicExecutionMode, VenueCategoryV2, MarginMode,
      KillSwitchReason, VenueFeature, RiskGateLayer/Decision, CompensationPolicy, MevSubmissionMode, HoldPolicy,
      StakingMethod) — extraction walks package-root exports only. — ALREADY FIXED (checkbox was stale)
      unified-trading-pm@50bdbcd36 (2026-06-11, same day as this issue doc): `extract_uic_enums()` now explicitly walks
      `unified_api_contracts.internal.architecture_v2.enums` + `.archetype_capability` submodules (not just root
      exports), and `extract_architecture_v2_capability_registry()` serialises `ARCHETYPE_CAPABILITY_REGISTRY`
      separately. Verified 2026-07-27 by running the generator live (UAC venv + workspace-sibling `PYTHONPATH`, output
      `ui-reference-data.json`): every named enum present with real counts — StrategyArchetype=60, StrategyFamily=9,
      AtomicExecutionMode=4, VenueCategoryV2=6, MarginMode=5, KillSwitchReason=8, VenueFeature=12, RiskGateLayer=4,
      RiskGateDecision=4, CompensationPolicy=3, MevSubmissionMode=6, HoldPolicy=7, StakingMethod=13;
      `archetype_capability_registry.archetype_count`=53.
- [x] ✅ [SCRIPT] P0. `generate_config_registry.py` mirrors the phantom/missing service list. — ALREADY FIXED (checkbox
      was stale) unified-trading-pm@50bdbcd36 (2026-06-11, same day as this issue doc): the phantom services
      (features-\*-service split / ml-inference / ml-training / pnl-attribution-service /
      position-balance-monitor-service / risk-and-exposure-service) are removed, per the file's own comment "Phantom
      services removed 2026-06-11"; features-service/ml-service/fund-administration-service/greeks-service are present.
      Verified 2026-07-27.
- [x] ✅ [SCRIPT] P1. `_validate_service_coverage()` warns instead of failing → suite rotted silently; committed outputs
      stale (May 22 – Jun 1 vs Jun 11). — ALREADY FIXED (checkbox was stale) unified-trading-pm@50bdbcd36 (2026-06-11,
      same day as this issue doc): `_validate_service_coverage()` now calls `sys.exit(1)` on missing coverage (line 550)
      instead of only warning. Verified 2026-07-27.
- [x] ✅ [SCRIPT] P1. Source-mode capability matrix (batch/live/replay × source × WS/REST) exists only as a manual audit
      doc (`source-mode-capability-matrix_2026-06-07.md`), not as registry + extraction. — **FIXED 2026-07-27
      (slot-6)**: the registry side was ALREADY DONE (checkbox was stale) — UAC's `SOURCE_MODE_CAPABILITY`
      (`unified_api_contracts/canonical/crosscutting/_source_priority_data.py`) encodes
      `plans/audit/results/source_mode_capability_matrix_2026_06_07.md` row-for-row, including its "CORRECTED MODEL"
      section, and is exposed via `modes_for_source()`/`modes_for()`. **The real gap was extraction**: the manifest
      exporter's `extract_data_sources()` (`scripts/openapi/_capability_extract.py`) never read that registry — it
      unconditionally emitted a `not_registered`/`missing_registry` gap edge for every non-batch (source, mode) pair.
      Fixed: `extract_data_sources()` now calls `modes_for_source(src)` and emits a real `available`/`not_available`
      verdict per (source, mode) — unified-trading-pm@ce6eb1775. Verified live: all 99 `supports_mode` edges (33
      external data sources × {batch, live, replay}) now resolve (79 available / 20 not_available), **0 remaining
      `missing_registry` gaps on this dimension** (was ~56-66 of the manifest's `missing_registry` total per the
      2026-06-11 v1 snapshot below). Spot-checked against the ratified matrix (tardis={batch}; databento={batch,live,
      replay}; yahoo/api_football={batch,(replay)} with no live; odds_api={batch,live,replay}) — all match. Manifest
      regenerated + committed: unified-api-contracts@ac4fd8572 (deterministic — byte-identical across two runs at a
      fixed UAC HEAD; `check_capability_regression.py` PASSES with 0 regressions vs the committed baseline, no
      `--update-baseline` needed — every change is either `newly_available` or an honest `not_available`, never a lost
      `available` edge). The per-source non-default-transport dimension (the WS/REST half not covered by
      `default_transport_for_source`) stays a real, smaller residual gap — out of scope for this todo, not hidden.

### Missing registries — `missing_registry` (Phase 2 of the plan)

- [x] ✅ [SPEC] P0. **Collateral**: accepted collateral per venue, haircut per collateral, max/liquidation LTV,
      maintenance vs liquidation margin, per-platform liquidation protocol, broker list. Currently derived from wallet
      structure (DeFi 20/80 treasury/hot, CeFi 0/100) — not declarative, not queryable. — ALREADY FIXED (checkbox was
      stale) `unified_api_contracts/internal/architecture_v2/collateral_registry.py` was backfilled 2026-06-12 (7 perp +
      2 lending MVP venues, every numeric cited to a `source_of_truth`) and has been actively maintained since (GMX
      removal 2026-07-25, Drift/Solana-perp-DEX removal 2026-07-16). Fully declarative + queryable:
      `COLLATERAL_REGISTRY` (`CollateralPolicy` per venue: `accepted_collateral` list of `AssetHaircut` with
      `haircut_pct`/per-asset `max_ltv`/`liquidation_threshold`/`liquidation_bonus`, policy-level
      `max_ltv`/`liquidation_ltv`/
      `maintenance_margin`/`margin_modes`/`liquidation_protocol`/`liquidation_description`), `TREASURY_SPLIT_POLICIES`
      (the DeFi 20/80 / CeFi 0/100 split, now typed not hardcoded), `STAKING_VENUES_NO_COLLATERAL_POLICY` (documented
      logical_dead_end for staking venues), and `BROKER_REGISTRY` (honest-empty — no TradFi broker in the DeFi/CeFi MVP
      set, a typed gap not a silent omission). Verified 2026-07-27 via live import: 7 registry venues, all fields
      populated or explicitly `None` with a cited reason.
- [x] ✅ [SPEC] P1. **Fees**: exchange/gas/broker/clearing fees at venue/instrument-type/tier granularity. — ALREADY
      FIXED (checkbox was stale) `unified_api_contracts/internal/architecture_v2/fees_registry.py` was backfilled
      2026-06-13 (commit `5e7d0685`): `FEES_REGISTRY` carries 21 cited entries — CeFi perp+spot maker/taker (official
      base/VIP0 tier per venue: hyperliquid/binance/bybit/okx/deribit) + DeFi swap fee + gas estimate + Aave flash-loan
      fee (transcribed from execution-service `algorithms/sor.py` / `venues/aave.py`, file:line cited). Verified
      2026-07-27: the module's own docstring falsely claimed the registry was "intentionally empty" — fixed in
      unified-api-contracts@13a01913 (this task) to accurately state the backfilled status. **RESIDUAL** (honest gap,
      same class as `collateral_registry.py`'s empty `BROKER_REGISTRY`): `FeeComponent.BROKER` (0 entries — no TradFi
      commission rate table in-repo, only IBKR's live `commissionReport` callback field) and `FeeComponent.CLEARING` (0
      entries — no CME/ICE/Deribit/CBOE clearing-fee constant in-repo) stay honest-empty; every entry carries
      `tier="base"` only (no volume/VIP fee-tier schedule exists in-repo, unlike margin's sibling
      `cefi_margin_tiers.py`). Also fixed stale doc-drift in `/codex/09-strategy/architecture-v2/capability-wizard.md`
      (line 115 said fees was still "honest-empty") and `capability-wizard-question-bank.md` (fee-stack question status
      `gap`→`partial`; the three sibling collateral-registry questions were ALSO stale `gap` despite
      `collateral_registry.py`'s 2026-06-12 backfill — fixed those to `registry` too, broker question stays `gap`).
- [x] ✅ [SPEC] P1. **Simulation assumptions**: simulatable candle granularities, matching/fill assumptions per
      archetype area, backtest-live symmetry nuances per venue/instrument. — **FIXED 2026-07-27 (slot-12)**: matches the
      2026-07-27 (slot-13) recurring pattern above — `SIM_ASSUMPTIONS_REGISTRY`
      (`unified_api_contracts/internal/architecture_v2/simulation_assumptions.py`) was ALREADY backfilled in
      `unified-api-contracts@5e7d0685` (2026-06-13) with 18 real per-(venue, instrument_type) entries covering every
      ask: `supported_granularities` (`["1m","5m","15m","1h","4h","24h"]`, cited to
      `strategy_service/cli/resolvers.py:32` `TIMEFRAMES`), `matching_model` (per-venue `MatchingModel`, derived from
      the canonical `BenchmarkFillMode`), and batch-live symmetry nuances (`fill_assumptions` carries the shared
      `_BATCH_LIVE_DIVERGENCE` note — benchmark-only fills, no real slippage/partial fills, in-process vs PBMS position
      state — on every entry). The module's own F11 code-scan answer (already in-file) also settles "per archetype
      area": fill model is dispatched by INSTRUCTION ACTION TYPE, not archetype family — the one archetype-specific
      exception (LIQUIDATION_CAPTURE → `LIQUIDATION_BONUS`) is the sole archetype-keyed rule. **Only the module
      docstring was stale** (claimed "intentionally empty" despite the real backfilled data below it) — fixed in
      `unified-api-contracts@5ff6e238` (mirrors the `fees_registry.py`/`order_semantics.py` STATUS-line pattern).
      Pre-existing passing tests already assert the backfill
      (`tests/unit/test_order_semantics_sim_backfill.py::test_sim_assumptions_is_backfilled_not_empty` +
      `tests/unit/test_capability_manifest.py::test_sim_assumptions_registry_backfilled`, both assert
      `len(SIM_ASSUMPTIONS_REGISTRY) >= 16`) — no new test needed. Companion doc-drift also fixed:
      `capability-wizard-question-bank.md`'s Stage E rows for "simulation matching/fill assumptions" and "known
      batch-live asymmetries" flipped `gap`→`registry` (`unified-trading-pm@97833e7d42786002ad8bca76bdba52701016511f`);
      `capability-wizard.md`'s status table already correctly cited `5e7d0685` for sim-assumptions (no fix needed
      there). No design work remaining.
- [x] ✅ [SPEC] P1. **Fund structures**: offerable pooled/SMA/prop structures with subscription/redemption + rebalance
      cadences (fund-administration state machines are runtime truth; nothing declares what is offerable). — **PUSH
      CONFIRMED LANDED 2026-07-27 (slot-13)**: `unified-api-contracts@8903683a` (docstring fix — the module's
      "intentionally empty" claim replaced with the accurate 2026-06-13 backfill status) verified present at the tip of
      `origin/live-defi-rollout` (`git log --oneline -1 origin/live-defi-rollout` = `8903683a`; local HEAD ahead/behind
      origin = 0/0; `.qg_last_passed_sha` sentinel == HEAD == `8903683a`, so the full `quality-gates.sh` green run
      claimed for this SHA is the same SHA that shipped, not a stale claim). `OFFERED_FUND_STRUCTURES` (POOLED + SMA,
      `FundStructureKind`, cited to `sma-vs-pooled.md`) confirmed populated with
      `share_classes`/`subscription_cadence`/`redemption_cadence`/`rebalance_cadence`/`supports_daily_withdraw_deposit`
      per entry; PROP honestly omitted. Pre-existing test
      `tests/unit/test_capability_manifest.py:: test_offered_fund_structures_backfilled` (asserts
      `len(OFFERED_FUND_STRUCTURES) == 2`) read directly — real, not stubbed. The companion doc-drift fixes also
      confirmed landed via `unified-trading-pm@53d45aa43` (already on `origin/live-defi-rollout`, same commit that
      recorded the original push-blocked state): `capability-wizard.md`'s status table now cites `5e7d0685` (not the
      stale pre-backfill `6f31f59`) for fund-structures/order-semantics/sim-assumptions/agent-capability/fees;
      `capability-wizard-question-bank.md`'s Stage A fund-structure question status reads `partial` (was `gap`),
      matching the sibling cadence question. No further action needed on this item.
- [x] ✅ [SPEC] P1. **Order semantics per venue adapter**: TIF (FOK/IOC/post-only), make/take, ref-pricing modes (fixed
      vs delta-adjusted to underlying), multi-leg/spread delta-risk ownership, auth-wired status. — ALREADY FIXED
      (checkbox was stale), confirming the 2026-07-27 (slot-13) pattern flagged above: `git log --follow` on
      `order_semantics.py` shows the registry was backfilled in `unified-api-contracts@5e7d0685` (2026-06-13, "backfill
      order-semantics + sim-assumptions + fees + fund-structures + trading-agent registries"), same commit as the other
      four Phase-2 items. Verified 2026-07-27: `VENUE_ORDER_SEMANTICS` carries 7 real per-venue entries
      (hyperliquid/deribit fully wired with source file:line citations; binance/bybit/okx honest `NOT_REGISTERED`
      scaffolds — `NotImplementedError` on `place_order`; aave_v3/kamino lending venues, no CLOB/TIF semantics) — every
      field the todo asks for (`honored_tif`, `make_take_modes`, `ref_pricing_modes`, `multi_leg_delta_owner`,
      `auth_wired`) is populated or explicitly honest-empty, matching the Collateral/Fees/Fund-structures resolution
      pattern exactly. Only the file's own top-of-file docstring was stale ("STATUS: schema shipped;
      `VENUE_ORDER_SEMANTICS` is intentionally empty") despite the real backfilled data below it — fixed in
      `unified-api-contracts@2648f916` (mirrors the `fees_registry.py` STATUS-line pattern). Pre-existing passing tests
      (`tests/unit/test_capability_manifest.py::test_venue_order_semantics_backfilled` +
      `tests/unit/test_order_semantics_sim_backfill.py`) already assert the backfilled population — no new test needed.
      No design work remaining.
- [x] ✅ [SPEC] P2. **Trading-agent/LLM capability**: no declaration linking trading-agent-service to archetypes (which
      strategies permit agent-driven instructions over features, which models are allowed). — **ALREADY FIXED (checkbox
      was stale), same 2026-07-27/28 pattern as the four sibling items above**: `TRADING_AGENT_CAPABILITIES`
      (`unified_api_contracts/internal/architecture_v2/trading_agent_capability.py`) was already backfilled in the same
      `unified-api-contracts@5e7d0685` (2026-06-13) commit that backfilled order-semantics/sim-assumptions/fees/
      fund-structures (commit message literally lists "...+ trading-agent registries"). Verified 2026-07-28: 3 real
      code-sourced entries (`CARRY_STAKED_BASIS`, `ARBITRAGE_PRICE_DISPERSION`, `VOL_TRADING_OPTIONS`), each citing
      trading-agent-service `core/allocation_directive_loop.py`/`config.py:156` source lines, each honestly
      `enabled=False` (service is a no-op stub) — every field the todo asks for (archetype↔agent link,
      `allowed_decision_models`, `parameter_guidance_scope`) is populated or explicitly honest-empty, matching the
      Order-semantics/Fees/Sim-assumptions/Fund-structures resolution pattern exactly. Only the module's own docstring
      was stale (claimed "intentionally empty"/`missing_registry` gap despite the real backfilled data below it) — fixed
      in `unified-api-contracts@89adf316`. Pre-existing passing test
      `tests/unit/test_capability_manifest.py::test_trading_agent_capabilities_backfilled` (asserts
      `len(TRADING_AGENT_CAPABILITIES) == 3`) already asserts the backfilled population — no new test needed. Companion
      doc-drift also fixed: `capability-wizard-question-bank.md`'s Stage C "Decision engine" row flipped
      `partial / gap`→`partial` (`unified-trading-pm@587afb751`); `capability-wizard.md`'s status table already
      correctly cited `5e7d0685` for agent-capability (no fix needed there). No design work remaining.

### Open questions — `needs_code_scan` candidates (agent-orchestrator once Phase 5 wiring exists)

- [x] ✅ [AGENT] P2. Options execution wiring depth: greeks-service computes; VOL family (18 archetypes) registered;
      whether execution-service options algos are wired end-to-end per venue is unverified. — ANSWERED 2026-06-13
      (code-scan): **Deribit options FULLY WIRED end-to-end** (venues/deribit_orders.py — instrument-type
      classification, integer-contract amount conversion, TIF map, httpx REST placement). **All other venues: options
      placement NOT implemented** — Binance/Bybit/OKX are scaffolds (NotImplementedError on place_order), Hyperliquid
      adapter has no options-specific logic. Net: options execution depth = Deribit-only today; the VOL family's other
      venues are compute-only (greeks) with no order path.
- [x] ✅ [AGENT] P1. Exposure normalization location: staked-ETH vs ETH equivalence / delta-adjusted exposure — not
      found as a declared model (greeks-service? features-service? ledger?); prospectus needs it. — ANSWERED 2026-06-13
      (code-scan) = **GENUINE GAP (F45)**. PRIMITIVES exist in UAC: `TOKEN_EQUIVALENCE_GROUPS` + `is_token_equivalent()`
      (registry/capability_declarations/\_defi.py:870-940/1019 — full 20+ LST universe) and `LST_BASE_ASSET` +
      `lst_adjusted_value()` (registry/token_wrapping.py:43-47/159 — 3 wrapped forms, oracle-ratio base-equivalent),
      plus the `RiskMetrics.delta_composite` schema (internal/risk.py:82) and per-instrument Black-Scholes greeks
      (greeks-service kernels/black_scholes.py). But **NO service owns the end-to-end pipeline** that maps each LST leg
      → underlying → per-leg delta → net `delta_composite`/USD-normalized view. greeks-service computes per-instrument
      greeks only; no `compute_net_delta`/`portfolio_delta`/`exposure_normalizer` exists. Prospectus correctly emits an
      honest gap line. Successor: a risk-service / strategy-service pre-trade layer consuming `lst_adjusted_value` +
      per-leg greeks. Filed F45 in findings doc.
- [x] ✅ [AGENT] P2. SOR decision trees: smart-order-routing logic scattered across algo files; no single manifest of
      routing decisions for the wizard to describe. — ANSWERED 2026-06-13 (code-scan): algo SELECTION lives in
      execution_service/algorithms/selector.py (`ALGORITHMS_BY_INSTRUCTION_TYPE` + `select_algorithm`: ZERO_ALPHA→
      BENCHMARK_FILL, then requested→config-default→type-default). Price-routing SOR proper is execution_service/
      algorithms/sor.py and is **DEX-ONLY (SWAP instruction)**: gather quotes from UNISWAP_V3/CURVE/BALANCER → sort by
      effective_price → single venue if impact ≤ max_slippage_bps else split inversely-weighted across top-N (impact is
      SIMULATED, not live pool state). **No CeFi perp SOR exists**; TRADE instructions use TWAP/VWAP/ALMGREN_CHRISS, not
      a price-routing SOR. This is captured declaratively in UAC `algo_compatibility.py` (already shipped Phase 6A).
- [x] ✅ [AGENT] P1. Multi-leg execution: which algorithm manages inter-leg delta risk for basis/spread/option-combo
      instructions executed simultaneously. — ANSWERED 2026-06-13 (code-scan) = **GAP (unmanaged)**. NO component
      manages inter-leg delta risk today. `algorithms/atomic_bundle_executor.py` handles DeFi flash-loan bundle
      atomicity (all-or-nothing revert) — pure execution coordination, no delta management. OPTIONS_COMBO routes to
      SEQUENTIAL_LEGS (selector default) but no code implements delta hedging or inter-leg netting. Reflected in
      VENUE_ORDER_SEMANTICS (`multi_leg_delta_owner=None` for every venue, backfilled 2026-06-13) — honest "no owner".

## Discovered later (append below; date each entry; pin a test when fixed)

### 2026-07-27 (slot-13) — recurring pattern: 4 of the 5 "missing_registry" Phase-2 items are already backfilled, only the checkbox/docstring is stale

Working todo 115 (Fund structures) surfaced a pattern worth flagging BEFORE picking up 113/117/119 (Simulation
assumptions / Order semantics / Trading-agent capability — still `- [ ]`, backlog ids `-008`/`-010`/`-011`): all FIVE
Phase-2 "missing_registry" items (Collateral, Fees, Fund structures, Order semantics, Simulation assumptions) plus
Trading-agent capability were seeded 2026-06-11 as schema-only, genuinely-empty stubs (`UAC@6f31f594`), then ALL
backfilled with real data in ONE commit — `unified-api-contracts@5e7d0685` (2026-06-13, "backfill order-semantics +
sim-assumptions + fees + fund-structures + trading-agent registries"). That commit updated the DATA in each file but did
**not** update each file's own top-of-file `STATUS: ... is intentionally empty` docstring line — so `order_semantics.py`
/ `simulation_assumptions.py` / `trading_agent_capability.py` (verified directly, 2026-07-27) all still read as empty in
their own docstrings despite `VENUE_ORDER_SEMANTICS` / `SIM_ASSUMPTIONS_REGISTRY` / `TRADING_AGENT_CAPABILITIES` each
carrying real per-venue/per-archetype entries, pre-existing passing tests in `tests/unit/test_capability_manifest.py`,
and no design work remaining. **Before implementing any of 113/117/119 from scratch:
`git log --follow -- unified_api_contracts/internal/architecture_v2/<file>.py` first** — if the latest commit is
`5e7d0685` (or a later backfill), the real work is (a) verify the registry's actual population against the todo's ask
(it likely already matches — that is what happened for Collateral/Fees/Fund-structures), (b) fix the stale docstring,
(c) flip the checkbox with the evidence, same as this entry's own todo 115 resolution above. Not fixed here (scope
discipline — one todo per dispatch, avoid same-file collision with whichever slot picks up 113/117/119 next); flagging
so that dispatch goes straight to the fix instead of re-deriving this from scratch.

### 2026-06-11 — capability-manifest v1 quantified the gap surface (exporter, slot-4)

`generate_capability_manifest.py` v1 generated `capability-manifest.json` (UAC@434e5be): **409 nodes, 663 edges**.
Edge-status breakdown: 441 available, 140 partial, 63 not_registered, 19 not_available. Typed-gap counts: **60
missing_registry, 3 needs_code_scan, 1 missing_extraction, 19 logical_dead_end**. Orphan/dead-end report: **124 orphan
nodes, 25 unbuilt dead-ends, 16 logical dead-ends** (`openapi/capability-orphan-report.txt`, UAC@1bc2f07).

Concrete gap drivers surfaced (each = a backfill candidate):

- **Source-mode matrix is a registry gap** — `live`/`replay` per-source capability is NOT in any UAC registry (it lives
  in the manual `source-mode-capability-matrix_2026-06-07.md` audit). The exporter emits a `missing_registry` gap edge
  per (source × {live,replay}) rather than parsing the markdown → ~56 of the 60 missing_registry edges. Codifying that
  matrix into a UAC registry is the single highest-leverage gap close.
- **Honest-empty registries** still empty: collateral, fees, fund-structure, order-semantics, trading-agent → one
  explicit `not_registered`/`needs_code_scan` edge each (never silently omitted). sim_assumptions = `needs_code_scan`
  (F11). These are the Phase-2 backfills already tracked above.
- **Min-data-to-run is only half-derivable** — feature-group lookback (max bar `period` per group) IS extracted from
  features-service; the ML training-window factor is a RUNTIME config with no static registry constant, so the full
  `min_data_to_run = feature_lookback × training_window` edge is emitted `partial` + `missing_extraction`. Closing it
  needs an ML-training-window registry constant (or a model_registry static field).
- **124 orphan nodes** — mostly venue / instrument_type / chain nodes present in venue registries but never referenced
  by an archetype capability cell. Expected (registry breadth > MVP archetype coverage); the wizard greys them.
- **25 unbuilt dead-ends** — (archetype, instrument_type) the capability registry marks `available` but where no venue
  of that instrument-type's asset_group lists the instrument type (missing-adapter class). These are the use-case-3
  "unbuilt" findings; each is a candidate adapter/registry build. Enumerated in `capability-orphan-report.txt`.

All gaps are TYPED in the manifest (never silent) — the forcing-function state the plan intends.

### 2026-06-13 — Wave-2 #2 readiness badges shipped (exporter); uts-ui badge surface is the follow-on

`generate_capability_manifest.py` now folds a per-edge operational-maturity tier
(`backtest-only | shadow-observed | staging-proven | live-proven`) onto every archetype-originating edge
(`CapabilityEdge.readiness`), plus a sibling `openapi/capability-readiness-report.{json,md}`. Evidence is the only real
on-host maturity signal: `LIVE_CLUSTER_REGISTRY` (UAC) — a PROD-tier row owning an archetype ⇒ `live-proven`, STAGING ⇒
`staging-proven`; absent evidence ⇒ `backtest-only` (honest default, never over-claimed). Today's distribution (57
archetypes): **2 live-proven** (`CARRY_STAKED_BASIS`, `ARBITRAGE_PRICE_DISPERSION` — the May-23 live archetypes, cited
by their PROD strategy/MTDS clusters), **0 staging-proven**, **0 shadow-observed** (no committed shadow ledger on-host;
the `shadow_mode` flag + GCS-backed `deployments_registry.py` carry no committed run records, so `shadow-observed` is
reached only via a deliberate `READINESS_OVERRIDES` entry — none today), **55 backtest-only**. Logic + tests:
`scripts/openapi/_capability_readiness.py` + `tests/unit/test_capability_readiness.py`. Additive metadata only — never
flips an edge's `status`; capability-regression gate green.

- [x] ✅ [UI] P2. **DONE 2026-07-28 (slot-4)** — **Surface the per-edge `readiness` badge in the capability wizard** —
      `unified-trading-system-ui@2af6c97d`. `capability-readiness-report.json` was never actually synced into
      `lib/registry/` (the sync step in `generate-unified-openapi.sh` already handled it, it just hadn't been re-run
      since Wave-2 #2 shipped) — copied it in, added a typed accessor (`lib/registry/capability-readiness.ts`), a
      `ReadinessBadge` chip component rendered next to the existing `GapChip` availability tick on archetype cards
      (`components/wizard/OptionCard.tsx`), and wired the tier + cited evidence through `getAllArchetypesForFamily`
      (`lib/wizard/graph.ts`) so nothing is invented client-side — backtest-only=grey, shadow-observed=amber,
      staging-proven=blue, live-proven=green, tooltip cites `live_cluster_registry:<name>` (or the honest "no
      operational evidence" default). New pw:L2 spec `tests/smoke/wizard-readiness-badge.spec.ts` proves both a
      live-proven archetype (`ARBITRAGE_PRICE_DISPERSION`) and a backtest-only sibling in the SAME family
      (`LIQUIDATION_CAPTURE`) render correctly on the same stage. **pw:L2 ✓**
      (`npx playwright test --project=chromium tests/smoke/wizard-readiness-badge.spec.ts` green). tsc/ESLint/Vitest
      (3286 tests) + full `quality-gates.sh` all green. Also fixed one adjacent pre-existing stale count assertion found
      while running the full smoke suite (venue count drifted 195→225 in `tests/smoke/wizard.spec.ts`); the remaining
      ~65 unrelated pre-existing smoke failures seen in that run were NOT individually triaged — filed as
      `plans/active/issues/wizard_smoke_suite_pre_existing_failures_2026_07_28.md`, since triaged and RESOLVED
      2026-08-01 (104/108 passed under the correct `--workers=1` measurement; 1 genuine defect found + filed as
      `/plans/archive/issues/wizard_jurisdiction_overlay_dropped_by_registry_regen_2026_08_01.md` (resolved 2026-08-02)
      — archived at `plans/archive/issues/wizard_smoke_suite_pre_existing_failures_2026_07_28.md`.

<!-- GAP ENTRIES: two-sided audit (auto-appended by audit_prospectus_vs_codex.py) -->

### Archetype Doc Coverage Gaps (from two-sided audit)

#### Doc-without-enum (orphan codex docs)

- `carry-recursive-borrow-perp-hedged.md` | taxonomy: `logical_dead_end` | would-map-to:
  `CARRY_RECURSIVE_BORROW_PERP_HEDGED` | action: add enum value OR delete stale doc
- `carry-recursive-staked-config-variants.md` | taxonomy: `logical_dead_end` | would-map-to:
  `CARRY_RECURSIVE_STAKED_CONFIG_VARIANTS` | action: add enum value OR delete stale doc

## Escalated needs_code_scan (auto-emitted)

_Auto-emitted 2026-06-11 by `scripts/openapi/emit_capability_gap_todos.py`._ _Dedup-idempotent on re-run. Only edges
with `needs_code_scan` gap_type and no_ _`agent_annotation` appear here. Once annotated, edge drops off on next emit
run._

- [x] ✅ [AGENT] P2. **gap_registry:order_semantics** — Venue order semantics registry is honest-empty — per-adapter
      order-semantics honor matrix code-scan. Target repo: `execution-service`. Cold-start context:
      VENUE_ORDER_SEMANTICS backfill: scan each venue execution adapter for TIF (FOK/IOC/post-only), make/take,
      ref-pricing mode, multi-leg delta ownership; populate
      unified_api_contracts/internal/architecture_v2/order_semantics.py VENUE_ORDER_SEMANTICS. (auto-emitted by
      emit_capability_gap_todos.py) — **DUPLICATE of the already-resolved "Order semantics per venue adapter" item above
      (Missing registries section) — no code change needed, re-verified 2026-07-28 (slot-4)**: read
      `unified_api_contracts/internal/architecture_v2/order_semantics.py` at current `origin/live-defi-rollout` HEAD
      (`698b5b6f`, 2026-07-28) directly — `VENUE_ORDER_SEMANTICS` carries 7 real per-venue entries
      (hyperliquid/deribit/binance/bybit/okx CeFi perp, all `auth_wired=AVAILABLE` with live CCXT/REST adapter file:line
      citations in `notes`; aave_v3/kamino DeFi lending, no CLOB/TIF applicable) — every field the todo asks for
      (`honored_tif`, `make_take_modes`, `ref_pricing_modes`, `multi_leg_delta_owner`, `auth_wired`) is populated or
      explicitly honest-empty (`multi_leg_delta_owner=None` on every entry — no venue has multi-leg ownership wired, an
      honest gap not a missing one). Docstring already accurate (fixed by `2648f916`). Ran the two test files live:
      `tests/unit/test_order_semantics_sim_backfill.py` (12 passed) + `test_capability_manifest.py -k order_semantics`
      (3 passed) — 15/15 green. Provenance chain: `5e7d0685` (2026-06-13 backfill) → `2648f916` (docstring fix) →
      `698b5b6f` (2026-07-28 binance/bybit/okx CCXT-vs-native correction) — all already on `live-defi-rollout`, no new
      commit required. Closing per the doc's own "dedup-idempotent on re-run" rule — this checkbox is the
      `agent_annotation` that drops the edge from the next `emit_capability_gap_todos.py` run.

### 2026-06-12 — Margin traceability audit (operator question: "can we trace where our margin sits?")

DeFi collateral IS traced end-to-end (SUPPLY LedgerRow → aToken position → margin models → MarginEvent pub/sub →
alerting/kill-switch/deleverage). CeFi perp margin is NOT — 7 gaps with file evidence (full report in plan Progress Log
context; recommended owner strategy-service PBM):

- [x] ✅ [SPEC] P1. `TransferIntent`/`AllocationTarget` gain a `transfer_purpose` field (MARGIN_DEPOSIT etc.) + ledger
      EventType gains COLLATERAL_POSTED/MARGIN_RELEASED — today a USDC margin transfer to hyperliquid is
      indistinguishable from any other transfer. unified-api-contracts + execution-service + fund-administration. —
      **UAC SURFACE DONE 2026-06-13 — unified-api-contracts@dc67ae6 (additive/non-breaking)**: `TransferPurpose` StrEnum
      (GENERAL default +
      MARGIN_DEPOSIT/MARGIN_WITHDRAWAL/COLLATERAL_POSTING/COLLATERAL_RELEASE/REBALANCE/TREASURY_SWEEP/FUNDING) +
      optional `TransferIntent.transfer_purpose` field (defaults GENERAL → existing emitters unaffected) +
      `EventType.COLLATERAL_POSTED`/`MARGIN_RELEASED` (instruction-driven, cross-referenced to the transfer purposes);
      exported via the crosscutting + root facades. 4 tests. NOTE: `AllocationTarget` lives in fund-administration (not
      UAC) — its `transfer_purpose` wiring + the execution-service/fund-admin consumers are the IMPLEMENT half below
      (engine-coupled). The contract surface that makes margin transfers traceable is now in place.
- [x] ✅ [IMPLEMENT] P1. CeFi margin emission: margin_event_emitter.py is DeFi-only (hardcodes venue_type="defi"); UTL
      margin models for HL/Bybit/OKX/Binance exist but nothing feeds them live balances. strategy-service PBM owns.
      **DONE 2026-07-27 — strategy-service@3c14639d.** The freeze cited below (2026-06-13) was lifted 2026-07-12
      (operator ruling; freeze language removed from `epics/strategy_master.md`), unblocking this. By the time of this
      flip, the emitter itself was ALREADY fixed by a separate margin-cluster remediation (2026-06-15, predates this
      flip): `emit_margin_event_for_cefi` in `margin_event_emitter.py` carries a real `venue_type="cefi"` path (not
      hardcoded "defi"), and `CefiVenueBalanceReader`/`cefi_margin_model_for_venue` (`core/venue_balance_tracker.py`)
      already built live per-venue `PortfolioInputs` from the UPI-backed `AccountQueryClient` — but only for the
      pull-based `margin_health.py` query API (`get_margin_health`/`compute_live_cefi_snapshots`). "Nothing feeds them
      live balances" into an actual _emission_ was the one part still genuinely open. Closed: added
      `emit_live_cefi_margin_events()` (`core/venue_balance_tracker.py`) — reuses the existing reader/model-resolution
      building blocks to PUSH a `MarginEvent` via `emit_margin_event_for_cefi` per CeFi perp venue (shard-isolated per
      venue), wired into the live monitor's periodic reconciliation loop (`cli/handlers/monitor_handler.py`) so a CeFi
      margin breach now reaches the `margin-events` topic the same way DeFi's `update_lending_positions` push already
      does. Also added shard-level failure isolation to the sibling read path (`compute_live_cefi_snapshots` in
      `api/margin_health.py`) — a pre-existing gap in the same file where one venue's exchange-fetch failure could fail
      the whole call. 5 new unit tests (`tests/position/unit/test_emit_live_cefi_margin_events.py`); quality-gates.sh
      green (sentinel=27c2ecd7, amended to 3c14639d by quickmerge's trailer). **Found + filed, not fixed here** (out of
      this todo's scope): the CeFi margin model's asset-symbol parsing mis-scores real (hyphenated) instrument ids via a
      bad fallback, misclassifying healthy positions as WARNING —
      `/plans/archive/issues/cefi_margin_model_hyphenated_instrument_id_misclassification_2026_07_27.md`.
- [x] ✅ [IMPLEMENT] P2. margin_health API is a Phase-1 stub returning []; no CeFi per-venue margin balance tracker
      (venue_balance_tracker.py is sports-only). strategy-service. **LOGIC FREEZE — engine-runtime, deferred to PBM
      dispatch** (the API surface exists; the real CeFi balance tracker is engine work). — **STALE, already resolved
      2026-07-28 (slot-12, no new code needed)**: re-verified against current `origin/live-defi-rollout`
      (`strategy-service@3c14639d`) — `strategy_service/position/api/margin_health.py` is NOT a stub (its own docstring:
      "the live compute here is the SSOT for current margin, not a stub"); `get_margin_health` /
      `compute_live_cefi_snapshots` build real `MarginHealthSnapshot[]` per CeFi perp venue via
      `CefiVenueBalanceReader.build_portfolio` + `get_margin_model(...).compute(...)`, haircut-adjusted collateral (F28
      SSOT), shard-isolated per venue. `venue_balance_tracker.py` is NOT sports-only — alongside the sports
      `VenueBalanceTracker`, it carries a full CeFi per-venue margin section (`CEFI_PERP_VENUES`,
      `CEFI_PERP_MARGIN_MODELS`, `cefi_margin_model_for_venue`, `CefiVenueBalanceReader`,
      `emit_live_cefi_margin_events`). This was built by the sibling P1 item above (`b9b26433` 2026-06-15 margin
      cluster + `3c14639d` 2026-07-27 emission wiring) — the freeze note here predates that work and was never updated.
      Ran the live test suite: `test_cefi_margin_traceability.py` + `test_emit_live_cefi_margin_events.py` +
      `test_venue_balance_tracker.py` — 37/37 passed. No code change required; closing per re-verification, not a new
      implementation.
- [x] ✅ [IMPLEMENT] P2. Runtime consumer for the UAC collateral registry: haircut-adjusted posted-collateral value
      feeding MarginHealthSnapshot.collateral_usd (also resolves the F28 dual-SSOT risk). UTL/strategy-service. —
      **RE-SCOPED + DONE 2026-07-28 (slot-3)**: re-verified against current code first (the 2026-07-27 slot-13
      recurring-pattern note above applies here too). strategy-service's `margin_health.py` (`_snapshot_for_venue` →
      `_haircut_adjusted_collateral_usd`) ALREADY builds a real, live, haircut-adjusted
      `MarginHealthSnapshot. collateral_usd` per CeFi perp venue, reading `get_collateral_haircut()` from UAC's
      F28-canonical `venue_collateral.py` — the functional runtime-consumer ask was met by the sibling
      margin-traceability work above (built after this todo was written 2026-06-11/12), just not via the literal
      `COLLATERAL_REGISTRY` module this todo names. **The real residual gap**: `COLLATERAL_REGISTRY` (architecture_v2)
      was a HAND-TRANSCRIBED copy of `venue_collateral.py`'s perp-CEX haircuts (confirmed via `git log` — commit
      `bc455499` had to touch BOTH files in the same commit to stay in sync) — a live F28-class dual-SSOT drift risk
      (not yet drifted, but one manual-sync-miss from it), distinct from the already-resolved F28 (venue_collateral.py
      vs the now-deleted execution-service `lst_collateral_resolver.py` `_LST_REGISTRY`). Fixed: `COLLATERAL_REGISTRY`'s
      5 perp-CEX venues (hyperliquid/binance/bybit/deribit/okx) now DERIVE their `accepted`/`haircut_pct` fields from
      `venue_accepts_collateral()`/`get_collateral_haircut()` at import time (`_ah_from_venue_collateral()`), mirroring
      the fix already shipped for `lst_collateral_resolver.py` — `unified-api-contracts@c0111ee1`. Verified numerically
      identical to the prior hardcoded values for all 30 perp-CEX rows (zero drift today); added a regression test
      (`test_perp_cex_haircuts_derived_from_venue_collateral_live`) pinning the derivation so a future accidental revert
      to a hardcoded literal is caught immediately instead of silently drifting. Aave/Kamino (LENDING) numerics stay
      hand-sourced — `venue_collateral.py` carries no LENDING rows to derive from, so there is no duplicate there.
      `quality-gates.sh` green (553s). No UTL-side change needed — UTL's margin models consume an already-computed
      `collateral_usd`, not raw haircut data; grepped UTL for `collateral_registry`/`COLLATERAL_REGISTRY` — zero hits,
      confirming no other consumer expectation exists there.
- [x] ✅ [UI] P2. uts-ui Stage-A jurisdiction-filter surface is the follow-on consumer of the UAC jurisdiction overlay
      registry (`unified_api_contracts.internal.architecture_v2.jurisdiction_overlay` — `Jurisdiction` /
      `JURISDICTION_VENUE_POLICIES` / `allowed_venues_for_jurisdiction` / `is_venue_allowed`, backfilled 2026-06-13):
      the wizard reads the investor entity's jurisdiction and filters the venue/instrument picklist so a config can
      never include a venue the jurisdiction cannot legally touch (conservative default = blocked + needs_legal_review).
      UI repo; registry layer is done — this is the thin Stage-A filter surface only. — **EVIDENCE-ONLY CLOSURE
      2026-07-28 (slot-12)**: already shipped by slot-13 same-day and the checkbox was simply never flipped (`git log`
      confirms `unified-trading-system-ui@49a6fc9f` "feat(wizard): Stage-A jurisdiction filter for the capability
      wizard", ancestor of current HEAD on `live-defi-rollout`). Re-verified the implementation directly against this
      todo's spec rather than trusting the commit message: `lib/wizard/graph.ts` `applyJurisdictionFilter()` marks an
      in-scope disallowed venue `disabled`+`status: "not_available"` with a policy-reason prefix (never un-disables a
      venue already blocked for capability reasons), `lib/registry/jurisdiction-overlay.ts` is the typed TS mirror of
      the UAC registry reading `ui-reference-data.json`, and `app/(wizard)/wizard/page.tsx` wires a
      `jurisdiction-select` dropdown into Stage A (`data-testid="stage-A-jurisdiction-filter"`) feeding the Stage-E
      venue/leg-group filtering. Note: the registry (and this filter) is venue-scoped, not instrument-scoped — the UAC
      `JurisdictionVenuePolicy` has no instrument axis, so "venue/instrument picklist" in the todo's prose is satisfied
      via venue-gating (an instrument is only reachable through an allowed venue). Re-ran the existing regression spec
      fresh (not just re-reading it):
      `npx playwright test --project=chromium tests/smoke/wizard-jurisdiction-filter.spec.ts` — 2/2 passed (US_CFTC
      blocks known CeFi-perp venues at Stage E; unset jurisdiction is a no-op). No code change required. —
      unified-trading-system-ui@49a6fc9f | pw:L2 ✓ | regression: tests/smoke/wizard-jurisdiction-filter.spec.ts

## Closest-to-unlock roadmap (auto-emitted)

_Auto-emitted by `scripts/openapi/generate_capability_unlock_report.py --emit-todos`._ _The N blocked edges closest to
available (lowest `unlock_distance`) — the_ _highest-leverage roadmap items. Dedup-idempotent on re-run._

- [x] ✅ [SCRIPT] P2. **INVESTIGATED 2026-07-29 (slot-3) — genuinely not unlockable via a leg-spec write; correctly
      stays `not_registered`.** **unlock ARBITRAGE_MEV_SANDWICH --has_leg:legs--> ARBITRAGE_MEV_SANDWICH** (distance 1,
      status not_registered) — missing: needs-leg-spec. Why blocked: ARBITRAGE_MEV_SANDWICH has no leg structure in
      ARCHETYPE_LEG_STRUCTURES yet — structural per-leg restrictions not modelled (F22 leg-truth gap). Confirmed via
      direct code read: `ARBITRAGE_MEV_SANDWICH` is absent from `ARCHETYPE_ENGINE_REGISTRY`
      (`strategy-service/strategy_service/engine/strategies/v2/factory.py`) — there is no `BaseArchetypeEngineV2` for
      it. Its only code, `sandwich_theoretical.py`, is an explicitly-documented backtest-only profit tracer ("This
      module computes the theoretical-upper-bound profit... it is _not_ an executable engine"; sandwich requires mempool
      pending-tx visibility, and the Bloxroute mempool feed was removed) — it emits `SandwichTheoreticalProfit`
      dataclasses, never an `AtomicLeg`/instruction structure a leg spec could cite. `archetype_leg_spec_seeds.py`'s own
      LOGIC FREEZE rule ("every leg is a citation of the shipped engine structure... NEVER invented") therefore forbids
      writing a real leg spec here — there is no engine structure to cite, so any leg spec would be invented, not
      transcribed. **This is why `_not_registered_structure()` seeded it explicitly** (not an oversight). Also confirmed
      the `missing_registry` gap-type labeling (vs `logical_dead_end`) is this workspace's deliberate, already-tested
      design, not a mislabel to fix:
      `tests/unit/test_capability_verdict_matrix.py::test_not_registered_archetypes_are_explicit_blocks` pins "the
      genuinely-underivable archetypes (no leg structure) → missing_registry" for this exact archetype —
      `missing_registry` correctly signals "not derivable YET" (conditionally blocked pending upstream data) rather than
      `logical_dead_end`'s "permanently, structurally impossible" (e.g. options on a sports venue), so reclassifying
      would be a regression, not a fix. **The real unlock path**: the archived, `status: paused`
      `/plans/archive/mempool_feed_integration_2026_06_01.plan.md` — reintroducing mempool data would let a real
      sandwich engine (and thus a real, citable leg spec) get built; per this workspace's own removed-provider rule
      (CLAUDE.md DeFi-execution section), Bloxroute is NOT to be reintegrated without explicit operator direction, so
      that plan stays paused pending an operator call, not agent action. No code changed — writing a leg spec now would
      violate LOGIC FREEZE; the `not_registered` structure + `missing_registry` gap type are both already correct.
      (auto-emitted by generate_capability_unlock_report.py)
- [x] ✅ [SCRIPT] P2. **FIXED 2026-07-29 (slot-16) — root-cause bug found + patched; edge correctly stays `partial`.**
      **unlock ARBITRAGE_PRICE_DISPERSION --supports--> venue:cboe** (distance 1, status partial) — missing:
      needs-config. Why blocked: (no reason recorded). Root cause: `_capability_extract.py`'s
      `extract_archetypes_and_families()` built the `archetype --supports--> venue` edge WITHOUT ever passing `reason=`,
      unlike the sibling `trades_instrument` edge from the same cell 3 lines earlier (which already does
      `reason=(cell.notes or None) if cell.notes else None`) — so every partial `supports` edge fell through the
      unlock-report classifier's empty-reason default (`needs-config`/"(no reason recorded)") even when the underlying
      `ArchetypeCapabilityCell.notes` already documented a real, specific caveat. For this cell specifically
      (`archetype_capability_manifest.json`, TRADFI/option), `notes` = "Same-surface no-arb (butterfly / calendar /
      parity) on CBOE via IBKR." — CBOE is a fully live, already-integrated venue (`CBOEAdapter` routes via IBKR,
      `readiness: live-proven`, prod slot `cboe-spy-surface-noarb-usd-prod`); the PARTIAL status is real and correct,
      not a venue-integration gap: the cell's declared `signal_variants` is `iv_dispersion` (full vol-surface
      dispersion) but only same-surface no-arb signals are actually built — full cross-strike/cross-expiry iv dispersion
      needs the multi-leg vol-arb algo the sibling `trades_instrument --> instrument_type:option` todo already documents
      as pending, which is a real build item, not a config fix, and out of scope for this todo. Fixed the propagation
      bug (one line, matches the existing `trades_instrument` pattern exactly) — unified-trading-pm@1e97a608f. Verified
      via regenerated `capability-unlock-report.json`: this edge now carries
      `reason="Same-surface no-arb (butterfly / calendar / parity) on CBOE via IBKR."` (status stays `partial`,
      correctly — no evidence justifies promoting to `available`). Note the new reason text contains the substring
      "calendar" (as in _calendar spread_), which the unlock-report's keyword classifier (`_capability_unlock.py`
      `_REASON_CLASSIFIER`) matches against its `needs-data-feed` family (intended for economic-calendar feeds) — so the
      piece label is now `needs-data-feed` instead of `needs-config`; this is a pre-existing classifier blunt-instrument
      quirk (documented as "deterministic, ordered match... first matching family wins"), not a new bug, and out of
      scope to refine here. **Independently converged with slot-10**: `unified-api-contracts@c4f42fbc` already
      regenerated + shipped the manifest/report artifacts under this exact fix (citing this same cboe example in its
      commit body) before I finished investigating — verified their committed `capability-unlock-report.json`
      byte-matches my own regen for this edge; no UAC-side action was needed from this todo, only the PM-side source fix
      their commit depended on (which had not yet landed — this commit lands it). `check_capability_regression.py`
      unaffected (no edge `status` changed, only `reason`). This same root-cause fix also resolves the 4 sibling
      `--supports--> venue:{cme,deribit,ibkr,ice}` todos below (each now carries its real cell `notes` as reason instead
      of "(no reason recorded)") — left their checkboxes un-flipped since they weren't this todo's scope; a future pass
      on those should find real reasons already populated once regenerated. (auto-emitted by
      generate_capability_unlock_report.py)
- [x] ✅ [SCRIPT] P2. **RESOLVED 2026-07-29 (data_pipeline_failure escalation worker, agt-79063c, resumed as
      capability_wizard_gap_discovery-020) — already fixed by the sibling `venue:cboe` todo above, no new code needed.**
      That todo's root-cause fix (`_capability_extract.py`'s `--supports-->` venue edge now passes
      `reason=(cell.notes or None) if cell.notes else None`, matching the sibling `trades_instrument` edge — shipped
      `unified-trading-pm@1e97a608f`, manifest regenerated `unified-api-contracts@c4f42fbc`) explicitly predicted it
      would also resolve this todo. Verified rather than re-diagnosed: regenerated `capability-unlock-report.json` from
      the already-committed, already-fresh `capability-manifest.json`
      (`generate_capability_unlock_report.py --output-dir /tmp/cap-unlock-check`, scratch dir — no repo files mutated)
      and confirmed the `ARBITRAGE_PRICE_DISPERSION --supports--> venue:cme` edge now carries
      `reason="IBKR smart-router absorbs most intra-TradFi spot arb."` (from the `(TRADFI, spot)` cell's `notes` in
      `archetype_capability_manifest.json` — status stays `partial`, correctly, since IBKR-routed spot arb is a real,
      narrower capability than full cross-venue price dispersion). Same pre-existing classifier-keyword quirk noted on
      the `venue:cboe` todo applies here too (`missing_pieces` relabeled `needs-registry-entry` instead of
      `needs-config` once a real reason populates the blunt keyword classifier) — not a new bug, not fixed here, same as
      that todo's own note. No code changed this pass; this is a checkbox-only verification flip.
- [x] ✅ [SCRIPT] P2. **RESOLVED 2026-07-29 (slot-12, capability_wizard_gap_discovery-021) — already fixed by the
      sibling `venue:cboe`/`venue:cme` todos above, no new code needed.** That todo's root-cause fix
      (`_capability_extract.py`'s `--supports-->` venue edge now passes
      `reason=(cell.notes or None) if cell.notes else None`, matching the sibling `trades_instrument` edge — shipped
      `unified-trading-pm@1e97a608f`, manifest regenerated `unified-api-contracts@c4f42fbc`) explicitly predicted it
      would also resolve this todo. Verified rather than re-diagnosed: regenerated `capability-unlock-report.json` from
      the already-committed, already-fresh `capability-manifest.json`
      (`generate_capability_unlock_report.py --output-dir <scratch>`, scratch dir — no repo files mutated) and
      confirmed the `ARBITRAGE_PRICE_DISPERSION --supports--> venue:deribit` edge now carries
      `reason="UAC lacks funding_arb flag distinct from price-arb (gap #2)."` (status stays `partial`, correctly — a
      real, narrower capability gap, not a venue-integration gap). Deribit sits in TWO `ARBITRAGE_PRICE_DISPERSION`
      cells in `archetype_capability_manifest.json` — CEFI/perp (this reason) and CEFI/option
      (`"vol_arb not a separate capability; multi-leg vol-arb algo pending."`), both PARTIAL;
      `compute_unlock_entries()`'s edge-key dedup (`_capability_unlock.py` — keeps first-encountered on a status tie,
      only overwrites on a strictly more-available status) deterministically resolves to the CEFI/perp cell's reason
      because it's iterated first in the manifest's cell order — the documented, pre-existing, already-tested dedup
      rule, not a new bug. Same pre-existing classifier-keyword quirk noted on the `venue:cboe`/`venue:cme` todos
      applies here too (`missing_pieces` relabeled `needs-registry-entry` instead of `needs-config` — the reason text
      contains the substring "gap #", which `_REASON_CLASSIFIER` matches to `PIECE_REGISTRY` before any config-shaped
      needle) — not a new bug, not fixed here, same as those todos' own notes. No code changed this pass; this is a
      checkbox-only verification flip.
- [x] ✅ [SCRIPT] P2. **RESOLVED 2026-07-29 (slot-16, capability_wizard_gap_discovery-022) — already fixed by the
      sibling `venue:cboe`/`venue:cme`/`venue:deribit` todos above, no new code needed.** That todo's root-cause fix
      (`_capability_extract.py`'s `--supports-->` venue edge now passes
      `reason=(cell.notes or None) if cell.notes else None`, matching the sibling `trades_instrument` edge — shipped
      `unified-trading-pm@1e97a608f`, manifest regenerated `unified-api-contracts@c4f42fbc`, confirmed ancestor of
      current UAC HEAD `f909e112` via `git merge-base --is-ancestor`) explicitly predicted it would also resolve this
      todo. Verified rather than re-diagnosed: regenerated `capability-unlock-report.json` from the already-committed,
      already-fresh `capability-manifest.json`
      (`generate_capability_unlock_report.py --output-dir <scratch> --dry-run`, scratch dir — no repo files mutated)
      and confirmed the `ARBITRAGE_PRICE_DISPERSION --supports--> venue:ibkr` edge now carries
      `reason="IBKR smart-router absorbs most intra-TradFi spot arb."` (status stays `partial`, correctly — IBKR is a
      real, narrower smart-router capability, not a missing venue integration). Traced to source:
      `archetype_capability_manifest.json`'s single `(TRADFI, spot)` cell lists BOTH `ibkr` and `cme` as `venue_ids`
      sharing this one `notes` string — the identical reason text on the sibling `venue:cme` todo above is not a
      coincidence, it is literally the same cell (IBKR is the smart-router venue that also routes CME-listed
      instruments). Same pre-existing classifier-keyword quirk noted on the `venue:cboe`/`venue:cme`/`venue:deribit`
      todos applies here too (`missing_pieces` relabeled `needs-registry-entry` instead of `needs-config` once a real
      reason populates the blunt keyword classifier) — not a new bug, not fixed here, same as those todos' own notes. No
      code changed this pass; this is a checkbox-only verification flip.
- [x] ✅ [SCRIPT] P2. **unlock ARBITRAGE_PRICE_DISPERSION --supports--> venue:ice** (distance 1, status partial) —
      missing: needs-config. Why blocked: (no reason recorded). (auto-emitted by generate_capability_unlock_report.py) —
      unified-api-contracts@c92cf034: the "(no reason recorded)" text was stale — the committed
      `capability-manifest.json` already carried a real reason ("Cross-product routing policy not declared in UAC (gap
      #10)."), which was itself FALSE: `unified_api_contracts/internal/architecture_v2/cross_venue_routing_policy.py`
      already declares `cme_wti_ice_brent_spread` (CROSS_VENUE_ROUTING_POLICIES), closing the UAC-declaration half of
      gap #10 since 2026-05-08. The manifest cell (`archetype_capability_manifest.json`, TRADFI/dated_future,
      venue_ids=[cme, ice]) just never got updated to reflect that. Grepped execution-service + strategy-service for any
      consumer of `CROSS_VENUE_ROUTING_POLICIES`/`CrossVenueRoutingPolicy`/`policies_for_venue_pair` — 0 hits, so the
      capability is still genuinely not end-to-end usable (kept status PARTIAL, not flipped to SUPPORTED). Corrected the
      cell's `notes` to name the real remaining gap (execution-service/strategy-service router integration, not UAC
      declaration) and propagated the fix through the committed derived artifacts (`capability-manifest.json`,
      `capability-unlock-report.json`, `prospectus/ARBITRAGE_PRICE_DISPERSION.md`) — hand-patched rather than
      full-regenerated, since a from-scratch regen in this slot picked up unrelated environment noise (missing
      sibling-service `.venv`s skewing unrelated edges/leg-venue lists); verified the 3-edge diff (`supports→venue:ice`,
      `supports→venue:cme`, `trades_instrument→instrument_type:dated_future`, all sourced from the same cell) was the
      only change via `git diff`. QG green (sentinel `a86be26d`); `tests/unit/test_capability_unlock.py` (PM) +
      `tests/internal/unit/test_archetype_capability_manifest_parity.py` +
      `tests/unit/test_archetype_capability_may_23_coverage.py` (UAC) all pass. Follow-up (not in this task's scope):
      actually wiring `CROSS_VENUE_ROUTING_POLICIES` into `execution-service/execution_service/v2/router.py` is the real
      unlock for this cell — left as a future SCRIPT/BACKEND todo, not fabricated here.
- [x] ✅ [SCRIPT] P2. **RESOLVED 2026-07-30 (slot-16, capability_wizard_gap_discovery-024) — already fixed by the
      sibling `venue:cboe`/`venue:cme`/`venue:deribit`/`venue:ibkr`/`venue:ice` todos above, no new code needed.**
      **unlock ARBITRAGE_PRICE_DISPERSION --trades_instrument--> instrument_type:dated_future** (distance 1, status
      partial) — missing: needs-config. Why blocked: Cross-product routing policy not declared in UAC (gap #10)..
      (auto-emitted by generate_capability_unlock_report.py) — Verified directly against
      `unified-api-contracts@c92cf034` ("fix(architecture-v2): correct stale gap#10 notes on ARBITRAGE_PRICE_DISPERSION
      CME/ICE cell", already HEAD == `origin/live-defi-rollout`, 0 ahead/0 behind): that commit's own diff shows all
      THREE edges sourced from the single `(TRADFI, dated_future)` cell were corrected together — `supports→venue:ice`,
      `supports→venue:cme`, and THIS todo's `trades_instrument→instrument_type:dated_future` — across every derived
      artifact (`unified_api_contracts/internal/architecture_v2/archetype_capability_manifest.json` source cell,
      `openapi/capability-manifest.json`, `openapi/capability-unlock-report.json`, and
      `openapi/prospectus/ARBITRAGE_PRICE_DISPERSION.md`'s TRADFI/dated_future row). Confirmed via `git show c92cf034`:
      the `trades_instrument→instrument_type:dated_future` edge in `capability-unlock-report.json` now carries
      `reason="Cross-venue routing policy IS declared in UAC (cross_venue_routing_policy.py: cme_wti_ice_brent_spread, gap #10 registry closed) but execution-service/strategy-service do not yet consume CROSS_VENUE_ROUTING_POLICIES — routing policy not wired into the SOR."`
      (status stays `partial`, correctly — the UAC-declaration half of gap #10 is closed but the SOR-wiring half is a
      real, still-open gap, same classifier-keyword quirk noted on the sibling todos, not fixed here). This checkbox was
      simply never flipped when the shared root-cause fix landed (the fixing todo's own scope note said it left the
      sibling checkboxes un-flipped). No code changed this pass; checkbox-only verification flip.
- [x] ✅ [SCRIPT] P2. **FIXED 2026-07-30 (slot-13, capability_wizard_gap_discovery-025) — stale cell reason corrected;
      edge correctly stays `partial`.** **unlock ARBITRAGE_PRICE_DISPERSION --trades_instrument--> instrument_type:lp**
      (distance 1, status partial) — missing: needs-registry-entry. Why blocked: Flash-loan receiver per-chain registry
      missing from UAC (gap #3).. (auto-emitted by generate_capability_unlock_report.py) —
      **unified-api-contracts@f8d266ab** (shipped earlier in this same task, already on `origin/live-defi-rollout`):
      UAC's `FlashLoanReceiverRegistry` (gap #3, `unified_api_contracts/internal/architecture_v2/flash_loan_receiver.py`
      — `FLASH_LOAN_RECEIVER_REGISTRY`) already exists with 10 real per-(chain, protocol) entries including an Arbitrum
      Uniswap V3 flash-swap row — the UAC-declaration half of gap #3 was already closed, so the cell's "registry
      missing" reason was stale/wrong. The real remaining gap is execution-wiring, not registry absence — independently
      re-verified every factual claim against current code before flipping: grepped execution-service directly and
      confirmed only `execution_service/defi_execution/orchestrators/recursive_loop_orchestrator.py` (a DIFFERENT
      archetype, `kind=recursive_leverage`) calls `flash_loan_receiver_for()` (2 call sites, both non-test); the live
      AAVE connector (`defi_execution/protocols/aave.py`/`aave_live.py`) resolves receivers only via config override or
      the testnet-only `TestnetContractRegistry`, never the UAC registry; and `engine/handlers/flash_loan_handler.py`
      (the paper/backtest simulator) has ZERO `receiver_address`/`receiver_kind` references — no receiver-address
      concept at all. Status correctly stays `partial` (registry now exists, but no live flash-loan-arb execution path
      consumes it) — the commit corrected the (DEFI, lp) cell's `notes` in the source
      `archetype_capability_manifest.json` and propagated the fix through the derived `capability-manifest.json`,
      `capability-unlock-report.json`, and the `ARBITRAGE_PRICE_DISPERSION` prospectus to name the real remaining gap
      (execution-wiring) instead of the closed one (registry declaration). No further code change needed this pass —
      checkbox flip only.
- [x] ✅ [SCRIPT] P2. **unlock ARBITRAGE_PRICE_DISPERSION --trades_instrument--> instrument_type:option** (distance 1,
      status partial) — missing: needs-leg-spec. Why blocked: vol_arb not a separate capability; multi-leg vol-arb algo
      pending.. (auto-emitted by generate_capability_unlock_report.py) — Verified accurate + current, not stale (unlike
      several sibling todos above): `ArbitragePriceDispersionEngine`
      (`strategy_service/engine/strategies/v2/arbitrage_structural/price_dispersion.py`), the SOLE
      `ARCHETYPE_ENGINE_REGISTRY`-mapped engine for this archetype (`factory.py:76`), exhaustively dispatches on
      `dispersion_type ∈ {price-dispersion, funding-rate-dispersion, cross-venue-prediction-dispersion}`
      (`_KNOWN_DISPERSION_TYPES`) — no vol/IV-dispersion branch exists for trading the same option at different IVs
      across Deribit vs OKX. Confirmed no CEFI options slot config for this archetype in `archetype_slots_cefi.py` (only
      spot/perp/funding-rate-disp slots). `vol_trading/dispersion.py` exists but solves a DIFFERENT problem
      (index-vs-component correlation dispersion, `VOL_TRADING` family, not reusable here — the codex archetype for that
      space, `VOL_ARB_RV_IV`, is itself still `implementation_status: design`). Cross-checked execution-service:
      `execution_service/engine/multi_leg_orchestrator.py` already provides generic multi-leg
      routing/compensation/unwind (used today by this archetype's OWN price-dispersion and funding-rate-dispersion paths
      via `AtomicInstruction`/`LEADER_HEDGE`) — so the gap is specifically the STRATEGY-layer dispatch branch +
      options-IV-computation/leg-construction logic, not a missing execution-side capability. Status correctly stays
      `partial` (not fabricated to `supported`). No code change this pass (matches the sibling `-024` precedent) —
      building the actual multi-leg vol-arb dispatch branch is real strategy-engineering design work (IV surface
      comparison methodology, strike/expiry matching, margin/greeks treatment), not a scriptable manifest fix; it stays
      recorded here as the durable, structured artifact for that gap rather than a fabricated new todo (CLAUDE.md
      dispatch-scope-eligibility: an open-ended design call isn't AO-eligible without a design decision first).
- [x] ✅ [SCRIPT] P2. **FIXED 2026-07-30 (slot-13, capability_wizard_gap_discovery-027) — stale cell note corrected;
      edge correctly stays `partial`.** **unlock CARRY_BASIS_DATED --supports--> venue:cme** (distance 1, status
      partial) — missing: needs-config. Why blocked: (no reason recorded). (auto-emitted by
      generate_capability_unlock_report.py) — **unified-api-contracts@f8515eb7**: the (TRADFI, dated_future) cell's
      `notes` claimed "IBKR ↔ CME cross-venue routing policy not declared (UAC gap #10)" — false. UAC's
      `CROSS_VENUE_ROUTING_POLICIES` (`unified_api_contracts/internal/architecture_v2/cross_venue_routing_policy.py`)
      already declares three IBKR↔CME policies (`ibkr_spy_cme_es_basis`, `ibkr_qqq_cme_nq_basis`,
      `ibkr_iwm_cme_rty_basis`) — the UAC-declaration half of gap #10 IS closed for the CME leg. Independently
      re-verified: grepped `execution-service` + `strategy-service` for `CROSS_VENUE_ROUTING_POLICIES` /
      `cross_venue_routing_policy` / `routing_policy_for` / `policies_for_venue_pair` — **zero call sites** in either
      repo, despite the UAC module's own `CONSUMER_CALL_SITES` metadata claiming four (execution-service `v2/router.py`,
      `algo_library/sor_cross_chain.py`, `algo_library/sor_twap.py`; strategy-service `portfolio_allocator/service.py`)
      — none of those actually import it. So the real remaining gap is SOR-wiring, not registry absence. Status
      correctly stays `partial` (not fabricated to `supported`) — corrected the note in the source
      `archetype_capability_manifest.json` cell and propagated through `capability-manifest.json`,
      `capability-unlock-report.json`, and the `CARRY_BASIS_DATED` prospectus to name the real gap. **Also confirmed the
      sibling `venue:ice` edge (below) has a genuinely DIFFERENT, still fully-open gap** — no IBKR↔ICE routing policy
      exists at all (`policies_for_venue_pair('ibkr','ice')` returns empty; only `cme_wti_ice_brent_spread` pairs
      CME↔ICE, both future legs, not usable for the IBKR spot leg) — so the corrected note distinguishes the
      closed-registry/open-SOR-wiring state (CME/IBKR legs) from the still-open-registry state (ICE leg). No further
      code change needed this pass — checkbox flip + note correction only.
- [x] ✅ [SCRIPT] P2. **FIXED 2026-07-30 (slot-14, capability_wizard_gap_discovery-028) — stale cell note already
      corrected by the sibling CME fix; edge correctly stays `partial`.** **unlock CARRY_BASIS_DATED --supports-->
      venue:ibkr** (distance 1, status partial) — missing: needs-config. Why blocked: (no reason recorded).
      (auto-emitted by generate_capability_unlock_report.py) — **unified-api-contracts@f8515eb7** (already shipped, on
      `origin/live-defi-rollout`): that single-cell fix (source `archetype_capability_manifest.json` cell) propagated to
      ALL THREE derived edges (`venue:cme`, `venue:ibkr`, `venue:ice`) simultaneously — confirmed via
      `git show f8515eb7 -- openapi/capability-unlock-report.json`, whose diff shows the same corrected `reason`
      string landing on all three `to_node_id` blocks in one commit. Independently re-verified both halves for the
      `ibkr` edge specifically (not just trusted the sibling's claim): (1) UAC's `CROSS_VENUE_ROUTING_POLICIES`
      (`unified_api_contracts/internal/architecture_v2/cross_venue_routing_policy.py`) declares four IBKR-leg policies
      with `leg_venues=("ibkr","cme")` (`ibkr_spy_cme_es_basis`, `ibkr_qqq_cme_nq_basis`, `ibkr_iwm_cme_rty_basis`,
      `ibkr_spy_option_cme_es_hedge`) — the UAC-declaration half of gap #10 IS closed for IBKR↔CME; (2) grepped
      execution-service (`v2/router.py`, `algo_library/sor_cross_chain.py`, `algo_library/sor_twap.py`) and
      strategy-service (`portfolio_allocator/service.py`) for `CROSS_VENUE_ROUTING_POLICIES` /
      `cross_venue_routing_policy` / `routing_policy_for` / `policies_for_venue_pair` — **zero call sites in either
      repo**, matching the CME sibling's finding despite the module's own `CONSUMER_CALL_SITES` metadata claiming four.
      So the real remaining gap for this edge is SOR-wiring (routing policy declared but not consumed), not registry
      absence. Status correctly stays `partial` (not fabricated to `supported`). No further code change needed this pass
      — checkbox flip only (the note correction already shipped bundled with the CME fix).
- [x] ✅ [SCRIPT] P2. **CONFIRMED 2026-07-30 (slot-13, capability_wizard_gap_discovery-029) — note already correct; edge
      correctly stays `partial`.** **unlock CARRY_BASIS_DATED --supports--> venue:ice** (distance 1, status partial) —
      missing: needs-config. Why blocked: (no reason recorded). (auto-emitted by generate_capability_unlock_report.py) —
      the cell's `notes` (corrected already, bundled into the sibling CME fix `unified-api-contracts@f8515eb7`) claims
      "IBKR ↔ ICE has no declared policy yet (gap #10 registry still open for that leg)" — independently re-verified
      this specific claim rather than trusting the sibling's note: ran `policies_for_venue_pair('ibkr','ice')` directly
      against the live `CROSS_VENUE_ROUTING_POLICIES` registry
      (`unified_api_contracts/internal/architecture_v2/cross_venue_routing_policy.py`) — returns an empty tuple, vs. 4
      for `('ibkr','cme')`. Read the registry source to confirm WHY: the only entry touching ICE at all is
      `cme_wti_ice_brent_spread` (`leg_venues=("cme","ice")`, both legs `FUTURE_LEG` — a CME-WTI-vs-ICE-Brent commodity
      spread), which cannot serve `CARRY_BASIS_DATED`'s `CARRY_BASIS_DATED@ibkr-ice-brent-fixed-feb26-usd-prod` slot (an
      IBKR SPOT leg vs. an ICE dated future) — no `leg_roles` combination matches, and no `("ibkr","ice")` pair exists
      in the registry at all. So this edge's gap is a genuine registry absence (no UAC declaration to wire up), unlike
      the sibling CME/IBKR edges (already-declared policy, just unconsumed by the SOR) — status correctly stays
      `partial`, not fabricated to `supported`. No code change this pass (the note was already corrected in `f8515eb7`);
      checkbox flip + independent verification only.

### 2026-06-13 — Wave-2 #9 follow-on (wizard sessions as reproducible artifacts)

Wave-2 #9 shipped the session-artifact schema (`e2e-testing/scripts/strategy/wizard_session.py` — `WizardSession`) + the
nightly-replay reconciler (`replay_wizard_sessions.py`, smoke `test_wizard_session_smoke.py`). The reconciler
re-evaluates each saved session's archetype edge-availability claims against the FRESH committed manifest and ALERTS on
a silent `available`↔`blocked` flip (reuses the Wave-2 #5 edge-status-hash diff). Remaining thin follow-on:

- [x] ✅ [UI] P2. **DONE 2026-07-30 (slot-9)** — **uts-ui "save session" surface** (target repo:
      `unified-trading-system-ui`) — wire the live wizard to WRITE the `WizardSession` JSON (answers + manifest_commit +
      manifest_edge_hash + config + prospectus_hash) at sign-off, into the sessions dir the nightly
      `replay_wizard_sessions.py --sessions-dir` reads. The Python schema + deterministic serialisation
      (`WizardSession.to_json`) is the contract to mirror; the StrategyConfigArtifact (`lib/wizard/output.ts`) is the
      config payload. Doubles as the client-onboarding compliance record. — `unified-trading-system-ui@bdb4a72e`.
      `POST /api/wizard/save-session` computes `manifest_commit` / `recorded_claims` / `manifest_edge_hash` server-side
      from the bundled capability manifest (never trusts a client-cached snapshot) and persists via a pluggable store
      (`lib/wizard/session-store.ts`, mirrors `lib/onboarding/doc-store.ts`'s local-disk/GCS dispatch pattern) — local
      disk under `.local-dev-cache/wizard-sessions/` in dev/mock (the literal directory `--sessions-dir` reads),
      `gs://odum-${env}- wizard-sessions/` in staging/prod. `lib/wizard/session.ts` mirrors `wizard_session.py`'s
      `edge_key`/ `archetype_claim_statuses`/canonical-JSON hashing exactly (verified byte-for-byte: a session saved by
      the route replays through the REAL `replay_wizard_sessions.py` with `edge_hash_match: true`). Found + fixed in the
      same commit: `WizardSession.archetype_id` (Python) reads `config["archetype_id"]`, a `ScenarioConfigRef`-era key
      the actual `StrategyConfigArtifact` never carries (it uses `archetype`) — every session this route would otherwise
      write raised `KeyError` in the nightly reconciler. Fixed by aliasing `archetype_id` onto the persisted `config`
      copy only (the live `StrategyConfigArtifact` TS contract used by download/copy/portfolio is untouched). Also
      allowlisted `/api/wizard/` in `lib/api/mock-handler.ts`'s real-route passthrough (the global mock-fetch
      interceptor was silently swallowing the POST with a fake `{}` 200 otherwise, matching the same class of gap the
      onboarding/questionnaire/strategy-evaluation routes needed). "Save session" button added to `ConfigOutput.tsx`
      (Stage J_REVIEW). 36 new Vitest unit tests (`tests/unit/wizard/session.test.ts`) + full existing wizard suite (267
      tests) green. **pw:L2 ✓** | regression: `tests/smoke/wizard-save-session.spec.ts` (drives the wizard to sign-off,
      clicks Save session, asserts the real POST response + "Session saved!" state — not mocked). tsc/ESLint clean; full
      `quality-gates.sh` green (sentinel=2319b519, amended to bdb4a72e by quickmerge's trailer).

### 2026-06-13 — Under-registration audit ("what can the system do that the registry doesn't capture", common-sense pass)

Census of the committed manifest node-kinds vs code/codex reality surfaced these (full detail = F49–F53 in the findings
doc):

- [x] ✅ [SPEC] P1. **Custody/signing-surface dimension (F49)** — UAC `SigningSurface` enum
      (CLOUD_KMS_ENCRYPTED/COPPER_MPC/ CEFFU/FIREBLOCKS_MPC) is real + config-relevant but ZERO manifest custody nodes +
      no wizard custody stage. Add a custody/signing-surface registry + emit real `custody_provider` nodes + a wizard
      stage. Targets: unified-api-contracts (registry) + unified-trading-pm (exporter node-kinds) +
      unified-trading-system-ui (Stage). Also fix the `custody_provider` node-kind dumping-ground
      (risk_layer/kill_switch/gap_registry get their own kinds). — **DONE end-to-end (Waves A/B/C 2026-06-14)**:
      UAC@7020b0c5 `custody_surfaces.OFFERED_SIGNING_SURFACES` registry + 5 new `CapabilityNodeKind` members;
      PM@3f4a1ee92 exporter re-kind (`custody_provider` 0 catch-all; real `signing_surface` nodes 3 + `signs_for:<ag>`
      edges); uts-ui@3c98036587 custody/signing-surface wizard stage in Stage I (CLOUD_KMS default / COPPER selectable /
      FIREBLOCKS greyed → `StrategyConfigArtifact.capital.signingSurface` + onboarding checklist; pw:L2 ✓ | regression:
      tests/smoke/wizard-custody.spec.ts); dep-ui@0db05b7 NodeKind types + count assertions.
- [x] ✅ [SCRIPT] P2. **fund_structure nodes (F50)** — exporter walks OFFERED_FUND_STRUCTURES (POOLED/SMA, already
      backfilled) into per-structure `CapabilityNodeKind.FUND_STRUCTURE` nodes/edges (today 0 nodes). Target:
      unified-trading-pm (`scripts/openapi/_capability_gaps.py`). — **DONE PM@3f4a1ee92 (Wave B)**: 2 `fund_structure`
      nodes (pooled + sma) emitted from `OFFERED_FUND_STRUCTURES` with share-class/cadence metadata +
      `offers_share_class` edges; UAC@e63a51156 / uts-ui@3c98036587 / dep-ui@0db05b7 NodeKind types.
- [x] ✅ [SCRIPT] P2. **Chain node dedup (F51)** — normalize the 35 numeric chain-id + 6 named chain nodes to one
      canonical node per chain (CHAIN_RPC_TEMPLATES is SSOT). Target: unified-trading-pm
      (`scripts/openapi/_capability_extract.py`). — **DONE PM@3f4a1ee92 (Wave B)**: chain nodes deduped 41→35
      (`MAINNET_CHAIN_IDS` name↔id SSOT; human name canonical, numeric chain_id in metadata; numeric-only nodes remain
      only for un-named chains/testnets).
- [x] ✅ [SCRIPT] P3. **data_source service-vs-vendor split (F52)** — exclude internal services (execution/instruments/
      features_onchain) from `data_source` nodes or give them a distinct kind. Target: unified-trading-pm exporter. —
      **DONE PM@3f4a1ee92 (Wave B)**: `data_source` nodes 28→24 — internal producers (execution/instruments/
      features_onchain/strategy service) excluded; real vendors retained.
- [x] ✅ [SCRIPT] P2. **ML model registry surfacing (F53)** — walk the ml-service model registry (per-archetype model
      variants) into `ml_model` nodes + archetype→model edges (today only `variant_config`). Targets: unified-trading-pm
      exporter (per-service venv import) + ml-service (a queryable model registry). — **DONE (model-TYPE half)
      PM@3f4a1ee92 (Wave B)**: `ml_model` nodes 1→8 from the ml-service `VALID_MODEL_TYPES` registry via per-service
      venv probe (each carries `VALID_TARGET_TYPES` + `ModelVariantConfig`). **RESIDUAL** = per-archetype
      archetype→model edges still need an ml-service queryable variant registry — tracked as the open P2 below
      (ml-service owner).

## Wave B SHIPPED 2026-06-14 — exporter re-kind + dedup (F49–F53)

The PM capability exporter side of F49–F53 is DONE (this Wave-B unit; collision-boundary = PM `scripts/**` + UAC
`openapi/**` regenerated outputs). Manifest regenerated with the UAC venv (deterministic — two runs byte-identical):

- **F49 (exporter) — FIXED.** `custody_provider` is no longer a catch-all (0 nodes): `risk_layer:*` → `RISK_GATE_LAYER`
  (4), `kill_switch:*` → `KILL_SWITCH_REASON` (8), `gap_registry:*`/`service_registry:*` → `GAP_REGISTRY` (7),
  `collateral:*` → `COLLATERAL_POLICY` (9). Real `signing_surface` nodes (3) now emitted from
  `custody_surfaces.OFFERED_SIGNING_SURFACES` (Wave A) with status/asset-group/source metadata + `signs_for:<ag>` edges.
  (`_capability_gaps.py`)
- **F50 — FIXED.** `fund_structure` nodes (2: pooled + sma) emitted from `OFFERED_FUND_STRUCTURES` with
  share-class/cadence metadata + `offers_share_class` edges. (`_capability_gaps.py`)
- **F51 — FIXED.** Chain nodes deduped 41→35 (no numeric-id + name duplicate for the same chain; `MAINNET_CHAIN_IDS` is
  the name↔id SSOT, human name is the canonical id, numeric chain_id in metadata; numeric-only nodes remain ONLY for
  chains with no registered name, e.g. testnets). (`_capability_extract.py`)
- **F52 — FIXED.** `data_source` nodes 28→24 — internal service producers (execution_service / instruments_service /
  features_onchain_service / strategy_service) excluded; real vendors retained. (`_capability_extract.py`)
- **F53 — FIXED (exporter).** `ml_model` nodes 1→8 — exporter now walks the ml-service `VALID_MODEL_TYPES` registry
  (lightgbm/xgboost/catboost/random_forest/huber/poisson_glm/ridge/ensemble) via the per-service venv probe; each node
  carries the `VALID_TARGET_TYPES` + `ModelVariantConfig` fields. NOTE: `VALID_MODEL_TYPES` is a flat model-TYPE
  registry, not a per-archetype model-VARIANT registry — the per-archetype archetype→model edge derivation still needs
  an ml-service queryable variant registry (residual P2 below). (`_capability_gaps.py`)

Regression note: the Wave-2 #5 capability-regression gate PASSED with NO `--update-baseline` — the re-kinding/dedup
renamed/removed nodes but kept every genuine capability AVAILABLE, so no `available→not_available` edge regression
fired.

### Residual (still open after Wave B)

- [x] ✅ [SPEC] P2. **ml-service per-archetype model-variant registry (F53 residual)** — ml-service exposes only flat
      `VALID_MODEL_TYPES`/`VALID_TARGET_TYPES` (no per-archetype model-variant enumeration); the manifest therefore
      emits `ml_model` nodes per model type but cannot yet emit archetype→model edges. Add a queryable per-archetype
      model-variant registry to ml-service so the exporter can derive `uses_model` edges. Target: ml-service. — **DONE
      end-to-end 2026-06-14**: ml-service@7ee05d6 new `model_variant_registry.py` — a queryable per-(asset_group,
      target_type) trainable-variant registry, **SSOT-derived, zero invented mapping**: sports from
      `SportsMLPresets.model_families()` (target_names + family-pinned algorithms), defi from `DEFI_TARGET_BUILDERS`
      keys, cefi/tradfi from the technical target subset of `VALID_TARGET_TYPES` (model_type = grid-eligible per
      fixed-grid-config) — 37 variants, exhaustiveness-asserted vs `VALID_TARGET_TYPES`, 10 tests. PM@c86135ce (PR #326)
      exporter probes the registry + emits **archetype→ml_model `uses_model` edges** by joining each archetype's real
      asset groups (`ARCHETYPE_CAPABILITY_REGISTRY` non-blocked cells) to the asset-group's variants — **167 edges (138
      available / 29 partial) across the 22 ML-driven archetypes, 0 dangling**; reason carries the contributing
      asset_groups + targets. Same fix reconnected the pre-existing **912 dangling `uses_algo` edges** (they referenced
      an `archetype:` prefix the nodes never had). Manifest regenerated **574 nodes / 2497 edges** (deterministic
      byte-identical; #5 capability-regression gate PASS, no `--update-baseline`); UAC@bccad6e. Re-bundled
      byte-identical into uts-ui@3c414001 (parity 27/27, `.husky` >1MB allowlist) + dep-ui@c1ba2aa (pw 9/9).
      **SUPERSEDED by the signal-grounded refinement (operator "do this", 2026-06-14)** — the asset_group blanket join
      was tightened to a per-signal join: UAC@c1ac124 `ml_signal_targets.SIGNAL_VARIANT_ML_TARGETS` (operator-authored
      signal→target map, every archetype `signal_variant` classified predictive-or-deterministic, exhaustiveness test) +
      ml-service@2c07a72 `model_types_for_target`/`asset_groups_for_target` + PM@PR#328 exporter
      `_archetype_model_edges` now joins each archetype's REAL per-cell `signal_variants` → ML targets → models
      (domain-gated). **167→103 edges (82 available / 21 partial, 14 archetypes)**: pure-carry archetypes
      (basis/staking_yield-only) now correctly get ZERO edges; a funding-predicting carry keeps only its funding_rate
      model edges. Manifest 574/**2433**; re-bundled byte-identical uts-ui@c5dc251c (243 vitest) + dep-ui@99a5f51 (pw
      9/9); #5 regression gate PASS. No open residual remains.
- [x] ✅ [UI] P1. **Custody/signing-surface wizard stage (F49 residual)** — manifest now carries `signing_surface`
      nodes; the wizard still needs a custody stage that constrains wallets/venues by signing surface. Target:
      unified-trading-system-ui (Wave C). — **DONE uts-ui@3c98036587 (Wave C)**: custody/signing-surface field added to
      Stage I (Capital & Structure) reading manifest `signing_surface` nodes — CLOUD_KMS_ENCRYPTED (default,
      active_may23) / COPPER_MPC (active_june1, selectable) / FIREBLOCKS_MPC (out_of_scope, greyed); choice flows into
      `StrategyConfigArtifact.capital.signingSurface` + onboarding checklist. Tests: custody-signing.test.ts + pw:L2 ✓
      tests/smoke/wizard-custody.spec.ts (13 passed). dep-ui@0db05b7 capability-tab counts re-synced.

## Progress Log

- **context-scout 2026-08-01**: populated/refreshed context_scope (3 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries, unchanged) — verified all still accurate and
  resolve; the doc carries zero open `- [ ]` items (a fully-resolved running gap-pool, kept `status: open` by design per
  its own stated purpose), so the sibling findings doc + parent plan + source registries remain the right set.
- **context-scout 2026-08-05**: re-scouted; fixed a broken `context_scope` path (`unified-trading-pm/scripts/openapi`
  never resolves — same-repo paths are plain repo-relative; corrected to `scripts/openapi`), now 5 entries.
