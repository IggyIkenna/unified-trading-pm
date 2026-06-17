"""Hermetic end-to-end test for the strict-quickmerge provenance checker.

Builds a throwaway git repo with one commit of each class and asserts `commit_violates`
flags ONLY a genuine bypass — a CODE change (`*.py`/`*.ts`/`*.tsx` outside
scripts/tests/.github) with no `Quickmerge:` trailer. This is the durable true-positive
proof for `provenance_gate_squash_perpetual_block_2026_06_17.md`: the squash-blind RANGE
fix narrows WHICH commits are scanned, but a fresh trailer-less bypass after the marker
must STILL be caught — the HARD RULE itself is unchanged.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_MOD_PATH = Path(__file__).resolve().parents[2] / "scripts" / "cicd" / "check_strict_quickmerge.py"
_spec = importlib.util.spec_from_file_location("check_strict_quickmerge", _MOD_PATH)
assert _spec and _spec.loader
csq = importlib.util.module_from_spec(_spec)
sys.modules["check_strict_quickmerge"] = csq
_spec.loader.exec_module(csq)

_ENV = {
    "GIT_AUTHOR_NAME": "Test Dev",
    "GIT_AUTHOR_EMAIL": "dev@example.com",
    "GIT_COMMITTER_NAME": "Test Dev",
    "GIT_COMMITTER_EMAIL": "dev@example.com",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
}


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=repo, env={"PATH": _path(), **_ENV}, check=True, capture_output=True, text=True)


def _path() -> str:
    import os

    return os.environ.get("PATH", "/usr/bin:/bin")


def _commit(repo: Path, rel: str, content: str, message: str, author: str | None = None) -> str:
    fp = repo / rel
    fp.parent.mkdir(parents=True, exist_ok=True)
    fp.write_text(content)
    _git(repo, "add", rel)
    env = {"PATH": _path(), **_ENV}
    if author:
        env["GIT_AUTHOR_NAME"] = author
        env["GIT_COMMITTER_NAME"] = author
    subprocess.run(
        ["git", "commit", "-q", "-m", message], cwd=repo, env=env, check=True, capture_output=True, text=True
    )
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, env={"PATH": _path()}, check=True, capture_output=True, text=True
    )
    return out.stdout.strip()


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    r = tmp_path / "repo"
    r.mkdir()
    _git(r, "init", "-q", "-b", "main")
    monkeypatch.chdir(r)  # the checker's _git runs in CWD
    return r


def test_trailerless_source_commit_is_flagged(repo: Path):
    # The 14b11e2 class: a *.py change with no `Quickmerge:` trailer, ordinary dev author.
    sha = _commit(repo, "src/bus.py", "x = 1\n", "fix(kill-switch): guard the bus")
    bad, why = csq.commit_violates(sha)
    assert bad is True
    assert "source changed without quickmerge" in why


def test_quickmerge_trailer_not_flagged(repo: Path):
    sha = _commit(repo, "src/bus.py", "x = 2\n", "fix: thing\n\nQuickmerge: agent")
    bad, why = csq.commit_violates(sha)
    assert bad is False
    assert "quickmerge" in why


def test_carveout_scripts_not_flagged(repo: Path):
    # scripts/ and .github/ .py are NONSOURCE_DIR → carve-out (no source changed).
    sha = _commit(repo, "scripts/migrate.py", "y = 1\n", "chore: migration script")
    bad, _ = csq.commit_violates(sha)
    assert bad is False


def test_docs_only_not_flagged(repo: Path):
    sha = _commit(repo, "docs/readme.md", "# hi\n", "docs: update readme")
    bad, _ = csq.commit_violates(sha)
    assert bad is False


def test_skip_ci_automation_not_flagged(repo: Path):
    sha = _commit(repo, "src/bus.py", "x = 3\n", "chore: regen [skip ci]")
    bad, why = csq.commit_violates(sha)
    assert bad is False
    assert "automation" in why


def test_bot_author_not_flagged(repo: Path):
    sha = _commit(repo, "src/bus.py", "x = 4\n", "fix: thing", author="github-actions[bot]")
    bad, _ = csq.commit_violates(sha)
    assert bad is False
