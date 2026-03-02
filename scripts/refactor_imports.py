#!/usr/bin/env python3
"""
Script to refactor all imports from implicit to explicit across specified repositories.

This script performs systematic find-and-replace operations to update import statements
from the old implicit format to the new explicit format.
"""

import os
import re
from typing import Dict, List, Tuple

# Import mappings to apply
IMPORT_MAPPINGS = {
    # unified_trading_services mappings
    "from unified_trading_services import get_storage_client": "from unified_trading_services.core.client_factory import get_storage_client",
    "from unified_trading_services import get_secret_client": "from unified_trading_services.core.client_factory import get_secret_client",
    "from unified_trading_services import CloudConfig": "from unified_trading_services.core.cloud_config import CloudConfig",
    "from unified_trading_services import CloudTarget": "from unified_trading_services.core.cloud_config import CloudTarget",
    "from unified_trading_services import UnifiedMonitor": "from unified_trading_services.core.unified_monitor import UnifiedMonitor",
    "from unified_trading_services import StandardizedDomainCloudService": "from unified_trading_services.domain.standardized_service import StandardizedDomainCloudService",
    "from unified_trading_services import setup_cloud_logging": "from unified_trading_services.core.logging import setup_cloud_logging",
    "from unified_trading_services import handle_api_errors": "from unified_trading_services.core.error_handling import handle_api_errors",
    "from unified_trading_services import GracefulShutdownHandler": "from unified_trading_services.core.signal_handler import GracefulShutdownHandler",

    # unified_events_interface mappings
    "from unified_events_interface import setup_events": "from unified_events_interface.core.events import setup_events",
    "from unified_events_interface import log_event": "from unified_events_interface.core.events import log_event",

    # unified_config_interface mappings
    "from unified_config_interface import UnifiedCloudConfig": "from unified_config_interface.core.config import UnifiedCloudConfig",
}

# Additional complex import patterns that need special handling
COMPLEX_IMPORT_PATTERNS = [
    # Multi-line import from unified_trading_services
    (
        r'from unified_trading_services import \(\s*([^)]+)\s*\)',
        lambda match: handle_multiline_unified_trading_services_import(match.group(1))
    ),
    # Single line multiple imports
    (
        r'from unified_trading_services import ([^,\n]+(?:,\s*[^,\n]+)*)',
        handle_single_line_multiple_imports
    )
]

def handle_multiline_unified_trading_services_import(import_content: str) -> str:
    """Handle multiline import statements from unified_trading_services."""
    imports = [imp.strip() for imp in import_content.split(',') if imp.strip()]
    result_lines = []

    for imp in imports:
        imp = imp.strip()
        if imp in ["get_storage_client", "get_secret_client"]:
            result_lines.append(f"from unified_trading_services.core.client_factory import {imp}")
        elif imp in ["CloudConfig", "CloudTarget"]:
            result_lines.append(f"from unified_trading_services.core.cloud_config import {imp}")
        elif imp == "UnifiedMonitor":
            result_lines.append(f"from unified_trading_services.core.unified_monitor import {imp}")
        elif imp == "StandardizedDomainCloudService":
            result_lines.append(f"from unified_trading_services.domain.standardized_service import {imp}")
        elif imp == "setup_cloud_logging":
            result_lines.append(f"from unified_trading_services.core.logging import {imp}")
        elif imp == "handle_api_errors":
            result_lines.append(f"from unified_trading_services.core.error_handling import {imp}")
        elif imp == "GracefulShutdownHandler":
            result_lines.append(f"from unified_trading_services.core.signal_handler import {imp}")
        else:
            # For now, keep unmapped imports as is but add a comment
            result_lines.append(f"from unified_trading_services import {imp}  # TODO: Map to explicit import")

    return '\n'.join(result_lines)

def handle_single_line_multiple_imports(match) -> str:
    """Handle single line multiple imports from unified_trading_services."""
    import_content = match.group(1)
    imports = [imp.strip() for imp in import_content.split(',') if imp.strip()]
    result_lines = []

    for imp in imports:
        imp = imp.strip()
        if imp in ["get_storage_client", "get_secret_client"]:
            result_lines.append(f"from unified_trading_services.core.client_factory import {imp}")
        elif imp in ["CloudConfig", "CloudTarget"]:
            result_lines.append(f"from unified_trading_services.core.cloud_config import {imp}")
        elif imp == "UnifiedMonitor":
            result_lines.append(f"from unified_trading_services.core.unified_monitor import {imp}")
        elif imp == "StandardizedDomainCloudService":
            result_lines.append(f"from unified_trading_services.domain.standardized_service import {imp}")
        elif imp == "setup_cloud_logging":
            result_lines.append(f"from unified_trading_services.core.logging import {imp}")
        elif imp == "handle_api_errors":
            result_lines.append(f"from unified_trading_services.core.error_handling import {imp}")
        elif imp == "GracefulShutdownHandler":
            result_lines.append(f"from unified_trading_services.core.signal_handler import {imp}")
        else:
            # For now, keep unmapped imports as is but add a comment
            result_lines.append(f"from unified_trading_services import {imp}  # TODO: Map to explicit import")

    return '\n'.join(result_lines)

def find_python_files(repo_path: str) -> List[str]:
    """Find all Python files in the repository, excluding .venv and build directories."""
    python_files = []
    for root, dirs, files in os.walk(repo_path):
        # Skip .venv and build directories
        dirs[:] = [d for d in dirs if d not in ['.venv', 'build', '__pycache__', '.git']]

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    return python_files

def refactor_file(file_path: str) -> Tuple[bool, List[str]]:
    """Refactor imports in a single file. Returns (was_modified, changes_made)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content
        changes_made = []

        # Apply simple mappings first
        for old_import, new_import in IMPORT_MAPPINGS.items():
            if old_import in content:
                content = content.replace(old_import, new_import)
                changes_made.append(f"{old_import} -> {new_import}")

        # Apply complex pattern replacements
        for pattern, handler in COMPLEX_IMPORT_PATTERNS:
            matches = list(re.finditer(pattern, content, re.MULTILINE | re.DOTALL))
            for match in reversed(matches):  # Process in reverse order to maintain indices
                if callable(handler):
                    replacement = handler(match)
                else:
                    replacement = handler
                content = content[:match.start()] + replacement + content[match.end():]
                changes_made.append(f"Complex pattern: {match.group(0)} -> multiline replacements")

        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes_made

        return False, []

    except (ConnectionError, TimeoutError, OSError, ValueError) as e:
        print(f"Error processing {file_path}: {e}")
        return False, [f"Error: {e}"]

def refactor_repository(repo_path: str) -> Dict[str, any]:
    """Refactor all imports in a repository."""
    print(f"Processing repository: {repo_path}")

    python_files = find_python_files(repo_path)
    print(f"Found {len(python_files)} Python files")

    results = {
        'total_files': len(python_files),
        'modified_files': 0,
        'changes': {},
        'errors': []
    }

    for file_path in python_files:
        was_modified, changes = refactor_file(file_path)
        if was_modified:
            results['modified_files'] += 1
            results['changes'][file_path] = changes
        elif changes:  # Had errors
            results['errors'].append((file_path, changes))

    return results

def main():
    """Main function to refactor all specified repositories."""
    base_path = "/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"

    repositories = [
        "instruments-service",
        "market-data-processing-service",
        "strategy-service",
        "execution-service",
        "position-balance-monitor-service",
        "risk-and-exposure-service"
    ]

    total_results = {}

    for repo in repositories:
        repo_path = os.path.join(base_path, repo)
        if os.path.exists(repo_path):
            results = refactor_repository(repo_path)
            total_results[repo] = results
        else:
            print(f"Repository not found: {repo_path}")
            total_results[repo] = {"error": "Repository not found"}

    # Print summary
    print("\n" + "="*80)
    print("REFACTORING SUMMARY")
    print("="*80)

    for repo, results in total_results.items():
        if 'error' in results:
            print(f"\n{repo}: {results['error']}")
            continue

        print(f"\n{repo}:")
        print(f"  Total files: {results['total_files']}")
        print(f"  Modified files: {results['modified_files']}")

        if results['changes']:
            print("  Changes made:")
            for file_path, changes in list(results['changes'].items())[:5]:  # Show first 5
                rel_path = os.path.relpath(file_path, base_path)
                print(f"    {rel_path}:")
                for change in changes[:3]:  # Show first 3 changes per file
                    print(f"      - {change}")
                if len(changes) > 3:
                    print(f"      ... and {len(changes) - 3} more")
            if len(results['changes']) > 5:
                print(f"    ... and {len(results['changes']) - 5} more files")

        if results['errors']:
            print(f"  Errors: {len(results['errors'])}")
            for file_path, error_msgs in results['errors'][:3]:
                rel_path = os.path.relpath(file_path, base_path)
                print(f"    {rel_path}: {error_msgs}")

if __name__ == "__main__":
    main()
