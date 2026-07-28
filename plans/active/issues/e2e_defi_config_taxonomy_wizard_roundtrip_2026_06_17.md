---
doc_type: issue
title: e2e DeFi strategy configs — taxonomy/wizard round-trip fidelity gaps
summary:
  Audit of whether the strategies EXERCISED in `e2e-testing/scripts/defi/` round-trip through the canonical archetype ×
  configuration-axis taxonomy and are constructible in the strategy wizard.
status: open
nature: process
asset_group:
  [defi] # corrected 2026-07-25 (ag-closeout-audit orthogonality fix) -- was [cross-cutting], a genuine mistag:
  # title says "e2e DeFi strategy configs", repos/paths are all e2e-testing/scripts/defi/* -- content is defi-only

stage: [meta]
repos: [e2e-testing, strategy-service, unified-api-contracts, unified-trading-system-ui]
scope: [engineer, admin]
tags: [defi, strategy, e2e, ui, uac, validation, verification]
related: [/plans/archive/issues/e2e_defi_strategy_funding_apr_gas_correctness_2026_06_17.md]
created: 2026-06-17
parent_epic: strategy_master
priority: P2
source:
  [
    e2e-testing/scripts/defi/*,
    unified-api-contracts/openapi/capability-verdict-matrix.json,
    unified-trading-system-ui/lib/registry/capability-manifest.json,
  ]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-28
---

## What I found

Audit of whether the strategies EXERCISED in `e2e-testing/scripts/defi/` round-trip through the canonical archetype ×
configuration-axis taxonomy and are constructible in the strategy wizard.

**Clean (the good news):** every (archetype × venue × instrument_type) combo the e2e DeFi tests touch is a genuinely
`available`, `venue_buildable` cell with first-class registered axis values, AND is selectable in the wizard's leg-aware
option tree — CSB(jito-staking / jupiter-spot / drift-perp), APD(binance/okx/hyperliquid spot+perp),
CARRY_BASIS_PERP(drift-perp). No off-taxonomy venue/instrument_type except D3 below.

**Divergences (the "we enabled them differently" the operator suspected):**

- [ ] [TEST] P2. **DEFERRED-BY-DESIGN** — **D1 — 5 of 7 engine-running e2e DeFi tests bypass the canonical config
      path.** They build the strategy by directly calling the engine class ctor with a hand-built
      `StrategyInstanceIdentity` + free-form `params` dict, skipping the production
      `load_strategy_config → ARCHETYPE_ENGINE_REGISTRY → ArchetypeEngineFactory.build` path that
      live/wizard/`colocated_engine` deployments use: `test_csb_paper_e2e_smoke.py:61`,
      `test_apd_paper_e2e_smoke.py:61`, `test_failure_modes_e2e_smoke.py:76,102`,
      `test_additional_asset_groups_e2e_smoke.py:80,175` (scen a+b). So these smokes prove engine MATH, not that the
      config loads through the production config-loader — a config that fails `strategy_config_loader` would still pass
      them. **Operator-ruled INTENTIONAL (2026-06-17, re-confirmed 2026-07-27
      `june_2026_vintage_audit_findings_2026_07_27.md` §5 item 5): the e2e tests build in isolation on purpose; they'll
      relocate to the canonical `load_strategy_config`/factory path when the isolation phase ends — no timeline given,
      NOT a fix to schedule.** Not routing to a fix-worker; **DEFERRED-BY-DESIGN** marker added (mirrors the `BLOCKED-*`
      convention used elsewhere in this corpus) so the backlog no longer re-derives this as ordinary open test work.
      (The orchestrator-based tests — `test_concurrent_*`, scen c, `backtest_solana_basis.py` — DO use the canonical
      factory.) WHEN the isolation phase ends (operator-owned, no timeline): route the smokes through
      `load_strategy_config_by_type`/ `register_instance` so they exercise the real config→factory path. Repo:
      e2e-testing. **Backlog-dispatch bug fixed 2026-07-28** — `_NON_DISPATCHABLE_RE` in `regen_backlog_from_plan.py`
      did not exclude `DEFERRED-BY-DESIGN` items, so this exact todo kept re-entering the backlog under a P-tag-less
      default priority and getting dispatched to workers every regen tick despite the standing 2026-06-17 ruling; fixed
      agent-orchestrator@12d656f (mirrors the existing BLOCKED-* exclusion).
- [ ] [SCRIPT] P2. **D2 — e2e-hardcoded engine params are not wizard-expressible.** `entry_bps`/`exit_bps`/
      `stake_fraction`/`candidate_venues` (comma-list)/token identities/`dispersion_bps`/`cost_bps` are free-form engine
      params, NOT axis enums; the wizard form exposes archetype + per-leg venue/instrument only. A wizard user can
      select the same archetype/venues/instrument_types but CANNOT reproduce the exact tuned e2e config. DECISION
      NEEDED: should these tuning params be (a) first-class wizard form fields, (b) named config presets, or (c)
      intentionally engine-internal defaults? Repos: unified-trading-system-ui (wizard) + strategy-service (config
      schema).
- [ ] [REGISTRY] P2. **D3 — `backtest_solana_basis.py` models a drift-perp / Orca(Raydium) SOL-DEX-spot basis, but the
      Solana-DEX spot leg has NO cell.** `CARRY_BASIS_PERP` matrix/wizard spot venues are CEX/`uniswap_v3` only —
      `orca`/`raydium`/`whirlpool` absent from the cells AND the wizard `leg:CARRY_BASIS_PERP:spot`. The backtest only
      _registers_ `venue="drift"` (a real cell); the Orca pool is a `--orca-pool` data-loader arg + a label in the
      `instance_id` string. So a wizard user could NOT build the drift-perp/orca-spot SOL basis strategy the backtest
      models. FIX: add the Solana-DEX spot venues (orca/raydium) to `CARRY_BASIS_PERP` leg-spec + verdict-matrix +
      wizard, OR document that Solana-DEX-spot basis is data-only / not a deployable cell. Repo: unified-api-contracts.
- [ ] [SCRIPT] P3. **D4 — `recursive_borrow_paper_smoke.py` is a non-instantiating stub** (`INFRA_GAP`/
      `NotImplementedError`, BLOCKED-CREDENTIALS) — references cell
      `CARRY_RECURSIVE_BORROW_LENDING_ONLY@aave_v3-ethereum-wsteth-weth-emode` but never builds an engine + never
      asserts that specific aave e-mode cell against the matrix. When the credentials/infra land, make it a real
      round-trip smoke through the canonical path. Repo: e2e-testing.

## Why it matters

The taxonomy + venue/instrument axes are sound and wizard-accessible — but the e2e smokes don't PROVE the
config-loader/wizard path works end-to-end (D1), the fine parameterization isn't operator-reproducible via the wizard
(D2), and one tested strategy shape (Solana-DEX-spot basis) isn't a constructible cell at all (D3). None is a data P0;
together they're a "tests prove the engine, not the deployable config" fidelity gap on the May-23 critical path.

## Recommended decision

Ack + route to the strategy-engine / capability-wizard owners. D1+D3 are the substantive ones (test fidelity + a genuine
missing cell); D2 is an operator product decision (expose tuning params in the wizard or not).

## Operator clarifications + deeper audit (2026-06-17)

**D1 is INTENTIONAL** (operator): the e2e tests build in isolation now; they'll be relocated to the proper canonical
path later. NOT a fix — re-tag: `[TEST] DEFERRED-BY-DESIGN` (relocate e2e → canonical `load_strategy_config`/factory
path when the isolation phase ends).

**D2 reframed — the wizard must parameterize the ENTIRE config surface, not archetype+venues** (operator vision): "once
you know the archetype + venues, you parameterize every single part of the food chain / services config." The wizard is
materially incomplete against that bar, for ALL archetypes, not just these.

### Drift collateral answer (operator's concrete question)

- **YES — Drift accepts the spot/LST as collateral** (collateralized short IS possible on drift): USDC(0), SOL(0.15),
  mSOL(0.20), JitoSOL(0.20) — `venue_collateral.py:119-151` (real on-chain `initialAssetWeight`, probed 2026-06-17,
  `unified-api-contracts@bc455499`). NOT stables-only. _(was: "USDC(0), SOL(0.05), mSOL(0.10 `# PLACEHOLDER`),
  JitoSOL(0.10)" per `venue_collateral.py:112-125` — corrected 2026-07-12, plan-reconciliation finding 296, §A2 B-queue
  ruling: superseded by the F28 live-probe documented in
  `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md:187-188`; these are now real on-chain values,
  not placeholders — the "held placeholder — must be re-probed" note + `PLACEHOLDER_HAIRCUTS_PENDING_GO_LIVE` reference
  immediately below are themselves stale for these three rows.)_
- **Aster = stables-only** (USDC/USDT; all LSTs `accepted=False`) — confirms the operator's example. **Hyperliquid =
  USDC-only** too. Bybit(stETH 0.10 PLACEHOLDER)/OKX(wstETH 0.10)/Deribit(stETH 0.075) accept some LSTs.

### NEW findings (buildable gaps)

- [x] ✅ [SCRIPT] P1. (was: `- [ ]` "Collateral-aware down-sizing is NOT implemented" — corrected 2026-07-12, finding
      301, §A2 "50 reclassified" blanket ruling) **Collateral-aware down-sizing IS now implemented** — the
      USDC-collateral + margin-buffer down-size branch this todo asked for shipped in
      `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md` Phase A (strategy-service@6e9164b1),
      confirmed live in strategy-service HEAD: `staked_basis.py` `_derive_structure` (:281-311) now branches on
      `venue_accepts_collateral`/`accepted_perp_collateral` and returns a `USDC_MARGIN_BUFFERED` structure; the setup
      routine (:314-360) derives `stake_fraction = 1.0 - margin_buffer_pct` for that structure (no longer forced ==
      1.0). Original text preserved below for context — the described gap no longer exists. Original:
      "**Collateral-aware down-sizing is NOT implemented — the operator's "deposit USDC + size down for margin headroom
      on a stables-only venue (Aster pattern)" path does not exist.** `staked_basis.py:219-229` `_derive_structure`: if
      the LST is not in `accepted_perp_collateral(perp_venue)` → returns `None` → slot REJECTED. The archetype is
      `LST_AS_MARGIN` only (SPLIT_STAKE deleted); `stake_fraction` forced == 1.0 (:242-248) so it cannot even express a
      down-sized deposit-and-buffer position. So **Aster (+ any USDC-only perp venue) is structurally unusable for
      staked-basis today** — rejected, not handled. The haircut is consulted only for hedge-leg delta-matching
      (`dynamic_hedge_ratio.py:167`), not buffer sizing. FIX: add the USDC-collateral + buffer-down-size branch (deposit
      stables, reduce hedge/trade size by a margin-call buffer) driven by
      `venue_accepts_collateral`/`get_collateral_haircut`; allow `stake_fraction < 1.0`. Repo: strategy-service (+ UTL
      margin)."
- [ ] [SCRIPT] P3. **Dead `per_venue_margin_buffer_pct: 0.20`** in
      `strategy-service/.../configs/arbitrage_price_dispersion.yaml` has ZERO Python wiring — wire it into the P1
      buffer-sizing or delete it. Repo: strategy-service.
- [ ] [REGISTRY] P2. **Spot-leg venue is hardcoded per-LST for staked-basis (ETH-LST→UNISWAP_V3, SOL-LST→JUPITER,
      `catalog_staked_basis.py:30-35`) — no Binance-spot / orca / raydium alternative**, though the engine accepts a
      `spot_venue` param. Operator wants spot venue selectable (Binance vs DEX, liquidity-driven). Make spot_venue a
      first-class selectable axis for staked-basis (it already is for APD via `venue_universe`). Repos:
      unified-api-contracts (leg-spec/manifest) + strategy-service (catalog).
- [x] ✅ [SCRIPT] P1. (RE-VERIFIED 2026-07-27, slot-4 — was `- [ ]`, stale: the FIX this todo asks for already shipped
      the same day it was filed, via the sibling initiative
      `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md`, but that plan's own checkbox flip never
      propagated back to this doc) **Wizard parameterizes ~0 of the numeric production-param surface** — exposes only
      structural picks. RESOLVED: independently re-verified all 3 legs of the FIX live on current `live-defi-rollout`
      HEAD, not just trusting the historical citation: (1) **flat per-archetype PARAM SCHEMA in the manifest** —
      `unified-api-contracts/openapi/capability-manifest.json` top-level `param_schema` key, 35 archetypes ×
      `{name,type,default,required,units,enum_values,min,max,source}` rows sourced to exact engine `file:line`s
      (verified by loading the JSON directly: `CARRY_STAKED_BASIS`/`ARBITRAGE_PRICE_DISPERSION`/`CARRY_BASIS_PERP` all
      present with real rows, e.g.
      `entry_bps`/`exit_bps`/`min_health_factor`/`hedge_deadline_ms`/`peg_drift_threshold_bps`/`stake_fraction`/`start_token`
      for CSB, ~18 keys for APD); byte-identical UI copy at
      `unified-trading-system-ui/lib/registry/capability-manifest.json`. Exporter:
      `unified-trading-pm/scripts/openapi/generate_capability_manifest.py` → `_capability_gaps.extract_param_schema()`
      probing `strategy_service.engine.strategies.v2.param_schema.build_param_schema_registry()` in strategy-service's
      own `.venv`. (2) **wizard renders per-archetype param forms from it** —
      `unified-trading-system-ui/components/wizard/ParamForm.tsx` wired at wizard stage `K_PARAMS`
      (`app/(wizard)/wizard/page.tsx:45,478`, confirmed live), numeric/enum/bool/str fields pre-filled with engine
      defaults, required fields enforced. (3) **wired through `strategy_config_loader`** —
      `strategy-service/strategy_service/engine/core/strategy_config_loader.py:128` `get_strategy_params()` confirmed
      present: reads `config["params"]`, resolves archetype, looks up `PARAM_SCHEMA_REGISTRY[archetype.value]`,
      loud-fails (`WizardParamPayloadError`) on an unknown param/missing required value, fills unset params from schema
      defaults. Shipped commits (git-log verified): strategy-service `f2d4bef5`+`965c1393`, unified-api-contracts
      `f0b66b2`, unified-trading-pm `853ae5ea4`, unified-trading-system-ui `869c5930`; same equivalent item already
      checked off with evidence in `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md:107`
      (`unified-trading-system-ui@869c5930 [UI] | pw:L2 ✓ | regression: tests/smoke/wizard-params.spec.ts + tests/unit/wizard/params.test.ts`).
      NOT re-doing this work — building it again would duplicate ~35 archetypes' worth of shipped, tested pipeline.
      **Residual (do not re-open here, already tracked elsewhere):** `collateral posting mode` specifically + the rest
      of the "food chain" (exec-algo params, risk ladder, source routing) remains open as
      `defi_collateral_sizing_and_wizard_full_parameterization_2026_06_17.md:110` `- [ ] [DOC] P2.`; the 4th archetype
      named implicitly by this todo's D4 neighbor, `CARRY_RECURSIVE_BORROW_LENDING_ONLY`, has no `PARAM_SCHEMA_REGISTRY`
      row (confirmed: 0 grep hits) but is a deliberate permanent engine stub (`on_tick()` always `return []`) pending an
      unresolved strategy-design decision — exhaustively scoped, not built, in
      `plans/active/issues/defi_catalog_engine_config_key_contract_drift_2026_07_23.md:482-660` — parameterizing it in
      the wizard today would be cosmetic since the engine can't act on it regardless.
- [ ] [SCRIPT] P2. **Audit production params vs e2e/testing params for functional alignment** (operator ask) — the e2e
      catalog sets the 7 structural params but leaves the 5 behavioural ones to engine defaults; confirm the engine
      defaults == the values the production/paper runs intend (functionally, not by name). Repo: e2e-testing +
      strategy-service.

### Food-chain parameterization completeness (wizard touches ~8 of ~16 config layers)

Wizard-set: archetype/family, leg instruments+venues, exec-algo (pick only), risk %×2, capital, treasury-split,
custody/signing, wallet, ML model (pick only). NOT set (defaults/code/placeholder-YAML): engine numeric params,
collateral token/posting mode, start_token, exec-algo PARAMS, the full risk-threshold ladder
(WARNING→AUTO_REDUCE→AUTO_CLOSE_ALL), data-source routing, margin buffer. The collateral posting-mode + margin-buffer
sizing — the operator's core question — is **not a parameter anywhere**; it is engine-derived accept/reject.
