#!/usr/bin/env python3
"""
Check Import Patterns v2 - With Circular Import Detection and Prevention

This enhanced version checks for import pattern violations while also
detecting potential circular import issues and suggesting fixes.

Usage:
    python check-import-patterns-v2.py           # Check all files
    python check-import-patterns-v2.py --fix     # Auto-fix violations
    python check-import-patterns-v2.py --circular # Check for circular imports
    python check-import-patterns-v2.py --safe-fix # Fix with circular import safety
"""

import argparse
import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Set, Dict
import importlib.util
from collections import defaultdict

# External packages that should only use top-level imports
EXTERNAL_PACKAGES = {
    'unified_config_interface',
    'unified_config_service',
    'unified_events_interface',
    'unified_domain_services',
    'unified_cloud_services',
    'unified_market_interface',
    'unified_trade_execution_interface',
    'unified_ml_interface',
    'unified_defi_execution_interface',
    'execution_algo_library',
    'matching_engine_library',
}

# Dependency hierarchy (lower level cannot import from higher level)
DEPENDENCY_LEVELS = {
    0: {'unified_config_interface', 'unified_events_interface'},
    1: {'unified_cloud_services', 'unified_domain_services'},
    2: {'unified_market_interface', 'unified_trade_execution_interface', 'unified_ml_interface'},
    3: {'execution_algo_library', 'matching_engine_library'},
}

# Known circular import risks (bidirectional dependencies)
CIRCULAR_RISKS = [
    ('unified_market_interface', 'unified_trade_execution_interface'),
    ('unified_ml_interface', 'unified_domain_services'),
]

# Patterns for detecting deep imports
DEEP_IMPORT_PATTERN = re.compile(
    r'^from\s+(' + '|'.join(EXTERNAL_PACKAGES) + r')\.(\w+(?:\.\w+)*)\s+import'
)

# Pattern for from imports
FROM_IMPORT_PATTERN = re.compile(
    r'^(\s*)from\s+([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)\s+import\s+(.+)$'
)


class ImportViolation:
    """Represents an import pattern violation."""
    
    def __init__(self, file_path: str, line_no: int, original: str, 
                 package: str, module_path: str, imports: str,
                 circular_risk: bool = False):
        self.file_path = file_path
        self.line_no = line_no
        self.original = original
        self.package = package
        self.module_path = module_path
        self.imports = imports
        self.circular_risk = circular_risk
        
    def get_fixed_import(self, safe_mode: bool = False) -> str:
        """Generate the corrected import statement."""
        indent = re.match(r'^(\s*)', self.original).group(1)
        
        if safe_mode and self.circular_risk:
            # Use function-level import for circular risk
            return f"{indent}# Moved to function level to avoid circular import: {self.package}"
        else:
            return f"{indent}from {self.package} import {self.imports}"
    
    def get_safe_alternative(self) -> str:
        """Get safe alternative for circular import risks."""
        indent = re.match(r'^(\s*)', self.original).group(1)
        return (f"{indent}# To avoid circular import, use inside function:\n"
                f"{indent}# def your_function():\n"
                f"{indent}#     from {self.package} import {self.imports}")
    
    def __str__(self) -> str:
        risk_marker = " [CIRCULAR RISK]" if self.circular_risk else ""
        return (f"{self.file_path}:{self.line_no}: "
                f"Deep import from {self.package}.{self.module_path}{risk_marker}")


class CircularImportDetector:
    """Detects potential circular import issues."""
    
    def __init__(self):
        self.import_graph = defaultdict(set)
        self.package_levels = {}
        
        # Build package level mapping
        for level, packages in DEPENDENCY_LEVELS.items():
            for package in packages:
                self.package_levels[package] = level
    
    def analyze_file(self, file_path: Path) -> List[str]:
        """Analyze a file for import patterns that might cause circular imports."""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
                
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module and any(node.module.startswith(pkg) for pkg in EXTERNAL_PACKAGES):
                        # Check if this import could cause issues
                        issue = self._check_import_safety(file_path, node.module)
                        if issue:
                            issues.append(issue)
                            
        except Exception as e:
            pass  # Ignore parsing errors
            
        return issues
    
    def _check_import_safety(self, file_path: Path, imported_module: str) -> Optional[str]:
        """Check if an import is safe from circular dependencies."""
        # Get the current package from file path
        current_package = self._get_package_from_path(file_path)
        if not current_package:
            return None
            
        # Get the imported package
        imported_package = imported_module.split('.')[0]
        
        # Check for known circular risks
        for pkg1, pkg2 in CIRCULAR_RISKS:
            if (current_package == pkg1 and imported_package == pkg2) or \
               (current_package == pkg2 and imported_package == pkg1):
                return f"Circular import risk between {current_package} and {imported_package}"
        
        # Check dependency levels
        current_level = self.package_levels.get(current_package, -1)
        imported_level = self.package_levels.get(imported_package, -1)
        
        if current_level >= 0 and imported_level >= 0:
            if current_level < imported_level:
                return f"Reverse dependency: Level {current_level} importing from Level {imported_level}"
                
        return None
    
    def _get_package_from_path(self, file_path: Path) -> Optional[str]:
        """Extract package name from file path."""
        parts = file_path.parts
        for part in parts:
            if part in EXTERNAL_PACKAGES:
                return part
        return None


class EnhancedImportChecker:
    """Enhanced import checker with circular import detection."""
    
    def __init__(self, verbose: bool = False, check_circular: bool = False):
        self.verbose = verbose
        self.check_circular = check_circular
        self.violations: List[ImportViolation] = []
        self.circular_detector = CircularImportDetector() if check_circular else None
        self.files_checked = 0
        self.files_with_violations = set()
        self.circular_warnings = []
        
    def check_file(self, file_path: Path) -> List[ImportViolation]:
        """Check a single file for import violations."""
        violations = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Check for circular import risks if enabled
            if self.check_circular:
                circular_issues = self.circular_detector.analyze_file(file_path)
                self.circular_warnings.extend(circular_issues)
                
            for line_no, line in enumerate(lines, 1):
                match = DEEP_IMPORT_PATTERN.match(line.strip())
                if match:
                    package = match.group(1)
                    module_path = match.group(2)
                    
                    # Check if this is a circular risk
                    circular_risk = False
                    if self.check_circular:
                        for pkg1, pkg2 in CIRCULAR_RISKS:
                            if package in [pkg1, pkg2]:
                                circular_risk = True
                                break
                    
                    # Extract what's being imported
                    import_match = FROM_IMPORT_PATTERN.match(line)
                    if import_match:
                        imports = import_match.group(3)
                        violation = ImportViolation(
                            str(file_path), line_no, line.rstrip(),
                            package, module_path, imports,
                            circular_risk=circular_risk
                        )
                        violations.append(violation)
                        
        except Exception as e:
            if self.verbose:
                print(f"Error checking {file_path}: {e}")
                
        return violations
    
    def check_directory(self, directory: Path) -> None:
        """Recursively check all Python files in a directory."""
        for file_path in directory.rglob('*.py'):
            # Skip certain directories
            if any(part in file_path.parts for part in 
                   ['.venv', 'venv', '__pycache__', '.git', 'node_modules']):
                continue
                
            self.files_checked += 1
            file_violations = self.check_file(file_path)
            
            if file_violations:
                self.violations.extend(file_violations)
                self.files_with_violations.add(str(file_path))
                
    def fix_file(self, file_path: str, violations: List[ImportViolation], 
                 safe_mode: bool = False) -> bool:
        """Fix violations in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Track which violations to convert to function-level imports
            function_level_imports = []
            
            # Sort violations by line number in reverse to avoid offset issues
            sorted_violations = sorted(violations, key=lambda v: v.line_no, reverse=True)
            
            for violation in sorted_violations:
                if safe_mode and violation.circular_risk:
                    # Add comment about moving to function level
                    lines[violation.line_no - 1] = violation.get_safe_alternative() + '\n'
                    function_level_imports.append(violation)
                else:
                    # Replace with fixed import
                    lines[violation.line_no - 1] = violation.get_fixed_import(safe_mode) + '\n'
                
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
                
            # Report function-level imports if any
            if function_level_imports:
                print(f"  ⚠️  {len(function_level_imports)} imports need manual function-level conversion")
                for v in function_level_imports:
                    print(f"     Line {v.line_no}: from {v.package} import {v.imports}")
                
            return True
            
        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False
            
    def fix_violations(self, safe_mode: bool = False) -> int:
        """Fix all found violations."""
        if not self.violations:
            return 0
            
        # Group violations by file
        violations_by_file = {}
        for violation in self.violations:
            if violation.file_path not in violations_by_file:
                violations_by_file[violation.file_path] = []
            violations_by_file[violation.file_path].append(violation)
            
        fixed_count = 0
        for file_path, file_violations in violations_by_file.items():
            if self.fix_file(file_path, file_violations, safe_mode):
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
            package_counts = {}
            circular_count = 0
            for v in self.violations:
                package_counts[v.package] = package_counts.get(v.package, 0) + 1
                if v.circular_risk:
                    circular_count += 1
            for package, count in sorted(package_counts.items()):
                print(f"  {package}: {count}")
            
            if circular_count > 0:
                print(f"\n⚠️  Circular import risks: {circular_count}")
                print("  Consider using function-level imports for these")
                
        if self.circular_warnings:
            print(f"\n⚠️  Circular Import Warnings: {len(self.circular_warnings)}")
            for warning in self.circular_warnings[:5]:  # Show first 5
                print(f"  • {warning}")
                
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
            if violation.circular_risk:
                print(f"  ⚠️  CIRCULAR RISK - Consider function-level import")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Enhanced import pattern checker with circular import detection'
    )
    parser.add_argument(
        'paths', nargs='*', default=['.'],
        help='Paths to check (default: current directory)'
    )
    parser.add_argument(
        '--fix', action='store_true',
        help='Automatically fix violations'
    )
    parser.add_argument(
        '--safe-fix', action='store_true',
        help='Fix with circular import safety (adds comments for risky imports)'
    )
    parser.add_argument(
        '--circular', action='store_true',
        help='Check for potential circular imports'
    )
    parser.add_argument(
        '--verbose', action='store_true',
        help='Show detailed output'
    )
    parser.add_argument(
        '--quiet', action='store_true',
        help='Only show errors'
    )
    
    args = parser.parse_args()
    
    checker = EnhancedImportChecker(
        verbose=args.verbose,
        check_circular=args.circular or args.safe_fix
    )
    
    # Check all specified paths
    for path in args.paths:
        path_obj = Path(path).resolve()
        if path_obj.is_file():
            if path_obj.suffix == '.py':
                checker.files_checked += 1
                violations = checker.check_file(path_obj)
                if violations:
                    checker.violations.extend(violations)
                    checker.files_with_violations.add(str(path_obj))
        elif path_obj.is_dir():
            checker.check_directory(path_obj)
        else:
            print(f"Warning: {path} is not a valid file or directory")
            
    # Handle output based on mode
    if args.fix or args.safe_fix:
        if checker.violations:
            fixed_count = checker.fix_violations(safe_mode=args.safe_fix)
            print(f"\n✅ Fixed {fixed_count} import violations")
            if args.safe_fix:
                print("📝 Check comments for imports that need manual function-level conversion")
            sys.exit(0)
        else:
            if not args.quiet:
                print("✅ No import pattern violations found")
            sys.exit(0)
    else:
        if args.verbose:
            checker.print_violations()
            
        if not args.quiet:
            checker.print_summary()
            
        if checker.violations:
            print("\n❌ Import pattern violations detected!")
            print("To fix automatically, run: python check-import-patterns-v2.py --fix")
            print("For circular-import-safe fixes: python check-import-patterns-v2.py --safe-fix")
            sys.exit(1)
        else:
            if not args.quiet:
                print("\n✅ No import pattern violations found")
            sys.exit(0)


if __name__ == '__main__':
    main()