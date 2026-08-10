"""Unit tests for scripts/quality_gates/check_workspace_code_workspace_drift.py.

Covers the regression guard for the .code-workspace repo-list drift root-caused in
plans/active/issues/workspace_config_repo_list_drift_2026_06_01.md.
"""

from __future__ import annotations

import importlib.util
import json
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "quality_gates" / "check_workspace_code_workspace_drift.py"
    spec = importlib.util.spec_from_file_location("check_ws_drift", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


# 2026-08-10 (55a43797a4): PM-root resolution is content-based from __file__ and ignores an
# explicit workspace_root, so a test passing a synthetic tmp_path fixture would otherwise be
# silently redirected to the REAL checkout. Redirect _pm_root_or_legacy to the fixture root so
# these tests exercise the drift logic against their tmp_path corpus. SSOT:
# plans/active/issues/pm_root_content_resolution_breaks_checker_unit_test_fixtures_2026_08_10.md
def _fixture_pm_root(root: Path) -> Path:
    return root / "unified-trading-pm"


MOD._pm_root_or_legacy = _fixture_pm_root  # type: ignore[attr-defined]


def _write_workspace(
    root: Path,
    *,
    folder_repos: list[str],
    manifest_repos: dict[str, str],
    include_root_folder: bool = True,
    settings: dict | None = None,
) -> None:
    """Materialise a minimal workspace tree (canonical .code-workspace + manifest)."""
    pm = root / "unified-trading-pm"
    (pm / "cursor-configs").mkdir(parents=True)
    folders: list[dict] = []
    if include_root_folder:
        folders.append({"path": "../../", "name": "Workspace Root"})
    folders.extend({"path": f"../../{r}"} for r in folder_repos)
    ws: dict = {"folders": folders}
    if settings is not None:
        ws["settings"] = settings
    (pm / "cursor-configs" / "unified-trading-system-repos.code-workspace").write_text(json.dumps(ws), encoding="utf-8")
    manifest = {"repositories": {n: {"status": s} for n, s in manifest_repos.items()}}
    (pm / "workspace-manifest.json").write_text(json.dumps(manifest), encoding="utf-8")


class TestRepoNameFromPath:
    def test_workspace_root_variants_map_to_none(self) -> None:
        for p in (".", "..", "../", "../..", "../../", "./"):
            assert MOD._repo_name_from_path(p) is None

    def test_relative_and_bare_paths_map_to_bare_name(self) -> None:
        assert MOD._repo_name_from_path("../../strategy-service") == "strategy-service"
        assert MOD._repo_name_from_path("strategy-service") == "strategy-service"


class TestCheck:
    def test_clean_workspace_passes(self, tmp_path: Path) -> None:
        _write_workspace(
            tmp_path,
            folder_repos=["strategy-service", "execution-service"],
            manifest_repos={
                "strategy-service": "active",
                "execution-service": "scaffolded",
            },
        )
        assert MOD.check(tmp_path) == 0

    def test_missing_active_repo_fails(self, tmp_path: Path) -> None:
        _write_workspace(
            tmp_path,
            folder_repos=["strategy-service"],
            manifest_repos={"strategy-service": "active", "greeks-service": "active"},
        )
        assert MOD.check(tmp_path) == 1

    def test_stale_archived_repo_listed_fails(self, tmp_path: Path) -> None:
        _write_workspace(
            tmp_path,
            folder_repos=["strategy-service", "risk-and-exposure-service"],
            manifest_repos={
                "strategy-service": "active",
                "risk-and-exposure-service": "archived",
            },
        )
        assert MOD.check(tmp_path) == 1

    def test_unknown_repo_in_folders_fails(self, tmp_path: Path) -> None:
        _write_workspace(
            tmp_path,
            folder_repos=["strategy-service", "totally-made-up-service"],
            manifest_repos={"strategy-service": "active"},
        )
        assert MOD.check(tmp_path) == 1

    def test_consolidated_repo_treated_as_inactive(self, tmp_path: Path) -> None:
        _write_workspace(
            tmp_path,
            folder_repos=["features-service", "features-onchain-service"],
            manifest_repos={
                "features-service": "active",
                "features-onchain-service": "consolidated-into-features-service",
            },
        )
        assert MOD.check(tmp_path) == 1

    def test_missing_canonical_returns_2(self, tmp_path: Path) -> None:
        (tmp_path / "unified-trading-pm").mkdir()
        assert MOD.check(tmp_path) == 2

    def test_soft_settings_warning_does_not_block(self, tmp_path: Path) -> None:
        # An unknown repo in git.ignoredRepositories is warn-only — still exit 0.
        _write_workspace(
            tmp_path,
            folder_repos=["strategy-service"],
            manifest_repos={"strategy-service": "active"},
            settings={"git.ignoredRepositories": ["some-unknown-repo"]},
        )
        assert MOD.check(tmp_path) == 0
