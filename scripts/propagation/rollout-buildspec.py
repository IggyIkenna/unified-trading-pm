#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""
rollout-buildspec.py

Propagates CodeBuild buildspec configs from PM templates to all repos.
Reads workspace-manifest.json, determines repo type, picks template, substitutes
{{SERVICE_NAME}} and {{REGISTRY_REPO}}, writes buildspec.aws.yaml to repo root.

Template mapping:
  - service, batch-service, api-service -> buildspec-service-template.yaml
  - ui -> buildspec-ui-template.yaml
  - library, infrastructure, test-harness -> skip

Skips: unified-trading-pm, unified-trading-codex, unified-trading-library,
       system-integration-tests.

Usage:
    python rollout-buildspec.py [--dry-run] [--repo NAME]

Options:
    --dry-run    Print what would be written without writing files.
    --repo NAME  Process a single repo only.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"
CONFIGS_DIR = PM_ROOT / "configs"

SKIP_REPOS = {
    "unified-trading-pm",
    "unified-trading-codex",
    "unified-trading-library",
    "system-integration-tests",
}

REGISTRY_REPO = "unified-trading-system"

TYPE_TO_TEMPLATE: dict[str, str] = {
    "service": "buildspec-service-template.yaml",
    "batch-service": "buildspec-service-template.yaml",
    "api-service": "buildspec-service-template.yaml",
    "ui": "buildspec-ui-template.yaml",
    "infrastructure": "buildspec-infra-template.yaml",
}

INFRA_REPO_CONFIG: dict[str, dict[str, str]] = {
    "ibkr-gateway-infra": {
        "pkg_name": "ibkr_gateway_client",
        "terraform_dir": "ibkr-gateway",
        "terraform_image": "ibkr-gateway-terraform",
    },
}


def load_manifest() -> dict:
    with MANIFEST_PATH.open() as f:
        return json.load(f)


def get_repos(manifest: dict) -> dict:
    return manifest.get("repositories", manifest.get("repos", {}))  # noqa: qg-empty-fallback


def validate_yaml(content: str, path_label: str) -> bool:
    """Basic YAML validation: load and check required keys."""
    if yaml is None:
        print(f"  WARNING: {path_label} - yaml module not available, skipping validation", file=sys.stderr)
        return True

    try:
        data = yaml.safe_load(content)
        if data is None:
            print(f"  WARNING: {path_label} parsed as empty/None", file=sys.stderr)
            return True
        if "version" not in data:
            print(f"  YAML VALIDATION: {path_label} missing 'version' key", file=sys.stderr)
            return False
        if "phases" not in data:
            print(f"  YAML VALIDATION: {path_label} missing 'phases' key", file=sys.stderr)
            return False
        return True
    except (yaml.YAMLError, TypeError) as exc:
        print(f"  YAML VALIDATION FAILED ({path_label}): {exc}", file=sys.stderr)
        return False


def generate_buildspec(repo_name: str, repo_info: dict) -> str | None:
    repo_type = repo_info.get("type") or ""
    template_name = TYPE_TO_TEMPLATE.get(repo_type)
    if not template_name:
        return None
    if repo_type == "infrastructure" and repo_name not in INFRA_REPO_CONFIG:
        return None
    template_path = CONFIGS_DIR / template_name
    if not template_path.exists():
        print(f"  Template not found: {template_path}", file=sys.stderr)
        return None
    content = template_path.read_text()
    if repo_type == "infrastructure":
        cfg = INFRA_REPO_CONFIG[repo_name]
        content = content.replace("{{PKG_NAME}}", cfg["pkg_name"])
        content = content.replace("{{TERRAFORM_DIR}}", cfg["terraform_dir"])
        content = content.replace('PKG_NAME: "{{PKG_NAME}}"', f'PKG_NAME: "{cfg["pkg_name"]}"')
        content = content.replace('TERRAFORM_DIR: "{{TERRAFORM_DIR}}"', f'TERRAFORM_DIR: "{cfg["terraform_dir"]}"')
    else:
        content = content.replace("{{SERVICE_NAME}}", repo_name)
        content = content.replace("{{REGISTRY_REPO}}", REGISTRY_REPO)
    return content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print changes, do not write")
    parser.add_argument("--repo", type=str, default="", help="Limit to single repo")
    args = parser.parse_args()

    manifest = load_manifest()
    repos = get_repos(manifest)
    if args.repo:
        if args.repo not in repos:
            print(f"Repo '{args.repo}' not in manifest", file=sys.stderr)
            return 1
        repos = {args.repo: repos[args.repo]}

    modified = 0
    for repo_name, repo_info in sorted(repos.items()):
        if repo_name in SKIP_REPOS:
            continue
        if not isinstance(repo_info, dict):
            continue
        content = generate_buildspec(repo_name, repo_info)
        if content is None:
            continue
        if not validate_yaml(content, repo_name):
            continue
        out_path = WORKSPACE_ROOT / repo_name / "buildspec.aws.yaml"
        if args.dry_run:
            print(f"[dry-run] Would write {out_path} ({len(content)} bytes)")
            modified += 1
        else:
            out_path.write_text(content)
            print(f"Wrote {out_path}")
            modified += 1

    print(f"Done. {'Would modify' if args.dry_run else 'Modified'} {modified} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
