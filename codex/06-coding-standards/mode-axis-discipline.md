---
scope: [engineer, admin]
created: 2026-05-14
plan: plans/active/batch_live_symmetry_2026_05_10.md Tab 1
---

# Mode-Axis Discipline

> Single SSOT for every mode enum in the system, the cartesian-product table of valid combinations, and the anti-pattern
> list for mode-conditional code. Pre-audit source: `batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab1`.

---

## §1 The four mode axes

Four independent axes control system behaviour. Each axis is a `StrEnum` in UAC; each is injected as an env var by the
deployment system and received by services through `UnifiedCloudConfig` (never via `os.getenv()`).

### RuntimeMode — service execution mode

**File**: `unified_api_contracts.internal.modes.RuntimeMode` **Env var**: `RUNTIME_MODE` (default: `live`)

| Value   | Meaning                                                       |
| ------- | ------------------------------------------------------------- |
| `live`  | Streaming / event-driven: subscribe to Redis Streams + PubSub |
| `batch` | Historical: read GCS Parquet → compute → write GCS Parquet    |

`RuntimeMode` is the PRIMARY axis that controls data transport and compute scheduling. All other axes are refinements or
orthogonal concerns.

### OperationalMode — what the service is doing with fills

**File**: `unified_api_contracts.internal.modes.OperationalMode` **Env var**: `OPERATIONAL_MODE` (default: `live`)

| Value      | Meaning                                                                        |
| ---------- | ------------------------------------------------------------------------------ |
| `live`     | Automated strategy execution — strategy-service → execution-service real fills |
| `manual`   | Operator-initiated instructions via API (manual trading panel)                 |
| `backtest` | Historical replay — batch mode, no live execution                              |
| `paper`    | Live market data, simulated execution — no real fills                          |

`OperationalMode` is relevant only at the execution boundary. Data pipelines (MTDS, MDPS, features-service) are
`OperationalMode`-agnostic — they serve the same data regardless.

### BatchExecutionMode — how batch fills are simulated

**File**: `unified_api_contracts.internal.execution.BatchExecutionMode` **Set by**: batch run config, NOT an env var
(varies per strategy run)

| Value       | Meaning                                                                                |
| ----------- | -------------------------------------------------------------------------------------- |
| `benchmark` | Always fill at requested price. Zero execution alpha. Isolates strategy P&L.           |
| `simulated` | Realistic fills: commission, L2 order-book depth (CeFi), AMM slippage (DeFi), latency. |

`BatchExecutionMode` only applies when `RuntimeMode = batch`. In live mode, real venue fills replace the matching engine
entirely — `BatchExecutionMode` has no runtime effect.

### StrategyMaturityPhase — strategy lifecycle stage

**File**: `unified_api_contracts.internal.domain.strategy_service.lifecycle.StrategyMaturityPhase` **Set by**: strategy
catalogue / promotion gates (NOT a deployment env var)

| Value                 | Rank | Meaning                                       |
| --------------------- | ---- | --------------------------------------------- |
| `smoke`               | 0    | Pre-backtest smoke, mock data only            |
| `backtest_minimal`    | 1    | < 1yr historical backtest — not viable yet    |
| `backtest_1yr`        | 2    | 1-year backtest — minimum viability threshold |
| `backtest_multi_year` | 3    | Multi-year backtest, extended track           |
| `paper_1d`            | 4    | First-day paper trading                       |
| `paper_14d`           | 5    | 14-day paper trading                          |
| `paper_stable`        | 6    | Extended paper, promotion-ready               |
| `live_early`          | 7    | Initial live, small capital                   |
| `live_stable`         | 8    | Mature live                                   |
| `retired`             | -1   | Terminal — orthogonal to the forward ladder   |

`StrategyMaturityPhase` drives the strategy catalogue display + deployment-UI lifecycle tabs. It does NOT control which
data pipeline runs — `RuntimeMode` does that.

---

## §2 Cartesian product — valid combinations

Not all combinations are meaningful. The table below shows valid runtime combinations for the May-23 scope:

| RuntimeMode | OperationalMode | BatchExecutionMode | MaturityPhase | Description                             | May-23 in scope? |
| ----------- | --------------- | ------------------ | ------------- | --------------------------------------- | ---------------- |
| batch       | backtest        | benchmark          | backtest\_\*  | Strategy P&L isolation (no exec alpha)  | ✅ YES           |
| batch       | backtest        | simulated          | backtest\_\*  | Execution alpha measurement             | ✅ YES           |
| batch       | backtest        | benchmark          | paper\_\*     | Paper-deploy calibration run            | ✅ YES           |
| live        | paper           | N/A                | paper\_\*     | Paper-deploy: real data, sim fills      | ✅ YES           |
| live        | live            | N/A                | live_early    | Initial live with real capital          | ✅ YES (May-23)  |
| live        | live            | N/A                | live_stable   | Mature live                             | ⏳ POST-CUTOVER  |
| batch       | backtest        | benchmark          | smoke         | Smoke test — mock data                  | ✅ YES (CI)      |
| live        | manual          | N/A                | any           | Operator-initiated trade                | ✅ YES           |
| live        | live            | benchmark          | any           | ILLEGAL — live doesn't use matching eng | ❌ FORBIDDEN     |
| batch       | live            | any                | any           | ILLEGAL — batch + live op is incoherent | ❌ FORBIDDEN     |
| live        | backtest        | any                | any           | ILLEGAL — backtest is a batch concern   | ❌ FORBIDDEN     |

**Rule**: `BatchExecutionMode` is only consulted when `RuntimeMode = batch`. `OperationalMode = backtest` implies
`RuntimeMode = batch`. `OperationalMode = live | paper` implies `RuntimeMode = live`.

---

## §3 Where mode-conditional code belongs — the seam rule

Mode differences belong ONLY at the 4 seams defined in
[`batch-live-architecture.md §2`](../04-architecture/batch-live-architecture.md):

1. **Data source seam** — `RuntimeMode` branch; batch reads GCS, live subscribes to Redis Stream / PubSub.
2. **Feature seam** — `RuntimeMode` branch; batch loads from GCS, live calls embedded UTL package.
3. **ML inference seam** — `RuntimeMode` branch; batch reads GCS prediction Parquet, live subscribes to topic.
4. **Execution fills seam** — `BatchExecutionMode` branch (batch only); `OperationalMode` branch (live: real vs paper).

**Everywhere else**: mode-conditional branches (`if mode == "live":`) inside business logic are FORBIDDEN.
`StrategyMaturityPhase` drives display logic and promotion gates only — never data-path branching.

---

## §4 Anti-patterns

### AP-1 — Mode conditional inside business logic

```python
# FORBIDDEN — business logic must not branch on RuntimeMode
if runtime_mode == "live":
    signal = compute_live_signal(tick)
else:
    signal = compute_batch_signal(bar)
```

Fix: put the mode branch at the seam (data source adapter or feature input adapter). The `compute_signal()` function
receives a canonical `FeatureVector` regardless of which seam produced it.

### AP-2 — `LIVE_*` event-prefix members

```python
# FORBIDDEN — event names must not encode mode
class VMEventType(StrEnum):
    LIVE_STARTED = "LIVE_STARTED"
    BATCH_STARTED = "BATCH_STARTED"
```

Fix: use a single event type + a `mode` field on the payload. Mode is a runtime attribute, not a schema dimension. Block
G1 (post-cutover): rename to `STARTED` + add `mode: RuntimeMode` field to the event schema.

### AP-3 — UI `RuntimeMode` redeclarations

```typescript
// FORBIDDEN — never redeclare what UAC owns
type ExecutionMode = "live" | "batch"; // in unified-trading-system-ui/context/...
```

Fix: import from UAC schema (Tab 3 ships this as an L3 violation fix — UAC re-exports `RuntimeMode` from UTL canonical;
UI imports from UAC). SSOT: `unified_api_contracts.internal.modes.RuntimeMode`.

### AP-4 — `BatchExecutionMode` as a CLI flag that changes business logic

```bash
# FORBIDDEN — BatchExecutionMode is config, not CLI-controlled business logic
python -m strategy_service --mode batch --exec-mode benchmark --special-path ...
```

Fix: `BatchExecutionMode` is a run-config field (`strategy_config.batch_execution_mode`). The strategy engine reads it
at run-start to select the matching engine. No "special paths" — same code, different matcher.

### AP-5 — Using `OperationalMode` to gate data-pipeline code

```python
# FORBIDDEN — data pipelines are OperationalMode-agnostic
if operational_mode == "live":
    write_to_live_bucket()
else:
    write_to_batch_bucket()
```

Fix: GCS bucket path is governed by `pipeline_mode` (the PipelineMode enum from UAC
`canonical/crosscutting/pipeline_mode.py`), NOT by `OperationalMode`. `OperationalMode` is an execution-boundary
concern, not a data-path concern.

### AP-6 — `StrategyMaturityPhase` controlling data pipeline execution

```python
# FORBIDDEN — MaturityPhase is a catalogue concept, not a pipeline gate
if strategy.maturity_phase == "live_stable":
    start_live_pipeline()
```

Fix: pipeline gate is operator-approval + deployment config. `StrategyMaturityPhase` informs the UI + promotion gates;
it does not start or stop pipeline services.

---

## §5 J1 helper — phase-to-mode derivation (DEFERRED post-cutover)

The `J1` helper (`runtime_mode_for_phase`) derives the canonical `(RuntimeMode, BatchExecutionMode, OperationalMode)`
triplet from a `StrategyMaturityPhase`. Design stub lives at
`unified_api_contracts/internal/domain/strategy_service/lifecycle.py:91-116`.

**DEFERRED**: wire-in is post-cutover per defaults #2. The function signature is locked; implementation pending.

```python
def runtime_mode_for_phase(
    phase: StrategyMaturityPhase,
) -> tuple[RuntimeMode, BatchExecutionMode, OperationalMode]:
    """Derive canonical mode triplet from maturity phase.

    SMOKE/BACKTEST_* → (batch, benchmark, backtest)
    PAPER_* → (live, N/A, paper)
    LIVE_* → (live, N/A, live)
    RETIRED → raises ValueError
    """
    ...  # implementation deferred post-cutover
```

Call site: `StrategyCatalogueSurface.tsx:85` `synthesiseMaturity()` calls this helper to derive the display triplet
(pre-audit Manifest 1). Wire-in deferred to post-cutover.

---

## §6 QG enforcement

| STEP | What it catches                                                                        | Status (2026-05-14)                    |
| ---- | -------------------------------------------------------------------------------------- | -------------------------------------- |
| L1   | Data*type enum contains `LIVE*`/`BATCH\_` prefixed members                             | DAY-1 ENABLE (0 violations)            |
| L2   | Mode-conditional branches outside seams (~21 violations)                               | FIX-REQUIRED before enable             |
| L3   | `RuntimeMode` declared outside UTL canonical (2 violations: UAC re-export + UI redecl) | FIX-REQUIRED before enable             |
| L4   | `LIVE_*` event-prefix members (~12 violations)                                         | **DEFERRED post-cutover** (Block G1)   |
| L5   | Unified DataType enum (no per-mode fork)                                               | DAY-1 ENABLE (0 violations)            |
| L6   | `BatchExecutorFactory` not yet shipped                                                 | **DEFERRED** until Tab 2 factory ships |
| L7   | `record_captured()` callsites missing `assert_available_at_present`                    | ongoing sweep                          |

Enforcement file: `scripts/quality-gates-base/base-service.sh`. STEPs L1/L5 enable on Day-1 (zero violations); L2/L3
enable after fix-batch lands (Tab 3). L4/L6 post-cutover.

---

## §7 Cross-references

- **Batch/live invariant**:
  [`../04-architecture/batch-live-architecture.md`](../04-architecture/batch-live-architecture.md)
- **Modes UAC source**: `unified_api_contracts.internal.modes` (all 4 axes)
- **Pipeline-mode partition** (data-path, orthogonal to these axes):
  [`../02-data/pipeline-mode-partition.md`](../02-data/pipeline-mode-partition.md)
- **QG STEPs L1-L7**: [`quality-gates.md`](quality-gates.md) § "STEP entries — batch/live symmetry"
- **Pre-audit manifest**: `plans/questions/batch_live_design_symmetry_preaudit_2026_05_10.md § 1.Tab1`
- **J1 helper (deferred)**: `unified_api_contracts/internal/domain/strategy_service/lifecycle.py:91-116`
