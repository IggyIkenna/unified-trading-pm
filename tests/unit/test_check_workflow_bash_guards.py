"""Unit tests for scripts/validation/check-workflow-bash-guards.py."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "validation" / "check-workflow-bash-guards.py"
    spec = importlib.util.spec_from_file_location("check_workflow_bash_guards", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# ── Tests: _check_file ───────────────────────────────────────────────────


class TestCheckFile:
    def test_clean_file(self, tmp_path: Path) -> None:
        wf = tmp_path / "clean.yml"
        wf.write_text(
            "name: CI\non: push\njobs:\n  build:\n    runs-on: ubuntu-latest\n    steps:\n      - run: echo hello\n"
        )
        violations = MOD._check_file(wf)
        assert violations == []

    def test_detects_secrets_telegram_chat_id(self, tmp_path: Path) -> None:
        wf = tmp_path / "telegram.yml"
        wf.write_text(
            "steps:\n"
            '  - run: curl -X POST "https://api.telegram.org"\n'
            "    env:\n"
            "      CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}\n"
        )
        violations = MOD._check_file(wf)
        assert len(violations) == 1
        assert "vars.TELEGRAM_CHAT_ID" in violations[0]

    def test_detects_unguarded_cmd_substitution(self, tmp_path: Path) -> None:
        wf = tmp_path / "unguarded.yml"
        wf.write_text('steps:\n  - run: |\n      RESULT=$(git diff --name-only && echo "changes found")\n')
        violations = MOD._check_file(wf)
        assert len(violations) == 1
        assert "|| true" in violations[0]

    def test_guarded_cmd_substitution_ok(self, tmp_path: Path) -> None:
        wf = tmp_path / "guarded.yml"
        wf.write_text('steps:\n  - run: |\n      RESULT=$(git diff --name-only && echo "changes" || true)\n')
        violations = MOD._check_file(wf)
        assert violations == []

    def test_comment_lines_skipped(self, tmp_path: Path) -> None:
        wf = tmp_path / "comments.yml"
        wf.write_text('steps:\n  # secrets.TELEGRAM_CHAT_ID is wrong\n  - run: echo "ok"\n')
        violations = MOD._check_file(wf)
        assert violations == []

    def test_unreadable_file(self, tmp_path: Path) -> None:
        wf = tmp_path / "nonexistent.yml"
        violations = MOD._check_file(wf)
        assert violations == []


# ── Tests: check_dir ─────────────────────────────────────────────────────


class TestCheckDir:
    def test_nonexistent_dir(self, tmp_path: Path) -> None:
        total = MOD.check_dir(tmp_path / "nonexistent")
        assert total == 0

    def test_empty_dir(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        total = MOD.check_dir(wf_dir)
        assert total == 0

    def test_dir_with_clean_files(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        (wf_dir / "a.yml").write_text("name: A\nsteps:\n  - run: echo ok\n")
        total = MOD.check_dir(wf_dir)
        assert total == 0

    def test_dir_with_violations(self, tmp_path: Path) -> None:
        wf_dir = tmp_path / "workflows"
        wf_dir.mkdir()
        (wf_dir / "bad.yml").write_text("steps:\n  - env:\n      CHAT: ${{ secrets.TELEGRAM_CHAT_ID }}\n")
        total = MOD.check_dir(wf_dir)
        assert total >= 1
