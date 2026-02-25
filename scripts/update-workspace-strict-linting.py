#!/usr/bin/env python3
"""
Update all workspace configuration files with strict linting settings.

This script ensures:
1. Strict type checking with reportAny warnings
2. Ruff version consistency (uses workspace venv ruff)
3. All diagnostic severity overrides for unused imports/variables
"""

import json
from pathlib import Path
from typing import Any, Dict

WORKSPACE_ROOT = Path(__file__).parent.parent.parent
WORKSPACE_CONFIGS_DIR = WORKSPACE_ROOT / ".cursor" / "workspace-configs"

# Strict settings to apply to all workspace files
STRICT_SETTINGS = {
    "python.defaultInterpreterPath": "/Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/.venv-workspace/bin/python",
    "python.terminal.activateEnvironment": True,
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
    "python.testing.pytestEnabled": True,
    "python.testing.unittestEnabled": False,
    "python.testing.pytestArgs": ["tests", "-v"],
    "files.autoSave": "afterDelay",
    "files.autoSaveDelay": 1000,
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
    "editor.rulers": [100],
    "editor.tabSize": 4,
    "editor.insertSpaces": True,
    "files.trimTrailingWhitespace": True,
    "files.insertFinalNewline": True,
    "files.trimFinalNewlines": True,
}


def update_workspace_file(workspace_file: Path) -> None:
    """Update a single workspace file with strict settings."""
    print(f"Updating {workspace_file.name}...")

    with open(workspace_file) as f:
        workspace_config = json.load(f)

    # Update settings, preserving any workspace-specific settings
    if "settings" not in workspace_config:
        workspace_config["settings"] = {}

    # Merge strict settings (strict settings take precedence)
    for key, value in STRICT_SETTINGS.items():
        workspace_config["settings"][key] = value

    # Write back with proper formatting
    with open(workspace_file, "w") as f:
        json.dump(workspace_config, f, indent=2)
        f.write("\n")  # Add final newline

    print(f"✅ Updated {workspace_file.name}")


def main() -> None:
    """Update all workspace configuration files."""
    print("🔧 Updating workspace configurations with strict linting...\n")

    # Update all workspace-*.code-workspace files
    workspace_files = list(WORKSPACE_CONFIGS_DIR.glob("workspace-*.code-workspace"))

    if not workspace_files:
        print("❌ No workspace files found in .cursor/workspace-configs/")
        return

    for workspace_file in sorted(workspace_files):
        update_workspace_file(workspace_file)

    # Also update the root workspace file
    root_workspace = WORKSPACE_ROOT / "unified-trading-system-repos.code-workspace"
    if root_workspace.exists():
        print(f"\nUpdating root workspace file...")
        update_workspace_file(root_workspace)

    print(f"\n✅ Successfully updated {len(workspace_files) + 1} workspace files")
    print("\n📋 Changes applied:")
    print("  - Strict type checking with reportAny warnings")
    print("  - Ruff 0.15.0 from workspace venv")
    print("  - Unused imports/variables as errors (RED)")
    print("  - Type issues as warnings (YELLOW)")
    print("  - Format on save with organize imports")


if __name__ == "__main__":
    main()
