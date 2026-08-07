"""Hermetic unit tests for ci_failure_watcher.conflict_prs_to_escalate (item C).

The selector is a PURE function over (stuck PR dicts, already-escalated set) — no
network / no ``gh`` — so it tests the close-the-loop routing rules directly (SSOT),
not a replica. Covers: only CONFLICTING/DIRTY qualify (BLOCKED does not), the
idempotency set suppresses re-dispatch, and an empty input is a no-op.

Operator-approved 2026-06-02 (cicd_contract_hardening_2026_06_01.md § C).
"""

from __future__ import annotations

import importlib.util
import json as _json
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    """Load ci_failure_watcher with its sibling import stubbed (mirrors the classify test)."""
    repo_root = Path(__file__).resolve().parents[2]
    watcher_path = repo_root / "scripts" / "repo-management" / "ci_failure_watcher.py"

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
_select = MOD.conflict_prs_to_escalate  # type: ignore[attr-defined]


def _pr(repo: str, number: int, state: str) -> dict:
    return {
        "repo": repo,
        "number": number,
        "state": state,
        "head": "live-defi-rollout",
        "base": "staging",
        "age_min": 40,
    }


class TestConflictPrsToEscalate:
    def test_conflicting_and_dirty_qualify(self) -> None:
        stuck = [_pr("mtds", 1, "CONFLICTING"), _pr("deployment-service", 2, "DIRTY")]
        out = _select(stuck, already_escalated=set())
        assert {s["number"] for s in out} == {1, 2}

    def test_blocked_is_not_a_conflict(self) -> None:
        # BLOCKED is a gate/review wall, not a merge conflict — never auto-escalated.
        out = _select([_pr("mtds", 3, "BLOCKED")], already_escalated=set())
        assert out == []

    def test_already_escalated_is_suppressed(self) -> None:
        stuck = [_pr("mtds", 1, "CONFLICTING"), _pr("strategy-service", 4, "DIRTY")]
        out = _select(stuck, already_escalated={("mtds", 1)})
        assert {s["number"] for s in out} == {4}

    def test_empty_input_is_noop(self) -> None:
        assert _select([], already_escalated=set()) == []

    def test_mixed_states_only_conflicts(self) -> None:
        stuck = [
            _pr("a", 1, "CONFLICTING"),
            _pr("b", 2, "BLOCKED"),
            _pr("c", 3, "DIRTY"),
        ]
        out = _select(stuck, already_escalated=set())
        assert {s["number"] for s in out} == {1, 3}


# ── _pr_escalation_suppressed / _post_escalation_reason_marker (reason-scoped idempotency) ──────
#
# 2026-08-07 fix: batch-live-reconciliation-service#315 was correctly escalated+labelled
# `escalation-dispatched` for a RUNS_ON workflow-yaml bug (reason A), fixed — then became blocked
# again for an UNRELATED dead-glue-runner stuck-QUEUED reason (reason B), and the watcher stayed
# silent solely because the label was still present. These tests cover the fix directly: the
# label alone must no longer mean "suppressed forever" once a reason-signature marker exists and
# a NEW signature no longer matches it.


def _run_view_stub(*, labels: list[dict] | None = None, comments: list[dict] | None = None):
    """A fake `subprocess.run` that answers `gh pr view --json labels,comments` (and
    `--json comments`) with a fixed payload; raises on any other call shape (surfaces a wiring
    bug in the test itself rather than silently returning garbage)."""

    class _R:
        def __init__(self, stdout: str, returncode: int = 0, stderr: str = "") -> None:
            self.stdout = stdout
            self.returncode = returncode
            self.stderr = stderr

    def _run(cmd, *_args, **_kwargs):
        if cmd[:3] == ["gh", "pr", "view"] and "--json" in cmd:
            json_idx = cmd.index("--json")
            fields = cmd[json_idx + 1]
            body: dict = {}
            if "labels" in fields:
                body["labels"] = labels or []
            if "comments" in fields:
                body["comments"] = comments or []
            return _R(_json.dumps(body))
        raise AssertionError(f"unexpected call in _run_view_stub: {cmd}")

    return _run


LABEL = [{"name": "escalation-dispatched"}]


class TestPrEscalationSuppressed:
    def test_no_label_not_suppressed(self, monkeypatch) -> None:
        monkeypatch.setattr(MOD.subprocess, "run", _run_view_stub(labels=[], comments=[]))
        assert MOD._pr_escalation_suppressed("mtds", 1, "sigA") is False

    def test_label_with_no_reason_marker_is_grandfathered_suppressed(self, monkeypatch) -> None:
        """A PR labelled before this per-reason tracking existed (or via the label-only
        agent-runner.yml path) carries NO reason-marker comment — stays suppressed exactly as
        before, so shipping this fix does not itself cause a re-page storm."""
        monkeypatch.setattr(MOD.subprocess, "run", _run_view_stub(labels=LABEL, comments=[]))
        assert MOD._pr_escalation_suppressed("mtds", 1, "sigA") is True

    def test_label_with_matching_reason_marker_stays_suppressed(self, monkeypatch) -> None:
        marker = MOD._escalation_reason_marker("sigA")
        comments = [{"body": f"{marker}\nsome context"}]
        monkeypatch.setattr(MOD.subprocess, "run", _run_view_stub(labels=LABEL, comments=comments))
        assert MOD._pr_escalation_suppressed("mtds", 1, "sigA") is True

    def test_label_with_mismatched_reason_marker_re_arms(self, monkeypatch) -> None:
        """THE bug fix: escalated+labelled for reason A, now blocked for unrelated reason B — must
        NOT stay suppressed (batch-live-reconciliation-service#315)."""
        marker_a = MOD._escalation_reason_marker("sigA")
        comments = [{"body": f"{marker_a}\nescalated for reason A"}]
        monkeypatch.setattr(MOD.subprocess, "run", _run_view_stub(labels=LABEL, comments=comments))
        assert MOD._pr_escalation_suppressed("mtds", 1, "sigB") is False

    def test_gh_read_error_is_not_suppressed(self, monkeypatch) -> None:
        """Best-effort fail-open: an unreadable PR stays pageable/re-escalatable, never silently
        suppressed (mirrors the old label-presence check's convention)."""

        class _R:
            returncode = 1
            stdout = ""
            stderr = "boom"

        monkeypatch.setattr(MOD.subprocess, "run", lambda *_a, **_k: _R())
        assert MOD._pr_escalation_suppressed("mtds", 1, "sigA") is False


class TestPostEscalationReasonMarker:
    def test_posts_a_comment_when_no_marker_exists(self, monkeypatch) -> None:
        calls: list[list[str]] = []

        def _run(cmd, *_args, **_kwargs):
            calls.append(cmd)
            if cmd[:3] == ["gh", "pr", "view"]:
                return _run_view_stub(comments=[])(cmd)

            class _R:
                returncode = 0
                stdout = ""
                stderr = ""

            return _R()

        monkeypatch.setattr(MOD.subprocess, "run", _run)
        MOD._post_escalation_reason_marker("mtds", 1, "sigA")
        comment_calls = [c for c in calls if c[:3] == ["gh", "pr", "comment"]]
        assert len(comment_calls) == 1
        assert MOD._escalation_reason_marker("sigA") in " ".join(comment_calls[0])

    def test_deduped_when_marker_already_present(self, monkeypatch) -> None:
        """A PR parked in the 503/no-headroom retry loop is a dispatch candidate every */15 tick
        until a slot frees — must NOT get a fresh comment on every retry."""
        marker = MOD._escalation_reason_marker("sigA")
        calls: list[list[str]] = []

        def _run(cmd, *_args, **_kwargs):
            calls.append(cmd)
            if cmd[:3] == ["gh", "pr", "view"]:
                return _run_view_stub(comments=[{"body": marker}])(cmd)

            class _R:
                returncode = 0
                stdout = ""
                stderr = ""

            return _R()

        monkeypatch.setattr(MOD.subprocess, "run", _run)
        MOD._post_escalation_reason_marker("mtds", 1, "sigA")
        assert not [c for c in calls if c[:3] == ["gh", "pr", "comment"]]


class TestAlreadyEscalatedSetReasonScoped:
    """Integration-shaped coverage of `_already_escalated_set` (the IO wrapper `main()` actually
    calls to build `stuck_prs_to_page`'s idempotency set) — proves the fix end-to-end at the
    boundary the real silent-page bug lived at."""

    def test_pr_labelled_for_reason_a_pages_again_for_unrelated_reason_b(self, monkeypatch) -> None:
        marker_a = MOD._escalation_reason_marker("sigA")
        comments = [{"body": f"{marker_a}\nescalated for the original RUNS_ON bug"}]
        monkeypatch.setattr(MOD.subprocess, "run", _run_view_stub(labels=LABEL, comments=comments))
        stuck = [_pr("batch-live-reconciliation-service", 315, "BLOCKED") | {"blocking_signature": "sigB"}]
        already_escalated = MOD._already_escalated_set(stuck)
        assert already_escalated == set()  # NOT suppressed — must page again
        assert MOD.stuck_prs_to_page(stuck, already_escalated) == stuck

    def test_pr_labelled_for_the_same_reason_stays_suppressed(self, monkeypatch) -> None:
        marker_a = MOD._escalation_reason_marker("sigA")
        comments = [{"body": f"{marker_a}\nescalated for the original RUNS_ON bug"}]
        monkeypatch.setattr(MOD.subprocess, "run", _run_view_stub(labels=LABEL, comments=comments))
        stuck = [_pr("batch-live-reconciliation-service", 315, "BLOCKED") | {"blocking_signature": "sigA"}]
        already_escalated = MOD._already_escalated_set(stuck)
        assert already_escalated == {("batch-live-reconciliation-service", 315)}
        assert MOD.stuck_prs_to_page(stuck, already_escalated) == []
