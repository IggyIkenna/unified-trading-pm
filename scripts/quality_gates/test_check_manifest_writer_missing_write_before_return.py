# Epic: sports_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_manifest_writer_missing_write_before_return.py.

Pure-Python — no GCS/AWS/network. Mirrors
test_check_pipeline_mode_explicit_at_record_calls.py in shape: constants
sanity, single-file scanning, the "other exit path DOES write" gate,
whitelist marker behaviour, workspace walker exclusions, baseline
tolerance, and a main() end-to-end smoke.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from check_manifest_writer_missing_write_before_return import (  # type: ignore[import-not-found]
    RECORD_METHOD_NAMES,
    WHITELIST_MARKER,
    WRITE_METHOD_NAMES,
    BaselineEntry,
    Finding,
    _iter_py_files,
    _scan_file,
    main,
)


def test_record_method_names_closed_set() -> None:
    assert (
        frozenset(
            {
                "record_captured",
                "record_captured_from_counts",
                "record_empty",
                "record_expected_empty",
                "record_expected_unattempted",
                "record_failed",
                "record_zero_rows",
            }
        )
        == RECORD_METHOD_NAMES
    )


def test_write_method_names_closed_set() -> None:
    assert frozenset({"write", "flush"}) == WRITE_METHOD_NAMES


def _write_py(tmp_path: Path, name: str, content: str) -> Path:
    file = tmp_path / name
    file.write_text(textwrap.dedent(content), encoding="utf-8")
    return file


def test_flags_early_return_missing_write_when_sibling_path_writes(tmp_path: Path) -> None:
    """The exact real-world bug shape: guard block records + returns with no
    .write(), while a sibling exit path in the same function DOES write."""
    target = _write_py(
        tmp_path,
        "weather.py",
        """
        async def _fetch_weather_data(date, bucket):
            manifest = ManifestWriter(service_name="x", catalogue_bucket=bucket)
            if guard:
                for lid in leagues:
                    manifest.record_expected_empty(row_key={}, reason="X")
                return counts
            manifest.write()
            return counts
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert len(findings) == 1
    assert findings[0].function == "_fetch_weather_data"
    assert findings[0].var == "manifest"


def test_clean_when_write_precedes_return_in_same_block(tmp_path: Path) -> None:
    """A record_*() call immediately followed by .write() before return is clean."""
    target = _write_py(
        tmp_path,
        "clean.py",
        """
        def emit(bucket):
            manifest = ManifestWriter(service_name="x", catalogue_bucket=bucket)
            manifest.record_captured(row_key={})
            manifest.write()
            return {}
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert findings == []


def test_not_flagged_when_no_other_exit_path_ever_writes(tmp_path: Path) -> None:
    """A function where NO exit path ever calls .write() is not flagged — the
    'other paths DO write' gate requires a sibling clean path to exist."""
    target = _write_py(
        tmp_path,
        "helper.py",
        """
        def build_payload(bucket):
            manifest = ManifestWriter(service_name="x", catalogue_bucket=bucket)
            manifest.record_empty(row_key={}, reason="Z")
            return {}
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert findings == []


def test_whitelist_marker_on_return_line_skips_finding(tmp_path: Path) -> None:
    target = _write_py(
        tmp_path,
        "weather.py",
        f"""
        async def _fetch_weather_data(date, bucket):
            manifest = ManifestWriter(service_name="x", catalogue_bucket=bucket)
            if guard:
                manifest.record_expected_empty(row_key={{}}, reason="X")
                return counts  # {WHITELIST_MARKER}
            manifest.write()
            return counts
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert findings == []


def test_flush_also_counts_as_persisted(tmp_path: Path) -> None:
    """.flush() satisfies the same contract as .write()."""
    target = _write_py(
        tmp_path,
        "closer.py",
        """
        def close(bucket):
            manifest = ManifestWriter(service_name="x", catalogue_bucket=bucket)
            if fast_exit:
                manifest.record_captured(row_key={})
                manifest.flush()
                return {}
            manifest.record_captured(row_key={})
            manifest.write()
            return {}
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert findings == []


def test_nested_function_scopes_are_independent(tmp_path: Path) -> None:
    """A helper closure's own record/return shouldn't leak into the outer
    function's pending state, and vice versa."""
    target = _write_py(
        tmp_path,
        "nested.py",
        """
        def outer(bucket):
            manifest = ManifestWriter(service_name="x", catalogue_bucket=bucket)

            def _inner_helper():
                manifest.record_empty(row_key={}, reason="Z")
                return None

            manifest.record_captured(row_key={})
            manifest.write()
            return {}
        """,
    )
    findings = _scan_file(target, repo="testrepo", repo_root=tmp_path)
    assert findings == []


def test_iter_py_files_skips_venv_and_archive(tmp_path: Path) -> None:
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
    repo = tmp_path / "myrepo"
    src = repo / "myrepo"
    src.mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\nname = 'myrepo'\n", encoding="utf-8")
    _write_py(
        src,
        "writer.py",
        """
        def emit(manifest):
            manifest.record_captured(row_key={})
            manifest.write()
            return {}
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
        "writer.py",
        """
        def emit(bucket):
            manifest = ManifestWriter(service_name="x", catalogue_bucket=bucket)
            if guard:
                manifest.record_captured(row_key={})
                return {}
            manifest.record_captured(row_key={})
            manifest.write()
            return {}
        """,
    )
    rc = main(["--workspace-root", str(tmp_path), "--scope", "myrepo"])
    captured = capsys.readouterr()
    assert rc == 1
    assert "FAIL" in captured.err
    assert "manifest.record_*" in captured.err


def test_finding_baseline_key_shape() -> None:
    f = Finding(repo="r", file="f.py", line=10, function="_fetch_x", var="manifest", snippet="return counts")
    assert f.baseline_key == ("r", "f.py", 10, "_fetch_x")


def test_baseline_entry_dataclass_fields() -> None:
    entry = BaselineEntry(
        repo="r",
        file="f.py",
        line=10,
        function="_fetch_x",
        status="pending_p2_audit",
        successor="manifest_early_return_missing_write_loss_2026_07_09",
    )
    assert entry.repo == "r"
    assert entry.line == 10
    assert entry.function == "_fetch_x"
