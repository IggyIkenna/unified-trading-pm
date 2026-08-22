# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Tests for check_imports_inside_functions — AST-based detector.

Reference incident 2026-05-11: docstring containing
``from features_service.monitors import FeatureFreshnessChecker`` (a usage
example) was flagged as a real nested import by the prior regex-based check.
The AST-based check MUST NOT flag docstrings, comments, or string literals.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from check_imports_inside_functions import find_function_scope_imports


@pytest.fixture
def write_py(tmp_path: Path):
    """Helper to write a .py file under tmp_path and return the path."""

    def _write(name: str, source: str) -> Path:
        p = tmp_path / name
        p.write_text(source, encoding="utf-8")
        return p

    return _write


# ── POSITIVE cases (should be flagged as violations) ─────────────────────────


def test_real_nested_import_in_function_is_flagged(write_py) -> None:
    src = """
def my_func():
    from json import loads
    return loads("{}")
"""
    path = write_py("a.py", src)
    violations = find_function_scope_imports(path)
    assert len(violations) == 1
    lineno, line_text = violations[0]
    assert lineno == 3
    assert "from json import loads" in line_text


def test_real_nested_import_in_async_function_is_flagged(write_py) -> None:
    src = """
async def my_func():
    import json
    return json.dumps({})
"""
    path = write_py("a.py", src)
    violations = find_function_scope_imports(path)
    assert len(violations) == 1


def test_real_nested_import_in_method_is_flagged(write_py) -> None:
    src = """
class Foo:
    def bar(self):
        from os import path
        return path.exists("/")
"""
    path = write_py("a.py", src)
    violations = find_function_scope_imports(path)
    assert len(violations) == 1


def test_multiple_nested_imports_all_flagged(write_py) -> None:
    src = """
def func1():
    from json import loads
    return loads("{}")

def func2():
    from os import path
    return path.exists("/")
"""
    path = write_py("a.py", src)
    violations = find_function_scope_imports(path)
    assert len(violations) == 2


# ── NEGATIVE cases (must NOT be flagged) ─────────────────────────────────────


def test_top_level_import_not_flagged(write_py) -> None:
    src = """
import json
from os import path

def my_func():
    return json.dumps({})
"""
    path = write_py("a.py", src)
    assert find_function_scope_imports(path) == []


def test_docstring_with_import_example_not_flagged(write_py) -> None:
    """REGRESSION TEST for 2026-05-11 incident — docstring usage example."""
    src = '''
"""Module docstring.

Example usage:
    from features_service.monitors import FeatureFreshnessChecker

    checker = FeatureFreshnessChecker()
    checker.check()
"""

import json

def my_func():
    return json.dumps({})
'''
    path = write_py("a.py", src)
    assert find_function_scope_imports(path) == []


def test_function_docstring_with_import_example_not_flagged(write_py) -> None:
    """REGRESSION TEST — usage example INSIDE a function docstring."""
    src = '''
def my_func():
    """Compute the freshness check.

    Example usage:
        from features_service.monitors import FeatureFreshnessChecker
    """
    return True
'''
    path = write_py("a.py", src)
    assert find_function_scope_imports(path) == []


def test_class_docstring_with_import_example_not_flagged(write_py) -> None:
    src = '''
class Foo:
    """A class.

    Example:
        from foo import Bar
        bar = Bar()
    """
    pass
'''
    path = write_py("a.py", src)
    assert find_function_scope_imports(path) == []


def test_commented_out_import_inside_function_not_flagged(write_py) -> None:
    src = """
def my_func():
    # from json import loads  -- removed 2026-05-01, no longer needed
    return None
"""
    path = write_py("a.py", src)
    assert find_function_scope_imports(path) == []


def test_string_literal_with_import_text_not_flagged(write_py) -> None:
    src = """
def my_func():
    error_msg = "Try `from json import loads` first."
    return error_msg
"""
    path = write_py("a.py", src)
    assert find_function_scope_imports(path) == []


def test_type_checking_block_at_module_scope_not_flagged(write_py) -> None:
    """TYPE_CHECKING block is If-node at MODULE scope (not function-scope)."""
    src = """
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

def my_func() -> "Iterator[int]":
    yield 1
"""
    path = write_py("a.py", src)
    assert find_function_scope_imports(path) == []


def test_noqa_marker_imports_inside_functions_skips(write_py) -> None:
    src = """
def my_func():
    from json import loads  # noqa: imports-inside-functions
    return loads("{}")
"""
    path = write_py("a.py", src)
    assert find_function_scope_imports(path) == []


def test_legacy_noqa_marker_qg_inside_import_skips(write_py) -> None:
    """Legacy marker from base-library.sh; kept for backwards compatibility."""
    src = """
def my_func():
    from json import loads  # noqa: qg-inside-import
    return loads("{}")
"""
    path = write_py("a.py", src)
    assert find_function_scope_imports(path) == []


def test_self_package_import_inside_function_not_flagged(write_py) -> None:
    """Preserves base-library.sh self-package auto-skip (circular-import workaround)."""
    src = """
def my_func():
    from my_pkg.submodule import helper
    return helper()
"""
    path = write_py("a.py", src)
    violations = find_function_scope_imports(path, self_pkg="my_pkg")
    assert violations == []
    # Without self_pkg, it IS flagged:
    violations = find_function_scope_imports(path, self_pkg=None)
    assert len(violations) == 1


def test_non_self_package_import_still_flagged_with_self_pkg(write_py) -> None:
    src = """
def my_func():
    from json import loads
    return loads("{}")
"""
    path = write_py("a.py", src)
    violations = find_function_scope_imports(path, self_pkg="my_pkg")
    assert len(violations) == 1


# ── Edge cases ───────────────────────────────────────────────────────────────


def test_syntax_error_returns_empty(write_py) -> None:
    """Files with syntax errors return empty list (not crash)."""
    src = """
def broken(:
    pass
"""
    path = write_py("a.py", src)
    assert find_function_scope_imports(path) == []


def test_empty_file_returns_empty(write_py) -> None:
    path = write_py("a.py", "")
    assert find_function_scope_imports(path) == []


def test_lambda_with_import_inside_flagged(write_py) -> None:
    """Lambdas can't contain imports as statements but nested defs CAN."""
    src = """
def outer():
    def inner():
        from json import loads
        return loads("{}")
    return inner
"""
    path = write_py("a.py", src)
    violations = find_function_scope_imports(path)
    assert len(violations) == 1
