---
doc_type: issue
title: PM scripts/ basedpyright typecheck debt — capability-wizard files pushed the ratchet 1511 -> 1517
summary: >-
  PM `scripts/` basedpyright ratchet debt — the `scripts/openapi/` capability-wizard files bumped
  `BASEDPYRIGHT_MAX_ERRORS` 1511->1517 (later 1523->1539->1555). RESOLVED 2026-06-24 by making basedpyright WARN-ONLY
  for PM `scripts/` (`unified-trading-pm@22b2f89d7`, PR #523), aligning with the lifecycle-marker SSOT (scripts =
  ruff-only); optional debt-paydown / scan-exclusion todos remain P3.
status: open
nature: notes
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, quickmerge, scripts, ssot-audit, orchestrator, self-healing]
related: [capability_wizard_and_manifest_2026_06_11]
created: 2026-06-11
parent_epic: infrastructure_master
priority: P3
source:
  [
    unified-trading-pm quality-gates-v2 main run 27355114310 (typecheck slice FAILED),
    "unified-trading-pm/scripts/openapi/{_capability_extract,_capability_gaps,_capability_orphan,generate_capability_manifest}.py",
  ]
assigned_vm: planning
resolved_by:
locked_by: live-defi-rollout
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
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

- [x] ✅ [SCRIPT] P3. **SUPERSEDED 2026-08-01 (slot 12) — moot, no code change.** The premise (annotate the 4 capability
      files, then ratchet `BASEDPYRIGHT_MAX_ERRORS` back down to 1511) no longer applies: the 2026-06-24 warn-only fix
      removed `BASEDPYRIGHT_MAX_ERRORS` from `scripts/quality-gates.sh` entirely (there is nothing left to ratchet), and
      the later 2026-07-27 fix (`unified-trading-pm@0db8ec5f2`, the `[CICD] P1` todo below) added `"scripts"` to
      `[tool.basedpyright] exclude` in `pyproject.toml`, so basedpyright analyzes ZERO files under `scripts/` regardless
      of CLI args. Re-verified live: `uv run basedpyright scripts/` → **0 errors, 0 warnings, 0 notes**.
      `scripts/quality-gates.sh:34-41` carries an explicit
      `DO NOT re-add BASEDPYRIGHT_MAX_ERRORS or narrow the pyproject.toml exclude` note — annotating the 4 files for a
      scan that structurally never runs would be pure busywork with no verifiable effect and no gate to check it
      against, and narrowing the exclude to make the scan "count" again is the exact regression that note forbids. No
      code shipped; this todo is closed as superseded by the broader fix, not executed as literally written.
- [x] ✅ [SCRIPT] P3. **NICE-TO-HAVE — SUPERSEDED 2026-08-01 (slot 12), same reasoning as above.** "Drive the ceiling
      materially below 1511" is moot: there is no ceiling (removed) and no scan (excluded) for any PM `scripts/` file,
      so annotating `check-repo-readiness.py` / `cicd/check_ci_status_bot_only.py` / `generate-cicd-diagram.py` /
      `feature_parity_diff.py` would not move any enforced number. Real type-safety work on these files is still welcome
      as ordinary code quality, but it is no longer this issue doc's QG-debt story — closing rather than leaving it to
      be re-discovered as apparently-still-live debt.

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
      the four-time `BASEDPYRIGHT_MAX_ERRORS` ratchet-bump trap (1511→…→1555) can never recur (was: "can never red the
      LDR→main PR / starve the fleet" — NARROWED 2026-07-12 per operator ruling finding 87, see the retagged todo below
      for the reconciliation-doc citation: this fix closed only the `BASEDPYRIGHT_MAX_ERRORS` ratchet-bump trap.
      `base-service.sh` carries a SEPARATE, unconditional zero-warning-policy block —
      `scripts/quality-gates-base/base-service.sh:882-885`
      (`if [ "${WARN_COUNT:-0}" -gt 0 ]; then ... log_fail "Type     check FAILED — $WARN_COUNT warning(s) ..."; exit 1; fi`)
      — untouched by the 2026-06-24 fix, so a PM `scripts/` basedpyright WARNING is still a live path to red the
      LDR→main promotion PR. Evidence: `active/issues/uv_pin_fleet_drift_2026_06_22.md:221-230` records PR #498's v2 RED
      on `QG slice (typecheck)` with ~3082 `reportAny`/`reportUnknown*` errors, observed 2026-06-27 (`last_updated`) —
      three days AFTER this fix shipped). Aligns with the lifecycle-marker SSOT (scripts = ruff-only). DO-NOT-re-add
      note is in the gate file.
- [x] ✅ [CICD] P1. **bumped per operator ruling 2026-07-12 (finding 87)** (was: P3 "NICE-TO-HAVE" — no longer accurate:
      the zero-warning-policy block in `base-service.sh` (see narrowed claim above) means this is a live path to red the
      LDR→main promotion PR, not a no-urgency cleanup). **Longer-term: fully exclude `scripts/` from the basedpyright
      SCAN, or annotate the debt down.** Warn-only (above) ends the `BASEDPYRIGHT_MAX_ERRORS` ratchet-bump trap but
      still RUNS basedpyright on `scripts/` (~240s), and the SEPARATE unconditional zero-warning-policy block still
      FAILS the gate on any `WARN_COUNT>0`. If the ~240s docs-repo cost is worth removing, exclude the scan (e.g. point
      `SOURCE_DIR` off `scripts/` or a pyrightconfig exclude) — vs. opportunistically annotating the `scripts/`
      `reportUnknown*`/`reportAny` if PM tooling ever wants real type-checking back. Ruling + rationale:
      `plans/active/issues/plan_reconciliation_operator_decisions_2026_07_11.md` §A2 (finding 87: "Narrow 'can never
      red' claim + bump off P3"). Provenance: same incident. Provenance:
      orchestrator_self_healing_hardening_2026_06_21.md § Operator review (2026-06-23) incident-cluster, verified
      2026-06-24 (failing step `QG slice (lint-codex)`; unblock commit `1e6ec188e`). **DONE 2026-07-27 (slot-5)** —
      `unified-trading-pm@0db8ec5f2`. Chose the exclude-the-scan option (annotating ~3082 `reportUnknown*`/`reportAny`
      diagnostics down was not remotely feasible as a single bounded task, and the file's own history shows the intent
      was already "scripts/ doesn't want real type-checking", not merely deferred). `[tool.basedpyright] exclude` now
      includes `"scripts"` itself. Verified empirically this wins over the explicit CLI path arg base-service.sh always
      passes (`basedpyright scripts/`): **0 errors, 0 warnings, 0 notes** — closing BOTH traps (the
      `BASEDPYRIGHT_MAX_ERRORS` ratchet-bump trap the 2026-06-24 fix already closed, AND the separate
      zero-warning-policy trap this finding narrowed) with **zero changes to the shared `base-service.sh`** (its
      zero-warning-policy is untouched — it simply never fires because PM's own config now produces nothing to fail on).
      Deleted the now-fully-dead ~85-entry per-file `ignore` list, rule-severity overrides, and `extraPaths` (nothing is
      ever scanned, so they were vestigial dead config, not kept as a shim). Full `bash scripts/quality-gates.sh` green,
      sentinel verified matching HEAD.

- [ ] [SCRIPT] P3. **New side-effect of the exclude-the-scan fix above**:
      `scripts/manifest/check-pyrightconfig-extrapaths.py` (a standalone, NOT CI-wired, manually-invoked audit tool —
      confirmed via grep, no `.github/workflows/` or other script calls it) will now flag PM's own repo entry as a
      "MISSING extraPath" (its Rule 3) the next time someone runs it, since PM's `[tool.basedpyright]` no longer carries
      `extraPaths` at all (removed as dead config — nothing is ever scanned). Not a QG blocker (tool isn't wired into
      any gate), but a real false-positive the next manual run will hit. Fix: either add PM to an exemption list in that
      script (repos whose basedpyright config excludes their own `SOURCE_DIR` have nothing to resolve imports for) or
      skip repos where `exclude` covers `include`. (repo: unified-trading-pm).
