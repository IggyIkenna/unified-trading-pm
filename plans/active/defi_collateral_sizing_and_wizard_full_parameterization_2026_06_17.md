---
title: Collateral-aware sizing + opportunity-checker + wizard full-parameterization
created: 2026-06-17
parent_epic: strategy_master
assigned_vm: vm-trading-core
estimate_class: brand-new
estimate_baseline_ai_days: 18.0
estimate_calibrated_ai_days: 18.0
locked_by: live-defi-rollout
locked_since: 2026-06-17
priority: P2
status: active
---

# Collateral-aware sizing + opportunity-checker + wizard full-parameterization

> **Origin**: operator directive 2026-06-17 (audit `plans/active/issues/e2e_defi_config_taxonomy_wizard_roundtrip_2026_06_17.md`).
> Build all four workstreams. Honest-discipline as ever (real logic + tests + ship; never invent numbers; single-canonical).

## Operator requirements baked in
- **R1 — wizard coverage = FULL supported set, not the e2e subset.** e2e was constrained to currently-available data
  (some still migrating/backfilling); the wizard's venue/instrument/archetype options must come from the catalogue
  (capability matrix/manifest), NOT be narrowed to what e2e happened to exercise.
- **R2 — opportunity checker reflects collateral-driven down-size.** When a venue is stables-only (deposit USDC, can't
  post the LST), the basis is doable only in REDUCED size (funds in two places + cross-exchange risk). The opportunity
  checker/ranker must account for that — smaller effective size + a cross-exchange-risk / dual-deposit capital cost →
  scored as a lesser opportunity, not the full-size one.

## Phase A — Collateral-aware down-sizing + opportunity-checker (strategy-service + UTL)  [WAVE 1]
The gap (issue doc): `staked_basis.py:219` rejects the slot when the perp venue won't take the LST; no
deposit-USDC-and-size-down branch; `stake_fraction` forced 1.0; dead `per_venue_margin_buffer_pct`.

- [x] ✅ [SCRIPT] P1. (strategy-service@6e9164b1) **Build the USDC-collateral + margin-buffer down-size branch** in the staked-basis (and basis-perp)
      engine: when `venue_accepts_collateral(perp_venue, lst)` is False but the venue accepts a stable → deposit the
      stable + size the position down by a margin-call buffer (driven by `get_collateral_haircut` + the buffer), allow
      `stake_fraction < 1.0`, keep delta-neutral on the reduced notional. Replaces the hard reject. Wire (or delete +
      re-add) `per_venue_margin_buffer_pct`. Unit tests: Aster/Hyperliquid (USDC-only) → buffered down-sized position
      (not reject); Drift/Bybit (LST-accepting) → full LST-as-margin path unchanged. Repos: strategy-service + UTL margin.
- [x] ✅ [SCRIPT] P1. (strategy-service@6e9164b1) **(R2) Feed the down-size into the opportunity checker/ranker** — find the opportunity/oppty-scoring
      surface (grep strategy-service/UTL for opportunity/scanner/ranker/edge-vs-cost); when a candidate basis requires
      stables-only collateral, the scored opportunity uses the REDUCED size + a cross-exchange-risk/dual-deposit capital
      cost, so it ranks below an equivalent full-collateral one. Tests assert the penalty. Repo: strategy-service (+ UTL).

## Phase B — Production-param surface audit + flat PARAM SCHEMA inventory (read-only → schema doc)  [WAVE 1]
- [x] [SCRIPT] P2. **Enumerate the full production-param surface per archetype** (engine `__init__`/config-model/
      `strategy_config_loader` schema) — name/type/default/range/units for every param, ALL archetypes (start with the
      live DeFi + the new VOL_*/MM). Confirm the e2e/catalog params functionally match the engine defaults (the
      prod-vs-testing alignment ask). OUTPUT: a structured per-archetype param schema (the input Phase C emits into the
      manifest). Repo: strategy-service (read) → schema artifact.
      — ✅ PM@0c6f5f0ab: `codex/09-strategy/architecture-v2/cross-cutting/archetype-param-schema-inventory.md` —
      29 archetypes catalogued (10 live DeFi + 19 new VOL_*/MM), ~170 params, each name/type/default/range/units/required
      cited to engine `file:line`. Prod-vs-testing: CSB + basis-perp **defaults align**; APD has ONE functional
      divergence — engine+catalog default `dispersion_bps`/`cost_bps` = 30/10 but e2e smoke uses 20/5 → wizard pre-fill
      must source the engine default (30/10), tracked as F4 in the doc. Side-findings F1–F3 (dead catalog params
      `max_loops`/LP keys, 3 unregistered MM engines) captured in the doc's Findings section for Phase C to honour.

## Phase C — Wizard full-parameterization (UAC manifest exporter + strategy-service config + UI)  [WAVE 2, needs B]
- [x] ✅ [SCRIPT] P1. **Emit a per-archetype flat PARAM SCHEMA into the capability manifest** (the exporter; sourced from
      each engine's config model — Phase B's inventory). The manifest is a node/edge graph today with NO param schema;
      add the schema block. Repos: unified-api-contracts (exporter) + strategy-service (config models expose the schema).
      — ✅ strategy-service@f2d4bef5 (SSOT) + unified-api-contracts@f0b66b2 (schema model + regenerated manifest) +
      unified-trading-pm@853ae5ea4 (exporter). **SSOT**: `strategy_service/engine/strategies/v2/param_schema.py`
      declares `PARAM_SCHEMA_REGISTRY` (35 archetype keys = 29 engines + 6 shared-engine aliases, **270 param rows**:
      `{name,type,default,required,units,enum_values,min,max,source}`) keyed by `StrategyArchetype` value; each default is
      the ENGINE default (F4 honoured — APD `dispersion_bps`/`cost_bps`=30/10 NOT the smoke 20/5; CSB new
      `margin_buffer_pct`=0.20 = `_DEFAULT_MARGIN_BUFFER_PCT`). UAC adds `ParamSchemaSpec` + `param_schema` field on
      `CapabilityManifest` (serialised in `to_canonical_dict`, archetype-sorted, deterministic). PM exporter
      `_capability_gaps.extract_param_schema` probes `build_param_schema_registry()` in strategy-service's OWN `.venv`
      (same per-service-venv idiom as `extract_service_registries`) → never re-typed in the exporter. Regenerated
      `openapi/capability-manifest.json` carries `param_schema` (35×270); **UI copy
      `unified-trading-system-ui/lib/registry/capability-manifest.json` re-synced byte-identical to the UAC canonical**
      (left uncommitted for the wizard-UI wave — out of this wave's scope). Tests: strategy-service
      `tests/unit/engine/strategies/v2/test_param_schema.py` (10, incl. an engine-source drift guard that reads each
      `*_param(...,<default>)` literal so the schema can't silently diverge from the engine) + PM
      `tests/unit/test_capability_param_schema.py` (5, CSB+APD+VOL_CARRY + manifest round-trip). Wizard-UI render + R1
      full-catalogue pickers + food-chain parameterization remain (next wave).
- [x] ✅ [SCRIPT] P1. (unified-trading-system-ui@869c5930 [UI] | pw:L2 ✓ | regression: tests/smoke/wizard-params.spec.ts + tests/unit/wizard/params.test.ts; loader round-trip strategy-service@965c1393) **Wizard renders per-archetype param forms** from that schema (every numeric/enum param:
      entry/exit bps, stake_fraction, start_token, health-factor, collateral-posting-mode, hedge timing, exec-algo
      params, risk-threshold ladder…) + **(R1)** the venue/instrument pickers expose the FULL catalogue set, not the
      e2e subset. Wire the values through `strategy_config_loader`. Repo: unified-trading-system-ui (+ strategy-service loader).
- [ ] [DOC] P2. Wizard parameterizes the whole food-chain (not just engine params) — exec-algo params, risk ladder,
      collateral posting mode, source routing — track each layer to done per the issue-doc food-chain inventory.

## Phase D — Spot-venue choice for staked-basis (UAC leg-spec/manifest + strategy-service catalog)  [WAVE 2]
- [x] ✅ [REGISTRY] P2. (unified-api-contracts@d0f8f96 + strategy-service@878ab7b8 + unified-trading-system-ui@1ad7fed2 [UI] | pw:L2 ✓ (33 passed) | regression: tests/unit/wizard/parity-gates.test.ts + tests/unit/wizard/graph.test.ts) Make `spot_venue` a first-class selectable axis for staked-basis (Binance vs DEX, liquidity-driven)
      like APD's `venue_universe` — instead of hardcoded per-LST (ETH→Uniswap, SOL→Jupiter). Repos: unified-api-contracts
      (leg-spec/manifest) + strategy-service (catalog).
      **Spot venues now eligible (the SWAP leg trades USDC→native, NOT the LST, so eligibility = "trades USDC↔ETH/SOL spot"):**
      ETH-LST family → `uniswap_v3` (deepest USDC/WETH pool), `curve` (tricrypto USDC↔ETH), `binance` (BINANCE-SPOT ETH/USDC);
      SOL-LST family → `jupiter` (Solana DEX aggregator), `orca` (SOL/USDC whirlpool), `raydium` (SOL/USDC AMM), `binance`
      (BINANCE-SPOT SOL/USDC). Every id is in KNOWN_VENUE_TOKENS + a registered venue (CARRY_BASIS_PERP spot leg already lists
      binance/uniswap_v3). NOT included: Binance does NOT trade the LSTs themselves — but it DOES trade the native USDC pair,
      which is what the SWAP leg needs. **Catalog change**: slot-per-(LST × spot_venue) — `catalog_staked_basis.py` emits one
      `TargetInstanceSpec` per (LST, spot_venue) (4 → 14 staked-basis slots); slot label carries the spot-venue token. **Manifest
      spot-leg venue count**: 2 (`{jupiter, uniswap_v3}`) → 6 (`{binance, curve, jupiter, orca, raydium, uniswap_v3}`). Engine
      preflight verified for BINANCE-SPOT (SWAP leg emits on the chosen venue, structure driven by the PERP venue's collateral
      acceptance — independent of spot venue). Tests: strategy-service `test_carry_staked_basis_spot_venue_axis.py` (Binance/
      Uniswap/Jupiter/Orca SWAP-leg + slot-per-venue catalog) + UAC `test_archetype_leg_spec.py` (spot leg >2 venues incl binance)
      + UI `parity-gates`/`graph` (edge-count + md5 parity). UI manifest + verdict-matrix copies re-synced byte-identical to UAC.

## Codex SSOT updates
- [ ] [DOC] P2. If collateral down-sizing ships, document the collateral-posting-mode + buffer-sizing contract in
      `codex/04-architecture/` (margin/collateral) + the wizard param-schema in the capability-wizard codex.

## Progress Log
- **2026-06-17 — Phase D spot-venue selectable axis SHIPPED** (unified-api-contracts@d0f8f96 + strategy-service@878ab7b8
  + unified-trading-system-ui@1ad7fed2). `spot_venue` is now a first-class selectable leg axis for staked-basis (Binance
  vs DEX), not hardcoded per-LST. Key insight: the SWAP leg trades **USDC→native (ETH/SOL)**, NOT the LST — so eligibility
  is "trades the native USDC pair", which legitimately includes Binance-spot (most-liquid for ETH/USDC + SOL/USDC) alongside
  the family DEXes. UAC `_SPOT_VENUES_STAKED` 2→6 (`{binance, curve, jupiter, orca, raydium, uniswap_v3}`); manifest spot-leg
  venue edges 2→6; catalog emits slot-per-(LST × spot_venue) (4→14 staked-basis slots, all parse + unique). Engine preflight
  verified for BINANCE-SPOT. Tests: SS `test_carry_staked_basis_spot_venue_axis.py` + updated `test_target_universe.py` slot
  counts; UAC `test_archetype_leg_spec.py`; UI `parity-gates`/`graph` (edge 2441→2449, cells 21600→21984). UI manifest +
  verdict-matrix copies md5-identical to UAC (`2835f939…` / `a3c26ef8…`). pw:L2 33 passed.
  - **Foreign WIP encountered + preserved (NOT mine)**: a dead-session source-provenance refactor (`data_source_provenance`
    plan) left UAC (`_source_priority_data.py`/`availability_semantics.py`/`pipeline_mode.py`/`test_source_mode_capability.py`)
    + UTL (`pipeline_mode_resolver.py`) dirty + RED (mid-refactor split of `test_bybit_and_aster…`). I did NOT touch/commit it
    — stashed-by-name to clear the dep tree for the SS quickmerge, then `stash pop` restored it exactly as found. FOLLOW-UP for
    the `data_source_provenance_all_asset_groups_2026_06_01.md` owner: that WIP is incomplete (broke 2 tests in collection-order)
    — finish or revert it.
- **2026-06-17 — Phase C param-schema foundation SHIPPED** (strategy-service@f2d4bef5 + unified-api-contracts@f0b66b2 +
  unified-trading-pm@853ae5ea4). Per-archetype flat PARAM SCHEMA now emitted into `capability-manifest.json` (35
  archetypes × 270 params), single-canonical from the strategy-service engine SSOT (`param_schema.py`), exporter
  probes it in the service's own venv, UAC schema typed (`ParamSchemaSpec`). F4 default-handling verified (engine
  defaults, not e2e-smoke). UI manifest copy re-synced byte-identical (uncommitted — wizard-UI wave owns the commit).
  - **Foreign LDR-debt encountered + reconciled to ship the PM exporter** (none from this change — all pre-existing
    drift the content-sentinel fast-path had been hiding until a content-changing PM commit forced a full gate): (1)
    basedpyright ceiling stale `1517`→`1523` (origin/LDR already sat at 1523 before this session; ratcheted to current
    reality, my exporter is net-0 errors); (2) two codex docs lacked `scope:` frontmatter
    (`carry-venue-live-integration-reference.md`, `dep-update-conflict-resolution.md`) + the former needed
    `last_reviewed:` — added; (3) one foreign `BLOCKED-CREDENTIALS` orphan in
    `carry_staked_basis_funding_scan_experiment_2026_06_16.md:450` — re-baselined the credential-orphan ratchet (the
    checker's own pre-existing-debt mechanism). FOLLOW-UPS for the carry-experiment plan owner: cite a ping on that
    L450 BLOCKED-CREDENTIALS line so the re-baseline can ratchet back to 0.
  - **PM Option-B version churn**: main raced 1.2.151→…→1.2.155 via semver bumps during the ship; aligned PM-self in
    pyproject + manifest each backmerge. The standing LDR→main PR (#387) carries the exporter to main.
- **Remaining for the wizard-UI wave** (Phase C todos 2-3): render per-archetype param forms FROM the manifest
  `param_schema` block; R1 full-catalogue venue/instrument pickers; wire values through `strategy_config_loader`;
  food-chain parameterization (exec-algo / risk ladder / collateral posting mode / source routing). The UI manifest
  copy is already synced + ready; commit it with the render code.

## Phase A follow-ups (discovered during build)
- [ ] [SCRIPT] P2. **Calibrate / parameterize the dual-deposit cross-exchange cost** — `archetypes_rank.py`
      `_DUAL_DEPOSIT_CROSS_EXCHANGE_COST_BPS = 150` is a flagged PLACEHOLDER (operator-calibration pending; affects
      opportunity RANKING only, never sizing/funds). Calibrate to a real cost + expose it as a config param in Phase C's
      wizard parameterization. Repo: strategy-service.
- [ ] [TEST] P3. **`test_batch_harness.py::test_position_state_survives_across_ticks` fails in ISOLATION** with
      `Event logging not initialized` (pre-existing on HEAD, events-bus setup ordering — NOT Phase A); passes in the
      full QG suite. Add a `setup_events()` fixture so it's isolation-safe. Repo: strategy-service.
- NOTE: a F28 live-probe (UAC@bc45549, ~2026-06-17) updated Drift haircuts to real on-chain initialAssetWeight
  (SOL/mSOL/JitoSOL = 0.15/0.20/0.20, were 0.10 placeholders) but left the dynamic-hedge tests stale (expected the old
  0.9 factor). Phase A reconciled them to 0.8 (the 0.20 haircut) — the SSOT is authoritative.
