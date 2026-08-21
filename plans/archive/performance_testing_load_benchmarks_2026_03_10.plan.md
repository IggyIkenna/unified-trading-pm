---
doc_type: plan
title: performance-testing-load-benchmarks-2026-03-10
summary:
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    execution-service,
    instruments-service,
    market-tick-data-service,
    strategy-service,
    system-integration-tests,
    unified-trading-pm,
  ]
scope: [engineer, admin]
tags: []
related: []
created: "2026-03-10"
overview:
  Establish system-wide performance baselines, load benchmarks, and resource limits across all critical paths before
  live trading; add CI gates for latency and throughput regressions.
type: code
epic: epic-code-completion
completion_gates: { code: C5, deployment: none, business: none }
repo_gates:
  - {
      repo: execution-service,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: system-integration-tests,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: unified-trading-pm,
      code: C1,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
  - {
      repo: unified-trading-codex,
      code: C0,
      deployment: none,
      business: none,
      readiness_note:
        "DR N/A: code-completion epic scope; deployment managed by dedicated infra plans. BR N/A: no commercial sign-off
        required for a code plan.",
    }
depends_on: [phase3_service_hardening_integration, mock_data_dev_project_seeding_2026_03_10]
todos:
  - {
      id: p0-define-targets,
      content:
        "Create unified-trading-/codex/06-coding-standards/performance-targets.md with latency, throughput, and resource
        targets",
      status: done,
      note: DONE 2026-03-11,
    }
  - {
      id: p1-latency-histogram,
      content: Add p50/p95/p99 latency histograms and assertions to existing execution-service benchmarks,
      status: done,
      note: DONE 2026-03-11,
    }
  - {
      id: p1-e2e-latency,
      content: Create execution-service/benchmarks/test_e2e_latency.py for order submission p99 ≤ 500ms,
      status: done,
      note:
        "DONE 2026-03-11 — test_e2e_latency.py created with 100-iteration histogram, p99<=500ms and p50<=200ms
        assertions",
    }
  - {
      id: p2-sit-performance-dir,
      content: Create system-integration-tests/tests/performance/ with 7 test files,
      status: done,
      note: DONE 2026-03-11,
    }
  - {
      id: p2-load-scenarios,
      content: Add normal/peak/sustained load scenarios to conftest_performance.py,
      status: done,
      note: DONE 2026-03-11,
    }
  - {
      id: p2-resource-leak-detection,
      content: Add ResourceMonitor to conftest_performance.py for memory leak detection,
      status: done,
      note: DONE 2026-03-11 — ResourceMonitor class and resource_monitor fixture added to conftest_performance.py,
    }
  - {
      id: p3-gha-perf-job,
      content: Create system-integration-tests/.github/workflows/performance-test.yml for nightly CI,
      status: done,
      note:
        DONE 2026-03-11 — nightly 2am UTC cron + workflow_dispatch; uploads artifacts to performance-results-<run_id>,
    }
  - {
      id: p3-regression-detection,
      content: Create compare_benchmark_baseline.py and commit baselines/baseline.json,
      status: done,
      note:
        DONE 2026-03-11 — CLI tool compares p50/p95/p99/max vs baseline; fails CI if >20% regression; baseline.json
        seeded from performance-targets.md,
    }
  - {
      id: p4-memory-profiling,
      content: Create unified-trading-pm/scripts/ops/profile-memory.sh,
      status: done,
      note: DONE 2026-03-11 — memray flamegraph + psutil RSS sampling fallback; asserts <10% growth over duration,
    }
  - {
      id: p4-cpu-profiling,
      content: Create unified-trading-pm/scripts/ops/profile-cpu.sh,
      status: done,
      note: DONE 2026-03-11 — py-spy speedscope flamegraph + cProfile fallback with pstats top-50 report,
    }
isProject: false
---

# Plan: Performance Testing, Load Benchmarks & Resource Baselines

status: active priority: P1 owner: backend/infra target: 2026-03-21

## Context

`execution-service/benchmarks/` has 4 benchmark files covering algo/pipeline/matching/orchestrator performance in
isolation. `market-tick-data-service` and `instruments-service` have individual perf tests. No system-wide performance
suite exists. The `master_pre_deployment_plan_chain` success gate requires ≤500ms order submission latency, but no
automated test validates this continuously. Before live trading, the system must have measured baselines for every
critical path under: (a) normal load, (b) peak load (5×), (c) sustained peak (1 hour), with confirmed no resource leaks
or regressions.

---

## Phase 0: Performance targets

### P0.1 — Define targets ✅ DONE 2026-03-11

File: `unified-trading-/codex/06-coding-standards/performance-targets.md` (new)

**Latency targets (p50 / p95 / p99 / max):**

| Path                                               | p50   | p95    | p99    | max    |
| -------------------------------------------------- | ----- | ------ | ------ | ------ |
| Order submission (execution-service → venue mock)  | 200ms | 400ms  | 500ms  | 1000ms |
| Signal generation (strategy-service, full cycle)   | 500ms | 800ms  | 1000ms | 2000ms |
| Feature computation (any single service, 1 symbol) | 100ms | 300ms  | 500ms  | 1000ms |
| ML inference (ml-inference-api, single prediction) | 50ms  | 150ms  | 250ms  | 500ms  |
| End-to-end signal-to-order (strategy → execution)  | 800ms | 1500ms | 2000ms | 5000ms |
| GCS read (feature batch, 1 day, 1 symbol)          | 500ms | 1000ms | 2000ms | 5000ms |
| PubSub publish (single event)                      | 10ms  | 50ms   | 100ms  | 200ms  |

**Throughput targets:**

| Component           | Target                                           |
| ------------------- | ------------------------------------------------ |
| Tick ingestion      | ≥1000 ticks/second per venue                     |
| PubSub events       | ≥500 events/second sustained                     |
| Backfill            | ≥1M ticks/hour per venue (with Tardis/Databento) |
| Feature computation | ≥100 instrument-days/second                      |
| ML inference batch  | ≥10 predictions/second                           |

**Resource targets (per service, per Cloud Run instance):**

| Service tier               | Max CPU | Max memory | Max GCS ops/min |
| -------------------------- | ------- | ---------- | --------------- |
| Data services (MTDH, MDPS) | 80%     | 2GB        | 1000            |
| Feature services (all 8)   | 70%     | 1.5GB      | 500             |
| ML inference               | 90%     | 4GB        | 100             |
| Strategy service           | 60%     | 1GB        | 200             |
| Execution service          | 70%     | 2GB        | 300             |

---

## Phase 1: Extend existing execution-service benchmarks

### P1.1 — Add latency histogram to existing benchmarks ✅ DONE 2026-03-11

Files: `execution-service/benchmarks/test_algorithm_performance.py`,
`execution-service/benchmarks/test_matching_engine_performance.py`

Add to each benchmark:

- Latency histogram: p50, p95, p99 calculated from 100+ iterations
- Pass/fail assertion: `assert p99 <= TARGET_P99_MS, f"p99={p99}ms > {TARGET_P99_MS}ms"`
- Targets imported from `performance-targets.md` (machine-readable YAML section)

### P1.2 — E2E order latency benchmark

File: `execution-service/benchmarks/test_e2e_latency.py` (new)

```python
async def test_order_submission_p99_within_500ms(mock_venue):
    """
    Measure: time from order dict creation → order accepted by mock venue.
    Mock venue responds in 0ms to isolate our code latency.
    100 iterations → histogram → assert p99 ≤ 500ms.
    """
    latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        await execution_engine.submit_order(test_order, venue="mock")
        latencies.append((time.perf_counter() - t0) * 1000)
    p99 = statistics.quantiles(latencies, n=100)[98]
    assert p99 <= 500, f"p99={p99:.1f}ms exceeds 500ms target"
```

---

## Phase 2: System-level performance test suite

### P2.1 — SIT performance directory ✅ DONE 2026-03-11

Directory: `system-integration-tests/tests/performance/`

```
performance/
├── conftest_performance.py        # shared fixtures: mock venues, mock GCS, metric collectors
├── test_execution_latency.py      # order submission under load
├── test_feature_throughput.py     # feature computation throughput per service
├── test_ml_inference_latency.py   # inference p50/p95/p99
├── test_tick_ingestion_throughput.py  # tick ingestion rate per venue
├── test_e2e_signal_to_order.py    # full signal-to-order pipeline latency
├── test_backfill_throughput.py    # historical data load speed
└── test_pubsub_throughput.py      # event bus throughput
```

### P2.2 — Load scenarios (applied to every test) ✅ DONE 2026-03-11

```python
# In conftest_performance.py
LOAD_SCENARIOS = {
    "normal": {"multiplier": 1, "duration_s": 60},
    "peak": {"multiplier": 5, "duration_s": 600},      # 10 min burst
    "sustained": {"multiplier": 5, "duration_s": 3600}, # 1 hour — nightly CI only
}
```

Mark slow tests: `@pytest.mark.slow` for peak/sustained scenarios. CI gate: only `normal` scenario in PR CI; `peak` in
nightly; `sustained` in weekly.

### P2.3 — Resource leak detection

```python
# In conftest_performance.py
class ResourceMonitor:
    def __init__(self) -> None:
        self._baseline_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss

    def assert_no_memory_leak(self, tolerance_pct: float = 10.0) -> None:
        current_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        growth_pct = (current_rss - self._baseline_rss) / self._baseline_rss * 100
        assert growth_pct <= tolerance_pct, f"Memory grew {growth_pct:.1f}% > {tolerance_pct}% threshold"
```

Apply to all performance tests.

---

## Phase 3: GHA performance CI job

### P3.1 — Performance workflow

File: `system-integration-tests/.github/workflows/performance-test.yml` (new)

```yaml
name: performance-tests
on:
  schedule:
    - cron: "0 2 * * *" # nightly at 02:00 UTC
  workflow_dispatch:

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run normal load performance tests
        run: |
          pytest tests/performance/ -m "not slow" \
            --benchmark-json=benchmark_results.json \
            -q
      - name: Compare vs baseline
        run: python scripts/compare_benchmark_baseline.py benchmark_results.json baselines/baseline.json
      - name: Upload results
        uses: actions/upload-artifact@v4
        with:
          name: benchmark-results
          path: benchmark_results.json
```

### P3.2 — Regression detection

File: `system-integration-tests/scripts/compare_benchmark_baseline.py`

- Load current results and stored `baselines/baseline.json`
- Alert (Telegram) if any metric regresses >20% vs baseline
- Update baseline if all metrics improved or unchanged

File: `system-integration-tests/benchmarks/baseline.json` — committed baseline values

---

## Phase 4: Resource profiling scripts

### P4.1 — Memory profiling

File: `unified-trading-pm/scripts/ops/profile-memory.sh`

```bash
# Runs execution-service live_mode for 30 minutes with realistic mock data
# Uses py-spy or tracemalloc to generate heap snapshot
# Assert: heap size at minute 30 ≤ 110% of heap size at minute 5 (no unbounded growth)
```

### P4.2 — CPU profiling

File: `unified-trading-pm/scripts/ops/profile-cpu.sh`

```bash
# Runs order submission path 1000 times under cProfile
# Generates: execution_service_cpu_flamegraph.svg
# Target: order submission hot path ≤ 50% of wall time at p95 load
```

---

## Verification Gates

- [ ] `pytest system-integration-tests/tests/performance/ -m "not slow"` exits 0
- [ ] All p99 latencies within targets in `performance-targets.md`
- [ ] No memory growth >10% over 30-minute soak test
- [ ] GHA performance job added and passing in nightly CI
- [ ] `baselines/baseline.json` committed with initial measurements

## Files Created / Modified

- `unified-trading-/codex/06-coding-standards/performance-targets.md` (new)
- `execution-service/benchmarks/test_e2e_latency.py` (new)
- `execution-service/benchmarks/test_algorithm_performance.py` (extend with assertions)
- `system-integration-tests/tests/performance/` (new directory, 8 files)
- `system-integration-tests/.github/workflows/performance-test.yml` (new)
- `system-integration-tests/benchmarks/baseline.json` (new)
- `system-integration-tests/scripts/compare_benchmark_baseline.py` (new)
- `unified-trading-pm/scripts/ops/profile-memory.sh` (new)
- `unified-trading-pm/scripts/ops/profile-cpu.sh` (new)

## Dependencies

- `phase3_service_hardening_integration.md` (services must be hardened before benchmarking)
- `e2e_smoke_and_portable_backtests.md` Layer 3 (infra live for system tests)
- `mock_data_dev_project_seeding_2026_03_10.md` (fixture data for load tests)
