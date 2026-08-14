#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
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

Refuses to write a repo's cloudbuild.yaml when the rendered template would DROP
content the live file already carries (a step, a secretEnv entry, an
availableSecrets entry, or an arg/script line) — see find_dropped_markers().
This is the "would drop content" guard: a repo carrying legitimate content the
template hasn't learned yet (template lag, or intentional per-repo drift) is
left untouched rather than silently regressed. Defaults to a dry run; writing
requires an explicit --apply.

Also refuses to write when the render would drop a consumer-only
`substitutions` key — see find_dropped_substitution_keys(). This is a SEPARATE
guard from find_dropped_markers()/_cloudbuild_markers(): those two feed
check_cloudbuild_template_drift.py's baseline-gated ratchet too (it reuses
this module's own rendering + diff functions as the single source of truth),
so adding `substitutions` to THEM would also raise that ratchet's count for
every consumer already carrying legitimate per-repo substitutions, against a
shrink-only baseline that requires an operator-sanctioned re-seed to raise
(see plans/active/issues/cloudbuild_template_drift_blocks_all_pm_commits_2026_08_12.md).
find_dropped_substitution_keys() is therefore only ever called from this
script's own --apply write path, never from the drift checker, so it protects
`--apply` without touching the ratchet baseline.

Usage:
    python rollout-cloudbuild.py [--apply] [--dry-run] [--repo NAME]

Options:
    --apply      Actually write files. Without this flag the tool always runs
                 as a dry run (prints what would happen, writes nothing).
    --dry-run    Force dry-run even if --apply is also given (explicit/no-op;
                 dry-run is already the default).
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
    except (yaml.YAMLError, TypeError) as exc:
        print(f"  YAML VALIDATION FAILED ({path_label}): {exc}", file=sys.stderr)
        return False


def _parse_cloudbuild_yaml(content: str) -> dict | None:
    """Parse cloudbuild YAML text into a dict, or None if unparseable/empty/unavailable."""
    if yaml is None:
        return None
    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def _cloudbuild_markers(data: dict) -> dict[str, set[str]]:
    """Extract identifiable content markers from a parsed cloudbuild.yaml doc.

    Parsing first (rather than a raw line diff) means purely cosmetic YAML
    reflow (e.g. a one-line `args: [...]` vs the same list wrapped across two
    lines) never shows up as a marker — only content a semantically-aware
    reader would call "dropped" does: whole steps, secretEnv/availableSecrets
    entries, list-arg items, and heredoc/script lines (compared line-wise
    since YAML block scalars preserve those breaks verbatim).
    """
    markers: dict[str, set[str]] = {
        "top-level key": set(data.keys()),
        "step": set(),
        "secretEnv": set(),
        "availableSecrets env": set(),
        "step arg": set(),
    }
    for step in data.get("steps") or []:
        if not isinstance(step, dict):
            continue
        step_id = step.get("id") or "<unnamed step>"
        markers["step"].add(step_id)
        for env_name in step.get("secretEnv") or []:
            markers["secretEnv"].add(f"{step_id}::{env_name}")
        args = step.get("args")
        if isinstance(args, list):
            for item in args:
                markers["step arg"].add(f"{step_id}::{item}")
        elif isinstance(args, str):
            for line in args.split("\n"):
                stripped = line.strip()
                if stripped:
                    markers["step arg"].add(f"{step_id}::{stripped}")
    avail = data.get("availableSecrets") or {}
    for entry in avail.get("secretManager") or []:
        if isinstance(entry, dict) and entry.get("env"):
            markers["availableSecrets env"].add(entry["env"])
    return markers


def find_dropped_markers(live_content: str, new_content: str) -> list[str] | None:
    """Diagnose content the LIVE file carries that the freshly-rendered NEW
    content is about to drop.

    Returns a list of human-readable diagnostics (empty list = nothing
    dropped), or None if the comparison itself could not be made (yaml
    module unavailable, or either document fails to parse as a dict) — the
    caller treats None conservatively (refuse rather than overwrite blind).
    """
    live_data = _parse_cloudbuild_yaml(live_content)
    if live_data is None:
        return None
    new_data = _parse_cloudbuild_yaml(new_content)
    if new_data is None:
        return None
    live_markers = _cloudbuild_markers(live_data)
    new_markers = _cloudbuild_markers(new_data)
    diagnostics: list[str] = []
    for category, live_set in live_markers.items():
        for marker in sorted(live_set - new_markers.get(category, set())):
            display = marker if len(marker) <= 160 else marker[:157] + "..."
            diagnostics.append(f"{category} dropped: {display}")
    return diagnostics


def _substitution_keys(data: dict) -> set[str]:
    subs = data.get("substitutions")
    if not isinstance(subs, dict):
        return set()
    return set(subs.keys())


def find_dropped_substitution_keys(live_content: str, new_content: str) -> list[str] | None:
    """Diagnose `substitutions` keys the LIVE file carries that the freshly
    rendered NEW content is about to drop.

    Deliberately NOT folded into find_dropped_markers()/_cloudbuild_markers()
    — see the module docstring's "Also refuses to write..." section for why:
    those two are reused by check_cloudbuild_template_drift.py's baseline
    ratchet, and this function is not, so it can guard --apply without
    requiring a baseline re-seed.

    Returns a list of human-readable diagnostics (empty list = nothing
    dropped), or None if the comparison itself could not be made (yaml
    module unavailable, or either document fails to parse as a dict) — the
    caller treats None conservatively (refuse rather than overwrite blind),
    matching find_dropped_markers()'s own contract.
    """
    live_data = _parse_cloudbuild_yaml(live_content)
    if live_data is None:
        return None
    new_data = _parse_cloudbuild_yaml(new_content)
    if new_data is None:
        return None
    dropped = sorted(_substitution_keys(live_data) - _substitution_keys(new_data))
    return [f"substitutions key dropped: {key}" for key in dropped]


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
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Force dry-run (default; no-op when --apply is absent, overrides --apply when both given)",
    )
    parser.add_argument("--apply", action="store_true", help="Actually write files (required — default is dry-run)")
    parser.add_argument("--repo", type=str, default="", help="Limit to single repo")
    parser.add_argument("--include-library", action="store_true", help="Also process type=library (wheel-only)")
    args = parser.parse_args()
    write_mode = args.apply and not args.dry_run

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
    would_regress = 0
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
        if out_path.exists():
            live_content = out_path.read_text()
            dropped = find_dropped_markers(live_content, content)
            if dropped is None:
                print(
                    f"  WOULD-DROP-CONTENT CHECK UNAVAILABLE ({repo_name}) — cannot parse the existing"
                    " cloudbuild.yaml (or the yaml module is missing); refusing an unverifiable overwrite.",
                    file=sys.stderr,
                )
                would_regress += 1
                continue
            if dropped:
                print(
                    f"  WOULD DROP CONTENT ({repo_name}) — the rendered template is missing content the"
                    " live file already carries; refusing to write. Forward-port the template or"
                    " reconcile this repo's cloudbuild.yaml first:",
                    file=sys.stderr,
                )
                for diag in dropped:
                    print(f"    {diag}", file=sys.stderr)
                would_regress += 1
                continue
            dropped_subs = find_dropped_substitution_keys(live_content, content)
            if dropped_subs is None:
                print(
                    f"  WOULD-DROP-CONTENT CHECK UNAVAILABLE ({repo_name}) — cannot parse the existing"
                    " cloudbuild.yaml (or the yaml module is missing); refusing an unverifiable overwrite.",
                    file=sys.stderr,
                )
                would_regress += 1
                continue
            if dropped_subs:
                print(
                    f"  WOULD DROP CONTENT ({repo_name}) — the rendered template is missing `substitutions`"
                    " key(s) the live file already carries; refusing to write. Forward-port the"
                    " substitution into the template or reconcile this repo's cloudbuild.yaml first:",
                    file=sys.stderr,
                )
                for diag in dropped_subs:
                    print(f"    {diag}", file=sys.stderr)
                would_regress += 1
                continue
        if write_mode:
            out_path.write_text(content)
            print(f"Wrote {out_path}")
            modified += 1
        else:
            print(f"[dry-run] Would write {out_path} ({len(content)} bytes)")
            modified += 1

    print(f"Done. {'Would modify' if not write_mode else 'Modified'} {modified} file(s).")
    if would_regress:
        print(
            f"REFUSED: {would_regress} repo(s) would have dropped live content — their cloudbuild.yaml was"
            " NOT written.",
            file=sys.stderr,
        )
    if failed_validation:
        print(
            f"ERROR: {failed_validation} repo(s) failed render validation — their cloudbuild.yaml was NOT written.",
            file=sys.stderr,
        )
    if failed_validation or would_regress:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
