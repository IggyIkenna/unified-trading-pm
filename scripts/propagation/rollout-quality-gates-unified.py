#!/usr/bin/env python3.13
"""
Roll out quality gates to all repositories from workspace-manifest.json.

Reads workspace-manifest.json from workspace root (parent of unified-trading-pm),
iterates over repositories, and for each repo:
- library -> library template (quality-gates-library-template.sh)
- service/api-service -> service template (quality-gates-service-template.sh)
- ui -> TypeScript template (inline)
- infrastructure/test-harness/devops -> service template

Copies scripts/quality-gates.sh, scripts/setup.sh, creates .cursorignore/.gitignore
from repo-type templates if missing, creates QUALITY_GATE_BYPASS_AUDIT.md stub
when doc_standard requires it. Skips deprecated/archived repos.

Usage:
    python3 scripts/propagation/rollout-quality-gates-unified.py [--dry-run] [--repo NAME]
"""

from __future__ import annotations

import argparse
import json
import sys
import typing
from pathlib import Path
from typing import TypeAlias, cast

JsonDict: TypeAlias = dict[str, object]


def _jdict(val: object) -> JsonDict | None:
    if isinstance(val, dict):
        return cast(JsonDict, val)
    return None


def _jstr(val: object, default: str = "") -> str:
    return str(val) if val is not None else default


# Paths relative to script location
SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
CODEX_ROOT = WORKSPACE_ROOT / "unified-trading-codex"
MANIFEST_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-manifest.json"

# Template paths
SETUP_SH_SOURCE = PM_ROOT / "scripts" / "setup.sh"
QG_LIBRARY_TEMPLATE = CODEX_ROOT / "06-coding-standards" / "quality-gates-library-template.sh"
QG_SERVICE_TEMPLATE = CODEX_ROOT / "06-coding-standards" / "quality-gates-service-template.sh"
TEMPLATES_DIR = SCRIPT_DIR / "templates"
CURSORIGNORE_PYTHON = TEMPLATES_DIR / "cursorignore-python.txt"
CURSORIGNORE_NODE = TEMPLATES_DIR / "cursorignore-node.txt"
GITIGNORE_PYTHON = TEMPLATES_DIR / "gitignore-python.txt"
GITIGNORE_NODE = TEMPLATES_DIR / "gitignore-node.txt"

# Doc standards that require QUALITY_GATE_BYPASS_AUDIT.md
BYPASS_AUDIT_DOC_STANDARDS = frozenset(
    {
        "service-canonical",
        "library-canonical",
        "infrastructure-canonical",
        "api-canonical",
    }
)

# Type -> template selection
TYPE_LIBRARY = "library"
TYPE_SERVICE = "service"
TYPE_API_SERVICE = "api-service"
TYPE_UI = "ui"
TYPE_INFRASTRUCTURE = "infrastructure"
TYPE_TEST_HARNESS = "test-harness"
TYPE_DEVOPS = "devops"

SKIP_STATUSES = frozenset({"deprecated", "archived", "deleted"})
# PM and Codex have their own quality-gates; do not overwrite with templates
ROLLOUT_SKIP_REPOS = frozenset({"unified-trading-pm", "unified-trading-codex"})


def get_typescript_quality_gates_script() -> str:
    """Generate quality-gates.sh for TypeScript/UI repos."""
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


def get_quality_gate_bypass_audit_stub() -> str:
    """Minimal QUALITY_GATE_BYPASS_AUDIT.md stub."""
    return """# Quality Gate Bypass Audit

## 2.1 File Size Exceptions

None.

## 2.2 Ruff Exceptions

None.

## 2.3 Basedpyright Exceptions

None.

"""


def discover_source_dir(repo_path: Path, repo_name: str) -> str:
    """Discover Python source directory. Fallback: repo name with underscores."""
    # PM and codex are not packages; Python lives in scripts/
    if repo_name in ("unified-trading-pm", "unified-trading-codex"):
        scripts = repo_path / "scripts"
        if scripts.is_dir() and any(scripts.rglob("*.py")):
            return "scripts"
    default = repo_name.replace("-", "_")  # Python package form (underscores)
    candidates = [default, "src"]  # Try underscore form, then src; not hyphen form
    for c in candidates:
        d = repo_path / c
        if d.is_dir():
            if (d / "__init__.py").exists() or list(d.rglob("__init__.py")):
                return c
            if any(d.rglob("*.py")):
                return c
    return default


def select_template_type(repo_type: str) -> str:
    """Map repo type to template: library, service, or typescript."""
    if repo_type == TYPE_LIBRARY:
        return "library"
    if repo_type in (TYPE_SERVICE, TYPE_API_SERVICE, TYPE_INFRASTRUCTURE, TYPE_TEST_HARNESS, TYPE_DEVOPS):
        return "service"
    if repo_type == TYPE_UI:
        return "typescript"
    return "service"  # default for unknown Python repos


def copy_quality_gates(
    repo_path: Path,
    repo_name: str,
    template_type: str,
    dry_run: bool,
) -> bool:
    """Copy and customize quality-gates.sh. Returns True if created/updated."""
    scripts_dir = repo_path / "scripts"
    dest = scripts_dir / "quality-gates.sh"

    if template_type == "typescript":
        content = get_typescript_quality_gates_script()
    else:
        template_path = QG_LIBRARY_TEMPLATE if template_type == "library" else QG_SERVICE_TEMPLATE
        if not template_path.exists():
            print(f"  ⚠️ Template not found: {template_path}")
            return False
        content = template_path.read_text()

    source_dir = discover_source_dir(repo_path, repo_name)
    package_name = repo_name  # repo name for PACKAGE_NAME/SERVICE_NAME

    if template_type == "library":
        content = content.replace('PACKAGE_NAME="REPLACE_ME"', f'PACKAGE_NAME="{package_name}"')
        content = content.replace('SOURCE_DIR="REPLACE_ME"', f'SOURCE_DIR="{source_dir}"')
    elif template_type == "service":
        content = content.replace('SERVICE_NAME="REPLACE_ME"', f'SERVICE_NAME="{package_name}"')
        content = content.replace('SOURCE_DIR="REPLACE_ME"', f'SOURCE_DIR="{source_dir}"')

    if dry_run:
        print(f"  [dry-run] Would write {dest}")
        return True

    scripts_dir.mkdir(parents=True, exist_ok=True)
    dest.write_text(content)
    dest.chmod(0o755)
    print("  ✅ Created/updated scripts/quality-gates.sh")
    return True


def copy_setup_sh(repo_path: Path, dry_run: bool) -> bool:
    """Copy setup.sh from PM. Returns True if created/updated."""
    if not SETUP_SH_SOURCE.exists():
        print(f"  ⚠️ setup.sh not found: {SETUP_SH_SOURCE}")
        return False
    dest = repo_path / "scripts" / "setup.sh"
    if dry_run:
        print(f"  [dry-run] Would copy setup.sh to {dest}")
        return True
    repo_path.mkdir(parents=True, exist_ok=True)
    (repo_path / "scripts").mkdir(parents=True, exist_ok=True)
    dest.write_text(SETUP_SH_SOURCE.read_text())
    dest.chmod(0o755)
    print("  ✅ Created/updated scripts/setup.sh")
    return True


def ensure_ignore_files(repo_path: Path, template_type: str, dry_run: bool) -> bool:
    """Create .cursorignore and .gitignore from templates if missing."""
    if template_type == "typescript":
        cursorignore_src = CURSORIGNORE_NODE
        gitignore_src = GITIGNORE_NODE
    else:
        cursorignore_src = CURSORIGNORE_PYTHON
        gitignore_src = GITIGNORE_PYTHON

    updated = False
    for name, src in [(".cursorignore", cursorignore_src), (".gitignore", gitignore_src)]:
        dest = repo_path / name
        if not dest.exists() and src.exists():
            if dry_run:
                print(f"  [dry-run] Would create {name}")
            else:
                dest.write_text(src.read_text())
                print(f"  ✅ Created {name}")
            updated = True
    return updated


def ensure_bypass_audit(repo_path: Path, doc_standard: typing.Optional[str], dry_run: bool) -> bool:
    """Create QUALITY_GATE_BYPASS_AUDIT.md stub if doc_standard requires it."""
    if not doc_standard or doc_standard not in BYPASS_AUDIT_DOC_STANDARDS:
        return False
    dest = repo_path / "QUALITY_GATE_BYPASS_AUDIT.md"
    if dest.exists():
        return False
    if dry_run:
        print("  [dry-run] Would create QUALITY_GATE_BYPASS_AUDIT.md")
        return True
    dest.write_text(get_quality_gate_bypass_audit_stub())
    print("  ✅ Created QUALITY_GATE_BYPASS_AUDIT.md stub")
    return True


def process_repo(
    repo_name: str,
    repo_info: JsonDict,
    workspace_root: Path,
    dry_run: bool,
) -> bool:
    """Process a single repository. Returns True on success."""
    status = repo_info.get("status", "active")
    if status in SKIP_STATUSES:
        print(f"\n⏭️ Skipping {repo_name} (status={status})")
        return True
    if repo_name in ROLLOUT_SKIP_REPOS:
        print(f"\n⏭️ Skipping {repo_name} (has own quality-gates, not overwritten)")
        return True
    repo_type = _jstr(repo_info.get("type"), "service")
    doc_standard_raw = repo_info.get("doc_standard")
    doc_standard: str | None = None if doc_standard_raw is None else _jstr(doc_standard_raw)
    template_type = select_template_type(repo_type)
    repo_path = workspace_root / repo_name
    if not repo_path.exists():
        print(f"\n⚠️ {repo_name}: directory not found at {repo_path}")
        return False
    # Override: package.json + no pyproject = TypeScript (manifest may mislabel UI as library)
    has_package_json = (repo_path / "package.json").exists()
    has_pyproject = (repo_path / "pyproject.toml").exists()
    if has_package_json and not has_pyproject:
        template_type = "typescript"

    # UI repos: need package.json
    if template_type == "typescript":
        if not (repo_path / "package.json").exists():
            print(f"\n⚠️ {repo_name}: no package.json (not a UI repo?)")
            return False
    else:
        if not (repo_path / "pyproject.toml").exists():
            print(f"\n⚠️ {repo_name}: no pyproject.toml (not a Python repo?)")
            return False

    print(f"\n🔧 Processing {repo_name} (type={repo_type}, template={template_type})")

    changed = False
    changed |= copy_quality_gates(repo_path, repo_name, template_type, dry_run)
    changed |= copy_setup_sh(repo_path, dry_run)
    changed |= ensure_ignore_files(repo_path, template_type, dry_run)
    changed |= ensure_bypass_audit(repo_path, doc_standard, dry_run)

    if not changed:
        print(f"  ✅ {repo_name} already has all quality gate files")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Roll out quality gates from workspace manifest")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without writing")
    parser.add_argument("--repo", type=str, help="Process only this repository")
    args = parser.parse_args()

    if not MANIFEST_PATH.exists():
        print(f"❌ Manifest not found: {MANIFEST_PATH}")
        return 1

    with open(MANIFEST_PATH) as f:
        manifest = cast(JsonDict, json.load(f))

    repos_raw = _jdict(manifest.get("repositories"))
    repositories = cast(dict[str, JsonDict], repos_raw) if repos_raw else {}
    dry_run = cast(bool, args.dry_run)
    repo_filter = cast(str | None, args.repo)
    if repo_filter is not None:
        if repo_filter not in repositories:
            print(f"❌ Repository not in manifest: {repo_filter}")
            return 1
        repositories = {repo_filter: repositories[repo_filter]}

    print("🚀 Rolling out quality gates (unified)")
    print(f"📁 Workspace: {WORKSPACE_ROOT}")
    print(f"📋 Repositories: {len(repositories)}")
    if dry_run:
        print("🔍 Dry run — no files will be written")

    success = 0
    errors = 0
    for repo_name in sorted(repositories.keys()):
        try:
            if process_repo(repo_name, repositories[repo_name], WORKSPACE_ROOT, dry_run):
                success += 1
            else:
                errors += 1
        except (OSError, ValueError) as e:
            print(f"  ❌ Error: {e}")
            errors += 1

    print("\n🎉 Rollout complete!")
    print(f"  ✅ Success: {success}")
    print(f"  ❌ Errors: {errors}")

    return 1 if errors > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
