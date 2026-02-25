# Cursor Rules Index

**Last Updated:** 2026-02-25  
**Total Rules:** 66  
**Always-Apply Rules:** 21

---

## Always-Apply Rules (alwaysApply: true)

These rules are **always active** regardless of file context:

| Rule | Description |
|------|-------------|
| agents-follow-cursor-rules.mdc | Sub-agents do not inherit rules — pass rules in every prompt |
| always-use-quickmerge.mdc | Use quickmerge.sh, never run quality-gates.sh standalone |
| basedpyright-safety.mdc | Never run basedpyright . — use timeout + source dir |
| codex-maintenance.mdc | Update codex when establishing new patterns |
| cursor-folder-boundary.mdc | .cursor/ = IDE config only; rules sync from unified-trading-pm |
| delete-deprecated.mdc | Delete deprecated code — do not archive in place |
| event-logging.mdc | setup_events/log_event from unified-events-interface |
| external-import-standards.mdc | Import from package root, never internal modules |
| instruments-domain-and-api-keys.mdc | Instruments via InstrumentsDomainClient, API keys via get_secret_with_fallback |
| never-revert-local-changes.mdc | Never git reset/revert without explicit user approval |
| no-summary-docs.mdc | BLOCKING: No summary/status docs unless requested |
| no-type-any-use-specific.mdc | Use specific types, never Any |
| parallel-agent-execution.mdc | Parallelize independent tasks across repos |
| plan-placement.mdc | Plans in unified-trading-pm or unified-trading-pm/plans/ai/ only |
| rollout-tracking.mdc | Plan complete on one repo ≠ workspace complete |
| rule-amnesia-detection.mdc | Stop if Cursor forgets rules |
| runtime-verification-required.mdc | Run code and check terminal before claiming done |
| search-before-implementing.mdc | Search unified libraries before writing new code |
| single-project-id-env-var.mdc | GCP_PROJECT_ID only — no GOOGLE_CLOUD_PROJECT |
| strict-quality-gates.mdc | All violations BLOCKING — no E722 global ignore |
| sub-agent-workflow-standard.mdc | Sub-agents preserve context, cost 10x less |

---

## Context-Sensitive Rules (globs)

- `**/pyproject.toml`, `**/uv.lock` → uv-lock-file.mdc
- `**/.github/workflows/*.yml`, `**/pyproject.toml` → path-dependency-ci.mdc
- `**/*.py` → no-type-any-use-specific, no-empty-fallbacks, code-quality-limits
- `**/tests/**` → test-quality-standards, test-coverage-targets

---

## Related

- **Workspace Rules:** `../.cursorrules`
- **Codex:** `unified-trading-codex/06-coding-standards/cursor-rules-system.md`
