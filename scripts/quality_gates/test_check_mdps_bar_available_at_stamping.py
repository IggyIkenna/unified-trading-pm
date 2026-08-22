# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_mdps_bar_available_at_stamping.py (Phase 0.6 QG STEP).

Run via pytest from a venv that has the workspace dependencies — pure Python,
no GCS / AWS / network.

Mirrors test_check_banned_placeholder_methods.py in shape: constants sanity,
single-file scanning, scope resolution, main() end-to-end smoke.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from check_mdps_bar_available_at_stamping import (  # type: ignore[import-not-found]
    CANONICAL_WRITER_ALLOWED_FUNCTIONS,
    QG_ALLOW_MARKER,
    _resolve_scopes,
    _scan_file,
    main,
)


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


# ── Constants sanity ─────────────────────────────────────────────────────────


def test_canonical_writer_allowed_functions_shape() -> None:
    """Only the canonical helper + its private validator may write `available_at`."""
    assert "_stamp_candle_available_at" in CANONICAL_WRITER_ALLOWED_FUNCTIONS
    assert "_validate_stamped_candle_bar_boundary" in CANONICAL_WRITER_ALLOWED_FUNCTIONS
    # Anything else writing the column is a banned bypass.
    assert "write_candle_parquet" not in CANONICAL_WRITER_ALLOWED_FUNCTIONS


def test_qg_allow_marker_shape() -> None:
    """The escape-hatch marker is stable so callers can rely on it."""
    assert QG_ALLOW_MARKER == "# QG-allow: mdps-bar-available-at"


# ── Single-file scanning ─────────────────────────────────────────────────────


def test_scan_file_flags_unauthorised_write(tmp_path: Path) -> None:
    """A new file outside canonical_writer.py that writes `df["available_at"]
    = ...` is an ERROR."""
    repo_root = tmp_path / "fake-mdps"
    canonical_writer_path = repo_root / "app" / "core" / "canonical_writer.py"

    offending = repo_root / "app" / "adapters" / "evil_inline_stamper.py"
    _write(
        offending,
        """
        import pandas as pd


        def stamp_inline(df: pd.DataFrame) -> pd.DataFrame:
            # BANNED — should be routed through _stamp_candle_available_at.
            df["available_at"] = df["timestamp"] + pd.Timedelta("50ms")
            return df
        """,
    )

    findings = _scan_file(
        offending,
        repo_name="fake-mdps",
        repo_root=repo_root,
        canonical_writer_path=canonical_writer_path,
    )
    assert len(findings) == 1
    f = findings[0]
    assert f.enclosing_function == "stamp_inline"
    assert "available_at" in f.snippet


def test_scan_file_allows_canonical_writer_helpers(tmp_path: Path) -> None:
    """Writes inside `_stamp_candle_available_at` / `_validate_stamped_candle_bar_boundary`
    in canonical_writer.py itself are allowed."""
    repo_root = tmp_path / "fake-mdps"
    canonical_writer_path = repo_root / "app" / "core" / "canonical_writer.py"
    _write(
        canonical_writer_path,
        """
        import pandas as pd


        def _stamp_candle_available_at(df: pd.DataFrame) -> pd.DataFrame:
            df["available_at"] = df["timestamp"] + pd.Timedelta("50ms")
            return df


        def _validate_stamped_candle_bar_boundary(df: pd.DataFrame) -> None:
            # Allowed inside the validator too — re-stamping for normalisation.
            df["available_at"] = df["available_at"]
        """,
    )
    findings = _scan_file(
        canonical_writer_path,
        repo_name="fake-mdps",
        repo_root=repo_root,
        canonical_writer_path=canonical_writer_path,
    )
    assert findings == []


def test_scan_file_blocks_other_canonical_writer_functions(tmp_path: Path) -> None:
    """Even WITHIN canonical_writer.py, only the 2 allowed helpers may write."""
    repo_root = tmp_path / "fake-mdps"
    canonical_writer_path = repo_root / "app" / "core" / "canonical_writer.py"
    _write(
        canonical_writer_path,
        """
        import pandas as pd


        def write_candle_parquet(df: pd.DataFrame) -> None:
            # BANNED — must call _stamp_candle_available_at, not stamp directly.
            df["available_at"] = df["timestamp"] + pd.Timedelta("50ms")
        """,
    )
    findings = _scan_file(
        canonical_writer_path,
        repo_name="fake-mdps",
        repo_root=repo_root,
        canonical_writer_path=canonical_writer_path,
    )
    assert len(findings) == 1
    assert findings[0].enclosing_function == "write_candle_parquet"


def test_scan_file_allows_inline_escape_hatch_marker(tmp_path: Path) -> None:
    """The `# QG-allow: mdps-bar-available-at` marker exempts a single line."""
    repo_root = tmp_path / "fake-mdps"
    canonical_writer_path = repo_root / "app" / "core" / "canonical_writer.py"
    offending = repo_root / "app" / "adapters" / "allowlisted_inline.py"
    _write(
        offending,
        """
        import pandas as pd


        def stamp_with_marker(df: pd.DataFrame) -> pd.DataFrame:
            df["available_at"] = df["timestamp"] + pd.Timedelta("50ms")  # QG-allow: mdps-bar-available-at
            return df
        """,
    )
    findings = _scan_file(
        offending,
        repo_name="fake-mdps",
        repo_root=repo_root,
        canonical_writer_path=canonical_writer_path,
    )
    assert findings == []


def test_scan_file_ignores_non_available_at_writes(tmp_path: Path) -> None:
    """Writes to other columns (`timestamp`, `close`, etc.) are not flagged."""
    repo_root = tmp_path / "fake-mdps"
    canonical_writer_path = repo_root / "app" / "core" / "canonical_writer.py"
    benign = repo_root / "app" / "calculators" / "polars_candle_engine.py"
    _write(
        benign,
        """
        import pandas as pd


        def aggregate(df: pd.DataFrame) -> pd.DataFrame:
            df["timestamp"] = df["t_close"]
            df["close"] = df["close"].fillna(method="ffill")
            return df
        """,
    )
    findings = _scan_file(
        benign,
        repo_name="fake-mdps",
        repo_root=repo_root,
        canonical_writer_path=canonical_writer_path,
    )
    assert findings == []


def test_scan_file_flags_aug_assign(tmp_path: Path) -> None:
    """`df["available_at"] += <delta>` is also banned."""
    repo_root = tmp_path / "fake-mdps"
    canonical_writer_path = repo_root / "app" / "core" / "canonical_writer.py"
    offending = repo_root / "app" / "adapters" / "evil_inline_aug.py"
    _write(
        offending,
        """
        import pandas as pd


        def shift_available_at(df: pd.DataFrame) -> pd.DataFrame:
            df["available_at"] += pd.Timedelta(minutes=1)
            return df
        """,
    )
    findings = _scan_file(
        offending,
        repo_name="fake-mdps",
        repo_root=repo_root,
        canonical_writer_path=canonical_writer_path,
    )
    assert len(findings) == 1
    assert findings[0].enclosing_function == "shift_available_at"


# ── Scope resolution ─────────────────────────────────────────────────────────


def test_resolve_scopes_defaults_to_mdps(tmp_path: Path) -> None:
    """No scope arg → default to market-data-processing-service."""
    (tmp_path / "market-data-processing-service" / "market_data_processing_service").mkdir(parents=True)
    scopes = _resolve_scopes(tmp_path, scope=None, source_dir=None)
    assert len(scopes) == 1
    repo, scan_root, canonical_path = scopes[0]
    assert repo == "market-data-processing-service"
    assert scan_root.name == "market_data_processing_service"
    assert canonical_path.name == "canonical_writer.py"


def test_resolve_scopes_returns_empty_when_repo_absent(tmp_path: Path) -> None:
    """Repo dir absent → empty list (clean skip, not failure)."""
    scopes = _resolve_scopes(tmp_path, scope="nonexistent-repo", source_dir=None)
    assert scopes == []


# ── main() end-to-end ────────────────────────────────────────────────────────


def test_main_exits_clean_when_no_findings(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Clean MDPS source → exit 0."""
    scan_root = tmp_path / "market-data-processing-service" / "market_data_processing_service"
    canonical_writer_path = scan_root / "app" / "core" / "canonical_writer.py"
    _write(
        canonical_writer_path,
        """
        import pandas as pd


        def _stamp_candle_available_at(df: pd.DataFrame) -> pd.DataFrame:
            df["available_at"] = df["timestamp"] + pd.Timedelta("50ms")
            return df
        """,
    )
    exit_code = main(["--workspace-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "OK" in captured.out


def test_main_exits_one_when_unauthorised_write(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Non-canonical `available_at` write → exit 1 + ERROR line."""
    scan_root = tmp_path / "market-data-processing-service" / "market_data_processing_service"
    canonical_writer_path = scan_root / "app" / "core" / "canonical_writer.py"
    _write(canonical_writer_path, "import pandas as pd\n")
    offending = scan_root / "app" / "adapters" / "evil_inline_stamper.py"
    _write(
        offending,
        """
        import pandas as pd


        def stamp_inline(df: pd.DataFrame) -> pd.DataFrame:
            df["available_at"] = df["timestamp"] + pd.Timedelta("50ms")
            return df
        """,
    )
    exit_code = main(["--workspace-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "FAIL" in captured.err
    assert "stamp_inline" in captured.err


def test_main_skips_clean_when_workspace_empty(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """No MDPS repo → exit 0 (clean skip, not failure)."""
    exit_code = main(["--workspace-root", str(tmp_path)])
    captured = capsys.readouterr()
    assert exit_code == 0
    assert "skipping" in captured.out
