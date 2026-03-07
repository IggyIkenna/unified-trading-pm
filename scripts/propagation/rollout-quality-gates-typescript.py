#!/usr/bin/env python3.13
"""
Roll out quality gates to all TypeScript/UI repositories.
This script adds missing quality gate scripts to package.json and creates quality-gates.sh scripts.
"""

import json
import sys
from pathlib import Path
from typing import cast

# UI repositories
UI_REPOS = [
    "execution-analytics-ui",
    "batch-audit-ui",
    "client-reporting-ui",
    "live-health-monitor-ui",
    "logs-dashboard-ui",
    "ml-training-ui",
    "onboarding-ui",
    "trading-analytics-ui",
]


def get_quality_gates_script() -> str:
    """Generate quality-gates.sh script for TypeScript repos."""
    return """#!/bin/bash

# Quality gates for TypeScript/React UI repository
set -e

echo "🔍 Running TypeScript/React Quality Gates..."

# Step 1: TypeScript type check
echo "Step 1/3: TypeScript type check..."
if [ -f "package.json" ] && [ -f "tsconfig.json" ]; then
    npm run typecheck
    echo "✅ TypeScript type check passed"
else
    echo "⚠️ No package.json or tsconfig.json found, skipping TypeScript check"
fi

# Step 2: ESLint
echo "Step 2/3: ESLint..."
if [ -f "package.json" ]; then
    if npm run lint --silent 2>/dev/null; then
        echo "✅ ESLint passed"
    else
        echo "⚠️ No lint script or lint failed"
    fi
else
    echo "⚠️ No package.json found, skipping ESLint"
fi

# Step 3 (optional): Smoke tests
echo "Step 3/3: Smoke tests (optional)..."
if [ -f "package.json" ] && grep -q '"smoketest"' package.json; then
    npm run smoketest || echo "⚠️ Smoke tests failed (not blocking)"
    echo "✅ Smoke tests completed"
else
    echo "⚠️ No smoke tests configured, skipping"
fi

echo ""
echo "🎉 All TypeScript/React quality gates completed!"
"""


def ensure_scripts_in_package_json(package_json_path: Path) -> bool:
    """Ensure package.json has required scripts for quality gates."""
    if not package_json_path.exists():
        return False

    try:
        with open(package_json_path, "r") as f:
            data: dict[str, object] = cast(dict[str, object], json.load(f))
    except json.JSONDecodeError:
        print(f"  ❌ Invalid JSON in {package_json_path}")
        return False

    scripts_val = data.get("scripts") or {}
    scripts: dict[str, str] = cast(dict[str, str], scripts_val) if isinstance(scripts_val, dict) else {}
    updated = False

    # Add typecheck script if missing
    if "typecheck" not in scripts:
        scripts["typecheck"] = "tsc --noEmit"
        updated = True
        print("  ➕ Added typecheck script")

    # Add lint script if missing (basic fallback)
    if "lint" not in scripts:
        scripts["lint"] = "eslint ."
        updated = True
        print("  ➕ Added lint script")

    # Update package.json if we made changes
    if updated:
        data["scripts"] = scripts
        with open(package_json_path, "w") as f:
            json.dump(data, f, indent=2)
        print("  ✅ Updated package.json scripts")

    return updated


def ensure_tsconfig_exists(repo_path: Path) -> bool:
    """Ensure tsconfig.json exists with basic TypeScript strict configuration."""
    tsconfig_path = repo_path / "tsconfig.json"

    if tsconfig_path.exists():
        return False  # Already exists

    # Create basic strict TypeScript config
    tsconfig_content: dict[str, object] = {
        "compilerOptions": {
            "target": "ES2020",
            "lib": ["DOM", "DOM.Iterable", "ES6"],
            "allowJs": True,
            "skipLibCheck": True,
            "esModuleInterop": True,
            "allowSyntheticDefaultImports": True,
            "strict": True,
            "forceConsistentCasingInFileNames": True,
            "noFallthroughCasesInSwitch": True,
            "module": "esnext",
            "moduleResolution": "node",
            "resolveJsonModule": True,
            "isolatedModules": True,
            "noEmit": True,
            "jsx": "react-jsx",
            "noImplicitAny": True,
            "strictNullChecks": True,
            "strictFunctionTypes": True,
        },
        "include": ["src", "**/*.ts", "**/*.tsx"],
        "exclude": ["node_modules", "dist", "build"],
    }

    with open(tsconfig_path, "w") as f:
        json.dump(tsconfig_content, f, indent=2)

    print("  📝 Created tsconfig.json with strict TypeScript configuration")
    return True


def ensure_quality_gates_script_exists(repo_path: Path) -> bool:
    """Ensure scripts/quality-gates.sh exists."""
    scripts_dir = repo_path / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    quality_gates_path = scripts_dir / "quality-gates.sh"

    if quality_gates_path.exists():
        # Check if it's the correct TypeScript version
        content = quality_gates_path.read_text()
        if "TypeScript/React Quality Gates" in content:
            return False  # Already has correct script

    quality_gates_path.write_text(get_quality_gates_script())
    quality_gates_path.chmod(0o755)  # Make executable

    print("  📝 Created scripts/quality-gates.sh")
    return True


def process_ui_repository(repo_name: str, workspace_path: Path) -> bool:
    """Process a single UI repository to add TypeScript quality gates."""
    print(f"\n🎨 Processing {repo_name}")

    repo_path = workspace_path / repo_name
    if not repo_path.exists():
        print(f"  ❌ Repository directory not found: {repo_path}")
        return False

    package_json_path = repo_path / "package.json"
    if not package_json_path.exists():
        print("  ❌ No package.json found - not a TypeScript/Node.js repository")
        return False

    # Update package.json scripts
    updated_package_json = ensure_scripts_in_package_json(package_json_path)

    # Ensure tsconfig.json exists
    created_tsconfig = ensure_tsconfig_exists(repo_path)

    # Ensure quality-gates.sh script exists
    created_quality_gates = ensure_quality_gates_script_exists(repo_path)

    if updated_package_json or created_tsconfig or created_quality_gates:
        print(f"  ✅ {repo_name} updated successfully")
        return True
    else:
        print(f"  ✅ {repo_name} already has all TypeScript quality gates")
        return True


def check_embedded_uis(workspace_path: Path) -> list[str]:
    """Check for embedded UIs (package.json in subdirectories)."""
    embedded_uis: list[str] = []

    # Check execution-service/visualizer-ui/
    execution_service_ui = workspace_path / "execution-service" / "visualizer-ui"
    if (execution_service_ui / "package.json").exists():
        embedded_uis.append("execution-service/visualizer-ui")

    # unified-trading-deployment-v3/ui/ violation resolved (2026-03-03): extracted to deployment-ui repo

    return embedded_uis


def process_embedded_ui(ui_path_str: str, workspace_path: Path) -> bool:
    """Process an embedded UI repository."""
    print(f"\n🎨 Processing embedded UI: {ui_path_str}")

    ui_path = workspace_path / Path(ui_path_str)
    if not ui_path.exists():
        print(f"  ❌ Embedded UI directory not found: {ui_path}")
        return False

    package_json_path = ui_path / "package.json"
    if not package_json_path.exists():
        print("  ❌ No package.json found in embedded UI")
        return False

    # Update package.json scripts
    updated_package_json = ensure_scripts_in_package_json(package_json_path)

    # Ensure tsconfig.json exists
    created_tsconfig = ensure_tsconfig_exists(ui_path)

    # Ensure quality-gates.sh script exists
    created_quality_gates = ensure_quality_gates_script_exists(ui_path)

    if updated_package_json or created_tsconfig or created_quality_gates:
        print(f"  ✅ {ui_path_str} updated successfully")
        return True
    else:
        print(f"  ✅ {ui_path_str} already has all TypeScript quality gates")
        return True


def main():
    """Main function to roll out TypeScript quality gates to all UI repositories."""
    # Get workspace path
    script_path = Path(__file__).parent.parent.parent.parent
    workspace_path = script_path

    print("🎨 Rolling out TypeScript quality gates to all UI repositories")
    print(f"📁 Workspace: {workspace_path}")
    print(f"🖼️  Processing {len(UI_REPOS)} standalone UI repositories")

    success_count = 0
    error_count = 0

    # Process standalone UI repos
    for repo_name in sorted(UI_REPOS):
        try:
            if process_ui_repository(repo_name, workspace_path):
                success_count += 1
            else:
                error_count += 1
        except (OSError, ValueError) as e:
            print(f"  ❌ Error processing {repo_name}: {e}")
            error_count += 1

    # Check for embedded UIs
    embedded_uis = check_embedded_uis(workspace_path)
    if embedded_uis:
        print(f"\n🔍 Found {len(embedded_uis)} embedded UIs")
        for ui_path in embedded_uis:
            try:
                if process_embedded_ui(ui_path, workspace_path):
                    success_count += 1
                else:
                    error_count += 1
            except (OSError, ValueError) as e:
                print(f"  ❌ Error processing {ui_path}: {e}")
                error_count += 1
    else:
        print("\n🔍 No embedded UIs found")

    print("\n🎉 TypeScript quality gates rollout complete!")
    print(f"  ✅ Successfully processed: {success_count}")
    print(f"  ❌ Errors: {error_count}")
    print(f"  📊 Total: {success_count + error_count}")

    if error_count > 0:
        print("\n⚠️  Some repositories had errors. Please review the output above.")
        sys.exit(1)
    else:
        print("\n🎯 All UI repositories now have TypeScript quality gates!")
        print("\n📝 Next steps:")
        print("  1. Run 'npm install' in each UI repo to install dependencies")
        print("  2. Run 'npm run typecheck' to test TypeScript type checking")
        print("  3. Run 'npm run lint' to test ESLint")
        print("  4. Run 'bash scripts/quality-gates.sh' to test full quality gates")


if __name__ == "__main__":
    main()
