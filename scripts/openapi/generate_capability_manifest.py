"""Generate the capability manifest — the typed graph of what the system can do.

Builds a ``CapabilityManifest`` (UAC schema, imported never redefined) whose
nodes/edges cover, in priority order:
  (a) archetypes/families + ARCHETYPE_CAPABILITY_REGISTRY,
  (b) venues / chains / instrument types (+ auth/access from ENDPOINT_REGISTRY),
  (c) data sources / modes / transports (SOURCE_PRIORITY + pipeline_mode),
  (d) gap registries (collateral/fees/sim/fund/order/agent + treasury split),
  (e) risk surface (KillSwitchReason x RiskGateLayer),
  (f) service-resident registries (exec algos / feature groups / ML models),
plus an orphan + dead-end report (plan item 2).

Output: ``unified-api-contracts/openapi/capability-manifest.json`` via
``to_canonical_dict()`` (deterministic — run twice, byte-identical).  A
companion human-readable ``capability-orphan-report.txt`` lands beside the
existing ``orphan-report.txt``.

manifest_version: ``1.0.0``.  ``generated_from_commit`` = UAC HEAD sha (read via
git — no timestamps, determinism rule).

SSOT for how this fits other UI sync paths: ``unified-trading-pm/docs/ui-alignment-ssot.md``
Plan: ``plans/active/capability_wizard_and_manifest_2026_06_11.md`` Phase 1.

Usage:
    python generate_capability_manifest.py [--output-dir PATH] [--workspace-root PATH]
"""

from __future__ import annotations

import os

os.environ.setdefault("CLOUD_PROVIDER", "local")
os.environ.setdefault("CLOUD_MOCK_MODE", "true")
os.environ.setdefault("DISABLE_AUTH", "true")
os.environ.setdefault("MOCK_STATE_MODE", "deterministic")
os.environ.setdefault("GCP_PROJECT_ID", "mock-project")
os.environ.setdefault("PUBSUB_EMULATOR_HOST", "localhost:8085")
os.environ.setdefault("STORAGE_EMULATOR_HOST", "http://localhost:4443")
os.environ.setdefault("BIGQUERY_EMULATOR_HOST", "localhost:9050")
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", "mock-project")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("API_KEY", "mock-api-key-for-openapi-gen")

import argparse
import json
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

from _capability_annotations import (
    build_annotation_index,
    merge_annotations_into_edges,
    render_annotation_orphan_section,
)
from _capability_extract import (
    extract_archetypes_and_families,
    extract_data_sources,
    extract_leg_structures,
    extract_venues,
)
from _capability_gaps import (
    extract_algo_compatibility,
    extract_gap_registries,
    extract_risk_surface,
    extract_service_registries,
)
from _capability_orphan import (
    find_dead_ends,
    find_orphan_nodes,
    render_orphan_report,
)
from unified_api_contracts.internal.architecture_v2.capability_manifest import (
    CapabilityEdge,
    CapabilityManifest,
    CapabilityNode,
)

MANIFEST_VERSION = "1.0.0"


def _read_uac_head_sha(uac_root: Path) -> str | None:
    """UAC HEAD sha via git (deterministic provenance — no Date.now)."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(uac_root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        logger.warning("  Could not read UAC HEAD sha: %s", exc)
        return None
    if proc.returncode != 0:
        logger.warning("  git rev-parse failed: %s", (proc.stderr or "").strip())
        return None
    return proc.stdout.strip() or None


def _dedup_nodes(nodes: list[CapabilityNode]) -> list[CapabilityNode]:
    """Collapse duplicate (kind, node_id) nodes, merging metadata (sorted keys).

    Later metadata wins on key collision; first-seen label is kept.
    """
    by_key: dict[tuple[str, str], CapabilityNode] = {}
    for n in nodes:
        key = (str(n.kind), n.node_id)
        existing = by_key.get(key)
        if existing is None:
            by_key[key] = n
        else:
            merged_meta = dict(existing.metadata)
            for mk, mv in n.metadata.items():
                merged_meta.setdefault(mk, mv)
            by_key[key] = CapabilityNode(
                kind=existing.kind,
                node_id=existing.node_id,
                label=existing.label,
                metadata=dict(sorted(merged_meta.items())),
            )
    return list(by_key.values())


def build_manifest(
    workspace_root: Path,
    uac_root: Path,
    sidecar_path: Path | None = None,
) -> tuple[CapabilityManifest, list[tuple[str, str, str]]]:
    """Assemble the full manifest from every extractor.

    Returns ``(manifest, annotation_orphans)`` where ``annotation_orphans`` is
    a list of ``(from_node, to_node, relation)`` tuples from the sidecar that
    had no matching edge (empty when no sidecar or all entries matched).
    """
    all_nodes: list[CapabilityNode] = []
    all_edges: list[CapabilityEdge] = []

    logger.info("1. Archetypes / families + capability registry...")
    n, e = extract_archetypes_and_families()
    all_nodes += n
    all_edges += e

    logger.info("1b. Archetype leg structures (F22 — per-leg restriction model)...")
    n, e = extract_leg_structures()
    all_nodes += n
    all_edges += e

    logger.info("2. Venues / chains / instrument types...")
    n, e = extract_venues()
    all_nodes += n
    all_edges += e

    logger.info("3. Data sources / modes / transports...")
    n, e = extract_data_sources()
    all_nodes += n
    all_edges += e

    logger.info("4. Gap registries + treasury split...")
    n, e = extract_gap_registries()
    all_nodes += n
    all_edges += e

    logger.info("5. Risk surface (kill-switch x risk-layer)...")
    n, e = extract_risk_surface()
    all_nodes += n
    all_edges += e

    logger.info("6. Service-resident registries (exec/features/ml, per-service venv)...")
    n, e = extract_service_registries(workspace_root)
    all_nodes += n
    all_edges += e

    logger.info("6b. Archetype -> execution-algo compatibility (Phase 6A)...")
    n, e = extract_algo_compatibility()
    all_nodes += n
    all_edges += e

    nodes = _dedup_nodes(all_nodes)

    # 7. Merge sidecar annotations into matching edges.
    annotation_orphans: list[tuple[str, str, str]] = []
    if sidecar_path is not None:
        logger.info("7. Merging sidecar annotations from %s...", sidecar_path)
        annotation_index = build_annotation_index(sidecar_path)
        if annotation_index:
            all_edges, annotation_orphans = merge_annotations_into_edges(all_edges, annotation_index)
    else:
        logger.info("7. No sidecar path provided — skipping annotation merge")

    manifest = CapabilityManifest(
        manifest_version=MANIFEST_VERSION,
        generated_from_commit=_read_uac_head_sha(uac_root),
        nodes=nodes,
        edges=all_edges,
    )
    return manifest, annotation_orphans


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the capability manifest")
    parser.add_argument("--output-dir", type=Path, default=None, help="Output directory (default: UAC openapi/)")
    parser.add_argument("--workspace-root", type=Path, default=None, help="Workspace root (default: PM's parent)")
    parser.add_argument("--uac-root", type=Path, default=None, help="unified-api-contracts repo (default: sibling)")
    parser.add_argument(
        "--sidecar",
        type=Path,
        default=None,
        help="Path to capability-annotations.yaml sidecar (default: same dir as this script)",
    )
    args = parser.parse_args()

    workspace_root = args.workspace_root or _SCRIPT_DIR.parent.parent.parent
    uac_root = args.uac_root or (workspace_root / "unified-api-contracts")
    output_dir = args.output_dir or (uac_root / "openapi")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Default sidecar: same directory as this script
    sidecar_path = args.sidecar or (_SCRIPT_DIR / "capability-annotations.yaml")

    logger.info("Generating capability manifest (workspace=%s)...", workspace_root)
    manifest, annotation_orphans = build_manifest(workspace_root, uac_root, sidecar_path=sidecar_path)

    canonical = manifest.to_canonical_dict()

    # Orphan + dead-end analysis (folded into manifest gaps + a text report).
    orphans = find_orphan_nodes(manifest.nodes, manifest.edges)
    unbuilt, logical = find_dead_ends(manifest.nodes, manifest.edges)
    # Fold the orphan/dead-end headline counts into the serialised gaps block.
    gaps_block = canonical.get("gaps", {})  # noqa: qg-empty-fallback
    if isinstance(gaps_block, dict):
        gaps_block["orphan_nodes"] = len(orphans)
        gaps_block["unbuilt_dead_ends"] = len(unbuilt)
        gaps_block["logical_dead_ends"] = len(logical)
        gaps_block["annotation_orphans"] = len(annotation_orphans)

    output_path = output_dir / "capability-manifest.json"
    with open(output_path, "w") as f:
        # sort_keys=True for determinism; to_canonical_dict already sorts the
        # node/edge lists, this guards any remaining dict-key order.
        json.dump(canonical, f, indent=2, sort_keys=True, default=str)
    logger.info("Wrote %s", output_path)

    report = render_orphan_report(
        orphans,
        unbuilt,
        logical,
        manifest.manifest_version,
        manifest.generated_from_commit,
    )
    # Append the annotation-orphan section (loud listing — never silent)
    report += render_annotation_orphan_section(annotation_orphans)
    report_path = output_dir / "capability-orphan-report.txt"
    with open(report_path, "w") as f:
        f.write(report)
    logger.info("Wrote %s", report_path)

    # Summary
    from collections import Counter

    node_kinds = Counter(str(n.kind) for n in manifest.nodes)
    edge_status = Counter(str(e.status) for e in manifest.edges)
    annotated = sum(1 for e in manifest.edges if e.agent_annotation is not None)
    print("\n" + "=" * 60)
    print("CAPABILITY MANIFEST — GENERATION SUMMARY")
    print("=" * 60)
    print(f"manifest_version: {manifest.manifest_version}")
    print(f"generated_from_commit: {manifest.generated_from_commit}")
    print(f"nodes: {len(manifest.nodes)}  edges: {len(manifest.edges)}")
    print("node kinds:")
    for k in sorted(node_kinds):
        print(f"  {k}: {node_kinds[k]}")
    print("edge statuses:")
    for k in sorted(edge_status):
        print(f"  {k}: {edge_status[k]}")
    print("gaps:")
    for k in sorted(gaps_block):
        print(f"  {k}: {gaps_block[k]}")
    print(f"orphans: {len(orphans)}  unbuilt dead-ends: {len(unbuilt)}  logical dead-ends: {len(logical)}")
    print(f"annotated edges: {annotated}  annotation orphans: {len(annotation_orphans)}")
    print(f"\nOutput: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
