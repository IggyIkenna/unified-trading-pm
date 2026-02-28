#!/usr/bin/env python3
"""
Comprehensive import refactoring script for specified repositories.

This script performs systematic find-and-replace operations to update import statements
from the old implicit format to the new explicit format across all specified repositories.
"""

import argparse
import glob
import os
import re
from pathlib import Path
from typing import Dict, List, Tuple

# Comprehensive import mappings based on actual package structure
IMPORT_MAPPINGS = {
    # ===== unified_trading_services =====
    # Client factory functions
    "from unified_trading_services import get_storage_client": "from unified_trading_services.core.client_factory import get_storage_client",
    "from unified_trading_services import get_secret_client": "from unified_trading_services.core.client_factory import get_secret_client",
    "from unified_trading_services import get_secret": "from unified_trading_services.core.client_factory import get_secret",
    "from unified_trading_services import download_from_storage": "from unified_trading_services.core.client_factory import download_from_storage",
    "from unified_trading_services import upload_to_storage": "from unified_trading_services.core.client_factory import upload_to_storage",
    "from unified_trading_services import storage_exists": "from unified_trading_services.core.client_factory import storage_exists",
    
    # Cloud configuration
    "from unified_trading_services import CloudConfig": "from unified_trading_services.core.cloud_config import CloudConfig",
    "from unified_trading_services import CloudTarget": "from unified_trading_services.core.cloud_config import CloudTarget",
    "from unified_trading_services import CloudProvider": "from unified_trading_services.core.cloud_config import CloudProvider",
    
    # Monitoring and validation
    "from unified_trading_services import UnifiedMonitor": "from unified_trading_services.core.unified_monitor import UnifiedMonitor",
    "from unified_trading_services import monitor_operation": "from unified_trading_services.core.unified_monitor import monitor_operation",
    "from unified_trading_services import track_operation": "from unified_trading_services.core.unified_monitor import track_operation",
    "from unified_trading_services import get_unified_monitor": "from unified_trading_services.core.unified_monitor import get_unified_monitor",
    "from unified_trading_services import validate_dataframe_memory": "from unified_trading_services.core.unified_monitor import validate_dataframe_memory",
    
    # Error handling
    "from unified_trading_services import handle_api_errors": "from unified_trading_services.core.error_handling import handle_api_errors",
    "from unified_trading_services import handle_storage_errors": "from unified_trading_services.core.error_handling import handle_storage_errors",
    "from unified_trading_services import with_error_handling": "from unified_trading_services.core.error_handling import with_error_handling",
    
    # Logging
    "from unified_trading_services import setup_cloud_logging": "from unified_trading_services.core.logging import setup_cloud_logging",
    "from unified_trading_services import log_with_context": "from unified_trading_services.core.logging import log_with_context",
    "from unified_trading_services import PerformanceLogger": "from unified_trading_services.core.logging import PerformanceLogger",
    
    # Domain services (legacy paths in unified_trading_services)
    "from unified_trading_services import StandardizedDomainCloudService": "from unified_trading_services.domain.standardized_service import StandardizedDomainCloudService",
    "from unified_trading_services import InstrumentsDomainClient": "from unified_trading_services.domain.clients import InstrumentsDomainClient",
    "from unified_trading_services import MarketDataDomainClient": "from unified_trading_services.domain.clients import MarketDataDomainClient",
    "from unified_trading_services import ExecutionDomainClient": "from unified_trading_services.domain.clients import ExecutionDomainClient",
    "from unified_trading_services import create_instruments_client": "from unified_trading_services.domain.clients import create_instruments_client",
    "from unified_trading_services import create_market_tick_data_client": "from unified_trading_services.domain.clients import create_market_tick_data_client",
    
    # Domain validation (legacy paths in unified_trading_services)
    "from unified_trading_services import DomainValidationService": "from unified_trading_services.domain.validation import DomainValidationService",
    "from unified_trading_services import DomainValidationConfig": "from unified_trading_services.domain.validation import DomainValidationConfig",
    "from unified_trading_services import validate_timestamp_date_alignment": "from unified_domain_client import validate_timestamp_date_alignment",

    # Date validation (moved to unified-domain-client)
    "from unified_trading_services import should_skip_date": "from unified_domain_client import should_skip_date",
    "from unified_trading_services import get_earliest_valid_date": "from unified_domain_client import get_earliest_valid_date",
    
    # Signal handling
    "from unified_trading_services import GracefulShutdownHandler": "from unified_trading_services.core.signal_handler import GracefulShutdownHandler",
    "from unified_trading_services import setup_graceful_shutdown": "from unified_trading_services.core.signal_handler import setup_graceful_shutdown",
    
    # Dependency checking
    "from unified_trading_services import BaseDependencyChecker": "from unified_trading_services.core.dependency_checker import BaseDependencyChecker",
    "from unified_trading_services import DependencyError": "from unified_trading_services.core.dependency_checker import DependencyError",
    "from unified_trading_services import log_dependency_failures": "from unified_trading_services.core.dependency_checker import log_dependency_failures",
    
    # Schema definitions and enforcement
    "from unified_trading_services import ParquetSchemaEnforcer": "from unified_trading_services.core.parquet_schema_enforcer import ParquetSchemaEnforcer",
    "from unified_trading_services import ColumnSchema": "from unified_trading_services.models.schema_definition import ColumnSchema",
    "from unified_trading_services import SchemaDefinition": "from unified_trading_services.models.schema_definition import SchemaDefinition",
    
    # I/O Writers and Loaders
    "from unified_trading_services import BaseGCSWriter": "from unified_trading_services.io.base_writer import BaseGCSWriter",
    "from unified_trading_services import BaseGCSLoader": "from unified_trading_services.io.base_loader import BaseGCSLoader",
    
    # ===== unified_domain_client =====
    "from unified_domain_client import InstrumentsDomainClient": "from unified_domain_client.clients.instruments import InstrumentsDomainClient",
    "from unified_domain_client import MarketDataDomainClient": "from unified_domain_client.clients.market_data import MarketDataDomainClient",
    "from unified_domain_client import DomainValidationService": "from unified_domain_client.validation import DomainValidationService",
    "from unified_domain_client import validate_timestamp_date_alignment": "from unified_domain_client.timestamp_validation import validate_timestamp_date_alignment",
    "from unified_domain_client import create_instruments_client": "from unified_domain_client.clients import create_instruments_client",
    "from unified_domain_client import create_market_tick_data_client": "from unified_domain_client.clients import create_market_tick_data_client",
    "from unified_domain_client import create_market_candle_data_client": "from unified_domain_client.clients import create_market_candle_data_client",
    "from unified_domain_client import should_skip_date": "from unified_domain_client.date_utils import should_skip_date",
    "from unified_domain_client import get_earliest_valid_date": "from unified_domain_client.date_utils import get_earliest_valid_date",
    
    # ===== unified_events_interface =====
    "from unified_events_interface import setup_events": "from unified_events_interface.core.events import setup_events",
    "from unified_events_interface import log_event": "from unified_events_interface.core.events import log_event",
    "from unified_events_interface import publish_coordination_event": "from unified_events_interface.pubsub.coordination import publish_coordination_event",
    
    # ===== unified_config_interface =====
    "from unified_config_interface import UnifiedCloudConfig": "from unified_config_interface.core.config import UnifiedCloudConfig",
    "from unified_config_interface import load_config": "from unified_config_interface.core.loader import load_config",
    "from unified_config_interface import BaseConfig": "from unified_config_interface.base_config import BaseConfig",
    
    # ===== unified_market_interface =====
    "from unified_market_interface import get_market_client": "from unified_market_interface.clients.factory import get_market_client",
    "from unified_market_interface import MarketClient": "from unified_market_interface.clients.base import MarketClient",
    
    # ===== execution_algo_library =====
    "from execution_algo_library import TWAPAlgorithm": "from execution_algo_library.algorithms import TWAPAlgorithm",
    "from execution_algo_library import VWAPAlgorithm": "from execution_algo_library.algorithms import VWAPAlgorithm",
    "from execution_algo_library import ExecutionAlgorithm": "from execution_algo_library.base_algorithm import ExecutionAlgorithm",
}

# Additional complex import patterns that need special handling
COMPLEX_IMPORT_PATTERNS = [
    # Multi-line import from unified_trading_services
    (
        r'from unified_trading_services import \(\s*([^)]+)\s*\)',
        lambda match: handle_multiline_unified_trading_services_import(match.group(1))
    ),
    # Multi-line import from unified_domain_client
    (
        r'from unified_domain_client import \(\s*([^)]+)\s*\)',
        lambda match: handle_multiline_unified_domain_client_import(match.group(1))
    ),
    # Single line multiple imports for all unified packages
    (
        r'from (unified_\w+) import ([^,\n]+(?:,\s*[^,\n]+)*)',
        lambda match: handle_single_line_multiple_imports(match)
    )
]

def handle_multiline_unified_trading_services_import(import_content: str) -> str:
    """Handle multiline import statements from unified_trading_services."""
    imports = [imp.strip() for imp in import_content.split(',') if imp.strip()]
    result_lines = []
    
    for imp in imports:
        imp = imp.strip()
        mapping_key = f"from unified_trading_services import {imp}"
        if mapping_key in IMPORT_MAPPINGS:
            result_lines.append(IMPORT_MAPPINGS[mapping_key])
        else:
            # For now, keep unmapped imports as is but add a comment
            result_lines.append(f"from unified_trading_services import {imp}  # TODO: Map to explicit import")
    
    return '\n'.join(result_lines)

def handle_multiline_unified_domain_client_import(import_content: str) -> str:
    """Handle multiline import statements from unified_domain_client."""
    imports = [imp.strip() for imp in import_content.split(',') if imp.strip()]
    result_lines = []
    
    for imp in imports:
        imp = imp.strip()
        mapping_key = f"from unified_domain_client import {imp}"
        if mapping_key in IMPORT_MAPPINGS:
            result_lines.append(IMPORT_MAPPINGS[mapping_key])
        else:
            # For now, keep unmapped imports as is but add a comment
            result_lines.append(f"from unified_domain_client import {imp}  # TODO: Map to explicit import")
    
    return '\n'.join(result_lines)

def handle_single_line_multiple_imports(match) -> str:
    """Handle single line multiple imports from unified packages."""
    package = match.group(1)
    import_content = match.group(2)
    imports = [imp.strip() for imp in import_content.split(',') if imp.strip()]
    result_lines = []
    
    for imp in imports:
        imp = imp.strip()
        mapping_key = f"from {package} import {imp}"
        if mapping_key in IMPORT_MAPPINGS:
            result_lines.append(IMPORT_MAPPINGS[mapping_key])
        else:
            # For now, keep unmapped imports as is but add a comment
            result_lines.append(f"from {package} import {imp}  # TODO: Map to explicit import")
    
    return '\n'.join(result_lines)

def find_python_files(repo_path: str) -> List[str]:
    """Find all Python files in the repository, excluding .venv and build directories."""
    python_files = []
    for root, dirs, files in os.walk(repo_path):
        # Skip .venv and build directories
        dirs[:] = [d for d in dirs if d not in ['.venv', 'build', '__pycache__', '.git', 'node_modules']]
        
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
                changes_made.append(f"Complex pattern: {match.group(0)[:50]}... -> multiline replacements")
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes_made
        
        return False, []
        
    except Exception as e:
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
        'errors': [],
        'complex_patterns': []
    }
    
    for file_path in python_files:
        was_modified, changes = refactor_file(file_path)
        if was_modified:
            results['modified_files'] += 1
            results['changes'][file_path] = changes
            # Look for TODO comments indicating complex patterns need manual review
            for change in changes:
                if 'TODO' in change:
                    results['complex_patterns'].append((file_path, change))
        elif changes:  # Had errors
            results['errors'].append((file_path, changes))
    
    return results

def main():
    """Main function to refactor all specified repositories."""
    base_path = "/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"
    
    # Target repositories as specified in the task
    repositories = [
        "ml-training-service",
        "ml-inference-service",
        "pnl-attribution-service",
        "features-calendar-service",
        "features-delta-one-service",
        "features-onchain-service",
        "features-volatility-service",
        "market-tick-data-handler"
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
    print("IMPORT REFACTORING SUMMARY")
    print("="*80)
    
    total_files_processed = 0
    total_files_modified = 0
    total_complex_patterns = 0
    total_errors = 0
    
    for repo, results in total_results.items():
        if 'error' in results:
            print(f"\n{repo}: {results['error']}")
            continue
            
        total_files_processed += results['total_files']
        total_files_modified += results['modified_files']
        total_complex_patterns += len(results['complex_patterns'])
        total_errors += len(results['errors'])
        
        print(f"\n{repo}:")
        print(f"  Total files: {results['total_files']}")
        print(f"  Modified files: {results['modified_files']}")
        print(f"  Complex patterns for review: {len(results['complex_patterns'])}")
        print(f"  Errors: {len(results['errors'])}")
        
        if results['changes']:
            print(f"  Sample changes:")
            for file_path, changes in list(results['changes'].items())[:3]:  # Show first 3
                rel_path = os.path.relpath(file_path, base_path)
                print(f"    {rel_path}:")
                for change in changes[:2]:  # Show first 2 changes per file
                    print(f"      - {change[:100]}...")
                if len(changes) > 2:
                    print(f"      ... and {len(changes) - 2} more")
            if len(results['changes']) > 3:
                print(f"    ... and {len(results['changes']) - 3} more files")
        
        if results['complex_patterns']:
            print(f"  Complex patterns needing manual review:")
            for file_path, pattern in results['complex_patterns'][:3]:
                rel_path = os.path.relpath(file_path, base_path)
                print(f"    {rel_path}: {pattern[:80]}...")
        
        if results['errors']:
            print(f"  Errors encountered:")
            for file_path, error_msgs in results['errors'][:3]:
                rel_path = os.path.relpath(file_path, base_path)
                print(f"    {rel_path}: {error_msgs}")
    
    print(f"\n" + "="*80)
    print("OVERALL SUMMARY:")
    print(f"Total repositories processed: {len([r for r in total_results.values() if 'error' not in r])}")
    print(f"Total Python files processed: {total_files_processed}")
    print(f"Total Python files modified: {total_files_modified}")
    print(f"Total complex patterns for manual review: {total_complex_patterns}")
    print(f"Total errors: {total_errors}")
    print("="*80)

if __name__ == "__main__":
    main()