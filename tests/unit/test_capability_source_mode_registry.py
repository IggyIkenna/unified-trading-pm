"""Unit tests for the data-source supports_mode edges reading SOURCE_MODE_CAPABILITY.

Pins the fix for the capability_wizard_gap_discovery_2026_06_11.md P1 gap: the
batch/live/replay-per-source matrix used to live only in a manual audit doc
(``source_mode_capability_matrix_2026_06_07.md``), so ``extract_data_sources()``
emitted a blanket ``missing_registry`` gap for every source's live/replay edge.
The matrix is now codified as ``SOURCE_MODE_CAPABILITY`` (built for the M2
reconciliation code); this test pins that the exporter reads it instead of
gap-stamping every non-batch edge.

Plan: plans/active/issues/capability_wizard_gap_discovery_2026_06_11.md.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

_SCRIPTS_OPENAPI = Path(__file__).resolve().parent.parent.parent / "scripts" / "openapi"
if str(_SCRIPTS_OPENAPI) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_OPENAPI))

os.environ.setdefault("CLOUD_PROVIDER", "local")
os.environ.setdefault("CLOUD_MOCK_MODE", "true")
os.environ.setdefault("DISABLE_AUTH", "true")
os.environ.setdefault("GCP_PROJECT_ID", "mock-project")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "mock-project")

from _capability_extract import extract_data_sources


def _mode_edges_for(source: str) -> dict[str, object]:
    _, edges = extract_data_sources()
    sid = f"data_source:{source}"
    return {
        e.relation.removeprefix("supports_mode:"): e
        for e in edges
        if e.from_node_id == sid and e.relation.startswith("supports_mode:")
    }


def test_ratified_source_with_full_capability_has_no_gap() -> None:
    """hyperliquid is ratified batch+live+replay — every mode edge is available."""
    edges = _mode_edges_for("hyperliquid")
    assert set(edges) == {"batch", "live", "replay"}
    for mode, edge in edges.items():
        assert str(edge.status) == "available", f"{mode} unexpectedly not available"
        assert edge.gap_type is None, f"{mode} still carries a gap_type"


def test_ratified_source_with_partial_capability_is_honest_negative_not_a_gap() -> None:
    """tardis is ratified batch-only — live/replay are a typed NOT_AVAILABLE fact, not a missing_registry gap."""
    edges = _mode_edges_for("tardis")
    assert str(edges["batch"].status) == "available"
    for mode in ("live", "replay"):
        assert str(edges[mode].status) == "not_available", f"{mode} should be an honest negative"
        assert edges[mode].gap_type is None, f"{mode} should not carry a gap_type once ratified"


def test_no_missing_registry_gap_survives_for_a_ratified_source() -> None:
    """Every source currently in SOURCE_PRIORITY is ratified in SOURCE_MODE_CAPABILITY —
    so no data_source supports_mode edge should still carry the missing_registry gap.
    """
    from unified_api_contracts import SOURCE_MODE_CAPABILITY

    nodes, edges = extract_data_sources()
    sources = {n.node_id.removeprefix("data_source:") for n in nodes if str(n.kind) == "data_source"}
    assert sources, "no data_source nodes extracted"
    assert sources <= SOURCE_MODE_CAPABILITY.keys(), (
        f"unratified sources present (would still need the gap path): {sources - SOURCE_MODE_CAPABILITY.keys()}"
    )

    gap_edges = [
        e for e in edges if e.relation.startswith("supports_mode:") and e.gap_type is not None
    ]
    assert not gap_edges, f"missing_registry gaps remain despite every source being ratified: {gap_edges}"


def test_unratified_source_still_falls_back_to_missing_registry_gap(monkeypatch) -> None:
    """A source dropped from SOURCE_MODE_CAPABILITY still gets the honest gap (defensive path).

    Simulates a newly-added SOURCE_PRIORITY source that hasn't been ratified yet by
    monkeypatching hyperliquid out of a copy of the registry — the extractor does a
    fresh ``from unified_api_contracts import SOURCE_MODE_CAPABILITY`` on every call,
    so patching the module attribute is enough to redirect it.
    """
    import unified_api_contracts

    patched = dict(unified_api_contracts.SOURCE_MODE_CAPABILITY)
    del patched["hyperliquid"]
    monkeypatch.setattr(unified_api_contracts, "SOURCE_MODE_CAPABILITY", patched)

    edges = _mode_edges_for("hyperliquid")
    assert str(edges["batch"].status) == "available", "batch stays the unconditional floor"
    for mode in ("live", "replay"):
        assert str(edges[mode].status) == "not_registered"
        assert edges[mode].gap_type is not None and str(edges[mode].gap_type) == "missing_registry"
