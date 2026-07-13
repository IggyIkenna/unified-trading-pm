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
resolved_by: slot-15 (cicd, agt-48117c)
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

## Interim resolution (2026-07-13, slot-15 cicd escalation agt-48117c)

Repo-blocker RB-e06aa00b needed the gate green now (it was blocking slot-11's unrelated in-flight work), so shipped a
scoped per-repo interim fix rather than waiting on the canonical-manifest coordination below:
`uv lock --upgrade-package click --upgrade-package pillow --upgrade-package soupsieve` in `system-integration-tests`
(all three are transitive deps with no `pyproject.toml` ceiling — resolved cleanly, zero conflicts). Note `soupsieve`
(CVE-2026-49477/CVE-2026-49476) had also newly surfaced since this doc's original diagnosis (click+pillow only) — same
fleet-wide 2026-07-13 CVE-disclosure window. Shipped `system-integration-tests@6d7a5b6`; full `quality-gates.sh`
confirmed green (`pip-audit clean`). Repo-blocker resolved.

The canonical fleet-wide bump (todo below) is still the RIGHT longer-term fix — it prevents the same click/pillow/
soupsieve CVEs from independently re-tripping every other repo that hasn't hit them yet — this interim fix only unblocks
`system-integration-tests`.

## Todos

- [x] ✅ [CODE] P1. Bumped the fleet-canonical `click` floor — SHIPPED `unified-trading-pm@c44b182f9` (PR #998).
      Fix-version corrected mid-task from the originally-quoted `>=8.3.2` to `>=8.3.3` after
      fund-administration-service's pip-audit run showed PYSEC-2026-2132's advisory data had tightened (same ID, later
      fix-version). `pillow>=12.3.0` and `soupsieve>=2.8.4` were already satisfied fleet-wide by each repo's own
      `uv.lock` resolution before this todo started — verified via a direct `uv.lock` scan across every repo that
      carries either package transitively or directly (features-service, alerting-service, client-reporting-api,
      deployment-api, deployment-service, e2e-testing, execution-service, fund-administration-service, greeks-service,
      market-tick-data-service, ml-service, strategy-service, system-integration-tests, unified-trading-api,
      agent-orchestrator, instruments-service): click resolves 8.3.3–8.4.2, pillow resolves 12.3.0, soupsieve resolves
      2.8.4 everywhere it appears — no repo needed a `soupsieve`-specific fix beyond the already-shipped
      `system-integration-tests@6d7a5b6` interim. **Click floor shipped per-repo** (declarative bump,
      `click>=8.3.2,<9.0.0` → `>=8.3.3,<9.0.0`, matching or re-locking as needed): `features-service@d676d24c`, plus the
      canonical file (`unified-trading-pm@c44b182f9`). Repos already resolving ≥8.3.3 transitively needed no
      direct-dependency change. **Self-correction mid-task (P1, cross-repo):** while chasing the PM dependency-alignment
      gate for this todo, I mistakenly widened the canonical `fastapi` ceiling to `<0.138.0` fleet-wide (13 repos) to
      clear an alignment failure — this directly contradicted an already-shipped, independently-investigated resolution
      (`unified-trading-pm@1ea525c6e`, slot-3, same day) that deliberately kept the ceiling at `<0.137.0` with a narrow
      ml-service-only exception, because fastapi 0.137.x still reproduces a real route-introspection break. Caught it
      before all 13 repos landed (7 already pushed), reverted every repo back to `<0.137.0` (unified-trading-library,
      agent-orchestrator, market-tick-data-service, greeks-service, alerting-service, deployment-api, features-service —
      each via a fresh revert commit + full QG + quickmerge; execution-service, client-reporting-api,
      fund-administration-service, unified-trading-api, deployment-service, strategy-service — never pushed, dropped
      locally), and re-verified `check-dependency-alignment.py --json` reports `aligned: true` fleet-wide. Full writeup:
      `plans/active/issues/slot13_fastapi_ceiling_widen_reverted_2026_07_13.md`. **Separate pre-existing blocker hit +
      resolved while shipping this todo:** PM's
      `test_capability_verdict_matrix.py::test_f47_unbuildable_venue_cells_are_not_available` regressed (unrelated to
      this todo — a stale `.qg_content_sentinel` fast-path had let a prior QG round report green without re-running the
      full suite). Declared repo-blocker `RB-cf58eb13`, verified pre-existing via clean-tree re-test, waited for
      `unified-api-contracts@c138145b` to land the actual fix, re-verified green, then shipped. Writeup:
      `plans/active/issues/pm_qg_red_f47_venue_token_regression_2026_07_13.md`. (repo: unified-trading-pm + fanned-out
      repos)
- [x] ✅ [VERIFY] P1. `bash scripts/quality-gates.sh` in system-integration-tests confirmed full-green
      (`system-integration-tests@6d7a5b6`); repo-blocker RB-e06aa00b resolved. (repo: system-integration-tests)

## Progress Log

- **2026-07-13 (slot-15, cicd, agt-48117c)** — Resolved the immediate gate-red via a per-repo `uv.lock` bump
  (click→8.4.2, pillow→12.3.0, soupsieve→2.8.4), all transitive/no-ceiling-conflict. Shipped
  `system-integration-tests@6d7a5b6`, full QG green. Left the canonical fleet-wide bump open as follow-up (prevents
  recurrence in other not-yet-hit repos).
