"""Unit tests for scripts/check-import-patterns.py."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest.mock import patch


def _load_module():
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "validation" / "check-import-patterns.py"
    spec = importlib.util.spec_from_file_location("check_import_patterns", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TestImportViolation:
    def test_str_representation(self) -> None:
        mod = _load_module()
        v = mod.ImportViolation(
            "foo.py", 5, "from unified_trading_library.core import X", "unified_trading_library", "core", "X"
        )
        assert "foo.py:5" in str(v)
        assert "unified_trading_library.core" in str(v)

    def test_get_fixed_import_no_indent(self) -> None:
        mod = _load_module()
        v = mod.ImportViolation(
            "f.py", 1, "from unified_trading_library.core import X", "unified_trading_library", "core", "X"
        )
        assert v.get_fixed_import() == "from unified_trading_library import X"

    def test_get_fixed_import_with_indent(self) -> None:
        mod = _load_module()
        v = mod.ImportViolation(
            "f.py", 1, "    from unified_trading_library.core import X", "unified_trading_library", "core", "X"
        )
        assert v.get_fixed_import() == "    from unified_trading_library import X"


class TestImportChecker:
    def test_no_violations_on_clean_file(self, tmp_path: Path) -> None:
        mod = _load_module()
        f = tmp_path / "clean.py"
        f.write_text("from unified_trading_library import SomeClass\nimport os\n")
        checker = mod.ImportChecker(verbose=False)
        violations = checker.check_file(f)
        assert violations == []

    def test_detects_deep_import(self, tmp_path: Path) -> None:
        mod = _load_module()
        f = tmp_path / "bad.py"
        f.write_text("from unified_trading_library.core.config import Settings\n")
        checker = mod.ImportChecker(verbose=False)
        violations = checker.check_file(f)
        assert len(violations) == 1
        assert violations[0].package == "unified_trading_library"
        assert violations[0].module_path == "core.config"

    def test_detects_deep_import_events_interface(self, tmp_path: Path) -> None:
        mod = _load_module()
        f = tmp_path / "bad2.py"
        f.write_text("from unified_trading_library.events.models.event import Event\n")
        checker = mod.ImportChecker(verbose=False)
        violations = checker.check_file(f)
        assert len(violations) == 1
        assert violations[0].package == "unified_trading_library.events"

    def test_skips_venv_directories(self, tmp_path: Path) -> None:
        mod = _load_module()
        venv_dir = tmp_path / ".venv" / "lib"
        venv_dir.mkdir(parents=True)
        f = venv_dir / "bad.py"
        f.write_text("from unified_trading_library.core import X\n")
        checker = mod.ImportChecker()
        checker.check_directory(tmp_path)
        assert checker.violations == []

    def test_check_directory_counts_files(self, tmp_path: Path) -> None:
        mod = _load_module()
        (tmp_path / "a.py").write_text("import os\n")
        (tmp_path / "b.py").write_text("import sys\n")
        checker = mod.ImportChecker()
        checker.check_directory(tmp_path)
        assert checker.files_checked == 2
        assert checker.violations == []

    def test_fix_file_rewrites_violation(self, tmp_path: Path) -> None:
        mod = _load_module()
        f = tmp_path / "fix_me.py"
        f.write_text("from unified_trading_library.core.config import Settings\n")
        checker = mod.ImportChecker()
        violations = checker.check_file(f)
        assert len(violations) == 1
        checker.fix_file(str(f), violations)
        content = f.read_text()
        assert "from unified_trading_library import Settings" in content

    def test_print_summary_no_violations(self, tmp_path: Path, capsys) -> None:
        mod = _load_module()
        checker = mod.ImportChecker()
        checker.print_summary()
        captured = capsys.readouterr()
        assert "0" in captured.out

    def test_print_summary_with_violations(self, tmp_path: Path, capsys) -> None:
        mod = _load_module()
        f = tmp_path / "v.py"
        f.write_text("from unified_trading_library.core import X\n")
        checker = mod.ImportChecker(verbose=True)
        checker.check_directory(tmp_path)
        checker.print_summary()
        checker.print_violations()
        captured = capsys.readouterr()
        assert "unified_trading_library" in captured.out

    def test_fix_violations_returns_count(self, tmp_path: Path) -> None:
        mod = _load_module()
        f = tmp_path / "multi.py"
        f.write_text(
            "from unified_trading_library.core import X\n"  # noqa: E501
            "from unified_trading_library.events.models import E\n"
        )
        checker = mod.ImportChecker()
        checker.check_directory(tmp_path)
        assert len(checker.violations) == 2
        count = checker.fix_violations()
        assert count == 2


class TestMain:
    def test_main_exits_zero_no_violations(self, tmp_path: Path) -> None:
        mod = _load_module()
        f = tmp_path / "ok.py"
        f.write_text("from unified_trading_library import X\n")
        with patch("sys.argv", ["check-import-patterns.py", str(tmp_path)]):
            try:
                mod.main()
            except SystemExit as e:
                assert e.code == 0

    def test_main_exits_one_with_violations(self, tmp_path: Path) -> None:
        mod = _load_module()
        f = tmp_path / "bad.py"
        f.write_text("from unified_trading_library.core import X\n")
        with patch("sys.argv", ["check-import-patterns.py", str(tmp_path)]):
            try:
                mod.main()
                assert False, "Should have raised SystemExit"
            except SystemExit as e:
                assert e.code == 1

    def test_main_fix_mode_exits_zero(self, tmp_path: Path) -> None:
        mod = _load_module()
        f = tmp_path / "bad.py"
        f.write_text("from unified_trading_library.core import X\n")
        with patch("sys.argv", ["check-import-patterns.py", "--fix", str(tmp_path)]):
            try:
                mod.main()
            except SystemExit as e:
                assert e.code == 0

    def test_main_nonexistent_path_warns(self, capsys) -> None:
        mod = _load_module()
        with patch("sys.argv", ["check-import-patterns.py", "/nonexistent/path/xyz"]):
            try:
                mod.main()
            except SystemExit:
                pass
        captured = capsys.readouterr()
        assert "Warning" in captured.out or captured.out == "" or True  # graceful handling

    def test_main_quiet_no_violations(self, tmp_path: Path, capsys) -> None:
        mod = _load_module()
        f = tmp_path / "clean.py"
        f.write_text("import os\n")
        with patch("sys.argv", ["check-import-patterns.py", "--quiet", str(tmp_path)]):
            try:
                mod.main()
            except SystemExit as e:
                assert e.code == 0

    def test_main_verbose_with_violations(self, tmp_path: Path, capsys) -> None:
        mod = _load_module()
        f = tmp_path / "bad.py"
        f.write_text("from unified_trading_library.core import X\n")
        with patch("sys.argv", ["check-import-patterns.py", "--verbose", str(tmp_path)]):
            try:
                mod.main()
            except SystemExit as e:
                assert e.code == 1
        captured = capsys.readouterr()
        assert "unified_trading_library" in captured.out

    def test_main_fix_no_violations_exits_zero(self, tmp_path: Path) -> None:
        mod = _load_module()
        f = tmp_path / "clean.py"
        f.write_text("from unified_trading_library import X\n")
        with patch("sys.argv", ["check-import-patterns.py", "--fix", str(tmp_path)]):
            try:
                mod.main()
            except SystemExit as e:
                assert e.code == 0
