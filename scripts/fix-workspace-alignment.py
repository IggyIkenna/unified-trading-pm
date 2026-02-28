#!/usr/bin/env python3
"""
Fix workspace configuration alignment issues.

This script ensures all workspace files have:
1. cursorpyright.analysis.extraPaths (for import resolution)
2. python.envFile (for .env loading)
3. Proper settings order (diagnosticSeverityOverrides near other Pylance settings)
4. All strict linting settings from the root workspace
"""

import json
from pathlib import Path
from typing import Any, Dict

WORKSPACE_ROOT = Path(__file__).parent.parent.parent
WORKSPACE_CONFIGS_DIR = WORKSPACE_ROOT / ".cursor" / "workspace-configs"

# All service/library paths for extraPaths
ALL_REPO_PATHS = [
    "${workspaceFolder}/backtest-ui",
    "${workspaceFolder}/batch-audit-ui",
    "${workspaceFolder}/client-reporting-ui",
    "${workspaceFolder}/execution-algo-library",
    "${workspaceFolder}/execution-services",
    "${workspaceFolder}/features-calendar-service",
    "${workspaceFolder}/features-delta-one-service",
    "${workspaceFolder}/features-onchain-service",
    "${workspaceFolder}/instruments-service",
    "${workspaceFolder}/features-volatility-service",
    "${workspaceFolder}/live-health-monitor-ui",
    "${workspaceFolder}/logs-dashboard-ui",
    "${workspaceFolder}/market-data-processing-service",
    "${workspaceFolder}/market-tick-data-handler",
    "${workspaceFolder}/ml-deployment-ui",
    "${workspaceFolder}/ml-inference-service",
    "${workspaceFolder}/ml-training-service",
    "${workspaceFolder}/pnl-attribution-service",
    "${workspaceFolder}/position-balance-monitor-service",
    "${workspaceFolder}/risk-and-exposure-service",
    "${workspaceFolder}/settlement-ui",
    "${workspaceFolder}/strategy-onboarding-ui",
    "${workspaceFolder}/strategy-service",
    "${workspaceFolder}/trading-analytics-ui",
    "${workspaceFolder}/unified-trading-deployment-v3",
    "${workspaceFolder}/unified-order-interface",
    "${workspaceFolder}/unified-market-interface",
    "${workspaceFolder}/unified-events-interface",
    "${workspaceFolder}/unified-domain-client",
    "${workspaceFolder}/unified-config-interface",
    "${workspaceFolder}/unified-trading-services",
]

# Complete strict settings (in proper order)
STRICT_SETTINGS_ORDERED = {
    # Python interpreter
    "python.defaultInterpreterPath": "/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.venv-workspace/bin/python",
    "python.terminal.activateEnvironment": True,
    "python.envFile": "${workspaceFolder}/.env",
    
    # Pylance type checking
    "cursorpyright.analysis.typeCheckingMode": "strict",
    "cursorpyright.analysis.autoSearchPaths": True,
    "cursorpyright.analysis.autoImportCompletions": True,
    "cursorpyright.analysis.useLibraryCodeForTypes": True,
    "cursorpyright.analysis.indexing": True,
    "cursorpyright.analysis.inlayHints.variableTypes": True,
    "cursorpyright.analysis.inlayHints.functionReturnTypes": True,
    "cursorpyright.analysis.diagnosticSeverityOverrides": {
        "reportUnusedImport": "error",
        "reportUnusedVariable": "error",
        "reportMissingImports": "error",
        "reportUndefinedVariable": "error",
        "reportGeneralTypeIssues": "warning",
        "reportOptionalMemberAccess": "warning",
        "reportOptionalSubscript": "warning",
        "reportUnknownArgumentType": "warning",
        "reportUnknownMemberType": "warning",
        "reportAny": "warning",
    },
    "cursorpyright.analysis.extraPaths": ALL_REPO_PATHS,
    
    # Python testing
    "python.testing.pytestEnabled": True,
    "python.testing.unittestEnabled": False,
    "python.testing.pytestArgs": ["tests", "-v"],
    
    # File auto-save
    "files.autoSave": "afterDelay",
    "files.autoSaveDelay": 1000,
    
    # Editor formatting
    "editor.formatOnSave": True,
    "editor.codeActionsOnSave": {"source.organizeImports": "explicit"},
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": True,
        "editor.codeActionsOnSave": {
            "source.fixAll": "explicit",
            "source.organizeImports": "explicit",
        },
    },
    
    # Ruff linter
    "ruff.enable": True,
    "ruff.lint.enable": True,
    "ruff.format.args": [],
    "ruff.lint.args": ["--select=E,F,W,I", "--line-length=120"],
    "ruff.showNotifications": "onError",
    "ruff.organizeImports": True,
    "ruff.fixAll": True,
    "ruff.path": [
        "/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.venv-workspace/bin/ruff"
    ],
    
    # File exclusions
    "files.exclude": {
        "**/__pycache__": True,
        "**/*.pyc": True,
        "**/.pytest_cache": True,
        "**/.ruff_cache": True,
        "**/.venv": True,
        "**/.pixi": True,
        "**/.venv.backup": True,
        "**/uv.lock": False,
    },
    "files.watcherExclude": {
        "**/.git/objects/**": True,
        "**/.git/subtree-cache/**": True,
        "**/node_modules/**": True,
        "**/.hg/store/**": True,
        "**/.pixi/**": True,
        "**/.venv/**": True,
        "**/.venv.backup/**": True,
    },
    "search.exclude": {
        "**/__pycache__": True,
        "**/.pytest_cache": True,
        "**/.ruff_cache": True,
        "**/.venv": True,
        "**/uv.lock": False,
    },
    
    # Editor preferences
    "editor.rulers": [100],
    "editor.tabSize": 4,
    "editor.insertSpaces": True,
    "files.trimTrailingWhitespace": True,
    "files.insertFinalNewline": True,
    "files.trimFinalNewlines": True,
}


def update_workspace_file(workspace_file: Path) -> None:
    """Update a single workspace file with complete aligned settings."""
    print(f"Updating {workspace_file.name}...")

    with open(workspace_file) as f:
        workspace_config = json.load(f)

    # Ensure settings section exists
    if "settings" not in workspace_config:
        workspace_config["settings"] = {}

    # Replace settings with ordered strict settings
    workspace_config["settings"] = STRICT_SETTINGS_ORDERED.copy()

    # Write back with proper formatting
    with open(workspace_file, "w") as f:
        json.dump(workspace_config, f, indent=2)
        f.write("\n")  # Add final newline

    print(f"✅ Updated {workspace_file.name}")


def verify_workspace_file(workspace_file: Path) -> Dict[str, bool]:
    """Verify a workspace file has all required settings."""
    with open(workspace_file) as f:
        workspace_config = json.load(f)

    settings = workspace_config.get("settings", {})
    
    checks = {
        "has_extraPaths": "cursorpyright.analysis.extraPaths" in settings,
        "has_envFile": "python.envFile" in settings,
        "has_reportAny": (
            "cursorpyright.analysis.diagnosticSeverityOverrides" in settings
            and "reportAny" in settings["cursorpyright.analysis.diagnosticSeverityOverrides"]
        ),
        "has_ruff_path": "ruff.path" in settings,
        "extraPaths_count": len(settings.get("cursorpyright.analysis.extraPaths", [])),
    }
    
    return checks


def main() -> None:
    """Update all workspace configuration files and verify."""
    print("🔧 Fixing workspace configuration alignment issues...\n")

    # Get all workspace files
    workspace_files = list(WORKSPACE_CONFIGS_DIR.glob("workspace-*.code-workspace"))
    root_workspace = WORKSPACE_ROOT / "unified-trading-system-repos.code-workspace"
    
    if root_workspace.exists():
        workspace_files.append(root_workspace)

    if not workspace_files:
        print("❌ No workspace files found")
        return

    print(f"Found {len(workspace_files)} workspace files\n")

    # Update all files
    for workspace_file in sorted(workspace_files):
        update_workspace_file(workspace_file)

    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60 + "\n")

    # Verify all files
    all_good = True
    for workspace_file in sorted(workspace_files):
        checks = verify_workspace_file(workspace_file)
        status = "✅" if all(checks.values()) else "⚠️"
        print(f"{status} {workspace_file.name}")
        
        if not all(checks.values()):
            all_good = False
            for check, result in checks.items():
                if not result:
                    print(f"   ❌ {check}: {result}")
        else:
            print(f"   ✅ extraPaths: {checks['extraPaths_count']} repos")

    print("\n" + "="*60)
    if all_good:
        print("✅ All workspace files aligned successfully!")
    else:
        print("⚠️ Some issues remain - check output above")
    print("="*60)

    print("\n📋 Changes applied:")
    print("  ✅ Added cursorpyright.analysis.extraPaths (31 repos)")
    print("  ✅ Added python.envFile for .env loading")
    print("  ✅ Moved diagnosticSeverityOverrides to proper location")
    print("  ✅ Ensured all strict linting settings present")
    print("  ✅ Proper settings order for readability")


if __name__ == "__main__":
    main()
