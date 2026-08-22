# Epic: ci_master
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
import pytest

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


# ── _gh_json mock ───────────────────────────────────────────────────────────────
# _lag makes TWO kinds of call now: the `compare/base...head` (net diff + window) and, per
# net-changed file, a `commits?sha=&path=` LAST-TOUCH lookup — the content-delta age that
# replaced the squash-ghost window aging. Dispatch on the path so each returns its own shape.


def _touch(date: str, msg: str = "feat: shipped", sha: str = "s1", parents: int = 1) -> dict:
    """One `commits?path=` entry — the commit that last touched a file."""
    return {
        "sha": sha,
        "commit": {"message": msg, "author": {"date": date}},
        "parents": [{"sha": f"p{i}"} for i in range(parents)],
    }


def _gh(compare: dict, touches: list | None = None):
    """side_effect for _gh_json: compare path → `compare`; last-touch path → `touches`."""

    def _dispatch(path: str):
        if "/compare/" in path:
            return compare
        if "/commits?" in path:
            return touches if touches is not None else []
        return None

    return _dispatch


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
    with patch.object(plm, "_gh_json", side_effect=_gh(real, [_touch(old)])):
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
    with patch.object(plm, "_gh_json", side_effect=_gh(stuck, [_touch(old)])):
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
    with patch.object(plm, "_gh_json", side_effect=_gh(real_main, [_touch(old)])):
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
    backmerge_touch = [
        _touch("2026-06-01T00:00:00Z", msg="Merge remote-tracking branch 'origin/main' into _backmerge", parents=2)
    ]
    with patch.object(plm, "_gh_json", side_effect=_gh(only_backmerge, backmerge_touch)):
        assert plm._lag("r", "main", "live-defi-rollout", now, 3600.0, skip_ci_counts=False) is None


def test_lag_ages_only_non_merge_after_excluding_backmerge() -> None:
    # The ancient backmerge merge in `commits` is squash-skew noise. Age comes from the file's
    # LAST-TOUCH (a 3h-old genuine forward commit), NOT the ~14-day window tail.
    now = dt.datetime(2026, 6, 15, 9, 0, tzinfo=dt.UTC)
    mix = {
        "files": [{"filename": "a.py"}],
        "commits": [
            {
                "commit": {
                    "message": "Merge remote-tracking branch 'origin/main' into _backmerge",
                    "author": {"date": "2026-06-01T00:00:00Z"},
                },
                "parents": [{"sha": "p1"}, {"sha": "p2"}],  # ancient merge — never aged over
            },
            {
                "commit": {"message": "feat: real forward content", "author": {"date": "2026-06-15T06:00:00Z"}},
                "parents": [{"sha": "q1"}],  # 3h-old non-merge — the real delta
            },
        ],
    }
    touches = [_touch("2026-06-15T06:00:00Z", msg="feat: real forward content", sha="q0")]
    with patch.object(plm, "_gh_json", side_effect=_gh(mix, touches)):
        res = plm._lag("r", "main", "live-defi-rollout", now, 3600.0, skip_ci_counts=False)
    assert res is not None and res[0] == 1  # only the real delta counted
    assert 10000 < res[1] < 11000  # age ~3h (10800s), not ~14 days


def test_lag_age_ignores_squash_ghost_window_entirely() -> None:
    """The 2026-07-16 regression, pinned: a 20-day squash ghost must not set the age.

    unified-trading-library reported "144 commit(s), oldest 28403m old" while its real net diff
    was last touched 25 MINUTES earlier — the age came from a ghost the squash never replayed, so
    it could never fall under the threshold and the pair paged forever. Age MUST come from the
    file's last-touch, so a fresh delta under a huge ghost window reports NO lag.
    """
    now = dt.datetime(2026, 6, 15, 9, 0, tzinfo=dt.UTC)
    ghosty = {
        "files": [{"filename": "a.py"}],  # real content, but freshly pushed
        "commits": [  # a 20-day squash-ghost tail that will never get younger
            {"commit": {"message": "feat: long promoted", "author": {"date": "2026-05-26T09:00:00Z"}}, "parents": [{}]},
        ],
    }
    fresh = [_touch("2026-06-15T08:35:00Z", msg="feat: just pushed")]  # 25m old
    with patch.object(plm, "_gh_json", side_effect=_gh(ghosty, fresh)):
        assert plm._lag("r", "main", "live-defi-rollout", now, 3600.0, skip_ci_counts=False) is None


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
    merge_touch = [_touch("2026-06-11T07:00:00Z", msg="Merge feature", parents=2)]
    with patch.object(plm, "_gh_json", side_effect=_gh(old_merge, merge_touch)):
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


# ── _main_direct_repos + staging-direction skip (WS-L cutover: staging toggled off) ──────────────


def test_main_direct_repos_includes_pm_and_ldr_main(tmp_path: Path) -> None:
    """PM is always main-direct; ldr_main repos are added; pyproject/other repos are excluded."""
    manifest = {
        "repositories": {
            "unified-trading-pm": {"promotion_model": "ldr_main"},
            "greeks-service": {"promotion_model": "ldr_main"},
            "e2e-testing": {"promotion_model": "staging"},
            "no-field-repo": {},
        }
    }
    mpath = tmp_path / "workspace-manifest.json"
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    md = plm._main_direct_repos(manifest_path=str(mpath))
    assert "unified-trading-pm" in md  # always main-direct (Option-B)
    assert "greeks-service" in md  # ldr_main → main-direct
    assert "e2e-testing" not in md  # staging promotion_model → still uses staging
    assert "no-field-repo" not in md  # no promotion_model → not main-direct


def test_main_direct_repos_pm_only_on_unreadable_manifest(tmp_path: Path) -> None:
    """Manifest unreadable → fall back to PM-only (prior behavior), never crash."""
    md = plm._main_direct_repos(manifest_path=str(tmp_path / "does-not-exist.json"))
    assert md == {"unified-trading-pm"}


def test_main_direct_repos_staging_dormant_toggle_includes_all(tmp_path: Path) -> None:
    """WS-L staging-dormant toggle: top-level staging_dormant_mode=true → EVERY repo is main-direct
    (staging dormant fleet-wide), so the lag monitor + Slack skip every staging direction."""
    manifest = {
        "staging_dormant_mode": True,
        "repositories": {
            "unified-trading-pm": {"promotion_model": "ldr_main"},
            "e2e-testing": {"promotion_model": "staging"},  # would normally NOT be main-direct
            "no-field-repo": {},
        },
    }
    mpath = tmp_path / "workspace-manifest.json"
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    md = plm._main_direct_repos(manifest_path=str(mpath))
    assert "e2e-testing" in md  # dormant toggle overrides per-repo promotion_model
    assert "no-field-repo" in md  # dormant toggle includes even no-field repos
    # toggle OFF → only PM + ldr_main (reversible)
    manifest["staging_dormant_mode"] = False
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    md_off = plm._main_direct_repos(manifest_path=str(mpath))
    assert "e2e-testing" not in md_off
    assert "no-field-repo" not in md_off


# ── _single_branch_repos (unified-trading-ci: no LDR/staging pipeline at all) ────────────────────


def test_single_branch_repos_includes_flagged_repo_only(tmp_path: Path) -> None:
    manifest = {
        "repositories": {
            "unified-trading-ci": {"promotion_model": "single_branch"},
            "greeks-service": {"promotion_model": "ldr_main"},
            "no-field-repo": {},
        }
    }
    mpath = tmp_path / "workspace-manifest.json"
    mpath.write_text(json.dumps(manifest), encoding="utf-8")
    sb = plm._single_branch_repos(manifest_path=str(mpath))
    assert sb == {"unified-trading-ci"}


def test_single_branch_repos_empty_on_unreadable_manifest(tmp_path: Path) -> None:
    """Manifest unreadable → fall back to empty (no exemption), never crash."""
    sb = plm._single_branch_repos(manifest_path=str(tmp_path / "does-not-exist.json"))
    assert sb == set()


def test_single_branch_repo_skipped_entirely_in_main_loop(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """A single_branch repo must produce NO entries in repo_lags at all — not one direction skipped,
    the WHOLE repo — so it can never appear in the lagging list in either direction (the regression
    unified_trading_ci_no_promotion_tiers_divergence_2026_08_07.md exists to fix). Runs `main()` for
    real with `_repos()`/`_gh_json()`/`_branch_exists()` mocked: any of the latter two firing for this
    repo is itself a bug (there is nothing to probe), so they raise if called."""
    manifest = {"repositories": {"unified-trading-ci": {"promotion_model": "single_branch"}}}
    mpath = tmp_path / "workspace-manifest.json"
    mpath.write_text(json.dumps(manifest), encoding="utf-8")

    monkeypatch.delenv("GH_ETAG_CACHE_FILE", raising=False)
    monkeypatch.delenv("GCP_PROJECT_ID", raising=False)
    real_single_branch_repos = plm._single_branch_repos
    monkeypatch.setattr(plm, "_repos", lambda: ["unified-trading-ci"])
    monkeypatch.setattr(plm, "_main_direct_repos", lambda: set())
    monkeypatch.setattr(plm, "_ldr_terminal_repos", lambda: set())
    monkeypatch.setattr(plm, "_single_branch_repos", lambda: real_single_branch_repos(manifest_path=str(mpath)))

    def _must_not_be_called(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("no gh call should fire for a fully-skipped single_branch repo")

    monkeypatch.setattr(plm, "_gh_json", _must_not_be_called)
    monkeypatch.setattr(plm, "_branch_exists", _must_not_be_called)
    monkeypatch.setattr(plm.sys, "argv", ["promotion_lag_monitor.py", "--now-iso", "2026-08-07T00:00:00Z"])

    exit_code = plm.main()
    assert exit_code == 0  # nothing lagging (nothing monitored) → clean exit
