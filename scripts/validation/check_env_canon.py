#!/usr/bin/env python3
"""Validate env var usage: only canonical keys from unified_api_contracts.internal.EnvVars.

Greps for os.getenv(, os.environ[, os.environ.get( in SOURCE_DIR.
Excludes tests/, conftest, scripts/, .github/.
Validates extracted keys against EnvVars.all_canonical().
Bootstrap files (_env_bootstrap.py, factory.py, constants.py) are skipped.

Usage:
    python scripts/validation/check_env_canon.py <repo_path>
    python scripts/validation/check_env_canon.py /path/to/features-commodity-service

Exit: 0 if all valid, 1 if any non-canonical.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

try:
    from unified_api_contracts.internal import EnvVars
except ImportError:
    # Fallback if UIC not available (e.g. running outside workspace)
    EnvVars = None

# Bootstrap allowlist: these files may use env before config exists; skip validation
# heartbeat_cli.py is a VM-side bootstrap CLI (deployment-service): reads VM metadata env
# vars at boot before the cloud config is reachable.
BOOTSTRAP_BASENAMES = {
    "_env_bootstrap.py",
    "factory.py",
    "constants.py",
    "config.py",
    "__main__.py",
    "kill_switch.py",
    "heartbeat_cli.py",
}

# Path segments to exclude from scanning
EXCLUDE_SEGMENTS = {"tests", "scripts", ".github", ".venv", "examples"}
EXCLUDE_FILENAMES = {"conftest.py"}

# Build/dependency dirs EXCLUDED from the source walk — os.walk never descends into them, so
# their contents are never scanned (these hold third-party / generated code, not repo source).
# Without this, a plain rglob("*.py") would still enumerate every .venv file (~14k on a big
# repo) just to discard them per-path. (Naming: these are excluded, not "pruned"/removed.)
EXCLUDE_DIR_NAMES = frozenset(
    {".venv", ".venv-workspace", "venv", "build", "dist", "node_modules", "__pycache__", ".git"}
)


def _iter_source_py(root: Path) -> list[Path]:
    """All `.py` under root, EXCLUDING EXCLUDE_DIR_NAMES dirs (os.walk never descends into them)."""
    out: list[Path] = []
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIR_NAMES]
        out.extend(Path(dirpath) / fn for fn in files if fn.endswith(".py"))
    return out

# Patterns for os.getenv, os.environ[, os.environ.get(
OS_GETENV_RE = re.compile(r"os\.getenv\s*\(\s*[\"']([^\"']+)[\"']")
OS_ENVIRON_GET_RE = re.compile(r"os\.environ\.get\s*\(\s*[\"']([^\"']+)[\"']")
OS_ENVIRON_INDEX_RE = re.compile(r"os\.environ\s*\[\s*[\"']([^\"']+)[\"']\s*\]")


def _get_canonical_keys() -> set[str]:
    """Return set of canonical env var keys from UIC EnvVars."""
    if EnvVars is not None:
        return EnvVars.all_canonical()
    else:
        # Fallback if UIC not available (e.g. running outside workspace)
        return {
            "RUNTIME_MODE",
            "DATA_MODE",
            "CLOUD_PROVIDER",
            "PHASE_MODE",
            "GCP_PROJECT_ID",
            "AWS_ACCOUNT_ID",
            "RUNTIME_TOPOLOGY_PATH",
            "WORKSPACE_ROOT",
            "DEPLOYMENT_ENV",
            "ENVIRONMENT",
            "PROTOCOL_DATA_SINK_BUCKET",
            "PROTOCOL_DATA_SINK_BACKEND",
            "PROTOCOL_DATA_SINK_TABLE_PREFIX",
            "PROTOCOL_DATA_SOURCE_BUCKET",
            "PROTOCOL_DATA_SOURCE_BACKEND",
            "PROTOCOL_DATA_SOURCE_DIR",
            "PROTOCOL_EVENT_BUS_PROJECT",
            "PROTOCOL_EVENT_BUS_BACKEND",
            "PROTOCOL_ANALYTICS_PROJECT",
            "PROTOCOL_ANALYTICS_DATASET",
            "PROTOCOL_ANALYTICS_BACKEND",
            "SERVICE_MODE",
            "AWS_REGION",
            "AWS_PROFILE",
            "ATHENA_OUTPUT_BUCKET",
            "GOOGLE_APPLICATION_CREDENTIALS",
            "GCS_REGION",
            "GCS_LOCATION",
            "BIGQUERY_LOCATION",
            "SECRETS_CLOUD_PROVIDER",
            "REDIS_URL",
            "PUBSUB_EMULATOR_HOST",
            "STORAGE_EMULATOR_HOST",
            "BIGQUERY_EMULATOR_HOST",
        }


def should_skip_path(rel_path: Path) -> bool:
    """Return True if path should be excluded from scanning."""
    parts = rel_path.parts
    if any(seg in parts for seg in EXCLUDE_SEGMENTS):
        return True
    return rel_path.name in EXCLUDE_FILENAMES


def is_bootstrap_file(rel_path: Path) -> bool:
    """Return True if file is in bootstrap allowlist (skip validation)."""
    return rel_path.name in BOOTSTRAP_BASENAMES


def extract_env_keys(content: str) -> list[tuple[int, str]]:
    """Extract (line_no, key) for each env read with literal string key.

    Lines containing ``# config-bootstrap:`` are skipped — they represent
    pre-config-init reads that happen before UnifiedCloudConfig is available.
    """
    results: list[tuple[int, str]] = []
    patterns = [OS_GETENV_RE, OS_ENVIRON_GET_RE, OS_ENVIRON_INDEX_RE]
    for i, line in enumerate(content.splitlines(), start=1):
        if "config-bootstrap:" in line:
            continue
        for pat in patterns:
            for m in pat.finditer(line):
                results.append((i, m.group(1)))
    return results


def scan_source_dir(source_dir: Path, canonical: set[str]) -> list[tuple[Path, int, str]]:
    """Scan source_dir for non-canonical env var usage. Return [(path, line, key), ...]."""
    violations: list[tuple[Path, int, str]] = []
    if not source_dir.is_dir():
        return violations

    for py_file in _iter_source_py(source_dir):
        try:
            rel = py_file.relative_to(source_dir)
        except ValueError:
            continue
        if should_skip_path(rel):
            continue
        if is_bootstrap_file(rel):
            continue
        try:
            content = py_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for line_no, key in extract_env_keys(content):
            if key not in canonical:
                violations.append((py_file, line_no, key))
    return violations


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python check_env_canon.py <repo_path>", file=sys.stderr)
        return 2
    repo_path = Path(sys.argv[1]).resolve()
    if not repo_path.exists():
        print(f"Error: path does not exist: {repo_path}", file=sys.stderr)
        return 2
    canonical = _get_canonical_keys()
    violations = scan_source_dir(repo_path, canonical)
    if violations:
        for path, line_no, key in violations:
            print(f"{path}:{line_no}: non-canonical env key: {key!r}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
