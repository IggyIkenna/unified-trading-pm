# Capability wizard — gap discovery tracker

**Purpose**: running pool of gaps surfaced by the capability wizard/manifest work (operator rule 2026-06-11: as much as
possible scripted; issues found get tests built around them; agents only when scripts cannot answer). Items here are
UNACKED scope — they graduate into todos on
[`capability_wizard_and_manifest_2026_06_11.md`](../capability_wizard_and_manifest_2026_06_11.md) or successor plans.

**Gap taxonomy**: `missing_registry` (no declarative source of truth) · `missing_extraction` (registry exists,
generators don't walk it) · `needs_code_scan` (answer only derivable by reading code → agent-orchestrator candidate) ·
`logical_dead_end` (correctly impossible — record so the wizard explains it, not a defect).

## Seeded 2026-06-11 (session audit)

### Generator-suite drift — `missing_extraction` (Phase 0 of the plan)

- [ ] [SCRIPT] P0. SERVICE_REGISTRY in `scripts/openapi/generate_unified_spec.py` lists 10+ phantom pre-consolidation
      services (8× `features-*-service`, `ml-inference/-training-service`, `pnl-attribution-service`,
      `position-balance-monitor-service`, `risk-and-exposure-service`) and misses `features-service`, `ml-service`,
      `fund-administration-service`, `greeks-service`.
- [ ] [SCRIPT] P0. `generate_ui_reference_data.py` never extracts `architecture_v2` (StrategyArchetype ×53,
      StrategyFamily ×9, ARCHETYPE_CAPABILITY_REGISTRY, AtomicExecutionMode, VenueCategoryV2, MarginMode,
      KillSwitchReason, VenueFeature, RiskGateLayer/Decision, CompensationPolicy, MevSubmissionMode, HoldPolicy,
      StakingMethod) — extraction walks package-root exports only.
- [ ] [SCRIPT] P0. `generate_config_registry.py` mirrors the phantom/missing service list.
- [ ] [SCRIPT] P1. `_validate_service_coverage()` warns instead of failing → suite rotted silently; committed outputs
      stale (May 22 – Jun 1 vs Jun 11).
- [ ] [SCRIPT] P1. Source-mode capability matrix (batch/live/replay × source × WS/REST) exists only as a manual audit
      doc (`source-mode-capability-matrix_2026-06-07.md`), not as registry + extraction.

### Missing registries — `missing_registry` (Phase 2 of the plan)

- [ ] [SPEC] P0. **Collateral**: accepted collateral per venue, haircut per collateral, max/liquidation LTV, maintenance
      vs liquidation margin, per-platform liquidation protocol, broker list. Currently derived from wallet structure
      (DeFi 20/80 treasury/hot, CeFi 0/100) — not declarative, not queryable.
- [ ] [SPEC] P1. **Fees**: exchange/gas/broker/clearing fees at venue/instrument-type/tier granularity.
- [ ] [SPEC] P1. **Simulation assumptions**: simulatable candle granularities, matching/fill assumptions per archetype
      area, backtest-live symmetry nuances per venue/instrument.
- [ ] [SPEC] P1. **Fund structures**: offerable pooled/SMA/prop structures with subscription/redemption + rebalance
      cadences (fund-administration state machines are runtime truth; nothing declares what is offerable).
- [ ] [SPEC] P1. **Order semantics per venue adapter**: TIF (FOK/IOC/post-only), make/take, ref-pricing modes (fixed vs
      delta-adjusted to underlying), multi-leg/spread delta-risk ownership, auth-wired status.
- [ ] [SPEC] P2. **Trading-agent/LLM capability**: no declaration linking trading-agent-service to archetypes (which
      strategies permit agent-driven instructions over features, which models are allowed).

### Open questions — `needs_code_scan` candidates (agent-orchestrator once Phase 5 wiring exists)

- [ ] [AGENT] P2. Options execution wiring depth: greeks-service computes; VOL family (18 archetypes) registered;
      whether execution-service options algos are wired end-to-end per venue is unverified.
- [ ] [AGENT] P1. Exposure normalization location: staked-ETH vs ETH equivalence / delta-adjusted exposure — not found
      as a declared model (greeks-service? features-service? ledger?); prospectus needs it.
- [ ] [AGENT] P2. SOR decision trees: smart-order-routing logic scattered across algo files; no single manifest of
      routing decisions for the wizard to describe.
- [ ] [AGENT] P1. Multi-leg execution: which algorithm manages inter-leg delta risk for basis/spread/option-combo
      instructions executed simultaneously.

## Discovered later (append below; date each entry; pin a test when fixed)

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

- [ ] [SPEC] P1. `TransferIntent`/`AllocationTarget` gain a `transfer_purpose` field (MARGIN_DEPOSIT etc.) + ledger
      EventType gains COLLATERAL_POSTED/MARGIN_RELEASED — today a USDC margin transfer to hyperliquid is
      indistinguishable from any other transfer. unified-api-contracts + execution-service + fund-administration.
- [ ] [IMPLEMENT] P1. CeFi margin emission: margin_event_emitter.py is DeFi-only (hardcodes venue_type="defi"); UTL
      margin models for HL/Bybit/OKX/Binance exist but nothing feeds them live balances. strategy-service PBM owns.
- [ ] [IMPLEMENT] P2. margin_health API is a Phase-1 stub returning []; no CeFi per-venue margin balance tracker
      (venue_balance_tracker.py is sports-only). strategy-service.
- [ ] [IMPLEMENT] P2. Runtime consumer for the UAC collateral registry: haircut-adjusted posted-collateral value feeding
      MarginHealthSnapshot.collateral_usd (also resolves the F28 dual-SSOT risk). UTL/strategy-service.
