#!/usr/bin/env python3.13
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
Add library pre-check step to service cloudbuild.yaml files.

For each repo with both cloudbuild.yaml and pyproject.toml:
- Inserts a step BEFORE configure-docker that runs:
  uv pip download <pkg><constraint> --index-url <artifact-registry>
  for each internal dep (unified-*, *-library, *-interface).
- Fails the build if any required version is missing from Artifact Registry.

Usage:
    python3 scripts/propagation/add-cloudbuild-prechecks.py [--dry-run] [--repo NAME]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent

# Artifact Registry Python index (same as cloudbuild-service-template)
ARTIFACT_REGISTRY_INDEX = "https://asia-northeast1-python.pkg.dev/$PROJECT_ID/unified-libraries/simple/"

# Internal dep pattern: unified-*, *-library, *-interface (captures full spec with constraint)
INTERNAL_DEP_PATTERN = re.compile(r'^\s*"((?:unified-[^"]+|[^"]+-library|[^"]+-interface)[^"]*)"\s*,?\s*$')

LIBRARY_PRECHECK_STEP = f'''  # Library pre-check: verify internal deps exist in Artifact Registry
  - name: "ghcr.io/astral-sh/uv:python3.13"
    id: "library-precheck"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        set -e
        INDEX="{ARTIFACT_REGISTRY_INDEX}"
        for spec in $(grep -oE '"(unified-[^"]+|[^"]+-library|[^"]+-interface)[^"]*"' pyproject.toml | sed 's/"//g'); do
          echo "Pre-check: $spec"
          uv pip download "$spec" --index-url "$INDEX" || exit 1
        done
        echo "All internal deps available."
    waitFor: ["-"]

'''


def get_internal_deps(pyproject_path: Path) -> list[str]:
    """Extract internal dep specs from pyproject.toml."""
    text = pyproject_path.read_text()
    deps: list[str] = []
    in_deps = False
    for line in text.splitlines():
        if "dependencies" in line and "=" in line and "[" in line:
            in_deps = True
            continue
        if in_deps:
            if line.strip().startswith("]"):
                break
            m = INTERNAL_DEP_PATTERN.match(line)
            if m:
                deps.append(m.group(1).strip())
    return deps


def has_library_precheck(cloudbuild_content: str) -> bool:
    """Check if cloudbuild already has library-precheck step."""
    return 'id: "library-precheck"' in cloudbuild_content


def insert_precheck_step(cloudbuild_content: str) -> str:
    """Insert library-precheck step before first step."""
    if has_library_precheck(cloudbuild_content):
        return cloudbuild_content
    idx = cloudbuild_content.find("steps:")
    if idx == -1:
        return cloudbuild_content
    steps_end = cloudbuild_content.find("\n", idx) + 1
    first_step = cloudbuild_content.find("  - name:", steps_end)
    if first_step == -1:
        return cloudbuild_content
    return cloudbuild_content[:first_step] + LIBRARY_PRECHECK_STEP + cloudbuild_content[first_step:]


class _ParsedArgs(argparse.Namespace):
    dry_run: bool
    repo: str | None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", dest="dry_run", help="Print changes, do not write")
    parser.add_argument("--repo", type=str, help="Limit to single repo")
    args = parser.parse_args(namespace=_ParsedArgs())

    modified = 0
    for repo_dir in sorted(WORKSPACE_ROOT.iterdir()):
        if not repo_dir.is_dir():
            continue
        name = repo_dir.name
        if args.repo and name != args.repo:
            continue
        cloudbuild = repo_dir / "cloudbuild.yaml"
        pyproject = repo_dir / "pyproject.toml"
        if not cloudbuild.exists() or not pyproject.exists():
            continue
        deps = get_internal_deps(pyproject)
        if not deps:
            continue
        content = cloudbuild.read_text()
        if has_library_precheck(content):
            continue
        new_content = insert_precheck_step(content)
        if new_content == content:
            continue
        if args.dry_run:
            print(f"[dry-run] Would patch {name}/cloudbuild.yaml")
            modified += 1
        else:
            cloudbuild.write_text(new_content)
            print(f"Patched {name}/cloudbuild.yaml")
            modified += 1
    print(f"Done. Modified {modified} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
