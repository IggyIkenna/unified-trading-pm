---
doc_type: issue
title: "codex-py schema-provenance check mis-applied to unified-trading-library (library repo) — noisy log_warn on every QG run (P2; NOT a ship blocker)"
summary: >-
  P2 (corrected 2026-08-19T21:3xZ). `check_schema_provenance.py` flags ~30 local
  BaseModel/TypedDict/dataclass definitions across `unified_trading_library/` (e.g.
  `walk_forward.py:WalkForwardReport`, `models/schemas.py:*`, `ml/models.py:*`) as "should import from UAC or UIC".
  In `base-library.sh`'s codex block this check is a `log_warn` — it does NOT increment the gate's V count and does
  NOT block `quality-gates.sh`. It is mis-applied: UTL is the type-DEFINING library (services import contract types
  from UAC/UIC; UTL's internal data structures — performance metrics, reconcile results, feature-calculator outputs —
  are legitimately local). INITIAL REPORT (21:2xZ) claimed this check blocks UTL ships — CORRECTED: the actual QG red
  was a hardcoded prod project ID in a regression test (`bucket = "market-data-tick-cefi-prd-central-element-323112"`
  in `test_manifest_consolidator.py`), which trips the "Hardcoded prod project ID in tests" check. Fixed by renaming to
  `-prd-test-project` (UTL@af783d92).
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-library]
scope: [engineer, admin]
tags: [quality-gates, codex, schema-provenance, quality-of-life, infrastructure]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
context_scope:
  [
    /codex/06-coding-standards/quality-gates.md,
    scripts/validation/check_schema_provenance.py,
    scripts/quality-gates-base/base-library.sh,
  ]
created: 2026-08-19
author: claude-agent
source: "slot-4 worker (manifest_consolidator todo-2), quality-gates.sh QG-red investigation on UTL commit d8f05a5d, 2026-08-19"
priority: P2
parent_epic: security_and_cross_cutting_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
depends_on: []
locked_by:
resolved_by:
---

# codex-py schema-provenance check mis-applied to UTL — 2026-08-19

## What I found

1. **`check_schema_provenance.py` flags ~30 local schema types across UTL on every `quality-gates.sh` run — as a
   WARNING, not a failure.** In `unified-trading-pm/scripts/quality-gates-base/base-library.sh`'s `[5] CODEX COMPLIANCE`
   block, the check (`validation/check_schema_provenance.py --repo <pkg>`) is invoked in an `if/else` that logs
   `log_success` on pass / `log_warn` on fail — it does **NOT** do `V=$(( V + 1 ))`. So it never fails the gate. The
   `run_codex_py_checks.py` orchestrator that reports `schema-provenance: FAIL (rc=1)` / `__CODEX_PY_FAILURES__=2` is a
   base-SERVICE.sh mechanism; base-library.sh does not invoke it.
2. **The initial "QG red" diagnosis was WRONG.** The full `quality-gates.sh` run on `d8f05a5d` actually failed on a
   DIFFERENT, V-counted check: `❌ Hardcoded prod project ID in tests — use 'test-project'` — caused by
   `tests/unit/test_manifest_consolidator.py: bucket = "market-data-tick-cefi-prd-central-element-323112"` (the real
   prod bucket name). The schema-provenance offender list was printed as a warning in the same run and misread as the
   cause. **This is a first-person misdiagnosis, corrected here: the blocker was my own test, fixed by renaming the
   bucket to `market-data-tick-cefi-prd-test-project` (UTL@af783d92).**
3. **The underlying observation still holds (P2): the schema-provenance check is mis-applied to a library repo.** UTL
   DEFINES the types services consume; its internal dataclasses are not UAC-contract types. The check is written for
   SERVICE repos that should import contract types from UAC/UIC. It produces a noisy `log_warn` on every UTL QG run.

## Why it matters

- P2 quality-of-life only: the check adds warning noise to every UTL QG run and flags legitimate internal types.
  It does not block shipping (verified: the QG's V-counted failure was the hardcoded project ID, now fixed).
- No data-correctness or shipping impact.

## Recommended decision

- Optionally scope the schema-provenance check to skip library repos (e.g. a `--skip-schema-provenance` flag wired in
  base-library.sh's codex block), or add a ratchet baseline for UTL's pre-existing internal types so new (service-style)
  violations are still caught. P2; do whenever convenient.

## Todos

- [ ] [BACKEND] P2. **Scope the codex-py `schema-provenance` check out of library repos (or baseline UTL's internal
      types)** so UTL's QG run stops warning on ~30 legitimate internal dataclasses. Wire `--skip-schema-provenance` in
      `base-library.sh`'s codex block (or an equivalent per-repo escape), verify `quality-gates.sh` on UTL no longer
      prints the warning. (repo: unified-trading-pm, scripts/quality-gates-base/base-library.sh). Done when: UTL QG run
      is clean of the schema-provenance warning.
- [x] ✅ [DATA-ENG] P1. **Fix the actual UTL QG red (hardcoded prod project ID in `test_manifest_consolidator.py`)** —
      the regression test used `bucket = "market-data-tick-cefi-prd-central-element-323112"`, tripping "Hardcoded prod
      project ID in tests". Renamed to `market-data-tick-cefi-prd-test-project` — `unified-trading-library@af783d92`.

## Progress Log

- **2026-08-19T21:2xZ (slot-4 worker, manifest_consolidator todo-2)**: filed as a P1 blocking issue (wrong diagnosis —
  attributed the QG red to the schema-provenance check).
- **2026-08-19T21:3xZ (slot-4 worker)**: CORRECTED. The schema-provenance check is a `log_warn` in base-library.sh and
  does not block. The actual QG failure was my own test's hardcoded prod bucket name; fixed in `af783d92`. This doc
  demoted to P2 (schema-provenance mis-application to a library repo remains a quality-of-life finding). Repo-blocker
  RB-959c7b8d was resolved via watcher_green and is moot.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
