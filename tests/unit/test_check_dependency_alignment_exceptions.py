"""Tests for check-dependency-alignment.py's YAML-backed per-repo exceptions loader.

dependency_alignment_red_multi_repo_ceiling_drift_2026_07_13.md todo 3: migrated
PER_REPO_EXTERNAL_EXCEPTIONS from a hand-edited Python dict literal to
dependency-exceptions.yaml (a YAML list + a mandatory justification field). These
tests guard the loader's schema validation (fails loud, never silently drops an
exception) and the real fixture file's shape.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest
import yaml

SCRIPT_PATH = Path(__file__).resolve().parents[2] / "scripts" / "manifest" / "check-dependency-alignment.py"


def _load_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("check_dependency_alignment", SCRIPT_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _write_yaml(tmp_path: Path, content: dict[str, object]) -> Path:
    p = tmp_path / "dependency-exceptions.yaml"
    p.write_text(yaml.safe_dump(content), encoding="utf-8")
    return p


def test_real_exceptions_file_loads_and_matches_prior_dict_shape() -> None:
    """The real fixture, loaded through the real loader, produces the exact
    9-entry fastapi set the pre-migration hand-edited dict literal declared,
    plus whatever later, independently-justified entries have accrued since
    (each carrying its own justification/ssot/added fields, schema-validated
    by the loader — this test's job is the SHAPE, not a frozen entry count)."""
    mod = _load_module()
    exceptions = mod._load_per_repo_exceptions(mod.EXCEPTIONS_YAML_PATH)
    assert len(exceptions) == 13
    for repo in (
        "ml-service",
        "unified-trading-library",
        "alerting-service",
        "greeks-service",
        "market-tick-data-service",
        "deployment-api",
        "agent-orchestrator",
        "features-service",
        "unified-trading-api",
    ):
        assert exceptions[(repo, "fastapi")] == "fastapi>=0.115.0,<0.138.0"

    # CVE-2026-59881/-69243/-69244 aiohttp cluster (2026-08-04): repos ahead of the canonical
    # aiohttp>=3.14.1,<4.0.0 floor, which stays put pending its own separate fleet sweep.
    assert exceptions[("unified-trading-library", "aiohttp")] == "aiohttp>=3.14.3,<4.0.0"
    assert exceptions[("market-tick-data-service", "aiohttp")] == "aiohttp>=3.14.3,<4.0.0"
    assert exceptions[("unified-trading-pm", "aiohttp")] == "aiohttp>=3.14.3,<4.0.0"


def test_missing_file_returns_empty_dict(tmp_path: Path) -> None:
    mod = _load_module()
    assert mod._load_per_repo_exceptions(tmp_path / "does-not-exist.yaml") == {}


def test_missing_required_field_fails_loud(tmp_path: Path) -> None:
    mod = _load_module()
    path = _write_yaml(
        tmp_path,
        {
            "exceptions": [
                {"repo": "foo", "package": "bar", "spec": "bar>=1.0"}  # missing justification/ssot/added
            ]
        },
    )
    with pytest.raises(SystemExit):
        mod._load_per_repo_exceptions(path)


def test_duplicate_repo_package_pair_fails_loud(tmp_path: Path) -> None:
    mod = _load_module()
    entry = {
        "repo": "foo",
        "package": "bar",
        "spec": "bar>=1.0",
        "justification": "test",
        "ssot": ["plans/active/issues/fake.md"],
        "added": "2026-01-01",
    }
    path = _write_yaml(tmp_path, {"exceptions": [entry, dict(entry)]})
    with pytest.raises(SystemExit):
        mod._load_per_repo_exceptions(path)


def test_non_mapping_top_level_fails_loud(tmp_path: Path) -> None:
    mod = _load_module()
    path = tmp_path / "dependency-exceptions.yaml"
    path.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        mod._load_per_repo_exceptions(path)


def test_entry_not_a_mapping_fails_loud(tmp_path: Path) -> None:
    mod = _load_module()
    path = _write_yaml(tmp_path, {"exceptions": ["not-a-mapping"]})
    with pytest.raises(SystemExit):
        mod._load_per_repo_exceptions(path)
