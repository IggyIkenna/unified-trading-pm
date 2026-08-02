"""Unit tests for scripts/workspace/sync-gitignore-cursorignore.py --dry-run gating.

Regression for issues/gitignore_sync_script_destructive_due_to_stale_central_template_2026_07_27.md
#1: `main()` previously wrote .gitignore/.cursorignore unconditionally and unconditionally chained
`untrack-ignored-files.py --untrack`, ignoring `dry_run` outside the `--purge-history` branch even
though the module docstring already promised "Preview changes without writing anything." These tests
pin that `--dry-run` now performs zero writes and forwards `--dry-run` (not `--untrack`) downstream.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "workspace" / "sync-gitignore-cursorignore.py"
    spec = importlib.util.spec_from_file_location("sync_gitignore_cursorignore", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


class _FakeCompletedProcess:
    returncode = 0


def _make_fake_repo(root: Path, name: str) -> Path:
    repo = root / name
    (repo / ".git").mkdir(parents=True)
    (repo / ".gitignore").write_text("# stale\n", encoding="utf-8")
    (repo / ".cursorignore").write_text("# stale\n", encoding="utf-8")
    return repo


@pytest.fixture()
def fake_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    ws = tmp_path / "workspace"
    ws.mkdir()
    _make_fake_repo(ws, "repo-a")
    # Redirect the module's workspace scan at a throwaway tree; CENTRAL_GITIGNORE/
    # CENTRAL_CURSORIGNORE stay pointed at the real (read-only) PM templates.
    monkeypatch.setattr(MOD, "WORKSPACE_ROOT", ws)
    return ws


def _stub_subprocess(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    calls: list[list[str]] = []

    def _fake_run(cmd: list[str], *args: object, **kwargs: object) -> _FakeCompletedProcess:
        calls.append(cmd)
        return _FakeCompletedProcess()

    monkeypatch.setattr(MOD.subprocess, "run", _fake_run)
    return calls


class TestDryRunGatesWrites:
    def test_dry_run_writes_nothing(
        self, fake_workspace: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _stub_subprocess(monkeypatch)
        monkeypatch.setattr(sys, "argv", ["sync-gitignore-cursorignore.py", "--dry-run"])
        gi = fake_workspace / "repo-a" / ".gitignore"
        ci = fake_workspace / "repo-a" / ".cursorignore"
        before_gi, before_ci = gi.read_text(), ci.read_text()

        MOD.main()

        assert gi.read_text() == before_gi
        assert ci.read_text() == before_ci

    def test_dry_run_output_says_would_update_not_updated(
        self, fake_workspace: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        _stub_subprocess(monkeypatch)
        monkeypatch.setattr(sys, "argv", ["sync-gitignore-cursorignore.py", "--dry-run"])

        MOD.main()

        out = capsys.readouterr().out
        assert "would update" in out
        assert "Updated repo-a/" not in out

    def test_dry_run_forwards_dry_run_not_untrack_to_untrack_script(
        self, fake_workspace: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        calls = _stub_subprocess(monkeypatch)
        monkeypatch.setattr(sys, "argv", ["sync-gitignore-cursorignore.py", "--dry-run"])

        MOD.main()

        assert calls, "expected the untrack-ignored-files.py subprocess call"
        untrack_cmd = calls[-1]
        assert "--dry-run" in untrack_cmd
        assert "--untrack" not in untrack_cmd


class TestApplyModeUnaffected:
    def test_apply_mode_still_writes_and_untracks(
        self, fake_workspace: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        calls = _stub_subprocess(monkeypatch)
        monkeypatch.setattr(sys, "argv", ["sync-gitignore-cursorignore.py"])
        gi = fake_workspace / "repo-a" / ".gitignore"

        MOD.main()

        assert gi.read_text() != "# stale\n"
        out = capsys.readouterr().out
        assert "Updated repo-a/" in out
        untrack_cmd = calls[-1]
        assert "--untrack" in untrack_cmd
        assert "--dry-run" not in untrack_cmd
