# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_asyncio_manifest_explicit_drain.py.

Pure-Python — no GCS/AWS/network. Mirrors test_check_pipeline_mode_explicit_at_record_calls.py
in shape: single-file scanning, noqa marker behaviour, workspace walker exclusions,
baseline tolerance, and a main() end-to-end smoke.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from check_asyncio_manifest_explicit_drain import (  # type: ignore[import-not-found]
    NOQA_MARKER,
    Baseline,
    _iter_py_files,
    file_missing_explicit_drain,
    main,
    scan_repo,
)


def _write_py(tmp_path: Path, name: str, content: str) -> Path:
    file = tmp_path / name
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(textwrap.dedent(content), encoding="utf-8")
    return file


def test_flags_asyncio_manifest_without_explicit_drain(tmp_path: Path) -> None:
    """asyncio.run( + MANIFEST_PER_VM_SHARDS present, no flush_all_pending_buckets( -> flagged."""
    target = _write_py(
        tmp_path,
        "backfill.py",
        """
        import asyncio
        import os

        os.environ["MANIFEST_PER_VM_SHARDS"] = "true"

        async def main() -> None:
            ...

        if __name__ == "__main__":
            asyncio.run(main())
        """,
    )
    assert file_missing_explicit_drain(target) is True


def test_clean_when_explicit_drain_present(tmp_path: Path) -> None:
    """The same shape but with an explicit flush_all_pending_buckets() call is clean."""
    target = _write_py(
        tmp_path,
        "backfill.py",
        """
        import asyncio
        import os

        os.environ["MANIFEST_PER_VM_SHARDS"] = "true"

        async def main() -> None:
            flushed = _mw.flush_all_pending_buckets()

        if __name__ == "__main__":
            asyncio.run(main())
        """,
    )
    assert file_missing_explicit_drain(target) is False


def test_clean_when_no_asyncio_run(tmp_path: Path) -> None:
    """A file referencing MANIFEST_PER_VM_SHARDS but never calling asyncio.run( is not flagged."""
    target = _write_py(
        tmp_path,
        "sync_backfill.py",
        """
        import os

        os.environ["MANIFEST_PER_VM_SHARDS"] = "true"

        def main() -> None:
            ...
        """,
    )
    assert file_missing_explicit_drain(target) is False


def test_clean_when_no_manifest_per_vm_shards(tmp_path: Path) -> None:
    """A plain asyncio script that never touches per-VM shard mode is not flagged."""
    target = _write_py(
        tmp_path,
        "unrelated.py",
        """
        import asyncio

        async def main() -> None:
            ...

        asyncio.run(main())
        """,
    )
    assert file_missing_explicit_drain(target) is False


def test_noqa_marker_bypasses_flagged_file(tmp_path: Path) -> None:
    """Inline `# noqa: qg-asyncio-manifest-drain` bypasses the check for the whole file."""
    target = _write_py(
        tmp_path,
        "backfill.py",
        f"""
        import asyncio
        import os

        os.environ["MANIFEST_PER_VM_SHARDS"] = "true"  # {NOQA_MARKER} — read-only manifest access

        async def main() -> None:
            ...

        asyncio.run(main())
        """,
    )
    assert file_missing_explicit_drain(target) is False


def test_iter_py_files_skips_venv_and_archive(tmp_path: Path) -> None:
    """Walker skips .venv / tests / /archive/ dirs but NOT scripts/ (the anti-pattern lives there)."""
    (tmp_path / "src").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / ".venv").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / "src" / "real.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "scripts" / "backfill.py").write_text("y = 2\n", encoding="utf-8")
    (tmp_path / ".venv" / "lib.py").write_text("y = 2\n", encoding="utf-8")
    (tmp_path / "tests" / "test_x.py").write_text("z = 3\n", encoding="utf-8")
    files = list(_iter_py_files(tmp_path))
    rels = sorted(str(f.relative_to(tmp_path)) for f in files)
    assert rels == ["scripts/backfill.py", "src/real.py"]


def test_scan_repo_counts_offending_files(tmp_path: Path) -> None:
    """scan_repo() counts exactly the offending files, sorted by relative path."""
    repo = tmp_path / "myrepo"
    _write_py(
        repo,
        "scripts/backfill_a.py",
        """
        import asyncio, os
        os.environ["MANIFEST_PER_VM_SHARDS"] = "true"
        asyncio.run(main())
        """,
    )
    _write_py(
        repo,
        "scripts/backfill_b.py",
        """
        import asyncio, os
        os.environ["MANIFEST_PER_VM_SHARDS"] = "true"
        _mw.flush_all_pending_buckets()
        asyncio.run(main())
        """,
    )
    scan = scan_repo(repo, "myrepo", repo_root=repo)
    assert scan.count == 1
    assert scan.sites == ["scripts/backfill_a.py"]


def test_main_at_baseline_returns_zero(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A repo whose offending-file count equals its baseline returns 0."""
    repo = tmp_path / "myrepo"
    _write_py(
        repo,
        "scripts/backfill.py",
        """
        import asyncio, os
        os.environ["MANIFEST_PER_VM_SHARDS"] = "true"
        asyncio.run(main())
        """,
    )
    baseline_file = tmp_path / "baseline.yaml"
    baseline_file.write_text("repos:\n  myrepo:\n    count: 1\n", encoding="utf-8")
    rc = main(
        [
            "--workspace-root",
            str(tmp_path),
            "--scope",
            "myrepo",
            "--baseline-file",
            str(baseline_file),
        ]
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "OK" in captured.out


def test_main_over_baseline_returns_one(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """A NEW offending file above the (zero) baseline fails the gate."""
    repo = tmp_path / "myrepo"
    _write_py(
        repo,
        "scripts/backfill.py",
        """
        import asyncio, os
        os.environ["MANIFEST_PER_VM_SHARDS"] = "true"
        asyncio.run(main())
        """,
    )
    rc = main(["--workspace-root", str(tmp_path), "--scope", "myrepo"])
    captured = capsys.readouterr()
    assert rc == 1
    assert "FAIL" in captured.err
    assert "backfill.py" in captured.err


def test_baseline_allowed_defaults_to_zero() -> None:
    """A repo not listed in the baseline defaults to allowed=0."""
    baseline = Baseline(counts={"other-repo": 5})
    assert baseline.allowed("myrepo") == 0
    assert baseline.allowed("other-repo") == 5
