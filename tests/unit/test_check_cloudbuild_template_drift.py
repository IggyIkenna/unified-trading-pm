"""Unit tests for scripts/quality_gates/check_cloudbuild_template_drift.py.

Positive (a consumer carrying content its mapped template lacks is flagged) +
negative (a consumer that renders clean is not) + baseline-ratchet semantics +
the "template lags repo" done-when criterion, per
plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md [INFRA] P2.

Templates + the manifest are synthetic, built in tmp_path and wired in via
monkeypatching the loaded rollout-cloudbuild module's own CONFIGS_DIR /
MANIFEST_PATH constants — this exercises the REAL generate_cloudbuild() /
find_dropped_markers() rendering + diff logic (never a re-implementation),
scoped to a throwaway fixture instead of the live fleet.
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
    path = repo_root / "scripts" / "quality_gates" / "check_cloudbuild_template_drift.py"
    spec = importlib.util.spec_from_file_location("check_cloudbuild_template_drift", path)
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
    args:
      - "-t"
      - "asia-northeast1-docker.pkg.dev/$PROJECT_ID/${_REGISTRY_REPO}/${_SERVICE_NAME}:$SHORT_SHA"
  - id: push
    args: ["push", "{{SERVICE_NAME}}"]
"""

_API_TEMPLATE = """\
substitutions:
  _SERVICE_NAME: "{{SERVICE_NAME}}"
  _REGISTRY_REPO: "{{REGISTRY_REPO}}"
steps:
  - id: build
    args: ["build", "${_SERVICE_NAME}"]
"""


def _write_configs(tmp_path: Path) -> Path:
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    (configs_dir / "cloudbuild-service-template.yaml").write_text(_SERVICE_TEMPLATE, encoding="utf-8")
    (configs_dir / "cloudbuild-api-template.yaml").write_text(_API_TEMPLATE, encoding="utf-8")
    return configs_dir


def _write_manifest(tmp_path: Path, repos: dict) -> Path:
    manifest_path = tmp_path / "workspace-manifest.json"
    manifest_path.write_text(json.dumps({"repositories": repos}), encoding="utf-8")
    return manifest_path


def _rendered_service_content(repo_name: str) -> str:
    """The rendered service template for a clean (non-drifted) consumer —
    hand-derived the same way generate_cloudbuild() substitutes, so a test
    fixture consumer file can be built to match it exactly byte-for-byte in
    content (aside from cosmetic differences find_dropped_markers ignores)."""
    return _SERVICE_TEMPLATE.replace('_SERVICE_NAME: "REPLACE_ME"', f'_SERVICE_NAME: "{repo_name}"').replace(
        "{{SERVICE_NAME}}", repo_name
    )


@pytest.fixture
def rollout_env(tmp_path: Path):
    """Yields (rollout_mod, workspace_root, configs_dir, manifest_path) with a
    fresh load of the rollout-cloudbuild module repointed at synthetic
    configs/manifest under tmp_path."""
    workspace_root = tmp_path / "workspace"
    workspace_root.mkdir()
    configs_dir = _write_configs(tmp_path)
    rollout_mod = MOD.load_rollout_module()
    yield rollout_mod, workspace_root, configs_dir


def _make_consumer(workspace_root: Path, repo_name: str, content: str) -> Path:
    repo_dir = workspace_root / repo_name
    repo_dir.mkdir(parents=True, exist_ok=True)
    path = repo_dir / "cloudbuild.yaml"
    path.write_text(content, encoding="utf-8")
    return path


# ── scan_drift — positive (drift detected) ───────────────────────────────────


class TestScanDriftPositive:
    def test_consumer_extra_step_flagged(self, tmp_path: Path, rollout_env) -> None:
        rollout_mod, workspace_root, configs_dir = rollout_env
        rollout_mod.CONFIGS_DIR = configs_dir
        rollout_mod.MANIFEST_PATH = _write_manifest(tmp_path, {"repo-a": {"type": "service"}})
        clean = _rendered_service_content("repo-a")
        # The live consumer carries an EXTRA step the template render lacks.
        live = clean.replace(
            "  - id: push\n",
            '  - id: extra-step\n    args: ["echo", "template does not know this"]\n  - id: push\n',
        )
        _make_consumer(workspace_root, "repo-a", live)
        drift, unparseable = MOD.scan_drift(rollout_mod, workspace_root)
        assert unparseable == []
        assert drift["repo-a"].count >= 1
        assert any("extra-step" in m for m in drift["repo-a"].dropped)

    def test_api_template_covered_not_just_service(self, tmp_path: Path, rollout_env) -> None:
        rollout_mod, workspace_root, configs_dir = rollout_env
        rollout_mod.CONFIGS_DIR = configs_dir
        rollout_mod.MANIFEST_PATH = _write_manifest(tmp_path, {"repo-api": {"type": "api-service"}})
        rendered = rollout_mod.generate_cloudbuild("repo-api", {"type": "api-service"}, deploy_via_dispatch=False)
        assert rendered is not None
        live = rendered.replace(
            "steps:\n",
            'steps:\n  - id: extra-secret-step\n    secretEnv: ["GH_PAT"]\n',
        )
        _make_consumer(workspace_root, "repo-api", live)
        drift, _ = MOD.scan_drift(rollout_mod, workspace_root)
        assert drift["repo-api"].template == "cloudbuild-api-template.yaml"
        assert drift["repo-api"].count >= 1


# ── scan_drift — negative (clean render, correctly excluded scopes) ──────────


class TestScanDriftNegative:
    def test_clean_consumer_zero_drift(self, tmp_path: Path, rollout_env) -> None:
        rollout_mod, workspace_root, configs_dir = rollout_env
        rollout_mod.CONFIGS_DIR = configs_dir
        rollout_mod.MANIFEST_PATH = _write_manifest(tmp_path, {"repo-a": {"type": "service"}})
        _make_consumer(workspace_root, "repo-a", _rendered_service_content("repo-a"))
        drift, unparseable = MOD.scan_drift(rollout_mod, workspace_root)
        assert unparseable == []
        assert drift["repo-a"].count == 0

    def test_library_type_excluded(self, tmp_path: Path, rollout_env) -> None:
        rollout_mod, workspace_root, configs_dir = rollout_env
        rollout_mod.CONFIGS_DIR = configs_dir
        rollout_mod.MANIFEST_PATH = _write_manifest(tmp_path, {"repo-lib": {"type": "library"}})
        _make_consumer(workspace_root, "repo-lib", "steps: []\n")
        drift, _ = MOD.scan_drift(rollout_mod, workspace_root)
        assert "repo-lib" not in drift

    def test_unmapped_type_excluded(self, tmp_path: Path, rollout_env) -> None:
        rollout_mod, workspace_root, configs_dir = rollout_env
        rollout_mod.CONFIGS_DIR = configs_dir
        rollout_mod.MANIFEST_PATH = _write_manifest(tmp_path, {"repo-tool": {"type": "tool"}})
        _make_consumer(workspace_root, "repo-tool", "steps: []\n")
        drift, _ = MOD.scan_drift(rollout_mod, workspace_root)
        assert "repo-tool" not in drift

    def test_missing_consumer_file_excluded(self, tmp_path: Path, rollout_env) -> None:
        rollout_mod, workspace_root, configs_dir = rollout_env
        rollout_mod.CONFIGS_DIR = configs_dir
        rollout_mod.MANIFEST_PATH = _write_manifest(tmp_path, {"repo-a": {"type": "service"}})
        # No cloudbuild.yaml written for repo-a at all.
        drift, unparseable = MOD.scan_drift(rollout_mod, workspace_root)
        assert "repo-a" not in drift
        assert unparseable == []

    def test_skip_repos_excluded(self, tmp_path: Path, rollout_env) -> None:
        rollout_mod, workspace_root, configs_dir = rollout_env
        rollout_mod.CONFIGS_DIR = configs_dir
        rollout_mod.MANIFEST_PATH = _write_manifest(tmp_path, {"unified-trading-pm": {"type": "devops"}})
        drift, _ = MOD.scan_drift(rollout_mod, workspace_root)
        assert drift == {}

    def test_repo_filter_scopes_to_one_repo(self, tmp_path: Path, rollout_env) -> None:
        rollout_mod, workspace_root, configs_dir = rollout_env
        rollout_mod.CONFIGS_DIR = configs_dir
        rollout_mod.MANIFEST_PATH = _write_manifest(
            tmp_path, {"repo-a": {"type": "service"}, "repo-b": {"type": "service"}}
        )
        _make_consumer(workspace_root, "repo-a", _rendered_service_content("repo-a"))
        _make_consumer(workspace_root, "repo-b", _rendered_service_content("repo-b"))
        drift, _ = MOD.scan_drift(rollout_mod, workspace_root, repo_filter="repo-a")
        assert set(drift.keys()) == {"repo-a"}


# ── baseline-ratchet semantics via main() ────────────────────────────────────


class TestBaselineRatchet:
    def _run(self, tmp_path: Path, configs_dir: Path, manifest_path: Path, baseline: Path, extra: list | None = None):
        argv = [
            "--workspace-root",
            str(tmp_path / "workspace"),
            "--configs-dir",
            str(configs_dir),
            "--manifest-path",
            str(manifest_path),
            "--baseline-file",
            str(baseline),
        ]
        if extra:
            argv += extra
        return MOD.main(argv)

    def test_over_baseline_fails(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir()
        configs_dir = _write_configs(tmp_path)
        manifest_path = _write_manifest(tmp_path, {"repo-a": {"type": "service"}})
        live = _rendered_service_content("repo-a").replace(
            "  - id: push\n", '  - id: extra-step\n    args: ["x"]\n  - id: push\n'
        )
        _make_consumer(workspace_root, "repo-a", live)
        baseline = tmp_path / "bl.yaml"
        rc = self._run(tmp_path, configs_dir, manifest_path, baseline)
        assert rc == 1

    def test_at_baseline_passes(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir()
        configs_dir = _write_configs(tmp_path)
        manifest_path = _write_manifest(tmp_path, {"repo-a": {"type": "service"}})
        live = _rendered_service_content("repo-a").replace(
            "  - id: push\n", '  - id: extra-step\n    args: ["x"]\n  - id: push\n'
        )
        _make_consumer(workspace_root, "repo-a", live)
        baseline = tmp_path / "bl.yaml"
        # extra-step contributes 2 markers: the step itself + its one arg.
        baseline.write_text("repos:\n  repo-a:\n    count: 2\n", encoding="utf-8")
        rc = self._run(tmp_path, configs_dir, manifest_path, baseline)
        assert rc == 0

    def test_clean_repo_passes_at_zero_default(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir()
        configs_dir = _write_configs(tmp_path)
        manifest_path = _write_manifest(tmp_path, {"repo-a": {"type": "service"}})
        _make_consumer(workspace_root, "repo-a", _rendered_service_content("repo-a"))
        baseline = tmp_path / "bl.yaml"
        rc = self._run(tmp_path, configs_dir, manifest_path, baseline)
        assert rc == 0

    def test_synthetic_template_lags_repo_case_fails_at_seeded_baseline(self, tmp_path: Path) -> None:
        """Done-when criterion: the checker runs clean once the real (today's)
        drift is baselined, then fails the moment the template falls FURTHER
        behind (a synthetic new template-lags-repo case)."""
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir()
        configs_dir = _write_configs(tmp_path)
        manifest_path = _write_manifest(tmp_path, {"repo-a": {"type": "service"}})
        live = _rendered_service_content("repo-a").replace(
            "  - id: push\n", '  - id: pre-existing-drift\n    args: ["x"]\n  - id: push\n'
        )
        _make_consumer(workspace_root, "repo-a", live)
        baseline = tmp_path / "bl.yaml"
        # Seed the baseline at today's real (pre-existing) drift.
        rc = self._run(tmp_path, configs_dir, manifest_path, baseline, extra=["--update-baseline"])
        assert rc == 0
        rc = self._run(tmp_path, configs_dir, manifest_path, baseline)
        assert rc == 0
        # The consumer fixes something else the template still doesn't know —
        # a brand-new synthetic template-lags-repo divergence.
        live2 = live.replace(
            "  - id: push\n", '  - id: new-fix-template-does-not-know\n    args: ["y"]\n  - id: push\n'
        )
        _make_consumer(workspace_root, "repo-a", live2)
        rc = self._run(tmp_path, configs_dir, manifest_path, baseline)
        assert rc == 1

    def test_update_baseline_clamps_down_never_up(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir()
        configs_dir = _write_configs(tmp_path)
        manifest_path = _write_manifest(tmp_path, {"repo-a": {"type": "service"}})
        live = _rendered_service_content("repo-a").replace(
            "  - id: push\n",
            '  - id: extra-1\n    args: ["a"]\n  - id: extra-2\n    args: ["b"]\n  - id: push\n',
        )
        _make_consumer(workspace_root, "repo-a", live)
        baseline = tmp_path / "bl.yaml"
        baseline.write_text("repos:\n  repo-a:\n    count: 1\n", encoding="utf-8")
        rc = self._run(tmp_path, configs_dir, manifest_path, baseline, extra=["--update-baseline"])
        assert rc == 0
        reloaded = MOD.load_baseline(baseline)
        assert reloaded.allowed("repo-a") == 1  # clamped to the prior baseline, not raised to 2

    def test_unparseable_consumer_fails_unconditionally(self, tmp_path: Path) -> None:
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir()
        configs_dir = _write_configs(tmp_path)
        manifest_path = _write_manifest(tmp_path, {"repo-a": {"type": "service"}})
        _make_consumer(workspace_root, "repo-a", "not: [valid, yaml: :::\n")
        baseline = tmp_path / "bl.yaml"
        rc = self._run(tmp_path, configs_dir, manifest_path, baseline)
        assert rc == 1
