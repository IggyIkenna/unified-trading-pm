---
scope: [engineer, admin]
last_reviewed: 2026-05-22
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
- `codex/09-strategy/architecture-v2/cross-cutting/allocator-pipeline-contract.md`
- `codex/09-strategy/architecture-v2/leverage-and-volatility.md`
