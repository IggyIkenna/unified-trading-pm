"""Unit tests for check_canonical_model_regressions.py (QG STEP 5.93).

Pure-Python — no GCS/network. Proves the three canonical-model regression
patterns (coarse pipeline_mode / exact-coarse reader probe / Era-A chain write)
fire on planted regressions (exit 1) and pass a canonical tree (exit 0), and
that the documented exclusions (docstrings, blank sentinel, UAC declaration
paths) do NOT false-positive.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

from check_canonical_model_regressions import (  # type: ignore[import-not-found]
    _scan_file,
    main,
)


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


def _patterns(path: Path, repo: str = "r") -> list[str]:
    return sorted(f.pattern for f in _scan_file(path, repo, path.parent))


# ── coarse-pipeline-mode ─────────────────────────────────────────────────────


def test_coarse_batch_assign_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path / "m.py", 'DEFAULT_PIPELINE_MODE = "batch"\n')
    assert _patterns(p) == ["coarse-pipeline-mode"]


def test_coarse_live_kwarg_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path / "m.py", 'w.record_captured(pipeline_mode="live")\n')
    assert _patterns(p) == ["coarse-pipeline-mode"]


def test_blank_sentinel_not_flagged(tmp_path: Path) -> None:
    # `pipeline_mode: str = ""` is the canonical v9 sentinel (derived at stamp).
    p = _write(tmp_path / "m.py", "class R:\n    pipeline_mode: str = ''\n")
    assert _patterns(p) == []


def test_source_aware_value_not_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path / "m.py", 'pipeline_mode = "batch_databento"\n')
    assert _patterns(p) == []


# ── exact-coarse-reader ──────────────────────────────────────────────────────


def test_exact_coarse_path_literal_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path / "r.py", 'PROBE = "raw_tick_data/day=1/pipeline_mode=batch/asset_group=defi/x.parquet"\n')
    assert _patterns(p) == ["exact-coarse-reader"]


def test_docstring_coarse_path_not_flagged(tmp_path: Path) -> None:
    p = _write(
        tmp_path / "r.py",
        '''
        """The retired coarse pipeline_mode=batch/ segment is gone."""
        X = 1
        ''',
    )
    assert _patterns(p) == []


def test_prefix_match_reader_not_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path / "r.py", 'PREFIX = "pipeline_mode=batch_"\n')
    assert _patterns(p) == []


# ── era-a-chain-write ────────────────────────────────────────────────────────


def test_era_a_data_type_kwarg_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path / "w.py", 'write_shards(data_type="options_chain")\n')
    assert _patterns(p) == ["era-a-chain-write"]


def test_era_b_trades_not_flagged(tmp_path: Path) -> None:
    p = _write(tmp_path / "w.py", 'write_shards(data_type="trades", instrument_type="options_chain")\n')
    assert _patterns(p) == []


def test_uac_declaration_path_excluded(tmp_path: Path) -> None:
    # legacy data_type-keyed entries are RETAINED in UAC registry/declaration trees.
    # repo_root = tmp_path so the relative path carries the excluded prefix.
    p = _write(
        tmp_path / "unified_api_contracts" / "registry" / "x.py",
        'InputReq(data_type="options_chain")\n',
    )
    assert [f.pattern for f in _scan_file(p, "r", tmp_path)] == []


# ── main() end-to-end (planted regression) ──────────────────────────────────


def test_main_planted_coarse_exits_1(tmp_path: Path) -> None:
    repo = tmp_path / "svc"
    _write(repo / "pyproject.toml", "[project]\nname='svc'\n")
    _write(repo / "pkg" / "mig.py", 'DEFAULT_PIPELINE_MODE = "batch"\n')
    assert main(["--workspace-root", str(tmp_path), "--scope", "svc", "--source-dir", "pkg"]) == 1


def test_main_clean_exits_0(tmp_path: Path) -> None:
    repo = tmp_path / "svc"
    _write(repo / "pyproject.toml", "[project]\nname='svc'\n")
    _write(repo / "pkg" / "mig.py", 'pipeline_mode = "batch_databento"\n')
    assert main(["--workspace-root", str(tmp_path), "--scope", "svc", "--source-dir", "pkg"]) == 0
