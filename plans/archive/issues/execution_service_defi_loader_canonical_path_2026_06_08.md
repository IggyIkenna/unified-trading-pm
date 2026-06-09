---
title: "execution-service DeFi backtest loader — canonical path candidate missing (LDR v2 RED)"
created: 2026-06-08
assigned_vm: planning
parent_epic: master_to_live_defi_2026_05_23
estimate_class: refactor
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.12
source:
  - "execution-service quality-gates-v2 on live-defi-rollout run 27113589926 (sha c71484d6) — FAILED"
  - "introduced by execution-service@c71484d6 (slot-2·laptop): fix(execution): DeFi backtest loader reads canonical
    pipeline_mode-aware path first"
locked_by: live-defi-rollout
priority: P2
status: resolved
resolved: 2026-06-09
resolution: ACKED-INTO-CODE — execution-service@abfadd803 (loaders/defi.py:70 adds chain= kwarg, fixes StopIteration); regression tests tests/unit/test_loaders_defi_canonical_paths.py::test_{swaps,liquidity}_canonical_path_precedes_legacy
---

## What I found

`execution-service` `quality-gates-v2` on `live-defi-rollout` is RED (run 27113589926, head `c71484d6`). Two unit tests
fail with **`StopIteration`**:

- `tests/unit/test_loaders_defi_canonical_paths.py::test_swaps_canonical_path_precedes_legacy`
- `tests/unit/test_loaders_defi_canonical_paths.py::test_liquidity_canonical_path_precedes_legacy`

Both fail at:

```python
canonical_idx = next(i for i, p in enumerate(candidates) if f"data_type={_CANONICAL_SWAP_DATA_TYPE}" in p)
```

`StopIteration` = the candidate list returned by `_candidates(...)` (the DeFi backtest loader's path-candidate
generator) contains **no path with the canonical `data_type=<canonical>` segment**. So the canonical pipeline_mode-aware
path that commit `c71484d6` was supposed to emit FIRST is not being generated at all.

This is the failure for the exact feature `c71484d6` introduced ("loader reads canonical pipeline_mode-aware path first
(legacy fallback)"). **Strong lead: this is a CODE bug** (the loader's canonical-path branch is incomplete / the
constant wiring is off), not a stale test — but the worker MUST diagnose test-vs-code per the rules (read both the
test's `_CANONICAL_SWAP_DATA_TYPE` / `_candidates` helper AND the loader's path-building code; fix the side that's
actually wrong).

## Why it matters

execution-service LDR is RED → it blocks the LDR→staging promote PR's `quality-gates-v2`, which feeds the SIT gate (the
cascade). It is the live execution-service regression as of 2026-06-08 03:09Z.

## Coordination

`c71484d6` is **slot-2·laptop's** in-flight work — coordinate / don't stomp a live edit. The commit is already on LDR,
so the fix is additive (complete the canonical-path emission OR correct the test). Worker: declare the
`execution-service` `executor`/loader path-building surface in your plan before starting.

## Status

- [ ] [TEST] P0. Diagnose + fix the `test_loaders_defi_canonical_paths.py` `StopIteration` (canonical `data_type=`
      candidate not emitted by the loader). Read both the test (`_CANONICAL_SWAP_DATA_TYPE`, `_candidates`) and the
      execution-service DeFi backtest loader path-builder (the code `c71484d6` added). Fix the wrong side, ship via
      `quality-gates.sh`-green → `quickmerge --agent --files`, verify `execution-service` `quality-gates-v2` GREEN on
      `live-defi-rollout`. repo: execution-service. Cold-start: read `cursor-configs/SUB_AGENT_MANDATORY_RULES.md`
      first. (assigned_vm `planning` is a PRAGMATIC override — the execution/defi epic VM that should own this is not
      running; this is the only live VM. Reassign if an execution VM comes up.)
