# Epic: deployment_and_user_management_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for import_graph_walker.py.

Verifies module resolution (absolute + relative imports, package `__init__.py`
targets), edge inversion, transitive-importer BFS, and the content-sentinel
cache key — against synthetic fixture repos built under `tmp_path`, per
test_impact_fleet_wide_measurement_and_rollout_2026_08_03.md Phase 2 todo 1's
done-when ("a verifiably-correct edge table for a hand-checked sample").
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from import_graph_walker import (  # type: ignore[import-not-found]
    affected_test_files,
    build_import_edges,
    compute_content_sentinel,
    invert_edges,
    transitive_importers,
)


def _write(root: Path, rel_path: str, content: str) -> Path:
    path = root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(textwrap.dedent(content).lstrip())
    return path


def _make_fixture_repo(tmp_path: Path) -> Path:
    """A small package: base -> mid -> leaf, plus a relative-import sibling,
    a package __init__.py target, and a test file importing the leaf."""
    repo = tmp_path / "repo"
    _write(repo, "pkg/__init__.py", "")
    _write(repo, "pkg/base.py", "def base_fn(): return 1\n")
    _write(
        repo,
        "pkg/mid.py",
        """
        from pkg.base import base_fn

        def mid_fn(): return base_fn() + 1
        """,
    )
    _write(
        repo,
        "pkg/leaf.py",
        """
        from pkg.mid import mid_fn

        def leaf_fn(): return mid_fn() + 1
        """,
    )
    _write(
        repo,
        "pkg/sibling.py",
        """
        from .base import base_fn

        def sibling_fn(): return base_fn() + 2
        """,
    )
    _write(repo, "pkg/subpkg/__init__.py", "VALUE = 1\n")
    _write(
        repo,
        "pkg/uses_subpkg.py",
        """
        from pkg import subpkg

        def f(): return subpkg.VALUE
        """,
    )
    _write(
        repo,
        "tests/test_leaf.py",
        """
        from pkg.leaf import leaf_fn

        def test_leaf_fn():
            assert leaf_fn() == 3
        """,
    )
    _write(
        repo,
        "pkg/broken.py",
        "def f(:\n",  # deliberately unparseable
    )
    return repo


def test_build_import_edges_absolute_import(tmp_path: Path) -> None:
    # `from pkg.base import base_fn` genuinely executes `pkg/__init__.py`
    # (the ancestor package) before `pkg/base.py` — both are real edges.
    repo = _make_fixture_repo(tmp_path)
    edges = build_import_edges(repo)
    mid_edges = edges[repo / "pkg/mid.py"]
    assert mid_edges == {repo / "pkg/__init__.py", repo / "pkg/base.py"}


def test_build_import_edges_relative_import(tmp_path: Path) -> None:
    repo = _make_fixture_repo(tmp_path)
    edges = build_import_edges(repo)
    sibling_edges = edges[repo / "pkg/sibling.py"]
    assert sibling_edges == {repo / "pkg/base.py"}


def test_build_import_edges_package_init_target(tmp_path: Path) -> None:
    # `from pkg import subpkg` genuinely executes BOTH `pkg/__init__.py` (the
    # package being imported FROM) and `pkg/subpkg/__init__.py` (the submodule
    # target) — recording both is the correct conservative-superset edge set,
    # not a narrower "just the submodule" edge.
    repo = _make_fixture_repo(tmp_path)
    edges = build_import_edges(repo)
    uses_subpkg_edges = edges[repo / "pkg/uses_subpkg.py"]
    assert uses_subpkg_edges == {repo / "pkg/__init__.py", repo / "pkg/subpkg/__init__.py"}


def test_build_import_edges_unparseable_file_yields_no_edges(tmp_path: Path) -> None:
    repo = _make_fixture_repo(tmp_path)
    edges = build_import_edges(repo)
    assert edges[repo / "pkg/broken.py"] == frozenset()


def test_transitive_importers_bfs(tmp_path: Path) -> None:
    repo = _make_fixture_repo(tmp_path)
    edges = build_import_edges(repo)
    inverted = invert_edges(edges)
    # base.py is imported directly by mid.py and sibling.py, and
    # TRANSITIVELY by leaf.py (via mid.py) and tests/test_leaf.py (via leaf.py).
    importers = transitive_importers(repo / "pkg/base.py", inverted)
    assert importers == {
        repo / "pkg/mid.py",
        repo / "pkg/sibling.py",
        repo / "pkg/leaf.py",
        repo / "tests/test_leaf.py",
    }


def test_transitive_importers_leaf_has_only_test(tmp_path: Path) -> None:
    repo = _make_fixture_repo(tmp_path)
    edges = build_import_edges(repo)
    inverted = invert_edges(edges)
    importers = transitive_importers(repo / "pkg/leaf.py", inverted)
    assert importers == {repo / "tests/test_leaf.py"}


def test_affected_test_files_narrows_to_the_one_dependent_test(tmp_path: Path) -> None:
    repo = _make_fixture_repo(tmp_path)
    edges = build_import_edges(repo)
    inverted = invert_edges(edges)
    affected = affected_test_files([repo / "pkg/base.py"], inverted)
    assert affected == {repo / "tests/test_leaf.py"}


def test_affected_test_files_empty_for_untested_leaf(tmp_path: Path) -> None:
    repo = _make_fixture_repo(tmp_path)
    edges = build_import_edges(repo)
    inverted = invert_edges(edges)
    # subpkg/__init__.py has exactly one importer (uses_subpkg.py), which is
    # not itself a test and has no test importing IT, so no test is affected.
    affected = affected_test_files([repo / "pkg/subpkg/__init__.py"], inverted)
    assert affected == frozenset()


def test_content_sentinel_changes_when_a_file_changes(tmp_path: Path) -> None:
    repo = _make_fixture_repo(tmp_path)
    before = compute_content_sentinel(repo)
    _ = (repo / "pkg/base.py").write_text("def base_fn(): return 999\n")
    after = compute_content_sentinel(repo)
    assert before != after


def test_content_sentinel_stable_for_unchanged_tree(tmp_path: Path) -> None:
    repo = _make_fixture_repo(tmp_path)
    first = compute_content_sentinel(repo)
    second = compute_content_sentinel(repo)
    assert first == second
