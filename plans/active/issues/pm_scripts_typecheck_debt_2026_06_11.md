---
doc_type: issue
title: PM scripts/ basedpyright typecheck debt — capability-wizard files pushed the ratchet 1511 -> 1517
summary:
status: open
nature: notes
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-06-11
parent_epic:
priority: P3
source:
  [
    unified-trading-pm quality-gates-v2 main run 27355114310 (typecheck slice FAILED),
    "unified-trading-pm/scripts/openapi/{_capability_extract,_capability_gaps,_capability_orphan,generate_capability_manifest}.py",
  ]
assigned_vm: NA
resolved_by:
locked_by: live-defi-rollout
---

## What I found

PM `main`'s `quality-gates-v2` went RED on 2026-06-11 (run 27355114310). Merge PR #270 changed `scripts/openapi/*.py`
(the capability-wizard files), so the full QG ran instead of PM's usual metadata-only fast-path on plan-only merges —
surfacing the strict basedpyright ratchet. The scripts/ basedpyright error count rose from the ceiling
`BASEDPYRIGHT_MAX_ERRORS=1511` to **1517** (+6 `reportAny` / `reportUnknownVariableType` / `reportUnknownMemberType`
errors), concentrated in the four new `scripts/openapi/` capability files plus pre-existing untyped scripts
(`check-repo-readiness.py`, `cicd/check_ci_status_bot_only.py`, etc.).

The interim clear (shipped 2026-06-11): raised `BASEDPYRIGHT_MAX_ERRORS` to 1517 to capture the existing errors only (no
headroom for new ones — the ratchet still blocks any future regression). PM is a non-package tooling/docs repo with a
documented basedpyright-baseline exception, so a ratchet bump is the sanctioned interim clear for a tooling repo.

## Why it matters

The ratchet is a one-way gate: errors only go DOWN. The +6 are real type-inference gaps in production CI/CD tooling
(`scripts/openapi/` feeds the capability manifest). Leaving them at the ceiling is fine as an interim, but the debt
should be retired so the ceiling can ratchet back toward zero.

## Recommended decision

- [ ] [SCRIPT] P3. Type-annotate the new
      `scripts/openapi/{_capability_extract,_capability_gaps,_capability_orphan,generate_capability_manifest}.py`
      capability files in `unified-trading-pm` so they are strict-clean (resolve the +6 `reportAny`/`reportUnknown*`
      errors), then ratchet `BASEDPYRIGHT_MAX_ERRORS` in `scripts/quality-gates.sh` back down to 1511 (or lower). The
      1517 ceiling is the interim clear. Verify with `cd unified-trading-pm && .venv/bin/basedpyright scripts/` (count
      must be at-or-below the new ceiling). Related: `plans/active/capability_wizard_and_manifest_2026_06_11.md`.
- [ ] [SCRIPT] P3. **NICE-TO-HAVE** Opportunistically annotate the other long-standing untyped PM scripts
      (`check-repo-readiness.py`, `cicd/check_ci_status_bot_only.py`, `generate-cicd-diagram.py`,
      `feature_parity_diff.py`) to drive the ceiling materially below 1511 over time, one PR per file (provenance: same
      run 27355114310).

## New inputs (2026-06-24) — recurring-trap diagnosis + the design fork (from orchestrator_self_healing_hardening incident review)

The ratchet has now been bumped **four times** (1511→1517→1523→1539→1555). Verified root cause of the recurrence (not
inference): PM's **metadata-only fast-path SKIPS the full basedpyright typecheck** on docs/plan-only merges, so
`scripts/` typing debt accumulates INVISIBLY; then any event forcing a full run (a bulk-edit cache-bust like the
lifecycle-marker frontmatter stamp `2dc131639`, an unblocked LDR→main drain, or a `scripts/` change) surfaces all the
accumulated debt at once → `QG slice (lint-codex)` red → ratchet bump (last: `1e6ec188e` 1539→1555). It also blocks the
whole fleet when it reddens PM's standing LDR→main PR (2026-06-23: stranded the staging→main fix off `main` → fleet
drain stalled).

**This is a SSOT contradiction to resolve, not just a debt-paydown:** the lifecycle-marker SSOT (CLAUDE.md § Script
Homes) says `scripts/` are **ruff-gated, NOT basedpyright/coverage-gated** — yet PM's QG basedpyright-gates `scripts/`
with the 1555 ratchet (all the debt is in `scripts/`). Pick ONE durable resolution (fleet blast-radius — prove before
shipping):

- [x] ✅ [CICD] P1. **Recurring-ratchet trap RESOLVED — basedpyright is WARN-ONLY for PM `scripts/`** (operator decision
      2026-06-24, shipped `unified-trading-pm@22b2f89d7` via PR #523). Removed `BASEDPYRIGHT_MAX_ERRORS=1555` from PM's
      `quality-gates.sh` → base-service runs basedpyright + reports the count as a WARNING but never FAILS the gate, so
      the four-time ratchet-bump trap (1511→…→1555) can never recur + can never red the LDR→main PR / starve the fleet.
      Aligns with the lifecycle-marker SSOT (scripts = ruff-only). DO-NOT-re-add note is in the gate file.
- [ ] [CICD] P3. **NICE-TO-HAVE — longer-term: fully exclude `scripts/` from the basedpyright SCAN, or annotate the debt
      down.** Warn-only (above) ends the trap but still RUNS basedpyright on `scripts/` (~240s + a warning). If the
      ~240s docs-repo cost is worth removing, exclude the scan (e.g. point `SOURCE_DIR` off `scripts/` or a
      pyrightconfig exclude) — vs. opportunistically annotating the `scripts/` `reportUnknown*`/`reportAny` if PM
      tooling ever wants real type-checking back. No urgency (the gate no longer blocks anything). Provenance: same
      incident. Provenance: orchestrator_self_healing_hardening_2026_06_21.md § Operator review (2026-06-23)
      incident-cluster, verified 2026-06-24 (failing step `QG slice (lint-codex)`; unblock commit `1e6ec188e`).
