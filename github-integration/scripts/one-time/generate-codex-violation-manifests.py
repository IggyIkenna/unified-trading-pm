#!/usr/bin/env python3
"""
Generate CODEX_VIOLATIONS_MANIFEST.md for each service repo. This is effectively `diff-checker`, but it's without the auto-creation of issues.

Runs the diff-checker script per repo and saves a human-readable manifest
of all codex violations that need fixing.

Usage:
    python generate-codex-violation-manifests.py [--dry-run]
"""

import json
import subprocess
import sys
from pathlib import Path

# 13 service repos for Initial Cleanup
REPOS = [
    "execution-services",
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


def run_diff_checker(codex_root: Path, workspace_root: Path, service_name: str) -> dict:
    """Run diff-checker for a specific service and return violations as JSON."""
    diff_checker_script = (
        codex_root / "11-project-management" / "github-integration" / "scripts" / "core" / "02-run-diff-checker.py"
    )

    # Run diff-checker with --dry-run and capture JSON output
    temp_json = workspace_root / f".temp_{service_name}_violations.json"

    cmd = [
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
        result = subprocess.run(
            cmd,
            cwd=workspace_root,
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            print("❌ FAILED")
            print(f"Error: {result.stderr}")
            return {"gaps": [], "error": result.stderr}

        # Read the JSON output
        if temp_json.exists():
            violations = json.loads(temp_json.read_text())
            temp_json.unlink()  # Clean up
            print(f"✅ Found {len(violations.get('gaps', []))} violations")
            return violations
        else:
            print("⚠️  No output file")
            return {"gaps": []}

    except Exception as e:
        print(f"❌ ERROR: {e}")
        return {"gaps": [], "error": str(e)}


def generate_manifest_markdown(service_name: str, violations: dict) -> str:
    """Generate human-readable markdown manifest from violations JSON."""
    gaps = violations.get("gaps", [])

    if not gaps:
        return f"""# Codex Violations Manifest: {service_name}

✅ **No violations found!** This service is compliant with all codex standards.

Generated: {violations.get("timestamp", "unknown")}
"""

    # Group by violation type
    by_type = {}
    for gap in gaps:
        gap_type = gap.get("gap_type", "unknown")
        by_type.setdefault(gap_type, []).append(gap)

    # Build markdown
    lines = [
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
    by_category = {}
    for gap in gaps:
        category = gap.get("category", "uncategorized")
        by_category.setdefault(category, []).append(gap)

    for category, items in sorted(by_category.items()):
        lines.extend(
            [
                f"### {category.replace('_', ' ').title()}",
                "",
                f"**Count**: {len(items)}",
                "",
            ]
        )

        for i, gap in enumerate(items, 1):
            lines.extend(
                [
                    f"#### {i}. {gap.get('title', 'Unknown')}",
                    "",
                    f"- **Priority**: {gap.get('priority', 'P3-low')}",
                    f"- **Gap ID**: `{gap.get('gap_id', 'unknown')}`",
                    f"- **Type**: {gap.get('gap_type', 'unknown')}",
                    f"- **Auto-fixable**: {'✅ Yes' if gap.get('auto_fixable', False) else '❌ No'}",
                    "",
                    "**Description**:",
                    gap.get("description", "No description"),
                    "",
                ]
            )

            affected = gap.get("affected_files", [])
            if affected:
                lines.append("**Affected Files**:")
                for f in affected[:10]:  # Limit to first 10
                    lines.append(f"- `{f}`")
                if len(affected) > 10:
                    lines.append(f"- ... and {len(affected) - 10} more files")
                lines.append("")

            codex_ref = gap.get("codex_reference", "")
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


def main():
    dry_run = "--dry-run" in sys.argv

    # Find paths
    script_dir = Path(__file__).parent
    # Script is in: unified-trading-codex/11-project-management/github-integration/scripts/one-time/
    # Codex root: unified-trading-codex/
    codex_root = script_dir.parent.parent.parent.parent
    # Workspace root: unified-trading-system-repos/
    workspace_root = codex_root.parent

    print(f"Codex root: {codex_root}")
    print(f"Workspace root: {workspace_root}")
    print(f"Dry run: {dry_run}")
    print()

    print("=" * 80)
    print("Generating Codex Violation Manifests for 13 Services")
    print("=" * 80)
    print()

    results = {}

    # Run diff-checker ONCE for all repos (it scans the entire workspace)
    print("Running diff-checker for entire workspace...")
    all_violations = run_diff_checker(codex_root, workspace_root, "workspace")

    print(f"  Total gaps found across workspace: {len(all_violations.get('gaps', []))}")
    print()

    # Now filter and create per-repo manifests
    for service in REPOS:
        service_dir = workspace_root / service

        if not service_dir.exists():
            print(f"⚠️  SKIP: {service} (directory not found)")
            continue

        # Filter gaps to only those from this service
        service_gaps = []
        for gap in all_violations.get("gaps", []):
            affected_files = gap.get("affected_files", [])
            # Check if any affected file belongs to this service
            if any(
                str(f).startswith(f"{service}/") or str(f).startswith(f"{workspace_root}/{service}/")
                for f in affected_files
            ):
                service_gaps.append(gap)

        # Create violations dict for this service
        service_violations = {"gaps": service_gaps, "timestamp": all_violations.get("timestamp", "unknown")}

        results[service] = service_violations

        print(f"  {service}: {len(service_gaps)} violations")

        # Generate manifest
        manifest_md = generate_manifest_markdown(service, service_violations)
        manifest_path = service_dir / "CODEX_VIOLATIONS_MANIFEST.md"

        if not dry_run:
            manifest_path.write_text(manifest_md)
            print(f"    → Saved to {manifest_path.relative_to(workspace_root)}")
        else:
            print(f"    → Would save to {manifest_path.relative_to(workspace_root)}")

        print()

    # Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print()

    total_violations = 0
    for service, violations in results.items():
        count = len(violations.get("gaps", []))
        total_violations += count
        status = "✅" if count == 0 else f"❌ {count} violations"
        print(f"  {service:40s} {status}")

    print()
    print(f"Total violations across all services: {total_violations}")
    print()

    if dry_run:
        print("🔍 DRY RUN: No files written. Re-run without --dry-run to save manifests.")
    else:
        print("✅ DONE: Manifests saved to each service directory.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
