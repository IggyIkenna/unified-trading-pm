# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for `_promote_pr_cause()` / `_sit_fleet_status()` in promotion_lag_monitor.

Closes the "done when" gap on `issues/silent_failures_surfacing_as_generic_promotion_lag_2026_07_17.md`
P2: the lag alert must name a cause per LDR→main finding line (SIT-gated in-flight, no promote PR,
promote PR BLOCKED/CONFLICTING, or explicitly "cause unknown") instead of implying "just slow".
A synthetic case per named cause + a genuinely-unknown case, mirroring the sibling
`test_promotion_lag_monitor_provenance_blocked.py`'s mock-`_gh_json` style (no network/token needed).
"""

from __future__ import annotations

from unittest.mock import patch

import promotion_lag_monitor as plm


def _pr(number: int, mergeable_state: str, sha: str = "abc123") -> dict[str, object]:
    return {"number": number, "mergeable_state": mergeable_state, "head": {"sha": sha}}


def test_no_open_promote_pr_is_no_promote_pr_cause() -> None:
    cause, pr_num = plm._promote_pr_cause("some-repo", None)
    assert (cause, pr_num) == ("no_promote_pr", None)


def test_dirty_mergeable_state_is_blocked_conflicting() -> None:
    pr = _pr(101, "dirty")
    cause, pr_num = plm._promote_pr_cause("some-repo", pr)
    assert (cause, pr_num) == ("blocked_conflicting", 101)


def test_blocked_mergeable_state_is_blocked_conflicting() -> None:
    pr = _pr(102, "blocked")
    cause, pr_num = plm._promote_pr_cause("some-repo", pr)
    assert (cause, pr_num) == ("blocked_conflicting", 102)


def test_pending_sit_fleet_status_is_sit_gated_inflight() -> None:
    """The synthetic reproducer for cause (a): promote PR clean, SIT status still pending."""
    pr = _pr(103, "clean", sha="deadbeef")
    with patch.object(plm, "_sit_fleet_status", return_value="pending") as mocked:
        cause, pr_num = plm._promote_pr_cause("some-repo", pr)
    mocked.assert_called_once_with("some-repo", "deadbeef")
    assert (cause, pr_num) == ("sit_gated_inflight", 103)


def test_clean_pr_no_sit_status_is_unknown() -> None:
    """A genuinely-unknown cause must say so explicitly, never silently fall back."""
    pr = _pr(104, "clean")
    with patch.object(plm, "_sit_fleet_status", return_value=None):
        cause, pr_num = plm._promote_pr_cause("some-repo", pr)
    assert (cause, pr_num) == ("unknown", 104)


def test_success_sit_fleet_status_is_unknown_not_inflight() -> None:
    # A resolved (success/failure/error) SIT status is not "in-flight" — only "pending" is.
    pr = _pr(105, "clean")
    with patch.object(plm, "_sit_fleet_status", return_value="success"):
        cause, pr_num = plm._promote_pr_cause("some-repo", pr)
    assert (cause, pr_num) == ("unknown", 105)


def test_pr_number_not_int_is_reported_as_none() -> None:
    pr: dict[str, object] = {"number": "not-an-int", "mergeable_state": "clean", "head": {}}
    with patch.object(plm, "_sit_fleet_status", return_value=None):
        cause, pr_num = plm._promote_pr_cause("some-repo", pr)
    assert (cause, pr_num) == ("unknown", None)


def test_sit_fleet_status_matches_context_and_returns_state() -> None:
    statuses = {
        "statuses": [
            {"context": "some-other-check", "state": "success"},
            {"context": plm._SIT_FLEET_CONTEXT, "state": "pending"},
        ]
    }
    with patch.object(plm, "_gh_json", return_value=statuses):
        assert plm._sit_fleet_status("some-repo", "deadbeef") == "pending"


def test_sit_fleet_status_absent_context_returns_none() -> None:
    with patch.object(plm, "_gh_json", return_value={"statuses": []}):
        assert plm._sit_fleet_status("some-repo", "deadbeef") is None


def test_sit_fleet_status_lookup_failure_returns_none() -> None:
    with patch.object(plm, "_gh_json", return_value=None):
        assert plm._sit_fleet_status("some-repo", "deadbeef") is None


def test_open_promote_pr_returns_first_chore_promote_titled_pr() -> None:
    prs = [
        {"number": 1, "title": "feat(cefi): unrelated"},
        {"number": 2, "title": "chore(promote): main <- live-defi-rollout"},
    ]
    with patch.object(plm, "_gh_json", return_value=prs):
        pr = plm._open_promote_pr("some-repo")
    assert pr is not None
    assert pr["number"] == 2


def test_open_promote_pr_none_when_no_match() -> None:
    prs = [{"number": 1, "title": "feat(cefi): unrelated"}]
    with patch.object(plm, "_gh_json", return_value=prs):
        assert plm._open_promote_pr("some-repo") is None


def test_open_promote_pr_none_on_lookup_failure() -> None:
    with patch.object(plm, "_gh_json", return_value=None):
        assert plm._open_promote_pr("some-repo") is None


# ── Hydration: the gap that made `blocked_conflicting` dead code (2026-08-10) ────────────────────
# Every test above hand-builds the PR dict WITH `mergeable_state`, so they all passed while the
# production path could never reach the branch they cover: `_open_promote_pr` read the PR *list*
# endpoint, which GitHub does not populate with `mergeable`/`mergeable_state`. Result — a genuinely
# BLOCKED promote PR reported "cause unknown — investigate directly" forever (market-tick-data-
# service #939, measured 248m lag / 14 commits). These exercise the REAL call path instead.

_LIST_URL_MARK = "pulls?state=open"


def _listed_pr(number: int) -> dict[str, object]:
    """Exactly what the LIST endpoint returns: note the absent `mergeable_state`."""
    return {"number": number, "title": "chore(promote): LDR → main (Option-B direct)", "head": {"sha": "abc123"}}


def test_open_promote_pr_hydrates_mergeable_state_via_single_pr_get() -> None:
    def _fake(path: str) -> object:
        if _LIST_URL_MARK in path:
            return [_listed_pr(939)]
        return {**_listed_pr(939), "mergeable": True, "mergeable_state": "blocked"}

    with patch.object(plm, "_gh_json", side_effect=_fake):
        pr = plm._open_promote_pr("market-tick-data-service")
    assert pr is not None
    # The whole point: the field the classifier keys on must survive the lookup.
    assert pr.get("mergeable_state") == "blocked"


def test_listed_pr_alone_cannot_classify_but_hydrated_one_does() -> None:
    """The end-to-end guard. Feeding `_promote_pr_cause` the raw LIST shape yields "unknown" — the
    exact production bug. Routing the same PR through `_open_promote_pr` must yield the actionable
    cause. If hydration is ever removed, this fails while every hand-built test above still passes.
    """
    with patch.object(plm, "_sit_fleet_status", return_value=None):
        raw_cause, _ = plm._promote_pr_cause("market-tick-data-service", _listed_pr(939))
    assert raw_cause == "unknown", "list-shaped PR is exactly what used to reach the classifier"

    def _fake(path: str) -> object:
        if _LIST_URL_MARK in path:
            return [_listed_pr(939)]
        return {**_listed_pr(939), "mergeable": True, "mergeable_state": "blocked"}

    with patch.object(plm, "_gh_json", side_effect=_fake):
        hydrated = plm._open_promote_pr("market-tick-data-service")
    cause, pr_num = plm._promote_pr_cause("market-tick-data-service", hydrated)
    assert (cause, pr_num) == ("blocked_conflicting", 939)


def test_open_promote_pr_falls_back_to_list_entry_when_hydration_fails() -> None:
    """A failed single-PR GET must never lose the PR — degrade to today's behaviour, not worse."""

    def _fake(path: str) -> object:
        return [_listed_pr(939)] if _LIST_URL_MARK in path else None

    with patch.object(plm, "_gh_json", side_effect=_fake):
        pr = plm._open_promote_pr("market-tick-data-service")
    assert pr is not None
    assert pr["number"] == 939


def test_open_promote_pr_hydration_skipped_when_number_is_not_an_int() -> None:
    """Malformed listing must not fabricate a `pulls/None` request."""
    calls: list[str] = []

    def _fake(path: str) -> object:
        calls.append(path)
        return [{"number": "nope", "title": "chore(promote): x"}] if _LIST_URL_MARK in path else None

    with patch.object(plm, "_gh_json", side_effect=_fake):
        pr = plm._open_promote_pr("some-repo")
    assert pr is not None
    assert len(calls) == 1, f"expected only the list call, got {calls}"


def test_mergeable_state_unknown_does_not_claim_blocked() -> None:
    # GitHub computes mergeability asynchronously; a cold PR answers "unknown". That must fall
    # through to the existing dispatch, not be reported as BLOCKED.
    pr = _pr(940, "unknown")
    with patch.object(plm, "_sit_fleet_status", return_value=None):
        cause, _ = plm._promote_pr_cause("some-repo", pr)
    assert cause == "unknown"
