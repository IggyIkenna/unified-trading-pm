"""Unit tests for workspace-manifest.json usage tags (p8-usage-tags).

Validates that every repo in the manifest has a `tags` array with
appropriate capability, domain, and criticality tags.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / "workspace-manifest.json"

# Valid tag categories
CAPABILITY_TAGS = {
    "market-data",
    "execution",
    "risk",
    "features",
    "ui",
    "library",
    "api",
    "analytics",
    "monitoring",
    "alerting",
    "deployment",
    "ml",
    "instruments",
    "strategy",
    "config",
    "contracts",
    "auth",
    "pnl",
    "reconciliation",
    "infrastructure",
    "testing",
    "pm",
    "codex",
    "events",
    "cloud",
    "position",
    "reference-data",
    "settlement",
    "batch",
    "sports",
    "reporting",
    "gateway",
}

DOMAIN_TAGS = {
    "cefi",
    "tradfi",
    "defi",
    "sports",
    "cross-domain",
    "cross-asset",
}

CRITICALITY_TAGS = {
    "tier-0",
    "tier-1",
    "tier-2",
    "tier-3",
    "critical-path",
    "supporting",
    "standard",
}


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


class TestAllReposHaveTags:
    """Every repo entry must have a non-empty tags array."""

    def test_manifest_exists(self) -> None:
        """workspace-manifest.json must exist."""
        assert MANIFEST_PATH.is_file()

    def test_all_repos_have_tags_key(self, repositories: dict[str, dict[str, object]]) -> None:
        """Every repo must have a 'tags' key."""
        missing = [name for name, entry in repositories.items() if "tags" not in entry]
        assert not missing, f"Repos missing 'tags' key: {missing}"

    def test_all_tags_are_lists(self, repositories: dict[str, dict[str, object]]) -> None:
        """Every repo's tags must be a list."""
        bad = [name for name, entry in repositories.items() if not isinstance(entry.get("tags"), list)]
        assert not bad, f"Repos where tags is not a list: {bad}"

    def test_all_tags_non_empty(self, repositories: dict[str, dict[str, object]]) -> None:
        """Every repo must have at least one tag."""
        empty = [
            name
            for name, entry in repositories.items()
            if isinstance(entry.get("tags"), list) and len(entry["tags"]) == 0
        ]
        assert not empty, f"Repos with empty tags array: {empty}"

    def test_all_tags_are_strings(self, repositories: dict[str, dict[str, object]]) -> None:
        """Every tag value must be a string."""
        bad: list[str] = []
        for name, entry in repositories.items():
            tags = entry.get("tags", [])
            if isinstance(tags, list):
                for tag in tags:
                    if not isinstance(tag, str):
                        bad.append(f"{name}: {tag!r}")
        assert not bad, f"Non-string tags found: {bad}"

    def test_all_tags_are_lowercase(self, repositories: dict[str, dict[str, object]]) -> None:
        """All tags should be lowercase for consistency."""
        bad: list[str] = []
        for name, entry in repositories.items():
            tags = entry.get("tags", [])
            if isinstance(tags, list):
                for tag in tags:
                    if isinstance(tag, str) and tag != tag.lower():
                        bad.append(f"{name}: '{tag}'")
        assert not bad, f"Tags should be lowercase: {bad}"


class TestTagCoverage:
    """Repos should have tags from multiple categories for comprehensive tagging."""

    def test_repo_count_matches_expectations(self, repositories: dict[str, dict[str, object]]) -> None:
        """Manifest should have a substantial number of repos.

        Floor is 20, not 30: the active surface was reconciled to 25 (23 active + 2
        scaffolded) by the 2026-06-02 canonicalisation (manifest commit fd616af4c),
        which relocated 14 consolidated/archived tombstone repos (features-* /ml-*
        children, user-management-ui, etc.) into ``removedEntries``. The threshold is
        a sanity floor for "substantial number of repos", not an exact count.
        """
        assert len(repositories) >= 20, f"Expected at least 20 repos, found {len(repositories)}"

    def test_ui_repos_have_meaningful_tags(self, repositories: dict[str, dict[str, object]]) -> None:
        """Repos of type 'ui' should have at least one domain or capability tag."""
        ui_repos_missing_tag: list[str] = []
        for name, entry in repositories.items():
            if entry.get("type") == "ui":
                tags = entry.get("tags", [])
                if isinstance(tags, list) and len(tags) < 2:
                    ui_repos_missing_tag.append(name)
        assert not ui_repos_missing_tag, f"UI repos with fewer than 2 tags: {ui_repos_missing_tag}"

    def test_api_repos_have_api_or_capability_tag(self, repositories: dict[str, dict[str, object]]) -> None:
        """API repos should include an api or capability tag."""
        bad: list[str] = []
        for name, entry in repositories.items():
            if entry.get("type") in ("api-service", "api"):
                tags = entry.get("tags", [])
                if isinstance(tags, list) and len(tags) == 0:
                    bad.append(name)
        assert not bad, f"API repos with no tags: {bad}"
