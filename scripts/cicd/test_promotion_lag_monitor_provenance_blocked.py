# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for `_provenance_blocked()` in promotion_lag_monitor.

Closes the "done when" gap on `issues/promotion_lag_alert_hides_provenance_block_2026_07_17.md`'s
part (a): the branch-health PROVENANCE-BLOCKED reclassification (`_provenance_blocked()` +
its inline-remedy finding line in `main()`) was already implemented and live, but had no
regression test exercising it against a synthetic provenance-blocked PR — this file closes
that gap. Mocks `_gh_json` (the sole GitHub API touchpoint) so no network/token is needed.
"""

from __future__ import annotations

from typing import cast
from unittest.mock import patch

import promotion_lag_monitor as plm


def _pr(number: int, title: str) -> dict[str, object]:
    return {"number": number, "title": title}


def _comment(body: str) -> dict[str, object]:
    return {"body": body}


def test_no_open_promote_prs_returns_false() -> None:
    with patch.object(plm, "_gh_json", return_value=[]):
        assert plm._provenance_blocked("some-repo") is False


def test_gh_json_non_list_fails_closed_to_false() -> None:
    # A lookup failure (e.g. rate-limited/network error) must report the ordinary lag line,
    # never fabricate a block that may not exist.
    with patch.object(plm, "_gh_json", return_value=None):
        assert plm._provenance_blocked("some-repo") is False


def test_open_promote_pr_without_marker_comment_returns_false() -> None:
    prs = [_pr(42, "chore(promote): main <- live-defi-rollout")]
    comments = [_comment("looks good, merging shortly")]

    def _fake_gh_json(path: str) -> object:
        if "/pulls" in path:
            return prs
        if "/comments" in path:
            return comments
        raise AssertionError(f"unexpected path: {path}")

    with patch.object(plm, "_gh_json", side_effect=_fake_gh_json):
        assert plm._provenance_blocked("some-repo") is False


def test_open_promote_pr_with_marker_comment_returns_true() -> None:
    """The synthetic reproducer the todo's done-when calls for."""
    prs = [_pr(672, "chore(promote): main <- live-defi-rollout")]
    comments = [
        _comment("routine promote PR opened by the bot"),
        _comment(f"Auto-merge withheld.\n{plm._PROVENANCE_MARKER}\nSee provenance gate for detail."),
    ]

    def _fake_gh_json(path: str) -> object:
        if "/pulls" in path:
            return prs
        if "/comments" in path:
            return comments
        raise AssertionError(f"unexpected path: {path}")

    with patch.object(plm, "_gh_json", side_effect=_fake_gh_json):
        assert plm._provenance_blocked("market-tick-data-service") is True


def test_non_promote_titled_pr_is_skipped_even_with_marker_body() -> None:
    # Only PRs whose title starts with "chore(promote)" are the bot's own promote PRs;
    # an unrelated open PR must never be mistaken for a provenance block.
    prs = [_pr(1, "feat(cefi): unrelated feature PR")]

    def _fake_gh_json(path: str) -> object:
        if "/pulls" in path:
            return prs
        if "/comments" in path:
            raise AssertionError("must not fetch comments for a non-promote PR title")
        raise AssertionError(f"unexpected path: {path}")

    with patch.object(plm, "_gh_json", side_effect=_fake_gh_json):
        assert plm._provenance_blocked("some-repo") is False


def test_pr_number_not_int_is_skipped_defensively() -> None:
    prs = [cast("dict[str, object]", {"number": "not-an-int", "title": "chore(promote): x"})]
    with patch.object(plm, "_gh_json", return_value=prs):
        assert plm._provenance_blocked("some-repo") is False
