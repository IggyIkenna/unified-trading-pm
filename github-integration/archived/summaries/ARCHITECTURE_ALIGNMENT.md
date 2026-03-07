# Architecture Alignment: Epic 1 (Exchange Interface)

## 📐 3-Layer Execution Stack

```
┌─────────────────────────────────────────────────────────────┐
│ LAYER 1: Strategy                                           │
│ ─────────────────────────────────────────────────────────   │
│ • Validates risk/position limits                            │
│ • Ensures logical pricing                                   │
│ • Defines instrument universe per instruction               │
│ • Output: ExecutionInstruction                              │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 2: Execution Manager                                  │
│ ─────────────────────────────────────────────────────────   │
│ • Receives instructions (subscriptions)                     │
│ • Routing (brokers, SOR, parent-child orders)              │
│ • Order lifecycle management                                │
│ • Output: Normalized routing actions (FOK, venue, amount)  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│ LAYER 3: Exchange Interface (Epic 1 scope)                 │
│ ─────────────────────────────────────────────────────────   │
│ • Translates normalized actions → venue-specific format     │
│ • Manages connectivity, retries, health                     │
│ • Returns order status/fills                                │
│                                                              │
│ ┌────────────────────────┬───────────────────────────────┐ │
│ │  Live Adapters         │  Simulation Adapters          │ │
│ ├────────────────────────┼───────────────────────────────┤ │
│ │ • Real venue APIs      │ • Matching engine integration │ │
│ │ • Binance, Coinbase    │ • Synthetic market data       │ │
│ │ • Actual responses     │ • Simulated fills             │ │
│ └────────────────────────┴───────────────────────────────┘ │
│                                                              │
│ Mode selection: Environment variable (EXECUTION_MODE)      │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Epic 1 Scope: Exchange Interface Package

### Confirmed In-Scope

**Task 1: Core Adapter Framework** (5 subtasks)

- Base adapter interface/abstract class
- Retry/idempotency decorator
- Connection health signaling
- ✅ **NEW:** Mode parameter (live/simulation)
- ✅ **NEW:** Adapter factory with env-based mode selection

**Task 2: Market Data Adapters** (2 subtasks)

- Market stream subscribe/unsubscribe (live)
- Market data normalization layer

**Task 3: Order Management Adapters** (2 subtasks)

- Order place/cancel/amend (live)
- Order status and fill events handler

**Task 4: Simulation Adapter Layer** (4 subtasks) ✅ **NEW TASK**

- Simulation adapter interface (extends base)
- Integration with existing matching engine
- Synthetic market data replay
- Simulation-specific health/status

**Task 5: Testing & Documentation** (4 subtasks)

- Unit tests for adapter interfaces
- Integration tests (live mode with test venues)
- ✅ **NEW:** Integration tests (simulation mode)
- Documentation (usage, extension, mode selection)

---

## 🚫 Explicitly Out of Scope (Layers 1-2)

### Layer 1: Strategy Validation

- Risk limit checks
- Position limit validation
- Price sanity checks
- Instrument universe definition

**Current state:** Embedded in `execution-service` **Action:** No refactoring needed (assume clean separation already
exists)

### Layer 2: Execution Manager

- Instruction routing (TWAP, SOR, parent-child)
- Order slicing/aggregation
- Execution algorithm orchestration

**Current state:** `InstructionRouter` in `execution-service` **Action:** No refactoring needed (assume clean separation
already exists)

---

## 🔧 Mode Selection Mechanism

### Environment Variable (Confirmed)

```bash
# Live mode (production, testnet)
export EXECUTION_MODE=live

# Simulation mode (backtest, paper trading)
export EXECUTION_MODE=simulation
```

### Adapter Factory Pattern

```python
# Pseudo-code (Epic 1 Task 1, Subtask 5)
class AdapterFactory:
    @staticmethod
    def create_adapter(venue: str) -> BaseExchangeAdapter:
        mode = os.getenv("EXECUTION_MODE", "live")

        if mode == "live":
            return LiveVenueAdapter(venue)
        elif mode == "simulation":
            return SimulationAdapter(venue, matching_engine)
        else:
            raise ValueError(f"Invalid EXECUTION_MODE: {mode}")
```

---

## 📦 Package Structure

```
exchange-interface/  (new shared package)
├── exchange_interface/
│   ├── __init__.py
│   ├── base_adapter.py         # Abstract base class
│   ├── protocols.py             # Type protocols
│   ├── retry.py                 # Retry/idempotency decorators
│   ├── health.py                # Health signaling
│   ├── factory.py               # Mode-aware adapter factory
│   │
│   ├── live/                    # Live venue adapters
│   │   ├── __init__.py
│   │   ├── binance.py
│   │   ├── coinbase.py
│   │   └── ...
│   │
│   ├── sim/                     # Simulation adapters
│   │   ├── __init__.py
│   │   ├── simulation_adapter.py
│   │   ├── matching_engine_integration.py
│   │   └── market_data_replay.py
│   │
│   └── normalizers.py           # Data normalization utilities
│
└── tests/
    ├── unit/
    ├── integration/
    │   ├── test_live_adapters.py
    │   └── test_sim_adapters.py
    └── ...
```

---

## 🔗 Dependencies

### From execution-service

- **Matching engine package** (already exists)
  - Used by: `sim/matching_engine_integration.py`
  - Purpose: Simulate order fills in backtest mode

### Consumed by

- **execution-service** (execution manager layer)
- **strategy-service** (if split in future)
- **live trading services** (position monitor, risk monitor, etc.)

---

## 📊 Updated Epic 1 Metrics

| Metric            | Original | Updated | Change                |
| ----------------- | -------- | ------- | --------------------- |
| Tasks             | 4        | 5       | +1 (Simulation Layer) |
| Subtasks          | 10       | 17      | +7                    |
| Estimated Hours   | 34.5h    | 50.5h   | +16h                  |
| Critical Subtasks | 1        | 2       | +1 (matching engine)  |
| Review Required   | 2        | 3       | +1 (matching engine)  |

### New Issues Created

- Issues #153-#174 (22 total)
- Original issues #56-#69 remain valid (duplicate epic for comparison)

---

## ✅ Alignment Verified

- [x] Covers Layer 3 (Exchange Interface) only
- [x] Respects existing Layer 1-2 architecture in execution-service
- [x] Includes both live and simulation adapters
- [x] Uses env var for mode selection
- [x] Integrates existing matching engine
- [x] Maintains batch-live symmetry principles

---

**Last Updated:** 2026-02-12 **Validated With:** User architecture clarification **Related Issues:** #153-#174 (Epic 1
updated breakdown)
