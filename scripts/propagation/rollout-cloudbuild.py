#!/usr/bin/env python3
"""
rollout-cloudbuild.py

Propagates Cloud Build configs from PM templates to all repos.
Reads workspace-manifest.json, determines repo type, picks template, substitutes
{{SERVICE_NAME}} and {{REGISTRY_REPO}}, writes cloudbuild.yaml to repo root.

Template mapping:
  - service, batch-service -> cloudbuild-service-template.yaml
  - api-service -> cloudbuild-api-template.yaml
  - ui -> cloudbuild-ui-template.yaml
  - library, infrastructure, test-harness -> skip (no Docker cloudbuild)

Skips: unified-trading-pm, unified-trading-codex, unified-trading-library.

SSOT: docs/ci-cd-ssot.md §7. Cloud Build and CodeBuild

Adds deploy-via-dispatch comment for repos with deploy_via_dispatch: true.

Usage:
    python rollout-cloudbuild.py [--dry-run] [--repo NAME]

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

LIBRARY_CUSTOM_CLOUDBUILD = {
    "unified-api-contracts",
    "unified-reference-data-interface",
}

SKIP_REPOS = {
    "unified-trading-pm",
    "unified-trading-codex",
    "unified-trading-library",
}

REGISTRY_REPO = "unified-trading-system"
DEPLOY_VIA_DISPATCH_COMMENT = "# deploy-via-dispatch — deployed via central deployment-service, not inline\n"
SUBSTITUTION_CHECKER_PATH = PM_ROOT / "scripts" / "quality_gates" / "check_cloudbuild_substitutions.py"

# type -> template filename (without path)
TYPE_TO_TEMPLATE: dict[str, str] = {
    "service": "cloudbuild-service-template.yaml",
    "batch-service": "cloudbuild-service-template.yaml",
    "api-service": "cloudbuild-api-template.yaml",
    "ui": "cloudbuild-ui-template.yaml",
    "library": "cloudbuild-library-template.yaml",
    "infrastructure": "cloudbuild-infra-template.yaml",
    "test-harness": "cloudbuild-sit-template.yaml",
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


def load_substitution_checker():
    """Load check_cloudbuild_substitutions.py by file path (it is not a package).

    Raises LOUDLY if the checker cannot be loaded — a render that cannot be
    substitution-validated must never be written (Cloud Build silently rejects
    configs with unescaped $VARs; incident 2026-06-10, see plans/active/issues/
    cloudbuild_silent_failures_no_alerting_no_validation_2026_06_10.md).
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location("check_cloudbuild_substitutions", SUBSTITUTION_CHECKER_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load substitution checker at {SUBSTITUTION_CHECKER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


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
        if "steps" not in data:
            print(f"  YAML VALIDATION: {path_label} missing 'steps' key", file=sys.stderr)
            return False
        return True
    except Exception as exc:
        print(f"  YAML VALIDATION FAILED ({path_label}): {exc}", file=sys.stderr)
        return False


def add_deploy_via_dispatch_comment(content: str) -> str:
    """Insert deploy-via-dispatch comment after first line if not present."""
    if "deploy-via-dispatch" in content or "deploys-via-dispatch" in content.lower():
        return content
    lines = content.split("\n")
    insert_at = 1
    for i, line in enumerate(lines[:5]):
        if i > 0 and (line.strip().startswith("#") or "Cloud Build" in line):
            insert_at = i + 1
            break
    before = "\n".join(lines[:insert_at])
    rest = "\n".join(lines[insert_at:])
    if before and not before.endswith("\n"):
        before += "\n"
    return before + DEPLOY_VIA_DISPATCH_COMMENT + rest


def generate_cloudbuild(repo_name: str, repo_info: dict, deploy_via_dispatch: bool) -> str | None:
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
    pkg_name = repo_name.replace("-", "_")
    if repo_type == "library":
        content = content.replace("{{LIBRARY_NAME}}", repo_name)
        content = content.replace("{{PKG_NAME}}", pkg_name)
        content = content.replace('_LIBRARY_NAME: "{{LIBRARY_NAME}}"', f'_LIBRARY_NAME: "{repo_name}"')
        content = content.replace('_PKG_NAME: "{{PKG_NAME}}"', f'_PKG_NAME: "{pkg_name}"')
    elif repo_type == "infrastructure":
        cfg = INFRA_REPO_CONFIG[repo_name]
        content = content.replace("{{PKG_NAME}}", cfg["pkg_name"])
        content = content.replace("{{TERRAFORM_DIR}}", cfg["terraform_dir"])
        content = content.replace("{{TERRAFORM_IMAGE_NAME}}", cfg["terraform_image"])
        content = content.replace('_PKG_NAME: "{{PKG_NAME}}"', f'_PKG_NAME: "{cfg["pkg_name"]}"')
        content = content.replace('_TERRAFORM_DIR: "{{TERRAFORM_DIR}}"', f'_TERRAFORM_DIR: "{cfg["terraform_dir"]}"')
        content = content.replace(
            '_TERRAFORM_IMAGE_NAME: "{{TERRAFORM_IMAGE_NAME}}"', f'_TERRAFORM_IMAGE_NAME: "{cfg["terraform_image"]}"'
        )
    elif repo_type == "test-harness":
        content = content.replace("{{REPO_NAME}}", repo_name)
        content = content.replace('_REPO_NAME: "{{REPO_NAME}}"', f'_REPO_NAME: "{repo_name}"')
    else:
        content = content.replace("{{SERVICE_NAME}}", repo_name)
        content = content.replace("{{REGISTRY_REPO}}", REGISTRY_REPO)
        content = content.replace("{{PKG_NAME}}", pkg_name)
        content = content.replace('_SERVICE_NAME: "REPLACE_ME"', f'_SERVICE_NAME: "{repo_name}"')
        content = content.replace('_REGISTRY_REPO: "REPLACE_ME"', f'_REGISTRY_REPO: "{REGISTRY_REPO}"')
        content = content.replace('_PKG_NAME: "REPLACE_ME"', f'_PKG_NAME: "{pkg_name}"')
    if deploy_via_dispatch:
        content = add_deploy_via_dispatch_comment(content)
    return content


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print changes, do not write")
    parser.add_argument("--repo", type=str, default="", help="Limit to single repo")
    parser.add_argument("--include-library", action="store_true", help="Also process type=library (wheel-only)")
    args = parser.parse_args()

    manifest = load_manifest()
    repos = get_repos(manifest)
    if args.repo:
        if args.repo not in repos:
            print(f"Repo '{args.repo}' not in manifest", file=sys.stderr)
            return 1
        repos = {args.repo: repos[args.repo]}

    # Loud-fail if the substitution checker is unavailable — never roll out
    # un-validated configs (Cloud Build rejects them SILENTLY).
    subst_checker = load_substitution_checker()

    modified = 0
    failed_validation = 0
    for repo_name, repo_info in sorted(repos.items()):
        if repo_name in SKIP_REPOS:
            continue
        if not isinstance(repo_info, dict):
            continue
        repo_type = repo_info.get("type") or ""
        if repo_type == "library":
            if not args.include_library:
                continue
            if repo_name in LIBRARY_CUSTOM_CLOUDBUILD:
                continue
        content = generate_cloudbuild(
            repo_name,
            repo_info,
            deploy_via_dispatch=bool(repo_info.get("deploy_via_dispatch")),
        )
        if content is None:
            continue
        if not validate_yaml(content, repo_name):
            failed_validation += 1
            continue
        # Post-render substitution validation: an unescaped $VAR in the RENDERED
        # output means Cloud Build would SILENTLY reject the config on push —
        # abort this repo's write rather than ever writing an invalid config.
        violations = subst_checker.scan_cloudbuild_text(content, label=f"{repo_name}/cloudbuild.yaml")
        if violations:
            print(
                f"  SUBSTITUTION VALIDATION FAILED ({repo_name}) — rendered config would be"
                " SILENTLY rejected by Cloud Build; refusing to write (file:step-id:varname):",
                file=sys.stderr,
            )
            for violation in violations:
                print(f"    {violation.render()}", file=sys.stderr)
            print(f"    Remedy: {subst_checker.REMEDY}", file=sys.stderr)
            failed_validation += 1
            continue
        out_path = WORKSPACE_ROOT / repo_name / "cloudbuild.yaml"
        if args.dry_run:
            print(f"[dry-run] Would write {out_path} ({len(content)} bytes)")
            modified += 1
        else:
            out_path.write_text(content)
            print(f"Wrote {out_path}")
            modified += 1

    print(f"Done. {'Would modify' if args.dry_run else 'Modified'} {modified} file(s).")
    if failed_validation:
        print(
            f"ERROR: {failed_validation} repo(s) failed render validation — their cloudbuild.yaml was NOT written.",
            file=sys.stderr,
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
