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
parent_epic: strategy_master
priority: P2
source: [gaps surfaced by capability wizard/manifest work 2026-06-11]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-27
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
      batch-live asymmetries" flipped `gap`→`registry` (`unified-trading-pm@6586b8a2e`); `capability-wizard.md`'s status
      table already correctly cited `5e7d0685` for sim-assumptions (no fix needed there). No design work remaining.
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
      `tests/unit/test_capability_manifest.py::     test_offered_fund_structures_backfilled` (asserts
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
- [ ] [SPEC] P2. **Trading-agent/LLM capability**: no declaration linking trading-agent-service to archetypes (which
      strategies permit agent-driven instructions over features, which models are allowed).

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

- [ ] [UI] P2. **Surface the per-edge `readiness` badge in the capability wizard** — `unified-trading-system-ui`. Read
      `lib/registry/capability-manifest.json` `edges[].readiness` + the synced `capability-readiness-report.json`;
      render a maturity chip per archetype/edge (backtest-only=grey, shadow-observed=amber, staging-proven=blue,
      live-proven=green) next to the existing availability tick, with the cited evidence
      (`live_cluster_registry:<name>`) in the tooltip. Thin follow-on to the exporter work above (Wave-2 #2). Needs
      `[UI]` + `pw:L2 ✓` + a regression spec per the playwright gate before ticking.

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

- [ ] [AGENT] P2. **gap_registry:order_semantics** — Venue order semantics registry is honest-empty — per-adapter
      order-semantics honor matrix code-scan. Target repo: `execution-service`. Cold-start context:
      VENUE_ORDER_SEMANTICS backfill: scan each venue execution adapter for TIF (FOK/IOC/post-only), make/take,
      ref-pricing mode, multi-leg delta ownership; populate
      unified_api_contracts/internal/architecture_v2/order_semantics.py VENUE_ORDER_SEMANTICS. (auto-emitted by
      emit_capability_gap_todos.py)

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
- [ ] [IMPLEMENT] P1. CeFi margin emission: margin_event_emitter.py is DeFi-only (hardcodes venue_type="defi"); UTL
      margin models for HL/Bybit/OKX/Binance exist but nothing feeds them live balances. strategy-service PBM owns.
      **STRATEGY-SERVICE ENGINE under LOGIC FREEZE (2026-06-13)** — this feeds live per-venue balances into the UTL
      margin models + flips margin_event_emitter off its hardcoded `venue_type="defi"`; both are engine-runtime changes,
      NOT surface-only, so they require the freeze to lift / a dedicated PBM dispatch. The UAC surface above
      (transfer_purpose + COLLATERAL_POSTED/MARGIN_RELEASED) is the contract these will emit against once unfrozen.
- [ ] [IMPLEMENT] P2. margin_health API is a Phase-1 stub returning []; no CeFi per-venue margin balance tracker
      (venue_balance_tracker.py is sports-only). strategy-service. **LOGIC FREEZE — engine-runtime, deferred to PBM
      dispatch** (the API surface exists; the real CeFi balance tracker is engine work).
- [ ] [IMPLEMENT] P2. Runtime consumer for the UAC collateral registry: haircut-adjusted posted-collateral value feeding
      MarginHealthSnapshot.collateral_usd (also resolves the F28 dual-SSOT risk). UTL/strategy-service. **LOGIC FREEZE —
      engine-runtime consumer; the UAC COLLATERAL_REGISTRY it would read is now backfilled (2026-06-12), so this is
      unblocked on the data side and waits only on the strategy-service/UTL runtime change.**
- [ ] [UI] P2. uts-ui Stage-A jurisdiction-filter surface is the follow-on consumer of the UAC jurisdiction overlay
      registry (`unified_api_contracts.internal.architecture_v2.jurisdiction_overlay` — `Jurisdiction` /
      `JURISDICTION_VENUE_POLICIES` / `allowed_venues_for_jurisdiction` / `is_venue_allowed`, backfilled 2026-06-13):
      the wizard reads the investor entity's jurisdiction and filters the venue/instrument picklist so a config can
      never include a venue the jurisdiction cannot legally touch (conservative default = blocked + needs_legal_review).
      UI repo; registry layer is done — this is the thin Stage-A filter surface only.

## Closest-to-unlock roadmap (auto-emitted)

_Auto-emitted by `scripts/openapi/generate_capability_unlock_report.py --emit-todos`._ _The N blocked edges closest to
available (lowest `unlock_distance`) — the_ _highest-leverage roadmap items. Dedup-idempotent on re-run._

- [ ] [SCRIPT] P2. **unlock ARBITRAGE_MEV_SANDWICH --has_leg:legs--> ARBITRAGE_MEV_SANDWICH** (distance 1, status
      not_registered) — missing: needs-leg-spec. Why blocked: ARBITRAGE_MEV_SANDWICH has no leg structure in
      ARCHETYPE_LEG_STRUCTURES yet — structural per-leg restrictions not modelled (F22 leg-truth gap). (auto-emitted by
      generate_capability_unlock_report.py)
- [ ] [SCRIPT] P2. **unlock ARBITRAGE_PRICE_DISPERSION --supports--> venue:cboe** (distance 1, status partial) —
      missing: needs-config. Why blocked: (no reason recorded). (auto-emitted by generate_capability_unlock_report.py)
- [ ] [SCRIPT] P2. **unlock ARBITRAGE_PRICE_DISPERSION --supports--> venue:cme** (distance 1, status partial) — missing:
      needs-config. Why blocked: (no reason recorded). (auto-emitted by generate_capability_unlock_report.py)
- [ ] [SCRIPT] P2. **unlock ARBITRAGE_PRICE_DISPERSION --supports--> venue:deribit** (distance 1, status partial) —
      missing: needs-config. Why blocked: (no reason recorded). (auto-emitted by generate_capability_unlock_report.py)
- [ ] [SCRIPT] P2. **unlock ARBITRAGE_PRICE_DISPERSION --supports--> venue:ibkr** (distance 1, status partial) —
      missing: needs-config. Why blocked: (no reason recorded). (auto-emitted by generate_capability_unlock_report.py)
- [ ] [SCRIPT] P2. **unlock ARBITRAGE_PRICE_DISPERSION --supports--> venue:ice** (distance 1, status partial) — missing:
      needs-config. Why blocked: (no reason recorded). (auto-emitted by generate_capability_unlock_report.py)
- [ ] [SCRIPT] P2. **unlock ARBITRAGE_PRICE_DISPERSION --trades_instrument--> instrument_type:dated_future** (distance
      1, status partial) — missing: needs-config. Why blocked: Cross-product routing policy not declared in UAC (gap
      #10).. (auto-emitted by generate_capability_unlock_report.py)
- [ ] [SCRIPT] P2. **unlock ARBITRAGE_PRICE_DISPERSION --trades_instrument--> instrument_type:lp** (distance 1, status
      partial) — missing: needs-registry-entry. Why blocked: Flash-loan receiver per-chain registry missing from UAC
      (gap #3).. (auto-emitted by generate_capability_unlock_report.py)
- [ ] [SCRIPT] P2. **unlock ARBITRAGE_PRICE_DISPERSION --trades_instrument--> instrument_type:option** (distance 1,
      status partial) — missing: needs-leg-spec. Why blocked: vol_arb not a separate capability; multi-leg vol-arb algo
      pending.. (auto-emitted by generate_capability_unlock_report.py)
- [ ] [SCRIPT] P2. **unlock CARRY_BASIS_DATED --supports--> venue:cme** (distance 1, status partial) — missing:
      needs-config. Why blocked: (no reason recorded). (auto-emitted by generate_capability_unlock_report.py)
- [ ] [SCRIPT] P2. **unlock CARRY_BASIS_DATED --supports--> venue:ibkr** (distance 1, status partial) — missing:
      needs-config. Why blocked: (no reason recorded). (auto-emitted by generate_capability_unlock_report.py)
- [ ] [SCRIPT] P2. **unlock CARRY_BASIS_DATED --supports--> venue:ice** (distance 1, status partial) — missing:
      needs-config. Why blocked: (no reason recorded). (auto-emitted by generate_capability_unlock_report.py)

### 2026-06-13 — Wave-2 #9 follow-on (wizard sessions as reproducible artifacts)

Wave-2 #9 shipped the session-artifact schema (`e2e-testing/scripts/strategy/wizard_session.py` — `WizardSession`) + the
nightly-replay reconciler (`replay_wizard_sessions.py`, smoke `test_wizard_session_smoke.py`). The reconciler
re-evaluates each saved session's archetype edge-availability claims against the FRESH committed manifest and ALERTS on
a silent `available`↔`blocked` flip (reuses the Wave-2 #5 edge-status-hash diff). Remaining thin follow-on:

- [ ] [UI] P2. **uts-ui "save session" surface** (target repo: `unified-trading-system-ui`) — wire the live wizard to
      WRITE the `WizardSession` JSON (answers + manifest_commit + manifest_edge_hash + config + prospectus_hash) at
      sign-off, into the sessions dir the nightly `replay_wizard_sessions.py --sessions-dir` reads. The Python schema +
      deterministic serialisation (`WizardSession.to_json`) is the contract to mirror; the StrategyConfigArtifact
      (`lib/wizard/output.ts`) is the config payload. Doubles as the client-onboarding compliance record.

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
