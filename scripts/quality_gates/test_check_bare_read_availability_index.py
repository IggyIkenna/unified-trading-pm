# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_bare_read_availability_index.py.

Pure-Python — no GCS/AWS/network. Mirrors
test_check_manifest_writer_missing_write_before_return.py in shape: constants
sanity, single-file scanning (bare/projected/attribute-call/nested-scope/
whitelist), workspace walker exclusions, baseline tolerance, and a main()
end-to-end smoke.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from check_bare_read_availability_index import (  # type: ignore[import-not-found]
    PROJECTION_KWARGS,
    TARGET_CALLEE_NAME,
    WHITELIST_MARKER,
    BaselineEntry,
    Finding,
    _iter_py_files,
    _scan_file,
    main,
)


def test_target_callee_name() -> None:
    assert TARGET_CALLEE_NAME == "read_availability_index"


def test_projection_kwargs_closed_set() -> None:
    assert frozenset({"columns", "filters"}) == PROJECTION_KWARGS


def _write_py(tmp_path: Path, name: str, content: str) -> Path:
    file = tmp_path / name
    file.write_text(textwrap.dedent(content), encoding="utf-8")
    return file


def test_flags_bare_call_with_no_kwargs(tmp_path: Path) -> None:
    target = _write_py(
        tmp_path,
        "reader.py",
        """
        def load(bucket):
            index = read_availability_index(bucket)
            return index
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert len(findings) == 1
    assert findings[0].function == "load"
    assert findings[0].line == 3


def test_clean_when_columns_kwarg_present(tmp_path: Path) -> None:
    target = _write_py(
        tmp_path,
        "reader.py",
        """
        def load(bucket):
            index = read_availability_index(bucket, columns=["date"])
            return index
        """,
    )
    assert _scan_file(target, repo="testrepo", repo_root=tmp_path) == []


def test_clean_when_filters_kwarg_present(tmp_path: Path) -> None:
    target = _write_py(
        tmp_path,
        "reader.py",
        """
        def load(bucket):
            index = read_availability_index(bucket, filters=[("date", "==", "2026-07-31")])
            return index
        """,
    )
    assert _scan_file(target, repo="testrepo", repo_root=tmp_path) == []


def test_flags_attribute_call_form(tmp_path: Path) -> None:
    """`module.read_availability_index(bucket)` (raw-import-under-alias /
    module-attribute access) must be caught, not just the bare Name form."""
    target = _write_py(
        tmp_path,
        "reader.py",
        """
        def load(bucket):
            index = _mw.read_availability_index(bucket)
            return index
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert len(findings) == 1


def test_whitelist_marker_on_call_line_skips_finding(tmp_path: Path) -> None:
    target = _write_py(
        tmp_path,
        "reader.py",
        f"""
        def load(bucket):
            index = read_availability_index(bucket)  # {WHITELIST_MARKER}
            return index
        """,
    )
    assert _scan_file(target, repo="testrepo", repo_root=tmp_path) == []


def test_module_level_bare_call_uses_module_placeholder(tmp_path: Path) -> None:
    target = _write_py(
        tmp_path,
        "reader.py",
        """
        INDEX = read_availability_index(BUCKET)
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert len(findings) == 1
    assert findings[0].function == "<module>"


def test_nested_function_scope_reported_independently(tmp_path: Path) -> None:
    target = _write_py(
        tmp_path,
        "reader.py",
        """
        def outer(bucket):
            def _inner(b):
                return read_availability_index(b)
            return _inner(bucket)
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert len(findings) == 1
    assert findings[0].function == "_inner"


def test_unrelated_call_not_flagged(tmp_path: Path) -> None:
    target = _write_py(
        tmp_path,
        "reader.py",
        """
        def load(bucket):
            index = read_something_else(bucket)
            return index
        """,
    )
    assert _scan_file(target, repo="testrepo", repo_root=tmp_path) == []


def test_iter_py_files_skips_venv_scripts_and_tests(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "src" / "real.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / ".venv" / "lib.py").write_text("y = 2\n", encoding="utf-8")
    (tmp_path / "tests" / "test_x.py").write_text("z = 3\n", encoding="utf-8")
    (tmp_path / "scripts" / "one_off.py").write_text("w = 4\n", encoding="utf-8")
    files = list(_iter_py_files(tmp_path))
    rels = sorted(str(f.relative_to(tmp_path)) for f in files)
    assert rels == ["src/real.py"]


def test_main_clean_returns_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = tmp_path / "myrepo"
    src = repo / "myrepo"
    src.mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname = 'myrepo'\n", encoding="utf-8")
    _write_py(
        src,
        "reader.py",
        """
        def load(bucket):
            return read_availability_index(bucket, columns=["date"])
        """,
    )
    rc = main(["--workspace-root", str(tmp_path), "--scope", "myrepo"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "OK" in captured.out


def test_main_dirty_returns_one(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    repo = tmp_path / "myrepo"
    src = repo / "myrepo"
    src.mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname = 'myrepo'\n", encoding="utf-8")
    _write_py(
        src,
        "reader.py",
        """
        def load(bucket):
            return read_availability_index(bucket)
        """,
    )
    rc = main(["--workspace-root", str(tmp_path), "--scope", "myrepo"])
    captured = capsys.readouterr()
    assert rc == 1
    assert "FAIL" in captured.err
    assert "bare 'read_availability_index(bucket)'" in captured.err


def test_finding_baseline_key_shape() -> None:
    f = Finding(repo="r", file="f.py", line=10, function="load", snippet="read_availability_index(bucket)")
    assert f.baseline_key == ("r", "f.py", 10, "load")


def test_baseline_entry_dataclass_fields() -> None:
    entry = BaselineEntry(
        repo="r",
        file="f.py",
        line=10,
        function="load",
        status="pending_triage",
        successor="read_availability_index_bare_defi_callers_2026_07_27",
    )
    assert entry.repo == "r"
    assert entry.line == 10
    assert entry.function == "load"
    assert entry.status == "pending_triage"
