"""Hermetic unit tests for ci_failure_watcher.auto_recover_stuck_prs (the "better fix").

``auto_recover_stuck_prs`` close+reopens the EXACT v2-never-reported deadlock signature
(BLOCKED + no failed check + v2 absent from the rollup) so it re-fires quality-gates-v2 with
no worker/orchestrator dependency. In ``dry_run`` it performs no ``gh`` calls and just returns
the selected set, so we test the gate directly (SSOT) — never touching a genuinely-failing PR
(v2 ran red → escalate instead), a v2-in-flight PR (no loop), or a non-promotion head.

Operator-requested 2026-06-09 ("is there not a better fix than escalating?").
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
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
_recover = MOD.auto_recover_stuck_prs  # type: ignore[attr-defined]


def _pr(
    number: int,
    *,
    state: str,
    failed_check: bool,
    v2_present: bool,
    v2_action_required: bool = False,
    head: str = "live-defi-rollout",
    head_message: str = "ci: real change",
    head_oid: str = "cafebabe",
) -> dict:
    return {
        "repo": "mtds",
        "number": number,
        "state": state,
        "failed_check": failed_check,
        "v2_present": v2_present,
        "v2_action_required": v2_action_required,
        "head": head,
        "base": "staging",
        "age_min": 40,
        "head_message": head_message,
        "head_oid": head_oid,
    }


class TestAutoRecoverStuckPrs:
    def test_v2_never_reported_deadlock_qualifies(self) -> None:
        # BLOCKED because the required check is MISSING (not failed), v2 absent → close+reopen.
        out = _recover([_pr(1, state="BLOCKED", failed_check=False, v2_present=False)], dry_run=True)
        assert {s["number"] for s in out} == {1}

    def test_v2_present_is_left_alone(self) -> None:
        # v2 is in the rollup (in-flight) — recovering would loop; do nothing.
        out = _recover([_pr(2, state="BLOCKED", failed_check=False, v2_present=True)], dry_run=True)
        assert out == []

    def test_genuine_failure_is_left_for_escalate(self) -> None:
        # A check actually ran red — close+reopen wouldn't fix it; escalate path owns this.
        out = _recover([_pr(3, state="BLOCKED", failed_check=True, v2_present=False)], dry_run=True)
        assert out == []

    def test_non_blocked_state_is_left_alone(self) -> None:
        out = _recover([_pr(4, state="CONFLICTING", failed_check=False, v2_present=False)], dry_run=True)
        assert out == []

    def test_non_promotion_head_is_left_alone(self) -> None:
        out = _recover([_pr(5, state="BLOCKED", failed_check=False, v2_present=False, head="feat/x")], dry_run=True)
        assert out == []

    def test_empty_input_is_noop(self) -> None:
        assert _recover([], dry_run=True) == []

    def test_skip_ci_head_still_qualifies(self) -> None:
        # A [skip ci] head is still the v2-absent deadlock signature → it must be recovered.
        out = _recover(
            [_pr(6, state="BLOCKED", failed_check=False, v2_present=False, head_message="pin x [skip ci]")],
            dry_run=True,
        )
        assert {s["number"] for s in out} == {6}

    def test_action_required_qualifies(self) -> None:
        # v2 PRESENT but concluded action_required (neither green nor red) → recoverable (2026-06-17).
        out = _recover(
            [_pr(12, state="BLOCKED", failed_check=False, v2_present=True, v2_action_required=True)],
            dry_run=True,
        )
        assert {s["number"] for s in out} == {12}

    def test_v2_present_without_action_required_still_left_alone(self) -> None:
        # v2 present + NOT action_required (in-flight / green-pending) → recovering would loop; skip.
        out = _recover(
            [_pr(13, state="BLOCKED", failed_check=False, v2_present=True, v2_action_required=False)],
            dry_run=True,
        )
        assert out == []


class TestAutoRecoverMechanism:
    """The recovery COMMAND must differ by head kind (2026-06-10, corrected same day).

    A CI-suppression-token head gets ZERO push/pull_request runs, close+reopen re-fires an
    equally-suppressed pull_request, and a workflow_dispatch run's check is NOT associated
    with the PR so its green does not satisfy the required check (verified live: 3x green
    dispatch runs on the exact head SHA, PR stayed BLOCKED). The only working lever is
    SUPERSEDING the head with an empty clean-message commit via the git-data API.
    """

    def _capture_gh_calls(self, monkeypatch, stuck: list[dict]) -> list[list[str]]:
        calls: list[list[str]] = []

        class _R:
            returncode = 0
            stderr = ""
            stdout = ""

        def _fake_run(cmd, *_args, **_kwargs):
            calls.append(cmd)
            r = _R()
            joined = " ".join(str(c) for c in cmd)
            if "git/commits/" in joined:  # GET head commit (tree lookup)
                r.stdout = '{"sha": "headsha", "tree": {"sha": "tree1"}, "message": "x"}'
            elif (
                joined.endswith("git/commits")
                or "git/commits -f" in joined
                or ("git/commits" in joined and "message=" in joined)
            ):  # POST create empty commit
                r.stdout = '{"sha": "newsha"}'
            elif "git/refs/heads/" in joined:  # PATCH advance branch ref
                r.stdout = '{"object": {"sha": "newsha"}}'
            return r

        monkeypatch.setattr(MOD.subprocess, "run", _fake_run)
        _recover(stuck, dry_run=False)
        return calls

    def test_skip_ci_head_superseded_by_empty_commit(self, monkeypatch) -> None:
        calls = self._capture_gh_calls(
            monkeypatch,
            [_pr(7, state="BLOCKED", failed_check=False, v2_present=False, head_message="pin y [skip ci]")],
        )
        joined = [" ".join(str(x) for x in c) for c in calls]
        # 1. read head commit tree, 2. create same-tree commit, 3. advance the branch ref.
        assert any("git/commits/cafebabe" in j for j in joined), joined
        assert any("message=" in j and "parents[]=cafebabe" in j for j in joined), joined
        assert any("git/refs/heads/live-defi-rollout" in j and "sha=newsha" in j for j in joined), joined
        # never close+reopen a suppressed head (futile) and never workflow_dispatch (doesn't count).
        assert not any(c[:3] == ["gh", "pr", "close"] for c in calls)
        assert not any(c[:3] == ["gh", "workflow", "run"] for c in calls)

    def test_ci_skip_marker_variant_also_superseded(self, monkeypatch) -> None:
        calls = self._capture_gh_calls(
            monkeypatch,
            [_pr(8, state="BLOCKED", failed_check=False, v2_present=False, head_message="release [ci skip]")],
        )
        assert any("git/refs/heads/" in " ".join(str(x) for x in c) for c in calls)

    def test_skip_token_mid_message_mention_also_superseded(self, monkeypatch) -> None:
        # The 2026-06-10 foot-gun: a recovery commit that merely MENTIONS the token in its
        # subject ("advance past [skip ci] bump head") is itself suppressed by GitHub.
        calls = self._capture_gh_calls(
            monkeypatch,
            [
                _pr(
                    10,
                    state="BLOCKED",
                    failed_check=False,
                    v2_present=False,
                    head_message="chore(ci): re-trigger v2 — advance past [skip ci] bump head",
                )
            ],
        )
        assert any("git/refs/heads/" in " ".join(str(x) for x in c) for c in calls)
        assert not any(c[:3] == ["gh", "pr", "close"] for c in calls)

    def test_recovery_marker_head_is_never_stacked(self, monkeypatch) -> None:
        # A head that IS our recovery commit must not get a second recovery on top.
        calls = self._capture_gh_calls(
            monkeypatch,
            [
                _pr(
                    11,
                    state="BLOCKED",
                    failed_check=False,
                    v2_present=False,
                    head_message="ci: re-fire quality-gates-v2 — supersede CI-suppressed head",
                )
            ],
        )
        assert calls == []

    def test_normal_head_still_close_reopen(self, monkeypatch) -> None:
        calls = self._capture_gh_calls(
            monkeypatch,
            [_pr(9, state="BLOCKED", failed_check=False, v2_present=False, head_message="feat: a real commit")],
        )
        assert [c[:3] for c in calls] == [["gh", "pr", "close"], ["gh", "pr", "reopen"]]
        assert not any("workflow" in c for c in calls)

    def test_action_required_head_close_reopen_and_marker(self, monkeypatch) -> None:
        # v2=action_required (present, not failed) → close+reopen to re-fire pull_request AND post the
        # bounding marker comment. Never the empty-commit supersede (that's the v2-absent skip-ci path).
        calls = self._capture_gh_calls(
            monkeypatch,
            [
                _pr(
                    14,
                    state="BLOCKED",
                    failed_check=False,
                    v2_present=True,
                    v2_action_required=True,
                    head_message="feat: real change",
                )
            ],
        )
        triples = [c[:3] for c in calls]
        assert ["gh", "pr", "close"] in triples
        assert ["gh", "pr", "reopen"] in triples
        assert ["gh", "pr", "comment"] in triples
        # marker comment body carries the hidden marker so the next tick is bounded
        assert any(MOD._ACTION_REQ_MARKER in " ".join(str(x) for x in c) for c in calls)
        assert not any("git/refs/heads/" in " ".join(str(x) for x in c) for c in calls)

    def test_action_required_bounded_when_recently_recovered(self, monkeypatch) -> None:
        # If a recent marker comment exists (within the window), do NOT close+reopen again (bound).
        calls: list[list[str]] = []

        class _R:
            returncode = 0
            stderr = ""
            stdout = ""

        def _fake_run(cmd, *_args, **_kwargs):
            calls.append(cmd)
            r = _R()
            if "--json" in cmd and "comments" in cmd and "view" in cmd:
                # a fresh marker comment exists → bounded
                r.stdout = '{"comments":[{"body":"' + MOD._ACTION_REQ_MARKER + '","createdAt":"2999-01-01T00:00:00Z"}]}'
            return r

        monkeypatch.setattr(MOD.subprocess, "run", _fake_run)
        _recover(
            [_pr(15, state="BLOCKED", failed_check=False, v2_present=True, v2_action_required=True)],
            dry_run=False,
        )
        # only the `pr view` comments query ran; no close/reopen/comment.
        assert not any(c[:3] == ["gh", "pr", "close"] for c in calls)
        assert not any(c[:3] == ["gh", "pr", "comment"] for c in calls)
