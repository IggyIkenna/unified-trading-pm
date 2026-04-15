"""Unit tests for scripts/validation/find-coding-violations.py."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


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
