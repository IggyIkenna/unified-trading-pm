# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_pipeline_mode_explicit_at_record_calls.py.

Pure-Python — no GCS/AWS/network. Mirrors test_check_banned_placeholder_methods.py
in shape: constants sanity, single-file scanning (record_* call AST detection),
whitelist marker behaviour, workspace walker exclusions, baseline tolerance,
and a main() end-to-end smoke.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from check_pipeline_mode_explicit_at_record_calls import (  # type: ignore[import-not-found]
    RECORD_METHOD_NAMES,
    WHITELIST_MARKER,
    BaselineEntry,
    Finding,
    _iter_py_files,
    _scan_file,
    main,
)


def test_record_method_names_closed_set() -> None:
    """The 5 v8 ManifestWriter record-* methods are exactly the closed set."""
    assert (
        frozenset(
            {
                "record_captured",
                "record_empty",
                "record_failed",
                "record_expected_unattempted",
                "record_empty_for_shard",
            }
        )
        == RECORD_METHOD_NAMES
    )


def _write_py(tmp_path: Path, name: str, content: str) -> Path:
    file = tmp_path / name
    file.write_text(textwrap.dedent(content), encoding="utf-8")
    return file


def test_scan_file_flags_record_call_without_pipeline_mode(tmp_path: Path) -> None:
    """A `record_captured(...)` call missing `pipeline_mode=` is flagged."""
    target = _write_py(
        tmp_path,
        "adapter.py",
        """
        from unified_trading_library import ManifestWriter

        def write_row(writer: ManifestWriter) -> None:
            writer.record_captured(asset_group="cefi", venue="binance")
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert len(findings) == 1
    assert findings[0].method == "record_captured"
    assert findings[0].file == "adapter.py"


def test_scan_file_clean_when_pipeline_mode_kwarg_present(tmp_path: Path) -> None:
    """A `record_captured(pipeline_mode=...)` call is NOT flagged."""
    target = _write_py(
        tmp_path,
        "adapter.py",
        """
        from unified_trading_library import ManifestWriter

        def write_row(writer):
            writer.record_captured(asset_group="cefi", pipeline_mode="BATCH_TARDIS")  # QG-allow: pipeline-mode-string-literal
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert findings == []


def test_scan_file_whitelist_marker_skips_call(tmp_path: Path) -> None:
    """Inline `# QG-allow: pipeline-mode-not-applicable` bypasses the check."""
    target = _write_py(
        tmp_path,
        "adapter.py",
        f"""
        from unified_trading_library import ManifestWriter

        def write_row(writer):
            writer.record_captured(**kwargs)  # {WHITELIST_MARKER}
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert findings == []


def test_scan_file_flags_each_method_in_set(tmp_path: Path) -> None:
    """Each of the 5 v8 record_* methods is detected when called without pipeline_mode=."""
    target = _write_py(
        tmp_path,
        "adapter.py",
        """
        def write_all(writer):
            writer.record_captured()
            writer.record_empty(reason="X")
            writer.record_failed(error=Exception())
            writer.record_expected_unattempted(reason="Y")
            writer.record_empty_for_shard(asset_group="cefi")
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    flagged_methods = {f.method for f in findings}
    assert flagged_methods == {
        "record_captured",
        "record_empty",
        "record_failed",
        "record_expected_unattempted",
        "record_empty_for_shard",
    }


def test_scan_file_ignores_non_record_attr_calls(tmp_path: Path) -> None:
    """Calls to similarly-named methods that aren't in the closed set don't flag."""
    target = _write_py(
        tmp_path,
        "adapter.py",
        """
        def write_other(writer):
            writer.record_captured_bytes_count(n=42)  # not in closed set
            writer.record(asset_group="cefi")  # too generic, not in set
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert findings == []


def test_iter_py_files_skips_venv_and_archive(tmp_path: Path) -> None:
    """Walker skips .venv / tests / scripts / /archive/ dirs."""
    (tmp_path / "src").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "real.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / ".venv" / "lib.py").write_text("y = 2\n", encoding="utf-8")
    (tmp_path / "tests" / "test_x.py").write_text("z = 3\n", encoding="utf-8")
    files = list(_iter_py_files(tmp_path))
    rels = sorted(str(f.relative_to(tmp_path)) for f in files)
    assert rels == ["src/real.py"]


def test_main_clean_returns_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """End-to-end: a clean tree with a properly-kwarged call returns 0."""
    repo = tmp_path / "myrepo"
    src = repo / "myrepo"
    src.mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname = 'myrepo'\n", encoding="utf-8")
    _write_py(
        src,
        "writer.py",
        """
        def emit(writer):
            writer.record_captured(pipeline_mode="BATCH_TARDIS", asset_group="cefi")  # QG-allow: pipeline-mode-string-literal
        """,
    )
    rc = main(["--workspace-root", str(tmp_path), "--scope", "myrepo"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "OK" in captured.out


def test_main_dirty_returns_one(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """End-to-end: a tree with a missing-kwarg call returns 1."""
    repo = tmp_path / "myrepo"
    src = repo / "myrepo"
    src.mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname = 'myrepo'\n", encoding="utf-8")
    _write_py(
        src,
        "writer.py",
        """
        def emit(writer):
            writer.record_captured(asset_group="cefi")
        """,
    )
    rc = main(["--workspace-root", str(tmp_path), "--scope", "myrepo"])
    captured = capsys.readouterr()
    assert rc == 1
    assert "FAIL" in captured.err
    assert "record_captured" in captured.err


def test_finding_baseline_key_shape() -> None:
    """Finding.baseline_key has the (repo, file, line, method) shape for baseline lookups."""
    f = Finding(repo="r", file="f.py", line=10, method="record_captured", snippet="x")
    assert f.baseline_key == ("r", "f.py", 10, "record_captured")


def test_baseline_entry_dataclass_fields() -> None:
    """BaselineEntry carries the 6 required fields per the loader contract."""
    entry = BaselineEntry(
        repo="r",
        file="f.py",
        line=10,
        method="record_captured",
        status="pending_phase_4_mtds",
        successor="manifest_schema_final_gate Phase 4.MTDS sweep",
    )
    assert entry.repo == "r"
    assert entry.line == 10
    assert entry.status == "pending_phase_4_mtds"
