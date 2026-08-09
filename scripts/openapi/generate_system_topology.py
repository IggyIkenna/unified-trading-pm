# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""
Generate a system topology file from workspace manifests.

Extracts and aggregates:
- Workspace manifest (all 71 repos: types, deps, tiers, CI status, versions)
- Deployment topology (environments, protocol defaults, colocation, messaging)
- Data flow manifest (service→API→UI pipelines, batch vs live)
- Strategy manifest (all strategies: IDs, venues, maturity, capabilities)
- Derived dependency graph

Usage:
    python generate_system_topology.py [--output-dir PATH]

SSOT for UI/registry generators and hand-maintained docs: unified-trading-pm/docs/ui-alignment-ssot.md
"""

from __future__ import annotations

import argparse
import json
import logging
from pathlib import Path

import yaml

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_json(path: Path) -> dict[str, object] | list[object] | None:
    """Load a JSON file, returning None on failure."""
    if not path.exists():
        logger.warning("  File not found: %s", path)
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError) as e:
        logger.warning("  Failed to load %s: %s", path, e)
        return None


def load_yaml_file(path: Path) -> dict[str, object] | list[object] | None:
    """Load a YAML file, returning None on failure."""
    if not path.exists():
        logger.warning("  File not found: %s", path)
        return None
    try:
        with open(path) as f:
            return yaml.safe_load(f)
    except (OSError, yaml.YAMLError) as e:
        logger.warning("  Failed to load %s: %s", path, e)
        return None


def extract_workspace_manifest(pm_root: Path) -> dict[str, object]:
    """Extract the workspace manifest with repo metadata."""
    data: dict[str, object] = {}
    manifest_path = pm_root / "workspace-manifest.json"
    manifest = load_json(manifest_path)
    if not manifest:
        return data

    # Repos — full list with type, tier, deps, status
    repos = manifest.get("repositories", {})  # noqa: qg-empty-fallback
    repo_summaries = {}
    for name, info in repos.items():
        repo_summaries[name] = {
            "type": info.get("type"),
            "tier": info.get("tier"),
            "role": info.get("role"),
            "tags": info.get("tags", []),  # noqa: qg-empty-fallback
            "version": info.get("version"),
            "ci_status": info.get("ci_status"),
            "coverage_pct": info.get("coverage_pct"),
            "testing_level": info.get("testing_level"),
            "status": info.get("status"),
            "dependencies": [d.get("name") if isinstance(d, dict) else d for d in info.get("dependencies", [])],  # noqa: qg-empty-fallback
            "service_declaration": info.get("service_declaration"),
            "serves_ui": info.get("serves_ui"),
            "proxies_service": info.get("proxies_service"),
            "completion_path": info.get("completion_path"),
            "sit_level": info.get("sit_level"),
        }
    data["repositories"] = repo_summaries
    data["total_repos"] = len(repos)

    # Versions
    data["versions"] = manifest.get("versions", {})  # noqa: qg-empty-fallback

    # Topological order (build/deploy order)
    data["topological_order"] = manifest.get("topologicalOrder", [])  # noqa: qg-empty-fallback

    # Tier rules
    data["tier_rules"] = manifest.get("tier_rules", {})  # noqa: qg-empty-fallback

    # Deployment topology
    data["deployment_topology"] = manifest.get("deployment_topology", {})  # noqa: qg-empty-fallback

    # Staging status
    data["staging_status"] = manifest.get("staging_status", {})  # noqa: qg-empty-fallback
    data["active_feature_branch"] = manifest.get("active_feature_branch")

    # Publishing order
    data["publishing_order"] = manifest.get("publishingOrder", [])  # noqa: qg-empty-fallback

    # Completion paths
    data["completion_paths"] = manifest.get("completion_paths", {})  # noqa: qg-empty-fallback

    # Doc standards
    data["doc_standards"] = manifest.get("doc_standards", {})  # noqa: qg-empty-fallback

    logger.info("  Workspace manifest: %d repos", len(repos))
    return data


def extract_data_flows(pm_root: Path) -> list[object]:
    """Extract the data flow manifest."""
    path = pm_root / "data-flow-manifest.json"
    manifest = load_json(path)
    if not manifest:
        return []
    flows = manifest.get("data_flows", [])  # noqa: qg-empty-fallback
    logger.info("  Data flows: %d pipelines", len(flows))
    return flows


def extract_strategy_manifest(pm_root: Path) -> list[object]:
    """Extract the strategy manifest."""
    path = pm_root / "strategy-manifest.json"
    manifest = load_json(path)
    if not manifest:
        return []
    strategies = manifest.get("strategies", [])  # noqa: qg-empty-fallback
    logger.info("  Strategies: %d entries", len(strategies))
    return strategies


def extract_ui_api_flow_tests(pm_root: Path) -> dict[str, object] | list[object] | None:
    """Extract the UI/API flow test manifest."""
    path = pm_root / "ui-api-flow-test-manifest.yaml"
    data = load_yaml_file(path)
    if data:
        len(data) if isinstance(data, list) else len(data.get("flows", data.get("tests", [])))  # noqa: qg-empty-fallback
        logger.info("  UI/API flow tests loaded")
    return data


def extract_dependency_graph(pm_root: Path) -> dict[str, object] | list[object] | None:
    """Extract the derived dependency manifest."""
    path = pm_root / "derived-dependency-manifest.json"
    data = load_json(path)
    if data:
        logger.info("  Derived dependency manifest loaded")
    return data


def extract_ui_api_mapping(pm_root: Path) -> dict[str, object]:
    """Extract the UI/API port mapping."""
    path = pm_root / "scripts" / "dev" / "ui-api-mapping.json"
    data = load_json(path)
    if data:
        stacks = data.get("stacks", {})  # noqa: qg-empty-fallback
        logger.info("  UI/API mapping: %d stacks", len(stacks))
        return stacks
    return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate system topology")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    workspace_root = Path(__file__).resolve().parent.parent.parent.parent
    pm_root = workspace_root / "unified-trading-pm"
    output_dir = args.output_dir or (workspace_root / "unified-api-contracts" / "openapi")
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Generating system topology...\n")

    topology: dict[str, object] = {
        "_meta": {
            "description": (
                "System topology: all repos, deployment config, data flow pipelines, "
                "strategy manifest, dependency graph, and UI/API mappings. "
                "Extracted from workspace-manifest.json and related PM manifests."
            ),
            "generated_by": "generate_system_topology.py",
            "source_files": [
                "unified-trading-pm/workspace-manifest.json",
                "unified-trading-pm/data-flow-manifest.json",
                "unified-trading-pm/strategy-manifest.json",
                "unified-trading-pm/ui-api-flow-test-manifest.yaml",
                "unified-trading-pm/derived-dependency-manifest.json",
                "unified-trading-pm/scripts/dev/ui-api-mapping.json",
            ],
        }
    }

    logger.info("1. Workspace manifest...")
    workspace_data = extract_workspace_manifest(pm_root)
    topology["workspace"] = {
        "repositories": workspace_data.get("repositories", {}),  # noqa: qg-empty-fallback
        "total_repos": workspace_data.get("total_repos", 0),
        "versions": workspace_data.get("versions", {}),  # noqa: qg-empty-fallback
        "topological_order": workspace_data.get("topological_order", []),  # noqa: qg-empty-fallback
        "tier_rules": workspace_data.get("tier_rules", {}),  # noqa: qg-empty-fallback
        "publishing_order": workspace_data.get("publishing_order", []),  # noqa: qg-empty-fallback
        "completion_paths": workspace_data.get("completion_paths", {}),  # noqa: qg-empty-fallback
        "doc_standards": workspace_data.get("doc_standards", {}),  # noqa: qg-empty-fallback
        "active_feature_branch": workspace_data.get("active_feature_branch"),
        "staging_status": workspace_data.get("staging_status", {}),  # noqa: qg-empty-fallback
    }

    logger.info("\n2. Deployment topology...")
    topology["deployment"] = workspace_data.get("deployment_topology", {})  # noqa: qg-empty-fallback

    logger.info("\n3. Data flow pipelines...")
    topology["data_flows"] = extract_data_flows(pm_root)

    logger.info("\n4. Strategy manifest...")
    topology["strategies"] = extract_strategy_manifest(pm_root)

    logger.info("\n5. UI/API flow tests...")
    topology["ui_api_flow_tests"] = extract_ui_api_flow_tests(pm_root)

    logger.info("\n6. Dependency graph...")
    topology["dependency_graph"] = extract_dependency_graph(pm_root)

    logger.info("\n7. UI/API port mapping...")
    topology["ui_api_mapping"] = extract_ui_api_mapping(pm_root)

    # Write output
    output_path = output_dir / "system-topology.json"
    with open(output_path, "w") as f:
        json.dump(topology, f, indent=2, sort_keys=False, default=str)
    logger.info("\nOutput written: %s", output_path)

    # Summary
    ws = topology.get("workspace", {})  # noqa: qg-empty-fallback
    print("\n" + "=" * 60)
    print("SYSTEM TOPOLOGY — GENERATION SUMMARY")
    print("=" * 60)
    print(f"Repos:              {ws.get('total_repos', 0)}")
    print(f"Strategies:         {len(topology.get('strategies', []))}")  # noqa: qg-empty-fallback
    print(f"Data flow pipes:    {len(topology.get('data_flows', []))}")  # noqa: qg-empty-fallback
    print(f"UI/API stacks:      {len(topology.get('ui_api_mapping', {}))}")  # noqa: qg-empty-fallback
    dt = topology.get("deployment", {})  # noqa: qg-empty-fallback
    print(f"Environments:       {len(dt.get('environments', {}))}")  # noqa: qg-empty-fallback
    print(f"Protocol defaults:  {len(dt.get('protocol_defaults', {}))}")  # noqa: qg-empty-fallback
    print(f"Colocation groups:  {len(dt.get('colocation_groups', []))}")  # noqa: qg-empty-fallback
    print(f"\nOutput: {output_path}")
    print("=" * 60)


if __name__ == "__main__":
    main()
