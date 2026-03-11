# Workspace Rules Housekeeping — 2026-03-11

## Status: FULLY COMPLETE (2026-03-11)

Cursor rules audit, script symlink consolidation, and workspace config cleanup.

---

## Completed

### Deleted cursor rule files (no value / stale)

- `cursor-rules/misc/pylance-extra-paths.mdc` — Pylance-specific, Pylance removed
- `cursor-rules/misc/pyright-unknown-types.mdc` — redundant with workspace pyrightconfig + each repo's pyproject.toml
- `cursor-rules/services/repo-type-detection.mdc` — superseded by manifest tags + naming conventions
- `cursor-rules/workflow/lobster-workflows.mdc` — lobster not in use

### Updated cursor rule files

- `cursor-rules/misc/validator-integration.mdc` — non-blocking → blocking (propagate exit code, fail fast)
- `cursor-rules/services/servicecli-framework.mdc` — fixed stale import path:
  `unified_trading_services.core.service_framework` → `unified_trading_library.service_cli`
- `cursor-rules/workflow/pr-review-checklist.mdc` — removed "dependency matrix alignment" / `--dep-branch`; now
  references `workspace-manifest.json`
- `cursor-rules/pm-python-standards.mdc` — removed `tests/` from basedpyright scope (globs + command)
- `cursor-rules/quality-gates/quality-gate-optimization.mdc` — made Pass 1 explicitly mandatory; added "NEVER: Skip Pass
  1 and go straight to quickmerge"

### Workspace config (`cursor-configs/unified-trading-system-repos.code-workspace`)

- Disabled conflicting language servers: `"python.languageServer": "None"`, `mypy-type-checker.enabled: false`,
  `ms-python.black-formatter.enabled: false`, `isort.enabled: false`
- Added `extensions.unwantedRecommendations`: pylance, mypy-type-checker, black-formatter, isort

### Script symlink consolidation

- `scripts/rollout-agent-symlinks.sh` — now rolls out `.cursor/scripts/check-import-patterns.py` symlinks for Python
  repos (detected via `pyproject.toml`); replaces local copies
- `scripts/repo-management/run-version-alignment.sh` — added step `[0.55/4]`: positive check that Python repos have
  symlink (not local copy); warns with fix command on failure

---

## Previously Deferred — Now Complete

| Item                                                                                | Resolution                                                                                                            |
| ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Run `bash scripts/rollout-agent-symlinks.sh` to convert 26 local copies to symlinks | ✅ Rollout executed — all repos committed                                                                             |
| Fix `WORKSPACE_MANIFEST_DAG.svg`: unified-reference-data-interface tier             | ✅ URDI merge_level 2→4; topologicalOrder + publishingOrder updated; DAG SVG regenerated; L4 band description updated |

## Session 2 Additions (2026-03-11)

- `docs/repo-management/CI-CD-FLOW.md` — 3 gaps fixed: pyrightconfig.json (IDE-only, not CI), test-harness exemption
  (string deps invisible to alignment scanner), --agent flag + two-pass model
- `scripts/repo-management/run-version-alignment.sh` step [0.55/4] — fixed false positive: PM now excluded; check scoped
  to manifest repos only (not untracked on-disk repos like elysium-defi-lite)
- `unified-trading-ui-kit` — `npm install` run to resolve stale package-lock
- All active plans scanned — no regressions from any session changes
