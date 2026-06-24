# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for the ETag conditional-request layer in promotion_lag_monitor.

The monitor compares ~25 repos x 4 directions every 20 min (~300 PAT calls/hr).
GitHub does NOT count a 304 against the rate limit, so an ETag cache (persisted
across CI runs via actions/cache) collapses unchanged-branch-pair compares to free
304s. These tests pin the parser + cache + the 304-reuses-cache behaviour.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import cast
from unittest.mock import patch

import promotion_lag_monitor as plm

_ETAG = 'W/"abc123"'


class _FakeProc:
    def __init__(self, stdout: str, returncode: int = 0) -> None:
        self.stdout = stdout
        self.returncode = returncode


def _resp_200(body: str) -> str:
    return f"HTTP/2.0 200 OK\r\nEtag: {_ETAG}\r\nContent-Type: application/json\r\n\r\n{body}"


_RESP_304 = f"HTTP/2.0 304 Not Modified\r\nEtag: {_ETAG}\r\n\r\n"


def setup_function() -> None:
    plm._ETAG_CACHE.clear()


# ── parser ────────────────────────────────────────────────────────────────────


def test_parse_200() -> None:
    status, etag, body = plm._parse_gh_api_i(_resp_200('{"commits": []}'))
    assert status == 200
    assert etag == _ETAG
    assert body is not None
    assert json.loads(body) == {"commits": []}


def test_parse_304() -> None:
    assert plm._parse_gh_api_i(_RESP_304) == (304, _ETAG, None)


def test_parse_garbage() -> None:
    assert plm._parse_gh_api_i("") == (None, None, None)
    assert plm._parse_gh_api_i("not http")[0] is None


# ── _gh_json conditional behaviour ────────────────────────────────────────────


def test_first_call_200_populates_cache() -> None:
    with patch.object(plm.subprocess, "run") as m:
        m.return_value = _FakeProc(_resp_200('{"commits": [1]}'))
        out = plm._gh_json("repos/o/r/compare/a...b")
    assert out == {"commits": [1]}
    assert plm._ETAG_CACHE["repos/o/r/compare/a...b"][0] == _ETAG
    sent = cast("list[str]", m.call_args[0][0])
    assert "-i" in sent and "If-None-Match" not in " ".join(sent)  # no conditional on first call


def test_304_reuses_cached_body_for_free() -> None:
    path = "repos/o/r/compare/a...b"
    plm._ETAG_CACHE[path] = (_ETAG, '{"commits": [1, 2]}')
    with patch.object(plm.subprocess, "run") as m:
        m.return_value = _FakeProc(_RESP_304, returncode=1)  # gh exits 1 on 304
        out = plm._gh_json(path)
    assert out == {"commits": [1, 2]}  # served from cache, no re-fetch cost
    sent = cast("list[str]", m.call_args[0][0])
    assert f"If-None-Match: {_ETAG}" in sent  # conditional request was sent


def test_non_200_returns_none() -> None:
    with patch.object(plm.subprocess, "run") as m:
        m.return_value = _FakeProc("HTTP/2.0 502 Bad Gateway\r\n\r\n", returncode=1)
        assert plm._gh_json("repos/o/r/compare/a...b") is None


# ── cache persistence ─────────────────────────────────────────────────────────


def test_cache_round_trip(tmp_path: Path) -> None:
    path = str(tmp_path / "etag.json")
    plm._ETAG_CACHE["k"] = (_ETAG, '{"x": 1}')
    plm.save_etag_cache(path)
    plm._ETAG_CACHE.clear()
    plm.load_etag_cache(path)
    assert plm._ETAG_CACHE["k"] == (_ETAG, '{"x": 1}')


def test_load_missing_is_noop(tmp_path: Path) -> None:
    plm.load_etag_cache(str(tmp_path / "nope.json"))
    assert plm._ETAG_CACHE == {}


# ── squash-skew content gate ────────────────────────────────────────────────────


def test_lag_suppressed_on_squash_skew() -> None:
    # A squash-merged repo stays ahead-by-commit-count of main even when content is byte-identical
    # (compare `files` is empty). The monitor MUST NOT page on the age of those phantom commits.
    now = dt.datetime(2026, 6, 15, 9, 0, tzinfo=dt.UTC)
    old = "2026-06-11T07:00:00Z"  # 4 days old → would breach a 60-min threshold if not gated
    skew = {
        "files": [],  # NET diff empty → content already promoted
        "commits": [{"commit": {"message": "feat: shipped", "author": {"date": old}}}],
    }
    with patch.object(plm, "_gh_json", return_value=skew):
        assert plm._lag("r", "main", "live-defi-rollout", now, 3600.0, skip_ci_counts=False) is None


def test_lag_fires_on_real_content() -> None:
    now = dt.datetime(2026, 6, 15, 9, 0, tzinfo=dt.UTC)
    old = "2026-06-11T07:00:00Z"
    real = {
        "files": [{"filename": "a.py"}],  # genuine unpromoted content
        "commits": [{"commit": {"message": "feat: shipped", "author": {"date": old}}}],
    }
    with patch.object(plm, "_gh_json", return_value=real):
        res = plm._lag("r", "main", "live-defi-rollout", now, 3600.0, skip_ci_counts=False)
    assert res is not None and res[0] == 1


# ── squash-WINDOW guard (forward LDR→staging only) ──────────────────────────────


def test_lag_suppressed_in_staging_drain_window() -> None:
    # files>0 (a fresh LDR commit not yet drained) but staging advanced within the threshold →
    # the Tier-C drain is live + the delta is the latest in-flight commit, NOT a stuck promotion.
    # The ancient `commits` entry is squash-skew; the guard must NOT page on its age.
    now = dt.datetime(2026, 6, 15, 9, 0, tzinfo=dt.UTC)
    ancient = "2026-06-11T07:00:00Z"  # squash-skew tail, 4 days old
    inflight = {
        "files": [{"filename": "a.py"}],  # genuine but transient in-flight delta
        "base_commit": {"commit": {"committer": {"date": "2026-06-15T08:50:00Z"}}},  # staging 10m ago
        "commits": [{"commit": {"message": "feat: shipped", "author": {"date": ancient}}}],
    }
    with patch.object(plm, "_gh_json", return_value=inflight):
        assert plm._lag("r", "staging", "live-defi-rollout", now, 3600.0, skip_ci_counts=False) is None


def test_lag_fires_on_stale_staging() -> None:
    # files>0 AND staging has NOT advanced within the threshold → the drain is genuinely wedged.
    now = dt.datetime(2026, 6, 15, 9, 0, tzinfo=dt.UTC)
    old = "2026-06-15T06:00:00Z"
    stuck = {
        "files": [{"filename": "a.py"}],
        "base_commit": {"commit": {"committer": {"date": "2026-06-15T05:00:00Z"}}},  # staging 4h stale
        "commits": [{"commit": {"message": "feat: shipped", "author": {"date": old}}}],
    }
    with patch.object(plm, "_gh_json", return_value=stuck):
        res = plm._lag("r", "staging", "live-defi-rollout", now, 3600.0, skip_ci_counts=False)
    assert res is not None and res[0] == 1


def test_staging_window_guard_does_not_apply_to_main() -> None:
    # main is also advanced by `[skip ci]` writes, so its HEAD recency is NOT a promotion signal —
    # the window guard is staging-only; a recent main HEAD must NOT suppress a real LDR→main lag.
    now = dt.datetime(2026, 6, 15, 9, 0, tzinfo=dt.UTC)
    old = "2026-06-11T07:00:00Z"
    real_main = {
        "files": [{"filename": "a.py"}],
        "base_commit": {"commit": {"committer": {"date": "2026-06-15T08:55:00Z"}}},  # main 5m ago (skip-ci write)
        "commits": [{"commit": {"message": "feat: shipped", "author": {"date": old}}}],
    }
    with patch.object(plm, "_gh_json", return_value=real_main):
        res = plm._lag("r", "main", "live-defi-rollout", now, 3600.0, skip_ci_counts=False)
    assert res is not None and res[0] == 1


# ── backmerge MERGE-commit exclusion (forward directions) ───────────────────────


def test_lag_excludes_backmerge_merge_commits() -> None:
    # A forward compare dominated by drift-tick backmerge MERGE-commits ("...into _backmerge",
    # parents>1) must NOT page on their ancient age — they're LDR-only, never forward-promotable.
    now = dt.datetime(2026, 6, 15, 9, 0, tzinfo=dt.UTC)
    only_backmerge = {
        "files": [{"filename": "a.py"}],  # squash-noise → non-empty net diff
        "commits": [
            {
                "commit": {
                    "message": "Merge remote-tracking branch 'origin/main' into _backmerge",
                    "author": {"date": "2026-06-01T00:00:00Z"},
                },
                "parents": [{"sha": "p1"}, {"sha": "p2"}],  # MERGE (2 parents)
            },
        ],
    }
    with patch.object(plm, "_gh_json", return_value=only_backmerge):
        assert plm._lag("r", "main", "live-defi-rollout", now, 3600.0, skip_ci_counts=False) is None


def test_lag_ages_only_non_merge_after_excluding_backmerge() -> None:
    # Ancient backmerge merge (excluded) + a 3h-old genuine forward commit → age is the 3h one,
    # NOT the ~14-day merge; n_commits counts only the non-merge.
    now = dt.datetime(2026, 6, 15, 9, 0, tzinfo=dt.UTC)
    mix = {
        "files": [{"filename": "a.py"}],
        "commits": [
            {
                "commit": {
                    "message": "Merge remote-tracking branch 'origin/main' into _backmerge",
                    "author": {"date": "2026-06-01T00:00:00Z"},
                },
                "parents": [{"sha": "p1"}, {"sha": "p2"}],  # ancient merge — excluded
            },
            {
                "commit": {"message": "feat: real forward content", "author": {"date": "2026-06-15T06:00:00Z"}},
                "parents": [{"sha": "q1"}],  # 3h-old non-merge — counted
            },
        ],
    }
    with patch.object(plm, "_gh_json", return_value=mix):
        res = plm._lag("r", "main", "live-defi-rollout", now, 3600.0, skip_ci_counts=False)
    assert res is not None and res[0] == 1  # only the non-merge counted
    assert 10000 < res[1] < 11000  # age ~3h (10800s), not ~14 days


def test_lag_counts_merge_in_backmerge_direction() -> None:
    # The merge-exclusion is forward-only; a backmerge-direction lag (skip_ci_counts=True) still
    # counts merge commits (a main commit not back-merged to LDR is real backmerge lag).
    now = dt.datetime(2026, 6, 15, 9, 0, tzinfo=dt.UTC)
    old_merge = {
        "files": [{"filename": "a.py"}],
        "commits": [
            {
                "commit": {"message": "Merge feature", "author": {"date": "2026-06-11T07:00:00Z"}},
                "parents": [{"sha": "p1"}, {"sha": "p2"}],
            },
        ],
    }
    with patch.object(plm, "_gh_json", return_value=old_merge):
        res = plm._lag("r", "live-defi-rollout", "main", now, 3600.0, skip_ci_counts=True)
    assert res is not None and res[0] == 1


# ── SSOT-consolidation guard (alert_quality_audit_2026_06_18) ───────────────────
# This monitor was reduced to a PURE branch-pair lag monitor: stuck/conflict-PR detection moved
# to ci-failure-watcher (the SSOT, which also auto-recovers + escalates), and dangling-staging-lock
# detection to sit-starvation-detector.yml — so one event no longer pages from three detectors.
# Pin that the stripped symbols are GONE so a future edit can't silently re-introduce the overlap.


def test_stuck_and_lock_detectors_removed():
    for sym in ("_stuck_prs", "_classify_stuck_pr", "_is_promotion_pr", "_lock_dangle", "_PROMOTION_BASES"):
        assert not hasattr(plm, sym), f"{sym} must stay removed (ci-failure-watcher / sit-starvation own these)"
