#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Check Import Patterns - Enforce top-level imports for external dependencies

This script checks Python files for violations of the external import standards.
It ensures that imports from unified libraries use top-level imports only.

Usage:
    python check-import-patterns.py           # Check all files
    python check-import-patterns.py --verbose # Show detailed output
    python check-import-patterns.py --fix     # Auto-fix violations
    python check-import-patterns.py src/      # Check specific directory
"""

import argparse
import re
import sys
from pathlib import Path

# External packages that should only use top-level imports
EXTERNAL_PACKAGES = {
    "unified_trading_library.config_interface",
    "unified_config_service",
    "unified_trading_library.events",
    "unified_domain_client",
    "unified_trading_library",
    "unified_trading_services",
    "unified_market_interface",
    "unified_trade_execution_interface",
    "unified_ml_interface",
    "unified_defi_execution_interface",
    "execution_algo_library",
    "matching_engine_library",
}

# Patterns for detecting deep imports
_sorted_pkgs = sorted(EXTERNAL_PACKAGES, key=len, reverse=True)
DEEP_IMPORT_PATTERN = re.compile(r"^from\s+(" + "|".join(_sorted_pkgs) + r")\.(\w+(?:\.\w+)*)\s+import")

# Pattern for from imports
FROM_IMPORT_PATTERN = re.compile(
    r"^(\s*)from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)"
    r"\s+import\s+(.+)$"
)


class ImportViolation:
    """Represents an import pattern violation."""

    def __init__(
        self,
        file_path: str,
        line_no: int,
        original: str,
        package: str,
        module_path: str,
        imports: str,
    ):
        self.file_path = file_path
        self.line_no = line_no
        self.original = original
        self.package = package
        self.module_path = module_path
        self.imports = imports

    def get_fixed_import(self) -> str:
        """Generate the corrected import statement."""
        # Extract indentation from original
        m = re.match(r"^(\s*)", self.original)
        indent = m.group(1) if m else ""
        return f"{indent}from {self.package} import {self.imports}"

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_no}: Deep import from {self.package}.{self.module_path}"


class ImportChecker:
    """Checks and fixes import patterns in Python files."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.violations: list[ImportViolation] = []
        self.files_checked = 0
        self.files_with_violations: set[str] = set()

    @staticmethod
    def _is_exempt(line: str) -> bool:
        """True if the line carries a per-line qg-deep-import opt-out marker."""
        return "# noqa: qg-deep-import" in line or "# noqa:qg-deep-import" in line

    @staticmethod
    def _is_same_package(file_path: Path, package: str) -> bool:
        """True if the importing file belongs to the same package as the import target."""
        path_str = str(file_path).replace("\\", "/")
        return f"/{package}/" in path_str or path_str.startswith(package + "/")

    def _check_line(self, file_path: Path, line_no: int, line: str) -> ImportViolation | None:
        """Return a violation for a single line, or None if the line is fine."""
        if self._is_exempt(line):
            return None
        match = DEEP_IMPORT_PATTERN.match(line.strip())
        if not match:
            return None
        package = match.group(1)
        module_path = match.group(2)
        if self._is_same_package(file_path, package):
            return None
        import_match = FROM_IMPORT_PATTERN.match(line)
        if not import_match:
            return None
        return ImportViolation(str(file_path), line_no, line.rstrip(), package, module_path, import_match.group(3))

    def check_file(self, file_path: Path) -> list[ImportViolation]:
        """Check a single file for import violations."""
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
        except (OSError, ValueError) as e:
            if self.verbose:
                print(f"Error checking {file_path}: {e}")
            return []

        violations: list[ImportViolation] = []
        for line_no, line in enumerate(lines, 1):
            violation = self._check_line(file_path, line_no, line)
            if violation is not None:
                violations.append(violation)
        return violations

    def check_directory(self, directory: Path) -> None:
        """Recursively check all Python files in a directory."""
        for file_path in directory.rglob("*.py"):
            # Skip certain directories
            # .deps: some repos (e.g. market-tick-data-service) vendor-clone sibling
            # packages (unified-trading-library, unified-api-contracts) here for Cloud
            # Build staging — that's the sibling's OWN source tree, not this repo's code,
            # so it must never be scanned for THIS repo's import-convention violations.
            # .claude: nested per-agent git worktrees (.claude/worktrees/<id>/) can carry a
            # stale/divergent snapshot of the same repo's source.
            skip_dirs = {".venv", "venv", "__pycache__", ".git", "node_modules", ".deps", ".claude"}
            if any(part in file_path.parts for part in skip_dirs):
                continue

            self.files_checked += 1
            file_violations = self.check_file(file_path)

            if file_violations:
                self.violations.extend(file_violations)
                self.files_with_violations.add(str(file_path))

    def fix_file(self, file_path: str, violations: list[ImportViolation]) -> bool:
        """Fix violations in a file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()

            # Sort violations by line number in reverse to avoid offset issues
            sorted_violations = sorted(violations, key=lambda v: v.line_no, reverse=True)

            for violation in sorted_violations:
                # Replace the line with fixed import
                lines[violation.line_no - 1] = violation.get_fixed_import() + "\n"

            with open(file_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            return True

        except (OSError, ValueError) as e:
            print(f"Error fixing {file_path}: {e}")
            return False

    def fix_violations(self) -> int:
        """Fix all found violations."""
        if not self.violations:
            return 0

        # Group violations by file
        violations_by_file: dict[str, list[ImportViolation]] = {}
        for violation in self.violations:
            if violation.file_path not in violations_by_file:
                violations_by_file[violation.file_path] = []
            violations_by_file[violation.file_path].append(violation)

        fixed_count = 0
        for file_path, file_violations in violations_by_file.items():
            if self.fix_file(file_path, file_violations):
                fixed_count += len(file_violations)
                print(f"Fixed {len(file_violations)} violations in {file_path}")

        return fixed_count

    def print_summary(self) -> None:
        """Print summary of findings."""
        print("\n" + "=" * 60)
        print("Import Pattern Check Summary")
        print("=" * 60)
        print(f"Files checked: {self.files_checked}")
        print(f"Files with violations: {len(self.files_with_violations)}")
        print(f"Total violations: {len(self.violations)}")

        if self.violations:
            print("\nViolations by package:")
            package_counts: dict[str, int] = {}
            for v in self.violations:
                package_counts[v.package] = package_counts.get(v.package, 0) + 1
            for package, count in sorted(package_counts.items()):
                print(f"  {package}: {count}")

    def print_violations(self) -> None:
        """Print detailed violation information."""
        if not self.violations:
            return

        print("\nDetailed Violations:")
        print("-" * 60)

        for violation in self.violations:
            print(f"\n{violation}")
            print(f"  Original: {violation.original}")
            print(f"  Fixed:    {violation.get_fixed_import()}")


def main() -> None:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Check and fix import patterns for external dependencies",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=["."],
        help="Paths to check (default: current directory)",
    )
    parser.add_argument("--fix", action="store_true", help="Fix violations")
    parser.add_argument("--verbose", action="store_true", help="Detailed output")
    parser.add_argument("--quiet", action="store_true", help="Only show errors")

    args = parser.parse_args()

    verbose = bool(getattr(args, "verbose", False))
    fix = bool(getattr(args, "fix", False))
    quiet = bool(getattr(args, "quiet", False))
    paths: list[str] = list(getattr(args, "paths", ["."]))

    checker = ImportChecker(verbose=verbose)
    _collect_violations(checker, paths)
    _report_and_exit(checker, fix=fix, quiet=quiet, verbose=verbose)


def _collect_violations(checker: ImportChecker, paths: list[str]) -> None:
    """Scan *paths* and accumulate violations on *checker*."""
    for path in paths:
        path_obj = Path(path).resolve()
        if path_obj.is_file():
            if path_obj.suffix == ".py":
                checker.files_checked += 1
                violations = checker.check_file(path_obj)
                if violations:
                    checker.violations.extend(violations)
                    checker.files_with_violations.add(str(path_obj))
        elif path_obj.is_dir():
            checker.check_directory(path_obj)
        else:
            print(f"Warning: {path} is not a valid file or directory")


def _report_and_exit(
    checker: ImportChecker,
    *,
    fix: bool,
    quiet: bool,
    verbose: bool,
) -> None:
    """Print results or apply fixes, then exit."""
    if fix:
        _apply_fixes_and_exit(checker, quiet=quiet)

    if verbose:
        checker.print_violations()
    if not quiet:
        checker.print_summary()

    if checker.violations:
        print("\nImport pattern violations detected!")
        print("Run: python check-import-patterns.py --fix")
        sys.exit(1)
    if not quiet:
        print("\nNo import pattern violations found")
    sys.exit(0)


def _apply_fixes_and_exit(
    checker: ImportChecker,
    *,
    quiet: bool,
) -> None:
    """Apply fixes and exit."""
    if checker.violations:
        fixed_count = checker.fix_violations()
        print(f"\nFixed {fixed_count} import violations")
    elif not quiet:
        print("No import pattern violations found")
    sys.exit(0)


if __name__ == "__main__":
    main()
