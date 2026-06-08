"""Unit tests for check_bar_edge_open_ingestion.py (QG STEP 5.92).

Pure-Python — no GCS/network. Proves the open-edge (left) bar-ingestion gate
fires on a NEW open-edge site (planted regression → exit 1) and passes a
close-converted tree (exit 0), plus the per-pattern detection + clearing logic.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from check_bar_edge_open_ingestion import (  # type: ignore[import-not-found]
    _scan_file,
    main,
)


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def _scan(path: Path, repo: str = "r") -> list[str]:
    return [f.function for f in _scan_file(path, repo, path.parent)]


# ── detection ────────────────────────────────────────────────────────────────


def test_period_start_unix_flagged(tmp_path: Path) -> None:
    p = _write(
        tmp_path / "a.py",
        """
        def _convert_item(item):
            return {"timestamp": int(item.get("periodStartUnix", 0))}
        """,
    )
    assert _scan(p) == ["_convert_item"]


def test_open_timestamp_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path / "a.py", "def f(bar):\n    return bar.openTimestamp\n")
    assert _scan(p) == ["f"]


def test_compute_bar_close_boundary_clears(tmp_path: Path) -> None:
    p = _write(
        tmp_path / "a.py",
        """
        def _convert_item(item):
            _o, t_close, _a = compute_bar_close_boundary(to_dt(item["periodStartUnix"]), "1h")
            return {"timestamp": t_close}
        """,
    )
    assert _scan(p) == []


def test_close_field_clears_candle_fn(tmp_path: Path) -> None:
    # candle fn uses vendor "t" (open) BUT also references "T" (close) → cleared.
    p = _write(
        tmp_path / "a.py",
        """
        def _parse_hl_candle(bar):
            open_ms = bar.get("t")
            return {"timestamp": bar.get("T")}
        """,
    )
    assert _scan(p) == []


def test_t_open_in_candle_fn_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path / "a.py", 'def _fetch_pacifica_candles(b):\n    return b.get("t")\n')
    assert _scan(p) == ["_fetch_pacifica_candles"]


def test_t_open_outside_candle_fn_not_flagged(tmp_path: Path) -> None:
    # "t" is too generic to flag outside a candle/ohlcv/kline fn.
    p = _write(tmp_path / "a.py", 'def helper(d):\n    return d.get("t")\n')
    assert _scan(p) == []


def test_noqa_suppresses(tmp_path: Path) -> None:
    p = _write(
        tmp_path / "a.py",
        """
        def f(item):
            return item.get("periodStartUnix")  # noqa: bar-boundary-open-edge
        """,
    )
    assert _scan(p) == []


# ── main() end-to-end (planted regression) ──────────────────────────────────


def test_main_planted_open_edge_exits_1(tmp_path: Path) -> None:
    repo = tmp_path / "svc"
    _write(repo / "pyproject.toml", "[project]\nname='svc'\n")
    _write(repo / "pkg" / "adapter.py", 'def _conv(i):\n    return {"timestamp": i["periodStartUnix"]}\n')
    rc = main(["--workspace-root", str(tmp_path), "--scope", "svc", "--source-dir", "pkg"])
    assert rc == 1


def test_main_clean_exits_0(tmp_path: Path) -> None:
    repo = tmp_path / "svc"
    _write(repo / "pyproject.toml", "[project]\nname='svc'\n")
    _write(repo / "pkg" / "adapter.py", "def _conv(i):\n    return {'timestamp': i['close_ts']}\n")
    rc = main(["--workspace-root", str(tmp_path), "--scope", "svc", "--source-dir", "pkg"])
    assert rc == 0
