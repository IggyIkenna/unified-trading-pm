"""Unit tests for the pure decision logic in scripts/cicd/sit_gate_stuck_detector.py.

The detector's whole reason to exist (`issues/sit_validated_tree_treadmill_blocks_breaking_promotes_2026_07_20.md`
[DEVOPS] P3): a repo stuck on the SIT-gate treadmill is currently only visible as a
`promotion_lag_monitor.py` alert, which reads as generic slowness rather than a stuck gate with a
specific cause. These tests cover the "N consecutive SIT GATE BLOCK ticks" contract: the detector
must fire once a repo's most recent `threshold` ticks were ALL SIT-gate-blocked, and must stay
SILENT the moment a block→revalidate→PASS cycle completes (i.e. the newest tick is a pass), no
matter how long the prior block streak ran.
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "cicd" / "sit_gate_stuck_detector.py"
    spec = importlib.util.spec_from_file_location("sit_gate_stuck_detector", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SGD = _load_module()


# ── parse_blocked_repos ──────────────────────────────────────────────────────────────────────


def test_parse_blocked_repos_extracts_breaking_pending_line() -> None:
    log = (
        "promote-ldr-to-main\tPromote LDR → main\t2026-08-03T00:00:12.0000000Z "
        "SIT GATE BLOCK deployment-api: in breaking_pending — awaiting SIT-green on staging before LDR→main\n"
    )
    assert SGD.parse_blocked_repos(log) == {"deployment-api"}


def test_parse_blocked_repos_extracts_tree_mismatch_line() -> None:
    log = (
        "SIT GATE BLOCK market-tick-data-service: true-delta not SIT-validated on this tree "
        "(live ci_status='pending', sit_validated_tree='abc', LDR tree='def') — fail-CLOSED.\n"
    )
    assert SGD.parse_blocked_repos(log) == {"market-tick-data-service"}


def test_parse_blocked_repos_multiple_repos_in_one_log() -> None:
    log = "SIT GATE BLOCK repo-a: reason one\nSIT GATE BLOCK repo-b: reason two\n"
    assert SGD.parse_blocked_repos(log) == {"repo-a", "repo-b"}


def test_parse_blocked_repos_no_match_on_clean_tick() -> None:
    log = "SKIP repo-a: promotion_model='staging_main' (not ldr_main)\nPROMOTED repo-b\n"
    assert SGD.parse_blocked_repos(log) == set()


def test_parse_blocked_repos_empty_log() -> None:
    assert SGD.parse_blocked_repos("") == set()


# ── repo_streak ──────────────────────────────────────────────────────────────────────────────


def test_repo_streak_counts_consecutive_from_newest() -> None:
    # newest-first: blocked, blocked, blocked
    ticks = [{"repo-a"}, {"repo-a"}, {"repo-a"}]
    assert SGD.repo_streak(ticks, "repo-a") == 3


def test_repo_streak_stops_at_first_gap() -> None:
    # newest-first: blocked, blocked, NOT blocked, blocked
    ticks = [{"repo-a"}, {"repo-a"}, set(), {"repo-a"}]
    assert SGD.repo_streak(ticks, "repo-a") == 2


def test_repo_streak_zero_when_newest_tick_passes() -> None:
    # block→revalidate→PASS: newest tick (index 0) is a clean pass
    ticks = [set(), {"repo-a"}, {"repo-a"}]
    assert SGD.repo_streak(ticks, "repo-a") == 0


def test_repo_streak_zero_when_repo_never_blocked() -> None:
    ticks = [{"repo-b"}, {"repo-b"}]
    assert SGD.repo_streak(ticks, "repo-a") == 0


def test_repo_streak_empty_history() -> None:
    assert SGD.repo_streak([], "repo-a") == 0


# ── stuck_repos — the synthetic N-tick block + the block-revalidate-pass non-case ──────────────


def test_stuck_repos_fires_on_exact_threshold_streak() -> None:
    """The acceptance case: a synthetic N-tick (N=3) SIT-gate block on one repo must fire."""
    ticks = [{"repo-a"}, {"repo-a"}, {"repo-a"}]
    findings = SGD.stuck_repos(ticks, threshold=3)
    assert findings == {"repo-a": 3}


def test_stuck_repos_fires_on_longer_than_threshold_streak() -> None:
    ticks = [{"repo-a"} for _ in range(5)]
    findings = SGD.stuck_repos(ticks, threshold=3)
    assert findings == {"repo-a": 5}


def test_stuck_repos_silent_on_block_revalidate_pass_cycle() -> None:
    """The acceptance case: two SIT-gate blocks followed by a genuine pass must stay silent — the
    cycle completed, so this is not a standing treadmill, even though 2 blocks occurred."""
    # newest-first: PASS (revalidated clean), then two older blocked ticks.
    ticks = [set(), {"repo-a"}, {"repo-a"}]
    findings = SGD.stuck_repos(ticks, threshold=2)
    assert findings == {}


def test_stuck_repos_not_stuck_when_streak_shorter_than_threshold() -> None:
    ticks = [{"repo-a"}, {"repo-a"}, set(), {"repo-a"}]
    findings = SGD.stuck_repos(ticks, threshold=3)
    assert findings == {}


def test_stuck_repos_not_stuck_when_fewer_ticks_than_threshold_even_if_all_match() -> None:
    """Insufficient history must never be mistaken for a confirmed streak."""
    ticks = [{"repo-a"}, {"repo-a"}]
    findings = SGD.stuck_repos(ticks, threshold=3)
    assert findings == {}


def test_stuck_repos_not_stuck_on_healthy_fleet() -> None:
    ticks = [set(), set(), set()]
    assert SGD.stuck_repos(ticks, threshold=3) == {}


def test_stuck_repos_empty_history() -> None:
    assert SGD.stuck_repos([], threshold=3) == {}


def test_stuck_repos_tracks_multiple_repos_independently() -> None:
    ticks = [
        {"repo-a", "repo-b"},
        {"repo-a"},
        {"repo-a"},
    ]
    findings = SGD.stuck_repos(ticks, threshold=3)
    # repo-a blocked all 3 ticks -> stuck; repo-b only blocked the newest tick -> not stuck.
    assert findings == {"repo-a": 3}


# ── build_report ─────────────────────────────────────────────────────────────────────────────


def test_build_report_healthy_names_no_alert() -> None:
    report = SGD.build_report("IggyIkenna/unified-trading-pm", {}, threshold=3, newest_run_url=None)
    assert "healthy" in report
    assert "STUCK" not in report


def test_build_report_names_the_stuck_repo_and_streak_length() -> None:
    report = SGD.build_report("IggyIkenna/unified-trading-pm", {"deployment-api": 3}, threshold=3, newest_run_url=None)
    assert "STUCK" in report
    assert "deployment-api" in report
    assert "3 straight" in report


def test_build_report_names_multiple_stuck_repos() -> None:
    report = SGD.build_report(
        "IggyIkenna/unified-trading-pm",
        {"deployment-api": 3, "market-tick-data-service": 4},
        threshold=3,
        newest_run_url=None,
    )
    assert "deployment-api" in report
    assert "market-tick-data-service" in report


def test_build_report_includes_run_link_when_provided() -> None:
    report = SGD.build_report(
        "IggyIkenna/unified-trading-pm",
        {"deployment-api": 3},
        threshold=3,
        newest_run_url="https://github.com/IggyIkenna/unified-trading-pm/actions/runs/123",
    )
    assert "https://github.com/IggyIkenna/unified-trading-pm/actions/runs/123" in report
