"""Unit tests for scripts/validators/validate_plan_links.py."""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path

import pytest


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "validators" / "validate_plan_links.py"
    spec = importlib.util.spec_from_file_location("validate_plan_links", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


class TestMain:
    def test_no_plans_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(
            "sys.argv",
            ["validate_plan_links.py", "--plans-dir", str(tmp_path / "nonexistent"), "--workspace-root", str(tmp_path)],
        )
        result = MOD.main()
        assert result == 0

    def test_empty_plans_dir(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        plans_dir = tmp_path / "plans" / "active"
        plans_dir.mkdir(parents=True)
        monkeypatch.setattr(
            "sys.argv",
            ["validate_plan_links.py", "--plans-dir", str(plans_dir), "--workspace-root", str(tmp_path)],
        )
        result = MOD.main()
        assert result == 0

    def test_plan_with_valid_http_link(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        plans_dir = tmp_path / "plans" / "active"
        plans_dir.mkdir(parents=True)
        plan = plans_dir / "test.md"
        plan.write_text("See [docs](https://example.com) for details.\n")
        monkeypatch.setattr(
            "sys.argv",
            ["validate_plan_links.py", "--plans-dir", str(plans_dir), "--workspace-root", str(tmp_path)],
        )
        result = MOD.main()
        assert result == 0

    def test_plan_with_anchor_link(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        plans_dir = tmp_path / "plans" / "active"
        plans_dir.mkdir(parents=True)
        plan = plans_dir / "test.md"
        plan.write_text("See [section](#my-section) for details.\n")
        monkeypatch.setattr(
            "sys.argv",
            ["validate_plan_links.py", "--plans-dir", str(plans_dir), "--workspace-root", str(tmp_path)],
        )
        result = MOD.main()
        assert result == 0

    def test_plan_with_valid_relative_link(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        plans_dir = tmp_path / "plans" / "active"
        plans_dir.mkdir(parents=True)
        other_plan = plans_dir / "other.md"
        other_plan.write_text("Other plan\n")
        plan = plans_dir / "test.md"
        plan.write_text("See [other](other.md) for details.\n")
        monkeypatch.setattr(
            "sys.argv",
            ["validate_plan_links.py", "--plans-dir", str(plans_dir), "--workspace-root", str(tmp_path)],
        )
        result = MOD.main()
        assert result == 0

    def test_plan_with_broken_relative_link(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        plans_dir = tmp_path / "plans" / "active"
        plans_dir.mkdir(parents=True)
        plan = plans_dir / "test.md"
        plan.write_text("See [missing](nonexistent.md) for details.\n")
        monkeypatch.setattr(
            "sys.argv",
            ["validate_plan_links.py", "--plans-dir", str(plans_dir), "--workspace-root", str(tmp_path)],
        )
        result = MOD.main()
        assert result == 1

    def test_plan_with_workspace_repo_link(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        plans_dir = tmp_path / "plans" / "active"
        plans_dir.mkdir(parents=True)
        # Create the repo directory so the link resolves
        repo_dir = tmp_path / "execution-service"
        repo_dir.mkdir()
        plan = plans_dir / "test.md"
        plan.write_text("See [exec](execution-service/something) for details.\n")
        monkeypatch.setattr(
            "sys.argv",
            ["validate_plan_links.py", "--plans-dir", str(plans_dir), "--workspace-root", str(tmp_path)],
        )
        result = MOD.main()
        assert result == 0

    def test_plan_with_repo_root_relative_leading_slash_link(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # "/codex/..." is this repo's PM-repo-root-relative convention, not filesystem-absolute
        # (unified-trading-pm@<pending>, fixing 15 real BROKEN false-positives in plans/active/*.md).
        plans_dir = tmp_path / "plans" / "active"
        plans_dir.mkdir(parents=True)
        codex_dir = tmp_path / "codex" / "04-architecture"
        codex_dir.mkdir(parents=True)
        (codex_dir / "custody-providers.md").write_text("Custody doc\n")
        plan = plans_dir / "test.md"
        plan.write_text("See [custody](/codex/04-architecture/custody-providers.md) for details.\n")
        monkeypatch.setattr(
            "sys.argv",
            ["validate_plan_links.py", "--plans-dir", str(plans_dir), "--workspace-root", str(tmp_path)],
        )
        result = MOD.main()
        assert result == 0

    def test_plan_with_broken_repo_root_relative_link(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        plans_dir = tmp_path / "plans" / "active"
        plans_dir.mkdir(parents=True)
        plan = plans_dir / "test.md"
        plan.write_text("See [missing](/codex/nonexistent.md) for details.\n")
        monkeypatch.setattr(
            "sys.argv",
            ["validate_plan_links.py", "--plans-dir", str(plans_dir), "--workspace-root", str(tmp_path)],
        )
        result = MOD.main()
        assert result == 1

    def test_plan_with_archive_fallback(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        plans_dir = tmp_path / "plans" / "active"
        plans_dir.mkdir(parents=True)
        archive_dir = tmp_path / "plans" / "archive"
        archive_dir.mkdir(parents=True)
        # Put an archived plan
        archived = archive_dir / "old.md"
        archived.write_text("Old plan\n")
        plan = plans_dir / "test.md"
        plan.write_text("See [old](old.md) for details.\n")
        monkeypatch.setattr(
            "sys.argv",
            ["validate_plan_links.py", "--plans-dir", str(plans_dir), "--workspace-root", str(tmp_path)],
        )
        result = MOD.main()
        assert result == 0
