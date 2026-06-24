---
title: PM scripts/ basedpyright typecheck debt — capability-wizard files pushed the ratchet 1511 -> 1517
created: 2026-06-11
source:
  - unified-trading-pm quality-gates-v2 main run 27355114310 (typecheck slice FAILED)
  - unified-trading-pm/scripts/openapi/{_capability_extract,_capability_gaps,_capability_orphan,generate_capability_manifest}.py
locked_by: live-defi-rollout
priority: P3
status: active
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

- [ ] [CICD] P1. **Resolve the PM `scripts/` basedpyright recurring-ratchet trap (design fork).** Either (a) annotate
      the ~1555 `scripts/` `reportUnknown*`/`reportAny` (JSON-load + subprocess CLI boundaries) to ratchet → 0 and keep
      basedpyright-gating real PM tooling; OR (b) **exclude `scripts/` from PM basedpyright per the lifecycle-marker
      SSOT** (scripts = ruff-only) — kills the trap outright but drops type-checking on PM's real tooling; OR (c) run
      the full basedpyright on the metadata-only fast-path too (catches debt incrementally, but slows docs/plan merges).
      Decide + ship one; verify PM `quality-gates-v2` green + the ratchet no longer bumps on a bulk-`scripts/` edit.
      Provenance: orchestrator_self_healing_hardening_2026_06_21.md § Operator review (2026-06-23) incident-cluster,
      verified 2026-06-24 (failing step `QG slice (lint-codex)`; unblock commit `1e6ec188e`).
