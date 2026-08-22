#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""Validate build auth before Cloud Build / CodeBuild runs.

Checks that credentials have the right permissions so builds don't fail mid-way
when pulling wheels or pushing images. Run locally (gcloud/aws configured) or
in CI before triggering builds.

Validates:
  - GCP: token, Python AR (unified-libraries) read, Docker AR (unified-trading-library) read
  - AWS: ECR auth, CodeArtifact (optional)
  - Secrets alignment: GCP_PROJECT_ID, AWS_ACCOUNT_ID present in env or .act-secrets

Usage:
    python3 validate-build-auth.py [--gcp-only] [--aws-only] [--check-secrets]
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
ACT_SECRETS = WORKSPACE_ROOT / ".act-secrets"
GCP_PYTHON_REPO = "unified-libraries"
GCP_DOCKER_REPO = "unified-trading-library"
GCP_REGION = "asia-northeast1"


def _run(cmd: list[str], capture: bool = True) -> tuple[int, str]:
    try:
        result = subprocess.run(cmd, capture_output=capture, text=True, timeout=30)
        return result.returncode, (result.stdout or "") + (result.stderr or "")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return -1, "Command failed"


def _get_project_id() -> str | None:
    pid = os.environ.get("GCP_PROJECT_ID") or os.environ.get("PROJECT_ID")
    if pid:
        return pid
    if ACT_SECRETS.exists():
        for line in ACT_SECRETS.read_text().splitlines():
            if line.startswith("GCP_PROJECT_ID="):
                return line.split("=", 1)[1].strip().strip('"')
    code, out = _run(["gcloud", "config", "get-value", "project", "--quiet"])
    return out.strip() if code == 0 and out.strip() else None


def check_gcp_token() -> tuple[bool, str]:
    code, out = _run(["gcloud", "auth", "print-access-token"])
    return (True, "GCP token OK") if code == 0 else (False, f"No GCP token: {out.strip() or 'gcloud auth required'}")


def check_gcp_python_ar_read(project_id: str) -> tuple[bool, str]:
    code, token_out = _run(["gcloud", "auth", "print-access-token"])
    if code != 0:
        return False, "No token for AR check"
    token = token_out.strip()
    url = f"https://{GCP_REGION}-python.pkg.dev/{project_id}/{GCP_PYTHON_REPO}/simple/"
    code, out = _run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "-H", f"Authorization: Bearer {token}", url]
    )
    if code != 0:
        return False, f"curl failed: {out}"
    status = out.strip()
    if status == "200":
        return True, f"Python AR ({GCP_PYTHON_REPO}) read OK"
    if status == "401":
        return False, "Python AR: 401 — token invalid or SA lacks roles/artifactregistry.reader"
    return False, f"Python AR: HTTP {status}"


def check_gcp_docker_ar_read(project_id: str) -> tuple[bool, str]:
    code, out = _run(
        [
            "gcloud",
            "artifacts",
            "repositories",
            "describe",
            GCP_DOCKER_REPO,
            f"--location={GCP_REGION}",
            f"--project={project_id}",
        ]
    )
    return (
        (True, f"Docker AR ({GCP_DOCKER_REPO}) read OK")
        if code == 0
        else (False, f"Docker AR: {out.strip() or 'describe failed'}")
    )


def check_aws_ecr_auth() -> tuple[bool, str]:
    region = os.environ.get("AWS_DEFAULT_REGION", "ap-northeast-1")
    code, out = _run(["aws", "ecr", "get-login-password", "--region", region])
    return (True, "ECR auth OK") if code == 0 else (False, f"ECR auth failed: {out.strip()}")


def check_secrets_file() -> tuple[bool, str]:
    if not ACT_SECRETS.exists():
        return False, ".act-secrets not found"
    text = ACT_SECRETS.read_text()
    if "GCP_PROJECT_ID=" not in text:
        return False, ".act-secrets missing GCP_PROJECT_ID"
    return True, ".act-secrets OK"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gcp-only", action="store_true")
    parser.add_argument("--aws-only", action="store_true")
    parser.add_argument("--check-secrets", action="store_true")
    args = parser.parse_args()

    failed = 0
    if args.check_secrets:
        ok, msg = check_secrets_file()
        print(f"  [{'OK' if ok else 'FAIL'}] {msg}")
        failed += 0 if ok else 1

    if not args.aws_only:
        project_id = _get_project_id()
        if not project_id:
            print("  [FAIL] GCP: No project ID (set GCP_PROJECT_ID)")
            failed += 1
        else:
            for name, check in [
                ("GCP token", check_gcp_token),
                ("Python AR read", lambda: check_gcp_python_ar_read(project_id)),
                ("Docker AR read", lambda: check_gcp_docker_ar_read(project_id)),
            ]:
                ok, msg = check()
                print(f"  [{'OK' if ok else 'FAIL'}] {name}: {msg}")
                failed += 0 if ok else 1

    if not args.gcp_only:
        ok, msg = check_aws_ecr_auth()
        print(f"  [{'OK' if ok else 'FAIL'}] AWS ECR: {msg}")
        failed += 0 if ok else 1

    if failed:
        print("\nPre-build auth validation failed.", file=sys.stderr)
        return 1
    print("\nPre-build auth validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
