"""Unit tests for ci_failure_watcher._classify_commit_data (push-author attribution).

Operator-approved 2026-06-02 (cicd_contract_hardening_2026_06_01.md line ~264).

Three cases:
    1. human       — author name in {IggyIkenna, CosmicTrader}, no Co-Authored-By trailer
    2. background-agent — commit message contains "Co-Authored-By: Claude"
    3. automation  — committer is "github-actions[bot]" or "GitHub"

The helper is a pure function over (author, committer, message) so tests run without
any network calls or subprocess invocations.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock


def _load_module() -> types.ModuleType:
    """Load ci_failure_watcher without executing its module-level side-effects.

    The module does `from pin_branch_protection_rulesets import ORG, REPOS` at the top
    level.  We stub that dependency so the test does not require the sibling module to
    be importable from the test runner's working directory.
    """
    repo_root = Path(__file__).resolve().parents[2]
    watcher_path = repo_root / "scripts" / "repo-management" / "ci_failure_watcher.py"

    # Provide a stub for the sibling module so the import doesn't fail.
    stub = types.ModuleType("pin_branch_protection_rulesets")
    stub.ORG = "IggyIkenna"  # type: ignore[attr-defined]
    stub.REPOS = []  # type: ignore[attr-defined]
    sys.modules.setdefault("pin_branch_protection_rulesets", stub)

    spec = importlib.util.spec_from_file_location("ci_failure_watcher", watcher_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()

# The pure classifier function
_classify = MOD._classify_commit_data  # type: ignore[attr-defined]


# ── Test cases ────────────────────────────────────────────────────────────────


class TestClassifyCommitData:
    """Tests for the pure _classify_commit_data(author, committer, message) function."""

    # Case 1 — human operator push
    def test_human_iggyikenna(self) -> None:
        name, role = _classify(
            author="IggyIkenna",
            committer="IggyIkenna",
            message="feat: add attribution to CI alerts\n\nShort body.",
        )
        assert role == "human"
        assert name == "IggyIkenna"

    def test_human_cosmictrader(self) -> None:
        name, role = _classify(
            author="CosmicTrader",
            committer="CosmicTrader",
            message="fix: some fix",
        )
        assert role == "human"
        assert name == "CosmicTrader"

    def test_human_case_insensitive(self) -> None:
        # Names are stored as-is but matched case-insensitively
        _name, role = _classify(
            author="iggyikenna",
            committer="iggyikenna",
            message="chore: something",
        )
        assert role == "human"

    # Case 2 — background-agent push (Co-Authored-By: Claude trailer)
    def test_background_agent_co_authored_by_claude(self) -> None:
        name, role = _classify(
            author="IggyIkenna",
            committer="IggyIkenna",
            message=(
                "feat: implement classifier\n\nCo-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
            ),
        )
        assert role == "background-agent"
        assert name == "IggyIkenna"

    def test_background_agent_trailer_case_insensitive(self) -> None:
        """'co-authored-by: claude' match is case-insensitive."""
        _name, role = _classify(
            author="orch-worker-vm1",
            committer="orch-worker-vm1",
            message="fix: something\n\nco-authored-by: Claude Sonnet <noreply@anthropic.com>",
        )
        assert role == "background-agent"

    def test_background_agent_unknown_author_with_trailer(self) -> None:
        """Agent co-authored commit from a non-human-named author still classifies as background-agent."""
        name, role = _classify(
            author="slot-3-worker",
            committer="slot-3-worker",
            message="chore: flip plan checkbox\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>",
        )
        assert role == "background-agent"
        assert name == "slot-3-worker"

    # Case 3 — automation (GHA / semver-agent merge commits)
    def test_automation_github_actions_bot(self) -> None:
        _name, role = _classify(
            author="github-actions[bot]",
            committer="github-actions[bot]",
            message="ci: bump version to 1.2.3 [skip ci]",
        )
        assert role == "automation"

    def test_automation_github_committer(self) -> None:
        name, role = _classify(
            author="IggyIkenna",
            committer="GitHub",
            message="Merge pull request #42 from IggyIkenna/feat/x",
        )
        assert role == "automation"
        # author name is preserved even though committer is GitHub
        assert name == "IggyIkenna"

    def test_automation_committer_case_insensitive(self) -> None:
        _name, role = _classify(
            author="some-bot",
            committer="github-actions[bot]",
            message="automated release",
        )
        assert role == "automation"

    # Edge cases
    def test_unknown_author_no_trailer(self) -> None:
        name, role = _classify(
            author="external-contributor",
            committer="external-contributor",
            message="fix: typo",
        )
        assert role == "unknown"
        assert name == "external-contributor"

    def test_empty_author_returns_unknown(self) -> None:
        name, role = _classify(author="", committer="", message="")
        assert role == "unknown"
        assert name == "unknown"

    def test_automation_takes_priority_over_co_authored_by(self) -> None:
        """Automation committer wins even if message has a Claude trailer."""
        _, role = _classify(
            author="github-actions[bot]",
            committer="github-actions[bot]",
            message="ci: auto-merge\n\nCo-Authored-By: Claude Haiku <noreply@anthropic.com>",
        )
        assert role == "automation"
