"""Unit tests for scripts/validation/check-circular-imports.py."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path

import pytest


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "validation" / "check-circular-imports.py"
    spec = importlib.util.spec_from_file_location("check_circular_imports", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# ── Tests: get_package_imports ─────────────────────────────────────────────


class TestGetPackageImports:
    def test_simple_import(self, tmp_path: Path) -> None:
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "a.py").write_text("from mypkg.b import something\n")
        (pkg / "b.py").write_text("import os\n")
        graph = MOD.get_package_imports(pkg)
        assert "mypkg.a" in graph
        assert "mypkg.b" in graph["mypkg.a"]

    def test_no_internal_imports(self, tmp_path: Path) -> None:
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "a.py").write_text("import os\nimport sys\n")
        graph = MOD.get_package_imports(pkg)
        assert "mypkg.a" not in graph or len(graph["mypkg.a"]) == 0

    def test_relative_import(self, tmp_path: Path) -> None:
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        # `from . import b` resolves to the package itself (no node.module)
        (pkg / "a.py").write_text("from . import b\n")
        (pkg / "b.py").write_text("")
        graph = MOD.get_package_imports(pkg)
        assert "mypkg.a" in graph
        # `from . import b` with node.module=None resolves to base package "mypkg"
        assert "mypkg" in graph["mypkg.a"]

    def test_relative_import_with_module(self, tmp_path: Path) -> None:
        pkg = tmp_path / "mypkg"
        sub = pkg / "sub"
        sub.mkdir(parents=True)
        (pkg / "__init__.py").write_text("")
        (sub / "__init__.py").write_text("")
        # `from .sub import something` resolves to mypkg.sub
        (pkg / "a.py").write_text("from .sub import something\n")
        graph = MOD.get_package_imports(pkg)
        # node.module="sub" -> target = "mypkg.sub"
        assert "mypkg.a" in graph
        assert "mypkg.sub" in graph["mypkg.a"]

    def test_syntax_error_file_skipped(self, tmp_path: Path) -> None:
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "broken.py").write_text("def incomplete(:\n")
        # Should not raise
        graph = MOD.get_package_imports(pkg)
        assert isinstance(graph, dict)

    def test_absolute_import_same_package(self, tmp_path: Path) -> None:
        pkg = tmp_path / "mypkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "a.py").write_text("import mypkg.b\n")
        (pkg / "b.py").write_text("")
        graph = MOD.get_package_imports(pkg)
        assert "mypkg.a" in graph
        assert "mypkg.b" in graph["mypkg.a"]


# ── Tests: find_cycles ─────────────────────────────────────────────────────


class TestFindCycles:
    def test_no_cycles(self) -> None:
        graph = {"a": {"b"}, "b": {"c"}, "c": set()}
        cycles = MOD.find_cycles(graph)
        assert cycles == []

    def test_simple_cycle(self) -> None:
        graph = {"a": {"b"}, "b": {"a"}}
        cycles = MOD.find_cycles(graph)
        assert len(cycles) >= 1
        # Check the cycle contains both nodes
        cycle_nodes = set()
        for cycle in cycles:
            cycle_nodes.update(cycle)
        assert "a" in cycle_nodes
        assert "b" in cycle_nodes

    def test_self_loop(self) -> None:
        graph = {"a": {"a"}}
        cycles = MOD.find_cycles(graph)
        assert len(cycles) >= 1

    def test_three_node_cycle(self) -> None:
        graph = {"a": {"b"}, "b": {"c"}, "c": {"a"}}
        cycles = MOD.find_cycles(graph)
        assert len(cycles) >= 1

    def test_empty_graph(self) -> None:
        graph: dict[str, set[str]] = {}
        cycles = MOD.find_cycles(graph)
        assert cycles == []

    def test_disconnected_graph(self) -> None:
        graph = {"a": {"b"}, "b": set(), "c": {"d"}, "d": set()}
        cycles = MOD.find_cycles(graph)
        assert cycles == []


# ── Tests: main (integration) ─────────────────────────────────────────────


class TestMain:
    def test_clean_package(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        pkg = tmp_path / "clean_pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        (pkg / "a.py").write_text("import os\n")
        monkeypatch.setattr("sys.argv", ["check-circular-imports.py", str(pkg)])
        result = MOD.main()
        assert result == 0

    def test_no_args(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check-circular-imports.py"])
        result = MOD.main()
        assert result == 1

    def test_nonexistent_dir(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr("sys.argv", ["check-circular-imports.py", "/nonexistent/path"])
        result = MOD.main()
        assert result == 1
