#!/usr/bin/env python3
"""
Final round of import fixes for remaining TODO mappings.
"""

import os
import re
from typing import Dict, List

# Final comprehensive mapping for remaining imports
FINAL_MAPPINGS = {
    # Dependency checker models
    "from unified_cloud_services import DependencyStatus  # TODO: Map to explicit import":
        "from unified_cloud_services.core.dependency_checker import DependencyStatus",
    "from unified_cloud_services import DependencyReport  # TODO: Map to explicit import":
        "from unified_cloud_services.core.dependency_checker import DependencyReport",
    "from unified_cloud_services import DependencyFailure  # TODO: Map to explicit import":
        "from unified_cloud_services.core.dependency_checker import DependencyFailure",
    
    # Error models
    "from unified_cloud_services import ErrorCategory  # TODO: Map to explicit import":
        "from unified_cloud_services.models.error import ErrorCategory",
    "from unified_cloud_services import ErrorContext  # TODO: Map to explicit import":
        "from unified_cloud_services.models.error import ErrorContext",
    "from unified_cloud_services import ErrorSeverity  # TODO: Map to explicit import":
        "from unified_cloud_services.models.error import ErrorSeverity",
    
    # Observability models
    "from unified_cloud_services import OperationContext  # TODO: Map to explicit import":
        "from unified_cloud_services.models.observability import OperationContext",
    
    # Date utilities
    "from unified_cloud_services import parse_date  # TODO: Map to explicit import":
        "from unified_cloud_services.core.date_utils import parse_date",
    
    # Other models that might be in different packages or modules
    "from unified_cloud_services import DownloadTarget  # TODO: Map to explicit import":
        "from unified_cloud_services.models.download import DownloadTarget",
    "from unified_cloud_services import OrchestrationResult  # TODO: Map to explicit import":
        "from unified_cloud_services.models.orchestration import OrchestrationResult",
    "from unified_cloud_services import ValidationConfig  # TODO: Map to explicit import":
        "from unified_cloud_services.models.validation import ValidationConfig",
    
    # Config interface models
    "from unified_config_interface import InstrumentType  # TODO: Map to explicit import":
        "from unified_config_interface.models.instruments import InstrumentType",
    "from unified_config_interface import Venue  # TODO: Map to explicit import":
        "from unified_config_interface.models.venue import Venue",
    
    # Domain services models
    "from unified_domain_services import InstrumentKey  # TODO: Map to explicit import":
        "from unified_domain_services.models.instruments import InstrumentKey",
    
    # Unified feature calculator imports
    "from unified_feature_calculator import FeatureCalculator  # TODO: Map to explicit import":
        "from unified_feature_calculator.base import FeatureCalculator",
    "from unified_feature_calculator import OnChainFeatureCalculator  # TODO: Map to explicit import":
        "from unified_feature_calculator.calculators.onchain import OnChainFeatureCalculator",
        
    # Market interface models
    "from unified_market_interface import DataSourceMapping  # TODO: Map to explicit import":
        "from unified_market_interface.models.mapping import DataSourceMapping",
    "from unified_market_interface import CurveAdapter  # TODO: Map to explicit import":
        "from unified_market_interface.adapters.curve import CurveAdapter",
    "from unified_market_interface import EulerAdapter  # TODO: Map to explicit import":
        "from unified_market_interface.adapters.euler import EulerAdapter",
    "from unified_market_interface import FluidAdapter  # TODO: Map to explicit import":
        "from unified_market_interface.adapters.fluid import FluidAdapter",
        
    # Cloud services domain functions
    "from unified_cloud_services import create_market_data_service  # TODO: Map to explicit import":
        "from unified_cloud_services.domain.services import create_market_data_service",
}

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

def apply_final_fixes(file_path: str) -> bool:
    """Apply final import fixes to a single file. Returns True if file was modified."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply final mappings
        for todo_import, correct_import in FINAL_MAPPINGS.items():
            if todo_import in content:
                content = content.replace(todo_import, correct_import)
        
        # Write back if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function to apply final fixes to all specified repositories."""
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
            print(f"Applying final fixes to {repo}...")
            python_files = find_python_files(repo_path)
            
            files_fixed = 0
            for py_file in python_files:
                if apply_final_fixes(py_file):
                    files_fixed += 1
                    
            print(f"  Fixed {files_fixed} files")
            total_files_fixed += files_fixed
        else:
            print(f"Repository not found: {repo_path}")
    
    print(f"\nTotal files with final fixes applied: {total_files_fixed}")

if __name__ == "__main__":
    main()