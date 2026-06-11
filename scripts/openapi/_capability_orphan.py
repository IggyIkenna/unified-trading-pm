"""Orphan + dead-end analysis for the capability manifest (plan item 2).

Two distinct findings:
  * Orphan nodes — nodes with no edges (neither source nor target).
  * Dead-end (archetype x instrument x venue) combinations:
      - UNBUILT dead-end: the capability registry says ``available`` for an
        (archetype, instrument_type) but NO venue of that instrument-type's
        asset-group actually supports the instrument type (missing adapter/
        registry — a build gap).
      - LOGICAL dead-end: combinations absent from the capability registry
        (e.g. options on sports) — correct and expected, not a build gap.

Returns a structured summary (folded into the manifest gaps section) plus a
human-readable text report appended to the openapi/ orphan-report family.

Codex SSOT: ``codex/09-strategy/architecture-v2/capability-wizard.md``
Plan: ``plans/active/capability_wizard_and_manifest_2026_06_11.md`` Phase 1.
"""

from __future__ import annotations

import logging

from unified_api_contracts.internal.architecture_v2.capability_manifest import (
    CapabilityEdge,
    CapabilityEdgeStatus,
    CapabilityNode,
)

logger = logging.getLogger(__name__)


def find_orphan_nodes(nodes: list[CapabilityNode], edges: list[CapabilityEdge]) -> list[str]:
    """Node ids that appear in no edge (self-loops count as touched)."""
    touched: set[str] = set()
    for edge in edges:
        touched.add(edge.from_node_id)
        touched.add(edge.to_node_id)
    return sorted(n.node_id for n in nodes if n.node_id not in touched)


def find_dead_ends(
    nodes: list[CapabilityNode],
    edges: list[CapabilityEdge],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    """Compute unbuilt vs logical dead-ends.

    Returns ``(unbuilt, logical)`` lists of {archetype, instrument_type,
    asset_group, reason} dicts, sorted deterministically.
    """
    # instrument_type -> asset_group (from node metadata where present).
    it_asset_group: dict[str, str] = {}
    for n in nodes:
        if n.node_id.startswith("instrument_type:"):
            ag = n.metadata.get("asset_group", "")
            if ag:
                it_asset_group[n.node_id] = ag

    # venue -> set of instrument_type node_ids it trades; venue -> category.
    venue_instr: dict[str, set[str]] = {}
    venue_category: dict[str, str] = {}
    for n in nodes:
        if n.node_id.startswith("venue:"):
            cat = n.metadata.get("category", "")
            if cat:
                venue_category[n.node_id] = cat
    for edge in edges:
        if (
            edge.from_node_id.startswith("venue:")
            and edge.to_node_id.startswith("instrument_type:")
            and edge.relation == "trades_instrument"
        ):
            venue_instr.setdefault(edge.from_node_id, set()).add(edge.to_node_id)

    # instrument_type -> does ANY venue of the same asset-group support it?
    supported_instr_by_ag: dict[str, set[str]] = {}
    for venue, instrs in venue_instr.items():
        cat = venue_category.get(venue, "")
        for it in instrs:
            supported_instr_by_ag.setdefault(cat, set()).add(it)

    # Archetype -> instrument edges from the capability registry (trades_instrument).
    arch_instr_available: list[tuple[str, str]] = []
    for edge in edges:
        if (
            not edge.from_node_id.startswith("venue:")
            and edge.to_node_id.startswith("instrument_type:")
            and edge.relation == "trades_instrument"
            and edge.status == CapabilityEdgeStatus.AVAILABLE
        ):
            arch_instr_available.append((edge.from_node_id, edge.to_node_id))

    unbuilt: list[dict[str, str]] = []
    for arch, it in sorted(set(arch_instr_available)):
        ag = it_asset_group.get(it, "")
        supported = supported_instr_by_ag.get(ag, set())
        if it not in supported:
            unbuilt.append(
                {
                    "archetype": arch,
                    "instrument_type": it.removeprefix("instrument_type:"),
                    "asset_group": ag,
                    "reason": (
                        "capability registry marks (archetype, instrument_type) available, "
                        f"but no {ag or 'matching-category'} venue lists this instrument type — "
                        "unbuilt dead-end (missing adapter/registry)"
                    ),
                }
            )

    # Logical dead-ends: NOT_AVAILABLE archetype->instrument edges (registry
    # explicitly marks them blocked / structurally impossible).
    logical: list[dict[str, str]] = []
    for edge in edges:
        if (
            not edge.from_node_id.startswith("venue:")
            and edge.to_node_id.startswith("instrument_type:")
            and edge.relation == "trades_instrument"
            and edge.status == CapabilityEdgeStatus.NOT_AVAILABLE
        ):
            logical.append(
                {
                    "archetype": edge.from_node_id,
                    "instrument_type": edge.to_node_id.removeprefix("instrument_type:"),
                    "asset_group": it_asset_group.get(edge.to_node_id, ""),
                    "reason": edge.reason or "registry marks this combination blocked (logical dead-end)",
                }
            )
    logical.sort(key=lambda d: (d["archetype"], d["instrument_type"]))

    logger.info("  dead-ends: %d unbuilt, %d logical", len(unbuilt), len(logical))
    return unbuilt, logical


def render_orphan_report(
    orphans: list[str],
    unbuilt: list[dict[str, str]],
    logical: list[dict[str, str]],
    manifest_version: str,
    generated_from_commit: str | None,
) -> str:
    """Human-readable text report (deterministic — sorted inputs)."""
    lines: list[str] = [
        "# Capability Manifest — Orphan + Dead-End Report",
        f"# manifest_version: {manifest_version}",
        f"# generated_from_commit: {generated_from_commit or '(none)'}",
        "#",
        "# Orphan nodes have no edges. Unbuilt dead-ends are registry-available",
        "# archetype/instrument combos with no supporting venue (build gap).",
        "# Logical dead-ends are registry-blocked combos (correct, not a gap).",
        "",
        f"## Orphan nodes ({len(orphans)})",
        "",
    ]
    lines.extend(f"ORPHAN: {o}" for o in orphans)
    lines.append("")
    lines.append(f"## Unbuilt dead-ends ({len(unbuilt)})")
    lines.append("")
    for d in unbuilt:
        lines.append(f"UNBUILT: {d['archetype']} x {d['instrument_type']} ({d['asset_group']}) — {d['reason']}")
    lines.append("")
    lines.append(f"## Logical dead-ends ({len(logical)})")
    lines.append("")
    for d in logical:
        lines.append(f"LOGICAL: {d['archetype']} x {d['instrument_type']} ({d['asset_group']}) — {d['reason']}")
    lines.append("")
    return "\n".join(lines)
