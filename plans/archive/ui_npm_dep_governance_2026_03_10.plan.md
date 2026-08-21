---
doc_type: plan
title: UI npm Dependency Governance — 2026-03-10
summary: "Six-part improvement to make UI npm dependency drift detectable and auto-resolved\nin the same CI/CD flow as Python\
  \ dependency alignment.\n\nProblem: package.json edits (e.g. adding @vitest/coverage-v8) did not trigger npm install\n\
  because setup.sh compared package.json mtime against the node_modules/ *directory* mtime,\nwhich a failed npm install\
  \ can touch without completing. This left node_modules stale silently.\n\nSolution:\n  1. setup.sh: compare package.json\
  \ against package-lock.json (written only on successful\n     install) instead of node_modules dir mtime.\n  2. run-version-alignment.sh:\
  \ add step [0.6/4] — scan all pure UI repos (package.json,\n     no pyproject.toml) and WARN if package.json is newer\
  \ than package-lock.json.\n     --strict makes it fatal. --ui-only skips Python alignment steps (runs 0.5+0.7 only).\n\
  \  3. base-ui.sh: --test flag added so run-all-quality-gates.sh --test skips lint for UI repos\n     (previously --test\
  \ was ignored by UI quality-gates.sh).\n  4. workspace-npm-constraints.json + rollout-npm-versions.py: canonical npm devDependency\n\
  \     versions enforced cross-repo (analogue of workspace-constraints.toml + propagate-canonical-\n     versions.py for\
  \ Python). Integrated as step [0.7/4] in run-version-alignment.sh so it runs\n     in the same CI/CD flow alongside Python\
  \ alignment. --fix applies version updates; --strict\n     makes mismatches fatal.\n  5. batch-audit-ui test setup: was\
  \ the only UI repo with testing_level: none. Added vitest,\n     @vitest/coverage-v8, @testing-library/react, jest-dom.\
  \ 3 tests, all pass.\n  6. Manifest updated: all 11 UI repos now testing_level: unit, quality_gate_status: PASSING."
status: completed
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: []
related: []
created: 2026-03-10
updated: 2026-03-10
isProject: false
todos:
- {id: fix-setup-sh-npm-detection, content: 'Change setup.sh npm install skip check from `package.json -nt node_modules` to `package.json -nt package-lock.json`. Lock file is only written on successful npm install, making it a reliable freshness signal. node_modules dir mtime is fragile (failed installs can touch it without completing).', status: completed, notes: 'Changed in unified-trading-pm/scripts/setup.sh lines ~190-198. Condition now: `[ ! -f "package-lock.json" ] || [ "package.json" -nt "package-lock.json" ]`. Top-of-file skip-logic comment updated to document the package-lock.json rationale.'}
- {id: add-ui-drift-step-to-alignment, content: 'Add step [0.6/4] to run-version-alignment.sh that scans all pure UI repos and warns if package.json is newer than package-lock.json. Add --ui-only flag to skip Python alignment steps (useful for quick UI-only checks). --strict makes drift fatal.', status: completed, notes: 'Step [0.6/4] added after broken-symlinks step [0.5/4]. Uses find -maxdepth 2 to locate package.json files, skips repos with pyproject.toml and workspace root. Reports per-repo with actionable fix command. --ui-only exits after step 0.6. --strict exits 1 on drift. Tested: touch package.json → WARN detected; npm install → OK confirmed.'}
- {id: add-base-ui-test-flag, content: 'Create base-ui.sh in unified-trading-pm/scripts/quality-gates-base/ to replace the standalone quality-gates-ui-template.sh. Add --test flag (skip lint, run typecheck+tests). Fix --lint and --quick to also skip build (was a bug: --lint ran build). Propagate stub to all 11 ui-type repos via rollout-quality-gates-unified.py.', status: completed, notes: 'base-ui.sh created. quality-gates-ui-template.sh in codex is now a ~8-line stub. All 11 ui-type repos updated via rollout. Docs updated in codex README.md, quality-gates.md, and quality-gates-base/README.md.'}
- {id: fix-vitest-version-mismatch, content: All 10 UI repos had vitest@^1.x but @vitest/coverage-v8@^2.0.0 — peer dep conflict prevented npm install from completing. Bump vitest to ^2.0.0 in all repos to match., status: completed, notes: 'Fixed in: trading-analytics-ui, deployment-ui, client-reporting-ui, settlement-ui, live-health-monitor-ui, logs-dashboard-ui, ml-training-ui, strategy-ui, onboarding-ui, execution-analytics-ui, unified-trading-ui-auth. Also bumped @vitest/ui ^1.x → ^2.0.0 in onboarding-ui. npm install completed cleanly in all repos after the version fix.'}
- {id: add-batch-audit-ui-tests, content: 'batch-audit-ui had no unit tests (testing_level: none, quality_gate_status: EXEMPT). Add vitest setup: package.json deps, vitest.config.ts, src/setupTests.ts, src/App.test.tsx.', status: completed, notes: 'Added vitest@^2.0.0, @vitest/coverage-v8@^2.0.0, @testing-library/react, jest-dom, jsdom. vitest.config.ts + setupTests.ts + App.test.tsx created (3 tests, all pass). Manifest updated: testing_level: unit, quality_gate_status: PASSING.'}
- {id: update-manifest-testing-level, content: Update manifest testing_level from none to unit for all UI repos now confirmed to have vitest configured. Update quality_gate_status from EXEMPT to PASSING., status: completed, notes: 'Updated 11 repos: all 10 vitest-configured repos + batch-audit-ui. batch-audit-ui: testing_level: unit, quality_gate_status: PASSING. batch-audit-ui was previously the only UI repo still at testing_level: none.'}
- {id: canonical-npm-version-enforcement, content: 'Close scope gap vs Python: add workspace-npm-constraints.json (analogue of workspace-constraints.toml) and rollout-npm-versions.py (analogue of propagate-canonical-versions.py). Integrate as step [0.7/4] in run-version-alignment.sh so users follow the same --fix / --ui-only workflow for npm versions as they do for Python dep alignment. --strict makes mismatches fatal; --fix applies updates; uncloned repos emit a warning, not a failure.', status: completed, notes: 'workspace-npm-constraints.json created in unified-trading-pm/ with 13 canonical devDependency versions. rollout-npm-versions.py created in scripts/propagation/; uses version_is_below_canonical() to avoid false positives on repos with newer patch versions (e.g. ^4.2.1 vs canonical ^4.2.0 → not flagged). Step [0.7/4] added to run-version-alignment.sh after step [0.6/4]; runs rollout-npm-versions.py --apply when --fix is passed, dry-run otherwise. Tested: onboarding-ui had 4 below-canonical
    versions (testing-library/react, jest-dom, playwright, eslint) → rollout --apply fixed all 4 → npm install OK → run-version-alignment.sh --ui-only confirmed [OK] on all 3 checks. deployment-ui (not cloned) correctly emits ⚠️ skipped warning, not failure.'}
---

# UI npm Dependency Governance — 2026-03-10

## Problem Statement

When `@vitest/coverage-v8` was added to UI repo `package.json` files during coverage remediation, `npm install` was
never re-run. The old `setup.sh` check compared `package.json` mtime against `node_modules/` directory mtime — fragile
because a failed npm install (e.g. due to the vitest version mismatch) can touch `node_modules/` without completing.
This left all UI repos with stale node_modules silently.

## Files Changed

| File                                                                                          | Change                                                                                             |
| --------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| `unified-trading-pm/scripts/setup.sh`                                                         | npm skip check: `node_modules` mtime → `package-lock.json` mtime                                   |
| `unified-trading-pm/scripts/repo-management/run-version-alignment.sh`                         | Added step [0.6/4] UI dep-drift check, step [0.7/4] canonical npm version check, `--ui-only` flag  |
| `unified-trading-pm/scripts/quality-gates-base/base-ui.sh`                                    | New — UI gate logic with `--test` flag                                                             |
| `unified-trading-codex/06-coding-standards/quality-gates-ui-template.sh`                      | Converted to stub sourcing base-ui.sh                                                              |
| All 11 `*-ui/scripts/quality-gates.sh`                                                        | Propagated new stub via rollout                                                                    |
| `unified-trading-pm/workspace-manifest.json`                                                  | testing_level + quality_gate_status updated for all 11 UI repos                                    |
| `batch-audit-ui/package.json` + `vitest.config.ts` + `src/setupTests.ts` + `src/App.test.tsx` | New test setup                                                                                     |
| `unified-trading-pm/workspace-npm-constraints.json`                                           | New — canonical npm devDependency versions (13 packages)                                           |
| `unified-trading-pm/scripts/propagation/rollout-npm-versions.py`                              | New — enforce canonical npm versions across UI repos (analogue of propagate-canonical-versions.py) |

## Test Coverage

```
# Dep-drift detection (step 0.6)
run-version-alignment.sh --ui-only          # [OK] all UI repos clean
touch batch-audit-ui/package.json
run-version-alignment.sh --ui-only          # [WARN] batch-audit-ui drift detected
npm install in batch-audit-ui
run-version-alignment.sh --ui-only          # [OK] clean again

# Canonical npm version enforcement (step 0.7)
# onboarding-ui had 4 below-canonical versions in package.json
run-version-alignment.sh --ui-only          # [WARN] 4 mismatches in onboarding-ui
run-version-alignment.sh --fix --ui-only    # [APPLY] fixed all 4 versions
cd onboarding-ui && npm install             # install updated deps
run-version-alignment.sh --ui-only          # [OK] all 3 checks pass
```
