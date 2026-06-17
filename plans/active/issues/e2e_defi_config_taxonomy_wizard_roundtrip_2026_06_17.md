---
title: e2e DeFi strategy configs — taxonomy/wizard round-trip fidelity gaps
created: 2026-06-17
source:
  - e2e-testing/scripts/defi/*
  - unified-api-contracts/openapi/capability-verdict-matrix.json
  - unified-trading-system-ui/lib/registry/capability-manifest.json
locked_by: live-defi-rollout
priority: P2
status: active
---

## What I found

Audit of whether the strategies EXERCISED in `e2e-testing/scripts/defi/` round-trip through the canonical
archetype × configuration-axis taxonomy and are constructible in the strategy wizard.

**Clean (the good news):** every (archetype × venue × instrument_type) combo the e2e DeFi tests touch is a
genuinely `available`, `venue_buildable` cell with first-class registered axis values, AND is selectable in the
wizard's leg-aware option tree — CSB(jito-staking / jupiter-spot / drift-perp), APD(binance/okx/hyperliquid
spot+perp), CARRY_BASIS_PERP(drift-perp). No off-taxonomy venue/instrument_type except D3 below.

**Divergences (the "we enabled them differently" the operator suspected):**

- [ ] [TEST] P2. **D1 — 5 of 7 engine-running e2e DeFi tests bypass the canonical config path.** They build the
      strategy by directly calling the engine class ctor with a hand-built `StrategyInstanceIdentity` + free-form
      `params` dict, skipping the production `load_strategy_config → ARCHETYPE_ENGINE_REGISTRY →
      ArchetypeEngineFactory.build` path that live/wizard/`colocated_engine` deployments use:
      `test_csb_paper_e2e_smoke.py:61`, `test_apd_paper_e2e_smoke.py:61`, `test_failure_modes_e2e_smoke.py:76,102`,
      `test_additional_asset_groups_e2e_smoke.py:80,175` (scen a+b). So these smokes prove engine MATH, not that the
      config loads through the production config-loader — a config that fails `strategy_config_loader` would still
      pass them. (The orchestrator-based tests — `test_concurrent_*`, scen c, `backtest_solana_basis.py` — DO use the
      canonical factory.) FIX: route the smokes through `load_strategy_config_by_type`/`register_instance` so they
      exercise the real config→factory path. Repo: e2e-testing.
- [ ] [SCRIPT] P2. **D2 — e2e-hardcoded engine params are not wizard-expressible.** `entry_bps`/`exit_bps`/
      `stake_fraction`/`candidate_venues` (comma-list)/token identities/`dispersion_bps`/`cost_bps` are free-form
      engine params, NOT axis enums; the wizard form exposes archetype + per-leg venue/instrument only. A wizard user
      can select the same archetype/venues/instrument_types but CANNOT reproduce the exact tuned e2e config. DECISION
      NEEDED: should these tuning params be (a) first-class wizard form fields, (b) named config presets, or (c)
      intentionally engine-internal defaults? Repos: unified-trading-system-ui (wizard) + strategy-service (config schema).
- [ ] [REGISTRY] P2. **D3 — `backtest_solana_basis.py` models a drift-perp / Orca(Raydium) SOL-DEX-spot basis, but
      the Solana-DEX spot leg has NO cell.** `CARRY_BASIS_PERP` matrix/wizard spot venues are CEX/`uniswap_v3` only —
      `orca`/`raydium`/`whirlpool` absent from the cells AND the wizard `leg:CARRY_BASIS_PERP:spot`. The backtest only
      *registers* `venue="drift"` (a real cell); the Orca pool is a `--orca-pool` data-loader arg + a label in the
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
(D2), and one tested strategy shape (Solana-DEX-spot basis) isn't a constructible cell at all (D3). None is a data
P0; together they're a "tests prove the engine, not the deployable config" fidelity gap on the May-23 critical path.

## Recommended decision

Ack + route to the strategy-engine / capability-wizard owners. D1+D3 are the substantive ones (test fidelity + a
genuine missing cell); D2 is an operator product decision (expose tuning params in the wizard or not).

## Operator clarifications + deeper audit (2026-06-17)

**D1 is INTENTIONAL** (operator): the e2e tests build in isolation now; they'll be relocated to the proper canonical
path later. NOT a fix — re-tag: `[TEST] DEFERRED-BY-DESIGN` (relocate e2e → canonical `load_strategy_config`/factory
path when the isolation phase ends).

**D2 reframed — the wizard must parameterize the ENTIRE config surface, not archetype+venues** (operator vision):
"once you know the archetype + venues, you parameterize every single part of the food chain / services config." The
wizard is materially incomplete against that bar, for ALL archetypes, not just these.

### Drift collateral answer (operator's concrete question)
- **YES — Drift accepts the spot/LST as collateral** (collateralized short IS possible on drift): USDC(0), SOL(0.05),
  **mSOL(0.10 `# PLACEHOLDER`)**, JitoSOL(0.10) — `venue_collateral.py:112-125`. NOT stables-only. (mSOL haircut is the
  held placeholder — must be re-probed before go-live, `PLACEHOLDER_HAIRCUTS_PENDING_GO_LIVE:268-273`.)
- **Aster = stables-only** (USDC/USDT; all LSTs `accepted=False`) — confirms the operator's example. **Hyperliquid =
  USDC-only** too. Bybit(stETH 0.10 PLACEHOLDER)/OKX(wstETH 0.10)/Deribit(stETH 0.075) accept some LSTs.

### NEW findings (buildable gaps)
- [ ] [SCRIPT] P1. **Collateral-aware down-sizing is NOT implemented — the operator's "deposit USDC + size down for
      margin headroom on a stables-only venue (Aster pattern)" path does not exist.** `staked_basis.py:219-229`
      `_derive_structure`: if the LST is not in `accepted_perp_collateral(perp_venue)` → returns `None` → slot
      REJECTED. The archetype is `LST_AS_MARGIN` only (SPLIT_STAKE deleted); `stake_fraction` forced == 1.0
      (:242-248) so it cannot even express a down-sized deposit-and-buffer position. So **Aster (+ any USDC-only perp
      venue) is structurally unusable for staked-basis today** — rejected, not handled. The haircut is consulted only
      for hedge-leg delta-matching (`dynamic_hedge_ratio.py:167`), not buffer sizing. FIX: add the USDC-collateral +
      buffer-down-size branch (deposit stables, reduce hedge/trade size by a margin-call buffer) driven by
      `venue_accepts_collateral`/`get_collateral_haircut`; allow `stake_fraction < 1.0`. Repo: strategy-service (+ UTL margin).
- [ ] [SCRIPT] P3. **Dead `per_venue_margin_buffer_pct: 0.20`** in `strategy-service/.../configs/arbitrage_price_dispersion.yaml`
      has ZERO Python wiring — wire it into the P1 buffer-sizing or delete it. Repo: strategy-service.
- [ ] [REGISTRY] P2. **Spot-leg venue is hardcoded per-LST for staked-basis (ETH-LST→UNISWAP_V3, SOL-LST→JUPITER,
      `catalog_staked_basis.py:30-35`) — no Binance-spot / orca / raydium alternative**, though the engine accepts a
      `spot_venue` param. Operator wants spot venue selectable (Binance vs DEX, liquidity-driven). Make spot_venue a
      first-class selectable axis for staked-basis (it already is for APD via `venue_universe`). Repos:
      unified-api-contracts (leg-spec/manifest) + strategy-service (catalog).
- [ ] [SCRIPT] P1. **Wizard parameterizes ~0 of the numeric production-param surface** — exposes only structural
      picks (archetype/legs/venues/algo/model/capital/risk-%×2/treasury/wallet/custody). The 5 behavioural params
      (`entry_bps`/`exit_bps`/`min_health_factor`/`hedge_deadline_ms`/`peg_drift_threshold_bps`) + `stake_fraction` +
      `start_token` + collateral posting mode are NOT form fields; APD's ~25-key surface is 100% absent. ROOT CAUSE:
      the capability-manifest is a node/edge GRAPH with **no flat parameter schema** — so there is nothing for the
      wizard to render param forms from. FIX (the real initiative): (1) emit a per-archetype flat PARAM SCHEMA into the
      capability manifest (name/type/default/range/units, sourced from each engine's config model), (2) wizard renders
      per-archetype param forms from it, (3) wire the values through `strategy_config_loader`. Repos:
      unified-api-contracts (manifest exporter) + strategy-service (engine config schema) + unified-trading-system-ui (wizard).
- [ ] [SCRIPT] P2. **Audit production params vs e2e/testing params for functional alignment** (operator ask) — the e2e
      catalog sets the 7 structural params but leaves the 5 behavioural ones to engine defaults; confirm the engine
      defaults == the values the production/paper runs intend (functionally, not by name). Repo: e2e-testing + strategy-service.

### Food-chain parameterization completeness (wizard touches ~8 of ~16 config layers)
Wizard-set: archetype/family, leg instruments+venues, exec-algo (pick only), risk %×2, capital, treasury-split,
custody/signing, wallet, ML model (pick only). NOT set (defaults/code/placeholder-YAML): engine numeric params,
collateral token/posting mode, start_token, exec-algo PARAMS, the full risk-threshold ladder
(WARNING→AUTO_REDUCE→AUTO_CLOSE_ALL), data-source routing, margin buffer. The collateral posting-mode + margin-buffer
sizing — the operator's core question — is **not a parameter anywhere**; it is engine-derived accept/reject.
