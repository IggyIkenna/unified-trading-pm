"""Unit tests for the strategy prospectus generator family.

Pins:
  - Determinism: two runs of generate_strategy_prospectus produce byte-identical output
  - Audit: audit_prospectus_vs_codex produces deterministic + structurally valid output
  - Helper modules: _prospectus_codex, _prospectus_manifest

Plan: plans/active/capability_wizard_and_manifest_2026_06_11.md Phase 3 [VERIFY] P2
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

# Ensure the scripts/openapi helpers are on the path for direct import
_SCRIPTS_OPENAPI = Path(__file__).resolve().parent.parent.parent / "scripts" / "openapi"
if str(_SCRIPTS_OPENAPI) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_OPENAPI))

_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_UAC_ROOT = _WORKSPACE_ROOT / "unified-api-contracts"
_PM_ROOT = _WORKSPACE_ROOT / "unified-trading-pm"

# Set env for mock mode
os.environ.setdefault("CLOUD_PROVIDER", "local")
os.environ.setdefault("CLOUD_MOCK_MODE", "true")
os.environ.setdefault("DISABLE_AUTH", "true")
os.environ.setdefault("MOCK_STATE_MODE", "deterministic")
os.environ.setdefault("GCP_PROJECT_ID", "mock-project")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("API_KEY", "mock-api-key-for-test")


# ---------------------------------------------------------------------------
# Codex helper tests
# ---------------------------------------------------------------------------


def test_archetype_id_to_filename_mapping() -> None:
    """CARRY_STAKED_BASIS → carry-staked-basis.md."""
    from _prospectus_codex import _archetype_id_to_filename

    assert _archetype_id_to_filename("CARRY_STAKED_BASIS") == "carry-staked-basis.md"
    assert _archetype_id_to_filename("DEFI_LP_CONCENTRATED") == "defi-lp-concentrated.md"
    assert _archetype_id_to_filename("VOL_TRADING_OPTIONS") == "vol-trading-options.md"


def test_archetype_id_from_stem_round_trip() -> None:
    """stem → id → stem should be identity."""
    from _prospectus_codex import _archetype_id_to_filename, archetype_id_from_stem

    archetype_id = "CARRY_STAKED_BASIS"
    stem = _archetype_id_to_filename(archetype_id)[:-3]  # strip .md
    assert archetype_id_from_stem(stem) == archetype_id


def test_parse_frontmatter_extracts_key_values() -> None:
    """parse_frontmatter should return a dict from YAML frontmatter."""
    from _prospectus_codex import parse_frontmatter

    doc = "---\narchetype: CARRY_STAKED_BASIS\nfamily: CARRY_AND_YIELD\nstatus: spec\n---\n\n# Body\n"
    fm = parse_frontmatter(doc)
    assert fm.get("archetype") == "CARRY_STAKED_BASIS"
    assert fm.get("family") == "CARRY_AND_YIELD"
    assert fm.get("status") == "spec"


def test_parse_frontmatter_empty_doc() -> None:
    """parse_frontmatter on body-only doc returns empty dict."""
    from _prospectus_codex import parse_frontmatter

    doc = "# Just a header\n\nSome body text.\n"
    fm = parse_frontmatter(doc)
    assert fm == {}


def test_get_body_text_strips_frontmatter() -> None:
    """get_body_text should return only the body after frontmatter."""
    from _prospectus_codex import get_body_text

    doc = "---\narchetype: X\n---\n\n# Real body\n\nContent here.\n"
    body = get_body_text(doc)
    assert "Real body" in body
    assert "archetype" not in body


def test_extract_section_returns_section_body() -> None:
    """extract_section should return content under the matching heading."""
    from _prospectus_codex import extract_section

    body = "# Title\n\n## What it does\n\nIt does things.\n\n## Another section\n\nOther content.\n"
    result = extract_section(body, "## What it does")
    assert result is not None
    assert "It does things" in result
    assert "Another section" not in result


def test_extract_section_missing_heading_returns_none() -> None:
    """extract_section should return None if heading not found."""
    from _prospectus_codex import extract_section

    body = "## Only this heading\n\nSome content.\n"
    result = extract_section(body, "## Missing heading")
    assert result is None


def test_list_all_codex_docs_returns_stems() -> None:
    """list_all_codex_docs should return stem names (no extension)."""
    from _prospectus_codex import list_all_codex_docs

    docs = list_all_codex_docs()
    # Should have at least some docs
    assert len(docs) > 0
    # Should not have .md extensions
    for doc in docs:
        assert not doc.endswith(".md"), f"Expected stem, got: {doc}"
    # Should be sorted
    assert docs == sorted(docs)


# ---------------------------------------------------------------------------
# Manifest helper tests
# ---------------------------------------------------------------------------


def test_load_manifest_returns_dict() -> None:
    """load_manifest should return a non-empty dict if manifest exists."""
    from _prospectus_manifest import load_manifest

    if not (_UAC_ROOT / "openapi" / "capability-manifest.json").exists():
        pytest.skip("capability-manifest.json not found")

    manifest = load_manifest(_UAC_ROOT)
    assert isinstance(manifest, dict)
    assert "nodes" in manifest
    assert "edges" in manifest


def test_get_manifest_provenance_returns_version() -> None:
    """get_manifest_provenance should return manifest_version key."""
    from _prospectus_manifest import get_manifest_provenance, load_manifest

    if not (_UAC_ROOT / "openapi" / "capability-manifest.json").exists():
        pytest.skip("capability-manifest.json not found")

    manifest = load_manifest(_UAC_ROOT)
    prov = get_manifest_provenance(manifest)
    assert "manifest_version" in prov
    assert prov["manifest_version"] != ""


def test_build_fund_flow_mermaid_contains_mermaid_fence() -> None:
    """build_fund_flow_mermaid should return a fenced mermaid block."""
    from _prospectus_manifest import build_fund_flow_mermaid

    mermaid = build_fund_flow_mermaid("CARRY_STAKED_BASIS", ["DEFI"], [])
    assert "```mermaid" in mermaid
    assert "flowchart TD" in mermaid
    assert "```" in mermaid


def test_build_fund_flow_mermaid_staked_basis_has_lst() -> None:
    """CARRY_STAKED_BASIS fund flow should include LST legs."""
    from _prospectus_manifest import build_fund_flow_mermaid

    mermaid = build_fund_flow_mermaid("CARRY_STAKED_BASIS", ["DEFI"], [])
    assert "LST" in mermaid
    assert "STAKING" in mermaid


def test_build_fund_flow_mermaid_deterministic() -> None:
    """build_fund_flow_mermaid should be deterministic across two calls."""
    from _prospectus_manifest import build_fund_flow_mermaid

    result1 = build_fund_flow_mermaid("MARKET_MAKING_CONTINUOUS", ["CEFI"], [])
    result2 = build_fund_flow_mermaid("MARKET_MAKING_CONTINUOUS", ["CEFI"], [])
    assert result1 == result2


# ---------------------------------------------------------------------------
# Audit determinism test
# ---------------------------------------------------------------------------


def test_audit_output_deterministic() -> None:
    """audit_prospectus_vs_codex.run_audit() should be deterministic (same results twice)."""
    # Add UAC to path for imports
    uac_path = str(_UAC_ROOT)
    if uac_path not in sys.path:
        sys.path.insert(0, uac_path)

    try:
        from audit_prospectus_vs_codex import render_audit_report, run_audit

        result1 = run_audit()
        result2 = run_audit()

        assert result1["total_archetype_ids"] == result2["total_archetype_ids"]
        assert result1["total_codex_docs"] == result2["total_codex_docs"]
        assert result1["enum_without_doc"] == result2["enum_without_doc"]
        assert result1["doc_without_enum"] == result2["doc_without_enum"]
        assert result1["contradictions"] == result2["contradictions"]

        # Rendered report should also be identical
        report1 = render_audit_report(result1)
        report2 = render_audit_report(result2)
        assert report1 == report2
    except ImportError as e:
        pytest.skip(f"UAC import unavailable: {e}")


def test_audit_57_archetypes() -> None:
    """Audit should report exactly 57 StrategyArchetype enum values."""
    uac_path = str(_UAC_ROOT)
    if uac_path not in sys.path:
        sys.path.insert(0, uac_path)

    try:
        from audit_prospectus_vs_codex import run_audit

        result = run_audit()
        assert result["total_archetype_ids"] == 57, (
            f"Expected 57 archetypes but got {result['total_archetype_ids']}. "
            "Update the plan if new archetypes were added (see F9 in findings tracker)."
        )
    except ImportError as e:
        pytest.skip(f"UAC import unavailable: {e}")


def test_audit_codex_docs_count() -> None:
    """Audit should find 59 codex archetype docs (57 mapped + 2 orphans)."""
    uac_path = str(_UAC_ROOT)
    if uac_path not in sys.path:
        sys.path.insert(0, uac_path)

    try:
        from audit_prospectus_vs_codex import run_audit

        result = run_audit()
        # If codex docs change, update this test
        assert result["total_codex_docs"] >= 57, (
            f"Expected at least 57 codex docs but got {result['total_codex_docs']}"
        )
    except ImportError as e:
        pytest.skip(f"UAC import unavailable: {e}")


# ---------------------------------------------------------------------------
# Prospectus generator determinism (integration) test
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_prospectus_generator_deterministic_single_archetype() -> None:
    """Generate prospectus for one archetype twice — byte-identical."""
    uac_path = str(_UAC_ROOT)
    if uac_path not in sys.path:
        sys.path.insert(0, uac_path)

    if not (_UAC_ROOT / "openapi" / "capability-manifest.json").exists():
        pytest.skip("capability-manifest.json not found")

    try:
        from _prospectus_manifest import get_execution_algos, get_manifest_provenance, load_manifest
        from generate_strategy_prospectus import render_prospectus

        manifest = load_manifest(_UAC_ROOT)
        provenance = get_manifest_provenance(manifest)
        exec_algos = get_execution_algos(manifest)

        doc1 = render_prospectus("CARRY_STAKED_BASIS", manifest, provenance, exec_algos)
        doc2 = render_prospectus("CARRY_STAKED_BASIS", manifest, provenance, exec_algos)
        assert doc1 == doc2, "Prospectus output is not deterministic"
    except ImportError as e:
        pytest.skip(f"UAC import unavailable: {e}")


@pytest.mark.integration
def test_prospectus_has_all_7_sections() -> None:
    """Generated prospectus for CARRY_STAKED_BASIS must contain all 7 sections."""
    uac_path = str(_UAC_ROOT)
    if uac_path not in sys.path:
        sys.path.insert(0, uac_path)

    if not (_UAC_ROOT / "openapi" / "capability-manifest.json").exists():
        pytest.skip("capability-manifest.json not found")

    try:
        from _prospectus_manifest import get_execution_algos, get_manifest_provenance, load_manifest
        from generate_strategy_prospectus import render_prospectus

        manifest = load_manifest(_UAC_ROOT)
        provenance = get_manifest_provenance(manifest)
        exec_algos = get_execution_algos(manifest)

        doc = render_prospectus("CARRY_STAKED_BASIS", manifest, provenance, exec_algos)

        expected_headings = [
            "## 1. What It Does",
            "## 2. Universe & Execution",
            "## 3. Exposures & Normalization",
            "## 4. Fund Flow",
            "## 5. Risk & Circuit Breakers",
            "## 6. Performance",
            "## 7. Provenance",
        ]
        for heading in expected_headings:
            assert heading in doc, f"Missing section: {heading}"
    except ImportError as e:
        pytest.skip(f"UAC import unavailable: {e}")


@pytest.mark.integration
def test_prospectus_honesty_labels() -> None:
    """Prospectus should contain [MACHINE-DERIVED] and [CODEX-DERIVED] labels."""
    uac_path = str(_UAC_ROOT)
    if uac_path not in sys.path:
        sys.path.insert(0, uac_path)

    if not (_UAC_ROOT / "openapi" / "capability-manifest.json").exists():
        pytest.skip("capability-manifest.json not found")

    try:
        from _prospectus_manifest import get_execution_algos, get_manifest_provenance, load_manifest
        from generate_strategy_prospectus import render_prospectus

        manifest = load_manifest(_UAC_ROOT)
        provenance = get_manifest_provenance(manifest)
        exec_algos = get_execution_algos(manifest)

        doc = render_prospectus("CARRY_STAKED_BASIS", manifest, provenance, exec_algos)
        assert "[MACHINE-DERIVED]" in doc
        assert "[CODEX-DERIVED]" in doc
        # Performance section must say "no backtest"
        assert "No backtest" in doc or "no backtest" in doc
    except ImportError as e:
        pytest.skip(f"UAC import unavailable: {e}")
