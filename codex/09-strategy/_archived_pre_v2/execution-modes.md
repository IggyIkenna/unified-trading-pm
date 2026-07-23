---
doc_type: codex-ssot
title: Execution Modes — SCE vs HUF vs EVT
summary: >-
  [SUPERSEDED, pre-v2] The three strategy execution modes — HUF (Hold Until Flip, signal-driven), SCE (Same Candle Exit,
  ML TP/SL within one candle), EVT (Event Driven, market-making / options / live sports) — with per-category
  allowed-mode restrictions (DeFi + Sports never SCE) enforced via UTL `id_conventions.py` and UAC
  `StrategyRegistry.allowed_modes`. Replaced by the architecture-v2 hold-policy axis.
status: superseded
nature: ssot
asset_group: [meta]
stage: [meta]
repos: [strategy-service, unified-api-contracts, unified-trading-library]
scope: [engineer, admin]
tags: [strategy, execution, cefi, tradfi, defi, uac]
related: [/codex/09-strategy/_archived_pre_v2/strategy-registry.md, ../architecture-v2/README.md]
created: 2026-04-16
authoritative_for:
referenced_by: [/codex/09-strategy/_archived_pre_v2/strategy-registry.md]
owner:
last_reviewed:
code_refs:
---

# Execution Modes — SCE vs HUF vs EVT

## Mode Definitions

| Mode | Name             | Behaviour                                                                      |
| ---- | ---------------- | ------------------------------------------------------------------------------ |
| HUF  | Hold Until Flip  | Signal updates drive position changes. Hold until next signal.                 |
| SCE  | Same Candle Exit | ML-driven TP/SL within one candle. Entry, take-profit, stop-loss, exit.        |
| EVT  | Event Driven     | Tick-level or real-time event responses (market making, options, live sports). |

## Category Restrictions

| Category   | Allowed Modes | Notes                                                  |
| ---------- | ------------- | ------------------------------------------------------ |
| DEFI       | HUF, EVT      | Never SCE. DeFi is inherently hold-until-flip.         |
| CEFI       | HUF, SCE, EVT | SCE only for ML TP/SL strategies. MM uses EVT.         |
| TRADFI     | HUF, SCE, EVT | SCE only for ML TP/SL strategies. Options MM uses EVT. |
| SPORTS     | HUF, EVT      | Never SCE. Match-event driven.                         |
| PREDICTION | HUF, EVT, SCE | Arb may use SCE for same-event exit.                   |

## Enforcement

- `id_conventions.py` in UTL cross-validates category x mode
- `StrategyRegistry` in UAC declares `allowed_modes` per strategy
- Invalid combinations raise `ValueError` at strategy ID generation time

## Market Making (All Categories)

Market making uses EVT mode with the **reference price model**:

1. Strategy emits `reference_price` in StrategyInstruction
2. Execution market-makes around that reference price
3. When strategy updates reference_price, execution updates quotes
4. For options: `delta_premium` from pricing engine -> execution computes option quotes
