---
doc_type: issue
title:
  Fleet QG-red findings surfaced while unblocking PM's workflow-template-parity gate — golden-fixture drift + pip-audit
  CVEs
summary:
  Chasing PM's `workflow-template-parity` QG failure (blocking ALL unified-trading-pm commits fleet-wide) traced to a
  legit same-day SSOT fix (escalation-dispatch target bug) not yet rolled out to 4 repos. Fixed + shipped the
  deployment-api leg (the only genuinely NEW/blocking one — the other 3 are baseline-grandfathered so didn't block PM).
  While probing why those 3 repos' own quality-gates.sh were independently red, found two separate real findings outside
  data_engineering craft scope — instruments-service has a sports odds-bookmaker golden-fixture drift (47→27), and
  e2e-testing + system-integration-tests both fail on pip-audit CVEs in shared deps
  (pyasn1/pydantic-settings/setuptools/starlette/ujson).
status: open
nature: process
asset_group: [cross-cutting, sports]
stage: [meta]
repos: [instruments-service, e2e-testing, system-integration-tests, unified-trading-pm]
scope: [engineer, admin]
tags: [quality-gates, ci-cd, dependencies, sports, workflow-templates, findings]
related: []
created: 2026-07-22
parent_epic: infrastructure_master
priority: P2
assigned_vm: planning
source: [data_engineering slot-8, dispatched to sports_p2_history_apifootball_2015_to_present-001, 2026-07-22T03:45Z]
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
---

## What I found

1. **PM's `workflow-template-parity` QG check (blocking, fleet-wide)** flagged 4 repos with drifted
   `.github/workflows/main-backmerge-to-ldr.yml` copies vs the SSOT
   (`unified-trading-pm/scripts/workflow-templates/main-backmerge-to-ldr.yml`, fixed at `unified-trading-pm@1abc3c07`
   2026-07-22T01:59:18Z — the escalation-dispatch target was `${GITHUB_REPOSITORY}` instead of always
   `unified-trading-pm`, silently no-opping backmerge-conflict escalation for every repo except PM itself). Only
   `deployment-api` was genuinely **NEW** drift (the other 3 — instruments-service/e2e-testing/system-integration-tests
   — are already baseline-grandfathered, so they do NOT block PM's gate even though their copies are also stale).
   **FIXED + SHIPPED**: rolled out the template to deployment-api only
   (`bash scripts/workflow-templates/rollout-workflow-templates.sh --template main-backmerge-to-ldr.yml`), QG green,
   shipped `deployment-api@4dafc9c3`. Confirmed post-fix: `detect_template_drift.py --workflows` now reads "NEW drift
   (blocking): 0".

2. **instruments-service — pre-existing, unrelated test failure blocking its own QG**:
   `tests/unit/scripts/test_expected_universe_golden.py::TestGoldenByteIdentical::test_expected_matches_golden[sports]`
   fails — golden fixture expects 47 `(bookmaker, odds, trades)` combos for the sports asset_group, actual registry only
   produces 27 (20 bookmakers missing, e.g. BETMGM/BETONLINEAG/BETOPENLY/BETRIVERS/BETSSON/BETVICTOR/BETWAY/
   BOVADA/CASUMO/CORAL + others). Verified pre-existing via stash-and-rerun on a clean tree (my session's only change in
   this repo was the workflow-template rollout, unrelated). Root cause not investigated (out of data_engineering scope
   for this dispatch — needs whoever owns the sports odds-bookmaker registry to determine whether the 20-bookmaker
   shrink is an intentional registry change that needs the golden fixture regenerated, or a real regression).

3. **e2e-testing + system-integration-tests — pre-existing pip-audit CVEs blocking QG (same dependency class both
   repos)**: `pip-audit` finds 10 known vulnerabilities across 5 shared packages — `pyasn1 0.6.3` (CVE-2026-59885,
   CVE-2026-59886, fix 0.6.4), `pydantic-settings 2.14.1` (GHSA-4xgf-cpjx-pc3j, fix 2.14.2), `setuptools 82.0.1`
   (PYSEC-2026-3447, fix 83.0.0), `starlette 1.2.1` (PYSEC-2026-248/249, fix 1.3.0/1.3.1), `ujson 5.12.1`
   (PYSEC-2026-2294, fix 5.13.0). Verified pre-existing on e2e-testing via stash-and-rerun (clean-tree
   `uv run pip-audit` reproduces byte-identical). Not independently re-verified on system-integration-tests (same
   violation signature, same shared dependency tree via the editable-workspace closure — high confidence same root
   cause) — flag for whoever picks this up to double-check if in doubt. Not attempted: bumping 5 packages across 2+
   repos needs re-test for breaking changes (starlette 1.2→1.3, pydantic-settings 2.14.1→2.14.2 especially) — out of
   scope for a single-dispatch fix.

## Why it matters

Both #2 and #3 are genuine `quality-gates.sh` failures in their own repos (independent of the workflow-template finding)
— they block ANY future commit to instruments-service / e2e-testing / system-integration-tests until fixed, the same
class of fleet-wide friction the workflow-template finding caused for PM. #1's remaining 3 repos (still carrying the
same escalation-dispatch bug, just grandfathered) means backmerge-conflict escalation is STILL silently broken for
instruments-service/e2e-testing/system-integration-tests today — low urgency (advisory-only signal loss, not
data-correctness) but worth closing once each repo's QG is independently green anyway.

## Recommended decision

Fix each independently, gated on repo-appropriate ownership (not this dispatch — out of `data_engineering` craft scope
and each needs real investigation/re-test, not a mechanical fix):

- [x] ✅ [BACKEND] P2. Determine whether instruments-service's sports odds-bookmaker golden fixture (47→27 combos) is a
      stale fixture needing regeneration (per the test's own docstring recipe) or a real registry regression — then fix
      accordingly. (repo: instruments-service) — RESOLVED, no new code needed. Root cause: the 47→27 shrink is a real,
      intentional registry change — `unified-api-contracts@9908520b` "purge 19/20 ODDS_API fan-out bookmakers from
      canonical sports venues (operator ruling 2026-07-22)". The instruments-service golden fixture
      (`tests/unit/scripts/goldens/expected_universe/sports.json`) was stale against that UAC change at the time slot-8
      found it, but has since been regenerated (incidentally, as part of an unrelated defi/LRT commit that reran the
      regen script across all asset groups) at `instruments-service@9553faca`. Verified on a fresh-pulled tree
      (`uv run pytest tests/unit/scripts/test_expected_universe_golden.py -v`): all 14 tests pass, including
      `test_expected_matches_golden[sports]` and `test_golden_tuple_count_matches_metadata[sports]` — golden now reads
      27 tuples, byte-identical to `build_expected("sports")`. No fix commit needed from this task —
      instruments-service@9553faca.
- [ ] [BACKEND] P2. Bump `pyasn1`→0.6.4, `pydantic-settings`→2.14.2, `setuptools`→83.0.0, `starlette`→1.3.1,
      `ujson`→5.13.0 in e2e-testing (re-test for breaking changes, esp. starlette 1.2→1.3), ship via normal QG+
      quickmerge flow. (repo: e2e-testing)
- [ ] [BACKEND] P2. Same CVE bump as e2e-testing above — confirm same violation signature first (`uv run pip-audit`),
      then bump + re-test + ship. (repo: system-integration-tests)
- [ ] [INFRA] P3. Once each of the 3 repos above is independently QG-green, roll out `main-backmerge-to-ldr.yml`
      (`bash unified-trading-pm/scripts/workflow-templates/rollout-workflow-templates.sh     --template main-backmerge-to-ldr.yml --repo <repo>`)
      to fix the same escalation-dispatch-target bug fixed in deployment-api@4dafc9c3, then QG+quickmerge ship. (repos:
      instruments-service, e2e-testing, system-integration-tests)
