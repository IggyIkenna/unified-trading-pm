"""Regression guard for the semver-agent baseline-resolution bounded-scan fix.

Incident 2026-06-09/10 — the spurious breaking-cascade fleet-lock class. The
semver-agent (`scripts/workflow-templates/semver-agent.yml.tmpl`) decides MINOR vs
breaking by scanning the commits SINCE the baseline version for a `feat!:` label
(and only consults the AST differ when no label says breaking). If the baseline
commit is resolved WRONG and the scan falls back to **all repo history**, it catches
an ancient `feat!:` → `BUMP=breaking` → `is_breaking=true` → a SPURIOUS staging-lock
cascade fleet-wide (the differ is skipped once the label says breaking).

Two real triggers, both fixed by BOUNDING the scan:
  1. baseline set by an admin `chore(version): align ... to X` message (not the
     standard `bump version to X`) → the message grep missed it → all-history.
     FIX: pickaxe the `version = "X"` string in pyproject.toml (message-agnostic).
  2. `BASELINE=0.0.0` (manifest `staging_versions` read 0.0.0/missing for a repo
     that HAS released — e.g. after a staging merge-sync) → the 0.0.0 branch scanned
     all history. FIX: bound to the most-recent release/version commit; only a
     GENUINE first release (no prior release commit at all) scans all history.

This test fails if either fix is reverted in the template (content guard), and
behaviorally proves the bounded resolution does NOT catch an ancient `feat!:` that
predates the baseline (which the old all-history scan did).
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

_PM_ROOT = Path(__file__).resolve().parents[2]
_TMPL = _PM_ROOT / "scripts" / "workflow-templates" / "semver-agent.yml.tmpl"


def _template_text() -> str:
    assert _TMPL.is_file(), f"semver-agent template missing at {_TMPL}"
    return _TMPL.read_text(encoding="utf-8")


# ── Content guard: the bounded-scan fix must remain in the template ──────────────


def test_else_branch_uses_pickaxe_baseline_resolution():
    """A non-zero baseline must be resolved by the message-AGNOSTIC pickaxe on the
    pyproject `version = "X"` string (HEAD-ancestry), not only a `bump version to`
    message grep that misses admin-set versions → all-history → spurious breaking."""
    text = _template_text()
    assert 'git log -1 --format=%H -S"version = \\"${BASELINE}\\""' in text, (
        "REGRESSION: the pickaxe baseline resolution (message-agnostic, HEAD-ancestry) is gone "
        "from semver-agent.yml.tmpl. Without it, an admin `chore(version): align ... to X` "
        "baseline falls back to scanning ALL history → ancient feat!: → spurious breaking-cascade."
    )
    # never `--all` (cross-branch) in the baseline resolution — HEAD-ancestry only
    assert "git log --oneline --all | grep -m1" not in text, (
        "REGRESSION: baseline resolution uses `git log --all` again — a cross-branch commit can "
        "poison the scan/differ base (the 2026-06-09 bug). Must be HEAD-ancestry."
    )


def test_zero_baseline_branch_is_bounded_not_all_history():
    """`BASELINE=0.0.0` must bound to the most-recent release/version commit; only a
    genuine first release (no prior release commit) may scan all history."""
    text = _template_text()
    # the 0.0.0 branch resolves a prior release/version commit before scanning
    assert 'grep -m1 -E "chore\\((release|version)\\):"' in text, (
        "REGRESSION: the BASELINE=0.0.0 branch no longer bounds its scan to the most-recent "
        "release/version commit. A spurious 0.0.0 (manifest staging_versions missing) will scan "
        "ALL history → ancient feat!: → spurious breaking-cascade (incident deployment-api=0.3.0)."
    )
    # the all-history fallback must be explicitly the genuine-first-release path
    assert "genuine first release" in text, (
        "REGRESSION: the all-history scan is no longer gated behind a 'genuine first release' "
        "guard. Unbounded all-history must ONLY run when there is no prior release commit at all."
    )


# ── Behavioral guard: the bounded resolution excludes a pre-baseline feat! ───────


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True, stderr=subprocess.DEVNULL).strip()


def _commit(cwd: Path, msg: str) -> None:
    (cwd / "marker").write_text(msg, encoding="utf-8")
    _git(cwd, "add", "marker")
    _git(cwd, "commit", "-q", "-m", msg)


def _resolve_bounded_baseline_sha(cwd: Path) -> str:
    """Faithful reference of the template's BASELINE=0.0.0 bounded resolver:
    the most-recent `chore(release|version):` commit reachable from HEAD."""
    out = _git(cwd, "log", "--oneline")
    for line in out.splitlines():
        if re.search(r"chore\((release|version)\):", line):
            return line.split()[0]
    return ""


@pytest.fixture()
def repo(tmp_path: Path) -> Path:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "t@t.t")
    _git(tmp_path, "config", "user.name", "t")
    # Ancient breaking feature BEFORE any release — the landmine the all-history scan hit.
    _commit(tmp_path, "feat!: removed the legacy adapter (ancient breaking change)")
    _commit(tmp_path, "feat: add some non-breaking feature")
    # Baseline set by an admin reconcile message (NOT 'bump version to') → version 0.2.0.
    _commit(tmp_path, "chore(version): reconcile source 0.1.1->0.2.0 to manifest")
    # Post-baseline chores only — nothing breaking.
    _commit(tmp_path, "chore(deps): pin unified-api-contracts to 0.3.0")
    _commit(tmp_path, "chore(release): bump version to 0.3.0")
    return tmp_path


def test_bounded_scan_excludes_pre_baseline_feat_bang(repo: Path):
    """With a spurious BASELINE=0.0.0, the bounded resolver scans only commits AFTER
    the most-recent release/version commit — so the ancient `feat!:` is NOT in range
    and the label scan would NOT classify breaking (the spurious lock is avoided).
    The old all-history scan WOULD have caught it."""
    base_sha = _resolve_bounded_baseline_sha(repo)
    assert base_sha, "fixture should have a release/version commit to bound to"
    bounded = _git(repo, "log", "--oneline", f"{base_sha}..HEAD")
    all_history = _git(repo, "log", "--oneline")

    feat_bang = re.compile(r"^[a-f0-9]+ [a-z]+!(\(.+\))?:|BREAKING CHANGE")
    bounded_breaking = any(feat_bang.search(ln) for ln in bounded.splitlines())
    all_history_breaking = any(feat_bang.search(ln) for ln in all_history.splitlines())

    assert all_history_breaking, "sanity: the OLD all-history scan catches the ancient feat!:"
    assert not bounded_breaking, (
        "REGRESSION: the bounded scan caught a feat!: that predates the baseline — the spurious "
        "breaking-cascade bug is back. Bounded COMMITS must start at the most-recent release commit."
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
