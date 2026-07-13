---
doc_type: issue
title: system-integration-tests quality-gates.sh RED — pip-audit click/pillow CVEs, ceiling is 0
summary:
  system-integration-tests' CODEX_MAX_VIOLATIONS=0 (zero-tolerance) is breached by the same fleet-wide click 8.3.1 /
  pillow 12.2.0 CVEs also hitting execution-service, ml-service, and unified-trading-api today — blocks all shipping to
  the repo.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [system-integration-tests]
scope: [engineer]
tags: [pip-audit, cve, quality-gates, repo-blocker]
related:
  [
    plans/active/issues/execution_service_codex_compliance_red_2026_07_13.md,
    plans/active/issues/ml_service_pip_audit_red_pillow_cryptography_starlette_2026_07_13.md,
    plans/active/issues/unified_trading_api_pip_audit_stale_ignore_list_2026_07_13.md,
  ]
created: "2026-07-13"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
source: [utl_reuse_phase7_low_lint_tail_2026_07_13.md, slot-11 backend-engineer task]
resolved_by:
locked_by:
drift_direction: advance-code
depends_on: []
---

# system-integration-tests quality-gates.sh RED — pip-audit click/pillow CVEs, ceiling is 0

## What I found

While shipping an unrelated 1-line import fix (`tests/integration/test_leveraged_leg_controller_e2e.py`, part of
`utl_reuse_phase7_low_lint_tail_2026_07_13.md`), `bash scripts/quality-gates.sh` failed:
`❌ Codex compliance FAILED: 1 violations (max allowed: 0)`. The violating check: `pip-audit vulnerabilities found` —
`click 8.3.1` (PYSEC-2026-2132, command injection in `click.edit()`), `pillow 12.2.0`
(PYSEC-2026-2253/2254/2255/2256/2257, PIL font/image parsers).

Not caused by my diff — a 1-line test-file import change cannot introduce a dependency CVE. This is the same
click/pillow CVE pair independently hitting `execution-service` (see
`execution_service_codex_compliance_red_2026_07_13.md`), and the same CVE class already tracked today for `ml-service`
(pillow/cryptography/starlette) and `unified-trading-api` (stale ignore-list). Looks like a fleet-wide
dependency-advisory event (all 4 issues filed the same day, 2026-07-13) rather than 4 independent regressions — likely
`click`/`pillow` CVEs were newly published and now trip every repo that pins them below the fixed version.

## Why it matters

`CODEX_MAX_VIOLATIONS=0` in system-integration-tests is zero-tolerance — this single pip-audit hit blocks ALL shipping
to the repo, including my in-flight `utl_reuse_phase7_low_lint_tail_2026_07_13.md` todo.

## Recommended decision

Given the fleet-wide pattern (4 repos same day), this is likely best fixed ONCE at the canonical dependency level
(`unified-trading-pm/workspace-constraints.toml` / `canonical-dependency-manifest.json` — bump the fleet `click` /
`pillow` ranges to the fixed versions) and fanned out via `update-dependency-version.yml`, rather than 4 separate
per-repo pyproject bumps. Cross-reference with the other 3 issue docs before fixing per-repo in isolation — one
coordinated canonical bump avoids re-litigating the same fix 4 times.

## Todos

- [ ] [CODE] P1. Bump the fleet-canonical `click` range to ≥8.3.2 and `pillow` range to ≥12.3.0 in
      `unified-trading-pm/workspace-constraints.toml` + `canonical-dependency-manifest.json`, re-lock every affected
      repo (system-integration-tests, execution-service, +whatever else `update-dependency-version.yml` fans out to),
      re-verify no API breakage. Coordinate with the ml-service and unified-trading-api pip-audit issue docs to avoid
      duplicate fixes. (repo: unified-trading-pm + fanned-out repos)
- [ ] [VERIFY] P1. Once the canonical bump lands, re-run `bash scripts/quality-gates.sh` in system-integration-tests
      full-green, then resolve the repo-blocker / flip the `repo-system-integration-tests-qg-green` condition. (repo:
      system-integration-tests)
