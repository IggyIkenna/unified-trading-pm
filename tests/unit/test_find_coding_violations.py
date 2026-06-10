"""Unit tests for scripts/validation/find-coding-violations.py."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "validation" / "find-coding-violations.py"
    spec = importlib.util.spec_from_file_location("find_coding_violations", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# ── Tests: CheckResult dataclass ────────────────────────────────────────


class TestCheckResult:
    def test_creation(self) -> None:
        cr = MOD.CheckResult(name="test", count=5, hits=[("f.py", 1, "content")])
        assert cr.name == "test"
        assert cr.count == 5
        assert len(cr.hits) == 1


# ── Tests: ViolationChecker base ────────────────────────────────────────


class TestViolationChecker:
    def test_get_exclude_globs(self, tmp_path: Path) -> None:
        checker = MOD.ViolationChecker(tmp_path)
        globs = checker.get_exclude_globs()
        assert isinstance(globs, list)
        assert len(globs) > 0
        # Should include directory exclusions
        assert any(".venv" in g for g in globs)
        # Should include file exclusions
        assert any("conftest" in g for g in globs)

    def test_should_exclude_line_base(self, tmp_path: Path) -> None:
        checker = MOD.ViolationChecker(tmp_path)
        assert checker.should_exclude_line("any content") is False


# ── Tests: PrintChecker ─────────────────────────────────────────────────


class TestPrintChecker:
    def test_excludes_console_print(self, tmp_path: Path) -> None:
        checker = MOD.PrintChecker(tmp_path)
        assert checker.should_exclude_line("    console.print(result)") is True

    def test_excludes_method_print(self, tmp_path: Path) -> None:
        checker = MOD.PrintChecker(tmp_path)
        assert checker.should_exclude_line("    obj.print('hello')") is True

    def test_excludes_doctest(self, tmp_path: Path) -> None:
        checker = MOD.PrintChecker(tmp_path)
        assert checker.should_exclude_line('    >>> print("example")') is True

    def test_excludes_string_literal(self, tmp_path: Path) -> None:
        checker = MOD.PrintChecker(tmp_path)
        assert checker.should_exclude_line('"print(something)"') is True
        assert checker.should_exclude_line("'print(something)'") is True

    def test_excludes_python_c(self, tmp_path: Path) -> None:
        checker = MOD.PrintChecker(tmp_path)
        assert checker.should_exclude_line('    python3 -c "print(1)"') is True

    def test_does_not_exclude_plain_print(self, tmp_path: Path) -> None:
        checker = MOD.PrintChecker(tmp_path)
        assert checker.should_exclude_line("    print(result)") is False


# ── Tests: OsGetenvChecker ──────────────────────────────────────────────


class TestOsGetenvChecker:
    def test_check_returns_result(self, tmp_path: Path) -> None:
        # This checker calls ripgrep, which may not find anything in tmp_path
        checker = MOD.OsGetenvChecker(tmp_path)
        result = checker.check()
        assert result.name == "os.getenv() usage"
        assert isinstance(result.count, int)


# ── Tests: NaiveDatetimeChecker ──────────────────────────────────────────


class TestNaiveDatetimeChecker:
    def test_excludes_comment(self, tmp_path: Path) -> None:
        checker = MOD.NaiveDatetimeChecker(tmp_path)
        assert checker.should_exclude_line("    # datetime.now() is bad") is True

    def test_does_not_exclude_actual_usage(self, tmp_path: Path) -> None:
        checker = MOD.NaiveDatetimeChecker(tmp_path)
        assert checker.should_exclude_line("    datetime.now()") is False


# ── Tests: BareExceptChecker ─────────────────────────────────────────────


class TestBareExceptChecker:
    def test_excludes_typed_except(self, tmp_path: Path) -> None:
        checker = MOD.BareExceptChecker(tmp_path)
        assert checker.should_exclude_line("    except ValueError:") is True

    def test_excludes_comment(self, tmp_path: Path) -> None:
        checker = MOD.BareExceptChecker(tmp_path)
        assert checker.should_exclude_line("    # except:") is True

    def test_does_not_exclude_bare_except(self, tmp_path: Path) -> None:
        checker = MOD.BareExceptChecker(tmp_path)
        assert checker.should_exclude_line("    except:") is False


# ── Tests: HardcodedPathChecker ──────────────────────────────────────────


class TestHardcodedPathChecker:
    def test_excludes_comment(self, tmp_path: Path) -> None:
        checker = MOD.HardcodedPathChecker(tmp_path)
        assert checker.should_exclude_line('    # "/path/to/file"') is True

    def test_excludes_import(self, tmp_path: Path) -> None:
        checker = MOD.HardcodedPathChecker(tmp_path)
        assert checker.should_exclude_line("    from x.y.z import something") is True

    def test_excludes_url(self, tmp_path: Path) -> None:
        checker = MOD.HardcodedPathChecker(tmp_path)
        assert checker.should_exclude_line('    url = "https://example.com/path"') is True

    def test_excludes_api_endpoint(self, tmp_path: Path) -> None:
        checker = MOD.HardcodedPathChecker(tmp_path)
        assert checker.should_exclude_line('    endpoint = "/v1/trades"') is True

    def test_does_not_exclude_hardcoded_path(self, tmp_path: Path) -> None:
        checker = MOD.HardcodedPathChecker(tmp_path)
        assert checker.should_exclude_line('    config = "/etc/myapp/config.yaml"') is False


# ── Tests: ALL_CHECKERS registry ────────────────────────────────────────


class TestCheckerRegistry:
    def test_all_checkers_registered(self) -> None:
        expected = {"print", "getenv", "imports", "datetime", "except", "paths"}
        assert set(MOD.ALL_CHECKERS.keys()) == expected

    def test_all_checkers_instantiable(self, tmp_path: Path) -> None:
        for name, cls in MOD.ALL_CHECKERS.items():
            checker = cls(tmp_path)
            assert hasattr(checker, "check"), f"{name} checker missing check method"
            assert hasattr(checker, "repo_path"), f"{name} checker missing repo_path"


# ── Tests: scan_single_repo ─────────────────────────────────────────────


class TestScanSingleRepo:
    def test_scan_empty_dir(self, tmp_path: Path) -> None:
        results = MOD.scan_single_repo(tmp_path)
        assert isinstance(results, dict)
        assert len(results) == len(MOD.ALL_CHECKERS)

    def test_scan_with_specific_checks(self, tmp_path: Path) -> None:
        results = MOD.scan_single_repo(tmp_path, ["print", "getenv"])
        assert len(results) == 2
        assert "print" in results
        assert "getenv" in results

    def test_scan_unknown_check(self, tmp_path: Path) -> None:
        results = MOD.scan_single_repo(tmp_path, ["nonexistent"])
        assert len(results) == 0


# ── Tests: IndentedImportChecker ─────────────────────────────────────────


class TestIndentedImportChecker:
    def test_excludes_type_checking_in_line(self, tmp_path: Path) -> None:
        checker = MOD.IndentedImportChecker(tmp_path)
        assert checker.should_exclude_line("    if TYPE_CHECKING:") is True

    def test_excludes_type_checking_import(self, tmp_path: Path) -> None:
        checker = MOD.IndentedImportChecker(tmp_path)
        assert checker.should_exclude_line("    from typing import TYPE_CHECKING") is True

    def test_excludes_commented_import(self, tmp_path: Path) -> None:
        checker = MOD.IndentedImportChecker(tmp_path)
        assert checker.should_exclude_line("    # from x import y") is True

    def test_excludes_doctest_triple_gt(self, tmp_path: Path) -> None:
        checker = MOD.IndentedImportChecker(tmp_path)
        assert checker.should_exclude_line("    >>> from x import y") is True

    def test_excludes_doctest_ellipsis(self, tmp_path: Path) -> None:
        checker = MOD.IndentedImportChecker(tmp_path)
        assert checker.should_exclude_line("    ... import something") is True

    def test_excludes_get_schema_usage_example(self, tmp_path: Path) -> None:
        checker = MOD.IndentedImportChecker(tmp_path)
        assert checker.should_exclude_line("    get_schema_for_output_type: from x import y") is True

    def test_plain_indented_import_not_excluded(self, tmp_path: Path) -> None:
        # A real indented import NOT in the exclusions JSON → should NOT be excluded
        checker = MOD.IndentedImportChecker(tmp_path)
        assert checker.should_exclude_line("    from os import path") is False


# ── Tests: ViolationChecker.check not implemented ─────────────────────────


class TestViolationCheckerCheckNotImplemented:
    def test_check_raises_not_implemented(self, tmp_path: Path) -> None:
        checker = MOD.ViolationChecker(tmp_path)
        with pytest.raises(NotImplementedError):
            checker.check()


# ── Tests: run_ripgrep error paths and result parsing ─────────────────────


class TestRunRipgrepErrorPaths:
    def test_timeout_returns_empty(self, tmp_path: Path) -> None:
        checker = MOD.ViolationChecker(tmp_path)
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("rg", 60)):
            result = checker.run_ripgrep("pattern")
        assert result == []

    def test_rg_not_found_returns_empty(self, tmp_path: Path, capsys) -> None:
        checker = MOD.ViolationChecker(tmp_path)
        with patch("subprocess.run", side_effect=FileNotFoundError):
            result = checker.run_ripgrep("pattern")
        assert result == []
        assert "ripgrep" in capsys.readouterr().out

    def test_parses_valid_rg_output(self, tmp_path: Path) -> None:
        checker = MOD.ViolationChecker(tmp_path)
        mock_proc = MagicMock()
        mock_proc.stdout = "file.py:5:    print(x)\nother.py:10:    print(y)\n"
        with patch("subprocess.run", return_value=mock_proc):
            result = checker.run_ripgrep("print")
        assert len(result) == 2
        assert result[0] == ("file.py", 5, "print(x)")
        assert result[1] == ("other.py", 10, "print(y)")

    def test_empty_rg_output_returns_empty(self, tmp_path: Path) -> None:
        checker = MOD.ViolationChecker(tmp_path)
        mock_proc = MagicMock()
        mock_proc.stdout = ""
        with patch("subprocess.run", return_value=mock_proc):
            result = checker.run_ripgrep("pattern")
        assert result == []

    def test_malformed_rg_line_skipped(self, tmp_path: Path) -> None:
        checker = MOD.ViolationChecker(tmp_path)
        mock_proc = MagicMock()
        mock_proc.stdout = "not-enough-colons\n"
        with patch("subprocess.run", return_value=mock_proc):
            result = checker.run_ripgrep("pattern")
        assert result == []

    def test_excluded_line_filtered(self, tmp_path: Path) -> None:
        # PrintChecker excludes .print() calls; verify filtering happens in run_ripgrep
        checker = MOD.PrintChecker(tmp_path)
        mock_proc = MagicMock()
        mock_proc.stdout = "file.py:1:    obj.print(x)\nfile.py:2:    print(y)\n"
        with patch("subprocess.run", return_value=mock_proc):
            result = checker.run_ripgrep(r"print\(")
        # Only the plain print(y) line survives
        assert len(result) == 1
        assert result[0][2] == "print(y)"


# ── Tests: HardcodedPathChecker extra exclusions ──────────────────────────


class TestHardcodedPathCheckerExtra:
    def test_excludes_dict_value_with_slash(self, tmp_path: Path) -> None:
        checker = MOD.HardcodedPathChecker(tmp_path)
        assert checker.should_exclude_line('    d = {"key": "/api/endpoint"}') is True

    def test_excludes_path_with_param(self, tmp_path: Path) -> None:
        checker = MOD.HardcodedPathChecker(tmp_path)
        # Has { and "/ → line 264 returns True
        assert checker.should_exclude_line('    url = "/{resource_id}/endpoint"') is True

    def test_plain_path_reaches_final_return(self, tmp_path: Path) -> None:
        checker = MOD.HardcodedPathChecker(tmp_path)
        # /etc path: no {, not /v or /api, not a dict value — reaches the final return
        assert checker.should_exclude_line('    cfg = "/etc/myapp.conf"') is False


# ── Tests: print_results ──────────────────────────────────────────────────


class TestPrintResults:
    def test_clean_repo_prints_clean(self, tmp_path: Path, capsys) -> None:
        results = {"print": MOD.CheckResult(name="print() statements", count=0, hits=[])}
        MOD.print_results("myrepo", tmp_path, results)
        assert "CLEAN" in capsys.readouterr().out

    def test_violations_prints_count(self, tmp_path: Path, capsys) -> None:
        hits = [(str(tmp_path / "foo.py"), 10, "print(result)")]
        results = {"print": MOD.CheckResult(name="print() statements", count=1, hits=hits)}
        MOD.print_results("myrepo", tmp_path, results)
        out = capsys.readouterr().out
        assert "1 violations" in out
        assert "print() statements" in out

    def test_verbose_shows_line_number(self, tmp_path: Path, capsys) -> None:
        hits = [(str(tmp_path / "foo.py"), 10, "print(result)")]
        results = {"print": MOD.CheckResult(name="print() statements", count=1, hits=hits)}
        MOD.print_results("myrepo", tmp_path, results, verbose=True)
        assert "L10" in capsys.readouterr().out

    def test_full_report_shows_all_files(self, tmp_path: Path, capsys) -> None:
        hits = [(str(tmp_path / f"f{i}.py"), i, f"c{i}") for i in range(10)]
        results = {"print": MOD.CheckResult(name="print() statements", count=10, hits=hits)}
        MOD.print_results("myrepo", tmp_path, results, full_report=True)
        out = capsys.readouterr().out
        assert "10 found" in out

    def test_truncation_with_many_files(self, tmp_path: Path, capsys) -> None:
        # 7 different files → verbose shows first 5, then "... and 2 more files"
        hits = [(str(tmp_path / f"f{i}.py"), 1, "print(x)") for i in range(7)]
        results = {"print": MOD.CheckResult(name="print() statements", count=7, hits=hits)}
        MOD.print_results("myrepo", tmp_path, results, verbose=True)
        out = capsys.readouterr().out
        assert "more files" in out

    def test_path_outside_repo_uses_raw_path(self, tmp_path: Path, capsys) -> None:
        # filepath not relative to repo_path → uses raw path (ValueError caught)
        other = tmp_path / "other_place" / "foo.py"
        base = tmp_path / "myrepo"
        base.mkdir()
        hits = [(str(other), 5, "print(x)")]
        results = {"print": MOD.CheckResult(name="print() statements", count=1, hits=hits)}
        MOD.print_results("myrepo", base, results, verbose=True)
        assert "foo.py" in capsys.readouterr().out

    def test_multiple_check_types_shown(self, tmp_path: Path, capsys) -> None:
        hits = [(str(tmp_path / "f.py"), 1, "print(x)")]
        results = {
            "print": MOD.CheckResult(name="print() statements", count=1, hits=hits),
            "getenv": MOD.CheckResult(name="os.getenv() usage", count=0, hits=[]),
        }
        MOD.print_results("myrepo", tmp_path, results)
        out = capsys.readouterr().out
        assert "os.getenv() usage" in out
        assert "CLEAN" in out


# ── Tests: main() ─────────────────────────────────────────────────────────


def _empty_rg() -> MagicMock:
    """Mock subprocess.run returning empty ripgrep output (no violations)."""
    m = MagicMock()
    m.stdout = ""
    return m


class TestMain:
    def test_folder_not_found_returns_1(self, tmp_path: Path, capsys) -> None:
        sys.argv = ["prog", "--folder", str(tmp_path / "nonexistent")]
        result = MOD.main()
        assert result == 1
        assert "not found" in capsys.readouterr().out

    def test_folder_exists_runs_and_returns_0(self, tmp_path: Path, capsys) -> None:
        with patch("subprocess.run", return_value=_empty_rg()):
            sys.argv = ["prog", "--folder", str(tmp_path)]
            result = MOD.main()
        assert result == 0
        out = capsys.readouterr().out
        assert "CODING STANDARDS" in out

    def test_repo_not_found_returns_1(self, tmp_path: Path, capsys) -> None:
        with patch.object(MOD, "WORKSPACE_ROOT", tmp_path):
            sys.argv = ["prog", "--repo", "nonexistent-repo"]
            result = MOD.main()
        assert result == 1
        assert "not found" in capsys.readouterr().out

    def test_repo_found_scans_and_returns_0(self, tmp_path: Path, capsys) -> None:
        repo = tmp_path / "my-repo"
        repo.mkdir()
        with patch.object(MOD, "WORKSPACE_ROOT", tmp_path), patch("subprocess.run", return_value=_empty_rg()):
            sys.argv = ["prog", "--repo", "my-repo"]
            result = MOD.main()
        assert result == 0

    def test_specific_check_flag(self, tmp_path: Path, capsys) -> None:
        with patch("subprocess.run", return_value=_empty_rg()):
            sys.argv = ["prog", "--folder", str(tmp_path), "--check", "print"]
            result = MOD.main()
        out = capsys.readouterr().out
        assert result == 0
        assert "print" in out.lower()
        # Only print check ran — getenv should not appear in summary
        assert "os.getenv" not in out

    def test_output_file_written(self, tmp_path: Path, capsys) -> None:
        out_file = tmp_path / "report.md"
        with patch("subprocess.run", return_value=_empty_rg()):
            sys.argv = ["prog", "--folder", str(tmp_path), "--output", str(out_file)]
            result = MOD.main()
        assert result == 0
        assert out_file.exists()
        content = out_file.read_text()
        assert "Coding Standards" in content

    def test_default_repos_missing_scans_zero(self, tmp_path: Path, capsys) -> None:
        # WORKSPACE_ROOT points to tmp_path → no default repos exist → 0 repos scanned
        with patch.object(MOD, "WORKSPACE_ROOT", tmp_path):
            sys.argv = ["prog"]
            result = MOD.main()
        assert result == 0
        out = capsys.readouterr().out
        assert "Scanning: 0 repos" in out

    def test_verbose_flag_does_not_crash(self, tmp_path: Path, capsys) -> None:
        with patch("subprocess.run", return_value=_empty_rg()):
            sys.argv = ["prog", "--folder", str(tmp_path), "--verbose"]
            result = MOD.main()
        assert result == 0

    def test_report_flag_implies_full_report(self, tmp_path: Path, capsys) -> None:
        with patch("subprocess.run", return_value=_empty_rg()):
            sys.argv = ["prog", "--folder", str(tmp_path), "--report"]
            result = MOD.main()
        assert result == 0

    def test_output_file_with_violations(self, tmp_path: Path, capsys) -> None:
        out_file = tmp_path / "violations.md"
        # Fake a violation in run_ripgrep output
        fake_rg = MagicMock()
        fake_rg.stdout = f"{tmp_path}/foo.py:1:    print(x)\n"
        with patch("subprocess.run", return_value=fake_rg):
            sys.argv = ["prog", "--folder", str(tmp_path), "--output", str(out_file), "--check", "print"]
            result = MOD.main()
        assert result == 0
        content = out_file.read_text()
        assert "print() statements" in content
