---
title: e2e DeFi strategy configs — taxonomy/wizard round-trip fidelity gaps
created: 2026-06-17
author: ikennaigboaka [slot-1·laptop]
source:
  - e2e-testing/scripts/defi/*
  - unified-api-contracts/openapi/capability-verdict-matrix.json
  - unified-trading-system-ui/lib/registry/capability-manifest.json
locked_by: live-defi-rollout
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
