---
doc_type: issue
title: "unified-trading-library quality-gates codex-py schema-provenance check is RED (no baseline) — blocks ALL UTL ships incl. the consolidator phantom-lock fix"
summary: >-
  LIVE, BLOCKING (as of 2026-08-19T21:2xZ). `bash scripts/quality-gates.sh` in unified-trading-library fails at the
  codex-py `schema-provenance` sub-check ("Codex compliance FAILED: 1 violations (max allowed: 0)"). The check
  (`unified-trading-pm/scripts/validation/check_schema_provenance.py`, wired via
  `unified-trading-pm/scripts/quality_gates/run_codex_py_checks.py`) flags ~30 local `BaseModel`/`TypedDict`/`dataclass`
  definitions across `unified_trading_library/` (e.g. `walk_forward.py:WalkForwardReport`, `per_leaf_failure.py:PerLeafFailureRouter`,
  `models/schemas.py:DownloadTarget/OrchestrationResult/ValidationConfig`, `ml/models.py:*`, `core/error_handling.py:*`, …)
  as "should import from UAC or UIC". The check has NO baseline (returns 1 if ANY local schema types exist), so it fails
  on the pre-existing corpus. The offenders pre-date the discovering worker's commit (`git show HEAD~1:unified_trading_library/walk_forward.py`
  carries `class WalkForwardReport`; the worker's own commit `d8f05a5d` touched only `manifest_consolidator.py` + its test,
  neither flagged). This is the direct blocker for shipping the consolidator phantom-lock guard fix
  (`manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md` todo 2) under the green-tree rule.
status: open
nature: issue
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-library]
scope: [engineer, admin]
tags: [quality-gates, codex, schema-provenance, ci, blocking, infrastructure]
related:
  [
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/codex_violations_ratchet_to_five_2026_06_10.md,
    /plans/active/issues/manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md,
    /codex/06-coding-standards/quality-gates.md,
  ]
context_scope:
  [
    /codex/06-coding-standards/quality-gates.md,
    unified-trading-pm/scripts/validation/check_schema_provenance.py,
  ]
created: 2026-08-19
author: claude-agent
source: "slot-4 worker (manifest_consolidator todo-2), quality-gates.sh run on commit d8f05a5d, 2026-08-19"
priority: P1
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

# unified-trading-library codex-py schema-provenance QG red — 2026-08-19

## What I found

1. **`quality-gates.sh` fails at the codex-py `schema-provenance` sub-check, pre-existing.** A full Pass-1 QG run on
   unified-trading-library at `d8f05a5d` exited 1 with `❌ Codex compliance FAILED: 1 violations (max allowed: 0)`. The
   direct invocation
   (`unified-trading-pm/scripts/quality_gates/run_codex_py_checks.py --repo-path <utl> …`) reports
   `[codex-py] schema-provenance: FAIL (rc=1)` / `__CODEX_PY_FAILURES__=2` and prints ~30 offender
   `repo:file:Symbol` lines.
2. **The offenders are pre-existing, not from the discovering commit.** `check_schema_provenance.py` scans the source
   dir for local `BaseModel`/`TypedDict`/`dataclass` definitions and flags them ("should import from UAC or UIC"). It has
   NO baseline (`return 1 if all_violations else 0`). Every flagged symbol is in a file the worker's commit did not touch
   (`git show --name-only d8f05a5d` = `manifest_consolidator.py` + `test_manifest_consolidator.py` only; neither flagged;
   `ConsolidationReport` predates the change). `git show HEAD~1:unified_trading_library/walk_forward.py` carries the
   offender, so the red predates the worker's work and the tree was already red at the freshly-pulled LDR head.
3. **This blocks every unified-trading-library ship** under the green-tree rule (commit only from a `quality-gates.sh`-
   green tree; quickmerge's `--agent` sentinel refuses a non-green HEAD). Concretely it is blocking the consolidator
   phantom-lock guard fix (`manifest_consolidator_market_data_cefi_stuck_lock_2026_08_19.md` todo 2, `d8f05a5d`).

## Why it matters

- A red `quality-gates.sh` on the integration branch means no code reaches UTL LDR (and thus no service image picks up
  UTL fixes). The consolidator phantom-lock guard — the durable fix for the ~41h market-data-cefi outage — cannot ship
  until this clears.
- The check appears mis-applied to a LIBRARY repo: UTL is the schema/type DEFINING library (services consume UAC/UIC
  types; UTL's internal dataclasses are its own legitimate data structures, not consumer-facing UAC-contract types).
  `check_schema_provenance.py` is written for SERVICE repos that should import schema types from UAC/UIC. Either the
  check needs a UTL-scoped exemption/baseline for internal (non-exported, non-UAC-contract) types, or the ~30 offenders
  need a large migration to UAC/UIC — an operator/gate-owner decision.
- Not independently checked this pass: whether CI (quality-gates-v2 on the LDR→main promote PR) is likewise red and
  whether the fleet is already firefighting this (a recent merge from `main` — `3d345d34` — and the strict-basedpyright
  refactor `22eb0ba0` are the plausible introducers of the schema types).

## Recommended decision

1. **Immediately**: confirm whether the schema-provenance check is meant to apply to UTL at all. If not, scope it out of
   the library gate (or add a UTL exemption for internal non-UAC types) and re-run QG — this unblocks the whole fleet's
   UTL shipping.
2. **Or**: add a ratchet baseline for UTL's pre-existing offenders (mirroring the `codex_violations_ratchet_to_five`
   pattern) so new violations are caught but the legacy corpus doesn't block shipping; then migrate the offenders to
   UAC/UIC types in tracked follow-ups.
3. The consolidator fix (`d8f05a5d`) ships as soon as the gate is green.

## Todos

- [ ] [BACKEND] P1. **Resolve the unified-trading-library codex-py `schema-provenance` QG red** — either scope the check
      out of the library gate (UTL defines internal types legitimately; the check is written for service repos that
      should import UAC/UIC types), or add a ratchet baseline for the pre-existing offenders (~30 local
      BaseModel/TypedDict/dataclass across `walk_forward.py`, `per_leaf_failure.py`, `models/schemas.py`, `ml/models.py`,
      `core/*`, `reconcile/*`, `feature_calculator/*`, `feature_service_base/*`, `pipeline_e2e_check/*`, etc.), then
      re-run `bash scripts/quality-gates.sh` green. (repo: unified-trading-library + unified-trading-pm QG templates).
      Done when: UTL `quality-gates.sh` exits 0 at LDR HEAD with no codex-py failure.
- [ ] [DATA-ENG] P1. **Once the above gate is green, ship the consolidator phantom-lock guard fix** (`d8f05a5d`:
      skip-with-loud-alert on oversized unprovable-cutoff merges, `manifest_consolidator.py`) via quickmerge, and proceed
      with the `manifest_consolidator_market_data_cefi_stuck_lock` issue's todo-3 recovery verification. (repo:
      unified-trading-library).

## Progress Log

- **2026-08-19T21:2xZ (slot-4 worker, manifest_consolidator todo-2)**: filed. QG on `d8f05a5d` failed at the codex-py
  schema-provenance sub-check; verified pre-existing (offenders at `HEAD~1`, none in the worker's 2-file commit).
  Declared repo-blocker `qg_red` for unified-trading-library. The consolidator guard fix is committed but parked behind
  this gate.
