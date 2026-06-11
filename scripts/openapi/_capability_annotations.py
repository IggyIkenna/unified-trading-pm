"""Sidecar annotation loader and edge-merge helper.

Loads ``capability-annotations.yaml`` (the hand/agent-appendable registry of
answers to ``needs_code_scan`` gap edges) and merges matching entries into the
manifest's ``CapabilityEdge.agent_annotation`` field.

Merge contract (deterministic):
  * Key: ``(from_node, to_node, relation)`` — exact match required.
  * Unmatched sidecar entries → listed in the orphan report (loud, never silent).
  * A sidecar entry for an already-annotated edge is a no-op (first annotation
    wins — annotations are append-only; do not clobber).
  * ``answered_on`` is an ISO date string (``YYYY-MM-DD``); merged into
    ``AgentAnnotation.annotated_at`` as UTC midnight of that date.
  * ``resolved_status`` is NOT in the YAML (the answer text carries enough
    context); the merge logic sets ``CapabilityEdgeStatus.PARTIAL`` by default
    (the agent answered the scan but the registry is still empty — the edge is
    no longer fully opaque).  Override by adding ``resolved_status:`` to the
    YAML entry.

Codex SSOT: ``codex/09-strategy/architecture-v2/capability-wizard.md``
Plan: ``plans/active/capability_wizard_and_manifest_2026_06_11.md`` Phase 5.
"""

from __future__ import annotations

import logging
import textwrap
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Key type: (from_node_id, to_node_id, relation)
_AnnotationKey = tuple[str, str, str]


def _load_sidecar(sidecar_path: Path) -> list[dict[str, str]]:
    """Parse the sidecar YAML.  Returns a list of raw annotation dicts."""
    try:
        import yaml  # noqa: imports-inside-functions, fallback-import — lazy optional dep; pyyaml not in all envs
    except ImportError:
        logger.warning("  PyYAML not available — sidecar annotations will not be merged; install pyyaml")
        return []

    if not sidecar_path.exists():
        logger.info("  No sidecar found at %s — skipping annotation merge", sidecar_path)
        return []

    with open(sidecar_path) as fh:
        data = yaml.safe_load(fh)

    if not isinstance(data, dict):
        logger.warning("  Sidecar YAML is not a mapping — skipping")
        return []

    annotations = data.get("annotations", [])  # noqa: qg-empty-fallback
    if not isinstance(annotations, list):
        logger.warning("  Sidecar 'annotations' key is not a list — skipping")
        return []

    return annotations  # type: ignore[return-value]


def _parse_date_to_utc(date_str: str) -> datetime:
    """Parse an ISO date string (YYYY-MM-DD) to UTC midnight datetime."""
    try:
        # Use fromisoformat on a date-typed string, then build an aware datetime.
        # We import `date` at module level alongside `datetime`; we use a split
        # constructor here instead of strptime to avoid a naive-datetime intermediate.
        parts = date_str.strip().split("-")
        return datetime(int(parts[0]), int(parts[1]), int(parts[2]), tzinfo=UTC)
    except (ValueError, IndexError):
        logger.warning("  Could not parse answered_on '%s' — using epoch", date_str)
        return datetime(2026, 6, 11, tzinfo=UTC)


def build_annotation_index(
    sidecar_path: Path,
) -> dict[_AnnotationKey, dict[str, str]]:
    """Return a mapping ``(from_node, to_node, relation) → raw annotation dict``."""
    raw = _load_sidecar(sidecar_path)
    index: dict[_AnnotationKey, dict[str, str]] = {}
    for entry in raw:
        if not isinstance(entry, dict):
            logger.warning("  Sidecar entry is not a mapping: %s — skipped", entry)
            continue
        from_node = str(entry.get("from_node", "")).strip()  # noqa: qg-empty-fallback
        to_node = str(entry.get("to_node", "")).strip()  # noqa: qg-empty-fallback
        relation = str(entry.get("relation", "")).strip()  # noqa: qg-empty-fallback
        if not (from_node and to_node and relation):
            logger.warning("  Sidecar entry missing from_node/to_node/relation — skipped: %s", entry)
            continue
        key: _AnnotationKey = (from_node, to_node, relation)
        if key in index:
            logger.warning("  Duplicate sidecar key %s — first entry kept", key)
            continue
        index[key] = entry
    logger.info("  Loaded %d sidecar annotation(s) from %s", len(index), sidecar_path)
    return index


def merge_annotations_into_edges(
    edges: list,  # list[CapabilityEdge] — typed lazily to avoid circular at load
    annotation_index: dict[_AnnotationKey, dict[str, str]],
) -> tuple[list, list[_AnnotationKey]]:
    """Merge sidecar annotations into the edge list.

    Returns:
        (merged_edges, unmatched_keys) where ``merged_edges`` is the updated
        list and ``unmatched_keys`` are sidecar keys with no matching edge.
    """
    from unified_api_contracts.internal.architecture_v2.capability_manifest import (  # noqa: imports-inside-functions — circular-safe deep import
        AgentAnnotation,
        CapabilityEdge,
        CapabilityEdgeStatus,
    )

    # Build a lookup: (from_node_id, to_node_id, relation) → index in list
    edge_index: dict[_AnnotationKey, int] = {}
    for i, edge in enumerate(edges):
        key: _AnnotationKey = (edge.from_node_id, edge.to_node_id, edge.relation)
        if key not in edge_index:
            edge_index[key] = i

    matched_keys: set[_AnnotationKey] = set()
    merged: list[CapabilityEdge] = list(edges)

    for key, entry in annotation_index.items():
        idx = edge_index.get(key)
        if idx is None:
            logger.warning("  Sidecar annotation %s has no matching edge — ORPHAN", key)
            continue

        matched_keys.add(key)
        edge = merged[idx]

        if edge.agent_annotation is not None:
            # Already annotated — first write wins (append-only rule)
            logger.debug("  Edge %s already annotated — sidecar entry skipped (first wins)", key)
            continue

        # Build the AgentAnnotation
        answered_on = str(entry.get("answered_on", "2026-06-11"))
        answered_by = str(entry.get("answered_by", "agent"))
        answer_text = str(entry.get("answer", "")).strip()  # noqa: qg-empty-fallback
        # Normalize multi-line YAML block scalars: collapse runs of whitespace
        answer_text = textwrap.dedent(answer_text).strip()

        # resolved_status: YAML may declare it; default to PARTIAL (answered but
        # registry still empty — the agent explained the gap, not closed it)
        raw_resolved = str(entry.get("resolved_status", "")).strip().lower()  # noqa: qg-empty-fallback
        resolved_map: dict[str, CapabilityEdgeStatus] = {
            "partial": CapabilityEdgeStatus.PARTIAL,
            "available": CapabilityEdgeStatus.AVAILABLE,
            "not_available": CapabilityEdgeStatus.NOT_AVAILABLE,
            "not_registered": CapabilityEdgeStatus.NOT_REGISTERED,
        }
        resolved_status = resolved_map.get(raw_resolved, CapabilityEdgeStatus.PARTIAL)

        annotation = AgentAnnotation(
            annotated_by=answered_by,
            annotated_at=_parse_date_to_utc(answered_on),
            answer=answer_text,
            resolved_status=resolved_status,
        )

        # CapabilityEdge is frozen — rebuild with annotation set
        merged[idx] = CapabilityEdge(
            from_node_id=edge.from_node_id,
            to_node_id=edge.to_node_id,
            relation=edge.relation,
            status=edge.status,
            gap_type=edge.gap_type,
            reason=edge.reason,
            readiness=edge.readiness,
            agent_annotation=annotation,
        )
        logger.info("  Merged annotation for edge %s", key)

    unmatched = [k for k in annotation_index if k not in matched_keys]
    if unmatched:
        logger.warning(
            "  %d sidecar annotation(s) have no matching edge (ORPHAN): %s",
            len(unmatched),
            unmatched,
        )

    return merged, unmatched


def render_annotation_orphan_section(unmatched: list[_AnnotationKey]) -> str:
    """Human-readable section listing unmatched sidecar entries."""
    lines = [
        "",
        f"## Sidecar annotation orphans ({len(unmatched)})",
        "",
        "# These sidecar entries in capability-annotations.yaml have no matching",
        "# edge in the current manifest. They are listed here for triage.",
        "",
    ]
    for from_node, to_node, relation in sorted(unmatched):
        lines.append(f"ANNOTATION_ORPHAN: ({from_node!r}, {to_node!r}, {relation!r})")
    if not unmatched:
        lines.append("# (none)")
    lines.append("")
    return "\n".join(lines)
