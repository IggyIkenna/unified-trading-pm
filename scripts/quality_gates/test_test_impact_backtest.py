# Epic: deployment_and_user_management_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for test_impact_backtest.py's failure-attribution logic.

Real CI logs are messy (see test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md's
Progress Log, 2026-08-03 backtest entry) — these fixtures mirror the two real
shapes found live: a clean pytest short-summary FAILED line, and a Timeout/crash
mid-test whose last traceback frame names the stuck test file. A run with
neither shape (an infra-level SIGINT/OSError kill) must return None, never a
guessed attribution.
"""

from __future__ import annotations

from test_impact_backtest import attribute_failure  # type: ignore[import-not-found]


def _gh_log(lines: list[str]) -> str:
    # gh's --log format prefixes every line with "<job>\t<step>\t<content>".
    return "\n".join(f"job\tstep\t{line}" for line in lines)


def test_attribute_failure_clean_pytest_summary() -> None:
    log = _gh_log(
        [
            "QG_SLICE=tests --",
            "........F..............",
            "=========================== short test summary info ===========================",
            "FAILED tests/unit/test_thing.py::test_it_works - AssertionError: boom",
            "1 failed, 99 passed in 12.34s",
            "##[error]QG selector 'tests' FAILED (leg=tests, exit=1)",
        ]
    )
    result = attribute_failure(123, "abc123", log)
    assert result is not None
    assert result.failing_test_files == frozenset({"tests/unit/test_thing.py"})
    assert result.attribution_method == "pytest_failed_nodeid"


def test_attribute_failure_timeout_traceback_fallback() -> None:
    log = _gh_log(
        [
            "QG_SLICE=tests --",
            '  File "/opt/runner/_work/repo/repo/tests/unit/test_slow.py", line 42, in test_it_hangs',
            "    result = compute_thing()",
            "+++++++++++++++++++++++++++++++++++ Timeout ++++++++++++++++++++++++++++++++++++",
            "##[error]QG selector 'tests' FAILED (leg=tests, exit=1)",
        ]
    )
    result = attribute_failure(456, "def456", log)
    assert result is not None
    assert result.failing_test_files == frozenset({"tests/unit/test_slow.py"})
    assert result.attribution_method == "traceback_last_test_frame"


def test_attribute_failure_unattributable_infra_kill_returns_none() -> None:
    log = _gh_log(
        [
            "QG_SLICE=tests --",
            "........................................",
            "WARNING Received SIGINT -- initiating graceful shutdown",
            "OSError: cannot send (already closed?)",
            "##[error]QG selector 'tests' FAILED (leg=tests, exit=1)",
        ]
    )
    result = attribute_failure(789, "ghi789", log)
    assert result is None


def test_attribute_failure_not_a_tests_leg_failure_returns_none() -> None:
    log = _gh_log(
        [
            "QG_SLICE=checks --",
            "##[error]QG selector 'checks' FAILED (leg=checks, exit=1)",
        ]
    )
    result = attribute_failure(101, "jkl101", log)
    assert result is None


def test_attribute_failure_prefers_clean_summary_over_traceback() -> None:
    # If BOTH shapes somehow appear (e.g. one test times out, another asserts),
    # the clean pytest summary is authoritative — it enumerates every real
    # failure, while the traceback fallback is only a last-resort single guess.
    log = _gh_log(
        [
            '  File "/opt/runner/_work/repo/repo/tests/unit/test_unrelated.py", line 1, in test_x',
            "=========================== short test summary info ===========================",
            "FAILED tests/unit/test_real_failure.py::test_y - AssertionError",
            "##[error]QG selector 'tests' FAILED (leg=tests, exit=1)",
        ]
    )
    result = attribute_failure(202, "mno202", log)
    assert result is not None
    assert result.failing_test_files == frozenset({"tests/unit/test_real_failure.py"})
    assert result.attribution_method == "pytest_failed_nodeid"
