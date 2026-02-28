# Cursor Rules Index

**Last Updated:** 2026-02-26
**Total Rules:** 77
**Always-Apply Rules:** 31

---

## Always-Apply Rules (alwaysApply: true)

These rules are **always active** regardless of file context:

| Rule | Priority | Description |
|------|----------|-------------|
| no-summary-docs.mdc | P100 | BLOCKING: No summary/status docs unless requested |
| plan-placement.mdc | P95 | Plans in unified-trading-pm or unified-trading-pm/plans/ai/ only |
| agents-follow-cursor-rules.mdc | P90 | Sub-agents do not inherit rules — pass rules in every prompt |
| always-use-quickmerge.mdc | P90 | Use quickmerge.sh, never run quality-gates.sh standalone |
| basedpyright-safety.mdc | P90 | Never run basedpyright . — use timeout + source dir |
| never-revert-local-changes.mdc | P90 | Never git reset/revert without explicit user approval |
| runtime-verification-required.mdc | P90 | Run code and check terminal before claiming done |
| anti-patterns-quick-reference.mdc | P80 | Don't/do pairs for common mistakes — quick reference |
| delete-deprecated.mdc | P80 | Delete deprecated code — do not archive in place |
| event-logging.mdc | P80 | setup_events/log_event from unified-events-interface |
| external-import-standards.mdc | P80 | Import from package root, never internal modules |
| gcp-auth-in-tests.mdc | P80 | Use google.auth.default() — never skip tests for missing creds |
| instruments-domain-and-api-keys.mdc | P80 | Instruments via InstrumentsDomainClient, API keys via get_secret_client |
| no-type-any-use-specific.mdc | P80 | Use specific types, never Any |
| search-before-implementing.mdc | P80 | Search unified libraries before writing new code |
| single-project-id-env-var.mdc | P80 | GCP_PROJECT_ID only — no GOOGLE_CLOUD_PROJECT |
| strict-quality-gates.mdc | P80 | All violations BLOCKING — no E722 global ignore |
| async-http-aiohttp.mdc | P80 | Use aiohttp for async HTTP, never requests |
| builtin-generics-standard.mdc | P80 | Use list/dict/tuple not typing.List/Dict/Tuple |
| no-backward-compatibility.mdc | P80 | Fail fast, clean migrations — no compat shims |
| utc-datetime.mdc | P80 | All datetimes must be timezone-aware UTC |
| batch-live-symmetry.mdc | P75 | 90% shared engine; only 4 seams differ between modes |
| concurrency-max-workers.mdc | P75 | MAX_WORKERS by workload type; adaptive RAM thresholds |
| schema-service-owned.mdc | P75 | Services own output schemas; validate before GCS write |
| codex-maintenance.mdc | P70 | Update codex when establishing new patterns |
| cloud-build-test-in-image.mdc | P70 | Quality gates run inside Docker image, not outside |
| context7-usage.mdc | P70 | Append "use context7" for external library work |
| cursor-folder-boundary.mdc | P70 | .cursor/ = IDE config only; rules sync from unified-trading-pm |
| hook-tooling-policy.mdc | P70 | Use prek for git hooks; config in .pre-commit-config.yaml |
| parallel-agent-execution.mdc | P70 | Parallelize independent tasks across repos |
| rollout-tracking.mdc | P70 | Plan complete on one repo ≠ workspace complete |
| rule-amnesia-detection.mdc | P70 | Stop if Cursor forgets rules |
| lobster-workflows.mdc | P50 | Use lobster for systematic 30+ repo improvements |
| sub-agent-workflow-standard.mdc | P50 | Sub-agents preserve context, cost 10x less |

---

## Priority Tier Guide

| Priority | Tier | Meaning |
|----------|------|---------|
| P100 | Blocking | No-summary-docs: violations block task completion |
| P95 | Structure | Plan-placement: controls where artifacts go |
| P90 | Safety | Runtime verification, never-revert, basedpyright-safety |
| P80 | Standards | Coding standards, import rules, type rules |
| P70 | Maintenance | Codex updates, rollout tracking, deprecation |
| P50 | Informational | Workflow guidance, sub-agent patterns |

---

## Context-Sensitive Rules (globs)

- `**/pyproject.toml`, `**/uv.lock` → uv-lock-file.mdc, workspace-venv-sync.mdc
- `**/.github/workflows/*.yml`, `**/pyproject.toml` → path-dependency-ci.mdc
- `**/*.py` → no-type-any-use-specific, no-empty-fallbacks, code-quality-limits
- `**/tests/**` → test-quality-standards, test-coverage-targets
- `unified-trading-codex/06-coding-standards/**` → coding-standards-alignment.mdc

---

## Related

- **Workspace Rules:** `../.cursorrules`
- **Codex:** `unified-trading-codex/06-coding-standards/cursor-rules-system.md`
