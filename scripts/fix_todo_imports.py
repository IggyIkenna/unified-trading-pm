#!/usr/bin/env python3
"""
Script to fix the remaining TODO import mappings by applying specific replacements.
"""

import os
import re
from typing import Dict, List

# Specific TODO fixes
TODO_FIXES = {
    "from unified_trading_services import BaseDependencyChecker  # TODO: Map to explicit import":
        "from unified_trading_services.core.dependency_checker import BaseDependencyChecker",
    "from unified_trading_services import DependencyError  # TODO: Map to explicit import":
        "from unified_trading_services.core.dependency_checker import DependencyError",
    "from unified_trading_services import log_dependency_failures  # TODO: Map to explicit import":
        "from unified_trading_services.core.dependency_checker import log_dependency_failures",
    "from unified_trading_services import ParquetSchemaEnforcer  # TODO: Map to explicit import":
        "from unified_trading_services.core.parquet_schema_enforcer import ParquetSchemaEnforcer",
    "from unified_trading_services import ColumnSchema  # TODO: Map to explicit import":
        "from unified_trading_services.models.schema_definition import ColumnSchema",
    "from unified_trading_services import SchemaDefinition  # TODO: Map to explicit import":
        "from unified_trading_services.models.schema_definition import SchemaDefinition",
    "from unified_trading_services import BaseGCSWriter  # TODO: Map to explicit import":
        "from unified_trading_services.io.base_writer import BaseGCSWriter",
    "from unified_trading_services import BaseGCSLoader  # TODO: Map to explicit import":
        "from unified_trading_services.io.base_loader import BaseGCSLoader",
    "from unified_domain_client import create_market_candle_data_client  # TODO: Map to explicit import":
        "from unified_domain_client.clients import create_market_candle_data_client",
    "from unified_config_interface import BaseConfig  # TODO: Map to explicit import":
        "from unified_config_interface.base_config import BaseConfig",
    
    # Handle cases with 'as' aliasing
    "from unified_trading_services import BaseDependencyChecker as DependencyChecker  # TODO: Map to explicit import":
        "from unified_trading_services.core.dependency_checker import BaseDependencyChecker as DependencyChecker",
    "from unified_trading_services import BaseDependencyChecker as LookbackValidator  # TODO: Map to explicit import":
        "from unified_trading_services.core.dependency_checker import BaseDependencyChecker as LookbackValidator",
}

def fix_todos_in_file(file_path: str) -> bool:
    """Fix TODO imports in a single file. Returns True if file was modified."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply specific TODO fixes
        for todo_import, correct_import in TODO_FIXES.items():
            if todo_import in content:
                content = content.replace(todo_import, correct_import)
        
        # Handle double TODO comments (artifacts from multiple runs)
        content = re.sub(r'# TODO: Map to explicit import  # TODO: Map to explicit import', 
                        '# TODO: Map to explicit import', content)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def find_python_files(repo_path: str) -> List[str]:
    """Find all Python files in the repository."""
    python_files = []
    for root, dirs, files in os.walk(repo_path):
        # Skip .venv and build directories
        dirs[:] = [d for d in dirs if d not in ['.venv', 'build', '__pycache__', '.git', 'node_modules']]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def main():
    """Main function to fix TODO imports in all specified repositories."""
    base_path = "/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos"
    
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
    
    total_files_fixed = 0
    
    for repo in repositories:
        repo_path = os.path.join(base_path, repo)
        if os.path.exists(repo_path):
            print(f"Fixing TODO imports in {repo}...")
            python_files = find_python_files(repo_path)
            
            files_fixed = 0
            for py_file in python_files:
                if fix_todos_in_file(py_file):
                    files_fixed += 1
                    
            print(f"  Fixed {files_fixed} files")
            total_files_fixed += files_fixed
        else:
            print(f"Repository not found: {repo_path}")
    
    print(f"\nTotal files with TODO fixes applied: {total_files_fixed}")

if __name__ == "__main__":
    main()