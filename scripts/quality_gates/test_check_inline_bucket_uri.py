# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_inline_bucket_uri.py (QG STEP 5.69).

Pure-Python — no GCS/AWS/network. Run via pytest from a venv with pyyaml
(the workspace `.venv-workspace` satisfies this), or via the workspace-root
pytest invocation base-service.sh wires up.

Mirrors test_check_banned_placeholder_methods.py in shape: regex sanity,
single-file counting (noqa/comment skipping), workspace walker exclusions,
scope resolution, and a main() end-to-end smoke (synthetic over-baseline → exit
1; at/under baseline → exit 0).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from check_inline_bucket_uri import (  # type: ignore[import-not-found]
    _INLINE_URI_RE,
    _ast_docstring_lines,
    _iter_py_files,
    _resolve_scopes,
    count_inline_uris_in_file,
    load_baseline,
    main,
    scan_repo,
)


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


# ── Regex sanity ─────────────────────────────────────────────────────────────


def test_regex_matches_f_string_uri() -> None:
    assert _INLINE_URI_RE.search('path = f"gs://{bucket}/p.parquet"')
    assert _INLINE_URI_RE.search("uri = f's3://{b}/x'")
    assert _INLINE_URI_RE.search('x = f"prefix gs://{b}/y"')  # gs:// need not be at start
    assert _INLINE_URI_RE.search('rf"gs://{b}/raw"')


def test_regex_ignores_plain_string_scheme_check() -> None:
    # No `f` prefix → not a URI build, just a scheme check / literal.
    assert not _INLINE_URI_RE.search('if cloud_path.startswith("gs://"):')
    assert not _INLINE_URI_RE.search('SCHEME = "gs://"')
    assert not _INLINE_URI_RE.search("uri = scheme + '://' + bucket")
    # An identifier ending in `f` immediately before the quote is not an f-string.
    assert not _INLINE_URI_RE.search('myconf"gs://x"')  # contrived; the [^A-Za-z0-9_] guard rejects it


# ── Single-file counting ─────────────────────────────────────────────────────


def test_count_skips_noqa_and_comments(tmp_path: Path) -> None:
    f = _write(
        tmp_path / "mod.py",
        """
        def f(bucket: str, path: str) -> list[str]:
            a = f"gs://{bucket}/{path}"
            b = f"gs://{bucket}/{path}"  # noqa: gs-uri — resolved bucket var, deliberate
            # c = f"gs://{bucket}/old"  -- a commented-out line
            d = "gs://literal-no-fstring"
            return [a, b, d]
        """,
    )
    hits = count_inline_uris_in_file(f)
    # Only line `a = f"gs://..."` counts: `b` has the noqa marker, the `c` line is a
    # whole-line comment, `d` is a plain string (no f-prefix).
    assert len(hits) == 1


def test_count_zero_when_no_inline_uris(tmp_path: Path) -> None:
    f = _write(
        tmp_path / "clean.py",
        """
        from unified_trading_library import resolve_bucket_uri
        def g() -> str:
            return resolve_bucket_uri(cloud="gcp", kind="market-data", path="x", asset_group="cefi")
        """,
    )
    assert count_inline_uris_in_file(f) == []


# ── v2 AST-walk: docstring false-positive avoidance ─────────────────────────


def test_count_skips_plain_string_docstring_with_uri_example(tmp_path: Path) -> None:
    """v2: a gs:// reference inside a plain-string docstring is not an f-string — never flagged."""
    f = _write(
        tmp_path / "mod.py",
        '''
        def resolve(bucket: str, path: str) -> str:
            """Compose a URI like gs://{bucket}/{path} using resolve_bucket_uri().

            Example call:
                resolve_bucket_uri(cloud="gcp", kind="market-data", path="x")
            """
            from unified_trading_library import resolve_bucket_uri
            return resolve_bucket_uri(cloud="gcp", kind="market-data", path=path, asset_group="cefi")
        ''',
    )
    assert count_inline_uris_in_file(f) == []


def test_count_skips_fstring_docstring_containing_uri(tmp_path: Path) -> None:
    """v2: an f-string docstring (JoinedStr) with gs:// is skipped via _ast_docstring_lines."""
    f = _write(
        tmp_path / "naming.py",
        '''
        def make_uri(bucket: str, path: str) -> str:
            f"""Return a URI of the form gs://{bucket}/{path}.

            Prefer resolve_bucket_uri() over building the URI directly.
            """
            from unified_trading_library import resolve_bucket_uri
            return resolve_bucket_uri(cloud="gcp", kind="market-data", path=path, asset_group="cefi")
        ''',
    )
    assert count_inline_uris_in_file(f) == []


def test_count_flags_real_inline_uri_outside_docstring(tmp_path: Path) -> None:
    """v2: a gs:// f-string outside any docstring is still flagged."""
    f = _write(
        tmp_path / "bad.py",
        '''
        def bad(bucket: str, path: str) -> str:
            """Build a URI (SHOULD use resolve_bucket_uri instead)."""
            return f"gs://{bucket}/{path}"
        ''',
    )
    hits = count_inline_uris_in_file(f)
    assert len(hits) == 1


def test_ast_docstring_lines_covers_module_class_function() -> None:
    """_ast_docstring_lines detects docstrings at all three scopes."""
    import ast as _ast  # local re-import to avoid shadowing

    source = '''
"""Module docstring with gs://{x}/path example."""

class Foo:
    """Class docstring."""

    def method(self) -> str:
        """Method docstring."""
        return "x"
'''
    tree = _ast.parse(source)
    lines = _ast_docstring_lines(tree)
    assert len(lines) >= 3  # module + class + method docstrings each contribute lines


# ── Walker exclusions ────────────────────────────────────────────────────────


def test_iter_py_files_excludes_venv_tests_scripts(tmp_path: Path) -> None:
    _write(tmp_path / "pkg" / "real.py", "x = 1\n")
    _write(tmp_path / ".venv" / "lib" / "vendored.py", 'a = f"gs://{b}/x"\n')
    _write(tmp_path / "tests" / "test_thing.py", 'a = f"gs://{b}/x"\n')
    _write(tmp_path / "scripts" / "tool.py", 'a = f"gs://{b}/x"\n')
    _write(tmp_path / "pkg" / "test_inline.py", 'a = f"gs://{b}/x"\n')  # test_* basename
    found = {p.name for p in _iter_py_files(tmp_path)}
    assert "real.py" in found
    assert "vendored.py" not in found
    assert "test_thing.py" not in found
    assert "tool.py" not in found
    assert "test_inline.py" not in found


# ── scan_repo + scope resolution ─────────────────────────────────────────────


def test_scan_repo_counts_only_unmarked(tmp_path: Path) -> None:
    repo = tmp_path / "myrepo"
    _write(repo / "a.py", 'x = f"gs://{b}/1"\ny = f"gs://{b}/2"  # noqa: gs-uri\n')
    _write(repo / "sub" / "c.py", 'z = f"s3://{b}/3"\n')
    scan = scan_repo(repo, "myrepo")
    assert scan.count == 2  # a.py:1 and sub/c.py:1 (a.py:2 has the marker)
    assert scan.repo == "myrepo"


def test_resolve_scopes_single_repo(tmp_path: Path) -> None:
    (tmp_path / "repoA").mkdir()
    (tmp_path / "repoA" / ".git").mkdir()
    (tmp_path / "repoA" / "pkg").mkdir()
    scopes = _resolve_scopes(tmp_path, "repoA", "pkg")
    assert len(scopes) == 1
    name, root = scopes[0]
    assert name == "repoA"
    assert root.name == "pkg"


def test_resolve_scopes_workspace_wide(tmp_path: Path) -> None:
    for r in ("repoA", "repoB"):
        (tmp_path / r).mkdir()
        (tmp_path / r / ".git").mkdir()
    (tmp_path / "not-a-repo").mkdir()  # no .git → skipped
    (tmp_path / ".hidden").mkdir()  # dot-dir → skipped
    names = {n for n, _ in _resolve_scopes(tmp_path, None, None)}
    assert names == {"repoA", "repoB"}


# ── Baseline loading ─────────────────────────────────────────────────────────


def test_load_baseline_real_file_present() -> None:
    # The committed baseline must parse and be non-empty (seeded 2026-05-11).
    bl = load_baseline()
    assert isinstance(bl.counts, dict)
    # `allowed()` defaults unknown repos to 0.
    assert bl.allowed("a-repo-that-definitely-is-not-listed") == 0


# ── main() end-to-end ────────────────────────────────────────────────────────


def test_main_fails_when_repo_over_baseline(tmp_path: Path) -> None:
    # Point the checker at a synthetic workspace with one repo NOT in the real
    # baseline (count defaults to 0) that has 1 inline formatter → exit 1.
    repo = tmp_path / "synthetic-over-baseline-repo"
    (repo / ".git").mkdir(parents=True)
    _write(repo / "pkg" / "writer.py", 'def w(b: str) -> str:\n    return f"gs://{b}/raw"\n')
    rc = main(["--workspace-root", str(tmp_path), "--scope", "synthetic-over-baseline-repo"])
    assert rc == 1


def test_main_clean_when_no_inline_uris(tmp_path: Path) -> None:
    repo = tmp_path / "clean-repo"
    (repo / ".git").mkdir(parents=True)
    _write(repo / "pkg" / "clean.py", "x = 1\n")
    rc = main(["--workspace-root", str(tmp_path), "--scope", "clean-repo"])
    assert rc == 0


def test_main_clean_when_noqa_marked(tmp_path: Path) -> None:
    repo = tmp_path / "marked-repo"
    (repo / ".git").mkdir(parents=True)
    _write(repo / "pkg" / "writer.py", 'def w(b: str) -> str:\n    return f"gs://{b}/raw"  # noqa: gs-uri\n')
    rc = main(["--workspace-root", str(tmp_path), "--scope", "marked-repo"])
    assert rc == 0
