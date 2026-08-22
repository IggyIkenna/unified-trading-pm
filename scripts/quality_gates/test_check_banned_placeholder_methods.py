# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_banned_placeholder_methods.py (QG STEP 5.67).

Run via pytest from a venv that has pyyaml installed (the workspace
.venv-workspace satisfies this), or via the workspace-root pytest invocation
that base-service.sh wires up. These tests are pure-Python — no GCS/AWS/network.

Mirrors test_check_removed_symbols.py in shape: baseline-loader validation,
single-file scanning (banned-name defs + candle-write upload_bytes bypass),
workspace walker exclusions, scope resolution, and a main() end-to-end smoke
(synthetic-new-occurrence → exit 1; baselined-occurrence → exit 0).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest
from check_banned_placeholder_methods import (  # type: ignore[import-not-found]
    BANNED_METHOD_NAMES,
    BaselineEntry,
    Finding,
    _iter_py_files,
    _resolve_scopes,
    _scan_file,
    load_baseline,
    main,
)

# ── Helpers ──────────────────────────────────────────────────────────────────


def _write(path: Path, body: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


# ── Constant sanity ──────────────────────────────────────────────────────────


def test_banned_name_set_shape() -> None:
    """The banned-name set is scoped to 'synthesise a fake candle' names.

    ``_handle_empty_tick_data`` was DROPPED 2026-05-11 PM after writegate Phase
    2.A reformed it into the canonical honest-handler — flagging it would be
    noise. Guard against an accidental re-add.
    """
    assert "_create_empty_output" in BANNED_METHOD_NAMES
    assert "_create_full_day_empty_output" in BANNED_METHOD_NAMES
    assert "_create_closed_market_candle" in BANNED_METHOD_NAMES
    assert "_maybe_write_vix_gap_placeholder" in BANNED_METHOD_NAMES
    assert "_handle_empty_tick_data" not in BANNED_METHOD_NAMES


# ── Baseline loading ─────────────────────────────────────────────────────────


def test_load_baseline_real_workspace_baseline() -> None:
    """The real workspace baseline must always parse cleanly + be all pending_removal.

    A shrinking ratchet — the entries dict is expected to reach (and stay) empty
    once every baselined occurrence is cleaned up (it did, 2026-05-17, per the
    baseline file's own ``entries_postscript``). This asserts the STRUCTURE
    (parses to a dict, every entry — if any — is pending_removal + a proper
    3-tuple key), not a non-empty count.
    """
    here = Path(__file__).resolve().parent
    real = here / "banned_placeholder_methods_baseline.yaml"
    if not real.is_file():  # pragma: no cover — defensive
        pytest.skip("real baseline not yet shipped")
    baseline, default_successor = load_baseline()
    assert isinstance(baseline, dict)
    assert all(e.status == "pending_removal" for e in baseline.values())
    assert default_successor  # non-empty
    # Keys are (repo, file, method) tuples.
    for key in baseline:
        assert isinstance(key, tuple) and len(key) == 3


def test_load_baseline_missing_file_returns_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("check_banned_placeholder_methods._baseline_path", lambda: tmp_path / "nope.yaml")
    baseline, default_successor = load_baseline()
    assert baseline == {}
    assert "writegate Phase 2.A" in default_successor


def test_load_baseline_parses_valid(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    f = _write(
        tmp_path / "baseline.yaml",
        """
        default_successor: "writegate Phase 2.A — test"
        entries:
          - repo: some-repo
            file: some_repo/app/core/foo.py
            method: _create_empty_output
            status: pending_removal
            successor: "writegate Phase 2.A — delete it"
        """,
    )
    monkeypatch.setattr("check_banned_placeholder_methods._baseline_path", lambda: f)
    baseline, default_successor = load_baseline()
    assert len(baseline) == 1
    entry = baseline[("some-repo", "some_repo/app/core/foo.py", "_create_empty_output")]
    assert entry.status == "pending_removal"
    assert "delete it" in entry.successor
    assert default_successor == "writegate Phase 2.A — test"


def test_load_baseline_skips_bad_entries(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Missing-key + invalid-status entries are skipped (stderr note), not raised — the
    loader is lenient so a malformed entry can't take down every consumer repo's QG."""
    f = _write(
        tmp_path / "baseline.yaml",
        """
        default_successor: "x"
        entries:
          - repo: r1
            file: r1/foo.py
            method: _create_empty_output
            status: pending_removal
            successor: "ok"
          - repo: r2
            status: pending_removal       # missing file/method/successor → skipped
          - repo: r3
            file: r3/bar.py
            method: _create_closed_market_candle
            status: not_a_real_status      # invalid status → skipped
            successor: "y"
        """,
    )
    monkeypatch.setattr("check_banned_placeholder_methods._baseline_path", lambda: f)
    baseline, _ = load_baseline()
    assert ("r1", "r1/foo.py", "_create_empty_output") in baseline
    assert ("r3", "r3/bar.py", "_create_closed_market_candle") not in baseline
    assert len(baseline) == 1


# ── Single-file scanning: banned method defs ─────────────────────────────────


def test_scan_detects_banned_def(tmp_path: Path) -> None:
    src = _write(
        tmp_path / "pkg" / "adapter.py", "class A:\n    def _create_empty_output(self):\n        return None\n"
    )
    findings = _scan_file(src, "fakerepo", tmp_path)
    assert len(findings) == 1
    f = findings[0]
    assert f.method == "_create_empty_output"
    assert f.line == 2
    assert f.file == "pkg/adapter.py"
    assert f.repo == "fakerepo"


def test_scan_detects_async_banned_def(tmp_path: Path) -> None:
    src = _write(
        tmp_path / "pkg" / "w.py", "class A:\n    async def _create_closed_market_candle(self):\n        ...\n"
    )
    findings = _scan_file(src, "r", tmp_path)
    assert len(findings) == 1
    assert findings[0].method == "_create_closed_market_candle"


def test_scan_clean_file_no_findings(tmp_path: Path) -> None:
    src = _write(tmp_path / "pkg" / "ok.py", "def record_empty_for_shard(**kw):\n    return None\n")
    assert _scan_file(src, "r", tmp_path) == []


def test_scan_does_not_fire_on_handle_empty_tick_data(tmp_path: Path) -> None:
    """Regression guard: _handle_empty_tick_data is the canonical honest-handler name
    (writegate Phase 2.A reform) — it must NOT be flagged. If this fails, someone
    re-added _handle_empty_tick_data to BANNED_METHOD_NAMES."""
    src = _write(
        tmp_path / "pkg" / "batch_workers.py",
        "class A:\n    def _handle_empty_tick_data(self):\n        record_empty_for_shard()\n",
    )
    assert _scan_file(src, "r", tmp_path) == []


def test_scan_handles_unparseable_file(tmp_path: Path) -> None:
    """SyntaxError in a file must NOT crash the scanner."""
    src = _write(tmp_path / "pkg" / "broken.py", "def f(:\n    pass\n")
    assert _scan_file(src, "r", tmp_path) == []


# ── Single-file scanning: candle-write upload_bytes bypass ───────────────────


def test_scan_detects_upload_bytes_in_candle_module(tmp_path: Path) -> None:
    src = _write(
        tmp_path / "pkg" / "orchestration_writer.py",
        "def write(self, blob):\n    self.storage_client.upload_bytes(blob)\n",
    )
    findings = _scan_file(src, "mdps", tmp_path)
    assert len(findings) == 1
    assert findings[0].method == "upload_bytes"
    assert findings[0].file == "pkg/orchestration_writer.py"


def test_scan_no_upload_bytes_finding_in_non_candle_module(tmp_path: Path) -> None:
    """upload_bytes in a module whose path doesn't look like a candle-write context is fine."""
    src = _write(tmp_path / "pkg" / "events_publisher.py", "def f(self, b):\n    self.storage_client.upload_bytes(b)\n")
    assert _scan_file(src, "r", tmp_path) == []


def test_scan_no_upload_bytes_finding_for_bare_call(tmp_path: Path) -> None:
    """A bare ``upload_bytes(...)`` call (not ``something.upload_bytes(...)``) doesn't match —
    the heuristic specifically targets the storage-client attribute-method bypass."""
    src = _write(tmp_path / "pkg" / "output_writer.py", "from x import upload_bytes\ndef f(b):\n    upload_bytes(b)\n")
    assert _scan_file(src, "r", tmp_path) == []


def test_scan_ohlcv_passthrough_is_a_candle_module(tmp_path: Path) -> None:
    src = _write(
        tmp_path / "adapters" / "tradfi" / "ohlcv_passthrough.py", "def w(self, b):\n    self.client.upload_bytes(b)\n"
    )
    findings = _scan_file(src, "mdps", tmp_path)
    assert len(findings) == 1 and findings[0].method == "upload_bytes"


# ── Workspace walker ─────────────────────────────────────────────────────────


def test_iter_py_files_excludes_venv_build_scripts_tests(tmp_path: Path) -> None:
    real = _write(tmp_path / "pkg" / "real.py", "# real\n")
    venv_noise = _write(tmp_path / ".venv" / "lib" / "noise.py", "# noise\n")
    build_noise = _write(tmp_path / "build" / "noise.py", "# noise\n")
    scripts_noise = _write(tmp_path / "scripts" / "tool.py", "# script\n")
    tests_noise = _write(tmp_path / "tests" / "test_x.py", "# test\n")
    found = set(_iter_py_files(tmp_path))
    assert real in found
    assert venv_noise not in found
    assert build_noise not in found
    assert scripts_noise not in found
    assert tests_noise not in found


def test_iter_py_files_excludes_archive_path_fragments(tmp_path: Path) -> None:
    real = _write(tmp_path / "pkg" / "real.py", "# real\n")
    archived = _write(tmp_path / "pkg" / "archive" / "old.py", "# old\n")
    found = set(_iter_py_files(tmp_path))
    assert real in found
    assert archived not in found


# ── Scope resolution ─────────────────────────────────────────────────────────


def test_resolve_scopes_with_source_dir(tmp_path: Path) -> None:
    (tmp_path / "myrepo" / "mypkg").mkdir(parents=True)
    scopes = _resolve_scopes(tmp_path, "myrepo", "mypkg")
    assert scopes == [("myrepo", tmp_path / "myrepo" / "mypkg")]


def test_resolve_scopes_scope_only_when_source_dir_absent(tmp_path: Path) -> None:
    (tmp_path / "myrepo").mkdir()
    scopes = _resolve_scopes(tmp_path, "myrepo", "nonexistent_pkg")
    assert scopes == [("myrepo", tmp_path / "myrepo")]


def test_resolve_scopes_missing_scope_dir_returns_empty(tmp_path: Path) -> None:
    assert _resolve_scopes(tmp_path, "no_such_repo", None) == []


def test_resolve_scopes_workspace_wide_picks_pyproject_dirs(tmp_path: Path) -> None:
    (tmp_path / "repo_a").mkdir()
    _ = (tmp_path / "repo_a" / "pyproject.toml").write_text("[project]\n")
    (tmp_path / "repo_b").mkdir()  # no pyproject → skipped
    (tmp_path / ".venv").mkdir()  # excluded dir name
    scopes = _resolve_scopes(tmp_path, None, None)
    names = {name for name, _ in scopes}
    assert "repo_a" in names
    assert "repo_b" not in names
    assert ".venv" not in names


# ── main() end-to-end ────────────────────────────────────────────────────────


def _seed_baseline(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, entries_yaml: str) -> None:
    body = 'default_successor: "writegate Phase 2.A — test"\nentries:\n' + textwrap.indent(
        textwrap.dedent(entries_yaml), "  "
    )
    f = _write(tmp_path / "_baseline.yaml", body)
    monkeypatch.setattr("check_banned_placeholder_methods._baseline_path", lambda: f)


def test_main_new_occurrence_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _seed_baseline(monkeypatch, tmp_path, "[]\n")
    repo = tmp_path / "fakerepo"
    _write(repo / "fakepkg" / "bad.py", "class A:\n    def _create_empty_output(self):\n        return None\n")
    assert main(["--workspace-root", str(tmp_path), "--scope", "fakerepo", "--source-dir", "fakepkg"]) == 1


def test_main_baselined_occurrence_passes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    repo = tmp_path / "fakerepo"
    _write(repo / "fakepkg" / "bad.py", "class A:\n    def _create_empty_output(self):\n        return None\n")
    _seed_baseline(
        monkeypatch,
        tmp_path,
        """
        - repo: fakerepo
          file: fakepkg/bad.py
          method: _create_empty_output
          status: pending_removal
          successor: "writegate Phase 2.A"
        """,
    )
    assert main(["--workspace-root", str(tmp_path), "--scope", "fakerepo", "--source-dir", "fakepkg"]) == 0


def test_main_clean_repo_passes(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _seed_baseline(monkeypatch, tmp_path, "[]\n")
    repo = tmp_path / "fakerepo"
    _write(repo / "fakepkg" / "ok.py", "def record_empty_for_shard(**kw):\n    return None\n")
    assert main(["--workspace-root", str(tmp_path), "--scope", "fakerepo", "--source-dir", "fakepkg"]) == 0


def test_main_absent_scope_is_clean_skip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _seed_baseline(monkeypatch, tmp_path, "[]\n")
    # scope dir doesn't exist → _resolve_scopes returns [] → main treats as clean skip (exit 0).
    assert main(["--workspace-root", str(tmp_path), "--scope", "no_such_repo"]) == 0


def test_main_candle_module_upload_bytes_bypass_fails(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _seed_baseline(monkeypatch, tmp_path, "[]\n")
    repo = tmp_path / "mdps"
    _write(repo / "core" / "orchestration_writer.py", "def w(self, b):\n    self.storage_client.upload_bytes(b)\n")
    assert main(["--workspace-root", str(tmp_path), "--scope", "mdps", "--source-dir", "core"]) == 1


# ── Dataclasses ──────────────────────────────────────────────────────────────


def test_finding_is_frozen() -> None:
    f = Finding(repo="r", file="f.py", line=1, method="_create_empty_output", snippet="def _create_empty_output(self):")
    with pytest.raises(AttributeError):
        f.line = 99  # type: ignore[misc]


def test_finding_baseline_key() -> None:
    f = Finding(repo="r", file="f.py", line=1, method="_create_empty_output", snippet="x")
    assert f.baseline_key == ("r", "f.py", "_create_empty_output")


def test_baseline_entry_is_frozen() -> None:
    e = BaselineEntry(repo="r", file="f.py", method="_create_empty_output", status="pending_removal", successor="x")
    with pytest.raises(AttributeError):
        e.status = "changed"  # type: ignore[misc]
