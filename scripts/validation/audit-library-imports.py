#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Import Audit Script for Unified Libraries Split

Scans all service repos to:
1. Detect which split libraries are actually imported
2. Find fallback patterns (try/except ImportError)
3. Distinguish direct imports vs UCS re-exports
4. Identify StorageClient abstraction leaks (Issue #1)
5. Generate structured report with recommendations

Usage:
    cd unified-trading-codex/scripts
    python audit-library-imports.py

Output:
    - Console report with per-service findings
    - JSON report: audit-report.json
    - Recommendations for migration priority
"""

from __future__ import annotations

import ast
import json
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import ClassVar


@dataclass
class ImportInfo:
    """Information about an import statement."""

    module: str
    names: list[str]
    is_fallback: bool
    file_path: str
    line_number: int


@dataclass
class ServiceImportReport:
    """Import report for a single service."""

    service_name: str
    direct_imports: dict[str, list[str]]  # library → list of files
    ucs_imports: dict[str, list[str]]  # UCS import → list of files
    fallback_patterns: list[dict[str, str]]  # [{library, file, lines}]
    storageclient_issues: list[dict[str, str]]  # [{method, file, line}]
    recommendation: str
    migration_tier: int


class ImportAuditor(ast.NodeVisitor):
    """AST visitor to detect import patterns."""

    SPLIT_LIBRARIES: ClassVar[set[str]] = {
        "unified_trading_library.events",
        "unified_trading_library.config_interface",
        "unified_market_interface",
        "unified_order_interface",
        "execution_algo_library",
    }

    UCS_RE_EXPORTS: ClassVar[set[str]] = {
        "setup_events",
        "log_event",
        "publish_coordination_event",
        "subscribe_coordination_events",
        "load_config",
    }

    STORAGECLIENT_PROBLEM_METHODS: ClassVar[set[str]] = {
        ".bucket(",
        "bucket(",
        "bucket_obj",
    }

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.imports: list[ImportInfo] = []
        self.in_try_block = False
        self.try_depth = 0
        self.storageclient_issues: list[dict[str, str]] = []

    def visit_Try(self, node: ast.Try) -> None:
        """Track try blocks for fallback pattern detection."""
        self.in_try_block = True
        self.try_depth += 1
        self.generic_visit(node)
        self.try_depth -= 1
        if self.try_depth == 0:
            self.in_try_block = False

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        """Visit 'from X import Y' statements."""
        if node.module and (
            node.module in self.SPLIT_LIBRARIES
            or node.module.startswith(tuple(f"{lib}." for lib in self.SPLIT_LIBRARIES))
            or node.module == "unified_trading_services"
            or node.module.startswith("unified_trading_services.")
        ):
            # Check for split library imports
            names = [alias.name for alias in node.names]
            self.imports.append(
                ImportInfo(
                    module=node.module,
                    names=names,
                    is_fallback=self.in_try_block,
                    file_path=self.file_path,
                    line_number=node.lineno,
                )
            )

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        """Visit 'import X' statements."""
        for alias in node.names:
            if (
                alias.name in self.SPLIT_LIBRARIES
                or alias.name.startswith(tuple(f"{lib}." for lib in self.SPLIT_LIBRARIES))
                or alias.name == "unified_trading_services"
                or alias.name.startswith("unified_trading_services.")
            ):
                self.imports.append(
                    ImportInfo(
                        module=alias.name,
                        names=[],
                        is_fallback=self.in_try_block,
                        file_path=self.file_path,
                        line_number=node.lineno,
                    )
                )

        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        """Visit attribute access (e.g., client.bucket())."""
        # Check for StorageClient abstraction leaks
        if isinstance(node.value, ast.Name) and node.attr == "bucket":
            # Check for .bucket() calls
            self.storageclient_issues.append(
                {
                    "method": ".bucket()",
                    "file": self.file_path,
                    "line": str(node.lineno),
                    "context": "StorageClient has no .bucket() method (GCP-specific)",
                }
            )

        self.generic_visit(node)


def scan_file(file_path: Path) -> tuple[list[ImportInfo], list[dict[str, str]]]:
    """Scan a single Python file for imports."""
    try:
        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(file_path))
        auditor = ImportAuditor(str(file_path))
        auditor.visit(tree)
        return auditor.imports, auditor.storageclient_issues

    except (SyntaxError, UnicodeDecodeError):
        # Skip files that can't be parsed
        return [], []


def scan_service_repo(service_path: Path) -> tuple[list[ImportInfo], list[dict[str, str]]]:
    """Scan all Python files in a service repo."""
    all_imports = []
    all_storageclient_issues = []

    # Find all .py files
    for py_file in service_path.rglob("*.py"):
        # Skip common non-source directories
        if any(
            part in py_file.parts for part in [".venv", "venv", "__pycache__", ".git", "node_modules", "build", "dist"]
        ):
            continue

        imports, issues = scan_file(py_file)
        all_imports.extend(imports)
        all_storageclient_issues.extend(issues)

    return all_imports, all_storageclient_issues


def analyze_imports(imports: list[ImportInfo]) -> dict[str, object]:
    """Analyze imports to generate report."""
    # Group direct imports by library
    direct_imports = defaultdict(set)
    for imp in imports:
        if imp.module in ImportAuditor.SPLIT_LIBRARIES and not imp.is_fallback:
            direct_imports[imp.module].add(imp.file_path)

    # Group UCS imports by imported name
    ucs_imports = defaultdict(set)
    for imp in imports:
        if imp.module.startswith("unified_trading_services"):
            for name in imp.names:
                ucs_imports[name].add(imp.file_path)

    # Find fallback patterns
    fallback_patterns = []
    fallback_imports = [imp for imp in imports if imp.is_fallback]
    for imp in fallback_imports:
        if imp.module in ImportAuditor.SPLIT_LIBRARIES:
            fallback_patterns.append(
                {
                    "library": imp.module,
                    "file": imp.file_path,
                    "line": imp.line_number,
                    "names": imp.names,
                }
            )

    return {
        "direct_imports": {lib: list(files) for lib, files in direct_imports.items()},
        "ucs_imports": {name: list(files) for name, files in ucs_imports.items()},
        "fallback_patterns": fallback_patterns,
    }


def generate_recommendation(
    service_name: str, direct_imports: dict, ucs_imports: dict, fallback_patterns: list, storageclient_issues: list
) -> tuple[str, int]:
    """Generate migration recommendation and tier assignment."""
    # Count split library usage
    num_split_libs = len(direct_imports)
    has_fallbacks = len(fallback_patterns) > 0
    has_storageclient_issues = len(storageclient_issues) > 0

    # Determine tier based on service name and complexity
    tier_1_services = {
        "execution-service",
        "position-balance-monitor-service",
        "risk-and-exposure-service",
    }
    tier_2_services = {
        "strategy-service",
        "market-tick-data-service",
        "market-data-processing-service",
    }

    if service_name in tier_1_services:
        tier = 1
        if has_fallbacks:
            n = len(fallback_patterns)
            recommendation = (
                f"🔥 MIGRATE IMMEDIATELY - Complex service with {n} fallback pattern(s). "
                "Remove fallbacks and use direct imports."
            )
        elif num_split_libs >= 1:
            recommendation = (
                f"✅ ALREADY USING {num_split_libs} split lib(s) directly. "
                "Complete migration by adding to pyproject.toml and updating CI workflow."
            )
        else:
            recommendation = (
                "🔥 MIGRATE IMMEDIATELY - Complex service should use direct imports for clearer architecture."
            )

    elif service_name in tier_2_services:
        tier = 2
        if has_fallbacks:
            recommendation = (
                f"⚠️ MIGRATE LATER (3-6 months) - Has {len(fallback_patterns)} fallback pattern(s). Medium priority."
            )
        elif num_split_libs >= 1:
            recommendation = (
                f"⚠️ MIGRATE LATER (3-6 months) - Already uses {num_split_libs} split lib(s). Medium priority."
            )
        else:
            recommendation = "⚠️ MIGRATE LATER (3-6 months) - Medium complexity, benefits from direct imports."

    else:  # Tier 3
        tier = 3
        if has_fallbacks:
            n = len(fallback_patterns)
            recommendation = (
                f"💡 KEEP TRANSITIVE - Simple service. Fallback patterns are fine. ({n} fallback(s) detected)"
            )
        else:
            recommendation = "💡 KEEP TRANSITIVE - Simple service. Transitive dependencies sufficient."

    # Add StorageClient issues to recommendation
    if has_storageclient_issues:
        recommendation += (
            f"\n   ⚠️ STORAGECLIENT ISSUE: {len(storageclient_issues)} call(s) to GCP-specific API. See Issue #1."
        )

    return recommendation, tier


def audit_service(service_path: Path) -> ServiceImportReport:
    """Audit a single service and generate report."""
    service_name = service_path.name

    # Scan all Python files
    imports, storageclient_issues = scan_service_repo(service_path)

    # Analyze imports
    analysis = analyze_imports(imports)

    # Generate recommendation
    recommendation, tier = generate_recommendation(
        service_name,
        analysis["direct_imports"],
        analysis["ucs_imports"],
        analysis["fallback_patterns"],
        storageclient_issues,
    )

    return ServiceImportReport(
        service_name=service_name,
        direct_imports=analysis["direct_imports"],
        ucs_imports=analysis["ucs_imports"],
        fallback_patterns=analysis["fallback_patterns"],
        storageclient_issues=storageclient_issues,
        recommendation=recommendation,
        migration_tier=tier,
    )


def print_report(reports: list[ServiceImportReport]) -> None:
    """Print human-readable report to console."""
    print("\n" + "=" * 80)
    print("UNIFIED LIBRARIES IMPORT AUDIT REPORT")
    print("=" * 80)
    print(f"\nTotal services scanned: {len(reports)}\n")

    # Group by tier
    by_tier = defaultdict(list)
    for report in reports:
        by_tier[report.migration_tier].append(report)

    # Print by tier
    for tier in sorted(by_tier.keys()):
        tier_name = {1: "Tier 1: Migrate First", 2: "Tier 2: Migrate Later", 3: "Tier 3: Keep Transitive"}[tier]
        print(f"\n{'─' * 80}")
        print(f"{tier_name} ({len(by_tier[tier])} services)")
        print("─" * 80)

        for report in sorted(by_tier[tier], key=lambda r: r.service_name):
            print(f"\n📦 {report.service_name}")
            print("─" * 40)

            # Direct imports
            if report.direct_imports:
                print("  ✅ Direct imports:")
                for lib, files in report.direct_imports.items():
                    print(f"     • {lib} ({len(files)} file(s))")
            else:
                print("  ⚪ No direct split library imports")

            # UCS imports (show only re-exports)
            ucs_re_exports_used = {
                name: files for name, files in report.ucs_imports.items() if name in ImportAuditor.UCS_RE_EXPORTS
            }
            if ucs_re_exports_used:
                print("  📥 Via UCS re-exports:")
                for name, files in ucs_re_exports_used.items():
                    print(f"     • {name} ({len(files)} file(s))")

            # Fallback patterns
            if report.fallback_patterns:
                print(f"  ⚠️  Fallback patterns detected: {len(report.fallback_patterns)}")
                for fb in report.fallback_patterns[:3]:  # Show first 3
                    print(f"     • {fb['library']} in {Path(fb['file']).name}:{fb['line']}")
                if len(report.fallback_patterns) > 3:
                    print(f"     • ... and {len(report.fallback_patterns) - 3} more")

            # StorageClient issues
            if report.storageclient_issues:
                print(f"  🚨 StorageClient API issues: {len(report.storageclient_issues)}")
                for issue in report.storageclient_issues[:3]:  # Show first 3
                    print(f"     • {issue['method']} in {Path(issue['file']).name}:{issue['line']}")
                if len(report.storageclient_issues) > 3:
                    print(f"     • ... and {len(report.storageclient_issues) - 3} more")

            # Recommendation
            print(f"\n  📊 {report.recommendation}")

    # Summary statistics
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS")
    print("=" * 80)

    total_direct = sum(len(r.direct_imports) for r in reports)
    total_fallbacks = sum(len(r.fallback_patterns) for r in reports)
    total_storageclient_issues = sum(len(r.storageclient_issues) for r in reports)

    print(f"\nTotal services: {len(reports)}")
    print(f"  • Tier 1 (migrate first): {len(by_tier[1])}")
    print(f"  • Tier 2 (migrate later): {len(by_tier[2])}")
    print(f"  • Tier 3 (keep transitive): {len(by_tier[3])}")

    print(f"\nDirect split library imports: {total_direct} libraries across all services")
    print(f"Fallback patterns detected: {total_fallbacks}")
    print(f"StorageClient API issues: {total_storageclient_issues} (Issue #1)")

    # Library usage summary
    print("\n" + "─" * 80)
    print("LIBRARY USAGE SUMMARY")
    print("─" * 80)

    lib_usage = defaultdict(int)
    for report in reports:
        for lib in report.direct_imports:
            lib_usage[lib] += 1

    for lib in sorted(lib_usage.keys()):
        print(f"  {lib}: {lib_usage[lib]} service(s) use directly")

    # Fallback pattern summary
    fallback_services = [r.service_name for r in reports if r.fallback_patterns]
    if fallback_services:
        print("\n" + "─" * 80)
        print("SERVICES WITH FALLBACK PATTERNS (candidates for cleanup)")
        print("─" * 80)
        for service_name in sorted(fallback_services):
            report = next(r for r in reports if r.service_name == service_name)
            print(f"  • {service_name} ({len(report.fallback_patterns)} fallback(s))")

    # StorageClient issue summary
    storageclient_services = [r.service_name for r in reports if r.storageclient_issues]
    if storageclient_services:
        print("\n" + "─" * 80)
        print("STORAGECLIENT API ISSUES (Issue #1 - Abstraction Leak)")
        print("─" * 80)
        for service_name in sorted(storageclient_services):
            report = next(r for r in reports if r.service_name == service_name)
            print(f"  • {service_name} ({len(report.storageclient_issues)} issue(s))")
        print("\n  💡 Fix: Add list_blobs(bucket, prefix, max_results) method to StorageClient")
        print("     See: unified-trading-codex/issues/2026-02-17-dependency-checker-gcs-bugs.md")


def main():
    """Main entry point."""
    # Find workspace root (unified-trading-system-repos)
    script_path = Path(__file__).resolve()
    workspace_root = script_path.parent.parent.parent

    if not workspace_root.exists():
        print(f"❌ Workspace not found: {workspace_root}")
        sys.exit(1)

    print(f"🔍 Scanning workspace: {workspace_root}")
    print("   Looking for service directories (*-service/)\n")

    # Find all service repos
    service_dirs = sorted([d for d in workspace_root.iterdir() if d.is_dir() and d.name.endswith("-service")])

    if not service_dirs:
        print("❌ No service directories found")
        sys.exit(1)

    print(f"Found {len(service_dirs)} service(s):")
    for svc in service_dirs:
        print(f"  • {svc.name}")
    print()

    # Audit each service
    reports = []
    for service_path in service_dirs:
        print(f"Scanning {service_path.name}...", end=" ")
        report = audit_service(service_path)
        reports.append(report)
        direct = len(report.direct_imports)
        fallback = len(report.fallback_patterns)
        storage = len(report.storageclient_issues)
        print(f"✅ ({direct} direct, {fallback} fallback, {storage} StorageClient issues)")

    # Print human-readable report
    print_report(reports)

    # Save JSON report
    output_path = workspace_root / "unified-trading-codex" / "scripts" / "audit-report.json"
    with open(output_path, "w") as f:
        json.dump([asdict(r) for r in reports], f, indent=2)

    print(f"\n📄 Full report saved to: {output_path}")
    print("\n✅ Audit complete")


if __name__ == "__main__":
    main()
