---
doc_type: issue
title:
  Port the stronger subprocess-based `--help` exit-code regression test (from discarded slot-5 commit b0a58bb9) onto the
  landed multi_timeframe argparse-dup fix (39cc8653)
summary: >-
  The multi_timeframe `--help` argparse-dup crash (`argument --start-date: conflicting option string`) was fixed on
  origin via features-service@39cc8653 (remove the duplicate `_extra_args()` registrations; use ServiceBootstrap's
  `add_date_args=True` default — the majority sports/commodity convention). A second, mutually-exclusive fix for the
  same bug (slot-5 commit b0a58bb9, `add_date_args=False` + keep custom registrations, the onchain-outlier approach) was
  correctly DISCARDED as superseded (never reached origin; slot 5 died and its worktree was reset to origin HEAD). BUT
  b0a58bb9 shipped a genuinely STRONGER regression test than 39cc8653's: a subprocess `--help` exit-code check that
  forces `CLOUD_MOCK_MODE=false`, catching a test-pollution class that 39cc8653's in-process parser-construction test
  misses (an integration module sets `CLOUD_MOCK_MODE=true` at import time, which leaks process-wide and short-circuits
  before the real parser is built; and ServiceBootstrap funnels ANY exception into the same `sys.exit(1)`, so
  `pytest.raises( SystemExit)` alone can't distinguish a working `--help` from a broken one). This todo ports that
  better test onto the landed fix. The source commit b0a58bb9 is dangling in slot-5's local clone only (never pushed)
  and GCs in ~2 weeks — so the full test body is embedded below, making this todo self-contained and GC-proof.
status: open
nature: issue
asset_group: [meta]
stage: [meta]
repos: [features-service]
scope: [engineer]
tags: [features-service, multi-timeframe, cli, argparse, test-hardening, regression-test, cloud-mock-mode, cosmetic]
related: []
created: "2026-08-01"
last_updated: "2026-08-03"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: backend_engineer
priority: P3
drift_direction: advance-code
source: [review-role-finding-agt-35d7d3, main-orchestrator-triage-agt-26fe12]
resolved_by:
locked_by:
locked_since:
depends_on: []
context_scope:
  [
    features-service/tests/multi_timeframe/unit/test_cli_main.py,
    features-service/tests/multi_timeframe/integration/test_mtf_deps_integration.py,
    features-service/tests/unit/test_cli_dispatch.py,
  ]
---

# What

The `features_service.multi_timeframe` CLI `--help` argparse-duplicate crash is FIXED on origin
(`features-service@39cc8653`). During the same-day same-bug race, a discarded alternative fix (slot-5 `b0a58bb9`)
carried a **stronger regression test** than the one that landed. `39cc8653`'s test is in-process (constructs the parser
and asserts `SystemExit`); `b0a58bb9`'s is a **subprocess `--help` exit-code check with `CLOUD_MOCK_MODE=false`
forced**, which catches a real test-pollution gotcha the in-process test cannot. This todo ports the stronger test onto
the landed fix.

# Why it matters

Two blind spots the in-process test has, that the subprocess test closes:

1. **`CLOUD_MOCK_MODE` leak**: `tests/multi_timeframe/integration/test_mtf_deps_integration.py` calls
   `os.environ.setdefault("CLOUD_MOCK_MODE", "true")` at MODULE IMPORT time. Once that module is collected in a full
   run, mock mode leaks process-wide and short-circuits before the real ServiceBootstrap parser is ever built — silently
   defeating the regression check. The subprocess test forces `CLOUD_MOCK_MODE=false` in the child env.
2. **`sys.exit(1)` funnel**: ServiceBootstrap's top-level handler converts ANY exception (including the `ArgumentError`
   this bug raised) into the same `sys.exit(1)` a real crash uses — so `pytest.raises(SystemExit)` alone can't tell a
   working `--help` from a broken one. Asserting `returncode == 0` from a real subprocess `--help` invocation does.

# Follow-up todo

- [x] ✅ [BACKEND] P3. Port the subprocess-based `--help` exit-code regression test below onto the landed
      `multi_timeframe` — features-service@0f894013 (added `test_cli_help_exits_zero_via_subprocess` to
      `tests/multi_timeframe/unit/test_cli_main.py`; confirmed PASSES against landed fix `39cc8653` and FAILS with the
      exact `ArgumentError: argument --start-date:     conflicting option string` when the parser-construction dup is
      reintroduced, matching this todo's done-when). argparse-dup fix (`features-service@39cc8653`), in
      `tests/multi_timeframe/unit/test_cli_main.py`. Confirm it PASSES against the landed fix and FAILS if the fix is
      reverted (parser-construction dup restored). Cite this doc + source SHA `b0a58bb9` in the commit. The test body
      (verbatim from the discarded `b0a58bb9`, so no reflog recovery is needed once this doc lands):

```python
    def test_cli_help_exits_zero_via_subprocess(self) -> None:
        """Regression: `python -m features_service.multi_timeframe --help` used to crash
        during parser CONSTRUCTION with `argparse.ArgumentError: argument --start-date:
        conflicting option string: --start-date` -- ServiceBootstrap's own
        `add_date_args=True` default registers --start-date/--end-date, and _extra_args
        registered them again without opting out via `add_date_args=False`. Note the
        CLOUD_MOCK_MODE-gated `test_main_help_exits` above does NOT catch this class of
        regression: mock mode short-circuits before the real parser is ever built, and
        even off mock mode, ServiceBootstrap's top-level handler converts ANY exception
        (including this ArgumentError) into the same `sys.exit(1)` a real crash would use,
        so `pytest.raises(SystemExit)` alone can't tell a working --help from a broken
        one. Invoking the actual `__main__` entry point via subprocess (mirroring the
        finding's own repro command and the project's established
        `tests/unit/test_cli_dispatch.py::test_version_via_subprocess_exits_clean`
        pattern) exercises the REAL shipped ServiceBootstrap(...) wiring end-to-end and
        asserts the specific exit code that only a genuine, successful --help produces.

        CLOUD_MOCK_MODE is forced to "false" (not just left unset): running the whole
        suite, `tests/multi_timeframe/integration/test_mtf_deps_integration.py` sets
        `os.environ.setdefault("CLOUD_MOCK_MODE", "true")` at MODULE IMPORT time, which
        leaks process-wide once that module is collected and would otherwise let the
        child inherit mock mode -- short-circuiting before the real parser is built and
        silently defeating this exact regression check.
        """
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, "-m", "features_service.multi_timeframe", "--help"],
            capture_output=True,
            text=True,
            check=False,
            env={
                **os.environ,
                "GCP_PROJECT_ID": "test-project",
                "CLOUD_PROVIDER": "local",
                "CLOUD_MOCK_MODE": "false",
            },
            timeout=60,
        )
        assert result.returncode == 0, f"stdout: {result.stdout}\nstderr: {result.stderr}"
```

## Progress Log

- **na-eligibility-audit 2026-08-03** (infra tranche, dispatch agt-a41abf): **RECLASSIFY -> planning.** First verdict
  for this doc. Read end-to-end; `grep -cE '^- \[ \]'` = **1**, matching this verdict's single item. The sole open todo
  is fully bounded and deterministic: exact target file (`tests/multi_timeframe/unit/test_cli_main.py`), exact test body
  given verbatim in this doc (no judgment call on what to write), exact done-when (passes against the landed fix, fails
  if the fix is reverted), exact commit-citation requirement (this doc + source SHA `b0a58bb9`). No redirect banner, no
  `depends_on` gate, no prior-revert marker, no operator-only action — a worker can execute this alone. Conflict-check
  (`ao-dispatch-batch-naming-and-conflict-check.md` §3) run: grepped `plans/active/*.md` + `plans/active/issues/*.md`
  for `b0a58bb9` / `test_cli_help_exits_zero_via_subprocess` / `multi_timeframe.*argparse` — no other active doc claims
  this test-port work; `infra_consolidated_closeout_2026_07_25.md` doesn't mention it either. Independently confirmed
  live in `features-service` (clean worktree, `live-defi-rollout`, `39cc8653` present): the weaker
  `test_main_help_exits` test exists, the stronger subprocess-based test this todo ports does NOT exist yet — genuinely
  undone, not stale. Flipped `assigned_vm: NA -> planning`, `execution_scope: local-only -> orchestrator-agent`, filled
  `assigned_role: backend_engineer` (matches the todo's own `[BACKEND]` tag; validated against the live `agents/*.md`
  registry). `doc_type: issue` living under `plans/active/issues/` is structurally exempt from the
  finalize-plan-coverage rule (`check_finalize_plan_coverage.py` globs `plans/active/*.md` only, non-recursive —
  confirmed by direct source read) — no companion finalize doc authored.
- **context-scout 2026-08-03**: populated context_scope (3 entries).
