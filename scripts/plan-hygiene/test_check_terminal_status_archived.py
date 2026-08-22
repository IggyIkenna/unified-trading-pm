# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_terminal_status_archived.py's --only symlink-resolution fix
(pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md, todo B).

THE BUG: `PM_DIR = Path(__file__).resolve().parents[2]` is symlink-resolved, but `_run_only`'s
`p = Path.cwd() / p` was NOT — `Path.cwd()` reflects the shell's un-resolved `$PWD` (macOS's
`/var/...` is a symlink to the real `/private/var/...`). Running `--precommit` from a worktree
under `/var/folders/...` (any macOS tmp-based worktree, including `ship-from-worktree.sh`'s
default) made `p.relative_to(PM_DIR)` raise `ValueError` even though both paths name the exact
same file — crashing the whole precommit sweep with a Python traceback (printed as a hard
failure) instead of a clean pass/fail. Hit live 2026-08-12 profiling the precommit critical
section for this same issue doc.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import check_terminal_status_archived as checker


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def pm_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    real = tmp_path / "real_root"
    (real / "plans" / "active" / "issues").mkdir(parents=True)
    _git(real, "init", "-q")
    monkeypatch.setattr(checker, "PM_DIR", real.resolve())
    return real


def _write(p: Path, status: str, doc_type: str) -> None:
    p.write_text(
        f"---\ndoc_type: {doc_type}\nstatus: {status}\n---\n\n# doc\n",
        encoding="utf-8",
    )


def test_only_mode_survives_a_symlinked_cwd(pm_repo: Path, tmp_path: Path) -> None:
    """Reproduces the exact incident: PM_DIR is the RESOLVED path; the file handed to
    --only is reached via a symlinked alias of the same directory, standing in for macOS's
    /var -> /private/var. Must not raise, and must still classify correctly."""
    doc = pm_repo / "plans" / "active" / "issues" / "open_one.md"
    _write(doc, "open", "issue")  # not terminal -> no violation

    alias = tmp_path / "alias_root"
    os.symlink(pm_repo, alias, target_is_directory=True)
    aliased_doc = alias / "plans" / "active" / "issues" / "open_one.md"

    violations = []
    for raw in [str(aliased_doc)]:
        p = Path(raw)
        if not p.is_absolute():
            p = Path.cwd() / p
        p = p.resolve()
        v = checker._check_one(p)
        if v is not None:
            violations.append(v)
    assert violations == []


def test_only_mode_still_flags_a_real_violation_through_the_symlink(pm_repo: Path, tmp_path: Path) -> None:
    doc = pm_repo / "plans" / "active" / "issues" / "resolved_one.md"
    _write(doc, "resolved", "issue")  # terminal -> violation

    alias = tmp_path / "alias_root2"
    os.symlink(pm_repo, alias, target_is_directory=True)
    aliased_doc = alias / "plans" / "active" / "issues" / "resolved_one.md"

    p = aliased_doc.resolve()
    v = checker._check_one(p)
    assert v is not None
    assert "status=resolved" in v


def test_run_only_end_to_end_through_symlink_does_not_crash(
    pm_repo: Path, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    doc = pm_repo / "plans" / "active" / "issues" / "resolved_two.md"
    _write(doc, "resolved", "issue")

    alias = tmp_path / "alias_root3"
    os.symlink(pm_repo, alias, target_is_directory=True)
    aliased_doc = alias / "plans" / "active" / "issues" / "resolved_two.md"

    rc = checker._run_only([str(aliased_doc)], quiet=False)
    out = capsys.readouterr().out
    assert rc == 1
    assert "1 violation(s)" in out
