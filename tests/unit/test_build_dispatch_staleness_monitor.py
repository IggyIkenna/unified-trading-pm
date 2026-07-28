"""Unit tests for the pure staleness decision in scripts/cicd/build_dispatch_staleness_monitor.py.

Guards, most-important first:
  * A fresh `main` HEAD (younger than the threshold) is NEVER stale — a build genuinely in flight
    looks identical to a dropped one for the first few minutes.
  * An old `main` HEAD with NO `:latest` image resolvable at all IS stale (fail toward reporting,
    not silently treating "unknown image" as "fine").
  * An `:latest` image pushed AT OR AFTER `main` HEAD is never stale, regardless of `main` HEAD age.
  * An `:latest` image behind `main` HEAD by less than the threshold is within the grace window.
  * Only a genuine build+dispatch-latency-exceeding gap pages.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "cicd" / "build_dispatch_staleness_monitor.py"
    spec = importlib.util.spec_from_file_location("build_dispatch_staleness_monitor", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BDS = _load_module()

_NOW = dt.datetime(2026, 7, 28, 12, 0, 0, tzinfo=dt.UTC)
_THRESH_S = 45 * 60.0


def test_fresh_main_head_never_stale_even_with_no_image() -> None:
    main_when = _NOW - dt.timedelta(minutes=5)
    stale, reason = BDS._stale(main_when, None, _NOW, _THRESH_S)
    assert stale is False
    assert "grace window" in reason


def test_old_main_head_with_no_image_is_stale() -> None:
    main_when = _NOW - dt.timedelta(minutes=90)
    stale, reason = BDS._stale(main_when, None, _NOW, _THRESH_S)
    assert stale is True
    assert "NO `:latest` image" in reason


def test_image_pushed_after_main_head_is_never_stale() -> None:
    main_when = _NOW - dt.timedelta(minutes=90)
    image_when = _NOW - dt.timedelta(minutes=10)
    stale, reason = BDS._stale(main_when, image_when, _NOW, _THRESH_S)
    assert stale is False
    assert "build is current" in reason


def test_image_lag_within_threshold_is_not_stale() -> None:
    main_when = _NOW - dt.timedelta(minutes=90)
    image_when = _NOW - dt.timedelta(minutes=95)  # image predates main HEAD by 5m < 45m threshold
    stale, reason = BDS._stale(main_when, image_when, _NOW, _THRESH_S)
    assert stale is False
    assert "grace window" in reason


def test_image_lag_beyond_threshold_pages() -> None:
    main_when = _NOW - dt.timedelta(minutes=120)
    image_when = _NOW - dt.timedelta(minutes=200)  # image predates main HEAD by 80m > 45m threshold
    stale, reason = BDS._stale(main_when, image_when, _NOW, _THRESH_S)
    assert stale is True
    assert "behind main HEAD" in reason


def test_ldr_main_repos_filters_by_promotion_model(tmp_path: Path) -> None:
    manifest = tmp_path / "workspace-manifest.json"
    manifest.write_text(
        '{"repositories": {'
        '"a": {"promotion_model": "ldr_main"}, '
        '"b": {"promotion_model": "staging_gated"}, '
        '"c": {"promotion_model": "ldr_main"}'
        "}}"
    )
    assert BDS._ldr_main_repos(str(manifest)) == ["a", "c"]
