---
doc_type: codex-ssot
title: Instrument Type × Leverage Matrix
summary:
  Config-SSOT matrix (DELTA 2026-05-22) of max leverage per instrument_type × asset_group, enforced by
  strategy_service/portfolio_allocator/guard_rails.py at instruction-emit time — SPOT 1.0×, PERPETUAL cefi 10.0× / defi
  5.0×, OPTION 1.0×, STAKED 1.0×, EVENT_CONTRACT (tradfi/prediction) 1.0×. Currently implicit in per-archetype config;
  full per-venue/per-archetype expansion owned by strategy_master.
status: draft
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [strategy, leverage, allocator, risk, defi, cefi]
related:
  [
    /codex/09-strategy/architecture-v2/cross-cutting/allocator-pipeline-contract.md,
    /codex/09-strategy/architecture-v2/cross-cutting/archetype-param-schema-inventory.md,
  ]
created: 2026-05-22
authoritative_for: [instrument-type x asset-group max-leverage matrix (guard_rails enforcement)]
referenced_by:
  [
    /codex/09-strategy/_archived_pre_v2/cross-cutting/venue-collateral-and-wrapping.md,
    /codex/09-strategy/architecture-v2/cross-cutting/allocator-pipeline-contract.md,
    /codex/09-strategy/architecture-v2/cross-cutting/archetype-param-schema-inventory.md,
    /codex/09-strategy/architecture-v2/cross-cutting/leverage-and-volatility.md,
  ]
owner:
last_reviewed: 2026-05-22
code_refs:
---

# Instrument Type × Leverage Matrix

> **[DELTA 2026-05-22]** **Current state:** Instrument-type leverage limits exist in config but are not documented at
> codex level. Discovery via `strategy_archetype_logic_audit_2026_05_20.md`. **Planned delta:** Full matrix per
> `strategy_master.md`. **Target architecture:** Canonical matrix of max leverage by instrument type + asset group.

## Context

Specifies which leverage multiples are permitted for each instrument type (spot/perp/option/etc.) per asset group. The
allocator's `guard_rails.py` enforces these at instruction-emit time; the matrix is the config SSOT.

## Current State

Leverage limits are expressed as `leverage_multiplier` in per-archetype config (e.g. `carry_staked_basis` archetype
config YAML) and enforced in `strategy_service/portfolio_allocator/guard_rails.py`. The matrix is implicit in the config
files, not centralised.

## Target

| instrument_type  | asset_group | max_leverage | Notes                                                     |
| ---------------- | ----------- | ------------ | --------------------------------------------------------- |
| `SPOT`           | any         | 1.0×         | No leverage on spot                                       |
| `PERPETUAL`      | cefi        | 10.0×        | Exchange margin limits apply; guard_rails clips below     |
| `PERPETUAL`      | defi        | 5.0×         | On-chain perp DEX (Hyperliquid/Drift); lower cap for risk |
| `OPTION`         | cefi        | 1.0×         | Defined-risk; no leverage on option purchase              |
| `STAKED`         | defi        | 1.0×         | LST staking positions are unleveraged by definition       |
| `EVENT_CONTRACT` | tradfi      | 1.0×         | CME event contracts; binary payoff; no leverage           |
| `EVENT_CONTRACT` | prediction  | 1.0×         | Polymarket; binary payoff; no leverage                    |

Full matrix expansion (per-venue sub-limits, per-archetype overrides, margin-mode check) is owned by
`plans/epics/strategy_master.md`.

## See also

- `plans/epics/strategy_master.md`
- `plans/active/issues/strategy_archetype_logic_audit_2026_05_20.md`
- `/codex/09-strategy/architecture-v2/cross-cutting/allocator-pipeline-contract.md`
- `/codex/09-strategy/architecture-v2/leverage-and-volatility.md`
