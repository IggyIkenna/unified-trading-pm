#!/usr/bin/env python3
"""
Roll out quality gates to all Python repositories.
This script adds missing quality gate configurations to pyproject.toml files and creates Makefiles.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List

# Repository categorization and coverage thresholds
CRITICAL_SERVICES = {
    # 85% coverage for critical services (execution, trading, ML)
    "instruments-service": 85,
    "market-data-processing-service": 85, 
    "strategy-service": 85,
    "execution-services": 85,
    "ml-training-service": 85,
    "ml-inference-service": 85,
    "risk-and-exposure-service": 85,
    "position-balance-monitor-service": 85,
    "pnl-attribution-service": 85,
}

STANDARD_SERVICES = {
    # 70% coverage for standard services
    "alerting-system": 70,
    "features-calendar-service": 70,
    "features-delta-one-service": 70,
    "features-onchain-service": 70,
    "features-volatility-service": 70,
    "market-tick-data-handler": 70,
}

SHARED_LIBRARIES = {
    # 70% coverage for shared libraries
    "unified-cloud-services": 70,
    "unified-config-interface": 70,
    "unified-defi-execution-interface": 70,
    "unified-domain-services": 70,
    "unified-events-interface": 70,
    "unified-market-interface": 70,
    "unified-ml-interface": 70,
    "unified-trade-execution-interface": 70,
    "execution-algo-library": 70,
    "matching-engine-library": 70,
}

UTILITY_REPOS = {
    # 50% coverage for utilities
    "api-contracts": 50,
    "mr_report": 50,
    "unified-trading-codex": 50,
    "unified-trading-deployment-v3": 50,
}

ALL_REPOS = {**CRITICAL_SERVICES, **STANDARD_SERVICES, **SHARED_LIBRARIES, **UTILITY_REPOS}


def get_source_dir_name(repo_name: str) -> str:
    """Get the source directory name based on repository name."""
    return repo_name.replace("-", "_")


def get_coverage_config(coverage_threshold: int) -> str:
    """Generate coverage configuration section."""
    return f"""[tool.coverage.report]
fail_under = {coverage_threshold}  # {'Critical' if coverage_threshold == 85 else 'Standard' if coverage_threshold == 70 else 'Utility'} service
show_missing = true
skip_covered = false
precision = 1
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "@abstractmethod",
    "raise NotImplementedError",
]"""


def get_ruff_config() -> str:
    """Generate ruff configuration section."""
    return """[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "SIM", "RUF"]
ignore = ["E501"]  # line too long handled by formatter

[tool.ruff.format]
quote-style = "double"
indent-style = "space" """


def get_basedpyright_config(source_dir: str) -> str:
    """Generate basedpyright configuration section."""
    return f"""[tool.basedpyright]
include = ["{source_dir}"]
exclude = ["tests", "**/__pycache__", ".venv*", "build", "dist"]
pythonVersion = "3.13"
typeCheckingMode = "standard"
reportMissingImports = "error"
reportUnusedVariable = "warning"
reportUnusedImport = "warning" """


def get_makefile_content(source_dir: str) -> str:
    """Generate Makefile content."""
    return f""".PHONY: help quality-gates test lint format typecheck coverage install clean

help:
	@echo "Available targets:"
	@echo "  quality-gates  - Run all quality gates (lint, format, typecheck, test with coverage)"
	@echo "  test          - Run tests"
	@echo "  lint          - Run ruff linter"
	@echo "  format        - Run ruff formatter"
	@echo "  typecheck     - Run basedpyright type checker"
	@echo "  coverage      - Run tests with coverage reporting"
	@echo "  install       - Install development dependencies"
	@echo "  clean         - Clean build artifacts"

quality-gates:
	@echo "Running quality gates..."
	ruff check . --fix
	ruff format .
	basedpyright {source_dir}/
	pytest --cov={source_dir} --cov-report=term-missing

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

typecheck:
	basedpyright {source_dir}/

coverage:
	pytest --cov={source_dir} --cov-report=term-missing --cov-report=html

install:
	uv pip install -e ".[dev]"

clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {{}} + 2>/dev/null || true"""


def has_coverage_config(pyproject_path: Path) -> bool:
    """Check if pyproject.toml has coverage configuration."""
    if not pyproject_path.exists():
        return False
    content = pyproject_path.read_text()
    return "[tool.coverage.report]" in content


def has_ruff_config(pyproject_path: Path) -> bool:
    """Check if pyproject.toml has proper ruff configuration."""
    if not pyproject_path.exists():
        return False
    content = pyproject_path.read_text()
    return "[tool.ruff.format]" in content and '"UP"' in content


def has_basedpyright_config(pyproject_path: Path) -> bool:
    """Check if pyproject.toml has basedpyright configuration."""
    if not pyproject_path.exists():
        return False
    content = pyproject_path.read_text()
    return "[tool.basedpyright]" in content


def has_quality_gates_makefile(repo_path: Path) -> bool:
    """Check if Makefile exists with quality-gates target."""
    makefile_path = repo_path / "Makefile"
    if not makefile_path.exists():
        return False
    content = makefile_path.read_text()
    return "quality-gates:" in content


def update_pyproject_toml(pyproject_path: Path, repo_name: str, coverage_threshold: int, source_dir: str):
    """Update pyproject.toml with missing quality gate configurations."""
    if not pyproject_path.exists():
        print(f"  ⚠️  pyproject.toml not found in {repo_name}")
        return False

    content = pyproject_path.read_text()
    updated = False

    # Add coverage config if missing
    if not has_coverage_config(pyproject_path):
        print(f"  📊 Adding coverage configuration (threshold: {coverage_threshold}%)")
        content += "\n\n" + get_coverage_config(coverage_threshold)
        updated = True

    # Update/add ruff config if needed
    if not has_ruff_config(pyproject_path):
        print(f"  🔍 Updating ruff configuration")
        # Find existing [tool.ruff] section and replace it
        lines = content.split('\n')
        new_lines = []
        in_ruff_section = False
        ruff_added = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            if line.startswith("[tool.ruff"):
                # Start of ruff section - replace entire section
                in_ruff_section = True
                if not ruff_added:
                    new_lines.append(get_ruff_config())
                    ruff_added = True
                # Skip lines until next section
                i += 1
                while i < len(lines) and not lines[i].startswith("["):
                    i += 1
                continue
            else:
                new_lines.append(line)
            i += 1
        
        if not ruff_added:
            # No existing ruff section, add it
            new_lines.append("\n" + get_ruff_config())
        
        content = '\n'.join(new_lines)
        updated = True

    # Add basedpyright config if missing
    if not has_basedpyright_config(pyproject_path):
        print(f"  🎯 Adding basedpyright configuration")
        content += "\n\n" + get_basedpyright_config(source_dir)
        updated = True

    if updated:
        pyproject_path.write_text(content)
        print(f"  ✅ Updated pyproject.toml")
        return True
    
    return False


def create_makefile(repo_path: Path, source_dir: str):
    """Create Makefile with quality gates."""
    makefile_path = repo_path / "Makefile"
    
    if not has_quality_gates_makefile(repo_path):
        print(f"  📝 Creating Makefile with quality gates")
        makefile_path.write_text(get_makefile_content(source_dir))
        print(f"  ✅ Created Makefile")
        return True
    
    return False


def process_repository(repo_name: str, workspace_path: Path):
    """Process a single repository to add quality gates."""
    print(f"\n🔧 Processing {repo_name}")
    
    repo_path = workspace_path / repo_name
    if not repo_path.exists():
        print(f"  ❌ Repository directory not found: {repo_path}")
        return False

    pyproject_path = repo_path / "pyproject.toml"
    if not pyproject_path.exists():
        print(f"  ❌ No pyproject.toml found - not a Python repository")
        return False

    coverage_threshold = ALL_REPOS.get(repo_name, 70)
    source_dir = get_source_dir_name(repo_name)
    
    # Check if source directory exists
    source_path = repo_path / source_dir
    if not source_path.exists():
        print(f"  ⚠️  Source directory {source_dir} not found, trying alternative names")
        # Try some alternatives
        alternatives = [repo_name.replace("-", "_"), "src", repo_name]
        for alt in alternatives:
            alt_path = repo_path / alt
            if alt_path.is_dir() and any(alt_path.glob("*.py")):
                source_dir = alt
                break
        else:
            print(f"  ⚠️  Could not find source directory, using {source_dir} anyway")

    updated_pyproject = update_pyproject_toml(pyproject_path, repo_name, coverage_threshold, source_dir)
    created_makefile = create_makefile(repo_path, source_dir)
    
    if updated_pyproject or created_makefile:
        print(f"  ✅ {repo_name} updated successfully")
        return True
    else:
        print(f"  ✅ {repo_name} already has all quality gates")
        return True


def main():
    """Main function to roll out quality gates to all Python repositories."""
    # Get workspace path
    script_path = Path(__file__).parent.parent
    workspace_path = script_path
    
    print("🚀 Rolling out quality gates to all Python repositories")
    print(f"📁 Workspace: {workspace_path}")
    print(f"📊 Processing {len(ALL_REPOS)} repositories")
    
    print(f"\n📈 Coverage thresholds:")
    print(f"  🔴 Critical services (85%): {len(CRITICAL_SERVICES)} repos")
    print(f"  🟡 Standard services (70%): {len(STANDARD_SERVICES)} repos") 
    print(f"  🔵 Shared libraries (70%): {len(SHARED_LIBRARIES)} repos")
    print(f"  🟢 Utility repos (50%): {len(UTILITY_REPOS)} repos")

    success_count = 0
    error_count = 0

    for repo_name in sorted(ALL_REPOS.keys()):
        try:
            if process_repository(repo_name, workspace_path):
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            print(f"  ❌ Error processing {repo_name}: {e}")
            error_count += 1

    print(f"\n🎉 Quality gates rollout complete!")
    print(f"  ✅ Successfully processed: {success_count}")
    print(f"  ❌ Errors: {error_count}")
    print(f"  📊 Total: {success_count + error_count}")

    if error_count > 0:
        print(f"\n⚠️  Some repositories had errors. Please review the output above.")
        sys.exit(1)
    else:
        print(f"\n🎯 All repositories now have quality gates!")


if __name__ == "__main__":
    main()