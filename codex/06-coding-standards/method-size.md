---
title: Method Size Rule
scope: [engineer]
owner: ikenna
status: reference
codified: 2026-05-19
sources:
  - plans/active/work_split_2026_05_19_ikenna.md (Slot 4 items 11-14, Batch-32)
---

# Method Size Rule

**Rule**: Every public method MUST be ≤50 lines. Every private helper SHOULD be ≤50 lines.

**Enforcement**: `FUNCTION_SIZE_EXTRA_EXCLUDES` in each service's `quality-gates.sh`. Files in the allowlist are tracked
technical debt with a named owner + batch (e.g. `Batch-32`). Allowlist must shrink monotonically — adding a new entry
requires a TODO comment with owning batch name.

**Pattern for remediation** (established Batch-32, 2026-05-19, execution-service):

1. Read the >50L method; identify logical phases (setup, iteration per item, per-phase transformation, finalization).
2. Extract each phase to a `_private_helper_method()` on the same class (descriptive names — not `_part1`).
3. Public method becomes a thin orchestrator ≤50 lines calling the helpers.
4. No behaviour change; all tests must pass; run `bash scripts/quality-gates.sh`.
5. Remove the file from `FUNCTION_SIZE_EXTRA_EXCLUDES` in the same commit.

**Techniques for hard cases**:

- Parameter-heavy signatures: introduce a frozen dataclass or `NamedTuple` to bundle >5 params that recur across
  helpers.
- `# fmt: off` / `# fmt: on` around irreducibly-long but semantically atomic blocks (e.g. a single multi-line dict
  literal).
- Nested inner functions that are only called once: hoist to private class methods.

**Batch sweep order** (as of 2026-05-19):

- `execution-service`: Batch-32 COMPLETE — allowlist `()` at `execution-service@23d8401c6`
- `strategy-service`: next stream — scan `FUNCTION_SIZE_EXTRA_EXCLUDES` for remaining files
- `unified-trading-api`, `ml-inference-service`, `ml-training-service`: subsequent streams
