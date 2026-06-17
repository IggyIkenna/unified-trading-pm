---
title: Collateral-aware sizing + opportunity-checker + wizard full-parameterization
created: 2026-06-17
author: ikennaigboaka [slot-1·laptop]
parent_epic: strategy_master
assigned_vm: vm-trading-core
estimate_class: brand-new
estimate_baseline_ai_days: 18.0
estimate_calibrated_ai_days: 18.0
locked_by: live-defi-rollout
locked_since: 2026-06-17
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

- [ ] [SCRIPT] P1. **Build the USDC-collateral + margin-buffer down-size branch** in the staked-basis (and basis-perp)
      engine: when `venue_accepts_collateral(perp_venue, lst)` is False but the venue accepts a stable → deposit the
      stable + size the position down by a margin-call buffer (driven by `get_collateral_haircut` + the buffer), allow
      `stake_fraction < 1.0`, keep delta-neutral on the reduced notional. Replaces the hard reject. Wire (or delete +
      re-add) `per_venue_margin_buffer_pct`. Unit tests: Aster/Hyperliquid (USDC-only) → buffered down-sized position
      (not reject); Drift/Bybit (LST-accepting) → full LST-as-margin path unchanged. Repos: strategy-service + UTL margin.
- [ ] [SCRIPT] P1. **(R2) Feed the down-size into the opportunity checker/ranker** — find the opportunity/oppty-scoring
      surface (grep strategy-service/UTL for opportunity/scanner/ranker/edge-vs-cost); when a candidate basis requires
      stables-only collateral, the scored opportunity uses the REDUCED size + a cross-exchange-risk/dual-deposit capital
      cost, so it ranks below an equivalent full-collateral one. Tests assert the penalty. Repo: strategy-service (+ UTL).

## Phase B — Production-param surface audit + flat PARAM SCHEMA inventory (read-only → schema doc)  [WAVE 1]
- [ ] [SCRIPT] P2. **Enumerate the full production-param surface per archetype** (engine `__init__`/config-model/
      `strategy_config_loader` schema) — name/type/default/range/units for every param, ALL archetypes (start with the
      live DeFi + the new VOL_*/MM). Confirm the e2e/catalog params functionally match the engine defaults (the
      prod-vs-testing alignment ask). OUTPUT: a structured per-archetype param schema (the input Phase C emits into the
      manifest). Repo: strategy-service (read) → schema artifact.

## Phase C — Wizard full-parameterization (UAC manifest exporter + strategy-service config + UI)  [WAVE 2, needs B]
- [ ] [SCRIPT] P1. **Emit a per-archetype flat PARAM SCHEMA into the capability manifest** (the exporter; sourced from
      each engine's config model — Phase B's inventory). The manifest is a node/edge graph today with NO param schema;
      add the schema block. Repos: unified-api-contracts (exporter) + strategy-service (config models expose the schema).
- [ ] [SCRIPT] P1. **Wizard renders per-archetype param forms** from that schema (every numeric/enum param:
      entry/exit bps, stake_fraction, start_token, health-factor, collateral-posting-mode, hedge timing, exec-algo
      params, risk-threshold ladder…) + **(R1)** the venue/instrument pickers expose the FULL catalogue set, not the
      e2e subset. Wire the values through `strategy_config_loader`. Repo: unified-trading-system-ui (+ strategy-service loader).
- [ ] [DOC] P2. Wizard parameterizes the whole food-chain (not just engine params) — exec-algo params, risk ladder,
      collateral posting mode, source routing — track each layer to done per the issue-doc food-chain inventory.

## Phase D — Spot-venue choice for staked-basis (UAC leg-spec/manifest + strategy-service catalog)  [WAVE 2]
- [ ] [REGISTRY] P2. Make `spot_venue` a first-class selectable axis for staked-basis (Binance vs DEX, liquidity-driven)
      like APD's `venue_universe` — instead of hardcoded per-LST (ETH→Uniswap, SOL→Jupiter). Repos: unified-api-contracts
      (leg-spec/manifest) + strategy-service (catalog).

## Codex SSOT updates
- [ ] [DOC] P2. If collateral down-sizing ships, document the collateral-posting-mode + buffer-sizing contract in
      `codex/04-architecture/` (margin/collateral) + the wizard param-schema in the capability-wizard codex.

## Progress Log
(loop handoff lands here)
