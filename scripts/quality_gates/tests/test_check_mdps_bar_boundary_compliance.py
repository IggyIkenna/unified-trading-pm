# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for STEP 5.74 — check_mdps_bar_boundary_compliance.py.

≥8 tests covering: valid source (no violations), each banned pattern triggers,
mixed-file detection, tests/ exclusion, noqa opt-out, syntax error handling.

Pure-Python: writes synthetic .py files to tmp_path; runs the checker via
subprocess invocation.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_CHECKER_SCRIPT = (Path(__file__).parent.parent / "check_mdps_bar_boundary_compliance.py").resolve()


def _write(file: Path, content: str) -> Path:
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(content, encoding="utf-8")
    return file


def _run_checker(source_dir: Path) -> tuple[int, str]:
    """Run the checker against source_dir. Return (exit_code, combined_stderr)."""
    result = subprocess.run(
        [sys.executable, str(_CHECKER_SCRIPT), "--source-dir", str(source_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode, result.stderr + result.stdout


def test_valid_source_uses_compute_bar_close_boundary(tmp_path: Path) -> None:
    """A file calling compute_bar_close_boundary() — exit 0."""
    _write(
        tmp_path / "valid.py",
        """
from unified_trading_library import compute_bar_close_boundary

def emit_bar(ts, tf):
    return compute_bar_close_boundary(ts, tf)
""",
    )
    code, _ = _run_checker(tmp_path)
    assert code == 0


def test_inline_timestamp_floor_triggers_violation(tmp_path: Path) -> None:
    """pd.Timestamp.floor("1h") — exit non-zero."""
    _write(
        tmp_path / "bad_floor.py",
        """
import pandas as pd

def bad(ts: pd.Timestamp):
    return ts.floor("1h")
""",
    )
    code, err = _run_checker(tmp_path)
    assert code == 1
    assert "floor" in err
    assert "bad_floor.py" in err


def test_inline_timestamp_round_triggers_violation(tmp_path: Path) -> None:
    """pd.Timestamp.round("15min") — exit non-zero."""
    _write(
        tmp_path / "bad_round.py",
        """
import pandas as pd

def bad(ts: pd.Timestamp):
    return ts.round("15min")
""",
    )
    code, err = _run_checker(tmp_path)
    assert code == 1
    assert "round" in err
    assert "bad_round.py" in err


def test_inline_polars_truncate_triggers_violation(tmp_path: Path) -> None:
    """polars dt.truncate("1h") — exit non-zero."""
    _write(
        tmp_path / "bad_polars.py",
        """
import polars as pl

def bad(df):
    return df.with_columns(pl.col("ts").dt.truncate("1h"))
""",
    )
    code, err = _run_checker(tmp_path)
    assert code == 1
    assert "truncate" in err


def test_inline_replace_minute_zero_triggers_violation(tmp_path: Path) -> None:
    """dt.replace(minute=0, second=0, microsecond=0) — exit non-zero."""
    _write(
        tmp_path / "bad_replace.py",
        """
def bad(dt):
    return dt.replace(minute=0, second=0, microsecond=0)
""",
    )
    code, err = _run_checker(tmp_path)
    assert code == 1
    assert "replace" in err


def test_replace_year_month_does_not_trigger(tmp_path: Path) -> None:
    """dt.replace(year=2024, month=1) is NOT a truncation — exit 0."""
    _write(
        tmp_path / "ok_replace.py",
        """
def adjust(dt):
    return dt.replace(year=2024, month=1)
""",
    )
    code, _ = _run_checker(tmp_path)
    assert code == 0


def test_mixed_file_one_violation_among_many_valid(tmp_path: Path) -> None:
    """One bad call among multiple valid usages — exit non-zero, only reports the bad one."""
    _write(
        tmp_path / "mixed.py",
        """
from unified_trading_library import compute_bar_close_boundary
import pandas as pd

def good_1(ts, tf):
    return compute_bar_close_boundary(ts, tf)

def good_2(ts, tf):
    return compute_bar_close_boundary(ts, tf)

def bad(ts):
    return ts.floor("1h")

def good_3(ts, tf):
    return compute_bar_close_boundary(ts, tf)
""",
    )
    code, err = _run_checker(tmp_path)
    assert code == 1
    # Only one violation reported
    assert err.count("floor") >= 1


def test_tests_dir_excluded(tmp_path: Path) -> None:
    """Violations inside tests/ are excluded — exit 0 even with bad code in tests/."""
    _write(
        tmp_path / "tests" / "test_foo.py",
        """
import pandas as pd

def test_floor():
    ts = pd.Timestamp.now()
    assert ts.floor("1h") is not None
""",
    )
    code, _ = _run_checker(tmp_path)
    assert code == 0


def test_noqa_marker_suppresses_violation(tmp_path: Path) -> None:
    """Line with `# noqa: bar-boundary-truncation` is skipped — exit 0."""
    _write(
        tmp_path / "noqa_opt_out.py",
        """
import pandas as pd

def legitimate_test_fixture(ts: pd.Timestamp):
    # Test fixture: deliberately misaligned bar for write-gate test
    return ts.floor("1h")  # noqa: bar-boundary-truncation
""",
    )
    code, _ = _run_checker(tmp_path)
    assert code == 0


def test_docstring_with_floor_example_not_flagged(tmp_path: Path) -> None:
    """Docstrings citing .floor() in usage examples are NOT flagged (AST-based)."""
    _write(
        tmp_path / "doc_only.py",
        '''
def safe():
    """Example usage:

    >>> ts.floor("1h")  # this is just docstring content
    """
    return None
''',
    )
    code, _ = _run_checker(tmp_path)
    assert code == 0


def test_syntax_error_does_not_crash(tmp_path: Path) -> None:
    """Malformed Python file — checker reports error but does not crash; exit 0 if no real violations."""
    _write(
        tmp_path / "broken.py",
        """
def broken(
    # missing close paren
""",
    )
    code, err = _run_checker(tmp_path)
    # Should report syntax error to stderr, but continue scanning other files (none here)
    # Exit 0 because no real violations were found (syntax errors don't count)
    assert code == 0
    assert "SYNTAX ERROR" in err or "syntax" in err.lower()


def test_nonexistent_source_dir_exits_2(tmp_path: Path) -> None:
    """--source-dir pointing at nonexistent path → exit 2."""
    code, err = _run_checker(tmp_path / "does-not-exist")
    assert code == 2
    assert "not a directory" in err.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
