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

- [ ] [SPEC] P1. **Custody/signing-surface dimension (F49)** — UAC `SigningSurface` enum
      (CLOUD_KMS_ENCRYPTED/COPPER_MPC/ CEFFU/FIREBLOCKS_MPC) is real + config-relevant but ZERO manifest custody nodes +
      no wizard custody stage. Add a custody/signing-surface registry + emit real `custody_provider` nodes + a wizard
      stage. Targets: unified-api-contracts (registry) + unified-trading-pm (exporter node-kinds) +
      unified-trading-system-ui (Stage). Also fix the `custody_provider` node-kind dumping-ground
      (risk_layer/kill_switch/gap_registry get their own kinds).
- [ ] [SCRIPT] P2. **fund_structure nodes (F50)** — exporter walks OFFERED_FUND_STRUCTURES (POOLED/SMA, already
      backfilled) into per-structure `CapabilityNodeKind.FUND_STRUCTURE` nodes/edges (today 0 nodes). Target:
      unified-trading-pm (`scripts/openapi/_capability_gaps.py`).
- [ ] [SCRIPT] P2. **Chain node dedup (F51)** — normalize the 35 numeric chain-id + 6 named chain nodes to one canonical
      node per chain (CHAIN_RPC_TEMPLATES is SSOT). Target: unified-trading-pm
      (`scripts/openapi/_capability_extract.py`).
- [ ] [SCRIPT] P3. **data_source service-vs-vendor split (F52)** — exclude internal services (execution/instruments/
      features_onchain) from `data_source` nodes or give them a distinct kind. Target: unified-trading-pm exporter.
- [ ] [SCRIPT] P2. **ML model registry surfacing (F53)** — walk the ml-service model registry (per-archetype model
      variants) into `ml_model` nodes + archetype→model edges (today only `variant_config`). Targets: unified-trading-pm
      exporter (per-service venv import) + ml-service (a queryable model registry).

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

- [ ] [SPEC] P2. **ml-service per-archetype model-variant registry (F53 residual)** — ml-service exposes only flat
      `VALID_MODEL_TYPES`/`VALID_TARGET_TYPES` (no per-archetype model-variant enumeration); the manifest therefore
      emits `ml_model` nodes per model type but cannot yet emit archetype→model edges. Add a queryable per-archetype
      model-variant registry to ml-service so the exporter can derive `uses_model` edges. Target: ml-service.
- [ ] [UI] P1. **Custody/signing-surface wizard stage (F49 residual)** — manifest now carries `signing_surface` nodes;
      the wizard still needs a custody stage that constrains wallets/venues by signing surface. Target:
      unified-trading-system-ui (Wave C).
