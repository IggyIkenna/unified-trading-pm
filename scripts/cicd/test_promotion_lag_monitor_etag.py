"""Unit tests for the ETag conditional-request layer in promotion_lag_monitor.

The monitor compares ~25 repos x 4 directions every 20 min (~300 PAT calls/hr).
GitHub does NOT count a 304 against the rate limit, so an ETag cache (persisted
across CI runs via actions/cache) collapses unchanged-branch-pair compares to free
304s. These tests pin the parser + cache + the 304-reuses-cache behaviour.
"""

from __future__ import annotations

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
