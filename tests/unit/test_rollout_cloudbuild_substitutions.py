"""Unit tests for scripts/propagation/rollout-cloudbuild.py's substitutions guard.

Covers the P1 finding in plans/active/issues/
cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md: `_cloudbuild_markers()`
never reads `substitutions`, so the pre-existing "would drop content" guard could not
see a consumer-only substitution key (deployment-api's `_DEPLOY`/`_ROLLUP_JOB`/
`_ROLLUP_SVC`, absent from cloudbuild-api-template.yaml) and `--apply` would silently
render it away. `find_dropped_substitutions()` closes that gap as an INDEPENDENT check
from `find_dropped_markers()`/`_cloudbuild_markers()` — those two feed
check_cloudbuild_template_drift.py's baseline ratchet, and folding substitutions into
them would raise the drift count for every consumer with legitimate per-repo
substitutions, which needs an operator-sanctioned baseline re-seed per that doc's own
P1 todo. This guard only gates rollout-cloudbuild.py's own `--apply` write path.
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "propagation" / "rollout-cloudbuild.py"
    spec = importlib.util.spec_from_file_location("rollout_cloudbuild_under_test", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()

_TEMPLATE_RENDERED = """\
substitutions:
  _SERVICE_NAME: "deployment-api"
  _REGISTRY_REPO: "unified-trading-system"
steps:
  - id: build
    args: ["build", "${_SERVICE_NAME}"]
"""

_CONSUMER_WITH_EXTRA_SUBS = """\
substitutions:
  _SERVICE_NAME: "deployment-api"
  _REGISTRY_REPO: "unified-trading-system"
  _DEPLOY: "false"
  _ROLLUP_JOB: "uts-prod-data-status-rollup"
  _ROLLUP_SVC: "uts-prod-data-status-rollup-svc"
steps:
  - id: build
    args: ["build", "${_SERVICE_NAME}"]
"""


def test_dropped_consumer_only_substitution_keys_detected() -> None:
    dropped = MOD.find_dropped_substitutions(_CONSUMER_WITH_EXTRA_SUBS, _TEMPLATE_RENDERED)
    assert dropped is not None
    assert dropped == [
        "substitutions key dropped: _DEPLOY",
        "substitutions key dropped: _ROLLUP_JOB",
        "substitutions key dropped: _ROLLUP_SVC",
    ]


def test_no_drop_when_new_content_carries_every_key() -> None:
    dropped = MOD.find_dropped_substitutions(_TEMPLATE_RENDERED, _TEMPLATE_RENDERED)
    assert dropped == []


def test_unparseable_input_returns_none_conservatively() -> None:
    assert MOD.find_dropped_substitutions("not: [valid: yaml", _TEMPLATE_RENDERED) is None
    assert MOD.find_dropped_substitutions(_TEMPLATE_RENDERED, "not: [valid: yaml") is None


def test_substitutions_are_not_folded_into_cloudbuild_markers() -> None:
    """The drift-ratchet-facing marker categories must stay unchanged — this guard
    is deliberately independent so it never raises check_cloudbuild_template_drift.py's
    baseline count."""
    data = MOD._parse_cloudbuild_yaml(_CONSUMER_WITH_EXTRA_SUBS)
    assert data is not None
    markers = MOD._cloudbuild_markers(data)
    assert "substitutions" not in markers
    for marker_set in markers.values():
        assert not any("_DEPLOY" in m or "_ROLLUP" in m for m in marker_set)


def test_apply_write_guard_refuses_on_dropped_substitution(tmp_path, monkeypatch, capsys) -> None:
    """End-to-end: main() with --apply must refuse to write a consumer whose
    substitutions would be dropped, exiting non-zero and leaving the file untouched."""
    configs_dir = tmp_path / "configs"
    configs_dir.mkdir()
    api_template = configs_dir / "cloudbuild-api-template.yaml"
    api_template.write_text(
        'substitutions:\n  _SERVICE_NAME: "{{SERVICE_NAME}}"\n  _REGISTRY_REPO: "{{REGISTRY_REPO}}"\n'
        'steps:\n  - id: build\n    args: ["build", "${_SERVICE_NAME}"]\n',
        encoding="utf-8",
    )
    workspace_root = tmp_path / "workspace"
    repo_dir = workspace_root / "deployment-api"
    repo_dir.mkdir(parents=True)
    (repo_dir / "cloudbuild.yaml").write_text(_CONSUMER_WITH_EXTRA_SUBS, encoding="utf-8")
    manifest_path = tmp_path / "workspace-manifest.json"
    manifest_path.write_text(
        '{"repositories": {"deployment-api": {"type": "api-service"}}}',
        encoding="utf-8",
    )

    monkeypatch.setattr(MOD, "CONFIGS_DIR", configs_dir)
    monkeypatch.setattr(MOD, "MANIFEST_PATH", manifest_path)
    monkeypatch.setattr(MOD, "WORKSPACE_ROOT", workspace_root)
    monkeypatch.setattr(
        MOD,
        "load_substitution_checker",
        lambda: types.SimpleNamespace(scan_cloudbuild_text=lambda content, label: []),
    )
    monkeypatch.setattr(sys, "argv", ["rollout-cloudbuild.py", "--apply", "--repo", "deployment-api"])

    exit_code = MOD.main()

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "substitutions key dropped: _DEPLOY" in captured.err
    assert (repo_dir / "cloudbuild.yaml").read_text(encoding="utf-8") == _CONSUMER_WITH_EXTRA_SUBS
