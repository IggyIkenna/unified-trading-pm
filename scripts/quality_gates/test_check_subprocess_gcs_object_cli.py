# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_subprocess_gcs_object_cli.py (QG STEP 5.105).

Pure-Python — no GCS/AWS/network. Run via pytest from a venv with pyyaml (the
workspace `.venv-workspace` satisfies this), or via the workspace-root pytest
invocation base-service.sh wires up.

Mirrors test_check_inline_bucket_uri.py in shape: classification sanity,
single-file counting (noqa/comment skipping, variable-resolution idiom),
workspace walker (scripts/ is NOT excluded, unlike STEP 5.69), scope
resolution, baseline loading, and a main() end-to-end smoke.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from check_subprocess_gcs_object_cli import (  # type: ignore[import-not-found]
    _classify_tokens,
    _iter_py_files,
    _resolve_scopes,
    count_hits_in_file,
    load_baseline,
    main,
    scan_repo,
)


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


# ── Classification sanity ────────────────────────────────────────────────────


def test_classify_flags_object_level_ops() -> None:
    assert _classify_tokens(["gcloud", "storage", "rm", "gs://b/x"]) is not None
    assert _classify_tokens(["gcloud", "storage", "cp", "a", "gs://b/x"]) is not None
    assert _classify_tokens(["gsutil", "rm", "gs://b/x"]) is not None
    assert _classify_tokens(["gsutil", "cat", "gs://b/x"]) is not None
    assert _classify_tokens(["aws", "s3", "rm", "s3://b/x"]) is not None
    assert _classify_tokens(["aws", "s3", "sync", "a", "s3://b/x"]) is not None
    assert _classify_tokens(["aws", "s3api", "delete-object", "--bucket", "b"]) is not None
    assert _classify_tokens(["aws", "s3api", "get-object", "--bucket", "b"]) is not None


def test_classify_does_not_flag_bucket_admin_ops() -> None:
    # Bucket-level admin ops have no UTL equivalent -- deliberately out of scope.
    assert _classify_tokens(["gsutil", "mb", "gs://b"]) is None
    assert _classify_tokens(["gsutil", "versioning", "set", "on", "gs://b"]) is None
    assert _classify_tokens(["gsutil", "lifecycle", "set", "policy.json", "gs://b"]) is None
    assert _classify_tokens(["gcloud", "storage", "buckets", "create", "gs://b"]) is None
    assert _classify_tokens(["aws", "s3", "rb", "s3://b"]) is None
    assert _classify_tokens(["aws", "s3api", "create-bucket", "--bucket", "b"]) is None


def test_classify_ignores_unrelated_commands() -> None:
    assert _classify_tokens(["git", "push", "origin", "main"]) is None
    assert _classify_tokens(["gcloud", "compute", "instances", "create", "x"]) is None
    assert _classify_tokens([]) is None


# ── Single-file counting: literal inline form ───────────────────────────────


def test_count_flags_literal_inline_list_call(tmp_path: Path) -> None:
    f = _write(
        tmp_path / "mod.py",
        """
        import subprocess

        def delete_it(uri: str) -> None:
            subprocess.run(["gsutil", "rm", uri], check=True)
        """,
    )
    hits = count_hits_in_file(f)
    assert len(hits) == 1


def test_count_skips_noqa_marker(tmp_path: Path) -> None:
    f = _write(
        tmp_path / "mod.py",
        """
        import subprocess

        def delete_it(uri: str) -> None:
            subprocess.run(["gsutil", "rm", uri], check=True)  # noqa: gcs-cli — deliberate, audited
        """,
    )
    assert count_hits_in_file(f) == []


def test_count_zero_when_using_sdk_wrapper(tmp_path: Path) -> None:
    f = _write(
        tmp_path / "clean.py",
        """
        from unified_trading_library import gcs_delete_object

        def delete_it(uri: str) -> None:
            gcs_delete_object(uri)
        """,
    )
    assert count_hits_in_file(f) == []


# ── Single-file counting: the dominant real-world idiom (assign-then-call) ──


def test_count_resolves_variable_assigned_command(tmp_path: Path) -> None:
    """The dominant real idiom found in production code (maintenance_handler.py,
    analyze_shard_memory.py): the command list is assigned to a variable first,
    THEN passed to subprocess.run — not inlined directly as the call argument."""
    f = _write(
        tmp_path / "maintenance.py",
        """
        import subprocess

        def cleanup(file_path: str) -> None:
            cmd = ["gsutil", "rm", file_path]
            subprocess.run(cmd, check=True, capture_output=True)
        """,
    )
    hits = count_hits_in_file(f)
    assert len(hits) == 1


def test_count_resolves_nearest_preceding_assignment_per_function(tmp_path: Path) -> None:
    """Two functions reusing the same variable name each resolve to THEIR OWN
    nearest-preceding assignment, not to a stale one from an earlier function."""
    f = _write(
        tmp_path / "multi.py",
        """
        import subprocess

        def list_objects(bucket: str) -> None:
            cmd = ["gsutil", "ls", "-b", bucket]
            subprocess.run(cmd, capture_output=True)

        def create_bucket(bucket: str) -> None:
            cmd = ["gsutil", "mb", bucket]
            subprocess.run(cmd, check=True)
        """,
    )
    hits = count_hits_in_file(f)
    # list_objects' `gsutil ls` is an object op (flagged); create_bucket's `gsutil mb`
    # is bucket-admin (not flagged).
    assert len(hits) == 1


def test_count_skips_dynamic_command_with_no_resolvable_assignment(tmp_path: Path) -> None:
    """A command built from a function parameter (no local literal assignment to
    resolve) is a false-negative, not a guess -- documented trade-off."""
    f = _write(
        tmp_path / "dynamic.py",
        """
        import subprocess

        def run_it(cmd: list[str]) -> None:
            subprocess.run(cmd, check=True)
        """,
    )
    assert count_hits_in_file(f) == []


def test_count_skips_docstring_and_comment_mentions(tmp_path: Path) -> None:
    """A prose mention of 'gsutil rm' in a docstring/comment (not a real call) is
    never flagged -- this check only inspects actual subprocess call arguments."""
    f = _write(
        tmp_path / "prose.py",
        '''
        def helper() -> None:
            """This does NOT run `gsutil rm` directly; see the SDK wrapper instead."""
            # gcloud storage rm gs://bucket/object -- old approach, no longer used
            pass
        ''',
    )
    assert count_hits_in_file(f) == []


def test_count_flags_os_system(tmp_path: Path) -> None:
    # A pure literal string arg (the shape this checker's static extraction
    # handles) -- string CONCATENATION (`"gsutil rm " + uri`) is a documented
    # false-negative, same trade-off as any other dynamically-built command.
    f = _write(
        tmp_path / "legacy.py",
        """
        import os

        def delete_it() -> None:
            os.system("gsutil rm gs://static-bucket/known-object")
        """,
    )
    hits = count_hits_in_file(f)
    assert len(hits) == 1


# ── Walker: scripts/ is NOT excluded (the whole point of this check) ───────


def test_iter_py_files_does_not_exclude_scripts_dir(tmp_path: Path) -> None:
    _write(tmp_path / "pkg" / "real.py", "x = 1\n")
    _write(tmp_path / ".venv" / "lib" / "vendored.py", "x = 1\n")
    _write(tmp_path / "scripts" / "tool.py", "x = 1\n")
    found = {p.name for p in _iter_py_files(tmp_path)}
    assert "real.py" in found
    assert "tool.py" in found  # unlike STEP 5.69, scripts/ IS scanned here
    assert "vendored.py" not in found


# ── scan_repo + scope resolution ────────────────────────────────────────────


def test_scan_repo_counts_only_unmarked_object_ops(tmp_path: Path) -> None:
    repo = tmp_path / "myrepo"
    _write(
        repo / "scripts" / "a.py",
        "import subprocess\n"
        'subprocess.run(["gsutil", "rm", "gs://b/1"])\n'
        'subprocess.run(["gsutil", "rm", "gs://b/2"])  # noqa: gcs-cli\n',
    )
    _write(
        repo / "pkg" / "b.py",
        'import subprocess\nsubprocess.run(["aws", "s3", "cp", "a", "s3://b/c"])\n',
    )
    scan = scan_repo(repo, "myrepo")
    assert scan.count == 2  # scripts/a.py:1 (unmarked) + pkg/b.py:1
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
    (tmp_path / "not-a-repo").mkdir()  # no .git -> skipped
    (tmp_path / ".hidden").mkdir()  # dot-dir -> skipped
    names = {n for n, _ in _resolve_scopes(tmp_path, None, None)}
    assert names == {"repoA", "repoB"}


# ── Baseline loading ─────────────────────────────────────────────────────────


def test_load_baseline_real_file_present() -> None:
    # The committed baseline must parse and be non-empty (seeded 2026-07-27).
    bl = load_baseline()
    assert isinstance(bl.counts, dict)
    # `allowed()` defaults unknown repos to 0.
    assert bl.allowed("a-repo-that-definitely-is-not-listed") == 0


# ── main() end-to-end ────────────────────────────────────────────────────────


def test_main_fails_when_repo_over_baseline(tmp_path: Path) -> None:
    repo = tmp_path / "synthetic-over-baseline-repo"
    (repo / ".git").mkdir(parents=True)
    _write(
        repo / "scripts" / "cleanup.py",
        'import subprocess\n\ndef w(uri: str) -> None:\n    subprocess.run(["gsutil", "rm", uri])\n',
    )
    rc = main(["--workspace-root", str(tmp_path), "--scope", "synthetic-over-baseline-repo"])
    assert rc == 1


def test_main_clean_when_no_object_cli_calls(tmp_path: Path) -> None:
    repo = tmp_path / "clean-repo"
    (repo / ".git").mkdir(parents=True)
    _write(repo / "pkg" / "clean.py", "x = 1\n")
    rc = main(["--workspace-root", str(tmp_path), "--scope", "clean-repo"])
    assert rc == 0


def test_main_clean_when_noqa_marked(tmp_path: Path) -> None:
    repo = tmp_path / "marked-repo"
    (repo / ".git").mkdir(parents=True)
    _write(
        repo / "scripts" / "cleanup.py",
        "import subprocess\n\n"
        "def w(uri: str) -> None:\n"
        '    subprocess.run(["gsutil", "rm", uri])  # noqa: gcs-cli — reason\n',
    )
    rc = main(["--workspace-root", str(tmp_path), "--scope", "marked-repo"])
    assert rc == 0
