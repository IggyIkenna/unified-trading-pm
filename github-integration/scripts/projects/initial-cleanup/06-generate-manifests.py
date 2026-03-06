#!/usr/bin/env python3
"""
Generate CODEX_VIOLATIONS_MANIFEST.md for Initial Cleanup Project

Scans each service repo for codex violations and creates a human-readable
manifest file (CODEX_VIOLATIONS_MANIFEST.md) listing all violations.

This is part of the Initial Cleanup project (Project #5).

Usage:
    cd unified-trading-codex/11-project-management/github-integration/scripts/projects/initial-cleanup
    python3 06-generate-manifests.py [--dry-run] [--repos "repo1,repo2"]
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import cast

# Type alias
JsonDict = dict[str, object]

# 13 service repos for Initial Cleanup
REPOS: list[str] = [
    "execution-service",
    "strategy-service",
    "instruments-service",
    "unified-trading-services",
    "market-data-processing-service",
    "ml-training-service",
    "ml-inference-service",
    "features-delta-one-service",
    "features-volatility-service",
    "features-calendar-service",
    "features-onchain-service",
    "market-tick-data-handler",
    "unified-trading-deployment-v2",
]


def _get_gaps(violations: JsonDict) -> list[JsonDict]:
    """Safely extract gaps list from violations dict."""
    raw: object = violations.get("gaps") or []
    if isinstance(raw, list):
        raw_list: list[object] = cast(list[object], raw)
        return [cast(JsonDict, item) for item in raw_list if isinstance(item, dict)]
    return []


def run_diff_checker(codex_root: Path, workspace_root: Path, service_name: str) -> JsonDict:
    """Run diff-checker for a specific service and return violations as JSON."""
    # Use the utilities script in this project directory
    diff_checker_script: Path = (
        codex_root
        / "11-project-management"
        / "github-integration"
        / "scripts"
        / "projects"
        / "initial-cleanup"
        / "utilities"
        / "check-codex-violations.py"
    )

    # Run diff-checker with --dry-run and capture JSON output
    temp_json: Path = workspace_root / f".temp_{service_name}_violations.json"

    cmd: list[str] = [
        "python3",
        str(diff_checker_script),
        "--dry-run",
        "--output-json",
        str(temp_json),
        "--codex-dir",
        str(codex_root),
        "--workspace-dir",
        str(workspace_root),
        "--repo",
        f"IggyIkenna/{service_name}",
    ]

    print(f"  Running diff-checker for {service_name}...", end=" ", flush=True)

    try:
        result: subprocess.CompletedProcess[str] = subprocess.run(
            cmd,
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            print("FAILED")
            print(f"Error: {result.stderr}")
            return {"gaps": [], "error": result.stderr}

        # Read the JSON output
        if temp_json.exists():
            violations: JsonDict = cast(JsonDict, json.loads(temp_json.read_text()))
            temp_json.unlink()  # Clean up
            gaps: list[JsonDict] = _get_gaps(violations)
            print(f"Found {len(gaps)} violations")
            return violations
        else:
            print("No output file")
            return {"gaps": []}

    except (OSError, PermissionError, ValueError) as e:
        print(f"ERROR: {e}")
        return {"gaps": [], "error": str(e)}


def generate_manifest_markdown(service_name: str, violations: JsonDict) -> str:
    """Generate human-readable markdown manifest from violations JSON."""
    gaps: list[JsonDict] = _get_gaps(violations)

    if not gaps:
        return f"""# Codex Violations Manifest: {service_name}

No violations found! This service is compliant with all codex standards.

Generated: {violations.get("timestamp", "unknown")}
"""

    # Group by violation type
    by_type: dict[str, list[JsonDict]] = {}
    for gap in gaps:
        gap_type: str = str(gap.get("gap_type", "unknown"))
        by_type.setdefault(gap_type, []).append(gap)

    # Build markdown
    lines: list[str] = [
        f"# Codex Violations Manifest: {service_name}",
        "",
        f"**Total Violations**: {len(gaps)}",
        f"**Generated**: {violations.get('timestamp', 'unknown')}",
        "",
        "## Summary by Type",
        "",
    ]

    for gap_type, items in sorted(by_type.items()):
        lines.append(f"- **{gap_type}**: {len(items)} violations")

    lines.extend(
        [
            "",
            "---",
            "",
            "## Violations by Category",
            "",
        ]
    )

    # Group by category
    by_category: dict[str, list[JsonDict]] = {}
    for gap in gaps:
        category: str = str(gap.get("category", "uncategorized"))
        by_category.setdefault(category, []).append(gap)

    for cat_name, cat_items in sorted(by_category.items()):
        lines.extend(
            [
                f"### {cat_name.replace('_', ' ').title()}",
                "",
                f"**Count**: {len(cat_items)}",
                "",
            ]
        )

        for i, gap in enumerate(cat_items, 1):
            auto_fixable: bool = bool(gap.get("auto_fixable", False))
            lines.extend(
                [
                    f"#### {i}. {gap.get('title', 'Unknown')}",
                    "",
                    f"- **Priority**: {gap.get('priority', 'P3-low')}",
                    f"- **Gap ID**: `{gap.get('gap_id', 'unknown')}`",
                    f"- **Type**: {gap.get('gap_type', 'unknown')}",
                    f"- **Auto-fixable**: {'Yes' if auto_fixable else 'No'}",
                    "",
                    "**Description**:",
                    str(gap.get("description", "No description")),
                    "",
                ]
            )

            raw_affected: object = gap.get("affected_files") or []
            affected: list[str] = (
                [str(f) for f in cast(list[object], raw_affected)] if isinstance(raw_affected, list) else []
            )
            if affected:
                lines.append("**Affected Files**:")
                for af in affected[:10]:  # Limit to first 10
                    lines.append(f"- `{af}`")
                if len(affected) > 10:
                    lines.append(f"- ... and {len(affected) - 10} more files")
                lines.append("")

            codex_ref: str = str(gap.get("codex_reference", ""))
            if codex_ref:
                lines.extend(
                    [
                        f"**Codex Reference**: `{codex_ref}`",
                        "",
                    ]
                )

            lines.append("---")
            lines.append("")

    return "\n".join(lines)


def main() -> int:
    dry_run: bool = "--dry-run" in sys.argv

    # Find paths
    script_dir: Path = Path(__file__).parent
    codex_root: Path = script_dir.parent.parent.parent.parent
    workspace_root: Path = codex_root.parent

    print(f"Codex root: {codex_root}")
    print(f"Workspace root: {workspace_root}")
    print(f"Dry run: {dry_run}")
    print()

    print("=" * 80)
    print("Generating Codex Violation Manifests for 13 Services")
    print("=" * 80)
    print()

    results: dict[str, JsonDict] = {}

    # Run diff-checker ONCE for all repos (it scans the entire workspace)
    print("Running diff-checker for entire workspace...")
    all_violations: JsonDict = run_diff_checker(codex_root, workspace_root, "workspace")

    all_gaps: list[JsonDict] = _get_gaps(all_violations)
    print(f"  Total gaps found across workspace: {len(all_gaps)}")
    print()

    # Now filter and create per-repo manifests
    for service in REPOS:
        service_dir: Path = workspace_root / service

        if not service_dir.exists():
            print(f"  SKIP: {service} (directory not found)")
            continue

        # Filter gaps to only those from this service
        service_gaps: list[JsonDict] = []
        for gap in all_gaps:
            raw_affected_files: object = gap.get("affected_files") or []
            affected_files: list[str] = (
                [str(f) for f in cast(list[object], raw_affected_files)] if isinstance(raw_affected_files, list) else []
            )
            if any(
                af.startswith(f"{service}/") or af.startswith(f"{workspace_root}/{service}/") for af in affected_files
            ):
                service_gaps.append(gap)

        service_violations: JsonDict = {
            "gaps": service_gaps,
            "timestamp": all_violations.get("timestamp", "unknown"),
        }

        results[service] = service_violations

        print(f"  {service}: {len(service_gaps)} violations")

        manifest_md: str = generate_manifest_markdown(service, service_violations)
        manifest_path: Path = service_dir / "CODEX_VIOLATIONS_MANIFEST.md"

        if not dry_run:
            manifest_path.write_text(manifest_md)
            print(f"    Saved to {manifest_path.relative_to(workspace_root)}")
        else:
            print(f"    Would save to {manifest_path.relative_to(workspace_root)}")

        print()

    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()

    total_violations: int = 0
    for service, violations_data in results.items():
        svc_gaps: list[JsonDict] = _get_gaps(violations_data)
        count: int = len(svc_gaps)
        total_violations += count
        status: str = "OK" if count == 0 else f"{count} violations"
        print(f"  {service:40s} {status}")

    print()
    print(f"Total violations across all services: {total_violations}")
    print()

    if dry_run:
        print("DRY RUN: No files written. Re-run without --dry-run to save manifests.")
    else:
        print("DONE: Manifests saved to each service directory.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
