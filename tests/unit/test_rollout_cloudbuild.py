"""Unit tests for scripts/propagation/rollout-cloudbuild.py's substitutions
would-drop-content guard.

Covers the P1 gap from
plans/active/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md:
``_cloudbuild_markers()`` never reads ``substitutions``, so a live consumer's
consumer-only substitution keys were invisible to the would-drop-content guard
— an ``--apply`` run could silently render them away. ``find_dropped_substitution_keys()``
closes that gap as a SEPARATE guard (not folded into ``_cloudbuild_markers()``/
``find_dropped_markers()``, which check_cloudbuild_template_drift.py's
baseline-gated ratchet also reuses — folding it in there would raise that
ratchet's count for every repo already carrying legitimate per-repo
substitutions, requiring an operator-sanctioned baseline re-seed this fix does
not need).

Templates + the manifest are synthetic, built in tmp_path and wired in via
monkeypatching the loaded module's own CONFIGS_DIR / MANIFEST_PATH /
WORKSPACE_ROOT constants — mirrors tests/unit/test_check_cloudbuild_template_drift.py's
fixture pattern, scoped to a throwaway fixture instead of the live fleet.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "propagation" / "rollout-cloudbuild.py"
    spec = importlib.util.spec_from_file_location("rollout_cloudbuild", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()

_SERVICE_TEMPLATE = """\
substitutions:
  _SERVICE_NAME: "REPLACE_ME"
  _REGISTRY_REPO: "REPLACE_ME"
  _PKG_NAME: "REPLACE_ME"
steps:
  - id: build
    args: ["build", "${_SERVICE_NAME}"]
"""


def _rendered_service_content(repo_name: str) -> str:
    """Mirrors generate_cloudbuild()'s own "service" repo_type substitution
    (SERVICE_NAME + REGISTRY_REPO + PKG_NAME) so a hand-built fixture matches
    the real render byte-for-byte — a partial mirror here previously left
    ``_PKG_NAME: "REPLACE_ME"`` unreplaced, which made a later
    ``.replace('_PKG_NAME: "<repo>"\\n', ...)`` silently no-op (target string
    never matched) instead of injecting the intended consumer-only key."""
    pkg_name = repo_name.replace("-", "_")
    return (
        _SERVICE_TEMPLATE.replace('_SERVICE_NAME: "REPLACE_ME"', f'_SERVICE_NAME: "{repo_name}"')
        .replace('_REGISTRY_REPO: "REPLACE_ME"', f'_REGISTRY_REPO: "{MOD.REGISTRY_REPO}"')
        .replace('_PKG_NAME: "REPLACE_ME"', f'_PKG_NAME: "{pkg_name}"')
    )


def _write_configs(tmp_path: Path) -> Path:
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    (configs_dir / "cloudbuild-service-template.yaml").write_text(_SERVICE_TEMPLATE, encoding="utf-8")
    return configs_dir


def _write_manifest(tmp_path: Path, repos: dict) -> Path:
    manifest_path = tmp_path / "workspace-manifest.json"
    manifest_path.write_text(json.dumps({"repositories": repos}), encoding="utf-8")
    return manifest_path


# ── find_dropped_substitution_keys() — unit level ────────────────────────────


class TestFindDroppedSubstitutionKeys:
    def test_consumer_only_key_flagged(self) -> None:
        rendered = _rendered_service_content("repo-a")
        live = rendered.replace('_PKG_NAME: "repo_a"\n', '_PKG_NAME: "repo_a"\n  _DEPLOY: "true"\n')
        assert live != rendered  # guard against the target string silently not matching
        dropped = MOD.find_dropped_substitution_keys(live, rendered)
        assert dropped == ["substitutions key dropped: _DEPLOY"]

    def test_clean_no_drop(self) -> None:
        content = _rendered_service_content("repo-a")
        assert MOD.find_dropped_substitution_keys(content, content) == []

    def test_new_template_key_not_flagged_as_dropped(self) -> None:
        """The render gaining a NEW substitution key the live file lacks is not
        a drop — only live-carries-but-render-lacks counts."""
        live = _rendered_service_content("repo-a")
        rendered = live.replace('_PKG_NAME: "repo_a"\n', '_PKG_NAME: "repo_a"\n  _NEW_KEY: "x"\n')
        assert rendered != live  # guard against the target string silently not matching
        assert MOD.find_dropped_substitution_keys(live, rendered) == []

    def test_unparseable_live_returns_none(self) -> None:
        rendered = _rendered_service_content("repo-a")
        assert MOD.find_dropped_substitution_keys("not: [valid, yaml: :::\n", rendered) is None

    def test_unparseable_rendered_returns_none(self) -> None:
        live = _rendered_service_content("repo-a")
        assert MOD.find_dropped_substitution_keys(live, "not: [valid, yaml: :::\n") is None

    def test_no_substitutions_block_is_empty_not_error(self) -> None:
        assert MOD.find_dropped_substitution_keys("steps: []\n", "steps: []\n") == []


# ── main() --apply — integration level ───────────────────────────────────────


@pytest.fixture
def rollout_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    configs_dir = _write_configs(tmp_path)
    manifest_path = _write_manifest(tmp_path, {"repo-a": {"type": "service"}})
    monkeypatch.setattr(MOD, "CONFIGS_DIR", configs_dir)
    monkeypatch.setattr(MOD, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(MOD, "WORKSPACE_ROOT", workspace_root)
    return workspace_root


def _make_consumer(workspace_root: Path, repo_name: str, content: str) -> Path:
    repo_dir = workspace_root / repo_name
    repo_dir.mkdir(parents=True, exist_ok=True)
    path = repo_dir / "cloudbuild.yaml"
    path.write_text(content, encoding="utf-8")
    return path


class TestApplyRefusesToDropSubstitutions:
    def test_apply_refuses_when_consumer_only_substitution_would_be_dropped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rollout_env: Path
    ) -> None:
        workspace_root = rollout_env
        rendered = _rendered_service_content("repo-a")
        live = rendered.replace('_PKG_NAME: "repo_a"\n', '_PKG_NAME: "repo_a"\n  _ROLLUP_SVC: "uts-prod-rollup-svc"\n')
        assert live != rendered  # guard against the target string silently not matching
        consumer_path = _make_consumer(workspace_root, "repo-a", live)
        monkeypatch.setattr(sys, "argv", ["rollout-cloudbuild.py", "--apply", "--repo", "repo-a"])
        rc = MOD.main()
        assert rc == 1
        # Refused to write — the live file (and its consumer-only key) is untouched.
        assert consumer_path.read_text(encoding="utf-8") == live

    def test_apply_writes_when_nothing_would_be_dropped(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, rollout_env: Path
    ) -> None:
        workspace_root = rollout_env
        clean = _rendered_service_content("repo-a")
        _make_consumer(workspace_root, "repo-a", clean)
        monkeypatch.setattr(sys, "argv", ["rollout-cloudbuild.py", "--apply", "--repo", "repo-a"])
        rc = MOD.main()
        assert rc == 0
