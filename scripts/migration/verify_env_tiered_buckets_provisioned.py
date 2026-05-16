#!/usr/bin/env python3
"""gap-2.6.C — Verify env-tiered buckets are provisioned per cloud-providers.yaml SSOT.

Phase 2.6 cutover prerequisite: every (kind × asset_group × env × cloud) tuple declared
in `deployment-service/configs/cloud-providers.yaml` MUST have a corresponding bucket
on the target cloud before Wave 1 rsync starts. This script enumerates the SSOT,
resolves each bucket name template with the requested env, calls
`gcloud storage buckets describe` / `aws s3api head-bucket` per tuple, and reports
the diff.

Exit-code semantics:
  0 — all checked buckets exist (Wave 1 prerequisite met for this env)
  1 — one or more missing (operator must provision before proceeding to rsync)
  2 — argument / IO / yaml-parse error

Usage::

    # Default: check prod tier on GCP
    python3 verify_env_tiered_buckets_provisioned.py

    # Check staging on both clouds
    python3 verify_env_tiered_buckets_provisioned.py --env stg --cloud all

    # Print provision commands for the missing ones
    python3 verify_env_tiered_buckets_provisioned.py --env prd --print-provision-commands

Wired by Wave 1 of `codex/05-infrastructure/phase-2-6-bucket-name-cutover-runbook.md`.
SSOT: `deployment-service/configs/cloud-providers.yaml`.

Reference: `plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md` §
"gap-2.6.C — verify_env_tiered_buckets_provisioned.py".
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import yaml

# Short-form env codes per cloud-providers.yaml header convention
_ENV_SHORT: dict[str, str] = {
    "dev": "dev",
    "stg": "stg",
    "prd": "prd",
    "test": "test",
}
_VALID_CLOUDS = ("gcp", "aws", "all")
_DEFAULT_GCP_PROJECT_ID = "central-element-323112"
_DEFAULT_AWS_ACCOUNT_ID = "427895769566"


@dataclass(frozen=True)
class BucketSpec:
    cloud: str
    kind: str
    asset_group: str | None
    env: str
    name: str


def _substitute_template(template: str, env_short: str, project_id: str, aws_account_id: str) -> str:
    """Mirror UTL `bucket_naming._substitute_env_vars` for the 3 vars used here."""
    return (
        template.replace("${DEPLOYMENT_ENV_SHORT}", env_short)
        .replace("${GCP_PROJECT_ID}", project_id)
        .replace("${AWS_ACCOUNT_ID}", aws_account_id)
    )


def _enumerate_buckets(
    yaml_data: dict[str, object],
    cloud: str,
    env: str,
    project_id: str,
    aws_account_id: str,
) -> list[BucketSpec]:
    """Walk the yaml SSOT and yield every (kind, asset_group, env) bucket name."""
    out: list[BucketSpec] = []
    env_short = _ENV_SHORT[env]
    storage = cast(dict[str, object], yaml_data.get(cloud, {})).get("storage", {})
    if not isinstance(storage, dict):
        return out
    typed_storage = cast(dict[str, object], storage)
    for kind, value in typed_storage.items():
        if isinstance(value, str):
            # Shared (no asset_group) — single template
            name = _substitute_template(value, env_short, project_id, aws_account_id)
            out.append(BucketSpec(cloud=cloud, kind=kind, asset_group=None, env=env, name=name))
        elif isinstance(value, dict):
            # Per-asset_group dict
            typed_value = cast(dict[str, object], value)
            for ag, tpl in typed_value.items():
                if not isinstance(tpl, str):
                    continue
                name = _substitute_template(tpl, env_short, project_id, aws_account_id)
                out.append(BucketSpec(cloud=cloud, kind=kind, asset_group=ag, env=env, name=name))
    return out


def _check_gcp_bucket(name: str) -> bool:
    """Return True if the GCS bucket exists (via gcloud storage buckets describe)."""
    try:
        result = subprocess.run(
            ["gcloud", "storage", "buckets", "describe", f"gs://{name}", "--format=value(name)"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _check_aws_bucket(name: str) -> bool:
    """Return True if the S3 bucket exists (via aws s3api head-bucket)."""
    try:
        result = subprocess.run(
            ["aws", "s3api", "head-bucket", "--bucket", name],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _check_bucket(spec: BucketSpec) -> bool:
    if spec.cloud == "gcp":
        return _check_gcp_bucket(spec.name)
    if spec.cloud == "aws":
        return _check_aws_bucket(spec.name)
    return False


def _provision_command(spec: BucketSpec) -> str:
    if spec.cloud == "gcp":
        return (
            f"gcloud storage buckets create gs://{spec.name} "
            "--location=asia-northeast1 --uniform-bucket-level-access"
        )
    if spec.cloud == "aws":
        return f"aws s3api create-bucket --bucket {spec.name} --region us-east-1"
    return f"# unknown cloud {spec.cloud}"


def _iter_clouds(cloud_arg: str) -> Iterable[str]:
    if cloud_arg == "all":
        return ("gcp", "aws")
    return (cloud_arg,)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify env-tiered buckets provisioned per cloud-providers.yaml SSOT."
    )
    parser.add_argument(
        "--yaml-path",
        type=Path,
        default=Path(__file__).resolve().parents[2].parent
        / "deployment-service"
        / "configs"
        / "cloud-providers.yaml",
        help="Path to cloud-providers.yaml SSOT",
    )
    parser.add_argument(
        "--env",
        choices=("dev", "stg", "prd", "test"),
        default="prd",
        help="Env short-form (default: prd)",
    )
    parser.add_argument(
        "--cloud",
        choices=_VALID_CLOUDS,
        default="gcp",
        help="Cloud to check (default: gcp; 'all' = both)",
    )
    parser.add_argument(
        "--project-id",
        default=os.environ.get("GCP_PROJECT_ID", _DEFAULT_GCP_PROJECT_ID),
        help="GCP project ID for ${GCP_PROJECT_ID} substitution",
    )
    parser.add_argument(
        "--aws-account-id",
        default=os.environ.get("AWS_ACCOUNT_ID", _DEFAULT_AWS_ACCOUNT_ID),
        help="AWS account ID for ${AWS_ACCOUNT_ID} substitution",
    )
    parser.add_argument(
        "--print-provision-commands",
        action="store_true",
        help="Print gcloud/aws provision commands for missing buckets",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Enumerate + print bucket names without checking existence (offline mode)",
    )
    return parser.parse_args()


def main() -> int:
    ns = _parse_args()
    yaml_path: Path = cast(Path, ns.yaml_path)
    env: str = cast(str, ns.env)
    cloud: str = cast(str, ns.cloud)
    project_id: str = cast(str, ns.project_id)
    aws_account_id: str = cast(str, ns.aws_account_id)
    print_commands: bool = cast(bool, ns.print_provision_commands)
    dry_run: bool = cast(bool, ns.dry_run)

    if not yaml_path.exists():
        print(f"ERROR: yaml not found: {yaml_path}", file=sys.stderr)
        return 2

    try:
        yaml_data = cast(object, yaml.safe_load(yaml_path.read_text(encoding="utf-8")))
    except yaml.YAMLError as exc:
        print(f"ERROR: yaml parse failed: {exc}", file=sys.stderr)
        return 2
    if not isinstance(yaml_data, dict):
        print("ERROR: yaml root is not a dict", file=sys.stderr)
        return 2
    typed_yaml = cast(dict[str, object], yaml_data)

    all_specs: list[BucketSpec] = []
    for c in _iter_clouds(cloud):
        all_specs.extend(_enumerate_buckets(typed_yaml, c, env, project_id, aws_account_id))

    print(
        f"Enumerated {len(all_specs)} bucket(s) from {yaml_path.name} "
        f"(cloud={cloud}, env={env}, project={project_id})."
    )

    if dry_run:
        for spec in all_specs:
            print(f"  {spec.cloud}: {spec.name}  ({spec.kind} / {spec.asset_group or '<shared>'})")
        return 0

    missing: list[BucketSpec] = []
    for spec in all_specs:
        exists = _check_bucket(spec)
        if not exists:
            missing.append(spec)

    print(f"Existing: {len(all_specs) - len(missing)} / {len(all_specs)}; missing: {len(missing)}.")

    if missing:
        print("\nMISSING buckets:")
        for spec in missing:
            print(
                f"  {spec.cloud}: {spec.name}  ({spec.kind} / {spec.asset_group or '<shared>'})"
            )
        if print_commands:
            print("\nProvision commands:")
            for spec in missing:
                print(f"  {_provision_command(spec)}")
        print(
            f"\n❌ {len(missing)} bucket(s) missing — provision before Wave 1 rsync. "
            "See codex/05-infrastructure/phase-2-6-bucket-name-cutover-runbook.md."
        )
        return 1

    print(
        f"\n✅ All {len(all_specs)} buckets exist for env={env} cloud={cloud}. "
        "Wave 1 prerequisite met."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
