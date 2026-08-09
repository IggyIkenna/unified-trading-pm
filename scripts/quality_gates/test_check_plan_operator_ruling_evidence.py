# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_plan_operator_ruling_evidence.py.

Focus: the --only pre-existing-debt exemption
(plan_hygiene_ratchet_regressions_outpace_serial_ci_fix_velocity_2026_08_09.md "New facet") —
an unsourced 'operator ruling' citation already present at HEAD must not block an unrelated
commit touching the same file; a brand-new one still must.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

import check_plan_operator_ruling_evidence as checker


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def git_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A real, tiny git repo so _violations_at_head's `git show HEAD:<path>` has something
    genuine to read — this logic is git-integration behavior, not worth mocking away."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "test")
    monkeypatch.setattr(checker, "_PM_ROOT", repo)
    return repo


def _commit(repo: Path, rel_path: str, content: str, message: str = "commit") -> None:
    p = repo / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    _git(repo, "add", rel_path)
    _git(repo, "commit", "-q", "-m", message)


_UNSOURCED_TODO = """- [x] [DATA] P2. Done via operator ruling, no doc cited here at all.
"""

_SOURCED_TODO = """- [x] [DATA] P2. Done via operator ruling, see plans/active/foo_2026_08_01.md for the record.
"""

_UNSOURCED_TODO_V2 = """- [x] [DATA] P2. Done via operator ruling, no doc cited here at all (edited).
"""


def test_violations_for_text_flags_unsourced_todo() -> None:
    violations = checker._violations_for_text(_UNSOURCED_TODO, Path("x.md"))
    assert len(violations) == 1
    assert violations[0].citation.source == "todo"


def test_violations_for_text_clean_when_sourced() -> None:
    assert checker._violations_for_text(_SOURCED_TODO, Path("x.md")) == []


def test_violations_at_head_empty_for_file_absent_from_head(git_repo: Path) -> None:
    p = git_repo / "plans" / "active" / "issues" / "new.md"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_UNSOURCED_TODO, encoding="utf-8")
    assert checker._violations_at_head(p) == []


def test_run_only_skips_violation_already_at_head(git_repo: Path, capsys: pytest.CaptureFixture[str]) -> None:
    rel = "plans/active/issues/existing.md"
    _commit(git_repo, rel, _UNSOURCED_TODO, "seed: pre-existing unsourced citation")
    # Working tree unchanged since HEAD -- same violation, already known.
    rc = checker._run_only([str(git_repo / rel)], quiet=True)
    assert rc == 0


def test_run_only_flags_brand_new_file(git_repo: Path) -> None:
    rel = "plans/active/issues/brand_new.md"
    p = git_repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(_UNSOURCED_TODO, encoding="utf-8")
    # Never committed -- absent from HEAD entirely.
    rc = checker._run_only([str(p)], quiet=True)
    assert rc == 1


def test_run_only_flags_new_citation_added_to_existing_file(git_repo: Path) -> None:
    rel = "plans/active/issues/existing.md"
    _commit(git_repo, rel, _SOURCED_TODO, "seed: clean file")
    # Working tree now introduces a fresh unsourced citation not present at HEAD.
    p = git_repo / rel
    p.write_text(_SOURCED_TODO + "\n" + _UNSOURCED_TODO, encoding="utf-8")
    rc = checker._run_only([str(p)], quiet=True)
    assert rc == 1


def test_run_only_flags_edited_citation_that_changes_context(git_repo: Path) -> None:
    """An edit to the citation text itself re-earns scrutiny rather than staying
    grandfathered forever purely because SOME unsourced citation existed at HEAD."""
    rel = "plans/active/issues/existing.md"
    _commit(git_repo, rel, _UNSOURCED_TODO, "seed: pre-existing unsourced citation")
    p = git_repo / rel
    p.write_text(_UNSOURCED_TODO_V2, encoding="utf-8")
    rc = checker._run_only([str(p)], quiet=True)
    assert rc == 1


def test_run_only_clean_when_no_violations_at_all(git_repo: Path) -> None:
    rel = "plans/active/issues/clean.md"
    _commit(git_repo, rel, _SOURCED_TODO, "seed: clean file")
    rc = checker._run_only([str(git_repo / rel)], quiet=True)
    assert rc == 0


def test_violation_identity_matches_on_phrase_and_context() -> None:
    v = checker._violations_for_text(_UNSOURCED_TODO, Path("x.md"))[0]
    same = checker._violations_for_text(_UNSOURCED_TODO, Path("y.md"))[0]
    assert checker._violation_identity(v) == checker._violation_identity(same)
