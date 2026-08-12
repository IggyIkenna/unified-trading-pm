# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_plan_commit_sha_evidence.py's origin-reachability requirement
(pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md, todo 5).

THE BUG THIS CLOSES: `git cat-file -t <sha>` succeeds for ANY object present in the local
object database, including a dangling commit a rebase already rewrote away. Both `4f901b9916`
and the earlier `0f9b8a65ca` incident existed as loose local objects when their citing commit
was authored (so the OLD precommit check, which only asked "does this object exist", passed)
but were reachable from no branch — either because the citing worker cited its own commit's
pre-rebase SHA (both shipping wrappers rebase before pushing, which rewrites it) or a
transcription slip. Neither was caught until a corpus-wide re-gate, hours later.

THE FIX: `_is_reachable_from_any_branch` additionally requires the cited sha be an ancestor of
some `origin/*` ref or of local HEAD — mirroring `reconcile-sha-citations.sh` Pass 2's own
reachability test, applied here BEFORE the commit instead of after. `_resolves_to_commit`'s new
`require_reachable` flag wires that in, scoped (by `main`) to citations of the repo's own
history — a cross-repo citation keeps the weaker existence-only test, since PM does not control
when a sibling repo pushes or rebases.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import check_plan_commit_sha_evidence as checker


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True)


@pytest.fixture
def repo_with_origin(tmp_path: Path) -> tuple[Path, Path]:
    """A bare `origin` plus a clone with one commit already pushed to `main`."""
    origin = tmp_path / "origin.git"
    origin.mkdir()
    subprocess.run(["git", "init", "-q", "--bare", str(origin)], check=True, capture_output=True)

    repo = tmp_path / "repo"
    subprocess.run(["git", "clone", "-q", str(origin), str(repo)], check=True, capture_output=True)
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    _git(repo, "checkout", "-q", "-B", "main")
    (repo / "README.md").write_text("seed\n", encoding="utf-8")
    _git(repo, "add", "README.md")
    _git(repo, "commit", "-q", "-m", "seed")
    _git(repo, "push", "-q", "origin", "HEAD:main")
    return repo, origin


def _commit(repo: Path, rel_path: str, content: str, message: str = "commit") -> str:
    p = repo / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    _git(repo, "add", rel_path)
    _git(repo, "commit", "-q", "-m", message)
    return _git(repo, "rev-parse", "HEAD").stdout.strip()


class TestIsReachableFromAnyBranch:
    def test_pushed_commit_is_reachable(self, repo_with_origin: tuple[Path, Path]) -> None:
        repo, _origin = repo_with_origin
        sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
        assert checker._is_reachable_from_any_branch(repo, sha) is True

    def test_local_only_unpushed_commit_is_reachable(self, repo_with_origin: tuple[Path, Path]) -> None:
        # The reconciler's own "OR local HEAD" allowance: genuinely unpushed-but-not-yet-rebased
        # work must not be flagged just for not being on origin yet.
        repo, _origin = repo_with_origin
        sha = _commit(repo, "unpushed.md", "content\n", "not yet pushed")
        assert checker._is_reachable_from_any_branch(repo, sha) is True

    def test_dangling_orphan_commit_is_not_reachable(self, repo_with_origin: tuple[Path, Path]) -> None:
        # Simulates the exact incident: a commit made, then rewritten out from under itself by
        # a reset (standing in for what a rebase does to the pre-rebase SHA) -- the old SHA
        # stays a loose object (git has not GC'd it) but is on no branch.
        repo, _origin = repo_with_origin
        orphan_sha = _commit(repo, "reset_away.md", "content\n", "will be reset away")
        _git(repo, "reset", "-q", "--hard", "HEAD~1")
        # Still present as a loose object -- this is the property the OLD check relied on.
        assert checker._cat_file_is_commit(repo, orphan_sha) is True
        # ...but reachable from nothing, which is the property that matters.
        assert checker._is_reachable_from_any_branch(repo, orphan_sha) is False


class TestResolvesToCommitRequireReachable:
    def test_dangling_orphan_passes_when_require_reachable_false(self, repo_with_origin: tuple[Path, Path]) -> None:
        # Cross-repo citations keep the weaker existence-only test (unchanged behaviour).
        repo, _origin = repo_with_origin
        orphan_sha = _commit(repo, "reset_away.md", "content\n", "will be reset away")
        _git(repo, "reset", "-q", "--hard", "HEAD~1")
        assert checker._resolves_to_commit(repo, orphan_sha, require_reachable=False) is True

    def test_dangling_orphan_fails_when_require_reachable_true(self, repo_with_origin: tuple[Path, Path]) -> None:
        # Self-citations get the stricter test -- this is the actual fix, reproducing the
        # 4f901b9916 / 0f9b8a65ca shape directly.
        repo, _origin = repo_with_origin
        orphan_sha = _commit(repo, "reset_away.md", "content\n", "will be reset away")
        _git(repo, "reset", "-q", "--hard", "HEAD~1")
        assert checker._resolves_to_commit(repo, orphan_sha, require_reachable=True) is False

    def test_pushed_commit_passes_require_reachable_true(self, repo_with_origin: tuple[Path, Path]) -> None:
        repo, _origin = repo_with_origin
        sha = _git(repo, "rev-parse", "HEAD").stdout.strip()
        assert checker._resolves_to_commit(repo, sha, require_reachable=True) is True

    def test_nonexistent_sha_fails_both_modes(self, repo_with_origin: tuple[Path, Path]) -> None:
        repo, _origin = repo_with_origin
        fake_sha = "0123456789abcdef0123456789abcdef01234567"
        assert checker._resolves_to_commit(repo, fake_sha, require_reachable=False) is False
        assert checker._resolves_to_commit(repo, fake_sha, require_reachable=True) is False
