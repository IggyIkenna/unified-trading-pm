---
doc_type: codex-ssot
title: Quality Gate Bypass Audit
summary: Registry of every sanctioned codex-repo QG exception — file-size (none), ruff (none), basedpyright (only the
  docs-only test_event_logging.py template, 17 cascade errors), and pip-audit CVEs (gunicorn/pip) owned by service repos
  not codex.
status: current
nature: ssot
asset_group: [meta]
stage: [meta]
repos: []
scope: [engineer, admin]
tags: [quality-gates, ssot-audit, cve, docspec]
related: [10-audit/QUALITY_GATE_BYPASS_AUDIT.md]
created: 2026-03-27
authoritative_for: [codex-repo-local quality-gate exception list (this docs-only repo's own bypasses)]
referenced_by:
owner:
last_reviewed:
code_refs:
---

# Quality Gate Bypass Audit

## 2.1 File Size Exceptions

None.

## 2.2 Ruff Exceptions

None.

## 2.3 Basedpyright Exceptions

### 06-coding-standards/test-templates/test_event_logging.py (17 errors)

**Justification:** This is a documentation template file (copy-paste starter), not a runnable module in this repo. It
imports `pytest` and `unified_trading_library.events` which are only available inside individual service repos, not in
the codex repo itself. The template is intentionally standalone and cannot resolve these imports from codex context.

**Errors bypassed:**

- `reportMissingImports`: `pytest`, `unified_trading_library.events` — not installed in codex (docs-only repo)
- `reportUnknownMemberType`, `reportUntypedFunctionDecorator`, `reportUnknownVariableType`, `reportUnknownArgumentType`
  — cascade from unresolvable pytest/UEI imports

**Owner:** codex maintainers **Added:** 2026-03-07 (pyrightconfig upgrade basic→strict)

## 2.4 pip-audit Exceptions (workspace-level CVEs, not codex deps)

Codex is a docs-only repo with no runtime Python dependencies. pip-audit runs against the workspace venv (shared across
all repos) and finds CVEs in unrelated service packages. These are tracked at the service-level, not here.

- `gunicorn 21.2.0`: CVE-2024-1135, CVE-2024-6827 (HTTP Request Smuggling) — Owned by: services using gunicorn; fix:
  bump gunicorn ≥ 22.0.0 in affected service repos
- `pip 25.2`: CVE-2025-8869, CVE-2026-1703 (tar path traversal) — Owned by: workspace bootstrap; fix: upgrade pip to
  26.0+ in workspace setup
