#!/usr/bin/env python3
"""
Fix workspace configuration alignment issues (CORRECTED VERSION).

This script ensures all workspace files have:
1. cursorpyright.analysis.extraPaths (based on ACTUAL folders in each workspace)
2. python.envFile (for .env loading)
3. Proper settings order
4. Auto-fix on save enabled
"""

import json
from pathlib import Path
from typing import Any, Dict, List

WORKSPACE_ROOT = Path(__file__).parent.parent.parent
WORKSPACE_CONFIGS_DIR = WORKSPACE_ROOT / ".cursor" / "workspace-configs"


def get_folder_paths_from_workspace(workspace_config: Dict[str, Any]) -> List[str]:
    """Extract folder paths from workspace config and convert to extraPaths format."""
    folders = workspace_config.get("folders", [])
    extra_paths = []
    
    for folder in folders:
        path = folder.get("path", "")
        if not path:
            continue
            
        # Convert relative path to workspaceFolder format
        # "../../instruments-service" -> "${workspaceFolder}/instruments-service"
        # "../../.cursor" -> skip (not a Python package)
        
        if path.startswith("../../"):
            folder_name = path.replace("../../", "")
            
            # Skip non-Python folders
            if folder_name in [".cursor", "unified-trading-codex", "unified-trading-deployment-v3"]:
                continue
                
            extra_paths.append(f"${{workspaceFolder}}/{folder_name}")
    
    return extra_paths


# Complete strict settings template (will be customized per workspace)
def get_strict_settings_template(extra_paths: List[str]) -> Dict[str, Any]:
    """Get strict settings template with workspace-specific extraPaths."""
    return {
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
        "cursorpyright.analysis.extraPaths": extra_paths,  # Workspace-specific!
        
        # Python testing
        "python.testing.pytestEnabled": True,
        "python.testing.unittestEnabled": False,
        "python.testing.pytestArgs": ["tests", "-v"],
        
        # File auto-save
        "files.autoSave": "afterDelay",
        "files.autoSaveDelay": 1000,
        
        # Editor formatting - AUTO-FIX ON SAVE
        "editor.formatOnSave": True,
        "editor.codeActionsOnSave": {
            "source.fixAll": "explicit",
            "source.organizeImports": "explicit"
        },
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
    """Update a single workspace file with correct workspace-specific settings."""
    print(f"Updating {workspace_file.name}...")

    with open(workspace_file) as f:
        workspace_config = json.load(f)

    # Ensure settings section exists
    if "settings" not in workspace_config:
        workspace_config["settings"] = {}

    # Extract folder paths from THIS workspace
    extra_paths = get_folder_paths_from_workspace(workspace_config)
    print(f"  Found {len(extra_paths)} Python repos in this workspace")

    # Get settings template with workspace-specific extraPaths
    workspace_config["settings"] = get_strict_settings_template(extra_paths)

    # Write back with proper formatting
    with open(workspace_file, "w") as f:
        json.dump(workspace_config, f, indent=2)
        f.write("\n")  # Add final newline

    print(f"✅ Updated {workspace_file.name} with {len(extra_paths)} extraPaths")


def verify_workspace_file(workspace_file: Path) -> Dict[str, Any]:
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
        "has_auto_fix": (
            "editor.codeActionsOnSave" in settings
            and "source.fixAll" in settings["editor.codeActionsOnSave"]
        ),
        "extraPaths_count": len(settings.get("cursorpyright.analysis.extraPaths", [])),
        "folder_count": len(workspace_config.get("folders", [])),
    }
    
    return checks


def main() -> None:
    """Update all workspace configuration files and verify."""
    print("🔧 Fixing workspace configuration alignment (CORRECTED VERSION)...\n")

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
        print()

    print("="*60)
    print("VERIFICATION")
    print("="*60 + "\n")

    # Verify all files
    all_good = True
    for workspace_file in sorted(workspace_files):
        checks = verify_workspace_file(workspace_file)
        status = "✅" if all(v for k, v in checks.items() if k != "folder_count" and k != "extraPaths_count") else "⚠️"
        print(f"{status} {workspace_file.name}")
        print(f"   📁 Folders: {checks['folder_count']}")
        print(f"   🔗 extraPaths: {checks['extraPaths_count']}")
        print(f"   🔧 Auto-fix on save: {'✅' if checks['has_auto_fix'] else '❌'}")
        
        if not all(v for k, v in checks.items() if k not in ["folder_count", "extraPaths_count"]):
            all_good = False
            for check, result in checks.items():
                if check not in ["folder_count", "extraPaths_count"] and not result:
                    print(f"   ❌ {check}: {result}")
        print()

    print("="*60)
    if all_good:
        print("✅ All workspace files aligned successfully!")
    else:
        print("⚠️ Some issues remain - check output above")
    print("="*60)

    print("\n📋 Changes applied:")
    print("  ✅ Added cursorpyright.analysis.extraPaths (workspace-specific)")
    print("  ✅ Added python.envFile for .env loading")
    print("  ✅ Moved diagnosticSeverityOverrides to proper location")
    print("  ✅ Enabled auto-fix on save (source.fixAll + organizeImports)")
    print("  ✅ Ensured all strict linting settings present")
    print("  ✅ Proper settings order for readability")


if __name__ == "__main__":
    main()
