---
scope: [engineer, admin]
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
