"""Tests for scripts/manifest/generate_workspace_dag.py.

Verifies manifest parsing, layout logic, SVG generation, and XML validity.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

# scripts/manifest/ is on extraPaths for basedpyright; add at runtime for pytest too
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "manifest"))

from generate_workspace_dag import (  # noqa: E402, I001
    JsonDict,
    LayoutEntry,
    RepoEntry,
    parse_level_descriptions,
    parse_repos,
    band_height,
    box_width,
    generate,
    generate_svg,
    layout_rows,
)


# --- Fixtures ---


def _minimal_manifest() -> JsonDict:
    """Minimal valid manifest with 2 levels and 3 repos."""
    return {
        "topologicalOrder": {
            "levels": [
                {"level": 0, "description": "Root"},
                {"level": 1, "description": "Libraries"},
            ],
        },
        "repositories": {
            "repo-a": {
                "merge_level": 0,
                "type": "infrastructure",
                "version": "0.1.0",
                "status": "active",
            },
            "repo-b": {
                "merge_level": 1,
                "type": "library",
                "version": "0.2.0",
                "status": "active",
            },
            "repo-c": {
                "merge_level": 1,
                "type": "service",
                "version": "0.3.0",
                "status": "planned",
            },
        },
    }


def _manifest_with_ampersand() -> JsonDict:
    """Manifest with special XML characters in descriptions."""
    return {
        "topologicalOrder": {
            "levels": [
                {"level": 0, "description": "Standards & codex"},
            ],
        },
        "repositories": {
            "test-repo": {
                "merge_level": 0,
                "type": "library",
                "version": "0.1.0",
                "status": "active",
            },
        },
    }


def _manifest_with_deprecated() -> JsonDict:
    """Manifest with deprecated repos (null and negative merge_level)."""
    return {
        "topologicalOrder": {
            "levels": [
                {"level": 0, "description": "Active"},
            ],
        },
        "repositories": {
            "active-repo": {
                "merge_level": 0,
                "type": "service",
                "version": "0.1.0",
                "status": "active",
            },
            "deprecated-null": {
                "merge_level": None,
                "type": "service",
                "version": "0.1.0",
                "status": "deprecated",
            },
            "deprecated-neg": {
                "merge_level": -1,
                "type": "service",
                "version": "0.1.0",
                "status": "deprecated",
            },
        },
    }


# --- box_width ---


class TestBoxWidth:
    """Tests for box_width()."""

    def test_short_name_uses_minimum(self) -> None:
        """Short names should use BOX_MIN_W."""
        assert box_width("ab") >= 130

    def test_long_name_scales(self) -> None:
        """Long names should exceed the minimum."""
        result = box_width("unified-trading-deployment-v3")
        assert result > 130

    def test_empty_name(self) -> None:
        """Empty name should still return minimum width."""
        assert box_width("") == 130


# --- layout_rows ---


class TestLayoutRows:
    """Tests for layout_rows()."""

    def test_single_repo(self) -> None:
        """Single repo should produce one row with one entry."""
        repos = [RepoEntry("test-repo", "0.1.0", "lib")]
        rows = layout_rows(repos)
        assert len(rows) == 1
        assert len(rows[0]) == 1
        assert rows[0][0].name == "test-repo"

    def test_entries_are_layout_entries(self) -> None:
        """Each entry should be a LayoutEntry with x and width set."""
        repos = [RepoEntry("a", "0.1.0", "lib"), RepoEntry("b", "0.2.0", "svc")]
        rows = layout_rows(repos)
        for row in rows:
            for entry in row:
                assert isinstance(entry, LayoutEntry)
                assert entry.x >= 70  # CANVAS_L
                assert entry.width >= 130  # BOX_MIN_W

    def test_wraps_to_next_row(self) -> None:
        """Many repos should wrap to multiple rows."""
        repos = [RepoEntry(f"repo-{i:03d}", "0.1.0", "lib") for i in range(30)]
        rows = layout_rows(repos)
        assert len(rows) > 1
        total = sum(len(r) for r in rows)
        assert total == 30

    def test_empty_input(self) -> None:
        """Empty list should produce empty rows."""
        assert layout_rows([]) == []


# --- band_height ---


class TestBandHeight:
    """Tests for band_height()."""

    def test_single_row(self) -> None:
        """Single row band height = header + padding + one row + padding."""
        row: list[LayoutEntry] = [LayoutEntry("a", "0.1.0", "lib", 70, 130)]
        result = band_height([row])
        # LVL_HDR_H(35) + LVL_PAD_T(12) + 1*ROW_H(48) + LVL_PAD_B(12) = 107
        assert result == 107

    def test_multiple_rows(self) -> None:
        """Multiple rows should increase height linearly."""
        row: list[LayoutEntry] = [LayoutEntry("a", "0.1.0", "lib", 70, 130)]
        h1 = band_height([row])
        h2 = band_height([row, row])
        assert h2 - h1 == 48  # ROW_H


# --- parse_level_descriptions ---


class TestParseLevelDescriptions:
    """Tests for parse_level_descriptions()."""

    def test_extracts_descriptions(self) -> None:
        """Should extract level descriptions from topologicalOrder."""
        result = parse_level_descriptions(_minimal_manifest())
        assert result[0] == "Root"
        assert result[1] == "Libraries"

    def test_fallback_to_topology(self) -> None:
        """Should fall back to topology.merge_order if topologicalOrder missing."""
        data: JsonDict = {
            "topology": {
                "merge_order": [
                    {"level": 0, "description": "Fallback L0"},
                ],
            },
            "repositories": {},
        }
        result = parse_level_descriptions(data)
        assert result[0] == "Fallback L0"

    def test_missing_description_uses_default(self) -> None:
        """Levels without description should get 'Level N' default."""
        data: JsonDict = {
            "topologicalOrder": {
                "levels": [{"level": 5}],
            },
            "repositories": {},
        }
        result = parse_level_descriptions(data)
        assert result[5] == "Level 5"

    def test_empty_manifest(self) -> None:
        """Empty manifest should return empty dict."""
        data: JsonDict = {"repositories": {}}
        result = parse_level_descriptions(data)
        assert result == {}


# --- parse_repos ---


class TestParseRepos:
    """Tests for parse_repos()."""

    def test_groups_by_level(self) -> None:
        """Should group repos by merge_level."""
        data = _minimal_manifest()
        repos_raw = data["repositories"]
        assert isinstance(repos_raw, dict)
        levels, _ = parse_repos(repos_raw)
        assert len(levels[0]) == 1  # repo-a
        assert len(levels[1]) == 2  # repo-b, repo-c

    def test_skips_deprecated(self) -> None:
        """Should skip repos with null or negative merge_level."""
        data = _manifest_with_deprecated()
        repos_raw = data["repositories"]
        assert isinstance(repos_raw, dict)
        levels, type_counts = parse_repos(repos_raw)
        assert len(levels) == 1
        assert len(levels[0]) == 1
        assert levels[0][0].name == "active-repo"
        # type_counts should include all 3 repos
        assert type_counts.get("service", 0) == 3

    def test_planned_gets_future_css(self) -> None:
        """Repos with status='planned' should get 'future' CSS class."""
        data = _minimal_manifest()
        repos_raw = data["repositories"]
        assert isinstance(repos_raw, dict)
        levels, _ = parse_repos(repos_raw)
        planned = [r for r in levels[1] if r.name == "repo-c"]
        assert len(planned) == 1
        assert planned[0].css_class == "future"

    def test_sorted_within_level(self) -> None:
        """Repos within a level should be sorted alphabetically."""
        data = _minimal_manifest()
        repos_raw = data["repositories"]
        assert isinstance(repos_raw, dict)
        levels, _ = parse_repos(repos_raw)
        names = [r.name for r in levels[1]]
        assert names == sorted(names)


# --- generate_svg ---


class TestGenerateSvg:
    """Tests for generate_svg()."""

    def test_valid_xml(self) -> None:
        """Generated SVG must be valid XML."""
        svg = generate_svg(_minimal_manifest())
        ET.fromstring(svg)

    def test_contains_all_repos(self) -> None:
        """SVG should contain text elements for all non-deprecated repos."""
        svg = generate_svg(_minimal_manifest())
        assert "repo-a" in svg
        assert "repo-b" in svg
        assert "repo-c" in svg

    def test_xml_escapes_ampersand(self) -> None:
        """Ampersands in descriptions must be escaped as &amp;."""
        svg = generate_svg(_manifest_with_ampersand())
        ET.fromstring(svg)
        assert "Standards &amp; codex" in svg
        assert "Standards & codex" not in svg

    def test_deprecated_repos_excluded(self) -> None:
        """Deprecated repos should not appear in SVG."""
        svg = generate_svg(_manifest_with_deprecated())
        assert "active-repo" in svg
        assert "deprecated-null" not in svg
        assert "deprecated-neg" not in svg

    def test_level_count_in_title(self) -> None:
        """Title should show correct level count."""
        svg = generate_svg(_minimal_manifest())
        assert "2 levels" in svg

    def test_repo_count_in_subtitle(self) -> None:
        """Subtitle should show total repo count."""
        svg = generate_svg(_minimal_manifest())
        assert "3 repos" in svg

    def test_level_descriptions_in_svg(self) -> None:
        """Level descriptions should appear in the SVG."""
        svg = generate_svg(_minimal_manifest())
        assert "Root" in svg
        assert "Libraries" in svg

    def test_version_strings_present(self) -> None:
        """Version strings should appear in the SVG."""
        svg = generate_svg(_minimal_manifest())
        assert "0.1.0" in svg
        assert "0.2.0" in svg
        assert "0.3.0" in svg

    def test_missing_repositories_raises(self) -> None:
        """Should raise ValueError when repositories key is missing."""
        with pytest.raises(ValueError, match="missing 'repositories' dict"):
            generate_svg({})

    def test_svg_root_element(self) -> None:
        """Root element should be an SVG with correct namespace."""
        svg = generate_svg(_minimal_manifest())
        root = ET.fromstring(svg)
        assert root.tag == "{http://www.w3.org/2000/svg}svg"

    def test_has_style_element(self) -> None:
        """SVG should contain a style element with CSS classes."""
        svg = generate_svg(_minimal_manifest())
        assert ".lib" in svg
        assert ".svc" in svg
        assert ".future" in svg


# --- generate (file I/O) ---


class TestGenerate:
    """Tests for generate() end-to-end file I/O."""

    def test_writes_valid_svg_file(self, tmp_path: Path) -> None:
        """Should write a valid SVG file to disk."""
        manifest_path = tmp_path / "manifest.json"
        manifest_path.write_text(json.dumps(_minimal_manifest()))
        output_path = tmp_path / "output.svg"

        result = generate(manifest_path=manifest_path, output_path=output_path)

        assert result == output_path
        assert output_path.exists()
        ET.parse(str(output_path))

    def test_invalid_manifest_raises(self, tmp_path: Path) -> None:
        """Should raise ValueError for manifest without repositories."""
        manifest_path = tmp_path / "bad.json"
        manifest_path.write_text(json.dumps({"not_repos": {}}))
        output_path = tmp_path / "output.svg"

        with pytest.raises(ValueError, match="missing 'repositories' dict"):
            generate(manifest_path=manifest_path, output_path=output_path)

    def test_real_manifest(self) -> None:
        """Smoke test: generate from the real workspace-manifest.json."""
        manifest = Path(__file__).parent.parent / "workspace-manifest.json"
        if not manifest.exists():
            pytest.skip("workspace-manifest.json not available")

        from typing import cast

        with open(manifest) as f:
            data = cast(JsonDict, json.load(f))
        svg = generate_svg(data)

        root = ET.fromstring(svg)
        ns = {"svg": "http://www.w3.org/2000/svg"}
        texts = root.findall(".//svg:text", ns)
        # 63 repos * ~2 text elements each + headers/footers
        assert len(texts) > 50
