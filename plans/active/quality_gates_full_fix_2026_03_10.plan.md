---
name: Quality Gates Full Fix — All Repos Pass Unit Tests + Coverage
overview: >
  Systematically run unit tests (RUN_INTEGRATION=false) across all repos, fix every failing test and coverage gap
  properly. No bypasses. No type:ignore hacks. No test exemptions. Fix root causes.

  Coverage targets:
    - T0–T3 libraries: >= 80%
    - Services / APIs: >= 70%
    - Exceptions (exactly 4 repos, designated below): allowed below 70%
    - UIs: no Python coverage target; smoke tests required

  Permitted < 70% repos (real-time / tick-level repos with tiny unit-test surface):
    1. market-tick-data-service    (live-tick ingestion, integration-only meaningful tests)
    2. execution-service           (1200+ tests but heavy integration surface; 26% placeholder)
    3. features-commodity-service  (early-stage, <15 tests currently)
    4. market-data-processing-service (pipeline throughput service)

  All other repos must meet targets above. Fix tests — do not lower thresholds.
isProject: true
todos:
  - id: baseline-run
    content: >
      Run RUN_INTEGRATION=false bash unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --test
      --skip-alignment --skip-setup  from workspace root. Capture full output to plans/active/work/qg_run_baseline.log.
      Parse FAIL lines → issue log.
    status: completed
    notes: |
      Running in background. Output written to work/qg_run_baseline.log.
      Issue log appended to work/qg_issues.md as results arrive.

  - id: issue-log
    content: >
      Maintain plans/active/work/qg_issues.md — canonical issue tracker. Columns: repo | issue_type
      (test_fail|coverage|import_error) | details | agent_id | status. Never delete rows — only update status (open →
      in_progress → fixed → verified).
    status: in_progress
    notes: See work/qg_issues.md

  - id: fix-t0-libraries
    content: >
      Fix all T0 libraries failing QG (tests + coverage >= 80%): unified-internal-contracts, matching-engine-library,
      execution-algo-library, unified-api-contracts. Spawn one agent per failing repo.
    status: pending

  - id: fix-t1-libraries
    content: >
      Fix all T1 libraries failing QG (tests + coverage >= 80%): unified-events-interface, unified-config-interface,
      unified-trading-library (currently 78% — needs +2%).
    status: pending

  - id: fix-t2-libraries
    content: >
      Fix all T2 libraries failing QG (tests + coverage >= 80%): unified-market-interface (40% — major gap),
      unified-trade-execution-interface, unified-ml-interface, unified-position-interface,
      unified-reference-data-interface, unified-defi-execution-interface, unified-feature-calculator-library,
      unified-sports-execution-interface (76% — below 80%).
    status: pending
    notes: |
      unified-market-interface at 40% is the biggest library gap.
      unified-sports-execution-interface at 76% needs ~4% more.
      unified-trading-library at 78% needs ~2% more.
      execution-algo-library at 72% needs ~8% more.

  - id: fix-t3-libraries
    content: >
      Fix all T3 libraries failing QG (tests + coverage >= 80%): unified-domain-client (84% — already passing).
    status: pending

  - id: fix-service-repos
    content: >
      Fix all service/API repos failing QG (tests + coverage >= 70%, except 4 exempt repos): alerting-service,
      client-reporting-api (18%!), deployment-api, deployment-service, execution-results-api (66%),
      features-calendar-service, features-cross-instrument-service (65%), features-delta-one-service,
      features-multi-timeframe-service (57%), features-onchain-service (39%), features-sports-service,
      features-volatility-service (35%), instruments-service (53%), market-data-api, ml-inference-service,
      ml-training-service (35%), pnl-attribution-service (46%), position-balance-monitor-service,
      risk-and-exposure-service, strategy-service, strategy-validation-service, trading-agent-service (50%),
      ml-inference-api, ml-training-api, trading-analytics-api (new repos — unknown coverage).
    status: pending
    notes: |
      Spawn one agent per repo. Agent must:
      1. cd <repo> && .venv/bin/pytest tests/unit/ -v --cov=<pkg> --cov-report=xml --cov-report=term-missing
      2. Identify all failing tests + coverage gaps
      3. Fix root causes (no mocks that bypass logic, no skip markers)
      4. Re-run to verify >= 70% and 0 test failures
      5. Commit with "test: fix unit tests in <repo>"

  - id: fix-ui-smoke-tests
    content: >
      Verify UI repos have thorough smoke tests (vitest + Playwright where applicable). Repos: deployment-ui,
      execution-analytics-ui, live-health-monitor-ui, logs-dashboard-ui, ml-training-ui, onboarding-ui, settlement-ui,
      strategy-ui, trading-analytics-ui, client-reporting-ui, batch-audit-ui, unified-trading-ui-auth.
    status: pending
    notes: |
      UIs have testing_level=unit. Check that quality-gates.sh runs vitest + coverage.
      If vitest coverage < reasonable threshold (60% statements), improve smoke coverage.

  - id: verify-no-bypasses
    content: >
      After all fix agents complete: run full QG scan to confirm no bypass patterns introduced. Check: no
      pytest.mark.skip without reason, no # type: ignore, no || true in QG scripts, no coverage threshold lowered below
      target, no test deleted (only fixed).
    status: pending

  - id: update-manifest-coverage
    content: >
      After verified green: run coverage-audit.py to update workspace-manifest.json with real coverage_pct values per
      repo. Commit to unified-trading-pm.
    status: pending

  - id: final-qg-run
    content: >
      Run full QG one last time to confirm all repos pass. RUN_INTEGRATION=false bash
      unified-trading-pm/scripts/repo-management/run-all-quality-gates.sh --test --skip-alignment --skip-setup Expected:
      0 FAIL rows.
    status: pending

  # ── Coverage SSOT alignment action items (added 2026-03-10) ──────────────────

  - id: audit-dual-coverage-sources
    content: >
      Audit the dual coverage enforcement sources across all 49+ repos that have fail_under in pyproject.toml.
      For each repo: compare [tool.coverage.report] fail_under vs scripts/quality-gates.sh MIN_COVERAGE.
      Produce a diff table: repo | qg_min | toml_fail_under | delta | verdict (in-sync / stale-toml / stale-qg).
      Run from workspace root:
        python3 unified-trading-pm/scripts/repo-management/coverage-audit.py --json > /tmp/cov_audit.json
        grep -r "fail_under" */pyproject.toml | grep -v ".venv" > /tmp/toml_fail_under.txt
      Then reconcile. Expected: 0 delta rows after fix.
    status: pending
    notes: |
      Root finding (2026-03-10): Two active enforcement sources are not in sync.
        1. scripts/quality-gates.sh: MIN_COVERAGE=<N> → pytest --cov-fail-under=$MIN_COVERAGE (authoritative in CI)
        2. pyproject.toml: [tool.coverage.report] fail_under = <N> → pytest reads this when run WITHOUT --cov-fail-under
      rollout-quality-gates-unified.py updates ONLY (1). pyproject.toml (2) is set manually and drifts.
      coverage-audit.py reads ONLY (1). So the toml value is an invisible second gate that can fire when
      developers run `pytest` locally without the QG wrapper — they may see a different pass/fail than CI.
      Examples found: alerting-service QG=82 vs toml=78 (toml stale); instruments-service both=70 (in sync).
      Additional coverage scripts found (2026-03-10) — must be checked for consistency:
        - unified-trading-pm/scripts/audit/generate-quality-gates-coverage-report.py (separate report generator)
        - instruments-service/scripts/run_quality_gates.py (repo-local QG runner)
        - unified-trading-library/scripts/run_quality_gates.py (repo-local QG runner)
        - market-tick-data-service/scripts/run_quality_gates.py + generate_coverage_report.py
      These per-repo run_quality_gates.py scripts may have their own hardcoded coverage thresholds that
      diverge from both quality-gates.sh MIN_COVERAGE and pyproject.toml fail_under — a third source of drift.

  - id: fix-ssot-rollout-to-sync-toml
    content: >
      Extend rollout-quality-gates-unified.py to also sync [tool.coverage.report] fail_under in pyproject.toml
      to match the computed MIN_COVERAGE value.
      Rule: the pyproject.toml fail_under must equal MIN_COVERAGE (the QG script value is authoritative).
      Implementation: after writing quality-gates.sh, parse pyproject.toml with tomllib/tomli_w and update
      [tool.coverage.report] fail_under. Only modify if the value differs. Write back preserving structure.
      Guard: if pyproject.toml has no [tool.coverage.report] section, skip (don't create one).
      Run: python3 unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py --dry-run first.
      Then: --recalibrate on repos where coverage.xml is fresh (< 1 day old); floor-only mode on others.
    status: pending
    notes: |
      SSOT rule: quality-gates.sh MIN_COVERAGE is the single source of truth.
      pyproject.toml fail_under must mirror it — it is a convenience for local pytest runs, not a second gate.
      Do NOT use pyproject.toml as the primary; it cannot express max(floor, actual-1) dynamically.

  - id: fix-race-condition-recalibrate
    content: >
      Fix the stale coverage.xml race condition in rollout-quality-gates-unified.py measure_coverage().
      Current bug: fast-path reads coverage.xml if it exists without checking file age. A stale coverage.xml
      (from a different branch or before recent code changes) causes measure_coverage() to return stale data,
      setting MIN_COVERAGE to wrong value via max(floor, stale_actual - 1).
      Fix: before trusting coverage.xml, verify it is newer than the newest .py source file in the package.
        import os, stat; newest_src = max(p.stat().st_mtime for p in Path(source_dir).rglob("*.py"))
        xml_mtime = xml_path.stat().st_mtime
        if xml_mtime < newest_src: fall through to slow path (run pytest --cov)
      Add --force-rerun flag to always use slow path regardless of xml age.
      Document: coverage-audit.py reads coverage.xml too — same staleness risk exists there. Add warning
      header to audit output if any coverage.xml is older than its source tree.
    status: pending
    notes: |
      This is not a true concurrency race (no threads). It is a staleness race:
        read-stale-xml → set-wrong-MIN_COVERAGE → commit → CI fails / passes incorrectly.
      The --recalibrate mode is meant to run after tests pass, so coverage.xml SHOULD be fresh then.
      But if rollout is run across all repos (not per-repo), some repos may have old xml from prior runs.

  - id: check-propagation-does-not-break-coverage
    content: >
      Verify that running rollout-quality-gates-unified.py without --recalibrate does NOT degrade any repo's
      MIN_COVERAGE below its current value (only raises to floor if below floor, never lowers).
      Verify the formula logic in copy_quality_gates():
        no-recalibrate: new_coverage = max(floor, existing_int or floor) — can only raise, never lower ✓
        recalibrate:    new_coverage = max(floor, actual - 1) — can lower if actual dropped legitimately
      Check: confirm base-service.sh and base-library.sh pass --cov-fail-under=$MIN_COVERAGE to pytest.
      Confirm: no pyproject.toml [tool.coverage.report] fail_under > MIN_COVERAGE (toml is stricter = bad).
      If toml fail_under > MIN_COVERAGE: toml silently rejects runs that QG would pass — fix by lowering toml.
      Run: python3 unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py --dry-run
      Confirm: no repo shows MIN_COVERAGE decreasing from current state.
    status: pending
    notes: |
      Confirmed (2026-03-10): rollout without --recalibrate is safe — max(floor, existing) never lowers.
      Risk: --recalibrate on repos with stale coverage.xml can lower MIN_COVERAGE if stale xml is low.
      This is why fix-race-condition-recalibrate must be done BEFORE running --recalibrate workspace-wide.

  - id: check-alignment-scripts-help-hinder
    content: >
      Run and evaluate all alignment/propagation scripts to confirm none degrade coverage config:
        1. python3 unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py --dry-run
           Expected: raises any below-floor MIN_COVERAGE; does NOT lower any above-floor value.
        2. bash unified-trading-pm/scripts/repo-management/run-version-alignment.sh --dry-run (if --dry-run exists)
           Expected: version alignment; no interaction with coverage values.
        3. python3 unified-trading-pm/scripts/repo-management/coverage-audit.py
           Expected: [C] INFO rows show stale thresholds; no [A] FAIL regressions from alignment runs.
        4. python3 unified-trading-pm/scripts/propagation/rollout-quality-gates-unified.py --recalibrate --dry-run
           Expected: preview shows max(floor, actual-1) per repo; no values < floor.
      After each dry-run: verify no repo's MIN_COVERAGE would be lowered below its floor.
      Document: alignment script verdict (helps / neutral / hinders) per script.
    status: pending
    notes: |
      Alignment scripts evaluated (2026-03-10 discovery run):
        rollout-quality-gates-unified.py (no --recalibrate): HELPS — enforces floor, never lowers
        rollout-quality-gates-unified.py (--recalibrate):     RISKY if stale xml (see race condition fix)
        run-version-alignment.sh:                             NEUTRAL — does not touch coverage config
        coverage-audit.py:                                   HELPS — read-only audit; raises [C] INFO on drift
        deployment-service/scripts/check_test_alignment.sh:  UNKNOWN — repo-local; must read before verdict
        unified-trading-codex/scripts/validate-alignment.py: NEUTRAL — codex doc validator; skips broken symlinks
        manifest/check-dependency-alignment.py:              NEUTRAL — package version checks only
        manifest/fix-internal-dependency-alignment.py:       NEUTRAL — package version fixes only
      Blocking issue: rollout does NOT sync pyproject.toml fail_under — this HINDERS because
        local pytest (no QG wrapper) uses toml value; CI uses QG MIN_COVERAGE; two different outcomes possible.

  - id: verify-ui-coverage-floor
    content: >
      Verify UI repos have vitest coverage configured with a floor matching the SSOT.
      SSOT standard: UIs must have smoke tests; no Python coverage floor; vitest statement coverage >= 60%.
      Current state: quality-gates-ui-template.sh is deployed but does it enforce a vitest coverage floor?
      Check: cat unified-trading-codex/06-coding-standards/quality-gates-ui-template.sh
      Confirm: vitest --coverage is called and coverage/coverage-summary.json is produced.
      Confirm: coverage-audit.py parse_ui_coverage() reads coverage/coverage-summary.json correctly.
      If no coverage floor is enforced for UIs: add minimum of 60% lines to UI template and rollout.
      No Python fail_under issue for UI repos (no pyproject.toml); risk is vitest coverage-summary.json absent.
    status: pending
    notes: |
      UIs: deployment-ui, execution-analytics-ui, live-health-monitor-ui, logs-dashboard-ui, ml-training-ui,
      onboarding-ui, settlement-ui, strategy-ui, trading-analytics-ui, client-reporting-ui, batch-audit-ui,
      unified-trading-ui-auth. These have no Python fail_under. Risk is vitest coverage not being generated.
---

# Quality Gates Full Fix — 2026-03-10

**Goal:** Every repo passes unit tests with zero failures and meets coverage targets. No bypasses.

---

## Coverage Targets

| Category        | Target      | Exempt repos                                                                                            |
| --------------- | ----------- | ------------------------------------------------------------------------------------------------------- |
| T0–T3 libraries | >= 80%      | none                                                                                                    |
| Services / APIs | >= 70%      | market-tick-data-service, execution-service, features-commodity-service, market-data-processing-service |
| UIs             | smoke tests | no Python coverage                                                                                      |
| Codex / PM      | no tests    | testing_level=none                                                                                      |

---

## Issue Log

See [work/qg_issues.md](work/qg_issues.md) — updated live as agents complete.

---

## Agent Orchestration Protocol

1. **Master agent** (this Claude session): runs QG script, reads output, spawns fix agents, tracks log.
2. **Fix agents**: one per failing repo. Each agent:
   - Reads existing tests carefully before touching anything
   - Checks git log to see if other agents recently committed (wait 5 min if so)
   - Fixes root cause of each failing test (not the test expectation unless expectation is provably wrong)
   - Adds tests to close coverage gap — real tests that cover real logic paths
   - Re-runs `pytest tests/unit/ -v --cov=<pkg> --cov-report=xml` to verify
   - Commits with `git add` + `git commit` (NO quickmerge, NO git push without explicit instruction)
3. **No destructive git ops**: never `git reset --hard`, `git push --force`, `git branch -D` without user confirmation.
4. **Conflict avoidance**: if agent sees another agent's recent commit (within 5 min), it stages its own work with
   `git stash`, waits, then applies.

---

## Known Issues from Last Run (2026-03-09)

| Repo                               | Issues                           | Root Cause                                                          |
| ---------------------------------- | -------------------------------- | ------------------------------------------------------------------- |
| unified-market-interface           | 40% coverage, 15 test failures   | RC-A/B: stale wheel (IBKR `ib=` kwarg) + missing aave_utils exports |
| unified-trade-execution-interface  | 89% cov, 5 failures              | RC-B: stale wheel IbkrTradFiAdapter                                 |
| unified-trading-library            | 78% coverage                     | Below 80% threshold                                                 |
| execution-algo-library             | 72% coverage                     | Below 80% threshold                                                 |
| unified-sports-execution-interface | 76% coverage                     | Below 80% threshold                                                 |
| features-multi-timeframe-service   | 57% coverage, 1 env-leak failure | RC-C: CLOUD_PROVIDER env leak in test                               |
| features-onchain-service           | 39% coverage                     | Coverage gap                                                        |
| features-volatility-service        | 35% coverage                     | Coverage gap                                                        |
| ml-training-service                | 35% coverage                     | Coverage gap                                                        |
| pnl-attribution-service            | 46% coverage                     | Coverage gap + 1 env-leak failure                                   |
| position-balance-monitor-service   | 77% coverage, 1 env-leak         | RC-C: CLOUD_PROVIDER env leak                                       |
| alerting-service                   | 87% coverage, 2 failures         | RC-D: setup_events() not called before log_event() in test          |
| client-reporting-api               | 18% coverage                     | Major coverage gap                                                  |
| execution-results-api              | 66% coverage                     | Below 70% threshold                                                 |
| features-cross-instrument-service  | 65% coverage                     | Below 70% threshold                                                 |
| instruments-service                | 53% coverage                     | Coverage gap                                                        |
| trading-agent-service              | 50% coverage                     | Coverage gap                                                        |

All items above must be fully fixed. No threshold lowering. No skipping.

---

## Coverage SSOT Alignment — Added 2026-03-10

### Problem: Dual Enforcement Sources Are Out of Sync

Two independent mechanisms enforce coverage floors, and they are **not kept in sync**:

| Source | Where | Who writes it | When used |
|--------|-------|---------------|-----------|
| `MIN_COVERAGE` in `scripts/quality-gates.sh` | Each repo | `rollout-quality-gates-unified.py` (automated) | CI via `--cov-fail-under=$MIN_COVERAGE` |
| `fail_under` in `pyproject.toml` `[tool.coverage.report]` | Each repo | Manual / one-off scripts | Local `pytest` runs without the QG wrapper |

**Result:** A developer running `pytest` locally sees a different pass/fail than CI. The audit tool (`coverage-audit.py`) only reads `quality-gates.sh`, so pyproject.toml drift is invisible to audits.

**Confirmed examples (2026-03-10):**

| Repo | QG `MIN_COVERAGE` | `pyproject.toml fail_under` | Delta |
|------|--------------------|------------------------------|-------|
| `alerting-service` | 82 | 78 | −4 (toml stale) |
| `instruments-service` | 70 | 70 | 0 (in sync) |
| `unified-events-interface` | 99 | 99 | 0 (in sync) |

49+ repos have `fail_under` in `pyproject.toml`. Unknown how many are drifted.

### Problem: Stale `coverage.xml` Race in `--recalibrate` Mode

`rollout-quality-gates-unified.py measure_coverage()` fast-path reads `coverage.xml` without checking its age.
If `coverage.xml` predates recent source changes, `max(floor, stale_actual - 1)` sets the wrong `MIN_COVERAGE`.

### Coverage Formula (SSOT)

```
MIN_COVERAGE = max(floor, actual_coverage - 1)

floor:
  libraries (T0–T3):         80%
  services / api-services:   70%
  UIs:                       60% statement (vitest)
  infrastructure/test-harness: 70%
```

The `-1` tolerance allows one-point natural churn between runs without requiring constant recalibration.

### Propagation Script Verdict

| Script | Effect on coverage config | Verdict |
|--------|---------------------------|---------|
| `rollout-quality-gates-unified.py` (no flags) | Raises MIN_COVERAGE to floor; never lowers | SAFE |
| `rollout-quality-gates-unified.py --recalibrate` | Sets `max(floor, actual-1)` from coverage.xml | RISKY if xml stale |
| `run-version-alignment.sh` | No interaction with coverage | NEUTRAL |
| `coverage-audit.py` | Read-only; raises [C] INFO on QG drift | SAFE |
| `rollout-quality-gates-unified.py` on pyproject.toml | **Does NOT update toml** — this is the gap | HINDERS |

### Action Items

See todos: `audit-dual-coverage-sources`, `fix-ssot-rollout-to-sync-toml`, `fix-race-condition-recalibrate`,
`check-propagation-does-not-break-coverage`, `check-alignment-scripts-help-hinder`, `verify-ui-coverage-floor`.
