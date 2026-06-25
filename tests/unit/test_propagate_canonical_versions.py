"""Unit tests for scripts/propagation/propagate-canonical-versions.py.

Regression guard for the ceiling-first spec parse bug: `_replace_dep_spec` must split
the package name on the EARLIEST operator position across all operators, not the first
operator scanned — else a ceiling-first spec ("fastapi<1.0.0,>=0.115.0") was silently
returned unchanged instead of being propagated to the canonical constraint.
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "propagation" / "propagate-canonical-versions.py"
    spec = importlib.util.spec_from_file_location("propagate_canonical_versions", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()

# Canonical constraint keys are normalized at load time (load_constraints), so a plain
# lowercase name is the realistic shape of the dict passed to _replace_dep_spec.
CONSTRAINTS = {"fastapi": "fastapi>=0.115.0,<1.0.0"}


class TestReplaceDepSpec:
    def test_ceiling_first_spec_is_replaced(self) -> None:
        """THE bug: a ceiling-first spec must still be recognised and replaced."""
        line = '    "fastapi<1.0.0,>=0.115.0",\n'
        out = MOD._replace_dep_spec(line, CONSTRAINTS)
        assert out == '    "fastapi>=0.115.0,<1.0.0",\n'

    def test_floor_first_spec_is_replaced(self) -> None:
        """Normal floor-first spec still propagates (no regression)."""
        line = '    "fastapi>=0.100.0,<1.0.0",\n'
        out = MOD._replace_dep_spec(line, CONSTRAINTS)
        assert out == '    "fastapi>=0.115.0,<1.0.0",\n'

    def test_exact_pin_spec_is_replaced(self) -> None:
        line = '    "fastapi==0.110.0",\n'
        out = MOD._replace_dep_spec(line, CONSTRAINTS)
        assert out == '    "fastapi>=0.115.0,<1.0.0",\n'

    def test_unconstrained_package_unchanged(self) -> None:
        line = '    "uvicorn>=0.30.0",\n'
        assert MOD._replace_dep_spec(line, CONSTRAINTS) == line

    def test_unconstrained_ceiling_first_unchanged(self) -> None:
        """Ceiling-first parsing must not accidentally MATCH an unconstrained package."""
        line = '    "uvicorn<1.0.0,>=0.30.0",\n'
        assert MOD._replace_dep_spec(line, CONSTRAINTS) == line

    def test_non_spec_line_unchanged(self) -> None:
        assert MOD._replace_dep_spec("dependencies = [\n", CONSTRAINTS) == "dependencies = [\n"

    def test_name_only_no_operator_unchanged(self) -> None:
        line = '    "fastapi",\n'
        assert MOD._replace_dep_spec(line, CONSTRAINTS) == line


class TestUpdatePyprojectContent:
    def test_block_with_ceiling_first_member(self) -> None:
        content = 'dependencies = [\n    "uvicorn>=0.30.0",\n    "fastapi<1.0.0,>=0.115.0",\n]\n'
        out = MOD.update_pyproject_content(content, CONSTRAINTS)
        assert '"fastapi>=0.115.0,<1.0.0"' in out
        assert '"uvicorn>=0.30.0"' in out
