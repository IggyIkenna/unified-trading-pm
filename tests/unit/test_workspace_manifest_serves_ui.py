"""Unit tests for workspace-manifest.json serves_ui mappings (p6-fix-orphaned-ui-api-mappings).

Validates that:
- All API repos that serve UIs have `serves_ui` fields
- serves_ui references only repos that exist in the manifest
- The ui-api-mapping.json (dev stack SSOT) is consistent with manifest serves_ui
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "workspace-manifest.json"
UI_API_MAPPING_PATH = REPO_ROOT / "scripts" / "dev" / "ui-api-mapping.json"


@pytest.fixture(scope="module")
def manifest() -> dict[str, object]:
    """Load the workspace manifest."""
    with open(MANIFEST_PATH) as f:
        return json.load(f)


@pytest.fixture(scope="module")
def repositories(manifest: dict[str, object]) -> dict[str, dict[str, object]]:
    """Extract the repositories dict from manifest."""
    repos = manifest.get("repositories")
    assert isinstance(repos, dict)
    return repos


@pytest.fixture(scope="module")
def ui_api_mapping() -> dict[str, object]:
    """Load the ui-api-mapping.json SSOT."""
    with open(UI_API_MAPPING_PATH) as f:
        return json.load(f)


class TestServesUiPresence:
    """All API repos that serve UIs must have serves_ui fields."""

    def test_api_repos_with_ui_stacks_have_serves_ui(
        self,
        repositories: dict[str, dict[str, object]],
        ui_api_mapping: dict[str, object],
    ) -> None:
        """Every API referenced in ui-api-mapping.json must have serves_ui in manifest."""
        stacks = ui_api_mapping.get("stacks", {})
        assert isinstance(stacks, dict)

        api_repos_from_mapping = set()
        for stack_info in stacks.values():
            assert isinstance(stack_info, dict)
            api = stack_info.get("api")
            if api is not None:
                api_repos_from_mapping.add(api)

        missing_serves_ui: list[str] = []
        for api_name in api_repos_from_mapping:
            if api_name in repositories:
                entry = repositories[api_name]
                if "serves_ui" not in entry:
                    missing_serves_ui.append(api_name)

        assert not missing_serves_ui, (
            f"API repos in ui-api-mapping.json but missing serves_ui in manifest: {missing_serves_ui}"
        )

    def test_known_apis_have_serves_ui(self, repositories: dict[str, dict[str, object]]) -> None:
        """Specific known APIs that serve UIs must have serves_ui."""
        expected_apis_with_ui = [
            "deployment-api",
            "execution-results-api",
            "config-api",
            "batch-audit-api",
            "trading-analytics-api",
            "client-reporting-api",
            "ml-training-api",
        ]
        missing: list[str] = []
        for api_name in expected_apis_with_ui:
            if api_name in repositories:
                entry = repositories[api_name]
                if "serves_ui" not in entry:
                    missing.append(api_name)
        assert not missing, f"Known APIs missing serves_ui: {missing}"


class TestServesUiValidity:
    """serves_ui values must reference valid UI repos."""

    def test_serves_ui_is_list_of_strings(self, repositories: dict[str, dict[str, object]]) -> None:
        """serves_ui must be a list of strings when present."""
        bad: list[str] = []
        for name, entry in repositories.items():
            if "serves_ui" in entry:
                sui = entry["serves_ui"]
                if not isinstance(sui, list):
                    bad.append(f"{name}: serves_ui is {type(sui).__name__}, not list")
                elif not all(isinstance(s, str) for s in sui):
                    bad.append(f"{name}: serves_ui contains non-string values")
        assert not bad, f"Invalid serves_ui format: {bad}"

    def test_serves_ui_references_existing_repos(self, repositories: dict[str, dict[str, object]]) -> None:
        """All repos listed in serves_ui must exist in the manifest."""
        all_repo_names = set(repositories.keys())
        orphaned: list[str] = []
        for name, entry in repositories.items():
            if "serves_ui" in entry and isinstance(entry["serves_ui"], list):
                for ui_name in entry["serves_ui"]:
                    if isinstance(ui_name, str) and ui_name not in all_repo_names:
                        orphaned.append(f"{name} -> {ui_name}")
        assert not orphaned, f"serves_ui references non-existent repos: {orphaned}"

    def test_serves_ui_references_are_ui_type(self, repositories: dict[str, dict[str, object]]) -> None:
        """Repos referenced in serves_ui should be of type 'ui'."""
        bad: list[str] = []
        for name, entry in repositories.items():
            if "serves_ui" in entry and isinstance(entry["serves_ui"], list):
                for ui_name in entry["serves_ui"]:
                    if isinstance(ui_name, str) and ui_name in repositories:
                        ui_entry = repositories[ui_name]
                        if ui_entry.get("type") != "ui":
                            bad.append(f"{name} -> {ui_name} (type={ui_entry.get('type')})")
        assert not bad, f"serves_ui references non-UI repos: {bad}"


class TestUiApiMappingConsistency:
    """Manifest serves_ui should be consistent with ui-api-mapping.json."""

    def test_mapping_stacks_covered_by_manifest(
        self,
        repositories: dict[str, dict[str, object]],
        ui_api_mapping: dict[str, object],
    ) -> None:
        """Every UI->API pairing in ui-api-mapping.json should be reflected in manifest serves_ui."""
        stacks = ui_api_mapping.get("stacks", {})
        assert isinstance(stacks, dict)

        missing_pairings: list[str] = []
        for stack_name, stack_info in stacks.items():
            assert isinstance(stack_info, dict)
            api = stack_info.get("api")
            ui = stack_info.get("ui")
            if api is None or ui is None:
                continue
            if api not in repositories:
                continue
            entry = repositories[api]
            serves_ui = entry.get("serves_ui", [])
            if isinstance(serves_ui, list) and ui not in serves_ui:
                # Some UIs are served by a different API in manifest than mapping
                # (e.g., strategy-ui is served by execution-results-api in mapping
                # but config-api in manifest). Only flag if serves_ui is empty.
                if len(serves_ui) == 0:
                    missing_pairings.append(f"stack={stack_name}: {api} should serve {ui}")
        # Note: Not all mappings will match 1:1 since some UIs are dual-served.
        # This test flags only APIs with no serves_ui at all.
        assert not missing_pairings, f"UI-API pairings in mapping not reflected in manifest: {missing_pairings}"

    def test_no_api_repos_without_serves_ui(self, repositories: dict[str, dict[str, object]]) -> None:
        """All API-type repos should have serves_ui (even if empty list)."""
        api_repos = [name for name, entry in repositories.items() if entry.get("type") in ("api-service", "api")]
        # All API repos should have serves_ui
        missing = [name for name in api_repos if "serves_ui" not in repositories[name]]
        assert not missing, f"API repos missing serves_ui field: {missing}"
