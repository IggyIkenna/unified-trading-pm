#!/usr/bin/env python3
"""gap-2.6.C — Verify env-tiered buckets are provisioned per cloud-providers.yaml SSOT.

Phase 2.6 cutover prerequisite: every (kind x asset_group x env x cloud) tuple declared
in `deployment-service/configs/cloud-providers.yaml` MUST have a corresponding bucket
on the target cloud before Wave 1 rsync starts. This script enumerates the SSOT,
resolves each bucket name template with the requested env, calls the cloud APIs
per tuple, and reports the diff.

Exit-code semantics:
  0 — all checked buckets exist (Wave 1 prerequisite met for this env)
  1 — one or more missing (operator must provision before proceeding to rsync)
  2 — argument / IO / yaml-parse error

Usage::

    # Default: check prod tier on GCP
    python3 verify_env_tiered_buckets_provisioned.py

    # Check prod on both clouds
    python3 verify_env_tiered_buckets_provisioned.py --env prd --cloud all

    # Print provision commands for the missing ones
    python3 verify_env_tiered_buckets_provisioned.py --env prd --print-provision-commands

    # Provision missing buckets (GCP only; AWS not yet automated)
    python3 verify_env_tiered_buckets_provisioned.py --env prd --provision-missing

Wired by Wave 1 of `codex/05-infrastructure/phase-2-6-bucket-name-cutover-runbook.md`.
SSOT: `deployment-service/configs/cloud-providers.yaml`.

Reference: `plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md` §
"gap-2.6.C — verify_env_tiered_buckets_provisioned.py".
"""

from __future__ import annotations

import argparse
import csv
import datetime
import os
import subprocess
import sys
from collections.abc import Iterable
from dataclasses import dataclass, fields
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


@dataclass
class BucketResult:
    cloud: str
    kind: str
    asset_group: str
    env: str
    name: str
    status: str  # PRESENT | MISSING


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
    storage = cast(dict[str, object], yaml_data.get(cloud, {})).get("storage", {})  # noqa: qg-empty-fallback
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


def _check_gcp_buckets_bulk(specs: list[BucketSpec]) -> dict[str, bool]:
    """Bulk-check GCS buckets using the Python client (one list call, then lookup)."""
    try:
        from google.cloud import storage as gcs  # type: ignore[import-untyped]

        client = gcs.Client(project=_DEFAULT_GCP_PROJECT_ID)
        existing: set[str] = {
            str(b.name)  # pyright: ignore[reportUnknownMemberType, reportUnknownArgumentType]
            for b in client.list_buckets()  # pyright: ignore[reportUnknownVariableType, reportUnknownMemberType]
        }
        return {spec.name: spec.name in existing for spec in specs}
    except Exception:
        # Fall back to subprocess per-bucket if GCS client unavailable
        return {spec.name: _check_gcp_bucket_subprocess(spec.name) for spec in specs}


def _check_gcp_bucket_subprocess(name: str) -> bool:
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


def _check_aws_buckets_bulk(specs: list[BucketSpec]) -> dict[str, bool]:
    """Bulk-check S3 buckets using boto3 list_buckets."""
    try:
        import boto3  # type: ignore[import-untyped]

        s3 = boto3.client("s3")  # pyright: ignore[reportUnknownMemberType]
        response = s3.list_buckets()  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]
        existing: set[str] = {
            str(b["Name"])  # noqa: qg-empty-fallback  # pyright: ignore[reportUnknownArgumentType, reportTypedDictNotRequiredAccess]
            for b in response.get("Buckets", [])  # pyright: ignore[reportUnknownVariableType]
        }
        return {spec.name: spec.name in existing for spec in specs}
    except Exception:
        # Fall back to subprocess per-bucket
        return {spec.name: _check_aws_bucket_subprocess(spec.name) for spec in specs}


def _check_aws_bucket_subprocess(name: str) -> bool:
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


def _check_buckets(specs: list[BucketSpec]) -> dict[str, bool]:
    """Bulk-check all specs by cloud."""
    gcp_specs = [s for s in specs if s.cloud == "gcp"]
    aws_specs = [s for s in specs if s.cloud == "aws"]
    results: dict[str, bool] = {}
    if gcp_specs:
        results.update(_check_gcp_buckets_bulk(gcp_specs))
    if aws_specs:
        results.update(_check_aws_buckets_bulk(aws_specs))
    return results


def _provision_command(spec: BucketSpec) -> str:
    if spec.cloud == "gcp":
        return (
            f"gcloud storage buckets create gs://{spec.name} --location=asia-northeast1 --uniform-bucket-level-access"
        )
    if spec.cloud == "aws":
        region = "ap-northeast-1"
        return (
            f"aws s3api create-bucket --bucket {spec.name} --region {region} "
            f"--create-bucket-configuration LocationConstraint={region}"
        )
    return f"# unknown cloud {spec.cloud}"


def _provision_gcp_bucket(name: str) -> bool:
    """Create a GCS bucket; return True on success."""
    try:
        result = subprocess.run(
            [
                "gcloud",
                "storage",
                "buckets",
                "create",
                f"gs://{name}",
                "--location=asia-northeast1",
                "--uniform-bucket-level-access",
                "--project=" + _DEFAULT_GCP_PROJECT_ID,
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode == 0:
            return True
        # "already exists" is also success
        if "already exists" in result.stderr.lower():
            return True
        print(f"  GCP create error: {result.stderr.strip()}", file=sys.stderr)
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        print(f"  GCP provision exception: {exc}", file=sys.stderr)
        return False


def _iter_clouds(cloud_arg: str) -> Iterable[str]:
    if cloud_arg == "all":
        return ("gcp", "aws")
    return (cloud_arg,)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify env-tiered buckets provisioned per cloud-providers.yaml SSOT.")
    parser.add_argument(
        "--yaml-path",
        type=Path,
        default=Path(__file__).resolve().parents[2].parent / "deployment-service" / "configs" / "cloud-providers.yaml",
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
        "--provision-missing",
        action="store_true",
        help="Provision missing GCP buckets (calls gcloud storage buckets create). AWS: print commands only.",
    )
    parser.add_argument(
        "--csv-out",
        type=Path,
        default=None,
        help="Write results to this CSV path. Defaults to plans/audit/results/env_tiered_buckets_provisioned_<date>.csv",  # noqa: E501
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Enumerate + print bucket names without checking existence (offline mode)",
    )
    return parser.parse_args()


def _write_csv(results: list[BucketResult], csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[fi.name for fi in fields(BucketResult)])
        writer.writeheader()
        for r in results:
            writer.writerow(
                {
                    "cloud": r.cloud,
                    "kind": r.kind,
                    "asset_group": r.asset_group or "",
                    "env": r.env,
                    "name": r.name,
                    "status": r.status,
                }
            )
    print(f"CSV written: {csv_path}")


def main() -> int:
    ns = _parse_args()
    yaml_path: Path = cast(Path, ns.yaml_path)
    env: str = cast(str, ns.env)
    cloud: str = cast(str, ns.cloud)
    project_id: str = cast(str, ns.project_id)
    aws_account_id: str = cast(str, ns.aws_account_id)
    print_commands: bool = cast(bool, ns.print_provision_commands)
    provision_missing: bool = cast(bool, ns.provision_missing)
    dry_run: bool = cast(bool, ns.dry_run)
    csv_out: Path | None = cast(Path | None, ns.csv_out)

    if csv_out is None:
        date_str = datetime.date.today().isoformat()
        default_csv_dir = Path(__file__).resolve().parents[2] / "plans" / "audit" / "results"
        csv_out = default_csv_dir / f"env_tiered_buckets_provisioned_{date_str}.csv"

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
        f"Enumerated {len(all_specs)} bucket(s) from {yaml_path.name} (cloud={cloud}, env={env}, project={project_id})."
    )

    if dry_run:
        for spec in all_specs:
            print(f"  {spec.cloud}: {spec.name}  ({spec.kind} / {spec.asset_group or '<shared>'})")
        return 0

    print("Checking bucket existence (bulk API)...")
    existence = _check_buckets(all_specs)

    missing: list[BucketSpec] = []
    results: list[BucketResult] = []
    for spec in all_specs:
        exists = existence.get(spec.name, False)
        status = "PRESENT" if exists else "MISSING"
        results.append(
            BucketResult(
                cloud=spec.cloud,
                kind=spec.kind,
                asset_group=spec.asset_group or "",
                env=spec.env,
                name=spec.name,
                status=status,
            )
        )
        if not exists:
            missing.append(spec)

    _write_csv(results, csv_out)

    present_count = len(all_specs) - len(missing)
    print(f"Existing: {present_count} / {len(all_specs)}; missing: {len(missing)}.")

    if missing:
        print("\nMISSING buckets:")
        for spec in missing:
            print(f"  {spec.cloud}: {spec.name}  ({spec.kind} / {spec.asset_group or '<shared>'})")

        if print_commands:
            print("\nProvision commands:")
            for spec in missing:
                print(f"  {_provision_command(spec)}")

        if provision_missing:
            print("\nProvisioning missing GCP buckets...")
            provisioned = 0
            skipped_aws: list[BucketSpec] = []
            for spec in missing:
                if spec.cloud == "gcp":
                    print(f"  Creating gs://{spec.name} ...", end=" ", flush=True)
                    ok = _provision_gcp_bucket(spec.name)
                    if ok:
                        print("OK")
                        provisioned += 1
                    else:
                        print("FAILED")
                else:
                    skipped_aws.append(spec)
            print(f"  GCP: provisioned {provisioned} bucket(s).")
            if skipped_aws:
                print(f"  AWS: {len(skipped_aws)} bucket(s) not auto-provisioned — run manually:")
                for spec in skipped_aws:
                    print(f"    {_provision_command(spec)}")
            # Re-check to update missing count
            remaining = [s for s in missing if s.cloud != "gcp"]
            if remaining:
                print(f"\n❌ {len(remaining)} AWS bucket(s) still missing after GCP auto-provision.")
                return 1
            print("\n✅ All GCP buckets provisioned. AWS buckets still require manual creation.")
            return 0

        print(
            f"\n❌ {len(missing)} bucket(s) missing — provision before Wave 1 rsync. "
            "See codex/05-infrastructure/phase-2-6-bucket-name-cutover-runbook.md."
        )
        return 1

    print(f"\n✅ All {len(all_specs)} buckets exist for env={env} cloud={cloud}. Wave 1 prerequisite met.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
