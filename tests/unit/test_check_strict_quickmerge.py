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


def test_already_on_main_not_flagged(repo: Path):
    # A trailer-less SOURCE commit (would normally be flagged) that is ALREADY reachable from
    # origin/main arrived via a backmerged promote-squash — exempt (provenance_gate_backmerge_
    # already_promoted_2026_06_24; the UTL 28072bc perpetual "Provenance gate BLOCKED").
    sha = _commit(repo, "src/bus.py", "x = 9\n", "promote(staging->main): catalog fix + peers (#472)")
    _git(repo, "update-ref", "refs/remotes/origin/main", sha)
    bad, why = csq.commit_violates(sha)
    assert bad is False
    assert "already promoted" in why


def test_already_on_staging_not_flagged(repo: Path):
    # Same exemption via the other promoted projection (a staging->LDR backmerged squash).
    sha = _commit(repo, "src/bus.py", "x = 10\n", "feat: shipped via staging")
    _git(repo, "update-ref", "refs/remotes/origin/staging", sha)
    bad, why = csq.commit_violates(sha)
    assert bad is False
    assert "already promoted" in why


def test_bypass_not_reachable_from_promoted_tip_still_flagged(repo: Path):
    # Fail-safe / true-positive guard: a trailer-less source commit on a SIDE branch that
    # origin/main does NOT contain is still flagged (the exemption fires only on a real
    # promoted-tip hit, never on a missing/non-reachable ref).
    base = _commit(repo, "README.md", "# base\n", "chore: base")
    _git(repo, "update-ref", "refs/remotes/origin/main", base)  # main is at `base`
    _git(repo, "checkout", "-q", "-b", "side")  # diverge — `bypass` will NOT be on origin/main
    bypass = _commit(repo, "src/bus.py", "x = 11\n", "fix: sneaky direct push")
    bad, why = csq.commit_violates(bypass)
    assert bad is True
    assert "source changed without quickmerge" in why


# ── Re-provenance: the self-service remedy for a MID-HISTORY bypass (2026-07-17) ──────────────────
# A trailer-less source commit that is not the branch tip cannot get a `Quickmerge:` trailer without
# rewriting shared history, and it deadlocks the promote it would ride. A later PROVENANCED commit
# that names it in a `Reprovenance: <sha>` trailer forgives it (created by reprovenance_bypass.sh
# after the dep-alignment gate). A bare (non-provenanced) Reprovenance commit must NOT forgive.


def _empty_commit(repo: Path, message: str, author: str | None = None) -> str:
    env = {"PATH": _path(), **_ENV}
    if author:
        env["GIT_AUTHOR_NAME"] = author
        env["GIT_COMMITTER_NAME"] = author
    subprocess.run(
        ["git", "commit", "-q", "--allow-empty", "-m", message], cwd=repo, env=env, check=True, capture_output=True
    )
    out = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, env={"PATH": _path()}, check=True, capture_output=True, text=True
    )
    return out.stdout.strip()


def _rng_shas(repo: Path, since: str) -> list[str]:
    out = subprocess.run(
        ["git", "rev-list", f"{since}..HEAD"],
        cwd=repo,
        env={"PATH": _path()},
        check=True,
        capture_output=True,
        text=True,
    )
    return [s for s in out.stdout.splitlines() if s.strip()]


def test_reprovenance_by_quickmerge_commit_forgives_midhistory_bypass(repo: Path):
    base = _commit(repo, "README.md", "# base\n", "chore: base")
    bypass = _commit(repo, "src/bus.py", "x = 1\n", "fix: direct-pushed sports fix")  # the bypass
    _commit(repo, "src/other.py", "y = 1\n", "feat: later\n\nQuickmerge: agent")  # unrelated later commit
    # Without a re-provenance commit, the bypass is flagged even though it is mid-history.
    reprov = csq._collect_reprovenanced(_rng_shas(repo, base))
    assert csq.commit_violates(bypass, reprov)[0] is True
    # A later PROVENANCED (Quickmerge:) commit that names the bypass forgives it.
    _empty_commit(repo, f"chore(provenance): re-provenance\n\nReprovenance: {bypass}\nQuickmerge: agent")
    reprov = csq._collect_reprovenanced(_rng_shas(repo, base))
    assert bypass in reprov
    bad, why = csq.commit_violates(bypass, reprov)
    assert bad is False
    assert "re-provenanced" in why


def test_reprovenance_matches_short_sha_prefix(repo: Path):
    base = _commit(repo, "README.md", "# base\n", "chore: base")
    bypass = _commit(repo, "src/bus.py", "x = 2\n", "fix: direct push")
    _empty_commit(repo, f"chore(provenance): bless\n\nReprovenance: {bypass[:8]}\nQuickmerge: agent")
    reprov = csq._collect_reprovenanced(_rng_shas(repo, base))
    assert bypass in reprov  # short-sha in the trailer still forgives the full-sha bypass


def test_bare_reprovenance_commit_cannot_self_forgive(repo: Path):
    # SECURITY: only a PROVENANCED commit may bless. A non-provenanced commit carrying a
    # Reprovenance: trailer must NOT forgive — else a bypasser could self-clear with an empty commit.
    base = _commit(repo, "README.md", "# base\n", "chore: base")
    bypass = _commit(repo, "src/bus.py", "x = 3\n", "fix: direct push")
    _empty_commit(repo, f"chore: sneaky self-forgive\n\nReprovenance: {bypass}")  # NO Quickmerge trailer
    reprov = csq._collect_reprovenanced(_rng_shas(repo, base))
    assert bypass not in reprov
    assert csq.commit_violates(bypass, reprov)[0] is True


def test_reprovenance_only_forgives_the_named_sha(repo: Path):
    # A blessing for sha A must not forgive an UNRELATED bypass B.
    base = _commit(repo, "README.md", "# base\n", "chore: base")
    bypass_a = _commit(repo, "src/a.py", "a = 1\n", "fix: A direct push")
    bypass_b = _commit(repo, "src/b.py", "b = 1\n", "fix: B direct push")
    _empty_commit(repo, f"chore(provenance): bless only A\n\nReprovenance: {bypass_a}\nQuickmerge: agent")
    reprov = csq._collect_reprovenanced(_rng_shas(repo, base))
    assert csq.commit_violates(bypass_a, reprov)[0] is False  # A forgiven
    assert csq.commit_violates(bypass_b, reprov)[0] is True  # B still flagged
